"""The banter line markup: what a line of banter.txt says, as pieces. This is inspired by Jim Kitchen.

D-035 (the owner's rule that the banter is customizable with own text and own sounds), D-048, CUSTOMIZABLE_CONTENT 12,
playbook 7.9. A line is a sequence of PIECES:

* Speak: one spoken part, said with `say` (the announcer, waited). Its items are plain text, `[name]` (the name drawn from
  the 58-name list, the same in the whole line), `[opponent quarterback]` and `[one of: a | b | c]` (one choice drawn with
  equal chances; each choice is text with `[name]` and `[opponent quarterback]` only);
* Bleep: `[bleep]`, the original's foot13 (played and waited, a key does not cut it);
* Sound: `[sound my laugh.wav]`, a file of the player's from customize\\sounds (played and waited like the bleep);
* Pause: `[pause]` (a random short pause, the original's rady) or `[pause 2]` (that many seconds, 0.1 to 10).

Two more words shape the parts: `[then]` ends the spoken part (the next text is a separate part, as the original's second
text is) and `[faster]` ends it too and speaks the next part one rate step faster (the original's line 113). The words are not
case sensitive. An unknown word in brackets is spoken as text and reported; an opening bracket with no closing one, a sound
name with a folder in it, a line of more than 500 characters or 20 pieces, a control character, or a line that says nothing
make the line bad (the original line with that ID is used, a new ID is left out).

The 142 original lines are written in this markup by `default_pieces` and `to_markup` (the file the game writes on its first
start), and a player's line that is exactly the markup of the original is the original (built in, with its exact spaces), so
an unchanged file plays exactly the original's lines.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .banter_lines import NAME, OPPONENT_QB, BanterLine

MAX_LINE_CHARS = 500
MAX_PIECES = 20
MAX_OPTIONS = 20
MIN_PAUSE, MAX_PAUSE = 0.1, 10.0
MAX_TOTAL_PAUSE = 30.0              # the pauses of one line together (keys never cut a pause short)
MAX_FILE_NAME = 100
BAD_FILE_CHARACTERS = '\\/:*?"<>|'
DEVICE_NAMES = frozenset(["con", "prn", "aux", "nul", "conin$", "conout$"]
                         + ["com%d" % n for n in range(10)] + ["lpt%d" % n for n in range(10)])


@dataclass(frozen=True)
class Text:
    text: str


@dataclass(frozen=True)
class NameRef:
    """The banter name the routine drew (the same in the whole line)."""


@dataclass(frozen=True)
class OppQbRef:
    """The opponent's quarterback (original line 45)."""


@dataclass(frozen=True)
class OneOf:
    options: tuple[tuple, ...]          # each option is a tuple of Text, NameRef and OppQbRef


@dataclass(frozen=True)
class Speak:
    items: tuple
    faster: bool = False                # one rate step faster (the original's line 113)


@dataclass(frozen=True)
class Bleep:
    pass


@dataclass(frozen=True)
class Sound:
    file: str


@dataclass(frozen=True)
class Pause:
    seconds: float | None = None        # None: rady, a random pause


class MarkupError(ValueError):
    """The line cannot be used at all (the reason is plain words for the log)."""


@dataclass
class ParsedMarkup:
    pieces: tuple | None                # None: the line is bad
    problems: list[str]


# ----- the original's lines as pieces -----

def _items_of(text: str) -> tuple:
    items: list = []
    for part in re.split("(%s|%s)" % (re.escape(NAME), re.escape(OPPONENT_QB)), text):
        if part == NAME:
            items.append(NameRef())
        elif part == OPPONENT_QB:
            items.append(OppQbRef())
        elif part:
            items.append(Text(part))
    return tuple(items)


def default_pieces(line: BanterLine) -> tuple:
    """GoSub 0x45915e step 5 and 6: the first text (one rate step faster for line 113), foot13 after it `bleeps` times, then
    the second text (lines 101 and 110: one of the alternatives, drawn). Every text keeps its exact spaces."""
    if line.rate_step not in (0, 1):
        raise ValueError("banter line %d has the rate step %r" % (line.number, line.rate_step))
    pieces: list = [Speak(_items_of(line.first), faster=line.rate_step == 1)]
    pieces.extend(Bleep() for _ in range(line.bleeps))
    if line.alternatives:
        pieces.append(Speak((OneOf(tuple(_items_of(alt) for alt in line.alternatives)),)))
    elif line.second != "":
        pieces.append(Speak(_items_of(line.second)))
    return tuple(pieces)


# ----- pieces to markup -----

def _items_markup(items: tuple) -> str:
    out = []
    for item in items:
        if isinstance(item, Text):
            out.append(item.text)
        elif isinstance(item, NameRef):
            out.append("[name]")
        elif isinstance(item, OppQbRef):
            out.append("[opponent quarterback]")
        elif isinstance(item, OneOf):
            out.append("[one of: " + " | ".join(_items_markup(option).strip() for option in item.options) + "]")
    return "".join(out)


def to_markup(pieces: tuple) -> str:
    """The text of a line in banter.txt for these pieces (parts are stripped of their outer spaces)."""
    out: list[str] = []
    previous_speak = False
    for piece in pieces:
        if isinstance(piece, Speak):
            if previous_speak:
                out.append("[then]")
            if piece.faster:
                out.append("[faster]")
            out.append(_items_markup(piece.items).strip())
            previous_speak = True
            continue
        previous_speak = False
        if isinstance(piece, Bleep):
            out.append("[bleep]")
        elif isinstance(piece, Sound):
            out.append("[sound %s]" % piece.file)
        elif isinstance(piece, Pause):
            out.append("[pause]" if piece.seconds is None else "[pause %g]" % piece.seconds)
    return " ".join(out)


# ----- markup to pieces -----

def _tokens(value: str) -> list[tuple[str, str]]:
    """("text", s) and ("tag", the words between a pair of brackets); brackets may nest inside [one of: ...]."""
    out: list[tuple[str, str]] = []
    buffer: list[str] = []
    index, size = 0, len(value)
    while index < size:
        char = value[index]
        if char != "[":
            buffer.append(char)
            index += 1
            continue
        depth, end = 1, index + 1
        while end < size and depth:
            depth += {"[": 1, "]": -1}.get(value[end], 0)
            end += 1
        if depth:
            raise MarkupError("an opening bracket has no closing bracket")
        if buffer:
            out.append(("text", "".join(buffer)))
            buffer = []
        out.append(("tag", value[index + 1:end - 1]))
        index = end
    if buffer:
        out.append(("text", "".join(buffer)))
    return out


def _split_options(body: str) -> list[str]:
    parts, depth, start = [], 0, 0
    for index, char in enumerate(body):
        if char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
        elif char == "|" and depth == 0:
            parts.append(body[start:index])
            start = index + 1
    parts.append(body[start:])
    return parts


def _tidy(items: list) -> tuple:
    """Join neighbouring texts, strip the outer spaces of the part, drop what is empty (a blank part says nothing)."""
    merged: list = []
    for item in items:
        if isinstance(item, Text):
            if not item.text:
                continue
            if merged and isinstance(merged[-1], Text):
                merged[-1] = Text(merged[-1].text + item.text)
                continue
        merged.append(item)
    if merged and isinstance(merged[0], Text):
        merged[0] = Text(merged[0].text.lstrip())
    if merged and isinstance(merged[-1], Text):
        merged[-1] = Text(merged[-1].text.rstrip())
    merged = [item for item in merged if not (isinstance(item, Text) and item.text == "")]
    return tuple(merged)


def _valid_file_name(name: str) -> str | None:
    """None when the name is fine, else the plain reason."""
    if not name:
        return "[sound] has no file name"
    if len(name) > MAX_FILE_NAME:
        return "the sound file name has more than %d characters" % MAX_FILE_NAME
    if any(c in BAD_FILE_CHARACTERS or ord(c) < 32 for c in name) or name.startswith(".") or name.endswith((" ", ".")):
        return "the sound file name '%s' has a folder or a character a file name cannot have; put the file in the sounds folder" % name
    if name.split(".")[0].rstrip().lower() in DEVICE_NAMES:         # CON, NUL, COM1 and the others are devices, not files
        return "the sound file name '%s' is the name of a Windows device, not of a file" % name
    return None


class _Builder:
    def __init__(self, problems: list[str]):
        self.problems = problems
        self.pieces: list = []
        self.items: list = []
        self.faster = False

    def text(self, text: str) -> None:
        if text:
            self.items.append(Text(text))

    def close(self) -> None:
        items = _tidy(self.items)
        self.items = []
        if items:
            self.pieces.append(Speak(items, self.faster))
            self.faster = False

    def inline(self, raw: str) -> tuple:
        """One choice of [one of: ...]: text, [name] and [opponent quarterback]."""
        items: list = []
        for kind, content in _tokens(raw):
            if kind == "text":
                items.append(Text(content))
                continue
            low = " ".join(content.lower().split())
            if low == "name":
                items.append(NameRef())
            elif low == "opponent quarterback":
                items.append(OppQbRef())
            else:
                self.problems.append("only [name] and [opponent quarterback] can be inside [one of:], [%s] is spoken as text"
                                     % content.strip())
                items.append(Text("[" + content + "]"))
        return _tidy(items)

    def tag(self, content: str) -> None:
        word = " ".join(content.split())
        low = word.lower()
        if low == "name":
            self.items.append(NameRef())
        elif low == "opponent quarterback":
            self.items.append(OppQbRef())
        elif low == "bleep":
            self.close()
            self.pieces.append(Bleep())
        elif low == "then":
            self.close()
        elif low == "faster":
            self.close()
            self.faster = True
        elif low == "pause":
            self.close()
            self.pieces.append(Pause())
        elif re.fullmatch(r"pause \d+(\.\d+)?", low):
            seconds = float(low.split()[1])
            if MIN_PAUSE <= seconds <= MAX_PAUSE:
                self.close()
                self.pieces.append(Pause(seconds))
            else:
                self.unknown(content, "a pause is %g to %g seconds" % (MIN_PAUSE, MAX_PAUSE))
        elif re.match(r"sound\s", low):
            name = content.strip()[5:].strip()
            reason = _valid_file_name(name)
            if reason:
                raise MarkupError(reason)
            self.close()
            self.pieces.append(Sound(name))
        elif low == "sound":
            raise MarkupError("[sound] has no file name")
        elif re.match(r"one of\s*:", low):
            body = content.strip().split(":", 1)[1]
            options = []
            for raw in _split_options(body):
                if not raw.strip():
                    self.problems.append("an empty choice in [one of:] is left out")
                    continue
                items = self.inline(raw)
                if items:
                    options.append(items)
            if len(options) > MAX_OPTIONS:
                raise MarkupError("[one of:] has more than %d choices" % MAX_OPTIONS)
            if options:
                self.items.append(OneOf(tuple(options)))
            else:
                self.problems.append("[one of:] has no choices, it is left out")
        else:
            self.unknown(content, "the word is not known")

    def unknown(self, content: str, reason: str) -> None:
        self.problems.append("[%s]: %s, it is spoken as text" % (content.strip(), reason))
        self.items.append(Text("[" + content + "]"))

    def finish(self) -> tuple:
        self.close()
        return tuple(self.pieces)


def parse_markup(value: str) -> ParsedMarkup:
    """The pieces of a line of banter.txt. Never raises: a bad line has pieces None and its reason in problems."""
    problems: list[str] = []
    if len(value) > MAX_LINE_CHARS:
        return ParsedMarkup(None, ["the line has more than %d characters" % MAX_LINE_CHARS])
    if any(ord(c) < 32 or ord(c) == 127 for c in value):
        return ParsedMarkup(None, ["the line has a control character"])
    builder = _Builder(problems)
    try:
        for kind, content in _tokens(value):
            if kind == "text":
                builder.text(content)
            else:
                builder.tag(content)
        pieces = builder.finish()
    except MarkupError as exc:
        return ParsedMarkup(None, problems + [str(exc)])
    if not pieces:
        return ParsedMarkup(None, problems + ["the line says and plays nothing"])
    if len(pieces) > MAX_PIECES:
        return ParsedMarkup(None, problems + ["the line has more than %d pieces" % MAX_PIECES])
    if sum(p.seconds for p in pieces if isinstance(p, Pause) and p.seconds is not None) > MAX_TOTAL_PAUSE:
        return ParsedMarkup(None, problems + ["the line has more than %d seconds of pauses" % MAX_TOTAL_PAUSE])
    return ParsedMarkup(pieces, problems)


# ----- saying a part -----

def speak_text(piece: Speak, name: str, opponent_quarterback: str, choices) -> str:
    """The words of a part: `choices` is an iterator of the 1-based choices drawn for the [one of:] items, in line order."""
    out = []
    for item in piece.items:
        if isinstance(item, Text):
            out.append(item.text)
        elif isinstance(item, NameRef):
            out.append(name)
        elif isinstance(item, OppQbRef):
            out.append(opponent_quarterback)
        elif isinstance(item, OneOf):
            chosen = next(choices, 1)
            option = item.options[min(max(chosen, 1), len(item.options)) - 1]
            out.append("".join(speak_text_item(sub, name, opponent_quarterback) for sub in option))
    return "".join(out)


def speak_text_item(item, name: str, opponent_quarterback: str) -> str:
    if isinstance(item, Text):
        return item.text
    return name if isinstance(item, NameRef) else opponent_quarterback


def choice_sizes(pieces: tuple) -> list[int]:
    """How many choices each [one of:] of the line has, in line order: the sizes of the draws made before it is said."""
    return [len(item.options) for piece in pieces if isinstance(piece, Speak)
            for item in piece.items if isinstance(item, OneOf)]
