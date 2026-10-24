#### 6.3 Distance and recovery spot
- No public average distance or recovery spot found. I looked at NFL Football Operations articles (404 on fetch), ESPN 2019, CBS, blogs.
- What the rule gives: the kicking team cannot legally touch before 10 yards (the receivers' line); the receivers' 8 to 9 setup players sit in the 10 to 25 yard band; so a recovery is always at 10 yards or more, except when a receiver touched it earlier. ESPN 2019 notes the kicker aims at 11 to 12 yards (Butker). SRC-SECONDARY color, not a statistic.

#### 6.4 Attempts by quarter and margin; early 2026
- Total attempts barely moved when the 2025 rule allowed any quarter: 50 in 2024, 52 in 2025.
- No source found that splits 2025 or 2026 attempts by quarter or margin. None found with a count of early 2026 attempts, or of attempts while leading or tied.
- Anecdotes from 2026 (not statistics): week 3 and week 4 games had late-game onside attempts that receivers won (Ravens and 49ers) and at least one with an unclear outcome (Raiders against Chiefs); all were trailing teams late. Source: search results of 2026-10-14 (Yahoo live blog and ESPN recap titles); I did not read the games. UNVERIFIED.
- Expectation from the rule makers: the McKay quote suggests the main intended use is after a penalty moved a kickoff to the 50.

#### 6.5 Kickoff results (return rate, touchbacks, start spot)
- 2023: return rate 21.8 percent (record low), 332 returns, touchback 73.0 percent (NFL via SI/other, search result; touchback figure for 2023 from the search summary; SRC-SECONDARY).
- 2024: return rate 32.8 percent, 919 returns, touchback 64.3 percent (ESPN, Kevin Seifert, quoted by SI "What Final Data From 2024 Season Shows About Impact of NFL's New Kickoff Rules"; Sharp Football Analysis gives 64.4). Average start after all kickoffs 30, after a return 29 (NFL, quoted by SI); PFF says 30.0 after returns, a different definition.
- 2025 (touchback to the 35): return rate 75.9 percent for the season, 2,076 returns (PFF, 2026-03-03: https://www.pff.com/news/nfl-kickoffs-are-evolving-as-returns-surged-in-2025; Sharp Football Analysis, Rich Hribar, 2026-07-13: 2,076 returns). Touchback rate 20.7 percent for the season; average start 30.8 for the return team (Sharp, same article, https://www.sharpfootballanalysis.com/?p=106745). Week 1: 75.6 percent returned and drive start after a return 29.5 (NFL.com, https://www.nfl.com/news/nfl-kickoff-rule-change-leads-to-highest-return-rate-since-2010); week 1 touchback rate 18.6 percent against 64.5 in week 1 of 2024 (Front Office Sports 2025-09-08, ESPN data). Through week 7, 79.3 percent returned, 877 returns (AP, 2025-10-21).
- 2026 to date: through two weeks 256 kickoffs returned for 6,773 yards (about 26.5 yards per return), the most return yards ever through two games, 16 returns of 40 yards or more, longest 79 yards, no return touchdown yet (Pro Football Talk, Josh Alper, 2026-09-23, quoting Troy Vincent). Touchback rate and average start for 2026: not found.
- Reading for the simulation: with a touchback to the 35 the NFL's own 2025 result is mostly returns (about 76 percent), average start about the 30 to 31; touchbacks about one in five.

### 7. Flags: where the requirements file (section 9) differs from the official text

- F1. "2025: the kick is taken from the 34-yard line". The 2026 book says 35 for the kickoff, for the onside kick's restraining line and for the ten other kickers' line on an onside kick (6-1-2(a), 6-1-6(b),(c)); there is no 34 anywhere in the book. The "34" is from press reports (SI live blog 2025-05-21; American Football International 2025-05-22; CBS 2025-09-03). Deseret News (2025-08-08) says the ten others line up on the 35. The most likely meaning is that the 2024 line for the other onside kickers was the 34, one yard behind the ball, and 2025 moved it to the 35 ("a yard closer"). I could not read the 2025 book, so this is UNVERIFIED. Use 35 in the 2026 table.
- F2. "Whether the trailing condition still holds is not settled." Settled: no score condition exists in 2026 (6-1-6). Winning, tied or trailing may declare.
- F3. "The receiving team gets the ball at the spot where the foul or the touch happens." True only for illegal touching of an onside kick (the receivers may take possession at the spot of the touch, or the kickers lose five yards and kick again). Other fouls are enforced from the previous spot with a re-kick, except the option rule of 6-3-1 when the receivers keep the ball, and the special cases (untouched beyond the setup zone, out of bounds). See 1.6 and 4.1.
- F4. "Recovery rate about 6.45 percent in 2024 with three successes". Three recoveries in 50 attempts is 6.0 percent (Albert, CBS Jones, USA Today/The Football Database). The 6.45 percent figure appears in a CBS Sports article (Jeff Kerr, 2025-09-03) with no source and does not fit 3 of 50. My guess (UNVERIFIED) is that it is a partial-season count such as 2 of 31. Use 6.0 percent for 2024 and 9.6 percent (5 of 52) for 2025.
- F5. "After a safety the conceding team kicks a free kick, and an onside kick is possible under the same rule" [UNVERIFIED in the file]: now SRC-OFFICIAL (11-5-2, 6-1-1(b), 6-1-6(b)). Add: the kick spot is the 20, punts are allowed, a tee is allowed.
- F6. "Other 2026 changes: new alignment of the receiving team in the setup zone" [SRC-SECONDARY]: now SRC-OFFICIAL with numbers (section 2.3).
- F7. N4.4 "a surprise onside kick when leading is a rare data-driven choice only if SX.0 finds that it is allowed": it is allowed (declared like any other), but it can never be a surprise because the receiving team is told before the play clock starts. Rename it "an onside kick when leading or tied".
- F8. N4.1 "when the NFL rule of the current table allows an onside kick, a yes-or-no question": in the 2026 table the rule allows it at every free kick, so the question is asked every time the player's team kicks off or kicks after a safety. Consider a switch or default "no" to avoid asking dozens of times; this is a design decision, not a rules point.
- F9. N4.3 and section 9 recovery rules "(the ball must travel ten yards unless touched by the receiving team ...)": confirmed (6-1-6(e)). The exact penalties for an illegal onside kick are in 1.6.
- F10. (Outside topic D, noticed on the way.) NQ4 says the clone keeps sudden death. The 2026 overtime (Rule 16, PDF 72 and 73) is modified sudden death: both teams get a possession, regular season is one 10-minute period (a tie is possible), the postseason uses 15-minute periods, no coach challenges, and an onside kick recovered by the kickers counts as the receivers' possession. NQ4 stays an accepted default, but "N. F. L. rules" would not match the NFL unless it changes. Timeouts in overtime: two in the regular season, three per half in the postseason (16-3-e, 16-4-g). For topic A and B writers.
- F11. 4-3-1: the clock does not start when the kicking team recovers an onside kick before any other legal touch, and does not start on a touchback (relevant to C2).

### Could not settle

- The casebook (Approved Rulings) for Rule 6: not reachable (operations.nfl.com pages return 404 to the fetch tool; searches found only an unofficial study aid). So: penalty for an undeclared onside kick; exact spot after the "untouched beyond the setup zone" foul; whether a punt or drop kick may be used for an onside kick after a kickoff; and the receivers' spot when an onside kick goes out of bounds short of 25 yards, are readings of the book, not of rulings.
- The 2025 rulebook text of 6-1-3 and 6-1-6 (kick spot 34 versus 35; alignment numbers of 2025): the 2025 rulebook PDF was not found; operations.nfl.com 2025 pages 404. Press accounts disagree (flag F1).
- Onside kick statistics for 2026 to date (attempts, recoveries, attempts while leading or tied): searched news, ESPN recaps, Football Database, Pro Football Reference; nothing reliable found.
- Onside attempts split by quarter and score margin for 2025 and 2026: not published in anything I could reach; only 2025 totals.
- Average distance or recovery spot of onside kicks: not found.
- 2026 kickoff touchback rate and average start: not found (only returns through two weeks).
- The NFL Football Operations articles on kickoffs ("Dynamic Kickoff Rule Explainer", "back and better in second season", "The Extra Point: Player tracking and the onside kick"): all 404 to my fetch; I used search-tool quotations of them and tagged those SRC-SECONDARY.
- Wayback Machine access is blocked for the fetch tool.

### Sources (all retrieved 2026-10-14)

Official or league:
- 2026 Official Playing Rules PDF (https://static.www.nfl.com/image/upload/fl_attachment/league/tqivdkzt9mu6wdgsh1ku.pdf): Rule 6 (PDF 29 to 32), 3-17 and 3-19 (PDF 13, 14), Rule 4 (PDF 18 to 22), 7-2-1 and 7-3-1 (PDF 33, 34), 10-1 and 10-2 (PDF 47), 11-4 to 11-6 (PDF 51), 12-2 and 12-3 (PDF 54 to 58), 14 (PDF 61 to 66), 16 (PDF 72, 73), penalty summary (PDF 78, 79), 2026 changes (PDF 2).
- operations.nfl.com rulebook page https://operations.nfl.com/the-rules/nfl-rulebook/ : the 2026 change list (6-1-3, 6-1-5, 6-1-6, 19-2).
- NFL.com, NFL announces new playing rules, bylaws, resolutions for 2026: https://www.nfl.com/news/nfl-announces-new-playing-rules-bylaws-resolutions-for-2026 (approved text, no rationale).
- NFL.com, 2024 NFL season: explaining rules for new dynamic kickoff (2024-09-05): https://amp.nfl.com/news/2024-nfl-season-explaining-rules-for-new-dynamic-kickoff
- NFL.com, NFL's kickoff rule change leads to highest return rate since 2010 (2025, week 1): https://www.nfl.com/news/nfl-kickoff-rule-change-leads-to-highest-return-rate-since-2010

Team and reference sites:
- Steelers (2026-03-31, the league's text): https://www.steelers.com/news/nfl-owners-approve-2026-nfl-rule-changes
- Rams, approved 2026 changes with McKay quotes (2026-03-31): https://www.therams.com/news/2026-nfl-rule-bylaw-resolution-changes-onside-kick-and-other-kickoff-adjustments-ability-for-league-personnel-to-consult-with-on-field-officials-when-considering-disqualifications-for-both-flagrant-football-acts-and-non-football-acts-without-being-called-on-the-field-among-those-approved
- Rams, proposals (2026-03-26): https://www.therams.com/news/2026-nfl-club-playing-rules-bylaws-and-resolution-proposals-onside-kick-and-other-kickoff-aspects-league-personnel-consulting-with-on-field-officials-when-considering-qualifications-ability-to-trade-draft-picks-five-years-into-future-among-those-slated-to-be-discussed
- Panthers (2026-04-01): https://www.panthers.com/news/the-nfl-rule-changes-for-2026-and-impact-on-panthers
- Rams (2025-04-01) and Raiders (2025-04-01) on the 2025 approvals: https://www.therams.com/news/2025-nfl-rule-bylaw-resolution-changes-owners-approve-expanded-replay-alignment-of-regular-season-and-overtime-rules-permanent-dynamic-kickoff-with-touchbacks-to-the-35-yard-line and https://www.raiders.com/news/nfl-owners-approve-proposals-for-2025-season-overtime-rules-dynamic-kickoff

News and analysis:
- CBS Sports 2026 rule changes (2026-03-31): https://www.cbssports.com/nfl/news/nfl-rule-changes-2026
- Football Zebras scorecard (2026-04-07): https://www.footballzebras.com/2026/04/nfl-owners-approve-rule-changes-for-the-2026-season/
- USA Today via AOL (2026-03-31), onside figures and setup zone: https://www.aol.com/articles/nfl-kickoff-rules-2026-league-213518217.html
- CBS Sports, Five new NFL rules (2025-09-03): https://www.cbssports.com/nfl/news/five-new-nfl-rules-to-know-heading-into-week-1-of-preseason-here-are-the-biggest-changes-for-2025
- CBS Sports, Jeff Kerr (2025-09-03), the 34 and 35 and 6.45 percent claims: https://www.cbssports.com/nfl/news/new-kickoff-rule-has-improvements-for-2025-but-theres-still-one-change-nfl-needs-to-address
- SI live blog, May 2025 owners vote (2025-05-21): https://www.si.com/nfl/vikings/onsi/news/live-updates-nfl-owners-voting-on-controversial-rules-in-minnesota
- American Football International (2025-05-22): https://www.americanfootballinternational.com/?p=190321
- Deseret News (2025-08-08): https://www.deseret.com/sports/2025/08/08/understanding-new-nfl-kickoff-rules-2025-season/
- ESPN, owners approve kickoff revamp (2024-03-26): https://www.espn.com/nfl/story/_/id/39812700/nfl-owners-approve-massive-revamp-kickoff-play
- ESPN, Kevin Seifert, how the NFL can save the onside kick (2019-03-19): https://www.espn.in/nfl/story/_/id/26299473/how-nfl-save-onside-kick
- CBS Sports, Jonathan Jones, onside kicks (2025-10-22): https://www.cbssports.com/nfl/news/nfl-plans-to-boost-onside-kick-success-rate-after-all-time-low-excitement and (2024-12-13): https://www.cbssports.com/nfl/news/thats-a-dead-play-onside-kicks-need-to-be-revitalized-and-the-nfl-plans-to-discuss-changes-this-offseason/
- Badger Bracketology, Laura Albert (2025-01-27): https://bracketology.engr.wisc.edu/nfl-analytics-recap-of-the-2024-regular-season/
- FanDuel (Football Database data): http://www.fanduel.com/research/theduel/history-of-onside-kicks-in-the-super-bowl-recent-attempts-successes-stats-01gr4a49de0r
- AP via news4jax (2025-10-21): https://www.news4jax.com/sports/2025/10/21/nfl-sees-a-surge-in-returns-with-the-new-dynamic-kickoff-onside-kicks-remain-a-concern/
- PFF (2026-03-03): https://www.pff.com/news/nfl-kickoffs-are-evolving-as-returns-surged-in-2025
- Sharp Football Analysis, Rich Hribar (2026-07-13): https://www.sharpfootballanalysis.com/?p=106745
- Front Office Sports (2025-09-08): https://frontofficesports.com/article/nfl-kickoff-returns-skyrocket-after-latest-rule-change/
- Pro Football Talk (2026-09-23): https://www.nbcsports.com/nfl/profootballtalk/rumor-mill/news/2026-season-has-seen-the-most-kickoff-return-yards-ever-through-two-weeks
- SI, final 2024 kickoff data (quoted by search, page not read): https://www.si.com/nfl/final-data-2024-season-impact-nfl-new-kickoff-rules
- Failed or not read (404, 403 or blocked): operations.nfl.com updates and stats-central pages, edge-operations.nfl.com media PDF of the 2026 proposals, Steelers Depot (403), Behind the Steel Curtain (403), web.archive.org (blocked).


## Part 6. Penalty enforcement, accept or decline, and clock effects

SX.0 topic E2 for the nfl4 project. Written 2026-10-14. Research only; nothing in the project folder was changed.

Main source: the 2026 Official Playing Rules of the NFL (PDF "ops-2026-NFL-Rulebook-FINAL", copyright 2026 NFL), read in full for Rule 14 and in the needed parts of Rules 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 15, 16, 18 and the Penalty Summary. Retrieved 2026-10-14.

How to read the citations
- Citations are Rule-Section-Article, for example 14-1-1.
- "PDF p." is the PDF page. The printed page number is the PDF page minus 7 (Rule 14 is PDF pages 61 to 66, printed 54 to 59).
- Tags: [SRC-OFFICIAL] read in the 2026 rulebook. [SRC-SECONDARY] a non-league page. [UNVERIFIED] not found.
- "reading" after a tag means I combined two or more rule texts to reach the statement; no single sentence says it.
- Team A is the team that puts the ball in play, Team B its opponent, and they keep these names for the whole down even after a change of possession (3-35-2). "Offense" and "defense" follow possession (3-35-1). Rule 14 and the Rule 14 exceptions use both pairs of names, so the notes say which one is meant.
- All paraphrases are mine. A short quote is marked with quotation marks.

### Answers in brief

Question 1: who chooses and how
- 1a. Any penalty may be declined by the offended team, and play then goes on as if no foul had occurred, unless a rule expressly prohibits declining. [SRC-OFFICIAL] 14-1-1, PDF p.61.
- 1b. The yardage can be declined even though the penalty is accepted (partial acceptance: for example keep the loss of down or the first down but not the yards). [SRC-OFFICIAL] 14-1-1.
- 1c. Who speaks: only one captain may indicate the team's penalty option; the Referee first explains the alternatives. The head coach is not named for this choice (he is named only for changing a choice after a replay reversal). [SRC-OFFICIAL] 18-1-3 (PDF p.76), 14-1-3, 15-7-3 Item 3.
- 1d. "Offended team" is not defined in the rulebook; it is used for the opponent of the team that fouled. [SRC-OFFICIAL] (negative finding: six uses, no definition).
- 1e. The choice is final once the penalty is fully administered or the ball is ready for play, except after a replay reversal. [SRC-OFFICIAL] 14-1-1, 15-7-3 Item 3.
- 1f. Multiple fouls by one team in one down (a multiple foul): only one penalty is enforced, chosen by the offended team after the Referee explains the alternatives. Exceptions enforced in addition: a foul against an official, a challenge made with no timeouts left, a fifth or later excess injury timeout; and a personal foul that is also defensive pass interference (both may be enforced). [SRC-OFFICIAL] 14-1-3, PDF p.61.
- 1g. No choice: double fouls offset and cannot be declined by either team; dead ball fouls by both teams offset; a disqualified or suspended player is removed even if the penalty is declined; the 10-second runoff after a replay reversal or nullified foul cannot be declined. [SRC-OFFICIAL] 14-5-1, 14-4-9 Item 2, 14-1-1, 4-7-4, 15-5-2.
- 1h. A first down gained on the play does not stop the offended team from accepting a foul by the other team; the offended team compares the two outcomes. [SRC-OFFICIAL, reading] 14-1-1 has no exception for that case.
- 1i. Fouls with a change of possession: a foul by Team B before it gains possession can be accepted (ball goes back to Team A) or declined (turnover stands); a foul by the offense before the change forces the defense to decline to keep the ball, except personal or unsportsmanlike fouls, which let the defense keep the ball and enforce from the dead ball spot. [SRC-OFFICIAL] 14-4-3 (a) (b), 14-2-4, PDF p.62 to 63.
- 1j. Fouls during a scrimmage kick: the receiving team may decline, replay the down from the previous spot, or (if it keeps possession all down) add the yardage to the dead ball spot. A receiving-team foul after it has possession of a kick that crossed the line of scrimmage is a "post-possession" foul enforced from the less favorable (for the receivers) of the end of the kick and the spot of the foul. [SRC-OFFICIAL] 14-4-8, 3-26, 9-5-1 Exceptions 2 and 4, PDF p.64 to 65.
- 1k. The rulebook has no separate "order of enforcement" article. Order is fixed only by these sequence rules: one penalty per multiple foul; fouls between downs are always enforced separately; personal fouls and unsportsmanlike fouls on a score go to the Try or kickoff; a personal foul that is also pass interference is enforced from the pass interference spot. [SRC-OFFICIAL, reading] 14-1-3, 14-4-9, 14-2-3, 8-5.

Question 2: spots
- 2a. The seven spots (previous, spot of the foul, spot of a backward pass or fumble, dead ball, succeeding, other Try spot, spot of change of possession) are defined in 3-13-3 and 14-3-4. The basic spot (dead ball spot for a run with no change of possession; the spot where possession was lost for a run with a change; the spot of the backward pass or fumble) is 14-3-5. [SRC-OFFICIAL] PDF p.12 and p.62.
- 2b. Three-and-one method: for fouls during a run, backward pass or fumble, enforce from the basic spot if the defense fouls ahead of it, the defense fouls behind it, or the offense fouls ahead of it; if the offense fouls behind it, enforce from the spot of the foul. [SRC-OFFICIAL] 14-3-6, PDF p.62.
- 2c. Half the distance: a distance penalty never moves the ball more than half the distance from the spot of enforcement to the offender's goal line; this supersedes other enforcement rules; exceptions are intentional grounding (8-2-1) and a palpably unfair act (12-3-4). [SRC-OFFICIAL] 14-2-1, PDF p.62. The rulebook gives no rounding for less than one yard. [UNVERIFIED]
- 2d. Spot fouls are not distance penalties: defensive pass interference is enforced at the spot of the foul (first down); behind the goal line it is first down on the one-yard line, or halfway between the previous spot and the goal line if the previous spot was inside the two-yard line. [SRC-OFFICIAL] 8-5 Penalty, 14-4-5 (b), PDF p.40, p.63 to 64.
- 2e. Offense foul behind its own goal line: a safety if the defense elects to enforce at that spot. If the dead ball spot is in the offensive end zone: a safety, wherever the foul occurred. [SRC-OFFICIAL] 14-2-2 (b), 14-3-6 Exceptions 2 and 3, 11-5-1 (a).
- 2f. Combination penalties (distance and loss of down): illegal forward pass from behind or beyond the line, intentional grounding, backward pass that conserves time, illegal forward handing, illegal punt or drop kick or place kick, illegal bat, illegal kick. On fourth down the ball goes to Team B and the distance is also enforced. [SRC-OFFICIAL] 14-1-2 Item 2, PDF p.61.
- 2g. First down after a penalty: a foul by Team B gives first-and-10 to Team A unless it is one of ten listed fouls (offside, encroachment, neutral zone infraction, delay of game, illegal substitution, excess timeout, running into the kicker, more than 11 players on the field at the snap, more than 11 in the formation before the snap, illegal formation by the defense on a scrimmage kick), for which the down and line to gain stay unless the distance puts the ball on or past the line to gain. A foul by Team A keeps the down (replay) unless a combination penalty, except that it is first-and-10 if the enforcement spot is in advance of the line to gain. [SRC-OFFICIAL] 14-1-2 Items 1, 4, 5, PDF p.61.

Question 3: offsetting
- 3a. A double foul (3-13-1-e) with no change of possession: penalties offset, the down is replayed at the previous spot with the same down number and line to gain; neither team may decline. [SRC-OFFICIAL] 14-5-1, PDF p.65.
- 3b. Exceptions: 15 yards against 5 yards (minor foul with no automatic first down, loss of down or runoff, or not a spot foul): the 15-yard penalty is enforced from the previous spot, the 5-yard one is disregarded. Dead ball fouls by both teams offset at the succeeding spot and the down counts. [SRC-OFFICIAL] 14-5-1 Exceptions 1, 2, 4.
- 3c. Double foul with a change of possession: the team that last gained possession keeps the ball after enforcement of its own foul if its hands were clean (it did not foul before last gaining possession); otherwise offset and replay. Several exceptions (kick plays, safety by enforcement, personal fouls). [SRC-OFFICIAL] 14-5-2, 14-5-3, PDF p.66.
- 3d. Dead ball and live ball fouls combine into double or multiple fouls, with three exceptions (5-v-15 on the last play of a half, a score followed by a dead ball foul, and "clean hands" at the end of a half). A foul between downs never combines. [SRC-OFFICIAL] 14-4-9 Items 2 and 3, PDF p.65.

Question 4: dead ball, live ball, scores
- 4a. Live ball foul: after the snap until the ball is dead. Dead ball foul: in the continuing action after a down, or taunting at any time; enforced from the succeeding spot and the down counts. Foul between downs: after the action ends and before the next snap or kick; enforced from the succeeding spot, down counts. [SRC-OFFICIAL] 3-13-1, 14-4-9, PDF p.12, p.65.
- 4b. Extra untimed down cases (extension of a period): accepted live ball foul by the defense on the last play; certain offensive fouls on request of the defense; double foul on the last down; and kick-related cases. [SRC-OFFICIAL] 4-8-2, PDF p.22.
- 4c. Scores: the offended team may accept the penalty with customary enforcement (new series or replay) instead of the points; personal and unsportsmanlike fouls on a touchdown play go to the Try, on a field goal or safety to the succeeding free kick. An offense foul that the defense accepts erases the score. [SRC-OFFICIAL] 14-2-3, 14-1-1, PDF p.62.
- 4d. Last play of a half: an offense foul stops any extension and a score by the offense is not counted (the text does not say whether the defense may decline). [SRC-OFFICIAL] 4-8-2 (b); option to decline [UNVERIFIED].

Question 5: clock
- 5a. The clock stops at the end of a down with a foul, and at the time of a foul that leaves the ball dead. After enforcement or declination it starts as if the foul had not occurred, except: it starts on the snap after the two-minute warning of the first half, inside the last five minutes of the second half, for an offense foul after the ball is ready during the fourth period or regular season overtime, after two successive delay-of-game penalties by the offense while time is in. [SRC-OFFICIAL] 4-4 (e) (g), 4-3-2 (e), PDF p.19.
- 5b. 10-second runoff, after the two-minute warning of either half, offense acts that conserve time while time is in (a foul that stops the clock in a dead ball period, intentional grounding, illegal forward pass, backward pass out of bounds, spiking, illegal bat or kick out of bounds; illegal substitution is the separate 4-7-2): the defense may take the yardage and decline the runoff; the offense may use a timeout instead; never against the defense. [SRC-OFFICIAL] 4-7-1, 4-7-2, 4-5-4 Note 9, PDF p.21 to 22.
- 5c. Runoff after a replay reversal or a nullified foul after the two-minute warning (when the correct ruling would not have kept the clock stopped): neither team can decline; either team can use a timeout to prevent it. [SRC-OFFICIAL] 4-7-4, 15-5-2, PDF p.22, p.70.
- 5d. Defensive foul on the last play of a half: if accepted, the offense may extend by one untimed down. Defensive time-conserving foul in the last 40 seconds: the half ends unless the defense has timeouts left or the offense chooses to start the clock on the snap. [SRC-OFFICIAL] 4-8-2 (a), 4-7-3, PDF p.22.
- 5e. Five-minute rule is the last five minutes of the second half, not "fourth quarter and overtime" as such (overtime gets fourth period timing through 16-3 (e)). [SRC-OFFICIAL] 4-3-2 (a) (3), (e) (2), (e) (3), 16-3 (e).

Question 6: special cases
- 6a. Try: all rules in 11-3-3; Team B fouls after the snap are enforced on the ensuing kickoff (except defensive pass interference), Team A fouls on a successful Try cause a repeat of the Try unless the penalty includes loss of down. [SRC-OFFICIAL] 11-3-3 Items 1 to 7, PDF p.49 to 50.
- 6b. Kickoff and punt: see sections 6.2 and 6.3 below. [SRC-OFFICIAL] 14-4-7, 14-4-8, 6-3-1, 9-5-1.
- 6c. Overtime: the 2026 NFL overtime gives both teams one possession unless the receiving team's first drive ends in a safety; special limits on accepting penalties that would create a second possession; no coach challenges; two timeouts (regular season) or three per half (postseason). [SRC-OFFICIAL] 16-3, 16-4, 16-5, PDF p.72 to 73.

Also in brief: the casebook (Approved Rulings) could not be reached publicly (section Could not settle).

### 0. Reading guide and key structure of Rule 14

Rule 14 is "governing all cases not otherwise specifically provided for" (PDF p.61). Its parts:
- Section 1: refusal, number of down, choice among multiple fouls.
- Section 2: half the distance, foul behind a goal line, foul during a score, personal fouls.
- Section 3: definitions of spots, basic spot, three-and-one method.
- Section 4: the spot by phase of play (articles 1 to 9).
- Section 5: double fouls.
Other rules carry their own penalties and some special enforcement (Rule 6 free kicks, Rule 8 passes, Rule 9 scrimmage kicks, Rule 11 Try, Rule 12 conduct, Rule 4 timing).

### 1. Who chooses and how

#### 1.1 Accept or decline, the base rule
- "Unless expressly prohibited" the penalty for any foul may be declined; play then continues as if no foul had been committed. [SRC-OFFICIAL] 14-1-1, PDF p.61.
- The yardage of any penalty may be declined even though the penalty is accepted. [SRC-OFFICIAL] 14-1-1.
  - Example of use: accept a defensive foul only to keep the first down, and decline its yards because the play gained more. (My example, not the rulebook's.)
  - Design note: the game's prompt can offer three outcomes in principle (decline; accept; accept without yards). The practical version for a spoken prompt is accept or decline; the "accept without yards" case can be folded into the computer's side only if SX.1 wants it.
- The decision may not be changed after the penalty has been fully administered or the ball has been made ready for play. The one exception: if a ruling is changed by replay, the head coach can change a decision to accept or decline that was made before the review. [SRC-OFFICIAL] 14-1-1, 15-7-3 Item 3, PDF p.61, p.71.
- A disqualified or suspended player must be removed whatever the penalty decision. [SRC-OFFICIAL] 14-1-1.
- Two unsportsmanlike fouls (punching or kicking at an opponent, abusive language, taunting) by the same player in a game cause automatic disqualification, whether each penalty is accepted or declined. [SRC-OFFICIAL] 12-4-1, PDF p.59.

#### 1.2 Who is "the offended team" and who speaks
- The rulebook never defines the term; it is used for the opponent of the fouling team (6-3-1, 14-1-3, 14-2-3, 14-4-7). [SRC-OFFICIAL, reading]
- "Only one captain is permitted to indicate the team's penalty option." [SRC-OFFICIAL] 18-1-3, PDF p.76 (short quote, under 15 words).
- Each team has up to six captains named by the coach before the game (18-1-1). [SRC-OFFICIAL]
- The Referee explains the alternatives to the offended team before the choice (14-1-3, multiple fouls). [SRC-OFFICIAL]
- Difference from the requirements file (section 12): it says "the offended team's captain or coach chooses". The rulebook names the captain for the option and the head coach only for the post-replay change. For the game: speak it as "your captain" or simply "you"; no rule problem either way, but "the coach decides" is not the rulebook wording.

#### 1.3 Multiple fouls by the same team (14-1-3, PDF p.61)
- A multiple foul is two or more fouls by the same team in the same down, dead ball fouls included (3-13-1-d). [SRC-OFFICIAL] PDF p.12.
- Only one penalty may be enforced, after the Referee has explained the alternatives. The offended team picks the one it prefers (or declines all). [SRC-OFFICIAL] 14-1-3.
- Exceptions, enforced in addition to any other foul and never part of a multiple foul:
  - a foul against an official;
  - a team initiating a challenge when it has no timeouts left (15 yards, a foul between downs, 15-1-1);
  - a fifth and later excess timeout for injury.
  [SRC-OFFICIAL] 14-1-3 Exception 1, 14-1-2 Item 4 Exception, 15-1-1 (d), 4-5-4 Note 2.
- Exception 2: when a personal foul is also defensive pass interference, both fouls may be enforced. 8-5 says the personal foul is enforced from the spot of the foul (for the interference), or from the end of the run if the pass interference is declined. [SRC-OFFICIAL] 14-1-3, 8-5 Penalty, PDF p.40.
- When the defense commits several fouls in a run followed by a change of possession, the enforcement is the one most beneficial to the offense. [SRC-OFFICIAL] 14-4-3 (c), PDF p.63.
- A foul between downs is never part of a multiple or double foul; it is always enforced separately (14-4-9). A foul against an official is always treated as a foul between downs. [SRC-OFFICIAL] 14-4-9, 14-1-2 Item 4 Exception.

#### 1.4 Cases with no choice (automatic)
- Double foul without change of possession: offset, down replayed; "cannot be declined by either team". [SRC-OFFICIAL] 14-5-1.
  - Secondary corroboration: news coverage of an Eagles/Andy Reid ruling quotes the same rule. https://www.nbcsportsphiladelphia.com/nfl/reid-on-offsetting-penalty-call-it-doesnt-make-sense/359126 (seen only as a search-result summary, 2026-10-14). [SRC-SECONDARY]
- Dead ball fouls by both teams: offset at the succeeding spot and the down counts, unless the dead ball fouls occur after the ball was made ready for play (then 5-v-15 enforcement). [SRC-OFFICIAL] 14-4-9 Item 2, 14-5-1 Exception 4.
- 5 versus 15: the team that committed the minor foul cannot decline, except when the minor foul is a dead ball delay of game for spiking the ball and the opponent's foul is a live ball foul (then the delay-of-game team may decline the opponent's foul and be assessed its own penalty). [SRC-OFFICIAL] 14-5-1 Exceptions 2 and 3, PDF p.66.
- The 10-second runoff after a reversal or nullified foul (neither team can decline, either can use a timeout). [SRC-OFFICIAL] 4-7-4, 15-5-2.
- Disqualification, as above.
- Fouls by the defense that are not "expressly prohibited" from being declined can be declined. Nothing in Rule 14 makes a dead ball foul or a between-downs foul mandatory. [SRC-OFFICIAL, reading]
- Overtime limit: the second team may not decline or accept in a way that creates a second possession for itself (16-5-a Note 2). [SRC-OFFICIAL] PDF p.72.

#### 1.5 The offense's choice between "result of the play" and "the penalty"
For a foul by Team B (the defense):
- Decline: the play counts as it ended; the down and distance follow the result (including a first down if made).
- Accept: the play is erased in most cases and the penalty is enforced from the spot rules in section 2. First-and-10 for Team A unless the foul is one of the ten fouls without an automatic first down (14-1-2 Item 5).
- Three-and-one exception: for fouls during a run (not a pass play), enforcement from the basic spot (dead ball spot) means the yards gained on the run stay and the penalty is added to them. [SRC-OFFICIAL] 14-3-6, 14-4-2.
For a foul by Team A (the offense):
- Decline: the play counts as it ended (including a turnover); the defense keeps what it earned.
- Accept: penalty enforced; Team A replays the down (same down number) unless loss of down applies; the play's result is erased except that enforcement from the dead ball spot or basic spot can keep part of the gain (for personal fouls, 14-4-5 (e), 14-2-4). [SRC-OFFICIAL] 14-1-2 Items 1 and 2, 14-4-1 Item 2.

#### 1.6 Fouls during a change of possession (14-4-3, 14-4-4, 14-4-5, 14-4-6, PDF p.63 to 64)
Foul by Team B (defense) before it gains possession on a run (fumble or similar):
- The ball reverts to Team A before enforcement; Team A may accept (ball back, penalty from the basic spot) or decline (Team B keeps the ball). [SRC-OFFICIAL] 14-4-3 (a).
Foul by Team A (offense) before the change of possession:
- The defense must decline to keep possession. [SRC-OFFICIAL] 14-4-3 (b).
- If the offense's foul is a personal foul or unsportsmanlike foul, the defense keeps possession and enforcement is from the dead ball spot; if the defense later loses the ball, the penalty is enforced from the spot where possession changed and the defense still keeps possession. [SRC-OFFICIAL] 14-4-3 (b), 14-2-4 (extra option: any personal or unsportsmanlike foul that is not part of a double foul may be enforced from the dead ball spot when the opponent has possession at the end of the down).
- On a pass play: personal or unsportsmanlike foul by the offense before it loses possession is enforced from the dead ball spot; if the defense later loses possession, from the spot of the defense's catch or recovery, and the defense keeps the ball. [SRC-OFFICIAL] 14-4-5 (e).
Foul after a change of possession:
- Enforced from the dead ball spot or the spot of the foul by the three-and-one method. It is first-and-10 for the team in possession at the time of the foul after a distance penalty. [SRC-OFFICIAL] 14-1-2 Item 6, 14-4-2, 14-4-3.
- If a change of possession is negated by enforcement against Team A, the line to gain stays the same. [SRC-OFFICIAL] 14-1-2 Item 3.
Foul in the end zone after a change of possession: see section 2.6.
Double fouls with a change of possession: section 3.4.
Fouls before gaining possession: pass interference or holding by the defense before an interception are fouls during the passing play (previous spot, 14-4-5); the offense may decline and let the interception stand, or accept and get the ball back with the penalty. [SRC-OFFICIAL, reading]

#### 1.7 Post-possession fouls and fouls on scrimmage kicks (14-4-8, 3-26, 9-5-1, PDF p.64 to 65)
- Post-possession foul: a foul by the receiving team during a scrimmage kick that crosses the line of scrimmage, provided the receiving team never loses possession during the rest of the down. [SRC-OFFICIAL] 3-26, PDF p.15.
- Enforcement is as if the receiving team had possession when it fouled, from the less favorable (to the receivers) of: the end of the kick, or the spot of the foul. A foul in the end zone is deemed to be at the 20-yard line unless it produces a safety. [SRC-OFFICIAL] 14-4-8 Exception 4.
- Fouls made in an attempt to block the kick are not post-possession fouls: running into or roughing the kicker, defensive holding (pull-and-shoot), leverage, leaping, pushing teammates into the offensive formation. [SRC-OFFICIAL] same.
- Kicking-team foul: previous spot; if the receiving team keeps possession throughout the down, the receiving team may take the penalty at the previous spot and replay the down, or add the penalty yardage to the dead ball spot. [SRC-OFFICIAL] 14-4-8 Exception 2, 9-5-1 Exception 2.
- Receiving team's illegal touch inside its five-yard line: the receivers may also take a touchback. [SRC-OFFICIAL] 14-4-8 Note (b).
- Penalties for holding and illegal use of hands by either team on a scrimmage kick play that goes beyond the line are 10 yards, unless the foul is committed in an attempt to block the kick. [SRC-OFFICIAL] 9-1-4 (e), PDF p.43.

### 2. The spots

#### 2.1 The seven spots (3-13-3, 14-3-4)
- Previous spot: where the ball was last put in play.
- Spot of the foul: where the foul was committed or is considered by rule to have been committed.
- Spot of a backward pass or fumble.
- Dead ball spot: where the ball became dead. (8-5 calls the dead ball spot of a run "the end of the run".)
- Succeeding spot: where the ball will next be put in play (the spot of the ball after enforcement for a foul, or the dead ball spot if no foul).
- The other Try spot: the yard line of the other Try option after any earlier penalties.
- Spot of a change of possession: where possession was gained or awarded.
[SRC-OFFICIAL] PDF p.12, p.62.

#### 2.2 Basic spot (14-3-5) and three-and-one (14-3-6)
- Basic spot applies to fouls during a running play or during a backward pass or fumble:
  - run, no change of possession: the dead ball spot;
  - run followed by a change of possession: the spot where possession was lost;
  - backward pass or fumble: the spot of that pass or fumble.
- Three-and-one: enforce from the basic spot if the defense fouls ahead of it, the defense fouls behind it, or the offense fouls ahead of it; if the offense fouls behind it, enforce from the spot of the foul. "Ahead" means nearer the defense's goal line.
- Exceptions for offense fouls:
  1. a foul behind the line of scrimmage: from the previous spot;
  2. a foul behind its own goal line: safety if the defense elects;
  3. a foul beyond the line of scrimmage when the basic spot is behind it: from the previous spot; if the dead ball spot is in the offensive end zone: safety whatever the foul;
  4. a foul in the defense's end zone before a touchdown: from the goal line.
- Exception for defense fouls: when the basic spot is behind the line of scrimmage, a defense foul (behind or beyond the line) is enforced from the previous spot.
[SRC-OFFICIAL] 14-3-5, 14-3-6, PDF p.62 to 63.

#### 2.3 Which spot for which phase (14-4)
- Before the snap (false start, encroachment, neutral zone infraction, delay of game with the ball dead, too many men in the formation): the succeeding spot; the down is not played and stays the same, unless enforcement gives a first down. [SRC-OFFICIAL] 14-4-1 Item 1.
- At the snap (illegal formation, illegal shift, illegal motion, offside, snap fouls, too many players on the field at the snap): the previous spot; the down is repeated unless it gives a first down. [SRC-OFFICIAL] 14-4-1 Item 2.
  - Offside is defined as "when the ball is put in play" (3-19, 7-4-5), so it is a foul at the snap: the play can run and the offense may decline. Encroachment and neutral zone infraction carry "officials are to blow their whistles immediately" (7-4-3, 7-4-4), and false start has the whistle blown immediately (7-4-2), so those are enforced before the snap. [SRC-OFFICIAL, reading]
- Running play, no change of possession: basic spot = dead ball spot, three-and-one. A foul in a run before a forward pass or kick from behind the line counts as a passing or kick foul. [SRC-OFFICIAL] 14-4-2.
- Running play followed by a change of possession: basic spot = spot where possession was lost. [SRC-OFFICIAL] 14-4-3.
- Passing play (snap until the forward pass from behind the line ends; a running play begins when the pass is caught): previous spot. Exceptions: intentional grounding; defensive pass interference (spot of the foul); offense foul behind its own goal line (safety if the defense elects); personal or unsportsmanlike foul by the defense before the pass is completed (previous spot or dead ball spot, whichever helps the offense more; on a scoring play, on the Try); personal or unsportsmanlike foul by the offense before it loses possession (dead ball spot; spot of the defense's catch if the defense later loses the ball). [SRC-OFFICIAL] 14-4-5, PDF p.63 to 64.
- Backward pass or fumble: the spot of the pass or fumble is the basic spot and three-and-one applies; if that spot is behind the line of scrimmage, all fouls are from the previous spot (offense in its end zone: safety if the defense elects); special rule for personal fouls by the offense when the defense recovers. [SRC-OFFICIAL] 14-4-6.
- Free kick: previous spot and the kick is made again; options described in 6.2. [SRC-OFFICIAL] 14-4-7.
- Scrimmage kick: previous spot (also for a foul during a run before a legal kick and a foul by the kicking team on a missed field goal try); options in 1.7. [SRC-OFFICIAL] 14-4-8.
- Dead ball foul and foul between downs: succeeding spot; the down counts. [SRC-OFFICIAL] 14-4-9.
- Foul during the continuing action after a score or between plays: see sections 4 and 6.
- Penalty on the offended team's option: 14-2-4 gives an additional option to enforce a personal or unsportsmanlike foul from the dead ball spot when the opponent has possession at the end of the down and it is not part of a double foul.

#### 2.4 Half the distance (14-2-1, PDF p.62)
- "If the enforcement of a distance penalty would move the ball more than half the distance from the spot of enforcement to the offender's goal line," the penalty is half that distance. [SRC-OFFICIAL] (the quoted words are the opening of 14-2-1).
- It applies to both teams: the offender's own goal line is the reference. A defense foul from the defense's 10 moves at most 5 yards; an offense foul from its own 10 moves at most 5 yards back.
- It "supersedes any other general or specific enforcement of a distance penalty". Exceptions: intentional grounding (8-2-1) and palpably unfair act (12-3-4).
- Pass interference by the defense is not a distance penalty (it is a spot foul) and has its own goal-line rules (8-5, 14-4-5 (b)); no half-distance cap applies to it, except the inside-the-two-yard-line case which says halfway between the previous spot and the goal line. [SRC-OFFICIAL, reading]
- Measuring the half: spot of enforcement to the offender's goal line, divided by two, enforced if smaller than the normal yardage. Secondary explainer, search-result summary only, 2026-10-14: https://www.footballnationusa.com/post/why-is-a-penalty-half-the-distance-to-the-goal-nfl-rule-explained [SRC-SECONDARY]
- Rounding: the rulebook gives no rule for a half that is less than a yard (ball on the 1 or the 2). On the 2-yard line half is one yard (the secondary source says a foul at the Try spot of the 2 puts the ball on the 1). On the 1-yard line half is half a yard. [UNVERIFIED] Suggestion for the engine (design, not rule): positions are whole yards, so for a half under 1 yard keep the ball where it is and apply any automatic first down.
- Test invariant (from the rule): for every distance penalty enforced by 14-2-1, the ball moves at most half the distance from the spot of enforcement to the offender's goal line. Spot fouls, intentional grounding and palpably unfair acts are outside it.

#### 2.5 Fouls behind a goal line and safeties (14-2-2, PDF p.62)
- (a) Defense foul where the spot of enforcement is behind the offense's own goal line: enforced from the goal line; if the play is a touchback, from the 20-yard line (or the 35 or 20 per 6-1-5 when the impetus was a free kick). [SRC-OFFICIAL] (the offense's goal line is the one it defends.)
- (b) Offense foul with the spot of enforcement behind its own goal line: a safety if the defense elects to enforce at that spot.
- (c) Offense foul where the spot of enforcement is behind the defense's goal line: enforced from the goal line.
- A safety by enforcement is only possible when the offense's foul is committed behind its own goal line (or the dead ball spot is in its own end zone). Holding on the 1-yard line, for example, is not a safety; the half-distance rule just moves the ball.
- Intentional grounding with the passer's whole body and the ball in his own end zone: a safety. [SRC-OFFICIAL] 8-2-1 (c).
- A forward pass from behind the line after the ball was beyond the line, or a second forward pass: from the previous spot, or a safety if the spot of the pass is behind the passer's goal line and the defense elects. [SRC-OFFICIAL] 14-4-5 Note 1.

#### 2.6 End zone cases after a change of possession (14-4-4, PDF p.63)
When there is a foul by either team after a change of possession and the dead ball spot is in Team B's end zone:
- Fouls by Team A: from the goal line if the impetus was by Team B; from the 20 (or 35 or 20 after a free kick) if the impetus was by Team A. Exception for momentum carrying a player into the end zone.
- Fouls by Team B with Team A impetus: if Team B tries to advance and its foul is in the end zone, a safety; if Team B does not advance and fouls in the end zone, from the 20 (or 35 or 20); if the spot of its foul is in the field of play, from the spot of the foul or the touchback spot, whichever is least beneficial to Team B.
- Fouls by Team B with Team B impetus: a safety, wherever the foul is.
[SRC-OFFICIAL]
- Safety exception for players whose momentum carries them in: if the spot where possession was established is in the end zone it is a touchback (11-5-1 Exception 2), and a live ball foul by that team in the end zone is a safety. [SRC-OFFICIAL] 11-5-1 Exception 2 (a).

#### 2.7 Fouls behind the line of scrimmage
- Offense foul behind the line of scrimmage: from the previous spot (14-3-6 Exception 1 for offense). [SRC-OFFICIAL]
- Defense foul where the basic spot is behind the line of scrimmage: from the previous spot. [SRC-OFFICIAL] 14-3-6, PDF p.63.
- Backward pass or fumble spot behind the line of scrimmage: all fouls by either team from the previous spot. [SRC-OFFICIAL] 14-4-6 (b).

#### 2.8 Number of the down after enforcement (14-1-2, PDF p.61) and first down rules (7-3-1, PDF p.34)
- Item 1: foul by Team A before or during a scrimmage play: after a distance penalty, if the ball is behind the line to gain the down number stays the same (the down is replayed), unless it is a combination penalty.
- Item 2: combination penalties (loss of down plus yards): illegal forward pass from behind or beyond the line (8-1-2), intentional grounding (8-2-1), backward pass that conserves time (8-7-2), illegally handing the ball forward (8-7-4), illegal punt or drop kick or place kick (9-1-1), illegal batting (12-5-1), illegal kicking (12-5-2). Before fourth down the next down is one higher; on fourth down the ball goes to Team B and the distance penalty is also enforced. (12-5-2 says no loss of down for a foul by Team A beyond the line of scrimmage during a scrimmage kick.)
- Item 3: change of possession negated by enforcement against Team A: the line to gain stays the same.
- Item 4: ball in advance of the line to gain after a distance penalty for a foul by Team A during a play from scrimmage: first-and-10 for Team A; also for a dead ball foul by Team A at the end of a play with no change of possession. Exception: a foul against an official, a challenge by a team without timeouts, and a fifth or later excess injury timeout are always treated as fouls between downs (so no first down just because of position).
  - Wording gap: Item 4 says "in advance of the line to gain", while 7-3-1 (b) (for Team B fouls) says "at or beyond". A Team A penalty that leaves the ball exactly on the line to gain is not addressed by Items 1 or 4. 3-8-2 treats reaching the line as enough. Suggestion: treat "at or beyond" as a first down. [UNVERIFIED for the exact-line case]
- Item 5: foul by Team B before, during or after a play from scrimmage: first-and-10 for Team A. Ten exceptions (no automatic first down): offside, encroachment, neutral zone infraction, delay of game, illegal substitution, excess timeout, running into the kicker, more than 11 players on the field at the snap, more than 11 players in the formation before the snap, illegal formation by the defense during a scrimmage kick play. For those, the down and the line to gain stay unless a distance penalty puts the ball on or in advance of the line to gain: then first-and-10.
  - Data-model consequence: store the exceptions ("no automatic first down") rather than only "has automatic first down" per foul. Every other Team B foul gives first-and-10 even when the foul's own text does not say "automatic first down". [SRC-OFFICIAL, reading]
- Item 6: foul after a change of possession during a down, after a distance penalty: first-and-10 for the team in possession when the foul occurred.
- Item 7: foul between downs: the down remains the same unless enforcement gives a first down.
- Item 8: double fouls that offset: replay the down, same down number.
- 7-3-1: new series for Team A when: the ball is dead in Team A's possession at or beyond the line to gain; enforcement of a Team B foul puts the ball at or beyond the line to gain or awards an automatic first down; there is a change of possession and Team A has possession at the end; the kicking team recovers a scrimmage kick after the receivers touched it beyond the line; the kicking team legally recovers a free kick. [SRC-OFFICIAL]
- 14-4-9 Items 1 on dead ball and between-downs fouls by Team A after a first down: "first-and-10" after a dead ball foul and "first-and-25" after a foul between downs. The "25" appears literally in the rulebook. If the line to gain is where the new series put it, geometry would give 10 plus the yards (first-and-15 after a five-yard foul). The literal number fits only a 15-yard foul. [SRC-OFFICIAL] literal text, PDF p.65; the intent [UNVERIFIED] (casebook not reached). Suggestion: compute "yards to go" from the line to gain and the new spot; this reproduces 25 for 15-yard fouls and is the reading that makes sense for the rest; flag in the design file.

#### 2.9 Worked examples for the tests (my arithmetic from the rule texts)
- Example 1: first-and-10 at the offense's own 35, incomplete pass, defensive holding (5 yards, automatic first down). Pass play: previous spot own 35 plus 5. Accept: own 40, first-and-10. Decline: second-and-10 at own 35. [14-4-5, 14-1-2 Item 5, 12-1-6]
- Example 2: third-and-8 at own 30, completed pass to own 42 (first down), defensive holding. Accept: own 35, first-and-10 (play erased). Decline: first-and-10 at own 42. [same]
- Example 3: first-and-10 at own 40, run to own 46, offensive holding (10 yards) at own 42 (beyond the line, behind the basic spot). From the spot of the foul: own 42 minus 10 equals own 32, first down replayed. Decline: first-and-10 becomes second-and-4 at own 46 (the run counts). [14-3-6, 12-1-3 (c), 14-1-2 Item 1]
- Example 4: the defense's 10-yard line, defensive 15-yard personal foul on an incomplete pass. Half the distance from the 10 to the defense's goal is 5. Accept: ball on the defense's 5, first-and-goal. [14-2-1]
- Example 5: the offense's own 4-yard line, false start (5 yards). Half the distance to its goal line is 2. Accept: ball on own 2, same down. [14-2-1, 14-4-1]
- Example 6: defensive offside (5 yards) and offensive holding on the same play. Double foul: offset, replay the down at the previous spot, same down and distance; no choice. [14-5-1]
- Example 7: defensive pass interference on a pass thrown to the defense's 20 from the offense's own 40: first down at the defense's 20 (spot of the foul), no half-distance cap. [8-5]

