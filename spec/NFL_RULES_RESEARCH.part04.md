### 5. Statistics (all SRC-SECONDARY unless stated; none from downloaded data files)

League quarterback rushing, regular season, all quarterbacks (StatMuse natural-language query pages; the page content was summarized by the fetch tool; cross-checked against the Parlay Savant table below)
- URL: https://www.statmuse.com/nfl/ask/total-quarterback-rushing-attempts-and-yards-by-season-2022-to-2025 (retrieved 2026-10-14).
- 2022: 2,310 attempts, 10,231 yards. 2023: 2,366 attempts, 9,840 yards. 2024: 2,352 attempts, 11,015 yards. 2025: 2,215 attempts, 9,686 yards. Four-year total 9,243 attempts, 40,772 yards (a second StatMuse page gave the same total and 4.4 yards per carry).
- Computed by me: yards per attempt 4.43, 4.16, 4.68, 4.37 for 2022 to 2025; 4.41 over four years. Attempts per team game (32 teams x 17 = 544 team games) 4.25, 4.35, 4.32, 4.07; yards per team game 18.8, 18.1, 20.2, 17.8. Quarterbacks are 15 to 16 percent of all rushing attempts (all-player totals 14,770, 14,606, 14,687, 14,601 attempts from https://www.statmuse.com/nfl/ask/league-average-yards-per-carry-by-year-2020-to-2025).
- The counts include scrambles and, as far as the source says, kneel-downs and sneaks (official stat rules count them as rushes; StatMuse does not state it). Sacks are not included.
- Cross-check: Parlay Savant table (https://www.parlaysavant.com/insights/why-rushing-qbs-essential-fantasy-football-dominance-2025, no named data source): QB rush attempts per game 8.33 (2022), 8.12 (2023), 8.27 (2024), 8.01 (2025, partly projected from week 11); QB rush yards per game 37.53, 35.53, 39.93, 36.74. Its "per game" is per NFL game (both teams together), roughly twice the per team game values above. The two sources agree within 3 percent.

Designed runs, scrambles and efficiency
- ESPN, Bill Barnwell, 2024-09-12 (https://www.espn.com/nfl/story/_/id/41217438/how-running-qbs-changed-nfl-dual-threat-history-value-scramble-stats-future; figures from ESPN tracking data and EPA data, not named NGS or nflfastR):
  - designed quarterback runs: 225 in 2009, 590 in 2023 ("more than doubled"); 37 in week 1 of 2024 (a 629-run pace).
  - Quarterback rushes in 2023 excluding sneaks, scrambles and kneel-downs: 0.16 EPA per rush; success rate "nearly 55%" against 43% for halfbacks.
  - Scrambles: "about 3%" of all offensive plays (1.7% in 2007); 2023 average scramble 0.31 EPA, 7.2 yards (6.8 in 2007), first-down rate 38.7% (36.6% in 2007); in 2023 quarterbacks scrambled for "nearly 7,400 yards" and 398 first downs. For comparison an average pass play gained 7.0 yards and 0.13 EPA, a non-scramble run -0.07 EPA.
  - Goal line: quarterbacks took 20 percent of carries inside the 5 in 2023 (10 percent in 2007); excluding sneaks and scrambles quarterback carries inside the 5 scored 60% of the time against 39.6% for backs.
  - Computed by me from the article's two totals: 7,400 / 7.2 gives about 1,030 scrambles in 2023 and 590 / 2,366 gives about a quarter of quarterback rushing attempts as designed non-sneak runs; the rest are scrambles, sneaks and kneel-downs. These two numbers come from different sources and definitions, so treat as a rough split.
- Scramble rate per dropback, Fantasy Footballers (Kyle Borgognoni, 2026-01-14, https://www.thefantasyfootballers.com/analysis/fantasy-football-25-qb-statistics-from-the-2025-season/): "Scramble rate = % of drop backs resulting in undesigned QB runs": 4.4% in 2020, 5.3% in 2024, 5.5% in 2025. The source of the data is not named.
- Sumer Sports (https://sumersports.com/players/quarterback/): scramble percentage (share of a quarterback's dropbacks where he "runs the ball past the line of scrimmage") 2022 to 2025 benchmarks across quarterbacks: median 4.70%, 25th percentile 3.07%, 75th 6.91%, 90th 9.06%. Different definition from the one above.
- PFF (Judah Fortgang, 2023-09-06, https://www.pff.com/news/nfl-data-study-components-quarterback-play-scrambling): PFF counts any time the quarterback begins to scramble, including ones that end in a sack or a pass; true scrambles are "only about 15%" of passing plays; EPA -0.15 per true scramble against -0.32 under pressure. Not directly comparable with the figures above.
- Yards per scramble in 2024 or 2025: not found.

Quarterback sneaks and tush pushes, 3rd or 4th and 1 unless stated
- League sneaks 2022 to 2026 (through about week 5 of 2026), regular season, charting "FTN Data via nflverse": 773 conversions of 972 attempts, 79.5 percent; counts a first down or a score; no public field tells whether teammates pushed, so this is a sneak rate (https://rollcoverage.com/tools/sneaks). No split by down or by distance on the page.
- Warren Sharp, X post of about 2025-02-24, seen only as a search snippet (the page returned HTTP 402): "QB sneak + tush push conversion rate on 3rd or 4th & 1 since 2022": Packers 92%, Eagles 90%, NFL average 84%, the 31 teams other than the Eagles 83% (https://x.com/SharpFootball/status/1894212512431673795). SRC-SECONDARY, snippet only.
- StatMuse X post, October 2023, snippet only: since 2022 Jalen Hurts 92.5% against 81.4% for the rest of the NFL (https://x.com/statmuse/status/1711124907172458830).
- FOX Sports, Greg Auman, 2025-05-22 (https://www.foxsports.com/stories/nfl/who-can-stop-eagles-tush-push-who-does-short-yardage-best): in 2024 about 1,200 plays on 3rd or 4th and 1 league-wide; teams ran on 78 percent; runs converted 74 percent and passes 57 percent (all runs, not sneaks). Quarterbacks on 3rd or 4th and 1 in 2024: Hurts 22 of 27, Allen 17 of 18, Nix 12 of 14, Daniels 12 of 12; 2023 Allen 24 of 27, Hurts 23 of 27; 2022 Hurts 25 of 29. No data source named.
- ESPN, Stephen Holder, 2025-09-16 (https://www.espn.com/nfl/story/_/id/46226517/nfl-eagles-chiefs-tush-push-brotherly-shove-jalen-hurts): since 2022 the tush push league average is 84.8 percent and the average non-tush fourth-and-1 play is 67.0 percent; the Eagles converted 96.6 percent of their fourth-and-1 tush pushes since 2022; Eagles 116 tush push attempts since 2022; Bills 51 of 57 (89.5 percent); Bears 16 attempts. Data source not named.
- ESPN, Mike Reiss and Kevin Seifert, 2026-02-23 (https://africa.espn.com/nfl/story/_/id/48010331/rich-mckay-expect-tush-push-ban-proposal-year): the NFL saw 112 tush pushes in 2025 against 101 in 2024; first down on 76.8 percent of attempts in 2025 against 82 percent in 2022 to 2024; Eagles (27) and Bills (17) "by far led the league in attempts" (the sentence's scope is unclear).
- Crossing Broad, 2026-02-24, citing tushpush.fyi (https://www.crossingbroad.com/news/eagles/no-proposal-to-ban-the-tush-push-this-offseason/): 2025 league 130 attempts, 96 successful, 73.8 percent; Eagles 33 attempts, 21 converted (64 percent); Bills 27 attempts, 21 converted (the article prints 89 percent, but 21 of 27 is 77.8 percent). NBC Sports Philadelphia (2026-02-22) agrees on Eagles 21 of 33 = 63.6 percent and says the Eagles were over 81 percent in 2024.
- The two 2025 counts conflict: ESPN 112 and 76.8 percent against tushpush.fyi 130 and 73.8 percent, and the Eagles' count 27 (ESPN) against 33. They use different definitions of a tush push and I could not retrieve the definitions (tushpush.fyi is a script-rendered page with no readable data). The league itself has published no count that I found. Use "about 75 to 77 percent, about 110 to 130 a year, 2025" as the honest range.
- McKay, 2026-03-25 (press report): traditional sneaks now succeed more often than tush pushes; no figures.
- Older sneak studies:
  - PFF, Ben Linsey, 2020-06-04 (https://www.pff.com/news/nfl-just-fall-forward-nfl-teams-qb-sneak-underutilized): sneaks converted 84 percent on average (five-year sample from 2015); sneaks were called on about 10 percent of 3rd or 4th and 1 plays, other designed runs 60 percent and designed passes 30 percent.
  - ESPN, Noah Davis and Michael Lopez, 2017-11-08 (https://www.espn.com/nfl/story/_/id/21158057/the-dying-art-qb-sneak), data 2001 to 2016: sneaking with 2 yards to go succeeded 73 percent, more than a non-sneak run or pass with 1 yard to go (65 percent); sneaks fell from 12.5 percent of short-yardage plays in 2001 to 4.8 percent in 2016 (figure via The Ringer's summary); league average 4.5 sneaks per team per 16 games.
  - Yale Undergraduate Sports Analytics Group, Green and Menz, fall 2015 (https://sports.sites.yale.edu/success-short-yardage-play-types-fourth-down), all 3,181 fourth-and-1 plays 1998 to 2015: sneaks 82.8 percent, non-quarterback runs 63.4 percent, passes 58.2 percent, all plays 65.7 percent; 4th and 2 sneaks 89.7 percent but only 29 of them.
  - The Ringer, Rodger Sherman, 2018-11-15 (https://www.theringer.com/2018/11/15/nfl/quarterback-sneak-short-yardage-play-calling-analysis), summarizing Football Outsiders, ESPN, PFF and the Wall Street Journal: sneak success roughly 70 to 90 percent; quarterbacks fumble on about 1.7 percent of sneaks (Football Outsiders).
- 3rd and 2 sneaks: very small samples (a Football Outsiders 2014 article is reported in a search summary as 7 uses, 5 conversions; its page now returns 404 so I could not verify). UNVERIFIED.

By down and distance
- A published table of yards per quarterback rush by down (1st, 2nd, 3rd, 4th) and distance (short, medium, long) does not exist in anything I could reach: StatMuse, Pro Football Reference, ESPN, PFF, Sumer, Fantasy Footballers, FOX and Sharp pages give only totals, scramble rates, or 3rd or 4th and 1 sneak rates. Building one needs the nflverse play-by-play files (not downloaded under the brief).
- Closest published figures: sneak and tush push 79.5 to 84 percent on 3rd or 4th and 1; all quarterback runs 4.4 yards per attempt; scrambles 7.2 yards per scramble and 38.7 percent first downs (2023); all runs on 3rd or 4th and 1, 74 percent (2024); non-sneak 4th and 1, 67 percent (since 2022); 2-yard sneaks about 73 percent (2001 to 2016).
- QB draws and bootlegs by type: no published split. Only the aggregate designed-run figure (0.16 EPA, success rate near 55 percent, 2023, ESPN) exists.

Fumbles and injury exposure
- Fumble on a sneak: about 1.7 percent (Football Outsiders via The Ringer, 2018). SRC-SECONDARY.
- Rushing-only quarterback fumble rate: not found. StatMuse list for all quarterbacks (https://www.statmuse.com/nfl/ask/total-quarterback-rushing-fumbles-and-fumbles-lost-by-season-2022-to-2025; I made up the slug, the page title that came back echoes it, so the scope is unsure; the totals look like all fumbles of all kinds): fumbles 297, 305, 292, 249 and fumbles lost 116, 140, 112, 109 for 2022 to 2025. Computed: 38 to 46 percent of quarterback fumbles are lost. UNVERIFIED as to scope, use only as a rough share.
- Injury: Injury Prone Newsletter (Edwin Porras, 2023-07-03, https://injurypronenewsletter.beehiiv.com/p/rushing-attempts-qb-injury-rates): "62%" of quarterback injury risk comes standing in the pocket and taking a hit; sacks and hits explain 62 percent of missed games; scrambles and designed runs have "minimal influence" on games missed (sample 195 quarterbacks, 2018 to 2022). The original paper was not found. SRC-SECONDARY.
- ESPN (2024 Barnwell article above) reports no injury or fumble rates.

### Flags against NFL_EXTRA_FEATURES.md section 8 and related lines

- Line 109 (a quarterback who tucks the ball and runs is a runner; passer protections apply while in the act of passing): by 3-27 any quarterback holding the ball is a runner; protections follow passing posture (12-2-9-a-1, 12-2-11), end when he becomes a runner (12-2-11-e), and are partly lost outside the pocket area (12-2-11-f). There is no "act of passing" definition. Rushes and yards count as rushing (Guide p. 11) unless the play is a sack.
- Line 110 (a runner who slides is down at the spot and may not be hit; contact is a foul, unnecessary roughness): the slide ends the play at the spot (7-2-1-d-2). Contact is a foul when the defender could have pulled up or when it is forcible to head or neck, or other unnecessary roughness; unavoidable contact by a defender who had already committed is not a foul (7-2-1 notes). The foul is 12-2-8-d. The kneel (7-2-1-c) is separate and quarterback-only. The penalty is 15 yards, automatic first down if by the defense.
- Line 111 and N3.1/N3.2: the 2026 term is "pocket area", not "tackle box". The grounding exception depends on where the pass lands (at or beyond the line of scrimmage extended), not on a "throw beyond the line".
- Line 112 (tush push decision 2025 to keep it legal; check 2026): confirmed. 2025 vote 22 to 10, 24 needed; 2026 no proposal, no vote; 12-1-4 unchanged. Add: the league has said it may still be discussed and a "pulling the runner" emphasis for 2026 officials was mentioned in February (not confirmed as issued).
- N3.1, QB Keeper "a sack-like loss chance": the official statistic for a designed keeper stopped behind the line is a rush for a loss, not a sack (Guide p. 11, p. 14 to 15). A sack is scored only after an apparent attempt to pass at or behind the line.
- N3.1, Scramble (called pass play that ends with the quarterback running): per the Guide, it is a rushing play once he crosses the statistical line of scrimmage; a scramble that ends behind the line after an apparent attempt to pass is a sack and the yards are deducted from team passing yards, not charged to his rushing.
- N3.3 (a fumble counts as a fumble lost when lost): matches the Guide's "fumbles lost" (Guide p. 25). On fourth down, after the two-minute warning and in a Try, a fumble recovered by a teammate other than the fumbler is dead at the spot (8-7-5, 8-7-6), a restriction the design must honor for keepers.
- C7 (quarterback runs and yards also counted in running plays and running yards, as in the NFL): matches the Guide; kneel-downs are rushing attempts with negative yards (reading); spikes are pass attempts, not rushes.
- Rule outline, last bullet (fumble and injury exposure): no official NFL number exists for a quarterback's rushing fumble rate (about 1.7 percent on sneaks, Football Outsiders) or injury rate per run; the one published analysis puts the injury risk mainly in the pocket (hits and sacks), not in runs.

### Could not settle

- The casebook (Approved Rulings). The operations.nfl.com rulebook page (https://operations.nfl.com/the-rules/nfl-rulebook/) lists only the rulebook PDF and a 2024 Record and Fact Book; no casebook link is on it, and a web search for the 2026 casebook found none. I read no approved ruling. Where this file says "reading", it is my reading of the rule text.
- The official 2026 proposals PDF (edge-operations.nfl.com) is a 404; the nfl.com article of the same list substitutes.
- The exact article text of the Packers' 2025 revised proposal (the league page and SI describe it only).
- A statistical rule that names the kneel-down or the spike (the Guide for Statisticians does not use either word).
- Yards per quarterback rush by down and distance; yards per scramble in 2024 and 2025; designed-run versus scramble totals for 2024 and 2025; rushing-only fumble rate; injury rate per play type; the definition behind tush push counts.
- Whether a 2026 officiating point of emphasis on pulling or carrying the runner was issued (searched, nothing found).
- Football Outsiders' 3rd-and-2 sneak counts (page 404).

### Sources (retrieved 2026-10-14 unless a date is given)

Official
- 2026 Official Playing Rules of the NFL (PDF): https://static.www.nfl.com/image/upload/fl_attachment/league/tqivdkzt9mu6wdgsh1ku.pdf (rules 3-12, 3-21, 3-24, 3-25, 3-27, 3-28, 3-38, 3-42, 4-3, 4-4, 4-7, 7-2, 8-1, 8-2, 8-7, 12-1, 12-2, 14-1 to 14-4, 15-3, 15-9, penalty summary).
- NFL Guide for Statisticians, copyright 2025, 38 pages: https://www.nflgsis.com/gsis/documentation/stadiumguides/guide_for_statisticians.pdf (fetched through the web tool, text extracted locally).
- nfl.com, playing rules, bylaw, resolution proposals for 2026: https://www.nfl.com/news/playing-rules-bylaw-resolution-proposals-for-2026-nfl-season
- nfl.com, approved 2026 rules: https://www.nfl.com/news/nfl-announces-new-playing-rules-bylaws-resolutions-for-2026
- nfl.com, tush push votes: https://www.nfl.com/news/nfl-owners-vote-against-banning-tush-push-play-at-spring-league-meeting ; https://www.nfl.com/news/vote-on-tush-push-rule-change-proposal-tabled-for-later-date ; https://www.nfl.com/news/packers-submit-revised-proposal-to-ban-tush-push-play-ahead-of-spring-league-meeting ; https://www.nfl.com/news/competition-committee-co-chairman-rich-mckay-doesn-t-expect-tush-push-ban-proposal-in-2026
- nfl.com player health and safety, rule changes since 2002: https://www.nfl.com/playerhealthandsafety/equipment-and-innovation/rules-changes/nfl-health-and-safety-related-rules-changes-since-2002
- Pittsburgh Steelers (league text of the approved changes), 2026-03-31: https://www.steelers.com/news/nfl-owners-approve-2026-nfl-rule-changes
- Not reachable: https://edge-operations.nfl.com/media/dxfj3uak/2026-playing-rules-bylaw-and-resolution-proposals.pdf (404); the Football Outsiders page (404).

Secondary (press, reference, analysis)
- ESPN, Barnwell, 2024-09-12: https://www.espn.com/nfl/story/_/id/41217438/how-running-qbs-changed-nfl-dual-threat-history-value-scramble-stats-future
- ESPN, Reiss and Seifert, 2026-02-23: https://africa.espn.com/nfl/story/_/id/48010331/rich-mckay-expect-tush-push-ban-proposal-year
- ESPN, Holder, 2025-09-16: https://www.espn.com/nfl/story/_/id/46226517/nfl-eagles-chiefs-tush-push-brotherly-shove-jalen-hurts
- ESPN, Davis and Lopez, 2017-11-08: https://www.espn.com/nfl/story/_/id/21158057/the-dying-art-qb-sneak
- NBC Sports PFT, 2026-03-25 and 2026-02-24: https://www.nbcsports.com/nfl/profootballtalk/rumor-mill/news/rich-mckay-no-proposal-to-ban-it-but-tush-push-still-has-some-people-concerned ; https://www.nbcsports.com/nfl/profootballtalk/rumor-mill/news/competition-committee-discusses-aiding-the-runner-but-no-proposals-to-ban-the-tush-push
- NBC Sports Philadelphia, 2026-02-22: https://www.nbcsportsphiladelphia.com/nfl/philadelphia-eagles/tush-push-no-rule-proposal-eagles-rich-mckay-competition-committe/717077/
- Crossing Broad, 2026-02-24: https://www.crossingbroad.com/news/eagles/no-proposal-to-ban-the-tush-push-this-offseason/
- Steelers Now, 2026-03-26: https://steelersnow.com/here-to-stay-no-discussion-on-banning-tush-push-in-2026/ (contains the "eight teams short" error)
- Sports Illustrated, 2025-05-20: https://www.si.com/nfl/packers-submit-revised-tush-push-proposal-voting-nfl-owners-meeting
- FOX Sports, Auman, 2025-05-22: https://www.foxsports.com/stories/nfl/who-can-stop-eagles-tush-push-who-does-short-yardage-best
- PFF, Linsey, 2020-06-04: https://www.pff.com/news/nfl-just-fall-forward-nfl-teams-qb-sneak-underutilized
- PFF, Fortgang, 2023-09-06: https://www.pff.com/news/nfl-data-study-components-quarterback-play-scrambling
- PFF, Jahnke, 2011-03-22: https://www.pff.com/news/stat-sheet-misconceptions-completion-percentage
- The Ringer, Sherman, 2018-11-15: https://www.theringer.com/2018/11/15/nfl/quarterback-sneak-short-yardage-play-calling-analysis
- Yale Undergraduate Sports Analytics Group, fall 2015: https://sports.sites.yale.edu/success-short-yardage-play-types-fourth-down
- Roll Coverage sneak tracker (FTN data via nflverse): https://rollcoverage.com/tools/sneaks
- StatMuse pages: https://www.statmuse.com/nfl/ask/total-quarterback-rushing-attempts-and-yards-by-season-2022-to-2025 ; https://www.statmuse.com/nfl/ask/league-average-yards-per-carry-by-year-2020-to-2025 ; https://www.statmuse.com/nfl/ask/total-quarterback-rushing-fumbles-and-fumbles-lost-by-season-2022-to-2025
- Parlay Savant: https://www.parlaysavant.com/insights/why-rushing-qbs-essential-fantasy-football-dominance-2025
- Fantasy Footballers, 2026-01-14: https://www.thefantasyfootballers.com/analysis/fantasy-football-25-qb-statistics-from-the-2025-season/
- Sumer Sports: https://sumersports.com/players/quarterback/
- Injury Prone Newsletter, 2023-07-03: https://injurypronenewsletter.beehiiv.com/p/rushing-attempts-qb-injury-rates
- Wikipedia (reference only): https://en.wikipedia.org/wiki/Quarterback_kneel ; https://en.wikipedia.org/wiki/Quarterback_sack


## Part 5. Kickoffs, onside kicks and the free kick after a safety

Written 2026-10-14 (2026 season in progress). Research only.
Main authority: the 2026 Official Playing Rules (the PDF converted to text, retrieved 2026-10-14).
Citations are Rule-Section-Article with the PDF page (the printed page is the PDF page minus 7).
Tags: SRC-OFFICIAL, SRC-SECONDARY, UNVERIFIED (as defined in Part 1.1).
Where I read the rulebook and then drew a conclusion, the line says "reading" so the builder can tell text from inference.

### Answers in brief

1. The 2026 onside kick rule (6-1-6, PDF 30): the kicking team may declare an onside kick at any time during the game. SRC-OFFICIAL.
2. Is the kicking team still required to be trailing? No. The 2026 book has no score condition anywhere in Rule 6 (word "trailing" appears nowhere in Rule 6 or 16). Winning, tied or losing may declare. SRC-OFFICIAL (text); the scorecard line "an onside kick by a team that is not trailing" PASSED is SRC-SECONDARY.
3. Declaration: the kicking team notifies the Referee before the 25-second play clock starts (that clock starts after an official hands the kicker the ball); the Referee tells the receiving team before starting the clock. SRC-OFFICIAL.
4. Declared kick that is not really an onside kick: if it goes untouched beyond the onside setup zone it is an unsportsmanlike conduct foul: 15 yards from the kicking team's restraining line, receivers get the ball. SRC-OFFICIAL (6-1-6 penalty). An onside kick WITHOUT a declaration: no rule text and no penalty line in the book. UNVERIFIED (casebook not reachable).
5. Kick spots (2026): kickoff 35 (own); safety kick 20 (own); an onside kick uses the same line, 35 or 20. The number 34 appears nowhere in the 2026 book. SRC-OFFICIAL. Press reports of 2025 say "34"; see the flag section. SRC-SECONDARY.
6. Free kick after a safety: by the team scored upon, from its own 20; punt, drop kick or place kick; tee allowed; an onside kick is allowed there under the same declaration rule (6-1-6(b) names the 20-yard line for a safety kick). SRC-OFFICIAL.
7. Kickoff rule history by year (2024, 2025, 2026): section 5. 2024 steps SRC-OFFICIAL (NFL.com page of 2024-09-05); 2025 and 2026 steps: the 2026 book itself is SRC-OFFICIAL, the 2025 details SRC-SECONDARY.
8. Fouls tied to kicks, with yards and enforcement: section 4. SRC-OFFICIAL.
9. Statistics: onside recoveries 2018 to 2025 found (SRC-SECONDARY); 2026 onside data NOT found; split into expected versus surprise only for 2018 to 2019 (and pre-2018); touchback and return figures 2023 to 2025 found, 2026 only the first two weeks (returns, not touchbacks). Section 6.
10. Contradictions in section 9 of the requirements file: section 7 of these notes (the "34" kick spot, the unsettled trailing condition, the 6.45 percent figure, the "spot of the foul or the touch" line, and an overtime item in NQ4).

### 1. The onside kick, 2026 rulebook

#### 1.1 Who may declare, when, how (6-1-6 lead-in, 6-1-1(c); PDF 29 and 30) SRC-OFFICIAL
- "At any time during the game" the kicking team may declare an onside kick.
- It does so by telling the Referee before the start of the play clock (the 25-second clock that runs after the game official hands the kicker the ball).
- The Referee then tells the receiving team, and only then starts the play clock.
- 6-1-1(c): an onside kick is the form of free kick that the kicking team must declare to the officials; a holder may be used.
- Reading: because the receiving team is always told first, no surprise onside kick exists any more. The "surprise" statistics of earlier years do not apply (section 6.4).
- Reading for N4.1: in 2026 the question can be asked at EVERY free kick of the game: opening kickoff, second half, after each score (the scoring team kicks), after a safety, overtime opening kick (3-17-1 lists the start of overtime as a kickoff, PDF 13). The question has to be answered before the kick play begins.

#### 1.2 No score condition (checked) SRC-OFFICIAL
- I searched the whole book for "trailing", "behind in the score", "fourth period" next to any onside text. The only hits are unrelated (replay challenge, clock rules).
- The 2026 change list on PDF 2 reads: permits the kicking team to declare an onside kick at any time during the game.
- NFL.com (www.nfl.com/news/nfl-announces-new-playing-rules-bylaws-resolutions-for-2026, retrieved 2026-10-14) lists it as an approved playing rule "By Competition Committee". SRC-OFFICIAL. It gives no rationale.
- Why the committee did it: Rich McKay, quoted on the Rams site (2026-03-31): after a penalty enforcement on a try, a team may have the kick moved to the 50, and teams asked why they could not kick onside there. He said the old rule allowed it only if behind or tied. SRC-SECONDARY.
- Football Zebras (2026-04-07) lists the rule on its scorecard as "Allow an onside kick by a team that is not trailing in score": PASSED. SRC-SECONDARY.
- The sunset ("self-destruct") language Football Zebras mentions belongs to a different rule (the replay assist for referee lockouts, 19-2 area), not to 6-1-6. SRC-SECONDARY; the 6-1-6 text in the book has no sunset.

#### 1.3 Kick spot and alignment of the kicking team (6-1-6(b)-(d); PDF 30) SRC-OFFICIAL
- Restraining line for the kicking team on an onside kick: its own 35 (or its own 20 for a safety kick), unless moved by a distance penalty.
- Every kicking player except the kicker and the holder: front foot on that line, both feet on the ground until the ball is kicked.
- At most five players on either side of the ball, and the holder counts as one of the five on his side.
- On each side of the ball at least two players (not counting a holder) inbounds between the sideline and the outside edge of the yard-line number, and at least two between the inside edge of the number and the inbounds line.
- All kicking players must be inbounds and behind the ball when it is kicked.
- Kicker and holder: the holder of a place kick may be beyond the line; the kicker may be beyond the line if his kicking foot is not (6-1-6(d), 3-19 offside definition, PDF 14).
- Tee and holder rules (6-1-1 note, PDF 29): a tee up to one inch high; a holder may be used on an onside kick; on an onside kick only, the ball may lean against the tee on the ground.
- Kick type: nothing in 6-1-6 restricts it. 6-1-1(a) lets a kickoff be a drop kick or place kick; 6-1-1(b) lets a safety kick be a drop kick, place kick or punt. Reading: the same type limits apply to an onside kick from those two situations. UNVERIFIED (no casebook).

#### 1.4 Alignment of the receiving team (6-1-6(g),(h); PDF 30) SRC-OFFICIAL
- Receiving team restraining line: the yard line 10 yards in advance of the kicking team's line.
- Until the ball is kicked, all receivers inbounds and behind that line, with at least eight and at most nine of them in the onside kick setup zone: the 15 yards behind their restraining line.
- Reading (numbers): measured from the kicking line the zone spans 10 to 25 yards downfield. A kick that nobody touches beyond 25 yards is "beyond the setup zone".
- The 2021 one-year trial that capped the zone at nine is now simply the text (history: section 5; SRC-SECONDARY).

#### 1.5 When the kicking team may touch or recover (6-1-6(e),(f); 6-2-5; PDF 30, 31, 32) SRC-OFFICIAL
- Legal for the kicking team to touch, catch or recover only if the ball (1) first touches a receiving player, or (2) reaches or crosses the receiving team's restraining line (the 10-yard rule).
- A touch by a player who was batted or illegally kicked into does not count as touching (note 1).
- Player who went out of bounds (6-2-5 item 2): he may not touch or recover the ball beyond the receivers' restraining line until a receiver has touched it; if he touches it before getting back inbounds it is a free kick out of bounds.
- If the kicking team recovers legally the ball is dead at the dead ball spot and belongs to the kicking team (6-1-6(f)); it is a new series, first down for the kicking team (7-3-1(e), PDF 34; 7-2-1(j), PDF 33).
- In overtime (16-5-c, PDF 72): a legal recovery by the kicking team counts as the receiving team's opportunity to possess, so the receivers have used their possession.

#### 1.6 Results, spot by spot (all SRC-OFFICIAL text; the "reading" lines are my arithmetic)
- Receiving team catches or recovers: may advance (6-1-6(i)).
- Ball comes to rest and nobody tries to possess it: dead, receivers' ball at the dead ball spot (6-1-6(j)).
- Goes untouched beyond the setup zone: ball dead, receivers' ball (6-1-6(k), 7-2-1(l)), AND an unsportsmanlike conduct foul: 15 yards "from the kicking team's restraining line", receiving team takes possession (6-1-6 penalty, PDF 31; listed in the penalty summary, PDF 79 as "Loss of Fifteen Yards from the Kicking Team's Restraining Line").
  - Reading: the ball is spotted 15 yards back from the kicker's line toward the kicker's goal: the kicking team's 20 after an onside kick from the 35; the half-distance rule (14-2-1, PDF 62) shortens it for a safety-kick onside (from the 20 the half distance is 10, so the kicking team's 10). The text does not say this outright. UNVERIFIED reading; the casebook would settle it.
- Kicking team touches too early (before the ball reaches the receivers' line and before a receiver touches it): foul, 6-2-5 item 1: loss of five yards, OR the receiving team takes possession at the spot of the illegal touch. Reading: the choice belongs to the offended team (14-1-1, PDF 61, penalties may be declined by the offended team). With the five-yard option the kick is made again from the new previous spot (6-3-1).
- Onside kick goes out of bounds: it is a "free kick out of bounds" (6-2-4, PDF 32). The kicking team may not kick it out of bounds nor be the last to touch it before it goes out. The receiving team may elect: 25 yards from the kick spot at the inbounds line on that side (30 for a safety kick), or the out of bounds spot, or the spot where it landed or was touched if that is less than 25 yards. Reading: the receivers will always pick the best, so their ball is at (kick spot plus the smaller of the out of bounds distance and 25 yards), or 30 for a safety kick. Example: onside kick from the 35 that goes out at 12 yards: receivers' ball 12 yards from the kick, the kicking team's 47. UNVERIFIED reading of "at the out of bounds spot"; the penalty summary lists only "inbounds spot" and "25 yards from spot of kick" for a kickoff.
- Offside, out of bounds when kicked, illegal formation by either team (6-1-6 penalty, PDF 31): loss of five yards (kick made again, 6-3-1).
- Blocking on an onside kick: 6-2-2 (PDF 31): kicking team may not block or use hands against an opponent between the restraining lines until the ball is legally touched, nor at or within five yards beyond the receivers' line until the ball is legally touched or touches the ground; receivers may not initiate blocks in the first 15 yards (from the kicking line to five yards behind the receivers' line) until the ball is legally touched or hits the ground. Penalty: 10 yards. Wedge and double-team limits apply too (15 yards).

#### 1.7 Declared but not an onside kick, and the reverse
- Declared and then kicked deep: the "untouched beyond the setup zone" penalty above is the written answer. SRC-OFFICIAL.
- Declared and kicked as a normal kick that a receiver touches inside the zone: no penalty text. It is simply an onside kick that the receivers recovered. Reading.
- Not declared, but kicked short or in an onside formation: the book has no sentence. The receiving team would be lined up as for a kickoff, so the kicker's alignment would break 6-1-3 (kickoff formation: all ten others on the receivers' 40), an illegal formation: five yards, kick made again (6-1-3 penalty, PDF 30). UNVERIFIED reading.
- Suggestion for the game: no path exists for an undeclared onside kick, so the question never arises. The computer declares first, always.

### 2. Kickoffs and the safety kick in the 2026 rulebook

#### 2.1 What a free kick is (6-1-1, 3-17; PDF 13 and 29) SRC-OFFICIAL
- Free kick: kickoff, safety kick, or onside kick. A kickoff starts each half, overtime, follows a Try and follows a successful field goal (the team that scored kicks). After a safety the team scored upon kicks (11-5-2, PDF 51).
- Illegal free kick: loss of five yards.

#### 2.2 Lines and zones, kickoff and safety kick (6-1-2, PDF 29) SRC-OFFICIAL
- Kicker's restraining line: the kicker's own 35 (kickoff) or own 20 (safety kick), moved by any distance penalty.
- Kicking team's line for the other ten players: the receiving team's 40-yard line (the same for a safety kick).
- Receiving team's restraining line: its own 35. Setup zone: its 35 to its 30. Landing zone: from its 20 to its goal line.

#### 2.3 Formation (6-1-3, PDF 29 and 30; the 2026 change) SRC-OFFICIAL
- Kicking team: inbounds, front foot on the line, both feet on the ground; at least two between the sideline and the outside of the number, at least two between the inside of the number and the inbounds line, at least two inside the inbounds lines. The kicker may be past the line if his kicking foot is not; after the kick he may not cross the vicinity of the 50 until the ball touches the ground or a player in the landing zone or end zone.
- Receiving team (new in 2026): at least nine in the setup zone; at least five with a front foot on the 35 (six if more than nine are in the zone), among them at least one in the middle (between the inbounds lines), and on each side at least one between the inside of the number and the inbounds line and at least one between the sideline and the outside of the number; at most four more in the setup zone off the line, never more than two in each of the three areas bordered by the sidelines and inbounds lines (and if there are four, at least one between the sideline and inbounds line on each side); at least three outside the inbounds line on each side; anyone outside the zone stays behind the 20 until the kick and behind the 30 until the ball lands or is touched in the landing zone or end zone.
- Penalty (6-1-3): offside, out of bounds, illegal formation by either team, early movement by kickers (other than the kicker) or by receivers in the setup zone, or the kicker going more than 15 yards before allowed: loss of five yards.

#### 2.4 Catch or recovery; kicking team touching (6-1-4; PDF 30) SRC-OFFICIAL
- Receivers may advance a catch or recovery in the landing zone or inbounds in the end zone.
- The kicking team may touch, catch or recover only after the ball lands or is touched by a receiver in the landing zone or end zone. A legal catch or recovery by the kickers is a dead ball at that spot, kickers' ball.
- Ball first touching the ground or a player short of the front line of the landing zone: dead (7-2-1(k), PDF 33); receivers' option under 6-2-4 (below).
- Ball at rest in the landing zone or end zone with nobody going for it: dead, receivers' ball.
- Dead ball in the end zone, or out of bounds in the end zone: touchback.

#### 2.5 Touchback spots (6-1-5, PDF 30; 11-6-3, PDF 51) SRC-OFFICIAL
- Touchback to the 20 if the kick touched the ground or a player in the landing zone and is then downed in the end zone or goes out behind the goal line.
- Touchback to the 35 if the kick, without touching the ground or a player in the landing zone, goes out behind the goal line, hits the goal post or crossbar, or lands at or past the goal line and is downed in the end zone.
- 2026 change: "in either case", if the kickoff came from the 50, a touchback is placed on the 20. (Reading: a kick from the 50 happens when a 15-yard penalty on the receiving team, for example a personal foul enforced on the kickoff, moves the kicker's line forward from the 35; McKay's remark about a penalty after a try fits this.)
- Same spots apply to a safety kick.
- Free kick out of bounds or short: 6-2-4, section 2.6. 25 yards from the kick for a kickoff gives the 40 for a kick from the 35; 30 yards for a safety kick gives the 50 for a kick from the 20.
- A touchback on the 35 or 20 is where the receivers next snap, anywhere between the inbounds lines (11-6-3).

#### 2.6 Kick out of bounds or not reaching the landing zone (6-2-4, PDF 32) SRC-OFFICIAL
- The kicking team may not kick out of bounds between the goal lines, nor be last to touch the ball before it goes out, nor kick a ball that first touches the ground or a player short of the landing zone's front line.
- Receivers' options: 25 yards from the kick spot (30 for a safety kick) at the inbounds line on that side; or the out of bounds spot; or the landing or touch spot if it is less than 25 (30). Foul codes KOB and LZ, signal 9.
- Reading: the receivers' ball is at (kick spot plus the smaller of the distance travelled and 25, or 30 for a safety kick).

#### 2.7 Safety kick (11-5-2, 6-1-1(b), 6-1-2(a); PDF 51, 29) SRC-OFFICIAL
- The team scored upon puts the ball in play from its own 20 (unless 4-8-2-g extends a half: a safety kick is made if the receivers request it).
- It may punt, drop kick or place kick; an artificial or manufactured tee may be used.
- The 25 and 30-yard out of bounds numbers above use 30 for a safety kick.
- An onside kick on a safety kick is allowed (6-1-6(b): line is the 20).

#### 2.8 Overtime kick (Rule 16; PDF 72 and 73) SRC-OFFICIAL
- The overtime period starts with a kickoff (3-17-1). It is a normal free kick: normal alignment, normal onside rule (any time).
- 16-3 (regular season): 10-minute period, both teams get the ball at least once unless the kicking team scores a safety on the receivers' first possession (then the kickers win); after that sudden death; a tie is possible. Each team has two timeouts.
- 16-4 (postseason): 15-minute periods, same possession rule, three timeouts per half.
- 16-5-c: an onside kick that the kicking team legally recovers uses up the receivers' possession.
- 16-5-d: no coach's challenges in overtime (the replay official starts all reviews).

### 3. Clock rules around free kicks (Rule 4)

- 4-3-1 (PDF 18) SRC-OFFICIAL: the game clock starts after a free kick when the ball is legally touched in the field of play. It does NOT start if (a) the receivers touch or recover it in the end zone and do not carry it into the field of play, (b) the kicking team recovers it in the field of play before any other legal touching (an onside recovery by the kickers), or (c) the receivers make a fair catch.
- 4-4(a) (PDF 19): the clock stops at the end of any down in which there is a free kick. (d): stops when the ball is dead on or behind a goal line (touchback).
- 4-6-2 (PDF 20, 21): the play clock is 25 seconds in these cases: a free kick after a television timeout; a free kick without one (after a Try or field goal teams have 40 seconds to align before the Referee's whistle, then 25 seconds). Also after a change of possession, a timeout, the two-minute warning, a penalty enforcement.
- 4-2-1(a) (PDF 18): delaying the start of a half: 15 yards from the kickoff spot of 6-1-2-a.
- 4-8-2(b)(1),(5) and (g) (PDF 22): a period may be extended by an untimed down; a safety kick is made if the receivers ask after a half-ending safety.
- Builder's reading for C2: a touchback or an onside recovery by the kickers costs no clock; a returned kick starts the clock when first legally touched (ball touched in the field of play), and the down ends with the whistle, after which the clock stops (4-4(a)).

### 4. Fouls tied to free kicks

#### 4.1 Enforcement of a foul on a free kick (6-3-1, PDF 32; 14-4-7, PDF 64) SRC-OFFICIAL
- General rule: from the previous spot, and the free kick is made again.
- Option rule: if the kicking team fouls before the end of the kick, or the receiving team fouls at or during a kickoff or safety kick, and the receiving team keeps possession through the down, the offended team may either enforce at the previous spot and replay the down, or enforce the yardage from the dead ball spot. The dead ball spot after a touchback is the 20 or the 35 (6-1-5).
- Exceptions: after-fair-catch-signal personal foul, fair catch interference, interference with the opportunity to catch, invalid fair catch signal and illegal double team or wedge blocks are enforced from the spot of the foul (or the previous spot if in the receivers' end zone, or during an onside kick). For those, if the foul is not part of a double foul and the opponent holds the ball at the end, the foul may be enforced from the dead ball spot (14-2-4).
- Out of bounds or short: 6-2-4. Illegal touching: 6-2-5.
- Any penalty may be declined by the offended team (14-1-1, PDF 61).
- Half-distance rule applies (14-2-1, PDF 62).
- Personal fouls and unsportsmanlike conduct on a play in which the opponent scores a field goal or safety: enforced on the succeeding free kick (14-2-3, PDF 62). After a touchdown they go to the Try, and a Team B foul on a successful Try may be enforced on the next kickoff. Dead ball personal fouls after the end of the second or fourth period are enforced on the second-half kickoff or the overtime kickoff (14-4-9, PDF 65).
- Double fouls on a free kick: 14-5-2 (PDF 66): if the kicking team fouled before the change of possession, the receivers may elect to replay the down.

#### 4.2 The foul list with yards (Rule 6, 10, 12 and the penalty summary, PDF 78 and 79) SRC-OFFICIAL
- Illegal free kick (6-1-1): 5 yards.
- Offside on free kick (code OFK), player out of bounds when kicked, illegal formation by either team, early movement by kickers or setup-zone receivers, kicker too far before allowed (6-1-3, 6-1-6): 5 yards.
- Illegal blocking or use of hands on a kickoff, safety kick (6-2-1) or onside kick (6-2-2): 10 yards.
- Illegal double team block or illegal wedge (6-2-1, 6-2-2): 15 yards. Enforced from the spot of the foul if during the kick; as usual if during the return; from the previous spot if in the receivers' end zone during the kick or on an onside kick.
- Running into the free kicker (6-2-3, PDF 32): 5 yards. Other contact with the kicker: unnecessary roughness, 15 yards (12-2-8(i), PDF 55: a kicker standing still or fading is out of the play). Roughing the kicker/holder (12-2-12 and 12-2-13, PDF 56, 57) is written for kicks from behind the line of scrimmage: 15 yards plus automatic first down; "running into the kicker" there is 5 yards.
- Free kick out of bounds or not reaching the landing zone (6-2-4): receivers' option as in 2.6. Codes KOB and LZ.
- Illegal touching by the kicking team (6-2-5 item 1, item 2; code ITK and POK): 5 yards; on an onside kick also the option of the receivers' ball at the spot of the touch.
- Kicking team player voluntarily out of bounds to avoid a block (6-2-6): 5 yards.
- Onside kick untouched beyond the setup zone (6-1-6): 15 yards from the kickers' line and the receivers' ball (unsportsmanlike conduct).
- Kicking team player out of bounds who does not try to return inbounds (12-3-1(u), PDF 58): unsportsmanlike conduct, 15 yards.
- Receivers blocking a kicker's player out of bounds (12-2-8(c), PDF 54): unnecessary roughness, 15 yards.
- Kick catch interference (10-1-1(a), PDF 47): loss of 15 yards from the spot of the foul and the receivers may put the ball in play by a snap from scrimmage. Fair catch interference (10-1-1(b)): 15 yards, fair catch awarded; listed in the summary as "loss of ball and 15 yards". Interference applies to free kicks as well as scrimmage kicks.
- Invalid fair catch signal (10-2-2): 5 yards; illegal block after a fair catch signal: 15 yards (from the previous spot in the receivers' end zone during a free kick or on an onside kick, PDF 47).
- Delay of kickoff (4-2-1, DOK): 15 yards from the kickoff spot. Delay of game before the kick (4-6): 5 yards.
- A fair catch can be made on a free kick that has not touched the ground (definition 3-9; 10-2-1).

### 5. Rule history by year (for the versioned data table)

Pre-history, brief (SRC-SECONDARY): the running start was banned for kickoffs in 2018 (CBS Sports 2024-12-13), the main reason onside recoveries fell; a one-year trial in 2021 capped the receivers' onside setup zone at nine players (NFL Football Operations, quoted by search 2026-10-14; page itself returned 404 to my fetch).

2024 season (dynamic kickoff), SRC-OFFICIAL for the content (NFL.com, "2024 NFL Season: Explaining rules for new dynamic kickoff", 2024-09-05, https://amp.nfl.com/news/2024-nfl-season-explaining-rules-for-new-dynamic-kickoff, retrieved 2026-10-14):
- Kick from the 35. The other ten kickers stand with a foot on the receivers' 40, nobody moves until the ball touches the ground or a player in the landing zone or end zone.
- Landing zone: receivers' goal line to the 20; two returners allowed there. Setup zone: 30 to 35, nine receivers, seven with a foot on the 35, two outside the hash marks.
- Kick that lands in the landing zone and goes into the end zone, downed: touchback to the 20. Kick that lands in the end zone and is downed, or goes out the back: touchback to the 30. Short of the landing zone or out of bounds: receivers at the 40.
- Onside kicks: only in the fourth quarter, only while trailing, declared to the officials beforehand.
- Adopted 2024-03-26, vote 29 to 3, for one year only (ESPN 2024-03-26 / Orlando; SRC-SECONDARY).

2025 season, SRC-SECONDARY (team sites relaying the league's text, news; the 2025 rulebook itself was not reachable):
- April 1, 2025 annual meeting (Palm Beach; Rams site 2025-04-01 and Raiders site 2025-04-01): dynamic kickoff made permanent; touchback after a kick that reaches the end zone moved from the 30 to the 35 (the landing-zone-then-end-zone touchback stays at the 20); alignment of receivers in the setup zone modified. Search tool quoting NFL Football Operations' explainer: at least nine in the zone, at least six on the 35, at most three off the line, never more than one in each of the three areas.
- The onside kick proposals (kicking-team alignment; declare at any time if trailing) were tabled in April and passed on 2025-05-21 at the Minneapolis meeting (SI live blog, 2025-05-21; American Football International 2025-05-22; Steelers Depot 2025-05).
- The official 2025 change list (operations.nfl.com, quoted by search tool, the page now shows the 2026 list): 6-1-5 changes the touchback spot to the 35; 6-1-6 modifies the kicking team's alignment on an onside kick and permits the kicking team to declare one at any time if trailing its opponent.
- McKay (2026-03-31): the 2025 rule let you kick onside "only if behind or tied" (his words); every other source says trailing. I treat "trailing" as the 2025 text and flag the difference.
- The alignment change (kicking team players one yard closer): press says either "kick from the 34" (SI live blog; American Football International; CBS 2025-09-03) or "kicking line on the 35 instead of the 34" (Deseret News 2025-08-08: ten players with foot on the 35). The 2026 book says 35 for everyone. See flags.

2026 season, SRC-OFFICIAL (the book, PDF 2, 29 to 31) and SRC-SECONDARY for the story (Steelers site 2026-03-31, Rams site 2026-03-31, CBS Sports 2026-03-31; NFL.com announcement page, retrieved 2026-10-14):
- Approved 2026-03-31 at the annual meeting in Phoenix, all three "By Competition Committee":
  - Rule 1, 6-1-6: declare an onside kick at any time during the game (no score condition).
  - Rule 2, 6-1-5: kickoff from the 50 that ends in a touchback is spotted on the 20 (removes the incentive to kick it out of bounds from the 50; the case was Dallas against Kansas City in 2025, CBS Sports).
  - Rule 3, 6-1-3: receivers' setup zone: minimum with a front foot on the line five instead of six; up to four off the line instead of three; no more than two per area (Rams site; the book confirms five and four).
- Committee reason for the setup-zone change, per the Panthers site (2026-04-01): player safety and more spark in kickoff returns. SRC-SECONDARY.

Suggested fields for the data table `nfl_rules_<year>` (my suggestion, not rulebook text):
- kickoff_spot, safety_kick_spot, onside_spot_equals_kick_spot (all true in 2026)
- onside_allowed_when: "any time" (2026), "trailing any time" (2025), "trailing 4th quarter" (2024)
- onside_declare_required: true (2024 to 2026)
- touchback_spots: landing_zone_then_end_zone 20; direct_into_end_zone_or_out_back 35 (2025, 2026), 30 (2024); from_the_50 20 (2026)
- out_of_bounds_or_short: receivers' ball at min(distance, 25), 30 for a safety kick
- onside_min_distance 10; onside_setup_zone_end 25 (measured from the kicking line)
- onside_recovery_probability (data with source and year, section 6)

### 6. Statistics (all SRC-SECONDARY unless said; retrieved 2026-10-14; no data files downloaded)

#### 6.1 Onside kick recoveries by the kicking team, regular season
- 2000 to 2017: 19.5 percent (CBS Sports, Jonathan Jones, 2025-10-22: https://www.cbssports.com/nfl/news/nfl-plans-to-boost-onside-kick-success-rate-after-all-time-low-excitement). 2001 to 2017 average 19.7 percent, and 2017 alone 21.1 percent (ESPN, Kevin Seifert, 2019-03-19).
- 2018: 4 of 52, 7.7 percent. 2019: 8 of 62 (FanDuel/Football Database) or 8 of 63, 12.7 percent (NFL Research via NFL.com). 2020: 3 of 67, 4.4 percent. 2021: 9 of 56, 16.1 percent. 2022: 3 of 56, 5.3 percent. Source for 2018 to 2022: FanDuel table crediting The Football Database (http://www.fanduel.com/research/theduel/history-of-onside-kicks-in-the-super-bowl-recent-attempts-successes-stats-01gr4a49de0r, updated "Sep 10", year not shown; its text mixes 2022 and 2022-23).
- 2018 to 2023 combined: 8.7 percent (CBS, Jones, 2025-10-22).
- 2023: 41 attempts and 4.9 percent, i.e. 2 recoveries (Badger Bracketology, Laura Albert, 2025-01-27). Other sources give 5.2 or 5.6 percent partial-season figures. 2023 is the least settled year.
- 2024: 3 of 50, 6.0 percent (Albert 2025-01-27; CBS Jones 2025-10-22; USA Today/AOL 2026-03-31 citing The Football Database). A mid-season CBS count was 3 of 41 (2024-12-13).
- 2025: 5 of 52, 9.6 percent (USA Today, Jacob Camenker, 2026-03-31, citing The Football Database: https://www.aol.com/articles/nfl-kickoff-rules-2026-league-213518217.html). Mid-season count: 1 of 21 (CBS 2025-10-22); Troy Vincent on 2025-10-21 said the recovery rate was under 5 percent (AP).
- 2026 to date: NOT FOUND (section "Could not settle").

#### 6.2 Expected versus surprise kicks
- Available only up to 2019. NFL Football Operations (via ESPN 2019-03-19): expected onside kicks in 2018 were recovered 8 percent of the time, in line with earlier years; surprise attempts and their success both fell.
- NFL Next Gen Stats / Football Operations article of October 2019 (quoted by search tool; my fetch of the page returned 404): since the start of 2018 the kickers recovered 6.1 percent of non-surprise attempts, below a historical 12 percent; surprise attempts averaged 9.4 a year from 2010 to 2017 and only five in 2018.
- Blog analysis (Bruin Sports Analytics, nflfastR, pre-2018): about 11 percent when expected, about 42 percent in surprise situations (win probability under 80 percent). Not verified; the sample and definitions are the blog's own.
- Since 2024 every attempt is declared, so every attempt is an "expected" kick. The relevant rate is the 6.0 to 9.6 percent of 2024 and 2025.
- The league would like about 12 percent (CBS 2025-10-22, unnamed sources).

