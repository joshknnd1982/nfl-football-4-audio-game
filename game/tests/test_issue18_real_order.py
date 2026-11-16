"""GitHub issue 18, Q-100 (D-246): "back to the real team's order" in your depth chart of a franchise (nfl4 only, rule 0.13; CLAUDE.md 0.30, 0.34).
This is inspired by Jim Kitchen.

The question (https://github.com/joshknnd1982/nfl-football-4-audio-game/issues/18#issuecomment-6923386655): should the depth chart have, next to
"back to the staff's order", an item that puts the team back in the real team's order of the newest rosters? The tester: "Either way works. B would
make less confusion"; the owner: "yes, choice b is good."

What is tested: every position of the player's team in the order of the game's rosters file for that team, the men the file does not list after them,
the return roles in the file's order; his own moves cleared and his key players kept; a position where the staff's rule would put a clearly better
backup first keeps the real order as his own order, the others keep none (so a later roster offer's third answer still brings their new order); the
staff's sort afterwards changes nothing; a franchise without the real rosters is told so; the menu's last item says it with the rosters' date and
writes the log line.
"""
import random

import pytest
from drrig import SURNAMES

from nfl4.extras import nx_texts as X
from nfl4.extras import real_names as R
from nfl4.extras import roster_model as RM
from nfl4.extras.franchise import aging
from nfl4.extras.franchise import depth as FD
from nfl4.extras.franchise import real_roster as RR
from nfl4.extras.franchise import roster_update as RU
from nfl4.extras.franchise.league import new_league
from nfl4.game.rnd import GameRandom

BILLS = 5


@pytest.fixture(autouse=True)
def fresh_defaults():
    R.reset_defaults_cache()
    yield
    R.reset_defaults_cache()


def real():
    return R.defaults()


def league():
    return new_league(GameRandom(random.Random(3)), SURNAMES, "Kim", BILLS, "20260101-000000", real=real())


def file_order(record, position):
    """The names of the team's men of `position` in the order of the rosters file (the team's own depth chart), only the men on that chart now."""
    on_chart = {record.players[pid].name.casefold() for pid in record.chart[BILLS - 1][position]}
    out = []
    for man in RR.file_teams(real())[BILLS].men:
        name = man.name.casefold()
        if name in on_chart and name not in out:
            out.append(name)
    return out


def names(record, position):
    return [record.players[pid].name.casefold() for pid in record.chart[BILLS - 1][position]]


def test_every_position_goes_back_to_the_real_teams_order_and_the_key_players_stay():
    record = league()
    chart = record.chart[BILLS - 1]
    moved = []
    for position in ("QB", "HB", "WR", "LT", "CB", "K"):
        if len(chart[position]) >= 2:
            RR.move_in_chart(record, position, chart[position][-1], 0)           # the player moves the last man to the top
            moved.append(position)
    assert len(moved) >= 4 and record.depth["order"]
    receiver = chart["WR"][2]
    FD.set_key(record, "redzone", "receiver", receiver)
    counts = FD.real_order(record, real())
    assert counts is not None and counts["listed"] > 40
    assert set(moved) <= set(counts["starters_changed"])
    for position in RM.MADDEN:
        listed = file_order(record, position)
        assert names(record, position)[:len(listed)] == listed, position
    for role in RM.ROLES:
        wanted = [n.casefold() for n in RR.file_teams(real())[BILLS].roles.get(role, ())]
        got = [record.players[pid].name.casefold() for pid in record.chart[BILLS - 1][role]]
        on = [n for n in wanted if n in got]
        assert got[:len(on)] == [n for k, n in enumerate(on) if n not in on[:k]], role
    assert record.depth["key"] == {"redzone": {"receiver": receiver}}
    assert set(record.depth) == {"order", "key"}
    whole = lambda value, lo, hi, what: None  # noqa: E731
    FD.check(record, whole)


def test_a_clearly_better_backup_does_not_take_the_real_starters_place():
    record = league()
    qbs = list(record.chart[BILLS - 1]["QB"])
    backup = record.players[qbs[1]]
    backup.rating = record.players[qbs[0]].rating + 20                       # the staff's rule (D-170) would start him
    aging.place_by_rating(record, BILLS)
    assert record.chart[BILLS - 1]["QB"][0] == backup.id
    counts = FD.real_order(record, real())
    assert names(record, "QB")[0] == file_order(record, "QB")[0] != backup.name.casefold()
    assert "QB" in counts["kept"] and "QB" in record.depth["order"]          # kept as his order: the staff's sort leaves it
    assert all(p in RM.MADDEN for p in counts["kept"])
    untouched = [p for p in RM.MADDEN if p not in counts["kept"]]
    assert untouched and not any(p in record.depth["order"] for p in untouched)   # the others follow the next roster offer
    aging.place_by_rating(record, BILLS)
    assert names(record, "QB")[0] == file_order(record, "QB")[0]


def test_a_franchise_without_the_real_rosters_has_no_real_order():
    record = league()
    before = dict(record.depth)
    assert FD.real_order(record, None) is None
    assert record.depth == before


def test_the_last_item_of_your_depth_chart_says_it_and_logs_it(monkeypatch):
    from test_lineup_sr6 import Keys, Speech, franchise
    from programrig import ENTER
    from nfl4.extras import depth_flow
    from nfl4.game.keys import KEY_END as END
    events = []
    monkeypatch.setattr(depth_flow.debuglog, "event", lambda *a, **k: events.append((a, k)))
    record = league()
    qbs = list(record.chart[BILLS - 1]["QB"])
    RR.move_in_chart(record, "QB", qbs[-1], 0)
    game, store = franchise(record)
    game.franchise_in_use, game.franchise, game.customization = True, (lambda: store), None
    speech = Speech()
    depth_flow.depth_menu(game, speech, Keys(END, ENTER))
    label = RU.spoken_date(RU.version_of(real()))
    assert label and X.text("NXM-D15") in speech.said and X.text("NXM-D16", label=label) in speech.said
    line = [k for a, k in events if a[:2] == ("franchise", "depth_real_order")]
    assert line and line[0]["done"] is True and line[0]["rosters"] == RU.version_of(real()) and "QB" in line[0]["starters_changed"]
    assert names(record, "QB")[0] == file_order(record, "QB")[0] and store.saves == 1


def test_a_franchise_of_the_older_names_is_told_it_has_no_real_order(monkeypatch):
    from test_lineup_sr6 import Keys, Speech, franchise
    from programrig import ENTER
    from nfl4.extras import depth_flow
    from nfl4.game.keys import KEY_END as END
    record = new_league(GameRandom(random.Random(3)), SURNAMES, "Kim", BILLS, "20260101-000000")       # no real rosters
    game, store = franchise(record)
    game.franchise_in_use, game.franchise, game.customization = True, (lambda: store), None
    speech = Speech()
    depth_flow.depth_menu(game, speech, Keys(END, ENTER))
    assert X.text("NXM-D17") in speech.said and store.saves == 0


def test_the_item_is_named_next_to_the_staffs_order():
    assert X.text("NXM-D15") == "back to the real team's order"
    assert "real team's order" in X.text("NXH-79") and "staff's order" in X.text("NXH-79")
