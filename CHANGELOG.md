# Changelog: what is new, and how to test it

This file lists everything new in each build of NFL Football 4, newest first, so that players and outside testers know what changed and what to try. The versions below are test builds, published on GitHub as pre-releases (the first from 0.16.2); the first full release will be 1.0.0.

## Before you start

- **Report a bug with a problem report.** In the game press F9, choose Speech settings, press Down until you hear "Save a problem report", then press Enter. The game saves one file and says where. Send that file with a few words: what you did, what you heard, what you expected. The file holds no passwords and no account name.
- **Your files** (settings, saved games, franchise, your own sounds and texts, logs) are in `%APPDATA%\Kitchensinc Revival\NFL Football 4`. The program folder holds only the program.
- **Keys:** F1 repeats the last prompt, F5 lists every key, F6 explains the game, F7 explains football words, F9 opens the added functions.
- "N. F. L. rules" below means the game's default mode. "Classic" is the original game's exact mode (F9, Rules); most new things are in the N. F. L. rules only, the radio broadcast is in both.
- Where a test says "Tell us", that is a question the maintainer wants answered.

## 0.16.8 (2026-10-27, test build)

The sixteenth test installer, with everything new since 0.16.6 (0.16.7 was never built as an installer; all of its changes are here). A radio crew calls the game in both rule sets, and the original game's jokes and commentator are gone; the free agents checked one by one, signing to the practice squad, and moving players up and down a depth chart; every team's starters checked; the end of games tuned so that overtime comes about as often as in the NFL; a deleted franchise can always be restored. Nobody has heard these changes yet, so every item below is still to be tested, and so is everything of 0.16.6 and before.

### A radio crew calls the game, in Classic too
With the comments on (F8), both rule sets now have a radio broadcast of the made-up Gridiron Radio Network, modelled on real NFL radio broadcasts. The crew: Walt Kessler calls the game (in the announcer's voice), Gus Delgado is the color analyst and Nora Banks the sideline reporter, each in a voice of their own. Before the coin toss Walt signs on, names the two teams and introduces the crew, Nora reports from the field and Gus gives his first thought; then the coin is tossed, as on the radio. During the game Gus explains some plays and moments, and Walt says the network's name about every seven minutes of game time (once a game, when you have no commercials, a listener's own words), says the score again when nobody has said it for a while, gives the quarter and half updates, and now and then an aside. At the two-minute warning and at half time Walt has a station break before your commercial; at half time Nora reports and Gus sums up. With the N. F. L. rules Walt also says the time left after every second play in the last two minutes of each half, sums up some scoring drives (the plays, the yards and the minutes), and in a franchise game Nora reports a player who was hurt. After the final score Gus sums up, and after the final statistics Walt signs off: his are the last words of the game. Every game has lines of its own: in a season the crew does not open every week with the same words. Classic plays exactly as the original: the broadcast draws only its own random numbers and changes nothing in the game.
- How to test: play a whole game in Classic with comments on (F8 says "comments on"), then one with the N. F. L. rules. Listen for the sign-on and the crew before the coin toss, Nora's note, the quarter updates, the station break at the two-minute warning, Nora and Gus at half time, and the sign-off after the final statistics. Then play the next game in the same session (the next week of a season): the crew opens it with other words. With the N. F. L. rules, the time left late in the second and fourth quarters.
- F9, Rules, Broadcast crew (this was Commentator) says the three names; Enter opens the crew (announcer, analyst, reporter, network) and each takes a name you type. A name you typed stays in the list when you go back to the original one. F9, Rules, Broadcast off silences Gus and Nora; F8 silences the whole broadcast.
- F12 and F11 now ask for the sideline reporter's voice and volume after the analyst's, in Classic too, while the comments and the broadcast are on.
- Every line is in remarks.txt, which Classic now reads too: the pools SGN, CRW, SON, UPD, QUP, STA, ASN, SIN, SHT, SGO, NID, LID, DRV and CLK are new (CUSTOMIZE.md, "The radio broadcast").
- Tell us: whether the crew talks too much or too little, any line said twice in a row, any line said at the wrong moment, and whether Nora's voice is easy to tell apart.

### The original game's jokes and its commentator are gone, in every mode
The owner had all of the original game's commentary taken out: its 142 jokes, the commentator Ghip, and the list of real sports podcasters' names you could give him. This is true in Classic too: Classic keeps the original's plays, rules and sounds, but the announcer no longer tells the original's jokes. The play-by-play, the referee and the stadium sounds stay. The color analyst is now called Gus Delgado, a made-up name, and he is part of the new radio crew (the item above).
- How to test: play a game in Classic with comments on (F8) and listen: you hear the plays, the score and the sounds, and none of the original's jokes. The analyst's lines name Gus Delgado, and F9, Rules, Broadcast crew names him. If your settings had Ghip or one of the podcasters, you now hear Gus Delgado.
- Your old banter.txt, if you had one, is left in the customize folder untouched and is no longer read. To keep a line of your own from it, copy it into remarks.txt as a BN line (CUSTOMIZE.md, "The old banter.txt").
- A game you saved or that was saved automatically before this build still continues.
- Tell us: any joke of the original you still hear, or anything that sounds missing.

### Every team's starters checked: the Giants start J.J. McCarthy
The rosters are now as of October 26, 2026. The game's roster file followed each team's own depth chart page, and those pages are often days behind: the Giants' page still started Jameis Winston after J.J. McCarthy was named the starter for the game of October 25. Every team's starters at all 22 positions were checked against two other depth charts that are kept more up to date (nflverse's, which follows ESPN's, and Sleeper's), against who played the snaps in each team's last two games, and the starting quarterbacks of all 32 teams against this week's news. Where both depth charts agree on a starter, he now starts: 79 positions changed, most of them only the order of the receivers, corners or defensive tackles. Among them: the Giants' quarterback (J.J. McCarthy, then Jameis Winston), the Eagles' backup quarterback (Joe Milton), the Bengals' and Rams' tight ends (Mike Gesicki, Tyler Higbee), the Chiefs' middle linebacker (Nick Bolton), the Jaguars' halfback (Bhayshul Tuten), and the Steelers', Dolphins' and Lions' strong safeties. Where a listed starter hardly played in both of his team's last two games while a backup played nearly every snap, the backup starts (5 positions, the Raiders' right guard Caleb Rogers among them). A player who is hurt for a game or two but not on injured reserve stays his team's starter. The file also has the real roster moves up to October 26. If the rosters.txt and free_agents.txt in your customize folder are exactly the ones 0.16.3 to 0.16.6 made, they are replaced once and yours are kept beside them.
- How to test: a new franchise or a quick game as the Giants: J.J. McCarthy is the quarterback. Then F9, Rules, Depth charts, and the starting lineup of a few teams you know.
- A franchise you already have keeps its own teams (its history is yours). Your own team's starters are yours to set: F9, Rules, Depth charts. The other 31 teams get the new rosters through F9, Customize, "get the latest rosters" once the new rosters are published.
- Tell us: any starter who is wrong, with the team and the position.

### The end of games: overtime about as often as in the NFL
With the N. F. L. rules the computer now decides its fourth downs in the fourth quarter as NFL coaches do. Behind in the last three minutes it never punts. Behind by 1 to 3 late it kicks the field goal that ties or wins when it is in reach (a kick of up to 57 yards), else it goes for it. Behind by a touchdown it goes for it; two scores behind it kicks the field goal that makes it a one-score game. Ahead or tied it punts or kicks. After a fourth-quarter touchdown that leaves it one point or eight points behind, it now kicks the extra point, as most coaches do, instead of going for two. In 10,000 computer games 4.8 percent now go to overtime (2.1 percent before; the NFL about 5.5). Classic is unchanged.
- How to test: play some close games against the computer with the N. F. L. rules. When the computer is behind late, does it go for it on fourth down instead of punting? Three points behind and in reach, does it kick the tying field goal? Does a close game sometimes go to overtime?
- Tell us: any fourth-down or extra-point choice of the computer that sounds wrong, with the score and the time left.

### A deleted franchise can always be restored
A tester deleted a franchise, closed the game with Alt+F4 and could not find the backup. It was there, but the start-up menu said only "start a new game" and nothing said to press Down. Now, when nothing is saved but the backup keeps something you deleted, the menu says so first: "Nothing is saved now, but the backup keeps what you deleted. Press Down for the restore item." "Start a new game" also offers "restore a deleted franchise", and so does F9, Franchise, while you play (only while a backup is there). A deleted saved game or season alone now brings the start-up menu back too. A saved game's record is now said "0 losses", not "0 losss".
- How to test: with the N. F. L. rules start a franchise and save. Start the game again, delete the franchise, close the game with Alt+F4 and start it again: you hear the backup sentence; press Down to "restore the deleted franchise of the ...", then Enter: it comes back with its week and record. Also try "start a new game", "restore a deleted franchise", and F9, Franchise, "restore a deleted franchise".
- Tell us: any restore that does not work (save a problem report right then).

### The radio crew now talks like a real radio crew
The owner had two whole real NFL radio broadcasts found, transcribed with Whisper (speech recognition) and studied: a modern national network call and a classic one. Real crews do not tell jokes about snacks. They say the situation (down, distance, where the ball is, the score, the clock), the analyst gives a reason and what to watch next, and the air between plays is filled with sayings of the sport. So the announcer's asides (142 lines), the twelve hand-offs to the analyst and the nineteen groups of analyst lines (after a touchdown, a sack, a turnover, a field goal, a penalty, at the two-minute warning, at the end of a quarter, at half time, at the end of the game and so on) were rewritten in that manner: 312 new lines, the same moments, the same amount of lines, the same randomness. With the N. F. L. rules and comments on (F8), the analyst explains what worked, and the announcer asks "walk us through that play" instead of making a joke. The notes of the study are in the repository, `spec/RADIO_NFL_STYLE.md`; the recordings and their full text are not published.
- How to test: play a game with the N. F. L. rules and comments on. Listen to the announcer between plays, to the question he asks the analyst, and to the analyst after a touchdown, a sack, a turnover, a field goal, at the two-minute warning and at half time. Do they sound like a radio crew explaining the game? Does any line come too often, or does one sound wrong or too long?
- Tell us: the line (as well as you can say it) and what had just happened. F9, Customize lets you change or switch off any line.

### Free agents checked one by one: only real unsigned players, at their real positions
A tester asked for a full audit of the free agents. Every one of the 834 free agents was checked against the league's data of October 27, 2026 (the 32 teams' own roster pages, the league's weekly rosters and depth charts through nflverse, and Sleeper's player list), and every doubtful player was looked up in the news. 32 were wrong and are gone: 17 are on a team (some under another spelling, such as the Bengals' Dax Hill, and ten on a team's injured reserve), 7 were the same player written twice (Matt and Matthew Judon, Shaq and Shaquill Griffin, and five more), 2 have retired or are on an injured list no source shows, and 6 are not confirmed as free by the second source. 6 real unsigned players were added, among them Mike White and the kicker John Parker Romo. The list now has 808 players, every one with his real age. And every free agent now has his real field position, one of the 22 of a real roster: before, the list said only "offensive line", "defensive line", "linebacker" or "safety", so in a franchise every free lineman became a left tackle and every free safety a free safety. Now Taylor Decker is a left tackle, Joey Bosa a left edge, Bobby Wagner a weak-side linebacker, Vonn Bell a strong safety, Nash Hutmacher (a lineman who moved from defense to offense) a left guard. The full report is in the repository, `spec/FREE_AGENTS_AUDIT_2026-10-27.md`. If the free_agents.txt in your customize folder is exactly one the game made, it is replaced once and yours is kept beside it.
- How to test: start a new franchise, then F9, Franchise, free agents, "sign a free agent": choose the offensive line and listen to the positions (left tackle, guard, center and so on); then the defensive line and the safeties. Tyreek Hill, Bobby Wagner and Justin Tucker are still there; Dax Hill, Ogbo Okoronkwo and Drew Ogletree are not (they are on teams).
- Tell us: any free agent who has signed with a team, retired, or plays another position, and the team or position you know.

### Sign free agents to your practice squad
In a franchise, a tester could not add anyone to the practice squad. The cause: every team starts the season with its real practice squad, which is already full (16 players, or 17 with an international player), and the game only said "your practice squad is full". Now, when the squad is full, the game lists your squad players, the weakest first, and you choose the one to release to make room; one question then says both moves. The NFL's practice squad rules: 16 players, and a 17th place for an international player of the league's pathway program; at most 6 veterans (players with more than two seasons), the others with two seasons or fewer; no age limit and any position; a squad player may be brought up for a game 3 times in the regular season (any number in the play-offs), at most 2 a game, and you may sign him to your roster at any time. So when the squad has its 6 veterans and you want another veteran, the game offers only veterans to release. The add is in two places: F9, Franchise, practice squad, "add a free agent", and F9, Franchise, free agents, "add to the practice squad". You choose the position first, then the player; each is said with his real position, age, rating, and "a veteran" when he is one. F9, Franchise, practice squad also has a new item, "the practice squad rules", which says them.
- How to test: in a franchise in the regular season (at the main menu, before the kick-off), F9, Franchise, practice squad, "add a free agent": choose a position, a player, then the squad player to release, and press Enter to confirm. "hear the practice squad" then has the new player and not the released one. Try the same from F9, Franchise, free agents, "add to the practice squad". Try a veteran (a player in his thirties) when your squad has 6 veterans.
- Tell us: any player the game would not let you sign, and what it said.

### Reorder your depth chart: move any player up or down
A tester asked to move a backup up the depth chart, for example the player at number 4 to number 3. Now, in F9, Rules, Depth charts, in the list of players of any position (open a position, or a place of the starting lineup), U moves the player you are on up one place and N moves him down one place; a digit from 1 to 9 puts him at that place, and the others move down one. The game says what changed: "... moves up to number 3 at wide receiver, ahead of ...", and when the move makes him a starter or takes him out of the starters it says that too. The order is kept until you change it, and the next game uses it. It works in a quick game and a season (for any of the 32 teams) and in a franchise (your own team, not during a game). Enter still makes the player the starter, as before. F1 in the list names the keys, and F5, F6 and the README list them.
- How to test: F9, Rules, Depth charts, choose a team (in a franchise your own), then "wide receivers": go down to the fourth player and press U; he is now third. Press 1 on a player to make him first. Press N on the last player: the game says he is already last. Leave and open the list again: the order is still yours. Play a game and listen for the receivers you moved up.
- Tell us: any move that is not kept, or a player who still plays where you moved him from.

## 0.16.6 (2026-10-26, test build)

The fifteenth test installer. Three fixes from the owner's report: the free agents who sat out last season, three franchises with backups that restore, and problem reports that name the players. Everything of 0.16.5 and before below is still to be tested.

### Free agents who sat out last season, like Justin Tucker
0.16.5 listed only players who were on an NFL roster this season or last season, so Justin Tucker (released in May 2025, unsigned all of 2025) was missing. The list now also has the players whose last season was 2024 and who are still in the news this past year: 836 free agents in all (17 kickers, 9 punters, 8 long snappers, 30 quarterbacks), with Justin Tucker, Taylor Heinicke and Dorian Thompson-Robinson among them. Players who have gone quiet for a year are left out, and so are known retirees the sources do not mark (Derek Carr, Tom Brady). If your free_agents.txt is exactly 0.16.5's, it is replaced once and yours is kept beside it.
- How to test: a new franchise, F9, Franchise, free agents, the kickers: Justin Tucker is there. Look for other unsigned players you know.
- Tell us: anyone still missing, or anyone listed who has signed or retired.

### Three franchises, and backups that restore
You can now keep three franchises. The franchise you have stays franchise 1. "Start a new game", then "a new franchise", asks where it goes: the list starts on the first empty franchise; a full one says its team and season and is replaced only after one more question (it goes to the backup). With more than one franchise, the start-up menu says each one and has "continue franchise 1, the Giants" and so on, and "delete a franchise". Before, a deleted or replaced franchise could be restored only while no other franchise existed, so starting a new franchise locked the older one away, and after you closed the game the start-up menu did not come back for a deleted franchise at all; now it does. Now every kept copy (the three last deleted or replaced of each franchise) can be restored: "restore the deleted franchise of the Giants, season 1" brings it back into its own franchise when that is empty, else into the first empty one; with three franchises the game says to delete one first and keeps the copy.
- How to test: with the N. F. L. rules start a franchise as one team, then "start a new game", "a new franchise", franchise 2, another team. Quit and start again: both franchises are said, and each can be continued. Delete franchise 1 and restore it. Start a new franchise in a full slot, then restore the replaced one: it comes back into the empty slot.
- Tell us: any restore that says it could not be restored (and save a problem report right then).


### A problem report names the real players
This one changes nothing you hear. The debug log hides every name you type, so that a report never holds a private name. It also hid the real players and coaches the game offers you (you only press Enter), so a report about who started at quarterback said only "typed". Now the real players and head coaches of the rosters, the free agents and the coaches file are named in the log; a name you type that is no real player's is still hidden. The log also writes one line at the start of each game with the two quarterbacks the game offered and the two who play, and whether yours came from the season's first game.
- How to test: play the first game of a franchise or a season, then F9, Speech settings, "Save a problem report", and send the file: it lets the maintainer see the quarterbacks by name.

## 0.16.5 (2026-10-26, test build)

The fourteenth test installer. Two fixes from the owner's report. Everything of 0.16.4, 0.16.3 and 0.16.2 below is still to be tested.

### Every real free agent, kickers, punters and long snappers too
The list of real free agents a new franchise starts with had only 170 players: 3 kickers, 2 punters and no long snapper. It now has all 771 players who were on an NFL roster this season or last season, have not retired and are on no team (as of 2026-10-25), at every position: 14 kickers (Younghoe Koo, Cade York, Greg Joseph, Matt Prater, Graham Gano and more), 7 punters (Johnny Hekker, Thomas Morstead and more), 7 long snappers, 140 offensive linemen, 25 quarterbacks. Two public sources must agree that a player is unsigned (nflverse's players table and Sleeper's player feed). The game still makes up a free agent only for a position that has too few real ones. If the free_agents.txt in your customize folder is exactly the copy 0.16.2 to 0.16.4 made, the game replaces it once and keeps yours beside it as `free_agents.txt.before-layout-2`; a file you changed stays yours.
- How to test: start a new franchise with the N. F. L. rules, then F9, Franchise, free agents, and go to the kickers: real kickers, no made-up names. Try the punters, the long snappers and the offensive line too.
- Tell us: a free agent who has in fact signed with a team, or a known unsigned player who is missing.

### A team keeps its real starter until a backup is clearly better
J.J. McCarthy really is a Giant now: the Vikings traded him to the Giants on 2026-09-28, and he is Jameis Winston's backup while Jaxson Dart is on injured reserve. A new franchise starts Winston, as the Giants do. But during a franchise, every time a team's roster changed (a signing, a trade, an injury, a new season) the staff put each position in order of the game's own ratings, and those ratings are made up, not real ones. So a backup rated one point higher took the job: in two-season tests 5 to 8 real starting quarterbacks a season lost their place on their own team (Josh Allen went to the Bills' practice squad, Caleb Williams sat behind Haynes King). Now a man passes the man ahead of him only when he is clearly better: 8 rating points at quarterback, 5 at every other position, and 3 for a man the team just brought in. In the same tests 2 or 3 starting quarterbacks a season lose their place, each to a clearly better man. Your own choice of starters is kept as before. The ratings are still the game's own, so after a few seasons a team's order can still differ from the real one; and an injured starter's place still goes to his backup for the games he misses.
- How to test: start a new franchise as the Giants with the N. F. L. rules: Jameis Winston starts at quarterback (F9, Rules, Depth charts, or the starting lineup), McCarthy is second. Play into the second season and listen to a few teams' quarterbacks: the real starters should mostly still start.
- Tell us: where you heard J.J. McCarthy start for the Giants (a quick game, or which week of a franchise, and whether Winston was hurt), and any real starter who loses his job to a man who is not clearly better.

## 0.16.4 (2026-10-26, test build)

The thirteenth test installer. A fix from a player's e-mail. Everything of 0.16.3 and 0.16.2 below is still to be tested; nothing here has been heard by the owner yet.

### Every position of a depth chart names the man who plays there
A player wrote that at some positions nobody was starting. Many real teams have no strong-side linebacker on their depth chart (they play a 3-4 defense with two inside linebackers), most have no fullback, and one team's only kicker is on the practice squad, so the starting lineup and the depth chart menu said "nobody" there, although the game always put a man on the field. Now each such place names the man who plays it and where he comes from: "strong-side linebacker, Jay Higgins the fourth, number 49, filling in from middle linebacker", "fullback, Justice Hill filling in from halfback", "kicker, Zane Gonzalez, from the practice squad for game day". The man keeps his own position on the roster, and nobody plays two places. Enter on the place still lists everyone who may start there; the man you choose then starts there.
- How to test: with the N. F. L. rules, F9, Rules, Depth charts, the Ravens: "strong-side linebacker" names a linebacker filling in, and "fullback" a halfback filling in; the starting lineup says the same. Go through every position of a few teams, in a quick game and in a franchise (F9, Rules, Depth charts while a franchise is open): no position says "nobody".
- Tell us: any position that still says nobody, and whether "filling in from" is clear.

## 0.16.3 (2026-10-26, test build)

The twelfth test installer. The real players now have their real ages in a new franchise, and the draft, the rookies before the cut, the free agents and the awards say each player's own position. Everything of 0.16.2 below is still to be tested; nothing here has been heard by the owner yet.

### Every real player has his real age in a new franchise
rosters.txt now gives each player's age on 2026-10-25 and how many NFL seasons he played before this one, worked out from the birth dates and first seasons in nflverse's public roster table (and Sleeper's player feed where nflverse has none); every one of the 2,521 players has them. A new franchise gives every real player his real age and seasons, so the veterans are old and the rookies young, as in the real league; the game keeps its ages from 21 to 40, so the few players over 40 are 40 in the game and retire after the first season. The ratings are still the game's own. On each practice squad the six most experienced players count as veterans, as the league's rule allows. In 20-season tests the league stayed as balanced as before.
- How to test: start a new franchise as the Bears with the N. F. L. rules, then F9, Franchise, your roster: Caleb Williams is 24, Tyson Bagent 26, Colston Loveland 22, and on the practice squad Miller Moss 24. Try a team with an old star you know (the Steelers' Aaron Rodgers is 40 in the game).
- Tell us: a player whose age is clearly wrong (say which team and player).

### Your copy of rosters.txt from 0.16.2 gets the ages once
If the rosters.txt in your customize folder is exactly the copy 0.16.2 made and you never changed it, the game replaces it once with the new one with ages and keeps yours beside it as `rosters.txt.before-layout-2`. A file you changed is yours and stays; a line without an age still works (a new franchise then gives that player an age of its own).
- How to test: install over 0.16.2, start the game with the N. F. L. rules, open the customize folder (F9, Customize, "Open the folder with the names and banter files"): rosters.txt has lines like `T17P01 = QB 18 Caleb Williams; age 24; seasons 2`, and your old copy is beside it.

### The draft, the rookies, the free agents and the awards say each player's position
The draft's prospects, your rookies before the roster cut, the undrafted players you sign, the free agents of the market and the awards of each season now name the player's own position ("strong safety", "your halfback") instead of the group word ("safety", "running back").
- How to test: in a franchise, at the draft listen to the prospects; after the draft, F9, Franchise, your roster, End, then Up: your rookies are said with their positions. After a season, the awards and F9, Franchise, history, awards.
- Tell us: any player still said as "defensive lineman", "running back" or "safety" in a franchise list where you expected his own position.

### A note on "get the latest rosters"
The rosters published on GitHub for "get the latest rosters" are still the ones of 0.16.2 (without ages), so this item says you already have the newest. Version 0.16.2 cannot read a rosters file with ages; the rosters with ages will be published once testers use 0.16.3.
- How to test: F9, Customize, "get the latest rosters": with internet it says you already have the newest.

## 0.16.2 (2026-10-26, test build)

The eleventh test installer. The real rosters are now in the Franchise too: its teams, the roster heard by positions, the starting lineup and the choice of who starts at every position, the returners, and "get the latest rosters" (which says you already have the newest until the maintainer publishes a rosters folder). Nothing here has been heard by the owner yet; please test the items below.

### The real rosters of 2026-10-25, read from each team's own pages
The rosters were read again, this time from the raw pages of all 32 teams (their roster and depth chart pages), and compared with two other sources (nflverse and Sleeper); where the sources disagreed, a search of the news settled it. The old file had missed some real players (for example Josh Jacobs, Brian Branch, Christian Kirk and Dre Greenlaw), and every practice squad now has at most 17 men, as the NFL allows. A player called up from the practice squad for one game day stays on the practice squad, as in the real NFL.
- How to test: with the N. F. L. rules, start a quick game as the Bears. Listen to the players named in the game: the quarterback is Caleb Williams; the tight ends Colston Loveland and Sam Roush are said as tight ends, not as wide receivers. Then try your favourite team.
- Tell us: a player who is on the wrong team, missing, or no longer on the team (rosters change every week; say which team and which player).

### Every player has his real position
rosters.txt now writes each player's real position as a real roster lists it: halfback, fullback, left and right tackle, left and right guard, center, left and right edge, defensive tackle, strong-side, middle and weak-side linebacker, free and strong safety, besides quarterback, receiver, tight end, cornerback, kicker, punter and long snapper. The kick and punt returners are written as returners of their own position. The men on injured reserve and other reserve lists are on the team but never play. A game still uses the game's places as before; the full real depth charts come to the Franchise in later sessions.
- How to test: press F9, choose Customize, then "Open the folder with the names and banter files" (it is `%APPDATA%\Kitchensinc Revival\NFL Football 4\customize`), and open rosters.txt: the Bears' lines start with `T17P01 = QB 18 Caleb Williams`, and you find `LT`, `LEDG`, `SAM` and `FS` lines, `IR` lines, and `T17KR1 =` and `T17PR1 =` lines.
- Tell us: if your own changed rosters.txt from an older version is still read as you wrote it (it should be).

### Your old rosters.txt and free_agents.txt are brought up to date once
If the rosters.txt or free_agents.txt in your customize folder is exactly a copy the game made earlier, and you never changed it, the game replaces it once with the new one and keeps yours beside it as `rosters.txt.before-format-2` (and `free_agents.txt.before-format-2`). A file you changed is yours and stays.
- How to test: install over 0.16.1, start the game with the N. F. L. rules, then look in the customize folder: the two old copies are there, and rosters.txt is the new one.

### The free agents of 2026-10-25
free_agents.txt was checked again: a player who has signed with a team since 2026-10-24 is no longer a free agent, a few men released since then are new free agents, and the ages are worked out from the birth dates.
- How to test: start a new franchise with the N. F. L. rules, then F9, Franchise, free agents: Tyreek Hill is there, age 32.

### A new franchise has every team's real roster, man for man
A new franchise with the N. F. L. rules now has exactly the players of the rosters: every team's active roster at the players' real positions and numbers, its practice squad, and its men on injured reserve and the other reserve lists (on the team, never in a game). Nobody is made up and nobody is left off. Your own team is its real roster too. The ratings and ages are still the game's own.
- How to test: start a new franchise as the Bears, then F9, Franchise, your roster: Caleb Williams, Tyson Bagent and Case Keenum are your quarterbacks, Colston Loveland and Sam Roush your tight ends, and Miller Moss is on the practice squad.
- Tell us: any made-up name on any team at the start of a new franchise, or a real player missing from his team.

### A team plays with the players it has
A team with three running backs now runs with those three: the game no longer makes up a fourth, fifth and sixth back. A team that plays a 3-4 defense fills its linebacker places with its outside rushers (its edge players), who keep their own position. The Dolphins, who have no kicker on the active roster, play the practice squad's kicker. In a quick game a team's real kick returner returns kicks even when he also plays receiver.
- How to test: with the N. F. L. rules, play a quick game as the Bears and listen to the running plays: only D'Andre Swift, Kyle Monangai and Roschon Johnson carry the ball. Play a quick game as the Dolphins: Zane Gonzalez kicks.
- Tell us: a ball carrier, tackler or returner who is not on the team, or a player said at a position he does not play.

### The colour commentator speaks less often
You said he talks too much. With the N. F. L. rules and the broadcast on, the colour commentator now says about half as many lines in a game: about 15 instead of about 26. He still opens the game, speaks at half time and after the final whistle, and still answers the big moments most of the time.
- How to test: play a whole game with the N. F. L. rules. He should feel like an occasional voice, not one after almost every play.
- Tell us: if he is now too quiet, or still too often.

### An older franchise is brought to the real positions when it is opened
A franchise saved by an older version is changed once when you open it: every real player gets his real position and number, and a franchise from before 0.16.0 (one quarterback a team) gets its teams' missing real players at once, so the Bears have their backup quarterbacks. The old file is kept as `league.sav.before-format-18` in the franchise folder. Since the later items of this version, who plays is made from each team's real roster (below).
- How to test: open a franchise you saved with 0.15.0 or older, then F9, Franchise, your roster: your backup quarterbacks are there. The franchise folder (in your files, `franchise`) has `league.sav.before-format-18`.
- Tell us: a franchise that will not open, or a team that lost a player when it was opened.

### Every part of a franchise works on the real roster
A franchise team is now its real roster of up to 53 players at their real positions, and everything in the franchise works on it: the roster cut keeps 53 (always two or three quarterbacks, a kicker, a punter, a long snapper, at least eight offensive linemen and enough of every other position, then the most valuable players), the draft has prospects of every real position (offensive linemen and long snappers too, never a "returner"), free agents and practice squad players sign while a team has room on its 53, a trade may swap players of different positions as long as both teams keep enough of every position, a hurt player's place goes first to a fit player of his position who is not starting, and the players on injured reserve and the other reserve lists come back to their teams at the next roster cut. Who starts each game is made from the depth chart: the best of each position first, or your own choice for your team. A franchise saved by 0.16.1 or older is brought to the real roster when it is opened, as above.
- How to test: start a new franchise with the N. F. L. rules and play (or let the staff play) a whole season and an offseason; at the roster cut, listen to who your staff would release, then F9, Franchise, your roster after the cut: 53 players or fewer, at least two quarterbacks, and offensive linemen and a long snapper among them. In the draft, listen for prospects at offensive tackle, guard, center, edge and long snapper.
- Tell us: a team that is short of a position after the cut (no kicker, one quarterback), a roster over 53 in the season, or a draft with no linemen.

### The salary cap of a real 53-man roster
The salary cap is now the cap of a whole real roster for every franchise: 244.2 million (it was 193.2 million for a franchise that kept only 34 players). It was measured so that a new franchise uses the same share of its cap as before (about 86 percent).
- How to test: start a new franchise, then F9, Franchise: your cap space is said in the same way as before; no team starts over the cap.

### Made-up players have the last names of real NFL players
With the N. F. L. rules, every player the game makes up (the draft classes after the first season, the undrafted rookies, the rookies of the roster cut, the stand-ins of injured players, the new young players of the practice squads) now has the last name of a real NFL player, with a first name of the game's own list, and never the full name of a real player of the rosters. The 9,504 last names are in nfl_surnames.txt in your customize folder, where you can change them or add your own. The Classic rules keep the original game's names.
- How to test: in a franchise, reach the draft of the first offseason and listen to the prospects' names; or F9, Customize, open the folder, and open nfl_surnames.txt.
- Tell us: a made-up player whose full name is a real player's name.

### Your roster is heard position by position
F9, Franchise, your roster is now one list in the order of a real team's positions: quarterbacks, halfbacks, fullbacks, wide receivers, tight ends, left tackles, left guards, centers, right guards, right tackles, left edge, right edge, defensive tackles, the three kinds of linebacker, cornerbacks, free and strong safeties, kickers, punters and long snappers. Each heading is said with its count ("quarterbacks, 3"), and each player with his own position, whether he starts or is the second or third man, his number, rating, age, potential and contract, and "kick returner" or "punt returner" when he returns kicks. After the positions come the practice squad, the reserve lists (injured reserve and the like) and, in the draft, the rookies who wait for the cut. "On the bench" is gone: a player without a place in the game's 34 places is simply on the roster.
- How to test: start a franchise (or open one), F9, Franchise, your roster. Down goes player by player and says a heading when a new position starts. Left and Right (or Page Up and Page Down) go from position to position; Home and End go to the ends; a letter goes to the next position that starts with it (L: left tackles, then left guards, then left edge; E: the tight ends). T does nothing, because T calls a time out in a game. F1 says the keys.
- Tell us: a player said at a wrong position, a position that is missing, a letter that goes somewhere you did not expect.

### The starting lineup: choose who starts at every position
F9, Rules, Depth charts, your team (any of the 32 teams in a quick game or a season; your own team in a franchise): the first item is now "starting lineup", one list with every starter: quarterback, halfback, fullback, three wide receivers, tight end, the five linemen, left edge, two defensive tackles, right edge, the three linebackers, two cornerbacks, free safety, strong safety, kicker, punter, long snapper, kick returner and punt returner. Each line says the position, the starter and his number. Enter on a line lists the men who may start there: the men of that position first (the one who starts now is marked), then the men who can move there from the other side or the other role (a right tackle at left tackle, a free safety at strong safety, a halfback at fullback, one linebacker position for another), then the practice squad's men of the position. Enter on a man makes him the starter; the man who was there takes his old place. The positions follow in the same menu (the old groups are gone), each with its first man, and so do the key downs and moments.
- How to test: F9, Rules, Depth charts, choose the Bears, "starting lineup": Down through the lines; Enter on "left tackle", Down to the right tackle in the list, Enter: you hear that he moves from right tackle to left tackle and starts there. Play a quick game: he is the left tackle in the set-up. In a franchise do the same: the choice is kept in the franchise and is still there after a trade, an injury or the roster cut.
- Tell us: a player you cannot choose who you expected, or a choice that is not in your game.

### A practice squad player can start
In the lineup list a practice squad player is marked, and choosing him as a starter brings him up. In a quick game or a season the game brings up at most two men from the practice squad for one game (the real rule), and the third is refused with a sentence. In a franchise the game asks the practice squad's own questions first (the contract, and whom to release when your 53 are full) and then makes him the starter.
- How to test: lineup list, a position, Down to the end of the list: the squad's man ("practice squad"); Enter. In a franchise, in the regular season, you are asked to sign him.

### When a starter you chose leaves the team
If a player you chose to start is traded, released, retires or is no longer on the team's roster file, the next man starts, and the next time you open the roster or the depth charts you hear one sentence ("Darnell Wright is no longer on the team; Braxton Jones starts at right tackle").
- How to test: choose a starter in a franchise, trade him away (F9, Franchise, trades), then open the lineup: you hear the sentence once.

### Kick and punt returners start elsewhere too (franchise games)
In a franchise game the kick returner and the punt returner you chose (and the team's real ones) now return on top of their own place, as in a quick game: a starting receiver can return punts. Before, a franchise game used only men who started nowhere else. A returner who is hurt is replaced by the next man of the list.
- How to test: franchise, F9, Rules, Depth charts, "punt returner": choose your best receiver. Play the game: he returns punts.

### A man is said at his own position everywhere
In the franchise a player is named with his real position in every list and sentence: "T.J. Watt, left edge", "halfback", "free safety", not "running back", "defensive lineman" or "safety".
- How to test: free agents, trades, the injury report and the news: positions are the real ones.

### Players with the same name
Six names belong to two real players. In a list of players from more than one team (trades, free agents) such a name is said with the position and the team ("Justin Jefferson, strong-side linebacker, Browns"), and two of one name on your own team by their numbers ("DeVonta Smith, number 6"). The play-by-play says the name only.
- How to test: trades, "ask a team for a player", Browns or Vikings: Justin Jefferson is said with his position and team.

### A trade can give a player of another position
When you ask for a player, the list of players you give ends with "a player of another position", which asks for the position and lists your players of it. Before, you could only give a player of the position you asked for.
- How to test: F9, Franchise, trades, ask a team for a player, choose a position and a player; at the list of your players go to the last line.

### What a position does (D)
In the lineup and in the positions' items of the depth charts, D says a plain description of the position, for a person who knows nothing of football ("The center is the middle lineman. He snaps the ball to the quarterback at the start of the play, then blocks."). The descriptions are in PLAYS_GUIDE.md too.
- How to test: lineup list, press D on a line, then Down and D again. The menu stays where it is.

### The keys are documented
F5, F6 and the Keys section of the README name the roster's keys, Enter on a position of the depth charts and D there.
- How to test: F5 and F6, and `README_keys.md`.

### Get the latest rosters
F9, Customize, "get the latest rosters" (N. F. L. rules), and F9, Franchise, "get the latest rosters" ask the game's page on GitHub for the newest rosters.txt and free_agents.txt, only when you choose it, never by themselves. A newer file is checked (every team, every position, the practice squads) and written to your customize folder; your earlier files are kept beside it as `rosters.txt.before-<date>` and `free_agents.txt.before-<date>`. A rosters.txt you wrote yourself asks one yes or no question first ("no" first), because your lines would be replaced. The game says "You now have the rosters of <date>", "You already have the newest rosters, from <date>" or why it could not (no connection, a file that failed its checks). The page has no rosters folder yet, so until the maintainer publishes one the game says you already have the newest.
- How to test: F9, Customize, "get the latest rosters" (the last item): with no internet you hear that the rosters could not be downloaded; with internet, that you already have the newest. Escape stops the wait.

### A franchise in progress can be brought up to a newer roster file
When a franchise was made from older rosters than the file you have, the game offers it once when you open the franchise: "There are newer real rosters, from <date>. Bring the other 31 teams up to them? Your own team is not changed." The first answer is "No, keep my league as it is", so Enter changes nothing. With "yes" the 31 computer teams get the file's players at their positions, numbers and lists (a player moves with his contract; a real player the file has nowhere becomes a free agent; a team over 53 is cut to 53), your team and your players are never touched, and the old file is kept as `league.sav.before-rosters-<date>`. It is never offered during a game, the draft or the roster cut.
- How to test: only possible once a newer rosters.txt exists (the maintainer's step); then open an old franchise.

### Your old franchise says what was done to it
When a franchise saved by an older version is converted as it opens, the game says so once: "Your franchise now has the real rosters' positions: every player has his real position, and <n> real players joined their teams."
- How to test: open a franchise saved by 0.15.0 or older; you hear the sentence once.

## 0.16.1 (2026-10-25, test build)

Nothing new to play in this build: it is the same game as 0.16.0 after a tidy-up of the project. The source folder of the project, which had an older name, is now called `game`, and the old word is gone from the texts of the program and from its log.

### The log and the problem report say the game's name
The debug log used to carry an extra old word between the name and the version, and again at its end. It now says "NFL Football 4 <version> starting" and "NFL Football 4 closed". Nothing else in the log changed.
- How to test: play a minute, close the game with the usual exit, then F9, Speech settings, "Save a problem report" (or open the newest file in the `logs` folder of your files): near the start of the log you find "NFL Football 4 0.16.1 starting" and near its end "NFL Football 4 closed", with nothing between the name and the version.
- Tell us: only if the installed game does not behave exactly like 0.16.0. Anything that sounds or plays differently is a mistake of this tidy-up.

### Folder names in the documents
The guides that come with the game (`docs` folder: keys, N. F. L. rules and Franchise, plays, customize, problem reports) and the README on GitHub name the folders `game/src`, `game/tests` and `game/tools`. The keys and the plays are the same.
- How to test: open `docs\README_keys.md` in the program folder: the keys are the same as in 0.16.0 and as F5 lists them.

## 0.16.0 (2026-10-25, test build)

### A franchise keeps every team's real 53 players
A franchise team used to carry only the 34 players the game plays. Now every team carries its real 53-man roster of 2026-10-24: the 34 who play in the game's places and up to 19 more on the bench, the backup quarterbacks, the extra receivers and defenders, the offensive line and the long snapper too. The bench plays no snaps and does not change a team's strength, so games come out as before; it is paid, grows older, improves, retires, and is signed again or let go like everyone else. In every player list a bench player is said as "quarterback on the bench" (or his own position). The salary cap is 54 million higher (247.2 million in all), so the bench's pay leaves the players in the places the money they had. The ratings and ages of real players are the game's own, not real ones (the game keeps facts only: names and positions).
- How to test: start a new franchise with the N. F. L. rules. F9, Franchise, your roster: the title says how many players you have, how many play in the places and how many are on the bench, for example "53 of 53 players: 34 in the game's places and 19 on the bench". Open the quarterbacks, the receivers and the offensive linemen: the bench players are the real backups of your team, each said "on the bench".
- Tell us: are the bench players the right men for your team? Is the roster list easy to move through with 53 names?

### A hurt player's place goes to the bench first
When a player of a franchise team is hurt, the staff now puts the best healthy man of the bench at his position in his place, so a hurt quarterback is played by the backup quarterback, never by a made-up stand-in while the team has one. The bench man plays at his own rating, but never better than the hurt man. In the week's to-do list and in F9, Franchise, injury report, "who starts for" now lists the bench players of that position too.
- How to test: play franchise weeks until one of your players is out. Open "who starts for" in the injury report: the bench players of his position are in the list, the staff's choice first. Choose one; in the game, listen for his name.

### The roster cut keeps 53
At the roster cut the best players of each position take the 34 places, as before, and up to 19 more stay on the bench: a backup quarterback, the long snapper and five offensive linemen first, then one backup at each position, then the best of the rest. Only the players beyond 53 are released. The draft's rookies and the undrafted free agents join the bench when they do not win a place. Since the draft makes no linemen and no long snappers, a bench that has fewer than one long snapper and five linemen gets young made-up ones at the cut. If you choose your cut yourself, the game asks "your roster has 58 players and room for 53. choose who is released." until your roster fits, the staff's choices first.
- How to test: play a franchise into the offseason, through the draft, to the roster cut. Choose "choose yourself" and release players until it stops asking. Then F9, Franchise, your roster: 53 players.
- Tell us: did the staff keep the players you would have kept?

### Bench players in trades, signings and the depth chart
- Trades: in F9, Franchise, trades, the lists of players now include the bench of each team; a bench player you trade away takes the other man's spot, in a place or on the bench.
- Free agents in the season: when your bench has room, a free agent you sign joins it and nobody has to be released; when the bench is full, you may release a bench player of the same position for him.
- Depth charts (F9, Rules, Depth charts in a franchise): each position lists its bench players after its starters and backups. Enter on a bench player makes him the starter, and the last man of the places goes to the bench; the game says so.
- Quarterbacks (F9, Rules, Quarterbacks, your own team): your backup quarterbacks of the bench come after the starter. Enter on one makes him the starter and the starter goes to the bench, with no release. A practice squad quarterback you make the starter signs to the bench first, and the starter goes to the bench.
- How to test: F9, Rules, Quarterbacks, your team, Down, Enter on the backup: the game says he starts now and the starter goes to the bench. Play the next game and listen for his name. F9, Rules, Depth charts, your team, a position, Enter on a bench player: the game says he is first and who went to the bench.
- Tell us: did you ever expect someone to be released who was not, or the other way round?

### A franchise saved by an older build
A franchise saved by 0.15.0 or older opens as it was, with nobody on a bench yet; its next roster cut fills the benches from the draft, the undrafted rookies and the free agents. Nothing is made up for its past. The cap is the new one from the moment it opens.
- How to test: keep a copy of a franchise from 0.15.0 (the `franchise` folder in your files), open it in 0.16.0 and play to the next cut: F9, Franchise, your roster then shows the bench.

## 0.15.0 (2026-10-24, test build)

### Every player at his real position
A tester heard a backup quarterback playing wide receiver. That is fixed: every player in a game and in a franchise now plays only his own position, taken from the teams' real depth charts of 2026-10-24. A quarterback is never a receiver, a safety is never a cornerback, a receiver is never a running back. When a team has too few real players of a position for the game's places, the game makes up a player for that place instead of moving someone from another position. In a franchise saved by an older build, a real player who sits at another position's place is given a made-up name there once, and the log says so.
- How to test: start a game with the N. F. L. rules between two teams, for example the Bears and the Bills. Listen to who catches the passes and who carries the ball: receivers and tight ends catch, running backs run, and no quarterback but the starter is named. F9, Rules, Depth charts (next item) lets you hear each team's players by position.
- Tell us: did you hear any player at a position that is not his?

### The starters play the most, like Madden
The original game picked the ball carrier and the tacklers at random, every player alike, so a fourth receiver caught as many passes as the first. Now the starters get most of the plays, as in a real game and in Madden: on a run the first running back carries about 60 times in 100, the second 25; on a pass the first receiver is thrown to most, then the second, the tight end and the third; the starting defenders make most of the tackles. In a franchise, a better-rated player also plays a little more. Classic keeps the original's draws.
- How to test: play a whole game with the N. F. L. rules and listen to the names: the first running back and the first two receivers should be heard much more often than the others, and the backups now and then.
- Tell us: does the share feel right? Too many plays for the starter, or too few?

### Set your starters: depth charts
F9, Rules, Depth charts (the item after Quarterbacks) lists the teams. Enter on a team gives its groups (running backs, wide receivers, tight ends, defensive linemen, linebackers, cornerbacks, safeties, kickers, punters, returners), each said with its first man. Enter on a group lists its players in order; Enter on a player makes him the first, and the next game plays him as the starter. "Back to the real order" undoes the team's changes. In a franchise the menu works on your own team, each player with his rating and age, and your order is kept in the franchise file; "back to the staff's order" gives it back to the staff. A new franchise gives each position's best rating to its real starter.
- How to test: F9, Rules, Depth charts, Enter on the Bengals, Enter on running backs, Down, Enter: the game says the second back "is now the first of the running backs". Start a game with the Bengals: that back carries most of the runs. Then choose "back to the real order".
- Tell us: are the groups and their names easy to move through?

### Your players for the key downs and moments
In the same team menu, "key downs and moments" lets you name who gets the ball on third and fourth down, in the red zone (inside the other team's 20) and in the last two minutes of a half, a back for the runs and a receiver for the passes. The man you name gets the ball about 60 times in 100 in that situation, the others share the rest. "The starter" (the first item of each list) clears your choice.
- How to test: F9, Rules, Depth charts, a team, "key downs and moments", choose "third and fourth down, the receiver", choose a receiver. The game says "on third and fourth down," then his name, "gets the ball most of the time". Play a game with that team: on third downs listen for his name.
- Tell us: does he get the ball too often or not enough?

### No music and no celebration sounds of the original
With the N. F. L. rules the game no longer plays the original game's start-up music (also heard at the exit, at half time and in the volume test) or its touchdown celebration sounds. The game starts with the welcome sentence at once, a touchdown is the announcer and the crowd. Classic keeps the original's music and celebrations.
- How to test: start the game with the N. F. L. rules: no music before or under the welcome. Score a touchdown: no celebration sounds after it. Switch to Classic (F9, Rules) and start again: the original's music is back.

### Your own music and celebrations
Put your own files in the sounds folder (F9, Sounds, "Open the sounds folder"):
- `music.wav` plays at the start (repeating until the welcome ends), at the exit, at half time and in the volume test.
- `celebration1.wav`, `celebration2.wav` and so on play after a touchdown, at half time and after the Super Bowl, 8 to 15 of them each time, as the original did with its own.
Wav, ogg, flac and mp3 work. Without these files the game plays nothing there. A later build may ship the maintainer's own music and celebrations; yours always come first.
- How to test: copy any short sound file into the sounds folder as `celebration1.wav` and score a touchdown with the N. F. L. rules: you hear it several times. Copy a longer one as `music.wav` and start the game: it plays under the start and stops when the welcome ends.
- Tell us: did anything sound cut off or too loud?

## 0.14.0 (2026-10-24, test build)

### Trades: choose the team first, then the position
"Ask a team for a player" (F9, Franchise, trades, the third item) asks which team you want to trade with, then which position, then which of its players, then whom you give. The old list of every team's players of a position is still there as the fourth item, "the league's best at a position".
- How to test: in a franchise season before the trade deadline, F9, Franchise, trades, "ask a team for a player". In the list of teams, type the first letters of a team's name (or use Up and Down) and press Enter. Choose a position, a player, then one of your own players of that position. Then comes the picks menu (next item): Enter on its first item, "send the proposal", sends it, and the other team answers.
- Tell us: is the order team, position, player, your player easy to follow?

### Add your draft picks to a trade, and ask for theirs
After you choose whom you give, a short menu lets you add your own picks of the coming draft and ask for the other team's, as the computer teams do. Each pick is said with its round and whose pick it was ("your round 2 pick", "their round 1 pick", "the round 3 pick of the Bears"). A side adds at most 2 picks. The other team answers by the same rule it uses for its own trades: when your offer is not enough, it says "the Bears want more than that" and names the picks of yours it asks for, and you accept with Enter or say no with Escape. From the draft to week 1 a trade is player for player, and the game says so.
- How to test: in the picks menu, "add one of your picks", "ask for one of their picks" and "take a pick out" each open a list. The first item says the picks so far. Try asking for their first-round pick and offering nothing: they should ask for picks of yours. Then F9, Franchise, trades, "your draft picks" should show the picks that moved.
- Tell us: are the pick names clear? Does the other team's answer feel fair?

### You choose who starts for an injured player
When one of your players will not play the week's game (he is out, or he is doubtful or questionable and rests), the week's to-do list asks who starts in his place: the staff's choice first, so Enter keeps it, then every other fit player of his position, the best first, each with his position, rating and age. For a kick returner the choices are your running backs and receivers. Your choice holds until he is fit again. F9, Franchise, injury report has a line "who starts for" under each such player: Enter on it lets you choose or change. With the staff handling the to-do list (F9, Franchise, settings) nothing is asked and the staff chooses.
- How to test: play a franchise season until one of your players is hurt (the injury report after the news names him). In the next week's to-do list, choose the second answer: the game says who starts in his place, and the play-by-play names him in that place. Also try F9, Franchise, injury report, the "who starts for" line.
- Note: the man you choose takes the hurt player's place and its plays; the place is still played at the backup level, so your choice changes who is named, not the team's strength.
- Tell us: does the question come at the right moment in the week?

### The real NFL rosters of 2026-10-24, with the practice squads
rosters.txt now holds every team's whole active roster as the teams' own sites showed it on 2026-10-24 (up to 53 players, the offensive linemen and the long snapper too) and each team's practice squad (the lines that start with PS). A game plays the same positions as before, from these players. A new franchise's practice squads are the real ones; made-up young players only fill places still open.
- Your rosters.txt (in the customize folder) is replaced once if you never changed it; the old one is kept as `rosters.txt.before-2026-10-24`. If you changed it, it is yours and stays: delete it to get the new players.
- Not yet: a franchise still keeps 34 players a team (the places the game plays). Keeping all 53 on the team (the backups, the offensive line, the long snapper) comes in a later build.
- How to test: F9, Rules, Quarterbacks lists each team's quarterbacks with no practice squad players. Start a new franchise: F9, Franchise, practice squad, "hear the practice squad" names real players (for the Bengals, Sean Clifford is the squad's quarterback). Open rosters.txt in the customize folder: each team ends with its PS lines.
- Tell us: did you hear any name said wrongly?

### The real free agents in a new franchise
The new file `free_agents.txt` lists 155 real NFL free agents (researched 2026-10-24 from free agent lists; no ratings are copied from anywhere: the game makes up each free agent's rating). In the first season of a new franchise they are the free agents of F9, Franchise, free agents; the game makes up a free agent only for a position the list has too few of. Offensive linemen on the list wait for the later build that keeps all 53. You can change the list like the other customize files.
- How to test: start a new franchise, F9, Franchise, free agents, "sign a free agent", choose a position: the names are real (Tyreek Hill is among the receivers).
- Tell us: has anyone on the list signed with a team since?

## 0.13.0 (2026-10-23, test build)

### Get the latest NFL calendar
A franchise plays the real 2026 schedule. When the NFL releases a new season's schedule, it is published in the game's GitHub repository, and the game can fetch it, only when you ask.
- How to test: F9, Franchise, the last item, "get the latest calendar". The game says it is asking, then one sentence: today GitHub has only the 2026 calendar, so it should say you have the newest one already. Unplug the network or turn Wi-Fi off and try again: it should say it could not reach GitHub. Press Escape while it is asking: it should stop at once.
- Tell us: is the waiting sentence clear? Did anything take longer than about 15 seconds?

### The NFL's 14-team play-offs in a franchise
A franchise on the real calendar now has the NFL's play-offs: 7 teams in each conference, and only the top seed rests in the wild card round (six wild card games). The division round is reseeded: the top seed plays the lowest seed left. Classic and a franchise on the original's 16 weeks keep the original's 12 teams. A franchise saved in the middle of its play-offs by 0.12.1 finishes them as they began.
- How to test: play a franchise season to the end (F9, Franchise, franchise settings, the staff and a short offseason make it faster). After week 18 the game names the division winners, three wild cards in each conference and "the top seeds ... have the only byes of the wild card round". Listen to the wild card games: six of them.
- Tell us: does the end of the regular season tell you enough about who plays whom?

### Trades from free agency to the deadline
Trades are open in the offseason from free agency on: before the draft, after it, after the roster cut and before week 1, then in the season until the deadline. They are closed while the draft is under way and while the roster cut is decided, and from the draft to week 1 a trade is player for player (no draft picks).
- How to test: in a franchise's offseason, at the end of the draft stage and at the end of the roster cut stage, press F9, Franchise, trades, and offer a player or ask for one. During the cut's own question the menu should say trades are closed. "Your draft picks" after the draft should say picks can be traded again when the season begins.

### Every team's quarterbacks, and you choose who starts
F9, Rules, Quarterbacks (the item before Reset) lists every team's quarterbacks with the starter first. Outside a franchise, Enter on a team lists its real quarterbacks and Enter on one makes him the starter from the next game; the choice is kept, and a new franchise starts with him. In a franchise the list has every team's starter and its practice squad quarterbacks; on your own team, a practice squad quarterback you make the starter signs to your roster and your starter is released (the game says the dead money and asks first).
- How to test: with the N. F. L. rules and no franchise, F9, Rules, Quarterbacks, choose a team and its second quarterback, then play a quick game with that team: the game names him as your quarterback. In a franchise, open the list on your own team and choose a practice squad quarterback.
- Tell us: in a franchise, would you rather keep the old starter as a backup? (The franchise roster has one quarterback place, so this build releases him.)

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
