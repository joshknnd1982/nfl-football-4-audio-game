"""The color commentator's name (nfl4 only, rule 0.13; SZ.1, D-106). This is inspired by Jim Kitchen.

The owner (2026-10-22): "The user should be able to change Ghip's name or pick from among popular sports podcaster names that Claude researches and
puts into the game." F9, Rules, Commentator lists Ghip, researched names and the item that lets the player type one. The properties that matter:
the name is heard in every line that turns to the commentator (the announcer's questions and radio banter, the remarks of the features, the intro);
a file of version 0.10.0 that still holds an unchanged default line follows the new name; a line the player changed is theirs; the name is a setting
that is saved, read, checked and used from the next game; and no random draw of the game moves.
"""
import pytest

from gamerig import Rig
from nfl4.data import settingsfile
from nfl4.data.settings import Settings
from nfl4.extras import broadcast as BC
from nfl4.extras import commentator_menu as CM
from nfl4.extras import commentators as CO
from nfl4.extras import nx_texts as X
from nfl4.extras import remarks as RM
from nfl4.extras.nfl_rules import NflRules, rules_from_settings
from nfl4.speech.roles import COLOR, EXTRA_NAMES, spoken_name
from nflrig import nfl_engine_rig
from programrig import DOWN, ENTER, ESC, UP
from randsources import ScriptedRandom, value_for
from test_functions import rig_for
from test_nx_remarks import pools_of

END = 35


# ----- the names -----

def test_the_researched_names_are_unique_sorted_plain_and_never_the_default():
    names = CO.NAMES
    assert len(names) >= 20 and len(set(n.lower() for n in names)) == len(names) and list(names) == sorted(names)
    assert "Ghip" not in names and CO.DEFAULT == "Ghip"
    for name in names:
        assert CO.clean(name) == name and name.isascii() and 2 <= len(name) <= CO.NAME_MAX, name


def test_a_typed_name_is_made_safe_to_speak_and_store():
    assert CO.clean("  pat   mcafee ") == "pat mcafee"
    assert CO.clean("Dan<Le>Batard;") == "DanLeBatard" and CO.clean("Joe, Jr.") == "Joe Jr."
    assert CO.clean("x") == "" and CO.clean("") == "" and CO.clean(None) == "" and CO.clean(5) == ""
    assert len(CO.clean("a" * 80)) == CO.NAME_MAX
    assert CO.clean("O'Brien-Smith") == "O'Brien-Smith"


def test_the_list_has_the_default_first_the_names_the_players_own_name_and_the_typing_item_last():
    items = CO.choices("Ghip")
    assert items[0] == ("default", "Ghip") and items[-1] == ("type", "") and [k for k, _ in items].count("name") == len(CO.NAMES)
    assert ("own", "Sam Smith") in CO.choices("Sam Smith") and ("own", "Pat McAfee") not in CO.choices("Pat McAfee")
    assert CM.item_name("default", "Ghip") == "Ghip, the default" and CM.item_name("own", "Sam Smith") == "Sam Smith, the name you typed"
    assert CM.item_name("type", "") == "Type a name of your own" and CM.item_name("name", "Pat McAfee") == "Pat McAfee"


def test_typing_letters_in_the_list_jumps_to_a_name():
    items = CO.choices("Ghip")
    find = CM.search(items)
    assert items[find("pat")][1] == "Pat McAfee" and items[find("mcaf")][1] == "Pat McAfee" and items[find("le b")][1] == "Dan Le Batard"
    assert find("zzz") is None and find("") is None


# ----- the setting -----

def test_the_name_is_saved_read_back_and_a_bad_line_keeps_the_default():
    settings = Settings.defaults()
    assert settings.game.nx_commentator == "Ghip"
    settings.game.nx_commentator = "Pat McAfee"
    text = settingsfile.render(settings)
    assert "nx_commentator = Pat McAfee\n" in text
    again, problems = settingsfile.parse(text)
    assert again.game.nx_commentator == "Pat McAfee" and problems == []
    bad, problems = settingsfile.parse(text.replace("nx_commentator = Pat McAfee", "nx_commentator = x"))
    assert bad.game.nx_commentator == "Ghip" and any("nx_commentator" in p for p in problems)
    old, problems = settingsfile.parse(text.replace("nx_commentator = Pat McAfee\n", ""))      # a file of version 0.10.0 has no such line
    assert old.game.nx_commentator == "Ghip" and problems == []


def test_the_programs_rules_and_every_new_game_carry_the_name():
    settings = Settings.defaults()
    settings.game.rules, settings.game.nx_commentator = "nfl", "Ryen Russillo"
    rules = rules_from_settings(settings.game)
    assert rules.broadcast.commentator == "Ryen Russillo" and rules.for_game().broadcast.commentator == "Ryen Russillo"
    assert NflRules().broadcast.commentator == "Ghip" and BC.Broadcast(None, commentator="x").commentator == "Ghip"


# ----- the lines -----

def strict(tmp_path, values, name):
    rig = nfl_engine_rig(tmp_path, rules=NflRules(broadcast_on=True, radio_banter=True, commentator=name), comments=True)
    rig.rnd.source = ScriptedRandom(values, strict=True)
    rig.rnd.trace = []
    return rig


@pytest.mark.parametrize("name", ["Ghip", "Pat McAfee"])
def test_the_announcer_turns_to_the_commentator_by_name(tmp_path, name):
    rig = strict(tmp_path, [value_for(12, 1)], name)
    assert RM.commentator_of(rig.game) == name
    remark = RM.say_remark(rig.game, rig.engine.s, rig.engine.s.extras, "ASK", {})
    assert remark.id == "ASK01"
    assert [t for t, _, _ in rig.said] == [" %s, what did you make of that one? " % name]
    assert rig.rnd.trace == [12]                                  # the name takes no draw


def test_the_remarks_of_the_features_and_the_radio_banter_say_the_name_too(tmp_path):
    rig = strict(tmp_path, [value_for(5, 2)], "Chris Long")
    RM.say_remark(rig.game, rig.engine.s, rig.engine.s.extras, "TO", {})
    assert [t for t, _, _ in rig.said] == [" Chris Long, that time out could come in handy later. "]
    lines = {line.number: line for line in rig.rules.broadcast.banter_lines(rig.game)}
    said = lines[41].pieces[0].items[0].text
    assert said.startswith(" Chris Long, I notice your headphones") and "<commentator>" not in said
    assert "Ghip" not in said and len(lines) == 142


def test_the_intro_names_the_commentator(tmp_path):
    assert X.text("NXB-B01", commentator="Pat McAfee").startswith(" Pat McAfee, the color commentator, is in the booth with me.")
    assert "Ghip" not in X.TEXTS["NXB-B01"] and "<commentator>" in X.TEXTS["NXB-B01"]


def test_no_default_line_says_ghip_any_more_and_none_makes_a_claim_about_a_person():
    for pool in RM.POOLS_BUILT:
        for remark in RM.DEFAULT_POOLS.lines(pool):
            text = X.TEXTS[remark.id]
            assert "Ghip" not in text, remark.id
            if "<commentator>" in text:
                assert not any(word in (" " + text.lower() + " ") for word in (" he ", " his ", " him ", " she ", " her ", " used to play", " played this game")), remark.id


def test_the_pronoun_free_texts_of_the_help_say_the_color_commentator_and_where_the_name_is_chosen():
    for text_id in ("NXH-65", "NXH-66", "NXH-68", "NXH-70"):
        assert " he " not in X.TEXTS[text_id].lower() and " his " not in X.TEXTS[text_id].lower(), text_id
    assert "F9, Rules, Commentator" in X.TEXTS["NXH-70"]
    assert EXTRA_NAMES[COLOR] == "the color commentator" == spoken_name(COLOR)


# ----- a file of version 0.10.0 -----

def test_an_unchanged_default_line_of_an_old_file_follows_the_name_and_a_changed_one_does_not():
    pools, problems = pools_of("TO02 = Ghip, that time out could come in handy later.\nTO05 = Ghip, my own wording.\n"
                               "BN42 = Ghip is looking very thoughtful over there. Either he is studying the game or he is wondering what is in the lunch bag.\n"
                               "BN43 = Ghip still gets that gleam in his eye when the crowd gets loud. Once a player, always a player.\n")
    lines = {r.id: r for r in pools.lines("TO")}
    assert lines["TO02"].builtin and lines["TO02"].markup == "<commentator>, that time out could come in handy later."
    assert not lines["TO05"].builtin and lines["TO05"].markup == "Ghip, my own wording."
    banter = {r.id: r for r in pools.lines("BN")}
    assert banter["BN42"].builtin and banter["BN43"].builtin and problems.count == 0
    assert set(RM.LEGACY_MARKUP) == {"BN42", "BN43", "BN82", "BN83", "BN123", "BN124", "ON03"}
    for key, old in RM.LEGACY_MARKUP.items():
        assert RM.DEFAULT_MARKUP[key] != old and ("Ghip" in old or key == "ON03")


def test_the_commentator_placeholder_is_known_in_every_pool_and_a_player_may_use_it():
    assert all("<commentator>" in RM.PLACEHOLDERS[pool] for pool in RM.POOLS_BUILT)
    pools, problems = pools_of("CTD11 = <commentator> sees <team> score\nTO06 = nice one, <commentator>\n")
    assert problems.count == 0 and pools.lines("CTD")[-1].id == "CTD11" and pools.lines("TO")[-1].id == "TO06"


# ----- the menu -----

def rules_menu(rig, keys):
    rig.game.options.settings.game.rules = "nfl"
    rig.keys.answers = [DOWN, DOWN, DOWN, ENTER] + keys + [ESC, ESC]
    rig.game.functions.run()
    from programrig import said
    return said(rig)


def test_the_rules_menu_has_the_commentator_before_reset_and_enter_chooses_a_name_from_the_list(tmp_path):
    rig = rig_for(tmp_path, [])
    spoken = rules_menu(rig, [END, UP, UP, ENTER, DOWN, ENTER])     # D-140: Quarterbacks between it and Reset
    assert "Commentator: Ghip" in spoken
    assert any(s.startswith("Choose the commentator. %d items." % (len(CO.NAMES) + 2)) for s in spoken)
    assert spoken[spoken.index("Alan Shearer")] == "Alan Shearer"
    assert "Commentator: Alan Shearer" + X.text("NXM-23") in spoken
    assert rig.game.options.settings.game.nx_commentator == "Alan Shearer" and rig.saves.count >= 1
    assert rig.game.rules.broadcast.commentator == "Alan Shearer"               # the next game's rules object has it


def test_escape_in_the_list_changes_nothing_and_left_and_right_step_through_the_names(tmp_path):
    rig = rig_for(tmp_path, [])
    spoken = rules_menu(rig, [END, UP, UP, ENTER, DOWN, ESC])
    assert rig.game.options.settings.game.nx_commentator == "Ghip" and not any("Commentator: Alan" in s for s in spoken)
    rig = rig_for(tmp_path / "step", [])
    spoken = rules_menu(rig, [END, UP, UP, 39, 39, 37])
    assert [s for s in spoken if s.startswith("Commentator:")] == ["Commentator: Ghip", "Commentator: Alan Shearer", "Commentator: Bill Simmons",
                                                                     "Commentator: Alan Shearer"]
    assert rig.game.options.settings.game.nx_commentator == "Alan Shearer"


def test_a_name_of_the_players_own_is_typed_with_the_originals_prompt_and_kept(tmp_path):
    rig = Rig(sounds_dir=tmp_path / "sounds", rng=__import__("random").Random(1))
    settings = Settings.defaults().game
    rig.keys.post(END)
    rig.keys.post(13)                                       # the last item: type a name of your own
    for code, char in ((83, "s"), (65, "a"), (77, "m"), (32, " "), (74, "j")):
        rig.keys.post(code)
        rig.keys.post_char(char)
    rig.keys.post(13)
    assert CM.pick(rig.game, rig.speech, rig.keys, settings) is True
    assert settings.nx_commentator == "sam j"
    assert X.text("NXM-43") in [t for t, *_ in rig.said]
    rig.keys.post(END)                                      # typing nothing keeps the name and says so
    rig.keys.post(13)
    rig.keys.post(13)
    assert CM.pick(rig.game, rig.speech, rig.keys, settings) is False
    assert settings.nx_commentator == "sam j" and X.text("NXM-44") in [t for t, *_ in rig.said]
