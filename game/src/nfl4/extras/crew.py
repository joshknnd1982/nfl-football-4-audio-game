"""The radio crew's names: the play-by-play announcer, the color analyst, the sideline reporter and the network (nfl4 only, rule 0.13; BC.3,
D-178, D-189). This is inspired by Jim Kitchen.

spec/NFL_BROADCAST_DESIGN.md section 3: the crew are made-up people (a web search of 2026-10-26 found no real broadcaster with these names),
and the player may rename each of them and the network in F9, Rules, Broadcast crew (extras/crew_menu.py); nobody has to type anything
(rule 0.19). Every line of the broadcast says the setting: <announcer>, <analyst> (and <commentator>, its older name in remarks.txt),
<sideline> and <network>.

Each name is two settings: nx_<role> the name in use, nx_<role>_own the last name the player typed. Choosing the default keeps the typed
name, so Left and Right go back to it (BC.2 lost it: the owner's design, BC.3). A typed or stored name is cleaned as the analyst's always
was (extras/commentators.clean) and a retired name (Ghip, the 28 podcasters of D-106, kept only as digests) reads as the default, in every
role.

    ROLES                   the four, in the order of the menu
    DEFAULTS                the made-up names
    name_of(settings, role) the name in use; own_of(settings, role) the typed name ("" when none)
    names(settings)         the four names by role
    placeholders(names)     the line placeholders and their names (<commentator> too)
    choices(settings, role) the items of a role's list: the default, the typed name when it is another, the item that types one
    choose(settings, role, name, typed)  set the name in use (and remember a typed one); True when it changed
    legacy_analyst(value)   an old settings.txt's nx_commentator: (name, own)
"""
from __future__ import annotations

from . import commentators

ANNOUNCER, ANALYST, SIDELINE, NETWORK = "announcer", "analyst", "sideline", "network"
ROLES = (ANNOUNCER, ANALYST, SIDELINE, NETWORK)
DEFAULTS = {ANNOUNCER: "Walt Kessler", ANALYST: commentators.DEFAULT, SIDELINE: "Nora Banks", NETWORK: "the Gridiron Radio Network"}
PLACEHOLDER = {ANNOUNCER: "<announcer>", ANALYST: "<analyst>", SIDELINE: "<sideline>", NETWORK: "<network>"}
CREW_PLACEHOLDERS = ("<announcer>", "<analyst>", "<sideline>", "<network>", "<commentator>")


def setting(role: str) -> str:
    return "nx_" + role


def own_setting(role: str) -> str:
    return "nx_" + role + "_own"


def clean(role: str, name) -> str:
    """A name made safe to speak and store; "" when it cannot be used or is a retired name (Ghip, the retired podcasters)."""
    text = commentators.clean(name)
    return "" if not text or commentators.is_retired(text) else text


def name_of_text(role: str, name) -> str:
    return clean(role, name) or DEFAULTS[role]


def name_of(settings, role: str) -> str:
    return name_of_text(role, getattr(settings, setting(role), DEFAULTS[role]))


def own_of_text(role: str, name) -> str:
    """A stored typed name: the cleaned name, "" when it is empty, unusable, retired or the default."""
    text = clean(role, name)
    return "" if text == DEFAULTS[role] else text


def own_of(settings, role: str) -> str:
    """The last name the player typed for the role, "" when none (or when it is the default)."""
    return own_of_text(role, getattr(settings, own_setting(role), ""))


def names(settings) -> dict[str, str]:
    return {role: name_of(settings, role) for role in ROLES}


def placeholders(crew_names: dict[str, str]) -> dict[str, str]:
    values = {PLACEHOLDER[role]: crew_names.get(role, DEFAULTS[role]) for role in ROLES}
    values["<commentator>"] = values["<analyst>"]            # the analyst's name in the lines of RS.1 (SZ.1's placeholder)
    return values


def choices(settings, role: str) -> list[tuple[str, str]]:
    """(kind, name): kind "default", "own" or "type"."""
    items = [("default", DEFAULTS[role])]
    own = own_of(settings, role)
    if own:
        items.append(("own", own))
    items.append(("type", ""))
    return items


def choose(settings, role: str, name: str, typed: bool = False) -> bool:
    """Set the name in use; a typed name is also remembered. True when the name in use changed."""
    name = name_of_text(role, name)
    if typed and name != DEFAULTS[role]:
        setattr(settings, own_setting(role), name)
    before = name_of(settings, role)
    setattr(settings, setting(role), name)
    return name != before


def step(settings, role: str, direction: int) -> bool:
    """Left and Right: the next or the previous of the default and the typed name, going around. True when the name changed."""
    names_ = [name for kind, name in choices(settings, role) if kind != "type"]
    current = name_of(settings, role)
    index = names_.index(current) if current in names_ else 0
    return choose(settings, role, names_[(index + (1 if direction >= 0 else -1)) % len(names_)])


def legacy_analyst(value: str) -> tuple[str, str]:
    """An old settings.txt's nx_commentator (SZ.1 to BC.2): the analyst's name, and the typed name to remember ("" for the default,
    Ghip and the retired podcasters' names)."""
    name = name_of_text(ANALYST, value)
    return name, ("" if name == DEFAULTS[ANALYST] else name)
