# Changelog, versions 0.16.11 to 0.16.12

The older versions of [CHANGELOG.md](../CHANGELOG.md), moved here whole when it grew too long to read in one piece; the newest versions, how to report a bug and where your files are, are in that file.

## 0.16.12 (2026-11-06, test build)

In a franchise, other teams now sign players from practice squads, yours too, and you choose the four squad players they cannot take. You can also sign another team's squad player yourself. Everything of 0.16.11 and earlier below is still to be tested too.

### Other teams sign practice squad players, and you protect four
As in the NFL, any team may sign another team's practice squad player to its own roster (never to its own practice squad), except the four players that team protects that week and the players of the team it plays that week. Each week of the regular season, after the games, a computer team that injuries have left short at a position for the coming weeks signs one squad player of that position: its own, or another team's when he is clearly better. A computer team that loses a squad player signs a free agent to its squad. Your team never signs anyone by itself.

**How to protect your squad players:** press F9, choose Franchise, then practice squad, then "protect squad players" (the fifth item). Each player is said with "protected" or "not protected"; Enter protects him or ends his protection, at most four at a time. Until you change one, your staff protects your four best each week; after that your choice is kept from week to week until you change it.
- How to test: in a franchise season, open the item, end the protection of one player and protect another, leave with Escape and open it again: is your choice kept? Try to protect a fifth player: you should hear that four are protected already. Play a few weeks: when a team signs one of your squad players, the week's report should tell you which team, which player and how many are left on your squad.
- Tell us: whether a protected player was ever taken (he never should be), and whether teams take your squad players too often or too rarely.

**How to sign another team's squad player:** F9, Franchise, practice squad, "sign from another team's squad" (the sixth item). Choose the position, then the player (each is said with his team); with a full roster you choose a player of the same position to release, then press Enter to confirm. He signs for the minimum salary for one season.
- How to test: sign one, then hear your roster (F9, Franchise, your roster): is he there at his position? The other team's four protected players and the players of the team you play this week should not be in the list.
- Tell us: anything said wrong in the lists or the question.

**Practice squad signings around the league** (the seventh item) lists every squad player signed to a roster this season, the newest first, and the practice squad rules item now says these rules too.
- How to test: after a few weeks, open the list: does each line say the week, the team that signed him, the player, his position and the squad he came from?
- Tell us: whether the list is useful or too long.

## 0.16.11 (2026-10-27, test build)

The announcer's voice now rises with the play, every kind of play result has at least ten wordings, and a new item turns the excited voice off or on. Everything of 0.16.10 and earlier below is still to be tested too.

### The excited voice
The owner asked for an enthusiastic radio play-by-play announcer whose voice gets faster and louder on the big plays, and that the player can turn this off or on. Every play call now has a level of excitement: a routine run or an incomplete pass is said in the voice as it is; a first down, a catch or a gain of ten yards or more a little higher; a big play of 20 yards or more, a long return, a field goal or the countdown of a long run higher, faster and a little louder; an interception, a fumble, a sack, a turnover on downs or a safety higher and faster again; and a touchdown the most. It works with the game's own Windows voices and with NVDA 2024.1 or newer. It was measured on the maintainer's PC: with NVDA's IBM ECI voice a touchdown is about 20 % higher and 25 % faster, and with the Windows voices the pitch rises from 5 % (Microsoft David) to 30 % or more (DECtalk and others; a few voices, such as FlexVoice and Lucent, do not change their pitch). JAWS cannot change its voice for a program, so with JAWS you hear the words and the exclamation marks only, and the menu item says so. Only the voice changes: the words, the plays, the score and the clock are exactly the same with the excited voice on or off.

Why not capital letters: the request was to write the big calls in capitals so the voice would raise its pitch. That was measured on 14 voices first. No voice said a word in capitals any higher, and many spelled it or stretched it out: Microsoft Zira says "GOT IT" as "got I T", and BeSTspeech takes four times as long to say "WOW". So the calls are written in normal case, and the game raises the pitch itself, through the voice's own pitch setting.

**How to turn it off or on:** press F9, choose Rules, press Down until you hear "Excited voice" (the thirteenth item, right after Play calls) and press Enter. Left and Right switch it too. You hear "Excited voice: on, the big plays are said higher, faster and a little louder" or "Excited voice: off, every call in the voice as it is". It is on by default, saved at once and used at once, also in the game you are playing. F9, Rules, Reset turns it on again. F6 names the item. In settings.txt it is `nx_excited_voice = on` or `off`. The items after it moved down one place: Stadium sounds is now the 14th item, Broadcast crew the 15th, Quarterbacks the 16th, Depth charts the 17th and Reset the 18th.
- How to test: play a few drives in the N. F. L. rules with NVDA or with the game's own voices (F9, Speech settings). Listen to a short run, a first down, a long gain, a sack or an interception and a touchdown: the voice should rise step by step. Then turn the excited voice off (F9, Rules, Excited voice, Enter, Escape twice) and play on: every call should be in the plain voice, with the same words. Turn it back on.
- Tell us: whether the steps are too small, too big or just right with your voice (name the voice), whether any call sounds too fast to follow, and, with JAWS, whether the item tells you that JAWS says the words only.

### Ten or more wordings for every kind of play result
Every kind of play result now has at least ten ways to be said, drawn at random and never the same one twice in a row: a gain of 1, a short gain, a gain of 4 to 9, of 10 to 19, of 20 to 39 and of 40 or more, a return and a big return, a loss and a loss on a sack, no gain on a run, an incomplete pass, a first down (also with a number and with goal to go), a touchdown, a safety, an interception, a fumble, a sack, a change of possession, a turnover on downs, a field goal made and missed, an extra point, a two-point conversion, a touchback, a fair catch and a catch. The big plays are short and punchy ("Big play! He rips off 25 yards!", "Off to the races! A gain of 31!", "Interception! Lewis jumps the route!", "Sacked! Brady never had a chance against Smith and Jones!"). The original game's six different sack sentences, its two interception sentences and its three plain catch sentences now share one list each, so the variety is that list's. Gus, the color analyst, still chimes in after the call with a short reason, as before.
- How to test: play a whole game in the N. F. L. rules and listen to the end of each play. With F2 you can hear the last play's calls again.
- Tell us: any call that does not fit what happened (a "big play" for a short gain, a team named wrong, a sack call on a play that was not a sack), and any wording you hear too often.
