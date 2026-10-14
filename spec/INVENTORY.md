# Inventory of the original files (S1.1, 2026-10-13)

Files are in `original/` (read-only attribute set). They were moved there from the game folder root with a hash check: SHA-256 of all 28 files before and after the move were identical (`spec/ORIGINAL_SHA256.txt`). Dates 2013-09-13 are the file dates of the owner's copy.
The `copy matches source` column of `work/inventory.md` is meaningless in this run (the tool compared the folder with itself); the before/after hash comparison is the proof.
Malware scan: Microsoft Defender (MpCmdRun 4.18.26080.4, custom scan of `original/`, remediation disabled): found no threats (2026-10-13).

| file | bytes | type | SHA-256 |
|---|---|---|---|
| football.exe | 581632 | Windows PE executable | 7c42bf7eb22e64a13ed39977cd20ee6c156437b469b4c3d97b8057ae590b6a6c |
| football.txt | 11199 | text | 45fff0d65a7d4fb4d8e7ca2f962117719b20969ab33069ac13efcf95565049a8 |
| foot0.wav | 75256 | WAV audio | fc0084a874bca555db6891e3a47effd9b53967b6b6420c8b2d8f7e8ae8f6abf2 |
| foot1.wav | 429650 | WAV audio | 3a0da3e9b06a97ac402626649f584eb5032ae07fcb2d7d9caccf60e53a902665 |
| foot2.wav | 176518 | WAV audio | 280d817ac2ede4e74a13e5d9eb2b5529cd7cfad83471f564ebfdf9f38504f762 |
| foot3.wav | 271862 | WAV audio | 237b64a345495211df141dc84a262887554b1c05e2a999e87e81ff0fd669531d |
| foot4.wav | 379378 | WAV audio | a2292ff9c397d7c7e1cd5cedaf019a686aaf01a6a64bf109c73be46dfda2fbb8 |
| foot5.wav | 273538 | WAV audio | 3c2a30b0f9290bfae409c4e5bcc0d1e2f29aa557d24f610aaa5705524b66f527 |
| foot6.wav | 258546 | WAV audio | cc71b7d00c3e8e70e3521902ad244b42679ff007dc0fc037500358c843d4e503 |
| foot7.wav | 53038 | WAV audio | bf50ed61e3e977feec51b3bded6a142a1f0a72f5c12c09755441573cb76472aa |
| foot8.wav | 123598 | WAV audio | 1c9e973693f86dcfbeba73165eba0c7ccf53bd23a75486c02bf2ea2b6a91557e |
| foot9.wav | 132418 | WAV audio | 4437a59b87b0ada968d2b61d84f34ac5dbad4d534b1ffd1466962c32ca937a56 |
| foot10.wav | 23878 | WAV audio | 0b36ab668d64852630d2abc916603695a2e502a7602cc54807b0fe567c00c9a2 |
| foot11.wav | 172106 | WAV audio | bc893155513ccb4700f8bc451acf2dd6367c1cb25edcd4377ff74d46cc9be9aa |
| foot12.wav | 35398 | WAV audio | 36f8385a0e2bfb8455515360f06a352ec37972d7374438ed52ff852e259a87d7 |
| foot13.wav | 8180 | WAV audio | 863f59b08d05c90063d07c8cb4ba08b46f87edf2e68d76096db3854a3617d46f |
| foot14.wav | 194158 | WAV audio | db98e6c87ec43d60a212edf3359583b4afa6c89c5bbfbbbc4c1e66b28ff4b266 |
| foot15.wav | 11300 | WAV audio | 6b0d32310306e0e49cf16f33e6125207c49fa1ba1a7ebf18ab6a2f42bad6e263 |
| foot16.wav | 16830 | WAV audio | 83301ec64a4856ec01d239f172830ae48d276e4a4866ea71ecc2b9c09868652b |
| foot17.wav | 6650 | WAV audio | a8df76abac41af0a8a2982166711eed8f9d102b03ffcd84fea2a05e8bf287c34 |
| foot18.wav | 3856 | WAV audio | b7de46a5cbb44cd2802b23ec689df1bad0486005c90a71ea39cf68c1cb5e3afe |
| foot19.wav | 2100 | WAV audio | eccee1dcfcb02c386cc7364dfe3fdc37d71d50db63294da348d56bbfc31a1471 |
| foot20.wav | 2326 | WAV audio | b79534aef2eafd00aaba5860eca6ecee234aead433af16a024d1e2504b1fb77b |
| foot21.wav | 7814 | WAV audio | 59d42ae422f5625b124fb72071e303712f1b4843e943c0801f3a8fef176e7504 |
| foot22.wav | 10804 | WAV audio | 21764e38450c6f768c860f7e23607404010e005bbf7ecd4df8ba5c375eabcbec |
| foot23.wav | 2876 | WAV audio | bc19e6f1a2d567810c00c3bdf2f8643bb385e0def72e75bfd29d21318892fe91 |
| foot24.wav | 2346 | WAV audio | ea0843af6bf2c41ac1fd1395e12fb51e02957076d57f4d00108fdd3ad0c1f004 |
| foot25.wav | 126386 | WAV audio | 58e91e13f4a34cf8634d9cf36eae93fa85c8157d49ed05441ea8f38e12678eeb |

## football.exe
- PE32 (x86), link time 2013-09-13T13:22:20+00:00 UTC, subsystem 2 (GUI), entry 0x1a08.
- Toolchain: Visual Basic 6.00.8041, NATIVE code (not p-code), Microsoft Linker 6.0 (Detect It Easy 3.21). VB5! header present; runtime MSVBVM60.DLL, 137 imports, no p-code engine imports. Project path string `C:\Program Files\Microsoft Visual Studio\VB98\football.vbp`, project name `football`.
- No packer (no UPX or similar section names, no overlay). Sections: .text 566,852 bytes (entropy 5.54), .data 3,192, .rsrc 2,272.
- Version resource: CompanyName Kitchens Inc, ProductName football, FileVersion 1.00. Resources: icon, group icon, version only (no form or binary resources of its own).
- One form (`Form1`), 64 methods named in the method table; native code range 0x41bbd0 to 0x48ad40 (455,024 bytes, 64 procedures by prologue scan; the two largest are 158,960 and 115,456 bytes).
- Type library reference: Microsoft Speech Object Library (`C:\WINDOWS\system32\SAPI.DLL`, type library C866CA3A-32F7-11D2-9602-00C04F8EE628), class SpVoice (SAPI 5).
- Sound: DirectX 8 for Visual Basic by class ID only (DirectX8 class E7FF1300-96A5-11D3-AC85-00C04FC2C602, DirectSound8 9F76FB00-8E92-11D1-8808-00C04FC2C603, secondary buffer 9F76FB01-8E92-11D1-8808-00C04FC2C603). Neither class nor dx8vb.dll is registered or present on this PC.
- Also uses: Shell.Application (late-bound, to find the Documents folder), rtcShell (launches `gamemenu.exe`), file I/O (Open, Line Input, Input, Print, Get, Put, Kill, MkDir, Dir), Randomize and Rnd, Timer, Beep, MsgBox.

## Other files
- football.txt: the player's help and readme (11,199 bytes, plain text). It is also embedded in the exe as strings. Contains Jim Kitchen's e-mail address, phone number and town: scrub before publishing (fixesforgames B-R2).
- foot0.wav to foot25.wav: 26 files, 2,800,810 bytes, 48.1 seconds in total; see `extracted/audio_info/wav_properties.md`.
- Not in the folder but named by the program or its readme: `uninfoot.bat` (uninstaller named in football.txt), `gamemenu.exe` (the Kitchensinc game menu that launches this game), data files made at run time (`footplay.txt`, `football.sav`, `football.vol`, `football.gtp`, `footbal0.dat` to `footbal5.dat`, `footballlog.txt`).