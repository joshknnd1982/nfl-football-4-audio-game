"""The replay challenges beside the other extras and the player's files: the settings line, the F9 item, the saved record, the
remark pools of remarks.txt, the menu with every item on, the quarterback's counts, the fouls (nfl4 only, rule 0.13;
NFL_EXTRAS_DESIGN 6, 12.1, 12.2, 12.3, CUSTOMIZABLE_CONTENT 13; PX SX.6). This is inspired by Jim Kitchen.
"""
import pytest

from nfl4.data import settingsfile
from nfl4.data.settings import Settings
from nfl4.data.customlists import Problems
from nfl4.extras import nx_texts as X
from nfl4.extras import remarks as RM
from nfl4.extras import review as RV
from nfl4.extras.nfl_rules import NflRules, is_nfl, rules_from_settings
from nfl4.extras.state import ExtrasRecord
from nfl4.game import outcome as O
from nfl4.game.gamestate import GameState
from nfl4.game.rules import CLASSIC, REVIEWED_FIELD
from pagrig import Draws, run_steps
from programrig import ENTER
from test_nx_remarks import entries_of
from test_nx_review_plays import RUN, TD, feed, rule, scene, texts, throw, used_up
from test_nx_settings import NEXT_GAME, rules_menu
from test_functions import rig_for


# ----- the settings -----

def test_the_settings_read_and_write_the_replay_challenges_line():
    settings, problems = settingsfile.parse(settingsfile.HEADER + "nx_challenges = off\n")
    assert problems == [] and settings.game.nx_challenges is False
    again, problems = settingsfile.parse(settingsfile.render(settings))
    assert problems == [] and again.game == settings.game
    assert "nx_challenges = off" in settingsfile.render(settings).splitlines()
    assert Settings.defaults().game.nx_challenges is True
    assert "nx_challenges" in settingsfile.HEADER


def test_a_bad_replay_challenges_value_is_a_problem_and_keeps_the_default():
    settings, problems = settingsfile.parse(settingsfile.HEADER + "nx_challenges = sometimes\n")
    assert len(problems) == 1 and settings.game.nx_challenges is True


def test_the_programs_rules_follow_the_replay_challenges_setting():
    settings = Settings.defaults()
    settings.game.rules = "nfl"
    rules = rules_from_settings(settings.game)
    assert is_nfl(rules) and rules.challenges_on is True and rules.for_game().challenges_on is True
    settings.game.nx_challenges = False
    rules = rules_from_settings(settings.game)
    assert rules.challenges_on is False and rules.for_game().challenges_on is False
    settings.game.rules = "classic"
    assert rules_from_settings(settings.game) is CLASSIC
    assert NflRules().challenges_on is False                      # a rules object made by hand has none


def test_the_extras_record_of_a_game_has_the_switch_the_game_was_made_with(tmp_path):
    rig, record = scene(tmp_path, RUN, yards=4, down=3, to_go=5)
    assert rig.engine.s.extras.challenges_on is True
    off = type(rig.rules)(timeouts_on=False)
    assert off.for_game().challenges_on is False


# ----- the F9 item -----

def test_replay_challenges_is_the_third_item_of_the_rules_menu_and_every_change_is_saved(tmp_path):
    rig = rig_for(tmp_path, [])
    spoken = rules_menu(rig, ["3", ENTER])
    assert spoken[1] == "Replay challenges on  used with the N. F. L. rules "
    assert spoken[2] == "Replay challenges off  used with the N. F. L. rules " + NEXT_GAME
    assert rig.game.options.settings.game.nx_challenges is False


# ----- the saved game -----

def test_the_saved_record_holds_the_switch_and_the_counts_and_loads_back(tmp_path):
    rig, record = scene(tmp_path, RUN, yards=4, down=3, to_go=5, extras={"chal_used": [2, 1], "chal_won": [1, 0]})
    saved = rig.engine.s.saved(100.0)
    assert saved.extras is not None
    loaded = ExtrasRecord.from_json(saved.extras)
    assert (loaded.challenges_on, loaded.chal_used, loaded.chal_won) == (True, [2, 1], [1, 0])
    fresh = GameState()
    fresh.extras = ExtrasRecord(challenges_on=False)
    fresh.load(saved)
    assert (fresh.extras.challenges_on, fresh.extras.chal_used, fresh.extras.chal_won) == (True, [2, 1], [1, 0])


def test_a_loaded_game_has_no_ruling_to_challenge(tmp_path):
    """The ruling of the last play and its board are not saved (design 12.3 as built): a new rules object has none."""
    rules = NflRules(timeouts_on=False, challenges_on=True)
    assert rules.review.pending is None and rules.review.replaying is False


# ----- the remark pools -----

def test_the_four_pools_are_commentary_and_f8_silences_them():
    assert {"CHS", "CHC", "RVR", "RVC"} <= RM.COMMENTARY_POOLS and not {"CHS", "CHC", "RVR", "RVC"} & RM.PLAY_BY_PLAY_POOLS
    notes = " ".join(RM.NOTES)
    assert "CHS" in notes and "RVC03" in notes and "replay pools" in notes


def pools_of(text):
    problems = Problems("remarks.txt")
    return RM.build_pools(RM.overrides_of(entries_of(text), problems), problems), problems


def test_a_line_of_the_replay_pools_is_changed_switched_off_or_added_with_its_placeholders():
    pools, problems = pools_of("CHS02 = <team> is not happy [bleep]\nCHC01 = off\nRVR04 = <coach> was right\nRVC03 = off\n"
                               "RVC05 = <score> is nothing\n")
    assert [r.id for r in pools.lines("CHS")] == ["CHS01", "CHS02", "CHS03", "CHS04"]
    assert [r.id for r in pools.lines("CHC")] == ["CHC02", "CHC03"]
    assert [r.id for r in pools.lines("RVR")] == ["RVR01", "RVR02", "RVR03", "RVR04"]
    assert [r.id for r in pools.lines("RVC")] == ["RVC01", "RVC02", "RVC05"]
    assert problems.count == 1 and "<score>" in problems.messages[0]
    assert RM.parse_id("rvc3") == ("RVC", 3) and RM.parse_id("RVC0") is None


def test_a_lost_challenge_draws_over_the_pool_the_player_made_and_the_defaults_are_used_for_an_older_file(tmp_path):
    rig, record = scene(tmp_path, RUN, yards=4, down=3, to_go=5, comments=True)
    pools, _ = pools_of("RVC03 = off\nRVC04 = a time out gone, <coach>\n")
    rig.game.remark_pools = pools                                        # RVC01, RVC02, RVC04
    rule(rig, record, Draws().below(1000, 40).below(100, 99))
    assert throw(rig, Draws().rady().rady().rnd(2, 1).rnd(3, 3)) is None
    assert texts(rig)[-1] == "a time out gone, Kim"                       # the player's own line: as written, no outer spaces
    rig.game.remark_pools = None                                          # remarks.txt of an older game: the defaults
    assert rig.game.remark_pools is None and RM.DEFAULT_POOLS.lines("RVC")[2].id == "RVC03"


# ----- every item of the menu at once -----

def test_the_menu_with_every_extra_on_numbers_the_items_and_puts_the_challenge_before_the_time_out(tmp_path):
    rules = NflRules(timeouts_on=True, challenges_on=True, qb_on=True)
    rig, record = scene(tmp_path, RUN, yards=4, down=3, to_go=5)
    rig.engine.s.extras.timeouts_on = rig.engine.s.extras.qb_on = True
    assert rule(rig, record, Draws().below(1000, 999)) is None
    items = rig.rules.offense_menu(rig.engine.s, False)
    assert [(i.text, i.letter) for i in items][6:] == [
        (" 7. Punt ", ""), (" 8. Quarterback Sneak ", ""), (" 9. Quarterback Keeper ", ""), (" 10. Quarterback Draw ", ""),
        (" 11. Challenge the Ruling ", "c"), (" 12. Time Out ", ""), (" 13. Save Game ", "s")]
    assert [i.digit for i in items][7:10] == [8, 9, 0]
    defense = rig.rules.defense_menu(rig.engine.s)
    assert [(i.text, i.letter) for i in defense][6:] == [
        (" 7. Challenge the Ruling ", "c"), (" 8. Time Out ", ""), (" 9. Save Game ", "s")]
    assert isinstance(rules, NflRules)


# ----- the quarterback's runs -----

def test_a_keeper_that_a_challenge_gives_one_more_yard_is_counted_once_with_the_corrected_yards(tmp_path):
    """Third and 5, a keeper of 4 ruled short: the first end point counts it (1 run, 4 yards), the challenge takes the count back
    with the board and the corrected end point counts the run of 5 yards: 1 run, 5 yards, never 2 runs."""
    rig, record = scene(tmp_path, RUN, yards=4, down=3, to_go=5, offense_play=9, defense_play=5, qb_run="keeper",
                        extras={"qb_on": True})
    rig.engine.s.qb_run = "keeper"
    d = Draws().below(4, 0).below(1000, 10).below(100, 0).below(100, 99).rnd(4, 1).below(11, 0)
    assert run_steps(rig, rig.engine.gain_and_end, d) == "next_play"
    x = rig.engine.s.extras
    assert (x.qb_runs, x.qb_yards) == ([1, 0], [4, 0])
    feed(rig, Draws().rady().rady())
    then = rig.rules.review.throw(rig.engine.s, 1, rig.rules.review.pending)
    used_up(rig, Draws().rady().rady())
    assert then == REVIEWED_FIELD and (x.qb_runs, x.qb_yards) == ([0, 0], [0, 0])
    assert run_steps(rig, rig.engine.continuation(then), Draws().below(4, 0).rnd(4, 1).below(11, 0)) == "next_play"
    assert (x.qb_runs, x.qb_yards) == ([1, 0], [5, 0])
    s = rig.engine.s
    assert (s.stats[1].running_plays, s.stats[1].running_yards) == (1, 5)
    assert [(e[2], e[3]) for e in rig.rules.qb.events] == [("keeper", 4), ("keeper", 5)]


def test_a_booth_reversal_of_a_keepers_touchdown_counts_the_run_once(tmp_path):
    rig, record = scene(tmp_path, TD, yards=5, spot=(1, 5), down=1, to_go=5, offense_play=9, defense_play=5, qb_run="keeper",
                        extras={"qb_on": True})
    rig.engine.s.qb_run = "keeper"
    d = Draws().below(4, 0).below(1000, 10).below(100, 0).below(100, 99).rady().rady().below(4, 0).rnd(4, 1).below(11, 0)
    assert run_steps(rig, rig.engine.touchdown_reached, d) == "next_play"
    x = rig.engine.s.extras
    assert (x.qb_runs, x.qb_yards) == ([1, 0], [4, 0])
    assert [(o.kind, o.qb_run, o.yards) for o in rig.engine.outcomes] == [(O.TOUCHDOWN, "keeper", 5), (O.RUN, "keeper", 4)]
