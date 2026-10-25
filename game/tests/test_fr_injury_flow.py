"""Injuries of the Franchise in the game and in the program (nfl4 only, rule 0.13; NFL_EXTRA_FEATURES N6.8 INJ-1 to INJ-4, NFL_FRANCHISE_DESIGN 17 SX.8k,
D-071): whole games with the game's injuries (tests/nflrig.py's engine, both sides by the computer), INJ-1 by the random draws, and a franchise's weeks on
the program rig (tests/frrig.py: the report, the question before a game, the staff's setting, F9's injury report). The rules are test_fr_injuries.py.
"""
import random
from collections import Counter

import pytest
from drrig import SURNAMES
from frrig import (COACH_AND_TEAM, DOWN, ENTER, ESC, F1, F9, WANT_FRANCHISE, franchise_rig, quit_policy, run_until, spoken)
from nflrig import RecordingRules, SimEngine
from pagrig import make_rig

from nfl4.extras import nx_texts as X
from nfl4.extras import tuning as T
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import history
from nfl4.extras.franchise import injuries as I
from nfl4.extras.franchise import injury_flow as F
from nfl4.extras.franchise.league import new_league
from nfl4.extras.state import ExtrasRecord
from nfl4.game.rnd import GameRandom

TEAM, OPP = 5, 9
WORDS = history.Words(lambda team: "Team%d" % team)
GAME = [ENTER, ENTER, ENTER]


def league_at(week, seed=3):
    league = new_league(GameRandom(random.Random(seed)), SURNAMES, "Kim", TEAM, "20260101-000000")
    league.gtp = week
    return league


class Counting:
    """The game's random source, counting the draws the injuries make through it."""

    def __init__(self, rnd):
        self.rnd, self.sizes = rnd, []

    def below(self, n):
        self.sizes.append(n)
        return self.rnd.below(n)

    def __call__(self, n):
        self.sizes.append(n)
        return self.rnd(n)

    def redraw(self, *args):
        return self.rnd.redraw(*args)


class Rigged:
    """A scripted source: `below` and `rnd` answer from the script (then the lowest value)."""

    def __init__(self, script):
        self.script = list(script)

    def below(self, n):
        return min(self.script.pop(0), n - 1) if self.script else 0

    def __call__(self, n):
        return self.below(n) + 1

    def redraw(self, draw, ok, scan, what):
        value = draw()
        return value if ok(value) else scan()


def play(tmp_path, seed, league, week, component=True):
    """One whole game of the player's team (side 1) against OPP with the week's lineups; with `component` the game has its injuries (as a franchise
    game has them), without it the same rosters are handed in and nothing of the injuries is there."""
    rig = make_rig(tmp_path, rng=random.Random(seed), fast=True, vtrnt=2, gtp=week)
    rig.rnd.trace = []
    rules = RecordingRules(penalties_on=True, qb_on=True)
    own = F.lineup_roster(league, TEAM, week, False)
    opponent = F.lineup_roster(league, OPP, week, True)
    game = None
    names = lambda state: (own.quarterback, opponent.quarterback)      # noqa: E731
    if component:
        game = F.GameInjuries(league, TEAM, OPP, week, False, Counting(rig.game.rnd), SURNAMES, WORDS, say=lambda text, plain: rig.game.say2(text))
        names = game.quarterbacks
    engine = SimEngine(rig.game, rules, quarterback_names=names, own_names=own, opponent_names=opponent)
    rig.game.play_engine = engine
    rig.game.game_injuries = game
    try:
        engine.run()
    finally:
        rig.game.play_engine = None
        rig.game.game_injuries = None
    return rig, engine, game


def exposed(game, engine):
    """The plays that can hurt a player (INJ-3), counted from the engine's records by their kinds (not by the code under test)."""
    from nfl4.game import outcome as O
    kinds = (O.RUN, O.PASS_COMPLETE, O.SACK, O.KICKOFF_RETURN)
    return sum(1 for outcome in engine.outcomes if outcome.kind in kinds and outcome.then is None and not outcome.two_point_try)


# ----- a game: equal to today with nobody hurt, and the only new draws -----

def test_week_16_with_nobody_hurt_is_the_game_without_the_injuries_to_the_draw(tmp_path):
    league = league_at(16)
    rig_a, engine_a, game = play(tmp_path / "a", 7, league, 16)
    rig_b, engine_b, _ = play(tmp_path / "b", 7, league, 16, component=False)
    assert not game.exposed and rig_a.rnd.trace == rig_b.rnd.trace
    assert [(o.kind, o.offense, o.yards, o.carrier) for o in engine_a.outcomes] == [(o.kind, o.offense, o.yards, o.carrier) for o in engine_b.outcomes]


def test_the_only_new_draws_of_a_game_are_one_per_play_that_can_hurt(tmp_path, monkeypatch):
    monkeypatch.setattr(T, "FR_INJ_PLAY", 0)                     # every draw is made, none hurts
    league = league_at(3)
    rig_a, engine_a, game = play(tmp_path / "a", 11, league, 3)
    rig_b, engine_b, _ = play(tmp_path / "b", 11, league, 3, component=False)
    assert game.rnd.sizes == [10000] * exposed(game, engine_a) and exposed(game, engine_a) > 30     # one draw for each play that can hurt, none else
    assert game.record["hurt"] == []


def test_a_player_hurt_in_a_game_leaves_it_at_once_and_the_announcer_says_so(tmp_path, monkeypatch):
    monkeypatch.setattr(T, "FR_INJ_PLAY", 10000)                 # every play that can hurt does: the ball carrier is hurt
    monkeypatch.setattr(T, "FR_INJ_TACKLER", 0)
    league = league_at(3)
    seen = []
    real = F.GameInjuries.after_play

    def watch(self, state, outcome):
        found = self.exposed_places(outcome, state)
        if found is not None:
            side, place, _ = found
            seen.append((self.identity[side][place], frozenset(row[0] for row in self.record["hurt"])))
        real(self, state, outcome)
    monkeypatch.setattr(F.GameInjuries, "after_play", watch)
    rig, engine, game = play(tmp_path, 5, league, 3)
    hurt = [row[0] for row in game.record["hurt"]]
    assert hurt and len(set(hurt)) == len(hurt)
    for identity, before in seen:
        assert identity not in before                            # a player already hurt never carries the ball again
    text = " ".join(spoken(rig))
    announced = [X.TEXTS[i].split("<player>")[-1].strip()[:12] for i in X.REMARK_POOLS["IJX"]]
    assert any(piece in text for piece in announced)
    for side, team in ((1, TEAM), (2, OPP)):
        names = set(engine.s.rosters[side].names()) | {engine.s.quarterbacks[side]}
        assert not {league.players[pid].name for pid in hurt if league.players[pid].team == team} & names
        assert sum(1 for pid in hurt if league.players[pid].team == team) <= T.FR_INJ_TEAM_MAX
    if any(league.players[pid].pos == "QB" for pid in hurt):
        assert any(row[1] == "QB" for row in game.record["stand_ins"])


def test_the_games_injuries_join_the_league_with_their_week(tmp_path, monkeypatch):
    monkeypatch.setattr(T, "FR_INJ_PLAY", 2000)
    league = league_at(3)
    rig, engine, game = play(tmp_path, 9, league, 3)
    rows = [list(row) for row in game.record["hurt"]]
    assert rows
    game.commit()
    for pid, kind, games, offset in rows:
        row = I.row_of(league, pid)
        assert row is not None and row[1] == kind and row[2] == 3 and row[3] == 4 + games
    assert game.record["hurt"] == [] and I.check_injuries(league, _whole) is None


def test_a_tackler_hurt_on_a_play_is_a_player_of_the_defense(tmp_path, monkeypatch):
    monkeypatch.setattr(T, "FR_INJ_PLAY", 10000)
    monkeypatch.setattr(T, "FR_INJ_TACKLER", 100)                # every hit of a tackled play hurts the tackler
    league = league_at(3)
    rig, engine, game = play(tmp_path, 6, league, 3)
    positions = {league.players[row[0]].pos for row in game.record["hurt"]}
    assert positions and positions <= {"DL", "LB", "CB", "S", "RET"}       # the returners: a kick-off return hurts its returner


def test_the_tackler_hurt_is_the_defenses_man_named_first():
    from nfl4.game import outcome as O
    from nfl4.game.outcome import PlayOutcome
    league = league_at(3)
    script = [0, 0, 0, 0, 0, 0]                                  # the play's draw hits, the tackler, then IJA for 1 game, offset 0, the announcer's line
    rnd = Rigged(script)
    game = F.GameInjuries(league, TEAM, OPP, 3, False, rnd, SURNAMES, WORDS, say=lambda text, plain: None)

    class State:
        rosters = {1: league.roster_for_game(TEAM), 2: league.roster_for_game(OPP)}
        quarterbacks = {}
        extras = ExtrasRecord()
        defense = 2
    state = State()
    game.quarterbacks(state)
    game.after_play(state, PlayOutcome(O.RUN, 1, 1, 1, carrier=2, defender1=3))
    tackler = league.player_at(OPP, D.PLACES_OF["DL"][0] + 2)
    assert [row[0] for row in game.record["hurt"]] == [tackler.id]


def test_the_stand_ins_a_game_signs_join_the_league(tmp_path, monkeypatch):
    monkeypatch.setattr(T, "FR_INJ_PLAY", 10000)
    monkeypatch.setattr(T, "FR_INJ_TACKLER", 0)                  # the carriers are hurt: the quarterback on a sack or a run
    league = league_at(3)
    rig, engine, game = play(tmp_path, 5, league, 3)
    signed = [list(row) for row in game.record["stand_ins"]]
    assert any(row[1] == "QB" for row in signed)
    game.commit()
    assert all(I.stand_in(league, row[0], row[1]) == row for row in signed)


def test_a_saved_game_keeps_its_injuries_and_a_bad_record_is_refused():
    record = ExtrasRecord(injuries={"hurt": [[12, "IJA", 2, 1]], "stand_ins": [[5, "QB", "Smith", 55]]})
    again = ExtrasRecord.from_json(record.to_json())
    assert again.injuries == record.injuries
    assert "injuries" not in ExtrasRecord().to_json()           # every other game's record is as before
    for bad in ({"hurt": [[12, "IJA", 2]], "stand_ins": []}, {"hurt": [], "stand_ins": [[5, "QB", "", 55]]}, {"hurt": [], "x": []},
                {"hurt": [[12, "IJA", 0, 1]], "stand_ins": []}, {"hurt": [], "stand_ins": [[5, "QB", "Smith", 30]]}):
        with pytest.raises(ValueError):
            ExtrasRecord.from_json(ExtrasRecord(injuries=bad).to_json())


def test_two_tacklers_drawn_on_places_one_man_plays_become_two_men():
    league = league_at(3)
    lb = league.group_of(OPP, "LB")
    I.injure(league, lb[0].id, "IJA", 5, 0, 2)                 # out: his place (defense 7) is played by the next linebacker (defense 8)
    game = F.GameInjuries(league, TEAM, OPP, 3, False, GameRandom(random.Random(1)), SURNAMES, WORDS)

    class State:
        rosters = {1: league.roster_for_game(TEAM), 2: league.roster_for_game(OPP)}
        quarterbacks = {}
        extras = ExtrasRecord()
        defense, defender1, defender2 = 2, 7, 8
    state = State()
    game.quarterbacks(state)
    game.after_draws(state)
    ids = game.identity[2][D.PLACES_OF["DL"][0]:D.PLACES_OF["DL"][0] + 17]
    assert state.defender1 == 7 and state.defender2 != 7 and ids[state.defender2 - 1] != ids[6]
    state.defender1, state.defender2 = 1, 2                      # two men already: nothing changes
    game.after_draws(state)
    assert state.defender2 == 2


def test_the_snaps_hook_reaches_the_games_injuries_at_every_snap(tmp_path, monkeypatch):
    calls = []
    real = F.GameInjuries.after_draws

    def count(self, state):
        calls.append(state.defender2)
        return real(self, state)
    monkeypatch.setattr(F.GameInjuries, "after_draws", count)
    rig, engine, game = play(tmp_path, 3, league_at(16), 16)
    runs_and_passes = sum(1 for outcome in engine.outcomes if 1 <= outcome.offense_play <= 5)     # each drew its carrier and tacklers first
    assert len(calls) >= runs_and_passes > 50


def test_a_kick_off_return_hurts_the_returner_of_the_state_not_the_last_snaps_carrier():
    from nfl4.game import outcome as O
    from nfl4.game.outcome import PlayOutcome
    league = league_at(3)
    game = F.GameInjuries(league, TEAM, OPP, 3, False, GameRandom(random.Random(1)), SURNAMES, WORDS)

    class State:
        returner = 2
    record = PlayOutcome(O.KICKOFF_RETURN, 1, 0, 0, carrier=6)          # the last snap's ball carrier was 6
    assert game.exposed_places(record, State()) == (1, D.PLACES_OF["RET"][1], False)
    assert game.exposed_places(PlayOutcome(O.PASS_INCOMPLETE, 1, 3, 1), State()) is None
    assert game.exposed_places(PlayOutcome(O.RUN, 2, 1, 1, carrier=4), State()) == (2, D.PLACES_OF["RB"][3], True)
    assert game.exposed_places(PlayOutcome(O.RUN, 2, 9, 1, carrier=4, qb_run="keeper"), State()) == (2, D.PLACES_OF["QB"][0], True)


def test_a_loaded_games_injuries_are_used_only_when_the_league_would_take_them():
    """A saved game's injuries of the two teams come back; damaged ones (too many games, an offset out of its range, a stranger, a stand-in with a
    control character) are left out, so the league's own check never refuses the league after the game (the review of SX.8k)."""
    league = league_at(3)
    own_rb, opp_wr, stranger = league.player_at(TEAM, 0), league.player_at(OPP, 6), league.player_at(2, 0)
    record = {"hurt": [[own_rb.id, "IJA", 2, 1], [opp_wr.id, "IJB", 50, 0], [opp_wr.id, "IJB", 3, 9], [stranger.id, "IJA", 2, 0], [own_rb.id, "XXX", 2, 0]],
              "stand_ins": [[TEAM, "QB", "Fine", 55], [OPP, "QB", "Tab	name", 55], [3, "QB", "Other", 55]]}
    game = F.GameInjuries(league, TEAM, OPP, 3, False, GameRandom(random.Random(1)), SURNAMES, WORDS)

    class State:
        rosters = {1: league.roster_for_game(TEAM), 2: league.roster_for_game(OPP)}
        quarterbacks = {}
        extras = ExtrasRecord(injuries=record)
    state = State()
    game.quarterbacks(state)
    assert game.record["hurt"] == [[own_rb.id, "IJA", 2, 1]] and game.record["stand_ins"] == [[TEAM, "QB", "Fine", 55]]
    assert own_rb.id not in game.identity[1]
    game.commit()
    league.check() if league.schedule else I.check_injuries(league, _whole)


def test_the_result_of_the_players_game_brings_its_injuries_into_the_league(monkeypatch):
    from nfl4.extras.franchise.mode import FranchiseHooks
    from nfl4.extras.franchise.league import team_ref
    from nfl4.game.playoffs import TeamRef
    league = league_at(3)
    calls = []

    class Game:
        teams = (TEAM, OPP)

        def commit(self):
            calls.append(1)

    class Store:
        pass
    store = Store()
    store.league, store.game_injuries = league, Game()
    hooks = FranchiseHooks(store)
    hooks.game_played("regular", 3, TeamRef(*team_ref(1)), TeamRef(*team_ref(2)), 21, 7)      # a computer game: nothing
    assert calls == [] and store.game_injuries is not None
    hooks.game_played("regular", 3, TeamRef(*team_ref(OPP)), TeamRef(*team_ref(TEAM)), 21, 7)
    assert calls == [1] and store.game_injuries is None


def test_the_computers_games_lean_by_the_teams_as_their_injuries_leave_them():
    from nfl4.extras.franchise.mode import FranchiseHooks
    from nfl4.extras.franchise.strength import LeaguePlace
    league = league_at(3)
    qb = league.player_at(2, D.PLACES_OF["QB"][0])
    I.injure(league, qb.id, "IJA", 5, 0, 2)                     # hurt in week 2: out in week 3
    I.settle(league, 3, GameRandom(random.Random(1)), SURNAMES)

    class Store:
        pass
    store = Store()
    store.league = league
    place = FranchiseHooks(store).place()
    healthy = LeaguePlace(league.sums)
    assert place.d[1] < healthy.d[1] and place.d == LeaguePlace(league.sums, I.effective_sums(league, 3)).d


def test_the_players_game_is_left_out_of_the_weeks_game_draws():
    from nfl4.extras.franchise import weekly
    league = league_at(4)
    league.results = [[0, 3, 1, 2, 21, 7], [0, 3, OPP, TEAM, 24, 10], [0, 2, TEAM, 7, 3, 0]]
    assert weekly.played_teams(league, 3) == (OPP, TEAM) and weekly.played_teams(league, 2) == (TEAM, 7) and weekly.played_teams(league, 1) == ()


def test_the_kick_off_returns_two_tacklers_are_two_men(tmp_path, monkeypatch):
    from nfl4.extras.nfl_rules import NflRules
    league = league_at(3)
    for p in league.group_of(OPP, "LB")[:4] + league.group_of(TEAM, "LB")[:4]:
        I.injure(league, p.id, "IJA", 6, 0, 2)                 # out: their places are played by the fifth linebacker
    seen = []
    real = NflRules.second_tackler

    def watch(self, state, first, second):
        got = real(self, state, first, second)
        injuries = self.game_injuries()
        ids = injuries.identity[state.defense][D.PLACES_OF["DL"][0]:D.PLACES_OF["DL"][0] + 17]
        seen.append(ids[first - 1] != ids[got - 1])
        return got
    monkeypatch.setattr(NflRules, "second_tackler", watch)
    for seed in range(4):
        play(tmp_path / str(seed), seed, league, 16)
    assert seen and all(seen)


def test_the_rules_object_keeps_the_kick_off_returns_tacklers_two_men():
    from types import SimpleNamespace
    from nfl4.extras.nfl_rules import NflRules
    league = league_at(3)
    lb = league.group_of(OPP, "LB")
    I.injure(league, lb[0].id, "IJA", 5, 0, 2)                 # defense 7 is played by the man of defense 8
    game = F.GameInjuries(league, TEAM, OPP, 3, False, GameRandom(random.Random(1)), SURNAMES, WORDS)

    class State:
        rosters = {1: league.roster_for_game(TEAM), 2: league.roster_for_game(OPP)}
        quarterbacks = {}
        extras = ExtrasRecord()
        defense = 2
    state = State()
    game.quarterbacks(state)
    rules = NflRules()
    rules.game = SimpleNamespace(game_injuries=game)
    assert rules.second_tackler(state, 7, 8) not in (7, 8) and rules.second_tackler(state, 1, 2) == 2
    rules.game = SimpleNamespace(game_injuries=None)
    assert rules.second_tackler(state, 7, 8) == 8              # no franchise game: the original's draw stands


def test_f9_with_the_staff_setting_on_says_the_staff_decides_and_changes_nothing(tmp_path, monkeypatch):
    hurt_own_quarterback(monkeypatch)

    def staff_on(rig):
        rig.game.options.settings.game.nx_fr_auto = True
    to_report = [F9] + [DOWN] * 4 + [ENTER] + [DOWN] * 8 + [ENTER]
    rig = run(tmp_path, GAME + to_report + [ENTER, ESC, ESC, ESC], setup=staff_on)
    qb = own_qb(rig)
    assert X.text("NXI-55") in spoken(rig) and X.text("NXD-04", n=1) in spoken(rig)
    assert I.row_of(rig.fstore.league, qb.id)[6] == 2              # the staff's answer (play a questionable man) stands: Enter in F9 changed nothing


# ----- INJ-1: no injury outside a franchise, counted by the random draws -----

def _forbid(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("an injury rule was used outside a franchise")
    for name in ("after_games", "lineup", "draw_injury", "injure", "settle", "effective_sums"):
        monkeypatch.setattr(I, name, refuse)
    monkeypatch.setattr(F.GameInjuries, "after_play", refuse)
    monkeypatch.setattr(F.GameInjuries, "after_draws", refuse)


def test_a_quick_game_with_the_nfl_rules_draws_and_says_no_injury(tmp_path, monkeypatch):
    from nflrig import sim_game
    plain_rig = sim_game(tmp_path / "a", 4, trace=True)[0]
    _forbid(monkeypatch)
    rig = sim_game(tmp_path / "b", 4, trace=True)[0]
    assert rig.rnd.trace == plain_rig.rnd.trace and rig.game.game_injuries is None
    injury_words = [X.TEXTS[i].strip()[:20] for i in X.TEXTS if i.startswith(("NXI", "IJX"))]
    assert not any(word in line for line in spoken(rig) for word in injury_words)


@pytest.mark.parametrize("nfl", [False, True])
def test_a_classic_season_draws_says_and_stores_no_injury(tmp_path, monkeypatch, nfl):
    from frrig import WANT_CLASSIC
    keys = (WANT_CLASSIC if nfl else []) + COACH_AND_TEAM + GAME * 3

    def season(folder):
        rig = franchise_rig(folder, keys, policy=quit_policy, nfl=nfl)
        rig.game.rnd.trace = []                                  # the size of every draw of the run
        return run_until(rig)
    plain = season(tmp_path / "a")
    _forbid(monkeypatch)
    rig = season(tmp_path / "b")
    assert rig.game.rnd.trace == plain.game.rnd.trace and len(rig.game.rnd.trace) > 100
    assert spoken(rig) == spoken(plain) and rig.game.season.gtp == plain.game.season.gtp == 4
    assert X.text("NXI-01") not in spoken(rig) and (rig.fstore is None or rig.fstore.league is None)


def test_a_franchise_week_draws_the_injuries_and_a_classic_week_does_not(tmp_path, monkeypatch):
    counted = []
    real = I.after_games

    def count(league, week, rnd, surnames, played=()):
        counted.append(week)
        return real(league, week, rnd, surnames, played)
    monkeypatch.setattr(I, "after_games", count)
    run_until(franchise_rig(tmp_path / "f", WANT_FRANCHISE + COACH_AND_TEAM + GAME * 2 + [ENTER], policy=quit_policy))
    assert counted == [1, 2]
    from frrig import WANT_CLASSIC
    run_until(franchise_rig(tmp_path / "c", WANT_CLASSIC + COACH_AND_TEAM + GAME * 2 + [ENTER], policy=quit_policy))
    assert counted == [1, 2]


# ----- a franchise's week on the program rig -----

def _whole(value, low, high, what):
    from nfl4.extras.franchise.league import LeagueError
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise LeagueError("%s is %r" % (what, value))


def hurt_own_quarterback(monkeypatch, games=1):
    """The week's draws as they are, and the player's quarterback hurt in week 1 (questionable for week 2 with one game). No extra-work item in week 2,
    so the injury's question is the week's only item."""
    monkeypatch.setattr(T, "FR_EXTRA_WORK_WEEKS", ())
    real = I.after_games

    def draws(league, week, rnd, surnames, played=()):
        done = real(league, week, rnd, surnames, played)
        if week == 1:
            qb = league.player_at(league.team, D.PLACES_OF["QB"][0])
            qb.rating = qb.peak = 80                           # a starter whose stand-in (55) is far below him: the to-do list asks
            league.sums = [league.strength_sum(t) for t in range(1, D.TEAMS + 1)]
            I.injure(league, qb.id, "IJE", games, 0, 1)
            I.settle(league, 2, rnd, surnames)
        return done
    monkeypatch.setattr(I, "after_games", draws)


def run(tmp_path, keys, setup=None, **kwargs):
    rig = franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM + keys, policy=quit_policy, **kwargs)
    if setup is not None:
        setup(rig)
    return run_until(rig)


def own_qb(rig):
    league = rig.fstore.league
    return league.player_at(league.team, D.PLACES_OF["QB"][0])


def test_the_report_comes_after_the_news_and_before_the_to_do_list_once(tmp_path, monkeypatch):
    hurt_own_quarterback(monkeypatch)
    rig = run(tmp_path, GAME)                                    # week 2: the window closes at the item's question
    text = spoken(rig)
    report = text.index(X.text("NXI-01"))
    assert text.index(X.text("NXN-01")) < report
    qb = own_qb(rig)
    line = [t for t in text[report:] if qb.name in t and "questionable" in t]
    assert line and X.text("NXI-41", player=qb.name, position=WORDS.position("QB")) in text[report:]
    assert text.count(X.text("NXI-01")) == 1 and rig.fstore.league.injuries["report"]["told"] == 1


def test_the_question_before_a_game_play_him(tmp_path, monkeypatch):
    hurt_own_quarterback(monkeypatch)
    rig = run(tmp_path, GAME + [ENTER])                          # the staff's recommendation for a questionable player: play him
    qb = own_qb(rig)
    assert I.row_of(rig.fstore.league, qb.id)[6] == 2 and X.text("NXI-42", player=qb.name) in spoken(rig)


def test_an_injury_question_left_for_later_rests_him_at_the_kick_off(tmp_path, monkeypatch):
    hurt_own_quarterback(monkeypatch)
    later = [DOWN, DOWN, ENTER]
    rig = run(tmp_path, GAME + later + [ENTER] + later)          # later; play game: asked again at the deadline, later again: he rests
    qb = own_qb(rig)
    assert I.row_of(rig.fstore.league, qb.id)[6] == 0 and X.text("NXD-30") in spoken(rig)
    assert not I.plays(rig.fstore.league, qb, 2, staff=False)


def test_with_the_staff_setting_on_nothing_is_asked_and_the_staffs_rule_plays_at_the_kick_off(tmp_path, monkeypatch):
    hurt_own_quarterback(monkeypatch)

    def staff_on(rig):
        rig.game.options.settings.game.nx_fr_auto = True
    rig = run(tmp_path, GAME + [ENTER], setup=staff_on)
    qb = own_qb(rig)
    assert X.text("NXI-41", player=qb.name, position=WORDS.position("QB")) not in spoken(rig)
    assert I.row_of(rig.fstore.league, qb.id)[6] == 2             # the kick-off wrote the staff's rule: a questionable player plays


def test_f9_injury_report_lists_him_and_enter_changes_whether_he_plays(tmp_path, monkeypatch):
    hurt_own_quarterback(monkeypatch)
    to_report = [F9] + [DOWN] * 4 + [ENTER] + [DOWN] * 8 + [ENTER]      # F9, Franchise, injury report (the 9th item)
    rig = run(tmp_path, GAME + [DOWN, DOWN, ENTER] + to_report + [ENTER, ESC, ESC, ESC])          # the question: later; F9: Enter plays him
    qb = own_qb(rig)
    text = spoken(rig)
    assert any(qb.name in t and "questionable" in t for t in text) and X.text("NXI-42", player=qb.name) in text
    assert I.row_of(rig.fstore.league, qb.id)[6] == 2


def test_the_franchise_game_is_played_with_the_weeks_lineup(tmp_path, monkeypatch):
    hurt_own_quarterback(monkeypatch, games=4)                   # out: the stand-in plays
    rig = run(tmp_path, GAME + GAME)
    league = rig.fstore.league
    week2 = [play for play in rig.plays if play["gtp"] == 2][0]
    stand = I.stand_in(league, league.team, "QB")
    assert stand is not None and week2["own_names"].quarterback == stand[2] and week2["own_names"].ratings[("Quarterback:", 1)] == stand[3]
    assert week2["quarterback_names"](None)[0] == stand[2]
