"""Get the latest rosters, the offer of newer rosters to a franchise and the conversion's sentence (nfl4 only, rule 0.13; CLAUDE.md 0.32, NX-L9;
NFL_FRANCHISE_DESIGN 21.6 (6), 21.10, 21.11; SR.6). This is inspired by Jim Kitchen.

The network is faked (a fetch that answers from a dict, like test_calendar_download_d128.py); the repository's `rosters` folder is not published yet,
so a 404 must say the player already has the newest rosters (D-141). The league update runs on drrig.full_league (a new franchise of the real rosters
made exact) with a rosters.txt changed for the test: a man moved between two computer teams, a man the file has nowhere, new men, a man of the
player's team named on a computer team.
"""
import os
import threading

import pytest

from drrig import full_league
from nfl4.data import customlists as cl
from nfl4.data import web
from nfl4.extras import nx_texts as X
from nfl4.extras import real_names as R
from nfl4.extras import tuning as T
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import real_roster as RR
from nfl4.extras.franchise import roster_update as RU
from nfl4.extras.franchise import rosters_flow as RF
from nfl4.extras.franchise.files import MemoryFiles
from nfl4.extras.franchise.league import DRAFT, OFFSEASON, SEASON
from nfl4.extras.franchise.store import FranchiseStore

NEW = "season 2026, as of 2026-11-02"
NEW_SPOKEN = "November 2, 2026"


def shipped(kind=R.ROSTERS) -> str:
    return R.shipped_text(kind)


def with_version(text: str, version: str) -> str:
    return "\n".join(("VERSION = " + version) if line.startswith("VERSION") else line for line in text.split("\n"))


def body(text: str) -> bytes:
    return text.encode("utf-8")


class Net:
    """A fake fetch: file name -> body (missing: 404), or an exception to raise."""

    def __init__(self, files=None, error=None):
        self.files, self.error, self.asked = files or {}, error, []

    def __call__(self, url):
        self.asked.append(url)
        if self.error is not None:
            raise self.error
        name = url.rsplit("/", 1)[1]
        if name in self.files:
            value = self.files[name]
            return value if isinstance(value, tuple) else (200, value)
        return 404, b"404: Not Found"


class Speech:
    def __init__(self):
        self.said = []

    def stop(self):
        pass

    def say_async(self, text):
        self.said.append(text)


class Keys:
    """read_key gives the scripted keys (then Enter); key_waiting is true once `escape_after` calls have passed."""

    def __init__(self, keys=(), escape_after=None):
        self.keys, self.escape_after, self.calls = list(keys), escape_after, 0

    def key_waiting(self):
        self.calls += 1
        return self.escape_after is not None and self.calls >= self.escape_after

    def read_key(self):
        return self.keys.pop(0) if self.keys else 13


class Game:
    """What the flow needs of the Game: the customization (or none), the real names, whether a game is being played and the franchise is in use."""

    def __init__(self, custom=None, real=None):
        self.customization = custom
        self.real_names = real if real is not None else (custom.snapshot.real_names if custom is not None else R.defaults())
        self.play_engine = None
        self.franchise_in_use = True
        self.applied = 0

    def apply_customization(self):
        self.applied += 1
        self.real_names = self.customization.snapshot.real_names


@pytest.fixture
def folder(tmp_path):
    return tmp_path / "customize"


@pytest.fixture
def game(folder):
    from nfl4.data.customize import Customization
    return Game(Customization(str(folder), extras=True))


def read(path) -> bytes:
    with open(path, "rb") as handle:
        return handle.read()


# ----- the address and the versions -----

def test_the_address_is_the_games_own_repository_folder_rosters():
    assert RF.url_of("rosters.txt") == "https://raw.githubusercontent.com/joshknnd1982/nfl-football-4-audio-game/master/rosters/rosters.txt"


def test_versions_compare_by_their_dates_and_are_said_as_dates():
    assert RU.newer(NEW, "season 2026, as of 2026-10-25") and not RU.newer("season 2026, as of 2026-10-25", NEW)
    assert not RU.newer(NEW, NEW) and RU.spoken_date(NEW) == NEW_SPOKEN
    assert RU.date_of("as of 2027-01-05") == "2027-01-05" and RU.spoken_date("my own rosters") == "my own rosters"
    assert R.defaults().roster_version == RF.text_version(shipped()) == "season 2026, as of 2026-10-25"


def test_the_shipped_files_pass_the_downloads_own_checks():
    assert RF.rosters_problem(shipped()) is None and RF.free_agents_problem(shipped(R.FREE_AGENTS)) is None


# ----- the download -----

def test_newer_rosters_are_checked_saved_with_a_copy_of_the_old_and_read_at_once(game, folder):
    old_rosters, old_free = read(folder / "rosters.txt"), read(folder / "free_agents.txt")
    net = Net({"rosters.txt": body(with_version(shipped(), NEW)), "free_agents.txt": body(with_version(shipped(R.FREE_AGENTS), NEW))})
    speech = Speech()
    text = RF.run(game, speech, Keys(), None, fetch=net)
    assert speech.said == [X.text("NXZ-U02")] and text == X.text("NXZ-U03", label=NEW_SPOKEN)
    assert RF.text_version(read(folder / "rosters.txt").decode("utf-8")) == NEW
    assert read(folder / "rosters.txt.before-2026-11-02") == old_rosters and read(folder / "free_agents.txt.before-2026-11-02") == old_free
    assert game.applied == 1 and game.real_names.roster_version == NEW                  # read at once: the next game, season or franchise uses it
    assert not RF.own_rosters(str(folder))                                               # a file this item wrote is the game's, never "his own"


def test_the_same_or_an_older_version_changes_nothing(game, folder):
    before = read(folder / "rosters.txt")
    for version in ("season 2026, as of 2026-10-25", "season 2026, as of 2026-09-01"):
        text = RF.run(game, Speech(), Keys(), None, fetch=Net({"rosters.txt": body(with_version(shipped(), version))}))
        assert text == X.text("NXZ-U04", label="October 25, 2026")
    assert read(folder / "rosters.txt") == before and game.applied == 0
    assert not [n for n in os.listdir(folder) if ".before-" in n and "layout" not in n]


def test_the_repository_without_a_rosters_folder_says_you_have_the_newest(game, folder):
    net = Net()
    text = RF.run(game, Speech(), Keys(), None, fetch=net)
    assert text == X.text("NXZ-U04", label="October 25, 2026") and net.asked == [RF.url_of("rosters.txt")]


@pytest.mark.parametrize("damage", ["parse", "check", "team", "header", "free"])
def test_a_damaged_file_is_refused_and_the_players_files_stay(game, folder, damage):
    text = with_version(shipped(), NEW)
    free = with_version(shipped(R.FREE_AGENTS), NEW)
    if damage == "parse":
        text += "T01P99 = XX 1 Not A Position\n"
    elif damage == "check":
        lines = text.split("\n")
        first = next(i for i, line in enumerate(lines) if line.startswith("T01P01 ="))
        second = next(i for i, line in enumerate(lines) if line.startswith("T01P02 ="))
        lines[second] = lines[second].split("=")[0] + "= " + lines[first].split("= ", 1)[1]        # a man twice on one team
        text = "\n".join(lines)
    elif damage == "team":
        text = "\n".join(line for line in text.split("\n") if not line.startswith("T32"))
    elif damage == "header":
        text = text.replace("# NFL Football 4 rosters, format 1", "# something else", 1)
    else:
        free += "F999 = XX 30 Nobody\n"
    before = {name: read(folder / name) for name in ("rosters.txt", "free_agents.txt")}
    got = RF.download(Net({"rosters.txt": body(text), "free_agents.txt": body(free)}), str(folder))
    assert got.result == RF.BAD_FILE and got.detail
    text_said = RF.run(game, Speech(), Keys(), None, fetch=Net({"rosters.txt": body(text), "free_agents.txt": body(free)}))
    assert text_said == X.text("NXZ-U05", label=X.text("NXZ-U08", label=got.detail.rstrip(".")))
    assert {name: read(folder / name) for name in before} == before and game.applied == 0


def test_no_connection_and_a_server_error_say_why_and_change_nothing(game, folder):
    before = read(folder / "rosters.txt")
    for kind in ("offline", "timeout"):
        assert RF.run(game, Speech(), Keys(), None, fetch=Net(error=web.WebError(kind, "test"))) == X.text("NXZ-U05", label=X.text("NXZ-U06"))
    assert RF.run(game, Speech(), Keys(), None, fetch=Net({"rosters.txt": (500, b"")})) == X.text("NXZ-U05", label=X.text("NXZ-U07"))
    assert read(folder / "rosters.txt") == before


def test_a_folder_that_cannot_be_written_says_so(game, folder, monkeypatch):
    monkeypatch.setattr(RF, "write_text_atomic", lambda path, text: False)
    text = RF.run(game, Speech(), Keys(), None, fetch=Net({"rosters.txt": body(with_version(shipped(), NEW))}))
    assert text == X.text("NXZ-U05", label=X.text("NXZ-U09"))


def test_the_players_own_rosters_ask_first_and_no_keeps_them(game, folder):
    own = read(folder / "rosters.txt").replace(b"Joe Burrow", b"Joseph Burrow")
    (folder / "rosters.txt").write_bytes(own)
    assert RF.own_rosters(str(folder))
    newer = Net({"rosters.txt": body(with_version(shipped(), NEW))})
    speech = Speech()
    text = RF.run(game, speech, Keys([13]), None, fetch=newer)                         # Enter on the first answer: no
    assert text == X.text("NXZ-U13") and read(folder / "rosters.txt") == own
    assert any(X.text("NXZ-U11") in s for s in speech.said)
    assert RF.run(game, Speech(), Keys([27]), None, fetch=newer) == X.text("NXZ-U13")   # Escape is no too
    text = RF.run(game, Speech(), Keys([40, 13]), None, fetch=newer)                   # Down, Enter: yes
    assert text == X.text("NXZ-U03", label=NEW_SPOKEN) and read(folder / "rosters.txt.before-2026-11-02") == own


def test_a_copy_is_never_written_over(game, folder):
    (folder / "rosters.txt.before-2026-11-02").write_bytes(b"an earlier copy")
    RF.run(game, Speech(), Keys(), None, fetch=Net({"rosters.txt": body(with_version(shipped(), NEW))}))
    assert read(folder / "rosters.txt.before-2026-11-02") == b"an earlier copy" and os.path.isfile(folder / "rosters.txt.before-2026-11-02-2")


def test_free_agents_that_are_not_newer_stay_and_a_missing_file_is_no_failure(game, folder):
    before = read(folder / "free_agents.txt")
    net = Net({"rosters.txt": body(with_version(shipped(), NEW)), "free_agents.txt": body(shipped(R.FREE_AGENTS))})
    assert RF.run(game, Speech(), Keys(), None, fetch=net) == X.text("NXZ-U03", label=NEW_SPOKEN)
    assert read(folder / "free_agents.txt") == before
    later = "season 2026, as of 2026-12-01"
    assert RF.run(game, Speech(), Keys(), None, fetch=Net({"rosters.txt": body(with_version(shipped(), later))})) == X.text(
        "NXZ-U03", label="December 1, 2026")


def test_escape_stops_the_wait_and_nothing_is_saved(game, folder):
    gate = threading.Event()
    before = read(folder / "rosters.txt")

    def slow(url):
        gate.wait(5)
        return 200, body(with_version(shipped(), NEW))
    text = RF.run(game, Speech(), Keys([27], escape_after=2), None, fetch=slow)
    gate.set()
    assert text == X.text("NXF-54") and read(folder / "rosters.txt") == before


def test_f9_customize_has_the_item_with_the_nfl_rules_and_it_asks_github(tmp_path, monkeypatch):
    from nfl4.data.customize import Customization
    from programrig import DOWN, ENTER, ESC, preset_season, program_rig, said
    END = 35
    asked = []
    monkeypatch.setattr(web, "fetch", lambda url, **kw: asked.append(url) or (404, b""))
    rig = program_rig(tmp_path, [], preset=preset_season())
    rig.game.customization = Customization(str(tmp_path / "customize"), extras=True)
    rig.game.apply_customization()
    rig.keys.answers = [DOWN, DOWN, ENTER, END, ENTER, ESC, ESC]
    rig.game.functions.run()
    spoken = said(rig)
    assert "Customize. 6 items. Press F1 for help. " in spoken[3] and X.text("NXZ-U01") + "." in spoken
    assert asked == [RF.url_of("rosters.txt")] and X.text("NXZ-U04", label="October 25, 2026") in spoken
    rig = program_rig(tmp_path / "classic", [], preset=preset_season())
    rig.game.customization = Customization(str(tmp_path / "classic" / "customize"))       # Classic: the five items of the original's files
    rig.keys.answers = [DOWN, DOWN, ENTER, ESC, ESC]
    rig.game.functions.run()
    assert "Customize. 5 items. Press F1 for help. " in said(rig)[3]


# ----- the league update (design 21.10, "WHAT IT CHANGES") -----

OWN = 5
A, B, C, E, F = 1, 2, 3, 4, 6


def lines_of(text):
    return text.split("\n")


def newer_rosters(league):
    """rosters.txt of NEW: A's starting quarterback moves to B; a new quarterback joins A; a real receiver of C is gone from the file; three new
    linemen join E (over 53); a man of the player's team is named on F; every other line as shipped."""
    text = with_version(shipped(), NEW)
    lines = lines_of(text)
    qb = next(i for i, line in enumerate(lines) if line.startswith("T01P") and "= QB " in line)
    mover = lines[qb].split(" ", 4)[-1]                                       # "Joe Burrow"
    lines[qb] = lines[qb].split("=")[0] + "= QB 2 Test Quarterback"
    lines.append("T02P198 = QB 9 %s" % mover)
    gone_at = next(i for i, line in enumerate(lines) if line.startswith("T03P") and "= WR " in line
                   and league_name(league, C, line.split(" ", 4)[-1]) is not None)
    gone = lines[gone_at].split(" ", 4)[-1]
    del lines[gone_at]
    lines += ["T04P197 = LT 60 New Tackle One", "T04P198 = LT 61 New Tackle Two", "T04P199 = LT 62 New Tackle Three"]
    own = next(p for p in RR.members(league, OWN) if p.position == "WR" and any(p.name == line.split(" ", 4)[-1] for line in lines if line.startswith("T%02dP" % OWN)))
    lines.append("T06P197 = WR 81 %s" % own.name)
    problems = {kind: cl.Problems(R.FILE_NAMES[kind]) for kind in R.FILE_NAMES}
    entries = R.parse_entries("\n".join(lines) + "\n", R.ROSTERS).entries
    real = R.build([], entries, [], R.defaults(), problems)
    return real, mover, gone, own


def league_name(league, team, name):
    return next((p for p in league.players.values() if p.team == team and p.status == "active" and p.name == name), None)


@pytest.fixture(scope="module")
def updated():
    league = full_league(team=OWN)
    league.reserves_on = True
    league.check()
    real, mover, gone, own = newer_rosters(league)
    before = {pid: p.to_list() for pid, p in league.players.items() if p.team == OWN}
    chart = dict(league.chart[OWN - 1])
    moving = league_name(league, A, mover)
    contract = (moving.salary, moving.years)
    dead = list(league.dead)
    counts = RU.update(league, real, RU.known_real_names(real))
    return dict(league=league, real=real, counts=counts, before=before, chart=chart, mover=moving, contract=contract, gone=gone, own=own, dead=dead)


def test_the_players_team_is_untouched_man_for_man(updated):
    league = updated["league"]
    assert {pid: p.to_list() for pid, p in league.players.items() if p.team == OWN} == updated["before"]
    assert league.chart[OWN - 1] == updated["chart"]
    assert updated["own"].team == OWN and updated["counts"]["with_you"] >= 1                 # named on F, he stays with the player


def test_a_man_moving_between_two_computer_teams_keeps_his_contract(updated):
    man = updated["mover"]
    assert (man.team, man.status) == (B, "active") and (man.salary, man.years) == updated["contract"]
    assert updated["counts"]["moved"] >= 1


def test_a_man_the_file_has_nowhere_is_a_free_agent_with_no_dead_money(updated):
    league = updated["league"]
    man = next(p for p in league.players.values() if p.name == updated["gone"])
    assert (man.status, man.team, man.salary, man.years) == ("free", 0, 0, 0) and man.left == league.season
    assert league.dead == updated["dead"]


def test_new_men_join_and_a_team_over_53_is_cut_to_53_with_its_minimums(updated):
    league = updated["league"]
    assert any(p.name == "Test Quarterback" and p.team == A and p.status == "active" for p in league.players.values())
    assert updated["counts"]["joined"] >= 4 and updated["counts"]["cut"] >= 3
    for team in range(1, D.TEAMS + 1):
        assert RR.roster_count(league, team) <= D.ROSTER_MAX, team
        if team != OWN:
            have = RR.counts_by_group(RR.members(league, team))
            assert all(have.get(group, 0) >= least for group, least in T.FR_FAMILY_MIN.items()), (team, have)


def test_the_league_passes_its_checks_and_round_trips(updated):
    from nfl4.extras.franchise.league import LeagueRecord
    league = updated["league"]
    league.check()
    again = LeagueRecord.from_json(league.to_json())
    again.check()


def test_the_counts_say_the_men_who_moved_or_joined_and_the_offer_is_not_made_again(updated):
    league, counts = updated["league"], updated["counts"]
    assert 0 < counts["n"] <= counts["moved"] + counts["signed"] + counts["joined"]          # the men still there at the end (a man cut again is not)
    assert league.roster_version == league.roster_offer == NEW and RU.offer_due(league, updated["real"]) == ""


def test_the_charts_take_the_files_order_among_equals_and_its_returners(updated):
    league, real = updated["league"], updated["real"]
    teams = RR.file_teams(real)
    for team in (A, B, C):
        roles = league.chart[team - 1]["KR"]
        names = [league.players[pid].name for pid in roles]
        assert names == [n for n in teams[team].roles["KR"] if league_name(league, team, n) is not None]


# ----- the offer -----

def store_of(league):
    store = FranchiseStore(MemoryFiles())
    store.league = league
    league.reserves_on = True
    assert store.save()
    return store


def test_the_legacy_label_is_not_offered_the_rosters_it_was_made_from():
    league = full_league(team=OWN)
    assert league.roster_version == R.defaults().roster_version                             # a new league carries the rosters.txt VERSION it was made from
    league.roster_version = R.defaults().version                                            # SR.4 and SR.5 wrote coaches.txt's VERSION (a legacy label)
    assert R.defaults().version != R.defaults().roster_version
    assert RU.offer_due(league, R.defaults()) == ""
    real, *_ = newer_rosters(league)
    assert RU.offer_due(league, real) == NEW


def test_no_keeps_the_league_and_is_not_asked_again(tmp_path, monkeypatch):
    monkeypatch.setattr(RF, "folder_of", lambda g: str(tmp_path))
    league = full_league(team=OWN)
    real, *_ = newer_rosters(league)
    store = store_of(league)
    before = league.to_json()
    asked = []
    text = RF.offer(Game(real=real), None, None, store, ask=lambda q, items: asked.append((q, items)) or 0)
    assert text == X.text("NXZ-U18") and asked == [(X.text("NXZ-U14", label=NEW_SPOKEN), [X.text("NXZ-U15"), X.text("NXZ-U16")])]
    assert league.roster_offer == NEW and RF.offer(Game(real=real), None, None, store, ask=lambda q, items: 1) is None
    league.roster_offer = ""
    assert league.to_json() == before                                                  # nothing else of the league changed


def test_yes_keeps_a_copy_of_the_league_and_says_the_number(tmp_path, monkeypatch):
    monkeypatch.setattr(RF, "folder_of", lambda g: str(tmp_path))
    league = full_league(team=OWN)
    real, *_ = newer_rosters(league)
    store = store_of(league)
    saved = store.files.data["league.sav"]
    text = RF.offer(Game(real=real), None, None, store, ask=lambda q, items: 1)
    copy = store.files.data.get("league.sav.before-rosters-2026-11-02")
    assert copy == saved
    n = int(text.split(":")[1].split()[0])
    assert text == X.text("NXZ-U17", label=NEW_SPOKEN, n=n) and n > 0
    assert store.league.roster_version == NEW
    from nfl4.extras.franchise.league import LeagueRecord
    LeagueRecord.from_json(store.files.data["league.sav"].decode("utf-8")).check()


def test_a_failed_update_puts_the_league_back(tmp_path, monkeypatch):
    monkeypatch.setattr(RF, "folder_of", lambda g: str(tmp_path))
    league = full_league(team=OWN)
    real, *_ = newer_rosters(league)
    store = store_of(league)
    before = league.to_json()

    def broken(lg, rl, known=frozenset()):
        lg.players[next(iter(lg.players))].team = 99
        raise ValueError("test")
    monkeypatch.setattr(RU, "update", broken)
    assert RF.offer(Game(real=real), None, None, store, ask=lambda q, items: 1) == X.text("NXZ-U21")
    assert store.league.to_json() == before.replace('"roster_offer":""', '"roster_offer":"' + NEW + '"')


@pytest.mark.parametrize("where", ["game", "draft", "cut", "draft_stage"])
def test_the_offer_is_not_made_in_a_game_the_draft_or_the_cut(tmp_path, monkeypatch, where):
    monkeypatch.setattr(RF, "folder_of", lambda g: str(tmp_path))
    league = full_league(team=OWN)
    real, *_ = newer_rosters(league)
    game = Game(real=real)
    if where == "game":
        game.play_engine = object()
    elif where == "draft_stage":
        league.stage = DRAFT
    else:
        league.stage, league.stage_no = OFFSEASON, D.STAGE_DRAFT if where == "draft" else D.STAGE_CUT
    store = FranchiseStore(MemoryFiles())
    store.league = league
    asked = []
    assert RF.offer(game, None, None, store, ask=lambda q, items: asked.append(q) or 1) is None
    assert asked == [] and league.roster_offer == "" and league.roster_version != NEW
    assert RU.allowed(league) is (where == "game")
    league.stage, league.stage_no = SEASON, 0
    assert RU.allowed(league)


def test_the_item_with_a_franchise_in_use_offers_after_the_download(game, folder, tmp_path, monkeypatch):
    league = full_league(team=OWN)
    store = store_of(league)
    net = Net({"rosters.txt": body(with_version(shipped(), NEW))})
    text = RF.run(game, Speech(), Keys([13]), store, fetch=net)                          # the offer's Enter: no
    assert text == X.text("NXZ-U03", label=NEW_SPOKEN).rstrip() + " " + X.text("NXZ-U18").lstrip()
    assert league.roster_offer == NEW


# ----- the conversion's sentence (design 21.6 (6)) -----

class Program:
    def __init__(self, league, real=None):
        self.store = FranchiseStore(MemoryFiles())
        self.store.league = league
        self.saved_game = False
        self.g = Game(real=real or R.defaults())
        self.g.said = []
        self.g.say2 = self.g.said.append


def test_the_conversion_is_said_once_with_the_men_who_joined():
    assert RF.conversion_sentence({"from": 16, "positions": 40, "joined": 7}) == X.text("NXZ-U19", n=7)
    assert RF.conversion_sentence({"from": 17, "positions": 40, "joined": 0}) == X.text("NXZ-U20")
    league = full_league(team=OWN)
    league.converted = {"from": 16, "positions": 12, "joined": 3}
    p = Program(league)
    RF.at_opening(p)
    RF.at_opening(p)
    assert p.g.said == [X.text("NXZ-U19", n=3)] and league.converted["told"] is True
    league.converted = None
    RF.at_opening(p)
    assert len(p.g.said) == 1


def test_nothing_is_said_or_asked_with_a_saved_game_about_to_go_on():
    league = full_league(team=OWN)
    league.converted = {"from": 16, "positions": 12, "joined": 3}
    p = Program(league)
    p.saved_game = True
    RF.at_opening(p)
    assert p.g.said == [] and not league.converted.get("told")
