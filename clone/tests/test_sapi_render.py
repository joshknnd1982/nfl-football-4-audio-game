"""SAPI 5 rendered mode with a fake voice and a fake player. This is inspired by Jim Kitchen.

Rendered mode (DECISIONS 2026-10-13, speech latency): SAPI makes each text into memory and a player
plays it, so stopping speech never waits for SAPI's audio output.
"""
import threading
import time

from nfl4.speech.sapi5 import CHUNK_FROM_CHARS, SVSF_PURGE_BEFORE_SPEAK, SapiBackend, split_chunks

from test_sapi_backend import TOKENS, FakeTokenObject, FakeVoice


class FakeStream:
    def __init__(self):
        self.data = b""

    def GetData(self):
        return memoryview(self.data)


class RenderVoice(FakeVoice):
    """A fake voice that writes 'audio' (the text as bytes) into its output stream after a delay."""
    def __init__(self, make_seconds=0.01, **kw):
        super().__init__(TOKENS, **kw)
        self.AudioOutputStream = None
        self.make_seconds = make_seconds
        self._making = None     # (text, stream, ready_at)
        self.output_resets = 0

    def Speak(self, text, flags):
        if self.fail_speak and text:
            raise OSError("engine broke")
        if flags & SVSF_PURGE_BEFORE_SPEAK:
            self._making = None
        if text:
            self._making = (text, self.AudioOutputStream, time.monotonic() + self.make_seconds)
        self.calls.append((text, flags))
        return 1

    def GetAudioOutputs(self):
        voice = self

        class Outputs:
            def Item(self, i):
                voice.output_resets += 1
                return "default output"
        return Outputs()

    def WaitUntilDone(self, ms):
        """Like SAPI: waits up to ms for the speech to be made."""
        deadline = time.monotonic() + ms / 1000.0
        while self._making is not None:
            text, stream, ready = self._making
            if time.monotonic() >= ready:
                stream.data = text.encode()
                self._making = None
                return True
            if time.monotonic() >= deadline:
                return False
            time.sleep(0.0005)
        return True


class FakePlayer:
    """Records blocks; each block 'plays' for play_seconds in order."""
    def __init__(self, play_seconds=0.05, refuse=False):
        self.blocks = []
        self.play_seconds = play_seconds
        self.refuse = refuse
        self.resets = 0
        self._end = 0.0
        self.closed = False

    def write(self, pcm):
        if self.refuse:
            return False
        self.blocks.append(bytes(pcm))
        self._end = max(time.monotonic(), self._end) + self.play_seconds
        return True

    def busy(self):
        return time.monotonic() < self._end

    def reset(self):
        self.resets += 1
        self._end = 0.0

    def close(self):
        self.closed = True


def make(voice=None, player=None, **kw):
    voice = voice or RenderVoice()
    player = player or FakePlayer()
    b = SapiBackend(voice_factory=lambda: voice, token_factory=FakeTokenObject, com_init=False, render=True,
                    player_factory=lambda: player, stream_factory=FakeStream, **kw)
    started = b.start(5)
    assert started.ok, started.error
    return b, voice, player


def texts(player):
    return [block.decode() for block in player.blocks]


def test_speech_is_made_in_memory_and_played():
    b, voice, player = make()
    try:
        b.speak("Select. no panning")
        b.wait_until_done()
        assert texts(player) == ["Select. no panning"]
        assert not b.is_speaking()
    finally:
        b.close()


def test_wait_covers_making_and_playing():
    b, voice, player = make(player=FakePlayer(play_seconds=0.15))
    try:
        t0 = time.monotonic()
        b.speak("hello")
        b.wait_until_done()
        assert time.monotonic() - t0 >= 0.15
    finally:
        b.close()


def test_stop_resets_the_player_at_once():
    b, voice, player = make(player=FakePlayer(play_seconds=5.0))
    try:
        b.speak("a long speech")
        time.sleep(0.1)
        assert b.is_speaking()
        t0 = time.monotonic()
        b.stop()
        for _ in range(500):
            if not b.is_speaking():
                break
            time.sleep(0.002)
        assert not b.is_speaking()
        assert time.monotonic() - t0 < 0.3
        assert player.resets >= 1
    finally:
        b.close()


def test_stop_while_making_drops_the_unfinished_text():
    b, voice, player = make(voice=RenderVoice(make_seconds=0.2))
    try:
        b.speak("never heard")
        time.sleep(0.05)
        b.stop()
        b.speak("heard")
        b.wait_until_done()
        assert texts(player) == ["heard"]
    finally:
        b.close()


def test_rapid_keys_only_the_last_item_is_left():
    b, voice, player = make(player=FakePlayer(play_seconds=0.5))
    try:
        for i in range(60):
            b.stop()
            b.speak(f"item {i}")
            time.sleep(0.003)
        b.wait_until_done()
        assert texts(player)[-1] == "item 59"
        assert player.resets >= 1
    finally:
        b.close()


def test_queued_texts_play_in_order():
    b, voice, player = make()
    try:
        for word in ("one", "two", "three"):
            b.speak(word)
        b.wait_until_done()
        assert texts(player) == ["one", "two", "three"]
    finally:
        b.close()


def test_long_text_is_made_sentence_by_sentence_in_order():
    text = ("This is the first sentence of the help. Here is the second one, a bit longer. "
            "And the third sentence follows. Then the fourth sentence ends it.")
    assert len(text) > CHUNK_FROM_CHARS
    b, voice, player = make()
    try:
        b.speak(text)
        b.wait_until_done()
        got = texts(player)
        assert len(got) == 4
        assert " ".join(got) == text
    finally:
        b.close()


def test_pitch_is_sent_as_xml_per_chunk():
    b, voice, player = make(pitch=3)
    try:
        b.speak("hello")
        b.wait_until_done()
        assert texts(player) == ['<pitch absmiddle="3">hello</pitch>']
    finally:
        b.close()


def test_no_audio_device_falls_back_to_direct_speech():
    voice = FakeVoice(TOKENS)

    def no_device():
        raise OSError("no device")

    b = SapiBackend(voice_factory=lambda: voice, token_factory=FakeTokenObject, com_init=False, render=True,
                    player_factory=no_device)
    assert b.start(5).ok
    try:
        b.speak("hello")
        b.wait_until_done()
        assert [c[0] for c in voice.calls] == ["hello"]
    finally:
        b.close()


def test_refused_audio_does_not_hang_or_crash():
    b, voice, player = make(player=FakePlayer(refuse=True))
    try:
        b.speak("hello")
        done = threading.Event()
        threading.Thread(target=lambda: (b.wait_until_done(), done.set()), daemon=True).start()
        assert done.wait(2.0)
        b.speak("again")
        b.wait_until_done()
    finally:
        b.close()


def test_failing_engine_does_not_hang():
    b, voice, player = make(voice=RenderVoice(fail_speak=True))
    try:
        b.speak("hello")
        b.wait_until_done()
        assert player.blocks == []
        assert not b.is_speaking()
    finally:
        b.close()


def test_close_closes_the_player():
    b, voice, player = make()
    b.speak("x")
    b.close()
    assert player.closed


def test_settings_still_reach_the_voice():
    b, voice, player = make()
    try:
        b.set_volume(40)
        b.set_rate(3)
        b.speak("x")
        b.wait_until_done()
        assert voice.Volume == 40 and voice.Rate == 3
    finally:
        b.close()


def test_split_chunks_short_text_whole():
    assert split_chunks(" My Brain  By Jim Kitchen.") == [" My Brain  By Jim Kitchen."]


def test_split_chunks_joins_tiny_pieces_and_loses_nothing():
    text = "Yes. No. " + "This sentence is long enough to stand alone. " * 2 + "Ok."
    chunks = split_chunks(text)
    assert all(len(c) >= 25 for c in chunks)
    assert " ".join(chunks).split() == text.split()


def test_split_chunks_splits_lines():
    text = "First line of the about text goes here\nSecond line of the about text goes here too"
    assert len(split_chunks(text)) == 2


# ----- the speed probe: slow voices are spoken directly -----

def test_a_fast_voice_is_rendered():
    b, voice, player = make()
    try:
        assert b.rendered
    finally:
        b.close()


def test_a_voice_too_slow_to_render_is_spoken_directly():
    voice = RenderVoice(make_seconds=1.0)
    b, voice, player = make(voice=voice)
    try:
        assert not b.rendered
        assert voice.output_resets == 1              # back on SAPI's own output
        voice.make_seconds = 0.01
        b.speak("hello")
        b.wait_until_done()
        assert player.blocks == []                   # nothing went through the player
        assert ("hello", 1) in voice.calls           # SAPI was given the text to play itself (async flag)
    finally:
        b.close()


def test_choosing_another_voice_probes_it_again():
    b, voice, player = make()
    try:
        assert b.rendered
        voice.make_seconds = 1.0
        b.set_voice(None)
        for _ in range(300):
            if not b.rendered:
                break
            time.sleep(0.01)
        assert not b.rendered
        voice.make_seconds = 0.01
        b.set_voice(None)
        for _ in range(300):
            if b.rendered:
                break
            time.sleep(0.01)
        assert b.rendered
        b.speak("again")
        b.wait_until_done()
        assert texts(player)[-1] == "again"
    finally:
        b.close()


# ----- texts a voice cannot say: other ways to write them -----

from nfl4.speech.sapi5 import ascii_fold, speech_variants  # noqa: E402


def test_variants_put_a_comma_between_adjacent_numbers():
    assert speech_variants("Infovox230 1.12 American English Child")[0] == "Infovox230, 1.12 American English Child"


def test_variants_fold_letters_with_marks_and_curly_quotes():
    text = "Infovox Fran" + chr(0xe7) + "ais: voix d" + chr(0x2019) + "homme"
    assert speech_variants(text)[0] == "Infovox Francais: voix d'homme"
    assert ascii_fold("Íslenska rödd") == "Islenska rodd"


def test_the_last_variant_spells_the_digits_and_plain_text_has_none():
    assert "two three zero" in speech_variants("Infovox230 1.12 American")[-1]
    assert speech_variants("Select. no panning") == []
    assert speech_variants("") == []


class SilentForNumbersVoice(RenderVoice):
    """Makes no audio for two numbers with only a space between them, like BestSpeech Fred."""
    def Speak(self, text, flags):
        import re
        if text and re.search(r"\d\s+\d", text):
            self._making = (text, self.AudioOutputStream, time.monotonic())
            self._mute = True
            self.calls.append((text, flags))
            return 1
        self._mute = False
        return super().Speak(text, flags)

    def WaitUntilDone(self, ms):
        done = super().WaitUntilDone(ms)
        if done and getattr(self, "_mute", False):
            self.AudioOutputStream.data = b""
        return done


def test_a_text_that_makes_no_sound_is_tried_again_written_another_way():
    b, voice, player = make(voice=SilentForNumbersVoice())
    try:
        b.speak("Infovox230 1.12 American")
        b.wait_until_done()
        assert texts(player) == ["Infovox230, 1.12 American"]
    finally:
        b.close()


def test_a_text_no_variant_can_save_ends_quietly_without_looping():
    class SilentVoice(RenderVoice):
        def WaitUntilDone(self, ms):
            done = super().WaitUntilDone(ms)
            if done:
                self.AudioOutputStream.data = b""
            return done

    b, voice, player = make(voice=SilentVoice())
    try:
        b.speak("Infovox230 1.12 American")
        b.wait_until_done()
        assert player.blocks == [] and not b.is_speaking()
        assert len([c for c in voice.calls if c[0]]) <= 4              # the text and at most its variants, never forever
    finally:
        b.close()
