"""The markup of a customizable line (game/banter_markup.py). This is inspired by Jim Kitchen.

D-035, D-048, CUSTOMIZABLE_CONTENT 12 and 13. What was written down before the code: a line is parts and actions; `[then]` ends a
part, `[faster]` ends it and speeds the next, a sound or bleep or pause ends it too; `[name]`, `[opponent quarterback]` and
`[one of: a | b]` sit inside a part; an unknown word is spoken as text and reported; an unclosed bracket, a sound name with a
folder, a line over 500 characters or 20 pieces, a control character, or a line that says nothing is a bad line. BC.2 (D-180): the
original's 142 banter lines and banter.txt's pool are gone from the game, and with them their tests; the markup stays for the pools of
remarks.txt, news.txt and injuries.txt.
"""
import pytest

from nfl4.game.banter_markup import (Bleep, NameRef, OneOf, OppQbRef, Pause, Sound, Speak, Text, choice_sizes, parse_markup,
                                     speak_text, to_markup)


def parse_ok(text):
    parsed = parse_markup(text)
    assert parsed.pieces is not None, parsed.problems
    return parsed


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
