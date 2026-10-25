"""What an automatic save keeps so that a crashed game goes on exactly as it would have: the engine's state as plain JSON. This is inspired by Jim Kitchen.

CLAUDE.md 0.23, playbook 7.17, NX-S4 (D-086). football.sav holds what the original saves (the board, the score, the clock counter); it does not hold
the phrase histories, the interception counts, the rosters the set-up drew, or where the random generator is, because the original starts those
afresh when it loads a game. An automatic save is the game the player was playing a moment ago, so it keeps them too: the test of NX-S4 kills the
process at a random play and requires the same final result as a game that was never interrupted. `capture` reads, `restore` puts back; neither
draws a number or speaks.

The text is JSON in which a tuple, a dictionary with any kind of key and an object of one of the four classes below keep their type; a class
outside `CLASSES` in a file is refused (a save is a file a player can edit, and loading one must never run anything).
"""
from __future__ import annotations

import dataclasses
import json
import logging
from typing import Any

from .gamestate import GameState, SideStats
from .phrases import GroupedPhrases, PhraseHistory
from .setup import Roster

log = logging.getLogger("nfl4.game")

FORMAT = 1
LIMIT_BYTES = 60_000                    # the file holds a section as one String Variant of at most 65,535 bytes
CLASSES = {cls.__name__: cls for cls in (SideStats, Roster, PhraseHistory, GroupedPhrases)}
SKIPPED = {"extras"}                    # the extras record has its own section in the file


class ResumeError(ValueError):
    """The resume text cannot be used whole."""


def to_plain(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, list):
        return [to_plain(item) for item in value]
    if isinstance(value, tuple):
        return {"__tuple__": [to_plain(item) for item in value]}
    if isinstance(value, dict):
        return {"__dict__": [[to_plain(k), to_plain(v)] for k, v in value.items()]}
    name = type(value).__name__
    if name in CLASSES and isinstance(value, CLASSES[name]):
        fields = ({f.name: getattr(value, f.name) for f in dataclasses.fields(value)} if dataclasses.is_dataclass(value)
                  else vars(value))
        return {"__class__": name, "fields": {k: to_plain(v) for k, v in fields.items()}}
    raise ResumeError("a %s cannot be kept in an automatic save" % type(value).__name__)


def from_plain(data: Any) -> Any:
    if isinstance(data, list):
        return [from_plain(item) for item in data]
    if not isinstance(data, dict):
        return data
    if "__tuple__" in data:
        return tuple(from_plain(item) for item in data["__tuple__"])
    if "__dict__" in data:
        return {_hashable(from_plain(k)): from_plain(v) for k, v in data["__dict__"]}
    if "__class__" in data:
        cls = CLASSES.get(data["__class__"])
        if cls is None:
            raise ResumeError("the class %r is not one an automatic save may hold" % (data["__class__"],))
        obj = cls.__new__(cls)
        for key, value in data.get("fields", {}).items():
            setattr(obj, key, from_plain(value))
        return obj
    raise ResumeError("an object of an unknown kind")


def _hashable(key):
    return tuple(key) if isinstance(key, list) else key


def capture(engine) -> str:
    """The engine's state as JSON text, for the NX-RESUME section."""
    g, s = engine.g, engine.s
    state = {f.name: to_plain(getattr(s, f.name)) for f in dataclasses.fields(GameState) if f.name not in SKIPPED}
    qc = g.quarter_clock
    clock = {"oldtime": qc.oldtime, "mins": qc.mins, "secs": qc.secs, "countdown": qc.countdown, "warning": to_plain(qc.warning)}
    rng = {"draws": g.rnd.draws}
    source = g.rnd.source
    if hasattr(source, "getstate"):
        version, internal, gauss = source.getstate()
        rng["state"] = [version, list(internal), gauss]
    data = {"v": FORMAT, "state": state, "clock": clock, "rng": rng,
            "engine": {"previous_play": s.previous_play, "repeats": s.repeats}}
    return json.dumps(data, separators=(",", ":"))


def restore(engine, text: str) -> bool:
    """Put the captured state back. True when it was used whole; False (and nothing changed) when the text cannot be used: the
    game then goes on from football.sav's values alone, as a saved game does."""
    try:
        data = json.loads(text)
        if not isinstance(data, dict) or data.get("v") != FORMAT:
            raise ResumeError("another format")
        state = {name: from_plain(value) for name, value in data["state"].items()}
        names = {f.name for f in dataclasses.fields(GameState)}
        if not set(state) <= names:
            raise ResumeError("a field this version does not have")
        clock = data["clock"]
        warning = from_plain(clock["warning"])
        rng = data["rng"]
        generator = None
        if "state" in rng:
            version, internal, gauss = rng["state"]
            generator = (version, tuple(internal), gauss)
            engine.g.rnd.source.setstate(generator)         # raises when the source has no state or the state is not valid
        draws = int(rng["draws"])
    except (ValueError, KeyError, TypeError, AttributeError, RecursionError) as exc:
        log.warning("the resume part of an automatic save cannot be used (%s): the game goes on from the saved board alone", exc)
        return False
    for name, value in state.items():
        setattr(engine.s, name, value)
    qc = engine.g.quarter_clock
    qc.oldtime, qc.mins, qc.secs, qc.countdown, qc.warning = clock["oldtime"], clock["mins"], clock["secs"], clock["countdown"], warning
    engine.g.rnd.draws = draws
    return True
