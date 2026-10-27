"""Speech layer: SAPI 5 (five speakers), NVDA and JAWS behind one manager. This is inspired by Jim Kitchen."""
from __future__ import annotations

import logging

from .jaws import JawsBackend
from .manager import SpeechManager
from .nvda import NvdaBackend
from .roles import ALL_ROLES, ANNOUNCER
from .sapi5 import RoleVoice, SapiBackend, SapiStart

log = logging.getLogger(__name__)


def speaker_voices(settings, skip: frozenset[str] = frozenset()) -> dict[str, RoleVoice]:
    """The speakers from the speech settings (the five of the original and the extras' analyst and referee). A voice in `skip` (one that crashed the program, data/voiceguard.py)
    is not opened: that speaker uses the first voice until the player chooses it again."""
    voices = {}
    for role in ALL_ROLES:
        voice_id = settings.voices.get(role) or None
        if voice_id and voice_id.strip().lower() in skip:
            voice_id = None
        voices[role] = RoleVoice(voice_id, settings.volumes.get(role, 95))
    return voices


def create_speech(settings, skip: frozenset[str] = frozenset(), arm=None, clear=None) -> tuple[SpeechManager, SapiStart]:
    """Start the engines from the speech settings. arm and clear are the crash guard's calls (data/voiceguard.py);
    the caller checks SapiStart for no voices."""
    sapi = SapiBackend(rate=settings.rate, pitch=settings.pitch, render=True,
                       roles=speaker_voices(settings, skip), default_role=ANNOUNCER)
    sapi.on_voice_trial = arm
    sapi.on_voice_proven = clear
    started = sapi.start()
    manager = SpeechManager(sapi, NvdaBackend(), settings.mode, JawsBackend())
    return manager, started
