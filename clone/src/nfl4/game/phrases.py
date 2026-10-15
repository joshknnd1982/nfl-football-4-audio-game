"""The play-by-play texts of the game and the histories that keep a phrase from coming back too soon. This is inspired by Jim Kitchen.

GAME_SPEC 5.8 to 5.11 and STRINGS.md (CODE (lifted) pag p_43a860; every text is copied from the lifted line named next
to it and checked against spec/strings_all.tsv by tests/test_phrases.py). The texts keep the original's spaces and
spellings exactly ("second airy", "lookes", "drops back  to pass" with two spaces); the sentences are joined from these
pieces in the engine as the original joins them, names and Str$ numbers in between.

A phrase history is the original's small array of the last values drawn (the snap phrase keeps 6, the sack 4, the throw
4, the incompletion 6, the catch 6, the hand-off 16, the drop-back 16): a draw that equals one of them is drawn again,
then the oldest drops out and the new value is entered last. The arrays start Empty, which equals no phrase number. The
histories live for one game and are not saved (Q37).
"""
from __future__ import annotations

from typing import Callable

from .rnd import GameRandom

# ----- the snap (5.8) -----
QB_LINE = (" is up to the line ", " is under center ", " barks out the snap count ", " is in the shot gun ")   # 0x43fece..
HUDDLE_BROKEN = " break the huddle "                                       # 0x440110 (9 in 10)
NO_HUDDLE = " come to the line without a huddle "                          # 0x4400ee (Int(Rnd * 10) + 1 = 7)
HUT_1, HUT_2, HIKE = " hut 1 ", " hut 2 ", " Hike! "                       # 0x4402ed, 0x44044f, 0x440d71
HUT = " hut"                                                               # 0x440b63, "!" appended 1 in 2
SNAP_PHRASES = (" takes the snap", " has the ball", " handles the snap", " takes the snap from center",
                " takes the ball", " has the snap", " gets the snap", " gets the ball", " gets the ball from center",
                " handles the snap from center", " gets the snap from center", " takes the ball from center",
                " has the snap from center")                              # 0x4416ca to 0x441ab7, Int(Rnd * 13) + 1

# ----- the kicks' snap count, kicksnap p_43a330 -----
KICK_HUT_1, KICK_HUT_2, KICK_HUT_3, KICK_HIKE = " hut 1 ", " hut 2 ", " hut 3 ", " hike! "

# ----- hand-off (GoSub 0x451b58) and drop-back (GoSub 0x4528c8), 5.9; "HS" = the He or She word of the passer -----
# (uses_hs, text): the phrase is <HS> + text when uses_hs, else text alone (" its a hand off to" and two others)
HANDOFF_PHRASES = ((True, "hands the ball off to"), (True, "hands the ball to"), (True, "turns and gives the ball to"),
                   (False, " its a hand off to"), (True, "turns and hands off to"), (True, "pitches the ball to"),
                   (False, " the hand off is to"), (False, " the hand off goes to"),
                   (True, "turns and hands the ball to"))                  # 0x452091 to 0x452429
DROPBACK_PHRASES = ("steps back to pass", "sets up in the pocket", "scrambles left looking for a receiver",
                    "scrambles right looking for a receiver", "looks for an open receiver", "drops back deep to pass",
                    "drops back  to pass", "looks left then right", "looks right then left", "takes a three step drop",
                    "sets and is forced out of the pocket")               # 0x452e09 to 0x45311f
# The fake texts are built and then overwritten, never spoken (Q35, D-028): kept here only as the record.
UNSPOKEN_FAKES = (" He fakes a hand off to ", " and then ", " He fakes a pass to ", " He pump fakes a pass and then ",
                  "fakes a hand off and then", "fakes to ", " then")

# ----- runs (5.9 table): the pieces of the run and tackle sentences -----
RUNS_STRAIGHT = " runs straight up the middle "
PILE_UP = " and there is a big pile up "
RUNS_OFF_TACKLE = " runs off tackle "
BROUGHT_DOWN, BY = " and is brought down", " by "
RUNS_THROUGH_A_HOLE = " runs through a hole "
TACKLED_BY = " and is tackled by "
AVOIDS_THE_BLITZ = " avoids the blitz of "
CAUGHT_BY = " AND IS CAUGHT BY "
FINDS_A_HOLE, SECOND_AIRY = " finds a hole ", " and gets into the second airy"
BEFORE, AND, CAN_CATCH_HIM = " before ", " and ", " can catch him"
RUNS_UP_FIELD, TACKLE_HIM = " and runs up field", " tackle him "
TRIES_TO_RUN, TACKLES_HIM = " tries to run ", " tackles him"
IS_TACKLED_BY, BEFORE_HE_CAN_GET = " is tackled by ", " before he can get "
RUNS, TACKLES_HIM_AT_THAT_POINT = " runs ", " tackles him at that point"
PAST, CHASES_AND_BRINGS_HIM_DOWN = " past ", " chases and brings him down"
FINDS_HIS_WAY, TRIPS_HIM_UP = " finds his way ", " trips him up"
GETS, HEADS_UP_FIELD, CHASE_HIM_DOWN = " gets ", " and heads up field, ", " chase him down"

# ----- passes (5.9) -----
THROW_PHRASES = (" puts the ball up", " gets the pass off", " lofts the ball up in to the air", " throws a perfect spiral",
                 " pumps then throws", " side arms the pass", " throws a side armed pass",
                 " throws an end over end wobbler", " rifles the ball")   # 0x44b855 to 0x44baf2, Int(Rnd * 9) + 1
CATCH_PHRASES = (" catches the ball ", " grabs it ", " comes down with it ", " is hit as he catches the pass ",
                 " makes a one handed catch ", " makes a leaping catch ", " comes back to the ball and makes the catch ",
                 " catches the ball on the run ", " makes an over the shoulder catch ")   # 0x44d674 to 0x44d911
INTERCEPTS, PICKS_OFF = " intercepts the ball ", " picks off the pass "            # 0x44bf11, 0x44bf60
SACKS, IS_SACKED_BY, SLAMS, TO_THE_GROUND = " sacks ", " is sacked by ", " slams ", " to the ground"
IS_SLAMMED_BY, IS_CHASED_DOWN_BY, SMOTHER = " is slammed to the ground by ", " is chased down by ", " smother "
DROPS_THE_BALL, OUT_OF_BOUNDS = " drops the ball ", " catches it out of bounds "
OVER_THE_HEAD_OF, FALLS_SHORT_OF = " it goes over the head of ", " it falls short of "
BATTED_DOWN_BY, BATS_IT_BACK_AT = " it is batted down by ", " bats it right back at "
THROUGH_THE_HANDS_OF = " it goes right through the hands of "
OFF_THE_CHEST_OF, OFF_THE_BACK_OF = " it bounces off of the chest of ", " it bounces off of the back of "
FUMBLE = " there is a fumble on the play "                                  # 0x44de49

# ----- the touchdown (5.11 item 2) -----
TD_CATCHES = (" catches the pass in the end zone ", " catches the pass, breaks a tackle and heads up field ",
              " catches the pass and runs up field ")                       # 0x44ec02 to 0x44eca7
HE_IS_AT_THE = " he is at the "
TOUCH_DOWN = " TOUCH DOWN"
SAFETY = " in the end zone for a safety"

# ----- the end of a play (5.11) -----
GAIN, LOSS, YARD, PLURAL = " There is a gain of ", " There is a loss of ", " yard", "s"
ON_THE_PLAY, ON_THE_PLAY_STOP = " on the play", " on the play."
NO_GAIN = " There is no gain on the play"
TURNED_OVER_ON_DOWNS = " ball turned over on downs the ball is now "
THE_BALL_IS_NOW = " the ball is now"
ITS_SPACE, ITS, ITS_CAPITAL = " it's ", " it's", " It's "
YOUR_BALL, MINE, ON = " your ball", " mine", " on"
YOUR, MY, BALL_ON, THE = " your", " my", " ball on", " the"
YARD_LINE_SPACED, YARD_LINE = " yard line", "yard line"
ORDINALS = {1: " first", 2: " second", 3: " third", 4: " fourth"}
DOWN_AND, GOAL, TO_GO = " down and", " goal", " to go"
YARD_NO_SPACE = "yard"                                    # the down sentence: Str$(L82c) & "yard" (" 10yards")
# F1 in a play menu (GoSub 0x458b24): " its " and " its" (no apostrophe), "your" and "my" without a space
F1_ITS, F1_ITS_SHORT, F1_YOUR, F1_MY = " its ", " its", "your", "my"

# ----- kicks (5.10) -----
FG_IN, WILL_HOLD = " is in for the field goal attempt ", " will hold "
SNAP_IS_GOOD, HOLD_IS_GOOD, KICK_IS_UP = " the snap is good ", " the hold is good", " the kick is up and it "
WAY_TO_SHORT, IS_GOOD = " is way to short", " is good"
FG_MISSES = (" is wide left", " is wide right", " hits the left upright", " hits the right upright",
             " hits the cross bar", " falls short")                         # 0x442ace to 0x442c24, Int(Rnd * 6) + 1
XP_IN, XP_GOOD = " is in for the extra point attempt ", " is good for the extra point "
TWO_POINT_GOOD = " the two point conversion is good "
PUNT_BACK_DEEP = " are back deep to receive the punt "
READY_TO_PUNT, KICK_THE_PUNT = " is ready to take the snap and ", " kick the punt "
LONG_SNAP, KICK_OFF_GETS = " takes the long snap", "gets the kick off "
ITS_A = " it's a. "
POOCH, PRETTY_GOOD, HIGH_BOOMING = " pooch kick", " pretty good kick", " high booming kick"
IT_TRAVELS, YARDS_IN_THE_AIR = " it travels", "yards in the air"
FAIR_CATCH = " calls for a fair catch "
OUT_OF_BOUNDS_PUNT = " the ball hits and bounces out of bounds "
DOWNED_BY = " the ball is downed by "
IT_IS_A_TOUCH_BACK = " IT IS A TOUCH BACK"
KICKOFF_BACK_DEEP = " are back deep to receive the kick off "
READY_TO_KICK_OFF = "  is ready to kick off "                              # two spaces, 0x444ac9
KICKOFF_UP = " The kick off is up and is headed for the end zone"
CATCHES_THE_BALL, DEEP_IN_THE_END_ZONE = " catches the ball", "deep in the end zone "
YARD_SPACE, YARDS_SPACE = " ", "s "
RUN_IT_OUT_1, RUN_IT_OUT_2 = " do you wish for ", " to run the ball out "
YES, NO = " yes ", " no "
DOWNS_IN_END_ZONE = " he downs the ball in the end zone for a touch back"
RETURN_RUNS = (" he is running left he turns and runs right now he is running left again",
               " He is running left he cuts right he cuts back to the left",
               " He lookes left then lookes right and heads for the middle of the field",
               " He starts left then changes direction and heads up the right side line",
               " He starts right then changes direction and heads up the left side line")   # 0x44587b to 0x445b07
IS_AT_THE_5 = " is at the 5"
RETURN_MARKS = ((9, " the 10"), (14, " the 15"), (19, " the 20"), (24, " 25"), (29, " 30"), (34, " 35"), (39, " 40"),
                (44, " 45"))                                                  # spoken when the return is past the number
ONE_MAN_TO_BEAT = " he is still running there is one man to beat"
CUT_DOWN, TACKLED, FINALLY_TACKLED = " He is cut down by", " He is tackled by", " He is finally tackled by"

# ----- the coin toss and the opening choice (4.14) -----
WHICH_DO_YOU_CALL = " Which do you call for the coin toss "
HEADS, TAILS = " heads ", " tails "
THE_TEAM, CALL = " the ", " call "               # " the " & team (the toss, the huddle)
HEADS_WORD, TAILS_WORD = "heads ", "tails "
HERE_IS_THE_COIN_TOSS, COIN_COMES_UP = " here is the coin toss ", " the coin comes up "
CHOOSE_TO_RECEIVE = " choose to receive "
WHICH_DO_YOU_WISH = " which do you wish to do "
RECEIVE, KICK_OFF = " receive ", " kick off "

# ----- the play menus (4.15) and the extra point choice (4.17) -----
SELECT_OFFENSE = " select the play for your off fence "
SELECT_DEFENSE = " select the play for your dee fence "
SELECT = " select "
KICK_FOR_EXTRA_POINT, TRY_FOR_TWO = " kick for extra point ", " try for two point conversion "

# ----- the breaks (4.19, 5.6) -----
END_OF_QUARTER = {1: " End of the First Quarter", 2: " End of the Second Quarter", 3: " End of the Third Quarter",
                  4: " End of the Fourth Quarter"}
TWO_MINUTE_WARNING = " Two Minute Warning"
OVERTIME_NUMBER = " We are going into over time number "
GAME_IS_OVER = " THE GAME IS OVER"
PRESS_ANY_KEY = " press any key to continue or the f 2 key to repeat "
STATS_AFTER = " Stats After Quarter number "
STAT_NAMES = (" Pass Attempts", " Pass Completions", " Passing Yardage ", " Times Sacked", " Times Intercepted",
              " Running Plays", " Running Yardage", " Fumbles Lost", " Total Yardage", " First Downs", " Points Scored")
GETTING_SAVED_GAME, GAME_SAVED = " getting saved game ", " Game Saved "
CONCEDE = " Do you wish to quit and concede this game? no "


class PhraseHistory:
    """The last `size` phrase numbers; a draw equal to one of them is drawn again (bounded, G-D1)."""

    def __init__(self, size: int):
        self.values: list[int] = [0] * size          # Empty = 0, which equals no phrase number

    def draw(self, rnd: GameRandom, count: int, what: str) -> int:
        """Int(Rnd * count) + 1 drawn again while it is in the history; then shifted in."""
        value = rnd.redraw(lambda: rnd(count), lambda v: v not in self.values,
                           lambda: next(v for v in range(1, count + 1) if v not in self.values), what)
        self.enter(value)
        return value

    def enter(self, value: int) -> None:
        self.values = self.values[1:] + [value]


class GroupedPhrases:
    """The hand-off and drop-back sentences (5.9): a group g = Int(Rnd * groups), drawn again while it equals the
    memory; a phrase p = Int(Rnd * per_group) + 1; the value 9 g + p (11 g + p) is drawn again (both draws) while it is
    one of the last 16 values. The hand-off's memory is the SENTENCE string of the main body (Q34: a number never
    equals a text, so after the first call nothing is rejected); the drop-back's is the group number. Empty (None
    here) equals 0, so the very first call of a game draws group 0 again in both. The phrase spoken is always the
    plain phrase of p (Q35)."""

    def __init__(self, groups: int, per_group: int, what: str):
        self.groups = groups
        self.per_group = per_group
        self.what = what
        self.history = PhraseHistory(16)
        self.memory: object = None                   # L4a0 (hand-off) or L438 (drop-back): Empty at a game's start

    def _rejects(self, group: int) -> bool:
        """`If g <> memory Then accept`: VB's Variant comparison. Empty equals 0; a text never equals a number."""
        if self.memory is None:
            return group == 0
        if isinstance(self.memory, str):
            return False
        return group == self.memory

    def draw(self, rnd: GameRandom, remember: Callable[[int], object]) -> int:
        """One call: the phrase number 1 to per_group. `remember(group)` gives what the routine stores as its memory
        once the value is accepted (the hand-off: the sentence text in L4f4; the drop-back: the group)."""
        def one_value() -> tuple[int, int]:
            group = rnd.redraw(lambda: rnd.below(self.groups), lambda g: not self._rejects(g),
                               lambda: next(g for g in range(self.groups) if not self._rejects(g)), self.what + " group")
            return group, group * self.per_group + rnd(self.per_group)

        def first_free() -> tuple[int, int]:
            for group in range(self.groups):
                if self._rejects(group):
                    continue
                for phrase in range(1, self.per_group + 1):
                    if group * self.per_group + phrase not in self.history.values:
                        return group, group * self.per_group + phrase
            raise RuntimeError("no free phrase value")      # 16 values cannot fill 27 or more

        group, value = rnd.redraw(one_value, lambda gv: gv[1] not in self.history.values, first_free, self.what)
        self.history.enter(value)
        self.memory = remember(group)
        return (value - 1) % self.per_group + 1
