"""The color analyst's name (nfl4 only, rule 0.13; SZ.1, D-106; BC.2, D-178, D-180). This is inspired by Jim Kitchen.

SZ.1 let the player change Ghip's name or pick a researched podcaster's name. BC.2 removed the original's character and that list (the owner,
2026-10-26: "get rid of all of Jim Kitchen's commentary and commenting code for Gip and other commenters"): the analyst is the made-up Gus
Delgado, and F9, Rules, Commentator lists the default, the player's own name and the item that types one. The properties that matter: the name
is heard in every line that turns to the analyst (the announcer's questions, the remarks of the features, the intro); Ghip and the retired
names in an older settings.txt read as the default; a file of version 0.10.0 that still holds an unchanged default line follows the new name;
a line the player changed is theirs; the name is a setting that is saved, read, checked and used from the next game; no random draw moves.
BC.3 (D-189): the item is F9, Rules, Broadcast crew, the four names of the radio crew (extras/crew_menu.py); the analyst's name is the setting
nx_analyst (an old nx_commentator is read once into it) and the last typed name stays in the list when the player goes back to the default.
"""
import pytest

from gamerig import Rig
from nfl4.data import settingsfile
from nfl4.data.settings import Settings
from nfl4.extras import broadcast as BC
from nfl4.extras import crew
from nfl4.extras import crew_menu as CM
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
DEFAULT = "Gus Delgado"


# ----- the names -----

def test_the_default_is_the_made_up_analyst_and_no_list_of_real_names_is_offered():
    assert CO.DEFAULT == DEFAULT and not hasattr(CO, "NAMES")
    assert len(CO.RETIRED_DIGESTS) == 29 and all(len(d) == 64 for d in CO.RETIRED_DIGESTS)    # Ghip and the 28 names of D-106
    assert not CO.is_retired(DEFAULT) and CO.clean(DEFAULT) == DEFAULT


@pytest.mark.parametrize("old", ["Ghip", "ghip", "  GHIP ", "Pat McAfee", "pat   mcafee", "PAT MCAFEE"])
def test_ghip_and_the_retired_names_read_as_the_default_from_settings_and_from_a_text(old):
    assert CO.is_retired(old) and CO.name_of_text(old) == DEFAULT
    settings = Settings.defaults()
    text = settingsfile.render(settings) + "nx_commentator = %s\n" % old           # a settings file of 0.16.7 or older
    again, problems = settingsfile.parse(text)
    assert again.game.nx_analyst == DEFAULT and again.game.nx_analyst_own == "" and problems == []
    assert all(not CO.is_retired(name) for _kind, name in crew.choices(again.game, crew.ANALYST) if name)
    assert crew.choices(again.game, crew.ANALYST) == [("default", DEFAULT), ("type", "")]


def test_a_typed_name_is_made_safe_to_speak_and_store():
    assert CO.clean("  sam   smith ") == "sam smith"
    assert CO.clean("Al<Le>Roy;") == "AlLeRoy" and CO.clean("Joe, Jr.") == "Joe Jr."
    assert CO.clean("x") == "" and CO.clean("") == "" and CO.clean(None) == "" and CO.clean(5) == ""
    assert len(CO.clean("a" * 80)) == CO.NAME_MAX
    assert CO.clean("O'Brien-Smith") == "O'Brien-Smith"
    assert CO.name_of_text("x") == DEFAULT and CO.name_of_text(None) == DEFAULT and CO.name_of_text("Sam Smith") == "Sam Smith"


def own(name):
    settings = Settings.defaults().game
    settings.nx_analyst = settings.nx_analyst_own = name
    return settings


def test_the_list_has_the_default_first_the_players_own_name_and_the_typing_item_last():
    assert crew.choices(Settings.defaults().game, crew.ANALYST) == [("default", DEFAULT), ("type", "")]
    assert crew.choices(own("Sam Smith"), crew.ANALYST) == [("default", DEFAULT), ("own", "Sam Smith"), ("type", "")]
    settings = own("Sam Smith")
    settings.nx_analyst = DEFAULT                                          # BC.3: back to the default, the typed name stays in the list
    assert crew.choices(settings, crew.ANALYST) == [("default", DEFAULT), ("own", "Sam Smith"), ("type", "")]
    assert CM.item_name("default", DEFAULT) == "Gus Delgado, the default" and CM.item_name("own", "Sam Smith") == "Sam Smith, the name you typed"
    assert CM.item_name("type", "") == "Type a name of your own"


def test_typing_letters_in_the_list_jumps_to_a_name():
    items = crew.choices(own("Sam Smith"), crew.ANALYST)
    find = CM.search(items)
    assert items[find("sam")][1] == "Sam Smith" and items[find("smi")][1] == "Sam Smith" and items[find("gus")][1] == DEFAULT
    assert find("zzz") is None and find("") is None


# ----- the setting -----

def test_the_name_is_saved_read_back_and_a_bad_line_keeps_the_default():
    settings = Settings.defaults()
    assert settings.game.nx_analyst == DEFAULT and settings.game.nx_analyst_own == ""
    settings.game.nx_analyst = settings.game.nx_analyst_own = "Sam Smith"
    text = settingsfile.render(settings)
    assert "nx_analyst = Sam Smith\n" in text and "nx_analyst_own = Sam Smith\n" in text and "nx_commentator" not in text
    again, problems = settingsfile.parse(text)
    assert again.game.nx_analyst == "Sam Smith" and again.game.nx_analyst_own == "Sam Smith" and problems == []
    bad, problems = settingsfile.parse(text.replace("nx_analyst = Sam Smith", "nx_analyst = x"))
    assert bad.game.nx_analyst == DEFAULT and any("nx_analyst" in p for p in problems)
    old, problems = settingsfile.parse(text.replace("nx_analyst = Sam Smith\n", "").replace("nx_analyst_own = Sam Smith\n", ""))
    assert old.game.nx_analyst == DEFAULT and problems == []                  # a file of version 0.10.0 has no such line
    legacy, problems = settingsfile.parse("nx_commentator = Sam Smith\n")       # 0.16.7 and older: read once into the analyst's name
    assert legacy.game.nx_analyst == "Sam Smith" and legacy.game.nx_analyst_own == "Sam Smith" and problems == []


def test_the_programs_rules_and_every_new_game_carry_the_name():
    settings = Settings.defaults()
    settings.game.rules, settings.game.nx_analyst = "nfl", "Sam Smith"
    rules = rules_from_settings(settings.game)
    assert rules.broadcast.commentator == "Sam Smith" and rules.for_game().broadcast.commentator == "Sam Smith"
    settings.game.nx_analyst = "Ryen Russillo"                         # a retired name set by hand (not read from a file)
    assert rules_from_settings(settings.game).broadcast.commentator == DEFAULT
    assert NflRules().broadcast.commentator == DEFAULT and BC.Broadcast(None, commentator="x").commentator == DEFAULT
    assert BC.Broadcast(None, commentator="Ghip").commentator == DEFAULT


# ----- the lines -----

def strict(tmp_path, values, name):
    rig = nfl_engine_rig(tmp_path, rules=NflRules(broadcast_on=True, commentator=name), comments=True)
    rig.rnd.source = ScriptedRandom(values, strict=True)
    rig.rnd.trace = []
    return rig


@pytest.mark.parametrize("name", [DEFAULT, "Sam Smith"])
def test_the_announcer_turns_to_the_analyst_by_name(tmp_path, name):
    rig = strict(tmp_path, [value_for(12, 1)], name)
    assert RM.commentator_of(rig.game) == name
    remark = RM.say_remark(rig.game, rig.engine.s, rig.engine.s.extras, "ASK", {})
    assert remark.id == "ASK01"
    assert [t for t, _, _ in rig.said] == [" %s, what did you see on that one? " % name]       # RS.1 (D-179): the hand-off in the real broadcasts' words
    assert rig.rnd.trace == [12]                                  # the name takes no draw


def test_the_remarks_of_the_features_and_the_radio_banter_say_the_name_too(tmp_path):
    rig = strict(tmp_path, [value_for(5, 2)], "Chris Smith")
    RM.say_remark(rig.game, rig.engine.s, rig.engine.s.extras, "TO", {})
    assert [t for t, _, _ in rig.said] == [" Chris Smith, that time out could come in handy later. "]
    rig = strict(tmp_path / "bn", [value_for(142, 69)], "Chris Smith")          # BC.3 draws BN; a line that names the analyst says the name
    remark = RM.say_remark(rig.game, rig.engine.s, rig.engine.s.extras, "BN", {})
    said = [t for t, _, _ in rig.said][0]
    assert remark.id == "BN69" and said.startswith(" Chris Smith is taking notes over there") and "<commentator>" not in said
    assert "Ghip" not in said


def test_the_intro_names_where_the_crew_is_set(tmp_path):
    # BC.3: the crew is introduced by name in the sign-on (pool CRW); the once-per-run sentence says where their voices and names are set
    assert "F12" in X.TEXTS["NXB-B01"] and "Broadcast crew" in X.TEXTS["NXB-B01"] and "Ghip" not in X.TEXTS["NXB-B01"]
    assert all("<analyst>" in X.TEXTS[r.id] for r in RM.DEFAULT_POOLS.lines("CRW"))


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
        assert "Ghip" not in X.TEXTS[text_id] and "podcast" not in X.TEXTS[text_id].lower(), text_id
    assert "F9, Rules, Broadcast crew" in X.TEXTS["NXH-70"] and DEFAULT in X.TEXTS["NXH-70"]
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

def rules_menu(rig, keys, name=None):
    rig.game.options.settings.game.rules = "nfl"
    if name is not None:
        rig.game.options.settings.game.nx_analyst = rig.game.options.settings.game.nx_analyst_own = name
    rig.keys.answers = [DOWN, DOWN, DOWN, ENTER] + keys + [ESC, ESC]
    rig.game.functions.run()
    from programrig import said
    return said(rig)


def test_the_rules_menu_has_the_crew_before_reset_and_enter_chooses_from_the_list(tmp_path):
    rig = rig_for(tmp_path, [])
    # D-140, NX-D3: Quarterbacks and Depth charts between it and Reset; BC.3: Enter opens the crew, Down to the analyst, Enter his list
    spoken = rules_menu(rig, [END, UP, UP, UP, ENTER, DOWN, ENTER, UP, ENTER, ESC], "Sam Smith")
    assert "Broadcast crew: Walt Kessler, Sam Smith, Nora Banks" in spoken
    assert any(s.startswith("Broadcast crew. 4 items.") for s in spoken)
    assert "Color analyst: Sam Smith" in spoken
    assert any(s.startswith("Choose a name. 3 items.") for s in spoken)
    assert "Gus Delgado, the default" in spoken
    assert "Color analyst: Gus Delgado" + X.text("NXM-23") in spoken
    assert "Broadcast crew: Walt Kessler, Gus Delgado, Nora Banks" + X.text("NXM-23") in spoken
    assert rig.game.options.settings.game.nx_analyst == DEFAULT and rig.saves.count >= 1
    assert rig.game.options.settings.game.nx_analyst_own == "Sam Smith"     # the typed name is remembered
    assert rig.game.rules.broadcast.commentator == DEFAULT                    # the next game's rules object has it


def test_escape_in_the_list_changes_nothing_and_left_and_right_step_between_the_names(tmp_path):
    rig = rig_for(tmp_path, [])
    spoken = rules_menu(rig, [END, UP, UP, UP, ENTER, DOWN, ENTER, UP, ESC, ESC], "Sam Smith")
    assert rig.game.options.settings.game.nx_analyst == "Sam Smith" and not any(s.startswith("Color analyst: Gus") for s in spoken)
    rig = rig_for(tmp_path / "step", [])
    spoken = rules_menu(rig, [END, UP, UP, UP, ENTER, DOWN, 39, 39, 37, ESC], "Sam Smith")
    # BC.3: the typed name stays an item when Right steps to the default (BC.2 lost it), so Right comes back to it
    assert [s for s in spoken if s.startswith("Color analyst:")] == ["Color analyst: Sam Smith", "Color analyst: Gus Delgado",
                                                                       "Color analyst: Sam Smith", "Color analyst: Gus Delgado"]
    assert rig.game.options.settings.game.nx_analyst == DEFAULT and rig.game.options.settings.game.nx_analyst_own == "Sam Smith"


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
    assert settings.nx_analyst == "sam j" and settings.nx_analyst_own == "sam j"
    assert X.text("NXM-43") in [t for t, *_ in rig.said]
    rig.keys.post(END)                                      # typing nothing keeps the name and says so
    rig.keys.post(13)
    rig.keys.post(13)
    assert CM.pick(rig.game, rig.speech, rig.keys, settings) is False
    assert settings.nx_analyst == "sam j" and X.text("NXM-44") in [t for t, *_ in rig.said]
    rig.keys.post(END)                                      # typing a retired name gives the default
    rig.keys.post(13)
    for code, char in ((71, "g"), (72, "h"), (73, "i"), (80, "p")):
        rig.keys.post(code)
        rig.keys.post_char(char)
    rig.keys.post(13)
    CM.pick(rig.game, rig.speech, rig.keys, settings)
    assert CO.name_of(settings) == DEFAULT
