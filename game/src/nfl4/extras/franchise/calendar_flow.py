"""F9, Franchise, get the latest N. F. L. calendar (nfl4 only, rule 0.13; D-128, the owner: "you must add a script or module to the game that lets the
game go get the latest calendar when the user chooses to do so from a game menu"). This is inspired by Jim Kitchen.

Only when the player chooses the item, never at start-up and never by itself, the game asks the game's own GitHub repository for the newest
`schedule_<year>.txt` the maintainer has published (the folder `calendars` of the repository; he adds each year's file when the NFL releases its
schedule, in the spring). It tries the years from next year down to the newest one the game already has, and takes the first that is there:

* nothing newer than the game's own calendars: one sentence says so, and which year the newest is;
* a newer one: it is checked with the very parser of the shipped file (`fixtures.parse`: 18 weeks, 17 games and one bye for every team, the division
  games), written whole to the player's customize folder (`fixtures.player_path`), and said in one sentence with the season it is for; a franchise
  plays it from the season of that year (the season in progress keeps the calendar it began with);
* no connection, no answer in time, a file that is not a whole calendar, a folder that cannot be written: one sentence each, and nothing is saved.

The request runs on a thread of its own, so Escape stops the wait at once (nothing is saved then). Every step is logged (rule 0.15). The network is
data/web.py (WinHTTP: the build has no Python ssl).
"""
from __future__ import annotations

import logging
import threading
import time

from ...data import debuglog
from ...data.healing import write_text_atomic
from ...game.keys import KEY_ESCAPE
from .. import nx_texts as X
from . import fixtures

log = logging.getLogger("nfl4.extras")

REPOSITORY_RAW = "https://raw.githubusercontent.com/joshknnd1982/nfl-football-4-audio-game/master/calendars/"
TIMEOUT = 15.0                     # seconds for each request
MAX_BYTES = 200_000                # a calendar is about 9 kB
YEARS_AHEAD = 1                    # the newest year asked for: next year (the NFL releases a schedule some months before its season)

OK, NOTHING_NEWER, OFFLINE, BAD_FILE, NOT_SAVED, STOPPED = "saved", "nothing_newer", "offline", "bad_file", "not_saved", "stopped"


def url_of(year: int) -> str:
    return REPOSITORY_RAW + fixtures.FILE_NAME % year


def this_year() -> int:
    return time.localtime().tm_year


def look_for_latest(fetch, newest_local: int, today: int) -> tuple:
    """The newest published calendar after `newest_local`: (OK, year, text), (NOTHING_NEWER, newest_local, ""), (OFFLINE, 0, detail) or (BAD_FILE, year,
    reason). `fetch(url)` is data.web.fetch (a test hands in its own)."""
    from ...data.web import WebError
    for year in range(max(today + YEARS_AHEAD, newest_local), newest_local, -1):
        url = url_of(year)
        try:
            status, body = fetch(url)
        except WebError as exc:
            debuglog.event("calendar", "fetch_failed", year=year, kind=exc.kind, detail=exc.detail)
            return (OFFLINE if exc.kind in ("offline", "timeout") else BAD_FILE), year, exc.detail
        debuglog.event("calendar", "fetched", year=year, status=status, size=len(body))
        if status == 404:
            continue
        if status != 200:
            return OFFLINE, year, "HTTP %d" % status
        try:
            text = body.decode("utf-8-sig")
            fixtures.parse(text)
        except (UnicodeDecodeError, ValueError) as exc:
            return BAD_FILE, year, str(exc)
        return OK, year, text
    return NOTHING_NEWER, newest_local, ""


def get_latest(fetch=None, today: int | None = None, cancelled=lambda: False) -> tuple:
    """The whole job without speech: (result, year, detail). Saves the file only when it is whole and the wait was not stopped."""
    if fetch is None:
        from ...data.web import fetch as web_fetch

        def fetch(url):
            return web_fetch(url, timeout=TIMEOUT, max_bytes=MAX_BYTES)
    years = fixtures.local_years()
    newest = years[-1] if years else fixtures.FIRST_YEAR - 1
    result, year, detail = look_for_latest(fetch, newest, this_year() if today is None else today)
    if result != OK:
        return result, year, detail
    if cancelled():
        return STOPPED, year, ""
    path = fixtures.player_path(year)
    if not write_text_atomic(path, detail.replace("\r\n", "\n")):          # written whole or not at all (its own log line says why)
        return NOT_SAVED, year, path
    return OK, year, path


def sentence(result: str, year: int, league=None) -> str:
    if result == OK:
        if league is not None and year >= fixtures.year_of(league.season + 1):
            return X.text("NXF-50", year=year)
        return X.text("NXF-56", year=year)
    return X.text({NOTHING_NEWER: "NXF-51", OFFLINE: "NXF-52", BAD_FILE: "NXF-53", NOT_SAVED: "NXF-55", STOPPED: "NXF-54"}[result],
                  year=year)


def run(g, speech, keys, store, fetch=None, today: int | None = None) -> str:
    """F9's item: says that it is asking, waits for the answer on a thread (Escape stops the wait), and returns the sentence of the result."""
    speech.stop()
    speech.say_async(X.text("NXF-49"))
    debuglog.event("calendar", "asked", newest_local=(fixtures.local_years() or [0])[-1])
    stop = threading.Event()
    box: dict = {}

    def work():
        try:
            box["result"] = get_latest(fetch, today, cancelled=stop.is_set)
        except Exception as exc:                                     # never a reason to stop the game
            log.exception("getting the latest calendar failed")
            box["result"] = (OFFLINE, 0, str(exc))
    worker = threading.Thread(target=work, name="nfl4-calendar", daemon=True)
    worker.start()
    while worker.is_alive():
        if keys.key_waiting() and keys.read_key() == KEY_ESCAPE:
            stop.set()
            debuglog.event("calendar", "stopped")
            return X.text("NXF-54")
        worker.join(0.05)
        debuglog.beat()
    result, year, detail = box.get("result", (OFFLINE, 0, "no answer"))
    if stop.is_set() and result == OK:
        result = STOPPED
    debuglog.event("calendar", "result", result=result, year=year, detail=str(detail)[:200])
    league = store.league if store is not None else None
    return sentence(result, year, league)
