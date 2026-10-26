"""NX-B2 (the owner's bug report of 2026-10-24, D-142, D-144): "it should be using the current 53 man rosters for each team" (nfl4 only, rule 0.13).

The shipped rosters.txt holds every player of each team's active roster (the offensive linemen and the long snapper too) and its practice squad (lines
marked PS), researched 2026-10-24 (spec/NFL_NAMES_RESEARCH.md section 6); the game plays its places from the active players of its positions exactly as
before; a player's rosters.txt that is exactly the older shipped copy is refreshed once (the copy kept), an edited one stays.
"""
import hashlib
import os

import pytest

from nfl4.data import customlists as cl
from nfl4.data import customize as C
from nfl4.extras import quarterbacks as Q
from nfl4.extras import real_names as R
from nfl4.extras.franchise import data as D


@pytest.fixture(autouse=True)
def fresh_defaults():
    R.reset_defaults_cache()
    yield
    R.reset_defaults_cache()


def test_the_shipped_file_is_the_53_man_rosters_of_2026_10_24():
    real = R.defaults()
    assert "VERSION = season 2026, as of 2026-10-25" in R.shipped_text(R.ROSTERS)     # SR.2: the real rosters of 2026-10-25        # (RealNames.version is coaches.txt's: the coaches of 2026-10-22)
    for team in range(1, 33):
        active, squad = real.active(team), real.squad(team)
        playing = [p for p in active if p.pos != "RET"]
        assert 50 <= len(playing) <= 55, team                          # SR.2: 53 and the game day's elevations (the Dolphins' squad kicker)                         # the pages showed 50 to 53 (spec/NFL_NAMES_RESEARCH.md section 6)
        assert 15 <= len(squad) <= 19, team
        positions = {p.pos for p in playing} | {p.pos for p in squad if p.pos in ("K", "P")}     # SR.4: the Dolphins' kicker is on the squad
        assert {"QB", "OL", "LS", "K", "P", "DL", "LB", "CB", "S", "WR"} <= positions, team
        assert sum(1 for p in playing if p.pos == "OL") >= 7, team
        assert 1 <= len([p for p in active if p.pos == "RET"]) <= 2 * 9, team     # SR.4: every man of the KR and PR roles, in turn (the view takes two)
        names = [p.name.casefold() for p in playing] + [p.name.casefold() for p in squad]
        assert len(names) == len(set(names)), team                     # nobody twice (a returner's RET line repeats his own)
        assert all(p.pos != "RET" for p in squad), team


def test_the_practice_squad_and_the_line_never_take_a_place_in_a_game():
    real = R.defaults()
    for team in range(1, 33):
        kickers = {p.pos for p in real.active(team)}
        squad = {p.name for p in real.squad(team) if not (p.pos in ("K", "P") and p.pos not in kickers)}   # SR.4: a squad kicker the view elevates
        line = {p.name for p in real.active(team) if p.pos in ("OL", "LS")}
        names = set(real.places(team)) | set(real.roster(team, None).names())
        assert not (names & {real.spoken(n) for n in squad | line}), team
        assert real.quarterback(team) not in {real.spoken(n) for n in squad}
        assert all(not p.squad for p in Q.quarterbacks_of(real, team)), team


def test_a_practice_squad_line_is_read_and_a_squad_returner_is_refused():
    problems = {kind: cl.Problems(R.FILE_NAMES[kind]) for kind in R.FILE_NAMES}
    text = "# NFL Football 4 rosters, format 1.\nT01P01 = QB 9 Joe Burrow\nT01P02 = OL 75 Orlando Brown Jr.\nT01P03 = PS WR 14 Jordan Moore\nT01P04 = PS RET 1 Nobody\n"
    entries = R.parse_entries(text, R.ROSTERS).entries
    real = R.build([], entries, [], None, problems)
    assert [(p.pos, p.name, p.squad) for p in real.rosters[0]] == [("QB", "Joe Burrow", False), ("OL", "Orlando Brown Jr.", False),
                                                                     ("WR", "Jordan Moore", True)]
    assert problems[R.ROSTERS].count == 1
    assert real.quarterback(1) == "Joe Burrow" and [p.name for p in real.squad(1)] == ["Jordan Moore"]


def test_an_older_file_without_the_new_lines_is_read_as_it_always_was():
    problems = {kind: cl.Problems(R.FILE_NAMES[kind]) for kind in R.FILE_NAMES}
    text = "# NFL Football 4 rosters, format 1.\nT02P01 = QB 1 A Quarterback\nT02P02 = RB 2 A Back\n"
    real = R.build([], R.parse_entries(text, R.ROSTERS).entries, [], None, problems)
    assert real.squad(2) == [] and [p.name for p in real.active(2)] == ["A Quarterback", "A Back"] and problems[R.ROSTERS].count == 0


def write(folder, text):
    with open(os.path.join(folder, "rosters.txt"), "w", encoding="utf-8", newline="\r\n") as fh:
        fh.write(text)


def test_an_older_shipped_copy_is_refreshed_once_and_kept_aside(tmp_path, monkeypatch):
    old = "# NFL Football 4 rosters, format 1.\nVERSION = season 2026, as of 2026-10-22\nT01P01 = QB 9 Joe Burrow\n"
    monkeypatch.setattr(C, "OLD_SHIPPED_ROSTERS", {hashlib.sha256(old.encode("utf-8")).hexdigest()})
    write(tmp_path, old)
    assert C.refresh_old_rosters(str(tmp_path)) == "refreshed"
    assert C.refresh_old_rosters(str(tmp_path)) == ""                  # once
    now = (tmp_path / "rosters.txt").read_text(encoding="utf-8")
    assert "as of 2026-10-25" in now and " = PS " in now
    assert (tmp_path / ("rosters.txt" + C.ROSTERS_BEFORE_REFRESH)).read_text(encoding="utf-8").replace("\r\n", "\n") == old


def test_a_file_the_player_changed_stays_his(tmp_path, monkeypatch):
    old = "# NFL Football 4 rosters, format 1.\nVERSION = season 2026, as of 2026-10-22\nT01P01 = QB 9 Joe Burrow\n"
    monkeypatch.setattr(C, "OLD_SHIPPED_ROSTERS", {hashlib.sha256(old.encode("utf-8")).hexdigest()})
    write(tmp_path, old + "T01P02 = QB 16 My Own Backup\n")
    assert C.refresh_old_rosters(str(tmp_path)) == ""
    assert "My Own Backup" in (tmp_path / "rosters.txt").read_text(encoding="utf-8")
    assert C.refresh_old_rosters(str(tmp_path / "nothing here")) == ""


def test_the_hash_of_the_0_13_0_copy_is_known():
    """The shipped file of 0.10.0 to 0.13.0 (git 6071f8e, season 2026 as of 2026-10-22) has this hash with LF line ends; a player's copy of it is replaced."""
    assert "962870e5691d6f7fe622d275d037334b59418f260742a27b98006ac50099c17e" in C.OLD_SHIPPED_ROSTERS
    shipped = R.shipped_text(R.ROSTERS)
    assert hashlib.sha256(shipped.encode("utf-8")).hexdigest() not in C.OLD_SHIPPED_ROSTERS      # the new file is never replaced by itself


def test_the_franchise_places_still_count_34():
    real = R.defaults()
    assert all(len(real.places(team)) == D.PLACE_COUNT for team in range(1, 33))


def test_a_new_franchise_has_the_real_practice_squads_and_made_up_players_only_fill_what_is_left():
    import random
    from drrig import SURNAMES
    from nfl4.extras.franchise import practice as P
    from nfl4.extras.franchise.league import new_league
    from nfl4.game.rnd import GameRandom
    real = R.defaults()
    league = new_league(GameRandom(random.Random(3)), SURNAMES, "Kim", 1, "20260101-000000", real=real)
    assert P.real_squads(league, real) == 0                                       # SR.4 (NX-L4): the new league has its real squads already
    for team in range(1, 33):
        names = {p.name for p in P.squad(league, team)}
        wanted = {real.spoken(p.name) for p in real.squad(team)}                  # every position now, the line and the snappers too
        elevated = {p.name for p in league.players.values() if p.team == team and p.status == "active" and p.name in wanted}
        assert names == wanted - elevated and len(names) <= P.SIZE + 1, team      # no made-up man fills a squad
    assert "Sean Clifford" in {p.name for p in P.squad(league, 1)}               # the Bengals' squad quarterback
    assert P.real_squads(league, real) == 0                                         # once
    # SR.4: a new franchise of the real rosters runs no top_up (mode.start_new): its squads are the real ones, 15 to 17 men
    # SR.7 (D-167): the real squads' real seasons, at most six veterans a squad (real_roster.cap_squad_veterans)
    for team in range(1, 33):
        assert sum(1 for p in P.squad(league, team) if p.seasons >= P.VETERAN_SEASONS) <= P.VETERANS, team
