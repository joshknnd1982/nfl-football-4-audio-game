"""The foul table of the N. F. L. rules mode, 2026 (nfl4 only, rule 0.13; NX7). This is inspired by Jim Kitchen.

NFL_EXTRAS_DESIGN 9.2 (D-042), the rows with their permanent IDs P01 to P26 and P33 (P27 to P32 are kept free for later
rows of NFL_RULES_RESEARCH Part 7 section 0). The yards, spots, loss of down and the automatic first down are the 2026
rulebook's (SRC-OFFICIAL, NFL_RULES_RESEARCH Part 6 and 7, citation per row); the rates are the design's start values from
the 2025 mix (SRC-SECONDARY, Part 8 section 6), per 100 plays the row can happen on, both teams together, and are scaled by
tuning.PENALTY_RATE_SCALE (the calibration of SX.3). The spoken names are the defaults of penalties.txt (STRINGS_NX
NXP-Fnn); the player can rename a foul, switch it off or change its weight (0 to 200 percent), never its yards or spots
(CUSTOMIZABLE_CONTENT 13, L14).

A row that either team can commit (face mask, unnecessary roughness, unsportsmanlike conduct) is two entries with the same
ID, one per offender, each with its share of the rate (design 9.1: one draw over the fitting rows of both teams gives the
foul and its team). Illegal block in the back is two entries too: the offense on a run, the receiving team on a kick-off
return.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..game import outcome as O
from . import rules_2026 as R

# who commits it
OFFENSE, DEFENSE = "offense", "defense"          # on a play from scrimmage (the punt and the field goal too)
KICKING, RECEIVING = "kicking", "receiving"      # on a kick-off

# when it can happen: the dead-ball fouls before the snap, the fouls at the snap (the play is run), the kinds of plays
# (outcome kinds) for the fouls during a play, the fouls after the play, and the onside kick (SX.4)
DEAD, SNAP, AFTER, ONSIDE = "dead", "snap", "after", "onside"
THROWN = (O.PASS_COMPLETE, O.PASS_INCOMPLETE, O.INTERCEPTION)     # a pass that was thrown
FIELD_GOAL = "field goal"                                         # good or missed (not " is way to short")

# where it is enforced from (14-3, 14-4; design 9.4)
SUCCEEDING = "succeeding"           # dead-ball fouls before the snap and fouls after the play (14-4-1, 14-4-9)
PREVIOUS = "previous"               # at the snap and on passes (14-4-1 Item 2, 14-4-5)
SPOT_OF_FOUL = "spot of the foul"   # pass interference by the defense (8-5), fouls by the receivers on a return
DEAD_BALL = "dead ball"             # where the ball became dead (personal fouls by the defense on runs)
THREE_AND_ONE = "three and one"     # runs (14-3-6)
BETTER_OF = "previous or dead ball, the better for the offense"   # personal fouls by the defense on a pass (14-4-5 (d))
PASS_SPOT = "spot of the pass"      # intentional grounding (8-2-1): the worse of 10 from the previous spot and the spot
CATCH_SPOT = "where the receivers got the ball"   # kick catch interference (10-1-1, SX.10d): the receivers' ball, 15 yards on


@dataclass(frozen=True)
class Foul:
    id: str                       # P01: permanent (penalties.txt, the statistics, the tests)
    code: str                     # the rulebook's code (PDF p. 86)
    name_id: str                  # the spoken name's default in STRINGS_NX
    offender: str
    phases: tuple
    yards: int                    # 0: a spot foul (pass interference)
    spot: str
    rate: float                   # per 100 plays it can happen on, before tuning.PENALTY_RATE_SCALE
    rule: str
    loss_of_down: bool = False    # a combination penalty (14-1-2 Item 2)
    personal: bool = False        # a personal or unsportsmanlike foul (14-2-3, 14-2-4)
    team_foul: bool = False       # announced with no player's name
    note: str = ""
    kicks2026: bool = False       # drawn only with the kicks of 2026 (a game where the player uses a playbook, SX.10d, D-094)

    @property
    def automatic_first_down(self) -> bool:
        """14-1-2 Item 5: every foul by the defense gives a first down, except the ten of the list."""
        return self.offender == DEFENSE and self.code not in R.NO_AUTOMATIC_FIRST_DOWN

    @property
    def offense_side(self) -> bool:
        """The foul is by the team that has the ball (the offense, or the receivers on a kick-off return)."""
        return self.offender in (OFFENSE, RECEIVING)


RUN_PASS_SACK = (O.RUN,) + THROWN + (O.SACK,)
PASS_SACK = THROWN + (O.SACK,)
FIELD_PLAYS = (O.RUN, O.PASS_COMPLETE, O.PASS_INCOMPLETE, O.SACK)
KICKOFFS = (O.KICKOFF_RETURN, O.KICKOFF_TOUCH_BACK)

FOULS: tuple[Foul, ...] = (
    Foul("P01", "FST", "NXP-F01", OFFENSE, (DEAD,), 5, SUCCEEDING, 2.0, "7-4-2, 14-4-1"),
    Foul("P02", "DOG", "NXP-F02", OFFENSE, (DEAD,), 5, SUCCEEDING, 0.55, "4-6-5", team_foul=True),
    Foul("P03", "DOF", "NXP-F03", DEFENSE, (SNAP,), 5, PREVIOUS, 0.43, "7-4-5, 14-4-1 Item 2, 14-1-2 Item 5"),
    Foul("P04", "NZI", "NXP-F04", DEFENSE, (DEAD,), 5, SUCCEEDING, 0.23, "7-4-4, 14-1-2 Item 5"),
    Foul("P05", "ENC", "NXP-F05", DEFENSE, (DEAD,), 5, SUCCEEDING, 0.08, "7-4-3, 14-1-2 Item 5"),
    Foul("P06", "ILF", "NXP-F06", OFFENSE, (SNAP,), 5, PREVIOUS, 0.33, "7-5-1, 14-4-1 Item 2"),
    Foul("P07", "ISH", "NXP-F07", OFFENSE, (SNAP,), 5, PREVIOUS, 0.15, "7-4-7, 14-4-1 Item 2"),
    Foul("P08", "OH", "NXP-F08", OFFENSE, RUN_PASS_SACK, 10, THREE_AND_ONE, 2.0, "12-1-3 (c), 14-3-6, 14-4-5",
         note="three and one on a run, the previous spot on a pass or a sack"),
    Foul("P09", "DH", "NXP-F09", DEFENSE, PASS_SACK, 5, PREVIOUS, 0.9, "12-1-6, 14-4-5"),
    Foul("P10", "ILH", "NXP-F10", DEFENSE, PASS_SACK, 5, PREVIOUS, 0.3, "12-1-7, 14-4-5"),
    Foul("P11", "ICT", "NXP-F11", DEFENSE, PASS_SACK, 5, PREVIOUS, 0.5, "8-4-3, 14-4-5", note="never on a Screen Pass"),
    Foul("P12", "DPI", "NXP-F12", DEFENSE, (O.PASS_INCOMPLETE, O.INTERCEPTION), 0, SPOT_OF_FOUL, 3.75, "8-5, 14-4-5 (b)",
         note="1.5 per pass, drawn only on a pass that is not caught (about 40 percent); three times as likely on a "
              "Long Pass as on a Short Pass, never on a Screen Pass; in the end zone first down on the 1"),
    Foul("P13", "OPI", "NXP-F13", OFFENSE, THROWN, 10, PREVIOUS, 0.4, "8-5, 14-4-5"),
    Foul("P14", "RPS", "NXP-F14", DEFENSE, THROWN, 15, BETTER_OF, 0.5, "12-2-11, 14-4-5 (d)", personal=True,
         note="twice as likely against a Blitz"),
    Foul("P15", "ING", "NXP-F15", OFFENSE, (O.PASS_INCOMPLETE,), 10, PASS_SPOT, 0.0, "8-2-1, 14-4-5 (a)",
         loss_of_down=True, note="drawn only in place of a sack (tuning.GROUNDING_PER_10000_SACKS), never by the rate"),
    Foul("P16", "IDP", "NXP-F16", OFFENSE, THROWN, 5, PREVIOUS, 0.2, "8-3-1, 14-4-5", note="three times as likely on a Screen"),
    Foul("P17", "FMM", "NXP-F17", DEFENSE, (O.RUN, O.PASS_COMPLETE, O.SACK), 15, DEAD_BALL, 0.38 * 0.8, "12-2-15",
         personal=True, note="four in five by the defense"),
    Foul("P17", "FMM", "NXP-F17", OFFENSE, (O.RUN, O.PASS_COMPLETE), 15, THREE_AND_ONE, 0.38 * 0.2, "12-2-15, 14-3-6",
         personal=True, note="the ball carrier's face mask: one in five"),
    Foul("P18", "UNR", "NXP-F18", DEFENSE, (AFTER,), 15, SUCCEEDING, 0.54 * 0.75, "12-2-8, 14-4-9", personal=True,
         note="three in four by the defense; after the play"),
    Foul("P18", "UNR", "NXP-F18", OFFENSE, (AFTER,), 15, SUCCEEDING, 0.54 * 0.25, "12-2-8, 14-4-9", personal=True),
    Foul("P19", "IBW", "NXP-F19", OFFENSE, (O.RUN,), 10, THREE_AND_ONE, 0.2, "12-1-3 (b), 14-3-6"),
    Foul("P19", "IBW", "NXP-F19", RECEIVING, (O.KICKOFF_RETURN,), 10, SPOT_OF_FOUL, 2.0, "12-1-3 (b), 14-4-7"),
    Foul("P20", "HC", "NXP-F20", DEFENSE, (O.RUN,), 15, DEAD_BALL, 0.15, "12-2-16", personal=True),
    Foul("P21", "UNS", "NXP-F21", DEFENSE, (AFTER,), 15, SUCCEEDING, 0.17 * 0.5, "12-3-1, 14-4-9", personal=True),
    Foul("P21", "UNS", "NXP-F21", OFFENSE, (AFTER,), 15, SUCCEEDING, 0.17 * 0.5, "12-3-1, 14-4-9", personal=True),
    Foul("P22", "RNK", "NXP-F22", DEFENSE, (O.PUNT, FIELD_GOAL), 5, PREVIOUS, 1.5, "12-2-12, 14-1-2 Item 5"),
    Foul("P23", "RRK", "NXP-F23", DEFENSE, (O.PUNT, FIELD_GOAL), 15, PREVIOUS, 0.5, "12-2-12", personal=True),
    Foul("P24", "OFK", "NXP-F24", KICKING, KICKOFFS + (ONSIDE,), 5, DEAD_BALL, 1.0, "6-1-3, 6-1-6, 14-4-7",
         note="the receivers keep the ball: the yards from the dead ball spot (14-4-7's option); the clone's kick-off "
              "has no kicking spot, so a kick made again would change nothing there; an onside kick has one (35 or 20), "
              "so when the kicking team recovered it the kick is made again from five yards back (SX.4)"),
    Foul("P25", "OH", "NXP-F08", RECEIVING, (O.KICKOFF_RETURN,), 10, SPOT_OF_FOUL, 2.0, "12-1-3 (c), 14-4-7"),
    Foul("P26", "DTM", "NXP-F26", DEFENSE, (SNAP,), 5, PREVIOUS, 0.12, "5-1-2, 14-1-2 Item 5", team_foul=True),
    Foul("P33", "ITK", "NXP-F33", KICKING, (ONSIDE,), 5, SPOT_OF_FOUL, 4.0, "6-2-5",
         note="the onside kick (SX.4): five yards when the receivers have the ball, or the receivers' ball at the spot when "
              "the kicking team recovered it (6-2-5 Item 1)"),
    # the 2026 kick fouls (G26-14, SX.10d; NFL_RULES_RESEARCH Part 7: 6-1-3, 6-2-1, 6-2-2, 10-1-1, 12-3-1). The rates are UNVERIFIED start
    # values (no published per-kick rate); SX.10e measures the fouls a game with them
    Foul("P34", "WED", "NXP-F34", RECEIVING, (O.KICKOFF_RETURN,), 15, SPOT_OF_FOUL, 0.3, "6-2-1, 6-2-2, 14-4-7",
         note="an illegal wedge or double team on the return", kicks2026=True),
    Foul("P35", "IFK", "NXP-F35", KICKING, KICKOFFS, 5, DEAD_BALL, 0.6, "6-1-3, 14-4-7",
         note="the 2026 setup: a player outside his zone or moving before the kick; the receivers keep the ball", kicks2026=True),
    Foul("P36", "LEA", "NXP-F36", DEFENSE, (FIELD_GOAL,), 15, PREVIOUS, 0.2, "12-3-1 (o), (p), (r)", personal=True,
         note="leaping or leverage to block the kick; the down again from 15 yards on, an automatic first down", kicks2026=True),
    Foul("P37", "KCI", "NXP-F37", OFFENSE, (O.PUNT,), 15, CATCH_SPOT, 0.5, "10-1-1, 14-4-8 Exc. (3)",
         note="the kicking team hinders the catch: the receivers' ball 15 yards beyond where they got it", kicks2026=True),
)

IDS: tuple[str, ...] = tuple(dict.fromkeys(f.id for f in FOULS))     # P01 ... P37 in order, each once
BY_ID: dict[str, tuple[Foul, ...]] = {i: tuple(f for f in FOULS if f.id == i) for i in IDS}
GROUNDING = BY_ID["P15"][0]


def name_id(foul_id: str) -> str:
    return BY_ID[foul_id][0].name_id
