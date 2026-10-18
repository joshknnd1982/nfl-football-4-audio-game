"""Renaming a player of the Franchise (nfl4 only, rule 0.13; NFL_FRANCHISE_DESIGN 17 SX.8m, D-073): F9, franchise, your roster, Enter on a player: the
original's typed prompt (as `game\\prompts.py` getter: Backspace, F1 again, the name cleaned by cqn), the original's yes or no question, the checks (a name in
use, a waiting rookie), and the file written. The program is the whole program on the rig of tests/frrig.py.
"""
import random

from drrig import SURNAMES
from frrig import COACH_AND_TEAM, DOWN, ENTER, ESC, F1, F9, WANT_FRANCHISE, franchise_rig, quit_policy, run_until, spoken

from nfl4.extras import nx_texts as X
from nfl4.extras.franchise import rename
from nfl4.extras.franchise.league import LeagueRecord, new_league
from nfl4.game.rnd import GameRandom

INTO_ROSTER = [F9, DOWN, DOWN, DOWN, DOWN, ENTER, DOWN, DOWN, ENTER]     # F9, Franchise, your roster
QUARTERBACK = [ENTER, ENTER]                                           # the first group (quarterback) and its player
BACKSPACE = 8


def renamed(tmp_path, typed, after=()):
    rig = run_until(franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM + INTO_ROSTER + QUARTERBACK + list(typed) + list(after), policy=quit_policy))
    return rig, rig.fstore.league


def saved(rig):
    return LeagueRecord.from_json(rig.files.data["league.sav"].decode("utf-8"))


# ----- the rule -----

def test_a_name_in_use_his_own_name_no_name_and_a_rookie_before_the_cut_are_refused():
    league = new_league(GameRandom(random.Random(3)), SURNAMES, "Kim", 1, "20260101-000000")
    qb, other = league.player_at(1, 33), league.player_at(2, 0)
    assert rename.check_name(league, qb, "") == "NXU-42"
    assert rename.check_name(league, qb, qb.name) == "NXU-43"
    assert rename.check_name(league, qb, other.name) == "NXU-44"
    assert rename.check_name(league, qb, "Brandnew") is None
    assert rename.check_name(league, qb, other.name.upper()) == "NXU-44" and rename.check_name(league, qb, other.name + " ") == "NXU-44"
    assert rename.check_name(league, qb, qb.name.lower()) == "NXU-43"
    qb.place = -1
    assert rename.check_name(league, qb, "Brandnew") == "NXU-45"


def test_the_name_of_a_prospect_of_the_draft_in_progress_is_refused():
    from drrig import draft_league
    from nfl4.extras.franchise import draft as DR
    league = draft_league(seed=4)
    draft = DR.Draft.create(league, GameRandom(random.Random(4)), SURNAMES)
    player = league.player_at(1, 0)
    assert rename.check_name(league, player, draft.prospects[0].name) == "NXU-44"
    assert rename.check_name(league, player, "Brandnew") is None


# ----- F9 on the program rig -----

def test_enter_on_a_player_asks_the_new_name_and_yes_renames_him_and_writes_the_file(tmp_path):
    rig, league = renamed(tmp_path, ["k", "a", "r", "s", "t", ENTER], [ENTER])
    qb = league.player_at(league.team, 33)
    assert qb.name == "karst"
    assert saved(rig).player_at(league.team, 33).name == "karst"
    text = spoken(rig)
    assert any(t.startswith(" type the new name of ") for t in text)
    assert X.text("NXU-41", name="karst") in text
    assert any(t.endswith(" is now karst. ") for t in text)


def test_no_at_the_question_keeps_the_name(tmp_path):
    rig, league = renamed(tmp_path, ["k", "a", "r", "s", "t", ENTER], [DOWN, ENTER])
    qb = league.player_at(league.team, 33)
    assert qb.name != "karst"
    assert X.text("NXU-42", player=qb.name) in spoken(rig)


def test_backspace_removes_the_last_letter_and_f1_starts_the_name_again(tmp_path):
    rig, league = renamed(tmp_path, ["x", "y", F1, "k", "a", "r", "s", "t", "z", BACKSPACE, ENTER], [ENTER])
    assert league.player_at(league.team, 33).name == "karst"


def test_escape_or_a_name_too_short_changes_nothing(tmp_path):
    rig, league = renamed(tmp_path, [ESC])
    before = league.player_at(league.team, 33).name
    assert X.text("NXU-42", player=before) in spoken(rig)
    rig, league = renamed(tmp_path / "b", ["k", ENTER])
    assert any(t.endswith(" keeps his name. ") for t in spoken(rig))


def test_the_name_of_another_active_player_is_refused(tmp_path):
    karst = ["k", "a", "r", "s", "t", ENTER]
    rig, league = renamed(tmp_path, karst, [ENTER, ESC, DOWN, ENTER, ENTER] + karst)        # the quarterback is karst; then the first running back
    back = league.player_at(league.team, 0)
    assert back.name != "karst" and league.player_at(league.team, 33).name == "karst"
    assert X.text("NXU-44", player=back.name) in spoken(rig)
