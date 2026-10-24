"""SX.11 (NX-N1 to NX-N7, D-098, CLAUDE.md 0.19): the real head coaches and rosters of the 32 teams, nobody types a name (nfl4 only, rule 0.13).

The shipped files (assets/data/coaches.txt, rosters.txt, respellings.txt) are the built-in values; the tests below read them as the program does
(extras/real_names.py), lay the player's files over them (data/customize.py), run the set-up of a game, the coach question and the quarterbacks'
questions on the virtual-clock rig, and make a Franchise league. Classic never reads any of it.
"""
import os
import random

import pytest

from gamerig import Rig
from nfl4.data import customlists as cl
from nfl4.data.customize import COACHES, RESPELLINGS, ROSTERS, Customization
from nfl4.extras import real_names as R
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise.league import new_league, team_index
from nfl4.game.gamestate import GameState
from nfl4.game.names import load_surnames
from nfl4.game.rnd import GameRandom

ENTER, DOWN, UP = 13, 40, 38


class Store:
    def __init__(self):
        self.calls = []

    def write_coach_and_team(self, tn1, tn2, coach):
        self.calls.append(("team", tn1, tn2, coach))

    def write_schedule(self, schedule):
        pass

    def append_quarterback(self, name):
        self.calls.append(("quarterback", name))


def nfl_rig(answers=(), seed=3, real=True):
    rig = Rig(answers, rng=random.Random(seed))
    game = rig.game
    game.options.settings.game.rules = "nfl"
    game.apply_rules_setting()
    game.real_names = R.defaults() if real else None
    rig.store = game.setup_store = Store()
    return rig


def said(rig):
    return [text for text, _, _ in rig.said]


# ----- the built-in values (NX-N2, NX-N3) -----

def test_the_shipped_files_have_a_coach_for_every_team_and_players_for_every_team():
    real = R.defaults()
    assert real is not None and real.version == "season 2026, as of 2026-10-22"
    assert len(real.coaches) == 32 and all(real.coaches)
    assert len(set(real.coaches)) == 32
    assert real.coach(4) == "Mike McCarthy" and real.coach(1) == "Zac Taylor"
    for team in range(1, 33):
        assert real.has_players(team), team
        positions = {p.pos for p in real.rosters[team - 1]}
        assert {"QB", "K", "P", "RET"} <= positions or team == 6, (team, positions)   # the Dolphins' kicker is written too, see below
        assert real.quarterback(team)


def test_every_shipped_name_passes_the_name_rules_and_the_numbers_are_numbers():
    real = R.defaults()
    names = list(real.coaches) + [p.name for roster in real.rosters for p in roster]
    assert len(names) > 1300
    for name in names:
        assert R.name_problem(name) is None, name
    for roster in real.rosters:
        for player in roster:
            assert player.pos in R.POSITIONS and (player.number == "-" or player.number.isdigit())


def test_the_set_up_has_a_real_player_in_every_place_but_the_back_places_the_team_has_no_running_back_for():
    """Tester 2026-10-23 ("wrong position players are still playing at running back"): a back place holds a real running back or fullback,
    else the draw's made-up name ("player" here, with no draw handed in); every other place holds a real player."""
    real = R.defaults()
    fillers = 0
    for team in range(1, 33):
        roster = real.roster(team, None)
        backs = [p.name for p in real.active(team) if p.pos in ("RB", "FB")]                # NX-B2: not the practice squad
        real_backs = [n for n in roster.running_backs if n != "player"]
        assert real_backs == [real.spoken(n) for n in backs][:6], team          # every real back, in depth order, none lost to the returners
        fillers += 6 - len(real_backs)
        others = roster.receivers + roster.defense + roster.special_teams + roster.kickers
        assert "player" not in others, team
        assert len(set(real_backs + others)) == len(real_backs) + len(others), team     # nobody twice
        places = real.places(team)
        assert len(places) == D.PLACE_COUNT and all(places[6:]), team
        assert places[-1] == real.quarterback(team)
        assert [p or "player" for p in places[:33]] == roster.names(), team      # the Franchise's places are the set-up's names in the same order
    assert fillers < 100                                                         # before the fix: 100 of 192 back places held another position


def test_no_back_place_holds_a_player_of_another_position_and_the_draw_fills_the_rest():
    from nfl4.game.setup import Roster
    real = R.defaults()
    positions = {}
    for roster in real.rosters:
        for p in roster:
            positions.setdefault(real.spoken(p.name), set()).add(p.pos)
    drawn = Roster(["Drawn%d" % n for n in range(6)], ["x%d" % n for n in range(6)], ["y%d" % n for n in range(17)], ["z0", "z1"], ["k0", "k1"])
    for team in range(1, 33):
        backs = real.roster(team, drawn).running_backs
        for index, name in enumerate(backs):
            assert name == "Drawn%d" % index or positions[name] & {"RB", "FB"}, (team, name, positions.get(name))


def test_each_group_takes_its_own_positions_first():
    real = R.defaults()
    roster = real.roster(team_index(7, 1), None)          # the Cardinals: T25
    assert roster.kickers == [real.spoken(next(p.name for p in real.rosters[24] if p.pos == "K")),
                              real.spoken(next(p.name for p in real.rosters[24] if p.pos == "P"))]
    lines = real.rosters[24]
    first_wr = real.spoken([p.name for p in lines if p.pos == "WR"][0])
    assert first_wr in roster.receivers or first_wr in roster.special_teams
    assert roster.defense[0] == real.spoken(next(p.name for p in lines if p.pos == "DL"))      # the first defensive lineman starts the defense list


def test_a_short_position_takes_the_players_left_over_and_a_team_with_no_player_for_a_place_keeps_the_drawn_name():
    entries = ["T01P01 = QB 1 Quinn Back", "T01P02 = K 2 Kay Icker", "T01P03 = P 3 Pat Punter"]
    names = real_names_with(roster=entries)
    fallback = R.Roster() if False else None
    from nfl4.game.setup import Roster
    drawn = Roster(["d%d" % n for n in range(6)], ["r%d" % n for n in range(6)], ["f%d" % n for n in range(17)], ["s0", "s1"], ["k0", "k1"])
    roster = names.roster(1, drawn)
    assert roster.kickers == ["Kay Icker", "Pat Punter"]
    assert roster.running_backs == drawn.running_backs and roster.defense == drawn.defense      # no real player: the drawn names stay
    assert names.quarterback(1) == "Quinn Back"
    assert names.places(1)[-1] == "Quinn Back" and names.places(1)[0] is None


def test_the_receivers_are_wide_receivers_and_tight_ends_in_the_order_of_the_depth_chart():
    lines = ["T01P%02d = WR 1 Wide %d" % (n, n) for n in range(1, 6)] + ["T01P%02d = TE 2 Tight %d" % (n, n) for n in range(6, 9)]
    roster = real_names_with(roster=lines + ["T01P09 = QB 1 Quinn Back", "T01P10 = K 2 Kay Icker", "T01P11 = P 3 Pat Punter"]).roster(1, None)
    assert roster.receivers == ["Wide 1", "Wide 2", "Wide 3", "Tight 6", "Wide 4", "Tight 7"]


def real_names_with(roster=(), coaches=(), respell=(), defaults=None):
    problems = {k: cl.Problems(R.FILE_NAMES[k]) for k in R.FILE_NAMES}
    base = defaults or R.RealNames("", ("",) * 32, ((),) * 32, ())
    parsed = lambda lines, kind: cl.parse_list(cl.render_list(R.GAME, kind, (), [tuple(l.split(" = ", 1)) for l in lines]), R.GAME, kind).entries
    return R.build(parsed(coaches, R.COACHES), parsed(roster, R.ROSTERS), parsed(respell, R.RESPELLINGS), base, problems)


# ----- how a name is said (NX-N6) -----

def test_the_respellings_say_a_suffix_as_words_and_only_as_a_whole_word():
    real = R.defaults()
    assert real.spoken("Marvin Mims Jr.") == "Marvin Mims Junior"
    assert real.spoken("Michael Carter II") == "Michael Carter the second"
    assert real.spoken("Ted Hurst III") == "Ted Hurst the third"
    assert real.spoken("Amon-Ra St. Brown") == "Amon-Ra Saint Brown"
    assert real.spoken("Benjamin St-Juste") == "Benjamin Saint Juste"
    assert real.spoken("Ivan Pace Jr.") == "Ivan Pace Junior"
    assert real.spoken("Ivor Vincent") == "Ivor Vincent"                  # II and V inside a word are left alone
    assert real.spoken("Joe Burrow") == "Joe Burrow"


def test_a_players_respelling_replaces_a_shipped_one_and_off_switches_it_off():
    base = R.defaults()
    changed = real_names_with(respell=["R001 = Jr. => Junior Junior", "R003 = off", "R100 = Mac Jones => Mack Jones"], defaults=base)
    assert changed.spoken("A B Jr.") == "A B Junior Junior"
    assert changed.spoken("A B Sr.") == "A B Sr."
    assert changed.spoken("Mac Jones") == "Mack Jones"
    assert changed.spoken("Marvin Mims Jr.") != base.spoken("Marvin Mims Jr.")


# ----- the player's files (NX-N4) -----

def custom(tmp_path):
    return Customization(str(tmp_path), extras=True)


def test_the_player_gets_the_three_files_and_a_missing_one_comes_back(tmp_path):
    c = custom(tmp_path)
    for name in ("coaches.txt", "rosters.txt", "respellings.txt"):
        assert (tmp_path / name).is_file(), name
        assert c.snapshot.statuses[name.split(".")[0]] in (cl.CREATED, cl.OK)
    assert c.snapshot.real_names.version == "season 2026, as of 2026-10-22"
    (tmp_path / "rosters.txt").unlink()
    c.reload()
    assert (tmp_path / "rosters.txt").is_file() and c.snapshot.real_names.has_players(32)


@pytest.mark.parametrize("damage", [b"", b"\x00\x01\x02" * 50, b"hello, this is not a list\n", b"# NFL Football 4 teams, format 1.\nT01 = Bengals\n",
                                    b"# NFL Football 4 rosters, format 9.\nT01P01 = QB 9 Joe Burrow\n"])
def test_a_damaged_file_is_copied_aside_and_made_again_from_the_built_in_names(tmp_path, damage):
    c = custom(tmp_path)
    (tmp_path / "rosters.txt").write_bytes(damage)
    notices = c.reload()
    assert c.snapshot.statuses[ROSTERS] == cl.RESET
    assert any("rosters.txt" in n and "damaged" in n for n in notices)
    assert any(name.startswith("rosters.txt.damaged") for name in os.listdir(tmp_path))
    assert c.snapshot.real_names.has_players(1) and len(c.snapshot.real_names.rosters[0]) > 30
    assert (tmp_path / "rosters.txt").read_text(encoding="utf-8").startswith("# NFL Football 4 rosters, format 1.")


def test_a_bad_line_keeps_the_built_in_value_and_is_counted_once_per_file(tmp_path):
    c = custom(tmp_path)
    text = (tmp_path / "coaches.txt").read_text(encoding="utf-8")
    text = text.replace("T01 = Zac Taylor", "T01 = Zac, Taylor").replace("T02 = Todd Monken", "T40 = Nobody")
    (tmp_path / "coaches.txt").write_text(text, encoding="utf-8")
    notices = c.reload()
    assert c.snapshot.problem_count(COACHES) == 2
    assert any("2 problems found in coaches.txt" in n for n in notices)
    assert c.snapshot.real_names.coach(1) == "Zac Taylor" and c.snapshot.real_names.coach(2) == "Todd Monken"


def test_the_player_changes_a_coach_and_a_new_season_replaces_a_teams_players(tmp_path):
    c = custom(tmp_path)
    coaches = (tmp_path / "coaches.txt").read_text(encoding="utf-8").replace("T04 = Mike McCarthy", "T04 = Brand New Coach")
    coaches = coaches.replace("VERSION = season 2026, as of 2026-10-22", "VERSION = season 2027, as of 2027-09-01")
    (tmp_path / "coaches.txt").write_text(coaches, encoding="utf-8")
    rosters = (tmp_path / "rosters.txt").read_text(encoding="utf-8")
    keep = [line for line in rosters.splitlines() if not line.startswith("T01P")]       # the Bengals' lines are replaced by two new ones
    (tmp_path / "rosters.txt").write_text("\n".join(keep + ["T01P01 = QB 7 New Quarterback", "T01P02 = K 3 New Kicker"]) + "\n", encoding="utf-8")
    c.reload()
    real = c.snapshot.real_names
    assert real.coach(4) == "Brand New Coach" and real.version == "season 2027, as of 2027-09-01"
    assert [p.name for p in real.rosters[0]] == ["New Quarterback", "New Kicker"]            # none of the old Bengals comes back
    assert len(real.rosters[1]) > 30                                                        # the other teams keep their own
    assert real.quarterback(1) == "New Quarterback"


def test_a_file_that_cannot_be_read_keeps_the_names_already_loaded(tmp_path, monkeypatch):
    c = custom(tmp_path)
    before = c.snapshot.real_names
    (tmp_path / "coaches.txt").write_text(c.default_text(COACHES).replace("Zac Taylor", "Zed Tailor"), encoding="utf-8")
    c.reload()
    assert c.snapshot.real_names.coach(1) == "Zed Tailor"
    (tmp_path / "coaches.txt").write_bytes(b"")
    monkeypatch.setattr(cl, "save_damaged_copy", lambda path: None)                        # a copy cannot be made: the file stays as it is
    c.reload()
    assert c.snapshot.statuses[COACHES] == cl.KEPT_DAMAGED
    assert c.snapshot.real_names.coach(1) == "Zed Tailor" and before.coach(1) == "Zac Taylor"      # the names already loaded stay in use


def test_with_the_classic_rules_no_name_file_is_read_made_or_checked(tmp_path):
    c = Customization(str(tmp_path), extras=False)
    assert c.snapshot.real_names is None
    assert not (tmp_path / "rosters.txt").exists() and not (tmp_path / "coaches.txt").exists()
    c.use_extras(True)
    assert (tmp_path / "rosters.txt").is_file() and c.snapshot.real_names is not None
    c.use_extras(False)
    assert c.snapshot.real_names is None


# ----- the set-up of a game (NX-N2, NX-N5, NX-R2) -----

def setup_of(real, own_names=None, opponent_names=None, seed=3, teams=(1, 1, 2, 4)):
    rig = nfl_rig(seed=seed, real=real)
    s = rig.game.season
    s.tn1, s.tn2, s.tn3, s.tn4 = teams
    setup = rig.game.new_game_setup(own_names, opponent_names, real_names=True)
    return rig, setup


def test_the_player_and_the_opponent_are_the_real_teams_and_the_draws_are_the_same_as_without():
    rig_real, real = setup_of(True)
    rig_old, old = setup_of(False)
    assert rig_real.game.rnd.draws == rig_old.game.rnd.draws                    # the set-up draws exactly what it drew with the original's names
    assert real.plays_per_period == old.plays_per_period and real.warnings == old.warnings
    names = R.defaults()
    assert real.rosters[1].kickers[0] == names.roster(team_index(1, 1), None).kickers[0] == "Evan McPherson"
    assert real.rosters[2].kickers[0] == names.roster(team_index(2, 4), None).kickers[0]        # the Patriots' kicker: the opponent's real roster
    assert real.rosters[1].names() != old.rosters[1].names()
    assert real.own_names_drawn                                                  # footplay.txt is written with the real players
    assert real.banter_names == [n for side in (1, 2) for n in (real.rosters[side].running_backs + real.rosters[side].receivers + real.rosters[side].defense)]
    assert len(real.banter_names) == 58


def test_a_footplay_file_the_player_has_is_the_players():
    from nfl4.game.setup import Roster
    mine = Roster(["a%d" % n for n in range(6)], ["b%d" % n for n in range(6)], ["c%d" % n for n in range(17)], ["d0", "d1"], ["e0", "e1"])
    rig, setup = setup_of(True, own_names=mine)
    assert setup.rosters[1].names() == mine.names() and not setup.own_names_drawn
    assert setup.rosters[2].kickers[0] != "e0"                                   # the opponent is still the real team


def test_a_franchise_opponent_is_the_leagues_not_the_real_roster():
    from nfl4.game.setup import Roster
    theirs = Roster(["x%d" % n for n in range(6)], ["y%d" % n for n in range(6)], ["z%d" % n for n in range(17)], ["u0", "u1"], ["v0", "v1"])
    rig, setup = setup_of(True, opponent_names=theirs)
    assert setup.rosters[2].names() == theirs.names()


def test_the_classic_rules_and_a_game_without_the_names_draw_the_original_surnames():
    rig_classic, classic = setup_of(True)
    rig = Rig(random.Random(3) and (), rng=random.Random(3))
    rig.game.real_names = R.defaults()
    s = rig.game.season
    s.tn1, s.tn2, s.tn3, s.tn4 = 1, 1, 2, 4
    plain = rig.game.new_game_setup(real_names=False)                           # pag passes False unless the rules are the N. F. L. rules
    surnames = set(load_surnames())
    assert set(plain.rosters[1].names()) <= surnames and set(plain.rosters[2].names()) <= surnames


def test_pag_asks_for_the_real_names_only_with_the_nfl_rules():
    from nfl4.game.pag import PlayEngine
    rig = nfl_rig()
    assert PlayEngine(rig.game, rig.game.rules).real_names_in_use()
    classic = nfl_rig()
    classic.game.options.settings.game.rules = "classic"
    classic.game.apply_rules_setting()
    assert not PlayEngine(classic.game, classic.game.rules).real_names_in_use()
    none = nfl_rig(real=False)
    assert not PlayEngine(none.game, none.game.rules).real_names_in_use()


# ----- the coach (NX-N1, NX-N7) -----

def test_a_new_player_chooses_the_team_and_keeps_the_real_coach_pressing_only_enter():
    rig = nfl_rig([ENTER, ENTER, ENTER])            # the first team, yes, keep the coach
    rig.game.coach_and_team()
    assert rig.game.season.coach == "Zac Taylor" and (rig.game.season.tn1, rig.game.season.tn2) == (1, 1)
    assert rig.store.calls[-1] == ("team", 1, 1, "Zac Taylor")                 # footbal1.dat holds the real name
    spoken = " ".join(said(rig))
    assert "The head coach of the Bengals is Zac Taylor" in spoken and "Keep Zac Taylor as your coach" in spoken
    assert "Enter the name of your coach" not in spoken                        # the typed prompt is never asked
    assert rig.keys.answers == []


def test_the_coach_of_another_team_is_the_one_offered():
    rig = nfl_rig([DOWN, DOWN, DOWN, ENTER, ENTER, ENTER])        # the fourth team of the first division, the Steelers
    rig.game.coach_and_team()
    assert rig.game.season.coach == "Mike McCarthy" and rig.store.calls[-1] == ("team", 1, 4, "Mike McCarthy")


def test_another_real_coach_is_chosen_from_the_list_of_the_32():
    rig = nfl_rig([DOWN, DOWN, DOWN, ENTER, ENTER, DOWN, ENTER, DOWN, ENTER])   # the Steelers, yes, "choose another", the list starts at the Steelers: Down, Enter
    rig.game.coach_and_team()
    assert rig.game.season.coach == R.defaults().coach(5) and rig.game.season.coach == "Joe Brady"       # the Bills' coach is the one after the Steelers'
    assert rig.store.calls[-1] == ("team", 1, 4, "Joe Brady")
    assert any("Choose your coach" in text for text in said(rig)) and any("Joe Brady is your coach" in text for text in said(rig))
    assert any("Mike McCarthy of the Steelers" in text for text in said(rig))


def test_a_name_can_still_be_typed_and_is_the_originals_prompt():
    rig = nfl_rig([ENTER, ENTER, DOWN, DOWN, ENTER, "k", "i", "m", ENTER, ENTER])       # team 1, yes, "type a name", kim, yes
    rig.game.coach_and_team()
    assert rig.game.season.coach == "kim" and rig.store.calls[-1] == ("team", 1, 1, "kim")
    assert any("Enter the name of your coach" in text for text in said(rig))


def test_classic_and_a_missing_file_ask_for_the_typed_coach_first_as_the_original():
    for real, rules in ((True, "classic"), (False, "nfl")):
        rig = nfl_rig(["k", "i", "m", ENTER, ENTER, ENTER, ENTER], real=real)
        rig.game.options.settings.game.rules = rules
        rig.game.apply_rules_setting()
        rig.game.coach_and_team()
        assert rig.game.season.coach == "kim", (real, rules)
        assert said(rig)[0].strip() == "Enter the name of your coach"


# ----- the quarterbacks (NX-N1, NX-N7) -----

def test_enter_takes_the_real_quarterbacks_and_the_draws_are_the_same():
    answers = [ENTER, ENTER, ENTER, ENTER]                    # no name typed, yes, no name typed, yes
    rig = nfl_rig(answers)
    rig.game.season.tn1, rig.game.season.tn2, rig.game.season.tn3, rig.game.season.tn4 = 1, 1, 2, 4
    state = GameState()
    own, opponent = rig.game.getqbs(state, defaults=("Joe Burrow", "Drake Maye"))
    plain = nfl_rig(answers)
    plain.game.season.tn1, plain.game.season.tn2, plain.game.season.tn3, plain.game.season.tn4 = 1, 1, 2, 4
    got = plain.game.getqbs(GameState())
    assert (own, opponent) == ("Joe Burrow", "Drake Maye")
    assert got[0] not in ("Joe Burrow",) and rig.game.rnd.draws == plain.game.rnd.draws          # same draws, other names
    assert rig.game.pool.available() == plain.game.pool.available() == 1708 - 2              # the two slots are drawn and used up either way
    assert rig.keys.answers == []


def test_typing_a_quarterback_still_works():
    rig = nfl_rig(["a", "b", ENTER, ENTER, ENTER, ENTER], seed=5)
    rig.game.season.tn1, rig.game.season.tn2, rig.game.season.tn3, rig.game.season.tn4 = 1, 1, 2, 4
    own, opponent = rig.game.getqbs(GameState(), defaults=("Joe Burrow", "Drake Maye"))
    assert own == "ab" and opponent == "Drake Maye"


# ----- the Franchise (NX-N5) -----

def make_league(real, seed=1, team=4):
    rnd = GameRandom(random.Random(seed))
    return new_league(rnd, load_surnames(), "Kim", team, "test", None, None, real)


def test_a_new_leagues_players_and_coaches_are_the_real_ones_with_the_same_ratings_ages_and_draws():
    names = R.defaults()
    real, old = make_league(names), make_league(None)
    assert [(p.pos, p.rating, p.age, p.potential, p.team, p.place) for p in real.players.values()] == \
           [(p.pos, p.rating, p.age, p.potential, p.team, p.place) for p in old.players.values()]
    for team in range(1, 33):
        expected = names.places(team)
        got = [real.player_at(team, i).name for i in range(D.PLACE_COUNT)]
        replaced = sum(1 for a, b in zip(expected, got) if a == b)
        assert replaced >= 33 - expected[:6].count(None), (team, replaced)       # a name another team's player has already stays with the first
        assert all(got[i] == expected[i] or expected[i] is None or expected[i] in got for i in range(6))      # a back place: a real back or the drawn name
    assert real.player_at(1, 33).name == "Joe Burrow"
    coaches = [c["name"] for c in real.staff["coaches"]]
    assert coaches[0] == "Zac Taylor" and coaches[1] == "Todd Monken" and coaches[3] == "Kim"       # the player's own team: the player
    assert [c for i, c in enumerate(coaches) if i != 3] == [names.coach(t) for t in range(1, 33) if t != 4]
    assert len({p.name for p in real.players.values()}) == len(real.players)       # unique across the league


def test_the_players_own_footplay_names_win_in_a_new_league():
    from nfl4.game.setup import Roster
    mine = Roster(["a%d" % n for n in range(6)], ["b%d" % n for n in range(6)], ["c%d" % n for n in range(17)], ["d0", "d1"], ["e0", "e1"], "My Quarterback")
    rnd = GameRandom(random.Random(1))
    league = new_league(rnd, load_surnames(), "Kim", 4, "test", mine, None, R.defaults())
    assert [league.player_at(4, i).name for i in range(34)] == mine.names() + ["My Quarterback"]
    assert league.player_at(1, 0).name != "a0" and league.player_at(1, 33).name == "Joe Burrow"


# ----- a whole game (NX-N7) -----

def test_a_whole_game_with_only_enter_has_the_real_players_and_quarterbacks(tmp_path):
    from pagrig import make_rig
    rig = make_rig(tmp_path, fast=True)                            # the Bengals at home against the Jets, every wait answered with Enter
    game = rig.game
    game.options.settings.game.rules = "nfl"
    game.apply_rules_setting()
    game.real_names = R.defaults()
    seen = {}
    real_getqbs = game.getqbs

    def spy(*args, **kwargs):
        seen["names"] = real_getqbs(*args, **kwargs)
        return seen["names"]

    game.getqbs = spy
    written = []
    game.play_game(roster_sink=written.append)
    assert seen["names"] == ("Joe Burrow", "Geno Smith")           # Enter took the real quarterbacks of the Bengals and the Jets
    assert written and written[0].kickers == ["Evan McPherson", "Ryan Rehkow"]
    spoken = " ".join(said(rig))
    assert "Joe Burrow" in spoken or "Geno Smith" in spoken
    assert "Eddy" not in spoken


def test_an_older_franchise_with_real_non_backs_in_running_back_places_gets_made_up_backs_once():
    """Tester 2026-10-23: a league made before the fix put real tight ends and quarterbacks in running back places; opening it renames them (the
    ratings stay), the player's own team keeps its names, and a second pass changes nothing."""
    from nfl4.extras.franchise import first_names as FN
    from nfl4.extras.franchise.league import fix_real_backs
    names = R.defaults()
    league = make_league(names)
    flacco, kelce = league.player_at(9, 4), league.player_at(4, 5)              # team 9's 5th back, the player's own team's 6th
    flacco.name, kelce.name = "Joe Flacco", "Bubba"                              # as the older league had it; his own back, a typed name
    rating = flacco.rating
    assert fix_real_backs(league, names) == 1
    assert FN.surname_of(league.league_id, flacco.name) is not None and flacco.rating == rating and flacco.pos == "RB"
    assert kelce.name == "Bubba"
    assert fix_real_backs(league, names) == 0 and fix_real_backs(league, None) == 0
    assert len({p.name for p in league.players.values()}) == len(league.players)
