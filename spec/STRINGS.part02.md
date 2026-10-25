## MENU-AND-EXIT-TEXT (21)

Main menu, welcome, week announcements, exit and error text (p_486990, the start-up and main flow). Includes the original title strings that rule 0.5.1 replaces.

- `2551` @0x1a1d4 [486990]: " NFL football  By Jim Kitchen "
- `2552` @0x1a248 [486990]: "football.sav"
- `2553` @0x1a268 [486990]: "football.vol"
- `2554` @0x1a288 [486990]: " Welcome to "
- `2555` @0x1a2a8 [486990]: " 2. see schedule "
- `2556` @0x1a2d0 [486990]: " Jim's N. F. L. Football, version 4. "
- `2557` @0x1a320 [486990]: "\\footballlog.txt"
- `2558` @0x1a348 [486990]: "NFL football  By Jim Kitchen"
- `2559` @0x1a388 [486990]: " This is the "
- `2560` @0x1a3b0 [486990]: " of Jim's N. F. L. football "
- `2561` @0x1a3f0 [486990]: " This is week "
- `2562` @0x1a414 [486990]: " This is week #"
- `2563` @0x1a438 [486990]: " Today's game is "
- `2564` @0x1a460 [486990]: " 1. play game "
- `2565` @0x1a484 [486990]: " 3. see standings "
- `2566` @0x1a4b0 [486990]: " 4. exit game "
- `2567` @0x1a4ec [486990]: " Thank you for playing N. F. L. football version 4 By Jim Kitchen "
- `2569` @0x1a5f4 [486990]: "Please contact Jim Kitchen"
- `2570` @0x1a630 [486990]: "Sorry but I couldn't find any voices to use"
- `2571` @0x1a68c [486990]: "gamemenu.exe"
- `2572` @0x1a6ac [486990]: "Sorry, but I could not find the Kitchensinc game menu program."

## ERROR-MESSAGE (1)

The wave-corrupt error text "Sorry but one or more of the wave files seem to be corrupt" (a length-prefixed text with no leading or trailing space). DEAD STRING (S4.4, scripted scan of the whole 581,632-byte exe for the address of its characters 0x41a578, its length prefix 0x41a574 and the two neighbors: no reference anywhere; P3 read all 64 procedures and found none either). The game reuses the sentence as the one spoken notice when a sound file cannot be used (spec/SOUND_DESIGN.md 5, GAP_REGISTER G-A6). [CODE]

- `2568` @0x1a578 []: "Sorry but one or more of the wave files seem to be corrupt"

## HELP-INSTRUCTIONS (27)

Game and football instructions: the same text as football.txt lines 3 to 20 (p_420040, F6 key and first start). Identical to the readme, line for line.

- `628` @0x03978 [420040]: "Game instructions."
- `629` @0x039ac [420040]: "Finally you will be asked to choose which team you will be for the season and then it is time to play."
- `630` @0x03a80 [420040]: "You will first be asked to choose the voices for the announcer, your quarterback, your opponents quarterback, your punter and your opponents punter."
- `631` @0x03bb0 [420040]: "You will then be asked to enter the name of your coach."
- `633` @0x03c68 [420040]: "Football instructions."
- `634` @0x03c9c [420040]: "The object of the game of football is to score more points than your opponent."
- `635` @0x03d40 [420040]: "There are several ways to score points."
- `636` @0x03d94 [420040]: "One way is to run or pass the ball over your opponents goal line."
- `638` @0x03e50 [420040]: "This is called a touchdown and is worth six points."
- `639` @0x03ebc [420040]: "After a touchdown you are given the choice of going for the extra point kick or a two point conversion."
- `640` @0x03f90 [420040]: "In both cases you start on your opponents two yard line."
- `642` @0x0403c [420040]: "The extra point kick you simply kick the ball through your opponents goal post."
- `643` @0x040e0 [420040]: "For the two point conversion you must run or pass the ball over your opponents goal line."
- `644` @0x04198 [420040]: "The longest field goal ever kicked was sixty one yards."
- `646` @0x0422c [420040]: "Another way to score points is called a field goal, which is when you kick the ball through your opponents goal post."
- `647` @0x0431c [420040]: "It is worth three points."
- `648` @0x04354 [420040]: "So you will want to add seventeen yards when figuring the distance for kicking a field goal."
- `649` @0x04414 [420040]: "You should remember that the goal post is located at the back of the end zone, which is ten yards deep."
- `650` @0x044e8 [420040]: "Also when you set up to kick a field goal you set the ball down seven yards back from the yard line that you are on."
- `652` @0x04600 [420040]: "The last way to score points is worth two points and is called a safety."
- `653` @0x04698 [420040]: "You score a safety by tackling your opponent in his own end zone."
- `657` @0x047e0 [420040]: "The game of football has four quarters of fifteen minutes each.  Or in this game twenty five to thirty five plays each quarter."
- `662` @0x049bc [420040]: "You will get a two minute warning before the end of the second and fourth quarter.  After the two minute warning there will be approximately five plays before the quarter ends."
- `665` @0x04bac [420040]: "The football field is one hundred yards long.  There are lines every ten yards and they are labeled, ten twenty thirty forty fifty, forty thirty twenty and ten."
- `666` @0x04cf4 [420040]: "The game begins with the kick off.  As does the second half or third quarter."
- `667` @0x04d94 [420040]: "Depending on who wins the coin toss, you or your opponent will catch the kick off in your own end zone.  You then decide wether to run the ball out or down it in the end zone.  If you down it in the end zone you will then begin on your own twenty yard line.  If you win the coin toss and receive the kick off you are now the offensive team and you try to move the ball by running or passing it down the field towards your opponents goal line.  As you try to move the ball down the field you get four downs or plays to move the ball ten yards.  If you do so, it is called a first down and you get four new downs to move the ball another ten yards.  If it is fourth down you would be advised to punt (kick) the ball away to your opponent, because if you do not and you do not make enough yards on fourth down to get a first down the ball is turned over to your opponent at that point on the field."
- `668` @0x05498 [420040]: "There are sixteen games in the regular season of football.  If you have the best record of all of the teams in your division, you move on to the play offs.  There are also four wild card teams that make it into the play offs.  The wild card teams are the two teams with the best records in the A. F. C. that did not win their division, as well as the two teams with the best records in the N. F. C. that did not win their divisions.  If you make it into the play offs, you hopefully win until you win the A. F. C. or N. F. C. championship game.  The last game is the Super Bowl game where the A. F. C. champion plays the N. F. C. champion for that seasons championship title."

## HELP-KEYS (13)

Special key instructions: the F1 to F12 and Escape list (p_420860, F5 key). Words are spelled for speech ("reed" for read).

- `654` @0x04720 [420860]: "F6. reed Game instructions. "
- `655` @0x04760 [420860]: "f7. football terminology And hints. "
- `656` @0x047b0 [420860]: "f8. comments toggle. "
- `658` @0x048e4 [420860]: "F2. instant replay. "
- `659` @0x04914 [420860]: "F3. say score. "
- `660` @0x04938 [420860]: "F4. announce game clock. "
- `661` @0x04970 [420860]: "F5. reed special key instructions. "
- `663` @0x04b24 [420860]: "Special key instructions. "
- `664` @0x04b60 [420860]: "F1. repeat current prompt. "
- `669` @0x059e4 [420860]: "F11. adjust volume of voices and sounds. "
- `670` @0x05a3c [420860]: "F12. change voice. "
- `671` @0x05a68 [420860]: "Control key, adjust rate of speech. "
- `672` @0x05ab8 [420860]: "escape key, exit game. "

## HELP-TERMS-AND-PLAYS (63)

Football terminology (a dictionary, A to W) and the explanations of the plays (p_420b50, F7 key): same text as football.txt. One difference: the blitz explanation ends with "...a very long gain on the " in the exe (the string stops after "the "), but the readme file has "play." at the end.

- `673` @0x05aec [420b50]: "football terminology."
- `674` @0x05b1c [420b50]: "Backfield: The area behind the line of scrimmage."
- `676` @0x05bbc [420b50]: "Backpedal: Backward running to drop into pass coverage."
- `677` @0x05c30 [420b50]: "Blitz: A pass rush involving defensive backs or linebackers."
- `678` @0x05cb0 [420b50]: "Block: An offensive player moves a defensive player away from the ball."
- `680` @0x05dac [420b50]: "Bootleg: A play where the quarterback fakes a handoff and runs around the tight end."
- `681` @0x05e5c [420b50]: "Bump and Run: A pass defense in which the defender bumps the receiver at the line of scrimmage."
- `682` @0x05f20 [420b50]: "Punt: A type of kick used primarily on fourth down."
- `683` @0x05f9c [420b50]: "Center: The middle offensive lineman that snaps the ball to the quarterback."
- `684` @0x0603c [420b50]: "Cornerback: One of two defensive backs positioned on the outside corners of the defense."
- `685` @0x060f4 [420b50]: "Defensive ends: The two players at the end of the defensive line."
- `686` @0x0618c [420b50]: "Defense: The team without the ball. The defense tries to get the ball back and stop the offense from scoring."
- `687` @0x0626c [420b50]: "Defensive backs: The cornerbacks and safeties behind the linebackers."
- `688` @0x062fc [420b50]: "Hashmarks: The short lines used to spot the ball on the field."
- `689` @0x06380 [420b50]: "Down: A play from scrimmage. The offense gets four downs numbered in sequence, first to fourth, to gain 10 yards and make a new first down."
- `690` @0x0649c [420b50]: "Eligible receiver: Any of the five offensive players who are allowed to receive a pass."
- `692` @0x0656c [420b50]: "End zone: The area, 10 yards deep, bounded by the end line, goal line, and both sidelines. A team scores points by moving the ball into their opponent's end zone for a touchdown."
- `693` @0x066d8 [420b50]: "Guards: The two offensive linemen on either side of the center."
- `694` @0x0675c [420b50]: "Extra point: The one- or two-point play allowed a team after scoring a touchdown. "
- `695` @0x06808 [420b50]: "Fair catch: An unhindered catch by the receiver of a punt or kickoff. The returner raises one arm high over his head to signal a fair catch."
- `696` @0x06944 [420b50]: "Forward pass: A ball thrown, usually with an overarm motion, in the direction of the offense's goal line."
- `697` @0x06a1c [420b50]: "Four point stance: A stance with both hands on the ground, often used by defensive linemen."
- `699` @0x06b34 [420b50]: "Fumble: Loss of possession of the football by the ball carrier or passer."
- `700` @0x06bcc [420b50]: "Goal line: The field stripe separating the end zone and the field of play that must be crossed to score a touchdown."
- `701` @0x06cbc [420b50]: "Half: There are two halves to a game."
- `703` @0x06d24 [420b50]: "Halftime: The intermission between the first and second halves of a game. Teams rest and discuss strategy during halftime."
- `704` @0x06e20 [420b50]: "Handoff: A play in which the ball is given to another player, usually from a quarterback to a running back."
- `706` @0x06f18 [420b50]: "Holding: The penalty called for illegal grabbing or use of hands."
- `707` @0x06fa0 [420b50]: "Hole: A space in the offensive line opened by blockers for a ball carrier to run through."
- `708` @0x07058 [420b50]: "Linebacker: A defender who plays between the defensive linemen and the defensive backs."
- `709` @0x0710c [420b50]: "Huddle: A brief gathering for play and signal calling by the offense and defense between plays."
- `710` @0x071d0 [420b50]: "I formation: A backfield formation featuring two running backs in line directly behind the quarterback."
- `711` @0x072a4 [420b50]: "Possession: When a team has the ball."
- `712` @0x072f4 [420b50]: "Interception: A change of possession when a defensive player catches a pass intended for an offensive player."
- `713` @0x073d4 [420b50]: "Lateral: A toss or pass backward from the direction of play."
- `714` @0x07454 [420b50]: "Pocket: The area of protection around a passer formed by his blockers."
- `715` @0x074e8 [420b50]: "Line of scrimmage: The imaginary line running from sideline to sideline on which the ball is snapped. It moves up and down the field with the ball."
- `716` @0x07614 [420b50]: "Man for man: A pass defense where each defender covers one receiver."
- `718` @0x076dc [420b50]: "Nose tackle: The defensive tackle in a 3-4 alignment who lines up opposite the center."
- `719` @0x07790 [420b50]: "Offense: The team that has the ball and is trying to score."
- `720` @0x0780c [420b50]: "Pass rush A play in which defenders try to sack the passer."
- `722` @0x078c8 [420b50]: "Penalty: A call made by the game official when a player breaks a rule. Apenalty may result in a loss of yardage or a down."
- `723` @0x079c4 [420b50]: "Play action: pass A play in which the quarterback fakes a running play, then passes."
- `725` @0x07ab8 [420b50]: "Quarter: There are four quarters in a game, two in each half."
- `726` @0x07b38 [420b50]: "Quarterback The player who leads the offense, calls plays, hands off the ball, runs with the ball, or passes it."
- `727` @0x07c20 [420b50]: "Set: When an offensive player gets into his stance."
- `729` @0x07ca0 [420b50]: "Rollout: When the quarterback leaves the pocket, following blockers, to throw a pass."
- `730` @0x07d50 [420b50]: "Running backs: The players who are the main ball carriers."
- `731` @0x07dcc [420b50]: "Sack: When the quarterback is tackled in the backfield while attempting to pass."
- `733` @0x07e88 [420b50]: "Sidelines: The lines running the length of the field, from end line to end line, marking the outside boundaries of the field and end zones. The sideline is out of bounds."
- `734` @0x07fe4 [420b50]: "Snap: When the center passes the ball to the quarterback to start a play."
- `735` @0x08080 [420b50]: "Snap count: The signal on which the ball is snapped."
- `736` @0x080f0 [420b50]: "Three point stance: A stance used by offensive and defensive linemen and running backs in which one hand is touching the ground."
- `739` @0x08264 [420b50]: "Tight end: A receiver/blocker position outside the offensive tackle."
- `740` @0x082f4 [420b50]: "Time out: When a team or an official stops action and the clock."
- `746` @0x0843c [420b50]: "Touchdown: A six-point scoring play that occurs when one team crosses the other team's goal line with the ball in its possession."
- `747` @0x08544 [420b50]: "Wide receiver: A pass receiver who is set outside the offensive tackle."
- `748` @0x085d8 [420b50]: "In Jim's NFL football game."
- `750` @0x0862c [420b50]: "A running play is where the quarterback takes the hike and hands the ball off to a running back.  The running back then either runs straight towards the line looking for a hole to run through that hopefully the offensive line has created by blocking the defensive line out of the way.  The other running play the running back runs toward the side line and then tries to turn and head up field.  Again his success depends on if the defenders are fooled or blocked so that they are not there to tackle him."
- `751` @0x08a24 [420b50]: "The line plunge is also a running play that is designed to try to get short yardage.  Like if you are a yard or so from the goal line or need a yard or so for a first down.  The running back runs straight towards the line.  It often results in all of the players from both teams in a pile at the line of scrimmage.  However depending on which play the defense calls it may result in a gain of many yards."
- `752` @0x08d54 [420b50]: "A pass or passing play is where the quarterback takes the snap and fades back looking for an open receiver to throw the ball to.  A short pass is usually easier to complete than a long one."
- `755` @0x08f38 [420b50]: "The screen pass play is a passing play where the quarterback throws the ball to a running back or receiver that is behind the line of scrimmage out towards the side line.  That player then tries to run up field.  If the defense detects the play he can be tackled behind the line of scrimmage for a loss.  But if they are fooled he may be able to run for a very good gain on the play."
- `756` @0x0923c [420b50]: "On defense the blitz play is where the defensive team sends a couple of extra players at the line in hopes of getting to the quarterback before he can get the pass off or perhaps to tackle the running back before he can get running good.  So it can be a good play to call if it works, however if the quarterback can get the pass off the extra defenders that were doing the blitz are no longer down field to try to stop the receiver from catching the ball or running with it after he catches it.  So if the blitz doesn't work the offence may end up with a very long gain on the "

## VOLUME-PROMPT (15)

Volume setting dialogue (F11): voices and sounds, up and down arrow keys, Enter to finish (p_421960; the volume file name football.vol is also here).

- `679` @0x05d44 [421960]: " Press the up arrow key to raise the volume of "
- `698` @0x06ad8 [421960]: " or the down arrow key to lower it."
- `737` @0x081f8 [421960]: "your opponents punter"
- `742` @0x0839c [421960]: "the announcer"
- `743` @0x083bc [421960]: "your quarterback"
- `744` @0x083e4 [421960]: "your punter"
- `745` @0x08400 [421960]: "your opponents quarterback"
- `757` @0x096c4 [421960]: " Press the enter key when the volume is set the way that you want it. "
- `758` @0x0977c [421960]: " volume maximum "
- `759` @0x097a4 [421960]: " volume higher "
- `760` @0x097c8 [421960]: " volume minimum "
- `761` @0x097f0 [421960]: " volume lower "
- `762` @0x09814 [421960]: " press the up arrow key to raise the volume of the sounds"
- `763` @0x0989c [421960]: " or press the down arrow key to lower them. "
- `764` @0x098fc [421960]: " Press the enter key when you have them set the way that you want them. "

## COMMENTS-TOGGLE (3)

F8 comments toggle messages (comments = the announcer banter).

- `741` @0x0837c [4216b0,421960,486990]: "\\football.vol"
- `753` @0x08ed4 [4216b0]: " comments toggle off "
- `754` @0x08f04 [4216b0]: " comments toggle, ON! "

## RATE-PROMPT (1)

Speech rate setting (Ctrl): arrow keys then Enter.

- `765` @0x099c0 [423530]: "to adjust the speech rate, use the arrow keys and then press enter"

## VOICE-CHOICE-PROMPT (7)

Voice choice prompts for the five roles (announcer, own quarterback, opponent quarterback, own punter, opponent punter) and the words around them (p_4239c0). The string ' AT&T ' is compared with voice names (AT&T Natural Voices handling), role to confirm in P3.

- `717` @0x076a4 [4239c0]: " for your quarter back? "
- `721` @0x07888 [4239c0]: " for the announcer?"
- `724` @0x07a74 [4239c0]: " Do you wish to use "
- `766` @0x09a78 [4239c0]: " for your opponent's quarter back? "
- `767` @0x09ac4 [4239c0]: " for your punter? "
- `768` @0x09af0 [4239c0]: " for your opponent's punter? "
- `769` @0x09b3c [4239c0]: " AT&T "

## TEAM-CHOICE-PROMPT (3)

ChooseTeam (p_4308e0, new season): " <coach> choose your team " (say2), then each team name alone while Up and Down step; Enter: " <coach> your team is the <team>. Is this correct? " and yes or no. [CODE (lifted, S3.3)]

- `789` @0x09fbc [4308e0]: " choose your team "
- `790` @0x09fe8 [4308e0]: " your team is the "
- `791` @0x0a014 [4308e0]: ". Is this correct? "

## COACH-PROMPT (2)

GetCoach (p_4311a0, new season): prompt " Enter the name of your coach " (say5 through getter), then say5 " is, <coach>, correct for the name of your coach? " (the part " is, " is shared with Getqbs) and the answers " yes " and " no " (say2). [CODE (lifted, S3.3)]

- `792` @0x0a040 [4311a0]: " Enter the name of your coach "
- `793` @0x0a094 [4311a0]: ", correct for the name of your coach? "

## QB-NAME-PROMPT (7)

Getqbs (p_4314d0, once per game): own quarterback " <coach> enter the name of your quarter back or press enter " (getter, say5), confirmation " is, <name>, correct for the name of your quarter back? " (say5, then yes or no with say2); opponent " enter the name of the <team> quarter back or press enter " and " is, <name>, correct for the name of the <team> quarter back? ". 'Quarterback:' is the heading written after the player names in footplay.txt. An empty answer draws a random unused surname. [CODE (lifted, S3.3)]

- `794` @0x0a0f0 [4314d0]: " enter the name of your quarter back or press enter "
- `796` @0x0a188 [4314d0]: ", correct for the name of your quarter back? "
- `797` @0x0a1e8 [4314d0]: "Quarterback:"
- `798` @0x0a208 [4314d0]: " enter the name of the "
- `799` @0x0a23c [4314d0]: " quarter back or press enter "
- `800` @0x0a27c [4314d0]: ", correct for the name of the "
- `801` @0x0a2c0 [4314d0]: " quarter back? "

## SCORE-SPEECH (2)

SayScore (p_42b590) " The score is " and SayFinalScore (p_42bab0) " The Final score is", each followed by the sentence of the numbers: "<leader>. <n>. <other>. <n>" or " tied <n> all" (built in code, the team names come from TEAM-NAME). [CODE (lifted, S3.3)]

- `770` @0x09b68 [42b590]: " The score is "
- `771` @0x09bdc [42bab0]: " The Final score is"

## CLOCK-SPEECH (7)

sgc (p_42bfc0, F4 and quarter starts): " <m> minute(s) <s> second(s) remaining in the <first|second|third|fourth|over time> quarter. " (the quarter names are built in a local array: 1 to 4, 5 to 10 'over time'). [CODE (lifted, S3.3)]

- `675` @0x05b84 [42bfc0]: " remaining in the "
- `705` @0x06efc [42bfc0]: " quarter. "
- `728` @0x07c8c [42bfc0]: " minute"
- `732` @0x07e74 [42bfc0,43a860]: " second"
- `738` @0x08248 [42bfc0]: "fourth"
- `749` @0x08614 [42bfc0]: "over time"
- `772` @0x09c18 [42bfc0]: "second"

## STANDINGS-SPEECH (2)

SayStand (p_42ce40): " Standings after week number <n> " (S5.2 correction: exactly " Standings after week number " & Trim$(Str$(n)), no space before or after the number, SayStand 0x42d62d), the division name (DIVISION-NAME), then for each team " <team> <wins>, and <losses>. " (sorted by fewest losses). [CODE (lifted, S3.3)]

- `778` @0x09cf4 [42ce40]: " Standings after week number "
- `779` @0x09d34 [42ce40]: ", and "

## SCHEDULE-SPEECH (10)

SayScedual (p_42eba0, main menu choice 2): " <team> schedual. ", then per week " game number <n>" and " <first team> verses the <second team>" (flag 1: opponent first, 2: own team first); in week 1 " <coach> do you like this schedual? yes " (say5) and yes or no; from week 17 " games for the <week name> are. " and " the <team> verses the <team>. " per game. The four play-off week names ("Wild card play off week", "division play off week", "division championship play off week", "super bowl week") are also used by Form_Load. [CODE (lifted, S3.3)]

- `645` @0x0420c [42eba0]: " game number "
- `691` @0x06550 [42eba0]: " schedual. "
- `780` @0x09dec [42eba0,486990]: " verses the "
- `781` @0x09e0c [42eba0]: " do you like this schedual? yes "
- `782` @0x09e5c [42eba0]: " games for the "
- `783` @0x09e80 [42eba0,486990]: "Wild card play off week"
- `784` @0x09eb4 [42eba0,486990]: "division play off week"
- `785` @0x09ee8 [42eba0,486990]: "division championship play off week"
- `786` @0x09f34 [42eba0,486990]: "super bowl week"
- `787` @0x09f58 [42eba0]: " are. "

## SEASON-RESULTS-SPEECH (14)

Texts of the season engine pog (p_4615b0, read in S3.6; GAME_SPEC 5.14 to 5.16). Regular week (say2, asynchronous, logged): " Games of week number " + the week (Trim$) + ". ", then for the player's game and the 15 other games "<winner> over the <loser> by the score of <w>, to <l>. " (no "The" in front, Trim$ numbers; the pieces " over the ", " by the score of ", ", to ", ". "). After week 16 (say4, logged, replay list): " the division winners are. ", each division name and "<team>. at <wins> and <losses>. " (". at ", " and ", ". "), " the A. F. C. wild card teams are. ", " the N. F. C. wild card teams are. " with two teams each, and for a team out of the play-offs " The <team> at <wins> and <losses>. did not make it into the playoffs. " (" The ", " at ", Str$ numbers). Play-off results (say4): the headings " In the A. F. C. wild card games. ", " In the N. F. C. wild card games. ", " In the A. F. C. division play off games. ", " In the N. F. C. division play off games. ", " In the A. F. C. championship  game. " (two spaces), " In the N. F. C. championship game. ", and per game " The <winner> won over the <loser> by the score of <w> to <l>. " (" won over the ", " to", Str$ numbers). Slips of the original: some results lose " The " or are never spoken (Q46, not reproduced, D-029); the headings of pog and finplay17 differ in capitals and spaces (Q47, kept). [CODE (lifted, S3.6)]

- `2529` @0x19af0 [4615b0]: " Games of week number "
- `2530` @0x19b24 [4615b0]: " over the "
- `2531` @0x19b40 [4615b0,47d8b0,484860]: " by the score of "
- `2532` @0x19b78 [4615b0]: " the division winners are. "
- `2533` @0x19bb4 [4615b0]: " the A. F. C. wild card teams are. "
- `2534` @0x19c00 [4615b0]: " the N. F. C. wild card teams are. "
- `2535` @0x19c6c [4615b0]: " did not make it into the playoffs. "
- `2536` @0x19cbc [4615b0,47d8b0]: " In the A. F. C. wild card games. "
- `2537` @0x19d08 [4615b0,47d8b0]: " won over the "
- `2538` @0x19d38 [4615b0,47d8b0]: " In the N. F. C. wild card games. "
- `2539` @0x19d84 [4615b0]: " In the A. F. C. division play off games. "
- `2540` @0x19de0 [4615b0,47d8b0]: " In the N. F. C. division play off games. "
- `2541` @0x19e3c [4615b0]: " In the A. F. C. championship  game. "
- `2542` @0x19e8c [4615b0]: " In the N. F. C. championship game. "

## PLAYOFF-RESULTS-SPEECH (4)

Headings only used by the play-off engine finplay17 (p_47d8b0, read in S3.6; GAME_SPEC 5.17), which plays the rounds without the player: " In the A. F. C. Division play off games. " (capital D, unlike pog's), " In the A. F. C. Championship game. ", " In the N. F. C. Championship game. " (capital C), " In the Super Bowl. "; finplay17 also speaks the wild card headings and " In the N. F. C. division play off games. " of class SEASON-RESULTS-SPEECH and one say4 per game " The <winner> won over the <loser> by the score of <w> to <l>. ". [CODE (lifted, S3.6)]

- `2543` @0x19fc0 [47d8b0]: " In the A. F. C. Division play off games. "
- `2544` @0x1a01c [47d8b0]: " In the A. F. C. Championship game. "
- `2545` @0x1a06c [47d8b0]: " In the N. F. C. Championship game. "
- `2546` @0x1a0bc [47d8b0]: " In the Super Bowl. "

## SUPERBOWL-SPEECH (2)

superbowl (p_484860): " The <winner> have Won the super Bowl! " + " They beat the <loser>" + " by the score of <a>, to <b>. " (say4), with celebration sounds (and foot25 when the player won); F1 or F2 repeat it. [CODE (lifted, S3.4)]

- `2547` @0x1a0ec [484860]: " have Won the super Bowl! "
- `2548` @0x1a128 [484860]: " They beat the "

## REPLAY-PROMPT (2)

'select your play' and the instant replay announcement (p_4863f0).

- `2549` @0x1a158 [4863f0]: " select your play "
- `2550` @0x1a184 [4863f0]: " here's the instant rea play "

## SNAP-CALL (6)

The snap count. Plays (pag 0x440126 to 0x440d71): " the <team> break the huddle " (1 in 10: " come to the line without a huddle "), "<quarterback> is up to the line / is under center / barks out the snap count / is in the shot gun " (say5), then in the quarterback's voice (say3): " hut 1 ", " hut 2 " (1 in 7), up to two calls of a snap-count word and a number 1 to 28 (" Blue  17", words in Me.m3dc), 0 to 3 times " hut" or " hut!", and " Hike! " (asynchronous). Kicks (kicksnap p_43a330, the punter voice): " hut 1 ", " hut 2 " (2 in 3), " hut 3 " (1 in 2 of those), 1 to 3 times " hut" or " hut!", " hike! ". [CODE (lifted, S3.4)] The ten snap-count words Me.m3dc are set in pag's set-up (0x4585ca): " Red ", " Right ", " Blue ", " Left ", " white ", " black ", " green ", " chrome ", " X ", " XP " (the pool files " Right " and " chrome " in this class, the other words are short strings in SPEECH-FRAGMENT or here). [CODE (lifted, S3.5)]

- `2065` @0x12c2c [43a330,43a860]: " hut 1 "
- `2066` @0x12c40 [43a330,43a860]: " hut 2 "
- `2067` @0x12c54 [43a330]: " hut 3 "
- `2068` @0x12c80 [43a330]: " hike! "
- `2268` @0x153d4 [43a860]: " Right "
- `2309` @0x15b18 [43a860]: " chrome "

## SAVED-GAME (2)

" getting saved game " (say) when pag starts with a saved game; football.sav is read and deleted. [CODE (lifted, S3.4)]

- `2069` @0x12c94 [43a860]: " getting saved game "
- `2070` @0x12cc4 [43a860,486990]: "\\football.sav"

## COIN-TOSS (12)

Coin toss (pag 0x43bb83 to 0x43cc63): the player calls when vtrnt is 2: " <coach> Which do you call for the coin toss " and the answer " heads " or " tails " (say2; Up, Down, h, t change it, Enter takes it, F1 starts again); the computer calls when vtrnt is 1: " the <opponent> call heads " or "tails " (say4, random). Then " here is the coin toss ", " the coin comes up heads " or "tails " (say4). The winner: the player chooses " <coach> which do you wish to do " with " receive " or " kick off " (say2; Up, Down, r, k, Enter, F1); the computer always says " the <opponent> choose to receive ". The calls are written to the log. [CODE (lifted, S3.4)]

- `2071` @0x12cec [43a860]: " Which do you call for the coin toss "
- `2072` @0x12d3c [43a860]: " heads "
- `2073` @0x12d50 [43a860]: " tails "
- `2074` @0x12d64 [43a860]: " call "
- `2075` @0x12d78 [43a860]: "heads "
- `2076` @0x12d8c [43a860]: "tails "
- `2077` @0x12db0 [43a860]: " here is the coin toss "
- `2078` @0x12de4 [43a860]: " the coin comes up "
- `2079` @0x12e10 [43a860]: " choose to receive "
- `2080` @0x12e3c [43a860]: " which do you wish to do "
- `2081` @0x12e74 [43a860]: " receive "
- `2082` @0x12e8c [43a860]: " kick off "

## QUARTER-MARKER (4)

" End of the First Quarter", " End of the Second Quarter", " End of the Third Quarter" (say4, after the whistle foot11), " Two Minute Warning" (say4, then foot11) in quarters 2 and 4 and in every overtime, when the play counter equals the plays of the quarter minus M2W, M4W or M5W. [CODE (lifted, S3.4)]

- `2083` @0x12eb8 [43a860]: " End of the First Quarter"
- `2084` @0x12ef0 [43a860]: " Two Minute Warning"
- `2085` @0x12f1c [43a860]: " End of the Second Quarter"
- `2086` @0x12f58 [43a860]: " End of the Third Quarter"

## PLAY-PROMPT (4)

" <coach> select the play for your off fence " and " <coach> select the play for your dee fence " (say5, spelled for speech), followed by the current menu item (PLAY-MENU); " <coach> select " with " kick for extra point " / " try for two point conversion " after the player's touchdown; " Do you wish to quit and concede this game? no " after Esc (yes, no; foot13 bleeps first). [CODE (lifted, S3.4)]

- `2087` @0x12f98 [43a860]: " green "
- `2088` @0x12fb0 [43a860]: " select the play for your off fence "
- `2089` @0x13024 [43a860]: " select the play for your dee fence "
- `2528` @0x199e4 [43a860]: " Do you wish to quit and concede this game? no "

## SNAP-PHRASE (22)

After the hike, "<quarterback>" and one of 13 phrases (" takes the snap", " has the ball", " handles the snap", " takes the snap from center", " takes the ball", " has the snap", " gets the snap", " gets the ball", " gets the ball from center", " handles the snap from center", " gets the snap from center", " takes the ball from center", " has the snap from center"; never one of the last six used) (say4). [CODE (lifted, S3.4)]

- `2090` @0x13074 [43a860]: " is up to the line "
- `2091` @0x130a0 [43a860]: " is under center "
- `2092` @0x130c8 [43a860]: " barks out the snap count "
- `2093` @0x13104 [43a860]: " is in the shot gun "
- `2094` @0x13134 [43a860]: " come to the line without a huddle "
- `2095` @0x13180 [43a860]: " break the huddle "
- `2096` @0x131ac [43a860]: " Hike! "
- `2097` @0x131c0 [43a860]: " tackle string "
- `2098` @0x131e4 [43a860]: " takes the snap"
- `2099` @0x13208 [43a860]: " has the ball"
- `2100` @0x13228 [43a860]: " handles the snap"
- `2101` @0x13250 [43a860]: " takes the snap from center"
- `2102` @0x1328c [43a860]: " takes the ball"
- `2103` @0x132b0 [43a860]: " has the snap"
- `2104` @0x132d0 [43a860]: " gets the snap"
- `2105` @0x132f4 [43a860]: " gets the ball"
- `2106` @0x13318 [43a860]: " the hold is good"
- `2107` @0x1334c [43a860]: " gets the ball from center"
- `2108` @0x13388 [43a860]: " handles the snap from center"
- `2109` @0x133c8 [43a860]: " gets the snap from center"
- `2110` @0x13404 [43a860]: " takes the ball from center"
- `2111` @0x13440 [43a860]: " has the snap from center"

## FIELD-GOAL-PHRASE (16)

Field goal (pag 0x441dfa): " <kicker> is in for the field goal attempt ", " <holder> will hold ", kicksnap, " the snap is good ", " the hold is good", " the kick is up and it " (say4), then " is good", one of " is wide left", " is wide right", " hits the left upright", " hits the right upright", " hits the cross bar", " falls short" (missed), or " is way to short" (the player kicking from his own half). The extra point uses the same pieces with " is in for the extra point attempt " and always " is good for the extra point ". [CODE (lifted, S3.4)]

- `2112` @0x13478 [43a860]: " is in for the field goal attempt "
- `2113` @0x134c4 [43a860]: " will hold "
- `2114` @0x134e0 [43a860]: " the snap is good "
- `2115` @0x1350c [43a860]: " black "
- `2116` @0x13520 [43a860]: " the kick is up and it "
- `2117` @0x13554 [43a860]: " is way to short"
- `2118` @0x1357c [43a860]: " is good"
- `2119` @0x13594 [43a860]: " is wide left"
- `2120` @0x135b4 [43a860]: " is wide right"
- `2121` @0x135d8 [43a860]: " hits the left upright"
- `2122` @0x1360c [43a860]: " hits the right upright"
- `2123` @0x13640 [43a860]: " hits the cross bar"
- `2124` @0x1366c [43a860]: " falls short"
- `2125` @0x1368c [43a860]: " it's "
- `2126` @0x136b0 [43a860]: "yards in the air"
- `2127` @0x136d8 [43a860]: " Left "

## PUNT-AND-KICKOFF-PHRASE (39)

Punt (pag 0x442ebe): " <st1> and <st2> are back deep to receive the punt ", " <punter> is ready to take the snap and  kick the punt ", "<punter> takes the long snap", "<He|She>gets the kick off ", " it's a.  pooch kick" (under 40 yards) / " pretty good kick" (40 to 49) / " high booming kick" (50 to 59), " it travels <n>yards in the air", then " <returner> calls for a fair catch ", " the ball hits and bounces out of bounds " or " the ball is downed by <receiver> " (1 in 3 each), " IT IS A TOUCH BACK" past the goal line. Kick-off (0x444645): " <st1> and <st2> are back deep to receive the kick off ", "<kicker>  is ready to kick off ", " The kick off is up and is headed for the end zone", "<returner> catches the ball <1 to 7> yard(s) deep in the end zone "; the player answers " <coach> do you wish for <returner> to run the ball out " (yes, no); " he downs the ball in the end zone for a touch back"; a return: one of five run descriptions (" he is running left he turns and runs right ..."), the yard calls " <returner> is at the 5", " the 10", " the 15", " the 20", " 25" ... " 45", " he is still running there is one man to beat", and " He is cut down by" / " He is tackled by" / " He is finally tackled by" with one or two defenders. [CODE (lifted, S3.4)]

- `2128` @0x136ec [43a860]: " are back deep to receive the punt "
- `2129` @0x13738 [43a860]: " is ready to take the snap and "
- `2130` @0x1377c [43a860]: " kick the punt "
- `2131` @0x137a0 [43a860]: " takes the long snap"
- `2132` @0x137d0 [43a860]: "gets the kick off "
- `2133` @0x137fc [43a860]: " it's a. "
- `2134` @0x13814 [43a860]: " pooch kick"
- `2135` @0x13830 [43a860]: " pretty good kick"
- `2136` @0x13858 [43a860]: " high booming kick"
- `2137` @0x13884 [43a860]: " it travels"
- `2138` @0x138a0 [43a860]: " white "
- `2139` @0x138b4 [43a860]: " calls for a fair catch "
- `2140` @0x138ec [43a860]: " the ball hits and bounces out of bounds "
- `2141` @0x13944 [43a860]: " the ball is downed by "
- `2142` @0x13978 [43a860]: " in the end zone for a safety"
- `2143` @0x139b8 [43a860]: " are back deep to receive the kick off "
- `2144` @0x13a0c [43a860]: "  is ready to kick off "
- `2145` @0x13a40 [43a860]: " He is finally tackled by"
- `2146` @0x13a78 [43a860]: "ball on"
- `2147` @0x13a8c [43a860]: " The kick off is up and is headed for the end zone"
- `2148` @0x13af8 [43a860]: " catches the ball"
- `2149` @0x13b3c [43a860]: "deep in the end zone "
- `2150` @0x13b6c [43a860]: " do you wish for "
- `2151` @0x13b94 [43a860]: " to run the ball out "
- `2152` @0x13bc4 [43a860]: " he is running left he turns and runs right now he is running left again"
- `2153` @0x13c5c [43a860]: " He is running left he cuts right he cuts back to the left"
- `2154` @0x13cd8 [43a860]: " He lookes left then lookes right and heads for the middle of the field"
- `2155` @0x13d6c [43a860]: " He starts left then changes direction and heads up the right side line"
- `2156` @0x13e00 [43a860]: " He is tackled by"
- `2157` @0x13e38 [43a860]: " He starts right then changes direction and heads up the left side line"
- `2158` @0x13ecc [43a860]: " is at the 5"
- `2159` @0x13eec [43a860]: " the 10"
- `2160` @0x13f00 [43a860]: " the 15"
- `2161` @0x13f14 [43a860]: " the 20"
- `2162` @0x13f64 [43a860]: " he is still running there is one man to beat"
- `2163` @0x13fc4 [43a860]: " He is cut down by"
- `2164` @0x13ff0 [43a860]: " Blue "
- `2165` @0x14004 [43a860]: " he downs the ball in the end zone for a touch back"
- `2166` @0x14070 [43a860]: " It's "

