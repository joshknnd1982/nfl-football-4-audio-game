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
- the folder playbooks, with plays.txt, styles.txt and team_styles.txt: the plays of the N. F. L. rules' playbooks (see below).
- news.txt, the news lines of a franchise, only when the N. F. L. rules are chosen in F9 (see below).

After you save a file, choose Reload in the Customize menu, or start the game again. A game in progress keeps the players it already has.

## How a file looks

The first line says what the file is and its format, for example `# NFL Football 4 teams, format 1.` Leave it as it is. Lines that begin with `#` are notes. Every other line is an ID, an equals sign and the text:

    T09 = Mustangs

The ID stays as it is. The text is what the voice speaks, so spell it the way it should sound. A name has 1 to 30 characters, with no comma and no semicolon.

## Rename a team

Open teams.txt and change the name after the ID. The teams are T01 to T32. To rename the Broncos, change `T09 = Broncos` to `T09 = Mustangs`. Two teams cannot have the same name. If you give a team the name another team has, the later one goes back to its original name. A season in progress and a saved game are not affected: they keep numbers, not names.

## Rename a division

Open divisions.txt and change, for example, `D1 = A. F. C. North.` to `D1 = The Northern Group.` The conference names A. F. C. and N. F. C. also appear inside a few fixed sentences of the play offs, and those do not change.

## Your own players' names

footplay.txt holds the 33 names of your own team's players and your quarterback, in sections: Running Backs, Receivers, Defensive Players, Special Teams Players, Kickers and Quarterback. The game draws new random names at the first game of every season, and when a season ends it keeps your old names as footplay.previous.txt. Copy it back over footplay.txt to keep them. If you edit footplay.txt, keep the section headings and the number of names in each section. A section that is wrong gets new random names and the rest stays.

## Other surnames

surnames.txt has 1,708 lines, S0001 to S1708. You can change the names. There are always 1,708 of them.

## The banter

banter.txt has the 142 original lines, B001 to B142. Each time the announcer speaks, the game chooses one line that is on, by chance, and no line comes twice in a game. The F8 key switches all banter off, your lines too.

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

## The penalties of the N. F. L. rules

With the N. F. L. rules the game also has penalties.txt. It lists the fouls the officials call, one line each, P01 to P26 and P33, with the name the announcer says:

    P08 = holding

Change the name to have it said your way. After the name you can add a semicolon and one setting:

- `P08 = holding; off` and holding is never called.
- `P08 = holding; weight 50` and holding is called half as often. The weight goes from 0 to 200 percent; 100 is the usual.

The yards and the rules of each penalty are the N. F. L.'s and cannot be changed in the file. To switch every foul off, set Penalties to off in the Rules item of the F9 menu. Delete a line to get the original back.

## The quarterback runs of the N. F. L. rules

With the N. F. L. rules the offense menu has three more plays after Punt: 8 Quarterback Sneak, 9 Quarterback Keeper and 0 Quarterback Draw (the key 0 is item 10; Time Out and Save Game come after them, T and S take you to them). The sneak gains a yard or two behind the center, the keeper is a run around the end, and the draw looks like a pass first. A pass play can also end with the quarterback running when nobody is open, a scramble. A quarterback who gains eight yards or more may slide, and, with Penalties on, a late hit on a quarterback who slides is a foul. The computer's quarterback sneaks on third or fourth and one or two yards, and now and then keeps the ball or runs a draw. In the Rules item of the F9 menu, Quarterback runs switches the whole feature on or off. The sentence that starts a keeper or a draw is one of the QB lines of remarks.txt. The quarter statistics add Quarterback Runs and Quarterback Running Yardage; a run is also counted in the team's ordinary running plays and yards.

## The replay challenges of the N. F. L. rules

With the N. F. L. rules some rulings on the field are wrong, and nobody is told. The announcer may hint (the CHS and CHC lines of remarks.txt, never after a ruling that is plainly right). The replay official reviews the plays that are his: scores, turnovers, a failed fourth down, every play after the two minute warning and every play in over time. On every other play, while you have a challenge and a time out, the play menu has one more item, Challenge the Ruling (the letter C), before Time Out. It asks what was ruled, how many challenges and time outs you have and says that a time out is lost if the ruling stands; the answer starts at no. If the referee finds the ruling wrong and clear, the corrected play is told and the game goes on from it; if not, you lose a time out. Each team has two challenges in a game, and a third once one of them won. The letter C when the item is not in the menu says why not. The computer's coach throws its own flag, mostly after a hint. In the Rules item of the F9 menu, Replay challenges switches the whole feature on or off. The quarter statistics add Challenges Won and Challenges Lost. A game you save does not keep the ruling of the last play: after you load it there is nothing to challenge until the next play.

## The onside kicks of the N. F. L. rules

With the N. F. L. rules your team may try an onside kick instead of the normal kick off. The game asks you only when it makes sense: your team is behind in the third or fourth quarter, or ahead by one score (1 to 8 points) with five minutes or less left in the fourth. The answer starts at no. In the Rules item of the F9 menu, Onside kicks switches the whole feature on or off, and Onside question can be set to always, so that you are asked at every kick off and every kick after a safety. The computer tries an onside kick only in the fourth quarter, when it is behind and the game is nearly over. The remarks it says are the ON lines of remarks.txt; the fouls on the kick, offside and illegal touching, are P24 and P33 of penalties.txt.

## The playbooks of the N. F. L. rules

With the N. F. L. rules you choose an offense playbook and a defense playbook in the Rules item of the F9 menu: Classic (the original's plays, and the usual), Team playbook (the style of your own team), or one of seven styles: Pro Style, West Coast, Air Raid, Power Run, Zone Run, Option and Pressure. With a playbook, the play menu has groups, such as Inside Runs, Outside Runs, Screens, Short Passes, Deep Passes and Play Action. Enter opens a group and shows its plays; Backspace or Left goes back, and so does the last item, Back (the letter B takes you to it). Field Goal and Punt stay in the first menu. Every play is one of the original's plays with a small change, strong against some defense calls and weak against others; the announcer and the sentences of the play are the original's. The computer's teams call the plays of their own style.

The folder playbooks has three files:

- plays.txt has every play with an ID, O001 to O052 for the offense and D001 to D030 for the defense. Change the name after the ID to have it said your way (at most 30 characters and six words), or add `; off` to take a play out of every style: `O004 = Draw Play; off`.
- styles.txt has the seven styles, S1 Pro Style, S2 West Coast, S3 Air Raid, S4 Power Run, S5 Zone Run, S6 Option and S7 Pressure. A line like `S2O017 = weight 7` puts play O017 in the style with the weight the computer calls it with; `off` takes it out, and a line for a play that is not in the style puts it in. A line like `S2OB1 = families 3 4; vs 1 2 3; sack -2; comp 3` is a small change the whole style makes: its plays of those families change against those calls of the other team. Every number has a bound, two yards for ylo and yhi, five points for sack and comp, five for fum, and a number past its bound is a problem and the original is used. The notes at the top of the file list the families and the calls. `S6QB = 300` is how often the computer runs its quarterback, in percent of the usual.
- team_styles.txt gives each of the 32 teams a style, for example `T01 = Air Raid; defense Pro Style`. Classic is the original's plays: put a team on Classic and the computer plays it with the original's plays.

With Rules on Classic, none of these files is read.

## The news of a franchise

With the N. F. L. rules the game also has news.txt, the lines of the news you hear in a franchise before each game: the biggest win of the week, an upset, the closest game, another team's winning or losing streak, your own streak and your wins as a head coach, and, in the offseason, the champion, a star who retires, your player who improved a lot, the first pick of the draft and the team with the most room under the salary cap. It works like remarks.txt: each line is an ID and the line. The letters of the ID say the kind of news: NWB the biggest win, NWU an upset, NWC the closest game, NWS another team's winning streak, NWL its losing streak, NWY your winning streak, NWZ your losing streak, NWM your wins as a head coach, NWT the champion, NWR a star who retires, NWD the first pick of the draft, NWP a player of yours who improved and NWK the team with the most cap space. Change a line, switch it off with `NWB02 = off`, delete it to get the original back, or add your own with a new number, NWB05 and higher. If every line of a kind is off, that kind of news is never told. The game takes one line of the kind by chance, never one of the last three of that kind. The words in square brackets of the banter work here too, except [name] and [opponent quarterback], because the news is told between games. These are filled in by the game:

- `<team>` is the team the news is about (in NWM, NWY and NWZ and in NWP, your team) and `<other>` the other team of the game.
- `<n>` is a number: the points of the win, the games in a row, your wins, or the season.
- `<score>` is the score as it is said, for example 24 to 17.
- `<coach>` is your name.
- `<player>`, `<position>` and, for NWP, `<r>`, the rating he has now, are in the kinds NWR, NWD and NWP, and `<cap>`, the cap space said in millions, is in NWK only.

For example:

    NWB05 = what a thrashing! the <team> win by <n>. [bleep]
    NWY05 = coach <coach>, <n> in a row, and still counting.

The F8 key does not switch the news off. The lines of the offseason's stages are said as words only; a sound in such a line is played in the weekly news only. The F9 menu, Franchise, News, lets you hear the lines again.

The F9 menu, Franchise, To do list, asks again the items you left for later. The setting "staff handles the to do list" in Franchise settings makes the staff take its own recommendation for every item.

## If something is wrong

- A line that cannot be used keeps the original, or is left out if it is new. The game says once how many problems it found in a file, and the log has the details. In the Customize menu, "Check the customization files" reads the results aloud.
- A file that is damaged as a whole (empty, not text, no first line, another format) is copied to a file with the ending damaged1 (the latest three are kept), and a new file with the original names is written. The game says so once.
- A file that is missing is written again, without a word.
- A file that another program holds open, or that cannot be written, is not changed. The original names are used that time.
- "Reset one list to the original" and "Reset all lists to the original" write the original files again. Your own file is kept with the ending before-reset, and the two copies before it with the endings before-reset2 and before-reset3. If the copy cannot be made, nothing is written. Your sound files and footplay.txt are never touched.
- If the game cannot read a file while it is running (another program has it open, for example), the names and lines it already loaded stay in use and it tells you once.
- A file may be up to one megabyte. A banter line's own sounds together are cut at 30 seconds, and its pauses together may be at most 30 seconds.
