"""The conformance map (S8.1): every requirement of the frozen spec has a test, and the map says which. This is inspired by Jim Kitchen.

tests/data/conformance_map.tsv lists, for each requirement, the tests that check it. This file reads the spec and the map and
fails when a requirement has no row, when a row names something the spec does not have (a stale row), when an entry matches no
test function, or when a "not applicable" row gives no reason. A new requirement in the spec (or a renamed test) fails here, so
the map cannot drift. spec/CONFORMANCE_MATRIX.md is the readable form of the same map (work/s81/matrix_s81.py).

The requirements: GAME_SPEC sections 1 to 14 (the leaf headings), the quirks Q1 to Q62 of section 15, the seven bullets of 17.2,
the gap-register entries that close in S8.1, the 26 sounds the owner confirmed by ear (observations/), and, because the project is
nfl4, the cross-cutting requirements C1 to C10 and the features' requirements N1.1 to N7.7 of NFL_EXTRA_FEATURES.md (rule 0.13).
"""
import ast
import re
from functools import lru_cache
from pathlib import Path

import pytest

from specfiles import GAME_ROOT, SPEC, need

TESTS = Path(__file__).resolve().parent
MAP = TESTS / "data" / "conformance_map.tsv"


@lru_cache(maxsize=1)
def function_names() -> dict[str, list[str]]:
    """{test file stem without test_: [test function names]} (module functions and methods of test classes)."""
    found = {}
    for path in sorted(TESTS.glob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        found[path.stem[len("test_"):]] = [node.name for node in ast.walk(tree)
                                           if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")]
    return found


@lru_cache(maxsize=1)
def load_map() -> dict[str, list[str]]:
    rows = {}
    for number, line in enumerate(MAP.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split("\t")
        assert len(parts) >= 2 and parts[0] and all(p.strip() for p in parts), "line %d is not an id and its entries" % number
        assert parts[0] not in rows, "%s has two rows" % parts[0]
        rows[parts[0]] = [p.strip() for p in parts[1:]]
    return rows


def spec_text() -> str:
    return need(SPEC / "GAME_SPEC.md").read_text(encoding="utf-8")


def section_ids() -> list[str]:
    """The leaf headings of sections 1 to 14: S3, S4.1 .. S4.19, S5.1 .. S5.17, S6, S7, S8.1, S8.2, S9.1, S9.2, S10 .."""
    tops, subs = [], {}
    for line in spec_text().splitlines():
        top = re.match(r"^## (\d+)\. ", line)
        sub = re.match(r"^### (\d+)\.(\d+) ", line)
        if top and int(top.group(1)) <= 14:
            tops.append(int(top.group(1)))
        elif sub and int(sub.group(1)) <= 14:
            subs.setdefault(int(sub.group(1)), []).append(int(sub.group(2)))
    ids = []
    for top in tops:
        ids += ["S%d.%d" % (top, n) for n in subs[top]] if top in subs else ["S%d" % top]
    return ids


def quirk_ids() -> list[str]:
    return ["Q%s" % m.group(1) for line in spec_text().splitlines() if (m := re.match(r"^Q(\d+) ", line))]


def exact_ids() -> list[str]:
    lines = spec_text().splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith("### 17.2 "))
    end = next(i for i, l in enumerate(lines) if l.startswith("### 17.3 "))
    bullets = [l for l in lines[start + 1:end] if l.startswith("- ")]
    return ["X%d" % n for n in range(1, len(bullets) + 1)]


def gap_ids() -> list[str]:
    text = need(SPEC / "GAP_REGISTER.md").read_text(encoding="utf-8")
    block = text.split("<!-- CLOSES-BEGIN -->")[1].split("<!-- CLOSES-END -->")[0]
    line = next(l for l in block.splitlines() if l.startswith("- S8.1:"))
    return re.findall(r"G-[A-Z]\d+", line)


def observed_ids() -> list[str]:
    ids = []
    for path in sorted(need(GAME_ROOT / "observations").glob("listening_round_*_answers.txt")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip() and not line.startswith("#"):
                ids.append("OBS-" + line.split("|")[0].strip()[:-4])
    return ids


def extra_ids() -> list[str]:
    text = need(SPEC / "NFL_EXTRA_FEATURES.md").read_text(encoding="utf-8")
    ids = re.findall(r"^- (C\d+) ", text, re.M) + re.findall(r"^- (N\d\.\d+) ", text, re.M)
    ids += re.findall(r"^- (NX-T\d) ", text, re.M)               # SX.2b: the three parts of the T key (owner rule 0.22)
    ids += re.findall(r"^- (NX-S\d) (?!to )", text, re.M)        # SX.14: the eight parts of the start-up choice and saved games (owner rule 0.23)
    ids += re.findall(r"^- (NX-P\d) ", text, re.M)               # SX.10e: every real NFL play and Madden concept (section 18; no NX-P6)
    ids += re.findall(r"^- (NX-N\d) ", text, re.M)               # SX.11: the real coaches and players, no typing of names (owner rule 0.19; no NX-N8)
    ids += sorted(set(re.findall(r"^- (NX-R7) ", text, re.M)))   # SX.10e: the 2026 rules (D-085); the id is used twice in the file
    #                                                              (section 1's style rule and section 18's 2026 rules): one row covers both
    return ids


def required_ids() -> list[str]:
    return section_ids() + quirk_ids() + exact_ids() + gap_ids() + observed_ids() + extra_ids()


def test_the_spec_parts_have_the_counts_the_map_was_written_for():
    assert len(quirk_ids()) == 62 and quirk_ids()[0] == "Q1" and quirk_ids()[-1] == "Q62"
    assert len(exact_ids()) == 7
    assert len(gap_ids()) == 15
    assert len(observed_ids()) == 26
    assert [i for i in extra_ids() if i.startswith("C")] == ["C%d" % n for n in range(1, 11)]
    assert len([i for i in extra_ids() if re.match(r"N\d\.", i)]) == 47
    assert [i for i in extra_ids() if i.startswith("NX-")] == (["NX-T1", "NX-T2", "NX-T3"] + ["NX-S%d" % n for n in range(1, 9)]
                                                               + ["NX-P%d" % n for n in (1, 2, 3, 4, 5, 7, 8)] + ["NX-N%d" % n for n in range(1, 8)] + ["NX-R7"])
    assert "S5.17" in section_ids() and "S4.19" in section_ids() and "S14" in section_ids() and "S15" not in section_ids()


def test_the_map_covers_every_requirement_and_names_nothing_else():
    required, mapped = required_ids(), set(load_map())
    assert len(required) == len(set(required)), "a requirement id appears twice in the spec files"
    assert sorted(set(required) - mapped) == [], "requirements without a row"
    assert sorted(mapped - set(required)) == [], "rows for requirements that the spec does not have"


def test_every_entry_matches_a_test_function_and_no_row_is_empty():
    tests, bad = function_names(), []
    for id_, entries in load_map().items():
        real = [e for e in entries if not e.startswith("NA:")]
        assert real or len(entries) == 1, id_
        for entry in real:
            stem, _, pattern = entry.partition("::")
            if stem not in tests or not pattern:
                bad.append((id_, entry, "no such test file or no pattern"))
            elif not any(re.search(pattern, name) for name in tests[stem]):
                bad.append((id_, entry, "no test function matches"))
    assert bad == []


def test_a_not_applicable_row_has_one_entry_with_a_reason():
    for id_, entries in load_map().items():
        if any(e.startswith("NA:") for e in entries):
            assert len(entries) == 1 and len(entries[0]) > 40, id_
    na = [i for i, e in load_map().items() if e[0].startswith("NA:")]
    assert sorted(na) == ["Q16", "Q30", "Q40", "S1", "S14", "S2"]


def test_the_quirk_classes_of_17_5_and_the_quirk_rows_are_the_same_set():
    """X7 (the quirks kept in 17.5) names this file: the quirk classes of 17.5 and the map's Q rows are the same set."""
    text = spec_text()
    classes = re.search(r"<!-- QUIRKS-BEGIN -->(.*)<!-- QUIRKS-END -->", text, re.S).group(1)
    in_classes = set()
    for line in classes.splitlines():
        if line.startswith("- "):
            in_classes |= {"Q%s" % n for n in re.findall(r"\bQ(\d+)\b", line)}
    assert in_classes == set(quirk_ids())
    assert set(quirk_ids()) <= set(load_map())
