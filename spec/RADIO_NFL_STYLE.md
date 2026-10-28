# NFL radio broadcast style guide (RS.1, D-179, written 2026-10-26)

nfl4 only for the facts, and the model for every sports game (AGENTS.md 0.33, playbook 7.24, template `games\shared\broadcast-style\STYLE_GUIDE_TEMPLATE.md`). This is inspired by Jim Kitchen.

The owner's instruction: find real NFL radio broadcasts, transcribe them with Whisper into markdown, and use that as the template for the game's radio broadcast style. This guide is the result. It holds numbers, patterns and lines written NEW for the game. The audio and the full transcripts are the broadcasters' property and stay in the gitignored `work\radio\` folder (never committed, shipped or quoted); only the Sources table below names the broadcasts. No sentence of a transcript is copied: a line check run on 2026-10-26, before the study scripts were deleted, found no run of eight words that a transcript also holds in any of the 312 new lines.

## 1. Sources studied

| Id | What | Kind | Length | Where | License label |
|---|---|---|---|---|---|
| B1 | The NFL championship game of February 2022, called live on a national radio network (play-by-play announcer, analyst, sideline reporter; pre-game, breaks and post-game included) | modern network call, recorded off a local affiliate | 6 h 09 min (live game: 3 h 25 min counted) | Internet Archive item `super-bowl-lvi-2022.02.13-750-am-kxl-portland-002` | none given |
| B2 | The NFL championship game of January 1969, called live on a national radio network (play-by-play announcer and two analysts) | classic network call, recording of the whole game | 3 h 15 min | Internet Archive item `0c5906ad-3cf2-4c69-8c8f-69aa36e00e62` | none given |

Whisper (faster-whisper, model large-v3-turbo, an RTX 5060 laptop GPU, about 35 times real time) transcribed both in full on 2026-10-26. Transcripts: `work\radio\sb_lvi_2022_network_radio.md` and `sb_iii_1969_network_radio.md` (machine transcripts: names and numbers may be wrong). Statistics: `work\radio\stats_lvi_game.md`, `stats_sb3.md`.

## 2. Numbers

| | B1 (live game only) | B2 (whole recording) |
|---|---|---|
| Words | 36,301 | 31,269 |
| Speech share of the time | 89 percent | 83 percent |
| Pace, words per minute of speech | 199 | 194 |
| Sentence length in words, median / 75th / 90th percentile | 8 / 13 / 20 | 9 / 16 / 24 |
| Down-and-distance statements | 172 (one every 71 s) | 155 (one every 75 s) |
| Sentences that say a score | 63 (one every 3.3 min) | 54 (one every 3.6 min) |
| Network identifications | 30 (one every 6.8 min) | 5 |
| Sentences that say the clock or the time left | 7 | 43 |
| Sentences about the crowd, noise, weather, wind, roof or band | 27 (one every 7.6 min; 7.9 an hour, 7.2 an hour before the kick-off) | 19 (5.8 an hour) |

Reading of the numbers:
- Sentences are short. The calls of a play are fragments of three to six words; the analyst's thoughts run to fifteen or twenty. The new lines have a median of 11 and a 90th percentile of 18 words per sentence, so they sit inside the same band as the analyst's sentences.
- Atmosphere is a steady small part of the air, not a break in it: about six to eight remarks an hour about the crowd, the noise, the weather or the roof, in the game as much as before the kick-off (measured with one word list on both calls: B1 7.9 an hour live, B2 5.8). The rest of the air is the situation (down, distance, spot, score, clock) and the reason things happen.
- The classic call talks about the clock and about kicking range far more than the modern one (43 against 7). A game with a real clock should say the time left every few plays near the end of a half.
- The identification of the network is a regular beat (modern: about every seven minutes).

## 3. The shape of a broadcast

1. Before the kick-off: the sign-on and the identification of the network and the event, the crew introduced by role, the sideline note (weather, crowd, warm-ups), the coin toss, who kicks and who receives, the jerseys, then the kick-off: "and we are underway".
2. Every play, in this order: the situation (down, distance, where the ball is), a few words of formation, the snap, two to four short fragments of action in the present tense, the result (where the ball is spotted, the gain, first down if there is one), then the next situation. The analyst adds one thought after about one play in three (a reading of the first drives, not a measured count), always a reason (the call, the matchup, the mistake) and never only a reaction.
3. A score: the call of the play, one short sentence that says what it was, the score said in two numbers with the leader named, sometimes the clock and the quarter ("the clock stands at ..."). A drive summary a little later: the score, how many plays, how many yards and how much time the drive took.
4. A quarter or half: "our score after fifteen minutes of play ...", then a break and an identification.
5. Stoppages: a timeout is announced with the reason as the analyst reads it (a wrong call, a bad communication); an injury is announced as "a player is hurt, timeout on the field", the analyst names the player's role, and the reporter comes back later with the status ("back in the huddle", "being looked at").
6. Penalties: the flag, the foul, the team, the decision (accepted or declined), the new down and distance. The analyst talks about whether it was the right call by the officials, politely.
7. The last two minutes of a half and the end of the game: the clock is said every play, timeouts are counted aloud ("the second timeout", "one left"), the victory formation is described ("takes a knee"), the champion is announced in one flat sentence, then the crew hands back to the studio.
8. The sideline reporter is introduced by a hand-off ("live on the field to ...") and ends with "thank you"; the reports are short: an injury status, the mood of the crowd, a word from a coach.

## 4. The voice

- Play-by-play: present tense in the action ("drops back", "throws"), past or flat tense for the result ("tackled at the thirty-six"). Short. The excitement is carried by the word, not by shouting: "Touchdown." then one more short phrase about how, then the score. A repeated word is the way a radio call raises its voice.
- Analyst: opens with the point ("what I like here is ...", "the key there was ..."), gives the reason in one or two sentences, and ends with what to watch next. Praise is specific; blame is gentle. The habit of saying "you know" 56 times in 3 hours is the speaker's, not the style: the game does not copy it.
- Hand-offs: by first name and as a question or a request ("what did you see there?", "walk us through that"), answered at once; the other speaker returns with "thank you".
- Friendly teasing between the crew is rare and short, a clause, never a joke that needs a second sentence. The 142 radio lines and the analyst pools the game used before (a snack, a popcorn, an antacid) were written from imagination; jokes of that kind did not turn up in the stretches of the real broadcasts that were read (the first drives, a score, each quarter end, the two-minute warning, half time, the ending). The new default lines keep a little humour, but the weight is on the reason and the situation.
- Never said in the game: swearing, betting, or any claim about a person's health beyond "being looked at".

## 5. Recurring moves, with the game's new lines

The game keeps its own play-by-play (the original author's sentences are the narration of every play and stay). The new lines are the voices around it. AMENDED 2026-10-27 (D-195, the owner on 0.16.9: "It still says 3rd and ten at the 26 yard line ... Make it an exciting radio broadcast. Radio broadcasters use a lot of exclamations"): the engine still makes the original's sentences, and each is now said as a radio call of section 4's voice (extras/radio_calls.py: present tense, short fragments, the teams by name, the down as a call says it, the key word repeated and an exclamation at a big play, a countdown on a long run); F9, Rules, Play calls brings back the original's words. NFL_BROADCAST_DESIGN.md section 13. Each move below names the pool that carries it (pool names are those of `spec\strings_nx.tsv` and of `NFL_BROADCAST_DESIGN.md`).

| Move | When | Pattern | Pool | Example (new) |
|---|---|---|---|---|
| Network identification | about every seven minutes of game time, at a dead ball | "You are listening to <event> on <network>." | BN (listener lines), STA | "You are listening to live radio coverage of N. F. L. football. Stay right where you are." |
| Listener hello | now and then | a welcome to a place a person listens from | BN | "Wherever you are listening, in the car, the kitchen or the garage, thank you for spending your afternoon with us." |
| Hand-off to the analyst | before an analyst line | name + question about the last play | ASK | "<analyst>, walk us through that play." |
| The analyst's reason after a touchdown | after the score | what worked, in the order protection, call, execution | CTD | "That is what a finished drive looks like: protection, a good call and a player making a play." |
| The analyst on a stoppage | after a sack, a turnover, a penalty | the cost to the drive, in terms of down and distance | CSK, CTV, CPN | "A sack is worth more than the yards. It takes away down and distance and half the call sheet." |
| Score recap | after every score | "so" + the score in words | UPD | "So <situation>." |
| Quarter recap | end of a quarter | "our score after ... " + the score | QUP, CQE | "That wraps up the <quarter>, and <situation>." |
| The reason at the break | two-minute warning, half time | what each side must do next | CTM, CHT | "Watch the first drive of the second half. It usually tells you who made the better adjustments." |
| The aside | one dead ball in about eight | a saying of the sport, the clock, the field, the officials, the crowd, the booth | BN | "Time is the most valuable thing on the field right now, and every second has a price." |
| The sideline note | before the kick-off, injuries, half time | place + one fact + hand back | SON, SIN, SHT | "The trainers are with <player> on the <team> sideline. He walked off under his own power." |
| The sign-off | end of the game | the crew named, thanks to the listeners, the network | SGO | "For <analyst> and <sideline>, I'm <announcer>. Thanks for listening to <network>." |

## 6. Filler and atmosphere

- In the stretches read, the real crews filled the air with the situation and with sayings of the sport rather than with jokes: time and the clock, field position, the line of scrimmage, ball security, discipline, preparation, the officials. The new BN pool is built on those twelve topics (listener and network 14 lines, clock 12, field position 12, line play and strategy 14, weather and crowd 16, the booth 14, momentum 14, kicking and turnovers 10, officials 8, coaching 10, fans 10, transitions 8; 142 in all, the same size as before so the draws do not change).
- Weather and crowd remarks come about once every eight minutes in the real calls, so they are a minor kind of aside: the pool keeps them at 16 of 142 lines (11 percent).
- The booth teasing lines name the analyst by the name the player chose and never use a pronoun for the analyst (the name may be the player's own).

## 7. What the game takes, and what it leaves

Takes (built in RS.1, D-179): the 142 BN lines, the 12 ASK lines and the 158 lines of the 19 analyst pools (CKO, CTD, CFG, CFM, CTV, CBG, CSK, CTC, CTS, CFD, CRZ, CPN, CHT, CFN, CFT, CTM, CQE, CTT, CBO) rewritten in the real calls' manner: the analyst gives a reason and a look ahead, the announcer asks plainly, the asides are sayings of the sport. Same IDs, same sizes, same placeholders, same draws; every line passes the text rules (ASCII, at most 150 characters, no digit, only the pool's placeholders).

Passes to BC.3 (`NFL_BROADCAST_DESIGN.md`, sections 4 and 10, the format) as the real broadcasts' confirmation and additions: the sign-on with the identification of the network; the crew introduced by role; the quarter and half recaps with the score said as two numbers; the "ten seconds for stations to identify themselves" pause at the two-minute warning (pool STA); the sideline reporter at injuries and at half time; the drive summary after a score (plays, yards, time: the engine knows all three, a pool DRV with those placeholders is proposed in the design's section 11); the clock said aloud in the last two minutes of a half (the game's own clock sentences, rule 0.20); the victory formation sentence at the end of a won game.

Leaves out: the direction of the kick ("from our right to our left": the game has no stadium orientation), the sponsored segments ("this drive is sponsored by ..."; the player's own commercials of rule 0.14 take that slot), the pre-game and post-game shows, the call-ins and interviews, any real name.

What a synthetic voice cannot carry: shouting and the rise of the voice, the crowd under the voice. The game already plays its own crowd sounds; the lines keep sentences short, repeat the key word on a big play, and let a one-word sentence ("Touchdown.") do what the pitch does on the air.

## 8. Checks the lines pass

- A line-check script written for the session (deleted afterwards with Whisper, at the owner's order) over the 312 new lines with both transcripts: 0 problems (ASCII, 2 to 150 characters, no digit or bracket, only the allowed placeholders, no duplicate, no stop-list word, no run of eight words from either transcript).
- `game\tests\test_rs1_radio_style.py`: the pools keep their sizes and IDs; the sentence length of the radio pools stays inside the band of section 2 (median at most 13, 90th percentile at most 22 words); no line that names the analyst gives the analyst a gender; every halftime line says the half; none of the old snack-bar words returns; the style guide has every heading.
- Updated expectations in `test_sz1_commentator.py` (the first hand-off and the first booth line).
- The listening round: the owner hears a whole game of the new lines (PLAYTEST_LIST).
