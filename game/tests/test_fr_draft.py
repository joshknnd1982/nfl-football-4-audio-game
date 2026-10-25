"""The Franchise's draft (nfl4 only, rule 0.13): the class, the order of the picks, what a team's pick is worth, the picks and the draft
record (NFL_FRANCHISE_DESIGN 7.1 to 7.5, 12 item 6, 16 SX.8d). Rules only, no speech: the questions and the stages are test_fr_draft_flow.py.
"""
import copy
import random

import pytest

from drrig import SURNAMES, draft_league
from nfl4.extras import tuning as T
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import first_names as FN
from nfl4.extras.franchise import draft as DR
from nfl4.extras.franchise.league import SEASON, LeagueError, LeagueRecord, Player
from nfl4.game.rnd import GameRandom
from randsources import ScriptedRandom, below_value, value_for


def rnd_of(seed=1):
    return GameRandom(random.Random(seed))


def mid_draft(seed=3, picks=40, team=5):
    """A league in the middle of its draft: the class made, `picks` picks made by the computer's rule."""
    league = draft_league(seed=seed, team=team)
    draft = DR.Draft.create(league, rnd_of(seed), SURNAMES)
    for _ in range(picks):
        _, _, who = draft.next_slot()
        draft.make_pick(who, draft.best_for(who))
    return league, draft


# ----- the class (design 7.1, 12 item 6) -----

WEIGHTS = [("RB", 6), ("WR", 6), ("QB", 2), ("DL", 6), ("LB", 5), ("CB", 4), ("S", 2), ("RET", 2), ("K", 1), ("P", 1)]
POSITION_OF_ROLL = [position for position, weight in WEIGHTS for _ in range(weight)]


def test_the_positions_are_drawn_by_the_weights_of_the_design():
    assert len(POSITION_OF_ROLL) == 35 == sum(weight for _, weight in T.FR_CLASS_WEIGHTS)
    assert tuple(WEIGHTS) == tuple(T.FR_CLASS_WEIGHTS)


@pytest.mark.parametrize("roll", range(35))
def test_the_first_prospects_position_follows_the_roll_below_35(roll):
    league = draft_league()
    source = ScriptedRandom([below_value(35, roll)], strict=False)
    assert DR.make_class(league, GameRandom(source), SURNAMES)[0].pos == POSITION_OF_ROLL[roll]


def test_one_prospect_is_drawn_in_the_order_position_name_rating_twice_potential_age_offset():
    league = draft_league()
    active = FN.name_keys(league.league_id, (p.name for p in league.players.values()))     # D-131: the draw compares the surnames
    free = next(i for i, name in enumerate(SURNAMES, start=1) if name not in active)
    script = [below_value(35, 14), value_for(len(SURNAMES), free), below_value(15, 7), below_value(15, 9), below_value(100, 10),
              below_value(3, 1), below_value(7, 4)]
    prospect = DR.make_class(league, GameRandom(ScriptedRandom(script, strict=False)), SURNAMES)[0]
    base = T.FR_ROOKIE_RATING[0]                                       # 45 since SX.8m (46 before: the design's)
    assert (prospect.pos, prospect.name, prospect.true, prospect.potential, prospect.age, prospect.low) == (
        "DL", FN.full_name(league.league_id, SURNAMES[free - 1]), base + 7 + 9, "high", 22, base + 16 - 4)
    assert (prospect.middle, prospect.high) == (base + 15, base + 18)


def test_a_name_in_use_by_an_active_player_is_drawn_again():
    league = draft_league()
    taken = FN.surname_of(league.league_id, league.players[1].name)                         # D-131: his drawn surname
    free = next(i for i, name in enumerate(SURNAMES, start=1)
                if name not in FN.name_keys(league.league_id, (p.name for p in league.players.values())))
    script = [below_value(35, 0), value_for(len(SURNAMES), SURNAMES.index(taken) + 1), value_for(len(SURNAMES), free)]
    prospect = DR.make_class(league, GameRandom(ScriptedRandom(script, strict=False)), SURNAMES)[0]
    assert prospect.name == FN.full_name(league.league_id, SURNAMES[free - 1])


@pytest.mark.parametrize("seed", [1, 2, 3, 4])
def test_the_class_has_the_designs_size_ranges_ages_and_unique_new_names(seed):
    league = draft_league(seed=seed)
    before = league.to_json()
    prospects = DR.make_class(league, rnd_of(seed), SURNAMES)
    assert league.to_json() == before                                       # making the class changes nothing of the league
    assert len(prospects) == T.FR_CLASS_SIZE == 260
    active = {p.name for p in league.players.values() if p.status == "active"}
    names = [p.name for p in prospects]
    assert len(set(names)) == 260 and not set(names) & active
    for prospect in prospects:
        base, span = T.FR_ROOKIE_RATING
        assert base <= prospect.true <= base + 2 * (span - 1) and 21 <= prospect.age <= 23
        assert prospect.low <= prospect.true <= prospect.low + 6 and prospect.high - prospect.low == 6
        assert prospect.potential in D.POTENTIALS and prospect.pos in D.POSITIONS
    shares = {pos: sum(1 for p in prospects if p.pos == pos) / 260 for pos in D.POSITIONS}
    assert 0.10 < shares["RB"] < 0.26 and shares["K"] < 0.08 and shares["P"] < 0.08 and shares["DL"] > 0.08


def test_the_potentials_follow_the_shares_of_the_design_over_many_classes():
    league = draft_league()
    counts = {"high": 0, "average": 0, "low": 0}
    for seed in range(20):
        for prospect in DR.make_class(league, rnd_of(seed), SURNAMES):
            counts[prospect.potential] += 1
    total = sum(counts.values())
    assert abs(counts["high"] / total - 0.25) < 0.03 and abs(counts["average"] / total - 0.50) < 0.03


# ----- the order (design 7.2) -----

# Teams 1 to 20 missed the play-offs; 21 to 24 lost in the wild card round, 25 to 28 in the division round, 29 and 30 in the conference
# championship; 31 lost the Super Bowl and 32 won it. The wins and the sums are chosen so that every tie rule is used once.
MISSED = [5, 3, 3, 7, 1, 1, 9, 9, 2, 4, 6, 6, 8, 8, 0, 10, 10, 11, 12, 12]
WINS = MISSED + [10, 9, 9, 12] + [11, 11, 11, 11] + [12, 11] + [13, 14]
FINISH = [0] * 20 + [1] * 4 + [2] * 4 + [3] * 2 + [4, 5]
SUMS = [7000] * 32
for _team, _sum in ((3, 7100), (8, 7200), (7, 6900), (11, 7300), (12, 7200), (16, 7500), (17, 7100), (22, 7100), (25, 7400), (26, 7300),
                    (27, 7300), (28, 7200)):
    SUMS[_team - 1] = _sum
EXPECTED_ORDER = [15, 5, 6, 9, 2, 3, 10, 1, 12, 11, 4, 13, 14, 7, 8, 17, 16, 18, 19, 20,      # missed: wins, then the weaker roster, then T01
                  23, 22, 21, 24,                                                             # wild card losers
                  28, 26, 27, 25,                                                             # division round losers
                  30, 29, 31, 32]                                                             # conference losers, the Super Bowl loser, the champion


def test_the_order_on_hand_worked_standings_uses_every_group_and_every_tie_rule():
    assert DR.draft_order(SUMS, WINS, FINISH) == EXPECTED_ORDER
    assert sorted(EXPECTED_ORDER) == list(range(1, 33))


def test_the_order_of_a_league_reads_its_history_entry_and_the_strengths_of_the_season():
    league = draft_league(wins=WINS, finish=FINISH)
    league.sums = list(SUMS)
    assert DR.order_of(league) == EXPECTED_ORDER
    draft = DR.Draft.create(league, rnd_of(), SURNAMES)
    assert draft.order == EXPECTED_ORDER and draft.slot(1) == (1, 1, 15) and draft.slot(33) == (2, 1, 15) and draft.slot(224) == (7, 32, 32)
    assert draft.place_in_round(15) == 1 and draft.place_in_round(32) == 32


def test_without_a_history_entry_the_records_and_the_strengths_decide():
    league = draft_league()
    league.records = [x for w in WINS for x in (w, 16 - w)]
    league.sums = list(SUMS)
    expected = DR.draft_order(SUMS, WINS, [0] * 32)
    assert DR.order_of(league) == expected


def test_the_order_is_the_same_in_all_seven_rounds_and_has_no_draw():
    league = draft_league(wins=WINS, finish=FINISH)
    league.sums = list(SUMS)
    with_order, class_only = ScriptedRandom([], seed=9), ScriptedRandom([], seed=9)
    draft = DR.Draft.create(league, GameRandom(with_order), SURNAMES)
    DR.make_class(league, GameRandom(class_only), SURNAMES)
    assert with_order.drawn == class_only.drawn > 1000                      # the class draws; making the order adds not one number
    assert [draft.slot(n)[2] for n in range(1, 225)] == EXPECTED_ORDER * 7


# ----- what a pick is worth (design 7.3) -----

def crafted(rows, seed=3, team=5, mutate=None):
    """A draft whose first prospects are `rows` ([pos, name, true, potential, age, low]) and a league made by `mutate`."""
    league = draft_league(seed=seed, team=team)
    if mutate is not None:
        mutate(league)
    made = DR.Draft.create(league, rnd_of(seed), SURNAMES)
    classes = [list(row) for row in league.draft["class"]]
    for index, row in enumerate(rows):
        classes[index] = list(row)
    league.draft["class"] = classes
    return league, DR.Draft(league)


def set_team(league, team, **ratings):
    """Ratings of the team's places: place index -> rating; a rating of None retires the player of the place."""
    for index, rating in ratings.items():
        place = int(index[1:])
        player = league.player_at(team, place)
        if rating is None:
            player.status, player.place, player.left = "retired", -1, league.season
            league.rosters[team - 1][place] = 0
        else:
            player.rating = player.peak = rating


def team_five(league):
    set_team(league, 5, **{"p%d" % i: 70 for i in range(6)}, p31=None, p32=70, p33=55, p29=60, p30=70)     # backs 70; no kicker; punter 70; QB 55; returners 60 and 70


def test_a_teams_needs_are_open_places_and_the_weakest_starter():
    league, draft = crafted([], mutate=team_five)
    needs = draft.needs(5)
    assert needs["RB"] == (False, 70)                     # six backs for six places
    assert needs["QB"] == (True, 55)                      # one place, held by a 55: under the weak mark of 60
    assert needs["K"] == (True, None)                     # no kicker
    assert needs["P"] == (False, 70) and needs["RET"] == (False, 60)


def test_the_value_of_a_prospect_adds_the_middle_the_potential_and_the_need_parts():
    rows = [["RB", "Aa", 60, "average", 22, 57],          # middle 60, average
            ["QB", "Bb", 63, "high", 22, 60],             # middle 63, high: +5
            ["K", "Cc", 53, "average", 22, 50],           # middle 53
            ["P", "Dd", 80, "low", 22, 77],               # middle 80, low: -4
            ["RET", "Ee", 65, "average", 22, 62]]         # middle 65
    league, draft = crafted(rows, mutate=team_five)
    needs = draft.needs(5)
    value = lambda i: draft.value(draft.prospects[i], needs)
    assert value(0) == 60                                 # no open place, 60 does not beat the lowest 70
    assert value(1) == 63 + 5 + 12 + 3                    # quarterback: open place +12, beats the 55 by +3
    assert value(2) == 53 + 8                             # a kicker: open place +8, nobody to beat
    assert value(3) == 80 - 4 - 10 + 3                    # a punter for a full group: -10, but beats the 70: +3
    assert value(4) == 65 - 10 + 3                        # a returner for a full group


def test_a_rookie_already_drafted_fills_the_place_and_raises_the_bar_by_the_middle_of_his_range():
    rows = [["QB", "Bb", 63, "high", 22, 60], ["RB", "Aa", 75, "average", 22, 72]]
    league, draft = crafted(rows, mutate=team_five)
    rookie = Player(10 ** 6, "Rookie", "QB", 66, "average", 22, 0, 66, [1, 1, 1], 0, "active", 0, 5, -1)
    league.players[rookie.id] = rookie
    draft.rookies[5] = [rookie]
    draft.middle_of[rookie.id] = 65
    assert draft.needs(5)["QB"] == (False, 65)            # the place is held by the rookie (65 by his range): no longer open or weak
    assert draft.value(draft.prospects[0], draft.needs(5)) == 63 + 5                      # 63 does not beat 65
    back = Player(10 ** 6 + 1, "Back", "RB", 74, "average", 22, 0, 74, [1, 2, 1], 0, "active", 0, 5, -1)
    league.players[back.id] = back
    draft.rookies[5] = [rookie, back]
    draft.middle_of[back.id] = 72
    needs = draft.needs(5)
    assert needs["RB"] == (False, 70)                     # seven backs for six places: the sixth best is still a 70
    assert draft.value(draft.prospects[1], needs) == 75 + 3                               # 75 beats the sixth starter


def test_a_group_with_a_rookie_for_its_last_place_is_full():
    league, draft = crafted([], mutate=lambda lg: set_team(lg, 5, p0=None))
    assert draft.needs(5)["RB"][0] is True
    rookie = Player(10 ** 6, "Rookie", "RB", 60, "average", 22, 0, 60, [1, 1, 1], 0, "active", 0, 5, -1)
    league.players[rookie.id] = rookie
    draft.rookies[5] = [rookie]
    draft.middle_of[rookie.id] = 58
    assert draft.needs(5)["RB"][0] is False


def test_the_open_places_are_listed_in_the_roster_menus_order_and_a_drafted_rookie_closes_one():
    league, draft = crafted([], mutate=lambda lg: set_team(lg, 5, p33=None, p0=None, p1=None, p31=None))
    assert DR.open_places(draft, 5) == [("QB", 1), ("RB", 2), ("K", 1)]
    rookie = Player(10 ** 6, "Rookie", "RB", 60, "average", 22, 0, 60, [1, 1, 1], 0, "active", 0, 5, -1)
    league.players[rookie.id] = rookie
    draft.rookies[5] = [rookie]
    assert DR.open_places(draft, 5) == [("QB", 1), ("RB", 1), ("K", 1)]
    assert DR.open_places(draft, 6) == []


def test_equal_values_go_to_the_prospect_with_the_lower_number():
    rows = [["RB", "Aa", 60, "average", 22, 57], ["RB", "Bb", 60, "average", 22, 57], ["RB", "Cc", 60, "average", 22, 57]]
    league, draft = crafted(rows)
    # three equal prospects at the top of the board: the lowest number first, and again after he is gone
    for row_index in range(260):
        if row_index >= 3:
            draft.data["class"][row_index] = ["K", "Z%d" % row_index, 40, "low", 22, 40]
    draft = DR.Draft(league)
    assert draft.best_for(5).index == 0 and draft.ranked_for(5)[0].index == 0
    assert [p.index for p in draft.ranked_for(5)[:3]] == [0, 1, 2]


# ----- the picks (design 7.3, 7.5) -----

@pytest.mark.parametrize("seed", [1, 2, 3])
def test_the_fast_best_choice_is_the_first_of_the_whole_ranking_and_of_a_brute_force_at_every_pick(seed):
    league = draft_league(seed=seed)
    draft = DR.Draft.create(league, rnd_of(seed), SURNAMES)
    while not draft.done:
        _, _, team = draft.next_slot()
        needs = draft.needs(team)
        brute = max(draft.board.available(), key=lambda p: (draft.value(p, needs), -p.index))
        ranked = draft.ranked_for(team)
        best = draft.best_for(team)
        assert best.index == brute.index == ranked[0].index
        assert [p.index for p in ranked] == sorted((p.index for p in ranked), key=lambda i: (-draft.value(draft.prospects[i], needs), i))
        draft.make_pick(team, best)


def test_a_whole_draft_gives_every_team_one_player_a_round_in_the_order_and_changes_nothing_else():
    league = draft_league(seed=4)
    before = copy.deepcopy(league.rosters)
    draft = DR.Draft.create(league, rnd_of(4), SURNAMES)
    first_id = league.next_id
    while not draft.done:
        round_no, in_round, team = draft.next_slot()
        prospect = draft.best_for(team)
        player = draft.make_pick(team, prospect)
        assert player.drafted == [league.season, round_no, in_round] and player.team == team and player.place == -1
        assert (player.name, player.pos, player.rating, player.potential, player.age) == (
            prospect.name, prospect.pos, prospect.true, prospect.potential, prospect.age)
        assert (player.status, player.seasons, player.points) == ("active", 0, 0) and player.peak == player.rating
    assert league.rosters == before                                                  # the rosters wait for the cut
    assert league.pick_no == 225 and league.next_id == first_id + 224
    by_team = {}
    for team, index, pid in league.draft["picks"]:
        by_team.setdefault(team, []).append(league.players[pid].drafted[1])
    assert all(rounds == [1, 2, 3, 4, 5, 6, 7] for rounds in by_team.values()) and len(by_team) == 32
    assert len({row[1] for row in league.draft["picks"]}) == 224                      # nobody twice
    assert len(league.waiting_rookies(5)) == 7 and all(p.place == -1 for p in league.waiting_rookies(5))
    names = [p.name for p in league.players.values() if p.status == "active"]
    assert len(names) == len(set(names))                                           # the rookies never repeat an active name


def test_a_pick_for_the_wrong_team_or_a_prospect_twice_or_after_the_last_is_refused():
    league, draft = mid_draft(picks=3)
    round_no, in_round, team = draft.next_slot()
    other = draft.order[0] if draft.order[0] != team else draft.order[1]
    with pytest.raises(LeagueError):
        draft.make_pick(other, draft.best_for(other))
    taken = draft.prospects[league.draft["picks"][0][1]]
    with pytest.raises(LeagueError):
        draft.make_pick(team, taken)
    while not draft.done:
        _, _, who = draft.next_slot()
        draft.make_pick(who, draft.best_for(who))
    with pytest.raises(LeagueError):
        draft.make_pick(draft.order[0], draft.prospects[0])


def test_the_same_class_gives_the_same_draft_by_the_best_choice_or_by_the_first_of_the_whole_ranking():
    """The computer takes `best_for` (found without ranking everybody) and the staff's list is the start of `ranked_for`: for every team at
    every pick they are the same prospect, so the two drafts are the same league. (Invariant I7 through the questions is in
    test_fr_draft_flow.py.)"""
    leagues = []
    for way in (lambda d, t: d.best_for(t), lambda d, t: d.ranked_for(t)[0]):
        league = draft_league(seed=6)
        draft = DR.Draft.create(league, rnd_of(6), SURNAMES)
        while not draft.done:
            _, _, team = draft.next_slot()
            draft.make_pick(team, way(draft, team))
        leagues.append(league.to_json())
    assert leagues[0] == leagues[1]


def test_the_staff_pick_flag_is_kept_in_the_record_and_the_class_is_not_made_twice():
    league, draft = mid_draft(picks=5)
    assert not draft.staff_all
    draft.let_the_staff_pick_the_rest()
    again = LeagueRecord.from_json(league.to_json())
    assert DR.Draft(again).staff_all and again.draft["picks"] == league.draft["picks"] and again.draft["class"] == league.draft["class"]


# ----- the record in a file (design 10.1) -----

def test_a_draft_in_progress_survives_a_round_trip_at_the_start_in_the_middle_and_at_the_end():
    for picks in (0, 1, 100, 223, 224):
        league, draft = mid_draft(picks=picks)
        again = LeagueRecord.from_json(league.to_json())
        assert again.to_json() == league.to_json() and again.pick_no == picks + 1
        assert [p.id for p in again.waiting_rookies(5)] == [p.id for p in league.waiting_rookies(5)]


def test_the_range_of_a_rookie_is_known_until_the_cut():
    league, draft = mid_draft(picks=60)
    for team, index, pid in league.draft["picks"][:40]:
        player = league.players[pid]
        low, high = league.rookie_range(player)
        assert (low, high) == (draft.prospects[index].low, draft.prospects[index].high) == draft.range_of(player)
        assert low <= player.rating <= high
    with pytest.raises(LeagueError):
        league.rookie_range(league.players[1])


def broken(mutation, why, picks=40):
    league, _ = mid_draft(picks=picks)
    mutation(league)
    with pytest.raises(LeagueError, match=why):
        LeagueRecord.from_json(league.to_json())


def pick_player(league, number=0):
    return league.players[league.draft["picks"][number][2]]


@pytest.mark.parametrize("name,mutation,why", [
    ("a pick of another team", lambda lg: lg.draft["picks"][0].__setitem__(0, lg.draft["order"][1]), "out of order or twice"),
    ("a prospect twice", lambda lg: lg.draft["picks"][1].__setitem__(1, lg.draft["picks"][0][1]), "out of order or twice"),
    ("a wrong next pick", lambda lg: setattr(lg, "pick_no", 5), "next pick"),
    ("staff_all of 2", lambda lg: lg.draft.__setitem__("staff_all", 2), "staff_all"),
    ("an order with a team twice", lambda lg: lg.draft["order"].__setitem__(1, lg.draft["order"][0]), "draft order"),
    ("a prospect whose range misses his rating", lambda lg: lg.draft["class"][0].__setitem__(5, lg.draft["class"][0][2] + 1), "range"),
    ("a prospect of an unknown position", lambda lg: lg.draft["class"][0].__setitem__(0, "TE"), "a prospect is"),
    ("a class that is too small", lambda lg: lg.draft.__setitem__("class", lg.draft["class"][:100]), "class holds"),
    ("a rookie who is not his prospect", lambda lg: setattr(pick_player(lg), "name", "Someoneelse"), "not the prospect"),
    ("a waiting rookie with a place", lambda lg: setattr(pick_player(lg), "place", 3), "not a rookie waiting"),
    ("a rookie who was drafted in another round", lambda lg: setattr(pick_player(lg), "drafted", [1, 7, 7]), "not a rookie waiting"),
    ("a rookie who is not active", lambda lg: setattr(pick_player(lg), "status", "released"), "not a rookie waiting"),
    ("a prospect aged 26", lambda lg: lg.draft["class"][0].__setitem__(4, 26), "a prospect.s age"),
    ("a class of 224", lambda lg: lg.draft.__setitem__("class", lg.draft["class"][:224]), "class holds"),
    ("a class of 261", lambda lg: lg.draft["class"].append(list(lg.draft["class"][0])), "class holds"),
    ("a cut after a half draft", lambda lg: setattr(lg, "stage_no", 5), "the cut after"),
    ("a draft in stage 3", lambda lg: setattr(lg, "stage_no", 3), "a draft in stage"),
    ("a draft in the season", lambda lg: setattr(lg, "stage", SEASON), "a draft in stage"),
    ("an extra key", lambda lg: lg.draft.__setitem__("note", 1), "the draft holds"),
    ("a missing key", lambda lg: lg.draft.pop("order"), "the draft holds"),
    ("too many picks", lambda lg: lg.draft["picks"].extend([[1, 0, 1]] * 200), "picks"),
    ("a pick row of two values", lambda lg: lg.draft["picks"].__setitem__(0, [1, 2]), "a pick is"),
    ("a draft that is not a table", lambda lg: setattr(lg, "draft", [1, 2, 3]), "the draft holds"),
])
def test_a_draft_record_that_is_not_whole_is_damage(name, mutation, why):
    broken(mutation, why)


def test_a_pick_number_without_a_draft_is_damage_and_so_is_a_player_without_a_place_and_without_a_draft():
    league, _ = mid_draft(picks=0)
    league.draft = None
    with pytest.raises(LeagueError):
        LeagueRecord.from_json(league.to_json())                                   # pick_no is 1 and there is no draft
    league.pick_no = 0
    LeagueRecord.from_json(league.to_json())                                       # at stage 4 before the class: fine
    league.players[5].place = -1                                                    # an active player outside every place
    with pytest.raises(LeagueError):
        LeagueRecord.from_json(league.to_json())


def test_every_stage_that_may_hold_a_draft_loads_and_the_others_do_not():
    for stage_no, ok in ((4, True), (5, True), (6, False), (2, False)):
        league, _ = mid_draft(picks=224)
        league.stage_no = stage_no
        if ok:
            LeagueRecord.from_json(league.to_json())
        else:
            with pytest.raises(LeagueError):
                LeagueRecord.from_json(league.to_json())
