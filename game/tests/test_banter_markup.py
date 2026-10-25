"""The banter line markup (game/banter_markup.py) and the pool (game/banter_pool.py). This is inspired by Jim Kitchen.

D-035, D-048, CUSTOMIZABLE_CONTENT 12. What was written down before the code: a line is parts and actions; `[then]` ends a
part, `[faster]` ends it and speeds the next, a sound or bleep or pause ends it too; `[name]`, `[opponent quarterback]` and
`[one of: a | b]` sit inside a part; an unknown word is spoken as text and reported; an unclosed bracket, a sound name with a
folder, a line over 500 characters or 20 pieces, a control character, or a line that says nothing is a bad line; the 142
original lines written as markup and read back are the original lines (spaces apart).
"""
import pytest

from nfl4.data.customlists import Problems
from nfl4.game.banter_lines import LINES, NAME, OPPONENT_QB
from nfl4.game.banter_markup import (Bleep, NameRef, OneOf, OppQbRef, Pause, Sound, Speak, Text, choice_sizes,
                                     default_pieces, parse_markup, speak_text, to_markup)
from nfl4.game.banter_pool import (DEFAULT_LINES, DEFAULT_MARKUP, DEFAULT_POOL, BanterPool, banter_id, banter_number,
                                   build_pool)


def parse_ok(text):
    parsed = parse_markup(text)
    assert parsed.pieces is not None, parsed.problems
    return parsed


# ----- the original lines as markup -----

def test_the_142_original_lines_are_the_defaults_with_their_numbers_and_ids():
    assert [line.number for line in DEFAULT_LINES] == list(range(1, 143)) and DEFAULT_POOL.size == 142
    assert all(line.builtin for line in DEFAULT_LINES)
    assert [banter_id(n) for n in (1, 45, 142, 143)] == ["B001", "B045", "B142", "B143"]
    assert [banter_number(x) for x in ("B045", "b45", "B1", "B9999", "B0", "B10000", "T01", "B", "B12x")] == \
        [45, 45, 1, 9999, None, None, None, None, None]


def test_every_original_line_written_as_markup_and_read_back_is_the_same_line_apart_from_the_outer_spaces():
    for line in DEFAULT_LINES:
        parsed = parse_ok(line.markup)
        assert parsed.problems == [], (line.number, parsed.problems)
        assert to_markup(parsed.pieces) == line.markup
        words = lambda pieces: [(type(p).__name__, getattr(p, "faster", None), speak_stripped(p)) for p in pieces]
        assert words(parsed.pieces) == words(line.pieces), line.number


def speak_stripped(piece):
    if not isinstance(piece, Speak):
        return None
    items = []
    for item in piece.items:
        if isinstance(item, Text):
            text = item.text.strip() if item is piece.items[0] or item is piece.items[-1] else item.text
            if text != "":                                  # the original's " <NAME> ..." has a blank text before the name
                items.append(("text", text))
        elif isinstance(item, OneOf):
            items.append(("oneof", tuple(tuple(sub.text.strip() if isinstance(sub, Text) else type(sub).__name__
                                               for sub in option) for option in item.options)))
        else:
            items.append((type(item).__name__,))
    return tuple(items)


def test_the_longest_original_line_in_markup_is_far_below_the_limit():
    longest = max(len(line.markup) for line in DEFAULT_LINES)
    assert longest < 300, longest                       # S7.7 measured it: the limit of 500 leaves a wide margin
    assert max(len(line.pieces) for line in DEFAULT_LINES) <= 4


def test_the_originals_pieces_say_what_the_lifted_routine_says():
    by_number = {line.number: line for line in DEFAULT_LINES}
    assert by_number[1].pieces == (Speak((Text(" It looks like "), NameRef(), Text(" is shaken up on the play "))),)
    assert [type(p) for p in by_number[69].pieces] == [Speak, Bleep, Speak]               # holy, bleep, Ghip!
    assert [type(p) for p in by_number[75].pieces] == [Speak, Bleep, Bleep]               # holy, two bleeps
    assert by_number[113].pieces[0].faster is True and by_number[1].pieces[0].faster is False
    assert isinstance(by_number[101].pieces[1].items[0], OneOf) and len(by_number[101].pieces[1].items[0].options) == 5
    assert len(by_number[110].pieces[1].items[0].options) == 3
    assert by_number[45].pieces[0].items[1] == OppQbRef()
    assert to_markup(by_number[69].pieces) == "Holy [bleep] Ghip!"
    assert to_markup(by_number[8].pieces) == ("Here are some scores from other games being played today [then] "
                                               "3 to 0  7 to 3  and 14 to 0  in the fourth")


def test_the_speech_of_every_original_line_equals_the_original_texts_for_every_choice():
    for line in LINES:
        built = default_pieces(line)
        alternatives = max(1, len(line.alternatives))
        for choice in range(1, alternatives + 1):
            texts = [speak_text(p, "Smith", "Starr", iter([choice])) for p in built if isinstance(p, Speak)]
            expected_first = line.first.replace(NAME, "Smith").replace(OPPONENT_QB, "Starr")
            second = line.alternatives[choice - 1] if line.alternatives else line.second
            expected = [expected_first] + ([second.replace(NAME, "Smith").replace(OPPONENT_QB, "Starr")] if second else [])
            assert texts == expected, line.number


# ----- reading a player's line -----

def test_text_only_sound_only_and_mixed_lines():
    only_text = parse_ok("What a hit!").pieces
    assert only_text == (Speak((Text("What a hit!"),)),)
    only_sound = parse_ok("[sound crowd boo.wav]").pieces
    assert only_sound == (Sound("crowd boo.wav"),)
    mixed = parse_ok("what a hit! [sound crunch.wav] Ghip, did you see that?").pieces
    assert mixed == (Speak((Text("what a hit!"),)), Sound("crunch.wav"), Speak((Text("Ghip, did you see that?"),)))


def test_the_words_are_not_case_sensitive_and_spaces_inside_them_do_not_matter():
    pieces = parse_ok("[ NAME ] is [Opponent   Quarterback] [BLEEP] [Sound  My Laugh.WAV ] [PAUSE] [Pause 2.5]").pieces
    assert pieces[0].items == (NameRef(), Text(" is "), OppQbRef())
    assert pieces[1:] == (Bleep(), Sound("My Laugh.WAV"), Pause(None), Pause(2.5))


def test_then_ends_a_part_and_faster_ends_it_and_speeds_the_next_part_only():
    pieces = parse_ok("one [then] two [faster] three [then] four").pieces
    assert [(p.items[0].text, p.faster) for p in pieces] == [("one", False), ("two", False), ("three", True), ("four", False)]
    assert parse_ok("[faster] quick").pieces == (Speak((Text("quick"),), True),)
    # a faster that is followed by a sound still speeds the next part
    assert parse_ok("[faster] [bleep] words").pieces == (Bleep(), Speak((Text("words"),), True))


def test_one_of_is_a_choice_inside_a_part_and_may_use_the_names():
    pieces = parse_ok("Ghip, [one of: [name] is great | you stink | what?] ok").pieces
    assert len(pieces) == 1 and isinstance(pieces[0].items[1], OneOf)
    assert pieces[0].items[1].options == ((NameRef(), Text(" is great")), (Text("you stink"),), (Text("what?"),))
    assert choice_sizes(pieces) == [3]
    assert speak_text(pieces[0], "Smith", "", iter([1])) == "Ghip, Smith is great ok"
    assert speak_text(pieces[0], "Smith", "", iter([3])) == "Ghip, what? ok"
    assert speak_text(pieces[0], "x", "", iter([99])) == "Ghip, what? ok"           # an out-of-range choice stays inside
    assert choice_sizes(parse_ok("[one of: a|b] and [one of: c|d|e]").pieces) == [2, 3]


def test_a_blank_part_says_nothing_and_a_line_that_says_nothing_is_bad():
    assert parse_ok("a [then]   [then] b").pieces == (Speak((Text("a"),)), Speak((Text("b"),)))
    for text in ("", "   ", "[then]", "[faster]", "[one of: ]", "[one of: | ]"):
        parsed = parse_markup(text)
        assert parsed.pieces is None and any("nothing" in p for p in parsed.problems), (text, parsed.problems)


def test_an_unknown_word_is_spoken_as_text_and_reported():
    parsed = parse_ok("a [laugh] b")
    assert parsed.pieces == (Speak((Text("a [laugh] b"),)),)
    assert len(parsed.problems) == 1 and "[laugh]" in parsed.problems[0]
    assert parse_ok("[pause 0]").problems and parse_ok("[pause 99]").problems and parse_ok("[pause 2]").problems == []
    nested = parse_ok("[one of: a [bleep] b | c]")
    assert nested.problems and nested.pieces[0].items[0].options[0] == (Text("a [bleep] b"),)


def test_bad_lines():
    cases = {
        "an unclosed [bracket": "closing bracket",
        "a [one of: a | [name] b": "closing bracket",
        "[sound]": "no file name",
        "[sound ]": "no file name",
        "[sound folder\\x.wav]": "folder",
        "[sound a/b.wav]": "folder",
        "[sound c:x.wav]": "folder",
        "[sound .hidden.wav]": "folder",
        "[sound CON.wav]": "device",
        "[sound nul]": "device",
        "[sound Com1.wav]": "device",
        "[sound lpt9 .wav]": "device",
        "[pause 10] [pause 10] [pause 10] [pause 1]": "30 seconds of pauses",
        "x" * 501: "500 characters",
        "tab\there": "control character",
        "[bleep] " * 21: "20 pieces",
        "[one of: " + " | ".join("a%d" % n for n in range(21)) + "]": "20 choices",
    }
    for text, reason in cases.items():
        parsed = parse_markup(text)
        assert parsed.pieces is None and any(reason in problem for problem in parsed.problems), (text, parsed.problems)
    assert parse_ok("x" * 500).pieces and parse_ok("[bleep] " * 20).pieces                  # the limits themselves are fine
    assert parse_ok("a ] b").pieces == (Speak((Text("a ] b"),)),)                        # a stray closing bracket is text


def test_markup_written_from_pieces_reads_back_the_same_pieces():
    for text in ("[faster] a [name] b [then] c [bleep] [bleep] [sound x y.wav] [pause] [pause 2.5] d [one of: a | [name] | b]",
                 "[sound only.wav]", "[bleep]", "[pause]", "one [then] two [then] three"):
        first = parse_ok(text).pieces
        assert parse_ok(to_markup(first)).pieces == first


# ----- the pool -----

def problems():
    return Problems("banter.txt")


def test_with_no_entries_the_pool_is_the_original_142():
    pool = build_pool({}, problems())
    assert [line.number for line in pool.lines] == list(range(1, 143)) and pool.off == ()
    assert all(a is b for a, b in zip(pool.lines, DEFAULT_LINES))


def test_the_markup_of_an_original_line_is_the_original_line_itself_with_its_exact_spaces():
    pool = build_pool({n: DEFAULT_MARKUP[n] for n in (1, 45, 113)}, problems())
    assert pool.lines[0] is DEFAULT_LINES[0] and pool.lines[44] is DEFAULT_LINES[44]
    assert pool.lines[0].pieces[0].items[0] == Text(" It looks like ")


def test_a_replaced_line_an_off_line_and_an_added_line():
    p = problems()
    pool = build_pool({45: "My own words", 46: None, 143: "Added [name]", 200: "[sound a.wav]", 201: None}, p)
    assert p.count == 0
    assert pool.off == (46,) and pool.size == 142 - 1 + 2
    by_number = {line.number: line for line in pool.lines}
    assert by_number[45].builtin is False and by_number[45].pieces == (Speak((Text("My own words"),)),)
    assert 46 not in by_number and 201 not in by_number
    assert by_number[143].pieces == (Speak((Text("Added "), NameRef())),) and by_number[200].pieces == (Sound("a.wav"),)
    assert pool.numbers() == sorted(pool.numbers())


def test_a_bad_line_keeps_the_original_or_is_left_out_and_is_counted_once_per_entry():
    p = problems()
    pool = build_pool({45: "bad [bracket", 143: "bad [bracket", 144: "a [laugh]"}, p)
    by_number = {line.number: line for line in pool.lines}
    assert by_number[45] is DEFAULT_LINES[44] and 143 not in by_number and 144 in by_number
    assert p.count == 3 and any("the original line is used" in m for m in p.messages)
    assert any("left out" in m for m in p.messages)


def test_all_lines_off_is_an_empty_pool_and_a_pool_of_one_line_works():
    pool = build_pool({n: None for n in range(1, 143)}, problems())
    assert pool.size == 0 and pool.off == tuple(range(1, 143))
    one = build_pool({**{n: None for n in range(2, 143)}}, problems())
    assert one.numbers() == [1]
    many = build_pool({n: "line %d" % n for n in range(143, 643)}, problems())
    assert many.size == 142 + 500
