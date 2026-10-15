"""The foul table and the penalties' rule values against the 2026 rulebook and the design (nfl4 only, rule 0.13;
NFL_EXTRAS_DESIGN 9.2, NFL_RULES_RESEARCH Part 6 and 7; PX SX.3). This is inspired by Jim Kitchen.

Every row is checked against the design's row (its ID, offender, yards, spot) and the rules table's lists; the spoken names
against STRINGS_NX; the rates against the design's start values (the calibration scales them all alike).
"""
import re
from pathlib import Path

import pytest

from nfl4.extras import fouls_2026 as F
from nfl4.extras import nx_texts as X
from nfl4.extras import rules_2026 as R
from nfl4.extras import tuning as T
from nfl4.game import outcome as O

DESIGN = Path(__file__).resolve().parents[2] / "spec" / "NFL_EXTRAS_DESIGN.md"

# the design's rows (9.2): ID -> (offender, yards); yards 0 for the spot foul
EXPECTED = {
    "P01": ("offense", 5), "P02": ("offense", 5), "P03": ("defense", 5), "P04": ("defense", 5), "P05": ("defense", 5),
    "P06": ("offense", 5), "P07": ("offense", 5), "P08": ("offense", 10), "P09": ("defense", 5), "P10": ("defense", 5),
    "P11": ("defense", 5), "P12": ("defense", 0), "P13": ("offense", 10), "P14": ("defense", 15), "P15": ("offense", 10),
    "P16": ("offense", 5), "P17": ("either", 15), "P18": ("either", 15), "P19": ("offense or receiving", 10),
    "P20": ("defense", 15), "P21": ("either", 15), "P22": ("defense", 5), "P23": ("defense", 15), "P24": ("kicking", 5),
    "P25": ("receiving", 10), "P26": ("defense", 5), "P33": ("kicking", 5),
}


def test_the_ids_are_the_designs_rows_and_p27_to_p32_are_kept_free():
    design_ids = sorted(set(re.findall(r"^- (P\d\d) ", DESIGN.read_text(encoding="utf-8"), flags=re.M)))
    assert list(F.IDS) == design_ids == sorted(EXPECTED)
    assert not any("P%02d" % n in F.BY_ID for n in range(27, 33))


@pytest.mark.parametrize("foul_id", sorted(EXPECTED))
def test_each_row_has_the_designs_offender_and_yards(foul_id):
    offender, yards = EXPECTED[foul_id]
    rows = F.BY_ID[foul_id]
    offenders = {row.offender for row in rows}
    if offender == "either":
        assert offenders == {F.OFFENSE, F.DEFENSE}
    elif offender == "offense or receiving":
        assert offenders == {F.OFFENSE, F.RECEIVING}
    else:
        assert offenders == {offender}
    assert {row.yards for row in rows} == {yards}
    assert all(row.rule for row in rows)


def test_the_automatic_first_down_follows_14_1_2_item_5():
    no_first_down = {f.id for f in F.FOULS if f.offender == F.DEFENSE and not f.automatic_first_down}
    assert no_first_down == {"P03", "P04", "P05", "P22", "P26"}      # offside, neutral zone, encroachment, RNK, 12 men
    assert set(R.NO_AUTOMATIC_FIRST_DOWN) >= {"DOF", "ENC", "NZI", "DOG", "RNK", "DTM"}
    assert not any(f.automatic_first_down for f in F.FOULS if f.offense_side or f.offender == F.KICKING)


def test_the_spots_loss_of_down_and_personal_fouls():
    spot = {f.id: f.spot for f in F.FOULS}
    assert spot["P12"] == F.SPOT_OF_FOUL and spot["P15"] == F.PASS_SPOT and spot["P14"] == F.BETTER_OF
    assert {f.id for f in F.FOULS if f.loss_of_down} == {"P15"}
    assert {f.id for f in F.FOULS if f.personal} == {"P14", "P17", "P18", "P20", "P21", "P23"}
    assert {f.id for f in F.FOULS if F.DEAD in f.phases} == {"P01", "P02", "P04", "P05"}
    assert {f.id for f in F.FOULS if F.SNAP in f.phases} == {"P03", "P06", "P07", "P26"}
    assert {f.id for f in F.FOULS if F.AFTER in f.phases} == {"P18", "P21"}
    assert {f.id for f in F.FOULS if f.team_foul} == {"P02", "P26"}


def test_the_rates_are_the_designs_start_values_and_either_rows_split_them():
    rate = {}
    for f in F.FOULS:
        rate[f.id] = rate.get(f.id, 0) + f.rate
    assert rate["P01"] == 2.0 and rate["P08"] == 2.0 and rate["P09"] == 0.9
    assert rate["P17"] == pytest.approx(0.38) and rate["P18"] == pytest.approx(0.54) and rate["P21"] == pytest.approx(0.17)
    assert rate["P12"] == 3.75                                        # 1.5 per pass, on the 40 percent not caught
    assert rate["P15"] == 0.0 and T.GROUNDING_PER_10000_SACKS > 0      # grounding only in place of a sack
    defense_share = sum(f.rate for f in F.BY_ID["P17"] if f.offender == F.DEFENSE) / rate["P17"]
    assert defense_share == pytest.approx(0.8)


def test_every_foul_has_its_spoken_name_in_strings_nx_and_p25_shares_holding():
    for foul_id in F.IDS:
        assert F.name_id(foul_id) in X.TEXTS and X.KINDS[F.name_id(foul_id)] == "foul"
    assert F.name_id("P25") == F.name_id("P08") == "NXP-F08"


def test_the_pre_snap_and_live_rows_cover_every_kind_of_play():
    for kind in (O.RUN, O.PASS_COMPLETE, O.PASS_INCOMPLETE, O.SACK, O.INTERCEPTION, O.PUNT, F.FIELD_GOAL,
                 O.KICKOFF_RETURN, O.KICKOFF_TOUCH_BACK):
        assert any(kind in f.phases for f in F.FOULS), kind


def test_the_rates_of_a_play_stay_far_below_one_draw_of_10000():
    worst = max((sum(f.rate for f in F.FOULS if kind in f.phases or F.AFTER in f.phases) for kind in
                 (O.RUN, O.PASS_INCOMPLETE, O.PASS_COMPLETE)), default=0)
    assert worst * 100 * T.PENALTY_RATE_SCALE * 2 * 3 < 10000         # weight 200 and the Long Pass factor included
