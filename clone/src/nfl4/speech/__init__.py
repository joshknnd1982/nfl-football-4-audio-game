"""Speech layer: SAPI 5, NVDA and JAWS behind one manager. This is inspired by Jim Kitchen's Brain."""
from __future__ import annotations

import logging

from .jaws import JawsBackend
from .manager import SpeechManager
from .nvda import NvdaBackend
from .sapi5 import SapiBackend, SapiStart

log = logging.getLogger(__name__)


def create_speech(settings) -> tuple[SpeechManager, SapiStart]:
    """Start the engines from the speech settings. The caller checks SapiStart for no voices."""
    sapi = SapiBackend(voice_id=settings.voice_id, rate=settings.rate,
                       volume=settings.volume, pitch=settings.pitch, render=True)
    started = sapi.start()
    manager = SpeechManager(sapi, NvdaBackend(), settings.mode, JawsBackend())
    return manager, started
