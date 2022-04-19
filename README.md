# The CrossCode Version Archive toolchain

## Useful links

- <https://crosscode.gamepedia.com/Version_history>
- <https://crosscode.fandom.com/wiki/Steam_depots>
- <https://crosscode.fandom.com/wiki/Version_history_(consoles)> (<https://www.youtube.com/watch?v=KfBzlzvt8RU>)
- <https://steamdb.info/app/368340/depots/>
- <https://steamdb.info/depot/368341/>
- <https://www.sqlitetutorial.net/>

## Instructions for myself

### What to do if a new version of the game comes out

(I need to automate this)

1. `$ poetry run python src/manifest_downloader.py open-steamdb-pages`
2. On each page, determine the manifest IDs (and seen-by-SteamDB dates) of the update by running the script [`extras/steamdb_extract_manifests_table.js`](extras/steamdb_extract_manifests_table.js) in the devtools console. There will most likely be two new manifests, one for the `public` branch and one for the `nwjs_old` branch. SteamDB only parses manifests on the `public` branch, so they can be easily told apart by a "No such change" error on the manifest from `nwjs_old`. Otherwise check file listings - new nw.js versions have a large dynamic library containing most of the Chromium code (`nw.dll`, `lib/libnw.so`) and a tiny launcher executable, older ones are compiled to a standalone executable.
3. The script will generate YAML, paste it into the relevant sections of the [`data/input_manifests.yaml`](data/input_manifests.yaml) file for each depot.
4. `$ poetry run python src/manifest_downloader.py update`
5. `$ poetry run python src/manifest_downloader.py export`
6. Record the manifest IDs of the new game version and of the updated DLCs (if any) in [`data/versions_mapping.yaml`](data/versions_mapping.yaml).
7. `$ poetry run python src/make_wiki_tables.py`
8. Diff file listings to see if the bundled nw.js has been, in fact, updated. If yes - update [`data/nwjs_versions.md`](data/nwjs_versions.md). Also the script [`extras/process_versions_dumper.html`](extras/process_versions_dumper.html) can be used for this.
9. Download the 32-bit Windows version for inclusion in the version archive with [DepotDownloader](https://github.com/SteamRE/DepotDownloader/releases/latest): \
   `$ dotnet DepotDownloader.dll -app 368340 -depot 368341 -manifest <ID> -username dmitmel -remember-password`
10. Add the new version to the archive:
    ```bash
    version="X.Y.Z"
    cd ~/all-crosscode-versions/
    rm -rvf assets favicon.png package.json
    cp -rv ~/SteamGames/CrossCode/{assets,favicon.png,package.json} .
    find assets favicon.png package.json -type f -print0 | xargs -0 chmod -v -x
    crosslocale mass-json-format -i assets package.json
    # Special case for 0.7.0: dos2unix assets/js/game.min.js
    prettier assets/js/game.compiled.js >| assets/js/game.formatted.js
    git add --all
    git commit -m "$version"
    git tag "$version"
    git push origin master "$version"
    sync
    ```
    (at the time of writing the version of Prettier is 2.4.1)
11. Upload a CrossLocalE scan:
    ```bash
    version="X.Y.Z"
    cd ~/crosscode/crosscode-crosslocale-scans/
    crosslocale scan ~/all-crosscode-versions/assets/ --compact -o scan-"$version".json
    git add --all
    git commit --amend --no-edit
    git push --force
    ```
