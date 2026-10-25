"""A franchise survives a closed window at any moment of its play-offs, a failed archive, and the other cases the independent review
of SX.8a found (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

The review's finding 1: the record must name a state the program can resume at EVERY write, also in the middle of the play-offs
(the engine changes the week before a round and writes a round's pairings before it changes the week back, and finplay17 writes
whole rounds without the player). The property test below restarts the program from every league.sav the franchise wrote in the
play-offs, for six ways a season can go, and requires the season to end with one entry of 267 games and one champion.
"""
import pytest

from frrig import (COACH_AND_TEAM, DOWN, ENTER, ESC, F9, WANT_FRANCHISE, enter_until, franchise_rig, quit_policy, run_until, spoken)
from nfl4.extras import nx_texts as X
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import history as fr_history
from nfl4.extras.franchise.files import MemoryFiles
from nfl4.extras.franchise.league import LeagueRecord, new_league
from nfl4.extras.franchise.store import FranchiseStore
from programrig import preset_season

QUESTION = X.text("NXF-01", coach="coach")
GAME = [ENTER, ENTER, ENTER]
FRANCHISE_MENU = [F9, DOWN, DOWN, DOWN, DOWN, ENTER]


class RecordingFiles(MemoryFiles):
    """Keeps a copy of league.sav at every successful write."""

    def __init__(self):
        super().__init__()
        self.snapshots = []

    def commit(self, name):
        ok = super().commit(name)
        if ok and name == "league.sav":
            self.snapshots.append(self.data["league.sav"])
        return ok


def league(rig):
    return rig.fstore.league


def season_two(get_rig):
    def predicate():
        rig = get_rig()
        return rig.fstore is not None and rig.fstore.league is not None and rig.fstore.league.season == 2
    return predicate


SCENARIOS = {
    "player out of the play-offs": lambda r: (3, 40),
    "loses the wild card game": lambda r: (28, 10) if r.game.season.gtp < 17 else (3, 40),
    "loses the division game": lambda r: (28, 10) if r.game.season.gtp < 18 else (3, 40),
    "loses the conference championship": lambda r: (28, 10) if r.game.season.gtp < 19 else (3, 40),
    "loses the Super Bowl": lambda r: (28, 10) if r.game.season.gtp < 20 else (3, 24),
    "champion": lambda r: (28, 10),
}


@pytest.mark.parametrize("name", list(SCENARIOS))
def test_a_restart_from_any_league_sav_written_in_the_play_offs_ends_the_season_with_one_entry_of_267_games(tmp_path, monkeypatch, name):
    files = RecordingFiles()
    first = franchise_rig(tmp_path / "one", WANT_FRANCHISE + COACH_AND_TEAM, scores=SCENARIOS[name], files=files,
                          policy=enter_until(lambda: season_two(lambda: first)()))
    run_until(first)
    states = []
    for raw in files.snapshots:
        record = LeagueRecord.from_json(raw.decode("utf-8"))
        if record.stage == "season" and (record.gtp >= 17 or record.gtp == 0):
            if raw not in states:
                states.append(raw)
    assert states, name
    seen = []
    real = fr_history.build_entry
    monkeypatch.setattr(fr_history, "build_entry", lambda record: (seen.append(len(record.results)), real(record))[1])
    for number, raw in enumerate(states):
        again_files = MemoryFiles()
        again_files.data["league.sav"] = raw
        again = franchise_rig(tmp_path / ("again%d" % number), [], files=again_files, kind="franchise", scores=SCENARIOS[name],
                              policy=enter_until(lambda: season_two(lambda: again)()))
        run_until(again)
        entry = league(again).history[0]
        assert len(league(again).history) == 1 and entry["finish"].count(D.FINISH_CHAMPION) == 1, (name, number)
        assert sum(entry["wins"]) == sum(entry["losses"]) == 256, (name, number)
    assert seen == [267] * len(states), (name, seen)


# ----- a new franchise never destroys the old one (finding 2) -----

def test_when_the_old_league_cannot_be_moved_it_stays_and_the_new_one_is_not_written_over_it():
    from test_fr_store import a_league, store_over
    import random
    files = MemoryFiles()
    store = store_over(files, a_league(1))
    store.save()
    store.league.coach = "Second"
    store.save()
    before = dict(files.data)
    real = files.move
    files.move = lambda source, target: False if source == "league.sav" else real(source, target)
    assert not store.create(a_league(2))
    assert store.keep_old and store.take_notices() == [X.text("NXF-32")]
    files.move = real
    assert store.save() is False
    assert files.data == before                                           # nothing was moved, deleted or written
    assert LeagueRecord.from_json(files.data["league.sav"].decode("utf-8")).coach == "Second" and "league.previous.sav" in files.data


# ----- the save is refused for a week that disagrees with its pairings (finding 3) -----

def test_a_record_whose_pairings_do_not_fit_its_week_is_damage():
    from test_fr_league import season_league
    import json
    league_ = season_league()
    league_.gtp, league_.records = 18, [8, 8] * 32
    with pytest.raises(ValueError):
        LeagueRecord.from_json(league_.to_json())                          # week 18 needs 4 games and 4 byes
    league_.pairings = [1, 1, 2, 1] * 4
    with pytest.raises(ValueError):
        LeagueRecord.from_json(league_.to_json())
    league_.byes = [1, 2, 3, 2, 5, 2, 7, 2]
    LeagueRecord.from_json(league_.to_json())
    league_.gtp = 19
    with pytest.raises(ValueError):
        LeagueRecord.from_json(league_.to_json())                          # week 19 needs 2 games
    league_.gtp, league_.pairings = 5, [1, 1, 2, 1]
    league_.records = [2, 2] * 32
    with pytest.raises(ValueError):
        LeagueRecord.from_json(league_.to_json())                          # no play-off games in week 5


# ----- the switches (findings 4, 5, 6, 9, 10) -----

def test_after_a_franchise_was_set_aside_at_the_start_f9_can_still_start_a_new_one(tmp_path):
    script = FRANCHISE_MENU + [ENTER, ENTER, ESC, ESC] + COACH_AND_TEAM
    rig = franchise_rig(tmp_path, script, kind="franchise", preset=preset_season(gtp=3),
                        policy=enter_until(lambda: rig.game.program.mode.kind == "franchise" and rig.game.season.gtp == 1 and
                                           X.text("NXF-08", n=1) in spoken(rig)))
    run_until(rig)
    text = spoken(rig)
    assert X.text("NXF-37") in text and X.text("NXF-07") in text and rig.game.program.mode.kind == "franchise"
    assert rig.game.options.settings.game.nx_season_kind == "franchise"


def test_the_kind_of_season_is_not_changed_until_the_league_exists(tmp_path):
    script = FRANCHISE_MENU + [ENTER, ENTER, ESC, ESC]                     # start a franchise now, confirm, close F9
    rig = franchise_rig(tmp_path, script, preset=preset_season(gtp=3), policy=quit_policy)
    run_until(rig)                                                          # the window closes at the coach's name
    assert " Enter the name of your coach " in spoken(rig)
    assert rig.game.options.settings.game.nx_season_kind == "classic" and rig.files.data == {}


def test_f9_has_no_franchise_item_while_a_new_franchise_is_being_made(tmp_path, monkeypatch):
    from nfl4.game import spoken_menu
    seen = []
    real = spoken_menu.SpokenMenu.__init__

    def spy(self, speech, keys, title, items, *args, **kwargs):
        seen.append([item.label() for item in items])
        real(self, speech, keys, title, items, *args, **kwargs)
    monkeypatch.setattr(spoken_menu.SpokenMenu, "__init__", spy)
    rig = franchise_rig(tmp_path, WANT_FRANCHISE + [F9, ESC], policy=quit_policy)       # the question, franchise, F9 at the coach's name
    run_until(rig)
    assert seen and all("Franchise" not in labels for labels in seen)


def test_a_switch_asked_in_an_offseason_that_a_switch_resumed_is_made_before_anything_is_announced(tmp_path):
    first = franchise_rig(tmp_path / "one", WANT_FRANCHISE + COACH_AND_TEAM, policy=enter_until(lambda: X.text("NXE-03") in spoken(first)))
    run_until(first)
    back = FRANCHISE_MENU + [ENTER, ESC]                                    # F9, Franchise, back to your franchise, close F9
    to_classic = FRANCHISE_MENU + [DOWN] * 12 + [ENTER, ENTER, ESC, ENTER]      # at the wait: play classic seasons (12th since SX.8l), confirm, close, go on   # D-136: practice squad is the 10th item
    second = franchise_rig(tmp_path / "two", back + to_classic, files=first.files, kind="classic", preset=preset_season(gtp=3),
                           policy=quit_policy)
    run_until(second)
    text = spoken(second)
    switch = text.index(X.text("NXF-06"))
    assert second.game.program.mode.kind == "classic"
    # after the confirmation nothing of the classic week is announced while the franchise is still the mode in use
    week_lines = [i for i, line in enumerate(text) if line.startswith(" This is week  3 ")]
    assert week_lines and all(i < text.index(X.text("NXF-05", team=second.game.league.team(1, 1))) or i > switch for i in week_lines)


def test_a_change_of_the_rules_does_not_ask_for_a_switch_when_the_franchise_cannot_be_used(tmp_path):
    first = franchise_rig(tmp_path / "one", WANT_FRANCHISE + COACH_AND_TEAM, policy=enter_until(lambda: season_two(lambda: first)()))
    run_until(first)
    files = MemoryFiles()
    files.data.update(first.files.data)
    files.held.add("league.sav")
    rules = [F9, DOWN, DOWN, DOWN, ENTER, DOWN, ENTER, ESC, ESC, ESC]       # F9, Rules, the second item (time outs) changed, leave
    rig = franchise_rig(tmp_path / "two", rules + [ENTER], files=files, kind="franchise", preset=preset_season(gtp=3), policy=quit_policy)
    run_until(rig)
    assert not rig.game.program.switch_requested
    # no restart of the week (a restart would say the week line a second time AND again after the hand-back): the line is said at the
    # start and once more by the F1 that the F9 menu hands back, which repeats the whole announcement (Q5, D-025 a)
    assert spoken(rig).count(" This is week  3 of Josh Kennedy's N. F. L. football ") == 2


def test_the_rules_item_says_the_franchise_uses_the_nfl_rules_only_while_they_are_on_and_after_a_stop(tmp_path):
    script = WANT_FRANCHISE + COACH_AND_TEAM + [F9, DOWN, DOWN, DOWN, ENTER, ENTER]       # the franchise, F9, Rules, change to Classic
    rig = franchise_rig(tmp_path, script, policy=quit_policy)
    run_until(rig)
    text = spoken(rig)
    opening = [t for t in text if t.startswith("Rules. 15 items")][0]     # NX-D3: Depth charts the fourteenth; D-140: Quarterbacks the thirteenth item     # SY.1: Broadcast is the tenth switch, SY.2: Stadium sounds the eleventh, SZ.1: Commentator the twelfth
    assert "Rules: N. F. L. rules. the franchise uses the N. F. L. rules." in opening
    changed = text[text.index(opening) + 1]
    assert "Rules: Classic" in changed and "the franchise uses" not in changed and X.text("NXF-04") in changed


# ----- the classic file footplay.txt is only read (finding 8) -----

def test_naming_a_new_league_reads_footplay_txt_without_repairing_or_copying_it(tmp_path):
    from nfl4.data.files.store import FileProgramStore
    from nfl4.extras.franchise.mode import own_names
    data = tmp_path / "data"
    custom = data / "customize"
    custom.mkdir(parents=True)
    broken = "Running Backs:\r\nAdams\r\nBaker\r\n"
    (custom / "footplay.txt").write_bytes(broken.encode("utf-8"))
    store = FileProgramStore(str(data), str(custom))

    class G:
        program_store = store
    assert own_names(G()) is None
    assert (custom / "footplay.txt").read_bytes() == broken.encode("utf-8")
    assert sorted(p.name for p in custom.iterdir()) == ["footplay.txt"] and store.take_notices() == []
