"""The player's customization: teams.txt, divisions.txt, surnames.txt, banter.txt and the sounds folder. This is inspired by Jim Kitchen.

D-032 items 7 to 11, D-035, D-048, CUSTOMIZABLE_CONTENT 3 to 6, 10 and 12, playbook 7.9 and 7.10. One folder, `customize`
(`paths.customize_dir()`), holds the files the player edits; footplay.txt and footplay.previous.txt live in it too but belong
to the store of S7.5 (data/files/store.py), which reads, repairs and writes them: this module only CHECKS footplay.txt for the
Customize menu and never changes it. `sounds` below it holds the player's own sound files for the banter.

`Customization` loads every list once when it is made (and again on reload), always ending with usable values:

* the built-in originals are the defaults and are never edited (game/league.py, assets/data/surnames.txt, game/banter_lines.py);
* a player's entry with the same ID replaces the default, a missing ID keeps it, an unknown ID is a problem and ignored;
* a bad entry (a name the rules refuse, a line the markup refuses) keeps the default and is a problem; every file with
  problems gives ONE spoken summary and its lines in the log;
* team names must all differ and division names must all differ (ignoring case): a collision sends the later entry back to
  its original name, and an original name taken by an earlier team's new name becomes "<name> 2" (then "3" and so on);
* a damaged file (data/customlists.py: empty, binary, no header, another list's header, another format version) is copied to
  <name>.damagedN and written again from the originals, one notice; a locked file or an unwritable folder uses the originals
  this time and says so; a missing file or folder is made again, silently.

Nothing here raises. The names are what the voice speaks (the original has no written form), 1 to 30 characters, no comma, no
semicolon, no control character; the count of teams (32), divisions (8) and surnames (1,708) is fixed (CUSTOMIZABLE_CONTENT 5).
"""
from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from typing import Callable

from ..audio.wavdata import SoundLoadError, load_sound_file
from ..game import league as league_module
from ..game.banter_markup import Sound
from ..game.banter_pool import DEFAULT_LINES, BanterPool, banter_id, banter_number, build_pool
from ..game.names import POOL_SIZE, load_surnames
from . import customlists as cl
from .files import playernames
from .healing import read_player_text

log = logging.getLogger("nfl4.data")

GAME = "NFL Football 4"
SOUNDS_FOLDER = "sounds"
NAME_MIN, NAME_MAX = 1, 30

TEAMS, DIVISIONS, SURNAMES, BANTER = "teams", "divisions", "surnames", "banter"


@dataclass(frozen=True)
class ListSpec:
    key: str
    file_name: str
    nouns: str            # what the file holds, in the notices ("team names")
    original_nouns: str   # "the original team names"


SPECS: tuple[ListSpec, ...] = (
    ListSpec(TEAMS, "teams.txt", "team names", "the original team names"),
    ListSpec(DIVISIONS, "divisions.txt", "division names", "the original division names"),
    ListSpec(SURNAMES, "surnames.txt", "surnames", "the original surnames"),
    ListSpec(BANTER, "banter.txt", "banter lines", "the original banter lines"),
)
SPEC_BY_KEY = {spec.key: spec for spec in SPECS}

# The texts the clone adds (CLONE texts, GAP_REGISTER section 8; S8.2 listens to them)
DAMAGED_RESET = " The file %s was damaged and has been reset to %s. A copy was saved. "
DAMAGED_KEPT = " The file %s is damaged and could not be replaced. %s are used this time. "
LOCKED_NOTICE = " The file %s is in use by another program. %s are used this time. "
UNWRITABLE_ONE = " The file %s could not be made, so %s are used. "
UNWRITABLE_MANY = " The game could not write its customization files, so the original names and lines are used. "

TEAM_NOTES = (
    "These are the 32 team names. Each line is an ID, an equals sign and the name the voice speaks.",
    "Change a name, save the file, then choose Reload in the Customize item of the F9 menu, or start the game again.",
    "The ID, T01 to T32, must stay as it is. A name has 1 to 30 characters, with no comma and no semicolon.",
    "Two teams cannot have the same name. Spell a name the way the voice should say it.",
    "Delete a line to get the original name back. Delete the whole file to get all the original names back.",
)
DIVISION_NOTES = (
    "These are the 8 division names. Each line is an ID, an equals sign and the words the voice speaks.",
    "The conference names A. F. C. and N. F. C. also appear inside fixed sentences of the play offs. They do not change here.",
    "Change a name, save the file, then choose Reload in the Customize item of the F9 menu, or start the game again.",
    "The ID, D1 to D8, must stay as it is. A name has 1 to 30 characters, with no comma and no semicolon.",
    "Two divisions cannot have the same name. Delete a line to get the original name back.",
)
SURNAME_NOTES = (
    "These are the 1,708 surnames the game draws the players' names from. Each line is an ID, an equals sign and the name.",
    "Only the names change: there are always 1,708. Spell a name the way the voice should say it.",
    "A name has 1 to 30 characters, with no comma and no semicolon. Delete a line to get the original name back.",
    "Your own team's players are in the file footplay.txt, which is next to this one.",
)
BANTER_NOTES = (
    "These are the announcer's remarks. B001 to B142 are the original lines. Each line is an ID, an equals sign and the line.",
    "Change a line to say something else. Write B045 = off to switch a line off. Delete a line to get the original back.",
    "Add your own lines with a new ID, B143 and up. Each line is chosen by chance, and none twice in a game.",
    "In a line these words in square brackets do something:",
    "  [name] is a player's name drawn by the game, the same name everywhere in the line.",
    "  [opponent quarterback] is the name of the other team's quarterback.",
    "  [bleep] plays the original's bleep sound.",
    "  [sound my laugh.wav] plays your own sound file from the sounds folder, which is next to this file.",
    "  [pause] is a short pause of random length, and [pause 2] a pause of 2 seconds.",
    "  [then] ends a spoken part: the words after it are said as a new part.",
    "  [faster] ends a spoken part and says the next part one step faster.",
    "  [one of: some words | other words | more words] says one of them, chosen by chance.",
    "A line can be words only, a sound only, or both. Examples:",
    "  B143 = What a hit! [sound crunch.wav] Ghip, did you see that?",
    "  B144 = [sound crowd boo.wav]",
    "A line has at most 500 characters and 20 parts. The F8 key switches all comments off, yours too.",
)


def name_problem(name: str) -> str | None:
    """None when the name passes the clone's limits (CUSTOMIZABLE_CONTENT 10), else the plain reason."""
    if not NAME_MIN <= len(name) <= NAME_MAX:
        return "a name has %d to %d characters" % (NAME_MIN, NAME_MAX)
    if "," in name or ";" in name:
        return "a name cannot have a comma or a semicolon"
    if any(ord(c) < 32 or ord(c) == 127 for c in name):
        return "a name cannot have a control character"
    return None


def unique_variant(name: str, used: set[str]) -> str:
    """"Browns" taken: "Browns 2", then "Browns 3", and so on (cut short to stay within 30 characters)."""
    number = 2
    while True:
        suffix = " %d" % number
        candidate = name[:NAME_MAX - len(suffix)].rstrip() + suffix
        if candidate.casefold() not in used:
            return candidate
        number += 1


def explicit_names(entries, pattern: re.Pattern, count: int, problems: cl.Problems) -> dict[int, str]:
    """The player's names by number: an unknown ID, a second entry for an ID and a name the rules refuse are problems."""
    values: dict[int, str] = {}
    seen: set[int] = set()
    for entry in entries:
        match = pattern.fullmatch(entry.id)
        number = int(match.group(1)) if match else 0
        if not 1 <= number <= count:
            problems.add("line %d" % entry.line, "the ID %s is not in this list, the line is ignored" % entry.id)
            continue
        if number in seen:
            problems.add(entry.id, "this ID is there twice, the first line is used")
            continue
        seen.add(number)
        reason = name_problem(entry.value)
        if reason:
            problems.add(entry.id, "%s, the original name is used" % reason)
            continue
        values[number] = entry.value
    return values


def distinct_names(explicit: dict[int, str], defaults: tuple[str, ...], label: Callable[[int], str], what: str,
                   problems: cl.Problems) -> tuple[str, ...]:
    """Every name different ignoring case: the player's names first, in the order of the IDs (a name an earlier entry took
    sends the later entry back to its original name); then each other slot takes its original name, or "<name> 2" when an
    earlier player's name took it."""
    final: dict[int, str] = {}
    used: set[str] = set()
    for number in sorted(explicit):
        name = explicit[number]
        if name.casefold() in used:
            problems.add(label(number), "the name %s is already used by another %s, the original name is used" % (name, what))
            continue
        final[number] = name
        used.add(name.casefold())
    for number in range(1, len(defaults) + 1):
        if number in final:
            continue
        name = defaults[number - 1]
        if name.casefold() in used:
            variant = unique_variant(name, used)
            problems.add(label(number), "the original name %s is used by another %s, so this one is called %s"
                         % (name, what, variant))
            name = variant
        final[number] = name
        used.add(name.casefold())
    return tuple(final[number] for number in range(1, len(defaults) + 1))


@dataclass
class Snapshot:
    """What the files held at one load, with the built-in values where they could not be used."""
    team_names: tuple[str, ...]
    division_names: tuple[str, ...]
    surnames: list[str] | None            # None: the original surname asset could not be read (the game reads it itself)
    banter: BanterPool
    statuses: dict[str, str] = field(default_factory=dict)          # list key -> load status (data.customlists)
    problems: dict[str, cl.Problems] = field(default_factory=dict)  # list key -> what was wrong inside the file
    notices: list[str] = field(default_factory=list)                # the spoken sentences of this load
    sound_files: list[str] = field(default_factory=list)            # the sound files the player's banter lines name

    def problem_count(self, key: str) -> int:
        problems = self.problems.get(key)
        return problems.count if problems else 0


@dataclass
class ResetResult:
    done: list[str] = field(default_factory=list)       # file names written again from the originals
    kept: list[str] = field(default_factory=list)       # the player's files kept as <name>.before-reset
    failed: list[str] = field(default_factory=list)


class Customization:
    def __init__(self, folder: str, default_surnames: Callable[[], list[str]] | None = None,
                 sound_probe: Callable[[str], str | None] | None = None):
        self.folder = folder
        self.sounds_dir = os.path.join(folder, SOUNDS_FOLDER)
        self._default_surnames = default_surnames or load_surnames
        self._surname_defaults: list[str] | None = None
        self.sound_probe = sound_probe or probe_sound_file
        self.files: dict[str, cl.ListFile] = {
            spec.key: cl.ListFile(folder, spec.file_name, GAME, spec.key, lambda key=spec.key: self.default_text(key))
            for spec in SPECS}
        self._notices: list[str] = []
        self._told_unwritable = False
        self.snapshot = self._load()
        self._notices.extend(self.snapshot.notices)

    # ----- the built-in text of each file -----

    def surname_defaults(self) -> list[str] | None:
        if self._surname_defaults is None:
            try:
                names = list(self._default_surnames())
                self._surname_defaults = names if len(names) == POOL_SIZE else None
            except Exception:
                log.exception("the original surnames could not be read")
                self._surname_defaults = None
        return self._surname_defaults

    def default_text(self, key: str) -> str:
        if key == TEAMS:
            entries = [("T%02d" % n, name) for n, name in enumerate(league_module.DEFAULT_TEAM_NAMES, start=1)]
            return cl.render_list(GAME, TEAMS, TEAM_NOTES, entries)
        if key == DIVISIONS:
            entries = [("D%d" % n, name) for n, name in enumerate(league_module.DEFAULT_DIVISION_NAMES, start=1)]
            return cl.render_list(GAME, DIVISIONS, DIVISION_NOTES, entries)
        if key == SURNAMES:
            names = self.surname_defaults()
            if names is None:
                raise RuntimeError("the original surnames are not available")
            return cl.render_list(GAME, SURNAMES, SURNAME_NOTES, [("S%04d" % n, name) for n, name in enumerate(names, start=1)])
        if key == BANTER:
            return cl.render_list(GAME, BANTER, BANTER_NOTES, [(banter_id(line.number), line.markup) for line in DEFAULT_LINES])
        raise KeyError(key)

    # ----- loading -----

    def _load(self) -> Snapshot:
        """Read every list; never raises."""
        try:
            os.makedirs(self.sounds_dir, exist_ok=True)
        except OSError:
            log.warning("could not make the folder %s", self.sounds_dir, exc_info=True)
        snapshot = Snapshot(league_module.DEFAULT_TEAM_NAMES, league_module.DEFAULT_DIVISION_NAMES,
                            None, BanterPool(DEFAULT_LINES))
        loads = {spec.key: self.files[spec.key].load() for spec in SPECS}
        for spec in SPECS:
            load = loads[spec.key]
            problems = cl.Problems(spec.file_name)
            snapshot.statuses[spec.key] = load.status
            snapshot.problems[spec.key] = problems
            entries = load.parsed.entries if load.parsed is not None else []
            if load.parsed is not None:
                for number, reason in load.parsed.bad_lines:
                    problems.add("line %d" % number, reason)
            try:
                self._apply_list(spec.key, entries, snapshot, problems)
            except Exception:
                log.exception("the list %s could not be used; the original values stay", spec.file_name)
        self._notices_of(snapshot, loads)
        return snapshot

    def _apply_list(self, key: str, entries, snapshot: Snapshot, problems: cl.Problems) -> None:
        if key == TEAMS:
            explicit = explicit_names(entries, re.compile(r"T(\d{1,2})", re.IGNORECASE), league_module.TEAM_COUNT, problems)
            snapshot.team_names = distinct_names(explicit, league_module.DEFAULT_TEAM_NAMES, lambda n: "T%02d" % n,
                                                 "team", problems)
        elif key == DIVISIONS:
            explicit = explicit_names(entries, re.compile(r"D(\d)", re.IGNORECASE), league_module.DIVISIONS, problems)
            snapshot.division_names = distinct_names(explicit, league_module.DEFAULT_DIVISION_NAMES, lambda n: "D%d" % n,
                                                     "division", problems)
        elif key == SURNAMES:
            defaults = self.surname_defaults()
            explicit = explicit_names(entries, re.compile(r"S(\d{1,4})", re.IGNORECASE), POOL_SIZE, problems)
            if defaults is not None:
                snapshot.surnames = [explicit.get(n, defaults[n - 1]) for n in range(1, POOL_SIZE + 1)]
        elif key == BANTER:
            overrides: dict[int, str | None] = {}
            seen: set[int] = set()
            for entry in entries:
                number = banter_number(entry.id)
                if number is None:
                    problems.add("line %d" % entry.line, "the ID %s is not a banter ID (B001 to B9999), the line is ignored"
                                 % entry.id)
                elif number in seen:
                    problems.add(entry.id, "this ID is there twice, the first line is used")
                else:
                    seen.add(number)
                    if entry.value.casefold() == "off":
                        overrides[number] = None
                    elif entry.value == "":
                        problems.add(entry.id, "the line has no text (write off to switch a line off), the original is used")
                    else:
                        overrides[number] = entry.value
            snapshot.banter = build_pool(overrides, problems)
            snapshot.sound_files = sorted({piece.file for line in snapshot.banter.lines if not line.builtin
                                           for piece in line.pieces if isinstance(piece, Sound)})

    def _notices_of(self, snapshot: Snapshot, loads) -> None:
        unwritable = [spec for spec in SPECS if snapshot.statuses[spec.key] == cl.UNWRITABLE]
        for spec in SPECS:
            status = snapshot.statuses[spec.key]
            if status == cl.RESET:
                snapshot.notices.append(DAMAGED_RESET % (spec.file_name, spec.original_nouns))
            elif status in (cl.KEPT_DAMAGED, cl.FAILED):
                snapshot.notices.append(DAMAGED_KEPT % (spec.file_name, capital(spec.original_nouns)))
            elif status == cl.LOCKED:
                snapshot.notices.append(LOCKED_NOTICE % (spec.file_name, capital(spec.original_nouns)))
            elif status == cl.UNWRITABLE and len(unwritable) == 1:
                snapshot.notices.append(UNWRITABLE_ONE % (spec.file_name, spec.original_nouns))
            count = snapshot.problem_count(spec.key)
            if count:
                snapshot.notices.append(cl.problems_notice(spec.file_name, count))
        if len(unwritable) > 1:
            snapshot.notices.append(UNWRITABLE_MANY)

    # ----- what the program asks for -----

    def reload(self) -> list[str]:
        """The Customize menu's reload: read every file again. The new values are `snapshot`; the sentences are returned."""
        self.snapshot = self._load()
        return list(self.snapshot.notices)

    def take_notices(self) -> list[str]:
        """The notice source of the program: it first makes any file or folder that has gone missing since the last look
        (silently: a missing file is the player asking for the originals, and the loaded values stay in use), then hands over
        the sentences of the start once."""
        self.tend()
        notices, self._notices = self._notices, []
        return notices

    def tend(self) -> None:
        """Recreate a missing file or sounds folder from the originals (playbook 7.10: at the next safe moment)."""
        try:
            os.makedirs(self.sounds_dir, exist_ok=True)
        except OSError:
            log.warning("could not make the folder %s", self.sounds_dir, exc_info=True)
        for spec in SPECS:
            file = self.files[spec.key]
            if file.exists():
                continue
            try:
                os.makedirs(self.folder, exist_ok=True)
            except OSError:
                pass
            if not file.write_defaults() and not self._told_unwritable:
                self._told_unwritable = True
                self._notices.append(UNWRITABLE_MANY)

    def check(self) -> str:
        """The Customize menu's check: every file is read as a reload does (a damaged one is healed, the sentences say so)
        but nothing is applied. Returns what is read aloud."""
        snapshot = self._load()
        parts = [notice.strip() for notice in snapshot.notices if "found in" not in notice]
        for spec in SPECS:
            count = snapshot.problem_count(spec.key)
            parts.append("%s: %s." % (spec.file_name, "no problems" if not count else cl.plural(count, "problem")))
        names = snapshot.sound_files
        if names:
            bad = [name for name in names if self.sound_probe(os.path.join(self.sounds_dir, name))]
            parts.append("The banter names %s, %s." % (cl.plural(len(names), "sound file"),
                                                       "all can be used" if not bad else "%d cannot be used" % len(bad)))
        parts.append(self._check_names())
        parts.append("Details of every problem are in the log.")
        return " ".join(part for part in parts if part)

    def _check_names(self) -> str:
        path = os.path.join(self.folder, playernames.FILE_NAME)
        if not os.path.isfile(path):
            return ""
        try:
            parsed = playernames.parse(read_player_text(path))
        except (OSError, ValueError):
            log.warning("%s could not be read", path, exc_info=True)
            return "%s: it cannot be read now. The game makes new random names." % playernames.FILE_NAME
        for problem in parsed.problems:
            log.warning("%s: %s", path, problem)
        if not parsed.problems:
            return "%s: no problems." % playernames.FILE_NAME
        return "%s: %s. The game repairs it when the next game starts." % (playernames.FILE_NAME,
                                                                         cl.plural(len(parsed.problems), "problem"))

    def reset(self, key: str | None = None) -> ResetResult:
        """Write the originals again: one list, or all (the player's file is kept as <name>.before-reset). The own roster
        footplay.txt and the player's sound files are never touched. The values are not applied: call `reload` after."""
        result = ResetResult()
        for spec in SPECS:
            if key is not None and spec.key != key:
                continue
            file = self.files[spec.key]
            had_file = os.path.isfile(file.path)
            try:
                ok = file.reset()
            except Exception:
                log.exception("could not reset %s", file.path)
                ok = False
            if not ok:
                result.failed.append(spec.file_name)
                continue
            result.done.append(spec.file_name)
            if had_file:
                result.kept.append(spec.file_name)
        return result


def capital(text: str) -> str:
    return text[:1].upper() + text[1:]


def probe_sound_file(path: str) -> str | None:
    """None when the sound file can be used, else the plain reason (the check item)."""
    if not os.path.isfile(path):
        return "the file was not found"
    try:
        load_sound_file(path)
    except SoundLoadError as exc:
        return str(exc)
    except Exception as exc:
        return "%s: %s" % (type(exc).__name__, exc)
    return None
