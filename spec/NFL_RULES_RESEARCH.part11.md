#### Kickoffs excluding onside kicks: 2026 regular season (79 games)
- Kickoffs: 805, 10.19 per game (both teams)
- Touchback rate (touchback flag on the kickoff row): 15.8% (127); kicks into the end zone 9.1%; returned (a returner is named, no touchback) 81.7% (658); any returner named incl. from the end zone 81.7%; fair catch 0.0%; out of bounds 0.9%; downed 0.0%; return touchdowns 0
- Average starting yard line of the receiving team after all kickoffs (own yard line, from the next scrimmage row; n=794): 30.2; after returns only: 29.8 (n=667); median all 30
- Spots after touchbacks (own yard line: count): 35: 102, 20: 24, 25: 1
- Kick distance (yards): mean 60.7, median 62; return yards on returns: mean 26.1, median 25, 90th percentile 33; returns of 40 or more yards: 32
- Starting yard line percentiles after all kickoffs (10, 25, 50, 75, 90): 20, 26, 30, 35, 38.7


### 5. Replay: challenges and reviews (regular season; playoffs at the end of this section)

What is counted: every play with replay_or_challenge=1. Coach challenges are the ones whose text says "X challenged the ... ruling"; replay-official reviews say "The Replay Official reviewed the ... ruling". A reversed challenge costs no timeout; an upheld one costs a timeout (all upheld coach challenges carry the timeout mark in the text, 100 percent). The nflverse file records no time or length of a review.

#### 2026 regular season to date (79 games, 158 team-games)
- Plays with replay_or_challenge=1: 94. Coach challenges: 36 (0.456 per game, 0.228 per team per game), reversed 18 = 50.0%. Replay-official reviews: 58 (0.734 per game), reversed 43 = 74.1%. All reviews 1.190 per game
- Share of all reviews started by a coach: 38.3%; by the replay official: 61.7%
- Lost challenges (upheld): 18 = 0.114 per team per game; of these 18 carry a "(Timeout #n.)" mark in the text and have timeout=1 (100.0%)
- Through week 7: coach challenges 36, reversed 18 (50.0%); all reviews 94 (coach 36, official 58)
- Coach challenges per team per game: 0: 77.8%, 1: 21.5%, 2: 0.6%
- Coach challenges per game, both teams: 0: 57.0%, 1: 40.5%, 2: 2.5%
- Team spread (coach challenges per team per game): mean 0.228, SD 0.174, min 0.00 (ARI), max 0.60 (TB); SD expected from chance alone 0.215
- Coach challenge by the team that had the ball on the challenged play: offense 30.6%, defense 69.4% (n=36)
- Coach challenges by quarter: Q1 19.4%, Q2 41.7%, Q3 22.2%, Q4 16.7%, QOT 0.0%
- Replay-official reviews by quarter: Q1 10.3%, Q2 36.2%, Q3 12.1%, Q4 39.7%, QOT 1.7%
- Replay-official reviews in the last two minutes of a half: 26 = 44.8%
- Coach challenges in the last two minutes of a half (the rule bars them for plays that begin after the warning): 0
- Play type of the reviewed play: pass 67, run 23, kickoff 2, no_play 2
- Coach challenges by category (count; reversed share):
  - catch or no catch (pass completion, incomplete pass): 18 (50.0% of coach challenges); reversed 55.6%
  - spot and line to gain (first down, short of the line to gain): 9 (25.0% of coach challenges); reversed 22.2%
  - down by contact (runner or passer, down or not down): 5 (13.9% of coach challenges); reversed 80.0%
  - goal line and touchdown (broke the plane, short of the goal line): 2 (5.6% of coach challenges); reversed 100.0%
  - fumble and loose ball (fumble, loose ball recovery): 1 (2.8% of coach challenges); reversed 0.0%
  - forward or backward pass, tipped pass: 1 (2.8% of coach challenges); reversed 0.0%
  - detail, rulings with 10 or more cases: pass completion 11 (rev 55%)
- Replay-official reviews by category (count; reversed share):
  - catch or no catch (pass completion, incomplete pass): 14 (24.1% of replay-official reviews); reversed 71.4%
  - down by contact (runner or passer, down or not down): 10 (17.2% of replay-official reviews); reversed 70.0%
  - goal line and touchdown (broke the plane, short of the goal line): 10 (17.2% of replay-official reviews); reversed 70.0%
  - spot and line to gain (first down, short of the line to gain): 9 (15.5% of replay-official reviews); reversed 77.8%
  - fumble and loose ball (fumble, loose ball recovery): 8 (13.8% of replay-official reviews); reversed 75.0%
  - out of bounds or inbounds (runner out of bounds, runner inbounds, ball inbounds): 3 (5.2% of replay-official reviews); reversed 100.0%
  - interception: 3 (5.2% of replay-official reviews); reversed 66.7%
  - forward or backward pass, tipped pass: 1 (1.7% of replay-official reviews); reversed 100.0%
  - detail, rulings with 10 or more cases: pass completion 12 (rev 75%)
#### 2024 and 2025 regular seasons combined (544 games, 1088 team-games)
- Plays with replay_or_challenge=1: 649. Coach challenges: 284 (0.522 per game, 0.261 per team per game), reversed 129 = 45.4%. Replay-official reviews: 365 (0.671 per game), reversed 282 = 77.3%. All reviews 1.193 per game
- Share of all reviews started by a coach: 43.8%; by the replay official: 56.2%
- Lost challenges (upheld): 155 = 0.142 per team per game; of these 155 carry a "(Timeout #n.)" mark in the text and have timeout=1 (100.0%)
- Through week 7: coach challenges 113, reversed 57 (50.4%); all reviews 254 (coach 113, official 141)
- Coach challenges per team per game: 0: 76.7%, 1: 20.9%, 2: 2.2%, 3: 0.3%
- Coach challenges per game, both teams: 0: 59.0%, 1: 31.6%, 2: 7.9%, 3: 1.1%, 4: 0.4%
- Team spread (coach challenges per team per game): mean 0.261, SD 0.096, min 0.12 (KC), max 0.50 (GB); SD expected from chance alone 0.088
- Coach challenge by the team that had the ball on the challenged play: offense 29.6%, defense 70.4% (n=284)
- Coach challenges by quarter: Q1 22.2%, Q2 23.6%, Q3 26.8%, Q4 27.5%, QOT 0.0%
- Replay-official reviews by quarter: Q1 11.5%, Q2 40.8%, Q3 12.3%, Q4 34.2%, QOT 1.1%
- Replay-official reviews in the last two minutes of a half: 164 = 44.9%
- Coach challenges in the last two minutes of a half (the rule bars them for plays that begin after the warning): 0
- Play type of the reviewed play: pass 486, run 139, no_play 11, punt 7, kickoff 5, field_goal 1
- Coach challenges by category (count; reversed share):
  - catch or no catch (pass completion, incomplete pass): 144 (50.7% of coach challenges); reversed 45.1%
  - spot and line to gain (first down, short of the line to gain): 75 (26.4% of coach challenges); reversed 48.0%
  - down by contact (runner or passer, down or not down): 32 (11.3% of coach challenges); reversed 50.0%
  - goal line and touchdown (broke the plane, short of the goal line): 13 (4.6% of coach challenges); reversed 53.8%
  - kicks and safety (kick touched, kick downed, touchback, safety): 6 (2.1% of coach challenges); reversed 0.0%
  - forward or backward pass, tipped pass: 5 (1.8% of coach challenges); reversed 40.0%
  - out of bounds or inbounds (runner out of bounds, runner inbounds, ball inbounds): 5 (1.8% of coach challenges); reversed 40.0%
  - fumble and loose ball (fumble, loose ball recovery): 2 (0.7% of coach challenges); reversed 0.0%
  - other (too many players, spot of a foul): 2 (0.7% of coach challenges); reversed 50.0%
  - detail, rulings with 10 or more cases: pass completion 96 (rev 45%); incomplete pass 48 (rev 46%); first down 41 (rev 46%); short of the line to gain 34 (rev 50%); runner was down by contact 23 (rev 48%); short of the goal line 12 (rev 50%)
- Replay-official reviews by category (count; reversed share):
  - catch or no catch (pass completion, incomplete pass): 90 (24.7% of replay-official reviews); reversed 72.2%
  - goal line and touchdown (broke the plane, short of the goal line): 74 (20.3% of replay-official reviews); reversed 83.8%
  - down by contact (runner or passer, down or not down): 45 (12.3% of replay-official reviews); reversed 80.0%
  - fumble and loose ball (fumble, loose ball recovery): 41 (11.2% of replay-official reviews); reversed 82.9%
  - interception: 35 (9.6% of replay-official reviews); reversed 68.6%
  - out of bounds or inbounds (runner out of bounds, runner inbounds, ball inbounds): 35 (9.6% of replay-official reviews); reversed 82.9%
  - spot and line to gain (first down, short of the line to gain): 31 (8.5% of replay-official reviews); reversed 64.5%
  - kicks and safety (kick touched, kick downed, touchback, safety): 8 (2.2% of replay-official reviews); reversed 87.5%
  - forward or backward pass, tipped pass: 5 (1.4% of replay-official reviews); reversed 80.0%
  - other (too many players, spot of a foul): 1 (0.3% of replay-official reviews); reversed 100.0%
  - detail, rulings with 10 or more cases: pass completion 70 (rev 73%); runner broke the plane 63 (rev 86%); fumble 40 (rev 82%); interception 35 (rev 69%); runner was not down by contact 34 (rev 82%); incomplete pass 20 (rev 70%); runner was out of bounds 18 (rev 94%); first down 18 (rev 67%); runner was inbounds 13 (rev 69%); short of the line to gain 13 (rev 62%); short of the goal line 11 (rev 73%)
### 6. Clock: plays, plays per quarter, time from snap to snap (regular season)

What is counted: "scrimmage plays" are pass and run plays that stood (sacks and scrambles included, kneel-downs, spikes, two-point tries and plays a foul wiped out excluded) in regulation. "Snaps" also include kneel-downs, spikes, punts and field goal tries. The clock at the snap of each play is in the data; elapsed seconds are the difference between two snaps in the same quarter. "Normal rules" means the clock after an out-of-bounds play restarts at the referee's ready signal; "late-half rules" means the last 5:00 of the second half and the last 2:00 of the first half, where it restarts at the snap. Pairs with a timeout or a dead-ball foul in between are reported apart. The figure over 25 seconds is the share of plays after which the clock kept running into the next snap.

#### 2026 regular season to date (79 games, 158 team-games)
- Scrimmage plays (pass, run incl. sacks and scrambles, no kneel or spike): 9555 in regulation, 60.47 per team per game, 120.95 per game; overtime 103
- Per quarter, both teams together, per game: Q1 27.57, Q2 33.42, Q3 27.89, Q4 32.08; per team per game: Q1 13.78, Q2 16.71, Q3 13.94, Q4 16.04
- All snaps from scrimmage including kneel-downs, spikes, punts and field goal tries (no kickoffs, no extra points): 134.42 per game, 67.21 per team per game; per quarter per game: Q1 30.30, Q2 37.49, Q3 30.51, Q4 36.11
- Game-clock seconds per scrimmage play (3600 divided by plays per game): 29.8; per snap including kicks, kneels and spikes: 26.8
- Plays in the last two minutes (clock 2:00 or less; kneel and spike included, pass and run): second quarter 9.53 per game, fourth quarter 7.13 per game, together 16.66 per game (8.33 per team per game)
- Snap pairs measured (a snap and the next snap in the same quarter): 10188; not measured: {'no next snap in the quarter': 964}
- Pairs with nothing between the snaps (no timeout, no foul before the snap, no two-minute warning): 9323 (91.5%); with a timeout between: 443 (4.3%); with a dead-ball foul between: 286 (2.8%); spanning the two-minute warning: 155
- Elapsed game-clock seconds from one snap to the next, by kind of the first play; NORMAL clock rules (not in the last 5:00 of the second half and not in the last 2:00 of the first half); nothing between the snaps; columns: n; mean; percentiles 10, 50, 90; share over 25 s (running clock):
  - pass complete, in bounds: n=1756, mean 38.1, 10th 27, median 40, 90th 45, over 25 s 92.4%
  - pass complete, out of bounds: n=444, mean 31.7, 10th 22, median 33, 90th 39, over 25 s 84.2%
  - pass incomplete: n=1217, mean 5.1, 10th 3, median 5, 90th 7, over 25 s 0.0%
  - run, in bounds: n=2923, mean 38.4, 10th 32, median 40, 90th 45, over 25 s 95.0%
  - run, out of bounds: n=240, mean 33.5, 10th 26, median 35, 90th 40, over 25 s 90.0%
  - sack: n=225, mean 37.3, 10th 17, median 41, 90th 45, over 25 s 88.0%
  - punt: n=492, mean 9.4, 10th 7, median 9, 90th 13, over 25 s 0.0%
  - field goal (missed): n=32, mean 4.7, 10th 4, median 4, 90th 5, over 25 s 0.0%
  - live play nullified by a foul: n=421, mean 15.7, 10th 4, median 15, 90th 28, over 25 s 20.4%
  - turnover (interception or fumble lost): n=105, mean 8.9, 10th 5, median 8, 90th 13, over 25 s 1.0%
  - ALL of these kinds together: n=7855, mean 29.1, median 36, over 25 s 67.1%
- Elapsed game-clock seconds from one snap to the next, by kind of the first play; LATE-HALF clock rules (last 5:00 of the second half, last 2:00 of the first half); nothing between the snaps; columns: n; mean; percentiles 10, 50, 90; share over 25 s (running clock):
  - pass complete, in bounds: n=389, mean 21.2, 10th 6, median 21, 90th 40, over 25 s 31.1%
  - pass complete, out of bounds: n=132, mean 6.1, 10th 4, median 6, 90th 8, over 25 s 0.8%
  - pass incomplete: n=320, mean 4.8, 10th 3, median 5, 90th 7, over 25 s 0.0%
  - run, in bounds: n=291, mean 26.8, 10th 5, median 33, 90th 45, over 25 s 57.0%
  - run, out of bounds: n=24, mean 7.0, 10th 5, median 7, 90th 8, over 25 s 0.0%
  - sack: n=63, mean 15.4, 10th 5, median 8, 90th 33, over 25 s 22.2%
  - punt: n=61, mean 8.8, 10th 6, median 8, 90th 12, over 25 s 0.0%
  - live play nullified by a foul: n=77, mean 5.7, 10th 3, median 6, 90th 8, over 25 s 0.0%
  - kneel-down: n=56, mean 33.5, 10th 18, median 39, 90th 42, over 25 s 78.6%
  - spike: n=23, mean 1.0, 10th 1, median 1, 90th 1, over 25 s 0.0%
  - turnover (interception or fumble lost): n=30, mean 8.6, 10th 6, median 8, 90th 11, over 25 s 0.0%
  - ALL of these kinds together: n=1466, mean 15.5, median 7, over 25 s 23.6%
- With a timeout between the snaps (normal rules): n=116, mean 26.2, 10th 4, median 32, 90th 45
- With a timeout between the snaps (late-half rules): n=313, mean 10.4, 10th 4, median 6, 90th 24
- With a dead-ball foul between the snaps (all rules): n=281, mean 37.6, 10th 5, median 46, 90th 64
- Spanning the two-minute warning: n=155, mean 20.6, median 19
- Share of plays followed by a running clock (elapsed over 25 s; normal rules, nothing between the snaps): 67.1% of 7855
- Estimate of the time from snap to the end of the play, from plays after which the clock is stopped until the next snap (the elapsed time then equals the length of the play, to the nearest second):
  - incomplete pass (all clock rules, nothing between): n=1537, mean 5.06, median 5, 10th 3, 90th 7
  - pass complete, out of bounds with late-half rules (clock restarts at the snap): n=132, mean 6.08, median 6, 10th 4, 90th 8
  - run, out of bounds with late-half rules (clock restarts at the snap): n=24, mean 7.00, median 7, 10th 5, 90th 8
  - pass complete, in bounds followed by a timeout (upper bound, includes the time until the timeout was called): n=88, mean 22.0, median 18, 10th 5, 90th 44
  - run, in bounds followed by a timeout (upper bound, includes the time until the timeout was called): n=118, mean 19.8, median 7, 10th 4, 90th 44
  - sack followed by a timeout (upper bound, includes the time until the timeout was called): n=24, mean 18.8, median 8, 10th 5, 90th 44
  - pass complete, in bounds, normal rules: first play snapped in no-huddle: n=97 mean 32.7; not no-huddle: n=1659 mean 38.5
  - run, in bounds, normal rules: first play snapped in no-huddle: n=108 mean 37.1; not no-huddle: n=2815 mean 38.4
#### 2024 and 2025 regular seasons combined (544 games, 1088 team-games)
- Scrimmage plays (pass, run incl. sacks and scrambles, no kneel or spike): 65784 in regulation, 60.46 per team per game, 120.93 per game; overtime 364
- Per quarter, both teams together, per game: Q1 27.23, Q2 32.82, Q3 27.76, Q4 33.12; per team per game: Q1 13.62, Q2 16.41, Q3 13.88, Q4 16.56
- All snaps from scrimmage including kneel-downs, spikes, punts and field goal tries (no kickoffs, no extra points): 134.05 per game, 67.02 per team per game; per quarter per game: Q1 29.76, Q2 36.86, Q3 30.17, Q4 37.25
- Game-clock seconds per scrimmage play (3600 divided by plays per game): 29.8; per snap including kicks, kneels and spikes: 26.9
- Plays in the last two minutes (clock 2:00 or less; kneel and spike included, pass and run): second quarter 9.35 per game, fourth quarter 6.78 per game, together 16.13 per game (8.07 per team per game)
- Snap pairs measured (a snap and the next snap in the same quarter): 69570; not measured: {'no next snap in the quarter': 6575, 'dropped elapsed <0 or >150': 11}
- Pairs with nothing between the snaps (no timeout, no foul before the snap, no two-minute warning): 63876 (91.8%); with a timeout between: 3206 (4.6%); with a dead-ball foul between: 1556 (2.2%); spanning the two-minute warning: 1064
- Elapsed game-clock seconds from one snap to the next, by kind of the first play; NORMAL clock rules (not in the last 5:00 of the second half and not in the last 2:00 of the first half); nothing between the snaps; columns: n; mean; percentiles 10, 50, 90; share over 25 s (running clock):
  - pass complete, in bounds: n=12313, mean 37.9, 10th 26, median 39, 90th 45, over 25 s 91.3%
  - pass complete, out of bounds: n=3333, mean 35.2, 10th 25, median 37, 90th 43, over 25 s 89.4%
  - pass incomplete: n=8149, mean 5.0, 10th 3, median 5, 90th 7, over 25 s 0.0%
  - run, in bounds: n=19985, mean 38.0, 10th 30, median 39, 90th 44, over 25 s 93.8%
  - run, out of bounds: n=1766, mean 36.8, 10th 27, median 38, 90th 44, over 25 s 92.5%
  - sack: n=1827, mean 37.7, 10th 21, median 41, 90th 46, over 25 s 87.7%
  - punt: n=3213, mean 9.4, 10th 7, median 9, 90th 13, over 25 s 0.0%
  - field goal (missed): n=196, mean 4.8, 10th 4, median 5, 90th 6, over 25 s 0.0%
  - live play nullified by a foul: n=2494, mean 15.4, 10th 4, median 15, 90th 29, over 25 s 21.7%
  - turnover (interception or fumble lost): n=745, mean 8.4, 10th 5, median 8, 90th 12, over 25 s 0.0%
  - ALL of these kinds together: n=54021, mean 29.5, median 36, over 25 s 68.0%
- Elapsed game-clock seconds from one snap to the next, by kind of the first play; LATE-HALF clock rules (last 5:00 of the second half, last 2:00 of the first half); nothing between the snaps; columns: n; mean; percentiles 10, 50, 90; share over 25 s (running clock):
  - pass complete, in bounds: n=2440, mean 21.6, 10th 6, median 21, 90th 41, over 25 s 31.3%
  - pass complete, out of bounds: n=841, mean 6.4, 10th 4, median 6, 90th 8, over 25 s 1.1%
  - pass incomplete: n=2179, mean 4.9, 10th 3, median 5, 90th 7, over 25 s 0.0%
  - run, in bounds: n=2296, mean 26.4, 10th 5, median 30, 90th 45, over 25 s 54.2%
  - run, out of bounds: n=199, mean 7.7, 10th 5, median 7, 90th 9, over 25 s 0.5%
  - sack: n=374, mean 19.7, 10th 5, median 10, 90th 43, over 25 s 37.2%
  - punt: n=417, mean 9.2, 10th 7, median 9, 90th 12, over 25 s 0.0%
  - field goal (missed): n=52, mean 4.5, 10th 4, median 4, 90th 5, over 25 s 0.0%
  - live play nullified by a foul: n=479, mean 5.7, 10th 4, median 5, 90th 8, over 25 s 0.0%
  - kneel-down: n=270, mean 33.2, 10th 18, median 37, 90th 42, over 25 s 80.0%
  - spike: n=142, mean 1.0, 10th 1, median 1, 90th 1, over 25 s 0.0%
  - turnover (interception or fumble lost): n=166, mean 7.7, 10th 4, median 7, 90th 12, over 25 s 0.0%
  - ALL of these kinds together: n=9855, mean 15.8, median 8, over 25 s 24.1%
- With a timeout between the snaps (normal rules): n=816, mean 26.1, 10th 4, median 34, 90th 44
- With a timeout between the snaps (late-half rules): n=2300, mean 11.7, 10th 4, median 6, 90th 39
- With a dead-ball foul between the snaps (all rules): n=1514, mean 38.1, 10th 5, median 46, 90th 65
- Spanning the two-minute warning: n=1064, mean 20.9, median 18
- Share of plays followed by a running clock (elapsed over 25 s; normal rules, nothing between the snaps): 68.0% of 54021
- Estimate of the time from snap to the end of the play, from plays after which the clock is stopped until the next snap (the elapsed time then equals the length of the play, to the nearest second):
  - incomplete pass (all clock rules, nothing between): n=10328, mean 4.99, median 5, 10th 3, 90th 7
  - pass complete, out of bounds with late-half rules (clock restarts at the snap): n=841, mean 6.36, median 6, 10th 4, 90th 8
  - run, out of bounds with late-half rules (clock restarts at the snap): n=199, mean 7.72, median 7, 10th 5, 90th 9
  - pass complete, in bounds followed by a timeout (upper bound, includes the time until the timeout was called): n=638, mean 20.8, median 16, 10th 6, 90th 43
  - run, in bounds followed by a timeout (upper bound, includes the time until the timeout was called): n=969, mean 21.6, median 10, 10th 4, 90th 45
  - sack followed by a timeout (upper bound, includes the time until the timeout was called): n=140, mean 18.5, median 8, 10th 5, 90th 45
  - pass complete, in bounds, normal rules: first play snapped in no-huddle: n=1336 mean 34.6; not no-huddle: n=10977 mean 38.3
  - run, in bounds, normal rules: first play snapped in no-huddle: n=1859 mean 35.9; not no-huddle: n=18126 mean 38.2

### 7. Cross-checks against published figures (and mismatches)

Format: published figure and where it comes from, then my figure, then the verdict. "Published" figures are those collected by the other topic notes (A_timeouts_clock, B_replay, C_qb, D_kicks, E3_penalty_stats) or named in the task.

Matches (exact or within rounding):
- Onside kicks, regular season. Topic D (The Football Database via USA Today and CBS): 2024 3 recoveries in 50 attempts, 2025 5 in 52. Mine: 2024 50 attempts, 3 recoveries (6.0 percent); 2025 52 attempts, 5 recoveries (9.6 percent). Exact match, including the safety free kicks (4 in each season).
- Coach challenges, regular season. Topic B (ESPN): 2024 133 challenges, 50 reversed (37.6 percent); 2025 151. Mine: 133 and 50 (37.6 percent); 151 (79 reversed, 52.3 percent). Exact. So ESPN's 151 for 2025 is regular season only (4 more coach challenges came in the playoffs).
- Through week 7 (ESPN, 2025-10-22): reversed 21 of 53 in 2024 and 36 of 60 in 2025; total reviews 117 and 137. Mine: 21 of 53, 36 of 60, and 117 and 137 reviews (coach challenges plus replay-official reviews). Exact, so ESPN's "reviews" means both kinds together.
- Replay-official success (ESPN: 76 percent in 2024). Mine 76.3 percent (148 of 194). The league figure of 171 "replay review or replay assist decisions" in 2025 (Troy Vincent, topic B) equals my count of replay-official reviews in the 2025 regular season (171), so it was probably the same set (a coincidence is not excluded).
- Accepted fouls (topic E3, nflpenalties.com, regular season): 3,506 (2024), 3,467 (2025), 1,191 (2026, 79 games). Mine: 3,512; 3,469; 1,193. Per game 12.91, 12.75, 15.10 against 12.89, 12.75, 15.08. Including playoffs: 3,648 and 3,565 against my 3,655 and 3,567; offensive holding 684 against my 685. Declined 466, 522, 132 against my 467, 525, 133. Offsetting flags 176, 147, 32: mine identical. Team extremes 2025 (Rams 4.41, Cowboys 7.82) and 2024 (Rams 5.35, Jets 8.06): identical. Accepted fouls by quarter 2025 incl. playoffs 754, 1,062, 828, 903, overtime 18 against mine 755, 1,063, 829, 902, 18. Penalty yards 27,871 and 28,410 against my 27,906 and 28,491 (0.1 to 0.3 percent more). The small excess is probably a few text segments that the site counts differently.
- Quarterback rushing (topic C, StatMuse): 2024 2,352 attempts and 11,015 yards, 2025 2,215 and 9,686. Mine with kneel-downs and aborted snaps (a fumbled snap that the quarterback picks up) included: 2,349 and 10,980; 2,212 and 9,682. Within 0.3 percent.
- Scramble rate per dropback (topic C, Fantasy Footballers): 5.3 percent (2024), 5.5 (2025). Mine 5.25 and 5.51.
- FOX Sports, 2024, third or fourth and 1, quarterback runs: Hurts 22 of 27, Allen 17 of 18, Nix 12 of 14, Daniels 12 of 12. Mine (all quarterback runs, scrambles and aborted snaps included, regular season): 22 of 27, 17 of 18, 12 of 14, 12 of 12. Exact. FOX also says teams ran 78 percent of the time on third or fourth and 1, runs converted 74 percent and passes 57 percent, about 1,200 plays. Mine, all runs including scrambles, aborted snaps left out: regular season 1,107 plays, 77.7 percent runs, runs converted 74.1 percent, passes 57.5 percent; regular season plus playoffs 1,173 plays, 78.2 percent, 74.4 percent, 57.6 percent. The percentages match either way; the play count is closer with the playoffs, the four quarterback lines match the regular season only.
- Sneak and tush push conversion on third or fourth and 1 (topic C, Sharp: league 84 percent since 2022): mine 83.4 percent for all designed quarterback runs (469 attempts, 2024 and 2025). The rollcoverage.com figure of 79.5 percent uses charted sneaks only and is another definition.
- Kickoffs (topic D). 2025 returns 2,076 (PFF, Sharp): mine 2,076, exact. 2024 returns 919: mine 917 (onside kicks excluded). Touchback rate 2024 64.3 percent: mine 65.5 percent without onside kicks, 64.3 percent (1,803 of 2,803) with them; 2025 20.7 percent: mine 21.1 percent, 20.7 percent with onside kicks (576 of 2,785). Average start after all kickoffs 2024 about 30 and after returns 29 (NFL via SI): mine 29.6 and 29.2.
- Plays per team per game. Rotowire 2024 62.2: mine 62.15 (pass, run, kneel-downs, spikes). Sharp 2025 61.3: mine 61.26.
- Time between snaps. Topic A estimated "about 28 to 29 game-clock seconds per counted scrimmage play" and "about three quarters of plays followed by a running clock". Mine: 29.8 seconds (30.0 in 2025) and 68.0 percent. The 28 to 29 estimate was close; the 75 percent was too high because the kicks and incomplete passes take part of the clock too.

Mismatches:
- NFL.com "Scrm Plys" (topic E3): 63.27 per team per game in 2025 and 64.1 in 2026 to date. Mine for plays that stood: 61.26 and 62.07 (incl. kneel-downs and spikes). Likely reason, not verified: the NFL.com total includes plays nullified by a foul (my count of live plays that a foul wiped out: 2.86 per team per game in 2025 and 3.38 in 2026; adding them gives 64.1 and 65.5, which brackets the NFL.com figure). Consequence: the foul rate per 100 plays depends on the denominator: 10.41 per 100 plays that stood (6.38 fouls over 61.26 plays), 9.95 per 100 including wiped-out plays, 10.07 with the NFL.com total.
- Average starting yard line (topic D): Sharp 30.8 for the return team in 2025, PFF 30.0 after returns in 2024. Mine 29.7 after returns in 2025 and 29.2 in 2024 (all kickoffs 30.3 and 29.6). Likely reason: the spot of the first scrimmage snap after a kickoff in the data includes the effect of a foul on the return, and the other sources may measure the spot of the catch or the drive start field. Not settled.
- Automatic first downs (topic E3, 822 in 2025 incl. playoffs, 23.1 percent of accepted fouls, defensive fouls with a first down regardless of distance): my flag first_down_penalty=1 is set whenever the foul itself produced the first down (979 in the 2025 regular season, 28.2 percent), so it also counts fouls whose yardage alone was enough (defensive offside 21 percent, neutral zone 31 percent). The two measures differ by definition; use the per-type shares of section 3 (99 to 100 percent: defensive pass interference, defensive holding, illegal contact) for the automatic ones.
- Sharp 2026 plays per team per game 61.16 (topic A): mine 61.13 for pass and run only, 62.07 with kneel-downs and spikes. Consistent if Sharp leaves out kneel-downs and spikes, but then its 2025 value 61.3 would not match mine (60.3 without them); the basis of the Sharp table is not known.
- Topic E3 and topic C counts for 2025 tush pushes (112, 130) cannot be tested: a sneak and a tush push cannot be told apart in the data.

No published figure existed (so no check possible): timeouts used per team per game, timeouts left at the end of each half, timeouts by time left, sub-groups of fouls (phase, last two minutes), all yards-by-down quarterback numbers, onside kicks by margin, snap-to-snap time by kind of play. Their only internal check: the nflverse field home_timeouts_remaining or away_timeouts_remaining on the last row of each half equals 3 minus the timeouts I counted in 99.4 percent of 2,176 team-halves (2024 and 2025).

### 8. Playoffs (season_type POST), kept apart

Two seasons of 13 games each. Too few games for any rate; shown only so that nothing is mixed in silently. Accepted fouls per game 11.0 (2024) and 7.5 (2025) against about 12.8 in the regular season; charged timeouts per team per game 3.96 and 4.54; playoff overtime: 2 games in 2025 (six timeouts charged in overtime), none in 2024.

#### Playoffs 2024 (13 games, 26 team-games; very small sample)
- Charged team timeouts: 103, 3.96 per team per game (coach-called 3.81); first half 1.85, second half 2.12, overtime 0
- Accepted fouls: 143, 11.00 per game (both teams), 5.50 per team per game; yards per team per game 44.2; before the snap 37.8%
- Scrimmage plays (pass and run) per team per game: 60.27
- QB rushes per team per game 5.88 (designed 3.15, scrambles 2.73); yards per attempt 5.66
- Onside kicks: 4 attempts, 0 recovered by the kickers
- Replay: 19 reviews, 6 coach challenges (2 reversed), 13 replay-official reviews; per game 1.46
- Games with overtime: 0
#### Playoffs 2025 (13 games, 26 team-games; very small sample)
- Charged team timeouts: 118, 4.54 per team per game (coach-called 4.50); first half 2.38, second half 1.92, overtime 6
- Accepted fouls: 98, 7.54 per game (both teams), 3.77 per team per game; yards per team per game 30.8; before the snap 40.8%
- Scrimmage plays (pass and run) per team per game: 64.96
- QB rushes per team per game 4.04 (designed 1.88, scrambles 2.15); yards per attempt 6.03
- Onside kicks: 1 attempts, 0 recovered by the kickers
- Replay: 13 reviews, 4 coach challenges (3 reversed), 9 replay-official reviews; per game 1.00
- Games with overtime: 2


### Could not settle

- Slides. The text of a play never says that a quarterback slid; a slide ends the play at the spot, so it looks like a normal run that ends in bounds. I can only report the out-of-bounds share (12.1 percent of designed runs, 34.0 percent of scrambles).
- Quarterback sneaks and tush pushes. The text of a sneak has no special word ("up the middle" or a gap name only), and the data have no formation field. My proxy is a designed quarterback run "up the middle" on third or fourth and 1 or 2; it contains plain quarterback draws, and it misses sneaks that are written with a gap name. Eagles tush pushes cannot be separated from ordinary sneaks. Result: the conversion rate of 83 percent is for designed quarterback runs on third or fourth and 1, whatever their form.
- A true split between designed keepers and scrambles. The word "scrambles" appears in the text only when the quarterback gained yards; a called pass that ends in a no-gain or loss run is written as a plain run and falls into my "designed" group (scrambles show 0.1 percent at zero or less). The designed group is therefore a little contaminated and its zero-or-negative share (20.3 percent) a little too high. No field in the data tells the two apart.
- Position of players. The file has no position column. Quarterbacks are players who threw on at least 10 regular-season pass plays in 2024 to 2026, minus Taysom Hill (a tight end who throws now and then; he has exactly 10 pass plays in the sample, so he met the threshold and I removed him by his id 00-0033357). A quarterback who only ran or knelt and never threw 10 times is missed (about 17 kneel-downs of 433 in 2025 have a rusher outside my list; no scramble effect larger than 2 plays per season).
- Length of a play from snap to the whistle. Not recorded. The estimate in section 6 from clock-stopped plays is an indirect measure (incomplete passes 5.0 seconds on average) and exists only for plays that stop the clock. For plays that leave the clock running (runs and catches in bounds) I have only an upper bound.
- The two-minute warning, injury timeouts and official timeouts are not rows. I used "2:00 left in the half" as the threshold for the warning, which is exact when the play before the warning ends at or above 2:00 on the clock and approximate otherwise.
- Timeouts: whether the 18 "Timeout #4" rows are excess timeouts for an injury is a reading of the text around them (all 18 are in the last two minutes of a half and have an injury mention within the three plays before); the rulebook side belongs to topic A.
- Timeout counts by overtime period (the postseason rule of three per half of overtime): no postseason overtime period with a second pair of periods exists in the sample (2 postseason overtime games in 2025, none in 2024).
- Penalty "phase": the data say what the play was, not whether a foul was before the snap. My phase uses the foul type for the before-the-snap group (false start, offside, neutral zone, encroachment, delay of game, illegal formation, shift, motion, too many men, defensive delay) and the play type of the row for the rest; a foul such as defensive offside that was called with a free play still counts as before the snap (about 29 percent of the before-the-snap fouls were called with the play running, see section 3).
- Penalty "last two minutes" and "per play" rates use the standing plays (and the nullified live plays) in those minutes; the exact number of plays in the minutes where a foul wiped out the play is estimated from the text (a play description that is not a pre-snap foul).
- The share of declined fouls that were declined by the offense or by the defense; the reasons for declining. The data give the declined foul's type and team; who declined is the other team by rule, but the reason (the play result being better) is not in the data.
- Challenges by team-game for 2026 are very small samples (36 coach challenges).
- Playoffs: 13 games per season (two seasons) are too few for any rate; section 8 lists them only for completeness.
- Per-snap clock effects of no-huddle offense: the no_huddle flag exists, but the number of plays is small at the late-half rules; shown in section 6 only for the normal rules.

### Sources and method

Data files (the three files the owner approved; downloaded 2026-10-14 with curl -L; kept in a temporary folder outside the project; the data dictionary named below is a fourth, small documentation file that was not on the approved list):
- https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_2024.csv.gz, 19,362,351 bytes, SHA-256 23370d5d10f8104d80d46a1fc5e61f4f6f5a3263fe96fe2dd629913cfcb08c06, 49,492 rows (plays) and 372 columns; 272 regular-season and 13 postseason games.
- https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_2025.csv.gz, 19,105,296 bytes, SHA-256 2f135887790a013fd004e609e37096bb4816d5cc80b9f19122e1bad478961978, 48,771 rows; 272 regular-season and 13 postseason games.
- https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_2026.csv.gz, 5,434,245 bytes, SHA-256 f6dca321749fc6ddbfa32cfb85c9818ab2b270ceae64a45299a46e9251cbd8fb, 13,842 rows; 79 regular-season games (weeks 1 to 5, 16 + 16 + 16 + 16 + 15 games, 2026-09-09 to 2026-10-12).
- Data dictionary: https://nflreadr.nflverse.com/articles/dictionary_pbp.html was fetched with WebFetch on 2026-10-14, but the page text contains only the navigation (the field table is script-rendered). The same dictionary table was read as a CSV from the nflreadr repository: https://raw.githubusercontent.com/nflverse/nflreadr/main/data-raw/dictionary_pbp.csv (39,127 bytes, retrieved with curl, kept in the temporary folder h_docs). Definitions used (quoted shortly): season_type "REG or POST"; half_seconds_remaining and quarter_seconds_remaining "seconds remaining in the half or quarter"; timeout and timeout_team "a timeout was called by either team"; home_timeouts_remaining "timeouts remaining in the half for the home team"; qb_scramble, qb_kneel, qb_spike binary; replay_or_challenge and replay_or_challenge_result "indicator for a replay or challenge" and its result; penalty "a penalty occurred"; first_down_penalty "a penalty converted the first down"; play_type "pass (includes sacks), run (includes scrambles), punt, field_goal, kickoff, extra_point, qb_kneel, qb_spike, no_play (timeouts and penalties)"; kickoff_attempt, own_kickoff_recovery "the kicking team recovered the kickoff"; touchback; out_of_bounds "1 if play description contains ran ob, pushed ob, or sacked ob"; aborted_play "the description indicates Aborted".
- Official comparison material: none used for numbers. Published figures used for cross-checks come from the other topic notes (A_timeouts_clock.md, B_replay.md, C_qb.md, D_kicks.md, E3_penalty_stats.md in the same notes folder) and are SRC-SECONDARY there.

Tools and safety:
- Python 3.10.11 from the PATH, run as python -I script.py <data folder> <cache folder>, standard library only (gzip, csv, re, pickle for my own cache, collections, math). pandas is not installed; nothing was installed. The data were only read as text; nothing from them was executed or evaluated.
- Scripts (a copy is in the shared notes folder, sx0_raw_notes/scripts_stats) were kept in a folder scripts_stats, different from the data folder: hload.py (loader and cache of 146 columns, a pickle of my own derived rows in h_cache), hcommon.py (helpers), s1_timeouts.py, s2_qb.py, s2b_shorty.py, s3_pen.py, s4_kicks.py, s5_replay.py, s6_clock.py, s7_post.py. The outputs they print are in the temporary folder h_out (s1.txt to s7.txt) and are included below under each section. Nothing was written to the project folder.

Definitions and filters, by section (all use season_type REG unless the heading says playoffs; a "team-game" is one team in one game):
- Plays that stand ("scrimmage plays"): play_type pass or run, two_point_attempt not 1 (pass includes sacks, run includes scrambles); "standing plays" adds qb_kneel and qb_spike. Plays that a foul wiped out have play_type no_play. Kickoffs, punts, field goals and extra points are separate play types.
- Games, per team per game: distinct game_id counts; team-games are twice that.
- Section 1 (timeouts): rows with timeout=1. Two kinds. (a) play_type no_play and the text "Timeout #n by TEAM at mm:ss": a timeout called by the coach (team from timeout_team). (b) timeout=1 on a pass, run, kickoff or punt row whose text says "TEAM challenged the ... ruling, and the play was Upheld" and ends with "(Timeout #n.)": the timeout that a lost challenge costs (team from timeout_team). Half from qtr (1 and 2 first, 3 and 4 second, 5 overtime). Time left from half_seconds_remaining of that row. Used in a half = the highest n of "Timeout #n" of that team in that half; remaining = 3 minus used. Leading, tied or trailing: total_home_score minus total_away_score on the row (carried forward from the last row that has it), seen from the team that took the timeout. Offense or defense: the posteam of the next row that has a posteam in the same half, unless that row is a kickoff or in another half, then the posteam of the previous play row; for a lost challenge the posteam of the row. Grouping of the last 5 minutes: the score on the last row with more than 300 half seconds left. The two-minute warning is approximated by half_seconds_remaining of 120 or less.
- Section 2 (quarterback runs): a quarterback rush is play_type run, rusher_player_id in my quarterback list (passers with at least 10 pass plays in REG 2024 to 2026, minus 00-0033357), two_point_attempt not 1, aborted_play not 1. Scramble = qb_scramble 1; designed = the rest. Kneel-downs (play_type qb_kneel), spikes (qb_spike) and sacks (sack=1 on a pass) are counted apart. Dropbacks: qb_dropback 1 on pass and run plays that stand. Yards: yards_gained. First down or touchdown: first_down_rush or rush_touchdown. Fumble lost: fumble_lost 1 and fumbled_1_player_id equal to the rusher. Down and distance: down and ydstogo (buckets 1, 2, 3 to 5, 6 to 10, 11 or more). Field zones: yardline_100 (51 to 99 own half, 11 to 50 opponent half, 6 to 10, 1 to 5). Out of bounds: out_of_bounds 1. Sneak proxy: designed run with run_location middle on third or fourth down with ydstogo 1 or 2.
- Section 3 (penalties): accepted foul = each text segment "PENALTY on TEAM-player, Type, N yards" in upper case in desc (the flag penalty=1 is set on exactly the rows that have such a segment; checked: 3,384 rows with only an accepted foul, 76 with an accepted and a declined one, 1 with an accepted and an offsetting one, in 2025; no row has penalty=1 without one). Declined fouls and offsetting fouls are NOT flagged (penalty=0 or empty, penalty_type empty); they exist only in the text as "Penalty on TEAM-player, Type, declined" and "..., offsetting" (lower case). Method reliability: my accepted, declined and offsetting counts are within 0.2 percent, 0.6 percent and exactly equal to those of nflpenalties.com (section 7); the type of my parse equals the nflverse penalty_type of the row for 3,463 of 3,469 accepted fouls in 2025. Offsetting counts are flags, not events (two flags per offsetting pair, sometimes three or four). Examples of the three text forms in the 2025 data (shortened): accepted, "(14:15) (No Huddle) PENALTY on TB, Delay of Game, 5 yards, enforced at MIA 49 - No Play." (play_type no_play, penalty=1); declined, "(9:36) (Shotgun) 10-B.Nix pass incomplete short middle to 14-C.Sutton. Penalty on DEN-13-P.Bryant, Offensive Offside, declined." (play_type pass, penalty=0, penalty_type empty); offsetting, "... Penalty on ATL-63-C.Lindstrom, Offensive Holding, offsetting, enforced at TB 4 - No Play. Penalty on TB-35-J.Dean, Defensive Holding, offsetting." (play_type no_play, penalty flag empty). Yards = the number in the text (kickoff fouls that place the ball have none: counted as 0). Phase and play kind: see "Could not settle". Standing plays are the denominator unless stated. First-down share = first_down_penalty. Team = the team in the text segment (the team that committed the foul).
- Section 4 (onside kicks, kickoffs): onside kick = play_type kickoff, kickoff_attempt 1 and the word onside in desc (re-kicks after a foul are separate rows; rows with kickoff_attempt blank or 0 are the nullified first kick and are not counted: 2 in 2024). Recovered by the kicking team = own_kickoff_recovery 1 (the text says RECOVERED by the kicker's team in all 8 cases). On kickoff rows posteam is the receiving team and defteam the kicking team. Margin of the kicker from total_home_score and total_away_score. Kickoff statistics exclude onside kicks: touchback = touchback 1; returned = kickoff_returner_player_id present and no touchback; start yard line = 100 minus yardline_100 of the next scrimmage row of the receiving team in the same quarter.
- Section 5 (replay): rows with replay_or_challenge=1. Coach challenge = text "X challenged the R ruling, and the play was Upheld or REVERSED"; replay-official review = "The Replay Official reviewed the R ruling, and the play was Upheld or REVERSED". Every one of the 649 rows (2024 and 2025) and the 94 rows of 2026 matched one of the two; no row with those words lacks the flag. Reversed = REVERSED in the text (replay_or_challenge_result reversed). The challenging team is read from the text (32 city names) and checked against timeout_team.
- Section 6 (clock): rows in the order of play_id within a game. A snap row = play_type pass, run, qb_kneel, qb_spike, punt, field_goal, or a no_play row whose text shows a play (the play ran and a foul wiped it out). The time of a row is the clock at the snap (checked on kickoffs and the start of each quarter). Elapsed = quarter_seconds_remaining of the first snap minus that of the next snap in the same quarter, with no kickoff, extra point, two-point try or end of quarter between them. A pair is discarded if the elapsed is negative or above 150 seconds (11 in 2024 and 2025). Pairs with a timeout row between, a dead-ball foul between, or the two-minute warning between (first snap above 2:00 left, next snap at 2:00 or less in the second or fourth quarter) are reported apart. Late-half rules = the last 5:00 of the second half or the last 2:00 of the first half (the clock restarts at the snap after an out-of-bounds play); normal rules = the rest.

## Part 10. Overtime (Rule 16), read again for SX.12

Read 2026-10-21 (session SX.12) from the 2026 Official Playing Rules of the NFL (PDF https://static.www.nfl.com/image/upload/fl_attachment/league/tqivdkzt9mu6wdgsh1ku.pdf, linked from https://operations.nfl.com/the-rules/nfl-rulebook/, cover "2026 OFFICIAL PLAYING RULES OF THE NATIONAL FOOTBALL LEAGUE"; converted with pdftotext 4.x to `work\sx12\rulebook_2026.txt`, not committed as a source). Rule 16 is on printed pages 64 to 66 and is numbered Section 1, Articles 1 to 5 (16-1-1 to 16-1-5; earlier parts of this file cite the same text as 16-3, 16-4, 16-5). Every line below is SRC-OFFICIAL unless it says otherwise.

Answers (what the clone builds, D-096):
- 16-1-1: a tied score at the end of regulation, in the regular season and the postseason, is followed by "modified sudden-death overtime". SRC-OFFICIAL.
- 16-1-2: at once a new coin toss at the center of the field, as the pregame toss (4-2-2); the visiting team's captain calls it again. SRC-OFFICIAL. 4-2-2: the winner chooses (a) to receive or kick off, or (b) the goal to defend; the loser gets the other. The pregame deferral is a deferral "to the second half", which overtime has not: the clone offers receive or kick only (reading, UNVERIFIED as a rule; the clone has no goals to choose).
- 16-1-3 (regular season), after an intermission of at most three minutes, one extra period of 10 minutes: (a) both teams must have the opportunity to possess the ball once, unless the team kicking off scores a safety on the receivers' initial possession, which wins; (b) after each team has had its opportunity, a team with more points wins (subject to 16-1-5 (a)); (c) if the first team does not score on its initial possession, or the score is tied after both, the next score by any method wins; (d) at most one 10-minute period, even when the second team has not had its opportunity or its initial possession has not ended; tied at its end, the game is a tie; (e) two timeouts each, excess timeouts as 4-5; the fourth quarter's general provisions, timing included, apply. SRC-OFFICIAL.
- 16-1-4 (postseason), periods of 15 minutes: (a) to (c) as in the regular season; (d) tied at the end of a period, or the second team's initial possession not ended, another period, as many as needed; (e) two minutes between periods, no halftime after the second; at the third period the captain who lost the toss has the first choice of 4-2-2 unless the toss winner deferred; (f) goals change at the end of the first and third periods (4-2-3); (g) three timeouts each "during a half"; (h) at the end of the second period timing as at the end of the first half, at the end of the fourth as at the end of the fourth quarter; (i) after the fourth period another coin toss and play goes on until a winner. SRC-OFFICIAL.
- 16-1-5 (both): (a) when the first team scored a field goal or touchdown and the second loses the ball by an interception or fumble, the down runs to its end and its points count; only fouls that require a replay of the down, fouls that negate a score, or palpably unfair acts are enforced; Notes 1 to 3 on a foul before the change of possession; (b) possession as 3-2-7 or 8-1-3; the defense gains it by a catch, an interception or a recovery; (c) the opportunity to possess applies only to kicking plays: a kickoff is the receivers' opportunity, even when the kickers legally recover it; a punt or field goal attempt that crosses the line and is muffed by the receivers is their opportunity; (d) the Replay Official starts every review, no coach's challenge; (e) a disqualified player does not return. SRC-OFFICIAL.
- 4-8-2 (c): a touchdown on the last play of a period is followed by its try, except during sudden-death overtime or when time in the fourth period ran out and a successful try could not change the result. SRC-OFFICIAL. The clone reads 16-1-3 (b) and (c) with it: the touchdown that decides an overtime is not followed by a try.
- Readings the clone makes where the text is silent (UNVERIFIED, decided in D-096): the third play-off period is received by the side that kicked off at the start of the last period that began with a toss (the clone's second-half rule, 16-1-4 (e) simplified: the toss loser's choice is taken as "receive"); after the fourth period the clone repeats the pattern (periods 5, 9, ... begin with a toss; 7, 11, ... like the third); a period that ends while an initial possession is still going on keeps the ball (16-1-4 (d)), also at the third period; the regular season's period, like the fourth quarter (16-1-3 (e)), has its two-minute warning (Part 2, SRC-SECONDARY practice).

The league's overtime numbers (for the measurement of SX.12; SRC-SECONDARY):
- Games that went to overtime: 665 of 12,379 regular-season games from 1974 to 2025, 5.39 percent; 16 of 272 in 2024; 14 in 2025; 21 in 2021. Ties: 30 since 1974, 0.25 percent of games (about 4.5 percent of overtime games); none in 2024, one in 2025 (Packers 40, Cowboys 40, the first under the rule that both teams possess). thesportsgeek.com, "What Percentage of NFL Games Go to Overtime or Are Tied?", fetched 2026-10-21 (its "one out of 412" contradicts its own counts and is not used).
- The overtime coin toss in the format in which both teams possess (the play-offs since March 2022, the regular season since 2025): its winners chose to kick in 14 of 20 games, and the team that received first went 11-8-1 (57.5 percent); since the start of the 2025 regular season toss winners were 6-12-1. Yahoo Sports, "To kick or receive? NFL coaches still haven't figured out the overtime coin toss", 2026-09-25. Small samples.
- Timeouts in a regular-season overtime: 22 of 60 teams used none, 26 one, 12 two (Part 9's play-by-play count, 2024 to 2026).
- The receiving team won 56.8 percent of overtime games in 2017 to 2024 under the old rule (AP, September 2025, as quoted by search; not fetched whole). Not used for a band.


## Part 11. The 2026 rules audit (SX.13)

The fresh review of everything the N. F. L. rules mode plays against the 2026 book is `spec\NFL_RULES_AUDIT_2026.md` (D-097): every difference with its rule number, what was fixed and what was decided. The book read there is the same PDF this file cites (SHA-256 144cec5b...87c55).
