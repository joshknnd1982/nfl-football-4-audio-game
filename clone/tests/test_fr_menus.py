"""F9's Franchise item: the roster, the league history, the franchise settings and the way between the kinds of season (nfl4 only,
rule 0.13). This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 11, SX.8a. The menus are the F9 classes with their keys as they are (SpokenMenu, ListPicker); the program is the
whole program on the rig of tests/frrig.py. The names of the players are drawn, so the tests read them from the league record. The
window closes (`quit_policy`) when the scripted keys are used up.
"""
from frrig import (COACH_AND_TEAM, DOWN, ENTER, ESC, F9, WANT_FRANCHISE, enter_until, franchise_rig, quit_policy, run_until,
                   spoken)
from nfl4.data import settingsfile
from nfl4.extras import nx_texts as X
from nfl4.game.keys import KEY_LEFT as LEFT
from nfl4.game.keys import KEY_RIGHT as RIGHT
from programrig import preset_season

GAME = [ENTER, ENTER, ENTER]
INTO_FRANCHISE = [F9, DOWN, DOWN, DOWN, DOWN, ENTER]
TWO = [DOWN, DOWN]                     # past the to do list and the news (SX.8e) to the roster


def league(rig):
    return rig.fstore.league


def in_a_franchise(tmp_path, keys):
    """A new franchise, then `keys` at the main menu of week 1."""
    return run_until(franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM + keys, policy=quit_policy))


def a_season_played(tmp_path):
    first = franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM,
                          policy=enter_until(lambda: league(first).season == 2 and league(first).stage == "season"))
    return run_until(first)


def menus_seen(monkeypatch):
    """(title, labels) of every SpokenMenu that opens."""
    from nfl4.game import spoken_menu
    seen = []
    real = spoken_menu.SpokenMenu.__init__

    def spy(self, speech, keys, title, items, *args, **kwargs):
        seen.append((title, [item.label() for item in items]))
        real(self, speech, keys, title, items, *args, **kwargs)
    monkeypatch.setattr(spoken_menu.SpokenMenu, "__init__", spy)
    return seen


def test_while_the_franchise_is_in_use_its_menu_has_the_to_do_list_the_news_the_roster_the_history_the_ratings_the_settings_and_the_way_to_classic(tmp_path, monkeypatch):
    seen = menus_seen(monkeypatch)
    in_a_franchise(tmp_path, INTO_FRANCHISE)
    assert ("Franchise", ["to do list", "news", "your roster", "league history", "team ratings", "salary cap",
                          "free agents", "trades", "injury report", "franchise settings", "play classic seasons"]) in seen       # injury report since SX.8k
    assert [labels for title, labels in seen if title == "Added functions"][0][3:] == ["Rules.", "Franchise", "About NFL Football 4."]


def test_the_roster_has_the_ten_groups_with_their_counts(tmp_path, monkeypatch):
    seen = menus_seen(monkeypatch)
    in_a_franchise(tmp_path, INTO_FRANCHISE + TWO + [ENTER])
    roster = [labels for title, labels in seen if title == "your roster"][0]
    assert roster == [" quarterback: 1 ", " running backs: 6 ", " receivers: 6 ", " defensive linemen: 6 ", " linebackers: 5 ",
                      " cornerbacks: 4 ", " safeties: 2 ", " returners: 2 ", " kicker: 1 ", " punter: 1 "]


def test_a_group_lists_its_players_by_name_position_rating_age_and_potential(tmp_path):
    rig = in_a_franchise(tmp_path, INTO_FRANCHISE + TWO + [ENTER, DOWN, DOWN, ENTER, DOWN])      # roster, receivers, the second player
    text = spoken(rig)
    receivers = league(rig).group_of(1, "WR")
    for player in receivers[:2]:
        assert any(" %s, receiver, rating %d, age %d, %s potential, " % (player.name, player.rating, player.age, player.potential) in t
                   and " million for " in t for t in text)               # SX.8b: the ratings are spoken (NXL-31); SX.8g: and the contract (NXL-33)


def test_the_history_menu_says_nothing_yet_before_the_first_season_ends(tmp_path):
    rig = in_a_franchise(tmp_path, INTO_FRANCHISE + TWO + [DOWN, ENTER, ENTER, DOWN, ENTER])            # history, champions, then your record
    text = spoken(rig)
    assert text.count(" nothing yet. ") == 2


def test_the_history_menu_after_a_season_lists_the_champion_the_record_and_the_seasons(tmp_path):
    first = a_season_played(tmp_path / "one")
    keys = INTO_FRANCHISE + TWO + [DOWN, ENTER, ENTER, ESC, DOWN, ENTER, ENTER, ESC, DOWN, ENTER, ENTER, ESC, DOWN, ENTER, ENTER, ESC]
    second = run_until(franchise_rig(tmp_path / "two", keys, files=first.files, kind="franchise", policy=quit_policy))
    text = spoken(second)
    entry = league(second).history[0]
    champion = second.game.league.team((entry["champion"] - 1) // 4 + 1, (entry["champion"] - 1) % 4 + 1)
    assert any(" season 1: the %s over the " % champion in t for t in text)
    assert any(" seasons: 1. wins: " in t for t in text)
    assert any(" season 1: you were " in t for t in text)
    assert any(" most wins in a season: the " in t for t in text)


def test_the_franchise_settings_change_the_offseason_with_left_right_and_enter_and_are_kept(tmp_path):
    rig = in_a_franchise(tmp_path, INTO_FRANCHISE + TWO + [DOWN] * 7 + [ENTER, DOWN, ENTER])          # settings (the 10th item since SX.8k), the offseason: short
    assert rig.game.options.settings.game.nx_fr_offseason == "short"
    text = spoken(rig)
    assert any(X.text("NXF-24") in t for t in text)
    rig = in_a_franchise(tmp_path / "b", INTO_FRANCHISE + TWO + [DOWN] * 7 + [ENTER, DOWN, RIGHT, LEFT, ENTER])
    assert rig.game.options.settings.game.nx_fr_offseason == "short"                           # Right, Left and Enter: short, full, short
    assert "nx_fr_offseason = short" in settingsfile.render(rig.game.options.settings)


def test_a_waiting_franchise_has_back_to_your_franchise_and_its_history_in_the_menu(tmp_path, monkeypatch):
    first = a_season_played(tmp_path / "one")
    seen = menus_seen(monkeypatch)
    script = [ENTER] + COACH_AND_TEAM + GAME + INTO_FRANCHISE                  # the classic answer, a classic game, F9, Franchise
    run_until(franchise_rig(tmp_path / "two", script, files=first.files, kind="classic", policy=quit_policy))
    assert ("Franchise", ["back to your franchise", "league history"]) in seen


def test_the_history_of_a_waiting_franchise_can_be_heard_from_the_classic_season(tmp_path):
    first = a_season_played(tmp_path / "one")
    script = [ENTER] + COACH_AND_TEAM + INTO_FRANCHISE + [DOWN, ENTER, DOWN, DOWN, ENTER]       # history, season by season
    second = run_until(franchise_rig(tmp_path / "two", script, files=first.files, kind="classic", policy=quit_policy))
    assert second.game.program.mode.kind == "classic"
    assert any(" season 1: you were " in t for t in spoken(second))


def test_starting_a_franchise_is_not_done_when_the_confirming_key_is_not_enter(tmp_path):
    rig = run_until(franchise_rig(tmp_path, INTO_FRANCHISE + [ENTER, ESC, ESC], preset=preset_season(gtp=3), policy=quit_policy))
    assert rig.game.program.mode.kind == "classic" and rig.files.data == {} and not rig.game.program.switch_requested
    assert X.text("NXF-27") in spoken(rig)
