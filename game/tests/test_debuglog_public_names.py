"""Rule 0.15 (2026-10-26): the owner's problem report about the Giants' starting quarterback said only "<typed>", because the debug log hid every
quarterback name, the real ones the game offered too. The real rosters' and coaches' names are public facts: the log names them; a name the player
types that is no real man's stays hidden. This is inspired by Jim Kitchen.
"""
import pytest

from nfl4.data import debuglog
from nfl4.extras import real_names as R


@pytest.fixture(autouse=True)
def clean():
    typed, public, sources = list(debuglog._typed), set(debuglog._public), list(debuglog._public_sources)
    del debuglog._typed[:]
    debuglog._public.clear()
    del debuglog._public_sources[:]
    R.reset_defaults_cache()
    yield
    debuglog._typed[:] = typed
    debuglog._public.clear()
    debuglog._public.update(public)
    debuglog._public_sources[:] = sources
    R.reset_defaults_cache()


def test_building_the_names_does_not_list_them_until_a_typed_name_is_checked():
    R.defaults()
    assert debuglog._public_sources and not debuglog._public            # registered, not yet listed (a list costs about 50 ms)
    debuglog.add_typed("Zorbo Quimby")
    assert not debuglog._public_sources and "jameis winston" in debuglog._public


def test_a_real_quarterback_and_coach_stay_in_the_log_and_a_made_up_name_is_hidden():
    real = R.defaults()
    assert "jameis winston" in real.public_names() and "john harbaugh" in real.public_names()
    debuglog.add_typed("Jameis Winston", "John Harbaugh", "Zorbo Quimby")
    line = debuglog.redact("quarterbacks own='Jameis Winston' opponent='Zorbo Quimby' coach John Harbaugh")
    assert "Jameis Winston" in line and "John Harbaugh" in line and "Zorbo Quimby" not in line and "<typed>" in line


def test_a_name_hidden_before_the_rosters_were_read_is_shown_once_they_are():
    debuglog.add_typed("J.J. McCarthy")
    assert "<typed>" in debuglog.redact("is J.J. McCarthy")
    R.defaults()
    assert debuglog.redact("is J.J. McCarthy") == "is J.J. McCarthy"


def test_the_spoken_form_of_a_real_name_is_public_too():
    real = R.defaults()
    assert "michael penix junior" in real.public_names()          # rosters.txt writes "Michael Penix Jr."
    debuglog.add_typed("Michael Penix Junior")
    assert "Michael Penix Junior" in debuglog.redact("the quarterback Michael Penix Junior")
