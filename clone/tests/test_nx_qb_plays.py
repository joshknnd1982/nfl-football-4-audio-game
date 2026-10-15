"""The quarterback's runs in the play engine: the sneak, keeper and draw from the menu, the scramble in place of a sack or an
incompletion, the slide, the fumble, touchdowns and safeties, out of bounds, the computer's choices and the defense's matching
(nfl4 only, rule 0.13; NFL_EXTRAS_DESIGN 7 and 15; PX SX.5). This is inspired by Jim Kitchen.

Every draw is planned on a strict scripted source (Draws, tests/pagrig.py) in the order of design 15 and every expected number
and text is worked out from the rule next to it, never from a run of the game (B-X38); the speech is the fake SAPI's list of
(text, speaker, rate step). Penalties are off here (tests/test_nx_qb_penalties.py has them).
"""
import pytest

from nfl4.extras import nx_texts as X
from nfl4.extras import qb_runs as QB
from nfl4.extras import tuning as T
from nfl4.extras.clock import live_time
from nfl4.extras.nfl_rules import NflRules
from nfl4.game import outcome as O
from nfl4.game import phrases as P
from nfl4.game.playtables import DEFENSE_MATCH, QB_DRAW, QB_KEEPER, QB_SNEAK
from nfl4.speech.roles import ANNOUNCER
from nflrig import nfl_engine_rig
from pagrig import Draws, run_steps, sounds_played
from randsources import ScriptedRandom
from test_pag_scrimmage import first_dropback, quiet_snap_count, snap_draws

START = dict(wisoff=1, defense=2, half=2, yard_line=30, down=1, to_go=10, quarter=1)
# the keeper's direction is Int(Rnd * 4) + 4 of the original's seven (GAME_SPEC 5.9): below(4) = k gives these
DIRECTIONS = ("around the right side", "around the left side", "around the left end", "around the right end")


def texts(rig, start=0):
    return [t for t, _, _ in rig.said[start:]]


def rig_for(tmp_path, play, call, qb_on=True, extras=None, **state):
    """The Bengals (side 1) on offense with `play` against the Jets' defense call `call`; time outs and penalties off."""
    fields = dict(START)
    fields.update(state)
    rules = NflRules(timeouts_on=False, qb_on=qb_on)
    rig = nfl_engine_rig(tmp_path, answers=[13] * 3, rules=rules, extras=extras or {}, offense_play=play, defense_play=call,
                         **fields)
    rig.game.pause_log = []
    return rig


def after_play(d: Draws, oob=None, live=(4, 0), banter=1, runoff=0, ready_cut=None) -> Draws:
    """What follows the run's end: the out-of-bounds draw (only when its rate is above 0 and the runner did not slide),
    the live time L (`below(n)`: a run 4 to 7 is below(4), a scramble 5 to 9 below(5)), the banter draw 1 in 4 at the position
    (1: none), then R = 30 to 40 (below(11) + 30) and, when the run went out of bounds, the ready-signal cut below(4) + 2."""
    if oob is not None:
        d.below(100, oob)
    d.below(*live)
    d.rnd(4, banter)
    d.below(11, runoff)
    if ready_cut is not None:
        d.below(4, ready_cut)
    return d


def run_draws(kind, call, yards, line=1, direction=0, d1=1, d2=2, carrier=1, fumble=1, slide=None, oob=99,
              ready_cut=None, live=(4, 0)):
    """The draws of a designed run from the snap on: the snap count and phrase, the start sentence (keeper, draw: pool QB
    `rnd(5)`), the direction (keeper: `below(4)`), the fumble test `rnd(odds)`, the yards `below(most - fewest + 1)`, the slide
    when the gain is 8 or more (`rnd(2)`, 1 slides, then the cut `below(3)`), the out-of-bounds draw, L, the banter draw, R."""
    entry = QB.make_entry(kind, call)
    d = quiet_snap_count(Draws())
    snap_draws(d, carrier=carrier, d1=d1, d2=d2)
    if kind in ("keeper", "draw"):
        d.rnd(5, line)
    if kind == "keeper":
        d.below(4, direction)
    d.rnd(entry.fumble, fumble).below(entry.high - entry.low, yards - entry.low)
    slid = False
    if yards >= T.QB_SLIDE_MIN_YARDS:
        if slide is None:
            d.rnd(T.QB_SLIDE_ONE_IN, 2)
        else:
            d.rnd(T.QB_SLIDE_ONE_IN, 1).below(3, slide)
            slid = True
    rate = T.QB_OUT_OF_BOUNDS[kind]
    return after_play(d, oob=oob if rate and not slid else None, live=live, ready_cut=ready_cut)


def touchdown_end(d: Draws, ones: int, live=(4, 0)) -> Draws:
    """After the yards of a run that scores: " he is at the " with its rady, one rady for each of the ones 5 to 1 that the
    distance reaches, L at the end point, the celebration, and the pause before the extra point choice."""
    for _ in range(1 + ones):
        d.rady()
    d.below(*live)
    return d.celebration(8).rady()


# ----- a sneak, a keeper and a draw, spoken like a run of 5.9 -----

def test_a_sneak_speaks_its_sentences_and_counts_as_a_running_play_and_on_its_own_line(tmp_path):
    rig = rig_for(tmp_path, QB_SNEAK, 1, down=3, to_go=1)                           # Sneak against the Goal Line: 0 to 2 yards
    assert run_steps(rig, rig.engine.snap, run_draws("sneak", 1, 1)) == "next_play"
    start = texts(rig).index("Starr takes the snap")
    assert rig.said[start:start + 4] == [("Starr takes the snap", ANNOUNCER, 0),
                                         (" Starr pushes forward behind the center ", ANNOUNCER, 0),
                                         (" and there is a big pile up ", ANNOUNCER, 0),
                                         (" There is a gain of 1 yard on the play", ANNOUNCER, 0)]
    assert sounds_played(rig)[-1] == "foot4"                                        # PlayTackle(1)
    s, x = rig.engine.s, rig.engine.s.extras
    assert (s.yard_line, s.down, s.to_go) == (31, 1, 10)                            # 1 yard on third and 1: a first down
    assert (s.stats[1].running_plays, s.stats[1].running_yards, s.stats[1].first_downs) == (1, 1, 1)
    assert (x.qb_runs, x.qb_yards) == ([1, 0], [1, 0])
    assert [(o.kind, o.qb_run, o.yards, o.slid) for o in rig.engine.outcomes] == [(O.RUN, "sneak", 1, False)]
    assert s.qb_run == "" and not s.slid                                            # cleared with the record


def test_a_keeper_says_a_line_of_pool_qb_then_the_run_with_a_direction_and_the_tackle(tmp_path):
    rig = rig_for(tmp_path, QB_KEEPER, 5, down=2, to_go=7)                          # Keeper against the Short Pass call: 3 to 12
    assert run_steps(rig, rig.engine.snap, run_draws("keeper", 5, 6, line=2, direction=2, oob=50)) == "next_play"
    spoken = texts(rig)
    start = spoken.index("Starr takes the snap")
    assert spoken[start:start + 5] == ["Starr takes the snap", " Starr fakes the hand off and keeps it ",
                                       " Starr runs around the left end ", " and is tackled by ODef1 ",
                                       " There is a gain of 6 yards on the play"]
    assert sounds_played(rig)[-1] == "foot6"                                        # PlayTackle(3)
    s = rig.engine.s
    assert (s.yard_line, s.down, s.to_go) == (36, 3, 1)
    assert (s.extras.qb_runs, s.extras.qb_yards) == ([1, 0], [6, 0])


@pytest.mark.parametrize("k", [0, 1, 2, 3])
def test_the_keepers_direction_is_the_originals_four_to_seven(tmp_path, k):
    rig = rig_for(tmp_path, QB_KEEPER, 5)
    run_steps(rig, rig.engine.snap, run_draws("keeper", 5, 5, direction=k))
    assert " Starr runs %s " % DIRECTIONS[k] in texts(rig)


def test_a_draw_is_spoken_straight_up_the_middle_and_brought_down_by_the_first_defender(tmp_path):
    rig = rig_for(tmp_path, QB_DRAW, 2)                                             # Draw against the Short Run call: -2 to 3
    run_steps(rig, rig.engine.snap, run_draws("draw", 2, 0, line=5, d1=3, oob=99))  # QB05, no gain
    spoken = texts(rig)
    start = spoken.index("Starr takes the snap")
    assert spoken[start:start + 5] == ["Starr takes the snap", " Starr drops back, then takes off ",
                                       " Starr runs straight up the middle ", " and is brought down by ODef3 ", P.NO_GAIN]
    assert sounds_played(rig)[-1] == "foot6"


def test_the_pool_line_is_play_by_play_said_with_comments_off_and_kept_for_the_replay(tmp_path):
    rig = rig_for(tmp_path, QB_KEEPER, 5)                                           # nfl_engine_rig: comments off (F8)
    assert rig.game.comtog == 1
    run_steps(rig, rig.engine.snap, run_draws("keeper", 5, 5, line=1))
    assert " Starr keeps the ball " in texts(rig)                                   # said although F8 switched comments off
    assert " Starr keeps the ball " in rig.game.replay                              # say4: F2 replays it


def test_a_pool_with_every_line_switched_off_falls_back_to_the_default_lines(tmp_path):
    """The play-by-play always has its sentence (CUSTOMIZABLE_CONTENT 13 L13): the player's pool is empty, the defaults speak."""
    from nfl4.extras import remarks
    rig = rig_for(tmp_path, QB_KEEPER, 5)
    rig.game.remark_pools = remarks.RemarkPools({pool: () if pool == "QB" else lines
                                                 for pool, lines in remarks.DEFAULT_REMARKS.items()})
    assert rig.game.remark_pools.lines("QB") == ()
    run_steps(rig, rig.engine.snap, run_draws("keeper", 5, 5, line=4))
    spoken = texts(rig)
    assert spoken[spoken.index("Starr takes the snap") + 1] == " Starr rolls out and takes off "        # QB04


def test_a_commentary_pool_with_every_line_switched_off_stays_silent():
    from nfl4.extras import remarks
    assert remarks.PLAY_BY_PLAY_POOLS == {"QB"} and not remarks.PLAY_BY_PLAY_POOLS & remarks.COMMENTARY_POOLS


def test_pool_qb_never_repeats_one_of_the_last_three_lines(tmp_path):
    rig = rig_for(tmp_path, QB_KEEPER, 5)
    rig.engine.s.extras.recent = {"QB": ["QB01", "QB02", "QB03"]}
    d = quiet_snap_count(Draws())
    snap_draws(d)
    entry = QB.make_entry("keeper", 5)
    d.rnd(5, 2).rnd(5, 3).rnd(5, 5)                                                     # QB02 and QB03 are recent: redrawn; QB05
    d.below(4, 0).rnd(entry.fumble, 1).below(entry.high - entry.low, 5 - entry.low)
    after_play(d, oob=99)
    run_steps(rig, rig.engine.snap, d)
    assert " Starr drops back, then takes off " in texts(rig)
    assert rig.engine.s.extras.recent["QB"] == ["QB02", "QB03", "QB05"]


# ----- every cell of the three rows: the fewest and the most yards -----

@pytest.mark.parametrize("kind", ["sneak", "keeper", "draw"])
@pytest.mark.parametrize("call", [1, 2, 3, 4, 5, 6])
def test_each_cell_gives_its_fewest_and_its_most_yards_when_no_slide_is_drawn(tmp_path, kind, call):
    play = {"sneak": QB_SNEAK, "keeper": QB_KEEPER, "draw": QB_DRAW}[kind]
    low, high = T.QB_ROWS[kind][call - 1]
    for yards in (low, high):
        rig = rig_for(tmp_path / ("y%d" % yards), play, call, yard_line=20)
        run_steps(rig, rig.engine.snap, run_draws(kind, call, yards))
        assert rig.engine.outcomes[0].yards == yards                                # rnd(2) = 2: no slide
        assert rig.engine.s.stats[1].running_yards == yards


# ----- a loss, a safety, a touchdown -----

def test_a_loss_on_a_keeper_is_a_rush_for_a_loss_never_a_sack(tmp_path):
    rig = rig_for(tmp_path, QB_KEEPER, 3, down=1, to_go=10)                         # Keeper against the Long Run call: -4 to 3
    run_steps(rig, rig.engine.snap, run_draws("keeper", 3, -4))
    s = rig.engine.s
    assert " There is a loss of 4 yards on the play." in texts(rig)
    assert (s.yard_line, s.down, s.to_go) == (26, 2, 14)
    assert (s.stats[1].running_plays, s.stats[1].running_yards, s.stats[1].sacked) == (1, -4, 0)
    assert (s.extras.qb_runs, s.extras.qb_yards) == ([1, 0], [-4, 0])
    assert rig.engine.outcomes[0].kind == O.RUN


def test_a_keeper_in_the_end_zone_runs_the_countdown_and_scores_not_a_catch(tmp_path):
    rig = rig_for(tmp_path, QB_KEEPER, 1, half=1, yard_line=3, down=2, to_go=3)     # Keeper against Goal Line: -2 to 6
    entry = QB.make_entry("keeper", 1)
    d = quiet_snap_count(Draws())
    snap_draws(d)
    d.rnd(5, 3).below(4, 1).rnd(entry.fumble, 1).below(entry.high - entry.low, 5 - entry.low)   # 5 yards from the 3
    touchdown_end(d, ones=3)                                                        # the distance 3: " 3", " 2", " 1"
    run_steps(rig, rig.engine.snap, d, until=("extra_point_choice",))
    spoken = texts(rig)
    assert spoken[spoken.index(" he is at the "):] == [" he is at the ", " 3", " 2", " 1", " TOUCH DOWN"]
    assert not any("catches" in t for t in spoken)
    s = rig.engine.s
    assert s.score(1) == 6
    assert [(o.kind, o.qb_run, o.yards) for o in rig.engine.outcomes] == [(O.TOUCHDOWN, "keeper", 5)]
    assert (s.extras.qb_runs, s.extras.qb_yards) == ([1, 0], [5, 0])
    assert (s.stats[1].running_plays, s.stats[1].running_yards) == (1, 5)


def test_a_keeper_that_loses_yards_in_his_own_end_zone_is_a_safety(tmp_path):
    rig = rig_for(tmp_path, QB_KEEPER, 3, half=2, yard_line=2, down=1, to_go=10)    # his own 2: a loss of 3 is a safety
    entry = QB.make_entry("keeper", 3)
    d = quiet_snap_count(Draws())
    snap_draws(d)
    d.rnd(5, 1).below(4, 0).rnd(entry.fumble, 1).below(entry.high - entry.low, -3 - entry.low)
    d.below(4, 0).rady()                                                            # L; the pause after the score
    assert run_steps(rig, rig.engine.snap, d) == "kick_off"
    s = rig.engine.s
    assert (s.score(2), s.score(1)) == (2, 0)
    assert P.SAFETY in texts(rig)
    assert [(o.kind, o.qb_run) for o in rig.engine.outcomes] == [(O.SAFETY_KIND, "keeper")]
    assert rig.engine.s.extras.qb_runs == [1, 0]


# ----- the fumble -----

def test_a_fumble_on_a_draw_is_a_fumble_lost_and_not_a_running_play(tmp_path):
    rig = rig_for(tmp_path, QB_DRAW, 4)                                             # Draw against the Blitz: fumble 1 in 90
    entry = QB.make_entry("draw", 4)
    assert entry.fumble == 90
    d = quiet_snap_count(Draws())
    snap_draws(d)
    d.rnd(5, 4).rnd(entry.fumble, 13)                                               # the fumble test hits
    d.below(6, 0).below(40, 0)                                                      # L = 5 to 10; the spot 5 to 44
    run_steps(rig, rig.engine.snap, d)
    st = rig.engine.s.stats[1]
    assert (st.running_plays, st.running_yards, st.fumbles_lost) == (0, 0, 1)
    assert rig.engine.s.extras.qb_runs == [0, 0]                                    # a fumbled run is not counted (Q60)
    assert [(o.kind, o.qb_run) for o in rig.engine.outcomes] == [(O.FUMBLE, "draw")]


@pytest.mark.parametrize("kind, odds", [("sneak", 100), ("keeper", 90), ("draw", 90), ("scramble", 200)])
def test_the_fumble_odds_are_the_designs(kind, odds):
    assert QB.make_entry(kind, 3).fumble == odds


# ----- the slide (design 7.3) -----

def test_a_gain_of_8_or_more_may_end_in_a_slide_that_cuts_the_gain_and_stays_in_bounds(tmp_path):
    rig = rig_for(tmp_path, QB_KEEPER, 6, down=2, to_go=10, yard_line=20)           # Keeper against the Long Pass call: 4 to 14
    run_steps(rig, rig.engine.snap, run_draws("keeper", 6, 10, line=3, direction=1, slide=2))   # 10 yards, cut 2: 8
    spoken = texts(rig)
    i = spoken.index(" Starr runs around the left side ")
    assert spoken[i + 1:i + 3] == [" Starr slides feet first ", " There is a gain of 8 yards on the play"]
    assert " and is tackled by ODef1 " not in spoken
    assert sounds_played(rig)[-1] == "foot11"                                       # the whistle
    s, x = rig.engine.s, rig.engine.s.extras
    assert (s.stats[1].running_yards, x.qb_yards) == (8, [8, 0])
    assert rig.engine.outcomes[0].slid and rig.engine.outcomes[0].yards == 8
    assert not x.out_of_bounds and x.running                                        # the clock keeps running (7-2-1 (d))


def test_a_gain_of_7_never_draws_a_slide_and_a_gain_that_scores_never_slides(tmp_path):
    rig = rig_for(tmp_path, QB_KEEPER, 6, down=2, to_go=10, yard_line=20)
    run_steps(rig, rig.engine.snap, run_draws("keeper", 6, 7))                       # the script has no rnd(2): strict
    assert not rig.engine.outcomes[0].slid
    rig = rig_for(tmp_path / "td", QB_KEEPER, 6, half=1, yard_line=8, down=1, to_go=8)    # 8 yards from the 8: a touchdown
    entry = QB.make_entry("keeper", 6)
    d = quiet_snap_count(Draws())
    snap_draws(d)
    d.rnd(5, 1).below(4, 0).rnd(entry.fumble, 1).below(entry.high - entry.low, 8 - entry.low)    # no rnd(2): it scored
    touchdown_end(d, ones=5)
    run_steps(rig, rig.engine.snap, d, until=("extra_point_choice",))
    assert [(o.kind, o.slid) for o in rig.engine.outcomes] == [(O.TOUCHDOWN, False)]


def test_a_sneak_never_draws_a_slide(tmp_path):
    rig = rig_for(tmp_path, QB_SNEAK, 6, yard_line=20, down=3, to_go=5)             # 1 to 5 yards: the most is 5
    run_steps(rig, rig.engine.snap, run_draws("sneak", 6, 5))
    assert not rig.engine.outcomes[0].slid


@pytest.mark.parametrize("cut", [0, 1, 2])
def test_the_slide_cuts_0_to_2_yards_and_a_cut_of_0_still_slides(tmp_path, cut):
    rig = rig_for(tmp_path, QB_KEEPER, 6, down=1, to_go=10, yard_line=20)
    run_steps(rig, rig.engine.snap, run_draws("keeper", 6, 12, slide=cut))
    assert rig.engine.outcomes[0].yards == 12 - cut and rig.engine.outcomes[0].slid


def test_a_draw_slides_too(tmp_path):
    rig = rig_for(tmp_path, QB_DRAW, 4, yard_line=20)                                # Draw against the Blitz: 4 to 16
    run_steps(rig, rig.engine.snap, run_draws("draw", 4, 15, slide=1))
    assert rig.engine.outcomes[0].yards == 14 and rig.engine.outcomes[0].slid
    assert " Starr slides feet first " in texts(rig)


# ----- out of bounds (design 7.1) -----

@pytest.mark.parametrize("kind, play, rate", [("keeper", QB_KEEPER, 12), ("draw", QB_DRAW, 5)])
def test_a_keeper_goes_out_of_bounds_with_12_percent_and_a_draw_with_5(tmp_path, kind, play, rate):
    assert T.QB_OUT_OF_BOUNDS[kind] == rate
    for value, out in ((rate - 1, True), (rate, False)):                            # below(100) < rate is out
        rig = rig_for(tmp_path / ("v%d" % value), play, 5, yard_line=20)
        run_steps(rig, rig.engine.snap, run_draws(kind, 5, 4, oob=value, ready_cut=0 if out else None))
        assert (X.text("NXC-04") in texts(rig)) is out
        assert rig.engine.s.extras.out_of_bounds is out


def test_a_sneak_is_never_out_of_bounds_and_draws_no_out_of_bounds_number(tmp_path):
    rig = rig_for(tmp_path, QB_SNEAK, 2, yard_line=20, down=3, to_go=2)
    run_steps(rig, rig.engine.snap, run_draws("sneak", 2, 1))                       # strict: no below(100) in the script
    assert X.text("NXC-04") not in texts(rig)


# ----- the scramble (design 7.1) -----

def test_a_sack_becomes_a_scramble_with_the_scramble_draw_and_takes_back_the_pass(tmp_path):
    rig = rig_for(tmp_path, 4, 4, yard_line=30, down=1, to_go=10)                    # Short Pass against the Blitz: sack 50 %
    entry = QB.make_entry("scramble", 4)
    assert (entry.low, entry.high, entry.fumble) == (1, 15, 200)                     # 1 to 14 yards, fumble 1 in 200
    d = quiet_snap_count(Draws())
    snap_draws(d)
    first_dropback(d)
    d.raw(0.10)                                                                       # 10 <= 50: the original draws a sack
    d.below(100, T.QB_SCRAMBLE_FROM_SACK - 1)                                         # the scramble draw: below(100) < 22
    d.rnd(200, 1).below(14, 9).rnd(2, 2)                                              # no fumble; 10 yards; no slide
    after_play(d, oob=99, live=(5, 0))
    run_steps(rig, rig.engine.snap, d)
    spoken = texts(rig)
    i = spoken.index("Starr takes the snap")
    assert spoken[i + 1:i + 5] == [" He steps back to pass", " Starr cannot find a receiver and takes off running ",
                                   " AND IS CAUGHT BY ODef1 ", " There is a gain of 10 yards on the play"]
    assert sounds_played(rig)[-1] == "foot5"                                         # PlayTackle(2)
    st = rig.engine.s.stats[1]
    assert (st.pass_attempts, st.sacked, st.passing_yards, st.interception_count) == (0, 0, 0, 0)
    assert (st.running_plays, st.running_yards) == (1, 10)
    o = rig.engine.outcomes[0]
    assert (o.kind, o.qb_run, o.offense_play, o.yards) == (O.RUN, "scramble", 4, 10)
    assert rig.engine.s.extras.qb_runs == [1, 0]


def test_the_original_sack_stands_when_the_scramble_draw_misses(tmp_path):
    rig = rig_for(tmp_path, 4, 4)
    d = quiet_snap_count(Draws())
    snap_draws(d)
    first_dropback(d)
    d.raw(0.10)
    d.below(100, T.QB_SCRAMBLE_FROM_SACK)                                             # 22 is not below 22: a sack
    d.rnd(6, 1).rnd(50, 1).below(12, 0)                                               # the sack phrase, no fumble, -12
    d.below(5, 0).rnd(4, 1).below(11, 0)                                              # L = 4 to 8; no banter; R
    run_steps(rig, rig.engine.snap, d)
    st = rig.engine.s.stats[1]
    assert (st.sacked, st.pass_attempts) == (1, 1)
    assert [(o.kind, o.qb_run) for o in rig.engine.outcomes] == [(O.SACK, "")]
    assert rig.engine.s.extras.qb_runs == [0, 0]


def test_an_incompletion_becomes_a_scramble_before_the_throw_sentence_with_6_percent(tmp_path):
    rig = rig_for(tmp_path, 4, 4, yard_line=30)                                       # Short Pass against the Blitz: 70 % complete
    d = quiet_snap_count(Draws())
    snap_draws(d)
    first_dropback(d)
    d.raw(0.99).raw(0.95)                                                             # no sack (99 > 50); 95 >= 70: incomplete
    d.below(100, T.QB_SCRAMBLE_FROM_INCOMPLETE - 1)                                   # 5 < 6: a scramble
    d.rnd(200, 1).below(14, 2)                                                        # 3 yards
    after_play(d, oob=99, live=(5, 0))
    run_steps(rig, rig.engine.snap, d)
    spoken = texts(rig)
    i = spoken.index("Starr takes the snap")
    assert spoken[i + 1:i + 3] == [" He steps back to pass", " Starr cannot find a receiver and takes off running "]
    assert not any(t in spoken for t in P.THROW_PHRASES)                              # no throw sentence
    assert rig.engine.s.stats[1].pass_attempts == 0
    o = rig.engine.outcomes[0]
    assert (o.qb_run, o.yards) == ("scramble", 3)


@pytest.mark.parametrize("value, scramble_from_sack, scramble_from_incomplete", [
    (0, True, True), (5, True, True), (6, True, False), (21, True, False), (22, False, False), (99, False, False)])
def test_the_two_scramble_draws_are_below_22_for_a_sack_and_below_6_for_an_incompletion(tmp_path, value, scramble_from_sack,
                                                                                        scramble_from_incomplete):
    rig = rig_for(tmp_path, 4, 4)
    rules, s = rig.engine.rules, rig.engine.s
    for method, expected in ((rules.qb.scramble_from_sack, scramble_from_sack),
                             (rules.qb.scramble_from_incomplete, scramble_from_incomplete)):
        rig.rnd.source = ScriptedRandom(Draws().below(100, value).values, strict=True)
        assert method(s) is expected


def test_with_quarterback_runs_off_no_scramble_draw_is_made(tmp_path):
    rig = rig_for(tmp_path, 4, 4, qb_on=False)
    rig.rnd.source = ScriptedRandom([], strict=True)
    assert rig.engine.rules.instead_of_sack(rig.engine.s) is None
    assert rig.engine.rules.instead_of_incompletion(rig.engine.s) is False


def test_a_scramble_that_scores_runs_the_countdown_and_is_a_touchdown_run_not_a_catch(tmp_path):
    rig = rig_for(tmp_path, 4, 4, half=1, yard_line=6, down=1, to_go=6)
    d = quiet_snap_count(Draws())
    snap_draws(d)
    first_dropback(d)
    d.raw(0.10).below(100, 0).rnd(200, 1).below(14, 9)                                # a scramble of 10 yards from the 6
    touchdown_end(d, ones=5, live=(5, 0))                                             # the distance is 6: " 5" to " 1"
    run_steps(rig, rig.engine.snap, d, until=("extra_point_choice",))
    assert [(o.kind, o.qb_run) for o in rig.engine.outcomes] == [(O.TOUCHDOWN, "scramble")]
    assert rig.engine.s.extras.qb_runs == [1, 0]
    assert not any("catches" in t for t in texts(rig))


def test_a_scramble_costs_5_to_9_seconds_and_a_run_4_to_7(tmp_path):
    rig = rig_for(tmp_path, 4, 4)
    state = rig.engine.s
    state.result_kind = O.RUN
    scramble = O.PlayOutcome(O.RUN, 1, 4, 4, yards=5, qb_run="scramble")
    assert [live_time(scramble, state, _Bound(5, k)) for k in range(5)] == [5, 6, 7, 8, 9]
    keeper = O.PlayOutcome(O.RUN, 1, 9, 4, yards=5, qb_run="keeper")
    assert [live_time(keeper, state, _Bound(4, k)) for k in range(4)] == [4, 5, 6, 7]


class _Bound:
    """A random source whose below(n) answers k and checks n."""

    def __init__(self, n, k):
        self.n, self.k = n, k

    def below(self, n):
        assert n == self.n, (n, self.n)
        return self.k


# ----- the computer: its offense and the defense's matching (design 7.4) -----

def computer_rig(tmp_path, play, down, to_go, qb_on=True, two_point=False):
    return rig_for(tmp_path, play, 1, qb_on=qb_on, down=down, to_go=to_go, two_point=two_point)


def call_hook(rig, draws: Draws):
    rig.rnd.source = ScriptedRandom(draws.values, strict=True)
    rig.rnd.trace = []
    rig.engine.rules.computer_offense(rig.engine.s)
    assert rig.rnd.trace == draws.sizes and rig.rnd.source.left == 0


@pytest.mark.parametrize("down, to_go, play, draw, expected", [
    (3, 1, 1, 1, QB_SNEAK),          # third and 1, a drawn run: a sneak with chance 1 in 2 (rnd(2) = 1)
    (3, 2, 4, 1, QB_SNEAK),          # third and 2, a short pass
    (4, 1, 2, 1, QB_SNEAK),          # fourth and 1 going for it: in place of "go for it"
    (4, 2, 5, 1, QB_SNEAK),
    (3, 1, 1, 2, 1),                 # rnd(2) = 2: the drawn play stays
    (4, 2, 3, 2, 3),
])
def test_the_computer_sneaks_on_third_or_fourth_and_one_or_two_with_chance_1_in_2(tmp_path, down, to_go, play, draw, expected):
    rig = computer_rig(tmp_path, play, down, to_go)
    call_hook(rig, Draws().rnd(2, draw))
    assert rig.engine.s.offense_play == expected


@pytest.mark.parametrize("down, play, draw, expected", [
    (1, 1, 1, QB_KEEPER), (2, 3, 1, QB_KEEPER), (3, 4, 1, QB_KEEPER),               # one draw rnd(150): 1 a keeper
    (1, 1, 2, QB_DRAW), (2, 5, 2, QB_DRAW), (3, 2, 2, QB_DRAW),                     # 2 a draw
    (1, 1, 3, 1), (2, 5, 150, 5), (3, 3, 77, 3),                                    # anything else: the drawn play
])
def test_the_computer_draws_one_number_on_downs_1_to_3_for_a_keeper_or_a_draw(tmp_path, down, play, draw, expected):
    assert T.QB_COMPUTER_OTHER_ONE_IN == 150
    rig = computer_rig(tmp_path, play, down, 8)
    call_hook(rig, Draws().rnd(T.QB_COMPUTER_OTHER_ONE_IN, draw))
    assert rig.engine.s.offense_play == expected


@pytest.mark.parametrize("play, down, to_go, qb_on, two_point", [
    (6, 4, 1, True, False), (7, 4, 8, True, False),                                  # a kick stays a kick: no draw
    (1, 4, 8, True, False),                                                          # fourth down, long: go for it as drawn
    (1, 3, 1, False, False), (1, 1, 10, False, False),                              # quarterback runs off
    (1, 3, 1, True, True),                                                           # the try: items 1 to 5 only
])
def test_the_computer_draws_nothing_where_no_rule_applies(tmp_path, play, down, to_go, qb_on, two_point):
    rig = computer_rig(tmp_path, play, down, to_go, qb_on=qb_on, two_point=two_point)
    call_hook(rig, Draws())
    assert rig.engine.s.offense_play == play


@pytest.mark.parametrize("play, match", [(QB_SNEAK, 1), (QB_KEEPER, 3), (QB_DRAW, 2)])
def test_the_computers_defense_matches_a_repeated_quarterback_run(tmp_path, play, match):
    rig = rig_for(tmp_path, play, 1)
    s = rig.engine.s
    s.previous_play, s.repeats = play, 1              # the same play a second time: matched with chance 1 in 2 (L588)
    rig.rnd.source = ScriptedRandom(Draws().rnd(6, 6).rnd(2, 2).values, strict=True)      # the drawn defense 6; 2: no stay
    assert rig.engine.offense_chosen() == rig.engine.snap
    assert (s.repeats, s.defense_play) == (2, match)
    s.previous_play, s.repeats = play, 2                                                 # the third time: always matched
    rig.rnd.source = ScriptedRandom(Draws().rnd(6, 6).values, strict=True)
    rig.engine.offense_chosen()
    assert s.defense_play == match
    s.previous_play, s.repeats = 0, 0                                                    # a first use: the drawn defense stays
    rig.rnd.source = ScriptedRandom(Draws().rnd(6, 6).values, strict=True)
    rig.engine.offense_chosen()
    assert s.defense_play == 6


def test_the_defense_match_table_keeps_the_originals_five_entries():
    assert {k: v for k, v in DEFENSE_MATCH.items() if k <= 5} == {1: 1, 2: 3, 3: 5, 4: 5, 5: 6}
    assert {k: v for k, v in DEFENSE_MATCH.items() if k > 5} == {8: 1, 9: 3, 10: 2}
