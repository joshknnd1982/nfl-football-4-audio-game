"""How much the radio crew talks (nfl4 only, rule 0.13; S-D, D-193). This is inspired by Jim Kitchen.

The owner on 0.16.8: "the new sports commentators are not talking enough even though comments are turned on. Make them talk more", and "add a
working menu option which lets the user control how much the sports commentators talk". So: F9, Rules, How much the crew talks, with four
levels (a little, some, a lot, the most; a lot is the default), the analyst's lines after ordinary plays (CRG, CRS, CPC, CPI, CPT, CKR), and
more of Walt's asides at the dead balls the analyst leaves. What is tested: the level "a little" keeps 0.16.8's rates (its whole games are
0.16.8's word for word: work\\sd_talk_1027\\measure_talk.py); each level talks more than the one before and none changes the game; the
ordinary plays find their pools; the level is the player's setting, read at every line, so a change in F9 applies at once; settings.txt keeps
it; the Rules item goes round, saves at once and says so; F6 names it.
"""
import logging
import random
from types import SimpleNamespace

import pytest

from nfl4.data import settingsfile
from nfl4.data.settings import Settings
from nfl4.extras import broadcast as BC
from nfl4.extras import nx_texts as X
from nfl4.extras import remarks as RM
from nfl4.extras.classic_radio import ClassicRadioRules
from nfl4.extras.nfl_rules import rules_from_settings
from nfl4.game import outcome as O
from nflrig import QUARTERBACKS, RecordingRules, SimEngine
from pagrig import make_rig
from programrig import DOWN, ENTER, ESC, said
from test_functions import rig_for

LEFT, RIGHT = 37, 39
OLD_CHANCE = {"CKO": 100, "CTD": 60, "CFG": 30, "CFM": 40, "CTV": 45, "CBG": 30, "CSK": 20, "CTC": 8, "CTS": 8, "CFD": 40, "CRZ": 15,
              "CPN": 15, "CTM": 45, "CQE": 35, "CHT": 100, "CFN": 100, "CFT": 100, "CTT": 35, "CBO": 25}      # 0.16.8's broadcast.CHANCE


# ----- the levels -----

def test_a_little_keeps_the_rates_of_0_16_8_and_has_no_lines_after_ordinary_plays():
    t = BC.TALK_LEVELS["little"]
    assert {pool: t.chance[pool] for pool in OLD_CHANCE} == OLD_CHANCE
    assert all(t.chance[pool] == 0 for pool in BC.PLAIN_POOLS)
    assert (t.min_gap, t.ask, t.aside_one_in, t.aside_gap, t.network_every, t.score_after, t.score_one_in) == (4, 25, 8, 4, 420, 360, 2)


def test_each_level_lets_the_crew_talk_at_least_as_much_as_the_one_before():
    levels = [BC.TALK_LEVELS[key] for key in BC.TALK_ORDER]
    assert BC.TALK_ORDER == ("little", "some", "lots", "most") and BC.DEFAULT_TALK == "lots"
    for low, high in zip(levels, levels[1:]):
        assert all(high.chance[pool] >= low.chance[pool] for pool in low.chance), (low.key, high.key)
        assert high.min_gap <= low.min_gap and high.aside_one_in <= low.aside_one_in and high.aside_gap <= low.aside_gap
        assert high.network_every <= low.network_every and high.score_after <= low.score_after
    assert set(levels[0].chance) == set(RM.ANALYST_POOLS) and all(set(t.chance) == set(levels[0].chance) for t in levels)
    assert [BC.talk_words(key) for key in BC.TALK_ORDER] == ["a little", "some", "a lot", "the most"]


@pytest.mark.parametrize("value, key", [("lots", "lots"), ("Most", "most"), ("a lot", "lots"), ("A Little", "little"), ("the most", "most"),
                                        ("some", "some"), ("loud", None), ("", None)])
def test_the_level_is_read_from_a_word(value, key):
    assert BC.talk_key(value) == key


def test_the_levels_go_round_both_ways():
    assert BC.next_talk("lots", 1) == "most" and BC.next_talk("most", 1) == "little"
    assert BC.next_talk("little", -1) == "most" and BC.next_talk("some", -1) == "little"


# ----- the analyst after an ordinary play -----

def facts(kind, yards=0, turnover=False, score=None):
    return SimpleNamespace(kind=kind, yards=yards, turnover=turnover, score=score)


@pytest.mark.parametrize("f, pool", [
    (facts(O.RUN, 4), "CRG"), (facts(O.RUN, 15), "CRG"), (facts(O.RUN, 3), "CRS"), (facts(O.RUN, -2), "CRS"),
    (facts(O.PASS_COMPLETE, 9), "CPC"), (facts(O.PASS_COMPLETE, -1), None), (facts(O.PASS_INCOMPLETE), "CPI"),
    (facts(O.PUNT, 44, turnover=True), "CPT"), (facts(O.PUNT, 40), None),                  # a muff the kicking team kept has no line
    (facts(O.KICKOFF_RETURN, 25), "CKR"), (facts(O.KICKOFF_TOUCH_BACK), "CKR"), (facts(O.ONSIDE_KICK), None),
    (facts(O.RUN, 12, score="touchdown"), None), (facts(O.RUN, 2, turnover=True), None), (facts(O.KICKOFF_RETURN, 9, turnover=True), None),
    (facts(O.FIELD_GOAL_GOOD), None), (facts(O.SAFETY_KIND), None)])
def test_an_ordinary_play_finds_its_pool_and_a_little_finds_none(f, pool):
    b = BC.Broadcast(None, analyst=True, talk="lots")
    assert b._plain_pool(f) == pool
    b.talk_level = "little"
    assert b._plain_pool(f) is None


# ----- whole games -----

def whole_game(tmp_path, seed, level, broadcast=True):
    pools = []
    real = BC.Broadcast._line

    def spy(self, state, pool, values, say):
        said_line = real(self, state, pool, values, say)
        if said_line is not None:
            pools.append(pool)
        return said_line
    rig = make_rig(tmp_path, rng=random.Random(seed), fast=True, vtrnt=2, gtp=1)
    rig.game.options.settings.game.nx_crew_talk = level
    rig.game.comtog_source = lambda: 0
    rules = RecordingRules(penalties_on=True, onside_on=True, qb_on=True, challenges_on=True, playbooks_on=True, broadcast_on=broadcast)
    engine = SimEngine(rig.game, rules, quarterback_names=lambda state: QUARTERBACKS)
    rig.game.play_engine = engine
    BC.Broadcast._line = spy
    try:
        result = engine.run()
    finally:
        BC.Broadcast._line = real
        rig.game.play_engine = None
    return rig, result, pools


def test_each_level_talks_more_than_the_one_before_and_none_changes_the_game(tmp_path):
    runs = {level: whole_game(tmp_path / level, 22, level) for level in BC.TALK_ORDER}
    counts = [len(runs[level][2]) for level in BC.TALK_ORDER]
    assert counts == sorted(counts) and len(set(counts)) == 4, counts
    analyst = {level: sum(1 for p in runs[level][2] if p in RM.ANALYST_POOLS) for level in BC.TALK_ORDER}
    assert analyst["lots"] >= 2 * analyst["little"], analyst          # the owner: "Make them talk more"
    assert not any(p in BC.PLAIN_POOLS for p in runs["little"][2])     # 0.16.8 had no line after an ordinary play
    assert any(p in BC.PLAIN_POOLS for p in runs["lots"][2])
    first = runs["little"]
    for level in BC.TALK_ORDER:
        rig, result, _pools = runs[level]
        assert result.scores == first[1].scores and rig.rnd.draws == first[0].rnd.draws   # the crew draws only from its own generator


def test_the_default_is_a_lot(tmp_path):
    assert Settings.defaults().game.nx_crew_talk == "lots"
    rig, _result, pools = whole_game(tmp_path, 23, Settings.defaults().game.nx_crew_talk)
    gus = sum(1 for p in pools if p in RM.ANALYST_POOLS)
    assert gus >= 40, gus                    # the analyst after about one play in two (0.16.8: 14 to 23 a game)


def test_with_the_broadcast_item_off_walt_still_talks_more_at_a_higher_level(tmp_path):
    little = whole_game(tmp_path / "a", 24, "little", broadcast=False)[2]
    most = whole_game(tmp_path / "b", 24, "most", broadcast=False)[2]
    assert not any(p in RM.ANALYST_POOLS or p in RM.SIDELINE_POOLS for p in little + most)
    assert most.count("BN") > little.count("BN")


# ----- the setting: read at every line, kept in settings.txt, carried by the rules -----

def test_a_change_in_f9_applies_at_once_in_the_game_being_played(caplog):
    settings = Settings.defaults()
    game = SimpleNamespace(options=SimpleNamespace(settings=settings), comtog=0)
    b = BC.Broadcast(None, analyst=True, talk="little")
    b.game = game
    with caplog.at_level(logging.INFO, logger="nfl4.extras"):
        assert b.talk().key == "lots"                       # the player's setting wins over the object's own
        settings.game.nx_crew_talk = "most"
        assert b.talk().key == "most"
        assert b.talk().key == "most"
    told = [r.getMessage() for r in caplog.records if "the crew talks" in r.getMessage()]
    assert told == ["broadcast: the crew talks a lot (lots)", "broadcast: the crew talks the most (most)"]   # the log says each change once
    b.game = None
    assert b.talk().key == "little"                         # a hand-made object without settings: its own


@pytest.mark.parametrize("level", BC.TALK_ORDER)
def test_settings_txt_keeps_the_level(level):
    settings = Settings.defaults()
    settings.game.nx_crew_talk = level
    text = settingsfile.render(settings)
    assert "nx_crew_talk = %s\n" % level in text
    again, problems = settingsfile.parse(text)
    assert again.game.nx_crew_talk == level and problems == []


def test_a_bad_level_is_a_problem_and_keeps_the_default_and_an_old_file_gets_a_lot():
    settings, problems = settingsfile.parse(settingsfile.HEADER + "nx_crew_talk = loud\n")
    assert settings.game.nx_crew_talk == "lots" and len(problems) == 1
    settings, problems = settingsfile.parse(settingsfile.HEADER + "nx_crew_talk = the most\n")
    assert settings.game.nx_crew_talk == "most" and problems == []
    settings, problems = settingsfile.parse(settingsfile.HEADER + "nx_broadcast = on\n")      # a file of 0.16.8
    assert settings.game.nx_crew_talk == "lots" and problems == []


@pytest.mark.parametrize("rules", ["nfl", "classic"])
def test_the_program_rules_carry_the_level_in_both_modes(rules):
    settings = Settings.defaults()
    settings.game.rules, settings.game.nx_crew_talk = rules, "some"
    made = rules_from_settings(settings.game)
    assert made.broadcast.talk_level == "some" and made.for_game().broadcast.talk_level == "some"
    assert ClassicRadioRules().broadcast.talk_level == "lots"


def test_f6_names_the_item_in_both_modes():
    assert "How much the crew talks" in X.text("NXH-83")
    assert X.text("NXH-83") in ClassicRadioRules().extra_help("117")
    settings = Settings.defaults()
    assert X.text("NXH-83") in rules_from_settings(settings.game).extra_help("117")


# ----- the F9 Rules item -----

def rules_menu(rig, keys):
    """F9, Rules, down to the eleventh item (How much the crew talks: Rules, then ten Downs), then the keys."""
    rig.keys.answers = [DOWN, DOWN, DOWN, ENTER] + [DOWN] * 10 + keys + [ESC, ESC]
    rig.game.functions.run()
    spoken = said(rig)
    return spoken[4 + 10:]                   # the menu opens on item 1 (spoken[4]); ten Downs reach item 11


def test_the_rules_item_goes_round_saves_at_once_and_says_it_applies_now(tmp_path):
    rig = rig_for(tmp_path, [])
    game = rig.game.options.settings.game
    spoken = rules_menu(rig, [ENTER, ENTER, ENTER, LEFT, RIGHT, ENTER])
    now = X.text("NXM-69")
    assert spoken[0] == "How much the crew talks: a lot"
    assert spoken[1:4] == ["How much the crew talks: the most," + now, "How much the crew talks: a little," + now,
                           "How much the crew talks: some," + now]
    assert spoken[4:6] == ["How much the crew talks: a little", "How much the crew talks: some"]
    assert spoken[6] == "How much the crew talks: a lot," + now
    assert game.nx_crew_talk == "lots" and rig.saves.count == 6
    assert "nx_crew_talk = lots" in settingsfile.render(rig.game.options.settings)
