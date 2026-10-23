# NFL_NAMES_RESEARCH (nfl4 only): the real head coaches and rosters of the 32 teams (SX.11, NX-N2, NX-N3, D-098)

Written by `work\sx11\make_names_doc.py` from the research files of session SX.11 (2026-10-22); never edit by hand. CLAUDE.md rule 0.19, playbook 7.14.

## 1. What was researched and how

- Date: 2026-10-22, week 7 of the 2026 season. The data is the current 2026 roster of each team as its own site shows it, and its head coach.
- Method: eight research subagents (one per division) fetched, for each of the 32 teams, the coaches page, the players roster page and the
  depth chart page of the team's own site (SRC-OFFICIAL; all 32 teams' official pages loaded, so no secondary source was needed for rosters
  or coaches). The Texans' depth chart is an image, so ESPN's depth chart (SRC-SECONDARY) was used for the order of that team's positions.
  The subagents returned their findings as text and the session wrote the files (fixesforgames B-X119).
- The fetch tool returns a summary of each page, not its raw text. Names are therefore as the summary spelled them (SRC-OFFICIAL for the page,
  with that caveat). A spelling the owner or a player finds wrong is fixed in `rosters.txt` (the README says how); the first fresh reviewer
  of the file (P8 or a later season's refresh) should spot-check names with accents, apostrophes and suffixes against the live pages.
- The roster pages show no "as of" date; the depth charts are labelled "Unofficial" by the teams (Bears: as of 10/6/2026, Titans: as of
  10/20/26, Packers: 10/20/26, 49ers: 10/21/26, Raiders: 10/20/26). The date of the data is the fetch date, 2026-10-22.
- Unusual rows, as the pages show them (not checked against a second source): the Rams' page lists Aaron Donald (99) as active and
  Myles Garrett (95) and Davante Adams (17) on Reserve/Injured; the Browns' page lists Jared Verse; Jaxson Dart, Jalen Hurts and Brian Burns
  are injured (not in the active table). The data takes the pages as they are.

## 2. Terms of use (NX-N3; Claude is not a lawyer)

- All 32 team sites are NFL-network sites. The NFL's terms of use (https://www.nfl.com/legal/terms/, section 1) allow "your own individual
  non-commercial and informational purposes", bar copying or redistributing the site's content without express permission, and bar (section
  1.3) the "systematic retrieval of data or other content" to build a compilation or database without prior written consent. The Broncos'
  and the Buccaneers' own terms pages say the same (personal, non-commercial use; no bots; no republishing); the other 30 teams' own terms pages
  were not found or not fetched.
- What the game keeps is facts only: a name, a jersey number and a position for the players of the positions the game uses, a head coach's
  name, no ratings, photographs, logos or text of the pages. Facts are not copyrighted, but the terms of the sites are a contract about how
  the data was retrieved and reused, and this research did retrieve a roster for each team in a systematic way (32 teams).
- DECISION (D-098): the files are built and kept in the repository as the program's built-in values; whether they are PUBLISHED in the
  repository at P11 is the owner's decision (Q-040, owner-needed, with a recommended answer). The README says the names are used descriptively
  and are not endorsed by the teams or the league.

## 3. How the files are made (decisions, all recorded in D-098)

- `clone/assets/data/coaches.txt`, `rosters.txt`, `respellings.txt` are written by `work/sx11/make_names_data.py` from the research files in
  `work/sx11/` (`source_*.txt`, `findings_nfc_east.txt`) and copied to the player's customize folder (playbook 7.9, 7.10).
- Players: the ACTIVE table of the team's roster page (the reserve/injured, PUP, NFI, suspended and practice-squad lists are not the team's players
  today). Offensive linemen and long snappers are not in the file: the game has no such place. One exception: the Dolphins' active table has no
  kicker (their depth chart says "K: no name listed"), so their practice-squad kicker is used.
- Positions: the page's position maps to QB, RB (RB, HB), FB, WR, TE, DL (DL, DT, DE, NT, EDGE), LB (LB, ILB, OLB, MLB), CB, S (S, FS, SS), K, P.
  A hybrid takes his first position (RB/WR is RB, WR/CB is WR, FB/DL is FB). A player the page calls DB is a CB or an S by the depth chart group he is in
  (the Bears' page calls every defensive back DB).
- Order: a team's players are written in depth order, the starters of each position first (the depth chart's order; a position with several
  rows takes the first of each row first).
- Returners: the first two different names of the depth chart's kick return and punt return rows are written again as RET lines.
- The game's 33 places (6 running backs, 6 receivers, 17 defensive players = 6 DL + 5 LB + 4 CB + 2 S, 2 returners, 2 kickers) and the quarterback
  are taken from these lines by `extras/real_names.py`: receivers are the wide receivers and tight ends in the order WR1, WR2, WR3, TE1, WR4, TE2;
  a short position takes the players left over (the order is in the module). No place is left without a real player in the shipped files.
- Spoken forms: the file keeps the written name; the game says the respelled form (`respellings.txt`): Jr. is Junior, Sr. Senior, II the second,
  III the third, IV the fourth, V the fifth, St. Saint. Pronunciation of other names cannot be checked by listening here; the owner's playtest
  adds lines to the file (PLAYTEST_LIST item 15).
- T24 was the game's "Redskins" and is "Commanders" since 2026-10-22 (Q-026 answered by the owner, D-120): the real team is the Washington Commanders; the files go by the team's ID, so renaming the team in
  teams.txt does not change its players.

## 4. The teams

### T01 Bengals
- Head coach: Zac Taylor (Head Coach ; https://www.bengals.com/team/coaches-roster/ ; SRC-OFFICIAL)
- Roster: https://www.bengals.com/team/players-roster/ (none shown ; SRC-OFFICIAL ; 2026-10-22)
- Depth chart: https://www.bengals.com/team/depth-chart/ ; none shown ; SRC-OFFICIAL
- Active players in the research: 42

### T02 Browns
- Head coach: Todd Monken (Head Coach ; https://www.clevelandbrowns.com/team/coaches-roster/ ; SRC-OFFICIAL)
- Roster: https://www.clevelandbrowns.com/team/players-roster/ (none shown ; SRC-OFFICIAL ; 2026-10-22)
- Depth chart: https://www.clevelandbrowns.com/team/depth-chart/ ; none shown ; SRC-OFFICIAL
- Active players in the research: 42

### T03 Ravens
- Head coach: Jesse Minter (Head Coach ; https://www.baltimoreravens.com/team/coaches-roster/ ; SRC-OFFICIAL)
- Roster: https://www.baltimoreravens.com/team/players-roster/ (none shown ; SRC-OFFICIAL ; 2026-10-22)
- Depth chart: https://www.baltimoreravens.com/team/depth-chart/ ; none shown ; SRC-OFFICIAL
- Active players in the research: 43

### T04 Steelers
- Head coach: Mike McCarthy (Head Coach ; https://www.steelers.com/team/coaches-roster/ ; SRC-OFFICIAL)
- Roster: https://www.steelers.com/team/players-roster/ (none shown ; SRC-OFFICIAL ; 2026-10-22)
- Depth chart: https://www.steelers.com/team/depth-chart/ ; none shown ; SRC-OFFICIAL
- Active players in the research: 43

### T05 Bills
- Head coach: Joe Brady (Head Coach ; https://www.buffalobills.com/team/coaches/ ; SRC-OFFICIAL)
- Roster: https://www.buffalobills.com/team/players-roster/ (none shown ; SRC-OFFICIAL ; 2026-10-22)
- Depth chart: https://www.buffalobills.com/team/depth-chart/ ; none shown ; SRC-OFFICIAL
- Active players in the research: 42

### T06 Dolphins
- Head coach: Jeff Hafley (Head Coach ; https://www.miamidolphins.com/team/coaches-roster/ ; SRC-OFFICIAL)
- Roster: https://www.miamidolphins.com/team/players-roster/ (none shown ; SRC-OFFICIAL ; 2026-10-22)
- Depth chart: https://www.miamidolphins.com/team/depth-chart/ ; none shown ; SRC-OFFICIAL
- Active players in the research: 42

### T07 Jets
- Head coach: Aaron Glenn (Head Coach ; https://www.newyorkjets.com/team/coaches/ ; SRC-OFFICIAL)
- Roster: https://www.newyorkjets.com/team/players-roster/ (none shown ; SRC-OFFICIAL ; 2026-10-22)
- Depth chart: https://www.newyorkjets.com/team/depth-chart/ ; none shown ; SRC-OFFICIAL
- Active players in the research: 43

### T08 Patriots
- Head coach: Mike Vrabel (Head Coach ; https://www.patriots.com/team/coaches/ ; SRC-OFFICIAL)
- Roster: https://www.patriots.com/team/players-roster/ (none shown ; SRC-OFFICIAL ; 2026-10-22)
- Depth chart: https://www.patriots.com/team/depth-chart/ ; none shown ; SRC-OFFICIAL
- Active players in the research: 43

### T09 Broncos
- Head coach: Sean Payton (Head Coach ; https://www.denverbroncos.com/team/coaches-roster/ ; SRC-OFFICIAL)
- Roster: https://www.denverbroncos.com/team/players-roster/ (none shown ; SRC-OFFICIAL ; 2026-10-22)
- Depth chart: https://www.denverbroncos.com/team/depth-chart/ ; none shown ; SRC-OFFICIAL
- Active players in the research: 43

### T10 Chargers
- Head coach: Jim Harbaugh (Head Coach ; https://www.chargers.com/team/coaches/ ; SRC-OFFICIAL)
- Roster: https://www.chargers.com/team/players-roster/ (none shown ; SRC-OFFICIAL ; 2026-10-22)
- Depth chart: https://www.chargers.com/team/depth-chart/ ; none shown ; SRC-OFFICIAL
- Active players in the research: 43

### T11 Chiefs
- Head coach: Andy Reid (Head Coach ; https://www.chiefs.com/team/coaches-roster/ ; SRC-OFFICIAL)
- Roster: https://www.chiefs.com/team/players-roster/ (none shown ; SRC-OFFICIAL ; 2026-10-22)
- Depth chart: https://www.chiefs.com/team/depth-chart/ ; none shown ; SRC-OFFICIAL
- Active players in the research: 41

### T12 Raiders
- Head coach: Klint Kubiak (Head Coach ; https://www.raiders.com/team/coaches-roster/ ; SRC-OFFICIAL)
- Roster: https://www.raiders.com/team/players-roster/ (none shown ; SRC-OFFICIAL ; 2026-10-22)
- Depth chart: https://www.raiders.com/team/depth-chart/ ; dated October 20, 2026 ; SRC-OFFICIAL
- Active players in the research: 43

### T13 Colts
- Head coach: Shane Steichen (Head Coach ; https://www.colts.com/team/coaches-roster/ ; SRC-OFFICIAL)
- Roster: https://www.colts.com/team/players-roster/ (none shown ; SRC-OFFICIAL ; 2026-10-22)
- Depth chart: https://www.colts.com/team/depth-chart/ ; none shown ; SRC-OFFICIAL
- Active players in the research: 43

### T14 Jaguars
- Head coach: Liam Coen (Head Coach ; https://www.jaguars.com/team/coaches-roster/ ; SRC-OFFICIAL)
- Roster: https://www.jaguars.com/team/players-roster/ (none shown ; SRC-OFFICIAL ; 2026-10-22)
- Depth chart: https://www.jaguars.com/team/depth-chart/ ; none shown ; SRC-OFFICIAL
- Active players in the research: 44

### T15 Texans
- Head coach: DeMeco Ryans (Head Coach ; https://www.houstontexans.com/team/coaches-roster/ ; SRC-OFFICIAL)
- Roster: https://www.houstontexans.com/team/players-roster/ (none shown ; SRC-OFFICIAL ; 2026-10-22)
- Depth chart: https://www.espn.com/nfl/team/depth/_/name/hou/houston-texans ; none shown ; SRC-SECONDARY
- Active players in the research: 40

### T16 Titans
- Head coach: Robert Saleh (Head Coach ; https://www.tennesseetitans.com/team/coaches-roster/ ; SRC-OFFICIAL)
- Roster: https://www.tennesseetitans.com/team/players-roster/ (none shown ; SRC-OFFICIAL ; 2026-10-22)
- Depth chart: https://www.tennesseetitans.com/team/depth-chart/ ; Unofficial Depth Chart (as of 10/20/26) ; SRC-OFFICIAL
- Active players in the research: 42

### T17 Bears
- Head coach: Ben Johnson (Head Coach ; https://www.chicagobears.com/team/coaches/ ; SRC-OFFICIAL)
- Roster: https://www.chicagobears.com/team/players-roster/ (none shown ; SRC-OFFICIAL ; 2026-10-22)
- Depth chart: https://www.chicagobears.com/team/depth-chart/ ; as of 10/6/2026 ; SRC-OFFICIAL
- Active players in the research: 43

### T18 Lions
- Head coach: Dan Campbell (Head Coach ; https://www.detroitlions.com/team/coaches-roster/ ; SRC-OFFICIAL)
- Roster: https://www.detroitlions.com/team/players-roster/ (none shown ; SRC-OFFICIAL ; 2026-10-22)
- Depth chart: https://www.detroitlions.com/team/depth-chart/ ; none shown ; SRC-OFFICIAL
- Active players in the research: 42

### T19 Packers
- Head coach: Matt LaFleur (Head Coach ; https://www.packers.com/team/coaches-roster/ ; SRC-OFFICIAL)
- Roster: https://www.packers.com/team/players-roster/ (none shown ; SRC-OFFICIAL ; 2026-10-22)
- Depth chart: https://www.packers.com/team/depth-chart/ ; Unofficial, Oct. 20, 2026 ; SRC-OFFICIAL
- Active players in the research: 38

### T20 Vikings
- Head coach: Kevin O'Connell (Head Coach ; https://www.vikings.com/team/coaches-roster/ ; SRC-OFFICIAL)
- Roster: https://www.vikings.com/team/players-roster/ (none shown ; SRC-OFFICIAL ; 2026-10-22)
- Depth chart: https://www.vikings.com/team/depth-chart/ ; none shown ; SRC-OFFICIAL
- Active players in the research: 43

### T21 Cowboys
- Head coach: Brian Schottenheimer (Head Coach ; https://www.dallascowboys.com/team/coaches-roster/ ; SRC-OFFICIAL)
- Roster: https://www.dallascowboys.com/team/players-roster/ (none shown ; SRC-OFFICIAL ; 2026-10-22)
- Depth chart: the roster page's order
- Active players in the research: 53

### T22 Eagles
- Head coach: Nick Sirianni (Head Coach ; https://www.philadelphiaeagles.com/team/coaches-roster/ ; SRC-OFFICIAL)
- Roster: https://www.philadelphiaeagles.com/team/players-roster/ (none shown (most recent dated item October 21, 2026) ; SRC-OFFICIAL ; 2026-10-22)
- Depth chart: the roster page's order
- Active players in the research: 51

### T23 Giants
- Head coach: John Harbaugh (Head Coach ; https://www.giants.com/team/coaches-roster/ ; SRC-OFFICIAL)
- Roster: https://www.giants.com/team/players-roster/ (none shown ; SRC-OFFICIAL ; 2026-10-22)
- Depth chart: the roster page's order
- Active players in the research: 53

### T24 Commanders (the original's Redskins; the game says Commanders since 2026-10-22, D-120)
- Head coach: Dan Quinn (Head Coach ; https://www.commanders.com/team/coaches-roster/ ; SRC-OFFICIAL)
- Roster: https://www.commanders.com/team/players-roster/ (none shown ; SRC-OFFICIAL ; 2026-10-22)
- Depth chart: the roster page's order
- Active players in the research: 53

### T25 Cardinals
- Head coach: Mike LaFleur (Head Coach ; https://www.azcardinals.com/team/coaches-roster/ ; SRC-OFFICIAL)
- Roster: https://www.azcardinals.com/team/players-roster/ (none shown ; SRC-OFFICIAL ; 2026-10-22)
- Depth chart: https://www.azcardinals.com/team/depth-chart/ ; none shown ; SRC-OFFICIAL
- Active players in the research: 44

### T26 Forty Niners
- Head coach: Kyle Shanahan (Head Coach ; https://www.49ers.com/team/coaches-roster/ ; SRC-OFFICIAL)
- Roster: https://www.49ers.com/team/players-roster/ (none shown ; SRC-OFFICIAL ; 2026-10-22)
- Depth chart: https://www.49ers.com/team/depth-chart/ ; Updated as of 10/21/26 ; SRC-OFFICIAL
- Active players in the research: 42

### T27 Rams
- Head coach: Sean McVay (Head Coach ; https://www.therams.com/team/coaches-roster/ ; SRC-OFFICIAL)
- Roster: https://www.therams.com/team/players-roster/ (none shown ; SRC-OFFICIAL ; 2026-10-22)
- Depth chart: https://www.therams.com/team/depth-chart/ ; none shown ; SRC-OFFICIAL
- Active players in the research: 42

### T28 Sea hawks
- Head coach: Mike Macdonald (Head Coach ; https://www.seahawks.com/team/coaches/ ; SRC-OFFICIAL)
- Roster: https://www.seahawks.com/team/players-roster/ (none shown ; SRC-OFFICIAL ; 2026-10-22)
- Depth chart: https://www.seahawks.com/team/depth-chart/ ; none shown ; SRC-OFFICIAL
- Active players in the research: 44

### T29 Buccaneers
- Head coach: Todd Bowles (Head Coach ; https://www.buccaneers.com/team/coaches-roster/ ; SRC-OFFICIAL)
- Roster: https://www.buccaneers.com/team/players-roster/ (none shown ; SRC-OFFICIAL ; 2026-10-22)
- Depth chart: https://www.buccaneers.com/team/depth-chart/ ; none shown ; SRC-OFFICIAL
- Active players in the research: 42

### T30 Falcons
- Head coach: Kevin Stefanski (Head Coach ; https://www.atlantafalcons.com/team/coaches-roster/ ; SRC-OFFICIAL)
- Roster: https://www.atlantafalcons.com/team/players-roster/ (none shown ; SRC-OFFICIAL ; 2026-10-22)
- Depth chart: https://www.atlantafalcons.com/team/depth-chart/ ; none shown ; SRC-OFFICIAL
- Active players in the research: 43

### T31 Panthers
- Head coach: Dave Canales (Head Coach ; https://www.panthers.com/team/coaches/ ; SRC-OFFICIAL)
- Roster: https://www.panthers.com/team/players-roster/ (none shown ; SRC-OFFICIAL ; 2026-10-22)
- Depth chart: https://www.panthers.com/team/depth-chart/ ; none shown ; SRC-OFFICIAL
- Active players in the research: 42

### T32 Saints
- Head coach: Kellen Moore (Head Coach ; https://www.neworleanssaints.com/team/coaches/ ; SRC-OFFICIAL)
- Roster: https://www.neworleanssaints.com/team/players-roster/ (none shown ; SRC-OFFICIAL ; 2026-10-22)
- Depth chart: https://www.neworleanssaints.com/team/depth-chart/ ; none shown ; SRC-OFFICIAL
- Active players in the research: 44

