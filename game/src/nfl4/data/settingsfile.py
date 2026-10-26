"""The player's settings.txt: saved speech, sound and game settings, self-healing. This is inspired by Jim Kitchen.

What the original kept in footbal0.dat and football.vol (data/settings.py) lives here, in the per-user data folder
(GAP_REGISTER G-F8), in plain lines (the kit's format, Brain DECISIONS P7 S7.2), so one missing comma never breaks
anything (playbook 7.9, 7.10):

    volume_announcer = 80
    speech_rate = original

Lines starting with # are notes. A bad line is skipped and reported, its setting stays original. A file that is empty,
binary, too large, of an unknown format version or all junk is copied aside as settings.txt.damaged1 and recreated
with the original values. A file held by another program is left alone (the original values are used this run and
nothing is saved over it). A folder or file that cannot be written is told once and the program carries on from memory.
"""
from __future__ import annotations

import logging
import os
import re
from typing import Callable

from ..speech.roles import ALL_ROLES
from . import debuglog, paths
from .healing import read_player_text, save_damaged_copy, write_text_atomic
from .settings import AudioSettings, GameSettings, Settings, SpeechSettings

log = logging.getLogger("nfl4.data")

FORMAT_VERSION = 1
FILE_NAME = "settings.txt"
MODES = ("sapi", "nvda", "jaws", "auto")
_MODE_WORDS = {"sapi": "sapi", "sapi5": "sapi", "sapi 5": "sapi", "nvda": "nvda", "jaws": "jaws", "auto": "auto",
               "automatic": "auto"}
_ON_WORDS = {"on": True, "yes": True, "true": True, "1": True, "off": False, "no": False, "false": False, "0": False}
_RULES_WORDS = {"classic": "classic", "nfl": "nfl", "n f l": "nfl", "n f l rules": "nfl", "nfl rules": "nfl"}
_VERSION = re.compile(r"^#\s*NFL Football 4 settings,\s*format\s+(\d+)", re.IGNORECASE)
_NAME = re.compile(r"^[a-z_]+$")
GAME_NAME = "NFL Football 4"

HEADER = f"""# {GAME_NAME} settings, format {FORMAT_VERSION}. Lines starting with # are notes and are ignored.
#
# The game saves this file itself whenever you change a setting in its menus (F8 comments, F9 speech settings,
# F11 volumes, F12 voices, the Ctrl key for the speech rate). You can also edit it in Notepad while the game is
# closed: one setting per line, name = value. A line that cannot be understood is skipped and that setting stays
# original. If this file is damaged, the game saves a copy next to it (settings.txt.damaged1) and makes a new one.
#
# speech_output       auto = NVDA or JAWS when one of them runs, else the five SAPI 5 voices (default), sapi = the five SAPI 5
#                     voices of the game always, nvda = NVDA only, jaws = JAWS only. When a screen reader runs the game asks
#                     once whether it should speak through it
# speech_output_chosen  yes when you said how the game speaks (the question at the start, or F9, Speech settings); a file
#                     without it that says sapi is read as auto, once
# voice_announcer, voice_own_quarterback, voice_opponent_quarterback, voice_own_punter, voice_opponent_punter
#                     the voice of each speaker, as the voice's identifier. Empty means the first voice in Windows'
#                     list (original). Choose the voices with F12 rather than typing them here.
# volume_announcer, volume_own_quarterback, volume_own_punter, volume_opponent_quarterback, volume_opponent_punter
#                     0 to 100 for each speaker (original 95); F11 changes them
# voice_color, volume_color   Ghip, the color commentator of the radio broadcast (the N. F. L. rules): his voice and volume, F12 and F11
#                     ask for him when the Broadcast item of F9, Rules is on
# speech_rate         -10 to 10, or original for the voice's own rate (original); the Ctrl key changes it
# speech_pitch        -10 to 10 (original 0). Not every voice supports it.
# list_letters        type = typing letters searches a list for a name (default), first = a letter jumps to the
#                     next name that starts with it (press it again for the one after)
# sound_volume        0 to -50: how many decibels below full volume the sounds play (original 0); F11 changes it
# comments            on or off: the announcer's comments (original on); F8 switches them
# commercials         off = none (default), every = one of your own commercial files at every break of the game, second =
#                     at every second break, third = at every third break; the Sounds menu changes it (the files are
#                     yours: see the commercials folder next to this file)
# rules               classic = the game exactly as the original, nfl = the N. F. L. rules with a real clock and the added
#                     features (default nfl); the Rules item of the F9 menu changes it, from the next game on
# nx_timeouts         on or off: the time outs of the N. F. L. rules (default on)
# nx_challenges       on or off: the replay challenges and the replay official's reviews of the N. F. L. rules (default on)
# nx_penalties        on or off: the penalties of the N. F. L. rules, with accept or decline (default on)
# nx_qb_runs          on or off: the quarterback sneak, keeper, draw and scramble of the N. F. L. rules (default on)
# nx_onside           on or off: the onside kicks of the N. F. L. rules (default on)
# nx_offense_playbook team = the style of your team with every play of the game (default), classic = the original's plays and
#                     kicks, or pro, west, air, power, zone, option, pressure: the plays your offense calls with the N. F. L. rules
# nx_defense_playbook the same for your defense
# nx_playbook_chosen  yes when you chose a playbook yourself; a file without it that says classic is read as team, once
# nx_stadium          on or off: the stadium sounds of the N. F. L. rules, the crowd, the hits, the first down chain (default on)
# nx_broadcast        on or off: Ghip, the color commentator of the radio broadcast of the N. F. L. rules, and the announcer's
#                     questions to him (default on; F8 switches all comments off, this switches only Ghip)
# nx_menu_hints       0 to 99: in how many program runs the play menus said where Right and M are; at 3 the hints stop (set it to 3 to
#                     stop them, to 0 to hear them again)
# nx_commentator      the name of the color commentator of the radio broadcast (default Ghip): the Rules item of the F9 menu lists
#                     well known sports podcasters and lets you type a name of your own; it is used from the next game
# nx_qb_starters      the quarterbacks you chose to start for a team (F9, Rules, Quarterbacks), like T05=Tyler Huntley; T12=Kenny Pickett.
#                     Empty (default): every team's first quarterback of rosters.txt starts. Used with the N. F. L. rules' real names
# nx_depth            the depth charts you set for a team (F9, Rules, Depth charts), like T05 RB=Ray Davis; T05 WR=Khalil Shakir,DJ Moore:
#                     the named players play first, in that order. Empty (default): the real order of rosters.txt
# nx_key_players      your players for the key downs and moments (F9, Rules, Depth charts, key downs and moments), like
#                     T05 redzone receiver=Dalton Kincaid; T05 down back=James Cook III (down: third and fourth down, redzone: inside the
#                     20, twominute: the last two minutes of a half). Empty (default): the starters
# nx_onside_question  always = you are asked about an onside kick at every kick off and safety kick (default, the 2026 rule),
#                     sensible = only when it makes sense (the late game of a team that trails or leads by one score)
# nx_onside_question_chosen  yes when you chose the line above yourself; a file without it is read as always, once
# nx_season_kind      classic = a classic season (default), franchise = your franchise, a league that lasts from season to
#                     season (F9, Franchise; used only with the N. F. L. rules)
# nx_franchise_slot   1, 2 or 3: which of your three franchises is in use (default 1); the start-up menu chooses it
# nx_fr_auto          on or off: the staff handles your to do list and the roster cut of the franchise (default off)
# nx_fr_offseason     full = every stage of the offseason is told (default), short = a sentence for each stage
# nx_fr_picks_told    first = the first picks and yours (default), mine = only yours, all = every pick of the draft
# debug_log           detailed = the log of what the game does, for fixing a bug on your computer (default), trace = even more
#                     (only when asked), normal = only problems and the main events, off = no log at all. The log files are in
#                     the logs folder next to this file and never leave your computer unless you send them. Without a log a
#                     bug that happens only on your computer cannot be fixed. F9, Speech settings, "Save a problem report"
#                     makes one file to send.
#
"""


class SettingsFormatError(ValueError):
    """The file as a whole is unusable (empty, unknown version, nothing understood)."""


def render(settings: Settings, voice_name: Callable[[str], str] = lambda role: "") -> str:
    sp, au, game = settings.speech, settings.audio, settings.game
    lines = [HEADER.rstrip("\n"), f"speech_output = {sp.mode}", f"speech_output_chosen = {'yes' if sp.mode_chosen else 'no'}"]
    for role in ALL_ROLES:
        voice_id = sp.voices.get(role)
        name = ""
        if voice_id:
            try:
                name = voice_name(role) or ""
            except Exception:
                name = ""
        if name:
            lines.append(f"# The voice below is: {name.replace(chr(10), ' ').replace(chr(13), ' ')}")
        lines.append(f"voice_{role} = {voice_id or ''}")
    for role in ALL_ROLES:
        lines.append(f"volume_{role} = {sp.volumes.get(role, 95)}")
    lines += [
        f"speech_rate = {'original' if sp.rate is None else sp.rate}",
        f"speech_pitch = {sp.pitch}",
        f"list_letters = {sp.list_letters}",
        f"sound_volume = {au.sound_level // 100}",
        f"commercials = {au.commercials}",
        f"comments = {'on' if game.comments else 'off'}",
        f"rules = {game.rules}",
        f"nx_timeouts = {'on' if game.nx_timeouts else 'off'}",
        f"nx_challenges = {'on' if game.nx_challenges else 'off'}",
        f"nx_penalties = {'on' if game.nx_penalties else 'off'}",
        f"nx_qb_runs = {'on' if game.nx_qb_runs else 'off'}",
        f"nx_onside = {'on' if game.nx_onside else 'off'}",
        f"nx_onside_question = {game.nx_onside_question}",
        f"nx_onside_question_chosen = {'yes' if game.nx_onside_question_chosen else 'no'}",
        f"nx_offense_playbook = {game.nx_offense_playbook}",
        f"nx_defense_playbook = {game.nx_defense_playbook}",
        f"nx_playbook_chosen = {'yes' if game.nx_playbook_chosen else 'no'}",
        f"nx_stadium = {'on' if game.nx_stadium else 'off'}",
        f"nx_broadcast = {'on' if game.nx_broadcast else 'off'}",
        f"nx_commentator = {game.nx_commentator}",
        f"nx_qb_starters = {game.nx_qb_starters}",
        f"nx_depth = {game.nx_depth}",
        f"nx_key_players = {game.nx_key_players}",
        f"nx_menu_hints = {game.nx_menu_hints}",
        f"nx_season_kind = {game.nx_season_kind}",
        f"nx_franchise_slot = {game.nx_franchise_slot}",
        f"nx_fr_auto = {'on' if game.nx_fr_auto else 'off'}",
        f"nx_fr_offseason = {game.nx_fr_offseason}",
        f"nx_fr_picks_told = {game.nx_fr_picks_told}",
        f"debug_log = {game.debug_log}",
    ]
    return "\n".join(lines) + "\n"


def _number(value: str, low: int, high: int) -> int:
    text = value.strip().rstrip("%").strip()
    if not re.fullmatch(r"[+-]?\d{1,6}", text):
        raise ValueError(f"'{value[:20]}' is not a whole number")
    number = int(text)
    if not low <= number <= high:
        raise ValueError(f"{number} is outside {low} to {high}")
    return number


def parse(text: str) -> tuple[Settings, list[str]]:
    """Parse the file's text into settings and a list of plain problems. Raises SettingsFormatError when unusable."""
    settings = Settings.defaults()
    problems: list[str] = []
    nonblank = 0
    understood = 0
    header_seen = False
    seen: set[str] = set()
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip().lstrip("﻿")
        if not line:
            continue
        nonblank += 1
        version = _VERSION.match(line)
        if version:
            if int(version.group(1)) != FORMAT_VERSION:
                raise SettingsFormatError(f"unknown format version {version.group(1)}")
            header_seen = True
            continue
        if line.startswith("#"):
            continue
        name, sep, value = line.partition("=")
        name = name.strip().lower()
        value = value.strip()
        if not sep or not _NAME.match(name):
            problems.append(f"line {number}: '{line[:40]}' is not 'name = value'")
            continue
        try:
            _apply(name, value, settings.speech, settings.audio, settings.game)
        except KeyError:
            problems.append(f"line {number}: '{name[:30]}' is not a known setting")
            continue
        except ValueError as exc:
            problems.append(f"line {number}: {name}: {exc}")
            continue
        understood += 1
        if name in seen:
            problems.append(f"line {number}: {name} appears twice, the last one is used")
        seen.add(name)
    if nonblank == 0:
        raise SettingsFormatError("the file is empty")
    if not header_seen and understood == 0 and problems:
        raise SettingsFormatError("no header and nothing understood")
    if not settings.speech.mode_chosen and settings.speech.mode == "sapi":
        settings.speech.mode = "auto"            # a player's e-mail, 2026-10-22 (D-109): the old default sapi, never chosen, becomes automatic, once
    game = settings.game
    if not game.nx_onside_question_chosen and game.nx_onside_question != "always":
        game.nx_onside_question = "always"       # SX.2b, D-085: a "sensible" the player never chose (the old default) becomes the 2026 rule, once
    if not game.nx_playbook_chosen:              # SX.10e, D-095: a Classic the player never chose (the old default) becomes the team's, once
        for name in ("nx_offense_playbook", "nx_defense_playbook"):
            if getattr(game, name) == "classic":
                setattr(game, name, "team")
    return settings, problems


def _apply(name: str, value: str, sp: SpeechSettings, au: AudioSettings, game: GameSettings) -> None:
    """Set one value; KeyError for an unknown name, ValueError for a bad value (the setting keeps its old value)."""
    if name.startswith("voice_") and name[6:] in ALL_ROLES:
        if len(value) > 400 or any(ord(c) < 32 for c in value):
            raise ValueError("not a voice identifier")
        sp.voices[name[6:]] = value or None
    elif name.startswith("volume_") and name[7:] in ALL_ROLES:
        sp.volumes[name[7:]] = _number(value, 0, 100)
    elif name == "speech_rate":
        sp.rate = None if value.lower() in ("original", "") else _number(value, -10, 10)
    elif name == "speech_pitch":
        sp.pitch = _number(value, -10, 10)
    elif name == "speech_output":
        mode = _MODE_WORDS.get(value.lower())
        if mode is None:
            raise ValueError(f"'{value[:20]}' is not sapi, nvda, jaws or auto")
        sp.mode = mode
    elif name == "speech_output_chosen":
        word = _ON_WORDS.get(value.lower())
        if word is None:
            raise ValueError(f"'{value[:20]}' is not yes or no")
        sp.mode_chosen = word
    elif name == "list_letters":
        if value.lower() not in ("type", "first"):
            raise ValueError(f"'{value[:20]}' is not type or first")
        sp.list_letters = value.lower()
    elif name == "sound_volume":
        au.sound_level = _number(value, -50, 0) * 100
    elif name == "commercials":
        if value.lower() not in ("off", "every", "second", "third"):
            raise ValueError(f"'{value[:20]}' is not off, every, second or third")
        au.commercials = value.lower()
    elif name == "comments":
        word = _ON_WORDS.get(value.lower())
        if word is None:
            raise ValueError(f"'{value[:20]}' is not on or off")
        game.comments = word
    elif name == "rules":
        rules = _RULES_WORDS.get(" ".join(value.lower().replace(".", " ").split()))
        if rules is None:
            raise ValueError(f"'{value[:20]}' is not classic or nfl")
        game.rules = rules
    elif name == "nx_timeouts":
        word = _ON_WORDS.get(value.lower())
        if word is None:
            raise ValueError(f"'{value[:20]}' is not on or off")
        game.nx_timeouts = word
    elif name == "nx_challenges":
        word = _ON_WORDS.get(value.lower())
        if word is None:
            raise ValueError(f"'{value[:20]}' is not on or off")
        game.nx_challenges = word
    elif name == "nx_penalties":
        word = _ON_WORDS.get(value.lower())
        if word is None:
            raise ValueError(f"'{value[:20]}' is not on or off")
        game.nx_penalties = word
    elif name == "nx_qb_runs":
        word = _ON_WORDS.get(value.lower())
        if word is None:
            raise ValueError(f"'{value[:20]}' is not on or off")
        game.nx_qb_runs = word
    elif name == "nx_stadium":
        word = _ON_WORDS.get(value.lower())
        if word is None:
            raise ValueError(f"'{value[:20]}' is not on or off")
        game.nx_stadium = word
    elif name == "nx_broadcast":
        word = _ON_WORDS.get(value.lower())
        if word is None:
            raise ValueError(f"'{value[:20]}' is not on or off")
        game.nx_broadcast = word
    elif name == "nx_menu_hints":
        game.nx_menu_hints = _number(value, 0, 99)
    elif name == "nx_commentator":
        from ..extras.commentators import clean
        if not clean(value):
            raise ValueError("not a name (at least two letters or digits)")
        game.nx_commentator = clean(value)
    elif name == "nx_qb_starters":
        from ..extras.quarterbacks import clean as clean_starters
        if value.strip() and not clean_starters(value):
            raise ValueError("not a list like T05=Tyler Huntley; T12=Kenny Pickett")
        game.nx_qb_starters = clean_starters(value)
    elif name == "nx_depth":
        from ..extras.depth_chart import clean_depth
        if value.strip() and not clean_depth(value):
            raise ValueError("not a list like T05 RB=Ray Davis; T05 WR=Khalil Shakir,DJ Moore")
        game.nx_depth = clean_depth(value)
    elif name == "nx_key_players":
        from ..extras.depth_chart import clean_keys
        if value.strip() and not clean_keys(value):
            raise ValueError("not a list like T05 redzone receiver=Dalton Kincaid")
        game.nx_key_players = clean_keys(value)
    elif name == "nx_onside":
        word = _ON_WORDS.get(value.lower())
        if word is None:
            raise ValueError(f"'{value[:20]}' is not on or off")
        game.nx_onside = word
    elif name == "nx_onside_question":
        if value.lower() not in ("sensible", "always"):
            raise ValueError(f"'{value[:20]}' is not sensible or always")
        game.nx_onside_question = value.lower()
    elif name == "nx_onside_question_chosen":
        word = _ON_WORDS.get(value.lower())
        if word is None:
            raise ValueError(f"'{value[:20]}' is not yes or no")
        game.nx_onside_question_chosen = word
    elif name == "nx_playbook_chosen":
        word = _ON_WORDS.get(value.lower())
        if word is None:
            raise ValueError(f"'{value[:20]}' is not yes or no")
        game.nx_playbook_chosen = word
    elif name in ("nx_offense_playbook", "nx_defense_playbook"):
        from ..extras.playbook_data import PLAYBOOK_CHOICES
        choice = value.lower().strip()
        if choice not in PLAYBOOK_CHOICES:
            raise ValueError(f"'{value[:20]}' is not one of {', '.join(PLAYBOOK_CHOICES)}")
        setattr(game, name, choice)
    elif name == "nx_season_kind":
        if value.lower() not in ("classic", "franchise"):
            raise ValueError(f"'{value[:20]}' is not classic or franchise")
        game.nx_season_kind = value.lower()
    elif name == "nx_franchise_slot":
        if value.strip() not in ("1", "2", "3"):
            raise ValueError(f"'{value[:20]}' is not 1, 2 or 3")
        game.nx_franchise_slot = int(value.strip())
    elif name == "nx_fr_auto":
        word = _ON_WORDS.get(value.lower())
        if word is None:
            raise ValueError(f"'{value[:20]}' is not on or off")
        game.nx_fr_auto = word
    elif name == "nx_fr_offseason":
        if value.lower() not in ("full", "short"):
            raise ValueError(f"'{value[:20]}' is not full or short")
        game.nx_fr_offseason = value.lower()
    elif name == "nx_fr_picks_told":
        if value.lower() not in ("first", "mine", "all"):
            raise ValueError(f"'{value[:20]}' is not first, mine or all")
        game.nx_fr_picks_told = value.lower()
    elif name == "debug_log":
        if value.lower() not in debuglog.LEVEL_NAMES:
            raise ValueError(f"'{value[:20]}' is not detailed, trace, normal or off")
        game.debug_log = value.lower()
    else:
        raise KeyError(name)


UNWRITABLE_NOTICE = (f"{GAME_NAME} could not save its settings file, so changes last only until the game closes. "
                     f"The file belongs in the {GAME_NAME} folder inside Kitchensinc Revival in your AppData Roaming folder.")
IN_USE_NOTICE = f"settings.txt is in use by another program, so {GAME_NAME} uses the original settings this time."
VOICE_MISSING_NOTICE = "A voice saved in the settings was not found, so the first voice is used for it."


class SettingsStore:
    """Loads, heals and saves settings.txt. Never raises. Notices are short sentences to speak once."""

    def __init__(self, folder: str | None = None, voice_name: Callable[[str], str] = lambda role: ""):
        self.folder = folder or paths.user_data_dir()
        self.path = os.path.join(self.folder, FILE_NAME)
        self.settings = Settings.defaults()
        self.voice_name = voice_name     # role -> the description of its voice, for the note above a saved voice
        self._notices: list[str] = []
        self._problems: list[str] = []
        self._save_blocked = False       # the file could not be read: never write over what we did not read
        self._unwritable_noted = False
        self.created = False             # True when this start made settings.txt: the first start (the original's missing
        #                                  footbal0.dat, GAME_SPEC 3 step 6, which shows the welcome and the voice choice)
        self._written: dict[str, str] = {}   # name -> value of the last text written or read, for the debug log's "setting" lines

    # ----- loading -----

    def load(self) -> Settings:
        """Read settings.txt (creating or resetting it as needed) and return the settings in force."""
        try:
            self._load()
        except Exception:                # a last-resort net: whatever happens the original settings run
            log.exception("settings could not be loaded; using the original settings")
            self.settings = Settings.defaults()
        return self.settings

    def _load(self) -> None:
        self.settings = Settings.defaults()
        if not os.path.isfile(self.path):
            self.created = True
            self._create("created")
            return
        try:
            settings, problems = parse(read_player_text(self.path))
        except OSError as exc:           # FileInUse, or any other failure to read the file
            log.warning("%s cannot be read now (%s); using the original settings, nothing is saved this run",
                        self.path, exc)
            self._save_blocked = True
            self._notices.append(IN_USE_NOTICE)
            return
        except (ValueError, UnicodeError) as exc:
            log.warning("%s is unusable (%s); resetting it", self.path, exc)
            saved = save_damaged_copy(self.path)
            if self._write(Settings.defaults()):
                self._notices.append("settings.txt was damaged and has been reset to the original settings."
                                     + (" A copy was saved." if saved else ""))
            return
        self.settings = settings
        self._problems = problems
        self._remember(settings)
        debuglog.event("settings", "loaded", path=self.path, problems=len(problems))
        if problems:
            for problem in problems:
                log.warning("%s: %s", FILE_NAME, problem)
            count = len(problems)
            self._notices.append(f"{count} problem{'s' if count != 1 else ''} found in settings.txt, "
                                 "details are in the log.")

    def _create(self, why: str) -> None:
        if self._write(self.settings):
            log.info("%s %s", why, self.path)

    # ----- saving -----

    def save(self) -> bool:
        """Write the settings now (called after every change). False when it could not be written."""
        if self._save_blocked:
            return False
        return self._write(self.settings)

    def _remember(self, settings: Settings) -> dict[str, str]:
        """The values of the text render() makes, by name (the voice notes and the header are left out)."""
        values: dict[str, str] = {}
        for line in render(settings).splitlines():
            if line and not line.startswith("#"):
                name, _, value = line.partition(" = ")
                values[name] = value
        old, self._written = self._written, values
        return old

    def _write(self, settings: Settings) -> bool:
        if write_text_atomic(self.path, render(settings, self.voice_name)):
            self._unwritable_noted = False
            old = self._remember(settings)
            for name, value in self._written.items():        # the debug log: every setting that changed, old and new
                if old.get(name, value) != value:
                    debuglog.event("settings", "changed", logging.INFO, name=name, old=old[name], new=value)
            return True
        if not self._unwritable_noted:
            self._unwritable_noted = True
            self._notices.append(UNWRITABLE_NOTICE)
        return False

    # ----- notices -----

    def note_voice_fallback(self, wanted: str | None, used: str) -> None:
        """A voice in settings.txt is not installed any more: say so once (the saved choice is kept)."""
        if wanted and wanted.lower() != (used or "").lower() and VOICE_MISSING_NOTICE not in self._notices:
            self._notices.append(VOICE_MISSING_NOTICE)

    def note_voice_crashed(self, label: str, used: str) -> None:
        """A saved voice took the program down last time: say so once (the saved choice is kept, picking it again
        retries)."""
        self._notices.append(f"The voice {label} crashed {GAME_NAME} last time, so the game uses "
                             f"{used or 'the first voice'} for now. Choose it again with F12 to try it again.")

    def take_notices(self) -> list[str]:
        notices, self._notices = self._notices, []
        return notices

    @property
    def problems(self) -> list[str]:
        return list(self._problems)
