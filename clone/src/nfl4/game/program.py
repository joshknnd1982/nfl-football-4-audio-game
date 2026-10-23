"""The whole program: start-up, the week loop, the main menu, what follows a game, and the exit. This is inspired by Jim Kitchen.

GAME_SPEC 3 and 4 (CODE (lifted) Form_Load p_486990, read in full in S7.4b: work/lift/p_486990_Form_Load.vb.txt, 494 lines).
The original did everything inside Form_Load with jumps; here each part is a method in the same order with the same waits,
texts, sounds and pauses, and the address of its lifted line beside it. What the clone does differently, each decided before:

* after a game the program returns to the week loop instead of ending (D-024 item 1, G-F2): the results and the standings
  are spoken, the standings wait for one key only when they were spoken (Q53 not reproduced), the crowd beds restart when
  the week loop begins (G-A5, B-A12); Save Game still ends the program (the saved game is loaded at the next start);
* a season that is over (gtp = 0) deletes its files, says so and runs the new-season set-up (G-F3, D-029 item 4);
* the title replaces the original's spoken title and is said at every launch, once (rule 0.5.1, G-F1);
* the exit is foot0, the thank-you, then the sounds stop and the program ends; the original's "game menu not found" branch
  (two beeps and a closing sentence, D-006, G-F6, B-X13) is gone (owner, S8.2, D-100, rule 0.26: no game says a menu program
  is missing);
* the voice choice of the first start is asked only when SAPI 5 speaks (D-022 item 4); the files are a `ProgramStore` (S7.5).

Not here: pag (game/pag.py), pog and finplay17 (game/season_engine.py), the typed prompts (game/prompts.py), the hot keys
(game/hotkeys.py) and F9 (game/functions.py); this module calls them where Form_Load does.
"""
from __future__ import annotations

import logging

from ..data import debuglog
from . import extra_texts as words
from . import program_texts as P
from . import prompt_texts as T
from . import save_texts, texts
from .keys import GameQuit
from .save_menu import SaveUi
from .season_mode import ClassicSeason
from .startup_menu import StartupMenu, primary
from .vbnum import str_, trim

log = logging.getLogger("nfl4.game")

KEY_ENTER, KEY_UP, KEY_DOWN, KEY_F1 = "13", "38", "40", "112"
INTRO_PAUSE = 0.2           # dy(0.2) before and after the F5 list of the first start (0x487d81, 0x487dea)
MENU_CHOICES = 4


class Program:
    def __init__(self, game, store):
        self.g = game
        self.store = store
        self.saved_game = False         # SavedGame (football.sav was there at the start; pag clears it when it loads it)
        self.intro_playing = False      # L68: the intro's loop (foot0) is still playing
        self.beds_stopped = False       # pag stopped the crowd beds: the week loop starts them again (G-A5)
        self.log_open = False           # L7c: footballlog.txt is opened once per run
        self.week_text = ""             # L118: the play-off week's text the menu speaks again (regular weeks: nothing)
        self.week_intro = ""            # Q5 / D-025 (a): the week line itself, said again before the menu's own lines after F1
        self.today_text = ""            # L11c: "Today's game is ..."
        self.ending = ""                # why the program ends: "exit" (menu choice 4) or "saved" (Save Game)
        # H15 (nfl4 only, rule 0.13): the season frame as one mode object; ClassicSeason is the original's code moved
        self.mode = ClassicSeason(self)
        self.switch_requested = False   # a menu asked for another kind of season (F9, a change of the Rules): the week loop acts
        self.switch_target = None       # the kind it asked for when the settings do not say yet (a franchise to be made)
        # SX.14 (CLAUDE.md 0.23, playbook 7.17): the start-up choice and the save questions. The tests' rigs switch them off (Game.startup_menu =
        # False) so the many tests that pin the original's start-up stay exact; only the tests of the choice switch them on.
        self.menu_on = bool(getattr(game, "startup_menu", True))
        self.load_entry = None          # the save the start-up menu chose to continue (a shelf Entry); loaded at the first "play game"
        self.slot_in_use = None         # the slot the game in progress was loaded from or last saved in (Save Game offers it first)
        self.new_game = None            # "season" or "franchise": the start-up menu chose a new game
        self.new_defaults = None        # (coach, tn1, tn2) of the season a new season replaced: the last choices are the defaults (NX-S7)
        self.save_ui = SaveUi(self) if self.menu_on else None

    # ----- helpers -----

    @property
    def sounds(self):
        return self.g.sounds

    @property
    def keys(self):
        return self.g.keys

    @property
    def season(self):
        return self.g.season

    def _stop_intro(self, second_pump: bool = True, reason: str = "week_line") -> None:
        """`If L68 = 1: m220.Stop, DoEvents, Set m220 = Nothing, DoEvents, L68 = 0` (the week lines 0x488618 to 0x488694 and
        0x4888dd to 0x48894f). The first start's copy (0x487c4f to 0x487cb7) has no second DoEvents and does not test L68.
        S8.2 (owner 2026-10-20, CLAUDE.md 0.21, B-A22): the loop also ends when the welcome ends and, as a safety, before the first
        question of the season set-up; the original let it run to the week line, which a new season or a franchise makes a minute
        of the same sound while the player answers. Safe to call twice; the log says why it stopped."""
        if not self.intro_playing:
            return
        debuglog.event("sound", "loop_stop", sound="intro foot0", reason=reason)
        if self.sounds is not None:
            self.sounds.stop_oneshot()                          # Me.m220.Stop
        self.keys.pump()                                        # DoEvents (0x487c65, 0x488636, 0x4888f7)
        if second_pump:
            self.keys.pump()                                    # DoEvents after Set Nothing (0x488671, 0x48892c)
        self.intro_playing = False

    def _sapi_speaks(self) -> bool:
        """The five voices are SAPI's: the first-start choice only makes sense when SAPI is the active engine (D-022 item 4)."""
        engine = self.g.speech.active_engine()
        return engine is not None and getattr(engine, "takes_roles", False)

    def _screen_reader_wanted(self) -> bool:
        """True when the player answered yes to the screen reader question in this run (rule 0.28 (1)): the voice list is not offered then, even when
        the screen reader has closed since and SAPI speaks."""
        return getattr(self, "screen_reader_yes", False)

    def screen_reader_choice(self) -> None:
        """SZ.4 (D-109, a player's e-mail of 2026-10-22: the screen reader was not detected and the voices were asked for anyway). When NVDA or
        JAWS runs and the player has not yet said how the game speaks, the game says which one it found and asks, in the original's yes or no
        way (yes first, Y and N, Up and Down, Enter, F1), whether it should speak through it. Yes keeps the automatic mode and the game asks
        for no voice; no switches to the five Windows voices. Asked once: the answer is saved (F9, Speech settings changes it)."""
        g = self.g
        options = getattr(g, "options", None)
        speech = options.settings.speech if options is not None else None
        if speech is None or speech.mode_chosen or speech.mode == "sapi":
            return
        engine = g.speech.active_engine()
        if engine is None or getattr(engine, "takes_roles", False):
            return                                              # SAPI speaks (no screen reader runs): nothing to ask, the five voices are the game's
        name = getattr(engine, "name", "the screen reader")
        debuglog.event("app", "screen_reader_found", logging.INFO, engine=name, mode=speech.mode)
        no = g.prompts._confirm(words.SCREEN_READER_QUESTION % name, g.say5, g.say2)        # True: the answer was no
        speech.mode_chosen = True
        self.screen_reader_yes = not no
        if no:
            speech.mode = "sapi"
            g.speech.mode = "sapi"
        options.save()
        debuglog.event("app", "screen_reader_answer", logging.INFO, engine=name, uses_screen_reader=not no)
        g.say(words.SCREEN_READER_NO if no else words.SCREEN_READER_YES % name)

    # ----- the program -----

    def run(self) -> None:
        self.startup()
        self.season_setup()
        self.week_loop()
        self.exit_program()

    # ----- start-up (0x486f9b to 0x487e0d) -----

    def startup(self) -> None:
        g, keys, sounds = self.g, self.keys, self.sounds
        self.mode.choose_at_start()                             # H15: which kind of season is in use (Classic: nothing)
        # 0x4874e2 to 0x48756e: football.sav, SavedGame = 1. With the start-up menu (rule 0.23) nothing is loaded here: the player chooses
        # after the welcome; without it (the tests of the original's start-up) the newest saved game is played at once, as the original did
        self.saved_game = False
        self.load_entry = None
        if not self.menu_on and self.store.has_saved_game():
            self.saved_game = True
            self.load_entry = primary(self.store.shelf.scan(self.store.classify))
        g.ptf = 0                                               # 0x4872bc
        g.qorp = 1                                              # 0x4873dd
        if sounds is not None:
            sounds.start_crowds()                               # 0x4876f0 crowd1, crwd1 = -1200 0x48772c, crowd2 0x487731
            sounds.intro()                                      # clk 0x48778d, foot0 once, then looped (L68 = 1)
            self.intro_playing = True                           # 0x487b05
            debuglog.event("sound", "loop_start", sound="intro foot0")
        keys.pump()                                             # 0x487b0b DoEvents
        if sounds is not None:
            sounds.make_hike()                                  # 0x487b14
            sounds.make_play_noise()                            # 0x487b2f
        # SetPlayerNames 0x487b4a and GetTeams 0x487b65: the name pool and the league are the Game's (loaded when needed)
        if self.store.first_run():                              # 0x487bff: footbal0.dat missing
            # 0x487c20 g.say2(P.WELCOME_TO) is not said: the welcome sentence below says "Welcome to" itself, once (rule 0.16, G-F1)
            keys.pump()                                         # 0x487c44
            self._stop_intro(second_pump=False, reason="first_start")   # 0x487c4f (Stop), 0x487c65 (DoEvents), 0x487c88, L68 = 0 0x487cb7
            g.voice_speak(" ", wait=True)                       # 0x487cfa Voice.Speak " ", 0 (waits for the line above)
            g.say(texts.TITLE_SPOKEN)                           # 0x487d35: the welcome in place of " Jim's N. F. L. Football, version 4. "
            debuglog.event("app", "welcome_spoken", logging.INFO, first_start=True, text=texts.TITLE_SPOKEN)
            g.speak_notices()
            self.screen_reader_choice()                         # SZ.4: NVDA or JAWS runs: speak through it? (asked once, before any voice is asked)
            g.dy(INTRO_PAUSE, 0x487d81)
            g.hotkeys.speckeys()                                # 0x487daa: the F5 key list
            # S8.2: where F9 is is now a line of the key list itself (hotkeys.speckeys), so the first start has no separate sentence
            g.dy(INTRO_PAUSE, 0x487dea)
            if self._sapi_speaks() and not self._screen_reader_wanted():
                g.hotkeys.change_voice()                        # 0x487e0d ChangeVoice (writes footbal0.dat: settings.txt)
            elif self._sapi_speaks():
                # S8.3 round 2, rule 0.28 (1): the player said yes to the screen reader and it closed a moment later; yes still means no voice list
                debuglog.event("app", "voice_list_skipped", logging.INFO, reason="the player chose the screen reader")
        else:
            g.say(texts.TITLE_SPOKEN)                           # rule 0.16, G-F1: once per launch, the intro loop goes on
            debuglog.event("app", "welcome_spoken", logging.INFO, first_start=False, text=texts.TITLE_SPOKEN)
            g.speak_notices()
            self._stop_intro(second_pump=False, reason="welcome_done")   # S8.2: the intro ends with the welcome, not at the week line
            self.screen_reader_choice()                         # SZ.4: a player who has not said how the game speaks and runs a screen reader now
        if self.menu_on:                                        # SX.14: what to do with what is saved, before anything is loaded
            StartupMenu(self).run()

    # ----- the kind of season in use, and a new game chosen at the start (SX.14) -----

    def use_kind(self, kind: str) -> bool:
        """Put the franchise or the classic season in use before the season is loaded (the start-up menu's choice). False when there is no
        franchise to put in use. Nothing is parked: no season has been loaded yet."""
        if self.mode.kind == kind:
            return True
        from ..extras.franchise import mode as franchise_mode
        from ..extras.nfl_rules import is_nfl
        g = self.g
        if kind == "franchise":
            store = g.franchise()
            if not (store.opened and store.available and store.exists):
                return False
            franchise_mode.set_kind(g, "franchise")
            franchise_mode.activate(self, store)
        else:
            franchise_mode.deactivate(self)
            if is_nfl(g.rules):
                franchise_mode.set_kind(g, "classic")
        debuglog.event("app", "kind_in_use", kind=self.mode.kind)
        return True

    def begin_new_game(self) -> None:
        """The new game the start-up menu chose (NX-S7): a new season (with the last coach and team as the default) or a new franchise.
        What it replaces was already asked about and is in the backup."""
        kind, self.new_game = self.new_game, None
        defaults, self.new_defaults = self.new_defaults, None
        self.use_kind("classic")
        if kind == "franchise":
            from ..extras.franchise import mode as franchise_mode
            self.g.rnd.mark("season_start", kind="franchise")
            franchise_mode.to_franchise(self, new=True)
            return
        self.new_season(None, ask=False, defaults=defaults)

    # ----- the season set-up (0x487e25 to 0x4882de) -----

    def season_setup(self) -> None:
        self._stop_intro(reason="before_first_prompt")           # S8.2 safety: no loop plays while the set-up waits for the player
        if self.new_game is not None:                           # SX.14: a new game was chosen at the start
            self.begin_new_game()
            return
        self.mode.season_setup()                                # 0x488018 to 0x4882f1: footbal1.dat, else a new season

    def new_season(self, coach: str | None = None, ask: bool = True, defaults: tuple | None = None) -> None:
        """A new season: the coach, the team, the schedule, week 1 (GetCoach 0x488234, ChooseTeam 0x48825d, makes 0x488278,
        gtp = 1 and football.gtp 0x4882b2 to 0x4882de); the code is `ClassicSeason.new_season` (H15). `coach` and `ask` are
        the N. F. L. rules' question of NFL_FRANCHISE_DESIGN 3.2 (ignored with Rules = Classic). `defaults`: SX.14, NX-S7."""
        self.g.rnd.mark("season_start", kind=self.mode.kind)         # the debug log: the generator and its draws so far (7.11)
        if defaults is None:
            self.mode.new_season(coach, ask)
        else:
            self.mode.new_season(coach, ask, defaults)
        debuglog.event("app", "season_made", kind=self.mode.kind, week=self.season.gtp, team=self.season.tn1)

    def request_switch(self, target: str | None = None) -> None:
        """A menu (F9, the Rules) asked for another kind of season: the main menu ends its wait and the week loop switches."""
        self.switch_requested = True
        self.switch_target = target

    def rules_changed(self) -> None:
        """The Rules setting changed: if it makes the other kind of season the one in use, ask for the switch."""
        from ..extras.franchise import mode as franchise_mode
        if franchise_mode.desired_kind(self) != self.mode.kind and not franchise_mode.franchise_unusable(self.g):
            self.switch_requested = True

    # ----- the week loop (label L_4882f7) -----

    def week_loop(self) -> None:
        """Runs until the program ends (menu choice 4, or Save Game: `ending` says which)."""
        while True:
            self.mode.switch_if_needed()                        # H15: a kind of season asked for in a menu (Classic: never)
            self.week_announcement()
            choice = self.main_menu()
            if choice == 0:                                     # H15: the menu ended its wait for a switch (B-X48)
                continue
            if choice == 4:                                     # 0x489d96 If L34 = 4 Then GoTo L_48a054
                self.ending = "exit"
                return
            if choice == 1:
                if self.play_and_after():                       # the original leaves for the exit here (0x48a042)
                    return
            elif choice == 2:
                self.g.say_schedule()                           # 0x48a8df
            else:
                self.g.say_stand()                              # 0x48a930

    def week_announcement(self) -> None:
        """Reads the week and says where the season stands: the week line (or the play-off week line), the log, the
        opponent, the records, today's game (0x488314 to 0x489845)."""
        g, season, keys = self.g, self.season, self.keys
        g.speak_notices()                                       # S7.5: a file that could not be written, said once
        if self.beds_stopped and self.sounds is not None:       # G-A5: the beds start again, as at the start of the program
            self.sounds.start_crowds()
        self.beds_stopped = False
        debuglog.event("app", "week", week=season.gtp, kind=self.mode.kind, saved_game=self.saved_game or None)
        if not self.log_open:                                   # 0x48836a to 0x488454: once per run
            self.log_open = True
            fresh = not self.saved_game and season.gtp == 1     # 0x48843a: Output with the title line, else Append
            self.store.open_log(fresh)
            if fresh:
                g.log_print(texts.CAPTION)                      # 0x488422: the clone's title replaces the original's
            g.log_print("")                                     # 0x48842f, 0x488454
        if not season.in_playoffs:
            self._regular_week_line()
        else:
            self._playoff_week_line()
        self.today_text = self.todays_game()                    # 0x4891a9 to 0x489800
        g.log_print("")                                         # 0x48981b
        g.log_print(self.today_text)                            # 0x48982b
        g.log_print("")                                         # 0x489845

    def _regular_week_line(self) -> None:
        g, season = self.g, self.season
        line = P.THIS_IS_WEEK + str_(season.gtp) + P.OF_FOOTBALL     # 0x488493 to 0x4884e8
        g.say2(line)                                            # 0x4884f4
        self.week_intro = line                                  # Q5 not reproduced: F1 in the menu says it again
        g.log_print(P.THIS_IS_WEEK_LOG + trim(str_(season.gtp)) + P.OF_FOOTBALL)   # 0x4885c8 Print #3
        self._stop_intro()                                      # 0x488609 L68 test, 0x488618 Stop, 0x488636, 0x488671, 0x488694
        g.voice_speak(" ", wait=True)                           # 0x4886f2 Voice.Speak " ", 0
        season.set_week_opponent()                              # 0x488772 to 0x488822: footbal2.dat, the gtp-th record
        self.week_text = ""                                     # L118: never set in a regular week (a fresh run: "")

    def _playoff_week_line(self) -> None:
        g, season = self.g, self.season
        g.say2(P.THIS_IS_THE)                                   # 0x488884
        self.week_intro = P.THIS_IS_THE                         # Q5 not reproduced: F1 in the menu says it again
        self._stop_intro()                                      # 0x4888c8 L68 test, 0x4888dd Stop, 0x4888f7, 0x48892c, 0x48894f
        g.voice_speak(" ", wait=True)                           # 0x4889a9 Voice.Speak " ", 0
        name = " " + T.PLAYOFF_WEEK_NAMES.get(season.classic_gtp(), "")   # 0x488960, 0x488ad0: " " & the week's name
        g.log_print("")                                         # 0x488adf
        g.log_print("#" + trim(str_(season.classic_gtp())))     # 0x488b7d (16 + the week of the play-offs)
        g.log_print(name)                                       # 0x488b8d
        g.log_print("")                                         # 0x488b96
        self.week_text = name + P.OF_FOOTBALL              # 0x488bb7, 0x488bc5 (L118)
        season.set_playoff_opponent()                           # 0x488bde to 0x488d6a: footbal4.dat

    def todays_game(self) -> str:
        """" Today's game is <A><wins> and <losses> verses the <B><wins> and <losses>": A is the opponent when vtrnt = 1 (the
        player's team is the home team), else the player's team (0x4891a9 to 0x489800)."""
        g, season = self.g, self.season

        def record(division: int, place: int) -> tuple[str, int, int]:
            wins, losses = season.records.record(division, place)
            return g.league.team(division, place), wins, losses

        if season.on_bye:                                       # SZ.8: a bye week of the real calendar has no opponent and no game
            from ..extras import nx_texts as X
            return X.text("NXC-23")
        own = record(season.tn1, season.tn2)
        opponent = record(season.tn3, season.tn4)
        first, second = (opponent, own) if season.vtrnt == 1 else (own, opponent)
        return (P.TODAYS_GAME_IS + first[0] + str_(first[1]) + P.AND + str_(first[2]) + T.VERSES_THE
                + second[0] + str_(second[1]) + P.AND + str_(second[2]))

    # ----- the main menu (0x489857 to 0x489d6c) -----

    def menu_digit(self) -> int:
        """Val(g2) as the main menu tests it ("1" to "4"); the keypad's 1 to 4 count too (Q32 not reproduced, D-027). Any other
        key, the keypad's 0 and 5 to 9 included, is "any other key" (0x489c69 to 0x489d2a test only "1" to "4")."""
        code = self.keys.code_text
        if code.isdigit() and 97 <= int(code) <= 100:
            return int(code) - 96
        char = self.keys.char
        return int(char) if len(char) == 1 and char in "1234" else 0

    def choice_text(self, choice: int) -> str:
        """The main menu's choice as it is spoken: the original's four, except that in the bye week of a calendar (SZ.8) the first one does not offer a
        game: it plays the week of the other teams."""
        if choice == 1 and self.season.on_bye:
            from ..extras import nx_texts as X
            return X.text("NXC-22")
        return P.CHOICES[choice]

    def main_menu(self) -> int:
        """Returns the choice 1 to 4 (L34). A saved game takes choice 1 after the two lines (0x4898fb)."""
        g, keys, season = self.g, self.keys, self.season
        while True:                                             # L_489857: L34 = 1
            choice = 1                                          # 0x489874
            repeat = True
            whole = False                                       # Q5: F1 repeats the whole announcement, the week line first
            while repeat:                                       # L_489876
                repeat = False
                if whole and self.week_intro != "":             # Q5 / D-025 (a), not reproduced: the original repeats no week line
                    g.say2(self.week_intro)
                if self.week_text != "":                        # 0x489888
                    g.say2(self.week_text)                      # 0x489896
                g.say2(self.today_text)                         # 0x4898b8
                if self.saved_game:                             # 0x4898fb
                    return 1
                self.mode.before_menu()                         # H15: the franchise's news and to-do list (Classic: nothing)
                g.say2(" " + season.coach + P.SELECT)           # 0x489935, 0x489951
                while True:                                     # L_489969
                    g.say2(self.choice_text(choice))            # 0x4899c0, 0x489a1b, 0x489a76, 0x489aca
                    keys.getkey(g.speech)                       # 0x489af1
                    if self.mode.switch_pending():              # H15, B-X48: a menu asked for another kind of season
                        return 0
                    code = keys.code_text
                    if code == KEY_ENTER:                       # 0x489b1a
                        debuglog.event("app", "main_menu_choice", choice=choice, week=season.gtp)
                        return choice
                    if code == KEY_UP:                          # 0x489b31
                        choice = choice - 1 or MENU_CHOICES
                        continue
                    if code == KEY_DOWN:                        # 0x489bcd
                        choice = choice + 1 if choice < MENU_CHOICES else 1
                        continue
                    digit = self.menu_digit()                   # 0x489c69 to 0x489d2a
                    if digit:
                        choice = digit
                        continue
                    if code == KEY_F1:                          # 0x489d42: again from the top, the choice kept
                        repeat = whole = True
                        break
                    g.saykey()                                  # 0x489d4b, then L_489857: the choice starts at 1 again
                    break

    # ----- choice 1: the game and what follows (0x489d96 to 0x48a042) -----

    def play_and_after(self) -> bool:
        """pag, then the season engine and the standings; returns True when the program ends (Save Game). The original
        leaves for its exit after any game; the clone goes back to the week loop (D-024 item 1)."""
        g, season, store = self.g, self.season, self.store
        self.mode.before_game()                                 # H15: the to-do list's deadline (Classic: nothing)
        if season.on_bye:                                       # SZ.8: the player's team has its bye: no game, the other teams play
            return self.play_bye_week()
        # pag read football.sav and deleted it (0x43afa4); the clone keeps it until the game it holds ends (NX-S3, rule 0.23), so a crash
        # or a closed window after the load loses nothing
        entry = self.load_entry if self.saved_game else None
        saved = entry.saved if entry is not None else None
        self.slot_in_use = entry.slot if entry is not None and not entry.is_auto else None
        self.load_entry = None
        if entry is not None:
            debuglog.event("save", "load", file=entry.name, auto=entry.is_auto, resume=bool(getattr(saved, "resume", None)))
        self.saved_game = False                                 # SavedGame = 0 when the game is loaded (0x43bb41)
        own_names = store.player_names()                        # footplay.txt read (pag 0x4544e1), repaired when it has a problem
        g.speak_notices()                                       # S7.5: a damaged footplay.txt, said before the game
        rules = None                                            # the program's rules; a save of the N. F. L. rules may ask
        if getattr(saved, "extras_marked", False):              # (nfl4 only, rule 0.13, SX.2: NFL_EXTRAS_DESIGN 12.3)
            from ..extras.saved import rules_for_saved_game
            rules = rules_for_saved_game(g, saved)              # (a window closed at the question loses nothing: the file is still there)
        arguments = self.mode.game_arguments()                  # H15 (nfl4 only): the Franchise's opponent and quarterbacks
        plan_rules = arguments.pop("rules", None)               # and, when the player took it, the staff's game plan (SX.8e)
        if rules is None:
            rules = plan_rules
        g.rnd.mark("game_start", week=season.gtp, rules=getattr(rules or g.rules, "name", None) or None,
                   resumed_save=saved is not None or None, tn1=season.tn1, tn2=season.tn2, tn3=season.tn3, tn4=season.tn4,
                   vtrnt=season.vtrnt)
        week = season.gtp                                       # the week this game belongs to: its saves end with it
        with debuglog.context("game week %s" % season.gtp):
            result = g.play_game(rules=rules, own_names=own_names, saved=saved, save_sink=store.save_game,
                                 roster_sink=store.write_player_names,   # 0x489ddb
                                 autosave_sink=store.autosave if self.menu_on else None, save_ui=self.save_ui,
                                 **arguments)
        debuglog.event("app", "game_end", week=season.gtp, scores=getattr(result, "scores", None), saved=result.saved or None,
                       draws=g.rnd.draws)
        if not result.saved:                                    # the game was played out or conceded: its saves have done their work
            self.game_over(week, entry)
        if result.saved:                                        # 0x489e2c: SavedGame = 1 skips pog and the standings
            self.saved_game = True
            self.ending = "saved"
            return True
        self.beds_stopped = True                                # pag stopped both crowd beds at its end (G-A5)
        if self.sounds is not None:
            self.sounds.crwd1 = -1200                           # 0x489e52
        if season.gtp != 0:                                     # 0x489e7f: pag sets 0 after a Super Bowl game
            g.pog()                                             # 0x489e88
            g.ptf = 0                                           # 0x489ec0
            self.after_game_standings()
            self.mode.after_week()                              # H15: the franchise's news (Classic: nothing)
        if season.gtp == 0:
            self.season_over()
        return False

    def play_bye_week(self) -> bool:
        """The bye week of the real calendar (nfl4's Franchise, SZ.8): the same steps as after a game, without a game. The week's other games are told,
        the records and the week counter go on, the standings follow, the Franchise prepares its next week. Never ends the program (False)."""
        g, season = self.g, self.season
        week = season.gtp
        debuglog.event("app", "bye_week", week=week, team=season.tn1)
        g.rnd.mark("bye_week", week=week, tn1=season.tn1, tn2=season.tn2)
        self.saved_game = False
        self.load_entry = None
        g.pog_bye()
        g.ptf = 0
        self.after_game_standings()
        self.mode.after_week()
        if season.gtp == 0:
            self.season_over()
        return False

    def game_over(self, week: int, loaded) -> None:
        """NX-S3: a game that ended (played out or conceded) retires its saves: the automatic save goes, and the saves of this week (the
        one it was loaded from too) move to the backup, three deep, and are never offered again. Said in one sentence when a saved game
        moved. Nothing a crash or a closed window leaves behind is touched: this runs only when the game really ended."""
        shelf = self.store.shelf
        entries = shelf.scan(None)
        targets = [entry for entry in entries
                   if entry.is_auto or entry.info.get("week") == week or (loaded is not None and entry.name == loaded.name)]
        moved = shelf.retire(targets, "the game of week %s ended" % week)
        if moved:
            self.g.say2(save_texts.GAME_OVER_SAVES_MOVED)
        self.slot_in_use = None

    def after_game_standings(self) -> None:
        """The standings after the games of the week: clk, SayStand, wait while the voice speaks and no key came, stop,
        a key when none came; F1 says them again (0x489ec5 to 0x48a012). The wait is only for standings that were spoken
        (Q53 not reproduced: the original's key press after silent standings, GAP_REGISTER G-F2)."""
        g, keys = self.g, self.keys
        while True:
            keys.clk()                                          # 0x489ec5
            if not g.say_stand():                               # 0x489ee0: nothing spoken (gtp 0 or 18 to 20): no wait
                return
            keys.wait_speech(g.speech)                          # L_489ef8 to 0x489fb4
            g.stopspeech()                                      # 0x489fbd
            if keys.code_text == "":                            # 0x489fe8
                keys.getkey(g.speech)                           # 0x489fed
            if keys.code_text != KEY_F1:                        # 0x48a012
                return

    def season_over(self) -> None:
        """gtp is 0: the season files go, the clone says so and runs the set-up of a new season (G-F3); the code is
        `ClassicSeason.season_over` (H15); a franchise runs its offseason instead."""
        self.mode.season_over()

    # ----- the exit (0x48a054 to 0x48aad2) -----

    def exit_program(self) -> None:
        g, sounds = self.g, self.sounds
        if self.season.gtp == 0:                                # 0x48a09d: the season is over
            self.store.delete_season_files()                    # 0x48a0ec to 0x48a511
        if sounds is not None:
            sounds.play(0, 0)                                   # 0x48a54f play("0", 0): foot0, waited
        g.say(texts.THANK_YOU)                                  # 0x48a59a (waited)
        if sounds is not None:
            sounds.stop_all()                                   # 0x48a5ed to 0x48a775: the DirectSound objects are released
        # the original's "gamemenu.exe not found" branch (two Beeps, the sentence, 0x48a80f to 0x48a9ce) is not run (D-100)
        log.info("exit: the thank-you is said, the program ends (no menu-program sentence, D-100)")
