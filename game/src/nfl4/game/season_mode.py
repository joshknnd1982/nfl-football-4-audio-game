"""The program's season frame as one mode object: H15 (nfl4 only, rule 0.13; NFL_FRANCHISE_DESIGN 13). This is inspired by Jim Kitchen.

`Program.mode` answers the moments of the program's flow where a Franchise must differ from the original: the start (which
kind of season is in use), the season set-up and a new season, the moment before the main menu and before a game, what
follows a week, the end of a season, and the switch between a classic season and a franchise. `ClassicSeason` is the code
the Program had before, moved here and not changed: with Rules = Classic nothing in this module reaches the Franchise, no
folder is opened and no word is added (P1). With the N. F. L. rules a classic season is the same season plus the question of
design 3.2 at a new season. The franchise's mode (`extras\\franchise\\mode.py` `FranchiseSeason`) takes the Program's place
through `switch`, and gives the same methods.

* `choose_at_start()`: which kind is in use, before the saved game is asked about;
* `season_setup()`, `new_season(coach, ask)`: a loaded season, else a new one (the question first, with the N. F. L. rules);
* `before_menu()`: inside the main menu, after today's game and before " <coach> select " (Classic: nothing);
* `before_game()`: when "play game" is chosen (Classic: nothing); `game_arguments()`: more arguments of `play_game` (Classic:
  none); `after_week()`: after pog and the standings (nothing);
* `season_over()`: gtp is 0; `switch_pending()`: a menu asked for a switch (the main menu goes back to the week loop at
  once, B-X48), `switch_if_needed()`: at the top of the week loop.
"""
from __future__ import annotations

from . import program_texts as P
from .season_engine import NULL_STORE


class SeasonMode:
    kind = ""

    def __init__(self, program):
        self.p = program

    def switch_pending(self) -> bool:
        """True when a menu asked for another kind of season: the main menu then ends its wait (B-X48). Always false while
        nothing can ask (Rules = Classic), so the menu is the original's."""
        return self.p.switch_requested

    def switch_if_needed(self) -> None:
        if not self.p.switch_requested:
            return
        from ..extras.franchise import mode as franchise_mode
        franchise_mode.switch(self.p)

    def before_menu(self) -> None:
        return None

    def before_game(self) -> None:
        return None

    def game_arguments(self) -> dict:
        """More arguments for `Game.play_game` (values only): the Franchise gives the opponent's team of the league and the two
        quarterbacks (H7, SX.8b). Classic: none, so the game is the original's (rosters drawn, Getqbs asked)."""
        return {}

    def after_week(self) -> None:
        return None


class ClassicSeason(SeasonMode):
    kind = "classic"

    # ----- the start -----

    def choose_at_start(self) -> None:
        """With the N. F. L. rules and a franchise as the kind of season, the franchise comes into use (design 3.1). With
        Rules = Classic nothing happens and nothing is opened (P1)."""
        if not self._nfl():
            return
        from ..extras.franchise import mode as franchise_mode
        franchise_mode.choose_at_start(self.p)

    def _nfl(self) -> bool:
        from ..extras.nfl_rules import is_nfl
        return is_nfl(self.p.g.rules)

    # ----- the season set-up (0x487e25 to 0x4882de) -----

    def season_setup(self) -> None:
        p = self.p
        if not p.store.load_season(p.season):                   # 0x488018 to 0x4882f1: footbal1.dat, else a new season
            p.new_season()

    def new_season(self, coach: str | None = None, ask: bool = True, defaults: tuple | None = None) -> None:
        """A new season: the coach, the team, the schedule, week 1 (GetCoach 0x488234, ChooseTeam 0x48825d, makes 0x488278,
        gtp = 1 and football.gtp 0x4882b2 to 0x4882de). With the N. F. L. rules the question of design 3.2 comes first.
        `defaults` (SX.14, NX-S7): the coach and team of the season this one replaces; one yes or no question takes them, so a player
        who plays on as before presses Enter once instead of typing a name and choosing a team."""
        p = self.p
        g = p.g
        if ask and self._nfl():
            from ..extras.franchise import mode as franchise_mode
            if franchise_mode.ask_kind(p, coach):               # the player chose a franchise: its set-up is done
                return
        if not self._same_coach_and_team(defaults):
            g.coach_and_team()                                  # GetCoach, ChooseTeam (with the real names: the team, then the real coach)
        g.make_schedule()
        p.season.gtp = 1
        (g.season_store or NULL_STORE).write_gtp(1)

    def _same_coach_and_team(self, defaults: tuple | None) -> bool:
        """The start-up menu's new season (NX-S7): the last coach and team as the default. True when the player took them (the season
        state and footbal1.dat are then set as ChooseTeam sets them), False to run the original's prompts."""
        if not defaults or not defaults[0] or defaults[0] == "coach":
            return False
        from ..extras.franchise.question import ask_yes_no
        from . import save_texts
        coach, tn1, tn2 = defaults
        g = self.p.g
        if not ask_yes_no(g, save_texts.SAME_COACH_QUESTION % (coach, g.league.team(tn1, tn2).strip())):
            return False
        g.season.coach = coach
        g.season.tn1, g.season.tn2 = tn1, tn2
        from .prompts import NullSetupStore
        (g.setup_store or NullSetupStore()).write_coach_and_team(tn1, tn2, coach)
        return True

    # ----- the end of a season -----

    def season_over(self) -> None:
        """gtp is 0: the season files go (the original's exit deletes them, 0x48a09d to 0x48a511; footplay.txt is first kept
        as footplay.previous.txt by the store, G-F4), the game says so and runs the set-up of a new season (G-F3)."""
        p = self.p
        g = p.g
        coach = p.season.coach
        p.store.delete_season_files()
        g.say(P.SEASON_OVER)
        p.season.reset_for_new_season()
        g.season_engine.player_won = False
        p.new_season(coach)
