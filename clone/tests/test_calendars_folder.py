"""The calendars folder of the repository, where the maintainer publishes each year's NFL schedule for the game's download (nfl4 only; D-128). This is
inspired by Jim Kitchen.

Every schedule_<year>.txt there must pass the very parser the game uses for a downloaded file, and the 2026 file must be the one the game ships.
"""
import hashlib
import os
import re

from nfl4.extras.franchise import fixtures

FOLDER = os.path.join(os.path.dirname(__file__), "..", "..", "calendars")


def files():
    return sorted(name for name in os.listdir(FOLDER) if re.fullmatch(r"schedule_\d{4}\.txt", name))


def test_every_published_calendar_is_whole():
    assert files(), "the calendars folder has the 2026 file at least"
    for name in files():
        with open(os.path.join(FOLDER, name), encoding="utf-8-sig") as handle:
            calendar = fixtures.parse(handle.read())
        assert calendar.length == fixtures.WEEKS, name


def test_the_published_2026_calendar_is_the_shipped_one():
    def digest(path):
        with open(path, "rb") as handle:
            return hashlib.sha256(handle.read()).hexdigest()
    assert digest(os.path.join(FOLDER, "schedule_2026.txt")) == digest(fixtures.shipped_path(2026))


def test_the_folder_says_how_a_new_season_is_published():
    with open(os.path.join(FOLDER, "README.md"), encoding="utf-8") as handle:
        text = handle.read()
    assert "get the latest calendar" in text and "schedule_<year>.txt" in text
