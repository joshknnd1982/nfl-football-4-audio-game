# Changelog

No release has been published yet. The versions below are test builds made for the maintainer; the first release will be 1.0.0.

## 0.12.1 (2026-10-23, test build)
- Free agents, draft prospects, undrafted rookies and injury stand-ins in the Franchise have a first and a last name. A franchise saved before gets the first names when it is opened; your own team keeps its names.
- If the real calendar file cannot be read, the game says so once and plays that Franchise season with the original's 16 weeks. A calendar file saved by Notepad (with a byte order mark) is read.
- When you answer yes to speaking through NVDA or JAWS and the screen reader closes right after, the game no longer opens the voice list.
- A typed commentator name with accents keeps its letters (José becomes Jose, not Jos).
- Many of your own stadium sounds no longer slow the game: with 2,000 crowd files a cheer took up to 15 seconds before; now it starts at once.
- With JAWS, speech follows the keys at once: the first sentence after a key interrupts JAWS, and a key no longer waits for the guessed end of the speech before it.
- The referee says the result of a penalty after it is accepted or declined: the yards and the next down.
- The whistles are an NFL official's whistle and every whistle of the N. F. L. rules uses it; your own whistle.wav replaces them all.
- The crowd is heard: it roars for your big plays, cheers a flag on the other team and boos one on yours, as the flag is thrown, on a sound channel of its own. Your own crowd_big_play and crowd_flag_cheer files replace these.
- Only running backs and fullbacks play at running back; a team short of real ones gets made-up running backs, and the first backs carry most. An older franchise gets made-up running backs in place of the tight ends and quarterbacks it had there.
- The Blitz item always sends five or more rushers, and a blitz gets home more often.
- A game of the N. F. L. rules starts, and a saved game goes on, without the intro jingle and the crowd surge.

## 0.12.0 (2026-10-22, test build)
- New key W in the play menus of the N. F. L. rules: it says which play the playbook would most likely pick for the play type or the list you are on, and how often. Plays that share the greatest chance are told as equal. It draws nothing, so asking changes nothing in the game.
- The keys of the play menus (Enter on a play type, Right, M, D and W) each have their own line in F5, F6 and the README keys.
- The Washington team is the Commanders by default (an older teams.txt is changed once; the old file is kept as teams.txt.before-commanders).
- The Franchise plays the real 2026 NFL schedule: 18 weeks with bye weeks, and the play-offs from week 19. Classic, the season of the original and quick games keep the original's 16 weeks. A franchise made before keeps its season and plays the new calendar from its next season.
- Free agents in the Franchise during the season, and trades until the trade deadline (the Tuesday after week 9); trades are also open in free agency of the offseason.

## 0.11.0 (2026-10-22, test build)
- The color commentator's name can be chosen from a list of sports podcasters and broadcasters, or typed.
- Your own sound files for the stadium, the referee's microphone and the whistles, with a list in the game that says which file name each sound takes.
- The game finds NVDA or JAWS by itself and asks once whether to speak through it; it then asks for no voice.
- More Plays on defense lists every defensive call, and the play menus say once where the other plays are.
- "The playbook's choice" in Formation and Tempo is explained in the game; no sentence is said twice in a row after an onside kick or a field goal.

## 0.10.0 (2026-10-22, test build)
- A radio-style broadcast: the announcer's banter and a color commentator in a voice of their own.
- Stadium sounds (a crowd, hits, the first down chain), and a referee who announces over a microphone, with whistles.
- R in the offense menu chooses who your next pass goes to; L in the defense menu chooses who blitzes.

## 0.9.0 (2026-10-22, test build)
- The first test build: the game as the original, plus the N. F. L. rules (a real clock, time outs, penalties, onside kicks, quarterback runs, replay challenges), every real NFL play with a plain description, playbooks, the real head coaches and players of the 32 teams, a Franchise, a choice at the start of what to do with a saved game, the lists of keys in F5 and F6, and a detailed log with a problem report for bugs on other computers.
- The exit says only the thank-you sentence.
