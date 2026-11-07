"""The positions the player chooses from in the Franchise's menus: the 22 real positions of Madden NFL, and the kick and punt returners (nfl4 only,
rule 0.13; rule 0.40, D-214). This is inspired by Jim Kitchen.

A tester (2026-11-06), made the owner's own: "First Safety and free safety are two different positions. It groups all safeties as one this is incorrect.
Second kick returners aren't tradable this is incorrect. All linebackers need to be properly separated as well." So the trades, the free agents and the
practice squad no longer ask for a group ("safeties", "linebackers") but for a real position (free safeties, strong safeties; strong-side, middle and
weak-side linebackers; the left and right edge ...), in the order of the roster (roster_flow), and the trades add the kick and punt returners. A man is
listed at his own real position; an older league's man without one is listed at the first position of his family. The rules of a trade or a signing
still work on the family (`Player.pos`), so nothing else changes. Plain rules and one menu; no draw.
"""
from __future__ import annotations

from ...game.spoken_menu import Item, SpokenMenu
from .. import nx_texts as X
from .. import roster_model as RM

RETURNERS = "KR"                                      # the item of the kick and punt returners (the trades)
HEADINGS = {key: "NXL-%d" % (60 + n) for n, key in enumerate(RM.MADDEN)}     # "free safeties", "middle linebackers" (roster_flow's headings)
ALL = tuple(RM.MADDEN)
WITH_RETURNERS = ALL + (RETURNERS,)


def word(code: str) -> str:
    """The position said in a menu and in the sentences that name a group: "free safeties", "kick and punt returners"."""
    return X.text("NXL-86") if code == RETURNERS else X.text(HEADINGS[code])


def position_of(player) -> str:
    """His real position; a man without one (an older league's man) at the first position of his family's word."""
    position = getattr(player, "position", "") or ""
    if position in RM.FAMILY:
        return position
    return RM.WORD_POSITIONS.get(getattr(player, "pos", ""), ("",))[0]


def family_word(code: str) -> str:
    """The family word of the Franchise's rules (RM.GROUP) for a position; "" for the returners."""
    return RM.GROUP.get(code, "")


def returners(league, team: int) -> list:
    """The team's kick and punt returners: the men its chart names for the two roles, then the men of the view's two return places, each once, active."""
    chart = league.chart[team - 1] if isinstance(league.chart, list) and len(league.chart) >= team and isinstance(league.chart[team - 1], dict) else {}
    out, seen = [], set()
    ids = list(chart.get("KR", ())[:1]) + list(chart.get("PR", ())[:1])
    ids += [p.id for p in league.group_of(team, "RET") if p is not None]
    for pid in ids:
        p = league.players.get(pid)
        if p is not None and pid not in seen and p.status == "active" and p.team == team:
            seen.add(pid)
            out.append(p)
    return out


def men(league, team: int, code: str, family_men) -> list:
    """The team's men of a position: `family_men(family word)` gives the men of the family (in the order of its menu), kept when they play this position."""
    if code == RETURNERS:
        return returners(league, team)
    return [p for p in family_men(family_word(code)) if position_of(p) == code]


def choose(speech, keys, title: str, codes=ALL) -> str | None:
    """A menu of positions (Up, Down, digits, Page Up and Page Down, Home and End, Enter); the code chosen, or None after Escape."""
    chosen: list = []

    class _Chosen(Exception):
        pass

    def take(code):
        chosen.append(code)
        raise _Chosen()
    items = [Item(lambda code=code: word(code), enter=lambda code=code: take(code)) for code in codes]
    if not items:
        return None
    try:
        SpokenMenu(speech, keys, title, items, space_enters=True, digits_jump=True).run()
    except _Chosen:
        pass
    return chosen[0] if chosen else None
