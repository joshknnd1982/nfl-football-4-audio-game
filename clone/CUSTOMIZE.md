# Changing the names and the banter in NFL Football 4

This is inspired by Jim Kitchen. The game is a new version of his N. F. L. football version 4. You can change the team names, the division names, the players' surnames and the announcer's banter, and you can add your own banter lines and your own sounds. With the files left alone the game says and plays exactly what the original does.

## Where the files are

Press F9, choose Customize, then "Open the folder with the names and banter files". The folder is also here:

    %APPDATA%\Kitchensinc Revival\NFL Football 4\customize

It holds these plain text files. Any text editor will do, and a screen reader reads them line by line:

- teams.txt, the 32 team names.
- divisions.txt, the 8 division names.
- surnames.txt, the 1,708 surnames the players' names are drawn from.
- banter.txt, the announcer's remarks.
- footplay.txt, the names of your own team's players. The game writes it at the first game of a season (see below).
- the folder sounds, for your own sound files used in the banter.
- remarks.txt, the remarks of the N. F. L. rules, only when that rule set is chosen in F9 (see below).
- penalties.txt, the fouls of the N. F. L. rules: their names, and which are called and how often (see below).
- the folder playbooks, with plays.txt, styles.txt, team_styles.txt and favourites.txt: the plays of the N. F. L. rules' playbooks and your favourite plays (see below).
- coaches.txt, rosters.txt and respellings.txt, the real head coaches and players of the 32 teams and how the voice says their names, only when the N. F. L. rules are chosen in F9 (see below).
- news.txt, the news lines of a franchise, only when the N. F. L. rules are chosen in F9 (see below).
- injuries.txt, the words the game says about injuries in a franchise, only when the N. F. L. rules are chosen in F9 (see below).

After you save a file, choose Reload in the Customize menu, or start the game again. A game in progress keeps the players it already has.

## How a file looks

The first line says what the file is and its format, for example `# NFL Football 4 teams, format 1.` Leave it as it is. Lines that begin with `#` are notes. Every other line is an ID, an equals sign and the text:

    T09 = Mustangs

The ID stays as it is. The text is what the voice speaks, so spell it the way it should sound. A name has 1 to 30 characters, with no comma and no semicolon.

## Rename a team

Open teams.txt and change the name after the ID. The teams are T01 to T32. To rename the Broncos, change `T09 = Broncos` to `T09 = Mustangs`. T24 is the Commanders; the original game called that team the Redskins, and `T24 = Redskins` brings that name back. A teams.txt written by an earlier version still said Redskins: the first time it is read the game changes that line to Commanders, adds a note, and keeps your file as teams.txt.before-commanders (once; after that your own T24 stays). Two teams cannot have the same name. If you give a team the name another team has, the later one goes back to its original name. A season in progress and a saved game are not affected: they keep numbers, not names.

## Rename a division

Open divisions.txt and change, for example, `D1 = A. F. C. North.` to `D1 = The Northern Group.` The conference names A. F. C. and N. F. C. also appear inside a few fixed sentences of the play offs, and those do not change.

## Your own players' names

footplay.txt holds the 33 names of your own team's players and your quarterback, in sections: Running Backs, Receivers, Defensive Players, Special Teams Players, Kickers and Quarterback. The game draws new random names at the first game of every season, and when a season ends it keeps your old names as footplay.previous.txt. Copy it back over footplay.txt to keep them. If you edit footplay.txt, keep the section headings and the number of names in each section. A section that is wrong gets new random names and the rest stays.

## Other surnames

surnames.txt has 1,708 lines, S0001 to S1708. You can change the names. There are always 1,708 of them.

## The real coaches and players of the N. F. L. rules

With the N. F. L. rules you type no name. When you choose your team, the game offers the real head coach of that team (press Enter to keep him, or choose another real coach from a list of the 32, or type a name if you want one). Your team's players, the other team's players and the two quarterbacks are the real players of the two teams, so Enter takes the real quarterbacks. A franchise starts with the real players and the real head coaches of all 32 teams. The original game's random surnames are used only with the Classic rules, and for the players the game makes up later (the draft classes of a franchise, stand-ins).

Three files hold the names. They are made for you the first time, in the same folder as the others, and they are kept right if you damage them (a copy of a damaged file is saved beside it).

- coaches.txt: one line for each team, `T04 = Mike McCarthy`, and a line `VERSION = season 2026, as of 2026-10-22` that says which season the names are from.
- rosters.txt: the players of each team, one line each: an ID, an equals sign, the position, the jersey number and the name, for example `T01P01 = QB 9 Joe Burrow`. The positions are QB, RB, FB, WR, TE, DL, LB, CB, S, K and P, and RET for a kick or punt returner (he is also written on his own line). A team's players come in depth order, the starters of each position first. The game does not use offensive linemen or long snappers, so they are not in the file. The numbers are kept for you and are never spoken.
- respellings.txt: how the voice says a name or a part of one, for example `R001 = Jr. => Junior`. Add a line with a new ID to fix a name the voice says wrong, for example `R100 = Mac Jones => Mack Jones`. `R001 = off` switches a line off. A written text is changed only where it is a whole word of a name.

The names in these files are facts, used descriptively. They are not endorsed by the teams or the league, and no ratings, photographs or logos are used.

To put in a new season's names: replace the lines of the teams that changed in rosters.txt and coaches.txt, change the VERSION line, save, and choose Reload in the Customize menu. If you write any line for a team in rosters.txt, your lines replace all the built-in lines of that team, so an old player does not come back. A coach is replaced by writing his line again. Delete a whole file to get the built-in names back. Your own team's players are the names in footplay.txt: the game writes it from the real roster at the first game of a season, and your changes to it are kept.

## The banter

banter.txt has the 142 original lines, B001 to B142. Each time the announcer speaks, the game chooses one line that is on, by chance, and no line comes twice in a game. The F8 key switches all banter off, your lines too. banter.txt is the banter of the Classic rules: with the N. F. L. rules the announcer says radio banter instead (see "The radio broadcast" below), and the 142 jokes of the original are not said.

Change a line by changing the text after its ID. Switch a line off like this:

    B045 = off

Delete a line from the file to get the original back. Add a line of your own with a new ID, B143 or higher:

    B143 = What a hit, Ghip!

Inside a line, these words in square brackets do something:

- `[name]` is a player's name drawn by the game, the same name everywhere in the line.
- `[opponent quarterback]` is the name of the other team's quarterback.
- `[bleep]` plays the original's bleep sound.
- `[sound my laugh.wav]` plays your own sound file from the sounds folder.
- `[pause]` is a short pause of random length. `[pause 2]` is a pause of 2 seconds.
- `[then]` ends a spoken part. The words after it are said as a new part.
- `[faster]` ends a spoken part and says the next part one step faster.
- `[one of: some words | other words | more words]` says one of them, chosen by chance.

A line can be words only, a sound only, or both. For example, a line with text and a sound:

    B144 = What a hit! [sound crunch.wav] Ghip, did you see that?

A line that is only a sound:

    B145 = [sound crowd boo.wav]

A line has at most 500 characters and 20 parts. A sound file goes in the sounds folder inside the customize folder, and the line names it without a folder. Wav files work; if your files are ogg, flac or mp3, they work too when this game's sound layer can read them. A sound file that cannot be used is skipped, the rest of the line is said, and the game tells you once.

## The remarks of the N. F. L. rules

When the Rules item of the F9 menu is set to N. F. L. rules, the game also has remarks.txt in the same folder (with the Classic rules the game never makes or reads it). It holds the announcer's remarks of the added features. Today these are the remarks after a time out, TO01 to TO05, one said after a time out one time in three, the remarks when an onside kick is declared, ON01 to ON03, one said one time in three, the sentences that start a quarterback keeper or draw, QB01 to QB05, one of them said at every keeper and draw, the remarks after a penalty is accepted, PN01 to PN04, also one time in three, and the remarks of the replay: the hint before a review, CHS01 to CHS04 after a ruling that was wrong and CHC01 to CHC03 after a close call, and the remark after a review, RVR01 to RVR03 when a ruling was changed and RVC01 to RVC03 when it stayed (one time in two; RVC03, about a time out wasted, is said only after a challenge that lost, never after the replay official's review). It works like banter.txt: change a line, switch it off with `TO03 = off`, delete it to get the original back, or add your own with a new number, TO06, ON04, QB06 or PN05 and higher. The words in square brackets of the banter work here too, and these are filled in by the game:

- `<team>` is the team that called the time out, the team that kicks the onside kick, the team the flag is on, or, in the replay remarks, the team the ruling went against.
- `<coach>` is your name.
- `<quarterback>` is that team's quarterback (in a QB line, the quarterback who runs).
- `<surname>` (PN lines only) is the player the flag is on.

For example:

    TO06 = the <team> stop the clock. [bleep]
    ON04 = here comes the surprise that nobody is surprised by.
    PN05 = <surname> will hear about that one from the coach.

A remark is never one of the last three said. F8 switches the remarks off with the banter, except the QB lines: they are the play by play of a run, so they stay on, and if you switch every QB line off the original five are used.

## The radio broadcast of the N. F. L. rules

With the N. F. L. rules the game is a radio broadcast, and its lines are in remarks.txt too. When the comments are on (F8), the announcer says a line of radio banter now and then, after a score, after a change of possession and after one play in four, exactly where the original said its jokes; the lines are BN01 to BN142 (generic remarks about the crowd, the weather, the band, the people listening at home, football sayings and a little teasing of the color commentator). The color commentator is called Ghip until you choose another name (see "The commentator's name" below): after some plays and at some moments the commentator adds one line in a voice of their own, and the announcer sometimes turns to the commentator first with a line of ASK01 to ASK12. The commentator's pools are:

- CKO before the opening kick off, CBG after a gain of 20 yards or more, CSK after a sack, CTV after a turn over, CTD after a touch down, CFG after a field goal, CFM after a missed kick, CTC after a third down made, CTS after a third down stopped, CFD when a team goes for it on fourth down, CRZ when a team gets inside the twenty, CPN after a penalty, CTM at the two minute warning, CQE at the end of the first and third quarter, CHT at half time, CFN at the end of a game that one team won, CFT at the end of a tie, CTT in a close fourth quarter and CBO in a game that is decided.

In every pool of remarks.txt `<commentator>` is the commentator's name (Ghip, or the name chosen in F9, Rules, Commentator): the default lines that turn to the commentator use it, and you may use it in your own. In the commentator's lines `<team>` is the team the line is about, `<opponent>` the other team, `<quarterback>` that team's quarterback, `<yards>` the gain, `<situation>` a whole clause with the score (the Bengals lead the Jets 17 to 10) and `<quarter>` the quarter; `<coach>` is your name. Each pool takes only some of them: CKO `<team>`, `<opponent>`, `<coach>`, `<quarterback>`; CBG `<team>`, `<opponent>`, `<yards>`, `<quarterback>`; CSK `<team>`, `<opponent>`, `<quarterback>`; CTD, CFG, CHT, CFN, CFT, CTT and CBO `<situation>`, `<team>` and `<opponent>`; CTM and CQE also `<quarter>`; the others `<team>` and `<opponent>`. The BN lines and the ASK lines have only `<commentator>`. The lines are changed, switched off and added like every other remark (BN143 and up, CTD11 and up), and may name your own sound files. The broadcast's own random numbers are not the game's, so the broadcast never changes how a game goes. A remarks.txt of version 0.10.0 keeps working: a default line that it still holds unchanged follows the commentator's name, a line you changed stays as you wrote it.

The commentator speaks with a voice of their own: F12 asks for it after the five speakers and F11 for its volume (only with the N. F. L. rules and the broadcast on). The first time, the game gives the commentator the next voice of the announcer's engine. F9, Rules, Broadcast switches the commentator and the questions to them off; the radio banter stays, it is the banter of the N. F. L. rules. With NVDA or JAWS the screen reader speaks the commentator too, in its one voice. The first key you press cuts the line that is being said.

## The commentator's name

F9, Rules, Commentator (the twelfth item, before Reset) is the name of the color commentator: Ghip is the default. Enter opens a list: Ghip, 28 well-known sports podcasters and broadcasters in alphabetical order, the name you typed last time, and, last, "Type a name of your own". Up and Down move, typing letters jumps to a name (type "pat" for Pat McAfee), Enter chooses, Escape goes back with no change. Left and Right on the item step through the names without opening the list. The new name is used from the next game, like every rule, in the announcer's questions and banter, in the intro and in the remarks of the features, and it is saved in settings.txt (nx_commentator). The names come from the podcast rankings of 2025 and 2026 (spec\COMMENTATOR_NAMES.md lists them with their sources); they are used descriptively, the game's voice and lines are not theirs, and nobody named has anything to do with this game.

## The stadium sounds of the N. F. L. rules

With the N. F. L. rules the game plays about 20 short sounds of its own beside the original's: the crowd (crowd_cheer, crowd_roar, crowd_groan, crowd_boo, crowd_gasp, crowd_applause, crowd_oh), the hits (hit_helmet, hit_pads, ball_catch), flag_throw, first_down_chain, goal_post_hit, the clicks of the referee's microphone (mic_on, mic_off) and the referee's whistles (whistle_short, whistle_long, whistle_double, whistle_triple). They are generated sounds, in the folder assets\sounds_nx of the program folder. They are quiet (15 to 26 decibels under the sound volume of F11) and never wait. F9, Rules, Stadium sounds switches them off.

To use your own sound, put a file with the same name in the sounds folder of your NFL Football 4 folder (the folder that holds your own foot7.wav files; F9, Sounds, Open the sounds folder opens it): it replaces the sound. The file may be a wav, ogg, flac or mp3. To add a second sound to a family, give it a number: crowd_cheer2.wav, crowd_cheer3.wav; the game draws one of them each time. Delete your file to get the original back.

F9, Sounds has two items at its end for this. "Stadium and referee sounds" lists the nineteen sounds in plain words with the file name each one takes and says whether it is the original, your sound, or several (Enter plays it at the level it has in the game, and again plays the next sound of its family; F1 explains how to use your own file). The whistles are whistle_short (time outs), whistle_long (quarter ends, flags and the final whistle), whistle_double (the two minute warning and reviews) and whistle_triple. "Put the stadium sounds back" moves all your files with these names to the "removed sounds" folder after one Enter, so the originals play again; nothing is deleted. A file that cannot be read is skipped and the original plays instead; the Sounds menu's Check files counts it, and the log says which file it was.

## The penalties of the N. F. L. rules

With the N. F. L. rules the game also has penalties.txt. It lists the fouls the officials call, one line each, P01 to P26 and P33 to P37, with the name the announcer says (P34 to P37 are the fouls of the 2026 kicks: the illegal wedge, the kick off formation, leaping, and kick catch interference; they are called only when you play with a playbook, as the 2026 kicks are):

    P08 = holding

Change the name to have it said your way. After the name you can add a semicolon and one setting:

- `P08 = holding; off` and holding is never called.
- `P08 = holding; weight 50` and holding is called half as often. The weight goes from 0 to 200 percent; 100 is the usual.

The yards and the rules of each penalty are the N. F. L.'s and cannot be changed in the file. To switch every foul off, set Penalties to off in the Rules item of the F9 menu. Delete a line to get the original back.

## The quarterback runs of the N. F. L. rules

With the N. F. L. rules the offense menu has three more plays after Punt: 8 Quarterback Sneak, 9 Quarterback Keeper and 0 Quarterback Draw (the key 0 is item 10; Time Out and Save Game come after them; S takes you to Save Game, and the T key calls a time out at once, anywhere in a game). The sneak gains a yard or two behind the center, the keeper is a run around the end, and the draw looks like a pass first. A pass play can also end with the quarterback running when nobody is open, a scramble. A quarterback who gains eight yards or more may slide, and, with Penalties on, a late hit on a quarterback who slides is a foul. The computer's quarterback sneaks on third or fourth and one or two yards, and now and then keeps the ball or runs a draw. In the Rules item of the F9 menu, Quarterback runs switches the whole feature on or off. The sentence that starts a keeper or a draw is one of the QB lines of remarks.txt. The quarter statistics add Quarterback Runs and Quarterback Running Yardage; a run is also counted in the team's ordinary running plays and yards.

## The replay challenges of the N. F. L. rules

With the N. F. L. rules some rulings on the field are wrong, and nobody is told. The announcer may hint (the CHS and CHC lines of remarks.txt, never after a ruling that is plainly right). The replay official reviews the plays that are his: scores, turnovers, a failed fourth down, every play after the two minute warning and every play in over time. On every other play, while you have a challenge and a time out, the play menu has one more item, Challenge the Ruling (the letter C), before Time Out. It asks what was ruled, how many challenges and time outs you have and says that a time out is lost if the ruling stands; the answer starts at no. If the referee finds the ruling wrong and clear, the corrected play is told and the game goes on from it; if not, you lose a time out. Each team has two challenges in a game, and a third once one of them won. The letter C when the item is not in the menu says why not. The computer's coach throws its own flag, mostly after a hint. In the Rules item of the F9 menu, Replay challenges switches the whole feature on or off. The quarter statistics add Challenges Won and Challenges Lost. A game you save does not keep the ruling of the last play: after you load it there is nothing to challenge until the next play.

## The onside kicks of the N. F. L. rules

With the N. F. L. rules your team may try an onside kick instead of the normal kick off. The game asks you only when it makes sense: your team is behind in the third or fourth quarter, or ahead by one score (1 to 8 points) with five minutes or less left in the fourth. The answer starts at no. In the Rules item of the F9 menu, Onside kicks switches the whole feature on or off, and Onside question can be set to always, so that you are asked at every kick off and every kick after a safety. The computer tries an onside kick only in the fourth quarter, when it is behind and the game is nearly over. The remarks it says are the ON lines of remarks.txt; the fouls on the kick, offside and illegal touching, are P24 and P33 of penalties.txt. When you play with a playbook (F9, Rules), every kick off of your team is a short menu instead of the question: the deep kick, a short kick into the landing zone, a squib kick and the onside kick, and after a safety a punt from the 20; the kinds of kicks can be renamed or switched off in plays.txt like any play (K001 to K036), except the deep kick, which is always there.

## The playbooks of the N. F. L. rules

With the N. F. L. rules you choose an offense playbook and a defense playbook in the Rules item of the F9 menu: Team playbook (the style of your own team, with every play of the game; the usual), Classic (the original's plays and kicks), or one of seven styles: Pro Style, West Coast, Air Raid, Power Run, Zone Run, Option and Pressure. With a playbook, the offense menu starts with the original's items, Line Plunge to Punt, with their digits. Enter on one of the first five calls the playbook's choice of that kind of play and says its name. The Right arrow on one of them opens its lists of plays, for example Inside Runs and then, with Right again, Power and Gap Runs; Backspace or Left goes back, and so does the item Back (the letter B). M opens More Plays (play action, the quarterback's runs, options, run pass options, trick plays, goal line plays, clock plays and more), and in it N finds a play by the first letters of its name. In a list, the plus key adds the play to your favourites and minus takes it off; F opens your favourites, A calls your last play again, K kneels down and P spikes the ball when they help, and O opens Formation and Tempo. D says what the current item does, in plain words. Every play has its own outcome, worked out from the league's real numbers, and the sentences and sounds of the play are the original's. The defense menu works the same way: the original's six calls first, Right opens their lists (Blitzes, Zone Coverages and more). The playbook's choice behind Enter fits the down, the distance, the field and the score. The computer's teams call every play of the game the same way, leaning on their own style: their style's plays in styles.txt count double, and a play you switch off in plays.txt is never called by them either. After a touch down the computer may try for two points.

The folder playbooks has four files:

- plays.txt has every play with an ID, O001 to O167 for the offense, D001 to D092 for the defense and K001 to K036 for the kicks. Change the name after the ID to have it said your way (at most 30 characters and six words), or add `; off` to take a play out of every style and every menu: `O004 = Draw Play; off`.
- styles.txt has the seven styles, S1 Pro Style, S2 West Coast, S3 Air Raid, S4 Power Run, S5 Zone Run, S6 Option and S7 Pressure. A line like `S2O017 = weight 7` puts play O017 in the style with the weight the computer calls it with; `off` takes it out, and a line for a play that is not in the style puts it in. A line like `S2OB1 = families 3 4; vs 1 2 3; sack -2; comp 3` is a small change the whole style makes: its plays of those families change against those calls of the other team. Every number has a bound, two yards for ylo and yhi, five points for sack and comp, five for fum, and a number past its bound is a problem and the original is used. The notes at the top of the file list the families and the calls. `S6QB = 300` is how often the computer runs its quarterback, in percent of the usual; when you play with a playbook, a number under 100 lowers the computer's quarterback runs and options and 0 takes them out (the style's own lean decides the rest).
- team_styles.txt gives each of the 32 teams a style, for example `T01 = Air Raid; defense Pro Style`. Classic is the original's plays: put a team on Classic and the computer plays it with the original's plays.
- favourites.txt has your favourite plays, at most ten for the offense and ten for the defense: `OF01 = O027` puts play O027 first. The game writes it when you press plus or minus on a play; you may edit it too. A line the game does not understand is left out.

With Rules on Classic, none of these files is read.

The defense menu has the same keys as the offense menu: Right on a call opens its lists (blitzes, zone coverages and the rest), and M, More Plays, lists every list of defensive calls, the situation defenses and the kick defense first. In your first three runs the game says one sentence after the first item of the offense menu, the defense menu and Formation and Tempo: where Right and M are, that Enter on a play type lets the playbook pick the play (the call is told afterwards), and that "the playbook's choice" of a setting means the play you call sets it and nothing is recommended. Opening a list with Right or More Plays ends the hints. In settings.txt, `nx_menu_hints` counts the runs (set it to 3 to stop the hints, to 0 to hear them again).

## How the game speaks (a screen reader or the game's own voices)

Speech output is automatic: NVDA when it runs, else JAWS when it runs, else the game's own Windows voices. When a screen reader runs and you have not chosen yet, the game says "You are running NVDA. Do you want the game to speak through it?" once (Enter or Y for yes, N for no). Yes: the game asks for no voice at any time. No: the game uses its own Windows voices (a first start then asks for them). The answer is saved as `speech_output_chosen` in settings.txt; F9, Speech settings, Speech output changes it at any time. F12 and the voices item of F9 say why there is nothing to choose while a screen reader speaks.

## The news of a franchise

With the N. F. L. rules the game also has news.txt, the lines of the news you hear in a franchise before each game: the biggest win of the week, an upset, the closest game, another team's winning or losing streak, your own streak and your wins as a head coach, and, in the offseason, the champion, a star who retires, your player who improved a lot, the first pick of the draft and the team with the most room under the salary cap, and, before the trade deadline, a trade between two other teams. It works like remarks.txt: each line is an ID and the line. The letters of the ID say the kind of news: NWB the biggest win, NWU an upset, NWC the closest game, NWS another team's winning streak, NWL its losing streak, NWY your winning streak, NWZ your losing streak, NWM your wins as a head coach, NWT the champion, NWR a star who retires, NWD the first pick of the draft, NWP a player of yours who improved, NWK the team with the most cap space, NWX a trade between two other teams, NWJ a player of another team who is hurt and out for weeks and NWH a player who asks to be traded. Change a line, switch it off with `NWB02 = off`, delete it to get the original back, or add your own with a new number, NWB05 and higher. If every line of a kind is off, that kind of news is never told. The game takes one line of the kind by chance, never one of the last three of that kind. The words in square brackets of the banter work here too, except [name] and [opponent quarterback], because the news is told between games. These are filled in by the game:

- `<team>` is the team the news is about (in NWM, NWY and NWZ and in NWP, your team) and `<other>` the other team of the game.
- `<n>` is a number: the points of the win, the games in a row, your wins, or the season.
- `<score>` is the score as it is said, for example 24 to 17.
- `<coach>` is your name.
- `<player>`, `<position>` and, for NWP, `<r>`, the rating he has now, are in the kinds NWR, NWD, NWP, NWX, NWJ and NWH, and `<cap>`, the cap space said in millions, is in NWK only. In NWX `<team>` is the team that traded the player away and `<other>` the team he goes to. In NWJ `<n>` is the most weeks he may miss.

For example:

    NWB05 = what a thrashing! the <team> win by <n>. [bleep]
    NWY05 = coach <coach>, <n> in a row, and still counting.

The F8 key does not switch the news off. The lines of the offseason's stages are said as words only; a sound in such a line is played in the weekly news only. The F9 menu, Franchise, News, lets you hear the lines again.

The F9 menu, Franchise, To do list, asks again the items you left for later. The setting "staff handles the to do list" in Franchise settings makes the staff take its own recommendation for every item.

## The injuries of a franchise

Injuries happen only in a franchise, never in a quick game or a classic season. With the N. F. L. rules the game has injuries.txt, the words it says about them. It works like news.txt: each line is an ID and the words.

- IJA to IJM are the names of the kinds of injury, said in the injury report after the word "with" ("out with a sprained ankle"): IJA an ankle sprain, IJB a hamstring, IJC a knee sprain, IJD a shoulder, IJE a concussion, IJF the ribs, IJG a groin, IJH a broken hand, IJK a high ankle sprain, IJL a torn knee ligament, IJM the back. Each kind has three lines; one of the lines that are on is chosen by chance. If every line of a kind is off, the report says the player is out without naming the injury.
- IJX is what the announcer says when a player is hurt in a game you play. There `<player>` is the player, `<position>` his position and `<team>` his team.

Change a line, switch it off with `IJA01 = off`, delete it to get the original back, or add your own with a new number, IJA04 and higher. The words in square brackets of the banter work here too, except [name] and [opponent quarterback]. How often an injury happens and how long it lasts never depend on this file. For example:

    IJX05 = [sound my groan.wav] oh no, <player> is down and he is not getting up.
    IJE04 = a bad blow to the head

Before each game of the regular season you hear the injury report after the news: who is out, doubtful or questionable, and who is back. A doubtful or questionable player plays only when you say so: the to do list asks about the ones who matter, and the F9 menu, Franchise, Injury report, lists every hurt player of yours; Enter on a doubtful or questionable one changes whether he plays this week. If you leave the question for later, he rests. With the setting "staff handles the to do list" the staff plays a questionable player and rests a doubtful one.

## If something is wrong

- A line that cannot be used keeps the original, or is left out if it is new. The game says once how many problems it found in a file, and the log has the details. In the Customize menu, "Check the customization files" reads the results aloud.
- A file that is damaged as a whole (empty, not text, no first line, another format) is copied to a file with the ending damaged1 (the latest three are kept), and a new file with the original names is written. The game says so once.
- A file that is missing is written again, without a word.
- A file that another program holds open, or that cannot be written, is not changed. The original names are used that time.
- "Reset one list to the original" and "Reset all lists to the original" write the original files again. Your own file is kept with the ending before-reset, and the two copies before it with the endings before-reset2 and before-reset3. If the copy cannot be made, nothing is written. Your sound files and footplay.txt are never touched.
- If the game cannot read a file while it is running (another program has it open, for example), the names and lines it already loaded stay in use and it tells you once.
- A file may be up to one megabyte. A banter line's own sounds together are cut at 30 seconds, and its pauses together may be at most 30 seconds.


## Add more sounds to the game

The game draws one sound at random for two things: the quiet ambient sounds that come now and then while the game waits for a key, and the short celebration sounds after a touchdown, at half time and after the Super Bowl. You can add your own sound files to both, and the game will draw them too. Nothing needs editing: you only name the file the right way.

The sounds folder is here, and the Sounds menu (F9, Sounds, "Open the sounds folder") opens it:

    %APPDATA%\Kitchensinc Revival\NFL Football 4\sounds

Name an added file with the name of the pool and a number:

- `celebration1.wav`, `celebration2.wav`, `celebration3.wav` and so on, for the celebration sounds.
- `ambient1.wav`, `ambient2.wav` and so on, for the ambient sounds.

Wav, ogg, flac and mp3 files work. Capital letters do not matter, and the numbers can have gaps (celebration1 and celebration7 are fine). Any number of files is allowed. Then choose "Reload the sounds from the folder" in the Sounds menu, or start the game again. The menu item "Sound pools you can add your own sounds to" tells you, for each pool, how many sounds it has and what the next file should be called, and plays them one after the other.

To take one of the original sounds out of the draw, put a line such as `foot15 = off` in sounds.txt in the same folder. A file that cannot be read is skipped, and the game tells you once. Your added sounds are drawn with the same chances as the original ones, so if you add ten files the original ten are heard half as often.

Your announcer's comments are text, not numbered sound files: for your own comments and your own sounds in them, see banter.txt above.

## Commercials

The game has no commercials of its own and ships none. If you want some, put your own sound files in the commercials folder, which the game makes next to the sounds folder:

    %APPDATA%\Kitchensinc Revival\NFL Football 4\commercials

Any name, and wav, ogg, flac or mp3. A file in that folder can play at any break; a file in one of the folders inside it plays only at that break: `quarter` (the end of the first and the third quarter), `two-minute-warning`, `halftime` and `final` (after the final score). Then turn them on: F9, Sounds, Commercials. Left and Right (or Enter) change it between off, at every break, at every second break and at every third break. It is off until you turn it on, even when files are there.

At a break the game says "Commercial. Any key skips it." and plays one of your files. The files play in a shuffled order, and none repeats until all have been played. A key stops the commercial at once and goes no further. A commercial changes nothing in the game, its random numbers or your saved games.
