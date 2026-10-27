## The N. F. L. rules and the Franchise

This section goes into the repository's README at P11 (S11.1). It is written for a player who uses a screen reader and the keyboard only.

NFL Football 4 plays Jim Kitchen's game exactly as he made it when the Rules setting is Classic. With the setting "N. F. L. rules", the
default for a new player, the game adds seven features that follow the rules of the National Football League:

- a real game clock of 15 minutes a quarter, with time outs for both teams and the two-minute warning;
- penalties, called by the officials, that you may accept or decline when the other team commits them;
- onside kicks, for you (the game asks you when it makes sense) and for the computer;
- quarterback runs: the sneak, the keeper, the draw and the scramble;
- replay challenges and the replay official's reviews of close plays;
- playbooks in seven styles, for your team and for the computer's teams;
- a Franchise: a league of 32 teams that lasts from season to season, with ratings, aging, the draft, contracts and the salary cap,
  free agency, trades, injuries, coaches and history.

### Choosing the rules

1. Press F9. This is the menu of the added functions.
2. Choose Rules and press Enter.
3. Item 1 switches between Classic and N. F. L. rules. Items 2 to 9 switch each feature on or off: time outs, replay challenges,
   quarterback runs, onside kicks, the onside question, penalties, the offense playbook and the defense playbook. Item 10 puts them all
   back to their defaults.
4. A change applies from the next game. A game in progress keeps its rules, and a saved game keeps the rules it was played with.

### Playing with the N. F. L. rules

- The play menus have new items after the plays: Challenge the Ruling (letter C), Time Out (reached by its number; the T key calls a time out at once, anywhere in a game, until the play is run) and, always last, Save Game
  (letter S).
- When the other team commits a foul, the game says what accepting and what declining would give, and asks you. A accepts, D declines,
  Up and Down change the answer, Enter takes it, F1 says the flag again. S saves the game with the question kept, when it can be kept (not on a score, a turnover, a try or
  the last second of a quarter); when you load that game, the question is asked again first. Where it cannot be kept the game says so.
- F1 in a play menu also says whether the clock is running and how many time outs each team has. F4 says the time left.
- Overtime follows the 2026 rules: a new coin toss (the visitors call it, H or T, then R receives or K kicks off), and each team gets the
  ball once unless the first drive ends in a safety; after that the next score wins. In the regular season (and in a single game) there is
  one period of 10 minutes, and a game still tied at its end is a tie: the standings and the season files count ties, and the Franchise
  too. Play-off overtime has periods of 15 minutes until there is a winner. Coaches cannot challenge in overtime. With Classic rules the
  original's sudden death stays.
- F5, F6 and F7 have added lines that explain the new keys, the rules and the words.

### The Franchise

Start a new season with the N. F. L. rules and answer "franchise" when the game asks which kind of season you wish to play. Your
league is kept in the folder `franchise` inside `%APPDATA%\Kitchensinc Revival\NFL Football 4`: `league.sav` and a copy of the save
before it, `league.previous.sav`, and `history.txt`, which you can read in Notepad. If league.sav is ever damaged, the game uses the copy
and tells you. F9, Franchise has your to-do list, the news, your roster, the league history, team ratings, the salary cap, free agents,
trades, the injury report, your job and staff, the franchise settings, and the way back to a classic season. Injuries happen only in a
franchise, never in a quick game or a classic season.

**The schedule.** A franchise plays the league's real calendar. The first season is the real 2026 NFL season: 18 weeks, 17 games for
every team and one bye week, with the real opponents and the real home and away games (the file `schedule_2026.txt` in the program's
`assets\data` folder; the facts were read from the public nflverse schedule table, which follows the NFL's release, and checked against the
NFL's announcement of the opener and of a team's last week; the source repository states no license, so only the facts of the schedule are used: the week, the two teams and the date). In your bye week the game tells you so and plays the other teams' games. The play
offs follow week 18. The NFL publishes each year's schedule only when it is released. When it is, the maintainer publishes it in the game's
GitHub repository (the `calendars` folder), and F9, Franchise, "get the latest calendar" (the last item) downloads it, only when you choose it:
the game checks that it is a whole calendar, saves it in your customize folder and says what it got, or why not. You can also put a
`schedule_<year>.txt` in your customize folder yourself. A season plays its own year's calendar when the game has one; otherwise it uses the
newest calendar the game has with the teams relabeled (the divisions of each conference rotate), which gives every team other opponents and
keeps every rule of the calendar. That is an approximation, not the NFL's own rotation. A franchise that was started before this version keeps
the season it is in, with the original's 16 random weeks, and plays the real calendar from its next season. If the calendar file is missing or
damaged, the game says once that the real calendar could not be read and plays that season with the original's 16 weeks; the next season tries
the file again.

**The play-offs.** A franchise on the real calendar has the NFL's play-offs: 7 teams in each conference, the four division winners seeded 1 to 4
by their record and three wild cards seeded 5 to 7. Only seed 1 rests in the wild card round, where 2 hosts 7, 3 hosts 6 and 4 hosts 5. In the
division round seed 1 hosts the lowest seed left and the other two winners meet at the better seed, and the better seed hosts the conference
championship. At the end of the regular season the game names the division winners, the wild cards and the two teams with a bye. The order of
the teams follows the game's own rule (the most wins, a tie counting half a win), not the NFL's long list of tie-breakers. Classic and a
franchise on the original's 16 weeks keep the original's 12 teams.

**The real roster.** Every franchise team is its real roster of up to 53 players, each at his real position (quarterback, halfback, fullback,
wide receiver, tight end, left and right tackle, left and right guard, center, left and right edge, defensive tackle, strong-side, middle and
weak-side linebacker, cornerback, free and strong safety, kicker, punter and long snapper), with a depth chart. The original's 34 places (six
backs, six receivers, seventeen defenders, two returners, two kickers and the quarterback) are only the view of that chart that the game plays:
a team with three running backs runs with three, a 3-4 team's edge players fill its linebacker places, and the offensive line and the long
snapper, who have no place in the original, are on the roster, paid and in every list. A new franchise is exactly the rosters of rosters.txt
(the game gives the ratings; since 0.16.3 every real player has his real age and seasons from rosters.txt, kept within the game's 21 to 40). When a player is hurt, the staff's first choice for his place is the best healthy man of his position
(never rated above the hurt man), so a hurt quarterback's place goes to the backup quarterback; "who starts for" in the to-do list and the
injury report lists those men too. At the roster cut every team keeps 53: two or three quarterbacks, a kicker, a punter, a long snapper, at
least eight linemen and enough of every other position first, then the most valuable players; the draft has prospects of every position, and
the made-up players of later classes take the last names of real NFL players. The salary cap is 244.2 million. F9, Franchise, your roster is
heard position by position (headings with their counts, each player with his own position, his depth, his number, his rating and age, his
contract and whether he returns kicks), then the practice squad, the reserve lists and the draft's rookies; Enter on a player makes him a
starter, a returner, or changes his name. F9, Rules, Depth charts has the starting lineup and chooses who starts at every position, from the
players on the team and, with a practice squad player, by bringing him up. A franchise saved by an older version is brought to this model when
it is opened.

**Practice squads.** Every team keeps a practice squad of up to 16 players (at most 6 of them veterans), the players who practice with the team but do not play unless they are elevated or signed. The squads are formed at the start of each season from the players cut and let go in the offseason, each team taking its own first; places nobody filled get young made-up players, so a new franchise has full squads from week 1. When an injury leaves a position with nobody fit to play, a squad player of that position is elevated to play (up to 3 times in a regular season, any number of times in the play-offs) before a made-up stand-in is used, and the week's injury report says so. F9, Franchise, practice squad (the tenth item) lets you hear your squad, sign a squad player to your roster for the minimum salary, add a free agent of the season to the squad, or release a squad player. Squad salaries count against the salary cap. The squads end with the season. Other teams do not sign players from your squad in this version.

**Names of new players.** The players of the real rosters keep their real names. Every player the game makes up (a free agent of the season,
a draft prospect, an undrafted rookie of the roster cut, a stand-in for an injured player) has a first and a last name. A franchise saved by an
older version gets the first names when it is opened; the players of your own team keep the names you gave them.

**Free agents and trades.** In the regular season, F9, Franchise, free agents lets you sign a free agent any week before the kick-off: choose
the position, the player and, when you have no open place there, the player of that position you release (his dead money counts against the
salary cap). Trades (F9, Franchise, trades) are open from free agency of the offseason until the trade deadline, which is the kick-off of week 10
of the real calendar (the NFL's deadline of 2026 is the day after week 9) and of week 9 of a season with the original's 16 weeks: before the
draft, after it, after the roster cut and before week 1 too, as in the NFL. They are closed while the draft is under way and while the roster
cut is being decided, and from the draft to week 1 a trade is player for player (draft picks can be traded again when the season begins). The
news at the start of the season says where they are, and the week before the deadline, its last week and the week after it are told too.
The picks you can trade are those of the coming draft and, since 0.16.10, those of the draft after it, as NFL teams trade them a year ahead: in
your first season (2026) the coming draft is the 2027 draft and the one after it the 2028 draft. A pick of the later draft is said with its year
("your 2028 round 2 pick") and comes after the coming draft's picks in the lists; it is worth a little less than the same round's pick of the
coming draft (about three quarters), and when its season begins it simply becomes a pick of the coming draft, owned by whoever got it. The computer
teams trade them too.

**Quarterbacks.** F9, Rules, Quarterbacks (the item before Reset) lists every team's quarterbacks. Outside a franchise they are the real
players of the rosters, the starter first; Enter on a team lists its quarterbacks, and Enter on one makes him that team's starter from the next
game (the choice is kept in settings.txt, and a new franchise starts with him as the team's quarterback). In a franchise the list has every
team's starter, its backup quarterbacks on the bench and its practice squad quarterbacks. On your own team, Enter on a backup of the bench
makes him the starter and the starter goes to the bench; a practice squad quarterback you make the starter signs to the bench for the minimum
and then starts, and the starter goes to the bench (when the bench is full, your starter is released instead: the game says his dead money and
asks first). The other teams' staffs choose their own starters.

### Your own words

The announcer's remarks of the added features (remarks.txt), the names of the fouls (penalties.txt), the playbooks (the folder
playbooks), the franchise's news (news.txt) and the injuries' words (injuries.txt) are in the customize folder and can be changed in any text
editor. CUSTOMIZE.md explains every file. With the Rules setting Classic the game never makes or reads them.

### Saved games, seasons and the start of the game

When the game starts and something is saved (a saved game, a game that was not finished, a season or a franchise), the game says one sentence
about each of them and asks what to do. Up and Down and the digits choose, Enter takes the choice, F1 says it again. The first item is what
the original game did, so Enter alone continues it. The items are: continue the saved game, choose another saved game, continue the season,
continue the franchise, start a new game, delete the saved game, the season or the franchise, and restore what was deleted.

- Nothing is loaded, deleted or replaced without a key from you. A delete asks again and starts at "no". A deleted saved game, season or
  franchise is moved to the backup, not erased, and the last one can be restored until you delete another.
- A saved game is kept until its game is over. The original game erased it as it loaded it; this game does not, so a crash or a closed
  window never loses it. When the game ends, the saves of that week move to the backup folder (the last three are kept) and the game says so.
- The game writes an automatic save at every play. If the program stops in the middle of a game, the next start offers "the game that was not
  finished" and goes on from the same play with the same outcomes.
- Save Game asks which of three places to use (the game's own place first, or the first empty one), says what a place holds before it is
  replaced and asks once, and then asks whether to quit (the first item) or keep playing.
- A saved game that is damaged, in use by another program, from a week that is over, or without a season is named and left where it is. Only
  you move it, by deleting it.
- A new game asks what kind (a new season or a new franchise, the last kind first). If it would replace your season, it says so, asks, and
  keeps the old season and its saved games in the backup. For a new season, one question takes your last coach and team.
- The files are in your data folder (see README_if_something_goes_wrong.md): football.sav, football2.sav and football3.sav are the three
  places, autosave.sav is the automatic save, the folder backup holds what was deleted or finished, and a franchise keeps its own set in its
  folder. Older saved games of the original game are place 1.
- You can keep three franchises (since 0.16.6). Each has its own folder: franchise (the one you had before), franchise2 and franchise3. With
  more than one, the start-up menu says each one and has "continue franchise 1, the Giants", "continue franchise 2, ..." and "delete a franchise".
  A new franchise asks where it goes: the list starts on the first empty franchise, and a full one says its team and season and is replaced
  only after one more question (the old one goes to the backup).
- Every franchise keeps its three last deleted or replaced copies in its folder old. "Restore the deleted franchise of the Giants, season 2"
  brings one back: into its own franchise when that is empty, else into the first empty one. With three franchises it tells you to delete one
  first, and the copy stays in the backup.

### The real coaches and players

With the N. F. L. rules you type no names. When you choose your team the game offers that team's real head coach (Enter keeps him, or pick
another real coach from the list of 32, or type one). The players of your team and of the other team, and the two quarterbacks, are the real
players of the two teams; Enter takes the quarterbacks. A new franchise starts with the real players and the real head coaches of all 32 teams.
The coaches are from the teams' own websites on 2026-10-22 and the rosters on 2026-10-24 (the 2026 season, week 8: every team's active roster
of up to 53 and its practice squad), and the real free agents are in free_agents.txt; they live in four files you can edit (coaches.txt,
rosters.txt, respellings.txt, free_agents.txt; CUSTOMIZE.md says how, and how a new season's names are put in). A new franchise's practice
squads are the real ones and its first season's free agents are the real ones. The Classic rules keep the original's random
surnames and the typed coach.

To bring the rosters up to today, choose **F9, Customize (or F9, Franchise), get the latest rosters**. Since 0.16.10 the game reads them
straight from the NFL: every team's own roster page and depth chart page, converted into the game's rosters in a few seconds (the lists, the
numbers, the positions, the return men, each player's age and seasons; a player the game knows keeps his checked position and depth place, new
players come in behind). Your rosters.txt and free_agents.txt are kept as copies first, a team whose pages cannot be read right then stays as it
was, and a franchise in use is asked whether its other 31 teams come up to the new rosters. The game's page on GitHub, with the maintainer's
checked file, is asked at the same time and used when the NFL's pages cannot be read.

Every player plays only his own position, as the teams' depth charts of 2026-10-24 list it: a quarterback is never a receiver, a safety
never a cornerback; a place a team has too few real players for gets a made-up player of that position. The starters play the most, as in
Madden: the first running back carries about 60 runs in 100, the first receivers are thrown to most, the starting defenders make most of the
tackles (in a franchise a better rating adds a little). F9, Rules, Depth charts has the starting lineup of any team (in a franchise, your own) and sets who starts at each of the 22 positions and who
returns kicks and punts and, under "key downs and moments", the back and the receiver who get the ball on third and fourth down, in the red zone
and in the last two minutes of a half (about 60 plays in 100 there). The Classic rules keep the original's draws.

The names are facts (names, positions, numbers), used descriptively; this project is not made, endorsed or supported by any team or by the
National Football League, and uses no ratings, photographs or logos. The names were collected from the teams' public websites, whose terms
limit how their content is copied; see spec/NFL_NAMES_RESEARCH.md for the sources and the terms.

### Trademark notice

The playbooks and the franchise mode are inspired by the playbooks and franchise ideas of Madden NFL. Madden NFL is a trademark of
Electronic Arts. This project is not made, endorsed or supported by EA or the NFL. The plays are football concepts named in plain
football words; many of them are also in the playbooks of Madden NFL. No text, play name, play list, ratings, art or sound of Madden
NFL is copied.

## The radio broadcast

With the comments on, every game is called like a radio broadcast of the Gridiron Radio Network, a made-up network. It works in both rule sets, Classic and the N. F. L. rules. Walt calls every play the way a radio announcer does, with exclamations at the big moments (see "The play calls" below), and the broadcast crew talks around the plays, between them and at the big moments, the way a real radio crew does. The style is modelled on real NFL radio broadcasts. The original game's jokes and its commentator are gone.

### The play calls

Every play is called like a live radio call, in short lively words: the snap, the throw, "Caught by Seals!", "Intercepted!", "Sacked!", "Fumble! The ball is loose!". The teams are named, never "my ball" or "your ball": "The Jets take over at their own 23.", "The Bengals are at the Jets 47.". The down is said as a radio call says it: "Third and 4! A big down here!", "First down, Bengals!", "Fourth and goal!". The gain grows with its size, from "A gain of 3." to "What a play! 34 yards!". A long touchdown run counts down, "He's at the 40! the 30! the 20! the 10! 5! 4! 3! 2! 1! Touchdown Bengals!", and a long kick return builds up the same way. Every moment has several wordings. With the game's own Windows voices the biggest calls are said a little faster; a screen reader speaks them at its own speed, with the exclamation marks.

You can go back to the original game's plain sentences: **F9, Rules, Play calls** (the twelfth item, right after How much the crew talks). Enter, Left and Right switch between "radio style, exciting" (the default) and "plain, the original's words". The change is saved and used at once, also in the game you are playing. F8 does not change the play calls: with the comments off you hear the radio calls without the crew. The setting is `nx_play_calls` in settings.txt (radio or plain). Only the words change: the plays, their results, the score and the clock are the same either way.

### The crew

- **Walt Kessler**, play-by-play, in the announcer's voice. He opens and closes the broadcast and fills the breaks.
- **Gus Delgado**, the color analyst, in a voice of his own. He explains what just happened and what to watch next.
- **Nora Banks**, the sideline reporter, in a voice of her own. She reports from the field. Her lines start with her name, or Walt names her first ("Let's go down to Nora Banks on the sideline."), so you know it is her even when a screen reader speaks the whole crew in one voice.

They are made-up people. You can give them, and the network, other names (see "Names, voices and volumes" below).

### What you hear during a game

- **Before the coin toss:** Walt signs on and names the two teams, introduces Gus and Nora, sends it down to Nora for a note from the field, and Gus gives his first thought. The first game after you start the program also has one sentence about the keys for the crew's voices and names.
- **After a play:** Gus explains it: why a run worked or was stopped, a catch or an incompletion, a sack, a turnover, a big gain, a third down made or stopped, a team going for it on fourth down, a trip inside the 20, a penalty, a punt, a kick off. Now and then Walt turns to him first ("walk us through that play"). After a touchdown, a takeaway, a big play, a sack or a missed field goal Gus often starts with an exclamation: "Wow!", "Unbelievable!".
- **Nora at the big moments:** after a touchdown, an interception or a lost fumble, or a big play of 20 yards or more; when a team goes for it on fourth down; at the two-minute warning; at the end of the first and third quarter; and always at the final whistle. She tells you what is happening on the field: the bench, the crowd, the players.
- **At the other breaks between plays:** Walt has an aside about the game, the crowd or football in general, says the network's name now and then, and says the score again when nobody has said it for a while.
- **After a score:** Gus on the touchdown or the field goal. With the N. F. L. rules Walt sometimes sums up the drive that scored (the plays, the yards and the minutes).
- **The end of the first and third quarter:** Walt's update with the score, then Gus.
- **The two-minute warning:** Walt's station break (your own commercial plays there if you have turned commercials on: CUSTOMIZE.md, "Commercials"), then Gus.
- **Half time:** Walt's update, Nora's report from the field, Gus's look at the first half, then Walt's station break (and your commercial, if any).
- **Late in each half (N. F. L. rules only):** in the last two minutes Walt says the time left after every second play.
- **A player hurt (a franchise game only):** after the game says so, Nora reports on him at the next break.
- **The end of the game:** after the final score Gus sums up the game. After the final statistics Walt signs off; his are the last words of the game.

Every game has lines of its own, so a season does not open every week with the same words, and the crew does not repeat a line in one game while it still has others for that moment.

### Turning the broadcast on and off

- **F8** switches all the comments on and off, the whole broadcast with them. The game says "comments toggle, ON!" or "comments toggle off".
- **F9, Rules, Broadcast** (the tenth item) switches Gus and Nora off and on. With them off, Walt still signs on, gives the updates and the breaks, and signs off, and his lines that name Gus or Nora are left out. Like the other rules, this applies from the next game.

### How much the crew talks

You choose how often the crew speaks: **F9, Rules, How much the crew talks**.

1. Press F9.
2. Press Down until you hear "Rules", then press Enter.
3. Press Down until you hear "How much the crew talks: a lot" (it is the eleventh item; pressing 0 jumps to Broadcast, the item just before it).
4. Press Enter to go to the next level. The levels go round: a little, some, a lot, the most. Left and Right also go down and up one level.
5. Press Escape twice to go back.

The levels:

- **a little:** the crew speaks only at the special plays and moments. This is how version 0.16.8 sounded: about 64 lines of the crew in a game, Gus after about one play in eight, Nora only before the kick-off, at half time and at a franchise injury, and no exclamations from Gus.
- **some:** Gus after about one play in three or four, about as often as on a real radio broadcast; Nora at about one big moment in three.
- **a lot** (the default): Gus after about one play in two, and Walt fills more of the breaks Gus leaves; Nora at more than half of the big moments, about ten to fifteen times a game.
- **the most:** someone of the crew after nearly every play, and Nora at nearly every big moment.

The change is saved at once and used at once, also in the game you are playing: you do not wait for the next game. F9, Rules, Reset brings back "a lot". The setting is `nx_crew_talk` in settings.txt (little, some, lots or most).

### Names, voices and volumes

- **Names:** F9, Rules, Broadcast crew (the fourteenth item) says the three names. Press Enter to open the crew: Play by play announcer, Color analyst, Sideline reporter and Network. On one of them, Enter opens a short list: the original name, the name you typed last time, and "Type a name of your own". Left and Right switch between the original name and yours without the list. You never have to type anything. New names are used from the next game.
- **Voices:** with the game's own Windows voices, F12 asks for Gus's and Nora's voices after the other speakers (while the comments and the broadcast are on). The first time, the game picks voices for them that differ from the announcer's. With NVDA or JAWS speaking for the game, the screen reader reads every line in its own one voice, so the crew all sound alike; to hear three voices, choose the game's own voices in F9, Speech settings, Speech output.
- **Volumes:** F11 sets each speaker's volume, Gus's and Nora's too while the comments and the broadcast are on.

### Your own lines

Every line of the crew is in remarks.txt in your customize folder (F9, Customize, "Open the folder with the customization files"). You can change any line, switch one off (for example `CRS01 = off`), add new lines with new numbers, and play your own sound files in a line. The lines are in groups by moment, for example SGN for Walt's sign on, CTD for Gus after a touchdown and CRG for Gus after a good run. CUSTOMIZE.md, "The radio broadcast", lists every group, when it is said and the words in angle brackets each group can use, such as `<team>` and `<quarterback>`.

### Good to know

- The first key you press cuts off the line being spoken, as with every other sentence of the game. If you choose your plays quickly you hear only the start of the crew's lines; wait a moment before the next key to hear them all.
- F2, the instant replay, repeats the play-by-play only (the radio calls as they were said), not the crew.
- F6 explains the broadcast and names these menu items.
- The broadcast never changes how a game goes. It uses its own random numbers, so the plays, the scores and the clock are the same with the crew on or off, and a Classic game is the original's game with or without it.
- Tell us what you think: is "a lot" the right amount, does a line not fit the play it follows, does one come too often? To report a problem, press F9, choose Speech settings, "Save a problem report", and send the file it saves.

## The stadium sounds and the referee

The crowd cheers, groans and boos at what happens (it roars for your big plays, cheers a flag on the other team and boos one on yours, as the flag is thrown), hits and catches sound, the first down chain clanks, a flag is thrown, the referee announces the flags, then the result after the penalty is accepted or declined (the yards and the next down), the time outs and the reviews over a microphone in a voice of their own, and the whistles are an NFL official's whistles. A game of the N. F. L. rules starts, or a saved one goes on, without the intro jingle and without the crowd surge of the original, and the program plays none of the original's music and none of its touchdown celebration sounds: put your own music.wav and celebration1.wav, celebration2.wav ... in the sounds folder and they play in those places (CUSTOMIZE.md, "Your own music and celebrations"). The sounds are generated (not recordings); you can replace any of them with your own wav, ogg, flac or mp3 file, and one file named whistle.wav replaces every whistle: F9, Sounds, Stadium and referee sounds lists the twenty-two sounds with the file name each one takes, plays them, and says whether you have replaced them; F9, Sounds, Put the stadium sounds back moves your files aside (CUSTOMIZE.md). F9, Rules, Stadium sounds and Broadcast switch them off.
