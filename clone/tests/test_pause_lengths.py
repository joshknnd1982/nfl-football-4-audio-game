"""The virtual-clock length of a snap count at the speech rates (GAP_REGISTER G-S2). This is inspired by Jim Kitchen.

rady waits Int(Rnd * 30) / (max(vr, 1) * 25) seconds (GAME_SPEC 7): at a rate of 1 or below 0 to 1.16 s, at rate 5 a fifth of
that, at rate 10 a tenth. The snap count of a line plunge with every draw at its largest (29) has six of them, after the
crowd's dy(0.2): the test writes the draws by hand from the lifted lines (the same order as test_pag_scrimmage.py), checks the
pauses that the engine recorded with the address of each call, and that the virtual clock moved at least that long (the
sounds' own waits come on top). The longest and the shortest snap count are the bounds the owner's pace control moves between.
"""
import pytest

from pagrig import Draws, run_steps
from test_pag_scrimmage import first_handoff, snap, snap_draws

SNAP_COUNT_SITES = [0x44027e, 0x440344, 0x4404a6, 0x44076b, 0x440b16, 0x440cb2]     # dy(0.2), then five rady
LONGEST = 29                                                                         # Int(Rnd * 30) at its largest


def a_line_plunge(steps: int) -> Draws:
    d = Draws()
    d.rnd(4, 2).rnd(10, 1).rady(steps).rnd(7, 3).rady(steps)
    d.rnd(5, 1).rnd(10, 3).rnd(28, 17).rady(steps).rnd(5, 3)
    d.below(4, 1).rady(steps).rnd(2, 1).rady(steps)
    snap_draws(d, carrier=4, d1=5, d2=9, phrase=1)
    first_handoff(d, group=2, phrase=1)
    d.rnd(3, 2).rnd(50, 1).below(7, 5)
    d.rnd(4, 1)
    return d


@pytest.mark.parametrize("vr, per_pause", [(-3, 1 / 25), (0, 1 / 25), (1, 1 / 25), (5, 1 / 125), (10, 1 / 250)])
def test_the_pauses_of_a_snap_count_follow_the_speech_rate(tmp_path, vr, per_pause):
    rig = snap(tmp_path, 1, 3)
    rig.game.options.set_vr(vr)
    start = rig.clock.now
    run_steps(rig, rig.engine.snap, a_line_plunge(LONGEST))
    pauses = rig.game.pause_log
    assert [site for site, _ in pauses[:6]] == SNAP_COUNT_SITES
    assert pauses[0][1] == pytest.approx(0.2)                                       # the crowd ramp's dy(0.2) at any rate
    count = sum(seconds for _, seconds in pauses[:6])
    assert count == pytest.approx(0.2 + 5 * LONGEST * per_pause)                     # the longest snap count at this rate
    assert rig.clock.now - start >= sum(seconds for _, seconds in pauses) - 1e-6    # the clock moved at least that long


def test_the_shortest_snap_count_is_only_the_crowd_pause(tmp_path):
    rig = snap(tmp_path, 1, 3)
    run_steps(rig, rig.engine.snap, a_line_plunge(0))
    assert sum(seconds for _, seconds in rig.game.pause_log[:6]) == pytest.approx(0.2)


def test_the_longest_snap_count_is_6_seconds_at_rate_one_and_1_36_at_rate_five(tmp_path):
    # GAME_SPEC 7 and G-S2: five pauses of up to 1.16 s plus the crowd's 0.2 s
    lengths = {}
    for vr in (1, 5):
        rig = snap(tmp_path, 1, 3)
        rig.game.options.set_vr(vr)
        run_steps(rig, rig.engine.snap, a_line_plunge(LONGEST))
        lengths[vr] = sum(seconds for _, seconds in rig.game.pause_log[:6])
    assert lengths[1] == pytest.approx(0.2 + 5 * 1.16)
    assert lengths[5] == pytest.approx(0.2 + 5 * 0.232)
