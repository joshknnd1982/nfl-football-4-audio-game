"""WaveOut: the real device in silence, and a stuck device (fake library). This is inspired by Jim Kitchen."""
import time

import pytest

from nfl4.speech import waveout
from nfl4.speech.waveout import STUCK_SECONDS, WaveOut, WaveOutError


def silence(seconds, rate=44100):
    return bytes(2 * int(rate * seconds))


@pytest.mark.sapi
def test_real_device_plays_silence_then_is_idle_and_reset_is_instant():
    try:
        out = WaveOut(44100)
    except WaveOutError:
        pytest.skip("no audio device")
    try:
        assert out.write(silence(0.2))
        assert out.busy()
        deadline = time.monotonic() + 2
        while out.busy() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert not out.busy()
        out.write(silence(2.0))
        t0 = time.perf_counter()
        out.reset()
        assert not out.busy() and time.perf_counter() - t0 < 0.1
    finally:
        out.close()
        out.close()


class StuckLibrary:
    """A device that accepts blocks and never says they are done."""
    def __init__(self):
        self.resets = 0

    def waveOutOpen(self, *a):
        return 0

    def waveOutPrepareHeader(self, *a):
        return 0

    def waveOutUnprepareHeader(self, *a):
        return 0

    def waveOutWrite(self, *a):
        return 0

    def waveOutReset(self, *a):
        self.resets += 1
        return 0

    def waveOutClose(self, *a):
        return 0


def test_a_device_that_never_finishes_is_given_up_on_so_speech_waits_end():
    lib = StuckLibrary()
    now = [100.0]

    class Stuck(WaveOut):
        _library = staticmethod(lambda: lib)

    out = Stuck(44100, clock=lambda: now[0])
    assert out.write(silence(0.5))
    assert out.busy()                               # on time: still playing as far as anyone can tell
    now[0] += 0.5 + STUCK_SECONDS - 0.1
    assert out.busy()                               # not yet past the margin
    now[0] += 0.2
    assert not out.busy()                           # past it: dropped, the wait for speech can end
    assert lib.resets == 1
    assert out.write(silence(0.1)) and out.busy()   # and it works again afterwards
