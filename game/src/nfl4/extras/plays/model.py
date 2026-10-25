"""The outcome models of the plays of the N. F. L. rules mode (nfl4 only, rule 0.13; NX-P3; design `spec/NFL_PLAYS_DESIGN.md`
section 4). This is inspired by Jim Kitchen.

Pure functions: a concept of catalog.py, a defense call (catalog.Call), the situation and the game's random source (anything with
`below(n)`, which is Int(Rnd * n), so a scripted source can force every branch) give a `Result`. No speech, no state, no file.
Every number comes from model_data.py; the few that the data does not give are START VALUES here, each named and marked
UNVERIFIED with what would show it wrong, and SX.10e may move them only with a recorded measurement (design 4.10).

    pass_play(concept, call, situation, rnd)       a drop-back: sack, target, band, completion or interception, yards
    run_play(concept, call, situation, rnd)        a hand-off: the gap's bins, the box, the call's run tags, the shift
    qb_play / option_play / rpo_play               the quarterback's runs, the reads
    play(concept, call, situation, rnd)            any offense concept: the right one of the above
    kickoff / punt / field_goal / extra_point      the kicks of 2026 (design 4.9)
"""
from __future__ import annotations

from typing import NamedTuple

from . import catalog as C
from . import model_data as M

SCALE = M.SCALE

# ----- START VALUES the data does not give (UNVERIFIED; design 4.10 says what would show each wrong) -----
MATCHUP_PASS_COMP = 300        # completion points (hundredths) for each of a pass concept's strong (+) or weak (-) tags met
MATCHUP_RUN_SHIFT = 40         # hundredths of a yard a carry for each of a run concept's strong or weak tags met
MATCHUP_CAP = 2                # at most two tags count each way, so a play moves by at most 6 points or 0.8 yards
RED_ZONE_COMP = (900, 120)     # inside the 10: this many completion points lost, and this many more per yard closer (data:
                               # 52.7 percent inside the 10, the end zone's back line already shortens the throws)
GOAL_LINE_YARDS = 5            # within this many yards a run's bins take the shape of the runs inside the 5 (GOAL_LINE_RUNS)
COVERAGE_DEPTH_SHRINK = 300    # a coverage's own throw depth against its shell's, by this many attempts
PLAY_ACTION_LATE_DOWN = 50     # percent of the fake's effect on 3rd or 4th and 7 or more (the defense does not bite)
RPO_THROW_HEAVY, RPO_THROW_LIGHT = 5000, 800    # the read throws against a box of 7 or more or a run blitz; else rarely
RPO_COMP = 500                 # the read's throw goes to the defender left alone (data: RPO throws 84.1 percent)
OPTION_MISREAD = 1000          # the quarterback reads it wrong one time in ten
PITCH_FUMBLE = (200, 6000)     # a pitch is fumbled 2 times in 100, the defense keeps 60 percent of those
LATERAL_FUMBLE = (200, 5000)   # a trick play's lateral before the throw
TRICK_INT = 120                # percent: a trick play's thrower is not the quarterback
TRICK_COMP = 600               # completion points: the fake leaves a receiver open (data: trick passes 61.5 percent at 9.2 air)
HAIL_MARY = {"touchdown": 830, "interception": 2590, "caught_short": 140}   # ESPN 16 and 50 in 193; FiveThirtyEight 9.7
LATERALS = {"touchdown": 300, "lost": 2500}    # the last play's laterals: no published rate
SACK_SCALE = 170               # percent: the engine's sacks, after the scrambles and the grounding, are the league's 6.5 percent of the
#                                drop-backs (SX.10e, D-095: 100 gave 3.7, 170 gave 6.4 over 60 games, work/sx10e/probe_calling.py)
CALL_PASS_TAGS = {             # a call's tags on a pass: (short bands' completion, deep bands' completion, interception %, sack %)
    "press": (-250, 150, 100, 100), "off": (200, -150, 100, 100), "robber": (-150, 0, 120, 100),
    "bracket": (0, -400, 110, 100), "deep_help": (0, -250, 105, 100), "drop": (-150, -100, 100, 90),
    "match": (-100, -150, 100, 100), "tampa": (0, -200, 105, 100), "disguise": (0, 0, 115, 103), "roll": (0, -200, 100, 100),
    "twist": (0, 0, 100, 108), "wide": (0, 0, 100, 108), "spy": (0, 0, 100, 95),
}
CALL_RUN_TAGS = {              # a call's tags on a run: percent on (loss, no gain, 1-3, 4-6, 7-9, 10-19, 20+)
    "run_blitz": (150, 120, 95, 85, 90, 115, 135), "slant": (125, 110, 100, 95, 95, 105, 115),
    "pinch": (110, 110, 100, 95, 95, 100, 100), "spill": (110, 100, 100, 100, 100, 100, 100),
    "two_gap": (95, 115, 110, 90, 90, 90, 90), "wide": (85, 90, 95, 110, 115, 115, 110),
}
OUTSIDE_TAGS = {"contain": (120, 105, 100, 95, 95, 80, 80), "spill": (125, 100, 100, 100, 100, 95, 95)}  # end runs only
SQUIB_SHORT = 1500             # a squib that first lands short of the landing zone: the ball at the 40 (RB26 6-2-4)
KICK_RETURN_SCALE = {"deep": 100, "short": 70, "squib": 60}    # percent of the return's yards (coverage arrives sooner)
KICK_TOUCHBACK = {"deep": 2800, "short": 0, "squib": 0}        # with about 55 deep and 45 short: 15.6 percent (2026)
KICK_CATCH = {"deep": (-5, 9), "short": (8, 19), "squib": (3, 14)}    # the receiving team's yard line of the catch
FG_BLOCK_RECOVERY = 7000       # the defense recovers a blocked field goal
FG_BLOCK_TD = 500              # and returns it for a touchdown
FAIR_CATCH_KICK_BONUS = 300    # no rush on a fair catch kick (RB26 10-2-4)
PUNT_INSIDE_20 = {"returned": 3000, "fair_catch": 3500, "downed": 1800, "out_of_bounds": 1700, "dead": 0}
PUNT_FIELD = {"returned": 5700, "fair_catch": 2700, "downed": 250, "out_of_bounds": 550, "dead": 800}
PUNT_END_ZONE_SAVED = 2500     # a spread punt bound for the end zone that the coverage downs short of the goal line
BLOCKED_PUNT_END_ZONE_TD = 5000    # SX.13 (UNVERIFIED: no published share found): a punt blocked behind the kicking team's goal line that the
#                                    receivers recover there for a touchdown; the rest leave the end zone (a safety)
PUNT_KIND = {"spread": {"block": 100, "gross": 0, "return": 100}, "tight": {"block": 30, "gross": -1, "return": 115},
             "rugby": {"block": 30, "gross": -3, "return": 85}, "pin": {"block": 100, "gross": 0, "return": 70}}
KICK_DEFENSE = {"return": {"block": 100, "return": 100, "fake": 100}, "fair_catch": {"block": 100, "return": 0, "fake": 100},
                "block": {"block": 600, "return": 70, "fake": 130}, "safe": {"block": 0, "return": 80, "fake": 60}}
FAKE_SUCCESS_BY_DISTANCE = ((2, 1500), (5, 0), (9, -2000), (99, -3500))     # points added to the 50 percent of the data


class Situation(NamedTuple):
    to_goal: int = 65               # yards from the line of scrimmage to the goal line the offense attacks
    down: int = 1
    distance: int = 10
    formation: str = ""             # "": the concept's own (catalog.SETTINGS["formation"])
    motion: str = ""                # "": the concept's own; "none" switches it off
    protection: str = "normal"
    # the Franchise's ratings door (H8, SX.10c; design 7): a shift of the run, the completion points, the sack and fumble rates
    # and the catch's yards, from the ratings' bounded Mod of extras/franchise/ratings.py. Zero (and 100) in every other game, so
    # every result and every draw is the same as without them
    run_shift: int = 0              # hundredths of a yard a carry
    comp_shift: int = 0             # completion points in hundredths
    sack_shift: int = 0             # added to the sack rate per 10,000 drop-backs
    fumble_pct: int = 100           # percent of the fumble rates
    catch_yards: int = 0            # added to a completion's yards
    # the player's own choices (SY.4, SY.5; empty unless he chose): the kind of the receiver the pass is thrown to ("WR", "TE", "RB") and
    # the kind of the player who blitzes ("DL", "LB", "DB")
    target: str = ""
    blitzer: str = ""


class Result(NamedTuple):
    kind: str                       # run, complete, incomplete, sack, interception, fumble, kneel, spike
    yards: int = 0                  # from the line of scrimmage (an interception: where it was caught)
    route: str = ""
    band: int = -1
    air: int = 0
    out_of_bounds: bool = False
    fumble_lost: bool = False
    return_yards: int = 0           # an interception's or a lost fumble's return
    return_touchdown: bool = False
    branch: str = ""                # a read's choice: give, keep, pitch, throw
    gap: str = ""                   # the engine knows the field: yards equal to to_goal is a touchdown, the model only caps


def chance(rnd, rate: int) -> bool:
    return rnd.below(SCALE) < rate


def pick(rnd, weights) -> int:
    """The index of one weight, drawn in proportion (one draw of the sum)."""
    total = sum(weights)
    if total <= 0:
        return 0
    x = rnd.below(total)
    for i, w in enumerate(weights):
        if x < w:
            return i
        x -= w
    return len(weights) - 1


def between(rnd, low: int, high: int) -> int:
    """A whole number from low to high; no draw when there is only one (a scripted source then needs no number for it)."""
    if high <= low:
        return low
    return low + rnd.below(high - low + 1)


# ----- what a call means (design 4.7) -----

def call_tags(call: C.Call) -> frozenset:
    tags = set(call.tags)
    if call.box >= 8:
        tags.add("box8")
    if call.box <= 6:
        tags.add("light")
    if call.rushers >= 5:
        tags.add("blitz")
    if call.rushers >= 6:
        tags.add("max_blitz")
    if call.rushers <= 3:
        tags.add("drop")
    if call.coverage in M.TWO_HIGH or call.coverage == C.PREVENT:
        tags.add("two_high")
    else:
        tags.add("one_high")
    tags.add("man" if call.coverage in M.MAN_COVERAGES else "zone")
    return frozenset(tags)


def matchup(concept: C.Concept, tags: frozenset) -> int:
    """+1 per strong tag met, -1 per weak tag met, each side capped (design 4.8)."""
    good = min(MATCHUP_CAP, sum(1 for t in concept.strong if t in tags))
    bad = min(MATCHUP_CAP, sum(1 for t in concept.weak if t in tags))
    return good - bad


# ----- the pass model's derived tables (computed once from model_data) -----

def _shrunk(cells_n, cells_v, base):
    k = M.COVERAGE_SHRINK
    return tuple((n * v + k * b) // (n + k) for n, v, b in zip(cells_n, cells_v, base))


COVERAGE_COMP = {k: _shrunk(v[0], v[1], M.BAND_COMP) for k, v in M.COVERAGE_BANDS.items()}
COVERAGE_INT = {k: _shrunk(v[0], v[2], M.BAND_INT) for k, v in M.COVERAGE_BANDS.items()}
COVERAGE_BLITZ = {k: v[3] for k, v in M.COVERAGE_BANDS.items()}


def _shell_factor(two_high: bool) -> tuple:
    keys = [k for k in M.COVERAGE_BANDS if (k in M.TWO_HIGH) == two_high]
    totals = [sum(M.COVERAGE_BANDS[k][0][b] for k in keys) for b in range(7)]
    whole = sum(totals)
    return tuple(t * SCALE * 100 // whole // max(1, s) for t, s in zip(totals, M.BAND_SHARE))   # percent


SHELL_FACTOR = {False: _shell_factor(False), True: _shell_factor(True)}


def _coverage_factor(key: str) -> tuple:
    """How deep the throws go against one coverage (quarterbacks throw deeper against man, data): its own band shares, shrunk to
    its shell's by COVERAGE_DEPTH_SHRINK attempts, in percent of the league's shares."""
    counts = M.COVERAGE_BANDS[key][0]
    total = sum(counts)
    shell = SHELL_FACTOR[key in M.TWO_HIGH]
    k = COVERAGE_DEPTH_SHRINK
    out = []
    for b in range(7):
        own = counts[b] * SCALE * 100 // total // M.BAND_SHARE[b]
        out.append((own * total + shell[b] * k) // (total + k))
    return tuple(out)


DEPTH_FACTOR = {k: _coverage_factor(k) for k in M.COVERAGE_BANDS}
# a prevent defense: the share of the deep bands falls, their completion falls, the short ones rise (UNVERIFIED shapes)
PREVENT_SHARE = (130, 120, 110, 80, 50, 35, 30)
PREVENT_COMP = (300, 300, 200, -300, -800, -1000, -1000)


class RouteProfile(NamedTuple):
    shares: tuple
    comp_delta: int        # completion points against what the band mix predicts
    int_pct: int           # interceptions in percent of what the band mix predicts
    yac_pct: int           # yards after the catch in percent of what the band mix predicts
    man_zone: int          # half the route's own man-zone gap beyond the bands' (+ against zone, - against man)
    oob: int


def _route_profile(row) -> RouteProfile:
    shares, comp, ints, yac, man, zone, oob = row
    total = sum(shares)
    exp_comp = sum(s * c for s, c in zip(shares, M.BAND_COMP)) // total
    exp_int = sum(s * i for s, i in zip(shares, M.BAND_INT)) // total
    exp_yac = sum(s * y for s, y in zip(shares, M.YAC_MEAN)) // total
    exp_gap = sum(s * (z - m) for s, z, m in zip(shares, M.ZONE_COMP, M.MAN_COMP)) // total
    return RouteProfile(shares, comp - exp_comp, ints * 100 // max(1, exp_int), yac * 100 // max(1, exp_yac),
                        ((zone - man) - exp_gap) // 2, oob)


ROUTE = {name: _route_profile(row) for name, row in M.ROUTES.items()}
SACK_YARDS = ((0, 750), (-1, 460), (-2, 510), (-3, 500), (-4, 700), (-5, 810), (-6, 910), (-7, 1180), (-8, 1330), (-9, 980),
              (-10, 700), (-11, 370), (-12, 240), (-13, 190), (-14, 130), (-15, 90), (-17, 150))    # COMPUTED, 2,601 sacks


def formation_class(concept: C.Concept, situation: Situation) -> str:
    form = situation.formation or concept.formation
    if form in ("shotgun", "pistol", "empty"):
        return form
    if form in ("wildcat",):
        return "shotgun"
    return "under_center"


def motion_on(concept: C.Concept, situation: Situation) -> bool:
    if situation.motion == "none":
        return False
    return bool(situation.motion or concept.motion)


# SY.4: the routes that suit a kind of receiver (a back runs the swing, the angle, the screen and the drag; a tight end the short and middle
# routes; a wide receiver the rest). A pass whose routes have none of them is thrown as it was (the target is then only named).
ROUTE_TARGETS = {"RB": ("swing", "angle", "screen", "drag"),
                 "TE": ("hitch", "drag", "dig", "slant", "quick_out", "deep_out", "angle"),
                 "WR": ("quick_out", "hitch", "dig", "go", "deep_out", "drag", "slant", "post", "corner", "wheel", "screen")}
BLITZER_SACK = {"DL": 100, "LB": 108, "DB": 112}      # SY.5: percent of the sack rate when the player named who blitzes on a blitz call


def targeted_routes(routes: tuple, kind: str) -> tuple:
    if not kind or kind not in ROUTE_TARGETS:
        return routes
    return tuple(r for r in routes if r[0] in ROUTE_TARGETS[kind]) or routes


def sack_rate(concept: C.Concept, call: C.Call, situation: Situation, tags: frozenset) -> int:
    rushers = max(3, min(6, call.rushers))
    rate = M.SACK_BY_RUSHERS[rushers][1 if "two_high" in tags else 0]
    if call.rushers <= 2:
        rate = rate * 80 // 100
    sack_pct = concept.params[1] if concept.kind not in ("rpo",) else 100
    rate = rate * sack_pct // 100
    if concept.kind == "screen":
        rate = rate * M.SCREEN_SACK // 100
    if concept.kind == "rpo":
        rate = rate * M.RPO_PASS["sack_per_dropback"] // M.LEAGUE_PASS["sack_per_dropback"]
    if concept.kind == "play_action":
        rate = rate * M.PLAY_ACTION_SACK // 100
    if concept.kind == "boot" and "contain" in tags:
        rate = rate * 130 // 100
    rate = rate * M.FORMATION_SACK.get(formation_class(concept, situation), 100) // 100
    if motion_on(concept, situation):
        rate = rate * M.MOTION_SACK // 100
    if situation.protection == "max":
        rate = rate * 70 // 100
    for tag in call.tags:
        if tag in CALL_PASS_TAGS:
            rate = rate * CALL_PASS_TAGS[tag][3] // 100
    if "delayed" in tags:
        rate = rate * (90 if concept.params[1] <= 70 else 110) // 100
    if situation.blitzer and call.blitz:
        rate = rate * BLITZER_SACK.get(situation.blitzer, 100) // 100
    return max(0, min(3000, rate * SACK_SCALE // 100 + situation.sack_shift))


def band_weights(route: RouteProfile, call: C.Call, tags: frozenset, deeper: int, to_goal: int) -> list:
    factor = DEPTH_FACTOR.get(call.coverage) or SHELL_FACTOR["two_high" in tags]
    weights = [s * f for s, f in zip(route.shares, factor)]
    if call.coverage == C.PREVENT:
        weights = [w * p // 100 for w, p in zip(weights, PREVENT_SHARE)]
    for _ in range(max(0, deeper)):
        moved = [w // 3 for w in weights]
        weights = [w - m for w, m in zip(weights, moved)]
        for b in range(6):
            weights[b + 1] += moved[b]
        weights[6] += moved[6]
    room = to_goal + 9                                  # the back of the end zone
    for b, (low, _high) in enumerate(M.AIR_RANGE):
        if low > room:
            weights[b] = 0
    if not any(weights):
        weights[0] = weights[1] = 1
    return weights


def completion_rate(concept, route: RouteProfile, call: C.Call, tags, band: int, situation: Situation) -> int:
    coverage = call.coverage if call.coverage in COVERAGE_COMP else "COVER_4"
    comp = COVERAGE_COMP[coverage][band] + route.comp_delta
    comp += route.man_zone if "zone" in tags else -route.man_zone
    blitz = SCALE if call.blitz else 0
    comp += (blitz - COVERAGE_BLITZ[coverage]) * M.BLITZ_COMP[band] // SCALE
    if call.coverage == C.PREVENT:
        comp += PREVENT_COMP[band]
    for tag in call.tags:
        if tag in CALL_PASS_TAGS:
            comp += CALL_PASS_TAGS[tag][0] if band <= M.MID else CALL_PASS_TAGS[tag][1] if band >= M.DEEP_IN else 0
    comp += concept.params[2]
    if concept.kind == "play_action":
        effect = M.PLAY_ACTION_COMP[band]
        if situation.down >= 3 and situation.distance >= 7:
            effect = effect * PLAY_ACTION_LATE_DOWN // 100
        comp += effect
    if concept.kind == "rpo":
        comp += RPO_COMP
    if concept.kind == "trick_pass":
        comp += TRICK_COMP
    if concept.kind == "boot" and "contain" in tags:
        comp -= 300
    if motion_on(concept, situation):
        comp += M.MOTION_COMP
    comp += matchup(concept, tags) * MATCHUP_PASS_COMP
    if situation.to_goal <= 10:
        comp -= RED_ZONE_COMP[0] + (10 - situation.to_goal) * RED_ZONE_COMP[1]
    comp += situation.comp_shift
    return max(500, min(9700, comp))


def interception_rate(concept, route: RouteProfile, call: C.Call, tags, band: int) -> int:
    coverage = call.coverage if call.coverage in COVERAGE_INT else "COVER_4"
    rate = COVERAGE_INT[coverage][band] * route.int_pct // 100
    blitz = SCALE if call.blitz else 0
    rate = rate * (10000 + (blitz - COVERAGE_BLITZ[coverage]) * (M.BLITZ_INT[band] - 100) // 100) // 10000
    if call.coverage == C.PREVENT and band >= M.DEEP_IN:
        rate = rate * 130 // 100
    for tag in call.tags:
        if tag in CALL_PASS_TAGS:
            rate = rate * CALL_PASS_TAGS[tag][2] // 100
    if concept.kind == "play_action":
        rate = rate * M.PLAY_ACTION_INT // 100
    if concept.kind == "trick_pass":
        rate = rate * TRICK_INT // 100
    return max(10, min(4000, rate))


def yards_after_catch(rnd, band: int, route: RouteProfile) -> int:
    which = pick(rnd, M.YAC_SHARE[band])
    if which == 0:
        base = 0
    elif which == 1:
        base = between(rnd, 1, 4)
    elif which == 2:
        base = between(rnd, 5, 9)
    elif which == 3:
        base = between(rnd, *M.YAC_MID_RANGE)
    else:
        base = between(rnd, 20, 2 * M.YAC_LONG_MEAN[band] - 20)
    return (base * route.yac_pct + 50) // 100


def interception_return(rnd) -> tuple[int, bool]:
    if chance(rnd, M.INTERCEPTION_RETURN_TD):
        return 100, True
    row = M.INTERCEPTION_RETURN[pick(rnd, [r[2] for r in M.INTERCEPTION_RETURN])]
    return between(rnd, row[0], row[1]), False


def fumble(rnd, kind: str, pct: int = 100) -> tuple[bool, bool, bool]:
    """(fumbled, lost, returned for a touchdown) for a run, a completion, a sack or a scramble (COMPUTED); `pct` the ratings door's
    percent of the rate."""
    rate, lost_share = M.FUMBLE[kind]
    if not chance(rnd, rate * pct // 100):
        return False, False, False
    lost = chance(rnd, lost_share)
    return True, lost, lost and chance(rnd, M.FUMBLE_RETURN_TD.get(kind, 0))


def throw_away_rate(call: C.Call, situation: Situation) -> int:
    """A legal throw-away (the passer outside the pocket, the ball past the line: RB26 8-2-1 Item 1), an incompletion."""
    rate = M.THROW_AWAY_BY_RUSHERS[max(3, min(6, call.rushers))]
    return rate * 70 // 100 if situation.protection == "max" else rate


def pass_play(concept: C.Concept, call: C.Call, situation: Situation, rnd) -> Result:
    tags = call_tags(call)
    if chance(rnd, sack_rate(concept, call, situation, tags)):
        yards = SACK_YARDS[pick(rnd, [w for _y, w in SACK_YARDS])][0]
        if yards == -17:
            yards = between(rnd, -20, -16)
        fumbled, lost, td = fumble(rnd, "sack", situation.fumble_pct)
        if fumbled:
            return Result("fumble", yards, fumble_lost=lost, return_touchdown=td)
        return Result("sack", yards)
    if concept.kind not in ("screen", "rpo") and chance(rnd, throw_away_rate(call, situation)):
        return Result("incomplete", 0, branch="thrown_away")
    if concept.kind == "trick_pass" and concept.id in ("O138", "O140") and chance(rnd, LATERAL_FUMBLE[0]):
        lost = chance(rnd, LATERAL_FUMBLE[1])           # SX.13 (RB26 8-7-1): a fumbled backward pass, told and counted as the laterals'
        return Result("fumble", -between(rnd, 5, 12), gap="laterals", fumble_lost=lost)    # run, never as a sack
    routes = targeted_routes(concept.params[0], situation.target)
    route_name = routes[pick(rnd, [w for _r, w in routes])][0]
    route = ROUTE[route_name]
    weights = band_weights(route, call, tags, concept.params[3], situation.to_goal)
    band = pick(rnd, weights)
    low, high = M.AIR_RANGE[band]
    air = between(rnd, low, high)
    comp = completion_rate(concept, route, call, tags, band, situation)
    ints = interception_rate(concept, route, call, tags, band)
    x = rnd.below(SCALE)
    if x < ints:
        back, td = interception_return(rnd)
        return Result("interception", min(air, situation.to_goal + 9), route_name, band, air, return_yards=back,
                      return_touchdown=td)
    if x >= ints + comp:
        return Result("incomplete", 0, route_name, band, air)
    yards = air + yards_after_catch(rnd, band, route)
    if concept.kind == "play_action":
        yards += M.PLAY_ACTION_YAC
    if concept.id == "O142":                              # the hook and lateral: the trailer gains more or fumbles
        if chance(rnd, LATERAL_FUMBLE[0] * 2):
            return Result("fumble", yards, route_name, band, air, fumble_lost=chance(rnd, LATERAL_FUMBLE[1]))
        yards += between(rnd, 3, 12)
    yards = min(yards + situation.catch_yards, situation.to_goal)
    if yards >= situation.to_goal:                       # SX.13 (RB26 11-2-1, 7-2-1): the ball crossed the goal line in his hands: a
        return Result("complete", yards, route_name, band, air)    # touchdown, the ball dead there, no fumble can follow
    fumbled, lost, td = fumble(rnd, "completion", situation.fumble_pct)
    if fumbled:
        return Result("fumble", yards, route_name, band, air, fumble_lost=lost, return_touchdown=td)
    oob = yards < situation.to_goal and chance(rnd, route.oob)
    return Result("complete", yards, route_name, band, air, out_of_bounds=oob)


# ----- runs (design 4.3) -----

RUN_MEANS: tuple = ()          # the mean yards of each bin, filled below


def _bin_means() -> tuple:
    loss = sum(y * w for y, w in M.RUN_LOSS) / sum(w for _y, w in M.RUN_LOSS)
    long_ = sum((lo + hi) / 2 * w for (lo, hi), w in M.RUN_LONG) / sum(w for _r, w in M.RUN_LONG)
    mids = [(lo + hi) / 2 for lo, hi in M.RUN_RANGES[1:6]]
    return (loss, *mids, long_)


RUN_MEANS = _bin_means()


def shift_bins(bins: list, shift: int) -> list:
    """Move mass between the stuffed bins (loss, no gain) and the gain bins (4-6, 7-9, 10-19) so the mean moves by `shift`
    hundredths of a yard (design 4.3); the 1-3 and 20+ bins keep their share."""
    if not shift:
        return bins
    bins = list(bins)
    total = sum(bins)
    low_idx, high_idx = (0, 1), (3, 4, 5)
    low_mass = sum(bins[i] for i in low_idx)
    high_mass = sum(bins[i] for i in high_idx)
    if not low_mass or not high_mass:
        return bins
    low_mean = sum(bins[i] * RUN_MEANS[i] for i in low_idx) / low_mass
    high_mean = sum(bins[i] * RUN_MEANS[i] for i in high_idx) / high_mass
    moved = total * (shift / 100.0) / (high_mean - low_mean)
    if moved > 0:
        moved = min(moved, low_mass * 0.7)
    else:
        moved = max(moved, -high_mass * 0.5)
    for i in low_idx:
        bins[i] -= moved * bins[i] / low_mass
    for i in high_idx:
        bins[i] += moved * bins[i] / high_mass
    return [max(0, int(round(b))) for b in bins]


def run_bins(gap: str, call: C.Call, tags: frozenset, shift: int, to_goal: int) -> list:
    base = M.RUN_BY_GAP[gap]
    box = max(5, min(8, call.box))
    every = M.RUN_BY_GAP["all"]
    bins = [b * x / e for b, x, e in zip(base, M.RUN_BY_BOX[box], every)]
    for tag in call.tags:
        if tag in CALL_RUN_TAGS:
            bins = [b * f / 100 for b, f in zip(bins, CALL_RUN_TAGS[tag])]
        if gap == "end" and tag in OUTSIDE_TAGS:
            bins = [b * f / 100 for b, f in zip(bins, OUTSIDE_TAGS[tag])]
    bins = [int(round(b)) for b in bins]
    bins = shift_bins(bins, shift)
    return goal_line(bins, to_goal)


def goal_line(bins: list, to_goal: int) -> list:
    """Within GOAL_LINE_YARDS of the goal the runs take the shape of the runs inside the 5 (data: 1.05 a carry)."""
    if to_goal > GOAL_LINE_YARDS:
        return bins
    factors = [inside * 100 // every for inside, every in M.GOAL_LINE_RUNS]
    return [b * factors[min(i, 3)] // 100 for i, b in enumerate(bins)]


def bin_yards(rnd, which: int, qb: bool = False) -> int:
    if which == 0:
        yards = M.RUN_LOSS[pick(rnd, [w for _y, w in M.RUN_LOSS])][0]
        if qb and chance(rnd, M.QB_LOSS_EXTRA):
            yards -= 1
        return yards
    if which == 6:
        if qb:
            return between(rnd, *M.QB_LONG_RANGE)
        low, high = M.RUN_LONG[pick(rnd, [w for _r, w in M.RUN_LONG])][0]
        return between(rnd, low, high)
    low, high = M.RUN_RANGES[which]
    return between(rnd, low, high)


RUN_OOB = {"end": 1990, "tackle": 250, "guard": 70, "middle": 40}


def run_play(concept: C.Concept, call: C.Call, situation: Situation, rnd, gap: str = "", shift: int | None = None,
             table: str = "run") -> Result:
    tags = call_tags(call)
    if not gap:
        gap = concept.params[0]
    if shift is None:
        shift = concept.params[1]
    shift += matchup(concept, tags) * MATCHUP_RUN_SHIFT
    shift += M.FORMATION_RUN_SHIFT.get(formation_class(concept, situation), 0)
    shift += situation.run_shift
    if table == "trick":
        bins = shift_bins(list(M.TRICK_RUN), shift)
    else:
        bins = run_bins(gap, call, tags, shift, situation.to_goal)
    yards = min(bin_yards(rnd, pick(rnd, bins)), situation.to_goal)
    rate = (170, SCALE) if table == "trick" else M.FUMBLE["run"]
    if yards < situation.to_goal and chance(rnd, rate[0] * situation.fumble_pct // 100):    # SX.13: none once he scored
        lost = chance(rnd, rate[1])
        return Result("fumble", yards, gap=gap, fumble_lost=lost,
                      return_touchdown=lost and chance(rnd, M.FUMBLE_RETURN_TD["run"]))
    oob = yards > 0 and yards < situation.to_goal and chance(rnd, RUN_OOB.get(gap, 0))
    return Result("run", yards, gap=gap, out_of_bounds=oob)


def qb_play(concept: C.Concept, call: C.Call, situation: Situation, rnd, table: str = "", shift: int | None = None) -> Result:
    tags = call_tags(call)
    table = table or concept.params[0]
    if shift is None:
        shift = concept.params[1] if concept.kind in ("qb_run", "sneak") else 0
    shift += matchup(concept, tags) * MATCHUP_RUN_SHIFT
    if "spy" in tags or "qb_contain" in tags:
        shift -= MATCHUP_RUN_SHIFT
    shift += situation.run_shift
    bins = list(M.QB_SNEAK if table == "sneak" else M.QB_DESIGNED)
    bins = shift_bins(bins, shift)
    if table != "sneak":                     # a sneak's bins are already the short-yardage shape
        bins = goal_line(bins, situation.to_goal)
    yards = min(bin_yards(rnd, pick(rnd, bins), qb=table != "sneak"), situation.to_goal)
    rate = M.FUMBLE["run"] if table == "sneak" else M.QB_RUN_FUMBLE
    if yards < situation.to_goal and chance(rnd, rate[0] * situation.fumble_pct // 100):    # SX.13: none once he scored
        return Result("fumble", yards, gap="qb", fumble_lost=chance(rnd, rate[1]))
    oob = table != "sneak" and 0 < yards < situation.to_goal and chance(rnd, 1800)
    return Result("run", yards, gap="qb", out_of_bounds=oob)


def read_keeps(call: C.Call, tags: frozenset, rnd) -> bool:
    """The read of an option (design 4.5): the read defender crashes on the dive (keep) or stays home (give)."""
    if tags & {"run_blitz", "slant", "box8"}:
        keep = True
    elif tags & {"contain", "qb_contain", "spy", "scrape"}:
        keep = False
    else:
        keep = rnd.below(2) == 0
    if chance(rnd, OPTION_MISREAD):
        keep = not keep
    return keep


def option_play(concept: C.Concept, call: C.Call, situation: Situation, rnd) -> Result:
    tags = call_tags(call)
    give, keep, pitch = concept.params
    branch = "keep"
    if give and not read_keeps(call, tags, rnd):
        branch = "give"
    if branch == "keep" and pitch:
        pitch_it = bool(tags & {"qb_contain", "spy", "scrape"}) or (not tags & {"pitch"} and rnd.below(2) == 0)
        if chance(rnd, OPTION_MISREAD):
            pitch_it = not pitch_it
        if pitch_it:
            branch = "pitch"
    if branch == "give":
        result = run_play(concept, call, situation, rnd, gap=give, shift=0)
    elif branch == "pitch":
        if chance(rnd, PITCH_FUMBLE[0]):
            return Result("fumble", -between(rnd, 2, 8), gap="end", fumble_lost=chance(rnd, PITCH_FUMBLE[1]), branch="pitch")
        result = run_play(concept, call, situation, rnd, gap="end", shift=20)
    else:
        result = qb_play(concept, call, situation, rnd, table=keep, shift=20)
    return result._replace(branch=branch)


def rpo_play(concept: C.Concept, call: C.Call, situation: Situation, rnd) -> Result:
    tags = call_tags(call)
    gap, routes = concept.params
    heavy = call.box >= 7 or "run_blitz" in tags
    if chance(rnd, RPO_THROW_HEAVY if heavy else RPO_THROW_LIGHT):
        throw = concept._replace(kind="rpo", params=(routes, 100, 0, 0))
        return pass_play(throw, call, situation, rnd)._replace(branch="throw")
    return run_play(concept, call, situation, rnd, gap=gap, shift=0)._replace(branch="give")


def hail_mary(call: C.Call, situation: Situation, rnd) -> Result:
    tags = call_tags(call)
    rushers = max(3, min(6, call.rushers))
    if chance(rnd, M.SACK_BY_RUSHERS[rushers][1 if "two_high" in tags else 0]):
        return Result("sack", SACK_YARDS[pick(rnd, [w for _y, w in SACK_YARDS])][0])
    td = HAIL_MARY["touchdown"] * (50 if situation.to_goal > 60 else 100) // 100
    x = rnd.below(SCALE)
    air = min(situation.to_goal + 5, between(rnd, 40, 60))
    if x < HAIL_MARY["interception"]:
        return Result("interception", air, "go", M.BOMB, air, return_yards=between(rnd, 0, 15))
    if x < HAIL_MARY["interception"] + td:
        return Result("complete", situation.to_goal, "go", M.BOMB, air)
    if x < HAIL_MARY["interception"] + td + HAIL_MARY["caught_short"]:
        return Result("complete", max(0, situation.to_goal - between(rnd, 1, 5)), "go", M.BOMB, air)
    return Result("incomplete", 0, "go", M.BOMB, air)


def laterals(situation: Situation, rnd) -> Result:
    x = rnd.below(SCALE)
    if x < LATERALS["touchdown"]:
        return Result("run", situation.to_goal, gap="laterals")
    if x < LATERALS["touchdown"] + LATERALS["lost"]:
        return Result("fumble", min(situation.to_goal, between(rnd, -10, 15)), gap="laterals", fumble_lost=True)
    return Result("run", min(situation.to_goal, between(rnd, 3, 25)), gap="laterals")


def play(concept: C.Concept, call: C.Call, situation: Situation, rnd) -> Result:
    """Any offense concept against a defense call (design 4.1)."""
    kind = concept.kind
    if kind in ("pass", "screen", "play_action", "boot", "trick_pass", "max_protect"):
        return pass_play(concept, call, situation._replace(protection="max") if kind == "max_protect" else situation, rnd)
    if kind in ("run", "draw"):
        return run_play(concept, call, situation, rnd)
    if kind == "trick_run":
        return run_play(concept, call, situation, rnd, table="trick")
    if kind in ("qb_run", "sneak"):
        return qb_play(concept, call, situation, rnd)
    if kind == "option":
        return option_play(concept, call, situation, rnd)
    if kind == "rpo":
        return rpo_play(concept, call, situation, rnd)
    if kind == "hail_mary":
        return hail_mary(call, situation, rnd)
    if kind == "laterals":
        return laterals(situation, rnd)
    if kind == "kneel":
        return Result("kneel", -1)
    if kind == "spike":
        return Result("spike", 0)
    raise ValueError("no offense model for %r (%s)" % (kind, concept.id))


# ----- kicks of 2026 (design 4.9) -----

class KickResult(NamedTuple):
    kind: str               # touchback, out_of_bounds, returned, landed_short, onside, blocked, muffed, fair_catch, downed,
                            # dead, made, missed, good, no_good
    start: int = 0          # the receiving team's yard line counted from its own goal (a kick) or 0
    returned: int = 0
    touchdown: bool = False
    gross: int = 0
    defense_recovers: bool = False


LANDING_ZONE_FRONT = 20       # RB26 6-1-2 (e): the landing zone is the receivers' 20 to their goal line, wherever the kick is made from


def short_kick_spot(spot: int, safety: bool = False, landed: int = 0) -> int:
    """RB26 6-2-4 penalty (SX.13): a free kick out of bounds, or one that first touches the ground or a player short of the landing zone,
    is the receivers' ball 25 yards from the spot of the kick (30 after a safety), or where it landed or went out when that is nearer
    the kick (`landed`, the receivers' yard line). From the 35: their 40; a safety kick from the 20: their 50."""
    return max(100 - spot - (30 if safety else 25), landed)


def kickoff(kind: str, rnd, spot: int = 35, touchback_pct: int = 100, safety: bool = False) -> KickResult:
    """A free kick of 2026 from the kicking team's 35 (RB26 6-1, 6-2): deep, short into the landing zone, squib. `spot` is the
    kicking team's yard line (the 20 after a safety, farther back after a foul, SX.10d): the catch moves as many yards nearer the
    kicking team; `touchback_pct` scales the touchbacks (a kick from the 20 reaches the end zone less); `safety`: the safety kick
    (6-2-4's 30 yards). A kick from anywhere but the 35 that comes down short of the landing zone is the 6-2-4 foul (SX.13): the draw of
    its catch comes before the return touchdown's, so a kick from the 35 draws exactly what it drew before. The defaults are SX.10b's."""
    if kind == "onside":
        return KickResult("onside")
    if chance(rnd, M.KICKOFF_2026["out_of_bounds"]):
        return KickResult("out_of_bounds", short_kick_spot(spot, safety))
    if kind == "squib" and chance(rnd, SQUIB_SHORT):
        return KickResult("landed_short", short_kick_spot(spot, safety))
    if chance(rnd, KICK_TOUCHBACK.get(kind, 0) * touchback_pct // 100):
        return KickResult("touchback", 35)
    if spot != 35:
        catch = between(rnd, *KICK_CATCH[kind]) + (35 - spot)
        if catch > LANDING_ZONE_FRONT:
            return KickResult("landed_short", short_kick_spot(spot, safety, catch))
        if chance(rnd, M.KICKOFF_2025["return_td"]):
            return KickResult("returned", 100, 100, True)
    else:
        if chance(rnd, M.KICKOFF_2025["return_td"]):
            return KickResult("returned", 100, 100, True)
        catch = between(rnd, *KICK_CATCH[kind])
    low, high = M.KICKOFF_RETURN[pick(rnd, [w for _r, w in M.KICKOFF_RETURN])][0]
    back = between(rnd, low, high) * KICK_RETURN_SCALE[kind] // 100
    start = catch + back
    if start >= 100:
        return KickResult("returned", 100, back, True)
    return KickResult("returned", max(1, start), back)


def punt_gross(rnd) -> int:
    """The distance of a spread punt: whole yards drawn to the percentiles of 2024 to 2026 (COMPUTED)."""
    ranges = (((20, 35), 1000), ((36, 40), 1500), ((41, 46), 2500), ((47, 53), 2500), ((54, 58), 1500), ((59, 70), 1000))
    low, high = ranges[pick(rnd, [w for _r, w in ranges])][0]
    return between(rnd, low, high)


def punt_return_yards(rnd) -> int:
    low, high = M.PUNT_RETURN[pick(rnd, [w for _r, w in M.PUNT_RETURN])][0]
    return between(rnd, low, high)


def punt(kind: str, to_goal: int, defense: str, rnd, free_kick: bool = False, gross_shift: int = 0) -> KickResult:
    """A punt from `to_goal` yards from the receiving team's goal (design 4.9); `defense` is the receiving call (return,
    fair_catch, block, safe). The start is the receiving team's yard line from its own goal. `free_kick`: the safety punt from the
    20 (RB26 11-5-2), which nobody can block; `gross_shift`: the ratings door's yards (SX.10d). The defaults are SX.10b's."""
    k = PUNT_KIND.get(kind, PUNT_KIND["spread"])
    d = KICK_DEFENSE.get(defense, KICK_DEFENSE["return"])
    if not free_kick and chance(rnd, M.PUNT["blocked"] * k["block"] * d["block"] // 10000):
        # the ball comes down behind the line, 5 to 12 yards nearer the kicking team's goal: the receivers' yard line is beyond
        # the line of scrimmage (to_goal from their goal)
        spot = to_goal + between(rnd, 5, 12)
        if spot >= 100:          # SX.13: behind the kicking team's goal line (RB26 11-2, 11-5-1): the receivers fall on it for a touchdown,
            if chance(rnd, BLOCKED_PUNT_END_ZONE_TD):           # or it goes out of the end zone, a safety (start 100, no touchdown)
                return KickResult("blocked", 100, touchdown=True, defense_recovers=True)
            return KickResult("blocked", 100)
        return KickResult("blocked", spot, defense_recovers=True)
    gross = punt_gross(rnd) + k["gross"] + gross_shift
    if kind == "pin":
        gross = min(gross, max(20, to_goal - 10 + between(rnd, -4, 4)))
    land = to_goal - gross                                       # the receiving team's yard line where it comes down
    if land <= 0:
        if chance(rnd, 6000 if kind == "pin" else PUNT_END_ZONE_SAVED):    # downed or stopped short of the goal line
            return KickResult("downed", between(rnd, 2, 9), gross=gross)
        return KickResult("touchback", 20, gross=gross)
    weights = dict(PUNT_INSIDE_20 if land <= 20 else PUNT_FIELD)
    weights["returned"] = weights["returned"] * k["return"] * d["return"] // 10000
    if defense == "fair_catch":
        weights["fair_catch"] += PUNT_FIELD["returned"]
    names = list(weights)
    outcome = names[pick(rnd, [weights[n] for n in names])]
    if outcome != "returned":
        return KickResult(outcome, land, gross=gross)
    if chance(rnd, M.PUNT["muffed_lost"] * 10000 // max(1, M.PUNT["returned"])):
        return KickResult("muffed", land, gross=gross, defense_recovers=True)
    if chance(rnd, M.PUNT["return_td"] * 10000 // M.PUNT["returned"]):
        return KickResult("returned", 100, 100 - land, True, gross)
    back = punt_return_yards(rnd) * k["return"] * d["return"] // 10000
    start = land + back
    if start >= 100:
        return KickResult("returned", 100, back, True, gross)
    return KickResult("returned", start, back, gross=gross)


def field_goal_rate(distance: int) -> tuple[int, int]:
    """(made, blocked) per 10,000 for a kick of `distance` yards (COMPUTED, 2024 to 2026): linear between the bands' middles,
    falling 700 a yard past 66."""
    rows = [((lo + hi) / 2, made, blocked) for (lo, hi), made, blocked, _n in M.FIELD_GOAL]
    if distance <= rows[0][0]:
        return rows[0][1], rows[0][2]
    for (x0, m0, b0), (x1, m1, b1) in zip(rows, rows[1:]):
        if distance <= x1:
            t = (distance - x0) / (x1 - x0)
            return int(m0 + t * (m1 - m0)), int(b0 + t * (b1 - b0))
    last = rows[-1]
    return max(0, int(last[1] - (distance - last[0]) * 700)), last[2]


def field_goal(distance: int, defense: str, rnd, fair_catch_kick: bool = False, made_shift: int = 0) -> KickResult:
    """`made_shift`: the ratings door's points of the made rate (SX.10d); 0 is SX.10b's model."""
    made, blocked = field_goal_rate(distance)
    if made_shift:
        made = max(0, min(9900, made + made_shift))
    if fair_catch_kick:
        made, blocked = min(9900, made + FAIR_CATCH_KICK_BONUS), 0
    if defense == "fg_block":
        blocked *= 2
    elif defense == "fg_safe":
        blocked //= 2
    if chance(rnd, blocked):
        recovers = chance(rnd, FG_BLOCK_RECOVERY)
        return KickResult("blocked", defense_recovers=recovers, touchdown=recovers and chance(rnd, FG_BLOCK_TD))
    return KickResult("made" if chance(rnd, made * 10000 // max(1, 10000 - blocked)) else "missed")


def extra_point(defense: str, rnd) -> KickResult:
    blocked = M.EXTRA_POINT["blocked"] * (2 if defense == "fg_block" else 1)
    if chance(rnd, blocked):
        return KickResult("blocked", defense_recovers=True, touchdown=chance(rnd, 300))
    return KickResult("good" if chance(rnd, M.EXTRA_POINT["good"] * 10000 // (10000 - M.EXTRA_POINT["blocked"])) else "no_good")


def fake_kick(distance: int, defense: str, rnd) -> bool:
    """A fake punt or field goal: did it gain the first down (data: 50 percent of 32 fake punts; shapes UNVERIFIED)."""
    rate = M.FAKE_PUNT["success"]
    for limit, points in FAKE_SUCCESS_BY_DISTANCE:
        if distance <= limit:
            rate += points
            break
    rate = rate * KICK_DEFENSE.get(defense, KICK_DEFENSE["return"])["fake"] // 100
    return chance(rnd, max(500, min(9000, rate)))
