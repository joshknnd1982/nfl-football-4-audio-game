"""Substitutions during a game (nfl4 only, rule 0.13; GitHub issue 14, D-229). This is inspired by Jim Kitchen.

The tester: "Add an option to sub players in for either a play or for the rest of the game. Example I might want to put all backups in if winning by
a large amount. I might want to put a particular player in for a play". U in a play menu (the N. F. L. rules) opens the substitutions: all backups in,
the starters back in, or any place and the man who comes in there, for the next play only or for the rest of the game. A substitution changes who
holds a place and never a draw; Save Game keeps it; a franchise game rates, tires and hurts the man who really plays.
"""
import random

import pytest
from nflrig import nfl_engine_rig
from pagrig import Draws, run_steps
from test_se1_franchise_back_targets import franchise_state, real_league_at

from nfl4.data import debuglog
from nfl4.extras import nx_texts as X
from nfl4.extras import real_names as R
from nfl4.extras import subs as S
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import injuries as I
from nfl4.extras.nfl_rules import NflRules
from nfl4.extras.state import ExtrasRecord
from nfl4.game import key_list
from nfl4.game.rules import CLASSIC, MENU_REFRESH
from nfl4.game.setup import Roster

ENTER, ESCAPE, UP, DOWN, HOME, END = 13, 27, 38, 40, 36, 35
MENU_UNTIL = ("offense_chosen", "defense_chosen", "concede", "save_game")
START = dict(wisoff=1, defense=2, half=2, yard_line=30, down=1, to_go=10, quarter=1)
BENGALS = 1


@pytest.fixture(autouse=True)
def fresh_defaults():
    R.reset_defaults_cache()
    yield
    R.reset_defaults_cache()


def rig_for(tmp_path, answers=(), offense="classic", **state):
    fields = dict(START)
    fields.update(state)
    rules = NflRules(timeouts_on=False, offense_book=offense)
    return nfl_engine_rig(tmp_path, answers=list(answers), rules=rules, **fields)


def texts(rig, start=0):
    return [t for t, _, _ in rig.said[start:]]


def the_offense_menu(rig):
    return run_steps(rig, rig.engine.offense_menu, Draws(), until=MENU_UNTIL)          # Draws(): no draw at all in the lists


def the_defense_menu(rig):
    return run_steps(rig, rig.engine.defense_menu, Draws(), until=MENU_UNTIL)


def names(rig):
    s = rig.engine.s
    roster = s.rosters[1]
    return roster.running_backs + roster.receivers + roster.defense + roster.special_teams + roster.kickers + [s.quarterbacks[1]]


def man(key, position, rating=None):
    return S.Man(key, str(key), position, rating)


# ----- the rules: backups in, one man in, the record -----

def table_of(*groups):
    """A 34-place table: (place, key, position) triples; every other place an unmovable stand-in."""
    table = [S.Man(None, "x") for _ in range(S.PLACE_COUNT)]
    for place, key, position in groups:
        table[place] = man(key, position)
    return table


def test_backups_in_rests_every_positions_starters_and_brings_in_the_bench():
    table = table_of((0, "HB1", "HB"), (1, "HB2", "HB"), (2, "HB3", "HB"), (3, "FB1", "FB"),
                     (6, "W1", "WR"), (7, "W2", "WR"), (8, "W3", "WR"), (9, "T1", "TE"), (10, "W4", "WR"), (11, "T2", "TE"),
                     (12, "LE1", "LEDG"), (13, "DT1", "DT"), (14, "DT2", "DT"), (15, "RE1", "REDG"), (16, "DT3", "DT"), (17, "LE2", "LEDG"),
                     (29, "W3", "WR"), (30, "C9", "CB"), (31, "K1", "K"), (32, "P1", "P"), (33, "QB1", "QB"))
    bench = [man("W5", "WR"), man("W6", "WR"), man("QB2", "QB"), man("QB3", "QB"), man("DT4", "DT"), man("T3", "TE"), man("K2", "K")]
    out = S.backups_in(table, bench)
    keys = [m.key for m in out]
    assert keys[0:4] == ["HB2", "HB3", "HB1", "FB1"]                           # one halfback starts; a lone fullback has nobody behind him
    assert [keys[p] for p in (6, 7, 8, 10)] == ["W4", "W5", "W6", "W1"]          # three receivers start: the fourth to sixth come in
    assert [keys[p] for p in (9, 11)] == ["T2", "T3"]                            # the tight ends at the tight ends' places
    assert [keys[p] for p in (13, 14, 16)] == ["DT3", "DT4", "DT1"]              # two tackles start
    assert keys[12] == "LE2" and keys[17] == "LE1" and keys[15] == "RE1"
    assert keys[33] == "QB2"                                                     # the backup quarterback
    assert keys[29:33] == ["W3", "C9", "K1", "P1"]                               # the returners, the kicker and the punter stay


def test_one_man_in_changes_places_with_the_man_there_or_comes_from_the_bench():
    table = table_of((0, "A", "HB"), (1, "B", "HB"), (2, "C", "HB"), (29, "B", "HB"), (30, "Z", "CB"), (33, "Q", "QB"))
    swapped = S.put(table, 0, table[2])
    assert [m.key for m in swapped[0:3]] == ["C", "B", "A"]
    benched = S.put(table, 0, man("D", "HB"))
    assert [m.key for m in benched[0:3]] == ["D", "B", "C"] and S.field_place_of(benched, "A") is None
    returner = S.put(table, 29, man("A", "HB"))
    assert returner[29].key == "A" and returner[0].key == "A"                    # a returner keeps his own place too
    other = S.put(table, 29, table[30])
    assert other[29].key == "Z" and other[30].key == "B"                         # the two returners change places


def test_the_record_applies_in_order_drops_a_man_who_cannot_play_and_covers_empty_places_again():
    base = table_of((0, "A", "HB"), (1, "B", "HB"), (2, "C", "HB"), (3, "C", "HB"), (33, "Q", "QB"))
    record = S.new_record()
    S.add(record, "game", 0, "C")
    S.add(record, "play", 1, "A")
    S.add(record, "game", 2, "GONE")
    table, dropped = S.effective(base, [], record, empty={3})
    assert [m.key for m in table[0:3]] == ["C", "A", "B"] and dropped == [("game", 2, "GONE")]
    assert table[3].key == "B"                                                   # the empty place says its nearest filled place's man
    S.add(record, "game", 1, "B")                                                # a newer word for the place ends its next-play man
    assert record["play"] == [] and record["game"] == [[0, "C"], [2, "GONE"], [1, "B"]]
    assert S.effective(base, [], S.new_record())[0] == base and S.is_empty(None)


def test_who_may_come_in_keeps_every_man_at_a_place_of_his_own_position_or_family():
    table = table_of((0, "H1", "HB"), (1, "H2", "HB"), (3, "F1", "FB"), (13, "D1", "DT"), (12, "E1", "LEDG"), (16, "D2", "DT"),
                     (18, "SAM", "SAM"), (19, "MIKE", "MIKE"), (29, "W1", "WR"), (31, "K1", "K"), (32, "P1", "P"), (33, "Q1", "QB"))
    bench = [man("H3", "HB"), man("E2", "REDG"), man("D3", "DT"), man("Q2", "QB"), man("L1", "LT"), man("C1", "CB"), man("WILL", "WILL")]
    at_halfback = [m.key for m, _where in S.candidates(table, bench, 0)]
    assert at_halfback == ["H2", "H3", "F1"]                                     # halfbacks first, then the fullback (his family's other role)
    assert [m.key for m, _ in S.candidates(table, bench, 13)] == ["D2", "D3"]    # a tackle's place takes tackles only
    assert [m.key for m, _ in S.candidates(table, bench, 12)] == ["E2"]          # a left edge takes a right edge
    assert [m.key for m, _ in S.candidates(table, bench, 18)] == ["MIKE", "WILL"]
    assert [m.key for m, _ in S.candidates(table, bench, 33)] == ["Q2"]
    assert "L1" not in [m.key for m, _ in S.candidates(table, bench, 29)] and "Q2" not in [m.key for m, _ in S.candidates(table, bench, 29)]
    assert [m.key for m, _ in S.candidates(table, bench, 31)] == ["P1"]


def test_the_saved_record_keeps_the_substitutions_and_refuses_a_damaged_one():
    record = ExtrasRecord()
    assert "subs" not in record.to_json()                                        # a game with none saves as before
    record.subs = {"backups": True, "game": [[0, "Joe Mixon"], [33, 4512]], "play": [[29, "Ray"]], "at": 12}
    again = ExtrasRecord.from_json(record.to_json())
    assert again.subs == record.subs
    for bad in ({"backups": 1, "game": [], "play": [], "at": 0}, {"backups": False, "game": [[34, "x"]], "play": [], "at": 0},
                {"backups": False, "game": [[0, ""]], "play": [], "at": 0}, {"backups": False, "game": [[0, True]], "play": [], "at": 0},
                {"backups": False, "game": [], "play": [], "at": -1}, {"backups": False, "game": []}):
        record.subs = bad
        with pytest.raises(ValueError):
            ExtrasRecord.from_json(record.to_json())


def test_the_key_is_u_in_the_key_list_and_no_play_menu_item_uses_it():
    row = key_list.BY_ID["subs"]
    assert row.keys == "U" and row.letters == "u" and row.modes == "nfl" and "U. in a play menu" in row.f5
    assert "next play" in row.what and "rest of the game" in row.what and "backups" in row.what
    assert "**U** (N. F. L. rules only)" in key_list.readme_text()


# ----- the U key in a game (no real names: the places' groups) -----

def test_u_opens_the_substitutions_and_escape_goes_back_to_the_play_menu_with_nothing_changed(tmp_path):
    rig = rig_for(tmp_path, answers=["u", ESCAPE, ESCAPE])
    before = names(rig)
    mark = len(rig.said)
    the_offense_menu(rig)
    said = texts(rig, mark)
    assert X.text("NXB-U01", coach="Kim") in said and " 1. %s " % X.text("NXB-U02") in said
    assert names(rig) == before and rig.engine.s.extras.subs is None


def test_all_backups_in_then_the_starters_back(tmp_path):
    rig = rig_for(tmp_path, answers=["u", ENTER, ESCAPE, ESCAPE])
    before = names(rig)
    mark = len(rig.said)
    the_offense_menu(rig)
    after = names(rig)
    assert X.text("NXB-U17") in texts(rig, mark) and rig.engine.s.extras.subs["backups"] is True
    assert after[0:6] == before[1:6] + before[0:1]                              # Back2 starts, Back1 last
    assert after[6:12] == before[10:12] + before[6:10]                          # four receivers start: Rec5 and Rec6 come in
    assert after[29:33] == before[29:33] and after[33] == before[33]            # returners, kickers stay; no backup quarterback known
    rig.keys.answers[:] = ["u", ENTER, ESCAPE, ESCAPE]                         # the first item is now "Starters back in"
    mark = len(rig.said)
    the_offense_menu(rig)
    assert X.text("NXB-U18") in texts(rig, mark) and names(rig) == before and S.is_empty(rig.engine.s.extras.subs)


def test_one_player_for_the_next_play_only_then_back_after_the_play(tmp_path):
    # the menu: 1 All backups in, 2 quarterback, 3 running backs; the backs' places: Enter on place 1; who: 1 is Back2, 2 is Back3; 1 next play
    rig = rig_for(tmp_path, answers=["u", "3", ENTER, ENTER, "2", ENTER, ENTER, ESCAPE, ESCAPE, ESCAPE])
    before = names(rig)
    mark = len(rig.said)
    the_offense_menu(rig)
    said = texts(rig, mark)
    assert names(rig)[0:3] == ["Back3", "Back2", "Back1"]                       # Back3 in at place 1, Back1 to his place
    assert X.text("NXB-U15", player="Back3", old="Back1") in said
    assert any(X.text("NXB-U09", label=X.text("NXM-L36", position=X.text("NXL-01"), n=1), player="Back1") == t for t in said)
    s = rig.engine.s
    s.extras.no_snap = True                                                     # a false start: the down again, the same men
    s.extras.plays += 1
    rig.rules.between_plays(s)
    assert names(rig)[0] == "Back3"
    s.extras.no_snap = False
    s.extras.plays += 1
    rig.rules.between_plays(s)
    assert names(rig) == before and s.extras.subs["play"] == []


def test_one_player_for_the_rest_of_the_game_stays_after_plays_and_the_defense_menu_has_u_too(tmp_path):
    # the defense menu: 1 All backups in, 2 quarterback, 3 backs, 4 receivers, 5 defensive linemen; place 2; who: Def1 (now place 1); 2 the game
    rig = rig_for(tmp_path, answers=["u", "5", ENTER, DOWN, ENTER, ENTER, DOWN, ENTER, ESCAPE, ESCAPE, ESCAPE], wisoff=2, defense=1)
    the_defense_menu(rig)
    assert names(rig)[12:14] == ["Def2", "Def1"]
    s = rig.engine.s
    for _ in range(3):
        s.extras.plays += 1
        rig.rules.between_plays(s)
    assert names(rig)[12:14] == ["Def2", "Def1"] and s.extras.subs["game"] == [[13, "Def1"]]


def test_classic_has_no_u_key():
    assert CLASSIC.menu_key(None, "u") is False


def test_a_loaded_game_plays_its_saved_substitutions(tmp_path):
    rig = rig_for(tmp_path, answers=[ESCAPE])
    s = rig.engine.s
    s.extras.subs = {"backups": False, "game": [[0, "Back4"]], "play": [], "at": 0}
    rig.rules.offense_menu(s, False)                                             # the first menu after the load
    assert names(rig)[0:4] == ["Back4", "Back2", "Back3", "Back1"]


# ----- the real rosters: positions and the bench -----

def real_rig(tmp_path, answers=()):
    rig = rig_for(tmp_path, answers=answers)
    real = R.defaults()
    rig.game.real_names = real
    rig.engine.s.rosters[1] = real.roster(BENGALS, rig.engine.s.rosters[1])
    rig.engine.s.quarterbacks[1] = real.quarterback(BENGALS)
    return rig, real


def test_with_the_real_rosters_backups_in_brings_the_backup_quarterback_and_bench_men_at_their_own_positions(tmp_path):
    rig, real = real_rig(tmp_path, answers=["u", ENTER, ESCAPE, ESCAPE])
    chart, _roles, _squad = real.chart(BENGALS)
    before = names(rig)
    the_offense_menu(rig)
    after = names(rig)
    assert after[33] == real.spoken(chart["QB"][1]) != before[33]               # the backup quarterback plays
    positions = {real.spoken(n): p for p, men in chart.items() for n in men}
    for place in S.FIELD:                                                        # every man at a place of his own position (rule 0.30)
        if positions.get(before[place]) and after[place] != before[place]:
            assert positions[after[place]] == positions[before[place]], (place, before[place], after[place])
    starters = {real.spoken(chart["WR"][i]) for i in range(3)}
    backups = len(chart["WR"]) - 3                                               # a team with two backup receivers keeps one starter in
    assert backups >= 1 and not starters & {after[p] for p in (6, 7, 8)[:min(3, backups)]}
    assert [after[p] for p in (6, 7, 8)][:min(3, backups)] == [real.spoken(n) for n in chart["WR"][3:3 + min(3, backups)]]


def test_with_the_real_rosters_a_bench_man_can_come_in_and_the_lists_say_positions(tmp_path):
    rig, real = real_rig(tmp_path)
    chart, _roles, _squad = real.chart(BENGALS)
    flow = rig.rules.subs
    base, bench, empty = flow.lineup(rig.engine.s)
    qbs = [m for m, where in S.candidates(base, bench, S.QUARTERBACK, empty)]
    assert [m.name for m in qbs] == [real.spoken(n) for n in chart["QB"][1:]] and all(where is None for m, where in S.candidates(base, bench, 33, empty))
    assert all(m.position == "QB" for m in qbs)
    text = flow.place_text(base, 33, None)
    assert text == X.text("NXB-U07", label=X.text("NXL-03"), player=base[33].name, position="quarterback")


# ----- a franchise game -----

def test_a_franchise_game_plays_the_bench_man_with_his_own_identity_and_rating_and_drops_him_when_hurt():
    league = real_league_at(3)
    game, state = franchise_state(league)
    rules = NflRules()
    rules.game = type("G", (), {"game_injuries": game, "season": None})()
    rules.state = state
    base, bench, empty = game.sub_lineup
    backup = next(m for m in bench if m.position == "QB")
    record = state.extras.subs = S.new_record()
    S.add(record, "game", S.QUARTERBACK, backup.key)
    game.refresh(1)
    assert state.quarterbacks[1] == backup.name and game.identity[1][D.PLACES_OF["QB"][0]] == backup.key
    assert state.rosters[1].ratings[("Quarterback:", 1)] == backup.rating
    game.record["hurt"].append([backup.key, "IJA", 2, 0])                       # hurt in the game: his place goes back to the starter
    game.refresh(1)
    assert state.quarterbacks[1] == base[S.QUARTERBACK].name


def test_a_franchise_game_with_no_substitution_is_unchanged():
    league = real_league_at(3)
    game, state = franchise_state(league)
    before = list(game.identity[1]), list(state.rosters[1].defense), dict(state.rosters[1].ratings)
    game.refresh(1)
    assert (list(game.identity[1]), list(state.rosters[1].defense), dict(state.rosters[1].ratings)) == before
    state.extras.subs = S.new_record()
    state.extras.subs["backups"] = True
    game.refresh(1)
    assert game.identity[1][S.QUARTERBACK] != before[0][S.QUARTERBACK]           # the backup quarterback plays
    assert len({i for p, i in enumerate(game.identity[1]) if p in S.FIELD and isinstance(i, int)}) == len(
        [p for p in S.FIELD if isinstance(game.identity[1][p], int)])            # one man, one place


# ----- a whole game: the substitutions move no draw -----

def subbing_rules():
    """After the fifth play all the backups go in and the sixth back comes in at place 1 for the game; every seventh play the sixth receiver goes in
    at receiver 1 for that play only."""
    from nflrig import RecordingRules

    class Rules(RecordingRules):
        def between_plays(self, state):
            x = state.extras
            if x.handled != x.plays:
                roster = state.rosters[1]
                if x.plays == 5:
                    record = state.extras.subs = S.new_record()
                    record["backups"] = True
                    S.add(record, "game", 0, roster.running_backs[5])
                    self.subs.apply(state, "test")
                elif x.plays > 5 and x.plays % 7 == 0:
                    S.add(state.extras.subs, "play", 6, self.subs.base_names[11])
                    state.extras.subs["at"] = x.plays
                    self.subs.apply(state, "test")
            return super().between_plays(state)
    return Rules(penalties_on=True, onside_on=True, qb_on=True, challenges_on=True, playbooks_on=True)


@pytest.mark.parametrize("seed", [31, 32])
def test_a_whole_game_with_substitutions_draws_and_scores_what_it_did_without_them(tmp_path, seed):
    from nflrig import RecordingRules, sim_game
    plain_rules = RecordingRules(penalties_on=True, onside_on=True, qb_on=True, challenges_on=True, playbooks_on=True)
    plain, _engine, _rules, plain_result = sim_game(tmp_path / "plain", seed, rules=plain_rules, trace=True)
    rig, engine, rules, result = sim_game(tmp_path / "subs", seed, rules=subbing_rules(), trace=True)
    assert rig.rnd.trace == plain.rnd.trace and len(rig.rnd.trace) > 1000
    assert result.scores == plain_result.scores
    record = engine.s.extras.subs
    assert record["backups"] is True and record["game"] and texts(rig) != texts(plain)    # other names were said


@pytest.mark.parametrize("seed", [31, 33])
def test_a_whole_franchise_game_with_the_backups_in_plays_to_the_end_with_one_man_in_one_place(tmp_path, seed):
    """One man in one place, except the places the Franchise's own rule covers after an injury (the next man up plays two: injuries.lineup); never a
    hurt man; the backup quarterback plays from the moment the backups go in, and the starter only while no other quarterback can."""
    from drrig import SURNAMES
    from nflrig import RecordingRules, SimEngine
    from pagrig import make_rig
    from test_fr_injury_flow import OPP, TEAM, WORDS
    from nfl4.extras.franchise import injury_flow as F
    league = real_league_at(3)
    rig = make_rig(tmp_path, rng=random.Random(seed), fast=True, vtrnt=2, gtp=3)
    checks, quarterbacks = [], []

    class Rules(RecordingRules):
        def between_plays(self, state):
            x = state.extras
            if x.handled != x.plays and x.plays == 3:
                state.extras.subs = S.new_record()
                state.extras.subs["backups"] = True
                self.subs.apply(state, "test")
            if x.handled != x.plays and state.extras.subs is not None:
                _base, bench, empty = game.sub_lineup
                ids = game.identity[1]
                seen, doubled = set(), []
                for place in S.FIELD:
                    if isinstance(ids[place], int):
                        if ids[place] in seen and place not in empty:
                            doubled.append(place)
                        seen.add(ids[place])
                hurt = [i for i in seen if i in game.out(1)]
                quarterbacks.append((ids[S.QUARTERBACK], [m.key for m in bench if m.position == "QB"]))
                checks.append((x.plays, doubled, hurt))
            return super().between_plays(state)

    rules = Rules(penalties_on=True, qb_on=True, onside_on=True, challenges_on=True)
    own, opponent = F.lineup_roster(league, TEAM, 3, False), F.lineup_roster(league, OPP, 3, True)
    game = F.GameInjuries(league, TEAM, OPP, 3, False, rig.game.rnd, SURNAMES, WORDS, say=lambda text, plain: rig.game.say2(text))
    engine = SimEngine(rig.game, rules, quarterback_names=game.quarterbacks, own_names=own, opponent_names=opponent)
    rig.game.play_engine, rig.game.game_injuries = engine, game
    try:
        result = engine.run()
    finally:
        rig.game.play_engine = rig.game.game_injuries = None
    starter = I.lineup(league, TEAM, 3, False)[S.QUARTERBACK][0]
    assert result is not None and len(checks) > 100
    assert [c for c in checks if c[1] or c[2]] == []
    assert quarterbacks[0][0] != starter
    for playing, bench_quarterbacks in quarterbacks:                            # the starter plays only when no backup quarterback is fit
        assert playing != starter or not bench_quarterbacks or bench_quarterbacks == [starter]
