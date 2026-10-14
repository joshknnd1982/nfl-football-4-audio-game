# Changelog

## 1.0.3 (2026-10-13)
- Much smaller again, with the same sound: pitch, panning and the generated beep no longer use numpy (28 MB of the install) but `audioop-lts`, a 30 KB package. The 64-bit program folder is 25 MB (was 54), the 32-bit one 21 MB (was 31), the installer 13.3 MB (was 22.9) and the portable zip 22.2 MB (was 39.6). Every sound is rendered within 2 of 32,768 steps of the numpy version (10,584 renders compared), so nothing can be heard to change.

## 1.0.2 (2026-10-13)
Version 1.0.1 was built and tested but never published; its changes are part of this version.
- Uninstalling removes the whole `My Brain` folder (it used to be left behind in Program Files when the game was still running, and was then "in use"). If My Brain is still running when you uninstall, the uninstaller closes it first. A file that is still in use at that moment is removed at the next restart, as a last resort.
- Closing My Brain now really ends it: the program never keeps its own folder as its working directory (Windows locks a folder that a process uses as its current folder, with nothing visible in Task Manager), it exits through a hard exit after saving its log, and a closing that hangs is ended after 6 seconds. The program folder can be renamed or deleted at once after closing.
- The shortcuts and the "Start My Brain now" box start the program from your Documents folder, not from the program folder.
- Much smaller install: the window toolkit is gone (a plain Win32 window through ctypes), and unused libraries (ssl, image and font libraries) are left out. The 64-bit program folder went from 92 MB to 54 MB and the 32-bit one from 63 MB to 31 MB.
- New setting in F3, the last item: "Sounds start: after the spoken prompt (original) or right away". With "right away" the sounds begin as soon as you press Enter in the panning menu, while "Press the space bar to stop" is still being spoken. Saved as `sound_start` in settings.txt.
- JAWS: the wait before the sounds start, when JAWS speaks the prompt, is now close to the real length of the speech (it was about half a second too long).
- No more silence between the spoken prompt and the first sound. SAPI 5 voices: the silence a voice adds at the end of its speech is cut (0.66 s with FlexVoice2 Bill, now 20 ms). NVDA: Brain waits until NVDA has really finished speaking (it waited a fixed guess of 3 seconds for a 1 second prompt, now about 0.16 s of silence).
- The 64-bit program no longer crashes when a voice that emulates a CPU, such as SmoothTalker, is chosen (the program was built with Windows' Control Flow Guard switched on).
- A voice that does crash Brain is set aside at the next start, so Brain always starts: it uses the first voice, says so, and the voice can be chosen again in F2.

## 1.0.0 (2026-10-13)
First complete version of My Brain by Josh Kennedy, inspired by Jim Kitchen.
- All of the original's behavior: 1 to 9 simultaneous sounds, four panning modes, random wavs at random pitch, keys, speech prompts, exit.
- Added: F1 help, F2 speech settings (any SAPI 5 voice, rate, volume, pitch, output), F3 sounds (volume, pitch variation, listen, reload, check, restore), F4 about; settings and sound files in `%APPDATA%\Kitchensinc Revival\Brain` with self-healing.
- Speech through SAPI 5, NVDA and JAWS. JAWS: fast interruption while arrowing through menus (a flushed SayString; JAWS 2026's StopSpeech does nothing).
- Installer (Inno Setup, 64-bit and 32-bit in one setup) and portable zip.
