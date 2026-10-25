"""The WinHTTP fetch of data/web.py (nfl4: D-128). This is inspired by Jim Kitchen.

These tests reach the real internet: the game's own public README on GitHub. Without a connection they are skipped (the fake network of
test_calendar_download_d128.py tests everything the game does with an answer). A wrong address is an error with a kind, never a crash.
"""
import pytest

from nfl4.data import web

README = "https://raw.githubusercontent.com/joshknnd1982/nfl-football-4-audio-game/master/README.md"


def reachable() -> bool:
    try:
        status, _ = web.fetch(README, timeout=10)
        return status == 200
    except web.WebError:
        return False


def test_only_an_https_address_is_fetched():
    with pytest.raises(web.WebError) as found:
        web.fetch("http://example.com/x")
    assert found.value.kind == "failed"


def test_a_name_that_does_not_exist_is_offline():
    with pytest.raises(web.WebError) as found:
        web.fetch("https://no-such-host.invalid/schedule_2027.txt", timeout=5)
    assert found.value.kind in ("offline", "timeout")


def test_the_games_own_readme_is_fetched_and_a_missing_file_is_404():
    if not reachable():
        pytest.skip("GitHub cannot be reached from this computer now")
    status, body = web.fetch(README)
    assert status == 200 and body.startswith(b"# NFL Football 4")
    status, _ = web.fetch(README.replace("README.md", "no-such-file-d128.txt"))
    assert status == 404


def test_a_body_larger_than_allowed_is_refused():
    if not reachable():
        pytest.skip("GitHub cannot be reached from this computer now")
    with pytest.raises(web.WebError) as found:
        web.fetch(README, max_bytes=100)
    assert found.value.kind == "too_large"
