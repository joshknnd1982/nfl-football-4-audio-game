## If something goes wrong

This section goes into the repository's README at P11 (S11.1). It is written for a player who uses a screen reader and the keyboard only.

NFL Football 4 writes down what it does, so that a problem on your computer can be found and fixed. The log stays on your computer. The game never sends it anywhere: you decide whether to send a file.

### Make a problem report (one file to send)

1. In the game press F9. This is the menu of the added functions.
2. Choose Speech settings (Enter), then press Down until you hear "Save a problem report", then press Enter.
3. Choose "Save the report without my saved games" and press Enter. Choose the second item instead if the problem has to do with a saved game or a season, and you are happy to send your saved game too.
4. The game says where the file is, for example "nfl4-problem-report-20261018-150000.zip", usually on your Desktop. Choose the next item and press Enter to open the folder.

If the game does not start at all, run the program once with the word `--problem-report` after its name (in a Command Prompt: `nfl4.exe --problem-report`). It makes the same zip without opening the game, and says where it is in a small message box.

### Where to send it

Open https://github.com/joshknnd1982, find the NFL Football 4 repository, choose Issues, then New issue. Say in a few words what happened and what you pressed, and attach the zip file. Please also say which screen reader you use and its version.

### What the report holds, and what it does not

- It holds: the newest three logs of the game (every key, menu step, spoken text and sound, in order), the crash log if the game ever stopped hard, a description of your Windows, your speech voices and your sound device, your settings file, and a list of your customization files and whether each is healthy.
- It does not hold: your Windows account name (it is replaced by `<user>`), your computer name, e-mail addresses, passwords, or the text you type (a coach's name is written as its length only). Your saved games and season files are included only if you chose the second item.
- If you do not want a log at all, F9, Speech settings, "Debug log" has four values: detailed (the default), trace (even more, only when you are asked for it), normal (only problems and the main events) and off (no log). With the log off, a problem that happens only on your computer cannot be fixed.

### Where the files are

The logs are in the `logs` folder inside `%APPDATA%\Kitchensinc Revival\NFL Football 4`. The game keeps the newest ten launches, each at most 10 MB. Uninstalling the game keeps them with your other files, like the settings; the uninstaller's delete switch removes them.
