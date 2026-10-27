"""The radio broadcast: a crew of three in a radio format, in both modes (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

CLAUDE.md 0.27 as amended on 2026-10-26 (the owner: the original's commentary goes from every mode; a made-up radio crew is the only
commentary), 0.33 (real broadcasts are the model: spec/RADIO_NFL_STYLE.md), playbook 7.19 and 7.24, D-101, D-178, D-179, D-180, D-189.
The design is spec/NFL_BROADCAST_DESIGN.md (sections 3 to 7, 10 and 11; BC.3 built it).

The crew (extras/crew.py, renamable in F9, Rules, Broadcast crew):
    Walt Kessler, play-by-play   the announcer's voice (say5: asynchronous, logged, never replayed by F2): the sign-on (SGN), the crew
                                 (CRW), the asides (BN), the network's identification (NID, once a game a listener's LID), the score
                                 reset (UPD), the quarter and half updates (QUP), the station breaks (STA), the hand-offs (ASK, ASN), the
                                 drive summary (DRV) and the clock late in a half (CLK) with the N. F. L. rules' real clock, the sign-off (SGO)
    Gus Delgado, color analyst   his own voice (speech/roles.COLOR): a reason after some plays and at the moments of D-101 (the C pools)
    Nora Banks, sideline report  her own voice (speech/roles.SIDELINE): before the kick-off (SON), at a Franchise game's injury (SIN), at half
                                 time (SHT)

The switches: F8 (the comments) silences all of it; F9, Rules, Broadcast switches Gus and Nora (and Walt's hand-offs to them) off, while
Walt's sign-on, identifications, updates, breaks and sign-off stay with the comments on (the lines of those pools that name the analyst or the
reporter are then left out of the draw).

The broadcast never changes the game: it draws only from its OWN random generator (seeded from the game's seed, so a session can be replayed),
never from the game's, it changes no state, no score, no clock and no sound, and every line is asynchronous so the first key (or T) cuts it.
A pool never gives the same line twice in a game while it has others (rule 0.28 (3)). The game's own score sentence after a score is the
score update there (rule 0.28 (3): Walt does not say it again right after); Walt resets the score at a dead ball when it has not been said
for a while, as the real calls do (RADIO_NFL_STYLE 2: a score every 3.3 minutes).

The modes: the N. F. L. rules call it from their hooks (extras/nfl_rules.py), Classic from its own rules object with only the broadcast
(extras/classic_radio.py); the bare Classic rules of the engine (game/rules.CLASSIC: the golden transcript) say nothing. The drive summary and
the clock need the real clock and are said only with the N. F. L. rules (Classic's time is made up from the play counter with a draw of the
game's generator, which the broadcast must never make).
"""
from __future__ import annotations

import logging
import random
from types import SimpleNamespace

from ..game import outcome as O
from ..game.gamestate import other, own_half
from ..game.rnd import GameRandom
from ..speech.roles import ANNOUNCER, COLOR, CREW_ROLES, EXTRA_ROLES, SIDELINE
from . import commentators
from . import crew
from . import nx_texts as X
from . import remarks

log = logging.getLogger("nfl4.extras")

# The chance in percent of the analyst at each kind of moment (his pool), and how often the announcer turns to him first.
# The owner, 2026-10-25 (Q-043): "Talks too much". Measured 26.5 lines a game (work\sr4\ghip_rate.py, 12 games); the ordinary moments' chances,
# the gap and the announcer's turn to him were lowered to about half that (the kick-off, half time and the final whistle stay). Was: CTD 85, CFG 55,
# CFM 70, CTV 80, CBG 60, CSK 40, CTC 15, CTS 15, CFD 70, CRZ 35, CPN 30, CTM 75, CQE 60, CTT 60, CBO 50; ASK_CHANCE 40; MIN_GAP 2.
CHANCE = {"CKO": 100, "CTD": 60, "CFG": 30, "CFM": 40, "CTV": 45, "CBG": 30, "CSK": 20, "CTC": 8, "CTS": 8, "CFD": 40, "CRZ": 15, "CPN": 15,
          "CTM": 45, "CQE": 35, "CHT": 100, "CFN": 100, "CFT": 100, "CTT": 35, "CBO": 25}
ASK_CHANCE = 25
MAJOR = frozenset(("CKO", "CTD", "CHT", "CFN", "CFT"))        # these never wait for the gap below
MIN_GAP = 4                                                    # plays between two ordinary lines of the analyst
BIG_GAIN = 20                                                  # yards: CBG
CLOSE_MARGIN, DECIDED_MARGIN = 3, 21                           # CTT in the fourth quarter, CBO in the second half
SEED_MIX = 0x6B1B_0C0F                                         # the broadcast's seed is the game's seed mixed with this
QUARTER_WORDS = {1: "first quarter", 2: "second quarter", 3: "third quarter", 4: "fourth quarter"}
HALF_WORDS = "first half"                                      # QUP at half time
THIRD_DOWN_KINDS = (O.RUN, O.PASS_COMPLETE, O.PASS_INCOMPLETE, O.SACK)
KICK_PLAYS = (6, 7)                                            # the engine's Field Goal and Punt, not a gamble on fourth down

# BC.3 (design 4 and 11, RADIO_NFL_STYLE 2): Walt's rates, in game time and plays
ASIDE_ONE_IN = 8               # BN: about one dead ball in eight ...
ASIDE_GAP = 4                  # ... never twice in four plays
NETWORK_EVERY = 420            # NID: about every seven minutes of game time (the modern call: 6.8 minutes)
LISTENER_ONE_IN = 4            # LID: one network identification in four may be a listener's, once a game, only with the commercials off
SCORE_RESET_AFTER = 360        # UPD: the score said again when nobody said it for six minutes of game time ...
SCORE_RESET_ONE_IN = 2         # ... at one dead ball in two
LATE_SECONDS = 120             # CLK: the last two minutes of the second and fourth quarters (the N. F. L. rules' real clock)
CLOCK_GAP = 2                  # CLK: at most every second play
DRIVE_ONE_IN = 3               # DRV: about one score in three
DRIVE_MIN = 2                  # DRV: a drive of at least two plays, two yards and two minutes ("1 minutes" is not said)
QUARTER_SECONDS = 900

WALT_POOLS = ("SGN", "CRW", "BN", "ASK", "ASN", "UPD", "QUP", "STA", "NID", "LID", "DRV", "CLK", "SGO")
NORA_POOLS = ("SON", "SIN", "SHT")
CREW_WORDS = ("<analyst>", "<commentator>", "<sideline>")      # a line that names Gus or Nora: left out while the Broadcast item is off


class Facts:
    """What the last play was, kept from the end of its narration until the next dead-ball moment."""

    def __init__(self, state, outcome):
        self.kind = outcome.kind
        self.offense = outcome.offense
        self.yards = outcome.yards
        self.turnover = bool(outcome.turnover)
        self.score = outcome.score
        self.two_point = bool(outcome.two_point_try)
        self.taken_over = getattr(outcome, "then", None) is not None   # a penalty or a review took the play over: no line for it
        self.down, self.to_go = state.down, state.to_go      # at the snap (the narration end point is before the downs)
        self.consumed = False


class Drive:
    """The possession that is going on: who has the ball, from how far out it began, when, and how many snaps (DRV)."""

    def __init__(self, side: int, to_goal: int, seconds: int):
        self.side, self.start_to_goal, self.start_seconds = side, to_goal, seconds
        self.last_to_goal = to_goal
        self.plays = 0


def to_goal(state) -> int:
    """The yards from the line of scrimmage to the defense's goal line."""
    return 100 - state.yard_line if state.half == own_half(state.wisoff) else state.yard_line


def time_words(seconds: int) -> str:
    """A spoken time: "1 minute and 10 seconds", "2 minutes", "45 seconds"."""
    minutes, rest = divmod(max(0, int(seconds)), 60)
    parts = []
    if minutes:
        parts.append("%d minute%s" % (minutes, "" if minutes == 1 else "s"))
    if rest or not minutes:
        parts.append("%d second%s" % (rest, "" if rest == 1 else "s"))
    return " and ".join(parts)


class Broadcast:
    def __init__(self, rules, analyst: bool = False, commentator: str = "", crew_names: dict | None = None):
        self.rules = rules
        self.analyst = bool(analyst)                # Gus, Nora and Walt's hand-offs to them (F9, Rules, Broadcast)
        names = dict(crew.DEFAULTS)
        names.update(crew_names or {})
        if commentator:
            names[crew.ANALYST] = commentator        # SZ.1's argument: the analyst's name
        self.names = {role: crew.name_of_text(role, names[role]) for role in crew.ROLES}
        self.game = None
        self.state = None
        self.clock = None
        self.rnd: GameRandom | None = None
        self._reset()

    def _reset(self) -> None:
        self.facts: Facts | None = None
        self.since = MIN_GAP
        self.opened = False
        self.red_zone_side = 0
        self.spoken = 0                              # how many lines of the crew this game (the log says it at the end)
        self.plays = 0                               # the plays told this game (note_outcome)
        self.handled = -1                            # the play whose dead ball was last handled (between)
        self.aside_since = ASIDE_GAP
        self.clock_since = CLOCK_GAP
        self.last_id = 0                             # game seconds of the last identification of the network
        self.listener_done = False
        self.score_said = 0                          # game seconds when the score was last said
        self.drive: Drive | None = None
        self.hurt: tuple[str, int] | None = None     # a Franchise game's man who was hurt: (name, side), Nora reports at the dead ball
        self.used: dict[str, set[str]] = {}
        self.signed_off = False
        self.own_record = SimpleNamespace(recent={})  # Classic has no extras record: the last lines of each pool are kept here

    # ----- the names (extras/crew.py) -----

    @property
    def commentator(self) -> str:
        """The analyst's name (SZ.1's attribute)."""
        return self.names[crew.ANALYST]

    @commentator.setter
    def commentator(self, name: str) -> None:
        self.names[crew.ANALYST] = commentators.name_of_text(name)

    def crew_values(self) -> dict[str, str]:
        return crew.placeholders(self.names)

    # ----- the game -----

    def attach(self, game, state, clock=None) -> None:
        """A new game: its own generator, seeded from the game's seed (or a fixed one when the game's source was given, as in tests)."""
        self.game, self.state, self.clock = game, state, clock
        seed = getattr(getattr(game, "rnd", None), "seed", None)
        self.rnd = GameRandom(random.Random((seed if seed is not None else 0x5EED) ^ SEED_MIX))
        self._reset()
        if self.analyst:
            self._own_voice()                         # starts the reading of the voice list when it is needed; the opening takes the voice

    def on_air(self) -> bool:
        """Walt may speak: the game has begun and the comments are on (F8)."""
        return bool(self.game is not None and self.rnd is not None and getattr(self.game, "comtog", 0) == 0)

    def active(self) -> bool:
        """Gus and Nora may speak: on the air and the Broadcast item is on."""
        return self.analyst and self.on_air()

    # ----- what the engine tells -----

    def note_outcome(self, state, outcome) -> None:
        self.facts = Facts(state, outcome)
        self.since += 1
        self.plays += 1
        self.aside_since += 1
        self.clock_since += 1

    def kickoff(self, state) -> None:
        """Before every kick-off: a new possession follows; before the opening one, the sign-on."""
        self.drive = None
        self.opening(state)

    def before_snap(self, state, offense_play: int) -> None:
        """Every snap: the drive is counted (no draw, no word); the analyst when a team goes for it on fourth down."""
        if not state.two_point:
            here = to_goal(state)
            if self.drive is None or self.drive.side != state.wisoff:
                self.drive = Drive(state.wisoff, here, self.game_seconds(state))
            self.drive.plays += 1
            self.drive.last_to_goal = here
        if not self.active() or state.down != 4 or state.two_point or offense_play in KICK_PLAYS or offense_play == 0:
            return
        self._try(state, "CFD", self._values(state, state.wisoff))

    def penalty(self, state, side: int) -> None:
        if self.active():
            self._try(state, "CPN", self._values(state, side))

    def injury(self, state, name: str, side: int) -> None:
        """A man of a Franchise game was hurt (the announcer has said so): Nora reports at the dead ball."""
        if self.active() and name:
            self.hurt = (name, side)

    # ----- the sign-on -----

    def opening(self, state) -> None:
        """Before the opening kick-off of a game: Walt's sign-on and the crew, Nora's note from the field, Gus's first thought."""
        x = getattr(state, "extras", None)
        played = x.plays if x is not None else max(0, state.counter - 1)
        if (self.opened or not self.on_air() or state.quarter != 1 or played != 0 or self.plays != 0
                or state.score(1) or state.score(2)):
            return
        self.opened = True
        g = self.game
        self._own_voice()
        values = self._values(state, 1)
        self._line(state, "SGN", values, g.say5)
        if self.active():
            self._line(state, "CRW", values, g.say5)
            if not getattr(g, "crew_introduced", False):          # once per program run: where the crew's voices and names are set
                g.crew_introduced = True
                g.say5(X.text("NXB-B01"))
            self._line(state, "SON", values, self._nora)
            self._say(state, "CKO", values, ask=False)
        self.last_id = self.score_said = self.game_seconds(state)

    def _own_voice(self) -> None:
        """The analyst, the reporter and the referee get a voice of their own the first time a game opens, when the player has not chosen
        one (F12): the next voice of the announcer's engine that nobody uses, else the next voice of the list. Done once the voice list is
        read (the game starts the reading in the background); until then they share the announcer's voice. The choice is saved like the
        player's own, so F12 shows it. Classic has no referee: only the crew's two. The voices carry no gender in the list the game reads, so
        the reporter gets the next free voice as the analyst does (D-189)."""
        roles = EXTRA_ROLES if getattr(self.rules, "name", "") != "Classic" else CREW_ROLES
        try:
            options = getattr(self.game, "options", None)
            if options is None or all(options.voice(role) for role in roles):
                return
            if getattr(getattr(self.game, "speech", None), "screen_reader_speaks", lambda: False)():
                return                                   # SZ.4: a screen reader's one voice speaks them; no voice list is read, none is saved
            catalog = getattr(options, "voice_catalog", None)
            if catalog is None:
                return
            if not catalog.loaded:
                catalog.load_async()
                return
            voices = list(catalog.voices(timeout=0.0))
            if len(voices) < 2:
                return
            current_id = options.voice(ANNOUNCER) or voices[0].voice_id
            current = next((v for v in voices if v.voice_id == current_id), voices[0])
            changed = False
            for role in roles:
                if options.voice(role):
                    continue
                used = {current.voice_id} | {options.voice(r) for r in EXTRA_ROLES if options.voice(r)}
                others = [v for v in voices if v.voice_id not in used]
                if not others:
                    continue
                pick = next((v for v in others if v.engine == current.engine), others[0])
                options.set_voice(role, pick.voice_id)
                changed = True
                log.info("broadcast: %s gets the own voice %r (the announcer has %r)", role, pick.name, current.name)
            if changed:
                options.save()
        except Exception as exc:
            log.warning("broadcast: the voices of the crew could not be chosen: %s", exc)

    # ----- the dead ball -----

    def between(self, state) -> None:
        """After the down sentence, before the next menu, once per play: Nora's injury report, Gus's line about the play, then at most one
        line of Walt's (the clock late in a half, the network, the score, an aside)."""
        if self.handled == self.plays:
            return
        self.handled = self.plays
        reported = self._injury_report(state)
        timed = self.on_air() and self._clock_line(state)    # late in a half the time comes first, then the analyst
        analyst = self._play_line(state)
        if not self.on_air() or reported or timed or analyst:
            return
        self._walt_filler(state)

    def _play_line(self, state) -> bool:
        """The last play's line of the analyst, in the order of what matters most."""
        f = self.facts
        if f is None or f.consumed:
            return False
        f.consumed = True
        if not self.active() or f.two_point or f.taken_over:
            return False
        side = f.offense
        if f.turnover and f.kind in (O.INTERCEPTION, O.FUMBLE):
            pool = "CTV"
        elif f.kind in (O.RUN, O.PASS_COMPLETE) and f.yards >= BIG_GAIN and not f.score:
            pool, side = "CBG", f.offense
        elif f.kind == O.SACK:
            pool = "CSK"
        elif f.kind in (O.FIELD_GOAL_MISSED, O.FIELD_GOAL_SHORT):
            pool = "CFM"
        elif f.down == 3 and f.kind in THIRD_DOWN_KINDS and not f.score:
            pool = "CTC" if f.kind in (O.RUN, O.PASS_COMPLETE) and f.yards >= f.to_go else "CTS"
        else:
            pool = self._red_zone(state)
            side = state.wisoff
            if pool is None:
                return False
        return self._try(state, pool, self._values(state, side, yards=f.yards))

    def _injury_report(self, state) -> bool:
        if self.hurt is None:
            return False
        (name, side), self.hurt = self.hurt, None
        if not self.active():
            return False
        values = dict(self._values(state, side), **{"<player>": name})
        self._line(state, "ASN", values, self.game.say5)
        return self._line(state, "SIN", values, self._nora) is not None

    def _clock_line(self, state) -> bool:
        """The N. F. L. rules' last two minutes of a half: the time left after every second play (the classic call says it every play)."""
        left = self._late_seconds(state)
        if left is None or state.two_point or self.clock_since < CLOCK_GAP:
            return False
        values = dict(self._values(state, state.wisoff), **{"<time>": time_words(left)})
        if self._line(state, "CLK", values, self.game.say5) is None:
            return False
        self.clock_since = 0
        self.score_said = self.game_seconds(state)
        return True

    def _walt_filler(self, state) -> None:
        if self._late(state):
            return                                           # the last two minutes of a half belong to the situation and the clock
        now = self.game_seconds(state)
        values = self._values(state, state.wisoff)
        if now - self.last_id >= NETWORK_EVERY:
            self.last_id = now
            if not self.listener_done and not self._commercials_on() and self.rnd(LISTENER_ONE_IN) == 1:
                self.listener_done = True
                self._line(state, "LID", values, self.game.say5)
            else:
                self._line(state, "NID", values, self.game.say5)
            return
        scored = state.score(1) or state.score(2)            # "tied at 0" is not said: a score reset needs a score
        if scored and now - self.score_said >= SCORE_RESET_AFTER and self.rnd(SCORE_RESET_ONE_IN) == 1:
            if self._line(state, "UPD", values, self.game.say5) is not None:
                self.score_said = now
            return
        if self.aside_since >= ASIDE_GAP and self.rnd(ASIDE_ONE_IN) == 1:
            if self._line(state, "BN", {}, self.game.say5) is not None:
                self.aside_since = 0

    # ----- the moments (the engine's hook H23, broadcast_moment) -----

    def moment(self, state, what: str, quarter: int = 0) -> None:
        if not self.on_air():
            return
        f = self.facts
        if what == "touchdown":                           # right after the six points: the scorer has the ball (state.wisoff)
            self._drive_summary(state, touchdown=True)
            self._try(state, "CTD", self._values(state, state.wisoff))
        elif what == "score":                             # after_score: the game has just said the score (a field goal, a safety, a try)
            if f is not None:
                f.consumed = True
            self.score_said = self.game_seconds(state)
            if state.points == 3:
                self._drive_summary(state, touchdown=False)
                self._try(state, "CFG", self._values(state, state.wisoff))
        elif what == "two_minute":
            self._try(state, "CTM", self._values(state, state.wisoff))
        elif what == "two_minute_break":                  # before the commercial slot of rule 0.14 at the two-minute warning
            self._station_break(state)
        elif what == "quarter_end":
            self._quarter_end(state, quarter)
        elif what == "half_time_break":                   # before the half time's commercial slot: Nora, Gus, then Walt's break
            if self.active():
                values = self._half_values(state)
                self._line(state, "ASN", values, self.game.say5)
                self._line(state, "SHT", values, self._nora)
                self._try(state, "CHT", self._values(state, 1))
            self._station_break(state)
        elif what == "final_score":                       # after the game's final score sentence: Gus, then Walt signs off
            self._game_end(state)
            if not self.signed_off:
                self.signed_off = True
                self._line(state, "SGO", self._values(state, 1), self.game.say5)
                log.info("broadcast: signed off after %d lines of the crew and %d plays", self.spoken, self.plays)

    def _station_break(self, state) -> None:
        self._line(state, "STA", self._values(state, state.wisoff), self.game.say5)
        self.last_id = self.game_seconds(state)

    def _quarter_end(self, state, quarter: int) -> None:
        if quarter not in (1, 2, 3):
            return
        values = self._values(state, 1, quarter=quarter)
        if quarter == 2:
            values["<quarter>"] = HALF_WORDS
        if self._line(state, "QUP", values, self.game.say5) is not None:
            self.score_said = self.game_seconds(state)
        if quarter == 2:
            return                                         # Gus speaks at the half time break
        margin = abs(state.score(1) - state.score(2))
        pool = "CQE"
        if quarter == 3 and margin <= CLOSE_MARGIN:
            pool = "CTT"
        elif quarter == 3 and margin >= DECIDED_MARGIN:
            pool = "CBO"
        self._try(state, pool, self._values(state, 1, quarter=quarter))

    def _game_end(self, state) -> None:
        a, b = state.score(1), state.score(2)
        if a == b:
            self._try(state, "CFT", self._values(state, 1))
        else:
            self._try(state, "CFN", self._values(state, 1 if a > b else 2))

    def _drive_summary(self, state, touchdown: bool) -> None:
        """DRV (the N. F. L. rules only): the plays, yards and minutes of the drive that scored, about once in three scores."""
        d = self.drive
        if d is None or d.side != state.wisoff or self._real_left() is None:
            return
        yards = d.start_to_goal if touchdown else d.start_to_goal - d.last_to_goal
        seconds = self.game_seconds(state) - d.start_seconds
        minutes = (seconds + 30) // 60
        if d.plays < DRIVE_MIN or yards < DRIVE_MIN or minutes < DRIVE_MIN or self.rnd(DRIVE_ONE_IN) != 1:
            return
        values = dict(self._values(state, d.side), **{"<plays>": str(d.plays), "<yards>": str(yards), "<minutes>": str(minutes)})
        self._line(state, "DRV", values, self.game.say5)

    def _red_zone(self, state) -> str | None:
        """The offense is inside the opponent's twenty for the first time in this possession."""
        side = state.wisoff
        if not state.in_own_half() and 1 <= state.yard_line <= 20:
            if self.red_zone_side == side:
                return None
            self.red_zone_side = side
            return "CRZ"
        if self.red_zone_side not in (0, side):        # the other team has the ball now: its next trip inside is a new one
            self.red_zone_side = 0
        return None

    # ----- the clock (no draw: Classic's time comes from its play counter without its drawn seconds) -----

    def _real_left(self) -> int | None:
        """The seconds left in the period with the N. F. L. rules' real clock; None in Classic or without a clock."""
        x = getattr(self.state, "extras", None)
        left = getattr(x, "left", None)
        return left if isinstance(left, int) else None

    def game_seconds(self, state) -> int:
        """The game time gone, in seconds (the network's identification and the score reset count it). Classic counts whole minutes."""
        quarter = max(1, min(getattr(state, "quarter", 1), 5))
        left = None
        try:
            if self.clock is not None:
                minutes, seconds = self.clock.summary_left()
                left = minutes * 60 + (seconds or 0)
        except Exception as exc:
            log.debug("broadcast: no time from the clock: %s", exc)
        if left is None:
            return self.plays * 30
        return QUARTER_SECONDS * (quarter - 1) + max(0, QUARTER_SECONDS - left)

    def _late_seconds(self, state) -> int | None:
        """The seconds left when the N. F. L. rules' clock is in the last two minutes of the second or fourth quarter, else None."""
        left = self._real_left()
        if left is None or state.quarter not in (2, 4) or not 0 < left < LATE_SECONDS:
            return None          # 2:00 itself is the game's two-minute warning
        return left

    def _late(self, state) -> bool:
        """The last two minutes of a half (and the end of an overtime period): no identification, no score reset, no aside."""
        left = self._real_left()
        if left is not None:
            return left <= LATE_SECONDS and (state.quarter in (2, 4) or state.quarter >= 5)
        try:
            return bool(self.clock is not None and self.clock.warning_zone())
        except Exception:
            return False

    def _commercials_on(self) -> bool:
        options = getattr(self.game, "options", None)
        audio = getattr(getattr(options, "settings", None), "audio", None)
        return getattr(audio, "commercials", "off") != "off"

    # ----- the lines -----

    def _values(self, state, side: int, yards: int = 0, quarter: int = 0) -> dict[str, str]:
        g = self.game
        vtrnt = getattr(getattr(g, "season", None), "vtrnt", 2)
        visitors, home = (1, 2) if vtrnt != 1 else (2, 1)
        values = {"<team>": state.teams.get(side, ""), "<opponent>": state.teams.get(other(side), ""),
                  "<coach>": getattr(getattr(g, "season", None), "coach", ""),
                  "<quarterback>": state.quarterbacks.get(side, ""), "<yards>": str(abs(yards)),
                  "<quarter>": QUARTER_WORDS.get(quarter or min(state.quarter, 4), "overtime"),
                  "<situation>": self.situation(state),
                  "<visitors>": state.teams.get(visitors, ""), "<home>": state.teams.get(home, "")}
        return values

    def _half_values(self, state) -> dict[str, str]:
        """Nora at half time: <team> the team that leads (the home team when it is tied), <opponent> the other."""
        a, b = state.score(1), state.score(2)
        vtrnt = getattr(getattr(self.game, "season", None), "vtrnt", 2)
        lead = 1 if a > b else 2 if b > a else (1 if vtrnt == 1 else 2)
        return self._values(state, lead)

    @staticmethod
    def situation(state) -> str:
        """A clause with the score: the Bengals lead the Jets 17 to 10, the Bengals and the Jets are tied at 14."""
        t1, t2 = state.teams.get(1, ""), state.teams.get(2, "")
        a, b = state.score(1), state.score(2)
        if a == b:
            return "the %s and the %s are tied at %d" % (t1, t2, a)
        (lead, trail, high, low) = (t1, t2, a, b) if a > b else (t2, t1, b, a)
        return "the %s lead the %s %d to %d" % (lead, trail, high, low)

    def _record(self, state):
        x = getattr(state, "extras", None)
        return x if x is not None and isinstance(getattr(x, "recent", None), dict) else self.own_record

    def _exclude(self, pool: str) -> tuple[str, ...]:
        """The lines not to draw now: the ones said this game while others are left (rule 0.28 (3)), and with the Broadcast item off the
        ones that name the analyst or the reporter."""
        pools = getattr(self.game, "remark_pools", None) or remarks.DEFAULT_POOLS
        lines = pools.lines(pool)
        crewless = set() if self.analyst else {r.id for r in lines if any(word in r.markup for word in CREW_WORDS)}
        used = self.used.get(pool, set())
        left = [r for r in lines if r.id not in crewless and r.id not in used]
        if not left:
            self.used[pool] = set()
            used = set()
        return tuple(sorted(crewless | used))

    def _nora(self, text: str) -> None:
        self.game.say_role(text, SIDELINE)

    def _gus(self, text: str) -> None:
        self.game.say_role(text, COLOR)

    def _line(self, state, pool: str, values: dict[str, str], say) -> remarks.Remark | None:
        """One line of a pool, said by `say`; None when nothing was said."""
        if not self.on_air():
            return None
        if pool not in WALT_POOLS and not self.active():
            return None
        said = remarks.say_remark(self.game, state, self._record(state), pool, values, say=say, exclude=self._exclude(pool), rnd=self.rnd)
        if said is not None:
            self.used.setdefault(pool, set()).add(said.id)
            self.spoken += 1
            log.info("broadcast: %s says %s (%s) after %d plays", self._speaker(pool), said.id, pool, self.plays)
        return said

    def _speaker(self, pool: str) -> str:
        if pool in NORA_POOLS:
            return "the reporter (%s)" % self.names[crew.SIDELINE]
        if pool in WALT_POOLS:
            return "the announcer (%s)" % self.names[crew.ANNOUNCER]
        return "the analyst (%s)" % self.names[crew.ANALYST]

    def _try(self, state, pool: str, values: dict[str, str]) -> bool:
        if not self.active() or (pool not in MAJOR and self.since < MIN_GAP):
            return False
        if self.rnd(100) > CHANCE[pool]:
            return False
        self._say(state, pool, values)
        return True

    def _say(self, state, pool: str, values: dict[str, str], ask: bool = True) -> None:
        if pool in ("CFN", "CFT"):
            values = dict(values, **{"<situation>": self._final_clause(state)})
        if ask and self.rnd(100) <= ASK_CHANCE:
            self._line(state, "ASK", {}, self.game.say5)
        if self._line(state, pool, values, self._gus) is not None:
            self.since = 0

    @staticmethod
    def _final_clause(state) -> str:
        t1, t2 = state.teams.get(1, ""), state.teams.get(2, "")
        a, b = state.score(1), state.score(2)
        if a == b:
            return "the %s and the %s tied at %d" % (t1, t2, a)
        winner, loser, high, low = (t1, t2, a, b) if a > b else (t2, t1, b, a)
        return "the %s beat the %s %d to %d" % (winner, loser, high, low)
