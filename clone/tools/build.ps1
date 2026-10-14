# Build Brain (PyInstaller, onedir, windowed) for 64-bit and 32-bit. This is inspired by Jim Kitchen's Brain.
# Usage: powershell -ExecutionPolicy Bypass -File clone\tools\build.ps1 [-Bits "64,32"]
# Builds from a COPY of clone\src in a scratch folder, so the build cannot see the source tree or the
# original files (playbook 8.1: catches files that are missing from the bundle).
# Output: %USERPROFILE%\.kitchensinc-builds\nfl4\<bits>\dist\nfl4\  (nfl4.exe, _internal\, assets\sounds\ beside the exe)
param([string]$Bits = "64,32")
$ErrorActionPreference = "Stop"
$clone = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$game = Split-Path -Parent $clone
# Outside OneDrive on purpose: a build folder holds thousands of files, and OneDrive syncing them slowed
# the test run (P9). Finished files (zip, checksums, build info) go to release\ in the game folder.
$buildRoot = Join-Path $env:USERPROFILE ".kitchensinc-builds\nfl4"
$venvs = Join-Path $env:USERPROFILE ".kitchensinc-venvs"

foreach ($b in ($Bits -split ",")) {
    $py = Join-Path $venvs "nfl4-$b\Scripts\python.exe"
    if (-not (Test-Path $py)) { throw "missing environment $py (run clone\tools\setup_envs.ps1)" }
    $root = Join-Path $buildRoot "$b"
    if (Test-Path $root) { Remove-Item -Recurse -Force $root }
    $srcCopy = Join-Path $root "src"
    New-Item -ItemType Directory -Force $srcCopy | Out-Null
    Copy-Item -Recurse (Join-Path $clone "src\nfl4") $srcCopy
    Get-ChildItem -Recurse -Directory -Filter "__pycache__" $srcCopy | Remove-Item -Recurse -Force
    Copy-Item (Join-Path $clone "tools\nfl4_entry.py") $root

    Push-Location $root
    try {
        & $py -I -m PyInstaller --noconfirm --clean --windowed --onedir `
            --name nfl4 --distpath dist --workpath work --specpath spec `
            --paths src `
            --add-data "$srcCopy\nfl4\speech\nvda_client;nfl4\speech\nvda_client" `
            --hidden-import win32com.client --hidden-import pythoncom --hidden-import pywintypes `
            --hidden-import win32timezone `
            --exclude-module tkinter --exclude-module pytest --exclude-module wx --exclude-module numpy `
            --exclude-module ssl --exclude-module _ssl --exclude-module _hashlib `
            --exclude-module pygame.font --exclude-module pygame.freetype --exclude-module pygame.image `
            --exclude-module pygame.imageext --exclude-module pygame.transform --exclude-module pygame.draw `
            --exclude-module pygame.mask --exclude-module pygame.pixelarray --exclude-module pygame.pixelcopy `
            --exclude-module pygame.scrap --exclude-module pygame._sdl2 `
            --exclude-module pygame.surfarray --exclude-module pygame.camera --exclude-module pygame.gfxdraw `
            nfl4_entry.py
        if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed for $b-bit" }
    } finally { Pop-Location }

    # Libraries that only the excluded pygame modules (image, font) and ssl need: PyInstaller's pygame hook copies
    # every DLL of the package, so the unused ones are deleted here (P10: 92 MB to 60 MB; the exe smoke test proves
    # nothing was missing).
    $internal = Join-Path $root "dist\nfl4\_internal"
    foreach ($name in @("SDL2_image.dll", "SDL2_ttf.dll", "freetype.dll", "libjpeg-62.dll", "libpng16-16.dll", "libtiff-5.dll",
                        "libwebp-7.dll", "libwebpdemux-2.dll", "libwebpmux-3.dll", "portmidi.dll", "libssl-3.dll", "libcrypto-3.dll",
                        "libssl-3-x64.dll", "libcrypto-3-x64.dll", "libssl-1_1.dll", "libcrypto-1_1.dll")) {
        foreach ($place in @($internal, (Join-Path $internal "pygame"))) {
            $file = Join-Path $place $name
            if (Test-Path $file) { Remove-Item -Force $file }
        }
    }
    # PyInstaller's bootloader is built with Control Flow Guard. A voice that emulates a CPU (SmoothTalker) generates code
    # at run time, and a CFG process dies with 0xC0000409 when it runs it (owner bug 2026-10-13, 64-bit build only).
    # python.exe has no CFG flag and runs such voices fine, so the flag is cleared (tools\clear_cfg_flag.py).
    & $py -I (Join-Path $clone "tools\clear_cfg_flag.py") (Join-Path $root "dist\nfl4\nfl4.exe")
    if ($LASTEXITCODE -ne 0) { throw "clear_cfg_flag failed for $b-bit" }

    # Sounds and attribution beside the exe: the player sees and can replace them (playbook 7.7).
    $out = Join-Path $root "dist\nfl4"
    $sounds = Join-Path $out "assets\sounds"
    New-Item -ItemType Directory -Force $sounds | Out-Null
    Copy-Item (Join-Path $clone "assets\sounds\*") $sounds
    Copy-Item (Join-Path $clone "README.md") (Join-Path $out "README.txt")
    Copy-Item (Join-Path $game "LICENSE") (Join-Path $out "LICENSE.txt")
    Copy-Item (Join-Path $game "SOUNDS_NOTICE.txt") $out
    Copy-Item (Join-Path $clone "THIRD_PARTY_NOTICES.txt") $out
    Write-Host "built $b-bit: $out"
}
