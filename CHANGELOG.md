# Changelog: what is new, and how to test it

This file lists everything new in each build of NFL Football 4, newest first, so that players and outside testers know what changed and what to try. No release has been published yet: the versions below are test builds; the first release will be 1.0.0.

## Before you start

- **Report a bug with a problem report.** In the game press F9, choose Speech settings, press Down until you hear "Save a problem report", then press Enter. The game saves one file and says where. Send that file with a few words: what you did, what you heard, what you expected. The file holds no passwords and no account name.
- **Your files** (settings, saved games, franchise, your own sounds and texts, logs) are in `%APPDATA%\Kitchensinc Revival\NFL Football 4`. The program folder holds only the program.
- **Keys:** F1 repeats the last prompt, F5 lists every key, F6 explains the game, F7 explains football words, F9 opens the added functions.
- "N. F. L. rules" below means the game's default mode. "Classic" is the original game's exact mode (F9, Rules); most new things are in the N. F. L. rules only.
- Where a test says "Tell us", that is a question the maintainer wants answered.

## 0.12.1 (2026-10-23, test build)

### Practice squads in the Franchise
Each team now keeps a practice squad of up to 16 players (at most 6 veterans), formed at the start of each season from the players cut and let go in the offseason. When an injury leaves a position with nobody fit to play, a squad player of that position is elevated to play (up to 3 times a regular season; no limit in the play-offs) before a made-up stand-in is used. A franchise made with an older version gets its squads when you open it.
- How to test: in a franchise, F9, Franchise, practice squad (the tenth item). "Hear the practice squad" lists your squad with each player's elevations left. "Sign a player to your roster" moves one up (when his position is full, you choose who is released). "Add a free agent" and "release a squad player" change the squad. When a player is elevated, the week's injury report says so.
- Tell us: is the squad easy to manage? Should computer teams sign players from other teams' squads (this build does not)?

### Speech with JAWS follows the keys
- How to test: with JAWS running (and NVDA closed), arrow quickly up and down a menu, press F1, F5 and letters. Each new item should start at once, as it does with NVDA.
- Tell us: try it at your usual JAWS rate and at a fast rate. Does any sentence you wanted to hear get cut?

### The referee announces the result of a penalty
After a penalty is accepted or declined, the referee says the result: "the penalty is accepted. 10 yards, it will be third and 5 on your 30 yard line."
- How to test: play a game with the N. F. L. rules until a flag is thrown (penalties are on by default). Accept one penalty and decline another.

### An NFL official's whistle, and your own whistle
Every whistle of the N. F. L. rules is now the officials' whistle (short, long and double). One file of yours, `whistle.wav` (or .ogg, .flac, .mp3) in the sounds folder, replaces every whistle.
- How to test: listen to the whistles at the end of plays, time outs and quarters. F9, Sounds, Stadium and referee sounds lists all 22 sounds and plays them; the last item is the one for every whistle.
- Tell us: does it sound like an NFL whistle?

### The crowd is heard
The crowd's reactions are louder than before and have their own sound channel, so a hit or the referee's microphone no longer cuts them. The crowd roars for your team's big plays (20 yards or more), cheers a flag on the other team and boos a flag on yours, as the flag is thrown. Your own sounds can replace these: `crowd_big_play.wav` and `crowd_flag_cheer.wav` in the sounds folder (numbered extra files like `crowd_big_play2.wav` add to them).
- How to test: play until your team gains 20 yards or more on a play, and until flags are thrown on each team.
- Tell us: are the reactions loud enough now, and not too loud over the speech?

### Running backs are running backs
Only running backs and fullbacks play at running back. A team with fewer than six real running backs gets made-up running backs for the rest, and the first backs carry the ball most often. An older franchise gets made-up running backs in place of the tight ends and quarterbacks it had there.
- How to test: play a quick game with the N. F. L. rules and listen to who carries the ball on running plays.

### Blitzes get home more often
The Blitz item always sends five or more rushers, and a blitz now gets to the quarterback more often.
- How to test: on defense, choose Blitz (4, then Enter) on passing downs over a few games, and count the sacks.

### No jingle when a game starts
A game of the N. F. L. rules now starts, and a saved game goes on, without the intro jingle and without the crowd surge. Classic keeps the original's start. The program's intro still plays once at launch, under the welcome.
- How to test: start a new game, then save and load a game.
- Tell us: should the launch intro go too?

### Made-up players have full names
Free agents of the season, draft prospects, undrafted rookies and injury stand-ins in the Franchise now have a first and a last name. A franchise saved before gets the first names when it is opened; your own team keeps the names it has.
- How to test: F9, Franchise, free agents, "hear the free agents".

### Smaller fixes
- If the real NFL calendar file cannot be read, the game says so once and plays that Franchise season with the original's 16 weeks. A calendar file saved by Notepad is read.
- When you answer yes to speaking through NVDA or JAWS and the screen reader closes right after, the game no longer opens the voice list.
- A typed commentator name with accents keeps its letters (José becomes Jose, not Jos).
- Many of your own stadium sounds (thousands of files) no longer slow the game down.

## 0.12.0 (2026-10-22, test build)
- **The W key** in the play menus of the N. F. L. rules says which play the playbook would most likely pick for the play type or list you are on, and how often. Plays that share the greatest chance are told as equal; asking changes nothing in the game. How to test: on offense, arrow to a play type and press W; press Right to open its list and press W again.
- **The keys of the play menus** (Enter on a play type, Right, M, D and W) each have their own line in F5, F6 and the README. How to test: press F5 and F6 in a game.
- **The Washington team is the Commanders** by default (an older teams.txt is changed once; your old file is kept as teams.txt.before-commanders). How to test: choose a team in the N. F. L. East.
- **The real 2026 NFL schedule in the Franchise:** 18 weeks with bye weeks, play-offs from week 19. Classic and quick games keep the original's 16 weeks. How to test: start a new franchise, then at the main menu choose 2 (see schedule); play through your bye week. Tell us: does anything still say week 16 or 17 where it should not?
- **Free agents and trades in the Franchise season:** F9, Franchise, free agents (sign a free agent any week before the kick-off) and trades, open until the trade deadline (the kick-off of week 10) and in the offseason's free agency. The news says where they are and when the deadline comes. How to test: sign a quarterback; try a trade in week 10 and in week 11.

## 0.11.0 (2026-10-22, test build)
- The color commentator's name can be chosen from a list of sports podcasters and broadcasters, or typed (F9, Rules, Commentator).
- Your own sound files for the stadium, the referee's microphone and the whistles, with a list in the game that says which file name each sound takes (F9, Sounds, Stadium and referee sounds).
- The game finds NVDA or JAWS by itself and asks once whether to speak through it; it then asks for no voice.
- More Plays on defense lists every defensive call, and the play menus say once where the other plays are.
- "The playbook's choice" in Formation and Tempo is explained in the game; no sentence is said twice in a row after an onside kick or a field goal.

## 0.10.0 (2026-10-22, test build)
- A radio-style broadcast: the announcer's banter and a color commentator in a voice of their own (comments on with F8).
- Stadium sounds (a crowd, hits, the first down chain), and a referee who announces over a microphone, with whistles.
- R in the offense menu chooses who your next pass goes to; L in the defense menu chooses who blitzes.

## 0.9.0 (2026-10-22, test build)
- The first test build: the game as the original, plus the N. F. L. rules (a real clock, time outs with T, penalties, onside kicks, quarterback runs, replay challenges), every real NFL play with a plain description (D in a play menu), playbooks, the real head coaches and players of the 32 teams, a Franchise, a choice at the start of what to do with a saved game, the lists of keys in F5 and F6, and a detailed log with a problem report for bugs on other computers.
