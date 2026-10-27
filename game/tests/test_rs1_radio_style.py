"""RS.1 (D-179): the default lines of the radio pools follow the style guide made from real radio broadcasts
(spec/RADIO_NFL_STYLE.md, CLAUDE.md 0.33, playbook 7.24). This is inspired by Jim Kitchen.

The guide's numbers are the properties tested here: the pools keep their sizes and IDs (the game's draws do not move), the sentences are short
(the real calls' median is 8 to 9 words, the analyst's longest 20 to 24), no line gives the analyst a gender, every halftime line says the half
(the halftime line is certain, test_sy1_broadcast), and the guide itself exists with every heading of the template.
"""
import re
import statistics
from pathlib import Path

import pytest

from nfl4.data import customlists as cl
from nfl4.extras import nx_texts as X
from nfl4.extras import remarks as RM
from nfl4.extras.remarks_retired import RETIRED

SIZES = {"BN": 142, "ASK": 12, "CKO": 8, "CTD": 10, "CFG": 8, "CFM": 8, "CTV": 10, "CBG": 10, "CSK": 10, "CTC": 8, "CTS": 8, "CFD": 8,
         "CRZ": 8, "CPN": 8, "CHT": 8, "CFN": 8, "CFT": 6, "CTM": 8, "CQE": 8, "CTT": 8, "CBO": 8}
GUIDE = Path(__file__).resolve().parents[2] / "spec" / "RADIO_NFL_STYLE.md"


def lines(pool):
    return [X.TEXTS[i].strip() for i in X.REMARK_POOLS[pool]]


def sentence_lengths(texts):
    out = []
    for t in texts:
        for s in re.split(r"(?<=[.!?:])\s+", re.sub(r"<[a-z_]+>", "x", t)):
            if s.strip():
                out.append(len(s.split()))
    return out


def test_the_radio_pools_keep_their_sizes_and_ids():
    for pool, size in SIZES.items():
        assert len(X.REMARK_POOLS[pool]) == size, pool
    assert X.REMARK_POOLS["BN"][0] == "BN01" and X.REMARK_POOLS["BN"][-1] == "BN142"


def test_the_sentences_of_the_radio_pools_are_as_short_as_the_real_calls_asides():
    every = [t for pool in SIZES for t in lines(pool)]
    lengths = sorted(sentence_lengths(every))
    median, p90 = statistics.median(lengths), lengths[int(len(lengths) * 0.9)]
    assert median <= 13, median                       # B1 and B2: 8 and 9 for the calls, an analyst's thought runs to 15 or 20
    assert p90 <= 22, p90                             # B1 and B2: 20 and 24 at the 90th percentile
    assert max(len(t) for t in every) <= 150


def test_no_line_that_names_the_analyst_gives_the_analyst_a_gender():
    named = [t for pool in SIZES for t in lines(pool) if "<commentator>" in t]
    assert len(named) >= 14                           # the booth lines of BN and the twelve hand-offs
    for t in named:
        assert not re.search(r"\b(he|she|his|her|hers|him)\b", t.lower()), t


def test_every_halftime_line_says_the_half():
    for t in lines("CHT"):
        assert "half" in t.lower(), t


def test_the_radio_lines_do_not_use_the_old_jokes_words_of_the_snack_bar():
    stale = re.compile(r"\b(popcorn|antacid|hotdog|hot dog|beer|nachos|pizza)\b", re.I)
    for pool in SIZES:
        for t in lines(pool):
            assert not stale.search(t), (pool, t)


@pytest.mark.skipif(not GUIDE.exists(), reason="the spec folder is not beside the game (a source zip)")
def test_the_style_guide_has_every_heading_of_the_template():
    text = GUIDE.read_text(encoding="utf-8")
    for heading in ("## 1. Sources studied", "## 2. Numbers", "## 3. The shape of a broadcast", "## 4. The voice",
                    "## 5. Recurring moves", "## 6. Filler and atmosphere", "## 7. What the game takes",
                    "## 8. Checks the lines pass"):
        assert heading in text, heading
    assert "Whisper" in text and "work\\radio" in text      # the method and where the working material stays


# ----- the players who already have a remarks.txt (found in RS.1, fixesforgames B-P196) -----

def entries_of(pairs):
    return cl.parse_list(cl.render_list("NFL Football 4", "remarks", RM.NOTES, pairs), "NFL Football 4", "remarks").entries


def test_an_old_file_that_still_holds_the_earlier_defaults_gets_the_new_lines():
    """remarks.txt is made with every default line written out; an unchanged old line is the default, not the player's own."""
    assert len(RETIRED) >= 280 and all(rid in X.TEXTS for rid in RETIRED)
    old = [(rid, texts[0]) for rid, texts in RETIRED.items()]
    problems = cl.Problems("remarks.txt")
    assert RM.overrides_of(entries_of(old), problems) == {} and problems.items == []
    pools = RM.build_pools(RM.overrides_of(entries_of(old), problems), problems)
    assert [r.markup for r in pools.lines("BN")] == [X.TEXTS[i].strip() for i in X.REMARK_POOLS["BN"]]
    assert [r.markup for r in pools.lines("CTD")] == [X.TEXTS[i].strip() for i in X.REMARK_POOLS["CTD"]]


def test_a_line_the_player_changed_stays_theirs_and_the_current_defaults_are_no_override():
    rid = "BN01"
    old = RETIRED[rid][0]
    problems = cl.Problems("remarks.txt")
    kept = RM.overrides_of(entries_of([(rid, old + " And my own words."), ("BN02", "off"), ("BN03", "a new line of mine")]), problems)
    assert kept == {rid: old + " And my own words.", "BN02": None, "BN03": "a new line of mine"}
    current = [(i, X.TEXTS[i].strip()) for i in X.REMARK_POOLS["BN"]]
    assert RM.overrides_of(entries_of(current), problems) == {i: X.TEXTS[i].strip() for i in X.REMARK_POOLS["BN"]}   # as before: equal to the default is harmless
    assert not any(X.TEXTS[i].strip() in RETIRED.get(i, ()) for i in X.REMARK_POOLS["BN"])
