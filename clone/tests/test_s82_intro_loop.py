"""S8.2 (owner, 2026-10-20): "the intro sound kept looping until the game actually started". CLAUDE.md 0.21, playbook 7.15, B-A22.
This is inspired by Jim Kitchen.

The original stops its start-up loop (foot0) at the week line. On a later start the clone kept that, so a new season or a franchise played
the same sound through the kind-of-season, coach and team questions. The loop now ends when the welcome ends, in every start-up path, and
a safety stop runs before the first question of the season set-up. The test: no loop is playing at the first key wait of the program.
"""
from nfl4.game import texts
from programrig import DOWN, ENTER, ESC, preset_season, program_rig, saved_game

EXIT_KEYS = [DOWN, DOWN, DOWN, ENTER]


def watch(rig):
    """Marks in the speech engine's event list: where the intro stopped and where the program first waited for a key."""
    events = rig.sapi.events
    real_stop = rig.sounds.stop_oneshot
    rig.sounds.stop_oneshot = lambda: (events.append(("marker", "intro stopped")), real_stop())[-1]
    for name in ("getkey", "getkey2", "wait_key", "read_key"):
        real = getattr(rig.keys, name)

        def wrapper(*args, _real=real, _name=name, **kwargs):
            events.append(("marker", "key wait " + _name))
            return _real(*args, **kwargs)
        setattr(rig.keys, name, wrapper)


def order(rig):
    return [text for kind, text in rig.sapi.events if kind == "marker" or kind == "speak"]


def run_to_the_end(rig):
    try:
        rig.run()
    except AssertionError:
        pass                                    # the script of keys ran out: only the start matters here


def first_marks(rig):
    marks = order(rig)
    stop = marks.index("intro stopped")
    wait = next(i for i, m in enumerate(marks) if m.startswith("key wait"))
    return marks, stop, wait


def test_a_later_start_stops_the_intro_with_the_welcome_not_at_the_week_line(tmp_path):
    rig = program_rig(tmp_path, EXIT_KEYS, preset=preset_season())
    watch(rig)
    rig.run()
    marks, stop, wait = first_marks(rig)
    assert marks[stop - 1] == texts.TITLE_SPOKEN and stop < wait
    assert marks.count("intro stopped") == 1


def test_a_first_start_has_the_intro_stopped_before_the_first_key_wait(tmp_path):
    rig = program_rig(tmp_path, EXIT_KEYS + [ESC] * 6, first=True, preset=preset_season())
    watch(rig)
    run_to_the_end(rig)
    marks, stop, wait = first_marks(rig)
    assert stop < wait and marks.count("intro stopped") == 1


def test_a_new_season_stops_the_intro_before_the_first_question(tmp_path):
    rig = program_rig(tmp_path, [ESC] * 4)                     # no season in the files: the set-up asks the coach and the team
    watch(rig)
    run_to_the_end(rig)
    marks, stop, wait = first_marks(rig)
    assert stop < wait and marks.index(texts.TITLE_SPOKEN) < stop
    assert marks.count("intro stopped") == 1


def test_a_saved_game_start_stops_the_intro_before_the_first_key_wait(tmp_path):
    rig = program_rig(tmp_path, EXIT_KEYS, preset=preset_season(), outcomes=[saved_game()])
    rig.store.has_saved_game = lambda: True
    watch(rig)
    run_to_the_end(rig)
    marks = order(rig)
    assert marks.count("intro stopped") == 1                  # the saved game plays at once: the loop must be over before pag starts
    assert marks.index("intro stopped") < len(marks) and marks[marks.index("intro stopped") - 1] == texts.TITLE_SPOKEN


def test_the_stop_is_logged_with_its_reason_and_is_safe_to_call_twice(tmp_path):
    from nfl4.data import debuglog
    seen = []
    real_event = debuglog.event

    def spy(area, name, *args, **kwargs):
        if name in ("loop_start", "loop_stop"):
            seen.append((name, kwargs.get("reason")))
        return real_event(area, name, *args, **kwargs)
    debuglog.event = spy
    try:
        rig = program_rig(tmp_path, EXIT_KEYS, preset=preset_season())
        rig.run()
    finally:
        debuglog.event = real_event
    assert ("loop_start", None) in seen and ("loop_stop", "welcome_done") in seen
    assert [s for s in seen if s[0] == "loop_stop"] == [("loop_stop", "welcome_done")]          # the safety stop did nothing: already stopped
