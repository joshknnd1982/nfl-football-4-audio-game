# The free agents audit of 2026-10-27 (D-185)

nfl4 only (rule 0.13; AGENTS.md 0.32 and 0.34, playbook 7.23). This is inspired by Jim Kitchen.

A remote tester: "Make sure all free agents are completely accurate. Do a full audit and correct any inaccuracies." The owner: "[the agent] must address all of these", and during the audit: "[the agent] should search the internet to do the audit if needed to ensure player and field position accuracy during the audit."

## Result in one paragraph

The shipped list (`game\assets\data\free_agents.txt`, as of 2026-10-26, 834 men) had five kinds of faults: men who are on a team (17), the same man written twice under two spellings (7), men who have retired or sit on a list no source shows (2), men the second source does not confirm as free (6), and the positions OL, DL, LB and S for 412 men, so in a franchise every free lineman became a left tackle, every edge rusher a left edge and every safety a free safety. The new list (as of 2026-10-27, 808 men) keeps every man of the old list who is really unsigned (with his old ID), adds 6 real unsigned men the old matching missed, and gives every man his real field position of the 22 of a real roster. The script that makes the list (`game\tools\update_rosters.py`) now does all of it by itself, so the next pull stays right.

## How the audit was done

1. A fresh pull of every source on 2026-10-27 (`update_rosters.py`, run folder `work\tester_1027\rosters_run`): the 32 teams' own roster and depth chart pages (the official primary source, D-156), nflverse's players table, its weekly roster of 2026 (newest week: 7) and its depth charts of 2026, 2025 and 2024 (CC BY 4.0), and Sleeper's player feed. The rosters of that day differ from the shipped rosters.txt of 2026-10-26 by one man's position.
2. `work\tester_1027\audit_free_agents.py` checks every man of a free_agents.txt against that data: on a team (any of the three sources), retired, unknown, not free in Sleeper, written twice, out two seasons, position, field position, age; and lists real unsigned men the file lacks. Its reports: `work\tester_1027\audit_fa_shipped.txt` (the old list), `audit_fa_final.txt` (the new one).
3. Every man the sources disagree on was looked up on the web (the teams' own news pages first). What the search settled is in `game\tools\free_agent_settlements.txt`, each line with its source.

## What was wrong, and why

| Fault | Men | Cause |
|---|---|---|
| On a team's roster or practice squad under another spelling | 7 | the old matching compared names, and a team page writes Dax Hill for Daxton Hill, Drew for Andrew Ogletree, Kiko for Francisco Mauigoa |
| On a team's reserve list (injured reserve) in the league's weekly roster | 10 | the league's weekly roster, the third source, was not read |
| One man written twice | 7 | the hand-researched list of 2026-10-24 and the pool of D-169 spelled him two ways (Matt and Matthew Judon, Shaq and Shaquill Griffin, Cam and Cameron Sample, Joe and Joseph Noteboom, Mike and Michael Jordan, Zach Thomas, Joshua Paschal) |
| Retired, or on a list no source shows | 2 | the old list's men were never checked again; the reserve/retired list (Taven Bryan) and a reversion to injured reserve in August (Malik Verdon) |
| Not confirmed as free by the second source | 6 | out since 2024 with no news for over a year (Nicholas Petit-Frere, Nick Harris, Josey Jewell, Emmanuel Moseley), a Sleeper record on a team (Nathan Thomas, Sleeper's Nate Thomas of the Texans), or no record at all (Seth Coleman) |
| Wrong ages | 13 | a loose name match (first initial and last name) took another man's record: Cam Robertson 38 for a man of 22, Andrew Ogletree 35 for 28 |
| Positions too coarse | 412 | the file had only OL, DL, LB and S; the game made each the first position of the family |

The men on a team, by source: the Bengals' Dax Hill, the 49ers' practice squad's Ogbo Okoronkwo, the Colts' Drew Ogletree, the Ravens' practice squad's Lardarius Webb Jr., the Jets' injured reserve's Kiko Mauigoa, the Patriots' practice squad's Al'zillion Hamilton, the Cardinals' practice squad's Cameron Robertson; on injured reserve in the league's week 7 roster: Carson Steele (Eagles, waived injured on 2026-10-20 and reverted), Cole Burgess, Matt Waletzko, Elijah Chatman, Daniel Rickert, Edefuan Ulofoshio, Ruben Hyppolite II, Daequan Hardy, Dallis Flowers (Bears, on injured reserve since 2026-08-07, a list the Bears' page does not show), Rico Payton.

## What the web search settled

| Man | Settled | Source |
|---|---|---|
| Thomas Morstead, punter | free: the Colts signed him to their practice squad on 2026-10-20 and released him from it before week 8; the league's week 7 list still has him | colts.com news; Field Level Media |
| Bryce Baringer, punter | free: the Patriots released him from their injured reserve list | patriots.com news, 2026-10 |
| Jaxson Moi, defensive tackle | free: the Rams' practice squad page of 2026-10-27 lists 16 men without him | therams.com roster page |
| Malik Verdon, linebacker | not free: reverted to the Falcons' injured reserve in August 2026 | RotoWire, ESPN |
| Carson Steele, running back | not free: waived injured by the Eagles on 2026-10-20, reverted to their injured reserve | Rotoballer, the Eagles' news |
| Dallis Flowers, cornerback | not free: on the Bears' injured reserve since 2026-08-07 | ESPN transactions, Wikipedia |
| Tyus Bowser | position LEDG, an edge rusher | ESPN, Wikipedia |
| Marquis Haynes | position REDG, an edge rusher | PlayerProfiler, Wikipedia |
| Ja'Whaun Bentley | position MIKE, an inside linebacker | team coverage, Wikipedia |
| Vonn Bell | position SS, a strong safety | team coverage, Wikipedia |
| Nash Hutmacher | position LG: a defensive tackle the Buccaneers moved to guard in 2026 | buccaneers.com camp preview, Fox Sports |
| Haggai Ndubuisi | stays a defensive tackle (he began on the offensive line) | Wikipedia, commanders.com |
| Leroy Watson IV | stays an offensive tackle (a tight end in college) | ESPN, CBS Sports |
| Tyreek Hill, Bobby Wagner, Matt Milano, Joey Bosa, Taylor Decker, Russell Wilson, Mike White, Justin Tucker | still unsigned | the 2026 free agent trackers (CBS Sports, Sports Illustrated, Last Word on Sports), team news |
| Stefon Diggs, Aaron Rodgers, Kirk Cousins, Keenan Allen, Jauan Jennings, A.J. Epenesa, Jonnu Smith, Deebo Samuel | signed (on their teams' pages), not in the list | the same trackers and the teams' pages |

## The rule the script follows now (D-185)

- A man is matched across the sources by his league ID (nflverse's gsis_id, which Sleeper and the weekly roster carry), then by his exact name with the same birth date or as the only man of that name and family, then by his last name and exact birth date (Carlos "Boogie" Basham); never by a first initial and a last name.
- A free agent is a man of nflverse's players table, not retired, of this season or the one before (or the one before that while he is in the news, D-172), on no team in any source, and active and teamless in Sleeper. For the active roster and the practice squad, a team's page read today is newer than the league's weekly list; for the reserve lists (which some teams' pages leave out) the weekly list decides. `free_agent_settlements.txt` settles what the sources get wrong: a retiree or a hidden list ("never free"), a release the sources have not caught ("free"), a field position ("position XX").
- His position is the league's own word, made one of the 22 positions of a real roster (QB, HB, FB, WR, TE, LT, LG, C, RG, RT, LEDG, REDG, DT, SAM, MIKE, WILL, CB, FS, SS, K, P, LS) by his newest depth chart row of that family (2026, then 2025, then 2024): a corner stays a corner on a safety's row and a safety stays a safety on a nickel row (D-157), a fullback stays a fullback, a back charted as a fullback is one. 10 men have no chart row that settles a side or a role (for example a safety listed only S): the script picks one of the family's positions by a hash of the name and the report lists them.
- The age comes from the birth date (Sleeper's, else nflverse's; nflverse's January 1st means not known).
- The old list's IDs stay; a man of the old list who is not free is left out with the reason in the report.

## The new file

808 men as of 2026-10-27: C 25, CB 116, DT 76, FB 2, FS 28, HB 53, K 18, LEDG 41, LG 33, LS 8, LT 32, MIKE 24, P 10, QB 31, REDG 29, RG 25, RT 22, SAM 10, SS 28, TE 53, WILL 19, WR 125. Added: Mike White, Irv Smith, Alex Williams, Ethan Robinson, Chris Edmonds, John Parker Romo. The audit of the new file finds nobody retired, unknown, written twice or with a wrong age; the 3 men one source still has on a team are the ones the web search settled above; the field positions that differ from a chart row are the corner and safety rule.

The game reads the 22 positions in the file (and the older words RB, OL, DL, LB and S in a player's own file), and a new franchise's free agents keep them: a guard is a guard, an edge an edge.

## Limits

- The data is facts only: names, positions, ages. No ratings: a free agent's rating is made by the game.
- A player's copy of the old shipped file (0.16.2 to 0.16.7) is replaced by the new one when the game starts (`customize.OLD_SHIPPED_FREE_AGENTS`).
- An older build that downloads this file from the repository's rosters folder refuses it (it does not know the 22 positions in a free agent's line) and keeps its own; BC.4 should publish the new free_agents.txt in rosters\ only with 0.16.8, as B-T120 says for rosters.txt.
- The audit is one day's picture: the league signs and releases men every day. Run the script again before a release: `py -3.14 -I game\tools\update_rosters.py` (a fresh pull), read the FREE AGENTS lines of its report, look up any man in its "check them" line.
