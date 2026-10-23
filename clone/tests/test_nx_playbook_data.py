"""The playbooks' data: the catalog, the seven styles, the tilts, the bounds and the 32 teams' styles (nfl4 only, rule 0.13;
NFL_EXTRAS_DESIGN 10, MADDEN_PLAYBOOK_RESEARCH 4 and 5, PX SX.7). This is inspired by Jim Kitchen.

Every expectation is worked out from the design or the research next to it, never from a run of the game (B-X38).
"""
import pytest

from nfl4.extras import nx_texts as X
from nfl4.extras import playbook_data as D
from nfl4.extras import playbooks as PB
from nfl4.game import league
from playbook_ev import dominating_play, offense_vector

TABLE = PB.DEFAULT_TABLE
# MADDEN_PLAYBOOK_RESEARCH 5, team by team in the order of league.DEFAULT_TEAM_NAMES: the style named for the team, and where EA
# names a different defensive identity the defense (the research's alternative for the Steelers: offense Pro Style)
RESEARCH = {"Bengals": ("air", "pro"), "Browns": ("pressure", "pressure"), "Ravens": ("option", "option"),
            "Steelers": ("pro", "pressure"), "Bills": ("option", "option"), "Dolphins": ("option", "option"),
            "Jets": ("pro", "pro"), "Patriots": ("pro", "pro"), "Broncos": ("pro", "pro"), "Chargers": ("zone", "zone"),
            "Chiefs": ("air", "pro"), "Raiders": ("zone", "zone"), "Colts": ("pro", "pro"), "Jaguars": ("west", "west"),
            "Texans": ("west", "west"), "Titans": ("power", "power"), "Bears": ("power", "power"),
            "Lions": ("power", "power"), "Packers": ("west", "west"), "Vikings": ("pressure", "pressure"),
            "Cowboys": ("air", "air"), "Eagles": ("option", "option"), "Giants": ("power", "power"),
            "Commanders": ("air", "air"), "Cardinals": ("option", "option"), "Forty Niners": ("zone", "zone"),
            "Rams": ("air", "air"), "Sea hawks": ("zone", "zone"), "Buccaneers": ("air", "air"),
            "Falcons": ("power", "power"), "Panthers": ("west", "west"), "Saints": ("west", "west")}


def test_the_catalog_has_52_offense_plays_and_30_defense_plays_with_permanent_ids():
    assert [p.id for p in D.CATALOG if p.side == "O"] == ["O%03d" % n for n in range(1, 53)]
    assert [p.id for p in D.CATALOG if p.side == "D"] == ["D%03d" % n for n in range(1, 31)]
    assert len(D.PLAYS) == 82 and D.OFFENSE_IDS[0] == "O001" and D.DEFENSE_IDS[-1] == "D030"


def test_every_play_maps_to_a_family_of_the_original_and_has_a_group():
    for play in D.CATALOG:
        if play.side == "O":
            assert play.family in D.OFFENSE_FAMILIES and play.group in D.OFFENSE_GROUPS, play.id
            expected = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 8: 7, 9: 7, 10: 7}[play.family]
            assert play.group == expected or (play.group == 6 and play.family in (4, 5)), play.id   # play action: 4 or 5
        else:
            assert play.family in D.DEFENSE_FAMILIES and play.group == play.family, play.id


def test_every_play_has_a_spoken_name_of_at_most_six_words_and_thirty_characters():
    for play in D.CATALOG:
        name = X.text(play.name_id)
        assert 1 <= len(name) <= 30 and len(name.split()) <= 6 and "," not in name and ";" not in name, (play.id, name)
        assert X.KINDS[play.name_id] == "menu" and X.SPEAKERS[play.name_id] == "say5"
    assert len({X.text(p.name_id).casefold() for p in D.CATALOG if p.side == "O"}) == 52
    assert len({X.text(p.name_id).casefold() for p in D.CATALOG if p.side == "D"}) == 30


def test_names_come_from_the_plain_football_words_and_no_ea_name_is_used():
    banned = ("madden", "x-factor", "ultimate", "superstar", "tush", "coach dna", "persona", "shotgun classic", "multiple d")
    for play in D.CATALOG:
        assert not any(word in X.text(play.name_id).casefold() for word in banned), play.id


def test_a_play_has_a_strength_and_a_weakness_against_the_defense_calls():
    """Design 10.3 and N5.2: each play tilts the original's row up against some calls and down against others (expected yards)."""
    for play in D.CATALOG:
        if play.side != "O" or play.id == "O038":
            continue
        base = [0.0] * 6
        vector = offense_vector(None, play)
        from playbook_ev import base_vector
        delta = [a - b for a, b in zip(vector, base_vector(play.family))]
        assert max(delta) > 0.1 and min(delta) < -0.1, (play.id, delta)


def test_every_rule_of_a_play_and_every_tilt_is_within_the_bounds():
    for play in D.CATALOG:
        for rule in play.rules:
            assert all(abs(v) <= b for v, b in zip(rule.mod, D.BOUNDS)), (play.id, rule)
            assert rule.vs and all(call in (D.DEFENSE_FAMILIES if play.side == "O" else D.OFFENSE_FAMILIES) for call in rule.vs)
    for style in D.STYLES:
        for tilt in style.off_bonus + style.off_penalty + style.def_bonus + style.def_penalty:
            assert all(abs(v) <= b for v, b in zip(tilt.mod, D.BOUNDS)), (style.key, tilt)


def test_the_bounds_are_the_designs_two_yards_five_points_and_five_on_the_fumble_denominator():
    assert D.BOUNDS == D.Mod(2, 2, 5, 5, 5)
    assert PB.clamp(D.Mod(9, -9, 9, -9, 9)) == D.Mod(2, -2, 5, -5, 5)


def test_the_seven_styles_are_the_researchs_and_pro_style_has_no_tilt():
    assert [s.key for s in D.STYLES] == ["pro", "west", "air", "power", "zone", "option", "pressure"]
    assert [X.text(s.name_id) for s in D.STYLES] == ["Pro Style", "West Coast", "Air Raid", "Power Run", "Zone Run", "Option",
                                                     "Pressure"]
    assert [s.code for s in D.STYLES] == ["PRO", "WES", "AIR", "POW", "ZON", "OPT", "PRE"]
    pro = D.STYLES[0]
    assert pro.off_bonus == pro.off_penalty == pro.def_bonus == pro.def_penalty == () and pro.qb_percent == 100
    assert X.text("NXM-27") == "Classic" and D.CLASSIC_KEY == "classic"


@pytest.mark.parametrize("style", D.STYLES, ids=lambda s: s.key)
def test_a_style_lists_plays_of_its_side_in_every_family_within_the_size_of_a_menu(style):
    offense = [D.PLAYS[i] for i, _ in style.offense]
    defense = [D.PLAYS[i] for i, _ in style.defense]
    assert all(p.side == "O" for p in offense) and all(p.side == "D" for p in defense)
    assert len({p.id for p in offense}) == len(offense) and len({p.id for p in defense}) == len(defense)
    assert all(w > 0 for _i, w in style.offense + style.defense)
    assert 24 <= len(offense) <= 40 and 14 <= len(defense) <= 24, (len(offense), len(defense))
    for family in (1, 2, 3, 4, 5):
        assert any(p.family == family for p in offense), family
    for call in D.DEFENSE_FAMILIES:
        assert 2 <= sum(p.family == call for p in defense) <= 5, call              # the research: 2 to 5 plays per call
    for group in D.OFFENSE_GROUPS:
        assert sum(p.group == group for p in offense) <= D.MAX_PER_GROUP, group     # + Back, C, T and S: at most 12 items
    assert any(p.family in D.QB_FAMILIES for p in offense)                          # the keeper family (Option's base)


@pytest.mark.parametrize("style", D.STYLES, ids=lambda s: s.key)
def test_a_style_has_at_most_three_bonus_and_three_penalty_entries_of_equal_total_size(style):
    """Design 10.3 and the research's size rule, each side of the ball."""
    for bonus, penalty in ((style.off_bonus, style.off_penalty), (style.def_bonus, style.def_penalty)):
        assert len(bonus) <= 3 and len(penalty) <= 3
        assert sum(t.mod.size() for t in bonus) == sum(t.mod.size() for t in penalty), (style.key, bonus, penalty)


@pytest.mark.parametrize("style", D.STYLES, ids=lambda s: s.key)
def test_a_bonus_helps_and_a_penalty_hurts_the_side_it_belongs_to(style):
    """Offense: more yards, completions, fewer sacks and fumbles is good; the defense's sign is the other way."""
    def good_for_offense(mod):
        return mod.ylo >= 0 and mod.yhi >= 0 and mod.sack <= 0 and mod.comp >= 0 and mod.fum >= 0

    def bad_for_offense(mod):
        return mod.ylo <= 0 and mod.yhi <= 0 and mod.sack >= 0 and mod.comp <= 0 and mod.fum <= 0

    assert all(good_for_offense(t.mod) for t in style.off_bonus) and all(bad_for_offense(t.mod) for t in style.off_penalty)
    assert all(bad_for_offense(t.mod) for t in style.def_bonus) and all(good_for_offense(t.mod) for t in style.def_penalty)


@pytest.mark.parametrize("style", D.STYLES, ids=lambda s: s.key)
def test_no_play_is_better_than_every_other_play_of_its_family_against_every_call(style):
    """Design 10.3: no play of a style beats the rest of its family, the original's play among them, against all six calls (the
    original's play may beat all of a style's: that family is simply worse in the style)."""
    book = TABLE.styles[style.key]
    for family in (1, 2, 3, 4, 5, 8, 9, 10):
        plays = [p for p, _w in TABLE.usable(style.key, "O") if p.family == family]
        from playbook_ev import base_vector
        vectors = {p.id: offense_vector(book, p) for p in plays}
        vectors["classic"] = base_vector(family)
        assert dominating_play(vectors) in (None, "classic"), (style.key, family, dominating_play(vectors))


def test_the_dominance_check_finds_a_play_that_is_better_everywhere():
    assert dominating_play({"a": [1, 2, 3], "b": [1, 1, 3], "c": [0, 2, 2]}) == "a"
    assert dominating_play({"a": [1, 2, 3], "b": [3, 2, 1]}) is None
    assert dominating_play({"a": [1, 2, 3], "b": [1, 2, 3]}) is None


def test_the_32_teams_have_the_styles_of_the_research_and_the_counts_of_its_totals():
    assert len(D.TEAM_STYLES) == 32 == len(league.DEFAULT_TEAM_NAMES)
    for name, expected in zip(league.DEFAULT_TEAM_NAMES, D.TEAM_STYLES):
        assert RESEARCH[name] == expected, name
    offense = [o for o, _d in D.TEAM_STYLES]
    # research totals (Pro Style 4, West Coast 5, Air Raid 6, Power Run 5, Zone Run 4, Option 5, Pressure 3) with the Steelers'
    # offense moved from Pressure to Pro Style, the research's alternative: its defense is the Pressure
    assert {k: offense.count(k) for k in ("pro", "west", "air", "power", "zone", "option", "pressure")} == {
        "pro": 5, "west": 5, "air": 6, "power": 5, "zone": 4, "option": 5, "pressure": 2}
    assert [d for _o, d in D.TEAM_STYLES].count("pressure") == 3
    assert all(k in D.BOOK_KEYS for pair in D.TEAM_STYLES for k in pair)


def test_the_playbook_choices_are_classic_first_then_the_team_then_the_seven_styles():
    assert D.PLAYBOOK_CHOICES == ("classic", "team", "pro", "west", "air", "power", "zone", "option", "pressure")
    assert D.BOOK_KEYS == ("classic", "pro", "west", "air", "power", "zone", "option", "pressure")


def test_the_family_masses_of_a_style_are_its_designed_mix_and_classic_is_the_originals():
    for style in D.STYLES:
        mix = {f: sum(w for i, w in style.offense if D.PLAYS[i].family == f) for f in (1, 2, 3, 4, 5)}
        assert all(mix[f] >= 1 for f in mix)
        total = sum(mix.values())
        for family, percent in D.MASS[style.code].items():
            assert abs(100 * mix[family] / total - percent) < 3, (style.key, family)
    assert D.MASS["PRO"] == {1: 22, 2: 22, 3: 22, 4: 22, 5: 11}        # GAME_SPEC 5.7: 2/9, 2/9, 2/9, 2/9, 1/9


# ----- what the review of SX.7 found -----

def test_no_play_is_at_least_as_good_as_another_of_its_family_against_every_call_even_in_pairs():
    """Design 10.3 says no play beats the best of its family everywhere; the stronger rule kept here: no pair of plays of a
    family where one is as good as the other on every call (a play nobody would ever choose, or a twin)."""
    from playbook_ev import defense_vector
    for side, vector, families in (("O", lambda p: offense_vector(None, p), (1, 2, 3, 4, 5, 8, 9, 10)),
                                   ("D", lambda p: defense_vector(None, p), (1, 2, 3, 4, 5, 6))):
        for family in families:
            plays = [p for p in D.CATALOG if p.side == side and p.family == family]
            vectors = {p.id: vector(p) for p in plays}
            for a in plays:
                for b in plays:
                    if a.id != b.id:
                        assert not all(x >= y - 1e-9 for x, y in zip(vectors[a.id], vectors[b.id])), (a.id, "is as good as", b.id)


def test_a_rule_never_changes_a_number_its_row_does_not_have():
    """A run's row has yards and a fumble chance, no sack and no catch percent; the quarterback's runs too."""
    from playbook_ev import RUN_FAMILIES
    for play in D.CATALOG:
        for rule in play.rules:
            on_runs = [call for call in rule.vs if (call if play.side == "D" else play.family) in RUN_FAMILIES]
            if play.side == "O" and play.family in RUN_FAMILIES:
                assert not (rule.mod.sack or rule.mod.comp), (play.id, rule)
            if play.side == "D":
                # a defense rule that names only run families cannot carry a sack or a catch change
                assert not (on_runs == list(rule.vs) and (rule.mod.sack or rule.mod.comp)), (play.id, rule)


def test_every_play_is_centered_its_own_tilt_moves_expected_yards_by_a_quarter_yard_at_most():
    from playbook_ev import mean_effect
    for play in D.CATALOG:
        assert abs(mean_effect(play)) <= 0.26, (play.id, mean_effect(play))


@pytest.mark.parametrize("style", D.STYLES, ids=lambda s: s.key)
def test_a_group_of_a_style_has_two_to_six_plays_as_the_research_sizes_it(style):
    groups = {}
    for play_id, _w in style.offense:
        groups[D.PLAYS[play_id].group] = groups.get(D.PLAYS[play_id].group, 0) + 1
    assert all(2 <= n <= 6 for n in groups.values()) and set(groups) == set(D.OFFENSE_GROUPS), groups
