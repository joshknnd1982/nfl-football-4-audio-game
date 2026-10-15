"""The texts and sentences of the season engine (GAME_SPEC 5.14 to 5.17, 5.6 item 7). This is inspired by Jim Kitchen.

Every text of game/season_texts.py is a string of the original's exe (spec/strings_all.tsv); the sentence builders join them as
the lifted code does (pog 0x46326b..., finplay17 0x47e2f4..., superbowl 0x484a05...).
"""
import ast
import collections

from nfl4.game import season_texts as T
from nfl4.game.season_engine import (out_of_the_playoffs, playoff_result, qualifier_line, super_bowl_sentence,
                                     week_result)
from specfiles import original_strings, strings_table


def module_texts():
    return {name: value for name, value in vars(T).items() if not name.startswith("_") and isinstance(value, str)}


def test_every_text_of_the_season_engine_is_a_string_of_the_original():
    strings = original_strings()
    assert [(n, t) for n, t in module_texts().items() if t not in strings] == []
    assert len(module_texts()) == 27


def test_no_name_of_the_text_module_is_assigned_twice():
    tree = ast.parse(open(T.__file__, encoding="utf-8").read())
    names = collections.Counter(n.id for node in tree.body if isinstance(node, ast.Assign)
                                for target in node.targets for n in ast.walk(target) if isinstance(n, ast.Name))
    assert [name for name, count in names.items() if count > 1] == []


def test_the_texts_are_used_by_the_procedures_the_string_table_names():
    """The string table lists the procedures that use each text: pog p_4615b0, finplay17 p_47d8b0, superbowl p_484860."""
    rows = {}
    for row in strings_table():
        rows.setdefault(row["text"], set()).update(p for p in row["procedures"].split(",") if p)
    owners = {"POG_AFC_DIVISION": {"p_4615b0"}, "FIN_AFC_DIVISION": {"p_47d8b0"}, "IN_THE_SUPER_BOWL": {"p_47d8b0"},
              "HAVE_WON_THE_SUPER_BOWL": {"p_484860"}, "THEY_BEAT_THE": {"p_484860"}, "GAMES_OF_WEEK": {"p_4615b0"},
              "POG_AFC_WILD_CARD": {"p_4615b0", "p_47d8b0"}, "POG_NFC_DIVISION": {"p_4615b0", "p_47d8b0"},
              "WON_OVER_THE": {"p_4615b0", "p_47d8b0"}, "BY_THE_SCORE_OF": {"p_4615b0", "p_47d8b0", "p_484860"}}
    for name, procedures in owners.items():
        assert rows[getattr(T, name)] >= procedures, name


def test_the_two_engines_keep_their_own_headings_q47():
    assert T.POG_AFC_DIVISION == " In the A. F. C. division play off games. "
    assert T.FIN_AFC_DIVISION == " In the A. F. C. Division play off games. "
    assert T.POG_AFC_CHAMPIONSHIP == " In the A. F. C. championship  game. "         # two spaces
    assert T.FIN_AFC_CHAMPIONSHIP == " In the A. F. C. Championship game. "
    assert T.POG_NFC_CHAMPIONSHIP == " In the N. F. C. championship game. "
    assert T.FIN_NFC_CHAMPIONSHIP == " In the N. F. C. Championship game. "
    assert T.POG_NFC_DIVISION == " In the N. F. C. division play off games. "         # finplay17 uses this one too


def test_a_regular_weeks_result_has_no_the_and_trimmed_numbers():
    assert week_result("Bears", "Lions", 24, 17) == "Bears over the Lions by the score of 24, to 17. "
    assert week_result("Jets", "Colts", 3, 0) == "Jets over the Colts by the score of 3, to 0. "


def test_a_playoff_result_has_str_numbers_so_two_spaces_before_the_score_and_the_loser_s_zero():
    assert playoff_result("Bears", "Lions", 24, 17) == " The Bears won over the Lions by the score of  24 to 17. "
    assert playoff_result("Jets", "Colts", 3, 0) == " The Jets won over the Colts by the score of  3 to 0. "


def test_a_division_winner_or_wild_card_line_has_trimmed_numbers():
    assert qualifier_line("Steelers", 12, 4) == "Steelers. at 12 and 4. "


def test_the_line_of_a_team_that_is_out_has_str_numbers_and_two_spaces_after_the_full_stop():
    """GAME_SPEC 5.15 item 6 (audit A-12): " The Bears at  7 and  9.  did not make it into the playoffs. "."""
    assert out_of_the_playoffs("Bears", 7, 9) == " The Bears at  7 and  9.  did not make it into the playoffs. "
    assert out_of_the_playoffs("Bears", 10, 6) == " The Bears at  10 and  6.  did not make it into the playoffs. "


def test_the_super_bowl_sentence_has_two_spaces_after_the_exclamation_mark():
    assert (super_bowl_sentence("Bengals", "Jets", 24, 17) ==
            " The Bengals have Won the super Bowl!  They beat the Jets by the score of 24, to 17. ")


def test_the_joining_texts_keep_their_spaces():
    assert (T.GAMES_OF_WEEK, T.OVER_THE, T.WON_OVER_THE, T.THE, T.AT, T.AND, T.TO) == (
        " Games of week number ", " over the ", " won over the ", " The ", " at ", " and ", " to")
    assert (T.DOT_AT, T.COMMA_TO, T.END) == (". at ", ", to ", ". ")
