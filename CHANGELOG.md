# Changelog: what is new, and how to test it

This file lists everything new in each build of NFL Football 4, newest first, so that players and outside testers know what changed and what to try. Version 1.0.0 is the first full release. The versions before it are test builds, published on GitHub as pre-releases (the first from 0.16.2).

## Before you start

- **Report a bug with a problem report.** In the game press F9, choose Speech settings, press Down until you hear "Save a problem report", then press Enter. The game saves one file and says where. Send that file with a few words: what you did, what you heard, what you expected. The file holds no passwords and no account name.
- **Your files** (settings, saved games, franchise, your own sounds and texts, logs) are in `%APPDATA%\Kitchensinc Revival\NFL Football 4`. The program folder holds only the program.
- **Keys:** F1 repeats the last prompt, F5 lists every key, F6 explains the game, F7 explains football words, F9 opens the added functions.
- "N. F. L. rules" below means the game's default mode. "Classic" is the original game's exact mode (F9, Rules); most new things are in the N. F. L. rules only, the radio broadcast is in both.
- Where a test says "Tell us", that is a question the maintainer wants answered.

## Unreleased (since 1.0.4)

### Clock updates: the game says when the clock runs, and F4 gives the time as it runs down
From a tester's report on GitHub issue 17: the clock seemed to keep running after a man was pushed out of bounds, there was no way to know when the clock started to run, and no way to hear the time as it ran down. The first is the real N. F. L. rule: out of bounds stops the clock until the next snap only in the last 2 minutes of the first half and the last 5 minutes of the game; earlier, the clock starts again when the referee signals the ball ready, a few seconds after the play. Now, with the N. F. L. rules, a new item in F9, Rules, "Clock updates" (on by default, just before Reset), makes this audible: after every play one short sentence says "the clock is running", "the clock is stopped", "the clock starts again on the referee's signal" (out of bounds early in a half) or "the clock is stopped until the snap" (out of bounds late). While you choose your play the clock runs down second by second when it is running, and F4 says the time now followed by whether the clock is running; it never runs further than the time that would run before the snap, so the game's clock is the same as before however slow or quick you are. A time out stops the clock where F4 said. F1 says the clock the same way. F6 explains the out of bounds rule and the item. With Clock updates off, everything is as in 1.0.4. The game's log now writes the clock after every play, so a report shows why it ran or stopped.

**How to test:** with the N. F. L. rules, play a game. After each play you should hear whether the clock is running. In the first quarter, when a runner is pushed out of bounds, you should hear "the clock starts again on the referee's signal"; in the last 5 minutes of the game, "the clock is stopped until the snap". After a run that stays in bounds, wait in the play menu and press F4 a few times: the time should go down and end with "the clock is running". Then turn F9, Rules, Clock updates off and check that the sentences stop.
**Tell us:** whether one sentence after every play is right, or too much (asked on issue 17), and whether F4's running time is useful.

## 1.0.4 (2026-11-15, test build)

Built from a tester's answer on GitHub issue 11: in overtime's last two minutes too, a time out pressed during a play is called as soon as the play ends. Everything of 1.0.3 and earlier below is in it.

### In overtime's last two minutes too, a time out pressed during a play is called when the play ends
From a tester's answer on GitHub issue 11. Since 1.0.3, a T pressed after the snap or the kick calls no time out, except in the last two minutes of the second and fourth quarters, where your time out is called as soon as the play ends. Asked whether overtime's last two minutes should work the same way, the tester chose yes. So now, with the N. F. L. rules, the same holds with 2:00 or less left in overtime: in the regular season's overtime period, and in the play-offs in the second and fourth overtime periods (the ones that have a two-minute warning, like the second and fourth quarters). Earlier in overtime, and in the first and third play-off overtime periods, a T after the snap is still not kept. The run-out question of a kick-off then says "the ball is live. you will have the time out when the play ends." F5, F6 and the README say it in the line for T.

**How to test:** with the N. F. L. rules and time outs on, play a game into overtime (a close game in a season, or tie it late). With 2:00 or less left in overtime, choose a play and press T after the quarterback says "Hike!". Right after the play the referee should call your time out and the clock should stop. Earlier in overtime, the same T should give "your time out came after the snap, so none was taken" after the play.
**Tell us:** whether the time out after the play comes when you expect it in overtime.

## 1.0.3 (2026-11-15, test build)

Built from a tester's answers to the open questions on GitHub (issues 6, 10, 11, 12, 14 and 16) and his answers to the follow-up questions: a penalty on the try moves the extra point, a time out pressed after the snap is no longer saved for after the play except in the last two minutes of a half, more substitution features (the backup returners, packages by formation and for the kicks, the computer resting its starters late in a game), the kick-off set-up said again and a re-kick asked again after a time out, and Quarterbacks also in F9, Franchise. Everything of 1.0.2 and earlier below is in it.

### A penalty on the try moves the extra point kick by its yards
From a tester's answer on GitHub issue 12. Since 0.16.24, after a penalty on your try for two points you choose again between the kick and the try for two, but a kick chosen then was always the usual extra point. Asked "should a penalty make the extra point longer or shorter?", the tester chose "move the kick by the penalty's yards". So now, with the N. F. L. rules and a playbook (the default), a penalty on the try moves the kick too, as the real rules do: from the kick's own spot, the 15 yard line, a foul by your team makes the kick longer (5 yards: from the 20, a 38 yard kick instead of 33) and a foul by the defense makes it shorter (5 yards: from the 10, a 28 yard kick), never more than half the way to the goal line; pass interference by the defense moves it half the way. Two penalties on one try add up. A longer kick is missed more often and a shorter one less often, as a field goal of that length would be. Before "select", one sentence says where the kick would be from and how long it is, so you know before you choose. A personal foul by the defense on your touchdown moves your kick the same way, and when the computer kicks a moved extra point the announcer says how long it is before the kick. The try for two keeps the spot the penalty gave it, also when you chose the kick and then called a time out. With no penalty, the extra point and the luck of the game are exactly as before. Classic, the original's exact game, has no penalties and its extra point never fails.

**How to test:** with the N. F. L. rules, Penalties on and a playbook, score a touchdown and choose "try for two point conversion". Play tries for two until a flag is accepted on one (a false start or illegal shift by your team is the most common). After the referee's words you should hear "after the penalty, the kick for extra point would be from the 20 yard line, a 38 yard kick", then "select" and "try for two point conversion". Press Up for the kick and Enter: the kick is made from there. After a foul by the defense the sentence should give a shorter kick.
**Tell us:** whether the sentence before the choice is clear, and whether the longer kicks are missed about as often as you expect.

### A time out pressed after the snap is no longer saved for after the play, except in the last two minutes of a half
From a tester's answer on GitHub issue 11. Asked whether T at the quarterback's "Hike!" should stop the play like the kicks, he chose to keep the snap as it is, "with an exception: you wouldn't want a timeout most likely after the play is over." Until now, with the N. F. L. rules, T pressed once the ball was snapped or kicked was kept and your time out was charged the moment the play ended. Now such a T calls no time out: nothing is charged, the clock runs after the play exactly as it would without the key, and when the play ends you hear once "your time out came after the snap, so none was taken." Pressed while the run-out question of a kick-off waits, you hear "the ball is live, so no time out is taken" at once, and nothing more after the play. T before the snap, during the snap count, and while the holder or the punter says "hike" works as before (the play is not run). The exception, from his answer to a second question: in the last two minutes of the second and the fourth quarter, T pressed during a play still calls your time out as soon as the play ends, so you save the seconds that would run before the next snap; there, the run-out question says "the ball is live. you will have the time out when the play ends." Overtime is not a half, so there T during a play is not kept (asked on issue 11). F5 and F6 say it in the line for T.

**How to test:** with the N. F. L. rules and time outs on, choose a play; after the quarterback says "Hike!", while the play is told, press T. After the play you should hear "your time out came after the snap, so none was taken", and F1 in the next menu still gives three time outs. Press T in that menu: the time out is called as always. Then, with 2:00 or less left in the second or fourth quarter, press T after "Hike!" again: this time the referee calls your time out right after the play and the clock stops.
**Tell us:** whether overtime's last two minutes should work like the end of a half (asked on issue 11).

### "All backups in" also puts the backup returners in
From a tester's answer on GitHub issue 14. "All backups in" (U in a play menu) kept your kick and punt returners in; now the backup returners come in too: your team's next kick and punt returners (with the real rosters, the second returners of each kind), else backs, receivers or defensive backs of your backups. The kicker and the punter stay. "Starters back in" brings the returners back too.

**How to test:** with the N. F. L. rules, press U in a play menu, then Enter on "All backups in for the game". Press U again and go down to the kick and punt returners: other men are named than before. At the next kick-off or punt to you, the new returner is named.

### Packages by formation and for the kicks
From a tester's answers on GitHub issue 14, as Madden's formation substitutions. The substitutions (U in a play menu) have a new last item, "Formation and kick packages". It lists the offense's formations (under center, shotgun, pistol, singleback, I formation, split backs, empty backfield, heavy goal line, and the other formations), the defense's packages (goal line with three defensive backs, base with four, nickel with five, dime with six, quarter with seven) and, as its last five items, the kicks' teams (the kick-off team, the kick return team, the punt team, the punt return team, and the field goal and extra point team), each with how many players you set. Enter on one lists the groups as they play in it, then the places and the players, as for a substitution, but with no question of how long: the player comes in for every play you call in that formation, and goes back out after it. "Clear this package" ends one. The offense's formation is the one the play lines up in (or the Formation setting of Formation and Tempo when you set one); the defense's is the number of defensive backs your call has against that offense. Plays of the Classic playbook have no formation, so no package plays there. A kick's team plays at that kick only: the kick-off team at your kick-offs, the kick return team at the computer's, the punt team at your punts, the punt return team at the computer's punts, and the field goal team at your field goals, extra points and fair catch kicks (the computer's field goals have none). "Starters back in" keeps your packages. Save Game keeps them. Nothing about the plays or the luck of the game changes; only who plays.

**How to test:** with the N. F. L. rules and a playbook (the default), press U in a play menu, press End for "Packages by formation", Enter. Down to "Shotgun", Enter; choose the running backs, place 1, and another back, Enter: you hear that he comes in for every Shotgun play. Escape back to the play menu and call a shotgun play: the back you set carries or catches the ball by his name. Call a play from under center: your usual starter is back. Then in the same list press End for "Field goal and extra point team", Enter, choose the kicker and the punter in his place: your next field goal and extra point are kicked by the punter, and your next punt by the punter as usual. In the kick return team, put a receiver in as kick returner 1: at the computer's next kick-off he is the returner you hear.
**Tell us:** whether the kicks' teams play at the right kicks.

### The computer rests its starters when it leads by a lot late in the game
From a tester's answers on GitHub issue 14. With the N. F. L. rules, when the computer's team leads by 21 points or more with 5 minutes or less left in the fourth quarter (the tester chose "later and less often"), it puts its backups in, and the announcer says "the" team "are resting their starters." If your team comes back to within 13 points, its starters return ("send their starters back in"). It never happens in overtime or before the fourth quarter. Its kicker and punter stay. In a franchise its backups play with their own ratings, so a big comeback is a little easier, as in a real game; in a single game only the names change. Save Game keeps it.

**How to test:** with the N. F. L. rules, let the computer lead by three scores in the fourth quarter (a franchise game against a strong team is quickest). With more than 5 minutes left nothing happens; at 5:00 or less, between plays you should hear that it is resting its starters, and its backup quarterback is named on its plays. Score twice to get within 13: its starters come back.
**Tell us:** whether it now rests at the right moment.

### After your time out, the whole kick-off set-up is said again
From a tester's answer on GitHub issue 16 (question 1, choice b). Since 1.0.2 a time out before your own kick-off brings "choose your kick off" back, but after your new choice the announcer did not say again who is back deep to receive. Now he says the whole set-up again: who is back deep, then that your kicker is set to kick it off. Classic, which has no time outs, is not changed.

**How to test:** with the N. F. L. rules and time outs on, at your kick-off choose Deep Kick and press T while the announcer gives the set-up. After the time out, choose again (for example 2 and Enter): you should hear who is back deep, then your kicker, then the short kick.

### A time out before a kick-off made again after a penalty asks your kick again
From a tester's answer on GitHub issue 16 (question 2, choice b: "that is how it is in nfl rules"). When a penalty makes your kick-off be kicked again, the game still uses the kick you chose and asks nothing. But a time out by T before that kick now takes it back and brings "choose your kick off" (or, without a playbook, the onside question when it is asked) back, from the spot the penalty moved the kick to, as a first kick-off does since 1.0.2. An onside kick made again and chosen again counts as the same onside try. The computer's kick made again is never asked.

**How to test:** with the N. F. L. rules, Penalties on and time outs on, kick off until a flag makes your kick-off be kicked again (offside by your kicking team is the usual one). In the set-up of the kick made again press T: after the time out you hear "choose your kick off" again; your new kick is made from 5 yards farther back.

### Quarterbacks is also in F9, Franchise
From a tester's answer on GitHub issue 10 (choice c, both places). F9, Rules, Quarterbacks, where you choose any team's starting quarterback, stays in Rules and is now also in F9, Franchise, next to the depth charts: in a franchise right after "your depth chart" (every later item there is one further down), and outside a franchise as the last item, after "Depth charts". It is the same list in both places.

**How to test:** with the N. F. L. rules, press F9, Down to Franchise, Enter. Outside a franchise press Up once: "Quarterbacks"; in a franchise it is the 5th item, after "your depth chart". Enter lists the teams as F9, Rules, Quarterbacks does.

### Two whistles on a play with a flag stay
From a tester's answer on GitHub issue 6 (choice a). A play with a flag keeps both whistles, the play's and then the referee's before he gives the penalty, as a real referee blows the play dead and then signals the foul. Nothing changes; this item only records the answer.

**How to test:** with the N. F. L. rules and Penalties on, play until a flag: you hear the play's whistle, then the referee's whistle and the penalty.

## 1.0.2 (2026-11-15, test build)

Two fixes from testers' GitHub issues: the computer team's own defenders are no longer named in its plays, and a time out after you chose your kick off lets you choose it again. Everything of 1.0.1 and earlier below is in it.

### A pass batted back names a defender of the defense, not of the team with the ball
From a tester's report (GitHub issue 15): "It is still putting defensive players in on offense for computer teams." His game log showed it: while the Bears had the ball, the announcer said "Tyrique Stevenson Senior bats it right back at Caleb Williams!", and Tyrique Stevenson is a Bears cornerback. Of the nine ways a pass falls incomplete, the original game named, in "bats it right back at the quarterback", a defender of the team that threw the pass, for either team. With the N. F. L. rules it is now always a defender of the team on defense: when the computer has the ball, one of your defenders bats it back; when you have the ball, one of the computer's. Nothing else changes: the same plays, the same results, the same luck. Every other name in a play (the tackles, the passes knocked down, the interceptions, the fouls) was already the right team's, and the tester's franchise files show every computer team's backs, receivers and quarterback at their real positions. Classic, the original's exact game, keeps the original's sentence.

**How to test:** with the N. F. L. rules, play a game (a franchise or a single game) and let the computer throw a good number of passes; listen for "bats it right back at" followed by the computer's quarterback. The player named before it must be one of YOUR defenders (F9, Franchise, your roster, or the starting lineup in your depth chart, tells you who they are). On offense, when your own pass is batted back, the man named must be one of the computer team's defenders. It is one sentence of nine, so it may take a few games to hear it.
**Tell us:** if you hear any player of the team with the ball named as a defender in a play, or any defender carrying or catching the ball for the computer team, save a problem report right after it, so we see the exact play.

### A time out before your kick off lets you choose your kick off again
From a tester's report (GitHub issue 16): "call a timeout after selecting a kick such as short kick onsides kick", "expected result you have the option to pick the type of kick. actual result it uses the kick you picked before the timeout." His game log showed it: he chose Deep Kick, pressed T while the announcer said that his kicker was set to kick it off, the time out was called, and the deep kick was made. With the N. F. L. rules, a time out you call with T after you chose your kick off and before the kick now takes that kick back: after the time out, "choose your kick off" comes again and you can choose any kick (deep, short, squib, onside, and the safety punt after a safety). With the Classic playbook and onside kicks on, the onside kick question is asked again the same way. Who is back deep to receive is not said a second time; the kicker's sentence comes again before the new kick, so you still hear when the kick is made. An onside kick that a time out took back is not counted in the onside kick statistics. A field goal, a punt and the try already worked this way. When the computer kicks off, your time out is called and its kick goes on as before, and a kick made again after a penalty keeps its kick as before. When you press no T, the game, its words and its luck are exactly as before. F5 and F6 say it in the line for T.

**How to test:** with the N. F. L. rules and a playbook (the default), play until you kick off (after you score, or at the start of a half you kick). At "choose your kick off" press Enter for Deep Kick. While the announcer says who is back deep or that your kicker is set to kick it off, press T. You hear the whistle, "time out called by" your team and how many time outs you have left, then "choose your kick off" again. Press 2 and Enter for the Short Kick: the short kick is made, not the deep kick. Next time, choose 4, the Onside Kick, press T in its line-up, then Enter on Deep Kick: the deep kick is made. If you press T a second time before the same kick, you hear "you have already called a time out" and the kick goes on.
**Tell us:** whether the choice comes back when you expect it, and whether hearing the kicker's sentence again before the new kick helps or is too much.

## 1.0.1 (2026-11-14, test build)

One new feature from a tester's GitHub issue: substitutions during a game. Everything of 1.0.0 and earlier below is in it.

### Substitutions: your backups in, or any player in for a play or for the rest of the game
From a tester's suggestion (GitHub issue 14): "Add an option to sub players in for either a play or for the rest of the game. Example I might want to put all backups in if winning by a large amount. I might want to put a particular player in for a play." With the N. F. L. rules, press U in any play menu, on offense or on defense, to open the substitutions for your team. The first item, "All backups in for the game", rests your starters at every position: the players behind them on the depth chart play, the backup quarterback too; the returners, the kicker and the punter stay. Once anything is changed, "Starters back in, undo every substitution" puts everyone back. Then come the groups (quarterback, running backs, receivers, defensive linemen, linebackers, cornerbacks, safeties, kick and punt returners, kicker, punter), each said with who plays there now. Enter on a group lists its places; Enter on a place lists who can come in there: the players of that position (a fullback for a halfback, any linebacker for a linebacker), each with his position and where he plays now or "on the bench". Enter on a player asks "For the next play only" or "For the rest of the game". A player who already plays another place changes places with the man he replaces. In these lists D says what a position does, Escape goes back one list, and T still calls a time out. A substitution for the next play ends when that play is over (a false start or other foul before the snap keeps it, as the down is played again). A substitution never changes the luck of the game: with nothing changed the game is exactly as before. Save Game keeps your substitutions. In the Franchise the player you put in plays with his own rating, his carries count, and he can be hurt; a hurt player leaves at once and his place goes back to your depth chart. Classic has no U key: its keys are the original's.

**How to test:** with the N. F. L. rules, start a game and, at your first play menu, press U. You should hear "substitutions. Who plays for your team?" and "1. All backups in for the game". Press Enter: "your backups are in for the rest of the game". Press Escape, then F1 or play a pass: the announcer should name your backup quarterback and backup receivers. Press U again: the first item is now "Starters back in, undo every substitution"; press Enter and your starters are back. Now press U, Down to "running backs", Enter, Enter on running back 1, Down to a backup, Enter, and choose "For the next play only": you hear that he comes in for your starter for the next play. Run a play: the next play he is out again (press U and listen to the running backs). Do the same with "For the rest of the game": he stays in. On defense, U works the same way. Save the game with a substitution, quit and load it: the substitution is still there. In F5 and F6 you should hear the U key.
**Tell us:** whether the substitutions let you do what you wanted, whether the lists are quick enough to use between plays, and whether "backups in" puts in the players you expected.

## 1.0.0 (2026-11-12, release)

The first full release of NFL Football 4. It is the game of the test build 0.16.25, whose listening tests the maintainer has passed; nothing in how the game plays or sounds changed since 0.16.25. Everything of 0.16.25 and earlier below is in it.

### The first full release
The installer's first page no longer calls this a test build: it says version 1.0.0, the first full release. The game's About says version 1.0.0. A portable zip comes with this release too: unpack it anywhere and start nfl4.exe in its 64-bit or 32-bit folder, with nothing installed; it keeps your settings in the same place as the installed game.

**How to test:** run the installer `nfl4-setup-1.0.0.exe` over your test build: its first page says "version 1.0.0, the first full release", and your settings, saved games and franchise are still there after it. In the game press F9, then Up once (the menu goes around to its last item, About), then Enter: you hear "Version 1.0.0."

## 0.16.25 (2026-11-11, test build)

One change from a tester's GitHub issue: you can release a player in the Franchise without signing anyone. Everything of 0.16.24 and earlier below is still to be tested too.

### Release a player without signing anyone (Franchise)
From a tester's report (GitHub issue 13): "Currently in franchise mode there is currently no way to release someone unless you are planning to sign someone this needs updated." Until now a player of your team could only be released as part of signing a free agent. Now you can release any player of your 53 on his own, in two places: in F9, Franchise, your roster, press Enter on a player and choose "release him" (the last item); or in F9, Franchise, free agents, choose "release a player", then the position, then the player. Before anything is done you hear one question with his contract, the dead money releasing him costs (it counts against the salary cap) and the cap room you will have left; Enter releases him, Escape keeps him. He becomes a free agent, so you or another team may sign him again. A release is refused, with the reason said, when the player is hurt, when your team would have fewer than the players it must keep of his group (for example two quarterbacks, one kicker), when his dead money would put you over the cap, during a game, and in the offseason (the roster cut releases players there). Releases work in the regular season and the play-offs, before the kick-off of the week. If you had chosen him as a starter, you hear who starts in his place. A practice squad player in your roster can be released the same way, and saying no to a practice squad release now says "you did not release", not "you did not sign".

**How to test:** with the N. F. L. rules and a franchise, in the regular season at the main menu before a game, open F9, Franchise, your roster. Go to a backup (for example a defensive lineman), press Enter, then End: you should hear "release him". Press Enter: you should hear his contract, his dead money and your cap room after. Press Escape: "you did not release" him and he stays. Do it again and press Enter: "is released and is a free agent now", and the roster's count is one lower. Then open F9, Franchise, free agents: its fourth item is "release a player". Try to release your only kicker: you should hear that a team must keep at least 1 kicker. Save, quit and open the franchise again: the player is still gone and is in the free agents' list.
**Tell us:** whether releasing a player now does what you wanted, and whether the question before the release tells you enough.

## 0.16.24 (2026-11-10, test build)

One change from a tester's GitHub issue: after a penalty or a time out on your two-point try, you may kick instead. Everything of 0.16.23 and earlier below is still to be tested too.

### After a penalty or a time out on your two-point try, you may kick instead
From a tester's report (GitHub issue 12): "when going for 2 points if a penalty or timeout is called you don't get the choice to go for 2 or kick the extra point." His problem report showed it: he went for two, a flag for an illegal shift on his own team was accepted, the referee said the try would be played again from the 7 yard line, and the game went straight back to the play menu. A time out before the snap of the try did the same. The real rule (N. F. L. rule 11, section 3, article 1) lets the team with the ball change its choice after a penalty or a charged time out. Now, after either one, the game asks "kick for extra point" or "try for two point conversion" again. It starts on the try for two, so Enter keeps your choice, from the spot where the penalty put the ball; Up or Down gives the kick. A time out called after you chose the kick asks the choice again too, as before. When the computer's two-point try is played again after a penalty, you now get your defense menu; before, the game wrongly gave you an offense menu for the computer's try.

**How to test:** with the N. F. L. rules, score a touchdown, choose "try for two point conversion" and, in the play menu, press T. You should hear the time out called, then "select" and "try for two point conversion" again; press Up to hear "kick for extra point" and Enter to kick, or Enter right away to keep the try for two. Play more tries for two until a flag is thrown on one and the try is played again: the same choice should come after the referee's words. Classic is unchanged: it has no penalties or time outs.
**Tell us:** whether the choice comes every time a flag or a time out stops your try, and whether starting on the try for two feels right.

## 0.16.23 (2026-11-09, test build)

One change from a tester's GitHub issue: a time out pressed while the holder or punter says "hike" is called before the kick. Everything of 0.16.22 and earlier below is still to be tested too.

### A time out while the holder says "hike" ices the kicker
From a tester's report (GitHub issue 11): "I tried to call a timeout before the kicker kicked a Field goal. It wasn't granted." His problem report showed T pressed while the holder was still saying "hike". The game had already counted the kick as snapped at the start of that word, so it kept the time out for after the play: the field goal was good, and the time out was used up before the kick-off. Now the holder's or punter's "hike" still belongs to the snap count: T while it is said stops it at once, the time out is called, the kick is not made and the play menu comes again. This works the same for a field goal, a punt and the kick after a touchdown. Once "hike" has been said the kick is live, and a T then is kept for the end of the play, as before. A play from scrimmage is unchanged: it is live from the quarterback's "Hike!", where the snap sound starts.

**How to test:** with the N. F. L. rules, play defense until the other team lines up for a field goal (the announcer names the kicker and the holder). Listen to the holder's count, "hut 1, hut 2, hut ... hike", and press T right as you hear "hike". You should hear the word cut off, "time out called by" your team, the time outs you have left, and then your defense menu again; the kick is tried again after your time out. Press T a moment later, during "the snap is good": the kick goes on, and the time out comes after the play, as before. F6 (in its list of keys) and the README's Keys section now say that T works until the holder or punter has said hike.
**Tell us:** whether pressing T at "hike" now feels like icing the kicker, and whether there is any moment before a kick when T still does not work.

## 0.16.22 (2026-11-09, test build)

One change from a tester's GitHub issue: the depth chart moved to the Franchise menu, next to your roster. Everything of 0.16.21 and earlier below is still to be tested too.

### The depth chart is in the Franchise menu now, next to your roster
From a tester's suggestion (GitHub issue 10): "Consider moving deapth Chart to either roster or Franchise. I think this would make more sense." The depth chart was the seventeenth item of F9, Rules, among the rule switches. It is now in F9, Franchise. While you play a franchise, "your depth chart" is the item right after "your roster" (the fourth item; the items after it, from league history to play classic seasons, are each one further down). When you play single games or classic seasons with the N. F. L. rules, "Depth charts" (any of the 32 teams) is the last item of F9, Franchise. Inside, nothing changed: the starting lineup, every position, U and N to move a player, the key downs and moments, and back to the real or the staff's order. The roster is linked too: in F9, Franchise, your roster, Enter on a player now has "his place on the depth chart", which opens his position's order with the list on him, so U and N move him up and down right away. F9, Rules now has 17 items, Reset the last. What you set before is kept.

**How to test:** with the N. F. L. rules and a franchise, open F9, Franchise and press Down three times: you should hear "your depth chart"; Enter opens your team's depth chart as before. Then go up one item to your roster, press Enter, Down to a backup, Enter, and choose "his place on the depth chart": you should hear his position's list starting on him; press U and he should move up one place. Outside a franchise, open F9, Franchise and press End: "Depth charts" lists the 32 teams. Open F9, Rules: the depth chart should be gone from it, Reset the seventeenth item.
**Tell us:** whether the new places are where you would look for the depth chart, and if any help or menu still sends you to F9, Rules for it.

## 0.16.21 (2026-11-09, test build)

Three changes from a tester's GitHub issues: the field goal's length on the radio, a franchise that saves again after a man comes back from a reserve list, and rosters that update for every team. Everything of 0.16.20 and earlier below is still to be tested too.

### The announcer says how long a field goal try is
From a tester's request (GitHub issue 7): "have radio announcer tell you the distance of the field goal being attempted. It should be just like in a radio broadcast." With the radio play calls (F9, Rules, Play calls: radio, the default), the call before every field goal now names its length, for example "Here comes Kim for a 42-yard field goal attempt." A try of 50 yards or more is called a long one, a little more excited. The fair catch kick says its length too, and some of the calls after the kick say it again ("From 42 yards, right through!"). The length is counted as on a real field: the yards to the goal line, plus 7 for the hold and 10 for the end zone, where the goal posts stand. It works with the N. F. L. rules and with Classic. With Play calls set to plain, the game keeps the original game's words, which have no length.

**How to test:** play a game with the radio play calls on and kick a field goal from your opponent's 25 yard line (Field Goal in the play menu): the announcer should say a 42-yard try. Try one from the opponent's 35 or farther out: it should be called a long one. Listen after the kick for the length said again on some kicks.
**Tell us:** whether the length comes at the right moment, and whether any wording sounds wrong.

### A franchise saves again after a man comes back from a reserve list
From a tester's report (GitHub issue 8): "After activating someone off injured reserve it can't save the franchise." A man who was on injured reserve, the PUP list or the NFI list when the franchise began had no contract, and activating him brought him back to the 53 without one, so from then on the franchise could not be saved and every change after it was lost when the game closed. Now he comes back on a new contract at the market price for his position and rating (the same contract the roster cut gives a man who comes back from a list), and the question before you press Enter says it, for example "Kerby Joseph comes back on a new contract of 3.3 million for 4 years." A man you placed on injured reserve yourself keeps his own contract. If a man on your roster ever has no contract again, the game now gives him one when it saves instead of refusing to save, and writes that in its log.

**How to test:** in a franchise with the N. F. L. rules, from week 5 on, open F9, Franchise, injured reserve, your players on the reserve lists. Choose a man who was on a list when the franchise began (one on the PUP list can be activated at once; one on injured reserve is designated first, then activated). Before Enter you should hear his new contract. After the activation, quit the game and start it again: he should still be on your active roster, and the game should not say that the franchise could not be saved.
**Tell us:** if any change of a franchise is gone after you start the game again, or if the game says the franchise could not be saved.

### Get the latest rosters brings every team up to date, and your own franchise team too if you want
From a tester's report (GitHub issue 9): "It says 4 teams can't be updated. I also haven't played a game or made any trades. My roster wasn't updated." Two things were wrong. (1) The day after a game, several teams' own roster pages are a day behind their moves: the players called up from the practice squad for the game are still listed on the 53, and a player just released is still on the practice squad. The game then counted more than 53 players or more than 17 on the practice squad and kept the whole team as it was. Now, for such a team, the game also reads the team's own transactions page: only the players it called up for the game go back to the practice squad, never more than the squad has room for and never a player the team signed to its 53; a player the page says was released is left out, and a player it says was placed on injured reserve stays there. Measured on the real pages of November 9: all 32 teams came up to date, where 3 had been kept. (2) In a franchise, the update never changed your own team. The question after the update now has a third answer, "Yes, all 32 teams, my own team too": your team becomes its real roster of that day, the players you put first on your depth chart stay first while they are with you, and a starter you chose who left is named once. The first answer, "No, keep my league as it is", is still the one Enter and Escape take, and the second still leaves your team as it is.

**How to test:** start a franchise with the N. F. L. rules, then choose F9, Franchise, get the latest rosters (it needs the internet). The game should say where the rosters came from and, on most days, no team that could not be read. When it asks about your league, press Down twice and Enter: "Yes, all 32 teams, my own team too". You should hear how many players moved or joined; then look at your roster (F9, Franchise, roster) and your depth chart: your team should match its real team today.
**Tell us:** if the game still says that some teams could not be read (and on what day), or if a player of your team is not where his real team has him.

## 0.16.20 (2026-11-07, test build)

One whistle, now really. From a tester's report on 0.16.19. Everything of 0.16.19 and earlier below is still to be tested too.

### The tackles no longer blow the original game's whistle
From a tester's report (GitHub issue 6): "two whistles appear to be used still." 0.16.18 made every whistle the one whistle the game made, but the original game's three tackle sounds (the pile up, two tacklers and one tackler) end in a referee whistle of their own, so every tackle still blew the original's whistle and every other dead ball the made one. With the N. F. L. rules the game now plays a tackle only up to the moment its old whistle began, then blows the one whistle at that same moment; a play takes as long as before. Your own whistle.wav replaces it there too. A tackle sound of your own (foot4, foot5 or foot6 in the sounds folder) should hold only the hit: it is played whole and the whistle follows it. The Classic rules keep the original game's sounds whole.

**How to test:** play a game with the N. F. L. rules and listen to a run that is tackled, a completed pass and a sack: after the hit you should hear the same whistle as after an incomplete pass, a kick off and the end of a quarter, and no second, different whistle. Turn the stadium sounds off (F9, Rules, Stadium sounds) and listen again. A play with a flag still has two whistles of the same sound: the one that ends the play and the referee's for the flag.

**Tell us:** if you still hear a whistle that is not the same as the others, and after what kind of play.

## 0.16.19 (2026-11-07, test build)

The changelog comes with every release now, and the Start menu opens it. From a tester's report. The four other reports of that night (injured reserve, the safeties and linebackers, the returners in trades, one whistle) were already fixed in 0.16.18; everything of 0.16.18 and earlier below is still to be tested too.

### The changelog in every release, and in the Start menu
From a tester's report (GitHub issue 5): "A change log needs to be included with every release so we know what to test for and what has been changed." Every release on GitHub now has, beside the installer, a file CHANGELOG-<version>.md: the whole changelog as it stood at that version, every item with how to test it. The release's notes carry that version's own part too. Once the game is installed, the Start menu has a new entry, "NFL Football 4 changelog, what is new", which opens this file in Notepad.

**How to test:** open the newest release on the Releases page: below its notes, the assets should list CHANGELOG-<version>.md beside the installer; download it and read it. Install the game, open the Start menu, type "NFL Football 4 changelog" and press Enter: Notepad should open this changelog, with the installed version's section at the top.

**Tell us:** if a release has no changelog file, or the Start menu entry opens nothing.

## 0.16.18 (2026-11-06, test build)

Injured reserve in the Franchise, every position on its own in the Franchise menus, returners you can trade, and one whistle. From a tester's e-mail. Everything of 0.16.17 and earlier below is still to be tested too.

### Injured reserve, designations to return and activations
The Franchise has injured reserve now, by the NFL's rules. F9, Franchise, injured reserve is the item after the injury report. A hurt player you put on injured reserve leaves your 53, so you can sign a free agent in his place, and he must miss at least 4 games. Once he has missed 2 games you can designate him to return, which opens his practice window for 3 weeks; once he has missed 4 games and is healthy you activate him, and he is back on your 53. If your 53 is full you choose who is released first. A man not activated in his window stays on injured reserve for the season, and the week's injury report says so. You have 8 returns in the regular season and 2 more in the play-offs, one man at most twice. Men on the physically unable to perform or non-football injury lists are activated after 4 games with no designation. The computer teams keep their real reserve lists. Saved franchises of older versions open as they were.

**How to test:** in a franchise, play until one of your players is hurt for several weeks (F9, Franchise, injury report names him). Press F9, Franchise, injured reserve, then "put a hurt player on reserve", choose him and press Enter: you should hear that he is on injured reserve and how much room your roster has. Play two weeks, then open "your players on the reserve lists" and press Enter on him: he should be designated to return, with 3 weeks in his window. Play until he has missed 4 games and is healthy, press Enter on him again: he should be back on your roster (F9, Franchise, your roster). Also try "the rules of injured reserve".

**Tell us:** if a step is refused when it should work, what was said.

### Free and strong safeties, and each linebacker, on their own
The trades, the free agents and the practice squad asked for a group ("safeties", "linebackers") and listed all of its men together. Now they ask for one of the 22 real positions, in the order of your roster: free safeties and strong safeties apart, and the strong-side, middle and weak-side linebackers apart (the NFL's and Madden NFL's three: one middle linebacker and two outside), the left and right edge, and so on. Each position lists only its own men.

**How to test:** press F9, Franchise, free agents, then sign a free agent: the menu should list free safeties, strong safeties, strong-side linebackers, middle linebackers and weak-side linebackers as separate items, and each should list only men of that position. Do the same in F9, Franchise, trades, offer one of your players, and in the practice squad's add a free agent.

**Tell us:** if any man is listed at a position that is not his.

### Kick and punt returners can be traded
A man who returned kicks was in no list of the trades, so he could not be offered or asked for. The trades now have the item "kick and punt returners" (the last in their positions' menu), and a returner is in the list of his own position too. You can now also give a man of another position than the one you ask for; the other team still answers by what the trade is worth to it.

**How to test:** press F9, Franchise, trades, then ask a team for a player, choose a team, then "kick and punt returners": you should hear that team's returners. Choose one and offer a player of yours: the other team should answer yes, more, or no.

**Tell us:** if a returner is still missing from a list.

### One whistle
With the N. F. L. rules the game played four different made whistles (short, long, double and triple), and the original game's whistle when the stadium sounds were off. Now every whistle is the one whistle the game made, at time outs, the ends of plays and quarters, flags, the two minute warning, reviews and the final whistle, with the stadium sounds on or off. Your own whistle.wav in the sounds folder replaces it everywhere (whistle2.wav and more join it). The Classic rules keep the original game's whistle. F9, Sounds, Stadium and referee sounds lists 18 sounds now; "put the stadium sounds back" also moves aside old whistle_short, whistle_long, whistle_double and whistle_triple files.

**How to test:** play a game with the N. F. L. rules and listen to the whistles after plays, at a time out (T) and at the end of a quarter: they should all be the same sound. Turn the stadium sounds off (F9, Rules, Stadium sounds) and listen again: still the same whistle. Put your own whistle.wav in the sounds folder (CUSTOMIZE.md says where) and every whistle should be yours.

**Tell us:** if you still hear two different whistles anywhere.

## 0.16.17 (2026-11-06, test build)

Page Up and Page Down now work in the F9 menus. Everything of 0.16.16 and earlier below is still to be tested too.

### Page Up and Page Down in the F9 menus
The help (F5 and F6) always said that Page Up and Page Down move ten items in the F9 menus, but in menus such as Speech settings they only said the current item again; so did the brackets that stand in for them since 0.16.15. Now they move ten items and stop at the first or the last, in every F9 menu and in the pages of text, as they already did in the long lists. F1 in these menus now names Page Up, Page Down, Home and End.

**How to test:** press F9, choose Speech settings. Press Page Down or the close bracket: you should hear the eleventh item. Press it again: the last item, "Save a problem report". Page Up or the open bracket goes back ten, and stops at the first item. Press F1: the help should name Page Up, Page Down, Home and End.

**Tell us:** if any F9 menu or list still ignores one of these keys.

## 0.16.16 (2026-11-06, test build)

Renaming a player now keeps what you type. Everything of 0.16.15 and earlier below is still to be tested too.

### Renaming a player keeps capitals, apostrophes, hyphens and periods
Before, a new name you typed in F9, Franchise, your roster (a player, change his name) came out all in lower case, an apostrophe was said as a strange letter ("thorn") and then left out, and hyphens and periods were dropped too: "Ja'Marr" became "jamarr". Now the name keeps what you typed: capital letters with Shift, apostrophes, hyphens and periods, as in the real names the game already uses (Ja'Marr, Amon-Ra St. Brown). Other characters are still left out, and a name needs at least two letters or digits. The names you type at the start of a Classic season are unchanged.

**How to test:** start or open a franchise, press F9, choose Franchise, then your roster, choose a player and change his name. Type a name with a capital letter, an apostrophe and a hyphen, for example O'Neil-Smith, then Enter. Each character should be said as you type it (the apostrophe as "apostrophe"), the question should say the name as you typed it, and after yes the roster should have it.

**Tell us:** if a character you need in a name is still left out.

## Older versions

The versions before 0.16.16 are in these files, newest first. Each is a markdown file in the `changelog` folder of this repository.

- [0.16.15 to 0.16.15](https://github.com/joshknnd1982/nfl-football-4-audio-game/blob/master/changelog/CHANGELOG-0.16.15-to-0.16.15.md)
- [0.16.14 to 0.16.14](https://github.com/joshknnd1982/nfl-football-4-audio-game/blob/master/changelog/CHANGELOG-0.16.14-to-0.16.14.md)
- [0.16.13 to 0.16.13](https://github.com/joshknnd1982/nfl-football-4-audio-game/blob/master/changelog/CHANGELOG-0.16.13-to-0.16.13.md)
- [0.16.11 to 0.16.12](https://github.com/joshknnd1982/nfl-football-4-audio-game/blob/master/changelog/CHANGELOG-0.16.11-to-0.16.12.md)
- [0.16.10 to 0.16.10](https://github.com/joshknnd1982/nfl-football-4-audio-game/blob/master/changelog/CHANGELOG-0.16.10-to-0.16.10.md)
- [0.16.9 to 0.16.9](https://github.com/joshknnd1982/nfl-football-4-audio-game/blob/master/changelog/CHANGELOG-0.16.9-to-0.16.9.md)
- [0.16.8 to 0.16.8](https://github.com/joshknnd1982/nfl-football-4-audio-game/blob/master/changelog/CHANGELOG-0.16.8-to-0.16.8.md)
- [0.13.0 to 0.16.6](https://github.com/joshknnd1982/nfl-football-4-audio-game/blob/master/changelog/CHANGELOG-0.13.0-to-0.16.6.md)
- [0.9.0 to 0.12.1](https://github.com/joshknnd1982/nfl-football-4-audio-game/blob/master/changelog/CHANGELOG-0.9.0-to-0.12.1.md)
