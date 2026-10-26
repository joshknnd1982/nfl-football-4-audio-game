# NFL Football 4: the owner's playtest list (N. F. L. rules and Franchise)

Written in session SX.9 (2026-10-19). Everything here can only be judged by ear: the tests and simulations already check the rules, the
numbers and the files. Each point says what to listen for, how to get there, what the default is and what can be changed. Tell Claude
in words what you heard ("the flag prompt is too long", "too many news lines"); nothing has to be written down in a special way.

Sources: every session's "left open on purpose" list (work\review_sx*_findings.md), NFL_FRANCHISE_DESIGN sections 18 and 19, and
DECISIONS D-049 to D-079.

## Recommended order

1. Sitting 1, start-up and menus: about 10 minutes.
2. Sitting 2, one quick game with every switch on: one whole game, plus about 10 minutes for the playbook menus.
3. Sitting 3, the first weeks of a franchise: weeks 1 to 4, about 5 minutes of franchise speech besides the games.
4. Sitting 4, two offseasons: the first at the defaults (about 15 minutes), the next in short mode with the staff (3 to 5 minutes).
5. Sitting 5, many seasons: impressions that only come over time; no fixed length.

## Sitting 1: start-up and menus

1. The welcome sentence: "Welcome to Josh Kennedy's N. F. L. football, loosely inspired by Jim Kitchen's original games." Is it clear,
   and is its timing against the opening music right? (D-077)
2. The Rules setting. NEW in SX.9: a new player starts with the N. F. L. rules (before, Classic). F9, Rules: item 1 switches between
   Classic and N. F. L. rules; items 2 to 9 are the switches; item 10 resets them. Is the default right for you? (NQ2, D-079)
3. F9's help (F1 in the F9 menu): it now says "six items" when the Franchise item is there. (SX.9)
4. F9, About: two new pages, what was added to the original game, and the trademark notice for the playbook and franchise ideas.
   Does it read well, and is it not too long? (SX.9, NX-R6)
5. The help keys F5, F6 and F7 in a game with the N. F. L. rules: the added lines after the original text.
6. NEW in SX.14, the start-up question (D-089): after the welcome, when anything is saved the game says one sentence about each save and
   asks what to do. Try, one thing at a time: Enter alone (it continues the saved game, or the season if no game is saved); a season only;
   Save Game in the middle of a game (which place, then quit or keep playing) and start again; close the window in the middle of a game
   (without saving) and start again: the first item is "continue the game that was not finished" and the game goes on from the same play;
   delete a saved game (the question starts at no; then restore it); start a new game (it asks before it replaces your season and takes
   your last coach and team with one yes). Are the sentences clear and not too long? Is the first item right for you? Is it a nuisance
   that a season in progress is also a question at every start? Is the menu too long with three saves?

## Sitting 2: one quick game, every switch on

Since the T key and the onside offer were built (SX.2b, D-087) the onside question is already "always": it comes at every kick-off and safety kick of your team, and F9, Rules, Onside question can set it back to "when it makes sense". Press T many times in this game, in every place you can think of: a play menu, a question, the huddle, the snap count, before a kick, during a play, at the end of a quarter. It should always answer at once and never break the game.

1. The clock: how fast the time runs, the two-minute warning, "the clock is running" at the menu.
2. Time outs: the T key, which calls one at once wherever you are in a game (a play menu, a question, the huddle, the snap count, before a kick), cuts what is being said and says the time out; the play you called is not run and the menu comes again. Pressed while the play is running it waits and is taken when the play ends. The Time Out item is still there, by its number and Enter. The play menus have new items after the plays, and Save Game is always the last item
   (letter S), so its number is no longer 8. When does the computer call its time outs?
3. Penalties: the flag announcement, the accept-or-decline question (A or D, Up and Down, Enter), how long the question is, and how
   often flags come (about 13 accepted fouls a game, the NFL's average is 12.8). With F9, Rules, Offense and Defense playbook set
   to "Team playbook", both teams play a style: the game has about 14 flags, a little more pace and more quarterback runs (measured,
   D-079). Say if that sounds too busy.
4. NEW in SX.9: at a penalty question, press S. The game is saved with the question kept; load it from the main menu and the question
   is asked again first ("a penalty is waiting for your choice"). Where it cannot be kept (a score, a turnover, a try, the last second of
   a quarter or a half) the game says "the game can be saved after this choice". Is that clear? (C10, D-079)
5. Onside kicks: the question (Y or N, the answer starts at no), the kick's words, and the two whistles on a kick with a flag.
6. Quarterback runs: the items Sneak, Keeper and Draw (keys 8, 9 and 0), the remarks, how often the computer runs its quarterback.
7. Challenges: the item "Challenge the Ruling" (letter C), the hints that a ruling may be wrong, the booth review sentences. Are rulings
   wrong too often? With Time outs off a challenge still needs a time out: is that confusing?
8. Playbooks: F9, Rules, Offense playbook and Defense playbook. The default is Classic (the original's plays); "Team playbook" is the
   second choice, then the seven styles. Listen to the groups and the plays; Backspace, Left or the Back item go back. The computer's
   teams play their own team's style; say if you would rather have them play Classic.

## Sitting 3: the first weeks of a franchise

Start: N. F. L. rules, a new season, answer "which kind of season" with franchise. The staff setting is off by default.

1. The weekly news: 2 to 4 lines a week; are the streak lines (about 4 weeks in 5) and the upset lines too many? F8 does not silence
   the news: right or wrong?
2. The to-do list: the extra-work question in weeks 2, 6, 10 and 14. Is it useful or a chore?
3. The game plan item (only when a playbook is not Classic): it always recommends West Coast on offense. Should the staff's choice vary?
4. The weekly goal said before the kick-off, and its verdict after the game.
5. The injury report (about four lines a week, at most two questions a week) and the stand-in quarterback.
6. Trades in weeks 4 to 9: the offers (contract and picks are said), the trade news, trade demands.
7. Measured time: a week's franchise speech takes about 35 seconds (50 with the team playbooks, 23 with the staff setting on).
8. F9, Franchise: the roster's words (tags, morale, "he cares most about"), money in millions ("12.4 million"), team ratings, salary
   cap, injury report, trades, your job and staff.

## Sitting 4: two offseasons

Defaults: "offseason: every stage", staff off, "draft picks told: first and yours".

1. The first offseason at the defaults. Measured: about 14 minutes (the longest 15, with browsing about 25). Too long?
2. The next one in short mode with the staff on, and at the first pick "the staff makes your other picks": about 3 minutes. Short
   mode with the staff off: about 11 minutes; full mode with the staff on: about 8 and a half.
3. Three choices for you after hearing both:
   - Should a new franchise start in short mode?
   - Should the staff setting also make the draft picks?
   - Should short mode tell fewer of the other teams' picks?
4. Stage 1: the awards and the hall of fame (about eight lines) and the two new history lists.
5. Retirements and development lines; the draft (seven questions, the round announcements, the rating ranges); the cut; the cap list;
   late-round kickers and punters released at once.
6. Expiring contracts (about ten talks): three rounds, the mood words, the counter offers, "he asks 0.9 million for one year", the
   franchise tag's price.
7. Free agency: three rounds, the list of five, "one other team is interested", the headlines, "ten percent more" (it always wins:
   too easy?), the staff taking over.
8. Camp: the focus question, holdouts (about one offseason in six), the undrafted question, the offer sheet sentence, compensatory picks.
9. The staff stage: coordinators every offseason; the job verdict, a firing and the three offers.

## Sitting 5: many seasons (impressions)

1. Do the teams sound too alike in the middle seasons? (A setting exists to try: FR_RESIGN_TARGET 0.55, D-078.)
2. Is your own team stuck near the bottom for years?
3. The same quarterbacks or kickers on top for many seasons?
4. A quarterback as most valuable player nearly every season; the hall too full or too empty?
5. The computer's scores: results of 51 points and shutouts come a little more often than in the original.
6. The defaults of design 18: the franchise offered only with the N. F. L. rules and the classic season as the first answer; 34
   places and 16 weeks; seven draft rounds; your team starts from footplay.txt's names; the to-do list asked by default; every stage
   told; the game plan item only with playbooks.

If you want to hear a league that is already many seasons old without playing them, ask Claude to prepare one from the simulation.

6. Added by S8.1 (D-080): two small changes to listen for.
   a. Press F1 at the main menu (and F5 to F8 or F9 and back): the week line ("This is week 3 of Jim's N. F. L. football", or "This is the division play off week ...") is now said again before today's game; the original said it only in the play-offs and without "This is the". Is that welcome, or noise?
   b. In an overtime game, press F4 at the very start of the overtime period: it says 15 minutes (the original said no time).

7. Added by S8.3 (D-081): three things to listen for.
   a. With NVDA, and with JAWS if you use it (F9, Speech settings, the speech output), listen to the sentences whose written form the original tuned for its SAPI voices: the yard words ("7 yards", "30 yard line"), the names that are spelled to be said ("Zoo lynn ski", "reed", "rea play", "quarter back") and "N. F. L.". If one sounds wrong, say which and with which screen reader: a respelling for that engine is then a small change. SAPI voices were checked by Claude: no sentence of the game is silent on any of the 27 engines that could be tested.
   b. The old emulated voices SAM and Votrax used to end the program on some of the game's own sentences (a list title followed by a count, a name that is empty). They are fixed. If you like, choose one of them for a speaker (F9, Speech settings, Voices) and play a little, to see that the game goes on talking. The built program is tested for this again at S9.2.
   c. F9, Speech settings, Save a problem report: the sentence that tells you where the file is, and whether the file is on your Desktop. This is what a player will send you.

8. Added by S8.2 (D-082): five things to listen for in the next build you play.
   a. F5: the list now ends with "F9. added functions: the speech settings, the sounds, the names and the banter, the rules, and the about text."
   b. F1 at a prompt: the prompt again, then "For help, F5 lists the special keys, F6 explains the game, F7 gives the football words, and F9 opens the added functions." Once per F1, never after other keys.
   c. The exit says "Thank you for playing N. F. L. football by Josh Kennedy, inspired by Jim Kitchen." and the week line says "This is week 1 of Josh Kennedy's N. F. L. football".
   d. The intro sound: it plays while the game starts and stops when the welcome sentence ends; it must be silent while you choose the kind of season, the coach and the team.
   e. Still to come (not in this build): every real NFL play (SX.10) and the real coaches and players with no typing (SX.11).

9. Added by SX.10b2 (D-092): the plain descriptions and the key help, by ear.
   a. N. F. L. rules, any play menu: press D on an item. You hear a description of one or two sentences for a person who has never watched football, then the item again; the menu stays where it was. Try a play, a group (Inside Runs), Field Goal, Time Out and Save Game, on offense and on defense. Tell Claude any description that is unclear or wrong, with the play's name.
   b. Classic: D does nothing new (the key echo as before). F7 now ends with the original's plays described: first the offense plays, then the defense plays.
   c. F5 now lists every key, in Classic too (Alt and F10, Up and Down, the digits, Enter, Y and N, the coin toss, typing a name, the F9 menus, the saved game questions). With the N. F. L. rules it also lists S and D. F6 ends with a Keys part that says, for every key, where it works and what it does. Tell Claude if that is too long or in the wrong order.
   d. Still to come: the new play menus (Right, F, A, M, K, P, O, N) are not in the game yet (SX.10c), so their keys are not in these lists yet.

10. Added by SX.10c (D-093): the new offense menus, by ear (N. F. L. rules; F9, Rules: choose an offense playbook, for example the team's, since a new player starts with Classic).
   a. The offense menu starts as the original's: Line Plunge to Punt with their digits. Enter on Line Plunge says "the call is ..." and the play runs. Is that as quick as the original?
   b. Right on Line Plunge: "Inside Runs, list 1 of 2." and the first play; Right again: the next list; Left or Backspace: back to the first menu. M: More Plays (play action, options, trick plays, clock plays); in it N, type a few letters (T works here), Enter.
   c. Plus on a play: "added to your favourites."; the first menu then has Favourites (F). Minus takes it off. After a play, Again (A) calls it once more.
   d. O: Formation and Tempo. Enter changes a value (shotgun, no huddle). Late in a half with the clock running: P spikes the ball; leading late in the fourth quarter: K kneels.
   e. Listen to the plays: the sentences and sounds should be the original's; new are a throw-away, a pitch, a keep, a fumble your team falls on, an interception run back ("runs it back 23 yards") and the defense's touchdown.
   f. Still to come: the defense menus and the 2026 kicks (SX.10d), the computer calling every play (SX.10e).

11. Added by SX.10d (D-094): the defense menus and the 2026 kicks, by ear (N. F. L. rules; F9, Rules: choose a defense playbook too).
   a. The defense menu starts with the original's six calls. Enter on one says "the call is ..."; Right on Blitz: "Blitzes, list 1 of 2."; Left goes back. O: Defensive Personnel and Coverage Shade. D describes an item.
   b. On fourth down the defense menu has Kick Defense (P): Punt Return, Fair Catch, Punt Block, Punt Safe, Field Goal Block, Field Goal Safe. Choosing one says "your kick defense is ..." and it is kept until you change it.
   c. Your kick off is now a short menu: the deep kick (Enter), a short kick, a squib kick, the onside kick, and after a safety a punt from the 20. Is it quick enough at every kick off?
   d. Kicks to listen for: a touch back at the 35; a kick out of bounds or short at the 40; a catch at the 8 and a return; punts that are returned, fair-caught, muffed or blocked; a field goal that misses (the other team gets the ball at the spot of the kick, or its 20); an extra point that misses; a fake punt or field goal (Right on Punt or Field Goal).
   e. Late in the second or fourth quarter, after your fair catch, you may be asked "do you wish to try a fair catch kick". Yes is a free kick with no rush.
   f. Still to come: the computer calling every play and kick choice from the catalog, and the team's playbook as the default (SX.10e).

12. Added by SX.10e (D-095): the computer's calling and the team's playbook as the default, by ear (N. F. L. rules; nothing to set: a new
    player, and a settings file that never chose a playbook, now plays the team's playbook on offense and defense; F9, Rules, the playbook
    items, choose Classic for the original's plays and kicks).
   a. The first game: the new menus come without any setting. Do they still feel like the original's (Enter on Line Plunge, the call, the
      play)? Is "the call is ..." before the snap welcome, or too much?
   b. Enter on a family now picks a play that fits the down and distance: on third and long a pass of that family that gains more, near
      the goal line the goal line plays, on third and one the power runs and the sneak. Does the pick sound sensible?
   c. Listen to the computer's plays when you defend: every kind of run and pass, screens, play action, an option now and then, a trick
      play rarely. Near the end of a half it may spike the ball, throw a Hail Mary, or take a knee when it leads. Does it sound like a
      real team? Too many kneels? (The simulation counts about 3 a game; the league about 1.5.)
   d. After its touchdown the computer sometimes says "the Jets will try for two points" (late in the game by a chart, now and then
      earlier) and runs a play from the 2 while you defend with your usual menu. Is that clear?
   e. The computer may fake a punt or a field goal on a short fourth down, rarely.
13. Added by SX.12 (D-096): the 2026 overtime, by ear (N. F. L. rules; a tied game after four quarters).
   a. After " We are going into over time number 1" two sentences explain the overtime. Then a new coin toss: the visitors call it (you,
      when you are the visitors), and the winner chooses to receive or kick. Are the sentences clear, and is the toss welcome?
   b. Each team gets the ball once. If the first team scores, the game goes on and the other team gets its chance; "both teams have had
      the ball. the next score wins." comes when it turns into sudden death. Is it clear who needs what?
   c. A regular-season game that stays tied for the whole 10 minutes ends with " The game ends in a tie. " and the final score " tied at
      20 all"; the week's results say "Bengals and the Jets tied at 20." and the standings say "9, and 6, and 1 tie." Do these sound right?
   d. In the play-offs a tied overtime period goes on into the next with the same ball, down and distance. (Rare: a whole 15-minute
      overtime period without a score.)
   e. When the computer is the second team and is behind, it no longer punts on fourth down (a punt would lose the game); it kicks a field
      goal only when the kick ties. Does that sound sensible?
14. Added by SX.13 (D-097): the rules the 2026 audit corrected, by ear (N. F. L. rules with a playbook, the default). Most are rare;
    listen for them when they come up.
   a. A touchdown on the last play of the fourth quarter that wins the game (or cannot save it) is followed by the end of the game with
      no try. When the try could still tie or win, it is played.
   b. After a safety the kick is made from your 20. If it comes down short of the receivers' 20, or goes out of bounds, you hear "the
      ball is placed at the 50". The computer always kicks deep after a safety. Is the sentence clear?
   c. Press T while a play is running late in a half: the time out is now called the moment the play ends, with no seconds lost.
   d. Late in a half, when the replay official reverses a play and the clock would have kept running, you hear "ten seconds run off the
      clock." (press T during the play to stop it).
   e. A punt blocked behind its own goal line is now a safety or a touchdown for the other team.
   f. The play once called Fake Kneel is now "Victory Formation Pass": the team lines up as if to run out the clock and throws deep at
      once. Does the new name and description sound right?
   g. In a play-off game's third overtime period the team that lost the overtime coin toss chooses to receive or kick; when that is
      you, you are asked as at the toss.
15. Added by SX.11 (D-098): the real coaches and players, by ear (N. F. L. rules; nothing to set). The names are the teams' own, fetched
    on 2026-10-22; nobody has heard them said yet.
   a. Start a new season. After you choose the team you hear "The head coach of the Steelers is Mike McCarthy", then three items: keep him
      (Enter), choose another real coach from the list of 32, or type a name. Is the order (team first, then the coach) all right? Every
      prompt after that says the coach's whole name ("Mike McCarthy which do you call"): is the whole name too long, would a last name be better?
   b. At the first game your players, and your opponent's, are real players, and the play-by-play says their whole names ("Joe Burrow
      throws to Ja'Marr Chase"). Is the whole name too slow in play? (Q-041: the choice is a last name only, here or in a setting.)
   c. The quarterbacks: Enter, Enter takes the real quarterback of each team. Do the names sound right?
   d. Listen for names the voice says wrong (an unusual spelling, an initial like D.J. or A.J., a suffix such as Junior or the second).
      Tell Claude which; a line in respellings.txt fixes it, and the fix goes into the shipped file.
   e. A new franchise: the other teams' head coaches and the players of all 32 teams are real. Ratings are the game's own and are not the
      real players' (they are not copied from any game).
   f. The Classic rules still ask you to type the coach and draw the original's random surnames.
16. Added by S8.2 (D-100): the exit. After "Thank you for playing N. F. L. football by Josh Kennedy, inspired by Jim Kitchen." the program ends: no beeps and no "could not find the Kitchensinc game menu program" sentence. (The owner's first S8.2 round of items 1 to 15 found nothing to change: the welcome, the start-up question, the coach, the help keys, the playbook menus, D, T, the kicks and the whole names are all right; how a name is said depends on the voice or the screen reader and is left alone.)
17. Added by SY.1 (D-101): the radio broadcast, by ear (N. F. L. rules; nothing to set; F9, Rules, Broadcast is item 10 and is on).
   a. The announcer's banter is now radio banter (the crowd, the weather, the band, listeners at home, teasing Ghip) instead of Jim Kitchen's jokes; it comes where the jokes came. The Classic rules still have the jokes. Are the lines the right kind, and not too long?
   b. Ghip, the color commentator, speaks after some plays and at the big moments, in a voice of his own. The first time, the announcer says "Ghip, the color commentator, is in the booth with me. F12 chooses his voice..." and the game gives him the next voice of the announcer's engine. Is his voice different enough from the announcer's? F12 asks for him after the five speakers, F11 for his volume.
   c. How often does Ghip speak (about one line in six plays, always at half time, the end and a touchdown most of the time)? Too often, too seldom? Is it a nuisance that his line comes before the next menu (the first key cuts it)? With NVDA or JAWS he speaks in the screen reader's voice.
   d. The announcer sometimes turns to Ghip first ("Ghip, what did you make of that one?", about two times in five). Is it welcome?
   e. F8 switches Ghip and the banter off with the other comments. F9, Rules, Broadcast switches only Ghip (and the questions to him) off.
18. Added by SY.2 (D-102): the stadium sounds, by ear (N. F. L. rules; F9, Rules, Stadium sounds is item 11 and is on). NOBODY HAS HEARD THESE: they are generated sounds. Listen in a whole game: a touchdown (the crowd cheers, and groans when the other team scores), a turnover and a sack (a groan, or a roar when it is the other team's; a sack also hits), a gain of 20 yards or more (a roar), a completed pass (the pop of the catch now and then), a first down (the chain), a missed field goal (a groan, now and then the goal post), a field goal (applause), a penalty (boos when the flag is on your team, the flag when it is on theirs), the end of the first and third quarter and half time (applause). Are they realistic enough? Too loud (they are 15 to 26 decibels under the sound volume) or too often? Do they cover the speech? Tell Claude which sound is wrong; any can be replaced by a real recording of your own (CUSTOMIZE.md) or one we find with a clear license.
19. Added by SY.3 (D-103): the referee's microphone and the whistles, by ear (N. F. L. rules, Broadcast on). The referee now says the flag announcements, the accepted and declined penalties, the time outs and the reviews, in a voice of his own with a public-address sound, after a click; F12 and F11 ask for his voice and volume after Ghip's. The whistles are pea whistles: short at a time out, long at a penalty and the end of a quarter, double at the two-minute warning and a review, else short or double, and the original's whistle now and then. Is the referee's voice clear and different from the announcer's and Ghip's? Is the PA sound pleasant, and does it hurt the understanding of a penalty? With a slow voice, NVDA or JAWS he speaks without the effect.
20. Added by SY.4 (D-104): choosing the receiver (N. F. L. rules with a playbook, the default). In the offense menu press R: the list opens with "The play picks the receiver" (Enter on it keeps the random pick), then your six receivers by name and position, then your first two running backs when the play can throw to one. Up, Down, Home, End, a digit and Enter work; Escape leaves it as it was; T calls a time out. After you choose, call a pass play: the sentences should name the chosen player ("and <name> catches the ball"). A running back target gets short routes. R works for the next play only. Is the list quick and clear? Is it a nuisance that R is a key and not an item of the menu?
21. Added by SY.5 (D-105): choosing the blitzer (same conditions). In the defense menu press L: the list of your seventeen defenders by name and position, the first item a player picked by chance. Choose one, then call a blitz (Enter on Blitz or a blitz from its lists). If the other team's quarterback is sacked the sack names your player; a linebacker or a defensive back makes a sack a little likelier. Without a blitz call the choice is ignored. Is this what you meant by "a player to blitz with"? Should the blitzer also change more (pressure, coverage)?
   (The owner's first round on 0.10.0: 16 the exit, 20 R and 21 L work; 18 the stadium sounds and 19 the referee and whistles are good; 17 asked for a name for the commentator. R and L are in F5 and F6 and the README keys, D-108.)
22. Added by SZ.1 (D-106): the commentator's name. F9, Rules: the twelfth item is Commentator: Ghip. Enter opens a list: Ghip the default, 28 sports podcasters and broadcasters in alphabetical order (type letters to jump, for example "pat"), your own earlier name, and last "Type a name of your own". Left and Right on the item step through the names. Choose one, start a game: the announcer says the new name in the questions ("<name>, what did you make of that one?") and in the banter and the intro ("<name>, the color commentator, is in the booth with me"). Does it sound right? Is the list quick to use? Are real names a problem next to the teasing lines (Q-049)?
23. Added by SZ.2 (D-107): your own sound files. F9, Sounds, the last two items. "Stadium and referee sounds" lists the 19 sounds with the file name each takes (for example crowd_cheer, whistle_long, mic_on), says whether it is the original, yours or several, and plays it on Enter (again for the next one of its family); F1 says how. Put your own wav in the sounds folder (F9, Sounds, Open the sounds folder) with one of those names, then open the list again: it says "your sound" and plays it. A name with a number added (crowd_cheer2) adds a second sound that is drawn. "Put the stadium sounds back" moves your files aside after one Enter. Check files counts a damaged file. Is it clear without help?
24. Added by SZ.4 (D-109): the screen reader. With NVDA or JAWS running, start the game: after the welcome the game says "You are running NVDA. Do you want the game to speak through it?" (yes first; Enter or Y for yes, N for no). Yes: no voice is asked for at any time, the game speaks through NVDA. No: the game uses its own Windows voices (the first start then asks the five voices). It asks only once; F9, Speech settings, Speech output changes it. F12 under a screen reader says why there is nothing to choose.
25. Added by SZ.5 (D-110): where the other plays are. Start a game with the N. F. L. rules and the default playbooks. After the first item of the offense menu, the defense menu and Formation and Tempo the game says one sentence (only in your first three runs; opening a list with Right or More Plays ends it): Right opens the lists of the play you are on, M opens More Plays, D describes a play, Enter on a play type lets the playbook pick. On defense More Plays (7) now lists every list of defensive calls (blitzes, zone coverages and the rest). Can you find the other defensive calls now?
26. Added by SZ.5 (D-110): "recommended". Open Formation and Tempo (the letter O): the settings start as "the playbook's choice". The game now says once that this means the play you call sets the setting and that nothing is recommended. Is that clear? Do you want a key that says which play the playbook would most likely call (Q-050)?
27. Added by SZ.6 (D-111): a sentence said twice. Play kicks, field goals and onside kicks, with and without penalties and time outs: nothing is said twice in a row.
   (The owner's third round on 0.11.0: 22 the commentator's name sounds right and the list is easy to use; 23 the sounds list is clear; 24 the screen reader question works; 25 the other defensive calls are found, and the keys had to be in F5 and in the help, D-113; 26 yes, a key that says which play the playbook would most likely call, documented in the game, D-112; 27 nothing is said twice.)
28. Added by SZ.7 (D-112): the W key. Start a game with the N. F. L. rules and the default playbooks. In the offense menu, on any play type (Line Plunge, End Run, Screen Pass, Short Pass, Long Pass) press W: the game says which play the playbook would most likely pick and about how often, or, when several plays share the most, which ones ("about equally often, each about 9 percent of the time"). Press Right to open a list of plays and W again: the same for that list. On defense press W on Goal Line, Blitz and the others, and in More Plays on a list. W on Field Goal, Punt, the quarterback runs, Save Game says what they are. It never changes the game: the plays that follow are the same with or without W. Is the answer what you wanted? Is W a good letter (Q-053)? Should it say the top three (Q-052)?
29. Added by SZ.7 (D-113): the keys in F5 and F6. Press F5: after the original's list and the added functions, the added keys follow; the playbook line now says Enter on a play type, Right, M and Back together, and there are lines for Right, M, W, D, R, L, F, A, K, P, O and N. F6 says each key with where it works and what it does. Can you find Right, M, D and W, and is Enter on a play type clear?
30. Added by SZ.7 (D-112): the hint now also names W. Start a new program run with the hints on (nfl4 settings: nx_menu_hints below 3), or ask a friend to play: after the first item of the offense menu the game says "Right opens more plays: the lists of the play you are on. M opens More Plays, D describes a play, and W says which play the playbook most likely picks. Enter on a play type lets the playbook pick."
40. Added by SZ.8 (D-120): the Commanders. Start the game. Open a new franchise or season and choose the team in the N. F. L. East that was the Redskins: the game says Commanders. If you have played before, your teams.txt (customize folder) is changed once; the old file is kept as teams.txt.before-commanders. Is Commanders what you wanted? F9, Customize, Reload: do other changes of yours stay?
41. Added by SZ.8 (D-121): the real 2026 schedule. Start a NEW franchise (an old one keeps its 16 random weeks until its next season). Choose the Commanders (or any team), then at the main menu choose 2, see schedule: the game now says "<team> schedual" and then "week 1", the game, "week 2" and so on to week 18, with one "bye week". It does not ask whether you like the schedule. Is week 1 the real one (the Commanders at the Eagles on September 13)? Is the bye week 7?
42. Added by SZ.8 (D-121): the bye week. Play to week 7 with the Commanders. The week line, then "Your team has a bye this week. There is no game today." The menu's first choice says "see this week's games". Enter: "Games of week number 7. Your team has a bye this week." and then the other teams' games. Then the standings. Does it feel right that no game is asked and nothing is said about a play plan, a goal or hurt players that week?
43. Added by SZ.8 (D-121): the end of the season. After week 18 the division winners and the wild cards are told as before, then the wild card week is week 19 (the menu says "Wild card play off week"), then the division week, the conference week and the Super Bowl. Does anything still say week 16 or 17? Do the standings after week 18 say 17 games for each team?
44. Added by SZ.8 (D-123): sign a free agent. In a franchise, any week: F9, Franchise, free agents (the seventh item). "Sign a free agent": the position, then the free agents of it (best first, with age, rating and what each asks), then the player of your team you would release (with his dead money), then one question. Enter signs, Escape says no. Try it with a quarterback. Is it easy to follow? Are the free agents good enough to be worth a choice, or too weak or too strong (rated 58 to 69)? Does "hear the free agents" list them all?
45. Added by SZ.8 (D-124): the trade deadline. Hear the news at week 1 ("in F9, under Franchise, you can sign free agents any week and make trades until the trade deadline, the kick-off of week 10"), then in weeks 9, 10 and 11 the sentences "the trade deadline is next week", "this is the last week for trades" and "the trade deadline has passed". Try a trade in week 10, then in week 11 (closed). In the offseason, at free agency (stage 8, before the draft), F9, Franchise, trades is open again. Is the deadline clear? Should trades also be open after the draft (Q-063)?
46. Added 2026-10-23 (D-134): JAWS and the keys. Start the game with JAWS running (and NVDA closed), at your usual JAWS rate and once at a fast rate. Arrow up and down in a menu quickly, press F1, F5 and letters: does each new item start at once, as with NVDA? Does any sentence get cut that you wanted to hear?
47. Added 2026-10-23 (D-135, the tester's bugs): a penalty. When a flag is thrown, the crowd boos (a flag on your team) or cheers (on the other team) as the flag is thrown. After you accept or decline, the referee says the result: "the penalty is accepted. 10 yards, it will be third and 5 on your 30 yard line." Is it clear and not too long?
48. Added 2026-10-23 (D-135): the whistle. Every whistle of the N. F. L. rules is the new official's whistle (short, long, double). Does it sound like an NFL whistle? To try your own: put a whistle.wav in the sounds folder (F9, Sounds, Open the sounds folder).
49. Added 2026-10-23 (D-135): the crowd. A gain of 20 yards or more by your team: the crowd roars. Are the crowd's reactions loud enough now, and not too loud over the speech?
50. Added 2026-10-23 (D-135): the running backs. In a quick game, listen to who carries the ball: always a running back (a real one, or a made-up name when the team has few)? The first back carries most.
51. Added 2026-10-23 (D-135): the blitz. On defense, press Enter on Blitz several times against passing downs: do blitzes get home more often (sacks)?
52. Added 2026-10-23 (D-135): the start of a game. Start a new game, and load a saved game: no intro jingle and no loud crowd surge before the coin toss or the first play. The program still plays its intro once at launch, with the welcome. Is that what you wanted, or should the launch intro go too?
53. Added 2026-10-23 (D-136): practice squads. Start a new franchise: F9, Franchise, practice squad (the tenth item) says "practice squad, 16 of 16 players". Hear the squad (each player's elevations left), sign one to your roster, add a free agent, release one. Play until an injury leaves a position with nobody fit (a quarterback injury is the clearest): the week's injury report says a squad player is elevated. Is it easy to manage? Should other teams be able to sign players from your squad (Q-067)?
54. Added 2026-10-23 (D-141): the latest calendar. F9, Franchise, the last item, "get the latest calendar": you hear that the game is asking GitHub, then (until the calendars folder is pushed to GitHub, and while 2026 is the newest) "you have the newest calendar already, the one of 2026". With the network off: "the game could not reach GitHub". Press Escape while it asks: it stops at once. Is the waiting sentence clear, and is the wait short?
55. Added 2026-10-23 (D-138): the 14-team play-offs. Play a franchise season on the real calendar to its end. After week 18: the division winners, three wild cards in each conference, then "the top seeds, the ... and the ..., have the only byes of the wild card round". The wild card week has six games; in the division round the top seed plays the lowest seed left. Is the end of the season told well enough?
56. Added 2026-10-23 (D-139): trades in the offseason. At the end of the free agency stage, of the draft stage and of the roster cut stage, F9, Franchise, trades: offer a player or ask for one. During the roster cut's own question the trades say they are closed. After the draft, "your draft picks" says picks can be traded again when the season begins.
57. Added 2026-10-23 (D-140): the quarterbacks. With the N. F. L. rules and no franchise: F9, Rules, Quarterbacks (the item before Reset). Each team is said with its starter and the men behind him; Enter on the Bengals, Down, Enter on Joe Flacco: "Joe Flacco starts for the Bengals from the next game". Play a quick game with the Bengals: Flacco is your quarterback. In a franchise: the list starts on your team; Enter, then a practice squad quarterback: the game asks to release your starter (with his dead money) and sign him. Would you rather keep the old starter as a backup (Q-069)?
58. Added 2026-10-24 (D-146, NX-B5): trades, the team first. In a franchise season before the deadline: F9, Franchise, trades, "ask a team for a player" (the third item). Type "be" in the list of teams: you should land on the Bears or the Bengals. Enter, choose quarterbacks, their quarterback, then yours. Listen: is the order team, position, player, your player clear? The fourth item, "the league's best at a position", is the old list.
59. Added 2026-10-24 (D-146, NX-B4): picks in your proposals. After whom you give, the picks menu: "send the proposal" (with the picks so far), "add one of your picks", "ask for one of their picks", "take a pick out". Ask for their round 1 pick and offer nothing: the other team should say it wants more and name your picks. Are the pick names clear ("your round 2 pick", "their round 1 pick", "the round 3 pick of the Bears")?
60. Added 2026-10-24 (D-143, NX-B1): who starts for an injured player. When one of your players is hurt and out for the next game, the week's to-do list asks "who starts in his place?" with the staff's choice first. Choose the second answer; listen for his name in that place during the game. F9, Franchise, injury report: the "who starts for" line under him. Is the question at the right moment, and the note that the strength does not change acceptable?
61. Added 2026-10-24 (D-144, NX-B2 in part): the real rosters of 2026-10-24. F9, Rules, Quarterbacks: no practice squad quarterbacks in a team's list. A new franchise: F9, Franchise, practice squad, hear the squad: real names (the Bengals' Sean Clifford). Listen for names said wrongly. Your old rosters.txt should have become rosters.txt.before-2026-10-24 if you never changed it.
62. Added 2026-10-24 (D-145, NX-B3): the real free agents. A new franchise: F9, Franchise, free agents, sign a free agent, receivers: real names (Tyreek Hill). Ratings are the game's own. Is anyone on the list known to have signed since?
63. Added 2026-10-24 (D-147, NX-D1): real positions. A quick game of the N. F. L. rules, the Bears against the Bills: is every name you hear at his own position (no quarterback catching passes, no safety called a cornerback)?
64. Added 2026-10-24 (D-147, NX-D2): playing time. A whole game: the first running back and the first two receivers are heard much more often than the backups, and the backups now and then. Too much, too little, right?
65. Added 2026-10-24 (D-147, NX-D3): depth charts. F9, Rules, Depth charts, a team, running backs, Down, Enter: "is now the first of the running backs". The next game with that team: he carries most of the runs. "Back to the real order" undoes it. In a franchise the same item lists your team with ratings and ages.
66. Added 2026-10-24 (D-147, NX-D4): key downs and moments. In a team's depth chart menu, "key downs and moments", third and fourth down, the receiver, choose one: on third downs he gets most of the passes.
67. Added 2026-10-24 (D-148, NX-M1, NX-M2): no music, no celebrations. With the N. F. L. rules: no music at the start, the exit or half time, and no celebration sounds after a touchdown. Classic still has both.
68. Added 2026-10-24 (D-148): your own music and celebrations. Put a sound file in the sounds folder as music.wav, start the game: it plays under the start and stops when the welcome ends. A file named celebration1.wav: heard several times after a touchdown.
69. Added 2026-10-25 (D-149, NX-B2b): the 53-man franchise. A new franchise: F9, Franchise, your roster: the title says 53 players, 34 in the game's places and 19 on the bench. Open the quarterbacks, receivers, offensive linemen and long snappers: are the bench players your team's real backups? Is a list of 53 easy to move through?
70. Added 2026-10-25 (D-149): a hurt man's place. Play weeks until a player of yours is out: "who starts for" lists the bench men of his position, the staff's choice first. A hurt quarterback is played by the backup quarterback (his name in the game).
71. Added 2026-10-25 (D-149): the cut keeps 53. The offseason's roster cut, "choose yourself": "your roster has n players and room for 53. choose who is released." until it fits. Afterwards F9, Franchise, your roster: 53. Did the staff keep the men you would have kept?
72. Added 2026-10-25 (D-149, Q-069): bench a starter without a release. F9, Rules, Quarterbacks, your team, Down, Enter on the backup: "X starts now, and Y goes to the bench." F9, Rules, Depth charts, a position, Enter on a bench player: he is first, the last starter goes to the bench.
73. Added 2026-10-25 (D-157, SR.2; version 0.16.2, after its build): the real rosters of 2026-10-25. With the N. F. L. rules, a quick game as the Bears: Caleb Williams at quarterback; Colston Loveland and Sam Roush named as tight ends. Then your own team: anyone missing, on the wrong team, or gone?
74. Added 2026-10-25 (D-158): the old copies replaced once. Install over 0.16.1 and start once with the N. F. L. rules: the customize folder has rosters.txt.before-format-2 and free_agents.txt.before-format-2, and rosters.txt starts "# NFL Football 4 rosters, format 1, layout 2".
75. Added 2026-10-25 (D-161, SR.4; version 0.16.2, after its build): a new franchise of the real rosters. New franchise as the Bears with the N. F. L. rules: F9, Franchise, your roster has Caleb Williams, Tyson Bagent and Case Keenum, the tight ends as tight ends, Miller Moss on the squad, nobody made up. A quick game as the Bears: only Swift, Monangai and Roschon Johnson carry the ball; Kalif Raymond returns kicks.
77. Added 2026-10-25 (D-163, Q-043): the colour commentator speaks about half as often (about 15 lines a game instead of 26). A whole game with the N. F. L. rules: is it right now, too quiet, or still too much?
76. Added 2026-10-25 (D-161): an older franchise opened. Open a franchise saved by 0.15.0 or older: it opens, the backup quarterbacks are there, the folder has league.sav.before-format-18.
78. Added 2026-10-25 (D-164, SR.5; version 0.16.2, after its build): a whole franchise season on the real roster. Let the staff play a season and an offseason: at the roster cut, F9, Franchise, your roster has at most 53, two or three quarterbacks, linemen and a long snapper; the draft names linemen, edges and snappers. Does anything sound wrong (a player at a strange position, a team with no kicker)?
79. Added 2026-10-25 (D-164, NX-L12): real NFL last names for made-up players. In the first offseason's draft, the prospects' names: real NFL last names with a first name, never a real player's full name. Do they sound right?
80. Added 2026-10-26 (D-165, SR.6; version 0.16.2, after its build): the roster by positions. New franchise as the Bears, F9, Franchise, your roster: "quarterbacks, 3", then Caleb Williams "quarterback, starter, number 18". Down through the three, then the halfbacks heading. Left and Right go from position to position; L goes to left tackles, then left guards, then left edge; E goes to the tight ends; T does nothing. Is every player at the position you know? Is the heading and the count clear?
81. Added 2026-10-26 (D-165): the starting lineup in a quick game. F9, Rules, Depth charts, the Bears, "starting lineup": 27 lines. Enter on left tackle, go down to the right tackle, Enter: he moves from right tackle to left tackle and starts there. D on any line says what the position does: are the descriptions clear to someone who knows nothing of football? Play a quick game: is he the left tackle in the set-up?
82. Added 2026-10-26 (D-165): choose the returners and a practice squad man. Lineup, kick returner: choose a wide receiver; lineup, a position, the end of the list: a practice squad man (marked); choose two, then a third: the third is refused. Play a quick game as that team: do the chosen men play?
83. Added 2026-10-26 (D-165, Q-082): returners in a franchise game. Franchise, F9, Rules, Depth charts, punt returner: your best receiver. Play a game: does he return punts while he also starts at receiver?
84. Added 2026-10-26 (D-165): a starter who left. In a franchise choose the second quarterback as the starter, then trade him away (F9, Franchise, trades): open F9, Rules, Depth charts: you hear once that he is no longer on the team and who starts.
85. Added 2026-10-26 (D-165): names two men share. Trades, ask a team for a player, Vikings or Browns: Justin Jefferson is said with his position and team. Trades, giving a player: the last line is "a player of another position".
86. Added 2026-10-26 (D-166, SR.6): get the latest rosters. F9, Customize, the last item: with no internet it says the rosters could not be downloaded and that yours stay; with internet and nothing published it says you already have the newest. Escape while it waits.
87. Added 2026-10-26 (D-166): an old franchise opened. Open a franchise saved by 0.15.0 or older: once you hear that it now has the real rosters' positions and how many real players joined.
88. Added 2026-10-26 (D-167, SR.7; version 0.16.3): real ages. New franchise as the Bears: F9, Franchise, your roster: Caleb Williams age 24, Tyson Bagent 26, Colston Loveland 22, Miller Moss (practice squad) 24. Do the ages of the players you know sound right? After the first offseason, do the oldest players (Aaron Rodgers, Joe Flacco) retire?
89. Added 2026-10-26 (D-167): positions in the draft and the awards. At the draft, are the prospects said with their own positions (left tackle, strong safety, halfback)? After the draft, your rookies at the end of your roster list? After a season, the awards ("your halfback" rather than "your running back")?
90. Added 2026-10-26 (D-167): install 0.16.3 over 0.16.2 with an unchanged rosters.txt in the customize folder: the new file has "; age" on its lines and the old one is kept as rosters.txt.before-layout-2.
91. Added 2026-10-26 (D-168, a player's e-mail: "at some positions it has no one starting"; version 0.16.4, after its build): F9, Rules, Depth charts, the Ravens: strong-side linebacker and fullback name a man "filling in from" his own position; go through every position of three teams, in a quick game and in a franchise, and of the starting lineup: does any position say nobody? Is "filling in from" clear?
92. Added 2026-10-26 (D-169, the owner: "it doesn't have all free agents example is kicker"; version 0.16.5): new franchise, F9, Franchise, free agents, the kickers: real kickers (Younghoe Koo, Cade York, Greg Joseph, Matt Prater, Graham Gano), no made-up names; the punters (Johnny Hekker, Thomas Morstead), the long snappers, the offensive line. Is anyone listed who has signed with a team?
93. Added 2026-10-26 (D-170, the owner: "the Giants started J.J Macarthy"): McCarthy was traded to the Giants on 2026-09-28 and is Winston's backup. New franchise as the Giants: does Jameis Winston start at quarterback (F9, Rules, Depth charts; the starting lineup)? Where did you hear McCarthy start (a quick game, or which week of a franchise, and was Winston hurt)? ANSWER 2026-10-26: "He started right away as the default starter" (build and mode not said). Checked in 0.16.5: every rosters.txt since SX.11 lists Winston first; F9 Rules Quarterbacks, the quick game's Getqbs default, the depth chart and the view, and new franchises (5 seeds) all start Winston; no log of the owner's play is on this PC (he plays on another one; this PC's customize rosters.txt is the 2026-10-22 copy, which 0.16.x replaces at its first start). Open: does 0.16.5 still start McCarthy for him, and in which mode (quick game, season, franchise)? SETTLED the same day by his problem report (20261026-174444): a franchise as the Giants in 0.16.5, every game started Winston (D-171); the McCarthy start was an older build's.
94. Added 2026-10-26 (D-170): play a franchise into its second season and listen to a few teams' quarterbacks (Bills, Bears, Cowboys, Patriots): do the real starters still start, unless a clearly better man came in?
