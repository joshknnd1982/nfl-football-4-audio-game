"""A rig for whole games of pag on the virtual clock. This is inspired by Jim Kitchen.

tests/gamerig.py gives the Game with fake speech and the real sound layer on a silent TimedOutput. Here:
* PolicyKeys: scripted answers first, then a policy chooses the key at every wait (so a whole game can be played
  without knowing how many waits it has);
* a fast mode for the many-game tests: a pause moves the virtual clock at once and a waited sound is polled every
  20 ms of virtual time instead of every millisecond (the order of everything stays the same; only the number of
  polling steps changes, B-X1);
* the season of a test game: the Bengals (division 1, place 1) at home against the Jets, the coach "Kim", fixed
  quarterback names, the player's 33 names drawn by the set-up.
"""
import random

from gamerig import Rig, ScriptedKeys
from nfl4.game.setup import Roster
from nfl4.game.sounds import GameSounds
from randsources import ScriptedRandom, below_value, value_for

ENTER, ESCAPE, UP, DOWN, F1, F2, F3, F4 = 13, 27, 38, 40, 112, 113, 114, 115
QUARTERBACKS = ("Starr", "Unitas")


class PolicyKeys(ScriptedKeys):
    """`policy(keys)` gives the key code to type when the scripted answers are used up (None: no key, a failure)."""

    def __init__(self, clock, answers=(), policy=None, fast=False):
        super().__init__(clock, answers)
        self.policy = policy
        self.fast = fast

    def type_next(self) -> bool:
        if super().type_next():
            return True
        if self.policy is None:
            return False
        key = self.policy(self)
        if key is None:
            return False
        if isinstance(key, str):
            self.answers.append(key)
            return super().type_next()
        self.post(key)
        return True

    def dy(self, seconds: float) -> None:
        if not self.fast:
            return super().dy(seconds)
        self.pump()
        self._sleep(seconds + 1e-6)
        self.pump()


def enter_policy(keys):
    return ENTER


def random_policy(seed: int, digits=(1, 2, 3, 4, 5, 6)):
    """Enter or a digit (which moves a play menu's current item; elsewhere it is "any other key")."""
    rng = random.Random(seed)

    def policy(keys):
        if rng.random() < 0.5:
            return str(rng.choice(digits))
        return ENTER
    return policy


def make_rig(tmp_path, rng=None, answers=(), policy=enter_policy, fast=False, vtrnt=2, gtp=1, speech_per_char=0.0):
    rig = Rig(sounds_dir=tmp_path / "sounds", rng=rng if rng is not None else random.Random(1),
              speech_per_char=speech_per_char)
    keys = PolicyKeys(rig.clock, answers, policy, fast)
    rig.keys = keys
    rig.game.keys = keys
    rig.sounds.keys = keys
    if fast:
        rig.sounds.sleep = lambda seconds: rig.clock.sleep(0.02)
    season = rig.game.season
    season.coach = "Kim"
    season.choose_team(1, 1)               # Bengals
    season.tn3, season.tn4 = 2, 3          # Jets
    season.vtrnt = vtrnt
    season.gtp = gtp
    return rig


def play(rig, **kwargs):
    kwargs.setdefault("quarterback_names", lambda state: QUARTERBACKS)
    return rig.game.play_game(**kwargs)


# ----- one step of pag at a time, with strict scripted draws -----

def named_roster(prefix: str) -> Roster:
    """Names that say where they come from: Back1, Rec3, Def17, Ret2, Kick1 (the opponent's with an O in front)."""
    return Roster([f"{prefix}Back{i}" for i in range(1, 7)], [f"{prefix}Rec{i}" for i in range(1, 7)],
                  [f"{prefix}Def{i}" for i in range(1, 18)], [f"{prefix}Ret{i}" for i in range(1, 3)],
                  [f"{prefix}Kick{i}" for i in range(1, 3)])


class Draws:
    """A strict script of random draws written by hand from the lifted lines: each entry is the size n the line uses
    (Int(Rnd * n)) or 0 for a bare Rnd, and the value that gives the wanted result. The test then checks the game's
    trace of sizes against `sizes` and that every value was used."""

    def __init__(self):
        self.items: list[tuple[int, float]] = []

    def rnd(self, n: int, k: int) -> "Draws":
        """Int(Rnd * n) + 1 = k."""
        self.items.append((n, value_for(n, k)))
        return self

    def below(self, n: int, k: int) -> "Draws":
        """Int(Rnd * n) = k."""
        self.items.append((n, below_value(n, k)))
        return self

    def raw(self, x: float) -> "Draws":
        """A bare Rnd (the sound procedures, Rnd * 100)."""
        self.items.append((0, x))
        return self

    def rady(self, steps: int = 0) -> "Draws":
        return self.below(30, steps)

    def celebration(self, count: int = 8) -> "Draws":
        """playcel: Int(Rnd * 8) + 8 sounds, each foot15 (Int(Rnd * 10) + 15) at +1600 Hz (Int(Rnd * 40) - 20 = 16)."""
        self.raw((count - 8 + 0.5) / 8)
        for _ in range(count):
            self.raw(0.05).raw(0.9)
        return self

    def extend(self, other: "Draws") -> "Draws":
        self.items.extend(other.items)
        return self

    @property
    def values(self) -> list[float]:
        return [v for _, v in self.items]

    @property
    def sizes(self) -> list[int]:
        return [n for n, _ in self.items]


def engine_rig(tmp_path, answers=(), comments=False, **state):
    """A rig and an engine in the middle of a game: Bengals (side 1, coach Kim, quarterback Starr) against the Jets
    (Unitas), named rosters, the banter names of both, comments off unless asked. Fields of `state` are set on the
    engine's GameState."""
    from nfl4.game.pag import PlayEngine
    rig = Rig(sounds_dir=tmp_path / "sounds", rng=ScriptedRandom([], strict=True))
    keys = PolicyKeys(rig.clock, answers, None, False)
    rig.keys = rig.game.keys = rig.sounds.keys = keys
    rig.game.season.coach = "Kim"
    rig.game.season.choose_team(1, 1)
    rig.game.season.tn3, rig.game.season.tn4 = 2, 3
    rig.game.comtog_source = (lambda: 0) if comments else (lambda: 1)
    engine = PlayEngine(rig.game, quarterback_names=lambda s: ("Starr", "Unitas"))
    s = engine.s
    s.teams = {1: "Bengals", 2: "Jets"}
    s.rosters = {1: named_roster(""), 2: named_roster("O")}
    s.quarterbacks = {1: "Starr", 2: "Unitas"}
    own, opp = s.rosters[1], s.rosters[2]
    s.player_names = (own.running_backs + own.receivers + own.defense + opp.running_backs + opp.receivers
                      + opp.defense)
    s.plays = [33, 33, 33, 33, 33]
    for name, value in state.items():
        setattr(s, name, value)
    rig.engine = engine
    return rig


def run_steps(rig, step, draws: Draws, until=("next_play", "play_menu", "kick_off", "offense_menu", "finish")):
    """Run pag from `step` with the scripted draws until a step named in `until` comes (returns its name; None when
    pag ended). Then the draws must be used up exactly, with the sizes of the script."""
    source = ScriptedRandom(draws.values, strict=True)
    rig.rnd.source = source
    rig.rnd.trace = []
    reached = None
    while step is not None:
        if step.__name__ in until:
            reached = step.__name__
            break
        step = step()
    assert rig.rnd.trace == draws.sizes, (rig.rnd.trace, draws.sizes)
    assert source.left == 0
    return reached


def texts(rig, start=0):
    return [t for t, _, _ in rig.said[start:]]


def sounds_played(rig):
    return [e.sound_id.replace("snd_", "") for e in rig.slot_log if e.action == "play"]


__all__ = ["GameSounds", "PolicyKeys", "make_rig", "play", "Draws", "engine_rig", "run_steps", "texts",
           "sounds_played", "named_roster"]
