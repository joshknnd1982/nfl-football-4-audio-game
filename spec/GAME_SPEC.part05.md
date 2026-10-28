## 15. Errors, edge cases and quirks of the original (list; decisions in DECISIONS.md D-022 to D-031)
Q1 The program plays one game per run: after the game it says thank you and ends (section 3 step 8; D-024: the game returns to the menu; Save Game still ends the program).
Q2 After the schedule or the standings (menu choices 2 and 3) the week line and today's game are spoken again before the menu (kept, it is what the player hears).
Q3 The very first division game cannot be in week 1 or 2 (`last` starts at 0); no other rule against it (kept; invisible).
Q4 Standings order uses the losses only; equal losses keep the team order (kept, the player hears it).
Q5 F1 in the play-off main menu repeats the week name without "This is the" and, in the regular season, repeats no week line (not reproduced: the game repeats the whole announcement, D-025).
Q6 F4 at play counter 0 with `oldtime` still Empty or 0 skips the time calculation; S3.4 showed the counter is 1 at the start of a game, so this happens only at the start of an overtime period when F4 was never pressed during the game (" remaining in the over time quarter." without a time) or was last pressed at counter 0 (that time is repeated); a clock at the very end of a quarter can give no seconds (the first is not reproduced, the game speaks the start-of-period time; the second is kept, D-025; Q-028 answered).
Q7 Missing files at the week loop: football.gtp, footbal2.dat (and footbal4.dat in the play-offs) are opened for reading without a check. CORRECTED in S3.6 (runtime evidence, section 12): For Binary Access Read CREATES a missing file empty, so the original does not end with run-time error 53 (as S3.3 had inferred); the reads leave the variables as they were (at a start Empty, which counts as 0), so it goes on with week 0 or the last opponent; damaged files give wrong values silently (not reproduced: the game repairs or restarts the season, D-024 item 5, tests in S8.3).
Q8 footplay.txt: pag reads it with Input #; any heading that differs from the expected one, a line that is missing or a name with a comma makes pag throw the whole file away and draw all names again (the player's edits are lost silently); the game keeps the format but repairs only the broken part and tells the player (7.10, D-025). S3.5 (Q36): the original does not even survive most of these cases (run-time error 9 or 62).
Q9 The quarterback of the player is the LAST item of footplay.txt; a typed name has leading spaces cut when it is read back (Input #); the name of the opponent quarterback is asked every game and is not stored (kept).
Q10 The surname pool has two stray characters in the data ("Jones" followed by a quote mark, "Maddox" followed by a closing parenthesis), 50 spaced or phonetic spellings, two Latin-1 letters (Martínez, Márquez) (kept as data, D-026).
Q11 Settled in S3.4 (4.14): vtrnt = 1 means the player's team is at home; the visitor (the player when vtrnt = 2) calls the coin toss; the computer always receives when it wins the toss (kept).
Q12 MsgBox "Sorry but I couldn't find any voices to use / Please contact Jim Kitchen" when SAPI has no voice, then the exit (the game speaks it through the active speech backend and ends, D-022). (S5.2, audit findings A-04 and A-23: the original's exit from there skips the season-file deletion, foot0 and the thank-you and still reaches the game-menu check with its two Beeps, section 3 step 3; the game's rule is superseded by G-F9, D-031 item 6 and D-032 item 3: the game shows the same message box, with the contact line pointing to the repository, speaks it through a screen reader when one runs, then ends; no foot0, no thank-you, no beeps.)
The play engine (S3.4; decisions in D-027):
Q13 The code draws 30 to 37 plays per quarter and 5 to 7 after the two-minute warning; football.txt and the F6 instructions say 25 to 35 (kept: the code's numbers, and the help text unchanged).
Q14 Quarters 1, 2 and 4 last one counted play less than quarters 3 and overtime (the counter starts at 1 or 0) (kept, not noticeable).
Q15 In quarters 2 and 4 the computer always kicks on fourth down in its own half: its random "go for it" test compares with a variable that is never assigned (Empty = 0; `L718`, read in the asm at 0x43f840) (kept: it is how the opponent plays).
Q16 Two empty delay loops run 0 times (their bound is multiplied by the never-assigned `L258`; 0x44f0f2, 0x453392) (nothing to reproduce).
Q17 In the run-out question every key other than Enter, F1, y and n toggles the answer (kept).
Q18 In the extra-point choice F2, F3, F4 and any other key reset the choice to the kick; F1 and Esc have no meaning of their own there (kept).
Q19 A kick-off return counts as a first down in the statistics and is followed by " There is a gain of <n> yards on the play" (kept, it is spoken).
Q20 Sacks count as pass attempts and subtract from the passing yardage (kept).
Q21 The extra point never fails (kept).
Q22 A failed two-point try is not announced (the gain or loss sentence and then the score); during the try F1 speaks the down and distance of the touchdown play (kept).
Q23 A turnover during a two-point try leaves the try open: the other side's next play counts as the try (2 points for a touchdown, nothing otherwise) and then the first side receives a kick-off (not reproduced: the try ends with the turnover, no points, kick-off).
Q24 A safety in overtime does not end the game (not reproduced: every score ends overtime).
Q25 The overtime kick-off does not set the field half, so when the side that had the ball at the end of regulation was in the opponent's half, a returned kick-off is an automatic touchdown and a touch back puts the ball on the opponent's 20 (not reproduced: the half is set as at every kick-off; the receiving side, the side with the ball at the end, is kept).
Q26 "Stats After Quarter number" is one too high at the start of every overtime and after an overtime game (not reproduced).
Q27 After a Super Bowl game the Super Bowl presentation runs twice, before and after the final statistics (not reproduced: once, in place of the final score, then the statistics).
Q28 A loaded saved game draws M2W, M4W, M5W again, restarts the overtime count and the interception counts, and does not know which side received the opening kick-off, so the second-half kick-off can go to the wrong side (the kick-off side is not reproduced: the game stores it after the original fields of football.sav; the rest kept). (S5.2, audit finding A-19, the rule after a load, pag 0x43ae36, 0x444672 to 0x4446a9, 0x43d3cf: L8a8 is 1 at every game start, so the first kick-off after the load sets L158 to its receiving side; with no kick-off before half time L158 stays Empty and `If L158 <> 1` gives the second-half ball to the player's team. A football.sav of the original, which has no stored side, follows this rule in the game too, D-027 item 3.)
Q29 The interception chance grows with every pass a side throws (1 / (C - 3 x passes since its last interception, this one included), at most 1/2; with the long pass against the long pass defense it reaches 1/2 after 10 passes) (kept, a rule of the game).
Q30 After " is way to short" the log flag stays on (log only; the game's log rules apply).
Q31 After an interception or a fumble the ball is placed at a random yard line 5 to 44 in the same half as before the play (kept, a rule of the game).
Q32 The keypad digits do not choose in the play menus or the main menu (they type letters, D-022) (not reproduced: the game accepts them as digits).
Q33 The game start loads foot9 into the ambient buffer without playing it; Save Game leaves the crowds running until the program ends (nothing audible to reproduce).
The GoSub routines (S3.5; decisions in D-028):
Q34 The hand-off routine remembers the SENTENCE of the previous call (`L4a0 = L4f4`) where it means to remember the group number, so its "group different from last time" test compares a number with a text and never rejects (VB6 compares a Single Variant with a String Variant as "less", never equal; tested with the runtime's own comparison, `work/variant_cmp_check.py`); only at the very first call of a game, when L4a0 is Empty (= 0), group 0 is drawn again. The drop-back routine stores the group number and its test works (kept as the exact algorithm; the player cannot hear the difference, 5.9).
Q35 The fake texts of the hand-off sentence (" He fakes a hand off to <back> and then ", " He fakes a pass to <receiver> and then ", " He pump fakes a pass and then ") and of the drop-back sentence ("fakes a hand off and then", "fakes to <back> then") are never spoken: the hand-off phrase chain assigns the sentence instead of appending to it, and the drop-back's jump back starts the sentence over, so 27 of the 36 hand-off values and 22 of the 33 drop-back values give a plain phrase (kept as heard: the game does not speak them; the players L31c and L390 that would name them are not drawn).
Q36 A damaged footplay.txt: only a wrong FIRST heading is repaired silently (the file is rewritten); any later mismatch (a heading, a missing line, a name with a comma) happens after three or more names were read, and the rewrite then overflows the banter name list L480 (61 entries; the bound 0x3d is checked before all nine stores) and the original ends with run-time error 9 (subscript out of range); a file that ends early ends it with run-time error 62 (input past end of file). Not reproduced (D-025 d: the game repairs only the broken section and tells the player).
Q37 The history of the banter lines used and the phrase histories are not saved with a saved game: after loading, lines spoken before the save can come again (kept).
Q38 Banter line 113 is spoken one speech-rate step faster, but the +1 is lost whenever say has to load the announcer voice again (the last speaker had another voice number); the game always applies it, clamped to the top of its rate range (not reproduced, one line).
Q39 After a saved game is loaded the opponent's 33 players have new names (football.sav keeps no names; the set-up runs before it is read); the player's own names come back from footplay.txt (kept).
Q40 `L184 = 317` in the set-up is never read; `L390` is never read; `L31c` is read only by the unspoken fake texts (nothing to reproduce).
The season engine and the play-offs (S3.6; decisions in D-029):
Q41 A tied score counts as a win for the opponent (pog: `If Me.m414(1) <= Me.m414(2)`, in the regular season and the play-offs); a game cannot end tied (overtime, and a conceded game always gives the opponent more), so it never happens (kept as the rule).
Q42 The other 30 teams follow no schedule: every week pog pairs them at random and draws their scores from a 32-entry table (no tie, the higher score wins); a team can meet the same opponent many times (kept, it is how the season is made).
Q43 Ties in the final standings: the division winner and the wild cards are the teams with the fewest losses (team order on a tie), but the player's team wins a tie with the division leader and with the second wild card (kept).
Q44 Seeding by WINS, fewest first: the two division winners with the most wins get the byes, the two others host the wild cards (best wild card at the division winner with the fewest wins); the bracket is fixed, there is no re-seeding (kept).
Q45 Every play-off game without the player is a coin flip (1 in 2 for each team, whatever the records or seeds), with scores from the table (winner never 0, loser lower) (kept).
Q46 Sentence slips in pog's play-off weeks (5.16 item 4): the first A. F. C. wild card result is lost when the player plays the second; three computer results lose their " The "; the player's own A. F. C. championship result is never spoken; the two A. F. C. wild card results are one text (not reproduced: every result its own sentence " The <winner> won over the <loser> by the score of <w> to <l>. ").
Q47 The headings differ between the two engines: pog " In the A. F. C. division play off games. ", " In the A. F. C. championship  game. " (two spaces), " In the N. F. C. championship game. "; finplay17 " In the A. F. C. Division play off games. ", " In the A. F. C. Championship game. ", " In the N. F. C. Championship game. " (kept: the speech engine reads them the same; each engine keeps its own text).
Q48 A conceded Super Bowl runs pog's championship branch on the Super Bowl record: two championship headings, the loss spoken once, then a simulated Super Bowl of the opponent against itself with random scores and the celebration (5.16 item 8) (not reproduced: " In the Super Bowl. ", the conceded result, the celebration and the wait, then the season ends).
Q49 When the player's team is out after week 16 or loses a play-off game, all remaining rounds are played and spoken at once (finplay17), with a key wait after each round and the celebration after the Super Bowl; the season then ends (kept).
Q50 After F1 or F2 at the end of finplay17 the Super Bowl celebration plays again after a 5-second pause (kept, it is what the player hears).
Q51 After week 16 the standings are spoken only when the player's team plays the wild card round (gtp 17); with a bye (gtp 18) or out (gtp 0) SayStand is silent (kept).
Speech, keys and the season's end (S4.3; decisions in D-031, details in GAP_REGISTER.md):
Q52 " Hike! " is spoken asynchronously in the quarterback's voice and the next announcer line (say4) reloads the voice object when the two voice numbers differ; releasing a speaking voice stops its speech (tested), so a "Hike!" still speaking after the 0.6 s crowd ramp (S5.2: 0.7 s, section 7) has its tail cut (not reproduced: one queue, nothing cut, G-S1).
Q53 After the standings the original waits for one key press even when it spoke no standings (gtp 18 to 20, because the exit follows) (not reproduced: no silent wait; the game waits for a key only after spoken standings, G-F2).
Q54 A key typed during narration (synchronous speech does not pump messages) is delivered at the next key wait with its code but no character, so the wait ends at once and an Enter chooses the first item of the next play menu (kept exactly, the starter kit's KeyInput does it, G-K1).
Q55 The exit with gtp = 0 deletes footplay.txt with the season files, so the player's edited names are gone and a new season draws new random names (kept: new random names each season; the game first saves the old file as footplay.previous.txt, G-F4).
Found by the fresh audit of S5.2 (audit report `work/audit_s52_findings.md`; decisions in D-034):
Q56 The incompletion " bats it right back at <quarterback> " names defensive player L578 of the side ON OFFENSE (`Me.m370(wisoff, L578)`, pag 0x44cc09, read in the asm at 0x44cadb), so the passer's own team's defender bats the ball back; every other defender text uses the defense's side L504 (5.9) (kept: it is what the player hears, the exact algorithm).
Q57 After " is way to short" (the player's field goal from his own half) the play noise foot14 is not stopped: no PlayTackle comes before the possession change, so it loops under the possession sentence, the banter, the down sentence and the next play menu until the next PlayTackle (5.10) (not reproduced: the game stops the loop after " is way to short", with no other sound; G-A2's safety net stays).
Q58 The key echo sets the rate to vr + 5 but queues the character asynchronously and sets vr back at once, and SAPI renders it at the restored rate (TESTED, 8.1), so the echo is heard at the normal rate (kept: the game echoes at the normal rate, G-S5).
Q59 F12 with only one SAPI voice: ChangeVoice returns at once without clk and without the F1 hand-back, so the interrupted wait receives F12 as an ordinary key (echoed as "{", the prompt starts again as for any other key; 4.7) (not reproduced: the game's F12 always ends with the F1 hand-back like every global key, D-018, also when there is nothing to choose).
Q60 A fumbled run is not counted as a running play (the count is in the branch without a fumble, pag 0x44db46), while a fumbled pass keeps its attempt and its completion or sack; the fumble also comes before the tackle, sack or catch sentence and the play's end sounds, which are then never heard (5.9) (kept: the statistics and the sentences as the original gives them).
Found while building the game (S7.3b; decisions in D-043; every path of pag was built from the lifted code and tested with scripted draws):
Q61 The kick-off starts the play noise foot14 (PlayNoise at 0x444c7d, after foot7) and nothing stops it before the player's run-out question (4.16: say5 and getkey2 at 0x445541): it loops under the question until the touch back's PlayTackle(8) or the return's tackle (kept: it is the sound of the kick in the air while the player decides; the game's safety net of G-A2 does not act at this one wait).
Q62 The return flag L30c (no pause before the tackle of a kick-off return) is set at every return (0x446bb6) and reset only where a play ends in the field of play (0x45073e); a return that goes for a touchdown leaves it set, so the next play that ends in the field of play (after a touch back on the following kick-off, or on a later possession) has no pause of |yards| / 25 before its tackle sound (kept: the exact algorithm, at most about a second of pause, tested in `game/tests/test_pag_kicks.py`).

## 16. Child games and links (P5 S5.1)
- Child games: none. The original starts no other game. It is itself one of the games of Jim Kitchen's Kitchensinc game menu `gamemenu.exe` (another program and another project, rule 0.2, D-006). Its only link to that menu is at the exit: `Dir("gamemenu.exe")` in the current folder; found: `Set Voice = Nothing`, `Shell "gamemenu.exe", 3`, `End`; not found: two Beeps, the sentence " Sorry, but I could not find the Kitchensinc game menu program. ", `End` (section 3, Exit; section 13; Q-013). [CODE (lifted)]
- The game launches nothing (D-006, 0.10) and always takes the "not found" branch with its two beeps and its sentence (G-F6, SOUND_DESIGN 4). A later version of the game menu could start this game; nothing in nfl4 depends on it. If S7.5 adds Brain's lookup of `gamemenu.exe` in the game's own folder, the beeps and the sentence play only when it is not found (SOUND_DESIGN 4 step 5).
- Shared data folder: the original keeps its files in `Documents\kitchensinc`, shared with the other Kitchens Inc programs (on this PC it holds Jim's `gamemenu.txt`); the game uses its own per-user folder and never reads or writes `Documents\kitchensinc` (D-024 item 3, G-F8). [CODE (lifted), getkp]
- `brain.txt`: a name in the first-run copy list, left over from Jim Kitchen's game Brain; nothing reads it and no data is shared with Brain (Q-015; D-016: the copy routine is not reproduced).
- `football.txt` names `uninfoot.bat` (an uninstall batch file, not in the owner's copy; the game's installer uninstalls, 0.10) and gives the author's contact details (never published, D-008). The exe's strings hold no web or mail address (scan of `spec/strings_all.tsv` in S5.1 for www, http, .com, .net: none).
- The no-voice message ends with "Please contact Jim Kitchen" (section 3 step 3); the game's message points to the repository instead (G-F9, D-008).

## 17. Game notes (P5 S5.1): decisions, what stays exact, what changes, what is added
The game is built from this spec on the starter kit (D-002) in P6 to P8. Every decision has its entry in `spec/DECISIONS.md` with the reason and what would show it wrong; `spec/GAP_REGISTER.md` gives the game's answer to every gap the code does not decide by itself, each default with the session that closes it (its section 9); `spec/SOUND_DESIGN.md` decides the sounds (nothing added) and `spec/CUSTOMIZABLE_CONTENT.md` the customization files. This section is the builder's summary; where it and a decision differ, the decision wins and this section is corrected.

### 17.1 The decisions, one line each (details in DECISIONS.md)
- D-001 The original wavs ship in the repository and the installer on the owner's responsibility (AGENTS.md 10).
- D-002 Rules 0.9 to 0.11: start from the starter kit, record fixes in fixesforgames.md, clean uninstall and clean exit, sound math with audioop-lts and no numpy (none needed: plain playback with volume, pan and frequency), output through the pygame-ce mixer.
- D-003 "Sounds start right away" is never the default.
- D-004 JAWS support: yes (the kit's backend).
- D-005 The original is not run (DirectX 8 for VB is not registered here); desk work only.
- D-006 The game does not launch `gamemenu.exe`.
- D-007 Name "NFL Football 4 by Josh Kennedy, inspired by Jim Kitchen", package `nfl4`, repository `nfl-football-4-audio-game`.
- D-008 Jim's contact details are never published; the surnames stay as the original data.
- D-009 Layout: the originals moved into `original\` after hashing, read-only; `work\football.exe` is the working copy.
- D-010 to D-012, D-019 to D-021 Method of P2 and P3 (recovery strategy, Ghidra folders, the gap-filled assembly, generated structure files, reading the lifted code, the batch plan).
- D-013 Random numbers: the system generator seeded from the clock, the original's ranges and choice structure, a fixed seed in tests.
- D-014 The blitz help text is spoken with "play." at the end (the original stops at "on the ", Q-020).
- D-015 The crude banter lines stay; README content note; the owner decides at S11.1 (Q-018).
- D-016 The game creates every data file itself; the first-run copy routine is not reproduced.
- D-017 STRINGS.md, strings_all.tsv and WAV_EVENT_MAP.md are generated; edit the generators.
- D-018 The global keys work at every wait and hand F1 to the interrupted wait, as the original does.
- D-022 Typed names follow the original rule; keypad keys type digits; the rate stays in -10 to 10; one SAPI voice means no voice choice and voice 0; every speaker call picks its voice and applies its role's own volume. (S5.2: F12 with one voice still ends with the F1 hand-back in the game, Q59, D-034.)
- D-023 Every sound with the original's volume, pan, frequency, loops, waits and key behavior; not reproduced: the double counting of wavol in the F11 sound step and the +1 Hz.
- D-024 After a game the game returns to the week loop and the menu (Save Game still ends the program); state rebuilt at every game; its own data folder; the original's value order in its files, read tolerantly; a missing or unreadable file never ends the program.
- D-025 Season, schedule, standings, clock and name quirks: kept as listed; not reproduced: F1 in the main menu, the clock at counter 0 before any F4, the missing-file paths, the silent loss of footplay.txt edits, the MsgBox (and, reversed by D-031, the doubled spaces are kept). (S5.2: "the MsgBox" is superseded by D-031 item 6 and D-032 item 3: the game shows the box and speaks it through a screen reader when one runs, G-F9, Q12.)
- D-026 The 32 team names and the 1,708 surnames stay as the original data (Q-016, Q-026 at S11.1).
- D-027 The play engine exactly as 4.14 to 5.12; kept and not reproduced quirks as in 17.5; football.sav gets one extra value (the side that received the opening kick-off).
- D-028 Phrases, rosters and banter exactly as 5.5, 5.9, 5.13 (the unspoken fake texts stay unspoken; the damaged-file crashes are not reproduced).
- D-029 The season engine and the play-offs exactly as 5.14 to 5.17; Q46 and Q48 not reproduced; at the season's end the game deletes the season data and starts a new season.
- D-030 The listening tool `tools\sound_review` and the three rounds (all 26 names OWNER-CONFIRMED).
- D-031 The gaps: one speech queue with the original's pauses, exact texts, five role voices on the kit's layer with SAPI as the default mode, the kit's key model with F9 for the added functions, the seven sound slots, the flow after a game and at the season's end, the data folder, bounded redraw loops.
- D-032 Nothing added to play and no music; the exit beeps reproduced; the dead "corrupt wave files" text reused as the sound-file notice; the crowd beds restart after a game; four customization files in one `customize` folder with the `ID = name` format.
- D-033 This consolidation (S5.1): the 5.1 order, sections 16 to 19, the generated regions of `work/check_spec_s51.py`, Q-020 answered.
- D-034 The fresh audit (S5.2): 34 findings fixed by adding words (18.5); quirks Q56, Q58, Q60 kept, Q57 and Q59 not reproduced; typed names up to 30 characters; G-S5 settled (the echo at the normal rate); the spec frozen as version 1.0.
- D-035 OWNER DECISION (2026-10-14): the banter is customizable with the player's own text and own sounds (`banter.txt`, CUSTOMIZABLE_CONTENT 12, built in S7.7); the same in every later game (AGENTS.md 0.12, playbook 7.9).

### 17.2 What must stay exact (the conformance tests of S8.1 check it against this spec and STRINGS.md)
- Every spoken text with its spelling, its spaces (Str$ leading and doubled spaces included, G-S3), its punctuation and its pieces as sections 3 to 5 build it; which speaker speaks it (waits or not, replay list, log, voice and volume: 9.1); the order of the lines.
- Every key in every state, including "any other key", F1 to F4 and the F1 hand-back after a global key menu (4, 8.1, 8.2; D-018), except the keypad digits and the typed-name keys of D-022.
- Every random draw with its range, its redraw rule and its history length, in the order of the code (5, 6; D-013); the outcome table, the field goal draws, punts, kick-off returns, the computer's choices, the schedule maker, the standings, the season's score table, the division winners, wild cards, seeds and bracket (5.1 to 5.17).
- Every sound: file, volume, pan, frequency, loop, slot, wait and key behavior and its place among the spoken lines (10, WAV_EVENT_MAP; D-023 except its two slips).
- The pauses dy and rady with their formulas and places (7; G-S2; S5.2: every site is in `work/pause_table_s43.txt`, and the sequences of 3 to 5 give their order on each path).
- The value order of the original's files as far as the game keeps them (12; D-024 item 4).
- The quirks kept in 17.5.

Conformance map (P8 S8.1, 2026-10-19, D-080): every requirement of sections 1 to 14, every quirk Q1 to Q62, each bullet of this list, the gap-register entries that close in S8.1, the 26 sounds the owner confirmed by ear and the extra features' requirements C1 to C10 and N1.1 to N7.7 has a row in `game/tests/data/conformance_map.tsv` naming its tests; `game/tests/test_conformance.py` fails when the spec and the map differ; the readable form is `spec/CONFORMANCE_MATRIX.md`.

### 17.3 What the game changes (each with its decision and its test)
- Program flow: the game returns to the week loop and the menu after a game (Q1, D-024 item 1); the standings wait only after spoken standings (Q53, G-F2); at the season's end a spoken notice and the new-season set-up (G-F3, D-029 item 4), footplay.txt first saved as footplay.previous.txt (G-F4, Q55); the spoken title at every launch (0.5.1, G-F1).
- Speech: one queue for all roles, nothing cut by a voice change (Q52, G-S1); NVDA and JAWS backends beside SAPI, SAPI 5 the default mode (D-004, G-S7); the 7.4.2 voice picker per role (G-S8); the voice picked and the role's volume applied at every call (D-022); the rate kept in -10 to 10 (D-022); the rate counter with NVDA and JAWS changes only the pauses (G-S4); the key echo rate (G-S5; S5.2: settled by a test, the echo is spoken at the normal rate as the original is heard, Q58, so this is no change); He or She from the SAPI voice token of the role as in the original, always He with NVDA or JAWS (G-S6); the log in the data folder with a 1 MB cap (G-S10).
- Keys: keypad digits type and choose digits (Q32, D-022, D-027); typed names stored up to 100 characters (G-K5; S5.2: 30 characters, D-034); F12 with only one SAPI voice ends with the F1 hand-back like every global key (Q59, D-034); the window's close button and Alt+F4 end the program at once (G-K4); F9 opens the added functions (G-K2).
- Files: the game's own data folder and settings file, no footbal0.dat or football.vol (G-F8); a missing or damaged file repaired or the season restarted with a notice (Q7, Q8, Q36, D-024 item 5, D-025 c and d); a damaged football.sav set aside (G-F5); football.sav carries the side of the opening kick-off (Q28, D-027 item 3); footplay.txt read as UTF-8 with a cp1252 fallback (D-028).
- Sound: the two arithmetic slips of D-023; the crowd beds restart after a game (G-A5); one spoken notice for an unusable sound file (G-A6); no sound device means play on silently with one notice (G-A4); the play-noise loop stopped at every key wait as a safety net (G-A2); the play noise stopped after " is way to short" (Q57, D-034).
- Texts: the blitz text completed (D-014); the no-voice message shown and spoken through a screen reader when one runs (Q12, G-F9).
- Robustness: every redraw loop bounded (G-D1).
- The slips of the original that are not reproduced: 17.5.

### 17.4 What the game adds
- The window title and the spoken title (0.5.1, G-F1); the About item with the note about Jim Kitchen (0.5); the README.
- The F9 menu: speech settings, sounds (7.7, `sounds.txt`), customize (7.9: `teams.txt`, `divisions.txt`, `surnames.txt`, `footplay.txt` in the `customize` folder), about (G-K2, CUSTOMIZABLE_CONTENT 10).
- The game-only spoken texts of GAP_REGISTER section 8 (draft wording; marked CLONE in the tests).
- No added sound and no music (D-032); the generated 80 ms blip is only the last fallback of the exit beep (SOUND_DESIGN 7).
- OWNER DECISION 2026-10-14 (D-035): the announcer's banter is customizable: `banter.txt` in the `customize` folder holds the 142 original lines of 5.13 as defaults (B001 to B142), the player can change or switch off any line and add lines of their own text, their own sound files (`customize\sounds\`) or both; the draw rule of 5.13 covers the whole pool and F8 silences all of it; with the file unchanged the game says and plays exactly what 5.13 gives (CUSTOMIZABLE_CONTENT 12, built in S7.7; the same rule for every later game, AGENTS.md 0.12). This changes nothing in sections 1 to 15, which describe the original. OWNER REQUEST 2026-10-14 (D-040): the finished game must also have seven extra in-game features that the original does not have: timeouts, replay challenges, quarterback keepers and onside kicks according to the NFL rules, optional Madden-style playbooks, a Franchise mode, and penalties with accept or decline; they belong to this game only and are specified in `spec/NFL_EXTRA_FEATURES.md` (a companion of this spec, version 0.1, requirements only; research and design sessions SX.0 and SX.1 come before any code). A setting "Rules" has the values Classic (everything of sections 1 to 15 and 17.2, exact, the one the conformance tests use) and N. F. L. rules (the extras); the classic engine is built with the hooks of that file's section 5 and a recorded golden transcript of a Classic game.

### 17.5 The quirks of section 15 by decision (generated by `work/check_spec_s51.py --write` from the table in that script, which checks each class against the wording of its line in section 15)
<!-- QUIRKS-BEGIN -->
- Kept (the player hears them, or they are rules of this game), 36: Q2, Q3, Q4, Q9, Q10, Q11, Q13, Q14, Q15, Q17, Q18, Q19, Q20, Q21, Q22, Q29, Q31, Q34, Q35, Q37, Q39, Q41, Q42, Q43, Q44, Q45, Q47, Q49, Q50, Q51, Q54, Q56, Q58, Q60, Q61, Q62.
- Not reproduced (slips of the original the game does not copy), 16: Q5, Q7, Q23, Q24, Q25, Q26, Q27, Q32, Q36, Q38, Q46, Q48, Q52, Q53, Q57, Q59.
- Changed by a game rule, 3: Q1 (the game returns to the menu after a game, D-024 item 1), Q8 (only the broken section is repaired, with a notice, D-025 d), Q12 (a message box and speech through a screen reader, G-F9).
- Partly kept, 3: Q6 (the time at counter 0 not reproduced, the clock without seconds kept), Q28 (the kick-off side stored, the rest kept), Q55 (new random names kept, footplay.previous.txt added).
- Nothing to reproduce (inaudible, or the log only), 4: Q16, Q30, Q33, Q40.
- Total 62 quirks, Q1 to Q62; each class was checked against the wording of its line in section 15: PASS.
<!-- QUIRKS-END -->

## 18. Checklist results (playbook 5.4; P5 S5.1, for the fresh audit of S5.2)
Every item of the 5.4 completeness checklist, answered from this spec and its companion files. An item is answered when its evidence is CODE, TESTED or OWNER-CONFIRMED unless it says otherwise; a default names the session whose test confirms or breaks it (GAP_REGISTER section 9).

### 18.1 The checklist
1. All strings tied to events, menus, choices: answered. All 3,155 strings are classified with the procedures that use them (STRINGS.md, strings_all.tsv); every text of the program is tied to its situation (Q-012, S3.4 to S3.6); the engines' texts are checked against the string table by script (`work/check_texts_s36.py`, banter `work/extract_banter_s35.py`, phrases `work/check_phrases_s35.py`) and every spoken sentence of pog and finplay17 on every path (`work/check_sentences_s36.py`). The strings with no referencing procedure are compiler, linker, type library, version and header items and junk bytes, plus one dead text (proven by scan, B-P35, reused as the sound-file notice, G-A6): counts in 18.3. [CODE]
2. All wavs tied to events, plus unreferenced files: answered. 26 of 26 files are referenced by code, every call site is tied to its situation (WAV_EVENT_MAP sections 2 and 5), no file is unreferenced; all 26 names OWNER-CONFIRMED in the three listening rounds (Q-009, D-030). [CODE, OWNER-CONFIRMED]
3. All PC speaker tones, beeps, music strings tied to events: answered. No tone and no music string exists; two `Beep` calls (the exit branch, `MessageBeep(0)`) and the no-voice message box sound (SOUND_DESIGN 2, WAV_EVENT_MAP section 7). [CODE, TESTED]
4. Every silent event and its decision: answered. 20 groups (SOUND_DESIGN 3: SE-01 to SE-08 outside a game, SE-10 to SE-21 in a game), each kept silent with its reason; nothing is added (D-032); default G-A7, closes S8.2.
5. All menus and choices with exact keys: answered. The main menu (4), the seven hot-key menus (4.1 to 4.8), the season prompts (4.9 to 4.13), the game's questions and menus (4.14 to 4.19), the key model and typing (8.1, 8.2), each with its "any other key" case. The game's F9 menu: G-K2, default, closes S7.4. [CODE (lifted)]
6. All loops, conditions, functions, procedures marked done: answered. 64 of 64 procedures done (PROCEDURE_INDEX, FEATURE_MAP; 18.3); the lifter's completeness check passes for all 64 (`work/lift/lift_report.md`); the lint's 10 names are explained (section 14); where each procedure is written: section 14. [CODE (lifted)]
7. All mechanics, formulas, constants, tables, random behavior: answered. Sections 5.1 to 5.17 and 6; the engines' random draws checked against the exe (0 mismatches), their integer constants (`tools/vb6_const_check.py`, every miss explained), both jump tables and both score tables by script (S3.4 to S3.6). [CODE (lifted)] (S5.2: the audit added the defender of " bats it right back at " (A-01, Q56), what a fumble skips (A-02, Q60) and the play noise after " is way to short" (A-03, Q57); 18.5.)
8. All maps, levels, rosters, tables: answered. No maps or levels; the 32 teams, 8 divisions, 1,708 surnames, the rosters and footplay.txt (11; SURNAMES.tsv; CUSTOMIZABLE_CONTENT 3 to 6, 12 of 12 scripted checks PASS), the schedule (5.1), the outcome tables (5.9), the score table (5.14). [CODE (lifted)]
9. Every customizable list with original limits (7.9): answered. CUSTOMIZABLE_CONTENT.md: the four files, the typed names, the settings and the lists that stay built in, each with its reason; format and limits D-032 items 7 to 11. (S5.2: the banter is a fifth file by the owner's decision, `banter.txt`, CUSTOMIZABLE_CONTENT 12, D-035; typed names limited to 30 characters like the files, A-31.)
10. All files, data files, formats: answered. Section 12: 13 files with writers, readers and layouts (Q-007). [CODE (lifted)]
11. All text files and everything else in the folder: answered. The original folder holds 28 files (football.exe, football.txt, foot0.wav to foot25.wav; INVENTORY.md, ORIGINAL_SHA256.txt); football.txt is compared with the exe's help texts (section 9: 89 of 97 non-empty lines are in the exe; the readme-only lines are listed there); nothing else. [CODE, OBSERVED (file text)]
12. All accessories and helpers: answered. Sections 13 and 16: the readme; `gamemenu.exe` at the exit, not part of this project; `uninfoot.bat` named but absent; no helper EXE or DLL besides DirectX 8 for VB and SAPI. [CODE]
13. All events and their order: answered. Sections 3, 4.14 to 4.19 and 5.6 to 5.17 in play order; WAV_EVENT_MAP section 5 (every sound in play order); how speech, pauses and sounds interlock (7, G-S1, G-S2). [CODE (lifted), TESTED] (S5.2: completed for fumbles (A-02), the play noise after " is way to short" (A-03), the Super Bowl presentation (A-07), F2 at the final score (A-08), the banter after the statistics of quarters 1 and 3 (A-15), the order of the snap's draws (A-20).)
14. Timing: answered. Section 7 (dy, rady, getkey2, PlayRan, the ramps, every fixed time; 68 pause sites in `work/pause_table_s43.txt`; synchronous speech, purge and voice release TESTED). The game's pause model: G-S2, default, closes S7.4 and S8.2. (S5.2: the pauses of kicksnap, the touchdown countdown and the kick-off return completed (A-09), c2dh is 0.7 s (A-13), the pause table is named as the list of every site (7 item 3).)
15. Error and bad-input behavior: answered. Section 15 (Q1 to Q55; S5.2: Q1 to Q60), every menu's "any other key" (4), typed names (8.2), GAP_REGISTER G-E1; the original's only error handling is one `On Error Resume Next` in getkp. [CODE (lifted)]
16. What the original does when its own file is missing, empty or corrupt: answered, with one INFERRED point. Section 12 (which readers check with Dir, which open without a check; a missing file opened For Binary Access Read is created empty, TESTED with the VB6 runtime's own open routine, B-P31), Q7, Q8, Q36. INFERRED: a `Get` past the end of a short file leaves the variable unchanged (the documented VB behavior, not run here); it decides nothing in the game, which repairs or restarts (D-024 item 5, D-025 c and d, G-F5); the S8.3 damage tests cover the game's side.
17. Start-up and shutdown, with what is spoken or played: answered. Section 3 steps 1 to 6 and 9 and the Exit bullet, SOUND_DESIGN 4. The game's title at every launch (G-F1) and its exit sequence (G-F6) are defaults; they close in S7.4, S8.1 and S8.2. [CODE (lifted), TESTED (the Beep)] (S5.2: the no-voice exit path corrected, 3 step 3, A-04.)
18. Child games: answered, none (section 16).
19. The gap items of 5.4 (timing, speech and key mechanics, flow at the end of a game or season, files, errors, bad input, randomness, added texts): answered in GAP_REGISTER.md (counts in 18.3; the game-only texts in its section 8); the silent events and system sounds in SOUND_DESIGN.md (item 3 and 4), the customizable lists in CUSTOMIZABLE_CONTENT.md (item 9).
20. The auditor: S5.2 is a fresh review by a session or subagent that did not write this spec (5.4); it reruns `work/check_spec_s51.py`. (S5.2: done, an Opus 5.5 subagent, `work/audit_s52_findings.md`; its verdict item by item: items 7, 13, 14 and 17 were not answered until A-01 to A-04, A-07 and A-09 were added, which is done; the others answered; 18.5.)

### 18.2 Findings still tagged INFERRED (no GUESS, no UNKNOWN; the scan is in 18.3)
None of them changes what the player hears in the game:
- The DirectX 8 for VB method names behind the vtable offsets and the buffer flags 224 (3 step 2, 10; Q-024): strongly INFERRED from every call site; no type library on this PC. The game does not call DirectX (pygame-ce mixer); the volumes, pans, frequencies, loops and waits the code passes are CODE.
- `KeyPreview = True` (form member 0x1d4; 3 step 1): what matters, that the handler sees every key, is CODE (8.1); the game uses the kit's window.
- The Variant type of the division games' values in footbal2.dat (Integer, from the For counters; 5.1): only the byte layout depends on it, and the game reads every numeric type (D-024 item 4).
- A `Get` past the end of a file (12): 18.1 item 16.
- The game's random generator (6): a decision (D-013, G-D2), not a finding about the original.
- Lines where INFERRED is kept as history next to its upgrade (7 the game clock, 10 the wav names, 11 the opponent's names, 14 the roles) and the header of the table in 12 ("INFERRED unless noted"; every row now carries its tag).
- OBSERVED in this spec always means text read from football.txt or the exe's strings; nothing was watched running (D-005).

### 18.3 Scripted results (generated by `work/check_spec_s51.py --write`; rerun it after any change to this file)
<!-- CHECKS-BEGIN -->
- Section order: the 19 sections of playbook 5.1, in order, each once: PASS.
- Against draft 0.10 (`work/GAME_SPEC_draft010_s51_backup.md`, copied at the start of S5.1): 580 non-empty lines; 518 kept verbatim, 60 edited and every word of each kept (allowed drop: the word "Status" of the old status line, now the history paragraph), 2 placeholder lines replaced by sections 16 to 19 with all their pointers present: PASS.
- Evidence tags in the preamble and sections 1 to 15, draft 0.10 then now: CODE 115 then 126, CODE (lifted) 66 then 75, TESTED 5 then 12, OBSERVED 4 then 5, OWNER-CONFIRMED 1 then 3, INFERRED 13 then 15, GUESS 1 then 2, UNKNOWN 1 then 2; no count went down: PASS.
- Against draft 0.11 (`work/GAME_SPEC_draft011_s52_backup.md`, copied at the start of S5.2, the text the audit read; generated regions excluded): 571 non-empty lines; 510 kept verbatim, 61 edited by S5.2 and every word of each kept; 23 new lines: PASS.
- GUESS 0 and UNKNOWN 0 in sections 1 to 16; INFERRED 13 times, each listed with its context in `work/spec_inferred_s51.txt` and covered by 18.2.
- Procedures: 64 of 64 done (`spec/PROCEDURE_INDEX.md` section 2).
- Strings: 3,155 in `spec/strings_all.tsv`; 615 have no referencing procedure: BUILD-PATH 1, ERROR-MESSAGE 1, IMPORT-NAME 177, JUNK 1, JUNK-ASCII 370, PE-HEADER 3, TYPELIB-NAME 3, VB-IDENTIFIER 41, VB-PROJECT-NAME 3, VERSION-INFO 15; all are compiler, linker, type library, version, header or junk items except ERROR-MESSAGE 1, the dead text (B-P35, SOUND_DESIGN 2).
- Gap register (its generated count line, `work/check_gap_register_s43.py`): Count: 37 entries. SETTLED 9, DEFAULT 23, NOTED 5. Entries naming each closing session: S8.1 15, S8.2 16, S8.3 5, S9.2 1 (an entry can name several; SETTLED entries that also name a session close their test there).
- Decisions: D-001 to D-059, 59 entries, none missing or doubled (`spec/DECISIONS.md`).
- Quirks: 62 (Q1 to Q62), each classified in 17.5.
<!-- CHECKS-END -->

### 18.4 What S5.1 changed in sections 1 to 15 (the reorder and the edits; 18.3 proves that no word of an old line was lost)
- The order: `work/reorder_spec_s51.py` moved the sections into the 5.1 order (old order 1, 2, 6, 9, 10, 11, 12, 13, 3, 7, 8, 14, 4, 5, 15; 580 non-empty lines before and after, the same byte count).
- The status paragraph is new; the old one stays below it as the history of the drafts.
- Headings of 3 and 4 made descriptive (the old words kept).
- Tags upgraded, the old tag kept as history: 7 (the game clock: CODE (lifted)), 10 (the wav names: OWNER-CONFIRMED, Q-009), 11 (the opponent's names: CODE (lifted)), 12 (the rows of footbal0.dat, football.vol, footballlog.txt and footplay.txt tagged), 14 (every role CODE (lifted)).
- Stale notes completed: 6 (every draw recovered and checked), 9 (the sentence assembly done), 12 (every writer read), 8.1 (the main menu is the first bullet of section 4, not 4.1).
- Pointers added: 4.4 (Q-020 answered), 4.7 (G-S8), 6 (G-D2), 8.2 (G-K5), 14 (where each procedure is written; the lint's 10 names).

### 18.5 What S5.2 changed: the fresh audit's findings and their fixes (D-034; report `work/audit_s52_findings.md`)
Every finding was verified by the agent in the lifted code (and the asm where it decides behavior) before it was fixed; all 34 are real. Each fix only adds words, marked "S5.2" in the text; the companion files were changed through their generators where they are generated. 18.3 proves that no word of draft 0.10 or 0.11 was lost.
- BLOCKER: A-01 the defender named in " bats it right back at " (5.9, Q56 kept); A-02 a fumble skips the play's sentence and end sounds, a fumbled run is not counted (5.9, Q60 kept); A-03 the play noise after " is way to short" (5.10, WAV_EVENT_MAP, G-A2, Q57 not reproduced).
- MAJOR: A-04 the no-voice exit path (3 step 3 and Exit, Q12, SOUND_DESIGN 4, G-F9); A-05 the extra point starts no play noise (WAV_EVENT_MAP foot14 row); A-06 the schedule can be cut in week 1 (4.11); A-07 the Super Bowl presentation by result (5.6 item 7, WAV_EVENT_MAP); A-08 F2 at the final score (4.19); A-09 the pauses of kicksnap, the touchdown countdown and the kick-off return, and the pause table (5.10, 5.11, 7).
- MINOR, exact texts: A-10 no space before the returner's name (4.16, 5.10); A-11 the standings heading trims its number (5.2, G-S3, STRINGS); A-12 two spaces before " did not make it into the playoffs" (5.15, Q-027).
- MINOR, counts and times: A-13 c2dh is 0.7 s (7, Q52, G-S1); A-14 198 Rnd calls, 87 in pag (2, 6, Q-008, Q-010, Q-012).
- MINOR, behavior details: A-15 banter after the statistics of quarters 1 and 3 (4.19, 5.13); A-16 F12 with one voice (4.7, 8.1, Q59 not reproduced); A-17 the sound volume at exactly -5000 (4.6); A-18 a loaded game without footplay.txt asks both names (4.12, 4.18); A-19 the kick-off side after a load (Q28); A-20 the order of the snap's draws (5.8).
- MINOR, descriptions and pointers: A-21 teams ordered by nickname (11, CUSTOMIZABLE_CONTENT 3, STRINGS, PROCEDURE_INDEX); A-22 the copy routine cofs (12); A-23 the no-voice message box rule (Q12, 17.1, D-025); A-24 the pointer for the double counting of wavol (4.6); A-25 the key after the standings (4.13); A-26 keys typed during a synchronous line (8.1); A-30 the decision named in G-F9; A-32 the counts in D-031; A-33 the role column note of PROCEDURE_INDEX; A-34 the sounds of an interception and a fumble (SOUND_DESIGN SE-14).
- MINOR, tested or reworded: A-27 the key echo is heard at the normal rate, TESTED (8.1, 8.2, G-S5 settled, Q58 kept); A-28 S8.3 cannot test the original's Get-at-end rule, and what depends on it (12); A-29 which sounds get the + 1 Hz (WAV_EVENT_MAP section 1); A-31 typed names limited to 30 characters (8.2, G-K5, CUSTOMIZABLE_CONTENT 6 and 10).
- Also in S5.2, not from the audit: the owner's decision that the banter is customizable with own text and own sounds (17.4, D-035, CUSTOMIZABLE_CONTENT 12).

## 19. Open questions (P5 S5.1; the list is `spec/OPEN_QUESTIONS.md`)
<!-- OQ-COUNTS-BEGIN -->
Count (generated from `spec/OPEN_QUESTIONS.md` by `work/check_spec_s51.py`): 30 items: 24 answered, 0 partly answered, 0 open, 3 accepted defaults (Q-016, Q-029, Q-030), 3 owner-needed (Q-017, Q-018, Q-026).
<!-- OQ-COUNTS-END -->
Answered, in short (details, evidence and sessions in OPEN_QUESTIONS.md):
- Q-001 In scope: Jim Kitchen's "NFL football version 4", Kitchens Inc, Visual Basic 6, free and unsupported.
- Q-002 Visual Basic 6.00.8041 native code, no packer.
- Q-003 Sound: DirectSound 8 through DirectX 8 for VB.
- Q-004 Speech: SAPI 5 only, no screen reader calls.
- Q-005 The original cannot run here (DirectX 8 for VB not registered); desk work (D-005).
- Q-006 Other COM: Shell.Application for the Documents folder; `gamemenu.exe` through Shell.
- Q-007 Every file and format is known (12).
- Q-008 `Randomize Timer` at 13 sites, `Rnd` 172 times (6).
- Q-009 Every sound call site tied; all 26 names OWNER-CONFIRMED (10, WAV_EVENT_MAP).
- Q-010 The big procedures: pag (the game), pog (the season), SetPlayerNames, finplay17, ChangeVoice, Form_Load.
- Q-011 Nothing is real time: one synchronous run with busy-wait pauses (3, 7).
- Q-012 Every text and its randomness is tied to its situation (5.8 to 5.17).
- Q-013 The exit and the game menu (3 Exit, 16); the game takes the not-found branch with the two beeps.
- Q-014 Customizable content: CUSTOMIZABLE_CONTENT.md.
- Q-015 `brain.txt` is a leftover name in the first-run copy list.
- Q-019 No reader needs a shipped data file (D-016).
- Q-020 (S5.1) The original speaks the cut blitz text; the game completes it (D-014).
- Q-021 The six speakers (9.1).
- Q-022 The 34 form variables and the private fields (PROCEDURE_INDEX 4 and 5).
- Q-023 A global key menu ends with F1 for the interrupted wait (8.1, D-018).
- Q-024 The DirectX 8 for VB method map (WAV_EVENT_MAP 3; INFERRED, strong).
- Q-025 One SAPI voice: the original does not crash (corrected in S3.6).
- Q-027 A team that is out gets the rest of the play-offs at once and the season ends (5.15 to 5.17).
- Q-028 The clock at play counter 0 (5.6 item 8).
Accepted defaults: Q-016 (the surname data: kept, D-008 and D-026; the owner may change the shipped default at S11.1) and Q-029 (the 27 defaults of GAP_REGISTER.md, each closed by its own session, the last before the build in S8.3; S5.2: 26, G-S5 was settled by a test).
Owner-needed, asked once at S11.1, not blocking the spec: Q-017 (the permission wording of the README), Q-018 (the crude banter lines), Q-026 (the team name "Redskins"). They decide public wording and shipped defaults; the spec describes the original either way, and each answer is one flag or one data line in the game (D-015, D-026, D-032). S5.2: the fresh auditor checked the five unanswered items and agrees that none changes what this spec says about the original, so version 1.0 is frozen without an owner round (D-033 item 5, D-034); with the customizable banter (D-035) the Q-018 answer only chooses which original lines ship switched off.
