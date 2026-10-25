### 5.12 Scores, the end of a game and the saved game [CODE (lifted, S3.4)]
- Touchdown: say4 " TOUCH DOWN" (logged with the replay list), foot11, playcel (crowd 2 up, 8 to 15 celebration sounds, 0.4 s, foot12 at -500, crowd 2 down), 6 points; the player: rady and the choice of 4.17; the computer: rady and the extra point kick.
- Every score then (field goal, extra point, two-point try; a safety joins here): the points are added; in overtime the game ends at once (5.6 item 7; not after a safety); otherwise SayScore (" The score is " + the sentence of 5.4), a synchronous Speak " " (waits for the end of the speech), rady, a banter line (5.13), the key wait (4.19), and the kick-off with the other side receiving.
- Save Game and concede: 4.18. football.sav: section 12.
- What pag leaves for the rest of the program: Me.m414(1) and (2) (the final or conceded score; pog uses them, S3.6), SavedGame (1 after Save Game), gtp (0 after a Super Bowl game, else unchanged; pog advances it, S3.6). Form_Load decides the rest (section 3 step 8).

### 5.13 The announcer's banter (GoSub 0x45915e, S3.5) [CODE (lifted); the 142 lines, their numbers, texts, bleeps and the rate step are taken out of the lifted text by `work/extract_banter_s35.py` and checked against the string table: 142 lines in order from 1 to 142, no gaps, all 196 strings of the class used, nothing missing; the table below is generated from that, never typed]
Remarks of the announcer (spoken in the announcer's voice), most of them addressed to "Ghip", the color commentator (section 9). When it runs: after every score (5.12: after SayScore, the " " speech and rady, before the key wait), after every change of possession (interception, fumble, turnover on downs, punt, missed field goal; 5.11 item 6) and after a normal play with chance 1 in 4 (`Int(Rnd * 4) + 1 = 2`, 5.11 item 5) (S5.2, audit finding A-15: also with chance 1 in 4 after the statistics of quarters 1 and 3, before the position and the down, because that path joins the same draw, pag 0x45f304 to 0x4510b6, 4.19). One call:
1. Comments off (comtog = 1, F8): nothing happens, no speech, no sound.
2. When 142 lines have been used in this game (L7dc = 142) nothing happens (not reachable in a normal game); otherwise the count L7dc grows by 1.
3. n = Int(Rnd * 142) + 1, drawn again while n is one of the lines already used in this game (history L8b4, empty at the start of every game, not saved, Q37): no line is spoken twice in a game.
4. L778 = Int(Rnd * 58) + 1 chooses <NAME>, the name L480(L778) of the banter name list (5.5 set-up: the 29 running backs, receivers and defensive players of the player's team, then of the opponent; no quarterbacks, special teams players or kickers); then rady (a random pause, section 7).
5. The texts of line n from the table below. <NAME> is that one name (the same one wherever it appears in the line); line 45 names the opponent's quarterback (Me.m2b8(2)); lines 101 and 110 choose their second text with a draw, Int(Rnd * 5) + 1 and Int(Rnd * 3) + 1, each alternative equally likely.
6. clk, then the first text is spoken with say (announcer, waits until it has been spoken, logged). Line 113 only: the speech rate is vr + 1 for that text and vr again afterwards. After the first text, lines 69, 72, 75, 83 and 140 play the bleep foot13 (play, waits; line 75 plays it twice in a row): the five lines stop at a swear word and the bleep covers it; the second text (lines 69 " Ghip! " and 72 " was that ") follows the bleep. clk, then the second text with say when the line has one, then clk. Nothing in this routine can be skipped with a key (only the global hot keys act, 8.1).
The table: n is the line number (the draw), "first" and "second" are the two texts as spoken (leading and trailing spaces as in the exe; the texts keep their spelling, including "ware", "klobbered", "masscot", "Felder Carb!", "reffer ease"). 15 lines use <NAME> (1, 9, 11, 23, 24, 36, 40, 46, 50, 51, 52, 62, 68, 82, 90); 30 lines have a second text. A keyword scan for the Q-018 decision at S11.1 (cheerleaders, underwear, sex jokes, jokes about a partner, drink, drugs, the five bleeped swear words) flags 35 of the 142 lines (`work/banter_keywords_s35.txt`; some hits are harmless, for example "nuts" and "box"): the owner decides at S11.1 (D-015, Q-018). (Game, OWNER DECISION 2026-10-14: these 142 lines become the defaults B001 to B142 of the player's file `banter.txt`, where any line can be changed or switched off and new lines of own text or own sounds added; D-035, CUSTOMIZABLE_CONTENT 12, 17.4.)

<!-- BANTER-TABLE-BEGIN -->
| n | first text (say, waits) | second text (say, waits; empty = none) | notes |
|---|---|---|---|
| 1 | " It looks like <NAME> is shaken up on the play " |  |  |
| 2 | " Wow! what a play " |  |  |
| 3 | " I wonder if that cheerleader knows that she forgot to ware her panties " |  |  |
| 4 | " Hey Ghip how come you got a hotdog and beer and I didn't? " |  |  |
| 5 | " Ghip is that a flag on the field or just a hotdog wrapper? " |  |  |
| 6 | " Look Ghip the fans are starting up another wave " |  |  |
| 7 | " Is that two footballs stuffed into that cheerleaders top or what? " |  |  |
| 8 | " Here are some scores from other games being played today " | " 3 to 0  7 to 3  and 14 to 0  in the fourth " |  |
| 9 | " The helmet of <NAME> is rolling around on the field " | " I hope that his head isn't in it " |  |
| 10 | " They will definitely have to look at that play on instant replay " | " Well maybe not " |  |
| 11 | " Ghip did you know that <NAME> once dated my sisters husbands brothers best friends next door neighbors sister? " |  |  |
| 12 | " Ghip how do you get your hair to stay like that? " |  |  |
| 13 | " Ghip where did you get that great suit I got to get me one" |  |  |
| 14 | " How was your dinner on the airplane last night Ghip? " |  |  |
| 15 | " It looked like he about took his head off on that play " |  |  |
| 16 | " Ghip what happend on that last play? I missed the whole play. " | " I was watching a cheerleader eat a hotdog" |  |
| 17 | " Holy cow that was great! I have never seen anything like it before " |  |  |
| 18 | " That was the stupidest play i have ever seen " |  |  |
| 19 | " The dog pound is in rare form today " |  |  |
| 20 | " Could some one please get some of these empty beer cans out of my way " |  |  |
| 21 | " Ghip whos on first? " |  |  |
| 22 | " When was the last time that you saw a play like that? " |  |  |
| 23 | " What a hit <NAME> took on that play " |  |  |
| 24 | " <NAME> has just set an all time new record " |  |  |
| 25 | " I remember when I could run like that " |  |  |
| 26 | " How about that! Ghip? " |  |  |
| 27 | " I can not believe that they called that play " |  |  |
| 28 | " do you still have that stupid dog of yours Ghip? " |  |  |
| 29 | " Ghip was that your wifes brother that I saw her with last night? " |  |  |
| 30 | " Ghip get that vendor back here my nuts are staile " |  |  |
| 31 | " Yes sir! this has turned out to be one heck of a game here today " |  |  |
| 32 | " I will bet you anything that he couldn't do that again " |  |  |
| 33 | " Well that play will have to either stand or not, unless! " | " Nope i guess that it will have to go one way or the other " |  |
| 34 | " How many hotdogs is that for you Ghip old buddy? " |  |  |
| 35 | " Ghip are your in laws still living at your house? " |  |  |
| 36 | " I can not believe that <NAME> is getting up after that " |  |  |
| 37 | " Cha ching bodda bing " |  |  |
| 38 | " Hey Ghip, can you lend me fifty bucks untill pay day? " |  |  |
| 39 | " Ghip pass me another beer " |  |  |
| 40 | " Ghip did you Know  that <NAME> has the biggest arms of any football player? " |  |  |
| 41 | " That looked like a busted play to me " |  |  |
| 42 | " So Ghip, what do you think of this weather we're having? " |  |  |
| 43 | " Ghip, what do you think of the price of rice in China? " |  |  |
| 44 | " Ghip, do you think that we will have a change in the weather? " |  |  |
| 45 | " A fan just hit <OPPONENT-QB> in the head with a dog bone " |  |  |
| 46 | " Ghip, DID YOU KNOW THAT <NAME> is thirty five years old today? " |  |  |
| 47 | " Ghip, if it was up to you would you have called that play? " |  |  |
| 48 | " How much money do you have riding on this game Ghip? " |  |  |
| 49 | " Ghip check out that W. M. M. S. T shirt on that lady in section 36 double Dee! " |  |  |
| 50 | " Well Ghip, <NAME> and his wife just had their first baby " |  |  |
| 51 | " You have to love the way that <NAME> runs " |  |  |
| 52 | " How in the heck did <NAME> do that? " |  |  |
| 53 | " Ghip, your shoe is untied " |  |  |
| 54 | " Ghip, why is the sky blue? " |  |  |
| 55 | " Well they will never make it to the Super Bowl  with a play like that " |  |  |
| 56 | " Ghip, if you have nothing smart to say, then just shut up " |  |  |
| 57 | " I bet that if they had not called that play, that would not have happened " |  |  |
| 58 | " hey Ghip " | " how much wood would a wood chuck chuck  if a wood chuck could chuck wood? " |  |
| 59 | " Ghip? Ghip? " | " wake up Ghip! " |  |
| 60 | " Rock n Roll " |  |  |
| 61 | " I wonder if they can pull off the 3 peat " |  |  |
| 62 | "<NAME> just klobbered the masscot " |  |  |
| 63 | " Ghip how was the hoe down last night? " |  |  |
| 64 | " Wow! I've never seen a cheerleader do that before " |  |  |
| 65 | " The fans are starting to file out after that play " |  |  |
| 66 | "Ghip, I believe in random drug tests " | " I've randomly tested quite a few of them myself " |  |
| 67 | " Ghip why are they putting that cheer leader on a stretcher? " |  |  |
| 68 | " Ghip have you seen the <NAME> bobble head doll? " |  |  |
| 69 | " Holy " | " Ghip! " | bleep foot13 after the first text |
| 70 | " well that'll take the starch out of your shorts! " |  |  |
| 71 | " They'll want to ree inflate that pig skin " |  |  |
| 72 | " Ghip what the " | " was that " | bleep foot13 after the first text |
| 73 | " zea ow e. " |  |  |
| 74 | " shazzam " |  |  |
| 75 | " holy " |  | bleep foot13 twice after the first text |
| 76 | " take my wife " | " please! " |  |
| 77 | " Ghip why are the cheerleaders on the field? " |  |  |
| 78 | " frack! " |  |  |
| 79 | " Take off A. " |  |  |
| 80 | " Frickin A. " |  |  |
| 81 | " sit on it Ghip " |  |  |
| 82 | " I haven't seen <NAME> do that since he was in the Canadian league " |  |  |
| 83 | " What total bull " |  | bleep foot13 after the first text |
| 84 | " Hey diddle diddle " |  |  |
| 85 | " Ghip, why is six afraid of seven? " | " because 7 8 9 " |  |
| 86 | " Ghip, my thong is riding up " |  |  |
| 87 | " I hate when that happens " |  |  |
| 88 | " Hey Ghip, If peter Piper picked a peck of pickled peppers? " | " how many peppers did Peter Piper pick? " |  |
| 89 | " What's up with that? " |  |  |
| 90 | " <NAME> should be penalized for ruffing the cheerleader on that play " |  |  |
| 91 | " Ghip, one day your head is going to open up. " | " and a prize will come out. " |  |
| 92 | " Ghip, my girlfriend can't wrestle worth a darn, " | " but you should see her box. " |  |
| 93 | " Ghip, are you still riding that soft tail? " |  |  |
| 94 | " She wore an its e bits e teen e ween e yellow poke adot bikini " |  |  |
| 95 | " Ghip, why do they call them apartments when they R all together? " |  |  |
| 96 | "Ghip, always said " | "Life is like, A box." |  |
| 97 | "Felder Carb!" |  |  |
| 98 | "lip stick" |  |  |
| 99 | "Ghip, look there's the twins " | "whore tense and Lisa, Bush." |  |
| 100 | "Ghip, do you know what a rhetorical question is? " |  |  |
| 101 | "Ghip, have you stopped" | "sucking your thumb?" or "beating your wife?" or "beating your kids?" or "cross dressing in public?" or "cheating on your taxes?" | second text is one of the alternatives (equal chance) |
| 102 | "Ghip, what happened to the reffer ease guide dog?" |  |  |
| 103 | "Ghip, you know I always thought that harass was two words." |  |  |
| 104 | "Ghip, you know on the other hand." | "you have different fingers." |  |
| 105 | "Ghip" | "What would you do with a brain if you had one?" |  |
| 106 | "Ghip, you know I don't suffer from insanity" | "I enjoy every minute of it." |  |
| 107 | "Ghip, Always remember you're unique, just like everyone else." |  |  |
| 108 | "Ghip, did I ever tell you that I know karate" | "and seven other Chinese words." |  |
| 109 | "Ghip, If we aren't supposed to eat animals, why are they made of meat?" |  |  |
| 110 | "Ghip, If life hands you lemons" | "make lemonade" or "make a bourbon sour" or "squirt them on lobster" | second text is one of the alternatives (equal chance) |
| 111 | "Ghip, look there are the twins" | "rent and lisa bush." |  |
| 112 | " How many beers is that for you Ghip old buddy? " |  |  |
| 113 | " red leather yellow leather red leather yellow leather red leather yellow leather red leather yellow leather red leather yellow leather " |  | spoken one rate step faster |
| 114 | " Ghip." | " you talkin to me? " |  |
| 115 | " Ghip, look at that ladies T-shirt.  It says. " | " Who needs brains when you have these. " |  |
| 116 | " O M G Ghip " |  |  |
| 117 | " Ping my Twitter Ghip " |  |  |
| 118 | " Wow they threw everything but the kitchen sink into that play " |  |  |
| 119 | " holy doughnuts " |  |  |
| 120 | " Butterscotch " |  |  |
| 121 | " Ghip I do not have a cell phone " | " because I have never been in jail " |  |
| 122 | " Ghip yesterday your wife was on my face " | " book " |  |
| 123 | " suffering succotash " |  |  |
| 124 | " Wow! " |  |  |
| 125 | " Ghip is that a pair of panties on top of the goal post? " |  |  |
| 126 | " Bummer Dude " |  |  |
| 127 | " Ghip I'd love to poke that cheer leader's in box " |  |  |
| 128 | " Ghip my wife wouldn't know I was missing unless my picture was on the side of a bon bon box " |  |  |
| 129 | " Ghip the last thing I want to do is to hurt you " | " but it's still on the list " |  |
| 130 | " Ghip my eye phone is on the blink again " |  |  |
| 131 | " Ghip is it just me or do giant eagle wings taste like chicken? " |  |  |
| 132 | " here kitty kitty " |  |  |
| 133 | " Ghip go ahead. make my day! " |  |  |
| 134 | " Gidder done! " |  |  |
| 135 | " Ghip " | " you just might be A red neck " |  |
| 136 | " Who's your daddy " |  |  |
| 137 | " Well Twitter my bits " |  |  |
| 138 | " That will put the starch in your jock " |  |  |
| 139 | " Oh Snap! " |  |  |
| 140 | " Son of A. " |  | bleep foot13 after the first text |
| 141 | " Take a hike Ghip. " |  |  |
| 142 | " Why don't you go and Google yourself Ghip. " |  |  |
<!-- BANTER-TABLE-END -->

### 5.14 The season engine: a regular week (`pog`, p_4615b0, gtp 1 to 16) [CODE (lifted, S3.6); checks: every Rnd draw against the exe (`work/rnd_check_pog_s36.txt`, 48 draws, 0 mismatches), every integer constant against the asm (`work/const_check_pog_s36.txt`: 1,014 constants, the 191 misses are all folded subscripts of the multi-dimensional arrays, `work/const_miss_filter_s36.py`), the score table (`work/score_tables_s36.txt`), every literal against the string table (`work/texts_check_s36.txt`), every write of the sentence variable against the asm (`work/assign_append_pog_s36.txt`) and every spoken sentence on every path (`work/sentences_pog_s36.txt`)]
pog runs after a game that was not saved, when gtp is not 0 (section 3 step 8); everything in 5.14 to 5.17 is decided and spoken at once, then the original speaks the standings and ends (D-024: the game returns to the menu). It plays no sound (the crowds were stopped by pag). Arrays: records(division 1 to 8, team 1 to 4, 1 = wins or 2 = losses) and "played this week"(division, team) are multi-dimensional (B-P29: index division + 9 x team + 45 x kind).
1. Every call: the eight division names (section 11), the score table T(1 to 32) = 0, 0, 3, 3, 6, 6, 7, 7, 9, 9, 10, 10, 12, 12, 14, 14, 17, 20, 20, 21, 21, 21, 24, 28, 31, 35, 38, 41, 42, 45, 49, 51 (finplay17 has the same table; checked by script), ptf = 1 (all of it goes to the log), GetTeams, L3d0 = 0 (set to 1 when the player wins a play-off game), the replay list emptied. Every team is marked "not played" (-1) and the records are set to 0; then the player's team is marked with its score Me.m414(1) and this week's opponent (tn3, tn4) with Me.m414(2). gtp 17 or more: the play-off weeks (5.16).
2. footbal3.dat is read (64 values, section 12). It is opened For Binary Access Read without a Dir check: in week 1 it does not exist yet, the VB runtime creates it empty and every record stays 0 (S3.6 runtime finding, section 12).
3. Randomize Timer; say2 " Games of week number <n>. " (n = the week just played, Trim$, so " Games of week number 5. "). All lines of this week are say2: asynchronous, logged, in the replay list.
4. The player's game: the player's team wins when its score is higher, otherwise the opponent wins (a tie would go to the opponent; a game cannot end tied, 5.6, Q41). say2 "<winner> over the <loser> by the score of <winner's score>, to <loser's score>. " (no "The" in front, Trim$ numbers, for example "Bears over the Lions by the score of 24, to 17. "); wins + 1 for the winner, losses + 1 for the loser.
5. The other 15 games, one at a time: team A = a random team not yet played this week (division Int(Rnd * 8) + 1, team Int(Rnd * 4) + 1, drawn again while played), its score index a = Int(Rnd * 32) + 1, A is now played; team B the same way, its index b = Int(Rnd * 32) + 1 drawn again while T(b) = T(a); the higher score wins (b > a: B, else A). say2 "<winner> over the <loser> by the score of <w>, to <l>. ", records updated. The other 30 teams follow no schedule: the pairings are new every week (a team can meet the same opponent several times and never meet its division rivals, Q42). Each table entry is drawn with chance 1/32 (scores 0, 3, 6, 7, 9, 10, 12, 14 and 20 have two entries, 21 three, the others one), the loser's again while equal, so no game is tied.
6. A blank line in the log; gtp = gtp + 1; footbal3.dat written (same order).
7. The wait: clk, getkey (no ambient sounds; the first key stops the speech, which is still running): F1 or F2 (or a global hot key, which ends as F1, D-018): clk, the replay list emptied, the 17 lines (heading, the player's game, the 15 others) spoken again with say2, and the wait again; any other key goes on.
8. gtp now 2 to 16: football.gtp written (gtp), pog returns; Form_Load speaks the standings (5.2, " Standings after week number <gtp - 1> ") and ends. gtp now 17 (week 16 was played): the end of the regular season (5.15).

### 5.15 The end of the regular season (pog after week 16) [CODE (lifted, S3.6); the four sorts checked in the asm at 0x466ee1, 0x46826d, 0x468e90, 0x46a540: operand order and the array (losses or wins)]
1. All records set to 0 and read again from footbal3.dat.
2. Division winners: in each division 1 to 8 the four teams are ordered by LOSSES, fewest first (insertion sort; equal losses keep the team order 1 to 4; the wins are not looked at); the first is the division winner. In the player's division, when the player's team is not first but has as many wins as the first (every team has played 16 games, so the same record), the player's team is the division winner instead (Q43).
3. The replay list emptied, ptf = 1, say4 " the division winners are. ", then for each division 1 to 8: say4 its name (" A. F. C. North. " ...) and say4 "<team>. at <wins> and <losses>. " (Trim$ numbers: "Steelers. at 12 and 4. "; the record is the first team's, the same as the player's when the player won the tie). A blank line in the log.
4. Wild cards, per conference (A. F. C. divisions 1 to 4, N. F. C. 5 to 8): the 16 teams in division and team order, the four division winners given 0 wins and 20 losses so they come last, are ordered by losses, fewest first (insertion sort, ties keep that order); the first two are wild card 1 and wild card 2. When the player's team is neither a division winner nor one of the two, is in that conference and has as many wins as wild card 2, it takes wild card 2's place (Q43). say4 " the A. F. C. wild card teams are. " and "<team>. at <wins> and <losses>. " for both (the record spoken for wild card 2 is the replaced team's, equal to the player's), then " the N. F. C. wild card teams are. " and its two. A blank line in the log.
5. Seeds, per conference: the four division winners ordered by WINS, fewest first (insertion sort, ties keep the division order North, East, West, South): D1 (fewest wins) to D4 (most). Wild card round (footbal4.dat, section 12; in each record the first team is the visitor, the second the home team): A. F. C. wild card 1 at D1, wild card 2 at D2, then the same for the N. F. C.; D3 and D4 have a bye (footbal5.dat: A. F. C. D3, D4, N. F. C. D3, D4). The bracket is fixed (Q44): in the division round the winner of a conference's first wild card game plays at its D3 and the winner of the second at its D4; in the championship the winner of the conference's first division game plays at the winner of the second; in the Super Bowl the A. F. C. champion plays at the N. F. C. champion. footbal4.dat is deleted first (k4), footbal5.dat too when it exists (Kill), because a Binary write does not shorten an existing file.
6. Where the player's team is: in footbal4.dat (a wild card game): the wait (norep = 1, getkey; F1 or F2: the instant replay of the list, the division winners and wild cards, without the introduction, then the wait again; any other key goes on, norep = 0), football.gtp = 17 written. Form_Load then speaks the standings after week 16 and ends; the next start is the wild card week.
   In footbal5.dat (a bye): the same wait, then the wild card games are played without the player: the replay list emptied, say4 " In the A. F. C. wild card games. ", the two A. F. C. records, " In the N. F. C. wild card games. ", the two N. F. C. records, each a computer game (5.17 item 2) with its own say4 " The <winner> won over the <loser> by the score of <w> to <l>. "; footbal4.dat is written for the division round (item 5); the wait again; gtp = 18 written. Form_Load says no standings (SayStand is silent above 17, Q51) and ends; the next start is the division week.
   In neither (out): say4 " The <team> at <wins> and <losses>. did not make it into the playoffs. " (Str$ numbers) (S5.2 exact text, audit finding A-12, pog 0x46f73c to 0x46f9e3: RTrim$(" The " & team & " at " & Str$(w) & " and " & Str$(l)) & ". " & " did not make it into the playoffs. ", so two spaces follow the full stop: " The Bears at  7 and  9.  did not make it into the playoffs. "), a blank line in the log, the wait, then finplay17 (5.17) plays all four rounds and sets gtp = 0; pog then returns WITHOUT writing football.gtp (the file still says 16), and Form_Load's exit deletes the season files because gtp = 0 (section 3 step 9). Q-027 answered: the original never reaches a play-off week without the player's team.

### 5.16 Play-off weeks with the player's team (pog, gtp 17 to 20) [CODE (lifted, S3.6); spoken sentences on every path by `work/check_sentences_s36.py`]
After the player's play-off game (Form_Load found the player's pairing in footbal4.dat, section 3 step 7c):
1. gtp = gtp + 1, the replay list emptied (L3d0 = 0 from 5.14 item 1).
2. The round by the old gtp: 17 (wild card week): say4 " In the A. F. C. wild card games. ", records 1 and 2 of footbal4.dat, " In the N. F. C. wild card games. ", records 3 and 4. 18 (division week): " In the A. F. C. division play off games. ", records 1 and 2, " In the N. F. C. division play off games. ", records 3 and 4. 19 or more (championship week): " In the A. F. C. championship  game. " (two spaces), record 1, " In the N. F. C. championship game. ", record 2.
3. A record with the player's team is the player's game: the player's team wins when its score is higher (a tie goes to the opponent, Q41), the sentence is " The <winner> won over the <loser> by the score of <winner's score> to <loser's score>. " (Str$ numbers) and L3d0 = 1 when the player won. Any other record is a computer game (5.17 item 2). The winner's division and team are kept for the next round.
4. What is spoken: each result as its own say4 " The <winner> won over the <loser> by the score of <w> to <l>. ", except (Q46, all found by the path script and confirmed in the asm): (a) wild card week: the two A. F. C. results are one say4 text, and when the player's game is the second A. F. C. record the first record's result is never spoken (the player's sentence is assigned over it); (b) a computer result loses its leading " The " ("Bears won over the Lions by the score of ...") for the third record of the wild card week, the second record of the division week and the A. F. C. record of the championship week (the sentence is assigned instead of appended, 0x475452, 0x478c56, 0x47b990 and their pairs); (c) when the player's team plays the A. F. C. championship its own result is never spoken: after the player's game the code jumps past the speak call (0x47b5ad, 0x47b621) and the N. F. C. heading replaces the sentence.
5. footbal4.dat (deleted first) is written for the next round: after the wild card week the four winners with the bye teams of footbal5.dat (winner n at bye n); after the division week two records (winner 1 at winner 2, winner 3 at winner 4); after the championship week one record (A. F. C. champion at N. F. C. champion).
6. The wait (norep = 1, getkey; F1 or F2: the instant replay of the round's lines without the introduction, then the wait again).
7. The player won: football.gtp = gtp written (18, 19 or 20: the next week); the original ends and the next start plays that round. The player lost: gtp = the next round (18, 19 or 20) and finplay17 (5.17) plays the rest; it sets gtp = 0, and pog writes football.gtp = 0. Form_Load says no standings (gtp is above 17 or 0) and ends; gtp = 0 deletes the season files.
8. The Super Bowl week: the player's Super Bowl game ends in pag (superbowl, gtp = 0, 5.6 item 7), so pog does not run. A CONCEDED Super Bowl (4.18) leaves gtp = 20 and pog runs its championship branch on the Super Bowl record (Q48): " In the A. F. C. championship  game. ", the player's result not spoken (4c), " In the N. F. C. championship game. ", the same record again (the Get past the end of the file leaves the values unchanged) so " The <opponent> won over the <player's team> by the score of <o> to <p>. ", footbal4.dat gets the opponent against itself, the wait, then finplay17 plays a Super Bowl " The <opponent> won over the <opponent> by the score of <w> to <l>. " with new random scores, the celebration and the wait; the season ends.

### 5.17 The play-off engine: the rounds without the player (`finplay17`, p_47d8b0) [CODE (lifted, S3.6); the On ... GoTo table read from the exe (`work/jumptables_s36.txt`), 36 Rnd draws checked (`work/rnd_check_finplay17_s36.txt`, 0 mismatches), the constants (`work/const_check_finplay17_s36.txt`: 331, the misses are subscripts encoded as displacements and zeros held in registers, read in the asm), the score table, the texts and the sentences by script]
Called by pog when the player's team is out after week 16 (gtp 17) or has just lost a play-off game (gtp 18, 19 or 20, the next round).
1. The replay list emptied, ptf = 1, the score table T (5.14), 0.2 s, Randomize Timer. It starts at round gtp - 16 (On ... GoTo: 1 wild card, 2 division, 3 championship, 4 Super Bowl; a value outside 1 to 4 starts at the wild card round) and plays every later round.
2. A computer game (here and in pog): the winner is the first team of the record (the visitor) when Int(Rnd * 2) + 1 = 1, else the second (the home team): 1 in 2 whatever the records or seeds (Q45); the winner's score index w = Int(Rnd * 32) + 1 drawn again while T(w) = 0, the loser's l = Int(Rnd * 32) + 1 drawn again while T(l) >= T(w), so the winner scores and the loser scores less. say4 " The <winner> won over the <loser> by the score of <T(w)> to <T(l)>. " (Str$ numbers; every game its own say4, `work/sentences_finplay17_s36.txt`).
3. Wild card round: say4 " In the A. F. C. wild card games. ", records 1 and 2, " In the N. F. C. wild card games. ", records 3 and 4; footbal4.dat (deleted first) for the division round (winner n at bye n of footbal5.dat); the wait (norep = 1, getkey; F1 or F2 replay without the introduction and wait again; any other key goes on). The replay list is emptied when the next round starts.
4. Division round: " In the A. F. C. Division play off games. " (capital D, unlike pog, Q47), records 1 and 2, " In the N. F. C. division play off games. ", records 3 and 4; footbal4.dat: winner 1 at winner 2, winner 3 at winner 4; the wait.
5. Championship round: " In the A. F. C. Championship game. ", record 1, " In the N. F. C. Championship game. ", record 2; footbal4.dat: the A. F. C. champion at the N. F. C. champion; the wait.
6. Super Bowl: " In the Super Bowl. ", the result; 0.2 s; norep = 1; the celebration: 8 to 15 sounds (Int(Rnd * 8) + 8), each a random foot15 to foot24 at -300 + wavol with frequency = original + 100 x k (k = Int(Rnd * 40) - 20, drawn again while 0; at least 8000 Hz), each waited to its end (keys do not stop it; no crowd ramp, no foot12, no foot25). Then getkey: F1 or F2: the instant replay (the Super Bowl lines) without the introduction, a 5-second pause and the celebration again with new sounds (Q50), then the wait again; any other key: norep = 0, gtp = 0 (the season is over), return to pog.

## 6. Randomness and seeding (5.5)
- Every `Randomize` call in the program (13 call sites in 11 procedures: p_41eaa0, p_41f320, p_42bfc0, p_42e980, p_42fa70, p_43a330, p_43a860 (3 sites), p_4314d0, p_4615b0, p_47d8b0, p_485b80) is `Randomize Timer` (a Single, seconds since midnight, passed as a Variant of type 4). The generator is reseeded from the clock many times in a session, so no game can be repeated from a seed. [CODE: scripted scan of all 13 call sites, P2 S2.1]
- `Rnd` (rtcRandomNext) is called 172 times (p_43a860 61, p_4615b0 48, p_47d8b0 36, p_484860 6, the rest 1 to 4 each) (S5.2 correction, audit finding A-14: 172 and 61 are the counts of the raw Ghidra export; the gap-filled assembly of D-012 in `work/ghidra` has 198 calls: p_43a860 87 (= the 63 + 24 draws checked below), p_4615b0 48, p_47d8b0 36, p_484860 6, p_42fa70 4, p_43a330 4, p_41eaa0 3, p_41f320 3, p_485b80 3, p_4314d0 2, p_42bfc0 1, p_42e980 1; counted by a scan for rtcRandomNext over all 64 files). The pattern seen in p_43a860 is `Int(Rnd * N) + 1` (a coin flip is `Int(Rnd * 2) + 1`, the constant 1.0 at 0x4013a8). Each use (which table, which N) is recovered in P3. Done: every draw is written where it is used (sections 4.12, 5.1, 5.3, 5.5 to 5.17, 7) and was checked against the exe: the engines by `tools/vb6_rnd_check.py` (pag's main body 63 lifted draws in S3.4, its GoSub routines 24 in S3.5, pog 48 and finplay17 36 in S3.6; 0 mismatches of N, `work/rnd_check_pag_main.txt`, `work/rnd_check_pag_gosub.txt`, `work/rnd_check_pog_s36.txt`, `work/rnd_check_finplay17_s36.txt`), the smaller procedures of S3.2 and S3.3 (makes, sgc, Getqbs, rady, PlayRan) by reading them with the assembly beside them (the headings of 5.1 and 5.3 say what was checked there). [CODE]
- Game: seeded from the system clock too (same distribution; the game's tests use a fixed seed). [INFERRED, D-013; this is a game decision, not a finding about the original; one generator behind one function, G-D2, tested in S8.1]

## 7. Timing
- There is no Timer control, no timer event and no multimedia or API timer in the program (the only imports used for time are `rtcGetTimer` = `Timer` and `rtcDoEvents`). [CODE]
- Waiting is done by busy loops over `Timer` (seconds since midnight as a Single) with `DoEvents` inside: `dy(seconds)` (p_42e880, a fixed pause; used 28 times, e.g. between crowd volume steps and between announcements), `rady` (p_42e980, a pause of random length; 40 calls, mostly in the play engine), `getkey2` (p_429c00, waits for a key while calling the ambient-sound player PlayRan on every pass), and `PlayRan` itself (schedules the next ambient sound with a Timer value kept in the variable `st4`). The original clock is not midnight safe (a Timer rollover during a wait would end the wait early or hang); the game uses a monotonic clock. [CODE for all four, lifted and read in full]
- `rady` = `Randomize Timer`, n = Int(Rnd * 30) (0 to 29), r = the speech rate vr but at least 1, waits n / (r * 25) seconds: with rate 0 or below up to 1.16 s, with rate 5 up to 0.23 s (the pause gets shorter as the player speeds the speech up). Keys are processed during the wait but never end it. [CODE (lifted)]
- `dy(s)` waits exactly s seconds (a Variant argument, usually a Single or Double such as 0.1, 0.2, 0.3, 0.4, 2.5); keys are processed but do not end it. [CODE (lifted)]
- Other fixed times seen in this batch: crowd 2 ramp step 0.1 s (a full ramp from the base level is 1.3 s), PlayTackle waits 2.5 s, playcel waits 0.4 s before its last sound, inrep waits 0.2 s after its introduction, readins waits 0.3 s between its two parts; PlayRan: first ambient sound 5 s after a getkey2 wait starts, later ones 3 to 10 s after the previous one started (Timer + Rnd * 7 + 3) and only when the previous one has ended. [CODE (lifted)]
- The game clock (quarter time, two-minute warning and so on) is simulated in the variables `mins`, `secs`, `CountDown`, `oldtime`, `M2W`, `M4W`, `M5W` by `sgc` (p_42bfc0), not read from a real-time clock. [INFERRED from the variable names and uses; confirmed in P3: CODE (lifted, S3.3 and S3.4), the formulas are section 5.3 and 5.6 item 8]
- Sound fades (`c2uh`, `c2uf`, `c2dh`, `c2df`) step the crowd 2 volume in a For loop (steps of 100, i.e. 1 dB) with a 0.1 s `dy` pause per step; c2uh never runs its loop (section 10). [CODE (lifted)]
- How speech, pauses and sounds interlock (P4 S4.3; gap register G-S1 to G-S3, G-A1; [CODE (lifted)] and TESTED, `work/sapi_*_test_s43.txt`, `work/pause_table_s43.txt`):
  1. Speech has three modes on one SpVoice object: flags 0 (say, say3, say4, the bare `Speak " "`) returns when the WHOLE queue of that voice is spoken, so it is also a barrier for every asynchronous line queued before it; flags 1 (say2, say5, say6, the replay lines, the key echo, the bare `Voice.Speak " Hike! ", 1`) queues and returns at once, queued lines play in order with no pause between them; flags 2 with "" (stopspeech: getkey, getkey2 and the key echo call it) purges the queue, so the first key at a key wait cuts everything.
  2. A voice reload (`Set Voice = Nothing`, a new SpVoice) stops speech that is still running (tested: a long text released at once rendered 0 percent, after 0.3 s 72 percent). say3 guards its reload with a synchronous `Speak " "` on the old voice, which waits for the old queue; the announcer's speakers (say, say2, say4, say5, inrep) reload only after say3 or the F11 and F12 menus, when nothing is pending. Unguarded: " Hike! " (asynchronous, quarterback voice) then PlayHike, the 0.6 s ramp c2dh (S5.2 correction, audit finding A-13: 0.7 s, 7 steps of 0.1 s from wavol down to -600 + wavol, p_41d240, counted as the 1.3 s of c2uf are) and say4 in the announcer's voice: with two different voice numbers a "Hike!" still speaking after the ramp is cut (Q52).
  3. 68 pause sites (28 dy, 40 rady; S5.2, audit finding A-09: every site is listed with its procedure, address and the events next to it in `work/pause_table_s43.txt`, generated by `games\tools\vb6_pause_table.py`; it is a check list in text order, not the flow: the sequences of sections 3 to 5 give the order on each path (S5.2 completed kicksnap in 5.10, the touchdown countdown in 5.11 item 2 and the kick-off return in 5.10), and the S8.1 conformance tests compare the game's pause sites with the list): 49 follow a synchronous say (an audible gap), 6 follow an asynchronous say (the pause runs under that speech, no gap), 6 follow a sound or ramp (3 ramps, 3 waited sounds), 7 sit inside the helpers (the four ramps' 0.1 s, PlayTackle's 2.5 s, inrep's 0.2 s, one in finplay17). rady = Int(Rnd * 30) / (max(vr, 1) * 25) s: 0 to 1.16 s, mean 0.58 s at rate 1 or below, 0.12 s at rate 5. A snap count has about 4.4 rady (mean 2.6 s at rate 1 or below). The game's model: one FIFO speech queue, asynchronous = queue and return, synchronous = queue and wait for the empty queue, pauses on a monotonic clock while queued speech plays, nothing cut by a voice change (D-031).
  4. Str$ doubled spaces (" game number  1") change nothing audible: the length of the audio was identical in 56 of 56 renders with six different voices (seven runs) (the samples differ only as the same text differs from itself); the game keeps the original's exact strings (supersedes the remark in D-025).

## 8. Input
### 8.1 Key model (P3 S3.2) [CODE (lifted)]
- All keys come through `Form_KeyDown(KeyCode, Shift)` (p_42e5e0, read in full). The `Shift` argument is never used (Shift+F5 is F5). F10 (121) and Alt (18) are swallowed (KeyCode set to 0 so Windows does not open a menu) and treated as the key code "27" (Escape) with g2 empty. Every other key stores the key code as text in `g` and `g2 = LCase(Chr(key code))`: letters and digits give themselves, Space gives " ", the numeric keypad keys 96 to 105 give "`" and the letters a to i, 106 to 111 give j to o, F2 F3 F4 give q r s, F9 gives x, the arrow keys 37 to 40 give % & ' (, Enter, Backspace, Tab, Esc give control characters. Key repeat (a held key) calls KeyDown again each time. A key that arrives while no wait is running is lost: the next `clk` clears it (S5.2: except the keys typed during a synchronous line, which survive with their code, last bullet of 8.1, G-K1). [CODE]
- Key states are strings: "112" F1, "113" F2, "114" F3, "115" F4, "116" F5, "117" F6, "118" F7, "119" F8, "122" F11, "123" F12, "27" Esc (also Alt and F10), "13" Enter, "38" Up, "40" Down, "17" Ctrl, "16" Shift, "8" Backspace. [CODE]
- The waits (all read in full): `clk` (p_429ac0) sets g = "" and g2 = "" (a DoEvents after each); `getkey` (p_429b40) = clk, loop with DoEvents until g is not empty, then `stopspeech`; `getkey2` (p_429c00) = st4 = Timer + 5, clk, the same loop with `PlayRan` called on every pass, then stopspeech. The speech of the prompt is therefore always cut off by the first key (any key, also Shift and Ctrl). `getkey2` is used by the play engine (7 calls) so ambient sounds play only while the player thinks about a play; every other wait is `getkey` (31 calls in 12 procedures). [CODE, call counts from the lifted text]
- Then the handler runs the global keys at once: F5 `speckeys`, F6 `readins`, F7 `SayHints`, F8 `ctog`, F11 `adjvol`, F12 `ChangeVoice`, Ctrl (17) `adjrate`. These keys therefore work at any moment, also in the middle of a wait of another procedure (the handler runs inside that wait's `DoEvents`), and each of them is its own small modal menu with its own key waits. [CODE]
- The other keys (F1 repeat, F2 replay, F3 score, F4 clock, Esc, Enter, arrows, letters, digits) are read by the key waits above and the typing helper `getter` (8.2). The table "key by state" grows with each batch: hot-key menus (section 4.2 to 4.8) and the typed-text prompt (8.2) are complete; the main menu is in section 4.1 (corrected in S5.1: the main menu is the first bullet of section 4; 4.1 is the hot-key menus); the game's menus and questions are in 4.14 to 4.19 (S3.4). [CODE]
- After a global key's menu: all seven (speckeys, readins, SayHints, ctog, adjvol, ChangeVoice, adjrate) end with `clk` and then `g = "112"`, the code of F1 (S5.2: except ChangeVoice when only one SAPI voice exists, which returns at once and leaves F12 in g, 4.7, Q59). The interrupted wait therefore ends as if the player had pressed F1, and F1 means "repeat the current prompt" at the prompts read so far (main menu, schedule question, volume menu, team, coach and name prompts, the game). So the observable result is: the menu runs, then the interrupted prompt is spoken again. Q-023 answered; D-018 updated (the game hands F1 to the interrupted wait). [CODE (lifted)]
- Key echo: `saykey` speaks the lower-case character of the key (g2) at rate vr + 5 after purging the speech, except for F1. [CODE (lifted)] (S5.2 correction, audit finding A-27, TESTED: saykey sets Rate = vr + 5, purges, queues the character ASYNCHRONOUSLY and sets Rate = vr at once, and SAPI renders the queued text at the restored rate: through that sequence a one-character echo and a sentence were byte for byte as long as at rate vr with the default voice, Microsoft David and Microsoft Zira, and a sentence on the sound device at volume 0 took 4.33 s against 4.34 s at vr and 2.51 s at vr + 5 (`games\tools\sapi_probes\sapi_echo_rate_test.py`, `work/sapi_echo_rate_test_s52.txt`). So the echo is HEARD at the normal rate vr; the + 5 never takes effect; quirk Q58, kept: the game echoes at the normal rate, G-S5.)
- A global key menu started from inside another one nests (F6 pressed during the F5 text runs a second menu inside the first); when the inner one ends it sets g = "112", and the outer one reads that as F1 (readins restarts its part 1, the others end their wait). The game dispatches the same global keys at every wait (D-018). [CODE (lifted)]
- Keys typed while a synchronous line is spoken (S4.3, G-K1, TESTED): Form_KeyDown runs only inside DoEvents; a synchronous `Speak` does not pump messages (a 24.1 s call let 0 timer messages and 0 posted messages through), so the keys wait in the Windows queue. The next pump (the first DoEvents of clk, which has just set g = "") delivers them in order, each overwriting g and g2, so only the LAST key survives; clk then clears g2 (not g), and the next key wait ends at once with that key's code and no character. Menus that read the code (Enter, Up, Down, F1 to F4, Esc) act on it (Enter typed during narration chooses item 1 of the next play menu, Q54); menus that read the character (digits, y, n, h, t, r, k) treat it as any other key. Keys typed during pauses and waited sounds are delivered at once: the global keys run their menu, any other key is cleared by the next clk. The starter kit's `KeyInput` implements exactly this; the game uses it unchanged and its added menus (F9) use `read_key`, which never discards a key. [CODE (lifted) + TESTED]

### 8.2 Typed text: getter, ccn, cqn (P3 S3.2) [CODE (lifted)]
- `getter(prompt)` (p_429d10) collects the typed text in the form string `r`: it clears the key, speaks the prompt with say5 (announcer, asynchronous), sets r = "" and then waits with getkey for each key: F1 speaks the prompt again and clears r; Shift (16) makes the next key upper case (UCase of its character, applied to whatever key comes next); Backspace (8) speaks the last typed character (saykey) and removes it, nothing when r is empty; Enter (13) ends the text; every other key is echoed (saykey: the character of the key code, at rate vr + 5; S5.2: heard at the normal rate, 8.1 key echo, Q58) and its character is appended to r. Esc has no special meaning here (it is appended as a control character and removed by the name check). [CODE]
- `ccn` (p_428f60, coach name) and `cqn` (p_429510, quarterback names) clean r: they keep only the characters with codes 32 (space), 48 to 57 (digits), 65 to 90 and 97 to 122 (letters), in order. If fewer than 2 characters were typed to begin with, or if only spaces (or nothing) remain, or fewer than 2 characters remain, the result is the default: `ccn` gives "coach" and `cqn` the empty string (the quarterback caller then keeps its own default, S3.3). There is no maximum length, no trimming of spaces, no capitalization of the first letter (the typed case is kept). [CODE]
- Consequences kept or changed in the game: D-022 (the keypad types letters in the original; arrows type % & ' ( that are spoken and then removed). The game stores at most 100 characters of a typed name (keys beyond that are echoed, not stored) and its window needs WM_CHAR for typed text (G-K5, D-031 item 4). S5.2 (audit finding A-31, D-034): the limit is 30 characters, the limit of every name in the customization files (CUSTOMIZABLE_CONTENT 10), because the own quarterback's typed name is appended to footplay.txt and read back by the same rules.

