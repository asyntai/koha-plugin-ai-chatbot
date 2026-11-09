"""Builds the .kpz file that Koha installs and that the docs page offers.

Run:
    venv/Scripts/python.exe plugins/koha/build_release.py

Writes plugins/koha/dist/asyntai-koha.kpz and a copy in static/downloads. A .kpz
is a zip with the Koha folder at its top level. It holds no tests.
"""

import os
import shutil
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "Koha")
DIST = os.path.join(HERE, "dist")
DOWNLOADS = os.path.join(HERE, "..", "..", "static", "downloads")
NAME = "asyntai-koha.kpz"


def main():
    os.makedirs(DIST, exist_ok=True)
    out = os.path.join(DIST, NAME)

    count = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(SRC):
            dirs.sort()
            for name in sorted(files):
                full = os.path.join(root, name)
                rel = os.path.relpath(full, HERE).replace("\\", "/")
                zf.write(full, rel)
                count += 1

    shutil.copyfile(out, os.path.join(DOWNLOADS, NAME))
    print("%s\n%d files, %d bytes" % (out, count, os.path.getsize(out)))


if __name__ == "__main__":
    main()
