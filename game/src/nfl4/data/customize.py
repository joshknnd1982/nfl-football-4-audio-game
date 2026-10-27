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

nfl4 only (rule 0.13, CUSTOMIZABLE_CONTENT 13, PX SX.2): remarks.txt holds the remark pools of the extra features
(extras/remarks.py), since SX.3 penalties.txt the names, switches and weights of the fouls (extras/penalty_list.py), and since
SX.7 the folder `playbooks` with plays.txt, styles.txt and team_styles.txt (extras/playbook_list.py). They are lists in the same format with the same healing, but in use only while the Rules setting is the N. F. L. rules
(`extras` / `use_extras`): with Classic they are never read, made, checked or reset.
"""
from __future__ import annotations

import dataclasses
import logging
import os
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Callable

from ..audio.wavdata import SoundLoadError, load_sound_file
from ..game import league as league_module
from ..game.banter_markup import Sound
from ..game.banter_pool import DEFAULT_LINES, BanterPool, banter_id, banter_number, build_pool
from ..game.names import POOL_SIZE, load_surnames
from . import customlists as cl
from . import debuglog
from .files import playernames
from .healing import read_player_text, save_backup_copy, write_text_atomic

log = logging.getLogger("nfl4.data")

GAME = "NFL Football 4"
SOUNDS_FOLDER = "sounds"
NAME_MIN, NAME_MAX = 1, 30

TEAMS, DIVISIONS, SURNAMES, BANTER = "teams", "divisions", "surnames", "banter"
REMARKS = "remarks"         # nfl4 only (rule 0.13): the extras' remark pools, read only with the N. F. L. rules (SX.2)
PENALTIES = "penalties"     # nfl4 only (rule 0.13): the fouls' names, switches and weights (SX.3)
PLAYS, STYLES, TEAMSTYLES = "plays", "styles", "teamstyles"     # nfl4 only: the playbooks' files in `playbooks` (SX.7)
NEWS = "news"               # nfl4 only (rule 0.13): the Franchise's news lines, read only with the N. F. L. rules (SX.8e)
INJURIES = "injuries"       # nfl4 only (rule 0.13): the Franchise's injury words, read only with the N. F. L. rules (SX.8k)
FAVOURITES = "favourite plays"   # the header word of favourites.txt; nfl4 only (rule 0.13): the player's favourite plays in `playbooks` (SX.10c, extras/plays/favourites.py)
PLAYBOOKS_FOLDER = "playbooks"
FREE_AGENTS = "freeagents"      # nfl4 only (NX-B3, D-145): free_agents.txt, the real free agents of a new franchise
COACHES, ROSTERS, RESPELLINGS = "coaches", "rosters", "respellings"   # nfl4 only (rule 0.13, SX.11, NX-N4): the real coaches and rosters and how they are said
NFL_SURNAMES = "nflsurnames"    # nfl4 only (NX-L12, D-164): nfl_surnames.txt, the real NFL players' last names of the made-up players


@dataclass(frozen=True)
class ListSpec:
    key: str
    file_name: str
    nouns: str            # what the file holds, in the notices ("team names")
    original_nouns: str   # "the original team names"
    folder: str = ""      # a folder of the customize folder that holds the file (the playbooks' three)


SPECS: tuple[ListSpec, ...] = (
    ListSpec(TEAMS, "teams.txt", "team names", "the original team names"),
    ListSpec(DIVISIONS, "divisions.txt", "division names", "the original division names"),
    ListSpec(SURNAMES, "surnames.txt", "surnames", "the original surnames"),
    ListSpec(BANTER, "banter.txt", "banter lines", "the original banter lines"),
)
# CUSTOMIZABLE_CONTENT 13: the files of the extra features are read, made, checked and reset only while the Rules setting is
# the N. F. L. rules (`Customization.use_extras`); with Classic none of them is ever opened
EXTRA_SPECS: tuple[ListSpec, ...] = (
    ListSpec(COACHES, "coaches.txt", "coach names", "the original coach names"),       # SX.11: first, so the older tests that count from the end still do
    ListSpec(ROSTERS, "rosters.txt", "players", "the original players"),
    ListSpec(RESPELLINGS, "respellings.txt", "respellings", "the original respellings"),
    ListSpec(FREE_AGENTS, "free_agents.txt", "free agents", "the original free agents"),       # NX-B3
    ListSpec(NFL_SURNAMES, "nfl_surnames.txt", "surnames of real players", "the original surnames of real players"),     # NX-L12
    ListSpec(REMARKS, "remarks.txt", "remarks", "the original remarks"),
    ListSpec(PENALTIES, "penalties.txt", "penalty names", "the original penalty names"),
    ListSpec(PLAYS, "plays.txt", "play names", "the original play names", PLAYBOOKS_FOLDER),
    ListSpec(STYLES, "styles.txt", "styles", "the original styles", PLAYBOOKS_FOLDER),
    ListSpec(TEAMSTYLES, "team_styles.txt", "team styles", "the original team styles", PLAYBOOKS_FOLDER),
    ListSpec(NEWS, "news.txt", "news lines", "the original news lines"),
    ListSpec(INJURIES, "injuries.txt", "injury words", "the original injury words"),
    ListSpec(FAVOURITES, "favourites.txt", "favourite plays", "no favourite plays", PLAYBOOKS_FOLDER),
)
SPEC_BY_KEY = {spec.key: spec for spec in SPECS + EXTRA_SPECS}

# The texts the game adds (CLONE texts, GAP_REGISTER section 8; S8.2 listens to them)
DAMAGED_RESET = " The file %s was damaged and has been reset to %s. A copy was saved. "
HOLD_STATUSES = (cl.KEPT_DAMAGED, cl.LOCKED, cl.FAILED, cl.UNREADABLE)      # the file cannot be used now and stays as it is
HOLD_REASONS = {cl.KEPT_DAMAGED: "is damaged and could not be replaced", cl.LOCKED: "is in use by another program",
                cl.FAILED: "could not be used", cl.UNREADABLE: "could not be read"}
UNWRITABLE_ONE = " The file %s could not be made, so %s are used. "
UNWRITABLE_MANY = " The game could not write its customization files, so the original names and lines are used. "

TEAM_NOTES = (
    "These are the 32 team names. Each line is an ID, an equals sign and the name the voice speaks.",
    "Change a name, save the file, then choose Reload in the Customize item of the F9 menu, or start the game again.",
    "The ID, T01 to T32, must stay as it is. A name has 1 to 30 characters, with no comma and no semicolon.",
    "Two teams cannot have the same name. Spell a name the way the voice should say it.",
    "Delete a line to get the original name back. Delete the whole file to get all the original names back.",
    "T24 is the Commanders now. The original game called this team the Redskins. Write T24 = Redskins to bring that name back.",
)
TEAM_OLD_LAST_NOTE = TEAM_NOTES[4]             # the last note of a teams.txt written before the rename (Q-026, 2026-10-22)
TEAM_RENAME_NOTE = TEAM_NOTES[5]               # a teams.txt that has this note has been made or migrated since: T24 = Redskins in it is the player's choice
TEAMS_BEFORE_RENAME = ".before-commanders"     # the copy of the player's teams.txt that the one-time migration keeps
_T24_REDSKINS = re.compile(r"^(\s*T0*24\s*=\s*)Redskins(\s*)$", re.IGNORECASE | re.MULTILINE)
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


def migrate_team_names(folder: str) -> str:
    """The one-time rename of T24 (Q-026, the owner 2026-10-22: "They are the Commanders"). Every teams.txt written by an older version names every
    team, so changing the built-in default alone would change nothing for a player who already has the file. A file that has the old notes and not
    the rename note is old: the note is added (so a later T24 = Redskins is the player's own choice and stays) and a T24 that still says Redskins
    becomes Commanders, with the player's file kept first as teams.txt.before-commanders. Returns "renamed", "noted" or "" (nothing to do, or the
    file could not be read or written: the file is then left as it is, and the built-in default shows through only where the file has no line).
    Never raises."""
    path = os.path.join(folder, "teams.txt")
    try:
        if not os.path.isfile(path):
            return ""
        try:
            text = read_player_text(path)
        except (ValueError, UnicodeError) as exc:              # a damaged file (binary, another encoding): the list loader heals it next
            debuglog.event("file", "teams_migration_skipped", logging.INFO, path=path, reason=str(exc))   # S8.3 round 2: no traceback for it
            return ""
        if TEAM_RENAME_NOTE in text or TEAM_OLD_LAST_NOTE not in text:
            return ""
        lines = text.replace("\r\n", "\n").split("\n")
        at = next(i for i, line in enumerate(lines) if line.strip() == "# " + TEAM_OLD_LAST_NOTE)
        lines.insert(at + 1, "# " + TEAM_RENAME_NOTE)
        edited = "\n".join(lines)
        renamed = _T24_REDSKINS.search(edited) is not None
        if renamed:
            edited = _T24_REDSKINS.sub(lambda m: m.group(1) + league_module.DEFAULT_TEAM_NAMES[23] + m.group(2), edited, count=1)
            if save_backup_copy(path, TEAMS_BEFORE_RENAME) is None:
                return ""                                     # never replace a file whose copy could not be made
        if not write_text_atomic(path, edited):
            return ""
        debuglog.event("file", "teams_renamed", path=path, t24="Commanders" if renamed else "unchanged")
        return "renamed" if renamed else "noted"
    except Exception:                                         # a file that cannot be used here is healed or kept by the list loader as always
        log.exception("teams.txt could not be migrated")
        return ""


# NX-B2 (D-144, the owner 2026-10-24: "it should be using the current 53 man rosters for each team"): the rosters.txt that the program copied into the
# customize folder is a whole copy of the built-in file, and a team's lines in it replace the built-in team (NX-N4), so a newer built-in roster would never
# be heard by a player who already has the file. A file that is EXACTLY an older shipped copy (the SHA-256 of its text with LF line ends) is the program's
# own, never the player's edit: it is replaced by the new built-in text once, the old one kept as rosters.txt + ROSTERS_BEFORE_REFRESH. A file the player changed
# in any way is his and stays (the README says how to get the new players: delete the file). Add the hash of the file a release ships here when the
# next roster refresh replaces it.
OLD_SHIPPED_ROSTERS = {
    "962870e5691d6f7fe622d275d037334b59418f260742a27b98006ac50099c17e",     # 0.10.0 to 0.13.0: season 2026, as of 2026-10-22 (SX.11)
    "e77caff85373148b9fe39fc9951b59d5ef6661ef49208d94ac937572fd273960",     # 0.14.0: as of 2026-10-24, format 1 (NX-B2; missed in 0.15.0, added in SR.2)
    "4ea4f247acd43e6698ea3cab300dcca8039d65e912a19b4b009020ab1732edc4",     # 0.15.0 to 0.16.1: as of 2026-10-24, format 1 with NX-D1's positions
    "10ce66ecfcf0de6766092d88e5bd5b042ab80c355f6cce625ecfc457f44d57a3",     # 0.16.2: as of 2026-10-25, layout 2 without ages (SR.7 adds them, D-167)
    "1ce8a093c45f139b2df35c190d92d1816aba61dea496dea022618651cb51c4ed",     # 0.16.3 to 0.16.6: as of 2026-10-25 with ages (D-177: the starters audit)
}
ROSTERS_BEFORE_REFRESH = ".before-layout-2"    # SR.2: the copy of the player's old file when the layout-2 rosters replace it (was .before-2026-10-24)


# SR.2: free_agents.txt in the same way (a player's copy lays every one of its IDs over the built-in list, so a man who has signed since would stay free)
OLD_SHIPPED_FREE_AGENTS = {
    "016328cf7ab998d2fe3f8763756871b03e02fcd196942d6e758c0da741ba892d",     # 0.14.0 to 0.16.1: as of 2026-10-24 (NX-B3)
    "48b1300b1a6c8b3b08134af599c73e3adc53d2a9025d9aa4b272d86225ca9304",     # 0.16.2 to 0.16.4: as of 2026-10-25, 170 men (D-169 adds the whole pool)
    "d44f6dd5f1c63fa74819cd551ceb5a1f8f68574dbbbb970b13875f75567f68fa",     # 0.16.5: 771 men (D-172 adds the men out a season who are still in the news)
    "94aae97409bbf27e44177d4b82714b5a4dc53b316a06d555f681383f9d42ec0a",     # 0.16.6: 836 men as of 2026-10-25 (D-177: the file of 2026-10-26)
    "d72a360eaf7a1ede935eb46703b8a5834debeb3c160a93557d0eae1cf52077d4",     # 0.16.7 (not released): 834 men as of 2026-10-26 (D-185: the audit's file)
}


def refresh_old_rosters(folder: str) -> str:
    """Replace a rosters.txt (and a free_agents.txt) that is exactly an older shipped copy with the built-in text (once, the old copy kept). Returns
    "refreshed" when rosters.txt was replaced, else "" (nothing to do: no file, the player's own file, the new one already, or it could not be read or
    written). Never raises."""
    _refresh_old_copy(folder, "free_agents.txt", OLD_SHIPPED_FREE_AGENTS, "freeagents")
    return _refresh_old_copy(folder, "rosters.txt", OLD_SHIPPED_ROSTERS, "rosters")


def _refresh_old_copy(folder: str, file_name: str, hashes: set, kind: str) -> str:
    import hashlib
    path = os.path.join(folder, file_name)
    try:
        if not os.path.isfile(path):
            return ""
        try:
            text = read_player_text(path)
        except (ValueError, UnicodeError):
            return ""                                             # a damaged file: the list loader heals it as always
        digest = hashlib.sha256(text.replace("\r\n", "\n").encode("utf-8")).hexdigest()
        if digest not in hashes:
            return ""
        from ..extras import real_names
        new = real_names.shipped_text(kind)
        if save_backup_copy(path, ROSTERS_BEFORE_REFRESH) is None:
            return ""                                             # never replace a file whose copy could not be made
        if not write_text_atomic(path, new):
            return ""
        debuglog.event("file", "%s_refreshed" % ("rosters" if kind == "rosters" else "free_agents"), path=path, old=digest[:12],
                       copy=path + ROSTERS_BEFORE_REFRESH)        # rule 0.15
        return "refreshed"
    except Exception:
        log.exception("%s could not be refreshed", file_name)
        return ""


def name_problem(name: str) -> str | None:
    """None when the name passes the game's limits (CUSTOMIZABLE_CONTENT 10), else the plain reason."""
    if not NAME_MIN <= len(name) <= NAME_MAX:
        return "a name has %d to %d characters" % (NAME_MIN, NAME_MAX)
    if "," in name or ";" in name:
        return "a name cannot have a comma or a semicolon"
    if any(ord(c) < 32 or ord(c) == 127 for c in name):
        return "a name cannot have a control character"
    if not any(unicodedata.category(c)[0] in "LNPS" for c in name):
        return "a name needs at least one letter, digit or sign that can be seen and spoken"
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
    kept: set[str] = field(default_factory=set)                     # lists whose file could not be read: the earlier values stay
    remarks: object = None              # extras.remarks.RemarkPools with the N. F. L. rules; None while they are not used
    fouls: object = None                # extras.penalty_list.FoulTable with the N. F. L. rules; None while not used (SX.3)
    playbooks: object = None            # extras.playbooks.Table with the N. F. L. rules; None while not used (SX.7)
    news: object = None                 # extras.franchise.news_pools.NewsPools with the N. F. L. rules; None while not used (SX.8e)
    injuries: object = None             # extras.franchise.injury_pools.InjuryPools with the N. F. L. rules; None while not used (SX.8k)
    favourites: object = None           # (offense IDs, defense IDs) of favourites.txt with the N. F. L. rules; None while not used (SX.10c)
    real_names: object = None           # extras.real_names.RealNames (coaches.txt, rosters.txt, respellings.txt) with the N. F. L. rules; None while not used (SX.11)

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
                 sound_probe: Callable[[str], str | None] | None = None, extras: bool = False):
        self.folder = folder
        self.sounds_dir = os.path.join(folder, SOUNDS_FOLDER)
        self._default_surnames = default_surnames or load_surnames
        self._surname_defaults: list[str] | None = None
        self.sound_probe = sound_probe or probe_sound_file
        self.extras = bool(extras)        # nfl4 only: the N. F. L. rules are in use, so remarks.txt is read too (SX.2)
        self._parked_remarks = None       # the remarks loaded before the extras were switched off
        self._parked_fouls = None         # and the foul table (SX.3)
        self._parked_playbooks = None     # and the playbooks (SX.7)
        self._parked_news = None          # and the Franchise's news lines (SX.8e)
        self._parked_injuries = None      # and its injury words (SX.8k)
        self._parked_favourites = None    # and the favourite plays (SX.10c)
        self._parked_real = None          # and the real names (SX.11)
        self.files: dict[str, cl.ListFile] = {
            spec.key: cl.ListFile(os.path.join(folder, spec.folder) if spec.folder else folder, spec.file_name, GAME, spec.key,
                                  lambda key=spec.key: self.default_text(key))
            for spec in SPECS + EXTRA_SPECS}
        self._notices: list[str] = []
        self._unwritable_told: set[str] = set()
        migrate_team_names(folder)                    # Q-026: a teams.txt of an older version says Redskins for T24; once, before it is read
        refresh_old_rosters(folder)                   # NX-B2: a rosters.txt that is an older shipped copy gets the 53-man rosters; once, before it is read
        self.snapshot = self._load()
        self._notices.extend(self.snapshot.notices)

    @property
    def specs(self) -> tuple[ListSpec, ...]:
        """The lists in use: the four of the classic game, and the extras' files only with the N. F. L. rules."""
        return SPECS + EXTRA_SPECS if self.extras else SPECS

    def use_extras(self, on: bool) -> None:
        """The Rules setting changed (nfl4 only, SX.2). On: remarks.txt is read (made or healed as every list) and its
        sentences join the next notices; off: it is not read any more and the game uses no remark of the file."""
        on = bool(on)
        if on == self.extras:
            return
        self.extras = on
        if not on:
            self._parked_remarks = self.snapshot.remarks      # what was loaded: used again if the file cannot be read then
            self._parked_fouls = self.snapshot.fouls
            self._parked_playbooks = self.snapshot.playbooks
            self._parked_news = self.snapshot.news
            self._parked_injuries = self.snapshot.injuries
            self._parked_favourites = self.snapshot.favourites
            self._parked_real = self.snapshot.real_names
            self.snapshot.real_names = None
            self.snapshot.remarks = None
            self.snapshot.fouls = None
            self.snapshot.playbooks = None
            self.snapshot.news = None
            self.snapshot.injuries = None
            self.snapshot.favourites = None
            for spec in EXTRA_SPECS:
                self.snapshot.statuses.pop(spec.key, None)
                self.snapshot.problems.pop(spec.key, None)
                self.snapshot.kept.discard(spec.key)
            return
        from ..extras.penalty_list import DEFAULT_TABLE
        from ..extras.remarks import DEFAULT_POOLS
        from ..extras.playbooks import DEFAULT_TABLE as DEFAULT_PLAYBOOKS
        from ..extras.franchise.news_pools import DEFAULT_POOLS as DEFAULT_NEWS
        from ..extras.franchise.injury_pools import DEFAULT_POOLS as DEFAULT_INJURIES
        previous = dataclasses.replace(self.snapshot, remarks=self._parked_remarks, fouls=self._parked_fouls,
                                       playbooks=self._parked_playbooks, news=self._parked_news, injuries=self._parked_injuries,
                                       favourites=self._parked_favourites, real_names=self._parked_real)
        from ..extras import real_names
        self.snapshot.real_names = real_names.defaults()
        self.snapshot.remarks = DEFAULT_POOLS
        self.snapshot.fouls = DEFAULT_TABLE
        self.snapshot.playbooks = DEFAULT_PLAYBOOKS
        self.snapshot.news = DEFAULT_NEWS
        self.snapshot.injuries = DEFAULT_INJURIES
        self.snapshot.favourites = ((), ())
        for spec in EXTRA_SPECS:
            self.snapshot.kept.discard(spec.key)
        before = len(self.snapshot.notices)
        self._load_into(self.snapshot, EXTRA_SPECS, previous)
        self._notices_of(self.snapshot, EXTRA_SPECS)
        self._notices.extend(self.snapshot.notices[before:])

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
        if key == REMARKS:
            from ..extras import remarks
            return cl.render_list(GAME, REMARKS, remarks.NOTES, remarks.default_entries())
        if key == PENALTIES:
            from ..extras import penalty_list
            return cl.render_list(GAME, PENALTIES, penalty_list.NOTES, penalty_list.default_entries())
        if key in (PLAYS, STYLES, TEAMSTYLES):
            from ..extras import playbook_list as pl
            notes, entries = {PLAYS: (pl.PLAYS_NOTES, pl.default_plays), STYLES: (pl.STYLES_NOTES, pl.default_styles),
                              TEAMSTYLES: (pl.TEAMS_NOTES, pl.default_teams)}[key]
            return cl.render_list(GAME, key, notes, entries())
        if key == NEWS:
            from ..extras.franchise import news_pools
            return cl.render_list(GAME, NEWS, news_pools.NOTES, news_pools.default_entries())
        if key == INJURIES:
            from ..extras.franchise import injury_pools
            return cl.render_list(GAME, INJURIES, injury_pools.NOTES, injury_pools.default_entries())
        if key == FAVOURITES:
            from ..extras.plays import favourites
            return favourites.text_of()
        if key in (COACHES, ROSTERS, RESPELLINGS, FREE_AGENTS, NFL_SURNAMES):
            from ..extras import real_names
            return real_names.shipped_text(key)         # raises when the asset cannot be read: the file is then not made, the built-in names are used
        raise KeyError(key)

    # ----- loading -----

    def _load(self, previous: Snapshot | None = None) -> Snapshot:
        """Read every list in use; never raises. `previous` is the snapshot in use: a list whose file cannot be read now (held
        by another program, damaged and not replaceable, unreadable) keeps the values it had (playbook 7.10: keep the loaded
        copy), and only the very first load falls back to the originals."""
        snapshot = Snapshot(league_module.DEFAULT_TEAM_NAMES, league_module.DEFAULT_DIVISION_NAMES,
                            None, BanterPool(DEFAULT_LINES))
        if self.extras:
            from ..extras.penalty_list import DEFAULT_TABLE
            from ..extras.playbooks import DEFAULT_TABLE as DEFAULT_PLAYBOOKS
            from ..extras.remarks import DEFAULT_POOLS
            from ..extras.franchise.news_pools import DEFAULT_POOLS as DEFAULT_NEWS
            from ..extras.franchise.injury_pools import DEFAULT_POOLS as DEFAULT_INJURIES
            snapshot.remarks = DEFAULT_POOLS
            snapshot.fouls = DEFAULT_TABLE
            snapshot.playbooks = DEFAULT_PLAYBOOKS
            snapshot.news = DEFAULT_NEWS
            snapshot.injuries = DEFAULT_INJURIES
            snapshot.favourites = ((), ())
            from ..extras import real_names
            snapshot.real_names = real_names.defaults()
        self._load_into(snapshot, self.specs, previous)
        self._notices_of(snapshot, self.specs)
        return snapshot

    def _load_into(self, snapshot: Snapshot, specs, previous: Snapshot | None) -> None:
        try:
            os.makedirs(self.sounds_dir, exist_ok=True)
        except OSError:
            log.warning("could not make the folder %s", self.sounds_dir, exc_info=True)
        loads = {spec.key: self.files[spec.key].load() for spec in specs}
        for spec in specs:
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
            if load.status in HOLD_STATUSES and previous is not None:
                self._keep_previous(spec.key, snapshot, previous)

    @staticmethod
    def _keep_previous(key: str, snapshot: Snapshot, previous: Snapshot) -> None:
        if key == TEAMS:
            snapshot.team_names = previous.team_names
        elif key == DIVISIONS:
            snapshot.division_names = previous.division_names
        elif key == SURNAMES:
            snapshot.surnames = previous.surnames
        elif key == BANTER:
            snapshot.banter, snapshot.sound_files = previous.banter, previous.sound_files
        elif key == REMARKS:
            if previous.remarks is None:            # the extras were just switched on: nothing loaded before, originals
                return
            snapshot.remarks = previous.remarks
        elif key == PENALTIES:
            if previous.fouls is None:
                return
            snapshot.fouls = previous.fouls
        elif key == NEWS:
            if previous.news is None:
                return
            snapshot.news = previous.news
        elif key == INJURIES:
            if previous.injuries is None:
                return
            snapshot.injuries = previous.injuries
        elif key == FAVOURITES:
            if previous.favourites is None:
                return
            snapshot.favourites = previous.favourites
        elif key in (COACHES, ROSTERS, RESPELLINGS, FREE_AGENTS, NFL_SURNAMES):
            if previous.real_names is None or snapshot.real_names is None:
                return
            # the three files make one set of names: the part the held file makes is the earlier one's, the others stay as read
            part = {COACHES: ("version", "coaches"), ROSTERS: ("rosters", "reserves", "roles", "roster_version"), RESPELLINGS: ("respellings",),
                    FREE_AGENTS: ("free_agents",), NFL_SURNAMES: ("surnames",)}[key]     # SR.4: a roster's reserve lists and return roles go with it
            snapshot.real_names = dataclasses.replace(snapshot.real_names, **{name: getattr(previous.real_names, name) for name in part})
        elif key in (PLAYS, STYLES, TEAMSTYLES):
            if previous.playbooks is None:
                return
            # the three files make one table: the part the held file makes is the earlier one's, the others stay as read
            snapshot.playbooks = dataclasses.replace(snapshot.playbooks, **{
                PLAYS: dict(names=previous.playbooks.names, disabled=previous.playbooks.disabled),
                STYLES: dict(styles=previous.playbooks.styles),
                TEAMSTYLES: dict(teams=previous.playbooks.teams)}[key])
        snapshot.kept.add(key)

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
        elif key == REMARKS:
            from ..extras import remarks
            snapshot.remarks = remarks.build_pools(remarks.overrides_of(entries, problems), problems)
        elif key == PENALTIES:
            from ..extras import penalty_list
            snapshot.fouls = penalty_list.table_of(entries, problems)
        elif key in (PLAYS, STYLES, TEAMSTYLES):
            from ..extras import playbook_list as pl
            apply = {PLAYS: pl.apply_plays, STYLES: pl.apply_styles, TEAMSTYLES: pl.apply_teams}[key]
            snapshot.playbooks = apply(snapshot.playbooks, entries, problems)
        elif key == NEWS:
            from ..extras.franchise import news_pools
            snapshot.news = news_pools.build_pools(news_pools.overrides_of(entries, problems), problems)
        elif key == INJURIES:
            from ..extras.franchise import injury_pools
            snapshot.injuries = injury_pools.build_pools(injury_pools.overrides_of(entries, problems), problems)
        elif key == FAVOURITES:
            from ..extras.plays import favourites
            snapshot.favourites = favourites.parse(entries, problems)
        elif key in (COACHES, ROSTERS, RESPELLINGS, FREE_AGENTS, NFL_SURNAMES):
            from ..extras import real_names
            if snapshot.real_names is not None:
                snapshot.real_names = real_names.apply_kind(snapshot.real_names, key, entries, problems)

    def _notices_of(self, snapshot: Snapshot, specs) -> None:
        unwritable = [spec for spec in specs if snapshot.statuses[spec.key] == cl.UNWRITABLE]
        told = {spec.key for spec in unwritable}                       # tend() does not say it again
        self._unwritable_told = (self._unwritable_told - {spec.key for spec in specs}) | told
        for spec in specs:
            status = snapshot.statuses[spec.key]
            if status == cl.RESET:
                snapshot.notices.append(DAMAGED_RESET % (spec.file_name, spec.original_nouns))
            elif status in HOLD_STATUSES:
                tail = ("The %s you already had stay in use." % spec.nouns if spec.key in snapshot.kept
                        else "%s are used this time." % capital(spec.original_nouns))
                snapshot.notices.append(" The file %s %s. %s " % (spec.file_name, HOLD_REASONS[status], tail))
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
        self.snapshot = self._load(self.snapshot)
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
        for spec in self.specs:
            file = self.files[spec.key]
            if file.exists():
                continue
            try:
                os.makedirs(os.path.dirname(file.path), exist_ok=True)
            except OSError as exc:
                log.warning("the folder of %s could not be made (%s)", file.path, exc)
            if file.write_defaults():
                self._unwritable_told.discard(spec.key)
            elif spec.key not in self._unwritable_told:       # said once per file, and not again for one the start said
                self._unwritable_told.add(spec.key)
                self._notices.append(UNWRITABLE_ONE % (spec.file_name, spec.original_nouns))

    def check(self) -> str:
        """The Customize menu's check: every file is read as a reload does (a damaged one is healed, the sentences say so)
        but nothing is applied. Returns what is read aloud."""
        snapshot = self._load()
        parts = [notice.strip() for notice in snapshot.notices if "found in" not in notice]
        for spec in self.specs:
            count = snapshot.problem_count(spec.key)
            status = snapshot.statuses[spec.key]
            if status in HOLD_STATUSES or status == cl.UNWRITABLE:       # nothing was read: do not say "no problems"
                parts.append("%s: it could not be read or made, so it was not checked." % spec.file_name)
            else:
                parts.append("%s: %s." % (spec.file_name, "no problems" if not count else cl.plural(count, "problem")))
        names = snapshot.sound_files
        if names:
            bad = [name for name in names if self.sound_probe(os.path.join(self.sounds_dir, name))]
            parts.append("The banter names %s, %s." % (cl.plural(len(names), "sound file"),
                                                       "all can be used" if not bad else "%d cannot be used" % len(bad)))
        for what, found in (("remarks", remark_sound_files(snapshot.remarks)), ("news lines", remark_sound_files(snapshot.news)),
                             ("injury words", remark_sound_files(snapshot.injuries))):
            if found:
                bad = [name for name in found if self.sound_probe(os.path.join(self.sounds_dir, name))]
                parts.append("The %s name %s, %s." % (what, cl.plural(len(found), "sound file"),
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
        for spec in self.specs:
            if key is not None and spec.key != key:
                continue
            file = self.files[spec.key]
            try:
                ok, kept = file.reset()
            except Exception:
                log.exception("could not reset %s", file.path)
                ok, kept = False, False
            if not ok:
                result.failed.append(spec.file_name)
                continue
            result.done.append(spec.file_name)
            if kept:
                result.kept.append(spec.file_name)
        return result


def capital(text: str) -> str:
    return text[:1].upper() + text[1:]


def remark_sound_files(pools) -> list[str]:
    """The sound files the player's remark lines name (nfl4 extras, SX.2); none while the extras are not in use."""
    if pools is None:
        return []
    return sorted({piece.file for pool in pools.pools.values() for line in pool if not line.builtin
                   for piece in line.pieces if isinstance(piece, Sound)})


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
