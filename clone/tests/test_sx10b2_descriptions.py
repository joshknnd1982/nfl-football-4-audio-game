"""The plain description of every play, item, list and setting, and the D key (nfl4 only, rule 0.13; NX-P8, D-091, CLAUDE.md 0.25; PX SX.10b2).
This is inspired by Jim Kitchen.

Every choice a player can make has one or two plain sentences of at most 35 words, written for a person who has never watched football: a
football word appears only when the original's F7 (or the added football words of F7, NXH-48 to NXH-51) explains it. The letter D of a play
menu in the N. F. L. rules says the current item's description and the menu stays on the item; Classic keeps the original's keys and F7
describes the original's plays instead. Every expected text is the row of the table, found by the design's id scheme (spec/NFL_PLAYS_DESIGN.md 3).
"""
import re

import pytest

from nfl4.extras import nx_texts as X
from nfl4.extras import playbooks as PB
from nfl4.extras.nfl_rules import NflRules
from nfl4.extras.plays import catalog as C
from nfl4.extras.plays import descriptions as DS
from nfl4.extras.plays import play_menus as P
from nfl4.extras.review import CHALLENGE_ACTION
from nfl4.game import help_texts as H
from nfl4.game import menus
from nfl4.game import phrases as PH
from nfl4.game.rules import CLASSIC, ClassicRules
from nfl4.game.setup import DEFENSE_ITEMS, OFFENSE_ITEMS
from nflrig import nfl_engine_rig
from pagrig import Draws, run_steps

ENTER, ESCAPE = 13, 27
SELECT = " Kim" + PH.SELECT_OFFENSE
SELECT_D = " Kim" + PH.SELECT_DEFENSE
MENU_UNTIL = ("offense_chosen", "defense_chosen", "concede", "save_game")
START = dict(wisoff=1, defense=2, half=2, yard_line=30, down=1, to_go=10, quarter=1)
MAX_WORDS = 35

# the football words that need an explanation (patterns): each one a description uses must be in the F7 text of its mode
JARGON = (r"shotgun", r"pistol", r"\bgaps?\b", r"\bzones?\b", r"safet(y|ies)", r"secondary", r"nickel", r"\bdime\b", r"\broutes?\b",
          r"coverage", r"\bedge\b", r"fullback", r"halfback", r"audible", r"stunt", r"\bflat\b", r"slant", r"counter", r"\bdraw",
          r"\boption", r"pitch", r"touchback", r"\bbump", r"run blitz", r"deep defenders", r"guarding areas", r"man for man", r"blitz",
          r"play action", r"bootleg", r"rollout", r"lateral", r"\bscreen", r"tight end", r"linebacker", r"cornerback", r"quarterback",
          r"running backs?", r"receiver", r"linem[ae]n", r"\bcenter\b", r"\bhole", r"line of scrimmage", r"side ?line", r"end zone",
          r"touchdown", r"\bsnap", r"handoff", r"fumble", r"\bsack", r"intercept", r"punt", r"pocket", r"backfield", r"goal line",
          r"\bjet\b", r"reverse", r"\bsweep", r"\bpower\b", r"quarters", r"bracket", r"crosser", r"wishbone", r"\bblock", r"huddle")


def f7_text(nfl: bool) -> str:
    """What F7 says in a mode: the original's football words, and in the N. F. L. rules also the added words (lower case)."""
    text = H.TERMINOLOGY + "play."
    if nfl:
        ids = ("NXH-07", "NXH-08", "NXH-26", "NXH-12", "NXH-13", "NXH-17", "NXH-21", "NXH-31", "NXH-32", "NXH-33") + DS.F7_WORD_ROWS
        text += " ".join(X.text(i) for i in ids)
    return text.lower()


def sentences(text: str) -> int:
    return len(re.findall(r"[.!?](?:\s|$)", text.strip()))


def original_rows() -> list[str]:
    """The rows whose words Classic's F7 must explain with the original's football words only."""
    return [DS.OFFENSE_ITEM_ROWS[n] for n in sorted(DS.OFFENSE_ITEM_ROWS)] + [DS.DEFENSE_ITEM_ROWS[n] for n in sorted(DS.DEFENSE_ITEM_ROWS)] + [
        DS.WORD_ROWS[menus.SAVE]]


# ----- the rows -----

def test_every_play_of_the_catalog_has_a_description_row_by_the_designs_scheme():
    assert len(C.CATALOG) == 282
    rows = [DS.play_row(c.id) for c in C.CATALOG]
    assert len(set(rows)) == 282 and all(row in X.TEXTS for row in rows)
    assert DS.play_row("O001") == "NXY-R01" and DS.play_row("O099") == "NXY-R99" and DS.play_row("O100") == "NXY-S00"
    assert DS.play_row("O167") == "NXY-S67" and DS.play_row("D001") == "NXZ-R01" and DS.play_row("D092") == "NXZ-R92"
    assert DS.play_row("K001") == "NXB-D01" and DS.play_row("K036") == "NXB-D36"


def test_every_original_item_menu_word_group_list_and_setting_has_a_row():
    assert sorted(DS.OFFENSE_ITEM_ROWS) == list(range(1, 8)) and sorted(DS.DEFENSE_ITEM_ROWS) == list(range(1, 7))
    assert len(DS.LIST_ROWS) == len(C.GROUPS) == 35 and len(DS.SETTING_ROWS) == 8 and len(DS.PLAYBOOK_GROUP_ROWS) == 7
    assert all(row in X.TEXTS for row in DS.all_rows())


def test_no_description_row_is_left_over_that_nothing_uses():
    pattern = re.compile(r"^NX(Y-[RS]\d\d|Z-[RS]\d\d|B-[DEFG]\d\d)$")
    wanted = set(DS.all_rows())
    found = {row for row in X.TEXTS if pattern.match(row)}
    # NXB-D.. also names nothing else, NXB-E.. and NXB-F.. likewise (the names of the plays are NXB-K.., NXB-1.. and NXB-5..)
    assert found == wanted - {r for r in wanted if r.startswith("NXH")}


def test_every_description_is_one_or_two_plain_sentences_of_at_most_35_words():
    for row in set(DS.all_rows()) - set(DS.F7_WORD_ROWS):         # the F7 words are definitions, not descriptions
        text = DS.text(row)
        words = len(text.split())
        assert 4 <= words <= MAX_WORDS, (row, words, text)
        assert 1 <= sentences(text) <= 2, (row, text)
        assert text[0].isupper() and text.endswith("."), (row, text)
        assert "  " not in text and "<" not in text, (row, text)


def test_no_two_plays_say_the_same_thing():
    seen = {}
    for c in C.CATALOG:
        text = DS.text(DS.play_row(c.id))
        assert text not in seen, (c.id, seen.get(text))
        seen[text] = c.id


def test_a_play_description_says_when_it_works_or_is_risky_or_what_it_is():
    """A play of the offense or defense says where it is strong or weak (the catalog's own stated strength and weakness) or that it is rare, risky
    or last chance; a kick says what it is for."""
    for c in C.CATALOG:
        text = DS.text(DS.play_row(c.id)).lower()
        if c.side in ("O", "D"):
            assert any(w in text for w in ("strong", "weak", "good", "works", "beats", "safe", "risky", "rare", "reliable", "stops",
                                           "gain", "surprise", "last", "chance", "needs", "fails", "helps", "uses", "saves", "loses")), (c.id, text)


# ----- the football words -----

@pytest.mark.parametrize("nfl", [False, True])
def test_a_football_word_in_a_description_is_explained_by_f7(nfl):
    f7 = f7_text(nfl)
    rows = sorted(set(DS.all_rows()) - set(DS.F7_WORD_ROWS)) if nfl else original_rows()
    checked = 0
    for row in rows:
        text = DS.text(row).lower()
        for pattern in JARGON:
            if re.search(pattern, text):
                assert re.search(pattern, f7), ("not in F7", row, pattern, text)
                checked += 1
    assert checked > (8 if not nfl else 300)           # the check looks at something


def test_the_words_the_n_f_l_rules_f7_adds_are_four_short_help_rows():
    for row in DS.F7_WORD_ROWS:
        assert X.KINDS[row] == "help" and len(X.TEXTS[row]) <= 200
    assert [X.text(r).split(":")[0].strip() for r in DS.F7_WORD_ROWS] == ["Deep defenders", "Run blitz", "Draw", "Touchback"]


def test_classic_f7_describes_the_original_items_after_its_own_words_and_the_n_f_l_rules_f7_has_the_added_words():
    lines = ClassicRules().extra_help("118")
    assert len(lines) == 2 and lines == DS.classic_f7_lines()
    for n in range(1, 8):
        assert ("%s: %s" % (OFFENSE_ITEMS[n - 1].strip()[3:], DS.text(DS.OFFENSE_ITEM_ROWS[n]))) in lines[0]
    for n in range(1, 7):
        assert ("%s: %s" % (DEFENSE_ITEMS[n - 1].strip()[3:], DS.text(DS.DEFENSE_ITEM_ROWS[n]))) in lines[1]
    assert lines[0].startswith(" The offense plays. ") and lines[0].rstrip().endswith("Saves the game so you can finish it later.")
    nfl = NflRules(playbooks_on=True).extra_help("118")
    assert [X.text(r) for r in DS.F7_WORD_ROWS] == nfl[-4:]


# ----- the menus of the file play_menus.py -----

def contexts():
    for side in ("O", "D"):
        for two_point in (False, True):
            for qb_on in (False, True):
                for kneel in (False, True):
                    for fourth in (False, True):
                        yield P.Context(side=side, two_point=two_point and side == "O", qb_on=qb_on, kneel_helps=kneel, spike_helps=kneel,
                                        fourth_down=fourth, last_call="O001" if side == "O" else "D001", favourites=("O001", "O002"))


def every_level_items(context):
    menus_ = P.PlayMenus(context)
    seen = []
    seen += menus_.items()
    for level_action in [i for i in menus_.items() if i.action[0] in ("more", "favourites", "settings")]:
        m = P.PlayMenus(context)
        m.enter(level_action)
        seen += m.items()
        for item in m.items():
            if item.action[0] == "open":
                m2 = P.PlayMenus(context)
                m2.enter(level_action)
                m2.enter(item)
                seen += m2.items()
    for group in C.GROUPS:
        if group.side in (context.side, "K"):
            m = P.PlayMenus(context)
            m._open(group.key, P.TOP)
            seen += m.items()
    m = P.PlayMenus(context)
    m.found = ("O001", "O002")
    m.level = P.FOUND
    seen += m.items()
    return seen


def test_every_item_of_every_level_of_the_play_menus_has_a_description():
    count = 0
    for context in contexts():
        menus_ = P.PlayMenus(context)
        for item in every_level_items(context):
            row = menus_.describe(item)
            assert row in X.TEXTS, (context.side, item)
            count += 1
    assert count > 1000


def test_the_kick_off_items_and_every_setting_have_a_description():
    for item in P.kickoff_items(safety=True):
        assert P.PlayMenus().describe(item) in X.TEXTS
    for name in P.OFFENSE_SETTINGS + P.DEFENSE_SETTINGS:
        assert P.PlayMenus().describe(P.Item("", -1, "", (P.SETTING, name))) in X.TEXTS


def test_no_play_menu_gives_d_or_t_to_an_item():
    for context in contexts():
        for item in every_level_items(context):
            assert item.letter not in ("d", "t"), item
    assert "d" in P.RESERVED and "t" in P.RESERVED


# ----- the live menus of the N. F. L. rules and the D key -----

def rig_for(tmp_path, answers=(), offense="west", defense="classic", qb_on=False, timeouts_on=False, rules=None, player_defends=False,
            **state):
    """The offense_book and defense_book are `offense` and `defense`; `player_defends` puts the other team on offense (side 1 defends)."""
    fields = dict(START)
    fields.update(state)
    if player_defends:
        fields.update(wisoff=2, defense=1)
    rules = rules or NflRules(timeouts_on=timeouts_on, qb_on=qb_on, offense_book=offense, defense_book=defense, playbooks_on=False)
    return nfl_engine_rig(tmp_path, answers=list(answers), rules=rules, **fields)


def texts(rig, start=0):
    return [t for t, _, _ in rig.said[start:]]


def the_menu(rig, defense=False):
    return run_steps(rig, rig.engine.defense_menu if defense else rig.engine.offense_menu, Draws(), until=MENU_UNTIL)


def live_items(rig, defense):
    s = rig.engine.s
    return rig.rules.defense_menu(s) if defense else rig.rules.offense_menu(s, False)


def open_groups(rig, defense):
    """Every menu a player of the playbook meets: the top, then each group's plays."""
    s = rig.engine.s
    out = list(live_items(rig, defense))
    for item in list(out):
        if item.action[0] in ("ogroup", "dgroup"):
            rig.rules.books.action(s, item.action)
            out += live_items(rig, defense)
            rig.rules.books.group = None
    return out


@pytest.mark.parametrize("defense", [False, True])
def test_every_item_of_every_style_and_the_classic_book_can_be_described(tmp_path, defense):
    s_styles = ["classic"] + sorted(PB.DEFAULT_TABLE.styles)
    count = 0
    for n, style in enumerate(s_styles):
        rig = rig_for(tmp_path / str(n), offense=style, defense=style, qb_on=True, timeouts_on=True, player_defends=defense)
        for item in open_groups(rig, defense):
            row = DS.action_row(not defense, item.action)
            assert row in X.TEXTS, (style, item)
            assert rig.rules.menu_key(rig.engine.s, "d", item) is True
            assert item.letter != "d"
            count += 1
    assert count > 100


def test_the_challenge_the_time_out_and_save_game_items_have_descriptions(tmp_path):
    for action in (CHALLENGE_ACTION, ("timeout", 0), (menus.SAVE, 0), ("back", 0)):
        assert DS.action_row(True, action) in X.TEXTS and DS.action_row(False, action) in X.TEXTS
    assert DS.action_row(True, ("unknown", 0)) is None


def test_the_letter_d_describes_the_current_item_and_the_menu_stays_on_it(tmp_path):
    rig = rig_for(tmp_path, answers=["d", ESCAPE])
    mark = len(rig.said)
    assert the_menu(rig) == "concede"
    assert texts(rig, mark) == [SELECT, " 1. Inside Runs ", DS.text("NXB-E27"), " 1. Inside Runs "]


def test_d_describes_the_item_that_is_current_after_a_digit_and_a_play_of_a_group(tmp_path):
    rig = rig_for(tmp_path, answers=["2", "d", ESCAPE])
    mark = len(rig.said)
    the_menu(rig)
    assert texts(rig, mark)[-3:] == [" 2. Outside Runs ", DS.text("NXB-E28"), " 2. Outside Runs "]
    rig = rig_for(tmp_path / "play", answers=[ENTER, "d", ESCAPE])
    mark = len(rig.said)
    the_menu(rig)
    first = rig.rules.books.table.name("O001")
    assert texts(rig, mark)[-3:] == [" 1. %s " % first, DS.text(DS.play_row("O001")), " 1. %s " % first]


def test_d_on_the_defense_menu_and_on_the_tail_items(tmp_path):
    rig = rig_for(tmp_path / "d", answers=["d", ESCAPE], offense="classic", defense="pro", player_defends=True)
    mark = len(rig.said)
    assert the_menu(rig, defense=True) == "concede"
    assert texts(rig, mark) == [SELECT_D, " 1. Goal Line ", DS.text("NXB-E11"), " 1. Goal Line "]
    rig = rig_for(tmp_path / "save", answers=["s", "d", ESCAPE], offense="classic", qb_on=True, timeouts_on=True)
    mark = len(rig.said)
    the_menu(rig)
    assert DS.text(DS.WORD_ROWS[menus.SAVE]) in texts(rig, mark)


def test_d_is_not_logged_in_the_game_speech_log_and_is_said_once_per_press(tmp_path):
    rig = rig_for(tmp_path, answers=["d", "d", ESCAPE])
    mark = len(rig.said)
    the_menu(rig)
    spoken = texts(rig, mark)
    assert spoken.count(DS.text("NXB-E27")) == 2
    assert [t for t, _role, _w in rig.said[mark:] if t == DS.text("NXB-E27")] == [DS.text("NXB-E27")] * 2


def test_classic_keeps_the_original_keys_d_is_an_unknown_key_and_no_item_has_a_letter(tmp_path):
    rig = rig_for(tmp_path, answers=["d", ESCAPE], rules=CLASSIC)
    mark = len(rig.said)
    assert the_menu(rig) == "concede"
    assert DS.text("NXB-E01") not in texts(rig, mark)
    assert CLASSIC.menu_key(rig.engine.s, "d", menus.offense_menu()[0]) is False
    assert all(item.letter == "" for item in menus.offense_menu() + menus.defense_menu())
