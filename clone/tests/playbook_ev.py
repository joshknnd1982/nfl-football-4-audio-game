"""Expected yards of the original's rows with and without a playbook's modifiers (nfl4 only, rule 0.13; PX SX.7). This is inspired by Jim Kitchen.

A yardstick for the data tests and for the calibration (work/calibrate_playbooks_sx7.py), never used by play. The value of a row
is its expected yards per call: runs and quarterback runs (1 - 1/fumble) x mean - 1/fumble x TURNOVER, passes
sack% x (-6.5) + (1 - sack%) x complete% x (that of a run). It ignores downs and field position on purpose: it says whether a play
tilts the original's row up or down, not how a game goes (the simulation says that).
"""
from nfl4.extras import playbook_data as D
from nfl4.extras import playbooks as PB
from nfl4.extras.qb_runs import make_entry
from nfl4.game.playtables import FUMBLE_ODDS, PASSES, RUNS

TURNOVER = 30.0           # a lost fumble is worth about this many yards
SACK_YARDS = -6.5         # Int(Rnd * 12) - 12: -12 to -1
QB_KEY = {8: "sneak", 9: "keeper", 10: "draw"}
CLASSIC_MIX = {1: 2, 2: 2, 3: 2, 4: 2, 5: 1}      # GAME_SPEC 5.7: the computer's offense families


def _run(entry, fumble: int) -> float:
    mean = (entry.low + entry.high - 1) / 2
    p = 1 / fumble
    return (1 - p) * mean - p * TURNOVER


def row_value(family: int, call: int, mod: D.Mod | None = None) -> float:
    """Expected yards of offense `family` against defense call `call` (1 to 6) moved by `mod`."""
    modifiers = PB.PlaybookModifiers()
    modifiers.arm(mod)
    if family <= 2:
        return _run(modifiers.run(family, call, RUNS[(family, call)]), modifiers.fumble_odds(1))
    if family <= 5:
        entry = modifiers.pass_(family, call, PASSES[(family, call)])
        p_sack = entry.sack / 100
        return p_sack * SACK_YARDS + (1 - p_sack) * entry.complete / 100 * _run(entry, modifiers.fumble_odds(1))
    entry = modifiers.qb_run(make_entry(QB_KEY[family], call))
    return _run(entry, entry.fumble)


def base_vector(family: int) -> list[float]:
    return [row_value(family, call) for call in range(1, 7)]


def offense_vector(book: PB.StyleBook | None, play: D.Play) -> list[float]:
    """The play's value against each of the six defense calls, with its own tilt and its style's."""
    return [row_value(play.family, call, PB.side_mod(book, play, call)) for call in range(1, 7)]


def classic_value() -> float:
    total = sum(CLASSIC_MIX.values())
    return sum(w * sum(base_vector(f)) / 6 for f, w in CLASSIC_MIX.items()) / total


def style_value(table: PB.Table, key: str) -> tuple[float, dict]:
    """The style's offense against a uniform defense, by its families' weights (the five families only), and its mix."""
    plays = [(p, w) for p, w in table.usable(key, "O") if p.family <= 5]
    book = table.styles[key]
    total = sum(w for _p, w in plays)
    value = sum(w * sum(offense_vector(book, p)) / 6 for p, w in plays) / total
    return value, {f: sum(w for p, w in plays if p.family == f) / total for f in range(1, 6)}


def defense_value(table: PB.Table, key: str) -> float:
    """What the original's offense mix gains against the style's defense: one of its plays of the called family by weight."""
    plays = table.usable(key, "D")
    book = table.styles[key]
    total_mix = sum(CLASSIC_MIX.values())
    value = 0.0
    for call in range(1, 7):
        family_plays = [(p, w) for p, w in plays if p.family == call]
        weight = sum(w for _p, w in family_plays)
        for play, w in family_plays:
            for family, mix in CLASSIC_MIX.items():
                value += (w / weight) * (mix / total_mix) * row_value(family, call, PB.side_mod(book, play, family)) / 6
    return value


def dominating_play(vectors: dict[str, list[float]]) -> str | None:
    """The ID of a play that is at least as good as every other one against every call and better against some, or None."""
    for play_id, mine in vectors.items():
        better_somewhere = False
        for other_id, theirs in vectors.items():
            if other_id == play_id:
                continue
            if any(a < b - 1e-9 for a, b in zip(mine, theirs)):
                break
            better_somewhere = better_somewhere or any(a > b + 1e-9 for a, b in zip(mine, theirs))
        else:
            if better_somewhere:
                return play_id
    return None
