# Development

## Files

```
Koha/                     the plugin, the only folder in the .kpz file
t/settings.t              reads the settings code, runs without Koha
t/00-load.t               loads the plugin, needs the Koha source
build_release.py          writes dist/asyntai-koha.kpz
tests/test_koha.py        end to end test of the real staff forms and OPAC pages
tests/test_browser.py     the same flow in real Chrome, and one chat question
```

## Test rig

The rig is koha-testing-docker (KTD), the official Koha test containers, in WSL.

```
git clone https://gitlab.com/koha-community/koha-testing-docker.git
git clone --branch 26.05.x --single-branch --depth 1 https://git.koha-community.org/Koha-community/Koha.git koha-26.05
export KTD_HOME=$PWD/koha-testing-docker SYNC_REPO=$PWD/koha-26.05 PROJECTS_DIR=$PWD LOCAL_USER_ID=1000
cd koha-testing-docker && cp env/defaults.env .env
sed -i "s/^KOHA_IMAGE=.*/KOHA_IMAGE=26.05/" .env
bin/ktd --name koha up -d && bin/ktd --name koha --wait-ready 600
```

The OPAC is at http://127.0.0.1:8080 and the staff interface is at http://127.0.0.1:8081. The KTD test login is `koha` with password `koha`.

## Run the tests

```
prove -l t/
python build_release.py
python tests/test_koha.py
python tests/test_browser.py install
python tests/test_browser.py chat
```

## Traps

- `LOCAL_USER_ID` must not be 0. Apache refuses to run as root, and the container stops. A root WSL shell gives 0 from `id -u`, so set it to 1000 and give that user the Koha source folder.
- `/tmp` in the container is a tmpfs, so `docker cp` to `/tmp` fails. Pipe a tar file or a script through `docker exec -i`.
- KTD runs the content security policy in `report-only` mode. A normal install has it off.
- The OPAC and the staff interface share cookies on 127.0.0.1, so a browser signed in to the staff interface is also signed in to the OPAC. `tests/test_koha.py` uses separate sessions.
- `wsl --shutdown` stops the containers. Other work on the same machine can do this.
