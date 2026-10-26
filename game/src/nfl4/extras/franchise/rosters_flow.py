"""F9, Customize (and F9, Franchise), get the latest rosters; the offer of newer rosters to a franchise; the conversion's sentence (nfl4 only, rule 0.13;
CLAUDE.md 0.32, NX-L9; NFL_FRANCHISE_DESIGN 21.6 (6), 21.10, 21.11; D-154, D-156; SR.6). This is inspired by Jim Kitchen.

THE DOWNLOAD (`run`): only when the player chooses the item, never by itself and never in a game. The game asks its own GitHub repository (the folder
`rosters`, the calendars' route of D-141 and data/web.py's WinHTTP fetch) for the maintainer's checked `rosters.txt` and `free_agents.txt`, reads the
VERSION line ("as of <date>") and compares it with the player's own file (the customize folder's copy, else the shipped one):

* not there (404: the repository has no `rosters` folder until the owner publishes one, a public action) or not newer: "You already have the newest
  rosters, from <date>." and nothing changes;
* newer: rosters.txt is checked by roster_file.parse and roster_file.check, the very checks of the maintainer's script (D-155: one failure refuses the
  file), and by the list loader's header; free_agents.txt (when it is there and newer) by the loader's own rules (every line must be read). A player's
  own edited rosters.txt (neither the shipped text, an older shipped copy, nor a file this item wrote) is replaced only after one question, "no" first.
  The player's files are kept as rosters.txt.before-<date> and free_agents.txt.before-<date> (the new file's date; a name already there gets -2, -3...),
  the new ones are written whole (data/healing.write_text_atomic) and the customization is read again at once, so the next quick game, season or new
  franchise plays them. "You now have the rosters of <date>.";
* no connection, a server error, a file that fails a check, a folder that cannot be written: "The rosters could not be downloaded: <reason>. Your
  rosters stay as they were." Nothing is written then.

The request runs on a thread of its own (calendar_flow's way), so Escape stops the wait at once and nothing is saved. Every step is logged (rule 0.15):
`rosters_download` with the result, the version and the size.

THE OFFER (`offer`, `at_opening`): a franchise keeps its league; when a league made from older rosters is opened (or the item above is used while it is in
use) the player is asked once, "No, keep my league as it is" first, whether the other 31 teams come up to the newer file (roster_update.py). Never in a
game, the draft or the cut: then it waits for the next opening. Before the change league.sav is kept as league.sav.before-rosters-<date>.

THE CONVERSION'S SENTENCE (`at_opening`): a league of format 17 or older converted when the store opened it (store._convert, real_roster.convert) is told
once what was done, where the player first opens the franchise.
"""
from __future__ import annotations

import hashlib
import logging
import os
import threading
import time
from dataclasses import dataclass

from ...data import customlists as cl
from ...data import debuglog
from ...data.healing import read_player_text, save_backup_copy, write_text_atomic
from ...game.keys import KEY_ESCAPE
from .. import nx_texts as X
from .. import roster_file as RF
from . import calendar_flow
from . import data as D
from . import roster_update as RU

log = logging.getLogger("nfl4.extras")

REPOSITORY_RAW = calendar_flow.REPOSITORY_RAW.rsplit("calendars/", 1)[0] + "rosters/"
ROSTERS_FILE, FREE_AGENTS_FILE = "rosters.txt", "free_agents.txt"
DOWNLOADED_MARK = "rosters.txt.downloaded"      # the SHA-256 of each rosters.txt this item wrote: such a file is the game's, not the player's own
TIMEOUT = 15.0                                  # seconds for each request
MAX_BYTES = 2_000_000                           # rosters.txt is about 80 kB
LEAGUE_BACKUP = ".before-rosters-"              # league.sav.before-rosters-<date> (the store's backup pattern, design 21.10 (4))

OK, NOTHING_NEWER, OFFLINE, SERVER, BAD_FILE, NOT_SAVED, STOPPED, KEPT_OWN = (
    "saved", "nothing_newer", "offline", "server", "bad_file", "not_saved", "stopped", "kept_own")


@dataclass
class Download:
    result: str
    version: str = ""           # the VERSION of the file offered (newer), or the player's own (nothing newer)
    detail: str = ""            # the reason of a failure, for the sentence and the log
    rosters: str = ""           # the checked text of rosters.txt (LF line ends)
    free: str = ""              # the checked text of free_agents.txt, "" when it is not newer or not there


def url_of(name: str) -> str:
    return REPOSITORY_RAW + name


def folder_of(g) -> str:
    custom = getattr(g, "customization", None)
    if custom is not None:
        return custom.folder
    from ...data import paths
    return paths.customize_dir()


# ----- the versions and the player's own files -----

def text_version(text: str) -> str:
    """The value of the file's VERSION line ("" when it has none)."""
    for line in text.splitlines():
        ident, sep, value = line.strip().partition("=")
        if sep and ident.strip().upper() == "VERSION":
            return value.strip()
    return ""


def _shipped(name: str) -> str:
    from .. import real_names
    kind = real_names.ROSTERS if name == ROSTERS_FILE else real_names.FREE_AGENTS
    try:
        return real_names.shipped_text(kind)
    except Exception:
        log.exception("the shipped %s could not be read", name)
        return ""


def _player_text(folder: str, name: str) -> str | None:
    """The player's copy (LF line ends), or None when there is none or it cannot be read (the list loader heals a damaged one)."""
    path = os.path.join(folder, name)
    if not os.path.isfile(path):
        return None
    try:
        return read_player_text(path).replace("\r\n", "\n")
    except (OSError, ValueError, UnicodeError):
        return None


def local_version(folder: str, name: str) -> str:
    text = _player_text(folder, name)
    return text_version(text if text is not None else _shipped(name))


def _digest(text: str) -> str:
    return hashlib.sha256(text.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def _downloaded(folder: str) -> set:
    text = _player_text(folder, DOWNLOADED_MARK) or ""
    return {line.strip() for line in text.splitlines() if len(line.strip()) == 64}


def own_rosters(folder: str) -> bool:
    """The player's rosters.txt has his own lines: not the shipped text, not an older shipped copy (customize.OLD_SHIPPED_ROSTERS), not a file this item
    wrote. Such a file is replaced only after a question (design 21.10)."""
    text = _player_text(folder, ROSTERS_FILE)
    if text is None:
        return False
    from ...data import customize
    digest = _digest(text)
    return not (digest in customize.OLD_SHIPPED_ROSTERS or text == _shipped(ROSTERS_FILE) or digest in _downloaded(folder))


# ----- the checks of a downloaded file -----

def rosters_problem(text: str) -> str | None:
    """None when the text is a whole rosters.txt of layout 2 the game can use, else the first reason (the maintainer's checks, D-155)."""
    from .. import real_names
    try:
        cl.parse_list(text, real_names.GAME, real_names.ROSTERS)
    except cl.ListFormatError as exc:
        return str(exc)
    version, teams, problems = RF.parse(text)
    if problems:
        return problems[0]
    if not version:
        return "the file has no VERSION line"
    fail, _warn = RF.check(teams)
    return fail[0] if fail else None


def free_agents_problem(text: str) -> str | None:
    """None when every line of free_agents.txt is one the game's loader reads (real_names.build), else the first reason."""
    from .. import real_names
    try:
        parsed = cl.parse_list(text, real_names.GAME, real_names.FREE_AGENTS)
    except cl.ListFormatError as exc:
        return str(exc)
    if parsed.bad_lines:
        return "line %d: %s" % parsed.bad_lines[0]
    problems = {kind: cl.Problems(real_names.FILE_NAMES[kind]) for kind in real_names.FILE_NAMES}
    built = real_names.build([], [], [], None, problems, parsed.entries)
    if problems[real_names.FREE_AGENTS].count:
        return problems[real_names.FREE_AGENTS].messages[0]
    return None if built.free_agents else "the file has no free agents"


# ----- the download (no speech: the thread's work) -----

def _get(fetch, name: str):
    """(status, text or None, failure): the failure is a Download when the request or the text failed."""
    from ...data.web import WebError
    try:
        status, body = fetch(url_of(name))
    except WebError as exc:
        debuglog.event("rosters", "fetch_failed", logging.INFO, file=name, kind=exc.kind, detail=exc.detail)
        return 0, None, Download(OFFLINE if exc.kind in ("offline", "timeout") else SERVER, detail=exc.detail or exc.kind)
    debuglog.event("rosters", "fetched", logging.INFO, file=name, status=status, size=len(body))
    if status == 404:
        return 404, None, None
    if status != 200:
        return status, None, Download(SERVER, detail="HTTP %d" % status)
    try:
        return 200, body.decode("utf-8-sig").replace("\r\n", "\n"), None
    except UnicodeDecodeError:
        return 200, None, Download(BAD_FILE, detail="%s is not a text file" % name)


def download(fetch, folder: str) -> Download:
    """The newest checked rosters (and free agents) newer than the player's, or why not. Writes nothing."""
    local = local_version(folder, ROSTERS_FILE)
    status, text, failed = _get(fetch, ROSTERS_FILE)
    if failed is not None:
        return failed
    if status == 404:                                        # D-141's behaviour until the owner publishes the folder
        return Download(NOTHING_NEWER, local)
    reason = rosters_problem(text)
    if reason:
        return Download(BAD_FILE, detail=reason)
    version = text_version(text)
    if not RU.newer(version, local):
        return Download(NOTHING_NEWER, local)
    status, free, failed = _get(fetch, FREE_AGENTS_FILE)
    if failed is not None:
        return failed
    if free is not None:
        reason = free_agents_problem(free)
        if reason:
            return Download(BAD_FILE, detail="free_agents.txt: " + reason)
        if not RU.newer(text_version(free), local_version(folder, FREE_AGENTS_FILE)):
            free = None                                      # the player's free agents are as new: they stay
    return Download(OK, version, rosters=text, free=free or "")


def _backup_suffix(path: str, suffix: str) -> str:
    """`suffix`, or suffix-2, -3... when a copy of that name is already there (an earlier copy is never written over)."""
    candidate, number = suffix, 2
    while os.path.exists(path + candidate):
        candidate, number = "%s-%d" % (suffix, number), number + 1
    return candidate


def save(folder: str, got: Download) -> tuple:
    """(OK or NOT_SAVED, detail): the player's files kept as <name>.before-<date>, then the new ones written whole. A copy that cannot be made writes
    nothing; a write that fails puts back what was written before it."""
    date = RU.date_of(got.version) or time.strftime("%Y-%m-%d")
    files = [(name, text) for name, text in ((ROSTERS_FILE, got.rosters), (FREE_AGENTS_FILE, got.free)) if text]
    kept: dict = {}
    for name, _text in files:
        path = os.path.join(folder, name)
        if os.path.isfile(path):
            copy = save_backup_copy(path, _backup_suffix(path, ".before-" + date))
            if copy is None:
                return NOT_SAVED, "the copy of %s could not be made" % name
            kept[name] = copy
    done: list = []
    for name, text in files:
        if not write_text_atomic(os.path.join(folder, name), text):
            for back in done:                                # never half of the pair
                if back in kept:
                    try:
                        write_text_atomic(os.path.join(folder, back), read_player_text(kept[back]))
                    except (OSError, ValueError, UnicodeError):
                        log.exception("%s could not be put back from %s", back, kept[back])
            return NOT_SAVED, "%s could not be written" % name
        done.append(name)
    marks = sorted(_downloaded(folder) | {_digest(got.rosters)})
    write_text_atomic(os.path.join(folder, DOWNLOADED_MARK), "\n".join(marks) + "\n")
    debuglog.event("rosters", "saved", logging.INFO, folder=folder, files=[name for name, _ in files], copies=sorted(kept.values()))
    return OK, ""


def reload(g) -> None:
    """The game reads the customization again at once (the Customize item's Reload), so quick games, seasons and new franchises use the new files."""
    custom = getattr(g, "customization", None)
    if custom is None:
        return
    custom.reload()
    g.apply_customization()


# ----- the sentences -----

def reason_of(result: str, detail: str) -> str:
    if result == OFFLINE:
        return X.text("NXZ-U06")
    if result == SERVER:
        return X.text("NXZ-U07")
    if result == BAD_FILE:
        return X.text("NXZ-U08", label=detail.rstrip("."))
    return X.text("NXZ-U09")


def sentence(result: str, version: str = "", detail: str = "") -> str:
    if result == OK:
        return X.text("NXZ-U03", label=RU.spoken_date(version))
    if result == NOTHING_NEWER:
        return X.text("NXZ-U04", label=RU.spoken_date(version))
    if result == STOPPED:
        return X.text("NXF-54")
    if result == KEPT_OWN:
        return X.text("NXZ-U13")
    return X.text("NXZ-U05", label=reason_of(result, detail))


def conversion_sentence(converted: dict) -> str:
    """Design 21.6 (6): what the conversion did (rule 0.28 (4)); the second part only when real men joined."""
    joined = converted.get("joined", 0) if isinstance(converted, dict) else 0
    return X.text("NXZ-U19", n=joined) if joined else X.text("NXZ-U20")


# ----- the menu item -----

def _menu_ask(speech, keys):
    """A question of an F9 menu: a two-item list, the first item current; Enter takes the item, Escape is the first."""
    from ...game.spoken_menu import ListPicker

    def ask(question: str, items: list) -> int:
        chosen = ListPicker(speech, keys, question.strip(), len(items), lambda i: items[i]).run()
        return 0 if chosen is None else chosen
    return ask


def run(g, speech, keys, store, fetch=None) -> str:
    """F9's item (Customize; Franchise after "get the latest calendar"): says that it is asking, waits for the answer on a thread (Escape stops the
    wait), asks about the player's own file, saves, and returns the sentence of the result; with a franchise in use whose league is older, the offer
    of 21.10 follows. `store` is the franchise store or None."""
    if fetch is None:
        from ...data.web import fetch as web_fetch

        def fetch(url):
            return web_fetch(url, timeout=TIMEOUT, max_bytes=MAX_BYTES)
    folder = folder_of(g)
    speech.stop()
    speech.say_async(X.text("NXZ-U02"))
    debuglog.event("rosters", "asked", logging.INFO, local=local_version(folder, ROSTERS_FILE))
    stop = threading.Event()
    box: dict = {}

    def work():
        try:
            box["got"] = download(fetch, folder)
        except Exception as exc:                                 # never a reason to stop the game
            log.exception("getting the latest rosters failed")
            box["got"] = Download(SERVER, detail=str(exc)[:200])
    worker = threading.Thread(target=work, name="nfl4-rosters", daemon=True)
    worker.start()
    while worker.is_alive():
        if keys.key_waiting() and keys.read_key() == KEY_ESCAPE:
            stop.set()
            debuglog.event("rosters", "rosters_download", logging.INFO, result=STOPPED, version="", size=0)
            return X.text("NXF-54")
        worker.join(0.05)
        debuglog.beat()
    got = box.get("got", Download(SERVER, detail="no answer"))
    result, detail = got.result, got.detail
    if result == OK and own_rosters(folder):
        answer = _menu_ask(speech, keys)(X.text("NXZ-U10"), [X.text("NXZ-U11"), X.text("NXZ-U12")])
        debuglog.event("rosters", "own_file_question", logging.INFO, replace=answer == 1)
        if answer != 1:
            result = KEPT_OWN
    if result == OK:
        result, detail = save(folder, got)
        if result == OK:
            reload(g)
    debuglog.event("rosters", "rosters_download", logging.INFO, result=result, version=got.version, size=len(got.rosters),
                   free_agents=len(got.free), detail=str(detail)[:200])
    text = sentence(result, got.version, detail)
    if result in (OK, NOTHING_NEWER, KEPT_OWN) and store is not None:
        more = offer(g, speech, keys, store)
        if more:
            text = text.rstrip() + " " + more.lstrip()
    return text


# ----- the offer to a franchise (design 21.10, "WHAT IT CHANGES") -----

def _in_use(g, store) -> bool:
    return bool(getattr(g, "franchise_in_use", True)) and getattr(store, "league", None) is not None


def offer(g, speech, keys, store, ask=None) -> str | None:
    """The question of 21.10 once for the league's newer rosters, and the update when the player says yes. Returns the sentence of the answer, or None
    when nothing is offered (nothing newer, answered already, a game being played, the draft or the cut: it waits). `ask(question, items)` gives the
    index of the answer (the program's flow passes FranchiseQuestion's; F9 a two-item list)."""
    league = getattr(store, "league", None)
    real = getattr(g, "real_names", None)
    version = RU.offer_due(league, real)
    if not version or not _in_use(g, store):
        return None
    if getattr(g, "play_engine", None) is not None or not RU.allowed(league):
        debuglog.event("rosters", "offer_waits", logging.INFO, version=version, stage=league.stage, stage_no=league.stage_no)
        return None
    question = X.text("NXZ-U14", label=RU.spoken_date(version))
    answer = (ask or _menu_ask(speech, keys))(question, [X.text("NXZ-U15"), X.text("NXZ-U16")])
    debuglog.event("rosters", "offer_answered", logging.INFO, version=version, update=answer == 1)
    if answer != 1:
        league.roster_offer = version
        store.save()
        return X.text("NXZ-U18")
    return apply_update(g, store, real, version)


def backup_names(folder: str) -> set:
    """The names of the player's earlier rosters (rosters.txt.before-*): real men a league may still have, so the update knows they were real."""
    from .. import real_names
    names: set = set()
    try:
        entries = sorted(n for n in os.listdir(folder) if n.lower().startswith(ROSTERS_FILE + ".before"))
    except OSError:
        return names
    for name in entries:
        text = _player_text(folder, name)
        if text is None:
            continue
        try:
            parsed = cl.parse_list(text, real_names.GAME, real_names.ROSTERS)
        except cl.ListFormatError:
            continue
        problems = {kind: cl.Problems(real_names.FILE_NAMES[kind]) for kind in real_names.FILE_NAMES}
        names |= real_names.build([], parsed.entries, [], None, problems).real_full_names()
    return names


def keep_league_copy(store, version: str) -> str | None:
    """league.sav as it is now, kept as league.sav.before-rosters-<date> (a name already there gets -2, -3...). The name, or None."""
    files = store.files
    if not files.exists(D.LEAGUE_FILE):
        return None
    base = D.LEAGUE_FILE + LEAGUE_BACKUP + (RU.date_of(version) or time.strftime("%Y-%m-%d"))
    target, number = base, 2
    while files.exists(target):
        target, number = "%s-%d" % (base, number), number + 1
    return target if files.copy(D.LEAGUE_FILE, target) else None


def apply_update(g, store, real, version: str) -> str:
    """Yes: the league saved and kept as a copy, the 31 teams brought up to the file (roster_update.update), the whole-file check, the league saved.
    Anything that fails puts the league back as it was (nothing half done) and says so."""
    from .league import LeagueRecord
    league = store.league
    store.save()
    copy = keep_league_copy(store, version)
    before = league.to_json()
    try:
        known = RU.known_real_names(real, backup_names(folder_of(g)))
        counts = RU.update(league, real, known)
        league.check()
    except Exception:
        log.exception("the league could not be brought up to the newer rosters")
        again = LeagueRecord.from_json(before)
        again.reserves_on, again.converted = league.reserves_on, league.converted
        again.roster_offer = version                      # asked and answered: not asked again at every opening (the log has the cause)
        store.league = again
        store.save()
        debuglog.event("rosters", "league_update_failed", logging.WARNING, version=version)
        return X.text("NXZ-U21")
    store.save()
    debuglog.event("rosters", "league_updated", logging.INFO, version=version, copy=copy, n=counts["n"])
    return X.text("NXZ-U17", label=RU.spoken_date(version), n=counts["n"])


# ----- where the player opens the franchise (mode.py's hooks) -----

def at_opening(p) -> None:
    """The conversion's sentence (once), then the offer (once a version), in the program's own flow: mode.resume for a league opened outside its
    regular season, FranchiseSeason.before_menu at the week's menu. Never with a saved game about to go on (the game is being played)."""
    store = getattr(p, "store", None)
    league = getattr(store, "league", None)
    if league is None or getattr(p, "saved_game", False):
        return
    g = p.g
    converted = league.converted
    if isinstance(converted, dict) and not converted.get("told"):
        converted["told"] = True                          # said once: the league is format 19 at its next save, so it is never converted again
        g.say2(conversion_sentence(converted))
        debuglog.event("franchise", "conversion_told", logging.INFO, **{k: v for k, v in converted.items() if k != "told"})
    if not RU.offer_due(league, getattr(g, "real_names", None)):
        return
    from .question import FranchiseQuestion
    text = offer(g, None, None, store, ask=lambda question, items: FranchiseQuestion(g, question, items).ask())
    if text:
        g.say2(text)
