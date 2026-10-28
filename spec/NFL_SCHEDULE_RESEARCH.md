# NFL schedule research (nfl4 only, SZ.8, D-121)

Why: a player's e-mail (2026-10-22) said the Franchise did not play the 2026 schedule. The Franchise now plays the league's real calendar (`clone/assets/data/schedule_2026.txt`, `extras/franchise/fixtures.py`).

## The data (evidence tags as GAME_SPEC 5.3)

- SRC-SECONDARY: the 272 games of the 2026 regular season were read on 2026-10-22 from the public nflverse games table (`https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv`, by Lee Sharpe; rows with season 2026 and game type REG). Only four facts of each row are kept: the week, the visiting team, the home team and the date. No score, odds, rest days or other field is used. The repository states no license (the API answers "not found" for it); the facts are the NFL's published schedule, used descriptively like the names of the teams and players; the README says so. The agent is not a lawyer.
- SRC-OFFICIAL, checked by search on 2026-10-22: the NFL's release story ("2026 NFL schedule release: complete slate of Week 1 games", nfl.com) and team listings say the season opens on Wednesday 2026-09-09 with the Patriots at the Seahawks (week 1, the first line of the file) and that the Patriots' last game is at home against Miami on 2027-01-10, week 18 (the file has `W18G13 = T06 T08 2027-01-10`).
- Whole check of the file (run by `fixtures.check`, pinned by `tests/test_fr_calendar.py`): 18 weeks of 16, 16, 16, 16, 15, 14, 14, 14, 15, 14, 13, 16, 14, 15, 16, 16, 16, 16 games = 272; every team 17 games, 8 or 9 at home, one bye in weeks 5 to 14; every division rival once at home and once away. The Commanders' bye is week 7, the Bengals' week 6.
- The team IDs are the game's (T01 to T32 in the order of `teams.txt`); the table's codes map CIN CLE BAL PIT BUF MIA NYJ NE DEN LAC KC LV IND JAX HOU TEN CHI DET GB MIN DAL PHI NYG WAS ARI SF LA SEA TB ATL CAR NO onto T01 to T32.

## Refresh

A new season is a new file: `assets/data/schedule_<year>.txt` in the same format (`# NFL Football 4 schedule, format 1.`, a `VERSION` line, `W<week>G<n> = T<visitor> T<home> <date>`), 18 weeks. The Franchise plays the file of its year (season 1 is 2026); a year with no file plays the 2026 calendar with the divisions of each conference rotated (an approximation: Q-060 asks whether to build the NFL's real rotation instead). The sentence about the deadline reads the calendar: the NFL's 2026 trade deadline is the Tuesday after week 9 (2026-11-10, research F2 of SX.8j), so trades are open up to the kick-off of week 10.

## Not covered

The day of the week and the time of a game are in the source table and are not used. The play-offs stay the original's 12 teams (Q-061).
