"""The game's later items in the program (nfl4 only, rule 0.13; NFL_FRANCHISE_DESIGN 17 SX.8o, D-076), on the program rig (tests/frrig.py): the games are
counted in every week's preparation and week 16's at the season's end, stage 1 says the season's awards and keeps them (and the hall's class) after its wait,
once, the counts end at stage 6, and F9's league history has the awards and the hall of fame.
"""
from frrig import COACH_AND_TEAM, WANT_FRANCHISE, enter_until, franchise_rig, run_until, spoken
from test_fr_mode import at_week_lambda, settings_of

from nfl4.extras import nx_texts as X
from nfl4.extras.franchise import honors as H
from nfl4.extras.franchise import workload as W


def test_a_season_counts_its_games_says_its_awards_at_stage_one_and_keeps_them(tmp_path, monkeypatch):
    counted = []
    real = W.count_games

    def spy(league, week, staff=True):
        counted.append((league.season, week))
        return real(league, week, staff)
    monkeypatch.setattr(W, "count_games", spy)
    kept = []
    real_apply = H.apply

    def apply_spy(league, rows, inducted):
        kept.append((league.season, [row[1] for row in rows]))
        return real_apply(league, rows, inducted)
    monkeypatch.setattr(H, "apply", apply_spy)
    rig = franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM, policy=enter_until(at_week_lambda(lambda: rig, 2, 1)))
    run_until(rig)
    league = rig.fstore.league
    assert counted == [(1, week) for week in range(1, 17)]                  # weeks 1 to 15 in the preparations, week 16 when the season ends
    assert kept == [(1, [row[1] for row in league.honors["awards"]])] and kept[0][1][-1] == "coy"     # applied once, after stage 1's wait
    text = spoken(rig)
    assert text.count(X.text("NXG-B01")) == 1
    first = text.index(X.text("NXG-B01"))
    assert all(H.AWARD_TEXT[row[1]] and X.text(H.AWARD_TEXT[row[1]]) in " ".join(text[first:first + 7]) for row in league.honors["awards"])
    assert len(league.honors["awards"]) == 5                               # every award has a winner in a whole season
    assert league.usage == W.empty(1) and league.season == 2                # the counts ended at stage 6 (the season they belonged to)


def test_the_short_offseason_says_the_most_valuable_player(tmp_path):
    rig = franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM, policy=enter_until(at_week_lambda(lambda: rig, 2, 1)))
    settings_of(rig).nx_fr_offseason = "short"
    run_until(rig)
    league = rig.fstore.league
    mvp = [row for row in league.honors["awards"] if row[1] == "mvp"]
    text = spoken(rig)
    assert X.text("NXG-B01") not in text
    assert mvp and sum(X.text("NXG-A01") in line for line in text) == 1
