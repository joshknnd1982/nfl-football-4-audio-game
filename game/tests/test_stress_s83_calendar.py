"""The real calendar under stress (S8.3 round 2; nfl4 only, rule 0.13; SZ.8's schedule_2026.txt, D-121, D-122). This is inspired by Jim Kitchen.

The Franchise plays `assets/data/schedule_2026.txt`. Here that file is damaged in every way of playbook 7.10 (the byte damages, deleted, a folder in its
place, held open, read-only) and in the ways a hand-edited calendar goes wrong (a team that does not exist, a week 19, 17 weeks, a team twice in a
week, a game twice, another encoding, a byte order mark, Unix line ends). The loader never raises; a calendar that is not whole is not used; the
Franchise then plays the original's 16 weeks, says ONE short notice (NXF-46) and writes why in the log (rule 0.15); a franchise that loses or gets the
file between two seasons goes on, and its league file stays whole.
"""
import logging
import os
import shutil

import pytest
import filedamage
from frrig import COACH_AND_TEAM, WANT_FRANCHISE, enter_until, franchise_rig, run_until, spoken

from nfl4.extras import nx_texts as X
from nfl4.extras.franchise import fixtures
from nfl4.extras.franchise.league import LeagueRecord

SHIPPED = fixtures.shipped_path(2026)


@pytest.fixture
def calendar_file(tmp_path, monkeypatch):
    """A copy of the shipped calendar that the program reads in its place (every year's file is looked for in the same folder)."""
    folder = tmp_path / "assets"
    folder.mkdir()
    path = folder / "schedule_2026.txt"
    shutil.copyfile(SHIPPED, path)
    monkeypatch.setattr(fixtures, "shipped_path", lambda year: str(folder / (fixtures.FILE_NAME % year)))
    fixtures._cache.clear()
    yield path
    fixtures._cache.clear()


def edit_text(path, change):
    text = path.read_text(encoding="utf-8")
    new = change(text)
    assert new != text, "the damage changed nothing"
    path.write_text(new, encoding="utf-8", newline="")


def wrong_team(text):
    return text.replace("= T08 T28", "= T33 T28", 1)


def wrong_week(text):
    return text.replace("W18G16 =", "W19G16 =", 1)


def seventeen_weeks(text):
    return "\n".join(line for line in text.splitlines() if not line.startswith("W18")) + "\n"


def team_twice_in_a_week(text):
    lines = text.splitlines()
    first = next(i for i, line in enumerate(lines) if line.startswith("W01G01 ="))
    second = next(i for i, line in enumerate(lines) if line.startswith("W01G02 ="))
    lines[second] = "W01G02 = " + lines[first].split("= ", 1)[1]
    return "\n".join(lines) + "\n"


def game_twice(text):
    line = next(line for line in text.splitlines() if line.startswith("W03G01 ="))
    return text + line + "\n"


CONTENT_DAMAGES = {"wrong_team": wrong_team, "wrong_week": wrong_week, "seventeen_weeks": seventeen_weeks,
                   "team_twice_in_a_week": team_twice_in_a_week, "game_twice": game_twice}
# damages after which the calendar is still whole and must still be played
HARMLESS = {"huge", "read_only", "bom", "unix_line_ends"}


def damage(path, kind):
    """Damage the calendar; a context manager for the damages that last while the program runs, else None."""
    if kind in filedamage.BYTE_DAMAGES:
        filedamage.apply(kind, path)
    elif kind in CONTENT_DAMAGES:
        edit_text(path, CONTENT_DAMAGES[kind])
    elif kind == "deleted":
        path.unlink()
    elif kind == "a_folder_in_its_place":
        path.unlink()
        path.mkdir()
    elif kind == "read_only":
        return filedamage.read_only(path)
    elif kind == "held_open":
        return filedamage.holding(path)
    elif kind == "latin1":
        text = path.read_text(encoding="utf-8").replace("season 2026", "saison été 2026", 1)
        path.write_bytes(text.encode("cp1252"))
    elif kind == "bom":
        path.write_bytes(b"\xef\xbb\xbf" + path.read_bytes())
    elif kind == "unix_line_ends":
        path.write_bytes(path.read_bytes().replace(b"\r\n", b"\n"))
    else:
        raise ValueError(kind)
    return None


KINDS = list(filedamage.BYTE_DAMAGES) + list(CONTENT_DAMAGES) + ["deleted", "a_folder_in_its_place", "read_only", "held_open", "latin1", "bom",
                                                                  "unix_line_ends"]


@pytest.mark.parametrize("kind", KINDS)
def test_a_damaged_calendar_never_raises_and_is_used_only_when_whole(calendar_file, kind, caplog):
    context = damage(calendar_file, kind)
    with caplog.at_level(logging.WARNING, logger="nfl4.extras"):
        if context is None:
            seasons = [fixtures.for_season(s) for s in (1, 2, 5)]
        else:
            with context:
                seasons = [fixtures.for_season(s) for s in (1, 2, 5)]
    if kind in HARMLESS:
        assert all(c is not None and c.length == 18 for c in seasons), kind
        return
    if kind == "newer_format" or kind == "another_list_header" and seasons[0] is not None:
        pass                                                                    # header words a calendar does not depend on: whole or not, never a raise
    for calendar in seasons:
        if calendar is not None:
            fixtures.check(calendar)                                            # a calendar that is used is whole
    if kind not in ("newer_format", "another_list_header"):
        assert seasons == [None, None, None], kind
        if kind != "deleted":                                                   # a file that is not there is not an error (an older install)
            assert any("cannot be used" in r.getMessage() for r in caplog.records), kind


def test_the_shipped_calendar_is_whole_and_read_the_same_with_unix_line_ends_and_a_byte_order_mark(calendar_file):
    whole = fixtures.load_file(SHIPPED)
    for kind in ("unix_line_ends", "bom"):
        damage(calendar_file, kind)
        fixtures._cache.clear()
        assert fixtures.for_season(1).weeks == whole.weeks, kind


# ----- the Franchise with a calendar that cannot be used -----

def events(monkeypatch):
    """The debug log's events while the test runs (the log itself is not started in the tests)."""
    from nfl4.data import debuglog
    seen, real = [], debuglog.event
    monkeypatch.setattr(debuglog, "event", lambda area, name, *args, **fields: (seen.append((name, fields)), real(area, name, *args, **fields))[1])
    return seen


def run_franchise(tmp_path, until):
    rig = franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM, real_calendar=True, scores=lambda r: (28, 10), policy=enter_until(lambda: until(rig)))
    return run_until(rig)


@pytest.mark.parametrize("kind", ["deleted", "cut_in_half", "wrong_team", "binary_zeros"])
def test_a_franchise_with_a_calendar_that_cannot_be_used_plays_16_weeks_and_says_one_notice(tmp_path, calendar_file, kind, monkeypatch):
    damage(calendar_file, kind)
    seen = events(monkeypatch)
    rig = run_franchise(tmp_path, lambda r: r.game.season.gtp == 3)
    league = rig.fstore.league
    assert league.calendar is None and league.regular_weeks == 16 and rig.game.season.calendar is None
    text = spoken(rig)
    assert text.count(X.text("NXF-46")) == 1                                    # said once, at the week line, never again
    assert [f for name, f in seen if name == "calendar_missing"] == [{"season": 1, "year": 2026, "path": fixtures.shipped_path(2026)}]   # rule 0.15
    LeagueRecord.from_json(league.to_json())


def test_a_franchise_that_loses_the_calendar_between_two_seasons_plays_16_weeks_and_its_file_stays_whole(tmp_path, calendar_file):
    def until(rig):
        league = rig.fstore.league
        if league is not None and league.season == 1 and rig.game.season.gtp >= 20 and calendar_file.exists():
            calendar_file.unlink()                                              # gone in the play-offs of season 1
            fixtures._cache.clear()
        return league is not None and league.season == 2 and rig.game.season.gtp == 3

    rig = run_franchise(tmp_path, until)
    league = rig.fstore.league
    assert league.season == 2 and league.calendar is None and league.regular_weeks == 16
    assert len(league.history) == 1 and league.history[-1]["champion"] == league.team             # season 1 was the 18-week calendar's, kept
    again = LeagueRecord.from_json(league.to_json())
    assert again.regular_weeks == 16 and again.season == 2
    assert spoken(rig).count(X.text("NXF-46")) == 1


def test_a_franchise_that_gets_the_calendar_back_for_its_next_season_plays_18_weeks(tmp_path, calendar_file):
    kept = calendar_file.read_bytes()
    calendar_file.unlink()

    def until(rig):
        league = rig.fstore.league
        if league is not None and league.season == 1 and rig.game.season.gtp >= 18 and not calendar_file.exists():
            calendar_file.write_bytes(kept)
            fixtures._cache.clear()
        return league is not None and league.season == 2 and rig.game.season.gtp == 2

    rig = run_franchise(tmp_path, until)
    league = rig.fstore.league
    assert league.season == 2 and league.calendar is not None and league.regular_weeks == 18
    assert "season 2027" in rig.game.season.calendar.label
    LeagueRecord.from_json(league.to_json())
