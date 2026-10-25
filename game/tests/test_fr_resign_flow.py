"""The Franchise's expiring contracts as stage 5 of 9 on the program rig (nfl4 only, rule 0.13; NFL_FRANCHISE_DESIGN 17 SX.8h, D-067): the other
teams settled by the staff's rule, the player's players asked one at a time (sign, offer less, franchise tag, let go), the staff setting, the
short offseason, a window closed in the middle and the file the stage writes. The rules are test_fr_resign.py.
"""
import copy

import pytest
from drrig import at_stage, draft_league, offseason_rig, saved_league
from frrig import DOWN, ENTER, ESC, F9, spoken

from nfl4.extras import nx_texts as X
from nfl4.extras import tuning as T
from nfl4.extras.franchise import contracts as CT
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import resign
from nfl4.extras.franchise.league import LeagueRecord

TEAM = 5
PLACES = (33, 0, 7)                         # the quarterback, a running back, a receiver
HEADER = " stage 5 of 9. expiring contracts. "



@pytest.fixture(autouse=True)
def cap_alone_decides(monkeypatch):
    """The staff's payroll target (FR_RESIGN_TARGET, SX.8i) is out of the way in these tests, which are about the cap and the talks; it has its own tests.
    SX.8n: so is the personality's rule in the talk (its percent of slack is 0 here; it has its own tests in test_fr_people.py and test_fr_people_flow.py)."""
    monkeypatch.setattr(T, "FR_RESIGN_TARGET", 1.0)
    monkeypatch.setattr(T, "FR_PERSON_TALK", {word: (0, 0, 0) for word in T.FR_PERSON_TALK})
    monkeypatch.setattr(T, "FR_PERSON_STARTER", (0, 0))

def contract_league(seed=3, places=PLACES, wins=8, mutate=None, others=(12, 20)):
    """A league at the start of stage 5 of 9 (the expiring contracts): these places of the player's team have no years left, and `others` of
    every other team. `wins` is every team's record of the season just played (8: content, 12: happy, 3: unhappy). The player's quarterback is
    rated 78, so he is the most valuable of the three."""
    def change(league):
        for index in places:
            league.player_at(TEAM, index).years = 0
        if 33 in places:
            league.player_at(TEAM, 33).rating = 78
        for team in range(1, D.TEAMS + 1):
            if team != TEAM:
                for index in others:
                    league.player_at(team, index).years = 0
        if 12 in others and TEAM != 2:
            league.player_at(2, 12).rating = 41                                         # one player of another team is too weak to be signed again
        if mutate is not None:
            mutate(league)
    return draft_league(seed=seed, team=TEAM, stage_no=D.STAGE_CONTRACTS, wins=[wins] * 32, finish=[D.FINISH_MISSED] * 32, mutate=change)


def run(tmp_path, league, keys=(), until=None, **kwargs):
    return offseason_rig(tmp_path, league, keys=keys, until=until or at_stage(D.STAGE_FREE_AGENCY), picks_told="mine", **kwargs)


def start_of(league):
    return LeagueRecord.from_json(league.to_json())


def asked(league):
    """The player's players in the order the stage asks about them."""
    return resign.expiring(start_of(league), TEAM)


def pick(item):
    """The keys that take the item with this number (1 is the first): Down to it, then Enter."""
    return [DOWN] * (item - 1) + [ENTER]


def question_of(text, player):
    at = next(i for i, t in enumerate(text) if t.startswith(" %s, " % player.name) and "he asks" in t)
    return text[at]


# ----- what the stage says and asks -----

def test_the_stage_names_itself_counts_the_other_teams_and_asks_about_the_first_player_with_his_mood_his_price_and_the_room(tmp_path):
    league = contract_league()
    rig = run(tmp_path, league)
    text = spoken(rig)
    start = start_of(league)
    order = asked(league)
    assert [p.pos for p in order][0] == "QB" and len(order) == 3
    copy_of = start_of(league)
    out = resign.run_teams(copy_of, skip=(TEAM,))
    at = text.index(HEADER)
    assert text[at + 1] == X.text("NXW-41", n=len([p for p in out.gone if p.team != TEAM]))
    assert X.text("NXW-01", coach="Kim", n=3) in text[at:]
    words = rig.fstore.words
    first = order[0]
    asking = resign.asking(first)
    line = X.text("NXW-03", player=first.name, position=words.position(first.pos), a=first.age, r=first.rating,
                  potential=words.potential(first.potential), mood=X.text("NXW-21"), contract=words.contract_of(*asking))
    assert line in text
    after = text[text.index(line):]
    assert after[1] == X.text("NXW-04", room=words.amount(resign.room(start, TEAM)))
    assert " 1. sign him " in after[:4] and text.index(HEADER) < text.index(line)


def test_the_count_of_the_other_teams_is_not_said_when_they_let_nobody_go(tmp_path):
    league = contract_league(others=())
    text = spoken(run(tmp_path, league))
    assert HEADER in text and not any(t.startswith(" the other teams did not sign") for t in text)
    assert X.text("NXW-01", coach="Kim", n=3) in text


def test_one_player_to_ask_is_told_in_the_singular(tmp_path):
    league = contract_league(places=(33,))
    text = spoken(run(tmp_path, league))
    assert X.text("NXW-06", coach="Kim") in text and not any("1 of your players" in t for t in text)


def test_a_player_who_asks_the_minimum_gets_no_offer_for_less_since_nothing_is_lower(tmp_path):
    def young(league):
        league.player_at(TEAM, 0).seasons = 1
    league = contract_league(places=(0,), mutate=young)
    text = spoken(run(tmp_path, league, keys=[DOWN, DOWN, DOWN, ENTER]))                    # round the items: sign him, (tag), let him go
    assert " 1. sign him " in text and not any("offer less" in t for t in text)


def test_the_five_answers_are_sign_offer_less_the_franchise_tag_with_its_price_the_nonexclusive_tag_and_let_him_go(tmp_path):
    league = contract_league()
    rig = run(tmp_path, league, keys=pick(5))                                            # the 5th item of the first question: let him go (SX.8m: 5 answers)
    text = spoken(rig)
    words = rig.fstore.words
    first = asked(league)[0]
    assert " 1. sign him " in text and " 2. offer less " in text
    tag = resign.tag_salary(start_of(league), first)
    assert " 3. %s " % X.text("NXW-A04", contract=words.contract_of(tag, 1)) in text
    from nfl4.extras.franchise import tags
    begun = start_of(league)
    resign.begin(begun, False)                                                               # (the history of salaries the stage keeps first)
    assert " 4. %s " % X.text("NXU-A10", contract=words.contract_of(tags.nonexclusive_salary(begun, first), 1)) in text
    assert " 5. let him go " in text
    assert X.text("NXW-13", player=first.name) in text                                       # and he was let go


# ----- signing -----

def test_enter_at_every_question_signs_each_player_at_his_price_for_the_length_of_his_age(tmp_path):
    league = contract_league()
    rig = run(tmp_path, league)
    final = rig.fstore.league
    words = rig.fstore.words
    text = spoken(rig)
    for player in asked(league):
        now = final.players[player.id]
        assert now.status == "active" and (now.salary, now.years) == resign.asking(player)
        assert X.text("NXW-10", player=player.name, contract=words.contract_of(*resign.asking(player))) in text
    assert X.text("NXW-31", n=3, m=0) in text
    assert final.resign is None and final.stage_no == D.STAGE_FREE_AGENCY


def test_the_signing_is_written_before_it_is_told(tmp_path):
    """The last file written before each line is spoken already holds that player signed, and not yet the next one (B-X53)."""
    league = contract_league()
    rig = run(tmp_path, league, keep=True)
    texts = [t for t, _, _ in rig.said]
    order = asked(league)
    lines = [next(i for i, t in enumerate(texts) if t.startswith(" %s signs, " % player.name)) for player in order]
    assert lines == sorted(lines)

    def file_before(line):
        counts = [(count, raw) for stage, _, _, raw, count in rig.saves if stage == D.STAGE_CONTRACTS and count <= line]
        return LeagueRecord.from_json(counts[-1][1].decode("utf-8"))
    for k, player in enumerate(order):
        assert file_before(lines[k]).players[player.id].years > 0                                # written before it was told
        if k + 1 < len(order):
            assert file_before(lines[k]).players[order[k + 1].id].years == 0                     # and not ahead of the line


def test_the_other_teams_are_settled_by_the_very_code_the_fast_run_uses(tmp_path):
    league = contract_league()
    rig = run(tmp_path, league)
    expected = start_of(league)
    out = resign.run_teams(expected, skip=(TEAM,))
    final = rig.fstore.league
    for player in expected.players.values():
        if player.team != TEAM:
            now = final.players[player.id]
            assert (now.salary, now.years, now.status) == (player.salary, player.years, player.status), player.id
    assert out.signed > 0


# ----- offering less -----

def test_offering_less_to_a_happy_player_signs_him_at_ninety_percent_at_once(tmp_path):
    league = contract_league(wins=12)
    first = asked(league)[0]
    rig = run(tmp_path, league, keys=pick(2))
    final = rig.fstore.league
    salary, years = resign.asking(first)
    assert (final.players[first.id].salary, final.players[first.id].years) == (resign.lower_offer(salary), years)
    assert X.text("NXW-10", player=first.name, contract=rig.fstore.words.contract_of(resign.lower_offer(salary), years)) in spoken(rig)
    assert X.text("NXW-21") not in " ".join(spoken(rig)) and X.text("NXW-20") in " ".join(spoken(rig))


def test_offering_less_to_a_content_player_is_countered_with_the_round_and_the_price_and_he_can_then_be_signed(tmp_path):
    league = contract_league(wins=8)
    first = asked(league)[0]
    salary, years = resign.asking(first)
    talk = resign.Talk.start(first, resign.CONTENT)
    assert talk.offer_less()[0] == resign.COUNTER
    rig = run(tmp_path, league, keys=pick(2) + pick(1))                                   # offer less, then sign at the counter
    final = rig.fstore.league
    words = rig.fstore.words
    assert X.text("NXW-11", player=first.name, contract=words.contract_of(talk.ask, years), round=2, m=3) in spoken(rig)
    assert (final.players[first.id].salary, final.players[first.id].years) == (talk.ask, years) and talk.ask < salary


def test_three_offers_for_less_that_fail_end_the_talk_and_the_player_leaves(tmp_path):
    league = contract_league(wins=8)
    first = asked(league)[0]
    rig = run(tmp_path, league, keys=pick(2) * 3)
    final = rig.fstore.league
    text = spoken(rig)
    assert X.text("NXW-12", player=first.name) in text
    gone = final.players[first.id]
    assert gone.status == "free" and gone.place == -1 and (gone.salary, gone.years) == (0, 0) and final.dead == [0] * D.TEAMS
    rounds = [t for t in text if t.startswith(" %s wants more." % first.name)]
    assert len(rounds) == 2 and " round 2 of 3. " in rounds[0] and " round 3 of 3. " in rounds[1]


def test_an_unhappy_player_is_not_moved_by_an_offer_for_less(tmp_path):
    league = contract_league(wins=3)
    first = asked(league)[0]
    salary, years = resign.asking(first)
    rig = run(tmp_path, league, keys=pick(2) + pick(1))
    final = rig.fstore.league
    text = spoken(rig)
    assert X.text("NXW-11", player=first.name, contract=rig.fstore.words.contract_of(salary, years), round=2, m=3) in text      # the same price again
    assert (final.players[first.id].salary, final.players[first.id].years) == (salary, years)
    assert X.text("NXW-22") in " ".join(text)


# ----- letting him go and the franchise tag -----

def test_let_him_go_makes_him_a_free_agent_with_no_dead_money_and_leaves_his_place_empty_for_the_draft(tmp_path):
    league = contract_league()
    order = asked(league)
    rig = run(tmp_path, league, keys=pick(5) + pick(1) + pick(1))
    final = rig.fstore.league
    gone = final.players[order[0].id]
    assert gone.status == "free" and gone.team == TEAM and gone.left == 1 and (gone.salary, gone.years) == (0, 0)
    assert final.dead == [0] * D.TEAMS
    assert X.text("NXW-13", player=gone.name) in spoken(rig)
    assert X.text("NXW-31", n=2, m=1) in spoken(rig)
    after_stage = LeagueRecord.from_json(rig.kept[D.STAGE_FREE_AGENCY].decode("utf-8"))
    assert after_stage.rosters[TEAM - 1][33] == 0 and after_stage.draft is None and after_stage.stage_no == D.STAGE_FREE_AGENCY      # the quarterback's place waits for the draft


def test_the_franchise_tag_signs_one_year_at_the_tag_price_and_is_offered_once_a_year(tmp_path):
    league = contract_league()
    order = asked(league)
    tag = resign.tag_salary(start_of(league), order[0])
    rig = run(tmp_path, league, keys=pick(3) + [DOWN, DOWN, DOWN, ENTER])                    # the tag, then round the second question's three items
    final = rig.fstore.league
    text = spoken(rig)
    words = rig.fstore.words
    assert (final.players[order[0].id].salary, final.players[order[0].id].years) == (tag, 1)
    assert X.text("NXW-14", player=order[0].name, contract=words.contract_of(tag, 1)) in text
    second = [i for i, t in enumerate(text) if t.startswith(" %s, " % order[1].name) and "he asks" in t][0]
    assert not any("franchise tag" in t for t in text[second:second + 8])                    # the tag is used: no such answer any more
    assert " 3. let him go " in text[second:second + 8]
    assert final.players[order[1].id].years > 0


def test_the_tag_price_is_never_over_the_maximum_and_the_contract_is_one_year_whatever_the_age(tmp_path):
    def rich(league):
        league.player_at(TEAM, 33).salary = T.FR_MAX_SALARY                           # 120 percent of the maximum is over the maximum
        for team in (1, 2, 3):
            league.player_at(team, 33).salary = 250
    league = contract_league(places=(33,), mutate=rich)
    assert resign.tag_salary(start_of(league), asked(league)[0]) == T.FR_MAX_SALARY
    rig = run(tmp_path, league, keys=pick(3))
    player = rig.fstore.league.players[asked(league)[0].id]
    assert (player.salary, player.years) == (T.FR_MAX_SALARY, 1) and player.years <= CT.years_for_age(player.age)


# ----- a young player (exclusive rights) -----

def test_a_young_players_question_says_he_asks_the_minimum_for_one_year_and_enter_signs_him_so(tmp_path):
    def young(league):
        league.player_at(TEAM, 0).seasons = 1
    league = contract_league(places=(0,), mutate=young)
    player = asked(league)[0]
    rig = run(tmp_path, league)
    words = rig.fstore.words
    assert X.text("NXA-11", salary=words.amount(CT.min_salary(1))) == "1 million for one year"           # research B4's table: a player with one season
    assert any(t.startswith(" %s, " % player.name) and " he asks 1 million for one year. " in t for t in spoken(rig))
    final = rig.fstore.league.players[player.id]
    assert (final.salary, final.years, final.status) == (CT.min_salary(1), 1, "active")


# ----- the cap -----

def test_when_nobody_fits_the_stage_says_so_and_offers_only_letting_him_go(tmp_path):
    def poor(league):
        for player in league.active_of(TEAM):
            if player is not None and player.years > 0:
                player.salary = 60                                                           # 31 running contracts of 6.0 million
    league = contract_league(mutate=poor)
    start = start_of(league)
    first = asked(league)[0]
    assert resign.room(start, TEAM) < resign.lower_offer(resign.asking(first)[0])
    rig = run(tmp_path, league, keys=[ENTER] * 3)
    text = spoken(rig)
    words = rig.fstore.words
    assert X.text("NXW-05", room=words.amount(resign.room(start, TEAM))) in text
    at = text.index(X.text("NXW-05", room=words.amount(resign.room(start, TEAM))))
    from nfl4.extras.franchise import people
    assert text[at + 1] == X.text("NXU-P01", trait=X.text(people.TRAIT_TEXT[people.personality(first.id)]))     # SX.8n: his personality after the room
    assert text[at + 2] == " 1. let him go "                                                 # the only answer there is
    assert rig.fstore.league.players[first.id].status == "free"
    after = LeagueRecord.from_json(rig.kept[D.STAGE_FREE_AGENCY].decode("utf-8"))
    assert CT.cap_used(after, TEAM) <= T.FR_CAP


def test_the_room_shrinks_as_the_player_signs_so_the_team_ends_under_the_cap(tmp_path):
    def thin(league):
        for player in league.active_of(TEAM):
            if player is not None and player.years > 0:
                player.salary = 44
    league = contract_league(mutate=thin)
    rig = run(tmp_path, league)                                                              # Enter signs whoever fits, else lets him go
    final = rig.fstore.league
    after = LeagueRecord.from_json(rig.kept[D.STAGE_FREE_AGENCY].decode("utf-8"))
    assert CT.cap_used(after, TEAM) <= T.FR_CAP
    assert all(p.years > 0 for p in after.active_of(TEAM) if p is not None) and final.stage_no >= D.STAGE_FREE_AGENCY


# ----- the staff and the setting -----

def test_with_the_staff_handling_it_nothing_is_asked_and_one_sentence_counts_what_it_did(tmp_path):
    league = contract_league()
    rig = run(tmp_path, league, auto=True)
    text = spoken(rig)
    expected = start_of(league)
    plan = resign.plan_team(expected, TEAM)
    assert X.text("NXW-30", n=len(plan.signed), m=len(plan.gone)) in text
    assert not any(t.endswith(" 1. sign him ") or t == " 1. sign him " or "he asks" in t for t in text)
    final = rig.fstore.league
    for player, salary, years in plan.signed:
        assert (final.players[player.id].salary, final.players[player.id].years) == (salary, years)
    assert all(final.players[p.id].status == "free" for p in plan.gone)


def test_with_the_setting_off_every_player_is_asked_and_nothing_is_decided_for_him(tmp_path):
    def weak(league):
        league.player_at(TEAM, 7).rating = 41                                                # the staff would let him go
    league = contract_league(mutate=weak)
    start = start_of(league)
    assert resign.worth_keeping(start.player_at(TEAM, 0)) and not resign.worth_keeping(start.player_at(TEAM, 7))
    rig = run(tmp_path, league)                                                              # Enter at every question
    text = spoken(rig)
    names = [t for t in text if "he asks" in t]
    assert len(names) == 3 and any(start.player_at(TEAM, 7).name in t for t in names)        # the weak one is asked about too
    assert rig.fstore.league.players[start.player_at(TEAM, 7).id].status == "active"         # and Enter signed him: the player's choice


def test_the_staffs_choice_for_the_players_team_equals_what_the_computer_teams_do_for_theirs(tmp_path):
    league = contract_league(places=(0, 7, 12, 20, 33))
    rig = run(tmp_path, league, auto=True)
    expected = start_of(league)
    resign.run_teams(expected)                                                               # the rule for all 32 teams
    final = rig.fstore.league
    for player in expected.players.values():
        if player.team == TEAM:
            now = final.players[player.id]
            assert (now.salary, now.years, now.status) == (player.salary, player.years, player.status), player.id


# ----- nobody, the short offseason, a window closed -----

def test_when_no_contract_ends_the_stage_says_so_asks_nothing_and_goes_on(tmp_path):
    league = contract_league(places=())
    rig = run(tmp_path, league)
    text = spoken(rig)
    assert X.text("NXW-02") in text and HEADER in text and not any("he asks" in t for t in text)
    final = rig.fstore.league
    assert final.resign is None and final.stage_no >= D.STAGE_FREE_AGENCY


def test_the_short_offseason_still_asks_about_the_players_and_ends_the_stage_without_a_wait(tmp_path):
    league = contract_league()
    rig = run(tmp_path, league, short=True)
    text = spoken(rig)
    stage = text[text.index(HEADER):text.index(" stage 6 of 9. free agency. ")]
    assert len([t for t in stage if "he asks" in t]) == 3
    assert X.text("NXE-03") not in stage and X.text("NXW-31", n=3, m=0) in stage


def test_the_short_offseason_with_nobody_to_ask_says_one_sentence_per_line_and_no_wait(tmp_path):
    league = contract_league(places=())
    text = spoken(run(tmp_path, league, short=True))
    stage = text[text.index(HEADER):text.index(" stage 6 of 9. free agency. ")]
    assert X.text("NXW-02") in stage and X.text("NXE-03") not in stage


def test_a_window_closed_at_the_first_question_leaves_him_as_he_was_and_the_stage_in_progress_on_disk(tmp_path):
    league = contract_league()
    rig = run(tmp_path, league, until=lambda r: any(" 1. sign him " in t for t in spoken(r)))
    saved = saved_league(rig)
    assert saved.stage_no == D.STAGE_CONTRACTS and saved.resign is not None
    assert len(saved.resign["pending"]) == 3 and saved.resign["signed"] == saved.resign["let_go"] == 0
    assert all(saved.players[pid].years == 0 and saved.players[pid].status == "active" for pid in saved.resign["pending"])
    assert not any(t.startswith(" ") and " signs, " in t for t in spoken(rig))                # nothing was told, nothing decided


def test_a_window_closed_after_the_first_decision_resumes_at_the_second_player_with_the_first_kept(tmp_path):
    league = contract_league()
    order = asked(league)
    first = run(tmp_path / "one", league, keys=pick(5), until=lambda r: any(" is let go. " in t for t in spoken(r)))
    saved = saved_league(first)
    assert saved.resign["pending"] == [p.id for p in order[1:]] and saved.resign["let_go"] == 1 and saved.players[order[0].id].status == "free"
    second = run(tmp_path / "two", None, files=first.files)
    text = spoken(second)
    assert not any(t.startswith(" %s, " % order[0].name) and "he asks" in t for t in text)      # not asked again
    assert any(t.startswith(" %s, " % order[1].name) and "he asks" in t for t in text)
    assert X.text("NXW-01", coach="Kim", n=2) in text and X.text("NXW-31", n=2, m=1) in text      # the rest, and the totals of both runs
    final = second.fstore.league
    assert final.players[order[0].id].status == "free" and final.players[order[1].id].years > 0 and final.resign is None


def test_a_window_closed_at_the_stages_wait_resumes_at_the_draft_with_nothing_asked_twice(tmp_path):
    league = contract_league()
    first = run(tmp_path / "one", league, until=lambda r: X.text("NXE-03") in spoken(r)[-3:] and any(" signs, " in t for t in spoken(r)))
    saved = saved_league(first)
    assert saved.stage_no == D.STAGE_FREE_AGENCY and saved.resign is None
    second = run(tmp_path / "two", None, files=first.files, until=at_stage(D.STAGE_DRAFT))             # the market (stage 6 of 9) runs, then the draft begins
    assert HEADER not in spoken(second) and not any("he asks" in t and "with the team" in t for t in spoken(second))      # (the market's lines say "he asks" too)


# ----- the file -----

def test_the_stage_starts_with_one_write_that_holds_the_other_teams_settled_and_the_players_still_to_ask(tmp_path):
    league = contract_league()
    rig = run(tmp_path, league, keep=True)
    saves = [s for s in rig.saves if s[0] == D.STAGE_CONTRACTS]
    first = LeagueRecord.from_json(saves[0][3].decode("utf-8"))
    assert first.resign is not None and len(first.resign["pending"]) == 3
    assert all(p.years > 0 for p in first.players.values() if p.status == "active" and p.team != TEAM)         # the others are settled
    assert [first.players[pid].years for pid in first.resign["pending"]] == [0, 0, 0]
    last = LeagueRecord.from_json(rig.kept[D.STAGE_FREE_AGENCY].decode("utf-8"))
    assert last.resign is None and all(p.years > 0 for p in last.players.values() if p.status == "active")


def test_every_save_of_the_stage_passes_the_whole_file_check_at_its_stage(tmp_path):
    league = contract_league()
    rig = run(tmp_path, league, keep=True, keys=pick(2) + pick(3) + pick(4))
    for stage, _, _, raw, _ in rig.saves:
        if raw is not None:
            LeagueRecord.from_json(raw.decode("utf-8"))                                      # the rig's store is strict as well


# ----- F9 in the middle of the stage -----

def test_the_roster_in_f9_says_contract_ended_for_a_player_still_to_be_asked_and_the_cap_does_not_count_him(tmp_path):
    from nfl4.extras.franchise import history
    league = contract_league()
    rig = run(tmp_path, league, until=lambda r: any(" 1. sign him " in t for t in spoken(r)))
    store = rig.fstore
    pending = store.league.players[store.league.resign["pending"][0]]
    assert X.text("NXW-60") in store.words.player_with_contract(pending)
    assert CT.cap_used(store.league, TEAM) == sum(p.salary for p in store.league.active_of(TEAM) if p is not None and p.years > 0)
    assert history.cap_text(store.league, store.words)


def test_stars_of_other_teams_who_are_let_go_are_named_best_first(tmp_path):
    def stars(league):
        for team, rating in ((2, 99), (3, 96), (4, 91), (6, 85)):
            player = league.player_at(team, 12)
            player.rating, player.peak, player.years = rating, rating, 0
            for other in league.active_of(team):
                if other is not None and other.years > 0:
                    other.salary = T.FR_MAX_SALARY                                           # no room: the star cannot be signed again
    league = contract_league(mutate=stars)
    rig = run(tmp_path, league)
    text = spoken(rig)
    words = rig.fstore.words
    lines = [t for t in text if "is not signed again and is a free agent" in t]
    assert len(lines) == 3
    start = start_of(league)
    names = [start.player_at(team, 12).name for team in (2, 3, 4)]
    assert [line.split(" of the ")[0].strip() for line in lines] == names
    assert words.team_name(2) in lines[0]


def test_the_staff_setting_turned_on_between_two_questions_hands_the_rest_to_the_staff(tmp_path):
    """A setting that hands the choice to the staff is read at every step (A56): turned on in F9 after the first answer, it applies to
    the players still to be asked, and the ones already answered stay as the player chose."""
    league = contract_league()
    order = asked(league)

    def until(rig):
        settings = rig.game.options.settings.game
        if any(" signs, " in t for t in spoken(rig)) and not settings.nx_fr_auto:
            settings.nx_fr_auto = True                      # the player turned it on after the first answer (the second question is open)
        return at_stage(D.STAGE_FREE_AGENCY)(rig)
    rig = run(tmp_path, league, until=until)
    text = spoken(rig)
    final = rig.fstore.league
    assert X.text("NXW-30", n=1, m=0) in text                 # the third player: the staff
    assert X.text("NXW-31", n=3, m=0) in text
    assert len([t for t in text if "he asks" in t]) == 2                       # only two players were asked
    assert all(final.players[p.id].years > 0 for p in order) and final.resign is None


def test_a_player_the_staff_lets_go_after_the_setting_was_turned_on_is_counted_as_let_go(tmp_path):
    def weak_last(league):
        league.player_at(TEAM, 7).rating = 41                       # the receiver, the least valuable of the three: the staff would let him go

    league = contract_league(mutate=weak_last)
    order = asked(league)
    assert order[-1].pos == "WR"

    def until(rig):
        settings = rig.game.options.settings.game
        if any(" signs, " in t for t in spoken(rig)) and not settings.nx_fr_auto:
            settings.nx_fr_auto = True
        return at_stage(D.STAGE_FREE_AGENCY)(rig)
    rig = run(tmp_path, league, until=until)
    text = spoken(rig)
    assert X.text("NXW-30", n=0, m=1) in text and X.text("NXW-31", n=2, m=1) in text
    assert rig.fstore.league.players[order[-1].id].status == "free"


def test_with_the_shipped_payroll_target_the_staffs_choice_for_the_players_team_is_the_computer_teams_rule_and_lets_players_go_for_the_market(tmp_path, monkeypatch):
    monkeypatch.setattr(T, "FR_RESIGN_TARGET", 0.62)                                        # the value the game ships with (the other tests of this file leave the target out)
    league = contract_league(places=(0, 7, 12, 20, 33))
    rig = run(tmp_path, league, auto=True)
    expected = start_of(league)
    out = resign.run_teams(expected)
    final = rig.fstore.league
    mine = [p for p in expected.players.values() if p.team == TEAM and league.players[p.id].years == 0]
    assert len(mine) == 5 and any(p.status == "free" for p in mine)                          # at the shipped target the payroll is over: some of his players go to the market
    for player in mine:
        now = final.players[player.id]
        assert (now.salary, now.years, now.status) == (player.salary, player.years, player.status), player.id
    assert X.text("NXW-30", n=len([p for p in mine if p.status == "active"]), m=len([p for p in mine if p.status == "free"])) in spoken(rig)
    assert out.gone
