# Changelog, versions 0.16.16 to 0.16.18

The older versions of [CHANGELOG.md](../CHANGELOG.md), moved here whole when it grew too long to read in one piece; the newest versions, how to report a bug and where your files are, are in that file.

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
