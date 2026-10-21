"""The offseason of a Franchise: stage 1 the season in review (SX.8a), 9 the staff right after it (SX.8l, `staff_flow.py`), 2 the retirements and 3 the player development (SX.8c),
4 the draft and 5 the roster cut with the fill (SX.8d, `draft_flow.py`), 6 the new season, 7 the expiring contracts (SX.8h,
`resign_flow.py`) and 8 free agency (SX.8i, `market_flow.py`; the two sit between 3 and 4) (nfl4 only, rule 0.13). This is inspired by
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
from .. import tuning as T
from . import aging
from . import camp
from . import comp
from . import data as D
from . import tags
from . import draft_flow, market_flow, people_flow, resign_flow, staff_flow
from . import people
from . import history, honors, honors_flow, injuries, news, staff, trades, weekly, workload
from .league import OFFSEASON, SEASON, team_ref
from .news_pools import DEFAULT_POOLS
from .question import FranchiseQuestion, wait_for_enter


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
        workload.count_games(league, D.REGULAR_WEEKS, bool(g.options.settings.game.nx_fr_auto))   # SX.8o: the games of week 16 (weeks 1 to 15: the preparations)
        injuries.end_of_season(league)                   # SX.8k: every player is fit for the next season (in the step that ends the season)
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
    pools = g.news_pools or DEFAULT_POOLS
    told, recent = news.render(league, [news.champion_event(entry["season"], entry["champion"])], pools, words, g.rnd)
    lines = [] if short else [_stage_line(n, m, "NXE-11")]
    lines.append(X.text("NXE-20", champion=words.team_name(entry["champion"]), n=entry["season"]))
    tied = history.ties_of(entry)                        # SX.12: the ties of the 2026 overtime (said only when a team has one)
    lines.append(X.text("NXE-21", w=entry["wins"][team], l=history.losses_and_ties(entry["losses"][team], tied[team]),
                        finish=words.finish(entry["finish"][team])))
    lines += staff_flow.verdict_lines(league, entry["wins"], entry["finish"])     # SX.8l: the owner's goal and the job rating (kept after the wait)
    awards, inducted = honors.stage_one(league, entry["wins"], entry["finish"])    # SX.8o: the season's awards and the hall's class (kept after the wait)
    honor_lines = honors_flow.stage_lines(league, words, awards, inducted)
    if short:
        for line in lines + honors_flow.short_lines(league, words, awards, inducted):
            g.say2(line)
    else:
        best, worst = entry["best"], entry["worst"]
        lines.append(X.text("NXE-28", best=words.team_name(best), best_w=entry["wins"][best - 1],
                            best_l=history.losses_and_ties(entry["losses"][best - 1], tied[best - 1]),
                            worst=words.team_name(worst), worst_w=entry["wins"][worst - 1],
                            worst_l=history.losses_and_ties(entry["losses"][worst - 1], tied[worst - 1])))
        career = history.career(history_with(league, entry))
        lines.append(X.text("NXE-29", n=career.seasons, w=career.wins, l=history.losses_and_ties(career.losses, career.ties)))
        lines += _news_texts(told)
        lines += honor_lines
        lines.append(X.text("NXE-03"))
        wait_for_enter(g, lines)
    staff.apply_verdicts(league, entry["wins"], entry["finish"])     # SX.8l: every coach's job rating, the season his firing is judged by
    honors.apply(league, awards, inducted)               # SX.8o
    league.history.append(entry)
    league.results = []
    news.keep(league, told, recent, D.NEWS_OFFSEASON)     # the champion's line: kept after the wait with the rest of the stage
    league.stage_no = _next_stage(D.STAGE_REVIEW)
    store.write_history()                                # history.txt first: a crash between leaves it ahead, never behind
    store.save()


def _news_texts(rendered: list) -> list:
    """The words of the offseason's news lines for a stage's list of lines (the stage's lines are plain sentences; a sound or a
    pause of a player's own line is for the weekly news and the lists of F9)."""
    return [text for text in (weekly.plain_text(markup) for _pool, markup in rendered) if text]


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
    told, recent = news.render(league, news.star_events(stars), g.news_pools or DEFAULT_POOLS, words, g.rnd)    # NWR, after the draws
    lines += _news_texts(told)
    lines.append(X.text("NXE-03"))
    short_line = X.text("NXE-71", n=len(retiring), m=len(own))
    aging.apply_aging(league, retiring)
    news.keep(league, told, recent, D.NEWS_OFFSEASON)
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
    header = _stage_line(n, m, "NXE-13")
    held, rest = people_flow.holdouts(p, header)            # SX.8n: the holdouts at the start of camp, settled and written before they are told
    choice, asked = camp_choice(g, league, None if held else header, rest)    # SX.8m: the camp's focus, asked before anything changes
    if asked:
        rest = []
    camp_lines = []
    if camp.in_use():
        camps = camp.apply(league, {league.team: choice} if choice else {})       # every team's camp points (the computer teams' focus by the same rule)
        focus, picked = camps[league.team]
        camp_lines.append(X.text("NXU-02", focus=X.text(camp.FOCUS_TEXT[focus]), list=", ".join(pl.name for pl in picked)) if picked
                          else X.text("NXU-03", focus=X.text(camp.FOCUS_TEXT[focus])))
    plan = aging.plan_development(league, g.rnd)
    summary = aging.summarize(plan, league.team)
    lines = ([] if asked or held else [header]) + rest + camp_lines + [X.text("NXE-40", n=summary.improved, m=summary.declined, k=summary.same)]
    for text_id, change in (("NXE-41", summary.best), ("NXE-42", summary.worst)):
        if change is not None:
            lines.append(X.text(text_id, player=change.player.name, position=words.position(change.player.pos),
                                d=abs(change.delta), r=change.new))
    told, recent = news.render(league, news.improver_events(plan, league.team), g.news_pools or DEFAULT_POOLS, words, g.rnd)   # NWP
    lines += _news_texts(told)
    lines += [X.text("NXE-43"), X.text("NXE-03")]
    short_line = X.text("NXE-72", n=summary.improved, m=summary.declined)
    aging.apply_development(plan)
    news.keep(league, told, recent, D.NEWS_OFFSEASON)
    league.stage_no = _next_stage(D.STAGE_DEVELOPMENT)
    store.save()
    if short:
        for line in rest + camp_lines:
            g.say2(line)
        g.say2(short_line)
    else:
        wait_for_enter(g, lines)


def camp_choice(g, league, header, before=()) -> tuple:
    """(the player's focus or None for the staff's, whether he was asked): the staff's recommendation is the first answer; with the staff handling the
    to-do list the staff's focus is taken without a question (SX.8m). `header`: the stage's line (None when a holdout question said it, SX.8n); `before`: lines
    still to say (the league's holdouts), said with the question."""
    if g.options.settings.game.nx_fr_auto or not camp.in_use():
        return None, False
    recommended = camp.recommend(league, league.team)
    foci = [recommended] + [focus for focus in T.FR_CAMP_FOCI if focus != recommended]
    situation = ([header] if header else []) + list(before) + [X.text("NXU-01", focus=X.text(camp.FOCUS_TEXT[recommended]))]
    answer = FranchiseQuestion(g, situation, [X.text(camp.FOCUS_TEXT[focus]) for focus in foci]).ask()
    return foci[answer], True


def stage_new_season(p, n: int, m: int, short: bool) -> None:
    """Stage 6: the new season: the retired and released players history does not need are dropped, the schedule is made, week 1
    is next. (The year's aging is stage 2's since SX.8c.)"""
    g, store = p.g, p.store
    league = store.league
    season = g.season
    trades.new_season(league)                            # SX.8j: the season's trades are history (before the players they name may be dropped)
    workload.new_season(league)                          # SX.8o: the season's games and carries are over (before the players they name may be dropped)
    aging.drop_the_unkept(league)
    news.drop_for_new_season(league)                     # the finished season's weekly news goes; its offseason's stays
    league.season += 1
    comp.drop_past(league)                               # SX.8m: the compensatory picks of the draft that is over
    tags.move_future(league)                             # SX.8m: the first-round picks owed for this season's draft join its table
    tags.close(league)
    people.new_season(league)                            # SX.8n: the morale halved, the season's demands and goals over
    league.results = []
    league.sums = [league.strength_sum(t) for t in range(1, D.TEAMS + 1)]
    staff.set_goals(league)                              # SX.8l: the owner's goal of every team by its rank at the season's start
    league.stage, league.stage_no = SEASON, 0
    league.told = [0, 0]
    league.prepared = [0, 0]
    season.reset_for_new_season()                        # the coach and the team stay
    season.coach = league.coach
    season.tn1, season.tn2 = team_ref(league.team)
    g.season_engine.player_won = False
    g.make_schedule()                                    # the original's makes draws; the store writes league.sav
    season.gtp = 1
    store.write_gtp(1)
    rating = history.team_rating_text(league)            # NXF-09: the team's rating and its number, after NXE-60 (design 14)
    goal = staff_flow.goal_line(league)                  # SX.8l: the owner's goal of the coming season
    if short:
        g.say2(X.text("NXE-60", n=league.season))
        g.say2(rating)
        g.say2(goal)
    else:                                                # design 3.3: every stage ends with NXE-03 (the league is saved already)
        wait_for_enter(g, [_stage_line(n, m, "NXE-16"), X.text("NXE-60", n=league.season), rating, goal, X.text("NXE-61"),
                           X.text("NXE-03")])


RUNNERS = {D.STAGE_REVIEW: stage_review, D.STAGE_STAFF: staff_flow.stage_staff, D.STAGE_AGING: stage_retirements, D.STAGE_DEVELOPMENT: stage_development,
           D.STAGE_CONTRACTS: resign_flow.stage_contracts, D.STAGE_FREE_AGENCY: market_flow.stage_free_agency,
           D.STAGE_DRAFT: draft_flow.stage_draft, D.STAGE_CUT: draft_flow.stage_cut, D.STAGE_NEW_SEASON: stage_new_season}
