"""S-H (2026-11-06, D-209, fixesforgames B-W45): F9's rename of a player keeps what the player typed. This is inspired by Jim Kitchen.

Found while building rule 0.38: the rename took the original's key character g2 (LCase(Chr(code)) in code page 1252), so an apostrophe was
echoed as "þ" (Chr(222)) and every letter was lower case, and the original's quarterback cleaning (cqn) then dropped the apostrophe, the hyphen
and the period. The game's own real names have them (rosters.txt: Ja'Marr, Amon-Ra St. Brown). The rename is the game's own F9 item, so it takes
the character the window typed, and keeps letters, digits, spaces, apostrophes, hyphens and periods. The original's prompts (the coach's and the
quarterbacks' names of the Classic setup) are not changed.
"""
from frrig import COACH_AND_TEAM, ENTER, F9, DOWN, WANT_FRANCHISE, franchise_rig, quit_policy, run_until, spoken

from nfl4.extras.franchise import rename
from nfl4.game import prompts as P

INTO_ROSTER = [F9, DOWN, DOWN, DOWN, DOWN, ENTER, DOWN, DOWN, ENTER]     # F9, Franchise, your roster (as test_fr_rename.py)
QUARTERBACK = [ENTER, DOWN, ENTER]                                     # issue 10: change his name after his place on the depth chart


def renamed(tmp_path, typed, after=(ENTER,)):
    rig = run_until(franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM + INTO_ROSTER + QUARTERBACK + list(typed) + list(after), policy=quit_policy))
    return rig, rig.fstore.league


def test_an_apostrophe_capitals_a_hyphen_and_a_period_are_kept_as_typed(tmp_path):
    rig, league = renamed(tmp_path, list("Ja'Marr St. Kane-Lee") + [ENTER])
    assert league.player_at(league.team, 33).name == "Ja'Marr St. Kane-Lee"
    text = spoken(rig)
    assert "þ" not in "".join(text) and "'" in text                    # the echo says the apostrophe, never "þ"
    assert any(t.endswith(" is now Ja'Marr St. Kane-Lee. ") for t in text)


def test_the_rename_cleaning_keeps_the_characters_of_real_names_and_drops_the_others():
    assert rename.clean_name("Ja'Marr Chase") == "Ja'Marr Chase"
    assert rename.clean_name("Amon-Ra St. Brown") == "Amon-Ra St. Brown"
    assert rename.clean_name("René [x]") == "René x"                # an accented letter stays; brackets go
    assert rename.clean_name("'-") == "" and rename.clean_name("a") == ""   # fewer than two letters or digits: no name, as cqn
    assert P.cqn("Ja'Marr") == "JaMarr"                                     # the original's prompts keep their own cleaning


def test_the_stand_in_keys_type_themselves_in_the_rename(tmp_path):
    """Rule 0.38: the apostrophe is End and the brackets turn pages outside a typed name; inside the rename they are characters."""
    rig, league = renamed(tmp_path, list("O'Neil") + [ENTER])
    assert league.player_at(league.team, 33).name == "O'Neil"
