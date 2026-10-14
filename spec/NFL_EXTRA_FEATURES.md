# NFL_EXTRA_FEATURES (nfl4 only): the seven extra in-game features the finished clone must have

Status: REQUIREMENTS, version 0.1 (2026-10-14, written before P7 S7.3b on the owner's request, D-040). Nothing is designed or built yet. This file is a companion of GAME_SPEC (version 1.2 points to it in 17.4); it is not part of GAME_SPEC sections 1 to 15, which describe the original and stay exact.

Who reads this: Claude at the sessions named in section 14, and the owner. Plain headings and lists, no tables. Feature IDs here are NX1 to NX7 (never "F1" to "F7": those are the keys of the game).

## 1. Binding rules

- NX-R1 nfl4 only. These features belong to the NFL football clone and to no other game, program or utility. They never go into `shared\starter-kit`, `shared\`, `tools\`, the playbook files, or any other game's folder. The file lives in `spec\` so that `tools\sync_playbooks.py` (which copies only CLAUDE.md, the three playbooks and `fixesforgames.md`) cannot spread it. CLAUDE.md names it in rule 0.13 and in the few places that rule lists, always with "nfl4 only".
- NX-R2 Classic stays exact. GAME_SPEC 1.2 sections 1 to 15 and 17.2 still describe what the clone does when the extras are off. A setting called "Rules" has two values: "Classic" (every extra off, the clone plays and speaks exactly as the original, with the original's menus, keys, pauses, random draws and sounds) and "N. F. L. rules" (the seven features in this file, each with its own on/off switch under it). The S8.1 conformance tests run in Classic mode and must keep passing unchanged. The default value of the setting is open question NQ2.
- NX-R3 The features are required, not optional for the project. "Optional" in the owner's words about playbooks means the player may choose them in the game. The Windows release (P9 to P11) waits until all seven features are built and tested, unless the owner says otherwise (section 14).
- NX-R4 Evidence before memory (CLAUDE.md 0.3). Every NFL rule, number and Madden fact in this file carries one of three tags: SRC-OFFICIAL (read in the NFL rulebook, casebook or operations site, or in EA's own pages, with the page and date), SRC-SECONDARY (a news, team or reference site found by search; the date and link are in section 16), UNVERIFIED (from general knowledge, to be checked). Session SX.0 (section 14) turns every UNVERIFIED and every SRC-SECONDARY rule into SRC-OFFICIAL or records why it could not. No rule value is hard-coded: they live in one versioned data table (`nfl_rules_<year>`), so a later rule change is a data change.
- NX-R5 Lessons are shared, features are not. A bug or surprise found while building a feature is written into `fixesforgames.md` in general terms (CLAUDE.md 0.9) like any other lesson; the feature itself is never copied anywhere else.
- NX-R6 Madden. The owner asked for playbooks and a franchise mode "like Madden". Only football concepts and the structure of those features are taken as inspiration. No EA text, play-name list copied as a whole, ratings, art or sounds are copied. The README and the About item say: inspired by the playbooks and franchise ideas of Madden NFL; Madden NFL is a trademark of Electronic Arts; this project is not made, endorsed or supported by EA or the NFL. (Rule 0.1: the project still clones only Jim Kitchen's game; Madden is not cloned.)
- NX-R7 Style. Every new prompt, menu and sentence is in the manner of the original: short spoken sentences, the coach's name where the original uses it, a numbered menu with Up, Down, digits, Enter, a first-letter key where it fits, F1 to F4 unchanged, "Ghip" the color commentator in the banter. Audio only: nothing needs sight or a mouse.
- NX-R8 Sounds. Reuse the original's 26 wavs (the whistle, the bleeps, the crowd, the kick and the tackle sounds). A new sound exists only as a generated tone under playbook 7.8 (owner listening round, SOUND_DESIGN.md updated). Nothing is recorded or taken from another game.

## 2. The request and how each line is read

The owner's words, 2026-10-14: add timeouts according to NFL rules; add replay challenges following NFL challenge rules; add QB keepers according to NFL rules; add onside kicks according to NFL rules; add playbooks from something like Madden football as optional uses (research current 2026 Madden NFL playbook guides and implement them in the style of Jim Kitchen's game); add something like Franchise mode (a Madden feature: research, then implement it in the style and gameplay of this clone); add penalties with the ability to accept or decline them according to NFL rules.

Readings (each is an accepted default under rule 0.8, recorded in D-040, and can be changed by the owner at any time):
- NX1 Timeouts: the NFL timeout rules for both teams, with a real game clock behind them (section 3, C2).
- NX2 Replay challenges: the coach's challenge and the replay official's reviews of the NFL, under the name "challenge" in menus so that it is never confused with the game's own F2 "instant replay" of the last play's speech.
- NX3 QB keepers: designed quarterback runs ("keeper", "sneak", "draw", bootleg and the scramble that ends in a run), with the NFL rules for a quarterback who is a runner (the slide, protection of a sliding runner, and the passer rules while he still throws). This is the reading to confirm (NQ1): the term has no single NFL rule of its own.
- NX4 Onside kicks: the kicking team's onside kick with the current NFL declaration, alignment, kick and recovery rules, for the player and for the computer.
- NX5 Playbooks: selectable playbooks in the manner of the team playbooks of Madden NFL 27 (current in 2026), "Classic" (the original's plays) being the default and always available.
- NX6 Franchise mode: a multi-season career in the manner of Madden's Franchise, adapted to this game: a persistent league, player ratings, progression, draft, free agency and salary cap, trades, injuries, staff, goals and history, all spoken.
- NX7 Penalties: NFL fouls with their enforcement, and for the offended team the choice to accept or decline, spoken with the consequence of each choice; the computer decides by rule.

## 3. Cross-cutting requirements

- C1 Switches. Under "Rules" in the F9 menu: one on/off per feature NX1 to NX4 and NX7, the playbook choice (NX5), and "Franchise" as a game mode chosen when a new season starts (NX6). Settings are kept in the settings file. A saved game remembers its own mode and state: football.sav gets a marked extra section in the manner of D-027 item 3 (a version value, then the extras' values); a classic save loads in any mode with the extras at their start values; an extras save never loads wrongly into Classic (it asks the player once, spoken).
- C2 The clock. The original has no clock: a quarter is a number of counted plays and F4 invents a time (GAME_SPEC 5.3, 5.6). Timeouts, the two-minute warning, challenge limits, onside kicks late in the game and penalty runoffs need real time. In N. F. L. rules mode a quarter is 15 minutes of game clock. Every play costs seconds by the NFL clock rules (the clock stops on an incomplete pass, a score, a change of possession's whistle, a penalty, a timeout and so on; it runs after a first down; verify all in SX.0), and F4 speaks the real time. Calibration: over 10,000 simulated quarters the average number of counted plays per quarter stays within the original's range (29 to 36 by 5.6 item 5) and each quarter ends when the clock reaches zero. The original's count clock remains for Classic. The computer's choices that read "plays left in the period" (5.7 items a and c) read "time left" in N. F. L. rules mode through the same hook (H1). Accepted default (NQ3); the owner may veto.
- C3 Neutral equals classic. Where a feature changes probabilities (ratings, playbooks, penalties' frequency), the neutral setting (all ratings average, playbook Classic, penalties off) gives exactly the original's tables of 5.7 to 5.10.
- C4 Random draws. All new draws use the one `GameRandom` with its bounded redraws (G-D1); each new draw is documented like the original's (range, order, redraw rule) in the design file; tests use the strict scripted source. In Classic mode the extras consume no random number at all.
- C5 Speech texts. New spoken sentences are listed with an ID and exact spelling in `spec\STRINGS_NX.md` (written by SX.1; a generator, never typed by hand, D-017). Pools of remarks (penalty announcements, review announcements, timeout remarks, onside remarks, keeper remarks, the franchise's news lines) are customizable commentary under CLAUDE.md 0.12 and playbook 7.9: permanent IDs, the player can change, switch off or add lines of own text or own sounds, with the file unchanged the defaults speak as written. The inventory is added to `spec\CUSTOMIZABLE_CONTENT.md` as section 13 (SX.1).
- C6 Help. F5, F6 and F7 (special keys, game instructions, football terminology and hints) are the original's strings. In N. F. L. rules mode each gets one added, separate section after the original text (written with the feature, listed in STRINGS_NX.md); the original text is never changed. Penalty names, timeout, challenge, onside kick, keeper, playbook and the franchise terms are explained in the F7 addition.
- C7 Statistics. The quarter statistics (4.19) keep their sentences. In N. F. L. rules mode, added lines (spoken after the original ones): penalties and penalty yards of each side, timeouts used, challenges won and lost, onside kicks tried and recovered, the quarterback's runs and yards (also counted in running plays and running yards, as in the NFL).
- C8 Tests (CLAUDE.md 1: run before saying it works). Each feature has: rule tests against `nfl_rules_<year>` (the numbers), scripted-random flow tests with the exact spoken order, property tests of the NFL invariants (never more than 3 timeouts per half, never more than 3 challenges per game, a penalty is never enforced beyond half the distance to the goal, and so on), and a Classic golden test: a full seeded game with the extras code present and switched off gives the same spoken and sound transcript and the same sequence of random draws as before the extras existed (the golden file is recorded by S7.3b and S7.3c, before any extra is built).
- C9 Accessibility. Every decision point speaks what is being asked, the choices, and the current answer; Up and Down or Tab change it, a letter key sets it, Enter takes it, F1 repeats the situation (position, down, clock, timeouts) as now; a wrong key is echoed as in the original; nothing happens on a timer without a spoken warning; no prompt waits for sight. The accept-or-decline prompt and the challenge prompt speak the result of each choice before the answer is taken (NX7, NX2).
- C10 Robustness. A damaged or missing extras file is repaired from the defaults with a spoken notice (playbook 7.10); the extras never end the program; Save Game works at every wait where it works now and, in N. F. L. rules mode, also while a decision is pending (the pending decision is saved).

## 4. What the original has and lacks (GAME_SPEC 1.2, for the builder)

- Plays: offense Line Plunge, End Run, Screen Pass, Short Pass, Long Pass, Field Goal, Punt, Save Game; defense Goal Line, Short Run, Long Run, Blitz, Short Pass, Long Pass, Save Game (4.15). A 5-by-6 matrix of outcomes (5.9). The computer chooses by 5.7.
- No clock (a counted-play clock, 5.3, 5.6), no timeouts, no penalties, no replay or challenge, no onside or squib kick (5.10: one kind of kick-off), no quarterback run, no player ratings (the 33 names per team are surnames only, 5.5), no persistent league (the season is 16 weeks and the play-offs, 5.14 to 5.17; at the season's end the clone starts a new season, D-029).
- The two-minute warning exists (5.6 items 4 and 5, from the play counter). Overtime is sudden death with periods (5.6 items 6 and 7).
- The key model: F1 position and down, F2 instant replay, F3 score, F4 clock, F5 to F7 help, F8 comments, F9 the clone's added menu, F11 volumes, F12 voice (8.1, 17.4).

## 5. Hooks the classic engine must leave (sessions S7.3b, S7.3c, S7.4, S7.5, S7.7)

The classic engine is built first and exact. So that the extras do not force a rewrite, these seams are built into it, with no change to what Classic does (the golden file of C8 proves it). Each hook is a plain function or data list that Classic fills with the original's behavior.

- H1 One period-clock interface: "plays left", "last play of the period", "end of the period", "two-minute warning due", "speak the clock". Classic answers from the play counter (5.3, 5.6); N. F. L. rules mode answers from seconds. Every place of 5.6 and 5.7 that reads the counter reads it through this interface.
- H2 A play is three steps: choose (menus and 5.7), resolve (5.8 to 5.10 produce one `PlayOutcome` record: yards, kind, spoken sentences and sounds in order, turnover, score, flags) and apply (5.11 and 5.12: position, downs, possession, score). Between resolve and apply there is one hook, `after_outcome(outcome)`, where penalties and challenges may change or hold the outcome. Classic returns it unchanged. The original's order of speech and sound inside a play is kept by the record.
- H3 The offense menu and the defense menu are data lists (item text, key, action), built by one function that the extras (more items, a playbook) can replace. Classic is the exact lists of 4.15, including Save Game's number.
- H4 The kick-off is one function with a `kind` argument (Classic: normal) and the return or recovery step replaceable (onside).
- H5 The game state is one record with an `extras` slot that is empty in Classic; Save Game and loading write and read that slot after the original's values (C1).
- H6 One `Rules` object (Classic = all off) is passed through the engine; the engine calls hook functions that Classic leaves as no-ops, and never tests feature flags itself in the middle of 5.7 to 5.12.
- H7 Rosters stay slot-based (the 33 names of 5.5 and the quarterback) with an empty per-slot `rating` that Classic never reads (franchise, NX6).
- H8 The outcome tables of 5.9 and 5.10 are data (minimum, maximum, sack percent, completion percent, interception rule, fumble chance), read through one `modifiers` argument that Classic passes as neutral (playbooks, ratings, QB keepers).
- H9 Speech and pause helpers (say to say6, dy, rady) are used as they are; extras add only new lines through them.

S7.3b and S7.3c record the golden Classic transcript (C8) and say in their NEXT_PROMPT which hooks they built.

## 6. NX1 Timeouts (according to NFL rules)

Rule outline for SX.0 to verify:
- Each team has three timeouts in each half; unused first-half timeouts do not carry into the second half. [UNVERIFIED; SRC-SECONDARY: the NFL operations article "How do NFL coaches use their timeouts?" says three per half]
- Overtime: regular season two timeouts per team; the postseason figure is not settled by the sources found (one says three). [SRC-SECONDARY, conflicting; verify. The clone's overtime stays sudden death by default, NQ4.]
- A team may call a timeout when the ball is dead, before the snap, whether it is on offense or defense. The clock stops; a timeout used with the clock running saves the time that would run. [UNVERIFIED]
- A request when the team has no timeout left is a foul (delay of game, with the five-yard penalty and, late in a half, possibly a runoff). [UNVERIFIED: verify]
- The two-minute warning is an automatic stoppage at 2:00 in the second and fourth quarters and is not a timeout. [SRC-SECONDARY]
- A timeout restored by a successful challenge (NX2) and the rule about timeouts after a replay review inside the last two minutes (casebook) are handled with NX2. [SRC-SECONDARY]

Requirements:
- N1.1 The state has the timeouts left of each team for each half and period. They are spoken at the start of each half and on F1 in N. F. L. rules mode ("you have two timeouts left").
- N1.2 The player calls a timeout from the offense menu or the defense menu (an added item and the letter key T) and at no other time; a timeout the player has none of is refused with a spoken sentence (whether a request without a timeout left is a foul is decided with NX7's list, section 12).
- N1.3 The computer uses timeouts by rules from published practice (SX.0 reads the NFL operations article on how coaches use timeouts and records the rules used): trailing late in a half, on defense to stop a running clock when it needs the ball back, on offense to save time before a score, never late-wasted before the two-minute warning when it leads, and to keep at least one for a challenge in the first three quarters (NX2).
- N1.4 The sounds and sentences: the whistle wav and the original's bleep for the stop, an announcer sentence ("Time out called by the <team>, <n> left"), a customizable remark pool (C5).
- N1.5 The clock effects of C2: the clock stops and restarts correctly; F4 speaks the real time.
- Done when: the rule tests and property tests of C8 pass, a seeded 10,000-quarter run never breaks a limit, the computer's use of timeouts is shown by a scripted end-of-half test (trailing team with timeouts uses them in the NFL way), and the Classic golden test passes.

## 7. NX2 Replay challenges (following NFL challenge rules)

Rule outline for SX.0 to verify:
- Each coach has two challenges per game; each challenge needs a timeout in hand; a successful challenge restores the timeout. [SRC-SECONDARY; the older text says a team that wins BOTH challenges gets a third; later sources say at least one success earns a third (a 2024 amendment); verify which is current in 2026. A fourth is never allowed.]
- No coach's challenge after the two-minute warning of each half, in overtime, after the challenging team committed a foul that delays the next snap, or when the team has no challenge or no timeout. [SRC-SECONDARY (an older rule text)]
- The replay official (the booth) reviews all scoring plays and turnovers automatically, and any play in the last two minutes of each half and in overtime, with no timeout charged and independent of the timeouts left. [SRC-SECONDARY]
- A challenge when not allowed costs a timeout, or a 15-yard foul when the team has none. [SRC-SECONDARY (older text); verify]
- Reviewable and non-reviewable plays (catch or no catch, fumble or down by contact, out of bounds, the goal line, the line to gain only in limited ways, and never judgment fouls). [UNVERIFIED; SX.0 reads the current rulebook and casebook.]
- 2026 changes found: none for challenges or timeouts. [SRC-SECONDARY: CBS Sports and team sites on the 2026 approved changes]

Requirements:
- N2.1 The ruling model. The simulation has no video, so some plays get an initial "ruling on the field" that is wrong with a small, tunable probability by category (a completion ruled incomplete or the reverse, a runner ruled down before a fumble, a runner ruled short of or over the goal line, a catch ruled in or out of bounds). The frequency, categories and the chance that the replay shows the error as clear and obvious are in a data table with their sources (SX.0 and the design session set them from published NFL replay statistics and record how). A wrong ruling is not hidden: it is the thing that a challenge or a booth review can reverse.
- N2.2 The player hears the ruling, a short color remark from the announcer that hints at how close it looked (in the manner of Ghip's remarks; customizable pool), and has the challenge key (the letter C and an added menu item) only while a challenge is allowed by the rules (section outline above). The prompt speaks the cost ("a timeout will be used and is given back if the call is reversed; you have <n> challenges and <n> timeouts").
- N2.3 The review: the announcer says the referee is going under the hood (a pause drawn in the original's manner with dy), then "the ruling on the field is confirmed" or "reversed" with the new result applied through H2. The outcome and the next sentences follow from the reversed result as they would from the play had it been called right.
- N2.4 Booth reviews (scoring plays, turnovers, the last two minutes, overtime): spoken as "the replay official has stopped the game to review"; no cost; the same reversal logic.
- N2.5 The computer coach challenges by rule of thumb that SX.0 records (a clear loss from the call, a significant situation, a challenge and a timeout in hand, the game's phase), sometimes wrongly, so it can lose a timeout and a challenge.
- N2.6 A challenge never reaches the original's F2 "instant replay" (the replay of the speech lines of the last play stays as it is and is named in the menus only as instant replay).
- Done when: the rule tests cover every limit above in the current wording, a scripted game shows a won challenge (timeout restored, result reversed), a lost challenge (timeout gone, ruling stands), a refused challenge (not allowed) and a booth review, and the Classic golden test passes.

## 8. NX3 QB keepers (according to NFL rules)

Reading (NQ1): designed quarterback runs and the NFL's treatment of a quarterback who runs.

Rule outline for SX.0 to verify:
- A quarterback who tucks the ball and runs is a runner (his rushes and yards count as rushing); while he is in the act of passing the passer protections apply. [UNVERIFIED]
- A runner who slides feet first is down at the spot of the slide and may not be hit; contact then is a foul (unnecessary roughness). [UNVERIFIED; verify the current article]
- Intentional grounding outside the tackle box and the scramble rules for a passer who leaves the pocket. [UNVERIFIED]
- The quarterback sneak: the NFL's decision on the "push" (the "tush push") in 2025 was to keep it legal; check 2026. [SRC-SECONDARY (2025 article titled "Tush push survives"); verify 2026 status]
- Fumble and injury exposure of a running quarterback (the original has no injuries; NX6 may add them).

Requirements:
- N3.1 New offense plays, each a named play with an outcome row against the six defense calls (data, H8): QB Sneak (short yardage, high success, tiny fumble chance, the right play on third and fourth and short), QB Keeper (a bootleg or naked keeper to the outside, medium yards, a sack-like loss chance), QB Draw (a pass look that becomes a run, strong against a blitz, weak against a short run defense), and the Scramble (a called pass play that, instead of the incompletion or the sack, ends with the quarterback running; it extends the original's drop-back sentences "scrambles left looking for a receiver" and "is forced out of the pocket", which today lead to ordinary pass results). The tables are SX.1's design, calibrated from NFL quarterback rushing statistics (average yards per quarterback rush by down and distance), sources recorded.
- N3.2 The slide: when a keeper gains a first down or is near the sideline or the goal line, a slide may be chosen by the quarterback (an automatic rule for the computer; for the player a quarterback who runs the play slides when the situation says so, announced, never a prompt in the middle of a play).
- N3.3 Statistics: the keeper counts as a running play and its yards as running yards, plus its own line in the added statistics (C7); a fumble counts as a fumble lost when lost.
- N3.4 Sentences in the manner of 5.9 ("<quarterback> keeps the ball and runs around the right end", "the quarterback sneak is good for a first down"), a new phrase family with the original's "never repeat one of the last N" rule, customizable (C5).
- N3.5 The computer chooses keepers (short-yardage sneaks, late-game scrambles when trailing, rarely otherwise) by rules in its design file; the defense calls against a keeper follow 5.7's matching logic extended to the new plays.
- Done when: the table values and the rule tests pass, every slide case is tested, a seeded long run's statistics are inside the NFL ranges the design file names, and the Classic golden test passes.

## 9. NX4 Onside kicks (according to NFL rules)

Rule outline for SX.0 to verify:
- 2024: the dynamic kickoff; an onside kick had to be declared to the officials in advance and only a team trailing in the fourth quarter could attempt it. [SRC-SECONDARY]
- 2025: the kicking team may declare an onside kick in any quarter; the team declaring must be trailing; the kick is taken from the 34-yard line; changes to the alignment of the kicking line. [SRC-SECONDARY; one report only on the alignment]
- 2026 (approved in the spring of 2026): "to permit the kicking team to declare an onside kick at any time during the game". Whether the trailing condition still holds is not settled by the page found. [SRC-SECONDARY: the Steelers' page of the league's approved changes; CBS Sports]
- Other 2026 kickoff changes: no incentive to kick out of bounds from the 50; new alignment of the receiving team in the setup zone. [SRC-SECONDARY]
- Recovery rules (the ball must travel ten yards unless touched by the receiving team; the kicking team may not touch it first; the receiving team gets the ball at the spot where the foul or the touch happens) and the penalties for an illegal onside kick. [UNVERIFIED]
- After a safety the conceding team kicks a free kick, and an onside kick is possible on it under the same rule. [UNVERIFIED]
- Recovery rate: about 6.45 percent in 2024 (only three successful), the 2025 and 2026 figures are for SX.0 to find. [SRC-SECONDARY]

Requirements:
- N4.1 At every kick-off the player's team makes (opening, second half, after a score, after a safety, overtime) in N. F. L. rules mode, when the NFL rule of the current table allows an onside kick, a yes-or-no question in the style of 4.16: "<coach> do you wish to try an onside kick" with the answer starting at no. When the rule does not allow it the question is not asked. Classic: never asked.
- N4.2 The kick: a short kick sentence sequence in the manner of 5.10 (the setup, the kick, the scramble for the ball), with the original's kick sounds, and one outcome draw with the recovery chance from the rules table (kept as data with its source and year, N4.4): recovered by the kicking team at a spot, or the receiving team gets it at a spot drawn as a short distance from the kick spot (and a rare long return for the receiving team).
- N4.3 Penalties on the kick (offside, illegal touching, illegal alignment) use NX7's machinery if NX7 is on; if not, they are not simulated.
- N4.4 The computer: declares onside kicks by a rule table (trailing late in the fourth quarter and the time left, a larger deficit earlier only when the 2026 rule allows and the situation is desperate; with the 2026 wording, a surprise onside kick when leading is a rare data-driven choice only if SX.0 finds that it is allowed). The recovery probability and the decision thresholds are data with their reason.
- N4.5 Statistics: onside kicks tried and recovered (C7).
- Done when: the rule tests match the 2026 wording SX.0 records, a scripted game shows the player declining, the player kicking and recovering, the player kicking and losing, and the computer kicking, and the Classic golden test passes.

## 10. NX5 Playbooks (optional, from Madden NFL's playbook idea)

Facts found so far (SRC-SECONDARY, 2026-10-14): Madden NFL 27 is the current game (released 2026-08-13; deluxe edition early access from 2026-08-10). EA's help page "Madden Playbooks Guide" says every NFL team has a unique playbook that reflects its real strategies and style; playbooks are customizable in some modes, including Franchise; custom offense and defense playbooks can be built in the Creation Center; fan guides list all 32 team playbooks plus a few custom ones. New in Madden 27: short-yardage mechanics, coverage improvements, pre-play strategic settings.

Requirements:
- N5.1 Research (SX.0, then deepened in SX.1): read EA's Madden NFL 27 playbook guide and current 2026 playbook guides, and write `spec\MADDEN_PLAYBOOK_RESEARCH.md` with sources: how Madden organizes a playbook (formation sets, concept groups, offensive and defensive schemes: West Coast, Air Raid, Spread, Pro Style, Power Run, Option; 4-3, 3-4, Nickel, Tampa 2, Cover 3, man press and similar), the list of team playbooks, and which of their concepts are plain football terms (usable) and which are EA's own naming (not used, NX-R6).
- N5.2 Mapping. Each playbook play is a named, spoken play that maps to a base family of the original's tables (inside run, outside run, screen, short pass, long pass, and the keeper family of NX3) with a bounded `modifiers` set (H8) such as yards range shifted by a few yards, completion percent plus or minus a few points, sack and interception odds, fumble chance. Rules: at "Classic" every play and modifier is the original's; no modifier can make a play better than the best play of the same family in every situation (balance test: each play has a stated strength and a stated weakness against the defense calls); all numbers are data in the playbook files, not code.
- N5.3 Defense. Playbooks also carry defensive schemes: a set of defense calls (named like the original's six plus scheme calls) that map to the original's six defense families with modifiers in the same way.
- N5.4 Selection. The player chooses his playbook in the F9 menu or before a game ("Playbook: Classic" is the default and is always first); the 32 teams each have an assigned playbook (the closest style to their Madden 27 team book, recorded in the research file) used by the computer, and the player may take any of them for his own team. A chosen playbook is remembered per season (and per franchise, NX6).
- N5.5 Menus. No menu longer than 12 items; a two-level menu (a group such as "runs", "short passes", "deep passes", "play action", "special", then the play) is used when a playbook has more; each item spoken in six words or fewer; the digits, Up, Down, Enter and letter keys work as in 4.15; F1 to F4 unchanged. Plays are described in F7's added help text.
- N5.6 The computer's play choice for a non-Classic playbook is a weighted draw over its plays by down, distance, field position and score, in the structure of 5.7 (the original's rules are the Classic playbook's weights).
- N5.7 Customization: playbooks are text data files in the `customize` folder with permanent IDs; the player can disable a play, rename a play and edit the modifiers within their bounds (7.9).
- Done when: SX.1 has accepted the research file and the mapping, every playbook passes the balance test over a seeded 10,000-game simulation (no playbook wins more than the range the design file sets against Classic), and the Classic golden test passes.

## 11. NX6 Franchise mode (in the manner of Madden's Franchise)

Facts found so far (SRC-SECONDARY): Madden NFL 27 describes a new "Persona Engine" that gives every athlete a personality, and Franchise carries a live-beta note on EA's pages. The remaining feature list is for SX.0 to read from EA's own pages and the current 2026 guides.

Research and adaptation (SX.0 and SX.8): write `spec\MADDEN_FRANCHISE_RESEARCH.md` listing Madden's Franchise features with sources and, for each, one of ADOPT (adapted to this game), LATER, or SKIP with the reason. Candidates to read and judge (the list is the search's starting point, not a decision): the stages of the year (preseason, regular season, play-offs, the offseason with re-signing, the combine and scouting, free agency, the draft, roster cuts); the roster with ratings, positions, age, potential and development; contracts and the salary cap; free agency; trades; progression and regression, retirement; injuries; coaching and staff and their schemes; owner or job-security goals; player personality and morale; league history (records, awards, a hall of fame); computer teams managing themselves; the schedule.

Requirements (the shape; the content is decided in SX.8 from the research):
- N6.1 Franchise is a game mode chosen when a new season starts: "Classic season" (the original's) or "Franchise". The Classic season is untouched. Franchise uses its own save file in the data folder.
- N6.2 Continuity. The league persists from season to season: 32 teams, their players, the coach (the player), standings history, records. The original's play-off and Super Bowl engine (5.14 to 5.17) is reused; its sentences stay.
- N6.3 Ratings. Each roster slot (the 33 named players of 5.5 and the quarterback, for both sides, and the computer teams' units) gets a rating, from an average neutral value. Ratings change the outcome tables only through bounded `modifiers` (H8): at a neutral rating the engine equals Classic (C3). The computer teams' season results (the original's score table, 5.14) are shaped by the team strength in the same bounded way.
- N6.4 Progression: each offseason players develop, hold or decline by age and potential; retirement; the roster stays at its slot counts.
- N6.5 Draft: seven rounds in an order from the previous season's standings, spoken one pick at a time with a short list the coach chooses from; drafted rookies take names from the surname pool (the pool of 1,708 is shared; duplicates are allowed by design, decided in SX.8) or the player's own surname file.
- N6.6 Free agency, contracts and salary cap: a spoken, numbered flow with a clear running summary (cap space), adapted for audio.
- N6.7 Trades: the player proposes, the computer answers by a value rule.
- N6.8 Injuries, staff and goals: at least injuries with games missed, a coordinator or staff effect that picks the scheme (NX5), and a season goal with a spoken verdict.
- N6.9 History: a spoken history menu (records, champions by year, the coach's record).
- N6.10 Everything is spoken, short and numbered, with F1 to F4 and F9 as elsewhere; long lists are paged (nine items) with the same keys.
- N6.11 The minimum franchise before the Windows release: N6.1 to N6.5 and N6.9, then N6.6, N6.7, N6.8 in the order SX.8 decides; the target is all of N6. The owner may cut the later items.
- Done when: SX.8's design is accepted, a seeded multi-season simulation (20 seasons, no player input) keeps the league healthy (rosters full, the cap respected, ratings in range, no team starved), neutral ratings reproduce Classic's outcomes, and the Classic golden test passes.

## 12. NX7 Penalties (accept or decline, according to NFL rules)

Rule outline for SX.0 to verify (the NFL penalty list is long; the clone starts with the common ones, the list is data and can grow):
- The offended team's captain or coach chooses to accept or decline each foul; accepting enforces the foul's yardage from its basic spot, declining keeps the result of the play. [SRC-SECONDARY: explainers; the NFL rulebook is the authority]
- Consequences of acceptance, by foul: yards, automatic first down, loss of down, replay of the down, spot of the foul or previous spot, the half-the-distance-to-the-goal rule, dead-ball versus live-ball fouls, offsetting fouls. [UNVERIFIED]
- The runoff rules and clock effects of a penalty late in a half (the 10-second runoff, the clock at five minutes in the fourth quarter and overtime). [UNVERIFIED; SRC-SECONDARY mentions fourth-quarter timing rules]
- The list to start from: false start, offside, neutral zone infraction, encroachment, delay of game, illegal formation, offensive and defensive holding, illegal use of hands, face mask, pass interference (offense and defense), illegal contact, roughing the passer, roughing the kicker, unnecessary roughness, unsportsmanlike conduct, intentional grounding, illegal block in the back, ineligible receiver downfield, illegal forward pass. [UNVERIFIED]

Requirements:
- N7.1 The foul table is data, with a permanent ID per foul: name, spoken text, who commits it, the phases it can happen in (before the snap, run, pass, kick), yards, automatic first down, loss of down, enforcement spot, whether the down is replayed, and its base chance per play type. Frequencies are calibrated to NFL accepted-penalty averages per game and per team (SX.0 records the sources and the average per play), with the quarter's feel of the original kept (a few flags per half, not a flag-fest).
- N7.2 When: pre-snap fouls (the play is not run), fouls during a run, a pass or a kick (the play is run and spoken as now, then the foul is announced at H2's hook). The announcer says what was flagged, on whom, with the player's surname from the roster ("a flag on the play, holding on the offense, <surname>"), then the choice.
- N7.3 The choice. When the player's team is the offended team: the prompt (in the style of 4.16 and 4.17) speaks the foul and the two outcomes in full ("if you accept: first and 10 on your 35; if you decline: second and 7 on your 42") and asks accept or decline, the answer starting at the better outcome by the computer's own rule, so a wrong key or Enter never hurts; Up, Down, a (accept), d (decline), Enter, F1 repeats the prompt with the situation. When the opponent is the offended team: the computer decides by rule (accept when the enforced outcome is better by its measure of down, distance, field position, clock and score; decline otherwise) and the announcer says what the opponent coach does. Both fouls by both teams on one play: offsetting, replay the down.
- N7.4 Enforcement is exact for the foul table: the half-distance rule, the spot, automatic first down, loss of down, replay, the touchdown and safety edge cases (a foul in the end zone), the interaction with a score, a turnover and a kick (a penalty on a kick-off or a punt, the two-point try, overtime).
- N7.5 Customization: the foul table's spoken texts and the on/off and weight of each foul are in `penalties.txt` in the `customize` folder (C5, 7.9).
- N7.6 Interactions are listed and tested: timeouts (NX1: delay-of-game foul), challenges (NX2: a foul is never reviewable, a foul can be hidden by a reversal), keepers (NX3: the slide and roughing), onside kicks (NX4), the clock (C2: runoff and clock restarts).
- Done when: every foul in the table has an enforcement test against the rule table, the offsetting and half-distance cases are tested, a scripted game shows the player accepting, declining, and being the fouling team, the frequency check over 10,000 simulated games falls inside the NFL averages the design file names, and the Classic golden test passes.

## 13. Optional companions (not requested; built only if the owner says yes)

Spike and kneel-down plays for the clock, a modern overtime, injuries outside Franchise, a "two-minute drill" help text. Ask once when SX.1 is accepted.

## 14. Delivery plan, sessions and the release gate

A new phase PX sits between P7 and P8 (CLAUDE.md 3, nfl4 only). It starts when S7.7 is done. The classic engine and its golden transcript come first (S7.3b to S7.7); the extras are added on the hooks of section 5.

- SX.0 Research (read-only, can run in parallel with S7.3b in its own session, writes only new files): `spec\NFL_RULES_RESEARCH.md` (every rule above made SRC-OFFICIAL from the current NFL rulebook, casebook, operations site and the 2026 approved changes, with page and date; NFL statistics for penalties, quarterback rushing, onside recovery, replay reversals), `spec\MADDEN_PLAYBOOK_RESEARCH.md` and `spec\MADDEN_FRANCHISE_RESEARCH.md` (sources: EA's help pages and current 2026 guides). Sonnet 5.5, medium; independent subagents per topic are fine (CLAUDE.md 1).
- SX.1 Design (all features, one file `spec\NFL_EXTRAS_DESIGN.md`): the clock model (C2), the rules table, states, menus and keys, every new draw, STRINGS_NX.md, CUSTOMIZABLE_CONTENT section 13, the save format, the order of building; owner choices NQ1 to NQ6 asked once, one at a time with recommended answers, or accepted by default. GAME_SPEC version 1.3 if the design changes a requirement. Opus 5.5, high.
- SX.2 Clock, timeouts and the two-minute warning (NX1, C2). Sonnet 5.5, high; Opus 5.5 for the clock calibration.
- SX.3 Penalties with accept or decline (NX7). Opus 5.5, high (many interlocking enforcement cases).
- SX.4 Onside kicks (NX4). Sonnet 5.5, high.
- SX.5 QB keepers (NX3). Sonnet 5.5, high.
- SX.6 Replay challenges and booth reviews (NX2). Sonnet 5.5, high.
- SX.7 Playbooks (NX5): the file format, two or three playbooks first, then the rest; the computer's choices. Sonnet 5.5, high (may be split).
- SX.8 Franchise design from the research (NX6) then SX.8a to SX.8f: the persistent league, ratings and progression, the draft, free agency and the cap, trades, injuries, staff and goals, history. Opus 5.5, high for the design, Sonnet 5.5, high for the building (several sessions).
- SX.9 Integration: all switches on and off in every combination that matters, the multi-season simulation, the stress tests of 8.3 with the extras, the owner's playtest list (what only ears can judge), README and About text (NX-R6 notice). Opus 5.5 or Sonnet 5.5, high.
- Release gate (NX-R3): P9 compile does not start until SX.9 passes, unless the owner says to release Classic first.
- Each session follows the usual rules: read CLAUDE.md and this file, answer open questions, add lessons to `fixesforgames.md`, update PROJECT_STATE.md and SESSION_LOG.md, end with the Next Session block (3.3), commit.

## 15. Open questions (accepted defaults until the owner says otherwise; also in D-040)

- NQ1 QB keepers: the reading of section 8. If the owner meant something else, the section changes.
- NQ2 Default of the "Rules" setting for a new player after the extras are finished and tested: recommended "N. F. L. rules" (the owner asked for the features); Classic stays one setting away and is what the conformance tests use. Until then Classic is the only mode.
- NQ3 The real clock of C2 in N. F. L. rules mode, calibrated to the original's number of plays per quarter. The alternative (timeouts as play credits in the count clock) is rejected because it cannot honor the two-minute and challenge rules.
- NQ4 Overtime: the clone keeps the original's sudden death (5.6 item 6) in both modes. Modern NFL overtime is not requested.
- NQ5 Playbook scope: a handful of style playbooks plus an assignment of each of the 32 teams to the closest style, in N5.4; the full 32 separate team books only if SX.1 finds the research supports it at a reasonable size.
- NQ6 Franchise scope: N6.11's minimum first, the rest in the order of SX.8, all of N6 as the target.
- NQ7 The F9 menu key map and the exact menu item numbers: SX.1 decides, under C9 and NX-R7.

## 16. Sources (fetched or searched 2026-10-14, all SRC-SECONDARY until SX.0 replaces them)

- NFL 2026 approved rule changes (Pittsburgh Steelers' site, the league's text): https://www.steelers.com/news/nfl-owners-approve-2026-nfl-rule-changes
- CBS Sports, 2026 rule changes: https://www.cbssports.com/nfl/news/nfl-rule-changes-2026
- 2025 onside-kick change: https://steelersdepot.com/2025/05/nfl-passes-onside-kick-rule-change-proposal and https://www.cbssports.com/nfl/news/five-new-nfl-rules-to-know-heading-into-week-1-of-preseason-here-are-the-biggest-changes-for-2025
- NFL overtime rules (NFL Football Operations): https://operations.nfl.com/the-rules/nfl-overtime-rules
- How NFL coaches use their timeouts (NFL Football Operations): https://operations.nfl.com/gameday/analytics/stats-articles/how-do-nfl-coaches-use-their-timeouts
- NFL challenge rules: https://amp.foxsports.com/stories/nfl/nfl-challenge-rules-how-many-challenges-does-each-team-get and the replay review article https://en.wikipedia.org/wiki/Replay_review_in_gridiron_football
- Madden NFL 27 playbooks (EA help): https://help.ea.com/fi/articles/madden-nfl/madden-playbooks-guide/ ; release and features: https://clutchpoints.com/gaming/madden-27-release-date and https://gamingbolt.com/madden-nfl-27-20-biggest-features-you-may-not-know
- The NFL rulebook, casebook and the Madden Franchise guides themselves: SX.0 reads and records them.

## 17. History

- 0.1 (2026-10-14): written on the owner's request before S7.3b (D-040); GAME_SPEC 1.2 points here; CLAUDE.md rule 0.13 and its pointers added.
