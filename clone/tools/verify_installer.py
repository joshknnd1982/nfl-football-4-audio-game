"""Scripted verification of the installer (P10 S10.3, playbook 8.2). Inspired by Jim Kitchen's Brain.

Runs the real setup file silently into a scratch folder (NOT AppData\\Local, which the Claude desktop app redirects),
current-user mode, and checks: files and registry entry, the installed exe starts and exits, settings and player sounds
survive an update over an older version (built here as 0.9.0), stale library files of the old version are removed,
a player's own file in assets\\sounds is kept, silent uninstall removes the program and keeps the settings, and
uninstall with /DELETEUSERDATA=1 removes them. The delete test touches the REAL per-user folder
(%APPDATA%\\Kitchensinc Revival\\Brain), so that folder is copied away first and put back at the end.
Usage: python verify_installer.py <report file>     (any Python 3; run from anywhere)
"""
import os
import shutil
import subprocess
import sys
import time
import winreg

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))     # python -I does not add the script's folder
import who_holds_folder      # same folder: which processes hold a folder's files (Restart Manager)

GAME = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RELEASE = os.path.join(GAME, "release")
import re
VERSION = re.search(r'VERSION = "([^"]+)"', open(os.path.join(GAME, "clone", "src", "nfl4", "__init__.py"), encoding="utf-8").read()).group(1)
SETUP = os.path.join(RELEASE, f"nfl4-setup-{VERSION}.exe")
ISCC = r"C:\Users\joshk\AppData\Local\Programs\Inno Setup 6\ISCC.exe"
SCRATCH = os.path.join(os.path.expanduser("~"), ".kitchensinc-builds", "nfl4", "install-test")
APP = os.path.join(SCRATCH, "app")
OLD_SETUP = os.path.join(SCRATCH, "nfl4-setup-0.9.0.exe")
DATA = os.path.join(os.environ["APPDATA"], "Kitchensinc Revival")
DATA_BACKUP = os.path.join(SCRATCH, "appdata-backup")
KEY = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\{6F2B8C14-3A7D-4E95-B1C0-5D9E47A82F36}_is1"
lines = []
failed = []


def check(name, ok, detail=""):
    text = ("PASS " if ok else "FAIL ") + name + (": " + str(detail) if detail else "")
    lines.append(text)
    print(text)
    if not ok:
        failed.append(name)


def run(args, timeout=300):
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout)


def install(setup, log):
    return run([setup, "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/CURRENTUSER", f"/DIR={APP}", f"/LOG={log}"])


def uninstall(extra=()):
    exe = os.path.join(APP, "unins000.exe")
    return run([exe, "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", *extra])


def registry_version():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, KEY) as key:
            return winreg.QueryValueEx(key, "DisplayVersion")[0]
    except OSError:
        return None


def wait_for(condition, seconds=45.0):
    """The uninstaller carries on in a temporary copy after its own process returns: poll instead of sleeping."""
    end = time.time() + seconds
    while time.time() < end:
        if condition():
            return True
        time.sleep(0.25)
    return condition()


def count(folder):
    return sum(len(files) for _, _, files in os.walk(folder)) if os.path.isdir(folder) else 0


def start_and_close(exe, data_dir, seconds=7):
    """Start the exe with a scratch data folder, wait, close its window politely, return the exit code."""
    env = dict(os.environ, NFL4_DATA_DIR=data_dir)
    proc = subprocess.Popen([exe], env=env, cwd=os.path.dirname(exe))
    time.sleep(seconds)
    alive = proc.poll() is None
    subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
    return alive


def start_in_program_folder(exe, data_dir, seconds=7):
    """Start the exe with the PROGRAM FOLDER as its working directory (what an old shortcut or a double click in
    Explorer does), the situation that used to lock the folder; return the process."""
    env = dict(os.environ, NFL4_DATA_DIR=data_dir)
    proc = subprocess.Popen([exe], env=env, cwd=os.path.dirname(exe))
    time.sleep(seconds)
    return proc


def close_politely(proc, limit=20.0):
    """Ask the window to close (WM_CLOSE, no /F), return how many seconds the process needed to be really gone (None: still there)."""
    started = time.time()
    subprocess.run(["taskkill", "/PID", str(proc.pid)], capture_output=True)
    try:
        proc.wait(limit)
    except subprocess.TimeoutExpired:
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
        return None
    return time.time() - started


def can_rename(folder):
    """A folder that something holds (open file, or a process whose working directory is in it) cannot be renamed."""
    probe = folder + "_probe_rename"
    try:
        os.rename(folder, probe)
        os.rename(probe, folder)
        return True
    except OSError:
        return False


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "installer_verify_report.txt"
    os.makedirs(SCRATCH, exist_ok=True)
    if os.path.exists(APP):
        shutil.rmtree(APP)
    if os.path.isdir(DATA):
        if os.path.exists(DATA_BACKUP):
            shutil.rmtree(DATA_BACKUP)
        shutil.copytree(DATA, DATA_BACKUP)
    check("setup file exists", os.path.exists(SETUP), f"{os.path.getsize(SETUP)} bytes")

    # older version for the update test (same AppId, version 0.9.0, written beside the real one, not in release/)
    build = run([ISCC, f"/DAppVersion=0.9.0", f"/O{SCRATCH}", os.path.join(RELEASE, "installer.iss")], timeout=600)
    check("older setup 0.9.0 compiled for the update test", build.returncode == 0 and os.path.exists(OLD_SETUP))

    try:
        # 1. fresh install of the OLD version, plant stale and custom files
        result = install(OLD_SETUP, os.path.join(SCRATCH, "install_old.log"))
        check("old version installs silently", result.returncode == 0 and os.path.exists(os.path.join(APP, "nfl4.exe")), result.returncode)
        check("registry says 0.9.0", registry_version() == "0.9.0", registry_version())
        stale = os.path.join(APP, "_internal", "stale_from_old_version.dll")
        open(stale, "w").write("old")
        mine = os.path.join(APP, "assets", "sounds", "my_own_sound.wav")
        open(mine, "w").write("player file")

        # 2. update over it with the real setup
        result = install(SETUP, os.path.join(SCRATCH, "install_new.log"))
        check(f"{VERSION} installs over 0.9.0", result.returncode == 0, result.returncode)
        check(f"registry says {VERSION}", registry_version() == VERSION, registry_version())
        check("stale library file of the old version is removed", not os.path.exists(stale))
        check("a player's own file in assets\\sounds is kept", os.path.exists(mine))
        check("42 shipped wavs and the license are installed",
              len([f for f in os.listdir(os.path.join(APP, "assets", "sounds")) if f.startswith("brain")]) == 42
              and os.path.exists(os.path.join(APP, "LICENSE.txt")) and os.path.exists(os.path.join(APP, "THIRD_PARTY_NOTICES.txt")))
        check("README.txt and uninstaller installed", os.path.exists(os.path.join(APP, "README.txt")) and os.path.exists(os.path.join(APP, "unins000.exe")))
        bits = "64-bit" if os.path.exists(os.path.join(APP, "_internal", "nfl4", "speech", "nvda_client", "x64")) else "32-bit"
        check("this 64-bit Windows got the 64-bit build", bits == "64-bit", bits)
        start_menu = os.path.join(os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs", "My Brain")
        check("Start menu entries made", os.path.exists(os.path.join(start_menu, "My Brain.lnk")) and os.path.exists(os.path.join(start_menu, "Uninstall My Brain.lnk")))

        # 3. the installed exe runs, with a fresh empty data folder: files are created
        fresh = os.path.join(SCRATCH, "fresh-data")
        shutil.rmtree(fresh, ignore_errors=True)
        alive = start_and_close(os.path.join(APP, "nfl4.exe"), fresh)
        check("installed exe starts and keeps running", alive)
        check("a missing settings folder is recreated with sounds.txt and a log",
              os.path.exists(os.path.join(fresh, "sounds", "sounds.txt")) and os.path.exists(os.path.join(fresh, "logs", "nfl4.log")))
        log_text = open(os.path.join(fresh, "logs", "nfl4.log"), encoding="utf-8", errors="replace").read()
        check("no warnings or errors in the installed exe's log", " ERROR " not in log_text and "Traceback" not in log_text)
        check(f"installed exe says version {VERSION}", f"Brain clone {VERSION} starting" in log_text)

        # 4. silent uninstall keeps settings
        marker = os.path.join(DATA, "Brain", "settings.txt")
        os.makedirs(os.path.dirname(marker), exist_ok=True)
        if not os.path.exists(marker):
            open(marker, "w").write("# Brain settings, format 1\n")
        before = count(DATA)
        result = uninstall()
        wait_for(lambda: registry_version() is None and not os.path.exists(APP))
        time.sleep(1)
        check("silent uninstall succeeds", result.returncode == 0, result.returncode)
        # owner bug 2026-10-13: the "My Brain" folder was left behind. The WHOLE program folder goes, even a file the
        # player put into it by hand (the player's own sounds belong in AppData, which is kept).
        check("the whole program folder is gone, nothing left in Program Files", not os.path.exists(APP), os.listdir(APP) if os.path.isdir(APP) else "")
        check("Start menu folder removed", not os.path.exists(start_menu))
        check("registry entry removed", registry_version() is None)
        check("settings kept by a silent uninstall", os.path.exists(marker) and count(DATA) == before, f"{before} files")

        # 5. closing the game must let go of its folder (owner bug 2026-10-13: "folder in use" until a restart)
        install(SETUP, os.path.join(SCRATCH, "install_again.log"))
        exe = os.path.join(APP, "nfl4.exe")
        proc = start_in_program_folder(exe, fresh)
        alive = proc.poll() is None
        needed = close_politely(proc)
        check("started from its own program folder it runs", alive)
        check("closing the window ends the process within 10 seconds", needed is not None and needed <= 10.0, needed)
        check("the program folder can be renamed right after closing (no process holds it)", wait_for(lambda: can_rename(APP), 3.0))
        holding = who_holds_folder.holders(who_holds_folder.files_under(APP))
        check("no process holds any file of the program folder after closing", not holding, holding)
        # 6. uninstalling while the game is still running must stop it and still remove everything
        proc = start_in_program_folder(exe, fresh)
        running = proc.poll() is None
        result = uninstall()
        wait_for(lambda: registry_version() is None and not os.path.exists(APP), 60.0)
        time.sleep(1)
        check("the game was running during the uninstall", running)
        check("uninstall while the game runs succeeds", result.returncode == 0, result.returncode)
        check("the running game was stopped by the uninstaller", proc.poll() is not None)
        check("uninstall while the game runs leaves no program folder", not os.path.exists(APP), os.listdir(APP) if os.path.isdir(APP) else "")
        if proc.poll() is None:
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)

        # 7. reinstall, uninstall with /DELETEUSERDATA=1 deletes the settings folder
        install(SETUP, os.path.join(SCRATCH, "install_final.log"))
        result = uninstall(["/DELETEUSERDATA=1"])
        wait_for(lambda: registry_version() is None and not os.path.isdir(os.path.join(DATA, "Brain")))
        check("uninstall with /DELETEUSERDATA=1 succeeds", result.returncode == 0, result.returncode)
        check("settings folder deleted by it", not os.path.isdir(os.path.join(DATA, "Brain")))
    finally:
        if os.path.exists(os.path.join(APP, "unins000.exe")):
            uninstall()
        shutil.rmtree(APP, ignore_errors=True)
        if os.path.isdir(DATA_BACKUP):
            shutil.rmtree(DATA, ignore_errors=True)
            shutil.copytree(DATA_BACKUP, DATA)
        lines.append(f"real per-user folder restored from the copy ({count(DATA)} files)")
    open(out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("ALL PASS" if not failed else "FAILED: " + ", ".join(failed))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
