# NFL Football 4

An audio-only American football game for blind players, by Josh Kennedy, inspired by Jim Kitchen. You play with the keyboard. The game tells you everything in speech and sound, through your screen reader or the Windows voices. There are no pictures.

**Status: a work in progress.** There is no release yet and no installer to download. The game can be run and built from the source in this repository. Test builds exist for the maintainer only.

## Inspired by Jim Kitchen

This is inspired by Jim Kitchen. Jim Kitchen was blind from birth and made many free games for the blind community. He died in 2015. This game is loosely inspired by his "NFL football version 4". It is new code, written from a description of how his program behaves, and it contains none of his program code. It plays his original sound files (see "Sounds and rights" below).

## Two ways to play

- **Classic** is the original game exactly as Jim Kitchen made it: the same menus, keys, plays, pace and sounds.
- **N. F. L. rules** is the default for a new player. The way you play stays like the original (short spoken menus, the same function keys), and the game adds the real National Football League:
  - a real game clock of 15 minutes a quarter, time outs and the two-minute warning;
  - penalties you may accept or decline, onside kicks, quarterback runs, replay challenges and the replay official's reviews;
  - every real NFL play, grouped into lists you reach with Right and M, each with a plain description (D) for people who do not know football, and a W key that says which play the playbook would most likely pick;
  - playbooks in seven styles, for your team and for the computer's;
  - the real head coaches and players of the 32 teams, so you type no names;
  - a radio-style broadcast: the announcer's banter and a color commentator in a voice of their own, stadium sounds, and a referee who announces over a microphone;
  - a Franchise: a league of 32 teams that lasts from season to season, with the real 2026 schedule and bye weeks, ratings, aging, the draft, contracts and the salary cap, free agency, trades until the deadline, injuries, coaches and history.

Choose the rules in the game: press F9, then Rules. The full description is in [clone/README_nfl_rules_and_franchise.md](clone/README_nfl_rules_and_franchise.md).

## Requirements

- Windows 10 or 11, 64-bit or 32-bit.
- A screen reader (NVDA or JAWS) or the Windows speech voices (SAPI 5), and speakers or headphones.
- To run it from source: Python 3.14. The libraries are listed in [clone/requirements.txt](clone/requirements.txt).

Speech output is automatic: NVDA when it runs, else JAWS, else the game's own Windows voices. When a screen reader runs and you have not chosen yet, the game asks once whether to speak through it. The maintainer plays it with NVDA. The Windows voices (SAPI 5) are covered by automatic tests. JAWS support is built and tested against a stand-in; it has not yet been checked with the real JAWS in the built game.

## Run it from source

In a Command Prompt or PowerShell:

1. `cd clone`
2. `py -3.14 -m venv .venv`
3. `.venv\Scripts\python -m pip install -r requirements.txt`
4. `cd src`
5. `..\.venv\Scripts\python -m nfl4`

The game opens a small window that receives the keys, and speaks its welcome.

## Changing the speech, the volume and the sounds

- F9 opens the added functions: the speech settings (engine, voice, rate, pitch, volume), the sounds, the names and the banter, the rules, the Franchise and the about text.
- F11 adjusts the volumes of the voices and the sounds. F12 changes the voices. The Control key adjusts the rate of speech.
- Your settings, saved games, own sounds, customization files and logs are in `%APPDATA%\Kitchensinc Revival\NFL Football 4`. The program folder holds only program files.
- You can change team names, division names, surnames and the announcer's banter, add banter lines of your own, add sounds to the numbered families of sounds the game draws among, and replace the stadium, referee and whistle sounds with your own files. [clone/CUSTOMIZE.md](clone/CUSTOMIZE.md) says how.

## Documents

- [clone/README_keys.md](clone/README_keys.md): every key, as below.
- [clone/README_nfl_rules_and_franchise.md](clone/README_nfl_rules_and_franchise.md): the N. F. L. rules, the Franchise, saved games, the real names, the broadcast.
- [clone/PLAYS_GUIDE.md](clone/PLAYS_GUIDE.md): every play with a short plain description.
- [clone/CUSTOMIZE.md](clone/CUSTOMIZE.md): names, banter and sounds.
- [clone/README_if_something_goes_wrong.md](clone/README_if_something_goes_wrong.md): problem reports.
- [spec/](spec/): the specification, the decisions and the research the game is built from.

<!-- keys:start -->
## Keys

Every key the game handles, where it works and what it does. This list is made from the game's master list of keys (`clone/src/nfl4/game/key_list.py`); the same keys are spoken by F5 (the special keys) and F6 (the game instructions). Keys marked "N. F. L. rules" work only with the N. F. L. rules; Classic is the original game exactly.

- **F1**: Anywhere. Repeats the current prompt, then says where the help is. (original game)
- **F2**: Anywhere, and in questions and lists. Plays the instant replay of what was just said. (original game)
- **F3**: Anywhere in a game. Says the score. (original game)
- **F4**: Anywhere in a game. Says the game clock; with the N. F. L. rules it also says whether the clock is running. (original game)
- **F5**: Anywhere. Reads the special key instructions. (original game)
- **F6**: Anywhere. Reads the game instructions. (original game)
- **F7**: Anywhere. Reads the football words and hints; in Classic it also describes the original's plays. (original game)
- **F8**: Anywhere. Switches the comments off and on. (original game)
- **F9**: Anywhere. Opens the added functions: the speech settings, the sounds, the names and the banter, the rules, the franchise and the about text. (added)
- **F11**: Anywhere. Adjusts the volume of the voices and the sounds: Up and Down, Enter for the next (with the N. F. L. rules and the broadcast on, the volumes of the color commentator and the referee too). (original game)
- **F12**: Anywhere. Changes the voices (with the N. F. L. rules and the broadcast on, the voices of the color commentator and the referee too). (original game)
- **Control**: Anywhere. Adjusts the rate of speech: Up and Down, Enter to keep it. (original game)
- **Escape**: Anywhere. Exits the game; in a play menu it asks whether you concede the game; in the F9 menus and lists it goes back. (original game)
- **Alt, or F10**: Anywhere. Does what Escape does. (original game)
- **Up and Down**: In every menu. Move to the previous or the next item; they go around from the last item to the first. (original game)
- **Digits 1 to 9 and 0**: In the play menus and the kick off menu. Make the item with that number the current item; 0 is the tenth. (original game)
- **Enter**: In every menu and question. Takes the current item or the answer. (original game)
- **Y, N, Tab**: In a yes or no question. Y says yes and N says no at once; Up, Down or Tab change the answer and Enter takes it. (original game)
- **H, T, R, K**: At the coin toss, and at the coin toss before over time in the N. F. L. rules. H is heads and T is tails; then R receives the kick off and K kicks off. (original game)
- **Letters, digits, Backspace**: When you type a name. Letters and digits type, Backspace deletes the last one and Enter finishes. (original game)
- **Left, Right, Page Up, Page Down, Home, End, Space, letters**: In the F9 menus and lists. Left and Right change a value, Page Up and Page Down move ten items, Home and End go to the ends, Space chooses where that fits, and typing letters jumps to a name. (added)
- **Page Up and Page Down**: In the saved game, franchise and season questions. Turn to the previous or the next page of a long list; F1 says the question again and F2 plays the replay. (added)
- **T** (N. F. L. rules only): Anywhere in a game being played, until the play is run. Calls your time out at once; a call during a running play is granted when the play ends. (added)
- **Backspace or Left, B** (N. F. L. rules only): In a list of plays or a playbook group. Go back one level, from a list of plays to the menu it came from; B chooses the Back item. (added)
- **Right** (N. F. L. rules only): In the offense and defense menus of the N. F. L. rules with a playbook. On a play family opens its lists of plays, and in a list goes to the family's next list; on Punt it opens the kinds of punts and the fake punts, and on Field Goal the fake field goals. (added)
- **Plus and Minus** (N. F. L. rules only): In a list of plays. Plus adds the current play to your favourites and minus takes it off; the main row's plus and the keypad's plus both work. (added)
- **Enter on a play type** (N. F. L. rules only): In the offense and defense menus of the N. F. L. rules with a playbook. Lets the playbook pick a play of that type for the down, the distance and the field position, and tells you its name; Enter on a play in a list calls that play. (added)
- **M** (N. F. L. rules only): In the offense and defense menus of the N. F. L. rules with a playbook. Opens More Plays, which holds every other list of plays; on defense it holds every list of defensive calls and the situation defenses. (added)
- **F, A, K, P, O, N** (N. F. L. rules only): In the offense and defense menus of the N. F. L. rules with a playbook. F opens your favourites, A calls your last play again, K kneels down and P spikes the ball when they help, O opens formation and tempo, and N in More Plays finds a play by its name; the defense menu has F, A, O and N as well, and on fourth down P opens the kick defense. (added)
- **W** (N. F. L. rules only): In the offense and defense menus of the N. F. L. rules with a playbook. Says which play the playbook would most likely pick for the play type you are on, or call in the list you are in, and how often; it draws nothing, so asking changes nothing in the game. (added)
- **R** (N. F. L. rules only): In the offense menu of the N. F. L. rules with a playbook. Chooses who your next pass goes to: the first item keeps the play's own pick, then the receivers, and the first two running backs when the play can throw to one. (added)
- **L** (N. F. L. rules only): In the defense menu of the N. F. L. rules with a playbook. Chooses who blitzes on your next blitz call: the first item picks a player by chance. (added)
- **Letters, Backspace, Enter** (N. F. L. rules only): In Find a Play by Name. Type the first letters of a word of the play's name, here T is a letter too; Backspace deletes the last one and Enter finds the plays. (added)
- **S** (N. F. L. rules only): In a play menu. Chooses the Save Game item, the last one; at the penalty question it saves the game with the question kept. (added)
- **C** (N. F. L. rules only): In a play menu. Chooses Challenge the Ruling, or says why you cannot challenge. (added)
- **D** (N. F. L. rules only): In a play menu and the kick off menu. Says a plain description of the current item for a person who knows nothing of football; the menu stays on the item. (added)
- **A and D** (N. F. L. rules only): At a penalty question. A accepts the penalty and D declines it; Up and Down change the answer and Enter takes it. (added)
- **8, 9 and 0** (N. F. L. rules only): In the offense menu with quarterback runs. 8 is the quarterback sneak, 9 the keeper and 0 the draw. (added)
<!-- keys:end -->

## If something goes wrong

NFL Football 4 writes down what it does, so that a problem on your computer can be found and fixed. The log stays on your computer. The game never sends it anywhere: you decide whether to send a file.

1. In the game press F9, choose Speech settings, press Down until you hear "Save a problem report", then press Enter.
2. Choose "Save the report without my saved games" (or the second item if the problem has to do with a saved game and you are happy to send it too).
3. The game says where the zip file is, usually on your Desktop.
4. If the game does not start at all, run `nfl4.exe --problem-report` (or `python -m nfl4 --problem-report` from source). It makes the same zip without opening the game.
5. Open a new issue in this repository, say in a few words what happened and what you pressed, which screen reader and version you use, and attach the zip.

The report holds the newest logs, a description of your Windows, voices and sound device, your settings and the names of your customization files. It does not hold your Windows account name (it is replaced by `<user>`), your computer name, e-mail addresses, passwords or the text you type. More in [clone/README_if_something_goes_wrong.md](clone/README_if_something_goes_wrong.md).

## Sounds and rights

- The 26 sound files `foot0.wav` to `foot25.wav` in `clone/assets/sounds` are Jim Kitchen's original wav files from his game "NFL football version 4", copied unchanged (each checked by its SHA-256 fingerprint against the original). The maintainer, Josh Kennedy, says that Jim Kitchen gave him permission to use the wav files of his games, but the original e-mail is lost, so that permission cannot be shown to anyone. The files are included on the maintainer's own responsibility. If a rights holder asks for them to be removed, they will be removed.
- The 19 stadium, crowd and whistle sounds in `clone/assets/sounds_nx` are generated by this project's own code. They are new work under the MIT license.
- The program code, tests and documents are new and under the MIT license (file `LICENSE`). The license does not cover Jim Kitchen's wav files. Third-party parts keep their own licenses: see [clone/THIRD_PARTY_NOTICES.txt](clone/THIRD_PARTY_NOTICES.txt) and [SOUNDS_NOTICE.txt](SOUNDS_NOTICE.txt).

## Names, trademarks and the NFL

- The names of the real teams, head coaches and players are facts (names, positions, numbers), used descriptively, from the teams' public websites on 2026-10-22. This project is not made, endorsed or supported by any team or by the National Football League, and uses no ratings, photographs or logos. The sources and their terms are in [spec/NFL_NAMES_RESEARCH.md](spec/NFL_NAMES_RESEARCH.md). The 2026 schedule is described in [spec/NFL_SCHEDULE_RESEARCH.md](spec/NFL_SCHEDULE_RESEARCH.md).
- The playbooks and the Franchise are inspired by the playbooks and franchise ideas of Madden NFL. Madden NFL is a trademark of Electronic Arts. This project is not made, endorsed or supported by EA or the NFL. The plays are football concepts named in plain football words; many of them are also in the playbooks of Madden NFL. No text, play name, play list, ratings, art or sound of Madden NFL is copied.

## Tests and building

- The tests are in `clone/tests`: more than 6,000, run in both the 64-bit and the 32-bit Python. From the `clone` folder: `.venv\Scripts\python -m pytest`.
- `clone/tools/build.ps1` builds the 64-bit and 32-bit programs with PyInstaller. `release/installer.iss` is the Inno Setup script for one installer that holds both. No installer is published yet.
- The Classic mode has a recorded transcript of the original's behavior that the tests compare with, so a change cannot alter the original game.

## License and credits

MIT License, Copyright (c) 2026 Josh Kennedy. The license covers the new code, tests and documents only, as explained under "Sounds and rights".

By [Josh Kennedy](https://github.com/joshknnd1982), inspired by Jim Kitchen.
