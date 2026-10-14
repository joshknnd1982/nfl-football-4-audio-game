"""The mixed output itself, read back sample by sample through SDL's disk driver (silent: nothing reaches the
speakers; the driver writes what the mixer makes to a file, in real time). This is inspired by Jim Kitchen.

What the other tests cannot see: the level the mixer really applies (D-023, hundredths of a decibel through the chunk
volume and the panning effect, output.split_gain), that a level change reaches a playing loop without restarting it
(the crowd ramps), that two slots add and a new sound in a slot replaces the old one (GAP_REGISTER G-A1), and pan.
A constant sample value (16000) makes every segment one plain number. The driver keeps its own pace, slower than the
wall clock when the PC is busy, so these tests check values and order, never how many samples a sleep produced.
"""
import array
import time
from collections import Counter

import pytest

from nfl4.audio.output import OutputError, PygameOutput, split_value
from nfl4.audio.render import level_gain, pan_gains, render_stereo
from nfl4.audio.wavdata import Sampled

pytestmark = pytest.mark.mixer

AMP = 16000


def dc_stereo(seconds, value=AMP):
    return array.array("h", [value, value] * int(44100 * seconds)).tobytes()


@pytest.fixture
def disk(tmp_path, monkeypatch):
    monkeypatch.setenv("SDL_AUDIODRIVER", "disk")
    raw = tmp_path / "mix.raw"
    try:
        output = PygameOutput(256, devicename=str(raw))
    except OutputError as exc:
        pytest.skip(f"SDL's disk driver is not available here: {exc}")
    state = {"closed": False}

    def finish():
        if not state["closed"]:
            time.sleep(0.05)
            output.close()
            state["closed"] = True
        samples = array.array("h")
        samples.frombytes(raw.read_bytes())
        return samples[0::2], samples[1::2]
    yield output, finish
    if not state["closed"]:
        output.close()


def wait_idle(output, slot, gap=0.03):
    while output.busy(slot):
        time.sleep(0.001)
    time.sleep(gap)


def runs(samples):
    """(start, end) of every stretch of non-zero samples."""
    found, start = [], None
    for i, value in enumerate(samples):
        if value and start is None:
            start = i
        elif not value and start is not None:
            found.append((start, i))
            start = None
    if start is not None:
        found.append((start, len(samples)))
    return found


def left_runs_in_order(samples):
    """(value, length) of every stretch of one non-zero value, in order (silence between them is not needed)."""
    found = []
    for value in samples:
        if not value:
            continue
        if found and found[-1][0] == value:
            found[-1][1] += 1
        else:
            found.append([value, 1])
    return [tuple(item) for item in found]


def test_the_mixer_applies_the_level_in_hundredths_of_a_decibel(disk):
    output, finish = disk
    levels = (0, -100, -600, -1200, -1500, -2750, -2900, -5000)
    for volume in levels:
        output.play(0, dc_stereo(0.04), level_gain(volume))
        wait_idle(output, 0)
    left, right = finish()
    values = Counter(zip(left, right))
    expected = {}
    for volume in levels:
        want = AMP * level_gain(volume)
        got = [v for (v, r), n in values.items() if v == r and v and abs(v - want) <= want * 0.005 + 2 and n > 100]
        assert len(got) == 1, (volume, want, values.most_common(12))
        assert abs(got[0] - AMP * split_value(level_gain(volume))) <= 2, volume
        expected[volume] = got[0]
    # nothing else was ever written: the level holds from each sound's first sample (no transient value)
    assert set(values) <= {(0, 0)} | {(v, v) for v in expected.values()}
    order = [v for v, _ in left_runs_in_order(left)]
    assert order == [expected[volume] for volume in levels]


def test_a_level_change_reaches_a_playing_loop_without_restarting_it(disk):
    output, finish = disk
    output.play(1, dc_stereo(0.02), level_gain(-1200), loop=True)
    time.sleep(0.08)
    output.set_gain(1, level_gain(-600))
    time.sleep(0.08)
    output.set_gain(1, level_gain(0))
    time.sleep(0.08)
    output.stop(1)
    left, _ = finish()
    found = runs(left)
    assert len(found) == 1                                 # one unbroken loop
    values = Counter(left[found[0][0]:found[0][1]])
    for volume in (-1200, -600, 0):
        want = AMP * level_gain(volume)
        assert any(abs(v - want) <= want * 0.005 + 2 and n > 1000 for v, n in values.items()), volume


def test_two_slots_add_up(disk):
    output, finish = disk
    output.play(1, dc_stereo(0.2, 8000), 1.0, loop=True)
    output.play(2, dc_stereo(0.05, 4000), 1.0)
    wait_idle(output, 2, gap=0.05)
    output.stop(1)
    left, _ = finish()
    values = Counter(left)
    # under load the disk driver writes fewer samples than the wall clock says: count presence, not durations
    assert values[12000] > 200 and values[8000] > 100
    assert set(values) <= {0, 8000, 12000}


def test_a_new_sound_in_a_slot_replaces_the_old_one(disk):
    output, finish = disk
    output.play(5, dc_stereo(0.5, 8000), 1.0)
    time.sleep(0.05)
    output.play(5, dc_stereo(0.05, 3000), 1.0)
    wait_idle(output, 5, gap=0.05)
    left, _ = finish()
    values = Counter(left)
    assert values[3000] > 200 and values[8000] > 100       # presence, not durations (the driver's pace varies)
    assert set(values) <= {0, 3000, 8000}                  # never both at once (11000)
    last = runs(left)[-1]
    assert Counter(left[last[1] - 100:last[1]]).most_common(1)[0][0] == 3000


def test_pan_attenuates_the_far_channel_in_the_mixed_output(disk):
    output, finish = disk
    mono = Sampled(array.array("h", [AMP] * 4410).tobytes(), 44100, 1)
    output.play(4, render_stereo(mono, 44100, 1400, 1.0), 1.0)          # foot10's extreme pans
    wait_idle(output, 4)
    output.play(4, render_stereo(mono, 44100, -1500, 1.0), 1.0)
    wait_idle(output, 4)
    left, right = finish()
    pairs = [pair for pair, n in Counter(zip(left, right)).items() if pair != (0, 0)]
    assert len(pairs) == 2, pairs
    right_side = next(p for p in pairs if p[1] > p[0])                  # pan +1400: the left is the far channel
    left_side = next(p for p in pairs if p[0] > p[1])
    assert right_side[1] == pytest.approx(AMP, abs=2)
    assert right_side[0] == pytest.approx(AMP * pan_gains(1400)[0], abs=2)
    assert left_side[0] == pytest.approx(AMP, abs=2)
    assert left_side[1] == pytest.approx(AMP * pan_gains(-1500)[1], abs=2)


def test_master_volume_zero_is_silence(disk):
    output, finish = disk
    output.volume = 0.0
    output.play(0, dc_stereo(0.05), 1.0)
    wait_idle(output, 0)
    left, right = finish()
    assert not any(left) and not any(right)
