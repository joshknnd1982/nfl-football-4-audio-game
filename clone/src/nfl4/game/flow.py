"""The program flow of NFL Football 4. This is inspired by Jim Kitchen.

GAME_SPEC 3. The original did everything inside Form_Load as one long routine with jumps; here each part will be a
method, in the same order and with the same waits. There is no window, sound card or screen reader code in this
module: it talks to a SpeechManager and a KeyInput, so the tests run it with fakes on a virtual clock
(tests/gamerig.py). App code (app.py) wires the real ones.

P7 S7.1 was the SKELETON (the title, the notices, a key wait). P7 S7.4b replaced its run() with Form_Load's flow in
game/program.py (start-up, season set-up, week loop, main menu, exit); the Game keeps the original's procedures as methods.

P7 S7.3a adds the season frame the later sessions stand on: the speakers (game/speakers.py), the one random function
(game/rnd.py), the league, the name pool, the season state, and the original's procedures SayStand, SayScore,
SayFinalScore and sgc as methods (say_stand, say_score, say_final_score, sgc) and `makes` (make_schedule), `GetTeams`
and `SetPlayerNames` (the league and the pool), pag's set-up (new_game_setup).
"""
from __future__ import annotations

import logging
import time
from typing import Callable

from ..data import debuglog, paths
from ..data.settings import Settings
from . import scorespeech
from .banter_pool import DEFAULT_POOL, BanterPool
from .functions import Functions
from .gameclock import QuarterClock
from .hotkeys import HotKeys
from .keys import KeyInput
from .league import League
from .names import NamePool
from .options import Options
from .program_store import MemoryProgramStore
from .prompts import Prompts
from .rnd import GameRandom
from .rules import CLASSIC
from .season import SeasonState
from .season_engine import CLASSIC_SEASON_HOOKS
from .setup import GameSetup, Roster, new_game_setup
from .speakers import ANNOUNCER, Speakers
from .standings import standings_speech

log = logging.getLogger("nfl4.game")

KEY_CODE_F1 = "112"     # the key code text a global menu and sgc leave in g: the waiting prompt then repeats


class Game(Speakers):
    def __init__(self, speech, keys: KeyInput, clock: Callable[[], float] = time.monotonic,
                 sleep: Callable[[float], None] = time.sleep, notice_sources=(), sounds=None,
                 rnd: GameRandom | None = None, league: League | None = None, pool: NamePool | None = None,
                 options: Options | None = None, rules=None, program_store=None,
                 open_folder: Callable[[str], bool] = paths.open_folder, settings_dir: str | None = None,
                 customization=None):
        super().__init__(speech, keys, rnd)
        self.clock = clock
        self.sleep = sleep
        self.notice_sources = tuple(notice_sources)   # objects with take_notices() (the settings file, the audio layer)
        self.sounds = sounds                          # game.sounds.GameSounds: the original's sound procedures (S7.2)
        if sounds is not None and getattr(sounds, "announce", None) is None:
            # owner rule 0.14: the spoken "Commercial" before a commercial; not logged, not kept for the replay
            sounds.announce = lambda text: self._speak(text, ANNOUNCER, True)
        self.league = league if league is not None else League()      # GetTeams (S7.7 fills it from teams.txt)
        self._pool = pool                             # SetPlayerNames: the 1,708 surnames, loaded when first needed
        self.banter_pool: BanterPool = DEFAULT_POOL   # the 142 lines plus the player's (S7.7, banter.txt)
        self.banter_sounds_dir: str | None = None     # customize\sounds: the player's files for [sound file] in a line
        self.remark_pools = None                      # the extras' remarks.txt (nfl4 only, SX.2); None = the defaults
        self.foul_table = None                        # the extras' penalties.txt (nfl4 only, SX.3); None = the defaults
        self.playbook_table = None                    # the extras' playbooks files (nfl4 only, SX.7); None = the defaults
        self.news_pools = None                        # the Franchise's news.txt (nfl4 only, SX.8e); None = the defaults
        self.injury_pools = None                      # the Franchise's injuries.txt (nfl4 only, SX.8k); None = the defaults
        self.favourite_plays = None                   # the player's favourites.txt (nfl4 only, SX.10c): (offense, defense) IDs
        self.real_names = None                        # the real coaches and rosters (nfl4 only, SX.11, extras.real_names.RealNames); None = the original's names
        self.customization = None                     # data.customize.Customization: the player's files (S7.7)
        self.season = SeasonState()                   # the coach, the teams, the week, the schedule, the records
        self.quarter_clock = QuarterClock()           # oldtime, mins, secs, CountDown, M2W, M4W, M5W
        self.coach_source = lambda: self.season.coach
        # S7.4a: the values the hot keys change (vr, comtog, the volumes, wavol, the voices) and where they are saved;
        # without one (the tests) the defaults, saved nowhere, sharing the sounds' AudioSettings
        if options is None:
            settings = Settings.defaults()
            if sounds is not None:
                settings.audio = sounds.settings
            options = Options(settings, speech)
        self.options = options
        self.vr_source = lambda: self.options.vr       # rady's rate counter (Ctrl changes it)
        self.comtog_source: Callable[[], int] = lambda: self.options.comtog   # F8: 1 = the comments (banter) are off
        self.rules = rules if rules is not None else CLASSIC   # the program's rules (H12 reads them; pag gets them)
        self.m414: tuple[int, int] | None = None      # the last game's result for the season engine (S7.3c)
        self.season_store = None                      # S7.5: writes football.gtp, footbal3.dat, footbal4.dat, footbal5.dat
        self.setup_store = None                       # S7.5: writes footbal1.dat, footbal2.dat and the quarterback line
        # nfl4 only (rule 0.13, SX.8a): H14's hooks (Classic: nothing), the franchise's store (made when first needed, only with
        # the N. F. L. rules; `franchise_factory(classic_store)` makes it, None = in memory for the tests) and the classic
        # season parked while the franchise is in use
        self.season_hooks = CLASSIC_SEASON_HOOKS
        self.franchise_factory: Callable | None = None
        self._franchise_store = None
        self.parked_classic: SeasonState | None = None
        self._season_engine = None
        self.play_engine = None                       # the running pag, so F12's GetSexOf reaches its He and She words
        self.game_injuries = None                     # nfl4 only (SX.8k): a Franchise game's injuries while it is played; None in every other game
        self.prompts = Prompts(self)                  # getter, GetCoach, ChooseTeam, Getqbs, SayScedual (S7.4a)
        self.hotkeys = HotKeys(self)                  # F5 to F8, F11, F12, Ctrl inside every wait (S7.4a, D-018)
        self.hotkeys.install()
        self.program_store = program_store if program_store is not None else MemoryProgramStore()   # S7.4b, S7.5
        # SX.14 (CLAUDE.md 0.23): the start-up choice and the save questions; the tests of the original's start-up (tests/gamerig.py) turn them off
        self.startup_menu = True
        self.functions = Functions(self, open_folder=open_folder, settings_dir=settings_dir)       # F9 (S7.4b, G-K2)
        self.functions.install()
        self.program = None                           # the running Program (game/program.py), for the tests and the exit
        if customization is not None:
            self.customization = customization
            self.apply_customization()

    @property
    def keys(self) -> KeyInput:
        return self._keys

    @keys.setter
    def keys(self, keys: KeyInput) -> None:
        """The hot keys follow the Game's key input: a test rig that swaps it keeps F5 to F12 and Ctrl working."""
        self._keys = keys
        hotkeys = self.__dict__.get("hotkeys")
        if hotkeys is not None:
            hotkeys.install()

    @property
    def pool(self) -> NamePool:
        if self._pool is None:
            self._pool = NamePool(self.rnd)
        return self._pool

    def apply_customization(self) -> None:
        """Take the values of the player's loaded files (S7.7): the team and division names, the surnames the next draws use
        (a game in progress keeps the roster it drew), the banter pool and the folder of the banter's own sounds. Never
        raises: what cannot be applied stays as it was."""
        custom = self.customization
        if custom is None:
            return
        try:
            snapshot = custom.snapshot
            self.league.rename(snapshot.team_names, snapshot.division_names)
            if snapshot.surnames is not None:
                if self._pool is None:
                    self._pool = NamePool(self.rnd, snapshot.surnames)
                else:
                    self._pool.replace_names(snapshot.surnames)
            self.banter_pool = snapshot.banter
            self.banter_sounds_dir = custom.sounds_dir
            self.remark_pools = snapshot.remarks              # None while the Rules are Classic (the file is not read)
            self.foul_table = snapshot.fouls                  # the same for penalties.txt (SX.3)
            self.playbook_table = snapshot.playbooks          # and the playbooks' three files (SX.7)
            self.news_pools = snapshot.news                   # and the Franchise's news.txt (SX.8e)
            self.injury_pools = snapshot.injuries             # and its injuries.txt (SX.8k)
            self.favourite_plays = snapshot.favourites        # and the favourite plays (SX.10c)
            self.real_names = snapshot.real_names             # and the real coaches, players and respellings (SX.11)
            if self.real_names is not None:
                debuglog.event("names", "loaded", version=self.real_names.version, coaches=sum(1 for c in self.real_names.coaches if c),
                               teams=sum(1 for r in self.real_names.rosters if r), respellings=len(self.real_names.respellings))
        except Exception:
            log.exception("the player's customization could not be applied")

    def apply_rules_setting(self) -> None:
        """The Rules setting changed (F9, nfl4 only, SX.2): the program's rules for the next game, and the extras' files
        read only when the rules are the N. F. L. rules (CUSTOMIZABLE_CONTENT 13). A game in progress keeps its rules."""
        from ..extras.nfl_rules import is_nfl, rules_from_settings
        self.rules = rules_from_settings(self.options.settings.game)
        if self.customization is not None:
            try:
                self.customization.use_extras(is_nfl(self.rules))
            except Exception:
                log.exception("the extras' customization files could not be loaded")
            self.apply_customization()
        if self.program is not None:                  # SX.8a: the kind of season follows the Rules (design 3.1)
            self.program.rules_changed()

    def franchise(self):
        """The franchise's store (nfl4 only, SX.8a): made when first needed, never with Rules = Classic. It opens the folder
        itself (`open`), so asking for it touches no file."""
        if self._franchise_store is None:
            from ..extras.franchise.files import MemoryFiles
            from ..extras.franchise.store import FranchiseStore
            if self.franchise_factory is not None:
                store = self.franchise_factory(self.program_store)
            else:
                store = FranchiseStore(MemoryFiles(), self.program_store)
            self._franchise_store = store
            self.notice_sources = self.notice_sources + (store,)
        return self._franchise_store

    def franchise_help(self, key: str) -> list:
        """The added help lines of F5, F6 and F7 while the franchise is in use (nfl4 only, SX.8e, H12); none in a classic season."""
        if not self.franchise_in_use:
            return []
        from ..extras.franchise.menus import help_lines
        return help_lines(key)

    @property
    def franchise_in_use(self) -> bool:
        """True while the franchise is the kind of season being played (nfl4 only, SX.8a)."""
        return self.program is not None and self.program.mode.kind == "franchise"

    # ----- the season frame: the original's procedures -----

    def own_team(self) -> str:
        """Me.m294(tn1 + tn2 * 9): the player's team."""
        return self.league.team(self.season.tn1, self.season.tn2)

    def opponent_team(self) -> str:
        """Me.m294(tn3 + tn4 * 9): this week's opponent."""
        return self.league.team(self.season.tn3, self.season.tn4)

    def make_schedule(self):
        """makes (GAME_SPEC 5.1): a new schedule for the player's team, written to footbal2.dat (setup_store, S7.5)."""
        schedule = self.season.make_schedule(self.rnd)
        if self.setup_store is not None:
            self.setup_store.write_schedule(schedule)
        return schedule

    # ----- the typed prompts and questions of the season (S7.4a, game/prompts.py) -----

    def getter(self, prompt: str) -> str:
        return self.prompts.getter(prompt)

    def get_coach(self) -> str:
        """GetCoach (GAME_SPEC 4.9): the coach's typed name, confirmed."""
        return self.prompts.get_coach()

    def coach_and_team(self) -> None:
        """GetCoach and ChooseTeam; with the N. F. L. rules and the real names the team is chosen first and the real coach of that team
        is offered, so nothing is typed (nfl4 only, SX.11, NX-N1)."""
        self.prompts.coach_and_team()

    def choose_team(self) -> None:
        """ChooseTeam (4.10): the player's team, confirmed, then footbal1.dat."""
        self.prompts.choose_team()

    def say_schedule(self) -> None:
        """SayScedual (4.11): the schedule, and before week 1 the question whether the player likes it."""
        self.prompts.say_schedule()

    def get_sex_of(self) -> None:
        """GetSexOf at the end of F12 (0x428e38): the He and She words of the game in progress follow the new voices
        (pag runs it again at the start of every game)."""
        if self.play_engine is not None:
            self.play_engine.get_sex_of()

    def new_game_setup(self, own_names: Roster | None = None, opponent_names: Roster | None = None,
                       real_names: bool = False) -> GameSetup:
        """pag's set-up GoSub (GAME_SPEC 5.5): the rosters, the banter names, the periods' lengths and the warnings; the
        three warning lengths also go to the clock. `opponent_names` is the Franchise's opponent (nfl4 only, SX.8b). `real_names`
        (nfl4 only, SX.11, the N. F. L. rules): the sides whose names the original draws take the real players of their teams."""
        setup = new_game_setup(self.rnd, self.pool, own_names, opponent_names)
        if real_names and self.real_names is not None:
            self._real_rosters(setup, own_names, opponent_names)
        self.quarter_clock.set_warnings(*setup.warnings)
        self.quarter_clock.start_quarter()
        return setup

    def _real_rosters(self, setup: GameSetup, own_names: Roster | None, opponent_names: Roster | None) -> None:
        """NX-N5: the names the set-up drew (after the draws, so a game draws exactly what it drew with the original's names) are replaced
        by the real players of the two teams: the player's own team when footplay.txt has to be written (a file the player has is
        the player's), the opponent when it is not a Franchise team. A place a team has no player for keeps the drawn name."""
        from ..extras.franchise.league import team_index
        season, real = self.season, self.real_names
        changed = []
        for side, names, tn1, tn2 in ((1, own_names, season.tn1, season.tn2), (2, opponent_names, season.tn3, season.tn4)):
            if names is not None:
                continue
            roster = real.roster(team_index(tn1, tn2), setup.rosters[side]) if 1 <= tn1 <= 8 and 1 <= tn2 <= 4 else None
            if roster is not None:
                setup.rosters[side] = roster
                changed.append(side)
        if changed:
            setup.banter_names = [name for side in (1, 2) for name in (setup.rosters[side].running_backs + setup.rosters[side].receivers
                                                                       + setup.rosters[side].defense)]
            debuglog.event("names", "real_rosters", sides=changed, version=real.version)

    def sgc(self, played: int, total: int, quarter: int) -> None:
        """The game clock (GAME_SPEC 5.3): say5 the made-up time, clk, then g = "112" so the waiting prompt repeats."""
        self.say_clock(self.quarter_clock.advance(played, total, quarter, self.rnd))

    def say_clock(self, text: str) -> None:
        """sgc's ending for a clock sentence: say5, clk, g = "112" (the real clock of the N. F. L. rules mode uses it too)."""
        self.say5(text)
        self.keys.clk()
        self.keys.code_text = KEY_CODE_F1

    @property
    def comtog(self) -> int:
        return int(self.comtog_source())

    # ----- the game itself: pag (S7.3b) -----

    def play_game(self, rules=None, own_names: Roster | None = None, saved=None, quarterback_names=None,
                  save_sink=None, roster_sink=None, opponent_names: Roster | None = None, game_injuries=None,
                  autosave_sink=None, save_ui=None):
        """pag (GAME_SPEC 4.14 to 5.13): one game against this week's opponent. Returns a GameResult (Me.m414, saved,
        conceded); m414 is kept for the season engine. rules: game.rules.ClassicRules (the original) unless the
        N. F. L. rules mode hands its own (nfl4 only, phase PX). opponent_names: the Franchise's opponent (H7, SX.8b). game_injuries: a
        Franchise game's injuries (SX.8k; the N. F. L. rules read it, H16 and H2), None in every other game."""
        from .pag import PlayEngine
        rules = (rules or self.rules).for_game()       # the N. F. L. rules get a fresh object per game; Classic is itself
        engine = PlayEngine(self, rules, own_names=own_names, saved=saved,
                            quarterback_names=quarterback_names, save_sink=save_sink, roster_sink=roster_sink,
                            opponent_names=opponent_names, autosave_sink=autosave_sink, save_ui=save_ui)
        self.play_engine = engine
        self.game_injuries = game_injuries
        try:
            result = engine.run()
        finally:
            self.play_engine = None
            self.game_injuries = None
        if result.scores is not None:
            self.m414 = result.scores
        return result

    def getqbs(self, state, saved: bool = False, own_from_file: str = "", defaults: tuple[str, str] | None = None) -> tuple[str, str]:
        """Getqbs (GAME_SPEC 4.12): the two quarterbacks' names (game/prompts.py). `defaults` (nfl4 only, SX.11): the real quarterbacks
        of the two teams, the names Enter takes instead of a drawn surname."""
        names = self.prompts.getqbs(state, saved=saved, own_from_file=own_from_file, defaults=defaults)
        debuglog.add_typed(*names)            # typed now or read from footplay.txt: the debug log hides them (playbook 7.11)
        return names

    def halftime(self) -> None:
        """halftime (p_485b80): foot0, 15 celebration sounds, foot0 (game/sounds.py)."""
        self.sounds.halftime()

    # ----- the season engine and the play-offs: pog, finplay17, superbowl (S7.3c) -----

    @property
    def season_engine(self):
        """pog, finplay17 and the Super Bowl presentation (game/season_engine.py); its state is `season`."""
        if self._season_engine is None:
            from .season_engine import SeasonEngine
            self._season_engine = SeasonEngine(self)
        return self._season_engine

    def pog(self):
        """pog (GAME_SPEC 5.14 to 5.16): after a game that was not saved, when gtp is not 0; uses `m414`. The speech log
        flag ptf stays 1, as in the original: the week loop sets it to 0 afterwards (Form_Load)."""
        return self.season_engine.pog()

    def finplay17(self) -> None:
        """finplay17 (GAME_SPEC 5.17): the rounds without the player's team, to the Super Bowl and the celebration."""
        self.season_engine.finplay17()

    def superbowl(self, scores: tuple[int, int]) -> None:
        """superbowl (p_484860, GAME_SPEC 5.6 item 7): the Super Bowl presentation after the player's Super Bowl game, in
        place of the final score; gtp is 42 at its end and pag sets 0."""
        self.season_engine.super_bowl_presentation(scores)

    def say_score(self, own_score: int, opponent_score: int) -> None:
        """SayScore (F3): " The score is ", the sentence (waited), then two lines to the log whatever ptf is, DoEvents."""
        self.say5(scorespeech.THE_SCORE_IS)
        sentence = scorespeech.score_sentence(self.own_team(), self.opponent_team(), own_score, opponent_score)
        self.say(sentence)
        self.log_print("")
        self.log_print(scorespeech.THE_SCORE_IS + sentence)
        self.keys.pump()

    def say_final_score(self, own_score: int, opponent_score: int) -> None:
        """SayFinalScore: ptf = 1, " The Final score is", the sentence (waited), ptf = 0."""
        self.ptf = 1
        self.say5(scorespeech.THE_FINAL_SCORE_IS)
        self.say(scorespeech.score_sentence(self.own_team(), self.opponent_team(), own_score, opponent_score))
        self.ptf = 0

    def say_stand(self) -> bool:
        """SayStand (GAME_SPEC 5.2): the standings after the week just played, nothing when gtp is 0 or above 17. The
        original clears the key twice (clk) on the way, the second time only when it will speak. True when it spoke."""
        self.keys.clk()
        speech = standings_speech(self.league, self.season.records, self.season.gtp)
        if speech is None:
            return False
        self.keys.clk()
        self.ptf = 1
        self.say2(speech.heading)
        for division_text, lines in speech.divisions:
            self.say2(division_text)
            for line in lines:
                self.say2(line)
            self.log_print("")
        self.ptf = 0
        return True

    # ----- the flow -----

    def speak_notices(self) -> None:
        """Short sentences about damaged files and voices, each said once (playbook 7.10)."""
        for source in self.notice_sources:
            try:
                notices = source.take_notices()
            except Exception as exc:              # a notice source must never stop the game
                log.warning("notices of %s failed: %s", type(source).__name__, exc)
                continue
            for notice in notices:
                self.say(notice)

    def run(self) -> None:
        """Form_Load (GAME_SPEC 3): start-up, the season set-up, the week loop with the main menu, the exit. game/program.py."""
        from .program import Program
        self.program = Program(self, self.program_store)
        self.program.run()
