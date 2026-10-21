"""The catalog of every real NFL play and every Madden NFL concept (nfl4 only, rule 0.13; NX-P2, NX-R6; design
`spec/NFL_PLAYS_DESIGN.md` sections 2 and 3; SX.10b). This is inspired by Jim Kitchen."""
import re

import pytest

from nfl4.extras import nx_texts as X
from nfl4.extras import playbook_data as SX7
from nfl4.extras.plays import catalog as C
from nfl4.extras.plays import model_data as M

TAGS = (C.SRC_OFFICIAL, C.SRC_SECONDARY, C.UNVERIFIED)
OFFENSE_KINDS = {"run", "draw", "qb_run", "sneak", "option", "rpo", "pass", "screen", "play_action", "boot", "max_protect",
                 "trick_run", "trick_pass", "hail_mary", "laterals", "kneel", "spike"}
GAPS = {"middle", "guard", "tackle", "end"}

# every play, formation, coverage, front, pressure and kick that NFL_PLAYS_RESEARCH sections 2 to 6 name (the research's
# section 9 "missing" lists and the SX.7 catalog), in lower case: each is a catalog name, a MERGED name or a LEFT_OUT name
RESEARCH_NAMES = (
    "inside zone", "outside zone", "stretch", "mid zone", "split zone", "wham", "belly", "duo", "power", "counter",
    "counter trey", "trap", "iso", "lead", "dive", "fullback dive", "fullback trap", "draw", "delayed draw", "off tackle",
    "cutback", "toss", "quick toss", "crack toss", "pin and pull", "jet sweep", "end around", "reverse", "fake reverse",
    "quarterback sneak", "sneak push", "quarterback power", "quarterback counter", "quarterback draw", "quarterback zone",
    "quarterback crack sweep", "read option", "zone read", "speed option", "triple option", "midline option", "inside veer",
    "inverted veer", "power read", "receiver pitch option", "run pass option", "bubble", "glance", "quick flat", "stick",
    "alert", "slant flat", "snag", "spacing", "hitch", "quick out", "speed out", "curl and flat", "fade", "back shoulder fade",
    "slants", "double slants", "dig", "levels", "mesh", "shallow cross", "drag", "drive", "y cross", "flood", "sail", "smash",
    "curl", "comeback", "out route", "deep out", "choice route", "dagger", "bench", "whip", "return route", "four verticals",
    "post", "corner", "post corner", "go route", "seam", "deep cross", "double posts", "post wheel", "mills", "yankee",
    "divide", "scissors", "sluggo", "stutter go", "out and up", "zig", "hail mary", "angle", "wheel", "swing", "flat route",
    "texas", "check down", "leak", "running back screen", "slip screen", "receiver screen", "tunnel", "jailbreak",
    "middle screen", "tight end screen", "fullback screen", "double screen", "shovel pass", "play action screen",
    "play action shot", "play action cross", "play action flood", "play action wheel", "bootleg", "naked bootleg", "waggle",
    "rollout", "sprint out", "max protect", "flea flicker", "halfback pass", "double pass", "throwback to the quarterback",
    "hook and lateral", "statue of liberty", "fumblerooski", "fake spike", "fake kneel", "wildcat", "jet touch pass",
    "fake sneak swing", "laterals at the end", "kneel", "spike", "wishbone", "flexbone", "wing t", "single wing",
    "full house", "split t",
    # defense
    "four three over", "four three under", "three four odd", "okie", "tite", "mint", "46", "bear front", "five two", "six one",
    "goal line six two", "goal line five three", "four four", "wide nine", "big nickel", "dollar", "quarter defense",
    "prevent", "cover zero", "cover one robber", "cover two zone", "tampa two", "two man", "cover three sky",
    "cover three cloud", "cover three buzz", "cover three match", "cover four quarters", "match quarters", "cover six",
    "palms", "cover nine", "man press", "off man", "bracket", "double coverage", "man three deep", "safety rotation",
    "two deep disguise", "drop eight", "zone blitz", "fire zone", "simulated pressure", "creeper", "overload", "a gap blitz",
    "double a gap", "edge blitz", "nickel blitz", "dime blitz", "safety blitz", "corner blitz", "defensive back fire",
    "delayed blitz", "cross blitz", "free fire", "twist", "loop", "pinch", "spy", "contain", "quarterback contain",
    "run blitz", "two gap", "one gap", "slant line", "angle line", "spill", "box the run", "pitch assignment",
    "scrape exchange", "hail mary defense", "two point defense", "two minute defense", "cover one contain",
    "cover two hard flat", "cover two invert", "cover four drop", "cover three seam", "cover four press", "cover two match",
    # special teams
    "deep kick", "short kick", "squib", "onside", "sky kick", "punt", "pin punt", "coffin corner", "pooch punt", "rugby punt",
    "tight punt", "quick kick", "fake punt run", "fake punt pass", "field goal", "fake field goal run",
    "fake field goal pass", "extra point", "drop kick", "fair catch kick", "swinging gate", "punt return", "fair catch",
    "punt block", "punt safe", "field goal block", "field goal safe", "safety punt",
)
# EA's own names that the game never uses (MADDEN_PLAYBOOK_RESEARCH 3 List B, NFL_PLAYS_RESEARCH 6.4)
EA_NAMES = ("tush push", "goal line sneak", "philly special", "hoss", "boomerang", "smart zone", "match check", "gap integrity",
            "id mike", "coachspeak", "coach mode", "auto flip", "sneak meter", "hulk", "gadget", "sugar", "predator", "grizzly",
            "cub", "plaster", "x-factor", "superstar", "persona", "roll coverage", "look for work", "smoke")


def test_the_ids_are_permanent_and_contiguous():
    assert [c.id for c in C.OFFENSE if int(c.id[1:]) <= 52] and len(C.BY_ID) == len(C.CATALOG)
    offense = sorted(int(c.id[1:]) for c in C.OFFENSE)
    defense = sorted(int(c.id[1:]) for c in C.DEFENSE)
    assert offense == list(range(1, len(offense) + 1))
    assert defense == list(range(1, len(defense) + 1))
    assert len({c.id for c in C.KICKS}) == len(C.KICKS)


def test_the_sx7_plays_keep_their_ids_and_names():
    for play in SX7.CATALOG:
        concept = C.BY_ID[play.id]
        assert concept.text_id == play.name_id
        assert concept.name == X.text(play.name_id)


@pytest.mark.parametrize("concept", C.CATALOG, ids=lambda c: c.id)
def test_every_name_is_short_spoken_words_and_is_the_text_tables_row(concept):
    assert 1 <= len(concept.name) <= 30 and len(concept.name.split()) <= 6
    assert "," not in concept.name and ";" not in concept.name and not re.search(r"\d", concept.name)
    assert X.text(concept.text_id) == concept.name
    assert concept.tag in TAGS
    assert concept.strong and concept.weak, "every play has a stated strength and weakness (design 4.8)"


def test_names_are_unique_on_each_side():
    for side in "ODK":
        names = [c.name.lower() for c in C.CATALOG if c.side == side]
        assert len(names) == len(set(names))


def test_the_lists_are_at_most_ten_and_each_family_has_its_lists():
    for group in C.GROUPS:
        members = [c for c in C.CATALOG if c.group == group.key or group.key in c.also]
        assert 1 <= len(members) <= C.MAX_PER_GROUP, group.key
        assert X.text(C.group_text_id(group)) == group.name
    for side, families in (("O", range(1, 6)), ("D", range(1, 7))):
        for family in families:
            orders = sorted(g.order for g in C.GROUPS if g.side == side and g.family == family)
            assert orders and orders == list(range(1, len(orders) + 1)), (side, family)


def test_every_offense_concept_has_a_known_model_and_valid_inputs():
    for c in C.OFFENSE:
        assert c.kind in OFFENSE_KINDS, c.id
        if c.kind in ("run", "draw", "trick_run"):
            assert c.params[0] in GAPS and -100 <= c.params[1] <= 100
        if c.kind in ("pass", "screen", "play_action", "boot", "max_protect", "trick_pass"):
            routes, sack, comp, deeper = c.params
            assert routes and all(r in M.ROUTES and w > 0 for r, w in routes), c.id
            assert 50 <= sack <= 150 and -1000 <= comp <= 1000 and deeper in (0, 1)
        if c.kind in ("qb_run", "sneak"):
            assert c.params[0] in ("designed", "sneak")
        if c.kind == "option":
            give, keep, pitch = c.params
            assert give in GAPS | {""} and keep == "designed" and pitch in ("", "end")
        if c.kind == "rpo":
            assert c.params[0] in GAPS and all(r in M.ROUTES for r, _w in c.params[1])


def test_every_defense_call_is_a_valid_call():
    for c in C.DEFENSE:
        call = c.params
        assert c.kind == "call"
        assert call.coverage in M.COVERAGE_BANDS or call.coverage == C.PREVENT
        assert 5 <= call.box <= 8 and 2 <= call.rushers <= 6 and 3 <= call.backs <= 7, c.id
        assert not (call.rushers >= 6 and not call.blitz and call.backs >= 5), "six rushers from a nickel need a blitzer"


def test_the_research_names_are_all_in_the_game_merged_or_left_out_with_a_reason():
    names = [c.name.lower() for c in C.CATALOG]
    missing = []
    for want in RESEARCH_NAMES:
        if any(want in n for n in names) or want in C.MERGED or any(want in key for key in C.LEFT_OUT):
            continue
        missing.append(want)
    assert missing == []
    assert all(target in C.BY_ID for target in C.MERGED.values())
    assert all(reason.strip() for reason in C.LEFT_OUT.values())


def test_no_ea_name_is_a_play_name_or_a_list_name():
    words = [c.name.lower() for c in C.CATALOG] + [g.name.lower() for g in C.GROUPS]
    for ea in EA_NAMES:
        assert not any(re.search(r"\b%s\b" % re.escape(ea), w) for w in words), ea


def test_the_trick_and_old_plays_are_marked_rare_and_the_clock_plays_marked_clock():
    for key in ("og16", "og19"):
        assert all("rare" in c.situations for c in C.CATALOG if c.group == key)
    assert all("clock" in c.situations for c in C.CATALOG if c.group == "og18")


def test_the_settings_are_values_not_plays():
    assert C.SETTINGS["formation"][0] == "book" and C.SETTINGS["tempo"][0] == "normal"
    assert "match" == C.SETTINGS["defense_personnel"][0]
