# NFL_ROSTERS_53_RESEARCH (nfl4 only): the 53-man rosters, practice squads and free agents of 2026-10-24 (NX-B2, NX-B3; D-144, D-145)

Written by hand in the NX-B session (2026-10-24). The first research of the names (coaches and the rosters of 2026-10-22) is spec/NFL_NAMES_RESEARCH.md;
this file records the second one. AGENTS.md rule 0.19, playbook 7.14; facts only (names, positions, numbers, ages).

## 1. What was researched and how

- Date: 2026-10-24, week 8 of the 2026 season. Four research subagents (two divisions each) read each team's own roster page and depth chart page
  (`https://www.<team site>/team/players-roster/`, `/team/depth-chart/`): every player of the active roster, the practice squad and the reserve lists.
  All 32 rosters came from the teams' own sites (SRC-OFFICIAL); the Texans' depth chart is an image, so ESPN's (SRC-SECONDARY) gave its order.
- The fetch tool returns a summary of a page, not its text (as in SX.11); the subagents were told to ask for every row and to re-fetch short tables.
  The active counts the pages showed: 53 for 21 teams, 52 for the Ravens, Dolphins, Patriots, Texans, Titans, Chiefs, Lions, Rams and Falcons,
  51 for the Steelers and the 49ers, 50 for the Eagles and the Packers (each short team was fetched twice with the same count, except the
  Falcons, 49ers and Rams; the 49ers' 51 rows were counted by hand). A real roster may be short in mid-week; the file takes the pages as they were.
- The reports were saved at once into `work/nxb/source_afc_east_north.txt`, `source_afc_south_west.txt`, `source_nfc_east_north.txt`,
  `source_nfc_south_west.txt` (B-X119: a subagent's report lives only in the conversation; the transcript files of these runs were empty). The
  reserve lists (injured reserve, PUP, NFI, suspended) are not part of the 53 and were left out; a name a depth chart gives that is on a reserve
  list or the practice squad was taken out of that chart's rows and noted in the team's COUNT line.
- No "as of" date on any roster page. Depth charts with a date: Bears 10/6/2026 (older than the roster: its LS row named the practice squad's
  long snapper and it listed the injured Cole Kmet; corrected to the roster), Titans 10/20/26, Raiders 10/20/2026, 49ers 10/21/26.
- Notable rows, as the pages show them: the Rams list Aaron Donald as active and Myles Garrett and Davante Adams on injured reserve; the Falcons
  carry four quarterbacks (Penix, Tagovailoa, Dalton, Strand); the Dolphins have no kicker on the active roster (their chart's K and P rows name
  the punter Bradley Pinion), so their practice squad's kicker Zane Gonzalez takes the kicker's line, SX.11's rule; the Eagles' page said Cam
  Jurgens was traded to the Ravens; two players are called Marcus Harris (the Titans' cornerback and the Chiefs' squad tackle): the Franchise
  keeps names unique, so the second is left out of the Chiefs' squad in a new franchise.

## 2. The free agents

- No official NFL list of October 2026 was found; Spotrac's free agents page answered HTTP 402 (not scraped) and Over The Cap's table was empty.
  The backbone is Sharp Football Analysis's best-available tracker (last updated 2026-10-23, names and positions), checked against Pro Football
  Rumors (2026-10-15), CBS Sports (2026-08-18), Yahoo with Spotrac's ages (2026-08-06), FFToday (2026-08-24, quarterbacks) and Bleacher Report
  (2026-07-19). All SRC-SECONDARY. Only Tyreek Hill, Bobby Wagner and Matt Milano were confirmed unsigned by two sources after mid-September; one
  name on the tracker had signed (Cooper Rush, left out), and the kickers and punters of a stale page were left out where they are on rosters.
- The Madden NFL game's lists were not used (the owner allowed them only to find who is a free agent; no rating, art or text of EA is used).
- `work/nxb/make_free_agents.py` leaves out anybody on a team's active roster or practice squad in the new rosters.txt: 155 players remain
  (DL 36, OL 31, S 16, WR 15, CB 15, LB 11, RB 10, TE 9, QB 8, K 3, P 1). Ages are the sources' (August to October), "-" where none was given.

## 3. Terms of use

The team sites are NFL-network sites; spec/NFL_NAMES_RESEARCH.md section 2 records the NFL's terms (personal, non-commercial use; no systematic
retrieval to build a database without consent). No terms text was seen on the pages fetched this time. The files keep facts only. Whether they are
published in the public repository is the owner's decision (Q-040, owner-needed); the shipped files follow D-098 as before. The agent is not a lawyer.

## 4. The files

- `clone/assets/data/rosters.txt` (VERSION season 2026, as of 2026-10-24): 32 teams, 1,678 active players and 545 practice squad players
  (`work/nxb/rosters_report.txt` lists every team's counts and returners).
- `clone/assets/data/free_agents.txt` (VERSION season 2026, as of 2026-10-24): 155 free agents (`work/nxb/free_agents_report.txt`).
- `clone/assets/data/respellings.txt`: R015 Peña => Pena (the Jaguars' squad receiver Trebor Peña), with the four accented names of SX.11.
- A spot-check of names with accents, apostrophes and suffixes against the live pages is left to the first fresh reviewer, as in SX.11.
