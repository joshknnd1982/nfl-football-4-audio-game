"""The Franchise's roster cut and fill as stage 5 on the program rig (nfl4 only, rule 0.13): the staff's releases and the player's answers, the
questions of his own choice, the fill, the settings, a window closed at the question and the file the stage writes
(NFL_FRANCHISE_DESIGN 7.6, 3.3 item 4, 16 SX.8d; SR.5, D-164, design 21.7 (1): the cut to 53 of the real roster, the fill of a family's minimum).
"""
import random

from drrig import SURNAMES, at_stage, default_until, draft_league, offseason_rig, saved_league
from frrig import DOWN, ENTER, ESC, F9, spoken
from nfl4.extras import nx_texts as X
from nfl4.extras import tuning as T
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import draft as DR
from nfl4.extras.franchise import real_roster as RR
from nfl4.extras.franchise.league import LeagueRecord
from nfl4.game.rnd import GameRandom

TEAM = 5


def cut_league(seed=3, picks=224):
    """A league of full real teams (drrig.full_league) at the start of stage 5: a whole draft made by the computer's rule, the rookies waiting."""
    league = draft_league(seed=seed, team=TEAM, real=True)
    draft = DR.Draft.create(league, GameRandom(random.Random(seed)), SURNAMES)
    for _ in range(picks):
        _, _, who = draft.next_slot()
        draft.make_pick(who, draft.best_for(who))
    league.stage_no = D.STAGE_CUT
    return league


def plain_cut(seed=3):
    """A league of full real teams at stage 5 without a draft: nobody to release (the player's men of a reserve list were let go, so none comes back)."""
    def drop_lists(league):
        for man in league.players.values():
            if man.status == "list" and man.team == TEAM:
                man.status, man.roster_list, man.left = "released", "", league.season
    return draft_league(seed=seed, team=TEAM, stage_no=D.STAGE_CUT, real=True, mutate=drop_lists)


def run(tmp_path, league, keys=(), until=None, **kwargs):
    return offseason_rig(tmp_path, league, keys=keys, until=until or default_until, picks_told="mine", **kwargs)


def at_cut(league):
    """The league as the stage sees it: the men of the real reserve lists back on their rosters (Q-079, real_roster.return_lists)."""
    copy = LeagueRecord.from_json(league.to_json())
    RR.return_lists(copy)
    return copy


def staffs_releases(league):
    league = at_cut(league)
    return DR.plan_cut(league, TEAM, DR.waiting_by_team(league))


def retire(league, men):
    for man in men:
        man.left = league.season
        RR.leave(league, man, "retired")


# ----- the staff's releases -----

def test_the_stage_names_itself_lists_what_the_staff_would_release_and_asks_release_them_or_choose_yourself(tmp_path):
    league = cut_league()
    rig = run(tmp_path, league)
    text = spoken(rig)
    expected = staffs_releases(rig.start if rig.start.draft else LeagueRecord.from_json(league.to_json()))
    assert len(expected) >= 7                                                          # 53 men and seven rookies or more: seven go
    at = text.index(" stage 8 of 9. the roster cut. ")
    assert text[at + 1] == X.text("NXE-50")
    lines = [X.text("NXE-51", player=p.name, position=rig.fstore.words.position_for(p), a=p.age, r=p.rating) for p in expected]  # SR.6: a man is said by his own position
    assert text[at + 2:at + 2 + len(lines)] == lines
    assert text[at + 2 + len(lines)] == " 1. release them "


def test_release_them_releases_exactly_those_players_and_the_rookies_who_stay_join_their_charts_by_rating(tmp_path):
    league = cut_league()
    expected = {p.id for p in staffs_releases(LeagueRecord.from_json(league.to_json()))}
    rig = run(tmp_path, league)
    final = rig.fstore.league
    before = at_cut(league)
    released = {p.id for p in final.players.values() if p.status in ("released", "practice") and p.id in before.players
                and before.players[p.id].status == "active" and before.players[p.id].team == TEAM}
    assert released == expected
    after_cut = LeagueRecord.from_json(rig.kept[D.STAGE_NEW_SEASON].decode("utf-8"))
    assert after_cut.stage_no == 6 and after_cut.draft is None and after_cut.pick_no == 0
    assert all(pid for i, pid in enumerate(after_cut.rosters[TEAM - 1]) if i not in D.BACK_PLACES)
    mine = RR.members(after_cut, TEAM)
    assert len(mine) == 53 and any(p.drafted is not None for p in mine)
    for position, ids in after_cut.chart[TEAM - 1].items():                             # the staff's order: the best of a position first
        if position not in ("KR", "PR"):
            ratings = [after_cut.players[pid].rating for pid in ids]
            assert ratings == sorted(ratings, reverse=True), position


def test_the_rookies_true_ratings_are_known_from_the_cut_on(tmp_path):
    league = cut_league()
    rig = run(tmp_path, league)
    text = spoken(rig)
    start = LeagueRecord.from_json(league.to_json())
    for rookie in DR.waiting_by_team(start).get(TEAM, []):
        if rookie in staffs_releases(start):
            assert X.text("NXE-51", player=rookie.name, position=rig.fstore.words.position_for(rookie), a=rookie.age,  # SR.6: a man is said by his own position
                          r=rookie.rating) in text


# ----- the player's own choice (one question a release, over his whole roster: D-149, SR.5) -----

def test_choosing_yourself_asks_one_question_for_each_release_over_the_roster_with_the_staffs_choices_first(tmp_path):
    league = cut_league()
    start = LeagueRecord.from_json(league.to_json())
    over = len(staffs_releases(start))
    rig = run(tmp_path, league, keys=[DOWN, ENTER])                                    # choose yourself, then Enter at every question
    text = spoken(rig)
    asked = [t for t in text if t.startswith(X.text("NXL-53", n=60, m=53)[:12])]
    seen = at_cut(start)
    sizes = [len(DR.team_candidates(seen, TEAM, DR.waiting_by_team(seen))) - k for k in range(over)]
    assert asked == [X.text("NXL-53", n=n, m=D.ROSTER_MAX) for n in sizes]
    gone = [t for t in text if t.endswith(" is released. ") and not t.endswith(" choose who is released. ")]
    assert len(gone) == over
    # Enter on every question releases the staff's first: the same players as release them
    again = run(tmp_path / "again", cut_league())
    key = lambda lg: sorted((p.id, p.status) for p in lg.players.values() if p.team == TEAM)
    assert key(rig.fstore.league) == key(again.fstore.league)


def test_choosing_a_player_other_than_the_staffs_first_releases_him(tmp_path):
    league = cut_league()
    start = LeagueRecord.from_json(league.to_json())
    order = staffs_releases(start)
    rig = run(tmp_path, league, keys=[DOWN, ENTER, DOWN, ENTER])                       # choose yourself; at the first question the second of the list
    final = rig.fstore.league
    assert final.players[order[1].id].status in ("released", "practice")
    assert X.text("NXE-55", player=order[1].name) in spoken(rig)


def test_a_weak_kicker_the_player_was_not_asked_about_still_goes_and_the_fill_replaces_him(tmp_path):
    league = plain_cut()
    kicker = next(p for p in RR.members(league, TEAM) if p.pos == "K")
    kicker.rating = 45
    rig = run(tmp_path, league, keys=[DOWN, ENTER])                                      # choose yourself: the roster is not over 53
    final = rig.fstore.league
    assert final.players[kicker.id].status in ("released", "practice")
    kickers = [p for p in RR.members(final, TEAM) if p.pos == "K"]
    assert len(kickers) == 1 and kickers[0].rating >= 50 and kickers[0].drafted is None
    assert X.text("NXE-57", n=1) in spoken(rig)
    assert not [t for t in spoken(rig) if t.startswith(X.text("NXL-53", n=60, m=53)[:12])]


# ----- nothing to release, the setting, the short offseason -----

def test_a_team_with_nobody_to_release_is_told_so_and_is_not_asked(tmp_path):
    rig = run(tmp_path, plain_cut())
    text = spoken(rig)
    at = text.index(" stage 8 of 9. the roster cut. ")
    assert text[at + 1] == X.text("NXE-58") and text[at + 2].startswith(" your cap space is ")          # SX.8g: the cap space follows
    assert X.text("NXE-03") in text[at + 3:at + 5] and not [t for t in text if "release them" in t]


def test_with_the_staff_handling_the_cut_one_sentence_counts_the_releases_and_nothing_is_asked(tmp_path):
    league = cut_league()
    count = len(staffs_releases(league)) + sum(len(DR.staff_cut(at_cut(league), TEAM, DR.waiting_by_team(at_cut(league)))) for _ in [0]) * 0
    count = len(DR.staff_cut(at_cut(league), TEAM, DR.waiting_by_team(at_cut(league))))       # the cut's list and the cap's releases
    rig = run(tmp_path, league, auto=True)
    text = spoken(rig)
    at = text.index(" stage 8 of 9. the roster cut. ")
    assert text[at + 1] == X.text("NXE-56", n=count)
    assert not [t for t in text if t == X.text("NXE-50") or "release them" in t]


def test_the_fill_is_told_for_the_players_team_with_each_new_players_line(tmp_path):
    league = plain_cut()
    men = RR.members(league, TEAM)
    backs = [p for p in men if p.pos == "RB"]
    retire(league, backs[:2] + [p for p in men if p.pos in ("K", "QB")])               # one back left of three, no kicker, no quarterback
    rig = run(tmp_path, league)
    text = spoken(rig)
    at = text.index(X.text("NXE-57", n=2 + 1 + 2))
    final = rig.fstore.league
    new = [p for p in final.players.values() if p.team == TEAM and p.id >= league.next_id]
    assert sorted(p.pos for p in new) == ["K", "QB", "QB", "RB", "RB"]
    assert sorted(text[at + 1:at + 6]) == sorted(rig.fstore.words.player(p) for p in new)
    assert all(45 <= p.rating <= 55 for p in new if p.pos == "RB") and all(50 <= p.rating <= 60 for p in new if p.pos != "RB")
    assert all(p.age == 22 and p.drafted is None for p in new)


def test_the_short_offseason_still_asks_the_cut_and_goes_on_without_a_wait(tmp_path):
    rig = run(tmp_path, cut_league(), short=True)
    text = spoken(rig)
    at = text.index(" stage 8 of 9. the roster cut. ")
    after = text[at:text.index(X.text("NXE-60", n=2))]
    assert " 1. release them " in after and X.text("NXE-03") not in after and " stage 9 of 9. the new season. " not in after
    assert rig.fstore.league.season == 2


def test_the_short_offseason_says_the_fill_in_one_sentence_without_the_players(tmp_path):
    league = plain_cut()
    retire(league, [p for p in RR.members(league, TEAM) if p.pos == "RB"][:2])
    rig = run(tmp_path, league, short=True)
    text = spoken(rig)
    at = text.index(X.text("NXE-58"))
    assert text[at + 1] == X.text("NXE-57", n=2) and text[at + 2].startswith(" your cap space is ")   # a sentence, no list, no wait
    assert text[at + 3] == X.text("NXE-60", n=2)


# ----- the file and a window closed at the question -----

def test_a_window_closed_at_the_cut_question_leaves_the_file_unchanged_and_the_cut_is_asked_again(tmp_path):
    league = cut_league()
    first = run(tmp_path / "first", league, until=at_stage(5))
    raw = league.to_json().encode("utf-8")
    assert first.files.data["league.sav"] == raw and not [s for s in first.saves if s[0] == 5]        # nothing was written
    second = run(tmp_path / "second", None, files=first.files)
    text = spoken(second)
    assert " 1. release them " in text and second.fstore.league.season == 2
    assert [stage for stage, *_ in second.saves][0] == D.STAGE_NEW_SEASON                         # the first thing the stage writes is its end


def test_the_stage_writes_the_cut_the_fill_and_the_end_of_the_draft_in_one_save(tmp_path):
    rig = run(tmp_path, cut_league())
    saves = [s for s in rig.saves if s[0] in (5, 6)]
    assert saves[0][:3] == (D.STAGE_NEW_SEASON, 0, -1)                                    # the first write after the question: stage 6, no draft
    after = LeagueRecord.from_json(rig.kept[D.STAGE_NEW_SEASON].decode("utf-8"))
    assert after.draft is None and not after.has_empty_place()
    assert all(RR.roster_count(after, team) <= D.ROSTER_MAX and not RR.short_groups(after, team) for team in range(1, D.TEAMS + 1))


def test_f9_at_the_cut_question_tells_the_waiting_rookies_by_their_ranges_as_the_draft_did(tmp_path):
    # SR.6: F9, your roster is one list by positions (roster_flow.PositionList): the rookies who wait for the cut are its last section (End, then Up to the
    # first), told by their ranges (the group word, as the draft told them), not by their ratings
    from frrig import UP
    from nfl4.game.keys import KEY_END
    league = cut_league()
    start = LeagueRecord.from_json(league.to_json())
    waiting = DR.waiting_by_team(start)[TEAM]
    rookie = waiting[0]
    low, high = start.rookie_range(rookie)
    heading = X.text("NXM-L01", heading=X.text("NXL-85"), n=len(waiting))
    keys = [F9, DOWN, DOWN, DOWN, DOWN, ENTER, DOWN, DOWN, ENTER, KEY_END] + [UP] * (len(waiting) - 1) + [ESC, ESC, ESC]
    expected = None

    def told(rig):
        nonlocal expected
        expected = rig.fstore.words.prospect_line(rookie.name, rookie.pos, low, high, rookie.age, rookie.potential)
        return any(t.startswith(heading) and t.endswith(expected) for t in spoken(rig))
    rig = run(tmp_path, league, keys=keys, until=told)
    assert told(rig)                                                                       # the cut has not been applied: the range, not the rating
    assert "rating" not in expected
