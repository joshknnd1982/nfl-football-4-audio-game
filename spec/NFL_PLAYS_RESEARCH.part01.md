# NFL_PLAYS_RESEARCH (nfl4 only): every real NFL play and every Madden NFL playbook concept, for SX.10b

Status: RESEARCH, version 1.0 (2026-10-20, PX session SX.10a). nfl4 only (AGENTS.md rules 0.13 and 0.20; requirements NX-P1 to NX-P7 and NX-R7 in `spec\NFL_EXTRA_FEATURES.md` section 18; decisions D-082, D-083, D-085). No game code was written. Plain headings and lists, no tables.

What this file is for: SX.10b designs the menus (NX-P7) and the outcome models (NX-P3) of every real NFL play and every Madden NFL playbook concept; SX.10c to SX.10e build them. This file gives SX.10b the complete list, what each play needs on the field, the published numbers to calibrate against, the rules that bound the list, the places where the game does not yet follow the 2026 rules (section 7) and the questions SX.10b must decide (section 10).

How it was made: four research passes on 2026-10-20 (offense, defense, special teams and two-point plays, Madden NFL 27's playbooks), each reading web pages only (no data files downloaded); the 2026 Official Playing Rules PDF was read as text on this PC (the fetch tool saved the PDF; the text was taken with pdftotext from MSYS2 and with pypdf 6.21.1, which one pass installed for Python 3.10 with pip, user scope). The raw notes with every detail and every source are in `work\sx10a\notes\` (A_offense.md, B_defense.md, C_special_teams.md, D_madden_concepts.md; not committed, like all of `work\`). This file is the reviewed summary; where it shortens a note, the note is the longer record.

Tags (playbook 5.3, as in NFL_RULES_RESEARCH): SRC-OFFICIAL = the 2026 NFL rulebook (cited as RB26 rule-section-article, PDF page = printed page + 7), operations.nfl.com, nfl.com and NFL Next Gen Stats (the NFL's own tracking, cited NGS), or for Madden facts an EA page; SRC-SECONDARY = a named other source (PFF, Sharp Football Analysis, ESPN, The 33rd Team, RotoWire, Fox Sports, Sports Info Solutions, MatchQuarters, madden.tools, Wikipedia and so on); UNVERIFIED = not found in a readable source (football knowledge, a reading, or an inference from a play's name). Every number below names its season and source. "Search summary" means the page itself could not be read and only a search result's summary was seen: weaker.

Names (NX-R6, D-083): every play here is a football concept in plain football words. Nothing of EA's play lists, formation strings, art, ratings or exact layouts is copied; a Madden play name appears at most as a short example to identify a concept. Section 6.4 adds to the list of EA names the game must not use. Madden NFL is a trademark of Electronic Arts; this game is not made or endorsed by EA or the NFL.

## 0. Answers in brief

1. The whole list (sections 2 to 6): offense about 150 named plays and formations in eight groups (formations and personnel, runs, quarterback runs and options, run-pass options, quick passes, intermediate and deep passes, screens, play-action and moving pocket, trick plays, clock and situation plays); defense 58 entries (16 fronts and personnel groups, 15 coverages, 15 pressure kinds, 5 run-defense ideas, 7 situation defenses) and 12 rules that limit a defense; special teams 33 entries (kick-offs, punts, field goals and tries, fakes, returns and blocks); two-point plays. Madden NFL 27's playbooks hold 167 concept lines (99 offensive concepts, 38 defensive, 21 special teams, 8 pre-snap tools); every one of them is inside the NFL list, except a handful of names that only Madden uses for a known concept (section 6).
2. The scale: Madden's whole pool is 10,694 plays in 34 formation families (offense 18 families, 435 sets, 9,007 plays; defense 16 families, 96 sets, 1,687 plays) (SRC-SECONDARY, madden.tools, read 2026-10-20). Those plays are combinations of a formation, a set and a concept; the distinct concepts are about 100 on offense and about 40 on defense. A team book is a selection of a few hundred (no EA figure; a fan post says books grew by about 30 percent over Madden 26). So "every play" for a spoken game means every CONCEPT, with formation, side and personnel as cheap modifiers (section 10, Q-P2).
3. The game today (SX.7) has 52 offense plays (O001 to O052) and 30 defense plays (D001 to D030), each a bounded change of one of the original's families. About 100 more offensive concepts, about 50 defensive ones and every special-teams play are missing (section 9).
4. The published numbers (section 8): league passing 2024 completion 65.3 percent, 7.13 yards per attempt, interceptions 2.17 percent, sacks 6.87 percent of dropbacks, 4.44 yards per carry (RotoWire); run concepts by yards per carry (PFF 2020 to 2022); play-action 25.65 percent of plays in 2025 at 7.76 yards per attempt against 6.72 (PFF); screens 11.0 percent of dropbacks at 86 percent completion (PFF 2024); coverage shares from Next Gen Stats 2025 (two-high 42.0 percent, Cover 2 13.9, Cover 4 17.2, Cover 6 9.2); blitz rate about 33 percent and 42.3 percent pressure on blitzes (PFF 2025); field goals by distance and extra points (ESPN 2025: 85.6 and 95.9 percent); punts (ESPN 2025: gross 47.15, 42.7 percent returned); two-point tries (46 percent in 2025, 41 in 2024).
5. The rules (section 1): the legal limits of formations, motion, passes, laterals, the spike and the kneel; what defenses and kick teams may not do. The tush push (the sneak with teammates pushing) is still legal in 2026: the 2025 ban failed 22 to 10 and nothing about it is in the 2026 changes (SRC-OFFICIAL, nfl.com). Wedge blocks on free kicks are never legal (RB26 6-2-1 Item 2(d)).
6. The game does not yet follow the 2026 rules in 14 places (section 7, G26-1 to G26-14; requirement NX-R7, D-085): the kick-off, the onside question, overtime, the extra point, punts, field goal odds, the missed field goal's spot, turnovers, fumble recoveries, the two-point try, the safety kick, the kneel and spike, the fair catch kick and the fouls of the new kicks.
7. How a blind player reaches hundreds of plays as quickly as the original's eight (NX-P7): section 10 Q-P1 lays out the measure (keys and spoken words to the snap) and five ways that keep the original's two keys for the usual call; the recommendation is that the original's items stay first and Enter on them calls the playbook's pick of that family, with the full list one level down by group, a favourites list, "the same play again" and a type-to-find.
8. Nothing here needs the owner now. One item needs the owner's yes in SX.10b: downloading public play-by-play and charting data to compute per-concept numbers the pages do not publish (Q-P15).

## 1. Rules that bound every play (2026 rulebook, SRC-OFFICIAL unless marked)

Offense:
- At the snap at least seven players on the line; the players on both ends of the line are eligible receivers and every player between them is ineligible (RB26 7-5-1(a), (b), PDF 35). Illegal formation: 5 yards.
- Eligible numbers 0 to 49 and 80 to 89 (RB26 5-3-1, 8-1-5(b)); the operations "football terms" page says 1 to 49; the rulebook controls. A player with an ineligible number may report as eligible (a "tackle eligible" or an unbalanced line), and the referee tells the defense (RB26 5-3-1, 5-3-2). Failing to report: illegal substitution, 5 yards.
- A shift (two or more players moving) needs a one-second stop of everyone before the snap; one backfield player may be in motion at the snap, parallel to or away from the line, never toward it; a T-formation quarterback in motion must stop for one second (RB26 7-4-7, 7-4-8, 3-42). Illegal shift or motion: 5 yards.
- The snap is a backward pass; a snap that hits the ground may be recovered and advanced by anyone (RB26 7-6-4).
- One forward pass a down, thrown from behind the line; a second one, or one thrown from beyond the line, or after the ball crossed the line and came back, is loss of down and 5 yards (RB26 8-1-2). Laterals (backward passes) are legal at any time, any number (RB26 8-7-1). A deliberate forward fumble counts as a forward pass (RB26 8-1-1(c)). A forward hand-off only to an eligible player behind the line (RB26 8-7-4).
- Ineligible players may not be more than one yard downfield before a forward pass is thrown (RB26 8-3-1, 5 yards); this is the NFL limit that shapes every run-pass option (college allows more; never copy the college limit).
- Intentional grounding: loss of down and 10 yards or the spot; a safety from the end zone; not grounding when the passer is outside the pocket and the ball reaches the line; the legal spike is a T-formation quarterback throwing the ball into the ground at once after the snap; a delayed spike is grounding (RB26 8-2-1 Items 1, 3, 4).
- The kneel: the ball is dead when the quarterback drops, or pretends to drop, to a knee (RB26 7-2-1(c)).
- On fourth down, after the two-minute warning and on a try, only the player who fumbled may recover and advance the offense's fumble (RB26 8-7-5, 8-7-6): this governs every lateral, flea flicker and double pass late in a half.
- Pulling a runner and interlocking interference are 10-yard fouls; pushing the runner is not listed, which is why the push sneak is legal (RB26 12-1-4; the reading is the research's). The 2025 proposal to ban the push failed 22 to 10 (24 needed) (SRC-OFFICIAL nfl.com; vote count SRC-SECONDARY Fox Sports); in 2026 no ban was proposed (SRC-OFFICIAL nfl.com, Rich McKay; the 2026 approved changes have nothing on it).
- Chop blocks, illegal crackbacks and peel-back blocks are fouls (RB26 12-2-2, 12-2-5, 12-2-6).
- 2026 changes (approved 2026-03-31): the kick-off setup-zone alignment, the dead-ball spot after a touchback of a kick-off from the 50, the onside kick at any time, a replay-assisted disqualification review; nothing on formations, motion, sneaks or passes (SRC-OFFICIAL, NFL media site and RB26).

Defense:
- Eleven players; more than eleven in the formation or at the snap is 5 yards (RB26 5-1-1). No rule limits how many linemen, linebackers or backs a defense uses, so every front and package below is legal; the only formation limits are on kicks (next list).
- Offside, encroachment, neutral zone infraction: 5 yards, no automatic first down (RB26 7-4-3 to 7-4-5).
- Illegal contact: a defender may chuck a receiver within five yards of the line; beyond five yards, while the quarterback is in the pocket with the ball, no contact that hinders the receiver: 5 yards and an automatic first down (RB26 8-4). Defensive holding: 5 yards and a first down (RB26 8-4-6, 12-1-6). Illegal use of hands: 5 yards and a first down (RB26 12-1-7).
- Defensive pass interference: a spot foul with an automatic first down; in the end zone the ball goes to the 1 (or halfway when the previous spot was inside the 2) (RB26 8-5, 8-6-1(b)).
- Roughing the passer, unnecessary roughness, the horse-collar and the hip-drop tackle: 15 yards and a first down (RB26 12-2).
- Words or acts meant to disconcert the offense at the snap: 15 yards (RB26 12-3-1(i)).

Kicks:
- A punt, drop kick or place kick from beyond the line: loss of down and 5 yards (RB26 9-1-1). On a scrimmage kick only the end men and eligible players wide of them may go downfield before the kick (RB26 9-1-2, 5 yards: the gunners).
- Against a punt or field-goal formation a defender within a yard of the line must be wholly outside the snapper's shoulder pads, and at most six defenders on the line on either side of the snapper against a field goal or try; pushing a teammate into the formation is 15 yards (RB26 9-1-3).
- Leaping over the line to block a kick unless stationary within a yard of the line at the snap, standing on or lifting a teammate, using a teammate for leverage: 15 yards (RB26 12-3-1(o) to (r)). Running into the kicker 5 yards, roughing the kicker or holder 15 and a first down (RB26 12-2-12, 12-2-13).
- No tee for a field goal or try (RB26 11-4-4); a tee only for free kicks.
- Free kicks: a wedge (two or more players shoulder to shoulder within two yards moving forward together) is never legal, 15 yards; a double-team block only by players who started in the setup zone (RB26 6-2-1 Item 2(c), (d)). The 2026 kick-off alignment, landing zone, touchback spots and onside rules are in NFL_RULES_RESEARCH Part 5 (6-1, 6-2).
- Fair catch: a signal, then the ball is dead on the catch, no contact (15 yards); interference by the kickers 15 yards; after a fair catch the receivers may snap or try a fair catch kick (RB26 10-1, 10-2).

## 2. Offense

Each entry: what it is (in this file's own words); the people it needs; published numbers; the question it raises for SX.10b (the Q-P numbers of section 10, or a short question).

### 2.1 Formations and personnel

Personnel is named by two digits: running backs (a fullback counts) then tight ends; receivers are the rest of the five skill players. 11 = one back, one tight end, three receivers; 12 = one back, two tight ends, two receivers; 21, 22, 13, 10, 20, 23, 01, 00 likewise (SRC-SECONDARY, Sharp, gorout).
- Usage: 11 personnel about 56 to 57 percent of plays in 2025 (SRC-SECONDARY, SumerSports data via JetsXFactor; two pieces differ by method); plays with two or more tight ends 33 percent in 2025, 30 in 2024 (SRC-SECONDARY, Sharp via search summary); 2026 to about week 3: 11 about 57, 12 about 24, 13 about 8, 21 about 7, 22 about 3 percent (SRC-SECONDARY, Sharp, the research's unweighted average, early). Pass rate by group in 2017: 11 72 percent, 12 52, 13 33 (SRC-SECONDARY, PFF). 21 personnel fell from 23 percent of plays in 2008 to 8 in 2017 (SRC-SECONDARY, PFF).
- Where the quarterback stands: under center 35 percent of plays in 2025 (30.5 in 2024, 29 in 2023; about 42 in the first weeks of 2026) (SRC-SECONDARY, ESPN's Barnwell via ABC7; Sportradar 34.7 for 2025); shotgun 62.3 percent and pistol 7.4 percent in 2024 (SRC-SECONDARY, RotoWire). Play-action is used on more than 75 percent of under-center dropbacks against 9.5 percent from the gun (week 1 of 2026, ESPN via ABC7).

Formations (backfield):
- Under center (T formation): the quarterback takes the snap from the center's hands. Question: a formation choice or a hidden tag of the play (Q-P2)?
- Shotgun: the quarterback about five yards back. Pistol: the quarterback about three or four yards back with a back behind him (distance UNVERIFIED).
- I formation (pro, strong, weak, offset): fullback and tailback in a line behind the quarterback, the fullback moved to the strong or weak side or offset; 21 or 22 personnel (SRC-SECONDARY, Wikipedia; the variant names coaching usage, UNVERIFIED). Power I and the "Maryland I" (three backs stacked) are heavy versions (SRC-SECONDARY, madden.tools).
- Singleback (ace): one back about five yards behind the quarterback, no fullback (SRC-SECONDARY, Wikipedia).
- Split backs (pro set): two backs side by side behind the quarterback (SRC-SECONDARY, Wikipedia). Near and far: two-back sets with the second back offset toward or away from the strength (SRC-SECONDARY, madden.tools; the meaning of the names UNVERIFIED).
- Full house, wishbone, flexbone, wing T, split T, single wing: three-back and option formations; legal, rare or never seen in today's NFL (SRC-SECONDARY, Wikipedia; the wishbone used by the 49ers once in 1987). Question: keep only as rare named plays (Q-P5).
- Wildcat: a back takes a direct snap in the gun, the quarterback lines up wide or leaves; 237 plays in 2008, 305 in 2009, 89 of 33,076 snaps in 2020 (SRC-SECONDARY, The Analyst).
- Goal line and short yardage: three or more tight ends, one or two backs (23, 22, 13 personnel) (SRC-SECONDARY, gorout).
- Empty (five wide): no back next to the quarterback; empty dropbacks about 14 percent of dropbacks in 2020 (SRC-SECONDARY, Sports Info Solutions via Sharp, search summary; no 2025 figure). Question: a higher sack chance with no back to block (Q-P4).

Receiver sets (the "set" level of a playbook): trips (three receivers to one side), bunch (three tight together, for rubs), stack (one directly behind another), doubles or two by two, twins, quads, spread, tight or wing alignments (SRC-SECONDARY, Wikipedia; bunch, stack, quads UNVERIFIED as definitions). Unbalanced lines and a tackle reported eligible are legal with the report (RB26 5-3-1).

Motion and shifts: the NFL tracks shifts and motions and in 2025 listed 19 motion types, among them jet, orbit, fly, glide and exit (SRC-OFFICIAL, NGS 2025). Jet motion runs across the formation at the snap; orbit loops behind the quarterback; return motion goes and comes back (SRC-SECONDARY, Viqtory via search summary; orbit UNVERIFIED). Shifts or motion on 63.9 percent of plays in 2025 (61.5 in 2024); EPA a play with motion +0.002 against -0.042 without, with shifts -0.070 against -0.014 without (SRC-SECONDARY, PFF): motion helps a little, shifts show no gain. Question: one switch for motion (none, jet, orbit) with a small model effect, or a hidden part of some plays (Q-P6)?

Questions for this group: whether the player picks a formation before the play (the real order and Madden's) or the play carries its formation (Q-P2); how personnel is said (plain words such as "three receivers, one tight end" rather than "eleven personnel", Q-P3).

### 2.2 Runs

League: 4.44 yards per carry in 2024, 4.20 in 2023, 4.46 in 2022; 27.0 rushes per team game in 2024; called run rate 43.4 percent in 2024 (SRC-SECONDARY, RotoWire). By concept, yards per carry 2020 to 2022: inside zone 3.90, outside zone 3.78, duo 3.71, power 4.53, counter 3.90, pull lead 3.85, draw 5.95 (SRC-SECONDARY, PFF); 2021 to 2024: inside zone 4.15 with 44.0 percent stuffed, outside zone 4.26 with 49.5 percent stuffed, gap runs 4.48 with 44.6 percent stuffed (SRC-SECONDARY, Fantasy Points via search summary). Shares: outside zone 27 percent of all runs in 2025, the most since 2014; only 918 power concepts in 2025; inside plus outside zone about half of runs, duo 16.3 percent, draws 3.0 percent (84 percent of draws on first or second down) in 2022 (SRC-SECONDARY, PFF). The two sources disagree on zone against gap: the period and the grouping differ. Hand-offs only to an eligible player behind the line (RB26 8-7-4).

Zone runs (the line blocks areas, the back reads):
- Inside zone: downhill between the tackles, the back reads the first gap and may cut back. 11, 12, 21 personnel; the tailback carries.
- Outside zone, stretch, wide zone: the line steps to the sideline, the back presses the edge and makes one cut; the most common run of 2025.
- Mid zone: between the two (SRC-SECONDARY, madden.tools names).
- Split zone: zone blocking with a tight end or back crossing the formation to block the backside end.
- Lead zone, wham (a tight end or back blocks a defensive tackle from inside), belly (a flatter path inside the tackle): variants (UNVERIFIED definitions).

Gap runs (blockers have men, linemen pull):
- Duo: double teams, no puller, the back reads the middle linebacker.
- Power: a backside guard pulls to the play side, often with a lead back.
- Counter (guard and tackle, or guard and fullback, pull; the back's first step goes the other way), counter trey (the tight end kicked out; naming UNVERIFIED).
- Trap: a defensive lineman is let through and blocked from the side by a pulling guard; a quick hand-off.
- Iso (a fullback isolates a linebacker), lead or blast (a back leads through the hole), dive (a quick hand-off straight ahead), fullback dive and fullback trap: two-back plays (21, 22).
- Draw and delayed draw: a pass look, linemen pass-block, then the hand-off; the best yards per carry of any concept but rare.
- Off tackle, slash, cutback and misdirection runs: short variants by the back's path (SRC-SECONDARY, madden.tools names).

Perimeter runs:
- Toss and pitch sweep, quick toss, crack toss (a receiver blocks back on a linebacker), pin and pull or buck sweep (two linemen pull around the end) (SRC-OFFICIAL for the pitch, NFL terms; the variants UNVERIFIED).
- Jet sweep: a receiver in jet motion takes a hand-off or a flip at full speed (the motion rule RB26 7-4-8).
- End around (a receiver takes the ball and runs the other way), reverse and fake reverse (a hand-off to a teammate going the opposite way) (SRC-SECONDARY, gorout).
No published yards by direction or by gap were found. Question for all runs: which concepts need their own outcome model, which share one with a small change (Q-P7).

### 2.3 Quarterback runs and options

- Quarterback sneak: the quarterback dives behind the center on short yardage; first down on 75.8 percent of sneaks in 2025 (SRC-SECONDARY, PFF); other filters give 84.2 to 84.8 percent for third or fourth and 1 since 2022 (CBS, ABC7 via search summary). The game already has it (O046) with D-052's numbers.
- The push sneak: the same with teammates pushing from behind; legal in 2026 (section 1); the best-known team's first-down rate fell from 88.1 percent (2022) to 65.5 (2025) (SRC-SECONDARY, PFF). Madden has it in six team books only (SRC-OFFICIAL, EA Week 1). The game has it (O051, "Sneak Push"; EA's name is not used).
- Quarterback power, quarterback counter, quarterback draw, quarterback zone, quarterback crack sweep: designed keepers behind pulling or zone blocks (PFF counts the quarterback draw as a draw; the rest UNVERIFIED definitions). No league rate of designed quarterback runs was found; one team's designed runs a game fell from 4.1 to 2.2 between 2019 and 2024 (SRC-SECONDARY, Fantasy Points via search summary); NFL_RULES_RESEARCH Part 9 has the league counts (1.29 designed and 1.97 scrambles per team game in 2024 and 2025).
- Read option (zone read): the quarterback reads an unblocked end and hands off or keeps. Speed option (the quarterback runs wide with a pitch man and reads the edge). Triple option (dive, keep or pitch), midline option (the quarterback reads a tackle), inside veer, inverted veer, power read, power option, an option with a receiver or tight end as the pitch man: the option family, mostly college, rare in the NFL (UNVERIFIED rates; the shapes from Wikipedia and madden.tools names).
- Scramble: not a call; the quarterback leaves the pocket under pressure (the game models it since SX.5).

### 2.4 Run-pass options (RPO)

A designed run with a quick throw the quarterback takes when one chosen defender commits. 7.95 percent of plays in 2025, 8.96 in 2024, 10.52 in 2023 (the peak); 2021 to 2025: 4.53 yards a play and 52.3 percent success against 5.43 and 48.1 for other plays; about three quarters end as runs; RPO runs 4.56 yards against 4.39 for other runs in 2025; used on 9.0 percent of early downs, 5.0 of third downs, 3.1 of fourth downs (SRC-SECONDARY, PFF). Kinds: the throw is a bubble screen, a slant or glance, a quick flat, a stick, a wheel or a tight-end route; an RPO off jet motion; an "alert" throw added to a run (SRC-SECONDARY, civil.gg and games.gg guides; the alert shape UNVERIFIED). The one-yard ineligible limit applies (RB26 8-3-1). The game has one RPO (O030). Question: the throw or hand-off decided by a rule (the defender's choice drawn) or by the player (Q-P8).

### 2.5 Passes

League 2024: completion 65.29 percent, 7.13 yards per attempt, interceptions 2.17 percent of attempts, sacks 6.87 percent of dropbacks, average depth of target 7.65 yards, 32.7 attempts per team game; 2023: 64.47, 7.02, 2.35, 7.15; 2022: 64.23, 7.03, 2.31, 6.70 (SRC-SECONDARY, RotoWire). PFF measures the average depth near 8.2 yards (another definition). Time to throw 2.86 seconds in 2025, the longest in PFF's records (SRC-SECONDARY, PFF). Deep passes (20 or more air yards): under 12 percent of attempts for six years; completed 39.6 percent in 2025 (PFF) or 36.6 (Sharp); a turnover-worthy throw on 7.6 percent; deep crosses completed 54.9 percent, deep seams 47.1, deep corners under 38 (SRC-SECONDARY, PFF). Completion by depth band (behind the line, 0 to 9, 10 to 19, 20 or more) was NOT found published; one study estimated about 71 percent for a 4-yard throw and 60 for a 9-yard throw (SRC-SECONDARY, SumerSports via search summary). Hail Mary passes: 16 touchdowns and 50 interceptions in 193 attempts from 2009 (ESPN; about one in 12); a completion of about 9.7 percent in another count (FiveThirtyEight via search summary).

Route words: the NFL's own flag-football sheet numbers the route tree flat 1, slant 2, comeback 3, hook 4, out 5, in 6, corner 7, post 8, fade 9 and defines levels, mesh, flood and spacing (SRC-OFFICIAL, NFL Flag training sheet).

Quick game (the ball out in about two and a half seconds, 0 to 7 air yards):
- Slants and double slants; slant-flat; stick (a 5-yard hitch with a quick flat); snag or spot (a triangle: a short sit, a corner, a flat); spacing (receivers spread at one depth, defined by the NFL flag sheet); hitch and all hitches; quick out and speed out; curl-flat; fade and back-shoulder fade; quick screens (2.6). Two or three routes each; passes inside three seconds averaged 6.29 to 6.60 yards per attempt in 2023 and early 2024 (SRC-SECONDARY, The Analyst).
Intermediate (8 to 19 air yards):
- Dig or square in; levels (two in-breaking routes at different depths, NFL flag sheet); mesh (two shallow crossers that rub defenders, NFL flag sheet); shallow cross and drag; drive (a shallow cross under a dig); Y-cross (the tight end crosses at 10 to 12 yards); flood or sail (three levels to one side, NFL flag sheet); smash (a corner over a hitch); curl, comeback, out and deep out; option or choice route (the receiver breaks in or out by the defender); dagger (a deep dig behind a seam that clears), follow and hank (UNVERIFIED definitions); bench, whip and return routes (SRC-SECONDARY, madden.tools names and games.gg).
Deep (20 or more):
- Four verticals; post; corner and post-corner; go, fly or nine; seam; deep cross; double posts, post-wheel, mills and yankee (two-route deep combinations, UNVERIFIED definitions); divide and scissors (two deep routes splitting or crossing the middle); double moves (sluggo = slant and go, stutter-go = hitch and go, out-and-up, zig); Hail Mary.
Backs and tight ends: angle, wheel, swing, flat, Texas (an angle-like inside break, UNVERIFIED), check-down, leak (a late release to the flat after a fake).

Question: how many pass concepts need their own model; the published numbers exist only by depth and for a few concepts (deep cross, seam, corner), so most concepts share a depth model with small differences against coverages (Q-P7, Q-P9).

### 2.6 Screens

Running-back screen (slip, swing or flare screen), receiver screen, bubble (to the slot with blockers), tunnel (the receiver comes back inside behind blockers), jailbreak (linemen release to the perimeter for a receiver), middle screen, tight-end screen, fullback screen, double screen, shovel pass (a short underhand forward toss) (SRC-SECONDARY, gorout and Wikipedia via search summary; the mechanics of the tight-end and middle screens UNVERIFIED). League: 11.0 percent of dropbacks in 2024 at 86.0 percent completion against 62.5 for other passes, -0.08 EPA a play (the same as designed runs) against +0.05 for other dropbacks; 2025 screen attempts 1,881, the fewest since 2018 (SRC-SECONDARY, PFF). The game has five screens (O017 to O021).

### 2.7 Play-action, bootlegs and the moving pocket

Play-action (a run fake, then a pass): 25.65 percent of plays in 2025 (24.94 in 2024); 7.76 yards per attempt against 6.72 without; EPA +0.054 a play against -0.031; teams from 17.1 to 34.4 percent (SRC-SECONDARY, PFF). Under-center dropbacks since 2021 gained 0.11 EPA against 0.04 from the gun, most of it from play-action (SRC-SECONDARY, Barnwell via ABC7). No league sack rate with and without play-action was found. Kinds: the play-action shot (deep after the fake), play-action crossers, play-action flood, wheel and divide, a deep post, corner, comeback or dig behind the fake, a back or tight end leaking to the flat, a screen behind the fake; the fake matches the run (zone, power, jet) (SRC-SECONDARY, madden.tools names; EA names play-action crossers, SRC-OFFICIAL).
Bootleg (the quarterback rolls away after the fake), naked bootleg (no blocker on the edge), waggle (a guard pulls to protect), rollout (the line slides with him), sprint out, moving pocket, max protect (extra blockers, fewer routes) (SRC-SECONDARY, coaching sites via search summary; max protect UNVERIFIED). Bootleg success fell about 14 percent in early 2024, 4.34 yards a play (SRC-SECONDARY, The Analyst); an older count: 0.9 percent interceptions and 3.5 percent sacks on bootlegs in 2020 (Sharp via search summary). A passer outside the pocket may throw the ball away past the line without grounding (RB26 8-2-1 Item 1). Question: play-action shares its pass model with the twin without the fake plus a fake bonus (Q-P9).

### 2.8 Trick plays

Flea flicker; halfback pass; receiver or double pass (a lateral first, then the forward pass; a second forward pass would be illegal); the tight-end throw back to the quarterback (the famous Super Bowl LII shape; the game says it in plain words, never EA's name); hook and lateral; statue of liberty (a fake pass, then a hand-off behind the back); the fumblerooski (a ball left on the ground for a lineman: a snap that hits the ground may be advanced by anyone, an intentional forward fumble is a forward pass, so it is legal only in some forms, UNVERIFIED as a ruling); fake spike; fake kneel; wildcat direct snap; jet touch pass; fake sneak to a swing; multiple laterals at the end of a game (legal, all backward) (SRC-SECONDARY, gorout; the rules RB26 8-1-2, 8-7-1, 7-6-4, 8-1-1(c)). No published rates. EA says one team book holds a double pass (SRC-OFFICIAL). Question: a separate group with its own risk (a fumble on a lateral, an interception, the fourth-down fumble rule) and rare use by the computer (Q-P10).

### 2.9 Clock and situation plays

- Kneel (victory formation): ends the down at once; recorded as a rush; the clock runs (RB26 7-2-1(c)). Not in the game's menus (G26-12).
- Spike: legal only at once after the snap by a T-formation quarterback, costs a down, stops the clock (RB26 8-2-1 Item 3). Not in the game's menus (G26-12).
- No-huddle and hurry-up: 9.91 percent of plays in 2025, 12.06 in 2024 (SRC-SECONDARY, PFF); the game's clock (design section 5) has a tempo; question whether the player can choose no-huddle (Q-P11).
- Two-minute and end-of-half plays, goal-line and short-yardage packages, the Hail Mary.
- Fourth down: converted 55.2 percent in 2025, about 56 to 57 in 2024 (SRC-SECONDARY, AOL and Fox via search summary).

### 2.10 Not legal or not used (left out)

Fewer than seven on the line; two in motion or motion toward the line at the snap; a second forward pass or one from beyond the line; a forward hand-off beyond the line or to an ineligible player; a lineman more than a yard downfield on a pass; a delayed spike; pulling a runner, chop blocks, crackbacks, peel-backs (all SRC-OFFICIAL, section 1). The college rule that lets linemen go further downfield on run-pass options does not apply. Wing T, flexbone, single wing and the triple option are legal but practically unused; the wildcat nearly gone (SRC-SECONDARY).

## 3. Defense

### 3.1 Fronts and personnel

Personnel share of defensive snaps: base 29.6 percent in 2025 (23.3 in 2024), nickel about 59.0 (65.2), dime about 9.4 (9.9) (SRC-SECONDARY, PFF via search summary; MatchQuarters similar). One team used base on 61.6 percent; another dime on 30.6 percent (SRC-SECONDARY, PFF 2025). Blitz rate by package 2025: base 30.2, nickel 29.6, dime 22.6 percent (SRC-SECONDARY, PFF).
- 4-3 (four linemen, three linebackers: sam, mike, will; SRC-OFFICIAL, NFL terms), over and under (the three-technique tackle to the strong or the open side), even and odd versions.
- 3-4 (a nose tackle, two ends, four linebackers; SRC-OFFICIAL for the nose in a 3-4), odd and "okie" (a zero nose with two five-technique ends; the label disputed).
- Tite or mint front (a zero nose with two 4i tackles, holding the B gaps; mint from nickel personnel) (SRC-SECONDARY, USA Football).
- 46 and bear fronts (eight near the line, the line shifted, one deep safety; the bear front covers the center and both guards) (SRC-SECONDARY, Wikipedia; the names used loosely).
- 5-2, 6-1, 6-2, 5-3 and 4-4 (heavy and goal-line fronts; the 6-2 and 5-3 historic base defenses) (SRC-SECONDARY, Wikipedia and MatchQuarters; modern use UNVERIFIED); wide nine (an end aligned very wide to rush the edge) (SRC-SECONDARY, CBS Chicago).
- Nickel: five defensive backs, as 4-2-5 or 3-3-5 (SRC-OFFICIAL for the nickel back, NFL terms); big nickel (the fifth back a safety; definition UNVERIFIED); 2-4-5 (UNVERIFIED definition).
- Dime: six defensive backs, as 4-1-6 or 3-2-6. Dollar and quarter: the sources disagree (Wikipedia: quarter 7 backs, half-dollar 8, dollar 9; coaching sites and Madden use dollar for six backs with walked-up linebackers, quarter for seven). The game must say what it means, not rely on the word (Q-P12).
- Prevent: three or four linemen, seven backs deep and soft (SRC-SECONDARY, Wikipedia).
- Goal line: 6-2, 5-3, 5-2 shapes with gap-assigned run stops (SRC-SECONDARY, madden.tools). The game has three goal-line plays (D001 to D003).
- Question: does the player choose the personnel, or does the game match it to the offense with an override (Q-P13)?

### 3.2 Coverages

Next Gen Stats 2025 (SRC-OFFICIAL, nfl.com, published 2026-02-18): two-high safeties on 42.0 percent of pass plays (32.9 in 2018, 40.4 in 2024); Cover 2 13.9 percent, Cover 4 17.2, Cover 6 9.2; average safety depth 12.0 yards; first downs on 29.0 percent of dropbacks against two-high; blitzes on 10.0 percent of two-high plays and 39.7 percent of the others. Secondary: 2023 single-high 53.4, two-high 42.1, man 28.4 and zone 71.6, Cover 1 22.2, Cover 2 12.7, Cover 3 31.1, Cover 4 17.5, Cover 6 9.8 percent (RotoWire); man coverage 22.6 percent of snaps in 2025 (PFF); yards per dropback since 2020: Cover 0 4.76, Cover 2 man 5.19, Cover 4 5.94, Cover 1 5.98, Cover 2 6.27, Cover 3 6.66, Cover 6 6.69, zone 6.39, man 5.76 (The 33rd Team; its Cover 6 share of 3.24 differs from NGS by classification: do not mix the two sources).
- Cover 0: man on every receiver, no deep safety, almost always with a blitz (blitz on about 90 percent outside the red zone, 62 inside; NGS via a search summary); 2.5 to 4 percent of dropbacks.
- Cover 1 (man free; robber or rat variants with a defender sitting underneath to jump crossers): 22 to 26 percent.
- Cover 2 zone (two deep halves, five underneath; SRC-OFFICIAL definition, NGS); Tampa 2 (the middle linebacker runs deep down the middle); 2-man (man underneath, two deep).
- Cover 3 (three deep thirds) with its force variants sky (a safety takes the run force), cloud (a corner), buzz (a safety to a hook zone) and match: 30 to 32 percent, the most common.
- Cover 4 or quarters, match quarters (zone that turns into man by route rules); Cover 6 (quarters to one side, halves to the other; SRC-OFFICIAL definition, NGS).
- Palms or 2-read, Cover 9 and other split-field checks: found only in playbook listings (UNVERIFIED as NFL terms; Madden uses some as play names).
- Press man and off man; bracket and double coverage on one receiver; man with three deep; roll coverage toward a receiver or a side; prevent deep zone; red-zone coverages; disguise (show two-high and rotate to one-high, a tracked NGS metric from 2025, SRC-OFFICIAL, no numbers).
- Question: is the coverage one pick and the pressure another, or one combined call as in Madden (Q-P14)?

### 3.3 Pressure

Blitz rate about 33 percent of pass plays for several years; pressure on 42.3 percent of blitzes in 2025, the most since 2017; pressure rate per rush snap 2025: edge 11.8, interior 7.8, off-ball linebacker 18.3 percent (SRC-SECONDARY, PFF). Split-safety blitzes league-wide 2019 to 2025: 41.3 percent pressure, 66.4 percent completion allowed (SRC-OFFICIAL, NGS article). Team pass-rush win rates 29 to 46 percent, run-stop win rates 26 to 34 percent in 2025 (SRC-SECONDARY, ESPN). Not found: league sack rate in 2025, completion and yards when blitzed against not blitzed, three-man and four-man rush shares.
- Four-man rush (the usual); three-man rush and drop eight (56.5 percent of Hail Mary defenses rush three or fewer, ESPN).
- Blitz (five or more rushers): linebacker blitzes (mike, will, sam), A-gap and double A-gap (two linebackers walked up over the center gaps), edge, nickel or dime back, safety (strong, free, double), corner, defensive back fire off the edge, overload (more rushers to one side), delayed blitz, cross blitz, free fire, run blitz (SRC-SECONDARY, Wikipedia and madden.tools names; overload, delayed and cross UNVERIFIED definitions).
- Zone blitz and fire zone (a lineman drops, a back or linebacker rushes; three deep, three under) (SRC-SECONDARY, Wikipedia; fire zone UNVERIFIED definition).
- Simulated pressure (shows five or six, rushes four, Cover 1 or three-deep behind) and the creeper (a fourth rusher from the second or third level with no pre-snap show) (SRC-SECONDARY, Silver and Black Pride, Buckeye Huddle).
- Stunts, twists, loops and pinch (two linemen cross; the tackles squeeze inside) (UNVERIFIED rates).
- Spy on the quarterback, contain rush, quarterback contain on options.

### 3.4 Run defense

One-gap and two-gap control; run fits; eight or more in the box (a stacked box: SRC-OFFICIAL definition, NGS 2016); slant and angle calls; spill or box (force the runner out or keep him in); the quarterback and pitch assignments against options. No league yards per carry by box count was found (only individual backs in 2016). Rushing touchdowns 2025: 28.6 percent from the 1, 53.5 inside the 5, 73.1 inside the 10 (SRC-SECONDARY, Sharp). Question: the game sets its own box model and records it as a game choice (Q-P7).

### 3.5 Situation defenses

Goal line and short yardage; two-minute (the last-two-minutes neutral zone rule, RB26 7-4-4(c)); prevent; Hail Mary defense (knock the ball down; many backs deep); the kneel (no foul for unavoidable contact if the quarterback does not kneel at once, RB26 7-2-1(c) note); the two-point try (section 5). Question: automatic by the situation or the player's call (Q-P13).

## 4. Special teams

### 4.1 Kick-offs (2026 dynamic kick-off; the rules in NFL_RULES_RESEARCH Part 5 sections 2.1 to 2.8)

- Deep kick into or through the end zone: a touchback at the 35 if it lands in the end zone untouched in the landing zone, the 20 if it hit the landing zone first (RB26 6-1-5). Touchbacks were 21.1 percent of kick-offs in 2025 and 15.8 percent in weeks 1 to 5 of 2026 (65.5 percent in 2024) (SRC-SECONDARY, computed from public play-by-play in this project, Part 9 section 4).
- Short kick into the landing zone (between the receivers' goal line and 20): it must be fielded and returned; kickers aim for this band now; a "trick bounce" kick (SRC-SECONDARY, AP 2025-09-18).
- Squib kick (low and skipping): under the same landing-zone rules; a kick that first lands short of the landing zone is dead and the receivers start at the 40 (RB26 6-2-4); no published usage (UNVERIFIED rate).
- Sky kick (very high): the coverage may not move until the ball lands, so height buys nothing (RB26 6-1-3); left out as a choice (recommendation).
- Out of bounds: 1.4 percent in 2025, 0.9 in 2026 (Part 9 section 4); a foul with the receivers' options (Part 5 section 2.6).
- Onside kick: declared, at any free kick (Part 5 section 1; the game has it, SX.4).
- Returns: 2,076 returns for 25.9 yards each and 6 touchdowns in 2025 (SRC-SECONDARY, ESPN); the average start the 30.3 (2025) and 30.2 (2026) (Part 9); hang time 3.37 seconds in 2025 against 3.86 in 2024 (SRC-SECONDARY, Sports Info Solutions). Middle, sideline and cross-field returns are play choices with no rule (UNVERIFIED as named schemes); wedges are illegal (section 1); laterals on returns are legal. A fair catch of a kick-off in the landing zone: the book's general definition allows it, one team article says no; recommendation: not offered.

