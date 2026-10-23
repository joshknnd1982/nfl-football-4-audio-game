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
offs follow week 18. The NFL publishes each year's schedule only when it is released, so from the second season the game uses the same calendar
with the teams relabeled (the divisions of each conference rotate), which gives every team other opponents and keeps every rule of the calendar.
That is an approximation, not the NFL's own rotation. A franchise that was started before this version keeps the season it is in, with the
original's 16 random weeks, and plays the real calendar from its next season. If the calendar file is missing or damaged, the game says once
that the real calendar could not be read and plays that season with the original's 16 weeks; the next season tries the file again.

**Names of new players.** The players of the real rosters keep their real names. Every player the game makes up (a free agent of the season,
a draft prospect, an undrafted rookie of the roster cut, a stand-in for an injured player) has a first and a last name. A franchise saved by an
older version gets the first names when it is opened; the players of your own team keep the names you gave them.

**Free agents and trades.** In the regular season, F9, Franchise, free agents lets you sign a free agent any week before the kick-off: choose
the position, the player and, when you have no open place there, the player of that position you release (his dead money counts against the
salary cap). Trades (F9, Franchise, trades) are open until the trade deadline, which is the kick-off of week 10 of the real calendar (the NFL's
deadline of 2026 is the day after week 9) and of week 9 of a season with the original's 16 weeks, and again in free agency of the offseason,
before the draft. The news at the start of the season says where they are, and the week before the deadline, its last week and the week after it
are told too.

### Your own words

The announcer's remarks of the added features (remarks.txt), the names of the fouls (penalties.txt), the playbooks (the folder
playbooks), the franchise's news (news.txt) and the injuries' words (injuries.txt) are in the customize folder and can be changed like
banter.txt. CUSTOMIZE.md explains every file. With the Rules setting Classic the game never makes or reads them.

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

### The real coaches and players

With the N. F. L. rules you type no names. When you choose your team the game offers that team's real head coach (Enter keeps him, or pick
another real coach from the list of 32, or type one). The players of your team and of the other team, and the two quarterbacks, are the real
players of the two teams; Enter takes the quarterbacks. A new franchise starts with the real players and the real head coaches of all 32 teams.
The names are from the teams' own websites on 2026-10-22 (the 2026 season, week 7) and live in three files you can edit (coaches.txt,
rosters.txt, respellings.txt; CUSTOMIZE.md says how, and how a new season's names are put in). The Classic rules keep the original's random
surnames and the typed coach.

The names are facts (names, positions, numbers), used descriptively; this project is not made, endorsed or supported by any team or by the
National Football League, and uses no ratings, photographs or logos. The names were collected from the teams' public websites, whose terms
limit how their content is copied; see spec/NFL_NAMES_RESEARCH.md for the sources and the terms.

### Trademark notice

The playbooks and the franchise mode are inspired by the playbooks and franchise ideas of Madden NFL. Madden NFL is a trademark of
Electronic Arts. This project is not made, endorsed or supported by EA or the NFL. The plays are football concepts named in plain
football words; many of them are also in the playbooks of Madden NFL. No text, play name, play list, ratings, art or sound of Madden
NFL is copied.

## The radio broadcast

With the N. F. L. rules the game sounds like a radio broadcast. The announcer's banter is standard sports banter (the crowd, the weather, the band, the people listening in their cars, a little teasing of the color commentator) instead of the jokes of the original game, and the color commentator (Ghip until you choose another name in F9, Rules, Commentator: a list of well-known sports podcasters and broadcasters, or a name you type; the names are used descriptively and nobody named has anything to do with this game) adds a line in a voice of their own after some plays: a touchdown, a turnover, a big gain, a sack, a missed kick, a third down, a fourth-down gamble, the red zone, a penalty, the two-minute warning, the end of a quarter, half time, a close or a decided game and the final whistle. Every line is customizable (CUSTOMIZE.md), F8 switches all comments off, and F9, Rules, Broadcast switches the commentator off. The broadcast never changes how a game goes: it draws only its own random numbers. The Classic rules keep the original's banter exactly.

## The stadium sounds and the referee

The crowd cheers, groans and boos at what happens (it roars for your big plays, cheers a flag on the other team and boos one on yours, as the flag is thrown), hits and catches sound, the first down chain clanks, a flag is thrown, the referee announces the flags, then the result after the penalty is accepted or declined (the yards and the next down), the time outs and the reviews over a microphone in a voice of their own, and the whistles are an NFL official's whistles. A game of the N. F. L. rules starts, or a saved one goes on, without the intro jingle and without the crowd surge of the original. The sounds are generated (not recordings); you can replace any of them with your own wav, ogg, flac or mp3 file, and one file named whistle.wav replaces every whistle: F9, Sounds, Stadium and referee sounds lists the twenty-two sounds with the file name each one takes, plays them, and says whether you have replaced them; F9, Sounds, Put the stadium sounds back moves your files aside (CUSTOMIZE.md). F9, Rules, Stadium sounds and Broadcast switch them off.
