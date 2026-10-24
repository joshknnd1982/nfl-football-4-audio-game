"""Who plays: the starters most, the backups seldom (nfl4 only, rule 0.13; NX-D2 and NX-D4, D-147, CLAUDE.md 0.30). This is inspired by Jim Kitchen.

The owner's second report of 2026-10-24 (a tester's words he made his own): "the top players should play more. It should take it from like Madden", and
"if you set certain players you should have them play on key downs and key moments". The original drew the ball carrier as one of six places and each
tackler as one of seventeen, every place alike (rnd(6), rnd(17)). With the N. F. L. rules each of those draws is ONE `below(total)` over the usage
shares of `extras/tuning.py` (USAGE_RUN, USAGE_PASS, USAGE_TACKLE: percent of the plays each place gets, the starters most), the same one random number
the original's draw costs; a franchise multiplies them by its rating weights; the player's man for a key situation (NX-D4) takes KEY_PLAYER_SHARE of
his group's draw. Plain rules, no speech, no files.
"""
from __future__ import annotations

from . import tuning as T

RUN, PASS = "run", "pass"


def shares(kind: str | None) -> list:
    """The six places' shares of a run (the backs) or a pass (the receivers: WR1, WR2, WR3, TE1, WR4, TE2); a run's for anything else."""
    return list(T.USAGE_PASS if kind == PASS else T.USAGE_RUN)


def combine(base: list, rating_weights: list | None) -> list:
    """The shares times a franchise's rating weights (None: the shares alone)."""
    if rating_weights is None:
        return list(base)
    return [share * weight for share, weight in zip(base, rating_weights)]


def with_key_player(weights: list, place: int | None) -> list:
    """NX-D4: the key situation's man (place 1 to 6, or None) gets KEY_PLAYER_SHARE percent of the draw, the others share the rest in their own
    proportions (a place of no share keeps none)."""
    if not place or not 1 <= place <= len(weights):
        return list(weights)
    others = sum(w for i, w in enumerate(weights, start=1) if i != place)
    if others <= 0:
        return [1 if i == place else 0 for i in range(1, len(weights) + 1)]
    key = T.KEY_PLAYER_SHARE
    # whole numbers: the man's weight and the others' scaled so that he has `key` percent of the total
    scale = 100 - key
    out = [w * scale for w in weights]
    out[place - 1] = others * key
    return out


def weighted_place(rnd, weights: list) -> int:
    """The place 1 to len(weights) of one `below(total)` draw over the weights."""
    total = sum(weights)
    roll = rnd.below(total)
    for number, weight in enumerate(weights, start=1):
        if roll < weight:
            return number
        roll -= weight
    raise AssertionError("the usage weights")


def defenders(rnd, weights: list | None = None) -> tuple:
    """The two tacklers of a scrimmage play, places 1 to 17, two different men: the first by the tackle shares, the second drawn again until he is
    another man, as the original redraws its second defender."""
    weights = list(T.USAGE_TACKLE) if weights is None else weights
    first = weighted_place(rnd, weights)
    second = rnd.redraw(lambda: weighted_place(rnd, weights), lambda d: d != first, lambda: 2 if first == 1 else 1, "second defender")
    return first, second
