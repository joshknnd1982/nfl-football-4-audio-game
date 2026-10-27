"""The radio-style broadcast of the N. F. L. rules mode: the color analyst (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

CLAUDE.md 0.27 as amended on 2026-10-26 (the owner: the original's commentary goes from every mode; a made-up radio crew is the only
commentary), playbook 7.19, D-101, D-178. BC.2 (D-180) removed the original's banter step and with it the pool BN drawn by the
original's rule on the game's generator (the Rules hook H23 banter_lines is gone); BC.3 brings the play-by-play announcer's asides
(pool BN), the sideline reporter and the radio format back on the broadcast's own generator (spec/NFL_BROADCAST_DESIGN.md).

The analyst: after some plays and at some moments (the opening kick-off, a touchdown, a turnover, a big gain, a sack, a missed kick, a
third down, a fourth-down gamble, the red zone, a penalty, the two-minute warning, the end of the first and third quarters, half time, a
close or a decided game, the final whistle) the color analyst adds one line from his pool in a voice of his own (speech/roles.COLOR), and
the announcer sometimes turns to him first (pool ASK). A line is said asynchronously, never replayed by F2, and the first key (or T) cuts it.

The broadcast never changes the game: it draws only from its OWN random generator (seeded from the game's seed, so a session can be replayed),
never from the game's, it changes no state and no sound, and the Classic rules never call it (the hooks H23 answer nothing there). F8 (comments
off) silences it; F9, Rules, Broadcast switches the analyst and the ASK lines off.
"""
from __future__ import annotations

import logging
import random

from ..game import outcome as O
from ..game.gamestate import other
from ..game.rnd import GameRandom
from ..speech.roles import ANNOUNCER, COLOR, EXTRA_ROLES
from . import commentators
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
THIRD_DOWN_KINDS = (O.RUN, O.PASS_COMPLETE, O.PASS_INCOMPLETE, O.SACK)
KICK_PLAYS = (6, 7)                                            # the engine's Field Goal and Punt, not a gamble on fourth down


class Facts:
    """What the last play was, kept from the end of its narration until the next dead-ball moment."""

    def __init__(self, state, outcome):
        self.kind = outcome.kind
        self.offense = outcome.offense
        self.yards = outcome.yards
        self.turnover = bool(outcome.turnover)
        self.score = outcome.score
        self.two_point = bool(outcome.two_point_try)
        self.taken_over = outcome.then is not None          # a penalty or a review took the play over: no line for it
        self.down, self.to_go = state.down, state.to_go      # at the snap (the narration end point is before the downs)
        self.consumed = False


class Broadcast:
    def __init__(self, rules, analyst: bool = False, commentator: str = commentators.DEFAULT):
        self.rules = rules
        self.analyst = bool(analyst)                # the analyst and the announcer's questions (F9, Rules, Broadcast)
        self.commentator = commentators.name_of_text(commentator)      # SZ.1, BC.2: his name (F9, Rules, Commentator); Gus Delgado by default
        self.game = None
        self.rnd: GameRandom | None = None
        self.facts: Facts | None = None
        self.since = MIN_GAP
        self.opened = False
        self.red_zone_side = 0
        self.spoken = 0                              # how many lines of the analyst this game (the log says it at the end)

    # ----- the game -----

    def attach(self, game, state) -> None:
        """A new game: its own generator, seeded from the game's seed (or a fixed one when the game's source was given, as in tests)."""
        self.game = game
        seed = getattr(getattr(game, "rnd", None), "seed", None)
        self.rnd = GameRandom(random.Random((seed if seed is not None else 0x5EED) ^ SEED_MIX))
        self.facts, self.since, self.opened, self.red_zone_side, self.spoken = None, MIN_GAP, False, 0, 0
        if self.analyst:
            self._own_voice()                         # starts the reading of the voice list when it is needed; the opening takes the voice

    def active(self) -> bool:
        """The analyst may speak: the broadcast is on, the game has begun and the comments are on (F8)."""
        return bool(self.analyst and self.game is not None and self.rnd is not None and self.game.comtog == 0)

    # ----- what the engine tells -----

    def note_outcome(self, state, outcome) -> None:
        self.facts = Facts(state, outcome)
        self.since += 1

    def opening(self, state) -> None:
        """Before the opening kick-off of the game: the announcer says once per program run who is in the booth, then the analyst's opening line."""
        x = state.extras
        if self.opened or not self.active() or state.quarter != 1 or x is None or x.plays != 0:
            return
        self.opened = True
        g = self.game
        self._own_voice()
        if not getattr(g, "analyst_introduced", False):
            g.analyst_introduced = True
            g.say5(X.text("NXB-B01", commentator=self.commentator))
        self._say(state, "CKO", self._values(state, 1), ask=False)

    def _own_voice(self) -> None:
        """The analyst and the referee get a voice of their own the first time a game opens, when the player has not chosen one (F12): the next
        voice of the announcer's engine that nobody uses, else the next voice of the list. Done once the voice list is read (the game
        starts the reading in the background); until then they share the announcer's voice. The choice is saved like the player's own,
        so F12 shows it."""
        try:
            options = getattr(self.game, "options", None)
            if options is None or all(options.voice(role) for role in EXTRA_ROLES):
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
            for role in EXTRA_ROLES:
                if options.voice(role):
                    continue
                used = {current.voice_id} | {options.voice(r) for r in EXTRA_ROLES if options.voice(r)}
                others = [v for v in voices if v.voice_id not in used]
                if not others:
                    continue
                pick = next((v for v in others if v.engine == current.engine), others[0])
                options.set_voice(role, pick.voice_id)
                changed = True
                log.info("broadcast: %s gets his own voice %r (the announcer has %r)", role, pick.name, current.name)
            if changed:
                options.save()
        except Exception as exc:
            log.warning("broadcast: the voices of the analyst and the referee could not be chosen: %s", exc)

    def before_snap(self, state, offense_play: int) -> None:
        if not self.active() or state.down != 4 or state.two_point or offense_play in KICK_PLAYS or offense_play == 0:
            return
        self._try(state, "CFD", self._values(state, state.wisoff))

    def penalty(self, state, side: int) -> None:
        if self.active():
            self._try(state, "CPN", self._values(state, side))

    def between(self, state) -> None:
        """After the down sentence, before the next menu: the last play's line, in the order of what matters most."""
        f = self.facts
        if f is None or f.consumed:
            return
        f.consumed = True
        if not self.active() or f.two_point or f.taken_over:
            return
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
                return
        self._try(state, pool, self._values(state, side, yards=f.yards))

    def moment(self, state, what: str, quarter: int = 0) -> None:
        if not self.active():
            return
        f = self.facts
        if what == "touchdown":                           # right after the six points: the scorer has the ball (state.wisoff)
            self._try(state, "CTD", self._values(state, state.wisoff))
        elif what == "score":                             # after_score: a field goal (a try's point has its own after_score, said nothing about)
            if f is not None:
                f.consumed = True
            if state.points == 3:
                self._try(state, "CFG", self._values(state, state.wisoff))
        elif what == "two_minute":
            self._try(state, "CTM", self._values(state, state.wisoff))
        elif what == "quarter_end":
            self._quarter_end(state, quarter)
        elif what == "half_time":
            self._try(state, "CHT", self._values(state, 1))
        elif what == "game_end":
            self._game_end(state)

    # ----- the moments -----

    def _quarter_end(self, state, quarter: int) -> None:
        if quarter not in (1, 3):
            return
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

    # ----- the line -----

    def _values(self, state, side: int, yards: int = 0, quarter: int = 0) -> dict[str, str]:
        g = self.game
        values = {"<team>": state.teams.get(side, ""), "<opponent>": state.teams.get(other(side), ""), "<coach>": g.season.coach,
                  "<quarterback>": state.quarterbacks.get(side, ""), "<yards>": str(abs(yards)),
                  "<quarter>": QUARTER_WORDS.get(quarter or min(state.quarter, 4), "overtime"),
                  "<situation>": self.situation(state)}
        return values

    @staticmethod
    def situation(state) -> str:
        """A clause with the score: the Bengals lead the Jets 17 to 10, the Bengals and the Jets are tied at 14."""
        t1, t2 = state.teams.get(1, ""), state.teams.get(2, "")
        a, b = state.score(1), state.score(2)
        if a == b:
            return "the %s and the %s are tied at %d" % (t1, t2, a)
        (lead, trail, high, low) = (t1, t2, a, b) if a > b else (t2, t1, b, a)
        return "the %s lead the %s %d to %d" % (lead, trail, high, low)

    def _try(self, state, pool: str, values: dict[str, str]) -> bool:
        if not self.active() or (pool not in MAJOR and self.since < MIN_GAP):
            return False
        if self.rnd(100) > CHANCE[pool]:
            return False
        self._say(state, pool, values)
        return True

    def _say(self, state, pool: str, values: dict[str, str], ask: bool = True) -> None:
        g = self.game
        x = state.extras
        if pool in ("CFN", "CFT"):
            values = dict(values, **{"<situation>": self._final_clause(state)})
        if ask and self.rnd(100) <= ASK_CHANCE:
            remarks.say_remark(g, state, x, "ASK", {}, say=g.say5, rnd=self.rnd)
        said = remarks.say_remark(g, state, x, pool, values, say=lambda text: g.say_role(text, COLOR), rnd=self.rnd)
        if said is not None:
            self.since = 0
            self.spoken += 1
            log.info("broadcast: the analyst (%s) says %s (%s) after %d plays", self.commentator, said.id, pool, getattr(x, "plays", 0))

    @staticmethod
    def _final_clause(state) -> str:
        t1, t2 = state.teams.get(1, ""), state.teams.get(2, "")
        a, b = state.score(1), state.score(2)
        if a == b:
            return "the %s and the %s tied at %d" % (t1, t2, a)
        winner, loser, high, low = (t1, t2, a, b) if a > b else (t2, t1, b, a)
        return "the %s beat the %s %d to %d" % (winner, loser, high, low)
