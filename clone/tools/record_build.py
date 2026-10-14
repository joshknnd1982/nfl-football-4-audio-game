"""Record tool versions and SHA-256 of a finished build in release/ (playbook 8.1). Inspired by Jim Kitchen's Brain.

Usage: python clone/tools/record_build.py   (any Python 3; reads %USERPROFILE%\\.kitchensinc-builds\\nfl4)
Writes release/build_manifest_64.txt and build_manifest_32.txt (every file: SHA-256, size, path) and
release/BUILD_INFO.md (tool versions, the exe hashes).
"""
import hashlib
import os
import subprocess
import sys

GAME = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILDS = os.path.join(os.path.expanduser("~"), ".kitchensinc-builds", "nfl4")
RELEASE = os.path.join(GAME, "release")
VENVS = os.path.join(os.path.expanduser("~"), ".kitchensinc-venvs")


def sha(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def tool_versions(bits):
    py = os.path.join(VENVS, f"nfl4-{bits}", "Scripts", "python.exe")
    code = ("import sys,struct,PyInstaller,pygame,win32api,importlib.metadata as m;"
            "print(sys.version.split()[0], struct.calcsize('P')*8, PyInstaller.__version__, pygame.version.ver, m.version('audioop-lts'))")
    out = subprocess.run([py, "-I", "-c", code], capture_output=True, text=True, env=dict(os.environ, PYGAME_HIDE_SUPPORT_PROMPT="1")).stdout.split()
    return dict(zip(["python", "bits", "pyinstaller", "pygame-ce", "audioop-lts"], out))


os.makedirs(RELEASE, exist_ok=True)
lines = ["# Build info: Brain clone", "",
         "Made by clone/tools/build.ps1 (PyInstaller, onedir, windowed); recorded by clone/tools/record_build.py.", ""]
for bits in (64, 32):
    folder = os.path.join(BUILDS, str(bits), "dist", "nfl4")
    if not os.path.isdir(folder):
        print("no build for", bits, file=sys.stderr)
        continue
    files = []
    for root, _, names in os.walk(folder):
        for name in sorted(names):
            path = os.path.join(root, name)
            files.append((os.path.relpath(path, folder).replace("\\", "/"), os.path.getsize(path), sha(path)))
    files.sort()
    with open(os.path.join(RELEASE, f"build_manifest_{bits}.txt"), "w", encoding="utf-8") as handle:
        handle.writelines(f"{digest}  {size:>10}  {rel}\n" for rel, size, digest in files)
    versions = tool_versions(bits)
    exe = next(f for f in files if f[0] == "nfl4.exe")
    lines += [f"## {bits}-bit", "",
              "- Tools: " + ", ".join(f"{k} {v}" for k, v in versions.items()),
              f"- nfl4.exe: {exe[1]} bytes, SHA-256 {exe[2]}",
              f"- Files: {len(files)}, {sum(f[1] for f in files) / 1e6:.1f} MB; full list with hashes in build_manifest_{bits}.txt", ""]
with open(os.path.join(RELEASE, "BUILD_INFO.md"), "w", encoding="utf-8") as handle:
    handle.write("\n".join(lines))
print("\n".join(lines))
