### p_42b470 say6 (slot 37, offset 0x910)
- Role [CODE]: say6(text): no voice change (whatever voice is current), logs when ptf = 1, speaks asynchronously (flags 1). Read in full (lifted, S3.1); corrects the S2.2 guess that it only logs.
- Size: 288 bytes, 109 assembly lines. Status: done.
- Calls (form procedures): none
- Called by: adjvol x4
- Main runtime calls: __vbaVarTstEq x1, __vbaPrintFile x1
- Form variables used: ptf x1

### p_42b590 SayScore (slot 38, offset 0x914)
- Role [CODE (lifted)]: SayScore(score of the player's team, score of the opponent) (F3 and during the game): say5 " The score is ", then say of: leader first "<team>. <n>. <team>. <n>" (names RTrim, numbers Str$), or " tied <n> all" when equal; writes a blank line and " The score is <text>" to the log. Read in full (S3.3).
- Size: 1312 bytes, 431 assembly lines. Status: done.
- Calls (form procedures): say x1, say5 x1
- Called by: pag x5
- Main runtime calls: __vbaStrCat x15, rtcRightTrimBstr x6, rtcStrFromVar x5, __vbaVarTstGt x2, __vbaPrintFile x2, __vbaAryConstruct2 x1, __vbaVarTstEq x1, rtcDoEvents x1
- Form variables used: tn1 x2, tn2 x2, tn3 x2, tn4 x2
- String classes: SPEECH-FRAGMENT 3, SCORE-SPEECH 1

### p_42bab0 SayFinalScore (slot 39, offset 0x918)
- Role [CODE (lifted)]: SayFinalScore(player's score, opponent's score): the same text as SayScore with the introduction " The Final score is", ptf = 1 around the speech (logged). Read in full (S3.3).
- Size: 1296 bytes, 414 assembly lines. Status: done.
- Calls (form procedures): say x1, say5 x1
- Called by: pag x1
- Main runtime calls: __vbaStrCat x14, rtcRightTrimBstr x6, rtcStrFromVar x5, __vbaVarTstGt x2, __vbaAryConstruct2 x1, __vbaVarTstEq x1, __vbaAryDestruct x1
- Form variables used: tn1 x2, tn2 x2, tn3 x2, tn4 x2, ptf x1
- String classes: SPEECH-FRAGMENT 3, SCORE-SPEECH 1

### p_42bfc0 sgc (slot 40, offset 0x91c)
- Role [CODE (lifted)]: sgc(plays played, plays in the quarter, quarter) (F4 and quarter starts): makes up the game clock from the play counter: percent of plays left = Int(100 * (total - played) / total); minutes = Int(percent * 15 / CountDown) with CountDown 100 (reset by pag each quarter), seconds from the fraction with a random jitter (-15 to +14, narrower near the two-minute warning of quarters 2, 4 and overtime where M2W, M4W, M5W (5 to 7 plays) raise CountDown and finally set it to 125, 170 or 215); speaks " <m> minute(s) <s> second(s) remaining in the <first, second, third, fourth, over time> quarter. " (say5), ends with clk and g = 112. Recomputed only when the play counter changed (oldtime). Read in full (S3.3).
- Size: 3712 bytes, 883 assembly lines. Status: done.
- Calls (form procedures): clk x1, say5 x1
- Called by: pag x4
- Main runtime calls: __vbaVarTstEq x9, __vbaStrCat x9, __vbaVarTstGt x7, __vbaVarMul x6, __vbaVarInt x5, __vbaVarSub x3, __vbaVarDiv x3, __vbaVarCmpEq x3
- Form variables used: mins x5, secs x5, CountDown x5, g x1, oldtime x1, M2W x1, M4W x1
- String classes: CLOCK-SPEECH 7, SPEECH-FRAGMENT 4, KEY-CODE-OR-NUMBER 1

### p_42ce40 SayStand (slot 41, offset 0x920)
- Role [CODE (lifted)]: SayStand (main menu choice 3, and after every game): reads footbal3.dat (64 values: for division 1 to 8, team 1 to 4: wins, losses; zeros when the file is missing); when 1 <= gtp <= 17 speaks " Standings after week number <min(gtp - 1, 16)> " and for each division its name and its four teams sorted by fewest losses (insertion sort on the losses only, equal ones keep the team order) as " <team> <wins>, and <losses>. "; sets ptf = 1 while speaking (logged), writes a blank line to the log per division. Read in full (S3.3).
- Size: 5040 bytes, 1284 assembly lines. Status: done.
- Calls (form procedures): say2 x3, clk x2
- Called by: Form_Load x2
- Main runtime calls: __vbaVarForInit x9, __vbaVarForNext x9, __vbaStrCat x8, __vbaVarAdd x7, __vbaAryConstruct2 x5, __vbaAryDestruct x5, rtcStrFromVar x3, rtcTrimBstr x3
- Form variables used: gtp x2, ptf x2, kp x1
- Files opened: footbal3.dat (Binary Read)
- String classes: DIVISION-NAME 8, FILE-NAME 2, STANDINGS-SPEECH 2, SPEECH-FRAGMENT 2

### p_42e1f0 k4 (slot 42, offset 0x924)
- Role [CODE]: k4 = kill 4: deletes the file <data folder>\footbal4.dat if it exists (Dir, LCase compare, Kill). Read in full.
- Size: 272 bytes, 96 assembly lines. Status: done.
- Calls (form procedures): none
- Called by: pog x5, finplay17 x3
- Main runtime calls: __vbaStrCat x1, rtcDir x1, rtcLowerCaseBstr x1, __vbaStrCmp x1, rtcKillFiles x1
- Form variables used: kp x1
- String classes: FILE-NAME 2

### p_42e300 stopspeech (slot 43, offset 0x928)
- Role [CODE]: stopspeech: gets the SpVoice and calls Speak("", flags 2) (purge before speak), so the current speech stops. Read in full.
- Size: 208 bytes, 85 assembly lines. Status: done.
- Calls (form procedures): none
- Called by: readins x3, speckeys x2, SayHints x2, ctog x1, adjvol x1, adjrate x1, ChangeVoice x1, getkey x1, getkey2 x1, pag x1, Form_Load x1
- Main runtime calls: none

### p_42e3d0 saykey (slot 44, offset 0x92c)
- Role [CODE]: saykey: key echo: Rate = vr + 5, purge (Speak "", 2), speaks g2 asynchronously unless the key is F1 ("112"), Rate back to vr. Read in full (lifted, S3.1).
- Size: 528 bytes, 200 assembly lines. Status: done.
- Calls (form procedures): none
- Called by: pag x6, ChangeVoice x5, adjvol x2, getter x2, ChooseTeam x2, Getqbs x2, SayScedual x1, GetCoach x1, Form_Load x1
- Main runtime calls: __vbaVarAdd x1, __vbaStrCmp x1
- Form variables used: g x1, g2 x1, vr x1
- String classes: KEY-CODE-OR-NUMBER 1

### p_42e5e0 Form_KeyDown (slot 62, offset 0x974)
- Role [CODE]: Form_KeyDown(KeyCode, Shift). Read in full: F10 and Alt are swallowed (KeyCode set to 0 and g set to "27"); every other key sets g = the key code as text and g2 = lower-case character of that code (this is how all the polling loops see keys). Then F12 -> ChangeVoice, F11 -> adjvol, F8 -> ctog, F7 -> SayHints, F6 -> readins, F5 -> speckeys, Ctrl (17) -> adjrate. F1 to F4, Esc and the others are read by the getkey loops, not here.
- Size: 672 bytes, 240 assembly lines. Status: done.
- Calls (form procedures): readins x1, speckeys x1, SayHints x1, ctog x1, adjvol x1, adjrate x1, ChangeVoice x1
- Called by: nobody (event handler, called by the runtime)
- Main runtime calls: __vbaStrCmp x7, __vbaStrI2 x1, __vbaI4Str x1, rtcBstrFromAnsi x1, rtcLowerCaseBstr x1
- Form variables used: g x2, g2 x2
- String classes: KEY-CODE-OR-NUMBER 8

### p_42e880 dy (slot 45, offset 0x930)
- Role [CODE]: dy(seconds): busy wait, Timer plus argument, loop with DoEvents until Timer passes. Read in full. (Not midnight safe: same as the original.)
- Size: 256 bytes, 88 assembly lines. Status: done.
- Calls (form procedures): none
- Called by: pag x10, Form_Load x5, SayScedual x3, finplay17 x2, c2uh x1, c2uf x1, c2dh x1, c2df x1, PlayTackle x1, playcel x1, readins x1, inrep x1
- Main runtime calls: rtcGetTimer x2, rtcDoEvents x1, __vbaVarAdd x1, __vbaVarTstGt x1

### p_42e980 rady (slot 46, offset 0x934)
- Role [CODE]: rady: random pause: Randomize Timer, n = Int(Rnd * 30), r = vr (at least 1), waits n / (r * 25) seconds (Timer loop with DoEvents). Read in full (lifted, S3.1).
- Size: 544 bytes, 165 assembly lines. Status: done.
- Calls (form procedures): none
- Called by: pag x35, kicksnap x5
- Main runtime calls: rtcGetTimer x3, rtcRandomize x1, rtcRandomNext x1, __vbaFPInt x1, __vbaVarTstLt x1, __vbaVarMul x1, __vbaVarDiv x1, __vbaVarAdd x1
- Form variables used: vr x1

### p_42eba0 SayScedual (slot 47, offset 0x938)
- Role [CODE (lifted)]: SayScedual (main menu choice 2): from week 17 on: " games for the <week name> are. " then every record of footbal4.dat as " the <team> verses the <team>. " (say4). Before: say2 " <team> schedual. ", reads footbal2.dat, then for every week " game number <n>" and " <first> verses the <second>" with the pauses dy(0.1) and dy(0.2); flag 1 = opponent first, own team second; flag 2 = own team first. In week 1 only (gtp <= 1): " <coach> do you like this schedual? yes " (say5); Up, Down, Tab toggle yes/no and speak it, Enter takes the current answer, y accepts, n and Enter on no call makes() and speak the new schedule again, F1 speaks the whole schedule again, other keys are echoed. Read in full (S3.3).
- Size: 3792 bytes, 1001 assembly lines. Status: done.
- Calls (form procedures): say2 x3, say5 x3, dy x3, clk x1, getkey x1, say4 x1, saykey x1, makes x1
- Called by: Form_Load x1
- Main runtime calls: __vbaStrCat x17, __vbaVarTstEq x8, __vbaStrCmp x7, __vbaGet3 x5, __vbaVarForInit x3, __vbaVarForNext x3, __vbaFileOpen x2, __vbaFileClose x2
- Form variables used: g x5, tn1 x3, tn2 x3, g2 x2, gtp x2, kp x2, coach x1
- Files opened: footbal4.dat (Binary Read); footbal2.dat (Binary Read)
- String classes: SCHEDULE-SPEECH 10, SPEECH-FRAGMENT 7, KEY-CODE-OR-NUMBER 5, FILE-NAME 2

### p_42fa70 makes (slot 48, offset 0x93c)
- Role [CODE (lifted)]: makes: builds the 16-game schedule into a local Variant table (week 1 to 16 x opponent division, opponent team, home flag) and writes footbal2.dat. Step 1: for each of the 3 other teams of the player's division, twice (flag 1 and 2): a random free week (Int(Rnd * 16) + 1) that is not within 2 weeks of the previously placed division game (the first draw is checked against 0, so weeks 1 and 2 are refused for it). Step 2: the 10 other weeks: a random other division (Int(Rnd * 8) + 1, not the own), a random team (Int(Rnd * 4) + 1), not already on the schedule, and a random flag (Int(Rnd * 2) + 1) with at most 5 of each. Result: 8 games with flag 1 and 8 with flag 2. Called by Form_Load at a new season and by SayScedual when the player rejects the schedule in week 1. Read in full (S3.3).
- Size: 3696 bytes, 903 assembly lines. Status: done.
- Calls (form procedures): none
- Called by: SayScedual x1, Form_Load x1
- Main runtime calls: __vbaVarTstEq x10, __vbaVarForInit x7, __vbaVarForNext x7, rtcRandomNext x4, __vbaFPInt x4, __vbaVarSub x4, __vbaVarCmpEq x4, __vbaVarTstNe x3
- Form variables used: kp x1
- Files opened: footbal2.dat (Binary Write)
- String classes: FILE-NAME 1

### p_4308e0 ChooseTeam (slot 49, offset 0x940)
- Role [CODE (lifted)]: ChooseTeam: says " <coach> choose your team " and then the team name of (tn1, tn2) starting at (1, 1); Up and Down step through the 32 teams division by division (tn2 1 to 4, then the next tn1 1 to 8, wrapping 1,1 to 8,4 and back), speaking only the team name; Enter asks " <coach> your team is the <team>. Is this correct? " with yes/no (Up, Down, y, n, Enter, F1 speaks the answer again); any other key is echoed and the whole choice starts again at the first team. Writes footbal1.dat (tn1, tn2, length of the coach name, one character code each). Called once, at a new season. Read in full (S3.3).
- Size: 2240 bytes, 605 assembly lines. Status: done.
- Calls (form procedures): say2 x5, getkey x2, saykey x2
- Called by: Form_Load x1
- Main runtime calls: __vbaStrCmp x9, __vbaStrCat x7, __vbaVarTstEq x7, __vbaPut3 x4, __vbaVarSub x2, __vbaVarAdd x2, __vbaFileOpen x1, __vbaLenBstr x1
- Form variables used: g x7, coach x4, tn1 x3, tn2 x3, g2 x2, kp x1
- Files opened: footbal1.dat (Binary Write)
- String classes: SPEECH-FRAGMENT 5, KEY-CODE-OR-NUMBER 4, TEAM-CHOICE-PROMPT 3, FILE-NAME 1

### p_4311a0 GetCoach (slot 50, offset 0x944)
- Role [CODE (lifted)]: GetCoach: clk, getter(" Enter the name of your coach "), ccn, coach = r; say5(" is, <coach>, correct for the name of your coach? ") then the current answer (say2 yes or no, starts as yes); Up, Down toggle and speak the answer, Enter takes the current answer (no = ask the name again), y accepts, n asks the name again, F1 and any other key (echoed first) ask the confirmation again. Called once, at a new season. Read in full (S3.3).
- Size: 816 bytes, 255 assembly lines. Status: done.
- Calls (form procedures): say2 x2, ccn x1, clk x1, getkey x1, getter x1, say5 x1, saykey x1
- Called by: Form_Load x1
- Main runtime calls: __vbaStrCmp x6, __vbaVarTstEq x3, __vbaStrCat x2
- Form variables used: g x4, g2 x2, coach x2, r x1
- String classes: SPEECH-FRAGMENT 5, KEY-CODE-OR-NUMBER 4, COACH-PROMPT 2

### p_4314d0 Getqbs (slot 51, offset 0x948)
- Role [CODE (lifted)]: Getqbs: names of the two quarterbacks (Me.m2b8(1) own, Me.m2b8(2) opponent). Own: when footplay.txt was valid (gpn <> 0) it is read with Input # until the end of the file and its last item is the own quarterback; otherwise getter(" <coach> enter the name of your quarter back or press enter "), cqn, an empty answer draws a random unused surname from Me.m278 (Int(Rnd * 1708) + 1 until the slot is not empty), say5 confirmation with yes/no, accepted names are blanked in the pool and appended to footplay.txt ("Quarterback:" and the name). Opponent (unless a saved game is loaded): the same with " enter the name of the <team> quarter back or press enter ", not written to a file. Called once per game by pag. Read in full (S3.3).
- Size: 3328 bytes, 950 assembly lines. Status: done.
- Calls (form procedures): say2 x4, cqn x2, getkey x2, getter x2, say5 x2, saykey x2
- Called by: pag x1
- Main runtime calls: __vbaStrCmp x18, __vbaStrCat x12, __vbaVarTstEq x8, rtcLowerCaseBstr x4, rtcRandomNext x2, __vbaFPInt x2, __vbaVarTstGt x2, __vbaFileOpen x2
- Form variables used: r x10, g x8, g2 x4, tn3 x2, tn4 x2, kp x2, coach x1, gpn x1, SavedGame x1
- Files opened: footplay.txt (Append); footplay.txt (Input)
- String classes: QB-NAME-PROMPT 7, SPEECH-FRAGMENT 6, KEY-CODE-OR-NUMBER 4, FILE-NAME 1

### p_4321d0 GetTeams (slot 52, offset 0x94c)
- Role [CODE (lifted)]: GetTeams: sets Me.m294(tn1 + 9 * tn2) to the 32 team nicknames: tn1 = division 1 to 8 (AFC North, East, West, South, NFC North, East, West, South), tn2 = team 1 to 4 inside the division (alphabetical by city; S5.2 correction: alphabetical by nickname, not by city); slots with tn1 = 0 or tn2 = 0 are not used. Called once at start-up. Read in full (S3.3).
- Size: 656 bytes, 174 assembly lines. Status: done.
- Calls (form procedures): none
- Called by: pog x1, Form_Load x1
- Main runtime calls: none
- String classes: TEAM-NAME 32

### p_432460 SetPlayerNames (slot 53, offset 0x950)
- Role [CODE (lifted)]: SetPlayerNames: sets Me.m278(1 to 1708) to the 1,708 roster surnames (index = byte offset / 4) and does nothing else. Extracted by script into spec/SURNAMES.tsv (work/extract_surnames.py: count, order, no duplicates, same set as the string table). Called once at start-up; Getqbs draws default quarterback names from it, pag the roster names (blanked when used). Read (S3.3, by script).
- Size: 32464 bytes, 6875 assembly lines. Status: done.
- Calls (form procedures): none
- Called by: Form_Load x1
- Main runtime calls: none
- String classes: SURNAME 1708

### p_43a330 kicksnap (slot 54, offset 0x954)
- Role [CODE (lifted)]: kicksnap (snap count before a field goal, punt or extra point): Randomize Timer, qorp = 2 (the punter voice of the kicking side speaks), c2uf (crowd 2 up to full), say3 " hut 1 ", rady; with 2 in 3 " hut 2 " and rady, then with 1 in 2 " hut 3 " and rady; then 1 to 3 times " hut" (" hut!" with 1 in 3) with rady; rady, say3 " hike! ", qorp = 1. Called by pag for the field goal, the punt and the extra point. Read in full (S3.4).
- Size: 1328 bytes, 391 assembly lines. Status: done.
- Calls (form procedures): say3 x5, rady x5, c2uf x1
- Called by: pag x3
- Main runtime calls: rtcRandomNext x4, __vbaFPInt x4, __vbaVarTstEq x3, rtcGetTimer x1, rtcRandomize x1, __vbaVarForInit x1, __vbaStrCat x1, __vbaVarForNext x1
- Form variables used: qorp x2
- String classes: SNAP-CALL 4, SPEECH-FRAGMENT 2

### p_43a860 pag (slot 55, offset 0x958)
- Role [CODE (lifted)]: pag, the game: set-up (GoSub 0x453eac: team names, play menus, footplay.txt, rosters, 30 to 37 plays per quarter, clock values), football.sav load, Getqbs, coin toss, kick-off and receive choice, the play loop (offense menu of 8, defense menu of 7, the computer's play choice and fourth-down rules, snap count, 5 x 6 outcome table of runs and passes, sacks, interceptions, fumbles, field goals, punts, kick-off returns, touchdowns, extra point and two-point try, safety, downs and field position), quarter ends, two-minute warnings, half time, overtime (sudden death), stats after each quarter, end of game (final score, Super Bowl), Save Game (writes football.sav) and quit-and-concede (Esc). Read in full: the main body (0x43a860 to 0x451b57) in S3.4 (GAME_SPEC 4.14 to 4.18, 5.5 to 5.12) and its eight GoSub routines in S3.5: hand-off phrases 0x451b58 and drop-back phrases 0x4528c8 (GAME_SPEC 5.9), set-up and rosters 0x453eac (5.5, 11), two-minute whistle 0x458aa5, F1 position 0x458b24 (4.15), the 142 banter lines 0x45915e (5.13), quarter statistics 0x45d0be and key wait 0x45f30f (4.19). Called once, from Form_Load.
- Size: 158960 bytes, 32992 assembly lines. Status: done.
- Calls (form procedures): say4 x71, say2 x57, rady x35, play x21, PlayTackle x18, say5 x18, dy x10, c2df x9, getkey2 x7, saykey x6, inrep x6, clk x5, say3 x5, SayScore x5, c2dh x4, say x4, sgc x4, c2uh x3, c2uf x3, PlayNoise x3, kicksnap x3, superbowl x3, getkey x2, PlayHike x1, play2 x1, playcel x1, GetSexOf x1, SayFinalScore x1, stopspeech x1, Getqbs x1, halftime x1
- Called by: Form_Load x1
- Main runtime calls: __vbaVarTstEq x408, __vbaStrCat x403, rtcRandomNext x87, __vbaStrCmp x79, __vbaVarAdd x68, __vbaFPInt x68, __vbaGosub x49, __vbaVarForInit x46
- Form variables used: g x47, g2 x10, coach x6, kp x4
- Files opened: football.sav (Binary Read); footplay.txt (Input); footplay.txt (Output); football.sav (Binary Write)
- String classes: ANNOUNCER-BANTER 196, SPEECH-FRAGMENT 40, PUNT-AND-KICKOFF-PHRASE 39, RUN-AND-TACKLE-PHRASE 34, PASS-AND-CATCH-PHRASE 33, HANDOFF-AND-FAKE-PHRASE 26, SCORING-AND-FIELD-POSITION 25, SNAP-PHRASE 22, FIELD-GOAL-PHRASE 16, PLAY-MENU 15, KEY-CODE-OR-NUMBER 13, COIN-TOSS 12, STATS-AND-SAVE 12, RUN-DIRECTION-PHRASE 7, ROSTER-HEADING 5, SNAP-CALL 4, QUARTER-MARKER 4, PLAY-PROMPT 4, WAV-NAME 4, GAME-END 3, FILE-NAME 2, SAVED-GAME 2, STAT-LABEL 2, CLOCK-SPEECH 1

### p_461550 p2ct (slot 56, offset 0x95c)
- Role [CODE]: p2ct: an empty Sub with one argument (prologue, epilogue, nothing else). No caller anywhere: dead code. Read in full.
- Size: 96 bytes, 39 assembly lines. Status: done.
- Calls (form procedures): none
- Called by: nobody (no call site found)
- Main runtime calls: none

### p_4615b0 pog (slot 57, offset 0x960)
- Role [CODE (lifted)]: pog, the season engine (called by Form_Load after a game that was not saved, when gtp is not 0): ptf = 1, ilc = 0, the score table of 32 entries (0, 0, 3, 3 ... 49, 51), the player's game result from Me.m414 (a tie goes to the opponent). Regular week (gtp 1 to 16): reads footbal3.dat, says " Games of week number <n>. ", the player's game and 15 other games with random pairings and table scores ("<winner> over the <loser> by the score of <w>, to <l>. ", say2), gtp + 1, writes footbal3.dat, waits (F1 or F2 speak the 17 lines again). After week 16: division winners (fewest losses, the player wins a tie), wild cards (two per conference, the player wins a tie for the second), seeds by wins (fewest first; the two with the most wins get byes), writes footbal4.dat (4 wild card games) and footbal5.dat (4 bye teams); then the player in a wild card game: gtp 17; with a bye: the wild card games simulated, footbal4.dat for the division round, gtp 18; out: " ... did not make it into the playoffs. " and finplay17 (gtp 0, football.gtp not written). Play-off weeks (gtp 17 to 20): the round's results (the player's from Me.m414, the others a coin flip with table scores; three sentence slips, Q46), footbal4.dat for the next round, a wait with instant replay (norep = 1); the player won: gtp + 1 written; lost: gtp = next round, finplay17, gtp 0 written. Writes football.gtp at the end of every path except "out". Read in full (S3.6; GAME_SPEC 5.14 to 5.16).
- Size: 115456 bytes, 23770 assembly lines. Status: done.
- Calls (form procedures): say4 x31, getkey x8, inrep x7, clk x6, k4 x5, say2 x4, finplay17 x4, GetTeams x1
- Called by: Form_Load x1
- Main runtime calls: __vbaStrCat x310, rtcStrFromVar x81, __vbaGet3 x80, __vbaVarAdd x71, __vbaPut3 x71, __vbaVarTstEq x58, __vbaVarCmpEq x52, rtcRandomNext x48
- Form variables used: kp x19, g x16
- Files opened: footbal3.dat (Binary Read); footbal3.dat (Binary Write); footbal3.dat (Binary Read); footbal4.dat (Binary Write); footbal5.dat (Binary Write); footbal4.dat (Binary Read); footbal5.dat (Binary Read); footbal4.dat (Binary Read); footbal5.dat (Binary Read); footbal4.dat (Binary Write); footbal4.dat (Binary Read); footbal5.dat (Binary Read); footbal4.dat (Binary Write); footbal4.dat (Binary Read); footbal4.dat (Binary Write); footbal4.dat (Binary Read); footbal4.dat (Binary Write); football.gtp (Binary Write)
- String classes: SEASON-RESULTS-SPEECH 14, DIVISION-NAME 8, SPEECH-FRAGMENT 7, FILE-NAME 5, KEY-CODE-OR-NUMBER 2

### p_47d8b0 finplay17 (slot 58, offset 0x964)
- Role [CODE (lifted)]: finplay17, the play-off engine for the rounds without the player (called by pog when the player's team is out after week 16, gtp 17, or has just lost a play-off game, gtp = the next round 18, 19 or 20): ilc = 0, ptf = 1, the same score table, 0.2 s, Randomize Timer, On gtp - 16 GoTo the round (1 wild card, 2 division, 3 championship, 4 Super Bowl; table at 0x484848), then every later round: the headings (" In the A. F. C. Division play off games. " with a capital D, " In the A. F. C. Championship game. ", " In the Super Bowl. " ...), every game a coin flip (Int(Rnd * 2) + 1) with table scores (winner not 0, loser lower), say4 " The <winner> won over the <loser> by the score of <w> to <l>. ", footbal4.dat for the next round (with the bye teams of footbal5.dat after the wild card round), a wait with instant replay (norep = 1) after each round; after the Super Bowl 0.2 s and 8 to 15 celebration sounds (foot15 to foot24, -300 + wavol, random pitch, at least 8000 Hz; again after a 5 s pause when F1 or F2 replays), then gtp = 0 (the season is over). Read in full (S3.6; GAME_SPEC 5.17; the three moves of the lift report and eight more are the winner's team of each game, lifted per path since the lifter fix B-P30).
- Size: 28592 bytes, 6742 assembly lines. Status: done.
- Calls (form procedures): say4 x18, getkey x4, inrep x4, k4 x3, dy x2
- Called by: pog x4
- Main runtime calls: __vbaStrCat x188, __vbaGet3 x52, rtcStrFromVar x45, rtcRandomNext x36, __vbaFPInt x36, __vbaVarTstEq x34, __vbaPut3 x28, rtcRightTrimBstr x22
- Form variables used: g x8, norep x8, kp x8, ilc x4, gtp x2, ptf x2
- Files opened: footbal4.dat (Binary Read); footbal5.dat (Binary Read); footbal4.dat (Binary Write); footbal4.dat (Binary Read); footbal4.dat (Binary Write); footbal4.dat (Binary Read); footbal4.dat (Binary Write); footbal4.dat (Binary Read)
- String classes: SEASON-RESULTS-SPEECH 5, PLAYOFF-RESULTS-SPEECH 4, WAV-NAME 3, SPEECH-FRAGMENT 3, FILE-NAME 2, KEY-CODE-OR-NUMBER 2

### p_484860 superbowl (slot 59, offset 0x968)
- Role [CODE (lifted)]: superbowl (end of the Super Bowl game): ilc = 0, ptf = 1; when the player won (Me.m414(1) > Me.m414(2)) say4 " The <own team> have Won the super Bowl!  They beat the <opponent> by the score of <a>, to <b>. ", 8 to 15 random celebration sounds (foot15 to foot24, -300 + wavol, random pitch, at least 8000 Hz) and foot25 (play 25); otherwise the same sentence with the opponent as the winner and no foot25; then 8 to 15 more celebration sounds; getkey: F1 or F2 start the whole presentation again, any other key ends it with gtp = 42 (pag then sets gtp = 0, the season is over). Called twice by pag at the end of a Super Bowl game (before and after the final stats, quirk), the third call site is unreachable. Read in full (S3.4, for its effect on gtp).
- Size: 4896 bytes, 1304 assembly lines. Status: done.
- Calls (form procedures): say4 x2, play x1, getkey x1
- Called by: pag x3
- Main runtime calls: __vbaStrCat x26, rtcStrFromVar x6, rtcTrimBstr x6, rtcRandomNext x6, __vbaFPInt x6, __vbaVarAdd x4, __vbaVarForInit x2, __vbaNew2 x2
- Form variables used: g x2, tn1 x2, tn2 x2, tn3 x2, tn4 x2, wavol x2, ilc x1, gtp x1, ptf x1
- String classes: WAV-NAME 3, KEY-CODE-OR-NUMBER 3, SPEECH-FRAGMENT 3, SUPERBOWL-SPEECH 2, SEASON-RESULTS-SPEECH 1

### p_485b80 halftime (slot 60, offset 0x96c)
- Role [CODE (lifted)]: halftime: Randomize Timer, play("0", 0) (foot0), then 15 celebration sounds (the count Int(Rnd * 10) + 10 is drawn and then overwritten with 15): each a random foot15 to foot24 at -300 + wavol, frequency original + 100 * k (k = Int(Rnd * 40) - 20, never 0), at least 8000 Hz, waited to its end; then play("0", 0) again. Called once by pag at the end of the second quarter. Read in full (S3.4).
- Size: 2160 bytes, 586 assembly lines. Status: done.
- Calls (form procedures): play x2
- Called by: pag x1
- Main runtime calls: __vbaStrCat x4, rtcRandomNext x3, __vbaFPInt x3, __vbaVarAdd x2, rtcGetTimer x1, rtcRandomize x1, __vbaVarForInit x1, rtcStrFromVar x1
- String classes: WAV-NAME 3, KEY-CODE-OR-NUMBER 1

### p_4863f0 inrep (slot 61, offset 0x970)
- Role [CODE (lifted)]: inrep (F2, instant replay): loads the announcer voice when needed, speaks ' here's the instant rea play ' (unless norep <> 0), waits 0.2 s, then speaks asynchronously every line of the replay list Me.m44c(1 to ilc) until the line equals ' <coach> select your play '. Read in full (S3.2). pag empties the list (ilc = 0) at every snap, field goal, punt, kick-off, extra point choice and quarter stats, so F2 replays the play in progress or the last one; pag sets norep = 1 only while the quarter stats wait for a key (S3.4).
- Size: 1440 bytes, 485 assembly lines. Status: done.
- Calls (form procedures): dy x1
- Called by: pog x7, pag x6, finplay17 x4
- Main runtime calls: __vbaVarTstEq x2, __vbaStrCat x2, __vbaNew x1, __vbaVarForInit x1, __vbaStrCmp x1, __vbaVarForNext x1
- Form variables used: anv x3, vr x1, ilc x1, coach x1, norep x1, LastVoice x1
- String classes: REPLAY-PROMPT 2, SPEECH-FRAGMENT 1

### p_486990 Form_Load (slot 63, offset 0x978)
- Role [CODE (lifted)]: Form_Load: the whole program runs from here as one synchronous procedure, with DoEvents in the waits. Start-up (window, DirectSound, voice check, data folder, sounds, names and teams, first-run welcome and voice choice, files), new season (coach, team, schedule), the week loop (week and game announcement, main menu 1 play game, 2 schedule, 3 standings, 4 exit), and the exit. Choice 1 runs pag and pog and standings and then the EXIT (the program plays one game per run); choices 2 and 3 return to the week loop. Read in full (S3.1, S3.3).
- Size: 17328 bytes, 4479 assembly lines. Status: done.
- Calls (form procedures): say2 x10, dy x5, say x3, clk x2, getkey x2, SayStand x2, getkp x1, cofs x1, crowd1 x1, crowd2 x1, MakeHike x1, MakePlayNoise x1, play x1, speckeys x1, ChangeVoice x1, stopspeech x1, saykey x1, SayScedual x1, makes x1, ChooseTeam x1, GetCoach x1, GetTeams x1, SetPlayerNames x1, pag x1, pog x1
- Called by: nobody (event handler, called by the runtime)
- Main runtime calls: __vbaStrCat x52, __vbaVarTstEq x27, __vbaStrCmp x25, __vbaGet3 x25, rtcDir x13, rtcLowerCaseBstr x13, __vbaFileOpen x12, __vbaPrintFile x11
- Form variables used: kp x21, tn3 x9, tn4 x9, g x8, tn1 x8, tn2 x8, SavedGame x5, g2 x4, coach x4, gtp x4, vtrnt x4, anv x3, wavol x3, vr x2, nv x2, crwd1 x2, LastVoice x2, ptf x2, nov x1, comtog x1, qorp x1
- Files opened: football.vol (Binary Read); footbal0.dat (Binary Read); footbal1.dat (Binary Read); footbal1.dat (Binary Read); football.gtp (Binary Write); football.gtp (Binary Read); footballlog.txt (Output); footballlog.txt (Append); football.gtp (Binary Read); footbal2.dat (Binary Read); footbal4.dat (Binary Read); footbal3.dat (Binary Read)
- String classes: MENU-AND-EXIT-TEXT 21, FILE-NAME 16, KEY-CODE-OR-NUMBER 9, SCHEDULE-SPEECH 5, SPEECH-FRAGMENT 4, WAV-NAME 3, COMMENTS-TOGGLE 1, SAVED-GAME 1, SCORING-AND-FIELD-POSITION 1

## 4. Public variables of the form (34)

Declared at module level of Form1 (VB member table at 0x41b8b0, 34 entries with name, dispatch id, accessor offset and instance offset). Offsets are inside the form instance; a 4-byte slot is a String (or Long), a 16-byte slot a Variant (the type is a guess from the slot size). Use lists come from register tracking (INFERRED: they may miss uses through other registers). The role column is a GUESS from the name and the uses unless it says CODE; each is confirmed or corrected in P3 (S5.2: done; every row of this table says CODE since S3.4, Q-022 answered, no role is left as a guess).

| name | offset | size | used by (procedures, count) | likely role |
|---|---|---|---|---|
| g | 0x34 | 4 | play2 x1, readins x8, speckeys x3, SayHints x3, ctog x1, adjvol x9, adjrate x3, ChangeVoice x20, clk x1, getkey x1, getkey2 x1, getter x4 ... | last key code as text (set by Form_KeyDown, cleared by clk) [CODE] |
| g2 | 0x38 | 4 | ChangeVoice x10, clk x1, getter x4, saykey x1, Form_KeyDown x2, SayScedual x2, ChooseTeam x2, GetCoach x2, Getqbs x4, pag x10, Form_Load x4 | last key as lower-case character [CODE] |
| vr | 0x3c | 16 | adjvol x2, adjrate x4, say x1, say2 x1, say3 x1, say4 x1, say5 x1, saykey x1, rady x1, inrep x1, Form_Load x2 | speech rate of the SAPI voices (Voice.Rate); adjrate changes it by 1, footbal0.dat; also divides the random pause rady [CODE] |
| nv | 0x4c | 16 | Form_Load x2 | index of the SAPI voice used first at start-up (always 0; footbal0.dat then supplies the announcer voice) [CODE (lifted, S3.3)] |
| nov | 0x5c | 16 | Form_Load x1 | number of SAPI voices minus 1, the highest voice index; the voice choice does nothing when it is 0 [CODE] |
| r | 0x6c | 4 | ccn x5, cqn x5, getter x5, GetCoach x1, Getqbs x10 | typed text (getter fills it, ccn and cqn clean it) [CODE] |
| anv | 0x70 | 16 | adjvol x2, adjrate x1, say x2, say2 x2, say4 x2, say5 x2, inrep x3, Form_Load x3 | announcer voice number (index in GetVoices) [CODE] |
| ilc | 0x80 | 16 | say2 x1, say4 x1, finplay17 x4, superbowl x1, inrep x1 | number of lines in the replay list Me.m44c (say2 and say4 add one, inrep replays them); pag empties it at every snap, field goal, punt, kick-off, extra point choice and quarter stats; pog at its start, before the division winners and at every play-off week; finplay17 at its start and at every round [CODE (lifted, S3.6)] |
| coach | 0x90 | 4 | SayScedual x1, ChooseTeam x4, GetCoach x2, Getqbs x1, pag x6, inrep x1, Form_Load x4 | coach name (ccn result, footbal1.dat) [CODE (lifted, S3.3)] |
| tn1 | 0x94 | 16 | SayScore x2, SayFinalScore x2, SayScedual x3, ChooseTeam x3, superbowl x2, Form_Load x8 | division 1 to 8 of the player's team (1 AFC North, 2 AFC East, 3 AFC West, 4 AFC South, 5 NFC North, 6 NFC East, 7 NFC West, 8 NFC South); an Integer Variant [CODE (lifted, S3.3)] |
| tn2 | 0xa4 | 16 | SayScore x2, SayFinalScore x2, SayScedual x3, ChooseTeam x3, superbowl x2, Form_Load x8 | team 1 to 4 inside the division (alphabetical by city; S5.2 correction: by nickname, not by city) of the player's team [CODE (lifted, S3.3)] |
| tn3 | 0xb4 | 16 | SayScore x2, SayFinalScore x2, Getqbs x2, superbowl x2, Form_Load x9 | division of this week's opponent (from footbal2.dat, or footbal4.dat in the play-offs) [CODE (lifted, S3.3)] |
| tn4 | 0xc4 | 16 | SayScore x2, SayFinalScore x2, Getqbs x2, superbowl x2, Form_Load x9 | team inside the division of the opponent [CODE (lifted, S3.3)] |
| gtp | 0xd4 | 16 | SayStand x2, SayScedual x2, finplay17 x2, superbowl x1, Form_Load x4 | week 0 to 20: 1 to 16 regular season, 17 wild card, 18 division, 19 division championship, 20 super bowl week; 0 = season over; file football.gtp (an Integer Variant). Set: Form_Load 1 at a new season; pog + 1 after every regular week and every play-off week the player won, 18 directly after week 16 when the player has a bye, 18, 19 or 20 before finplay17 when the player lost; finplay17 0 at its end (the player out or beaten); pag 0 after a Super Bowl game (superbowl sets 42). pog writes football.gtp at the end of every path except when the player is out after week 16 (then 0 only in memory; the exit deletes the season files) [CODE (lifted, S3.6)] |
| wisoff | 0xe4 | 16 | say3 x1 | side on offense in the game (1 = the player's team, 2 = the opponent; the kicking team is the other one, local L504); also the side whose quarterback or punter voice say3 uses; saved first in football.sav [CODE (lifted, S3.4)] |
| norep | 0xf4 | 16 | finplay17 x8, inrep x1 | replay switch: not 0 = inrep skips its introduction; pag sets 1 only while the quarter stats wait for a key; pog and finplay17 set 1 around every wait after their say4 lines (F1 or F2 replay without the introduction) and 0 after it [CODE (lifted, S3.6)] |
| crwd1 | 0x104 | 16 | adjvol x1, Form_Load x2 | nominal volume of crowd 1: -1200 in the menus (Form_Load), -100 from the start of a game (pag 0x43b8fe; crowd 1 is set to -100 + wavol there); adjvol applies crwd1 + wavol [CODE (lifted, S3.4)] |
| comtog | 0x114 | 16 | ctog x2, adjvol x1, Form_Load x1 | comments toggle: 1 = comments OFF [CODE] |
| vtrnt | 0x124 | 16 | Form_Load x4 | home flag of this week's game: 1 = the player's team is at home (the opponent is named first and the computer calls the coin toss), 2 = the player's team is the visitor and calls the toss; from footbal2.dat, or footbal4.dat in the play-offs; pag reads it only at the coin toss [CODE (lifted, S3.4)] |
| st4 | 0x134 | 16 | PlayRan x1, getkey2 x1 | Timer value of the next ambient sound (getkey2 sets Timer + 5, PlayRan Timer + 3 to 10) [CODE] |
| LastVoice | 0x144 | 16 | say x1, say2 x1, say3 x2, say4 x1, say5 x1, inrep x1, Form_Load x2 | number of the voice loaded into Voice (cache; 2005 forces a reload) [CODE] |
| qorp | 0x154 | 16 | say3 x1, kicksnap x2, Form_Load x1 | say3 selector: 1 = quarterback voice (the snap count of a play), 2 = punter voice (kicksnap sets 2 for the snap count of a kick and 1 again at its end) [CODE (lifted, S3.4)] |
| wavol | 0x164 | 16 | c2uh x1, c2uf x1, c2dh x1, c2df x1, PlayHike x1, PlayNoise x1, play2 x1, playcel x1, ctog x1, adjvol x7, superbowl x2, Form_Load x3 | sound volume offset added to every sound volume, 0 to -5000 in steps of 100 (F11 part 2) [CODE] |
| oldtime | 0x174 | 16 | sgc x1 | play counter of the last clock calculation; sgc recomputes minutes and seconds only when it changes (Empty at start equals 0) [CODE (lifted, S3.3)] |
| mins | 0x184 | 16 | sgc x5 | minutes shown by the clock (Double from Int) [CODE (lifted, S3.3)] |
| secs | 0x194 | 16 | sgc x5 | seconds shown by the clock, with a random jitter [CODE (lifted, S3.3)] |
| CountDown | 0x1a4 | 16 | sgc x5 | divisor of the clock formula: 100 at the start of the game and of every quarter and overtime (pag's set-up and stats routine), raised by M2W, M4W or M5W per new play near the two-minute warning, then 125, 170 or 215; saved in football.sav [CODE (lifted, S3.4)] |
| M2W | 0x1b4 | 16 | sgc x1 | plays from the two-minute warning to the end of quarter 2: Int(Rnd * 3) + 5 (5 to 7), drawn by pag at the start of every game (also a loaded one, so a saved game can get a different value); the warning comes when the play counter equals plays in the quarter - M2W [CODE (lifted, S3.4)] |
| M4W | 0x1c4 | 16 | sgc x1 | the same for quarter 4 [CODE (lifted, S3.3)] |
| M5W | 0x1d4 | 16 | none found | the same for overtime (quarters 5 to 10) [CODE (lifted, S3.3)] |
| gpn | 0x1e4 | 16 | Getqbs x1 | footplay.txt was found and read (1) or has to be created (0): set by pag's set-up before Getqbs (pag sets 0 at the start of every game and 1 when the file exists, and 0 again when a heading of the file is wrong, S3.5); Getqbs reads the own quarterback from the file when it is not 0 [CODE (lifted, S3.4)] |
| SavedGame | 0x1f4 | 16 | Getqbs x1, Form_Load x5 | 1 = football.sav exists (Form_Load) or the game was just saved (pag Save Game, then Form_Load skips the season engine and ends); pag sets it to 0 after loading and deleting the saved game [CODE (lifted, S3.4)] |
| kp | 0x204 | 4 | getkp x1, cofs x10, ctog x1, adjvol x1, adjrate x1, ChangeVoice x1, SayStand x1, k4 x1, SayScedual x2, makes x1, ChooseTeam x1, Getqbs x2 ... | data folder path: Documents\kitchensinc (current folder when the Documents folder cannot be found) [CODE (lifted, S3.3)] |
| ptf | 0x208 | 16 | say x1, say2 x1, say4 x1, say5 x1, say6 x1, SayFinalScore x1, SayStand x2, finplay17 x2, superbowl x1, Form_Load x2 | speech log flag: 1 = every speaker also writes footballlog.txt; pog and finplay17 set 1 at their start (all season and play-off results are logged), Form_Load sets 0 after pog [CODE (lifted, S3.6)] |

## 5. Private fields of the form (not in the member table)

Offsets inside the form instance, found while reading the lifted code (S3.1 to S3.3); the other private arrays of the play engine are named in their batches.

| field | role | evidence |
|---|---|---|
| Me.m218 | DirectX8 object (Form_Load) | CODE (lifted) |
| Me.m21c | DirectSound object | CODE (lifted) |
| Me.m220 | one-shot sound buffer (also the intro music) | CODE (lifted) |
| Me.m224 | crowd 1 buffer (foot1, looping) | CODE (lifted) |
| Me.m228 | crowd 2 buffer (foot2, looping) | CODE (lifted) |
| Me.m22c | hike sound buffer (foot3) | CODE (lifted) |
| Me.m230 | ambient sound buffer (PlayRan; pag creates it with foot9 at the game start) | CODE (lifted) |
| Me.m234 | tackle sound buffer | CODE (lifted) |
| Me.m238 | play noise buffer (foot14, looping) | CODE (lifted) |
| Me.m23c / Me.m240 | DirectSound buffer description and its flags (224) | CODE (lifted) |
| Me.m278 | String array 0 to 1708: the roster surname pool (index 1 to 1708 from SetPlayerNames; names are blanked when used) | CODE (lifted, S3.3) |
| Me.m294 | String array (0 to 8, 0 to 4): team nicknames at index tn1 + 9 * tn2 (GetTeams) | CODE (lifted, S3.3) |
| Me.m2b8 | String array: quarterback names, 1 = the player's, 2 = the opponent's (Getqbs; football.sav keeps the opponent's as length and character codes) | CODE (lifted, S3.3) |
| Me.m2d4 / Me.m2f0 | quarterback and punter voice numbers of side 1 and 2 | CODE (lifted) |
| Me.m30c | the five voice volumes | CODE (lifted) |
| Me.m328, Me.m34c, Me.m370, Me.m394, Me.m3b8 | player names by position, index 3 * n + side: running backs (6), receivers (6), defensive players (17), special teams players (2), kickers (2); side 1 is read from or written to footplay.txt by pag, side 2 is drawn from the surname pool at every game (S3.5, GAME_SPEC 5.5 and 11); stored as 2-D arrays (side, number), index side + 3 * n | CODE (lifted, S3.3 and S3.5, pag 0x4544e1 to 0x458a9f) |
| Me.m414 | Variant array 1 to 2: the final score of the player's team (1) and the opponent (2), set by pag at the end of the game (when the player concedes: 0 for the player and at least 1 for the opponent unless the player was already behind); read by pog (the week's result: the player wins only when (1) > (2), a tie goes to the opponent; also the play-off result sentence) and superbowl | CODE (lifted, S3.6) |
| Me.m44c | the replay list (say2 and say4 lines, ilc entries) | CODE (lifted) |
| Me.m468 | the words He or She of the four player voices | CODE (lifted) |
| Me.m3dc | String array 1 to 10: the words of the quarterback's snap count, " Red ", " Right ", " Blue ", " Left ", " white ", " black ", " green ", " chrome ", " X ", " XP " (set by pag's set-up; spoken with a number 1 to 28 before the hike: the colour words of the string pool) | CODE (lifted, S3.4) |
| Me.m3f8 | String array 1 to 7: run directions: "up the middle", "on the left side", "on the right side" (1 to 3, line plunge), "around the right side", "around the left side", "around the left end", "around the right end" (4 to 7, end run) | CODE (lifted, S3.4) |
| Me.m430 | String array 1 to 2: the team nicknames of this game, 1 = the player's team (Me.m294(tn1 + 9 * tn2)), 2 = the opponent (tn3, tn4); set by pag's set-up | CODE (lifted, S3.4) |
