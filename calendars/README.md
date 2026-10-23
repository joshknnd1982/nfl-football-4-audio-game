# The NFL calendars of NFL Football 4

This folder holds the real NFL regular-season schedules a franchise of the game plays, one file a year: `schedule_<year>.txt`.

- The game asks this folder for the newest file only when a player chooses F9, Franchise, "get the latest calendar". It tries the years from next year down to the newest one it already has, takes the first that is here, checks that it is a whole calendar and saves it in the player's customize folder.
- A player can also download a file from here and put it in `%APPDATA%\Kitchensinc Revival\NFL Football 4\customize`, keeping its name.

## For the maintainer: publishing a new season

When the NFL releases a season's schedule (in the spring):

1. Make `schedule_<year>.txt` in the format of [schedule_2026.txt](schedule_2026.txt): the comment lines at the top, a `VERSION` line, then one line a game, `W01G01 = T08 T28 2026-09-09` (the week and the game's number, the visiting team, the home team, the date). The team IDs are those of the game's teams.txt, T01 to T32, listed in the file's top lines.
2. Check it with the game's own parser before you publish it: the tests of the game read every file of this folder (`clone/tests/test_calendars_folder.py`), so run them.
3. Commit it to this folder on the `master` branch and push. A player's game finds it the next time the player chooses the menu item.

Only the facts of the schedule are used: the week, the two teams and the date. The names of the teams are used descriptively; this project is not made, endorsed or supported by the NFL.
