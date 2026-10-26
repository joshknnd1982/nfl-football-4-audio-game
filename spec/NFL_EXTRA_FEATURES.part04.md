# NFL_EXTRA_FEATURES (part 4 of the split file; section 21 continued)

### 21.5 SR.2 done (2026-10-25; D-157, D-158; the record is spec\NFL_ROSTERS_LIVE_RESEARCH.md section 9)

- BUILT: `game\tools\update_rosters.py` (NX-L8): the 32 teams' own roster and depth chart pages read gently (D-156; `--no-official` switches that reader off), nflverse's roster and newest depth chart snapshot, Sleeper's feed; the checks of D-155 in `game\src\nfl4\extras\roster_file.py` (the same module the game's "get the latest rosters" will use, NX-L9, SR.6); `roster_settlements.txt` for the differences a search settled; the game-day elevations sent back to the squad; a report of every difference and every change since the last file; `--write` replaces the shipped files only when every check passes; tests on saved excerpts, no network (test_update_rosters_sr2.py, test_roster_file_sr2.py).
- SHIPPED (NX-L1, NX-L2): rosters.txt of 2026-10-25, layout 2 (the 22 positions of D-152, the lists, numbers, depth order, KR and PR), 1,686 active men, 531 on the squads, 304 on reserve lists; free_agents.txt of 2026-10-25 (159 men). Every listed difference between the sources settled (by kind, by a search, or in a settlement); six teams hand-checked equal to their live pages.
- The loader reads layout 2 and still hands the engine the original's groups (D-157 item 4); the real roster model is SR.3 and SR.4. Q-076 answered; Q-077 stays for SR.3.

Status after SR.2: NX-L1, NX-L2 (the data), NX-L8 BUILT. (SR.3 below.)

### 21.6 SR.3 done (2026-10-25; D-159; the design is spec\NFL_FRANCHISE_DESIGN.part05.md section 21)

- DESIGNED (no code changed): a team is its roster and depth chart on the 22 positions (the returner a role, the bench gone, the real lists kept); the engine's 34 places are a view made for each game (empty back places with no share, a short defense place filled by the nearest family's spare man, a cover for the original's uniform draws, the squad's kicker as an elevation, no draw added or removed); a new franchise is exactly the file with today's draws given to the view's men; league.sav format 18 (number, list, chart, roster_version, roster_offer; the 34 IDs made in memory); the conversion of format 17 and older; every Franchise block by family (cut to 53, draft of all 22 positions, signings, trades, injuries, must-haves, strength, cap, squads); the speech by positions; namesakes; the in-game update with the once-offered sync of the other 31 teams (the player's team never touched).
- Q-077 ANSWERED (two sources: EA's saved pages and the file agree on the family of all 28 front-seven men EA lists). New accepted defaults Q-078 to Q-081; none needs the owner.

Status 2026-10-25: NX-L1, NX-L2 (the data), NX-L8 BUILT; NX-L3 to NX-L7, NX-L9 DESIGNED (SR.3), NOT BUILT; NX-L10 REQUIRED. Next: SR.4.

### 21.7 Owner requirement of 2026-10-25 (b): the player chooses who starts, from the current rosters (NX-L11, D-160)

The owner, during SR.3: "Claude must add the ability for the user to choose who starts from the current rosters." REQUIRED for nfl4 (rule 0.13), and the global rule 0.30 (3) is amended to say the same for every sports game (CLAUDE.md, playbook 7.21, fixesforgames A112). What 0.15.0 has (NX-D3, D-147) is not enough: F9, Rules, Depth charts orders the original's GROUPS (running backs, wide receivers, tight ends, defensive linemen, linebackers, cornerbacks, safeties, kickers, punters, returners), so a player cannot choose the starting left tackle, center, guards, long snapper, which edge men, tackles and backers start, or the free and strong safety, and the list is the original's groups, not the real roster of today.

- **NX-L11 Choose who starts, from the current rosters.** With the N. F. L. rules, in a quick game, a season and a franchise:
  1. For every one of the 22 positions (D-152) and the kick and punt returner roles, the player hears who starts and chooses the starter (or the starters: three wide receivers, two defensive tackles, two cornerbacks, one of every other position) from EVERY man of the team's CURRENT active roster at that position: the newest rosters.txt the game has (the shipped one, the player's own, or the one "get the latest rosters" downloaded, NX-L9) in a quick game or a season, the league's roster in a franchise. Each man is said with his position, number, place on the chart and, in a franchise, rating and age. A man of the same family may be moved to the other side or role (left or right tackle, guard or edge, MIKE or WILL, free or strong safety, halfback or fullback); never to another family (a backup quarterback never starts at receiver, rule 0.30 (1)). Any active man may be a returner (the role).
  2. A "starting lineup" item says the whole lineup in one list (offense, defense, the kickers, the snapper, the returners: one man a line, his position first) and Enter on any line opens that position's choice, so the player reaches any starter in two keys.
  3. Practice squad men are listed after the active men of the position; choosing one is a game-day elevation (a quick game or a season: at most two a game, the NFL's rule; a franchise: the elevation rules of D-136, or a promotion when they are used up), said in one sentence.
  4. Which teams: in a quick game and a season any team (the player's and the opponent's, the real order the default); in a franchise the player's own team (the staff orders the other 31, NX-D3). The staff setting (nx_fr_auto) may keep choosing for him in a franchise.
  5. The choice is kept: settings (nx_depth, by team, position and name) for quick games and seasons, the league's chart (format 18) in a franchise; it holds through trades, signings, injuries (NX-B1 asks for a replacement and the chosen starter comes back when fit), the cut and a roster update (a chosen man no longer on the team is dropped, and one sentence says who starts now). "The real order" puts a position, or the whole team, back.
  6. The chosen starters are the view's first men (design 21.4): they get the starter's usage share (NX-D2) and are the default key-down men (NX-D4).
  7. Keys in F5, F6 and the README (0.24), a plain description of each item (0.25), CHANGELOG.md with "How to test" (0.29), the log line `starter_chosen` (0.15), no doubled sentence and nothing promised that is not shown (0.28). Classic keeps the original exactly.
- Done when: a test chooses a starter at each of the 22 positions and both roles for one team in a quick game and in a franchise, the view puts him first, 20,000 draws give him the starter's share, the choice survives a save, a trade and a roster update (a gone man dropped with its sentence), a squad man chosen is an elevation within the limits, and the owner hears the lineup item (PLAYTEST_LIST).
- Sessions: the data (the chart order, nx_depth on the 22 positions and the roles, an older nx_depth by group read through the conversion table of design 21.6 (2)) in SR.4; the menus, the lineup item, speech and keys in SR.6; checked in SR.7.

Status 2026-10-25: NX-L1, NX-L2 (the data), NX-L8 BUILT; NX-L3 to NX-L7, NX-L9 DESIGNED (SR.3); NX-L11 REQUIRED, designed (design 21.13), NOT BUILT; NX-L10 REQUIRED. Next: SR.4.

### 21.8 SR.4 done (2026-10-25; D-161; design 21.14)

- BUILT: the roster model (`extras\roster_model.py`: the chart on the 22 positions and the return roles, the view of the engine's 34 places, the conversion table, the starter's swap); quick games and seasons play the view of the file's chart (empty back places with no share, the 3-4 covers, the squad kicker elevated, a returner may also play elsewhere); league.sav format 18 (position, number, list, status "list", the charts, the rosters' version); a new franchise is exactly rosters.txt (every man, his position, number and list, nobody made up, nobody left off, the same draws); a league of format 17 or older is converted when it is opened (positions by name, the missing real men of a league without benches, the backup file); the data of choosing who starts at all 22 positions and both roles (a franchise: the league's chart; a quick game or a season: nx_depth by position and role, the older group entries read through the table).
- THE BRIDGE (D-161): the Franchise's blocks (the cut, the draft, the fill, signings, trades, injuries, aging) still store and read the 34 places and the bench; the charts follow them at every save. SR.5 moves every block onto the chart (NX-L6) and drops the stored places.
- Tests: tests\test_real_roster_sr4.py (14); 21 older pins moved, each with its reason (format 18, the view's covers, the returner on top of a place, the real roster for the player's own team; the bench tests run on the older shape of the names).

Status 2026-10-25: NX-L1, NX-L2, NX-L8 BUILT; NX-L3, NX-L4, NX-L7 BUILT (SR.4, with the bridge); NX-L5 IN PART (the quick game and a new franchise; the blocks in SR.5); NX-L11 DATA BUILT (menus SR.6); NX-L6, NX-L9 DESIGNED, NOT BUILT; NX-L10 REQUIRED. Next: SR.5.

### 21.9 Owner requirement of 2026-10-25 (c): real NFL surnames for made-up players (NX-L12, D-163)

The owner, answering Q-016: "claude must research the last names of real nfl players and use those."
- **NX-L12 Real surnames.** With the N. F. L. rules every made-up player (later draft classes, the undrafted, stand-ins, squad top-ups, a quick game's last-resort name) takes the last name of a real NFL player: researched (rule 0.19, facts only, sources and date recorded) from the game's real rosters and a larger public table of NFL players (nflverse's players table, CC BY 4.0), a first name from the game's own first-name list, never a full name a real man of the league has (no made-up man is taken for a real one). A customizable file with the healing and refresh path of the other name files; `update_rosters.py` refreshes it. Classic keeps Jim Kitchen's 1,708 surnames (its golden transcript). Done when: a test makes 20 seasons of draft classes in the N. F. L. rules and finds every made-up surname in the researched list and no full name equal to a real player's; Classic's draws and names unchanged.
- Session: SR.5 (the draft classes and the undrafted are made again there).

### 21.10 SR.5 done (2026-10-25; D-164; design 21.15)

- BUILT (NX-L6, NX-L5 in full, NX-L12): the chart is the team in every block of the Franchise. league.sav format 19 stores the charts and no places (the
  34 places are the view made in memory after every change); the bench status of D-149 is gone; one join and one leave for every block (signings, the
  market, the tag's sheet, trades of any position for any position within the family minimums, practice promotions, re-signing, retirements, the cut);
  the cut keeps 53 by the family minimums and the keep value, the fill makes only a family's missing minimum, the reserve lists come back at the cut; the
  draft of the 22 positions by the league's mix with needs by family (the real league's mean rounded down, or a starter under 60) and the NFL's jersey
  ranges; the market and the signings by the 53's room and the families' needs; injuries by the chart; `is_starter` by the chart; the cap of a real 53
  (FR_CAP_ROSTER 510, measured); the squads of any position. NX-L12: nfl_surnames.txt (9,504 real NFL last names, nflverse CC BY 4.0 and the rosters),
  customizable, refreshed by update_rosters.py; no made-up man has a real player's full name; a quick game's last-resort name is a real surname.
- Tests: tests\test_real_roster_sr5.py (22) and the older franchise tests moved to the new model, each pin with an "SR.5" comment (see D-164).
- NOT YET (SR.6): the speech of the roster by positions, the lineup item and the menus of NX-L11, the trade menus' other positions, the conversion's
  sentence, the in-game update (NX-L9), a returner on top of his place in a franchise game (Q-082).

Status 2026-10-25: NX-L1 to NX-L8, NX-L10's tests of the model, NX-L12 BUILT; NX-L11 DATA BUILT (menus SR.6); NX-L9 DESIGNED, NOT BUILT; nothing heard
(SR.7). Next: SR.6.
