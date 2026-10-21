"""The play menus in the original's style (nfl4 only, rule 0.13; NX-P4, NX-P7; design `spec/NFL_PLAYS_DESIGN.md` section 2;
SX.10b). This is inspired by Jim Kitchen.

The keys are the engine's (game/pag.py `_menu`): Up and Down move and wrap, a digit or a letter makes an item current, Enter takes
it, Right opens a family's lists, Left goes back. A breadth-first search over those keys from the top of the menu finds the
fewest keys to every play: the usual call is two keys, every play at most six (design 2.3, the research's Q-P1 measure).
"""
import copy

import pytest

from nfl4.extras import nx_texts as X
from nfl4.extras.plays import catalog as C
from nfl4.extras.plays import play_menus as P
from nfl4.game.setup import DEFENSE_ITEMS, OFFENSE_ITEMS

UP, DOWN, ENTER, RIGHT, LEFT = "up", "down", "enter", "right", "left"


def keys_of(menus, current):
    items = menus.items()
    keys = [UP, DOWN, ENTER, RIGHT, LEFT]
    keys += ["#%d" % item.digit for item in items if item.digit >= 0]
    keys += ["@" + item.letter for item in items if item.letter]
    return items, keys


def press(menus, current, key):
    """The engine loop's answer to one key: (menus, current, chosen action or None)."""
    items = menus.items()
    if key == UP:
        return menus, current - 1 if current > 1 else len(items), None
    if key == DOWN:
        return menus, current + 1 if current < len(items) else 1, None
    if key.startswith("#"):
        digit = int(key[1:])
        return menus, next(n for n, i in enumerate(items, 1) if i.digit == digit), None
    if key.startswith("@"):
        return menus, next(n for n, i in enumerate(items, 1) if i.letter == key[1:]), None
    m = copy.deepcopy(menus)
    item = m.items()[current - 1]
    if key == ENTER:
        done = m.enter(item)
        if isinstance(done, tuple):
            return m, current, done
        return m, 1 if done else current, None
    if key == RIGHT:
        return m, 1 if m.right(item) else current, None
    if key == LEFT:
        return m, 1 if m.back() else current, None
    raise ValueError(key)


def fewest_keys(context, limit=6):
    """Every action reachable from the top within `limit` keys, with its fewest keys."""
    start = P.PlayMenus(context)
    best = {}
    frontier = [(start, 1)]
    seen = set()
    for depth in range(1, limit + 1):
        nxt = []
        for menus, current in frontier:
            _items, keys = keys_of(menus, current)
            for key in keys:
                m, cur, chosen = press(menus, current, key)
                if chosen is not None:
                    best.setdefault(chosen, depth)
                    continue
                state = (m.level, m.group, m.parent, cur)
                if state in seen:
                    continue
                seen.add(state)
                nxt.append((m, cur))
        frontier = nxt
    return best


def listed_offense():
    return [c for c in C.OFFENSE if not set(c.situations) & P.ASKED]


def test_the_original_items_stay_first_in_their_places_with_their_digits():
    items = P.PlayMenus(P.Context(side="O")).items()
    for n in range(1, 8):
        assert items[n - 1].text_id == "=" + OFFENSE_ITEMS[n - 1].strip()[3:] and items[n - 1].digit == n % 10
    assert [i.action for i in items[7:10]] == [("pick", 8), ("pick", 9), ("pick", 10)]
    defense = P.PlayMenus(P.Context(side="D")).items()
    for n in range(1, 7):
        assert defense[n - 1].text_id == "=" + DEFENSE_ITEMS[n - 1].strip()[3:] and defense[n - 1].digit == n


def test_the_usual_call_is_the_originals_two_keys():
    best = fewest_keys(P.Context(side="O"), limit=2)
    assert best[("pick", 1)] == 1                       # the first item is current at the prompt: Enter alone, as in the original
    for family in (2, 3, 4, 5, 8, 9, 10):
        assert best[("pick", family)] == 2
    assert best[("kick", 6)] == 2 and best[("kick", 7)] == 2
    best = fewest_keys(P.Context(side="D"), limit=2)
    assert best[("pick", 1)] == 1 and all(best[("pick", f)] == 2 for f in range(2, 7))


def test_every_listed_offense_play_and_kick_is_at_most_six_keys_away():
    best = fewest_keys(P.Context(side="O"))
    missing = [c.id for c in listed_offense() if ("call", c.id) not in best]
    assert missing == []
    for kid in ("K011", "K012", "K013", "K014", "K015", "K016", "K021", "K022", "K023"):
        assert best[("call", kid)] <= 4                  # Right on Punt or Field Goal, then the digit and Enter
    first_lists = [c.id for c in C.OFFENSE if C.GROUP_BY_KEY[c.group].family and C.GROUP_BY_KEY[c.group].order == 1]
    assert all(best[("call", i)] <= 4 for i in first_lists)


def test_every_defense_call_is_at_most_six_keys_away_and_kick_defense_four_on_fourth_down():
    best = fewest_keys(P.Context(side="D"))
    assert [c.id for c in C.DEFENSE if ("call", c.id) not in best] == []
    fourth = fewest_keys(P.Context(side="D", fourth_down=True), limit=4)
    assert all(fourth[("call", k)] <= 4 for k in ("K031", "K032", "K033", "K034", "K035", "K036"))


def test_the_kickoff_menu_puts_the_deep_kick_first_so_enter_keeps_the_originals_pace():
    items = P.kickoff_items()
    assert items[0].action == ("call", "K001") and [i.action[1] for i in items] == ["K001", "K002", "K003", "K004"]
    assert P.kickoff_items(safety=True)[-1].action == ("call", "K027")


@pytest.mark.parametrize("context", [
    P.Context(side="O"), P.Context(side="O", two_point=True), P.Context(side="O", kneel_helps=True, spike_helps=True),
    P.Context(side="O", last_call="O001", favourites=("O027", "O031")), P.Context(side="D", fourth_down=True),
    P.Context(side="D", last_call="D017", favourites=("D011",)), P.Context(side="O", qb_on=False)])
def test_no_level_gives_t_s_or_c_to_an_item_and_letters_are_unique(context):
    menus = P.PlayMenus(context)
    levels = [menus.items()]
    for item in menus.items():
        m = copy.deepcopy(menus)
        if m.enter(item) is True:
            levels.append(m.items())
        m = copy.deepcopy(menus)
        if m.right(item):
            levels.append(m.items())
    for items in levels:
        letters = [i.letter for i in items if i.letter]
        assert len(letters) == len(set(letters))
        assert not set(letters) & set(P.RESERVED)
        digits = [i.digit for i in items if i.digit >= 0]
        assert len(digits) == len(set(digits))


def test_right_walks_a_familys_lists_and_left_goes_back():
    menus = P.PlayMenus(P.Context(side="O"))
    plunge = menus.items()[0]
    assert menus.right(plunge) and menus.group == "og01"
    assert menus.heading() == (C.group_text_id(C.GROUP_BY_KEY["og01"]), 1, 2)
    assert menus.right(menus.items()[0]) and menus.group == "og02"
    assert menus.right(menus.items()[0]) and menus.group == "og01"          # it wraps
    assert menus.back() and menus.level == P.TOP and not menus.back()


def test_more_plays_lists_the_other_groups_then_find_and_back():
    menus = P.PlayMenus(P.Context(side="O"))
    more = next(i for i in menus.items() if i.action[0] == P.MORE)
    assert more.letter == "m" and menus.enter(more) is True
    items = menus.items()
    assert [i.action[1] for i in items[:10]] == [g.key for g in C.GROUPS if g.side == "O" and g.family == 0]
    assert [i.digit for i in items[:10]] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 0]
    assert items[10].action == ("find", 0) and items[10].letter == "n" and items[11].action == ("back", 0)
    menus.enter(items[0])                                       # Play Action
    assert menus.level == P.LIST and menus.back() and menus.level == P.MORE_LEVEL


def test_favourites_and_again():
    favs = ()
    for pid in ("O027", "O031", "O027"):
        favs, said = P.add_favourite(favs, pid)
    assert favs == ("O027", "O031") and said == P.TEXT["fav_added"]
    for n in range(20):
        favs, said = P.add_favourite(favs, "O%03d" % (60 + n))
    assert len(favs) == P.FAVOURITES_MAX and said == P.TEXT["fav_full"]
    favs, said = P.remove_favourite(favs, "O027")
    assert "O027" not in favs and said == P.TEXT["fav_removed"]
    menus = P.PlayMenus(P.Context(side="O", last_call="O033"))
    again = next(i for i in menus.items() if i.action[0] == P.AGAIN)
    assert again.letter == "a" and again.extra == C.BY_ID["O033"].text_id and menus.enter(again) == ("call", "O033")
    assert not any(i.action[0] == P.FAVOURITES for i in menus.items())


def test_the_typed_search_finds_plays_by_any_word_of_their_name():
    menus = P.PlayMenus(P.Context(side="O"))
    assert menus.search("mesh") == 1 and menus.level == P.FOUND
    assert menus.items()[0].action == ("call", "O027")
    menus.reset()
    assert menus.search("zone") >= 4 and len(menus.items()) <= C.MAX_PER_GROUP + 1
    menus.reset()
    assert menus.search("xyz") == 0 and menus.level == P.TOP
    defense = P.PlayMenus(P.Context(side="D"))
    assert defense.search("cover three") >= 4 and all(C.BY_ID[i].side in "DK" for i in defense.found)
    menus.reset()
    menus.search("kick")                          # the kick-offs have their own menu; the try's and fair catch kicks a question
    assert not {"K001", "K002", "K003", "K004", "K024", "K025", "K027"} & set(menus.found)
    menus.reset()
    assert menus.search("swinging") == 0          # a try play, offered only on a try
    tries = P.PlayMenus(P.Context(side="O", two_point=True))
    assert tries.search("swinging") == 1
    assert "K026" not in [c.id for c in P.concepts_of("og17", P.Context(side="O"))]


def test_the_try_offers_the_five_original_items_and_the_goal_line_list():
    menus = P.PlayMenus(P.Context(side="O", two_point=True))
    items = menus.items()
    assert [i.action for i in items[:5]] == [("pick", n) for n in range(1, 6)]
    assert not any(i.action in (("kick", 6), ("kick", 7), ("pick", 8)) for i in items)
    goal = P.concepts_of("og17", menus.context)
    assert "K026" in [c.id for c in goal] and "O148" in [c.id for c in goal]


def test_the_settings_level_and_every_text_the_menus_say_exist():
    menus = P.PlayMenus(P.Context(side="O"))
    menus.enter(next(i for i in menus.items() if i.action[0] == P.SETTINGS))
    assert [i.action[1] for i in menus.items()[:-1]] == list(P.OFFENSE_SETTINGS)
    for text_id in list(P.TEXT.values()) + list(P.SETTING_TEXT.values()) + list(P.SETTING_VALUE_TEXT.values()):
        assert text_id in X.TEXTS, text_id
    assert all(C.group_text_id(g) in X.TEXTS for g in C.GROUPS)
    assert len(set(P.SETTING_VALUE_TEXT.values())) == len(P.SETTING_VALUE_TEXT)
