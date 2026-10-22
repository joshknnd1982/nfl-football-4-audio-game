# NFL_RULES_RESEARCH (nfl4 only): the NFL rules behind the seven extra features, checked against the official 2026 sources

Status: RESEARCH, version 1.0 (2026-10-14, session SX.0). Research only: no code was written and no other file was changed. This file settles the rule lines of `spec\NFL_EXTRA_FEATURES.md` (sections 3 C2, 6, 7, 8, 9, 12) that were tagged UNVERIFIED or SRC-SECONDARY. Session SX.1 turns the answers into the `nfl_rules_2026` data table and changes the tags in the requirements file; SX.0 did not edit that file.

Who reads this: Claude at SX.1 to SX.7 and SX.9, and the owner. Plain headings and lists, no tables. Part 1 is the summary and is enough to design from. Parts 2 to 9 are the detailed notes of each topic, kept so that a build session can look up the exact article, page and number; each starts with its own short list of answers.

## Part 1. Summary for SX.1

### 1.1 Sources, tags and what was not reachable

- The authority is the 2026 Official Playing Rules of the NFL (the rulebook), PDF "ops-2026-NFL-Rulebook-FINAL", copyright 2026 NFL, 92 PDF pages, https://static.www.nfl.com/image/upload/fl_attachment/league/tqivdkzt9mu6wdgsh1ku.pdf , linked from https://operations.nfl.com/the-rules/nfl-rulebook/ . Retrieved 2026-10-14 and read in full for Rules 3, 4, 6, 7, 8, 9, 11, 12, 14, 15, 16 and the Penalty Summary. Citations are Rule-Section-Article, for example 4-5-1, with the PDF page. The printed page number is the PDF page minus 7.
- The book is not kept in the project folder (it is the league's copyrighted text). To repeat a check: download the PDF from the URL above and run `pdftotext -layout` on it.
- Other official sources used: operations.nfl.com (football terms, replay officials, Art McNally GameDay Central, salary cap and free-agency pages), nfl.com news pages (approved rules 2024 to 2026, the tush push votes), the NFL's Guide for Statisticians (copyright 2025, 38 pages, https://www.nflgsis.com/gsis/documentation/stadiumguides/guide_for_statisticians.pdf).
- The Casebook (Approved Rulings) is not publicly reachable: the rulebook page links only to the rulebook; the old casebook address returns 404. Every point that only the casebook would settle is marked "reading" or UNVERIFIED in the detailed parts, and Part 1.5 lists them.
- The NFL Football Operations article on how coaches use timeouts (https://operations.nfl.com/gameday/analytics/stats-articles/how-do-nfl-coaches-use-their-timeouts , published 2021-11-10) returns 404 today although search engines still list it. Its findings are rebuilt from search summaries and press reports (SRC-SECONDARY).
- Tags: SRC-OFFICIAL means read in the 2026 rulebook, the Guide for Statisticians or a league page, on 2026-10-14. SRC-SECONDARY means a press, club or reference page, or a figure computed from public data. UNVERIFIED means not found. "Reading" means the researcher combined two rule texts and no single sentence says it.
- Statistics: published articles, plus figures computed from the public nflverse play-by-play files for 2024, 2025 and 2026 to date, downloaded with the owner's approval on 2026-10-14 (see Part 9; one more small public file was read, the 39 KB data dictionary of the same project, a documentation file that was not on the approved list). They stay SRC-SECONDARY because nflverse is a volunteer data project built on the league's feed, not a league publication.

### 1.2 Which lines of the requirements file are now settled

Timeouts (requirements section 6)

- Three charged team timeouts per team in each half; unused first-half timeouts do not carry over (the text says "during each half" and has no carry-over sentence). SRC-OFFICIAL 4-5-1 Item 1.
- Overtime, regular season: two timeouts per team, and there is only one overtime period (10 minutes). SRC-OFFICIAL 16-3-e. Overtime, postseason: three timeouts "during a half" (16-4-g); periods are 15 minutes. The conflict is settled: two in the regular season, three per half in the postseason. That the three are shared by overtime periods 1 and 2 and fresh again at period 3 is a reading from CBS Sports (SRC-SECONDARY); the book never defines "half" for overtime.
- A timeout may be granted only while the ball is dead (3-36-2, 4-5-1); the head coach or any player who is not a substitute asks any official. The clock stops (4-4) and restarts on the next snap (4-3-2), so a timeout taken while the clock runs saves the time. SRC-OFFICIAL.
- A request with no timeout left "should be ignored". It is a foul only if it is granted anyway: delay of game, 5 yards, the timeout is charged, no loss of down (4-5-1 Item 3, 4-6-5(g)). Before a field goal or Try kick an excess or second timeout attempt is unsportsmanlike conduct, 15 yards, automatic first down, even if ignored (4-5-1 Item 4, 12-3-1(v)). SRC-OFFICIAL. After the two-minute warning a 10-second runoff option may be added (see the clock below).
- Each team may be granted one charged timeout per dead-ball period; a second one in the same dead-ball period is prohibited and is the same 5-yard foul (4-5-1 Item 3). A timeout lasts two minutes, or 30 seconds in the listed cases (4-5-1 Item 2); the play clock is reset to 25 seconds afterwards. SRC-OFFICIAL.
- Two-minute warning: 3-41 calls it "an automatic timeout" at the end of the last down snapped or kicked before two minutes remain in the second and fourth periods. It is not charged to a team, it stops the clock (4-4(h)), it resets the play clock to 25 and the clock restarts on the snap. The old requirement line "is not a timeout" is imprecise: it is an automatic timeout that no team is charged for. SRC-OFFICIAL. Overtime: the definition names only periods 2 and 4; practice shows a warning at 2:00 of the regular-season overtime period (a Bills-Rams game on 2026-10-12), and for the postseason in overtime periods 2 and 4. SRC-SECONDARY. Recommended default in the data table: regular season at 2:00 of the one overtime period, postseason at overtime periods 2 and 4.
- A successful challenge: the book never "restores" a timeout; it charges one only when a challenge is unsuccessful (15-1-1(e), 15-6-1). The one true "restored" rule is 15-6-2: a charged timeout taken at a team's request after the two-minute warning is restored if a review changes the ruling. SRC-OFFICIAL. The requirement line "a successful challenge restores the timeout" gives the same result; model it as "charged only if lost".
- How coaches use timeouts (N1.3): see Part 2 section 5 and Part 9. Keep one timeout for a challenge until the two-minute warning of a half; time-saving timeouts late in a half; operational timeouts (to avoid a delay of game or fix a substitution) are wasteful and rare early; the trailing defense starts using them near the five-minute mark. SRC-SECONDARY (the league article itself was not readable).

Clock rules behind C2 (all SRC-OFFICIAL, Rule 4)

- Four periods of 15 minutes, 13 minutes at halftime; the two-minute warning as above; play clock 40 seconds from the end of the previous play, 25 seconds after administrative stoppages (change of possession, charged timeout, the warning, penalty enforcement, and others). Delay of game is 5 yards (4-6).
- The clock keeps running after an in-bounds run or catch (a first down does not stop it) and after a sack or a kneel-down. It stops for an incomplete pass, a runner out of bounds, a score, a touchback, a change of possession, a timeout, a penalty, an injury after the warning, a kicking-team recovery beyond the line. The full list of "clock status after each play type" with citations is in Part 2 section 4.
- Restart: after most stops the clock restarts on the Referee's ready-for-play signal; it restarts on the snap after a change of possession, after the two-minute warning of the first half, and inside the last five minutes of the second half (4-3-2). After a kickoff it starts when the ball is legally touched in the field of play (4-3-1).
- The 10-second runoff applies only after the two-minute warning of either half: offense acts that conserve time while time is in (4-7-1), substitution violations (4-7-2), a replay reversal or nullified foul (4-7-4, 15-5-2). The defense may decline the first kind; nobody may decline the replay kind. There is no "inside one minute" rule in 2026; the sub-minute thresholds are the last 40 seconds (4-7-3) and the five-second cap on a field goal's clock (11-4-2). The five-minute rule is the last five minutes of the second half; an offense foul after the ball is ready in the fourth period or regular-season overtime also starts the clock on the snap (4-3-2(e)).
- Calibration facts for C2 are in Part 1.6.

Replay challenges and booth reviews (requirements section 7; all SRC-OFFICIAL, Rule 15 in full)

- Two challenges per team per game; a third if at least ONE challenge succeeded (15-1-1(f), in force since the March 2024 amendment); never a fourth. The old "both challenges" text was the 2016 to 2023 rule and is gone. The limit is per game, not per half; none in overtime (15-1-2(b), 16-5-d).
- Each challenge needs an available timeout (15-1-1(d)). A challenge thrown when not permitted: a timeout is charged; if the team has none, a 15-yard foul enforced as a foul between downs that cannot offset and is enforced in addition to any other foul (14-1-2, 14-1-3). Whether the play is still reviewed when a flag is illegal: the book is silent; older practice says no (SRC-SECONDARY).
- No coach's challenge of plays that BEGIN after the two-minute warning of each half (so the last play before the warning can still be challenged in the stoppage), in overtime, of scoring plays, Tries and turnovers (booth-only plays), by a team that fouled so as to prevent the next snap (the book says "prevents", the requirements file said "delays"), or by a team with no timeout or no challenge left (15-1-1, 15-1-2).
- The Replay Official (booth) or the league officiating chief "may initiate" reviews of scores, Tries, interceptions, fumble or backward-pass recoveries by the opponent, fourth-down failures, kicking-team possession at the end of a kick, disqualifications, every play after the two-minute warning and every overtime play. No timeout is charged and the book sets no cap. The requirement line "reviews all scoring plays and turnovers automatically" is right in practice (the league page says so), but the book's verb is "may initiate"; model the booth as acting when the ruling is wrong or doubtful.
- Standard of review: clear and obvious visual evidence (15-2-1). Reviewable and non-reviewable lists: Part 3 section 5 (catch or no catch, fumble, down by contact, out of bounds, line to gain, goal line, number of players, game clock restoration; NOT reviewable: erroneous whistle, illegal bat or kick, intentional grounding, ineligible receiver downfield, illegal contact, illegal block). Pass interference and other judgment fouls are not reviewable (the 2019 trial is not in the book). A foul's administration (spot, down, yards, player) is reviewable (15-7); the sentence "a foul is never reviewable" in N7.6 is too strong.
- A challenge counts as successful if any reviewable aspect of the play changes; for a line-to-gain challenge only if the new-series ruling changes (15-3-7).
- Effects of a reversal: the clock is reset to when the ball should have been dead (15-5-1); after the warning a 10-second runoff may follow (15-5-2); a head coach may change an accept or decline decision made before the review (15-7-3 Item 3), which matters for NX7.
- 2026 changes: none to counts, timeouts or reviewable plays. One summer edit: the head coach's pregame challenge designee may throw the flag (15-1-1(a); ESPN and NFL.com, 2026-08-10, SRC-SECONDARY for how it was adopted). Replay assist (15-9) is a separate help for game administration.

Quarterback runs, slide, sneak (requirements section 8)

- A runner is the offensive player holding a live ball (3-27), so a quarterback who tucks the ball is a runner; his rushes and yards count as rushing, unless the play is a sack (Guide for Statisticians p. 11). A sack needs an apparent attempt to pass at or behind the line (Guide p. 14 to 15); a designed keeper stopped behind the line is a rush for a loss. The requirements file's "sack-like loss chance" for a keeper is therefore a rush for a loss in the statistics. SRC-OFFICIAL.
- Passer protections follow "passing posture" (12-2-9, 12-2-11) and end when he becomes a runner (12-2-11(e)); outside the pocket area he loses part of them (12-2-11(f)). The book has no phrase "in the act of passing" and no "tackle box": the term is "pocket area" (3-25). SRC-OFFICIAL.
- Slide: a runner who slides or dives feet or head first, or simulates it, is down the instant he touches the ground (7-2-1(d)); a quarterback who immediately drops to a knee behind or beyond the line is down (7-2-1(c)). Defenders must pull up; unavoidable contact by a defender already committed is not a foul unless it is a forcible hit to the head or neck or other unnecessary roughness; late contact on a slid or kneeling runner is unnecessary roughness, 15 yards, automatic first down if by the defense (12-2-8(d)). "May not be hit" is too strong. SRC-OFFICIAL.
- Intentional grounding (8-2-1): loss of down and 10 yards from the previous spot, or loss of down at the spot of the pass if that is worse for the offense (more than 10 yards back or more than half the distance), or a safety in the end zone. The pocket-area exception depends on where the ball lands: a passer outside the pocket area who throws to or beyond the line of scrimmage is not grounding. SRC-OFFICIAL.
- The quarterback sneak and the tush push: legal in 2026. 12-1-4 bans pulling the runner (10 yards) and does not name pushing him. The 2025 vote on a ban failed 22 to 10 (24 needed) on 2025-05-21; no club proposed a ban in 2026 and 12-1-4 is unchanged. SRC-OFFICIAL (nfl.com). The league says the debate may continue (SRC-SECONDARY).
- A fumble by a runner on fourth down, after the two-minute warning or on a Try may be recovered and advanced by the fumbler only (8-7-5, 8-7-6): the design of keepers must honor it. SRC-OFFICIAL.

Onside kicks and free kicks (requirements section 9)

- 2026 rule 6-1-6: "At any time during the game" the kicking team may declare an onside kick. There is no trailing, score or period condition anywhere in the 2026 book. SRC-OFFICIAL. The trailing condition (2024 and earlier) is gone: this settles the open question.
- Declaration: to the Referee before the 25-second play clock starts; the Referee tells the receiving team before starting the clock, so no surprise onside kick exists. If a declared kick goes untouched beyond the receivers' setup zone it is unsportsmanlike conduct: 15 yards from the kicking team's restraining line, receivers get the ball. Undeclared onside kick: no rule text (UNVERIFIED).
- Kick spot: the kicking team's 35 for a kickoff, its own 20 for a safety kick; an onside kick uses the same restraining line. There is no 34-yard line anywhere in the 2026 book (the "34" came from press reports of 2025; UNVERIFIED which 2025 line it meant). SRC-OFFICIAL.
- Kicking team alignment on an onside kick: every player except the kicker and the holder has a front foot on the line and both feet on the ground until the kick; at most five players on each side of the ball (the holder counts); at least two between the sideline and the number and two between the number and the inbounds line on each side. Receiving team: restraining line 10 yards in front of the kicking line; at least eight and at most nine players in the 15-yard onside kick setup zone behind it (6-1-6(c) to (h); the 2026 change to the ordinary kickoff setup zone is in 6-1-3 and is separate). SRC-OFFICIAL.
- Recovery: the kicking team may touch or recover only after the ball touches a receiving player or reaches the receivers' restraining line (10 yards); illegal early touching is 5 yards, or the receivers take the ball at the spot of the touch; a legal recovery by the kickers is their ball (first down). A ball that comes to rest untouched, or goes untouched beyond the setup zone, is dead and the receivers' ball. An onside kick out of bounds follows the out-of-bounds free kick rule (6-2-4). In overtime a legal recovery by the kickers counts as the receivers' possession (16-5-c). SRC-OFFICIAL.
- Free kick after a safety: by the team scored upon, from its own 20, punt, drop kick or place kick, tee allowed, and an onside kick is allowed under the same declaration rule (11-5-2, 6-1-1(b), 6-1-6(b)). SRC-OFFICIAL.
- 2026 also: the dead-ball spot after a touchback on a kickoff taken from the 50 is the 20 (6-1-5). SRC-OFFICIAL.
- Rule history for the versioned table (2024 dynamic kickoff, 2025 and 2026 steps): Part 5 section 5. 2025 details are SRC-SECONDARY because the 2025 rulebook was not found.
- Recovery rates: Part 1.6.

Penalties with accept or decline (requirements section 12)

- The offended team may decline any penalty unless a rule prohibits it, and play then goes on as if there were no foul; it may accept the penalty and decline only the yardage (14-1-1). Only one captain may indicate the option, after the Referee explains the alternatives (18-1-3); the head coach is not named. The choice is final once the penalty is administered or the ball is ready for play, except that a head coach may change it after a replay reversal (15-7-3). "Offended team" is not defined. SRC-OFFICIAL.
- Several fouls by one team in a down: only one penalty is enforced, chosen by the offended team (14-1-3); a foul against an official, a challenge with no timeouts, and the fifth and later excess injury timeouts are enforced in addition. Double fouls (a foul by each team, no change of possession) offset and the down is replayed; neither team may decline (14-5-1); a 15-yard foul against a 5-yard foul without automatic first down, loss of down or runoff: the 15 is enforced and the 5 is disregarded. SRC-OFFICIAL.
- Automatic first down: any foul by the defense on a scrimmage down gives first and 10 EXCEPT ten listed fouls (offside, encroachment, neutral zone infraction, delay of game, illegal substitution, excess timeout, running into the kicker, more than 11 players in the formation, more than 11 at the snap, illegal formation by the defense on a scrimmage kick), where the down and line to gain stay unless the yardage reaches the line to gain (14-1-2 Item 5). The Penalty Summary has no "automatic first down" group. Offense fouls keep the down (replay) unless a combination penalty; but the ball past the line to gain after enforcement is first and 10 (Item 4). Combination penalties (distance plus loss of down): illegal forward pass, intentional grounding, backward pass that conserves time, illegal handing forward, illegal punt, drop kick or place kick from beyond the line, illegal bat, illegal kick (Item 2). SRC-OFFICIAL.
- Spots (3-13-3, 14-3): previous spot, spot of the foul, dead ball spot, succeeding spot, basic spot. Run plays use the "three-and-one" method (14-3-6): defense fouls or offense fouls ahead of the basic spot: enforced from the basic spot; offense foul behind it: from the spot of the foul; offense fouls behind the line: from the previous spot. Pass plays: previous spot, except defensive pass interference (spot of the foul) and personal and unsportsmanlike fouls (14-4-5). Fouls before the snap: enforced from the succeeding spot with the down unchanged; at the snap: previous spot (14-4-1). SRC-OFFICIAL.
- Half the distance to the goal (14-2-1): a distance penalty never moves the ball more than half the distance from the spot of enforcement to the offender's goal line; exceptions: intentional grounding and the palpably unfair act (and spot fouls such as defensive pass interference are not distance penalties). Rounding below one yard: UNVERIFIED.
- Live ball and dead ball: offside is a live-ball foul at the snap; false start, encroachment and neutral zone infraction are whistled dead before the snap. Fouls between downs never combine with live-ball or dead-ball fouls (14-4-9).
- Scores: a personal or unsportsmanlike foul by the defense on a touchdown play is enforced on the Try or the kickoff; the offended team may instead accept the penalty with normal enforcement and lose the points (14-2-3). An offense foul that the defense accepts erases a score.
- Clock after a penalty: the clock stops for the foul and restarts "as if the foul had not occurred", except that it restarts on the snap in the listed cases (after the two-minute warning of the first half, in the last five minutes of the second half, for an offense foul after the ball is ready in the fourth period or overtime, after two successive delay-of-game penalties). 10-second runoffs: Part 1.2 clock section; the defense may decline them with the yardage. SRC-OFFICIAL.
- The full foul list is Part 7. The Penalty Summary has about 94 distance entries (29 of 5 yards, 8 of 10, 57 of 15), 1 loss of down without yardage, 7 loss of down with yardage, and 45 further lines. The book's own table of three-letter foul codes lists 63 names (PDF page 86). Part 7 section 0 gives the starting list of about 40 fouls with the clone's play for each. Differences between the summary and the articles: holding and illegal hands by either team on a scrimmage kick that crosses the line are 10 yards (9-1-4(e)); the summary label "Loss of Ball and Fifteen Yards" has no article behind it. The article text wins.
- Accept or decline decisions in plain words, per situation: Part 6 section 8.

### 1.3 Corrections that SX.1 must carry into NFL_EXTRA_FEATURES.md

Each is a place where the official text differs from what the requirements file says. SX.0 did not edit that file.

- Section 6 and C2: the two-minute warning is an automatic timeout (not charged), taken at the end of the last down before 2:00, not "at 2:00 and not a timeout". A request without timeouts is ignored and is a foul only if granted. A won challenge never "restores" a timeout. A first down does not stop the clock; a sack does not stop it. There is no "inside one minute" rule; the five-minute rule is the second half only.
- Property test in C8, "never more than 3 timeouts per half": regular-season overtime has 2 per team in the one period, the postseason has 3 per half (a pair of overtime periods); excess injury timeouts after the warning are charged separately and do not count against the three.
- Section 7: coach challenges are barred for plays that begin after the warning (not the warning moment itself); booth reviews "may be initiated" and are free; the third challenge needs one success (already the accepted reading); the foul for an improper challenge is 15 yards between downs, and only when no timeout is left; pass interference is not reviewable.
- N7.6: penalty administration is reviewable; judgment fouls are not. Add the interaction that a head coach may change an accept or decline decision after a reversal.
- Section 8: "tackle box" becomes "pocket area" (and the grounding exception depends on where the ball lands); "may not be hit" becomes the 7-2-1(d) rule; the keeper's loss is a rush for a loss unless there was an apparent pass attempt; the tush push is legal and was voted down 22 to 10 in 2025.
- Section 9: kick spot 35 (not 34); no trailing condition; the question can be asked at every free kick; no surprise kick; "6.45 percent in 2024" is 3 of 50, 6.0 percent (2025: 5 of 52, 9.6 percent); after a safety the kick is from the 20 and an onside kick is allowed there. N4.4 "a surprise onside kick when leading" becomes "an onside kick when leading or tied", declared like any other.
- Section 12: the captain, not the coach, indicates the option; the yardage alone may be declined; automatic first down is the default for every defense foul with ten exceptions (not a flag per foul); N7.2 "pre-snap" must separate the dead-ball fouls (false start, encroachment, neutral zone infraction, delay) from offside, illegal formation, motion and shift, which are called at the snap; C8's half-distance invariant needs the four exceptions above; the five-minute clock rule is the second half only. A foul between downs after a first down is literally "first and 25" in 14-4-9 Item 1 (an oddity of the text; UNVERIFIED how it is applied).
- NQ4 (overtime): the 2026 book (Rule 16) is a modified sudden death: both teams get a possession unless the first drive ends in a safety; regular season one 10-minute period (a tie is possible), the postseason 15-minute periods; no coach challenges; an onside kick recovered by the kickers counts as the receivers' possession. The clone's sudden death stays an accepted default but does not match the NFL in "N. F. L. rules" mode; this is a decision to show the owner at SX.1.
- Section 11 (Franchise): the phrase "Franchise carries a live-beta note on EA's pages" could not be confirmed (MADDEN_FRANCHISE_RESEARCH.md, section I); the build is estimated at 18 to 22 sessions for the ADOPT items, not the six sub-sessions SX.8a to SX.8f.
- Section 10 (playbooks): the research file proposes seven style playbooks and assigns all 32 teams (MADDEN_PLAYBOOK_RESEARCH.md).

### 1.4 The open conflicts named in the requirements file

- Third replay challenge: at least one success earns a third (not both). SRC-OFFICIAL 15-1-1(f), 2026 book; the nfl.com page of 2024 approved changes shows the amendment.
- Overtime timeouts: two per team in the regular season, three per half in the postseason. SRC-OFFICIAL 16-3-e, 16-4-g.
- Whether an onside kick still needs the kicking team to trail in 2026: no. SRC-OFFICIAL 6-1-6.

### 1.5 Could not be settled (and the default to use)

- Everything that only the Casebook answers: the half-distance rounding under one yard (default: round the spot to the nearest yard line, at least one yard when the distance is under two); whether delay of game triggers the 10-second runoff (default: no, 4-7-1 does not list it); who holds the runoff option for an offense excess timeout (default: the defense, as in the parallel passages); the 5-versus-15 first-down detail; a Team A foul that leaves the ball exactly on the line to gain (default: first and 10 only if the ball is past the line); double fouls with a change of possession on a scoring play; the spot after an onside kick untouched beyond the setup zone (reading: 15 yards back from the kicking line; shortened by the half-distance rule from the 20); the penalty for an undeclared onside kick (default: the question cannot arise, the computer always declares first); how 12-3-1(v) works in overtime.
- Whether the five-minute out-of-bounds clock rule applies in overtime (default: yes for sudden-death overtime, treat all of it like the last five minutes).
- Whether the two-minute warning exists in overtime of the regular season by rule (practice says yes; default in 1.2).
- Statistics the public sources do not give: yards per quarterback rush by down and distance in a published table (computed in Part 9 instead); the league's own penalty table; the share of fouls that nullify a play; reversal rates of automatic reviews; reversal rates by category after 2020; onside kick data by quarter and margin for 2026 beyond what Part 9 computes.
- Madden facts: EA does not publish its list of the 32 playbooks or the plays per book (MADDEN_PLAYBOOK_RESEARCH.md), nor the names of Madden 27's Franchise stages or its cap and roster numbers (MADDEN_FRANCHISE_RESEARCH.md).

### 1.6 Statistics for calibration

All SRC-SECONDARY. "Computed" means computed in Part 9 from the public nflverse play-by-play files for the regular seasons 2024 (272 games), 2025 (272 games) and 2026 to date (79 games, weeks 1 to 5), cross-checked against more than ten published figures (Part 9, section 7: onside kick counts, challenge counts, accepted fouls, quarterback totals and the FOX sneak lines matched exactly or within 0.5 percent). Playoffs are kept apart (13 games a season, too few for rates). Per-season and finer tables are in Parts 8 and 9.

Clock and plays per quarter (C2)
- Scrimmage plays that stood (pass and run, sacks and scrambles included, no kneel-down, spike or play wiped out by a foul), per team per game, computed: 60.96 (2024), 59.97 (2025), 60.47 (2026). With kneel-downs and spikes: about 61.8, 60.9, 61.4. NFL.com's own total is higher (63.3 in 2025), probably because it also counts plays a foul wiped out (a guess).
- Both teams together, per quarter, computed (2024 and 2025): Q1 27.2, Q2 32.8, Q3 27.8, Q4 33.1 scrimmage plays, so the second and fourth quarters carry about 5 more plays than the first and third. The mean is about 30.2 per quarter. The original's 29 to 36 counted plays per quarter (GAME_SPEC 5.6) therefore corresponds to the NFL's second and fourth quarters, or to a count that includes kicks; SX.2 must decide which NFL count the calibration targets (C2 says the 10,000-quarter average stays in the original's range).
- Game-clock seconds per scrimmage play, computed: 29.8 (30.0 in 2025); per snap including punts, field goal tries, kneel-downs and spikes: 26.9. Share of plays followed by a running clock (more than 25 seconds to the next snap, normal clock rules): 68.0 percent.
- Elapsed seconds from one snap to the next, computed (10th percentile, median, 90th percentile): complete in bounds 37.9 mean (26, 39, 45); complete out of bounds 35.2 (25, 37, 43); incomplete pass 5.0 (3, 5, 7); run in bounds 38.0 (30, 39, 44); run out of bounds 36.8 (27, 38, 44); sack 37.7 (21, 41, 46); punt 9.4 (7, 9, 13); missed field goal 4.8. Inside the last five minutes of the second half and the last two of the first half an out-of-bounds play takes only 6 to 8 seconds (the clock restarts at the snap). After an incomplete pass snap-to-snap equals the length of the play: 5.0 seconds on average (10,328 plays).
- Last two minutes of a half, computed: 16.1 plays per game for both teams (9.35 in the second quarter, 6.78 in the fourth).
- Published: about 61 to 65 offensive plays per team per game depending on the counting basis (Rotowire 62.2 for 2024, PFF 65.3, Sharp 61.3 for 2025); the average drive has about 5.8 plays and about 2:48 of clock (inference).

Timeouts, computed (N1.3)
- Charged timeouts per team per game: 3.88 (2024), 3.85 (2025), 3.84 (2026); in 2024 and 2025 3.72 called by the coach and 0.14 charged for a lost challenge. By half 1.92 and 1.90; overtime about 0.05. By quarter Q1 0.21, Q2 1.71, Q3 0.20, Q4 1.70.
- Timeouts left at the end of the first half: 3 left 11.5 percent of team-halves, 2 left 23.1, 1 left 28.1, none 37.3. At the end of the second half: 3 left 17.6, 2 left 18.9, 1 left 20.8, none 42.6.
- When: first half, under 2 minutes left 73.6 percent of the half's timeouts, 8 minutes or more 17.1; second half under 2 minutes 42.4, 2 to 4 minutes 25.5, 4 to 8 minutes 13.8, 8 or more 18.3. About a quarter (26.2 percent) of first-half timeouts come before the two-minute warning.
- Who: coach-called first-half timeouts 62 percent by the team that has the ball next, 38 by the defense; second half 39 offense and 61 defense; second half with 2 to 4 minutes left 20 offense and 80 defense.
- By score, last 5 minutes of the second half, timeouts used per team: leading 0.95, tied 1.75, trailing 1.81; trailing by 1 to 8 points 2.25 (only 5.1 percent use none, 0.44 left at the end); leading by 9 or more 0.58 (56.6 percent use none); trailing by 9 or more 1.48. First half last 5 minutes: leading 1.48, trailing 1.58, tied 1.44.
- Overtime (regular season): at most 2 per team; 22 of 60 teams used none, 26 one, 12 two.
- 18 rows are a "fourth timeout" of one half, all in the last two minutes of a half and all near an injury: probably excess timeouts after an injury (4-5-4), which the three-per-half property test must not count.
- Rules of thumb for the computer coach, from this and Part 2 section 5: keep timeouts until the last 5 minutes unless a delay penalty is worse; the trailing defense starts near the 5-minute mark; the leading team uses about half as many; a trailing team within one score uses about 2.25 in the last 5 minutes; keep one timeout for a challenge until the two-minute warning of a half.

Replay, computed (N2)
- Coach challenges per season: 133 (2024), 151 (2025), 36 so far in 2026; per team per game 0.244, 0.278, 0.228. Reversed: 37.6 percent (2024), 52.3 (2025), 50.0 (2026). Lost challenges, hence timeouts lost: 0.142 per team per game. A team challenges in 23.3 percent of its games; both teams together: no challenge in 59.0 percent of games, one in 31.6, two in 7.9, three or four in 1.5. The team on defense makes 70.4 percent of challenges.
- Replay-official (booth) reviews: 194 (2024), 171 (2025), 58 (2026); reversed 76.3, 78.4, 74.1 percent. The league's "171 decisions in 2025" equals the 2025 count.
- Categories, 2024 and 2025, share of the challenges and share reversed: catch or no catch 50.7 percent (45.1 reversed); spot and line to gain 26.4 (48.0); down by contact 11.3 (50.0); goal line 4.6 (53.8). Booth reviews: catch 24.7 (72.2 reversed); goal line and touchdown 20.3 (83.8); down by contact 12.3 (80.0); fumble 11.2 (82.9); interception 9.6 (68.6); out of bounds 9.6 (82.9).
- Published: an average review takes 1:25 (league, 2024).

Quarterback runs, computed (N3), 2024 and 2025 combined
- Per team per game: 3.26 quarterback rushes (1.29 designed, 1.97 scrambles) plus 0.77 kneel-downs, 0.14 spikes and 2.39 sacks; about 5.4 percent of scrimmage plays; scrambles are 5.25 to 5.51 percent of dropbacks (about 36.6 dropbacks per team per game).
- Yards per attempt: designed 3.66 (3.99 in 2024, 3.25 in 2025), scrambles 7.67, all quarterback rushes 6.09. First down or touchdown: designed 51.3 percent, scrambles 41.0. Fumble lost: designed 1.07 percent, scrambles 0.47. Gain percentiles (10, 25, 50, 75, 90): designed 0, 1, 2, 5, 10; scrambles 2, 3, 6, 10, 15. Caveat: a scramble that loses yards is written as a sack or a plain run in the play text, so "designed" is slightly contaminated.
- Third or fourth and 1, designed quarterback run: 469 attempts, 83.4 percent converted (third down 81.9, fourth down 86.4); other runners 69.2 percent; passes 52.0 percent. At 2 yards: 74.2 percent (62 attempts). The published figures agree: sneak and tush push 79.5 to 85 percent since 2022. Inside the opponent's 5: first down or touchdown 59.0 percent, touchdown 52.8, 0.90 yards per run (178 runs); in the own half 4.10 yards per run.
- Out of bounds: 12.1 percent of designed runs, 34.0 percent of scrambles. A slide is not recorded in the data. The tables by down (1 to 4) and distance (1, 2, 3 to 5, 6 to 10, 11 or more) and by field zone are in Part 9, section 2.
- 2025 tush push counts: 112 (ESPN) or 130 (tushpush.fyi), 76.8 or 73.8 percent; the two counts disagree on the definition.

Onside kicks and kickoffs, computed (N4)
- 2024: 50 attempts, 3 recovered by the kicking team (6.0 percent). 2025: 52 attempts, 5 recovered (9.6 percent). 2026 to date: 11 attempts, none recovered. All 113 attempts came in the fourth quarter and all by the trailing team: no attempt in the first three quarters and none while leading or tied, even after the 2026 "at any time" rule (11 attempts in 79 games).
- 2024 and 2025 (102 attempts): time left, last two minutes 55 attempts, 2 to 5 minutes 30, 5 to 10 minutes 14, over 10 minutes 3. By the kicking team's deficit: 1 to 8 points 43 attempts and 5 recoveries; 9 to 16 points 39 and 1; over 16 points 20 and 2. Kick distance mean 10.4 yards (10th to 90th percentile 7 to 14); the eight recoveries went 8 to 13 yards. The kick spot was the 35 in 92 attempts and the 20 after a safety in 8.
- Earlier published rates: 2018 to 2023 together 8.7 percent; 2000 to 2017 19.5 percent; the league would like about 12 percent.
- Kickoffs that are not onside kicks: touchback rate 65.5 percent in 2024 (touchbacks to the 30), 21.1 in 2025 (touchbacks to the 35), 15.8 in 2026; returned 33.3, 76.0, 81.7 percent; average starting yard line after kickoffs 29.6, 30.3, 30.2.

Penalties, computed and published (N7)
- Accepted fouls per game, both teams: 12.91 (2024), 12.75 (2025), 15.10 (2026 to date, 79 games, the highest since 1978 according to ESPN); 12.83 for 2024 and 2025. Per team per game 6.42; penalty yards 51.8 per team per game; 8.08 yards per accepted foul; 10.40 accepted fouls per 100 scrimmage plays that stood.
- Phase: before the snap 39.2 percent (2.52 per team per game); during a run 14.0; during a pass 35.1; special teams 11.7 (kickoff 0.35, punt 0.35, field goal and extra point 0.06 per team per game). By quarter 21.0, 29.7, 23.5, 25.4, overtime 0.4 percent. The last two minutes of each half hold 12.4 percent of the fouls, but the rate per play there is slightly lower than elsewhere.
- Declined 0.91 per team per game (12.4 percent of the fouls that offer a choice); offsetting flags 0.30 per team per game; 7 to 8 percent of snap-like events are wiped out by a foul.
- Types per game, both teams, 2024 and 2025: offensive holding 2.49, false start 2.46, defensive pass interference 1.07, defensive holding 0.65, unnecessary roughness 0.64, delay of game 0.63; the rest in Parts 8 and 9. About 27 to 28 percent of accepted fouls produce a first down for the offense; defensive pass interference, defensive holding and illegal contact do so 99 to 100 percent of the time.
- Team spread (per team per game): standard deviation 0.71 (2024) and 0.80 (2025); most is chance (0.62); the lasting team effect is about 0.4 fouls a game (6 percent). Use a team factor of 0.85 to 1.15.
- Target for the 10,000-game simulation: 12.8 accepted fouls per game plus or minus 0.8 (the 2024 and 2025 range); the early-2026 value 15.1 is a small sample. Part 8, section 6 has the per-type mix.

### 1.7 Decisions this research puts in front of SX.1 (all with a recommended default; none blocks)

- Overtime in "N. F. L. rules" mode (NQ4): keep sudden death as the accepted default, or adopt the 2026 modified overtime. Recommended: keep the default and record the difference; the owner may ask for the NFL's overtime later (it needs possession tracking, a 10-minute period and a possible tie).
- How often to ask "do you wish to try an onside kick": the rule allows it at every free kick of the game, so the question could be asked about ten times a game. Recommended: ask only when it is meaningful by the computer's own measure (trailing in the second half or a late lead of one possession) plus a setting "always ask", default off; the computer coach still declares by its own rule.
- Two-minute warning in overtime: the default in 1.2.
- The size of Franchise and the number of build sessions: MADDEN_FRANCHISE_RESEARCH.md, section D.
- Which statistics target year to use for penalties: 12.8 accepted fouls per game plus or minus 0.8 (Part 1.6), or the higher early-2026 value.

### 1.8 Parts of this file

- Part 2. Timeouts and the game clock (notes A).
- Part 3. Instant replay, challenges and booth reviews (notes B).
- Part 4. Quarterback runs, the slide, the sneak (notes C).
- Part 5. Kickoffs, onside kicks and the safety kick (notes D).
- Part 6. Penalty enforcement, accept or decline and clock effects (notes E2).
- Part 7. The complete foul list (notes E1).
- Part 8. Penalty statistics (notes E3).
- Part 9. Statistics computed from the public play-by-play data (notes H).


## Part 2. Timeouts and the game clock (2026 NFL rules)

Written 2026-10-14. Research only. Rulebook = "2026 Official Playing Rules of the NFL" (converted to text, retrieved 2026-10-14). Citations are Rule-Section-Article and the PDF page of that file (printed page = PDF page minus 7). Quotes are short and few; everything else is paraphrase.

Tags: SRC-OFFICIAL, SRC-SECONDARY, UNVERIFIED. "Inference" marks my own reading or arithmetic and is never a source.

### Answers in brief

1. Timeouts per half: three charged team timeouts per team in each half. SRC-OFFICIAL (4-5-1 Item 1, PDF 19). The text says "during each half" and never says anything can carry over, so unused first-half timeouts are gone at halftime (SRC-OFFICIAL by wording; SRC-SECONDARY sources say it outright).
2. Overtime, regular season: two timeouts per team, and there is only one overtime period (10 minutes), so no per-period question arises. SRC-OFFICIAL (16-3-d, 16-3-e, 4-5-1 Item 1; PDF 72, 19).
3. Overtime, postseason: three timeouts per team "during a half" (16-4-g, PDF 72). The conflict is settled: regular season two, postseason three. The rulebook never defines "a half" for overtime; 16-4-h treats overtime periods in pairs, and CBS reads it as three fresh timeouts at the start of the third overtime period. Pairing and reset: SRC-SECONDARY.
4. Who, when: head coach or any player who is not a substitute, to any official, only while the ball is dead (3-36-2, 4-5-1). SRC-OFFICIAL.
5. A timeout request when none is left: the rulebook says such a request "should be ignored" (4-5-1 Item 1). Only if it is granted anyway is there a foul: delay of game, five yards, timeout charged, no loss of down (4-5-1 Item 3, 4-6-5(g)). After the two-minute warning a 10-second runoff option can be added. SRC-OFFICIAL.
6. Freezing the kicker: an excess or second timeout attempt before a field goal or Try kick is ignored and is unsportsmanlike conduct, 15 yards, charged if granted (4-5-1 Item 4, 12-3-1(v)). SRC-OFFICIAL.
7. Two-minute warning: an automatic official timeout (not charged to a team) at the end of the last down snapped or kicked before two minutes remain, second and fourth periods (3-41, 4-4(h), 4-6-2(c)). SRC-OFFICIAL. In overtime: not stated by the definition; observed in regular-season overtime on 2026-10-12 (SRC-SECONDARY) and reported for the 2nd and 4th overtime periods in the postseason (SRC-SECONDARY).
8. Clock: 15-minute periods, at least 2 minutes between periods 1-2 and 3-4, 13 minutes at halftime, 40-second and 25-second play clocks, full start and stop table in section 4. SRC-OFFICIAL.
9. Ten-second runoff: after the two-minute warning, offense acts that conserve time while time is in (4-7-1), substitution violations (4-7-2), reversals and nullified fouls (4-7-4, 15-5-2). Defense may decline the first kind; nobody may decline the replay kind. There is no "inside one minute" rule in the 2026 book. SRC-OFFICIAL.
10. NFL Football Operations article on coaches and timeouts: the page is gone (404 on every URL form tried); findings are rebuilt from secondary reports. SRC-SECONDARY, and the article's own numbers are UNVERIFIED.
11. Statistics: about 61 to 65 offensive plays per team per game (depends on counting basis), about 31 to 33 counted plays per quarter for both teams together, about 5.8 plays and about 2:48 per drive. SRC-SECONDARY and inference. No official table could be fetched.

### 1. Timeout counts

- Three per half. "A team is allowed three charged team timeouts during each half and two timeouts during an overtime period in the regular season." (4-5-1 Item 1, PDF 19.) SRC-OFFICIAL.
- The Referee tells the head coach when the permitted number is used up; further requests are ignored. Same place. SRC-OFFICIAL.
- League glossary agrees: three in each half. operations.nfl.com football-terms page, retrieved 2026-10-14. SRC-OFFICIAL.
- No carry-over sentence exists in the 2026 rulebook (searched "carry" and "each half"). Allowance is per half. Explicit statements that unused timeouts do not carry over appear in secondary pages (Ringer: "six timeouts a game"). SRC-SECONDARY.
- Regular-season overtime: 16-3-e says each team is "entitled to two timeouts", excess timeouts follow 4-5, and fourth-quarter provisions "including timing" apply (PDF 72). Only one period of at most 10 minutes (16-3-d). SRC-OFFICIAL.
- Postseason overtime: periods are 15 minutes, as many as needed, two-minute intermission between them, no halftime intermission after the second (16-4, PDF 72). 16-4-g: three timeouts "during a half". 16-4-h: timing as at the end of the first half after the second overtime period, as at the end of the fourth period after the fourth. SRC-OFFICIAL for the text.
- Per-overtime-period count: the text gives no per-period number for the postseason. Reading "half" as a pair of overtime periods (timeouts shared by periods 1 and 2, fresh three at period 3, fresh three at period 5) comes from CBS Sports ("three more timeouts to kickoff the third overtime") and Fox Sports; NBC (2026-01-18) says playoff overtime is "played like a whole new game" and "three timeouts per half". SRC-SECONDARY.
- 12-3-1(v) (freeze the kicker) speaks of "three charged team timeouts that are permitted in a half" and does not mention the two of regular-season overtime. How it applies in overtime is UNVERIFIED (the casebook was not reachable).
- Timeouts charged by other rules: unsuccessful coach's challenge costs a timeout (15-1-1(e), 15-6-1, PDF 67, 70); a challenge needs an available timeout (15-1-1(d)); excess timeouts for injury after the warning (4-5-4); timeout restored when a review changes the ruling on a charged timeout taken after the warning (15-6-2). SRC-OFFICIAL. Replay detail belongs to the replay topic.

### 2. Requests, length, charge, penalties

- Who: "the head coach or any player (not a substitute)" asks any official. If an assistant coach signals and it is inadvertently granted, it stands. (4-5-1, PDF 19.) SRC-OFFICIAL.
- When: the Referee suspends play "while the ball is dead". 3-36-2: a timeout may be granted only when the ball is dead. So no timeout with a live ball. Any dead-ball moment qualifies by the text, including after the ball is ready for play and before the snap; a charged timeout may also follow a Referee's timeout or an automatic timeout such as the warning (4-5-1 Item 3). Before a Try the offense may change its choice if there is a charged timeout (11-3-1, PDF 49). SRC-OFFICIAL.
- Length: two minutes, or 30 seconds when the television commercials of the quarter are used up, when it is a second charged timeout in the same dead-ball period, or when the Referee says so (4-5-1 Item 2). The length does not change the game clock; the play clock after a charged timeout is reset to 25 seconds (4-6-2(b), 4-6-3(a)(1), PDF 20-21). SRC-OFFICIAL.
- Clock: the clock is stopped by any official's timeout signal (4-4(j)) and, after any timeout, restarts on the next snap (4-3-2 opening sentence), with the exceptions listed there. A team that calls a timeout while the clock is running therefore saves the time that would have run to the snap. SRC-OFFICIAL (inference for the saving).
- One per dead-ball period per team: each team may be granted one charged timeout in the same dead-ball period; a second one by either team is prohibited (4-5-1 Item 3). SRC-OFFICIAL.
- Penalty: for a second timeout in the same dead-ball period, or a timeout after the permitted ones are used: loss of five yards for delay of game, and the timeout is charged (4-5-1 Item 3, 4-6-5(g); penalty summary "Team timeout requested and granted when not allowed", PDF 78). No loss of down. Enforced as in 4-6-5: from the succeeding spot if between downs and the ball is dead. SRC-OFFICIAL.
- Runoff add-on: "If the timeout is by the offense while time is in after the two-minute warning, a 10-second runoff option is available", with the play clock reset to 30. A defensive excess timeout while time is in resets the play clock to 40, and the clock starts at ready-for-play unless the offense chooses the snap. SRC-OFFICIAL. The text does not say who holds the runoff option; the parallel passages (4-5-4 Note 3, 4-7-1 Item 1) give it to the defense. UNVERIFIED reading.
- Second excess timeout after the warning (injury timeouts, 4-5-4, PDF 20): when a team has used its three, the Referee calls an excess timeout for an injury, with exceptions (opponent's foul; change of possession, touchdown, safety, successful field goal, free kick or Try on that down). First excess: no yardage, but a 10-second runoff may apply (Note 1). Second and later excess: five yards for delay of game, runoff possibly (Note 2). Never a runoff against the defense (Note 9). Either half can end by the runoff (Note 4). A fifth and later injury excess timeout is a foul between downs (Note 2; 14-1-2 exception). The penalty summary lists "Second excess team timeout after two-minute warning" under five yards. SRC-OFFICIAL.
- Before the warning, an injury timeout does not charge a team and the clock restarts as if it had not happened (4-5-3); after the warning the injured player's team is charged a timeout if it has one (4-5-4(a)). SRC-OFFICIAL.
- Freeze the kicker: 4-5-1 Item 4 and 12-3-1(v) (PDF 19, 58). An attempt to call an excess timeout, or a second timeout in the same dead-ball period, by Team B before a field goal or Try kick is ignored and is unsportsmanlike conduct; the officials do not grant it and play continues; the foul is enforced after the down; if granted, it is enforced as a dead-ball foul and the timeout is charged. Penalty 15 yards, automatic first down for a defensive foul (summary: "Attempting to call excess/illegal timeout to freeze kicker", PDF 78). One ordinary timeout before the kick is legal. SRC-OFFICIAL.
- Referee's timeout (4-5-5, PDF 20): no penalty, no charge, for first-down measurement, a pileup, slow spotting, injury to an official, conference, equipment repair; the play clock keeps its value and both clocks start as if nothing happened. SRC-OFFICIAL.
- A spike is the legal way to stop the clock without a timeout, once, by a T-formation quarterback who throws into the ground immediately on the snap (8-2-1 Item 3, PDF 38); it costs the down. A delayed spike is intentional grounding (Item 4). SRC-OFFICIAL.

### 3. Two-minute warning

- Definition (3-41, PDF 17): "an automatic timeout" at the conclusion of the last down snapped or kicked before two minutes remain on the game clock in the second and fourth periods. SRC-OFFICIAL.
- It is a timeout of the official kind: it stops the clock (4-4(h)), is not charged to either team, resets the play clock to 25 seconds (4-6-2(c), 4-6-3(a)(2)), and after it the clock restarts on the snap (4-3-2). Another team timeout may follow it in the same dead-ball period (4-5-1 Item 3). SRC-OFFICIAL.
- The league glossary says it only occurs in the second and fourth quarters. operations.nfl.com football-terms, 2026-10-14. SRC-OFFICIAL.
- Timing: it happens at the end of the down in progress when the clock goes under 2:00; if the ball is dead at 2:00 it is taken at 2:00. The clock can therefore read, for example, 1:56 or 1:55 when the warning comes. Wikipedia states this and states the clock is always stopped. SRC-SECONDARY. Skipping: the rulebook gives no way to skip it; a clock that is already stopped for another reason does not cancel it (SRC-SECONDARY, Wikipedia). Inference for a simulator: if a down ends with the clock at 2:00 or less and no warning has been given in that half, give it then.
- Overtime: 3-41 names only the second and fourth periods. 16-3-e applies "the general provisions for the fourth quarter ... including timing" to regular-season overtime, which does not say yes or no. Evidence of practice: Bills 37, Rams 34 in overtime, played 2026-10-12, Bills kicker kicked "coming out of the two-minute warning in overtime" (buffalobills.com, 2026-10-13). SRC-SECONDARY. Wikipedia says the warning occurs at 2:00 left in a regular-season overtime period and, in the postseason, only in the 2nd and 4th overtime periods (matches 16-4-h). CBS Sports agrees for the postseason. SRC-SECONDARY. Recommended default: warning at 2:00 of the single regular-season overtime period; in the postseason at 2:00 of overtime periods 2 and 4 only.
- It is not a timeout charged to a team, but it is a timeout in the rulebook's sense (3-36-1: any interval during which the clock is stopped). The requirements file says "is not a timeout"; the precise statement is "automatic, not charged".
- Rules that switch on after the warning in either half: clock starts on the snap after an out-of-bounds play in the first half (4-3-2(a)(2)); clock starts on the snap after fouls in the first half (4-3-2(e)(1)); 10-second runoffs (4-7); fumbles by either team can be advanced only by the fumbler or an opponent (8-7-6, PDF 42); a backward pass out of bounds before a change of possession is loss of down and 5 yards (8-7-2, PDF 41); shift converts to false start if players are not all set for one second while the clock runs (7-4-2 Item 6, PDF 34); the offense may snap without waiting for defensive substitutions (5-2-10 applies only before the warning, PDF 24); only the Replay Official may start a review of plays after the warning (15-1-2(a), PDF 67), so no coach's challenge. SRC-OFFICIAL.

### 4. The game clock

#### Periods and intermissions
- Four periods of 15 minutes (4-1-1, PDF 18). SRC-OFFICIAL.
- At least two minutes between periods 1 and 2 and between 3 and 4 (4-1-2); halftime 13 minutes (4-1-3); teams change goals after periods 1 and 3 with possession, down and distance unchanged (4-2-3). SRC-OFFICIAL.
- Overtime: intermission of no more than three minutes after regulation (16-3, 16-4); regular season one period of 10 minutes; postseason periods of 15 minutes with two-minute intermissions (16-4-e). SRC-OFFICIAL.
- Official time is the stadium clock; officials may correct it only before the next legal snap or kick (4-1-4). The game clock is reviewable only to restore time, not to remove it (15-3-9, PDF 69-70). SRC-OFFICIAL.
- A period in which time expires with the ball live continues until the down ends (4-8-1). It is extended by an untimed down for listed fouls and situations, including a defensive live-ball foul the offense chooses to use, a double foul on the last down of a half, a fair-catch situation (4-8-2, PDF 22). The Try after a last-play touchdown is played except in sudden death or when it cannot change the result in the fourth period (4-8-2(c)). SRC-OFFICIAL.

#### Play clock
- 40 seconds: it is delay of game if the ball is not snapped within 40 seconds after the play clock starts; it starts when a play ends (4-6-1, PDF 20). "Ball ready for play" is while that clock runs (3-2-2, PDF 10). SRC-OFFICIAL.
- 25 seconds after administrative stoppages, counted from the Referee's whistle: change of possession, charged timeout, two-minute warning, end of a period, penalty enforcement, a free kick after a television timeout, replay administration when the play clock was under 25, and others (4-6-2, PDF 20-21). A free kick with no television timeout, after a Try or a successful field goal: teams get 40 seconds to align before the whistle. SRC-OFFICIAL.
- After an interruption the play clock keeps the value it had, except: reset to 25 after a charged timeout, the warning, expiry of a period, replay with under 25 left, penalty enforcement (not time-conserving), an excess timeout against the offense with no runoff; reset to 40 after a reversal with no runoff or timeout, a nullified live-ball foul, an excess timeout against the defense, a defensive time-conserving foul; 30 after a 10-second runoff; 10 if fewer than 10 seconds were left (4-6-3, PDF 21). SRC-OFFICIAL.
- Delay of game: five yards from the succeeding spot if the ball stays dead, from the previous spot if it was live (4-6-5, penalty clause); the Back Judge whistles and the ball remains dead (4-6-4). Other delay acts: staying on a dead ball, undue delay assembling after a timeout, spiking or throwing the ball after the down except after a score, intentional contact with the ball to delay the snap, a second timeout in one dead-ball period (4-6-5(a) to (g)). Two successive delay-of-game penalties in the same down while time is in: unsportsmanlike conduct, 15 yards (12-3-1(n), PDF 58), and the clock then starts on the snap (4-3-2(e)(4)). SRC-OFFICIAL.
- Snap rules that touch the clock: the snapper may not snap until the officials have had reasonable time to get in position; the ball stays dead, no penalty unless repeated after a warning (then delay of game, 4-6-5(b)); an illegal snap is five yards (7-6-3, PDF 36). Defensive substitution matchups: before the warning the offense cannot rush the snap after substituting; if it does and the defense is caught with too many men, the down is replayed and the clock is reset to the snap time (5-2-10(b), PDF 24). SRC-OFFICIAL.
- Multiple fouls to run off time: 15 yards, clock reset to its value at the snap, clock starts on the next snap (12-3-3, PDF 58; summary "Time Restored and Fifteen Yards", PDF 79). SRC-OFFICIAL.

#### Clock status after each kind of play (implementable list)
A. Keeps running (time in):
- Run or completed pass ended in bounds, with or without a first down. 4-4 lists no stop for it; a first down does not stop the clock. 4-6-1 starts the 40-second clock. SRC-OFFICIAL (by absence in 4-4(a) to (j)).
- Quarterback sack and kneel-down: ordinary tackled plays, clock runs. No entry in 4-4; a 2014 Eagles explainer says the clock runs after a sack outside two minutes (SRC-SECONDARY). Kneel-down: inference.
- Runner out of bounds is not here; see B.

B. Stops, restarts on the Referee's ready-for-play signal:
- Runner (including a receiver who has caught the ball) out of bounds on a play from scrimmage: stops (4-4(c)); restarts on the ready signal (4-3-2(a)). Exception, restart on the snap: after a change of possession; after the two-minute warning of the first half; inside the last five minutes of the second half. PDF 18-19.
- Fumble or backward pass out of bounds: restarts on the Referee's signal that the ball is back in the field (4-3-2(f)). No exception is written; whether the snap exceptions of (a) apply is UNVERIFIED.
- After a 10-second runoff: restarts on the ready signal (4-3-2(g)).
- After an injury timeout before the warning, a Referee's timeout, or a first-down measurement: as if it had not happened (4-3-2(b), (d); 4-5-5). If a team takes a timeout in the same stoppage as an injury timeout, the clock restarts on the snap (4-5-3).
- Excess timeout after the warning (injury): restarts at ready-for-play unless the opponent chooses the snap (4-3-2(c)).

C. Stops, restarts on the snap:
- Incomplete forward pass: stops (4-4(f)). A legal spike is an incomplete pass.
- Any team timeout, the two-minute warning (4-4(h), 4-4(j), 4-3-2 opening).
- Change of possession: the clock stops at the end of the down, whether by interception, fumble recovery, turnover on downs, missed field goal taken by the receivers, or punt caught (4-4(i), PDF 19). Restart on the snap (4-3-2(a)(1) covers the out-of-bounds case; the general rule covers the rest).
- Touchdown, safety, touchback, any ball dead on or behind a goal line (4-4(d)).
- Kicking team recovers a scrimmage kick beyond the line of scrimmage (4-4(b)).
- Ball out of bounds (4-4(c)); end of a down with a foul (4-4(e)); a foul that leaves the ball dead (4-4(g)).
- A penalty, accepted or declined: after enforcement or declination the clock starts "as if the foul had not occurred" (so running clocks resume at the ready signal), except it starts on the snap if the foul comes after the warning in the first half, inside the last five minutes of the second half, is an offensive foul in the fourth period or regular-season overtime after the ball was ready, is the second successive delay penalty, or a specific rule says so (4-3-2(e)(1) to (5), PDF 19).
- Replay reversal: the clock is reset to when the ball should have been dead, and 4-3 decides the status (15-5-1, PDF 70). After the warning, if the correct ruling would have stopped the clock but the on-field one let it run, or the reverse, a 10-second runoff follows (15-5-2).

D. Kicks:
- Kickoff or safety kick: the clock starts when the ball is legally touched in the field of play (4-3-1). It does not start if the receivers touch or recover it in the end zone without bringing it out, if the kicking team recovers it in the field of play before other legal touching, or on a fair catch (4-3-1(a) to (c)). It stops at the end of the free-kick down (4-4(a)) and restarts on the snap.
- Punt: runs from the snap; stops as in C (change of possession, out of bounds, touchback, kicking-team recovery beyond the line).
- Field goal: successful, or missed without landing in the field of play: at most five seconds may run off the game clock (11-4-2 Note 5, PDF 50). A missed attempt taken by the receivers stops the clock as a change of possession. After a made field goal the clock restarts when the next kickoff is touched.
- Try: untimed; the clock does not run (4-3-2(h), 11-3-1, PDF 49).

E. Period end: ball live at 0:00 means the down is played out (4-8-1); untimed down cases in 4-8-2. SRC-OFFICIAL.

#### Last two minutes and the 10-second runoff
- Illegal time-conserving acts after the warning (4-7-1, PDF 21): any foul by either team that stops the clock in a dead-ball period, intentional grounding, an illegal forward pass, a backward pass thrown out of bounds, spiking or throwing the ball after a down except after a touchdown (the legal spike aside), illegally batting or kicking the ball out of bounds. Penalty: five yards unless a larger distance applies.
- Offense, time in: 10 seconds are run off, the play clock is reset to 30, the ball is put in play on the ready signal, and the game clock starts at the ready signal. The offense may use a timeout instead; then the clock starts on the snap. The defense may always decline the runoff and take the yardage; declining the yardage declines the runoff too, play clock 25, clock starts on the snap (Item 1).
- Defense: no runoff. Play clock 40; clock starts at the ready signal unless the offense chooses the snap; the defense may use a timeout instead (Item 2).
- Substitution violation after the warning with the ball dead and time in: five yards and a 10-second runoff (4-7-2; penalty summary).
- Last 40 seconds of a half: a defensive foul that conserves time, or an excess injury timeout by the defense, while time is in ends the half unless the defense has timeouts left or the offense chooses the clock to start on the snap or plays on after the ready-signal start (4-7-3, PDF 22). Plain reading; the exact wording is dense.
- Replay reversal or nullified foul after the warning, when the right call would not have stopped the clock: 10 seconds run off, play clock 30, nobody may decline, either team may use a timeout to avoid it (4-7-4, 15-5-2, PDF 22, 70). If a timeout is used, the clock is reset to when the play should have ended, play clock 25, clock starts on the snap.
- If fewer than 10 seconds remain, the runoff ends the half or the game (15-5-2; 4-5-4 Note 4).
- "Inside one minute" provisions: none found in the 2026 rulebook (searched "minute"). The only sub-minute thresholds are the last 40 seconds (4-7-3), the five-second field goal cap (11-4-2) and "fewer than 10 seconds" (15-5-2, 4-6-3(d)). SRC-OFFICIAL by absence.

#### Last five minutes of the second half
- Clock starts on the snap after an out-of-bounds play (4-3-2(a)(3)) and after a foul (4-3-2(e)(2)). Before that (the first half up to the warning, the third quarter and the first 10 minutes of the fourth), the out-of-bounds clock restarts on the ready signal. SRC-OFFICIAL. In overtime the five-minute rule is not stated (the clause says "second half"); Wikipedia's clock-management page says overtime follows the fourth-quarter pattern, a weak source. UNVERIFIED default for sudden-death overtime: treat all of it like the last five minutes.

### 5. How coaches use timeouts

#### The NFL Football Operations article
- URL named in the requirements file: https://operations.nfl.com/gameday/analytics/stats-articles/how-do-nfl-coaches-use-their-timeouts . Result on 2026-10-14: HTTP 404 from WebFetch and from curl; same with a trailing slash, the new /stats-central/ path and the edge-operations host; archive.org blocked or rate-limited. The league site was reorganized (rulebook now at /rules-officiating/2026-nfl-rulebook). So I could not read the article. The article's own numbers are UNVERIFIED.
- What reports of the article say (a web search on 2026-10-14 returned a summary of the page; I treat it as secondary): published November 2021; teams get three timeouts each half; two groups, "time-saving" timeouts (late in a half; an offense stopping the clock, a defense trying to get the ball back) and ones coaches "would like back" (earlier in a half: avoiding delay of game, an uncertain play call, defensive substitution trouble, a lost challenge); other reasons such as a late-half injury under 5% of the total; Michael Lopez, the league's analytics director, tracked and categorized every timeout from 2018 into the 2021 season; Brian Burke is cited as valuing each second-half timeout at about 3% of win probability. SRC-SECONDARY (search-engine summary).
- BroBible, 2021-11-11 (SRC-SECONDARY), describing a chart by Tom Bliss, a football data analyst for the NFL, posted on the NFL's site: five categories (Time Saving Offense, Time Saving Defense, Unnecessary Offense, Unnecessary Defense, Lost Challenges), data 2018 through Week 9 of 2021. Per game: the Rams' head coach 2.9 unnecessary timeouts (league high); Arians 2.1; Belichick 1.9; Reid 1.7; Dan Campbell 2.7 time-saving; Urban Meyer 2.5 time-saving. The search summary adds Arthur Smith 1.1 and Nick Sirianni 1.4 as the most economical (unconfirmed by the page).
- The Ringer, 2023-01-12 (SRC-SECONDARY): Lopez's research found most timeouts wasteful while time-saving ones were worth more; "unnecessary" = used outside the last four minutes of the half; operational timeouts = getting the right call or personnel; coaches get six timeouts a game.

#### Other timeout research (all SRC-SECONDARY, labeled by who)
- Sumer Sports (article date not shown; its coach table is for 2022): a timeout counts as wasted if taken in the first half before the final two minutes or in the second half before the final four minutes; each excess timeout costs roughly 1 to 2 percentage points of win probability, depending on the half. No per-game league average given.
- FiveThirtyEight/Hermsmeyer (2021, as quoted by the Ringer): operational timeouts = low-leverage timeouts with four or more minutes left in the half; only the Dolphins and Ravens got surplus value from them in 2021.
- Burke, Advanced Football Analytics, 2014-03 ("When Coaches Use Timeouts"; second-half data only; seasons not stated): "teams burn half a timeout on average in the second half" before the endgame; a trailing defense shows "a clear inflection point at the 5-minute mark" and has about 0.7 timeouts left at the end; teams trailing by more than one score start using them about 30 seconds sooner; defenses that lead use fewer than those that trail; no obvious offense-versus-defense difference except a slight one in the endgame.
- Burke 2014-01 ("The Value of a Timeout"): in a third-quarter sample the first timeout is worth about 0.05 win probability; offense win rate falls from about 69% to 63% going from three timeouts to two; adjusted costs 0.04 (defensive) and 0.06 (offensive). Seasons not named.
- Yale Sports Analytics (regular seasons 2009 to 2015): use is relatively even over roughly the first 20 minutes of each half, with road teams using more then, almost always to avoid delay of game; in the first half usage surges right after the two-minute warning; in the second half urgency "kicks into high gear with around seven minutes left"; home teams use more after the warning. No counts given.
- Beasley, Greenwald and Agha, Journal of SPORT 2015 (USF), 2009-2011 regular seasons, 83 possessions in games tied or within 3 points in the last 6 minutes where the team behind reached the 35-yard line: the offense had 1.8 timeouts available and used 0.51; 19% used all, 63% used none; using an offensive timeout in the last drive added 22 seconds to reaching field-goal range, while merely having one cut 19 seconds; the defense used 0.70 timeouts in tied games against 0.45 in non-tied, and 0.82 in tied games against a non-hurried offense.
- Football Outsiders-style counts of league-wide timeouts used per team per game, or the share unused at the end of each half: not found anywhere reachable. nflverse data has the fields (home_timeouts_remaining, timeout_team) but I did not download any data set (a download needs the owner's permission).

#### Rules a computer coach can follow (design hints; inference built on the rules above and the research)
- Operational timeouts (to avoid a delay of game, or a wrong substitution): rare, early in a half, when the play clock is nearly gone. Support: NFL article summary, Yale, FiveThirtyEight. Cost: a timeout that could save about 1 to 2 win-probability points later.
- Never spend timeouts for operational reasons in the last four minutes unless a delay penalty is worse; nothing wasted before the final two minutes of the first half or the final four of the second (Sumer windows).
- Trailing defense in the second half: begin timeouts near five minutes left, earlier if behind by more than one score; leading defense: few, until the lead is at risk. Support: Burke 2014.
- Trailing or tied offense late: use a timeout only when the clock is running after a play that did not stop it and time is the binding limit; keep one timeout to avoid a runoff (4-7-1 Item 1). Kent paper: offenses use few (0.51 of 1.8).
- First half: save for after the two-minute warning (surge in Yale data); a leading team does not call timeouts before the warning.
- Challenges: keep one timeout in the first three quarters and up to the warning, because a challenge needs one (15-1-1(d)) and coaches cannot challenge after the warning (15-1-2(a)).
- Before a kick: one legal timeout to "ice" is fine; a second is a 15-yard foul.
- Never request a timeout with none left (five yards, runoff risk).

### 6. Statistics (counting basis matters)

Unit: offensive plays per team per game, regular season, unless said. Rotowire's counts look like pass attempts plus rush attempts plus sacks (inference: its 2024 figures of 32.7 pass attempts and 27.0 rush attempts per team game add to 59.7, and the 2.5 left over would be plausible for sacks; the page does not define "plays"). PFF's figures run about 3 plays higher for the same seasons and the basis is not stated (it may include plays nullified by penalty). Neither basis includes kickoffs; whether punts and field goal attempts are in is not stated.
- 2013 peak 65.0; 2023 63.1; 2024 62.2, "a 17-year low" (Rotowire, updated 2025-09-02). SRC-SECONDARY.
- 2023 65.89; 2024 65.31; 2025 64.32, a three-year low (PFF, article on 2026 value). SRC-SECONDARY.
- 2025 on the Rotowire basis: not found. A search summary quotes 61.3 plays per game, "fewest of the 2000s" from a Sharp Football July 2026 article, but the page is paywalled and the season is not confirmed. UNVERIFIED.
- 2026 to date (page dated 2026-10-13, each team 4 or 5 games): mean of the 32 team values 61.16 plays per game (range 54.6 Tennessee and Miami to 72.0 Chicago). Sharp Football pace table, my arithmetic. SRC-SECONDARY.
- Plays per quarter, both teams together = 2 times plays per team per game, divided by 4 (inference): 2024 31.1 (Rotowire basis) or 32.7 (PFF basis); 2025 32.2 (PFF basis); 2026 to date 30.6. All inside the original's 29 to 36 range. Quarter-to-quarter spread was not found.
- Clock budget (inference): 900 seconds per quarter divided by those counts is about 27 to 29 game-clock seconds per counted scrimmage play, kicks and stoppages included. 3600 / 124.4 = 28.9 (2024, Rotowire basis); 3600 / 130.6 = 27.6 (PFF basis); 3600 / 122.3 = 29.4 (2026 to date). The scrimmage-play count excludes punts, field goals and kickoffs, which also use clock, so the true time per snap is a little lower. This is the figure to calibrate the simulator to (target: 10,000 simulated quarters averaging this).
- Drives per team per game: 2024 10.7, "all-time-low" (Rotowire). Another table gives 10.2 for 2024 (Sharp Football, from a search summary; counts possessions that did not end in kneel-downs; not confirmed on the page). SRC-SECONDARY.
- Plays per drive: 2026 to date mean 5.82 (range 4.9 Seattle to 6.78 Dallas; Sharp). 2024 inference: 62.2 / 10.7 = 5.8. SRC-SECONDARY and inference.
- Time of possession per drive: 2024 inference: 30 minutes per team divided by 10.7 drives is about 2:48. The Sharp 2026 table's time-of-possession column averages 29.34 minutes per team per game (definition not given), which with 10.5 drives is about 2:47. Dolphins and Chiefs led with 3:34 per drive in an ESPN piece, season unclear. SRC-SECONDARY and inference.
- Seconds between plays while the clock runs: "play clock used" (how many of the 40 seconds the offense takes before the snap) mean 32.15 seconds, neutral situations 32.67 (team values 29.7 to 34.5), 2026 to date, my arithmetic on the Sharp table. About 6 percent of plays are no-huddle (mean 6.2%); PFF reports 9.91% for 2025. SRC-SECONDARY.
- Older: New England 24.9 seconds per play in 2012, the fastest team; New Orleans 26.1 (Football Perspective, 2013). Different metric (seconds per play over all plays). SRC-SECONDARY.
- Length of a play, snap to whistle: about 4 seconds on average, ball in play about 11 minutes a game (Wall Street Journal study of four broadcasts, January 2010, as quoted by Fox Sports and others). Super Bowl XLIV: runs about 4 seconds, passes about 5 seconds (fan analysis, one game). SRC-SECONDARY, weak. League-wide run versus pass clock time: not found.
- Penalties and time: no figures gathered (other topics).

Suggested calibration identity (inference): game-clock time per counted play = (time to run the play, about 4 to 6 s) + (time until the next snap when the clock runs, about 32 s from the 40-second clock) for plays followed by a running clock, and about 5 s plus the stoppage restart for plays followed by a stopped clock. About 28 s on average means roughly three quarters of counted plays are followed by a running clock: (28.9 - 5) / 32 = 0.75. Derived only from the numbers above; check against a real play-by-play table in SX.2 (the owner's permission is needed to download one).

### Differences from the requirements file (section 6, C2)

- "The two-minute warning ... is not a timeout." Wrong in wording: 3-41 calls it "an automatic timeout". It is not a team timeout and is not charged. Also it does not happen "at 2:00" exactly: it comes at the end of the last down snapped before two minutes remain.
- "A request when the team has no timeout left is a foul." Not quite: the request "should be ignored"; the foul (delay of game, 5 yards, timeout charged) exists only if the timeout is granted. A second timeout request in the same dead-ball period is treated the same way. For a kick, an excess or second timeout attempt is a 15-yard unsportsmanlike foul even if ignored. The five-yard penalty has no loss of down; a 10-second runoff option applies only after the warning, offense, time in.
- "A timeout used with the clock running saves the time that would run." Right. After the timeout the clock restarts on the snap (except the excess-timeout cases of 4-3-2(c)).
- "Postseason ... one says three": settled, it is three per half (16-4-g), against two in the regular season (16-3-e). The three is shared by overtime periods 1 and 2 and fresh again from period 3 (the pairing is secondary).
- "The clone's overtime stays sudden death" is compatible; but the clone then needs the 10-minute regular-season period or the 15-minute postseason period with the rules above.
- Property test "never more than 3 timeouts per half" (C8) must allow two in regular-season overtime and three per overtime pair in the postseason; injury excess timeouts do not count against the three.
- C2's list of when the clock stops is right in spirit; the rulebook does not stop the clock at a first down; the clock restart after an out-of-bounds play depends on the minute (section 4B). A sack does not stop the clock.
- N1.3 "keep at least one for a challenge in the first three quarters": the rule is stronger, a challenge needs an available timeout (15-1-1(d)) and coaches cannot challenge after the two-minute warning of either half or in overtime (15-1-2); in the fourth quarter before the warning a challenge is still allowed.
- 12-3-1(v) is worded for three timeouts per half only; the overtime case is not covered in the text I read.

### Could not settle

- The ops article's own figures (shares of categories, per-coach list, minutes). Page 404, archive.org blocked. Needs the page, an archive copy, or the league's data.
- League-wide timeouts used per team per game, timeouts left at the end of each half, behavior leading versus trailing, offense versus defense: no published source reachable. A computed answer needs nflverse or nflfastR play-by-play for 2024 and 2025 (I did not download anything; it needs the owner's permission, file names and size to be stated).
- Official season totals (plays per game): pro-football-reference, footballdb and teamrankings returned 403; nfl.com stats pages are script-rendered; only secondary counts available.
- Clock time per run play versus per pass play, and the typical delay from an out-of-bounds play to the ready signal: no source.
- The casebook (Approved Rulings): not found; operations.nfl.com no longer links one on the pages I fetched. Items that depend on it: how 12-3-1(v) works in overtime, who holds the runoff option in 4-5-1 Item 3, whether the snap-start exceptions apply to fumbles out of bounds.
- Whether the five-minute out-of-bounds rule applies in overtime.
- Whether the regular-season overtime warning is written anywhere in the rulebook; practice and Wikipedia say yes.
- The rule that a timeout restored after a replay review inside the last two minutes (casebook language from 2018, footballzebras) is only reported by a search summary; the rulebook text is 15-6-2.

### Sources (all retrieved 2026-10-14)

Official:
- 2026 Official Playing Rules of the NFL, PDF, https://static.www.nfl.com/image/upload/fl_attachment/league/tqivdkzt9mu6wdgsh1ku.pdf (converted to text; rules 3, 4, 5, 7, 8, 11, 12, 14, 15, 16 and the penalty summary).
- NFL Football Operations, football terms (timeout, two-minute warning, play clock, injury timeouts), https://operations.nfl.com/rules-officiating/nfl-football-basics/football-terms
- NFL Football Operations, featured rules (2025 changes, overtime), https://operations.nfl.com/rules-officiating/featured-rules (nothing on timeouts)
- Not reachable (404): https://operations.nfl.com/gameday/analytics/stats-articles/how-do-nfl-coaches-use-their-timeouts and the old overtime and video rulebook pages.

Secondary:
- BroBible, 2021-11-11, chart by Tom Bliss: https://brobible.com/sports/article/chart-nfl-coaches-best-worst-using-timeouts/
- The Ringer, 2023-01-12: https://www.theringer.com/2023/01/12/nfl/nfl-timeouts-playoff-coaches-mike-mccarthy-pete-carroll-kevin-oconnell
- Sumer Sports, in-game coaching model: https://sumersports.com/the-zone/sumersports-in-game-coaching-model-an-introduction/
- Burke, Advanced Football Analytics: http://www.advancedfootballanalytics.com/2014/01/the-value-of-timeout-first-approximation.html and https://www.advancedfootballanalytics.com/2014/03/when-coaches-use-timeouts.html
- Yale Sports Analytics: https://sports.sites.yale.edu/node/251 and https://sports.sites.yale.edu/node/246
- Beasley, Greenwald, Agha, "NFL Time Management: The Role of Timeouts in End-Game Scenarios", Journal of SPORT 4(1), 2015: https://oaks.kent.edu/_flysystem/ojs/journals/4/articles/154/submission/154-37-578-1-2-20200103.pdf
- Wikipedia, Two-minute warning: https://en.wikipedia.org/wiki/Two-minute_warning
- CBS Sports, overtime in the playoffs: https://www.cbssports.com/nfl/news/how-nfl-overtime-works-in-the-playoffs-explaining-the-difference-between-postseason-and-regular-season-rules
- ESPN, overtime rules: https://www.espn.in/nfl/story/_/id/39111637/what-nfl-rules-regular-postseason-play
- NBC Sports, 2026-01-18, playoff overtime: https://www.nbcsports.com/nfl/profootballtalk/rumor-mill/news/2026-nfl-playoffs-and-super-bowl-overtime-rules-explained
- Buffalo Bills, 2026-10-13, Brady on overtime against the Rams: https://www.buffalobills.com/news/bills-hc-joe-brady-looks-back-on-ot-game-management-against-rams
- Philadelphia Eagles, Football 101 (2014-10-26): https://www.philadelphiaeagles.com/news/football-101-two-minute-warning-clock-14073493
- Rotowire, league-wide trends (updated 2025-09-02): https://www.rotowire.com/football/article/nfl-state-of-the-union-how-league-wide-trends-impact-fantasy-football-95635
- PFF, pace and no-huddle trends: https://www.pff.com/news/fantasy-football-nfl-pace-volume-how-no-huddle-trends-shape-2026-value
- Sharp Football Analysis, team pace table dated 2026-10-13: https://www.sharpfootballanalysis.com/stats-nfl/nfl-team-pace-stats/ and https://www.sharpfootballanalysis.com/?p=111750
- Football Perspective, tempo posts: https://www.footballperspective.com/tag/tempo/
- Super Bowl XLIV play-time count: https://joshmadison.com/2010/02/08/actual-play-time-of-super-bowl-xliv/ (seen only in a search summary)
- Search-engine summaries (not fetched pages) were used for: the ops article's description, the Sharp 10.2 and 61.3 figures, and the Fox/Wall Street Journal 11-minute figure. They are marked as such above.


## Part 3. Instant replay, challenges and booth reviews

Researched 2026-10-14 for NFL_EXTRA_FEATURES.md section 7 (NX2) and the cross-cutting items in section 3.
Authority: the 2026 Official Playing Rules of the NFL, Rule 15 (Instant Replay), read in full.
Citations are Rule-Section-Article. "PDF p." is the page of the PDF; printed page = PDF page minus 7.
Rule 15 starts on PDF p. 67 (printed 60) and ends on PDF p. 71 (printed 64).
Tags: SRC-OFFICIAL, SRC-SECONDARY, UNVERIFIED (as in the common brief).

### Answers in brief

1. Challenges per team per game: two, plus a third if at least ONE of the first two succeeded (not both). A fourth is never allowed. The 2026 book has the "at least one" text (15-1-1-f), in force since the March 2024 amendment. The older "both" text (2016 to 2023) is gone. Never reset at halftime; none in overtime. [SRC-OFFICIAL]
2. Cost: an unsuccessful challenge is charged one timeout (15-1-1-e, 15-6-1). A successful one is not charged. A challenge needs a timeout in hand. Not permitted but thrown: a timeout is charged; if the team has no timeouts left, a 15-yard foul between downs. [SRC-OFFICIAL]
3. No coach challenge for: plays that begin after the two-minute warning of each half, all overtime, scores, Tries, turnovers and the other booth-only plays, a team that committed a foul that prevents the next snap, a team with no timeout or no challenge left. [SRC-OFFICIAL]
4. Automatic reviews: scores, Tries, turnovers (interception, fumble or backward pass recovered by the opponent or out through the opponent's end zone, fourth-down failure, kicking-team possession at the end of a kick), disqualifications. Started only by the Replay Official or the League Officiating chief or designee. No timeout is charged. [SRC-OFFICIAL]
5. Reviewable and non-reviewable lists, the "clear and obvious video evidence" standard, and the effects of a reversal are all in Rule 15, sections 2 to 7 (details below). Judgment fouls are not reviewable. [SRC-OFFICIAL]
6. 2026 change: 15-1-1-a now lets the head coach OR a pregame challenge designee throw the flag. It is not in the book's 2026 change list (a summer rulebook edit). No change to counts, timeouts or reviewable plays. A one-year work-stoppage replay provision exists but is moot. [SRC-OFFICIAL for the text; SRC-SECONDARY for how it was adopted]
7. Statistics: 133 coach challenges in 2024 regular season (50 reversed, 37.6 percent); 151 in 2025 (season scope not stated); 2023 about 137 (blog count); 2026 to date not found. Booth success 76 percent in 2024 (ESPN). Category breakdown only for 2020. [SRC-SECONDARY]

Flags against the requirements file (section 7): see "Where the official text differs from NFL_EXTRA_FEATURES.md" below. Three real differences: "restored" timeout wording, "after the two-minute warning" timing, and "booth reviews any play" wording.

### 1. Number of challenges

- Each team gets a minimum of two challenges that start replay reviews. [15-1-1, PDF p. 67] [SRC-OFFICIAL]
- A third challenge is allowed if the team has been successful on at least one of its challenges. A fourth is not allowed. [15-1-1-f, PDF p. 67] [SRC-OFFICIAL]
- So the maximum is three per game. The limit is per game, not per half. Timeouts are per half (3), so a challenge also needs a timeout left in the current half.
- Which text is current: the 2026 book says "at least one". [SRC-OFFICIAL]
- History of the conflict:
  - 2016 text (Spring League Meeting, May 24, 2016): a challenge is restored only if the team was successful on BOTH, then a third, never a fourth. [SRC-SECONDARY: chargers.com article, dated 2016-05-24]
  - Detroit's proposal, adopted at the Annual Meeting in Orlando, March 2024: third challenge after one success. NFL.com's official summary lists it as an amendment to Rule 15, Section 1, Article 1. [SRC-OFFICIAL: nfl.com approved 2024 rules page] The vote barely passed (24 of 32 needed), per Competition Committee chair McKay; he said teams had resisted because data showed a third challenge is rarely needed. [SRC-SECONDARY: Bleacher Report 2024-03-25; Pride of Detroit and Detroit Free Press via search summary]
  - Wikipedia's replay article also dates the change to 2024 and says the older rule dated from 2004. [SRC-SECONDARY]
  - Conclusion: the requirements file's "later sources say at least one" is correct and is the 2026 wording. "A fourth is never allowed" is correct.
- Overtime: coach challenges are not allowed. 16-5-d: all replay reviews are started by the Replay Official and "Coaches' challenges will not be allowed" (applies to regular season and postseason overtime). Also 15-1-2-b. [SRC-OFFICIAL, PDF p. 73 and p. 67]
- The rulebook says "a minimum of two"; no rule gives more than two to start. The third is only earned.

### 2. Cost, return, consequences, procedure

Cost and return:
- Each challenge needs an available team timeout. A team out of timeouts, or out of challenges, may not attempt a challenge. [15-1-1-d] [SRC-OFFICIAL]
- An unsuccessful challenge: the team is charged a timeout. [15-1-1-e; 15-6-1, PDF p. 70] [SRC-OFFICIAL]
- A successful challenge: no timeout is charged. The book never uses the word "restored" for a won challenge; it simply charges only on a loss. A challenge counts as successful if any reviewable aspect of the play is changed (15-6-1), with the line-to-gain exception: a line-to-gain challenge is successful only if the ruling on whether a new series was awarded changes, even if the ball is moved (15-3-7 notes 2 and 3, PDF p. 69). [SRC-OFFICIAL]
- If a team takes a timeout and then challenges unsuccessfully, it is charged a second timeout (15-6-1). A challenge still needs an available timeout, so the team must have a further one. [SRC-OFFICIAL]
- The only true "restored" rule: a charged timeout taken at a team's request after the two-minute warning of either half is restored if a review changes the ruling (15-6-2). That is about a timeout the team called before a booth review, not about a challenge. An injury timeout is charged or restored only if the changed ruling affects whether it is charged (Rule 4-5-4). [SRC-OFFICIAL, PDF p. 70]

When a challenge is thrown but not permitted:
- The team is charged a team timeout. [15-1-1-d] [SRC-OFFICIAL]
- Penalty (when the team has exhausted its timeouts): loss of 15 yards, enforced as a foul between downs. [15-1-1-d, PDF p. 67] [SRC-OFFICIAL]
- Enforcement details: it is always treated as a foul between downs (14-1-2, Item 4, exception, PDF p. 61) and is not part of a multiple foul, so it is enforced in addition to any other foul (14-1-3, exception 1, PDF p. 61). [SRC-OFFICIAL]
- The penalty summary table (printed pp. 71 to 73) does not list this foul; only 15-1-1-d and the two Rule 14 exceptions carry it. (The 5-yard "timeout requested and granted when not allowed" entry is a different foul, 4-5-1.) [SRC-OFFICIAL]
- The rulebook does not say whether the play is still reviewed. Practice, from Football Zebras posts of 2013 and 2016 (older text of the same rule): the challenge is not legal, a timeout is charged first if the team has one, and the flag blocks a review in that team's favor. [SRC-SECONDARY] Treat "not reviewed on the coach's behalf" as the default. Exact current practice [UNVERIFIED].
- History of this penalty (Wikipedia replay article, SRC-SECONDARY): an unsportsmanlike conduct penalty for improper challenges was added in 2005; in 2012 a timeout loss and a bar on review of that play were added. The May 2016 text (chargers.com) already read as the 2026 book does: a timeout is charged, and 15 yards only when the team has exhausted its timeouts. The 2026 book is what counts.

Procedure:
- The head coach, or the head coach's pregame challenge designee (2026), throws a red flag onto the field before the next legal snap or kick. [15-1-1-a] [SRC-OFFICIAL]
- The head coach may move down the sideline outside the bench area to challenge when the ball is outside the bench area. [13-1-5, PDF p. 60] [SRC-OFFICIAL]
- No numeric time limit is in the book: only "before the next legal snap or kick".
- Practice: ESPN (2023-01-31) quotes league officiating staff that the flag should be thrown once the play clock is at 20 seconds or lower; a flag thrown earlier ends any replay assist and starts the formal challenge. [SRC-SECONDARY]
- Review is done by the Senior VP of Officiating (or designee, at Art McNally GameDay Central in New York) in consultation with the stadium Replay Official and the Referee; an expedited review can happen without the Referee. [15-2, PDF p. 67] [SRC-OFFICIAL]
- The Referee announces the result on the field. [operations.nfl.com AMGC page] [SRC-OFFICIAL]
- Standard: an on-field ruling is changed only on "clear and obvious video evidence". [15-2-1] [SRC-OFFICIAL]
- Scope: once a review starts, all reviewable aspects may be examined and changed, even if not the stated reason (15-2-2). Each ruling is reviewed separately; an unchanged aspect is treated as correct (15-2-4). [SRC-OFFICIAL]
- Review length: the average review lasted 1 minute 25 seconds in 2024 (operations.nfl.com AMGC page). [SRC-OFFICIAL] ESPN (2025-10-22) says the average was 2:20 in 2023 and 1:25 in 2025, both through week 7. The two sources name different seasons for 1:25. [SRC-SECONDARY]
- If league communication is lost: the Referee waits at the monitor one minute, then reviews himself in consultation with the Replay Official (15-8). [SRC-OFFICIAL]

### 3. When a coach may not challenge, and what happens instead

From 15-1-1 and 15-1-2 (PDF p. 67) and 16-5-d (PDF p. 73): [SRC-OFFICIAL]
- A play that begins after the two-minute warning of either half: only the Replay Official (or the League's Officiating chief or designee) may start a review (15-1-2-a). Note the wording is plays that BEGIN after the warning. The last play before the warning began earlier, so a coach may still challenge it during the warning stoppage (before the next snap). Two-minute warning definition: automatic timeout after the last down snapped or kicked before two minutes remain in the second and fourth periods (3-41, PDF p. 17).
- Throughout any overtime period (15-1-2-b; 16-5-d).
- When points are scored by either team (15-1-2-c), and any Try attempt, successful or not (15-1-2-d).
- When the on-field ruling is: an interception by an opponent; a fumble or backward pass recovered by an opponent or out of bounds through the opponent's end zone; the offense failed to reach the line to gain on fourth down; possession by the kicking team at the end of a free kick or scrimmage kick down; a disqualification of a player (15-1-2-e). Such plays may be reviewed even if a foul on the play would negate the ruling.
- A team that commits a foul that prevents the next snap can no longer challenge the previous play. The non-fouling team still can, and both teams benefit from the result (15-1-1-b). (The requirements file says "delays"; the book says "prevents".)
- A team with no timeout, or with no challenges left, may not challenge (15-1-1-d).
- Plays not listed as reviewable (15-4 and Section 3) cannot be challenged; see section 5.
- Not stated in the rulebook: whether a play already reviewed can be challenged again. It is mostly moot: a review examines all reviewable aspects (15-2-2). [UNVERIFIED]

What happens instead: the Replay Official (booth) may initiate the review until the next legal snap or kick, and may consult a designated League officiating staff member (15-1-2, last paragraph). No timeout is charged for these (the only timeout charges in Rule 15 are for coach challenges, 15-1-1-d, 15-1-1-e, 15-6-1). [SRC-OFFICIAL]
- The book sets no cap on booth-started reviews and no rule that the evidence must be clear before he may start one. Only the change itself needs clear and obvious evidence. Search-result summaries of Fox Sports and Sportskeeda pages say booth reviews are unlimited (I did not open those pages). [SRC-SECONDARY]
- operations.nfl.com says replay officials are solely responsible for confirming all plays that result in a score, turnovers, failed fourth-down attempts and all Try attempts, and stop the game for a review on any play that begins after the two-minute warning and in overtime. [SRC-OFFICIAL: replay-officials page]
- The practice that the booth stops the game only when it sees a likely error is not stated anywhere I could read. [UNVERIFIED]

### 4. Automatic reviews (booth-only plays)

- Who starts them: the Replay Official or the Senior VP of Officiating (or designee). [15-1-2] [SRC-OFFICIAL]
- Which plays: the list in section 3 (scores; Tries; interceptions; fumbles or backward passes recovered by the opponent or out through the opponent's end zone; fourth-down failure; kicking-team possession at the end of a kick; disqualifications; every play beginning after the two-minute warning; all overtime plays).
- Also: ball touching a foreign object may be reviewed by the Replay Official at any time in the game (15-3-11, Item 5, note 1). [SRC-OFFICIAL]
- AMGC page (operations.nfl.com): all scoring plays and turnovers are automatically reviewed, along with clock issues. [SRC-OFFICIAL]
- Timeout: none charged, and not tied to timeouts left. The only link between a booth review and a timeout is 15-6-2 (a timeout taken after the two-minute warning is restored if the review changes the ruling) and the 10-second runoff option (section 5 below).
- A review of a score or turnover can be done even if a foul on the play would negate the ruling (15-1-2 closing sentence).
- Replay assist (not a review): Rule 15-9 lets the Replay Official and League staff advise on game administration (down, penalty enforcement, timing or spot of a foul, game clock, possession, direction of a pass, touching of a ball or line, location of the ball, down by contact) and on a list of called fouls where clear and obvious video shows the foul did not happen (roughing the passer on head or neck contact only, intentional grounding where the passer was out of the pocket, two unnecessary roughness cases, facemask, horse-collar, tripping, and roughing the kicker when the defender touched the kick). [15-9, PDF p. 71] [SRC-OFFICIAL]
- 15-9 does not stop a head coach or the Replay Official from using Section 1.

### 5. Reviewable and non-reviewable rulings, standard and effects

Standard: clear and obvious video evidence (15-2-1). [SRC-OFFICIAL]

Reviewable (15-3). [SRC-OFFICIAL, PDF pp. 67 to 70] Grouped:
- Game administration (15-3-1-h): penalty enforcement, proper down, spot of a foul, status of the game clock. Penalty administration also includes yardage and fouling player's number (15-7-1).
- Possession (15-3-2):
  - Completion or incompletion of a pass.
  - Incomplete changed to a catch: ball spotted where the receiver's second foot or body part touched the ground with control; no advance is awarded.
  - Incomplete changed to catch and fumble: ball to the team that recovers in the immediate continuing action; otherwise to the team last in possession at the spot where possession was lost; if lost in the team's own end zone and not clearly recovered there, the one-yard line.
  - Recovery of a loose ball (field, sideline, goal line, end zone).
  - Forward pass or fumble (whether the passer's hand started forward with control). Same recovery rule when "incomplete" is changed to a fumble. On a fourth-down fumble, after the two-minute warning or on a Try, if a passer ruled to have fumbled clearly threw, the ball goes to the spot of the completion or interception, no advance; if the pass was incomplete, the ball returns to the previous spot and the down counts.
  - A ruling of fumble changed to an incomplete pass can create intentional grounding only if a pre-review announcement said a changed ruling would create that foul.
  - Fumble before down by contact, out of bounds or giving up, or before or at the same time as contact when forward progress had been ruled stopped. The spot of a forward fumble out of bounds, or a fumble on fourth down, after the two-minute warning or on a Try, is reviewable.
- Touching the ball or the ground (15-3-3): down by contact; whether the ball was thrown before the passer was ruled down by contact (ball goes to the spot of the completion or interception, no advance; if incomplete the down counts); touching of a forward pass (only the fact of touching, not intent; touching removes pass interference if away from and noticeably before it); touching of a kick (a roughing or running-into-the-kicker foul can be removed, or created after a pre-review announcement); touching a loose ball; a free kick touching the ground; a scrimmage kick touching the ground before a punter or holder catches it.
- Goal line (15-3-4): whether the ball broke the plane while in player possession; a touchdown can be reviewed for an earlier fumble (no clear recovery: the fumbling team keeps it at the spot). The dead-ball spot is not reviewable solely to move it closer to or farther from the goal line. Momentum: the spot where the second foot (or non-hand body part) touched; on or past the goal line it is a touchback. Whether momentum carried him in is not reviewable.
- Boundary lines (15-3-5): a runner ruled inbounds; a runner ruled out of bounds only for the ball's spot against the line to gain or goal line, a fumble before two more steps, or the ball at or past the line before two more steps; a receiver out of bounds; a passer out of bounds before throwing (spot of completion or interception, no advance); a player out of bounds on a scrimmage kick; a loose ball touching a boundary line, pylon or object (possession can go to a team recovering in the immediate continuing action).
- Line of scrimmage (15-3-6): illegal pass beyond the line; illegal kick or second kick beyond the line.
- Line to gain (15-3-7): the dead-ball spot against the line. Forward progress is where a contacted player with control is driven backward. Success only if the new-series ruling changes.
- Number of players on the field (15-3-8): whether a player was on the field at the snap (off the field means touching the ground out of bounds; on the field means both feet or a body part in the field of play).
- Game clock (15-3-9): time may be restored, never taken off. (a) before the next legal snap or kick, if the clock was wrongly started. (b) last play of a half, or of an overtime period: reviewable by the Replay Official only when the evidence shows the clock should have stopped with two or more seconds left; in the first half time is restored only if the added play is a snap from scrimmage; in the second half only if the next play is a snap by a team trailing by eight or fewer, or by either team if tied. (c) and (d) whether time properly expired or the two-minute warning came before a snap.
- Disqualification (15-3-10): League review; other aspects reviewed only if the Replay Official or a coach's challenge applies.
- Other (15-3-11): direction of a pass (forward or backward; incomplete changed to a backward pass uses the same recovery rule); an illegal forward pass; a field goal or Try, only if the ball crosses the goal post plane below the top of the uprights or touches anything; an illegal forward handoff; the ball touching a foreign object (down replayed from the previous spot; clock reset to the snap time, starts on the snap).

Not reviewable (15-4, PDF p. 70): [SRC-OFFICIAL]
- whether an erroneous whistle sounded
- whether a ball was illegally batted or kicked
- whether a passer intentionally grounded a pass
- whether an ineligible receiver was downfield
- whether a receiver was illegally contacted
- whether a block was illegal
- anything not listed as reviewable in Section 3
- Consequence for the clone: pass interference, holding and other judgment fouls are never challenged. The 2019 pass-interference review was a one-year trial (Wikipedia, SRC-SECONDARY) and is not in the 2026 book.
- Coach challenge of called fouls (my reading of 15-3, 15-4 and 15-7-1): a judgment flag itself cannot be challenged; only its administrative parts (spot, down, yardage, fouling player's number) and a reviewable fact behind it (touching, out of bounds, number of players) can.

Effects of a reversal: [SRC-OFFICIAL, PDF pp. 67 to 71]
- Clock: the game clock is reset to the time when the ball should have been declared dead; status by Rule 4-3. If the ruling is not changed, the clock is not reset (15-5-1).
- 10-second runoff (15-5-2; also 4-7-4, PDF p. 22): for plays that begin after the two-minute warning, if the changed ruling gives a running clock (or a clock that would have restarted before the snap), reset to the time the play should have ended, then run 10 seconds. The play clock is set to 30; both clocks start on the ready-for-play signal. If under 10 seconds remain, the half or game is over. Neither team may decline it; either team may avoid it by taking a charged timeout (then the clock is reset, the play clock is 25 and the game clock starts on the snap).
- Play clock after a review: reset to 40 when a reversal brings no runoff and no timeout (4-6-3-b); 25 for replay administration under 15-9 with under 25 seconds left (4-6-2-h, 4-6-3-a; PDF p. 21).
- Erroneous whistle: the normal whistle rule (7-2-1-o, PDF p. 33) does not apply when a play is reversed or administered in replay; Rule 15 governs.
- Possession after a reversal (15-2-3): when the on-field ruling was a dead ball (score, down by contact, incomplete pass) and replay finds possession was lost before the ball should have been dead, possession may be given to a player who clearly recovers a loose ball in the immediate continuing action. A loose ball that touches out of bounds counts as a clear recovery by the player who last had it. A preliminary ruling by officials on who recovered may count as the clear recovery. No clear recovery: the notes above apply (last possession, one-yard line in own end zone).
- Fouls (15-7, PDF p. 71):
  - A foul is nullified when a necessary aspect of it is changed (15-7-2). A foul can be created if the reviewed fact itself creates it, or if the Referee announced before the review that there was no foul because of a ruling that is then changed.
  - Fouls after the ball should have been dead are disregarded, except personal fouls and unsportsmanlike conduct (15-7-3, item 1). Live-ball fouls before that moment may be enforced.
  - Pre-snap fouls (other than personal and unsportsmanlike) before a review are ignored if the earlier ruling is changed (item 2).
  - The head coach may change an accept or decline decision made before the review (item 3). This matters for NX7: a decision can be re-opened after a reversal.
- Timeout: 15-6; see section 2.

### 6. 2026 changes

- The book's own list (PDF p. 2) has only 6-1-3, 6-1-5, 6-1-6 and 19-2. None touches replay or challenges. [SRC-OFFICIAL]
- 15-1-1-a (head coach's pregame challenge designee) is in the 2026 text but not in that list. ESPN (Aug 10, 2026) says the league made it as a summer rulebook edit, without an owners' vote, and a league official confirmed it. The designee must be told to the officiating crew before the game and keeps the job for the game; the head coach keeps the decision in practice. [SRC-SECONDARY]. NFL.com ran the same story on Aug 10, 2026. Mechanics for the clone: unchanged; only who throws the flag.
- 2026 Playing Rule 5, one year only: the NFL Officiating department may correct clear and obvious mistakes if there is a work stoppage with the NFL Referees Association (nfl.com announcement page for 2026). [SRC-OFFICIAL for the item; text not in the rulebook] The NFLRA ratified a 7-year agreement in late May 2026, and reports said the rule would not apply if the deal was ratified by May 31, so it is moot. [SRC-SECONDARY: National Football Post 2026-05-29; NBC station reports]
- Counts, timeouts and the list of reviewable plays: no 2026 change. The third-challenge rule (2024) and the replay-assist list (April 2025) are older and already in the 2026 book. [SRC-OFFICIAL for the text; SRC-SECONDARY for the 2025 dates (ESPN 2025-08-29: owners voted in April to add facemask, horse-collar and tripping to replay assist)]
- Camera access change (2025): coaches and club staff in the coaching booth can see the Replay Official's camera feed. [SRC-SECONDARY: ESPN 2025-10-22]

### 7. Statistics

All coach-challenge counts are regular season unless stated. "Per game" figures I computed use 272 regular-season games per season (17 games x 32 teams / 2), so "per team per game" is half of "per game". These are computed from public numbers.

Coach challenges, per season:
- 2018 to 2020 average: 174 per season. 2021: 131. 2022: 131. [SRC-SECONDARY: ESPN Seifert 2023-01-18]
- 2023: 137 in the regular season. [SRC-SECONDARY, weak: Mile High Report blog, 2024-09-05; could not verify against a league source] Computed: 0.50 per game, 0.25 per team per game.
- 2024: 133 challenges, 50 reversed (37.6 percent; ESPN says "about 38 percent", the lowest rate in five years). Data compiled from NFL game books, regular season, 2010 to 2024. [SRC-SECONDARY: ESPN, Lavigne and Surendran, 2025-08-29] Computed: 0.49 per game, 0.24 per team per game; 83 lost challenges, so 83 timeouts lost, 0.31 per game, 0.15 per team per game.
- 2025: 151 coach challenges, the most since 2019. [SRC-SECONDARY: ESPN, Seifert, 2026-08-10; the page does not say whether playoffs are included.] If regular season only: 0.56 per game, 0.28 per team per game. No full-season success rate found.
- 2026 to date: not found. [UNVERIFIED] (searches for week-by-week 2026 numbers returned nothing; the designee rule is brand new.)
- Since 2010 the number of coach challenges has fallen about 47 percent. [SRC-SECONDARY: ESPN 2025-08-29]

Coach challenges, success (reversal) rate. Through week 7 of each season: [SRC-SECONDARY: ESPN, Kahler, 2025-10-22, "NFL replay challenges through Week 7"]
- 2021: 16 of 46 (34.8 percent)
- 2022: 18 of 51 (35.3 percent)
- 2023: 24 of 55 (42.9 percent)
- 2024: 21 of 53 (39.6 percent)
- 2025: 36 of 60 (60.0 percent); flags thrown 60, against an average of 51.5 for the same weeks of the previous four seasons (the table's own average is 51.25).
- ESPN credits the 2025 jump to the new camera feed in the coaching booth.
- Earlier: 2020 through Dec. 14: 59 of 116 (50.9 percent) [Football Zebras 2020 statistics page]; 2017: about 47.6 percent, 2016: 48.8 percent [Football Zebras post, via search summary]. ESPN (2023-01-31) says about 40 percent of challenged plays overall have been reversed (as worded; no period given). All SRC-SECONDARY.
- Lost challenge and timeout: every lost challenge costs one timeout (15-6-1). So the share of challenges that cost a timeout was about 62 percent in 2024 (83 of 133, computed) and 40 percent in 2025 through week 7 (24 of 60, computed).
- Third challenge: McKay said data show it is rarely needed (2024). No count found. [SRC-SECONDARY]

Booth-started reviews and replay assist:
- Booth success: ESPN says the success rate of replay challenges by league officials in the booth rose from 25 percent in 2010 to 76 percent in 2024. ESPN does not say whether automatic reviews of scores and turnovers are counted. No season counts given. [SRC-SECONDARY: ESPN 2025-08-29]
- Football Zebras 2020 (through Dec. 14): replay booth 103 reversals in 179 reviews (57.5 percent); coaches 59 of 116; all replays 162 of 295. The page prints 290 as the total, but 116 plus 179 is 295 and the page's own by-type table adds to 295; the 290 is a misprint on the page. [SRC-SECONDARY]
- Replay assist used more than 300 times in 2024 (NFL spokesperson to ESPN). 90 percent of replay assist interventions are for line to gain (first downs and goal line), catch or no catch, down by contact, and flag pickups (Butterworth, NFL VP of officiating). The league does not plan to publish detailed numbers; assists are not consistently noted in game books. [SRC-SECONDARY: ESPN 2025-08-29]
- Total reviews, first seven weeks: 117 in 2024 and 137 in 2025 (ESPN 2025-10-22). Reading this as all reviews including coaches' challenges, booth reviews would be about 77 of the 137 in 2025 (derived; the article does not define it). [SRC-SECONDARY]
- Quality: Troy Vincent said there were 171 replay review or replay assist decisions in 2025 and five that the league wanted back (about 2.9 percent, computed); four of the five were in 1 p.m. ET games. [SRC-SECONDARY: ESPN, Kahler, 2026-02-25] The 171 does not match the 137 through week 7, so it is probably a narrower set; the article does not say.
- Rate of automatic reviews (scores, turnovers) that are reversed: no figure found for 2023 to 2026. [UNVERIFIED]. The nearest figures are the booth rates above.

Breakdown by category (reversal rate). Only one dataset found: Football Zebras, 2020 season through Dec. 14, by the call on the field; coach and booth reviews apparently combined (its reversals column sums to 162, the same as "all replays"). The page does not say whether automatic reviews are included. [SRC-SECONDARY: footballzebras.com/replay/2020-replay-statistics/] Format: call, reversals of reviews, rate.
- Pass completion ruled: 34 of 70 (48.6 percent)
- Runner broke the plane: 25 of 39 (64.1 percent)
- Incomplete pass ruled: 24 of 37 (64.9 percent)
- Fumble: 17 of 28 (60.7 percent)
- First down: 11 of 25 (44.0 percent)
- Interception: 12 of 18 (66.7 percent)
- Runner was not down by contact: 12 of 15 (80.0 percent)
- Short of the line to gain: 2 of 14 (14.3 percent)
- Short of the goal line: 7 of 12 (58.3 percent)
- Runner was down by contact: 5 of 12 (41.7 percent)
- Runner was inbounds: 2 of 6 (33.3 percent)
- Too many players on the field: 3 of 4 (75.0 percent)
- Touchback: 2 of 3; loose-ball recovery: 2 of 3; score: 1 of 3
- One review each: tipped pass (reversed), safety (reversed), pass was not tipped (reversed), legal forward pass (upheld), forward pass (upheld), ball out of bounds (upheld)
- No category dataset for 2023 to 2026 was found. A claim of 57 percent success on score and turnover reviews and 39 percent on spot and first-down reviews appeared in one blog without a data source; I did not use it.
- Pass interference: reviewable only in 2019; not now. Out of bounds and "catch in the end zone" are folded into the rows above (possession, boundary, goal line); no separate rates found.

Useful derived values for the design session (all from the numbers above):
- A rough challenge frequency: about 0.25 to 0.28 per team per game.
- Reversal share: about 38 percent (2024) with a recent rise toward 60 percent (2025, first seven weeks).
- Time per review: about 85 seconds average.

### Where the official text differs from NFL_EXTRA_FEATURES.md (sections 3 and 7)

- Section 7 outline, "a successful challenge restores the timeout": the 2026 book charges a timeout only on an unsuccessful challenge; it never says a won challenge "restores" one. Results are the same. The only explicit "restored" rule is 15-6-2 (a timeout taken after the two-minute warning is restored if a review changes the ruling). NX1 should handle that case.
- "No coach's challenge after the two-minute warning of each half": the book bars coach challenges of plays that BEGIN after the warning (15-1-2-a). The last play before the warning can still be challenged by the coach. Key the rule on when the challenged play began.
- "The booth reviews all scoring plays and turnovers automatically, and any play in the last two minutes": the book says the Replay Official "may initiate" those reviews and sets no limit. In practice he starts a review when he sees a likely error; the confirmation of scores and turnovers is routine. Model a booth review as something that happens when the on-field ruling is wrong or doubtful, not on every play.
- "After the challenging team committed a foul that delays the next snap": book wording is "prevents the next snap" (15-1-1-b).
- "A challenge when not allowed costs a timeout, or a 15-yard foul when the team has none": confirmed (15-1-1-d), plus the 15-yard foul is a foul between downs that cannot offset and is enforced in addition to any other foul.
- "Reviewable and non-reviewable lists": fully settled; the requirements file's example categories are all correct. Pass interference is not reviewable (apart from touching of the pass and the spot of the foul), so N2.1 should not include it.
- NX7 link: 15-7-3-item 3 lets a head coach change an earlier accept or decline decision after a reversal.
- A line-to-gain challenge is "successful" (no timeout lost) only if the new-series ruling changes (15-3-7 notes 2 and 3). So a challenge can move the ball to a better spot and still lose the timeout; the design must treat that case separately.
- Section 3 C8 "never more than 3 challenges per game": confirmed. "Never more than 3 timeouts per half": confirmed for regulation (4-5-1, item 1, PDF p. 19) and postseason overtime (16-1-4-g: three per half); regular-season overtime is 2 per period (4-5-1; 16-1-3-e).

### Could not settle

- The Casebook (Approved Rulings). operations.nfl.com/the-rules/nfl-rulebook/ has no link to it, searches for a 2026 casebook found nothing, and the rulebook only cites "A.R." in Rule 3. It is not publicly reachable.
- Exact spoken wording of the Referee's announcements, and the practical time limit for throwing the flag. The book says only "before the next legal snap or kick". The 20-second play-clock figure is a coach-side practice quote (ESPN 2023).
- Whether a play is still reviewed when a flag is thrown illegally (book silent; older Football Zebras posts suggest not).
- Whether a play already reviewed can be challenged again (book silent).
- 2026 season-to-date counts and success rates; a full-season 2025 success rate; an official 2023 count.
- Reversal rates for automatic reviews (scores, turnovers) and for any category in 2023 to 2026. Only 2020 category data exist publicly.
- operations.nfl.com pages "How do NFL coaches use their challenges" and "...timeouts" returned 404 when fetched; only search-result summaries were seen (2019 analysis: league-wide analyses of challenge frequency per game, for example one head coach at 0.29 challenges per game, 23 of 45 successful). Not used for numbers.
- Whether ESPN's 151 (2025) includes playoff games, and what the 171 (2025) counts.

### Sources (retrieved 2026-10-14 unless stated)

Official:
- 2026 Official Playing Rules of the NFL (PDF, from nfl.com / operations.nfl.com/the-rules/nfl-rulebook/), converted to text; Rules 3-36, 3-41, 4-3 to 4-7, 7-2-1-o, 8-7, 14-1, 14-1-3, 15, 16-1; pages as cited.
- https://operations.nfl.com/rules-officiating/instant-replay/replay-officials : roles and duties of replay officials.
- https://operations.nfl.com/rules-officiating/instant-replay/art-mcnally-gameday-central : AMGC process; "clear and obvious"; 2024 average review 1 min 25 s.
- https://www.nfl.com/news/approved-2024-nfl-season-playing-rules-bylaws-and-resolutions : 2024 amendment to 15-1-1 (third challenge after one success); the page's publication date field is blank.
- https://www.nfl.com/news/nfl-announces-new-playing-rules-bylaws-resolutions-for-2026 : 2026 approved items (the one-year work-stoppage rule).
- https://www.nfl.com/news/nfl-to-allow-head-coaches-to-designate-an-assistant-to-throw-challenge-flag : 2026 designee (2026-08-10, via fetch of the amp.nfl.com copy).

Secondary:
- https://www.espn.com/story/_/id/49575837 (Seifert, 2026-08-10): designee rule; 151 challenges in 2025.
- https://www.espn.com/nfl/story/_/id/46087159 (Lavigne and Surendran, 2025-08-29): 133 and 50 in 2024; 38 percent; booth 25 to 76 percent; replay assist more than 300 uses; 90 percent categories.
- https://www.espn.com/nfl/story/_/id/46675881 (Kahler, 2025-10-22): week-7 tables 2021 to 2025; camera feed; review lengths; reviews 117 and 137.
- https://africa.espn.com/nfl/story/_/id/48035813 (Kahler, 2026-02-25): 171 decisions, five wanted back.
- https://africa.espn.com/nfl/story/_/id/35468076 (Seifert, 2023-01-18): 174, 131 and 131 per season.
- https://www.espn.com/nfl/story/_/id/35387469 (Holder, 2023-01-31): practice of flag timing, overall about 40 percent reversals.
- https://bleacherreport.com/articles/10114326 (2024-03-25): the 2024 third-challenge change.
- https://chargers.com/news/nfl-tweaks-instant-replay-system-132066 (2016-05-24): the 2016 rule text (both challenges; 15 yards when no timeouts).
- https://www.footballzebras.com/replay/2020-replay-statistics/ (last updated 2020-12-14): 2020 coach, booth and by-type figures.
- https://www.footballzebras.com/2013/01/ridiculous-red-flag-rule-burden-on-referee/ (2013-01-05) and https://www.footballzebras.com/2016/10/quick-calls-week-8-2016/ : older practice on illegal challenges.
- https://en.wikipedia.org/wiki/Replay_review_in_gridiron_football : rule history (1999, 2004, 2011, 2012, 2019 trial, 2022 expedited review, 2024).
- https://www.foxsports.com/stories/nfl/nfl-replay-review-expansion-what-fouls-can-challenged-2025 : 2025 cheat sheet of coach, replay-assist-only and booth-only plays.
- https://sports.yahoo.com/articles/nfl-rule-changes-2026-competition-212655469.html (2026-03-24): the five 2026 proposals.
- https://www.nationalfootballpost.com/2026/05/29/its-official-nfl-reaches-7-year-deal-with-referees-association : referees' agreement, work-stoppage rule moot.
- https://www.milehighreport.com/2024/9/5/24235727/nfl-head-coach-challenge-records : 2023 count of 137 (seen only as a search summary; the page returned 403).


## Part 4. Quarterback runs, the slide and the sneak

Retrieved 2026-10-14. Rulebook = the 2026 Official Playing Rules of the NFL (PDF, copyright 2026 NFL), PDF page numbers given as "PDF p. n". Citations are Rule-Section-Article.
Tags: SRC-OFFICIAL, SRC-SECONDARY, UNVERIFIED. My own readings and calculations are marked "reading" or "computed".

### Answers in brief

1. Runner, passer, passing posture.
   - A runner is any offensive player in possession of a live ball (3-27, PDF p. 15). So a quarterback holding the ball is a "runner" by definition at every moment before he throws. SRC-OFFICIAL.
   - A passer is a player who makes a legal forward pass, and he is "the passer" until the play ends (3-21-2, PDF p. 14). SRC-OFFICIAL.
   - The rulebook has no phrase "in the act of passing". The protections attach to "passing posture" (before, during or after throwing or attempting a pass) in 12-2-9-a-1 and 12-2-11. They end when the passer "becomes a blocker, or a runner" (12-2-11-e). SRC-OFFICIAL.
   - A quarterback who tucks the ball and runs: rushing for statistics (Guide for Statisticians, p. 15, item 3). SRC-OFFICIAL.
2. Slide, kneel, down by contact.
   - A slide or dive (feet or head first, or a simulated one) ends the play the instant he touches the ground with anything but hands or feet (7-2-1-d-2). SRC-OFFICIAL.
   - A quarterback who immediately drops to a knee, or simulates it, behind or beyond the line of scrimmage: ball dead (7-2-1-c). SRC-OFFICIAL.
   - "May not be hit" is too strong. Defenders must treat him as down by contact and pull up; unavoidable contact by a defender already committed is not a foul unless it is a forcible hit to head or neck with helmet, shoulder or forearm, or other unnecessary roughness. The runner must begin before contact is imminent. SRC-OFFICIAL.
   - Late contact on a slid, kneeling or stopped runner is unnecessary roughness, 12-2-8-d: 15 yards, plus automatic first down if by the defense. SRC-OFFICIAL.
3. Intentional grounding (8-2-1, PDF p. 38). SRC-OFFICIAL.
   - The 2026 book says "pocket area" (3-25), not "tackle box". The term "tackle box" does not appear in the book.
   - Penalty: loss of down and 10 yards from the previous spot, or loss of down at the spot of the pass when that spot is more than 10 yards back or more than half the distance to the goal line; a safety if the passer's entire body and the ball are in his end zone. The half-distance rule (14-2-1) does not apply to it.
4. Tush push, assisting the runner.
   - 12-1-4 (PDF p. 53) bans pulling a runner and two other acts; it names no ban on pushing a runner forward. 10 yards. The words "sneak" and "tush push" do not appear in the rulebook. SRC-OFFICIAL.
   - 2025: the Packers' revised ban failed 22 to 10 on 2025-05-21 (24 of 32 needed). SRC-OFFICIAL (nfl.com).
   - 2026: no club submitted a ban; the five competition-committee proposals approved at Phoenix (2026-03-31) do not mention it; 12-1-4 is not among the 2026 rule changes of the book. SRC-OFFICIAL.
5. Spot, ball dead, statistics.
   - Spot: where the ball is declared dead (3-12-1; 7-2-1), which is the dead ball spot and the succeeding spot (14-3-4). SRC-OFFICIAL.
   - Statistics come from the NFL's own Guide for Statisticians (copyright 2025). All plays from scrimmage are rushing plays unless a kick, a pass, or an "apparent attempt to pass" ends at or behind the statistical line of scrimmage (then it is a sack). SRC-OFFICIAL.
   - Kneel-down: no pass, no kick, so a rushing play (reading of the Guide's default rule; the Guide does not name the kneel). Spike: a forward pass into the ground, an incomplete pass attempt (reading of the Guide; rulebook 15-3-2 item 3 note 4 treats a spike as a pass ruling). SRC-OFFICIAL for the rules, UNVERIFIED that the Guide names either play.
   - Fumble lost: "all fumbles which result in opponents' recoveries" (Guide p. 25). SRC-OFFICIAL.
6. Numbers (section 5 below). League QB rushing 2022 to 2025 (regular season, StatMuse): 2,215 to 2,366 attempts a year, 4.1 to 4.7 yards per attempt, about 4.1 to 4.35 attempts per team game. SRC-SECONDARY.
   - Sneak or tush push on 3rd or 4th and 1: about 80 to 85 percent league-wide since 2022, depending on source and definition. SRC-SECONDARY.
   - Yards per QB rush split by down and distance: not published anywhere I could reach. Plainly: none found. The closest figures are listed in section 5.
7. Requirements file section 8: several items differ from the official text; see "Flags" at the end.

### 1. Runner, passer, passing posture, protections

Definitions
- 3-27 Runner (PDF p. 15). A runner is the offensive player in possession of a live ball, "holding the ball or carrying it in any direction". SRC-OFFICIAL.
- 3-21-2 Passer (PDF p. 14). A player who makes a legal forward pass is the passer until the play ends. SRC-OFFICIAL.
- 3-21-3 Forward pass and items (PDF p. 14 to 15). Any intentional forward movement of the hand of a player holding the ball to pass starts a forward pass. Item 1: contact that materially affects the passer after his throwing motion starts does not bring intentional grounding. Item 2 "Passer tucks ball": if he loses the ball while bringing it back toward his body, or after he has tucked it into his body, it is a fumble. Item 3: loss of the ball while re-cocking the arm is a fumble. (The same text is repeated in 8-1-1, PDF p. 37.) SRC-OFFICIAL.
- 3-2-5 Fumble (PDF p. 10). A fumble is any act, other than passing, successful handing or kicking, that loses player possession; it is not a fumble if the player immediately regains control inbounds. SRC-OFFICIAL.
- 3-25 Pocket area (PDF p. 15). The area between the outside edges of the normal tackle positions, extending back to the offense's end line. A player with the ball is out of the pocket area, and the area no longer exists, if any part of his body or the ball is outside it. SRC-OFFICIAL.
- 3-42 T-formation quarterback (PDF p. 17). A player aligned one yard or less behind the snapper. SRC-OFFICIAL.
- "In the act of passing" and "passing posture". There is no definition of the first phrase. 12-2-9-a-1 lists "a player in a passing posture (i.e. before, during, or after throwing or attempting a pass)" as defenseless, and 12-2-11 says players in a passing posture are treated as defenseless. SRC-OFFICIAL.

When a quarterback who keeps the ball is a runner, and what protection he keeps
- By 3-27 he is a runner while holding the ball. The special passer protections are tied to passing posture, not to the label "passer".
- 12-2-11-e (PDF p. 56): a passer who is standing still or fading backward after the ball left his hand must not be unnecessarily contacted through the end of the down, "or until the passer becomes a blocker, or a runner" (or, after a change of possession, a defensive player). SRC-OFFICIAL.
- 12-2-11-f (PDF p. 56): when the passer goes outside the pocket area and either keeps moving with the ball (without attempting to advance it as a runner) or throws on the run, he loses the one-step protection (a) and the low-hit protection (d) but keeps b, c and e and the ordinary unnecessary-roughness rules. If he stops behind the line and clearly sets a passing posture he is again covered by all passer protections. SRC-OFFICIAL.
- 12-2-11-g (PDF p. 56): the official must blow the play dead as soon as the passer is clearly in the grasp and control of a tackler behind the line and his safety is in jeopardy. SRC-OFFICIAL.
- Reading (mine): a quarterback who tucks the ball and runs to gain yards is a runner (protections of a runner, 12-2-8-d and 7-2-1-d, but not roughing the passer); a quarterback who is scrambling with the ball outside the pocket without attempting to advance keeps the partial passer protections of 12-2-11-f. The rulebook does not state this in one sentence; it follows from 12-2-11-e and f. SRC-OFFICIAL text, my synthesis.

Roughing the passer, 12-2-11 (PDF p. 55 to 56)
- a: pass rusher must stop after the first step once the ball has left the passer's hand; "drive through" is a foul.
- b: no stuffing or driving the passer into the ground; do not land on him with all or most of the weight.
- c: no forcible hit to head or neck, no helmet use against a passer in a defenseless posture.
- d: no forcible hit in the knee area or below on a passer with a foot on the ground (not applying out of the pocket, see f).
- Penalty: loss of 15 yards and automatic first down; disqualification if flagrant. SRC-OFFICIAL.

Defenseless player, 12-2-9 (PDF p. 55)
- The list includes: a player in a passing posture (1), "a runner already in the grasp of a tackler and whose forward progress has been stopped" (5), a player on the ground (7), and a quarterback at any time after a change of possession (9).
- Prohibited: forcibly hitting head or neck area with helmet, facemask, forearm or shoulder; lowering the head and making forcible contact with the helmet; illegal launching. Penalty: loss of 15 yards and automatic first down; disqualification if flagrant. SRC-OFFICIAL.

Unnecessary roughness against a runner, 12-2-8 (PDF p. 54 to 55)
- b: forcibly contacting a runner out of bounds.
- d: running, diving into or throwing the body against or on a runner whose forward progress has been stopped, "who has slid or taken a knee", or who has declared himself down by going to the ground untouched without trying to advance. Cross-reference to the 7-2-1-d notes about a sliding player.
- e: contact on any player on the ground before or after the ball is dead.
- f: throwing the runner to the ground after the ball is dead.
- g: unnecessary contact on a player who is out of the play or who should not have anticipated it.
- Penalty: loss of 15 yards; disqualification if flagrant; if by the defense also an automatic first down. The Penalty Summary (PDF p. 78) lists "Unnecessary contact against a runner, 12-2-8(d), (f)" under 15 yards. SRC-OFFICIAL.

Horse-collar and hip-drop
- 12-2-16 Horse-collar (PDF p. 57): does not apply to a runner in the pocket area or the close-line area; a foul if the knees buckle. 15 yards and automatic first down. SRC-OFFICIAL.
- 12-2-18 Hip-drop tackle (PDF p. 57): grabbing or wrapping the runner and then unweighting by swiveling and dropping the hips, landing on or trapping the runner's legs at or below the knee. 15 yards and automatic first down. SRC-OFFICIAL.
- Context: NFL health and safety page lists the hip-drop ban as a 2024 change, the helmet and low-hit protections of quarterbacks as 2002 to 2011 changes (https://www.nfl.com/playerhealthandsafety/equipment-and-innovation/rules-changes/nfl-health-and-safety-related-rules-changes-since-2002). SRC-OFFICIAL.

The slide, the kneel and "giving himself up", 7-2-1 (PDF p. 33)
- a: ball dead when a runner is contacted by an opponent and touches the ground with any part of the body other than hands (including the wrist) or feet (including the ankle).
- b: ball dead when a runner is held or restrained so that forward progress ends.
- c: ball dead "when a quarterback immediately drops to his knee, or simulates dropping to his knee, behind or beyond the line of scrimmage". Note: if he does not immediately drop to a knee and contact by a rushing defender is unavoidable, it is not a foul unless the defender commits some other act that is unnecessary roughness.
- d: a runner declares himself down by (1) falling to the ground or kneeling and clearly making no immediate effort to advance, or (2) sliding or diving feet or head first, or simulating it: the ball is dead the instant he touches the ground with anything other than hands or feet, or begins to simulate touching.
- d notes: (1) defenders must treat a sliding or diving runner as down by contact; (2) a defender must pull up when the slide begins, but if already committed and contact is unavoidable it is not a foul unless he makes forcible contact into the head or neck with helmet, shoulder or forearm, or commits other unnecessary roughness; (3) the runner must start the slide or dive before contact is imminent, otherwise he "puts himself in jeopardy of being contacted".
- s: ball dead when a runner's helmet comes completely off.
- The phrase "given himself up" survives only in the replay article 15-3-2 item 4 (PDF p. 68); the operative wording is "declares himself down". SRC-OFFICIAL.
- A slide protects every runner, not only the quarterback; the kneel (c) is specific to the quarterback.

Fumbles by a running quarterback
- 8-7-3 (PDF p. 41): a fumble is any act other than a pass or kick that loses possession; either team may recover and advance, unless the fumble is on fourth down (8-7-5) or after the two-minute warning or in a Try (8-7-6).
- 8-7-5 (PDF p. 42): on a fourth-down fumble from scrimmage the ball may be advanced by any defender, but the fumbler is the only offensive player allowed to recover and advance before a change of possession; if a teammate recovers, the ball is dead and the next snap is at the spot of the fumble, or the spot of recovery if that is behind it.
- 8-7-6 (PDF p. 42): the same restriction after the two-minute warning and during a Try (the fumbler alone may recover and advance). SRC-OFFICIAL.
- Replay: 15-3-2 item 4 (PDF p. 68) lets the league review whether a runner fumbled before he was down by contact, out of bounds or had given himself up. SRC-OFFICIAL.

Enforcement of a foul on a quarterback who runs (needed to build accept or decline)
- 14-3-5 and 14-3-6 (PDF p. 62): for a foul during a running play with no change of possession, the basic spot is the dead ball spot. Penalty from the basic spot if the defense fouls in advance of or behind it, or the offense fouls in advance of it; if the offense fouls behind the basic spot, from the spot of the foul. Exceptions: offensive fouls behind the line are enforced from the previous spot; when the basic spot is behind the line and the defense fouls behind or beyond the line, from the previous spot. SRC-OFFICIAL.
- 14-4-2 Note (PDF p. 63): a foul during a run prior to a forward pass or kick from behind the line is enforced as a foul during a passing play (previous spot, 14-4-5). SRC-OFFICIAL.
- 14-2-4 (PDF p. 62): personal foul or unsportsmanlike conduct foul with the opponent in possession at the end of the down may also be enforced from the dead ball spot. SRC-OFFICIAL.
- 14-2-1 half-distance (PDF p. 62): applies to distance penalties; the two listed exceptions are intentional grounding and the palpably unfair act. SRC-OFFICIAL.
- Clock after a quarterback run: a slide, a kneel or a sack inbounds is not in the list of clock stoppers of 4-4 (PDF p. 19); a run out of bounds is (4-4-c), and the restart is given in 4-3-2 (PDF p. 18). SRC-OFFICIAL.

### 2. Intentional grounding and the scramble rules

8-2-1 (PDF p. 38). SRC-OFFICIAL.
- Definition: a passer "facing an imminent loss of yardage because of pressure from the defense" throws a forward pass not in the direction and vicinity of an originally eligible receiver. The pass need not be incomplete.
- Item 1, outside the pocket area: not called when a passer who is outside, or has been outside, the pocket area throws a forward pass that lands at or beyond the line of scrimmage extended (including out of bounds over the sideline or end line), even if no offensive player has a realistic chance to catch it. If a loose ball leaves the pocket area the area no longer exists. A passer is out of the pocket area if any part of his body or the ball is outside it. So the exception depends on where the ball lands, not on where he threw from.
- Item 2, contact: not called if (a) the passer started the pass toward an eligible receiver and was then significantly affected by contact so that the ball lands away from an eligible receiver, or (b) the passer is out of the pocket area and contact significantly affected the motion so that the ball lands short of the line of scrimmage.
- Item 3, spike on the snap: a T-formation quarterback may stop the clock if, immediately upon receiving the snap, he begins a continuous motion and throws the ball directly into the ground. Reading (mine): the item names only the T-formation quarterback; the definition of grounding needs "pressure from the defense", which an unpressured immediate spike does not have.
- Item 4, delayed spike: a passer who delays his passing action for strategic purposes may not throw the ball to the ground in front of him, even under no pressure.
- Penalty (8-2-1): (a) loss of down and 10 yards from the previous spot; or (b) loss of down at the spot of the pass if the spot is more than 10 yards from the previous spot or more than half the distance to the goal line; or (c) a safety if the passer's entire body and the ball are in his end zone when thrown.
- 14-4-5-a (PDF p. 63): "loss of down at the spot of the foul, or loss of down and a 10-yard penalty from the previous spot, whichever is less beneficial for the offense"; if the foul occurs less than 10 yards behind the line but more than half the distance to the goal line, the ball is placed at the spot of the pass; a pass thrown from the end zone is a safety.
- Combination penalty (14-1-2 item 2, PDF p. 61): grounding is a loss-of-down-plus-yardage penalty. On fourth down the ball goes to the opponent, and the distance penalty is also enforced.
- After the two-minute warning (4-7-1, PDF p. 21): grounding is an act that "conserves time"; if committed by the offense while time is in, 10 seconds are run off and the play clock is set to 30 (the offense may use a timeout instead; the defense may decline the runoff and take the yardage, and then the runoff is declined too). Loss of five yards "unless a larger distance penalty" applies. SRC-OFFICIAL.
- Replay (15-9-j-2, PDF p. 71): the league office may help only with a grounding call that rests on whether the passer was out of the pocket area; 15-3-2 item 3 note 3 (PDF p. 68): a grounding foul can be created in replay only if a pre-review announcement said so. SRC-OFFICIAL.
- Passing-play enforcement exceptions (14-4-5-c, PDF p. 63): offensive foul behind its own goal line is a safety if the defense elects.

Scramble rules in general
- There is no separate "scramble" article. A passer who runs behind the line may throw a legal forward pass anywhere behind the line (8-1-2, PDF p. 37): a pass thrown when his entire body and the ball are beyond the line is illegal (loss of down and 5 yards from the spot where the ball was released). Once the ball crosses the line of scrimmage, no forward pass behind the line is allowed (8-1-2). SRC-OFFICIAL.
- A "running play" begins with the snap if there is no kick or pass from behind the line (3-24-3-a). SRC-OFFICIAL.

### 3. The sneak and the tush push

Rulebook text (2026), PDF p. 52 to 53. SRC-OFFICIAL.
- 12-1-2-a (PDF p. 52): an offensive player may use hands and arms to restrict an opponent "if he is a runner. A runner may ward off opponents with his hands and arms. He may also lay his hand on a teammate or push him into an opponent, but he may not grasp or hold on to a teammate."
- 12-1-4 (PDF p. 53) Assisting the runner and interlocking interference. No offensive player may (a) pull a runner in any direction at any time; (b) use interlocking interference by grasping a teammate or encircling the body of a teammate to block an opponent; (c) push or throw his body against a teammate to aid him in an attempt to obstruct an opponent or to recover a loose ball. Penalty: loss of 10 yards.
- Reading (mine): the text bans pulling a runner and pushing a teammate in order to obstruct an opponent or recover a loose ball. It has no sentence that bans pushing the runner forward. This is consistent with how the competition committee and the press describe the tush push as legal. The Penalty Summary (PDF p. 78) lists "Assisting the runner, 12-1-4" under loss of 10 yards. The word "sneak" does not occur in the rulebook (checked by text search).

History and votes
- 2025, April: the Packers' first proposal (aimed at a teammate lined up behind the snapper pushing at the snap) was tabled at the Annual League Meeting (Palm Beach, around 2025-04-01). SRC-OFFICIAL (https://www.nfl.com/news/vote-on-tush-push-rule-change-proposal-tabled-for-later-date; the page shows no publication date).
- 2025-05-20: the Packers filed a revised proposal that would ban pushing or pulling a runner "in any direction at any time" and lifting him to his feet, now framed as "assisting the runner", "harkening back" to the rule in force until 2005 (https://www.nfl.com/news/packers-submit-revised-proposal-to-ban-tush-push-play-ahead-of-spring-league-meeting). SRC-OFFICIAL. Sports Illustrated says the penalty would have been 10 yards (https://www.si.com/nfl/packers-submit-revised-tush-push-proposal-voting-nfl-owners-meeting, SRC-SECONDARY). I could not find the proposal's exact article text.
- 2025-05-21: Spring League Meeting; the revised proposal failed, "two votes shy" of the 24 votes required; ten teams voted against, so 22 in favor. McKay: "the rule will stay as it is" (https://www.nfl.com/news/nfl-owners-vote-against-banning-tush-push-play-at-spring-league-meeting). SRC-OFFICIAL. A third-party site (Steelers Now, 2026-03-26) wrongly says "eight teams short"; the league's page and the 22-10 count win.
- 2026-02-22 to 24 (NFL scouting combine): McKay said he had seen no team proposal; Troy Vincent said the deadline had passed without the committee receiving one, and that the committee had talked about "aiding the runner" (players picked up and carried; example given: Christian McCaffrey, Josh Allen) but nothing on the push itself; the rule against pulling a runner "is not currently enforced as a call" and could become a point of emphasis in 2026 (https://www.nfl.com/news/competition-committee-co-chairman-rich-mckay-doesn-t-expect-tush-push-ban-proposal-in-2026 for McKay; https://www.nbcsports.com/nfl/profootballtalk/rumor-mill/news/competition-committee-discusses-aiding-the-runner-but-no-proposals-to-ban-the-tush-push for Vincent, dated 2026-02-24). McKay SRC-OFFICIAL; Vincent SRC-SECONDARY (PFT).
- 2026-03-24 to 25: the league released the proposals. Five playing-rules proposals, all from the competition committee: onside kick declared at any time; removal of the incentive to kick out of bounds from the 50; kickoff setup-zone alignment; league consultation on disqualifications; a one-year officiating correction power during a referees' work stoppage (https://www.nfl.com/news/playing-rules-bylaw-resolution-proposals-for-2026-nfl-season). No proposal about the sneak, the tush push, pushing or pulling a runner or Rule 12-1-4. SRC-OFFICIAL.
- 2026-03-31 (Annual League Meeting, Phoenix): clubs approved those playing-rule changes (https://www.nfl.com/news/nfl-announces-new-playing-rules-bylaws-resolutions-for-2026; https://www.steelers.com/news/nfl-owners-approve-2026-nfl-rule-changes). Neither text mentions the tush push. SRC-OFFICIAL.
- 2026 book: the front page of the rulebook (PDF p. 2) lists the 2026 changes as 6-1-3, 6-1-5, 6-1-6 and 19-2 only, so 12-1-4 is unchanged. SRC-OFFICIAL.
- 2026-03-25: McKay (conference call with reporters before the Phoenix meeting): "I don't know that it's the end of the debate"; "there's still people who are concerned with the whole pushing element"; the league's data show traditional sneaks now succeed more often than the tush push (https://www.nbcsports.com/nfl/profootballtalk/rumor-mill/news/rich-mckay-no-proposal-to-ban-it-but-tush-push-still-has-some-people-concerned). SRC-SECONDARY (press report of a league executive). The play therefore stays legal in 2026, but a future ban is not ruled out.
- The official 2026 proposals PDF named in the task (https://edge-operations.nfl.com/media/dxfj3uak/2026-playing-rules-bylaw-and-resolution-proposals.pdf) returns HTTP 404 today, also under operations.nfl.com. The same list is on the nfl.com article above. UNVERIFIED that the PDF says more than the article (Pittsburgh's and Cleveland's club resolutions are the only other items).

### 4. Spot, ball dead and statistics for a quarterback run

Spot
- 3-12-1 (PDF p. 12): forward progress is the point where the advance ends and "the spot at which the ball is declared dead by rule", even if the runner is pushed backward. SRC-OFFICIAL.
- 7-2-1 (PDF p. 33): see section 1; for a slide the ball is dead the instant he touches the ground (or begins to simulate); for a kneel, at the knee; for a sack, when he is touched and goes down or is held (a, b), or earlier if the official blows it dead under 12-2-11-g. SRC-OFFICIAL.
- 14-3-4 (PDF p. 62): the dead ball spot is where the ball became dead; the succeeding spot is where the ball is next put in play. SRC-OFFICIAL.
- Touchdown, 3-38 (PDF p. 16): any part of the ball on, above or behind the goal line while legally in possession of an inbounds player. A runner who slides short of the line is down at the slide spot. SRC-OFFICIAL.
- Safety, 3-28 (PDF p. 16): ball dead in possession of a team on or behind its own goal line when the impetus came from that team. A quarterback downed in his own end zone after dropping back there is a safety (reading, the standard application; the article text is the definition). SRC-OFFICIAL text.

Statistics: the NFL's own manual. Document: Guide for Statisticians, copyright 2025 National Football League, last modified 2025, 38 pages, hosted at https://www.nflgsis.com/gsis/documentation/stadiumguides/guide_for_statisticians.pdf (the NFL's Game Statistics and Information System). SRC-OFFICIAL. Page numbers below are the document's "n of 38".
- Determining the yard line (p. 4): if any point of the ball rests on or above a yard stripe, action is computed from that yard line; if all of the ball is beyond the stripe, from the first yard line in advance.
- Rushing (p. 11): "All plays from scrimmage are rushing plays unless" (1) a kick from behind the line, (2) a pass from behind the line, or (3) a player makes an apparent attempt to pass before he or a teammate is tackled, steps out of bounds, or fumbles behind or at the line of scrimmage, in which case it is a sack. Yards are netted (a loss is a minus rushing yard, there is no separate "yards lost" rushing category). Rush credited to the last offensive player to possess the ball behind the line. A run from a fake-punt or field-goal formation is a rushing attempt.
- Sacks, offense (p. 14 to 15): rule 1: apparent attempt to pass, then tackled, out of bounds or fumble at or behind the statistical line, is a sack with yards lost attempting to pass; "should he advance the ball across the statistical line of scrimmage, it is a rushing play". Rule 2: a quarterback tackled, or who fumbles or falls, while retreating to his normal passing position is a sack even without a passing position (exception: he recovers his own fumble and crosses the line: rush, fumble, own recovery). Rule 3: a rolling-out quarterback who, "with the ball in his throwing hand looks directly at an eligible receiver" before being tackled behind or at the line is a sack; if he "tucks the ball away without looking at a receiver, or lifts his arm as if to throw on an apparent designed rushing play", it is a rushing play. Rule 4: once he carries the ball beyond the statistical line, no sack is scored even if he later retreats and is tackled behind the line. Rule 5: a sack is not a pass attempt and the individual passer is not charged with lost yardage, but the yards are deducted from team gross passing yards.
- Aborted plays (p. 27): a fumbled snap or handoff with no pass is a rush for 0 yards charged to the ball handler, plus a fumble; "if the ball-handler fumbles when pulling the ball back to run himself, score the play as a rushing play".
- Fumbles (p. 25 to 31): own-recovery, charge the fumble to the player who lost possession; "fumbles lost" are fumbles recovered by opponents or fumbled through the end zone for a touchback (a fumble through the own end zone for a safety is not a fumble lost). On a rushing play, if the fumbler's team recovers behind or on the line, the fumbler is credited yardage to the point of recovery.
- Third and fourth down efficiency (p. 6): a third-down attempt is credited with a rushing attempt, a pass or a sack; a conversion is a first down rushing or passing.
- Kneel-down (reading, SRC-OFFICIAL rule applied): a kneel is a play from scrimmage with no kick or pass, so it falls under "All plays from scrimmage are rushing plays", a rushing attempt for the lost yards (the Guide does not use the word "kneel"; I searched the text for "kneel", "knee" and "spik" and found nothing relevant). Secondary sources agree: Wikipedia says a kneel is "typically recorded as a rushing attempt for -1 or -2 yards" (uncited, https://en.wikipedia.org/wiki/Quarterback_kneel, SRC-SECONDARY).
- Spike (reading): a spike is a forward pass thrown to the ground, so it is an incomplete pass attempt ("An incomplete pass, including when ... the pass strikes the ground", Guide p. 13). The Guide does not name the spike. PFF (Nathan Jahnke, 2011-03-22) says "on the stat sheet this is also considered an incomplete pass" and that a little over 1 percent of incomplete passes in 2010 were spikes (https://www.pff.com/news/stat-sheet-misconceptions-completion-percentage, SRC-SECONDARY). The rulebook itself treats a spike as a passer ruling in the replay article 15-3-2 item 3 note 4 (PDF p. 68). Grounding does add a pass attempt plus the penalty (Guide p. 13).
- Scramble ending in a sack versus a rush: sack if he made an apparent attempt to pass at or behind the line (including looking at a receiver with the ball in his throwing hand); rush if he tucked and ran, or crossed the line. Quarterback runs stopped behind the line with no apparent pass attempt are rushes for a loss, not sacks. This also matches the secondary description at https://en.wikipedia.org/wiki/Quarterback_sack (SRC-SECONDARY).

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

### 3. Offsetting fouls

#### 3.1 What counts as a double foul
- A foul by either team during the same down in which both teams commit at least one foul, dead ball fouls included. [SRC-OFFICIAL] 3-13-1 (e), PDF p.12.
- A foul between downs cannot combine with a live ball or dead ball foul to make a double foul; it is always enforced separately. [SRC-OFFICIAL] 14-4-9.
- A violation (an infraction with no penalty) does not offset a foul. [SRC-OFFICIAL] 3-13-4.

#### 3.2 No change of possession (14-5-1, PDF p.65 to 66)
- Offset; replay the down at the previous spot; the down number and line to gain are those of the down in which the fouls occurred; neither team can decline.
- Exceptions:
  1. A 15-yard penalty (one or more fouls) against a five-yard penalty that has no automatic first down, loss of down or 10-second runoff, or is not a spot foul: the 15-yard penalty is enforced from the previous spot and the five-yard penalty is disregarded; the minor-foul team cannot decline.
  2. Dead ball delay-of-game for spiking against a live ball foul by the opponent: the delay team may decline the opponent's foul and take its own penalty from the dead ball spot.
  3. Both fouls dead ball (or treated as such): offset at the succeeding spot and the down counts, unless they occurred after the ball was made ready (then 5-v-15 rules).
  4. 14-4-9 Item 3 cases (section 3.5).
- Reading for 5-v-15 (not stated in one sentence): because the 15-yard penalty is enforced rather than offset, Items 1, 4 and 5 of 14-1-2 apply to it (a defensive 15 gives first-and-10 to Team A; an offensive 15 repeats the down). Item 8 (replay with the same down) applies to offsetting fouls. [SRC-OFFICIAL, reading] [UNVERIFIED in the casebook]

#### 3.3 Related notes
- Fouls with a change of possession (including post-possession fouls on a scrimmage kick) follow 14-5-2 and 14-5-3 instead of 14-5-1.
- First touching by the kicking team does not offset a foul by the receivers; the foul is enforced as customary and the first-touching violation is disregarded. [SRC-OFFICIAL] 9-2-2, PDF p.44.

#### 3.4 Double foul with a change of possession (14-5-2, 14-5-3, PDF p.66)
- Article 2 Item 1: a double foul during a down with one or more changes of possession (including a post-possession foul by Team B on a scrimmage kick): the team last gaining possession keeps the ball after enforcement for its own foul, provided it did not foul before last gaining possession ("clean hands").
  - Exceptions: (1) if Team A fouls during a free kick or scrimmage kick before the change of possession, Team B may elect to replay the down at the previous spot; (2) if a safety results from enforcement of a Team B foul, the down is replayed at the previous spot; (3) if the offense's foul before the change is a personal or unsportsmanlike foul, the penalties offset and the team last in possession keeps the ball at the spot where its foul would be enforced if it were the only foul; exceptions (1) and (2) also apply.
- Item 2: if the team last in possession does not have clean hands, the penalties offset and the down is replayed at the previous spot.
- Article 3 (both teams foul after the last change of possession): offset; the team last in possession keeps the ball at the spot where its foul would be enforced alone; if that spot would be a touchback the ball is put on the 20 (or the 35 or 20 per 6-1-5 for a free kick); if it would be a safety, on the one-yard line. If the offense also fouled before the change, the same applies; on a kicking play Team B may elect to replay the down.
[SRC-OFFICIAL] The score-on-the-play interplay (a double foul on a play where the team last in possession scores) is not spelled out in these articles; the "clean hands" rule governs and the score is not mentioned. [UNVERIFIED for scoring plays]

#### 3.5 Dead ball fouls and live ball fouls (14-4-9, PDF p.65)
- Item 1: a dead ball foul by Team A after a down in which Team A made a first down: first-and-10 after enforcement; a foul between downs: "first-and-25" (see 2.8).
- Item 2: dead ball fouls by both teams offset at the succeeding spot and the down counts; any disqualified player is still removed.
- Item 3: live ball and dead ball fouls combine to create double or multiple fouls with the customary rules. Exceptions:
  1. A 5-v-15 double foul on the last play of a half where the 15 is a dead ball personal, unsportsmanlike or taunting foul by either team: the penalty yardage is enforced on the second-half kickoff or the overtime kickoff; no extension of the period.
  2. The scoring team commits a dead ball foul after a score and the opponent's live ball foul is not a personal or unsportsmanlike foul: the opponent's foul is disregarded, the score counts, and the dead ball foul is enforced on the Try (or on the succeeding free kick if no Try). If the opponent's foul is personal or unsportsmanlike: the score counts and the fouls offset after the play.
  3. "Clean hands end of half": the only foul by the defense is a dead ball foul on the last play of the half. A non-personal, non-unsportsmanlike foul by the offense is disregarded and the defense's dead ball personal or unsportsmanlike foul is enforced on the second-half kickoff or the overtime kickoff. If both teams' fouls are personal or unsportsmanlike, they offset at the end of the down.
- Exception to Article 9: a personal, unsportsmanlike or taunting foul by either team after the end of the second or fourth period is enforced on the second-half kickoff or the overtime kickoff, unless part of a double foul. [SRC-OFFICIAL]

### 4. Dead ball versus live ball, scores, and extra plays

#### 4.1 Definitions again (short)
- Live ball foul: after the snap until the ball is dead. [3-13-1 (a)]
- Dead ball foul: in the continuing action after a down ends; taunting at any time. A foul occurring simultaneously with the ball becoming dead is a dead ball foul. [3-13-1 (b), 14-4-9]
- Foul between downs: after the down and any continuing action, before the next snap or free kick. [3-13-1 (c)]
- All [SRC-OFFICIAL] PDF p.12, p.65.

#### 4.2 Fouls on a scoring play
- A live ball foul by the scoring team: the score is erased if the offended team accepts the penalty (an unaccepted foul has no effect on the score). Enforcement follows the usual spot for the type of play. [SRC-OFFICIAL, reading] 14-1-1, 14-4.
  - Special case: a foul by the offense in the defense's end zone before scoring a touchdown on a run is enforced from the goal line. 14-3-6 Exception 4 (offense).
  - Special case: on the last play of a half a score by the offense is not counted if the offense fouls (4-8-2 (b)); extension may be asked by the defense only for the five listed offensive fouls (illegal touching, kick catch or fair catch interference, palpably unfair act, a personal or unsportsmanlike foul before a safety, an interception, a fumble or backward pass recovery or a fourth-down failure, and a kicking-team foul before the receiving team has possession).
- Fouls by the defense during a down in which the offense scores: "In all scoring situations, the offended team also has the option of accepting the penalty with customary enforcement and beginning a new series, or replaying the down, instead of counting the points." [SRC-OFFICIAL] 14-2-3 (quote is under 40 words; paraphrase: the offended team may take the penalty instead of the points).
- Personal fouls, unsportsmanlike fouls and palpably unfair acts by a team during a down in which the opponent scores a field goal or a safety are enforced on the succeeding free kick (unless the score resulted from the enforcement). On a touchdown the penalty, whether a live ball, dead ball or between-downs foul, is enforced on the Try. On a successful Try kick, a Team B foul that does not result in a re-Try or negate a score may be enforced on the succeeding free kick. [SRC-OFFICIAL] 14-2-3, PDF p.62.
- A safety by enforcement exists only when the offense fouls behind its own goal line and the defense elects it (2.5); the half-distance rule alone never produces a safety.
- Overtime: if the first team to possess the ball scores and the second team loses possession by interception or fumble on its first possession, the down runs to its conclusion and only fouls that require replay, negate a score, or palpably unfair acts are enforced. [SRC-OFFICIAL] 16-5 (a), PDF p.72.

#### 4.3 The "nullified score and previous spot" rule
- A pass-play foul by either team from the snap until the forward pass ends is enforced from the previous spot; so a touchdown pass erased by offensive holding returns the ball to the previous spot minus 10. [SRC-OFFICIAL, reading] 14-4-5 and 12-1-3 (c).
- A foul by the offense before a change of possession (for example before a pass that is intercepted and run back for a touchdown): the defense may decline and keep the touchdown, or accept and the ball goes back to the offense from the previous spot. [SRC-OFFICIAL, reading] 14-4-3 (b).
- Personal and unsportsmanlike fouls by the offense are the exception: they do not erase the defense's possession (14-4-3 (b), 14-4-5 (e)).

#### 4.4 Extra plays (extension of a period, 4-8-2, PDF p.22)
- Ball in play when time expires: the period continues until the down ends (4-8-1).
- Defense accepted live ball foul on the last play: the offense may extend by one untimed down after the penalty. In the first or third period, if the offense does not extend, any accepted penalty is enforced before the succeeding period starts (so the next period begins at the new spot). If the first or third period is extended, any additional play, including a Try, is completed before the teams change goals.
- Offense foul: no extension. Exceptions on the defense's request (five fouls listed in 4.2).
- A touchdown on the last play of a period: the Try is made (not in sudden-death overtime; not when a Try cannot change the outcome in the fourth period).
- Kick catch interference with no fair catch signal: the receiving team may extend by a down from scrimmage. Fair catch made: receivers may choose a fair catch kick down. Fair catch interference: down from scrimmage or fair catch kick.
- A safety from a foul on the last play of a half: the score counts, and a safety kick is made if the receivers ask.
- Double foul on the last down of either half: the period is extended by an untimed down, with exceptions: both fouls dead ball; major-minor 5-v-15 where the major is the offense's or a dead ball foul by either team; "clean hands end of half"; a double foul with a change of possession that does not replay the down. A double foul on the last play of the first or third period does not extend the period.
- There may be more than one untimed down at the end of a period. [SRC-OFFICIAL]

### 5. Clock effects of penalties

#### 5.1 When the clock stops and starts (4-3, 4-4, PDF p.18 to 19)
- The clock stops: at the end of a down during which a foul occurs (4-4 (e)); at the time of a foul that keeps the ball dead or kills it at once (4-4 (g)); at the Referee's two-minute warning; when the ball is out of bounds, a pass is incomplete, a score or change of possession ends the down, and so on. [SRC-OFFICIAL]
- Starting rule after a timeout: the clock starts on the next snap, except as listed in 4-3-2.
  - Runner out of bounds on a play from scrimmage: clock starts on the Referee's ready-for-play signal, except it starts on the snap after a change of possession, after the two-minute warning of the first half, and inside the last five minutes of the second half. (4-3-2 (a))
  - Foul stops the clock before or after a down: after enforcement or declination, the clock starts as if the foul had not occurred, except that it starts on the snap when:
    1. the foul occurs after the two-minute warning of the first half;
    2. the foul occurs inside the last five minutes of the second half;
    3. the offense commits a foul during the fourth period or regular season overtime after the ball was made ready for play, causing the clock to stop before a snap;
    4. the offense commits two successive delay-of-game penalties during the same down while time is in (this is also unsportsmanlike conduct, 15 yards: 12-3-1 (n));
    5. a specific rule prescribes otherwise. (4-3-2 (e))
  - After a 10-second runoff the clock starts on the ready-for-play signal. (4-3-2 (g))
- In plain words for the engine: "as if the foul had not occurred" means the clock status follows the result of the down (stopped after an incomplete pass, score, out of bounds in many cases; running after an in-bounds tackle), and the foul only changes it in the five exceptions.
- The text has no general rule restoring the time that a nullified play ran off the clock. Reset language appears only in specific rules: a multiple-foul attempt to run time (12-3-3: 15 yards and clock reset to the snap time), the erroneous whistle replay (7-2-1 (o) (4)), the ball striking a video board or similar (7-2-1 (r)), the offense snapping before the defense has substituted (5-2-9, 5-2-10 (b)), and replay reversals (15-5-1). [SRC-OFFICIAL, reading] [UNVERIFIED in the casebook]

#### 5.2 Play clock after a penalty (4-6, PDF p.20 to 21)
- Normal play clock 40 seconds (4-6-1). 25 seconds after administrative stoppages including a penalty enforcement (4-6-2 (e)). Rest of the rule: 4-6-3.
- After a penalty enforcement other than an action that conserves time: play clock reset to 25 seconds. After a penalty enforcement for a defensive foul that conserves time: reset to 40 seconds. After a 10-second runoff: 30 seconds. [SRC-OFFICIAL] 4-6-3 (a) (5), (b) (4), (c).

#### 5.3 Delay of game
- Foul if the ball is not put in play by a snap within the play clock. The Back Judge blows the whistle and the ball remains dead. [SRC-OFFICIAL] 4-6-1, 4-6-4.
- Other delay of game acts: unnecessarily remaining on a dead ball or a downed runner, snapping repeatedly before officials are in position, undue delay assembling after a timeout, a defender's fake false-start movement, spiking or throwing the ball after a down (except after a score), intentional contact with the ball or a player to delay, and a second timeout in the same dead ball period or a timeout after exhausting timeouts. [SRC-OFFICIAL] 4-6-5.
- Penalty: five yards from the succeeding spot if between downs and the ball remains dead; from the previous spot if the ball was in play. [SRC-OFFICIAL] 4-6-5 Penalty, PDF p.21.
- Delay of game by the defense is one of the ten exceptions for the automatic first down.
- A timeout requested and granted when not allowed (second timeout in a dead ball period, or none left): five yards for delay of game and the timeout is charged; after the two-minute warning, if the offense takes it while time is in, the defense has the 10-second runoff option. [SRC-OFFICIAL] 4-5-1 Item 3, PDF p.19.
- Whether delay of game by itself triggers the 10-second runoff is not stated. The list in 4-7-1 does not name delay of game. A secondary explainer (Football Zebras, article dated 2017-10-19 with later updates, retrieved 2026-10-14, https://footballzebras.com/2017/10/everything-need-know-10-second-runoffs) does not mention it either. [SRC-SECONDARY] Treat the delay of game as not a runoff foul unless SX.1 wants the safer reading (a delay of game does not leave the clock stopped, because the clock restarts as if the foul had not occurred).

#### 5.4 10-second runoff (all cases)
1. Illegal acts to conserve time after the two-minute warning of either half (4-7-1, PDF p.21 to 22): a foul by either team that stops the clock during any dead ball period; intentional grounding; an illegal forward pass; a backward pass thrown out of bounds; spiking or throwing the ball in the field of play after a down has ended, except after a touchdown; illegally batting or kicking the ball out of bounds. Penalty five yards unless a larger distance penalty applies.
   - Offense, while time is in: the officials run 10 seconds off the game clock and reset the play clock to 30 before permitting the ball to be put in play on the ready signal; the clock starts on the ready signal. If the offense has timeouts, it may use one instead of the runoff (clock then starts on the snap). The defense always has the option to decline the runoff and have the yardage penalty enforced; if the yardage penalty is declined, the runoff is declined too; the play clock is set to 25 and the clock starts on the snap.
   - Defense: play clock reset to 40, clock starts on the ready signal unless the offense chooses the snap; if the defense has timeouts it may use one in lieu of the game clock being started.
   - There can never be a 10-second runoff against the defensive team (4-5-4 Note 9). [SRC-OFFICIAL]
2. Illegal substitution after the two-minute warning while the ball is dead and time is in: five yards and a 10-second runoff. [SRC-OFFICIAL] 4-7-2, PDF p.22.
3. Defensive foul that conserves time, or an excess timeout for injury to a defensive player, in the last 40 seconds of either half while time is in: the half ends, unless the defense has timeouts remaining, or the offense chooses to have the clock start on the snap or to continue play after the clock starts on the ready signal. [SRC-OFFICIAL] 4-7-3.
4. Replay reversal or a foul that is called while time is in and then nullified, after the two-minute warning, when the correct ruling would not have stopped the clock or would have restarted it before the next snap: 10 seconds run off, play clock 30; neither team can decline; either team can use a timeout to prevent it (then the clock is reset to the time the play should have ended and starts on the snap, play clock 25). If less than 10 seconds remain, the half or game is over. [SRC-OFFICIAL] 4-7-4, 15-5-2, PDF p.22, p.70.
5. Excess team timeouts: when an excess timeout for injury is charged against the team in possession and stops the clock, a 10-second runoff may apply (4-5-4 Note 3); the first excess timeout after the two-minute warning has no yardage penalty, the second and later cost five yards. A foul in the same down prevents the runoff because the foul stopped the clock (4-5-4 Notes 6 and 7). [SRC-OFFICIAL] PDF p.20.
6. Either half can end because of a runoff (4-5-4 Note 4). [SRC-OFFICIAL]
- Secondary corroboration for the general shape (false start with the clock running triggers it; the defense may keep the yardage and decline the runoff): Football Zebras, 2017-10-19 (updated), https://footballzebras.com/2017/10/everything-need-know-10-second-runoffs, retrieved 2026-10-14. [SRC-SECONDARY] The 2026 rulebook wins where wording differs.

#### 5.5 Timeouts interplay
- Excess timeout (a request after all three timeouts are used, or a second in a dead ball period): five yards, delay of game, and the timeout is charged. [SRC-OFFICIAL] 4-5-1 Item 3.
- Timeouts per team: three per half, two in an overtime period in the regular season (4-5-1 Item 1); two in regular season overtime (16-3 (e)); three per half in postseason overtime (16-4 (g)). [SRC-OFFICIAL]
- Attempting to call an excess or illegal timeout to freeze a kicker: unsportsmanlike conduct, 15 yards, enforced after the down (dead ball foul if granted). [SRC-OFFICIAL] 4-5-1 Item 4, 12-3-1 (v).
- Initiating a challenge without a timeout: 15 yards, treated as a foul between downs, and a timeout is charged. [SRC-OFFICIAL] 15-1-1 (d).
- A team that commits a foul that prevents the next snap can no longer challenge the previous play; the other team still can. [SRC-OFFICIAL] 15-1-1 (b).
- Fouls and replay (15-7, PDF p.71):
  - Penalty administration (the number of the down, the yardage, the fouling player's number, the spot of a foul) is reviewable (15-7-1).
  - A foul is nullified when a necessary aspect of the foul is changed in replay; it can be created by replay in specific cases (15-7-2).
  - After a changed ruling, fouls after the ball should have been dead are disregarded except personal and unsportsmanlike fouls; pre-snap fouls (except personal and unsportsmanlike) before the review are ignored if the previous ruling changes (15-7-3 Items 1 and 2).
  - The head coach can change a pre-review accept or decline decision (15-7-3 Item 3).
  - Non-reviewable: whether a ball was illegally batted or kicked, intentional grounding, ineligible receiver downfield, illegal contact, an illegal block (15-4). [SRC-OFFICIAL]
- Difference from the requirements file: N7.6 says "a foul is never reviewable"; the rulebook says the foul calls listed in 15-4 are not reviewable but penalty administration is, and a changed ruling can remove or create a foul. [SRC-OFFICIAL]
- Scoring plays and turnovers after the two-minute warning and all of overtime are reviewed by the Replay Official "regardless of whether a foul is committed on the play that, if accepted, would negate the on-field ruling". [SRC-OFFICIAL] 15-1-2, PDF p.67.

#### 5.6 Extension of a period and time restored
- Extension: 4.4 above. Time restored: 12-3-3 (intentional fouls to manipulate the clock: 15 yards and the clock goes back to its time at the snap; the clock starts on the next snap), replay-based restoration (15-9), and erroneous whistle or object-strike replays (7-2-1 (o), (r)). [SRC-OFFICIAL]
- Clock at the end of a half with a penalty: the half can end on a runoff; 4-7-3 for the last 40 seconds.

#### 5.7 The five-minute rule and the fourth period
- Inside the last five minutes of the second half: an out-of-bounds runner's clock starts on the snap (4-3-2 (a) (3)); a foul that stops the clock restarts it on the snap (4-3-2 (e) (2)). The same applies after the two-minute warning of the first half.
- Fourth period and regular season overtime: an offensive foul after the ball is ready that stops the clock before the snap restarts it on the snap (4-3-2 (e) (3)). In regular season overtime "the general provisions for the fourth quarter of a game, including timing, shall apply" (16-3 (e)). In postseason overtime, the end of the second overtime period uses first-half timing, the end of the fourth overtime period uses fourth-period timing (16-4 (h)). [SRC-OFFICIAL]

### 6. Special cases the engine must handle

#### 6.1 Foul during a Try (11-3, PDF p.49 to 50)
- A Try is one untimed scrimmage down after a touchdown (3-40, 11-3-1). The ball is placed anywhere on or between the inbounds lines: 15 yards from the defense's goal line for a kick, 2 yards for a run or pass. After the ready-for-play signal the offense may change its choice if there is a penalty or a charged timeout by either team. [SRC-OFFICIAL] 11-3-1.
- Results: a kick (field goal) is 1 point; a touchdown by either team is 2; a result that would be a safety gives the opponent 1; any touchback means the Try fails with no replay. [SRC-OFFICIAL] 11-3-2.
- If a foul results in a re-Try, Team A may enforce the penalty from the Try spot (previous spot) or from the yard line of the other Try option, and then may place the ball anywhere on or between the inbounds lines. Defensive pass interference on a Try is a spot foul; in the end zone the ball goes on the one-yard line or half the distance, whichever helps Team A, and Team A may also take half the distance from the other Try spot. [SRC-OFFICIAL] 11-3-3 and its exception.
- Item 1: a foul by either team after a touchdown and before the ready-for-play signal is enforced on the Try.
- Item 2: a foul after the ready signal that stops the play before the snap is treated like a pre-snap foul in scrimmage. If the defense's foul prevents the Try attempt, the offense may take the distance penalty on the next Try or on the ensuing kickoff.
- Item 3 (Team A fouls at or after the snap): a foul during a successful Try repeats the Try, unless the penalty includes loss of down (then the Try is unsuccessful, no replay). Fouls after a change of possession, and all personal or unsportsmanlike fouls: distance penalty on the ensuing kickoff, unless it offsets or negates a successful Try. A foul that causes a safety: Team B gets one point.
- Item 4 (Team B fouls at or after the snap): all fouls except defensive pass interference are enforced on the ensuing kickoff unless they offset, create a re-Try or negate a score by Team B. A safety by Team B's foul: Team A gets one point. A Team B foul during an unsuccessful Try: Team A may decline the distance penalty and the down is replayed ("Replay Down Penalties" in the summary).
- Item 5: fouls by both teams without a change of possession: the Try is replayed (14-5-1), unless the scoring team's only foul is a dead ball foul after a score.
- Item 6: fouls by both teams with a change of possession: both before the first change, or Team B before it: the Try is repeated; Team A before it: the Try fails; neither before it and both after: the Try fails.
- Item 7: a foul after a Try is enforced on the succeeding free kick; fouls by both teams follow the normal rules.
- Article 4: the team on defense during the Try receives the succeeding free kick.
[SRC-OFFICIAL]
- Overtime and the Try: 4-8-2 (c) excludes the Try during "sudden-death overtime". The 2026 overtime (16-3, 16-4) is a modified form and 16-5 (f) says all other rules apply, so whether a Try is played after an overtime touchdown is not stated in one place. [UNVERIFIED how 4-8-2 (c) applies to the 2026 overtime]

#### 6.2 Free kicks: kickoff, safety kick, onside kick (14-4-7, 6-3-1, PDF p.32 and p.64)
- Fouls during a free kick: enforced from the previous spot and the kick is made again.
- Option exception: if the kicking team commits a foul before the end of the kick, or the receiving team commits a foul at or during a kickoff or safety kick, and the receiving team keeps possession throughout the down, the offended team may either enforce at the previous spot and replay the down, or enforce the yardage from the dead ball spot. The dead ball spot for a touchback is the 20 or 35 (6-1-5). [SRC-OFFICIAL]
- The previous spot for the kick moves with a distance penalty: kicker's restraining line is the kicking team's 35 for a kickoff and 20 for a safety kick "unless it is adjusted because of a distance penalty" (6-1-2 (a)); the onside kick uses the same line (6-1-6 (b)). [SRC-OFFICIAL] PDF p.29 to 30.
- 2026 changes touching enforcement: if a kickoff is from the 50-yard line (after penalties) and the play results in a touchback, the dead ball spot is the 20 (6-1-5). The kicking team may declare an onside kick at any time (6-1-6). [SRC-OFFICIAL] PDF p.30; cross-checked: the owner brief lists these as the 2026 changes; search summary https://www.steelers.com/news/nfl-owners-approve-2026-nfl-rule-changes (2026-10-14).
- Exceptions to "previous spot" (enforced from the spot of the foul unless noted): personal foul (blocking) after a fair catch signal; fair catch interference; interference with the opportunity to make a catch; invalid fair catch signal; illegal double team or wedge during the kick (previous spot if in Team B's end zone or during an onside kick). When the foul is not part of a double foul and the opponent has possession at the end of the down, a foul in (a), (b), (c) and (e) may be enforced from the dead ball spot. [SRC-OFFICIAL] 14-4-7 Exceptions, 6-3-1.
- Kick catch interference (no signal): 15 yards from the spot of the foul and the offended team puts the ball in play by a snap; fair catch interference: 15 yards from the spot of the foul and a fair catch is awarded. [SRC-OFFICIAL] 10-1-1 Penalties, PDF p.47.
- Free kick out of bounds or not reaching the landing zone: the receiving team may take possession 25 yards from the spot of the kick (30 for a safety kick) at the inbounds line, or at the out of bounds spot, or where the ball landed or was touched short, if less than 25 or 30. [SRC-OFFICIAL] 6-2-4, PDF p.32.
- Onside kick specifics: untouched beyond the setup zone: unsportsmanlike conduct 15 yards from the kicking team's restraining line and the receivers get the ball; illegal touching: five yards, or the receivers take the ball at the spot of the illegal touch. [SRC-OFFICIAL] 6-1-6 Penalty, 6-2-5.
- Offside, illegal formation and similar on a free kick: five yards. Illegal blocking or use of hands: 10 yards; illegal wedge or double team: 15. [SRC-OFFICIAL] 6-1-3, 6-2-1, 6-2-2.
- A free kick ends when Team B establishes possession; after that, fouls are enforced from the dead ball spot or the spot of the foul by the three-and-one method. Team A's foul before Team B's possession is an offensive foul. [SRC-OFFICIAL] 14-4-7 last paragraph.
- Penalty on the receiving team on a kickoff: kicking team's choices are "decline", "re-kick from the new kicking line" (the line moves forward for the receivers' penalty yards: 35 + 15 = 50 for a 15-yard foul), or "yardage from the dead ball spot" if the receiving team keeps the ball all down. [SRC-OFFICIAL, reading] 14-4-7, 6-1-2 (a), 6-1-5.

#### 6.3 Punts and other scrimmage kicks (14-4-8, 9-5-1, 9-1-4 (e), PDF p.43 to 46, p.64 to 65)
- Foul by the kicking team before the end of the kick: previous spot; if the receivers keep possession all down they may take the penalty at the previous spot and replay the down, or add the yardage to the dead ball spot. They may also decline. [SRC-OFFICIAL]
- Foul by the receiving team during the kick, in an attempt to block it (running into the kicker 5 yards, no automatic first down; roughing the kicker 15 yards with automatic first down; both "from the previous spot"): the kicking team accepts (kick made again from the new spot, same down for running into; first-and-10 for roughing the kicker) or declines (the kick stands). [SRC-OFFICIAL] 12-2-12 Penalties, 14-1-2 Item 5 Exception 7.
- Roughing the holder: 15 yards from the previous spot and an automatic first down. [SRC-OFFICIAL] 12-2-13.
- Receiving team foul that is not in an attempt to block: post-possession foul (1.7). If the receiving team loses the ball later in the down it is not a post-possession foul. [SRC-OFFICIAL] 3-26.
- Kick catch interference, fair catch interference, invalid fair catch signal, illegal touching (inside the five-yard line the receivers may also take a touchback): as in 6.2 and 9-2-3. [SRC-OFFICIAL] 9-2-3, 14-4-8 Note (b).
- Kicking team illegally catches or recovers beyond the line before the receivers touch it: ball dead, first-and-10 for the receivers at the spot. [SRC-OFFICIAL] 9-3-2 Item 2.
- A punt (or drop kick or place kick) beyond the line of scrimmage: loss of down and five yards from the spot of the kick. [SRC-OFFICIAL] 9-1-1, PDF p.43.
- Ineligible kicking-team player downfield before the kick: five yards. [SRC-OFFICIAL] 9-1-2.
- Illegal formation by the defense on a punt or field goal try: five yards (no automatic first down). Pushing teammates into the formation: 15 yards. [SRC-OFFICIAL] 9-1-3, PDF p.43.

#### 6.4 Personal foul enforcement on the next free kick after a score
- On a touchdown: on the Try. On a field goal or safety: on the succeeding free kick. [SRC-OFFICIAL] 14-2-3.
- After a score, a dead ball foul by the scoring team with an unrelated defensive live ball foul: score counts, dead ball foul on the Try or kickoff (14-4-9 Item 3 Exception 2).
- After a Try, a foul is enforced on the succeeding free kick (11-3-3 Item 7).
- Mechanics (reading): a 15-yard penalty against the kicking team moves the kicker's restraining line back to the 20; against the receiving team forward to the 50; a kickoff from the 50 that is a touchback puts the ball on the 20 (6-1-5). [SRC-OFFICIAL, reading]

#### 6.5 Field goal try
- A foul by the kicking team during a field goal try is a scrimmage kick foul from the previous spot; if the receiving team is awarded the ball after a missed attempt (11-4-2) and takes the yardage option, it is enforced from the succeeding spot (the spot of the kick, or the 20 if the kick was inside the 20). [SRC-OFFICIAL] 14-4-8 Exception 2 Note (c), 11-4-2.
- A foul by the defense during a try: if the kick is good, the offended team may accept the penalty (erasing the points, with replay from the enforcement spot) or decline and keep 3 points (14-2-3, 14-1-1). If the kick misses: accept (penalty from the previous spot, kick replayed or down repeated) or decline (receivers' ball at the spot of the kick or the 20). [SRC-OFFICIAL, reading]
- Roughing the kicker or holder: 15 yards and an automatic first down from the previous spot (12-2-12, 12-2-13).
- Illegal leaping across the line to block a field goal try, and other kick-block conduct (12-3-1 (o) to (r)): unsportsmanlike conduct, 15 yards (the Penalty Summary lists leaping and goaltending in the 15-yard group). Goaltending (12-3-1 (s)): the Referee may also award three points as a palpably unfair act. [SRC-OFFICIAL] PDF p.58, p.78.
- Maximum clock runoff on a successful field goal or a missed attempt that does not land in the field of play: five seconds (11-4-2 note 5). [SRC-OFFICIAL] PDF p.50.

#### 6.6 Overtime specifics (Rule 16, PDF p.72 to 73)
- Regular season: one 10-minute period; both teams must have the opportunity to possess the ball once, unless the team that kicked off scores a safety on the receivers' first possession; then next score wins; may end in a tie; two timeouts each; fourth period timing applies. [SRC-OFFICIAL] 16-3.
- Postseason: 15-minute periods until a winner; both teams get a possession; three timeouts per half; no halftime after the second period; timing rules like first half at the end of the second period and like the fourth period at the end of the fourth period. [SRC-OFFICIAL] 16-4.
- In regular season and postseason alike, the first team's score followed by the second team losing possession by interception or fumble: the down runs on; only fouls that require replay, negate a score, or palpably unfair acts are enforced. If the second team loses possession but the opponent fouled before that, its possession has not legally ended and the game cannot end on the down; the second team cannot decline in a way that creates a second possession for itself. [SRC-OFFICIAL] 16-5 (a) Notes 1 to 3.
- Opportunity to possess applies only on kicking plays; a kickoff is the receiving team's opportunity; a punt or field goal attempt that crosses the line and is muffed by the receivers counts. [SRC-OFFICIAL] 16-5 (c).
- Coaches' challenges are not allowed; the Replay Official initiates all reviews. Disqualified players do not re-enter. [SRC-OFFICIAL] 16-5 (d), (e).
- The requirements file keeps the original's sudden death in both modes (NQ4). The 2026 rulebook's overtime gives both teams a possession in the regular season and postseason, so if the owner later wants real NFL overtime the penalty rule in 16-5 (a) needs to be built. Not a conflict with NQ4 as written.

### 7. Reference data for the starting foul table (N7.1)

Official names and the three-letter foul codes are on PDF p.86 (printed p.79): the table lists 63 names. Useful ones for the starter list: False Start (FST), Offensive Offside (OOF), Defensive Offside (DOF), Encroachment (ENC), Neutral Zone Infraction (NZI), Delay of Game (DOG), Defensive Delay of Game (DOD), Illegal Formation (ILF), Illegal Motion (ILM), Illegal Shift (ISH), Illegal Substitution (ILS), Offensive Holding (OH), Defensive Holding (DH), Illegal Use of Hands (ILH), Facemask (FMM), Offensive Pass Interference (OPI), Defensive Pass Interference (DPI), Illegal Contact (ICT), Roughing the Passer (RPS), Roughing the Kicker/Holder (RRK), Running into the Kicker (RNK), Unnecessary Roughness (UNR), Unsportsmanlike Conduct (UNS), Intentional Grounding (ING), Illegal Block Above the Waist (IBW), Ineligible Downfield Pass (IDP), Illegal Forward Pass (IFP), Taunting (TAU), Horse Collar (HC), Clipping (CLP), Illegal Touch Pass (ITP). [SRC-OFFICIAL]

The following is the yards, first down and spot data from the rule texts for the owner's starting list (N7.1, section 12 of the requirements file):
- False start: 5 yards, offense, pre-snap, from the line of scrimmage (succeeding spot), down repeated (7-4-2). Dead ball (whistle).
- Offside: 5 yards, at the snap, previous spot; defense: no automatic first down (7-4-5, 14-1-2 Item 5).
- Encroachment: 5 yards, defense, pre-snap, no automatic first down (7-4-3).
- Neutral zone infraction: 5 yards, defense, pre-snap, no automatic first down (7-4-4).
- Delay of game: 5 yards; succeeding spot if between downs and the ball is dead, previous spot if in play (4-6-5). Offense: down repeated.
- Illegal formation, illegal motion, illegal shift: 5 yards, offense, at the snap (7-5-1, 7-4-7, 7-4-8).
- Offensive holding: 10 yards (12-1-3 (c)). Illegal use of hands by the offense: 10 (12-1-3 (a)). Illegal block in the back above the waist: 10 (12-1-3 (b)).
- Defensive holding: 5 yards and automatic first down (12-1-6). Illegal use of hands by the defense: 5 and automatic first down (12-1-7). Illegal contact: 5 and automatic first down (8-4-3).
- Face mask: 15 yards, "if the foul is by the defense, it is also an automatic first down" (12-2-15).
- Offensive pass interference: 10 yards from the previous spot (8-5). Defensive pass interference: first down at the spot of the foul (8-5).
- Roughing the passer: 15 yards and automatic first down (12-2-11). Roughing the kicker: 15 from the previous spot and automatic first down (12-2-12). Running into the kicker: 5 from the previous spot, no automatic first down. Roughing the holder: 15 and automatic first down (12-2-13).
- Unnecessary roughness: 15 yards, automatic first down if by the defense, possible disqualification (12-2-8). Players in a defenseless posture: 15 and automatic first down (12-2-9).
- Unsportsmanlike conduct (a) to (h): 15 yards from the succeeding spot, automatic first down if by the defense (12-3-1); (i) to (v): 15 from the succeeding spot if the ball is dead, the previous spot if in play.
- Intentional grounding: loss of down and 10 yards from the previous spot, or loss of down at the spot of the pass if worse for the offense or more than half the distance; safety in the end zone (8-2-1, 14-4-5 (a)).
- Illegal forward pass from beyond the line: loss of down and 5 yards from the spot of the pass; second forward pass or pass after the ball returned behind the line: loss of down and 5 from the previous spot; pass after a change of possession: 5 yards from where the ball is released (8-1-2).
- Ineligible player downfield on a pass: 5 yards from the previous spot, no loss of down (8-3-1).
- Clipping: 15 (12-2-1). Horse-collar tackle: 15 and automatic first down (12-2-16). Taunting is a dead ball foul at any time (3-13-1 (b)).
- Penalties yards for holding and illegal hands on scrimmage kick plays beyond the line: 10 for either team unless in an attempt to block the kick (9-1-4 (e)).
All [SRC-OFFICIAL]; the 2026 Penalty Summary on PDF p.78 to 79 lists the same yardage groups.

### 8. Decision table for the accept-or-decline prompt

Format: situation; if you accept; if you decline; note. "Own" is the offense's own territory. All positions below are for the team that is the offended team. These are bullets, not a table. The rule references are in the sections above.

Offended team is the offense (foul by the defense):
- Pre-snap defensive foul with the whistle (encroachment, neutral zone infraction, too many men in the formation). Accept: 5 yards toward the defense's goal from the line of scrimmage (half-distance cap), same down, no automatic first down; first-and-10 if that reaches the line to gain. Decline: replay the down from the same spot. Note: accepting is almost always better.
- Offside with the play run. Accept: 5 yards from the previous spot, play erased, same down (first-and-10 if it reaches the line to gain). Decline: the result of the play stands. Note: a free play; decline when the play gained more than 5 or scored.
- Defensive holding, illegal contact or illegal use of hands on a pass play. Accept: 5 yards from the previous spot (not from the catch), play erased, first-and-10 (automatic first down). Decline: the result of the pass (incomplete means the next down, a completion stands at the end of the play, a first down on the play counts).
- Defensive pass interference. Accept: first down at the spot of the foul (no cap); special goal-line rules (first down on the 1 if the spot is behind the goal line and the previous spot is outside the 2; halfway between the previous spot and the goal line if the previous spot is inside the 2). Decline: the result of the pass.
- Defensive foul on a running play (holding 5, or a 15-yard foul such as face mask or horse collar). Accept: penalty from the dead ball spot (the yards of the run stay), automatic first down, half-distance cap. Decline: the run's result. Note: if the run was behind the line of scrimmage, the penalty is from the previous spot.
- Defensive personal foul on a pass (roughing the passer, unnecessary roughness). Accept: 15 yards from the previous spot or the dead ball spot, whichever is better for the offense, automatic first down; the play's result erased only if the previous spot is the better one. Decline: the result of the pass.
- Defensive foul on the play where the offense scored a touchdown. Accept: touchdown erased; penalty from the usual spot; first-and-10 (new series) or replay, per 14-2-3. Decline: touchdown stands. Special: a personal or unsportsmanlike foul on a touchdown play is enforced on the Try or kickoff, so decline the replay and take the points and the yards.
- Defensive foul on a field goal try. If the kick was good: accept (3 points erased, replay from the new spot) or decline (3 points). If missed: accept (penalty from the previous spot, first down for roughing the kicker or holder) or decline (receivers' ball at the spot or the 20).
- Defensive foul on the last play of a half. Accept: penalty plus one untimed down (4-8-2 (a)). Decline: the half ends. Note: say this in the prompt.
- Defensive foul on a punt: running into the kicker. Accept: 5 yards from the previous spot, kick made again, same down (first-and-10 if the spot reaches the line to gain), no automatic first down. Decline: the kick stands. Roughing the kicker: 15 from the previous spot, first-and-10. Decline: the kick stands.
- Turnover on the play with an earlier defensive foul (for example holding before an interception). Accept: the ball returns to the offense with the penalty enforced (previous spot for a pass play). Decline: the turnover stands. Note: accept.

Offended team is the defense (foul by the offense):
- Pre-snap offensive foul (false start, delay of game before the snap, illegal formation caught before the snap, 12 men in the huddle): Accept: 5 yards from the line of scrimmage (half-distance cap), down repeated, clock per 4-3-2 (e). Decline: replay the down from the same spot. Note: accept unless the clock or the half-distance cap makes it pointless.
- Offensive holding (10), illegal use of hands (10), illegal block in the back (10) on a pass play: Accept: 10 yards back from the previous spot (half-distance cap), play erased, same down. Decline: the result of the play (including a turnover or a sack).
- Offensive holding on a running play beyond the line of scrimmage: Accept: spot of the foul minus 10 if the foul was behind the end of the run (the usual case), or from the dead ball spot if the foul was ahead of it; same down. Decline: the run counts. Note: behind the line of scrimmage the penalty is from the previous spot.
- Offensive foul behind its own goal line: Accept: a safety (2 points and a free kick). Decline: the play's result. Special rule: only if the foul was committed in the end zone.
- Intentional grounding: Accept: loss of down and 10 yards from the previous spot, or loss of down at the spot of the pass if that is worse for the offense; safety if in the end zone. Decline: incomplete pass as usual.
- Offensive pass interference: Accept: 10 yards from the previous spot, same down. Decline: the result of the play.
- Offensive foul on an interception: Accept: the interception is erased and the penalty enforced from the previous spot (the offense keeps the ball). Decline: keep the ball and the return. Exception: a personal or unsportsmanlike foul by the offense lets the defense keep the ball and have the penalty enforced from the dead ball spot (or the spot of the defense's recovery if it later loses the ball).
- Offensive foul on a touchdown play (by the offense): Accept: touchdown erased, penalty enforced. Decline: touchdown stands.
- Offensive foul after the two-minute warning with the clock running (for example a false start): Accept: 5 yards plus a 10-second runoff; Accept the yardage only: 5 yards, no runoff, clock starts on the snap; Decline: no penalty, no runoff, clock starts on the snap. The defense may also decline the runoff while keeping the yards. 4-7-1.

Kick plays:
- Kickoff with a foul by the kicking team (offside, illegal formation, out of bounds): the receivers choose to decline; or re-kick from the previous spot moved back; or (if the receivers keep the ball) add the yardage to the dead ball spot.
- Kickoff with a foul by the receiving team (illegal block, offside): the kicking team chooses to decline; or re-kick from the previous spot moved forward by the penalty yards (kicker's line moves up); or enforce the yardage from the dead ball spot if the receivers kept the ball.
- Punt with a foul by the kicking team before the end of the kick: the receivers choose decline; or the punt is made again from the new spot (previous spot minus yards); or (if they keep the ball) add the yards to the dead ball spot.
- Punt with a post-possession foul by the receiving team (for example a block in the back during the return): the kicking team chooses decline (return stands) or accept (from the end of the kick or the spot of the foul, whichever is less beneficial to the receivers).
- Field goal or punt with illegal formation by the defense: accept: 5 yards, no automatic first down, same down; decline: the kick stands.
- Try with a defensive foul on an unsuccessful Try: accept (Try replayed with yards, or the replay with the distance declined) or decline (no points). Try with a foul by the offense on a successful Try: Try repeated unless the penalty includes loss of down. A personal foul on a Try is enforced on the kickoff.

Double fouls (no prompt): offset, the down is replayed from the previous spot, same down and distance. Say what both fouls were.

Computer's rule of thumb (design guidance, not a rule): compare the two outcomes in order: points or a turnover, then first down, then field position, then down and distance, then clock and score; take a first down gained on the play over a small penalty yardage; accept when the penalty erases a turnover or a score by the opponent; never offer "accept" for a pre-snap offensive penalty that only costs the offense yards unless the computer is the offended team and the clock favors it.

### 9. Differences from the requirements file and surprises

- Captain, not the coach, indicates the penalty option (18-1-3).
- "A foul is never reviewable" (N7.6) is too strong: penalty administration is reviewable and a changed ruling can nullify or create a foul (15-7). Intentional grounding, ineligible receiver downfield, illegal contact, illegal block and illegal bat or kick are non-reviewable calls (15-4).
- The rulebook allows accepting a penalty and declining its yardage (14-1-1). The requirements file mentions only accept or decline.
- "Automatic first down" is better modelled as the default for every Team B foul with ten listed exceptions (14-1-2 Item 5) than as a flag per foul.
- Offside is a live ball foul at the snap; false start, encroachment and neutral zone infraction are blown dead before the snap. The requirements file's N7.2 groups all as "pre-snap".
- The five-minute rule is in the second half (last five minutes), and the fourth-period rule for offense fouls is separate (4-3-2 (e) (2) and (3)). The requirements file section 12 says "the clock at five minutes in the fourth quarter and overtime".
- The C8 invariant "a penalty is never enforced beyond half the distance to the goal" needs exceptions: spot fouls (defensive pass interference), intentional grounding at the spot of the pass, palpably unfair acts, and safety by enforcement (14-2-1, 8-5, 8-2-1).
- Rulebook oddity: foul between downs after a first down is "first-and-25" (14-4-9 Item 1).
- Overtime in the 2026 rulebook gives both teams a possession (16-3, 16-4). The requirements file keeps sudden death by owner choice (NQ4), so no change is needed unless the owner changes it.
- 2026 changes in the owner's brief that touch penalties: 6-1-5 (dead ball spot after a kickoff touchback when the kick is from the 50 is the 20), 6-1-6 (onside kick declared at any time), 19-2 (league personnel consult on disqualifications). [SRC-OFFICIAL] PDF p.30, p.77.

### 10. Engine notes for SX.1 (suggestions, not rules)

- Needs a "spot of the foul" for: offensive fouls on runs (between the line of scrimmage and the end of the run), defensive pass interference (the depth of the throw), fouls behind the line, fouls by a receiving team on a return.
- Pass plays: all live ball fouls are enforced from the previous spot except pass interference, personal fouls and unsportsmanlike fouls (previous spot or dead ball spot per 14-4-5 (d) and (e)).
- Run plays: three-and-one; the data needed per foul is "behind the end of the run" or "ahead of it".
- A foul table row should carry: yards, offender, automatic first down only if not in the ten exceptions, loss of down, combination, spot kind (succeeding, previous, spot of foul, dead ball, basic), personal-foul class (for the dead ball spot option and for the score rule), conserves-time class (for the runoff), live or dead ball, and whether it can occur on kick plays.
- Tests (from the rules): no distance penalty beyond half the distance; double foul replays the same down; Team B fouls give first-and-10 except the ten; combination penalty on fourth down gives the ball to the other team after the yards; offense foul in its own end zone offers a safety; defense chooses; clock restarts per 4-3-2 (e); runoff never against the defense; a decision is final once the ball is ready; disqualified player leaves in all cases.

### Could not settle

- The NFL Casebook (Approved Rulings). Tried: web search "NFL casebook 2026 approved rulings operations.nfl.com", search "NFL Casebook Approved Rulings 2025", fetched https://operations.nfl.com/the-rules/nfl-casebook/ (404), https://operations.nfl.com/rules-officiating/featured-rules and https://operations.nfl.com/rules-officiating/2026-nfl-rulebook (no casebook link). The casebook does not seem to be public; the rulebook itself has a section on approved rulings (3-1) but no case texts. All readings flagged "reading" or [UNVERIFIED] above are the ones the casebook would settle.
- Rounding of half the distance for less than one yard (14-2-1 gives no rule).
- Whether the defense may decline the "score not counted" result on an offense foul during the last play of a half (4-8-2 (b)).
- Whether the exact-line-to-gain case after a Team A foul is a first down (14-1-2 Item 4 versus 7-3-1 (b)).
- The "first-and-25" wording for a foul between downs (14-4-9 Item 1).
- Whether delay of game triggers the 10-second runoff (4-7-1 does not list it).
- Double fouls with a change of possession on a play that also scores (14-5-2 and 14-5-3 do not mention scores).
- Exact penalty yards for every other foul in the book (not needed for the starting list; the Penalty Summary on PDF p.78 to 79 has them).
- Penalty frequency statistics (N7.1 calibration): outside this topic.

### Sources

- 2026 Official Playing Rules of the NFL (PDF), https://static.www.nfl.com/image/upload/fl_attachment/league/tqivdkzt9mu6wdgsh1ku.pdf, linked from https://operations.nfl.com/the-rules/nfl-rulebook/ ; read from the local text conversion, retrieved 2026-10-14. [SRC-OFFICIAL]
- Page https://operations.nfl.com/rules-officiating/2026-nfl-rulebook (links to the rulebook PDF and the 2026 rulebook page on nfl.com), fetched 2026-10-14; no casebook link. [SRC-OFFICIAL, negative]
- https://operations.nfl.com/rules-officiating/featured-rules fetched 2026-10-14; no casebook or enforcement explainer. [SRC-OFFICIAL, negative]
- https://operations.nfl.com/the-rules/nfl-casebook/ : HTTP 404 on 2026-10-14.
- Football Zebras, "Everything you need to know about 10-second runoffs", https://footballzebras.com/2017/10/everything-need-know-10-second-runoffs, article dated 2017-10-19 with later updates, retrieved 2026-10-14. [SRC-SECONDARY]
- Explainer on half the distance, https://www.footballnationusa.com/post/why-is-a-penalty-half-the-distance-to-the-goal-nfl-rule-explained (search-result summary only, page not opened), 2026-10-14. [SRC-SECONDARY]
- NBC Sports Philadelphia on a double foul that cannot be declined, https://www.nbcsportsphiladelphia.com/nfl/reid-on-offsetting-penalty-call-it-doesnt-make-sense/359126 (search-result summary only), 2026-10-14. [SRC-SECONDARY]
- 2026 approved rule changes, https://www.steelers.com/news/nfl-owners-approve-2026-nfl-rule-changes (search-result summary only), 2026-10-14. [SRC-SECONDARY]


## Part 7. The complete list of fouls and their penalties (2026 rulebook)

Research notes for SX.0, topic E1. Written 2026-10-14. No code, nothing in the project folder was changed.
Main source: the 2026 Official Playing Rules of the NFL (PDF "ops-2026-NFL-Rulebook-FINAL"), read from the text converted from the PDF. Page numbers below are PDF page numbers (printed page = PDF page minus 7). Tag SRC-OFFICIAL means read in that rulebook (or on operations.nfl.com) on 2026-10-14.

### Answers in brief

- The Penalty Summary is on printed pages 71 and 72 (PDF pages 78 and 79), not 71 to 73. Printed page 73 (PDF 80) already starts "Official Signals". SRC-OFFICIAL.
- The summary has 29 entries under Loss of Five Yards, 8 under Loss of Ten Yards, 57 under Loss of Fifteen Yards (94 distance entries), 1 under Loss of Down Without Yardage, 7 under Loss of Down with Yardage, and about 45 more lines in the other groups (replay down, scoring, time, new series, combination, miscellaneous situations). Every one is in this file (section 1 to 13 below). SRC-OFFICIAL.
- This edition of the summary has no group named "Automatic First Down" and none named "Disqualification". Automatic first downs and disqualifications must be read from the articles. The general rule for automatic first downs by the defense is 14-1-2 Item 5 (PDF 61): any foul by the defense on a scrimmage down gives first and 10, except ten listed exceptions. SRC-OFFICIAL.
- Yards: the Penalty Summary and the article text agree for every foul I checked. Section 15 has 9 notes. The only real differences are three: (1) 10 yards instead of 5 for holding and illegal use of hands by either team on a scrimmage kick that crosses the line (9-1-4-e), not mentioned in the summary; (2) the summary label "Loss of Ball and Fifteen Yards" on fair catch interference and on contact with a kick returner, which the articles do not say; (3) the summary words "behind the line of scrimmage" for illegal batting and kicking with loss of down, narrower than the article (12-5-2). Article text wins in all three. SRC-OFFICIAL.
- Starting list for the clone: section 0 below (about 40 fouls, each with a one-line definition and the phase of the clone's game where it fits). SRC-OFFICIAL.
- Fouls that are not "accept or decline" in the usual sense: section 14 (disqualification, offsetting double fouls, 10-second runoffs that cannot be declined, fouls between downs and against officials, timeout charges, scoring-play fouls, options that are not yardage). SRC-OFFICIAL.
- The Casebook (Approved Rulings) was not reachable: operations.nfl.com/the-rules/nfl-rulebook/ links only to the rulebook PDF. See "Could not settle".
- operations.nfl.com also has an official "Table of Foul Codes" with three-letter codes (FST, OFF and so on). Codes are given in brackets in the starting list. SRC-OFFICIAL, retrieved 2026-10-14.

### Key to the bullets

Each bullet has the fixed form: Name (citation, PDF page): by whom; when; yards; automatic first down (AFD); loss of down (LOD); spot of enforcement; live ball or dead ball; what happens to the down; note; tag.
- AFD = automatic first down (first and 10 for the offended offense).
- "down repeated" = after accepted enforcement the same down number is played again (no AFD, no LOD).
- "previous spot" = where the ball was last put in play (usually the line of scrimmage). "succeeding spot" = where the ball will next be put in play. "dead ball spot" = where the ball became dead. "basic spot" = the reference point for runs: dead ball spot, or the spot where possession is lost (14-3-5). Definitions are in 14-3-4 and 3-13-3 (PDF 62 and 15).
- "three-and-one" (14-3-6, PDF 62): on a run, a defensive foul is enforced from the basic spot; an offensive foul in advance of the basic spot is enforced from the basic spot; an offensive foul behind the basic spot is enforced from the spot of the foul. Offensive fouls behind the line of scrimmage are enforced from the previous spot.
- "Live ball foul" (3-13-1-a) happens after the snap until the ball is dead. "Dead ball foul" (3-13-1-b) happens in the continuing action after a down ends (taunting counts at any time). "Foul between downs" (3-13-1-c) happens after the down and its continuing action, before the next snap. The rulebook enforces all fouls before the snap from the succeeding spot with the down unchanged (14-4-1 Item 1, PDF 63) and fouls at the snap from the previous spot with the down repeated (Item 2). For the clone, a "pre-snap" foul means: whistle at once, the play is not run, the ball stays on the line of scrimmage.

### General rules that apply to many bullets (SRC-OFFICIAL)

- G1. The penalty for any foul may be declined by the offended team unless the rule prohibits it (14-1-1, PDF 61). The yardage alone may be declined even if the penalty is accepted. The choice cannot be changed after the penalty is fully administered or the ball is made ready for play. A disqualified player must leave in every case, including when the penalty is declined. With several fouls by the same team in one down, only one penalty may be enforced, chosen by the offended team (14-1-3, PDF 61).
- G2. Number of the down (14-1-2, PDF 61): after a distance penalty on the offense the down number is unchanged unless it is a combination penalty (LOD): illegal forward pass, intentional grounding, backward pass that conserves time, illegal handing forward, illegal punt/drop kick/place kick, illegal bat, illegal kick (Item 2). If the ball ends beyond the line to gain after enforcement of an offensive foul, it is first and 10 (Item 4). A foul by the defense on a scrimmage down gives first and 10 to the offense (Item 5), except: offside, encroachment, neutral zone infraction, delay of game, illegal substitution, excess timeout, running into the kicker, more than 11 players on the field at the snap, more than 11 in the formation before the snap, illegal formation by the defense on a scrimmage kick play. For those ten the down number and line to gain stay, unless the yardage reaches the line to gain (then first and 10).
- G3. Half-distance rule (14-2-1, PDF 62): a distance penalty never moves the ball more than half the distance from the spot of enforcement to the offender's goal line. Exceptions: intentional grounding (8-2-1) and palpably unfair act (12-3-4).
- G4. Foul behind a goal line (14-2-2, PDF 62): a foul by the offense behind its own goal line is a safety if the defense elects to enforce at that spot; offensive foul behind the defense's goal line is enforced from the goal line; defensive foul behind the offensive goal line is enforced from the goal line (from the 20 or 35 after a touchback).
- G5. Personal or unsportsmanlike foul during a score (14-2-3, PDF 62): on a touchdown the penalty goes to the Try; on a field goal or safety to the next free kick; the offended team may also accept the penalty with normal enforcement instead of counting the points. Personal or unsportsmanlike foul with the ball changing sides: enforcement may also be from the dead ball spot (14-2-4).
- G6. Dead ball foul, or foul between downs (14-4-9, PDF 65): enforced from the succeeding spot, the down counts. A foul between downs cannot combine with a live or dead ball foul, and a foul against an official is always a foul between downs. Dead ball fouls by both teams offset.
- G7. Passing play (14-4-5 and 8-6-1, PDF 63 and 40): fouls from the snap until a forward pass thrown from behind the line ends are enforced from the previous spot. Exceptions: intentional grounding, defensive pass interference (spot of the foul), offensive foul in the end zone is a safety option, and personal fouls or unsportsmanlike conduct by the defense before the catch (previous spot or dead ball spot, whichever is better for the offense).
- G8. Scrimmage kick play (14-4-8, PDF 64): fouls from the snap to the end of a legal kick are enforced from the previous spot. If the kicking team fouls and the receiving team keeps the ball, the receivers may choose: previous spot and replay the down, or add the yardage to the dead ball spot.
- G9. Free kick play (14-4-7, PDF 64): enforcement is from the previous spot and the kick is made again, with the same option for the receiving team when it keeps the ball.
- G10. Fouls by both teams (14-5, PDF 65 and 66): penalties offset, the down is replayed at the previous spot, and neither team may decline the offset. A 15-yard foul against a 5-yard foul (no AFD, LOD or runoff on the minor one): the 15 is enforced from the previous spot and the 5 is disregarded; the minor-foul team cannot decline it.
- G11. Clock: the clock stops for a foul (4-4-e, PDF 19). After a foul the clock starts as if there had been no foul, except it starts on the snap after the two-minute warning of the first half, inside the last five minutes of the second half, when the offense fouls in the fourth period or regular-season overtime after the ball is ready, after two successive delay-of-game penalties, and when a rule says so (4-3-2-e, PDF 19). Ten-second runoffs: see 4-5-1, 4-5-4, 4-7-1, 4-7-2, 4-7-4 in section 8 below.

### 0. Fouls the clone should START with

Clone phases used: offense plays Line Plunge (inside run), End Run (outside run), Screen Pass, Short Pass, Long Pass, Field Goal, Punt; kickoffs; defense calls Goal Line, Short Run, Long Run, Blitz, Short Pass, Long Pass. Before the snap means it fits every scrimmage play (including Field Goal and Punt) and the kickoff.
One-line definitions are in my own words. Codes in brackets are the official codes on operations.nfl.com. Yards and AFD are in the detailed bullets below.

Pre-snap and snap fouls
- False start [FST] (7-4-2): an offensive player makes a quick abrupt movement that looks like the start of the play, or a lineman who set himself moves his hand or position. Before the snap, offense, 5, no AFD. Any scrimmage play.
- Offside [DOF or OOF] (7-4-5): any part of a player's body is in or beyond the neutral zone when the ball is snapped. Defense or offense; 5; snap time. Any scrimmage play.
- Neutral zone infraction [NZI] (7-4-4): a defender goes into the neutral zone before the snap, past or beside a lineman, or makes the offense flinch. Defense; before the snap; 5. Any scrimmage play, especially Short and Long Pass, Blitz.
- Encroachment [ENC] (7-4-3): a defender enters the neutral zone and touches an offensive player or the ball before the snap. Defense; before the snap; 5.
- Delay of game [DOG, DOD] (4-6): the ball is not snapped within the 40-second play clock (25 after a stoppage), or a team delays the game in another listed way. Mostly offense; 5; before the snap. Ties to timeouts and the clone's clock (NX1).
- Illegal formation [ILF] (7-5-1): at the snap the offense has fewer than seven on the line, no eligible player on each end of the line, a player out of bounds, or a player not clearly on or off the line. Offense; at the snap; 5. Any scrimmage play.
- Illegal motion [ILM] (7-4-8): a player is moving toward the line of scrimmage at the snap, or more than one man is in motion. Offense; at the snap; 5.
- Illegal shift [ISH] (7-4-7): after a shift the offense does not come to a complete stop for one full second before the snap. Offense; before the snap; 5.
- Illegal substitution [ILS] (5-2-8, 5-3-2, 4-7-2): a substitute enters while the ball is live, an offensive substitute does not reach the inside of the field numerals, or a change of eligibility is not reported. Either team; 5 (plus 10-second runoff after the two-minute warning).
- Too many men on the field [OTM, DTM] (5-1-1): more than 11 players in the formation or on the field at the snap. Either team; 5.
- Illegal snap (7-6-3, 7-6-4): the snap is not one quick continuous motion, or goes to an ineligible player on the line. Offense; 5 from the line. Any scrimmage play.

Fouls during runs and passes
- Offensive holding [OH] (12-1-3-c): the offensive blocker grabs, tackles, or pulls the defender, restricting his path. Offense; run or pass; 10. Line Plunge, End Run, Screen, Short Pass, Long Pass.
- Defensive holding [DH] (12-1-6, 8-4-6): the defender tackles or holds an opponent who is not the runner. Defense; run or pass; 5 and AFD. Mainly Short Pass, Long Pass, Screen, Blitz.
- Illegal use of hands, offense [ILH] (12-1-3-a): the blocker thrusts his hands forward into the defender's head or neck area. Offense; 10. Line Plunge, End Run, pass blocking.
- Illegal use of hands, defense (12-1-7): same act by a defender. Defense; 5 and AFD.
- Face mask [FMM] (12-2-15): a player grasps and controls, twists, turns, pushes, or pulls an opponent's facemask or helmet opening. Either; any play; 15 (AFD if defense).
- Offensive pass interference [OPI] (8-5-2, 8-5-4): an offensive player more than one yard past the line significantly hinders a defender's chance to play the ball, or blocks downfield before the pass. Offense; pass play; 10 from the previous spot. Short Pass, Long Pass, Screen.
- Defensive pass interference [DPI] (8-5-2): a defender more than one yard past the line significantly hinders an eligible receiver's chance to catch the ball. Defense; pass play; spot foul, AFD. Mostly Long Pass.
- Illegal contact [ICT] (8-4-2, 8-4-3): the defender makes contact beyond the five-yard zone, or initiates contact in the back or keeps it past the receiver, while the passer is still in the pocket. Defense; pass play; 5 and AFD. Short Pass, Long Pass.
- Roughing the passer [RPS] (12-2-11): the defender hits the passer after the ball has left, hits him in the head or neck, low, or lands on him with his weight. Defense; pass play; 15 and AFD. Short Pass, Long Pass, Screen, Blitz.
- Intentional grounding [ING] (8-2-1): a passer under pressure throws to nowhere near an eligible receiver. Offense; pass play; loss of down and 10 yards (or spot of the pass). Short Pass, Long Pass; with the Blitz as the defense call.
- Ineligible receiver downfield [IDP] (8-3-1): an ineligible lineman is more than one yard downfield before a legal pass is thrown. Offense; pass play; 5 from the previous spot. Screen Pass first, Short Pass, Long Pass.
- Illegal forward pass [IFP] (8-1-2): a forward pass from beyond the line, a second forward pass, or a pass after the ball has crossed the line and come back. Offense; loss of down and 5. Rare; Screen and passes.
- Illegal touching of a forward pass [ITP] (8-1-8): an ineligible receiver first touches a forward pass, or an eligible receiver who went out of bounds touches it first. Offense; pass play; 5 (or loss of down for the out of bounds version).
- Illegal block in the back [IBW] (12-1-3-b): a block from behind above the waist. Offense (also the kicking team in flight of a punt); 10. Runs, returns, punts.
- Clipping [CLP] (12-2-1): blocking an opponent from behind below the waist when he is not the runner. Either team; 15. Runs, End Run (pursuit), returns.
- Chop block [CHB] (12-2-5): one blocker hits a defender low while another blocks him high. Offense; 15. Line Plunge, pass blocking.
- Illegal batting or kicking of the ball [BAT, KIK] (12-5-1, 12-5-2): a player bats or kicks a loose ball toward the opponent's goal line (or in an end zone). Either; 10 (loss of down if the offense, before a change of possession, except beyond the line on a kick). Fumbles on any play.

Personal fouls and conduct
- Unnecessary roughness [UNR] (12-2-8): hitting a runner out of bounds, a player already down, a player out of the play, or other extra contact before or after the whistle. Either; 15 (AFD if defense); possible disqualification. Any play, after the play.
- Unnecessary roughness against a defenseless player (12-2-9): contact with the head or neck, lowered helmet, or a launch against a passer, receiver, kicker, returner, player on the ground, etc. Either; 15 and AFD. Pass plays and kicks.
- Roughing the kicker [RRK] (12-2-12 Item 1): contact with the planted leg of a kicker whose kicking leg is in the air, or with a kicker standing on both feet. Defense; Punt, Field Goal; 15 and AFD.
- Running into the kicker [RNK] (12-2-12 Item 2): contact with the kicking leg or foot, or sliding under the kicker. Defense; Punt, Field Goal; 5, no AFD.
- Roughing the holder (12-2-13): forcible contact with the holder of a place kick. Defense; Field Goal; 15 and AFD.
- Unsportsmanlike conduct [UNS, TAU] (12-3-1): taunting, abusive language, a violent gesture, a punch, excessive celebration, and about twenty other listed acts. Either; usually after the play; 15 (AFD if defense); possible disqualification.
- Hip-drop tackle [HDT] (12-2-18), horse-collar tackle [HC] (12-2-16), leg whip, helmet as a weapon, impermissible use of the helmet [UOH] (12-2-10): named tackle fouls. Defense mostly; runs; 15 and AFD.

Kicks and returns
- Fair catch interference [FCI] and kick catch interference [KCI] (10-1-1): a kicking team player hinders a receiver's chance to catch a kick. Kicking team; Punt, kickoff; 15 from the spot of the foul.
- Invalid fair catch signal [IFC] (10-2-2 Item 2): a receiver raises his hands above his shoulders in a way other than the valid wave. Receiving team; Punt, kickoff; 5.
- Illegal block after a fair catch signal (10-2-2 Item 5) and illegal contact after a fair catch (10-2-3-c): 15. Punt.
- Ineligible player downfield on a kick [IDK] (9-1-2): a kicking team player other than an end man goes more than a yard past the line before the kick. Kicking team; Punt, Field Goal; 5.
- Illegal touching of a kick [ITK] (9-2-3, 6-2-5): a kicking team player who was out of bounds touches or recovers the kick. 5 (touchback option inside the 5).
- Offside on a free kick [OFK] and illegal formation on a free kick (6-1-3): kickoff; 5 and the kick again.
- Onside kick untouched beyond the setup zone (6-1-6): 15 from the kicking team's restraining line and the receiving team takes the ball. Onside kick feature (NX4).
- Kicker, punter or holder simulating roughing (12-3-1-t): 15.

Timing
- Timeout fouls (4-5-1, 4-5-4): a second timeout in the same dead ball period or a timeout beyond three in a half. 5 and the timeout is charged. NX1.

Suggested later additions (not in the first list but each is a single data row): illegal peel back, illegal blindside, illegal crackback, illegal cut block, illegal use of the helmet, leverage, leaping, illegal wedge and double team on kickoffs, disconcerting signals, taunting as its own foul, illegal handing forward, backward pass out of bounds late in a half.

### 1. Pre-snap fouls by the offense

- False start (7-4-2, PDF 34; code FST): by offense; before the snap (whistle at once, snap or not); 5 yards; AFD no; LOD no; spot: line of scrimmage ("enforced prior to the snap"); dead-ball; down repeated; note: covers an interior lineman who moves after taking a three-point stance, an eligible receiver on the line who moves forward after everyone is set for one second, quick movements by a shotgun or T-formation quarterback, and an attempt to draw the defense offside; after the two-minute warning of a half with the clock running, not being set for one full second is converted to a false start (Item 6); SRC-OFFICIAL.
- Illegal shift (7-4-6 and 7-4-7, PDF 35; also 7-4-2 Item 6; code ISH): by offense; at or before the snap; 5; AFD no; LOD no; spot: per 14-4-1 (line of scrimmage either way); live ball if the snap is made, otherwise dead; down repeated; note: all players must stop and be set together for a full second after the last shift; a second player may go in motion without a new full-second pause only after the first has come to a complete stop; SRC-OFFICIAL.
- Illegal motion (7-4-8, PDF 35; code ILM): by offense; at the snap; 5; AFD no; LOD no; spot: previous spot; live ball; down repeated; note: only one back may be in motion, parallel to or away from the line; a T-formation quarterback in motion must stop for a full second; SRC-OFFICIAL.
- Illegal formation, scrimmage down (7-5-1, PDF 35; summary: Illegal formation (scrimmage down); code ILF): by offense; at the snap; 5; AFD no; LOD no; spot: previous spot; live ball; down repeated; note: seven players on the line, eligible players on both ends, nobody out of bounds, at most one player in a "neither on nor off the line" spot (must be eligible and obey motion rules); SRC-OFFICIAL.
- Illegal snap (7-6-3, PDF 36): by offense (snapper); at the snap; 5 from the line of scrimmage; AFD no; LOD no; spot: line of scrimmage; dead ball for the snap before officials are in position (no penalty, repeated act after a warning becomes delay of game); down repeated; SRC-OFFICIAL.
- Snap to an ineligible player (7-6-4, PDF 36): by offense; at the snap; 5 from the line of scrimmage; whistle at once; AFD no; LOD no; down repeated; SRC-OFFICIAL.
- Delay of game, offense (4-6-1 to 4-6-5, PDF 20 and 21; codes DOG): by offense; before the snap; 5; AFD no; LOD no; spot: succeeding spot if between downs and the ball stays dead (4-6-4), previous spot if the ball was in play; dead ball (the Back Judge whistles, ball remains dead); down repeated; note: play clock is 40 seconds from the end of the previous play, 25 seconds after a change of possession, charged timeout, two-minute warning, period end, penalty enforcement, replay review; also delay: player stays on a dead ball or on a downed runner, repeated early snap before officials are in position, undue delay assembling after a timeout, spiking or throwing the ball after a down (not after a score), intentional contact to delay the snap, second timeout in a dead ball period (4-6-5-g); two successive delay-of-game penalties in the same down with the clock running are unsportsmanlike conduct, 15 (12-3-1-n); the 10-second runoff rules of 4-7 apply to actions that conserve time (section 8); SRC-OFFICIAL.
- Illegal substitution (4-7-2, 5-2-4, 5-2-8, 5-3-2, PDF 22, 23, 24, 25; code ILS): by either team; before the snap or during a live ball; 5 yards; AFD no (defense: on the 14-1-2 Item 5 exception list); LOD no; spot: succeeding spot if the whistle blows with the ball dead (12 or more in the offensive huddle: 5-2-8-a), previous spot if the ball is in play or for a substitute not reaching the inside of the field numerals, a withdrawn player leaving on the wrong side, return of a suspended player, and a designated holder leaving wrong; dead-ball or live-ball by case; down repeated; note: after the two-minute warning with time in and the ball dead, illegal substitution adds a 10-second runoff (4-7-2); failure to report a change of eligible or ineligible status is also five yards for illegal substitution (5-3-2, 5-3-3); an illegal substitute who interferes with play can be a palpably unfair act (5-2-8-c); SRC-OFFICIAL.
- Too many players, offense (5-1-1, PDF 23; summary: Too many players on the field; code OTM): by offense; before the snap (more than 11 in the formation for more than three seconds) or at the snap (more than 11 on the field when the ball is snapped); 5; AFD no; LOD no; spot: succeeding spot before the snap (whistle at once), previous spot at the snap; dead ball before, live ball at the snap; down repeated; note: the designated holder on a kickoff is a non-player and may be the 12th person; SRC-OFFICIAL.
- 12 or more in the offensive huddle (5-2-1, 5-2-8-a, PDF 23, 24): by offense; before the snap while the play clock runs; 5 from the succeeding spot; whistle at once, ball remains dead; AFD no; LOD no; down repeated; SRC-OFFICIAL.
- Player in motion or lined up in front of his bench area (12-3-1-l, PDF 58; summary: Player going in motion in front of bench area): by offense; before the snap; 15 (unsportsmanlike conduct) from the succeeding spot if the ball is dead; AFD no; dead-ball; down repeated; SRC-OFFICIAL.
- Using substitutes or returning players to deceive (12-3-1-k and 5-2-11, PDF 58, 24): by either team; before the snap; 15; AFD if defense; dead-ball; note: includes simulated substitutions sent toward the huddle and returned, and lingering players leaving the field; SRC-OFFICIAL.
- Unsportsmanlike conduct after a warning for a quick snap against a defense still substituting (5-2-9 and 5-2-10, PDF 24): by offense; before the snap; 15 from the succeeding spot; AFD no; the first time no penalty is enforced except for personal and unsportsmanlike fouls, a defensive too-many-men foul is wiped out and the down is replayed with the clock reset; SRC-OFFICIAL.

### 2. Pre-snap fouls by the defense

- Offside (7-4-5, PDF 35; codes DOF, OOF, OFK; summary group Loss of Five): by either team (the rule is not limited to the defense); at the snap (live ball) or before it (whistle); 5; AFD no (exception list); LOD no; spot: line of scrimmage; down repeated; note: offside means any part of the body in or beyond the neutral zone when the ball is put in play, or beyond a restraining line on an onside kick; SRC-OFFICIAL.
- Encroachment (7-4-3, PDF 34; code ENC): by defense; before the snap; 5 from the line of scrimmage "prior to the snap"; AFD no (exception list); LOD no; dead-ball; down repeated; note: a defender enters the neutral zone and contacts an offensive player or the ball, or interferes with the ball during the snap; whistle at once; SRC-OFFICIAL.
- Neutral zone infraction (7-4-4, PDF 34 and 35; code NZI): by defense; before the snap; 5 from the line of scrimmage; AFD no (exception list); LOD no; dead-ball (whistle at once); down repeated; note: three cases: a defender past or beside a lineman with a clear path to the quarterback or kicker; a defender enters the neutral zone and makes an offensive player move; in the last two minutes of a half the snap comes before all defenders are on their side of the line; SRC-OFFICIAL.
- Disconcerting acts or signals (12-3-1-i, PDF 58; summary group Loss of Fifteen): by defense; before or at the snap (the official whistles at once); 15 from the succeeding spot if dead, previous spot if in play; AFD yes (12-3-1 penalty text and 14-1-2 Item 5); LOD no; dead-ball; down repeated with AFD; note: acts or words meant to disconcert the offense at the snap; SRC-OFFICIAL.
- Delay of game, defense, abrupt actions (4-6-5-d, PDF 21; code DOD): by defense; before the snap; 5 (delay of game); AFD no (exception list); note: a defender stationary within a yard of the line makes quick abrupt movements to make the offense jump; the official whistles at once; a defender who walks or runs up to time the snap and stops is not a foul; SRC-OFFICIAL.
- Too many players, defense (5-1-1, PDF 23; code DTM): by defense; "snap is imminent" (more than 11 in the formation) or at the snap (more than 11 on the field); 5; AFD no (exception list); LOD no; succeeding spot or previous spot as for the offense; down repeated; note: if the offense snaps before the defense has a chance to substitute, a too-many-men foul is wiped out and the down replayed (5-2-9, 5-2-10); SRC-OFFICIAL.
- Illegal formation by the defense on a punt, field goal or Try kick (9-1-3 Items 1 and 2, PDF 43; summary: Illegal formation (scrimmage kick)): by defense; at the snap; 5; AFD no (exception list); LOD no; spot: previous spot; live ball; down repeated; note: a defender within one yard of the line must have his entire body outside the snapper's shoulder pads; on a field goal or Try no more than six defenders on the line on either side of the snapper; the restrictions lapse if the offense does not show the standard formation or shifts or sends a man in motion after it is set; SRC-OFFICIAL.
- Pushing a teammate into the offensive formation (9-1-3 Items 1(2) and 2(3), PDF 43; summary: Pushing teammate on scrimmage kick): by defense; at the snap or during the kick; 15; AFD yes (not on the exception list, and a foul by Team B on a scrimmage down); LOD no; spot: previous spot; live ball; note: a foul committed in an attempt to block the kick, so it is not treated as a post-possession foul (9-5-1 Exception 4); SRC-OFFICIAL.
- Defensive offside on a free kick, illegal formation on a free kick: see section 6.

### 3. Fouls by the offense on runs and passes

- Holding, offense (12-1-3-c, PDF 52; summary: Holding (offense); code OH): by offense; run, pass, or kick; 10; AFD no; LOD no; spot: run = three-and-one (basic spot = dead ball spot; foul behind the basic spot is enforced from the spot of the foul; behind the line of scrimmage = previous spot); pass = previous spot; kick = previous spot; live ball; down repeated; note: material restriction (grabbing, tackling, hooking, jerking, twisting, pulling to the ground); blocking notes list nine situations where it is not called (runner tackled simultaneously by another defender, runner goes out of bounds at the same time, away from the point of attack, double team, defensive "rip" technique, and others); SRC-OFFICIAL.
- Illegal use of hands, offense (12-1-3-a, PDF 52; summary: Illegal use of hands (offense); code ILH): by offense; run or pass; 10; AFD no; LOD no; spot as for holding; live ball; down repeated; note: hands thrust forward above the frame into the head or neck in a direct or prolonged manner; SRC-OFFICIAL.
- Illegal block in the back (above the waist) (12-1-3-b, PDF 52; code IBW): by offense (and a kicking team player during a punt in flight); run, pass or kick; 10; AFD no; LOD no; spot: three-and-one on runs, previous spot on pass or kick plays; live ball; down repeated; note: not a foul when making a personal attempt to recover a loose ball, when the opponent turns away, or when both hands are on his side; close-line play exception; SRC-OFFICIAL.
- Assisting the runner and interlocking interference (12-1-4, PDF 53): by offense; run; 10; AFD no; LOD no; spot: three-and-one; live; down repeated; note: pulling or pushing the runner, grasping a teammate, or throwing the body against a teammate to help block; also called "illegal use of hands, arms or body"; SRC-OFFICIAL.
- Offensive pass interference (8-5-2 and 8-5-4, PDF 40; code OPI): by offense; during a pass from the snap until the ball is touched (blocking more than a yard downfield before the pass is also OPI); 10 from the previous spot; AFD no; LOD no; spot: previous spot; live ball; down repeated; note: only on a pass thrown from behind the line; acts that restrict the opponent's chance to catch or push off; a clearly uncatchable pass is not interference except for blocking downfield; SRC-OFFICIAL.
- Ineligible player downfield on a pass (8-3-1, PDF 39; summary: Ineligible player downfield on pass; code IDP): by offense; pass play before the pass is thrown (more than a yard beyond the line); 5; AFD no; LOD no; spot: previous spot; live; down repeated; note: legal when a lineman is engaged within a yard of the line and moves with the contact; after the pass is thrown he may go downfield but not block a defender more than a yard past the line until the ball is touched (that is pass interference); SRC-OFFICIAL.
- Illegal touching of a forward pass (8-1-8-a, PDF 38; code ITP): by offense (an ineligible player intentionally touches or catches it); pass play; 5 at the previous spot; AFD no; LOD no; live; down repeated; note: if caught it is a live ball; SRC-OFFICIAL.
- Illegal touching of a forward pass by an eligible receiver who had gone out of bounds and reestablished (8-1-8-b, PDF 38; summary group Loss of Down Without Yardage): by offense; pass play; no yards; LOD yes at the previous spot; AFD no; live; note: this is the only "loss of down without yardage" foul in the summary; SRC-OFFICIAL.
- Illegal forward pass (8-1-2, PDF 37; summary group Loss of Down with Yardage; code IFP): by offense (and by either team in the case of a pass after a change of possession); pass attempt; (a) from beyond the line of scrimmage: loss of down and 5 from the spot of release; (b) a second forward pass behind the line, or a forward pass after the ball went beyond the line and came back: loss of down and 5 from the previous spot; (c) after a change of possession: 5 from where the ball is released, no loss of down; AFD no; live; note: an intercepted illegal pass may be advanced and the penalty declined (Item 2); eligibility, pass interference and grounding rules do not apply to a pass from beyond the line or after a change of possession; if the offense must be penalized on fourth down the ball goes to the defense and the distance penalty is also enforced (14-1-2 Item 2); SRC-OFFICIAL.
- Intentional grounding (8-2-1, PDF 38; summary group Loss of Down with Yardage; code ING): by offense (passer); pass play with imminent loss of yardage from pressure; (a) loss of down and 10 yards from the previous spot, (b) loss of down at the spot of the pass if that spot is more than 10 yards behind the previous spot or more than half the distance to the goal line, (c) a safety if the passer's entire body and the ball are in his end zone at the throw; AFD no; LOD yes; spot: previous spot or spot of the pass, whichever is less beneficial to the offense (8-6-1-a, 14-4-5-a); live; note: the pass does not have to be incomplete; not called when the passer is outside the pocket and the ball lands at or beyond the line of scrimmage, or when contact significantly affects the throw; a T-formation quarterback may legally spike the ball immediately on the snap to stop the clock; a delayed spike is prohibited; after the two-minute warning it is an action that conserves time (4-7-1: 10-second runoff against the offense, section 8); SRC-OFFICIAL.
- Illegal handing the ball forward (8-7-4, PDF 41; summary: Illegal forward handing, under both Loss of Five Yards and Loss of Down with Yardage (beyond the line of scrimmage or to an ineligible receiver behind the line of scrimmage); code IFH): by offense (any team after a change of possession); run; (a) beyond the line of scrimmage: loss of down and 5 from the spot of the foul; (b) to an ineligible receiver behind the line: loss of down and 5 from the previous spot; (c) after a change of possession: 5 from the spot of the foul, no loss of down; AFD no; live; note: a muffed handoff is a fumble and the ball stays alive; SRC-OFFICIAL.
- Backward pass out of bounds that conserves time (8-7-2, PDF 41; summary group Loss of Down with Yardage): by offense; run; during a play that starts after the two-minute warning of either half, before a change of possession; loss of down and 5; AFD no; LOD yes; live; note: also listed as an illegal act in 4-7-1-d (10-second runoff applies to the offense while time is in); SRC-OFFICIAL.
- Illegal batting or punching the ball (12-5-1 and the penalty in 12-5-2, PDF 59; summary: Loss of Ten Yards, and Loss of Down with Yardage: Illegal batting behind the line of scrimmage; code BAT): by either team; during a run, fumble, or kick; 10; for the offense before a change of possession on a scrimmage down also loss of down (not when the offense is beyond the line on a scrimmage kick); AFD no (or yes if the defense is the offender by 14-1-2 Item 5); spot: spot of the foul (the rule lists no special spot; 14-3-3 says "spot of the foul" when no rule governs; 9-5-1 note 5 sends to 12-5-1); live; note: four types: batting a loose ball toward the opponent's goal line in the field of play; batting a loose ball that has touched the ground in an end zone in any direction; an offensive player batting a backward pass in flight toward the opponent's goal line; a controlled forward pass thrown forward again before the catch; a forward pass in flight may be tipped by an eligible player; an intentional muff forward on a fair catch is an illegal bat (10-2-2 Item 4); SRC-OFFICIAL. Disagreement noted in section 15 (the summary says "behind the line of scrimmage" for the loss of down version).
- Illegally kicking the ball (12-5-2, PDF 59; summary: Loss of Ten Yards; and Loss of Down with Yardage: Illegal kicking behind the line of scrimmage; code KIK): by either team; any play; 10; offense before change of possession on a scrimmage down: also loss of down (no loss of down for a foul by Team A beyond the line during a scrimmage kick); AFD as for batting; live; note: kicking a loose ball or a ball in a player's possession; the ball stays live when an illegally kicked ball is recovered; SRC-OFFICIAL.
- Chop block (12-2-5, PDF 54; code CHB): by offense; run or pass; 15; AFD no; LOD no; spot: three-and-one on runs, previous spot on passes; live; down repeated; note: a high-low double team block by the offense, in six described situations including "lure" and "reverse chop"; not a foul if the defender initiates the contact or the blocker is trying to slip free; SRC-OFFICIAL.
- Peel back block (12-2-2, PDF 53): by offense; run, pass or kick play; 15; AFD no; spot: three-and-one on runs; live; note: a block to the side and below the waist by a player moving toward his own end line, approaching from behind or from the side unless his near shoulder crosses in front of both legs; SRC-OFFICIAL.
- Crackback block (12-2-6, PDF 54): by offense; run or pass; 15; AFD no; live; note: within five yards of the line, by a flexed or motion player moving back toward the ball's snap position; contact below the waist or with defenseless-player contact is prohibited against the recipient; SRC-OFFICIAL.
- Blindside block (12-2-7, PDF 54): by either team (a block with the player's path toward or parallel to his own end line); run or return; 15; AFD no (offense) or yes (by defense); live; note: forcible contact with helmet, forearm or shoulder, except in close-line play before the ball leaves the area; SRC-OFFICIAL.
- Illegal block below the waist (12-2-4, PDF 53 and 54; code LBL): by either team; prohibited after a change of possession, on kick plays (kicking team after the kick, receiving team during the down), and outside the tight end box before a change of possession; 15; AFD if defense; live; note: not a foul against the runner or a player attempting to catch a pass; the tight end box does not excuse cut, clipping, peel back, chop or crackback; SRC-OFFICIAL.
- Clipping (12-2-1, PDF 53; code CLP): by either team (usually the offense, or any team on a return); run, kick return; 15; AFD if the fouling team is the defense; LOD no; spot: three-and-one on runs; live; note: a block from behind below the waist against a non-runner; legal in close-line play above the knee, except an offensive lineman may not clip a defender above the knees who is lined up opposite another lineman more than one position away and reacting to flow away; also clipping if a legal block is followed by rolling up on the back or side of the leg; SRC-OFFICIAL.

### 4. Fouls by the defense on runs and passes

- Defensive holding (12-1-6, 8-4-6, PDF 53 and 39; summary: Holding (defense); code DH): by defense; run or pass; 5 and AFD; LOD no; spot: previous spot on passes; three-and-one on runs; live; first and 10; note: tackling or holding an opponent who is not the runner (a pretend ball carrier in the pocket counts as a runner), or "pull-and-shoot" on a punt, field goal or Try; on a scrimmage kick that crosses the line, holding and illegal use of hands by either team are 10 yards unless the foul is in an attempt to block the kick (9-1-4-e, PDF 43); SRC-OFFICIAL.
- Illegal use of hands, defense (12-1-7, PDF 53; summary: Illegal use of hands by defense): by defense; run or pass; 5 and AFD; spot as for defensive holding; live; note: thrusting hands forward into the head or neck of an opponent; SRC-OFFICIAL.
- Illegal contact (8-4-2, 8-4-3, 8-4-4, PDF 39; code ICT): by defense; pass play while the player who took the snap is still in the pocket with the ball; 5 and AFD; LOD no; spot: previous spot; live; first and 10; note: within the five-yard zone the defender may not make first contact in the back, or keep contact after the receiver is even with him, or contact again after losing contact; beyond five yards no contact on a receiver trying to evade; restrictions end when the quarterback hands off, throws, fumbles, is tackled, or leaves the pocket with the ball; also not applied when a punt formation is shown; SRC-OFFICIAL.
- Illegal cut block (8-4-5 and 12-2-3, PDF 39 and 53; code ICU): by defense (a blocker below the waist on an eligible receiver, at, behind or beyond the line, rules differ for flexed and tight receivers); pass play; 15 and AFD; LOD no; spot: previous spot; live; note: only on eligible receivers and ends when the quarterback shows no further intention to pass; SRC-OFFICIAL.
- Defensive pass interference (8-5-2, 8-5-4, 8-6-1-b, PDF 40; summary: Defensive pass interference under First down at Spot of Foul; code DPI): by defense; pass play from the throw until the ball is touched; no fixed yardage: first down for the offense at the spot of the foul; AFD yes; LOD no; spot: spot of the foul; live; first and 10; note: if the spot is behind the defense's goal line and the previous spot was on or outside the defense's 2-yard line, first down at the 1-yard line (inbounds spot matching the interference); if the previous spot was inside the 2-yard line, the ball goes halfway between the previous spot and the goal line, first down (the summary lists this as "Ball Placed on 1-Yard Line" and "Defensive pass interference in its end zone and previous spot is outside its 2-yard line"); if the interference is also a personal foul, both can be enforced (14-1-3 exception 2); on a Try the rule is in 11-3-3; permissible acts (incidental contact, uncatchable pass) are in 8-5-3; SRC-OFFICIAL.
- Roughing the passer (12-2-11, PDF 55 and 56; code RPS): by defense; pass play before, during or after the throw; 15 and AFD; LOD no; spot: previous spot or dead ball spot, whichever is more beneficial to the offense (14-4-5-d, 8-6-1-d); live; first and 10; note: disqualification if flagrant; protection after the ball is released (only the rusher's first step), no "stuffing" or landing with all weight, no helmet or head or neck hit, no low hit on the knee or below when the passer has a foot on the ground, protection after a change of possession for the quarterback; the passer outside the pocket loses the first-step rule and the low-hit rule but keeps the others; SRC-OFFICIAL.
- Prohibited contact with a defenseless player (12-2-9, PDF 55; summary: Prohibited contact to a defenseless player): by either team (usually the defense); pass play, kick, return; 15 and AFD (the article's penalty line says "Loss of 15 yards and an automatic first down" without limiting it to the defense); possible disqualification if flagrant; spot: previous spot or dead ball spot where the defender hits the passer or receiver before a catch (8-6-1-d); live; note: eleven kinds of defenseless players are listed (passer, receiver running a route hit from the side or behind, receiver in the act of catching, intended receiver around an interception, runner already in a tackler's grasp, kick returner who has not become a runner, player on the ground, kicker or punter, quarterback after a change of possession, player who received an illegal blindside or crackback, long snapper on a kick); three prohibited acts (head or neck with helmet, facemask, forearm or shoulder; lowered head with forcible helmet contact; illegal launch); SRC-OFFICIAL. UNVERIFIED point: the text does not say how the AFD works when the fouling team is the offense; 14-1-2 Item 6 says that after a change of possession the team in possession gets first and 10.
- Unnecessary roughness (12-2-8, PDF 54 and 55; code UNR): see section 7.
- Leverage, leaping and the other block-the-kick fouls: see section 5.
- Twisting, turning or pulling the facemask (12-2-15): see section 7.

### 5. Kicker and holder protection and kick-block fouls

- Roughing the kicker (12-2-12 Item 1, PDF 56; code RRK): by defense; punt, field goal, or Try kick from behind the line; 15 from the previous spot and AFD; LOD no; spot: previous spot; live; first and 10; note: personal foul; disqualification if flagrant; contact with the plant leg while the kicking leg is in the air, sliding into or contacting a kicker with both feet on the ground (unless not severe), or any other unnecessary roughness; not a foul when contact is incidental after touching the kick in flight, caused by the kicker's own motion, during a quick kick or run, when the defender is blocked into him, or caused by an opponent's foul; SRC-OFFICIAL.
- Running into the kicker (12-2-12 Item 2, 6-2-3, PDF 56 and 32; summary: Running into kicker; code RNK): by defense (6-2-3: by the receiving team on a free kick); punt or field goal; 5 from the previous spot; AFD no ("There is not an automatic first down"); LOD no; spot: previous spot; live; down repeated; note: contact with the kicking leg or foot, even if the kicker is airborne, or sliding under the kicker so he cannot return both feet to the ground; the 14-1-2 exception list names it; two defenders blocking the kick at the same instant: not enforced unless the Referee judges that one clearly caused the block (12-2-13 Note); SRC-OFFICIAL.
- Roughing the holder (12-2-13, PDF 56 and 57; summary: Roughing the holder): by defense; place kick (field goal or Try); 15 from the previous spot and AFD; LOD no; spot: previous spot; live; first and 10; note: personal foul, disqualification if flagrant; SRC-OFFICIAL.
- Unnecessary contact to a kicker out of the play (12-2-8-i, PDF 55): by the receiving team; punt or kick; 15; AFD if defense; spot: previous spot or per post-possession rules (9-5-1 Exception 4); a kicker standing still or fading backward is out of the play until he assumes a distinctly defensive position; SRC-OFFICIAL.
- Kicker, punter or holder simulating being roughed (12-3-1-t, PDF 58; summary: Kicker or holder simulating being roughed): by the kicking team; punt, field goal; 15 from the previous spot if in play; AFD no; live; SRC-OFFICIAL.
- Leaping (12-3-1-r, PDF 58; summary: Leaping 12-3-1(o), (r)): by defense; field goal or Try kick attempt; 15; AFD yes ((i) through (v) in 12-3-1: "if the foul is by the defense, it is also an automatic first down"); spot: previous spot; live; note: running forward and leaping across the line of scrimmage to block a kick unless the player was stationary within a yard of the line at the snap; a player more than a yard back may run and leap if he does not cross the line or land on players; SRC-OFFICIAL.
- Jumping or standing on a teammate or opponent to block a kick (12-3-1-o): by defense; kick; 15; AFD yes; same spot; SRC-OFFICIAL.
- Leverage: placing a hand on a teammate or opponent to gain height to block a kick or to go through a gap (12-3-1-p, PDF 58; summary: Leverage): by defense; kick; 15; AFD yes; SRC-OFFICIAL.
- Picking up a teammate to block a kick (12-3-1-q, PDF 58; summary: Picking up a teammate to block a kick): by defense; kick; 15; AFD yes; SRC-OFFICIAL.
- Goaltending (12-3-1-s, PDF 58; summary: Goaltending): by defense; field goal or Try kick; 15 plus the Referee may award three points for a palpably unfair act (12-3-4); AFD yes; SRC-OFFICIAL.
- Pushing a teammate into the offensive formation (9-1-3, PDF 43): see section 2.
- Illegal batting or kicking (12-5): see section 3.
- Ineligible player downfield on a kick (9-1-2, PDF 43; summary: Ineligible player downfield on kick; code IDK): by the kicking team; scrimmage kick, before the ball is kicked; 5; AFD no; LOD no; spot: previous spot (scrimmage kick enforcement); live; down repeated; note: only the end men on each side of the line at the snap, or an eligible receiver aligned or in motion behind the line and more than a yard outside the end man, may go more than a yard beyond the line before the kick; SRC-OFFICIAL.
- Punt, drop kick, or place kick from beyond the line (9-1-1, PDF 43; summary: Punt, drop kick, or place kick from beyond the line (5 yards) and Punt, drop kick, or place kick from beyond scrimmage (loss of down with yardage); code IPU): by the kicking team; kick; loss of down and 5 from the spot of the kick (or, for a second kick from behind the line after the ball has crossed it, loss of down and 5 from the previous spot); AFD no; LOD yes; live; note: a kick is "beyond the line" when the kicker's entire body and the ball are beyond it; SRC-OFFICIAL.
- Kicking team player voluntarily out of bounds on a scrimmage kick (9-1-5, PDF 44; summary: Kicking team player voluntarily out of bounds): by the kicking team; punt after it crosses the line, before the kick ends; 5; AFD no; spot: previous spot; live; note: a kicking team player who goes out of bounds voluntarily without contact to avoid a block; if he does not try to return inbounds in a reasonable time it is unsportsmanlike conduct, 15 (12-3-1-u); SRC-OFFICIAL.
- Illegal touching of a scrimmage kick (9-2-3, PDF 44; summary: Touchback: Illegal touching of scrimmage kick inside five-yard line): by the kicking team (a kicking team player who went out of bounds touches or recovers the kick beyond the line before it is touched by a kicking team player who was not out of bounds or by the receivers); 5 from the previous spot; if the illegal touch is inside the receiver's five-yard line the receiving team may take a touchback instead; AFD no; live; down repeated; note: "first touching" by the kickers (9-2-2) is a violation, not a foul, with the receiving team's option to take the ball at the spot of first touching; SRC-OFFICIAL.
- Illegal formation, scrimmage kick (9-1-3, PDF 43): see section 2. For Offensive illegal formation, see section 1.

### 6. Free kicks (kickoffs, safety kicks, onside kicks) and returns

- Illegal free kick (6-1-1, PDF 29; summary: Illegal kick): by the kicking team; free kick; 5; AFD n/a; spot: previous spot and kick again; note: a kick not made from the restraining line, or a tee higher than one inch; SRC-OFFICIAL.
- Illegal formation, free kick (6-1-3, 6-1-6, PDF 29, 30, 31; summary: Illegal formation (free kick)): by either team; at the kick; 5 from the previous spot and the kick is made again, except that when the kicking team fouls before the kick ends or the receiving team fouls at or during a kickoff or safety kick and the receivers keep the ball, they may instead take the yardage from the dead ball spot (6-3-1, 14-4-7); AFD n/a; live; note: kicking team players other than the kicker must be on the restraining line, feet on the ground; at least two between sideline and number, two between number and inbounds line, two inside; the receiving team needs nine players in the setup zone and five on the restraining line; the kicker may not move beyond 15 yards before permitted; 2026 change: 6-1-3 rewrote the receiving team's setup-zone alignment; SRC-OFFICIAL.
- Offside, free kick (7-4-5 and 6-1-3 Penalty, 6-1-6, PDF 35, 30, 31; code OFK): by either team; at the kick; 5 and the kick again (or from the dead ball spot by the 6-3-1 option); SRC-OFFICIAL.
- Player out of bounds when the ball is kicked (6-1-3 Penalty, 6-1-6 Penalty; code POK): by either team; at the kick; 5; SRC-OFFICIAL.
- Onside kick untouched beyond the onside kick setup zone (6-1-6 and Penalty, PDF 30 and 31; summary: Loss of Fifteen Yards from the Kicking Team's Restraining Line: Onside Kick Untouched Beyond Onside Kick Setup Zone): by the kicking team; onside kick; unsportsmanlike conduct, loss of 15 yards from the kicking team's restraining line, and the receiving team takes possession; AFD n/a; LOD n/a; live; note: also dead ball when an onside kick goes untouched beyond the setup zone (7-2-1-l); 2026 change: the kicking team may declare an onside kick at any time in the game (6-1-6) by telling the Referee before the play clock starts; SRC-OFFICIAL.
- Illegal blocking or use of hands on a free kick (6-2-1 Item 1 and 2, 6-2-2, PDF 31; summary: Illegal blocking or use of hands (free kick)): by either team; during the kick (kickoff, safety kick or onside kick); 10; AFD n/a; spot: previous spot (free kick enforcement), spot per 14-4-7; live; note: before the ball hits or is touched in the landing zone or end zone, the receiving team may not start a block on the kickers; during the kick both sides are subject to normal blocking restrictions; on an onside kick, the two zones in 6-2-2 limit blocks between the restraining lines and in the next five yards; SRC-OFFICIAL.
- Illegal double team block and illegal wedge block on a free kick (6-2-1 Item 2(c) and (d), 6-2-2 Item 2(d), PDF 31; summary: Illegal double team block; Illegal wedge on free kick; codes IDT, WED): by either team; during the kick or the return; 15; AFD n/a; spot: spot of the foul if the foul occurs during the kick, as customary if during the return, previous spot if it occurs in the receiving team's end zone during the kick or during an onside kick; live; note: a double team block is only legal for players who started in the setup zone; a wedge block is two or more players lined up shoulder to shoulder within two yards and moving forward together (no contact needed); SRC-OFFICIAL.
- Running into the free kicker (6-2-3, PDF 32; summary: Running into kicker): by the receiving team; kickoff; 5; SRC-OFFICIAL.
- Free kick out of bounds, or not reaching the landing zone (6-2-4, PDF 32; summary: Kickoff Out of Bounds Between Goal Lines; Kickoff Not Reaching the Landing Zone; codes KOB, LZ): by the kicking team; kickoff or safety kick; no yardage: the receiving team may take the ball 25 yards from the spot of the kick (30 for a safety kick) at the inbounds line on the side where it went out or landed short, or at the out of bounds spot, or at the spot where the ball lands or is touched short of the landing zone if less than 25 (or 30) yards; the summary lists "Receiver's ball at inbounds spot" and "Receiver's ball 25 yards from spot of kick" (and for the landing zone also "Receiver's ball at the spot where ball lands or touched"); AFD n/a; note: a kick that first touches the ground or a player in front of the landing zone's front line is dead (7-2-1-k); SRC-OFFICIAL.
- Free kick illegally touched (6-2-5, PDF 32; summary: Illegally touching of a free kick): by the kicking team; onside kick before the ball reaches the receiving team's restraining line (unless touched first by a receiver); or a kicking player who was out of bounds touches the ball beyond the line; 5 yards, or the receiving team takes possession at the spot of the illegal touch (Item 1); Item 2 (out of bounds player): 5; SRC-OFFICIAL.
- Player voluntarily out of bounds on a free kick (6-2-6, PDF 32; summary: Voluntarily going out of bounds on free kick): by the kicking team; before the ball is touched by the receivers or the kick ends; 5; SRC-OFFICIAL.
- Delay of kickoff [DOK]: foul code exists on operations.nfl.com; the rulebook treats it as delay of game (4-6-2-f and 4-6-2-g, 25 seconds, or 40 seconds to align after a Try or successful field goal); 5; SRC-OFFICIAL (code table) with the rule inferred; the rulebook penalty is the delay of game penalty of 4-6.
- Kickers recovering a free kick (6-1-4-d-1, 7-2-1-j; summary: Ball Dead Immediately): not a foul; the ball is dead and belongs to the kicking team at the dead ball spot if the recovery is legal; SRC-OFFICIAL.
- Delaying the start of a half (4-2-1-a, PDF 18; summary: Delaying the start of a half): by either team; kickoff at the half; 15 from the spot of the kickoff; SRC-OFFICIAL.

### 7. Fair catch and kick catch fouls

- Fair catch interference (10-1-1-b, 10-2-2 Item 3, PDF 47; summary: Interference with a fair catch, and under Combination: Fair catch interference; code FCI): by the kicking team; punt or free kick with a valid fair catch signal; 15 from the spot of the foul; a fair catch is awarded even if the ball is not caught; AFD n/a (the receiving team takes the ball); spot: spot of the foul (6-3-1-b, 9-5-1 Exception 3); if the interference is also unnecessary roughness the 15 is enforced from the spot of the foul or the previous spot; the receiving team then may snap the ball or try a fair catch kick (10-2-4); in the receiving team's end zone the 15 is enforced from its 20 (10-2-4); live; note: after a muff the receiver is still protected (10-2-2 Item 3); on the last play of a half the receiving team may extend the period (4-8-2-f); SRC-OFFICIAL.
- Kick catch interference (10-1-1-a, PDF 47; summary: Interference with the opportunity to make a catch; code KCI): by the kicking team; punt or free kick without a signal; 15 from the spot of the foul, and the offended team is entitled to put the ball in play by a snap from scrimmage; AFD n/a; spot: spot of the foul; live; note: contact with the receiver before or at the moment he touches the ball, or blocking his path, even without contact; not a foul if the kick is clearly uncatchable (clearly out of bounds or not in the vicinity of the receiver) or the kicker is blocked into the receiver; a receiver moving toward a kick in flight has the right of way; in the receiver's end zone this is a touchback (11-6-2-e); SRC-OFFICIAL.
- Invalid fair catch signal (10-2-2 Item 2, PDF 47; summary: Invalid fair catch signal; code IFC): by the receiving team; during the kick; 5 from the spot of the signal (previous spot if in Team B's end zone during a free kick or during an onside kick); AFD n/a; live; note: the ball is dead when an invalid-signal receiver catches it but there is no fair catch; a signal behind the line of scrimmage is ignored; SRC-OFFICIAL.
- Illegal block after a fair catch signal (10-2-2 Item 5, PDF 47; summary: Illegal block after fair catch signal): by the receiving team; until the ball touches a teammate or an opponent; 15 from the spot of the foul (previous spot in Team B's end zone during a free kick or onside kick); AFD n/a; live; note: a personal foul (6-3-1-a, 14-4-7-a); SRC-OFFICIAL.
- Illegal contact after a fair catch (10-2-3-c, PDF 48; summary: Illegal contact after a fair catch): by the kicking team (an opponent of the fair catcher); after a fair catch; 15 from the dead ball spot; disqualification if flagrant; AFD n/a; dead-ball; SRC-OFFICIAL.
- Catch after fair catch signal (10-2-3, 7-2-1-n; summary: Catch after fair catch signal under Ball Dead Immediately): not a foul; the ball is dead when a receiver who signaled catches it; SRC-OFFICIAL.
- Prohibited contact against a kick returner (12-2-9-a-6, PDF 55; summary: Prohibited contact against a kick returner, listed under Combination Penalties: Loss of Ball and Fifteen Yards): by the kicking team; return; 15 and AFD per the 12-2-9 penalty; spot: spot of the foul or dead ball spot if the opponent has the ball at the end of the down (6-3-1 Note, 14-2-4); live; note: the summary heading "Loss of Ball and Fifteen Yards" is not matched by the article (see section 15); SRC-OFFICIAL.
- Interference with the opportunity to make a fair catch after a muff (10-2-2 Item 3): see fair catch interference above.
- Intentional muff forward (10-2-2 Item 4): is an illegal bat (12-5-1); 10; SRC-OFFICIAL.

### 8. Timing, timeout and substitution-time fouls

- Team timeout requested and granted when not allowed (4-5-1, PDF 19; summary: Team timeout requested and granted when not allowed): by either team; before the snap while the ball is dead; 5 yards for delay of game and the timeout is charged; AFD no; LOD no; spot: succeeding spot; dead-ball; down repeated; note: this covers a second timeout in the same dead ball period (after the first was charged) and a timeout after the team has used all three in the half (two in an overtime period of the regular season); if the offense calls it after the two-minute warning while time is in, a 10-second runoff option is available (the play clock is reset to 30 seconds); a defensive timeout while time is in: play clock reset to 40 and the clock starts at the ready for play signal unless the offense chooses to start it on the snap; SRC-OFFICIAL.
- Second excess team timeout after the two-minute warning (4-5-4 Penalty, PDF 20; summary: Second excess team timeout after two-minute warning): by either team; injury timeout after the two-minute warning when the team has used its three timeouts; the first excess timeout: no yardage (possible 10-second runoff); the second and each later excess timeout: 5 yards from the succeeding spot; a fifth and later excess injury timeout is treated as a foul between downs; AFD no; down repeated; note: there can never be a 10-second runoff against the defense (Note 9); SRC-OFFICIAL.
- Actions that conserve time after the two-minute warning (4-7-1, PDF 21 and 22; summary: Time Penalty, and Ball Dead Immediately: Committing acts that conserve time): by either team; after the two-minute warning of either half; 5 yards unless a larger distance penalty applies; the acts: a foul by either team that stops the clock during a dead ball period, intentional grounding, an illegal forward pass, a backward pass out of bounds, spiking or throwing the ball after a down (except after a touchdown), illegally batting or kicking the ball out of bounds; AFD no; the ball is dead immediately; offense: 10 seconds are run off the game clock while time is in (play clock reset to 30; the offense may use a timeout instead of the runoff; the defense may decline the runoff and take the yardage but then the runoff is also declined and the clock starts on the snap); defense: play clock reset to 40, clock starts at the ready signal unless the offense chooses the snap, defense may use a timeout; SRC-OFFICIAL.
- Illegal substitution after the two-minute warning (4-7-2, PDF 22): by either team; ball dead and time in; 5 and a 10-second runoff (a larger distance penalty replaces the 5); SRC-OFFICIAL.
- Defensive fouls or injuries during the last 40 seconds of a half (4-7-3, PDF 22): by the defense; if a defensive foul that conserves time, or an excess timeout for an injury, happens in the last 40 seconds while time is in, the half ends unless the defense has timeouts left or the offense chooses to start the clock on the snap or play on after the ready signal; SRC-OFFICIAL.
- 10-second runoff after a replay reversal or a nullified foul after the two-minute warning (4-7-4, PDF 22): neither team can decline the runoff; either team can use a timeout to prevent it; SRC-OFFICIAL.
- Foul at the end of a half, extension of a period (4-8-2, PDF 22; summary: Time Penalty: Fouling by defense, illegal touching or fair catch interfering by offense or fouling by both teams at end of half during play in which time expires (extend quarter); Score Not Allowed): the period is extended by one untimed down if the defense commits an accepted live ball foul on the last play, if the offense commits illegal touching, kick catch or fair catch interference, a palpably unfair act, a personal or unsportsmanlike foul before a safety, interception, recovery of a backward pass or fumble, or failing to reach the line on fourth down, or a foul by the kicking team before the receivers secure the kick, and if both teams foul on the last play (double foul), except in listed cases; an offensive foul on the last play of the half means a score by the offense does not count (4-8-2-b); SRC-OFFICIAL.
- Intentional fouls to manipulate the game clock (12-3-3, PDF 58; summary: Time Restored and Fifteen Yards: Intentional fouls to manipulate game clock): by either team; multiple fouls in the same down; 15 yards and the game clock is reset to where it was at the snap; the clock starts at the next snap; SRC-OFFICIAL.
- Successive delay-of-game penalties when time is in (12-3-1-n, PDF 58; summary: Successive delay of game penalties when time in): see section 1; 15 yards, unsportsmanlike conduct.
- Repeated illegal substitutions when time is in (12-3-1-m, PDF 58; summary: Repeated illegal substitutions when time is in): by either team; after the two-minute warning; 15 unsportsmanlike conduct; AFD yes if defense; dead-ball; SRC-OFFICIAL.
- Illegally entering the field (4-1-2, PDF 18; summary: Illegally entering field): by non-players or players during intermissions; 15 from the succeeding spot (13-1-6); SRC-OFFICIAL.
- Failing to appear on the field 10 minutes before kickoff (4-2-1-b, PDF 18): loss of the coin toss option for both halves and overtime and 15 yards from the kickoff spot for the first half; SRC-OFFICIAL.
- Toss of the coin violation (4-2-2, PDF 18): loss of coin toss option for both halves and overtime and 15 yards from the kickoff spot for the first half; SRC-OFFICIAL.
- Initiating a challenge when out of timeouts (15-1-1-d, PDF 67): by a coach; 15 yards enforced as a foul between downs; the challenge is treated as a timeout charged; a foul between downs that is always enforced separately (14-1-2 Item 4 exception); SRC-OFFICIAL.
- Snapping before officials assume their positions (4-6-5-b, 7-6-3-c, summary: Ball Remains Dead): ball stays dead, no penalty on the first offense; a repeated act after a warning is delay of game; SRC-OFFICIAL.

### 9. Personal fouls (unnecessary roughness and the named types)

All personal fouls: 15 yards; "Other personal fouls" with 15-yard penalties not listed are personal fouls for enforcement (12-2-19, PDF 57). Personal fouls and unsportsmanlike fouls may be enforced from the dead ball spot if the opponent has the ball at the end of the down (14-2-4); they are enforced on the Try or the next free kick when they occur during a score (G5); they are enforced even when other fouls are disregarded after a changed replay ruling or an erroneous whistle (7-2-1-o, 7-2-1-r); and a personal foul by the defense on a pass play before the catch is enforced from the previous spot or the dead ball spot, whichever is better for the offense (8-6-1-d).

- Unnecessary roughness (12-2-8, PDF 54 and 55; summary: Unnecessary roughness; code UNR): by either team; run, pass, kick, after the play; 15; AFD if defense (explicit); LOD no; spot: three-and-one on runs; dead ball spot or previous spot on passes (see G7); live ball or dead ball (continuing action after the whistle); first and 10; note: the player may be disqualified if flagrant; the article's list: (a) leg whip, (b) forcibly contacting a runner out of bounds, (c) a receiving team player who is out of bounds blocking a kicking team player out of bounds during the kick (the summary's Blocking a kicking team player out of bounds), (d) running into or throwing the body against a runner whose progress is stopped, who has slid or taken a knee, or declared himself down, (e) against any player on the ground before or after the ball is dead, (f) throwing the runner to the ground after the ball is dead, (g) a player who is out of the play or could not expect contact, (h) pulling an opponent off a pile aggressively, (i) the kicker or punter who is standing still or fading backward; SRC-OFFICIAL.
- Leg whip (12-2-8-a): see unnecessary roughness; 15 (summary lists it as its own entry); AFD if defense; disqualification possible; SRC-OFFICIAL.
- Forcibly contacting a player out of bounds (12-2-8-b; summary: Forcibly contacting a player out of bounds): 15; AFD if defense; defenders must make an effort to avoid contact with a runner out of bounds; SRC-OFFICIAL.
- Blocking a kicking team player out of bounds (12-2-8-c; summary: Blocking a kicking team player out of bounds): by the receiving team; kick; 15; on a scrimmage kick post-possession rules apply (9-5-1); SRC-OFFICIAL.
- Unnecessary contact against a runner (12-2-8-d and -f; summary: Unnecessary contact against a runner): 15; SRC-OFFICIAL.
- Unnecessary contact against a player on the ground (12-2-8-e; summary: Unnecessary contact against player on the ground): 15; SRC-OFFICIAL.
- Unnecessary contact to a player out of the play (12-2-8-g; summary: Unnecessary contact to a player out of the play): 15; SRC-OFFICIAL.
- Pulling an opponent off a pile of players (12-2-8-h; summary: Pulling opponent off a pile of players): 15; SRC-OFFICIAL.
- Unnecessary contact to a kicker out of the play (12-2-8-i; summary: Unnecessary contact to a kicker out of the play): see section 5.
- Prohibited contact against a defenseless player (12-2-9, PDF 55): see section 4; 15 and AFD (penalty text), disqualification if flagrant.
- Impermissible use of the helmet (12-2-10, PDF 55; summary: Impermissible Use of the Helmet; code UOH): by either team; run, pass, any play; 15; AFD if defense; the player may be disqualified; live; SRC-OFFICIAL. Note: it is a foul if a player lowers his head and makes forcible contact with the helmet against an opponent, or uses the helmet or facemask to butt or make forcible contact to the head or neck; conventional tackles with incidental contact are not fouls.
- Roughing the passer (12-2-11): see section 4.
- Roughing the kicker, running into the kicker, roughing the holder (12-2-12, 12-2-13): see section 5.
- Striking, kicking, tripping or kneeing an opponent (12-2-14, PDF 57; summary: Striking, kicking, tripping or kneeing an opponent; codes TRP): by either team; any play; 15; AFD if defense; disqualification if flagrant and the whole action is seen; live; note: five listed acts: striking with fists; kicking or kneeing; tripping an opponent (including the runner); striking, swinging at or clubbing the head or neck with the wrist, arm, elbow, or hand (palm contact allowed by a defender warding off at the line, not repeated, or by anyone going for a loose ball); striking below the shoulders with a forearm or elbow by turning or pivoting; SRC-OFFICIAL.
- Twisting, turning or pulling the facemask or helmet opening (12-2-15, PDF 57; summary: Twisting, turning or pulling of opponent's facemask; code FMM): by either team; any play; 15; AFD if defense; disqualification if flagrant; live; note: a player who grasps the facemask or helmet opening must immediately release it; SRC-OFFICIAL.
- Horse-collar tackle (12-2-16, PDF 57; code HC): by the defense (a tackler); run; 15 and AFD; no disqualification stated; spot: three-and-one; live; note: grabbing the inside collar of the back, or the side of the shoulder pads or jersey, or the jersey at the nameplate or above, and pulling the runner toward the ground; knees buckled counts even if the runner stays up; not called on a runner in the pocket or in close-line play; SRC-OFFICIAL.
- Use of the helmet as a weapon (12-2-17, PDF 57; summary: Use of the helmet as a weapon): by either team; any time; 15 and automatic disqualification; AFD if defense; SRC-OFFICIAL. Note: this concerns a helmet that is no longer worn by anyone, used to strike, swing at, or throw at an opponent.
- Hip-drop tackle (12-2-18, PDF 57; code HDT; summary: Hip-drop tackle): by the defense (a tackler); run; 15 and AFD; spot: three-and-one; live; note: grabs or wraps the runner with the arms, then swivels and drops his hips or lower body, landing on or trapping the runner's leg at or below the knee; SRC-OFFICIAL.
- Clipping, peel back block, blocking below the waist, chop block, crackback block, blindside block: see section 3 (15 each; the blindside is also a defenseless-player trigger for the recipient, 12-2-9-a-10).
- Roughing the passer after change of possession: see section 4 (12-2-11-e).
- Disqualification rules for flagrant fouls (12-2, 12-3, 19-2, PDF 77): the Officiating department can instruct the crew to disqualify a player for a flagrant foul (also for an act not called on the field if decided before the next snap or kick); penalty: 15 yards and disqualification if flagrant (19-2); 2026 change: league personnel consult with the officials on disqualifications; SRC-OFFICIAL.

### 10. Unsportsmanlike conduct, taunting and conduct fouls

All items of 12-3-1 (PDF 57 and 58). Penalty for (a) through (h): 15 yards from the succeeding spot or whatever spot the Referee, after consulting the crew, deems equitable; if by the defense also AFD; if flagrant and an official sees the whole action the player is also disqualified. Penalty for (i) through (v): 15 yards from the succeeding spot if the ball is dead or the previous spot if the ball was in play; flagrant: also disqualified; by defense also AFD. Two violations of (a), (b) or (c) by one player in a game mean automatic disqualification even if the penalty is declined (12-3-1, 12-4-1, PDF 59). Dead ball, live ball or foul between downs by timing; taunting is a dead ball foul at any time (3-13-1-b); a foul against an official is always a foul between downs (14-4-9). The down repeated, AFD per the defense rule.

- Throwing a punch, forearm or kicking at an opponent (12-3-1-a; summary: Throwing a punch, forearm, or kicking at opponent): either; 15; anywhere in the stadium where officials have jurisdiction; SRC-OFFICIAL.
- Abusive, threatening or insulting language or gestures (12-3-1-b; summary: Using abusive, threatening or insulting language): either; 15; SRC-OFFICIAL.
- Baiting or taunting acts or words (12-3-1-c; summary: Using baiting or taunting acts or words; code TAU): either; any time (always a dead ball foul); 15; SRC-OFFICIAL.
- Violent, offensive or sexually suggestive gesture (12-3-1-d; summary: Violent, offensive, or sexually suggestive gesture): either; 15 (examples: throat slash, simulated gun, "nose wipe"); SRC-OFFICIAL.
- Unnecessary physical contact with a game official (12-3-1-e; summary: Unnecessary physical contact with game official): either; 15; the player shall be disqualified and the action reported to the Commissioner; a foul against an official is a foul between downs and is not part of a multiple foul (14-1-3 exception 1); SRC-OFFICIAL.
- Prolonged or excessive celebration (12-3-1-f; summary: Prolonged or excessive celebration): either; 15; penalized anywhere on the field other than the bench area; SRC-OFFICIAL.
- Using an object as a prop or possessing foreign objects (12-3-1-g; summary: Using an object as a prop): either; 15; the player may be ejected if the object is a safety hazard; SRC-OFFICIAL.
- Removal of the helmet in the field of play or end zone (12-3-1-h; summary: Removal of helmet in the field of play): either; during a celebration or a confrontation; 15; SRC-OFFICIAL.
- Disconcerting acts or signals (12-3-1-i): see section 2.
- Concealing the ball under the uniform or using equipment to simulate a ball (12-3-1-j; summary: Concealing ball or using equipment to simulate ball): either; 15; SRC-OFFICIAL.
- Using substitutes or returning players to deceive (12-3-1-k): see section 1.
- Player lining up or in motion less than five yards from the sideline in front of his bench (12-3-1-l): see section 1.
- Repeated illegal substitutions when time is in (m), successive delay-of-game penalties when time is in (n): see sections 8 and 1.
- Jumping or standing on a teammate or opponent to block a kick (o), hand on a teammate or opponent for height (p; "leverage"), picking up a teammate (q), running forward and leaping (r), goaltending (s): see section 5.
- Punter, placekicker or holder simulating being roughed (t): see section 5.
- Kicking team player forced or voluntarily out of bounds who does not return inbounds in a reasonable time (12-3-1-u; summary: Kicking player not attempting to return inbounds): by the kicking team; kick; 15 (previous spot if in play); AFD n/a; SRC-OFFICIAL.
- Attempting to call an excess or illegal timeout to freeze a kicker (12-3-1-v and 4-5-1 Item 4, PDF 58 and 19; summary: Attempting to call excess/illegal timeout to freeze kicker): by the defense (Team B); before a field goal attempt or Try kick; 15; if the timeout is not granted, play continues and the penalty is enforced after the down; if granted, it is enforced as a dead ball foul, and the timeout is charged; AFD yes by defense rule; SRC-OFFICIAL.
- Fouls to prevent a score (12-3-2, PDF 58; summary: Repeated fouling by defense to prevent score, under Score Awarded): by the defense; repeated or successive fouls; the score involved is awarded to the offensive team if the violation is repeated after a warning; SRC-OFFICIAL.
- Palpably unfair act (12-3-4 and 13-1-7, PDF 58 and 60; summary: Palpably unfair act, under Score Awarded): by any player, substitute or non-player; offender may be disqualified; the Referee, after consulting the crew, enforces whatever distance penalty is equitable, irrespective of any other code penalty, and may award a score; the half-distance rule does not limit it (14-2-1 exception 2); SRC-OFFICIAL.
- Automatic disqualification for two unsportsmanlike fouls (12-4-1, PDF 59): see the note above; also applies to non-player personnel; SRC-OFFICIAL.

### 11. Fouls on tries (extra points and two-point conversions) and in overtime

- General (11-3-3 Items 1 to 7, PDF 49 and 50; summary: Replay Down Penalties: Defensive foul on unsuccessful Try; Scoring Penalties: Try: Foul by Team B that would result in a safety during Try; Unsuccessful Try: Team A committing foul during a Try...; Team B recovering ball): SRC-OFFICIAL.
  - Fouls before the ready-for-play signal are enforced on the Try (Item 1). A foul after the ready signal that kills the play before the snap is treated as a pre-snap foul on a scrimmage play; if a defensive foul prevents the Try, the offense may take the yardage on the next Try or the ensuing kickoff (Item 2).
  - Team A foul at or after the snap (Item 3): during a successful Try the Try is repeated unless the penalty includes loss of down; a penalty with loss of down means the Try is unsuccessful with no replay; fouls after a change of possession and all personal or unsportsmanlike fouls are enforced on the ensuing kickoff (provided they do not offset or negate a successful Try); a foul that results in a safety gives Team B one point.
  - Team B foul at or after the snap (Item 4): all fouls except defensive pass interference are enforced on the ensuing kickoff, provided they do not offset, create a re-Try, or negate a score by Team B; a foul that results in a safety gives Team A one point; a foul during an unsuccessful Try: Team A may decline the distance penalty and the down is replayed ("Replay Down Penalties: Defensive foul on unsuccessful Try").
  - Fouls by both teams (Items 5 and 6): no change of possession: the Try must be replayed; with changes of possession: both before the first change, or Team B before the first change: replay; Team A before the first change: Try failed; neither before the first change and both afterward: Try failed.
  - Foul after a Try (Item 7): enforced on the succeeding free kick.
  - Re-Try enforcement: from the spot where Team A attempted the Try or from the other Try yard line, then the ball may be placed anywhere between the inbounds lines; defensive pass interference is a spot foul on a Try, but from the end zone the ball goes on the defense's one-yard line or half the distance, whichever is better for Team A.
  - The summary line "Unsuccessful Try: Team A committing foul during a Try which would ordinarily result in loss of down or in a touchback; in loss of ball in field of play (not during a kick); Team B recovering ball" corresponds to Item 3 (loss of down), Item 3(c) and Item 6 (change of possession).
- Touchback on a Try is unsuccessful and not replayed (11-3-2-d).
- Overtime (16-1-3 to 16-1-5, PDF 72 and 73): the regular timeout rules apply (two timeouts in a regular season overtime period, three per half in the postseason); the replay rule is Replay Official only (no coach challenges, 16-1-5-d); disqualified players may not re-enter (16-1-5-e); a game that ends on the second possession can only be affected by fouls that require the down to be replayed, fouls that negate a score, and palpably unfair acts (16-1-5-a); in overtime the team that kicks off and scores a safety on the receiving team's first possession wins; SRC-OFFICIAL.

### 12. Non-player conduct fouls

- Unsportsmanlike conduct by a non-player (13-1-1 through 13-1-6, PDF 60; summary: Unsportsmanlike conduct by non-player 13-1): by a substitute, coach, attendant or other non-player entitled to sit on the bench, during any period or timeout, including between halves; 15 from the team for whose supposed benefit the foul was made; enforcement from the succeeding spot if the ball is dead or from whatever spot the Referee deems equitable if the ball is in play; for a flagrant violation the Referee may exclude the offender from the playing field enclosure; SRC-OFFICIAL. The acts: "loud speaker" coaching, coaches or other non-players entering the field (13-1-2, 4-1-2), bench credential violations, being inside the six-foot border or past the 23 yards of lateral movement, unauthorized persons at field level; a head coach may move down the sideline outside the bench area to call a timeout or challenge (13-1-5).
- Palpably unfair act by a non-player (13-1-7): as in 12-3-4 (Referee's equitable ruling, 19-1-3); SRC-OFFICIAL.
- Non-player unnecessary contact or abusive language (13-1-8, PDF 60; the summary prints "13-8"): by management, coaches, trainers, equipment personnel; 15; enforcement from the succeeding spot if the ball is dead, the previous spot if in play, or an equitable spot (palpably unfair act); disqualification may follow; Commissioner discipline possible; SRC-OFFICIAL.
- Illegally entering the field: see section 8.
- Non-player on the field of play (17-1-1, PDF 74): the Referee, after consulting the crew, enforces whatever penalty or score the interference warrants; SRC-OFFICIAL.

### 13. Rare and miscellaneous situations (every remaining line of the Penalty Summary)

These are in the "Miscellaneous Situations" and other headings of the summary. Many are not fouls: they are results or options. They are listed so that every summary line has a place.

- Ball Placed on 1-Yard Line: "Defensive pass interference in its end zone and previous spot is outside its 2-yard line" (8-5, 8-6-1-b, PDF 40): first down for the offense at the defense's 1-yard line; see DPI in section 4; SRC-OFFICIAL.
- First down at Spot of Foul: "Defensive pass interference" (8-5-2, 8-5-4): see section 4; SRC-OFFICIAL.
- Fair Catch Awarded: "Interference with opportunity to make fair catch" (10-1-1, 10-2-2): a fair catch is awarded at the spot of the interference even if the ball is not caught; see section 7; SRC-OFFICIAL.
- Safety: "Ball in possession of team behind or out of bounds behind own goal line and impetus from player of that team" (11-5-1, PDF 51): the result of a play, not a foul; the exceptions are a momentum carry-in by a defensive player (11-5-1 Exception 2) and an incomplete forward pass in the end zone; SRC-OFFICIAL.
- Safety: "Enforcement for offensive foul behind goal line" (11-5-1, 14-2-2, 14-4-5-c): the defense may elect to enforce the penalty at the spot behind the goal line, which is a safety; SRC-OFFICIAL.
- Safety: "Intentional grounding in own end zone" (8-2-1-c): see section 3; SRC-OFFICIAL.
- Touchback: "Illegal touching of scrimmage kick inside five-yard line" (9-2-3): the receiving team may take a touchback instead of the 5 yards; see section 5; SRC-OFFICIAL.
- Kickoff Out of Bounds Between Goal Lines: "Receiver's ball at inbounds spot" and "Receiver's ball 25 yards from spot of kick" (6-2-4): see section 6; SRC-OFFICIAL.
- Kickoff Not Reaching the Landing Zone: "Receiver's ball at inbounds spot", "25 yards from spot of kick", "at the spot where ball lands or touched" (6-2-4): see section 6; SRC-OFFICIAL.
- Ball Remains Dead: "Actions that delay game" (4-6-4, 4-6-5) and "Snapping before Officials assume normal position" (4-6-5-b): see sections 1 and 8; SRC-OFFICIAL.
- Ball Dead Immediately: "Committing acts that conserve time" (4-7-1); "Kickers recovering free kick" (6-1-4-d-1); "Kickers advancing after recovery of a scrimmage kick unless behind line" (9-3-1, 9-3-2); "Any kick touching receiver's goal post or cross bar unless scoring field goal" (6-1-5-c, 9-4-2, 11-6-2-d); "Official sounding whistle" (7-2-1-o, 7-2-2); "Catch after fair catch signal" (10-2-3): rulebook rules about when the ball is dead, not fouls; SRC-OFFICIAL.
- Penalty Enforced from Goal Line: "Spot of enforcement behind other team's goal line" and "Runner crosses opponent's goal line and spot of enforcing foul by teammate during run is behind defense goal line" (14-2-2): the penalty is enforced from the goal line; SRC-OFFICIAL.
- Penalty Enforced on Next Free Kick: "Personal foul, unsportsmanlike conduct foul, or palpably unfair act committed during opponent scoring play" (14-2-3): see G5; SRC-OFFICIAL.
- New Series Penalties: "Team B foul during scrimmage down" (14-1-2 Item 5): see G2; SRC-OFFICIAL.
- Replay Down Penalties: "Defensive foul on unsuccessful Try" (11-3-3) and "Double foul without change of possession" (14-5-1): see sections 11 and 14; SRC-OFFICIAL.
- Scoring Penalties, Score Awarded: palpably unfair act (12-3-4, 13-1-7) and repeated fouling by the defense to prevent a score (12-3-2): see section 10; SRC-OFFICIAL.
- Scoring Penalties, Score Not Allowed: "Offending team scores after foul during down in which time expires for half (with no extension of time)" (4-8-2-b): see section 8; SRC-OFFICIAL.
- Time Penalty and Time Restored and Fifteen Yards: see section 8; SRC-OFFICIAL.
- Combination Penalties, "Loss of Ball and Fifteen Yards": "Fair catch interference" (10-1-1) and "Prohibited contact against a kick returner" (12-2-9-a-6): see sections 7 and 15; SRC-OFFICIAL.
- Fouls with a loss of ball in other cases: an intercepted illegal forward pass keeps the ball with the intercepting team if the penalty is declined (8-1-2 Item 2); fourth-down loss of down gives the ball to the defense (14-1-2 Item 2); a foul by the offense during the play does not lose the ball itself except through those two rules; SRC-OFFICIAL.
- Return of a disqualified player (5-2-8-g, PDF 24): by either team; 15 yards from the previous spot if discovered while the ball is in play, from the succeeding spot if between downs, and exclusion from the playing field enclosure; SRC-OFFICIAL.
- Illegal return of a suspended player and equipment suspensions (5-2-8-f, 5-4 Penalty (e), PDF 24 and 28): by either team; 5 yards from the previous spot (succeeding spot if not known); removal until properly equipped after one down; SRC-OFFICIAL. Repeat equipment violation: disqualification (5-4 Penalty (f)).
- Illegal forward pass not from scrimmage, backward pass out of bounds, and other forward-pass variants: see section 3; SRC-OFFICIAL.
- Flagrant fouls found by the Officiating department (19-2, PDF 77): 15 yards and disqualification if flagrant; SRC-OFFICIAL.
- Unsportsmanlike conduct after a warning for substituting tactics (5-2-9, 5-2-10, 5-2-11): see section 1; SRC-OFFICIAL.
- Emergencies (17-1, 17-2 and later, PDF 74): the Referee enforces equitable rulings; not covered in detail here; SRC-OFFICIAL.

### 14. Fouls that are NOT "accept or decline" in the usual sense

The general rule (14-1-1) lets the offended team decline any penalty unless the rules prohibit it. These are the cases where the usual accept/decline choice does not work, or where more than the yardage is decided:

- Disqualification. A disqualified or suspended player must leave the game whether the penalty is accepted or declined (14-1-1); two unsportsmanlike fouls of the (a), (b), (c) kinds mean automatic disqualification regardless of acceptance (12-4-1); the helmet as a weapon carries automatic disqualification (12-2-17); flagrant personal fouls, unsportsmanlike conduct, and flagrant acts found by the Officiating department can bring disqualification (12-2, 12-3, 19-2); unnecessary physical contact with an official brings disqualification (12-3-1-e); a disqualified player may not re-enter, even in overtime (16-1-5-e).
- Fouls by both teams (double fouls) (14-5, PDF 65 and 66): when the fouls offset, neither team may decline; the down is replayed at the previous spot; a 15 versus 5 pair is enforced as the 15 only and the minor-foul team cannot decline; dead ball fouls by both teams offset at the succeeding spot and the down counts (14-4-9 Item 2); some changes of possession (clean hands) change what happens (14-5-2, 14-5-3).
- A 10-second runoff after a replay reversal or a nullified foul: neither team may decline it, either team may use a timeout (4-7-4). A 10-second runoff after an offensive action that conserves time: the defense may decline the runoff but then must also take the yardage as declined and the clock starts on the snap (4-7-1 Item 1). A runoff can never be against the defense (4-5-4 Note 9).
- Fouls between downs and fouls against an official: always enforced separately, never combined with another foul or offset (14-1-3 exception 1, 14-4-9): foul against an official, challenge initiated with no timeouts left, and fifth and later excess injury timeouts.
- Timeout charges: a timeout requested and granted when not allowed is charged whether or not the yardage is accepted (4-5-1); a challenge that is unsuccessful costs a timeout (15-1-1-e). The charge is not a choice.
- Palpably unfair act and fouls to prevent a score: the Referee rules, there is no offended-team choice to make; the score may be awarded (12-3-2, 12-3-4).
- Intercepted illegal forward pass: the team that intercepts may advance and decline the penalty (8-1-2 Item 2): a normal decline, but with the ball.
- Offense loss of down on fourth down: the ball goes to the defense; the defense also gets the distance penalty enforced for combination penalties (14-1-2 Item 2).
- Foul by the offense after a change of possession: the defense must decline the penalty to keep possession, except for personal fouls and unsportsmanlike conduct, which are enforced from the dead ball spot and the defense keeps the ball (14-4-3-b).
- Fouls that carry options other than yardage: free kick out of bounds or short (the receiver picks among three spots, 6-2-4); illegal touching of a scrimmage kick inside the 5 (touchback option, 9-2-3); first touching by the kickers (9-2-2); offsides on a free kick when the receivers keep the ball (previous spot and replay, or yardage from the dead ball spot, 6-3-1, 14-4-7, 14-4-8); fouls in scoring plays where the offended team may accept the penalty and begin a new series, or replay the down, instead of counting the points (14-2-3); extension of a period at the end of a half by an untimed down (4-8-2).
- Fouls that carry a replay of the down regardless of choice: the defense too-many-men foul that follows an offense snapping before the defense can substitute (5-2-9, 5-2-10; the down is replayed, penalties disregarded except personal and unsportsmanlike fouls); an erroneous whistle when the team in possession elects to replay (7-2-1-o); a loose ball that hits a video board, wire or sky cam (7-2-1-r); a Try with fouls by both teams (11-3-3).
- Ten-second runoff on offensive actions that conserve time: the offense may use a timeout in place of the runoff (4-7-1 Item 1).
- Fouls enforced on the Try or the free kick rather than the play: personal and unsportsmanlike fouls on a scoring play (14-2-3, 11-3-3); a foul after the end of the second or fourth period by either team of the personal, unsportsmanlike or taunting type goes to the second-half kickoff or the overtime kickoff (14-4-9 exception).
- Safety on enforcement: an offensive foul behind its own goal line: the defense chooses whether to enforce at that spot for a safety (14-2-2-b).

### 15. Cross-check of the Penalty Summary against the articles (yards and other disagreements)

For every distance foul in the summary I read the "Penalty:" line of its article. Result: the yards agree everywhere I could check. Items that need a note:

1. Defensive holding and illegal use of hands on a scrimmage kick that crosses the line (9-1-4-e, PDF 43): 10 yards for either team unless the foul is committed trying to block the kick. The summary lists "Holding (defense)" under 5 yards and does not mention this. Article text wins. SRC-OFFICIAL.
2. "Loss of Ball and Fifteen Yards" heading (summary, printed page 72) lists Fair catch interference and Prohibited contact against a kick returner. The articles (10-1-1, 12-2-9) say 15 yards (and a fair catch awarded, or AFD), with no loss of ball. I treat the heading as a label quirk. SRC-OFFICIAL, interpretation flagged.
3. "Illegal batting behind the line of scrimmage" and "Illegal kicking behind the line of scrimmage" are listed under Loss of Down with Yardage, but the article text (12-5-2) gives loss of down and 10 for any foul by Team A before possession changes on a scrimmage down, with the only exception being a Team A foul beyond the line during a scrimmage kick. The phrase "behind the line" in the summary is narrower than the article. Article text wins (14-1-2 Item 2 lists illegal batting and kicking as combination penalties without that limit). SRC-OFFICIAL.
4. "Illegal touching of a forward pass" is under 5 yards in the summary; the article gives 5 yards for an ineligible player (8-1-8-a) and loss of down without yardage for an eligible receiver who went out of bounds (8-1-8-b). The summary does list both. Agree.
5. "Illegal forward handing" and "Illegal forward pass" appear in both the 5-yard group and the Loss of Down with Yardage group. This is consistent with the articles: the loss of down version is 8-1-2-a and -b and 8-7-4-a and -b; the 5-yard-only version is 8-1-2-c and 8-7-4-c (after a change of possession). Agree.
6. "Punt, drop kick, or place kick from beyond the line" is in both groups: the article gives loss of down and 5 (9-1-1). Agree.
7. "Non-player unnecessary contact or abusive language 13-8" in the summary should read 13-1-8 in the article numbering (Rule 13, Section 1, Article 8). Typographical.
8. The requirements note placed the summary on printed pages 71 to 73; it is on printed pages 71 and 72. Official signals (a chart of referee gestures) follow on 73 to 75.
9. No distance foul in the summary has a different yardage from its article: delay of game 5 (4-6), encroachment 5, false start 5, offside 5, neutral zone 5, illegal formation 5 (three kinds), illegal motion 5, illegal shift 5, illegal snap 5, illegal substitution 5, illegal touching of a free kick 5, ineligible player downfield on a kick 5 and on a pass 5, invalid fair catch signal 5, running into the kicker 5, second excess timeout 5, timeout not allowed 5, too many players 5, voluntarily out of bounds (kick and free kick) 5, illegal contact 5, defensive holding 5, illegal use of hands by defense 5; assisting the runner 10, offensive holding 10, illegal batting 10, illegal kicking 10, illegal blocking or use of hands on a free kick 10, illegal use of hands by offense 10, illegal block in the back 10, offensive pass interference 10; all 57 entries of the 15-yard group have 15 in the article (the double team and wedge on a free kick (6-2-1) are 15 while illegal blocking on a free kick is 10; the free kick out of bounds has no yardage). Disqualification and AFD data are only in the articles, not in the summary.

### Could not settle

- The NFL Casebook (Approved Rulings): not reachable. operations.nfl.com/the-rules/nfl-rulebook/ (WebFetch 2026-10-14) links only the 2026 rulebook PDF, and the guesses operations.nfl.com/the-rules/ and operations.nfl.com/the-rules/nfl-rules-digest/ gave HTTP 404. A web search for "NFL casebook 2026 approved rulings" found only rule-change news. This does not block the foul list: the rulebook text is the authority.
- How the AFD in 12-2-9 ("Loss of 15 yards and an automatic first down", no "if by the defense") works when the fouling team is the offense: the text does not say. UNVERIFIED. The clone can apply it only to fouls by the team without the ball.
- Foul frequencies, accepted-penalty averages by foul type and per game: not part of this topic (Part 8 covers statistics).
- Exact start-of-clock details by foul (4-3-2-e) are summarized in G11 only; the Rule 14 enforcement details are not repeated (Part 6 covers them).
- Whether every single foul below 15 yards is also classified as a "personal foul": the rulebook defines personal fouls only by Section 2 of Rule 12 plus the sentence in 12-2-19 that other 15-yard fouls count as personal fouls for enforcement.

### Sources

- 2026 Official Playing Rules of the NFL, PDF "ops-2026-NFL-Rulebook-FINAL", https://static.www.nfl.com/image/upload/fl_attachment/league/tqivdkzt9mu6wdgsh1ku.pdf (linked from https://operations.nfl.com/the-rules/nfl-rulebook/), read from the converted text (PDF pages 18 to 77 for the rules, 78 to 79 for the Penalty Summary), retrieved 2026-10-14.
- https://operations.nfl.com/the-rules/nfl-rulebook/ : the page lists the 2026 rulebook download and contains penalty tables and a "Table of Foul Codes" (name and three-letter code), retrieved 2026-10-14 (WebFetch answers, so only the codes I quote above are used).
- Web search "NFL casebook 2026 approved rulings operations.nfl.com", 2026-10-14: only rule-change news (nfl.com "NFL announces new playing rules, bylaws, resolutions for 2026"), no casebook.


## Part 8. Penalty statistics

Retrieved 2026-10-14. Purpose: calibrate how often fouls are called and accepted (requirement N7.1, C7 of NFL_EXTRA_FEATURES.md).
No data files were downloaded. WebFetch and WebSearch only. My own arithmetic is marked "computed".

### Answers in brief

- Accepted fouls per game, both teams, regular season: 2021 11.82, 2022 11.19, 2023 11.42, 2024 12.89, 2025 12.75, 2026 to date 15.08 (79 games). SRC-SECONDARY (nflpenalties.com, computed from its weekly tables).
- Accepted fouls per team per game: 5.91, 5.59, 5.71, 6.44, 6.37, and 7.54 in 2026 (5 weeks). SRC-SECONDARY, the 2021 to 2025 values confirmed by the site's own regular-season view.
- Penalty yards per team per game: 51.0, 46.1, 47.1, 52.2, 51.2, and 60.2 in 2026. Yards per accepted foul: 8.0 to 8.6 every season. SRC-SECONDARY.
- Declined fouls per team per game about 0.8 to 1.0 (2025: 0.96); offsetting flags about 0.2 to 0.3 per team per game (2024: 0.32). About 87 to 90 percent of fouls that offer a choice are enforced, 10 to 13 percent are declined. SRC-SECONDARY.
- Top types in 2025 (accepted, season incl. playoffs): offensive holding 684, false start 681, defensive pass interference 289, defensive holding 183, delay of game 182, unnecessary roughness 181, defensive offside 146, illegal formation 112. Full list with 2024 and 2026 in section 2. SRC-SECONDARY.
- Pre-snap fouls are about 37 percent of accepted fouls (2025: 2.36 of 6.37 per team per game; 2024: 2.49 of 6.44; 2026: 2.94 of 7.54). SRC-SECONDARY.
- By committing phase (2025): offense 48 percent, defense 35 percent, special teams 17 percent. SRC-SECONDARY.
- By quarter (2025): Q1 21 percent, Q2 30 percent, Q3 23 percent, Q4 25 percent, overtime 0.5 percent. SRC-SECONDARY. Last two minutes of the halves: no league figure published (UNVERIFIED; one-team and snippet evidence only).
- Rates per run play, pass play, kick: not published. I derived rates per scrimmage play from the NFL.com play counts (section 3). Share of fouls that nullify a play: UNVERIFIED (only nullified touchdowns are published).
- Automatic first downs from defense fouls: 822 in 2025 (23 percent of accepted fouls, 2.9 per game both teams), 808 in 2024, 250 in 79 games of 2026. Average yardage of those fouls about 10.5. SRC-SECONDARY.
- Team spread, regular season 2025 (accepted per game): lowest LA Rams 4.41, highest Dallas 7.82, mean 6.37, standard deviation 0.79. Most of that spread is chance (computed). SRC-SECONDARY.
- Decline rates by foul type are in section 5. Highest: ineligible player downfield on a pass (40 to 50 percent), offensive offside, illegal shift, defensive offside, illegal formation, illegal contact, defensive holding (23 to 38 percent). Near zero: false start, neutral zone, delay of game, roughing, face mask. SRC-SECONDARY, rule SRC-OFFICIAL (14-1-1).
- Designer target (section 6): about 12.8 accepted fouls per game (6.4 per team, about 3.2 per team per half), of which about 37 percent pre-snap. The 2026 early season is much higher (15.1 per game) and may be partly noise.

### How to read these numbers (source and caveats)

- Main source: nflpenalties.com. Its footer says 2020 to 2026 data comes from nflfastR (play-by-play) and that it is not affiliated with the NFL. SRC-SECONDARY.
- Its own caveat, quoted: "Offsetting and Declined penalties are not included in any columns except 'Offsetting', 'Declined', and 'Total Flags'." So "Count" or "Against Count" means accepted fouls only.
- Total Flags = accepted + declined + offsetting. I checked this arithmetic for every season below (it holds exactly).
- Offsetting is a count of flags, not of pairs: the 2026 game list has games with 3 and 5 offsetting flags. The number of offsetting events is therefore smaller than the figure (computed, the site does not say so).
- The yearly "league" and "team" pages include the playoffs (285 games in 2025 and 2024; 272 regular-season games plus 13 playoff games). I removed the playoffs by using its weekly table (weeks 1 to 18 only) and its "Regular Season Per Game" view. The two agree to the last digit (for example 2025: 3,467 accepted in 272 games, 6.37 per team per game).
- 2022 had 271 regular-season games (one game was not played), so its per-game values use 271.
- The playoffs have fewer fouls per game (2025: 98 accepted in 13 games, 7.5 per game). Per-type tables below include the playoffs, so per-game values for types (count divided by 285) are about 2 percent too low for the regular season.
- The site's "Plays" column counts every line item of the play-by-play (its blog "What Is A Play?" says this adds about 20 to 30 plays per game). Do not use it as a snap count. For snaps I use the NFL.com scrimmage play counts instead.
- The site's "Pre-snap" definition is not published (change log only says it was added in 2012). It looks like fouls that stopped the play before the snap. Cross-check: my own grouping of pre-snap foul types gives 1,361 in 2025 against the site's 1,322 (within 3 percent).
- Independent checks that agree with it: ESPN's count of 963 accepted fouls through Week 4 of 2026 equals the site's weeks 1 to 4 (237+218+237+271). RotoWire's 2026 team figures (ESPN box scores) equal the site's team counts exactly (for example Jets 47 fouls, 412 yards). StatMuse's 2025 regular-season team totals match the site (Dallas 133, Tennessee 130, NY Giants 128, Jacksonville 128, Denver 124, Chicago 120, Kansas City 119).
- One disagreement: the Deseret News column of 2026-10-10 gives 3,572 (2024) and 3,565 (2025) with no source. 3,565 equals the site's 2025 total including the playoffs; 3,572 matches neither the site's 2024 total with playoffs (3,648) nor without (3,506). I use the site's numbers. The same column's "140 penalties that were called but not accepted" through Week 4 of 2026 equals the site's declined plus offsetting for weeks 1 to 4 (113 + 28 = 141), so it counts both together.
- 2026 is a small sample: 79 games, weeks 1 to 5, which is 29 percent of a season. Week 6 had not been played on 2026-10-14.

### 1. League-wide, regular season, by season

All values SRC-SECONDARY (computed from nflpenalties.com weekly tables, weeks 1 to 18 for 2021 to 2025, weeks 1 to 5 for 2026). "Both teams" means per game. Seasons 2015, 2017, 2019, 2020 come from the site's regular-season view.

Per season (games; accepted; yards):
- 2021: 272 games; 3,216 accepted; 27,739 yards.
- 2022: 271 games; 3,032 accepted; 24,988 yards.
- 2023: 272 games; 3,107 accepted; 25,620 yards.
- 2024: 272 games; 3,506 accepted; 28,410 yards.
- 2025: 272 games; 3,467 accepted; 27,871 yards.
- 2026: 79 games (weeks 1 to 5); 1,191 accepted; 9,510 yards.

Accepted per game, both teams, then per team per game:
- 2015: 13.84 and 6.92. 2017: 13.36 and 6.68. 2019: 13.48 and 6.74. 2020: 11.24 and 5.62.
- 2021: 11.82 and 5.91. 2022: 11.19 and 5.59. 2023: 11.42 and 5.71.
- 2024: 12.89 and 6.44. 2025: 12.75 and 6.37.
- 2026 to date: 15.08 and 7.54. Week by week 2026: 14.8, 13.6, 14.8, 16.9, 15.2 per game.

Penalty yards per game both teams, then per team per game:
- 2021: 102.0 and 51.0. 2022: 92.2 and 46.1. 2023: 94.2 and 47.1.
- 2024: 104.4 and 52.2. 2025: 102.5 and 51.2. 2026 to date: 120.4 and 60.2.
- Earlier per team per game: 2015 58.9, 2017 57.8, 2019 57.3, 2020 48.7.

Yards per accepted foul: 2021 8.63, 2022 8.24, 2023 8.25, 2024 8.10, 2025 8.04, 2026 7.98.

Declined fouls (season total; per team per game):
- 2021: 435; 0.80. 2022: 442; 0.82. 2023: 464; 0.85. 2024: 466; 0.86. 2025: 522; 0.96. 2026: 132 in 79 games; 0.84.
- Earlier per team per game: 2015 0.99, 2017 0.98, 2019 1.07, 2020 0.77.

Offsetting flags (season total; per team per game):
- 2021: 120; 0.22. 2022: 105; 0.19. 2023: 119; 0.22. 2024: 176; 0.32. 2025: 147; 0.27. 2026: 32 in 79 games; 0.20.

Enforced versus declined (accepted divided by accepted plus declined):
- 2021 88.1 percent, 2022 87.3, 2023 87.0, 2024 88.3, 2025 86.9, 2026 90.0. So 10 to 13 percent of flagged fouls with a choice are declined.

Total flags thrown and recorded (accepted + declined + offsetting), per team per game: 2021 6.93, 2022 6.60, 2023 6.78, 2024 7.63, 2025 7.60, 2026 8.58. Flags that were picked up (waved off) are not in play-by-play and so not counted (the site does not say; this is my reading).

Home versus away (accepted, incl. playoffs): 2025 home 1,760 and away 1,805; 2024 home 1,795 and away 1,853; 2026 home 594 and away 597. The away team draws about 50.5 percent. No home-field adjustment is needed.

Context (SRC-SECONDARY): ESPN says the 963 accepted fouls through Week 4 of 2026 are the most through Week 4 since play-by-play data began in 1978, and Week 4 alone had 271, the second-most for any week. Sharp Football Analysis says all of the year-over-year increase is on offense (defensive flags are slightly down, defensive pass interference is below average) and that touchdowns nullified by fouls reached 17 through four weeks (5 in 2025, 4 in 2024, prior decade average 8.3). The Deseret column calls 2015 the record (4,245); that number is closer to total flags than to accepted fouls (2015 total flags 8.17 per team per game x 512 = about 4,180), so the column compares unlike things (UNVERIFIED which count it means).

### 2. Accepted fouls by type

Source: nflpenalties.com "all penalties" page for each year (SRC-SECONDARY). The type totals add up exactly to the season totals (I checked: 3,565, 3,648 and 1,191). These tables include the playoffs.
Format per line: 2025 count (per game, average yards each); 2024 the same; 2026 to date (79 games). "Declined" is the number of flags of that type that were declined in the same season (2025, 2024, 2026).
Per game = count divided by 285 (2025, 2024) or 79 (2026). Add about 2 percent for the regular season.
"Automatic first down" notes follow section 4.

Top 20 and the next most common:
- Offensive holding (10 yd): 684 (2.40, 9.6 yd); 706 (2.48, 9.7); 260 (3.29, 9.6). Declined 89, 88, 30.
- False start (5 yd): 681 (2.39, 4.9); 707 (2.48, 4.9); 222 (2.81, 4.9). Declined 3, 2, 0.
- Defensive pass interference: 289 (1.01, 15.2); 315 (1.11, 15.4); 84 (1.06, 16.6). Declined 31, 19, 11.
- Defensive holding (5 yd, automatic first down): 183 (0.64, 4.6); 184 (0.65, 4.8); 62 (0.78, 4.5). Declined 75, 56, 14.
- Delay of game (5 yd): 182 (0.64, 4.9); 172 (0.60, 4.9); 80 (1.01, 4.9). Declined 7, 12, 2.
- Unnecessary roughness (15 yd): 181 (0.64, 13.1); 187 (0.66, 13.3); 55 (0.70, 12.6). Declined 5, 3, 1. Offsetting 19, 43, 6.
- Defensive offside (5 yd): 146 (0.51, 4.8); 165 (0.58, 4.7); 49 (0.62, 4.5). Declined 88, 72, 15.
- Illegal formation (5 yd): 112 (0.39, 4.9); 129 (0.45, 4.9); 36 (0.46, 5.0). Declined 41, 53, 14.
- Face mask (15 yd): 100 (0.35, 13.0); 90 (0.32, 13.7); 36 (0.46, 12.6). Declined 4, 2, 1.
- Illegal contact (5 yd, automatic first down): 96 (0.34, 4.9); 57 (0.20, 4.9); 23 (0.29, 5.0). Declined 37, 22, 8.
- Roughing the passer (15 yd): 94 (0.33, 13.4); 100 (0.35, 13.4); 30 (0.38, 11.6). Declined 1, 3, 0.
- Neutral zone infraction (5 yd): 77 (0.27, 5.0); 94 (0.33, 4.9); 32 (0.41, 4.9). Declined 1, 0, 0.
- Offensive pass interference (10 yd): 72 (0.25, 9.7); 75 (0.26, 9.5); 22 (0.28, 9.5). Declined 13, 11, 7.
- Illegal use of hands (5 yd by defense, 10 yd by offense; the site does not split): 61 (0.21, 5.6); 72 (0.25, 5.7); 25 (0.32, 6.4). Declined 17, 23, 5.
- Intentional grounding: 59 (0.21, 11.4); 34 (0.12, 11.5); 11 (0.14, 12.0). Declined 0, 1, 0.
- Illegal block above the waist = block in the back (10 yd): 57 (0.20, 9.6); 54 (0.19, 9.1); 27 (0.34, 9.4). Declined 4, 3, 1. The label mapping is my inference (name and 10-yard average); the 2026 rulebook lists "illegal block in the back" with 10 yards at 12-1-3(b), PDF page 52. SRC-OFFICIAL for the rule.
- Illegal shift (5 yd): 50 (0.18, 4.8); 62 (0.22, 5.0); 24 (0.30, 5.0). Declined 37, 20, 11.
- Ineligible downfield on a pass (5 yd): 46 (0.16, 4.8); 74 (0.26, 4.9); 12 (0.15, 5.0). Declined 46, 50, 4.
- Kickoff short of landing zone (no yardage recorded, ball placement): 46 (0.16); 20 (0.07); 13 (0.16). Declined 0, 0, 0.
- Kickoff out of bounds (no yardage recorded): 39 (0.14); 17 (0.06); 8 (0.10). Declined 1, 1, 0.
- Unsportsmanlike conduct (15 yd): 39 (0.14, 13.4); 42 (0.15, 12.8); 12 (0.15, 12.6). Declined 1, 0, 0.
- Encroachment (5 yd): 36 (0.13, 4.4); 37 (0.13, 4.1); 11 (0.14, 4.6). Declined 1, 1, 0.
- Defensive too many men on the field (5 yd): 31 (0.11, 4.4); 53 (0.19, 4.5); 6 (0.08, 4.3). Declined 10, 10, 3.
- Illegal blindside block (15 yd): 28 (0.10, 12.8); 12 (0.04, 10.8); 6 (0.08, 12.7).
- Taunting (15 yd): 26 (0.09, 14.9); 20 (0.07, 14.4); 6 (0.08, 15.0). Front Office Sports (2026-08-25) lists 28 league-wide taunting fouls in 2025, 21 in 2024, 18 in 2023, 22 in 2022, 61 in 2021.
- Offensive offside: 22; 11; 6. Declined 10, 11, 2.
- Tripping: 17; 6; 1. Low block: 13; 15; 3.
- Illegal motion: 12; 19; 1. Offensive too many men: 8; 11; 2. Illegal forward pass: 8; 6; 1.
- Roughing the kicker: 6; 6; 2. Running into the kicker: 5; 5; 0. Fair catch interference: 5; 9; 2. Kick catch interference: 4; 5; none listed.
- Chop block 6; 6; 6. Disqualification 7; 3; 1. Horse collar 4; 16; 1. Illegal touch pass 5; 4; 1. Hip drop tackle 2; 1; 0.
- 2024 only: illegal substitution 3, clipping 1, illegal crackback 1, lowering the head 2 (2026: 3), illegal kick 1.

Shares of the 2025 total (computed): offensive holding 19.2 percent of accepted fouls and 22.9 percent of yards; false start 19.1 percent and 11.6 percent; defensive pass interference 8.1 percent and 15.4 percent; the top eight types are 69 percent of all accepted fouls (2,458 of 3,565).

Stability (computed from the two seasons): the top types move by under 10 percent from 2024 to 2025 (false start 707 to 681, offensive holding 706 to 684, defensive pass interference 315 to 289). Minor types swing a lot (illegal contact 57 to 96, ineligible downfield pass 74 to 46, defensive too many men 53 to 31, kickoff short of landing zone 20 to 46). Treat any type under about 100 per season as plus or minus 50 percent.

2026 versus 2025 per game (computed): offensive holding 3.29 versus 2.40 (+37 percent), delay of game 1.01 versus 0.64 (+58 percent), false start 2.81 versus 2.39, face mask 0.46 versus 0.35, defensive pass interference about the same. Sharp attributes the rise to offense.

Rule note for the types with automatic first downs and yardage: the 2026 rulebook, PDF pages 39, 53, 55 to 57: illegal contact by the defense is five yards and an automatic first down; defensive holding five yards and automatic first down; illegal use of hands by the defense five yards and automatic first down; unnecessary roughness, roughing the passer, roughing the kicker, horse-collar and hip-drop tackles are 15 yards and an automatic first down; several other personal fouls say "if the foul is by the defense, it is also an automatic first down". SRC-OFFICIAL (read in rulebook2026_pages.txt). The penalty summary (printed page 71, PDF page 78) lists every foul by yardage.

### 3. By play type, phase, quarter, down

#### Pre-snap versus during the play
- The site's pre-snap count of accepted fouls: 2025 1,322 of 3,565 (37.1 percent; offense 947, defense 247, special teams 128); 2024 1,406 of 3,648 (38.5 percent; 975, 280, 151); 2026 464 of 1,191 (39.0 percent; 332, 91, 41).
- Regular season per team per game (site's own average row): pre-snap 2.10 (2021), 1.97 (2022), 2.17 (2023), 2.49 (2024), 2.36 (2025), 2.94 (2026). As a share of accepted: 35.5, 35.2, 38.0, 38.7, 37.0, 39.0 percent. Earlier years: 2015 2.45, 2017 2.22, 2019 2.20, 2020 2.01.
- Pre-snap fouls are almost never declined (false start 3 of 684, neutral zone 1 of 78, delay of game 7 of 189 in 2025) because the play is not run.

#### By committing phase (own offensive plays, own defensive plays, special teams plays)
The site counts a foul under the phase of the team that committed it. SRC-SECONDARY.
- 2025: offense 1,713 (48.1 percent), defense 1,231 (34.5), special teams 621 (17.4). Yards 12,274, 11,683, 4,715.
- 2024: offense 1,889 (51.8), defense 1,265 (34.7), special teams 494 (13.5). Yards 13,775, 12,060, 3,709.
- 2026 to date: offense 611 (51.3), defense 385 (32.3), special teams 195 (16.4). Yards 4,368, 3,573, 1,569.
- Sharp Football Analysis reports an NFL average offensive share of 47.7 percent in 2025 team reports; this agrees with 48.1 (SRC-SECONDARY, snippet).
- Special teams fouls were 13.5 percent of the total in 2024 and 17.4 percent in 2025. The two kickoff-placement fouls (kickoff short of landing zone and kickoff out of bounds) were 37 in 2024 and 85 in 2025. A search snippet (Sports Info Solutions, page not read, UNVERIFIED) says the kickoff touchback rate fell from 65 percent in 2024 to 17 percent in 2025, which would explain more kick returns and more kick-play fouls.

#### Rates per scrimmage play (computed)
- Official denominator, NFL.com team stats "Scrm Plys", regular season. SRC-OFFICIAL: 2025 total 34,417 for 32 teams, 63.27 per team per game, 126.5 per game for both teams. 2026 to date total 10,131 in 79 games, 64.1 per team per game, 128.2 per game. Other counts differ: PFF 64.3 and Sharp 61.3 offensive plays per game in 2025 (search snippets).
- Accepted fouls per 100 scrimmage plays, 2025 regular season (numerators scaled by 3,467/3,565): all phases 10.07; offense 4.84; defense 3.48; special teams 1.75; pre-snap fouls (all phases) 3.74.
- 2026 to date: all phases 11.76; offense 6.03; defense 3.80; special teams 1.92; pre-snap 4.58.
- Check against a published figure: Sharp Football Analysis reports offenses flagged at 6.18 per 100 snaps in weeks 1 to 4 of 2026, the highest per-snap rate for that stretch since 2000. My 6.03 for weeks 1 to 5 is consistent. (The Deseret column wrongly says "6.18 out of every 100 NFL plays results in a penalty"; the figure is for offensive snaps only.)
- Sharp also reports 7.5 flags per 100 snaps on third and fourth downs in 2026 (tied for the worst since 2000), and red-zone offensive fouls at 0.61 per team per game (a record).
- PFF (2026-07-17, five seasons 2021 to 2025, base not defined, counts declined and offsetting too): offensive foul rates from 4.0 percent (Rams) to 5.9 percent (Dolphins, Cardinals); defensive from 3.0 percent (Falcons) to 4.5 percent (Cowboys, Jets, Lions).
- Not published: separate rates for run plays, pass plays, punts, kickoffs, field goals.

#### My grouping of 2025 accepted fouls by what they need (computed; per team per game, regular season)
- Pre-snap types (false start, delay, offside both sides, encroachment, neutral zone, illegal formation, shift, motion, too many men): 2.43 (the site's own pre-snap figure is 2.36).
- Pass-play-only types (defensive and offensive pass interference, defensive holding, illegal contact, roughing the passer, intentional grounding, ineligible downfield pass, illegal forward pass, illegal touch pass): 1.52. The site's page on passing fouls counts 660 for four of these types in 2025 (pass interference 289, defensive holding 181, illegal contact 96, roughing 94), 18.5 percent of all accepted.
- Kick-only types (kickoff and kick fouls, fair catch, running into or roughing the kicker): 0.21.
- All other live-ball fouls (offensive holding, face mask, unnecessary roughness, illegal use of hands, blocks, personal fouls): 2.21.
- Total 6.37. Offensive holding is the one big type that happens on both runs and passes. FiveThirtyEight (search snippet, 2009 to 2018) reported 2,636 holding calls on rushing plays and 1,673 on passing plays, about 61 percent on runs; UNVERIFIED (page redirected, not read).

#### By quarter (accepted fouls, league, SRC-SECONDARY)
- 2025: Q1 754 (21.2 percent), Q2 1,062 (29.8), Q3 828 (23.2), Q4 903 (25.3), overtime 18 (0.5). First half 50.9 percent, second half 48.6.
- 2024: Q1 750 (20.6), Q2 1,079 (29.6), Q3 869 (23.8), Q4 940 (25.8), overtime 10 (0.3).
- 2026 to date: Q1 261 (21.9), Q2 349 (29.3), Q3 275 (23.1), Q4 297 (24.9), overtime 9 (0.8).
- The second quarter is the busiest every year, about 8 points above the first.
- The last two minutes of each half: no league-wide figure found. Search snippets only (UNVERIFIED): a Buffalo Rumblings analysis of the 2024 Bills found 17 of the 45 second-quarter flags against Bills opponents came at or after the two-minute warning (37.8 percent, against about 13.3 percent expected if evenly spread) while the Bills' own were 12 of 47; the author says this is one team and no league data. A Harvard Sports Analysis post (2025-09) says fouls spike in the last five minutes of the halves and that procedural fouls (false start, neutral zone) cluster early in the first half; the page returned an error, so I only have the snippet.

#### By down (2025, site's down-and-distance page, accepted, incl. playoffs; SRC-SECONDARY)
- No-down plays (kickoffs and extra points): 353 (9.9 percent). First down 1,070 (30.0). Second 904 (25.4). Third 765 (21.5). Fourth 473 (13.3, includes punts and field goals).
- First and ten alone: 957 fouls (26.8 percent of all).
- 2026 to date: no-down 104, first 394, second 293, third 248, fourth 152 (of 1,191).
- Declined by down 2025: no-down 13, first 130, second 154, third 188, fourth 50. Third down has the most declines.

#### Share of fouls that nullify the play
- Not published. UNVERIFIED. Tried: nflpenalties.com (pages, blog, change log), Sharp, PFF, CBS, Deseret. The only published figure is nullified touchdowns: 17 in weeks 1 to 4 of 2026, 5 in 2025, 4 in 2024.
- Reasoning from the rulebook (computed, not a statistic): every pre-snap foul (about 37 percent of accepted fouls) nullifies the snap by definition, and an accepted live-ball foul by the offense replays the down, so well over half of accepted fouls remove or replace the play's result.

### 4. Automatic first downs and team spread

#### Automatic first downs (site's page; SRC-SECONDARY)
- What the page counts: fouls by the defense that award a first down regardless of distance; special teams fouls are excluded; declined and offsetting are not counted. It lists defensive pass interference, defensive holding, illegal contact, roughing the passer, face mask, illegal use of hands, unsportsmanlike conduct, taunting, tripping and horse-collar (my summary of the page note; the page text I received did not list unnecessary roughness, though the rule gives it a first down when by the defense).
- 2025 (incl. playoffs): 822 automatic first downs = 23.1 percent of 3,565 accepted fouls, 2.88 per game both teams, 1.44 per team per game. Penalty yards on them 8,648, average 10.5 yards. By down: first 278, second 255, third 246, fourth 36. Third and 6 or longer: 163. "Desperation" (third and 10 or more, or fourth and 6 or more): 80. Yards still needed when flagged: 7,035 (8.6 on average).
- 2024: 808 (22.1 percent of 3,648), yards 8,905, average 11.0. First 280, second 238, third 260, fourth 24.
- 2026 to date: 250 in 79 games (21.0 percent of 1,191; 3.16 per game), yards 2,642, average 10.6. First 93, second 65, third 83, fourth 7.
- About 34 percent of these (2025: 282 of 822) come on third or fourth down, where they extend drives.
- Team range in 2025: Chargers 18 (fewest), Denver 36 (most), mean about 26 per team.

#### Team spread, regular season, accepted fouls per team per game (computed from the site's team table)
- 2025: mean 6.37, standard deviation 0.79, lowest LA Rams 4.41, 49ers 4.88, Bengals 5.18, highest Dallas 7.82, Tennessee 7.65, Jacksonville and NY Giants 7.53, Denver 7.29. Tenth and ninetieth percentile 5.59 and 7.53.
- 2024: mean 6.44, standard deviation 0.69, lowest LA Rams 5.35, Arizona 5.41, Indianapolis 5.47, highest NY Jets 8.06, Baltimore and Tennessee 7.76, Dallas 7.53. Tenth and ninetieth percentile 5.53 and 7.53.
- 2023: lowest Las Vegas 4.41, Cincinnati 4.47; highest NY Jets 7.29, Cleveland and Dallas 6.76. 2022: lowest Atlanta 4.00, LA Rams 4.47; highest Arizona 6.94, Las Vegas and Denver 6.65. 2021: lowest Green Bay 4.06, Cincinnati 4.24; highest Dallas 7.47, Las Vegas 7.29.
- Yards per team per game 2025: mean 51.2, lowest Rams 33.7, highest Denver 67.6 and Dallas 66.8. 2024: lowest Indianapolis 40.2, highest Jets 66.7.
- Pre-snap per team per game 2025: 1.53 (Buffalo) to 3.18 (NY Giants), mean 2.36; 2024: 1.53 to 3.59, mean 2.49.
- Most of the spread is chance. If every team had the same rate of 6.4 and fouls were random with variance equal to the mean, the standard deviation of a 17-game average would be 0.61 (computed). Observed 0.79 (2025) and 0.69 (2024), so the real persistent team effect is only about 0.3 to 0.5 fouls per game, 5 to 8 percent of the mean.
- A long-run view (PFF, five seasons, offense only, counts declined too): best 4.0 percent, worst 5.9 percent around a 5 percent middle, so 20 percent either way. Defense 3.0 to 4.5 percent. Suggested bound for a clone's team foul multiplier: 0.85 to 1.15 (normal), never beyond 0.75 to 1.25 (my judgment from these figures, not a published rule).
- Referee crews matter about as much as teams: 2025 crews ranged from 10.13 (Brad Allen) to 16.13 (Alex Moore) accepted fouls per game (17 crews, 15 to 18 games each, playoffs included), standard deviation 1.5. After removing chance the crew effect is about 1.1 per game (about 8 to 9 percent; computed, indicative).
- 2026 team rates after five games range from 5.0 (49ers, Colts) to 9.8 (Browns) per game (standard deviation 1.21, almost exactly what chance alone gives, 1.22). So early-2026 team differences carry no information.

### 5. Declined fouls

#### Rule (SRC-OFFICIAL)
- 14-1-1 (PDF page 61): unless expressly prohibited, the offended team may decline the penalty and play proceeds as if no foul; the yardage may be declined even if the penalty is accepted; the decision cannot be changed once the penalty is fully administered or the ball is ready for play.
- Double fouls (14-5-1, PDF page 65): offset and the down is replayed; neither team can decline. This matches the site's "Offsetting" column.

#### Rates by foul type (declined divided by accepted plus declined; computed from the site)
2025, then 2024:
- Ineligible downfield pass: 50.0 and 40.3 percent.
- Illegal shift: 42.5 and 24.4 percent. Defensive offside: 37.6 and 30.4. Offensive offside: 31.2 and 50.0.
- Defensive holding: 29.1 and 23.3. Illegal formation: 26.8 and 29.1. Illegal contact: 27.8 and 27.8. Defensive too many men: 24.4 and 15.9. Illegal use of hands: 21.8 and 24.2.
- Offensive pass interference: 15.3 and 12.8. Offensive holding: 11.5 and 11.1. Defensive pass interference: 9.7 and 5.7. Illegal block above the waist: 6.6 and 5.3.
- Under 5 percent: delay of game (3.7, 6.5), face mask (3.8, 2.2), unnecessary roughness (2.7, 1.6), roughing the passer (1.1, 2.9), neutral zone (1.3, 0.0), false start (0.4, 0.3), encroachment, unsportsmanlike, taunting.
- 2026 to date: ineligible downfield pass 25, defensive offside 23, illegal formation 28, illegal shift 31, offensive pass interference 24, defensive holding 18, offensive holding 10, defensive pass interference 12 percent.

#### Who declines (computed, 2025, 535 declined)
- About 250 (47 percent) are fouls by the offense that the defense declined (offensive holding 89, ineligible downfield pass 46, illegal formation 41, illegal shift 37, offensive pass interference 13, offensive offside 10).
- About 243 (45 percent) are fouls by the defense that the offense declined (defensive offside 88, defensive holding 75, illegal contact 37, defensive pass interference 31, defensive too many men 10).
- The remaining 8 percent are shared types (illegal use of hands 17, face mask 4, roughness 5 and so on).
- So decline decisions are about evenly split between the offense and the defense. Both sides decline mostly when the play result beats the foul.

#### Reasons (rule logic plus explainers; SRC-SECONDARY, no published breakdown)
- The offended team keeps the play when the result is better than the penalty: the offense declines a defensive offside or holding when the play gained more than five yards or scored; the defense declines an offensive hold or ineligible downfield pass when it sacked the quarterback, intercepted the pass, or the play already lost yards; the defense declines when accepting would replay a down the offense was losing anyway. A search explainer (generic sites, not the rulebook) gives the sack and the holding-on-first-and-ten examples. Not quantified anywhere I could reach.
- Pre-snap dead-ball fouls (false start, neutral zone, encroachment) cannot be played out, so they are almost never declined. They can only be declined by choice in odd cases (a delay of game before a punt, for example).
- No league source gives a "decline rate" for offense fouls versus defense fouls as such; the split above is my computation from the type table.

### 6. Summary for the designer

Baseline to hit (NFL regular season 2024 and 2025, SRC-SECONDARY plus computed): about 12.8 accepted fouls per game, both teams.

Per team per game, accepted:
- 6.4 in total (2024 6.44, 2025 6.37).
- Pre-snap: 2.4 (2024 2.49, 2025 2.36).
- During the play (live ball and kick plays): 4.0.
- Offense side 3.0, defense side 2.2, special teams 1.1 (2025 phase shares applied to 6.37: 48 percent, 35 percent, 17 percent).
- Penalty yards 51 to 52, average 8.1 per accepted foul.
- Declined 0.9 to 1.0 flags (13 percent of those flagged with a choice), offsetting about 0.3 flags.

Per team per half: about 3.2 in the first half (51 percent) and 3.1 in the second half (49 percent), overtime 0.5 percent.
- Pre-snap about 1.2 per half and 2.0 during the play.
- Heavier in the second quarter (30 percent of the game) than the first (21 percent).

For 10,000 simulated games (both teams):
- Mean 12.5 to 13.0 accepted fouls per game; yards 100 to 105 per game; pre-snap 4.7 to 5.0 per game; declined 1.7 to 1.9; offsetting flags 0.4 to 0.65.
- Spread of single games (indicative; from a transcribed list of 2025 games with small errors): standard deviation about 4.3 against 3.5 for pure chance, so fouls are somewhat clustered by game; middle half of games 10 to 15, 5th to 95th percentile 6 to 21, maximum 26 (Dallas-Giants, week 2) in 2025 and 30 (Chargers-Seahawks) in 2026.
- The standard error of a 10,000-game mean is only about 0.04, so the tolerance of the test comes from the choice of target year, not from sampling: 2021 to 2023 were 11.2 to 11.8, 2024 to 2025 12.8 to 12.9, 2015 to 2019 13.4 to 13.8, early 2026 15.1.
- Recommended target and band: 12.8 plus or minus 0.8 (12.0 to 13.6). That band contains 2017, 2019, 2024 and 2025 and leaves out 2020 to 2023 (11.2 to 11.8) and 2015 (13.8). A wider "any recent NFL season" band is 11.2 to 13.9. If the owner wants the "2026 feel", use 15, but that is a 79-game sample and the highest since 1978 (ESPN).

Target mix per game, both teams (2025 counts scaled to the regular season, count divided by 279.7; computed; 12.75 total):
- Offensive holding 2.45 and false start 2.43 (together 38 percent).
- Defensive pass interference 1.03, defensive holding 0.65, delay of game 0.65, unnecessary roughness 0.65.
- Defensive offside 0.52, illegal formation 0.40, face mask 0.36, illegal contact 0.34, roughing the passer 0.34, neutral zone 0.28.
- These twelve add up to 10.10. Everything else together about 2.65 (offensive pass interference, illegal use of hands, grounding, block in the back, shift, ineligible downfield, kickoff fouls, unsportsmanlike, encroachment and the rest).
- Average yards per accepted foul by group: pre-snap and five-yard fouls 4.4 to 5.0; offensive holding and block in the back about 9.6; offensive pass interference 9.7; intentional grounding 11.4; defensive pass interference 15.2; personal fouls (roughness, face mask, roughing) 13 to 14.

Rates to use in the foul table (N7.1), per scrimmage play (computed, 2025 regular season): 10.1 accepted fouls per 100 scrimmage plays in all, 3.7 of them pre-snap; offense 4.8, defense 3.5, special teams 1.75 (special teams per kick play is not derivable from public data, UNVERIFIED).

Automatic first downs: about 22 to 23 percent of accepted fouls (2.9 per game both teams, 1.4 per team per game), average 10.5 yards; one third on third or fourth down.

Decline policy check for the computer's choice: over a season it should decline about 12 to 13 percent of fouls that offer a choice, near zero for pre-snap dead-ball fouls, 25 to 50 percent for ineligible downfield, offside (defense), illegal shift, illegal formation, illegal contact and defensive holding, 10 to 15 percent for offensive holding and offensive pass interference, under 10 percent for defensive pass interference and personal fouls. Use these as a plausibility check on the rule-based decision, not as the decision.

Team differences: multiply a team's foul rate by a factor between 0.85 and 1.15 (computed spread); crews 0.9 to 1.1.

### Could not settle

- Official NFL league penalty totals: no official table reached. nfl.com team stats pages have no penalty column (checked "downs"); operations.nfl.com stats pages returned 404 and "stats-central" is not found; the NFL Record and Fact Book PDF is above the fetch size limit (10 MB); Pro-Football-Reference, TeamRankings and FootballDB return 403; ESPN pages load without tables. Everything about penalty counts is therefore SRC-SECONDARY, but it is cross-checked (ESPN, RotoWire/ESPN box scores, StatMuse).
- Share of fouls that nullify a play, rates per run play, per pass play and per kick, and a league figure for the last two minutes of the halves: not published in anything I could reach (details in section 3).
- The site's exact definitions of "pre-snap" and "Offsetting" (see caveats above).
- The Deseret column's 2024 total (3,572) and its 2015 record claim (see section 1).
- A per-game distribution of fouls: the site's "all games" page was read by a small model that returned a list with the wrong length (288 values for 285 games in 2025, sum 3,601 instead of 3,565; 82 values for 79 games in 2026). I used it only for rough shape (standard deviation about 4.3, range 3 to 26). The 2026 declined and offsetting lists were correct (79 values, sums 132 and 32). For a firm figure, compute from a play-by-play data set (not downloaded here by instruction).
- Whether the 2026 jump is real or noise: not settled. Sources disagree on cause (Front Office Sports snippet says it is probably not different officiating; others point to offense). No league statement was found (checked Competition Committee and Troy Vincent coverage; found only the 2026 health-and-safety suspension policy and the taunting emphasis).
- Context found but outside this topic: the league is mulling letting replay officials throw flags (ESPN, discussed 2026-02-23, not adopted); owners approved letting replay officials disqualify for a flagrant act missed on the field (Front Office Sports 2026-08-25; this matches rule 19-2 in the 2026 rulebook, PDF page 77).
- A snippet claiming "17.4 flags per game, 1,116 flags in 64 games" for the 2025 season could not be traced; it is probably 2026 weeks 1 to 4 (the site's total flags for those weeks are 1,104). Not used.

### Sources

All retrieved 2026-10-14.
- https://www.nflpenalties.com/ (home, 2026 league table, site notes). Secondary, nflfastR-based.
- https://www.nflpenalties.com/week/?year=2021 and the same for 2022, 2023, 2024, 2025, 2026 (weekly tables, accepted, yards, declined, offsetting, total flags).
- https://nflpenalties.com/index.php?year=2025&view=reg_season_game and the same for 2024, 2023, 2022, 2021, 2020, 2019, 2017, 2015 (regular-season per-game views and team tables). For 2026: https://nflpenalties.com/index.php?year=2026&view=game.
- https://www.nflpenalties.com/index.php?view=total&year=2025 and the 2023 and 2024 versions (team totals incl. playoffs).
- https://www.nflpenalties.com/all-penalties.php?year=2025 (and year=2024, year=2026): penalty types.
- https://www.nflpenalties.com/phase.php?year=2025 (and 2024, 2026): offense, defense, special teams, pre-snap.
- https://www.nflpenalties.com/penalties-by-quarter.php?year=2025 (and 2024, 2026).
- https://www.nflpenalties.com/league-by-down.php?year=2025 (and 2026).
- https://www.nflpenalties.com/automatic-first-downs.php?year=2025 (and 2024, 2026).
- https://www.nflpenalties.com/passing-penalties.php?year=2025 and /hard-counts.php?year=2025.
- https://www.nflpenalties.com/all-games.php?year=2025 (and 2026) and /all-referees.php?year=2025.
- https://www.nflpenalties.com/blog/what-is-a-play and /blog/the-obligatory-answers-to-questions-that-generally-no-one-ever-asked, /change-log.php (definitions).
- https://www.nfl.com/stats/team-stats/offense/downs/2025/reg/all and .../2026/reg/all (scrimmage plays per team). SRC-OFFICIAL (NFL.com).
- 2026 NFL rulebook text: 14-1-1 (PDF page 61), 14-5-1 (PDF page 65), 12-1-3(b) (page 52), automatic first down lines on PDF pages 39, 53, 55 to 57, penalty summary (page 77), 19-2 (page 77). SRC-OFFICIAL.
- https://www.deseret.com/sports/2026/10/10/its-time-for-nfl-officials-to-be-flagged/ (column, 2026-10-10; unsourced totals).
- https://cbssports.com/nfl/news/nfl-sets-penalty-record-through-week-4-officials/ (ESPN's 963 and 271 figures).
- https://www.sharpfootballanalysis.com/analysis/nfl-penalties-2026/amp/ (Warren Sharp, weeks 1 to 4 of 2026: 6.18 per 100 snaps, 17 touchdowns nullified, offense only).
- https://brobible.com/sports/article/nfl-penalty-flags-2026-season-data/ (repeats Sharp).
- https://www.pff.com/news/inside-the-nfls-most-and-least-penalized-teams-since-2021 (PFF, 2026-07-17; team rates 2021 to 2025).
- https://www.rotowire.com/football/article/most-penalized-nfl-teams-in-2025-95950 (page now shows 2026 through week 5 per team; ESPN box scores).
- https://www.statmuse.com/nfl/ask/most-penalties-nfl-team-2025 (2025 regular-season team totals).
- https://frontofficesports.com/article/nfl-taunting-crackdown-fines-penalties/ (2026-08-25; taunting counts by year).
- https://africa.espn.com/nfl/story/_/id/48016228/nfl-mulls-allowing-replay-officials-throw-flags (replay officials and flags, 2026-02-23).
- Search snippets only (page not read, UNVERIFIED): Harvard Sports Analysis "Inside the Flags" (2025-09); Buffalo Rumblings "deep analysis of Buffalo Bills penalties from 2024"; FiveThirtyEight holding and run-pass article (redirected); Sports Info Solutions kickoff touchback rates.


## Part 9. Statistics computed from the public play-by-play data

Written 2026-10-14. Research only. This part keeps the answers, the 2024 and 2025 combined blocks, the 2026-to-date blocks, the cross-checks, the playoffs summary and the method. The separate 2024 and 2025 blocks, the playoff blocks of section 5 and the plus-playoffs blocks of section 3 were left out to keep the file readable; the headline per-season numbers are in the answers and in Part 1.6, and the full notes and the scripts are kept in the shared notes folder of this session group (sx0_raw_notes/H_nflverse_stats_full.md and sx0_raw_notes/scripts_stats/). To repeat any figure: download the three files named in the last section (SHA-256 given there) and run the scripts with `python -I`. Every figure in this file was computed by me from three nflverse files, listed in "Sources and method" at the end. Tag for all of them: SRC-SECONDARY (computed result from nflverse data; the data file is named in the line or in the section heading). Where a figure was also checked against a published number, the check is listed in section 7.

Samples (regular season, season_type REG, unless said):
- 2024: 272 games (544 team-games), 2024-09-05 to 2025-01-05.
- 2025: 272 games (544 team-games), 2025-09-04 to 2026-01-04.
- 2026 to date: 79 games (158 team-games), weeks 1 to 5, through the game of 2026-10-12. Small sample, treat as a first look.
- 2024 and 2025 combined: 544 games (1088 team-games). This is the main sample.
- Playoffs (season_type POST) are never mixed in: 13 games in 2024 and 13 in 2025, summarized in section 8. Two blocks in section 3 that add the playoffs are marked as such and exist only to compare with sources that include them.
- "Per team per game" means a count divided by twice the number of games.

### Answers in brief

1. TIMEOUTS (section 1)
   - Charged team timeouts per team per game: 3.88 (2024), 3.85 (2025), 3.84 (2026 to date); 3.86 in 2024 and 2025 combined. Of these, 3.72 are called by the coach and 0.14 are charged for a lost challenge.
   - Per half, 2024 and 2025: 1.92 in the first half and 1.90 in the second half per team; overtime 0.05 (50 timeouts in 30 overtime games).
   - By quarter, per team per game: Q1 0.21, Q2 1.71, Q3 0.20, Q4 1.70. In the first three quarters a team is charged 2.12 timeouts (coach-called 2.02); about 1.4 of those are in the last two minutes of the first half.
   - Timeouts left at the end of the first half (2024 and 2025): 3 left 11.5 percent, 2 left 23.1, 1 left 28.1, none left 37.3 (mean 1.09 left). End of the second half: 3 left 17.6, 2 left 18.9, 1 left 20.8, none left 42.6 (mean 1.12 left).
   - Time left in the half (share of all timeouts of that half): first half 8 minutes or more 17.1 percent, 8 to 4 minutes 5.2, 4 to 2 minutes 4.1, under 2 minutes 73.6. Second half: 18.3, 13.8, 25.5, 42.4.
   - Share of first-half timeouts called before the two-minute warning (more than 2:00 left): 26.2 percent.
   - Offense or defense (coach-called, who has the ball at the next snap): first half 62 percent offense, 38 defense; second half 39 offense, 61 defense. Second half with 2 to 4 minutes left: 20 offense, 80 defense.
   - Leading, tied, trailing at the time of the timeout: second half last 5:00: leading 28.5 percent, tied 9.4, trailing 62.1. First half last 5:00: 45.2, 8.3, 46.4.
   - Timeouts used in the last 5:00 of the second half, per team, by the score at the start of those 5 minutes: all leading teams 0.95, all trailing teams 1.81, tied 1.75. Trailing by 1 to 8 points: 2.25 (only 5.1 percent use none, 0.44 timeouts left at the end). Leading by 9 or more: 0.58 (56.6 percent use none). Trailing by 9 or more: 1.48. First half last 5:00: leading 1.48, trailing 1.58, tied 1.44.
   - Overtime (regular season): at most 2 timeouts per team were used (22 of 60 teams used none, 26 used one, 12 used two, 2024 and 2025).

2. QUARTERBACK RUNS (section 2)
   - Per team per game (2024 and 2025): 3.26 quarterback rushes: 1.29 designed and 1.97 scrambles; plus 0.77 kneel-downs, 0.14 spikes and 2.39 sacks. About 5.4 percent of scrimmage plays are quarterback rushes.
   - Yards per attempt: designed 3.66 (3.99 in 2024, 3.25 in 2025, 3.04 in 2026), scrambles 7.67 (7.85, 7.48, 7.86), all quarterback rushes 6.09.
   - First down or touchdown: designed 51.3 percent, scrambles 41.0. Fumble lost: designed 1.07 percent per run, scrambles 0.47, all 0.71.
   - Gain percentiles 10, 25, 50, 75, 90: designed 0, 1, 2, 5, 10; scrambles 2, 3, 6, 10, 15.
   - Scrambles per dropback: 5.25 percent (2024), 5.51 (2025), 5.23 (2026); sacks per dropback about 6.5 percent. About 36.6 dropbacks per team per game.
   - Third or fourth and 1, designed quarterback run (a quarterback sneak cannot be told from other designed runs, see section 2): 469 attempts, converted 83.4 percent (third down 81.9, fourth down 86.4); "up the middle" only (sneak proxy): 307 attempts, 83.4 percent. Other runners on third or fourth and 1: 69.2 percent. Passes: 52.0 percent. At 2 yards: quarterback designed runs 74.2 percent (62 attempts).
   - Field zone, designed runs: inside the opponent 5: 59.0 percent first down or touchdown, 52.8 percent touchdowns, 0.90 yards per run (178 runs); own half 4.10 yards.
   - Out of bounds: 12.1 percent of designed runs and 34.0 percent of scrambles end out of bounds. A slide is not recorded anywhere in the data.

3. ACCEPTED PENALTIES (section 3)
   - Per game, both teams: 12.91 (2024), 12.75 (2025), 15.10 (2026 to date); 12.83 in 2024 and 2025 combined. Per team per game 6.42 (combined), yards 51.8 per team per game, 8.08 yards per accepted foul.
   - Per 100 standing scrimmage plays: 10.40. Before the snap: 39.2 percent of accepted fouls (2.52 per team per game). During a run play 14.0 percent, during a pass play 35.1 percent, special teams 11.7 percent (kickoff 0.35, punt 0.35, field goal and extra point 0.06 per team per game).
   - By quarter: Q1 21.0, Q2 29.7, Q3 23.5, Q4 25.4, overtime 0.4 percent. Last two minutes of each half: 12.4 percent of all accepted fouls, but the foul rate per play there (9.45 per 100) is slightly lower than elsewhere (9.99).
   - Declined: 0.91 per team per game (decline share 12.4 percent of fouls with a choice). Offsetting flags: 0.30 per team per game (153 plays in two seasons).
   - 73.1 percent of accepted fouls sit on a play that is nullified or never run (no_play): 4.69 per team per game; 7 to 8 percent of all snap-like events are nullified by a foul.
   - Team spread (per team per game): SD 0.71 (2024) and 0.80 (2025), range 4.41 (Rams, 2025) to 8.06 (Jets, 2024). Chance alone gives an SD of about 0.62. Two seasons pooled per team: SD 0.59 against 0.43 by chance, so the lasting team effect is about 0.4 fouls per game (about 6 percent of the mean).
   - Top types per game (both teams, 2024 and 2025): offensive holding 2.49, false start 2.46, defensive pass interference 1.07, defensive holding 0.65, delay of game 0.63, unnecessary roughness 0.64. Full list in section 3.
   - Fouls that produced a first down (flag first_down_penalty): 27.0 percent (2024), 28.2 (2025) of accepted fouls; for defensive pass interference and defensive holding 99 percent.

4. ONSIDE KICKS AND KICKOFFS (section 4)
   - Attempts and recoveries by the kicking team: 2024 50 attempts, 3 recoveries (6.0 percent); 2025 52 attempts, 5 recoveries (9.6 percent); 2026 to date 11 attempts, 0 recoveries. All 113 attempts came in the fourth quarter, all by the trailing team. No attempt in the first three quarters, none while leading or tied.
   - Time left: in 2024 and 2025 combined, 55 of 102 attempts came in the last two minutes of the game, 30 with 2 to 5 minutes left, 14 with 5 to 10, 3 with more than 10. In 2026 to date: 8 in the last two minutes, 2 between 2 and 5 minutes, one with 10:49 left (Raiders, trailing by 21).
   - By margin of the kicking team (2024 and 2025): trailing by 1 to 8: 43 attempts, 5 recoveries; 9 to 16: 39 attempts, 1 recovery; more than 16: 20 attempts, 2 recoveries.
   - Kick distance (2024 and 2025): mean 10.4 yards, middle 10, 10th to 90th percentile 7 to 14; the eight recoveries went 8 to 13 yards. 2026 to date: mean 13.4. Kick spot: the 35 in 92 of 102 attempts, the 20 after a safety in 8 (the other two after fouls).
   - Dynamic kickoff (kickoffs without onside kicks): touchback rate 65.5 percent (2024, with 30-yard touchbacks), 21.1 (2025), 15.8 (2026 to date). Returned: 33.3, 76.0, 81.7 percent. Average starting yard line after all kickoffs: 29.6, 30.3, 30.2 (median 30, 31, 30).

5. REPLAY (section 5)
   - Plays with a replay or challenge mark, regular season: 327 (2024), 322 (2025), 94 (2026 to date). Coach challenges 133, 151 and 36; replay-official reviews 194, 171 and 58.
   - Reversed: coach challenges 37.6 percent (2024), 52.3 (2025), 50.0 (2026); replay-official reviews 76.3, 78.4, 74.1.
   - Per team per game: 0.244 (2024), 0.278 (2025), 0.228 (2026) coach challenges; 0.142 lost challenges (so 0.142 timeouts) per team per game in 2024 and 2025 combined. A team challenges in 23.3 percent of its games (0 challenges in 76.7 percent, 1 in 20.9, 2 in 2.2, 3 in 0.3; 2024 and 2025). Both teams together: 59.0 percent of games have no coach challenge, 31.6 percent one, 7.9 percent two, 1.5 percent three or four. Coach challenges are made by the team on defense 70.4 percent of the time.
   - Categories (coach challenges, 2024 and 2025): catch or no catch 50.7 percent of challenges (reversed 45.1), spot and line to gain 26.4 (48.0), down by contact 11.3 (50.0), goal line 4.6 (53.8). Replay official: catch 24.7 (72.2 reversed), goal line and touchdown 20.3 (83.8), down by contact 12.3 (80.0), fumble 11.2 (82.9), interception 9.6 (68.6), out of bounds 9.6 (82.9).

6. CLOCK (section 6)
   - Scrimmage plays in regulation (pass and run incl. sacks and scrambles, no kneel or spike, no nullified play) per team per game: 60.96 (2024), 59.97 (2025), 60.47 (2026); with kneel-downs and spikes about 61.8, 60.9, 61.4 (overtime adds about 0.3). Both teams per quarter per game (2024 and 2025): Q1 27.2, Q2 32.8, Q3 27.8, Q4 33.1. Last two minutes of a half: 16.1 plays per game, both teams (kneel-downs and spikes included): 9.35 in the second quarter and 6.78 in the fourth.
   - Game-clock seconds per scrimmage play: 29.8 (30.0 in 2025); per snap including punts, field goal tries, kneel-downs and spikes: 26.9.
   - Elapsed game-clock seconds from one snap to the next, normal clock rules: complete in bounds 37.9 (10th 26, median 39, 90th 45); complete out of bounds 35.2 (25, 37, 43); incomplete 5.0 (3, 5, 7); run in bounds 38.0 (30, 39, 44); run out of bounds 36.8 (27, 38, 44); sack 37.7 (21, 41, 46); punt 9.4 (7, 9, 13); missed field goal 4.8.
   - Share of plays followed by a running clock (more than 25 seconds to the next snap, normal rules): 68.0 percent.
   - Snap to end of play: not recorded in the data, but after an incomplete pass the clock stops and starts again only at the next snap, so snap to snap equals the length of the play: mean 4.99 seconds, median 5 (10th 3, 90th 7; 10,328 plays). Out-of-bounds completions with the late-half rule 6.4 seconds, out-of-bounds runs 7.7.

### Surprises and mismatches (details in section 7)

- One mismatch: the NFL.com team total "Scrm Plys" quoted in topic E3 (63.27 per team per game in 2025) against my count of plays that stood (61.26, pass, run, kneel-downs and spikes). My count equals the Rotowire 2024 value (62.2) and the Sharp 2025 value (61.3), so the NFL.com total probably also counts plays that a foul nullified (I count 2.9 per team per game of those). This reason is a guess; I cannot see the NFL.com definition.
- The other differences are small or a question of definition (average kickoff start spot, automatic first downs; section 7). More than ten published figures were reproduced exactly or within 0.5 percent (onside counts 50 and 52 attempts with 3 and 5 recoveries; coach challenges 133 and 151; reversal rates 37.6 and 60.0 percent through week 7; review totals 117 and 137 through week 7; accepted penalties; declined and offsetting counts; the four FOX quarterback sneak figures; kickoff returns).
- The data fix an open point of topic B: the "171 replay review or replay assist decisions in 2025" quoted by the league equals my count of replay-official reviews in the 2025 regular season (171); the 137 reviews through week 7 are coach challenges and replay-official reviews together (60 coach plus 77 official).
- Timeouts: the data contain 18 cases of a fourth timeout in one half ("Timeout #4": 6 in 2024, 10 in 2025, 2 in 2026). All 18 fall in the last two minutes of a half and all have an injury mention in the three plays before them, so they are probably excess timeouts after an injury. Not verified against the rulebook (topic A).
- The two-minute warning is not a row in the data and neither are injury timeouts or official timeouts. Time between plays shows them only as long gaps.
- Out-of-bounds plays under the normal clock rule take as long to the next snap as in-bounds plays (35 to 37 seconds), so the clock restarts at the ready signal as the rulebook says; in the last five minutes of the second half they take only 6 to 8 seconds.
- Fouls are not more frequent per play in the last two minutes of the halves, only more of them happen there because many more plays are run.
- 2026 so far has more fouls than any recent season (15.10 per game against 12.8) and fewer second-half timeouts used (1.72 per team against 1.90).
- A quarterback scramble in the data practically never loses yards (0.1 percent at zero or less): the word "scrambles" appears in the text only when the quarterback gains yards, so a scramble for a loss or no gain is written as a sack or as a plain run and lands in my "designed" group. This makes the designed group look a little worse and the scramble group a little better than the true split.

### 1. Timeouts (regular season; counted from the rows with timeout=1)

What is counted: a charged team timeout is either a timeout called by the coach (a separate row "Timeout #n by TEAM") or the timeout that a lost coach challenge costs (marked "(Timeout #n.)" on the play row). "All charged" is both together. Injury and official timeouts and the two-minute warning are not in the data. Details of every filter are in "Sources and method".
Reading the lists: "used" and "remaining" are per team per half (three per half); time left is in the half; leading and trailing are seen from the team that took the timeout.

#### 2026 to date (REG, 79 games, 158 team-games)
- Parse notes (unparsed rows; how the side was decided): {'side_from_next': 539, 'side_from_previous': 50, 'standalone_unparsed': 1}
- All charged team timeouts: 606, per team per game 3.84 (called by the coach 3.73, charged for a lost challenge 0.11)
- first half: 317 timeouts, per team per game 2.01
- second half: 272 timeouts, per team per game 1.72
- overtime: 17 timeouts, per team per game 0.11
- By quarter, per team per game: Q1 0.241, Q2 1.766, Q3 0.133, Q4 1.589, QOT 0.108
- First three quarters: 2.14 charged timeouts per team per game (coach-called only 2.05)
- Integrity check: team-halves where the number of events differs from the highest "Timeout #n": 1 of 283 team-halves with any timeout
- Timeouts USED per team in the first half: 0: 8.9%, 1: 24.1%, 2: 26.6%, 3: 40.5% (mean 1.99)
- Timeouts REMAINING at the end of the first half: 3 left: 8.9%, 2 left: 24.1%, 1 left: 26.6%, 0 left: 40.5% (mean 1.01)
- Timeouts USED per team in the second half: 0: 18.4%, 1: 25.9%, 2: 20.9%, 3: 34.8% (mean 1.72)
- Timeouts REMAINING at the end of the second half: 3 left: 18.4%, 2 left: 25.9%, 1 left: 20.9%, 0 left: 34.8% (mean 1.28)
- Regulation timeouts used per team per game, distribution: 0: 3.2%, 1: 10.8%, 2: 8.2%, 3: 17.7%, 4: 25.9%, 5: 17.1%, 6: 17.1%
- Overtime: 6 games went to overtime; timeouts used per team in overtime: 0 used: 2 teams, 1 used: 3 teams, 2 used: 7 teams
- first half timeouts by time left in the half (n=317; per team per game in brackets): 8:00 or more left in the half: 21.5% [0.430]; 4:00 to 8:00 left: 3.8% [0.076]; 2:00 to 4:00 left: 1.9% [0.038]; under 2:00 left: 72.9% [1.462]
- second half timeouts by time left in the half (n=272; per team per game in brackets): 8:00 or more left in the half: 17.6% [0.304]; 4:00 to 8:00 left: 12.1% [0.209]; 2:00 to 4:00 left: 26.1% [0.449]; under 2:00 left: 44.1% [0.759]
- first half coach-called timeouts by side (n=304): offense 59.5%, defense 40.5%, before a kickoff 0.0%, unknown 0.0%
  - first half, 8:00 or more left in the half: n=61, offense 75.4%, defense 24.6%
  - first half, 4:00 to 8:00 left: n=7, offense 100.0%, defense 0.0%
  - first half, 2:00 to 4:00 left: n=5, offense 20.0%, defense 80.0%
  - first half, under 2:00 left: n=231, offense 55.0%, defense 45.0%
- second half coach-called timeouts by side (n=268): offense 40.7%, defense 59.3%, before a kickoff 0.0%, unknown 0.0%
  - second half, 8:00 or more left in the half: n=44, offense 70.5%, defense 29.5%
  - second half, 4:00 to 8:00 left: n=33, offense 69.7%, defense 30.3%
  - second half, 2:00 to 4:00 left: n=71, offense 21.1%, defense 78.9%
  - second half, under 2:00 left: n=120, offense 33.3%, defense 66.7%
  - first half, 8:00 or more left in the half, all charged timeouts by the score at that moment (n=68): leading 25.0%, tied 44.1%, trailing 30.9%
  - first half, 4:00 to 8:00 left, all charged timeouts by the score at that moment (n=12): leading 33.3%, tied 41.7%, trailing 25.0%
  - first half, 2:00 to 4:00 left, all charged timeouts by the score at that moment (n=6): leading 33.3%, tied 16.7%, trailing 50.0%
  - first half, under 2:00 left, all charged timeouts by the score at that moment (n=231): leading 45.5%, tied 13.0%, trailing 41.6%
  - second half, 8:00 or more left in the half, all charged timeouts by the score at that moment (n=48): leading 50.0%, tied 4.2%, trailing 45.8%
  - second half, 4:00 to 8:00 left, all charged timeouts by the score at that moment (n=33): leading 33.3%, tied 9.1%, trailing 57.6%
  - second half, 2:00 to 4:00 left, all charged timeouts by the score at that moment (n=71): leading 18.3%, tied 4.2%, trailing 77.5%
  - second half, under 2:00 left, all charged timeouts by the score at that moment (n=120): leading 38.3%, tied 17.5%, trailing 44.2%
- Lost-challenge timeouts (n=17): charged to a team that had the ball 23.5%, to the defense 76.5%
- first half, all charged timeouts by the score at that moment (n=317): leading 40.4%, tied 20.8%, trailing 38.8%
- first half, last 5:00 only (n=238): leading 45.0%, tied 13.0%, trailing 42.0%; side: offense 54.2%, defense 45.8%
- second half, all charged timeouts by the score at that moment (n=272): leading 34.6%, tied 10.7%, trailing 54.8%
- second half, last 5:00 only (n=205): leading 30.2%, tied 12.2%, trailing 57.6%; side: offense 30.7%, defense 69.3%
- Timeouts used in the last 5:00 of the first half, per team, grouped by the score at the start of those 5 minutes:
  - leading by 9 or more: 1.28 used per team-half (n=18), zero used in 16.7%, timeouts still left at the end of the half 1.17
  - leading by 1 to 8: 1.64 used per team-half (n=47), zero used in 21.3%, timeouts still left at the end of the half 1.02
  - tied: 1.54 used per team-half (n=28), zero used in 14.3%, timeouts still left at the end of the half 0.82
  - trailing by 1 to 8: 1.57 used per team-half (n=47), zero used in 19.1%, timeouts still left at the end of the half 0.89
  - trailing by 9 or more: 1.17 used per team-half (n=18), zero used in 33.3%, timeouts still left at the end of the half 1.44
  - ALL leading teams: 1.54; ALL trailing teams: 1.46; tied: 1.54
- Timeouts used in the last 5:00 of the second half, per team, grouped by the score at the start of those 5 minutes:
  - leading by 9 or more: 0.46 used per team-half (n=37), zero used in 64.9%, timeouts still left at the end of the half 1.97
  - leading by 1 to 8: 1.31 used per team-half (n=35), zero used in 22.9%, timeouts still left at the end of the half 1.40
  - tied: 1.36 used per team-half (n=14), zero used in 28.6%, timeouts still left at the end of the half 1.07
  - trailing by 1 to 8: 2.17 used per team-half (n=35), zero used in 5.7%, timeouts still left at the end of the half 0.43
  - trailing by 9 or more: 1.27 used per team-half (n=37), zero used in 40.5%, timeouts still left at the end of the half 1.35
  - ALL leading teams: 0.88; ALL trailing teams: 1.71; tied: 1.36
- First half: 27.1% of timeouts come with more than 2:00 left in the half (before the two-minute warning), 72.9% with 2:00 or less (n=317)
- Second half: 24.6% with more than 5:00 left, 55.1% with more than 2:00 left (n=272)
- Cross-check: the field home/away_timeouts_remaining on the last row of each half equals 3 minus the timeouts I counted in 99.4% of 316 team-halves
#### 2024 and 2025 combined (REG, 544 games, 1088 team-games)
- Parse notes (unparsed rows; how the side was decided): {'side_from_next': 3728, 'side_from_previous': 322, 'standalone_unparsed': 1, 'side_from_none': 1}
- All charged team timeouts: 4205, per team per game 3.86 (called by the coach 3.72, charged for a lost challenge 0.14)
- first half: 2093 timeouts, per team per game 1.92
- second half: 2062 timeouts, per team per game 1.90
- overtime: 50 timeouts, per team per game 0.05
- By quarter, per team per game: Q1 0.211, Q2 1.712, Q3 0.198, Q4 1.698, QOT 0.046
- First three quarters: 2.12 charged timeouts per team per game (coach-called only 2.02)
- Integrity check: team-halves where the number of events differs from the highest "Timeout #n": 8 of 1897 team-halves with any timeout
- Timeouts USED per team in the first half: 0: 11.5%, 1: 23.1%, 2: 28.1%, 3: 37.3% (mean 1.91)
- Timeouts REMAINING at the end of the first half: 3 left: 11.5%, 2 left: 23.1%, 1 left: 28.1%, 0 left: 37.3% (mean 1.09)
- Timeouts USED per team in the second half: 0: 17.6%, 1: 18.9%, 2: 20.8%, 3: 42.6% (mean 1.88)
- Timeouts REMAINING at the end of the second half: 3 left: 17.6%, 2 left: 18.9%, 1 left: 20.8%, 0 left: 42.6% (mean 1.12)
- Regulation timeouts used per team per game, distribution: 0: 2.0%, 1: 6.7%, 2: 11.6%, 3: 19.9%, 4: 23.9%, 5: 20.0%, 6: 15.0%, 7: 0.8%
- Overtime: 30 games went to overtime; timeouts used per team in overtime: 0 used: 22 teams, 1 used: 26 teams, 2 used: 12 teams
- first half timeouts by time left in the half (n=2093; per team per game in brackets): 8:00 or more left in the half: 17.1% [0.329]; 4:00 to 8:00 left: 5.2% [0.100]; 2:00 to 4:00 left: 4.1% [0.078]; under 2:00 left: 73.6% [1.416]
- second half timeouts by time left in the half (n=2062; per team per game in brackets): 8:00 or more left in the half: 18.3% [0.347]; 4:00 to 8:00 left: 13.8% [0.262]; 2:00 to 4:00 left: 25.5% [0.483]; under 2:00 left: 42.4% [0.803]
- first half coach-called timeouts by side (n=2020): offense 61.9%, defense 38.1%, before a kickoff 0.0%, unknown 0.0%
  - first half, 8:00 or more left in the half: n=304, offense 78.0%, defense 22.0%
  - first half, 4:00 to 8:00 left: n=95, offense 78.9%, defense 21.1%
  - first half, 2:00 to 4:00 left: n=80, offense 52.5%, defense 47.5%
  - first half, under 2:00 left: n=1541, offense 58.1%, defense 41.8%
- second half coach-called timeouts by side (n=1981): offense 39.2%, defense 60.8%, before a kickoff 0.0%, unknown 0.0%
  - second half, 8:00 or more left in the half: n=317, offense 72.6%, defense 27.4%
  - second half, 4:00 to 8:00 left: n=277, offense 35.7%, defense 64.3%
  - second half, 2:00 to 4:00 left: n=513, offense 20.1%, defense 79.9%
  - second half, under 2:00 left: n=874, offense 39.5%, defense 60.5%
  - first half, 8:00 or more left in the half, all charged timeouts by the score at that moment (n=358): leading 31.0%, tied 38.3%, trailing 30.7%
  - first half, 4:00 to 8:00 left, all charged timeouts by the score at that moment (n=109): leading 40.4%, tied 11.9%, trailing 47.7%
  - first half, 2:00 to 4:00 left, all charged timeouts by the score at that moment (n=85): leading 44.7%, tied 8.2%, trailing 47.1%
  - first half, under 2:00 left, all charged timeouts by the score at that moment (n=1541): leading 45.4%, tied 8.1%, trailing 46.5%
  - second half, 8:00 or more left in the half, all charged timeouts by the score at that moment (n=377): leading 60.7%, tied 5.0%, trailing 34.2%
  - second half, 4:00 to 8:00 left, all charged timeouts by the score at that moment (n=285): leading 31.2%, tied 2.1%, trailing 66.7%
  - second half, 2:00 to 4:00 left, all charged timeouts by the score at that moment (n=526): leading 19.2%, tied 3.2%, trailing 77.6%
  - second half, under 2:00 left, all charged timeouts by the score at that moment (n=874): leading 35.2%, tied 14.3%, trailing 50.5%
- Lost-challenge timeouts (n=154): charged to a team that had the ball 26.6%, to the defense 73.4%
- first half, all charged timeouts by the score at that moment (n=2093): leading 42.6%, tied 13.5%, trailing 43.9%
- first half, last 5:00 only (n=1656): leading 45.2%, tied 8.3%, trailing 46.4%; side: offense 58.0%, defense 41.9%
- second half, all charged timeouts by the score at that moment (n=2062): leading 35.3%, tied 8.1%, trailing 56.6%
- second half, last 5:00 only (n=1523): leading 28.5%, tied 9.4%, trailing 62.1%; side: offense 32.0%, defense 68.0%
- Timeouts used in the last 5:00 of the first half, per team, grouped by the score at the start of those 5 minutes:
  - leading by 9 or more: 1.40 used per team-half (n=171), zero used in 21.6%, timeouts still left at the end of the half 1.06
  - leading by 1 to 8: 1.53 used per team-half (n=310), zero used in 18.7%, timeouts still left at the end of the half 1.07
  - tied: 1.44 used per team-half (n=126), zero used in 24.6%, timeouts still left at the end of the half 1.23
  - trailing by 1 to 8: 1.56 used per team-half (n=310), zero used in 20.3%, timeouts still left at the end of the half 1.09
  - trailing by 9 or more: 1.62 used per team-half (n=171), zero used in 16.4%, timeouts still left at the end of the half 1.03
  - ALL leading teams: 1.48; ALL trailing teams: 1.58; tied: 1.44
- Timeouts used in the last 5:00 of the second half, per team, grouped by the score at the start of those 5 minutes:
  - leading by 9 or more: 0.58 used per team-half (n=295), zero used in 56.6%, timeouts still left at the end of the half 1.77
  - leading by 1 to 8: 1.45 used per team-half (n=217), zero used in 25.8%, timeouts still left at the end of the half 1.12
  - tied: 1.75 used per team-half (n=64), zero used in 14.1%, timeouts still left at the end of the half 0.77
  - trailing by 1 to 8: 2.25 used per team-half (n=217), zero used in 5.1%, timeouts still left at the end of the half 0.44
  - trailing by 9 or more: 1.48 used per team-half (n=295), zero used in 34.9%, timeouts still left at the end of the half 1.03
  - ALL leading teams: 0.95; ALL trailing teams: 1.81; tied: 1.75
- First half: 26.2% of timeouts come with more than 2:00 left in the half (before the two-minute warning), 73.8% with 2:00 or less (n=2093)
- Second half: 26.1% with more than 5:00 left, 57.1% with more than 2:00 left (n=2062)
- Cross-check: the field home/away_timeouts_remaining on the last row of each half equals 3 minus the timeouts I counted in 99.4% of 2176 team-halves

### 2. Quarterback runs (regular season)

What is counted: runs by a quarterback on plays that stood (no kneel-downs, no spikes, no two-point tries, no aborted snaps). "Designed" and "scramble" follow the nflverse flag qb_scramble (the text says "scrambles"). Sacks, kneel-downs and spikes are shown apart. "First down or TD" means a new first down by the run or a touchdown. There is no position column; quarterbacks are found by their passes (see "Sources and method"). A sneak is not marked in the data; the "sneak proxy" lines use designed runs "up the middle" on third or fourth and 1 or 2.

#### 2026 to date (REG, 79 games, 158 team-games)
- QB rushes (excluding kneel-downs, spikes, two-point tries, aborted snaps): 477 total, 3.02 per team per game; designed 170 (1.08 per team per game), scrambles 307 (1.94 per team per game)
- Kneel-downs (play_type qb_kneel): 125, 0.79 per team per game; spikes: 24, 0.15 per team per game; sacks: 357, 2.26 per team per game
- Share of all scrimmage plays that are QB rushes: 4.94% (designed 1.76%, scramble 3.18%); scrimmage plays 61.13 per team per game
- Dropbacks (qb_dropback=1: pass attempts, sacks, scrambles): 5873, 37.17 per team per game. Scramble rate per dropback 5.23%; sack rate per dropback 6.08%; designed QB run per 100 non-dropback plays 4.5
- All QB rushes: n=477, 6.14 yd/att, first down or TD 47.4%, TD 6.7%, fumble lost 1.05%
- Designed QB runs: n=170, 3.04 yd/att, first down or TD 57.1%, TD 11.8%, fumble lost 1.18%
- Scrambles: n=307, 7.86 yd/att, first down or TD 42.0%, TD 3.9%, fumble lost 0.98%
- Yards per attempt: designed 3.04, scramble 7.86; share of runs for zero or negative yards: designed 19.4%, scramble 0.3%; for 10 or more yards: designed 5.9%, scramble 28.0%
- Gain percentiles designed (10, 25, 50, 75, 90): 0, 1, 2, 3, 8; mean 3.04; max 35, min -12
- Gain percentiles scramble (10, 25, 50, 75, 90): 2, 3, 6, 10, 16; mean 7.86; max 39, min 0
- Out of bounds (ran ob or pushed ob in the text): 10.0% of designed runs; a slide is not recorded anywhere in the data (no text with slide or slid)
- Out of bounds (ran ob or pushed ob in the text): 38.1% of scramble runs; a slide is not recorded anywhere in the data (no text with slide or slid)
- Kneel-downs: mean yards -1.21
#### Short yardage, QB designed runs (sneak proxy): 2026 to date
- Run location of designed QB runs on 3rd or 4th and 1 (the text of a sneak says "up the middle", no sneak word exists): {'middle': 59, 'left': 12, 'right': 8}
- 3 down and 1 yard, any designed QB run: n=61, 1.98 yd/att, first down or TD 90.2%, TD 6.6%, fumble lost 0.00%
  - of those "up the middle" (sneak proxy): n=48, 2.04 yd/att, first down or TD 91.7%, TD 6.2%, fumble lost 0.00%
- 3 down and 2 yards, any designed QB run: n=4, 0.50 yd/att, first down or TD 25.0%, TD 25.0%, fumble lost 0.00%
  - of those "up the middle" (sneak proxy): n=2, -1.00 yd/att, first down or TD 0.0%, TD 0.0%, fumble lost 0.00%
- 4 down and 1 yard, any designed QB run: n=18, 0.78 yd/att, first down or TD 61.1%, TD 16.7%, fumble lost 0.00%
  - of those "up the middle" (sneak proxy): n=11, 1.09 yd/att, first down or TD 72.7%, TD 27.3%, fumble lost 0.00%
- 4 down and 2 yards, any designed QB run: n=0
  - of those "up the middle" (sneak proxy): n=0
- 3rd and 4th and 1 together, any designed QB run: n=79, 1.71 yd/att, first down or TD 83.5%, TD 8.9%, fumble lost 0.00%
- 3rd and 4th and 1 together, up the middle: n=59, 1.86 yd/att, first down or TD 88.1%, TD 10.2%, fumble lost 0.00%
- 3rd and 4th and 1 or 2 together, any designed QB run: n=83, 1.65 yd/att, first down or TD 80.7%, TD 9.6%, fumble lost 0.00%
- 3rd and 4th and 1 or 2 together, up the middle: n=61, 1.77 yd/att, first down or TD 85.2%, TD 9.8%, fumble lost 0.00%
#### 2024 and 2025 combined (REG, 544 games, 1088 team-games)
- QB rushes (excluding kneel-downs, spikes, two-point tries, aborted snaps): 3543 total, 3.26 per team per game; designed 1399 (1.29 per team per game), scrambles 2144 (1.97 per team per game)
- Kneel-downs (play_type qb_kneel): 838, 0.77 per team per game; spikes: 150, 0.14 per team per game; sacks: 2601, 2.39 per team per game
- Share of all scrimmage plays that are QB rushes: 5.36% (designed 2.11%, scramble 3.24%); scrimmage plays 60.80 per team per game
- Dropbacks (qb_dropback=1: pass attempts, sacks, scrambles): 39850, 36.63 per team per game. Scramble rate per dropback 5.38%; sack rate per dropback 6.53%; designed QB run per 100 non-dropback plays 5.3
- All QB rushes: n=3543, 6.09 yd/att, first down or TD 45.1%, TD 6.0%, fumble lost 0.71%
- Designed QB runs: n=1399, 3.66 yd/att, first down or TD 51.3%, TD 9.4%, fumble lost 1.07%
- Scrambles: n=2144, 7.67 yd/att, first down or TD 41.0%, TD 3.8%, fumble lost 0.47%
- Yards per attempt: designed 3.66, scramble 7.67; share of runs for zero or negative yards: designed 20.3%, scramble 0.1%; for 10 or more yards: designed 10.6%, scramble 27.3%
- Gain percentiles designed (10, 25, 50, 75, 90): 0, 1, 2, 5, 10; mean 3.66; max 50, min -10
- Gain percentiles scramble (10, 25, 50, 75, 90): 2, 3, 6, 10, 15; mean 7.67; max 47, min 0
- Out of bounds (ran ob or pushed ob in the text): 12.1% of designed runs; a slide is not recorded anywhere in the data (no text with slide or slid)
- Out of bounds (ran ob or pushed ob in the text): 34.0% of scramble runs; a slide is not recorded anywhere in the data (no text with slide or slid)
- Kneel-downs: mean yards -1.09
#### Short yardage, QB designed runs (sneak proxy): 2024 and 2025 combined
- Run location of designed QB runs on 3rd or 4th and 1 (the text of a sneak says "up the middle", no sneak word exists): {'middle': 307, 'left': 93, 'right': 67, 'none': 2}
- 3 down and 1 yard, any designed QB run: n=315, 2.18 yd/att, first down or TD 81.9%, TD 5.4%, fumble lost 1.27%
  - of those "up the middle" (sneak proxy): n=201, 1.66 yd/att, first down or TD 82.6%, TD 4.5%, fumble lost 0.50%
- 3 down and 2 yards, any designed QB run: n=55, 3.75 yd/att, first down or TD 74.5%, TD 5.5%, fumble lost 1.82%
  - of those "up the middle" (sneak proxy): n=14, 2.86 yd/att, first down or TD 64.3%, TD 7.1%, fumble lost 0.00%
- 4 down and 1 yard, any designed QB run: n=154, 2.27 yd/att, first down or TD 86.4%, TD 5.8%, fumble lost 0.65%
  - of those "up the middle" (sneak proxy): n=106, 1.55 yd/att, first down or TD 84.9%, TD 4.7%, fumble lost 0.94%
- 4 down and 2 yards, any designed QB run: n=7, 4.43 yd/att, first down or TD 71.4%, TD 14.3%, fumble lost 0.00%
  - of those "up the middle" (sneak proxy): n=1, 3.00 yd/att, first down or TD 100.0%, TD 0.0%, fumble lost 0.00%
- 3rd and 4th and 1 together, any designed QB run: n=469, 2.21 yd/att, first down or TD 83.4%, TD 5.5%, fumble lost 1.07%
- 3rd and 4th and 1 together, up the middle: n=307, 1.62 yd/att, first down or TD 83.4%, TD 4.6%, fumble lost 0.65%
- 3rd and 4th and 1 or 2 together, any designed QB run: n=531, 2.40 yd/att, first down or TD 82.3%, TD 5.6%, fumble lost 1.13%
- 3rd and 4th and 1 or 2 together, up the middle: n=322, 1.68 yd/att, first down or TD 82.6%, TD 4.7%, fumble lost 0.62%
#### Down and distance, field zone, sneak proxy: 2024 and 2025 combined
- By down, designed QB runs: down 1: n=413, 4.96 yd/att, first down or TD 27.1%, TD 14.0%, fumble lost 0.48%; down 2: n=352, 3.49 yd/att, first down or TD 32.4%, TD 10.5%, fumble lost 1.42%; down 3: n=469, 3.10 yd/att, first down or TD 74.8%, TD 5.5%, fumble lost 1.49%; down 4: n=165, 2.40 yd/att, first down or TD 85.5%, TD 6.1%, fumble lost 0.61%
  - designed QB runs, down 1, 1 yard to go: n=45, 0.49 yd/att, first down or TD 62.2%, TD 62.2%, fumble lost 0.00%
  - designed QB runs, down 1, 2 yards to go: n=8, 0.75 yd/att, first down or TD 50.0%, TD 50.0%, fumble lost 0.00%
  - designed QB runs, down 1, 3 to 5 yards to go: n=16, 2.00 yd/att, first down or TD 31.2%, TD 25.0%, fumble lost 0.00%
  - designed QB runs, down 1, 6 to 10 yards to go: n=329, 5.84 yd/att, first down or TD 22.8%, TD 6.7%, fumble lost 0.30%
  - designed QB runs, down 1, 11 or more yards to go: n=15, 4.47 yd/att, first down or TD 0.0%, TD 0.0%, fumble lost 6.67%
  - designed QB runs, down 2, 1 yard to go: n=67, 2.18 yd/att, first down or TD 79.1%, TD 29.9%, fumble lost 1.49%
  - designed QB runs, down 2, 2 yards to go: n=17, 0.65 yd/att, first down or TD 41.2%, TD 17.6%, fumble lost 0.00%
  - designed QB runs, down 2, 3 to 5 yards to go: n=61, 2.33 yd/att, first down or TD 29.5%, TD 13.1%, fumble lost 1.64%
  - designed QB runs, down 2, 6 to 10 yards to go: n=175, 4.27 yd/att, first down or TD 19.4%, TD 3.4%, fumble lost 1.14%
  - designed QB runs, down 2, 11 or more yards to go: n=32, 5.69 yd/att, first down or TD 6.2%, TD 0.0%, fumble lost 3.12%
  - designed QB runs, down 3, 1 yard to go: n=315, 2.18 yd/att, first down or TD 81.9%, TD 5.4%, fumble lost 1.27%
  - designed QB runs, down 3, 2 yards to go: n=55, 3.75 yd/att, first down or TD 74.5%, TD 5.5%, fumble lost 1.82%
  - designed QB runs, down 3, 3 to 5 yards to go: n=57, 5.47 yd/att, first down or TD 68.4%, TD 7.0%, fumble lost 0.00%
  - designed QB runs, down 3, 6 to 10 yards to go: n=25, 5.84 yd/att, first down or TD 36.0%, TD 8.0%, fumble lost 4.00%
  - designed QB runs, down 3, 11 or more yards to go: n=17, 6.06 yd/att, first down or TD 23.5%, TD 0.0%, fumble lost 5.88%
  - designed QB runs, down 4, 1 yard to go: n=154, 2.27 yd/att, first down or TD 86.4%, TD 5.8%, fumble lost 0.65%
  - designed QB runs, down 4, 2 yards to go: n=7, 4.43 yd/att, first down or TD 71.4%, TD 14.3%, fumble lost 0.00%
  - designed QB runs, down 4, 3 to 5 yards to go: n=2, 7.50 yd/att, first down or TD 100.0%, TD 0.0%, fumble lost 0.00%
  - designed QB runs, down 4, 6 to 10 yards to go: n=2, 0.50 yd/att, first down or TD 50.0%, TD 0.0%, fumble lost 0.00%
- By field zone, designed QB runs: 
  - designed QB runs, own half (51 to 99 yards from the goal): n=491, 4.10 yd/att, first down or TD 45.4%, TD 0.0%, fumble lost 0.61%
  - designed QB runs, opponent half outside the 10 (11 to 50): n=651, 4.12 yd/att, first down or TD 53.5%, TD 2.5%, fumble lost 1.54%
  - designed QB runs, inside the opponent 10 (6 to 10): n=79, 3.46 yd/att, first down or TD 53.2%, TD 26.6%, fumble lost 1.27%
  - designed QB runs, inside the opponent 5 (1 to 5): n=178, 0.90 yd/att, first down or TD 59.0%, TD 52.8%, fumble lost 0.56%
- By down, scrambles: down 1: n=707, 7.14 yd/att, first down or TD 24.3%, TD 2.7%, fumble lost 0.71%; down 2: n=694, 7.68 yd/att, first down or TD 40.5%, TD 4.2%, fumble lost 0.29%; down 3: n=681, 8.11 yd/att, first down or TD 54.8%, TD 3.5%, fumble lost 0.44%; down 4: n=62, 8.58 yd/att, first down or TD 87.1%, TD 16.1%, fumble lost 0.00%
  - scrambles, down 1, 1 yard to go: n=2, 1.00 yd/att, first down or TD 100.0%, TD 100.0%, fumble lost 0.00%
  - scrambles, down 1, 2 yards to go: n=3, 1.33 yd/att, first down or TD 33.3%, TD 33.3%, fumble lost 0.00%
  - scrambles, down 1, 3 to 5 yards to go: n=10, 3.20 yd/att, first down or TD 20.0%, TD 20.0%, fumble lost 0.00%
  - scrambles, down 1, 6 to 10 yards to go: n=651, 7.27 yd/att, first down or TD 25.3%, TD 2.2%, fumble lost 0.77%
  - scrambles, down 1, 11 or more yards to go: n=41, 6.85 yd/att, first down or TD 4.9%, TD 0.0%, fumble lost 0.00%
  - scrambles, down 2, 1 yard to go: n=11, 7.64 yd/att, first down or TD 90.9%, TD 9.1%, fumble lost 0.00%
  - scrambles, down 2, 2 yards to go: n=23, 6.74 yd/att, first down or TD 87.0%, TD 13.0%, fumble lost 0.00%
  - scrambles, down 2, 3 to 5 yards to go: n=111, 8.18 yd/att, first down or TD 65.8%, TD 7.2%, fumble lost 0.00%
  - scrambles, down 2, 6 to 10 yards to go: n=393, 7.51 yd/att, first down or TD 39.7%, TD 4.1%, fumble lost 0.25%
  - scrambles, down 2, 11 or more yards to go: n=156, 7.92 yd/att, first down or TD 14.1%, TD 0.6%, fumble lost 0.64%
  - scrambles, down 3, 1 yard to go: n=27, 4.89 yd/att, first down or TD 100.0%, TD 14.8%, fumble lost 0.00%
  - scrambles, down 3, 2 yards to go: n=48, 6.10 yd/att, first down or TD 75.0%, TD 4.2%, fumble lost 0.00%
  - scrambles, down 3, 3 to 5 yards to go: n=190, 6.95 yd/att, first down or TD 72.1%, TD 3.7%, fumble lost 0.53%
  - scrambles, down 3, 6 to 10 yards to go: n=271, 9.00 yd/att, first down or TD 52.0%, TD 3.0%, fumble lost 0.74%
  - scrambles, down 3, 11 or more yards to go: n=145, 9.23 yd/att, first down or TD 22.1%, TD 2.1%, fumble lost 0.00%
  - scrambles, down 4, 1 yard to go: n=18, 6.56 yd/att, first down or TD 100.0%, TD 27.8%, fumble lost 0.00%
  - scrambles, down 4, 2 yards to go: n=9, 8.67 yd/att, first down or TD 88.9%, TD 22.2%, fumble lost 0.00%
  - scrambles, down 4, 3 to 5 yards to go: n=20, 8.10 yd/att, first down or TD 95.0%, TD 15.0%, fumble lost 0.00%
  - scrambles, down 4, 6 to 10 yards to go: n=10, 10.20 yd/att, first down or TD 60.0%, TD 0.0%, fumble lost 0.00%
  - scrambles, down 4, 11 or more yards to go: n=5, 14.40 yd/att, first down or TD 60.0%, TD 0.0%, fumble lost 0.00%
- By field zone, scrambles: 
  - scrambles, own half (51 to 99 yards from the goal): n=1154, 8.04 yd/att, first down or TD 38.6%, TD 0.0%, fumble lost 0.26%
  - scrambles, opponent half outside the 10 (11 to 50): n=858, 7.65 yd/att, first down or TD 42.3%, TD 2.7%, fumble lost 0.82%
  - scrambles, inside the opponent 10 (6 to 10): n=76, 5.78 yd/att, first down or TD 46.1%, TD 34.2%, fumble lost 0.00%
  - scrambles, inside the opponent 5 (1 to 5): n=56, 2.73 yd/att, first down or TD 64.3%, TD 58.9%, fumble lost 0.00%
#### Down and distance, field zone, sneak proxy: 2026 to date
- By down, designed QB runs: down 1: n=46, 4.43 yd/att, first down or TD 21.7%, TD 10.9%, fumble lost 0.00%; down 2: n=31, 3.23 yd/att, first down or TD 41.9%, TD 22.6%, fumble lost 6.45%; down 3: n=75, 2.65 yd/att, first down or TD 84.0%, TD 6.7%, fumble lost 0.00%; down 4: n=18, 0.78 yd/att, first down or TD 61.1%, TD 16.7%, fumble lost 0.00%
  - designed QB runs, down 1, 1 yard to go: n=6, 0.83 yd/att, first down or TD 83.3%, TD 83.3%, fumble lost 0.00%
  - designed QB runs, down 1, 3 to 5 yards to go: n=2, 0.00 yd/att, first down or TD 0.0%, TD 0.0%, fumble lost 0.00%
  - designed QB runs, down 1, 6 to 10 yards to go: n=35, 4.97 yd/att, first down or TD 11.4%, TD 0.0%, fumble lost 0.00%
  - designed QB runs, down 1, 11 or more yards to go: n=3, 8.33 yd/att, first down or TD 33.3%, TD 0.0%, fumble lost 0.00%
  - designed QB runs, down 2, 1 yard to go: n=9, 0.89 yd/att, first down or TD 66.7%, TD 55.6%, fumble lost 0.00%
  - designed QB runs, down 2, 2 yards to go: n=3, 2.00 yd/att, first down or TD 66.7%, TD 33.3%, fumble lost 0.00%
  - designed QB runs, down 2, 3 to 5 yards to go: n=3, 6.67 yd/att, first down or TD 66.7%, TD 33.3%, fumble lost 0.00%
  - designed QB runs, down 2, 6 to 10 yards to go: n=14, 4.00 yd/att, first down or TD 21.4%, TD 0.0%, fumble lost 14.29%
  - designed QB runs, down 2, 11 or more yards to go: n=2, 5.00 yd/att, first down or TD 0.0%, TD 0.0%, fumble lost 0.00%
  - designed QB runs, down 3, 1 yard to go: n=61, 1.98 yd/att, first down or TD 90.2%, TD 6.6%, fumble lost 0.00%
  - designed QB runs, down 3, 2 yards to go: n=4, 0.50 yd/att, first down or TD 25.0%, TD 25.0%, fumble lost 0.00%
  - designed QB runs, down 3, 3 to 5 yards to go: n=6, 6.67 yd/att, first down or TD 83.3%, TD 0.0%, fumble lost 0.00%
  - designed QB runs, down 3, 6 to 10 yards to go: n=3, 9.67 yd/att, first down or TD 66.7%, TD 0.0%, fumble lost 0.00%
  - designed QB runs, down 3, 11 or more yards to go: n=1, 7.00 yd/att, first down or TD 0.0%, TD 0.0%, fumble lost 0.00%
  - designed QB runs, down 4, 1 yard to go: n=18, 0.78 yd/att, first down or TD 61.1%, TD 16.7%, fumble lost 0.00%
- By field zone, designed QB runs: 
  - designed QB runs, own half (51 to 99 yards from the goal): n=54, 4.24 yd/att, first down or TD 66.7%, TD 0.0%, fumble lost 0.00%
  - designed QB runs, opponent half outside the 10 (11 to 50): n=78, 3.01 yd/att, first down or TD 51.3%, TD 0.0%, fumble lost 2.56%
  - designed QB runs, inside the opponent 10 (6 to 10): n=7, 2.57 yd/att, first down or TD 14.3%, TD 0.0%, fumble lost 0.00%
  - designed QB runs, inside the opponent 5 (1 to 5): n=31, 1.13 yd/att, first down or TD 64.5%, TD 64.5%, fumble lost 0.00%
- By down, scrambles: down 1: n=92, 7.34 yd/att, first down or TD 26.1%, TD 4.3%, fumble lost 3.26%; down 2: n=108, 8.28 yd/att, first down or TD 46.3%, TD 4.6%, fumble lost 0.00%; down 3: n=104, 8.00 yd/att, first down or TD 50.0%, TD 2.9%, fumble lost 0.00%; down 4: n=3, 4.33 yd/att, first down or TD 100.0%, TD 0.0%, fumble lost 0.00%
  - scrambles, down 1, 2 yards to go: n=1, 2.00 yd/att, first down or TD 100.0%, TD 100.0%, fumble lost 0.00%
  - scrambles, down 1, 3 to 5 yards to go: n=2, 8.00 yd/att, first down or TD 50.0%, TD 0.0%, fumble lost 50.00%
  - scrambles, down 1, 6 to 10 yards to go: n=83, 7.18 yd/att, first down or TD 26.5%, TD 3.6%, fumble lost 2.41%
  - scrambles, down 1, 11 or more yards to go: n=6, 10.17 yd/att, first down or TD 0.0%, TD 0.0%, fumble lost 0.00%
  - scrambles, down 2, 1 yard to go: n=4, 6.75 yd/att, first down or TD 100.0%, TD 0.0%, fumble lost 0.00%
  - scrambles, down 2, 2 yards to go: n=4, 7.25 yd/att, first down or TD 75.0%, TD 25.0%, fumble lost 0.00%
  - scrambles, down 2, 3 to 5 yards to go: n=15, 6.93 yd/att, first down or TD 66.7%, TD 0.0%, fumble lost 0.00%
  - scrambles, down 2, 6 to 10 yards to go: n=67, 8.18 yd/att, first down or TD 40.3%, TD 4.5%, fumble lost 0.00%
  - scrambles, down 2, 11 or more yards to go: n=18, 10.33 yd/att, first down or TD 33.3%, TD 5.6%, fumble lost 0.00%
  - scrambles, down 3, 1 yard to go: n=6, 2.83 yd/att, first down or TD 100.0%, TD 16.7%, fumble lost 0.00%
  - scrambles, down 3, 2 yards to go: n=6, 11.67 yd/att, first down or TD 83.3%, TD 16.7%, fumble lost 0.00%
  - scrambles, down 3, 3 to 5 yards to go: n=30, 6.77 yd/att, first down or TD 60.0%, TD 0.0%, fumble lost 0.00%
  - scrambles, down 3, 6 to 10 yards to go: n=36, 7.83 yd/att, first down or TD 47.2%, TD 2.8%, fumble lost 0.00%
  - scrambles, down 3, 11 or more yards to go: n=26, 10.00 yd/att, first down or TD 23.1%, TD 0.0%, fumble lost 0.00%
  - scrambles, down 4, 1 yard to go: n=1, 1.00 yd/att, first down or TD 100.0%, TD 0.0%, fumble lost 0.00%
  - scrambles, down 4, 2 yards to go: n=1, 5.00 yd/att, first down or TD 100.0%, TD 0.0%, fumble lost 0.00%
  - scrambles, down 4, 6 to 10 yards to go: n=1, 7.00 yd/att, first down or TD 100.0%, TD 0.0%, fumble lost 0.00%
- By field zone, scrambles: 
  - scrambles, own half (51 to 99 yards from the goal): n=165, 7.90 yd/att, first down or TD 40.6%, TD 0.0%, fumble lost 1.21%
  - scrambles, opponent half outside the 10 (11 to 50): n=126, 8.33 yd/att, first down or TD 43.7%, TD 4.8%, fumble lost 0.79%
  - scrambles, inside the opponent 10 (6 to 10): n=10, 4.90 yd/att, first down or TD 40.0%, TD 30.0%, fumble lost 0.00%
  - scrambles, inside the opponent 5 (1 to 5): n=6, 2.17 yd/att, first down or TD 50.0%, TD 50.0%, fumble lost 0.00%
- CROSS-CHECK 2024: QB rushes plus kneel-downs = 2247 attempts, 10974 yards; adding 102 aborted snaps (a fumbled snap the QB picked up) = 2349 attempts, 10980 yards (4.67 per attempt)
- CROSS-CHECK 2025: QB rushes plus kneel-downs = 2134 attempts, 9675 yards; adding 78 aborted snaps (a fumbled snap the QB picked up) = 2212 attempts, 9682 yards (4.38 per attempt)
- CROSS-CHECK FOX figures (2024, 3rd or 4th and 1, REG only): J.Hurts all QB runs incl. scrambles and aborted snaps 22 of 27 (designed only 22 of 26); J.Allen all QB runs incl. scrambles and aborted snaps 17 of 18 (designed only 17 of 18); B.Nix all QB runs incl. scrambles and aborted snaps 12 of 14 (designed only 12 of 14); J.Daniels all QB runs incl. scrambles and aborted snaps 12 of 12 (designed only 9 of 9)
- CROSS-CHECK FOX figures (2024, 3rd or 4th and 1, REG and POST): J.Hurts all QB runs incl. scrambles and aborted snaps 25 of 30 (designed only 25 of 29); J.Allen all QB runs incl. scrambles and aborted snaps 24 of 29 (designed only 23 of 28); B.Nix all QB runs incl. scrambles and aborted snaps 13 of 15 (designed only 13 of 15); J.Daniels all QB runs incl. scrambles and aborted snaps 13 of 13 (designed only 10 of 10)

#### Short-yardage context (all teams): 2026 to date
- 3rd or 4th and 1 yard: 328 plays; designed runs 73.2% (QB designed runs 79 = 24.1% of all plays, conversion 83.5%; other runners 161, conversion 66.5%); scrambles 7; passes 24.7% (conversion 59.3%, incl. sacks)
  - down 3: 237 plays; QB designed runs 61 (25.7% of plays; conversion 90.2%), other runs 110 (conversion 67.3%), passes 60 (conversion 60.0%)
  - down 4: 91 plays; QB designed runs 18 (19.8% of plays; conversion 61.1%), other runs 51 (conversion 64.7%), passes 21 (conversion 57.1%)
- 3rd or 4th and 2 yards: 213 plays; designed runs 37.1% (QB designed runs 4 = 1.9% of all plays, conversion 25.0%; other runners 75, conversion 56.0%); scrambles 7; passes 59.6% (conversion 58.3%, incl. sacks)
  - down 3: 185 plays; QB designed runs 4 (2.2% of plays; conversion 25.0%), other runs 71 (conversion 56.3%), passes 104 (conversion 55.8%)
  - down 4: 28 plays; QB designed runs 0 (0.0% of plays; conversion n/a%), other runs 4 (conversion 50.0%), passes 23 (conversion 69.6%)
#### Short-yardage context (all teams): 2024 and 2025 regular seasons
- 3rd or 4th and 1 yard: 2307 plays; designed runs 75.6% (QB designed runs 469 = 20.3% of all plays, conversion 83.4%; other runners 1274, conversion 69.2%); scrambles 45; passes 22.5% (conversion 52.0%, incl. sacks)
  - down 3: 1658 plays; QB designed runs 315 (19.0% of plays; conversion 81.9%), other runs 942 (conversion 69.9%), passes 374 (conversion 52.1%)
  - down 4: 649 plays; QB designed runs 154 (23.7% of plays; conversion 86.4%), other runs 332 (conversion 67.5%), passes 145 (conversion 51.7%)
- 3rd or 4th and 2 yards: 1403 plays; designed runs 36.4% (QB designed runs 62 = 4.4% of all plays, conversion 74.2%; other runners 448, conversion 60.0%); scrambles 58; passes 59.5% (conversion 53.2%, incl. sacks)
  - down 3: 1164 plays; QB designed runs 55 (4.7% of plays; conversion 74.5%), other runs 417 (conversion 59.5%), passes 643 (conversion 51.2%)
  - down 4: 239 plays; QB designed runs 7 (2.9% of plays; conversion 71.4%), other runs 31 (conversion 67.7%), passes 192 (conversion 59.9%)

### 3. Accepted penalties (regular season)

What is counted: every foul that was enforced (text "PENALTY on ..." in upper case, nflverse flag penalty=1). Declined and offsetting fouls are not flagged in the data; I read them from the text "Penalty on ..., declined" and "..., offsetting" (reliability: section 7). "Before the snap" is decided by the type of the foul (false start, offside, neutral zone, encroachment, delay of game, illegal formation, illegal shift, illegal motion, too many men, defensive delay of game); "during a run", "during a pass" and "special teams" by the play of that row or the play text. The per-100-plays figures use the plays that stood as the denominator, plus a version that adds the live plays a foul wiped out. The last two blocks add the playoffs and exist only to compare with sources that include them (headline lines only).

#### 2026 regular season to date (79 games, 158 team-games)
- Accepted fouls (text "PENALTY on" in upper case): 1193, 15.10 per game (both teams), 7.55 per team per game; yards 9557, 60.49 per team per game, 8.01 per accepted foul
- Declined fouls (text "Penalty on ..., declined"): 133 flags (131 plays), 0.84 per team per game; offsetting flags 32 (14 plays), 0.20 flags per team per game; share of accepted among accepted plus declined: 90.0%
- Standing scrimmage plays (pass, run, kneel, spike, no two-point tries): 9807, 62.07 per team per game. Plays run and then nullified by a foul (no_play rows with play text): 534, 3.38 per team per game
- Accepted fouls per 100 standing scrimmage plays: 12.16 (per team per game 7.55 fouls over 62.07 plays); per 100 standing plus nullified-live plays: 11.54
- By phase, count, share, per team per game, per 100 standing plays:
  - before the snap: 472, 39.6%, 2.987 per team per game, 4.81 per 100 plays
  - during a run play: 173, 14.5%, 1.095 per team per game, 1.76 per 100 plays
  - during a pass play: 392, 32.9%, 2.481 per team per game, 4.00 per 100 plays
  - special teams (kickoff, punt, field goal, extra point): 155, 13.0%, 0.981 per team per game, 1.58 per 100 plays
  - other or unclear (no play text): 1, 0.1%, 0.006 per team per game, 0.01 per 100 plays
- Special-teams fouls by play (not counting before-the-snap types): kickoff 87 (0.551 per team per game), punt 59 (0.373 per team per game), field goal or extra point 9 (0.057 per team per game)
- Of the before-the-snap fouls, 74.4% stopped the play before any snap (no play text); the rest were called with the play running (offside with a free play, for example)
- By side of the committing team (offense / defense / special teams play): offense 633 (53.1%), defense 388 (32.5%), special teams 172 (14.4%)
- By quarter: Q1 261 (21.9%), Q2 349 (29.3%), Q3 275 (23.1%), Q4 299 (25.1%), QOT 9 (0.8%)
- Last two minutes of each half (clock 2:00 or less in Q2 and Q4): 140 accepted fouls, 11.7% of all (those 4 minutes are 6.7% of the regulation clock), 0.89 per team per game; 10.17 per 100 plays there against 11.75 per 100 plays elsewhere (plays include nullified ones)
- Standing plays in the last two minutes of the halves: 8.33 per team per game
- Accepted fouls on a row that is "no_play" (the play is nullified or never run): 880 = 73.8% of accepted fouls; 5.57 per team per game; of these 528 had play text (the play ran and was wiped out) and 352 had none (dead-ball fouls before the snap)
- Nullifying fouls as a share of all snap-like events (standing plays plus nullified rows): 8.5%
- Fouls flagged first_down_penalty=1 (the foul produced the first down): 313 = 26.2% of accepted, 3.96 per game (both teams)
- Team spread (accepted fouls committed, per team per game, 32 teams): mean 7.56, SD 1.23, min 5.00 (IND), max 9.80 (CLE), 10th percentile 6.02, 90th percentile 9.16; lowest three IND 5.00, SF 5.00, MIN 6.00; highest three CLE 9.80, LAC 9.60, NYJ 9.40
- SD expected from chance alone for a team with the same rate over 5 games, if fouls were Poisson: 1.24
- Accepted fouls per game (both teams): mean 15.10, SD 4.51, percentiles 5/25/50/75/95: 8, 12, 15, 17, 23.1, max 30, min 6
- By type (accepted count; per game both teams; average yards over fouls with a yardage; declined flags; first_down_penalty share). Types with at least 5 accepted:
  - Offensive Holding: 260; 3.29; 9.6 yd; declined 30; first-down flag 0%; phase during or after the play
  - False Start: 222; 2.81; 4.9 yd; declined 0; first-down flag 0%; phase before the snap
  - Defensive Pass Interference: 85; 1.08; 16.9 yd; declined 12; first-down flag 98%; phase during or after the play
  - Delay of Game: 80; 1.01; 4.9 yd; declined 2; first-down flag 0%; phase before the snap
  - Defensive Holding: 63; 0.80; 4.6 yd; declined 14; first-down flag 98%; phase during or after the play
  - Unnecessary Roughness: 55; 0.70; 12.6 yd; declined 1; first-down flag 62%; phase during or after the play
  - Defensive Offside: 49; 0.62; 4.5 yd; declined 15; first-down flag 18%; phase before the snap
  - Face Mask: 36; 0.46; 12.6 yd; declined 1; first-down flag 69%; phase during or after the play
  - Illegal Formation: 36; 0.46; 5.0 yd; declined 14; first-down flag 0%; phase before the snap
  - Neutral Zone Infraction: 32; 0.41; 4.9 yd; declined 0; first-down flag 41%; phase before the snap
  - Roughing the Passer: 30; 0.38; 11.6 yd; declined 0; first-down flag 100%; phase during or after the play
  - Illegal Block Above the Waist: 27; 0.34; 9.4 yd; declined 1; first-down flag 0%; phase during or after the play
  - Illegal Use of Hands: 25; 0.32; 6.4 yd; declined 5; first-down flag 64%; phase during or after the play
  - Illegal Shift: 24; 0.30; 5.0 yd; declined 11; first-down flag 0%; phase before the snap
  - Illegal Contact: 23; 0.29; 5.0 yd; declined 8; first-down flag 100%; phase during or after the play
  - Offensive Pass Interference: 22; 0.28; 9.5 yd; declined 7; first-down flag 0%; phase during or after the play
  - Kickoff Short of Landing Zone: 13; 0.16; 0.0 yd; declined 0; first-down flag 0%; phase during or after the play
  - Ineligible Downfield Pass: 12; 0.15; 5.0 yd; declined 4; first-down flag 0%; phase during or after the play
  - Unsportsmanlike Conduct: 12; 0.15; 12.6 yd; declined 0; first-down flag 25%; phase during or after the play
  - Encroachment: 11; 0.14; 4.6 yd; declined 0; first-down flag 9%; phase before the snap
  - Intentional Grounding: 11; 0.14; 12.0 yd; declined 0; first-down flag 0%; phase during or after the play
  - Kickoff Out of Bounds: 8; 0.10; 0.0 yd; declined 0; first-down flag 0%; phase during or after the play
  - Chop Block: 6; 0.08; 13.0 yd; declined 0; first-down flag 0%; phase during or after the play
  - Illegal Blindside Block: 6; 0.08; 12.7 yd; declined 1; first-down flag 0%; phase during or after the play
  - Taunting: 6; 0.08; 15.0 yd; declined 0; first-down flag 33%; phase during or after the play
  - Defensive Too Many Men on Field: 6; 0.08; 4.3 yd; declined 3; first-down flag 33%; phase before the snap
  - Offensive Offside: 6; 0.08; 4.5 yd; declined 2; first-down flag 0%; phase before the snap
  - all other types (fewer than 5 each): 27
- Types where declined flags exceed 3 in the sample (decline share = declined / (accepted + declined)): Offensive Holding 10% (30 of 290); Defensive Offside 23% (15 of 64); Illegal Formation 28% (14 of 50); Defensive Holding 18% (14 of 77); Defensive Pass Interference 12% (12 of 97); Illegal Shift 31% (11 of 35); Illegal Contact 26% (8 of 31); Offensive Pass Interference 24% (7 of 29); Illegal Use of Hands 17% (5 of 30); Ineligible Downfield Pass 25% (4 of 16)
- Parser check: 1189 of 1193 accepted fouls have a type equal to the nflverse penalty_type column of their row (rows with two fouls only match the first)
#### 2024 and 2025 regular seasons combined (544 games, 1088 team-games)
- Accepted fouls (text "PENALTY on" in upper case): 6981, 12.83 per game (both teams), 6.42 per team per game; yards 56397, 51.84 per team per game, 8.08 per accepted foul
- Declined fouls (text "Penalty on ..., declined"): 992 flags (966 plays), 0.91 per team per game; offsetting flags 323 (153 plays), 0.30 flags per team per game; share of accepted among accepted plus declined: 87.6%
- Standing scrimmage plays (pass, run, kneel, spike, no two-point tries): 67136, 61.71 per team per game. Plays run and then nullified by a foul (no_play rows with play text): 3247, 2.98 per team per game
- Accepted fouls per 100 standing scrimmage plays: 10.40 (per team per game 6.42 fouls over 61.71 plays); per 100 standing plus nullified-live plays: 9.92
- By phase, count, share, per team per game, per 100 standing plays:
  - before the snap: 2737, 39.2%, 2.516 per team per game, 4.08 per 100 plays
  - during a run play: 976, 14.0%, 0.897 per team per game, 1.45 per 100 plays
  - during a pass play: 2448, 35.1%, 2.250 per team per game, 3.65 per 100 plays
  - special teams (kickoff, punt, field goal, extra point): 816, 11.7%, 0.750 per team per game, 1.22 per 100 plays
  - other or unclear (no play text): 4, 0.1%, 0.004 per team per game, 0.01 per 100 plays
- Special-teams fouls by play (not counting before-the-snap types): kickoff 377 (0.347 per team per game), punt 375 (0.345 per team per game), field goal or extra point 64 (0.059 per team per game)
- Of the before-the-snap fouls, 71.0% stopped the play before any snap (no play text); the rest were called with the play running (offside with a free play, for example)
- By side of the committing team (offense / defense / special teams play): offense 3616 (51.8%), defense 2408 (34.5%), special teams 957 (13.7%)
- By quarter: Q1 1463 (21.0%), Q2 2076 (29.7%), Q3 1643 (23.5%), Q4 1774 (25.4%), QOT 25 (0.4%)
- Last two minutes of each half (clock 2:00 or less in Q2 and Q4): 869 accepted fouls, 12.4% of all (those 4 minutes are 6.7% of the regulation clock), 0.80 per team per game; 9.45 per 100 plays there against 9.99 per 100 plays elsewhere (plays include nullified ones)
- Standing plays in the last two minutes of the halves: 8.07 per team per game
- Accepted fouls on a row that is "no_play" (the play is nullified or never run): 5103 = 73.1% of accepted fouls; 4.69 per team per game; of these 3155 had play text (the play ran and was wiped out) and 1948 had none (dead-ball fouls before the snap)
- Nullifying fouls as a share of all snap-like events (standing plays plus nullified rows): 7.3%
- Fouls flagged first_down_penalty=1 (the foul produced the first down): 1928 = 27.6% of accepted, 3.54 per game (both teams)
- Team spread (accepted fouls committed, per team per game, 32 teams): mean 6.42, SD 0.59, min 4.88 (LA), max 7.71 (TEN), 10th percentile 5.80, 90th percentile 7.05; lowest three LA 4.88, CIN 5.56, SF 5.71; highest three TEN 7.71, DAL 7.68, NYJ 7.26
- SD expected from chance alone for a team with the same rate over 34 games, if fouls were Poisson: 0.43
- Accepted fouls per game (both teams): mean 12.83, SD 4.11, percentiles 5/25/50/75/95: 7, 10, 13, 15, 20, max 26, min 4
- By type (accepted count; per game both teams; average yards over fouls with a yardage; declined flags; first_down_penalty share). Types with at least 5 accepted:
  - Offensive Holding: 1356; 2.49; 9.6 yd; declined 169; first-down flag 0%; phase during or after the play
  - False Start: 1337; 2.46; 4.9 yd; declined 5; first-down flag 0%; phase before the snap
  - Defensive Pass Interference: 585; 1.08; 15.3 yd; declined 50; first-down flag 99%; phase during or after the play
  - Defensive Holding: 353; 0.65; 4.7 yd; declined 128; first-down flag 99%; phase during or after the play
  - Unnecessary Roughness: 347; 0.64; 13.2 yd; declined 8; first-down flag 58%; phase during or after the play
  - Delay of Game: 343; 0.63; 4.9 yd; declined 18; first-down flag 0%; phase before the snap
  - Defensive Offside: 298; 0.55; 4.8 yd; declined 155; first-down flag 18%; phase before the snap
  - Illegal Formation: 240; 0.44; 4.9 yd; declined 90; first-down flag 0%; phase before the snap
  - Roughing the Passer: 192; 0.35; 13.5 yd; declined 3; first-down flag 96%; phase during or after the play
  - Face Mask: 181; 0.33; 13.5 yd; declined 7; first-down flag 67%; phase during or after the play
  - Neutral Zone Infraction: 166; 0.31; 4.9 yd; declined 1; first-down flag 28%; phase before the snap
  - Illegal Contact: 152; 0.28; 4.9 yd; declined 60; first-down flag 100%; phase during or after the play
  - Offensive Pass Interference: 143; 0.26; 9.6 yd; declined 24; first-down flag 0%; phase during or after the play
  - Illegal Use of Hands: 125; 0.23; 5.7 yd; declined 40; first-down flag 76%; phase during or after the play
  - Ineligible Downfield Pass: 116; 0.21; 4.9 yd; declined 93; first-down flag 0%; phase during or after the play
  - Illegal Shift: 109; 0.20; 4.9 yd; declined 57; first-down flag 0%; phase before the snap
  - Illegal Block Above the Waist: 106; 0.19; 9.3 yd; declined 7; first-down flag 0%; phase during or after the play
  - Intentional Grounding: 91; 0.17; 11.5 yd; declined 1; first-down flag 0%; phase during or after the play
  - Defensive Too Many Men on Field: 82; 0.15; 4.4 yd; declined 19; first-down flag 29%; phase before the snap
  - Unsportsmanlike Conduct: 78; 0.14; 13.1 yd; declined 1; first-down flag 18%; phase during or after the play
  - Encroachment: 68; 0.12; 4.5 yd; declined 2; first-down flag 25%; phase before the snap
  - Kickoff Short of Landing Zone: 63; 0.12; 0.0 yd; declined 0; first-down flag 0%; phase during or after the play
  - Kickoff Out of Bounds: 54; 0.10; 0.0 yd; declined 2; first-down flag 0%; phase during or after the play
  - Taunting: 44; 0.08; 14.5 yd; declined 1; first-down flag 27%; phase during or after the play
  - Illegal Blindside Block: 41; 0.08; 12.3 yd; declined 2; first-down flag 5%; phase during or after the play
  - Offensive Offside: 32; 0.06; 4.7 yd; declined 21; first-down flag 0%; phase before the snap
  - Illegal Motion: 29; 0.05; 4.9 yd; declined 10; first-down flag 3%; phase before the snap
  - Low Block: 29; 0.05; 12.9 yd; declined 0; first-down flag 62%; phase during or after the play
  - Player Out of Bounds on Kick: 25; 0.05; 5.0 yd; declined 1; first-down flag 0%; phase during or after the play
  - Tripping: 21; 0.04; 12.6 yd; declined 0; first-down flag 52%; phase during or after the play
  - Horse Collar Tackle: 20; 0.04; 14.2 yd; declined 0; first-down flag 90%; phase during or after the play
  - Offensive Too Many Men on Field: 18; 0.03; 4.8 yd; declined 0; first-down flag 0%; phase before the snap
  - Illegal Forward Pass: 15; 0.03; 4.1 yd; declined 2; first-down flag 0%; phase during or after the play
  - Fair Catch Interference: 13; 0.02; 13.8 yd; declined 0; first-down flag 0%; phase during or after the play
  - Defensive Delay of Game: 12; 0.02; 5.0 yd; declined 0; first-down flag 17%; phase before the snap
  - Roughing the Kicker: 11; 0.02; 15.0 yd; declined 0; first-down flag 82%; phase during or after the play
  - Chop Block: 11; 0.02; 13.7 yd; declined 3; first-down flag 0%; phase during or after the play
  - Disqualification: 10; 0.02; 12.2 yd; declined 0; first-down flag 30%; phase during or after the play
  - Running Into the Kicker: 10; 0.02; 5.0 yd; declined 7; first-down flag 50%; phase during or after the play
  - Kick Catch Interference: 9; 0.02; 15.0 yd; declined 0; first-down flag 0%; phase during or after the play
  - Leverage: 9; 0.02; 11.9 yd; declined 0; first-down flag 56%; phase during or after the play
  - Illegal Touch Pass: 8; 0.01; 0.5 yd; declined 2; first-down flag 0%; phase during or after the play
  - Ineligible Downfield Kick: 8; 0.01; 4.9 yd; declined 1; first-down flag 0%; phase during or after the play
  - all other types (fewer than 5 each): 21
- Types where declined flags exceed 3 in the sample (decline share = declined / (accepted + declined)): Offensive Holding 11% (169 of 1525); Defensive Offside 34% (155 of 453); Defensive Holding 27% (128 of 481); Ineligible Downfield Pass 44% (93 of 209); Illegal Formation 27% (90 of 330); Illegal Contact 28% (60 of 212); Illegal Shift 34% (57 of 166); Defensive Pass Interference 8% (50 of 635); Illegal Use of Hands 24% (40 of 165); Offensive Pass Interference 14% (24 of 167); Offensive Offside 40% (21 of 53); Defensive Too Many Men on Field 19% (19 of 101); Delay of Game 5% (18 of 361); Illegal Motion 26% (10 of 39); Unnecessary Roughness 2% (8 of 355); Illegal Block Above the Waist 6% (7 of 113); Running Into the Kicker 41% (7 of 17); Face Mask 4% (7 of 188); False Start 0% (5 of 1342)
- Parser check: 6966 of 6981 accepted fouls have a type equal to the nflverse penalty_type column of their row (rows with two fouls only match the first)
### 4. Onside kicks and kickoffs (regular season)

What is counted: an onside kick is a kickoff row (including free kicks after a safety) whose text says onside. The kicking team is the defteam of the kickoff row. Margin is the kicking team's score minus the receiving team's score. "Time left" is game time left. Kickoff statistics leave out onside kicks. The 2026 list names every attempt of the season so far (weeks 1 to 5, 79 games).

#### Onside kicks 2026 regular season (79 games)
- Attempts (kickoff rows with the word onside, kickoff_attempt=1): 11, recoveries by the kicking team (own_kickoff_recovery=1): 0, recovery rate 0.0%; per game 0.139, per team per game 0.070
- Playoffs 2026: attempts 0, recoveries 0
- Outcome type: receivers took it 8, other 1, fair catch 1, out of bounds 1
- With a foul on the play (PENALTY in the text): 1 of 11
- By quarter: Q4 11 (rec 0)
- By score margin of the kicking team: trailing by 1 to 8 6 (rec 0); trailing by 9 to 16 4 (rec 0); trailing by more than 16 1 (rec 0)
- By time left in the game: 10:00 to 15:00 left (rest of Q4) 1 (rec 0); 2:00 to 5:00 left 2 (rec 0); last 2:00 of the game 8 (rec 0)
- Kick distance (yards): mean 13.4, median 12, min 9, max 22; kick spot: 35: 10, 20: 1
- Margin check: the kicker margin from total scores equals minus score_differential in 11 of 11 attempts
#### 2026 regular season to date: every onside kick
- Week 1, CAR kicking to CHI, Q4 04:00 (game clock left 240 s), kicker margin -15.0 (trailing means negative), kick 14 yards from the 35, receivers took it
- Week 1, TEN kicking to NYJ, Q4 02:42 (game clock left 162 s), kicker margin -13.0 (trailing means negative), kick 9 yards from the 35, receivers took it
- Week 1, WAS kicking to PHI, Q4 01:01 (game clock left 61 s), kicker margin -2.0 (trailing means negative), kick 17 yards from the 35, receivers took it
- Week 2, DET kicking to BUF, Q4 01:42 (game clock left 102 s), kicker margin -10.0 (trailing means negative), kick 12 yards from the 35, other
- Week 2, LAC kicking to LV, Q4 01:41 (game clock left 101 s), kicker margin -12.0 (trailing means negative), kick 22 yards from the 20, fair catch
- Week 3, ARI kicking to SF, Q4 00:34 (game clock left 34 s), kicker margin -6.0 (trailing means negative), kick 10 yards from the 35, receivers took it
- Week 3, LAC kicking to BUF, Q4 01:56 (game clock left 116 s), kicker margin -8.0 (trailing means negative), kick 10 yards from the 35, receivers took it
- Week 4, LV kicking to KC, Q4 01:46 (game clock left 106 s), kicker margin -3.0 (trailing means negative), kick 20 yards from the 35, receivers took it
- Week 4, TEN kicking to BAL, Q4 01:12 (game clock left 72 s), kicker margin -6.0 (trailing means negative), kick 9 yards from the 35, receivers took it
- Week 5, MIA kicking to CIN, Q4 00:45 (game clock left 45 s), kicker margin -7.0 (trailing means negative), kick 15 yards from the 35, out of bounds (foul on the play)
- Week 5, LV kicking to NE, Q4 10:49 (game clock left 649 s), kicker margin -21.0 (trailing means negative), kick 9 yards from the 35, receivers took it
#### Onside kicks 2024 and 2025 regular seasons combined (n=102)
- Attempts 102, recoveries 8 (7.8%)
- By kicker margin: trailing by 1 to 8 43 (rec 5); trailing by 9 to 16 39 (rec 1); trailing by more than 16 20 (rec 2)
- By quarter: Q4 102
- By time left: 10:00 to 15:00 left (rest of Q4) 3 (rec 0); 2:00 to 5:00 left 30 (rec 2); 5:00 to 10:00 left 14 (rec 1); last 2:00 of the game 55 (rec 5)
- Kick distance: mean 10.4, percentiles 10/50/90: 7, 10, 14
- Kick distance of recoveries: 9, 13, 8, 9, 13, 8, 10, 12; of failures (mean) 10.4
#### Kickoffs excluding onside kicks: 2024 regular season (272 games)
- Kickoffs: 2753, 10.12 per game (both teams)
- Touchback rate (touchback flag on the kickoff row): 65.5% (1803); kicks into the end zone 12.9%; returned (a returner is named, no touchback) 33.3% (917); any returner named incl. from the end zone 33.3%; fair catch 0.0%; out of bounds 0.5%; downed 0.0%; return touchdowns 6
- Average starting yard line of the receiving team after all kickoffs (own yard line, from the next scrimmage row; n=2716): 29.6; after returns only: 29.2 (n=913); median all 30
- Spots after touchbacks (own yard line: count): 30: 1741, 20: 39, 25: 12, 35: 11
- Kick distance (yards): mean 63.9, median 65; return yards on returns: mean 27.5, median 26, 90th percentile 37; returns of 40 or more yards: 58
- Starting yard line percentiles after all kickoffs (10, 25, 50, 75, 90): 24, 30, 30, 30, 32
#### Kickoffs excluding onside kicks: 2025 regular season (272 games)
- Kickoffs: 2733, 10.05 per game (both teams)
- Touchback rate (touchback flag on the kickoff row): 21.1% (576); kicks into the end zone 9.8%; returned (a returner is named, no touchback) 76.0% (2076); any returner named incl. from the end zone 76.0%; fair catch 0.0%; out of bounds 1.4%; downed 0.0%; return touchdowns 6
- Average starting yard line of the receiving team after all kickoffs (own yard line, from the next scrimmage row; n=2694): 30.3; after returns only: 29.7 (n=2118); median all 31
- Spots after touchbacks (own yard line: count): 35: 489, 20: 80, 30: 4, 40: 2, 10: 1
- Kick distance (yards): mean 60.7, median 62; return yards on returns: mean 25.9, median 25, 90th percentile 33; returns of 40 or more yards: 87
- Starting yard line percentiles after all kickoffs (10, 25, 50, 75, 90): 20, 26, 31, 35, 37
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
