"""The staff in the program: the verdict of stage 1, the stage "the staff", the goal at a season's start, F9's job and staff (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 17 SX.8l (F9, N6.8, D-072). The rules are `staff.py`; this module speaks, asks the player and writes league.sav, as `resign_flow.py` does:

* Stage 1 (`verdict_lines`): the owner's goal of the season met or missed and the job rating's change, worked out before stage 1 speaks and kept after its
  wait with the season's history (the stage's own pattern: nothing of it is changed before the wait).
* Stage "the staff" (number 9, right after stage 1): every step changes the league and writes it BEFORE it is told (B-X53); a window closed at a question
  resumes at that question (the step is kept in `league.staff["stage"]`). The player who is fired chooses his new team among his offers; the player whose
  staff setting is off keeps or replaces his coordinators himself and picks each new one among three candidates (nothing is decided for him); with the
  setting on the staff takes the best ranked offer, follows the computer teams' rule and hires the best rated candidate.
* Stage 6 and a new franchise (`goal_line`): the owner's goal of the coming season.
"""
from __future__ import annotations

from .. import nx_texts as X
from .. import playbooks as PB
from . import data as D
from . import staff as S
from .question import FranchiseQuestion

GOAL_TEXT = {S.GOAL_WINS: "NXV-G01", S.GOAL_PLAYOFFS: "NXV-G02", S.GOAL_TITLE_GAME: "NXV-G03"}
SIDE_TEXT = {"left": ("NXV-17", "NXV-18"), "hired": ("NXV-15", "NXV-16"), "now": ("NXV-20", "NXV-21"), "choose": ("NXV-23", "NXV-24"),
             "new": ("NXV-25", "NXV-26")}
REPLACE_BOTH_SIDES = ([], [0], [1], [0, 1])          # the answers of the question about two coordinators: keep them, the offense, the defense, both


def _offseason():
    from . import offseason                      # the stage helpers and the wait live there (a late import: offseason imports this module)
    return offseason


def goal_text(goal: list) -> str:
    kind, number = goal
    return X.text(GOAL_TEXT[kind], n=number)


def style_name(key: str) -> str:
    return PB.DEFAULT_TABLE.style_name(key)


# ----- stage 1: the verdict -----

def verdict_lines(league, wins: list, finish: list) -> list:
    """The player's verdict of the season (the goal met or missed, the job rating and its change, a warning when it is low), from `staff.verdicts`."""
    team = league.team
    coach = S.coach_of(league, team)
    before, after, met = S.verdicts(league, wins, finish)[team - 1]
    lines = [X.text("NXV-01" if met else "NXV-02", goal=goal_text(coach["goal"]))]
    if after > before:
        lines.append(X.text("NXV-03", a=after, d=after - before))
    elif after < before:
        lines.append(X.text("NXV-04", a=after, d=before - after))
    else:
        lines.append(X.text("NXV-05", a=after))
    if S.in_danger(after) and not S.winning(wins[team - 1]):          # after a winning season he cannot be fired this offseason
        lines.append(X.text("NXV-06"))
    return lines


def goal_line(league) -> str:
    """NXV-07: the owner's goal of the season about to start."""
    return X.text("NXV-07", n=league.season, goal=goal_text(S.coach_of(league, league.team)["goal"]))


# ----- the stage "the staff" -----

class Speaker:
    """The stage's lines: kept until a question says them as its situation, or said before the next line that is told on its own."""

    def __init__(self, g):
        self.g = g
        self.pending: list = []

    def add(self, *lines) -> None:
        self.pending += [line for line in lines if line]

    def take(self) -> list:
        lines, self.pending = self.pending, []
        return lines

    def flush(self) -> None:
        for line in self.take():
            self.g.say2(line)


def stage_staff(p, n: int, m: int, short: bool) -> None:
    off = _offseason()
    g, store = p.g, p.store
    league = store.league
    words = store.words
    rnd = g.rnd

    def staff_on() -> bool:                       # read at every step: the setting turned on in F9 hands the rest to the staff
        return bool(g.options.settings.game.nx_fr_auto)

    if league.staff["stage"] is None:              # the stage starts: the firings; written before anything is said
        S.begin(league)
        store.save()
    state = league.staff["stage"]
    out = Speaker(g)
    out.add(off._stage_line(n, m, "NXE-19"))
    if state["step"] == S.STEP_JOB:
        _job(p, league, words, state, out, staff_on())
    if state["step"] == S.STEP_COACHES:
        S.hire_head_coaches(league, staff_on())
        store.save()
    out.add(*_league_lines(league, words, state, short))
    if state["step"] == S.STEP_OWN:
        _own(p, league, words, out, staff_on())
    if state["step"] == S.STEP_DRAW:
        S.draw_candidates(league, rnd, surnames_of(g), staff_on())
        store.save()
        for team, side, name in state["new"]:
            if team == league.team:
                out.add(X.text(SIDE_TEXT["new"][side], name=name))
    for side in S.waiting_sides(league):
        _pick(p, league, side, out, staff_on())
    closing = [X.text(SIDE_TEXT["now"][side], name=c["name"], style=style_name(c["style"]), r=c["rating"])
               for side, c in ((side, S.coordinator_of(league, league.team, side)) for side in S.SIDES)]
    if short:
        closing = []
    S.finish(league)
    league.stage_no = off._next_stage(D.STAGE_STAFF)
    store.save()
    if short:
        out.flush()
    else:
        off.wait_for_enter(g, out.take() + closing + [X.text("NXE-03")])


def surnames_of(g) -> list:
    from . import weekly
    return weekly.surnames_of(g)


def _rank(league, team: int) -> int:
    return league.rank_of(team)


def _job(p, league, words, state: dict, out: Speaker, staff: bool) -> None:
    """The player was fired: the sentence, then his offers (the best ranked first); the job he takes is written before it is told."""
    g, store = p.g, p.store
    entry = league.history[-1] if league.history else None
    wins = entry["wins"][league.team - 1] if entry else 0
    losses = entry["losses"][league.team - 1] if entry else 0
    out.add(X.text("NXV-09", a=state["approval"], l=losses) if wins == 1 else X.text("NXV-10", a=state["approval"], w=wins, l=losses))
    offers = state["offers"]
    if staff:
        choice = offers[0]
    else:
        items = [X.text("NXV-A01", team=words.team_name(t), r=league.strength(t), k=_rank(league, t)) for t in offers]
        choice = offers[FranchiseQuestion(g, out.take() + [X.text("NXV-11", coach=league.coach)], items).ask()]
    S.take_job(league, choice)
    from .league import team_ref
    p.season.tn1, p.season.tn2 = team_ref(league.team)
    store.save()
    out.add(X.text("NXV-12", team=words.team_name(choice)))
    if state["let_go"]:
        out.add(X.text("NXV-28", team=words.team_name(state["let_go"])))


def _league_lines(league, words, state: dict, short: bool) -> list:
    """What the league's head coaches did, and the player's coordinators who left to be head coaches."""
    lines = [X.text("NXV-13", n=len(state["fired"])) if state["fired"] else X.text("NXV-14")]
    if not short:
        for team, source, side, name in state["hired"][:D.STARS_NAMED]:
            lines.append(X.text(SIDE_TEXT["hired"][side], team=words.team_name(team), name=name, other=words.team_name(source)))
    if not state["old_team"]:                     # a player who moved never had his new team's coordinators: the stage's end names his staff
        for side, name, team in state["lost"]:
            lines.append(X.text(SIDE_TEXT["left"][side], name=name, team=words.team_name(team)))
    return lines


def _own(p, league, words, out: Speaker, staff: bool) -> None:
    """The player keeps or replaces the coordinators still in place (the staff's rule first; with the setting on, the rule)."""
    g, store = p.g, p.store
    team = league.team
    present = [side for side in S.SIDES if S.coordinator_of(league, team, side) is not None]
    rule = [side for side in S.rule_sides(league, team) if side in present]
    if staff:
        sides = rule
    else:
        situation = [X.text(SIDE_TEXT["now"][side], name=S.coordinator_of(league, team, side)["name"],
                            style=style_name(S.coordinator_of(league, team, side)["style"]), r=S.coordinator_of(league, team, side)["rating"])
                     for side in present]
        situation.append(X.text("NXV-22", coach=league.coach))
        if len(present) == 2:
            choices = list(REPLACE_BOTH_SIDES)
            texts = {(): "NXV-A02", (0,): "NXV-A03", (1,): "NXV-A04", (0, 1): "NXV-A05"}
        else:
            choices = [[], list(present)]
            texts = {(): "NXV-A06", tuple(present): "NXV-A07"}
        choices.sort(key=lambda sides: sides != rule)          # the staff's recommendation first, the others in their order
        items = [X.text(texts[tuple(sides)]) for sides in choices]
        sides = choices[FranchiseQuestion(g, out.take() + situation, items).ask()]
    S.own_sides(league, sides)
    store.save()


def _pick(p, league, side: int, out: Speaker, staff: bool) -> None:
    """The player's new coordinator of `side`: one of the candidates, the best rated first (the staff's recommendation); written before it is told."""
    g, store = p.g, p.store
    candidates = league.staff["stage"]["candidates"][S.key_of(league.team, side)]
    if staff:
        index = 0
    else:
        items = [X.text("NXV-A08", name=c["name"], style=style_name(c["style"]), r=c["rating"]) for c in candidates]
        index = FranchiseQuestion(g, out.take() + [X.text(SIDE_TEXT["choose"][side])], items).ask()
    chosen = S.hire(league, league.team, side, index)
    store.save()
    out.add(X.text(SIDE_TEXT["new"][side], name=chosen["name"]))


# ----- F9: your job and staff -----

def job_lines(league) -> list:
    """F9, franchise, your job and staff (NXF-45): the owner's goal, the job rating, the two coordinators."""
    coach = S.coach_of(league, league.team)
    lines = []
    if coach is None:                            # fired, while the job question waits (F9 works at every question of the flow)
        return [X.text("NXV-32")]
    lines += [X.text("NXV-30", goal=goal_text(coach["goal"])), X.text("NXV-31", a=coach["approval"])]
    for side in S.SIDES:
        c = S.coordinator_of(league, league.team, side)
        if c is not None:
            lines.append(X.text(SIDE_TEXT["now"][side], name=c["name"], style=style_name(c["style"]), r=c["rating"]))
    return lines
