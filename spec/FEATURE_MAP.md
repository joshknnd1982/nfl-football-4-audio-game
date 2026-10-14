# FEATURE_MAP (nfl4)

P3 S3.1, 2026-10-13; S3.6 (2026-10-14) read the last two procedures (pog and finplay17): all 64 done, Phase 3 complete. Statuses updated in S3.2 (batch 1 of D-021 done: sections 2 to 5, 41 procedures), S3.3 (batch 2 done: sections 1 and 6, 14 more procedures) and S3.4 (batch 3 done: pag's main body, plus kicksnap, halftime and superbowl, which the main body needed) and S3.5 (batch 4 done: pag's eight GoSub routines; 62 of 64 procedures done, only pog and finplay17 unread (S3.6)). The 64 procedures grouped by feature, with their reading volume before and after lifting, their status, and the P3 batch that reads them. Sizes: asm = gap-filled assembly lines (`work/ghidra/`), lifted = lines of `work/lift/<p_addr>_<name>.vb.txt` (`tools/vb6_lift.py`, D-020; numbers from `work/lift/lift_report.md`). Status as in `spec/PROCEDURE_INDEX.md` (done = read in full, partial, unread). Evidence for every role: `PROCEDURE_INDEX.md`; facts found while reading go into `GAME_SPEC.md`.

How to read a batch: open the lifted file next to the asm (`work/ghidra/<p_addr>.asm`; the address at the start of each lifted line is the address of the instruction that does it); trust statements, check anything that matters against the asm; `{a | b}` is a value that differs by path (the compiler shared the tail of an If/Else or Select Case: alternatives in the order forward jumps first, then the fall-through); `Me.mXXX` are private form fields (arrays and DirectSound objects, not in the member table); `obj.vt_XX` is a method of an interface the lifter cannot name yet (DirectX 8 for VB: Q-024); `arg1` is the procedure's first (ByRef) argument; `L<hex>` are local variables named by frame offset. The completeness check in `lift_report.md` (every form call, Open, Close, Get, Put, Print, Kill, For, Shell and Rnd of the asm appears in the lifted text) passes for all 64 procedures.

## 1. Start-up, main menu, exit (batch S3.3, done)
Form_Load holds the whole program; GAME_SPEC section 3 has the structure (S3.1, details and the exit-after-one-game finding S3.3).
| procedure | role | asm / lifted | status |
|---|---|---|---|
| p_486990 Form_Load | start-up, week announcement, main menu loop, exit | 4479 / 491 | done (S3.3) |
| p_41bd80 getkp, p_41bbe0 SpecialFolder | data folder Documents\kitchensinc | 331 / 28 | done (S3.3) |
| p_41c000 cofs | first-run copy of shipped files | 720 / 131 | done (P2) |
| p_461550 p2ct | empty, never called | 39 / 1 | done |

## 2. Keys, waits, typing (batch S3.2)
| procedure | role | asm / lifted | status |
|---|---|---|---|
| p_42e5e0 Form_KeyDown | every key; runs the global-key menus | 240 / 31 | done |
| p_429b40 getkey, p_429c00 getkey2, p_429ac0 clk | key waits, clear key | 212 / 19 | done |
| p_42e880 dy, p_42e980 rady | fixed and random pauses | 253 / 18 | done |
| p_42e3d0 saykey | key echo | 200 / 7 | done |
| p_429d10 getter, p_428f60 ccn, p_429510 cqn | typed names and their checks | 991 / 107 | done (S3.2) |

## 3. Speech and voices (batch S3.2)
| procedure | role | asm / lifted | status |
|---|---|---|---|
| p_42a000 say to p_42b470 say6 | the six speakers (GAME_SPEC 9.1) | 1975 / 79 | done (S3.1, Q-021) |
| p_42e300 stopspeech | purge speech | 85 / 2 | done |
| p_41fb50 GetSexOf | voice gender for He/She | 448 / 21 | done (S3.2) |
| p_4863f0 inrep | instant replay (F2) | 485 / 23 | done (S3.2; the ilc and norep setters in pag found in S3.4) |

## 4. Global-key menus: help and settings (batch S3.2)
All seven end with clk and g = "112" (F1), so the interrupted wait repeats its prompt (Q-023 answered).
| procedure | key | asm / lifted | status |
|---|---|---|---|
| p_420860 speckeys | F5 key list | 280 / 26 | done |
| p_420040 readins | F6 instructions | 753 / 56 | done (S3.2) |
| p_420b50 SayHints | F7 terms and hints | 1130 / 76 | done (S3.2) |
| p_4216b0 ctog | F8 comments toggle | 221 / 25 | done |
| p_421960 adjvol | F11 volumes | 2032 / 155 | done (S3.2) |
| p_4239c0 ChangeVoice | F12 voices (also on the first run) | 5327 / 365 | done (S3.2) |
| p_423530 adjrate | Ctrl speech rate | 415 / 36 | done (S3.2) |

## 5. Sound (batch S3.2, with the DirectX 8 method names, Q-024)
The DirectSound set-up and the intro music are in Form_Load (GAME_SPEC 10).
| procedure | role | asm / lifted | status |
|---|---|---|---|
| p_41c950 crowd1, p_41cbe0 crowd2 | crowd loops foot1, foot2 | 486 / 22 | done |
| p_41ce70 c2uh, p_41d090 c2uf, p_41d240 c2dh, p_41d430 c2df | crowd 2 volume ramps | 641 / 47 | done (S3.2; c2uh never ramps) |
| p_41d620 MakeHike, p_41d940 PlayHike, p_41da90 MakePlayNoise, p_41ddb0 PlayNoise | hike foot3 and play noise foot14 | 809 / 39 | done (S3.2) |
| p_41def0 PlayTackle, p_41e3a0 play, p_41e780 play2 | one-shot sounds by number | 1050 / 60 | done (S3.2) |
| p_41eaa0 playcel, p_41f320 PlayRan | celebration, ambient sounds while waiting | 1152 / 83 | done (S3.2; lifter fix B-P16) |

## 6. Season set-up and reports (batch S3.3, done)
| procedure | role | asm / lifted | status |
|---|---|---|---|
| p_4311a0 GetCoach, p_4314d0 Getqbs | coach and quarterback names | 1205 / 164 | done (S3.3) |
| p_4308e0 ChooseTeam, p_4321d0 GetTeams | team choice, team table | 779 / 118 | done (S3.3) |
| p_432460 SetPlayerNames | 1,708 surnames (data table: extracted by script, spec/SURNAMES.tsv) | 6875 / 1709 | done (S3.3, by script) |
| p_42fa70 makes, p_42eba0 SayScedual | schedule: make and speak | 1904 / 202 | done (S3.3) |
| p_42ce40 SayStand | standings | 1284 / 109 | done (S3.3) |
| p_42b590 SayScore, p_42bab0 SayFinalScore, p_42bfc0 sgc | score and clock speech | 1728 / 181 | done (S3.3) |
| p_42e1f0 k4 | delete footbal4.dat | 96 / 6 | done |

## 7. Play engine (batches S3.4 and S3.5)
| procedure | role | asm / lifted | status |
|---|---|---|---|
| p_43a860 pag, main body (lifted lines 1 to 2281, 0x43a860 to 0x451b57) | coin toss, play loop, play menus, the computer's choice, outcome table, kicks, quarters, overtime, end of game | 19696 / 2278 | done (S3.4; GAME_SPEC 4.14 to 4.19, 5.5 to 5.12) |
| p_43a860 pag, main-body pieces placed after it (lifted 2455 to 2526 end of game and last-play rule, 3738 to 3872 Save Game and concede) | end of game, Save Game, concede | in the line above | done (S3.4) |
| p_43a860 pag, 8 GoSub routines (lifted lines 2282 to 3737 without the pieces above) | hand-off and drop-back phrases (0x451b58, 0x4528c8), set-up and rosters (0x453eac), two-minute whistle (0x458aa5), F1 position (0x458b24), banter (0x45915e), statistics (0x45d0be), key wait (0x45f30f) | 13296 / 1591 | done (S3.5; effects first read in S3.4: GAME_SPEC 4.15, 4.19, 5.5, 5.9, 5.13, 11) |
| p_43a330 kicksnap, p_485b80 halftime | kick snap call, half time | 977 / 73 | done (S3.4) |
| p_484860 superbowl | Super Bowl presentation (moved here from section 8: read in S3.4 for its effect on gtp) | 1304 / 102 | done (S3.4) |

## 8. Season engine and play-offs (batch S3.6)
| procedure | role | asm / lifted | status |
|---|---|---|---|
| p_4615b0 pog | the season engine: the other 15 games of a week, records, division winners, wild cards, seeds and byes, the play-off weeks with the player | 23770 / 1551 | done (S3.6; GAME_SPEC 5.14 to 5.16) |
| p_47d8b0 finplay17 | the play-off rounds without the player, the celebration after a simulated Super Bowl, gtp = 0 | 6742 / 560 | done (S3.6; GAME_SPEC 5.17) |
| p_484860 superbowl | Super Bowl presentation | 1304 / 102 | done in S3.4 (section 7) |

## 9. Files (who reads and writes what)
GAME_SPEC section 12 holds the file table and the formats recovered so far (footbal0.dat, footbal1.dat, footbal2.dat, footbal3.dat, football.gtp, football.vol, footballlog.txt, the season reset at exit, which readers check for the file); footplay.txt is in section 11. football.sav is in GAME_SPEC 12 and the write side of footplay.txt prints the reader's headings and counts (both S3.4). S3.6 completed the list: football.gtp, footbal3.dat, footbal4.dat (the pairings of the coming play-off round) and footbal5.dat (the four bye teams) are in GAME_SPEC 12, and a missing file opened For Binary Access Read is created empty by the VB runtime (no error 53; correction, B-P31). Every file is known (Q-007 answered).

## Notes from S3.2 for the later batches
- The lifter was fixed twice in S3.2 (B-P16): a shared tail with a path-dependent move is now shown as `{ a = x | b = y }` (PlayRan lost a line before), and String array indexes are now element-size 4 (the standings, clock and volume name tables were wrong). Total lifted lines now 10,592. Everything lifted before S3.2 that was read in S3.1 (Form_Load, the six speakers) is unchanged by the diff.
- The lift report now warns about moves it cannot resolve: three remain, all in finplay17 (0x47e837, 0x47eff8, 0x47f7f0: a VarCopy into a field of the form reached through a saved Me pointer). Read those three places in the asm in S3.6.
- Variables whose setters are in the engines: ilc (reset by pag and pog), norep (set 1 and 0 around calls to inrep), crwd1 (-100 set by pag at the game start, -1200 by Form_Load), m230 (ambient buffer created by pag at the start of a game, 0x43aca4), GetSexOf call at the start of pag (0x43aa89). Confirm in S3.4. (Confirmed in S3.4, with the exact places: GAME_SPEC 5.6, PROCEDURE_INDEX section 4.)
- Sound call sites in pag seen in S3.2: play("0", 0) at the game start (0x43ba63), play("2", 0) once, play("7", -1500 or -1200) after kicksnap and PlayNoise, play("12", v) 12 times, play("13", 0) six times and play2("foot13") once in the GoSub routines, PlayTackle(8, 2, 3, L4f0), playcel once (0x44f560); superbowl play("25", 0); halftime play("0", 0) twice. S3.4 and S3.5 tie each to its play situation; the answers go to WAV_EVENT_MAP.md (rerun `work\make_wav_event_map.py` after editing the EV table).

## Notes from S3.3 for the later batches
- Lifter: fixed again in S3.3 (B-P19): two frame-slot constants that differ per path at a loop-back join were dropped (`L24 = L74` in Getqbs, `Me.tn1 = L84` in ChooseTeam; now `{1 | 2}` and `{8 | 1}`), and `Int` was printed `rInt` (also `rAbs`, `rFix`). New check: `py -3.10 -I work\scan_undefined_locals.py work\lift` lists names that are read but never assigned; after the fix 10 remain: eight are false alarms (late-bound call arguments in SpecialFolder, the Show arguments and the MsgBox result in Form_Load, the surname "Lee"), TWO ARE IN pag: `L718` at 0x43f84b (`If L82c <= L718`, a value the lifter did not follow, read the asm around 0x43f800) and `L258` at 0x44f0f2 (`For ... To (L898 / 20 + 1) * L258`, and again at 0x453392). Read those two places in the asm in S3.4 and S3.5.
- pag calls Getqbs at 0x43b899 after loading a saved game and after the footplay.txt GoSub (0x453eac, lifted lines 2535 to 2900, read only as far as the file layout in S3.3). The roster loops there (6 running backs, 6 receivers, 17 defensive players, 2 special teams players, 2 kickers) and the arrays m328, m34c, m370, m394, m3b8 (index 3 * n + side) are for S3.5.
- sgc is called by pag at 0x43e1b9, 0x43eda4, 0x44fafd and 0x45f5a5 with (L738, L2cc(L3c0), L3c0): played plays, plays in the quarter, quarter (S3.4 confirms and says whether play counter 0 can reach the clock at the start of a game). pag sets CountDown = 100 at 0x458416 and 0x45d143 and M2W, M4W, M5W = Int(Rnd * 3) + 5 at 0x4584a8 to 0x458598.
- vtrnt: pag 0x43bb7c skips the coin-toss question when vtrnt = 1; the opponent is named first in that case, so vtrnt = 1 probably means the player is the home team and the visitor calls the toss (S3.4 confirms the meaning of home in play).
- pog (S3.6): footbal3.dat is written in the order read here (wins at +45, losses at +90 confirmed in pog 0x463872 and 0x46412c); when the scores are equal pog gives the win to the OPPONENT (`If m414(1) <= m414(2)` goes to the opponent's win); gtp = gtp + 1 at 0x465da2; where gtp becomes 0 and how a player who is out of the play-offs is handled (Form_Load keeps the old opponent when no footbal4.dat record has the player's team) is S3.6.
- Form_Load exits after one game (GAME_SPEC section 3 step 8): pag must be read for what "save game" and "end of game" do to SavedGame and gtp.

## Notes from S3.4 for the later batches
- Lifter fixed again (B-P22): the GoTo right after a GoSub Return was dropped when other code jumps to it; in pag this was the next-play jump at 0x451b53 (`GoTo L_43cc68`, the end of every play). The lift report's completeness check now also lists every reachable JMP that gave no statement (none left). The rerun changed only that line (pag 3,869 lifted lines, total 10,593). The lint's two pag names are read in the asm: `L718` (0x43f840) and `L258` (0x44f0c1, 0x453392) are frame slots that are never written anywhere in pag, so they are Empty (0): the fourth-down test always keeps the kick (Q15) and both delay loops run 0 times (Q16).
- Checked against the asm: all 63 Rnd draws of the main body (`work/check_rnd_consts.py`, result `work/rnd_check_pag_main.txt`: N and the added constant of every `Int(Rnd * N) + k`), the two play jump tables (`work/dump_jumptables_s34.py`), the yardage formula's operand order (0x44da0a: L548 - L44), the fourth-down constants (41, 40, 2, 5, 3, 4, 9, 25, 20, 14, 7, 30, 8), the plays per quarter (Int(Rnd * 8) + 30, 0x45830c), halftime's 15 sounds (0x485d3b), the gtp 42 tests (0x453a35, 0x453ab2).
- For S3.5 (the GoSub routines, lifted lines 2282 to 3737 without the main-body pieces): 0x451b58 hand-off phrases (L6b4 = L604 * 9 + 1 to 9, L604 0 to 3 never equal to the previous, history L70 of 16; values 10 to 27 add a fake first; uses L31c, L408), 0x4528c8 drop-back phrases (11 per group, 3 groups, history L164 of 16), 0x453eac set-up (footplay.txt read and write, the rosters of both sides and the surname pool blanking, L2cc, the clock values, m3dc, m3f8; the write side's headings and counts are already confirmed), 0x45915e banter (142 lines, history L8b4, L778 = Int(Rnd * 58) + 1 picks a player name from L480 for line 1, foot13 bleeps after lines 69, 72, 75 (twice), 83, 140, line 113 one rate step faster, a second text L708 after the line), 0x45d0be statistics and 0x45f30f key wait (read in S3.4, GAME_SPEC 4.19), 0x458aa5 (PlayTackle 8), 0x458b24 (F1 position, GAME_SPEC 4.15). Also the role of L390 (drawn at every snap, not used by the main body).
- For S3.6: pog uses Me.m414 (the scores pag leaves, conceded games included) and gtp (pag leaves 0 only after a Super Bowl game; after a conceded week-20 game gtp is still 20 and pog runs); finplay17 plays foot<n> files itself (0x4840d9 to 0x48453c); Q-027.

## Notes from S3.5 for the later batches
- Lifter: no change needed this session. Every integer constant of the GoSub routines (lifted lines 2282 to 3737 without 2455 to 2526, 1,384 lines) was checked against the assembly by the new tool `tools\vb6_const_check.py` (hand-off and drop-back 61 constants, set-up 176, F1 14, banter 171, statistics and key wait 44: no mismatch; four apparent misses are the folded `3 * 2` of a two-dimensional index), the 24 Rnd draws of the range by `tools\vb6_rnd_check.py` (0 mismatches), the 142 banter lines and the 26 phrase strings by script (`work\extract_banter_s35.py`, `work\check_phrases_s35.py`). The lint still lists the same 10 names, none new (`L718` and `L258` are pag's two typos, Q15 and Q16).
- Facts found that change what the clone says: the "fake" texts of the hand-off and drop-back sentences are built and then overwritten (never spoken, Q35); the hand-off routine's group test compares a number with a sentence and never rejects (Q34, tested with the VB6 runtime's own comparison, `work\variant_cmp_check.py`); a damaged footplay.txt ends the original in most cases (Q36); the opponent's 33 names are drawn at every game (Q39); the banter is 142 lines with 15 names and 5 bleeps (5.13).
- For S3.6: counted in the lifted text in S3.5: pog uses Me.m414 (13 places), gtp (15) and the team table Me.m294 (75); finplay17 uses Me.m294 (45) and gtp (2) but not Me.m414; neither touches pag's roster arrays (Me.m328 to Me.m3b8), the surname pool Me.m278, Me.m430 or Me.m2b8, and neither plays foot13. finplay17 plays foot<n> files itself (0x4840d9 to 0x48453c); Q-027.

## Notes from S3.6 (the last batch of Phase 3)
- Lifter fixed (B-P30): finplay17 had 11 lines `L158(n) = ?arg` (a move two instructions into a shared tail, with the source register different per path) but the lift report showed only 3 of them (it printed the three most common warnings). The per-path move lifting now replays the MOV and LEA between the join and the move, and the report lists every warning. The diff of the whole lift is exactly those 11 lines (`{ L158(19) = L114 | L158(19) = L144 }`: the winner's team of each game) and the report row; the completeness check passes for all 64 procedures, the lint still lists the same 10 names (none in pog or finplay17).
- Checked by script: 48 + 36 Rnd draws (0 mismatches), 1,014 + 331 constants (every miss explained: folded subscripts of multi-dimensional arrays, subscripts as displacements and zeros in registers in finplay17's optimized code, `work/const_miss_filter_s36.py`), the finplay17 jump table, both 32-entry score tables (equal, `work/score_tables_s36.txt`), all 56 literals against the string table (PASS), all 346 writes of the two sentence variables against the asm (assign or append, `work/check_assign_append_s36.py`, a negative test finds two planted errors), and every spoken sentence on every path (`work/check_sentences_s36.py`): finplay17 is clean, pog has the slips Q46.
- Found by reading the VB6 runtime (msvbvm60.dll) and calling its own open routine: a missing file opened For Binary Access Read is CREATED empty; S3.3's "run-time error 53" for football.gtp, footbal2.dat and footbal4.dat and S3.2's crash with one SAPI voice (Q-025) were wrong and are corrected (GAME_SPEC 12, Q7; D-022, D-024, D-025; B-P31).
- Phase 3 is complete: 64 of 64 procedures done. What P4 needs is in PROJECT_STATE.md (Phase 3 summary).

## Totals and batches
104,410 asm lines; 10,592 lifted lines (9.9 times shorter); 1,709 of them are the surname table (script); after S3.3 the six procedures left unread (pag, pog, finplay17, superbowl, halftime, kicksnap) hold 3,868 + 1,551 + 560 + 102 + 41 + 32 = 6,154 lifted lines. Batches (lifted lines including context already read): S3.2 keys, speech, global-key menus and sound, 1,297; S3.3 start-up, files, season set-up and reports, 1,299 plus the surname script; S3.4 play engine main body, 2,277; S3.5 play engine GoSub routines with kicksnap and halftime, 1,664; S3.6 season engine and play-offs, 2,213 (split into two sessions if it does not fit). After S3.4 (10,593 lifted lines after the B-P22 fix): left are pag's GoSub routines (lifted lines 2282 to 3737 without 2455 to 2526, about 1,385 lines, of which the statistics, key wait, F1 and two-minute routines, about 120 lines, are already read) for S3.5, and pog plus finplay17 (1,551 + 560 = 2,111 lines) for S3.6; superbowl, halftime and kicksnap moved into S3.4.
