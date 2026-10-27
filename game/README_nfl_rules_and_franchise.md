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

With the comments on, in both rule sets, the game is a radio broadcast of the Gridiron Radio Network (version 0.16.8; the original game's jokes are gone from every mode). The crew are made-up people: Walt Kessler calls the game, Gus Delgado is the color analyst and Nora Banks the sideline reporter, each in a voice of their own, until you choose other names in F9, Rules, Broadcast crew. Walt signs on before the kick-off and introduces the crew, Nora reports from the field and Gus gives his first thought; during the game Gus explains some plays and moments, Walt says the network's name now and then, the score when nobody has said it for a while, the quarter and half updates, the station breaks at the two-minute warning and at half time (before your commercials) and a few asides; Nora reports at half time; after the final score Gus sums up and Walt signs off. With the N. F. L. rules' real clock Walt also says the time left late in each half and sums up some scoring drives, and in a franchise game Nora reports a player who was hurt. The style follows real NFL radio broadcasts (spec/RADIO_NFL_STYLE.md). Every line is customizable (CUSTOMIZE.md), F8 switches the whole broadcast off, and F9, Rules, Broadcast switches Gus and Nora off. The broadcast never changes how a game goes: it draws only its own random numbers, so a Classic game is the original's game with it or without it.

## The stadium sounds and the referee

The crowd cheers, groans and boos at what happens (it roars for your big plays, cheers a flag on the other team and boos one on yours, as the flag is thrown), hits and catches sound, the first down chain clanks, a flag is thrown, the referee announces the flags, then the result after the penalty is accepted or declined (the yards and the next down), the time outs and the reviews over a microphone in a voice of their own, and the whistles are an NFL official's whistles. A game of the N. F. L. rules starts, or a saved one goes on, without the intro jingle and without the crowd surge of the original, and the program plays none of the original's music and none of its touchdown celebration sounds: put your own music.wav and celebration1.wav, celebration2.wav ... in the sounds folder and they play in those places (CUSTOMIZE.md, "Your own music and celebrations"). The sounds are generated (not recordings); you can replace any of them with your own wav, ogg, flac or mp3 file, and one file named whistle.wav replaces every whistle: F9, Sounds, Stadium and referee sounds lists the twenty-two sounds with the file name each one takes, plays them, and says whether you have replaced them; F9, Sounds, Put the stadium sounds back moves your files aside (CUSTOMIZE.md). F9, Rules, Stadium sounds and Broadcast switch them off.
