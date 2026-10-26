"""The surnames of real NFL players that the made-up players take with the N. F. L. rules (nfl4 only, rule 0.13; NX-L12, D-163, D-164; CLAUDE.md 0.19).
This is inspired by Jim Kitchen.

The owner (2026-10-25, Q-016): "claude must research the last names of real nfl players and use those." The list is nfl_surnames.txt (written by the
maintainer's game\\tools\\update_surnames.py from nflverse's players table and the game's rosters; customizable like the other name files: the player's
copy in the customize folder, healed when damaged). A made-up man of the Franchise (a later draft class, the undrafted, the cut's fill, a stand-in, a
practice squad's top-up, a free agent of the season) draws his last name from it with the league's own name rule (`league.draw_name`: the same number of
draws as before, from a longer list) and takes a first name of the game's list that never makes a real player's full name (first_names.first_name).
Classic keeps the original's 1,708 surnames and never reaches this module.
"""
from __future__ import annotations

import logging

log = logging.getLogger("nfl4.extras")

_SHIPPED: list | None = None


def shipped() -> list:
    """The built-in list (the shipped file), read once; [] when it cannot be read."""
    global _SHIPPED
    if _SHIPPED is None:
        from . import real_names
        names = real_names.defaults()
        _SHIPPED = names.surname_pool() if names is not None else []
    return list(_SHIPPED)


def pool(g=None) -> list:
    """The surnames a made-up man takes: the player's nfl_surnames.txt as loaded (`g.real_names`), else the built-in list; the original's surnames when
    neither has a name (a damaged install), so the game never stops for want of a name."""
    real = getattr(g, "real_names", None) if g is not None else None
    names = real.surname_pool() if real is not None and hasattr(real, "surname_pool") else []
    if not names:
        names = shipped()
    if names:
        return names
    pool_ = getattr(g, "pool", None) if g is not None else None
    if pool_ is not None:
        return list(pool_.original)
    from ..game.names import load_surnames
    log.warning("NX-L12: no surnames of real players could be read; the original's surnames are used")
    return load_surnames()
