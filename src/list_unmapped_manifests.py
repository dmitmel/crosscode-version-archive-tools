from __future__ import annotations

import gevent.monkey

gevent.monkey.patch_all()

import contextlib
import os
import sqlite3
from typing import NewType, TypedDict

import yaml

import manifest_downloader

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULT_BRANCH_NAME = "public"

AppName = NewType("AppName", str)
AppId = NewType("AppId", str)
DepotId = NewType("DepotId", str)
DepotName = NewType("DepotName", str)
BranchName = NewType("BranchName", str)
VersionNumber = NewType("VersionNumber", str)
ManifestId = NewType("ManifestId", str)


class VersionsMappingFile(TypedDict):
  apps: dict[AppName, VersionsMappingApp]


class VersionsMappingApp(TypedDict):
  id: AppId
  depots: dict[DepotName, DepotId]
  branches: dict[BranchName, None]
  versions: dict[VersionNumber, dict[BranchName, dict[DepotName, ManifestId | list[ManifestId]]]]


def main() -> None:
  versions_mapping_data = load_versions_mapping()

  db_connection: sqlite3.Connection = manifest_downloader.connect_to_database()
  with db_connection, contextlib.closing(db_connection.cursor()) as db_cursor:
    for app in versions_mapping_data["apps"].values():
      mapped_manifests: set[tuple[int, int]] = set()
      for version_branches in app["versions"].values():
        for branch_manifests in version_branches.values():
          for depot_name, manifest_id in branch_manifests.items():
            manifest_ids = manifest_id if isinstance(manifest_id, list) else [manifest_id]
            for manifest_id in manifest_ids:
              mapped_manifests.add((int(app["depots"][depot_name]), int(manifest_id)))

      header_printed = False
      for depot_id, manifest_id, created_at, seen_by_steamdb_at in db_cursor.execute(
        """ SELECT depot_id, id, created_at, seen_by_steamdb_at FROM manifests """
      ):
        if (depot_id, manifest_id) not in mapped_manifests:
          if not header_printed:
            header_printed = True
            print(
              "Depot ID   Manifest ID          Created at                Seen by SteamDB at        SteamDB link"
            )
            print(
              "---------- -------------------- ------------------------- ------------------------- ------------------------------------------------------------------------------"
            )
          print(
            f"{depot_id:<10} {manifest_id:<20} {created_at:<25} {seen_by_steamdb_at:<25} https://steamdb.info/depot/{depot_id}/history/?changeid=M:{manifest_id}"
          )


def load_versions_mapping() -> VersionsMappingFile:
  with open(os.path.join(PROJECT_DIR, "data", "versions_mapping.yaml"), "r") as file:
    return yaml.safe_load(file)


if __name__ == "__main__":
  main()
