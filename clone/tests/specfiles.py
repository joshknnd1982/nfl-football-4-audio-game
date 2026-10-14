"""Reads of the frozen spec files the logic tests compare against. This is inspired by Jim Kitchen.

The spec folder is part of the repository (game root: spec\\). A test that needs one of its files is skipped when the folder
is not there (a copy of clone\\ alone); the lifted code of the original is not in the repository (work\\lift is kept out),
so the few checks that read it skip as well.
"""
import re
from pathlib import Path

import pytest

GAME_ROOT = Path(__file__).resolve().parents[2]
SPEC = GAME_ROOT / "spec"
LIFT = GAME_ROOT / "work" / "lift"


def need(path: Path) -> Path:
    if not path.exists():
        pytest.skip("%s is not in this copy of the project" % path)
    return path


def strings_table() -> list[dict]:
    """spec\\strings_all.tsv: id, class, text of every string of the original's exe (GAME_SPEC 9, STRINGS.md)."""
    rows = []
    text = need(SPEC / "strings_all.tsv").read_text(encoding="utf-8")
    for line in text.split("\n")[1:]:
        parts = line.rstrip("\r").split("\t")
        if len(parts) >= 7:
            rows.append({"id": parts[0], "class": parts[1], "procedures": parts[5], "text": "\t".join(parts[6:])})
    return rows


def original_strings() -> set[str]:
    return {row["text"] for row in strings_table()}


def strings_of_class(name: str) -> list[str]:
    return [row["text"] for row in strings_table() if row["class"] == name]


def surnames_table() -> list[str]:
    """spec\\SURNAMES.tsv: the surname column in index order."""
    rows = need(SPEC / "SURNAMES.tsv").read_text(encoding="utf-8").split("\n")
    names = []
    for number, line in enumerate((r for r in rows[1:] if r.strip()), start=1):
        parts = line.rstrip("\r").split("\t")
        assert int(parts[0]) == number
        names.append(parts[1])
    return names


def spec_team_lists() -> list[tuple[str, list[str]]]:
    """GAME_SPEC 11, first bullet: '32 teams ...: AFC North Bengals, Browns, Ravens, Steelers; AFC East Bills, ...'."""
    text = need(SPEC / "GAME_SPEC.md").read_text(encoding="utf-8")
    line = next(l for l in text.split("\n") if l.startswith("- 32 teams (nicknames only"))
    body = line.split("):", 1)[1].split(". Spellings", 1)[0]
    result = []
    for part in body.split(";"):
        match = re.match(r"\s*([AN]FC (?:North|East|West|South))\s+(.*)$", part)
        assert match, part
        result.append((match.group(1), [name.strip() for name in match.group(2).split(",")]))
    return result
