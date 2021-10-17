from __future__ import annotations

import gevent.monkey

gevent.monkey.patch_all()

import contextlib
import html
import os
import re
import sqlite3
from datetime import datetime, timezone
from typing import IO, Optional

import mwclient

import list_unmapped_manifests
import manifest_downloader
from list_unmapped_manifests import AppName, BranchName, DepotName, ManifestId, VersionNumber

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

VERSION_HISTORY_WIKI_PAGE_ID = "Version_history"
DEPOTS_INFO = {
  368341: "Windows32",
  368342: "Linux32",
  368343: "Linux64",
  368344: "macOS",
  368349: "Windows64",
  368345: "Chinese Windows32",
  368346: "Chinese Linux32 (unused)",
  368347: "Chinese Linux64 (unused)",
  368348: "Chinese macOS (unused)",
  1517030: "A New Home DLC",
  1517031: "A New Home DLC (macOS)",
  1585790: "Manlea DLC",
  1585791: "Manlea DLC (macOS)",
  960310: "Ninja Skin DLC",
  916191: "Ninja Skin DLC (macOS)",
}
BRANCHES_INFO = {
  "public": "<the default branch>",
  "nwjs_old": "Might crash less often.",
  "nwjs_new": "Choose this if game is slow!",
}


def main() -> None:
  versions_mapping_data = list_unmapped_manifests.load_versions_mapping()
  crosscode_app = versions_mapping_data["apps"][AppName("crosscode")]

  wiki = mwclient.Site("crosscode.fandom.com", path="/")

  def wiki_url(path: str) -> str:
    return f"{wiki.scheme}://{wiki.host}{wiki.path}{path}"

  response = wiki.post("parse", page=VERSION_HISTORY_WIKI_PAGE_ID, prop="sections")
  version_header_regex = re.compile(r"^(\d+.\d+.\d+):")
  version_headers_mapping: dict[str, str] = {}
  for section in response["parse"]["sections"]:
    match = version_header_regex.search(section["line"])
    if match is not None:
      version_headers_mapping[match.group(1)] = section["anchor"]

  db_connection: sqlite3.Connection = manifest_downloader.connect_to_database()
  with db_connection, contextlib.closing(db_connection.cursor()) as db_cursor:

    with open("data/steam_manifests.md", "w") as output_doc:

      def esc(x: object) -> str:
        return html.escape(str(x))

      def render_branch_name(branch_name: str) -> str:
        return f"<code>{esc(branch_name)}</code>"

      def render_depot_id(depot_id: int) -> str:
        return f'<a href="https://steamdb.info/depot/{esc(depot_id)}/"><code>{esc(depot_id)}</code></a>'

      def render_manifest_id(depot_id: int, manifest_id: int) -> str:
        url = f"exported_manifests/{esc(app_id)}/{esc(depot_id)}/{esc(manifest_id)}.txt"
        # url = f"https://steamdb.info/depot/{esc(depot_id)}/history/?changeid=M:{esc(manifest_id)}"
        return f'<a href="{url}"><code>{esc(manifest_id)}</code></a>'

      def render_version(version: str) -> str:
        anchor = version_headers_mapping.get(
          version[:version.find("-")] if "-" in version else version
        )
        if anchor is not None:
          url = wiki_url(f"{VERSION_HISTORY_WIKI_PAGE_ID}#{anchor}")
          return f'<a href="{esc(url)}">{esc(version)}</a>'
        else:
          return esc(version)

      app_id = int(crosscode_app["id"])
      output_doc.write(
        f'# Steam manifests of app <a href="https://steamdb.info/app/{esc(app_id)}/"><code>{esc(app_id)}</code></a>\n'
      )
      output_doc.write("\n")

      output_doc.write("## Depots\n")
      output_doc.write("\n")
      output_doc.write("<table><thead>\n")
      output_doc.write("<tr><th>Depot</th><th>Note</th></tr>\n")
      output_doc.write("</thead><tbody>\n")

      table = TableBuilder()
      for i, (depot_name, depot_id) in enumerate(crosscode_app["depots"].items()):
        depot_id = int(depot_id)
        table.put(i, 0, render_depot_id(depot_id))
        table.put(i, 1, esc(DEPOTS_INFO.get(depot_id, "")))
      table.render_to_html(output_doc)

      output_doc.write("</tbody></table>\n")
      output_doc.write("\n")

      output_doc.write("## Branches\n")
      output_doc.write("\n")
      output_doc.write("<table><thead>\n")
      output_doc.write("<tr><th>Branch</th><th>Info</th><th>Depot</th><th>Manifest</th></tr>\n")
      output_doc.write("</thead><tbody>\n")

      table = TableBuilder()
      for branch_name in crosscode_app["branches"].keys():
        branch_latest_manifests: dict[DepotName, tuple[VersionNumber, list[ManifestId]]] = {}
        for version_num, version_branches in crosscode_app["versions"].items():
          for depot_name, manifest_id in version_branches.get(branch_name, {}).items():
            branch_latest_manifests.setdefault(
              depot_name,
              (version_num, manifest_id if isinstance(manifest_id, list) else [manifest_id])
            )

        last_row = table.row_count()
        table.put(
          last_row, 0, render_branch_name(branch_name), rowspan=len(branch_latest_manifests)
        )
        table.put(
          last_row,
          1,
          esc(BRANCHES_INFO.get(branch_name, "")),
          rowspan=len(branch_latest_manifests)
        )

        for i, (depot, (version, manifest_ids)) in enumerate(branch_latest_manifests.items()):
          depot_id = int(crosscode_app["depots"][depot])
          table.put(
            last_row + i, 2, f"{render_depot_id(depot_id)} {esc(DEPOTS_INFO.get(depot_id, ''))}"
          )
          table.put(
            last_row + i, 3, "<br>".join(
              f"{render_manifest_id(depot_id, int(manifest_id))} {render_version(version)}"
              for manifest_id in manifest_ids
            )
          )

      table.render_to_html(output_doc)

      output_doc.write("</tbody></table>\n")
      output_doc.write("\n")

      for branch_name in ("public", "nwjs_old", "nwjs_new"):
        depot_names = ("win32", "linux32", "linux64", "macos", "win64")

        output_doc.write(f"## Manifests ({render_branch_name(branch_name)})\n")
        output_doc.write("\n")
        output_doc.write("<table><thead>\n")
        output_doc.write("<tr><th>Version</th>")
        for depot_name in depot_names:
          depot_id = int(crosscode_app["depots"][DepotName(depot_name)])
          output_doc.write(f"<th>Manifest {esc(DEPOTS_INFO.get(depot_id, ''))}</th>")
        output_doc.write("<th>Uploaded at (YYYY/MM/DD hh:mm:ss) UTC</th></tr>\n")
        output_doc.write("</thead><tbody>\n")

        output_doc.write("<tr><th><em>Depot</em></th>")
        for depot_id in depot_names:
          depot_id = int(crosscode_app["depots"][DepotName(depot_name)])
          output_doc.write(f"<th>{render_depot_id(depot_id)}</th>")
        output_doc.write("<th></th></tr>\n")

        table = TableBuilder()
        for version_num, version_branches in crosscode_app["versions"].items():
          depot_manifests = version_branches.get(BranchName(branch_name))
          if depot_manifests is None:
            continue
          depot_manifests = {
            depot_name:
            list(map(int, manifest_id if isinstance(manifest_id, list) else [manifest_id]))
            for depot_name, manifest_id in depot_manifests.items()
          }

          last_row = table.row_count()
          table.put(last_row, 0, render_version(version_num))

          upload_dates: list[datetime] = []
          for i, depot_name in enumerate(depot_names):
            depot_id = int(crosscode_app["depots"][DepotName(depot_name)])
            manifest_ids = depot_manifests.get(DepotName(depot_name), [])
            table.put(
              last_row, 1 + i, "<br>".join(
                render_manifest_id(depot_id, manifest_id) for manifest_id in manifest_ids
              )
            )

            for manifest_id in manifest_ids:
              uploaded_at, = db_cursor.execute(
                """ SELECT seen_by_steamdb_at FROM manifests WHERE depot_id = ? AND id = ? """,
                (depot_id, manifest_id)
              ).fetchone()
              upload_dates.append(datetime.fromisoformat(uploaded_at))

          table.put(
            last_row, 1 + len(depot_names),
            esc(min(upload_dates).astimezone(timezone.utc).strftime("%Y/%m/%d %H:%M:%S"))
          )

        table.render_to_html(output_doc)
        output_doc.write("</tbody></table>\n")

        output_doc.write("\n")


class TableBuilder:

  __slots__ = ("cells",)

  def __init__(self) -> None:
    self.cells: list[list[TableCell]] = []

  def put(
    self,
    row: int,
    col: int,
    cell: object,
    rowspan: int = 1,
    colspan: int = 1,
    is_heading: bool = False,
  ) -> None:
    cell = TableCell(is_heading, cell)
    for _ in range(row - len(self.cells) + rowspan):
      self.cells.append([])
    for row_cells in self.cells[row:row + rowspan]:
      # Dammit, this is the one time I miss Lua tables
      for _ in range(col - len(row_cells)):
        row_cells.append(TableCell(False, None))
      for i in range(col, col + colspan):
        if i == len(row_cells):
          row_cells.append(cell)
        else:
          row_cells[i] = cell

  def get(self, row: int, col: int) -> TableCell:
    return self.cells[row][col]

  def row_count(self) -> int:
    return len(self.cells)

  def col_count(self, row: Optional[int] = None) -> int:
    if row is None:
      return max(map(len, self.cells))
    else:
      return len(self.cells[row])

  def total_cell_count(self) -> int:
    return sum(map(len, self.cells))

  def render_to_html(self, output: IO[str]) -> None:
    for row_cells in self.cells:
      for cell in row_cells:
        cell.already_rendered = False

    for row_idx, row_cells in enumerate(self.cells):
      output.write("<tr>\n")

      for col_idx, cell in enumerate(row_cells):
        if cell.already_rendered:
          continue
        cell.already_rendered = True
        rowspan, colspan = 1, 1

        for hscan_cell in row_cells[col_idx + 1:]:
          if hscan_cell is cell:
            colspan += 1
          else:
            break
        for vscan_row_cells in self.cells[row_idx + 1:]:
          vscan_row_slice = vscan_row_cells[col_idx:col_idx + colspan]
          if len(vscan_row_slice) != colspan:
            break
          if all(vscan_cell is cell for vscan_cell in vscan_row_slice):
            rowspan += 1
          else:
            break

        tag_name = "th" if cell.is_heading else "td"
        output.write(f"<{tag_name}")
        if rowspan > 1:
          output.write(f' rowspan="{rowspan}"')
        if colspan > 1:
          output.write(f' colspan="{colspan}"')
        output.write(">")
        if cell.contents is not None:
          output.write(str(cell.contents))
        output.write(f"</{tag_name}>\n")

      output.write("</tr>\n")


class TableCell:

  __slots__ = ("is_heading", "contents", "already_rendered")

  def __init__(self, is_heading: bool, contents: object) -> None:
    self.is_heading = is_heading
    self.contents = contents
    self.already_rendered = False

  def __repr__(self) -> str:
    return f"<{self.__class__.__name__}(is_heading={self.is_heading!r}, contents={self.contents!r}, already_rendered={self.already_rendered!r}) at {hex(id(self))}>"


if __name__ == "__main__":
  main()
