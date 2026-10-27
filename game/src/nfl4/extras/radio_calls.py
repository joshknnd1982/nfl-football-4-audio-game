"""The radio play-by-play: every play called like a live radio broadcast, both modes (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

The owner, 2026-10-27, on 0.16.9: "The game still does not have radio-style broadcast. It still says 3rd and ten at the 26 yard line. Why
isn't it having exciting radio style? "caught by "playername!!" touchdown!!" Make it an exciting radio broadcast. Radio broadcasters use a
lot of exclamations. Make this a much more exciting and enthusiastic radio broadcast." (D-195; rule 0.27, 0.33, spec/RADIO_NFL_STYLE.md 4:
present tense in the action, a short result, the key word repeated on a big play.)

How it works. The engine still tells every play with the original's sentences, in the original's order and with the original's draws (pag
and its steps are not touched, so every game plays exactly as before). Each sentence the announcer says with say2 or say4 (the play-by-play;
menus, prompts and the crew use say5 and say_role and never come here) passes through RadioCalls.call, which knows the shapes of those
sentences (work/rc_1027/shapes.txt: every shape of ten whole games of both modes) and gives the radio call for it:
    * the action in short, lively words, with an exclamation where a real call raises its voice: "Caught by Seals!", "Intercepted!",
      "Sacked!", "Fumble! The ball is loose!", "Touchdown! Touchdown, Bengals!";
    * the teams by name instead of the original's "my ball" and "your ball": "The Bengals take over at their own 31.";
    * the down and distance as a radio call says it: "Third and 4! A big down here!", "First down, Bengals!";
    * the gain by its size: "A gain of 3.", "Good for 7 yards!", "What a play! 34 yards!";
    * growing excitement on a long run or a return: "He's at the 40! the 30! the 20! the 10! 5! 4! 3! 2! 1!".
A sentence of no known shape (the player's own lines, a sentence a later session adds) is said exactly as it is.

XV (D-198; the owner on 2026-10-27 asked for "an enthusiastic 1990s NFL radio play-by-play announcer": short punchy fragments on big plays,
exclamations, a color commentator chiming in after the call, "a randomized list of 10+ broadcast templates per play result type so it never
feels repetitive", and the voice faster and louder with the excitement, which "user should be able to turn it on or off"):
    * every kind of play result (RESULT_CALLS) has at least ten ways to say it; the sentences of one kind share a pool (the six sack
      sentences, the two interceptions, the three plain catches), so the variety is the pool's;
    * every call has a level of excitement (LEVELS: 1 routine, 2 a gain, 3 a big play, 4 a turnover or a sack, 5 the touchdown), and with
      F9, Rules, Excited voice on (nx_excited_voice, the default) the call is said with it: the game's own voices and NVDA say it higher,
      faster and a little louder as the level grows (speech/lift.py has the amounts and the measurements); JAWS says the words only;
    * the calls are written in normal case: the owner's example used capitals "so the system TTS raises its pitch", but MEASURED on 14 voices
      capitals raise no pitch and make many voices spell or stretch the word (work/xv_1027/sapi.txt), so the lift does that job;
    * the color analyst after the call is the broadcast's (extras/broadcast.py: Gus after a play, 10 to 24 lines a kind of play).

The switch: F9, Rules, Play calls (setting nx_play_calls): radio (the default) or plain, the original's words. It is read at every sentence,
so a change applies at once, also in the game being played; it is its own switch, not F8's (the comments): a player who turns the crew off
keeps the radio calls. Classic (extras/classic_radio.py) has them too; the engine's bare Classic rules (game/rules.CLASSIC, the golden
transcript) have none, because only the broadcast attaches the caller (the engine clears it at the start of every game).

The caller draws only from its OWN random generator (seeded like the broadcast's, game/rnd.side_seed), never from the game's, and changes no
state: the game's draws, plays, scores and times are the same with the radio calls as with the plain words (tests/test_rc_radio_calls.py).
F2 replays the calls that were said (they are what the replay list keeps).
"""
from __future__ import annotations

import logging
import random
import re

from ..game.rnd import side_seed
from ..speech.lift import BIG_PLAY, GAIN, ROUTINE, TOUCHDOWN, TURNOVER

log = logging.getLogger("nfl4.extras")

SEED_MIX = 0x2AD1_0CA1            # the radio calls' seed is the game's seed mixed with this (the broadcast's is another)
RADIO, PLAIN = "radio", "plain"
DEFAULT_CALLS = RADIO
CALLS_WORDS = {"radio": RADIO, "radio style": RADIO, "exciting": RADIO, "on": RADIO,
               "plain": PLAIN, "original": PLAIN, "the original's words": PLAIN, "off": PLAIN}
DEFAULT_EXCITED_VOICE = True      # XV (D-198): the calls said with their excitement (speech/lift.py); F9, Rules, Excited voice
BIG, HUGE = 20, 40                # yards: a big play, a huge one
MARKS_EXCITED = 3                 # a return: from the third yard marker on, every marker is called with an exclamation


def calls_key(value) -> str | None:
    """A value of the settings file: radio or plain, or None when it is neither (the spoken words are read too)."""
    word = " ".join(str(value or "").lower().split())
    return CALLS_WORDS.get(word)


def next_calls(key: str) -> str:
    """Enter, Left and Right switch between the two."""
    return PLAIN if key == RADIO else RADIO


# ----- the calls: each a tuple of variants, drawn with the caller's own generator, never the same variant twice in a row -----
# {team} the team the sentence is about, {spot} where the ball is ("their own 25", "the Jets 47", "midfield"), {n} a number, the others
# the names the original's sentence holds. Every variant is ASCII, at most 150 characters, one to three short sentences, in normal case:
# capitals raise no voice's pitch and make many voices spell the word (speech/lift.py, MEASURED), so the excitement is the voice's lift.
# XV (D-198): every kind of play result (RESULT_CALLS) has at least MIN_RESULT_VARIANTS ways to say it, so it never feels repetitive; the
# big plays are short, punchy fragments with exclamations.

CALLS = {
    # the huddle and the line (the start of a play)
    "huddle": ("The {t} break the huddle.", "Here come the {t} out of the huddle.", "The {t} out of the huddle and up to the line."),
    "no_huddle": ("No huddle! The {t} hurry up to the line!", "The {t} go no huddle! They rush to the line!"),
    "qb_up": ("{q} walks up to the line.", "{q} up to the line."),
    "qb_center": ("{q} under center.", "{q} is under center."),
    "qb_count": ("{q} barks out the signals.", "{q} calls out the signals."),
    "qb_gun": ("{q} in the shotgun.", "{q} sets up in the shotgun."),
    # the snap
    "snap": ("The snap to {q}.", "{q} takes the snap.", "{q} with the snap.", "Here's the snap to {q}."),
    # the drop-back ({h} is the original's He or She word)
    "drop_back": ("{h} drops back to pass.", "{h} drops back."),
    "drop_deep": ("{h} drops back deep.", "{h} drops way back to throw."),
    "step_back": ("{h} steps back to pass.", "{h} steps back to throw."),
    "pocket": ("{h} sets up in the pocket.", "{h} sets up, looking downfield."),
    "scramble_left": ("{h} rolls left, looking for someone open!", "{h} scrambles to the left, looking for a receiver!"),
    "scramble_right": ("{h} rolls right, looking for someone open!", "{h} scrambles to the right, looking for a receiver!"),
    "looks_open": ("{h} looks for an open receiver.", "{h} looks downfield."),
    "looks_lr": ("{h} looks left, then right.",),
    "looks_rl": ("{h} looks right, then left.",),
    "three_step": ("{h} takes a quick three-step drop.",),
    "flushed": ("{h} is flushed out of the pocket!", "Pressure! {h} is forced out of the pocket!"),
    # the hand-off
    "handoff": ("Handoff to {x}.", "{h} hands it off to {x}.", "The handoff goes to {x}."),
    "handoff_named": ("Handoff to {x}.", "The handoff goes to {x}.", "It's {x} with the handoff."),
    "pitch": ("{h} pitches it out to {x}!", "The pitch goes to {x}!"),
    # the throw
    "throw_up": ("{q} puts it up!", "{q} lets it fly!"),
    "throw_off": ("{q} gets the pass away!", "{q} gets it off!"),
    "throw_loft": ("{q} lofts one up in the air!", "{q} floats it up!"),
    "throw_spiral": ("{q} fires a perfect spiral!", "{q} throws a beautiful spiral!"),
    "throw_pump": ("{q} pumps, and throws!", "{q} pump fakes, then throws!"),
    "throw_side": ("{q} throws it sidearm!", "{q} sidearms it!"),
    "throw_wobble": ("{q} throws a wobbler, end over end!", "{q} gets off an ugly wobbler!"),
    "throw_rifle": ("{q} rifles it!", "{q} fires!"),
    # the catch: the original's three plain catch sentences share one pool; the others keep their own detail
    "catch": ("Caught by {r}!", "And {r} has it!", "{r} makes the catch!", "{r} grabs it!", "And {r} hauls it in!", "{r} comes down with it!",
              "Complete to {r}!", "{r} pulls it in!", "Got it! {r} makes the grab!", "And it's caught! {r} has it!", "{r} reels it in!",
              "Right on target! Caught by {r}!"),
    "catch_hit": ("Caught by {r}, and he takes a big hit!", "{r} makes the catch and gets drilled!"),
    "catch_one_hand": ("One hand! {r} makes a one-handed catch!", "{r} with a one-handed grab! What a catch!"),
    "catch_leap": ("{r} leaps and makes the catch!", "A leaping grab by {r}! What a catch!"),
    "catch_back": ("{r} comes back to the ball and makes the catch!", "{r} comes back for it and makes the grab!"),
    "catch_run": ("Caught on the run by {r}!", "{r} catches it in stride!"),
    "catch_shoulder": ("Over the shoulder! Caught by {r}!", "{r} with an over-the-shoulder catch! Beautiful!"),
    "td_catch_zone": ("{r} catches it in the end zone!", "Caught in the end zone by {r}!", "In the end zone! {r} has it!"),
    "td_catch_break": ("Caught by {r}! He breaks a tackle and he's gone!", "{r} makes the catch, breaks a tackle, and he's off to the races!"),
    "td_catch_run": ("Caught by {r}, and he's off and running!", "{r} hauls it in and races up field! Look at him go!"),
    # the pass that is not caught
    "through_hands": ("Right through the hands of {r}!", "It goes right through the hands of {r}!"),
    "over_head": ("It sails over the head of {r}!", "Over the head of {r}!"),
    "short_of": ("It falls short of {r}!", "Underthrown! It falls short of {r}!"),
    "batted": ("Batted down by {y}!", "{y} knocks it down!"),
    "bats_back": ("{y} bats it right back at {q}!",),
    "off_chest": ("It bounces off the chest of {r}!",),
    "off_back": ("It bounces off the back of {r}!",),
    "dropped": ("Dropped by {r}!", "{r} drops it! He had it, and he dropped it!"),
    "out_of_bounds": ("{r} catches it, but he's out of bounds!", "{r} has it, but he's out of bounds!"),
    # takeaways: both interception sentences of the original share one pool
    "pick": ("Intercepted! {y} picks it off!", "And it's picked off! {y} has it!", "Picked off! {y} intercepts the pass!",
             "Intercepted! {y} steps in front of it!", "Oh, it's picked! {y} comes up with it!", "Interception! {y} jumps the route!",
             "{y} picks it off! Intercepted!", "Intercepted by {y}! What a play!", "It's picked off! {y} read it all the way!",
             "Interception! {y} has the ball!", "Up for grabs, and {y} takes it away! Intercepted!", "Intercepted! {y} snags it out of the air!"),
    "fumble": ("Fumble! The ball is loose!", "He fumbles! The ball is on the ground!", "Fumble! Loose ball, loose ball!",
               "The ball is out! Fumble!", "Fumble! It's on the turf!", "He coughs it up! Fumble!", "Loose ball! It's a fumble!",
               "Fumble! The ball is bouncing around!", "It's knocked loose! Fumble!", "Fumble! Somebody fall on it!",
               "Oh, he put it on the ground! Fumble!", "Fumble! Bodies flying everywhere!"),
    "scramble_ball": ("There's a scramble for it!", "Everybody dives for it!", "A pile of bodies going after it!"),
    "falls_on": ("And {y} falls on it!", "And {y} comes up with it!"),
    # sacks: the original's six sack sentences share one pool ({y} may be two names joined by "and", so every line works with both)
    "sack": ("Sacked! {q} goes down, and that's {y}!", "Down goes {q}! Sacked by {y}!", "{q} is buried by {y}! Sacked!",
             "Sacked! {q} never had a chance against {y}!", "Sacked! {q} is dropped by {y}!", "{q} is taken down by {y}! Sacked!",
             "Sacked! {q} is brought down by {y}!", "Pressure, and down goes {q}! A sack by {y}!", "Sacked! {q} is swallowed up by {y}!",
             "{q} is wrapped up by {y}! Sacked!", "Sacked! {y} with a huge play on {q}!", "Oh, {q} is crushed! Sacked by {y}!"),
    # the quarterback's own runs (the QB pool's default lines; a player's own line is said as written)
    "qb_scramble": ("Nobody open! {q} takes off running!",),
    "qb_fake_keep": ("{q} fakes the handoff and keeps it!",),
    "qb_roll": ("{q} rolls out and takes off!",),
    "qb_slide": ("{q} slides, feet first.",),
    "qb_sneak": ("{q} pushes forward on the sneak!",),
    "qb_draw": ("{q} drops back, then takes off!",),
    "qb_keeps": ("{q} keeps it!",),
    "throw_away": ("{q} throws it away. No sack there.",),
    # runs ({w} where: "up the middle", "on the left side", "the right end" ...)
    "middle": ("{x} straight up the middle!", "{x} runs right up the middle!"),
    "off_tackle": ("{x} runs off tackle!", "{x} hits it off tackle!"),
    "hole": ("{x} bursts through a hole {w}!", "{x} through a hole {w}!"),
    "hole_free": ("{x} bursts through a hole {w}! He's into the open field!", "{x} through a hole {w}, and he's off to the races!"),
    "secondary": ("{x} finds a hole {w}, and he's into the secondary!", "{x} squirts through {w}! He's into the secondary! Look out!"),
    "around_up": ("{x} gets around {w}! He heads up field!", "{x} turns the corner around {w}! He's off to the races!"),
    "tries_around": ("{x} tries to get around {w}.", "{x} tries {w}."),
    "around_past": ("{x} around {w}, right past {y}!", "{x} races around {w}, and he's past {y}! Look at him go!"),
    "around": ("{x} runs around {w}!", "{x} around {w}!"),
    "finds_way": ("{x} finds his way around {w}!", "{x} works his way around {w}!"),
    "avoids_blitz": ("{x} makes {y} miss!", "{x} slips away from the blitzing {y}!"),
    # the tackle
    "stopped_before": ("{y} stops {x} before he can get {w}!", "{x} is tackled by {y} before he can get {w}."),
    "he_tackled": ("Brought down by {y}.", "Tackled by {y}."),
    "he_cut_down": ("Cut down by {y}!",),
    "he_finally": ("Finally brought down by {y}!", "And he's finally tackled by {y}!"),
    "caught_by": ("And he's caught from behind by {y}!",),
    "and_tackled": ("and he's brought down by {y}.", "and he's tackled by {y}."),
    "and_brought": ("and he's brought down by {y}.",),
    "tackles": ("{y} makes the tackle.", "{y} brings him down."),
    "tackles_there": ("{y} brings him down right there.", "{y} makes the stop there."),
    "chases_down": ("{y} chases him down!",),
    "two_chase": ("{y} and {z} chase him down!",),
    "before_catch": ("before {y} and {z} finally catch up with him!",),
    "before_trip": ("before {y} trips him up!",),
    "before_tackle": ("before {y} and {z} bring him down!",),
    "pile_up": ("and there's a big pile-up!", "and he disappears into a big pile!"),
    "pushed_out": ("and he's pushed out of bounds.",),
    # the result of the play: routine gains are calm, the bigger the play the shorter and louder the call
    "gain_1": ("A gain of 1.", "Just a yard on the play.", "He picks up a yard.", "A yard on the play.", "One yard, that's all.",
               "He gets a yard.", "Just one yard there.", "A short gain of 1.", "He falls forward for a yard.", "Only a yard on that one.",
               "A yard and no more."),
    "gain_short": ("A gain of {n}.", "{n} yards on the play.", "He picks up {n}.", "A short gain of {n}.", "{n} yards, and he's down.",
                   "He gets {n} on the play.", "Good for {n}.", "A pickup of {n}.", "He pushes ahead for {n}.", "{n} yards there.",
                   "A modest gain of {n}."),
    "gain": ("A gain of {n}!", "Good for {n} yards!", "{n} yards on the play!", "He picks up {n}!", "A nice gain of {n}!", "That's {n} yards!",
             "He gets {n} on the play!", "A solid gain of {n}!", "{n} yards, a good chunk!", "He moves it {n} yards!",
             "Positive yards! A gain of {n}!", "That's a pickup of {n}!"),
    "gain_good": ("A big gain of {n}!", "That's good for {n} yards!", "What a pickup! {n} yards!", "{n} yards on the play! Nice gain!",
                  "A chunk play! {n} yards!", "He rips off {n} yards!", "A gain of {n}, and that's a nice play!", "{n} yards! That moves the ball!",
                  "Nice gain! {n} yards on that one!", "He breaks off {n} yards!", "A healthy gain of {n}!", "That's {n} yards! Good football!"),
    "gain_big": ("What a play! A gain of {n} yards!", "{n} yards! A huge gain!", "A big, big play! {n} yards!", "Look at him go! {n} yards!",
                 "Big play! {n} yards on that one!", "{n} yards! What a gain!", "Off to the races! A gain of {n}!", "A breakaway! {n} yards!",
                 "Big play! He rips off {n} yards!", "Wow! {n} yards on the play!", "{n} yards! The crowd is on its feet!",
                 "Huge gain! {n} yards!"),
    "gain_huge": ("Oh, what a play! {n} yards!", "A gain of {n} yards! What a play!", "{n} yards! That's a monster play!", "Unbelievable! {n} yards!",
                  "A monster gain! {n} yards!", "{n} yards! What a play! The place is going crazy!", "Wow! {n} yards! What a play!",
                  "A huge, huge play! {n} yards!", "Oh, my! {n} yards on that one!", "{n} yards! Unbelievable!",
                  "What a play! {n} yards! You will not see many better than that!", "Explosive! {n} yards on the play!"),
    "return": ("A return of {n} yards.", "{n} yards on the return.", "He brings it back {n} yards!", "A nice return of {n}!",
               "{n} yards on the runback.", "He returns it {n} yards.", "A return of {n}, and decent field position.", "He takes it back {n}.",
               "That's {n} yards on the return!", "A solid return of {n} yards."),
    "return_big": ("What a return! {n} yards!", "A big return! {n} yards!", "{n} yards! What a return!", "He brings it back {n} yards! Huge return!",
                   "A monster return! {n} yards!", "Wow! {n} yards on the return!", "{n} yards! The return team came up big!",
                   "What a runback! {n} yards!", "Big play! A return of {n}!", "{n} yards on the return! Unbelievable!"),
    "loss_1": ("A loss of 1.", "He loses a yard.", "Dropped for a loss of 1.", "A yard lost on the play.", "Back one yard.",
               "He's stopped for a loss of 1.", "One yard lost.", "A loss of a yard there.", "They lose a yard.", "Stopped behind the line, a loss of 1."),
    "loss": ("A loss of {n}!", "Thrown for a loss of {n}!", "He loses {n} on the play!", "Dropped for a loss of {n}!",
             "A loss of {n}! The defense wins that one!", "Back {n} yards!", "Stopped behind the line! A loss of {n}!", "{n} yards lost on the play!",
             "The defense blows it up! A loss of {n}!", "Nowhere to go! A loss of {n}!", "He gives up {n} yards!"),
    "loss_sack": ("A loss of {n} on the sack!", "That sack costs {n} yards!", "{n} yards lost on the sack!", "The sack backs them up {n} yards!",
                  "A loss of {n}, and that hurts!", "That's {n} yards in the wrong direction!", "{n} yards back on the sack!",
                  "A drive killer! {n} yards lost!", "The sack takes away {n} yards!", "Back go the {t}, {n} yards!", "A big loss of {n} on the sack!"),
    "no_gain_incomplete": ("Incomplete.", "The pass falls incomplete.", "Incomplete, no gain.", "Incomplete pass.", "Incomplete. Nothing there.",
                           "No good, the pass is incomplete.", "And that one falls incomplete.", "Incomplete, and the play goes nowhere.",
                           "The pass is incomplete.", "Incomplete, no gain on the play.", "Incomplete. Nothing doing."),
    "no_gain_run": ("No gain on the play!", "Stopped cold! No gain!", "Nothing there! No gain.", "No gain! The defense holds!",
                    "He's stuffed at the line! No gain!", "No gain on that one.", "Stopped right there! No gain!", "Met at the line! No gain!",
                    "Going nowhere! No gain!", "The wall holds! No gain on the play!", "Nothing doing! No gain!"),
    "no_gain": ("No gain on the play.", "No gain.", "Nothing gained on the play.", "No gain there.", "And no gain.", "No gain on that one.",
                "That's no gain.", "Zero yards on the play.", "No gain, the ball stays put.", "No yards on the play."),
    # the ball and the downs ({spot} is "their own 25", "the Jets 47" or "midfield")
    "ball": ("The {t} are at {spot}.", "{t} ball at {spot}.", "The {t} have it at {spot}."),
    "ball_new": ("The {t} take over at {spot}.", "{t} ball, starting at {spot}.", "The {t} will start this drive at {spot}."),
    "ball_turnover": ("And the {t} take over at {spot}!", "The {t} have it now, at {spot}!", "Change of possession! {t} ball at {spot}!",
                      "Turnover! The {t} take over at {spot}!", "The {t} get the ball back at {spot}!",
                      "A huge change of possession! The {t} have it at {spot}!", "Takeaway! The {t} take over at {spot}!",
                      "The {t} will take it from {spot}! What a turn of events!", "And now it's {t} ball, at {spot}!",
                      "A gift for the {t}! They take over at {spot}!"),
    "ball_downs": ("Turnover on downs! The {t} take over at {spot}!", "They come up short! The {t} take over on downs at {spot}!",
                   "Stopped! Turnover on downs! {t} ball at {spot}!", "The defense holds! The {t} take over on downs at {spot}!",
                   "Short! And the {t} get it on downs at {spot}!", "Turnover on downs! What a stand! The {t} have it at {spot}!",
                   "No first down! The {t} take over at {spot}!", "The gamble fails! Turnover on downs! {t} ball at {spot}!",
                   "A huge stop! Turnover on downs! The {t} take over at {spot}!", "They didn't get it! The {t} take over on downs at {spot}!"),
    "first_gained": ("First down!", "First down, {t}!", "And that's a first down!", "That moves the chains! First down, {t}!",
                     "Move the chains! First down!", "First down! The drive rolls on!", "They've got the first down!",
                     "That's enough for a first down, {t}!", "First down! The {t} keep it going!", "Moving the sticks! First down!",
                     "And he's got the first down!", "First down, and the {t} keep coming!"),
    "first_gained_n": ("First down, {t}! First and {n}.", "That's a first down! First and {n}.", "First down! First and {n} now.",
                       "Move the chains! First and {n}.", "The {t} pick up the first down! First and {n}.", "First down! It's first and {n}.",
                       "They've got it! First and {n}, {t}!", "That's a first down! Now first and {n}!", "First down, {t}! It'll be first and {n}.",
                       "The chains move! First and {n}!"),
    "first": ("First and {n}.", "First and {n} to start the drive.", "First and {n}, here we go."),
    "first_goal_gained": ("First and goal, {t}!", "First and goal!", "First down, and it's first and goal!",
                          "First and goal! The {t} are knocking on the door!", "They're in close now! First and goal!",
                          "First and goal, and the {t} can smell the end zone!", "In close! First and goal!", "First and goal! Here we go!",
                          "That's first and goal for the {t}!", "First and goal! The end zone is right there!"),
    "first_goal": ("First and goal.",),
    "second_short": ("Second and {n}. Short yardage.", "Second and {n}, just {n} to go!"),
    "second_long": ("Second and {n}.", "Second and long, {n} to go."),
    "second": ("Second and {n}.", "Second down, {n} to go."),
    "second_goal": ("Second and goal.",),
    "third_short": ("Third and {n}! A short-yardage play coming up!", "Third and {n}! Can they pick it up?"),
    "third_long": ("Third and long! {n} yards to go!", "Third and {n}! A tough spot for the {t}!"),
    "third": ("Third and {n}! A big down here!", "Third down, {n} to go! This is a big one!"),
    "third_goal": ("Third and goal!", "Third and goal! A huge play coming up!"),
    "fourth": ("Fourth and {n}!", "Fourth down, {n} to go!"),
    "fourth_goal": ("Fourth and goal!",),
    # the kick-off and the return
    "deep_kickoff": ("{a} and {b} are back deep to receive.", "{a} and {b} are back deep for the kick off."),
    "ready_kickoff": ("{k} is set to kick it off.", "{k} is ready to kick off."),
    "kickoff_up": ("And here's the kick! It's headed for the end zone!", "The kick is in the air! It's deep, headed for the end zone!"),
    "deep_catch": ("{x} takes it {n} yards deep in the end zone!", "{x} catches it {n} yards deep in the end zone!"),
    "downs_end_zone": ("He takes a knee in the end zone. Touchback.", "He downs it in the end zone. Touchback."),
    "touch_back": ("Touchback.", "It's a touchback.", "Touchback, no return.", "And that will be a touchback.", "A touchback.",
                   "No return, touchback.", "That's a touchback.", "Into the end zone, touchback.", "It's a touchback, nothing more.",
                   "Touchback, and the ball comes out."),
    "ret_left_right": ("He's running left, he turns back right, now he's going left again!",),
    "ret_cuts": ("He's running left, he cuts right, he cuts back to the left!",),
    "ret_middle": ("He looks left, he looks right, and heads for the middle of the field!",),
    "ret_right_line": ("He starts left, cuts back, and heads up the right sideline!",),
    "ret_left_line": ("He starts right, cuts back, and heads up the left sideline!",),
    "ret_at_5": ("{x} is at the 5,", "{x} at the 5,"),
    "one_man": ("He's still going! Only one man to beat!", "He's still running! There's one man to beat!"),
    # the punt
    "deep_punt": ("{a} and {b} are back deep for the punt.", "{a} and {b} are back to receive the punt."),
    "long_snap": ("The long snap to {x}.", "{x} takes the long snap."),
    "ready_punt": ("{p} is back to punt.", "{p} drops back to punt it away."),
    "punt_away": ("He gets it away!", "He gets the punt away!"),
    "punt_good": ("A pretty good kick.",),
    "punt_booming": ("A high, booming kick!", "A booming punt! Way up there!"),
    "punt_pooch": ("A little pooch kick.",),
    "punt_travels": ("It travels {n} yards in the air.", "{n} yards in the air."),
    "downed": ("Downed by {x}.",),
    "fair_catch": ("{x} waves for a fair catch.", "{x} calls for the fair catch.", "Fair catch signaled by {x}.", "{x} puts up his hand. Fair catch.",
                   "{x} signals for a fair catch.", "No return, {x} calls for the fair catch.", "{x} waves his arm. Fair catch.",
                   "{x} will fair catch it.", "Fair catch by {x}.", "{x} takes the fair catch."),
    "bounces_out": ("It bounces out of bounds.",),
    # field goals and tries ({t} the kicking team)
    "fg_in": ("{k} comes on for the field goal try.", "Here comes {k} for the field goal attempt."),
    "xp_in": ("{k} is on for the extra point.", "Here's {k} for the extra point."),
    "holder": ("{x} will hold.", "{x} is the holder."),
    "snap_good": ("The snap is good,", "Good snap,"),
    "hold_good": ("the hold is down,", "the hold is good,"),
    "kick_up": ("The kick is up, and it",),
    "fg_good": ("is good! It's good!", "is good! Right down the middle!", "is good! Right through the uprights!", "is good! Three points for the {t}!",
                "is good! Split the uprights!", "is good! The kick is good!", "is good! Plenty of leg on that one!", "is good! Right between the pipes!",
                "is good! Never a doubt!", "is good! The {t} put three on the board!", "is good! Dead center!", "is good! The {t} add three!"),
    "xp_good": ("is good! The extra point is good!", "is good! And that's the extra point!", "is good! The point after is good!",
                "is good! Tack on the extra point!", "is good! Right through!", "is good! No trouble there!", "is good! The {t} add the point!",
                "is good! Automatic!", "is good! That one splits the uprights!", "is good! The point after is in!"),
    "fg_miss": ("{m}! No good!", "{m}! The kick is no good!", "{m}! It's no good!", "{m}! Oh, no good!", "{m}! And that one is no good!",
                "{m}! No good! The {t} come away empty!", "{m}! No good! What a miss!", "{m}! And it's no good! Oh, my!",
                "{m}! No good! That one will sting!", "{m}! No good, and the {t} get nothing!", "{m}! The kick is no good! A big miss!"),
    "fg_way_short": ("is way too short! No good!",),
    "two_good": ("The two-point conversion is good!", "They get it! The two-point try is good!", "Two points! The conversion is good!",
                 "It's good! The {t} get the two points!", "They're in! The two-point try is good!", "The conversion is good! Two more for the {t}!",
                 "Yes! The two-point try is good!", "Got it! The {t} convert the two!", "The two-point play works! It's good!",
                 "Two points for the {t}! The conversion is good!"),
    # the touchdown and the safety
    "he_is_at": ("He's at the",),
    "touchdown": ("Touchdown! Touchdown, {t}!", "Touchdown {t}! What a play!", "He's in! Touchdown!", "Touchdown! The {t} score!",
                  "He scores! Touchdown, {t}!", "Into the end zone! Touchdown!", "Touchdown! Six points for the {t}!",
                  "Oh, he's in there! Touchdown, {t}!", "Touchdown! The {t} find the end zone!", "And that's a touchdown! The {t} score!",
                  "Touchdown! Unbelievable! The {t} put six on the board!", "Six points! Touchdown, {t}!"),
    "safety": ("in the end zone! It's a safety!", "in the end zone! Safety! Two points for the defense!", "in the end zone! That's a safety!",
               "in the end zone! A safety! What a play by the defense!", "in the end zone! Safety! The defense comes up big!",
               "in the end zone! It's a safety, and two points!", "in the end zone! Safety! Oh, what a stop!", "in the end zone! A safety! The defense scores!",
               "in the end zone! Safety! They trapped him!", "in the end zone! It's a safety! Two points on the board!"),
    # the onside kick
    "onside": ("The {t} are going for the onside kick!", "Here it comes! The {t} try the onside kick!"),
}

# XV (D-198): the excitement of each call (speech/lift.py): 2 a gain, 3 a big play, 4 a turnover or a sack, 5 the touchdown; every other call
# is routine (1). A countdown's yard marker is a big play, a return's first markers a gain (_r_mark).
LEVELS = {
    GAIN: ("catch", "catch_hit", "catch_back", "catch_run", "first_gained", "first_gained_n", "first_goal_gained", "gain_good", "return",
           "loss", "loss_sack", "xp_good", "third", "third_short", "third_long", "third_goal", "fourth", "fourth_goal", "flushed",
           "scramble_left", "scramble_right", "avoids_blitz", "kickoff_up", "punt_booming", "no_huddle", "ret_at_5", "dropped", "batted"),
    BIG_PLAY: ("gain_big", "gain_huge", "return_big", "one_man", "he_is_at", "hole_free", "secondary", "around_up", "around_past",
               "td_catch_break", "td_catch_run", "catch_one_hand", "catch_leap", "catch_shoulder", "fg_good", "two_good", "fg_miss", "onside",
               "fg_way_short"),
    TURNOVER: ("pick", "fumble", "scramble_ball", "falls_on", "sack", "ball_turnover", "ball_downs", "safety", "bats_back"),
    TOUCHDOWN: ("touchdown", "td_catch_zone"),
}
LEVEL_OF = {key: level for level, keys in LEVELS.items() for key in keys}
# XV (D-198): the kinds of play result, each said in at least MIN_RESULT_VARIANTS ways (the owner's request: "a randomized list of 10+
# broadcast templates per play result type so it never feels repetitive"; tests/test_xv_excited_voice.py)
MIN_RESULT_VARIANTS = 10
RESULT_CALLS = ("gain_1", "gain_short", "gain", "gain_good", "gain_big", "gain_huge", "return", "return_big", "loss_1", "loss", "loss_sack",
                "no_gain_incomplete", "no_gain_run", "no_gain", "first_gained", "first_gained_n", "first_goal_gained", "touchdown", "safety",
                "pick", "fumble", "sack", "ball_turnover", "ball_downs", "fg_good", "xp_good", "fg_miss", "two_good", "touch_back", "fair_catch",
                "catch")
TEAM_CALLS = frozenset(("touchdown", "onside", "fg_good", "xp_good", "fg_miss", "two_good"))   # {t}: the team with the ball

_W = r"(?P<w>up the middle|on the left side|on the right side|the left end|the right end|the left side|the right side)"
_N = r"(?P<n>\d+)"
_DOWNS = r"(?P<d>first|second|third|fourth)"
_OWNER = r"(?P<p>your ball|my ball|mine)"
_HALF = r"(?P<h>your|my|the)"
_MISS = r"(?P<m>is wide left|is wide right|hits the left upright|hits the right upright|hits the cross bar|falls short)"

# (pattern on the sentence with its spaces collapsed, the rule): the more particular pattern first
PATTERNS = [
    # the play's start
    (r"the (?P<t>.+?) break the huddle", "huddle"),
    (r"the (?P<t>.+?) come to the line without a huddle", "no_huddle"),
    (r"(?P<q>.+?) is up to the line", "qb_up"),
    (r"(?P<q>.+?) is under center", "qb_center"),
    (r"(?P<q>.+?) barks out the snap count", "qb_count"),
    (r"(?P<q>.+?) is in the shot gun", "qb_gun"),
    # the quarterback's runs
    (r"(?P<q>.+?) cannot find a receiver and takes off running", "qb_scramble"),
    (r"(?P<q>.+?) fakes the hand off and keeps it", "qb_fake_keep"),
    (r"(?P<q>.+?) rolls out and takes off", "qb_roll"),
    (r"(?P<q>.+?) slides feet first", "qb_slide"),
    (r"(?P<q>.+?) pushes forward behind the center", "qb_sneak"),
    (r"(?P<q>.+?) drops back, then takes off", "qb_draw"),
    (r"(?P<q>.+?) keeps the ball", "qb_keeps"),
    (r"(?P<q>.+?) throws the ball away to avoid the sack\.?", "throw_away"),
    # the snap (the original's thirteen snap sentences)
    (r"(?P<q>.+?) (?:takes|has|handles|gets) the (?:snap|ball)(?: from center)?", "snap"),
    # the drop-back
    (r"(?P<h>\w+) drops back to pass", "drop_back"),
    (r"(?P<h>\w+) drops back deep to pass", "drop_deep"),
    (r"(?P<h>\w+) steps back to pass", "step_back"),
    (r"(?P<h>\w+) sets up in the pocket", "pocket"),
    (r"(?P<h>\w+) scrambles left looking for a receiver", "scramble_left"),
    (r"(?P<h>\w+) scrambles right looking for a receiver", "scramble_right"),
    (r"(?P<h>\w+) looks for an open receiver", "looks_open"),
    (r"(?P<h>\w+) looks left then right", "looks_lr"),
    (r"(?P<h>\w+) looks right then left", "looks_rl"),
    (r"(?P<h>\w+) takes a three step drop", "three_step"),
    (r"(?P<h>\w+) sets and is forced out of the pocket", "flushed"),
    # the hand-off ({h} the original's He or She word)
    (r"(?P<h>\w+) hands the ball off to (?P<x>.+)", "handoff"),
    (r"(?P<h>\w+) hands the ball to (?P<x>.+)", "handoff"),
    (r"(?P<h>\w+) turns and gives the ball to (?P<x>.+)", "handoff"),
    (r"(?P<h>\w+) turns and hands off to (?P<x>.+)", "handoff"),
    (r"(?P<h>\w+) turns and hands the ball to (?P<x>.+)", "handoff"),
    (r"(?P<h>\w+) pitches the ball to (?P<x>.+)", "pitch"),
    (r"its a hand off to (?P<x>.+)", "handoff_named"),
    (r"the hand off is to (?P<x>.+)", "handoff_named"),
    (r"the hand off goes to (?P<x>.+)", "handoff_named"),
    # the throw
    (r"(?P<q>.+?) puts the ball up", "throw_up"),
    (r"(?P<q>.+?) gets the pass off", "throw_off"),
    (r"(?P<q>.+?) lofts the ball up in to the air", "throw_loft"),
    (r"(?P<q>.+?) throws a perfect spiral", "throw_spiral"),
    (r"(?P<q>.+?) pumps then throws", "throw_pump"),
    (r"(?P<q>.+?) side arms the pass", "throw_side"),
    (r"(?P<q>.+?) throws a side armed pass", "throw_side"),
    (r"(?P<q>.+?) throws an end over end wobbler", "throw_wobble"),
    (r"(?P<q>.+?) rifles the ball", "throw_rifle"),
    # the catch
    (r"and (?P<r>.+?) catches the ball on the run", "catch_run"),
    (r"and (?P<r>.+?) catches the ball", "catch"),
    (r"and (?P<r>.+?) grabs it", "catch"),
    (r"and (?P<r>.+?) comes down with it", "catch"),
    (r"and (?P<r>.+?) is hit as he catches the pass", "catch_hit"),
    (r"and (?P<r>.+?) makes a one handed catch", "catch_one_hand"),
    (r"and (?P<r>.+?) makes a leaping catch", "catch_leap"),
    (r"and (?P<r>.+?) comes back to the ball and makes the catch", "catch_back"),
    (r"and (?P<r>.+?) makes an over the shoulder catch", "catch_shoulder"),
    (r"(?P<r>.+?) catches the pass in the end zone", "td_catch_zone"),
    (r"(?P<r>.+?) catches the pass, breaks a tackle and heads up field", "td_catch_break"),
    (r"(?P<r>.+?) catches the pass and runs up field", "td_catch_run"),
    # the pass that is not caught
    (r"it goes right through the hands of (?P<r>.+)", "through_hands"),
    (r"it goes over the head of (?P<r>.+)", "over_head"),
    (r"it falls short of (?P<r>.+)", "short_of"),
    (r"it is batted down by (?P<y>.+)", "batted"),
    (r"(?P<y>.+?) bats it right back at (?P<q>.+)", "bats_back"),
    (r"it bounces off of the chest of (?P<r>.+)", "off_chest"),
    (r"it bounces off of the back of (?P<r>.+)", "off_back"),
    (r"(?P<r>.+?) drops the ball", "dropped"),
    (r"(?P<r>.+?) catches it out of bounds", "out_of_bounds"),
    # takeaways
    (r"and (?P<y>.+?) intercepts the ball", "pick"),
    (r"and (?P<y>.+?) picks off the pass", "pick"),
    (r"there is a fumble on the play", "fumble"),
    (r"there is a scramble for the ball\.?", "scramble_ball"),
    (r"and (?P<y>.+?) falls on the ball\.?", "falls_on"),
    # sacks
    (r"(?P<y>.+?) and (?P<z>.+?) smother (?P<q>.+)", "SMOTHER"),
    (r"(?P<q>.+?) is sacked by (?P<y>.+)", "sack"),
    (r"(?P<q>.+?) is slammed to the ground by (?P<y>.+)", "sack"),
    (r"(?P<q>.+?) is chased down by (?P<y>.+)", "sack"),
    (r"(?P<y>.+?) slams (?P<q>.+?) to the ground", "sack"),
    (r"(?P<y>.+?) sacks (?P<q>.+)", "sack"),
    # runs
    (r"(?P<x>.+?) runs straight up the middle", "middle"),
    (r"(?P<x>.+?) runs off tackle", "off_tackle"),
    (r"(?P<x>.+?) runs through a hole " + _W + r" and runs up field", "hole_free"),
    (r"(?P<x>.+?) runs through a hole " + _W, "hole"),
    (r"(?P<x>.+?) finds a hole " + _W + r" and gets into the second airy", "secondary"),
    (r"(?P<x>.+?) gets around " + _W + r" and heads up field,?", "around_up"),
    (r"(?P<x>.+?) tries to run around " + _W, "tries_around"),
    (r"(?P<x>.+?) runs around " + _W + r" past (?P<y>.+)", "around_past"),
    (r"(?P<x>.+?) runs around " + _W, "around"),
    (r"(?P<x>.+?) finds his way around " + _W, "finds_way"),
    (r"(?P<x>.+?) avoids the blitz of (?P<y>.+)", "avoids_blitz"),
    # the tackle
    (r"(?P<x>.+?) is tackled by (?P<y>.+?) before he can get (?P<w>.+)", "stopped_before"),
    (r"he is tackled by (?P<y>.+)", "he_tackled"),
    (r"he is cut down by (?P<y>.+)", "he_cut_down"),
    (r"he is finally tackled by (?P<y>.+)", "he_finally"),
    (r"and is caught by (?P<y>.+)", "caught_by"),
    (r"and is tackled by (?P<y>.+)", "and_tackled"),
    (r"and is brought down by (?P<y>.+)", "and_brought"),
    (r"(?P<y>.+?) tackles him at that point", "tackles_there"),
    (r"(?P<y>.+?) chases and brings him down", "chases_down"),
    (r"(?P<y>.+?) and (?P<z>.+?) chase him down", "two_chase"),
    (r"(?P<y>.+?) tackles him", "tackles"),
    (r"before (?P<y>.+?) and (?P<z>.+?) can catch him", "before_catch"),
    (r"before (?P<y>.+?) trips him up", "before_trip"),
    (r"before (?P<y>.+?) and (?P<z>.+?) tackle him", "before_tackle"),
    (r"and there is a big pile up", "pile_up"),
    (r"and is pushed out of bounds", "pushed_out"),
    # the result of the play
    (r"there is a gain of " + _N + r" yards? on the play\.?", "GAIN"),
    (r"there is a loss of " + _N + r" yards? on the play\.?", "LOSS"),
    (r"there is no gain on the play\.?", "NO_GAIN"),
    (r"ball turned over on downs the ball is now " + _OWNER + " on " + _HALF + " " + _N + r" ?yard line", "BALL_DOWNS"),
    (r"the ball is now " + _OWNER + " on " + _HALF + " " + _N + r" ?yard line", "BALL_TURNOVER"),
    (r"it's " + _OWNER + " on " + _HALF + " " + _N + r" ?yard line", "BALL"),
    (r"it's " + _DOWNS + r" down and goal to go", "DOWN_GOAL"),
    (r"it's " + _DOWNS + r" down and " + _N + r" ?yards? to go", "DOWN"),
    # the kick-off and the return
    (r"(?P<a>.+?) and (?P<b>.+?) are back deep to receive the kick off", "deep_kickoff"),
    (r"(?P<k>.+?) is ready to kick off", "ready_kickoff"),
    (r"the kick off is up and is headed for the end zone", "kickoff_up"),
    (r"(?P<x>.+?) catches the ball " + _N + r" yards? deep in the end zone", "deep_catch"),
    (r"he downs the ball in the end zone for a touch back", "downs_end_zone"),
    (r"it is a touch back", "touch_back"),
    (r"he is running left he turns and runs right now he is running left again", "ret_left_right"),
    (r"he is running left he cuts right he cuts back to the left", "ret_cuts"),
    (r"he lookes left then lookes right and heads for the middle of the field", "ret_middle"),
    (r"he starts left then changes direction and heads up the right side line", "ret_right_line"),
    (r"he starts right then changes direction and heads up the left side line", "ret_left_line"),
    (r"(?P<x>.+?) is at the 5", "ret_at_5"),
    (r"he is still running there is one man to beat", "one_man"),
    (r"(?:the )?" + _N, "MARK"),
    # the punt
    (r"(?P<a>.+?) and (?P<b>.+?) are back deep to receive the punt", "deep_punt"),
    (r"(?P<x>.+?) takes the long snap", "long_snap"),
    (r"(?P<p>.+?) is ready to take the snap and kick the punt", "ready_punt"),
    (r"he gets the kick off", "punt_away"),
    (r"it's a\. pretty good kick", "punt_good"),
    (r"it's a\. high booming kick", "punt_booming"),
    (r"it's a\. pooch kick", "punt_pooch"),
    (r"it travels " + _N + r" ?yards in the air", "punt_travels"),
    (r"the ball is downed by (?P<x>.+)", "downed"),
    (r"(?P<x>.+?) calls for a fair catch", "fair_catch"),
    (r"the ball hits and bounces out of bounds", "bounces_out"),
    # field goals and tries
    (r"(?P<k>.+?) is in for the field goal attempt", "fg_in"),
    (r"(?P<k>.+?) is in for the extra point attempt", "xp_in"),
    (r"(?P<x>.+?) will hold", "holder"),
    (r"the snap is good", "snap_good"),
    (r"the hold is good", "hold_good"),
    (r"the kick is up and it", "kick_up"),
    (r"is good for the extra point", "xp_good"),
    (r"is good", "fg_good"),
    (_MISS, "fg_miss"),
    (r"is way to short", "fg_way_short"),
    (r"the two point conversion is good", "two_good"),
    # the touchdown and the safety
    (r"he is at the", "he_is_at"),
    (r"touch down", "touchdown"),
    (r"in the end zone for a safety", "safety"),
    # the onside kick
    (r"the (?P<t>.+?) will try an onside kick\.?", "onside"),
]
COMPILED = [(re.compile(pattern, re.IGNORECASE), rule) for pattern, rule in PATTERNS]

# what the last action of a play was (the result's words follow it)
ACTION_OF = {"catch": "catch", "catch_hit": "catch", "catch_one_hand": "catch",
             "catch_leap": "catch", "catch_back": "catch", "catch_run": "catch", "catch_shoulder": "catch", "td_catch_zone": "catch",
             "td_catch_break": "catch", "td_catch_run": "catch",
             "through_hands": "incomplete", "over_head": "incomplete", "short_of": "incomplete", "batted": "incomplete",
             "bats_back": "incomplete", "off_chest": "incomplete", "off_back": "incomplete", "dropped": "incomplete",
             "out_of_bounds": "incomplete", "throw_away": "incomplete",
             "pick": "takeaway", "fumble": "takeaway",
             "sack": "sack",
             "middle": "run", "off_tackle": "run", "hole": "run", "hole_free": "run", "secondary": "run", "around_up": "run",
             "tries_around": "run", "around_past": "run", "around": "run", "finds_way": "run", "avoids_blitz": "run",
             "qb_scramble": "run", "qb_fake_keep": "run", "qb_roll": "run", "qb_sneak": "run", "qb_draw": "run", "qb_keeps": "run",
             "deep_catch": "return", "ret_left_right": "return", "ret_cuts": "return", "ret_middle": "return",
             "ret_right_line": "return", "ret_left_line": "return", "ret_at_5": "return",
             "ready_punt": "kick", "ready_kickoff": "kick", "deep_kickoff": "kick", "fg_in": "kick", "xp_in": "kick",
             "deep_punt": "kick"}
# a new play begins: what the last one did is forgotten
STARTS = frozenset(("huddle", "no_huddle", "deep_kickoff", "ready_kickoff", "deep_punt", "ready_punt", "fg_in", "xp_in"))
ORDINAL = {"first": 1, "second": 2, "third": 3, "fourth": 4}


class RadioCalls:
    """The caller of one broadcast (extras/broadcast.Broadcast.calls): attached to each game with the broadcast."""

    def __init__(self, broadcast):
        self.b = broadcast
        self.game = None
        self.rnd = random.Random(SEED_MIX)
        self._told = None                     # the setting the log last named
        self._voice_told = None               # XV: the Excited voice setting the log last named
        self._reset()

    def _reset(self) -> None:
        self.action = None                    # the last action of this play: run, catch, incomplete, sack, takeaway, return, kick
        self.ball_side = 0                    # the side that had the ball at the last ball sentence (0: none yet this game)
        self.new_possession = True            # the last ball sentence gave the ball to the other side (or it was the game's first)
        self.countdown = None                 # the touchdown countdown: how many numbers were called (None: not in one)
        self.marks = None                     # a return's yard markers called (None: not in a return)
        self.last: dict[str, int] = {}        # the variant said last for each call
        self.calls = 0                        # the calls said this game (the log says it at the end of the game)

    def attach(self, game) -> None:
        """A new game: its own generator, seeded from the program's seed and the game's draws so far (as the broadcast's)."""
        self.game = game
        self.rnd = random.Random(side_seed(getattr(game, "rnd", None), SEED_MIX))
        self._reset()
        self._told = None
        self._voice_told = None
        self.on()                             # the log names the setting of this game
        self.excited()

    # ----- the switch -----

    def setting(self) -> str:
        settings = getattr(getattr(getattr(self.game, "options", None), "settings", None), "game", None)
        return calls_key(getattr(settings, "nx_play_calls", None)) or getattr(self.b, "play_calls", DEFAULT_CALLS)

    def on(self) -> bool:
        key = self.setting()
        if key != self._told:
            self._told = key
            log.info("radio calls: %s", "on, the play-by-play is called like a radio broadcast" if key == RADIO
                     else "off, the play-by-play in the original's words")
        return key == RADIO and self.game is not None

    def excited(self) -> bool:
        """XV (D-198): F9, Rules, Excited voice (nx_excited_voice), read at every call so a change applies at once."""
        settings = getattr(getattr(getattr(self.game, "options", None), "settings", None), "game", None)
        value = getattr(settings, "nx_excited_voice", None)
        if value is None:
            value = getattr(self.b, "excited_voice", DEFAULT_EXCITED_VOICE)
        value = bool(value)
        if value != self._voice_told:
            self._voice_told = value
            log.info("radio calls: excited voice %s", "on, the big plays are said higher, faster and louder" if value
                     else "off, every call in the voice as it is")
        return value

    # ----- the call -----

    def call(self, text: str) -> tuple[str, int]:
        """The radio call of one sentence of the play-by-play and its excitement (XV, D-198: 1 to 5, or 0 with the Excited voice off); the
        sentence itself and 0 when it has no known shape or the radio calls are off."""
        if not self.on():
            return text, 0
        plain = " ".join(text.split())
        for pattern, rule in COMPILED:
            m = pattern.fullmatch(plain)
            if m is None:
                continue
            said = self._rule(rule, m)
            if said is None:
                return text, 0
            key, out = said
            self.calls += 1
            return " " + out + " ", (self.level(key, out) if self.excited() else 0)
        return text, 0

    @staticmethod
    def level(key: str, said: str) -> int:
        """XV (D-198): the excitement of a call: its LEVELS entry; a yard marker is a big play in a countdown or with its exclamation."""
        if key == "mark":
            return BIG_PLAY if said.endswith("!") else GAIN
        return LEVEL_OF.get(key, ROUTINE)

    def _rule(self, rule: str, m) -> tuple[str, str] | None:
        values = {k: v.strip() for k, v in m.groupdict().items() if v is not None}
        if rule in STARTS:
            self.action, self.countdown, self.marks = None, None, None
        handler = getattr(self, "_r_" + rule.lower(), None) if rule.isupper() else None
        if handler is not None:
            return handler(values)
        if rule in ACTION_OF:
            self.action = ACTION_OF[rule]
        if rule == "ret_at_5":
            self.marks = 1
        elif rule == "he_is_at":
            self.countdown, self.marks = 0, None
        elif rule in ("touchdown", "safety", "touch_back", "downs_end_zone"):
            self.countdown, self.marks = None, None
        if rule in TEAM_CALLS:
            values["t"] = values.get("t") or self.team(self.side_with_ball())
        return rule, self.pick(rule, values)

    # ----- the rules that need the game -----

    def _r_gain(self, v):
        n = int(v["n"])
        if self.action == "return":
            key = "return_big" if n >= 30 else "return"
        elif n >= HUGE:
            key = "gain_huge"
        elif n >= BIG:
            key = "gain_big"
        elif n >= 10:
            key = "gain_good"
        elif n >= 4:
            key = "gain"
        elif n >= 2:
            key = "gain_short"
        else:
            key = "gain_1"
        self.marks = None
        return key, self.pick(key, {"n": str(n)})

    def _r_loss(self, v):
        n = int(v["n"])
        key = "loss_sack" if self.action == "sack" else "loss_1" if n == 1 else "loss"
        return key, self.pick(key, {"n": str(n), "t": self.team(self.side_with_ball())})

    def _r_smother(self, v):
        """Two tacklers smother the quarterback: the sack pool, its lines said with both names (XV: every sack line fits two names)."""
        self.action = "sack"
        return "sack", self.pick("sack", {"y": v["y"] + " and " + v["z"], "q": v["q"]})

    def _r_no_gain(self, v):
        key = {"incomplete": "no_gain_incomplete", "run": "no_gain_run"}.get(self.action, "no_gain")
        return key, self.pick(key, {})

    def _ball(self, v, kind: str):
        side = 1 if v["p"].lower() == "your ball" else 2
        half = {"your": 1, "my": 2}.get(v["h"].lower(), 0)
        n = int(v["n"])
        if half == 0 or n >= 50:
            spot = "midfield"
        elif half == side:
            spot = "their own %d" % n
        else:
            spot = "the %s %d" % (self.team(half), n)
        self.new_possession = side != self.ball_side or kind != "ball"
        self.ball_side = side
        if kind == "ball" and self.new_possession:
            kind = "ball_new"
        self.marks = self.countdown = None
        return kind, self.pick(kind, {"t": self.team(side), "spot": spot})

    def _r_ball(self, v):
        return self._ball(v, "ball")

    def _r_ball_turnover(self, v):
        return self._ball(v, "ball_turnover")

    def _r_ball_downs(self, v):
        return self._ball(v, "ball_downs")

    def _r_down(self, v):
        down = ORDINAL[v["d"].lower()]
        n = int(v["n"])
        values = {"n": str(n), "t": self.team(self.ball_side or self.side_with_ball())}
        gained = not self.new_possession and self.action != "incomplete"      # a first down the offense earned (a penalty's too)
        if down == 1:
            key = ("first_gained" if n == 10 else "first_gained_n") if gained else "first"
        elif down == 2:
            key = "second_short" if n <= 3 else "second_long" if n >= 10 else "second"
        elif down == 3:
            key = "third_short" if n <= 2 else "third_long" if n >= 8 else "third"
        else:
            key = "fourth"
        self.action = None
        self.new_possession = False
        return key, self.pick(key, values)

    def _r_down_goal(self, v):
        down = ORDINAL[v["d"].lower()]
        gained = not self.new_possession and self.action in ("run", "catch")
        key = {1: "first_goal_gained" if gained else "first_goal", 2: "second_goal", 3: "third_goal", 4: "fourth_goal"}[down]
        self.action = None
        self.new_possession = False
        return key, self.pick(key, {"t": self.team(self.ball_side or self.side_with_ball())})

    def _r_mark(self, v):
        """A bare yard number: the touchdown countdown or a return's markers; any other number is said as it is."""
        n = v["n"]
        if self.countdown is not None:
            self.countdown += 1
            if self.countdown == 1 or int(n) < 10:
                return "mark", n + "!"
            return "mark", "the " + n + "!"
        if self.marks is not None:
            self.marks += 1
            return "mark", "the " + n + ("!" if self.marks >= MARKS_EXCITED else ",")
        return None

    # ----- the parts -----

    def side_with_ball(self) -> int:
        state = getattr(self.b, "state", None)
        return getattr(state, "wisoff", 0) or self.ball_side or 1

    def team(self, side: int) -> str:
        state = getattr(self.b, "state", None)
        teams = getattr(state, "teams", None) or {}
        name = str(teams.get(side, "") or "").strip()
        return name or ("home team" if side == 1 else "visitors")

    def pick(self, key: str, values: dict[str, str]) -> str:
        """One variant of the call, never the one said last for it while it has others, with the values filled in."""
        variants = CALLS[key]
        index = self.rnd.randrange(len(variants))
        if len(variants) > 1 and index == self.last.get(key):
            index = (index + 1 + self.rnd.randrange(len(variants) - 1)) % len(variants)
        self.last[key] = index
        text = variants[index]
        for name, value in values.items():
            text = text.replace("{" + name + "}", value)
        return text[:1].upper() + text[1:] if not text.startswith(("and ", "before ", "is ", "in the ")) else text

    def game_over(self) -> None:
        if self.game is not None:
            log.info("radio calls: %d calls this game", self.calls)
