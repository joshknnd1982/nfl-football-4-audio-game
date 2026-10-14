"""Reading sound files. This is inspired by Jim Kitchen."""
import os
import wave

import pytest

from nfl4.audio import wavdata
from nfl4.audio.wavdata import SoundLoadError, load_sound_file, parse_wav
from nfl4.data import paths
from wavmaker import floats, sine, wav_bytes, write

DATA = os.path.join(os.path.dirname(__file__), "data")


def test_8bit_is_unsigned_with_silence_at_128():
    sound = parse_wav(wav_bytes([0.0, 0.0, 0.5, -0.5], rate=8000, bits=8))
    assert sound.rate == 8000 and sound.channels == 1 and sound.frames == 4
    values = floats(sound)
    assert values[0] == 0.0
    assert values[2] == pytest.approx(0.5, abs=0.01)
    assert values[3] == pytest.approx(-0.5, abs=0.01)


@pytest.mark.parametrize("bits", [16, 24, 32])
def test_pcm_depths(bits):
    original = sine(440, 0.01, 22050)
    sound = parse_wav(wav_bytes(original, rate=22050, bits=bits))
    assert sound.frames == len(original)
    assert floats(sound) == pytest.approx(original, abs=2e-4)


def test_float32_and_float64():
    original = sine(300, 0.01, 11025)
    for bits in (32, 64):
        sound = parse_wav(wav_bytes(original, bits=bits, fmt_tag=3))
        assert floats(sound) == pytest.approx(original, abs=6e-5)         # 16-bit samples: a step is 3e-5


def test_extensible_header():
    original = sine(300, 0.01, 11025)
    sound = parse_wav(wav_bytes(original, bits=16, extensible=True))
    assert floats(sound) == pytest.approx(original, abs=1e-3)


def test_stereo_keeps_both_channels():
    both = [(0.25, -0.25)] * 100
    sound = parse_wav(wav_bytes(both, channels=2))
    assert sound.channels == 2 and sound.frames == 100
    assert floats(sound, 0)[0] == pytest.approx(0.25, abs=1e-3) and floats(sound, 1)[0] == pytest.approx(-0.25, abs=1e-3)


def test_24_and_32_bit_and_8_bit_stereo_keep_their_levels():
    for bits in (8, 24, 32):
        sound = parse_wav(wav_bytes([(0.5, -0.25)] * 10, bits=bits, channels=2))
        assert floats(sound, 0)[3] == pytest.approx(0.5, abs=0.01) and floats(sound, 1)[3] == pytest.approx(-0.25, abs=0.01), bits


def test_float_wav_with_not_a_number_and_out_of_range_values():
    sound = parse_wav(wav_bytes([float('nan'), 3.0, -3.0, 0.5], bits=32, fmt_tag=3))
    values = sound.samples()
    assert list(values[:3]) == [0, 32767, -32768] and values[3] == pytest.approx(16384, abs=1)


def test_extra_chunk_with_odd_size_is_skipped():
    assert parse_wav(wav_bytes(sine(200, 0.01, 11025), extra_chunk=True)).frames == 110


def test_cut_off_data_keeps_whole_frames():
    sound = parse_wav(wav_bytes(sine(200, 0.01, 11025), bits=16, truncate=3))
    assert sound.frames == 108                    # 110 frames, 3 bytes missing: 2 frames lost


def test_data_size_larger_than_file_uses_what_is_there():
    sound = parse_wav(wav_bytes(sine(200, 0.01, 11025), data_size=0xFFFFFFFF))
    assert sound.frames == 110


@pytest.mark.parametrize("raw", [
    b"", b"RIFF", b"not a wave file at all, just text",
    b"RIFF\x04\x00\x00\x00WAVE",
    wav_bytes([]),                                                  # no samples
    wav_bytes([0.1], rate=0),                                       # rate 0
    wav_bytes([0.1, 0.1, 0.1], channels=3),                         # 3 channels
])
def test_damaged_files_raise_soundloaderror(raw, tmp_path):
    path = tmp_path / "bad.wav"
    path.write_bytes(raw)
    with pytest.raises(SoundLoadError):
        load_sound_file(str(path))


def test_missing_file_and_unknown_type_raise_soundloaderror(tmp_path):
    with pytest.raises(SoundLoadError):
        load_sound_file(str(tmp_path / "nothing.wav"))
    (tmp_path / "x.txt").write_text("hello")
    with pytest.raises(SoundLoadError, match="not supported"):
        load_sound_file(str(tmp_path / "x.txt"))


def test_random_bytes_in_a_wav_file(tmp_path):
    path = tmp_path / "noise.wav"
    path.write_bytes(os.urandom(5000))
    with pytest.raises(SoundLoadError):
        load_sound_file(str(path))


def test_very_long_sound_is_refused(tmp_path):
    path = write(tmp_path / "long.wav", [0.0] * (8000 * 31), rate=8000, bits=8)
    with pytest.raises(SoundLoadError, match="long"):
        load_sound_file(path)


def test_every_shipped_wav_loads_and_matches_the_standard_reader():
    folder = os.path.join(paths.program_dir(), "assets", "sounds")
    for number in range(1, 43):
        path = os.path.join(folder, f"brain{number}.wav")
        ours = load_sound_file(path)
        with wave.open(path, "rb") as ref:
            assert ours.rate == ref.getframerate(), number
            assert ours.frames == ref.getnframes(), number
            assert ours.channels == ref.getnchannels() == 1, number


def test_ogg_flac_mp3_need_the_mixer_and_decode_with_it(monkeypatch):
    import pygame
    for ext in ("ogg", "flac", "mp3"):
        path = os.path.join(DATA, f"tone.{ext}")
        pygame.mixer.quit()
        with pytest.raises(SoundLoadError, match="sound system"):
            load_sound_file(path)
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    pygame.mixer.init(44100, -16, 2, 256)
    try:
        for ext in ("ogg", "flac", "mp3"):
            sound = load_sound_file(os.path.join(DATA, f"tone.{ext}"))
            assert sound.rate == 44100 and sound.channels == 1
            assert 0.09 < sound.seconds < 0.2
            assert sound.peak > 0.1 * 32768
    finally:
        pygame.mixer.quit()


def test_constants_match_the_playbook_lookup_order():
    assert wavdata.DECODER_EXTENSIONS[0] == ".wav"
