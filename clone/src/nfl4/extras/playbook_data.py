"""The playbooks of the N. F. L. rules mode as data (nfl4 only, rule 0.13; NX5, design 10, built in SX.7). This is inspired by Jim Kitchen.

NFL_EXTRAS_DESIGN 10, MADDEN_PLAYBOOK_RESEARCH 3 to 5 (only the plain football words of its List A, NX-R6). Everything a playbook
has is a number or an ID in this module, never code: `playbooks.py` reads it (and the player's files `plays.txt`, `styles.txt`
and `team_styles.txt` that change it within bounds) and the engine reads only the result through the H8 `modifiers`.

The catalog: one shared list of offense plays (O001 to O052) and defense plays (D001 to D030) with permanent IDs, each mapped to
a FAMILY of the original's tables and spoken in at most six words (the names are STRINGS_NX rows NXO-nn and NXD-nn):
    offense families: 1 Line Plunge, 2 End Run, 3 Screen Pass, 4 Short Pass, 5 Long Pass (the original's, GAME_SPEC 5.9) and the
                      quarterback runs 8 sneak, 9 keeper, 10 draw (SX.5)
    defense families: 1 Goal Line, 2 Short Run, 3 Long Run, 4 Blitz, 5 Short Pass, 6 Long Pass
A play's own tilt is a few `Rule`s, each a strength or a weakness against some calls of the opponent (design 10.3: a play has a
stated strength and a stated weakness, so none is better than the best play of its family against every call).

A MOD changes a family's row only, and by at most BOUNDS: yards low and high each by 2, sack percent and completion percent each by
5 points, the fumble denominator by 5 (1 in 50 is at worst 1 in 45 or 1 in 55). Its sign is the effect on the OFFENSE: for a
defense play a good play has negative yards, negative completion and positive sack, and a fumble denominator below zero.

A STYLE is a list of offense plays and defense plays with the computer's weights, and tilts of its own: at most three BONUS and
three PENALTY entries for each side, of equal total size (design 10.3; `tests/test_nx_playbook_data.py` checks it). Pro Style has
none: it equals Classic in numbers (the control group of the balance test). Classic is not here: it is the original's table.
"""
from __future__ import annotations

from typing import NamedTuple


class Mod(NamedTuple):
    ylo: int = 0       # added to the fewest yards (the table's L44)
    yhi: int = 0       # added to the most yards (the table's L548, one more than the most)
    sack: int = 0      # added to the sack percent of a pass
    comp: int = 0      # added to the completion percent of a pass
    fum: int = 0       # added to the fumble denominator (more is fewer fumbles)

    def size(self) -> int:
        return sum(abs(v) for v in self)

    def plus(self, other: "Mod") -> "Mod":
        return Mod(*(a + b for a, b in zip(self, other)))


ZERO = Mod()
BOUNDS = Mod(2, 2, 5, 5, 5)             # the greatest absolute value of each component (design 10.3)
MOD_NAMES = ("ylo", "yhi", "sack", "comp", "fum")


class Rule(NamedTuple):
    vs: tuple[int, ...]    # the opponent's families this applies to (a play's rule), or the calls (offense) / plays (defense)
    mod: Mod


class Tilt(NamedTuple):
    """A style's entry: its plays of `families` against `vs` change by `mod`."""
    families: tuple[int, ...]
    vs: tuple[int, ...]
    mod: Mod


class Play(NamedTuple):
    id: str                 # O001 .. O052, D001 .. D030
    family: int
    group: int              # offense group 1 to 7 (the groups of the menu, NXB-01 to NXB-07); defense: the family
    rules: tuple[Rule, ...]

    @property
    def side(self) -> str:
        return self.id[0]

    @property
    def number(self) -> int:
        return int(self.id[1:])

    @property
    def name_id(self) -> str:
        return "NX%s-%02d" % ("Y" if self.id[0] == "O" else "Z", self.number)    # NXO is the onside kicks' letter


def M(ylo=0, yhi=0, sack=0, comp=0, fum=0) -> Mod:
    return Mod(ylo, yhi, sack, comp, fum)


def R(vs, mod: Mod) -> Rule:
    return Rule(tuple(vs), mod)


# ----- the archetypes: a strength and a weakness each (offense: vs the defense calls 1 to 6) -----
_ARCHETYPE_RULES: dict[str, tuple[Rule, ...]] = {
    # runs
    "steady": (R((1, 2, 3), M(1)), R((5, 6), M(0, -1))),
    "power": (R((1, 2, 3), M(1, 1)), R((4, 5, 6), M(0, -2))),
    "counter": (R((4,), M(1, 2)), R((1, 2, 3), M(-1))),
    "draw": (R((4, 5, 6), M(0, 2)), R((1, 2, 3), M(-1, -1))),
    "dive": (R((1, 2, 3), M(1, 0, 0, 0, 3)), R((5, 6), M(0, -2))),
    "iso": (R((2, 3), M(1, 1)), R((1, 5, 6), M(-1))),
    "trap": (R((4,), M(0, 2)), R((1, 3), M(-1))),
    "lead": (R((1, 2), M(1)), R((6,), M(0, -1))),
    "stretch": (R((2, 3), M(1, 1)), R((1, 4), M(-1, -1))),
    "zone_out": (R((3, 4), M(0, 2)), R((1, 2), M(-1))),
    "toss": (R((4, 5), M(0, 2, 0, 0, -2)), R((1, 2), M(-1))),
    "jet": (R((2, 3, 4), M(0, 2)), R((1, 5, 6), M(-2))),
    "pitch": (R((5, 6), M(1, 1, 0, 0, -2)), R((2, 3), M(-1, -1))),
    "around": (R((1, 2), M(1, 2, 0, 0, -3)), R((4, 5, 6), M(-1, -1))),
    "speed_option": (R((2, 3, 4), M(1, 1)), R((1,), M(-2, -1))),
    "reverse": (R((4, 5, 6), M(0, 2, 0, 0, -3)), R((1, 2, 3), M(-1, -1))),
    # screens
    "rb_screen": (R((4,), M(0, 2, -3)), R((1, 2, 3), M(-1, 0, 0, -2))),
    "wr_screen": (R((5, 6), M(0, 1, 0, 3)), R((4,), M(0, -2, 3))),
    "te_screen": (R((1, 2, 3), M(1, 0, 0, 3)), R((4,), M(0, -1, 2))),
    "tunnel": (R((2, 3, 5), M(1, 1, 0, 2)), R((4,), M(0, -2, 2, -2))),
    "bubble": (R((1, 2, 3), M(0, 1, 0, 4)), R((5, 6), M(-1, -1, 0, -2))),
    # short passes
    "hitch": (R((1, 2, 3, 6), M(0, 0, 0, 3)), R((4,), M(0, 0, 3, -2))),
    "curl_flat": (R((5,), M(0, 1, 0, 3)), R((4,), M(0, 0, 3))),
    "stick": (R((4, 5), M(0, 0, -3, 2)), R((1,), M(0, -1, 0, -3))),
    "drag": (R((4, 6), M(0, 2, -2)), R((5,), M(0, -1, 0, -3))),
    "mesh": (R((5, 6), M(0, 1, 0, 4)), R((4,), M(-1, 0, 3))),
    "quick_out": (R((2, 4), M(0, 0, -3, 2)), R((5, 6), M(0, -1, 0, -3))),
    "shallow": (R((5,), M(0, 2, 0, 2)), R((1, 2, 3), M(0, -1, 0, -2))),
    "spacing": (R((6,), M(0, 1, 0, 3)), R((4,), M(-1, 0, 2))),
    "rpo": (R((1, 2, 3), M(1, 1)), R((5, 6), M(-1, 0, 0, -3))),
    "slant": (R((4, 5), M(0, 1, 0, 2)), R((1, 2, 3), M(0, 0, 0, -3))),
    # long passes
    "verts": (R((1, 2, 3), M(0, 2, 0, 2)), R((4,), M(0, 0, 4)), R((6,), M(0, -2, 0, -3))),
    "post": (R((1, 2, 3, 5), M(0, 2)), R((6,), M(0, 0, 0, -4))),
    "corner": (R((1, 2), M(0, 1, 0, 3)), R((4, 5), M(0, 0, 3))),
    "go": (R((1, 2, 3), M(0, 2)), R((4, 5, 6), M(0, -1, 0, -2))),
    "deep_cross": (R((5,), M(0, 2, 0, 3)), R((6,), M(0, -2, 0, -3))),
    "flood": (R((5, 6), M(0, 1, 0, 3)), R((4,), M(0, 0, 3, -2))),
    "hail": (R((4, 5), M(0, 2, -3)), R((1, 2, 3, 6), M(0, 0, 0, -3))),
    "wheel": (R((1, 2, 3), M(1, 2)), R((5, 6), M(0, -1, 0, -3))),
    # play action
    "pa_short": (R((1, 2, 3), M(0, 0, -3, 2)), R((6,), M(0, -1, 0, -3))),
    "pa_deep": (R((1, 2, 3), M(0, 2, -3)), R((4, 5, 6), M(0, -1, 0, -3))),
    "boot_short": (R((4,), M(0, 1, -4)), R((1,), M(0, -2, 0, -3))),
    "rollout": (R((4, 5), M(0, 0, -3, 2)), R((6,), M(0, -1, 0, -3))),
    "pa_shot": (R((1, 2, 3), M(0, 2, 0, 2)), R((4, 5, 6), M(0, 0, 3))),
    "pa_cross": (R((5,), M(0, 2, -2, 2)), R((6,), M(0, -2, 0, -2))),
    # the quarterback's runs (ylo, yhi, fum count)
    "q_sneak": (R((1, 2, 3), M(1, 0, 0, 0, 3)), R((5, 6), M(0, -1))),
    "q_keeper": (R((4, 5, 6), M(0, 2)), R((1, 2, 3), M(-1, -1))),
    "q_draw": (R((5, 6), M(0, 2)), R((1, 2), M(-1, -1))),
    "q_option": (R((4, 5), M(1, 2, 0, 0, -2)), R((1,), M(-2, -1))),
    "q_power": (R((1, 2, 3), M(1, 1, 0, 0, -2)), R((4, 5, 6), M(0, -1, 0, 0, -2))),
    "q_push": (R((1,), M(1, 1, 0, 0, 3)), R((5, 6), M(0, -1))),
    "q_boot": (R((1, 2), M(1, 1)), R((4, 5, 6), M(-1, -1, 0, 0, -2))),
    # defense (the sign is the effect on the offense: a good defense play is negative; vs the offense families 1 to 5, 8 to 10)
    "d_goal_up": (R((1, 2), M(-1, -1)), R((3, 4, 5), M(0, 2, 0, 3))),
    "d_goal_stack": (R((1, 8), M(-1, -1)), R((2, 3), M(0, 1))),
    "d_bear": (R((1, 2, 9), M(-1)), R((4, 5), M(0, 0, -2, 2))),
    "d_run_fit": (R((1, 9), M(-1)), R((2,), M(0, 1))),
    "d_run_blitz": (R((1, 2), M(-1, -1, 0, 0, -2)), R((3, 4, 5), M(0, 1, 0, 3))),
    "d_inside_force": (R((1, 8), M(-1)), R((2,), M(0, 1))),
    "d_contain": (R((2, 9), M(-1, -1)), R((1,), M(0, 1))),
    "d_edge": (R((2,), M(-1)), R((5,), M(0, 0, 0, 2))),
    "d_spy": (R((9, 10, 2), M(-1)), R((4,), M(0, 0, 0, 2))),
    "d_zone_blitz": (R((4, 5), M(0, 0, 3, -2)), R((1, 2, 3), M(0, 1))),
    "d_cover0": (R((3, 4, 5), M(0, 1, 3, -2)), R((1, 2, 3), M(1, 2))),
    "d_safety_blitz": (R((4,), M(0, 0, 3, -2)), R((9, 10), M(-1)), R((1, 2, 3), M(0, 1))),
    "d_corner_blitz": (R((4,), M(0, 0, 3, -1)), R((5,), M(0, 1, 0, 2))),
    "d_lb_blitz": (R((1, 2), M(-1)), R((4,), M(0, 0, 2, -2)), R((3, 5), M(0, 1, 0, 1))),
    "d_agap": (R((1,), M(-1)), R((4,), M(0, 0, 3)), R((10,), M(-1, -1)), R((2,), M(0, 1)), R((3, 5), M(0, 1, 0, 2))),
    "d_cover2": (R((4, 5), M(0, 0, 0, -3)), R((1,), M(0, 1))),
    "d_cover3": (R((5,), M(0, -1, 0, -3)), R((3,), M(0, 1, 0, 2))),
    "d_man_free": (R((4,), M(0, 0, 0, -3)), R((9, 10), M(0, 1))),
    "d_under": (R((3, 4), M(0, -1, 0, -2)), R((5,), M(0, 1, 0, 3))),
    "d_nickel": (R((4,), M(0, 0, 0, -3)), R((8,), M(-1)), R((1, 2), M(0, 1))),
    "d_tampa": (R((4,), M(0, -1, 0, -2)), R((5,), M(0, 1, 0, 2))),
    "d_quarters": (R((5,), M(0, -2, 0, -3)), R((1,), M(0, 1))),
    "d_thirds": (R((5,), M(0, -1, 0, -3)), R((4,), M(0, 0, 0, 2))),
    "d_prevent": (R((5,), M(0, -2, 0, -4)), R((3, 4), M(0, 0, 0, 3))),
    "d_cover6": (R((4, 5), M(0, -1, 0, -2)), R((1,), M(0, 1))),
    "d_double": (R((5,), M(0, 0, 0, -4)), R((2,), M(0, 1))),
    "d_palms": (R((4,), M(0, 0, 0, -2)), R((3,), M(0, 0, 0, 2))),
    "d_dime": (R((4, 5), M(0, 0, 0, -2)), R((2,), M(0, 1))),
    "d_man_press": (R((4,), M(0, 0, 0, -3)), R((9, 10), M(-1)), R((5,), M(0, 1, 0, 2))),
}

# (id, family, group, archetype). Offense groups: 1 inside runs, 2 outside runs, 3 screens, 4 short passes, 5 deep passes,
# 6 play action, 7 quarterback runs. The spoken names: NXO-nn and NXD-nn in spec/strings_nx.tsv.
_OFFENSE = (
    ("O001", 1, 1, "steady"), ("O002", 1, 1, "power"), ("O003", 1, 1, "counter"), ("O004", 1, 1, "draw"),
    ("O005", 1, 1, "dive"), ("O006", 1, 1, "iso"), ("O007", 1, 1, "trap"), ("O008", 1, 1, "lead"),
    ("O009", 2, 2, "stretch"), ("O010", 2, 2, "zone_out"), ("O011", 2, 2, "toss"), ("O012", 2, 2, "jet"),
    ("O013", 2, 2, "pitch"), ("O014", 2, 2, "around"), ("O015", 2, 2, "speed_option"), ("O016", 2, 2, "reverse"),
    ("O017", 3, 3, "rb_screen"), ("O018", 3, 3, "wr_screen"), ("O019", 3, 3, "te_screen"), ("O020", 3, 3, "tunnel"),
    ("O021", 3, 3, "bubble"),
    ("O022", 4, 4, "hitch"), ("O023", 4, 4, "quick_out"), ("O024", 4, 4, "curl_flat"), ("O025", 4, 4, "stick"),
    ("O026", 4, 4, "drag"), ("O027", 4, 4, "mesh"), ("O028", 4, 4, "shallow"), ("O029", 4, 4, "spacing"),
    ("O030", 4, 4, "rpo"), ("O031", 4, 4, "slant"),
    ("O032", 5, 5, "verts"), ("O033", 5, 5, "post"), ("O034", 5, 5, "corner"), ("O035", 5, 5, "go"),
    ("O036", 5, 5, "deep_cross"), ("O037", 5, 5, "flood"), ("O038", 5, 5, "hail"), ("O039", 5, 5, "wheel"),
    ("O040", 4, 6, "pa_short"), ("O041", 5, 6, "pa_deep"), ("O042", 4, 6, "boot_short"), ("O043", 4, 6, "rollout"),
    ("O044", 5, 6, "pa_shot"), ("O045", 4, 6, "pa_cross"),
    ("O046", 8, 7, "q_sneak"), ("O047", 9, 7, "q_keeper"), ("O048", 10, 7, "q_draw"), ("O049", 9, 7, "q_option"),
    ("O050", 9, 7, "q_power"), ("O051", 8, 7, "q_push"), ("O052", 9, 7, "q_boot"),
)
_DEFENSE = (
    ("D001", 1, "d_goal_up"), ("D002", 1, "d_goal_stack"), ("D003", 1, "d_bear"),
    ("D004", 2, "d_run_fit"), ("D005", 2, "d_run_blitz"), ("D006", 2, "d_inside_force"),
    ("D007", 3, "d_contain"), ("D008", 3, "d_edge"), ("D009", 3, "d_spy"),
    ("D010", 4, "d_zone_blitz"), ("D011", 4, "d_cover0"), ("D012", 4, "d_safety_blitz"), ("D013", 4, "d_corner_blitz"),
    ("D014", 4, "d_lb_blitz"), ("D015", 4, "d_agap"),
    ("D016", 5, "d_cover2"), ("D017", 5, "d_cover3"), ("D018", 5, "d_man_free"), ("D019", 5, "d_under"),
    ("D020", 5, "d_nickel"), ("D021", 5, "d_tampa"),
    ("D022", 6, "d_quarters"), ("D023", 6, "d_thirds"), ("D024", 6, "d_prevent"), ("D025", 6, "d_cover6"),
    ("D026", 6, "d_double"), ("D027", 6, "d_palms"), ("D028", 5, "d_dime"), ("D029", 6, "d_dime"),
    ("D030", 5, "d_man_press"),
)

CATALOG: tuple[Play, ...] = (
    tuple(Play(i, f, g, _ARCHETYPE_RULES[a]) for i, f, g, a in _OFFENSE)
    + tuple(Play(i, f, f, _ARCHETYPE_RULES[a]) for i, f, a in _DEFENSE))
PLAYS: dict[str, Play] = {p.id: p for p in CATALOG}
OFFENSE_IDS = tuple(p.id for p in CATALOG if p.side == "O")
DEFENSE_IDS = tuple(p.id for p in CATALOG if p.side == "D")
OFFENSE_FAMILIES = (1, 2, 3, 4, 5, 8, 9, 10)
QB_FAMILIES = (8, 9, 10)
DEFENSE_FAMILIES = (1, 2, 3, 4, 5, 6)
OFFENSE_GROUPS = (1, 2, 3, 4, 5, 6, 7)          # NXB-01 .. NXB-07 (QB runs only with the switch on)
MAX_PER_GROUP = 8                                # a group, with Back, Challenge, Time Out and Save Game, is at most 12 items


class Style(NamedTuple):
    code: str                           # PRO, WES, AIR, POW, ZON, OPT, PRE: the start of the IDs in styles.txt
    key: str                            # the setting's value: pro, west, air, power, zone, option, pressure
    name_id: str                        # NXM-28 .. NXM-34
    offense: tuple[tuple[str, int], ...]     # (play ID, the computer's weight)
    defense: tuple[tuple[str, int], ...]
    off_bonus: tuple[Tilt, ...] = ()
    off_penalty: tuple[Tilt, ...] = ()
    def_bonus: tuple[Tilt, ...] = ()
    def_penalty: tuple[Tilt, ...] = ()
    qb_percent: int = 100               # the computer's quarterback runs as a percent of the Classic rate (design 7.4)


def weights(text: str) -> tuple[tuple[str, int], ...]:
    """"O001:5 O002:4" as ((ID, weight), ...)."""
    pairs = []
    for item in text.split():
        play_id, weight = item.split(":")
        pairs.append((play_id, int(weight)))
    return tuple(pairs)


def T(families, vs, mod: Mod) -> Tilt:
    return Tilt(tuple(families), tuple(vs), mod)


_RAW_STYLES: tuple[Style, ...] = (
    Style("PRO", "pro", "NXM-28",
          weights("O001:6 O002:4 O003:3 O004:3 O005:2 O006:2  O009:5 O010:5 O011:4 O012:3 O013:3  "
                  "O017:6 O018:5 O019:4 O020:3 O021:2  O022:3 O023:3 O024:3 O025:2 O027:2 O028:2 O040:2 O042:1 O043:1  "
                  "O032:2 O033:2 O034:2 O036:1 O037:1 O041:1  O044:1  O046:1 O047:1 O048:1"),
          weights("D001:4 D002:3 D003:3  D004:4 D005:3 D006:3  D007:4 D008:3 D009:3  D010:3 D011:2 D012:3 D014:3  "
                  "D016:3 D017:3 D018:2 D020:2  D022:3 D023:3 D025:2")),
    Style("WES", "west", "NXM-29",
          weights("O001:5 O002:3 O003:3 O005:3 O006:2  O009:3 O010:3 O011:3 O013:2  "
                  "O017:7 O018:6 O019:6 O021:5  O022:5 O023:5 O024:4 O025:4 O027:4 O028:3 O040:2 O043:2  "
                  "O033:2 O034:2 O037:2 O041:1  O044:1  O046:1 O047:1 O048:1"),
          weights("D001:3 D002:3 D003:2  D004:3 D006:3 D005:2  D007:3 D008:3 D009:2  D010:3 D012:3 D014:2  "
                  "D016:4 D017:4 D019:3 D020:3 D021:3  D022:3 D023:3 D025:3"),
          off_bonus=(T((3, 4), (1, 2, 3), M(0, 0, -2, 3)),),
          off_penalty=(T((5,), (1, 2, 3, 4, 5, 6), M(0, -2, 0, -3)),),
          def_bonus=(T((5, 6), (3, 4), M(0, 0, 0, -3)),),
          def_penalty=(T((2,), (2,), M(1, 2)),)),
    Style("AIR", "air", "NXM-30",
          weights("O001:3 O004:3 O005:2  O009:3 O010:3 O012:2  "
                  "O017:5 O018:5 O021:4  O022:5 O023:4 O024:4 O025:3 O027:3 O028:3 O040:2  "
                  "O032:4 O033:3 O034:3 O035:3 O036:3 O037:3  O041:2  O044:2  O046:1 O047:1 O048:1"),
          weights("D001:3 D002:2 D003:2  D004:3 D005:2 D006:2  D007:3 D008:2 D009:2  D010:2 D012:3 D014:2  "
                  "D016:4 D017:4 D019:3 D020:4 D028:3  D022:4 D023:3 D029:3"),
          off_bonus=(T((4, 5), (1, 2, 3), M(0, 2, 0, 3)),),
          off_penalty=(T((3, 4, 5), (4, 5, 6), M(0, 0, 3, -2)),),
          def_bonus=(T((5, 6), (4, 5), M(0, 0, 0, -2)),),
          def_penalty=(T((2, 3), (2,), M(0, 2)),)),
    Style("POW", "power", "NXM-31",
          weights("O001:8 O002:8 O003:6 O005:5 O006:5 O008:5  O009:2 O010:2 O014:1 O013:1  "
                  "O019:5 O017:2 O021:1  O022:2 O024:2 O025:3 O030:2 O040:3 O042:2  "
                  "O032:2 O033:2 O034:1 O035:1 O041:3 O044:2  O046:2 O047:1 O048:1 O050:1"),
          weights("D001:5 D002:5 D003:5  D004:5 D005:4 D006:5  D007:3 D008:3 D009:2  D010:2 D012:2 D014:3 D015:3  "
                  "D016:3 D017:3 D018:2 D020:2  D022:3 D023:2 D025:2"),
          off_bonus=(T((1,), (1, 2, 3), M(1)),),
          off_penalty=(T((3, 4, 5), (1, 2, 3, 4, 5, 6), M(0, 0, 0, -1)),),
          def_bonus=(T((1, 2, 3), (1, 2, 8), M(-1)),),
          def_penalty=(T((5, 6), (3, 4, 5), M(0, 0, 0, 1)),)),
    Style("ZON", "zone", "NXM-32",
          weights("O001:4 O003:2 O005:2 O006:2  O009:8 O010:8 O011:4 O012:3 O013:3 O015:2  "
                  "O017:3 O018:3 O019:5 O020:3  O022:3 O023:3 O024:2 O025:3 O027:3 O028:2 O040:5 O042:4 O043:3 O045:3  "
                  "O032:1 O033:2 O034:1 O041:3 O044:2  O046:1 O047:1 O048:1 O052:1"),
          weights("D001:3 D002:3 D003:2  D004:4 D006:3 D005:2  D007:4 D008:4 D009:3  D010:3 D012:2 D014:2  "
                  "D016:3 D017:5 D019:3 D021:3  D022:4 D023:4 D025:3"),
          off_bonus=(T((2,), (1, 2, 3), M(1, 1)), T((4,), (1, 2), M(0, 1, -1, 1))),
          off_penalty=(T((5,), (4, 5, 6), M(0, -2, 0, -3)),),
          def_bonus=(T((5, 6), (5, 2), M(0, -1, 0, -2)),),
          def_penalty=(T((5,), (3, 4), M(0, 1, 0, 2)),)),
    Style("OPT", "option", "NXM-33",
          weights("O001:3 O002:3 O003:3 O004:2 O005:2  O009:4 O010:4 O011:3 O012:3 O014:2 O015:5  "
                  "O017:3 O018:3 O020:3 O021:2  O022:3 O023:3 O025:2 O030:5 O027:2 O028:2 O040:2 O042:3 O043:2  "
                  "O032:1 O034:1 O037:1 O041:2  O044:1  O046:2 O047:2 O048:2 O049:3 O051:1 O052:1"),
          weights("D001:3 D002:3 D003:2  D004:3 D005:3 D006:3  D007:4 D008:3 D009:4  D010:3 D012:3 D014:2  "
                  "D016:2 D017:3 D018:3 D021:2  D022:3 D023:3 D025:2"),
          off_bonus=(T((2,), (4, 5, 6), M(0, 2)), T((9,), (4, 5, 6), M(1, 2))),
          off_penalty=(T((5,), (4, 5, 6), M(0, -2, 0, -3)),),
          def_bonus=(T((2, 3), (2, 9), M(-1, -1)),),
          def_penalty=(T((6,), (5,), M(0, 1, 0, 1)),),
          qb_percent=300),
    Style("PRE", "pressure", "NXM-34",
          weights("O001:4 O002:3 O003:3 O005:2 O006:2  O009:3 O010:3 O011:2 O013:2  "
                  "O017:3 O019:3  O022:2 O023:2 O024:2 O025:2 O028:2 O040:3 O042:2  "
                  "O032:5 O033:4 O034:4 O035:3 O036:3 O037:3 O041:5 O044:4  O046:1 O047:1 O048:1"),
          weights("D001:2 D002:2 D003:2  D004:3 D005:4 D006:2  D007:3 D008:2 D009:2  "
                  "D010:5 D011:4 D012:4 D014:4 D015:4  D016:2 D017:3 D018:4 D030:3  D022:3 D023:2 D026:3"),
          off_bonus=(T((5,), (1, 2, 3), M(0, 2, -2, 2)),),
          off_penalty=(T((3, 4), (4, 5, 6), M(0, 0, 0, -2)), T((5,), (4, 5, 6), M(0, -2, 2, 0))),
          def_bonus=(T((4,), (3, 4, 5), M(0, 0, 2, -1)),),
          def_penalty=(T((4,), (3,), M(0, 1, 0, 2)),)),
)
# What share of its calls (percent) each style gives each of the original's five offense families (the computer's mix; the plays
# of a family share its mass by their relative weights above). Classic's mix is 22, 22, 22, 22 and 11 (GAME_SPEC 5.7). The mixes
# and the tilts are balanced together (work/calibrate_playbooks_sx7.py): a run-heavy style keeps the family that gains the
# most per call but pays for it in its penalty entries.
MASS: dict[str, dict[int, int]] = {
    "PRO": {1: 22, 2: 22, 3: 22, 4: 22, 5: 11},
    "WES": {1: 22, 2: 12, 3: 30, 4: 26, 5: 10},
    "AIR": {1: 10, 2: 10, 3: 18, 4: 40, 5: 22},
    "POW": {1: 23, 2: 17, 3: 15, 4: 33, 5: 12},
    "ZON": {1: 14, 2: 26, 3: 18, 4: 30, 5: 12},
    "OPT": {1: 18, 2: 26, 3: 16, 4: 30, 5: 10},
    "PRE": {1: 19, 2: 14, 3: 14, 4: 36, 5: 17},
}


def _scaled(offense: tuple[tuple[str, int], ...], mass: dict[int, int]) -> tuple[tuple[str, int], ...]:
    """The offense weights with each family's plays scaled so the family's total is `mass` x 10 (whole numbers, at least 1);
    the quarterback runs keep their weights (the computer's rate for them is qb_percent)."""
    totals: dict[int, int] = {}
    for play_id, weight in offense:
        family = PLAYS[play_id].family
        if family <= 5:
            totals[family] = totals.get(family, 0) + weight
    return tuple((play_id, weight if PLAYS[play_id].family > 5 else max(1, round(weight * mass[PLAYS[play_id].family] * 10
                                                                                 / totals[PLAYS[play_id].family])))
                 for play_id, weight in offense)


STYLES: tuple[Style, ...] = tuple(s._replace(offense=_scaled(s.offense, MASS[s.code])) for s in _RAW_STYLES)
STYLE_BY_CODE = {s.code: s for s in STYLES}
STYLE_BY_KEY = {s.key: s for s in STYLES}

# The 32 teams' styles (T01 .. T32, the order of league.DEFAULT_TEAM_NAMES): (offense style key, defense style key)
# MADDEN_PLAYBOOK_RESEARCH 5: the style named for the team, and where EA names a different defensive identity the defense
# (Bengals, Chiefs: Pro Style; Steelers: offense Pro Style, defense Pressure). The weak assignments (Browns, Panthers,
# Lions, Redskins) stay as proposed. Pro 4, West Coast 5 (6 with the Steelers' defense counted apart), Air Raid 6, Power 5,
# Zone 4, Option 5, Pressure 3.
TEAM_STYLES: tuple[tuple[str, str], ...] = (
    ("air", "pro"), ("pressure", "pressure"), ("option", "option"), ("pro", "pressure"),       # A. F. C. North
    ("option", "option"), ("option", "option"), ("pro", "pro"), ("pro", "pro"),                # A. F. C. East
    ("pro", "pro"), ("zone", "zone"), ("air", "pro"), ("zone", "zone"),                        # A. F. C. West
    ("pro", "pro"), ("west", "west"), ("west", "west"), ("power", "power"),                    # A. F. C. South
    ("power", "power"), ("power", "power"), ("west", "west"), ("pressure", "pressure"),        # N. F. C. North
    ("air", "air"), ("option", "option"), ("power", "power"), ("air", "air"),                  # N. F. C. East
    ("option", "option"), ("zone", "zone"), ("air", "air"), ("zone", "zone"),                  # N. F. C. West
    ("air", "air"), ("power", "power"), ("west", "west"), ("west", "west"),                    # N. F. C. South
)
CLASSIC_KEY, TEAM_KEY = "classic", "team"
BOOK_KEYS = (CLASSIC_KEY,) + tuple(s.key for s in STYLES)      # what a game's side can play (state.py checks a save against it)
PLAYBOOK_CHOICES = (CLASSIC_KEY, TEAM_KEY) + tuple(s.key for s in STYLES)    # the F9 items' values, in the order of cycling
