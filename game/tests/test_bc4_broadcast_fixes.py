"""BC.4: what the listening test of the broadcast found, fixed (nfl4 only, rule 0.13; D-191). This is inspired by Jim Kitchen.

The listening test (work/bc4_1027/listen_broadcast.py: whole games in both modes, every line in order) found:
- Every game of one program run opened with the same sign-on, crew line, reporter's note and analyst's line: the broadcast's (and the
  stadium's) own generator was seeded from the program's seed only, which the program makes once per run. Now the seed and the draws the
  game's generator has made so far (game/rnd.side_seed): new lines every game, and the same seed and keys still give the same lines.
- The sign-on came after the coin toss; the real calls (spec/RADIO_NFL_STYLE.md section 3) sign on, introduce the crew and the reporter's
  note, and THEN toss the coin. Now the moment "sign_on" before the opening toss (H23; the engine's Classic answers it with nothing).
- The sign-off came before the final statistics (sixty lines of numbers after "so long, everybody"). Now the moment "sign_off" after them.
- Walt's hand-off "walk us through that play" came before the analyst's line at the end of a quarter or of the game. Now no hand-off
  before a line that is not about a play (broadcast.NO_ASK).
- A line that begins with the network's name began with a small letter ("the Gridiron Radio Network coverage continues after this").
"""
import random
import re
from pathlib import Path

import pytest

from nflrig import QUARTERBACKS, RecordingRules, SimEngine
from pagrig import make_rig, play
from test_pag_games import lively_policy
from nfl4.extras import broadcast as BC
from nfl4.extras import nx_texts as X
from nfl4.extras import remarks as RM
from nfl4.extras.classic_radio import ClassicRadioRules
from nfl4.extras.stadium import SEED_MIX as STADIUM_MIX
from nfl4.game.rnd import GameRandom, side_seed
from nfl4.game.rules import CLASSIC

SEED, PLAYER_SEED = 2034, 3034                  # the golden transcript's game
RUN_SEED = 0x1234_ABCD_5678_9EF0                # a seed as the program's GameRandom makes one, once per run
OPENING = ("SGN", "CRW", "SON", "CKO")
PATTERNS = [(pool, re.compile(re.sub(r"<[a-z ]+>", ".+", re.escape(X.TEXTS[r.id].strip()))))
            for pool in RM.BROADCAST_POOLS for r in RM.DEFAULT_POOLS.lines(pool)]


def pool_of(text: str):
    for pool, pattern in PATTERNS:
        if pattern.fullmatch(text.strip()):
            return pool
    return None


def nfl_game(tmp_path, seed=31, rig=None, run_seed=None):
    """One whole N. F. L. rules game with every extra and the crew, on the fast clock; a second call with the same rig is the next game of
    the same program run. Returns the rig and what this game said."""
    if rig is None:
        rig = make_rig(tmp_path, rng=random.Random(seed), fast=True, vtrnt=2, gtp=1)
        if run_seed is not None:
            rig.rnd.seed = run_seed                 # the program's GameRandom has a seed of its own; a test's source has none
    start = len(rig.said)
    rules = RecordingRules(penalties_on=True, onside_on=True, qb_on=True, challenges_on=True, playbooks_on=True, broadcast_on=True)
    engine = SimEngine(rig.game, rules, quarterback_names=lambda state: QUARTERBACKS)
    rig.game.play_engine = engine
    try:
        engine.run()
    finally:
        rig.game.play_engine = None
    return rig, rig.said[start:]


def opening(said):
    return [text.strip() for text, _r, _s in said if pool_of(text) in OPENING]


@pytest.fixture(scope="module")
def two_games(tmp_path_factory):
    rig, first = nfl_game(tmp_path_factory.mktemp("run"), run_seed=RUN_SEED)
    _rig, second = nfl_game(None, rig=rig)
    return first, second


@pytest.fixture(scope="module")
def classic_radio(tmp_path_factory):
    rig = make_rig(tmp_path_factory.mktemp("classic"), rng=random.Random(SEED), vtrnt=2)
    rig.keys.policy = lively_policy(rig, PLAYER_SEED)
    rig.rnd.trace = []
    result = play(rig, rules=ClassicRadioRules(broadcast_on=True))
    return rig, result


# ----- the seed of the side generators -----

def test_a_tests_source_keeps_the_fixed_seed_of_before():
    given = GameRandom(random.Random(5))
    assert given.seed is None
    assert side_seed(given, BC.SEED_MIX) == 0x5EED ^ BC.SEED_MIX
    assert side_seed(None, STADIUM_MIX) == 0x5EED ^ STADIUM_MIX


def test_the_programs_seed_and_the_games_draws_make_the_seed():
    rnd = GameRandom()                               # the program's: a seed of its own
    first = side_seed(rnd, BC.SEED_MIX)
    rnd.random()
    second = side_seed(rnd, BC.SEED_MIX)
    assert first != second                           # the next game of the run (the game's generator has drawn since)
    again = GameRandom(random.Random(rnd.seed))
    again.seed = rnd.seed
    again.random()
    assert side_seed(again, BC.SEED_MIX) == second   # the same seed and the same draws: the same broadcast (a session replays)
    assert side_seed(rnd, BC.SEED_MIX) != side_seed(rnd, STADIUM_MIX)


def test_two_games_of_one_run_open_with_lines_of_their_own(two_games):
    first, second = two_games
    o1, o2 = opening(first), opening(second)
    assert len(o1) == len(o2) == 4
    assert o1 != o2


# ----- the order of the broadcast -----

def _order(said):
    texts = [text.strip() for text, _r, _s in said]
    pools = [pool_of(text) for text, _r, _s in said]
    return texts, pools


def test_the_sign_on_comes_before_the_coin_toss_in_both_modes(two_games, classic_radio):
    rig, _result = classic_radio
    for said in (two_games[0], two_games[1], rig.said):
        texts, pools = _order(said)
        toss = next(i for i, t in enumerate(texts) if "here is the coin toss" in t)
        assert pools.index("SGN") < pools.index("CRW") < pools.index("SON") < pools.index("CKO") < toss
        assert pools.count("SGN") == 1


def test_the_sign_off_is_the_crews_last_line_after_the_final_statistics(two_games, classic_radio):
    rig, _result = classic_radio
    for said in (two_games[0], two_games[1], rig.said):
        texts, pools = _order(said)
        crew_at = [i for i, p in enumerate(pools) if p]
        stats = max(i for i, t in enumerate(texts) if t.startswith("Stats After Quarter number"))
        final = max(i for i, t in enumerate(texts) if "Final score" in t)
        assert pools[crew_at[-1]] == "SGO" and pools.count("SGO") == 1
        assert crew_at[-1] > stats > final


def test_no_hand_off_before_a_line_that_is_not_about_a_play(two_games, classic_radio):
    rig, _result = classic_radio
    for said in (two_games[0], two_games[1], rig.said):
        _texts, pools = _order(said)
        crew = [p for p in pools if p]
        for a, b in zip(crew, crew[1:]):
            assert not (a == "ASK" and b in BC.NO_ASK), (a, b)


def test_every_crew_line_begins_with_a_capital_letter(two_games, classic_radio):
    rig, _result = classic_radio
    for said in (two_games[0], two_games[1], rig.said):
        for text, _r, _s in said:
            if pool_of(text):
                assert not text.strip()[:1].islower(), text


def test_a_line_that_begins_with_the_network_begins_with_a_capital_letter():
    said = []
    BC._capital_first(said.append)(" the Gridiron Radio Network coverage continues after this. ")
    assert said == [" The Gridiron Radio Network coverage continues after this. "]
    said = []
    speak = BC._capital_first(said.append)
    speak("   ")
    speak(" the rest")
    speak(" and more")                                # only the first spoken piece of a line
    assert said == ["   ", " The rest", " and more"]


# ----- the game itself does not move -----

def test_classic_with_the_crew_still_makes_exactly_the_engines_classic_draws(classic_radio, tmp_path):
    rig, result = classic_radio
    bare = make_rig(tmp_path, rng=random.Random(SEED), vtrnt=2)
    bare.keys.policy = lively_policy(bare, PLAYER_SEED)
    bare.rnd.trace = []
    bare_result = play(bare, rules=CLASSIC)
    assert rig.rnd.trace == bare.rnd.trace and result.scores == bare_result.scores == (28, 39)
    plain = [(t, r) for t, r, _s in rig.said if pool_of(t) is None and t != X.text("NXB-B01")]
    assert plain == [(t, r) for t, r, _s in bare.said]
