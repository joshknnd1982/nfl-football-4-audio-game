"""SR.7 (phase PR, NX-L10, design 21.11): whole quick games of every team on the real rosters (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

Each of the 32 teams plays one fast game with the N. F. L. rules and the shipped rosters.txt: no sentence says an empty name ("None", a gap where a name
belongs), every team's real starting quarterback is said, and no man the game names is anyone but a real man of the two teams (rosters.txt, active or
practice squad) or the original's own words.
"""
import random
import re

import pytest

from nfl4.extras import real_names as R
from nfl4.extras import roster_file as RF

PAIRS = [(t, 33 - t) for t in range(1, 17)]                       # T01 against T32, T02 against T31, ... every team once
EMPTY = re.compile(r"\bNone\b|, ,|\bto \.|\bby \.|  [,.]")


@pytest.fixture(autouse=True)
def fresh_defaults():
    R.reset_defaults_cache()
    yield
    R.reset_defaults_cache()


def ref(team: int):
    return (team - 1) // 4 + 1, (team - 1) % 4 + 1


@pytest.mark.parametrize("home,away", PAIRS)
def test_a_whole_game_of_every_team_says_real_names_and_no_empty_one(tmp_path, home, away):
    from pagrig import make_rig
    from programrig import said
    real = R.defaults()
    _, teams, problems = RF.parse(R.shipped_text(R.ROSTERS))
    assert problems == []
    rig = make_rig(tmp_path, fast=True)
    game = rig.game
    game.season.choose_team(*ref(home))
    game.season.tn3, game.season.tn4 = ref(away)
    game.options.settings.game.rules = "nfl"
    game.apply_rules_setting()
    game.real_names = real
    random.seed(home)
    game.play_game()
    lines = said(rig)
    assert len(lines) > 100
    bad = [line for line in lines if EMPTY.search(line)]
    assert bad == [], bad[:5]
    spoken = " ".join(lines)
    for team in (home, away):
        starter = real.spoken(next(m.name for m in teams[team].active() if m.pos == "QB"))
        assert starter in spoken, (team, starter)
    # every name the rosters of the two teams give the engine is a real man of that team (no made-up man, no other team's man)
    for team in (home, away):
        roster = real.roster(team, None)
        file_names = {real.spoken(m.name) for m in teams[team].men}
        names = roster.running_backs + roster.receivers + roster.defense + roster.special_teams + roster.kickers + [roster.quarterback]
        assert all(n in file_names for n in names if n), (team, [n for n in names if n and n not in file_names][:5])
