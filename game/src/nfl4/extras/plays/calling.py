"""The computer's calling over the catalog, the playbook's pick behind Enter on a family, the clock plays and the two-point chart (nfl4
only, rule 0.13; NX-P4, NX-P5, NX-R7 G26-10; design `spec/NFL_PLAYS_DESIGN.md` sections 7 and 8; built in SX.10e, D-095). This is
inspired by Jim Kitchen.

Pure: no speech, no state of the engine. Every weight is a whole number and every draw is one `rnd.below(total)` of the game's one
generator, so a scripted source reaches every branch and a seeded game is the same on 32 and 64 bits.

The offense (`offense_weights`): each play's weight is its list's share (GROUP_MASS, the league's mix of calls from the data of
`model_data`) shared among the usable plays of that list, times the style's lean on the list (STYLE_GROUP) and on its own plays (a
style's SX.7 plays count OWN_PLAY_PERCENT), times the situation (short yardage, long yardage, the red zone, the goal line, late and
behind); then the pass calls together are scaled to the drop-back share of the down and distance (model_data.PASS_RATE, moved by the
style's STYLE_PASS_SHIFT and by the score late in a half) and the run calls to the rest. The defense (`defense_weights`): each call's
base weight (calling_data.DEFENSE_BASE, fitted to the league's coverage, rusher, blitz and box shares) times the style's lean
(STYLE_DEFENSE_GROUP, its own SX.7 calls) and the situation (the goal line, short yardage, third and long, a lead to keep late, a Hail
Mary to stop, the try). The playbook's pick is the same weights over the plays of one family. Trick plays and the old formations are
rare by their small list shares.

The clock plays and the try are rules, not draws: `kneel_helps`, `spike_wanted`, `last_play_call` and `goes_for_two` (the chart of
fourth-quarter margins, SRC-SECONDARY, plus a small early rate calibrated to the league's 9.8 percent of touchdowns).
"""
from __future__ import annotations

from typing import NamedTuple

from . import calling_data as CD
from . import catalog as C
from . import model_data as MD

PASS_KINDS = ("pass", "screen", "play_action", "boot", "trick_pass", "max_protect", "hail_mary")
CLOCK_KINDS = ("kneel", "spike", "hail_mary", "laterals")
QB_KINDS = ("sneak", "qb_run", "option")     # the plays whose ball carrier may be the quarterback (a style's qb_percent scales them)
KNEEL, SPIKE, HAIL_MARY, LATERALS = "O152", "O153", "O038", "O156"

# ----- the offense's mix (per 1,000 runs and per 1,000 drop-back calls; COMPUTED shares of model_data, the rest UNVERIFIED) -----
# runs: designed quarterback runs and sneaks 1.37 a team-game of about 27 runs (5.5), options about 4, run-pass options 4.7 percent of
# plays (about 9 of the runs' 42 percent); the rest by the charted gaps (inside 53, outside 29 of the runs, model_data.RUN_BY_GAP)
RUN_GROUP_MASS = {"og01": 323, "og02": 250, "og03": 215, "og04": 60, "og13": 35, "og14": 25, "og15": 90, "og19": 2}
SNEAK_PERCENT = 300                 # a sneak counts three times in its list: sneaks are 35 percent of the quarterback's runs (527 of 1,490;
#                                     200 gave the designed runs 4.20 yards over 1,000 games, NFL 3.66 with the sneaks)
# drop-backs: screens 8.4 percent, play action 22.9 (play action 17, the moving pocket 6), trick plays 0.4, the rest by the route mix
PASS_GROUP_MASS = {"og05": 84, "og11": 170, "og12": 60, "og06": 230, "og07": 160, "og08": 160, "og09": 70, "og10": 40, "og16": 4,
                   "og20": 22, "og18": 2}
# og18's fake spike and victory formation pass: only in the last two minutes of a half (CLOCK_SECONDS); the kneel, the spike, the Hail Mary and the
# laterals are rules, never drawn
GOAL_LINE_GROUP_MASS = 150          # og17 inside the 10 (per 1,000 of its class); nothing outside it (UNVERIFIED)
OWN_PLAY_PERCENT = 200              # a style's own SX.7 plays (playbook_data) count double within their list
RARE_PERCENT = 25                   # a play marked rare in a list that is not itself rare
# the styles' lean (percent of a list's share; 100 is none) and the pass share they add (per 10,000 drop-back calls); UNVERIFIED
STYLE_PASS_SHIFT = {"pro": 0, "west": 300, "air": 700, "power": -600, "zone": -300, "option": -500, "pressure": 300}
STYLE_GROUP = {
    "pro": {},
    "west": {"og05": 140, "og06": 130, "og07": 130, "og09": 70, "og10": 70},
    "air": {"og09": 150, "og10": 150, "og06": 120, "og11": 70, "og13": 60},
    "power": {"og02": 150, "og01": 120, "og03": 80, "og11": 140, "og05": 80},
    "zone": {"og03": 160, "og01": 110, "og02": 70, "og11": 140, "og12": 160},
    "option": {"og14": 300, "og13": 250, "og15": 200, "og04": 130, "og09": 70},
    "pressure": {"og09": 160, "og10": 160, "og11": 130},
}
STYLE_DEFENSE_GROUP = {
    "pro": {},
    "west": {"dg07": 130},
    "air": {"dg09": 130, "dg10": 120},
    "power": {"dg02": 140, "dg03": 130, "dg01": 120},
    "zone": {"dg07": 120, "dg09": 120},
    "option": {"dg04": 200},
    "pressure": {"dg05": 200, "dg06": 180},
}
# the situations (UNVERIFIED shapes; the pass share by down and distance is the data's)
SHORT_YARDS, LONG_YARDS, RED_ZONE, GOAL_LINE = 2, 10, 20, 10
SHORT_OFFENSE = {"og02": 150, "og09": 30, "og10": 30, "og05": 50}
SNEAK_SHORT_PERCENT = 400           # the sneaks on third or fourth and 1 or 2 (81.8 percent converted)
LONG_OFFENSE = {"og05": 130, "og09": 130, "og10": 130, "og06": 80}
RED_ZONE_OFFENSE = {"og09": 40, "og10": 40, "og16": 50}
LATE_BEHIND_OFFENSE = {"og09": 150, "og10": 150, "og05": 70}
LATE_SECONDS = 300                  # the fourth quarter's last five minutes
TWO_MINUTES = 120
LATE_PASS_FLOOR = 7000              # behind by 9 or more late, or behind in the last two minutes of a half: at least this share passes
#                                     (8000 gave quarters 2 and 4 7.02 more plays than 1 and 3, SX.2's band 2 to 7; 7000: 6.82)
LATE_LEAD_PASS_CEILING = 3000       # ahead late in the fourth quarter: at most this share
# the try: the data's tries are 24 percent runs (74 of 306), the gate a rare trick
TRY_WEIGHTS = (("O150", 90), ("O002", 70), ("O046", 80), ("O148", 120), ("O149", 160), ("O151", 120), ("O031", 120), ("O078", 120),
               ("O027", 110), ("K026", 10))
# the defense's situations
DEFENSE_GOAL_LINE = 5               # within this many yards the goal line calls take GOAL_LINE_CALL_SHARE of the weight
GOAL_LINE_CALL_SHARE = 6000
TRY_CALLS = (("D086", 3000), ("D001", 1200), ("D002", 1200), ("D031", 800), ("D032", 800), ("D034", 1500), ("D030", 800),
             ("D018", 700))
SHORT_DEFENSE = {"dg02": 200, "dg03": 200, "dg01": 200, "dg09": 50, "dg10": 50}
LONG_DEFENSE = {"dg05": 140, "dg06": 140, "dg09": 130, "dg10": 130, "dg02": 40, "dg03": 40}
PROTECT_CALLS = (("D087", 2500), ("D024", 800), ("D083", 700))       # a lead of 4 or more in the last two minutes: 25 percent of calls
PROTECT_SHARE = 2500
HAIL_MARY_CALL = "D085"
HAIL_MARY_DEFENSE_FROM = 35         # the last play of a half this far from the goal: the Hail Mary defense takes
HAIL_MARY_DEFENSE_SHARE = 7000      # this share of the calls (UNVERIFIED)
# the clock plays
SPIKE_CHANCE = 2                    # the computer spikes one time in this many when it wants to (UNVERIFIED; data 0.29 a game)
SPIKE_SECONDS = 60
KNEEL_HALF_SECONDS = 40
COMPUTER_KNEEL_HALF = (30, 70)      # the computer kneels at the end of the first half with at most 30 seconds left, 70 or more yards
#                                     from the goal (UNVERIFIED; data 1.54 kneels a game)
HAIL_MARY_REACH = 62                # a field goal longer than this on the last play of a half: the Hail Mary instead (UNVERIFIED)
LATERALS_FROM = 75                  # the last play of the game, behind by 8 or less, this far from the goal: the laterals
# the two-point chart: fourth quarter, the margin after the touchdown's six points, before the try (positive: ahead). Laura Albert,
# Punk Rock Operations Research, 6 February 2024, tables 1 and 2 (SRC-SECONDARY): go for two behind by 10, 8, 5, 2 or 1 and ahead by
# 1, 2, 4, 5 or 7; kick tied, behind by 3, 4 or 6, ahead by 3 or 6 (a margin it does not name: the kick). D-175 (Q-037): where the
# league's coaches are measured, the chart is what they do: behind by 1 they kick to tie (13.8 percent went for two in the fourth quarters
# of 2021 to 2025, nflverse via vertizesports.com; 34 percent in the last two minutes, CBS 2025) and behind by 8 they kick (37.3 percent
# went for two, 28 of 75); behind by 2 they all go (49 of 49). SRC-SECONDARY; work/late_1026/nfl_late_game_research.md
TWO_POINT_CHART = frozenset((-10, -5, -2, 1, 2, 4, 5, 7))
# in overtime the paper's chart as SX.12 measured it: the coaches' figures above are the fourth quarter's, and with the kick that ties the
# 10-minute period often ran out tied (10,000 games: 14.0 percent of overtime games ended tied, the league 5.9 in 2017 to 2024; D-175)
TWO_POINT_CHART_OVERTIME = frozenset((-10, -8, -5, -2, -1, 1, 2, 4, 5, 7))
TWO_POINT_EARLY = 300              # per 10,000 touchdowns before the chart's time (UNVERIFIED; calibrated so all touchdowns give about
#                                     the league's 9.8 percent, model_data.TWO_POINT_TRY_SHARE)
CHART_SECONDS = 600                 # the chart rules the last ten minutes (the paper's last six possessions or so; UNVERIFIED reading)
# the fourth quarter's fourth down (D-175, Q-037; `fourth_down_call`). The yards are to the goal line (a kick of to_goal + 17 yards);
# the seconds are the fourth quarter's. Values: see D-175 and work/late_1026/nfl_late_game_research.md
KICK_REACH = 37                     # the field goal in the ordinary choice: at most a 54-yard kick (model_data.FIELD_GOAL 50-54: 73.3)
LAST_KICK_REACH = 40                # the late kick that ties or wins: at most a 57-yard kick (55-59: 67.9)
LATE_BEHIND_SECONDS = 300           # behind in the last five minutes: the late rules
ALL_IN_SECONDS = 180                # behind in the last three minutes: never the punt
TWO_SCORES_SECONDS = 480            # two scores behind in the last eight minutes: no punt in the other half
TWO_SCORE_KICK_SECONDS = 60         # two scores behind late: the field goal that makes it one score while a minute is left
GO_ZONE = 50                        # behind late: from the other half the offense goes for it
SHORT_GO = 1                        # fourth and this many or fewer: short
GOAL_TO_GO_GO = 3                   # fourth and short this close to the goal, tied or behind: go for the touchdown
HALF_FIELD = 50                     # fourth and short in the other half: go for it (the ordinary choice)


class Situation(NamedTuple):
    down: int = 1
    to_go: int = 10
    to_goal: int = 75
    quarter: int = 1
    left: int = 900             # seconds left in the quarter
    lead: int = 0               # the offense's lead
    two_point: bool = False
    last_play: bool = False     # the last play of a half (the defense expects a Hail Mary from far away)


def pass_class(concept: C.Concept) -> bool:
    return concept.kind in PASS_KINDS


def pass_rate(sit: Situation, style: str = "") -> int:
    """The drop-back share (per 10,000 calls) of the down and distance (model_data.PASS_RATE), the style's lean, and late in a half."""
    if sit.down == 1:
        key = "1st"
    elif sit.down == 2:
        key = "2nd 1-3" if sit.to_go <= 3 else "2nd 4-7" if sit.to_go <= 7 else "2nd 8+"
    elif sit.down == 3:
        key = "3rd 1-2" if sit.to_go <= 2 else "3rd 3-6" if sit.to_go <= 6 else "3rd 7+"
    else:
        key = "4th"
    rate = MD.PASS_RATE[key] + STYLE_PASS_SHIFT.get(style, 0)
    late = sit.quarter >= 4 and sit.left <= LATE_SECONDS
    two_minutes = sit.quarter in (2, 4) and sit.left <= TWO_MINUTES
    if (late and sit.lead <= -9) or (two_minutes and sit.lead < 0) or (sit.quarter == 2 and two_minutes and sit.to_goal > 25):
        rate = max(rate, LATE_PASS_FLOOR)
    elif late and sit.lead > 0:
        rate = min(rate, LATE_LEAD_PASS_CEILING)
    return max(300, min(9700, rate))


def _situation_percent(concept: C.Concept, sit: Situation) -> int:
    """The situation's percent on one offense play (100: none)."""
    pct = 100
    group = concept.group
    short = sit.down >= 3 and sit.to_go <= SHORT_YARDS
    if short:
        pct = pct * SHORT_OFFENSE.get(group, 100) // 100
        if concept.kind == "sneak":
            pct = pct * SNEAK_SHORT_PERCENT // 100
    elif sit.down >= 2 and sit.to_go >= LONG_YARDS:
        pct = pct * LONG_OFFENSE.get(group, 100) // 100
    if sit.to_goal <= RED_ZONE:
        pct = pct * RED_ZONE_OFFENSE.get(group, 100) // 100
    if sit.quarter >= 4 and sit.left <= LATE_SECONDS and sit.lead < 0:
        pct = pct * LATE_BEHIND_OFFENSE.get(group, 100) // 100
    if "clock" in concept.situations and not (sit.quarter in (2, 4) and sit.left <= TWO_MINUTES):
        return 0
    if "goal_line" in concept.situations and group != "og17":
        pct = pct * (300 if sit.to_goal <= GOAL_LINE else 0) // 100
    return pct


def offense_weights(candidates, style: str, own: frozenset, sit: Situation, qb_percent: int = 100) -> list[tuple[str, int]]:
    """The weights of the offense plays `candidates` (catalog concepts, already usable) for a style ("" none) in a situation; the clock
    plays are never drawn; `qb_percent` (the style's line of styles.txt, SX.7) lowers the quarterback's own runs and the options when it
    is under 100 (0: none); above 100 it adds nothing, the style's lean already counts. Whole numbers summing to about 100,000; a play with no weight is left out."""
    plays = [c for c in candidates if c.side == "O" and c.kind not in CLOCK_KINDS
             and (qb_percent > 0 or c.kind not in QB_KINDS)]
    goal = sit.to_goal <= GOAL_LINE
    lean = STYLE_GROUP.get(style, {})
    sizes: dict[tuple[str, bool], int] = {}
    for c in plays:
        if c.group == "og17" and not goal:
            continue
        sizes[(c.group, pass_class(c))] = sizes.get((c.group, pass_class(c)), 0) + _play_factor(c, own)
    raw: list[tuple[C.Concept, int]] = []
    for c in plays:
        passing = pass_class(c)
        key = (c.group, passing)
        if key not in sizes:
            continue
        masses, others = (PASS_GROUP_MASS, RUN_GROUP_MASS) if passing else (RUN_GROUP_MASS, PASS_GROUP_MASS)
        # a list holds plays of both kinds now and then (a trick run among the trick passes): its share is the list's either way
        mass = GOAL_LINE_GROUP_MASS if c.group == "og17" else masses.get(c.group, others.get(c.group, 0))
        weight = mass * lean.get(c.group, 100) * _situation_percent(c, sit) * _play_factor(c, own) * 100 // max(1, sizes[key])
        if c.kind in QB_KINDS:                      # a lower rate only: STYLE_GROUP already gives Option its many quarterback runs
            weight = weight * min(100, qb_percent) // 100
        if weight > 0:
            raw.append((c, weight))
    rate = pass_rate(sit, style)
    totals = {True: sum(w for c, w in raw if pass_class(c)), False: sum(w for c, w in raw if not pass_class(c))}
    share = {True: rate, False: 10000 - rate}
    if not totals[True] or not totals[False]:              # one class only (a family's pick): its own weights
        share = {True: 10000, False: 10000}
    out = []
    for c, weight in raw:
        value = weight * share[pass_class(c)] * 10 // max(1, totals[pass_class(c)])
        if value > 0:
            out.append((c.id, value))
    return out


def _play_factor(concept: C.Concept, own: frozenset) -> int:
    factor = OWN_PLAY_PERCENT if concept.id in own else 100
    if concept.kind == "sneak":
        factor = factor * SNEAK_PERCENT // 100
    if "rare" in concept.situations and concept.group not in ("og16", "og19"):
        factor = factor * RARE_PERCENT // 100
    return factor


def try_weights(usable) -> list[tuple[str, int]]:
    """The computer's two-point try (design 2.6): the goal line plays and the try's list, a quarter of them runs as the data's tries."""
    return [(i, w) for i, w in TRY_WEIGHTS if i in usable]


def defense_weights(candidates, style: str, own: frozenset, sit: Situation) -> list[tuple[str, int]]:
    """The weights of the defense calls `candidates` (catalog concepts, usable) for a style in a situation (the offense's down, distance,
    line, quarter, time and lead)."""
    calls = [c for c in candidates if c.side == "D"]
    if sit.two_point:
        wanted = dict(TRY_CALLS)
        return [(c.id, wanted[c.id]) for c in calls if c.id in wanted]
    lean = STYLE_DEFENSE_GROUP.get(style, {})
    protect = sit.quarter >= 4 and sit.left <= TWO_MINUTES and sit.lead <= -4
    out: list[tuple[str, int]] = []
    goal_line, normal = [], []
    for c in calls:
        base = CD.DEFENSE_BASE.get(c.id, 0)
        weight = base * lean.get(c.group, 100) // 100
        if c.id in own:
            weight = weight * OWN_PLAY_PERCENT // 100
        if sit.down >= 3 and sit.to_go <= SHORT_YARDS:
            weight = weight * SHORT_DEFENSE.get(c.group, 100) // 100
        elif sit.down >= 3 and sit.to_go >= 7:
            weight = weight * LONG_DEFENSE.get(c.group, 100) // 100
        if "goal_line" in c.situations:
            goal_line.append(c)
        elif weight > 0:
            normal.append((c, weight))
    if goal_line and (sit.to_goal <= DEFENSE_GOAL_LINE or not normal):     # no other call (a family's pick): the goal line calls
        total = sum(w for _c, w in normal)
        out = [(c.id, w * (10000 - GOAL_LINE_CALL_SHARE) // max(1, total)) for c, w in normal]
        out += [(c.id, GOAL_LINE_CALL_SHARE // len(goal_line)) for c in goal_line]
    else:
        out = [(c.id, w) for c, w in normal]
    if sit.last_play and sit.to_goal >= HAIL_MARY_DEFENSE_FROM and any(c.id == HAIL_MARY_CALL for c in calls):
        total = sum(w for _i, w in out)
        out = [(i, w * (10000 - HAIL_MARY_DEFENSE_SHARE) // max(1, total)) for i, w in out]
        out.append((HAIL_MARY_CALL, HAIL_MARY_DEFENSE_SHARE))
        return [(i, w) for i, w in out if w > 0]
    if protect:
        total = sum(w for _i, w in out)
        wanted = [(i, w) for i, w in PROTECT_CALLS if any(c.id == i for c in calls)]
        if wanted and total:
            scale = sum(w for _i, w in wanted)
            out = [(i, w * (10000 - PROTECT_SHARE) // total) for i, w in out if i not in dict(wanted)]
            out += [(i, w * PROTECT_SHARE // scale) for i, w in wanted]
    return [(i, w) for i, w in out if w > 0]


def draw(weights: list[tuple[str, int]], rnd) -> str:
    """One draw: `below(total)` over the whole weights; "" when nothing can be drawn (no draw then)."""
    total = sum(w for _i, w in weights)
    if total <= 0:
        return ""
    pick = rnd.below(total)
    for play_id, weight in weights:
        if pick < weight:
            return play_id
        pick -= weight
    return weights[-1][0]


# ----- the clock plays and the try -----

def kneel_helps(quarter: int, left: int, down: int, lead: int, their_timeouts: int, two_point: bool = False) -> bool:
    """Design 2.7: the offense leads in the fourth quarter and kneels can run the clock out (the time left at most the downs left times
    40 seconds, less 40 for each timeout the defense has), or the first half is in its last seconds."""
    if two_point or left <= 0:
        return False
    downs = 5 - down
    if quarter == 4 and lead > 0:
        return left <= max(0, downs - their_timeouts) * 40
    if quarter == 2:
        return left <= KNEEL_HALF_SECONDS
    return False


def spike_wanted(quarter: int, left: int, running: bool, down: int, lead: int, own_timeouts: int, to_goal: int) -> bool:
    """The computer wants to stop the clock with a spike: the clock runs in the last minute of a half, it has no timeout left, a down is
    left after the spike, it is not ahead in the fourth quarter, and it is in reach of a score."""
    if quarter not in (2, 4) or not running or not 0 < left <= SPIKE_SECONDS or down >= 3 or own_timeouts > 0:
        return False
    if quarter == 4 and lead > 0:
        return False
    return to_goal <= 50


def last_play_call(quarter: int, lead: int, to_goal: int, kick_chosen: bool) -> str:
    """The last play of a half by the computer when the original's rule chose the field goal (`kick_chosen`): the Hail Mary when the kick
    would be longer than HAIL_MARY_REACH and a touchdown helps; the laterals from far away at the end of the game; else "" (the kick)."""
    if not kick_chosen:
        return ""
    long_kick = to_goal + 17 > HAIL_MARY_REACH
    if quarter == 4 and -8 <= lead <= -4:                  # behind by more than a field goal: only a touchdown helps
        return LATERALS if to_goal >= LATERALS_FROM else HAIL_MARY
    if long_kick and (quarter == 2 or -3 <= lead <= 0):
        return HAIL_MARY if to_goal <= 70 else ""
    return ""


def fourth_down_call(left: int, lead: int, to_goal: int, to_go: int) -> str:
    """D-175 (Q-037): the computer's fourth down in the fourth quarter, as the league's coaches decide it (a rule, no draw): "go", "kick"
    (a field goal) or "punt". `left` is the seconds left, `lead` the offense's own lead, `to_goal` the yards to the goal line, `to_go`
    the yards to gain. Behind late it never gives the ball away while a score can still help: a field goal that ties or wins is kicked
    within LAST_KICK_REACH, a team that needs a touchdown goes for it, a team two scores behind kicks the field goal that makes it one
    score. Otherwise the ordinary choice: the kick within KICK_REACH, fourth and short in the other half goes for it, else the punt."""
    if lead < 0 and left <= LATE_BEHIND_SECONDS:
        if lead >= -3:                                          # a field goal ties or wins
            if to_goal <= LAST_KICK_REACH:
                return "kick"
            if left <= ALL_IN_SECONDS or to_goal <= GO_ZONE or to_go <= SHORT_GO:
                return "go"
            return "punt"
        if lead >= -8:                                          # a touchdown is needed
            if left > ALL_IN_SECONDS and lead >= -6 and to_go > SHORT_GO and to_goal <= KICK_REACH:
                return "kick"                                   # the field goal makes it a one-point to three-point game
            if left <= ALL_IN_SECONDS or to_goal <= GO_ZONE or to_go <= SHORT_GO:
                return "go"
            return "punt"
        if lead >= -11 and to_goal <= KICK_REACH and left >= TWO_SCORE_KICK_SECONDS:
            return "kick"                                       # two scores behind: the kick makes it one score
        if left <= ALL_IN_SECONDS or to_goal <= GO_ZONE:
            return "go"
        return "punt"
    if lead < -8 and left <= TWO_SCORES_SECONDS:
        if to_goal <= KICK_REACH and lead >= -11:
            return "kick"
        if to_goal <= GO_ZONE or to_go <= SHORT_GO:
            return "go"
        return "punt"
    if to_goal <= KICK_REACH:
        return "go" if to_go <= SHORT_GO and to_goal <= GOAL_TO_GO_GO and lead <= 0 else "kick"
    if to_go <= SHORT_GO and to_goal <= HALF_FIELD:
        return "go"
    return "punt"


def goes_for_two(quarter: int, margin: int, rnd, left: int = 0) -> bool:
    """G26-10: after a touchdown (the margin counts its six points), the chart in the last CHART_SECONDS of the fourth quarter and in
    overtime (no draw); earlier one draw against TWO_POINT_EARLY."""
    if quarter >= 5:
        return margin in TWO_POINT_CHART_OVERTIME
    if quarter == 4 and left <= CHART_SECONDS:
        return margin in TWO_POINT_CHART
    return rnd.below(10000) < TWO_POINT_EARLY
