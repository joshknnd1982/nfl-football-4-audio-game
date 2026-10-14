# CUSTOMIZABLE_CONTENT (nfl4): every list a player might change, with the original's limits (P4 S4.5, 2026-10-14)

Playbook 7.9. Purpose: S7.7 builds the customization files from this inventory and a fresh auditor (S5.2) can check that nothing a player could want to change is missing. Evidence tags as 5.3. The lists in sections 3 (teams), 4 (divisions), 5 (surnames) and 7 (words and directions) are taken out of the lifted code and the string tables by `work\make_customizable_s45.py` (checks in `work\customizable_check_s45.txt`, 12 of 12 PASS), never typed by hand; the regions between the markers are generated (`--write`), the rest is hand-written. Decisions: D-032 (items 7 to 11); D-035 (the owner's decision of 2026-10-14 that the banter is customizable with own text and own sounds, section 12). Owner questions that touch this file: Q-016 (the surname data) and Q-026 (the team name "Redskins"), both asked once at S11.1; they stay as defaults and this file shows that either answer is one file edit (section 10).

## 1. The inventory in short

Customizable by file (the original values are the defaults, built into the program):
- L1 Team nicknames, 32, `teams.txt`.
- L2 Division names, 8, `divisions.txt`.
- L3 Roster surnames, 1,708, `surnames.txt`.
- L4 The player's own roster names, 33 names in five sections plus the quarterback (34 lines), `footplay.txt` (the original's own file and layout).
- L12 The announcer's banter, the 142 original lines plus any the player adds, `banter.txt`: own text lines and own sounds (OWNER DECISION 2026-10-14, given during P5 S5.2, D-035; section 12). This reverses "built in" for the banter in the paragraph below and in section 7.

Typed in the game, not files (limits recorded for the typing code and the tests):
- L5 The coach's name. L6 The quarterbacks' names (own, opponent).

Settings (kept in the settings file, not customization lists): section 9.

Not customizable, built into the program (reason in section 7): the snap-count words (10), the run directions (7), the play-off week names (4), the play-by-play phrase families (about 330 strings), the announcer's banter (142 lines, 196 strings), the help texts, menu and prompt texts, the conference names inside fixed sentences, the score table of the season engine. There is NO attribute table to separate from the names: the original has no rating, strength or skill value for any team or player (GAME_SPEC 5.7 to 5.9: the outcome of a play depends only on the pair of plays and random draws; every team and every player is equal).

## 2. Where the original stores each list

- Teams: hard-coded, `GetTeams` (p_4321d0) sets them into the form's array Me.m294 at index tn1 + 9 x tn2 (tn1 division 1 to 8, tn2 place 1 to 4). [CODE (lifted)]
- Division names: hard-coded, TWO copies of the same eight texts: the array Le0 in `SayStand` (p_42ce40, the standings) and the array L2c0 in `pog` (p_4615b0, the division winners after week 16). [CODE (lifted)]
- Surnames: hard-coded, `SetPlayerNames` (p_432460) sets 1,708 texts into Me.m278 (1 to 1708). [CODE (lifted)]
- Own roster names: the text file `footplay.txt` in the data folder (Documents\kitchensinc), created by `pag` at the first game of a season, deleted with the season files at the end of the season (Q55), the quarterback line appended by `Getqbs`. The readme tells the player to edit it. [CODE (lifted), OBSERVED readme]
- Coach name: `footbal1.dat` (tn1, tn2, the name length, one character code per letter), written by `ChooseTeam`. [CODE (lifted)]
- Own quarterback: the last item of `footplay.txt`; opponent quarterback: asked every game, kept only in `football.sav` while a game is saved. [CODE (lifted)]
- Voices and speech rate: `footbal0.dat`; volumes, sound volume and the comments flag: `football.vol`. [CODE (lifted)]
- Words and directions: arrays set in pag's set-up (0x4585ca to 0x458aa7). [CODE (lifted)]

## 3. L1 Team nicknames (32) [CODE (lifted)]

Original limits: count 32, fixed by the two-level index (a division number 1 to 8 and a place 1 to 4); no limit on length or characters in the code (VB strings); the longest default is 12 characters ("Forty Niners"); no city names; the order is division by division, inside a division alphabetical by city (the code does not store the city; S5.2 correction, audit finding A-21: alphabetical by NICKNAME, not by city: Bengals, Browns, Ravens, Steelers, GetTeams 0x43221d to 0x432431); the standings sort by fewest losses only and break ties in this table order (5.2), so the table order, not the alphabet, decides ties. Several names are spelled for the speech engine ("Forty Niners", "Sea hawks"). Uniqueness is not checked in the original (the data has none equal). Used in: the team choice, the schedule, "Today's game", the standings, the score speech, the coin toss, the snap-count lines, the season results, the play-off results, the Super Bowl sentence.

Saves and season files hold division and team NUMBERS only (footbal1.dat, footbal2.dat, footbal3.dat, footbal4.dat, footbal5.dat, football.sav carry no team name), so renaming never touches a season or a saved game.

Clone IDs: T01 to T32 in the original's order (T01 = division 1 place 1 ... T32 = division 8 place 4). Defaults:

<!-- TEAMS-BEGIN -->
- T01 (division D1, place 1): Bengals
- T02 (division D1, place 2): Browns
- T03 (division D1, place 3): Ravens
- T04 (division D1, place 4): Steelers
- T05 (division D2, place 1): Bills
- T06 (division D2, place 2): Dolphins
- T07 (division D2, place 3): Jets
- T08 (division D2, place 4): Patriots
- T09 (division D3, place 1): Broncos
- T10 (division D3, place 2): Chargers
- T11 (division D3, place 3): Chiefs
- T12 (division D3, place 4): Raiders
- T13 (division D4, place 1): Colts
- T14 (division D4, place 2): Jaguars
- T15 (division D4, place 3): Texans
- T16 (division D4, place 4): Titans
- T17 (division D5, place 1): Bears
- T18 (division D5, place 2): Lions
- T19 (division D5, place 3): Packers
- T20 (division D5, place 4): Vikings
- T21 (division D6, place 1): Cowboys
- T22 (division D6, place 2): Eagles
- T23 (division D6, place 3): Giants
- T24 (division D6, place 4): Redskins
- T25 (division D7, place 1): Cardinals
- T26 (division D7, place 2): Forty Niners
- T27 (division D7, place 3): Rams
- T28 (division D7, place 4): Sea hawks
- T29 (division D8, place 1): Buccaneers
- T30 (division D8, place 2): Falcons
- T31 (division D8, place 3): Panthers
- T32 (division D8, place 4): Saints
<!-- TEAMS-END -->

## 4. L2 Division names (8) [CODE (lifted)]

Original limits: count 8; no limit on length or characters; each is a whole spoken phrase with its own final full stop, with a space before and after in the string (" A. F. C. North. "); the two copies (SayStand, pog) are equal. Spoken in the standings headings and before each division winner after week 16. The conference names "A. F. C." and "N. F. C." also occur inside 12 fixed strings (11 sentences of the season and play-off engines, the wild card, division play off and championship headings, classes SEASON-RESULTS-SPEECH and PLAYOFF-RESULTS-SPEECH, and one paragraph of the F6 help text; counted by script over `strings_all.tsv`): they are NOT separate data in the original and stay fixed, so a player who renames a division still hears "A. F. C." in the play-off headings (README says so).

Clone IDs: D1 to D8 in the original's order (the same division number tn1 as in the team IDs). The file value is the text without the surrounding spaces, with its final full stop; the program adds the spaces. Defaults:

<!-- DIVISIONS-BEGIN -->
- D1: A. F. C. North.   (the original text is " A. F. C. North. ")
- D2: A. F. C. East.   (the original text is " A. F. C. East. ")
- D3: A. F. C. West.   (the original text is " A. F. C. West. ")
- D4: A. F. C. South.   (the original text is " A. F. C. South. ")
- D5: N. F. C. North.   (the original text is " N. F. C. North. ")
- D6: N. F. C. East.   (the original text is " N. F. C. East. ")
- D7: N. F. C. West.   (the original text is " N. F. C. West. ")
- D8: N. F. C. South.   (the original text is " N. F. C. South. ")
<!-- DIVISIONS-END -->

## 5. L3 Roster surnames (1,708) [CODE (lifted), checked by script]

Original limits: count 1,708 (the draws are `Int(Rnd * 1708) + 1` and the redraws loop, so the count is in the logic, not only in the data); no limit on length or characters in the code; no duplicates ignoring case in the data; roughly alphabetical (the order breaks for names with an apostrophe or a space; the order has no meaning, the draw is uniform). Drawn WITHOUT replacement: a used entry is blanked, so within a run no surname is used twice; the opponent's 33 names are drawn at every game, the player's own 33 only when `footplay.txt` is missing or invalid, and the default quarterback names come from the same pool; 15 banter lines speak one of 58 roster names, so the pool is also in the commentary. Pool entries are never shown, only spoken, so a phonetic spelling IS the name (50 of them).

Clone IDs: S0001 to S1708 in the original's index order. Default statistics (generated):

<!-- SURNAMES-BEGIN -->
- Count 1,708, IDs S0001 to S1708 in the original's index order (spec\SURNAMES.tsv: index, text, address).
- Length 3 to 14 characters (the longest is van der Linden).
- 50 have a space (phonetic spellings such as Zoo lynn ski, and two-part names); 4 have an apostrophe; no two are equal ignoring case.
- Characters other than letters and space: quote mark (1), apostrophe (4), closing parenthesis (1).
- Letters above ASCII: Martínez (S0967), Márquez (S1076).
- Stray characters kept as the original data (D-026): S0775 Jones", S0943 Maddox).
<!-- SURNAMES-END -->

Count rule (7.9: "do not hard-code a count the original logic did not"): the original logic does hard-code 1,708, so the first release keeps 1,708 slots; a player renames entries, never adds or removes them. The logic itself would work with any pool of at least about 100 names (68 are drawn per game and 2 default quarterback names; the clone's redraw loops are bounded, G-D1), so a flexible count is one constant and a validation rule, built ONLY if the owner asks (then recorded in DECISIONS.md).

## 6. L4 The player's own roster names, `footplay.txt` (33 + 1 names), L5 and L6 typed names [CODE (lifted)]

footplay.txt, original format kept (D-024 item 4, D-025 d, Q-014; damaged-file behavior in GAME_SPEC 15, quirks Q8 and Q36): plain text, one item per line, in this fixed order: heading `Running Backs:` then 6 names, `Receivers:` 6, `Defensive Players:` 17, `Special Teams Players:` 2, `Kickers:` 2, then `Quarterback:` and 1 name (added after the first game's quarterback question): 33 names in five sections plus the quarterback, 34 name lines, 6 headings. Only the player's own side is stored; the opponent's names are drawn again every game. How the names are used (5.5, 11): a running back carries the ball on runs and a receiver is the target and the catcher on passes (index by the same draw), defensive players tackle and intercept, the two special teams players are the returners, kicker 1 kicks field goals, extra points and kick-offs, kicker 2 holds and punts. Limits of the original: the counts and headings above are exact (the reader compares each heading), a name is any text without a comma (the reader is `Input #`), no length limit, no uniqueness check; the original reads and writes the system's ANSI code page, so a name with an accent in a file made by the original is Latin-1. Per-entry attributes: none (the position comes from the heading). Created with random unused surnames when missing or when the FIRST heading is wrong (the rest of a damaged file ends the original in a run-time error, Q36, not reproduced). Clone: reads UTF-8 (cp1252 fallback), writes UTF-8; keeps every valid section and repairs only the broken one with a spoken notice (D-025 d); at the end of a season the file is saved as `footplay.previous.txt` and a new random set starts (G-F4, Q55); the file lives in the customization folder with the other editable files so the player has one folder to open (D-032 item 11).

Typed names (not files): coach (L5) and quarterbacks (L6) follow `getter`, `ccn`, `cqn` (8.2, D-022 item 1): keep only letters, digits and spaces; fewer than 2 characters typed, or only spaces left, give the default (coach: "coach"; quarterback: a random unused surname); no maximum length in the original, the clone stores at most 100 characters (G-K5; S5.2, D-034: 30 characters, the limit of section 10, because the own quarterback's typed name goes into `footplay.txt` and is read back by the same rules); case is kept; the coach name is asked once per season and kept for the season (footbal1.dat), the own quarterback once per season (last item of footplay.txt), the opponent's every game.

## 7. Not customizable in the first release, and why [CODE (lifted)]

Inventoried because 7.9 says "when unsure include it"; the decision for each is DEFAULT built in, cheap to reverse (a list moves into a file without touching the logic) and listed for the owner's veto in section 11.

- L7 Snap-count words, 10, and L8 run directions, 7 (generated list at the end of this section). Words are chosen by index (a random word of ten, the second call one of the first eight), directions by play (1 to 3 line plunge, 4 to 7 end run): the MEANING of a direction is bound to the play, so a changed text would contradict the play; nobody needs a different colour word.
- L9 The four play-off week names ("Wild card play off week", "division play off week", "division championship play off week", "super bowl week") and the conference names inside sentences: part of the fixed league structure and of 12 fixed strings (section 4).
- L10 The play-by-play phrase families (about 330 strings in groups of 5 to 13 with "never one of the last N used" memories, 5.8 to 5.10), the hand-off and drop-back phrases, the 142 banter lines (15 with a roster name, 5 with a bleep, 30 with a second text), the help texts (F5 to F7), the menu and prompt texts: the phrase groups are counted and remembered by the logic and are spelled for the speech engine, so editing them needs a structured format and a count check per group; the banter is the content of Q-018 (the owner may want the crude lines switchable at S11.1: then the banter becomes a data table with a flag per line, which the program needs anyway; whether that table is also exposed as a player file is a later choice). (S5.2: the owner chose on 2026-10-14: the banter IS exposed as a player file, with own text lines and own sounds; section 12, D-035. The play-by-play phrase families, the help texts and the menu texts stay built in.)
- L11 The score table of the season engine (32 scores) and the other random-game parameters: game balance, not names (7.9: attribute editing only when the owner asks).

<!-- WORDS-BEGIN -->
- Snap-count words (Me.m3dc): 1 "Red", 2 "Right", 3 "Blue", 4 "Left", 5 "white", 6 "black", 7 "green", 8 "chrome", 9 "X", 10 "XP".
- Run directions (Me.m3f8): 1 "up the middle", 2 "on the left side", 3 "on the right side", 4 "around the right side", 5 "around the left side", 6 "around the left end", 7 "around the right end".
<!-- WORDS-END -->

## 8. The generated lists above, checked

`work\make_customizable_s45.py`: 32 team slots are exactly division 1 to 8 x place 1 to 4; the 32 names are different; the eight division names are the same array in SayStand and pog; SURNAMES.tsv equals the lifted SetPlayerNames (1,708 assignments, indexes 1 to 1,708); no two default surnames are equal ignoring case; ten words and seven directions; every DEFAULT name passes the clone's limits of section 10 (so loading the defaults never reports a problem). Re-run after any change: `py -3.10 -I work\make_customizable_s45.py [--write]` from the game folder.

## 9. Settings (not customization lists) [CODE (lifted)]

- Five voices (announcer, own quarterback, opponent quarterback, own punter, opponent punter): the original stores five voice NUMBERS (index in the SAPI voice list, meaningless on another PC); the clone stores voice ids (G-S8) and offers the 7.4.2 picker.
- Voice volumes, five: 0 to 100 in steps of 5, default 95. Sound volume `wavol`: 0 to -5000 in steps of 100 (a hundredth of a decibel each), default 0.
- Speech rate: any integer in the original (no limit); the clone keeps -10 to 10, default 0 (D-022 item 3, G-S4).
- Comments (the banter) on or off: F8, default on (it also silences the player's own banter lines and sounds, section 12).
- Clone-only: speech mode (SAPI 5 default, G-S7), the sound settings of 7.7 (`sounds.txt`: per sound file, volume, off).
- Stored in the kit's plain-line settings file (G-F8); `footbal0.dat` and `football.vol` are not created and the original's are not imported.

## 10. The clone's files, format and rules (decided here, D-032 items 7 to 11; built in S7.7)

nfl4 is the first game with customization lists, so this is the format "chosen once" of 7.9 and reused through `shared\` (a module `customlists` in the starter kit; S7.7 writes it, the kit is refreshed at the end of that session).

- Folder: `customize` inside the data folder (`%APPDATA%\Kitchensinc Revival\NFL Football 4\customize`, G-F8); S7.1 names it in the paths module. It holds `teams.txt`, `divisions.txt`, `surnames.txt` and `footplay.txt` (and `footplay.previous.txt` after a season), so the player opens ONE folder. (S5.2, D-035: also `banter.txt` and the subfolder `sounds` for the player's own banter sounds, section 12.) Season and save files stay in the data folder.
- Format, plain UTF-8 (a byte order mark is accepted, cp1252 is the fallback for a file made by the original), readable in Notepad and by a screen reader, CRLF or LF: a header of `#` notes in plain words with the format version on its first line (`# NFL Football 4 teams, format 1.`), then ONE entry per line: `ID = name`, for example `T09 = Mustangs`. Blank lines and lines starting with `#` are ignored; spaces around the equals sign and at the ends of the name are ignored; the ID is permanent and not case sensitive. Strict formats (JSON) are not used: one missing comma must not break the file.
- The name is what the voice SPEAKS (as in the original: "Sea hawks", "Zoo lynn ski"), so the player spells it the way it should sound. No second field in the first release (the original has no separate written form: the program has no screen); a `spoken=` setting after a semicolon is reserved, which is why a name may not contain a semicolon.
- Limits (clone, DEFAULT; the original has none): 1 to 30 characters after trimming (S5.2, audit finding A-31, D-034: the same limit applies to `footplay.txt` and to the typed coach and quarterback names, G-K5, so a typed quarterback name always passes when the file is read back), no comma (it would break `footplay.txt` for the original and for a player who copies files across), no semicolon, no control character; any other character is allowed (letters of any language, digits, apostrophes, parentheses; the two stray characters of the default data, `Jones"` and `Maddox)`, pass). Teams: no two equal ignoring case (a collision sends the later entry back to its default; if that default is taken too, S7.7 writes the deterministic rule and a test). Divisions: the same. Surnames: duplicates are allowed (the draw cannot break; it is only logged).
- Defaults ship inside the program and are never edited; a player's entry with the same ID overrides; a missing ID uses the default; an unknown ID is ignored and counted; a line that does not parse is skipped, the default is used, and ONE spoken summary follows at load ("2 problems found in teams.txt, details are in the log"; log file, line, reason). The 7.10 healing applies to every file: missing = recreated from the built-in values with the commented header; unusable (empty, cut off, random bytes, unknown format version, missing header) = copied beside it as `teams.txt.damaged1` (three kept) and recreated, one spoken message per start; read-only or locked = built-in values, one notice, play on.
- F9 Customize menu (G-K2): open folder, reload names (applies at once to everything spoken after it; a game in progress keeps the roster it already drew; `footplay.txt` is read at the start of each game), check files (the results read aloud), reset one list, reset all. README examples: rename a team (`T09 = Mustangs`), rename a division, write your own roster names, replace the surname list.
- Tests (S7.7, S8.1, S8.3): defaults load with no problem; a changed team name appears in the schedule, the standings, the results and the play text; bad lines fall back; a season and a saved game survive a rename (IDs); reset works; the 7.10 matrix (delete, empty, cut in half, random bytes, other encodings, huge, read-only, locked, newer version, bad line in the middle) plus the 300-case fuzz over all four files; property test: after any load all 32 team names are different and 8 division names are different.

## 11. Points the owner can veto (all cheap; nothing is asked now)

- The four files and their folder (section 10); a flexible surname count (off); the 30-character limit; no `spoken=` field.
- Making L7 to L10 files later (section 7); the banter as a data table with a switch per crude line (Q-018, at S11.1). (S5.2: the banter file is decided by the owner, section 12; Q-018 at S11.1 now only chooses which original lines ship switched off.)
- Section 12: the markup words, the limits and the folder for the player's own sounds are drafts that S7.7 fixes.

## 12. L12 The announcer's banter, `banter.txt`: own text and own sounds (OWNER DECISION 2026-10-14, D-035; built in S7.7)

The owner, during P5 S5.2: "in the cloned game, I want to be able to customise the banter, either by adding new sounds, or by adding my own text", and the same for such features in later games (playbook 7.9, CLAUDE.md 0.12). The original's banter is GAME_SPEC 5.13 (142 lines in a table generated from the code); what follows is the clone's file, a DRAFT that S7.7 builds and fixes in its tests.

- File: `banter.txt` in the `customize` folder, the format of section 10 (`# NFL Football 4 banter, format 1.` first, `#` notes, one entry per line, `ID = line`), plus the subfolder `customize\sounds\` for the player's sound files.
- IDs: B001 to B142 are the original lines with their original numbers (the defaults, built into the program from the 5.13 table by script, never typed); the player adds lines with new IDs (B143 and up, any free number). A player's line with an original ID replaces that line; `B045 = off` switches a line off; deleting a line from the file brings back the default (as every list of section 10).
- A line is a sequence of pieces, in any order: plain text (spoken by the announcer with say, waits, as the original's texts), and markup in square brackets (draft words, final in S7.7): `[name]` one of the 58 banter names drawn as in 5.13 step 4 (the same name everywhere in the line), `[opponent quarterback]` (line 45), `[bleep]` the original's foot13 (play, waits), `[sound my laugh.wav]` a sound file of the player from `customize\sounds\` (any format the sound layer reads, 7.7; played on the one-shot slot at the sound volume, waited, a key does not cut it, like the bleep), `[pause]` one rady, `[faster]` the next text one rate step faster (line 113), `[one of: text a | text b | text c]` a choice drawn with equal chances (lines 101 and 110). A line may be text only, sound only (`B150 = [sound crowd boo.wav]`) or both (`B151 = what a hit! [sound crunch.wav] Ghip, did you see that?`). The 142 defaults are written in this markup so that, with the file absent or unchanged, the clone says and plays exactly what the original does (the S8.1 conformance tests run on the defaults).
- Draw: the original's rule over the whole pool of lines that are on: one line drawn with equal chances per call, none twice in a game, nothing more once every line has been used in a game (5.13 steps 2 and 3, with the pool size in place of 142); the call places (after a score, a change of possession, one play in four, the statistics of quarters 1 and 3) do not change. Comments off (F8) silences every line, the player's too.
- Limits (draft, S7.7 measures the longest original line and adds a margin): a line of up to 500 characters, at most 20 pieces, no control character; an unknown markup word is spoken as text and logged; a missing or unusable sound file is skipped and the rest of the line is spoken, with the one spoken sound notice of SOUND_DESIGN 5; a pool with no line switched on means no banter (as comments off).
- Q-018 (the crude lines, S11.1): the owner's answer becomes `off` entries in the SHIPPED defaults or a README note; no code change, and every player can switch any line on or off.
- F9 Customize menu (G-K2): reload, check files and reset also cover `banter.txt`; "open folder" opens `customize`. README: one example of a text line, one of a sound line, one of switching a line off.
- Tests (S7.7, S8.1, S8.3): the 142 defaults equal the 5.13 table (generated from it); a text line, a sound line and a mixed line are spoken and played in order; `off` works; a pool of 1 and of 500 lines; the draw never repeats in a game; F8 silences all; the 7.10 damage matrix on `banter.txt` and on a sound file in `customize\sounds\`.
- Q-016 (surnames) and Q-026 ("Redskins", `T24`): with the files in place the owner's S11.1 answer only chooses what the shipped DEFAULT is; no code changes either way, and every player can change the names themselves on day one. The README says where the files are.
