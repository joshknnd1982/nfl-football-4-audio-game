# NFL Football 4 clone: create or refresh the 64-bit and 32-bit Python environments (the kit's recipe; nfl4 P6 made
# them as plain commands, fixesforgames B-T29). Inspired by Jim Kitchen.
# Needs Python 3.14 64-bit and 32-bit installed for this user (py -3.14-64, py -3.14-32).
# Environments live in C:\Users\joshk\.kitchensinc-venvs, outside OneDrive (thousands of files)
# and outside AppData\Local (the Claude app redirects new folders there into its private storage).
# Run from anywhere:  powershell -ExecutionPolicy Bypass -File <this file>
$ErrorActionPreference = "Stop"
$req = Join-Path $PSScriptRoot "..\requirements.txt"
$root = Join-Path $env:USERPROFILE ".kitchensinc-venvs"
foreach ($bits in "64", "32") {
    $venv = Join-Path $root "nfl4-$bits"
    if (-not (Test-Path "$venv\Scripts\python.exe")) { py "-3.14-$bits" -m venv $venv }
    & "$venv\Scripts\python.exe" -m pip install -q --upgrade pip
    & "$venv\Scripts\python.exe" -m pip install -q --only-binary=:all: -r $req
    "nfl4-$bits ready: $venv"
}
