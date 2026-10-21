# NFL_PLAYS_DESIGN (nfl4 only): the menus, the catalog and the outcome models of every real NFL play and every Madden NFL concept

Status: DESIGN, version 1.1 (2026-10-20, PX session SX.10b; decisions D-090 and D-091). nfl4 only (CLAUDE.md rules 0.13 and 0.20 as amended (c); requirements NX-P1 to NX-P7 and NX-R7 in `spec\NFL_EXTRA_FEATURES.md` section 18; decisions D-082 to D-089; research `spec\NFL_PLAYS_RESEARCH.md` 1.0). Built in SX.10b, as pure modules NOT yet connected to the engine: the catalog, the outcome models, the menus, the favourites file, their text rows and 365 tests (section 9: 292 catalog, 50 model, 18 menu, 5 favourites). SX.10c, SX.10d and SX.10e connect them (section 10). Classic is untouched: no file of the classic engine changed in SX.10b and the golden Classic transcript passes.

How to read it: section 0 is every decision in one line; sections 2 to 4 say how the menus, the catalog and the models work and why; section 6 says how each place where the N. F. L. mode does not yet follow the 2026 rules (G26-1 to G26-14) closes; section 7 is the engine work SX.10c to SX.10e must do. Every fact keeps the research's tag (SRC-OFFICIAL, SRC-SECONDARY, UNVERIFIED); COMPUTED means computed in SX.10b from public data (section 5). Madden NFL is a trademark of Electronic Arts; nothing of EA's text, play names, lists, art or ratings is used, only football concepts in plain words.

## 0. The decisions (D-090; each question of the research section 10, with its reason)

- Q-P1 (NX-P7) The menus: the original's items stay first with their digits and Enter on a play family calls the playbook's pick of that family for the down and distance; Right opens the family's lists and walks them; More Plays (M), Favourites (F), Again (A), Formation and Tempo (O), and Kneel (K) and Spike (P) only when they help; a typed search under More Plays (N). Measured: the usual call one or two keys (Enter alone for the first item, as in the original), every one of the 176 offense and 98 defense plays at most six keys, mean 4.8 and 4.3 (section 2.3). Reason: the original's two keys stay, Right is the one new key and the original's play menus never used it, the letters avoid T, S and C.
- Q-P2 Concept first; the formation is the concept's own, changed in Formation and Tempo. Reason: one step fewer; the measured effect of the formation is small (sacks 0.85 to 1.09 times, runs within 0.2 yards, section 4.4).
- Q-P3 Personnel and formations in plain words ("one back, two tight ends", "shotgun"); the rare words go into F7 (SX.10c writes the rows).
- Q-P4 A new outcome layer for every catalog play in the N. F. L. rules mode (`extras\plays\model.py`); Classic, and the playbook choice "Classic" in the N. F. L. mode, keep the original's tables; SX.7's bounded changes of the original's table are replaced for catalog plays. Reason: a 30-cell table cannot reach the league's numbers for 282 plays; the new layer reaches them within the tolerances of section 4.11.
- Q-P5 The two-point try offers the original's items 1 to 5 (the playbook's pick of that family) and More Plays with the goal-line list first (it holds the swinging gate); the old formations are a list of rare named plays; the drop kick, the quick kick and the sky kick are left out (catalog LEFT_OUT, with reasons).
- Q-P6 Motion is a remembered setting (the playbook's, none, jet, orbit, a shift); the concept's own motion by default; effect half the measured difference (selection is in it): completion plus 1.5 points, interceptions 0.9 times, sacks 0.93 times.
- Q-P7 Every concept has its own inputs and shares one of twelve models; runs are four gap shapes times four box shapes from the data, a shift from the published concept numbers and the call's run tags; passes are a mix of the thirteen charted routes, each with its measured depth, completion, interceptions, yards after the catch, man and zone split and out-of-bounds share.
- Q-P8 A read (option, run-pass option) is a draw keyed to the defense's call: a crashing call (run blitz, slant, eight in the box) is kept, a call that stays home (contain, quarterback contain, spy, scrape) is handed off, else even; one read in ten is wrong. A run-pass option throws half the time against a box of seven or more or a run blitz and 8 times in 100 against a light box: 26 percent in all (data 25). The player never decides at the line, so the pace stays.
- Q-P9 Play action is its routes plus the measured fake by depth (completion points per band), interceptions 0.78 times, sacks 0.88 times, one more yard after the catch; half the fake on third or fourth and 7 or more (UNVERIFIED: the defense does not bite).
- Q-P10 Trick plays are their own list, marked rare (the computer seldom calls them, SX.10e: about 0.4 percent of drop-backs as in the charting); a lateral before the throw is fumbled 2 times in 100 (half lost); a thrower who is not the quarterback throws 1.2 times the interceptions; the fake leaves a receiver open (plus 6 points). The fourth-down and two-minute fumble rule (RB26 8-7-5, 8-7-6) applies to their laterals (SX.10c).
- Q-P11 Tempo is a setting (normal, no huddle, hurry up) the clock's tempo reads (SX.10c); Kneel and Spike appear at the top only when they help (section 2.7).
- Q-P12 The disputed words are said with numbers: "dime, six defensive backs", "quarter, seven defensive backs", "big nickel, three safeties"; dollar and okie are merged into dime and the odd front; Palms and Cover Nine are kept as names (F7 explains them).
- Q-P13 The defense's personnel follows the offense's by default (nickel against three receivers, base against two backs or two tight ends, dime against four or five receivers, heavy at the goal line), with an override in Formation and Tempo; the computer matches the same way.
- Q-P14 One combined call (front, defensive backs, box, coverage, rushers, tags), grouped by the original's six defensive families and More Plays.
- Q-P15 OWNER ANSWER (2026-10-20, asked once with a recommended answer, taken): download the public data; done (section 5).
- Q-P16 Kicks: Enter on Punt is the original's punt, Right opens the punt kinds and the fakes; Enter on Field Goal is the kick, Right opens the fakes; the kick-off menu puts the deep kick first so Enter keeps the pace (it replaces SX.2b's onside question in SX.10d); the receiving team's call is a remembered call set from the defense menu's item P on fourth down or More Plays, never a new question at each kick.
- Q-P17 The kneel ends the down (one yard lost, data); when the computer kneels the player's defense menu is not asked, one sentence says it.
- Q-P18 The fair catch kick is a yes or no question (starting at no) only after a fair catch in the last seconds of a half in range; its odds are the field goal's at the distance plus 3 points (no rush, UNVERIFIED).
- Q-P19 The Franchise: the styles' weights over the whole catalog are set in SX.10e and the 20-season test runs again (NX-P5).
- Q-P20 Fouls by the call (start values, SX.10e measures the fouls a game): press man illegal contact and defensive holding 1.3 times; six or more rushers roughing the passer 1.2 times; a run-pass option's throw ineligible downfield (a new row at its 2026 rate); the kicks the 2026 kick fouls (SX.10d).
- Q-032 is answered by these decisions; the owner's listening round confirms the menus (PLAYTEST_LIST).
- OWNER RULES at the end of SX.10b (D-091, version 1.1 of this design): every key in three places, the special keys (F5), the help (F6) and the GitHub README (NX-H1, for every game CLAUDE.md 0.24); and a short plain description of every play for people who know nothing of football (NX-P8; for every sports game CLAUDE.md 0.25), heard with the letter D in any play menu (the function keys are all taken: F8 is the original's comments switch), in F7 for the original's items in Classic, and in a plays guide for GitHub. Session SX.10b2 builds both, before SX.10c.

## 1. What SX.10b built and what it did not

Built (pure modules, read by nothing in the engine yet):
- `clone\src\nfl4\extras\plays\catalog.py`: 282 plays (167 offense, 92 defense calls, 23 special-teams plays), 35 lists, the merged names, what is left out and why, the settings.
- `extras\plays\model_data.py`: every number the models use, with its source and seasons.
- `extras\plays\model.py`: the outcome models and the named start values.
- `extras\plays\play_menus.py`: the menus, the kick-off menu, favourites, the search.
- `extras\plays\favourites.py`: the player's `customize\playbooks\favourites.txt` read, healed (the list format and healing of playbook 7.9) and written whole; the game reads it from SX.10c.
- `spec\strings_nx.tsv`: 302 new rows (the play names, the lists, the menu words, the settings and their values) and the regenerated `extras\nx_texts.py` and `spec\STRINGS_NX.md`.
- Tests `clone\tests\test_sx10b_catalog.py`, `test_sx10b_model.py`, `test_sx10b_menus.py`, `test_sx10b_favourites.py`; `test_sx9_about.py` checks the reworded notice.
- The README and About notice reworded (D-088 item 4): "The plays are football concepts named in plain football words; many of them are also in the playbooks of Madden NFL. No text, play name, play list, ratings, art or sound of Madden NFL is copied."
- Work files (not committed): `work\sx10b\fetch_data.py`, `analyze_data.py` and its output `data_numbers_sx10b.txt`, `probe_model.py` and `probe_sx10b.txt`, `key_counts.py`.

Not built (sections 7 and 10): the engine's use of any of it, the narration of the new plays, the computer's calling over the catalog, the kicks of 2026 in the game, the F5 and F7 rows of the new keys and words, the player's files for the new plays, the conformance rows NX-P1 to NX-P7 and NX-R7.

## 2. The menus (NX-P4, NX-P7)

### 2.1 The measure

The research's measure (Q-P1): keys from the prompt to the call. The original: Enter on the first item, or a digit and Enter. The design keeps exactly that for the usual call and adds one key (Right) to reach a play by name in a family, or the letter M for the other lists. `tests\test_sx10b_menus.py` searches every key sequence of up to six keys from the top (Up, Down, digits, letters, Enter, Right, Left as the engine's loop treats them) and requires: the first family by Enter alone, every other family and Field Goal and Punt in two keys, every listed play in at most six, every play of a family's first list in at most four, every kind of punt and field goal in four, every kick-defense call in four on fourth down.

Measured with `work\sx10b\key_counts.py`: offense 176 plays outside a try (2 keys: 1, 3: 17, 4: 62, 5: 39, 6: 57; mean 4.76; the swinging gate is offered only on a try); defense 98 calls (2: 1, 3: 11, 4: 47, 5: 34, 6: 5; mean 4.32); defense on fourth down mean 4.19. The playbook's pick (Enter on a family) is one or two keys.

### 2.2 The top level

Offense, in this order: 1 Line Plunge, 2 End Run, 3 Screen Pass, 4 Short Pass, 5 Long Pass (Enter: the playbook's pick of the family for the down, distance, field and score, said before the snap; SX.10e builds the pick), 6 Field Goal, 7 Punt (Enter: the original's kick), 8 Quarterback Sneak, 9 Quarterback Keeper, 0 Quarterback Draw (when quarterback runs are on, as SX.5), then F Favourites (only when there are any), A Again with the last play's name, M More Plays, K Kneel Down and P Spike the Ball (only when they help), O Formation and Tempo; NflRules then adds C Challenge the Ruling (only while allowed), Time Out (no letter: T calls it anywhere) and S Save Game, as today.

Defense: 1 Goal Line, 2 Short Run, 3 Long Run, 4 Blitz, 5 Short Pass, 6 Long Pass (Enter: the playbook's pick of that family), F, A, M, P Kick Defense (fourth down only), O, then the same tail.

With the playbook "Classic" in the N. F. L. mode the top level is today's (the original's items and the quarterback runs, no letters but C and S). Classic mode is unchanged.

### 2.3 The lists and the Right key

A list is at most ten plays, so a digit reaches each (the tenth is 0), then Back (B). Right on a family's item opens its first list; Right in a list opens the family's next list and wraps; Left or Backspace (or Back) goes up one level. When a list opens the game says its name and its place: " Inside Runs, list 1 of 2. " (NXB-61). The lists of the families:
- Line Plunge: Inside Runs; Power and Gap Runs.
- End Run: Outside Runs; Misdirection Runs.
- Screen Pass: Screens.
- Short Pass: Quick Passes; Crossers and Backs; Intermediate Passes.
- Long Pass: Deep Passes; Deep Combinations.
- The quarterback items 8, 9 and 0: Quarterback Runs.
- Field Goal: Field Goals and Tries (its fakes); Punt: Punts (the kinds and the fakes).
- Defense, Goal Line: Goal Line Defenses; Short Run: Run Fronts, Run Stunts; Long Run: Edge and Contain; Blitz: Blitzes, Pressure Looks; Short Pass: Zone Coverages, Man Coverages; Long Pass: Two Deep Coverages, Deep Help.

### 2.4 More Plays

Offense: 1 Play Action, 2 Moving Pocket, 3 Quarterback Runs, 4 Option Runs, 5 Run Pass Options, 6 Trick Plays, 7 Goal Line and Short Yardage, 8 Clock Plays, 9 Old Formations, 0 More Routes, N Find a Play by Name, B Back. Defense: 1 Situation Defenses, 2 Kick Defense, N, B.

### 2.5 Favourites, again, the search and the settings

- In any list the plus key adds the current play to the favourites (at most ten, NXB-58, NXB-60) and the minus key takes it off (NXB-59); Favourites (F) lists them. Kept per side in the player's file `customize\playbooks\favourites.txt` (lines like `OF01 = O027`, healed like every list of 7.9; the module `extras\plays\favourites.py` is built, SX.10c reads it and adds it to the Customize item's files).
- Again (A) calls the last play the player called on that side, said with its name.
- Find a Play by Name (N): a typed box (the only place in a game where t is a letter, rule 0.22): the first letters of any word of a play's name, then Enter; the plays found are a list (at most ten); " no play has that name. " otherwise.
- Formation and Tempo (O): offense Formation, Personnel, Motion, Side, Tempo, Protection; defense Defensive Personnel and Coverage Shade. Enter changes the value (Up and Down move); the values are kept for the game (the extras' state, saved with it) and their spoken words are NXB-70 on.

### 2.6 The try, the kick-offs and the kick defense

- The try: items 1 to 5 as the original's try menu; M opens More Plays with Goal Line and Short Yardage (fade, rub routes, jumbo power, tight end flat, and the sneak, power, slants, snag, mesh and the swinging gate listed again). The choice to kick or go for two stays the question it is.
- The kick-off (SX.10d, replaces SX.2b's onside question; the onside kick is declared, RB26 6-1-6): 1 Deep Kick, 2 Short Kick, 3 Squib Kick, 4 Onside Kick; after a safety also 5 Safety Punt (RB26 11-5-2). Enter takes the deep kick.
- The kick defense: Punt Return (the original's), Fair Catch, Punt Block, Punt Safe, Field Goal Block, Field Goal Safe; one remembered call for the game, set from P on fourth down or More Plays. Kick-off returns and the hands team against a declared onside kick are automatic.

### 2.7 Kneel and spike

Kneel (K) appears when the offense leads in the fourth quarter and the clock can run out with kneels (the time left is at most the downs left times 40 seconds plus the defense's timeouts' worth) or at the end of a half; Spike (P) appears when the clock is running in the last two minutes of a half (SX.10c writes the exact tests). The kneel loses a yard and runs the clock; the spike is an incomplete pass that stops it (RB26 7-2-1(c), 8-2-1 Item 3).

### 2.8 Keys, T and the help

- T is never an item's letter (tests); S and C stay NflRules'; D is reserved for the description of the current item (D-091); the letters F, A, M, K, P, O, N and B are unique in each level (tests).
- Every key in three places (NX-H1, CLAUDE.md 0.24, D-091): SX.10b2 makes the master key list `game\key_list.py` with every key that exists then, and generates from it the added lines of F5 (the special keys) and F6 (the help) in every mode and the draft `clone\README_keys.md` for the GitHub README; SX.10c adds the play menus' keys to the list (Right, Left, Backspace, plus, minus, F, A, M, K, P, O, N, B, D) the same session it wires them; F7 gets the new football words (personnel, formations, coverages, fronts, the reads).
- The description of the current item (NX-P8, D-091): D in any play menu of the N. F. L. mode says the item's description (a play's, a family item's, a list's, a setting's) and the menu stays on the item; it is heard once per press, in the menu's voice, and not written to the game's speech log.

## 3. The catalog (NX-P2)

- IDs: O001 to O167, D001 to D092, K001 to K036 (with gaps between the kinds). O001 to O052 and D001 to D030 are SX.7's plays with the same names and text rows (tests). Text rows: NXY-nn and NXY-Ann (offense past 99), NXZ-nn, NXB-Knn; the lists NXB-11 to NXB-45.
- Each play: its list, its model (`kind`) and inputs, its formation, personnel and motion, a stated strength and weakness (tags of the defense's call for an offense play, kinds of plays for a defense call), its tag and its situations (goal line, two-point, clock, late, rare, fourth down).
- Every name the research's sections 2 to 6 gives is a play, MERGED into a named play (for example Texas into Angle Route, slip screen into Running Back Screen, dollar into Dime Short Coverage) or LEFT_OUT with its reason (the fumblerooski, the drop kick, the quick kick, the sky kick, a surprise onside kick, a fair catch of a kick-off, follow and hank, the audible, the hot route, the kick-off return choices, the punt return direction); a test checks the list of 230 research names.
- No EA name (MADDEN_PLAYBOOK_RESEARCH List B and NFL_PLAYS_RESEARCH 6.4); "Roll Coverage" is on that list, so the concept is "Safety Rotation".
- The pre-snap tools of Madden's playbooks are settings, not plays: formation, personnel, motion, the side (flip), tempo, protection, the defense's personnel and press or off.
- Descriptions (NX-P8, D-091, written in SX.10b2): every play, every original item, every list and every setting has one or two plain sentences, at most 35 words, saying what it tries to do and when it works or is risky, for a person who has never watched football (the play's stated strength and weakness, section 4.8, in everyday words: "good when the defense sends extra players after the quarterback, risky when ..."). They are rows of `spec\strings_nx.tsv`: the description rows follow a fixed scheme so a test can find each (offense O001 to O099 NXY-R01 to NXY-R99 and O100 on NXY-S00 on; defense D001 on NXZ-R01 on; kicks K001 to K036 NXB-D01 to NXB-D36; the original's items, the lists and the settings NXB-E and NXB-F rows; SX.10b2 writes the exact rows). A football word (from a glossary in the test) used in a description is explained in it or in F7. `clone\PLAYS_GUIDE.md` (for GitHub) is generated from the rows, list by list.

## 4. The outcome models (NX-P3)

### 4.1 Where they sit

`model.play(concept, call, situation, rnd)` gives a result (run, complete, incomplete, sack, interception, fumble, kneel, spike; the yards; the route, depth and air yards; out of bounds; a lost fumble; a return and a return touchdown; a read's branch). `rnd` is the game's one generator (`below(n)`), so the draws are the game's and a scripted source reaches every branch. Pure: no speech, no state.

### 4.2 A pass

1. Sack: the rushers and the shell (data: 3 rushers 5.1 and 5.3 percent of drop-backs one-high and two-high, 4 rushers 6.0 and 6.2, 5 rushers 7.2 and 8.2, 6 or more 8.4 and 11.0) times the concept's time to throw (quick game 60 percent, deep 120 to 135), a screen 3 percent, a run-pass option 22 percent, play action 88, the formation (under center 88, shotgun 103, pistol 85, empty 109), motion 93, max protect 70, the call's tags (twist and wide 108, drop 90). Yards from the 2,601 sacks of the data (0 to minus 20, mean minus 6.5); 11.4 percent of sacks fumble, half lost, 12.8 percent of those returned for a touchdown.
2. A legal throw-away (RB26 8-2-1 Item 1): 3.4 percent of drop-backs against four rushers, more against more (3.6 in the data).
3. The target: one of the concept's routes by its weight; its depth band (behind the line, 0 to 4, 5 to 9, 10 to 14, 15 to 19, 20 to 29, 30 or more air yards) from the route's measured shares times the coverage's measured depth (quarterbacks throw deeper against man), no band beyond the back of the end zone.
4. Completion: the coverage's measured rate in that band (cells shrunk to the league's band by 60 attempts) plus the route's own difference, its man or zone split, the blitz against the coverage's usual blitz share, the call's tags (press, off, robber, bracket, deep help, drop, match, Tampa, roll), the concept's own points, play action by band, a read's throw (plus 5), a trick's fake (plus 6), motion (plus 1.5), the matchup (plus or minus 3 points a strong or weak tag met, at most two each way), and inside the 10 minus 9 points and 1.2 more per yard closer. Interceptions: the coverage's rate in the band, times the route's, the blitz, prevent, the tags, play action (0.78), a trick (1.2).
5. The yards: the air yards in the band's range plus the yards after the catch from the band's measured shape times the route's measured share, plus one with play action; capped at the goal line; out of bounds by the route's share (quick out 37 percent, slant 3); 1.0 percent of catches fumble, 48 percent of those lost.

### 4.3 A run

The gap's measured bins (loss, no gain, 1 to 3, 4 to 6, 7 to 9, 10 to 19, 20 or more; middle, guard, tackle, end; outside the 10) times the box's measured shape over the league's (5 or fewer, 6, 7, 8 or more), times the call's run tags (run blitz: more losses and more long runs; slant; pinch; spill; two gap; wide; on end runs contain and spill), then the shift: the concept's own (PFF's concept numbers: power plus 0.4, duo minus 0.1, draw plus 0.5, dive minus 0.2 and so on), the matchup (0.4 yards a tag), the formation (shotgun plus 0.1, pistol plus 0.2, under center minus 0.1). The shift moves mass between the stuffed bins and the 4 to 19 bins so the mean moves by exactly the shift (a test). Within 5 yards of the goal line the bins take the shape of the runs inside the 5 (1.05 yards a carry, data). Losses and the 20 or more bin from their measured shapes. 0.9 percent fumble, 57.5 percent of those lost; out of bounds by the gap (end 19.9 percent).

### 4.4 Play action, motion and the formation

Section 4.2's numbers; the data's play-action effect by box is the same with 7 or more in the box and 6 or fewer (8.07 and 8.13 yards an attempt), so the fake does not depend on the call; motion and the formation are kept at half their measured differences because selection is in them.

### 4.5 The quarterback and the reads

Designed quarterback runs: the 963 runs' bins (4.87 a carry; loss mean minus 2.83, so a loss is one yard deeper half the time; the 20 or more bin 20 to 40), 3.0 percent fumbles, 43 percent of those lost; a spy or a quarterback contain minus 0.4 yards. Sneaks: the 527 sneaks' bins (81.8 percent of 1-to-go converted). The reads of section 0 Q-P8; a pitch is fumbled 2 times in 100 (60 percent lost, UNVERIFIED); a give is the run of its gap, a keep the designed run plus 0.2, a pitch an end run plus 0.2.

### 4.6 Tricks, the Hail Mary, the laterals and the clock

Trick runs: the 236 charted trick runs' bins (5.46 a carry), 1.7 percent fumbled and lost. Trick passes: section 0 Q-P10. The Hail Mary: 8.3 percent touchdowns (half from beyond the 40), 25.9 percent intercepted, 1.4 percent caught short (ESPN, FiveThirtyEight). The last play's laterals: 3 percent touchdowns, 25 percent lost (no published rate, UNVERIFIED). The kneel: minus 1 yard. The spike: an incompletion.

### 4.7 What a call is

A defense call is its front, defensive backs, box (5 to 8), coverage (the eight FTN coverages or prevent), rushers (2 to 6), whether a blitzer comes, and its tags. The model reads: eight or more in the box, six or fewer (light), five or more rushers (blitz), six or more (max blitz), three or fewer (drop), one-high or two-high, man or zone, and the tags.

### 4.8 No best play

Every play has a stated strength and a weakness; a test requires every offense play to meet a catalog call it is weak against and one it is strong against, and every call to meet a play that beats it (the SX.7 rule, design 10.3, carried over).

### 4.9 The kicks of 2026

- Kick-off (RB26 6-1, 6-2): out of bounds 0.8 percent (ball at the 40); a squib lands short of the landing zone 15 percent of the time (ball at the 40, UNVERIFIED rate); touchback to the 35 on 28 percent of deep kicks and none of the short ones (with 55 deep and 45 short: 15.6 percent, 2026's); returns from the catch (deep: from 5 yards deep in the end zone to the receiving 9; short: the 8 to the 19; squib: the 3 to the 14) by the 2025 return shapes, short kicks' returns 70 percent and squibs' 60 percent (UNVERIFIED); 0.2 percent returned for a touchdown. The mix gives a start at the 30.3 (data about the 30).
- Punts: the spread punt's distance drawn to the percentiles of 2024 to 2026 (10th 36, median 47, 90th 59); 0.5 percent blocked; into the end zone a touchback unless the coverage downs it short (25 percent, pin punts 60); landing inside the 20 or not decides the shares of returns, fair catches, downed, out of bounds and dead balls; returns from the measured shape; muffs lost 0.9 percent of punts, return touchdowns 0.6; kinds: tight (fewer blocks, longer returns), rugby (fewer blocks, shorter), pin (lands near the 10); the receiving call changes blocks, returns and fakes.
- Field goals: made by distance, linear between the measured bands (97.7 percent at 18 to 29 yards to 44.4 at 60 to 70), falling 7 points a yard past 66; blocked by band (0.2 to 6.7 percent; a block call doubles it, a safe call halves it); a blocked kick is the defense's 70 percent of the time, 5 percent of those returned for a touchdown (UNVERIFIED); any distance may be tried (G26-6).
- The extra point: 95.2 percent good, 0.9 blocked (2,943 tries); a blocked try returned for two 3 percent of the time (UNVERIFIED).
- Fakes: 50 percent converted (32 fake punts), plus 15 points at 2 yards or less, minus 20 at 6 to 9, minus 35 farther; a safe call 0.6 times, a block call 1.3 times (UNVERIFIED shapes).

### 4.10 The start values (UNVERIFIED, each in `model.py` with its name)

MATCHUP_PASS_COMP 300 and MATCHUP_RUN_SHIFT 40 (wrong if a styled game's balance in SX.10e is off by more than SX.7's band); RED_ZONE_COMP 900 and 120 (checked: 54 percent inside the 10, data 52.7); GOAL_LINE_YARDS 5 (checked: two-point runs 54 percent); COVERAGE_DEPTH_SHRINK 300; PLAY_ACTION_LATE_DOWN 50; RPO_THROW_HEAVY and LIGHT 5000 and 800 and RPO_COMP 500 (checked: 26 percent thrown, bubbles 84 percent); OPTION_MISREAD 1000; PITCH_FUMBLE; LATERAL_FUMBLE; TRICK_INT 120 and TRICK_COMP 600 (checked against the 122 charted trick passes within their sampling error); HAIL_MARY; LATERALS; SACK_SCALE 100 (SX.10e sets it so the engine's sacks after its scrambles and throw-aways are 6.5 percent); CALL_PASS_TAGS and CALL_RUN_TAGS; the kick values marked so in 4.9. A value moves only with a measurement recorded in DECISIONS.

### 4.11 The calibration (`work\sx10b\probe_sx10b.txt`, 30,000 plays a line; the tests use 5,000 to 15,000)

- League passing with the charted route mix against the league's calls: completion 64.7 (data 65.1, test 2.0), interceptions 2.11 (2.2, 0.6), yards an attempt 6.94 (7.11, 0.45), sacks 6.4 of drop-backs (6.5, 1.0), throw-aways 3.6 (3.6, 0.8).
- Each of the thirteen routes: completion within 3 points of its charted rate when targeted, interceptions within 1.6.
- Each coverage with the league's routes: Cover 0 56.6 (54.6), Cover 1 61.5 (58.6), Cover 2 68.1 (71.1), two-man 63.1 (60.9), Cover 3 67.1 (69.3), Cover 4 66.7 (68.5), Cover 6 65.7 (66.9), Cover 9 63.8 (64.4); test 5 points and man below zone. The rest of the gap is the routes quarterbacks choose against each coverage, which a called concept does not change (a modeling choice).
- Runs outside the 10: middle 4.15 (4.30), guard 4.32 (4.43), tackle 4.62 (4.70), end 5.17 (5.15); test 0.3 yards and 3 points of stuffed runs; the box from 5 to 8 lowers a guard run from 5.25 to 3.78 (data all gaps 5.58 to 4.20; test the difference within 0.4).
- Quarterback keeper 5.05 (4.87, test 0.45); sneak 1 to go 85 percent against light boxes and about 82 against a neutral call (81.8, test 4).
- Play action against the same routes: plus 0.5 to 2.2 yards an attempt (data plus 1.3), fewer sacks and interceptions.
- Screens 86 percent (86.0), almost never sacked; run-pass options thrown 26 percent (25), bubble throws 84 (84.1), the runs 4.6 (4.57).
- Inside the 10: completion 54 (52.7, test 4). Two-point tries from the 2 against goal-line defenses: runs about 54 (54.1, test 10), passes about 38 (42.2, test 12).
- Kicks: field goals within 1.8 points of the curve and 4 of the band; the extra point 95.3 (95.2); the kick-off mix touchback 15.1 (15.6), start the 30.7; punts' shares within 2 points of the data (returned 37.3 against 36.4), gross 46.7 (47.2).
- Turnovers: interception touchdowns 7.4 (7.4), sacks fumbled 11.4 (11.4).

## 5. The data (Q-P15)

The owner's yes (2026-10-20). Downloaded with `work\sx10b\fetch_data.py` into the session's scratch folder outside the project, read with the standard library only, deleted at the end of the session: nflverse play-by-play 2024 (19,362,351 bytes, SHA-256 23370d5d...08c06), 2025 (19,105,296 bytes, 2f135887...78961978), 2026 to week 6 (6,436,955 bytes, 14d0b7ed...e38a98); FTN charting 2024 (8,254,908 bytes), 2025 (8,128,926), 2026 (2,724,781); FTN participation 2024 (49,688,308) and 2025 (49,094,943); 163 MB in all; the full hashes are in `work\sx10b\MANIFEST.tsv`. Terms: the FTN files are CC-BY-SA 4.0 with the credit "FTN Data via nflverse" (SRC-OFFICIAL for the terms: nflreadr's reference pages, read 2026-10-20). Only computed numbers enter the game, with the credit in `model_data.CREDIT`; they are facts about plays. Claude is not a lawyer.

## 6. The 2026 gaps (NX-R7)

- G26-1 Kick-off: model `kickoff` and menu `kickoff_items` built; SX.10d connects them (the setup and landing zones' rules are in the model's spots).
- G26-2 Closed in SX.2b.
- G26-3 Overtime: SX.12.
- G26-4 The extra point that can miss: `extra_point` built; SX.10d.
- G26-5 Punts returned, blocked, fair-caught, muffed: `punt` built; SX.10d.
- G26-6 Field goals by the published odds from any distance: `field_goal_rate` built; SX.10d (the original's own-half refusal stays in Classic).
- G26-7 A missed field goal at the spot of the kick or the 20: a rule for SX.10d.
- G26-8 Turnovers returned and scored: `interception_return` and `fumble` built; SX.10c replaces the turnover spot in the N. F. L. mode.
- G26-9 Fumbles the offense recovers: `fumble`'s lost share; SX.10c (and the 8-7-5 rule).
- G26-10 The computer's two-point tries and the defense's two points: SX.10e researches and tags a published two-point chart and calibrates it to about 10 percent of touchdowns (Fox 2024: 9.8); SX.10c scores a returned try.
- G26-11 The safety kick: `kickoff_items(safety=True)` with the punt; SX.10d.
- G26-12 Kneel and spike: in the catalog, the models and the menus; SX.10c.
- G26-13 The fair catch kick: `field_goal(..., fair_catch_kick=True)`; SX.10d asks the question.
- G26-14 The fouls of the new kicks and plays: SX.10d and SX.10e (Q-P20).

## 7. The engine work (SX.10c to SX.10e)

- A new hook in the scrimmage step (after the snap sentence): when the N. F. L. rules have a catalog play called, the play's result comes from `model.play` and the engine narrates it with the original's sentence pools (the run sentence of the original entry whose yard range holds the result, the throw and catch phrases, the sack, incompletion and interception sentences), so the pace and the sounds stay (NX-P7); short new sentences for the new results (a throw-away, a kneel, a spike, a pitch, a keep, a lateral, a return) as text rows.
- The H3 hooks: `offense_menu` and `defense_menu` give `PlayMenus.items()`; one new hook for the Right key in `pag._menu` (Classic: none, the key stays the original's); `menu_action` passes Enter; the plus and minus keys in a list.
- The clock reads the model's out-of-bounds flag (design 5.2's late-window rule); the tempo setting is its tempo.
- SX.5's scramble and SX.3's grounding stay where they are (in place of the model's sack or incompletion); SACK_SCALE is set so the engine's sacks are 6.5 percent of drop-backs and scrambles 5.4.
- The Franchise's ratings door (H8): the ratings' Mod becomes a shift of the run, completion points, the sack and fumble rates within the same bounds; injuries (H16) unchanged.
- The replay review (SX.6) reads the result's kind and spot; a review of a catch, a fumble or a touchdown works on the model's result.
- The computer's calling: each style's weights over the catalog; the situation factors from the data's pass rates by down and distance (1st 49.8 percent drop-backs, 3rd and 7 or more 92.2 and so on); the defense's coverage, blitz, rusher and box shares from the data, matched to the offense's personnel; trick plays rare; the playbook's pick for Enter on a family uses the same weights.
- The new player's default playbook becomes the team's (D-083: "all plays" is the default; Classic stays a choice).
- The player's files: plays.txt grows to the new IDs and the K plays (names and off switches), favourites.txt; their healing.
- The bands of SX.2 to SX.9 and the 20-season Franchise test run again (NX-P5); the conformance map gets rows NX-P1 to NX-P7 and NX-R7.

## 8. The computer's mixes to reach (SX.10e)

Drop-backs over plays by down and distance (data 2024 to 2025): 1st 49.8; 2nd and 1 to 3 36.2, 4 to 7 55.7, 8 or more 74.9; 3rd and 1 to 2 38.7, 3 to 6 87.2, 7 or more 92.2; 4th 66.3. Play action 22.9 percent of drop-backs, screens 8.4, run-pass options 4.7 percent of plays, motion 51.6, no huddle 11.0. Defense: Cover 1 29.5, Cover 3 22.7, Cover 2 21.8, Cover 4 8.0, two-man 6.1, Cover 6 4.4, Cover 0 4.0, Cover 9 2.1; a blitzer on 29.1 percent of drop-backs; four rushers 69.1 percent, five 19.9, six or more 6.6; boxes on runs 5 or fewer 4.0, 6 52.5, 7 34.7, 8 or more 8.7; defensive backs 4: 26.3, 5: 62.6, 6: 9.4. Kneels 1.54 a game, spikes 0.29.

## 9. The tests

Built: `test_sx10b_catalog.py` (IDs, names, text rows, lists, models' inputs, calls, research names, EA names, situations; 297 with the About tests), `test_sx10b_model.py` (section 4.11's checks, the scripted branches, the purity of the models, every play against every kind of call), `test_sx10b_menus.py` (the original's items, the keys, T, the lists, More Plays, favourites, again, the search, the try, the settings, every text), `test_sx10b_favourites.py` (made when missing, written and read back, bad lines left out and counted, a damaged file copied aside and made again, ten a side). To build: SX.10c the engine path (golden Classic, scripted games with each family, the narration, the hooks' no-op in Classic, the mutation check), SX.10d the kicks in the game, SX.10e 10,000 games against every band.

## 10. The sessions

- SX.10b2 (BUILT 2026-10-20, D-092) The play descriptions and every key in three places (D-091; NX-P8, NX-H1): the descriptions of section 3, the D key in today's play menus and in `play_menus.py`, F7's descriptions of the original's items in Classic, `game\key_list.py`, F5's and F6's added lines, `clone\README_keys.md` and `clone\PLAYS_GUIDE.md`, the tests. Sonnet 5.5 at high. Before SX.10c.
- SX.10c The offense in the game: the hook, the narration, the menus with Right, plus and minus, favourites and settings saved, kneel and spike, turnovers returned (G26-8, G26-9, G26-12), the ratings door, plays.txt and favourites.txt, F5 and F7 rows. Sonnet 5.5 at high (Opus 5.5 if the narration of the reads needs new engine steps).
- SX.10d The defense calls and special teams in the game: the defense menus, the 2026 kick-off menu and model, punts, field goals, the extra point, the fair catch kick, the safety kick, the kick defense, the kick fouls (G26-1, G26-4 to G26-7, G26-11, G26-13, G26-14). Sonnet 5.5 at high.
- SX.10e The computer's calling over the catalog, the playbook's pick, the two-point chart (G26-10), SACK_SCALE, the bands of SX.2 to SX.9, 10,000 games, the 20-season Franchise test, the conformance rows, the owner's listening list. Opus 5.5 at high (calibration).

## 11. History

- 1.0 (2026-10-20, PX SX.10b, D-090): written with the build of the pure modules and their tests; the owner answered Q-P15 (download the data).
- 1.1 (2026-10-20, end of PX SX.10b, D-091): the owner's two rules: every key in the special keys, the help and the GitHub README (for every game, CLAUDE.md 0.24) and a plain description of every play (first nfl4's, then widened by the owner to every sports game, CLAUDE.md 0.25); the D key reserved in `play_menus.py`; session SX.10b2 added before SX.10c.
- 1.2 (2026-10-20, PX SX.10b2, D-092): the descriptions are written and built as rows with the final id scheme (358 rows), the D key works in the live menus and in `play_menus.py` (`PlayMenus.describe`), the master key list, the generated F5, F6, README draft and plays guide, the tests.
