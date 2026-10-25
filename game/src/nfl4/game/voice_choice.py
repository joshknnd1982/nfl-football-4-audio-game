"""The voice choice of one speaker: engines first, then that engine's voices. This is inspired by Jim Kitchen.

GAP_REGISTER G-S8 (D-031 item 3): the original's F12 asked " Do you wish to use <name> for the announcer?" voice by voice
(GAME_SPEC 4.7), unusable with the owner's 1,811 voices; the game uses the picker of playbook 7.4.2 (owner-verified on
Brain: its `Functions.choose_voice`) once per speaker, in the original's order, with the speaker named in the title. Step
1 lists "All voices of all engines" and every engine with its voice count, opening on the engine of the speaker's voice;
step 2 the voices of the chosen engine, opening on the speaker's voice marked "current voice". Escape in a voice list goes
back to the engines; Escape in the engine list keeps the speaker's voice. Up, Down, Page Up and Down, Home, End, F1 and
the letter keys (type-ahead or first letter, the saved setting list_letters) as in every list of the game.
"""
from __future__ import annotations

import logging
import time
from typing import Callable

from ..speech.roles import spoken_name
from ..speech.voices import ENGINE_FALLBACK, VoiceInfo, first_letter_index, group_by_engine
from ..speech.voices import search as search_voices
from . import extra_texts as words
from .spoken_menu import ListPicker

log = logging.getLogger("nfl4.game")


def role_title(role: str) -> str:
    """The game's title of the engine list for one speaker (GAP_REGISTER 8 draft: " Choose the voice for the
    announcer. "): "Choose the voice for your punter"."""
    return "Choose the voice for " + spoken_name(role)


def voices_or_none(catalog) -> list[VoiceInfo] | None:
    """The voice list (waits up to 5 s for it the first time); None when there is no catalog or it failed."""
    if catalog is None:
        return None
    try:
        return list(catalog.voices(timeout=5.0))
    except Exception as exc:
        log.warning("the voice list could not be read: %s", exc)
        return None


def choose_role_voice(speech, keys, voices: list[VoiceInfo], role: str, current_id: str | None,
                      letter_mode: Callable[[], str] = lambda: "type",
                      clock: Callable[[], float] = time.monotonic) -> VoiceInfo | None:
    """The engine list, then the voices of one engine; the chosen voice, or None when Escape left the engine list."""
    in_use = next((v for v in voices if current_id and v.voice_id == current_id), voices[0])
    groups = group_by_engine(voices)
    plain = ["All voices of all engines"] + [engine for engine, _ in groups]
    spoken = [words.all_voices_item(len(voices))] + [words.engine_item(e, len(vs)) for e, vs in groups]
    start = 1 + next((i for i, (e, _) in enumerate(groups) if e == (in_use.engine or ENGINE_FALLBACK)), 0)

    def find_engine(text: str) -> int | None:
        needle = text.strip().casefold()
        hits = [i for i, n in enumerate(plain) if n.casefold().startswith(needle)]
        hits += [i for i, n in enumerate(plain) if needle in n.casefold() and i not in hits]
        return hits[0] if hits else None

    while True:
        picked = ListPicker(speech, keys, role_title(role), len(spoken), lambda i: spoken[i], start=start,
                            search=find_engine, clock=clock, help_text=words.ENGINE_HELP,
                            first_letter=lambda c, at: first_letter_index(plain, c, at),
                            letter_mode=letter_mode).run()
        if picked is None:
            return None
        if picked == 0:
            subset, title = voices, words.ALL_VOICES_TITLE
        else:
            engine, subset = groups[picked - 1]
            title = words.engine_voices_title(engine)
        voice = _pick_voice(speech, keys, subset, title, in_use.voice_id, letter_mode, clock)
        if voice is not None:
            return voice
        start = picked                                   # Escape in the voice list: back to the engines


def _pick_voice(speech, keys, subset: list[VoiceInfo], title: str, current: str, letter_mode, clock):
    names = [v.name for v in subset]
    at = next((i for i, v in enumerate(subset) if v.voice_id == current), 0)

    def name(i: int) -> str:
        return names[i] + (", " + words.CURRENT_VOICE if subset[i].voice_id == current else "")

    def find(text: str) -> int | None:
        found = search_voices(subset, text) if text.strip() else []
        return subset.index(found[0]) if found else None

    chosen = ListPicker(speech, keys, title, len(subset), name, start=at, search=find, clock=clock,
                        first_letter=lambda c, cur: first_letter_index(names, c, cur),
                        letter_mode=letter_mode, help_text=words.list_help(letter_mode())).run()
    return None if chosen is None else subset[chosen]
