"""A voice that kills the program is set aside at the next start (owner bug on Brain 2026-10-13: SmoothTalker chosen,
then the game would not start any more; playbook 7.4.5). This is inspired by Jim Kitchen.

nfl4 S7.1: five speakers, so several voices are opened one after the other; the trial holds the one being opened and is
cleared only by that voice's all clear (or by a normal close). The whole program's side is in test_app_startup.py,
the SAPI backend's side in test_sapi_roles.py.
"""
from nfl4.data.voiceguard import CRASHED_FILE, MAX_LISTED, TRIAL_FILE, VoiceGuard, voice_label

VOICE = r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\TokenEnums\SmoothTalker\SmoothTalker"


def test_a_trial_that_never_ended_puts_the_voice_on_the_list_and_is_reported_once(tmp_path):
    guard = VoiceGuard(str(tmp_path))
    guard.arm(VOICE)
    assert (tmp_path / TRIAL_FILE).is_file()
    restarted = VoiceGuard(str(tmp_path))            # the next start
    assert restarted.recover() == VOICE
    assert restarted.is_crashed(VOICE) and restarted.is_crashed(VOICE.lower())
    assert not (tmp_path / TRIAL_FILE).exists()
    assert VoiceGuard(str(tmp_path)).recover() is None          # reported once
    assert (tmp_path / CRASHED_FILE).read_text().split() == [VOICE]


def test_a_voice_that_spoke_or_a_normal_close_leaves_no_trial_behind(tmp_path):
    guard = VoiceGuard(str(tmp_path))
    guard.arm(VOICE)
    guard.clear()
    assert guard.recover() is None and not guard.is_crashed(VOICE)
    guard.arm(None)                                   # the default voice is never put on trial
    assert not (tmp_path / TRIAL_FILE).exists()


def test_clearing_one_voice_leaves_another_voices_trial_alone(tmp_path):
    guard = VoiceGuard(str(tmp_path))
    guard.arm("token-2")
    guard.arm(VOICE)                                  # a second speaker's voice is being opened now
    guard.clear("token-2")                            # the first one's all clear comes late: VOICE stays on trial
    assert (tmp_path / TRIAL_FILE).read_text().strip() == VOICE
    guard.clear(VOICE.upper())                        # ids compare without case
    assert not (tmp_path / TRIAL_FILE).exists()
    guard.clear("token-2")                            # nothing on trial: nothing happens
    assert guard.recover() is None


def test_choosing_a_set_aside_voice_again_takes_it_off_the_list(tmp_path):
    guard = VoiceGuard(str(tmp_path))
    guard.arm(VOICE)
    guard.recover()
    guard.forget(VOICE)
    assert not guard.is_crashed(VOICE) and guard.crashed() == []


def test_the_list_is_bounded_and_survives_other_voices(tmp_path):
    guard = VoiceGuard(str(tmp_path))
    for i in range(MAX_LISTED + 10):
        guard.arm(f"voice-{i}")
        guard.recover()
    assert len(guard.crashed()) == MAX_LISTED and guard.is_crashed(f"voice-{MAX_LISTED + 9}")
    assert not guard.is_crashed("voice-0")


def test_a_folder_that_cannot_be_written_never_raises(tmp_path):
    blocker = tmp_path / "file"
    blocker.write_text("not a folder")
    guard = VoiceGuard(str(blocker / "inside"))
    guard.arm(VOICE)
    guard.clear(VOICE)
    guard.clear()
    assert guard.recover() is None and guard.crashed() == [] and not guard.is_crashed(VOICE)
    guard.forget(VOICE)


def test_a_label_for_the_spoken_notice():
    assert voice_label(VOICE) == "SmoothTalker"
    assert voice_label("") == "voice" and voice_label("token-3") == "token-3"
