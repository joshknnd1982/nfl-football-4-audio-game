"""Made-up Franchise players have a first and a last name (nfl4 only, rule 0.13; S8.3 round 2, D-131). This is inspired by Jim Kitchen.

The owner (2026-10-23): "free agents must have both first and last names. As of now they only have first names." The league drew a made-up
player's name from the original's surnames only ("Berry"). Now every drawn player (a new league's, the draft class, the undrafted rookies of the
cut, the stand-ins, the free agents of the season) is "First Surname"; the first name comes from a hash, never from a draw, so the league's draws,
ratings and ages are exactly what they were. A league.sav of format 12 or older is migrated once; the player's own team keeps its names.
"""
import json
import logging
import random

import pytest
from drrig import SURNAMES, draft_league
from frrig import COACH_AND_TEAM, ENTER, WANT_FRANCHISE, franchise_rig, quit_policy, run_until, spoken
from test_fr_signings import FREE_AGENTS, quarterback_of

from nfl4.extras.franchise import aging
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import draft as DR
from nfl4.extras.franchise import first_names as FN
from nfl4.extras.franchise import injuries as I
from nfl4.extras.franchise import signings as S
from nfl4.extras.franchise.league import SEASON, LeagueRecord, new_league
from nfl4.game.rnd import GameRandom

LID = "20260101-000000"
TEAM = 5


def league_of(seed=3):
    league = new_league(GameRandom(random.Random(seed)), SURNAMES, "Kim", TEAM, LID)
    league.stage, league.gtp = SEASON, 1
    return league


def made_up(league, name):
    return FN.surname_of(league.league_id, name) is not None


# ----- the names -----

def test_the_first_names_are_one_word_each_and_none_is_twice():
    assert len(FN.FIRST_NAMES) >= 150 and len(set(FN.FIRST_NAMES)) == len(FN.FIRST_NAMES)
    assert all(name.isalpha() and name[0].isupper() and " " not in name for name in FN.FIRST_NAMES)


def test_a_surname_gets_the_same_first_name_every_time_and_splits_back():
    for surname in SURNAMES[:400] + [s for s in SURNAMES if " " in s]:
        full = FN.full_name(LID, surname)
        assert full == FN.full_name(LID, surname) and full.endswith(" " + surname) and full.count(" ") == surname.count(" ") + 1
        assert FN.surname_of(LID, full) == surname and FN.full_name(LID, full) == full          # a full name is not given a second first name
    assert FN.surname_of(LID, "Joe Burrow") in (None, "Burrow") and FN.surname_of(LID, "Berry") is None


def test_every_drawn_player_of_a_new_league_has_two_names_and_every_name_is_unique():
    league = league_of()
    names = [p.name for p in league.players.values()]
    assert len(names) == len(set(names))
    assert all(" " in name for name in names)
    assert sum(made_up(league, name) for name in names) == len(names)                   # no real names in this league: every one is drawn


def test_the_free_agents_of_the_season_have_a_first_and_a_last_name():
    league = league_of()
    S.ensure_pool(league, SURNAMES)
    pool = S.pool(league)
    assert pool and all(made_up(league, p.name) for p in pool)
    names = [p.name for p in league.players.values()]
    assert len(names) == len(set(names))


def test_the_draft_class_the_cut_and_the_stand_ins_have_a_first_and_a_last_name():
    league = draft_league(seed=2)
    prospects = DR.make_class(league, GameRandom(random.Random(7)), SURNAMES)
    assert all(made_up(league, p.name) for p in prospects)
    row = I.make_stand_in(league, 9, "QB", GameRandom(random.Random(8)), SURNAMES)
    assert made_up(league, row[2])
    fresh = league_of()
    for team in (2, 11):
        fresh.rosters[team - 1][D.PLACES_OF["QB"][0]] = 0
    assert aging.fill_places(fresh, GameRandom(random.Random(9)), SURNAMES) == 2
    assert all(made_up(fresh, fresh.player_at(team, D.PLACES_OF["QB"][0]).name) for team in (2, 11))


# ----- the draws do not change -----

@pytest.mark.parametrize("seed", [1, 2, 3])
def test_the_first_names_change_no_draw_rating_or_age(seed, monkeypatch):
    def made(rnd_seed):
        league = league_of(seed)
        S.ensure_pool(league, SURNAMES)
        prospects = DR.make_class(league, GameRandom(random.Random(rnd_seed)), SURNAMES)
        stand_in = I.make_stand_in(league, 9, "QB", GameRandom(random.Random(rnd_seed + 1)), SURNAMES)
        return league, prospects, stand_in

    with_names = made(seed)
    real_full = FN.full_name
    monkeypatch.setattr(FN, "full_name", lambda lid, surname: surname)                   # the program of 0.12.0: bare surnames
    bare = made(seed)
    monkeypatch.setattr(FN, "full_name", real_full)
    (a, ap, asi), (b, bp, bsi) = with_names, bare
    assert sorted(a.players) == sorted(b.players)
    for pid, player in a.players.items():
        other = b.players[pid]
        assert (player.pos, player.rating, player.age, player.potential, player.team, player.status) == (
            other.pos, other.rating, other.age, other.potential, other.team, other.status)
        assert player.name == FN.full_name(LID, other.name)
    assert [(p.pos, p.true, p.age, p.low) for p in ap] == [(p.pos, p.true, p.age, p.low) for p in bp]
    assert [p.name for p in ap] == [FN.full_name(a.league_id, p.name) for p in bp]
    assert asi[2] == FN.full_name(a.league_id, bsi[2]) and asi[3] == bsi[3]


# ----- a league of 0.12.0 (format 12): migrated once, the player's team left -----

def as_format_12(league):
    """The league as 0.12.0 wrote it: bare drawn surnames, format 12."""
    for player in league.players.values():
        surname = FN.surname_of(league.league_id, player.name)
        if surname is not None:
            player.name = surname
    data = json.loads(league.to_json())
    data["format"] = 12
    return json.dumps(data)


def test_a_format_12_league_gets_first_names_once_and_the_players_own_team_keeps_its_names(caplog):
    league = league_of()
    S.ensure_pool(league, SURNAMES)
    own_qb = quarterback_of(league)
    text = as_format_12(league)
    with caplog.at_level(logging.INFO, logger="nfl4.extras"):
        loaded = LeagueRecord.from_json(text)
    assert any("got a first name (D-131)" in r.getMessage() for r in caplog.records)      # rule 0.15: the migration is in the log
    for pid, player in loaded.players.items():
        if player.team == TEAM and player.status == "active":
            assert player.name == league.players[pid].name                              # his own team: as it was (bare here)
        elif player.status == "practice" or pid not in league.players:
            continue                                                                    # D-136: the squads formed at the load
        else:
            assert made_up(loaded, player.name), player.name
    assert " " not in loaded.players[own_qb.id].name or own_qb.name in SURNAMES
    assert all(made_up(loaded, p.name) for p in S.pool(loaded))
    again = LeagueRecord.from_json(loaded.to_json())                                    # format 13 now: nothing more changes
    assert [p.name for p in again.players.values()] == [p.name for p in loaded.players.values()]
    assert json.loads(loaded.to_json())["format"] == D.FORMAT == 15


def test_a_one_word_name_the_player_gave_in_a_format_13_league_is_never_changed():
    league = league_of()
    other = league.player_at(9, D.PLACES_OF["QB"][0])
    other.name = "Bubba"                                                                 # a rename the player typed (F9, Franchise)
    loaded = LeagueRecord.from_json(league.to_json())
    assert loaded.players[other.id].name == "Bubba"


def test_a_format_12_draft_class_gets_first_names():
    league = draft_league(seed=2, stage_no=D.STAGE_DRAFT)
    DR.Draft.create(league, GameRandom(random.Random(5)), SURNAMES)
    data = json.loads(as_format_12(league))
    assert data["draft"]["class"]
    for row in data["draft"]["class"]:
        row[1] = FN.surname_of(league.league_id, row[1]) or row[1]
    loaded = LeagueRecord.from_json(json.dumps(data))
    assert all(made_up(loaded, row[1]) for row in loaded.draft["class"])


def test_a_format_12_stand_in_gets_a_first_name():
    league = league_of()
    league.injuries["stand_ins"].append([9, "QB", "Berry", 40])
    loaded = LeagueRecord.from_json(as_format_12(league))
    assert loaded.injuries["stand_ins"][-1][2] == FN.full_name(loaded.league_id, "Berry")


# ----- what the player hears -----

def test_the_signing_sentence_says_the_free_agents_first_and_last_name(tmp_path):
    rig = franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM + FREE_AGENTS + [ENTER] * 5, policy=quit_policy)
    run_until(rig)
    league = rig.fstore.league
    signed = [t for t in spoken(rig) if t.startswith(" you released ")]
    new = quarterback_of(league)
    assert len(signed) == 1 and made_up(league, new.name) and new.name.split(" ")[0] in FN.FIRST_NAMES
    assert new.name.lower() in signed[0].lower()
