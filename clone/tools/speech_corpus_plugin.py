"""pytest plugin of S8.3 (G-S9): records every text that any test made the program say, for the silent-text check of
clone/tools/sapi_render_check.py. Use: PYTHONPATH=clone/tools pytest -p speech_corpus_plugin ... ; the texts go to the file named by S83_CORPUS (JSON lines)."""
import json
import os
import threading

from nfl4.speech.fake import FakeBackend

_texts = set()
_lock = threading.Lock()
_real = FakeBackend.speak


def _speak(self, text, role=None, rate_step=0):
    with _lock:
        _texts.add(text)
    return _real(self, text, role, rate_step)


def pytest_configure(config):
    FakeBackend.speak = _speak


def pytest_sessionfinish(session, exitstatus):
    path = os.environ.get("S83_CORPUS")
    if path:
        with _lock, open(path, "w", encoding="utf-8") as out:
            for text in sorted(_texts):
                out.write(json.dumps(text) + "\n")
