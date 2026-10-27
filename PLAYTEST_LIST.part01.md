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

