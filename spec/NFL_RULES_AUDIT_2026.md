# NFL_RULES_AUDIT_2026 (nfl4 only, rule 0.13): the N. F. L. rules mode read against the 2026 Official Playing Rules

Version 1.0, PX Session SX.13, 2026-10-21 (NX-R7, D-085 (4), decision D-097). Fresh review: six reviewers that had not built the rules (one
per area: the clock and timeouts, penalties, replay, kicks, plays and the try, overtime and ties) read the book rule by rule against the
code; the session checked every finding in the book itself before acting. Every value below is tagged as in GAME_SPEC 5.3.

## 1. The source

- The 2026 Official Playing Rules of the National Football League, downloaded 2026-10-21 from the official page
  https://operations.nfl.com/the-rules/nfl-rulebook/ (link "ops-2026-NFL-Rulebook-FINAL", the PDF at
  https://static.www.nfl.com/image/upload/fl_attachment/league/tqivdkzt9mu6wdgsh1ku.pdf, 3,844,147 bytes, SHA-256
  144cec5bffd2725bb703a26523f5ccf0b16c59c2fe5c13f6e671f4bddaa87c55). Converted to text with pdftotext into `work\sx13\` (kept out of the
  repository); the layout text is byte for byte the text SX.12 read (`work\sx12\rulebook_2026.txt`), so the book has not changed since.
  Citations are Rule-Section-Article with the printed page. Tag: SRC-OFFICIAL for every rule statement below.
- The 2026 casebook could not be read (the page is rendered in the browser and no PDF was found): Q-038's readings stay readings where the
  book is silent.
- The reviewers' full reports: `work\sx13\findings_clock.md`, `findings_penalties.md`, `findings_replay.md`, `findings_kicks.md`,
  `findings_plays.md`, `findings_overtime.md` (with their probes in the folders beside them).

## 2. What was checked and found right

Each reviewer listed the rules of its area the game plays and named the test that proves each. These matched the book and were already
tested: the periods, the play clock bounds and the warning (3-41, 4-1, 4-4 (h), 4-6); the timeouts of a half and of overtime (4-5-1 Items
1 and 3, 16-1-3 (e), 16-1-4 (g)); the T key's live-play rule (3-36-2); the runoff of 4-7-1 Item 1 with its 30-second play clock; the
untimed down after a defense foul in the second and fourth quarters (4-8-2 (a)); every row of the foul table (yards, spot, first down, loss
of down: Rules 6, 8, 10, 11, 12 and the penalty summary, pages 70 to 72); half the distance (14-2-1); the spots of 14-3 and 14-4 for the
plays the game has; 15 against 5 without a change of possession (14-5-1 Exc. 1); the challenges' number, cost, timeout and booth limits
(15-1-1, 15-1-2, 15-6-1); the clock reset after a reversal (15-5-1); the declined flags offered again (15-7-3 Item 3); the kick-off from
the 35 with its 2026 touchbacks, landing zone and 40-yard line (6-1, 6-2); the onside kick declared at any time (6-1-6); punts, the fair
catch, kick catch interference (9, 10); field goals from any distance, the missed kick's spot and its 20 (11-4-2); the try from the 2 and
the 15, the defense's two points (11-3); the kneel and the spike (7-2-1 (c), 8-2-1 Item 3); the slide (7-2-1 (d)); the legal push sneak
(12-1-4 bans only pulling); grounding and its safety (8-2-1); the catalog's trick plays (one forward pass each, 8-1); Rule 16's
possession rule, its periods, ties and the absence of coach challenges; a tie as half a win and half a loss in every ranking (nfl.com
tie-breaking procedures, SRC-OFFICIAL).

## 3. Every difference, and what was done

Status: FIXED (code changed, test named), DECISION (recorded in D-097 with what would show it wrong), NOT-MODELED (the clone has no such
thing; nothing it plays contradicts the rule). Tests are in `clone\tests\test_sx13_rules_audit.py` unless named otherwise.

### 3.1 The clock and timeouts

- A-01 4-8-2 (c), p.15 (also 16-1-3 (e)). No try after a touchdown made on the down in which the fourth period's time expired when a good
  try cannot change the result; the game always played it. FIXED: `overtime.last_try_cannot_matter`, asked in H22 `points_end_game`
  after the six points (the regular season's overtime period too; a play-off period never ends a game by its clock; the first three
  quarters keep their try). Tests: `test_a_touchdown_as_the_fourth_quarter_runs_out_has_a_try_only_when_the_try_can_change_the_result`,
  `test_a_return_touchdown_as_time_runs_out_has_no_try_when_it_cannot_matter`, `test_a_last_second_touchdown_of_another_quarter_keeps_its_try`,
  `test_the_regular_seasons_overtime_period_has_the_fourth_quarters_rule`, `test_the_rule_reads_the_margin_after_the_six_points`;
  `test_nx_review.py` M1 moved to a tied score (its try matters).
- A-02 16-1-3 (e), 16-1-4 (h), p.65; 4-3-2 (a), (e). Overtime was one long late window (a runner out of bounds stopped the clock to the snap
  at any time, every foul started the clock on the snap). The book gives the regular season's period the fourth period's timing and times
  play-off period 2 as the end of a first half and period 4 as the end of the fourth period; 4-3-2 (e)(3) names only the regular season's
  overtime. FIXED: `clock.late_window` and `penalty_flow.late_for_fouls` read the period and the play-offs, `clock_after_foul`'s (3).
  Tests: `test_the_late_windows_of_overtime`, `test_an_offense_foul_before_the_snap_stops_the_clock_to_the_snap_only_in_the_regular_seasons_overtime`;
  `test_nx_clock.py` row (5, 599) moved to False.
- A-03 3-36-2, 4-5-1. A T key pressed during the live play was granted after H10 drew the runoff, so 3 to 8 seconds ran off before the
  timeout. FIXED: H10 grants the kept request before the runoff. Test: `test_a_t_kept_during_the_play_stops_the_clock_when_the_play_ends`.
- A-04 4-5-1 Item 3 with 3-8-1. The dead-ball period ended only at a scrimmage snap, so a timeout called before a kick-off, a punt, a
  field goal or a kicked try still counted at the next dead ball and a legal timeout was refused. FIXED: hook H18 `ball_live` at every snap
  and kick (Classic: nothing). Test: `test_a_snap_or_a_kick_ends_the_dead_ball_period`.
- A-05 4-5-1, 11-3-1. A timeout before a try at 0:00 was refused "no time" though the ball is dead and the try's down is still to come.
  FIXED: the try is due from the touchdown's six to the try's snap or kick (`NflRules.try_due`). Tests:
  `test_a_timeout_may_be_called_before_a_try_at_0_00_and_not_after_it`, `test_a_touchdown_makes_the_try_due_and_the_kick_ends_it`.
- A-06 4-8-2 (a) with 16-1-5 (f). The untimed down after an accepted defense foul was limited to quarters 2 and 4; the regular season's
  overtime period, which ends the game by its clock, never had it. FIXED: `PenaltyFlow.half_over`. Test:
  `test_an_accepted_defense_foul_extends_the_regular_seasons_overtime_period`.
- A-07 4-8-2 (h), p.15. A double foul on the last down of a half gave no untimed down. FIXED with the four exceptions:
  `PenaltyFlow.double_extends`. Test: `test_offsetting_fouls_on_the_last_down_of_a_half_give_an_untimed_down`.
- A-08 4-8-2 (e), 10-2-5 (a), p.41. The fair catch kick was never offered when the punt used the last second. FIXED: the question at 0:00,
  a yes gives the untimed down (the regular season's overtime too). Test: `test_a_fair_catch_as_time_runs_out_offers_the_untimed_fair_catch_kick`.
- A-09 4-3-1 (b), p.11. An onside kick the kicking team recovers started the clock (3 to 5 seconds). FIXED: no live time. Test:
  `test_an_onside_kick_the_kickers_keep_takes_no_time`.
- A-10 4-7-1 (a), p.14. "A foul by either team that stops the clock during any dead ball period" after the warning conserves time: delay of
  game was excluded from the 10-second runoff (a Part 1.5 default). FIXED: `rules_2026.NO_RUNOFF_FOULS` is empty. Test:
  `test_delay_of_game_after_the_warning_offers_the_ten_second_runoff`.
- A-11 4-7-1 Item 2, p.15. A defense foul that stops a running clock after the warning: the clock starts on the ready signal unless the
  offense chooses the snap; the game always stopped it to the snap. FIXED: the offense's choice by the score (ahead: the ready signal, to
  run the clock; level or behind: the snap), no question asked (the choice a coach makes; a recorded simplification of the asking).
  Test: `test_a_defense_foul_after_the_warning_lets_a_leading_offense_run_the_clock`.
- A-12 15-5-2 and 4-7-4, p.63 and p.15. After a reversal of a play that began after the two-minute warning, when the corrected result keeps
  the clock running, 10 seconds run off (under 10 seconds the half or the game ends), the play clock is 30 and both clocks start on the
  ready signal; a team may take a timeout to avoid it. The game drew an ordinary runoff. FIXED: `ReviewFlow.runoff_due`, H10 (NXP-12 is
  said). Tests: `test_a_reversal_after_the_warning_to_a_running_clock_runs_ten_seconds_off`,
  `test_a_timeout_avoids_the_ten_seconds_and_a_stopped_clock_has_none`. NFL_EXTRAS_DESIGN listed it as not built.
- A-13 15-6-2, p.63. A timeout taken after the warning is restored when a review changes the ruling. DECISION (D-097 item 6): the clone's
  booth reviews at the play's end point, before any timeout of that dead ball can be called; the one timeout that can come at that moment
  (the T key pressed during the play) is the timeout taken to avoid the 15-5-2 runoff, which the book charges (15-5-2 Note).
- A-14 4-7-1 Item 1. The offense's timeout in place of the 10-second runoff. DECISION (item 7): not offered at the runoff prompt (the
  player can call a timeout at the next prompt; the clock then stops after the runoff).
- A-15 4-7-1 (b). Intentional grounding after the warning with time in is also a runoff action. DECISION (item 8): not built (grounding
  is rare in the clone, drawn only in place of a sack; the 10 seconds would come on top of a stopped clock).
- A-16 4-7-3. The last 40 seconds with a defense foul that conserves time: the half may end. NOT-MODELED (no such choice is drawn).
- A-17 4-8-2 last paragraph, 4-2-3. A score as the first or third quarter ran out: the kick-off is played at 0:00 of the old period, so its
  return's seconds are not taken from the next quarter. DECISION (item 9): kept (rare; a few seconds).
- A-18 4-5-1 Item 4, 12-3-1 (v). A timeout requested to freeze a kicker beyond the limits is a foul. DECISION (item 10): the menu refuses
  every timeout the rules do not grant (rules_2026's note), so the foul cannot arise.
- A-19 Citations and tags (SRC-SECONDARY moved to SRC-OFFICIAL with the book's text): the overtime two-minute warnings (16-1-3 (e),
  16-1-4 (h), 15-3-9 (b), (c)); OT_POST_TIMEOUTS is 16-1-4 (g), not "16-4-g"; the try kick's spot is 11-3-1 (b).

### 3.2 Penalties

- A-20 14-5-2, p.58. Fouls by both teams on a kick-off return were enforced as 15 against 5, which gave the receivers the ball on their own
  0 (the wedge P34 against the kicking team's P24 or P35); a punt's kick catch interference against running into the kicker walked the
  punting team back to fourth and 23. A kick or a turnover changes possession: 14-5-1 does not apply, the fouls offset and the down is
  played again. FIXED: `penalties.double_foul`. Test: `test_double_fouls_with_a_change_of_possession_are_played_again`.
- A-21 14-4-8, 10-1-1. Kick catch interference on a punt the receivers ran back for a touchdown: the computer accepted the penalty and
  lost its touchdown (the play's facts carried no score). FIXED: the end point says "return touchdown" and a foul by the team that lost
  the ball is not offered. Test: `test_kick_catch_interference_never_takes_a_punt_return_touchdown_away`.
- A-22 14-3-6 Exception 2, 14-2-2 (b), p.55. A foul by the offense behind its own goal line on a run never gave the safety. FIXED. Test:
  `test_an_offense_foul_behind_its_own_goal_line_and_a_run_that_ends_there_are_safeties`.
- A-23 14-3-6 Exception 3. A run that ended in the offense's own end zone with an offense foul: accepting gave a new down; the book: a
  safety regardless. FIXED (no choice, the safety stands). Same test.
- A-24 14-3-6, 14-4-5. The ball carrier's face mask after a catch was enforced from the previous spot; after the catch it is a run's foul:
  three and one from the end of the run. FIXED. Test: `test_the_ball_carriers_face_mask_after_the_catch_is_enforced_three_and_one`.
- A-25 14-5-2 Item 1 and Exception (1). The receivers who fouled with "clean hands" after gaining the ball may keep it after their foul's
  enforcement, or replay. DECISION (item 11): every double foul with a change of possession is played again (the clone's fouls on these
  plays all come before or during the kick).
- A-26 14-2-3, 11-3-3 Item 4 (a), 14-4-9 Exc., 14-4-3 (b). Penalty yards that the book carries to the try or the next kick-off (a personal
  foul on a field goal or a safety, a defense foul on a good try, personal fouls after the end of a half, an offense personal foul before a
  turnover, a personal foul on a touchdown when the try is a kick). DECISION (item 12, D-050 kept): not carried (the clone's kick-off has
  one spot rule for the kick made again, and these fouls are rare).
- A-27 14-4-7. A foul by the kicking team on a kick-off: the receivers may also have the kick made again 5 yards back. DECISION (item 13):
  only the dead-ball spot's option is offered (with the 2026 kick-offs it is the receivers' better choice in practice); fouls_2026's P24
  note was out of date and is now this decision.
- A-28 14-1-3. Grounding and an at-snap foul by the same offense: the at-snap foul is dropped, so the defense has no choice between them.
  DECISION (item 14): rare; kept.
- A-29 14-4-3 (a). A foul before a fumble is enforced from the previous spot, not the spot of the fumble (the clone has no fumble spot).
  DECISION (item 15): kept.
- A-30 14-1-2 Item 4, 7-1-1 (b). An offense foul that leaves the ball exactly on the line to gain: the book is silent; the clone says
  "1 to go" (Part 1.5). DECISION (item 16): kept.
- A-31 11-3-3 Item 4 (c). The wording for a defense foul on a failed try. DECISION (item 17): kept (the try is tried again, as the
  research read it).
- A-32 Citations: P07 is 7-4-7 (the shift), P36 adds 12-3-1 (o), P37 is 14-4-8 Exc. (3); penalty_list's problem sentence names P01 to P37.

### 3.3 Replay

- A-33 15-1-1 (a), p.60. A coach may challenge the last play of the first or third quarter until the next snap; the game refuses (D-053).
  DECISION (item 18): kept (a reversal would have to reopen the period that ended, which the clone's quarter change cannot).
- A-34 15-1-2 last paragraph, 15-7-3 Item 1. A play with a foul after it enforced from the succeeding spot is never ruled, so it cannot be
  reviewed. DECISION (item 19): kept (rare).
- A-35 15-3-2 Item 1 Note 1. No advance after a catch that replay finds: the game gives the row's yards. DECISION (item 20): kept (the row
  models the catch as the receiver had it).
- A-36 15-1-2 (a): a play that runs across 2:00 stays a coach's play; 15-6-1: a timeout and then a lost challenge charge two timeouts.
  MATCH, now tested: `test_a_play_across_the_two_minutes_is_still_a_coachs` and `test_a_timeout_and_a_lost_challenge_cost_two_timeouts`.

### 3.4 Kicks

- A-37 6-1-2 (e), 6-1-4 (d)(3), 6-2-4, p.22 to 24. The landing zone is the receivers' 20 to their goal line wherever the kick is made from.
  A free kick from anywhere but the 35 (the safety kick from the 20, a kick made again from the 30) could be caught short of the landing
  zone and returned; a kick out of bounds or short gave the 40 always. The book: a foul, the receivers' ball 25 yards from the kick (30
  after a safety), or where it came down when that is nearer the kick. FIXED: `model.kickoff(..., safety)`, `model.short_kick_spot`,
  `ExtrasRecord.free_after_safety` (a safety kick made again is still one), sentences NXB-J25 and NXB-J26 with the spot. A kick from the
  35 draws exactly what it drew. Tests: `test_a_kick_off_from_the_35_draws_exactly_what_it_drew_before`,
  `test_the_receivers_ball_after_a_short_or_out_of_bounds_free_kick`,
  `test_a_free_kick_from_another_spot_is_never_returned_from_short_of_the_landing_zone`,
  `test_a_safety_kick_out_of_bounds_or_short_is_said_with_its_spot`.
- A-38 6-1-5 (d), 6-1-4 (e). The safety punt is a free kick: its touchback is the 35 (was a punt's 20); one that comes down short of the
  landing zone is the 6-2-4 foul; the punt model's "downed" is a ball at rest, the receivers' at the spot. FIXED:
  `KickFlow.safety_punt`. Tests: `test_the_safety_punt_is_read_as_the_free_kick_it_is`, `test_sx10d_kicks.py::test_the_safety_punt_ends_as_a_punt_and_its_touch_back_is_at_the_35`.
- A-39 9-3, 11-2, 11-5-1. A punt blocked behind the kicking team's own goal line stayed on the 1. FIXED: the receivers fall on it for a
  touchdown or it leaves the end zone for a safety (BLOCKED_PUNT_END_ZONE_TD 5000, UNVERIFIED: no published share), sentences NXB-J27 and
  NXB-J28. Tests: `test_a_punt_blocked_behind_the_own_goal_line_is_a_safety_or_the_receivers_touchdown`, `test_the_engine_tells_the_end_zone_block`.
- A-40 Strategy after the fix of A-37: the computer's safety kick is the deep kick (from the 20 a short or squib kick lands short almost
  always). Test: `test_after_a_safety_the_computer_kicks_deep_with_no_draw_and_a_safety_kick_made_again_stays_one`.
- A-41 The Classic playbook in the N. F. L. rules mode plays the original's kicks and plays (the kick-off touchback at the 20, the missed
  field goal at the line, an extra point that never fails, every fumble lost, turnovers at a drawn spot, no computer two-point try).
  DECISION (item 1; Q-036 as answered by D-095): the team's playbook is every new player's default and plays the 2026 book; the Classic
  playbook is the player's explicit choice of the original's plays inside the mode (as NX-P1 keeps Classic as a switch). The F6 help
  already says what the Classic playbook is.
- A-42 The fair catch kick is offered only to the player and only late in the second and fourth quarters (and now the regular season's
  overtime) in range. DECISION (item 2; D-094 (9) kept).
- A-43 NOT-MODELED: a free kick's recovery by the kicking team in the landing zone; a kick-off that lands in the zone and is downed in the
  end zone (the 20); the kick-off fair catch (LEFT_OUT); the onside kick out of bounds or untouched beyond 25 yards; a blocked punt run
  back; first touching; a missed field goal run back; the kicking team keeping a blocked field goal; fouls on the try kick.

### 3.5 Plays and the try

- A-44 7-2-1 (c), p.26. The ball is dead when the quarterback "simulates dropping to his knee": O155 "Fake Kneel" (pretend to kneel, then
  throw) is not a legal play. FIXED: O155 is "Victory Formation Pass" (the formation and an at-once pass, no kneel shown), its text rows
  NXY-A55 and NXY-S55 reworded, "fake kneel" listed in LEFT_OUT with the rule. Test: `test_no_play_simulates_a_kneel_and_the_clock_plays_keep_their_formation`.
- A-45 7-2-1, 11-2-1. The model drew a fumble after the gain reached the goal line, so a touchdown could become a fumble (kept: still a
  score; lost: a touchback). FIXED: no fumble draw once the runner or the receiver reached the goal line. Test:
  `test_no_fumble_is_drawn_once_the_ball_carrier_reached_the_goal_line`.
- A-46 8-7-1. A fumbled lateral on the Flea Flicker or the Double Pass was told and counted as a sack. FIXED: the laterals' run. Test:
  `test_a_fumbled_lateral_is_the_laterals_run_never_a_sack`.
- A-47 8-2-1 Item 3, 3-42; 8-1-6. The spike is legal only from under center; the Throwback's quarterback must be eligible. FIXED (no setting
  can make them illegal): the Formation setting never changes the kneel, the spike and the Throwback. Same test as A-44.
- A-48 8-2-1 Item 3. A spike with the clock stopped costs the down; the book names no foul. MATCH (P9 of the reviewer's probe).
- A-49 11-3-2 (c). A one-point safety on a try. NOT-MODELED (no play reaches that end zone).
- A-50 11-5-1 Exception 2 (momentum). NOT-MODELED (no return goes backward into its own end zone).

### 3.6 Overtime and ties

- A-51 16-1-4 (e), p.65. At the third play-off period the captain who lost the overtime toss has the first choice; the game gave the
  kick-off to the side that kicked the first period, asking nobody. FIXED: the toss's loser is recorded (`ot_toss_loser`, H22
  `overtime_toss_won`, saved), the player who lost it is asked receive or kick, the computer chooses with its toss share; a game saved
  before SX.13 keeps SX.12's reading. Tests: `test_the_player_who_lost_the_toss_chooses_to_receive_or_kick_at_the_third_period`,
  `test_the_computer_that_lost_the_toss_chooses_with_its_toss_share`, `test_the_overtime_toss_records_its_loser_and_the_save_keeps_it`;
  `test_sx12_overtime.py` moved.
- A-52 16-1-5 (c), 16-1-3 (b). The second team, behind, keeping its own punt after the first team muffed it: the punt ended its initial
  possession and the muff was the first team's opportunity, so the side ahead wins (Q-038's reading turned around). FIXED:
  `overtime.kickers_kept_punt`. Test: `test_sx12_overtime.py::test_a_muffed_punt_the_kickers_keep_was_the_receivers_chance`.
- A-53 16-1-4 (e) says "unless the team that won the coin toss deferred": the book assumes an overtime deferral. DECISION (item 3): no
  deferral (receive or kick), a simplification now recorded as one.
- A-54 16-1-4 (i). Periods 5, 9 and later begin with a new toss even while an initial possession goes on. DECISION (item 4): kept; the
  book is silent after the eighth period.
- A-55 16-1-5 (a) Note 2 and the remaining readings: MATCH (an accepted foul before the turnover keeps the second team's possession
  through the penalty flow); the overtime toss is called by the visitors (16-1-2): MATCH.

## 4. The gaps G26-1 to G26-14 (NFL_PLAYS_RESEARCH section 7)

With a playbook (every new player's default) the game follows the 2026 book in each; with the Classic playbook the original's kicks and
plays are the player's choice (A-41).

- G26-1 the kick-off: CLOSED (SX.10d; A-37 fixed the kicks not made from the 35).
- G26-2 the onside question: CLOSED (SX.2b, SX.10d).
- G26-3 overtime: CLOSED (SX.12; A-51, A-52 fixed).
- G26-4 the extra point: CLOSED (SX.10d).
- G26-5 punts: CLOSED (SX.10d; A-39 fixed the block behind the goal line).
- G26-6 field goal odds and the long try: CLOSED (SX.10d).
- G26-7 the missed field goal's spot: CLOSED (SX.10d).
- G26-8 turnovers returned: CLOSED (SX.10c).
- G26-9 fumbles either team may recover: CLOSED (SX.10c; A-45 fixed the fumble at the goal line).
- G26-10 two-point tries by either team: CLOSED (SX.10e).
- G26-11 the safety kick: CLOSED (SX.10d; A-37, A-38 fixed its spots and its touchback).
- G26-12 kneel and spike: CLOSED (SX.10c; A-44, A-47).
- G26-13 the fair catch kick: CLOSED (SX.10d; A-08 added the untimed down); the computer never tries one (DECISION item 2).
- G26-14 the fouls of the new kicks: CLOSED (SX.10d, rows P34 to P37); fair catch interference, an invalid fair catch signal and the
  block after a signal have no rows (DECISION item 21: their rates are unpublished and they change only a few kicks a season).

## 5. Open questions this audit settles or keeps

- Q-036: answered (D-095) and confirmed here as a recorded choice (A-41).
- Q-037 (fewer overtimes than the league): kept accepted-default; no rule of the book explains it (the regulation game's late margins).
- Q-038 (the readings where Rule 16 is silent): two readings settled by the book (A-51 the third period, A-52 the second team's kept
  punt), one recorded as a simplification (A-53), the rest kept (A-54); the casebook could not be read.
- Q-039 (the player's team and its peers in the Franchise): kept; no Franchise run in this session (P8's run).
- Q-030: the shapes of the computer's calling stay UNVERIFIED (no rule decides them).
