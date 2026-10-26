# The real rosters of NFL Football 4

This folder holds the newest real rosters the maintainer has checked: `rosters.txt` (the 32 teams' active rosters, practice squads, reserve lists and kick and punt returners, at the real positions) and `free_agents.txt` (the real free agents). Both carry a `VERSION` line, for example `season 2026, as of 2026-10-25`.

- The game asks this folder for them only when a player chooses F9, Customize, "get the latest rosters" (or the same item in F9, Franchise). It compares the `VERSION` lines, checks the new file (every team, every position, the practice squads), keeps the player's earlier files beside it as `rosters.txt.before-<date>` and `free_agents.txt.before-<date>`, and says in one sentence what it did. A franchise in progress is offered the newer rosters once and can say no.
- A player can also download the two files from here and put them in `%APPDATA%\Kitchensinc Revival\NFL Football 4\customize`, keeping their names.
- The names are facts (names, teams, positions, numbers), used descriptively; no ratings are included. The README of the repository has the notice about trademarks and sources.

## For the maintainer: publishing new rosters

1. Run `game/tools/update_rosters.py` (it reads the teams' official pages gently, compares nflverse and Sleeper, checks the result and writes the files with a report; it never replaces a good file with a failed pull).
2. Copy `game/assets/data/rosters.txt` and `free_agents.txt` here (the same files), commit and push. Players get them the next time they choose "get the latest rosters".
