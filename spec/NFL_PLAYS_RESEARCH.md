# NFL_PLAYS_RESEARCH (nfl4 only): every real NFL play and every Madden NFL playbook concept, for SX.10b

Status: RESEARCH, version 1.0 (2026-10-20, PX session SX.10a). nfl4 only (CLAUDE.md rules 0.13 and 0.20; requirements NX-P1 to NX-P7 and NX-R7 in `spec\NFL_EXTRA_FEATURES.md` section 18; decisions D-082, D-083, D-085). No game code was written. Plain headings and lists, no tables.

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

### 4.2 Punts

League 2025 (SRC-SECONDARY, ESPN team pages summed): 1,932 punts (3.55 per team game), gross 47.15 yards, net about 42.6; inside the 20 39.2 percent, touchbacks 7.7, fair catches 27.3, returned 42.7 percent for 10.25 yards (15 touchdowns), blocked 0.47 percent. 2024: 2,038 punts, gross 47.47, net about 43.0, inside the 20 41.5, touchbacks 7.6, fair catches 27.6, returned 42.8 for 9.85, blocked 0.59. 2026 to week 6: gross 47.8, net about 42.0, inside the 20 40.8, touchbacks 7.1 (SRC-SECONDARY, CBS).
- Spread or shield punt (today's usual formation); tight punt (more protection, slower coverage; the book's standard punt formation note, RB26 9-1-3 Note); rugby punt (the punter rolls out and kicks on the move); directional and coffin-corner punts (aimed at the sideline near the goal line); pooch or pin punt (short and high to be downed inside the 10); sky punt; quick kick from an offensive formation (legal, RB26 9-1-1 Note 3; no recent use found).
- Returns: return middle, left, right, a wall return (a punt-return wedge has no rule against it, UNVERIFIED); punt safe (no return or block risk) and punt rush or block (a block chance; running into the kicker 5 yards, roughing 15).
- Fair catch (27 percent of punts) and the fair catch kick (a field-goal try from the spot of the fair catch with the defense 10 yards away, no tee, RB26 10-2-4, 11-4-3; last made 2024-12-19 from 57 yards, the first since 1976; SRC-SECONDARY).
- Muffed punts: either team recovers after a receiver touched it; the kickers' first touching gives the receivers the spot (RB26 9-2-2, 9-3-2); no published muff rate.
- A punt that hits the kickers' goal post is a safety (RB26 9-4-3); a punt from the end zone is an ordinary punt.

### 4.3 Field goals and tries

- Field goals, 2025 (SRC-SECONDARY, ESPN): 20 to 29 yards 98.1 percent, 30 to 39 93.0, 40 to 49 84.3, 50 or more 68.8, all 85.6 (931 of 1,088); 2024: 97.0, 94.3, 76.7, 69.9, all 84.1. About 2.0 attempts per team game; about 0.4 of 50 yards or more per team game in 2025 (SRC-SECONDARY, Pro Football Talk); the longest made in 2025 was 68 yards. The kick is about seven yards behind the line (the formation rule says seven or more, RB26 3-17-7(b); the exact distance UNVERIFIED). A made kick or a miss that does not land in the field of play takes at most 5 seconds (RB26 11-4-2 Note 5).
- A missed field goal: the receivers' ball at the spot of the kick, or at the 20 when the kick was from inside the 20; a miss the receivers touch beyond the line may be returned (RB26 11-4-2).
- Extra point (try kick) from the 15-yard line (a 33-yard kick): 95.9 percent in 2025, 95.8 in 2024 (SRC-SECONDARY, ESPN); 94.2 in 2015 after the move from the 2 (SRC-SECONDARY).
- Drop kick: legal for a field goal, try or free kick; last used 2006-01-01 (SRC-SECONDARY); recommendation: not offered.
- Blocked field goals: either team recovers; no published block rate.

### 4.4 Fakes

- Fake punt (the up-back or punter runs, the punter throws, a direct snap to a back): under 1 percent of punts (SRC-SECONDARY, Towards Data Science via search summary); about five fake-punt passes a season league-wide (Ringer 2019 via Full10Yards); one team 9 of 12 recently (Sports Illustrated). A punt formation keeps the gunner rule (RB26 9-1-2).
- Fake field goal (the holder runs or throws, the kicker throws): no league rate found.
- Swinging-gate or other unbalanced formations on a try: legal (RB26 11-3-1), no usage found.

## 5. Two-point plays

- The try from the 2 (a run or pass), the kick from the 15 (RB26 11-3-1); a touchdown by either team on a try scores 2, so the defense scores 2 by returning an interception, a fumble or a blocked kick (RB26 11-3-2(b), since 2015); a safety on a try gives the other team 1 point; a touchback ends the try; the team may change its choice after a charged timeout or a foul (RB26 11-3-1).
- Conversion: 46 percent in 2025 (SRC-SECONDARY, Yahoo Sports); 41 percent in 2024, the lowest in 15 years, passes 37 percent and runs 50 percent, 73 percent of attempts were passes, 72 percent came in the fourth quarter, 9.8 percent of touchdowns were followed by a try for two; about 55 percent in 2023; 47.6 percent over the five seasons to 2024; break-even against a 96 percent kick about 48 percent (SRC-SECONDARY, Fox Sports and the University of Wisconsin's Badger Bracketology).
- The plays used: the usual pass concepts near the goal line (quick passes, rubs and picks, rollouts, fades), quarterback runs (4 of 9 in 2024) and running back carries (14 of 26) (SRC-SECONDARY, Fox). In the game the try uses the offense menu's first five items (the original); SX.10b decides which of the new plays the try offers (Q-P5).

## 6. Madden NFL 27's playbooks, as football concepts (NX-P2, D-083)

### 6.1 Structure and size

A team book is formation families, then sets, then plays; offense and defense books are chosen separately (MADDEN_PLAYBOOK_RESEARCH section 1). madden.tools (SRC-SECONDARY, read 2026-10-20) lists 18 offensive families (Shotgun 238 sets and 5,631 plays; Singleback 63 and 1,449; Pistol 51 and 888; I-Form 17 and 330; Strong I 17 and 260; Weak I 13 and 140; Split Backs 5 and 60; Near 5 and 49; Full House, Maryland I, Far, Power I, Flexbone, Wishbone, Split T, Wildcat, Goal Line and Hail Mary with 3 to 31 plays each) and 16 defensive families (Nickel 31 sets and 672 plays; Dime 13 and 274; 3-4 15 and 190; 4-3 9 and 129; 4-2-5 5 and 111; 3-3-5 5 and 86; Dollar, Quarter, Big Nickel, 46, 2-4-5, 2-5, 4-4, 5-2, Goal Line, Prevent with 6 to 49 each). "Gun Bunch", "Gun Trips", "Gun Empty" and wing looks are sets inside Shotgun, not families; "Under Center" is not a family. EA publishes no plays-per-book figure (SRC-OFFICIAL, by absence).

### 6.2 The concepts (merged catalog, plain words; each is inside sections 2 to 5)

From ten offensive sets (324 plays) and six defensive sets (178 plays) read by name, and guides (SRC-SECONDARY unless marked; "common" means in many of the sampled sets):
- Runs (21): dive; inside zone; outside zone or stretch; mid zone; split zone; power; counter (strong and weak); iso; lead or blast; duo; trap; draw (halfback, lead, delayed); toss and pitch sweep; double-pull sweep; off tackle or slash; belly; cutback or misdirection; jet sweep; end around; reverse and fake reverse; fullback dive or trap.
- Quarterback runs and options (13): read option; speed option; triple option; midline option; inside veer; power option; an option with a receiver or tight end as the pitch man; the sneak (EA made it a timing mechanic, SRC-OFFICIAL); the push sneak (six team books, SRC-OFFICIAL); quarterback draw; quarterback zone; quarterback counter, wrap or crack sweep; the bootleg keep.
- Run-pass options (6): with a bubble, a slant or glance, a flat, a wheel or tight-end route, off jet motion, an "alert" throw on a run.
- Quick and short passes (18): slants (single, double, slant and go; SRC-OFFICIAL as a kind); stick (SRC-OFFICIAL); spot or snag; smash; curl-flat (SRC-OFFICIAL as slant-flat); hitch, quick out, quick fade; mesh with its variants (a post, spot, rail or wheel on top; SRC-OFFICIAL); drive; shallow cross or drag; spacing; levels (SRC-OFFICIAL); dagger; bench and angle; swing; whip; choice route; return routes; leaks.
- Intermediate and deep (14): flood (SRC-OFFICIAL); four verticals (SRC-OFFICIAL); seam; post; corner and post-corner; deep cross or Y-cross; dig and double dig; comeback and curl; out and double out; fade, go, goal-line fade; double moves (SRC-OFFICIAL as a kind); wheel and post-wheel; divide or scissors; sail.
- Screens (7): halfback slip screen; halfback flat screen; receiver and middle screen; bubble; tight-end screen; fullback screen; jailbreak.
- Play-action (9): boot, waggle, rollout (SRC-OFFICIAL); the deep shot; crossers (SRC-OFFICIAL); flood; post, corner, double post, comeback or dig; flat or leak; screen behind the fake; wheel or divide; the fake matched to the run.
- Trick and special (12): flea flicker; halfback pass; double pass (SRC-OFFICIAL, one team book); receiver reverse pass; fake reverse to a halfback pass; the tight-end throw to the quarterback; jet touch pass; fake sneak to a swing; Hail Mary; spike; fake spike; kneel.
- Coverages (16): Cover 0; Cover 1 (hole, robber, contain, press); Cover 2 (hard flat, invert, sink, drop, roll, match); Cover 2 man; Tampa 2; Cover 3 (sky, cloud, buzz, hard flat, seam, match); Cover 4 or quarters (drop, palms, press); Cover 6; match-quarters hybrids; match zone (more match checks in Madden 27, SRC-OFFICIAL); bracket and double coverage (new in Madden 27, SRC-OFFICIAL); roll coverage (SRC-OFFICIAL); man with three deep; spy; prevent; show-two and disguise.
- Pressure and run defense (14): linebacker, nickel or dime, safety, corner and edge blitzes; defensive back fire; zone blitz or fire zone (SRC-OFFICIAL); overload; simulated pressure; twist, stunt, loop; cross blitz; run blitz and gap-assigned run stops; contain and quarterback contain (SRC-OFFICIAL); pinch.
- Fronts as looks (8): 4-3 (over, under, even, odd); 3-4 (under, tite, bear, odd); 46 or bear; goal line (5-3, 6-2); nickel with walked-up linebackers; dime and dollar (six backs); quarter (seven) and prevent; the small odd fronts (4-4, 5-2, 2-5, 3-3-5, 4-2-5, 2-4-5).
- Special teams (21): kick-off deep, squib, onside high and low (SRC-SECONDARY, ClutchPoints and games.gg; Madden 27 plays the NFL's dynamic kick-off with the touchback at the 35), a short high kick (UNVERIFIED in Madden 27); the landing zone; kick-off returns (middle, left, right) and the hands team; punts normal, sky and backspin, coffin corner (UNVERIFIED in Madden 27); punt returns, the safe return and the fair catch; punt block; fake punt run and pass; field goal and extra point; field-goal block; fake field goal run and pass; two-point plays (the last five known from older Madden versions only, UNVERIFIED for Madden 27).
- Pre-snap tools (8): an audible to a preset (four per formation, SRC-SECONDARY); a hot route (one receiver's route changed); motion; a formation shift within the same personnel (new in Madden 27, SRC-OFFICIAL); flip (the play mirrored); defensive shading (press or off, inside or outside); protection (normal, max, slide); a personnel substitution at the call (SRC-OFFICIAL).
Every concept above is in the NFL list of sections 2 to 5; what Madden adds is the organization (formation, set, play), the per-team selection, and the pre-snap tools. Concepts in every major family (Shotgun, Singleback, Pistol, I-Form): inside and outside zone, draw, power, counter, slip screen, slants, curl-flat, mesh, flood, post, corner, dig, comeback, play-action boot and shot. Only in heavy sets: iso, lead, duo, the option runs, fullback dive, the sneaks, split zone. Only in spread sets: bubble, RPOs, quarterback draw and zone, jet sweep, four verticals, spacing.

### 6.3 What the Madden structure means for a spoken game

The pool is huge because one concept appears in many formations and sets; a spoken game reaches the same variety with few keys by treating the formation, the side (flip) and the personnel as modifiers of a concept (one extra step or a remembered default), and a team's book as a weighted selection of concepts (SX.7's styles already do this). EA's own advice that a small book the player knows well can beat a big one (MADDEN_PLAYBOOK_RESEARCH section 1) supports favourites and a short first level.

### 6.4 More EA names never to use (add to MADDEN_PLAYBOOK_RESEARCH section 3 list B)

The push sneak's EA name and EA's goal-line sneak formation name; the EA name of the Super Bowl LII trick play; branded play strings and stems (for example names built like "Hoss Juke", "Boomerang", "Alert X Smoke"); the smart-zone modes and match-check names; the coverage adjustment hub; ID Mike; gap integrity as a feature; formation shift, custom adjustments, macros, CoachSpeak, Coach Mode and Auto Flip as feature names; the sneak meter; set names such as Hulk, Gadget, Sugar, Predator, Grizzly, Cub. The football words behind them (jumbo, bear front, walked-up linebackers, wide edges, mirror the play) are free.

## 7. Where the N. F. L. rules mode does not yet follow the 2026 rules (NX-R7, D-085)

Each gap: what the mode does now (the original's rule, GAME_SPEC), what 2026 says, who closes it. Classic keeps the original in every case.
- G26-1 Kick-off. Now: the original's kick-off (5.10: always caught 1 to 7 yards deep in the end zone, the run-out question, a touchback to the 20, returns of 12 to 101; D-042 item 6). 2026: the dynamic kick-off (the setup zone, the landing zone, the touchback to the 35 or the 20, a short kick to the 40, out of bounds to the 40, about 21 percent touchbacks in 2025 and 16 in 2026, the average start about the 30; RB26 6-1, 6-2; Part 5). Closes: SX.10b design, SX.10d build (the kick-off menu with deep, short, squib and onside; the return).
- G26-2 Onside question only when it "makes sense" (D-041). 2026: any free kick (RB26 6-1-6). Closes: SX.2b (asked at every kick, D-085). CLOSED 2026-10-20 in SX.2b (D-087): asked at every kick-off and safety kick of the player's team; SX.10d makes it the 2026 kick-off menu.
- G26-3 Overtime is sudden death (D-041). 2026: Rule 16 (both teams get a possession unless the first drive ends in a safety, one 10-minute regular-season period that may end tied, 15-minute play-off periods, the overtime timeouts, no coach challenges). Closes: SX.12 (the owner's answer of 2026-10-20). CLOSED 2026-10-21 by SX.12 (D-096): Rule 16 is built in the N. F. L. rules mode (`extras\overtime.py`, the hooks H22), Classic keeps sudden death.
- G26-4 The extra point never misses (Q21). 2026: the try kick from the 15, made 95.9 percent in 2025. Closes: SX.10b and SX.10d.
- G26-5 Punts: 25 to 59 yards evenly, never returned, never blocked or muffed; one third each fair catch, out of bounds and downed. 2026 practice: gross about 47, 42.7 percent returned for about 10 yards, 0.5 percent blocked; the rules of 9-2 to 9-4. Closes: SX.10b and SX.10d (punt kinds, returns, the fair catch, the block).
- G26-6 Field goals: good with 63 percent from the 30 (a 47-yard kick) and 50 percent from the 35, never tried from the kicker's own half ("is way to short"). 2025: 84.3 percent from 40 to 49 yards, 68.8 from 50 or more, made from 68 yards. Closes: SX.10b and SX.10d (the published odds by distance, the long try allowed).
- G26-7 A missed field goal gives the ball at the line of scrimmage (5.11). 2026: at the spot of the kick, or the 20 when kicked from inside the 20 (RB26 11-4-2). Closes: SX.10d.
- G26-8 Interceptions and fumbles put the ball at a random yard line 5 to 44 in the same half, never returned, never a defensive touchdown (Q31). 2026: the defense may advance, score and fumble again (RB26 8-7, 7-2). Closes: SX.10b (the turnover model) and SX.10c.
- G26-9 Every fumble is lost (5.9). 2026: either team may recover; on fourth down, after the warning and on a try only the fumbler may advance (RB26 8-7-5, 8-7-6). Closes: SX.10b and SX.10c.
- G26-10 Two-point tries: only the player tries one; a turnover leaves the try open (Q23); the defense cannot score. 2026: either team may try (the computer went for two after 9.8 percent of touchdowns in 2024), the defense scores 2 on a return (RB26 11-3-2). Closes: SX.10b, SX.10c (the computer's choice by the score and the clock).
- G26-11 After a safety the kick is the ordinary kick-off. 2026: a safety kick from the 20 by punt, drop kick or place kick (RB26 11-5-2; the onside part is already built, SX.4). Closes: SX.10d.
- G26-12 No kneel and no spike in the menus. 2026: both legal plays (RB26 7-2-1(c), 8-2-1 Item 3). Closes: SX.10c.
- G26-13 No fair catch kick. 2026: allowed after a fair catch (RB26 10-2-4, 11-4-3), also on an untimed down at the end of a half. Closes: SX.10d (offered only in range at the end of a half, recommendation).
- G26-14 The fouls of the new kicks and plays (the wedge, illegal double teams, the landing-zone and kick-out-of-bounds fouls, fair catch interference, kick catch interference, the gunner rule, the leaping and leverage fouls, ineligible downfield on run-pass options) are not in the foul table of SX.3. Closes: SX.10d and SX.10e (rows in `extras\fouls_2026.py` with their 2026 rates, NFL_RULES_RESEARCH Part 7).
SX.13 (a fresh reviewer, D-085) reads the whole 2026 book against the mode and may find more; each new gap gets the next number.

## 8. Numbers for the outcome models (all collected; the season and source on each line)

League passing and running
- 2024: completion 65.29 percent; 7.13 yards per attempt; interceptions 2.17 percent of attempts; sacks 6.87 percent of dropbacks; 4.44 yards per carry; 32.74 attempts and 27.00 rushes per team game. 2023: 64.47, 7.02, 2.35, 7.15, 4.20. 2022: 64.23, 7.03, 2.31, 6.70, 4.46. (SRC-SECONDARY, RotoWire)
- Average depth of target about 8.2 (PFF) or 7.65 (RotoWire, 2024); time to throw 2.86 seconds (2025, PFF).
- Deep passes: under 12 percent of attempts; completion 39.6 (PFF 2025) or 36.6 (Sharp 2025); deep cross 54.9, deep seam 47.1, deep corner under 38 percent (PFF 2025).
- Passes inside three seconds 6.29 yards per attempt, after three seconds 8.19 (early 2024, The Analyst).
- Hail Mary: 16 touchdowns, 50 interceptions in 193 tries from 2009 (ESPN); about 9.7 percent completed (FiveThirtyEight, undated, search summary).
Concepts
- Run yards per carry 2020 to 2022 (PFF): inside zone 3.90, outside zone 3.78, duo 3.71, power 4.53, counter 3.90, pull lead 3.85, draw 5.95. 2021 to 2024 (Fantasy Points, search summary): inside zone 4.15 and 44.0 percent stuffed, outside zone 4.26 and 49.5, gap runs 4.48 and 44.6.
- Shares: outside zone 27 percent of runs (2025); draws 3 percent (2022); duo 16 percent (2022) (PFF).
- Play-action 25.65 percent of plays (2025), 7.76 against 6.72 yards per attempt (PFF).
- RPO 7.95 percent of plays (2025); 4.53 yards and 52.3 percent success against 5.43 and 48.1 (2021 to 2025) (PFF).
- Screens 11.0 percent of dropbacks, 86.0 percent completed (2024, PFF).
- Sneaks: first down 75.8 percent (2025, PFF); the push sneak of the best-known team 65.5 percent in 2025.
- Fourth down converted about 55 percent (2025).
- No-huddle 9.91 percent of plays (2025, PFF); shifts or motion 63.9 percent (2025, PFF).
Defense
- Two-high 42.0 percent of pass plays, Cover 2 13.9, Cover 4 17.2, Cover 6 9.2 (2025, NGS, SRC-OFFICIAL); Cover 1 about 22 to 26, Cover 3 about 30 to 32, Cover 0 about 2.5 to 4 (RotoWire, The 33rd Team, MatchQuarters).
- Yards per dropback by coverage since 2020 (The 33rd Team): Cover 0 4.76, Cover 2 man 5.19, Cover 4 5.94, Cover 1 5.98, Cover 2 6.27, Cover 3 6.66, Cover 6 6.69.
- Man coverage 22.6 percent of snaps (2025, PFF); base 29.6, nickel 59.0, dime 9.4 percent of snaps (2025, PFF).
- Blitz about 33 percent of pass plays; pressure on 42.3 percent of blitzes (2025, PFF); blitz on 10.0 percent of two-high plays and 39.7 of the others (NGS).
Special teams and tries
- Kick-offs: touchbacks 21.1 percent (2025), 15.8 (2026 to week 5); returns 25.9 yards; the average start about the 30 (Part 9, ESPN).
- Punts: gross 47.15, net about 42.6, returned 42.7 percent for 10.25 yards, fair caught 27.3, inside the 20 39.2, touchbacks 7.7, blocked 0.47 percent; 3.55 punts per team game (2025, ESPN).
- Field goals by distance 2025: 98.1, 93.0, 84.3, 68.8 percent (20s, 30s, 40s, 50 and more), 85.6 overall, 2.0 tries per team game (ESPN).
- Extra point 95.9 percent (2025, ESPN).
- Two-point tries 46 percent (2025); 41 (2024: passes 37, runs 50); tried after 9.8 percent of touchdowns (2024) (Yahoo, Fox, Badger Bracketology).
- Fake punts under 1 percent of punts (weak).
The bands of SX.2 to SX.9 (NFL_EXTRAS_DESIGN sections 4 to 10, D-078, D-079) stay; SX.10e adds a band for each line above that a new play changes.

## 9. Mapping onto the game's catalog (SX.7: O001 to O052, D001 to D030)

Already in the catalog (by its spoken name): offense runs inside zone, power, counter, draw, dive, iso, trap, lead, stretch, outside zone, toss sweep, jet sweep, pitch, end around, speed option, reverse; screens to the back, a receiver, the tight end, tunnel, bubble; passes hitch, quick out, curl and flat, stick, drag, mesh, shallow cross, spacing, one RPO, slants, four verticals, deep post, corner, go, deep cross, flood, Hail Mary, wheel; play-action short, deep, shot and cross, bootleg short, rollout; quarterback sneak, keeper, draw, read option keep, power, the push sneak, bootleg run. Defense goal line eight up and stack, bear front, base run fit, run blitz, inside run force, contain, edge setting, spy, zone blitz, Cover 0 blitz, safety, corner, linebacker and A-gap blitzes, Cover 2, Cover 3, man free, underneath zone, nickel quick coverage, Tampa 2, Cover 4, deep thirds, prevent, Cover 6, double coverage, palms, dime short and deep, man press.
Missing, offense (about 100): duo, split zone, mid zone, counter trey, buck or pin-pull sweep, crack toss, quick toss, off tackle, belly, wham, cutback, delayed draw, fullback dive and trap; triple, midline, inside veer, inverted veer, power read and power options, the receiver-pitch option, quarterback zone, counter and crack sweep; RPO kinds (bubble, glance, flat, stick, wheel, jet, alert); slant-flat, snag or spot, smash, all hitches, speed out, double slants, fade, back-shoulder, dig, levels, drive, Y-cross, sail, comeback, curl, out, deep out, choice route, dagger, follow, hank, post-wheel, mills, yankee, double posts, seam, sluggo, stutter-go, out-and-up, zig, angle, swing, flat, Texas, check-down, bench, whip, return routes, leaks, divide or scissors; slip screen, jailbreak, middle screen, double screen, shovel pass, fullback screen, screen behind a fake; play-action flood and wheel, naked boot, waggle, sprint out, max protect; flea flicker, halfback pass, double pass, the tight-end throw to the quarterback, hook and lateral, statue of liberty, fake spike, fake kneel, wildcat snap, jet touch pass, fake sneak swing, end-of-game laterals; kneel; spike; formations and personnel as modifiers; motion; flip.
Missing, defense (about 50): fronts and packages as choices (4-3 over and under, 3-4 odd, tite or mint, 46, 5-2, 6-1 and 6-2, 5-3, 4-4, wide nine, nickel 4-2-5 and 3-3-5, big nickel, 2-4-5, dime 4-1-6 and 3-2-6, dollar, quarter, 2-5); Cover 1 robber, 2-man, Cover 3 sky, cloud, buzz and match, match quarters, Cover 9-style checks, off man, bracket, man with three deep, roll, disguise; four-man and three-man rushes, fire zone, simulated pressure, creeper, overload, double A-gap, edge, nickel and dime blitzes, defensive back fire, delayed and cross blitzes, stunts and twists, pinch, free fire; one-gap and two-gap, slant and angle calls, spill or box, the option assignments; the Hail Mary, kneel and two-point defenses.
Missing, special teams: every choice of section 4 (the original has one kick-off, one punt, one field goal, one extra point); the receiving team's calls (return, fair catch, block, safe, hands team); the fakes.

## 10. Open design questions for SX.10b (each with the research's recommendation; SX.10b decides and records)

- Q-P1 (NX-P7) How a blind player reaches hundreds of plays as quickly as the original's eight. The measure: keys and spoken words from the prompt to the snap. The original: the prompt, one digit (the item is said) and Enter, or Up and Down and Enter; two keys for any call. Ways to keep that: (a) the original's items stay first at the top level and keep their digits; Enter on one of them calls the playbook's pick of that family for this down and distance (two keys, as now); (b) one more top item "all plays" opens groups (by kind for the offense: inside runs, outside runs, quarterback and option, run-pass options, quick passes, intermediate, deep, screens, play-action, trick plays, clock plays; for the defense: fronts, coverages, pressure; special teams by kick) and then the play (four to five keys); (c) a favourites list the player fills (one key to add the current play), as the first group; (d) "the same play again" on one key; (e) type-to-find: letters spell the start of a play's name and the list jumps there (the original echoes letters, so this is a clone addition the key help names); (f) the formation, side and personnel are remembered defaults that a separate step changes, never asked every play. Recommendation: (a) plus (b), (c), (d) and (e); measured in a test (any play in at most six keys, the usual call in two) and in the owner's listening round. Note: the letters T (timeout, CLAUDE.md 0.22), S (Save Game) and C (challenge) are taken; type-to-find must leave them alone or start with a key of its own.
- Q-P2 Formation first or play first. Real football and Madden choose the formation first; a spoken game is faster with the concept first and the formation as a default. Recommendation: concept first, formation a remembered default per group with a change step.
- Q-P3 How personnel and formations are said: plain words ("three receivers, one tight end", "shotgun"), never digit codes, and every rare word explained in F7 (the football words).
- Q-P4 The outcome model. The original's 5 by 6 family table with bounded changes (SX.7) cannot reach the published league numbers (section 8) for a hundred concepts. Recommendation: in the N. F. L. rules mode a new outcome layer: each concept has a family (run inside, run outside, quarterback run, option, RPO, quick pass, intermediate pass, deep pass, screen, play-action, trick), a base model calibrated to the league numbers (completion, yards per attempt, sacks, interceptions, yards per carry, stuffed runs, explosive plays), and small matchup changes against the defense's front, coverage and pressure from the published coverage and pressure numbers; Classic keeps the original's table untouched. The bands of SX.2 to SX.9 must still hold (NX-P5).
- Q-P5 Which plays the two-point try offers; which rare formations (wishbone, flexbone, wildcat, single wing) and plays (drop kick, quick kick, sky kick) ship at all. Recommendation: the try offers the short and goal-line concepts and the quarterback runs; the rare formations as named plays in a "rare" group; the drop kick, quick kick and sky kick left out.
- Q-P6 Motion: one remembered switch (none, jet, orbit) with the small published effect, or part of some plays only.
- Q-P7 Which concepts get their own model and which share one with a small change; run concepts by the PFF and Fantasy Points numbers; the box count model for runs (no published league numbers by box).
- Q-P8 Run-pass options and read options: the throw, keep or hand-off decided by a draw keyed to the defense's call, or by the player at the line.
- Q-P9 Play-action as its pass twin plus a fake effect (7.76 against 6.72 yards per attempt) rather than separate models.
- Q-P10 Trick plays: their risk (a lateral fumbled, the fourth-down fumble rule, interceptions) and how often the computer calls them (rare, by situation).
- Q-P11 No-huddle and the two-minute offense: a player's switch (the clock design's tempo) and the clock plays (kneel, spike) in the menu only when they apply.
- Q-P12 The word "dollar" (six, seven or nine backs in different sources) and other disputed words (okie, big nickel, palms, Cover 9): the game says the number of backs and linebackers, not only the word.
- Q-P13 The defense's personnel and situation defenses: chosen by the player or matched by the game with an override; the computer's defense chooses by the offense's personnel.
- Q-P14 Coverage and pressure as one combined call (as Madden and SX.7 do) or two picks; two picks double the keys, one combined call needs about 60 named calls. Recommendation: one combined call in the groups, with "coverage" and "pressure" as the two groups of the all-plays list.
- Q-P15 Data for per-concept numbers. The pages publish league totals and a few concepts; per-concept completion, sack and interception rates by coverage are not published. The public nflverse play-by-play files (already used in SX.0 with the owner's approval, NFL_RULES_RESEARCH Part 9) and the FTN charting data published with them (play-action, screen, RPO, blitzers, box count; its license must be read first) would give them. Downloading needs the owner's yes (one question in SX.10b with the files, sizes and terms named).
- Q-P16 Special teams menus: the kick-off menu (deep, short into the landing zone, squib, onside), the punt menu (normal, pin or coffin corner, rugby, fake run, fake pass), the field-goal menu (kick, fake run, fake pass), the receiving team's menu (return middle or sideline, fair catch, block, safe, hands team), each with the original's item first so Enter keeps the original's pace.
- Q-P17 The kneel and the defense: the kneel ends the down with no defensive choice; offered only when it helps (leading late).
- Q-P18 The fair catch kick: offered only at the end of a half after a fair catch in range, as a yes or no.
- Q-P19 The Franchise: the team playbooks (SX.7 styles, SX.8o "playbooks follow the best players") grow to the full catalog; the styles' weights over the new concepts are set in SX.10e and the 20-season test runs again (NX-P5).
- Q-P20 The penalty table: which new fouls attach to which calls (press man more illegal contact, blitzes more roughing the passer, RPOs ineligible downfield, kicks the 2026 kick fouls) (G26-14).

## 11. Could not settle

- League completion and yards per attempt by air-yards band; league sack rate for 2025 and with or without play-action; completion and yards when blitzed against not blitzed; three- and four-man rush shares; yards per carry by box count; screen rates by type; designed quarterback run and option rates; kneel, spike and fake-kick rates; muff and field-goal block rates (Q-P15 is the route to most of them).
- Definitions with no reliable source: dagger, follow, hank, post-wheel, mills, yankee, Texas, palms, 2-read, Cover 9, overload and delayed blitz, big nickel, 2-4-5, sail, fork, the "6-5" goal line; the meaning of "dollar".
- Conflicts kept as ranges: 11 personnel 56.1 or 57 percent; sneak success 75.8 (PFF) against 84.2 to 84.8 (other filters); deep completion 39.6 against 36.6; average depth 8.2 against 7.65; Cover 6 share 9.2 (NGS) against 3.24 (The 33rd Team).
- Whether a fair catch of a kick-off in the landing zone is allowed in 2026 (the book's general text says yes, a team article says no; the casebook was not reached).
- The NFL "football terms" page still says a free-kick touchback goes to the 25; the 2026 rulebook says the 20 or the 35 (the rulebook wins).
- Madden 27's special-teams plays beyond the kicking basics and the dynamic kick-off; EA's plays per team book; the current state of Madden's auto flip.
- Pages that would not open: Pro Football Reference (403), TeamRankings (403), Fantasy Points (402), Next Gen Stats tables (drawn by script), Madden School (403), the EA forum thread (403), civil.gg's playbook database (script).

## 12. Sources (all read 2026-10-20 unless dated; the full lists with every URL are in the notes files named at the top)

Official (NFL):
- 2026 NFL Official Playing Rules (PDF): https://static.www.nfl.com/image/upload/fl_attachment/league/tqivdkzt9mu6wdgsh1ku.pdf (Rules 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14).
- NFL Football Operations, football terms: https://operations.nfl.com/rules-officiating/nfl-football-basics/football-terms
- NFL Flag training sheet (route tree and concepts): https://static.www.nfl.com/image/upload/league/w7jrxyki5ffvoncw3ckg.pdf
- NFL youth and high school football glossary: https://playfootball.nfl.com/tackle/youth-and-high-school-tackle-football-glossary/
- Next Gen Stats, new metrics for 2025: https://www.nfl.com/news/next-gen-stats-new-advanced-metrics-you-need-to-know-for-the-2025-nfl-season
- Next Gen Stats, the coverage that turned the Seahawks into Super Bowl winners (2026-02-18): https://amp.nfl.com/news/the-coverage-that-turned-the-seahawks-into-super-bowl-winners-and-is-taking-the-nfl-by-storm
- Next Gen Stats, entering week 14 (2025): https://www.nfl.com/news/outrageous-next-gen-stats-entering-week-14
- Next Gen Stats, stacked boxes (2016): https://www.nfl.com/news/jay-ajayi-leads-top-10-rbs-against-stacked-boxes-0ap3000000772651
- Approved 2026 playing rules: https://media.nfl.com/football-information/2026/news/approved-2026-playing-rules--bylaws-and-resolutions and https://www.nfl.com/news/nfl-announces-new-playing-rules-bylaws-resolutions-for-2026
- The 2025 push-sneak vote: https://www.nfl.com/news/nfl-owners-vote-against-banning-tush-push-play-at-spring-league-meeting ; no 2026 proposal: https://www.nfl.com/news/competition-committee-co-chairman-rich-mckay-doesn-t-expect-tush-push-ban-proposal-in-2026
Official (EA, Madden NFL 27; concepts only):
- Week 1 breakdown: https://www.ea.com/games/madden-nfl/madden-nfl-27/news/madden-nfl-27-kickoff-week-1-breakdown
- Gameplay Deep Dive (2026-06-04): https://www.ea.com/games/madden-nfl/madden-nfl-27/news/madden-27-gameplay
- Launch guide: https://www.ea.com/games/madden-nfl/madden-nfl-27/news/madden-nfl-27-launch-guide
- Title updates of 2026-08-26 and 2026-09-16: https://www.ea.com/games/madden-nfl/madden-nfl-27/news/m27-title-update-august-26-2026 and https://www.ea.com/games/madden-nfl/madden-nfl-27/news/madden-nfl-27-title-update-september-16
- EA help, improving at Madden: https://help.ea.com/en/articles/madden-nfl/madden-improve/
Secondary (the main ones):
- PFF: play-action, motion and RPO rates (2025 data) https://www.pff.com/news/fantasy-football-2026-how-play-action-pre-snap-motion-and-rpo-rates-define-2026-fantasy-value ; RPOs over five seasons https://www.pff.com/news/nfl-analyzing-the-effectiveness-of-rpos-over-the-last-five-nfl-seasons ; the deep ball https://www.pff.com/news/nfl-deep-ball-analysis-more-efficient ; screens https://www.pff.com/news/nfl-screen-pass-rates-success-study-2025 ; sneaks https://www.pff.com/news/is-the-tush-push-losing-its-edge-analyzing-nfl-sneak-success-since-2022 ; run concepts https://www.pff.com/news/fantasy-football-finding-an-edge-in-offensive-run-concepts-2023 and https://www.pff.com/news/breaking-down-pffs-run-concepts ; run-game stagnation https://www.pff.com/news/nfl-rushing-attacks-inside-the-league-wide-stagnation-of-run-game-innovation ; no-huddle https://www.pff.com/news/fantasy-football-nfl-pace-volume-how-no-huddle-trends-shape-2026-value ; 11 personnel https://pff.com/news/pro-the-rise-of-11-personnel-in-the-nfl ; 2025 schematic trends https://www.pff.com/news/nfl-is-evolving-five-schematic-trends-that-have-shaped-the-2025-season ; blitzers https://www.pff.com/news/nfl-5-most-effective-blitzers-from-the-2025-nfl-season
- RotoWire, league trends: https://www.rotowire.com/football/article/nfl-state-of-the-union-how-league-wide-trends-impact-fantasy-football-95635 and https://www.rotowire.com/football/article/nfl-state-of-the-union-2024-season-preview-84647
- ESPN (Barnwell via ABC7) on under-center offenses: https://abc7.com/post/nfl-offenses-are-going-center-more-often-2026/19843021/ ; ESPN win rates 2025: https://africa.espn.com/nfl/story/_/id/46138675/2025-nfl-win-rates-top-teams-players-rankings-pass-run-block ; ESPN, the Hail Mary: https://africa.espn.com/nfl/story/_/id/27951311/the-evolution-hail-mary-perfect-throw-how-defend-it
- ESPN team statistics (punting, returning, kicking 2024 and 2025): https://www.espn.com/nfl/stats/team/_/view/special/stat/punting/season/2025/seasontype/2 , https://www.espn.com/nfl/stats/team/_/view/special/season/2025/seasontype/2 , https://www.espn.com/nfl/stats/team/_/view/special/stat/kicking/season/2025/seasontype/2 and the 2024 pages
- CBS Sports team punting 2026: https://www.cbssports.com/nfl/stats/team/team/punting/nfl/regular/
- The 33rd Team, man and zone coverage: https://www.the33rdteam.com/breaking-down-nfl-man-zone-coverage-schemes/
- MatchQuarters: https://www.matchquarters.com/p/even-front-odd-spacing-nfl-defense-walk-solid , https://www.matchquarters.com/p/sending-the-house-a-lesson-from-the , https://www.matchquarters.com/p/chargers-run-defense-small-ball-jesse-minter
- Sharp Football Analysis: personnel https://www.sharpfootballanalysis.com/stats-nfl/nfl-offensive-personnel/ ; coverage table https://www.sharpfootballanalysis.com/stats-nfl/nfl-coverage-schemes/amp ; red zone https://www.sharpfootballanalysis.com/fantasy/nfl-red-zone-stats-expectations-running-backs-2025/amp/
- The Analyst, 2024 passing: https://theanalyst.com/articles/whats-behind-drop-in-2024-nfl-passing-stats
- Fox Sports, two-point conversions: https://amp.foxsports.com/stories/nfl/why-nfls-two-point-conversion-rate-15-year-low ; Yahoo Sports (2026-10-06): https://sports.yahoo.com/articles/buffalo-bills-2-point-conversion-114546709.html ; Badger Bracketology 2024 recap: https://bracketology.engr.wisc.edu/nfl-analytics-recap-of-the-2024-regular-season/
- Sports Info Solutions, kick-offs (2025-10-02): https://www.sportsinfosolutions.com/?p=8292 ; AP via news4jax (2025-09-18): https://www.news4jax.com/sports/2025/09/18/no-longer-a-dull-formality-nfl-kickoffs-require-a-new-set-of-skills-for-kickers-and-returners/ ; Atlanta Falcons, dynamic kick-off check: https://www.atlantafalcons.com/news/dynamic-nfl-kickoff-new-rule-rich-mckay-evaluation
- Pro Football Talk, long field goals: https://www.nbcsports.com/nfl/profootballtalk/rumor-mill/news/nfl-kickers-are-77-for-108-on-50-yard-field-goals-this-season ; American Football International, the fair catch kick: https://www.americanfootballinternational.com/?p=184802 ; Pro Football Hall of Fame: https://profootballhof.com/the-last-dropkick and https://profootballhof.com/news/2024/09/2-point-conversion-turns-30-years-old
- USA Football, the tite front: https://blogs.usafootball.com/blog/7253/the-tite-front-why-defenses-are-tightening-down-the-interior-of-their-defense ; Viqtory Sports, defenses explained: https://www.viqtorysports.com/football-defenses-explained/ ; gorout (trick plays, personnel): https://gorout.com/football-trick-plays/ , https://gorout.com/football-personnel-groupings/
- Wikipedia (definitions only): formations, routes, the fumblerooski, defense, the glossary, the blitz, the prevent defense, the 46 defense, the 5-3 defense, two-point conversion.
- madden.tools (Madden 27 playbook database: the families, sets and play names): https://madden.tools/playbooks and its formation and set pages; games.gg Madden 27 guides (offense, defense, onside, passing, complete guide); civil.gg tips pages; ClutchPoints Madden 27 kicking guide https://clutchpoints.com/gaming/madden-27-kicking-guide ; mut.gg deep-dive summary; madden27.wiki.
- Search summaries only (weakest): Fantasy Points run concepts, JetsXFactor personnel, FiveThirtyEight on the Hail Mary, Fox and AOL on fourth downs, CBS and ABC7 on sneaks, Towards Data Science on fake punts, The Ringer, SumerSports.

## 13. History

- 1.0 (2026-10-20, PX SX.10a, D-084, D-085, D-086): written from four research passes (offense, defense, special teams with the two-point plays, Madden NFL 27's playbooks), reviewed and merged here; section 7 added for the owner's report that the game must follow the 2026 rules (D-085). No game code changed.
- 1.0, note of 2026-10-20 (PX SX.10b, D-090): the questions of section 10 are decided in `spec\NFL_PLAYS_DESIGN.md` 1.0 section 0; Q-P15 was answered by the owner (download) and the numbers section 11 could not settle (completion by depth band, by coverage and blitz, yards by box count, screen, run-pass option and trick-play rates, punt, kick-off and field-goal shapes) are computed from the nflverse and FTN data in `work\sx10b\data_numbers_sx10b.txt` and kept with their credit in `clone\src\nfl4\extras\plays\model_data.py`. This file's text is unchanged.
