"""The schedule maker (`makes`). This is inspired by Jim Kitchen.

GAME_SPEC 5.1 (CODE (lifted) p_42fa70, every draw checked against the exe by `tools/vb6_rnd_check.py`), GAP_REGISTER G-D1
and G-D2. A scripted source plays the whole lifted procedure draw by draw: the rejected weeks, the duplicate team, the
full flag; a seeded source checks what must hold for every season.
"""
import random
from collections import Counter

from nfl4.game.league import DIVISIONS, PLACES
from nfl4.game.rnd import GameRandom
from nfl4.game.schedule import WEEKS, ScheduleEntry, make_schedule
from nfl4.game.season import SeasonState
from randsources import ScriptedRandom, StuckRandom, draws

# The player's team is division 1, place 1. Each pair is rnd(n) = k, in the order the lifted procedure draws them.
SCRIPT = draws(
    # the six division games: rivals 2, 3, 4, each with flag 1 then flag 2; the week is drawn until free and not 1 or 2
    # weeks from the week placed just before (the first draw is never week 1 or 2: last = 0)
    (16, 1), (16, 2), (16, 6),                        # place 2, flag 1: 1 and 2 refused, week 6
    (16, 5), (16, 8), (16, 6), (16, 9),               # place 2, flag 2: 5 and 8 too near 6, 6 taken, week 9
    (16, 10), (16, 11), (16, 3),                      # place 3, flag 1: 10 and 11 too near 9, week 3
    (16, 4), (16, 5), (16, 13),                       # place 3, flag 2: 4 and 5 too near 3, week 13
    (16, 12), (16, 15), (16, 1),                      # place 4, flag 1: 12 and 15 too near 13, week 1
    (16, 2), (16, 3), (16, 16),                       # place 4, flag 2: 2 too near 1, 3 taken, week 16
    # the ten free weeks 2, 4, 5, 7, 8, 10, 11, 12, 14, 15 in order: division, place, flag
    (8, 1), (8, 8), (4, 4), (2, 1),                   # week 2: division 1 is the player's, so 8; place 4; flag 1
    (8, 2), (4, 1), (2, 2),                           # week 4: division 2 place 1, flag 2
    (8, 8), (4, 4), (8, 3), (4, 2), (2, 1),           # week 5: 8/4 is on the schedule (week 2), draw both again: 3/2
    (8, 3), (4, 2), (8, 4), (4, 3), (2, 2),           # week 7: 3/2 is taken (week 5): 4/3, flag 2
    (8, 5), (4, 1), (2, 1),                           # week 8
    (8, 5), (4, 2), (2, 1),                           # week 10
    (8, 6), (4, 3), (2, 1),                           # week 11: the fifth flag 1
    (8, 6), (4, 4), (2, 1), (2, 1), (2, 2),           # week 12: flag 1 is full, drawn again twice, then flag 2
    (8, 7), (4, 1), (2, 2),                           # week 14
    (8, 7), (4, 2), (2, 2),                           # week 15
)

EXPECTED = [
    (1, 4, 1), (8, 4, 1), (1, 3, 1), (2, 1, 2), (3, 2, 1), (1, 2, 1), (4, 3, 2), (5, 1, 1),
    (1, 2, 2), (5, 2, 1), (6, 3, 1), (6, 4, 2), (1, 3, 2), (7, 1, 2), (7, 2, 2), (1, 4, 2),
]


def test_a_scripted_schedule_follows_the_lifted_procedure_draw_by_draw():
    source = ScriptedRandom(SCRIPT, strict=True)
    schedule = make_schedule(GameRandom(source), 1, 1)
    assert [(e.division, e.team, e.flag) for e in schedule] == EXPECTED
    assert source.left == 0 and source.drawn == len(SCRIPT)          # not one draw more or fewer


def check_a_schedule(schedule, own_division, own_team):
    assert len(schedule) == WEEKS == 16
    assert all(isinstance(entry, ScheduleEntry) for entry in schedule)
    assert Counter(entry.flag for entry in schedule) == {1: 8, 2: 8}                       # eight of each, GAME_SPEC 5.1
    division_games = [e for e in schedule if e.division == own_division]
    assert len(division_games) == 6
    rivals = Counter(e.team for e in division_games)
    assert rivals == {place: 2 for place in range(1, PLACES + 1) if place != own_team}      # each rival twice
    for place in rivals:
        assert sorted(e.flag for e in division_games if e.team == place) == [1, 2]
    others = [(e.division, e.team) for e in schedule if e.division != own_division]
    assert len(others) == 10 and len(set(others)) == 10                                     # ten different teams
    assert all(1 <= d <= DIVISIONS and 1 <= t <= PLACES for d, t in others)
    assert (own_division, own_team) not in others and all(e.team != own_team for e in division_games)
    assert Counter(e.flag for e in schedule if e.division != own_division) == {1: 5, 2: 5}


def test_every_team_gets_a_valid_schedule_from_any_seed():
    for own_division in range(1, DIVISIONS + 1):
        for own_team in range(1, PLACES + 1):
            for seed in range(25):
                rnd = GameRandom(random.Random(1000 * own_division + 100 * own_team + seed))
                check_a_schedule(make_schedule(rnd, own_division, own_team), own_division, own_team)
                assert rnd.fallbacks == 0                  # with the original data no redraw loop reaches its bound


def test_the_division_games_never_sit_one_or_two_weeks_from_the_game_placed_just_before():
    """The placement order is known from the result: rival places in order (the player's own skipped), flag 1 then 2."""
    for seed in range(300):
        own_division, own_team = 3, 2
        schedule = make_schedule(GameRandom(random.Random(seed)), own_division, own_team)
        week_of = {(e.team, e.flag): week for week, e in enumerate(schedule, start=1) if e.division == own_division}
        order = [week_of[(place, flag)] for place in range(1, PLACES + 1) if place != own_team for flag in (1, 2)]
        assert len(set(order)) == 6
        before = 0                                       # `last` starts at 0: the first game is never in week 1 or 2
        for week in order:
            assert abs(week - before) not in (1, 2), (seed, order)
            before = week


def test_a_source_stuck_on_one_number_still_gives_a_valid_schedule_through_the_bounds():
    for value in (0.0, 0.5, 0.9999999):
        stuck = StuckRandom(value)
        rnd = GameRandom(stuck)
        rnd.redraw_limit = 40                              # keep the run short; the bound itself is tested in test_rnd
        schedule = make_schedule(rnd, 4, 3)
        check_a_schedule(schedule, 4, 3)
        assert rnd.fallbacks > 0


def test_the_season_state_makes_the_schedule_and_the_week_loop_reads_this_weeks_opponent():
    season = SeasonState()
    season.choose_team(1, 1)
    season.make_schedule(GameRandom(ScriptedRandom(SCRIPT, strict=True)))
    for week, (division, team, flag) in enumerate(EXPECTED, start=1):
        season.gtp = week
        entry = season.set_week_opponent()
        assert (season.tn3, season.tn4, season.vtrnt) == (division, team, flag) == (entry.division, entry.team, entry.flag)
    season.gtp = 17                                        # a play-off week: the file of the schedule is not read
    assert season.set_week_opponent() is None
    assert (season.tn3, season.tn4, season.vtrnt) == (1, 4, 2)
