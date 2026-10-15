"""The golden Classic transcript (nfl4 only: NFL_EXTRA_FEATURES 3 C8, NFL_EXTRAS_DESIGN 2 P1). This is inspired by Jim Kitchen.

One whole game on a seeded source with a seeded player (keys at every wait: Enter, digits, Down, F1 to F4, Escape answered
"no"), played on the virtual clock with the real sound layer, recorded event by event in order: every text given to the
speech engine (speaker, rate step), every stop of the speech, every sound slot event (play, level, stop, with its sound,
level, pitch, pan and loop), every pause with its site in the lifted code, every random draw's size, every key, each
with its virtual time in milliseconds. tests/data/golden_classic_s73b.txt is the record made in S7.3b, before any extra
feature exists. The game in Classic mode must give exactly this transcript, so a PX session (the seven extra features)
that changes anything the classic game does fails here.

Re-record only when a classic session (S7.3c, S7.4, S7.5, S7.7, S8.x) changes what the classic game does ON PURPOSE,
never in PX, and write the reason in DECISIONS.md:  set NFL4_RECORD_GOLDEN=1 and run this file, then diff the old and
new file. A failure prints the first line that differs.
"""
import os
import random
from pathlib import Path

from pagrig import make_rig, play
from test_pag_games import lively_policy

GOLDEN = Path(__file__).parent / "data" / "golden_classic_s73b.txt"
SEED, PLAYER_SEED = 2034, 3034          # chosen from 34 seeds: touchdowns of both, two good two-point tries, a safety
HEADER = ("# nfl4 golden Classic transcript, S7.3b: one game, game seed %d, player seed %d, Bengals (visitor, the "
          "player calls the toss) at the Jets, week 1; time in ms of virtual time\n" % (SEED, PLAYER_SEED))


class Recording(list):
    def __init__(self, sink, kind, clock):
        super().__init__()
        self.sink, self.kind, self.clock = sink, kind, clock

    def append(self, item):
        self.sink.append((self.clock(), self.kind, item))
        super().append(item)


def record_game(tmp_path):
    rig = make_rig(tmp_path, rng=random.Random(SEED), vtrnt=2)
    rig.keys.policy = lively_policy(rig, PLAYER_SEED)
    events = []
    now = lambda: rig.clock.now - 1000.0
    speak, stop = rig.sapi.speak, rig.sapi.stop

    def speak_recorded(text, role=None, rate_step=0):
        events.append((now(), "say", (role, rate_step, text)))
        return speak(text, role=role, rate_step=rate_step)

    def stop_recorded():
        events.append((now(), "stop", None))
        return stop()

    rig.sapi.speak, rig.sapi.stop = speak_recorded, stop_recorded
    rig.audio.slot_log = Recording(events, "snd", now)
    rig.game.pause_log = Recording(events, "pause", now)
    rig.rnd.trace = Recording(events, "rnd", now)
    post = rig.keys.post

    def post_recorded(code):
        events.append((now(), "key", code))
        return post(code)

    rig.keys.post = post_recorded
    result = play(rig)
    lines = []
    for time, kind, item in events:
        stamp = "%9d" % round(time * 1000)
        if kind == "say":
            role, step, text = item
            lines.append("%s say %s %d |%s|" % (stamp, role, step, text))
        elif kind == "snd":
            lines.append("%s snd %d %s %s %d %d %d %s" % (stamp, item.slot, item.action, item.sound_id or "-",
                                                          item.volume, item.freq, item.pan, "loop" if item.loop else "once"))
        elif kind == "pause":
            site, seconds = item
            lines.append("%s pause %s %.6f" % (stamp, hex(site) if site is not None else "None", seconds))
        elif kind == "rnd":
            lines.append("%s rnd %d" % (stamp, item))
        elif kind == "key":
            lines.append("%s key %d" % (stamp, item))
        else:
            lines.append("%s %s" % (stamp, kind))
    lines.append("result %r" % (result.scores,))
    return lines


def test_the_classic_game_gives_the_golden_transcript(tmp_path):
    lines = record_game(tmp_path)
    text = HEADER + "\n".join(lines) + "\n"
    if os.environ.get("NFL4_RECORD_GOLDEN") == "1":
        GOLDEN.parent.mkdir(exist_ok=True)
        GOLDEN.write_text(text, encoding="utf-8", newline="\n")
    expected = GOLDEN.read_text(encoding="utf-8").split("\n")
    got = text.split("\n")
    for number, (want, have) in enumerate(zip(expected, got), start=1):
        assert have == want, "line %d differs:\n  golden: %s\n  now:    %s" % (number, want, have)
    assert len(got) == len(expected)


def test_the_golden_game_is_a_whole_game_with_the_main_events():
    text = GOLDEN.read_text(encoding="utf-8")
    for needed in ("| hut 1 |", "| TOUCH DOWN|", "| End of the Second Quarter|", "| THE GAME IS OVER|",
                   "| The Final score is|", "| Stats After Quarter number 4|", "| here is the coin toss |",
                   "snd 6 play snd_foot14", "pause 0x44027e", "| here's the instant rea play |"):
        assert needed in text, needed
    assert text.count("\n") > 5000
