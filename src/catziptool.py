# type: ignore

# Note: this script is incomplete! --print-hash is very likely broken.

import argparse
import contextlib
import hashlib
import io
import re
import sys
import zipfile


class DebugZipFile(zipfile.ZipFile):

  @property
  def debug(self):
    return 3

  @debug.setter
  def debug(self, value):
    pass


def very_hacky_and_idiotic_split(path):
  stdout = io.StringIO()
  with contextlib.redirect_stdout(stdout):
    try:
      with DebugZipFile(path, "r"):
        pass
    except zipfile.BadZipFile:
      return None
  match = re.search(r"^given, inferred, offset \d+ \d+ (\d+)$", stdout.getvalue(), re.MULTILINE)
  return int(match.group(1)) if match else None


def sane_split(path):
  with open(path, "rb") as fp:
    # Copied from <https://github.com/python/cpython/blob/v3.9.7/Lib/zipfile.py#L1316-L1339>
    try:
      endrec = zipfile._EndRecData(fp)
    except OSError:
      return None
    if not endrec:
      return None
    size_cd = endrec[zipfile._ECD_SIZE]
    offset_cd = endrec[zipfile._ECD_OFFSET]
    concat = endrec[zipfile._ECD_LOCATION] - size_cd - offset_cd
    if endrec[zipfile._ECD_SIGNATURE] == zipfile.stringEndArchive64:
      concat -= zipfile.sizeEndCentDir64 + zipfile.sizeEndCentDir64Locator
    return concat


def main():
  parser = argparse.ArgumentParser(
    description="A script for separating Zip files appended to executables."
  )
  parser.add_argument("zip_file", nargs="+")
  parser.add_argument("--use-hacky-impl", action="store_true")
  mode_group = parser.add_mutually_exclusive_group(required=True)
  mode_group.add_argument("--get-offset", action="store_true")
  mode_group.add_argument("--print-hash", choices=["exe", "zip", "both"])
  mode_group.add_argument("--truncate", choices=["exe", "zip"])
  mode_group.add_argument("--copy-exe", metavar="PATH")
  mode_group.add_argument("--copy-zip", metavar="PATH")
  args = parser.parse_args()

  any_errors = False

  for input_path in args.zip_file:
    zip_offset = (
      very_hacky_and_idiotic_split(input_path) if args.use_hacky_impl else sane_split(input_path)
    )
    if not zip_offset:
      print(f"{input_path}: not a zip file", file=sys.stderr)
      any_errors = True
      continue

    if args.get_offset:
      with open(input_path, "rb") as file:
        fsize = file.seek(0, io.SEEK_END)
      print(f"{zip_offset}-{fsize}  {fsize-zip_offset}  {input_path}")

    elif args.print_hash:
      with open(input_path, "rb") as file:
        hasher = hashlib.sha1()
        bytes_left = zip_offset
        while bytes_left > 0:
          chunk = file.read(min(io.DEFAULT_BUFFER_SIZE, bytes_left))
          if not chunk:
            break
          bytes_left -= len(chunk)
          hasher.update(chunk)
        print(f"{hasher.hexdigest()}  {input_path}")

    elif args.truncate == "exe":
      with open(input_path, 'rb+') as file:
        file.truncate(zip_offset)

    else:
      raise NotImplementedError()

  if any_errors:
    sys.exit(1)


if __name__ == "__main__":
  main()
