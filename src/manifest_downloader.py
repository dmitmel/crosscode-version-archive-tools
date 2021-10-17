from __future__ import annotations

import gevent.monkey

gevent.monkey.patch_all()

import argparse
import contextlib
import logging
import os
import sqlite3
import sys
from datetime import datetime, timezone
from getpass import getpass
from types import TracebackType
from typing import IO, Optional, Type, TypedDict, Union, cast

import yaml
from steam.client import SteamClient
from steam.client.cdn import CDNClient, CDNDepotManifest
from steam.enums.common import EResult

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class InputManifestsData(TypedDict):
  apps: list[InputManifestsApp]


class InputManifestsApp(TypedDict):
  id: str
  title: str
  enabled: bool
  depots: list[InputManifestsDepot]


class InputManifestsDepot(TypedDict):
  id: str
  title: str
  enabled: bool
  manifests: list[InputManifestsManifest]


class InputManifestsManifest(TypedDict):
  id: str
  enabled: bool
  seen: int


def main() -> None:
  parser = argparse.ArgumentParser()
  subparsers = parser.add_subparsers(required=True, metavar="COMMAND")

  subparser = subparsers.add_parser("update", help="")
  subparser.set_defaults(func=cmd_update_database)

  subparser = subparsers.add_parser("open-steamdb-pages", help="")
  subparser.set_defaults(func=cmd_open_steamdb_pages)

  subparser = subparsers.add_parser("view", help="")
  subparser.set_defaults(func=cmd_view_manifest)
  subparser.add_argument("depot_id")
  subparser.add_argument("manifest_id", nargs="?")

  subparser = subparsers.add_parser("export", help="")
  subparser.set_defaults(func=cmd_export_manifests)
  subparser.add_argument("--output", "-o", required=True)

  args = parser.parse_args()
  args.func(args)


def cmd_update_database(args: argparse.Namespace) -> None:
  db_connection = connect_to_database()
  input_manifests_data = load_input_manifests()

  each_and_every_manifest: list[tuple[int, int, int, InputManifestsManifest]] = []
  for input_app in input_manifests_data["apps"]:
    if not input_app.get("enabled", True):
      continue
    for input_depot in input_app["depots"]:
      if not input_depot.get("enabled", True):
        continue
      for input_manifest in input_depot["manifests"]:
        if not input_manifest.get("enabled", True):
          continue
        each_and_every_manifest.append((
          int(input_app["id"]), int(input_depot["id"]), int(input_manifest["id"]), input_manifest
        ))

  auth_secrets_dir = os.path.join(PROJECT_DIR, "data", "steam_auth")
  os.chmod(auth_secrets_dir, 0o700)
  with MySteamClient() as client:
    client.set_credential_location(auth_secrets_dir)
    client.username = cast(str, input_manifests_data.get("username"))
    client.my_fancy_login_routine()
    print(f"Logged in as: {client.user.name if client.user is not None else None}")
    cdn_client = CDNClient(client)

    for idx, (app_id, depot_id, manifest_id, manifest_obj) in enumerate(each_and_every_manifest):
      print(
        f"[{idx + 1}/{len(each_and_every_manifest)}] Downloading manifest {app_id}/{depot_id}/{manifest_id}..."
      )

      with db_connection, contextlib.closing(db_connection.cursor()) as db_cursor:
        if db_cursor.execute(
          """
          SELECT 1 FROM manifests WHERE app_id = ? AND depot_id = ? AND id = ? LIMIT 1
          """, (app_id, depot_id, manifest_id)
        ).fetchone() is not None:
          continue

        # See also:
        # <https://github.com/SteamDatabase/Protobufs/blob/a4d8b95a6ac5c1a45036cffa4349d28993edd7ba/steam/content_manifest.proto>
        manifest: CDNDepotManifest = cdn_client.get_manifest(app_id, depot_id, manifest_id)

        db_cursor.execute(
          """
          INSERT INTO manifests(app_id, depot_id, id, created_at, seen_by_steamdb_at, original_size, compressed_size)
          VALUES (?, ?, ?, ?, ?, ?, ?)
          """, (
            app_id,
            depot_id,
            manifest_id,
            datetime.fromtimestamp(manifest.creation_time, timezone.utc),
            datetime.fromtimestamp(manifest_obj["seen"], timezone.utc),
            manifest.size_original,
            manifest.size_compressed,
          )
        )

        def normalize_file_path(path_raw: str) -> str:
          return path_raw.rstrip("\0").replace("\\", "/")

        for file in manifest:
          original_size = sum(chunk.cb_original for chunk in file.chunks)
          compressed_size = sum(chunk.cb_compressed for chunk in file.chunks)
          assert file.size == original_size
          row = (
            normalize_file_path(file.file_mapping.filename),
            original_size,
            compressed_size,
            len(file.chunks),
            file.flags,
            file.file_mapping.sha_content,
            normalize_file_path(file.file_mapping.linktarget),
          )

          # <https://stackoverflow.com/questions/19337029/insert-if-not-exists-statement-in-sqlite#comment45649892_19343100>
          db_cursor.execute(
            """
            INSERT OR IGNORE INTO all_files(
              path, original_size, compressed_size, chunks_count, flags, hash_sha1, link_target
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, row
          )
          db_cursor.execute(
            """
            INSERT INTO manifest_files(depot_id, manifest_id, file_id)
            VALUES (?, ?, (
              SELECT id FROM all_files
              WHERE path = ? AND original_size = ? AND compressed_size = ? AND chunks_count = ?
                AND flags = ? AND hash_sha1 = ? AND link_target = ?
              LIMIT 1
            ))
            """, (depot_id, manifest_id, *row)
          )


def cmd_open_steamdb_pages(args: argparse.Namespace) -> None:
  import webbrowser
  input_manifests_data = load_input_manifests()
  for app in input_manifests_data["apps"]:
    for depot in app["depots"]:
      webbrowser.open(f"https://steamdb.info/depot/{depot['id']}/manifests/")


def cmd_view_manifest(args: argparse.Namespace) -> None:
  db_connection = connect_to_database()
  try:
    export_single_manifest(db_connection, args.depot_id, args.manifest_id, sys.stdout)
  except BrokenPipeError:
    pass


def cmd_export_manifests(args: argparse.Namespace) -> None:
  db_connection = connect_to_database()
  all_manifests: list[sqlite3.Row] = []
  with db_connection, contextlib.closing(db_connection.cursor()) as db_cursor:
    all_manifests = db_cursor.execute(
      """
      SELECT app_id, depot_id, id FROM manifests
      ORDER BY app_id ASC, depot_id ASC, datetime(created_at) DESC
      """
    ).fetchall()
  for idx, (app_id, depot_id, manifest_id) in enumerate(all_manifests):
    print(
      f"[{idx + 1}/{len(all_manifests)}] Exporting manifest {app_id}/{depot_id}/{manifest_id}..."
    )
    export_dir = args.output
    for component in (str(app_id), str(depot_id)):
      try:
        export_dir = os.path.join(export_dir, component)
        os.mkdir(export_dir)
      except FileExistsError:
        pass
    with open(os.path.join(export_dir, str(manifest_id) + ".txt"), "w") as file:
      export_single_manifest(db_connection, depot_id, manifest_id, file)


def export_single_manifest(
  db_connection: sqlite3.Connection, depot_id: int, manifest_id: Optional[int], output: IO[str]
) -> None:
  """
  The exported text format is basically a rip-off from
  <https://github.com/SteamRE/DepotDownloader/blob/DepotDownloader_2.4.4/DepotDownloader/ContentDownloader.cs#L1339-L1372>.
  """

  with db_connection, contextlib.closing(db_connection.cursor()) as db_cursor:
    if manifest_id is None:
      result: sqlite3.Row = db_cursor.execute(
        """
        SELECT id FROM manifests
        WHERE depot_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """, (depot_id,)
      ).fetchone()
      if result is not None:
        manifest_id, = result

    result: sqlite3.Row = db_cursor.execute(
      """
      SELECT created_at, seen_by_steamdb_at, original_size, compressed_size FROM manifests
      WHERE depot_id = ? AND id = ? LIMIT 1
      """, (depot_id, manifest_id)
    ).fetchone()
    if result is None:
      raise LookupError("Manifest not found!")
    created_at, seen_by_steamdb_at, original_size, compressed_size = result

    files: list[sqlite3.Row] = db_cursor.execute(
      """
      SELECT a.path, a.original_size, a.flags, a.hash_sha1, a.link_target FROM all_files AS a
      INNER JOIN manifest_files AS m ON a.id = m.file_id
      WHERE m.depot_id = ? AND m.manifest_id = ?
      ORDER BY a.path ASC
      """, (depot_id, manifest_id)
    ).fetchall()

  if isinstance(created_at, int):
    created_at = datetime.fromtimestamp(created_at, timezone.utc)
  else:
    created_at = datetime.fromisoformat(created_at)

  if isinstance(seen_by_steamdb_at, int):
    seen_by_steamdb_at = datetime.fromtimestamp(seen_by_steamdb_at, timezone.utc)
  else:
    seen_by_steamdb_at = datetime.fromisoformat(seen_by_steamdb_at)

  output.write(f"Content Manifest for Depot {depot_id}\n")
  output.write("\n")
  output.write(f"Manifest ID            : {manifest_id}\n")
  output.write(f"Creation time          : {created_at}\n")
  output.write(f"Seen by SteamDB at     : {seen_by_steamdb_at}\n")
  output.write(f"Total number of files  : {len(files)}\n")
  output.write(f"Total bytes on disk    : {original_size}\n")
  output.write(f"Total bytes compressed : {compressed_size}\n")
  output.write("\n")
  output.write("          Size Hash                                     Flags Name\n")
  output.write("-------------- ---------------------------------------- ----- ")
  output.write("-" * max(20, max(len(path) for path, *_ in files)))
  output.write("\n")
  for path, original_size, flags, hash_sha1, link_target in files:
    output.write(f"{original_size:14} {bytes.hex(hash_sha1):<40} {flags:5} {path}")
    if link_target is not None and len(link_target) > 0:
      output.write(f" -> {link_target}")
    output.write("\n")
  output.flush()


def load_input_manifests() -> InputManifestsData:
  with open(os.path.join(PROJECT_DIR, "data", "input_manifests.yaml"), "r") as file:
    return yaml.safe_load(file)


def connect_to_database() -> sqlite3.Connection:
  db_connection = sqlite3.connect(os.path.join(PROJECT_DIR, "data", "manifests.sqlite3"))
  db_connection.row_factory = sqlite3.Row
  with db_connection, contextlib.closing(db_connection.cursor()) as db_cursor:
    db_cursor.executescript(
      """
      CREATE TABLE IF NOT EXISTS manifests (
        app_id             INTEGER NOT NULL,
        depot_id           INTEGER NOT NULL,
        id                 INTEGER NOT NULL,
        created_at         TEXT    NOT NULL,
        seen_by_steamdb_at TEXT    NOT NULL,
        original_size      INTEGER NOT NULL,
        compressed_size    INTEGER NOT NULL,
        PRIMARY KEY (depot_id, id)
      );
      CREATE TABLE IF NOT EXISTS manifest_files (
        depot_id    INTEGER NOT NULL,
        manifest_id INTEGER NOT NULL,
        file_id     INTEGER NOT NULL,
        FOREIGN KEY (depot_id, manifest_id) REFERENCES manifests(depot_id, id)
          ON UPDATE CASCADE ON DELETE CASCADE,
        FOREIGN KEY (file_id) REFERENCES all_files(id)
          ON UPDATE CASCADE ON DELETE CASCADE
      );
      CREATE TABLE IF NOT EXISTS all_files (
        id              INTEGER NOT NULL PRIMARY KEY,
        path            TEXT    NOT NULL,
        original_size   INTEGER NOT NULL,
        compressed_size INTEGER NOT NULL,
        chunks_count    INTEGER NOT NULL,
        flags           INTEGER NOT NULL,
        hash_sha1       INTEGER NOT NULL,
        link_target     TEXT    NOT NULL
      );
      CREATE UNIQUE INDEX IF NOT EXISTS all_files_idx ON all_files (
        path, original_size, compressed_size, chunks_count, flags, hash_sha1, link_target
      );
      """
    )
  return db_connection


class MySteamClient(SteamClient):
  """
  See also: <https://github.com/ValvePython/steamctl/blob/v0.9.0/steamctl/clients.py>
  """

  _LOG = logging.getLogger("SteamClient")
  credentials_db: Optional[sqlite3.Connection] = None

  def __init__(self) -> None:
    super().__init__()
    self.on(self.EVENT_NEW_LOGIN_KEY, self._handle_login_key_step2)

  def set_credential_location(self, path: Union[str, os.PathLike[str]]) -> None:
    super().set_credential_location(path)
    self.credential_location = path
    if self.credentials_db:
      self.credentials_db.close()
    self.credentials_db = sqlite3.connect(
      os.path.join(self.credential_location, "credentials.sqlite3")
    )
    self.credentials_db.row_factory = sqlite3.Row
    with self.credentials_db, contextlib.closing(self.credentials_db.cursor()) as db_cursor:
      db_cursor.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
          username  TEXT NOT NULL PRIMARY KEY,
          sentry    BLOB     NULL,
          login_key TEXT     NULL
        );
        """
      )

  # def _get_key_file_path(self, username: str) -> Optional[str]:
  #   if self.credential_location:
  #     return os.path.join(self.credential_location, f"{username}.key")
  #   else:
  #     return None

  def _get_key_file_path(self, username: str) -> Optional[str]:
    raise NotImplementedError("{self.__name__} uses a database for storing login keys")

  def _get_sentry_path(self, username: str) -> Optional[str]:
    raise NotImplementedError("{self.__name__} uses a database for storing sentries")

  def get_sentry(self, username: str) -> Optional[bytes]:
    if self.credentials_db:
      with self.credentials_db, contextlib.closing(self.credentials_db.cursor()) as db_cursor:
        db_cursor.execute(""" SELECT sentry FROM users WHERE username = ? LIMIT 1 """, (username,))
        result: sqlite3.Row = db_cursor.fetchone()
        if result and result[0]:
          assert isinstance(result[0], bytes)
          return result[0]
    return None

  def store_sentry(self, username: str, sentry_bytes: bytes) -> bool:
    if self.credentials_db:
      with self.credentials_db, contextlib.closing(self.credentials_db.cursor()) as db_cursor:
        try:
          db_cursor.execute(
            """ INSERT INTO users(username, sentry) VALUES (?, ?) """, (username, sentry_bytes)
          )
        except sqlite3.IntegrityError:
          db_cursor.execute(
            """ UPDATE users SET sentry = ? WHERE username = ? """, (sentry_bytes, username)
          )
        return True
    return False

  def get_login_key(self, username: str) -> Optional[str]:
    if self.credentials_db:
      with self.credentials_db, contextlib.closing(self.credentials_db.cursor()) as db_cursor:
        db_cursor.execute(
          """ SELECT login_key FROM users WHERE username = ? LIMIT 1 """, (username,)
        )
        result: sqlite3.Row = db_cursor.fetchone()
        if result and result[0]:
          assert isinstance(result[0], str)
          return result[0]
    return None

  def store_login_key(self, username: str, login_key: str) -> bool:
    if self.credentials_db:
      with self.credentials_db, contextlib.closing(self.credentials_db.cursor()) as db_cursor:
        try:
          db_cursor.execute(
            """ INSERT INTO users(username, login_key) VALUES (?, ?) """, (username, login_key)
          )
        except sqlite3.IntegrityError:
          db_cursor.execute(
            """ UPDATE users SET login_key = ? WHERE username = ? """, (login_key, username)
          )
        return True
    return False

  def _handle_login_key_step2(self) -> None:
    if self.username and self.login_key:
      self.store_login_key(self.username, self.login_key)

  def my_fancy_login_routine(self) -> bool:
    """
    See also: <https://github.com/ValvePython/steamctl/blob/v0.9.0/steamctl/clients.py#L42-L126>
    """
    result: EResult
    if not self.username:
      self.username = input("Username: ")
    if not self.login_key:
      self.login_key = self.get_login_key(self.username)
    result = self.relogin()
    if result != EResult.OK:
      password = getpass("Password: ")
      result = self.cli_login(self.username, password)
      if result != EResult.OK:
        print(f"Failed to log in. Error: {result!r}")
        return False
    return True

  def __enter__(self) -> MySteamClient:
    return self

  def __exit__(
    self,
    exc_type: Optional[Type[BaseException]],
    exc_value: Optional[BaseException],
    traceback: Optional[TracebackType],
  ) -> None:
    self.logout()


if __name__ == "__main__":
  main()
