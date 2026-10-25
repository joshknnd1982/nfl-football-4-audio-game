# NFL_EXTRA_FEATURES (part 4 of the split file; section 21 continued)

### 21.5 SR.2 done (2026-10-25; D-157, D-158; the record is spec\NFL_ROSTERS_LIVE_RESEARCH.md section 9)

- BUILT: `game\tools\update_rosters.py` (NX-L8): the 32 teams' own roster and depth chart pages read gently (D-156; `--no-official` switches that reader off), nflverse's roster and newest depth chart snapshot, Sleeper's feed; the checks of D-155 in `game\src\nfl4\extras\roster_file.py` (the same module the game's "get the latest rosters" will use, NX-L9, SR.6); `roster_settlements.txt` for the differences a search settled; the game-day elevations sent back to the squad; a report of every difference and every change since the last file; `--write` replaces the shipped files only when every check passes; tests on saved excerpts, no network (test_update_rosters_sr2.py, test_roster_file_sr2.py).
- SHIPPED (NX-L1, NX-L2): rosters.txt of 2026-10-25, layout 2 (the 22 positions of D-152, the lists, numbers, depth order, KR and PR), 1,686 active men, 531 on the squads, 304 on reserve lists; free_agents.txt of 2026-10-25 (159 men). Every listed difference between the sources settled (by kind, by a search, or in a settlement); six teams hand-checked equal to their live pages.
- The loader reads layout 2 and still hands the engine the original's groups (D-157 item 4); the real roster model is SR.3 and SR.4. Q-076 answered; Q-077 stays for SR.3.

Status 2026-10-25: NX-L1, NX-L2 (the data), NX-L8 BUILT; NX-L3 to NX-L7, NX-L9, NX-L10 REQUIRED, NOT BUILT. Next: SR.3.
