# NFL_EXTRAS_DESIGN (nfl4 only): the design of the seven extra features

Status: DESIGN, version 1.0 (2026-10-14, session SX.1, D-041 and D-042). nfl4 only (CLAUDE.md rule 0.13): nothing in this file goes into the starter kit, `shared\`, `tools\`, a playbook or another game. It turns the requirements of `spec\NFL_EXTRA_FEATURES.md` (version 0.2) and the research of SX.0 (`spec\NFL_RULES_RESEARCH.md`, `spec\MADDEN_PLAYBOOK_RESEARCH.md`, `spec\MADDEN_FRANCHISE_RESEARCH.md`) into one design that the build sessions SX.2 to SX.9 follow. Every new spoken text is in `spec\STRINGS_NX.md` (generated from `spec\strings_nx.tsv` by `work\make_strings_nx.py`, D-017); every customizable pool is in `spec\CUSTOMIZABLE_CONTENT.md` section 13.

Who reads this: Claude at S7.3b to S7.7 (section 3, the hooks, which the classic engine builds before any extra exists) and at every PX session; the owner. Plain headings and lists, no tables. Rule citations are Rule-Section-Article of the 2026 rulebook as NFL_RULES_RESEARCH.md gives them; "Part n" means a part of that file.

Numbers marked "start value" are design values that a build session calibrates against the target named next to them, with the result recorded in DECISIONS.md. Numbers marked with a rule citation are the NFL's and do not move.

## 1. Owner decisions taken in this session (2026-10-14, D-041)

Asked once, one at a time, each with a recommended answer; the owner took all three recommendations.
- Overtime in N. F. L. rules mode: the original's sudden death stays in both modes (NQ4 confirmed). The 2026 NFL overtime (both teams get a possession, a regular-season tie) is not built; it stays on the list of optional companions (section 14). What N. F. L. rules mode takes from Rule 16 is only the period length, the timeout counts and "no coach's challenge in overtime" (section 4.6).
- The onside kick question: asked only when it makes sense (the player's team trails in the second half, or leads by one score late in the fourth quarter), with a setting "Onside question: always" that is off by default (section 8.2).
- Franchise before the first Windows release: the core only (a league that lasts, history, ratings, aging and retirement, the draft, the to-do list and the news). Contracts with the salary cap and free agency, trades, injuries, coordinators and the job rating come after the release as updates (NQ6 answered; section 11; the release gate in section 13).

## 2. Principles

- P1 Classic is untouched. With Rules = Classic the program does exactly what GAME_SPEC 1 to 15 and 17.2 say, consumes no extra random number and speaks no extra word. The golden Classic transcript of S7.3b and S7.3c is the proof and every PX session reruns it.
- P2 One engine, two rule sets. The extras live in a separate package `clone\src\nfl4\extras\` that the classic engine calls only through the hooks of section 3. The engine never tests a feature flag in the middle of GAME_SPEC 5.7 to 5.12 (H6).
- P3 Rules are data. Every NFL number is in the table `nfl_rules_2026` (section 4), one module `extras\rules_2026.py`, each value with its citation in a comment. A later rule year is a new table, chosen by one setting value.
- P4 Calibration values are data too. Start values for clock, foul rates, ruling errors, keeper tables and the computer's thresholds are in `extras\tuning.py` with their target; a build session changes a value only with a recorded seeded simulation.
- P5 Audio first. Every new decision point speaks the question, the choices and the current answer; nothing happens on a timer without a spoken warning; the added speech per play is short (a flag or a timeout adds one to three sentences; most plays add nothing).
- P6 Small effects. Playbooks and (later) ratings move the original's numbers only within the bounds of section 10.3, so the game still feels like Jim Kitchen's.

## 3. Hooks for the classic engine (S7.3b to S7.7 build them; this refines NFL_EXTRA_FEATURES.md section 5)

The classic engine is built first and exact. Each hook below is a plain function, data list or record that Classic fills with the original's behavior. In Classic every hook is an identity or a no-op and costs no random number. S7.3b and S7.3c say in their Next Session block which hooks exist.

- H1 The period clock. One interface `PeriodClock` with: `plays_left()` (5.7 items a and c: "plays of the period minus the counter"), `played()` (the counter itself, 5.7 "the counter is past 20"), `is_last_play()`, `period_over()`, `warning_due()` (5.6 items 4 and 5), `speak()` (F4, 5.3), `after_play(outcome)` (advances the clock), `before_snap()` (applies a pending runoff, section 5.3). Classic answers every call from the play counter exactly as 5.3 and 5.6 (the counter, L2cc, M2W, M4W, M5W, CountDown, the Single chain). Every place in 5.6 and 5.7 that reads the counter reads it through this interface.
- H2 A play is five steps: (1) choose (the menus and 5.7), (2) `before_snap(play, defense)` (pre-snap fouls; Classic returns "go on"), (3) snap, resolve and narrate exactly as the original (5.8 to 5.10, with every draw, sentence, sound and pause in the original's order), which ends at the narration end point and yields one `PlayOutcome` record, (4) `after_outcome(outcome)` (live-ball fouls, the booth review; Classic returns the record unchanged), (5) apply (5.11 and 5.12). The narration end point, per kind of result, is: a run, pass or sack that ends in the field of play: after the gain or loss sentence of 5.11 item 3 and before the downs of item 4; a touchdown: after the run countdown or the catch sentence (5.11 item 2) and before " TOUCH DOWN"; a safety: after the tackle or sack sentence and foot5 and before " in the end zone for a safety"; an interception or a fumble: after its sentence and sound and before the possession sentence; a field goal: after its result sentence, foot12, the log flag and foot11 and before the points; a punt: after its last sentence (fair catch, out of bounds, downed, touch back) and before the possession sentence; a kick-off: after the touch back or return sentences and before the position sentence. `PlayOutcome` holds: offense play, defense play, kind (run, pass complete, pass incomplete, sack, interception, fumble, field goal good or missed, punt, kick-off return or touch back, two-point try), yards, the ball carrier slot and the two defender slots, turnover, score kind, the spot before the snap, and the ruling fields that only the extras fill (section 6.1). The speech, sound and pause events up to the end point are not replayed from the record: they have already happened in the original's order.
- H3 The play menus are data. One function builds the offense and the defense menu as a list of items (text, digit, letter or none, action). Classic is the exact lists of 4.15 with their keys (Save Game 8 and 7, the two-point try's items 1 to 5, no letter keys). The extras pass a different list (section 9).
- H4 The kick-off is one function `kick_off(kicking_side, kind)` with the decision point `before_kickoff(kicking_side, situation)` that returns the kind (Classic: always "normal", no question); the kind "onside" replaces the catch, return and touch back part (section 8). The safety's free kick goes through the same function with the spot "after a safety".
- H5 The game state is one record. It holds every value of 5.5 and an `extras` slot that is None in Classic. It can be copied (a snapshot taken before step 5 of H2, kept until the next snap, used by challenges, section 6.4). Save Game writes the original's values, then D-027's Variant, then the extras (section 12); loading reads them in that order.
- H6 One `Rules` object, passed through the engine; Classic is "all off". The engine calls hook functions; it never tests feature flags in 5.7 to 5.12.
- H7 Rosters stay slot-based (5.5): 6 running backs, 6 receivers, 17 defensive players, 2 special teams players, 2 kickers and the quarterback for each side, with an empty per-slot `rating` that Classic never reads.
- H8 The outcome tables are data. The 30 entries of 5.9 (yards minimum and maximum, sack percent, completion percent, the tackle sound) and the fumble chance, the interception rule and the field-goal and punt numbers of 5.10 are read through one `modifiers` argument that Classic passes as neutral (no change). Playbooks (section 10) and ratings (section 11) use it; the quarterback runs (section 7) add rows to the same table.
- H9 The speech and pause helpers (say to say6, dy, rady, the replay list, the log) are used as they are; the extras only add lines through them.
- H10 (new) Between plays. One call `between_plays(state)` after the down-and-distance sentence of 5.11 item 5 and before the next play menu (and after the possession sentence of a turnover): Classic does nothing. N. F. L. rules mode uses it for the two-minute warning and the period end of the real clock (section 5), booth reviews of the last two minutes (section 6), the computer's timeouts and challenges (sections 4 and 6) and the clock-running warning (section 5.5).
- H11 (new) Added statistics. The quarter statistics of 4.19 call `extra_stats_lines()` after " Points Scored"; Classic returns nothing (C7).
- H12 (new) Added help. F5, F6 and F7 call `extra_help(key)` after the original text; Classic returns nothing (C6).
- H13 (new) Situation speech. F1 in a play menu calls `extra_situation()` after the original's position and down sentences; Classic returns nothing (N. F. L. rules mode adds the clock state and the timeouts, section 5.6).
- Built in P7 S7.3b (2026-10-14, D-043): H1 (`game/periodclock.py`, ClassicPeriodClock, with one more call `warning_zone()`: the original turns its log flag on from L2cc - W on), H2 (`game/outcome.py`, the record at every narration end point listed there, through `Rules.after_outcome`; `Rules.before_snap`), H3 (`game/menus.py`), H4 (`Rules.before_kickoff`; a kind other than "normal" raises until SX.4), H5 (`game/gamestate.py`: GameState with `extras`, `snapshot`, `saved` and `load`), H6 (`game/rules.py`, ClassicRules), H7 (`Roster.ratings`), H8 (`game/playtables.py`, Modifiers and NEUTRAL), H9 (the speakers), H10, H11 and H13 (`Rules.between_plays`, `extra_stats_lines`, `extra_situation`). H12 waits for S7.4. The golden Classic transcript: `clone/tests/data/golden_classic_s73b.txt` with `clone/tests/test_pag_golden.py`.

## 4. The rules table `nfl_rules_2026`

One module, read-only data, a citation per value (all SRC-OFFICIAL from the 2026 rulebook unless marked). Grouped:

Clock and periods
- quarter_seconds 900 (4-1). halftime: not simulated (the original's half time presentation stays).
- warning_seconds 120; warning_periods 2 and 4 (3-41); the warning is an automatic timeout charged to nobody (3-41, 4-4(h)).
- ot_regular_period_seconds 600 (16-3); ot_post_period_seconds 900 (16-4). The clone plays sudden death periods until a score (D-041); every new period repeats the same length.
- ot_warning: regular season at 2:00 of every overtime period; play-offs at 2:00 of overtime periods 2 and 4 (SRC-SECONDARY practice, Part 1.2 default).
- play_clock 40, after administrative stoppages 25 (4-6); used only to bound the runoff ranges of section 5.
- runoff_seconds 10, only after the two-minute warning of either half (4-7-1, 4-7-2, 4-7-4, 15-5-2).
- five_minute_rule: the last 300 seconds of the second half (4-3-2(a)(3), 4-3-2(e)(2)); overtime treated like it (Part 1.5 default).
- field_goal_max_clock 5 (11-4-2 Note 5). try_untimed true (4-3-2(h), 11-3-1).

Timeouts
- timeouts_per_half 3, no carry-over (4-5-1 Item 1).
- ot_regular_timeouts 2 per team; the clone gives 2 again at every new sudden-death period (a clone rule: the NFL has one regular-season period). ot_post_timeouts 3 per pair of overtime periods (16-4-g; periods 1 and 2 share three, 3 and 4 get three again, SRC-SECONDARY reading).
- one_charged_timeout_per_dead_ball true (4-5-1 Item 3). A request with no timeout left is ignored (4-5-1 Item 3); the clone's menu refuses it with a sentence and never grants it, so the delay-of-game foul for a granted excess timeout and the unsportsmanlike foul of 4-5-1 Item 4 cannot arise (recorded, not simulated).
- timeout_restored_after_warning_reversal true (15-6-2).

Challenges and reviews
- challenges_per_game 2; third_after_successes 1; challenges_max 3 (15-1-1(f)).
- challenge_needs_timeout true (15-1-1(d)); failed_challenge_charges_timeout true (15-1-1(e), 15-6-1).
- no_challenge_for_plays_begun_after_warning true (15-1-2(a)); no_challenge_in_overtime true (15-1-2(b), 16-5-d); booth_only: scores, tries, turnovers (15-1-2).
- booth_initiates: scores, tries, interceptions, fumbles recovered by the opponent, fourth-down failures, every play after the two-minute warning, every overtime play (15-2); no timeout charged, no cap.
- standard_clear_and_obvious true (15-2-1). Not reviewable: judgment fouls, pass interference, intentional grounding, ineligible downfield, illegal contact (15-4). Penalty administration reviewable (15-7). After a reversal a head coach may change an accept or decline choice (15-7-3 Item 3).

Kicks
- kickoff_spot 35; safety_kick_spot 20 (6-1-2, 11-5-2).
- onside_any_time true, onside_must_be_declared true, onside_no_score_condition true (6-1-6, 2026).
- onside_min_distance 10 (6-1-6(e), 6-2-5); early touching by the kickers: 5 yards or the receivers' ball at the spot (6-2-5).
- The original's kick-off (5.10: the ball caught deep in the end zone, the run-out question, a touch back to the 20, returns of 12 to 101) stays in both modes. The 2026 kickoff (setup zone, touch back to the 35) is not one of the seven features; it is on the companion list (section 14, D-042 item 6).

Quarterback runs
- runner_is_qb_with_ball true (3-27); a loss behind the line on a designed run is a rush, not a sack (Guide for Statisticians p. 11, 14 to 15).
- slide_down_at_touch true (7-2-1(d)); late hit on a slider is unnecessary roughness, 15, automatic first down (12-2-8(d)).
- sneak_push_legal true (12-1-4; the 2025 ban vote failed 22 to 10).
- fumbler_only_recovery: fourth down, after the warning, a try (8-7-5, 8-7-6). The clone has no recovery by the offense (every fumble is lost, 5.9), so this rule never changes a result; recorded.

Penalties (enforcement rules; the fouls themselves are in section 9.2)
- half_distance true, exceptions: spot fouls (defensive pass interference), intentional grounding at the spot of the pass, palpably unfair acts, safety by enforcement (14-2-1, 8-5, 8-2-1).
- automatic_first_down_for_defense_fouls true, except: offside, encroachment, neutral zone infraction, delay of game, illegal substitution, excess timeout, running into the kicker, more than 11 in the formation, more than 11 at the snap, defensive illegal formation on a scrimmage kick (14-1-2 Item 5).
- one_penalty_per_team_per_down, chosen by the offended team (14-1-3); double fouls offset and the down is replayed (14-5-1); 15 against 5 without other effects: the 15 is enforced (14-5-1).
- spots: previous, succeeding, spot of the foul, dead ball, basic; runs use three-and-one (14-3-6); passes the previous spot except pass interference and personal fouls (14-4-5).
- score_rules: a defensive personal or unsportsmanlike foul on a touchdown is enforced on the try or the kick-off (14-2-3); an accepted offense foul erases a score.
- last_play_extension true: an accepted defensive foul on the last play of a half gives one untimed down (4-8-2(a)).
- clock_after_penalty: as if the foul had not happened, except on the snap after the first-half warning, in the last five minutes of the second half, for an offense foul in the fourth period or overtime, after a second delay (4-3-2(e)).

Statistics targets (SRC-SECONDARY, Part 1.6; used only by the calibration tests, never by play)
- accepted fouls per game 12.8, band 12.0 to 13.6; pre-snap share 37 to 40 percent.
- charged timeouts per team per game 3.85; quarters 1 and 3 about 0.2 each, 2 and 4 about 1.7 each.
- coach challenges per team per game 0.24 to 0.28, reversed 38 to 52 percent; booth reviews about 0.65 per game, reversed 74 to 78 percent.
- quarterback rushes per team per game 3.26 (1.29 designed, 1.97 scrambles); designed 3.66 yards, scrambles 7.67 yards; third or fourth and 1 designed quarterback run converted 83.4 percent.
- onside kicks recovered 6.0 to 9.6 percent (2024, 2025); attempts about 0.19 per game, all in the fourth quarter by the trailing team.
- seconds per scrimmage play 29.8; snaps per quarter including kicks about 33.5 (900 / 26.9).

## 5. The clock (C2, NX1 base; built in SX.2)

### 5.1 What a play costs

In N. F. L. rules mode every period has a clock in whole seconds. A play costs its live time L (the ball is live, the clock runs unless the clock is stopped at the snap and the play is a free kick) and, when the clock keeps running after the play, a runoff R until the next snap. Start values (seconds, uniform whole numbers, drawn with `rnd`):
- run or keeper, ended in bounds or out of bounds: L = 4 to 7.
- pass complete: L = 5 to 8. Pass incomplete: L = 3 to 7 (the NFL's incomplete snap-to-snap is 3, 5, 7 at the 10th, 50th, 90th percentile, Part 9 section 6).
- sack: L = 4 to 8. Scramble: L = 5 to 9.
- interception or fumble: L = 5 to 10.
- punt: L = 8 to 12. Field goal: L = 3 to 5 (never more than field_goal_max_clock). Extra point and two-point try: 0 (untimed).
- kick-off: a touch back costs 0 (the clock starts only when the ball is touched in the field of play, 4-3-1); a return costs 3 + (return yards \ 10) + 0 to 3; an onside kick 3 to 5.

### 5.2 Whether the clock keeps running

After the play (Part 2 section 4, list A to D):
- Keeps running: a run or a completed pass that ends in bounds, a sack, a keeper slide.
- Stops and restarts on the ready signal (the runoff is shortened, section 5.3): a run or completed pass out of bounds before the late windows; a penalty (accepted or declined) outside the cases of 4-3-2(e).
- Stops and restarts on the snap (no runoff): an incomplete pass; a score; a touch back; a change of possession (interception, fumble, turnover on downs, missed field goal, punt, kick-off); a timeout; the two-minute warning; an out-of-bounds play inside the late windows (the last 2:00 of the first half, the last 5:00 of the second half, all of overtime); a penalty inside the cases of 4-3-2(e); a challenge or booth review (the clock is then set as the corrected ruling says, 15-5-1).
- Out of bounds is a new draw (the original has no sidelines): after a run, keeper or completion that did not score, with the chance by kind: run 8 percent, completion 21 percent, keeper 12 percent, scramble 34 percent (start values from the 2024 to 2026 play-by-play data, Part 9). The sentence " and is pushed out of bounds " (NX-strings) follows the tackle sentence; the tackle sound stays.

### 5.3 The runoff and the tempo

R is drawn at the end of the play (step 5 of H2), from the tempo of the side that will snap next:
- normal: R = 27 to 37 (with L about 5.5 this gives a snap-to-snap mean near 37.5, NFL 37.9 to 38.4).
- hurry-up: R = 12 to 20. Used by the offense in the last 2:00 of the first half, by a trailing offense in the last 5:00 of the fourth quarter, by a tied offense in the last 2:00 of the fourth quarter, and in the last 2:00 of an overtime period.
- milk: R = 37 to 39 (the snap with 1 to 3 seconds on the play clock). Used by a leading offense in the last 8:00 of the fourth quarter.
- After a stop that restarts on the ready signal, R is shortened by 2 to 5 (the NFL's out-of-bounds plays take about 3 seconds less, Part 9).
The tempo is automatic for both sides (the player's offense too); the player stops the clock with a timeout. A hurry-up offense snaps before time runs out when at least 6 seconds are left (start value; with no spike play, section 14); otherwise the period ends.

R is not applied at once. It is kept as the pending runoff and applied at the next snap (H1 `before_snap`), so that the play menu (and the computer's decisions in H10) can stop it: a timeout called at the menu uses only u = 3 to 8 seconds of R (the time to signal the official; NFL data: a timeout after an in-bounds run comes a median 7 seconds later, Part 9). Two exceptions are applied at the end of the play: when the pending runoff would cross 2:00 of a warning period, the clock stops at exactly 2:00 and the warning follows (3-41: the warning comes at the end of the last down snapped before 2:00); when the live time L itself crosses 2:00, the warning follows the play at the time left.

### 5.4 Periods, warning and the end

- The period ends when the clock reaches 0. If it reaches 0 during the live time, the play is completed (4-8-1). If the pending runoff is larger than the time left and nobody stops the clock (no timeout, a hurry-up offense with fewer than 6 seconds), the period ends before the next snap.
- The original's sentences and sounds mark the events (the trigger changes, the speech does not): " Two Minute Warning" with foot11, " End of the First Quarter" and the others with foot11, the half time, " We are going into over time number", " THE GAME IS OVER".
- The warning is given once per warning period, through H10 (before the next play menu).
- An accepted defensive foul on the last play of a half gives one untimed down (section 9.4).

### 5.5 What the player hears and does

- F4 speaks the real time with the original's sentence builder (5.3: " <m> minutes <s> seconds remaining in the second quarter. "): the time left at the end of the last play.
- F1 in a play menu adds after the original's position and down sentences (H13): " the clock is running " or " the clock is stopped ", then the timeouts (section 6.3).
- Clock-running warning (C9): when the clock is running and the pending runoff is at least the time left, the next play menu first says " the clock is running with <n> seconds left. " so that a timeout can still be called.

### 5.6 What the computer reads through H1

- `plays_left()` in N. F. L. rules mode = time left divided by 38 (the mean snap-to-snap of a running clock), rounded up, at least 1. So 5.7's thresholds keep their meaning: "last play of the period" when the time left is at most 38 seconds and the clock is running or at most 8 seconds when it is stopped; "fewer than 7 plays left" when fewer than 266 seconds remain.
- `played()` stays the counter of plays in the period (5.7 "past 20").

### 5.7 Calibration (SX.2, done-when of NX1 with C2)

A seeded simulation of 10,000 quarters of each kind, both sides played by the computer: the mean number of counted plays (5.6 item 2: the same unit as the original) per regulation quarter is between 29 and 36 (C2); the second and fourth quarters carry 2 to 7 more than the first and third (NFL about 5); seconds per counted play 26 to 30; no period ever ends with a negative clock or two warnings. If a band is missed, the runoff ranges are moved by at most 4 seconds and the move is recorded.

## 6. NX1 timeouts and NX2 challenges and reviews

### 6.1 The ruling model (NX2; built in SX.6)

The engine knows the truth of every play. A ruling field in `PlayOutcome` says what the officials called, which is the truth except when a ruling error is drawn. After the narration end point, for the plays of a category below, one draw decides: correct and plain, correct but close, or wrong. Start values (per eligible play; SX.6 calibrates to the targets of section 4):
- catch: a completion called incomplete or an incompletion called complete: wrong 0.6 percent, close 1.0 percent of passes.
- down by contact: a fumble called "down before the fumble" or a tackle called a fumble: wrong 8 percent, close 8 percent of fumbles; wrong 0.2 percent of runs and catches.
- goal line: a run or catch that ends within 2 yards of the goal line, called on the wrong side: wrong 6 percent, close 8 percent.
- line to gain: a run or catch that ends within 1 yard of the line to gain, called on the wrong side: wrong 3 percent, close 6 percent.
- out of bounds: a catch called out of bounds (incomplete) when in, or the reverse: wrong 0.5 percent, close 1 percent of passes near the sideline (half the completions).
A wrong ruling means the narration already spoke the called result (the narration is built from the ruling, so the wrong call is what the player hears). Evidence: a wrong ruling is clear and obvious on replay with chance 85 percent (start value); a close correct ruling is never reversed.

The hint: after a wrong ruling the announcer says a strong hint remark (pool CH-S, section 13) with chance 70 percent, after a close one a close-call remark (pool CH-C) with chance 50 percent (start values). The computer reads the same hint (it has no other knowledge), so neither side gets more information than the other.

### 6.2 Booth reviews (N2.4)

At H2 step 4, before the result is applied: a scoring play, an interception, a fumble lost, a turnover on downs, any play after the two-minute warning and any overtime play is reviewed by the replay official when its ruling is wrong or close (15-2: the booth "may initiate"; it initiates when there is doubt). Spoken: foot11, " the replay official has stopped the game to review the play. ", then the review of 6.4. No timeout is charged. Calibrate to about 0.65 reviews per game, 74 to 78 percent reversed.

### 6.3 Timeouts (NX1; built in SX.2)

- State: timeouts left per side, reset at the start of each half and of each overtime period or pair (section 4); the count of timeouts already called in the current dead-ball period.
- Spoken at the start of each half and overtime period, after the kick-off set-up and before the kick: " each team has <n> time outs for this half. " (" for this period. " in overtime).
- F1 (H13): " you have <n> time outs left, and the <team> have <m>. ".
- The player calls a timeout from the offense or defense menu (item "Time Out", letter T) and at no other point. With none left: " you have no time outs left. "; a second in the same dead-ball period: " you have already called a time out. ". Either refusal leaves the menu where it was.
- A granted timeout: foot11, " time out called by the <team>. ", " they have <n> time outs left. " (for the player: " you have <n> time outs left. "), a remark from pool TO with chance 1 in 3, the clock stops (only u of the pending runoff is used, section 5.3), the play menu is spoken again.
- The computer (N1.3; start rules, calibrated in SX.2 to 3.85 per team per game with the quarter split of section 4), checked in H10 after every play in this order, the first that applies decides:
  1. No timeout when it has none, or when it would leave none and a challenge is still possible for it (before the two-minute warning of the half, quarters 1 to 4), unless rule 3 or 4 applies.
  2. First half, after the warning: the side with the ball next calls one when the clock is running, the pending runoff is more than 10 seconds and it is in a drive (the ball on its own 30 or beyond); the defense calls one when the clock is running and the offense is inside its own 35 on third down or later (to get the ball back after a punt).
  3. Fourth quarter, the computer trails or is tied: on offense when the clock is running and the time left is under 2:00 (tied) or 5:00 (trailing); on defense when trailing and the time left is under 5:00 + 40 seconds for each timeout it holds, and the clock is running.
  4. Overtime: like rule 2 in the last 2:00 of the period.
  5. A leading computer team never calls a timeout in the fourth quarter.
  6. Operational timeouts (the NFL's quarter 1 and 3 timeouts): before a snap in quarters 1 and 3, chance 1 in 80 for a side with three timeouts (start value).
- Property tests: never more than the table's timeouts per half or overtime unit; never two in one dead-ball period; never a timeout while the ball is live.

### 6.4 Challenges (NX2; built in SX.6)

- When: the play just finished has a challengeable ruling (any play of the categories of 6.1 that is not booth-only, section 4), it began before the two-minute warning of its half, it is not overtime, and the team has a challenge (2, a third after one success, never a fourth) and a timeout. Only then the next play menu (offense or defense, whichever the player has) offers the item "Challenge the Ruling" (before Time Out) and the letter C; it disappears at the snap. C when no challenge is possible speaks the reason (no challenge left, no time out left, after the two-minute warning, in overtime, the replay official reviews scoring plays and turnovers, nothing to challenge) and the menu goes on.
- The question (C9): " <coach> do you wish to challenge the ruling that <ruling>? ", " you have <n> challenges and <m> time outs left. a time out is lost if the ruling stands. ", answer " no " first; y, n, Up, Down, Enter, F1 as section 9.3's prompt.
- The review (N2.3): foot11, " the referee is going under the hood to look at the play. ", a pause of dy 2.0 and two rady (the NFL's review takes 1:25; no game time passes), then " after further review, the ruling on the field is reversed. " with the corrected result's short sentence, or " after further review, the ruling on the field stands. " (wrong but not clear) or " after further review, the ruling on the field is confirmed. " (right). Then " the <team> lose a time out. " when the ruling stands (and the challenge counts as lost). With chance 1 in 2 a remark follows: pool RVR after a reversal, pool RVC after a ruling that stands or is confirmed (RVC03 only after a lost challenge).
- A reversal restores the state snapshot of H5 (taken before the wrong result was applied, statistics included), applies the true outcome with the same apply step (5.11, 5.12: position, downs, gain sentence of the corrected result, score, banter by the original's rules), sets the clock to when the ball should have been dead (15-5-1) and, after the warning, applies the runoff of 15-5-2 when the corrected ruling would not have stopped the clock. A foul decision on that play is asked again (15-7-3, section 9.3).
- The computer challenges (N2.5) when the ruling went against it, the play is challengeable, and: after a strong hint with chance 70 percent, after a close-call remark with chance 30 percent (start values; SX.6 calibrates to 0.24 to 0.28 per team per game and about 70 percent of challenges by the defense). Spoken: " the <team> have thrown the red flag. they are challenging the ruling that <ruling>. ", then the review.
- F2 (instant replay) is untouched (N2.6): it replays the last play's speech, never a review.

## 7. NX3 quarterback runs (built in SX.5)

### 7.1 The plays

Three new offense plays with an outcome row against each of the six defense calls (H8 rows, start values to calibrate; yards are uniform whole numbers min to max as 5.9):
- Quarterback Sneak: Goal Line 0 to 2, Short Run 0 to 3, Long Run 1 to 4, Blitz -1 to 3, Short Pass 1 to 4, Long Pass 1 to 5; fumble 1 in 100; never out of bounds. Target: third or fourth and 1 converted about 80 to 85 percent against the computer's defense mix.
- Quarterback Keeper (bootleg): Goal Line -2 to 6, Short Run -3 to 5, Long Run -4 to 3, Blitz -3 to 15, Short Pass 3 to 12, Long Pass 4 to 14; fumble 1 in 90; out of bounds 12 percent.
- Quarterback Draw: Goal Line -1 to 3, Short Run -2 to 3, Long Run 1 to 6, Blitz 4 to 16, Short Pass 2 to 9, Long Pass 3 to 12; fumble 1 in 90; out of bounds 5 percent.
- Targets (section 4): designed quarterback runs about 3.7 yards mean over the computer's defense mix, first down or touchdown about half of the attempts.
- The scramble: on a Screen, Short or Long Pass, when the original's draws give a sack, one more draw turns it into a scramble with chance 15 percent; when the completion draw gives an incompletion (before the throw sentence), one more draw turns it into a scramble with chance 6 percent (start values; target: scrambles about 5.4 percent of drop-backs). A scramble replaces the sack or the throw, the interception test and the incompletion. Yards 1 to 14 (mean 7.5, NFL 7.67); fumble 1 in 200; out of bounds 34 percent.

### 7.2 The words (N3.4)

- A keeper is spoken in the 5.9 manner: the start sentence of its family (pool QB, never one of the last three used), the run sentence, the tackle sound and sentence, the gain sentence. The quarterback's name is used, never "He" or "She" (the clone does not guess a gender for a new sentence).
- A scramble keeps the drop-back sentence (5.9; "scrambles left looking for a receiver" fits), then " <quarterback> cannot find a receiver and takes off running ", then the tackle and gain sentences.
- A loss on a keeper is spoken as a run's loss and counted as rushing (section 4).

### 7.3 The slide (N3.2)

After a keeper or a scramble that gained 8 or more yards and did not score, with chance 1 in 2 the quarterback slides: the gain is cut by 0 to 2 yards, no fumble is possible, " <quarterback> slides feet first " follows the run sentence, and the clock keeps running (7-2-1(d)). A late hit on the slider is a foul of the table (section 9.2, P18) with chance 1 in 40 of slides when penalties are on.

### 7.4 The computer and the statistics

- Offense (with the Classic playbook; other playbooks weight the family themselves, section 10.4): on third or fourth down with 1 or 2 yards to go, a Quarterback Sneak with chance 1 in 2 in place of the drawn play (and on fourth down in place of "go for it"); on downs 1 to 3 otherwise, a Keeper or a Draw with chance 1 in 30 each.
- Defense: the matching of 5.7 extends: Quarterback Sneak with Goal Line, Quarterback Keeper with Long Run, Quarterback Draw with Short Run.
- Statistics (C7, N3.3): every keeper and scramble is a running play with its yards in the running yards, and is also counted on its own line (" Quarterback Runs ", " Quarterback Running Yardage "); a fumble is a fumble lost.

## 8. NX4 onside kicks (built in SX.4)

### 8.1 The rule

Under the 2026 rule 6-1-6 the kicking team may declare an onside kick at any free kick (kick-off or safety kick), in any period and with any score; the declaration is told to the receivers, so there is no surprise kick. The kick is from the kicking team's 35 (after a safety from its 20).

### 8.2 The player's question (owner decision D-041)

At H4's decision point, when the player's team kicks, in N. F. L. rules mode with onside kicks on, the question is asked when:
- the player's team trails in quarter 3 or 4, or
- quarter 4, at most 5:00 left, the player's team leads by 1 to 8 points,
- or the setting "Onside question: always" is on (then at every kick-off and safety kick).
The question: " <coach> do you wish to try an onside kick ", answer " no " first; y, n, Up, Down, Enter, F1 as section 9.3. Never asked in Classic, never in overtime unless "always".

### 8.3 The kick

- Spoken: " the <kicking team> line up for an onside kick. ", " the <receiving team> send in their hands team. ", " <kicker 1> bounces the ball along the ground. " with foot7 (-1200) and PlayNoise, " there is a scramble for the ball. ", then the result. A pause of rady before the result.
- Draws, in order: distance 8 to 14 yards; recovery by the kickers with chance 8 percent (start value: the declared kicks of 2024 to 2026 gave 8 of 113, 7.1 percent; 2018 to 2023 8.7 percent); with penalties on, a foul draw (section 9.2, P24 and P33) before the recovery draw.
- Recovered: " and the <kicking team> recover it. " and the kickers' first and 10 at the spot (their 35 + distance). Not recovered: " and <returner> falls on the ball. " (a special teams player of the receivers) and their first and 10 at the spot; with chance 1 in 25 of these a return instead: " <returner> picks it up and runs ", 5 to 44 yards, and with chance 1 in 100 of the failures a touchdown.
- Clock: 3 to 5 seconds (section 5.1). Statistics: onside kicks tried and recovered (C7).

### 8.4 The computer (N4.4)

A computer kicking team declares an onside kick (start values, calibrated to about 0.19 attempts per game, all in the fourth quarter by the trailing team, Part 1.6):
- quarter 4, trailing by 1 to 16, at most 2:00 left: chance 9 in 10;
- quarter 4, trailing by 9 or more, 2:00 to 5:00 left: chance 6 in 10;
- quarter 4, trailing by 17 or more, 5:00 to 10:00 left: chance 1 in 4;
- never otherwise (the 2024 to 2026 data have no attempt while leading or tied, so the "late lead" rule is the player's own choice only).
Spoken first: " the <kicking team> will try an onside kick. ".

## 9. NX7 penalties with accept or decline (built in SX.3)

### 9.1 When fouls happen

- Pre-snap, dead ball (false start, delay of game, neutral zone infraction, encroachment): drawn at H2 step 2 after both plays are chosen. When one occurs, the snap starts as 5.8 step 1 (the huddle and the quarterback's line), the quarterback says " hut 1 ", then foot11 and the announcement; no play is run (Part 6, 3.5).
- At the snap, live ball (offside, illegal formation, illegal shift, too many men on the field): drawn at the same point but the play is run and spoken; the flag is announced at H2 step 4 (a "free play" for the offense when the defense jumped).
- During the play (holding, pass interference, roughing, face mask and the rest): drawn at H2 step 4, after the narration end point, from the rows that fit the play kind.
- After the play (unnecessary roughness, unsportsmanlike conduct): at H2 step 4 too, enforced as dead-ball fouls from the succeeding spot.
- Draw order at step 4: one draw against the cumulative table of the fitting rows of both teams (a hit gives the foul and its team); then the offender's slot (a surname of that side's roster group the row names: linemen are the 17 defensive players for the defense, and for the offense the running backs and receivers, since the original names no offensive linemen); then, for a spot foul, its spot; then with chance 1 in 40 a second foul by the other team (offsetting, Part 1.6: about 0.3 offsetting pairs per game).

### 9.2 The foul table (data `extras\fouls_2026.py`, IDs permanent, spoken names in STRINGS_NX NXP-Fnn)

Each row: ID, code, spoken name, offender (offense, defense, kicking, receiving, either), phase (dead pre-snap, at snap, run, pass, after, field goal, punt, kick-off, return, onside), yards, spot (succeeding, previous, spot of the foul, dead ball, three-and-one), loss of down, the automatic first down exception flag (14-1-2 Item 5), personal-foul class, time-conserving class (4-7-1), and a start rate per 100 eligible plays (both teams, from the 2025 mix in Part 8 section 6, divided by about 121 scrimmage plays, 70 passes and 51 runs per game; SX.3 calibrates the sum to 12.8 per game, band 12.0 to 13.6):
- P01 false start (FST), offense, dead pre-snap, 5, succeeding spot, rate 2.0 per scrimmage play.
- P02 delay of game (DOG), offense, dead pre-snap, 5, succeeding, rate 0.55.
- P03 offside (DOF), defense, at snap, 5, previous, no automatic first down, rate 0.43.
- P04 neutral zone infraction (NZI), defense, dead pre-snap, 5, succeeding, no automatic first down, rate 0.23.
- P05 encroachment (ENC), defense, dead pre-snap, 5, succeeding, no automatic first down, rate 0.08.
- P06 illegal formation (ILF), offense, at snap, 5, previous, rate 0.33.
- P07 illegal shift (ISH), offense, at snap, 5, previous, rate 0.15.
- P08 holding (OH), offense, run and pass, 10, three-and-one on runs and previous spot on passes, rate 2.0.
- P09 holding (DH), defense, pass, 5, previous, automatic first down, rate 0.9 per pass.
- P10 illegal use of hands (ILH), defense, pass, 5, previous, automatic first down, rate 0.3 per pass.
- P11 illegal contact (ICT), defense, pass (not on a Screen), 5, previous, automatic first down, rate 0.5 per pass.
- P12 pass interference (DPI), defense, pass, spot of the foul (no half-distance limit; in the end zone: first down on the 1), automatic first down, rate 1.5 per pass, three times as likely on a Long Pass as on a Short Pass and none on a Screen.
- P13 offensive pass interference (OPI), offense, pass, 10, previous, rate 0.4 per pass.
- P14 roughing the passer (RPS), defense, pass, 15, previous or dead ball spot (the better for the offense), automatic first down, rate 0.5 per pass, doubled against a Blitz call.
- P15 intentional grounding (ING), offense, pass, loss of down and 10 from the previous spot or at the spot of the pass, safety in the end zone, not reviewable; drawn only in place of a sack (1 in 12 of sacks).
- P16 ineligible receiver down field (IDP), offense, pass, 5, previous, rate 0.2 per pass, three times as likely on a Screen.
- P17 face mask (FMM), either (defense 4 in 5), run, completion or sack, 15, dead ball spot, automatic first down if defense, rate 0.38.
- P18 unnecessary roughness (UNR), either (defense 3 in 4), after, 15, succeeding, automatic first down if defense, rate 0.54; also the late hit on a slider (section 7.3).
- P19 illegal block in the back (IBW), offense or receiving team, run and kick-off return, 10, three-and-one or spot of the foul on a return, rate 0.2 per run and 2.0 per kick-off return.
- P20 horse collar tackle (HC), defense, run, 15, dead ball spot, automatic first down, rate 0.15 per run.
- P21 unsportsmanlike conduct (UNS), either, after, 15, succeeding, automatic first down if defense, rate 0.17.
- P22 running into the kicker (RNK), defense, punt and field goal, 5, previous, no automatic first down, the kick is made again, rate 1.5 per kick.
- P23 roughing the kicker (RRK), defense, punt and field goal, 15, previous, automatic first down, rate 0.5 per kick.
- P24 offside on the kick off (OFK), kicking team, kick-off and onside kick, 5, the kick is made again, rate 1.0 per kick.
- P25 holding (on a return), receiving team, kick-off return, 10, spot of the foul, rate 2.0 per return.
- P26 too many men on the field (DTM), defense, at snap, 5, previous, no automatic first down, rate 0.12.
- P33 illegal touching of the kick, kicking team, onside kick, 5 or the receivers' ball at the spot, rate 4.0 per onside kick.
(IDs P27 to P32 are reserved for the suggested later rows of Part 7 section 0; a new row is one data line.)

### 9.3 The choice (N7.3, C9)

- Announcement: foot11, " there is a flag on the play. " (pre-snap: " the play is dead. " first), then " <foul name>, on the <team>, <surname>. " (the team as the announcer names it, the surname from the roster slot drawn).
- When the player's team is offended and has a real choice: " <coach> if you accept the penalty, <situation>. if you decline it, <situation>. " and the answer " accept " or " decline ", starting at the one the computer's own rule calls better (so Enter never hurts). <situation> is built from pieces in STRINGS_NX (NXP-S): " it will be <down> and <distance> on <my|your|the> <yard> yard line ", " the touch down stands ", " the touch down does not count ", " it will be my ball on ... ", " the half ends ", " there will be one more play ". Keys: a accept, d decline, Up, Down or Tab toggle and speak, Enter takes it, F1 repeats the announcement and the prompt, F2 to F4 as in a play menu then the prompt again, S saves the game with the decision pending (C10), any other key is echoed (saykey) and the prompt is spoken again with the current answer. After the two-minute warning, an offense foul that stops a running clock offers three answers: " accept with the ten second run off ", " accept the yards only ", " decline " (4-7-1).
- No prompt when there is no choice: double fouls (offset, the down is replayed, " there are flags on both teams. the penalties offset. replay the down. "), a dead-ball foul whose decline would only replay the same down (accepted automatically, as officials do), a non-player conduct foul.
- The computer decides by comparing the two outcomes in this order (Part 6 section 8): points or a turnover; a first down; field position (yards from its own goal); down and distance; clock and score late in the half. It accepts when the penalty erases an opponent's score or turnover. Spoken: " the <team> accept the penalty. " or " the <team> decline the penalty. ". Plausibility check over a season (SX.3): about 12 to 13 percent of choices declined (Part 8 section 6).
- Then the enforcement (9.4) and the position and down sentences of 5.11 item 5 (the original's builder), with " automatic first down. ", " loss of down. ", " half the distance to the goal. " where they apply.

### 9.4 Enforcement (N7.4; the full rule list is NFL_RULES_RESEARCH.md Part 6; SX.3 builds every case with a test)

- Spots: dead pre-snap fouls from the succeeding spot, down unchanged; at-snap fouls from the previous spot; runs by three-and-one (14-3-6); passes from the previous spot except pass interference (spot of the foul) and personal fouls (previous or dead ball spot, the better for the offended team); after-play fouls from the succeeding spot.
- Half the distance (14-2-1) with its exceptions (section 4); spots rounded to whole yards (the clone has no fractions), at least one yard when the distance is under two (Part 1.5 default).
- Downs: offense fouls replay the down unless loss of down; defense fouls give first and 10 except the ten fouls of 14-1-2 Item 5; any enforcement that reaches the line to gain is first and 10.
- Scores: an accepted offense foul erases a score; a defense personal foul on a touchdown play is enforced on the try or the kick-off (14-2-3); a foul by the offense in its own end zone gives a safety; a defense foul on an unsuccessful try replays the try.
- Turnovers: an accepted foul by the team that gained the ball erases the turnover (previous spot); an accepted earlier foul by the team that lost the ball keeps the turnover (the rare personal-foul exception of 14-4-3 included).
- Kicks: the kick is made again (running into the kicker on a punt or field goal, offside on a kick-off), or the yards are added at the dead ball spot (return fouls).
- Last play of a half: an accepted defensive foul gives an untimed down (4-8-2(a)).
- Clock after the penalty: section 4 and 5.2; the 10-second runoff after the warning (4-7).
- Interactions (N7.6): a timeout request without timeouts never becomes a foul (section 4); a challenge or booth review never changes a judgment foul, but a reversal can change the enforcement (15-7) and lets the player choose again (6.4); the late hit on a slider (7.3); fouls on onside kicks (8.3).

## 10. NX5 playbooks (built in SX.7)

### 10.1 The set

Classic (the original's plays and numbers, always first, the default) and seven style playbooks from MADDEN_PLAYBOOK_RESEARCH.md section 4: Pro Style, West Coast, Air Raid, Power Run, Zone Run, Option, Pressure (NQ5 answered: the research found no published list of the 32 team books, so styles plus an assignment). The player chooses the offense playbook and the defense playbook separately (EA does the same), both defaulting to the team's style; the 32 teams are assigned as research section 5 says (data, `customize\playbooks\team_styles.txt`; the weak assignments Browns, Panthers, Lions and Redskins stay as proposed).

### 10.2 The plays

- One shared catalog of about 50 offense plays and 30 defense plays with permanent IDs (O001..., D001...), each mapped to a family of the original (offense: Line Plunge, End Run, Screen Pass, Short Pass, Long Pass, and the quarterback runs of section 7; defense: the six calls) and spoken in at most six words. Names come only from the plain football words of research section 3 List A (NX-R6); SX.7 writes the catalog as data and STRINGS_NX gets their spoken names then.
- Each style lists about 30 offense and 18 defense plays from the catalog, with the computer's weights by situation and the modifiers.

### 10.3 The modifiers (H8) and the balance rule

- A play's modifier changes its family's row only: yards minimum and maximum each by at most 2, sack percent and completion percent each by at most 5 points, the fumble denominator by at most 1 point of chance (1 in 50 becomes at most 1 in 45 or 1 in 55). A style has at most three bonus entries and three penalty entries of equal total size (research section 4); Pro Style is equal to Classic in numbers (the control group).
- Balance test (SX.7, NX5 done-when): over 10,000 seeded computer-against-computer games, every style against Classic wins between 45 and 55 percent; no single play is better than the best play of its family against every defense call.

### 10.4 Menus (N5.5) and the computer (N5.6)

- Classic playbook in N. F. L. rules mode: the original's items 1 to 7, then the quarterback runs when they are on (8 Quarterback Sneak, 9 Quarterback Keeper, 0 Quarterback Draw), then Challenge the Ruling (C, only when allowed), Time Out (T, when timeouts are on), Save Game (S) last. The defense menu: the six calls, then Challenge the Ruling, Time Out, Save Game. At most 12 items; digits 1 to 9 and 0 for item 10; letters for the rest.
- A style playbook: a top menu of groups (Inside Runs, Outside Runs, Screens, Short Passes, Deep Passes, Play Action, Quarterback Runs when on, Field Goal, Punt) followed by Challenge the Ruling, Time Out and Save Game; Enter on a group opens its 3 to 6 plays; Backspace or Left goes back to the groups; Esc is still quit and concede (4.18). The defense: the six calls as groups, each with 2 to 5 plays.
- The computer: a weighted draw over the style's plays by down, distance, field position and score in the structure of 5.7 (the Classic playbook's weights are 5.7 itself; fourth-down and last-play rules of 5.7 stay above the draw).

## 11. NX6 Franchise (core before the release, D-041; SX.8 designs the detail)

### 11.1 Scope

- Before the Windows release (the core, NQ6 answered): F0 the league that lasts and the season loop, F4 history, F1 ratings with bounded effect, F2 progression, regression and retirement, F3 the draft, F5 the to-do list and the news (MADDEN_FRANCHISE_RESEARCH.md section D, items 1 to 6; N6.1 to N6.5, N6.9, N6.10).
- After the release, as updates in this order: F6 contracts, salary cap, re-signing and free agency (N6.6); F7 trades (N6.7); F8 injuries; F9 coordinators, the job rating and the owner goal (N6.8); then the LATER items of the research (personality, holdouts, morale, undrafted free agents, compensatory picks, awards).

### 11.2 Mode and flow

- Chosen when a new season starts and Rules is N. F. L. rules: " <coach> which kind of season do you wish to play ", answers " classic season " (first) and " franchise ". With Rules = Classic the question is not asked (P1). A Franchise season always plays with N. F. L. rules (the feature switches still apply); the F9 Rules item then says " the franchise uses the N. F. L. rules. ".
- The season itself is the original's: 16 weeks, the schedule maker, the season engine and the play-offs (5.1, 5.14 to 5.17) with their sentences; Franchise adds the offseason after the play-offs and the to-do list and news before each game.
- Ratings change only bounded modifiers (H8) and the shape of the computer games' score table (5.14), with neutral ratings equal to Classic (C3).

### 11.3 Data decided now (SX.8 may refine with a recorded reason)

- Rating scale 40 to 99, neutral 70; potential in 3 levels; age 21 to 40.
- Position labels of the 17 defensive slots (the original names none): 1 to 6 defensive line, 7 to 11 linebackers, 12 to 15 cornerbacks, 16 and 17 safeties. Offense: the 6 running backs, 6 receivers, the quarterback, 2 kickers (kicker and punter) and 2 returners as the original's slots.
- Files: one folder `franchise` in the data folder with `league.sav` (the whole league, written whole each time with a backup copy `league.previous.sav`, format version first, healed as 7.10) and `history.txt` (plain text the player can read in Notepad).

### 11.4 Sessions

SX.8 (design), then SX.8a F0 and F4, SX.8b F1, SX.8c F2, SX.8d F3 (may take two), SX.8e F5, SX.8f the core's 20-season simulation (research section G invariants for the core: no player under 30 retires, every slot filled after every offseason, no rating outside 40 to 99, neutral ratings reproduce Classic, computer picks in one code path). After the release: SX.8g to SX.8i F6, SX.8j F7, SX.8k F8, SX.8l F9 (with the full 20-season test of research section G).

## 12. Settings, save format and files

### 12.1 Settings (settings.txt, C1)

New keys with their defaults: rules = classic (NQ2: becomes "nfl" for a new player only after SX.9 passes); nx_timeouts = on; nx_challenges = on; nx_qb_runs = on; nx_onside = on; nx_onside_question = sensible (or always); nx_penalties = on; nx_offense_playbook = team; nx_defense_playbook = team (or classic or a style name); nx_rules_year = 2026. A change of Rules or of a switch applies from the next game: " the new rules apply from the next game. ".

### 12.2 The F9 menu (NQ7 answered)

F9 (17.4: speech settings, sounds, customize, about) gets "Rules" before "About". Its items, in order: 1 Rules: Classic or N. F. L. rules; 2 Time outs; 3 Replay challenges; 4 Quarterback runs; 5 Onside kicks; 6 Onside question; 7 Penalties; 8 Offense playbook; 9 Defense playbook; 10 Reset the rules to the defaults. Up and Down move, Enter or Space changes the current item and speaks the new value, the digits 1 to 9 and 0 jump, Escape leaves. Items 2 to 9 say " used with the N. F. L. rules " after their value when Rules is Classic.

### 12.3 football.sav (C1, C10, H5)

After the original's 36 values and the opponent quarterback's name, and after D-027's Variant (the side that received the opening kick-off), a game played with N. F. L. rules writes three more Variants: the string "NX-EXTRAS", the Integer 1 (the format), and one string holding the extras record (UTF-8 JSON: the clock, the timeouts, the challenges, the ruling and snapshot of the last play, the pending decision if any, the extras' statistics, the playbooks, the rules year). The original never reads past its own values, so the file stays readable by it. Loading:
- no marker: a Classic save; in N. F. L. rules mode it loads with the extras at their start values (full timeouts, the clock at the start of the current quarter's play counter as 15:00 minus 28 seconds per counted play, at least 1:00).
- a marker with Rules = Classic: asked once, " this saved game was played with the N. F. L. rules. do you wish to play it with those rules? " answer " yes " first; yes plays this game with N. F. L. rules (the setting is unchanged); no plays it as Classic and drops the extras.
- a pending decision (accept or decline, challenge, onside question) is asked again first.
- a damaged extras string: the extras start values with one spoken notice (C10, 7.10); the original's values still load.

### 12.4 Customize folder (CUSTOMIZABLE_CONTENT section 13)

`penalties.txt`, `remarks.txt`, the folder `playbooks` (catalog, styles, team styles) and, with Franchise, `news.txt`.

## 13. Build order, sessions and the release gate

- S7.3b, S7.3c, S7.4, S7.5, S7.7 (the classic line, in progress): the hooks of section 3 and the golden Classic transcript. Unchanged by this design except that they read section 3 here.
- SX.2 the clock (section 5), timeouts (6.3), F1 and F4 in N. F. L. rules mode, the Rules setting and the F9 Rules menu, the extras save section. Sonnet 5.5 at high; Opus 5.5 for the calibration.
- SX.3 penalties (section 9). Opus 5.5 at high (many interlocking enforcement cases).
- SX.4 onside kicks (section 8). Sonnet 5.5 at high.
- SX.5 quarterback runs and the scramble (section 7). Sonnet 5.5 at high.
- SX.6 ruling model, booth reviews and challenges (6.1, 6.2, 6.4). Sonnet 5.5 at high; Opus 5.5 if the snapshot rollback interacts badly with penalties.
- SX.7 playbooks (section 10), may be split: format and three styles, then the rest and the balance test. Sonnet 5.5 at high.
- SX.8 Franchise design, then SX.8a to SX.8f the core (section 11.4). Opus 5.5 at high for the design, Sonnet 5.5 at high for the building.
- SX.9 integration: the switch combinations that matter, the long simulations, the 8.3 stress tests with the extras, the owner's playtest list (what only ears can judge), README and About (NX-R6 notice), NQ2's default flips to N. F. L. rules. Opus 5.5 or Sonnet 5.5 at high.
- Release gate (NX-R3 as changed by D-041): P9 starts when SX.2 to SX.7, SX.8 to SX.8f and SX.9 pass. The later Franchise blocks (SX.8g on) come after the release as updates, each with its own tag and release.
- Estimate: SX.2 to SX.9 with the Franchise core about 16 to 20 sessions; the later Franchise blocks about 8 to 10.

## 14. Optional companions (not requested; asked once when this design is accepted, NFL_EXTRA_FEATURES.md section 13)

- Spike and kneel-down plays (they make the real clock fully playable: a spike stops the clock in about 3 seconds; a kneel-down runs it).
- A manual tempo choice for the player's offense (hurry-up or slow down) in place of the automatic tempo of 5.3.
- The 2026 NFL overtime (both teams get a possession; the regular-season tie).
- The 2026 kickoff (setup zone, touch back to the 35) and a missable extra point from the 15.
- Injuries outside Franchise; a "two-minute drill" help text.

## 15. Every new random draw (C4)

All draws use the one `GameRandom` (`rnd(n)` = Int(Rnd * n) + 1, `below(n)`) and its bounded redraw (G-D1). In Classic none of them happens. In N. F. L. rules mode, inside one play they come in this order (a feature that is off skips its draws):
1. H2 step 2: the pre-snap foul draw (one `below(10000)` against the cumulative per-10,000 rates of the dead and at-snap rows that fit the play), then for a hit the offender's slot.
2. H2 step 3: the original's draws of 5.8 to 5.10 in their order, with the inserted draws of section 7.1 (the scramble test right after the original's sack test or completion draw) and, for the quarterback runs, the row's yards and fumble draws in the order of a 5.9 run (sentence draws first, then the fumble, then the yards).
3. After the narration end point (H2 step 4), in this order: out of bounds (5.2); the slide (7.3); the ruling category draw (6.1, one `below(1000)`); the hint remark draw; the live foul draw (`below(10000)`), the offender's slot, the spot, the offsetting draw; the computer's accept or decline needs no draw.
4. H1 after the play: the live time L, then the runoff R (5.1, 5.3).
5. H10 between plays: the computer's operational timeout draw (6.3 rule 6), the computer's challenge draw (6.4), the remark draws (pool, never one of the last three).
6. H4 kick-offs: the onside question needs no draw; the computer's onside choice (8.4), then the onside kick's distance, the foul draw, the recovery, the return.
Each build session documents its draws again in its tests with the strict scripted source, and adds a test that a Classic game draws exactly the golden sequence.

## 16. History

- 1.0 (2026-10-14, SX.1): written from NFL_EXTRA_FEATURES.md 0.1 and the SX.0 research; the owner's three decisions (D-041); the design decisions (D-042).
- 1.0, note of S7.3b (2026-10-14, D-043): section 3 says which hooks were built and where; no design changed.
