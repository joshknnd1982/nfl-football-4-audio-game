"""The news lines of the Franchise and news.txt (nfl4 only, rule 0.13; CUSTOMIZABLE_CONTENT 13 L16, CLAUDE.md 0.12, playbook 7.9 and 7.10;
PX SX.8e). This is inspired by Jim Kitchen.

The defaults are STRINGS_NX's lines; a player's line replaces, `off` switches off, a new number adds; [name] and [opponent quarterback]
are refused (the news is told between games); the draw is never one of the last three; news.txt heals like every list of the customize
folder and is read only with the N. F. L. rules.
"""
import os
import random
import re

import pytest

from drrig import SURNAMES
from filedamage import BYTE_DAMAGES, apply, holding
from frrig import COACH_AND_TEAM, ENTER, WANT_FRANCHISE, franchise_rig, quit_policy, run_until, spoken
from nfl4.data import customlists as cl
from nfl4.data.customize import Customization
from nfl4.extras import nx_texts as X
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import history, news
from nfl4.extras.franchise import news_pools as NP
from nfl4.extras.franchise.league import new_league
from nfl4.game.banter_markup import Bleep, Pause, Speak, Text
from nfl4.game.rnd import GameRandom
from randsources import ScriptedRandom, value_for

GAME = "NFL Football 4"
WORDS = history.Words(lambda team: "Team%d" % team)


# ----- the defaults -----

def test_the_thirteen_pools_are_the_lines_of_strings_nx_with_their_exact_spaces():
    assert NP.POOLS == D.NEWS_POOLS and len(NP.POOLS) == 13
    for pool in NP.POOLS:
        lines = NP.DEFAULT_POOLS.lines(pool)
        assert [r.id for r in lines] == ["%s0%d" % (pool, n) for n in (1, 2, 3, 4)] == list(X.REMARK_POOLS[pool])
        for remark in lines:
            assert remark.builtin and remark.pieces == (Speak((Text(X.TEXTS[remark.id]),)),)
            assert remark.markup == X.TEXTS[remark.id].strip()
    assert NP.DEFAULT_POOLS.size == 52


def test_every_default_line_uses_only_the_placeholders_of_its_pool():
    for pool in NP.POOLS:
        for remark in NP.DEFAULT_POOLS.lines(pool):
            used = set(re.findall(r"<[^<>]{1,30}>", X.TEXTS[remark.id]))
            assert used <= set(NP.PLACEHOLDERS[pool]), (remark.id, used)


def test_the_file_of_the_defaults_lists_every_default_line(tmp_path):
    entries = NP.default_entries()
    assert entries == [(r.id, r.markup) for pool in NP.POOLS for r in NP.DEFAULT_POOLS.lines(pool)]
    text = Customization(str(tmp_path / "customize")).default_text("news")
    assert text.startswith("# NFL Football 4 news, format 1.\n")
    parsed = cl.parse_list(text, GAME, "news")
    assert [(e.id, e.value) for e in parsed.entries] == entries and parsed.bad_lines == []


@pytest.mark.parametrize("entry_id, parsed", [("NWB01", ("NWB", 1)), ("nwb1", ("NWB", 1)), ("NwB0001", ("NWB", 1)), ("NWP9999", ("NWP", 9999)),
                                              ("NWB0", None), ("NWB10000", None), ("NWX01", None), ("TO01", None), ("B001", None),
                                              ("NW01", None), ("NWBB1", None)])
def test_news_ids(entry_id, parsed):
    assert NP.parse_id(entry_id) == parsed


# ----- the player's lines -----

def entries_of(text):
    return cl.parse_list(cl.render_list(GAME, "news", NP.NOTES, []) + text, GAME, "news").entries


def pools_of(text):
    problems = cl.Problems("news.txt")
    return NP.build_pools(NP.overrides_of(entries_of(text), problems), problems), problems


def test_a_line_is_changed_switched_off_added_or_kept_when_it_is_bad():
    pools, problems = pools_of("NWB02 = what a win [bleep]\nNWB03 = off\nNWB05 = [pause] <team> again\nNWB04 = [unclosed\n"
                               "NWB06 = [sound ../x.wav]\nnwb01 = " + X.TEXTS["NWB01"].strip() + "\n")
    lines = {r.id: r for r in pools.lines("NWB")}
    assert sorted(lines) == ["NWB01", "NWB02", "NWB04", "NWB05"]
    assert lines["NWB02"].pieces == (Speak((Text("what a win"),)), Bleep()) and not lines["NWB02"].builtin
    assert lines["NWB05"].pieces == (Pause(), Speak((Text("<team> again"),)))
    assert lines["NWB04"].builtin and lines["NWB01"].builtin                 # bad: the original; exactly the original: builtin
    assert problems.count == 2                                                # NWB04 and NWB06


def test_the_banter_names_are_not_allowed_in_the_news_and_the_default_or_nothing_is_used():
    pools, problems = pools_of("NWB01 = [name] won\nNWB06 = [opponent quarterback] lost\nNWB07 = x [one of: a | [name]]\n")
    lines = {r.id: r for r in pools.lines("NWB")}
    assert lines["NWB01"].builtin and "NWB06" not in lines and "NWB07" not in lines
    assert problems.count == 3 and all("not known in the news" in m for m in problems.messages)


def test_an_unknown_placeholder_of_the_pool_is_counted_and_spoken_as_written():
    pools, problems = pools_of("NWS05 = <team> and <other> and <player>\n")
    assert [r.id for r in pools.lines("NWS")][-1] == "NWS05"
    assert problems.count == 1 and "<other>" in problems.messages[0] and "<player>" in problems.messages[0]
    ok, none = pools_of("NWP05 = <player> <position> <r> <team> <coach>\n")
    assert none.count == 0


def test_ids_that_are_not_news_twice_or_empty_are_problems():
    pools, problems = pools_of("TO01 = no\nXY01 = no\nNWB02 = first\nNWB02 = second\nNWB03 =\n")
    assert {r.id: r for r in pools.lines("NWB")}["NWB02"].pieces == (Speak((Text("first"),)),)
    assert problems.count == 4


def test_the_examples_of_the_players_guide_work_as_written():
    from pathlib import Path
    guide = (Path(__file__).resolve().parent.parent / "CUSTOMIZE.md").read_text(encoding="utf-8")
    lines = [line.strip() for line in guide.splitlines() if line.strip().startswith(("NWB05 = ", "NWY05 = "))]
    assert len(lines) == 2
    pools, problems = pools_of("\n".join(lines) + "\n")
    assert problems.count == 0
    assert pools.lines("NWB")[-1].id == "NWB05" and pools.lines("NWY")[-1].id == "NWY05"


def test_every_line_off_means_a_kind_of_news_is_never_told():
    pools, _ = pools_of("".join("NWB%02d = off\n" % n for n in range(1, 5)))
    assert pools.lines("NWB") == () and len(pools.lines("NWU")) == 4


# ----- the line a piece of news becomes -----

def strict(*picks):
    rnd = GameRandom(ScriptedRandom([value_for(n, k) for n, k in picks], strict=True))
    rnd.trace = []
    return rnd


def a_league():
    return new_league(GameRandom(random.Random(3)), SURNAMES, "Kim", 5, "20260101-000000")


def test_a_choice_in_a_line_is_drawn_after_the_line_and_kept_as_the_words_chosen():
    pools, _ = pools_of("".join("NWB%02d = off\n" % n for n in range(1, 5)) + "NWB05 = <team> win [one of: big | small | huge], says <coach>\n")
    league = a_league()
    rnd = strict((1, 1), (3, 2))
    made = news.make_entries(league, [news.Event("NWB", team=1, other=2, n=7, score=(27, 20))], pools, WORDS, rnd, 3)
    assert made[0]["markup"] == "Team1 win small, says Kim" and rnd.trace == [1, 3]


def test_a_sound_a_pause_and_a_bleep_stay_in_the_kept_line():
    pools, _ = pools_of("".join("NWB%02d = off\n" % n for n in range(1, 5)) + "NWB05 = [sound hooray.wav] <team> [pause 2] [bleep]\n")
    league = a_league()
    made = news.make_entries(league, [news.Event("NWB", team=1, other=2, n=7, score=(27, 20))], pools, WORDS, strict((1, 1)), 3)
    markup = made[0]["markup"]
    assert "[sound hooray.wav]" in markup and "Team1" in markup and "[pause 2]" in markup and "[bleep]" in markup


def test_a_changed_line_is_the_one_a_week_of_a_franchise_tells(tmp_path):
    pools, _ = pools_of("".join("NW%s%02d = off\n" % (kind, n) for kind in "BC" for n in range(1, 5))
                        + "NWB05 = the big one was won by <team>.\nNWC05 = the close one was won by <team>.\n")

    def setup(rig):
        rig.game.news_pools = pools
    rig = franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM + [ENTER, ENTER, ENTER, ENTER], policy=quit_policy)
    setup(rig)
    run_until(rig)
    text = spoken(rig)
    assert any(t.startswith("the big one was won by ") for t in text) and any(t.startswith("the close one was won by ") for t in text)
    assert not any(t.startswith("a big win for the") for t in text)


# ----- news.txt in the customize folder (7.10) -----

def write(folder, text):
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "news.txt"), "w", encoding="utf-8", newline="\r\n") as handle:
        handle.write(cl.header_line(GAME, "news") + "\n" + text)


def test_the_players_news_txt_is_read_and_its_problems_said_once(tmp_path):
    folder = str(tmp_path / "customize")
    write(folder, "NWB02 = off\nNWB09 = <team> again\nNWB04 = [oops\n")
    custom = Customization(folder, extras=True)
    assert [r.id for r in custom.snapshot.news.lines("NWB")] == ["NWB01", "NWB03", "NWB04", "NWB09"]
    assert custom.take_notices() == [" 1 problem found in news.txt, details are in the log. "]
    assert custom.take_notices() == []


def test_with_classic_rules_news_txt_is_never_made_or_read_and_with_the_nfl_rules_it_is(tmp_path):
    folder = str(tmp_path / "customize")
    classic = Customization(folder)
    assert classic.snapshot.news is None and not os.path.exists(os.path.join(folder, "news.txt"))
    assert "news" not in [spec.key for spec in classic.specs]
    classic.use_extras(True)
    assert os.path.exists(os.path.join(folder, "news.txt")) and classic.snapshot.news.size == 52
    classic.use_extras(False)
    assert classic.snapshot.news is None


@pytest.mark.parametrize("kind", BYTE_DAMAGES)
def test_a_damaged_news_txt_is_copied_aside_and_made_again_or_read_in_part(tmp_path, kind):
    folder = str(tmp_path / "customize")
    Customization(folder, extras=True)
    path = os.path.join(folder, "news.txt")
    original = open(path, "rb").read()
    apply(kind, path)
    damaged = open(path, "rb").read()
    custom = Customization(folder, extras=True)
    notices = custom.take_notices()
    pools = custom.snapshot.news
    if kind in ("cut_in_half", "bad_line_in_the_middle"):
        assert not os.path.exists(path + ".damaged1")
        assert [r.id for r in pools.lines("NWB")] == ["NWB01", "NWB02", "NWB03", "NWB04"]
    else:
        assert open(path + ".damaged1", "rb").read() == damaged
        assert open(path, "rb").read() == original
        assert notices == [" The file news.txt was damaged and has been reset to the original news lines. A copy was saved. "]
        assert pools.lines("NWB") == NP.DEFAULT_POOLS.lines("NWB")
        assert Customization(folder, extras=True).take_notices() == []        # the next start says nothing more
    if kind == "bad_line_in_the_middle":
        assert notices == [" 2 problems found in news.txt, details are in the log. "]


def test_a_news_txt_held_by_another_program_is_not_damage(tmp_path):
    folder = str(tmp_path / "customize")
    write(folder, "NWB01 = mine\n")
    custom = Customization(folder, extras=True)
    with holding(os.path.join(folder, "news.txt")):
        notices = custom.reload()
    assert any("news.txt is in use by another program. The news lines you already had stay in use." in n for n in notices)
    assert custom.snapshot.news.lines("NWB")[0].pieces == (Speak((Text("mine"),)),)


def test_reset_of_one_list_writes_the_originals_and_keeps_the_players_file(tmp_path):
    folder = str(tmp_path / "customize")
    write(folder, "NWB01 = mine\n")
    custom = Customization(folder, extras=True)
    result = custom.reset("news")
    assert result.done == ["news.txt"] and result.kept == ["news.txt"]
    assert "mine" in open(os.path.join(folder, "news.txt.before-reset"), encoding="utf-8").read()
    assert "mine" not in open(os.path.join(folder, "news.txt"), encoding="utf-8").read()


def test_the_check_tries_the_sound_files_of_the_news_lines(tmp_path):
    folder = str(tmp_path / "customize")
    write(folder, "NWB05 = [sound nothere.wav] <team>\n")
    text = Customization(folder, extras=True).check()
    assert "news.txt: no problems." in text and "The news lines name 1 sound file, 1 cannot be used." in text and "The remarks name" not in text


def test_a_fuzz_of_damaged_news_files_never_raises_and_always_leaves_a_usable_pool(tmp_path):
    rng = random.Random(29)
    folder = str(tmp_path / "customize")
    Customization(folder, extras=True)
    path = os.path.join(folder, "news.txt")
    good = open(path, "rb").read()
    for case in range(60):
        raw = bytearray(good)
        for _ in range(rng.randint(1, 20)):
            raw[rng.randrange(len(raw))] = rng.randrange(256)
        with open(path, "wb") as handle:
            handle.write(bytes(raw[:rng.randint(0, len(raw))]))
        custom = Customization(folder, extras=True)
        assert isinstance(custom.snapshot.news, NP.NewsPools)
        for pool in NP.POOLS:
            for remark in custom.snapshot.news.lines(pool):
                assert remark.pieces


# ----- what is filled into a line (the review's findings) -----

def one_line_pool(pool, line):
    others = "".join("%s%02d = off\n" % (pool, n) for n in range(1, 5))
    return pools_of(others + "%s05 = %s\n" % (pool, line))[0]


def test_a_name_with_brackets_cannot_make_a_word_of_the_markup():
    league = a_league()
    names = history.Words(lambda team: "Sea [hawks" if team == 1 else "Bears [pause]")
    pools = one_line_pool("NWB", "the <team> beat the <other>.")
    made = news.make_entries(league, [news.Event("NWB", team=1, other=2, n=7, score=(27, 20))], pools, names, strict((1, 1)), 3)
    assert made[0]["markup"] == "the Sea (hawks beat the Bears (pause)."
    from nfl4.game.banter_markup import parse_markup
    assert parse_markup(made[0]["markup"]).pieces == (Speak((Text("the Sea (hawks beat the Bears (pause)."),)),)


def test_a_line_that_the_names_make_too_long_is_replaced_by_the_first_default_line_and_the_record_still_passes_its_check():
    from nfl4.game.banter_markup import parse_markup
    league = a_league()
    league.coach = "c" * 30
    pools = one_line_pool("NWY", "<coach>" * 71)                              # 497 characters: no problem for news.txt
    made = news.make_entries(league, [news.Event("NWY", team=5, n=3)], pools, WORDS, strict((1, 1)), 3)
    assert made[0]["markup"] == X.TEXTS["NWY01"].strip().replace("<coach>", "c" * 30).replace("<n>", "3")
    assert parse_markup(made[0]["markup"]).pieces is not None and league.news_recent["NWY"] == ["NWY05"]
    from nfl4.extras.franchise.league import LeagueRecord
    LeagueRecord.from_json(league.to_json())                                 # it writes and reads back


def test_a_kind_of_news_fills_only_its_own_placeholders_the_others_stay_as_written():
    league = a_league()
    player = league.active_of(3)[0]
    pools = one_line_pool("NWR", "<player> after <n> seasons and <r> and <team>")
    made = news.make_entries(league, [news.Event("NWR", team=3, n=9, player=player, rating=80)], pools, WORDS, strict((1, 1)), 16)
    assert made[0]["markup"] == "%s after <n> seasons and <r> and Team3" % player.name
