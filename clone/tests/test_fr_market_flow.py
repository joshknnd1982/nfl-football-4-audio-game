"""The Franchise's free agency as stage 5 of 8 on the program rig (nfl4 only, rule 0.13; NFL_FRANCHISE_DESIGN 17 SX.8i, D-068): the market in rounds, the player's
offers, the staff setting, the short offseason, a window closed in the middle, F9's free agents and the file the stage writes. The rules are test_fr_market.py.
"""
import pytest
from drrig import at_stage, draft_league, offseason_rig, saved_league
from frrig import DOWN, ENTER, ESC, F9, UP, spoken

from nfl4.extras import nx_texts as X
from nfl4.extras import tuning as T
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import market as M
from nfl4.extras.franchise import resign
from nfl4.extras.franchise.league import LeagueRecord

TEAM = 5
OWN = (33, 0, 7)                                     # the player's own players who were not signed again: the quarterback, a running back, a receiver
OTHERS = ((2, 12, 82), (3, 18, 74), (4, 7, 88), (6, 23, 66), (8, 0, 72), (9, 31, 61), (10, 33, 80), (11, 13, 77), (12, 19, 69))      # (team, place, rating)
HEADER = " stage 5 of 8. free agency. "
DRAFT_HEADER = " stage 6 of 8. the draft. "
END_ROUND = [UP, UP, ENTER]                          # the last item but one wraps round from the first: "end the round and hear the results"
STAFF_REST = [UP, ENTER]                             # ... and the last: "let the staff make my offers from now on"


def market_league(seed=3, own=OWN, others=OTHERS, wins=8, mutate=None, broke=()):
    """A league at the start of free agency (stage 5 of 8): the player's own players of these places and the other teams' players of `others` are free agents
    (the ones stage 7 did not sign again), their places empty."""
    def change(league):
        for index in own:
            resign.let_go(league, league.player_at(TEAM, index))
        for team, index, rating in others:
            player = league.player_at(team, index)
            player.rating, player.peak = rating, max(player.peak, rating)
            resign.let_go(league, player)
        for team in broke:                                   # these teams have no room under the cap: they make no offer
            for player in league.active_of(team):
                if player is not None:
                    player.salary = T.FR_MAX_SALARY
        if mutate is not None:
            mutate(league)
    return draft_league(seed=seed, team=TEAM, stage_no=D.STAGE_FREE_AGENCY, wins=[wins] * 32, finish=[D.FINISH_MISSED] * 32, mutate=change)


def quiet_league(**kwargs):
    """The same market, but the teams the other free agents came from cannot pay: only the player's team wants his own players and theirs."""
    return market_league(broke=(4, 8, 10), **kwargs)


def first_question(rig):
    """The predicate that stops the program at the first question of round 1 (the window is closed at the first wait for a key)."""
    return any(t.startswith(" round 1 of 3. your open places") for t in spoken(rig))


def run(tmp_path, league, keys=(), until=None, **kwargs):
    return offseason_rig(tmp_path, league, keys=keys, until=until or at_stage(D.STAGE_DRAFT), picks_told="mine", **kwargs)


def start_of(league):
    return LeagueRecord.from_json(league.to_json())


def three_rounds():
    return END_ROUND * T.FR_FA_ROUNDS


def final_of(rig):
    return rig.fstore.league


def after_stage(rig):
    """The league as the stage left it: the first save that names the draft."""
    return LeagueRecord.from_json(rig.kept[D.STAGE_DRAFT].decode("utf-8"))


def staff_market(league, skip=()):
    """The market as the computer teams make it: the same rules the program calls (`market.run_market`) on a copy of the league."""
    copy_of = start_of(league)
    M.run_market(copy_of, skip)
    return copy_of


def same_players(a, b):
    for pid, player in a.players.items():
        other = b.players[pid]
        assert (other.status, other.team, other.place, other.salary, other.years) == (player.status, player.team, player.place, player.salary, player.years), pid
    assert a.rosters == b.rosters


def wanted_by(league, round_no=1):
    """The free agents for the player's open places in the order his question lists them, and the interest of the computer's teams."""
    positions = {position for position, _ in M.open_places(league, TEAM)}
    wanted = [pl for pl in M.pool(league) if pl.pos in positions]
    return wanted, M.interest(M.computer_bids(league, round_no, skip=(TEAM,)))


def end_from(league, cursor):
    """The keys that end round 1 when the cursor stands on item `cursor` (from 0) of its question: down to "end the round and hear the results", then Enter.
    (After an offer or a refusal the question comes back on the item the player was on; the next round starts on the first item.)"""
    wanted, _ = wanted_by(start_of(league))
    shown = min(len(wanted), T.FR_FA_LIST)
    end = shown + (1 if len(wanted) > shown else 0)
    return [DOWN] * (end - cursor) + [ENTER]


def line_of(words, player, round_no, heard, offer=None):
    salary, years = M.price(player, round_no)
    return words.free_agent(player, salary, years, heard.get(player.id, 0), offer)


# ----- what the stage says and asks -----

def test_the_stage_names_itself_counts_the_market_and_asks_round_one_with_the_open_places_the_room_and_the_first_free_agents(tmp_path):
    league = market_league()
    rig = run(tmp_path, league, until=first_question)
    text = spoken(rig)
    start = start_of(league)
    words = rig.fstore.words
    at = text.index(HEADER)
    assert text[at + 1] == X.text("NXJ-01", n=len(M.pool(start)))
    assert text[at + 2] == X.text("NXJ-02", round=1, m=T.FR_FA_ROUNDS, list=words.open_places(M.open_places(start, TEAM)), room=words.amount(M.room(start, TEAM)))
    assert "quarterback 1" in text[at + 2] and "running back 1" in text[at + 2] and "receiver 1" in text[at + 2]
    wanted, heard = wanted_by(start)
    assert text[at + 3] == " 1. " + line_of(words, wanted[0], 1, heard).strip() + " "
    assert all(pl.pos in ("QB", "RB", "WR") for pl in wanted)


def test_the_list_holds_the_staffs_five_then_hear_more_then_the_two_last_answers(tmp_path):
    league = market_league()
    wanted, _ = wanted_by(start_of(league))
    assert len(wanted) > T.FR_FA_LIST
    rig = run(tmp_path, league, keys=[UP, UP, UP, DOWN, ENTER] + END_ROUND * 2)      # round from the first item to the last three (each is spoken), then end the round
    asked = spoken(rig)[spoken(rig).index(HEADER):]
    count = T.FR_FA_LIST
    assert " %d. hear more free agents " % (count + 1) in asked
    assert " %d. end the round and hear the results " % (count + 2) in asked
    assert " %d. let the staff make my offers from now on " % (count + 3) in asked


def test_the_free_agents_with_interest_are_told_how_many_other_teams_want_them(tmp_path):
    league = market_league(broke=(8,))                                    # the running back's team cannot pay him: nobody else wants the running backs
    wanted, heard = wanted_by(start_of(league))
    assert any(heard.get(pl.id, 0) >= 1 for pl in wanted) and any(heard.get(pl.id, 0) == 0 for pl in wanted)
    rig = run(tmp_path, league, keys=[DOWN] * (T.FR_FA_LIST + 1) + [ENTER] + END_ROUND * 2)       # walk down the list so that each item is spoken, then end the round
    text = spoken(rig)
    words = rig.fstore.words
    for number, player in enumerate(wanted[:T.FR_FA_LIST], start=1):                           # each item says what the computer teams' offers say
        line = line_of(words, player, 1, heard).strip()
        assert " %d. %s " % (number, line) in text
        want = "no other team is interested" if heard.get(player.id, 0) == 0 else "one other team is interested" if heard[player.id] == 1 else "%d other teams are interested" % heard[player.id]
        assert want in line
    assert any(heard.get(pl.id, 0) >= 2 for pl in wanted[:T.FR_FA_LIST]) or any(heard.get(pl.id, 0) == 1 for pl in wanted[:T.FR_FA_LIST])


# ----- nothing is decided for the player -----

def test_when_the_player_ends_every_round_with_no_offer_nothing_is_signed_for_him_and_the_other_teams_sign_by_the_staffs_rule(tmp_path):
    league = market_league()
    rig = run(tmp_path, league, keys=three_rounds(), keep=True)
    final = after_stage(rig)
    same_players(final, staff_market(league, skip=(TEAM,)))
    assert [final.rosters[TEAM - 1][i] for i in OWN] == [0, 0, 0]
    assert final.market is None and final.stage_no == D.STAGE_DRAFT
    text = spoken(rig)
    assert not any(" signs with you, " in t for t in text)
    assert X.text("NXJ-F02", n=0, m=0, k=len(M.pool(final))) in text


def test_the_headlines_name_the_most_valuable_signings_of_the_other_teams_then_count_the_rest(tmp_path):
    league = market_league()
    rig = run(tmp_path, league, keys=three_rounds())
    text = spoken(rig)
    words = rig.fstore.words
    first = M.run_round(start_of(league), 1, (), skip=(TEAM,))
    assert len(first.signed) > D.STARS_NAMED
    for player, bid in first.signed[:D.STARS_NAMED]:
        assert X.text("NXJ-E04", player=player.name, team=words.team_name(bid.team), position=words.position(player.pos), r=player.rating) in text
    assert X.text("NXJ-E05", n=len(first.signed) - D.STARS_NAMED) in text
    fourth, bid = first.signed[D.STARS_NAMED]                          # the fourth signing is counted, not named
    assert X.text("NXJ-E04", player=fourth.name, team=words.team_name(bid.team), position=words.position(fourth.pos), r=fourth.rating) not in text


# ----- offers -----

def target_without_rivals(league):
    wanted, heard = wanted_by(start_of(league))
    shown = wanted[:T.FR_FA_LIST]
    pick = next(pl for pl in shown if heard.get(pl.id, 0) == 0)
    return shown.index(pick), pick


def test_an_offer_at_the_price_for_a_free_agent_nobody_else_wants_signs_him_on_that_contract(tmp_path):
    league = quiet_league()
    index, target = target_without_rivals(league)
    rig = run(tmp_path, league, keys=[DOWN] * index + [ENTER, ENTER] + end_from(league, index) + END_ROUND * 2)
    final = final_of(rig)
    words = rig.fstore.words
    salary, years = M.price(target, 1)
    signed = final.players[target.id]
    assert (signed.status, signed.team, signed.salary, signed.years) == ("active", TEAM, salary, years)
    text = spoken(rig)
    assert X.text("NXJ-C07", player=target.name, contract=words.contract_of(salary, years)) in text
    assert X.text("NXJ-E01", player=target.name, contract=words.contract_of(salary, years)) in text
    assert X.text("NXJ-F02", n=1, m=0, k=len(M.pool(final))) in text
    assert signed.place in D.PLACES_OF[target.pos] and final.rosters[TEAM - 1][signed.place] == target.id


def test_a_second_offer_for_the_same_free_agent_replaces_the_first(tmp_path):
    league = quiet_league()
    index, target = target_without_rivals(league)
    salary, years = M.price(target, 1)
    keys = [DOWN] * index + [ENTER, ENTER] + [ENTER, DOWN, ENTER] + end_from(league, index) + END_ROUND * 2          # the price, then ten percent more for the same player
    rig = run(tmp_path, league, keys=keys)
    signed = final_of(rig).players[target.id]
    assert (signed.team, signed.salary) == (TEAM, M.more(salary))
    text = spoken(rig)
    assert len([t for t in text if t.startswith(" you offer %s " % target.name)]) == 2
    assert X.text("NXJ-F02", n=1, m=0, k=len(M.pool(final_of(rig)))) in text


def test_offering_ten_percent_more_signs_him_for_that_money(tmp_path):
    league = quiet_league()
    index, target = target_without_rivals(league)
    rig = run(tmp_path, league, keys=[DOWN] * index + [ENTER, DOWN, ENTER] + end_from(league, index) + END_ROUND * 2)
    salary, years = M.price(target, 1)
    signed = final_of(rig).players[target.id]
    assert (signed.team, signed.salary, signed.years) == (TEAM, M.more(salary), years) and M.more(salary) > salary


def rival_league():
    """A receiver rated 90 of team 9 is on the market. Team 9's other receivers are poor (he would be the best of the group: fit 2), the player's are very good
    (he would not be better than the weakest: fit 0), so at the same price the computer team's offer scores more."""
    def change(league):
        for team, rating in ((TEAM, 95), (9, 60)):
            for index in D.PLACES_OF["WR"]:
                if league.rosters[team - 1][index]:
                    league.players[league.rosters[team - 1][index]].rating = rating
    return market_league(own=(7,), others=((9, 6, 90),), mutate=change)


def rival_index(league):
    wanted, heard = wanted_by(start_of(league))
    star = next(pl for pl in wanted if pl.rating == 90)
    assert wanted.index(star) < T.FR_FA_LIST and heard.get(star.id, 0) >= 1
    return wanted.index(star), star


def test_an_offer_that_scores_less_than_a_computer_teams_loses_and_the_player_hears_who_signed_him(tmp_path):
    league = rival_league()
    index, star = rival_index(league)
    start = start_of(league)
    price = M.price(star, 1)[0]
    assert M.score(start, TEAM, star, price) < M.score(start, 9, star, price)
    rig = run(tmp_path, league, keys=[DOWN] * index + [ENTER, ENTER] + end_from(league, index) + END_ROUND * 2)
    final = final_of(rig)
    words = rig.fstore.words
    assert final.players[star.id].team == 9
    text = spoken(rig)
    assert X.text("NXJ-E02", player=star.name, team=words.team_name(9)) in text
    assert not any(" signs with you, " in t and star.name in t for t in text)
    assert X.text("NXJ-F02", n=0, m=1, k=len(M.pool(final))) in text


def test_ten_percent_more_beats_the_better_fit_of_a_computer_team(tmp_path):
    league = rival_league()
    index, star = rival_index(league)
    start = start_of(league)
    price, years = M.price(star, 1)
    assert M.score(start, TEAM, star, M.more(price)) > M.score(start, 9, star, price)
    rig = run(tmp_path, league, keys=[DOWN] * index + [ENTER, DOWN, ENTER] + end_from(league, index) + END_ROUND * 2)
    signed = final_of(rig).players[star.id]
    assert (signed.team, signed.salary) == (TEAM, M.more(price))
    assert X.text("NXJ-E01", player=star.name, contract=rig.fstore.words.contract_of(M.more(price), years)) in spoken(rig)


def test_a_placed_offer_is_withdrawn_from_the_same_menu(tmp_path):
    league = quiet_league()
    index, target = target_without_rivals(league)
    rig = run(tmp_path, league, keys=[DOWN] * index + [ENTER, ENTER] + [ENTER, DOWN, DOWN, ENTER] + end_from(league, index) + END_ROUND * 2)
    text = spoken(rig)
    assert X.text("NXJ-C08", player=target.name) in text
    assert final_of(rig).players[target.id].team != TEAM
    assert X.text("NXJ-A04", contract=rig.fstore.words.contract_of(*M.price(target, 1))) in " ".join(text)         # the item said so while the offer stood
    assert not any(" signs with you, " in t for t in text)


def test_never_mind_places_nothing(tmp_path):
    league = market_league()
    rig = run(tmp_path, league, keys=[ENTER, UP, ENTER] + END_ROUND * 3)               # open the first free agent's menu, then its last answer: never mind
    text = spoken(rig)
    assert not any(t.startswith(" you offer ") for t in text) and not any(" signs with you, " in t for t in text)


def test_no_more_offers_than_a_round_may_have_are_taken(tmp_path, monkeypatch):
    monkeypatch.setattr(T, "FR_FA_OFFERS", 1)
    league = market_league()
    rig = run(tmp_path, league, keys=[ENTER, ENTER, DOWN, ENTER, ENTER] + end_from(league, 1) + END_ROUND * 2)       # an offer for the first, then another for the second
    text = spoken(rig)
    assert X.text("NXJ-D03") in text and len([t for t in text if t.startswith(" you offer ")]) == 1


def test_no_more_offers_for_a_position_than_it_has_open_places_times_the_chase(tmp_path, monkeypatch):
    monkeypatch.setattr(T, "FR_FA_CHASE", 1)
    league = market_league(others=OTHERS + ((13, 8, 70),))
    wanted, _ = wanted_by(start_of(league))
    same = [i for i, pl in enumerate(wanted[:T.FR_FA_LIST]) if pl.pos == wanted[0].pos]
    assert len(same) >= 2
    keys = [ENTER, ENTER] + [DOWN] * same[1] + [ENTER, ENTER]
    rig = run(tmp_path, league, keys=keys + end_from(league, same[1]) + END_ROUND * 2)
    text = spoken(rig)
    assert X.text("NXJ-D02") in text and len([t for t in text if t.startswith(" you offer ")]) == 1


def test_in_a_later_round_he_may_place_one_more_offer_for_a_position_as_the_computer_teams_chase_one_more(tmp_path, monkeypatch):
    monkeypatch.setattr(T, "FR_FA_CHASE", 1)
    league = market_league(others=OTHERS + ((13, 8, 70), (14, 9, 68)))
    after_one = start_of(league)
    M.run_round(after_one, 1, (), skip=(TEAM,))
    wanted, _ = wanted_by(after_one, 2)
    shown = wanted[:T.FR_FA_LIST]
    same = [i for i, pl in enumerate(shown) if pl.pos == shown[0].pos]
    assert len(same) >= 2 and M.chase(2) == 2
    end = len(shown) + (1 if len(wanted) > len(shown) else 0)
    keys = END_ROUND + [ENTER, ENTER] + [DOWN] * same[1] + [ENTER, ENTER] + [DOWN] * (end - same[1]) + [ENTER] + END_ROUND
    rig = run(tmp_path, league, keys=keys)
    text = spoken(rig)
    round_two = text[next(i for i, t in enumerate(text) if t.startswith(" round 2 of 3. your open places")):]
    assert len([t for t in round_two if t.startswith(" you offer ")]) == 2 and X.text("NXJ-D02") not in round_two          # a flat chase of 1 would have refused the second


def test_one_free_agent_on_the_market_is_told_in_the_singular(tmp_path):
    league = market_league(own=(), others=((2, 12, 82),))
    text = spoken(run(tmp_path, league))
    assert X.text("NXJ-I01") in text and not any("1 free agents" in t for t in text)


def test_an_offer_he_cannot_pay_is_not_in_the_menu(tmp_path):
    def poor(league):
        for player in league.active_of(TEAM):
            if player is not None:
                player.salary = 60                                              # 31 contracts of 6.0 million: hardly any room
    league = market_league(mutate=poor)
    start = start_of(league)
    space = M.room(start, TEAM)
    wanted, _ = wanted_by(start)
    dear = next(pl for pl in wanted[:T.FR_FA_LIST] if M.price(pl, 1)[0] > space)
    rig = run(tmp_path, league, keys=[DOWN] * wanted.index(dear) + [ENTER],
              until=lambda r: any(t.startswith(" %s. you can pay up to " % dear.name) for t in spoken(r)))
    text = spoken(rig)
    at = max(i for i, t in enumerate(text) if t.startswith(" %s. you can pay up to " % dear.name))
    assert not any(t.startswith(" 1. offer ") for t in text[at:at + 3]) and " 1. never mind " in text[at:at + 3]
    assert M.price(dear, 1)[0] > space and M.more(M.price(dear, 1)[0]) > space


# ----- the staff -----

def test_with_the_staff_handling_it_nothing_is_asked_and_the_players_team_is_a_computer_team_of_the_market(tmp_path):
    league = market_league()
    rig = run(tmp_path, league, auto=True, keep=True)
    text = spoken(rig)
    assert HEADER in text and X.text("NXJ-G01") in text
    assert not any(t.startswith(" round ") and "your open places" in t for t in text)
    same_players(after_stage(rig), staff_market(league))
    assert any(" signs with you, " in t for t in text)


def test_handing_the_rest_of_free_agency_to_the_staff_in_the_first_round_equals_the_staff_handling_it(tmp_path):
    league = market_league()
    rig = run(tmp_path, league, keys=STAFF_REST, keep=True)
    same_players(after_stage(rig), staff_market(league))
    assert X.text("NXJ-G01") in spoken(rig)
    assert len([t for t in spoken(rig) if t.startswith(" round ") and "your open places" in t]) == 1         # asked once, then the staff
    assert X.text("NXJ-G03") not in spoken(rig)                       # he had placed nothing


def test_the_players_offers_of_earlier_rounds_stand_when_he_hands_the_rest_to_the_staff(tmp_path):
    league = quiet_league()
    index, target = target_without_rivals(league)
    rig = run(tmp_path, league, keys=[DOWN] * index + [ENTER, ENTER] + end_from(league, index) + STAFF_REST, keep=True)
    final = after_stage(rig)
    assert final.players[target.id].team == TEAM and final.players[target.id].status == "active"
    assert final.market is None


def test_the_staff_setting_turned_on_while_the_player_is_placing_an_offer_hands_the_round_to_the_staff(tmp_path):
    """The player opens the first free agent's menu; while it is open the setting is turned on (as F9 would). The rig then presses Up, Up, Enter: the offer for
    ten percent more is placed, the question comes back to the round, sees the setting and hands the round (and the offer, which the staff's own replace) to the staff."""
    league = market_league()

    def until(rig):
        settings = rig.game.options.settings.game
        if any(t.endswith(". you can pay up to 50.9 million. ") and not t.startswith(" round") for t in spoken(rig)) and not settings.nx_fr_auto:
            settings.nx_fr_auto = True
        return at_stage(D.STAGE_DRAFT)(rig)
    rig = run(tmp_path, league, keys=[ENTER], until=until, keep=True)
    final = after_stage(rig)
    same_players(final, staff_market(league))
    assert X.text("NXJ-G03") in spoken(rig)                           # the offer he had placed was withdrawn, and he was told
    assert X.text("NXJ-G01") in spoken(rig)


# ----- the short offseason and nobody to sign -----

def test_the_short_offseason_still_asks_the_player_and_ends_the_stage_with_one_sentence_and_no_wait(tmp_path):
    league = market_league()
    rig = run(tmp_path, league, keys=three_rounds(), short=True)
    text = spoken(rig)
    stage = text[text.index(HEADER):text.index(DRAFT_HEADER)]
    assert X.text("NXJ-I04") in stage and X.text("NXE-03") not in stage
    assert any(t.startswith(" round 3 of 3. your open places") for t in stage)
    assert not any(t.startswith(" ") and " signs with the " in t for t in stage)               # no headlines in a short offseason


def test_the_short_offseason_tells_his_own_result_after_each_round_not_at_the_end(tmp_path):
    league = quiet_league()
    index, target = target_without_rivals(league)
    rig = run(tmp_path, league, keys=[DOWN] * index + [ENTER, ENTER] + end_from(league, index) + END_ROUND * 2, short=True)
    text = spoken(rig)
    stage = text[text.index(HEADER):text.index(DRAFT_HEADER)]
    signs = next(i for i, t in enumerate(stage) if t.startswith(" %s signs with you, " % target.name))
    second = next(i for i, t in enumerate(stage) if t.startswith(" round 2 of 3. your open places"))
    assert signs < second and X.text("NXJ-I03") in stage


def test_the_short_offseason_with_the_staff_asks_nothing_and_counts_what_it_signed(tmp_path):
    league = market_league()
    rig = run(tmp_path, league, auto=True, short=True)
    text = spoken(rig)
    stage = text[text.index(HEADER):text.index(DRAFT_HEADER)]
    expected = staff_market(league)
    mine = [p for p in expected.players.values() if p.status == "active" and p.team == TEAM and league.players[p.id].status == "free"]
    assert len(mine) > 1 and X.text("NXJ-G02", n=len(mine)) in stage and not any(t.startswith(" round ") and "your open places" in t for t in stage)
    assert len([t for t in stage if " signs with you, " in t]) == len(mine)


def test_when_the_players_team_has_no_open_place_nothing_is_asked_and_the_stage_says_so(tmp_path):
    league = market_league(own=())
    rig = run(tmp_path, league)
    text = spoken(rig)
    assert X.text("NXJ-D01") in text and not any(t.startswith(" round ") and "your open places" in t for t in text)
    assert text.count(X.text("NXJ-D01")) == 1                          # said once, not in every round
    assert final_of(rig).stage_no >= D.STAGE_DRAFT and final_of(rig).market is None


def test_when_no_free_agent_is_left_for_the_open_places_the_question_says_so(tmp_path):
    def nobody(league):
        for player in league.players.values():
            if player.status == "free" and player.pos in ("QB", "RB", "WR"):
                player.status = "retired"
    league = market_league(mutate=nobody)
    text = spoken(run(tmp_path, league, keys=END_ROUND * 3))
    assert X.text("NXJ-D05") in text


# ----- a window closed in the middle -----

def test_a_window_closed_at_the_first_question_leaves_the_market_in_progress_on_disk_with_nothing_signed_for_him(tmp_path):
    league = market_league()
    rig = run(tmp_path, league, until=lambda r: any(t.startswith(" round 1 of 3. your open places") for t in spoken(r)))
    saved = saved_league(rig)
    assert saved.stage_no == D.STAGE_FREE_AGENCY and saved.market == M.begin()
    assert [saved.rosters[TEAM - 1][i] for i in OWN] == [0, 0, 0]


def test_a_window_closed_after_an_offer_resumes_the_same_round_with_the_offer_kept(tmp_path):
    league = quiet_league()
    index, target = target_without_rivals(league)
    first = run(tmp_path / "one", league, keys=[DOWN] * index + [ENTER, ENTER],
                until=lambda r: r.fstore is not None and r.fstore.league.market is not None and bool(r.fstore.league.market["offers"]) and
                any(t.startswith(" you offer ") for t in spoken(r)))
    saved = saved_league(first)
    price = M.price(target, 1)[0]
    assert saved.market["round"] == 1 and saved.market["offers"] == [[target.id, price]]
    second = run(tmp_path / "two", None, files=first.files, keys=END_ROUND * 3)
    text = spoken(second)
    assert X.text("NXJ-A04", contract=second.fstore.words.contract_of(*M.price(target, 1))) in " ".join(text)         # his offer is still on the item
    assert final_of(second).players[target.id].team == TEAM and final_of(second).market is None


def test_a_window_closed_between_two_rounds_resumes_at_the_next_round_and_does_not_judge_the_first_again(tmp_path):
    league = market_league()
    first = run(tmp_path / "one", league, keys=END_ROUND,
                until=lambda r: sum(1 for t in spoken(r) if t.startswith(" round ") and "your open places" in t) >= 2)
    saved = saved_league(first)
    assert saved.market["round"] == 2
    round_one = M.run_round(start_of(league), 1, (), skip=(TEAM,))
    assert all(saved.players[p.id].team == bid.team for p, bid in round_one.signed)
    second = run(tmp_path / "two", None, files=first.files, keys=END_ROUND * 2, keep=True)
    text = spoken(second)
    assert not any(t.startswith(" round 1 of 3. ") for t in text) and any(t.startswith(" round 2 of 3. ") for t in text)
    assert X.text("NXJ-F02", n=0, m=0, k=len(M.pool(after_stage(second)))) in text


def test_a_window_closed_at_the_stages_wait_resumes_at_the_draft_with_nothing_asked_twice(tmp_path):
    league = market_league()
    first = run(tmp_path / "one", league, keys=three_rounds(), until=lambda r: X.text("NXJ-F02", n=0, m=0, k=len(M.pool(r.fstore.league))) in spoken(r))
    saved = saved_league(first)
    assert saved.stage_no == D.STAGE_DRAFT and saved.market is None
    second = run(tmp_path / "two", None, files=first.files)
    assert HEADER not in spoken(second) and not any(t.startswith(" round ") and "your open places" in t for t in spoken(second))


# ----- the file -----

def test_the_stage_starts_with_one_write_and_the_market_then_ends_with_the_stage_changed_in_the_same_save(tmp_path):
    league = market_league()
    rig = run(tmp_path, league, keys=three_rounds(), keep=True)
    saves = [s for s in rig.saves if s[0] == D.STAGE_FREE_AGENCY]
    first = LeagueRecord.from_json(saves[0][3].decode("utf-8"))
    assert first.market == M.begin() and first.stage_no == D.STAGE_FREE_AGENCY
    assert len(saves) == T.FR_FA_ROUNDS                                   # the opening, and one save for each of the first two rounds' judgement
    last = after_stage(rig)
    assert last.market is None and last.stage_no == D.STAGE_DRAFT
    rounds = [LeagueRecord.from_json(s[3].decode("utf-8")) for s in saves]
    assert [r.market["round"] for r in rounds] == [1, 2, 3]


def test_every_save_of_the_stage_passes_the_whole_file_check_at_its_stage(tmp_path):
    league = quiet_league()
    index, _ = target_without_rivals(league)
    rig = run(tmp_path, league, keys=[DOWN] * index + [ENTER, ENTER] + end_from(league, index) + [ENTER, DOWN, ENTER] + END_ROUND * 2, keep=True)
    count = 0
    for stage, _, _, raw, _ in rig.saves:
        if raw is not None:
            LeagueRecord.from_json(raw.decode("utf-8"))
            count += 1
    assert count >= 5


def test_the_result_of_a_round_is_written_before_it_is_told(tmp_path):
    """The last file written before the line that tells a signing already holds that player on his new team (B-X53)."""
    league = quiet_league()
    index, target = target_without_rivals(league)
    rig = run(tmp_path, league, keys=[DOWN] * index + [ENTER, ENTER] + end_from(league, index) + END_ROUND * 2, keep=True)
    texts = [t for t, _, _ in rig.said]
    line = next(i for i, t in enumerate(texts) if t.startswith(" %s signs with you, " % target.name))
    files = [(count, raw) for stage, _, _, raw, count in rig.saves if stage == D.STAGE_FREE_AGENCY and count <= line]
    saved = LeagueRecord.from_json(files[-1][1].decode("utf-8"))
    assert saved.players[target.id].team == TEAM and saved.players[target.id].status == "active" and saved.market["round"] == 2


# ----- F9 -----

FREE_AGENTS_IN_F9 = [F9, DOWN, DOWN, DOWN, DOWN, ENTER] + [DOWN] * 6 + [ENTER]          # F9, Franchise, the free agents (the 7th item)


def test_f9_lists_the_free_agents_with_their_asking_prices_during_the_stage(tmp_path, monkeypatch):
    from nfl4.extras.franchise import menus
    lists = []
    real = menus._lines_picker

    def picker(speech, keys, title, lines):
        lists.append((title, list(lines)))
        real(speech, keys, title, lines)
    monkeypatch.setattr(menus, "_lines_picker", picker)
    league = market_league()
    rig = run(tmp_path, league, keys=FREE_AGENTS_IN_F9 + [ESC] * 4, until=lambda r: bool(lists))
    words = rig.fstore.words
    start = start_of(league)
    heard = M.interest(M.computer_bids(start, 1, skip=(TEAM,)))
    assert lists and lists[0][0] == X.text("NXF-29")
    assert lists[0][1] == [line_of(words, pl, 1, heard) for pl in M.pool(start)] and len(lists[0][1]) == len(M.pool(start))


def test_the_list_of_free_agents_is_empty_when_the_market_is_not_open():
    from nfl4.extras.franchise import market_flow
    from nfl4.extras.franchise.history import Words
    league = market_league()
    words = Words(lambda team: "team %d" % team)
    assert league.market is None and market_flow.market_lines(league, words) == []
    league.market = M.begin()
    assert len(market_flow.market_lines(league, words)) == len(M.pool(league))


def test_f9_says_the_market_is_closed_outside_the_stage(tmp_path):
    league = draft_league(stage_no=D.STAGE_DRAFT, team=TEAM)                    # at the draft, the question of the player's first pick is open when F9 is pressed
    rig = run(tmp_path, league, keys=FREE_AGENTS_IN_F9 + [ESC] * 4, until=lambda r: X.text("NXJ-H01") in spoken(r))
    assert X.text("NXJ-H01") in spoken(rig)


def test_the_franchise_menu_lists_the_free_agents_after_the_salary_cap(tmp_path, monkeypatch):
    from nfl4.game import spoken_menu
    seen = []
    real = spoken_menu.SpokenMenu.__init__

    def spy(self, speech, keys, title, items, *args, **kwargs):
        seen.append((title, [item.label() for item in items]))
        real(self, speech, keys, title, items, *args, **kwargs)
    monkeypatch.setattr(spoken_menu.SpokenMenu, "__init__", spy)
    run(tmp_path, market_league(), keys=[F9, DOWN, DOWN, DOWN, DOWN, ENTER, ESC, ESC, ESC], until=lambda r: any(t == "Franchise" for t, _ in seen))
    franchise = [labels for title, labels in seen if title == "Franchise"][0]
    assert franchise.index("free agents") == franchise.index("salary cap") + 1 and franchise[-1] == "play classic seasons"
