"""The Franchise's roster cut and fill as stage 5 on the program rig (nfl4 only, rule 0.13): the staff's releases and the player's answers, the
questions of his own choice, the fill, the settings, a window closed at the question and the file the stage writes
(NFL_FRANCHISE_DESIGN 7.6, 3.3 item 4, 16 SX.8d).
"""
from drrig import at_stage, default_until, draft_league, offseason_rig, saved_league
from frrig import DOWN, ENTER, ESC, F9, spoken
from nfl4.extras import nx_texts as X
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import draft as DR
from nfl4.extras.franchise.league import LeagueRecord
from test_fr_draft import mid_draft

TEAM = 5


def cut_league(seed=3, retire=(), picks=224):
    """A league at the start of stage 5: a whole draft made, the rookies waiting; `retire` are places of the player's team that are empty."""
    league, draft = mid_draft(seed=seed, picks=picks, team=TEAM)
    league.stage_no = D.STAGE_CUT
    for index in retire:
        player = league.player_at(TEAM, index)
        player.status, player.place, player.left = "retired", -1, league.season
        league.rosters[TEAM - 1][index] = 0
    return league


def run(tmp_path, league, keys=(), until=None, **kwargs):
    return offseason_rig(tmp_path, league, keys=keys, until=until or default_until, picks_told="mine", **kwargs)


def staffs_releases(league):
    return DR.plan_cut(league, TEAM, DR.waiting_by_team(league))


def player_line(words, player):
    return words.player(player)


# ----- the staff's releases -----

def test_the_stage_names_itself_lists_what_the_staff_would_release_and_asks_release_them_or_choose_yourself(tmp_path):
    league = cut_league()
    rig = run(tmp_path, league)
    text = spoken(rig)
    expected = staffs_releases(rig.start if rig.start.draft else LeagueRecord.from_json(league.to_json()))
    assert len(expected) >= 7
    at = text.index(" stage 8 of 9. the roster cut. ")
    assert text[at + 1] == X.text("NXE-50")
    lines = [X.text("NXE-51", player=p.name, position=rig.fstore.words.position(p.pos), a=p.age, r=p.rating) for p in expected]
    assert text[at + 2:at + 2 + len(lines)] == lines
    assert text[at + 2 + len(lines)] == " 1. release them "


def test_release_them_releases_exactly_those_players_and_the_rookies_who_stay_take_their_places_by_rating(tmp_path):
    league = cut_league()
    expected = {p.id for p in staffs_releases(LeagueRecord.from_json(league.to_json()))}
    rig = run(tmp_path, league)
    final = rig.fstore.league
    released = {p.id for p in final.players.values() if p.status == "released" and p.left == 1}
    assert released == expected
    after_cut = LeagueRecord.from_json(rig.kept[D.STAGE_NEW_SEASON].decode("utf-8"))
    assert after_cut.stage_no == 6 and after_cut.draft is None and after_cut.pick_no == 0
    assert all(pid for roster in after_cut.rosters for pid in roster)
    mine = [p for p in after_cut.players.values() if p.team == TEAM and p.status == "active"]
    assert len(mine) == 34 and any(p.drafted is not None for p in mine) and all(p.place >= 0 for p in mine)
    for position, places in D.PLACES_OF.items():                                       # the best of a group is in its first place
        ratings = [after_cut.player_at(TEAM, i).rating for i in places]
        assert ratings == sorted(ratings, reverse=True)


def test_the_rookies_true_ratings_are_known_from_the_cut_on(tmp_path):
    league = cut_league()
    rig = run(tmp_path, league)
    text = spoken(rig)
    start = LeagueRecord.from_json(league.to_json())
    for rookie in DR.waiting_by_team(start).get(TEAM, []):
        if rookie in staffs_releases(start):
            assert X.text("NXE-51", player=rookie.name, position=rig.fstore.words.position(rookie.pos), a=rookie.age,
                          r=rookie.rating) in text


# ----- the player's own choice -----

def surplus_groups(league):
    waiting = DR.waiting_by_team(league)
    return [(position, over) for position, over in ((p, DR.surplus(league, TEAM, waiting).get(p, 0)) for p in D.ROSTER_ORDER) if over]


def test_choosing_yourself_asks_one_question_for_each_release_of_a_group_over_its_places_with_the_staffs_choices_first(tmp_path):
    league = cut_league()
    start = LeagueRecord.from_json(league.to_json())
    groups = surplus_groups(start)
    assert len(groups) >= 3
    rig = run(tmp_path, league, keys=[DOWN, ENTER])                                    # choose yourself, then Enter at every question
    text = spoken(rig)
    words = rig.fstore.words
    waiting = DR.waiting_by_team(start)
    asked = [t for t in text if t.endswith(" choose who is released. ")]
    expected = []
    for position, over in groups:
        players = DR.group_players(start, TEAM, position, waiting)
        for k in range(over):
            expected.append(X.text("NXE-54", position=words.group(position), n=len(players) - k, m=D.GROUP_SIZE[position]))
    assert asked == expected
    gone = [t for t in text if t.endswith(" is released. ") and not t.endswith(" choose who is released. ")]
    assert len(gone) == sum(over for _, over in groups)
    # Enter on every question releases the worst first: the same players as release them (the floor releases are the staff's too)
    again = run(tmp_path / "again", cut_league())
    key = lambda lg: sorted((p.id, p.status) for p in lg.players.values() if p.team == TEAM)
    assert key(rig.fstore.league) == key(again.fstore.league)


def test_choosing_a_player_other_than_the_staffs_first_releases_him_and_keeps_the_one_the_staff_would_have_released(tmp_path):
    league = cut_league()
    start = LeagueRecord.from_json(league.to_json())
    position, over = surplus_groups(start)[0]
    players = DR.group_players(start, TEAM, position, DR.waiting_by_team(start))
    order = DR.release_order(players)
    rig = run(tmp_path, league, keys=[DOWN, ENTER, DOWN, ENTER])                       # choose yourself; in the first group the second of the list
    final = rig.fstore.league
    assert final.players[order[1].id].status == "released"
    if over == 1:
        assert final.players[order[0].id].status == "active"                           # the staff's first choice stays
    assert X.text("NXE-55", player=order[1].name) in spoken(rig)


def retool(league, rookie, pos, rating):
    """Make a waiting rookie a player of another position and rating, in his record and in the draft's prospect row."""
    for _, index, pid in league.draft["picks"]:
        if pid == rookie.id:
            row = league.draft["class"][index]
            row[0], row[2], row[5] = pos, rating, rating
            rookie.pos, rookie.rating, rookie.peak = pos, rating, rating
            return
    raise AssertionError("not a rookie of this draft")


def test_a_weak_player_of_a_small_group_the_player_was_not_asked_about_still_goes_and_the_fill_replaces_him(tmp_path):
    league = draft_league(seed=3, team=TEAM, stage_no=D.STAGE_CUT)
    for index in D.PLACES_OF["RET"]:
        league.player_at(TEAM, index).rating = 45
    rig = run(tmp_path, league, keys=[DOWN, ENTER])                                      # choose yourself: no group is over its places
    final = rig.fstore.league
    assert all(final.player_at(TEAM, i).rating >= 50 for i in D.PLACES_OF["RET"])
    assert X.text("NXE-57", n=2) in spoken(rig)
    assert not [t for t in spoken(rig) if t.endswith(" choose who is released. ")]


def test_what_the_player_keeps_by_his_own_choice_in_a_group_he_was_asked_about_stays_even_when_it_is_weak(tmp_path):
    """The staff would release the 48 (under the floor of a small group) and the first rookie; the player keeps the 48 and releases all
    seven rookies one by one, so the floor does not take back a player he chose to keep."""
    league = cut_league()
    for rookie in league.waiting_rookies(TEAM):
        retool(league, rookie, "RET", 60 + rookie.id % 7)
        rookie.potential = "low"                             # no youth bonus: every rookie keeps under the 70 (the test is about the floor, not the bonus)
        for _, index, pid in league.draft["picks"]:
            if pid == rookie.id:
                league.draft["class"][index][3] = "low"      # (the class row keeps the prospect's potential too)
    league.player_at(TEAM, D.PLACES_OF["RET"][0]).rating = 48
    league.player_at(TEAM, D.PLACES_OF["RET"][1]).rating = 70
    weak = league.player_at(TEAM, D.PLACES_OF["RET"][0])
    rig = run(tmp_path, league, keys=[DOWN, ENTER] + [DOWN, ENTER] * 7)
    final = rig.fstore.league
    assert final.players[weak.id].status == "active" and final.players[weak.id].team == TEAM
    assert sorted(final.player_at(TEAM, i).rating for i in D.PLACES_OF["RET"]) == [48, 70]
    staff = rig.fstore.words.player(weak)
    text = spoken(rig)
    assert X.text("NXE-51", player=weak.name, position="returner", a=weak.age, r=48) in text         # the staff's list named him
    assert X.text("NXE-55", player=weak.name) not in text


# ----- nothing to release, the setting, the short offseason -----

def test_a_team_with_nobody_to_release_is_told_so_and_is_not_asked(tmp_path):
    league = draft_league(seed=3, team=TEAM, stage_no=D.STAGE_CUT)
    rig = run(tmp_path, league)
    text = spoken(rig)
    at = text.index(" stage 8 of 9. the roster cut. ")
    assert text[at + 1] == X.text("NXE-58") and text[at + 2].startswith(" your cap space is ")          # SX.8g: the cap space follows
    assert X.text("NXE-03") in text[at + 3:at + 5] and not [t for t in text if "release them" in t]


def test_with_the_staff_handling_the_cut_one_sentence_counts_the_releases_and_nothing_is_asked(tmp_path):
    league = cut_league()
    count = len(staffs_releases(LeagueRecord.from_json(league.to_json())))
    rig = run(tmp_path, league, auto=True)
    text = spoken(rig)
    at = text.index(" stage 8 of 9. the roster cut. ")
    assert text[at + 1] == X.text("NXE-56", n=count)
    assert not [t for t in text if t == X.text("NXE-50") or "release them" in t]


def test_the_fill_is_told_for_the_players_team_with_each_new_players_line(tmp_path):
    league = draft_league(seed=3, team=TEAM, stage_no=D.STAGE_CUT)
    for index in (0, 1, 31, 33):                                                          # two backs, the kicker, the quarterback
        player = league.player_at(TEAM, index)
        player.status, player.place, player.left = "retired", -1, league.season
        league.rosters[TEAM - 1][index] = 0
    rig = run(tmp_path, league)
    text = spoken(rig)
    at = text.index(X.text("NXE-57", n=4))
    final = rig.fstore.league
    new = sorted((p for p in final.players.values() if p.team == TEAM and p.id >= league.next_id), key=lambda p: p.place)
    assert [p.pos for p in new] == ["RB", "RB", "K", "QB"] and text[at + 1:at + 5] == [rig.fstore.words.player(p) for p in new]
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
    league = draft_league(seed=3, team=TEAM, stage_no=D.STAGE_CUT)
    for index in (0, 1):
        player = league.player_at(TEAM, index)
        player.status, player.place, player.left = "retired", -1, league.season
        league.rosters[TEAM - 1][index] = 0
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


def test_f9_at_the_cut_question_tells_the_waiting_rookies_by_their_ranges_as_the_draft_did(tmp_path, monkeypatch):
    from nfl4.extras.franchise import menus
    lists = []
    real = menus._lines_picker

    def picker(speech, keys, title, lines, **kwargs):
        lists.append((title, list(lines)))
        real(speech, keys, title, lines, **kwargs)
    monkeypatch.setattr(menus, "_lines_picker", picker)
    league = cut_league()
    start = LeagueRecord.from_json(league.to_json())
    rookie = DR.waiting_by_team(start)[TEAM][0]
    low, high = start.rookie_range(rookie)
    steps = D.ROSTER_ORDER.index(rookie.pos)
    keys = [F9, DOWN, DOWN, DOWN, DOWN, ENTER, DOWN, DOWN, ENTER] + [DOWN] * steps + [ENTER, ESC, ESC, ESC, ESC]
    rig = run(tmp_path, league, keys=keys, until=lambda r: bool(lists))
    words = rig.fstore.words
    expected = words.prospect_line(rookie.name, rookie.pos, low, high, rookie.age, rookie.potential)
    group = [lines for title, lines in lists if expected in lines]
    assert group, lists                                                                    # the cut has not been applied: the range, not the rating
    assert words.player(rookie) not in group[0]
