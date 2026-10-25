"""Make the portable zip and the checksums file for a release (playbook 8.2). Inspired by Jim Kitchen.

Usage: python game/tools/make_portable.py [version]      (any Python 3; default version from nfl4.VERSION)
Reads the builds in %USERPROFILE%\\.kitchensinc-builds\\nfl4\\{64,32}\\dist\\nfl4 (run build.ps1 first).
Writes release/nfl4-portable-<version>.zip (folders 64-bit and 32-bit, plus PORTABLE.txt) and
release/checksums.txt (SHA-256 of the setup file and the zip, whichever exist).
"""
import hashlib
import os
import re
import sys
import zipfile

GAME = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RELEASE = os.path.join(GAME, "release")
BUILDS = os.path.join(os.path.expanduser("~"), ".kitchensinc-builds", "nfl4")

PORTABLE_TXT = """My Brain by Josh Kennedy, inspired by Jim Kitchen
Portable version {version}

Unpack this zip anywhere (a folder you can write to, such as Documents or a USB stick).
Open the folder 64-bit if your Windows is 64-bit (almost all are) or 32-bit otherwise, and start nfl4.exe.
Nothing is installed and nothing is written to the registry.

Your settings, your own sounds and the log go to your AppData Roaming folder, in Kitchensinc Revival, then Brain,
the same place the installed version uses. Delete that folder by hand to remove them.

The zip is not code-signed. If Windows SmartScreen warns, choose More info, then Run anyway.
Read README.txt in the program folder for keys, speech settings and replacing sounds.

This is inspired by Jim Kitchen, who was blind from birth, made free games for the blind community and died in 2015.
Source and updates: https://github.com/joshknnd1982
"""


def version_from_source():
    text = open(os.path.join(GAME, "game", "src", "nfl4", "__init__.py"), encoding="utf-8").read()
    return re.search(r'VERSION = "([^"]+)"', text).group(1)


def sha(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    version = sys.argv[1] if len(sys.argv) > 1 else version_from_source()
    zip_path = os.path.join(RELEASE, f"nfl4-portable-{version}.zip")
    if os.path.exists(zip_path):
        os.remove(zip_path)
    top = f"nfl4-portable-{version}"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr(f"{top}/PORTABLE.txt", PORTABLE_TXT.format(version=version).replace("\n", "\r\n"))
        for bits, folder in (("64", "64-bit"), ("32", "32-bit")):
            root = os.path.join(BUILDS, bits, "dist", "nfl4")
            if not os.path.isdir(root):
                raise SystemExit(f"missing build {root} (run game\\tools\\build.ps1)")
            for base, _dirs, files in os.walk(root):
                for name in sorted(files):
                    full = os.path.join(base, name)
                    rel = os.path.relpath(full, root).replace(os.sep, "/")
                    z.write(full, f"{top}/{folder}/{rel}")
    lines = []
    for name in (f"nfl4-setup-{version}.exe", f"nfl4-portable-{version}.zip"):
        path = os.path.join(RELEASE, name)
        if os.path.exists(path):
            lines.append(f"{sha(path)}  {name}  ({os.path.getsize(path)} bytes)")
    with open(os.path.join(RELEASE, "checksums.txt"), "w", encoding="utf-8") as out:
        out.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
