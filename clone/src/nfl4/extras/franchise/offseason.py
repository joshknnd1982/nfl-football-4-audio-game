"""The offseason of a Franchise: stage 1 the season in review (SX.8a), 2 the retirements and 3 the player development (SX.8c),
4 the draft and 5 the roster cut with the fill (SX.8d, `draft_flow.py`), 6 the new season (nfl4 only, rule 0.13). This is inspired by
Jim Kitchen.

NFL_FRANCHISE_DESIGN 3.3. The stages are the data list `data.STAGES` (a later session inserts its stage). Stage 1 speaks
and waits first and makes its changes after the wait (the season's results stay in the file until then). Stages 2 and 3 make
their draws (`extras\\franchise\\aging.py` plans without changing anything), work the spoken lines out from the plan, change the
league and write league.sav, and only then speak and wait: the roster and the ratings the player may open in F9 at the wait are what
the stage just said, and a window closed at the wait resumes at the next stage (design 3.3 item 4, invariant I10; a stage is
idempotent until its save, B-X51).

With the setting "offseason: short" a stage that needs no decision says its summary sentences and goes on without a key.
"""
from __future__ import annotations

from .. import nx_texts as X
from . import aging
from . import data as D
from . import draft_flow
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


def stage_retirements(p, n: int, m: int, short: bool) -> None:
    """Stage 2: everybody is a year older, then the retirements (design 6.1, 6.3): the player's team's by name, the other teams'
    stars (at most three, the highest peak first, equal peaks in league order) by name, the count of the league. The draws are
    made and the lines worked out from the plan, then the players are changed and the league is saved, then the stage speaks and
    waits: the roster and the ratings in F9 at the wait are what the stage just said (review finding 3 of SX.8c), and a window
    closed at the wait resumes at the next stage. The news lines NWR are SX.8e's."""
    g, store = p.g, p.store
    league = store.league
    words = store.words
    retiring = aging.plan_retirements(league, g.rnd)
    own = [player for player in retiring if player.team == league.team]
    stars = sorted((player for player in retiring if player.team != league.team and player.peak >= D.STAR_PEAK),
                   key=lambda player: -player.peak)[:D.STARS_NAMED]                    # sorted keeps the league order of equals
    lines = [_stage_line(n, m, "NXE-12")]
    if own:
        lines.append(X.text("NXE-30"))
        lines += [X.text("NXE-31", player=player.name, position=words.position(player.pos), a=aging.aged(player),
                         r=player.rating, n=player.seasons + 1) for player in own]
    else:
        lines.append(X.text("NXE-32"))
    lines.append(X.text("NXE-33", n=len(retiring)))
    lines += [X.text("NXE-35", player=player.name, team=words.team_name(player.team), position=words.position(player.pos),
                      n=player.seasons + 1) for player in stars]
    lines.append(X.text("NXE-03"))
    short_line = X.text("NXE-71", n=len(retiring), m=len(own))
    aging.apply_aging(league, retiring)
    league.stage_no = _next_stage(D.STAGE_AGING)
    store.save()
    if short:
        g.say2(short_line)
    else:
        wait_for_enter(g, lines)


def stage_development(p, n: int, m: int, short: bool) -> None:
    """Stage 3: progression and regression of every player (design 6.2): the player's team's counts, its most improved and its
    biggest drop. The development points go back to 0. The empty places of the retirements stay empty until the roster cut
    fills them (stage 5, SX.8d). The news lines NWP are SX.8e's. As in stage 2 the league is changed and saved before the stage speaks
    and waits."""
    g, store = p.g, p.store
    league = store.league
    words = store.words
    plan = aging.plan_development(league, g.rnd)
    summary = aging.summarize(plan, league.team)
    lines = [_stage_line(n, m, "NXE-13"), X.text("NXE-40", n=summary.improved, m=summary.declined, k=summary.same)]
    for text_id, change in (("NXE-41", summary.best), ("NXE-42", summary.worst)):
        if change is not None:
            lines.append(X.text(text_id, player=change.player.name, position=words.position(change.player.pos),
                                d=abs(change.delta), r=change.new))
    lines += [X.text("NXE-43"), X.text("NXE-03")]
    short_line = X.text("NXE-72", n=summary.improved, m=summary.declined)
    aging.apply_development(plan)
    league.stage_no = _next_stage(D.STAGE_DEVELOPMENT)
    store.save()
    if short:
        g.say2(short_line)
    else:
        wait_for_enter(g, lines)


def stage_new_season(p, n: int, m: int, short: bool) -> None:
    """Stage 6: the new season: the retired and released players history does not need are dropped, the schedule is made, week 1
    is next. (The year's aging is stage 2's since SX.8c.)"""
    g, store = p.g, p.store
    league = store.league
    season = g.season
    aging.drop_the_unkept(league)
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


RUNNERS = {D.STAGE_REVIEW: stage_review, D.STAGE_AGING: stage_retirements, D.STAGE_DEVELOPMENT: stage_development,
           D.STAGE_DRAFT: draft_flow.stage_draft, D.STAGE_CUT: draft_flow.stage_cut, D.STAGE_NEW_SEASON: stage_new_season}
