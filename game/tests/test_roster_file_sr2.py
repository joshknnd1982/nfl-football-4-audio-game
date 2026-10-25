"""SR.2 (NX-L1, NX-L2, NX-L8; D-152 to D-156): rosters.txt layout 2, its checks, and the game's loader of it. This is inspired by Jim Kitchen."""
from nfl4.data import customlists as cl
from nfl4.extras import real_names as R
from nfl4.extras import roster_file as RF


def shipped():
    return R.shipped_text(R.ROSTERS)


def test_the_shipped_file_is_format_2_and_passes_every_check():
    version, teams, problems = RF.parse(shipped())
    assert problems == []
    assert version.startswith("season 2026, as of 2026-10-")
    failures, _ = RF.check(teams)
    assert failures == []
    assert RF.render(version, teams) == shipped().replace("\r\n", "\n")      # the file is exactly what the writer makes of it
    for t, team in teams.items():
        assert all(m.pos in RF.MADDEN for m in team.men), t
        assert RF.ACTIVE_MIN <= len(team.active()) <= RF.ACTIVE_MAX, t
        assert len(team.squad()) <= RF.SQUAD_MAX, t
        assert {"QB", "LT", "C", "RT", "DT", "CB", "K", "P", "LS"} <= {m.pos for m in team.active()} | {m.pos for m in team.squad()}, t


def test_a_tight_end_and_a_returner_keep_their_own_positions_and_the_bears_have_their_quarterbacks():
    _, teams, _ = RF.parse(shipped())
    bears = teams[17]
    quarterbacks = [m.name for m in bears.active() if m.pos == "QB"]
    assert len(quarterbacks) >= 2 and quarterbacks[0] == "Caleb Williams"
    assert {m.pos for m in bears.men if m.name == "Colston Loveland"} == {"TE"}
    assert bears.roles["KR"] and bears.roles["PR"]
    for name in bears.roles["KR"] + bears.roles["PR"]:
        assert next(m for m in bears.active() if m.name == name).pos in RF.MADDEN


def test_the_loader_gives_the_engine_the_groups_and_keeps_the_reserve_lists_apart():
    R.reset_defaults_cache()
    real = R.defaults()
    _, teams, _ = RF.parse(shipped())
    lent = 0
    for t in range(1, 33):
        active = [p for p in real.active(t) if p.pos != "RET"]
        squad = [m.name for m in teams[t].squad()]
        elevated = [m.name for m in teams[t].squad() if m.pos in ("K", "P") and not any(a.pos == m.pos for a in teams[t].active())][:1]
        assert [p.name for p in active] == [m.name for m in RF.group_order(teams[t].active())] + elevated, t      # the Dolphins' squad kicker plays
        for p in active:                                                       # each man plays his own group, or a spare edge man a linebacker place
            assert p.pos == RF.GROUP_OF[p.madden] or (p.pos == "LB" and p.madden in ("LEDG", "REDG")), (t, p)
        lent += sum(1 for p in active if p.pos == "LB" and p.madden in ("LEDG", "REDG"))
        assert sum(1 for p in active if p.pos == "LB") >= 5 or sum(1 for p in active if p.pos == "DL") <= 6, t
        assert [p.name for p in real.squad(t)] == [n for n in squad if n not in elevated], t
        assert [p.name for p in real.reserve(t)] == [m.name for m in teams[t].reserves()], t
        names = {p.name for p in real.active(t)} | {p.name for p in real.squad(t)}
        assert not names & {p.name for p in real.reserve(t)}, t                 # a man on injured reserve never plays
        returners = [p.name for p in real.active(t) if p.pos == "RET"]
        assert returners and len(returners) == len(set(returners)), t
        assert set(returners) <= set(teams[t].roles["KR"]) | set(teams[t].roles["PR"]), t
    assert real.quarterback(17) == "Caleb Williams"
    assert lent > 0                                                             # the 3-4 teams (the Vikings among them)
    assert "Zane Gonzalez" in [p.name for p in real.active(6)]                  # the Dolphins' kicker, as SX.11 had him


def test_group_order_takes_every_starter_first():
    men = [RF.Man(p, "-", n) for p, n in (("LEDG", "E1"), ("LEDG", "E2"), ("REDG", "R1"), ("DT", "D1"), ("DT", "D2"), ("DT", "D3"),
                                          ("WR", "W1"), ("WR", "W2"), ("WR", "W3"), ("WR", "W4"))]
    assert [m.name for m in RF.group_order(men)] == ["W1", "W2", "W3", "E1", "R1", "D1", "D2", "W4", "E2", "D3"]


def _league():
    teams = {}
    for t in range(1, 33):
        men = [RF.Man(p, str(i), "Man %d %d" % (t, i)) for i, p in enumerate(
            ["QB", "QB", "HB", "FB", "WR", "WR", "WR", "TE", "LT", "LG", "C", "RG", "RT", "LEDG", "REDG", "DT", "DT", "SAM", "MIKE", "WILL",
             "CB", "CB", "FS", "SS", "K", "P", "LS"] + ["WR"] * 19)]
        men += [RF.Man("WR", "-", "Squad %d %d" % (t, i), "PS") for i in range(16)] + [RF.Man("TE", "85", "Hurt %d" % t, "IR")]
        teams[t] = RF.Team(men=men, roles={"KR": ["Man %d 4" % t], "PR": ["Man %d 5" % t]})
    return teams


def test_the_checks_pass_on_a_good_league_and_fail_on_every_kind_of_damage():
    good = _league()
    assert RF.check(good)[0] == []
    text = RF.render("season 2026, as of 2026-10-25", good)
    assert RF.parse(text)[1].keys() == good.keys() and RF.parse(text)[2] == []

    def broken(change):
        league = _league()
        change(league)
        return RF.check(league)[0]

    assert broken(lambda L: L[3].men.extend(RF.Man("WR", "1", "Extra %d" % i) for i in range(8)))                 # 54 active
    assert broken(lambda L: L[4].men.extend(RF.Man("WR", "-", "More %d" % i, "PS") for i in range(2)))            # 18 on the squad
    assert broken(lambda L: setattr(L[5], "men", [m for m in L[5].men if m.pos != "QB"]))                         # no quarterback
    assert broken(lambda L: setattr(L[5], "men", [m for m in L[5].men if m.pos != "LS"]))                         # no long snapper
    assert broken(lambda L: L[6].men.append(RF.Man("WR", "-", "Man 6 7", "PS")))                                  # one man twice
    assert broken(lambda L: L[7].men.__setitem__(0, RF.Man("RET", "1", "Man 7 0")))                               # RET is not a position
    assert broken(lambda L: L[8].men.__setitem__(0, RF.Man("QB", "100", "Man 8 0")))                              # a number of three digits
    assert broken(lambda L: L[9].roles.__setitem__("KR", ["Squad 9 1"]))                                          # a returner off the active roster
    assert broken(lambda L: L.pop(32))                                                                            # 31 teams
    assert broken(lambda L: L[10].men.__setitem__(0, RF.Man("QB", "1", "A, B")))                                  # a comma in a name


def test_a_squad_kicker_is_a_warning_not_a_failure():
    league = _league()
    league[6].men = [m for m in league[6].men if m.pos != "K"] + [RF.Man("K", "4", "Squad Kicker", "PS")]
    league[6].men.append(RF.Man("WR", "1", "Filler"))
    failures, warnings = RF.check(league)
    assert failures == [] and any("T06 has no kicker" in w for w in warnings)


def test_the_parser_refuses_lines_that_are_not_format_2():
    _, _, problems = RF.parse("VERSION = x\nT01P01 = RET 1 A Man\nT01P02 = QB 1 Good Man\nT01X = what\nT33P01 = QB 1 Nobody\n")
    assert len(problems) == 3


def test_a_players_format_2_lines_replace_the_team_and_old_words_still_read():
    text = "# NFL Football 4 rosters, format 1.\nT02P01 = QB 7 My Quarterback\nT02P02 = HB 22 My Back\nT02P03 = LT 70 My Tackle\nT02P04 = IR WR 11 My Hurt Receiver\nT02KR1 = My Back\n"
    problems = {k: cl.Problems(R.FILE_NAMES[k]) for k in R.FILE_NAMES}
    real = R.apply_kind(R.defaults(), R.ROSTERS, R.parse_entries(text, R.ROSTERS).entries, problems[R.ROSTERS])
    assert problems[R.ROSTERS].count == 0
    assert [(p.pos, p.madden, p.name) for p in real.active(2)] == [("QB", "QB", "My Quarterback"), ("RB", "HB", "My Back"),
                                                                   ("OL", "LT", "My Tackle"), ("RET", "", "My Back")]
    assert [p.name for p in real.reserve(2)] == ["My Hurt Receiver"]
    old = "# NFL Football 4 rosters, format 1.\nT03P01 = QB 1 Old Style\nT03P02 = RB 2 Old Back\nT03P03 = RET 2 Old Back\n"
    real = R.apply_kind(R.defaults(), R.ROSTERS, R.parse_entries(old, R.ROSTERS).entries, problems[R.ROSTERS])
    assert [(p.pos, p.name) for p in real.active(3)] == [("QB", "Old Style"), ("RB", "Old Back"), ("RET", "Old Back")]
    assert real.reserve(3) == [] and problems[R.ROSTERS].count == 0
