"""The catalog of plays of the N. F. L. rules mode: every real NFL play and every Madden NFL playbook concept, in plain football
words (nfl4 only, rule 0.13; NX-P2; design `spec/NFL_PLAYS_DESIGN.md` sections 2 and 3). This is inspired by Jim Kitchen.

The list is the research `spec/NFL_PLAYS_RESEARCH.md` sections 2 to 6, each entry tagged as there: SRC-OFFICIAL (the 2026 rulebook,
the NFL's own pages, NGS, an EA page for a Madden concept), SRC-SECONDARY (a named other source) or UNVERIFIED (a reading). The
IDs are permanent: O001 to O052 and D001 to D030 are SX.7's plays with the same names (the text rows NXY-01 to NXY-52 and NXZ-01
to NXZ-30); new offense plays are O053 on, new defense calls D031 on, the kicks K001 on. LEFT_OUT lists what is not offered and why.

A group is one spoken list of at most ten plays, so a digit and Enter reach every play of a list (design 2.3). The first
groups of each side belong to the original's families (Line Plunge, End Run, Screen Pass, Short Pass, Long Pass; Goal Line,
Short Run, Long Run, Blitz, Short Pass, Long Pass): Right on a family's item opens its first list, Right in a list goes to the
family's next list. The other lists are under "More plays". A play may also be listed in a second list (`also`).

Nothing here is a number of a model: `kind` and `params` name the model and its few inputs (routes and their weights, the
gap a run hits and its shift in hundredths of a yard, the read of an option), and model.py turns them into outcomes.
"""
from __future__ import annotations

from typing import NamedTuple

SRC_OFFICIAL, SRC_SECONDARY, UNVERIFIED = "SRC-OFFICIAL", "SRC-SECONDARY", "UNVERIFIED"


class Group(NamedTuple):
    key: str            # og01 ..; dg01 ..; kg01 ..
    side: str           # O, D or K
    name: str           # spoken (the text row NXB-11 on)
    family: int         # the original's family whose item opens it with Right (0: under More plays or a kick list)
    order: int          # its place among the family's lists (1 is the first)


class Concept(NamedTuple):
    id: str
    side: str           # O offense, D defense, K special teams
    name: str           # the default spoken name: at most six words and 30 characters
    group: str
    kind: str           # the model (model.py): run, draw, qb_run, sneak, option, rpo, pass, screen, play_action, boot, trick_run,
                        # trick_pass, hail_mary, laterals, kneel, spike; call (a defense); kickoff, punt, field_goal, try, ...
    params: tuple       # the model's inputs (see the helpers below)
    formation: str = ""
    personnel: str = ""     # offense: running backs then tight ends ("11"); defense: the defensive backs ("5")
    motion: str = ""        # "", "jet", "orbit"
    strong: tuple = ()      # the defense's tags (offense) or the offense's kinds (defense) this play is good against
    weak: tuple = ()        # and bad against: every play has at least one (no best play, design 4.8)
    tag: str = SRC_SECONDARY
    situations: tuple = ()  # "goal_line", "two_point", "clock", "late", "rare", "fourth_down"
    also: tuple = ()        # other lists it is said in
    family: int = 0         # the original's family whose Enter may draw it (1 to 5 offense, 1 to 6 defense; 0: never)

    @property
    def text_id(self) -> str:
        """The row of spec/strings_nx.tsv that holds the name: NXY offense, NXZ defense, NXB-K.. kicks."""
        number = int(self.id[1:])
        if self.side == "K":
            return "NXB-K%02d" % number
        letter = "Y" if self.side == "O" else "Z"
        if number < 100:
            return "NX%s-%02d" % (letter, number)
        return "NX%s-%s%02d" % (letter, chr(ord("A") + number // 100 - 1), number % 100)


# ----- the lists (design 2.3) -----

GROUPS: tuple[Group, ...] = (
    Group("og01", "O", "Inside Runs", 1, 1), Group("og02", "O", "Power and Gap Runs", 1, 2),
    Group("og03", "O", "Outside Runs", 2, 1), Group("og04", "O", "Misdirection Runs", 2, 2),
    Group("og05", "O", "Screens", 3, 1),
    Group("og06", "O", "Quick Passes", 4, 1), Group("og07", "O", "Crossers and Backs", 4, 2),
    Group("og08", "O", "Intermediate Passes", 4, 3),
    Group("og09", "O", "Deep Passes", 5, 1), Group("og10", "O", "Deep Combinations", 5, 2),
    Group("og11", "O", "Play Action", 0, 1), Group("og12", "O", "Moving Pocket", 0, 2),
    Group("og13", "O", "Quarterback Runs", 0, 3), Group("og14", "O", "Option Runs", 0, 4),
    Group("og15", "O", "Run Pass Options", 0, 5), Group("og16", "O", "Trick Plays", 0, 6),
    Group("og17", "O", "Goal Line and Short Yardage", 0, 7), Group("og18", "O", "Clock Plays", 0, 8),
    Group("og19", "O", "Old Formations", 0, 9), Group("og20", "O", "More Routes", 0, 10),
    Group("dg01", "D", "Goal Line Defenses", 1, 1),
    Group("dg02", "D", "Run Fronts", 2, 1), Group("dg03", "D", "Run Stunts", 2, 2),
    Group("dg04", "D", "Edge and Contain", 3, 1),
    Group("dg05", "D", "Blitzes", 4, 1), Group("dg06", "D", "Pressure Looks", 4, 2),
    Group("dg07", "D", "Zone Coverages", 5, 1), Group("dg08", "D", "Man Coverages", 5, 2),
    Group("dg09", "D", "Two Deep Coverages", 6, 1), Group("dg10", "D", "Deep Help", 6, 2),
    Group("dg11", "D", "Situation Defenses", 0, 1),
    Group("kg01", "K", "Kick Offs", 0, 1), Group("kg02", "K", "Punts", 0, 2),
    Group("kg03", "K", "Field Goals and Tries", 0, 3), Group("kg04", "K", "Kick Defense", 0, 4),
)
GROUP_BY_KEY = {g.key: g for g in GROUPS}
MAX_PER_GROUP = 10


def group_text_id(group: Group) -> str:
    return "NXB-%02d" % (11 + GROUPS.index(group))


# ----- offense helpers: a run hits a gap (middle, guard, tackle, end) with a shift in hundredths of a yard; a pass is routes -----

def _o(pid, name, group, kind, params, *, form="singleback", pers="11", motion="", strong=(), weak=(), tag=SRC_SECONDARY,
       sit=(), also=()):
    family = GROUP_BY_KEY[group].family
    return Concept(pid, "O", name, group, kind, params, form, pers, motion, tuple(strong), tuple(weak), tag, tuple(sit),
                   tuple(also), family)


def run(pid, name, group, gap, shift=0, **kw):
    return _o(pid, name, group, "run", (gap, shift), **kw)


def draw(pid, name, group, gap, shift=0, **kw):
    kw.setdefault("form", "shotgun")
    return _o(pid, name, group, "draw", (gap, shift), **kw)


def passes(pid, name, group, routes, *, kind="pass", sack=100, comp=0, deeper=0, **kw):
    """routes: "hitch 60 quick_out 40"; sack: percent of the drop-back sack rate (time to throw); comp: completion points in
    hundredths; deeper: +1 moves a third of each band's share one band deeper (a curl is a deeper hitch)."""
    bits = routes.split()
    pairs = tuple((bits[i], int(bits[i + 1])) for i in range(0, len(bits), 2))
    kw.setdefault("form", "shotgun")
    return _o(pid, name, group, kind, (pairs, sack, comp, deeper), **kw)


def qb(pid, name, group, table, shift=0, **kw):
    kw.setdefault("form", "shotgun")
    return _o(pid, name, group, "sneak" if table == "sneak" else "qb_run", (table, shift), **kw)


def option(pid, name, group, give, keep, pitch="", **kw):
    """The read (design 4.5): give is a run's gap or "", keep the quarterback's table, pitch a gap or ""."""
    kw.setdefault("form", "shotgun")
    return _o(pid, name, group, "option", (give, keep, pitch), **kw)


def rpo(pid, name, group, gap, routes, **kw):
    bits = routes.split()
    pairs = tuple((bits[i], int(bits[i + 1])) for i in range(0, len(bits), 2))
    kw.setdefault("form", "shotgun")
    return _o(pid, name, group, "rpo", (gap, pairs), **kw)


OFFENSE: tuple[Concept, ...] = (
    # og01 Inside Runs (family 1, Line Plunge)
    run("O001", "Inside Zone", "og01", "guard", 0, strong=("two_high",), weak=("box8",)),
    run("O005", "Dive", "og01", "middle", -20, form="i_form", pers="21", strong=("blitz",), weak=("box8",)),
    draw("O004", "Draw Play", "og01", "guard", 50, strong=("blitz", "light"), weak=("run_blitz", "box8")),
    run("O053", "Split Zone", "og01", "guard", 10, pers="12", strong=("light",), weak=("run_blitz",)),
    run("O054", "Mid Zone", "og01", "tackle", 0, strong=("two_high",), weak=("slant",)),
    draw("O055", "Delayed Draw", "og01", "guard", 40, strong=("blitz",), weak=("run_blitz", "spy")),
    draw("O056", "Lead Draw", "og01", "guard", 30, form="i_form", pers="21", strong=("blitz",), weak=("box8",)),
    run("O057", "Wham", "og01", "middle", 10, pers="12", strong=("run_blitz",), weak=("two_gap",), tag=UNVERIFIED),
    run("O058", "Belly", "og01", "tackle", 0, form="i_form", pers="21", strong=("light",), weak=("pinch",), tag=UNVERIFIED),
    run("O059", "Fullback Dive", "og01", "middle", -30, form="i_form", pers="21", strong=("blitz",), weak=("box8",),
        sit=("goal_line",)),
    # og02 Power and Gap Runs (family 1)
    run("O002", "Power Left", "og02", "guard", 40, form="i_form", pers="21", strong=("light",), weak=("slant",),
        also=("og17",)),
    run("O003", "Counter", "og02", "tackle", 10, pers="12", strong=("run_blitz", "slant"), weak=("contain",)),
    run("O006", "Iso", "og02", "guard", 0, form="i_form", pers="21", strong=("two_high",), weak=("run_blitz",)),
    run("O007", "Trap", "og02", "middle", 10, strong=("run_blitz", "slant"), weak=("two_gap",)),
    run("O008", "Lead Run", "og02", "guard", 0, form="i_form", pers="21", strong=("light",), weak=("box8",)),
    run("O060", "Duo", "og02", "guard", -10, pers="12", strong=("two_high",), weak=("run_blitz",)),
    run("O061", "Counter Trey", "og02", "tackle", 10, pers="12", strong=("run_blitz",), weak=("contain",), tag=UNVERIFIED),
    run("O062", "Fullback Trap", "og02", "middle", 0, form="i_form", pers="21", strong=("run_blitz",), weak=("box8",)),
    run("O063", "Off Tackle", "og02", "tackle", 0, strong=("light",), weak=("pinch",)),
    run("O064", "Cutback Run", "og02", "tackle", 0, strong=("slant",), weak=("two_gap",)),
    # og03 Outside Runs (family 2, End Run)
    run("O009", "Stretch Outside", "og03", "end", -10, strong=("two_high", "slant"), weak=("contain",)),
    run("O010", "Outside Zone", "og03", "end", -10, strong=("light",), weak=("contain",)),
    run("O011", "Toss Sweep", "og03", "end", 10, form="i_form", pers="21", strong=("box8",), weak=("contain",)),
    run("O013", "Pitch", "og03", "end", 0, strong=("blitz",), weak=("contain",)),
    run("O065", "Quick Toss", "og03", "end", 10, strong=("run_blitz",), weak=("contain",)),
    run("O066", "Crack Toss", "og03", "end", 20, strong=("box8",), weak=("contain",), tag=UNVERIFIED),
    run("O067", "Pin and Pull Sweep", "og03", "end", 10, pers="12", strong=("light",), weak=("slant",), tag=UNVERIFIED),
    run("O068", "Double Pull Sweep", "og03", "end", 0, pers="12", strong=("two_high",), weak=("run_blitz",)),
    # og04 Misdirection Runs (family 2)
    run("O012", "Jet Sweep", "og04", "end", 20, motion="jet", form="shotgun", strong=("man",), weak=("contain",)),
    _o("O014", "End Around", "og04", "trick_run", ("end", -40), strong=("slant", "run_blitz"), weak=("contain",)),
    _o("O016", "Reverse", "og04", "trick_run", ("end", -40), strong=("run_blitz",), weak=("contain",)),
    run("O069", "Fake Reverse", "og04", "end", 10, strong=("contain",), weak=("slant",), tag=UNVERIFIED),
    run("O070", "Orbit Sweep", "og04", "end", 10, motion="orbit", form="shotgun", strong=("man",), weak=("contain",),
        tag=UNVERIFIED),
    run("O071", "Jet Fake Inside Zone", "og04", "guard", 20, motion="jet", form="shotgun", strong=("man",), weak=("box8",)),
    # og05 Screens (family 3, Screen Pass)
    passes("O017", "Running Back Screen", "og05", "screen 100", kind="screen", strong=("blitz", "max_blitz"), weak=("drop",)),
    passes("O018", "Receiver Screen", "og05", "screen 100", kind="screen", strong=("two_high",), weak=("press",)),
    passes("O019", "Tight End Screen", "og05", "screen 100", kind="screen", pers="12", strong=("blitz",), weak=("drop",)),
    passes("O020", "Tunnel Screen", "og05", "screen 100", kind="screen", strong=("man",), weak=("drop",)),
    passes("O021", "Bubble Screen", "og05", "screen 100", kind="screen", strong=("box8",), weak=("press",)),
    passes("O072", "Flat Screen", "og05", "swing 100", kind="screen", strong=("blitz",), weak=("zone",)),
    passes("O073", "Middle Screen", "og05", "screen 100", kind="screen", strong=("blitz",), weak=("drop",)),
    passes("O074", "Jailbreak Screen", "og05", "screen 100", kind="screen", strong=("max_blitz",), weak=("press",)),
    passes("O075", "Fullback Screen", "og05", "screen 100", kind="screen", form="i_form", pers="21", strong=("blitz",),
           weak=("drop",)),
    passes("O076", "Shovel Pass", "og05", "screen 100", kind="screen", strong=("blitz",), weak=("spy",)),
    # og06 Quick Passes (family 4, Short Pass)
    passes("O022", "Hitch Routes", "og06", "hitch 100", sack=60, strong=("two_high",), weak=("press",), tag=SRC_OFFICIAL),
    passes("O023", "Quick Out", "og06", "quick_out 100", sack=60, strong=("zone",), weak=("press",), tag=SRC_OFFICIAL),
    passes("O025", "Stick", "og06", "hitch 60 quick_out 40", sack=60, strong=("zone", "blitz"), weak=("man",)),
    passes("O031", "Slants", "og06", "slant 100", sack=60, strong=("blitz",), weak=("drop",), tag=SRC_OFFICIAL,
           also=("og17",)),
    passes("O029", "Spacing", "og06", "hitch 50 quick_out 30 angle 20", sack=65, strong=("zone",), weak=("man",),
           tag=SRC_OFFICIAL),
    passes("O077", "Slant Flat", "og06", "slant 60 quick_out 40", sack=60, strong=("one_high",), weak=("two_high",)),
    passes("O078", "Snag", "og06", "hitch 40 corner 30 quick_out 30", sack=75, strong=("zone",), weak=("man",),
           also=("og17",)),
    passes("O079", "Speed Out", "og06", "quick_out 70 deep_out 30", sack=65, strong=("zone",), weak=("press",)),
    passes("O080", "Fade", "og06", "go 70 corner 30", sack=70, strong=("one_high",), weak=("two_high",), tag=SRC_OFFICIAL),
    passes("O081", "Back Shoulder Fade", "og06", "deep_out 60 go 40", sack=70, strong=("press",), weak=("two_high",)),
    # og07 Crossers and Backs (family 4)
    passes("O024", "Curl and Flat", "og07", "hitch 60 quick_out 40", sack=80, strong=("one_high",), weak=("two_high",)),
    passes("O026", "Drag", "og07", "drag 100", sack=70, strong=("blitz",), weak=("drop",)),
    passes("O027", "Mesh Crossers", "og07", "drag 60 corner 15 swing 15 angle 10", sack=85, strong=("man",), weak=("drop",),
           tag=SRC_OFFICIAL, also=("og17",)),
    passes("O028", "Shallow Cross", "og07", "drag 70 dig 30", sack=85, strong=("blitz",), weak=("drop",)),
    passes("O082", "Drive", "og07", "drag 50 dig 50", sack=95, strong=("one_high",), weak=("two_high",)),
    passes("O083", "Angle Route", "og07", "angle 100", sack=80, strong=("man",), weak=("zone",)),
    passes("O084", "Swing Pass", "og07", "swing 100", sack=60, strong=("blitz",), weak=("zone",)),
    passes("O085", "Check Down", "og07", "swing 50 angle 30 drag 20", sack=70, strong=("two_high",), weak=("man",)),
    passes("O086", "Flat Route", "og07", "quick_out 70 swing 30", sack=65, strong=("one_high",), weak=("two_high",),
           tag=SRC_OFFICIAL),
    passes("O165", "Whip Route", "og07", "quick_out 60 slant 40", sack=70, strong=("man",), weak=("zone",), tag=UNVERIFIED),
    # og08 Intermediate Passes (family 4)
    passes("O088", "Dig", "og08", "dig 100", sack=110, strong=("one_high",), weak=("two_high",), tag=SRC_OFFICIAL),
    passes("O089", "Levels", "og08", "dig 50 hitch 30 drag 20", sack=105, strong=("zone",), weak=("man",), tag=SRC_OFFICIAL),
    passes("O090", "Y Cross", "og08", "dig 50 deep_out 20 corner 15 swing 15", sack=110, pers="12", strong=("one_high",),
           weak=("two_high",)),
    passes("O091", "Smash", "og08", "corner 50 hitch 50", sack=100, strong=("two_high",), weak=("one_high",)),
    passes("O092", "Curl", "og08", "hitch 100", sack=95, deeper=1, strong=("zone",), weak=("press",), tag=SRC_OFFICIAL),
    passes("O093", "Comeback", "og08", "deep_out 100", sack=105, strong=("man",), weak=("two_high",), tag=SRC_OFFICIAL),
    passes("O094", "Out Route", "og08", "deep_out 60 quick_out 40", sack=95, strong=("zone",), weak=("press",),
           tag=SRC_OFFICIAL),
    passes("O095", "Deep Out", "og08", "deep_out 100", sack=110, strong=("one_high",), weak=("two_high",)),
    passes("O096", "Choice Route", "og08", "hitch 40 quick_out 30 slant 30", sack=90, strong=("man",), weak=("drop",)),
    passes("O097", "Sail", "og08", "deep_out 40 quick_out 30 corner 30", sack=110, strong=("one_high",), weak=("two_high",),
           tag=UNVERIFIED),
    # og09 Deep Passes (family 5, Long Pass)
    passes("O032", "Four Verticals", "og09", "go 60 post 20 swing 20", sack=125, strong=("one_high",), weak=("prevent",),
           tag=SRC_OFFICIAL),
    passes("O033", "Deep Post", "og09", "post 100", sack=125, strong=("two_high",), weak=("one_high",), tag=SRC_OFFICIAL),
    passes("O034", "Corner Route", "og09", "corner 100", sack=120, strong=("two_high",), weak=("man",), tag=SRC_OFFICIAL),
    passes("O035", "Go Route", "og09", "go 100", sack=125, strong=("man",), weak=("two_high",)),
    passes("O036", "Deep Cross", "og09", "dig 100", sack=125, deeper=1, strong=("man",), weak=("drop",)),
    passes("O037", "Flood", "og09", "corner 35 deep_out 35 quick_out 30", sack=115, strong=("one_high",), weak=("man",),
           tag=SRC_OFFICIAL),
    passes("O039", "Wheel Route", "og09", "wheel 100", sack=115, strong=("man",), weak=("zone",)),
    passes("O098", "Seam", "og09", "go 60 post 40", sack=120, strong=("one_high",), weak=("two_high",)),
    passes("O099", "Post Corner", "og09", "corner 70 post 30", sack=130, strong=("one_high",), weak=("two_high",)),
    passes("O100", "Double Posts", "og09", "post 70 dig 30", sack=125, strong=("two_high",), weak=("one_high",),
           tag=UNVERIFIED),
    # og10 Deep Combinations (family 5)
    passes("O101", "Dagger", "og10", "dig 50 go 50", sack=125, strong=("one_high",), weak=("two_high",), tag=UNVERIFIED),
    passes("O102", "Mills", "og10", "post 50 dig 50", sack=125, strong=("two_high",), weak=("one_high",), tag=UNVERIFIED),
    passes("O103", "Yankee", "og10", "post 60 dig 40", sack=135, deeper=1, strong=("one_high",), weak=("two_high",),
           tag=UNVERIFIED),
    passes("O104", "Divide", "og10", "go 50 post 50", sack=125, strong=("one_high",), weak=("two_high",)),
    passes("O105", "Scissors", "og10", "corner 50 post 50", sack=125, strong=("two_high",), weak=("man",)),
    passes("O106", "Post Wheel", "og10", "post 50 wheel 50", sack=125, strong=("man",), weak=("two_high",), tag=UNVERIFIED),
    passes("O107", "Sluggo", "og10", "go 100", sack=130, comp=-300, strong=("press",), weak=("two_high",)),
    passes("O108", "Stutter Go", "og10", "go 100", sack=130, comp=-200, strong=("man",), weak=("two_high",)),
    passes("O109", "Out and Up", "og10", "go 70 deep_out 30", sack=130, strong=("man",), weak=("two_high",)),
    # og11 Play Action (More plays)
    passes("O040", "Play Action Short", "og11", "hitch 40 quick_out 30 drag 30", kind="play_action", form="under_center",
           strong=("box8", "run_blitz"), weak=("two_high",)),
    passes("O041", "Play Action Deep", "og11", "post 70 go 30", kind="play_action", form="under_center", sack=120,
           strong=("box8", "one_high"), weak=("two_high",)),
    passes("O044", "Play Action Shot", "og11", "go 60 post 40", kind="play_action", form="under_center", sack=130,
           strong=("box8", "run_blitz"), weak=("two_high",)),
    passes("O045", "Play Action Cross", "og11", "dig 60 drag 40", kind="play_action", form="under_center", sack=110,
           strong=("one_high",), weak=("drop",), tag=SRC_OFFICIAL),
    passes("O111", "Play Action Flood", "og11", "corner 35 deep_out 35 quick_out 30", kind="play_action", form="under_center",
           sack=115, strong=("one_high",), weak=("man",)),
    passes("O112", "Play Action Wheel", "og11", "wheel 60 post 40", kind="play_action", form="under_center", sack=115,
           strong=("man",), weak=("two_high",)),
    passes("O113", "Play Action Screen", "og11", "screen 100", kind="screen", form="under_center", strong=("blitz",),
           weak=("drop",)),
    passes("O114", "Play Action Leak", "og11", "angle 50 quick_out 50", kind="play_action", form="under_center", sack=90,
           strong=("box8", "run_blitz"), weak=("contain",)),
    passes("O115", "Play Action Dig", "og11", "dig 100", kind="play_action", form="under_center", sack=115,
           strong=("one_high",), weak=("two_high",)),
    passes("O116", "Play Action Corner", "og11", "corner 100", kind="play_action", form="under_center", sack=115,
           strong=("two_high",), weak=("man",)),
    # og12 Moving Pocket
    passes("O042", "Bootleg Short", "og12", "quick_out 40 drag 40 corner 20", kind="boot", form="under_center", sack=90,
           strong=("run_blitz", "slant"), weak=("contain",), tag=SRC_OFFICIAL),
    passes("O043", "Rollout", "og12", "quick_out 50 deep_out 30 corner 20", kind="boot", sack=90, strong=("blitz",),
           weak=("contain",), tag=SRC_OFFICIAL),
    passes("O117", "Naked Bootleg", "og12", "quick_out 50 drag 30 corner 20", kind="boot", form="under_center", sack=110,
           strong=("run_blitz",), weak=("contain",)),
    passes("O118", "Waggle", "og12", "drag 40 quick_out 30 deep_out 30", kind="boot", form="under_center", sack=95,
           strong=("slant",), weak=("contain",), tag=SRC_OFFICIAL),
    passes("O119", "Sprint Out", "og12", "quick_out 60 deep_out 40", kind="boot", sack=90, strong=("man",), weak=("contain",)),
    passes("O120", "Max Protect Shot", "og12", "go 50 post 50", kind="max_protect", form="under_center", sack=100,
           pers="12", strong=("blitz", "max_blitz"), weak=("two_high",), tag=UNVERIFIED),
    # og13 Quarterback Runs (also the items 8, 9 and 0 of the original's N. F. L. menu, SX.5)
    qb("O046", "Quarterback Sneak", "og13", "sneak", 0, form="under_center", strong=("light",), weak=("box8",),
       also=("og17",)),
    qb("O047", "Quarterback Keeper", "og13", "designed", 0, strong=("man",), weak=("spy", "qb_contain")),
    qb("O048", "Quarterback Draw", "og13", "designed", 20, strong=("blitz", "man"), weak=("spy", "qb_contain")),
    qb("O050", "Quarterback Power", "og13", "designed", 10, strong=("light",), weak=("spy", "qb_contain")),
    qb("O051", "Sneak Push", "og13", "sneak", 0, form="under_center", strong=("slant",), weak=("two_gap",)),
    qb("O052", "Bootleg Run", "og13", "designed", 0, form="under_center", strong=("run_blitz",), weak=("contain",)),
    qb("O121", "Quarterback Counter", "og13", "designed", 10, strong=("run_blitz",), weak=("spy",)),
    qb("O122", "Quarterback Zone", "og13", "designed", 0, strong=("two_high",), weak=("spy",)),
    qb("O123", "Quarterback Crack Sweep", "og13", "designed", 10, strong=("box8",), weak=("contain",)),
    # og14 Option Runs
    option("O049", "Read Option Keep", "og14", "", "designed", strong=("run_blitz",), weak=("qb_contain", "spy")),
    option("O015", "Speed Option", "og14", "", "designed", "end", strong=("blitz",), weak=("qb_contain", "contain")),
    option("O124", "Zone Read", "og14", "guard", "designed", strong=("slant",), weak=("scrape",)),
    option("O125", "Triple Option", "og14", "middle", "designed", "end", strong=("run_blitz",), weak=("pitch",)),
    option("O126", "Midline Option", "og14", "middle", "designed", strong=("slant",), weak=("scrape",)),
    option("O127", "Inside Veer", "og14", "tackle", "designed", strong=("run_blitz",), weak=("scrape",)),
    option("O128", "Inverted Veer", "og14", "end", "designed", strong=("slant",), weak=("spy",)),
    option("O129", "Power Read", "og14", "end", "designed", strong=("contain",), weak=("spy",)),
    option("O130", "Receiver Pitch Option", "og14", "", "designed", "end", strong=("blitz",), weak=("pitch",)),
    # og15 Run Pass Options
    rpo("O030", "Run Pass Option", "og15", "guard", "slant 50 hitch 50", strong=("box8",), weak=("two_high",)),
    rpo("O131", "Bubble Option", "og15", "guard", "screen 100", strong=("box8",), weak=("press",)),
    rpo("O132", "Glance Option", "og15", "guard", "slant 100", strong=("run_blitz",), weak=("two_high",)),
    rpo("O133", "Quick Flat Option", "og15", "guard", "quick_out 100", strong=("box8",), weak=("press",)),
    rpo("O134", "Stick Option", "og15", "guard", "hitch 60 quick_out 40", strong=("zone", "box8"), weak=("man",)),
    rpo("O135", "Tight End Option", "og15", "guard", "drag 60 wheel 40", pers="12", strong=("box8",), weak=("zone",)),
    rpo("O136", "Jet Option", "og15", "guard", "screen 100", motion="jet", strong=("man",), weak=("contain",)),
    rpo("O137", "Alert Throw", "og15", "guard", "go 100", strong=("box8",), weak=("two_high",), tag=UNVERIFIED),
    # og16 Trick Plays (the computer calls them rarely, design 5.4)
    passes("O138", "Flea Flicker", "og16", "post 40 dig 30 go 30", kind="trick_pass", form="under_center", sack=140,
           strong=("box8", "run_blitz"), weak=("two_high",), sit=("rare",)),
    passes("O139", "Halfback Pass", "og16", "corner 40 dig 30 go 30", kind="trick_pass", sack=120, comp=-300,
           strong=("run_blitz",), weak=("two_high",), sit=("rare",)),
    passes("O140", "Double Pass", "og16", "corner 40 deep_out 30 go 30", kind="trick_pass", sack=120, comp=-200, strong=("box8",),
           weak=("two_high",), tag=SRC_OFFICIAL, sit=("rare",)),
    passes("O141", "Throwback to the Quarterback", "og16", "wheel 100", kind="trick_pass", sack=120, comp=-300,
           strong=("man",), weak=("zone",), sit=("rare",)),
    passes("O142", "Hook and Lateral", "og16", "hitch 100", kind="trick_pass", sack=90, strong=("prevent",), weak=("man",),
           sit=("rare", "late")),
    _o("O143", "Statue of Liberty", "og16", "trick_run", ("end", -40), strong=("blitz",), weak=("contain",), sit=("rare",)),
    passes("O144", "Jet Touch Pass", "og16", "screen 100", kind="screen", motion="jet", strong=("man",), weak=("contain",),
           sit=("rare",)),
    passes("O145", "Fake Sneak Swing", "og16", "swing 100", kind="trick_pass", form="under_center", sack=80,
           strong=("box8",), weak=("contain",), sit=("rare",)),
    passes("O146", "Double Screen", "og16", "screen 100", kind="screen", strong=("blitz",), weak=("drop",), sit=("rare",)),
    passes("O147", "Reverse Pass", "og16", "dig 40 post 30 go 30", kind="trick_pass", sack=140, comp=-300, strong=("run_blitz",),
           weak=("contain",), sit=("rare",)),
    # og17 Goal Line and Short Yardage (and the two-point try's list, design 2.6)
    passes("O148", "Goal Line Fade", "og17", "go 100", sack=70, strong=("man",), weak=("two_high",), sit=("goal_line",)),
    passes("O149", "Rub Routes", "og17", "slant 50 quick_out 50", sack=65, strong=("man",), weak=("zone",),
           sit=("goal_line",)),
    run("O150", "Jumbo Power", "og17", "guard", 30, form="heavy", pers="23", strong=("light",), weak=("run_blitz",),
        sit=("goal_line",)),
    passes("O151", "Tight End Flat", "og17", "angle 50 quick_out 50", kind="play_action", form="heavy", pers="22", sack=80,
           strong=("box8",), weak=("contain",), sit=("goal_line",)),
    # og18 Clock Plays
    _o("O152", "Kneel Down", "og18", "kneel", (), form="victory", strong=("light",), weak=("box8",), tag=SRC_OFFICIAL,
       sit=("clock",)),
    _o("O153", "Spike the Ball", "og18", "spike", (), form="under_center", strong=("light",), weak=("box8",),
       tag=SRC_OFFICIAL, sit=("clock",)),
    passes("O154", "Fake Spike", "og18", "slant 50 go 50", kind="trick_pass", form="under_center", sack=80, comp=200,
           strong=("two_high",), weak=("man",), sit=("clock", "rare")),
    passes("O155", "Victory Formation Pass", "og18", "go 100", kind="trick_pass", form="victory", sack=120, strong=("box8",),
           weak=("two_high",), sit=("clock", "rare")),        # SX.13: no simulated kneel (RB26 7-2-1 (c)); "fake kneel" is LEFT_OUT
    _o("O038", "Hail Mary", "og18", "hail_mary", (), form="shotgun", strong=("one_high",), weak=("prevent",),
       sit=("clock", "late")),
    _o("O156", "Laterals at the End", "og18", "laterals", (), form="shotgun", strong=("prevent",), weak=("man",),
       sit=("clock", "late", "rare")),
    # og19 Old Formations (rare named plays: legal, seldom or never seen today)
    run("O157", "Wishbone Dive", "og19", "middle", -10, form="wishbone", pers="30", strong=("two_high",), weak=("box8",),
        sit=("rare",)),
    option("O158", "Flexbone Option", "og19", "middle", "designed", "end", form="flexbone", pers="30",
           strong=("run_blitz",), weak=("pitch",), sit=("rare",)),
    run("O159", "Single Wing Power", "og19", "tackle", 20, form="single_wing", pers="21", strong=("light",),
        weak=("run_blitz",), sit=("rare",)),
    run("O160", "Wing T Buck Sweep", "og19", "end", 10, form="wing_t", pers="21", strong=("light",), weak=("contain",),
        sit=("rare",)),
    run("O161", "Full House Dive", "og19", "middle", -10, form="full_house", pers="30", strong=("two_high",),
        weak=("box8",), sit=("rare",)),
    run("O162", "Wildcat Run", "og19", "tackle", 10, form="wildcat", strong=("man",), weak=("box8",), sit=("rare",)),
    passes("O163", "Wildcat Pass", "og19", "dig 40 corner 30 go 30", kind="trick_pass", form="wildcat", sack=120, comp=-400,
           strong=("box8",), weak=("two_high",), sit=("rare",)),
    option("O164", "Split T Option", "og19", "", "designed", "end", form="split_t", pers="21", strong=("blitz",),
           weak=("pitch",), sit=("rare",)),
    # og20 More Routes
    passes("O166", "Return Route", "og20", "quick_out 50 hitch 50", sack=75, strong=("man",), weak=("zone",), tag=UNVERIFIED),
    passes("O167", "Bench Route", "og20", "deep_out 60 quick_out 40", sack=95, strong=("zone",), weak=("press",),
           tag=UNVERIFIED),
    passes("O110", "Zig Route", "og20", "quick_out 50 slant 50", sack=85, deeper=1, strong=("man",), weak=("zone",),
           tag=UNVERIFIED),
    passes("O087", "Double Slants", "og20", "slant 100", sack=60, strong=("blitz",), weak=("drop",), tag=SRC_OFFICIAL),
)


# ----- defense: a call is a front, the defensive backs, the box, a coverage, the rushers and its tags -----

class Call(NamedTuple):
    front: str
    backs: int          # defensive backs on the field
    box: int            # defenders in the box (5 is five or fewer, 8 is eight or more)
    coverage: str       # one of model_data.COVERAGE_BANDS, or PREVENT
    rushers: int        # 2 is two or fewer (prevent), 6 six or more
    blitz: bool         # a blitzer (a rusher who is not a lineman)
    tags: tuple         # run_blitz, slant, pinch, spill, two_gap, contain, qb_contain, spy, scrape, pitch, press, off, robber,
                        # bracket, roll, disguise, match, drop, tampa, deep_help, wide, twist, delayed, prevent, hail_mary


PREVENT = "PREVENT"


def _d(pid, name, group, front, backs, box, coverage, rushers, blitz=False, tags=(), *, strong=(), weak=(),
       tag=SRC_SECONDARY, sit=()):
    family = GROUP_BY_KEY[group].family
    return Concept(pid, "D", name, group, "call", Call(front, backs, box, coverage, rushers, blitz, tuple(tags)), front,
                   str(backs), "", tuple(strong), tuple(weak), tag, tuple(sit), (), family)


DEFENSE: tuple[Concept, ...] = (
    # dg01 Goal Line Defenses (family 1, Goal Line)
    _d("D001", "Goal Line Eight Up", "dg01", "goal_line", 3, 8, "COVER_0", 6, True, ("run_blitz",), strong=("run",),
       weak=("pass",), sit=("goal_line",)),
    _d("D002", "Goal Line Stack", "dg01", "goal_line", 3, 8, "COVER_1", 5, False, ("two_gap",), strong=("run",),
       weak=("play_action",), sit=("goal_line",)),
    _d("D003", "Bear Front", "dg01", "46", 4, 8, "COVER_1", 5, True, ("slant",), strong=("run",), weak=("screen",)),
    _d("D031", "Goal Line Six Two", "dg01", "6-2", 3, 8, "COVER_0", 6, False, ("run_blitz",), strong=("run",),
       weak=("pass",), sit=("goal_line",)),
    _d("D032", "Goal Line Five Three", "dg01", "5-3", 3, 8, "COVER_1", 5, False, ("two_gap",), strong=("run",),
       weak=("pass",), sit=("goal_line",)),
    _d("D033", "Short Yardage Four Four", "dg01", "4-4", 3, 8, "COVER_3", 4, False, ("pinch",), strong=("run",),
       weak=("pass",), sit=("goal_line",)),
    _d("D034", "Goal Line Man", "dg01", "goal_line", 4, 7, "COVER_1", 5, True, ("press",), strong=("pass",),
       weak=("run",), sit=("goal_line",)),
    # dg02 Run Fronts (family 2, Short Run)
    _d("D004", "Base Run Fit", "dg02", "4-3", 4, 7, "COVER_3", 4, False, (), strong=("run",), weak=("play_action",)),
    _d("D006", "Inside Run Force", "dg02", "4-3", 4, 7, "COVER_1", 4, False, ("pinch",), strong=("run",), weak=("boot",)),
    _d("D035", "Four Three Over", "dg02", "4-3 over", 4, 7, "COVER_3", 4, False, (), strong=("run",), weak=("pass",)),
    _d("D036", "Four Three Under", "dg02", "4-3 under", 4, 7, "COVER_1", 4, False, (), strong=("run",), weak=("pass",)),
    _d("D037", "Three Four Odd", "dg02", "3-4", 4, 7, "COVER_3", 4, False, ("two_gap",), strong=("run",),
       weak=("screen",)),
    _d("D038", "Tite Front", "dg02", "tite", 5, 6, "COVER_4", 4, False, ("two_gap",), strong=("run",), weak=("draw",)),
    _d("D039", "Forty Six Defense", "dg02", "46", 4, 8, "COVER_1", 5, True, ("slant",), strong=("run",), weak=("pass",)),
    _d("D040", "Five Two", "dg02", "5-2", 4, 8, "COVER_3", 5, False, ("two_gap",), strong=("run",), weak=("pass",)),
    _d("D041", "Six One", "dg02", "6-1", 4, 8, "COVER_1", 6, False, ("run_blitz",), strong=("run",), weak=("pass",)),
    _d("D084", "Big Nickel", "dg02", "big nickel", 5, 7, "COVER_3", 4, False, (), strong=("run",), weak=("pass",),
       tag=UNVERIFIED),
    # dg03 Run Stunts (family 2)
    _d("D005", "Run Blitz", "dg03", "4-3", 4, 8, "COVER_1", 5, True, ("run_blitz",), strong=("run",), weak=("screen",)),
    _d("D042", "Slant Line", "dg03", "4-3", 4, 7, "COVER_3", 4, False, ("slant",), strong=("run",), weak=("counter",)),
    _d("D043", "Angle Line", "dg03", "3-4", 4, 7, "COVER_1", 4, False, ("slant",), strong=("run",), weak=("counter",)),
    _d("D044", "Pinch Line", "dg03", "4-3", 4, 7, "COVER_3", 4, False, ("pinch",), strong=("run",), weak=("outside",)),
    _d("D045", "Spill the Run", "dg03", "4-3", 4, 7, "COVER_3", 4, False, ("spill",), strong=("run",), weak=("outside",)),
    _d("D046", "Box the Run", "dg03", "4-3", 4, 7, "COVER_1", 4, False, ("contain",), strong=("outside",), weak=("run",)),
    _d("D047", "Two Gap Front", "dg03", "3-4", 4, 7, "COVER_3", 4, False, ("two_gap",), strong=("run",), weak=("draw",)),
    _d("D048", "One Gap Charge", "dg03", "4-3", 4, 7, "COVER_1", 4, False, ("slant", "run_blitz"), strong=("run",),
       weak=("draw",)),
    # dg04 Edge and Contain (family 3, Long Run)
    _d("D007", "Contain Outside Force", "dg04", "4-3", 4, 7, "COVER_3", 4, False, ("contain",), strong=("outside",),
       weak=("run",)),
    _d("D008", "Edge Setting", "dg04", "4-3", 4, 7, "COVER_2", 4, False, ("contain",), strong=("outside",), weak=("run",)),
    _d("D009", "Spy", "dg04", "nickel", 5, 6, "COVER_1", 4, False, ("spy",), strong=("qb_run",), weak=("pass",)),
    _d("D049", "Wide Nine", "dg04", "4-3 wide", 4, 6, "COVER_2", 4, False, ("wide",), strong=("pass",), weak=("run",),
       tag=SRC_SECONDARY),
    _d("D050", "Quarterback Contain", "dg04", "4-3", 4, 7, "COVER_3", 4, False, ("qb_contain", "contain"),
       strong=("option",), weak=("run",), tag=SRC_OFFICIAL),
    _d("D051", "Pitch Assignment", "dg04", "4-3", 4, 7, "COVER_3", 4, False, ("pitch",), strong=("option",), weak=("pass",)),
    _d("D052", "Scrape Exchange", "dg04", "4-3", 4, 7, "COVER_1", 4, False, ("scrape",), strong=("option",),
       weak=("run",), tag=UNVERIFIED),
    # dg05 Blitzes (family 4, Blitz)
    _d("D010", "Zone Blitz", "dg05", "nickel", 5, 6, "COVER_3", 5, True, ("drop",), strong=("pass",), weak=("screen",),
       tag=SRC_OFFICIAL),
    _d("D011", "Cover Zero Blitz", "dg05", "nickel", 5, 7, "COVER_0", 6, True, (), strong=("pass",), weak=("screen",)),
    _d("D012", "Safety Blitz", "dg05", "nickel", 5, 7, "COVER_1", 5, True, (), strong=("pass",), weak=("screen",)),
    _d("D013", "Corner Blitz", "dg05", "nickel", 5, 6, "COVER_3", 5, True, (), strong=("pass",), weak=("screen",)),
    _d("D014", "Linebacker Blitz", "dg05", "4-3", 4, 7, "COVER_1", 5, True, (), strong=("run",), weak=("screen",)),
    _d("D015", "A Gap Blitz", "dg05", "nickel", 5, 7, "COVER_1", 5, True, (), strong=("qb_run",), weak=("screen",)),
    _d("D053", "Double A Gap", "dg05", "nickel", 5, 7, "COVER_1", 6, True, (), strong=("pass",), weak=("screen",)),
    _d("D054", "Nickel Blitz", "dg05", "nickel", 5, 6, "COVER_1", 5, True, (), strong=("pass",), weak=("screen",)),
    _d("D055", "Dime Blitz", "dg05", "dime", 6, 6, "COVER_1", 5, True, (), strong=("pass",), weak=("run",)),
    _d("D056", "Defensive Back Fire", "dg05", "nickel", 5, 6, "COVER_0", 6, True, (), strong=("pass",), weak=("screen",)),
    # dg06 Pressure Looks (family 4)
    _d("D057", "Fire Zone", "dg06", "nickel", 5, 6, "COVER_3", 5, True, ("drop",), strong=("pass",), weak=("screen",),
       tag=SRC_OFFICIAL),
    _d("D058", "Overload Blitz", "dg06", "nickel", 5, 7, "COVER_1", 6, True, (), strong=("pass",), weak=("screen",),
       tag=UNVERIFIED),
    _d("D059", "Simulated Pressure", "dg06", "nickel", 5, 6, "COVER_3", 4, True, ("disguise", "drop"), strong=("pass",),
       weak=("run",)),
    _d("D060", "Creeper", "dg06", "nickel", 5, 6, "COVER_3", 4, True, ("disguise",), strong=("pass",), weak=("run",)),
    _d("D061", "Delayed Blitz", "dg06", "4-3", 4, 7, "COVER_1", 5, True, ("delayed",), strong=("play_action",),
       weak=("quick",), tag=UNVERIFIED),
    _d("D062", "Cross Blitz", "dg06", "4-3", 4, 7, "COVER_1", 5, True, (), strong=("run",), weak=("screen",), tag=UNVERIFIED),
    _d("D063", "Free Fire", "dg06", "nickel", 5, 7, "COVER_0", 6, True, (), strong=("pass",), weak=("screen",)),
    _d("D064", "Twist Stunt", "dg06", "nickel", 5, 6, "COVER_3", 4, False, ("twist",), strong=("pass",), weak=("draw",)),
    _d("D065", "Loop Stunt", "dg06", "nickel", 5, 6, "COVER_2", 4, False, ("twist",), strong=("pass",), weak=("draw",)),
    _d("D066", "Edge Blitz", "dg06", "nickel", 5, 6, "COVER_1", 5, True, (), strong=("pass",), weak=("outside",)),
    # dg07 Zone Coverages (family 5, Short Pass)
    _d("D016", "Cover Two Zone", "dg07", "nickel", 5, 6, "COVER_2", 4, False, (), strong=("pass",), weak=("run",),
       tag=SRC_OFFICIAL),
    _d("D017", "Cover Three Zone", "dg07", "4-3", 4, 7, "COVER_3", 4, False, (), strong=("pass",), weak=("quick",)),
    _d("D019", "Underneath Zone", "dg07", "nickel", 5, 6, "COVER_2", 4, False, ("drop",), strong=("quick",),
       weak=("deep",)),
    _d("D020", "Nickel Quick Coverage", "dg07", "nickel", 5, 6, "COVER_3", 4, False, ("match",), strong=("quick",),
       weak=("run",)),
    _d("D021", "Tampa Two", "dg07", "nickel", 5, 6, "COVER_2", 4, False, ("tampa",), strong=("deep",), weak=("run",)),
    _d("D067", "Cover Three Sky", "dg07", "4-3", 4, 7, "COVER_3", 4, False, (), strong=("run",), weak=("deep",)),
    _d("D068", "Cover Three Cloud", "dg07", "nickel", 5, 6, "COVER_3", 4, False, ("press",), strong=("quick",),
       weak=("deep",)),
    _d("D069", "Cover Three Buzz", "dg07", "nickel", 5, 6, "COVER_3", 4, False, ("robber",), strong=("pass",),
       weak=("outside",)),
    _d("D070", "Cover Three Match", "dg07", "nickel", 5, 6, "COVER_3", 4, False, ("match",), strong=("deep",),
       weak=("quick",)),
    _d("D071", "Drop Eight", "dg07", "nickel", 5, 6, "COVER_3", 3, False, ("drop",), strong=("pass",), weak=("run",)),
    # dg08 Man Coverages (family 5)
    _d("D018", "Man Free", "dg08", "nickel", 5, 7, "COVER_1", 4, False, (), strong=("pass",), weak=("crossers",)),
    _d("D030", "Man Press", "dg08", "nickel", 5, 7, "COVER_1", 4, False, ("press",), strong=("quick",), weak=("deep",)),
    _d("D072", "Cover One Robber", "dg08", "nickel", 5, 7, "COVER_1", 4, False, ("robber",), strong=("crossers",),
       weak=("deep",)),
    _d("D073", "Two Man", "dg08", "nickel", 5, 6, "2_MAN", 4, False, (), strong=("pass",), weak=("qb_run",)),
    _d("D074", "Off Man", "dg08", "nickel", 5, 7, "COVER_1", 4, False, ("off",), strong=("deep",), weak=("quick",)),
    _d("D075", "Man Three Deep", "dg08", "nickel", 5, 6, "COVER_1", 3, False, ("deep_help",), strong=("deep",),
       weak=("run",), tag=UNVERIFIED),
    _d("D076", "Cover One Contain", "dg08", "nickel", 5, 7, "COVER_1", 4, False, ("qb_contain",), strong=("qb_run",),
       weak=("deep",)),
    # dg09 Two Deep Coverages (family 6, Long Pass)
    _d("D022", "Cover Four Quarters", "dg09", "nickel", 5, 6, "COVER_4", 4, False, (), strong=("deep",), weak=("quick",)),
    _d("D025", "Cover Six", "dg09", "nickel", 5, 6, "COVER_6", 4, False, (), strong=("deep",), weak=("run",),
       tag=SRC_OFFICIAL),
    _d("D027", "Palms", "dg09", "nickel", 5, 6, "COVER_4", 4, False, ("press",), strong=("quick",), weak=("deep",),
       tag=UNVERIFIED),
    _d("D077", "Match Quarters", "dg09", "nickel", 5, 6, "COVER_4", 4, False, ("match",), strong=("deep",),
       weak=("crossers",)),
    _d("D078", "Cover Nine", "dg09", "nickel", 5, 6, "COVER_9", 4, False, (), strong=("deep",), weak=("quick",),
       tag=UNVERIFIED),
    _d("D079", "Two Deep Disguise", "dg09", "nickel", 5, 7, "COVER_3", 4, False, ("disguise",), strong=("pass",),
       weak=("run",)),
    _d("D080", "Cover Two Match", "dg09", "nickel", 5, 6, "COVER_2", 4, False, ("match",), strong=("deep",),
       weak=("run",)),
    _d("D088", "Cover Two Hard Flat", "dg09", "nickel", 5, 6, "COVER_2", 4, False, ("press",), strong=("quick",),
       weak=("deep",)),
    _d("D089", "Cover Two Invert", "dg09", "nickel", 5, 6, "COVER_2", 4, False, ("disguise",), strong=("deep",),
       weak=("quick",), tag=UNVERIFIED),
    _d("D090", "Cover Four Drop", "dg09", "nickel", 5, 6, "COVER_4", 4, False, ("drop",), strong=("crossers",),
       weak=("quick",)),
    # dg10 Deep Help (family 6)
    _d("D023", "Deep Thirds", "dg10", "nickel", 5, 6, "COVER_3", 4, False, ("deep_help",), strong=("deep",),
       weak=("quick",)),
    _d("D024", "Prevent Deep", "dg10", "prevent", 7, 5, PREVENT, 3, False, ("prevent",), strong=("deep",), weak=("run",)),
    _d("D026", "Double Coverage", "dg10", "nickel", 5, 6, "COVER_2", 4, False, ("bracket",), strong=("deep",),
       weak=("run",)),
    _d("D028", "Dime Short Coverage", "dg10", "dime", 6, 6, "COVER_2", 4, False, ("drop",), strong=("quick",),
       weak=("run",)),
    _d("D029", "Dime Deep Coverage", "dg10", "dime", 6, 5, "COVER_4", 4, False, ("deep_help",), strong=("deep",),
       weak=("run",)),
    _d("D081", "Bracket Coverage", "dg10", "nickel", 5, 6, "COVER_1", 4, False, ("bracket",), strong=("deep",),
       weak=("run",), tag=SRC_OFFICIAL),
    _d("D082", "Safety Rotation", "dg10", "nickel", 5, 6, "COVER_3", 4, False, ("roll",), strong=("deep",),
       weak=("quick",), tag=SRC_OFFICIAL),
    _d("D083", "Quarter Defense", "dg10", "quarter", 7, 5, "COVER_4", 4, False, ("deep_help",), strong=("deep",),
       weak=("run",)),
    _d("D091", "Cover Three Seam", "dg10", "nickel", 5, 6, "COVER_3", 4, False, ("deep_help",), strong=("deep",),
       weak=("quick",)),
    _d("D092", "Cover Four Press", "dg10", "nickel", 5, 6, "COVER_4", 4, False, ("press",), strong=("quick",),
       weak=("deep",)),
    # dg11 Situation Defenses (More plays)
    _d("D085", "Hail Mary Defense", "dg11", "prevent", 7, 5, PREVENT, 3, False, ("prevent", "hail_mary"),
       strong=("deep",), weak=("run",), sit=("late",)),
    _d("D086", "Two Point Defense", "dg11", "goal_line", 4, 7, "COVER_1", 5, True, ("press",), strong=("pass",),
       weak=("run",), sit=("two_point", "goal_line")),
    _d("D087", "Two Minute Defense", "dg11", "nickel", 5, 6, "COVER_2", 4, False, ("deep_help",), strong=("deep",),
       weak=("quick",), sit=("late",)),
)

# ----- special teams (design 4.9) -----


def _k(pid, name, group, kind, params=(), *, strong=(), weak=(), tag=SRC_SECONDARY, sit=(), also=()):
    return Concept(pid, "K", name, group, kind, tuple(params), "", "", "", tuple(strong), tuple(weak), tag, tuple(sit),
                   tuple(also), 0)


KICKS: tuple[Concept, ...] = (
    _k("K001", "Deep Kick", "kg01", "kickoff", ("deep",), strong=("return",), weak=("touchback",), tag=SRC_OFFICIAL),
    _k("K002", "Short Kick", "kg01", "kickoff", ("short",), strong=("touchback",), weak=("return",), tag=SRC_OFFICIAL),
    _k("K003", "Squib Kick", "kg01", "kickoff", ("squib",), strong=("return",), weak=("short",)),
    _k("K004", "Onside Kick", "kg01", "kickoff", ("onside",), strong=("late",), weak=("field",), tag=SRC_OFFICIAL),
    _k("K011", "Punt", "kg02", "punt", ("spread",), strong=("return",), weak=("block",)),
    _k("K012", "Pin Punt", "kg02", "punt", ("pin",), strong=("field",), weak=("touchback",)),
    _k("K013", "Rugby Punt", "kg02", "punt", ("rugby",), strong=("block",), weak=("distance",)),
    _k("K014", "Tight Punt", "kg02", "punt", ("tight",), strong=("block",), weak=("return",), tag=SRC_OFFICIAL),
    _k("K015", "Fake Punt Run", "kg02", "fake", ("run",), strong=("return",), weak=("safe",), sit=("rare", "fourth_down")),
    _k("K016", "Fake Punt Pass", "kg02", "fake", ("pass",), strong=("block",), weak=("safe",), sit=("rare", "fourth_down")),
    _k("K021", "Field Goal", "kg03", "field_goal", ("kick",), strong=("safe",), weak=("block",)),
    _k("K022", "Fake Field Goal Run", "kg03", "fake", ("run",), strong=("block",), weak=("safe",), sit=("rare",)),
    _k("K023", "Fake Field Goal Pass", "kg03", "fake", ("pass",), strong=("block",), weak=("safe",), sit=("rare",)),
    _k("K024", "Extra Point Kick", "kg03", "try", ("kick",), strong=("safe",), weak=("block",), tag=SRC_OFFICIAL,
       sit=("try",)),
    _k("K025", "Fair Catch Kick", "kg03", "fair_catch_kick", (), strong=("block",), weak=("distance",), tag=SRC_OFFICIAL,
       sit=("fair_catch",)),
    _k("K026", "Swinging Gate Try", "kg03", "try", ("gate",), strong=("block",), weak=("safe",), sit=("two_point", "rare"),
       also=("og17",)),
    _k("K027", "Safety Punt", "kg01", "kickoff", ("safety_punt",), strong=("return",), weak=("distance",), tag=SRC_OFFICIAL),
    _k("K031", "Punt Return", "kg04", "kick_defense", ("return",), strong=("spread",), weak=("pin",)),
    _k("K032", "Fair Catch", "kg04", "kick_defense", ("fair_catch",), strong=("pin",), weak=("spread",), tag=SRC_OFFICIAL),
    _k("K033", "Punt Block", "kg04", "kick_defense", ("block",), strong=("spread",), weak=("fake",)),
    _k("K034", "Punt Safe", "kg04", "kick_defense", ("safe",), strong=("fake",), weak=("spread",)),
    _k("K035", "Field Goal Block", "kg04", "kick_defense", ("fg_block",), strong=("kick",), weak=("fake",)),
    _k("K036", "Field Goal Safe", "kg04", "kick_defense", ("fg_safe",), strong=("fake",), weak=("kick",)),
)

CATALOG: tuple[Concept, ...] = OFFENSE + DEFENSE + KICKS
BY_ID: dict[str, Concept] = {c.id: c for c in CATALOG}

# What the research lists and the game does not offer, with the reason (design 2.8). A test requires every research name to be
# in the catalog, here, or merged into a named play (MERGED).
LEFT_OUT = {
    "fumblerooski": "a ball left on the ground on purpose is a forward pass or a fumble the defense may take (RB26 7-6-4, 8-1-1(c)); "
                    "its usual form is not legal",
    "fake kneel": "the ball is dead when the quarterback drops to a knee or simulates it (RB26 7-2-1 (c), SX.13); O155 Victory Formation "
                  "Pass is the legal form: the victory formation and a pass at once, with no kneel shown",
    "drop kick": "legal, last used in 2006; the research recommends not offering it",
    "quick kick": "legal from a scrimmage formation, no recent use; not offered (research 4.2)",
    "sky kick": "the 2026 kick-off's coverage may not move until the ball lands, so height gains nothing (RB26 6-1-3)",
    "surprise onside kick": "the 2026 rules require the onside kick to be declared (RB26 6-1-6); K004 is the declared one",
    "kick-off fair catch": "the research could not settle whether the 2026 landing zone allows it; not offered",
    "follow": "no reliable definition (research 11)",
    "hank": "no reliable definition (research 11)",
    "audible": "a turn-based call already picks any play at the menu; an audible adds no choice",
    "hot route": "one receiver's route changed: each route's concept is in the list instead",
    "kick-off return choices": "the receiving team's return and its hands team (against a declared onside kick) are automatic",
    "punt return direction": "middle, sideline and wall returns have no published difference; one return model",
}
MERGED = {
    "texas": "O083", "double slants": "O087", "all hitches": "O022", "slip screen": "O017", "power option": "O129",
    "zone read hand-off": "O124", "smoke": "O018", "spot": "O078", "halfback flat screen": "O072", "lead zone": "O053",
    "blast": "O008", "pull lead": "O008", "buck sweep": "O067", "slash": "O063", "jumbo": "O150", "pooch punt": "K012",
    "coffin corner": "K012", "sky punt": "K012", "spread punt": "K011", "shield punt": "K011", "hands team": "K004",
    "dollar": "D028", "nickel 4-2-5": "D016", "dime 4-1-6": "D028", "okie": "D037", "mint": "D038", "46": "D039",
    "cover 1 hole": "D018", "cover 2 man": "D073", "cover 9": "D078", "red zone coverage": "D086", "spy": "D009",
    "wildcat direct snap": "O162", "victory formation": "O152", "cover 2 sink": "D019", "cover 2 drop": "D019",
    "cover 2 roll": "D082", "cover 3 hard flat": "D068", "cover 1 press": "D030", "double safety blitz": "D012",
    "mike blitz": "D014", "will blitz": "D014", "sam blitz": "D014", "4-3 even": "D035", "4-3 odd": "D036",
    "eight in the box": "D005", "contain rush": "D007", "stacked box": "D005",
}

# The pre-snap tools and formations are remembered settings of a game, not plays (design 2.5): name -> values
SETTINGS = {
    "formation": ("book", "under_center", "shotgun", "pistol", "singleback", "i_form", "split_backs", "empty", "heavy"),
    "personnel": ("book", "11", "12", "13", "21", "22", "10", "20", "01", "00"),
    "motion": ("book", "none", "jet", "orbit", "shift"),
    "side": ("book", "left", "right"),
    "tempo": ("normal", "no_huddle", "hurry_up"),
    "protection": ("normal", "max", "slide"),
    "defense_personnel": ("match", "base 4-3", "base 3-4", "nickel 4-2-5", "nickel 3-3-5", "nickel 2-4-5", "big nickel",
                          "dime 4-1-6", "dime 3-2-6", "quarter", "2-5", "heavy"),
    "coverage_shade": ("book", "press", "off"),
}
