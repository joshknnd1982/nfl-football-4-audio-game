"""NX-D1 (the owner's second report of 2026-10-24, D-147, CLAUDE.md 0.30): every real player at his real position (nfl4 only, rule 0.13).

The owner: "The players must be at the right positions. Go online and find the right depth charts and put players in at the proper positions. A backup
quarterback should not be playing wide receiver." The positions in rosters.txt come from the teams' own depth charts of 2026-10-24; the set-up's places
(the quick game, a season, a new franchise) take only players of their own position; a short group keeps made-up players of that position.
"""
import pytest

from nfl4.extras import real_names as R
from nfl4.extras.franchise import data as D

SECTIONS = (("running_backs", {"RB", "FB"}), ("receivers", {"WR", "TE"}), ("kickers", None))
DEFENSE = ["DL"] * 6 + ["LB"] * 5 + ["CB"] * 4 + ["S"] * 2


@pytest.fixture(autouse=True)
def fresh_defaults():
    R.reset_defaults_cache()
    yield
    R.reset_defaults_cache()


def positions_of(real, team):
    out = {}
    for p in real.active(team) + real.squad(team):                  # SR.4: a squad kicker the view elevates for the game (the Dolphins')
        if p.pos != "RET":
            out.setdefault(real.spoken(p.name), set()).add(p.pos)
    return out


def test_no_team_has_a_player_at_another_position():
    real = R.defaults()
    wrong = []
    for team in range(1, 33):
        pos = positions_of(real, team)
        roster = real.roster(team, None)
        for section, allowed in SECTIONS:
            names = getattr(roster, section)
            if section == "kickers":
                wanted = [{"K"}, {"P"}]
            else:
                wanted = [allowed] * len(names)
            for name, want in zip(names, wanted):
                if name != "player" and not pos.get(name, set()) & want:
                    wrong.append((team, section, name, pos.get(name)))
        for name, want in zip(roster.defense, DEFENSE):               # SR.4 (design 21.4 (4)): a short section takes the nearest family's spare man
            allowed = {want} | set(D.PLACE_COVERS.get(want, ()))         # (a 3-4 team's edge men at linebacker), never a man of another family
            if name != "player" and not pos.get(name, set()) & allowed:
                wrong.append((team, "defense", name, pos.get(name)))
    assert wrong == []


def test_the_bears_backup_quarterback_is_not_a_receiver_any_more():
    real = R.defaults()
    bears = 17
    roster = real.roster(bears, None)
    quarterbacks = {real.spoken(p.name) for p in real.active(bears) if p.pos == "QB"}
    assert not quarterbacks & set(roster.receivers + roster.running_backs + roster.defense + roster.special_teams)
    assert real.roster(bears, None).receivers[0] == "Rome Odunze"


def test_the_depth_chart_decides_a_players_position():
    real = R.defaults()
    pos = positions_of(real, 15)                                           # the Texans: Jalen Pitre is a safety on the page, the nickel back on the chart:
    assert pos["Jalen Pitre"] == {"S"}                                     # SR.2, D-157: the nickel is a role, so he stays a safety (Madden's FS)
    assert positions_of(real, 3)["Kyle Hamilton"] == {"S"}                 # a generic DB row does not move a safety (the Ravens)
    assert positions_of(real, 10)["Khalil Mack"] == {"DL"}                 # an edge rusher of an EDGE row is a lineman (the Chargers)


def test_the_franchise_places_follow_the_same_rule():
    real = R.defaults()
    for team in range(1, 33):
        pos = positions_of(real, team)
        for name, (_heading, _number, position) in zip(real.places(team), D.PLACES):
            if name is None or position in ("RET", "QB"):
                continue
            want = {"RB": {"RB", "FB"}, "WR": {"WR", "TE"}}.get(position, {position} | set(D.PLACE_COVERS.get(position, ())))   # SR.4 covers
            assert pos.get(name, set()) & want, (team, position, name, pos.get(name))


def test_an_older_franchise_with_a_quarterback_at_receiver_gets_a_made_up_receiver_once():
    """A league made before NX-D1 had the Bears' backup quarterback in a receiver's place; opening it renames such a player of another team (the
    ratings stay), keeps a lineman at linebacker (near enough for a league already played) and the player's own team's names."""
    import random
    from drrig import SURNAMES
    from nfl4.extras.franchise import first_names as FN
    from nfl4.extras.franchise.league import fix_real_positions, new_league
    from nfl4.game.rnd import GameRandom
    names = R.defaults()
    league = new_league(GameRandom(random.Random(3)), SURNAMES, "Kim", 4, "20260101-000000", real=names)
    receiver = league.player_at(17, D.PLACES_OF["WR"][5])
    lineman_at_lb = league.player_at(17, D.PLACES_OF["LB"][4])
    own = league.player_at(4, D.PLACES_OF["WR"][5])
    receiver.name, lineman_at_lb.name, own.name = "Tyson Bagent", "Montez Sweat", "Case Keenum"
    rating = receiver.rating
    assert fix_real_positions(league, names) == 1
    assert FN.surname_of(league.league_id, receiver.name) is not None and receiver.rating == rating and receiver.pos == "WR"
    assert lineman_at_lb.name == "Montez Sweat" and own.name == "Case Keenum"
    assert fix_real_positions(league, names) == 0 and fix_real_positions(league, None) == 0
