# NFL_EXTRAS_DESIGN (nfl4 only): the design of the seven extra features

Status: DESIGN, version 1.0 (2026-10-14, session SX.1, D-041 and D-042). nfl4 only (CLAUDE.md rule 0.13): nothing in this file goes into the starter kit, `shared\`, `tools\`, a playbook or another game. It turns the requirements of `spec\NFL_EXTRA_FEATURES.md` (version 0.2) and the research of SX.0 (`spec\NFL_RULES_RESEARCH.md`, `spec\MADDEN_PLAYBOOK_RESEARCH.md`, `spec\MADDEN_FRANCHISE_RESEARCH.md`) into one design that the build sessions SX.2 to SX.9 follow. Every new spoken text is in `spec\STRINGS_NX.md` (generated from `spec\strings_nx.tsv` by `work\make_strings_nx.py`, D-017); every customizable pool is in `spec\CUSTOMIZABLE_CONTENT.md` section 13.

Who reads this: Claude at S7.3b to S7.7 (section 3, the hooks, which the classic engine builds before any extra exists) and at every PX session; the owner. Plain headings and lists, no tables. Rule citations are Rule-Section-Article of the 2026 rulebook as NFL_RULES_RESEARCH.md gives them; "Part n" means a part of that file.

Numbers marked "start value" are design values that a build session calibrates against the target named next to them, with the result recorded in DECISIONS.md. Numbers marked with a rule citation are the NFL's and do not move.

## 1. Owner decisions taken in this session (2026-10-14, D-041)

Asked once, one at a time, each with a recommended answer; the owner took all three recommendations.
- Overtime in N. F. L. rules mode: the original's sudden death stays in both modes (NQ4 confirmed). The 2026 NFL overtime (both teams get a possession, a regular-season tie) is not built; it stays on the list of optional companions (section 14). What N. F. L. rules mode takes from Rule 16 is only the period length, the timeout counts and "no coach's challenge in overtime" (section 4.6). SUPERSEDED 2026-10-21 by SX.12 (D-085 (3), D-096): the N. F. L. rules mode plays the whole of Rule 16 (`extras\overtime.py`: the overtime's coin toss, both teams possess unless the first drive ends in a safety, then the next score wins, one 10-minute regular-season period that can end tied, play-off periods of 15 minutes until a winner, the timeouts, no coach's challenge; ties in the standings, the season files and the Franchise); Classic keeps sudden death.
- The onside kick question: asked only when it makes sense (the player's team trails in the second half, or leads by one score late in the fourth quarter), with a setting "Onside question: always" that is off by default (section 8.2).
- Franchise before the first Windows release: the core only (a league that lasts, history, ratings, aging and retirement, the draft, the to-do list and the news). Contracts with the salary cap and free agency, trades, injuries, coordinators and the job rating come after the release as updates (NQ6 answered; section 11; the release gate in section 13). CHANGED BY THE OWNER ON 2026-10-16 (D-062): this split is withdrawn. The WHOLE Franchise, contracts, cap, free agency, trades, injuries, coordinators, job rating, goals and the LATER items, is in the first release, built by SX.8g to SX.8p before SX.9 (`NFL_EXTRA_FEATURES.md` N6.11 and section 14). Every "after the release", "as an update" or "version two" below in this file reads "in the first release, in the session named". Injuries exist only inside a Franchise, never in a quick game (INJ-1 to INJ-6 in N6.8).

## 2. Principles

- P1 Classic is untouched. With Rules = Classic the program does exactly what GAME_SPEC 1 to 15 and 17.2 say, consumes no extra random number and speaks no extra word. The golden Classic transcript of S7.3b and S7.3c is the proof and every PX session reruns it.
- P2 One engine, two rule sets. The extras live in a separate package `game\src\nfl4\extras\` that the classic engine calls only through the hooks of section 3. The engine never tests a feature flag in the middle of GAME_SPEC 5.7 to 5.12 (H6).
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
- Built in P7 S7.3b (2026-10-14, D-043): H1 (`game/periodclock.py`, ClassicPeriodClock, with one more call `warning_zone()`: the original turns its log flag on from L2cc - W on), H2 (`game/outcome.py`, the record at every narration end point listed there, through `Rules.after_outcome`; `Rules.before_snap`), H3 (`game/menus.py`), H4 (`Rules.before_kickoff`; a kind other than "normal" raises until SX.4), H5 (`game/gamestate.py`: GameState with `extras`, `snapshot`, `saved` and `load`), H6 (`game/rules.py`, ClassicRules), H7 (`Roster.ratings`), H8 (`game/playtables.py`, Modifiers and NEUTRAL), H9 (the speakers), H10, H11 and H13 (`Rules.between_plays`, `extra_stats_lines`, `extra_situation`). H12 waits for S7.4. Built in P7 S7.4a (2026-10-14, D-045): H12 (`Rules.extra_help(key)` with key "116", "117" or "118"; `game/hotkeys.py` speaks its lines with say5 after the original text of F5, F6 and F7 and before the menu's wait; ClassicRules returns nothing; the hot keys read `Game.rules`, the program's rules, which `play_game` uses when it is given none). All thirteen hooks exist; the golden Classic transcript is unchanged. The golden Classic transcript: `game/tests/data/golden_classic_s73b.txt` with `game/tests/test_pag_golden.py`. Added in PX SX.2 (2026-10-15, D-049), each a no-op in Classic and the golden transcript unchanged: H2 `Rules.after_tackle(state)` (after the tackle sentence of a play that ends in the field of play), H3 `Rules.menu_action(state, action)` with a `letter` per menu item (an action that is neither a play nor Save Game), H1 `before_snap()` returning True (the pending runoff ran the period out: the engine's new step `period_checks`) and `warning_given()`, H4's kind "period over" (no kick-off), and `Rules.for_game()` (one rules object per game). Added in PX SX.7 (2026-10-15, D-054), each a no-op in Classic: H3 `Rules.menu_back(state)` and a `(PLAY, n)` answer of `Rules.menu_action` (a play of a playbook was chosen), H2 `Rules.computer_defense(state)`, and H8 `rules.modifiers` is `PlaybookModifiers` in the N. F. L. rules mode.
- Designed in PX SX.8 (2026-10-15, D-055; `spec\NFL_FRANCHISE_DESIGN.md` section 13), to be built in SX.8a and SX.8b, each a no-op or an identity in Classic: H14 (new) the season hooks `Game.season_hooks` that the season engine reads (`computer_index` after each score index of a regular week's computer game, `playoff_first_wins` in place of the play-off coin, `game_played` after every result); H15 (new) the program's season frame as one mode object (`Program.mode`: which kind of season is in use and its stores, the season set-up, the new season, `before_menu` inside the main menu after today's game, `before_game`, the game's arguments, after the week, the season's end, the switch at the top of the week loop and `switch_pending` asked by the main menu after each key; `ClassicSeason` is today's code moved); H7 extended (`adopt_roster` keeps `ratings` and `quarterback`; `new_game_setup`, `Game.play_game` and `PlayEngine` take `opponent_names`); `GameRandom.chance_first(per_mille)` (one draw traced as size 2, equal to `rnd(2) == 1` at 500). No hook in the play engine: the ratings use H8. Built in PX SX.8a (2026-10-15, D-056): H15 (`Program.mode`, `game\season_mode.py`) and H14's `game_played`. Built in PX SX.8b (2026-10-16, D-057): H14's `computer_index` and `playoff_first_wins` (`ClassicSeasonHooks` are the identity and `rnd(2) == 1`; `computer_game(rnd, first_wins)` in `game\playoffs.py`), H7 extended (`adopt_roster` keeps `ratings` and `quarterback`, `adopt_opponent`, `new_game_setup(..., opponent_names)`, `Game.play_game` and `PlayEngine` take `opponent_names`), `GameRandom.chance_first`, H15's `game_arguments()` (Classic: `{}`; the Franchise: `opponent_names` and `quarterback_names`) and, in the playbooks' H8 object, `PlaybookModifiers.mod_for(kind)` and `bind(state)`, which `extras\franchise\ratings.py` `FranchiseModifiers` overrides.

## 4. The rules table `nfl_rules_2026`

One module, read-only data, a citation per value (all SRC-OFFICIAL from the 2026 rulebook unless marked). Grouped:

Clock and periods
- quarter_seconds 900 (4-1). halftime: not simulated (the original's half time presentation stays).
- warning_seconds 120; warning_periods 2 and 4 (3-41); the warning is an automatic timeout charged to nobody (3-41, 4-4(h)).
- ot_regular_period_seconds 600 (16-3); ot_post_period_seconds 900 (16-4). The game plays sudden death periods until a score (D-041); every new period repeats the same length. SX.12 (D-096): one regular-season period that may end tied; play-off periods until a winner, the ball kept from one period to the next (16-1-4).
- ot_warning: regular season at 2:00 of every overtime period; play-offs at 2:00 of overtime periods 2 and 4 (SRC-SECONDARY practice, Part 1.2 default).
- play_clock 40, after administrative stoppages 25 (4-6); used only to bound the runoff ranges of section 5.
- runoff_seconds 10, only after the two-minute warning of either half (4-7-1, 4-7-2, 4-7-4, 15-5-2).
- five_minute_rule: the last 300 seconds of the second half (4-3-2(a)(3), 4-3-2(e)(2)); overtime treated like it (Part 1.5 default).
- field_goal_max_clock 5 (11-4-2 Note 5). try_untimed true (4-3-2(h), 11-3-1).

Timeouts
- timeouts_per_half 3, no carry-over (4-5-1 Item 1).
- ot_regular_timeouts 2 per team; the game gives 2 again at every new sudden-death period (a game rule: the NFL has one regular-season period; SX.12, D-096: now one period, 16-1-3 (e)). ot_post_timeouts 3 per pair of overtime periods (16-4-g; periods 1 and 2 share three, 3 and 4 get three again, SRC-SECONDARY reading).
- one_charged_timeout_per_dead_ball true (4-5-1 Item 3). A request with no timeout left is ignored (4-5-1 Item 3); the game's menu refuses it with a sentence and never grants it, so the delay-of-game foul for a granted excess timeout and the unsportsmanlike foul of 4-5-1 Item 4 cannot arise (recorded, not simulated).
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
- fumbler_only_recovery: fourth down, after the warning, a try (8-7-5, 8-7-6). The game has no recovery by the offense (every fumble is lost, 5.9), so this rule never changes a result; recorded.

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

### 5.8 As built (PX SX.2, 2026-10-15, D-049)

- Code: `game\src\nfl4\extras\clock.py` (NflPeriodClock and the rules of time as functions), `timeouts.py`, `nfl_rules.py`, `state.py` (the ExtrasRecord in `GameState.extras`), `rules_2026.py`, `tuning.py` (the calibrated values with their history).
- Where the time is taken: L at the narration end point of every play (H2 `after_outcome`, scores and kick-offs too); R once per play in H10 (a second H10 call for the same play, the statistics' down sentence, draws nothing), kept pending; the pending runoff runs at the snap (H1 `before_snap`), and when it runs the period out the engine goes to a new step `period_checks` (the next-play step without counting a play; Classic never takes it). The warning: when L crosses 2:00 it follows the play; when R would cross it the clock stops at exactly 2:00; the engine tells the clock it was said (H1 `warning_given`, a no-op in Classic).
- A score as time runs out: in quarters 2 and 4 H4 returns "period over" and the half or the game ends after the try, with no kick-off; in quarters 1 and 3 the try and the kick-off come at 0:00 and the quarter ends after the return (the NFL kicks off at the start of the next quarter; the return's few seconds are not charged to it). This keeps the original's period flow; SX.9's playtest list names it.
- Out of bounds: a new hook (H2 `after_tackle`) after the tackle sentence and sound of a play that ends in the field of play and before the crowd fade and the gain sentence, so the sentence follows the tackle sentence as 5.2 says; no original draw lies between, so the new draws keep the order of section 15 (out of bounds, then L).
- 5.6 corrected: with "rounded up" (which gives the last-play rule above), "fewer than 7 plays left" means 228 seconds or less, not "fewer than 266" (that is the rounded-down reading). The formula stands.
- A hurry-up offense with at least 6 seconds left snaps with 1 second left when its runoff would run the period out; a timeout uses u = 3 to 8 seconds but never the period's last second.
- Calibration (`work\calibrate_clock_sx2.py`, the real engine with both sides played by the computer, `game\tests\nflrig.py`; 10,000 seeded games on the final code, `work\calibrate_clock_sx2_10000.txt`): 34.03 counted plays per regulation quarter (Q1 30.86, Q2 36.98, Q3 31.03, Q4 37.25), quarters 2 and 4 carry 6.17 more, 26.45 seconds per counted play, no period with a negative clock or two warnings, every period at 0. One move: the normal runoff 27 to 37 became 30 to 40 (the start values gave 25.07 seconds per counted play; 40 is the play clock).
- After the independent review (D-049 item 11): the two-point try is untimed at its snap too (a touchdown that used the last second is followed by its try, then the half or the game ends); nothing is granted at 0:00; the clock counts as stopped from every narration end point until H10 decides (F1 at the try's menu); F4 at 0:00 says " 0 seconds" with the original's words; a game saved in overtime keeps its overtime number through the record.

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
- The player calls a timeout with the T key anywhere in a game until the play is run (6.6, D-084, D-087) or from the offense or defense menu (the item "Time Out", reached by its number). With none left: " you have no time outs left. "; a second in the same dead-ball period: " you have already called a time out. ". Either refusal leaves the menu where it was.
- A granted timeout: foot11, " time out called by the <team>. ", " they have <n> time outs left. " (for the player: " you have <n> time outs left. "), a remark from pool TO with chance 1 in 3, the clock stops (only u of the pending runoff is used, section 5.3), the play menu is spoken again.
- The computer (N1.3; start rules, calibrated in SX.2 to 3.85 per team per game with the quarter split of section 4), checked in H10 after every play in this order, the first that applies decides:
  1. No timeout when it has none, or when it would leave none and a challenge is still possible for it (before the two-minute warning of the half, quarters 1 to 4), unless rule 3 or 4 applies.
  2. First half, after the warning: the side with the ball next calls one when the clock is running, the pending runoff is more than 10 seconds and it is in a drive (the ball on its own 30 or beyond); the defense calls one when the clock is running and the offense is inside its own 35 on third down or later (to get the ball back after a punt).
  3. Fourth quarter, the computer trails or is tied: on offense when the clock is running and the time left is under 2:00 (tied) or 5:00 (trailing); on defense when trailing and the time left is under 5:00 + 40 seconds for each timeout it holds, and the clock is running.
  4. Overtime: like rule 2 in the last 2:00 of the period.
  5. A leading computer team never calls a timeout in the fourth quarter.
  6. Operational timeouts (the NFL's quarter 1 and 3 timeouts): before a snap in quarters 1 and 3, chance 1 in 80 for a side with three timeouts (start value).
- Property tests: never more than the table's timeouts per half or overtime unit; never two in one dead-ball period; never a timeout while the ball is live.
- As built (PX SX.2, 2026-10-15, D-049): the menus end with " 8. Time Out " and " 9. Save Game " (offense) or " 7. Time Out " and " 8. Save Game " (defense); T and S make their item current like a digit and Enter takes it, so no single key calls a timeout; the two-point try keeps the original's items 1 to 5 (the try is untimed). The timeouts are said at the first kick-off of a half or overtime unit before the kick-off set-up (H4 is there). The whistle is foot11 through the original's PlayTackle(8); the announcer's sentences are logged like the warning. Rule 1's challenge clause is built in SX.6 (6.5). Calibrated (10,000 games): rule 2's runoff "more than 12" (start value 10), rule 3's defense 60 seconds per timeout held (40), rule 6 1 in 140 (1 in 80); 3.76 charged timeouts per team per game (target 3.85): quarters 1 and 3 0.20 each, quarter 2 1.78, quarter 4 1.57, overtime 0.015 (accepted as close to 0.2 and 1.7). The sentences have singular forms for one timeout and one second (STRINGS_NX NXT-11 to NXT-13, NXC-05), and a pair of play-off overtime periods is announced " for these two periods. " (NXT-14).

### 6.4 Challenges (NX2; built in SX.6)

- When: the play just finished has a challengeable ruling (any play of the categories of 6.1 that is not booth-only, section 4), it began before the two-minute warning of its half, it is not overtime, and the team has a challenge (2, a third after one success, never a fourth) and a timeout. Only then the next play menu (offense or defense, whichever the player has) offers the item "Challenge the Ruling" (before Time Out) and the letter C; it disappears at the snap. C when no challenge is possible speaks the reason (no challenge left, no time out left, after the two-minute warning, in overtime, the replay official reviews scoring plays and turnovers, nothing to challenge) and the menu goes on.
- The question (C9): " <coach> do you wish to challenge the ruling that <ruling>? ", " you have <n> challenges and <m> time outs left. a time out is lost if the ruling stands. ", answer " no " first; y, n, Up, Down, Enter, F1 as section 9.3's prompt.
- The review (N2.3): foot11, " the referee is going under the hood to look at the play. ", a pause of dy 2.0 and two rady (the NFL's review takes 1:25; no game time passes), then " after further review, the ruling on the field is reversed. " with the corrected result's short sentence, or " after further review, the ruling on the field stands. " (wrong but not clear) or " after further review, the ruling on the field is confirmed. " (right). Then " the <team> lose a time out. " when the ruling stands (and the challenge counts as lost). With chance 1 in 2 a remark follows: pool RVR after a reversal, pool RVC after a ruling that stands or is confirmed (RVC03 only after a lost challenge).
- A reversal restores the state snapshot of H5 (taken before the wrong result was applied, statistics included), applies the true outcome with the same apply step (5.11, 5.12: position, downs, gain sentence of the corrected result, score, banter by the original's rules), sets the clock to when the ball should have been dead (15-5-1) and, after the warning, applies the runoff of 15-5-2 when the corrected ruling would not have stopped the clock. A foul decision on that play is asked again (15-7-3, section 9.3). SX.13 (D-097, A-12): the 15-5-2 runoff is BUILT now (`ReviewFlow.runoff_due`, H10: ten seconds, the play clock 30, the half over under ten seconds; a timeout taken in that dead ball avoids it); until SX.13 the corrected play drew an ordinary runoff.
- The computer challenges (N2.5) when the ruling went against it, the play is challengeable, and: after a strong hint with chance 70 percent, after a close-call remark with chance 30 percent (start values; SX.6 calibrates to 0.24 to 0.28 per team per game and about 70 percent of challenges by the defense). Spoken: " the <team> have thrown the red flag. they are challenging the ruling that <ruling>. ", then the review.
- F2 (instant replay) is untouched (N2.6): it replays the last play's speech, never a review.

