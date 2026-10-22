"""Settings with the original's values as defaults. This is inspired by Jim Kitchen.

The original kept the five voice numbers and the rate vr in footbal0.dat, and the five voice volumes, the sound volume
wavol and the comments flag comtog in football.vol (GAME_SPEC 12). The clone keeps them all in its own settings.txt in
the per-user data folder (data/settingsfile.py; GAP_REGISTER G-F8, D-024 item 3): voices as voice ids, because voice
numbers mean nothing on another PC (G-S8); footbal0.dat and football.vol are neither written nor imported.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..speech.roles import ALL_ROLES, DEFAULT_VOLUME

SOUND_LEVEL_MIN, SOUND_LEVEL_MAX = -5000, 0     # wavol, hundredths of a decibel (F11 part 2, GAME_SPEC 4.6)


@dataclass
class SpeechSettings:
    mode: str = "sapi"           # "sapi" (G-S7: the five voices are part of the game), "nvda", "jaws", "auto"
    voices: dict[str, str | None] = field(default_factory=lambda: {role: None for role in ALL_ROLES})
    # None = the first voice in SAPI's list (the original's voice 0, GAME_SPEC 3 step 4)
    volumes: dict[str, int] = field(default_factory=lambda: {role: DEFAULT_VOLUME for role in ALL_ROLES})
    rate: int | None = None      # vr; None = the first voice's own rate, read and kept (GAME_SPEC 3 step 3)
    pitch: int = 0               # clone addition; 0 sends text exactly as the original did
    list_letters: str = "type"   # clone addition: letter keys in lists: "type" = type-ahead search, "first" = first-letter jump


@dataclass
class GameSettings:
    comments: bool = True        # F8 (ctog, GAME_SPEC 4.5): comtog 0 or Empty = the announcer's comments are on
    # nfl4 only (rule 0.13, NFL_EXTRAS_DESIGN 12.1, PX SX.2): the Rules setting and the switches of the extra features
    rules: str = "nfl"           # "nfl" (the N. F. L. rules: the default for a new player since SX.9, NQ2) or "classic" (the original)
    nx_timeouts: bool = True     # the real clock's timeouts in N. F. L. rules mode
    nx_penalties: bool = True    # the penalties with accept or decline in N. F. L. rules mode (SX.3)
    nx_onside: bool = True       # the onside kicks of the N. F. L. rules mode (SX.4)
    nx_onside_question: str = "always"     # "always": the player is asked at every kick-off and safety kick (the 2026 rule 6-1-6, D-085);
    #                                        "sensible": only when it makes sense (the player's own choice in the Rules menu)
    nx_onside_question_chosen: bool = False   # the player chose "sensible" or "always" himself (a file from before SX.2b never did)
    nx_qb_runs: bool = True      # the quarterback sneak, keeper, draw and scramble of the N. F. L. rules mode (SX.5)
    nx_challenges: bool = True   # the ruling model, booth reviews and replay challenges of the N. F. L. rules mode (SX.6)
    nx_offense_playbook: str = "team"      # the player's offense playbook (SX.7): classic, team (the team's style) or a style key;
    #                                        the team's since SX.10e (D-095): every play of the catalog by default (D-083)
    nx_defense_playbook: str = "team"      # and the defense playbook
    nx_broadcast: bool = True    # the radio broadcast of the N. F. L. rules: the announcer's radio banter and Ghip, the color commentator (SY.1, rule 0.27)
    nx_playbook_chosen: bool = False       # the player chose a playbook himself (a file from before SX.10e never did: its Classic, the old
    #                                        default, becomes the team's once)
    # the Franchise (SX.8a, NFL_FRANCHISE_DESIGN 10.5): nfl4 only; the Rules menu's reset leaves them alone
    nx_season_kind: str = "classic"        # "classic" or "franchise": which kind of season the player is in
    nx_fr_auto: bool = False               # the staff handles the to-do list and the roster cut (SX.8e)
    nx_fr_offseason: str = "full"          # "full" or "short": every stage of the offseason, or a sentence per stage
    nx_fr_picks_told: str = "first"        # "first", "mine" or "all": which picks of the draft are told (SX.8d)
    # the detailed debug log (owner rule 0.15, playbook 7.11): detailed (default), trace, normal or off; a clone addition
    debug_log: str = "detailed"


@dataclass
class AudioSettings:
    sound_level: int = 0         # wavol: 0 (full) down to -5000 hundredths of a decibel, added to every sound (GAME_SPEC 10)
    commercials: str = "off"     # clone addition (rule 0.14): off, every, second or third = the player's commercial files play at every,
                                 # every second or every third break of the game; off until the player turns it on
    # S7.2 removed the kit's Brain-only fields (effects volume, pitch spread, sounds start early): nfl4's only sound
    # level is wavol (D-038), and it has no "sounds start right away" setting (G-S11).


@dataclass
class Settings:
    speech: SpeechSettings
    audio: AudioSettings = field(default_factory=AudioSettings)
    game: GameSettings = field(default_factory=GameSettings)

    @classmethod
    def defaults(cls) -> "Settings":
        return cls(speech=SpeechSettings())
