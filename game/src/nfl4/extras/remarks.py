"""The announcer's remarks of the extras: the pools of remarks.txt (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

CUSTOMIZABLE_CONTENT 13 (L13), CLAUDE.md 0.12, playbook 7.9, D-042. Every pool is customizable commentary: the defaults are the
lines of spec/STRINGS_NX.md (extras/nx_texts.py, generated, never typed), each with a permanent ID; a player's line with the
same ID replaces it, `TO03 = off` switches it off, a new number adds a line (TO06 and up). A line uses the markup of banter.txt
(game/banter_markup.py: [sound file], [pause], [bleep], [one of: a | b], [name], [opponent quarterback], [then], [faster]) and
the placeholders of its pool in angle brackets (the TO pool: <team>, <coach>, <quarterback>); an unknown placeholder is spoken
as it is written and counted as a problem when the file is read.

The draw (design 6.3, CUSTOMIZABLE_CONTENT 13): one line of the pool's lines that are on, with equal chances, never one of the
last three spoken in this game when the pool has more than three lines on (`Int(Rnd * size) + 1`, drawn again while it is one
of them; bounded, G-D1); a line with [name] draws a name of the banter's list after it, a line with [one of:] its choices
after that. F8 (comments off) silences the pools of commentary before any draw. A pool with no line on says nothing.

A pool of the play-by-play (QB) is never silent: with every line switched off its default lines speak.
Built so far: TO (SX.2), PN (SX.3, after an accepted penalty, design 9), ON (SX.4, when an onside kick is declared, design 8),
QB (SX.5, the start of a keeper or a draw, design 7.2: play-by-play in the quarterback's sentence, said with say4 so that F2
replays it, and never silenced by F8), CHS and CHC (SX.6, the hints after a wrong or a close ruling, design 6.1), RVR and RVC
(SX.6, after a review, design 6.4; RVC03 is drawn only after a lost challenge).
Each later session adds its pool to POOLS_BUILT
and its placeholders to PLACEHOLDERS.

SY.1 (the radio-style broadcast, CLAUDE.md 0.27, playbook 7.19, D-101): BN is the announcer's radio banter, 142 lines that replace Jim Kitchen's
jokes in the N. F. L. rules mode (game/banter.py draws them by the original's rule through the Rules hook `banter_lines`); ASK is the announcer
turning to Ghip; CKO CBG CSK CTV CTD CFG CFM CTC CTS CFD CRZ CPN CTM CQE CHT CFN CFT CTT CBO are Ghip's lines, the color commentator, spoken
in his own voice (extras/broadcast.py). They are drawn with the broadcast's OWN random generator, so the game's draws do not move.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Mapping

from ..game.banter import NAME_LIST_SIZE, play_line
from ..game.banter_markup import NameRef, OneOf, Speak, Text, choice_sizes, parse_markup, to_markup
from . import commentators, nx_texts
from .remarks_retired import RETIRED
from .state import RECENT_REMARKS

log = logging.getLogger("nfl4.extras")

BROADCAST_POOLS = ("BN", "ASK", "CKO", "CBG", "CSK", "CTV", "CTD", "CFG", "CFM", "CTC", "CTS", "CFD", "CRZ", "CPN", "CTM", "CQE", "CHT",
                   "CFN", "CFT", "CTT", "CBO")      # SY.1: the radio banter, the announcer's question and Ghip's pools (rule 0.27)
COLOR_POOLS = tuple(pool for pool in BROADCAST_POOLS if pool not in ("BN", "ASK"))      # said by Ghip's voice
POOLS_BUILT = ("TO", "CHS", "CHC", "RVR", "RVC", "ON", "QB", "PN") + BROADCAST_POOLS     # the pools whose feature exists (SX.2 timeouts, SX.6 replay
#                                                         challenges, SX.4 onside kicks, SX.5 quarterback runs, SX.3 penalties),
#                                                         in the order of remarks.txt (design 13)
COMMENTARY_POOLS = frozenset(("TO", "CHS", "CHC", "RVR", "RVC", "ON", "PN") + BROADCAST_POOLS)   # F8 silences these; QB is play-by-play
PLAY_BY_PLAY_POOLS = frozenset(("QB",))      # never silenced: with every line switched off the default lines speak (design 13, L13)
PLACEHOLDERS = {"TO": ("<team>", "<coach>", "<quarterback>"),
                "CHS": ("<team>", "<coach>", "<quarterback>"),
                "CHC": ("<team>", "<coach>", "<quarterback>"),
                "RVR": ("<team>", "<coach>", "<quarterback>"),
                "RVC": ("<team>", "<coach>", "<quarterback>"),
                "ON": ("<team>", "<coach>", "<quarterback>"),
                "QB": ("<team>", "<coach>", "<quarterback>"),
                "PN": ("<team>", "<coach>", "<quarterback>", "<surname>"),
                "BN": (), "ASK": ()}
# SY.1: Ghip's pools. <team> the team the line is about, <opponent> the other one, <quarterback> that team's quarterback, <coach> the
# player's name, <yards> a gain, <situation> a clause with the score, <quarter> "second quarter" and so on
for _pool, _names in (("CKO", ("<team>", "<opponent>", "<coach>", "<quarterback>")), ("CBG", ("<team>", "<opponent>", "<yards>", "<quarterback>")),
                      ("CSK", ("<team>", "<opponent>", "<quarterback>")), ("CTV", ("<team>", "<opponent>")),
                      ("CTD", ("<team>", "<opponent>", "<situation>")), ("CFG", ("<team>", "<opponent>", "<situation>")),
                      ("CFM", ("<team>", "<opponent>")), ("CTC", ("<team>", "<opponent>")), ("CTS", ("<team>", "<opponent>")),
                      ("CFD", ("<team>", "<opponent>")), ("CRZ", ("<team>", "<opponent>")), ("CPN", ("<team>", "<opponent>")),
                      ("CTM", ("<situation>", "<quarter>", "<team>", "<opponent>")), ("CQE", ("<situation>", "<quarter>", "<team>", "<opponent>")),
                      ("CHT", ("<situation>", "<team>", "<opponent>")), ("CFN", ("<situation>", "<team>", "<opponent>")),
                      ("CFT", ("<situation>", "<team>", "<opponent>")), ("CTT", ("<situation>", "<team>", "<opponent>")),
                      ("CBO", ("<situation>", "<team>", "<opponent>"))):
    PLACEHOLDERS[_pool] = _names
# SZ.1 (D-106): <commentator> is the color commentator's name (F9, Rules, Commentator) and fits every pool; the default lines that said Ghip say it
for _pool in PLACEHOLDERS:
    PLACEHOLDERS[_pool] = tuple(PLACEHOLDERS[_pool]) + ("<commentator>",)
# The wording the 0.10.0 files carry for the default lines that were reworded in SZ.1 (the others only had "Ghip" where "<commentator>" is now):
# a line of the player's file that is still one of these is the unchanged default and follows the commentator's name like the new one.
LEGACY_MARKUP = {
    "BN42": "Ghip is looking very thoughtful over there. Either he is studying the game or he is wondering what is in the lunch bag.",
    "BN43": "Ghip still gets that gleam in his eye when the crowd gets loud. Once a player, always a player.",
    "BN82": "Ghip is nodding over there like he has seen it all before. Of course he has, he is practically older than the goalposts.",
    "BN83": "Ghip, you used to play this game, and now you sit there making it look easy. I admire the nerve, my friend.",
    "BN123": "Ghip, you played this game once. Tell me honestly, did you ever really enjoy the film study?",
    "BN124": "Ghip is sitting very quietly over there. Either he is thinking deeply, or he is hoping nobody asks him a question.",
    "ON03": "the hands team is on the field.",             # SZ.6: it repeated the sentence of the kick (NXO-03) that came just before it
}
ID_PATTERN = re.compile(r"([A-Z]{2,3})(\d{1,4})", re.IGNORECASE)
MAX_NUMBER = 9999
_PLACEHOLDER = re.compile(r"<[^<>]{1,30}>")


def remark_id(pool: str, number: int) -> str:
    return "%s%02d" % (pool, number)


def parse_id(entry_id: str) -> tuple[str, int] | None:
    """TO3, to03 and TO03 are ("TO", 3); None for anything that is not a remark ID of a pool this game has."""
    match = ID_PATTERN.fullmatch(entry_id)
    if match is None:
        return None
    pool, number = match.group(1).upper(), int(match.group(2))
    if pool not in POOLS_BUILT or not 1 <= number <= MAX_NUMBER:
        return None
    return pool, number


@dataclass(frozen=True)
class Remark:
    id: str
    pool: str
    number: int
    pieces: tuple
    markup: str
    builtin: bool                  # a default line: its text keeps the exact spaces of STRINGS_NX


def _builtin(remark_id_text: str) -> Remark:
    parsed = parse_id(remark_id_text)
    if parsed is None:
        raise ValueError("%s is not a remark of a built pool" % remark_id_text)
    pieces = (Speak((Text(nx_texts.TEXTS[remark_id_text]),)),)
    return Remark(remark_id_text, parsed[0], parsed[1], pieces, to_markup(pieces), True)


DEFAULT_REMARKS: dict[str, tuple[Remark, ...]] = {
    pool: tuple(_builtin(rid) for rid in nx_texts.REMARK_POOLS[pool]) for pool in POOLS_BUILT}
DEFAULT_MARKUP: dict[str, str] = {r.id: r.markup for lines in DEFAULT_REMARKS.values() for r in lines}


class RemarkPools:
    """The lines that are on, per pool, in the order of their numbers."""

    def __init__(self, pools: Mapping[str, tuple[Remark, ...]] | None = None):
        source = pools if pools is not None else DEFAULT_REMARKS
        self.pools: dict[str, tuple[Remark, ...]] = {
            pool: tuple(sorted(source.get(pool, ()), key=lambda r: r.number)) for pool in POOLS_BUILT}

    def lines(self, pool: str) -> tuple[Remark, ...]:
        return self.pools.get(pool, ())

    @property
    def size(self) -> int:
        return sum(len(lines) for lines in self.pools.values())


DEFAULT_POOLS = RemarkPools()


def _texts_of(pieces: tuple) -> list[str]:
    out = []
    for piece in pieces:
        if isinstance(piece, Speak):
            for item in piece.items:
                if isinstance(item, Text):
                    out.append(item.text)
                elif isinstance(item, OneOf):
                    out.extend(sub.text for option in item.options for sub in option if isinstance(sub, Text))
    return out


def legacy_markup(key: str) -> str | None:
    """What a file of version 0.10.0 holds for an unchanged default line that now says <commentator>: the line with Ghip in its place, or
    the old wording of a line that was reworded (LEGACY_MARKUP). None for a line that never said Ghip."""
    if key in LEGACY_MARKUP:
        return LEGACY_MARKUP[key]
    original = DEFAULT_MARKUP.get(key)
    if original is not None and "<commentator>" in original:
        return original.replace("<commentator>", "Ghip")
    return None


def commentator_of(game) -> str:
    """The color commentator's name for this game: the broadcast of the game's rules knows it (extras/broadcast.py); Ghip in a rig without."""
    for rules in (getattr(getattr(game, "play_engine", None), "rules", None), getattr(game, "rules", None)):    # the game being played first
        name = getattr(getattr(rules, "broadcast", None), "commentator", None)
        if name:
            return name
    return commentators.DEFAULT


def build_pools(overrides: Mapping[str, str | None], problems) -> RemarkPools:
    """The pools for the player's entries: `overrides` maps a canonical ID (TO03) to the markup, or to None for `off`.
    `problems` gets the plain-word problems (data.customlists.Problems): a bad line keeps the default (or is left out when it
    is a new ID); an unknown placeholder is a problem and is spoken as written."""
    lines: dict[str, Remark] = {r.id: r for pool in DEFAULT_REMARKS.values() for r in pool}
    for key in sorted(overrides):
        value = overrides[key]
        pool, number = parse_id(key)
        if value is None:
            lines.pop(key, None)
            continue
        original = DEFAULT_MARKUP.get(key)
        if original is not None and (value == original or value == legacy_markup(key)):
            continue                                            # the default, unchanged: its exact spaces stay (a 0.10.0 file's too, SZ.1)
        parsed = parse_markup(value)
        for reason in parsed.problems:
            problems.add(key, reason)
        if parsed.pieces is None:
            problems.add(key, "the line is left out" if original is None else "the original line is used")
            continue
        known = PLACEHOLDERS.get(pool, ())
        unknown = sorted({p for text in _texts_of(parsed.pieces) for p in _PLACEHOLDER.findall(text) if p not in known})
        if unknown:
            problems.add(key, "%s is not known in this pool and is spoken as written (known: %s)"
                         % (", ".join(unknown), ", ".join(known) or "none"))
        lines[key] = Remark(key, pool, number, parsed.pieces, to_markup(parsed.pieces), False)
    grouped: dict[str, list[Remark]] = {pool: [] for pool in POOLS_BUILT}
    for remark in lines.values():
        grouped[remark.pool].append(remark)
    return RemarkPools({pool: tuple(items) for pool, items in grouped.items()})


# ----- the draw and the line -----

def _fill(text: str, values: Mapping[str, str]) -> str:
    for placeholder, value in values.items():
        text = text.replace(placeholder, value)
    return text


def filled(pieces: tuple, values: Mapping[str, str]) -> tuple:
    """The pieces with the placeholders replaced in every text (the radio banter's <commentator>, SZ.1)."""
    return _filled(pieces, values)


def _filled(pieces: tuple, values: Mapping[str, str]) -> tuple:
    """The pieces with the pool's placeholders replaced in every text, the choices of [one of:] too."""
    out = []
    for piece in pieces:
        if not isinstance(piece, Speak):
            out.append(piece)
            continue
        items = []
        for item in piece.items:
            if isinstance(item, Text):
                items.append(Text(_fill(item.text, values)))
            elif isinstance(item, OneOf):
                items.append(OneOf(tuple(tuple(Text(_fill(sub.text, values)) if isinstance(sub, Text) else sub
                                                for sub in option) for option in item.options)))
            else:
                items.append(item)
        out.append(Speak(tuple(items), piece.faster))
    return tuple(out)


def _has_name(pieces: tuple) -> bool:
    for piece in pieces:
        if isinstance(piece, Speak):
            for item in piece.items:
                if isinstance(item, NameRef):
                    return True
                if isinstance(item, OneOf) and any(isinstance(sub, NameRef) for option in item.options for sub in option):
                    return True
    return False


def pick(pool_lines: tuple[Remark, ...], recent: list[str], rnd) -> Remark | None:
    """One line, never one of the last three spoken when the pool has more than three (G-D1 bounds the redraw)."""
    if not pool_lines:
        return None
    size = len(pool_lines)
    if size <= RECENT_REMARKS:
        return pool_lines[rnd(size) - 1]
    index = rnd.redraw(lambda: rnd(size), lambda n: pool_lines[n - 1].id not in recent,
                       lambda: next(n for n in range(1, size + 1) if pool_lines[n - 1].id not in recent), "remark line")
    return pool_lines[index - 1]


def say_remark(game, state, record, pool: str, values: Mapping[str, str], say=None, exclude=(), rnd=None) -> Remark | None:
    """Draw and say one remark of `pool` (F8 silences the commentary pools before any draw). Returns the line said. `say` is
    the speaker of its parts (None: the announcer's `say`; pool QB passes say4). `exclude`: IDs that may not be drawn this
    time (RVC03 after a booth review, SX.6). `rnd`: the generator of the draws (None: the game's; the broadcast gives its own, so the
    game's draws do not move, SY.1)."""
    rnd = rnd if rnd is not None else game.rnd
    if pool in COMMENTARY_POOLS and game.comtog == 1:
        return None
    pools = getattr(game, "remark_pools", None) or DEFAULT_POOLS
    recent = list(record.recent.get(pool, []))
    lines = tuple(line for line in pools.lines(pool) if line.id not in exclude)
    if not lines and pool in PLAY_BY_PLAY_POOLS:       # the play-by-play always has a sentence (CUSTOMIZABLE_CONTENT 13 L13)
        lines = DEFAULT_REMARKS[pool]
    remark = pick(lines, recent, rnd)
    if remark is None:
        return None
    record.recent[pool] = (recent + [remark.id])[-RECENT_REMARKS:]
    name = ""
    if _has_name(remark.pieces):
        names = state.banter_names
        index = rnd(NAME_LIST_SIZE)
        name = names[index - 1] if index <= len(names) else ""
    pieces = _filled(remark.pieces, {"<commentator>": commentator_of(game), **values})
    choices = [rnd(size) for size in choice_sizes(pieces)]
    play_line(game, pieces, name, state.quarterbacks.get(2, ""), choices, say)
    return remark


# ----- remarks.txt -----

NOTES = (
    "These are the announcer's remarks of the N. F. L. rules. The game reads this file only when the Rules setting of the F9 "
    "menu is N. F. L. rules.",
    "Each line is an ID, an equals sign and the remark. The letters of the ID say the pool: TO are the remarks after a time out,",
    "CHS the strong hints after a ruling that was wrong and CHC the hints after a close call, RVR the remarks after a review",
    "changed a ruling and RVC after a ruling stood or was confirmed (RVC03 only after a challenge that lost),",
    "ON the remarks when an onside kick is declared, QB the sentences that start a quarterback keeper or draw (they are",
    "the play-by-play and stay on when you switch the comments off with F8), PN the remarks after a penalty is accepted.",
    "Change a line to say something else. Write TO03 = off to switch a line off. Delete a line to get the original back.",
    "Add your own lines with a new number in a pool, TO06 or PN05 and up. A remark is chosen by chance, never one of the last three.",
    "In a line, <team> is the team that called the time out, kicked the onside kick, has the ball (QB), was flagged or, in the",
    "replay pools, the team the ruling went against,",
    "<coach> is your name and",
    "<quarterback> that team's quarterback (in a QB line the quarterback who runs); in a PN line <surname> is the player the",
    "flag was on.",
    "The words in square brackets of banter.txt work here too: [sound my laugh.wav], [pause], [bleep], [one of: a | b].",
    "A line has at most 500 characters and 20 parts. The F8 key switches all comments off, these too, except the QB lines:",
    "they are the play by play of a run and stay on; if you switch every QB line off, the original five are used.",
    "BN are the announcer's radio banter, 142 lines that the N. F. L. rules use instead of the jokes of the original (banter.txt keeps the",
    "original's lines for the Classic rules). They fit any moment, so they have few <...> words. ASK are the announcer's questions to the color",
    "commentator, who is called Ghip until you choose another name in F9, Rules, Commentator. <commentator> is that name, in every pool.",
    "The other new pools are the color commentator's, said in a voice of their own: CKO before the opening kick off, CBG after a gain of 20",
    "yards or more, CSK after a sack, CTV after a turn over, CTD after a touch down, CFG after a field goal, CFM after a missed kick, CTC and",
    "CTS after a third down made or stopped, CFD when a team goes for it on fourth down, CRZ inside the twenty, CPN after a penalty, CTM at the",
    "two minute warning, CQE at the end of the first and third quarter, CHT at half time, CFN and CFT at the end (a win, a tie), CTT in a",
    "close fourth quarter and CBO in a game that is decided. In them <team> is the team the line is about, <opponent> the other team,",
    "<quarterback> that team's quarterback, <yards> the gain, <situation> a whole clause with the score (the Bengals lead the Jets 17 to 10),",
    "<quarter> the quarter and <coach> your name; each pool says which of them it has. F9, Rules, Broadcast switches the commentator off.",
)


def default_entries() -> list[tuple[str, str]]:
    return [(r.id, r.markup) for pool in POOLS_BUILT for r in DEFAULT_REMARKS[pool]]


def overrides_of(entries, problems) -> dict[str, str | None]:
    """The player's entries of remarks.txt by canonical ID; a non-remark ID, a second line for an ID and an empty value are
    problems (the default stays)."""
    overrides: dict[str, str | None] = {}
    for entry in entries:
        parsed = parse_id(entry.id)
        if parsed is None:
            problems.add("line %d" % entry.line, "the ID %s is not a remark ID (%s and a number), the line is ignored"
                         % (entry.id, ", ".join(POOLS_BUILT)))
            continue
        key = remark_id(*parsed)
        if key in overrides:
            problems.add(key, "this ID is there twice, the first line is used")
            continue
        if entry.value.casefold() == "off":
            overrides[key] = None
        elif entry.value == "":
            problems.add(key, "the line has no text (write off to switch a line off), the original is used")
        elif entry.value.strip() in RETIRED.get(key, ()):
            continue          # RS.1 (D-179): an unchanged default of an earlier build, not the player's line: the new default is used
        else:
            overrides[key] = entry.value
    return overrides
