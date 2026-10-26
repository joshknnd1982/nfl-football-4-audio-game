## 21. The real roster (phase PR, session SR.3, 2026-10-25; D-159; NX-L3 to NX-L7, NX-L9; nfl4 only, rule 0.13)

Written in SR.3 for SR.4 to SR.7. It stands on rosters.txt layout 2 (SR.2, D-157), the 22 positions of D-152, the mapping of D-153 (settled here: 21.2), the
bench of NX-B2b (D-149, replaced here) and the inventory of every module that reads the 34 places (21.9, from a read-only sweep of `extras\franchise\`
in this session). Classic is not touched by anything below: the original's places, groups, names and draws stay with their golden transcript. Every
number below that is measured says so and names its script in `work\sr3\`; every choice is DECIDED (D-159) unless it is tagged otherwise.

### 21.1 The facts this design is built on (measured 2026-10-25, `work\sr3\view_counts.py` over the shipped rosters.txt)

- Active men by position (1,686): QB 86, HB 105, FB 13, WR 174, TE 119, LT 61, LG 62, C 62, RG 54, RT 54, LEDG 77, REDG 75, DT 172, SAM 22, MIKE 66,
  WILL 63, CB 180, FS 75, SS 71, K 31, P 32, LS 32. SRC-OFFICIAL (the teams' pages, SR.2).
- Against the engine's 34 places at full health (no injury), each team filling a place only from men of its own family (backs HB+FB, receivers WR+TE,
  line LEDG+REDG+DT, backers SAM+MIKE+WILL, corners CB, safeties FS+SS): 74 back places are short over the league (teams carry 2 to 6 backs; the
  Eagles and the Buccaneers 2), 14 linebacker places (13 teams carry 3 or 4 backers: the 3-4 fronts, whose outside backers are edge men), 1 corner
  place (the Commanders carry 3 corners) and 1 kicker (the Dolphins have none active: their practice squad kicker is elevated every game day). Every
  team has at least 2 spare men of its line (the line holds 8 to 13) and at least 1 spare safety or corner where it needs one. Receivers, line,
  safeties, quarterback and punter are never short.
- The usage shares of NX-D2 (`extras\tuning.py`): the six back places run 60, 25, 10, 5, 0, 0 percent; the fifth and sixth back places never carry
  the ball now. The tackles of the 17 defense places: line 6, 6, 5, 5, 2, 1; backers 13, 11, 7, 2, 1; corners 9, 8, 4, 1; safeties 10, 9.
- Every place name the engine says is reached in one of two ways (a grep of `game\pag*.py` and `extras\` in this session): through a usage draw
  (`draw_carrier`, `usage.defenders`: the carrier and the two tacklers of a scrimmage play), or through a plain draw of the original that is still
  uniform: `rnd(6)` over the receivers ("downed by", `pag_kicks.py` 144, `pag_kicks26.py` 84 and 210), `rnd(17)` over the defense (the kick return's
  tacklers `pag_kicks.py` 273 and 279, the blocked kicks of `pag_kicks26.py` 183, 226, 295, 359), `rnd(2)` over the returners. The back places are
  named only through the usage draw, and in the R key's list of targets (`choices.py`).
- Six names belong to two real men (SR.2): Brandon Johnson (Steelers WR on the squad, Buccaneers CB on the squad), Byron Young (Eagles DT, Rams
  LEDG), DeVonta Smith (Eagles WR, Panthers CB on the squad), Jaylon Jones (Jaguars CB, Titans CB), Justin Jefferson (Browns SAM, Vikings WR),
  Marcus Harris (Chiefs DT on the squad, Titans CB). No team has two men of one name.

### 21.2 Q-077 settled: the 3-4 calls (two sources)

- Source 1, EA's own Madden NFL 27 pages saved raw in SR.1 (`work\pr\raw\ea_ratings.html`, `ea_pos_wr.html`; no new request to EA, whose robots.txt
  reserves text and data mining; `work\sr3\ea_positions_3_4.py`, report `work\sr3\ea_positions_report.txt`): 187 players with a position, 28 of them
  of the front seven. EA lists the 3-4 ends as DT (Cameron Heyward, Leonard Williams, Quinnen Williams, Dexter Lawrence II), the rushing outside backers
  of 3-4 teams as edge men (T.J. Watt LEDG, Nik Bonitto REDG, Micah Parsons REDG) and the 3-4 inside backers as MIKE or WILL (Roquan Smith MIKE, Zack
  Baun WILL). SRC-OFFICIAL (structure only).
- Source 2, the file of SR.2 (the teams' pages for the group, nflverse's charts for the side and the role): all 28 are in it (name forms Cam and
  Cameron, Jr and Jr. allowed) and all 28 are in the same FAMILY as EA has them (edge, tackle, backer); 24 have the same code; 4 differ only by the
  side or by the inside backer's role: Nick Bosa and Brian Burns (EA left, ours right and the reverse), Zack Baun and Demario Davis (MIKE and WILL
  swapped).
- ANSWER: D-153's group calls stand as SRC-OFFICIAL (a 3-4 end is a DT, a rushing 3-4 outside backer is an edge man, a 3-4 inside backer is a MIKE or
  a WILL). The side (LEDG or REDG, LT or RT, LG or RG) and which inside backer is MIKE or WILL are not facts the sources agree on: the game treats them
  as slots of one family (21.3) that the staff and the player may change; the file keeps nflverse's call (the team's chart where nflverse has none);
  tagged SRC-SECONDARY. Nothing in the engine's play depends on the side.

### 21.3 The model: a team is its roster and its depth chart

- THE MAN (league.sav format 18, 21.6): every player of the league has his POSITION, one of the 22 (D-152), for good: a drafted, signed or made man
  too. The returner is not a position. A man changes position only when the player or the staff moves him inside his family on the depth chart (a
  left tackle to right tackle, a MIKE to WILL, a free safety to strong safety, an edge man from left to right): the family never changes, so a tight
  end is never a wide receiver and a quarterback is never anything else.
- THE FAMILIES (for the view and the tables, never spoken as a position): QB; backs HB, FB; receivers WR, TE; offensive line LT, LG, C, RG, RT;
  defensive line LEDG, REDG, DT; backers SAM, MIKE, WILL; corners CB; safeties FS, SS; K; P; LS.
- THE LISTS a man of a team is on: the active roster (at most 53; `data.ROSTER_MAX`), the practice squad (16 plus one International Pathway man,
  `roster_file.SQUAD_MAX` 17), or a reserve list (IR, IRD, PUP, NFI, SUS, PSI, EXM, RTD, LFT, MIL, PSX: `roster_file.RESERVE`; not on the 53, never in a
  game). Off a team: free, released, retired. The old status "reserve" (the bench of D-149) is GONE: a bench man of format 17 is an active man who is
  not in the game's view.
- THE DEPTH CHART: for each team, each of the 22 positions an ordered list of its active men (the starter first), and the return roles KR and PR each an
  ordered list of active men of any position (a returner keeps his position). The chart holds every active man exactly once at his own position; the
  roles hold men already in the chart. How many of a position start: `roster_file.STARTERS` (WR 3, DT 2, CB 2; one of every other position).
- WHO ORDERS THE CHART: a new franchise and a quick game or a season: the file's order (the teams' real charts). In a franchise the computer teams' and
  the staff's order is the staff's rule (by rating within the position, the real order first among equals; the rule of `depth.real_starters_first` and
  `aging.place_by_rating`, now per position); the player's own team keeps his order (NX-D3, now per position) and his key-down men (NX-D4, now by
  player ID) through trades, signings, injuries and the cut, as D-147 said. The Quarterbacks item (D-140) is the QB chart of the player's team.
- NOTHING IS MADE UP to complete a team (NX-L3, NX-L4): a new franchise has exactly the men of rosters.txt on every team, at their positions, numbers
  and lists, and no other man. Made-up men exist only in later draft classes and the undrafted (they are new men, as in the real league), and as the
  one last resort of 21.4 (a family with no man at all, after injuries).

### 21.4 The view: the engine's 34 places, made for each game from the chart (never stored)

The engine plays the original's sections (6 backs, 6 receivers, 17 defenders, 2 returners, 2 kickers, the quarterback). For every game, and for every
sum that counts the men who play, the view is made from the chart, skipping the men who will not play this week (injured, NX-B1's choice applied):

1. QUARTERBACK: the QB chart's first fit man.
2. BACKS, places 1 to 6: the HB chart, then the FB chart (as today). A back place with no fit back is EMPTY: no man, usage share 0. A run is carried
   by the backs who are there, in their own proportions (one `below(total)` draw over the weights that are there: the draw count is the same). The
   fifth and sixth places carry nothing today, so a team with 4 backs plays exactly as before; a team with 2 or 3 backs gives the third and fourth
   places' 10 and 5 percent to the first two in proportion. This is the real game: a team with three backs runs with three backs.
3. RECEIVERS, places 1 to 6: WR1, WR2, WR3, TE1, WR4, TE2, WR5, TE3, ... (today's order, `roster_file.group_order`). Never short in the file; after
   injuries an empty place is handled as in 2. The uniform `rnd(6)` "downed by" draw of a kick names, for an empty place, the place's COVER (6).
4. DEFENSE, places 1 to 17: line 1 to 6 (LEDG1, REDG1, DT1, DT2, then the second tier, `group_order`), backers 7 to 11 (SAM1, MIKE1, WILL1, then the
   second tier), corners 12 to 15, safeties 16 and 17 (FS1, SS1, then FS2, SS2). A defense place the family cannot fill takes the best SPARE man of the
   nearest family, who keeps his own position in every word (21.8): a backer place takes a spare edge man (a 3-4 team's outside backers ARE its stand-up
   linebackers: this is D-157's lent linebacker made the rule; every team has at least 2 spare line men, so all 14 short places of the file are
   filled), then a spare tackle; a corner place a
   spare safety; a safety place a spare corner; a line place a spare backer. Spare means not already in the view. The defense is never short in the
   file; it can be short only after many injuries, then 6 applies.
5. RETURNERS, places 1 and 2: KR1, PR1, KR2, PR2, ... the first two different fit men (today's rule, `_team_lines`); a team with fewer than two
   different returners takes the fit backs, then receivers, then corners who are not starters (today's fallback, on real men only).
6. KICKER and PUNTER: the K and P charts' first fit man. A team with no active one plays its practice squad's (a game-day elevation, as the Dolphins do;
   in a franchise 21.7 (7) makes it real). With none on the squad either, the punter kicks or the kicker punts (what a real team does on the day).
7. THE COVER of an empty place (no draw): the nearest filled place of the same section, counting down first, then up. It is used only by the
   original's uniform draws (3 and 4 above) so that their draw count stays; the second man of a two-tackler sentence is never the first man again: the
   H16 hook (`second_tackler`, today the Franchise's) is used with the N. F. L. rules everywhere and steps to the next different man of the section.
8. THE LAST RESORT (21.3): only when a whole family has no fit man (all quarterbacks hurt; every back hurt) and no squad man of it can be elevated:
   today's stand-in is made (the stand-in's draw is made in any case, NX-B2b, so the draws are the same). It is a made-up man for that game only and is
   never on a roster, in a list or in the league file.

The view is a function of (chart, roles, who is fit, the player's choices): `roster_view(team) -> 34 player IDs or None`. The Roster the engine gets
is built from it: a name for every filled place, "" for an empty one; the tests of SR.4 play whole games and fail on an empty or doubled name in any
sentence. The R and L lists (`choices.py`), F9's "who plays" lines and every place menu skip an empty place.

THE DRAWS (NX-L3, NX-D2): the view adds no draw and removes none. A game draws exactly what it draws today; with every place filled (receivers,
defense, returners, kickers) the same draw names the same place; a run's one draw is over the weights that are there.

### 21.5 A new franchise, a quick game and a season (NX-L4)

- QUICK GAME AND SEASON (the N. F. L. rules): `RealNames.roster(team, fallback)` is replaced by the view over the file's chart (21.4) with the player's
  `nx_depth` order (by name, as today). The fallback names are still drawn first (`Game._real_rosters`), so the draws are the same; a filled place says
  the real man; an empty back place says nothing (no fallback name is ever used while the team has real men). D-157's loader hacks (the lent
  linebacker, the elevated squad kicker, the RET lines) become 21.4's rules and leave `real_names._team_lines`.
- NEW FRANCHISE (`league.new_league`): every man of rosters.txt joins his team on his list, at his position and number, in the file's chart order; the
  KR and PR lines become the roles; the free agents are free_agents.txt (D-145, D-158) with their 22-position words (21.7 (9)).
- RATINGS, AGES, POTENTIALS (no rating is copied from anyone, Q-074): the new league makes today's draws in today's order (each of the 34 places of each
  team: the drawn player's rating, potential, age; his drawn name is discarded), and gives each drawn value to the man the view puts in that place at
  full health. So the starters get exactly the draws a franchise of 0.16.x gives its places with the same seed. Every other man (active, squad, reserve
  list) gets today's bench rule (D-149: 1 to 4 under the weakest view man of his family, from a hash, no draw; the offensive line and the snapper
  FR_RESERVE_RATING; the squad today's squad rule). An empty back place's draw is made and its values are dropped.
- REAL AGES (Q-078, accepted-default): the file has no ages; SR.2's script reads Sleeper's birth dates for the free agents only. Default: the drawn and
  hashed ages as today (the progression, retirement and cap bands were measured with them). SR.5 may add the birth year to the file (a fact) and measure
  the bands with real ages; if they hold, real ages become the default.
- Two real men of one name are both in the league (21.8); nobody is renamed, nobody left off. `use_real_names`' namesake rule (a drawn surname for the
  second man) is gone.

### 21.6 league.sav format 18 and the conversion of older leagues (NX-L7)

FORMAT 18 (`data.FORMAT`; a format change, as every other, with its migration step in `LeagueRecord.from_json`):
- A player row grows from 16 to 18 values: `number` (the jersey number as text, "-" for none) and `list` ("" active, "PS" practice squad, or a reserve
  list code of `roster_file.RESERVE`). `pos` takes the 22 codes (the old group words only in rows older than 18). `place` is kept in the row and always
  -1 (the view is not stored); `status` keeps active, practice, free, released, retired, and gains "list" (on a reserve list of his team).
- The league drops `rosters` (the 32 tables of 34 IDs) from the file and gains `chart` (32 objects: position -> list of IDs, "KR" and "PR" -> list of
  IDs), `roster_version` (the VERSION of the rosters.txt the league was made from or last brought up to, 21.10) and `roster_offer` (the VERSION whose
  offer of 21.10 was answered). `depth.order` is folded into `chart` (the player's own team); `depth.key` and `injuries.stand_ins` / `injuries.chosen`
  are keyed by player ID instead of by place.
- IN MEMORY, for the modules that ask "who plays": `LeagueRecord.rosters` stays as a list of 34 IDs a team, made by the view at full health whenever a
  team's chart changes (`league.refresh_view(team)`), never saved, and `Player.place` is set from it. So the modules that mean "the men who play"
  (strength, ratings, usage, workload, honors, the engine's names) keep reading places, and the modules that mean "the men on the team" read
  `league.team_men(team)` (21.9 says which is which). This keeps SR.4 small and every band comparable.
- THE CHECKS (`league.check`, `_check_rosters`): every active man is in his team's chart exactly once at his own position; at most 53 active, at most 17
  on the squad (a new franchise may start with a file team of 50 to 53); the roles name active men of the team; no man on two teams; `list` agrees with
  `status`; a position is one of the 22 (format 18) or one of the old words (an older row, before its migration).

THE CONVERSION of a league of format 17 or older, once, when it is opened (NX-L7; never a draw, so the league's later draws are the ones it would make):
1. The old file is kept as `league.sav.before-format-18` (the store's backup pattern), then the league is migrated through every older step as today.
2. POSITIONS: every man of a team, a free agent and a retired man, is looked up by name in the game's rosters.txt (the player's copy, else the shipped
   one): found on the same team, he takes the file's position and number; found on another team (a real man the league has moved), the file's position
   and number too. A man the file does not have (drafted, undrafted, made up by an older version, a real man since gone from the league) is mapped from
   his group word to the position of his family that his team's chart is shortest of against the league's mix (21.1's counts): RB -> HB (always: a
   fullback is a fact only the file gives), FB -> FB, TE -> TE, WR -> WR, QB, K, P, CB the same, DL -> LEDG,
   REDG or DT, LB -> SAM, MIKE or WILL, S -> FS or SS, OL -> LT, LG, C, RG or RT, LS. A "RET" man (a made-up returner of an older league) becomes WR or
   CB, whichever his team is shorter of; his returner role is kept. Ties go to the first in the 22's order. The rule is written down as a table in the
   code and pinned by a test.
3. A format-16-or-older league has no bench: its teams get, at once, the real men of rosters.txt who are on that team in the file and on no team of the
   league (a real man the league has elsewhere is never moved), the quarterbacks first, then K, P, LS, then by the file's order, while the team has
   fewer than 53 active; their ratings and ages by the bench rule (no draw), their contracts the market price. So an old franchise has its backup
   quarterbacks the moment it is opened (the tester's report, Q-073).
4. THE CHART of each team: the staff's rule (by rating within the position, the real file order among equals); the player's team keeps his order of
   format 16 and 17 (`depth.order`, by group) mapped onto the positions, and his key-down men mapped by name to IDs. The returners: the old RET men's
   roles, then the file's KR and PR for real men of the team.
5. A team over 53 active after 2 and 3 (a format-17 team can have 34 places and 19 benchers with a made-up man among them): nothing is cut at the
   opening; the team is over the limit until its next cut (as the real offseason roster is 90), and the to-do list and F9's roster say so; the cut of
   the next offseason brings it to 53 by the cut's rule. The in-season signing rules count from 53 down (a team over 53 signs nobody before a release).
6. ONE SENTENCE (rule 0.28 (4): it says what was done): "Your franchise now has the real rosters' positions: every player has his real position, and
   <n> real players joined their teams." (n = 0: the second part is left out). Logged as `league_converted` with the counts (0.15). New text rows:
   SR.6 (21.11).

### 21.7 Every Franchise block on the real roster (NX-L6; built in SR.5; the module list is 21.9)

1. THE CUT TO 53 (offseason stage of the cut): every team keeps at most 53 active men. The staff's cut keeps, in this order, the chart's must-haves (two
   quarterbacks, a kicker, a punter, a snapper, and the family minimums of 21.7 (12)), then the men of the most value by `resign.value` within the
   roster's position mix; the player's own cut asks over the whole roster as today (NXL-53). `reserves.COVER_FIRST` and `reserves.fill_line` are gone:
   the draft makes linemen and snappers now (2).
2. THE DRAFT AND THE UNDRAFTED: prospects of all 22 positions. The class weights are the league's active mix of 21.1 (the 1,686 men by position, one
   table in `extras\tuning.py`, SRC-OFFICIAL counts) in place of FR_CLASS_WEIGHTS' place counts; there is no RET prospect. A team's needs are its
   positions under the family minimums. Rookies join the active roster (the cut decides) with a free jersey number of his position (the lowest number of
   the NFL's range for the position that nobody on the team has; no draw).
3. FREE AGENCY, RE-SIGNING, THE TAG, SIGNINGS IN THE SEASON, SQUAD PROMOTIONS: a man signs to the active roster when the team has fewer than 53 (or for a
   released man of the team); open "places" become open roster spots and the family minimums. The market's need of a computer team (`market.open_places`)
   is its families under the minimums and its starters' quality by family (the view), not the 34 places.
4. TRADES (NX-B4, NX-B5): any active man for any active man of any position (the value rule decides); a team's chart and the view are made again after
   it; the player's starters he set keep their places in his chart unless they leave.
5. INJURIES (NX-B1): a hurt man is out of the view; the next fit man of his position's chart, then of his family, takes his place (the staff's
   choice); the player chooses among every fit man of the family and the squad's men of it (an elevation). `injuries.after_games` still draws a PLACE
   by FR_INJ_GAME_WEIGHT and hurts the view's man there: so the offensive line and the snapper, who are in no place, are never hurt (as today), and the
   draws are the same.
6. AGING, DEVELOPMENT, RETIREMENT, CONTRACTS, MORALE, HONORS: every man of the team, by his family's row of the tuning tables (FR_PEAK, FR_PAY,
   FR_INJ_GAME_WEIGHT, FR_FILL_RATING...): the 22 positions read their family's row, the offensive line and the snapper keep the rows they have today
   (D-149), so no table gets a new number in SR.4. "Starter" (people.is_starter) means first on the chart.
7. MUST-HAVES IN THE SEASON: a computer team with no active quarterback, kicker, punter or snapper (the Dolphins' kicker; a hurt man) promotes its
   squad's man at the week's preparation (releasing the least valuable active man when it is at 53); the player's team gets a to-do item for it (the
   staff setting decides it for him). In the game of that week the elevation rule of 21.4 (6) covers him.
8. THE STRENGTH (NX-L6: "the men who play"): `strength_sum` counts the view's men at full health with today's place weights (78 in all), over the FILLED
   places, scaled back to 78: sum of weight times rating over the filled places, times 78, over the filled places' weight. So a team with three backs
   is not weaker for back places that carry nothing, and every band keeps its scale. The effective sums of a week use the view with the week's injuries.
9. FREE AGENTS FILE: free_agents.txt moves to the 22 positions (the script writes them from the same sources as rosters.txt; SR.4 or SR.5 runs it);
   an older group word is read through the conversion table of 21.6 (2).
10. THE CAP (Q-072's figure, 53 salaries): a team pays every active man (the bench was already paid: 34 places plus up to 19 is 53), so the cap stays
    FR_CAP + FR_CAP_RESERVES (247.2 million) as the first value; SR.5 measures the mean payroll of 320 new teams on the real roster at the game's market
    prices (`work\nxb2b\measure_bench_cap.py`'s method) and sets one constant `FR_CAP_ROSTER` so that a new league's mean cap use is what 0.16.0's was;
    the soaks are its check. The practice squad pay stays as built (Q-068 open).
11. THE PRACTICE SQUAD (D-136): the real squads of the file (any of the 22 positions, the line and the snapper too: B-X147's limit to "the game's
    positions" goes), 16 plus one; the elevations as today.
12. THE FAMILY MINIMUMS (the cut, the needs, the market; UNVERIFIED first values from the file's smallest real teams, 21.1): QB 2, backs 3, receivers 7,
    offensive line 8, LS 1, defensive line 8, backers 3, corners 4, safeties 3, K 1, P 1. A table in tuning, measured again by the soaks.
13. THE SOAKS (NX-L6, NX-L10): 20 seasons on both calendars, the whole program and the program rig, every band of D-149's soaks, plus: every team 53 or
    fewer after every cut, every family at its minimum, no made-up man on a roster, no view with a doubled man, the mean cap use.

### 21.8 Speech of a 53-man roster by positions (built in SR.6)

- F9, Franchise, roster (and the roster of any team where the menus show one): the positions in the 22's order, each heading said with its count
  ("Quarterbacks, 3."), then the men in chart order, each said: name, position in words (`roster_file.SPOKEN`), depth ("starter", "second", "third"...;
  the returner roles after it: "kick returner"), number, rating, age, then contract and injury as today. A man in a place of another family's section
  in the game (a 3-4 edge man in a backer place) is still said by his own position everywhere: "T.J. Watt, left edge".
- Keys (rule 0.24; letters as in other lists, never T, rule 0.22): Up and Down man by man, Left and Right (and Page Up, Page Down) position by
  position, Home and End, and the first letter of a position's words jumps to it, the same letter again to the next position with that letter (L: left
  tackle, left guard, left edge; R: right guard, right tackle, right edge; S: strong-side linebacker, strong safety; and so on); the tight ends and the
  tackles whose words start with T are reached by the arrows and by E ("end") for the tight ends. Enter opens the man's items as today. F5, F6 and the
  README list them; the plain description of each item (rule 0.25).
- "On the bench" (NXL-52) is gone; the practice squad and the reserve lists are their own headings after the active roster ("Practice squad, 16.",
  "Injured reserve, 9.").
- Two men of one name (21.1): in a list or sentence that can hold men of more than one team (league lists, trades, free agents, honors, history, the
  news), a name that another man of the league also has is said with his position and team ("Justin Jefferson, strong-side linebacker, Browns"); two
  of one name on one team (after a trade) are told apart by their numbers in every list ("DeVonta Smith, number 6"). The play-by-play says the name only.
  The league never renames a real man; everything is keyed by player ID; a typed name (rule 0.19) that two men share asks which one.

### 21.9 Where each module goes (the inventory of this session; SR.4 does the model, SR.5 the blocks)

- MEANS "WHO PLAYS" (keeps reading the view's places in memory, 21.6): `ratings` (team_edge, carrier_weights, kicks), `workload`, `usage` in
  `nfl_rules`, `honors` (candidates by place weight), `camp`, `staff.side_rating` and `lean`, `injuries.after_games`' place draw, `injury_flow`'s
  report, `league.roster_for_game`, `strength_sum`, `people.played_ids`.
- MEANS "WHO IS ON THE TEAM" (moves to `team_men` and the chart): `league` (statuses, `bench`, `active_of`, `group_of`, `_check_rosters`,
  `fix_real_positions`, `fix_real_backs`, `use_real_names`, `new_league`), `data` (PLACES stay for the view; POSITIONS, ROSTER_ORDER, BENCH_ORDER,
  RESERVE_POSITIONS, ALL_POSITIONS, GROUP_SIZE, WEIGHT by family), `aging` (league_order, place_by_rating -> chart order, fill_places -> gone),
  `draft` and `draft_flow` (needs, open places, the cut, surplus by family), `undrafted`, `market` (filled, ready_bench -> gone, open_places, fit_level),
  `signings` and `signings_flow`, `trades` and `trade_flow` (same-position rule -> any position, execute swaps lists not places), `injuries` (lineup,
  cover_choices, bench_covers -> the chart's next man), `practice` (RETURN_COVER, eligible: any of the 22), `reserves` (retired whole: the bench is
  gone; its checks move to `_check_rosters`), `contracts` (team_players, replacement_rating by family), `resign` (expiring, room_after: 53 spots),
  `tags`, `people` (is_starter -> chart first; holdouts, acceptable), `depth` (put_first, reset, real_starters_first -> per position), `menus`
  (roster_menu, group_picker -> 21.8), `history.Words` ("on the bench" -> the list), `quarterbacks` (starter = QB chart first; swap within the chart),
  `depth_chart.py` (key_names and key_place_for by ID), `real_names` (`_assemble`, `places`, `_team_lines`' D-157 rules -> 21.4), `store` (`_benches`,
  `create`, `player_names`).
- RETURNERS: "RET" leaves `data.POSITIONS`, FR_PEAK, FR_CLASS_WEIGHTS, FR_PAY, FR_INJ_GAME_WEIGHT, `draft.SURPLUS_POSITIONS`, `depth.GROUPS`,
  `practice.RETURN_COVER`, `injury_flow.RET_FIRST`; the return places of the view read the roles.
- NX-L5 (Jim Kitchen's roster code out of the N. F. L. rules): the 34 places as storage, the bench, RET as a position, the short group's made-up man and
  the original's groups as positions are all gone from the N. F. L. rules by 21.3 to 21.7; Classic keeps every one (its golden transcript is a test of
  SR.4 and SR.7).

### 21.10 "Get the latest rosters" in the game (NX-L9; D-154 and D-156: the game downloads the maintainer's checked file only)

- WHERE: F9, Customize, "get the latest rosters", and F9, Franchise, the same item after "get the latest calendar". Only when the player chooses it
  (rule 0.15); never in a game.
- WHAT: the game downloads `rosters/rosters.txt` and `rosters/free_agents.txt` from the repository (raw.githubusercontent.com, the calendars' route of
  D-141, `data\web.py` by WinHTTP), reads each VERSION line ("as of <date>"), and compares with its own. Newer: the file is parsed and checked by
  `roster_file.parse` and `roster_file.check` (the script's checks, D-155: a failure refuses the file) and the free agents by the loader's rules; the
  player's current files are kept as `rosters.txt.before-<date>` and `free_agents.txt.before-<date>` in the customize folder; the new ones are written
  there and read at once. The same or older: nothing changes. One sentence each time: "You now have the rosters of <date>." / "You already have the
  newest rosters, from <date>." / "The rosters could not be downloaded: <reason>. Your rosters stay as they were." (no connection, the server, a check
  that failed and which). A player's own edited rosters.txt (not the shipped text and not a downloaded one) is still replaced only after one yes/no
  question, "no" first, because his own lines would be lost (they stay in the backup).
- WHAT IT CHANGES: quick games, seasons and new franchises use the new file at once. A FRANCHISE IN PROGRESS keeps its own league: its history is the
  player's (NX-L9). When a league whose `roster_version` is older than the new file is next opened, it is offered ONCE (`roster_offer`): "There are
  newer real rosters, from <date>. Bring the other 31 teams up to them? Your own team is not changed." with "No, keep my league as it is" first, so
  Enter changes nothing (rule 0.23's spirit: saved progress is not changed by Enter). Yes, outside a game and outside the draft and the cut:
   1. Only the 31 computer teams change; the player's team and his men are never touched.
   2. For each computer team, each man of the new file's team: on that team already -> the file's position, number, list and chart order; on another
      computer team of the league -> he moves (his contract goes with him); on the player's team -> he stays there and the computer team does without
      him; a free agent of the league -> he signs at the market price; not in the league -> he joins with the bench rule's rating, a hashed age and the
      market price (no draw).
   3. A man of a computer team whom the new file does not have on that team: a real man the file has nowhere (released in reality) becomes a free agent
      (released, no dead money: the league did not choose it); a man the league made (drafted, undrafted, older made-up men) stays, and a team over 53
      goes down to 53 by the staff's cut rule at once.
   4. The charts of the 31 teams: the file's order for the file's men, the staff's rule for the others; `roster_version` set; the backup
      `league.sav.before-rosters-<date>`; one sentence: "The other 31 teams now have the rosters of <date>: <n> players moved or joined." Logged
      `league_rosters_updated` with the counts.
   5. In the regular season after the trade deadline the offer still works (it is the player's choice to bring the real league in); the news of the
      week says nothing of it (no made-up news).
- The second item of NX-L9 (the pull from the sources inside the game) stays DROPPED (D-154): `update_rosters.py` is the maintainer's tool.
- NOT LIVE UNTIL A PUSH: the repository has no `rosters` folder yet; publishing it is a public action (the owner's approval, 8.3); until then the item
  says the player already has the newest (the calendars' behaviour, D-141). The fake-server tests (newer, same, damaged, no connection) are SR.6's.

### 21.11 Texts, keys, logs and tests (for SR.4 to SR.7)

- New text rows (`strings_nx.tsv`, SR.6): the conversion sentence (21.6), the offer, its answers and its result (21.10), the download's three
  sentences and the own-file question, the roster headings and the man's line (21.8), the namesake forms, the to-do item for a must-have (21.7 (7)),
  F5/F6 lines for the keys. The CHANGELOG.md section with "How to test" for each (rule 0.29); PLAYTEST_LIST: the Bears' roster in a new franchise first.
- Log lines (0.15): `league_converted`, `league_rosters_updated`, `rosters_download` (result, version, size), `roster_view` at debug level when a place is
  empty or covered, `must_have_promoted`.
- Tests (NX-L10): all 32 teams of a new franchise equal rosters.txt (names, positions, numbers, lists, chart order, roles; no made-up man; nobody left
  off); the view of every team at full health (empty back places only where the team has fewer than 6 backs; the 14 short backer places filled by edge
  men; no doubled man); whole games of every team with no empty or doubled name in any sentence; the draws of a game the same as 0.16.2's for a team
  with every place filled; leagues of format 16 and 17 opened (every team's real quarterbacks, positions by name, the over-53 case, the sentence);
  format 18 round trip; the offer and the update with the player's team untouched; the download with a fake server; the cap measurement; the soaks;
  Classic's golden transcript.

### 21.12 What this design leaves open (OPEN_QUESTIONS)

- Q-078 real ages (21.5): accepted-default, drawn and hashed ages; answers-by SR.5 (the birth years in the file and the bands measured).
- Q-079 when a man of a real reserve list comes back in a franchise: accepted-default, at the next offseason (every list man returns to the active
  roster before the cut; IR, PUP and NFI end with the season as the real ones do for most men); the injury model of the Franchise stays the game's for
  its own injuries. Answers-by: SR.5's soaks and the owner's playtest.
- Q-080 the offer's first answer (21.10): accepted-default "No, keep my league as it is" first; answers-by the owner's playtest.
- Q-081 the family minimums (21.7 (12)): accepted-default as listed, UNVERIFIED; answers-by SR.5's soaks.
- None needs the owner before SR.4.

### 21.13 Choosing who starts from the current rosters (NX-L11, D-160; the owner's requirement of 2026-10-25, during SR.3)

- THE DATA: the starters are the first men of each position's chart (21.3); STARTERS (WR 3, DT 2, CB 2, one of every other position) says how many. A quick game or a season keeps the player's order in `nx_depth` by team, position and name, now on the 22 positions and the roles KR and PR ("T17 LT=Theo Benedet; T17 KR=Kalif Raymond"); an older entry by group (RB, WR, TE, DL, LB, CB, S, K, P, RET) is read once through the conversion table of 21.6 (2) (DL to the man's own position in the file, RET to KR) and written back in the new form. A franchise keeps it in the league's chart (format 18). The view (21.4) takes them first; nothing else changes the draws.
- CHOOSING A STARTER: the position's list holds every active man of the position, then the men of its family who could move there (the other side or role: LT and RT, LG and RG, LEDG and REDG, SAM MIKE WILL, FS and SS, HB and FB), then the practice squad's men of the position. Enter on a man makes him the starter of the slot the player is on (the man who was there takes the chosen man's old place on the chart: a swap, so nobody leaves the chart); a man moved from the other side or role takes the new position on the chart and keeps his family. A squad man chosen is an elevation (quick game or season: two a game; franchise: D-136's elevations, then a promotion with its own question); said in one sentence.
- THE LINEUP ITEM: one list: QB, HB, FB (when the team has one), WR1 to WR3, TE, LT, LG, C, RG, RT; LEDG, DT1, DT2, REDG, SAM, MIKE, WILL, CB1, CB2, FS, SS; K, P, LS; KR, PR. Each line: position in words, then the man ("left tackle, Theo Benedet, number 79"). Enter opens that position's choice; Backspace or Escape returns to the line. A position the team has nobody active for says so ("long snapper: nobody on the active roster; the practice squad has Beau Gardner") and offers the squad man.
- WHERE: F9, Rules, Depth charts (any team in a quick game or season; the 32 teams, letters find one) gains the lineup item first and the 22 positions and two roles after it (the old group items go); in a franchise F9, Rules, Depth charts and F9, Franchise, roster (Enter on a man: "make him the starter") work on the player's own team. Not inside a play; between plays only through F9 as today.
- WHEN THE ROSTER CHANGES: a chosen man no longer on the team (a trade, a release, a roster update, a new rosters.txt) is dropped from the choice and the next man of the chart starts; at the next menu or week the player hears one sentence per dropped starter ("Darnell Wright is no longer on the team; Ozzy Trapilo starts at right tackle."). A chosen man who is hurt is replaced as NX-B1 says and starts again when fit.
- TESTS AND TEXTS: as NX-L11's done-when; text rows NXM-L.. (SR.6); the log line `starter_chosen` with team, position, man and mode.

### 21.14 SR.4 as built (2026-10-25, D-161): what differs from 21.3 to 21.6 until SR.5

- `Player.pos` stays the Franchise's group word (the rows of its tuning tables and the groups of its places); the real position is `Player.position`. A player row of format 18 has 19 values: the 16 of format 17, then position, number, list. SR.5 folds `pos` into the position (its family's row) when every block reads the families.
- The 34 places are still STORED in league.sav (21.6 drops them in SR.5) because the cut, the draft, the fill, signings, trades, injuries and aging still write places; `real_roster.sync_chart` makes the charts from the places and the bench at every save (the men of the places first, in place order; then the earlier chart order; then the rating), and `real_roster.refresh_view` makes a team's places from its chart (a new franchise; the player's choice of a starter, in a stage of whole places).
- The Franchise's view keeps one man in one place (`make_view(distinct=True)`): its returners are the role men who hold no other place, then the spare backs, receivers and corners (Q-082); the quick game's view lets a returner also hold his place.
- An empty back place is marked, never guessed from a repeated name (fixesforgames B-P175): `Roster.empty` in a game, the identity `injuries.EMPTY` in a lineup; every share and injury draw skips it.
- A converted older league keeps its places as they were (no view is made for it until SR.5); its charts, positions, numbers and (format 16 and older) missing real men are the conversion's.
- 21.13's data is built (`real_roster.choose_starter`, `depth_chart.choose_starter`, `migrate_depth`, nx_depth by position and role); the write-back of an older group entry in the new form is done by SR.6's menus, which write only the new form.

### 21.15 SR.5 as built (2026-10-25, D-164): every Franchise block on the chart

- THE CHART IS THE TEAM (21.3, 21.6). league.sav FORMAT 19: `rosters` (the 34 places) is no longer saved and a player row's place is -1; the places are
  made in memory from each team's chart by `real_roster.refresh_view` (the chart cleaned: every active man of the team once at his own position, nobody
  else; each position in the staff's order, the best rating first, the chart's order among equals, the player's own team with the men he put first,
  `depth["order"]` by POSITION now; the roles kept to men still there; then `roster_model.make_view(distinct=True)`). The status "reserve" (D-149's
  bench) is gone: a man of the roster without a place is an active man (`LeagueRecord.bench` lists them from the chart). `Player.pos` is his family's word
  (QB RB WR OL DL LB CB S K P LS), always `roster_model.GROUP[position]`; RET is only the group of the view's two return places. A file of format 18 or older
  is read through `real_roster.from_places` (its stored places and bench checked as written, `legacy_check`, then the chart; the order by group becomes the
  order by position); a format-19 file's chart is checked as written (a damaged chart is refused, never cleaned silently) before the places are made.
- ONE WAY ON AND OFF A TEAM: `real_roster.join(league, team, man)` and `leave(league, man, status)` (then `refresh_view`) are used by signings, the market,
  the tag's offer sheet, trades (both teams), practice squad promotions, re-signing's let-go, retirements and the cut. The store's save makes every chart
  and view again first (`_mend_charts`) and logs `chart_mended` with the teams when a chart's men had to change (rule 0.15: a path that forgot to say so).
- THE CUT TO 53 (21.7 (1)): `draft.keep_plan` keeps the family minimums first (FR_FAMILY_MIN; a one-man family's man under the floor not counted), then
  every man by keep value while his family is under its most (FR_FAMILY_MAX: QB 3, K 1, P 1, LS 1), at most 53 less the men the fill must make;
  `apply_cut` ends the draft and makes every chart again (the rookies who stay join them). The fill is `real_roster.fill_needs` (21.3's last resort, after
  the cut: an undrafted rookie for each man a family is short of its minimum, drawn as the old fill drew; NX-L12 surnames). `return_lists` brings the real
  reserve lists' men back at the start of the cut (Q-079's default). COVER_FIRST, fill_line, real_reserves and reserves.py are gone.
- THE DRAFT (21.7 (2)): the class by position (FR_CLASS_POSITIONS, the league's mix; no returner prospect); a class row has 7 values (the position last);
  needs by family: under FR_ROSTER_TARGET (the league's mean rounded DOWN: QB 2, RB 3, WR 9, OL 9, DL 10, LB 4, CB 5, S 4, K 1, P 1, LS 1) or a starter
  (FR_GROUP_STARTERS of the family's best) under FR_DRAFT_WEAK, the line and the snapper apart (they play no place); "better" when the prospect beats
  the weakest starter; K, P and LS are the surplus positions. A rookie gets the lowest free jersey number of his position's NFL range.
- THE MARKET AND SIGNINGS (21.7 (3)): a man signs while his team has fewer than 53 (`real_roster.room`); a computer team bids for its families under their
  targets (and a weak starter), at most its room, and an offer of a family whose need an earlier signing of the round met lapses (`resolve`'s spots); the
  player's own offers are his choice. Signings in the season, practice promotions and the tag's sheet join the chart. The season's veterans of the pool
  are made for the line and the snapper too.
- TRADES (21.7 (4)): any man for any man; a trade that leaves a team under a family minimum it holds is refused ("a team would be short of a position").
  The trade menus still offer one position (SR.6 widens them).
- INJURIES (21.7 (5)): the lineup is the view with the week's injuries; a hurt man's place goes to the man the staff's rule names (the best fit man of his
  family without a place first, never above the hurt man's rating, then the next man up, then the stand-in); the player's choice (NX-B1) is any fit man of
  the place's family or of his own; a hurt man without a place leaves no place to fill.
- STARTERS (21.7 (6)): `people.is_starter` is the first STARTERS men of his position's chart.
- MUST-HAVES (21.7 (7)): a team with no active kicker or punter signs its squad's to the 53 at the next refresh (logged `must_have_promoted`); the family
  minimums are kept by the cut, the fill and the trade rule, so a team starts every season with them (the soaks).
- THE CAP (21.7 (10)): `contracts.cap_of` = FR_CAP + FR_CAP_ROSTER (510, measured: `work\sr5\measure_cap.py`) for every league; the re-signing room counts
  the 53 spots (`resign.league_terms`), only the roster's men hold a spot (the squad is paid, holds none) and the minimum's reserve is never negative.
- THE SQUADS (21.7 (11)): any of the 22 positions; the made-up young men of a top-up take a position of their family and the NX-L12 surnames.
- NX-L12 (D-163): `assets\data\nfl_surnames.txt` (9,504 last names of real NFL players: nflverse's players table, CC BY 4.0, and the rosters; written by
  `game\tools\update_surnames.py`, refreshed by `update_rosters.py --write`), a customizable file of the N. F. L. rules (real_names kind
  `nflsurnames`); every made-up man of the Franchise takes one (weekly.surnames_of); a first name never makes a real player's full name of the files
  (written or spoken, first_names.first_name steps to the next name); a quick game's last-resort name is a real surname chosen from the drawn one
  (`RealNames.last_resort`, no draw). Classic keeps the original's 1,708 surnames.
- NOT YET (SR.6): the roster said by positions (21.8), the lineup item and the choice of every starter by menu (21.13), the conversion's sentence, the
  in-game update (21.10); the trade menus' other positions; a returner on top of his place in a franchise game (Q-082, decided for SR.6).

### 21.16 SR.7 as built (2026-10-26, D-167): real ages, the position words, NX-L10's checks

- REAL AGES (21.5's last item settled, Q-078): rosters.txt's player line may end with `; age N; seasons N` (written by update_rosters.py from nflverse's roster
  table, Sleeper's feed second); a new franchise gives the real men their real ages (21 to 40) and seasons (at most age less 21), after the view's draws;
  each practice squad keeps at most six veterans (the six most experienced); a man with no age keeps the drawn or hashed age. Measured: the 20-season
  bands of SR.5 and SR.6 hold (D-167 (3)).
- POSITION WORDS: the draft's prospects, the rookies before the cut, the undrafted, the market's free agents and the award rows say the man's own
  position (an older draft's prospect without one keeps his group's word).
- NX-L10 (21.11's list) and where each item is tested: all 32 teams of a new franchise equal rosters.txt (test_real_roster_sr4 "every team ... man for
  man", the Bears' quarterbacks and Miller Moss); the view of every team at full health (sr4 "the view of every team ... the design's counts"); whole
  games of every team, no empty or doubled name (test_nx_l10_sr7, 16 games; sr4 "a whole quick game ... never gives an empty back place the ball");
  the draws the same as 0.16.x (sr4 "the same draws with or without the real rosters", test_sx11_names); leagues of format 16 and 17 opened (sr4 the
  format 16 and 17 tests, "the store keeps the older file and converts"); format 18 and 19 round trips (sr4, sr5); the offer and the update with the
  player's team untouched and the download with a fake server (test_rosters_update_sr6); the cap measurement (sr5 "the cap is the measured cap");
  the soaks (work\sr6, work\sr7, 0 problems); Classic's golden transcript (test_pag_golden and the Classic tests in the full suites).
