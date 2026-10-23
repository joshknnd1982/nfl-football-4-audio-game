"""The W key: which play the playbook would most likely pick, and the menu keys in F5 and F6 (nfl4 only, rule 0.13; CLAUDE.md 0.24, 0.28;
SZ.7, D-112, D-113, Q-050). This is inspired by Jim Kitchen.

The owner, after hearing the hints (PLAYTEST_LIST 25 and 26): "document these keys in special keys (F5) and in help" and "yes, I want a key.
This key must also be documented in game." So W (what would the playbook call) says, on a play type of the offense or the defense, the plays
Enter would most likely get and how often, and in a list of plays the plays of it the playbook most likely calls. It uses the weights of
Enter's pick and draws NOTHING (the rig's scripted source is strict: a draw fails the test). Many plays share the greatest weight, so a tie is
told as a tie and no play is named the favourite (rule 0.28 (4)); the words are "most likely" and a chance, never "recommended"; it is not
written to the speech log; and it is in F5, F6, the README keys and the hints.
"""
import random
import re
from pathlib import Path

from nfl4.extras import nx_texts as X
from nfl4.extras import playbooks as PB
from nfl4.extras.nfl_rules import NflRules
from nfl4.extras.offense_flow import likely_sentence
from nfl4.extras.plays import calling as K
from nfl4.extras.plays import catalog as C
from nfl4.extras.plays import play_menus as PM
from nfl4.game import extra_texts as words
from nfl4.game import help_texts as H
from nfl4.game import key_list as KL
from nfl4.game.rules import CLASSIC
from nflrig import nfl_engine_rig
from pagrig import Draws, run_steps

ENTER, ESCAPE, RIGHT = 13, 27, 39
MENU_UNTIL = ("offense_chosen", "defense_chosen", "concede", "save_game")
DEFENSE = dict(wisoff=2, defense=1, half=2, yard_line=30, down=1, to_go=10, quarter=1)
OFFENSE = dict(wisoff=1, defense=2, half=2, yard_line=30, down=1, to_go=10, quarter=1)
CLONE = Path(__file__).resolve().parent.parent
W_SENTENCE = re.compile(r"^ .+\. The playbook |^ W says |^ W needs |^ .+ is one play, and Enter calls it\. $")


def rig_for(tmp_path, answers, rules=None, **state):
    fields = dict(DEFENSE)
    fields.update(state)
    rules = rules or NflRules(timeouts_on=False, offense_book="pro", defense_book="pro")
    rig = nfl_engine_rig(tmp_path, answers=list(answers), rules=rules, **fields)
    rig.game.options.settings.game.nx_menu_hints = 3          # the hints are not the subject here
    return rig


def menu(rig, defense=False):
    return run_steps(rig, rig.engine.defense_menu if defense else rig.engine.offense_menu, Draws(), until=MENU_UNTIL)


def texts(rig, start=0):
    return [t for t, _, _ in rig.said[start:]]


def first_w(rig, mark):
    """The sentences W said (a sentence of the key's own wording; the items and prompts of the menu are not)."""
    return [t for t in texts(rig, mark) if W_SENTENCE.match(t)]


# ----- the words -----

def test_a_single_favourite_every_time_and_the_ties_are_told_in_their_own_words():
    names = {"a": "Slant", "b": "Hitch", "c": "Curl", "d": "Post"}.get
    say = lambda kind, ids, percent: likely_sentence(kind, "Short Pass", ids, percent, names)
    assert say("family", ("a",), 17) == " Short Pass. The playbook would most likely pick Slant, about 17 percent of the time. "
    assert say("family", ("a",), 100) == " Short Pass. The playbook picks Slant every time. "
    assert say("family", ("a", "b"), 12) == " Short Pass. The playbook would pick Slant or Hitch about equally often, each about 12 percent of the time. "
    assert say("list", ("a", "b", "c"), 9) == " Short Pass. The playbook would pick Slant, Hitch or Curl about equally often, each about 9 percent of the time. "
    assert say("list", ("a", "b", "c", "d"), 6) == (
        " Short Pass. The playbook would pick any of 4 plays about equally often, such as Slant, each about 6 percent of the time. ")
    assert say("family", ("a",), 0) == " Short Pass. The playbook has no favourite, and Enter takes Slant. "
    assert say("list", ("a",), 0) == " Short Pass. The playbook has no favourite play here. "
    assert say("list", (), 0) == ""


def test_no_text_of_the_key_promises_a_recommendation():
    for number in range(1, 11):
        text = X.TEXTS["NXB-W%02d" % number].lower()
        assert "recommend" not in text and " best" not in text and "suggest" not in text, number
        assert len(text) <= 200
    assert "most likely" in X.TEXTS["NXB-W01"] and "percent" in X.TEXTS["NXB-W01"] and "equally" in X.TEXTS["NXB-W02"]


# ----- the key on a play type, in a list, on one play -----

def test_w_on_a_play_type_of_the_offense_names_the_most_likely_plays_and_their_chance(tmp_path):
    rig = rig_for(tmp_path, ["w", ESCAPE], **OFFENSE)
    mark = len(rig.said)
    assert menu(rig) == "concede"
    said = first_w(rig, mark)
    assert len(said) == 1 and said[0].startswith(" Line Plunge. The playbook ")
    ids, percent = rig.rules.books.likely(rig.engine.s, 1, "O", rig.rules.offense.family_plays(rig.engine.s, 1))
    assert len(ids) >= 2 and 1 <= percent <= 50                  # the pro style's Line Plunge has plays that share the greatest weight
    for play_id in ids:
        assert rig.rules.offense.name(play_id) in said[0], play_id
    assert "about equally often, each about %d percent of the time. " % percent in said[0]


def test_the_chance_w_says_is_the_chance_enter_gets_each_told_play_with_the_same_weights(tmp_path):
    """The played pick and the told chance are one calculation: 20,000 draws of Enter's weights give each told play about as often as told,
    and no other play clearly more often."""
    rig = rig_for(tmp_path, [ESCAPE], **OFFENSE)
    state = rig.engine.s
    seen_tie = seen_single = False
    for role, groups in (("O", [rig.rules.offense.family_plays(state, f) for f in range(1, 6)]),
                         ("D", [rig.rules.defense.family_calls(state, f) for f in range(1, 7)])):
        for candidates in groups:
            ids, percent = rig.rules.books.likely(state, 1, role, candidates)
            weights = dict(rig.rules.books.weights(state, 1, role, candidates))
            top = max(weights.values())
            assert ids and all(weights[i] == top for i in ids) and len(ids) == list(weights.values()).count(top)
            generator, counts = random.Random(5), {}

            class Below:
                @staticmethod
                def below(total):
                    return generator.randrange(total)

            pairs = list(weights.items())
            for _ in range(20000):
                picked = K.draw(pairs, Below)
                counts[picked] = counts.get(picked, 0) + 1
            for play_id in ids:
                assert abs(counts.get(play_id, 0) / 200 - percent) <= 1.5, (role, play_id, percent, counts.get(play_id))
            assert max(counts.values()) <= counts.get(ids[0], 0) + 300
            seen_tie, seen_single = seen_tie or len(ids) > 1, seen_single or len(ids) == 1
    assert seen_tie and seen_single


def test_w_in_a_list_names_the_plays_of_the_list_the_playbook_most_likely_calls(tmp_path):
    rig = rig_for(tmp_path, [RIGHT, "w", ESCAPE], **OFFENSE)
    mark = len(rig.said)
    menu(rig)
    said = first_w(rig, mark)
    group = PM.family_groups("O", 1)[0]
    where = X.text(C.group_text_id(C.GROUP_BY_KEY[group])).strip()
    assert len(said) == 1 and said[0].startswith(" %s. The playbook " % where), said
    ids, percent = rig.rules.books.likely(rig.engine.s, 1, "O", PM.concepts_of(group, rig.rules.offense.context(rig.engine.s)))
    assert all(rig.rules.offense.name(i) in said[0] for i in ids) and ("%d percent" % percent) in said[0]


def test_w_on_the_defense_menu_and_in_its_more_plays_lists(tmp_path):
    rig = rig_for(tmp_path, ["w", ESCAPE])
    mark = len(rig.said)
    menu(rig, defense=True)
    said = first_w(rig, mark)
    assert len(said) == 1 and said[0].startswith(" Goal Line. The playbook picks ") and said[0].endswith(" every time. "), said
    rig = rig_for(tmp_path / "more", ["m", ENTER, "w", ESCAPE])
    mark = len(rig.said)
    menu(rig, defense=True)
    said = first_w(rig, mark)
    first_list = PM.more_groups("D")[0]
    where = X.text(C.group_text_id(C.GROUP_BY_KEY[first_list])).strip()
    assert len(said) == 1 and said[0].startswith(" %s. The playbook " % where), said


def test_w_on_one_play_says_it_is_one_play(tmp_path):
    rules = NflRules(timeouts_on=False, qb_on=True, offense_book="pro", defense_book="pro")
    rig = rig_for(tmp_path, ["8", "w", "6", "w", ESCAPE], rules=rules, **OFFENSE)
    mark = len(rig.said)
    menu(rig)
    said = first_w(rig, mark)
    assert said == [" %s is one play, and Enter calls it. " % rig.rules.offense.name("O046"), " Field Goal is one play, and Enter calls it. "]
    assert X.text("NXB-W08", name="Field Goal") == said[1]


def test_w_in_a_list_the_playbook_never_calls_from_says_it_has_no_favourite(tmp_path):
    rig = rig_for(tmp_path, ["p", "w", ESCAPE], down=4)           # the kick defense: the playbook never calls from it
    mark = len(rig.said)
    menu(rig, defense=True)
    said = first_w(rig, mark)
    assert len(said) == 1 and said[0].endswith(". The playbook has no favourite play here. "), said


def test_w_on_a_tail_item_and_with_the_original_items_says_what_it_is_for(tmp_path):
    rig = rig_for(tmp_path, ["s", "w", ESCAPE], **OFFENSE)                     # Save Game
    mark = len(rig.said)
    menu(rig)
    assert X.text("NXB-W09") in texts(rig, mark)
    classic_books = NflRules(timeouts_on=False, offense_book="classic", defense_book="classic")
    rig = rig_for(tmp_path / "classic", ["w", ESCAPE], rules=classic_books, **OFFENSE)
    mark = len(rig.said)
    menu(rig)
    assert X.text("NXB-W10") in texts(rig, mark)


def test_classic_has_no_w_key(tmp_path):
    rig = rig_for(tmp_path, ["w", ESCAPE], rules=CLASSIC, **OFFENSE)
    mark = len(rig.said)
    assert menu(rig) == "concede"
    assert not [t for t in texts(rig, mark) if "playbook" in t]
    assert CLASSIC.menu_key(rig.engine.s, "w", object()) is False


# ----- it draws nothing, it logs nothing -----

def test_w_draws_nothing_on_any_item_of_any_style_and_any_list(tmp_path):
    """The rig's source is strict and has no draws: one draw by W would raise. Every item of the top, of every list and of More Plays."""
    count = 0
    for n, style in enumerate(sorted(PB.DEFAULT_TABLE.styles)):
        for defense in (False, True):
            rules = NflRules(timeouts_on=False, qb_on=True, offense_book=style, defense_book=style)
            rig = rig_for(tmp_path / ("%s%s" % (n, defense)), [ESCAPE], rules=rules, **(DEFENSE if defense else OFFENSE))
            state, flow = rig.engine.s, (rig.rules.defense if defense else rig.rules.offense)

            def items():
                return list(rig.rules.defense_menu(state) if defense else rig.rules.offense_menu(state, False))

            for item in items():
                assert rig.rules.menu_key(state, "w", item) is True
                count += 1
                if flow.owns(item.action) and rig.rules.menu_right(state, item):
                    for inner in items():
                        assert rig.rules.menu_key(state, "w", inner) is True
                        count += 1
                    flow.reset()
    assert count > 150


def test_w_is_said_once_per_press_and_is_not_in_the_game_speech_log(tmp_path):
    rig = rig_for(tmp_path, ["w", "w", ESCAPE], **OFFENSE)
    mark = len(rig.said)
    menu(rig)
    sentences = first_w(rig, mark)
    assert len(sentences) == 2 and sentences[0] == sentences[1]
    assert [wait for t, _role, wait in rig.said[mark:] if t == sentences[0]] == [False, False]      # voice_speak: no wait, not logged


# ----- documented in the game: F5, F6, the README, the hints -----

def all_on_rules() -> NflRules:
    return NflRules(timeouts_on=True, penalties_on=True, onside_on=True, qb_on=True, challenges_on=True, offense_book="west",
                    defense_book="pro", playbooks_on=True)


def f5_text(rules):
    return " ".join([H.SPECIAL_KEYS, words.KEYS_ADDED_F9] + rules.extra_help(KL.KEY_F5))


def test_w_enter_on_a_play_type_and_m_are_in_f5_and_f6_in_words_a_player_can_follow():
    rules = all_on_rules()
    f5 = f5_text(rules)
    assert KL.BY_ID["likely"].f5.strip() in f5
    assert "W. in the offense and defense menus, says which play the playbook would most likely pick, and how often." in f5
    assert "Enter on a play type lets the playbook pick the play" in f5 and "M opens More Plays" in f5
    assert "Right opens its lists" in f5 and "D. in a play menu and the kick off menu" in f5
    f6 = rules.extra_help(KL.KEY_F6)
    for row in ("likely", "more", "enter_pick"):
        keys, where, what = KL.BY_ID[row].keys, KL.BY_ID[row].where, KL.BY_ID[row].what
        assert " %s. %s. %s. " % (keys, where, what[0].upper() + what[1:]) in f6, row
    assert any(line.startswith(" W. In the offense and defense menus") and "draws nothing" in line for line in f6)
    assert any(line.startswith(" Enter on a play type. ") for line in f6)


def test_every_key_a_hint_names_is_a_row_of_the_key_list_and_is_in_f5_and_f6_on_its_own():
    """B-W30, A92: the owner heard the hint and asked for its keys in F5 and F6; each key a hint names has its own row and sentences."""
    rules = all_on_rules()
    f5, f6 = f5_text(rules), rules.extra_help(KL.KEY_F6)
    named = set()
    for text_id in ("NXB-H17", "NXB-H18"):
        named |= set(re.findall(r"\b([A-Z]) (?:opens|describes|says)", X.TEXTS[text_id]))
        assert "Right opens" in X.TEXTS[text_id] and "Enter on a" in X.TEXTS[text_id]
    assert named == {"M", "D", "W"}
    rows = {"Right": "right", "Enter on a play type": "enter_pick"}
    rows.update({letter: next(row.id for row in KL.ROWS if row.keys == letter) for letter in named})          # a row of the key alone
    for keys, row_id in rows.items():
        row = KL.BY_ID[row_id]
        assert row.keys == keys and row.modes == "nfl", row_id
        assert (row.probe5 or row.f5.strip()) in f5, row_id
        assert any(line.startswith(" %s. " % keys) for line in f6), row_id


def test_the_playbook_keys_are_not_in_classic_and_only_spoken_with_a_playbook():
    assert "W." not in " ".join(CLASSIC.extra_help(KL.KEY_F5)) and "likely" not in " ".join(CLASSIC.extra_help(KL.KEY_F6))
    off = NflRules(timeouts_on=False, offense_book="classic", defense_book="classic", playbooks_on=False)
    lines = " ".join(off.extra_help(KL.KEY_F5) + off.extra_help(KL.KEY_F6))
    assert "would most likely pick" not in lines and "Enter on a play type" not in lines


def test_the_readme_keys_has_w_enter_on_a_play_type_and_m():
    text = (CLONE / "README_keys.md").read_bytes().decode("utf-8")
    assert text == KL.readme_text()
    for keys in ("W", "M", "Enter on a play type", "F, A, K, P, O, N"):
        assert "- **%s** (N. F. L. rules only)" % keys in text, keys
    assert "draws nothing" in text


def test_w_is_reserved_no_item_has_it_and_it_is_in_the_master_list_once():
    assert "w" in PM.RESERVED
    assert [row.id for row in KL.ROWS if "w" in row.letters] == ["likely"]
    assert KL.BY_ID["likely"].feature == "playbooks" and KL.BY_ID["likely"].modes == "nfl"
    for context in (PM.Context(side="O", favourites=("O001",), last_call="O001", kneel_helps=True, spike_helps=True),
                    PM.Context(side="D", fourth_down=True, favourites=("D001",), last_call="D001")):
        assert "w" not in [i.letter for i in PM.PlayMenus(context).items()]


def test_the_hints_name_w_and_stay_short():
    for text_id in ("NXB-H17", "NXB-H18"):
        assert "W says which" in X.TEXTS[text_id] and "most likely picks" in X.TEXTS[text_id] and len(X.TEXTS[text_id]) <= 200
    assert "Enter on a play type lets the playbook pick" in X.TEXTS["NXB-H17"]
    assert "Enter on a call lets the playbook pick" in X.TEXTS["NXB-H18"]
