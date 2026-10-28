# NFL_FRANCHISE_DESIGN (nfl4 only): the design of the Franchise (NX6)

Status: DESIGN, version 1.16 (1.16: 2026-10-19, SX.8p, D-078, the whole Franchise's 20-season test: the Franchise is complete; 1.15: 2026-10-18, SX.8o, D-076; 1.14: 2026-10-18, SX.8n, D-074; 1.13: 2026-10-17, SX.8m, D-073; 1.9: 2026-10-16, SX.8i, D-069; 1.10: 2026-10-17, SX.8j, D-070; 1.11: 2026-10-17, SX.8k, D-071; 1.12: 2026-10-17, SX.8l, D-072; 1.0: 2026-10-15, session PX SX.8, D-055; 1.1: SX.8a, D-056; 1.2: 2026-10-16, SX.8b, D-057; 1.3: 2026-10-16, SX.8c, D-058; 1.4: 2026-10-16, SX.8d, D-059; 1.5: 2026-10-16, SX.8e, D-060; 1.6: 2026-10-16, SX.8f, D-061; 1.7: 2026-10-16, SX.8g, D-066; 1.8: 2026-10-16, SX.8h, D-067; as-built notes in section 20). The core is built and its 20-season simulation passes (SX.8f). nfl4 only (AGENTS.md rule 0.13): nothing in this file goes into the starter kit, `shared\`, `tools\`, a playbook or another game. It turns NX6 of `spec\NFL_EXTRA_FEATURES.md` (N6.1 to N6.11), section 11 of `spec\NFL_EXTRAS_DESIGN.md` and the research `spec\MADDEN_FRANCHISE_RESEARCH.md` (sections D, F, G, H, K) into one design that the build sessions SX.8a to SX.8f follow, in the way SX.1 designed the other six features. Design only: no code was written in SX.8. Every new spoken text is listed in section 14 as rows for `spec\strings_nx.tsv`; the build sessions add them to the table and generate `STRINGS_NX.md` and `extras\nx_texts.py` from it (D-017), nothing is typed into code.

Who reads this: the agent at SX.8a to SX.8f and at the rest of the Franchise, SX.8g to SX.8p, which the owner moved INTO the first release on 2026-10-16 (D-062: no part of the Franchise waits for a later version; read every "after the release", "update" and "later" below as "in the first release, in the session named"), and the owner. Plain headings and lists, no tables. "Design n" means a section of `NFL_EXTRAS_DESIGN.md`; "research X" a section of `MADDEN_FRANCHISE_RESEARCH.md`; "spec n" a section of `GAME_SPEC.md`.

Numbers marked "start value" are design values that a build session calibrates against the target named next to them, with the result recorded in DECISIONS.md and the history in `extras\tuning.py` (design P4). Numbers without that mark are fixed design rules (the scale, the counts, the bounds).

Plain football words only (research E): rating, potential, rookie, draft, round, pick, prospect, roster, released, retire, offseason, to-do list, news, history, champion. No EA name of a feature is used anywhere (NX-R6): not in the menus, not in the texts, not in the code's names.

## 1. Scope

### 1.1 The core, before the Windows release (D-041, N6.11)

- F0 the league that lasts and the season loop (N6.1, N6.2): sections 3, 4 and 10.
- F4 history and records (N6.9): section 9.
- F1 ratings with a bounded effect, in played games and in the computer's games (N6.3): sections 4 and 5.
- F2 progression, regression and retirement (N6.4): section 6.
- F3 the draft, the roster cut and the fill (N6.5): section 7.
- F5 the to-do list and the news (design 11.1): section 8.
- N6.10 everything spoken, short and numbered, F1 to F4 and F9 as elsewhere, long lists paged by nine: sections 3.7 and 11.

### 1.2 The rest of the Franchise, ALSO in the first release (D-041 said "after the release"; the owner changed it on 2026-10-16, D-062; section 17 says where each plugs in and what each session does)

F6 contracts, the salary cap, re-signing and free agency (N6.6); F7 trades (N6.7); F8 injuries (N6.8); F9 coordinators, the job rating and the owner's goal (N6.8); then the research's LATER items (personality words, holdouts and trade demands, morale, undrafted free agents as a market, compensatory picks, awards and a hall of fame, a camp focus, the non-exclusive tag, a weighted ball-carrier draw, the returners' rating in the kick-off return, renaming a player).

### 1.3 What stays as it is (binding)

- P1 of the design: with Rules = Classic the program is exactly the original. The Franchise is never offered, its folder is never opened or created, no extra random number is drawn, no extra word is spoken. The golden Classic transcript (`game\tests\data\golden_classic_s73b.txt`) is unchanged by every SX.8 session.
- INJURIES ONLY IN A FRANCHISE (owner rule, 2026-10-16, D-062): a quick game, a Classic season, a season played with the N. F. L. rules but no franchise, and any game that is not a game of a franchise season never draw, speak, store or show an injury; no injury switch exists outside a franchise. SX.8k tests this by comparing random-draw counts and the golden transcript.
- Classic is the default of the Rules setting (NQ2 until SX.9) and "classic season" is the first and default answer of the new question (section 3.2). A Franchise exists only when the player chooses it.
- The season inside a franchise year is the original's: 16 weeks, the schedule maker for the player's team (spec 5.1), the random pairings of the other 30 teams every week (Q42 kept, research B12: the schedule is not changed), the standings, the division winners, wild cards, seeds and the fixed bracket with their quirks (Q43, Q44, Q47 kept), the play-off and Super Bowl sentences, the waits and the celebration (spec 5.14 to 5.17, D-029). The Franchise changes only which team wins a computer game and by what score, through a bounded shift (section 5.2), and adds its own speech before the main menu and after the season.
- A Franchise always plays with the N. F. L. rules (design 11.2); the feature switches of the F9 Rules menu still apply to its games.
- Every number is data: the fixed rules of this file in `extras\franchise\data.py`, the calibrated values in `extras\tuning.py` (names `FR_...`) with their target and history.
- Ratings change the outcome tables only through the H8 door with bounds (section 5.1); neutral ratings (all 70) give exactly the original's numbers (C3).

## 2. What the design stands on (read in SX.8; file and line references for the build sessions)

- The season engine is one class over one record: `game\season_engine.py` `SeasonEngine` (pog, finplay17, the Super Bowl presentation) over `game\season.py` `SeasonState` (coach, tn1 to tn4, vtrnt, gtp, schedule, records, `PlayoffState`), writing through the `SeasonStore` protocol (`write_records`, `write_gtp`, `write_pairings`, `write_byes`) at the original's moments. No extras hook falls in it today (S7.3c, D-044).
- A computer game of a regular week (`SeasonEngine._regular_week`, spec 5.14 item 5): team A drawn, its score index `a = rnd(32)`, team B drawn, `b = rnd(32)` again while the score `T(b)` equals `T(a)`, the higher index wins, the sentence speaks `T(a)` and `T(b)`. A computer game of the play-offs (`playoffs.computer_game`, spec 5.17 item 2): the coin `rnd(2)` (1: the visitor wins, Q45), then the winner's and the loser's score indices. Team strength has no effect anywhere (research C).
- The program frame is `game\program.py` `Program`: `startup` (`store.has_saved_game`), `season_setup` (`store.load_season` else `new_season`: GetCoach, ChooseTeam, makes, gtp 1), `week_loop` (`week_announcement`, `main_menu`, `play_and_after` or the schedule or the standings), `play_and_after` (`store.player_names()` = footplay.txt, `Game.play_game(rules, own_names, saved, save_sink, roster_sink)`, then pog, the standings, `season_over` when gtp is 0), `season_over` (deletes the season files, " the season is over ", `reset_for_new_season`, `new_season`), `exit_program`. The stores are attributes: `Program.store` (ProgramStore), `Game.season_store` (SeasonStore), `Game.setup_store` (SetupStore); `data\files\store.py` `FileProgramStore` is all three over the data folder, with the healing at start (D-047).
- A game's rosters: `game\setup.py` `new_game_setup(rnd, pool, own_names)`: side 1 from footplay.txt (`adopt_roster`, which blanks the pool entries) or drawn, side 2 always drawn (33 pool draws, Q39); `Roster` has the five sections, `quarterback` and `ratings` (H7: a dict keyed (section heading, number), empty and never read in Classic). `adopt_roster` builds a NEW Roster from the names and drops `ratings` (section 13 changes that). `PlayEngine.getqbs` (`game\pag.py`) takes the two quarterbacks from a `quarterback_names` callable when one is given (a test seam today), else asks Getqbs (spec 4.12).
- The H8 door: `game\playtables.py` `Modifiers` (`run`, `pass_`, `fumble_odds(side)`, `field_goal_odds(side)`, `punt(side)`); the engine reads `rules.modifiers` at every table read (`pag_scrimmage.py` lines 106, 109, 290; `pag_kicks.py` lines 71, 120). The ball carrier `s.carrier = rnd(6)` and the two defenders `rnd(17)` are drawn in `snap_draws` BEFORE the rows are read (`pag_scrimmage.py` lines 85 to 88), so a modifier can read who carries and who tackles. With the N. F. L. rules `rules.modifiers` is `extras\playbooks.py` `PlaybookModifiers`, whose `Mod(ylo, yhi, sack, comp, fum)` is clamped to `BOUNDS = Mod(2, 2, 5, 5, 5)` (design 10.3); `qb_run(entry)` moves the quarterback runs' rows.
- The one generator: `game\rnd.py` `GameRandom` (`rnd(n)`, `below(n)`, `below_single(n)`, `random()`, the bounded `redraw`, and `trace`, which records the size of every draw so a test compares whole games).
- The names: `game\names.py` `NamePool` (1,708 surnames from `customize\surnames.txt`, drawn without replacement inside a run, refilled when used up); `game\league.py` `League` (the 32 team names and the 8 division names from `customize\teams.txt` and `divisions.txt`; `team_id(division, place)` is T01 to T32).
- The extras: `extras\state.py` `ExtrasRecord` (one JSON record saved in football.sav after the marker NX-EXTRAS), `extras\saved.py`, `extras\rules_menu.py` (the F9 Rules items, `settings.txt` keys `rules`, `nx_...`), `extras\nfl_rules.py` (`rules_from_settings`), `extras\tuning.py`, `extras\remarks.py` and `data\customlists.py` with `data\customize.py` (EXTRA_SPECS: a list file read only while the Rules are the N. F. L. rules, with the healing of CUSTOMIZABLE_CONTENT 10 and 14).
- The test rigs: `tests\seasonrig.py` (the season engine with a recording store and strict scripted draws), `tests\programrig.py` (the whole program with a stand-in pag and a `RigStore`), `tests\test_season_games.py` (whole seeded seasons), `tests\nflrig.py` (whole games with both sides played by the computer).

## 3. The mode and its flow

### 3.1 Which season is played

- A setting `nx_season_kind` (settings.txt, `classic` or `franchise`, default `classic`) says which kind of season the player is in. The FRANCHISE IS IN USE only when the Rules are the N. F. L. rules AND `nx_season_kind` is `franchise` AND the franchise file loads (section 10.1). Otherwise the classic season is in use, exactly as today.
- Each kind keeps its own files. The classic season keeps the original's season files in the data folder (footbal1.dat to footbal5.dat, football.gtp, football.sav). The franchise keeps everything in the folder `franchise` of the data folder: `league.sav` (the league and the current season, section 10.1), `league.previous.sav`, its own `football.sav` (a franchise game saved with Save Game), `history.txt`. The classic season files are never written while the franchise is in use, and the franchise folder is never written while the classic season is in use (it is only read, for the waiting franchise's team name and history in F9). So a classic season and a franchise can both be in progress, and the player moves between them without losing either.
- When the kind in use changes (the player chose it in the new-season question, started, left or resumed a franchise in the F9 Franchise menu, or changed the Rules in F9), the change applies at the next return to the week loop, never inside a game. F9 opened at the main menu's wait: when the menu closes, the main menu goes back to the week loop at once (it does not wait for a choice), so the switch is heard right away; F9 opened inside a game: the game ends as it began (its own kind, its own rules), its results go to its own season, and the switch comes when the week loop starts again. F9 opened during the offseason (a stage, the draft, the roster cut): the stage in progress goes on to its end and is written, then the offseason stops there (it resumes at the next stage when the franchise is in use again) and the switch is made. At the switch: the program's three stores (`Program.store`, `Game.season_store`, `Game.setup_store`) and the `SeasonState` are swapped for the other kind's, `Program.saved_game` is asked again of the new store (`has_saved_game`: a saved game of that kind is loaded at its next "play game", as at a start), and one sentence says so (NXF-05 " back to your franchise with the <team>. ", NXF-06 " your franchise waits. the classic season goes on. "). A change of the Rules to Classic while the franchise is in use says NXF-04 " your franchise waits until the rules are the N. F. L. rules again. " in the F9 Rules menu (after NXM-23 " the new rules apply from the next game. ").
- At the start of the program the kind in use is decided before `has_saved_game` is asked, so the saved game that is loaded is the one of the kind in use.

### 3.2 The question at a new season (N6.1, design 11.2)

- Asked at every new season of the CLASSIC kind when the Rules are the N. F. L. rules: at the first start and after a classic season has ended (`Program.new_season`). Never with Rules = Classic (P1). Never at the end of a franchise season: a franchise goes on into its offseason and its next season by itself.
- The question is a `FranchiseQuestion` (3.7), in the manner of the original's yes/no questions of `game\prompts.py` (GetCoach, Getqbs): NXF-01 " <coach> which kind of season do you wish to play " then the current answer, with the keys of 3.7. The answers, first NXF-A01 " classic season " (the default), then, when a franchise exists, NXF-A03 " your franchise with the <team> " and NXF-A04 " a new franchise ", and when none exists, NXF-A02 " franchise ". <coach> is the coach of the season that just ended, or the original's default " coach " at a first start.
- Classic season: GetCoach, ChooseTeam, makes, week 1, as today.
- A new franchise: when one exists, NXF-02 " your franchise with the <team> will be kept as a copy. do you wish to start a new franchise? " (a yes/no question whose answer starts at " no ", as the original's concede question of spec 4.18 does for a choice that ends something); no goes back to the question. Then GetCoach and ChooseTeam (the original's prompts, unchanged; ChooseTeam's write goes to the franchise store), the league is made (section 4.5), NXF-07 " your new league is ready. 32 teams and their players. ", NXF-09 " your team's rating is <r>, number <k> of 32. ", makes, week 1. `nx_season_kind` becomes `franchise`. A franchise that existed is moved to `franchise\old\league-1.sav` with its history as `history-1.txt` (an older copy 1 becomes 2, 2 becomes 3, and 3 is deleted: the three newest are kept). The game offers no way back to an old copy in the core; the README (SX.9) says how to restore one by hand (copy it over league.sav while the game is closed).
- Your franchise: `nx_season_kind` becomes `franchise` and the franchise goes on where it stood (a week of its season, or a stage of its offseason).

### 3.3 A franchise year

1. The season: weeks 1 to 16 and the play-offs, the original's flow (section 1.3), with the franchise's speech of section 3.4 before the main menu of each week and the results recorded (H14, section 13).
2. The offseason (when gtp becomes 0, in place of the classic `season_over`): NXE-01 " the season is over. the offseason begins. ", then the stages in this fixed order, each announced NXE-02 " stage <n> of <m>. <name>. " and ended with NXE-03 " press enter to go on. F1 says it again. ":
   - stage 1, NXE-11 " the season in review ": the champion, your record and finish, the best and worst records, your record as head coach (section 9); history.txt is written.
   - stage 2, NXE-12 " retirements ": everybody ages one year, then the retirements of the league (section 6.3): yours by name, the count of the whole league, then the other teams' stars by name (as built, entry 1.3).
   - stage 3, NXE-13 " player development ": progression and regression (section 6.2): your counts, your most improved and your biggest drop.
   - stage 4, NXE-14 " the draft ": the order, the seven rounds, your picks (section 7).
   - stage 5, NXE-15 " the roster cut ": the staff's cuts and your choice, the fill of empty places (section 7.6).
   - stage 6, NXE-16 " the new season ": the season number, your team's rating and rank, makes, week 1 (NXE-60, NXE-61).
   The stages are a data list (`data.STAGES`), so the later updates insert theirs (section 17). AS BUILT (SX.8l, entry 1.12): there are NINE, the staff (NXE-19, number 9) is spoken as stage 2 of 9 right after the season in review. m is the number of stages in that list (6 in the core). AS BUILT (SX.8i, entry 1.9): there are EIGHT, free agency (NXE-18) is spoken as stage 5 of 8 right after the expiring contracts. AS BUILT (SX.8h, entry 1.8): there are SEVEN, the expiring contracts (NXE-17) are spoken as stage 4 of 7, between the development and the draft; a stage's number is its ID in the file, so they are number 7 and the draft, the roster cut and the new season keep 4, 5 and 6.
3. With the setting "offseason: short" (`nx_fr_offseason = short`) every stage that needs no decision says one summary sentence and goes on without a key: stage 1 NXE-20 and NXE-21, stage 2 NXE-71 " retiring: <n> in the league, <m> from your team. ", stage 3 NXE-72 " your players: improved <n>, declined <m>. " (section 14's wording), stage 6 NXE-60; the draft and the roster cut still ask.
4. The offseason is written to league.sav at the end of every stage, and the draft after every pick, so closing the window at any wait loses at most the undecided part of the stage in progress; the next start resumes at that stage (its speech again from its start; a draft at its next pick).

### 3.4 A week of the season with the franchise in use

The original's week loop speaks the week line (spec 3 step 7) and its main menu speaks today's game (`program.main_menu`, spec 4). Inside the main menu, after today's game and before " <coach> select ", on the week's FIRST pass only (H15 `before_menu`, section 13):
1. Week 1 only: NXF-08 " this is season <n> of your franchise. ".
2. The news of the week that was just played (section 8.3): NXN-01 " this week's news. " and up to four lines; nothing when there is none.
3. The to-do list (section 8.1): its items asked one at a time, or with the setting "the staff handles the to-do list" one sentence NXD-03 " the staff took care of <n> items. ".
4. The original's " <coach> select " and the choices.
"First pass" is a flag kept in league.sav (the week and the season for which the news and the list were told), so neither the schedule or standings choice, nor F1 in the main menu, nor a restart of the program in the same week tells them again (F9 Franchise has them). A loaded saved game goes straight to its game (the original's main menu returns at once, spec 3 step 8) and `before_menu` is not called. In the play-off weeks there is no news (the original speaks every play-off result) and no item (section 8.1).

### 3.5 Leaving and returning

- The F9 Franchise menu (section 11) has, while the franchise is in use, NXF-17 " play classic seasons " (with the confirming question NXF-23): `nx_season_kind` becomes `classic`; the classic season goes on where it stood, or a classic new season starts with the original's prompts when there is none (the question of 3.2 is NOT asked: the player just chose).
- While a classic season is in use and a franchise exists, the same menu has NXF-18 " back to your franchise " (only with the N. F. L. rules).
- While a classic season is in use and NO franchise exists, the same menu has NXF-19 " start a franchise now " (with the confirming question NXF-27): at the switch (3.1) the new-franchise flow of 3.2 runs (GetCoach, ChooseTeam, the league, makes, week 1) and the classic season waits at its week. So a player who switches the Rules to the N. F. L. rules in the middle of a classic season need not finish it first.
- Leaving keeps everything: the franchise waits at its week or stage, with its saved game if any.

### 3.6 What classic seasons keep

Everything. A classic season with the N. F. L. rules is what SX.2 to SX.7 built (the extras in the games, the original's season frame); with Rules = Classic it is the original. The only addition is the question of 3.2 at a new season with the N. F. L. rules. footplay.txt belongs to the classic season: the franchise reads it once, when a new franchise is made, to give the player's team the player's own names (section 4.5), and never writes it.

### 3.7 Keys in every franchise menu and question

Two kinds, because the F9 menus and the program's own prompts read keys differently (`game\spoken_menu.py` reads them with `KeyInput.read_key`, which runs no hot key and speaks with `say_async` outside the replay list; the original's prompts read them with `getkey`, which runs the global keys):
- In the flow of the program (the new-season question, the stage waits, the to-do list, the draft, the roster cut): a new extras class `FranchiseQuestion` (`extras\franchise\question.py`), built on the pattern of `program.main_menu` and `game\prompts.py`: the question or the situation is spoken with say2 (the replay list and the speech log, as the season engine's lines), then the current item with say2 (" 1. classic season ", as the main menu speaks its choices); `getkey` reads the key, so F5 to F8, F11, F12, Ctrl and F9 work as at every wait of the original and hand F1 back (D-018); Up and Down move (they wrap) and speak the new item; the digits 1 to 9 take that item as the current one and speak it (the main menu's rule; Enter then takes it); Enter takes the current item; F1 says the question and the current item again; F2 is the original's instant replay of the replay list; Page Down and Page Up turn a page of a paged list; a letter goes to an item only where a question says so; any other key is echoed (saykey) and the question is said again from the top, the current item kept. A stage's wait (NXE-03) is a FranchiseQuestion with one item: Enter (or Escape) goes on, F1 says the stage again. A list of more than nine items is paged: nine items, then NXF-40 " more " (the digit 0 goes to it) and on later pages the existing NXB-10 " Back " to the page before; each page starts with NXF-42 " page <n> of <m>. ". The class reads no hot key itself and changes nothing of the original's prompts.
- In F9 (section 11): the existing SpokenMenu for short menus and ListPicker for long lists (the roster's players, history's lists, the team ratings), with their keys as they are today (SpokenMenu: Up, Down, Home, End, the digits where the menu turns them on, Left and Right change, Enter acts, F1 its help, Escape back; ListPicker: also Page Up and Page Down by ten and the first letter). Neither class is changed, so Classic's F9 is untouched.

## 4. The data

### 4.1 The league

One record, `extras\franchise\league.py` `League` (plain data, no reference to the game, the speech or the files, so it can be copied and written whole), with:
- the format (1) and a league ID (the date and time the league was made, `YYYYMMDD-HHMMSS`, no random draw), the season number (1 and up), the stage (`season`, or `offseason` with the stage number, or `draft` with the pick number);
- the coach's name and the player's team (T01 to T32, `League.team_id`);
- the 32 teams, each with its roster (section 4.2) of player IDs;
- the players (section 4.3), active and kept retired players, and the next free player ID;
- the current season: the `SeasonState` values (gtp, the schedule, the records, the play-off pairings and byes, tn3, tn4, vtrnt) and this season's results (section 9.1);
- the history (section 9.1);
- the to-do list and the news of the season (section 8), and per news pool the IDs spoken last;
- the draft in progress (the class, the order, the picks made; only during stage 4).

### 4.2 The roster: 34 places per team, positions of every place (N6.3, 11.3)

The original's slots, unchanged in number and order (spec 5.5, H7), each with a position:
- running backs 1 to 6: position RB (" running back ");
- receivers 1 to 6: WR (" receiver ");
- defensive players 1 to 6: DL (" defensive lineman "); 7 to 11: LB (" linebacker "); 12 to 15: CB (" cornerback "); 16 and 17: S (" safety ") (design 11.3; the original names none of them, research C);
- special teams players 1 and 2: RET (" returner ", the two kick-off returners of spec 5.10);
- kicker 1: K (" kicker ": field goals, extra points, kick-offs); kicker 2: P (" punter ": holds and punts);
- the quarterback: QB (" quarterback ").
That is 6 + 6 + 17 + 2 + 2 + 1 = 34 places, 1,088 players in the league. A place is always filled after every offseason (invariant I3). The order of the places is the original's footplay.txt order, then the quarterback; the key of a place in `Roster.ratings` is the original's section heading and the number (`("Running Backs:", 3)`, `("Defensive Players:", 14)`, `("Kickers:", 2)`, `("Quarterback:", 1)`).

A position group is the set of places with one position (RB, WR, QB, DL, LB, CB, S, RET, K, P: ten groups). A player belongs to one position for life (no position change in the core).

### 4.3 A player

- ID: a number, permanent within the league, never reused (P1 to P99999 spoken nowhere).
- Name: a surname (section 7.4 for rookies, section 4.5 at the start).
- Position: one of the ten.
- Rating: a whole number 40 to 99; 70 is average and neutral (design 11.3). Spoken " rating 74 ".
- Potential: high, average or low (three levels, design 11.3), fixed at birth. Spoken " high potential ", " average potential ", " low potential " for the player's own players and for prospects; it is the growth speed of section 6.2.
- Age: 21 to 40 (11.3). Rookies are 21 to 23.
- Seasons: the seasons played in the league (0 for a rookie).
- Peak: the highest rating the player ever had (for history).
- Drafted: season, round and pick, or none (a player of the first league, or an undrafted rookie of the fill).
- Development points of this season (section 8.2), 0 to 3.
- Status: active (on a roster), retired or released, with the season it happened.
- Contract (SX.8g, format 2): `salary` in tenths of a million dollars and `years` left, the coming season included (0 and 0 once he retired or was released); the team has dead money for the cap year (`LeagueRecord.dead`). Section 20 entry 1.7 and D-066 have the rules.
- The team (T01 to T32) and the place, while active.
Retired and released players are kept only when they matter to history: the player's own team's players, and every player whose peak was at least `data.STAR_PEAK` = 85. Others are dropped at the end of the offseason (league.sav stays small: about 1,088 active players and a few hundred kept, under 400 KB after 20 seasons).

### 4.4 Team strength

- strength(team) = the weighted mean of its 34 ratings, a whole number: weights (data) QB 12, every RB 2, every WR 2, every DL, LB, CB and S 2, K 4, P 2, every RET 1, the sum of the weights 78; strength = (sum of weight x rating + 39) // 78 (rounded half up, integers only). All ratings 70 give 70.
- Why these weights: they follow how often the engine reads each place (spec 5.9 and 5.10): the quarterback in every pass, one of six backs or receivers per play, two of 17 defenders per play, the kicker in field goals and extra points, the punter in punts; the returners have no effect in the core (section 5.1) and count a little for the computer's games only.
- The exact strength is the weighted SUM itself (a whole number, 78 x 40 to 78 x 99), so nothing is lost to rounding: the rank, the draft order's tie (7.2), the shift and the play-off lean (5.2) all use the sum; only the spoken rating is the rounded mean. While places are empty (stages 2 to 5 of the offseason) the strength is not used: every use of it falls in the season or at stage 1, where all 34 places are filled.
- The team's rank: 1 to 32 by the exact sum, highest first, ties by team order (T01 first). Spoken " your team's rating is <r>, number <k> of 32 ".

### 4.5 A new league (section 12 has the draws)

- The player's team is made FIRST, so no other team can draw the player's own names: its 33 names from footplay.txt when the classic store reads it as complete, else from footplay.previous.txt when that is complete (the classic store keeps the file under that name when a classic season ends, which is when the question of 3.2 is asked), and its quarterback from the file's last item when there is one; otherwise drawn like every other team's. Its level and ratings are drawn like every other team's.
- Then every other team in order T01 to T32 (the player's team skipped). For each team: one team level `below(9) - 4` (-4 to +4, start value `FR_TEAM_LEVEL`), then for every place in roster order: the name (unless from footplay.txt), the rating `58 + below(13) + below(13) + level` clamped to 40 to 99 (start value: 58 to 82 before the level, mean 70), the potential (`below(100)`: under 20 high, under 70 average, else low; start values `FR_POTENTIAL_SHARES`), the age `21 + below(5) + below(5) + below(4)` (21 to 32, mean about 26.5; start value `FR_START_AGE`; kickers and punters `+ below(5)` more), seasons = age - 22 (at least 0), peak = rating.
- Why a team level: 34 ratings average out, so without it every team would start within about two points of 70 and team strength would barely matter; the level gives a spread of strengths like a real league from season 1 (calibrated in SX.8b against the win spread of section 5.4).
- Names: a name is drawn from the surname pool (`customize\surnames.txt`, the player's own surname file) with `rnd(1708)`, again while an active player of the league already has it (bounded, G-D1; then the first free name in pool order, then any name: a duplicate is allowed only when the pool is used up). The league's names are drawn with the franchise's own draws, never with the game's `NamePool`, so the classic pool is not touched.

## 5. Ratings and their bounded effect (F1, N6.3, C3)

### 5.1 In a game the player plays (H8)

- The franchise gives `play_game` both rosters with their ratings (`Roster.ratings`, H7) and the two quarterbacks' names (section 13), so Getqbs asks nothing in a franchise game and no pool name is drawn.
- `FranchiseModifiers` (extras\franchise\ratings.py) is a `PlaybookModifiers` (so the playbooks still work) that adds a ratings Mod at the moment the engine reads a row. It keeps a reference to the game's state (given in `before_snap`, like the playbook arming) and reads the side with the ball (`wisoff`), the ball carrier or target (`carrier`, the slot drawn at the snap) and the two defenders (`defender1`, `defender2`):
  - a run (`run`): the offense rating is the carrier's (running back `carrier`);
  - a pass (`pass_`): the offense rating is (2 x quarterback + receiver `carrier` + 1) // 3;
  - a designed quarterback run (`qb_run`: the sneak, keeper and draw): the quarterback's rating; a scramble gets no ratings Mod (its row does not pass `qb_run`: `extras\nfl_rules.py` `qb_entry` hands a scramble's entry over unchanged, and that stays as SX.7 built it), but the quarterback's rating already moves the pass row's sack percent that leads to most scrambles;
  - the defense rating is (defender1 + defender2 + 1) // 2 of the other side's defensive players;
  - d = offense rating - defense rating;
  - the ratings Mod: ylo = yhi = step(d, `FR_YARD_STEP` 12, 1); sack = -step(d, `FR_SACK_STEP` 6, 3); comp = step(d, `FR_COMP_STEP` 6, 3); fum = step(d, `FR_FUM_STEP` 8, 3) (all start values), where step(x, per, cap) = sign(x) x min(cap, |x| // per): zero while |d| is under `per`, whole numbers only, the same size up and down.
  - The ratings Mod and the playbook Mod of the two plays called are ADDED and the sum is clamped to `BOUNDS` (2, 2, 5, 5, 5) of design 10.3, then applied as `PlaybookModifiers` applies its Mod (yards low and high together, a row never under one yard of range, the sack and catch percents in 0 to 100 with a catch at least 1, the fumble denominator at least 2). The ratings alone never move a row more than 1 yard and 3 points (design P6: small effects; the playbooks keep room).
  - `fumble_odds(side)` uses the same armed Mod's fum.
  - `field_goal_odds(side)`: `FIELD_GOAL_ODDS` + step(K - 70, `FR_KICK_STEP` 5, 5) where K is the kicking side's kicker 1 (start value; 65 to 75 against the original's 70).
  - `punt(side)`: (`PUNT_ODDS`, `PUNT_SHORTEST` + step(P - 70, `FR_PUNT_STEP` 8, 3)) with P the kicking side's punter (start value; the shortest punt 22 to 28 against the original's 25).
  - AS BUILT (SX.8o, entry 1.15): the returners move the shortest kick-off return (H8 `return_shortest`) and the ratings weight the draw of the ball carrier (H17 `draw_carrier` in `snap_draws`; equal weights are the original's rnd(6)). The core's words: Not in the core: the returners (the kick-off return has no H8 call; LATER, section 17), a weighted choice of the ball carrier (LATER: research B2 says ratings may weight the draw; it would need a hook in `snap_draws`).
- As built in SX.8b (section 20, entry 1.2): the gap d of every play also counts a team edge, `FR_TEAM_EDGE` times the two teams' strength gap (2.5 times, in rating points of the weighted mean), and the calibrated steps are finer than the start values above (the caps, 1 yard and 3 points, are unchanged). The per-play matchup of the next paragraph still decides WHICH plays the Mod moves and how much; with the edge, the teams' strength is the larger part of the gap at the spreads of a real league (an edge of 4 at one standard deviation of the league, 1.5 points), so the sentence of a better back or a worse pair of tacklers matters less than it was designed to and the team's rating more. The owner's playtest (SX.9) should listen for that.
- Why per play and not per team: the tackle sentence names the two defenders and the run sentence the back; a better back or a worse pair of tacklers should be what the player hears changing the play. The league's ratings are spread symmetrically around 70 on both sides of the ball, and the Mod is the same size up and down, so its mean effect over a league is near zero (B-P62: measured by test C-F3, not assumed).

### 5.2 In the computer's games (H14, the 5.14 score table, N6.3)

- The team's place in its league: z(team) = (sum(team) - mean of the 32 sums) / max(the standard deviation of the 32 sums, `FR_SPREAD_FLOOR`), with the sums of 4.4 taken at the start of the season (week 1, after stage 6) and kept for the whole season (start value of the floor: 78 x 1.0, one rating point of strength). Why the league and not 70: the rosters even out over the seasons (the draft's order, the cut and aging pull every team towards the middle: the review's simulation found the standard deviation of the strengths falling from 2.7 to about 1.5 within five seasons), so a shift taken from the distance to 70 would fade back to the original's coin and a league that drifted above 70 would inflate every score; the place in the league keeps the effect of being the best or the worst team, while the ratings still decide who that is. A league whose 32 sums are all equal (every rating 70 included) has z = 0 for every team.
- A regular week (spec 5.14 item 5): the shift of a team is shift(team) = sign(z) x min(`FR_SHIFT_MAX`, round_half_up(|z| x `FR_SHIFT_PER_SD`)) (start values 6 and 3: a team one standard deviation above its league moves three places up the table), computed with whole numbers from the sums (no float in a rule the tests compare: SX.8b writes it as integer arithmetic, sign-symmetric, so a team below the mean gets exactly the negative of the same distance above it). After the original's draw of team A's index `a = rnd(32)`, the index used is a' = clamp(a + shift(A), 1, 32); team B's index is b' = clamp(b + shift(B), 1, 32), and the original's redraw "again while T(b) = T(a)" tests T(b') against T(a') (its bounded scan too). The higher index wins and the sentence speaks T(a') and T(b'), as the original does with a and b. So the draws are the original's draws, the score table is the original's table, and only the place in it moves with strength.
- A play-off game without the player (spec 5.17 item 2, also the bye week's games and finplay17): the original's coin `rnd(2) = 1` (the visitor wins) becomes one draw "the visitor wins with chance p per mille", p = clamp(500 + round_half_up(`FR_PLAYOFF_PER_SD` x (z(visitor) - z(home))), 250, 750), sign-symmetric (start value 60 per mille per standard deviation; SX.8b sets it so that the lean equals the regular week's win share at the same distance, C-F2). The draw is the new `GameRandom.chance_first(p)` (section 13): ONE number from the generator, traced as a draw of size 2, and true exactly when `rnd(2)` would have given 1 when p is 500. The winner's and the loser's scores are the original's draws.
- The player's own games are played, never shifted.
- Why a shift of the index and not a new table: the original's table, its 1-in-32 entries and its sentences stay; a stronger team draws its score some places higher in the 32-place table, which is a bounded change of the same shape (N6.3 "in the same bounded way"). Because the shift is centred on the league, the league's mean shift is near zero and the computer's scores keep the original's average (the review measured 39.3 points a game at shift 0 against 45.5 when both teams had +2).

### 5.3 Neutral ratings equal Classic (C3): what the tests prove

- N1 With every rating 70 (and with the ratings dict empty) the ratings Mod is zero for every pair of slots, so every row of spec 5.9 and 5.10 read through `FranchiseModifiers` with no playbook play armed equals the original's (a table test over the 30 entries, the quarterback rows, the fumble, field goal and punt numbers).
- N2 A seeded whole game with the N. F. L. rules, the franchise's rosters all at 70 and the same names, gives the same spoken and sound transcript and the same trace of draw sizes as the same game played with those rosters handed in without the franchise (both through the `opponent_names` and `quarterback_names` seams).
- N3 A seeded whole season of the season engine with every strength 70 (and, the same, with all 32 sums equal at any value) gives the same draws, sentences, records, pairings and celebration as the classic SeasonEngine with the same seed (every shift 0; `chance_first(500)` against `rnd(2)` over 100,000 numbers of the source and on a strict script at the edges 0.4999 and 0.5).
- N4 The golden Classic transcript is unchanged, and with Rules = Classic no file of the franchise folder is opened (a test deletes the folder and the settings key and checks the golden transcript and that the folder is not made).

### 5.4 Calibration (SX.8b; the targets)

- C-F1 the win spread: over seasons 1 to 20 of the fast run (the player's games decided like the computer's; SX.8b runs it with the aging, draft and cut of SX.8c and SX.8d as stand-ins until they exist, SX.8f again with the real ones), the standard deviation of the 32 teams' wins lies in 2.6 to 3.4 in EVERY season, not only in the first (Classic gives 2.0, the coin of 16 games). Target: the NFL's spread of wins scaled to 16 games, about 3 (UNVERIFIED: SX.8b reads it from a league or statistics source and records the source; if it differs the band moves with it). Moves `FR_SHIFT_PER_SD`, `FR_SHIFT_MAX`, `FR_SPREAD_FLOOR`.
- C-F2 the same game in both kinds, ONE target: the regular week's mapping. In played games (`nflrig`, both sides by the computer, 2,000 games per point) between two rosters drawn as in 4.5 (with their levels; never uniform rosters, which leave every row unmoved until the gap passes a step, as the review's probe showed: a gap of 4 gave 0.492 with uniform rosters and 0.567 with drawn ones), the stronger team's win share at a distance of 1 and 2 standard deviations of the league lies within 5 points of the regular week's share at the same distance, measured at the league's spread of seasons 1, 5 and 10 of a fast run. The play-off lean `FR_PLAYOFF_PER_SD` is then set to the regular week's share. If the played games' effect is too small at a small spread, SX.8b raises the ratings' steps (inside the bounds of 5.1) or lowers `FR_SHIFT_PER_SD`, and records the trade-off. Why: the player's games must feel like the same league as the results he hears.
- C-F3 centering (B-P62): 2,000 played games between two rosters drawn as in 4.5 with level 0 give mean points per game and mean yards per play within 2 percent of the same games with every rating 70, once with Classic playbooks and once with the computer's styles in use on both sides (the ratings Mod is added to a playbook Mod that may already sit at a bound, so the clamp could tilt the sum: review note 1).
- Each run is a script in `work\` with a 10,000-game or 10,000-season report; the moved values go into `extras\tuning.py` with their history and into the session's decision.

## 6. Progression, regression and retirement (F2, N6.4)

### 6.1 Aging

At the start of stage 2 every active player's age goes up by one and his seasons by one. A player who reaches 40 retires (the age cap of 11.3; 6.3 retires him without a draw), so nobody is older than 40 and nobody active is older than 39 after stage 2.

### 6.2 Progression and regression (stage 3)

For every active player, in league order (T01 to T32, roster order), change = base(position, age, potential) + `below(5) - 2` (the spread, -2 to +2) + the player's development points of the season (0 to 3, section 8.2); the new rating is clamped to 40 to 99; peak is updated; the development points go back to 0.
- base by age against the group's peak window (data, start values `FR_PEAK`): RB 24 to 27, WR 25 to 29, QB 26 to 32, DL 25 to 29, LB 25 to 29, CB 25 to 28, S 25 to 29, RET 24 to 27, K 26 to 34, P 26 to 34 (research B6: a receiver declines later than a running back; the 2026-09-16 update: quarterbacks in their early thirties hold);
  - before the window: high +5, average +3, low +1 (start values `FR_GROWTH`);
  - in the window: high +1, average 0, low 0;
  - after the window, at k = age - the window's last age (k is 1 the first year after it): -min(6, 1 + k), so -2, -3, -4, -5, -6, -6 (start value `FR_DECLINE`), whatever the potential.
- The calibration of these values (C-F4, SX.8c) counts the development points as they are given (section 8.1: four extra-work weeks a season for every team, the computer's teams always using them), because the points are rating added to the league every year: the review's simulation with a point every week for every computer team lifted the league's mean rating to 74.6 by season 20. C-F4 is measured with the whole offseason loop (aging, retirement, draft, cut, fill, points) and is part of the done-when of SX.8c (with stand-ins for the draft), SX.8d and SX.8e, so a later session that adds rating to the league sees the drift at once. Besides the league's mean, the single-place groups drift by selection (the cut keeps the better of the incumbent and the rookie: the review found the quarterbacks' mean at 77 to 81, kickers and punters 74 to 78): C-F4 also bounds every group's league mean (I8b, section 16).
- Spoken (stage 3, the player's team only): NXE-40 " your players: improved <n>, declined <m>, the same <k>. ", NXE-41 " most improved: <player>, <position>, up <d> to <r>. ", NXE-42 " the biggest drop: <player>, <position>, down <d> to <r>. " (none when nobody went down), NXE-43 " your whole roster is in the franchise menu on F9. ". The news of the offseason gets NWP lines for the player's players who improved by 5 or more (at most two).

### 6.3 Retirement (stage 2)

- For every active player aged 30 or more, in league order: one draw `below(1000)` against r = clamp((age - 29) x `FR_RETIRE_PER_YEAR` - (rating - 70) x `FR_RETIRE_PER_POINT`, 0, 1000) (start values 110 and 6): retire when the draw is under r. At 40, r is 1000 without a draw. A player under 30 never retires and never draws (research G: no retirement at illogical points; invariant I1). The chance rises with age and falls with rating by construction (I2, a property test of the function).
- Spoken: NXE-30 " from your team: " then NXE-31 " <player>, <position>, age <a>, rating <r>, retires. seasons played: <n>. " for each, or NXE-32 " nobody from your team retires. "; NXE-33 " players retiring in the whole league: <n>. "; the league's stars who retire (peak 85 or more, at most three, the highest peak first): NXE-35 " <player> of the <team>, <position>, retires. seasons played: <n>. ". The NWR news lines tell the stars again in the season's news.
- A released player (section 7.6) is not a retired player: he leaves the league at any age and is never counted as a retirement.

## 7. The draft, the roster cut and the fill (F3, N6.5)

### 7.1 The draft class (made at the start of stage 4)

- `FR_CLASS_SIZE` = 260 prospects (start value; 224 picks plus a choice at the last picks). For each prospect in order: the position by `below(35)` over the weights RB 6, WR 6, QB 2, DL 6, LB 5, CB 4, S 2, RET 2, K 1, P 1 (data: the roster's shares with one more quarterback, because a team has only one); the name (section 7.4); the true rating `46 + below(15) + below(15)` (46 to 74, mean 60; start value `FR_ROOKIE_RATING`); the potential (`below(100)` against `FR_ROOKIE_POTENTIAL_SHARES`, start: under 25 high, under 75 average, else low); the age `21 + below(3)`; the scouting offset `below(7)`, which places the true rating inside the spoken range: low end = true - offset, high end = low end + 6 (" about 62 to 68 "; research B12's range, without a scouting level in the core).
- The class is kept in league.sav for the stage; prospects not drafted are dropped after the fill (no undrafted market in the core). AS BUILT (SX.8m, entry 1.13): the prospects nobody drafted are a market for places in camp right after the last pick, and the class has one more prospect for each compensatory pick of the draft.

### 7.2 The order (N6.5, research F2)

- Teams that missed the play-offs pick 1 to 20, then the play-off teams by the round they lost: wild card losers 21 to 24, division round losers 25 to 28, conference championship losers 29 and 30, the Super Bowl loser 31, the champion 32 (NFL draft rules, SRC-OFFICIAL in research F2). Inside a group: fewer wins first; equal wins: the lower exact strength first (the sum of 4.4 as it was at stage 1, before the retirements, kept in the season's history; a weaker roster picks earlier; the NFL uses the strength of schedule, which the original's random pairings do not give); then the team order T01 first. No draw.
- The same order in all seven rounds (no compensatory picks; AS BUILT, SX.8m: the compensatory picks awarded a year before sit at the end of rounds 3 to 7, entry 1.13). AS BUILT (SX.8j, entry 1.10): a pick of the coming draft may change hands in a trade of the season; the draft names the owner of each pick (`owners`).
- Spoken at the start of the stage: NXK-01 " the draft has 7 rounds. you have pick number <n> in every round. ".

