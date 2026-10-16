"""The Franchise as a kind of season: the mode object, the switches, the question at a new season and a new franchise (nfl4 only,
rule 0.13). This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 3 and 13 (H15). The program has one `Program.mode`; `ClassicSeason` (game/season_mode.py) is the original's
season frame, `FranchiseSeason` here is the league that lasts. A switch (design 3.1) changes five things together and nothing
else: the program's three stores (`Program.store`, `Game.season_store`, `Game.setup_store`), H14's hooks, the mode, what the
Game's one `SeasonState` holds, and `Program.saved_game` (asked again of the new store). The classic season is parked in
memory while the franchise is in use (its files are never written by the franchise); the franchise waits in its folder.
"""
from __future__ import annotations

import copy
import logging
import time

from ...game.season import DEFAULT_COACH, SeasonState
from ...game.season_engine import CLASSIC_SEASON_HOOKS, ClassicSeasonHooks
from ...game.season_mode import ClassicSeason, SeasonMode
from .. import nx_texts as X
from ..nfl_rules import is_nfl
from . import data as D
from . import history, weekly
from .league import SEASON, new_league, team_index, team_ref
from .question import FranchiseQuestion, ask_yes_no
from .strength import LeaguePlace

log = logging.getLogger("nfl4.game")


class FranchiseHooks(ClassicSeasonHooks):
    """H14 for the franchise: every result of the engine goes into the league record (design 9.1), and the computer's games lean
    by the team's place in its league (design 5.2: the score index of a regular week, the play-off coin)."""

    def __init__(self, store):
        self.store = store
        self._sums = None
        self._place = None

    def game_played(self, stage, week, winner, loser, winner_score, loser_score) -> None:
        league = self.store.league
        if league is None or league.stage != SEASON:
            return
        league.results.append([D.STAGE_CODE[stage], week, team_index(winner.division, winner.place),
                               team_index(loser.division, loser.place), winner_score, loser_score])

    def place(self) -> LeaguePlace | None:
        """The league's 32 sums of this season (kept at the start of the season), or None when there are none: no shift."""
        league = self.store.league
        if league is None or league.stage != SEASON or len(league.sums) != D.TEAMS:
            return None
        if self._place is None or self._sums != league.sums:
            self._sums = list(league.sums)
            self._place = LeaguePlace(self._sums)
        return self._place

    def computer_index(self, team, index: int) -> int:
        place = self.place()
        return index if place is None else place.index(team_index(team.division, team.place), index)

    def playoff_first_wins(self, rnd, visitor, home) -> bool:
        place = self.place()
        if place is None:
            return rnd(2) == 1
        return rnd.chance_first(place.playoff_per_mille(team_index(visitor.division, visitor.place),
                                                        team_index(home.division, home.place)))


class FranchiseSeason(SeasonMode):
    kind = "franchise"

    def choose_at_start(self) -> None:
        return None

    def season_setup(self) -> None:
        resume(self.p)

    def new_season(self, coach: str | None = None, ask: bool = True) -> None:
        """Not reached in normal play (a franchise goes from its offseason into its next season by itself); a franchise whose
        season cannot be loaded hands over to a classic season."""
        to_classic(self.p, announce=False)

    def before_menu(self) -> None:
        """Design 3.4: week 1 NXF-08, the news of the week that was played, the to-do list, once a week (the told mark of the
        record, so a restart or F1 does not say them again)."""
        weekly.before_menu(self.p)

    def before_game(self) -> None:
        """The to-do list's deadline, the kick-off (design 8.1)."""
        weekly.before_game(self.p)

    def game_arguments(self) -> dict:
        """The opponent is a team of the league with its own players and ratings, and both quarterbacks are players of the league,
        so Getqbs asks nothing and no name is drawn (design 5.1, 13: H7 extended)."""
        p = self.p
        league = p.store.league
        if league is None or league.stage != SEASON:
            return {}
        opponent = league.roster_for_game(team_index(p.season.tn3, p.season.tn4))
        own_quarterback = league.roster_for_game(league.team).quarterback
        names = (own_quarterback, opponent.quarterback)
        arguments = {"opponent_names": opponent, "quarterback_names": lambda state: names}
        rules = weekly.game_rules(p)                      # the staff's game plan, when the player took it (design 8.1 T2)
        if rules is not None:
            arguments["rules"] = rules
        return arguments

    def season_over(self) -> None:
        from . import offseason
        offseason.run(self.p)


def say_team_rating(g, league) -> None:
    """NXF-09: the player's team's rating and its number among the 32 (a new league and the start of every season)."""
    g.say2(history.team_rating_text(league))


# ----- which kind of season, and the store swap -----

def desired_kind(p) -> str:
    """The kind the settings ask for: the franchise only with the N. F. L. rules and nx_season_kind = franchise (design 3.1).
    A menu that asks for a franchise that does not exist yet (F9, start a franchise now) names its target in
    `Program.switch_target`, so the setting is not changed before the league is made (review finding 9)."""
    g = p.g
    if not is_nfl(g.rules):
        return "classic"
    if p.switch_target is not None:
        return p.switch_target
    return "franchise" if g.options.settings.game.nx_season_kind == "franchise" else "classic"


def franchise_unusable(g) -> bool:
    """The franchise folder was opened and cannot be used this run (held by another program, saved by a newer version)."""
    store = g._franchise_store
    return store is not None and store.opened and not store.available


def set_kind(g, kind: str) -> None:
    settings = g.options.settings.game
    if settings.nx_season_kind != kind:
        settings.nx_season_kind = kind
        g.options.save()


def _settle_open(g, store) -> None:
    """After `open`: a franchise that could not be used sets the kind back to classic (design 10.1)."""
    if store.force_classic:
        set_kind(g, "classic")


def activate(p, store) -> None:
    """The stores, the hooks and the mode of the franchise (design 3.1); the classic stores are kept to come back to."""
    g = p.g
    p.classic_stores = (p.store, g.season_store, g.setup_store)
    store.bind(g.season)
    store.words = history.Words(lambda team: g.league.team(*team_ref(team)))
    p.store = g.season_store = g.setup_store = store
    g.season_hooks = FranchiseHooks(store)
    p.mode = FranchiseSeason(p)


def deactivate(p) -> None:
    g = p.g
    store = p.store
    if hasattr(store, "unbind"):
        store.unbind()
    p.store, g.season_store, g.setup_store = p.classic_stores
    p.classic_stores = None
    g.season_hooks = CLASSIC_SEASON_HOOKS
    p.mode = ClassicSeason(p)


def restore_state(dst: SeasonState, src: SeasonState) -> None:
    """The parked classic season goes back into the Game's SeasonState (in place: the records and the play-off lists keep
    their objects, as the classic store's load_season does)."""
    dst.coach, dst.tn1, dst.tn2, dst.tn3, dst.tn4 = src.coach, src.tn1, src.tn2, src.tn3, src.tn4
    dst.vtrnt, dst.gtp = src.vtrnt, src.gtp
    dst.schedule = list(src.schedule)
    for d in range(len(dst.records.wins)):
        dst.records.wins[d][:] = src.records.wins[d]
        dst.records.losses[d][:] = src.records.losses[d]
    dst.playoffs.pairings[:] = src.playoffs.pairings
    dst.playoffs.byes[:] = src.playoffs.byes


# ----- the start -----

def choose_at_start(p) -> None:
    """With the N. F. L. rules: open the franchise folder (the question needs to know whether a franchise exists) and, when the
    kind is franchise and the file loads, put the franchise in use before the saved game is asked about (design 3.1)."""
    g = p.g
    want = g.options.settings.game.nx_season_kind == "franchise"
    store = g.franchise()
    store.open(want)
    _settle_open(g, store)
    if want and store.exists and store.available and not store.force_classic:
        activate(p, store)


# ----- the question at a new season (design 3.2) -----

def ask_kind(p, coach: str | None) -> bool:
    """The question at a new season with the N. F. L. rules. True when a franchise was chosen and is set up (the caller has
    nothing left to do); False for a classic season (the original's prompts follow)."""
    g = p.g
    store = g.franchise()
    store.open(g.options.settings.game.nx_season_kind == "franchise")
    _settle_open(g, store)
    g.speak_notices()
    if not store.available:
        return False
    situation = X.text("NXF-01", coach=coach or DEFAULT_COACH)
    while True:
        exists = store.exists
        team = g.league.team(*team_ref(store.league.team)) if exists else ""
        items = [X.text("NXF-A01")]
        items += [X.text("NXF-A03", team=team), X.text("NXF-A04")] if exists else [X.text("NXF-A02")]
        answer = FranchiseQuestion(g, situation, items).ask()
        if answer == 0:
            set_kind(g, "classic")
            return False
        if exists and answer == 1:
            set_kind(g, "franchise")
            to_franchise(p, new=False)
            return True
        if exists and not ask_yes_no(g, X.text("NXF-02", team=team), start_yes=False):
            continue
        to_franchise(p, new=True)
        return True


# ----- the switches (design 3.1, 3.5) -----

def switch(p) -> None:
    """The week loop's switch: the kind the settings ask for becomes the kind in use. It goes on until it is: an offseason
    that was resumed may itself end with another switch asked in F9 (review finding 5)."""
    for _ in range(5):
        p.switch_requested = False
        g = p.g
        want = desired_kind(p)
        target, p.switch_target = p.switch_target, None
        if want == p.mode.kind:
            return
        if want == "franchise":
            store = g.franchise()
            store.open(True)
            store.force_classic = False              # the notice of the start was given; a franchise may be made now
            g.speak_notices()
            if not store.available:
                return
            to_franchise(p, new=not store.exists)
        else:
            to_classic(p, announce=is_nfl(g.rules))
        if not p.switch_requested:
            return


def to_franchise(p, new: bool, announce: bool = True) -> None:
    g = p.g
    store = g.franchise()
    g.parked_classic = copy.deepcopy(g.season) if p.mode.kind == "classic" and g.season.schedule else None
    activate(p, store)
    if new:
        start_new(p)
        return
    if announce:
        g.say2(X.text("NXF-05", team=g.league.team(*team_ref(store.league.team))))
    p.saved_game = store.has_saved_game()
    resume(p)


def to_classic(p, announce: bool) -> None:
    g = p.g
    deactivate(p)
    if announce:
        g.say2(X.text("NXF-06"))
    parked, g.parked_classic = g.parked_classic, None
    loaded = False
    if parked is not None:
        restore_state(g.season, parked)
        loaded = True
    else:
        g.season.reset_for_new_season()
        loaded = p.store.load_season(g.season)
    p.saved_game = p.store.has_saved_game()
    if not loaded:                                    # no classic season to go on with: the original's prompts, no question
        g.season.reset_for_new_season()
        p.mode.new_season(None, ask=False)


def resume(p) -> None:
    """The franchise is in use: continue its offseason where the file says, then load its season."""
    from . import offseason
    store = p.store
    if store.league.stage == SEASON:                     # the season first: the offseason of a season that ended reads its values
        store.load_season(p.season)
        if not p.season.schedule:                        # a window closed between the league and its first schedule
            p.g.make_schedule()
            p.season.gtp = 1
            store.write_gtp(1)
        resume_playoffs(p)
    if store.league.stage != SEASON or p.season.gtp == 0:    # gtp 0: the season ended and its offseason has not begun
        offseason.run(p)


def resume_playoffs(p) -> None:
    """The record is saved only at whole states of the play-offs (store.engine_consistent): a round the player is in, or a round
    played without him that has to be played again from its pairings. A player who is out of the play-offs, or who had a bye in the
    wild card round, is not in the coming round's games: the engine plays the rest, as it does in the original's own flow (review
    finding 1 of SX.8a)."""
    g, season = p.g, p.season
    if season.gtp < 17:
        return
    own, playoffs = season.own_team, season.playoffs
    if playoffs.contains_player(own):
        return
    if own in playoffs.byes and season.gtp == 17:
        g.season_engine._wild_card_games_without_the_player()
        return
    g.finplay17()

# ----- a new franchise (design 3.2) -----

def new_league_id(g) -> str:
    return time.strftime("%Y%m%d-%H%M%S")


def own_names(g):
    """The names of the player's first team: footplay.txt when the classic store reads it as complete, else
    footplay.previous.txt (the classic store keeps the file under that name when a classic season ends)."""
    classic = g.program_store
    current = getattr(classic, "current_player_names", None) or classic.player_names      # reading only, nothing repaired
    for read in (current, getattr(classic, "previous_player_names", None)):
        if read is None:
            continue
        try:
            roster = read()
        except Exception:
            log.exception("the player's names could not be read for the new league")
            roster = None
        if roster is not None and roster.is_complete():
            return roster
    return None


def start_new(p) -> None:
    """GetCoach and ChooseTeam (the original's prompts), the league, makes, week 1."""
    g = p.g
    store = p.store
    season = g.season
    season.reset_for_new_season()
    g.season_engine.player_won = False
    p.saved_game = False
    store.creating = True
    g.get_coach()
    g.choose_team()
    team = team_index(season.tn1, season.tn2)
    league = new_league(g.rnd, list(g.pool.original), season.coach, team, new_league_id(g), own_names(g))
    store.create(league)
    set_kind(g, "franchise")                             # only now: a window closed before this leaves no franchise to look for
    g.say2(X.text("NXF-07"))
    say_team_rating(g, store.league)
    g.make_schedule()
    season.gtp = 1
    store.write_gtp(1)
