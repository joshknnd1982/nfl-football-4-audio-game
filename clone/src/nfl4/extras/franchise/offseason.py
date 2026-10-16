"""The offseason of a Franchise, the part SX.8a builds: stage 1 the season in review and stage 6 the new season (nfl4 only, rule 0.13).
This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 3.3. The stages are the data list `data.STAGES` (a later session inserts its own: SX.8c the retirements and
the development, SX.8d the draft and the roster cut). A stage speaks first, then makes its changes in one block and writes
league.sav, so closing the window at any wait loses nothing but the stage in progress: the next start resumes at that stage and
speaks it again from its start (design 3.3 item 4, invariant I10). Until SX.8c the year's aging is part of stage 6: every active
player is one year older, at most 40.

With the setting "offseason: short" a stage that needs no decision says its summary sentences and goes on without a key.
"""
from __future__ import annotations

from .. import nx_texts as X
from . import data as D
from . import history
from .league import OFFSEASON, SEASON, team_ref
from .question import wait_for_enter


def run(p) -> None:
    """The offseason from the stage the record says (a season that just ended, or a resumed offseason), to the new season. It
    stops early, with the record written, when a menu asked for another kind of season (design 3.1)."""
    from . import mode
    g, store = p.g, p.store
    league = store.league
    short = g.options.settings.game.nx_fr_offseason == "short"
    numbers = [number for number, _ in D.STAGES]
    if league.stage == SEASON:                           # the season is over: the finished season's values are kept
        store.sync()
        league.stage, league.stage_no = OFFSEASON, numbers[0]
        store.save()
    if league.stage_no == numbers[0]:
        g.say2(X.text("NXE-01"))
    while league.stage == OFFSEASON:
        number = league.stage_no
        index = numbers.index(number)
        RUNNERS[number](p, index + 1, len(numbers), short)
        if p.switch_requested:
            if mode.desired_kind(p) != "franchise":
                return                                   # the stage is written; the week loop makes the switch
            p.switch_requested = False


def _stage_line(n: int, m: int, name_id: str) -> str:
    return X.text("NXE-02", n=n, m=m, stage=X.text(name_id))


def stage_review(p, n: int, m: int, short: bool) -> None:
    """Stage 1: the champion, the team's record and finish, the best and the worst record, the coach's record; the season
    goes into the history and history.txt is written (design 9)."""
    g, store = p.g, p.store
    league = store.league
    words = store.words
    entry = history.build_entry(league)
    team = entry["team"] - 1
    lines = [] if short else [_stage_line(n, m, "NXE-11")]
    lines.append(X.text("NXE-20", champion=words.team_name(entry["champion"]), n=entry["season"]))
    lines.append(X.text("NXE-21", w=entry["wins"][team], l=entry["losses"][team], finish=words.finish(entry["finish"][team])))
    if short:
        for line in lines:
            g.say2(line)
    else:
        best, worst = entry["best"], entry["worst"]
        lines.append(X.text("NXE-28", best=words.team_name(best), best_w=entry["wins"][best - 1], best_l=entry["losses"][best - 1],
                            worst=words.team_name(worst), worst_w=entry["wins"][worst - 1], worst_l=entry["losses"][worst - 1]))
        career = history.career(history_with(league, entry))
        lines.append(X.text("NXE-29", n=career.seasons, w=career.wins, l=career.losses))
        lines.append(X.text("NXE-03"))
        wait_for_enter(g, lines)
    league.history.append(entry)
    league.results = []
    league.stage_no = _next_stage(D.STAGE_REVIEW)
    store.write_history()                                # history.txt first: a crash between leaves it ahead, never behind
    store.save()


def history_with(league, entry):
    """The record as it will be once the entry is added (for the coach's record, spoken before the entry is kept)."""
    import copy
    shown = copy.copy(league)
    shown.history = list(league.history) + [entry]
    return shown


def _next_stage(number: int) -> int:
    numbers = [n for n, _ in D.STAGES]
    return numbers[numbers.index(number) + 1]


def stage_new_season(p, n: int, m: int, short: bool) -> None:
    """Stage 6: the new season: everybody is a year older (until SX.8c), the schedule is made, week 1 is next."""
    g, store = p.g, p.store
    league = store.league
    season = g.season
    for player in league.players.values():
        if player.status == "active":
            player.age = min(D.AGE_MAX, player.age + 1)
            player.seasons += 1
            player.points = 0
    league.season += 1
    league.results = []
    league.sums = [league.strength_sum(t) for t in range(1, D.TEAMS + 1)]
    league.stage, league.stage_no = SEASON, 0
    league.told = [0, 0]
    season.reset_for_new_season()                        # the coach and the team stay
    season.coach = league.coach
    season.tn1, season.tn2 = team_ref(league.team)
    g.season_engine.player_won = False
    g.make_schedule()                                    # the original's makes draws; the store writes league.sav
    season.gtp = 1
    store.write_gtp(1)
    rating = history.team_rating_text(league)            # NXF-09: the team's rating and its number, after NXE-60 (design 14)
    if short:
        g.say2(X.text("NXE-60", n=league.season))
        g.say2(rating)
    else:                                                # design 3.3: every stage ends with NXE-03 (the league is saved already)
        wait_for_enter(g, [_stage_line(n, m, "NXE-16"), X.text("NXE-60", n=league.season), rating, X.text("NXE-61"),
                           X.text("NXE-03")])


RUNNERS = {D.STAGE_REVIEW: stage_review, D.STAGE_NEW_SEASON: stage_new_season}
