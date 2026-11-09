# Changelog: what is new, and how to test it

This file lists everything new in each build of NFL Football 4, newest first, so that players and outside testers know what changed and what to try. The versions below are test builds, published on GitHub as pre-releases (the first from 0.16.2); the first full release will be 1.0.0.

## Before you start

- **Report a bug with a problem report.** In the game press F9, choose Speech settings, press Down until you hear "Save a problem report", then press Enter. The game saves one file and says where. Send that file with a few words: what you did, what you heard, what you expected. The file holds no passwords and no account name.
- **Your files** (settings, saved games, franchise, your own sounds and texts, logs) are in `%APPDATA%\Kitchensinc Revival\NFL Football 4`. The program folder holds only the program.
- **Keys:** F1 repeats the last prompt, F5 lists every key, F6 explains the game, F7 explains football words, F9 opens the added functions.
- "N. F. L. rules" below means the game's default mode. "Classic" is the original game's exact mode (F9, Rules); most new things are in the N. F. L. rules only, the radio broadcast is in both.
- Where a test says "Tell us", that is a question the maintainer wants answered.

## Unreleased (since 0.16.20)

Changes made since the last test build. They will be in the next one.

### The announcer says how long a field goal try is
From a tester's request (GitHub issue 7): "have radio announcer tell you the distance of the field goal being attempted. It should be just like in a radio broadcast." With the radio play calls (F9, Rules, Play calls: radio, the default), the call before every field goal now names its length, for example "Here comes Kim for a 42-yard field goal attempt." A try of 50 yards or more is called a long one, a little more excited. The fair catch kick says its length too, and some of the calls after the kick say it again ("From 42 yards, right through!"). The length is counted as on a real field: the yards to the goal line, plus 7 for the hold and 10 for the end zone, where the goal posts stand. It works with the N. F. L. rules and with Classic. With Play calls set to plain, the game keeps the original game's words, which have no length.

**How to test:** play a game with the radio play calls on and kick a field goal from your opponent's 25 yard line (Field Goal in the play menu): the announcer should say a 42-yard try. Try one from the opponent's 35 or farther out: it should be called a long one. Listen after the kick for the length said again on some kicks.
**Tell us:** whether the length comes at the right moment, and whether any wording sounds wrong.

## 0.16.20 (2026-11-07, test build)

One whistle, now really. From a tester's report on 0.16.19. Everything of 0.16.19 and earlier below is still to be tested too.

### The tackles no longer blow the original game's whistle
From a tester's report (GitHub issue 6): "two whistles appear to be used still." 0.16.18 made every whistle the one whistle the game made, but the original game's three tackle sounds (the pile up, two tacklers and one tackler) end in a referee whistle of their own, so every tackle still blew the original's whistle and every other dead ball the made one. With the N. F. L. rules the game now plays a tackle only up to the moment its old whistle began, then blows the one whistle at that same moment; a play takes as long as before. Your own whistle.wav replaces it there too. A tackle sound of your own (foot4, foot5 or foot6 in the sounds folder) should hold only the hit: it is played whole and the whistle follows it. The Classic rules keep the original game's sounds whole.

**How to test:** play a game with the N. F. L. rules and listen to a run that is tackled, a completed pass and a sack: after the hit you should hear the same whistle as after an incomplete pass, a kick off and the end of a quarter, and no second, different whistle. Turn the stadium sounds off (F9, Rules, Stadium sounds) and listen again. A play with a flag still has two whistles of the same sound: the one that ends the play and the referee's for the flag.

**Tell us:** if you still hear a whistle that is not the same as the others, and after what kind of play.

## 0.16.19 (2026-11-07, test build)

The changelog comes with every release now, and the Start menu opens it. From a tester's report. The four other reports of that night (injured reserve, the safeties and linebackers, the returners in trades, one whistle) were already fixed in 0.16.18; everything of 0.16.18 and earlier below is still to be tested too.

### The changelog in every release, and in the Start menu
From a tester's report (GitHub issue 5): "A change log needs to be included with every release so we know what to test for and what has been changed." Every release on GitHub now has, beside the installer, a file CHANGELOG-<version>.md: the whole changelog as it stood at that version, every item with how to test it. The release's notes carry that version's own part too. Once the game is installed, the Start menu has a new entry, "NFL Football 4 changelog, what is new", which opens this file in Notepad.

**How to test:** open the newest release on the Releases page: below its notes, the assets should list CHANGELOG-<version>.md beside the installer; download it and read it. Install the game, open the Start menu, type "NFL Football 4 changelog" and press Enter: Notepad should open this changelog, with the installed version's section at the top.

**Tell us:** if a release has no changelog file, or the Start menu entry opens nothing.

## 0.16.18 (2026-11-06, test build)

Injured reserve in the Franchise, every position on its own in the Franchise menus, returners you can trade, and one whistle. From a tester's e-mail. Everything of 0.16.17 and earlier below is still to be tested too.

### Injured reserve, designations to return and activations
The Franchise has injured reserve now, by the NFL's rules. F9, Franchise, injured reserve is the item after the injury report. A hurt player you put on injured reserve leaves your 53, so you can sign a free agent in his place, and he must miss at least 4 games. Once he has missed 2 games you can designate him to return, which opens his practice window for 3 weeks; once he has missed 4 games and is healthy you activate him, and he is back on your 53. If your 53 is full you choose who is released first. A man not activated in his window stays on injured reserve for the season, and the week's injury report says so. You have 8 returns in the regular season and 2 more in the play-offs, one man at most twice. Men on the physically unable to perform or non-football injury lists are activated after 4 games with no designation. The computer teams keep their real reserve lists. Saved franchises of older versions open as they were.

**How to test:** in a franchise, play until one of your players is hurt for several weeks (F9, Franchise, injury report names him). Press F9, Franchise, injured reserve, then "put a hurt player on reserve", choose him and press Enter: you should hear that he is on injured reserve and how much room your roster has. Play two weeks, then open "your players on the reserve lists" and press Enter on him: he should be designated to return, with 3 weeks in his window. Play until he has missed 4 games and is healthy, press Enter on him again: he should be back on your roster (F9, Franchise, your roster). Also try "the rules of injured reserve".

**Tell us:** if a step is refused when it should work, what was said.

### Free and strong safeties, and each linebacker, on their own
The trades, the free agents and the practice squad asked for a group ("safeties", "linebackers") and listed all of its men together. Now they ask for one of the 22 real positions, in the order of your roster: free safeties and strong safeties apart, and the strong-side, middle and weak-side linebackers apart (the NFL's and Madden NFL's three: one middle linebacker and two outside), the left and right edge, and so on. Each position lists only its own men.

**How to test:** press F9, Franchise, free agents, then sign a free agent: the menu should list free safeties, strong safeties, strong-side linebackers, middle linebackers and weak-side linebackers as separate items, and each should list only men of that position. Do the same in F9, Franchise, trades, offer one of your players, and in the practice squad's add a free agent.

**Tell us:** if any man is listed at a position that is not his.

### Kick and punt returners can be traded
A man who returned kicks was in no list of the trades, so he could not be offered or asked for. The trades now have the item "kick and punt returners" (the last in their positions' menu), and a returner is in the list of his own position too. You can now also give a man of another position than the one you ask for; the other team still answers by what the trade is worth to it.

**How to test:** press F9, Franchise, trades, then ask a team for a player, choose a team, then "kick and punt returners": you should hear that team's returners. Choose one and offer a player of yours: the other team should answer yes, more, or no.

**Tell us:** if a returner is still missing from a list.

### One whistle
With the N. F. L. rules the game played four different made whistles (short, long, double and triple), and the original game's whistle when the stadium sounds were off. Now every whistle is the one whistle the game made, at time outs, the ends of plays and quarters, flags, the two minute warning, reviews and the final whistle, with the stadium sounds on or off. Your own whistle.wav in the sounds folder replaces it everywhere (whistle2.wav and more join it). The Classic rules keep the original game's whistle. F9, Sounds, Stadium and referee sounds lists 18 sounds now; "put the stadium sounds back" also moves aside old whistle_short, whistle_long, whistle_double and whistle_triple files.

**How to test:** play a game with the N. F. L. rules and listen to the whistles after plays, at a time out (T) and at the end of a quarter: they should all be the same sound. Turn the stadium sounds off (F9, Rules, Stadium sounds) and listen again: still the same whistle. Put your own whistle.wav in the sounds folder (CUSTOMIZE.md says where) and every whistle should be yours.

**Tell us:** if you still hear two different whistles anywhere.

## 0.16.17 (2026-11-06, test build)

Page Up and Page Down now work in the F9 menus. Everything of 0.16.16 and earlier below is still to be tested too.

### Page Up and Page Down in the F9 menus
The help (F5 and F6) always said that Page Up and Page Down move ten items in the F9 menus, but in menus such as Speech settings they only said the current item again; so did the brackets that stand in for them since 0.16.15. Now they move ten items and stop at the first or the last, in every F9 menu and in the pages of text, as they already did in the long lists. F1 in these menus now names Page Up, Page Down, Home and End.

**How to test:** press F9, choose Speech settings. Press Page Down or the close bracket: you should hear the eleventh item. Press it again: the last item, "Save a problem report". Page Up or the open bracket goes back ten, and stops at the first item. Press F1: the help should name Page Up, Page Down, Home and End.

**Tell us:** if any F9 menu or list still ignores one of these keys.

## 0.16.16 (2026-11-06, test build)

Renaming a player now keeps what you type. Everything of 0.16.15 and earlier below is still to be tested too.

### Renaming a player keeps capitals, apostrophes, hyphens and periods
Before, a new name you typed in F9, Franchise, your roster (a player, change his name) came out all in lower case, an apostrophe was said as a strange letter ("thorn") and then left out, and hyphens and periods were dropped too: "Ja'Marr" became "jamarr". Now the name keeps what you typed: capital letters with Shift, apostrophes, hyphens and periods, as in the real names the game already uses (Ja'Marr, Amon-Ra St. Brown). Other characters are still left out, and a name needs at least two letters or digits. The names you type at the start of a Classic season are unchanged.

**How to test:** start or open a franchise, press F9, choose Franchise, then your roster, choose a player and change his name. Type a name with a capital letter, an apostrophe and a hyphen, for example O'Neil-Smith, then Enter. Each character should be said as you type it (the apostrophe as "apostrophe"), the question should say the name as you typed it, and after yes the roster should have it.

**Tell us:** if a character you need in a name is still left out.

## 0.16.15 (2026-11-06, test build)

Keys for laptops that have no Home, End, Page Up or Page Down. Everything of 0.16.14 and earlier below is still to be tested too.

### Stand-in keys for Home, End, Page Up and Page Down
Many laptop keyboards, Acer's among them, have no Home, End, Page Up or Page Down key, and the game uses them in the F9 menus and lists, in the saved game and franchise questions, and in your franchise roster. Now four keys that every keyboard has do the same work, in Classic and in the N. F. L. rules:
- the open bracket is Page Up (on a US keyboard, the key right of P),
- the close bracket is Page Down (the next key to the right),
- the semicolon is Home (the key right of L),
- the apostrophe is End (the next key to the right).

While you type a name they are not used this way, so typing is not disturbed (a name keeps only letters, digits and spaces, as in the original). F5 and F6 name the four keys.

**How to test:** press F9 and open a long list, for example Speech settings and then the voices, or your franchise roster. Press the close bracket: the list should move ten items down, as Page Down does. The open bracket moves ten up, the apostrophe goes to the last item and the semicolon to the first. At a long saved game or franchise question, the brackets should turn the pages.

**Tell us:** if your keyboard lacks another key the game uses.

## 0.16.14 (2026-11-06, test build)

The keyboard's volume, mute and media keys no longer interrupt the game. Everything of 0.16.13 and earlier below is still to be tested too.

### The volume keys leave the game alone
Before, pressing your keyboard's volume up or volume down key while the game spoke stopped the speech, the game said a stray symbol (NVDA read it as "macron" or "registered"), and the menu started again from its first item. Windows still changed the volume. Now the volume, mute, media (play, pause, next, previous) and browser keys belong to Windows only: the volume changes as always and the game goes on with what it was saying. This is the same in Classic and in the N. F. L. rules. F5 and F6 now say so.

**How to test:** start a game and wait for a play menu. While the announcer is speaking, press volume up and volume down a few times. The volume should change, the sentence should go on to its end, and you should hear no symbol and no repeated menu. Then press Down: the menu should move to the next item as usual.

**Tell us:** if any other key of your keyboard makes the game say a symbol.

## 0.16.13 (2026-11-06, test build)

In a franchise on the real calendar, teams with the same record are now put in order by the NFL's own tie-breakers, for the standings, the division titles, the wild cards and the play-off seeds. Everything of 0.16.12 and earlier below is still to be tested too.

### The NFL's tie-breakers in the standings and the play-offs
When two or more teams finish with the same record, the game now follows the NFL's tie-breaking procedures: first the games between the teams, then the record in division games (inside a division) or in conference games (for a wild card), the record against common opponents, the strength of victory and of schedule, points scored and allowed, net points, and last a coin toss. Before, equal teams kept the league's order, and your team won every tie for the last place; now it must win the tie-breaker like everyone else. The coin toss is fixed for each season, so the seeds never change between rounds. The game cannot count touchdowns of the other games, so the NFL's net touchdowns step is skipped. Classic and a franchise on the original's 16 weeks are unchanged.

**How to test:** play a franchise on the real calendar to the end of a regular season (week 18). Listen to the standings after each week: inside a division, a team with a better winning percentage now comes first even with as many losses, and equal teams are in tie-breaker order. At the end of the regular season the game names the division winners, the wild cards and the two teams with a bye; when a tie-breaker decided your division title or your conference's last wild card place, one more sentence says who won it, over whom, and why (for example "the games between the teams"). F6 in a franchise now says that equal records are settled by the NFL's tie-breakers.

**Tell us:** when your team was in a tie, did the sentence make clear why it got in or stayed out?

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

## 0.16.10 (2026-10-27, test build)

Every play is now called like an exciting radio broadcast, the sideline reporter speaks at the big moments, "get the latest rosters" reads the NFL's own pages, the 2028 draft picks can be traded, a running back can be your pass target in a franchise game too, and a fix for the R key on the run pass options. Everything of 0.16.9 and 0.16.8 below is still to be tested too.

### Get the latest rosters reads the NFL's own pages
A tester's problem report showed "get the latest rosters" failing twice with "the game could not reach GitHub": the game only downloaded the maintainer's file from the game's page on GitHub, and that tester's network does not reach GitHub's file server. Now the game reads the rosters straight from the NFL: every team's own roster page and depth chart page on its NFL club site, converted into the game's rosters with the same code the maintainer uses (the lists, the numbers, the 22 positions, the return men, each player's age and seasons). It takes a few seconds. A player the game already knows keeps his checked position and his place in the depth order (a team's page can lag the news; an injured starter stays the starter unless he goes on a reserve list); new players come in at the position the team gives them, behind the others. A player a team no longer lists joins the free agents, and a free agent who signed leaves them. When a team's pages cannot be read right then (or show more than 53 active players on a game day), that team stays as it was and the game says how many teams that was. The game's page on GitHub is still asked at the same time, never waited for more than three seconds: when it has a newer checked file, the NFL's changes go on top of it, and when the NFL's pages cannot be read at all, that checked file is used. Your old files are kept as copies, as before, and a franchise is offered the newer rosters, as before.
- How to test: press F9, choose Customize (or Franchise), and choose "get the latest rosters". You should hear "asking the N. F. L. teams' own pages", then within a few seconds "You now have the rosters of" today's date, "They come from the N. F. L. teams' own roster and depth chart pages", and perhaps how many teams could not be read. Start a quick game or open your franchise and listen to a team you follow. If you are on a network that blocks GitHub, it should work all the same.
- Tell us: the exact sentence you hear, and any player on the wrong team, at the wrong position or with the wrong number (save a problem report right after: F9, Speech settings, Save a problem report).

### The 2028 draft picks can be traded
In a franchise, trades could include only the picks of the coming draft (the 2027 draft in your first season). Now the picks of the draft after it (the 2028 draft in your first season) can be traded too, as NFL teams do a year ahead: they come after the coming draft's picks in the lists of F9, Franchise, trades (your draft picks, and the picks you add or ask for in a proposal), each said with its year ("your 2028 round 2 pick", "the 2028 round 1 pick of the Bears"). Such a pick is worth about three quarters of the same round's pick of the coming draft. When its season begins it becomes a pick of the coming draft, owned by whoever got it, and that team makes it in the draft. The computer teams use the coming draft's picks first and a pick a year ahead only when those cannot make a trade even. Your saved franchise opens as before.
- How to test: in a franchise during the regular season (or in free agency before the draft), press F9, Franchise, trades, "your draft picks": after this year's seven picks you hear seven 2028 picks. Propose a trade and add a 2028 pick; the other team answers by its value. After the next draft, at the new season, the pick you traded is the other team's in the draft, and you can trade 2029 picks.
- Tell us: whether the 2028 picks are worth about right in trades, and any pick said with the wrong year or the wrong team.

### Every play called like an exciting radio broadcast
The owner on 0.16.9: the game still said "it's third down and 10 yards to go" and "it's my ball on my 26 yard line" in flat words; it should sound like a radio call, with exclamations: "caught by" the player, "touchdown!". Now the announcer calls every play that way, in both rule sets. The teams are named instead of "my ball" and "your ball" ("The Jets take over at their own 23.", "The Bengals are at the Jets 47."); the down is said as a radio call says it ("Third and 4! A big down here!", "First down, Bengals!", "Fourth and goal!"); the action is short and lively ("Starr fires a perfect spiral!", "Caught by Seals!", "One hand! Seals makes a one-handed catch!", "Intercepted! Scanlon picks it off!", "Sacked! Brown gets Unitas!", "Fumble! The ball is loose!"); the gain grows with its size ("A gain of 3.", "Good for 7 yards!", "What a play! 34 yards!"); a long run counts down ("He's at the 40! the 30! the 20! the 10! 5! 4! 3! 2! 1! Touchdown Bengals!"), a long return builds up the same way, and a field goal ends in "It's good!" or "Wide left! No good!". Each moment has several wordings, so a game does not repeat itself. With the game's own voices, the biggest calls are also said a little faster; a screen reader speaks the words and the exclamation marks at its own speed. The plays themselves, their results, the score and the clock are exactly as before: only the words changed.

The new item F9, Rules, Play calls (right after How much the crew talks, in both rule sets) has two values: radio style, exciting (the default) and plain, the original's words (the sentences of the original game, exactly). Enter, Left and Right switch it; it is saved at once and used at once, also in the game you are playing. It is its own switch: F8 turns the crew off but keeps the radio calls. F9, Rules, Reset brings back radio style. F6 names the item.
- How to test: play a few drives of a game in the N. F. L. rules. Listen to the end of each play: the team with the ball, where it is, and the down should be said as a radio call, with no "my ball" or "your ball". Listen for a catch, an incomplete pass, a sack, a long run, a punt and a kick off, and for the countdown of a long touchdown. Then press F9, Rules, press Down until you hear "Play calls: radio style, exciting", press Enter to hear "plain, the original's words", press Escape twice and play on: the plays are told in the original's words again. Switch it back. Try Classic too.
- Tell us: any play-by-play sentence that still sounds flat or still says "my ball", any call that does not fit what happened (a "big gain" for a short one, a team named wrong, a first down called when it was not one), and whether there are too many or too few exclamations.

### The sideline reporter speaks, and the crew gets excited
The owner on 0.16.9: "Not once did the game have the sideline reporter speak at all. I want an exciting commentary for this game." His log showed why: Nora spoke once, before the coin toss, and with a screen reader every member of the crew speaks in the same voice, so a line from the field that does not name her sounds like Walt. She also had only three moments (before the kick-off, a franchise injury, half time). Now Walt names her before her first note ("Let's go down to Nora Banks on the sideline."), and Nora has seven new moments, each line starting with her name: after a touchdown (the bench, the crowd, the scorers), after an interception or a lost fumble, after a big play of 20 yards or more, when a team goes for it on fourth down, at the two-minute warning, at the end of the first and third quarters, and at the final whistle (always, with the winner or a tie). Gus now opens his line after a touchdown, a takeaway, a big play, a sack or a missed field goal with an exclamation ("Wow!", "Unbelievable!", "Are you kidding me?"). How often both happen follows F9, Rules, How much the crew talks: with the default "a lot" Nora speaks about ten to fifteen times a game; "a little" stays exactly as 0.16.8. F9, Rules, Broadcast off silences Nora and Gus, as before; the game itself does not change.
- How to test: play a whole game in the N. F. L. rules with comments on and "How much the crew talks" at "a lot" or "the most". Listen for Walt naming Nora before her first note, and for Nora after touchdowns, takeaways and big plays, at the two-minute warning and at the final whistle. Play a game in Classic too.
- The new lines are in remarks.txt (the pools CXR, STD, STV, SBG, SFD, SMW, SQE, SFN and SFT, at the end of the file), and you can change or switch off any of them (CUSTOMIZE.md).
- Tell us: whether you can now tell when Nora speaks, whether she speaks too often or too little, and any line that does not fit the moment.

### Passes to running backs in a franchise game
With the N. F. L. rules, R in the offense menu chooses who your next pass goes to. In a quick game the list has always ended with your first two running backs when the play has a route for a back (a screen, a swing, an angle, a drag, a wheel), but a franchise game offered only the receivers. Now a franchise game offers the backs too. A pass to a back counts with his own rating as a running back, and a back who catches it can be hurt on the play, as a receiver can; a catch does not count as one of his carries (the carries that make a busy back likelier to be hurt are his runs). The receivers in a franchise game's list are now said by each man's real position, wide receiver or tight end, as in a quick game; before, every one was "receiver". A game where you choose nothing plays exactly as before.
- How to test: in a franchise game with the N. F. L. rules, in the offense menu, go to a screen pass or another pass with a back's route (press D on a play to hear what it does), press R, then End: the last two items are your first two running backs, each said with "running back". Press Enter on one, then Enter on the play: if the pass is caught, the catch names him. Then press R on a deep pass (a go route or a post): the list has only the receivers.
- Tell us: whether the two backs are the right men (the first two running backs of your depth chart), whether the receivers' positions are right, and whether passes to a good back gain more than passes to a weak one over a few games.

### R on a run pass option no longer stops the game
The eight run pass options (More Plays, Run Pass Options: the quarterback hands off or throws, by what the defense does) failed when you pressed R on one, and a running back chosen with R followed by a run pass option failed at the snap: the program stopped. Now R works on them: the list has the receivers, and the two running backs on the three whose throw has a back's route (Bubble Option, Tight End Option, Jet Option). When the quarterback hands off on one of those, the back you chose carries the ball.
- How to test: in the offense menu of the N. F. L. rules (a quick game or a franchise game), press M for More Plays, open Run Pass Options, move to Bubble Option and press R: you hear the list. Press End and Enter to choose the second running back, then Enter to call the play: the game goes on; if the quarterback hands off, that back carries the ball. Try R on Stick Option too: only the receivers.
- Tell us: any play where R, or a target you chose, does something you did not expect.

## 0.16.9 (2026-10-27, test build)

The seventeenth test installer. The owner played 0.16.8 and found that the radio crew hardly spoke: in eight plays Gus said one line after the sign-on. The crew now talks about twice as much, and a new menu item lets you choose how much. Everything of 0.16.8 is still to be tested too (its section below).

### The radio crew talks more, and you choose how much
In 0.16.8 Gus spoke only after special plays and moments (a touchdown, a sack, a turnover, a big gain, a third down, the red zone), and only now and then, so most plays had nothing after them: the analyst spoke after about one play in eight, and three or four plays in a row often went by in silence. Now Gus also has lines after ordinary plays: a run that gains well, a run that is stopped, a pass caught, a pass that falls incomplete, a punt and a kick off (104 new lines, written in the manner of the real radio broadcasts the crew is modelled on: a reason and what to watch next). Walt fills more of the breaks Gus leaves with an aside, the network's name or the score. With the default level, a whole game has about 140 lines of the crew instead of about 64, and Gus speaks after about one play in two. The play-by-play, the scores and the clock are unchanged, and the crew still never changes how a game goes.

The new item F9, Rules, How much the crew talks (right after Broadcast, in both rule sets) has four levels: a little (exactly as 0.16.8), some (Gus after about one play in three or four, as on a real radio call), a lot (the default) and the most (a line after nearly every play). Enter goes to the next level and says it; Left and Right go down and up. The change is saved at once and used at once, also in the game you are playing: you do not have to wait for the next game. F9, Rules, Reset brings back "a lot". F6 names the item.
- How to test: play a game with comments on (F8) and listen between plays: after most runs and passes you should now hear Gus, and sometimes Walt first ("walk us through that play"). Then, during the same game, press F9, choose Rules, press Down until you hear "How much the crew talks: a lot", press Enter to hear "the most", press Escape twice and play on: Gus now speaks after nearly every play. Go back and choose "a little": the crew is as quiet as in 0.16.8. Try it in Classic too.
- The first key you press still cuts the line being said, so if you choose your play quickly you hear only the start of Gus's line. Wait a moment before you press a key to hear it all.
- The new lines are in remarks.txt (the pools CRG, CRS, CPC, CPI, CPT and CKR, at the end of the file), and you can change or switch off any of them (CUSTOMIZE.md).
- Tell us: which level you like best, whether "a lot" is right as the default, any line that does not fit the play it follows (a "nice run" after a short gain, say), and any line you hear too often.

## Older versions

The versions before 0.16.9 are in these files, newest first. Each is a markdown file in the `changelog` folder of this repository.

- [0.16.8 to 0.16.8](https://github.com/joshknnd1982/nfl-football-4-audio-game/blob/master/changelog/CHANGELOG-0.16.8-to-0.16.8.md)
- [0.13.0 to 0.16.6](https://github.com/joshknnd1982/nfl-football-4-audio-game/blob/master/changelog/CHANGELOG-0.13.0-to-0.16.6.md)
- [0.9.0 to 0.12.1](https://github.com/joshknnd1982/nfl-football-4-audio-game/blob/master/changelog/CHANGELOG-0.9.0-to-0.12.1.md)
