"""The salary cap in the Franchise's roster cut (stage 5), in the news and in F9 (nfl4 only, rule 0.13; NFL_FRANCHISE_DESIGN 17 SX.8g, D-066):
the staff lets go of players for a team that would be over the cap, the player is asked about his own team (or the staff does it when the
setting says so), the cap space is told and the team with the most room is news. The rules themselves are test_fr_contracts.py.
"""
import random

import pytest
from drrig import SURNAMES, offseason_rig
from frrig import DOWN, ENTER, ESC, F9, spoken
from test_fr_cut_flow import TEAM, cut_league, run, surplus_groups

from nfl4.extras import nx_texts as X
from nfl4.extras import tuning as T
from nfl4.extras.franchise import contracts as CT
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import draft as DR
from nfl4.extras.franchise import history, news
from nfl4.extras.franchise.league import LeagueRecord, new_league
from nfl4.extras.franchise.news_pools import DEFAULT_POOLS, PLACEHOLDERS
from nfl4.game.rnd import GameRandom


def overspend(league, team, salary=80):
    """The team's veterans earn `salary` on one-year contracts: it is over the cap once the cut is made."""
    for player in league.players.values():
        if player.team == team and player.status == "active" and player.place >= 0:
            player.salary, player.years = salary, 1


def start_of(league):
    """The league as the program reads it, and the table of the rookies waiting."""
    start = LeagueRecord.from_json(league.to_json())
    return start, DR.waiting_by_team(start)


# ----- a team under the cap: the stage tells the space and the news the team with the most room -----

def test_the_stage_tells_the_players_cap_space_after_the_fill_and_the_news_names_the_team_with_the_most_room(tmp_path):
    rig = run(tmp_path, cut_league())
    text = spoken(rig)
    final = rig.fstore.league
    words = rig.fstore.words
    space = X.text("NXA-14", space=words.amount(CT.cap_space(final, TEAM)))
    assert space in text and X.text("NXE-03") in text[text.index(space):]            # said inside the stage, before its wait
    best = CT.cap_ranking(final)[0]
    lines = [e for e in final.news if e["pool"] == "NWK"]
    assert len(lines) == 1 and lines[0]["week"] == D.NEWS_OFFSEASON and lines[0]["told"] == 0
    assert words.team_name(best) in lines[0]["markup"] and words.amount(CT.cap_space(final, best)) in lines[0]["markup"]
    assert any(words.amount(CT.cap_space(final, best)) in t for t in text if t != space)      # and the stage says the same line as words
    assert not [t for t in text if "over the salary cap" in t]                                  # nobody was over the cap


def test_the_news_line_and_the_cap_space_are_written_with_the_stage_before_they_are_spoken(tmp_path):
    rig = run(tmp_path, cut_league())
    after = LeagueRecord.from_json(rig.kept[D.STAGE_NEW_SEASON].decode("utf-8"))
    assert [e["pool"] for e in after.news].count("NWK") == 1 and after.stage_no == D.STAGE_NEW_SEASON and after.draft is None


def test_the_short_offseason_says_the_cap_space_in_one_sentence_and_keeps_the_news_line_unspoken(tmp_path):
    rig = run(tmp_path, cut_league(), short=True)
    text = spoken(rig)
    final = rig.fstore.league
    assert X.text("NXA-14", space=rig.fstore.words.amount(CT.cap_space(final, TEAM))) in text
    assert [e["pool"] for e in final.news].count("NWK") == 1
    assert not [t for t in text if " the most cap space " in t or " most room under the cap " in t or " more than anybody" in t]


def test_every_team_is_under_the_cap_after_the_stage_and_the_dead_money_of_its_releases_is_on_its_books(tmp_path):
    league = cut_league()
    overspend(league, 9)
    start, waiting = start_of(league)
    assert CT.cap_over(start, 9, waiting, DR.plan_cut(start, 9, waiting)) > 0          # the computer team is over the cap after the cut
    staff = {t: DR.staff_cut(start, t, waiting) for t in range(1, D.TEAMS + 1)}
    assert len(staff[9]) > len(DR.plan_cut(start, 9, waiting))                         # and the staff lets go of more players than the cut
    rig = run(tmp_path, league)
    final = rig.fstore.league
    assert all(CT.cap_used(final, t) <= T.FR_CAP for t in range(1, D.TEAMS + 1))
    assert all(p.id not in final.players or final.players[p.id].status in ("released", "practice") for p in staff[9])       # (the dropped ones are gone)
    assert final.dead[8] == sum(CT.dead_money(p) for p in staff[9]) > 0


# ----- the player's team over the cap -----

def test_the_staffs_list_for_a_team_over_the_cap_names_the_cap_and_the_players_let_go_for_it_after_the_cuts_own_list(tmp_path):
    league = cut_league()
    overspend(league, TEAM)
    start, waiting = start_of(league)
    cut = DR.plan_cut(start, TEAM, waiting)
    staff = DR.staff_cut(start, TEAM, waiting)
    assert len(staff) > len(cut) >= 7
    rig = run(tmp_path, league)
    text = spoken(rig)
    words = rig.fstore.words
    at = text.index(" stage 8 of 9. the roster cut. ")
    over = CT.cap_over(start, TEAM, waiting, cut)
    assert over > 0
    expected = [X.text("NXE-50")] + [X.text("NXE-51", player=p.name, position=words.position(p.pos), a=p.age, r=p.rating) for p in cut]
    expected += [X.text("NXE-59", over=words.amount(over))] + [words.released_for_the_cap(p) for p in staff[len(cut):]]
    assert text[at + 1:at + 1 + len(expected)] == expected
    assert text[at + 1 + len(expected)] == " 1. release them "
    final = rig.fstore.league
    assert {p.id for p in final.players.values() if p.status in ("released", "practice") and p.left in (0, 1) and p.team == TEAM} == {p.id for p in staff}
    assert CT.cap_used(final, TEAM) <= T.FR_CAP


def test_a_released_player_of_the_cap_list_is_told_with_what_he_costs():
    league = new_league(GameRandom(random.Random(3)), SURNAMES, "Kim", 5, "x")
    player = league.player_at(5, 0)
    player.salary, player.years = 124, 3
    words = history.Words(lambda t: "")
    line = words.released_for_the_cap(player)
    assert line == " %s, %s, age %d, rating %d, 12.4 million for 3 years. " % (player.name, words.position(player.pos), player.age, player.rating)
    player.salary, player.years = 9, 1
    assert words.contract(player) == "0.9 million for one year" and words.amount(1932) == "193.2 million"
    assert words.amount(120) == "12 million"


def test_choosing_yourself_asks_for_each_release_the_cap_needs_after_the_groups_with_the_staffs_choice_first(tmp_path):
    league = cut_league()
    overspend(league, TEAM)
    start, waiting = start_of(league)
    groups = sum(over for _, over in surplus_groups(start))
    cut = DR.plan_cut(start, TEAM, waiting)
    extras = CT.cap_releases(start, TEAM, waiting, cut)
    assert groups >= 3 and len(extras) >= 2
    rig = run(tmp_path, league, keys=[DOWN, ENTER])                                  # choose yourself, then Enter at every question
    text = spoken(rig)
    words = rig.fstore.words
    asked = [t for t in text if t.endswith(" choose who is released. ") and "salary cap" in t]
    assert len(asked) == len(extras)
    over = CT.cap_over(start, TEAM, waiting, cut)
    assert asked[0] == X.text("NXA-13", over=words.amount(over))
    assert asked[0] != asked[-1] or len(extras) == 1
    for player in extras:
        assert X.text("NXE-55", player=player.name) in text
    final = rig.fstore.league
    assert {p.id for p in final.players.values() if p.status in ("released", "practice") and p.left in (0, 1) and p.team == TEAM} == {p.id for p in cut + extras}
    assert CT.cap_used(final, TEAM) <= T.FR_CAP


def test_choosing_a_player_other_than_the_staffs_first_for_the_cap_releases_him_and_asks_again_until_the_cap_is_met(tmp_path):
    league = cut_league()
    overspend(league, TEAM)
    start, waiting = start_of(league)
    groups = sum(over for _, over in surplus_groups(start))
    cut = DR.plan_cut(start, TEAM, waiting)
    candidates = CT.cap_candidates(start, TEAM, waiting, cut)
    rig = run(tmp_path, league, keys=[DOWN, ENTER] + [ENTER] * groups + [DOWN, ENTER])        # the second of the staff's list at the first cap question
    final = rig.fstore.league
    assert final.players[candidates[1].id].status in ("released", "practice")
    assert X.text("NXE-55", player=candidates[1].name) in spoken(rig)
    assert CT.cap_used(final, TEAM) <= T.FR_CAP
    asked = [t for t in spoken(rig) if t.endswith(" choose who is released. ") and "salary cap" in t]
    own = {p.id for p in final.players.values() if p.status in ("released", "practice") and p.left in (0, 1) and p.team == TEAM}
    assert len(asked) == len(own) - len(cut) >= 1              # one question for each release the cap needed, then no more


def test_with_the_staff_handling_the_cut_nothing_is_asked_and_the_cap_releases_are_counted_in_the_one_sentence(tmp_path):
    league = cut_league()
    overspend(league, TEAM)
    start, waiting = start_of(league)
    staff = DR.staff_cut(start, TEAM, waiting)
    rig = run(tmp_path, league, auto=True)
    text = spoken(rig)
    assert X.text("NXE-56", n=len(staff)) in text
    assert not [t for t in text if "release them" in t or "choose who is released" in t or "over the salary cap" in t]
    assert CT.cap_used(rig.fstore.league, TEAM) <= T.FR_CAP


def test_a_window_closed_at_the_question_of_a_team_over_the_cap_leaves_the_file_as_it_was_and_nobody_is_released(tmp_path):
    """With the setting off the question is asked first: nothing is written and nobody is released before the player answers."""
    league = cut_league()
    overspend(league, TEAM)
    first = run(tmp_path / "first", league, until=lambda r: any(" release them " in t for t in spoken(r)))
    raw = league.to_json().encode("utf-8")
    assert first.files.data["league.sav"] == raw                                      # nothing was written: the player has not answered
    assert not [t for t in spoken(first) if t.endswith(" is released. ")]


def test_a_cap_list_with_no_cut_of_its_own_says_would_release_and_a_team_that_cannot_get_under_the_cap_is_told_so(tmp_path):
    from drrig import draft_league
    league = draft_league(seed=3, team=TEAM, stage_no=D.STAGE_CUT)                   # no draft: the cut has nothing of its own to release
    overspend(league, TEAM)
    start, waiting = start_of(league)
    assert DR.plan_cut(start, TEAM, waiting) == [] and CT.cap_releases(start, TEAM, waiting, []) != []
    rig = run(tmp_path, league)
    text = spoken(rig)
    words = rig.fstore.words
    at = text.index(" stage 8 of 9. the roster cut. ")
    assert text[at + 1] == X.text("NXA-15", over=words.amount(CT.cap_over(start, TEAM, waiting, [])))
    assert not [t for t in text if t == X.text("NXE-50")] and " 1. release them " in text
    # and a team for whom nobody saves money stays over the cap, which the player is told (never a silent failure)
    stuck = draft_league(seed=3, team=TEAM, stage_no=D.STAGE_CUT)
    for player in stuck.players.values():
        if player.team == TEAM and player.status == "active":
            player.salary, player.years = 100, 4
    rig = run(tmp_path / "stuck", stuck)
    final = rig.fstore.league
    over = -CT.cap_space(final, TEAM)
    assert over > 0
    assert X.text("NXA-16", over=rig.fstore.words.amount(over)) in spoken(rig)
    assert not [t for t in spoken(rig) if t.startswith(" your cap space is ")]


def test_an_amount_below_zero_is_told_with_the_minus_text():
    words = history.Words(lambda t: "")
    assert words.amount(-67) == "minus 6.7 million" and words.amount(67) == "6.7 million" and words.amount(0) == "0 million"


# ----- the news -----

def test_the_news_line_names_the_team_with_the_most_cap_space_and_equal_space_goes_to_the_lower_team_number():
    league = new_league(GameRandom(random.Random(3)), SURNAMES, "Kim", 5, "x")
    for player in league.players.values():
        player.salary, player.years = T.FR_MIN_SALARY, 1
    league.dead = [5] * D.TEAMS
    league.dead[11] = league.dead[12] = 0
    event = news.cap_event(league)
    assert (event.pool, event.team, event.n) == ("NWK", 12, T.FR_CAP - 34 * T.FR_MIN_SALARY)
    league.dead[11] = 3
    assert news.cap_event(league).team == 13


def test_the_cap_pool_has_four_default_lines_that_use_only_its_placeholders_and_fill_them():
    assert PLACEHOLDERS["NWK"] == ("<team>", "<cap>", "<coach>") and "NWK" in D.NEWS_POOLS
    assert [r.id for r in DEFAULT_POOLS.lines("NWK")] == ["NWK01", "NWK02", "NWK03", "NWK04"] == list(X.REMARK_POOLS["NWK"])
    league = new_league(GameRandom(random.Random(3)), SURNAMES, "Kim", 5, "x")
    words = history.Words(lambda t: "the Tigers")
    event = news.Event("NWK", team=3, n=124)
    values = news.placeholders(event, league, words)
    assert values == {"<team>": "the Tigers", "<cap>": "12.4 million", "<coach>": "Kim"}
    for remark in DEFAULT_POOLS.lines("NWK"):
        assert "<cap>" in remark.markup and "<team>" in remark.markup


# ----- F9 -----

def test_f9_has_the_salary_cap_item_with_the_players_numbers_his_rank_and_the_32_teams_by_cap_space(tmp_path, monkeypatch):
    from nfl4.extras.franchise import menus
    lists = []
    real = menus._lines_picker

    def picker(speech, keys, title, lines, **kwargs):
        lists.append((title, list(lines)))
        real(speech, keys, title, lines, **kwargs)
    monkeypatch.setattr(menus, "_lines_picker", picker)
    keys = [F9, DOWN, DOWN, DOWN, DOWN, ENTER] + [DOWN] * 5 + [ENTER, ESC, ESC, ESC, ESC]       # F9, Franchise, the salary cap (the 6th item)
    rig = offseason_rig(tmp_path, cut_league(), keys=keys, until=lambda r: bool(lists), picks_told="mine")
    words = rig.fstore.words
    league = rig.fstore.league
    assert lists and lists[0][0] == X.text("NXF-28")
    lines = lists[0][1]
    assert len(lines) == 2 + D.TEAMS
    assert lines[0] == history.cap_text(league, words) and lines[0].startswith(" the salary cap is 193.2 million. your payroll is ")
    ranking = CT.cap_ranking(league)
    assert lines[1] == X.text("NXA-02", k=ranking.index(TEAM) + 1)
    assert lines[2:] == [X.text("NXA-03", k=rank, team=words.team_name(team), space=words.amount(CT.cap_space(league, team)))
                         for rank, team in enumerate(ranking, start=1)]


def test_the_menu_of_the_franchise_lists_the_salary_cap_after_the_team_ratings(tmp_path, monkeypatch):
    from nfl4.game import spoken_menu
    seen = []
    real = spoken_menu.SpokenMenu.__init__

    def spy(self, speech, keys, title, items, *args, **kwargs):
        seen.append((title, [item.label() for item in items]))
        real(self, speech, keys, title, items, *args, **kwargs)
    monkeypatch.setattr(spoken_menu.SpokenMenu, "__init__", spy)
    offseason_rig(tmp_path, cut_league(), keys=[F9, DOWN, DOWN, DOWN, DOWN, ENTER, ESC, ESC, ESC], until=lambda r: any(t == "Franchise" for t, _ in seen))
    franchise = [labels for title, labels in seen if title == "Franchise"][0]
    assert franchise.index("salary cap") == franchise.index("team ratings") + 1 and franchise[-2:] == ["play classic seasons", "get the latest calendar"]      # D-141
