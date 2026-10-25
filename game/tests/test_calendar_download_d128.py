"""F9, Franchise, get the latest calendar (nfl4 only, rule 0.13; D-128). This is inspired by Jim Kitchen.

Only when the player chooses it, the game asks its own GitHub repository (the folder `calendars`) for the newest schedule_<year>.txt after the newest it
has, checks it with the parser of the shipped file, saves it whole in the player's customize folder and says in one sentence what it got or why not. A
franchise plays a year's own file in that year's season, and a later season relabels the newest earlier calendar. The network is faked here; the real
WinHTTP fetch is checked by tests/test_web_fetch.py when the internet can be reached.
"""
import os
import threading

import pytest

from nfl4.data import web
from nfl4.extras import nx_texts as X
from nfl4.extras.franchise import calendar_flow as CF
from nfl4.extras.franchise import fixtures


@pytest.fixture
def folder(tmp_path, monkeypatch):
    target = tmp_path / "customize"
    monkeypatch.setattr(fixtures, "player_folder", lambda: str(target))
    fixtures._cache.clear()
    return target


def shipped_text() -> str:
    with open(fixtures.shipped_path(2026), encoding="utf-8") as handle:
        return handle.read()


def calendar_of(year: int) -> bytes:
    """A whole calendar for `year`: the 2026 games (a valid calendar) under another VERSION line."""
    lines = [("VERSION = season %d, published for the test" % year) if line.startswith("VERSION") else line for line in shipped_text().splitlines()]
    return ("\n".join(lines) + "\n").encode("utf-8")


class Net:
    """A fake fetch: a dict of year -> body (missing: 404), or an exception to raise."""

    def __init__(self, files=None, error=None):
        self.files, self.error, self.asked = files or {}, error, []

    def __call__(self, url):
        self.asked.append(url)
        if self.error is not None:
            raise self.error
        year = int(url.rsplit("_", 1)[1].split(".")[0])
        if year in self.files:
            return 200, self.files[year]
        return 404, b"404: Not Found"


def test_the_address_is_the_games_own_repository():
    assert CF.url_of(2027) == "https://raw.githubusercontent.com/joshknnd1982/nfl-football-4-audio-game/master/calendars/schedule_2027.txt"


def test_a_newer_calendar_is_checked_saved_whole_and_used_for_its_season(folder):
    net = Net({2027: calendar_of(2027)})
    result, year, path = CF.get_latest(net, today=2026)
    assert (result, year) == (CF.OK, 2027) and os.path.isfile(path) and os.path.dirname(path) == str(folder)
    assert net.asked[0].endswith("schedule_2027.txt")
    assert fixtures.local_years() == [2026, 2027]
    second = fixtures.for_season(2)                                             # 2027: the downloaded file itself, not the relabeled 2026
    assert "published for the test" in second.label
    third = fixtures.for_season(3)                                              # 2028: the newest earlier calendar, 2027, relabeled by one year
    assert "the 2027 calendar" in third.label


def test_nothing_newer_says_which_year_is_the_newest_and_saves_nothing(folder):
    net = Net()
    result, year, _ = CF.get_latest(net, today=2026)
    assert (result, year) == (CF.NOTHING_NEWER, 2026) and not folder.exists()
    assert CF.sentence(result, year) == X.text("NXF-51", year=2026)


def test_the_years_tried_run_from_next_year_down_to_the_newest_the_game_has(folder):
    net = Net()
    CF.get_latest(net, today=2029)
    assert [url.rsplit("_", 1)[1] for url in net.asked] == ["2030.txt", "2029.txt", "2028.txt", "2027.txt"]


def test_no_connection_or_no_answer_says_so_and_saves_nothing(folder):
    for kind in ("offline", "timeout"):
        result, _, _ = CF.get_latest(Net(error=web.WebError(kind, "test")), today=2026)
        assert result == CF.OFFLINE and not folder.exists()
    assert CF.sentence(CF.OFFLINE, 2027) == X.text("NXF-52")


def test_a_file_that_is_not_a_whole_calendar_is_not_saved(folder):
    broken = calendar_of(2027).replace(b"W18G01", b"W18G99")
    result, year, _ = CF.get_latest(Net({2027: broken}), today=2026)
    assert (result, year) == (CF.BAD_FILE, 2027) and not folder.exists()
    result, _, _ = CF.get_latest(Net({2027: b"\xff\xfe junk"}), today=2026)
    assert result == CF.BAD_FILE


def test_a_folder_that_cannot_be_written_says_so(folder, monkeypatch):
    monkeypatch.setattr(CF, "write_text_atomic", lambda path, text: False)
    result, _, _ = CF.get_latest(Net({2027: calendar_of(2027)}), today=2026)
    assert result == CF.NOT_SAVED and CF.sentence(result, 2027) == X.text("NXF-55")


def test_a_saved_file_with_windows_line_ends_reads_back(folder):
    CF.get_latest(Net({2027: calendar_of(2027).replace(b"\n", b"\r\n")}), today=2026)
    with open(fixtures.player_path(2027), "rb") as handle:
        assert b"\r\r\n" not in handle.read()
    assert fixtures.for_season(2) is not None


def test_the_sentence_names_the_season_a_franchise_plays_it_in():
    class League:
        season = 1
    assert CF.sentence(CF.OK, 2027, League()) == X.text("NXF-50", year=2027)        # the coming season of a franchise in 2026
    assert CF.sentence(CF.OK, 2026, League()) == X.text("NXF-56", year=2026)        # the season in progress keeps its calendar
    assert CF.sentence(CF.OK, 2027) == X.text("NXF-56", year=2027)                  # no franchise


# ----- the menu item: speech, the wait and Escape -----

class Speech:
    def __init__(self):
        self.said = []

    def stop(self):
        pass

    def say_async(self, text):
        self.said.append(text)


class Keys:
    def __init__(self, escape_after=None):
        self.escape_after, self.calls = escape_after, 0

    def key_waiting(self):
        self.calls += 1
        return self.escape_after is not None and self.calls >= self.escape_after

    def read_key(self):
        return 27


def test_the_item_says_it_is_asking_and_then_the_result(folder):
    speech = Speech()
    text = CF.run(None, speech, Keys(), None, fetch=Net({2027: calendar_of(2027)}), today=2026)
    assert speech.said == [X.text("NXF-49")] and text == X.text("NXF-56", year=2027)


def test_escape_stops_the_wait_at_once(folder):
    gate = threading.Event()

    def slow(url):
        gate.wait(5)
        return 404, b""
    speech = Speech()
    text = CF.run(None, speech, Keys(escape_after=2), None, fetch=slow, today=2026)
    gate.set()
    assert text == X.text("NXF-54")


def test_the_game_never_asks_the_network_by_itself(tmp_path, monkeypatch):
    """Starting a franchise and playing its first week never calls the network (only the menu item does)."""
    from frrig import COACH_AND_TEAM, WANT_FRANCHISE, enter_until, franchise_rig, run_until
    calls = []
    monkeypatch.setattr(web, "fetch", lambda *a, **k: calls.append(a) or (404, b""))
    rig = franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM, real_calendar=True, policy=enter_until(lambda: rig.game.season.gtp == 3))
    run_until(rig)
    assert calls == []
