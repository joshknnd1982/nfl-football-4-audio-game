"""The five speakers of NFL Football 4 and their voices. This is inspired by Jim Kitchen.

GAME_SPEC 9.1 and 4.6 to 4.7 (CODE, lifted): the original speaks with five voices chosen by the player: the announcer
and the quarterback and punter of each side (side 1 = the player's team, side 2 = the opponent). Each has a voice number
and a volume (95 by default, 0 to 100). The clone keeps a voice id per role (voice numbers mean nothing on another PC,
GAP_REGISTER G-S8) and gives every role its own volume at every call, also when two roles share a voice (D-022 item 5).
"""
from __future__ import annotations

ANNOUNCER = "announcer"
OWN_QUARTERBACK = "own_quarterback"
OPPONENT_QUARTERBACK = "opponent_quarterback"
OWN_PUNTER = "own_punter"
OPPONENT_PUNTER = "opponent_punter"

# The order ChangeVoice (F12) asks and footbal0.dat stores them (GAME_SPEC 4.7, 12)
ROLES = (ANNOUNCER, OWN_QUARTERBACK, OPPONENT_QUARTERBACK, OWN_PUNTER, OPPONENT_PUNTER)
# SY.1 (the radio broadcast, rule 0.27): Ghip, the color commentator, is a sixth speaker that only the N. F. L. rules use. He is NOT in ROLES:
# the original's F11 and F12 loop over ROLES and Classic must stay exact; the extras' loops add him (game/hotkeys.py).
COLOR = "color"
REFEREE = "referee"            # SY.3: the referee over the public address (extras/stadium.py, speech/pa_effect.py)
EXTRA_ROLES = (COLOR, REFEREE)
ALL_ROLES = ROLES + EXTRA_ROLES
# The order adjvol (F11) walks them = volumes 1 to 5 (GAME_SPEC 4.6, 9.1)
VOLUME_ORDER = (ANNOUNCER, OWN_QUARTERBACK, OWN_PUNTER, OPPONENT_QUARTERBACK, OPPONENT_PUNTER)

DEFAULT_VOLUME = 95          # GAME_SPEC 3 step 4: volumes 1 to 5 = 95
# How the original names them in F11 (GAME_SPEC 4.6) and in F12 (4.7, " Do you wish to use <name> for ...?")
F11_NAMES = {ANNOUNCER: "the announcer", OWN_QUARTERBACK: "your quarterback", OWN_PUNTER: "your punter",
             OPPONENT_QUARTERBACK: "your opponents quarterback", OPPONENT_PUNTER: "your opponents punter"}
F12_NAMES = {ANNOUNCER: "the announcer", OWN_QUARTERBACK: "your quarter back",
             OPPONENT_QUARTERBACK: "your opponent's quarter back", OWN_PUNTER: "your punter",
             OPPONENT_PUNTER: "your opponent's punter"}
EXTRA_NAMES = {COLOR: "Ghip, the color commentator", REFEREE: "the referee"}      # SY.1: the extras' speakers (F11 and F12 say these when they ask for them)


def spoken_name(role: str) -> str:
    """How F11 and F12 name a speaker: the original's words, or the extras' for Ghip."""
    return F11_NAMES.get(role) or EXTRA_NAMES[role]


def player_role(side: int, punter: bool = False) -> str:
    """say3's speaker: the quarterback (qorp = 1) or the punter of side wisoff (1 = the player, 2 = the opponent)."""
    if side == 1:
        return OWN_PUNTER if punter else OWN_QUARTERBACK
    return OPPONENT_PUNTER if punter else OPPONENT_QUARTERBACK


def pronoun(gender: str) -> str:
    """GetSexOf (GAME_SPEC 9.2): " She " when the voice token's Gender attribute is "Female", else " He " (also when
    the voice has no Gender attribute). VB compares texts case by case here, so "female" gives " He " as well."""
    return " She " if (gender or "").strip() == "Female" else " He "
