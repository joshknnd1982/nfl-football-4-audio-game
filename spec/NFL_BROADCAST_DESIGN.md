# The radio broadcast of NFL Football 4 (D-178, written 2026-10-26)

nfl4 only (rule 0.13), and the model for every sports game of the owner's (rule 0.27 as amended on 2026-10-26). This is inspired by Jim Kitchen.

## 1. The owner's words and answers

- 2026-10-26, in chat: "You need to forget and get rid of all of Jim Kitchen's commentary and commenting code for Gip and other commenters. Once you
  throw all that away... next: incorporate all new broadcast code in a new style radio broadcast format with new announcer names, etcetera."
- Asked: should Classic (the exact original, F9, Rules) keep the original's commentary? Answer: "Every mode": the original's commentary goes from
  Classic too; Classic keeps the original's plays and rules, and with comments on it uses the new radio broadcast.
- Asked: a rule for every sports game? Answer: "Yes, every sports game": CLAUDE.md 0.27, playbook 7.19 and fixesforgames A87 are amended.
- Reading of "commentary" (Claude's, recorded in D-178, the owner may correct it): the commentary is what is said ABOUT the game around the plays:
  the original's 142 jokes and asides of the announcer ("Ghip" and the 58 names they tease), their timing and their draws, and the color
  commentator "Ghip" with the list of 28 real podcasters' names the player could give him (D-106, "other commenters"). The play-by-play of a
  play (the original's sentences that say what happened: the snap, the run, the tackle, the gain, the score) is not commentary: it is how the
  game tells the play, and it stays. The referee's announcements and the stadium's sounds stay (they are not commenters).

## 2. What goes

| Goes | Where today | Why |
|---|---|---|
| The 142 original lines and their data | game/banter_lines.py | the original's jokes, about 77 of them about Ghip |
| The original's banter step: the line draw, the 58-name draw, the choices, the bleeps | game/banter.py `speak_banter` | the original's commenting code (GoSub 0x45915e) |
| banter.txt and its pool (B001 to B142 and the player's B-lines) | game/banter_pool.py, data/customize.py BANTER | the customization of the original's jokes |
| Ghip, the default name | extras/commentators.py DEFAULT, settings nx_commentator, texts | the original's character |
| The 28 real podcasters' names (F9, Rules, Commentator) | extras/commentators.py NAMES, spec/COMMENTATOR_NAMES.md | "other commenters" |
| The pool BN drawn by the original's rule on the game's generator | extras/broadcast.py `banter_lines`, hook H23 `banter_lines` | the original's timing and draws |

The original's strings stay in spec/STRINGS.md (the record of what the original says, rule 0.3); nothing of them is said or shipped as a line.
foot13.wav (the bleep) stays: the original also plays it when the player concedes (pag_breaks.concede), which is not commentary. The list of
58 players' names (setup.banter_names, the running backs, receivers and defenders of both teams) stays under a plain name (player_names): the
added remark lines that name a player (<name>, extras/remarks.py) draw from it.

What the game keeps of the old step, on purpose: the one draw `Int(Rnd * 4) + 1` after a play that ends in the field of play
(pag_results.banter_position). The original draws it after EVERY such play, comments on or off, so it is part of the game's random sequence:
kept, it leaves every seeded game with comments off exactly as it was (the golden transcript's plays, every calibrated band, every whole-game
test); it no longer decides anything that is said. The draws that happened only with comments on (the line, the name, the choices) go, so a
seeded game with comments on changes after its first old banter moment: the golden transcript (recorded with comments on) is recorded again on
purpose (B-X22), and the reason is D-178.

## 3. The crew (new names, made up, no real person; checked by web search on 2026-10-26)

| Who | Name | Speaker (voice) | Does |
|---|---|---|---|
| Play-by-play announcer | Walt Kessler | the announcer (the original's voice) | the welcome, the plays (the game's narration), the score updates, the asides, the hand-offs, the sign-off |
| Color analyst | Gus Delgado | COLOR (his own voice, F12) | the analysis after plays and at the moments (the pools C.. of the radio broadcast of D-101) |
| Sideline reporter | Nora Banks | SIDELINE (new, her own voice, F12) | the injury reports, the weather and the crowd at the start, the half-time report |

The network is "the Gridiron Radio Network" (made up). The player may rename each of the three and the network (F9, Rules, Broadcast crew:
each name read, Enter types a new one, Escape keeps it; nobody has to type, rule 0.19); the names are settings (nx_announcer, nx_analyst,
nx_sideline, nx_network) and every line says the setting (placeholders <announcer>, <analyst>, <sideline>, <network>). An old settings.txt's
nx_commentator is read once: a name the player typed (not Ghip, not one of the 28 podcasters) becomes the analyst's name; Ghip and the
podcasters' names become Gus Delgado.

## 4. The format (both modes, comments on)

1. Sign-on, before the opening kick-off: Walt's welcome (" Good afternoon, everybody, and welcome to the Gridiron Radio Network's coverage
   of N. F. L. football: the <visitors> at the <home>. I'm <announcer>, alongside <analyst>, and <sideline> is on the sideline. "), Nora's
   sideline note (pool SON: the weather, the crowd, the warm-ups), Gus's opening line (pool CKO). Once per game (not per program run).
2. Every play: the game's narration as now (the announcer's voice).
3. After a play, at a dead ball: Gus's analysis at the moments of D-101 (turnover, big gain, sack, missed kick, third down, red zone, fourth-down
   gamble, penalty), the chances and gaps of D-163 (the owner's "talks too much" stays answered); Walt now and then turns to him first (pool ASK).
   Walt's asides (pool BN, the radio banter of D-101, the crowd, the weather, the booth) about one dead ball in eight, never twice in four plays,
   on the broadcast's own generator.
4. A score: the game's touchdown or field goal sentence, then Walt's score update (" That makes it <team> 14, <opponent> 10. "), then Gus (CTD,
   CFG).
5. An injury (the N. F. L. rules' game injuries): Nora's report (pool SIN: " <sideline> here on the sideline: the trainers are looking at <player>
   ... "), and when he is out of the game, Walt says who comes in (the game already names the replacement: the line only says it once).
6. The end of the first and third quarters: Walt's quarter update (" At the end of the <quarter>, it's ... "), Gus (CQE, CTT, CBO).
7. The two-minute warning: Walt's station break (" Two minutes to go in the <quarter>. You're listening to the Gridiron Radio Network. "), then
   the commercial slot of rule 0.14 when the player has one there (the half and the quarter ends keep theirs), then Gus (CTM).
8. Half time: Walt's half-time update, Nora's half-time report (pool SHT), Gus (CHT), Walt's station break before the commercial slot.
9. The end of the game: the game's final score sentence, Gus (CFN, CFT), Walt's sign-off (pool SGO: " For <analyst> and <sideline>, I'm
   <announcer>. Thanks for listening to the Gridiron Radio Network. ").
10. Timeouts, penalties, onside kicks, challenges and reviews: the remark pools TO, PN, ON, CHS, CHC, RVR, RVC of the extras keep their draws
    (they are the game's generator's, calibrated) and their moments; their lines that talked to Ghip now talk to <analyst>.

## 5. Switches, keys and voices

- F8 (comments) switches the whole broadcast, as it switched the original's banter: off, nobody of the crew speaks (the play-by-play stays).
- F9, Rules, Broadcast: on (default) or off: Gus and Nora on or off; Walt's sign-on, updates and sign-off stay while comments are on. It is the
  same item as D-101's and now applies in Classic too (no " used with the N. F. L. rules ").
- F9, Rules, Broadcast crew (replaces Commentator): the four names.
- F12 (voices) and F11 (volumes) ask for the analyst and the sideline reporter in both modes while comments are on (the original's five speakers
  first, as before). Keys documented in F5, F6 and README_keys (rule 0.24); a test requires it.
- The sideline reporter's voice is chosen like the analyst's (_own_voice: a voice of the other gender when there is one, else another voice).

## 6. Random draws and the game

- The broadcast draws only from its own generator (seeded from the game's seed mixed with SEED_MIX), as D-101's did; the game's generator keeps
  every draw it had with comments off (section 2), so no calibrated band moves.
- The broadcast changes no state, no score and no clock; F2 never replays a crew line; the first key (or T) cuts a line that is being said.
- A line is never said twice in a row by mistake (rule 0.28 (3)): a pool never gives the same line twice in a game while it has others.

## 7. Customization (rules 0.12 and 0.14)

- remarks.txt holds every pool: BN (Walt's asides), ASK, the C pools (Gus), the new SON, SIN, SHT (Nora), SGN (sign-on), SGO (sign-off), UPD
  (score updates), STA (station breaks). Each line has a permanent ID; the player changes a line, switches it off, adds lines of text, sound files
  or both (banter_markup); numbered sound families of rule 0.14 work in a line as before. A damaged file heals (7.10).
- banter.txt is no longer read. A player's banter.txt stays on disk untouched; the CHANGELOG says how to move a line of one's own into
  remarks.txt (pool BN).

## 8. Sessions (one writer at a time; the 0.16.7 session commits first)

- BC.1 (this document, D-178, the rule amendments). Opus 5.5, high.
- BC.2 Remove the original's commentary: banter_lines.py, banter.py's speak_banter (play_line and the sound player move to banter_markup or a
  module of their own, the Franchise's weekly and news pools use them), banter_pool.py and the BANTER customization, Ghip and the 28 names,
  hook H23 banter_lines; keep the per-play draw and the 58 players' names (renamed player_names); the golden transcript recorded again; every test that pinned the jokes. Sonnet 5.5,
  high (Opus 5.5 if the draws move). DONE 2026-10-27 (D-180, Opus 5.5): as planned; the analyst's default name is already Gus Delgado; the
  draws of seeded comments-off games are proved unchanged (tests/test_bc2_no_original_commentary.py); the new line player is
  game/line_player.py. For BC.3: BN is not drawn at all now; the menu loses a typed name once the player steps to the default.
- BC.3 The crew and the format: the broadcast in both modes (the moments of section 4 from both rules' hooks), the new pools and texts
  (strings_nx.tsv), the names and their menu, SIDELINE in roles, F11, F12, the help, the keys (0.24), CHANGELOG 0.16.8, CUSTOMIZE.md, README.
  Opus 5.5, high.
  DONE 2026-10-27 (D-189, Opus 5.5): as designed, with section 11; Classic through extras/classic_radio.py (the engine's exact Classic and the
  golden transcript unchanged: the same draws and score with the crew); differences recorded in D-189: UPD is the score said again when
  nobody said it for six minutes (the game's own score sentence follows every score), DRV and CLK only with the real clock, LID in place of
  one NID, the moments two_minute_break, half_time_break and final_score, remarks.txt read in both modes, eight name settings with the
  last typed name kept, the reporter's voice the next free one (no gender in the voice list).
- BC.4 Verification: full suites 64 and 32, a listening test of a whole game's broadcast transcript (work script: every line in order, no doubled
  sentence), the playtest list, a test build at the owner's word.
  DONE 2026-10-27 (D-191, Opus 5.5): the suites, the soaks and the listening test (work\bc4_1027\listen_broadcast.py: whole games in both modes, every line in order); fixed before the release: each game's own broadcast seed (game/rnd.side_seed), the sign-on before the opening coin toss (H23 "sign_on"), the sign-off after the final statistics (H23 "sign_off"), no hand-off before a line that is not about a play (NO_ASK), a capital first letter; the test build 0.16.8.

## 9. Tests (BC.2 and BC.3)

- Nothing of the 142 lines, "Ghip" or the 28 podcasters' names is in any text the game can say (a scan of every text and pool).
- Comments off: a seeded game in Classic and in the N. F. L. rules makes exactly the draws it made before (the per-play draw kept).
- Comments on: the sign-on once, a score update after every score, the quarter updates, the two-minute station break, half time, the sign-off
  once; Nora at an injury; no crew line twice in a row; F8 silences all of it; Broadcast off silences Gus and Nora only.
- The crew's names: the menu, a typed name cleaned, the old nx_commentator converted once.
- F11 and F12 ask for the analyst and the sideline reporter in both modes; the keys are in F5, F6 and README_keys.
- The golden transcript recorded again, with the reason, and passing on 32 and 64 bit.

## 10. The new default lines (BC.3 puts them in spec/strings_nx.tsv with these IDs; each pool is customizable, rule 0.12)

Placeholders: <announcer>, <analyst>, <sideline>, <network> (the crew's names, section 3), <visitors>, <home>, <team> and <opponent> (the team
the moment is about and the other), <situation> (the score in words, as D-101's: "the Bengals lead 14 to 10" or "it is tied at 7"), <quarter>,
<player> (the injured man), <stadium> is not used (the game has no stadium names). Every line is one or two plain sentences of at most 150
characters, gentle, no real person, team brand or statistic, no swearing, no bleeps (rule 0.27).

Sign-on, Walt (pool SGN, one at the start of every game):
- SGN01 Good afternoon, everybody, and welcome to <network> coverage of N. F. L. football: the <visitors> at the <home>. I'm <announcer>.
- SGN02 Hello again, everybody, from the booth. It's the <visitors> and the <home> today, and I'm <announcer> for <network>.
- SGN03 Welcome to <network>. The <visitors> visit the <home> this afternoon, and I'm <announcer> with you for every snap.
- SGN04 It's football time on <network>. The <visitors> at the <home>, and I'm <announcer> calling it for you.
Introducing the crew, Walt (pool CRW, right after the sign-on):
- CRW01 Alongside me as always is <analyst>, and <sideline> is down on the field.
- CRW02 <analyst> is here in the booth with me, and <sideline> has the sideline for us.
- CRW03 With me, <analyst>. On the field, <sideline>. Let's get to it.
Nora before the kick-off (pool SON):
- SON01 <sideline> here on the field. A light wind is blowing toward the south end zone, and both kickers spent warm-ups testing it.
- SON02 Down here it's loud already. The <home> fans were in their seats a good half hour before the kick-off.
- SON03 The <visitors> came out for warm-ups looking loose, plenty of laughter in the stretching lines. Back to you, <announcer>.
- SON04 It's a perfect afternoon for football down here: cool air, dry grass, and a crowd that's ready to go.
- SON05 I talked to the <home> equipment staff, and they say this field is as fast as it's been all season.
- SON06 The <visitors> quarterbacks threw for a long time in warm-ups. They look ready. <announcer>, back up to you.
- SON07 A few clouds rolling in, but nothing that should bother anybody. It's a good day to throw the ball.
- SON08 From the sideline: both teams are fully dressed and stretching. We're just about ready.
Score updates, Walt (pool UPD, after every score, before Gus):
- UPD01 So <situation>.
- UPD02 And with that, <situation>.
- UPD03 Let's reset it for you: <situation>.
- UPD04 The scoreboard tells it: <situation>.
Quarter updates, Walt (pool QUP, at the ends of the first and third quarters and at half time):
- QUP01 That's the end of the <quarter>, and <situation>.
- QUP02 We've reached the end of the <quarter> here on <network>, and <situation>.
- QUP03 The <quarter> is in the books, and <situation>.
- QUP04 And that will do it for the <quarter>: <situation>.
Station breaks, Walt (pool STA, at the two-minute warning and at half time, before the commercial slot of rule 0.14):
- STA01 You're listening to <network> coverage of N. F. L. football.
- STA02 This is <network>. Stay with us.
- STA03 You're tuned to <network>, and we'll be right back.
- STA04 We'll take a break here on <network>. Don't go anywhere.
- STA05 <network> coverage continues after this.
- STA06 This is <announcer> with <analyst> and <sideline> on <network>. Back in a moment.
Walt to Nora (pool ASN, before her injury and half-time reports):
- ASN01 Let's go down to <sideline> on the sideline.
- ASN02 <sideline>, what are you seeing down there?
- ASN03 We'll check in with <sideline>.
- ASN04 <sideline> has more from the field.
Nora on an injury (pool SIN, the N. F. L. rules' game injuries):
- SIN01 The trainers are with <player> on the <team> sideline. He walked off under his own power.
- SIN02 <player> is being looked at in the medical tent. The <team> will let us know more soon.
- SIN03 <player> was favoring his leg on the way off. The <team> staff are taking a careful look.
- SIN04 The <team> have <player> on the bench with a trainer. He's talking and alert.
- SIN05 From the sideline: <player> is getting some attention from the <team> medical staff. We'll keep you posted.
- SIN06 <player> came off slowly. The <team> trainers are checking him out right now.
Nora at half time (pool SHT):
- SHT01 Both locker rooms will be busy. The <team> coaches were already talking with their offensive line on the way in.
- SHT02 The <opponent> went in fast and quiet. You can bet there are some adjustments coming.
- SHT03 Down here the crowd is on its feet for the halftime show, but the players went straight inside.
- SHT04 I spoke briefly with the <team> staff: they want to run the ball more in the second half.
- SHT05 The <opponent> kicker stayed out to practice a few kicks into the wind before heading in.
- SHT06 The temperature has dropped a few degrees, and the field is holding up well.
- SHT07 The <team> sideline was all smiles heading in. The <opponent> sideline, a little less so.
- SHT08 Plenty of energy down here. Whatever happens next, this crowd is ready for it.
Sign-off, Walt (pool SGO, once at the end of every game):
- SGO01 For <analyst> and <sideline>, I'm <announcer>. Thanks for listening to <network>.
- SGO02 That's our broadcast. On behalf of <analyst> and <sideline>, I'm <announcer>. Good night, everybody.
- SGO03 Thank you for spending the afternoon with us on <network>. I'm <announcer>, so long, everybody.
- SGO04 <analyst>, <sideline>, and I thank you for listening. This has been <network>.

## 11. Review against real radio broadcasts (RS.1, D-179, 2026-10-26; the owner's instruction of the same day)

The owner asked for real NFL radio broadcasts to be fetched, transcribed with Whisper and used as the template (CLAUDE.md 0.33, playbook 7.24). Two whole games were transcribed (a modern national network call and a classic one); the result is `spec\RADIO_NFL_STYLE.md`. Its findings change this design as follows; where this section and sections 4 or 10 differ, this section wins.

Confirmed by the real calls (nothing to change): the sign-on with the identification of the network and the crew by role (SGN, CRW), the sideline note before the kick-off (SON), the score recap after every score (UPD), the quarter recap (QUP), the station break at the two-minute warning (STA: the real call says it aloud, "pause ten seconds for stations to identify themselves"), the reporter at injuries and at half time (SIN, SHT), the analyst's reason after a play (the C pools) and the sign-off (SGO).

Already done in RS.1 (the pools of D-101 that BC.2 and BC.3 keep): the BN, ASK and C pools are rewritten in the real calls' manner (same IDs, sizes, placeholders and draws). BC.3 takes them as they are in `strings_nx.tsv`; the design's "Walt's asides one dead ball in eight" is the right rate for BN (the real calls fill the air with the situation, not with asides).

Changes and additions for BC.3:
1. A pool NID (network identification, Walt, at a dead ball about every seven minutes of game time, never in the last two minutes of a half; the real modern call says it every 6.8 minutes, the classic one rarely):
   - NID01 You are listening to <network> coverage of N. F. L. football.
   - NID02 This is <network>, your home for football today.
   - NID03 Stay with us. You are listening to <network>.
   - NID04 This is <announcer> with <analyst> and <sideline> on <network>.
   - NID05 It's <network>, live from the stadium.
   - NID06 Thanks for being with us on <network>.
2. A pool LID (a listener's own identification, the real modern call has them; made-up people only, read by Walt in the first person, at most one a game and only when the player has the commercial slot of rule 0.14 off, so it never doubles a break):
   - LID01 My name is Dolores, I am seventy-nine, and I listen from a porch swing. You are listening to <network>.
   - LID02 My name is Marcus, I am thirty-four, and I am listening from the cab of a truck. You are listening to <network>.
   - LID03 My name is Priya, I am twelve, and I am listening under the covers. You are listening to <network>.
   - LID04 My name is Walter, I am eighty-one, and I have not missed a game on the radio since I was a boy. You are listening to <network>.
   - LID05 My name is Tanya, I am fifty-two, and I am listening in the kitchen with the stove on. You are listening to <network>.
   - LID06 My name is Eli, I am nineteen, and I am listening from a dorm room, trying not to wake anyone. You are listening to <network>.
3. A pool DRV (drive summary, Walt, right after the score update of a touchdown or field goal, once in three scores; the engine knows the plays, the yards and the time of the drive; the real calls say it after a score; placeholders <plays>, <yards>, <minutes>, <team>):
   - DRV01 That drive took <plays> plays, covered <yards> yards, and used up <minutes> minutes.
   - DRV02 A <plays> play drive, <yards> yards in all, and <minutes> minutes off the clock.
   - DRV03 The <team> went <yards> yards on <plays> plays, and took <minutes> minutes to do it.
   - DRV04 That was a <yards> yard drive. <plays> plays, <minutes> minutes, and points at the end of it.
   - DRV05 It took <plays> plays and <yards> yards, and the <team> got it done.
   - DRV06 <minutes> minutes, <plays> plays and <yards> yards. That is how the <team> built that score.
4. A pool CLK (the clock said aloud, Walt; the classic call says the time left far more than the modern one; in the last two minutes of each half, after every play that stops the clock, at most every second play; placeholders <time> as a spoken time such as "one minute and ten seconds", <quarter>, <situation>):
   - CLK01 The clock is at <time> in the <quarter>, and <situation>.
   - CLK02 <time> to play in the <quarter>. <situation>.
   - CLK03 We have <time> left in the <quarter>, and <situation>.
   - CLK04 The clock stands at <time>, and <situation>.
5. The injury report (SIN) says no pronoun for the player (the name may be the player's own, and a pronoun would be a guess). Replace SIN01, SIN03 and SIN04 of section 10 by:
   - SIN01 The trainers are with <player> on the <team> sideline. <player> walked off without help.
   - SIN03 <player> was favoring a leg on the way off. The <team> staff are taking a careful look.
   - SIN04 The <team> have <player> on the bench with a trainer. <player> is talking and alert.
6. The analyst's lines (the C pools) are reasons, as in the real calls; BC.3 keeps the engine's `<situation>` clause at the end of a sentence ("... and now <situation>") for the score recaps.
7. Not adopted from the real calls: the direction of the kick ("from our right to our left"), sponsored segments (rule 0.14's commercials are the player's), pre-game and post-game shows, interviews, call-ins.
8. Session RS.1 changed texts only (no engine, no hook, no draw). BC.2 and BC.3 stay as planned; the golden transcript recorded for BC.2 includes these lines.

## 12. How much the crew talks (S-D, D-193, 2026-10-27; the owner on 0.16.8: "not talking enough")

1. The analyst also speaks after ordinary plays on first, second and fourth down and after the kicks: CRG (a run of four yards or more), CRS (a run of three yards or less, or a loss), CPC (a pass caught for a gain), CPI (an incomplete pass), CPT (a punt that gives the ball away) and CKR (a kick off, returned or a touch back); none after a score, a turnover, a muffed punt the kicking team kept, an onside kick or a two-point try. The special pools keep their order first (a turnover, a big gain, a sack, a missed kick, a third down, the first trip into the red zone); an ordinary play's pool is tried only when none of them applies.
2. Four levels, the setting nx_crew_talk, F9, Rules, item 11: a little (0.16.8's rates exactly, no ordinary-play line), some, a lot (the default), the most. The table is extras/broadcast.py TALK_LEVELS: per level the analyst's chance at each pool, the plays between two of his ordinary lines, Walt's hand-off share, Walt's aside (one dead ball in n, never twice in m plays), the network's identification (seconds of game time) and the score reset (seconds, one dead ball in n).
3. The broadcast reads the player's setting at every line (Broadcast.talk), so a change in F9 applies at once, also in the game in progress; a rules object without a game (a test's) uses its own level. The log says the level at each game's start and when it changes.
4. Measured whole games (D-193): a little 64 crew lines a game, some 98, a lot 140, the most 188; at every level the game's draws and score are unchanged and no crew sentence comes twice in a row.

## 13. The radio play calls and the reporter's moments (RC, D-195, 2026-10-27; the owner on 0.16.9)

The owner: "It still says 3rd and ten at the 26 yard line. Why isn't it having exciting radio style? "caught by "playername!!" touchdown!!" Make it an exciting radio broadcast. Radio broadcasters use a lot of exclamations", and "Not once did the game have the sideline reporter speak at all. I want an exciting commentary for this game." Section 1's reading (the play-by-play is not commentary and stays) is kept for what the engine decides and draws; how it is SAID is now a radio call.

1. The play calls (extras/radio_calls.py). Every sentence of the play-by-play (say2 and say4, and the huddle and the quarterback at the line through Speakers.say5_call) passes through RadioCalls.call: a sentence of a known shape (151 patterns over the shapes of ten whole games, work\rc_1027\shapes.txt) becomes its radio call (168 calls, one to four wordings each, never the same wording twice in a row); any other sentence is said as it is. The teams by name in place of "my ball" and "your ball" (a continuing drive, a new possession, a takeover after a turnover, a turnover on downs); the down as a call says it, an earned first down with an exclamation; the gain by its size (under 4, 4 to 9, 10 to 19, 20 to 39, 40 and more; a return its own words); the touchdown countdown ("He's at the 40! the 30! ... 1!") and a return's markers (an exclamation from the third on); the scoring team at a touchdown; "It's good!" or "No good!". The biggest calls one rate step faster with the game's own voices. The caller draws only on its own generator (side_seed, SEED_MIX 0x2AD10CA1) and changes no state.
2. The switch: F9, Rules, Play calls (item 12), radio style, exciting (default) or plain, the original's words; nx_play_calls; read at every sentence; its own switch, not F8's. Both modes; the engine's bare Classic has no caller (pag clears game.radio_calls at every game's start, only the broadcast attaches it), and Classic with plain calls is the original's words exactly.
3. The reporter: Walt names her (ASN) before her note at the sign-on; her own moments, every line starting with her name (a screen reader speaks the crew in one voice): STD after a touchdown (after Gus), STV after a takeaway and SBG after a gain of 20 or more (at the dead ball, after Gus's line, not twice within the level's plays), SFD at a fourth-down gamble (after Gus's CFD), SMW at the two-minute warning, SQE at the end of the first and third quarters, SFN or SFT at the final whistle (always). Gus's exclamation CXR before CTD, CTV, CBG, CSK and CFM.
4. The rates are fields of TALK_LEVELS: Nora's chance 35, 60 and 85 percent at some, a lot and the most (gaps 6, 4 and 3 plays), CXR 35, 60 and 85; "a little" has none and draws nothing for them, so it stays the 0.16.8 broadcast.
5. Measured (work\bc4_1027\listen_broadcast.py with the radio calls' checks, PROBLEMS 0): the same scores and draws with radio and plain calls in Classic and in six N. F. L. rules games; no sentence twice in a row that the plain game does not say twice; the reporter in six games at "a lot": STD 19, SBG 21, SQE 10, SMW 9, STV 7, SFN 6, SFD 3.
