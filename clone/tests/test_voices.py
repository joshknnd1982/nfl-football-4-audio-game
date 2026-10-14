"""Voice list with thousands of entries and broken ones (playbook 7.4). This is inspired by Jim Kitchen's Brain."""
import time

from nfl4.speech.voices import VoiceCatalog, enumerate_voices, search


class Token:
    def __init__(self, i):
        self.i = i

    @property
    def Id(self):
        if self.i % 997 == 13:
            raise OSError("broken token")
        return f"HKEY_LOCAL_MACHINE\\SOFTWARE\\Voices\\Tokens\\Voice{self.i}"

    def GetDescription(self):
        if self.i % 500 == 7:
            raise OSError("no description")
        return f"Fake Voice {self.i}"


class Tokens:
    def __init__(self, n):
        self.Count = n

    def Item(self, i):
        if i == 4242:
            raise OSError("item failed")
        return Token(i)


def test_five_thousand_voices_with_broken_entries():
    start = time.monotonic()
    voices, broken = enumerate_voices(lambda: Tokens(5000))
    assert time.monotonic() - start < 1.0
    expected_broken = len([i for i in range(5000) if i % 997 == 13]) + 1
    assert broken == expected_broken
    assert len(voices) == 5000 - expected_broken
    assert voices[0].index == 0 and voices[0].name == "Fake Voice 0"
    no_desc = next(v for v in voices if v.index == 7)
    assert no_desc.name == "Voice7"                  # falls back to the token's last ID part


def test_unavailable_list_is_empty_not_an_error():
    def fail():
        raise OSError("SAPI missing")
    assert enumerate_voices(fail) == ([], 0)


def test_search_prefix_first_then_contains():
    voices, _ = enumerate_voices(lambda: Tokens(300))
    found = search(voices, "fake voice 12")
    names = [v.name for v in found]
    assert names[0] == "Fake Voice 12" and "Fake Voice 120" in names
    assert search(voices, "") == voices
    assert [v.name for v in search(voices, "voice 299")] == ["Fake Voice 299"]


def test_catalog_loads_in_background_and_caches():
    calls = []

    def source():
        calls.append(1)
        return Tokens(2000)
    catalog = VoiceCatalog(source, com_init=False)
    catalog.load_async()
    voices = catalog.voices()
    assert len(voices) > 1990
    catalog.voices()
    assert len(calls) == 1
    catalog.load_async(refresh=True)
    catalog.voices()
    assert len(calls) == 2
