"""The catalog's offense in whole games, in the saved game, in the player's files, through the ratings door and on the clock (nfl4 only,
rule 0.13; NX-P1 to NX-P8, NX-H1; NFL_PLAYS_DESIGN 2 and 7; PX SX.10c, D-093). This is inspired by Jim Kitchen.

Whole seeded games where the player's offense calls the catalog's plays (each family and the other lists) end as the original's games end,
with the scores the statistics hold; Again and Formation and Tempo are saved with the game and refused when damaged; plays.txt holds every
play of the catalog and its off switch takes a play out of the menus; favourites.txt is one of the Customize layer's files; a Franchise
game's ratings move the models within the bounds; the player's Tempo is the clock's tempo between plays.
"""
import random

import pytest

from nfl4.data import customize as CU
from nfl4.extras import clock as CK
from nfl4.extras import offense_flow as OF
from nfl4.extras import playbook_data as PD
from nfl4.extras import playbook_list as PL
from nfl4.extras import playbooks as PB
from nfl4.extras import tuning as T
from nfl4.extras.nfl_rules import NflRules
from nfl4.extras.plays import catalog as C
from nfl4.extras.plays import favourites as FV
from nfl4.extras.plays import model as M
from nfl4.extras.state import ExtrasRecord
from nfl4.game import key_list as K
from nfl4.game.rules import CLASSIC
import nflrig
from nflrig import nfl_engine_rig

START = dict(wisoff=1, defense=2, half=2, yard_line=30, down=1, to_go=10, quarter=1)


class CatalogSim(nflrig.SimEngine):
    """Both sides by the computer, and side 1's offense calls a catalog play of the family the computer's draw gave (any play of the
    offense one time in four): the model's path in whole games."""

    def __init__(self, *args, picker_seed=7, **kwargs):
        super().__init__(*args, **kwargs)
        self.picker = random.Random(picker_seed)

    def offense_menu(self):
        step = super().offense_menu()
        s = self.s
        if s.offense_play in (6, 7):
            return step
        pool = [c for c in C.OFFENSE if OF.engine_family(c) == s.offense_play and c.kind not in ("kneel", "spike")]
        if self.picker.random() < 0.25 or not pool:
            pool = [c for c in C.OFFENSE if c.kind not in ("kneel", "spike")]
        concept = self.picker.choice(pool)
        self.rules.offense.called = concept.id
        s.offense_play = OF.engine_family(concept)
        return step


def catalog_game(tmp_path, seed):
    rig = nflrig.make_rig(tmp_path, rng=random.Random(seed), fast=True, vtrnt=2)
    rules = nflrig.RecordingRules(qb_on=True, penalties_on=True, challenges_on=True, onside_on=True)
    engine = CatalogSim(rig.game, rules, quarterback_names=lambda state: nflrig.QUARTERBACKS, picker_seed=seed)
    rig.game.play_engine = engine
    try:
        result = engine.run()
    finally:
        rig.game.play_engine = None
    return rig, engine, rules, result


@pytest.mark.parametrize("seed", range(1, 9))
def test_whole_games_with_the_catalogs_plays_end_and_their_scores_are_the_statistics(tmp_path, seed):
    rig, engine, rules, result = catalog_game(tmp_path, seed)
    s = engine.s
    assert result.scores == (s.score(1), s.score(2))
    events = rules.offense.events
    assert len(events) > 30                                   # the player's offense played catalog plays
    assert {kind for _p, _c, kind, _y, _b in events} >= {"run", "complete", "incomplete"}
    catalog_outcomes = [o for o in engine.outcomes if o.catalog]
    assert catalog_outcomes and all(o.offense == 1 for o in catalog_outcomes)
    # no result is left over; a call may be, when the game ran out at its snap (H1): the play was never run, the next menu or kick-off
    # clears it, and the next game has its own rules object (for_game)
    assert engine.noise_net == 0 and rules.offense.result is None
    assert s.extras.again[0] in C.BY_ID


def test_the_catalogs_games_score_like_football(tmp_path):
    """A loose plausibility check on 8 games (SX.10e measures the bands): the player's catalog offense scores and gains like an offense."""
    points, plays, yards = [], 0, 0
    for seed in range(1, 9):
        _rig, engine, rules, result = catalog_game(tmp_path / str(seed), seed)
        points.append(result.scores[0])
        plays += len(rules.offense.events)
        yards += sum(y for _p, _c, kind, y, _b in rules.offense.events if kind in ("run", "complete", "sack", "kneel"))
    assert 5 <= sum(points) / len(points) <= 45, points
    assert 3.0 <= yards / plays <= 8.0, yards / plays


# ----- the saved game -----

def test_again_and_the_play_settings_are_saved_with_the_game_and_checked():
    record = ExtrasRecord()
    record.again = ["O027", "D017"]
    record.play_settings = {"formation": "shotgun", "tempo": "hurry_up"}
    back = ExtrasRecord.from_json(record.to_json())
    assert back.again == ["O027", "D017"] and back.play_settings == {"formation": "shotgun", "tempo": "hurry_up"}
    old = ExtrasRecord.from_json('{"rules_year": %d}' % ExtrasRecord().rules_year)        # a record saved before SX.10c
    assert old.again == ["", ""] and old.play_settings == {}
    for bad in (["D017", ""], ["O999", ""], "O027", ["O027"]):
        record.again = bad
        with pytest.raises(ValueError):
            ExtrasRecord.from_json(record.to_json())
    record.again = ["", ""]
    for bad in ({"formation": "wishbone"}, {"colour": "red"}, {"tempo": 3}):
        record.play_settings = bad
        with pytest.raises(ValueError):
            ExtrasRecord.from_json(record.to_json())


# ----- plays.txt -----

def test_plays_txt_holds_every_play_of_the_catalog_and_its_off_switch_takes_a_play_out_of_the_menus(tmp_path):
    entries = PL.default_plays()
    assert [pid for pid, _name in entries] == sorted((c.id for c in C.CATALOG), key=lambda i: ("ODK".index(i[0]), int(i[1:])))
    assert len(entries) == len(C.CATALOG) == 282
    assert dict(entries)["O120"] == PB.DEFAULT_TABLE.name("O120") and dict(entries)["K011"] == "Punt"

    class Entry:
        def __init__(self, id_, value, line):
            self.id, self.value, self.line = id_, value, line

    class Problems:
        def __init__(self):
            self.items = []

        def add(self, where, why):
            self.items.append((where, why))

    problems = Problems()
    table = PL.apply_plays(PB.DEFAULT_TABLE, [Entry("O120", "Big Slant; off", 1), Entry("K011", "Boomer", 2),
                                               Entry("O400", "Nothing", 3)], problems)
    assert "O120" in table.disabled and table.name("K011") == "Boomer" and len(problems.items) == 1
    rules = NflRules(timeouts_on=False, offense_book="west", defense_book="classic")
    rig = nfl_engine_rig(tmp_path, rules=rules, **START)
    rig.game.playbook_table = table
    assert "O120" not in rules.offense.usable(rig.engine.s) and "O121" not in rules.offense.usable(rig.engine.s)


# ----- favourites.txt in the Customize layer -----

def test_favourites_txt_is_a_file_of_the_customize_layer_read_only_with_the_nfl_rules(tmp_path):
    custom = CU.Customization(str(tmp_path), default_surnames=lambda: ["Smith"] * 1708, extras=True)
    assert custom.snapshot.favourites == ((), ())
    path = tmp_path / CU.PLAYBOOKS_FOLDER / FV.FILE_NAME
    assert path.exists()
    assert FV.write(str(tmp_path), ("O027", "O001"), ("D017",))
    custom.reload()
    assert custom.snapshot.favourites == (("O027", "O001"), ("D017",))
    classic = CU.Customization(str(tmp_path / "classic"), default_surnames=lambda: ["Smith"] * 1708)
    assert classic.snapshot.favourites is None and not (tmp_path / "classic" / CU.PLAYBOOKS_FOLDER / FV.FILE_NAME).exists()


def test_plus_writes_favourites_txt_where_the_program_keeps_the_players_files(tmp_path):
    rules = NflRules(timeouts_on=False, offense_book="west", defense_book="classic")
    rig = nfl_engine_rig(tmp_path / "rig", rules=rules, **START)

    class Custom:
        folder = str(tmp_path / "custom")
    rig.game.customization = Custom()
    flow = rules.offense
    item = [i for i in (flow.menus._open("og06", "top") or rules.offense_menu(rig.engine.s, False)) if i.action[0] == "pm:call"][0]
    flow.key(rig.engine.s, OF.KEY_PLUS_MAIN, item)
    offense, defense, _load, problems = FV.read(Custom.folder)
    assert offense == (item.action[1],) and defense == () and problems.count == 0


# ----- the ratings door -----

def test_the_ratings_door_moves_the_models_within_the_bounds_and_is_nothing_without_ratings(tmp_path):
    rules = NflRules(timeouts_on=False, offense_book="west", defense_book="classic")
    rig = nfl_engine_rig(tmp_path, rules=rules, **START)
    flow = rules.offense
    assert flow.ratings_door(C.BY_ID["O001"]) == {}                      # no ratings: nothing
    assert rules.modifiers.ratings_mod("run") is None
    rules.modifiers.ratings_mod = lambda kind: PD.Mod(2, 2, -3, 3, 3)
    door = flow.ratings_door(C.BY_ID["O017"])
    assert door == dict(run_shift=200, comp_shift=300, sack_shift=-3 * T.FR_MODEL_SACK, fumble_pct=50 * 100 // 53, catch_yards=2)
    situation = flow.situation(rig.engine.s, C.BY_ID["O017"])
    assert situation.comp_shift == 300 and situation.to_goal == 70


def test_the_ratings_shifts_move_the_models_means_the_right_way():
    rnd = random.Random(3)

    class Source:
        @staticmethod
        def below(n):
            return int(rnd.random() * n)
    call = C.BY_ID["D017"].params
    run = C.BY_ID["O001"]
    plain = sum(M.run_play(run, call, M.Situation(), Source).yards for _ in range(4000)) / 4000
    better = sum(M.run_play(run, call, M.Situation(run_shift=200), Source).yards for _ in range(4000)) / 4000
    assert better > plain + 0.5                        # the shift moves no more than the stuffed bins hold (model.shift_bins)
    slant = C.BY_ID["O017"]
    caught = sum(M.pass_play(slant, call, M.Situation(), Source).kind == "complete" for _ in range(4000))
    more = sum(M.pass_play(slant, call, M.Situation(comp_shift=600), Source).kind == "complete" for _ in range(4000))
    assert more > caught + 100


# ----- the clock -----

@pytest.mark.parametrize("setting, span", [("hurry_up", T.RUNOFF_HURRY), ("no_huddle", T.RUNOFF_NO_HUDDLE), ("normal", T.RUNOFF_NORMAL)])
def test_the_players_tempo_is_the_clocks_tempo_between_his_plays(tmp_path, setting, span):
    rules = NflRules(timeouts_on=False, offense_book="west", defense_book="classic")
    rig = nfl_engine_rig(tmp_path, rules=rules, **START)
    x = rig.engine.s.extras
    if setting != "normal":
        x.play_settings["tempo"] = setting
    x.left, x.running = 600, True

    class Low:
        @staticmethod
        def below(n):
            return 0
    seconds = rules.clock.runoff(Low, True, False, 0)
    assert seconds == span[0]
    rig.engine.s.wisoff = 2                                     # the computer's offense keeps its own tempo
    assert rules.clock.runoff(Low, True, False, 0) == T.RUNOFF_NORMAL[0]


def test_the_kneel_and_the_spike_take_their_own_live_time():
    from nfl4.game.outcome import PlayOutcome

    class Low:
        @staticmethod
        def below(n):
            return 0
    kneel = PlayOutcome("run", 1, 1, 2, catalog="O152")
    spike = PlayOutcome("pass incomplete", 1, 4, 2, catalog="O153")
    assert CK.live_time(kneel, None, Low) == T.LIVE_KNEEL[0] and CK.live_time(spike, None, Low) == T.LIVE_SPIKE[0]


# ----- the keys -----

def test_the_new_keys_are_in_f5_and_f6_while_a_playbook_is_used_and_never_in_classic():
    rules = NflRules(timeouts_on=True, offense_book="west", defense_book="classic", playbooks_on=True)
    f5 = " ".join(rules.extra_help(K.KEY_F5))
    f6 = " ".join(rules.extra_help(K.KEY_F6))
    for row_id in ("right", "plus_minus", "play_letters", "find"):
        row = K.BY_ID[row_id]
        assert row.f5 in f5 and row.keys in f6, row_id
    classic = " ".join(CLASSIC.extra_help(K.KEY_F5) + CLASSIC.extra_help(K.KEY_F6))
    assert "Plus and Minus" not in classic and "Right." not in classic
    plain = NflRules(timeouts_on=True, offense_book="classic", defense_book="classic", playbooks_on=False)
    assert K.BY_ID["plus_minus"].f5 not in " ".join(plain.extra_help(K.KEY_F5))
