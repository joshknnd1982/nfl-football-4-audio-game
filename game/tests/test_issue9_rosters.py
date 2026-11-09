"""GitHub issue 9 (Dennisl123, 2026-11-09, on 0.16.20): "It says 4 teams can't be updated. I also haven't played a game or made any trades. My
roster wasn't updated. This needs fixed." (nfl4 only, rule 0.13; CLAUDE.md 0.32, 0.34; D-222). This is inspired by Jim Kitchen.

FOUND (work\\i9_1109, the live pages of 2026-11-09, the day after a game day): the update kept every team whose page was over a league limit as it
was, and the club pages are over one for a day after a game (the game-day elevations still listed active, a release not yet off the squad). The old
rule sent back EVERY active man of the previous file's squad (the Lions' two, though the Lions had signed both to their 53), so the squad came to 18
and the whole team was kept. And a franchise's update never touched the player's own team (design 21.10), which the tester expected.

What is tested: the transactions page's clauses and their kinds (the real pages' sentences); only as many elevations as the team is over 53 and its
squad has room for, the page's elevated men first, a promoted man never; a release or a reserve move of the transactions page fits a team a day
behind; a whole read of 32 teams with three of them over a limit keeps none; the franchise's third answer brings the player's own team up too, keeps
the men he put first on his chart, drops his records of men who left, passes the league's checks and round-trips.
"""
import pytest

import test_rc_roster_live as RL
import test_rosters_update_sr6 as SR
from drrig import full_league
from nfl4.extras import nx_texts as X
from nfl4.extras import roster_file as RF
from nfl4.extras import roster_nfl as N
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import real_roster as RR
from nfl4.extras.franchise import roster_update as RU
from nfl4.extras.franchise import rosters_flow as F
from nfl4.extras.franchise.league import LeagueRecord


# ----- the transactions page -----

def page(*lines) -> bytes:
    return ("<html><body>%s</body></html>" % "".join("<p>%s</p>" % line for line in lines)).encode("utf-8")


@pytest.mark.parametrize("clause, kind", [
    ("elevated WR Brandon Johnson to the Active/Inactive Roster from the Practice Squad", N.ELEVATED),
    ("Elevated RB Cody Schrader to active roster", N.ELEVATED),
    ("The 49ers announced they have activated LB Jalen Graham and WR Malik Turner from the practice squad", N.ELEVATED),
    ("The Detroit Lions sign CB Nick Whiteside to the active roster from the practice squad", N.PROMOTED),
    ("Promoted S Taylor Rapp to active roster", N.PROMOTED),
    ("Signed WR Van Jefferson from the practice squad", N.PROMOTED),
    ("The Detroit Lions sign TE Tyler Conklin", N.PROMOTED),
    ("Broncos activate WR Pat Bryant from IR", N.PROMOTED),
    ("The Detroit Lions place S Thomas Harper on Reserve/Injured", N.RESERVE),
    ("Released LB Austin Keys", N.RELEASED),
    ("The 49ers Sign WR KhaDarel Hodge to Practice Squad", N.SIGNED_SQUAD),
    ("opened the practice window for WR Jacob Cowing (Injured Reserve List)", ""),
])
def test_each_kind_of_move_is_read_from_the_clubs_own_words(clause, kind):
    assert N.move_kind(clause) == kind


def test_clauses_split_at_each_move_but_not_at_a_jr_or_an_initial():
    clauses = N.transaction_clauses(page("11/04", "The Detroit Lions sign LB K.J. Britt to the active roster and sign LB Owen Pappoe to the practice "
                                         "squad. Elevated DB Sean Fresch Jr. to active roster.",
                                         "Signed LB Kyzir White to the practice squad, opened the practice window for WR Jacob Cowing."))
    assert "The Detroit Lions sign LB K.J. Britt to the active roster" in clauses
    assert "sign LB Owen Pappoe to the practice squad" in clauses
    assert "Elevated DB Sean Fresch Jr. to active roster" in clauses
    assert "opened the practice window for WR Jacob Cowing" in clauses


def test_a_mans_newest_move_decides_and_a_namesake_inside_a_longer_name_does_not():
    p = page("11/07", "The Lions sign TE Tyler Conklin.", "08/30", "The Lions release TE Tyler Conklin and DL Myles Adams.",
             "10/01", "Signed Joe Smithson to the practice squad.")
    moves = N.newest_moves(p, ["Tyler Conklin", "Myles Adams", "Joe Smith"])
    assert moves[N.name_key("Tyler Conklin")][0] == N.PROMOTED and moves[N.name_key("Myles Adams")][0] == N.RELEASED
    assert N.name_key("Joe Smith") not in moves
    assert N.newest_moves(None, ["Tyler Conklin"]) == {}


# ----- the elevations and the limits -----

def team_of(active: int, squad: int, extra=()):
    men = [RF.Man("WR", str(i), "Active Man %d" % i) for i in range(active)]
    men += [RF.Man("WR", str(60 + i), "Squad Man %d" % i, "PS") for i in range(squad)]
    men += list(extra)
    return RF.Team(men=men, roles={"KR": [], "PR": []})


def test_only_as_many_go_back_as_the_team_is_over_53_and_its_squad_has_room():
    # the Lions of 2026-11-09: 54 active, 16 on the squad, two men of the previous file's squad on the 53
    team = team_of(52, 16, [RF.Man("LB", "35", "Joe Bachie"), RF.Man("CB", "38", "Nick Whiteside")])
    previous = {N.name_key(n): (18, "PS", "LB", n) for n in ("Joe Bachie", "Nick Whiteside")}
    notes = []
    N.return_elevations({18: team}, previous, notes)
    assert (len(team.active()), len(team.squad())) == (53, 17) and len(notes) == 1          # the old rule sent both: a squad of 18
    full = team_of(52, 17, [RF.Man("LB", "35", "Joe Bachie"), RF.Man("CB", "38", "Nick Whiteside")])
    N.return_elevations({18: full}, previous, [])
    assert (len(full.active()), len(full.squad())) == (54, 17)                             # a full squad has no elevated man on the 53


def test_the_transactions_page_names_the_elevations_and_a_promoted_man_never_goes_back():
    team = team_of(51, 15, [RF.Man("S", "30", "Taylor Rapp"), RF.Man("DB", "37", "Sean Fresch Jr."), RF.Man("RB", "25", "Cody Schrader"),
                            RF.Man("WR", "13", "Pat Bryant")])
    previous = {N.name_key(n): (9, "PS", "x", n) for n in ("Taylor Rapp", "Sean Fresch Jr.", "Cody Schrader")}
    previous[N.name_key("Pat Bryant")] = (9, "IR", "WR", "Pat Bryant")
    moves = {9: N.newest_moves(page("Promoted S Taylor Rapp to active roster.", "Elevated RB Cody Schrader to active roster.",
                                    "Elevated DB Sean Fresch Jr. to active roster.", "Activated WR Pat Bryant from injured reserve."),
                               ["Taylor Rapp", "Sean Fresch Jr.", "Cody Schrader", "Pat Bryant"])}
    notes = []
    N.return_elevations({9: team}, previous, notes, moves)
    assert sorted(m.name for m in team.squad() if not m.name.startswith("Squad")) == ["Cody Schrader", "Sean Fresch Jr."]
    assert {m.name for m in team.active()} >= {"Taylor Rapp", "Pat Bryant"} and len(team.active()) == 53
    assert all("transactions" in n for n in notes)
    # a man of the previous squad whom the page says was promoted stays on the 53, though the team is over and the squad has room
    lions = team_of(53, 15, [RF.Man("CB", "38", "Nick Whiteside")])
    N.return_elevations({18: lions}, {N.name_key("Nick Whiteside"): (18, "PS", "CB", "Nick Whiteside")}, [],
                        {18: N.newest_moves(page("The Detroit Lions sign CB Nick Whiteside to the active roster from the practice squad."),
                                            ["Nick Whiteside"])})
    assert man_named(lions, "Nick Whiteside").status == "" and len(lions.active()) == 54
    # a man of no team before goes back only when the page says he was signed to the squad (a free agent signed to the 53 looks the same)
    niners = team_of(53, 16, [RF.Man("WR", "86", "KhaDarel Hodge")])
    N.return_elevations({26: niners}, {}, [])
    assert len(niners.active()) == 54
    N.return_elevations({26: niners}, {}, [], {26: N.newest_moves(page("The 49ers Sign WR KhaDarel Hodge to Practice Squad"), ["KhaDarel Hodge"])})
    assert man_named(niners, "KhaDarel Hodge").status == "PS" and len(niners.active()) == 53


def man_named(team, name):
    return next(m for m in team.men if m.name == name)


def test_a_page_a_day_behind_is_fitted_by_its_transactions():
    # the Commanders of 2026-11-09: 18 on the squad page, one of them released
    team = team_of(52, 17, [RF.Man("LB", "57", "Austin Keys", "PS")])
    base = team_of(52, 17, [RF.Man("LB", "57", "Austin Keys", "PS")])
    notes = []
    N.fit_limits(24, team, base, N.newest_moves(page("Released LB Austin Keys."), ["Austin Keys"]), notes)
    assert len(team.squad()) == 17 and "Austin Keys" not in {m.name for m in team.men} and "released" in notes[0]
    # the Lions: a man listed active whose newest move put him on injured reserve stays on it
    lions = team_of(53, 16, [RF.Man("SS", "12", "Thomas Harper")])
    base = team_of(53, 16, [RF.Man("SS", "12", "Thomas Harper", "IR")])
    N.fit_limits(18, lions, base, N.newest_moves(page("The Detroit Lions place S Thomas Harper on Reserve/Injured."), ["Thomas Harper"]), [])
    assert man_named(lions, "Thomas Harper").status == "IR" and len(lions.active()) == 53
    # no transactions: the man new to an over-full squad with no number yet waits for the next update
    squad = team_of(53, 17, [RF.Man("DT", "-", "Daniel Ekuale", "PS")])
    N.fit_limits(24, squad, team_of(53, 17), {}, [])
    assert len(squad.squad()) == 17 and "Daniel Ekuale" not in {m.name for m in squad.men}


# ----- a whole read: no team kept for a page a day behind -----

class NFLWithMoves(RL.NFL):
    def __init__(self, teams, moves: dict, **kw):
        super().__init__(teams, **kw)
        self.moves = moves

    def __call__(self, url):
        if url.endswith("/team/transactions/"):
            self.asked.append(url)
            t = self.hosts.get(url.split("/")[2])
            return (200, self.moves[t]) if t in self.moves else (404, b"")
        return super().__call__(url)


def test_a_league_read_the_day_after_a_game_keeps_no_team(folder):
    teams = RL.shipped_teams()
    # T18: two men of its squad on the page's 53 (one elevated, one signed), so 54 active
    lions = teams[18]
    while len(lions.active()) > 52:                                          # a receiver released (never the only snapper or kicker)
        cut = [m for m in lions.active() if m.pos == "WR"][-1]
        lions.men.remove(cut)
        for role in RF.ROLES:
            lions.roles[role] = [n for n in lions.roles[role] if n != cut.name]
    up = [m for m in lions.squad()][:2]
    for m in up:
        m.status = ""
    # T24: a released man still on the squad page, so 18 there
    commanders = teams[24]
    while len(commanders.squad()) < 18:
        commanders.men.append(RF.Man("MIKE", "5%d" % len(commanders.squad()), "Extra Squad%s" % chr(65 + len(commanders.squad())), "PS", 25, 2))
    gone = commanders.squad()[-1]
    # T06 over 53 with no transactions page and no man of its squad: still kept, as before
    crowded = teams[6]
    for n in range(54 - len(crowded.active())):
        crowded.men.insert(0, RF.Man("WR", "1%d" % n, "Extra Receiver%s" % chr(65 + n), "", 24, 1))
    moves = {18: page("Elevated %s %s to active roster." % (up[0].pos, up[0].name), "Signed %s to the active roster from the practice squad." % up[1].name),
             24: page("Released LB %s." % gone.name)}
    net = NFLWithMoves(teams, moves)
    got = RL.download(net, folder)
    assert got.result == F.OK and got.read == 31 and [t for t, _r in got.kept] == [6]
    _v, read, problems = RF.parse(got.rosters)
    assert not problems and not RF.check(read)[0]
    assert RL.man(read[18], up[0].name).status == "PS" and RL.man(read[18], up[1].name).status == ""
    assert gone.name not in {m.name for m in read[24].men} and len(read[24].squad()) == 17
    asked = [u for u in net.asked if u.endswith("/team/transactions/")]
    assert sorted(asked) == sorted("https://%s/team/transactions/" % host for t, _n, host, *_ in N.TEAMS if t in (6, 18, 24))   # only the teams over


# ----- the franchise: the player's own team too -----

def updated_with_own():
    """A league of the player's team 5 and a newer file where a receiver of his has moved to team 6 (on no line of team 5 now) and a new tight end
    joins team 5; the player put his starting quarterback first on his chart."""
    from nfl4.data import customlists as cl
    from nfl4.extras import real_names as R
    league = full_league(team=SR.OWN)
    league.reserves_on = True
    lines = SR.with_version(SR.shipped(), SR.NEW).split("\n")

    def name_of(line):
        return line.split(";")[0].split(" ", 4)[-1]
    at = next(i for i, line in enumerate(lines) if line.startswith("T%02dP" % SR.OWN) and "= WR " in line
              and SR.league_name(league, SR.OWN, name_of(line)) is not None)
    own = SR.league_name(league, SR.OWN, name_of(lines[at]))
    del lines[at]
    lines += ["T06P197 = WR 81 %s" % own.name, "T%02dP198 = TE 89 New Tight End" % SR.OWN]
    problems = {kind: cl.Problems(R.FILE_NAMES[kind]) for kind in R.FILE_NAMES}
    real = R.build([], R.parse_entries("\n".join(lines) + "\n", R.ROSTERS).entries, [], R.defaults(), problems)
    starter = league.chart[SR.OWN - 1]["QB"][0]
    league.depth["order"]["QB"] = [starter]                                    # the player put his quarterback first
    file_kr = RR.file_teams(real)[SR.OWN].roles["KR"]
    returner = next(p for p in RR.members(league, SR.OWN) if p.position in ("WR", "CB", "HB") and p.id != own.id and not file_kr[:1] == [p.name]
                    and p.name in {m.name for m in RR.file_teams(real)[SR.OWN].active()})
    league.depth["order"]["KR"] = [returner.id]                                # and his own kick returner
    return league, real, own, starter


def test_the_third_answer_brings_the_players_own_team_up_and_keeps_his_order(tmp_path, monkeypatch):
    monkeypatch.setattr(F, "folder_of", lambda g: str(tmp_path))
    league, real, own, starter = updated_with_own()
    store = SR.store_of(league)
    asked = []
    text = F.offer(SR.Game(real=real), None, None, store, ask=lambda q, items: asked.append(items) or 2)
    assert asked == [[X.text("NXZ-U15"), X.text("NXZ-U16"), X.text("NXZ-U26")]]
    n = int(text.split(":")[1].split()[0])
    assert text == X.text("NXZ-U27", label=SR.NEW_SPOKEN, n=n) and n > 0
    league = store.league
    assert own.team == 6 and own.status == "active"                           # the file names him on F: he goes there now
    assert league.chart[SR.OWN - 1]["QB"][0] == starter                      # the man he put first stays first
    assert league.chart[SR.OWN - 1]["KR"][0] == league.depth["order"]["KR"][0]    # his kick returner too
    teams = RR.file_teams(real)
    file_men = {m.name for m in teams[SR.OWN].men}
    mine = {p.name for p in league.players.values() if p.team == SR.OWN and p.status in RU.ON_TEAM}
    known = RU.known_real_names(real)
    assert {n for n in mine if n.casefold() in known} <= file_men and "New Tight End" in mine     # every real man of his team is the file's
    assert RR.roster_count(league, SR.OWN) <= D.ROSTER_MAX
    league.check()
    LeagueRecord.from_json(store.files.data["league.sav"].decode("utf-8")).check()
    assert store.files.data.get("league.sav.before-rosters-2026-11-02") is not None


def test_the_second_answer_still_leaves_the_players_team_alone(tmp_path, monkeypatch):
    monkeypatch.setattr(F, "folder_of", lambda g: str(tmp_path))
    league, real, own, _starter = updated_with_own()
    store = SR.store_of(league)
    before = {pid: p.to_list() for pid, p in league.players.items() if p.team == SR.OWN}
    text = F.offer(SR.Game(real=real), None, None, store, ask=lambda q, items: 1)
    assert text.startswith(X.text("NXZ-U17", label=SR.NEW_SPOKEN, n=0).split(":")[0])
    assert {pid: p.to_list() for pid, p in store.league.players.items() if p.team == SR.OWN} == before and own.team == SR.OWN


def test_records_of_a_man_who_left_the_players_team_go_with_him():
    league, real, own, _starter = updated_with_own()
    league.todo.append({"kind": D.TODO_LINEUP, "season": league.season, "week": 1, "state": D.ITEM_NEW, "player": own.id})
    keep = next(p for p in RR.members(league, SR.OWN) if p.id != own.id and p.name in {m.name for m in RR.file_teams(real)[SR.OWN].men})
    league.todo.append({"kind": D.TODO_INJURY, "season": league.season, "week": 2, "state": D.ITEM_NEW, "player": keep.id})
    counts = RU.update(league, real, RU.known_real_names(real), own_too=True)
    assert counts["records_dropped"] >= 1
    assert [item["player"] for item in league.todo if item.get("player") in (own.id, keep.id)] == [keep.id]
    league.check()


def test_a_failed_update_of_all_32_says_so_and_puts_the_league_back(tmp_path, monkeypatch):
    monkeypatch.setattr(F, "folder_of", lambda g: str(tmp_path))
    league, real, _own, _starter = updated_with_own()
    store = SR.store_of(league)
    before = league.to_json()

    def broken(lg, rl, known=frozenset(), own_too=False):
        assert own_too
        raise ValueError("test")
    monkeypatch.setattr(RU, "update", broken)
    assert F.offer(SR.Game(real=real), None, None, store, ask=lambda q, items: 2) == X.text("NXZ-U28")
    assert store.league.to_json() == before.replace('"roster_offer":""', '"roster_offer":"' + SR.NEW + '"')


@pytest.fixture
def folder(tmp_path):
    return tmp_path / "customize"
