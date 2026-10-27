"""The radio play-by-play and the reporter's own moments (nfl4 only, rule 0.13; RC, D-195). This is inspired by Jim Kitchen.

The owner on 0.16.9: "The game still does not have radio-style broadcast. It still says 3rd and ten at the 26 yard line. ... "caught by
"playername!!" touchdown!!" Make it an exciting radio broadcast. Radio broadcasters use a lot of exclamations", and "the game has a sideline
reporter. Not once did the game have the sideline reporter speak at all. I want an exciting commentary for this game."

What is tested: every play sentence of a known shape becomes a radio call (team names for "my ball" and "your ball", the down as a call says
it, the gain by its size, exclamations at the big moments, the scoring team at a touchdown); a sentence of no known shape stays as it is; the
calls never change a game (the same draws and score as the original's words) and never say a sentence twice in a row that the original's
words do not; F9, Rules, Play calls switches them (radio, the default, or plain), at once and saved; the engine's bare Classic has none; the
reporter speaks at her new moments, always named, at every level but "a little" (which stays the 0.16.8 broadcast).
"""
import random
import re
from types import SimpleNamespace

import pytest

from nfl4.data import settingsfile
from nfl4.data.settings import Settings
from nfl4.extras import broadcast as BC
from nfl4.extras import nx_texts as X
from nfl4.extras import radio_calls as RC
from nfl4.extras import remarks as RM
from nfl4.extras.classic_radio import ClassicRadioRules
from nfl4.extras.nfl_rules import rules_from_settings
from nfl4.game.rules import CLASSIC
from nflrig import QUARTERBACKS, RecordingRules, SimEngine
from pagrig import make_rig, play
from programrig import DOWN, ENTER, ESC, said
from test_functions import rig_for
from test_pag_games import lively_policy

LEFT, RIGHT = 37, 39
SENTENCE = re.compile(r"(?<=[.!?])\s+")


def caller(wisoff=1, calls="radio"):
    """A caller of a broadcast with a game whose settings say `calls`; the Bengals are side 1 (the player), the Jets side 2."""
    settings = Settings.defaults()
    settings.game.nx_play_calls = calls
    b = SimpleNamespace(state=SimpleNamespace(teams={1: "Bengals", 2: "Jets"}, wisoff=wisoff), play_calls="radio")
    c = RC.RadioCalls(b)
    c.attach(SimpleNamespace(options=SimpleNamespace(settings=settings), rnd=None))
    return c


def said_text(c, text):
    return " ".join(c.call(text)[0].split())


# ----- the calls themselves -----

def test_every_call_is_short_plain_ascii_with_known_names_and_every_rule_has_its_call():
    for key, variants in RC.CALLS.items():
        assert variants and len(set(variants)) == len(variants), key
        for text in variants:
            assert text.isascii() and 0 < len(text) <= 150, text
            assert set(re.findall(r"\{(\w+)\}", text)) <= {"t", "q", "h", "r", "y", "z", "x", "w", "n", "a", "b", "k", "p", "m", "spot"}, text
            assert "Jim" not in text and "Kitchen" not in text
    for _pattern, rule in RC.PATTERNS:
        assert rule.isupper() or rule in RC.CALLS, rule
    assert RC.EXCITED_CALLS <= set(RC.CALLS)


@pytest.mark.parametrize("value, key", [("radio", "radio"), ("Radio Style", "radio"), ("plain", "plain"), ("the original's words", "plain"),
                                        ("loud", None), ("", None)])
def test_the_setting_is_read_from_a_word(value, key):
    assert RC.calls_key(value) == key
    assert RC.next_calls("radio") == "plain" and RC.next_calls("plain") == "radio"


@pytest.mark.parametrize("text, wanted", [
    (" it's your ball on my 47yard line", r"Bengals .*(at|have it at) the Jets 47\."),
    (" it's  mine on my 46 yard line", r"Jets .*their own 46\."),
    (" it's my ball on the 50yard line", r"Jets .*midfield\."),
    (" ball turned over on downs the ball is now  mine on your 16 yard line", r"!.*Jets take over .*the Bengals 16!"),
    (" the ball is now your ball on my 9 yard line", r"Bengals .*the Jets 9!"),
])
def test_the_ball_is_said_with_the_team_names(text, wanted):
    assert re.search(wanted, said_text(caller(), text)), said_text(caller(), text)


def test_the_down_is_called_like_a_radio_call():
    c = caller()
    c.call(" it's your ball on your 25yard line")
    c.call(" it's first down and 10yards to go")
    assert said_text(c, " it's third down and 4yards to go").startswith(("Third and 4!", "Third down, 4 to go!"))
    assert said_text(c, " it's fourth down and goal to go") == "Fourth and goal!"
    assert said_text(c, " it's second down and 1yard to go").startswith("Second and 1")


def test_a_first_down_earned_is_exciting_and_a_new_drive_is_not():
    c = caller()
    c.call(" it's  your ball on your 31 yard line")              # after a punt: a new possession
    assert said_text(c, " it's first down and 10yards to go").startswith("First and 10")
    c.call(" Murtha runs off tackle")
    c.call(" There is a gain of 10 yards on the play")
    c.call(" it's your ball on your 41yard line")
    first = said_text(c, " it's first down and 10yards to go")
    assert "first down" in first.lower() and first.endswith("!")


@pytest.mark.parametrize("yards, key", [(1, "gain_1"), (3, "gain_short"), (7, "gain"), (14, "gain_good"), (25, "gain_big"), (55, "gain_huge")])
def test_the_gain_grows_with_its_size(yards, key):
    c = caller()
    text, step = c.call(" There is a gain of %d yard%s on the play" % (yards, "" if yards == 1 else "s"))
    filled = {v.replace("{n}", str(yards)) for v in RC.CALLS[key]}
    assert " ".join(text.split()) in filled
    assert step == (RC.EXCITED if yards >= RC.BIG else 0)


def test_the_owners_example_caught_by_and_touchdown_with_the_team():
    c = caller(wisoff=1)
    catch = said_text(c, " and Seals catches the ball ")
    assert catch.endswith("!") and "Seals" in catch
    td, step = c.call(" TOUCH DOWN")
    assert "Touchdown" in td and "!" in td and step == RC.EXCITED
    assert any("Bengals" in v.replace("{t}", "Bengals") for v in RC.CALLS["touchdown"])


def test_the_countdown_and_a_return_build_up():
    c = caller()
    assert said_text(c, " he is at the") == "He's at the"
    assert [said_text(c, n) for n in ("40", "30", "5", "1")] == ["40!", "the 30!", "5!", "1!"]
    c.call(" TOUCH DOWN")
    assert said_text(c, "30") == "30"                       # outside a countdown or a return a bare number stays
    c.call(" Powers is at the 5")
    assert [said_text(c, m) for m in (" the 10", " the 15", " 25")] == ["the 10,", "the 15!", "the 25!"]


def test_an_incompletion_ends_in_incomplete_and_a_sack_costs_yards():
    c = caller()
    assert said_text(c, " it goes right through the hands of Duran").endswith("Duran!")
    assert "ncomplete" in said_text(c, " There is no gain on the play")
    c.call(" Unitas is slammed to the ground by Scanlon")
    assert "sack" in said_text(c, " There is a loss of 4 yards on the play.")


@pytest.mark.parametrize("text", [" select the play for your off fence ", " Kim select your play ", " Stats After Quarter number 1",
                                  " here is the coin toss ", " End of the First Quarter", "Bengals 6", " press any key to continue or the f 2 key to repeat "])
def test_a_sentence_of_no_known_shape_is_said_as_it_is(text):
    assert caller().call(text) == (text, 0)


def test_plain_calls_say_the_original_words():
    c = caller(calls="plain")
    for text in (" TOUCH DOWN", " it's your ball on my 47yard line", " There is a gain of 34 yards on the play"):
        assert c.call(text) == (text, 0)


# ----- the speakers and the engine -----

def test_the_speakers_use_the_caller_for_the_play_by_play_only_and_f2_replays_the_calls(tmp_path):
    rig = make_rig(tmp_path, rng=random.Random(5))
    g = rig.game
    g.radio_calls = caller()
    g.say4(" TOUCH DOWN")
    g.say5(" TOUCH DOWN")                                   # a menu's speaker is never the caller's
    texts = [t for t, _r, _s in rig.said]
    assert "Touchdown" in texts[-2] and texts[-1] == " TOUCH DOWN"
    assert "Touchdown" in g.replay[-1]                     # F2 says what was said


def test_a_failing_caller_leaves_the_original_words(tmp_path, caplog):
    rig = make_rig(tmp_path, rng=random.Random(5))
    rig.game.radio_calls = SimpleNamespace(call=lambda text: 1 / 0)
    rig.game.say2(" TOUCH DOWN")
    assert rig.said[-1][0] == " TOUCH DOWN"


def classic_game(tmp_path, rules, calls="radio", comments=True):
    rig = make_rig(tmp_path, rng=random.Random(2034), vtrnt=2)
    rig.keys.policy = lively_policy(rig, 3034)
    rig.game.options.settings.game.nx_play_calls = calls
    if not comments:
        rig.game.comtog_source = lambda: 1
    result = play(rig, rules=rules)
    return rig, result, [t for t, _r, _s in rig.said]


def doubles(texts):
    s = [x.strip() for t in texts for x in SENTENCE.split(t.strip()) if x.strip()]
    return [s[k] for k in range(1, len(s)) if s[k].casefold() == s[k - 1].casefold()]


def test_classic_radio_calls_change_words_only_and_the_bare_classic_has_none(tmp_path):
    rig_r, res_r, radio = classic_game(tmp_path / "r", ClassicRadioRules(broadcast_on=True), comments=False)
    rig_p, res_p, plain = classic_game(tmp_path / "p", ClassicRadioRules(broadcast_on=True), "plain", comments=False)
    rig_b, res_b, bare = classic_game(tmp_path / "b", CLASSIC, comments=False)
    assert res_r.scores == res_p.scores == res_b.scores and rig_r.rnd.draws == rig_p.rnd.draws == rig_b.rnd.draws
    assert plain == bare                                    # plain calls: the original's words exactly
    assert radio != plain and len(radio) == len(plain)      # the same sentences in number, said as radio calls
    assert not any("TOUCH DOWN" in t or "it's" in t and "yard line" in t for t in radio)    # F1's "its ... yard line" is the original's
    #                                                                                         prompt again, word for word (rule 0.17)
    assert any("Touchdown" in t for t in radio) and any(t.strip().endswith("!") for t in radio)
    assert len(doubles(radio)) <= len(doubles(plain))


def test_the_engine_clears_the_caller_so_a_bare_classic_after_a_radio_game_says_the_original(tmp_path):
    rig = make_rig(tmp_path, rng=random.Random(2034), vtrnt=2)
    rig.keys.policy = lively_policy(rig, 3034)
    rig.game.options.settings.game.nx_play_calls = "radio"
    play(rig, rules=ClassicRadioRules(broadcast_on=True))
    assert rig.game.radio_calls is not None
    assert any(t.strip().startswith("Touchdown") or "Touchdown" in t for t, _r, _s in rig.said)
    start = len(rig.said)
    play(rig, rules=CLASSIC)
    assert rig.game.radio_calls is None
    assert not any(t.strip().startswith("Touchdown") for t, _r, _s in rig.said[start:])


def nfl_game(tmp_path, seed, calls="radio", level="lots", broadcast=True):
    rig = make_rig(tmp_path, rng=random.Random(seed), fast=True, vtrnt=2, gtp=1)
    rig.game.options.settings.game.nx_play_calls = calls
    rig.game.options.settings.game.nx_crew_talk = level
    rig.game.comtog_source = lambda: 0
    rules = RecordingRules(penalties_on=True, onside_on=True, qb_on=True, challenges_on=True, playbooks_on=True, broadcast_on=broadcast)
    engine = SimEngine(rig.game, rules, quarterback_names=lambda state: QUARTERBACKS)
    rig.game.play_engine = engine
    try:
        result = engine.run()
    finally:
        rig.game.play_engine = None
    return rig, result, rig.said


def test_nfl_rules_radio_calls_change_words_only(tmp_path):
    rig_r, res_r, radio = nfl_game(tmp_path / "r", 22)
    rig_p, res_p, plain = nfl_game(tmp_path / "p", 22, "plain")
    assert res_r.scores == res_p.scores and rig_r.rnd.draws == rig_p.rnd.draws
    texts = [t for t, _r, _s in radio]
    assert len(doubles(texts)) <= len(doubles([t for t, _r, _s in plain]))
    assert not any(re.search(r"it's (your ball|my ball|mine) on", t) for t in texts)
    assert sum(1 for t in texts if "!" in t) > 100                 # the owner: "a lot of exclamations"


def test_a_change_of_the_setting_applies_at_once(caplog):
    c = caller()
    assert c.call(" TOUCH DOWN")[0] != " TOUCH DOWN"
    c.game.options.settings.game.nx_play_calls = "plain"
    assert c.call(" TOUCH DOWN") == (" TOUCH DOWN", 0)


# ----- the reporter -----

CREW_PATTERNS = [(pool, re.compile(re.sub(r"<[a-z ]+>", ".+", re.escape(X.TEXTS[r.id].strip()))))
                 for pool in RM.BROADCAST_POOLS for r in RM.DEFAULT_POOLS.lines(pool)]


def crew_said(rig_said):
    """The crew's lines of a game in order: (pool, role, text)."""
    pools = []
    for text, role, _s in rig_said:
        pool = next((p for p, pattern in CREW_PATTERNS if pattern.fullmatch(text.strip())), None)
        if pool is not None:
            pools.append((pool, role, text.strip()))
    return pools


def test_every_new_reporter_line_names_her_and_every_new_pool_is_customizable():
    for pool in RM.RC_SIDELINE_POOLS:
        lines = RM.DEFAULT_POOLS.lines(pool)
        assert len(lines) >= 4, pool
        for r in lines:
            assert "<sideline>" in r.markup, r.id
            assert X.SPEAKERS[r.id] == "sideline"
    assert [r.id for r in RM.DEFAULT_POOLS.lines("CXR")][:2] == ["CXR01", "CXR02"]
    assert set(RM.RC_SIDELINE_POOLS) <= set(BC.NORA_POOLS) and set(RM.RC_SIDELINE_POOLS) <= set(RM.COMMENTARY_POOLS)


@pytest.mark.parametrize("level", ["lots", "most"])
def test_the_reporter_speaks_at_her_moments_and_is_named(tmp_path, level):
    rig, _result, spoken = nfl_game(tmp_path, 22, level=level)
    pools = crew_said(spoken)
    nora = [p for p, _role, _t in pools if p in BC.NORA_POOLS]
    assert len(nora) >= 6, nora                                       # 0.16.9: two or three a game (the owner: "Not once")
    assert any(p in RM.RC_SIDELINE_POOLS for p in nora)
    for i, (pool, role, text) in enumerate(pools):
        if pool in BC.NORA_POOLS:
            assert role == "sideline"
            named = "Nora Banks" in text or (i and pools[i - 1][0] == "ASN")
            assert named, text                                        # a screen reader speaks the crew in one voice
    assert [p for p, _r, _t in pools[:5]][:4] in (["SGN", "CRW", "ASN", "SON"],)   # Walt names her before her first words


def test_a_little_has_no_new_reporter_moments_no_exclamations_and_no_hand_off_before_her_first_note(tmp_path):
    _rig, _result, spoken = nfl_game(tmp_path, 22, level="little")
    pools = [p for p, _r, _t in crew_said(spoken)]
    assert not any(p in RM.RC_SIDELINE_POOLS or p == "CXR" for p in pools)
    assert pools[:3] == ["SGN", "CRW", "SON"]
    t = BC.TALK_LEVELS["little"]
    assert (t.nora, t.chance["CXR"], t.nora_intro) == (0, 0, False)


def test_the_reporter_and_the_exclamations_never_change_the_game(tmp_path):
    runs = [nfl_game(tmp_path / level, 23, level=level) for level in ("little", "most")]
    assert runs[0][1].scores == runs[1][1].scores and runs[0][0].rnd.draws == runs[1][0].rnd.draws


def test_the_reporter_is_silent_with_the_broadcast_item_off(tmp_path):
    _rig, _result, spoken = nfl_game(tmp_path, 24, level="most", broadcast=False)
    assert not any(p in BC.NORA_POOLS or p == "CXR" for p, _r, _t in crew_said(spoken))


# ----- the setting, the Rules item, F6 -----

@pytest.mark.parametrize("value", ["radio", "plain"])
def test_settings_txt_keeps_the_play_calls(value):
    settings = Settings.defaults()
    assert settings.game.nx_play_calls == "radio"
    settings.game.nx_play_calls = value
    text = settingsfile.render(settings)
    assert "nx_play_calls = %s\n" % value in text
    again, problems = settingsfile.parse(text)
    assert again.game.nx_play_calls == value and problems == []


def test_a_bad_play_calls_value_is_a_problem_and_an_old_file_gets_radio():
    settings, problems = settingsfile.parse(settingsfile.HEADER + "nx_play_calls = loud\n")
    assert settings.game.nx_play_calls == "radio" and len(problems) == 1
    settings, problems = settingsfile.parse(settingsfile.HEADER + "nx_crew_talk = most\n")      # a file of 0.16.9
    assert settings.game.nx_play_calls == "radio" and problems == []


@pytest.mark.parametrize("rules", ["nfl", "classic"])
def test_f6_names_the_item_in_both_modes(rules):
    settings = Settings.defaults()
    settings.game.rules = rules
    assert "Play calls" in X.text("NXH-84")
    assert X.text("NXH-84") in rules_from_settings(settings.game).extra_help("117")
    made = rules_from_settings(settings.game)
    made.broadcast.play_calls = "plain"
    assert made.for_game().broadcast.play_calls == "plain"


def rules_menu(rig, keys):
    """F9, Rules, down to the twelfth item (Play calls: Rules, then eleven Downs), then the keys."""
    rig.keys.answers = [DOWN, DOWN, DOWN, ENTER] + [DOWN] * 11 + keys + [ESC, ESC]
    rig.game.functions.run()
    spoken = said(rig)
    return spoken[4 + 11:]


def test_the_play_calls_item_switches_saves_at_once_and_says_it_applies_now(tmp_path):
    rig = rig_for(tmp_path, [])
    game = rig.game.options.settings.game
    game.nx_play_calls = Settings.defaults().game.nx_play_calls      # the program's default (the rig's player has plain calls)
    spoken = rules_menu(rig, [ENTER, LEFT, RIGHT])
    now = X.text("NXM-69")
    assert spoken[0] == "Play calls: radio style, exciting"
    assert spoken[1] == "Play calls: plain, the original's words," + now
    assert spoken[2:4] == ["Play calls: radio style, exciting", "Play calls: plain, the original's words"]
    assert game.nx_play_calls == "plain" and rig.saves.count == 3
    assert "nx_play_calls = plain" in settingsfile.render(rig.game.options.settings)
