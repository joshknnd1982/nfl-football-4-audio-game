"""The player's files: what the original kept in Documents\\kitchensinc, in the clone's per-user folder. This is inspired by Jim Kitchen.

One module per file (GAME_SPEC 12, D-024 item 4, D-046): `variant` (the Variant record reader and writer), `coachteam`
(footbal1.dat), `schedulefile` (footbal2.dat), `weekfile` (football.gtp), `recordsfile` (footbal3.dat), `pairingsfile`
(footbal4.dat), `byesfile` (footbal5.dat), `savedgame` (football.sav), `playernames` (footplay.txt), `speechlog`
(footballlog.txt), and `store` (`FileProgramStore`: what the program, the season engine and the set-up prompts read and
write, with the healing of playbook 7.10). Every file module holds only pure encode and decode functions over bytes or
text; `store` does the disk.
"""
