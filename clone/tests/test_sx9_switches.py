"""Every switch of the F9 Rules menu on and off, in a quick game, a classic season with the N. F. L. rules and a franchise (nfl4 only, rule
0.13; NFL_EXTRA_FEATURES C1, C3, C4, C8 and section 14 SX.9). This is inspired by Jim Kitchen.

* Quick games: all 64 combinations of the six switches (time outs, penalties, onside kicks, quarterback runs, replay challenges, the
  player's playbooks), the onside question "always" in half of them: every game ends with a winner, the extras record is whole, and a
  switch that is off leaves no event, no statistic line, no word and no menu item of its feature; a switch that is on is heard in its
  statistics lines.
* The program: a classic season with the N. F. L. rules and a franchise, each week's game played by the real engine (both sides by the
  computer's rules, as work/full_sx8f.py does) with the program's own settings, for combinations of the switches: the same properties
  game by game; injuries only in the franchise (INJ-1).
* Rules = Classic: the new player's default is the N. F. L. rules (NQ2); a settings file that says classic plays the original: no extras
  record, no word of the extras or of the Franchise, no extras file read (the golden transcript is tests/test_pag_golden.py).
"""
import itertools

import pytest

from frrig import COACH_AND_TEAM, ENTER, WANT_CLASSIC, WANT_FRANCHISE, enter_until, franchise_rig, run_until, spoken
from nfl4.data.settings import GameSettings, Settings
from nfl4.extras import nx_texts as X
from nfl4.extras import rules_menu
from nfl4.extras.nfl_rules import NflRules, is_nfl, rules_from_settings
from nfl4.extras.playbook_flow import PlaybookFlow
from nfl4.game.rules import CLASSIC
from nflrig import RecordingRules, SimEngine, sim_game

SWITCHES = ("timeouts", "penalties", "onside", "qb", "challenges", "playbooks")
COMBOS = list(itertools.product((False, True), repeat=len(SWITCHES)))
GAME = [ENTER, ENTER, ENTER]                  # the main menu's play game, the results, the standings


def feature_lines(rules, state):
    """The statistics lines of each feature (H11), keyed by switch."""
    x = state.extras
    return {"penalties": rules.penalty.stats_lines(state) if x.penalties_on else [],
            "challenges": rules.review.stats_lines(state) if x.challenges_on else [],
            "qb": rules.qb.stats_lines(state) if x.qb_on else []}


def check_game(engine, rules, on, said, quick=True):
    """The properties of one finished game with the switches `on` (a dict of SWITCHES)."""
    s, x = engine.s, engine.s.extras
    x.check()
    assert engine.result.scores is not None and engine.result.scores[0] != engine.result.scores[1]
    assert (x.timeouts_on, x.penalties_on, x.onside_on, x.qb_on, x.challenges_on) == \
        (on["timeouts"], on["penalties"], on["onside"], on["qb"], on["challenges"])
    lines = rules.extra_stats_lines(s)
    assert (X.text("NXS-03") in lines) == on["timeouts"]
    assert (X.text("NXS-01") in lines) == on["penalties"]
    assert (X.text("NXS-06") in lines) == on["onside"]
    for name, own in feature_lines(rules, s).items():
        assert bool(own) == on[name] and all(line in lines for line in own)
    if not on["timeouts"]:
        assert not any(t.startswith(X.text("NXT-01", team="")[:20]) for t in said)
        if quick:
            assert rules.timeouts == []
    if not on["penalties"]:
        assert rules.penalty.events == [] and x.flags == [0, 0] and X.text("NXP-01") not in said
    if not on["onside"]:
        assert x.onside_tried == [0, 0] and x.onside_recovered == [0, 0]
        if quick:
            assert rules.onsides == []
    if not on["qb"]:
        assert rules.qb.events == [] and x.qb_runs == [0, 0]
        assert not any(t.strip() == X.text("NXM-01").strip() for t in said)
    if not on["challenges"]:
        assert rules.review.events == [] and rules.review.rulings == [] and x.chal_used == [0, 0]
    if not on["playbooks"]:
        assert x.offense_book[0] == "classic" and x.defense_book[0] == "classic"
        if quick:
            assert not PlaybookFlow.in_use(x)


# ----- quick games: all 64 combinations -----

@pytest.mark.parametrize("combo", COMBOS, ids=["".join("1" if v else "0" for v in c) for c in COMBOS])
def test_every_combination_of_the_switches_in_a_quick_game(tmp_path, combo):
    on = dict(zip(SWITCHES, combo))
    seed = 5000 + COMBOS.index(combo)
    book = "team" if on["playbooks"] else "classic"
    rules = RecordingRules(timeouts_on=on["timeouts"], penalties_on=on["penalties"], onside_on=on["onside"],
                           onside_always=on["onside"] and seed % 2 == 0, qb_on=on["qb"], challenges_on=on["challenges"],
                           offense_book=book, defense_book=book, playbooks_on=on["playbooks"])
    rig, engine, rules, result = sim_game(tmp_path, seed, rules=rules)
    assert rig.rnd.fallbacks == 0 and engine.noise_net == 0
    said = [t for t, _, _ in rig.said]
    check_game(engine, rules, on, said)
    if on["onside"] and seed % 2 == 0:
        assert engine.s.extras.onside_always
    menu = [item.text for item in rules.offense_menu(engine.s, False)]
    assert any(X.text("NXM-05").strip() in t for t in menu) == on["timeouts"]
    assert any(X.text("NXM-06").strip() in t for t in menu)                    # Save Game is always the last item
    if not on["playbooks"]:
        assert any(X.text("NXM-01").strip() in t for t in menu) == on["qb"]


# ----- the program: a classic season with the N. F. L. rules and a franchise, real games -----

PROGRAM_COMBOS = [
    dict(timeouts=True, penalties=True, onside=True, qb=True, challenges=True, playbooks=True),
    dict(timeouts=False, penalties=False, onside=False, qb=False, challenges=False, playbooks=False),
    dict(timeouts=True, penalties=False, onside=True, qb=False, challenges=True, playbooks=False),
    dict(timeouts=False, penalties=True, onside=False, qb=True, challenges=False, playbooks=True),
    dict(timeouts=False, penalties=True, onside=True, qb=True, challenges=True, playbooks=True),
    dict(timeouts=True, penalties=True, onside=False, qb=False, challenges=False, playbooks=False),
]


def real_games(rig, played):
    """The rig's stand-in pag replaced by the real engine with both sides by the computer's rules (work/full_sx8f.py), the program's rules."""
    game = rig.game

    def play_game(rules=None, own_names=None, saved=None, quarterback_names=None, save_sink=None, roster_sink=None, opponent_names=None,
                  game_injuries=None, **ignored):
        rules = (rules or rules_from_settings(game.options.settings.game, auto_sides=(1, 2))).for_game()
        rules.auto_sides = (1, 2)
        engine = SimEngine(game, rules, own_names=own_names, saved=saved, quarterback_names=quarterback_names, save_sink=save_sink,
                           roster_sink=roster_sink, opponent_names=opponent_names)
        game.play_engine, game.game_injuries = engine, game_injuries
        start = len(rig.said)
        try:
            result = engine.run()
        finally:
            game.play_engine, game.game_injuries = None, None
        played.append((engine, rules, [t for t, _, _ in rig.said[start:]], game_injuries))
        if result.scores is not None:
            game.m414 = result.scores
        return result
    game.play_game = play_game


def season_with(tmp_path, on, kind):
    played = []
    want = WANT_FRANCHISE if kind == "franchise" else WANT_CLASSIC

    def setup(settings):
        settings.nx_timeouts, settings.nx_penalties, settings.nx_onside = on["timeouts"], on["penalties"], on["onside"]
        settings.nx_qb_runs, settings.nx_challenges = on["qb"], on["challenges"]
        settings.nx_offense_playbook = settings.nx_defense_playbook = "team" if on["playbooks"] else "classic"
    rig = franchise_rig(tmp_path, want + COACH_AND_TEAM + GAME * 2, policy=enter_until(lambda: len(played) >= 2))
    setup(rig.game.options.settings.game)
    rig.game.apply_rules_setting()
    real_games(rig, played)
    run_until(rig)
    return rig, played


@pytest.mark.parametrize("kind", ["classic season", "franchise"])
@pytest.mark.parametrize("which", range(len(PROGRAM_COMBOS)))
def test_the_switches_in_the_programs_classic_season_and_franchise_games(tmp_path, kind, which):
    on = PROGRAM_COMBOS[which]
    rig, played = season_with(tmp_path, on, kind)
    assert len(played) >= 2
    for engine, rules, said, injuries in played:
        check_game(engine, rules, on, said, quick=False)
        if kind == "franchise":
            assert injuries is not None and engine.s.extras.injuries is not None
        else:
            assert injuries is None and engine.s.extras.franchise is None and engine.s.extras.injuries is None
            assert not any(t.startswith(X.text("NXI-01")[:15]) for t in said)
    if kind != "franchise":
        assert rig.fstore is None or rig.fstore.league is None


# ----- Rules = Classic and the new player's default (NQ2) -----

def test_a_new_players_settings_say_the_nfl_rules_with_every_switch_on_and_classic_is_one_setting_away():
    settings = Settings.defaults().game
    assert settings.rules == "nfl" and GameSettings().rules == "nfl"
    rules = rules_from_settings(settings)
    assert is_nfl(rules)
    assert (rules.timeouts_on, rules.penalties_on, rules.onside_on, rules.qb_on, rules.challenges_on, rules.onside_always) == \
        (True, True, True, True, True, True)         # SX.2b, D-085: the onside question is asked at every kick
    assert rules_menu.DEFAULTS["rules"] == "nfl" and rules_menu.DEFAULTS["nx_offense_playbook"] == "classic"
    settings.rules = "classic"
    assert rules_from_settings(settings) is CLASSIC


def test_a_settings_file_without_the_rules_line_gets_the_nfl_rules_and_one_that_says_classic_keeps_it():
    from nfl4.data import settingsfile
    loaded, _ = settingsfile.parse("comments = on\n")
    assert loaded.game.rules == "nfl"
    loaded, _ = settingsfile.parse("rules = classic\n")
    assert loaded.game.rules == "classic"
    assert "rules = nfl" in settingsfile.render(Settings.defaults())


def test_with_rules_classic_a_season_says_nothing_of_the_extras_or_the_franchise(tmp_path):
    rig = franchise_rig(tmp_path, COACH_AND_TEAM + GAME * 2, nfl=False, policy=enter_until(lambda: rig.game.season.gtp == 3))
    run_until(rig)
    assert not is_nfl(rig.game.rules) and rig.game.options.settings.game.rules == "classic"
    # every text of the extras, cut at its first placeholder, is never part of anything said (a piece of 12 letters or more)
    pieces = {t.split("<")[0].strip() for t in X.TEXTS.values()}
    pieces = {p for p in pieces if len(p) >= 12}
    assert not [(p, t) for t in spoken(rig) for p in pieces if p in t]
    assert rig.game._franchise_store is None and rig.files.data == {}
    customization = rig.game.customization
    assert customization is None or not customization.extras


# ----- the player's own side (the review of SX.9): the prompts, the questions and the menus are met by a seeded player -----

PLAYER_COMBOS = [c for i, c in enumerate(COMBOS) if i % 8 == 3 or c in ((True,) * 6, (False,) * 6)]


@pytest.mark.parametrize("combo", PLAYER_COMBOS, ids=["".join("1" if v else "0" for v in c) for c in PLAYER_COMBOS])
def test_the_switches_with_the_player_answering_his_own_prompts_questions_and_menus(tmp_path, combo):
    import random
    from pagrig import make_rig, play
    from test_nx_penalty_games import player_policy
    on = dict(zip(SWITCHES, combo))
    seed = 7000 + COMBOS.index(combo)
    book = "team" if on["playbooks"] else "classic"
    rig = make_rig(tmp_path, rng=random.Random(seed), fast=True, vtrnt=1 + seed % 2)
    rig.keys.policy = player_policy(rig, seed + 1)
    program = RecordingRules(auto_sides=(2,), timeouts_on=on["timeouts"], penalties_on=on["penalties"], onside_on=on["onside"],
                             onside_always=on["onside"], qb_on=on["qb"], challenges_on=on["challenges"], offense_book=book,
                             defense_book=book, playbooks_on=on["playbooks"])
    result = play(rig, rules=program)
    rules = program.used
    said = [t for t, _, _ in rig.said]
    assert result.scores is not None and result.scores[0] != result.scores[1] and rig.rnd.fallbacks == 0
    x = rules.state.extras
    x.check()
    question = X.text("NXO-01", coach=rig.game.season.coach)
    menu = X.text("NXB-J01", coach=rig.game.season.coach)
    # "always": the player is asked at his kick-offs; with a playbook (SX.10d) the 2026 kick-off menu is asked instead, at every kick-off,
    # its fourth item the onside kick only with the switch on
    assert (question in said) == (on["onside"] and not on["playbooks"])
    assert (menu in said) == on["playbooks"]
    assert (" 4. Onside Kick " in said) <= on["onside"]
    if not on["penalties"]:
        assert X.text("NXP-01") not in said and rules.penalty.events == []
    if not on["challenges"]:
        assert rules.review.events == [] and x.chal_used == [0, 0]
    if not on["qb"]:
        assert x.qb_runs == [0, 0]
    if not on["timeouts"]:
        assert rules.timeouts == []
    if on["playbooks"]:
        assert x.offense_book[0] != "classic" or x.defense_book[0] != "classic"
    else:
        assert x.offense_book[0] == x.defense_book[0] == "classic"
