"""The program flow of NFL Football 4. This is inspired by Jim Kitchen.

GAME_SPEC 3. The original did everything inside Form_Load as one long routine with jumps; here each part will be a
method, in the same order and with the same waits. There is no window, sound card or screen reader code in this
module: it talks to a SpeechManager and a KeyInput, so the tests run it with fakes on a virtual clock
(tests/gamerig.py). App code (app.py) wires the real ones.

P7 S7.1 is the SKELETON: the spoken title once per launch (rule 0.5.1, GAP_REGISTER G-F1), the notices the settings
file and the voice crash guard collected (said once, playbook 7.10), then a key wait that ends the program on Escape.
S7.4 replaces run() with the start-up of GAME_SPEC 3 (intro music, first-run welcome, season set-up, the week loop, the
main menu, the exit sequence with its beeps and sentence); Escape does not end the original from the main menu.

P7 S7.3a adds the season frame the later sessions stand on: the speakers (game/speakers.py), the one random function
(game/rnd.py), the league, the name pool, the season state, and the original's procedures SayStand, SayScore,
SayFinalScore and sgc as methods (say_stand, say_score, say_final_score, sgc) and `makes` (make_schedule), `GetTeams`
and `SetPlayerNames` (the league and the pool), pag's set-up (new_game_setup).
"""
from __future__ import annotations

import logging
import time
from typing import Callable

from ..data.settings import Settings
from . import scorespeech, texts
from .gameclock import QuarterClock
from .hotkeys import HotKeys
from .keys import KEY_ESCAPE, KeyInput
from .league import League
from .names import NamePool
from .options import Options
from .prompts import Prompts
from .rnd import GameRandom
from .rules import CLASSIC
from .season import SeasonState
from .setup import GameSetup, Roster, new_game_setup
from .speakers import Speakers
from .standings import standings_speech

log = logging.getLogger("nfl4.game")

KEY_CODE_F1 = "112"     # the key code text a global menu and sgc leave in g: the waiting prompt then repeats


class Game(Speakers):
    def __init__(self, speech, keys: KeyInput, clock: Callable[[], float] = time.monotonic,
                 sleep: Callable[[float], None] = time.sleep, notice_sources=(), sounds=None,
                 rnd: GameRandom | None = None, league: League | None = None, pool: NamePool | None = None,
                 options: Options | None = None, rules=None):
        super().__init__(speech, keys, rnd)
        self.clock = clock
        self.sleep = sleep
        self.notice_sources = tuple(notice_sources)   # objects with take_notices() (the settings file, the audio layer)
        self.sounds = sounds                          # game.sounds.GameSounds: the original's sound procedures (S7.2)
        self.league = league if league is not None else League()      # GetTeams (S7.7 fills it from teams.txt)
        self._pool = pool                             # SetPlayerNames: the 1,708 surnames, loaded when first needed
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
        self._season_engine = None
        self.play_engine = None                       # the running pag, so F12's GetSexOf reaches its He and She words
        self.prompts = Prompts(self)                  # getter, GetCoach, ChooseTeam, Getqbs, SayScedual (S7.4a)
        self.hotkeys = HotKeys(self)                  # F5 to F8, F11, F12, Ctrl inside every wait (S7.4a, D-018)
        self.hotkeys.install()

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

    def new_game_setup(self, own_names: Roster | None = None) -> GameSetup:
        """pag's set-up GoSub (GAME_SPEC 5.5): the rosters, the banter names, the periods' lengths and the warnings; the
        three warning lengths also go to the clock."""
        setup = new_game_setup(self.rnd, self.pool, own_names)
        self.quarter_clock.set_warnings(*setup.warnings)
        self.quarter_clock.start_quarter()
        return setup

    def sgc(self, played: int, total: int, quarter: int) -> None:
        """The game clock (GAME_SPEC 5.3): say5 the made-up time, clk, then g = "112" so the waiting prompt repeats."""
        self.say5(self.quarter_clock.advance(played, total, quarter, self.rnd))
        self.keys.clk()
        self.keys.code_text = KEY_CODE_F1

    @property
    def comtog(self) -> int:
        return int(self.comtog_source())

    # ----- the game itself: pag (S7.3b) -----

    def play_game(self, rules=None, own_names: Roster | None = None, saved=None, quarterback_names=None,
                  save_sink=None):
        """pag (GAME_SPEC 4.14 to 5.13): one game against this week's opponent. Returns a GameResult (Me.m414, saved,
        conceded); m414 is kept for the season engine. rules: game.rules.ClassicRules (the original) unless the
        N. F. L. rules mode hands its own (nfl4 only, phase PX)."""
        from .pag import PlayEngine
        engine = PlayEngine(self, rules or self.rules, own_names=own_names, saved=saved,
                            quarterback_names=quarterback_names, save_sink=save_sink)
        self.play_engine = engine
        try:
            result = engine.run()
        finally:
            self.play_engine = None
        if result.scores is not None:
            self.m414 = result.scores
        return result

    def getqbs(self, state, saved: bool = False, own_from_file: str = "") -> tuple[str, str]:
        """Getqbs (GAME_SPEC 4.12): the two quarterbacks' names (game/prompts.py)."""
        return self.prompts.getqbs(state, saved=saved, own_from_file=own_from_file)

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

    def say_stand(self) -> None:
        """SayStand (GAME_SPEC 5.2): the standings after the week just played, nothing when gtp is 0 or above 17. The
        original clears the key twice (clk) on the way, the second time only when it will speak."""
        self.keys.clk()
        speech = standings_speech(self.league, self.season.records, self.season.gtp)
        if speech is None:
            return
        self.keys.clk()
        self.ptf = 1
        self.say2(speech.heading)
        for division_text, lines in speech.divisions:
            self.say2(division_text)
            for line in lines:
                self.say2(line)
            self.log_print("")
        self.ptf = 0

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
        self.say(texts.TITLE_SPOKEN)              # once per launch (rule 0.5.1, G-F1)
        self.speak_notices()
        while True:                               # S7.1 skeleton: S7.4 builds the week loop and the main menu here
            self.keys.getkey(self.speech)
            if self.keys.code_text == str(KEY_ESCAPE):
                log.info("skeleton: Escape ends the program")
                return
