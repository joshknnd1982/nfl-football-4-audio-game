"""The staff of a Franchise: the head coaches with their job rating and the owner's goal, the coordinators (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 17 SX.8l (F9, N6.8; research B8, B9, G; D-072). Rules over the league record, no speech and no files; the only draws are the
candidates for an open coordinator's place, made with the one GameRandom handed in. The program's stage (`staff_flow.py`) and the fast run call these very
functions, so the computer teams and the player's team are judged, fired and staffed in one code path.

`league.staff` (league.sav format 7):

    {"coaches": [32 x {"name", "approval", "seasons", "goal": [kind, n], "last": [wins, finish, met, approval before] or None}],
     "coordinators": [32 x [offense, defense]], each {"name", "style", "rating", "seasons"},
     "stage": None, or the stage in progress (see `begin`)}

The player's team's head coach is the player (`league.coach`; the name in its record is not spoken). A place may be None (open) only while the stage is in progress.

* The season's end (stage 1): `verdicts` works out every coach's goal and new job rating from the season (pure), `apply_verdicts` keeps them.
* The stage "the staff" (stage 9, right after stage 1): `begin` fires the coaches the rule fires (a job rating under FR_FIRE_BELOW, NEVER after a winning
  season) and, when the player is one of them, makes his offers (`offers`: never the team that fired him); `take_job`; `hire_head_coaches` (every open head
  coach's place takes the best coordinator of the league, and a new head coach brings his own coordinators); `own_sides` (the player's own choice, or the
  staff's rule when the staff handles his team); `draw_candidates` (three for every open coordinator's place; the computer teams take the best); `hire`;
  `finish`.
* The season's start (stage 6, a new league): `set_goals` by the team's rank of the exact strengths.
* The games: `team_styles` is every team's (offense style, defense style), the coordinators' (the playbooks, design 10), and `recommended` the staff's
  game plan of a side (design 8.1 T2).
"""
from __future__ import annotations

from .. import playbook_data as PD
from .. import tuning as T
from . import data as D
from .league import LeagueError, draw_name

STYLE_KEYS = tuple(s.key for s in PD.STYLES)          # what a candidate's style is drawn from (below(7)); a new league's coordinators may also have Classic
SIDES = (0, 1)                                        # 0 the offensive coordinator, 1 the defensive coordinator
GOAL_WINS, GOAL_PLAYOFFS, GOAL_TITLE_GAME = "wins", "playoffs", "title_game"
GOAL_KINDS = (GOAL_WINS, GOAL_PLAYOFFS, GOAL_TITLE_GAME)
STEP_JOB, STEP_COACHES, STEP_OWN, STEP_DRAW, STEP_PICK = "job", "coaches", "own", "draw", "pick"
STEPS = (STEP_JOB, STEP_COACHES, STEP_OWN, STEP_DRAW, STEP_PICK)
OFFENSE_POSITIONS, DEFENSE_POSITIONS = ("QB", "RB", "WR"), ("DL", "LB", "CB", "S")
NAME_STRIDE = 13                                      # a new league's staff is named by a walk through the surnames (no draw): 13 and 1,708 have no common factor
STAGE_KEYS = {"step", "fired", "old_team", "approval", "offers", "let_go", "hired", "lost", "replaced", "candidates", "new"}


# ----- the records -----

def new_coach(name: str) -> dict:
    return {"name": name, "approval": T.FR_APPROVAL_START, "seasons": 0, "goal": [GOAL_WINS, D.REGULAR_WEEKS // 2], "last": None}


def new_coordinator(name: str, style: str, rating: int) -> dict:
    return {"name": name, "style": style, "rating": rating, "seasons": 0}


def coach_of(league, team: int):
    return league.staff["coaches"][team - 1]


def coordinator_of(league, team: int, side: int):
    return league.staff["coordinators"][team - 1][side]


def winning(wins: int) -> bool:
    """A winning season: more wins than losses in the 16 games of the regular season (the original has no ties)."""
    return wins > D.REGULAR_WEEKS // 2


# ----- a new league (and a league of an older format: no draw) -----

def side_rating(league, team: int, side: int) -> int:
    """A new league's coordinator is rated by the side of the ball he coaches: the mean rating of its players (rounded half up); 70 when it has none."""
    positions = OFFENSE_POSITIONS if side == 0 else DEFENSE_POSITIONS
    ratings = [p.rating for p in league.active_of(team) if p is not None and p.pos in positions]
    if not ratings:
        return D.RATING_NEUTRAL
    return max(D.RATING_MIN, min(D.RATING_MAX, (2 * sum(ratings) + len(ratings)) // (2 * len(ratings))))


def _walked_names(league, surnames: list, count: int) -> list:
    """`count` names for a new staff without a draw: a walk through the surnames from a place the league's strengths decide, every NAME_STRIDE-th
    name, skipping the names of active players and names already given (then the pool's order; a duplicate only when the pool is used up)."""
    used = {p.name for p in league.players.values() if p.status == "active"} | {league.coach}
    n = len(surnames)
    out = []
    if n:
        start = sum(league.strength_sum(t) for t in range(1, D.TEAMS + 1)) % n
        for index in [(start + k * NAME_STRIDE) % n for k in range(n)] + list(range(n)):
            if len(out) == count:
                break
            name = surnames[index]
            if name not in used and 1 <= len(name) <= 40:
                used.add(name)
                out.append(name)
    while len(out) < count:
        out.append(surnames[len(out) % n] if n else "Coach")
    return out


def new_staff(league, surnames: list, team_styles=PD.TEAM_STYLES) -> None:
    """The staff of a new league: every team's head coach (the player's team's is the player), its two coordinators with the styles of `team_styles` (the
    playbooks' assignment of the teams) rated by the sides of their rosters, the goals of season 1. No draw. The player is new to his team (the job rating
    FR_APPROVAL_START, his season of grace); the other teams' coaches have served for a while with different standing (`league_start`), so the grace of
    32 new coaches does not end in one offseason (the independent review: 13 of 32 fired in a new league's second offseason)."""
    names = iter(_walked_names(league, surnames, 3 * D.TEAMS))
    coaches, coordinators = [], []
    for team in range(1, D.TEAMS + 1):
        head = next(names)
        if team == league.team:
            coaches.append(new_coach(league.coach))
        else:
            coach = new_coach(head)
            coach["approval"], coach["seasons"] = league_start(team)
            coaches.append(coach)
        styles = team_styles[team - 1] if team - 1 < len(team_styles) else (PD.CLASSIC_KEY, PD.CLASSIC_KEY)
        pair = []
        for side in SIDES:
            style = styles[side] if styles[side] in PD.BOOK_KEYS else PD.CLASSIC_KEY
            pair.append(new_coordinator(next(names), style, side_rating(league, team, side)))
        coordinators.append(pair)
    league.staff = {"coaches": coaches, "coordinators": coordinators, "stage": None}
    set_goals(league)


def league_start(team: int) -> tuple:
    """(job rating, seasons with the team) of a computer team's head coach in a new league: past his grace, the rating spread over FR_APPROVAL_LEAGUE_START
    by a walk over the team numbers (no draw)."""
    base, span, stride = T.FR_APPROVAL_LEAGUE_START
    return base + (team * stride) % span, T.FR_FIRE_GRACE + 1


def migrate(league) -> None:
    """A league.sav of format 6 or older has no staff: it gets a new league's staff (no draw), named from the shipped surnames."""
    from ...game.names import load_surnames
    try:
        surnames = load_surnames()
    except OSError:
        surnames = []
    try:
        new_staff(league, surnames)
    except (AttributeError, KeyError, TypeError, ValueError, IndexError) as exc:
        raise LeagueError("the staff of an older franchise file could not be made: %s" % exc) from exc


# ----- the owner's goal -----

def goal_for(rank: int) -> list:
    for last, kind, number in T.FR_GOALS:
        if rank <= last:
            return [kind, number]
    return [GOAL_WINS, 0]


def set_goals(league) -> None:
    """Every team's goal for the coming season by its rank of the exact strengths (design 4.4), at the season's start."""
    for rank, team in enumerate(league.ranking(), start=1):
        coach = coach_of(league, team)
        if coach is not None:
            coach["goal"] = goal_for(rank)


def goal_met(goal: list, wins: int, finish: int) -> bool:
    kind, number = goal
    if kind == GOAL_WINS:
        return wins >= number
    if kind == GOAL_PLAYOFFS:
        return finish >= D.FINISH_WILD_CARD
    return finish >= D.FINISH_CHAMPIONSHIP


# ----- the season's end: the verdict (stage 1) -----

def new_approval(approval: int, goal: list, wins: int, finish: int) -> tuple:
    """(the job rating after the season, the goal met): the goal (FR_APPROVAL_GOAL), the wins against 8 (FR_APPROVAL_PER_WIN) and the finish
    (FR_APPROVAL_FINISH), the sum kept in 0 to 100."""
    met = goal_met(goal, wins, finish)
    change = (T.FR_APPROVAL_GOAL[0] if met else -T.FR_APPROVAL_GOAL[1]) + T.FR_APPROVAL_PER_WIN * (wins - D.REGULAR_WEEKS // 2) + T.FR_APPROVAL_FINISH[finish]
    return max(0, min(100, approval + change)), met


def verdicts(league, wins: list, finish: list) -> list:
    """Every team's (approval before, approval after, goal met), worked out from the season and changing nothing (stage 1 speaks before it keeps them)."""
    out = []
    for team in range(1, D.TEAMS + 1):
        coach = coach_of(league, team)
        after, met = new_approval(coach["approval"], coach["goal"], wins[team - 1], finish[team - 1])
        out.append((coach["approval"], after, met))
    return out


def apply_verdicts(league, wins: list, finish: list) -> None:
    """The season is judged: every coach's new job rating, his season's record kept for the firing rule, a season more for every coach and coordinator."""
    for team, (before, after, met) in enumerate(verdicts(league, wins, finish), start=1):
        coach = coach_of(league, team)
        coach["last"] = [wins[team - 1], finish[team - 1], int(met), before]
        coach["approval"] = after
        coach["seasons"] += 1
        for side in SIDES:
            coordinator_of(league, team, side)["seasons"] += 1


def is_fired(coach: dict) -> bool:
    """The rule (research G): a job rating under FR_FIRE_BELOW after the season, never after a winning season, and never after his first FR_FIRE_GRACE
    seasons with the team."""
    last = coach["last"]
    return last is not None and coach["approval"] < T.FR_FIRE_BELOW and not winning(last[0]) and coach["seasons"] > T.FR_FIRE_GRACE


def had_winning_season(coach: dict) -> bool:
    """His last season judged was a winning one (a coach with no season judged yet had none)."""
    return coach["last"] is not None and winning(coach["last"][0])


def in_danger(approval: int) -> bool:
    return approval < T.FR_FIRE_BELOW + T.FR_DANGER


# ----- the stage "the staff" -----

def begin(league) -> dict:
    """The stage starts (no draw): every head coach the rule fires leaves his place open; when the player is one, his offers. Returns the stage's record
    (also `league.staff["stage"]`): the step to take next, the fired teams in team order, the player's old team and offers, and the lists the stage fills
    (the head coaches hired, the player's coordinators who left, the coordinators replaced, the candidates, the coordinators hired)."""
    fired = [team for team in range(1, D.TEAMS + 1) if is_fired(coach_of(league, team))]
    state = {"step": STEP_COACHES, "fired": fired, "old_team": 0, "approval": 0, "offers": [], "let_go": 0, "hired": [], "lost": [], "replaced": [],
             "candidates": {}, "new": []}
    if league.team in fired:
        state["approval"] = coach_of(league, league.team)["approval"]
    for team in fired:
        league.staff["coaches"][team - 1] = None
    if league.team in fired:
        state["old_team"] = league.team
        state["offers"] = offers(league, league.team)
        state["step"] = STEP_JOB
    league.staff["stage"] = state
    return state


def offers(league, team: int) -> list:
    """The jobs offered to the fired head coach of `team` (research B9, G): the other teams whose head coach's place is open, the best ranked first; when
    there are fewer than FR_OFFERS, the other teams whose head coach did not have a winning season, the coaches past their grace first, then the lowest job
    rating (one of them lets his coach go if the player takes the job; a coach in his grace only when no other is left, the review's finding 4). NEVER `team`. At most FR_OFFERS, listed by rank (the staff's recommendation first). There are always three such teams
    (a fired coach's team did not win more than it lost, so at most 28 of the other 31 can have)."""
    rank = {t: n for n, t in enumerate(league.ranking(), start=1)}
    open_places = sorted((t for t in range(1, D.TEAMS + 1) if t != team and coach_of(league, t) is None), key=lambda t: rank[t])
    chosen = open_places[:T.FR_OFFERS]
    if len(chosen) < T.FR_OFFERS:
        others = sorted((t for t in range(1, D.TEAMS + 1) if t != team and coach_of(league, t) is not None and not had_winning_season(coach_of(league, t))),
                        key=lambda t: (coach_of(league, t)["seasons"] <= T.FR_FIRE_GRACE, coach_of(league, t)["approval"], t))
        chosen += others[:T.FR_OFFERS - len(chosen)]
    return sorted(chosen, key=lambda t: rank[t])


def take_job(league, team: int) -> None:
    """The player takes the job of `team`, one of his offers: he is its head coach (a job rating FR_APPROVAL_START); a coach still in the place is let go."""
    state = league.staff["stage"]
    if state is None or state["step"] != STEP_JOB or team not in state["offers"]:
        raise LeagueError("the player cannot take the job of team %r now" % (team,))
    if coach_of(league, team) is not None:
        state["let_go"] = team
    league.staff["coaches"][team - 1] = new_coach(league.coach)
    league.team = team
    state["step"] = STEP_COACHES


def best_coordinator(league):
    """(team, side) of the best rated coordinator of the league (of equals the first in team order, the offensive one before the defensive one), or None."""
    best = None
    for team in range(1, D.TEAMS + 1):
        for side in SIDES:
            c = coordinator_of(league, team, side)
            if c is not None and (best is None or c["rating"] > best[0]):
                best = (c["rating"], team, side)
    return None if best is None else (best[1], best[2])


def new_head_coach_teams(league) -> set:
    """The teams whose head coach is new this offseason: the ones the stage hired for, and the player's new team."""
    state = league.staff["stage"]
    teams = {row[0] for row in state["hired"]}
    if state["old_team"] and league.team != state["old_team"]:
        teams.add(league.team)
    return teams


def rule_sides(league, team: int) -> list:
    """The coordinators the staff's rule replaces (a computer team, and the player's team when the staff handles it): the open places, both when the head
    coach is new, else the ones rated under FR_COORD_KEEP."""
    new_head = team in new_head_coach_teams(league)
    return [side for side in SIDES if coordinator_of(league, team, side) is None or new_head or coordinator_of(league, team, side)["rating"] < T.FR_COORD_KEEP]


def hire_head_coaches(league, staff: bool) -> None:
    """Every open head coach's place (team order; never the player's) takes the best coordinator of the league as its head coach, whose place opens; then
    every computer team replaces the coordinators of `rule_sides`, and so does the player's team when `staff` (the staff handles it). The next step is the
    player's own choice when the staff does not handle his team and a coordinator of his is still in place, else the draw."""
    state = league.staff["stage"]
    for team in range(1, D.TEAMS + 1):
        if coach_of(league, team) is not None:
            continue
        found = best_coordinator(league)
        if found is None:
            raise LeagueError("no coordinator is left to be a head coach")
        source, side = found
        promoted = coordinator_of(league, source, side)
        league.staff["coaches"][team - 1] = new_coach(promoted["name"])
        league.staff["coordinators"][source - 1][side] = None
        state["hired"].append([team, source, side, promoted["name"]])
        if source == league.team:
            state["lost"].append([side, promoted["name"], team])
    for team in range(1, D.TEAMS + 1):
        if team == league.team and not staff:
            continue
        open_sides(league, team, rule_sides(league, team))
    mine = league.team if 1 <= league.team <= D.TEAMS else 0
    if mine and not staff and any(coordinator_of(league, mine, side) is not None for side in SIDES):
        state["step"] = STEP_OWN
    else:
        state["step"] = STEP_DRAW


def open_sides(league, team: int, sides: list) -> None:
    """The coordinators of `sides` leave the team (a place already open stays open)."""
    state = league.staff["stage"]
    for side in sides:
        c = coordinator_of(league, team, side)
        if c is not None:
            state["replaced"].append([team, side, c["name"]])
            league.staff["coordinators"][team - 1][side] = None


def own_sides(league, sides: list) -> None:
    """The player's answer about his coordinators (the sides he replaces; none keeps them)."""
    state = league.staff["stage"]
    if state["step"] != STEP_OWN:
        raise LeagueError("the player's coordinators are not asked now")
    open_sides(league, league.team, sides)
    state["step"] = STEP_DRAW


def draw_candidate(league, rnd, surnames: list, used: set) -> dict:
    """One candidate: his name (the players' rule: again while in use, G-D1), his style below(7) of the seven styles, his rating (FR_COORD_RATING)."""
    name = draw_name(rnd, surnames, used)
    used.add(name)
    style = STYLE_KEYS[rnd.below(len(STYLE_KEYS))]
    base, first, second = T.FR_COORD_RATING
    rating = max(D.RATING_MIN, min(D.RATING_MAX, base + rnd.below(first) + rnd.below(second)))
    return new_coordinator(name, style, rating)


def ranked(candidates: list) -> list:
    """The candidates best rated first, equals in the order they were drawn (the staff's recommendation is the first)."""
    return [c for _, c in sorted(enumerate(candidates), key=lambda pair: (-pair[1]["rating"], pair[0]))]


def draw_candidates(league, rnd, surnames: list, staff: bool) -> None:
    """FR_COORD_CANDIDATES candidates for every open coordinator's place, team by team, the offense first; every computer team takes its best at once, and
    so does the player's team when `staff`; the player's open places wait for his choice (`hire`)."""
    state = league.staff["stage"]
    used = {p.name for p in league.players.values() if p.status == "active"} | {league.coach}
    for coach in league.staff["coaches"]:
        if coach is not None:
            used.add(coach["name"])
    for pair in league.staff["coordinators"]:
        for c in pair:
            if c is not None:
                used.add(c["name"])
    for team in range(1, D.TEAMS + 1):
        for side in SIDES:
            if coordinator_of(league, team, side) is not None:
                continue
            drawn = ranked([draw_candidate(league, rnd, surnames, used) for _ in range(T.FR_COORD_CANDIDATES)])
            state["candidates"][key_of(team, side)] = drawn
            if team != league.team or staff:
                hire(league, team, side, 0)
    state["step"] = STEP_PICK


def key_of(team: int, side: int) -> str:
    return "%d:%d" % (team, side)


def waiting_sides(league) -> list:
    """The player's open coordinator places still waiting for his choice."""
    state = league.staff["stage"]
    if state is None or state["step"] != STEP_PICK:
        return []
    return [side for side in SIDES if coordinator_of(league, league.team, side) is None and key_of(league.team, side) in state["candidates"]]


def hire(league, team: int, side: int, index: int) -> dict:
    """The team hires candidate `index` (0 the best rated) for its open place of `side`."""
    state = league.staff["stage"]
    candidates = state["candidates"].get(key_of(team, side))
    if not candidates or coordinator_of(league, team, side) is not None or not 0 <= index < len(candidates):
        raise LeagueError("team %d cannot hire candidate %r of side %d" % (team, index, side))
    chosen = dict(candidates[index])
    league.staff["coordinators"][team - 1][side] = chosen
    state["new"].append([team, side, chosen["name"]])
    return chosen


def finish(league) -> None:
    """The stage is over: every place is filled."""
    for team in range(1, D.TEAMS + 1):
        if coach_of(league, team) is None or any(coordinator_of(league, team, side) is None for side in SIDES):
            raise LeagueError("team %d has an open place on its staff at the stage's end" % team)
    league.staff["stage"] = None


def settle(league, rnd, surnames: list) -> dict:
    """The whole stage with the staff's answer to every question (the player's best ranked offer): the very steps the program takes with the staff
    setting on. The fast run takes the same steps itself (it also asks every fired coach's offers). Returns the stage's record."""
    state = begin(league)
    if state["step"] == STEP_JOB:
        take_job(league, state["offers"][0])
    hire_head_coaches(league, staff=True)
    draw_candidates(league, rnd, surnames, staff=True)
    finish(league)
    return state


# ----- the games: the playbooks and the game plan -----

def team_styles(league) -> tuple | None:
    """Every team's (offense style, defense style): its coordinators' (design 17 SX.8l: the coordinators choose the playbooks). None while a place is open."""
    staff = getattr(league, "staff", None)
    if not staff:
        return None
    out = []
    for pair in staff["coordinators"]:
        if pair[0] is None or pair[1] is None:
            return None
        out.append((pair[0]["style"], pair[1]["style"]))
    return tuple(out)


def lean(table: list) -> tuple:
    """(offense, defense) of a lineup `table` (identity, name, rating per place): +1 when it leans by FR_FIT_GAP rating points or more to the pass (the
    passing rating (2 x the quarterback + the receivers' carry-weighted mean) / 3 over the backs' carry-weighted mean) or to the rush (the line and linebackers'
    mean over the cornerbacks and safeties'), -1 the other way, else 0. Whole numbers only (the sides of each comparison multiplied out)."""
    from . import workload
    gap = T.FR_FIT_GAP
    rb = [(workload.carry_weight(table[i][2]), table[i][2]) for i in D.PLACES_OF["RB"]]
    wr = [(workload.carry_weight(table[i][2]), table[i][2]) for i in D.PLACES_OF["WR"]]
    w_rb, s_rb = sum(w for w, _ in rb), sum(w * r for w, r in rb)
    w_wr, s_wr = sum(w for w, _ in wr), sum(w * r for w, r in wr)
    qb = table[D.PLACES_OF["QB"][0]][2]
    edge = (2 * qb * w_wr + s_wr) * w_rb - 3 * w_wr * s_rb           # 3 x w_rb x w_wr x (passing - running)
    bound = 3 * gap * w_rb * w_wr
    offense = 1 if edge >= bound else -1 if edge <= -bound else 0
    front = [table[i][2] for position in ("DL", "LB") for i in D.PLACES_OF[position]]
    cover = [table[i][2] for position in ("CB", "S") for i in D.PLACES_OF[position]]
    edge = len(cover) * sum(front) - len(front) * sum(cover)           # len(front) x len(cover) x (front - cover)
    bound = gap * len(front) * len(cover)
    defense = 1 if edge >= bound else -1 if edge <= -bound else 0
    return offense, defense


def fit(table: list, offense_style: str, defense_style: str) -> tuple:
    """The styles a team's coordinators play with the lineup `table` (research B8's LATER: its best players): FR_FIT_STYLES' passing or running style when
    its offense leans, its rushing or covering style when its defense leans, else the coordinators' own styles."""
    offense, defense = lean(table)
    styles = T.FR_FIT_STYLES
    return (styles["pass"] if offense > 0 else styles["run"] if offense < 0 else offense_style,
            styles["rush"] if defense > 0 else styles["cover"] if defense < 0 else defense_style)


def fitted_styles(league, week: int) -> tuple | None:
    """Every team's (offense style, defense style) for the game of `week` in a franchise (SX.8o, D-076): the styles its coordinators play with its week's
    lineup (`fit`: the ratings the game reads, the hurt men's places played by the next man up, the morale). EVERY team, the player's too: his "team"
    playbook is his coordinators', who follow his best players as every team's do (a playbook he chooses by name in F9 is his and never changes; the
    whole-program run's C-F2 was -1.07 wins with the computer teams alone fitted, so the fit helped only his opponents, B-P107). Outside the season (the
    offseason has empty places): the coordinators' styles. None while a place is open."""
    base = team_styles(league)
    if base is None or league.stage != "season" or not 1 <= week <= D.SUPER_BOWL_WEEK:
        return base
    from . import injuries, people, workload
    hurt = people.hurt_teams(league, week)
    out = []
    for team, (offense_style, defense_style) in enumerate(base, start=1):
        staff_rule = team != league.team                   # the player's team: his own decisions about his hurt men (written at the kick-off)
        table = injuries.lineup(league, team, week, staff_rule, hurt_before=week) if team in hurt else people.plain_table(league, team)
        out.append(fit(workload.rated_table(league, team, table), offense_style, defense_style))
    return tuple(out)


def game_team_styles(game) -> tuple | None:
    """The teams' styles of the franchise in use (`Game.franchise_styles`, set while the franchise is in use, `mode.activate`); None in every other game."""
    source = getattr(game, "franchise_styles", None)
    return source() if source is not None else None


def recommended(league, side: int, their_style: str, styles, own_style: str | None = None) -> str:
    """The staff's game plan of the player's side `side` against the opponent's style on the other side of the ball (design 8.1 T2): a coordinator rated
    FR_COORD_ADAPT or more answers it as FR_GAME_PLAN says, a lesser one recommends his own style (`own_style`: the style his team's lineup fits,
    SX.8o; else his record's). A style the player's files do not have is Classic."""
    c = coordinator_of(league, league.team, side)
    if c is None:
        return PD.CLASSIC_KEY
    if c["rating"] >= T.FR_COORD_ADAPT:
        key = T.FR_GAME_PLAN["offense" if side == 0 else "defense"].get(their_style, PD.CLASSIC_KEY)
    else:
        key = own_style or c["style"]
    return key if key in styles else PD.CLASSIC_KEY


# ----- the whole-file check -----

def _check_name(name, what) -> None:
    if not isinstance(name, str) or not 1 <= len(name) <= 60 or any(ord(ch) < 32 for ch in name):
        raise LeagueError("%s has the name %r" % (what, name))


def _check_coordinator(c, whole, what) -> None:
    if not isinstance(c, dict) or set(c) != {"name", "style", "rating", "seasons"}:
        raise LeagueError("%s is %r" % (what, c))
    _check_name(c["name"], what)
    if c["style"] not in PD.BOOK_KEYS:
        raise LeagueError("%s has the style %r" % (what, c["style"]))
    whole(c["rating"], D.RATING_MIN, D.RATING_MAX, "the rating of " + what)
    whole(c["seasons"], 0, D.MAX_SEASONS, "the seasons of " + what)


def check_staff(league, whole) -> None:
    """The staff whole (LeagueError otherwise): 32 head coaches and 64 coordinators in range; an open place only while the stage "the staff" is in
    progress, whose record must be well formed. (The player's team's head coach is the player whatever name its record holds: nothing speaks it.)"""
    staff = league.staff
    if not isinstance(staff, dict) or set(staff) != {"coaches", "coordinators", "stage"}:
        raise LeagueError("the staff is %r" % (type(staff).__name__,))
    coaches, coordinators, stage = staff["coaches"], staff["coordinators"], staff["stage"]
    if not isinstance(coaches, list) or len(coaches) != D.TEAMS or not isinstance(coordinators, list) or len(coordinators) != D.TEAMS:
        raise LeagueError("the staff has %r head coaches and %r pairs of coordinators" % (
            len(coaches) if isinstance(coaches, list) else None, len(coordinators) if isinstance(coordinators, list) else None))
    in_stage = league.stage == "offseason" and league.stage_no == D.STAGE_STAFF
    if stage is not None and not in_stage:
        raise LeagueError("the stage of the staff is in progress outside its stage")
    for team, coach in enumerate(coaches, start=1):
        if coach is None:
            if stage is None:
                raise LeagueError("team %d has no head coach" % team)
            continue
        if not isinstance(coach, dict) or set(coach) != {"name", "approval", "seasons", "goal", "last"}:
            raise LeagueError("the head coach of team %d is %r" % (team, coach))
        _check_name(coach["name"], "the head coach of team %d" % team)
        whole(coach["approval"], 0, 100, "the job rating of team %d" % team)
        whole(coach["seasons"], 0, D.MAX_SEASONS, "the head coach's seasons of team %d" % team)
        goal = coach["goal"]
        if not isinstance(goal, list) or len(goal) != 2 or goal[0] not in GOAL_KINDS:
            raise LeagueError("the goal of team %d is %r" % (team, goal))
        whole(goal[1], 0, D.REGULAR_WEEKS, "the goal's number of team %d" % team)
        last = coach["last"]
        if last is not None:
            if not isinstance(last, list) or len(last) != 4:
                raise LeagueError("the last season of team %d's head coach is %r" % (team, last))
            whole(last[0], 0, D.REGULAR_WEEKS, "the wins of team %d's last season" % team)
            whole(last[1], D.FINISH_MISSED, D.FINISH_CHAMPION, "the finish of team %d's last season" % team)
            whole(last[2], 0, 1, "the goal met of team %d's last season" % team)
            whole(last[3], 0, 100, "the job rating before team %d's last season" % team)
    for team, pair in enumerate(coordinators, start=1):
        if not isinstance(pair, list) or len(pair) != 2:
            raise LeagueError("the coordinators of team %d are %r" % (team, pair))
        for side, c in enumerate(pair):
            if c is None:
                if stage is None:
                    raise LeagueError("team %d has no %s coordinator" % (team, ("offensive", "defensive")[side]))
                continue
            _check_coordinator(c, whole, "a coordinator of team %d" % team)
    if stage is not None:
        _check_stage(league, stage, whole)


def _check_open_places(league, stage) -> None:
    """The open places fit the step: a head coach's place is open only before the head coaches are hired (the step job or coaches), the player's own
    only at the step job; at the step pick only the player's coordinator places are open, each with its candidates."""
    step = stage["step"]
    for team in range(1, D.TEAMS + 1):
        if coach_of(league, team) is None:
            if step not in (STEP_JOB, STEP_COACHES):
                raise LeagueError("team %d's head coach's place is open at the step %s" % (team, step))
            if team == league.team and step != STEP_JOB:
                raise LeagueError("the player's head coach's place is open at the step %s" % step)
        if step == STEP_PICK:
            for side in SIDES:
                if coordinator_of(league, team, side) is None and (team != league.team or key_of(team, side) not in stage["candidates"]):
                    raise LeagueError("team %d's coordinator place %d is open at the step pick" % (team, side))
    if step == STEP_JOB and coach_of(league, league.team) is not None:
        raise LeagueError("the player waits for an offer while he has his job")


def _check_stage(league, stage, whole) -> None:
    if not isinstance(stage, dict) or set(stage) != STAGE_KEYS or stage["step"] not in STEPS:
        raise LeagueError("the stage of the staff is %r" % (stage,))
    for key in ("fired", "offers"):
        if not isinstance(stage[key], list) or len(stage[key]) > D.TEAMS:
            raise LeagueError("the staff stage's %s is %r" % (key, stage[key]))
        for team in stage[key]:
            whole(team, 1, D.TEAMS, "a team of the staff stage's %s" % key)
    whole(stage["old_team"], 0, D.TEAMS, "the player's old team")
    whole(stage["let_go"], 0, D.TEAMS, "the team that let its coach go")
    whole(stage["approval"], 0, 100, "the player's job rating when he was fired")
    if stage["old_team"] in stage["offers"] or len(stage["offers"]) > T.FR_OFFERS:
        raise LeagueError("the player's offers are %r" % (stage["offers"],))
    if stage["step"] == STEP_JOB and (not stage["offers"] or league.team != stage["old_team"]):
        raise LeagueError("the player waits for an offer without one")
    # each row's values (the review's finding 3: a damaged row passed the check and then crashed the stage): (team, team, side, name) of "hired",
    # (side, name, team) of "lost", (team, side, name) of "replaced" and "new"
    for key, kinds in (("hired", "ttsn"), ("lost", "snt"), ("replaced", "tsn"), ("new", "tsn")):
        rows = stage[key]
        if not isinstance(rows, list) or len(rows) > 4 * D.TEAMS or any(not isinstance(row, list) or len(row) != len(kinds) for row in rows):
            raise LeagueError("the staff stage's %s is %r" % (key, rows))
        for row in rows:
            for value, kind in zip(row, kinds):
                if kind == "t":
                    whole(value, 1, D.TEAMS, "a team of the staff stage's %s" % key)
                elif kind == "s":
                    whole(value, 0, 1, "a side of the staff stage's %s" % key)
                else:
                    _check_name(value, "a name of the staff stage's %s" % key)
    _check_open_places(league, stage)
    candidates = stage["candidates"]
    if not isinstance(candidates, dict) or len(candidates) > 2 * D.TEAMS:
        raise LeagueError("the candidates are %r" % (type(candidates).__name__,))
    for key, rows in candidates.items():
        parts = key.split(":") if isinstance(key, str) else []
        if len(parts) != 2 or not parts[0].isdigit() or parts[1] not in ("0", "1") or not 1 <= int(parts[0]) <= D.TEAMS:
            raise LeagueError("a candidates' place is %r" % (key,))
        if not isinstance(rows, list) or not 1 <= len(rows) <= T.FR_COORD_CANDIDATES:
            raise LeagueError("the candidates of %s are %r" % (key, rows))
        for c in rows:
            _check_coordinator(c, whole, "a candidate")
