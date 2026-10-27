"""The facts a save carries about itself and the one sentence that says them. This is inspired by Jim Kitchen.

CLAUDE.md 0.23, playbook 7.17, NX-S1 (D-086). `make_info` is what the engine writes into a save's `info` section (teams, week, the
time left, the kind of season; the shelf adds the date and the slot); `game_sentence`, `season_sentence` and `franchise_sentence` are the
sentences the start-up menu says before its items; `short_game` is the same save in a few words for a list. Nothing here draws a random
number or changes the game: the time left of a classic game is an estimate from the play counter (the original has no clock), so the
made-up seconds of `sgc` (which are drawn) are not used.
"""
from __future__ import annotations

import time

from . import prompt_texts as T
from . import save_texts as S
from .vbnum import rtrim

MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")
QUARTER_WORDS = {1: "first", 2: "second", 3: "third", 4: "fourth"}
FORMAT = 1


def when_words(stamp: float) -> str:
    """"October 20 at 8:15 PM" in the computer's local time; "" when the date is not known."""
    if not stamp or stamp <= 0:
        return ""
    try:
        t = time.localtime(stamp)
    except (OverflowError, OSError, ValueError):
        return ""
    return "%s %d at %d:%02d %s" % (MONTHS[t.tm_mon - 1], t.tm_mday, t.tm_hour % 12 or 12, t.tm_min, "PM" if t.tm_hour >= 12 else "AM")


def _name(text: str) -> str:
    return rtrim(text or "").strip()


def make_info(engine) -> dict:
    """The facts of the game being saved, from the running engine (pure: reads the state and the clock)."""
    g, s = engine.g, engine.s
    try:
        minutes, seconds = engine.clock.summary_left()
    except Exception:                                   # the summary must never stop a save
        minutes, seconds = None, None
    return {"v": FORMAT, "week": g.season.gtp, "reg": g.season.regular_weeks, "kind": "franchise" if g.franchise_in_use else "classic",
            "rules": getattr(engine.rules, "name", "classic") or "classic", "own": _name(s.teams.get(1, "")), "opp": _name(s.teams.get(2, "")),
            "lm": minutes, "ls": seconds}


def _plural(n: int) -> str:
    return "" if n == 1 else "s"


def left_words(info: dict) -> str:
    minutes, seconds = info.get("lm"), info.get("ls")
    if not isinstance(minutes, int):
        return ""
    if seconds is None:                                 # a classic game: made up from the counter, so "about"
        return S.ABOUT + "%d minute%s" % (minutes, _plural(minutes)) if minutes > 0 else S.LESS_THAN_A_MINUTE
    parts = []
    if minutes:
        parts.append("%d minute%s" % (minutes, _plural(minutes)))
    if seconds or not minutes:
        parts.append("%d second%s" % (seconds or 0, _plural(seconds or 0)))
    return " ".join(parts)


def playoff_name(week: int, regular: int = 16, default: str = "play off week") -> str:
    """The name of a play-off week by its counter, in the original's numbering (17 to 20) whatever the length of the regular season (a calendar's 18 weeks)."""
    return T.PLAYOFF_WEEK_NAMES.get(week - regular + 16, default)


def week_words(week: int | None, regular: int = 16) -> str:
    if not isinstance(week, int) or week < 1:
        return ""
    if week > regular:
        return S.THE_PLAYOFF_WEEK % playoff_name(week, regular)
    return S.THE_WEEK % week


def _slot_part(entry, many: bool) -> str:
    return S.IN_SLOT % entry.slot if many and entry.slot else ""


def game_sentence(entry, many: bool = False) -> str:
    """The one sentence about a game save, whatever its state."""
    slot = _slot_part(entry, many)
    if not entry.playable:
        text = {"damaged": S.THE_GAME_IS_DAMAGED, "held": S.THE_GAME_IS_HELD, "stale": S.THE_GAME_IS_OLD,
                "orphan": S.THE_GAME_HAS_NO_SEASON}.get(entry.status, S.THE_GAME_IS_DAMAGED)
        return text % slot
    saved, info = entry.saved, entry.info
    own, opp = info.get("own"), info.get("opp")
    a, b = saved.stats[1].score, saved.stats[2].score
    if own and opp:
        score = S.THE_SCORE_TIED % (own, opp, a, b) if a == b else (S.THE_SCORE % (own, opp, a, b) if a > b else S.THE_SCORE % (opp, own, b, a))
    else:
        score = S.THE_SCORE_UNNAMED % (a, b)
    head = S.YOU_HAVE_AN_UNFINISHED_GAME if entry.is_auto else S.YOU_HAVE_A_GAME
    text = head + slot + ":" + score[1:]                  # the score phrase starts with ", "
    text += S.IN_OVER_TIME if saved.quarter >= 5 else S.IN_THE_QUARTER % QUARTER_WORDS.get(saved.quarter, "")
    left = left_words(info)
    if left:
        text += S.WITH_TIME_LEFT % left
    ball = own if saved.wisoff == 1 else opp
    if ball:
        text += S.THE_BALL % ball
    text += week_words(info.get("week"), info.get("reg") if isinstance(info.get("reg"), int) else 16)
    when = when_words(entry.stamp)
    return text + (S.SAVED_ON % when if when else S.NO_DATE)


def short_game(entry, with_slot: bool = True) -> str:
    """The save in a few words, for a list: "slot 2, the Bears and the Packers, week 5, saved October 20 at 8:15 PM"."""
    where = "slot %d" % entry.slot if entry.slot else "the automatic save"
    if not entry.playable:
        return "%s, %s" % (where, "damaged" if entry.status == "damaged" else "cannot be played") if with_slot else (
            "a damaged save" if entry.status == "damaged" else "a save that cannot be played")
    info = entry.info
    parts = [where] if with_slot else []
    if info.get("own") and info.get("opp"):
        parts.append("%s and %s" % (info["own"], info["opp"]))
    week = info.get("week")
    if isinstance(week, int) and week >= 1:
        regular = info.get("reg") if isinstance(info.get("reg"), int) else 16
        parts.append("week %d" % week if week <= regular else playoff_name(week, regular))
    when = when_words(entry.stamp)
    if when:
        parts.append("saved " + when)
    return ", ".join(parts) or "a saved game"


def _record_words(wins: int, losses: int) -> str:
    """"1 win and 2 losses" (D-176: "losses" was said "losss", one "s" added to "loss")."""
    return S.WINS_AND_LOSSES % (wins, _plural(wins), losses, "" if losses == 1 else "es")


def season_sentence(coach: str, team: str, gtp: int, wins: int, losses: int) -> str:
    where = S.WEEK_RECORD % gtp if gtp < 17 else S.PLAYOFFS_RECORD % T.PLAYOFF_WEEK_NAMES.get(gtp, "play offs")
    record = _record_words(wins, losses)
    team = _name(team)
    if coach and coach != "coach":
        return S.THE_SEASON % (coach, team, where, record)
    return S.THE_SEASON_NO_COACH % (team, where, record)


def franchise_sentence(coach: str, team: str, season: int, in_season: bool, gtp: int, wins: int, losses: int, regular: int = 16) -> str:
    team = _name(team)
    coach = coach if coach and coach != "coach" else "the player"
    if not in_season:
        return S.THE_FRANCHISE_OFFSEASON % (coach, team, season)
    where = S.WEEK_RECORD % gtp if gtp <= regular else S.PLAYOFFS_RECORD % playoff_name(gtp, regular, "play offs")
    return S.THE_FRANCHISE % (coach, team, season, where, _record_words(wins, losses))
