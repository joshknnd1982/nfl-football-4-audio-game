# SOUND_DESIGN (nfl4): silent events, system sounds, what the game adds (P4 S4.4, 2026-10-14)

Playbook 7.8 (c) and 5.4. Evidence tags as 5.3. Decisions: D-032 (items 1 to 6); gap register entries G-A5 to G-A7 and G-F6 (changed in this session). The sound files and the places where each plays are in `spec\WAV_EVENT_MAP.md` (all 26 names OWNER-CONFIRMED, section 6); this file decides what is NOT a wav: the silent events, the system sounds of the original and the text it never uses, and what the game adds, which is nothing in play.

## 1. Decisions in short

1. The original is rich in sound: 26 wav files played from 74 calls of its sound procedures (counted in the lifted code: play, play2, PlayTackle, playcel, PlayHike, PlayRan, the crowd starts and ramps), two looping crowd beds under everything, ambient sounds while a key is awaited, an intro and an exit jingle. Every event it leaves without a sound is announced by a spoken sentence of its own, with one exception (a failed two-point try, SE-15, which the spoken score that follows makes clear). The game ADDS NO SOUND to play and no music: every silent event of section 3 stays silent, each with its reason, and section 3 ends with the cues S8.2 could promote if the owner's playtest finds a confusing silence (none is built).
2. The tone generator is not needed. The kit's one generated sound, the 80 ms blip `beep_exit`, stays as the last fallback of the exit beep (same as Brain, tested in the kit). The S7.6 session (generated sounds and music, owner listening round) is dropped from the plan: nothing new is generated: the blip is the one Brain 1.0.3 ships (Brain's own SOUND_DESIGN says it was "not yet heard by the owner"; it plays only when the Windows default sound cannot be played), the README lists it so the owner can veto it, the exit beeps are heard in the S8.2 playtest, and the blip's checks run in S7.2.
3. The original's only non-wav sounds are two `Beep` statements and one message box (section 2). The two beeps are reproduced as the original plays them (G-F6, changed from "not reproduced" in S4.3): at the exit, after "Thank you for playing", two system default sounds 0.1 s apart, then the original sentence " Sorry, but I could not find the Kitchensinc game menu program. ", exactly the branch the original takes when it finds no game menu, which is always the case for the game (D-006) and the same as Brain 1.0.3 (public repository joshknnd1982/my-brain-audio-game, spec\DECISIONS.md 2026-10-12 P4 and P7 S7.3 and its SOUND_DESIGN.md: the same MessageBeep(0) finding, two beeps 0.1 s apart, sound ID `beep_exit`, the generated blip as the last fallback; "Decided by Claude" there, no recorded owner choice).
4. The no-voice message box is left to Windows: the game shows the same kind of box (OK button, no icon), so Windows plays the same system sound.
5. The one text of the original that nothing uses, "Sorry but one or more of the wave files seem to be corrupt", is reused as the spoken notice when a sound file cannot be used (7.7 asks for one short spoken warning): it is the author's own wording for that case (G-A6).
6. The setting "Added sounds" (7.7) is not offered: there are no added sounds to switch. Default for added sounds and added music: none. The music the original has (the intro jingle foot0, looped under the start-up announcements) is original and plays as in the original; the player can silence any original sound with `off` in `sounds.txt` (7.7) or change the level with the sound volume (F11).
7. A crowd-bed gap the original never had to decide is settled: after a game the game restarts both crowd beds when it returns to the week loop (G-A5).

## 2. What the original has, by kind (7.8 (a) to (d) checked)

- ORIGINAL-WAV, 26 files foot0 to foot25: every one is referenced by code (none is unreferenced), every call site is tied to its situation, every name is OWNER-CONFIRMED (WAV_EVENT_MAP sections 2, 5, 6). [CODE, OWNER-CONFIRMED]
- ORIGINAL-TONE (PC speaker, SOUND, PLAY or BEEP tones): NONE. The exe imports only MSVBVM60.DLL (pefile), has no `Declare` of a tone or sound API (no kernel32, user32 or winmm string in either string dump), and Visual Basic 6 has no SOUND or PLAY statement. [CODE]
- Music strings: none. Music files: none beyond the wavs; the intro jingle foot0 is the only music-like file (a 3.4 s jingle, played once and then looped until the first announcement; played again at the start of each game, at half time and at the exit). [CODE]
- System sound 1, `Beep`, TWO call sites, both in the exit branch of `Form_Load` where `Dir("gamemenu.exe")` finds nothing: 0x48a80f and 0x48a861, each followed by `dy(0.1)` (0.1 s), then `say("Sorry, but I could not find the Kitchensinc game menu program.")` (synchronous), `dy(0.2)`, `Set Voice = Nothing`, `End`. The VB6 runtime's `rtcBeep` is `push 0; call MessageBeep; ret`: the Windows DEFAULT BEEP of the player's sound scheme (MB_OK), volume and sound set belong to Windows, not to the game's sound volume. [CODE; TESTED by disassembly of this PC's msvbvm60.dll, `work\vbrt_beep_s44.py`, output `work\vbrt_beep_s44.txt`; the same fact is in the kit as `SystemBeeper`]
- System sound 2, `MsgBox` (style 0: OK button, no icon), ONE call site, 0x486f15: the "no voice" message ("Sorry but I couldn't find any voices to use", "Please contact Jim Kitchen"). Windows plays the sound of a plain message box. [CODE]
- Run-time error dialogs (a VB run-time error also plays Windows' error sound): the original has almost no error handling (one `On Error Resume Next`, in `getkp`; D-024 item 5), the game never shows such dialogs (7.10), so there is nothing to reproduce.
- The unreferenced text (string 2568, "Sorry but one or more of the wave files seem to be corrupt", no leading or trailing space): searched in the whole 581,632-byte exe for the address of its characters (0x41a578), its length prefix (0x41a574) and the two neighbors: no reference at all. A dead string, probably meant for an error handler that was never written (the only `On Error` in the 64 procedures is the one in `getkp`, the data-folder lookup, so a wav that cannot be loaded would end the original with a run-time error, INFERRED). [CODE, scripted scan, S4.4]

## 3. Silent events (7.8 (c)): what the player hears now, and the decision

Never truly silent: the two crowd beds (foot1, foot2) loop under every menu and prompt at a quiet level from the first second until a game ends, so "silent" below means no sound of its own for the event. Decision for every item: SILENT (keep), because the original announces the event by a spoken sentence (SE-15 is the one exception, made clear by the score) and no cue was clearly missing; an added sound would change the pace the original players know, could mask speech, and the rule "never change logic or timing for an added sound" would be hard to keep around the 49 pauses that follow a synchronous line (G-S2).

Outside a game
- SE-01 Menu movement (main menu, team choice, yes/no toggles, the voice picker): the new item is spoken. SILENT.
- SE-02 Typing a name: every key is echoed by speech; Backspace speaks the removed character. SILENT.
- SE-03 An invalid or unknown key: its character is echoed and the prompt is spoken again. SILENT.
- SE-04 The week announcement, today's game, the schedule, the standings (after a game also with the crowd beds already stopped): speech only. SILENT.
- SE-05 The help texts (F5 to F7), the comments toggle (F8), the speech rate (Ctrl), the five voice volumes (F11 part 1: the voice itself speaks at its new level, which is the feedback): speech only. The sound volume step of F11 is NOT silent: it plays foot0 as the demo.
- SE-06 The results of the week's other games, the division winners and wild cards, the play-off results with the player (`pog`): speech only, crowd beds off. SILENT.
- SE-07 A season that ends without the player: the rounds are speech only; the celebration sounds play only after a Super Bowl the player's team did not play (8 to 15 sounds, again after F1 or F2). Everything else SILENT.
- SE-08 Added events: the "season is over" notice, damaged-file and sound notices, the F9 menu, the customize and speech settings, the voice picker's sample: speech only. SILENT (no added event needs a cue: each is spoken and the F9 menu is a menu like the others).

In a game
- SE-10 The coin toss (the call, the toss, the result), the receive or kick question, "run the ball out?": speech; while the player thinks, the ambient sounds foot8 to foot10 may play (not silent). SILENT otherwise.
- SE-11 Moving through a play menu and choosing a play: speech. The first sound after Enter is the crowd swell of the snap count. SILENT.
- SE-12 F1 position and down, F2 instant replay, F3 score, F4 clock: speech. The replay repeats the lines and NOT the sounds. SILENT.
- SE-13 First down, down and distance, field position, the gain or loss of a play: speech. SILENT.
- SE-14 A change of possession (turnover on downs, after a kick or a missed field goal, the interception and fumble have foot6 and foot12 before their sentences; S5.2 correction, audit finding A-34: the interception plays foot12, the sentence, crowd 2 down, foot6, and the fumble the sentence, foot6, crowd 2 down, without foot12, both before " the ball is now ...", pag 0x44bfa2 to 0x44c0bd and 0x44de49 to 0x44df12): the sentence "the ball is now ..." and a banter line. SILENT.
- SE-15 A failed two-point try: no sound and no announcement (Q22); the score spoken right after shows that nothing was added. SILENT (kept as original).
- SE-16 The score speech after a score and the key wait that follows: speech (the scoring play itself has its sounds). SILENT.
- SE-17 The quarter statistics and the "press any key" waits: speech; ambient sounds while waiting. SILENT.
- SE-18 The overtime announcement and the overtime kick-off line: speech (the whistle of the fourth quarter's end precedes). SILENT.
- SE-19 The end of a game that is not the Super Bowl: the whistle of the fourth quarter precedes; " THE GAME IS OVER" and the final score are speech and the crowd beds stop. SILENT. (A win or a loss has no sound of its own in the original; only the Super Bowl has the celebration and foot25.)
- SE-20 Save Game: " Game Saved " is spoken, then the program ends (the exit has its jingle). SILENT.
- SE-21 The announcer's banter (142 lines): speech; only five lines have a bleep. SILENT otherwise.

Cues S8.2 could promote if the owner's playtest finds a confusing silence (NOT built, none is expected; each would be a sound ID `added_<name>`, GENERATED, short, quiet, never over speech, from the 7.8 sports palette): a soft chime at a change of possession (SE-14), a low tone at a failed two-point try (SE-15), a short fanfare at the end of a won game (SE-19). The path: S8.2 finds the silence, a listening round of 7.8 follows with `sound_review`, the setting "Added sounds" appears at the same time.

## 4. The game's exit, step by step (G-F6, D-032 item 2)

1. Menu choice 4 (or the end after Save Game, or no voice; S5.2 correction, audit finding A-04: NOT for no voice, that path is G-F9: the message box, speech through a screen reader when one runs, then the end, with no foot0, no thank-you and no beeps; in the original the no-voice jump lands after the deletion, foot0 and the thank-you, Form_Load 0x486f63 to 0x48a5c8): when gtp = 0 the season files are deleted first (G-F3). S7.4b correction (2026-10-15, D-046; the lifted Form_Load decides, GAME_SPEC 3 step 9 already had it right): the crowd beds are NOT stopped here; they play under foot0 and the thank-you (steps 2 and 3 below), and every sound stops only after the thank-you, as the original's release of the DirectSound objects does (0x48a5ed to 0x48a775), before the two beeps. After a game the beds were stopped by pag already; after Save Game they were not (pag does not stop them on that path).
2. foot0 plays once and is waited for (original order: before the thank-you); " Thank you for playing N. F. L. football version 4 By Jim Kitchen " is spoken (waited).
3. `beep_exit` plays, 0.1 s, `beep_exit` plays, 0.1 s. Chain (7.7, the kit's engine): the player's `beep_exit.wav` if there is one, else the Windows default sound (`MessageBeep(0)`, the original's), else the generated 80 ms blip. `beep_exit = off` in `sounds.txt` silences both beeps.
4. " Sorry, but I could not find the Kitchensinc game menu program. " is spoken (waited), 0.2 s, then the end through `finish()` (0.10, 7.2.1). Any key cuts the closing speech short and ends the program at once (B-X13).
5. If S7.5 adds Brain's lookup of `gamemenu.exe` in the game's own folder (Brain does this, DECISIONS P7 S7.3, a decision of Claude there; the kit comments that call it "owner choice 17" are mis-attributed, Brain's owner decision 17 is the numpad digits; D-006 now says the game launches nothing), steps 3 and 4 play only when it is not found and the menu is started instead, exactly as the original branches. Either way the beeps and the sentence belong to the "not found" branch only.
Wrong if: the owner finds the closing sentence odd for a program that never has a game menu: one flag (step 3 and 4 off). Tested by: S8.1 (the exit sequence on the virtual clock: two beeps 0.1 s apart, then the sentence, then the end; the chain with a fake beeper), S8.2 (the owner hears the exit).

## 5. The text of the dead string (G-A6)

When a sound file cannot be used (a player's replacement that is empty or corrupt, or a shipped file that fails to load), the chain falls back to the next choice (7.7) and the game says ONCE per start (the kit already collects such notices and speaks them, `speak_notices`; its wording was only "A sound file could not be used and was skipped, details are in the log."): " Sorry but one or more of the wave files seem to be corrupt " (the author's words) followed by the kit's sentence, so the author's wording is kept and the player still hears what the game did (draft, added to GAP_REGISTER section 8). Which file and why go to the log and to the F9 sounds menu's "check files" result. The text is not used for a sound that is merely missing from the player's folder (that is the normal fall back to the shipped sound). Tested by: S7.2 (corrupt and empty player files for a looped, a one-shot and a waited sound), S8.3 (the damage matrix).

## 6. The sound set the game ships and how a player changes it (7.7)

- Sound IDs: `snd_foot0` to `snd_foot25` (WAV_EVENT_MAP section 2, with the event names intro_music, crowd_bed_1, ... super_bowl) and `beep_exit`.
- Chain: the player's file for the ID (any rate, depth, channels; wav, ogg, flac or mp3 where the library reads them), then the shipped original, then (only `beep_exit`) the Windows default sound and the generated blip, then silence with a log entry. A generated sound is never played together with, before or after the player's file for that ID.
- Slots: the original's seven buffer slots (G-A1: one-shot, crowd 1, crowd 2, hike, ambient, tackle, play noise), plus ONE extra channel that is not an original slot and is never used in play: the previews of the F9 sounds menu and the exit beep (the kit's BEEP_SLOT).
- `sounds.txt` (plain lines, kit format): `snd_foot7 = file=my kick.wav; volume=80`, `snd_foot13 = off`. F9 sounds menu (G-K2): open folder, reload, export the generated blip, reset one or all, preview by name from the list of the 27 IDs; separate saved levels: the sound volume (the original's F11 part 2) and the speech volumes.
- README: how to replace a sound with an example, and the sound notes as short as the names (WAV_EVENT_MAP section 6, B-A10).

## 7. The one generated sound

- `beep_exit`: square wave, 880 Hz, 80 ms, volume 0.35, 2 ms attack and release, 44,100 Hz mono (kit `tonegen`, GENERATED). Only a fallback (section 4 step 3). Automatic checks are in the kit's tests and run again in S7.2: length 80 ms, deterministic samples, exports to a playable wav, the chain player file, then generated, then off. Listening review: no separate round (it plays only when the Windows default sound cannot be played; Brain 1.0.3 ships the same blip and records it as not yet heard by the owner); the README lists it under the sounds so the owner can veto it, and the S8.2 playtest can play it once through the sounds menu preview.
- Research of 7.8 ("start of S7.6"): not needed, no new synthesis; the evidence for the system sounds is the disassembly of section 2.

## 8. What closes this

- S7.2 (audio): the seven slots and the extra channel, the chain for all 27 IDs, `beep_exit`'s chain and checks, the notice of section 5. DONE 2026-10-14 (D-038): built in `game\src\nfl4\audio` and `game\sounds.py` and tested (the slot log on the virtual clock, the mixed samples through SDL's disk driver, the real device at volume 0); the blip's checks pass (80 ms, 880 Hz, peak 0.35, no click, deterministic, exports to a wav); "off" plays nothing and waits nothing (GAP_REGISTER G-A3).
- S7.4 (menus and flow): the exit sequence of section 4, the crowd beds at the return to the week loop (G-A5).
- S8.1: tests of the exit sequence, the chain, the notice.
- S8.2 (owner playtest): the exit sounds right, no silence that confuses (G-A7), the crowd beds are back in the menus after a game.
- S8.3: damaged and corrupt sound files.
