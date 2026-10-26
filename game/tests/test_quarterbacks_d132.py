"""Every team's quarterbacks and the starter the player chooses (nfl4 only, rule 0.13; D-132, the owner's answer to Q-065: "List and choose"). This is
inspired by Jim Kitchen.

F9, Rules, Quarterbacks. Outside a franchise: the real rosters' quarterbacks of the 32 teams, the first one starting; Enter on one makes him the starter
from the next game (the setting nx_qb_starters, by the written name; a game, its Getqbs default and a new franchise use him). In a franchise: the
league's quarterbacks, the roster's starter and the practice squad's; on the player's own team a squad quarterback can become the starter (he signs to
the roster for the minimum and the starter is released, the practice squad's move with its confirmation).
"""
from frrig import COACH_AND_TEAM, WANT_FRANCHISE, franchise_rig, quit_policy, run_until, spoken
from programrig import DOWN, ENTER, ESC, said
from test_functions import rig_for

from nfl4.data import settingsfile
from nfl4.data.settings import Settings
from nfl4.extras import nx_texts as X
from nfl4.extras import quarterbacks as Q
from nfl4.extras import real_names as R
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import practice as P

BENGALS, RAVENS = 1, 3
F9 = 120
RULES = [DOWN, DOWN, DOWN, ENTER]                        # F9's fourth item
QUARTERBACKS = [DOWN] * 12 + [ENTER]                       # the Rules menu's thirteenth item, before Reset


def shipped():
    R.reset_defaults_cache()
    return R.defaults()


# ----- the choices and the names -----

def test_the_setting_is_read_and_written_as_team_and_name_and_a_bad_part_is_dropped():
    assert Q.parse_choices("T01=Joe Flacco; T3 = Tyler Huntley;;T40=Nobody; X=Y; T05=") == {1: "Joe Flacco", 3: "Tyler Huntley"}
    assert Q.render_choices({3: "Tyler Huntley", 1: "Joe Flacco"}) == "T01=Joe Flacco; T03=Tyler Huntley"
    assert Q.clean("T03=Tyler Huntley; junk") == "T03=Tyler Huntley" and Q.clean("") == ""


def test_settings_txt_keeps_the_choice_and_a_line_that_is_not_one_is_a_problem():
    settings = Settings.defaults()
    settings.game.nx_qb_starters = "T01=Joe Flacco"
    text = settingsfile.render(settings)
    assert "nx_qb_starters = T01=Joe Flacco\n" in text
    again, problems = settingsfile.parse(text)
    assert again.game.nx_qb_starters == "T01=Joe Flacco" and problems == []
    bad, problems = settingsfile.parse(settingsfile.HEADER + "nx_qb_starters = whoever\n")
    assert bad.game.nx_qb_starters == "" and len(problems) == 1


def test_the_chosen_starter_takes_the_first_quarterback_line_and_the_others_keep_their_order():
    real = shipped()
    names = [p.name for p in Q.quarterbacks_of(real, BENGALS)]
    assert names[:2] == ["Joe Burrow", "Joe Flacco"]
    moved = Q.with_starters(real, {BENGALS: "joe flacco"})                      # the written name, in any case
    assert [p.name for p in Q.quarterbacks_of(moved, BENGALS)][:2] == ["Joe Flacco", "Joe Burrow"]
    assert moved.quarterback(BENGALS) == "Joe Flacco" and real.quarterback(BENGALS) == "Joe Burrow"
    assert moved.rosters[RAVENS - 1] == real.rosters[RAVENS - 1]                 # the other teams are as they were
    others = [p for p in real.rosters[BENGALS - 1] if p.pos != "QB"]
    assert [p for p in moved.rosters[BENGALS - 1] if p.pos != "QB"] == others


def test_a_choice_whose_player_is_not_on_the_team_is_left_out():
    real = shipped()
    assert Q.with_starters(real, {BENGALS: "Lamar Jackson"}).quarterback(BENGALS) == "Joe Burrow"


def test_a_game_with_the_real_names_names_the_chosen_starter_and_a_new_franchise_gives_him_its_place():
    real = Q.with_starters(shipped(), {BENGALS: "Joe Flacco"})
    roster = real.roster(BENGALS)
    assert "Joe Flacco" not in roster.receivers and "Joe Burrow" not in roster.running_backs
    places = real.places(BENGALS)
    assert places[D.PLACES_OF["QB"][0]] == "Joe Flacco"


# ----- F9, Rules, Quarterbacks outside a franchise -----

def nfl_rig(tmp_path, keys):
    rig = rig_for(tmp_path, [])
    rig.game.options.settings.game.rules = "nfl"
    rig.game.real_names = shipped()
    rig.keys.answers = RULES + QUARTERBACKS + keys + [ESC, ESC]
    rig.game.functions.run()
    return rig


def test_the_list_says_each_teams_starter_and_the_men_behind_him(tmp_path):
    rig = nfl_rig(tmp_path, [ESC])
    text = said(rig)
    assert any(X.text("NXJ-Q01").strip() in line for line in text)
    bengals = rig.game.league.team(1, 1)
    assert any(line.endswith(X.text("NXJ-Q02", team=bengals, player="Joe Burrow") + X.text("NXJ-Q03", list="Joe Flacco")) for line in text)


def test_enter_on_a_quarterback_makes_him_the_starter_saves_it_and_the_next_game_uses_him(tmp_path):
    rig = nfl_rig(tmp_path, [ENTER, DOWN, ENTER, ESC])                         # the Bengals, their second quarterback
    settings = rig.game.options.settings.game
    assert settings.nx_qb_starters == "T01=Joe Flacco" and rig.saves.count == 1
    assert rig.game.real_names.quarterback(BENGALS) == "Joe Flacco"
    assert X.text("NXJ-Q08", player="Joe Flacco", team=rig.game.league.team(1, 1)) in said(rig)


def test_choosing_the_rosters_own_first_quarterback_again_keeps_no_choice(tmp_path):
    rig = rig_for(tmp_path, [])
    rig.game.options.settings.game.rules = "nfl"
    rig.game.options.settings.game.nx_qb_starters = "T01=Joe Flacco"
    rig.game.real_names = Q.with_starters(shipped(), {BENGALS: "Joe Flacco"})
    rig.keys.answers = RULES + QUARTERBACKS + [ENTER, DOWN, ENTER, ESC, ESC, ESC]      # Burrow is second now
    rig.game.functions.run()
    assert rig.game.options.settings.game.nx_qb_starters == "" and rig.game.real_names.quarterback(BENGALS) == "Joe Burrow"


def test_enter_on_the_starter_says_he_already_starts(tmp_path):
    rig = nfl_rig(tmp_path, [ENTER, ENTER, ESC])
    assert X.text("NXJ-Q09", player="Joe Burrow", team=rig.game.league.team(1, 1)) in said(rig)
    assert rig.game.options.settings.game.nx_qb_starters == "" and rig.saves.count == 0


def test_with_the_classic_rules_the_item_says_the_real_players_come_with_the_nfl_rules(tmp_path):
    rig = rig_for(tmp_path, [])
    rig.keys.answers = RULES + QUARTERBACKS + [ESC, ESC]
    rig.game.functions.run()
    text = said(rig)
    assert X.text("NXM-58") + X.text("NXM-22") in text and X.text("NXJ-Q20") in text


# ----- in a franchise -----

FRANCHISE_QBS = [F9] + RULES + QUARTERBACKS                                  # the list starts on the player's own team


def test_in_a_franchise_the_list_has_the_rosters_starter_and_the_practice_squads_quarterbacks(tmp_path):
    rig = franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM + FRANCHISE_QBS + [ESC, ESC, ESC, ESC], practice=True, policy=quit_policy)
    run_until(rig)
    league = rig.fstore.league
    first = league.player_at(league.team, D.PLACES_OF["QB"][0])
    squad = [p for p in P.squad(league, league.team) if p.pos == "QB"]
    assert squad, "a new franchise's squad has a quarterback (practice.TEMPLATE)"
    line = X.text("NXJ-Q12", team=rig.fstore.words.team_name(league.team), player=first.name, r=first.rating, a=first.age)
    assert any(line in text for text in spoken(rig))


def test_on_his_own_team_the_player_makes_a_squad_quarterback_the_starter_and_the_starter_goes_to_the_bench(tmp_path):
    # SR.5 (D-164, D-149): a team has room under 53 in every league now (no "reserves_on" switch), so the squad quarterback signs to the roster
    # for the minimum and starts (the first of the QB chart) and the old starter is the second of the chart, on the bench: nobody is released
    rig = franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM + FRANCHISE_QBS + [ENTER, DOWN, ENTER, ENTER, ESC, ESC, ESC, ESC],
                        practice=True, policy=quit_policy)
    run_until(rig)
    league = rig.fstore.league
    now = league.player_at(league.team, D.PLACES_OF["QB"][0])
    assert now.status == "active" and now.years == 1 and not [p for p in P.squad(league, league.team) if p.id == now.id]
    chart = league.chart[league.team - 1]["QB"]
    assert chart[0] == now.id and len(chart) >= 2
    old = league.players[chart[1]]
    assert old.status == "active" and old.team == league.team and old in league.bench(league.team, "QB")
    assert not [p for p in league.players.values() if p.status == "free" and p.left == league.season and p.pos == "QB"]
    assert any(X.text("NXJ-P08", player=now.name) + X.text("NXL-58", player=now.name, other=old.name) in t for t in spoken(rig))
    league.check()
