"""S8.1: the conformance tests that the map of tests/data/conformance_map.tsv found missing. This is inspired by Jim Kitchen.

Each test names the requirement it closes: Q29 (the interception chance grows with every pass), Q35 (the fake sentences are never
spoken), Q58 and G-S5 (the key echo), G-A2 (the safety net of the play noise), and the sound roles that the owner confirmed by
ear in the three listening rounds (observations/listening_round_*_answers.txt, WAV_EVENT_MAP 6).
"""
import random
import re

import pytest

from gamerig import Rig
from nfl4.audio import ids
from nfl4.audio.output import SLOT_HIKE, SLOT_NOISE, SLOT_TACKLE
from nfl4.game import phrases
from nfl4.speech.roles import ANNOUNCER, OWN_QUARTERBACK
from pagrig import engine_rig
from specfiles import GAME_ROOT, need
from test_pag_games import spy_game

ENTER = 13


# ----- Q58, G-S5: the key echo (saykey, p_42e3d0) -----

def echo(rig, code, char):
    rig.keys.code_text, rig.keys.char = code, char
    mark, said = len(rig.sapi.events), len(rig.said)
    rig.game.saykey()
    return [kind for kind, _ in rig.sapi.events[mark:]], rig.said[said:]


def test_the_key_echo_purges_then_queues_the_character_in_the_last_voice_at_the_normal_rate_q58():
    rig = Rig()
    rig.game.say(" hello ")
    events, said = echo(rig, "71", "g")
    assert events == ["stop", "speak"]                       # the purge first, then the character, asynchronously
    assert said == [("g", ANNOUNCER, 0)]                     # the announcer spoke last; the rate step 0 is the normal rate (Q58)
    rig.game.wisoff, rig.game.qorp = 1, 1
    rig.game.say3(" Hut ")                                    # the quarterback of the side on offense speaks last
    events, said = echo(rig, "72", "h")
    assert said == [("h", OWN_QUARTERBACK, 0)]


def test_f1_is_purged_but_not_echoed_and_a_control_character_is_never_sent():
    rig = Rig()
    rig.game.say(" hello ")
    for code, char in (("112", "F"), ("27", ""), ("9", "\t"), ("8", "\b"), ("13", "\r")):
        events, said = echo(rig, code, char)
        assert events == ["stop"] and said == [], (code, char)


# ----- G-A2: the play noise never loops at a key wait; the net stops it and counts it -----

def test_the_safety_net_stops_the_play_noise_at_a_key_wait_and_counts_it_and_otherwise_does_nothing(tmp_path):
    rig = engine_rig(tmp_path, answers=[ENTER, ENTER, ENTER])
    engine, sounds = rig.engine, rig.sounds
    sounds.make_hike()
    sounds.make_play_noise()
    engine.getkey()                                           # no noise: nothing to stop, nothing counted
    assert engine.noise_net == 0
    sounds.play_noise()
    assert sounds.play_noise_running()
    engine.getkey()
    assert engine.noise_net == 1 and not sounds.play_noise_running()
    assert [e.action for e in rig.slot_log if e.slot == SLOT_NOISE][-1] == "stop"
    sounds.play_noise()
    engine.getkey2()                                          # getkey2 has the same net
    assert engine.noise_net == 2 and not sounds.play_noise_running()
    sounds.play_noise()
    engine.keys.answers.append(ENTER)
    engine.getkey2(net=False)                                 # the one wait that keeps the noise (Q61: the run-out question)
    assert engine.noise_net == 2 and sounds.play_noise_running()


# ----- Q29: the interception chance grows with every pass a side throws -----

def test_the_interception_chance_is_1_in_c_minus_3_per_pass_since_the_last_interception_and_at_most_1_in_2_q29(tmp_path):
    """The long pass against the long pass defense: C = 30, so 1 in 27 at the first pass, 1 in 24 at the second, and so on
    down to 1 in 2 (the floor) from the tenth pass on; an interception sets the count back to zero."""
    rig = engine_rig(tmp_path, wisoff=1, defense=2, half=2, yard_line=30, down=1, to_go=10)
    rig.keys.fast = True
    rig.sounds.sleep = lambda seconds: rig.clock.sleep(0.02)
    rig.rnd.source = random.Random(29)
    engine, s = rig.engine, rig.engine.s
    asked = []
    real = rig.rnd.below_single

    def spy(n):
        asked.append(n)
        return real(n)
    rig.rnd.below_single = spy
    stats = s.stats[1]
    stats.interception_count = 0
    seen = {"first": 0, "grown": 0, "floor": 0, "reset": 0}
    for _ in range(600):
        s.wisoff, s.defense, s.half, s.yard_line, s.down, s.to_go = 1, 2, 2, 30, 1, 10
        s.offense_play, s.defense_play = 5, 6
        before, picks, sacks, asked[:] = stats.interception_count, stats.intercepted, stats.sacked, []
        step = engine.snap
        while step.__name__ not in ("next_play", "play_menu", "touchdown"):
            step = step()
        if stats.sacked > sacks or not asked:
            continue                                          # a sack: the count grew by 3 but no interception draw was made
        expected = max(2, 30 - (before + 3))                  # the spec's numbers, not the module's: 1 in 2 at most (Q29)
        assert asked[0] == expected, (before, asked)
        if before == 0:
            assert asked[0] == 27
            seen["first"] += 1
        elif expected > 2:
            seen["grown"] += 1
        else:
            seen["floor"] += 1
        if stats.intercepted > picks:
            assert stats.interception_count == 0
            seen["reset"] += 1
    assert min(seen.values()) > 0, seen


# ----- Q35: the fake sentences are built and overwritten, never spoken -----

def test_the_fake_sentences_are_never_spoken_in_a_whole_game_q35(tmp_path):
    fakes = [f for f in phrases.UNSPOKEN_FAKES if "fake" in f]
    assert len(fakes) == 5
    checked = 0
    for seed in range(8):
        rig, engine, _ = spy_game(tmp_path / str(seed), 700 + seed)
        spoken = [t for t, *_ in rig.said]
        assert any("hands" in t or "hand off" in t for t in spoken) and any("pass" in t for t in spoken)
        for text in spoken:
            assert not any(fake in text for fake in fakes), text
            checked += 1
    assert checked > 1000


def test_nothing_but_the_phrases_module_knows_the_unspoken_fakes():
    source = (GAME_ROOT / "game" / "src" / "nfl4").rglob("*.py")
    users = [p.name for p in source if p.name != "phrases.py" and "UNSPOKEN_FAKES" in p.read_text(encoding="utf-8")]
    assert users == []


# ----- the sound roles that the owner confirmed by ear (observations/, WAV_EVENT_MAP 6) -----

OBSERVED = {   # the owner's label of the listening round -> (foot number, the game's event name)
    "ambient sound one": (8, "ambient sound 1"), "ambient sound two": (9, "ambient sound 2"),
    "ambient sound three": (10, "ambient sound 3, panned"), "intro music": (0, "intro music"),
    "play noise": (14, "play noise"), "ball contact": (12, "ball contact"), "pile up hit": (4, "hit, pile up"),
    "two tackler hit": (5, "hit, two tacklers"), "single tackle hit": (6, "hit, single tackle"),
    "referee whistle": (11, "whistle"), "Super Bowl win music": (25, "Super Bowl"), "the snap": (3, "hike"),
    "kick": (7, "kick"), "censor bleep": (13, "bleep"), "crowd, first layer": (1, "crowd bed 1"),
    "crowd, second layer": (2, "crowd bed 2"),
    **{"celebration sound %s" % word: (15 + i, "celebration %d" % (15 + i)) for i, word in enumerate(
        ("one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"))},
}


def owner_answers():
    rows = []
    folder = need(GAME_ROOT / "observations")
    for path in sorted(folder.glob("listening_round_*_answers.txt")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("#") or not line.strip():
                continue
            rows.append([part.strip() for part in line.split("|")])
    return rows


def test_every_sound_the_owner_confirmed_has_the_clones_event_name_for_its_file():
    rows = owner_answers()
    assert len(rows) == 26
    for file, kind, label, typed, _when in rows:
        assert kind == "guess" and typed == "", (file, kind)          # the owner agreed with the name; no correction
        number, event = OBSERVED[label]
        assert file == "foot%d.wav" % number
        assert ids.EVENT_NAMES[number] == event
    assert sorted(int(r[0][4:-4]) for r in rows) == list(range(26))   # all 26 files were heard


def test_the_confirmed_roles_play_the_confirmed_files_through_the_games_sound_procedures(tmp_path):
    rig = Rig(sounds_dir=tmp_path / "sounds", rng=random.Random(3))
    sounds = rig.sounds
    sounds.make_hike()
    sounds.make_play_noise()
    sounds.play_hike()
    sounds.play_noise()
    for n in (1, 2, 3, 8):                                   # PlayTackle(n) loads foot(n + 3): pile up, two tacklers, single, whistle
        sounds.play_tackle(n)
    played = [(e.slot, e.sound_id) for e in rig.slot_log if e.action == "play"]
    assert (SLOT_HIKE, "snd_foot3") in played and (SLOT_NOISE, "snd_foot14") in played
    assert [s for slot, s in played if slot == SLOT_TACKLE] == ["snd_foot4", "snd_foot5", "snd_foot6", "snd_foot11"]


def test_whole_games_play_the_kick_the_ball_contact_the_bleep_and_the_celebrations_the_owner_named(tmp_path):
    heard = set()
    for seed in range(12):
        rig, _, _ = spy_game(tmp_path / str(seed), 800 + seed)
        heard |= {e.sound_id for e in rig.slot_log if e.action == "play"}
    expected = {"snd_foot%d" % n for n in (3, 4, 5, 6, 7, 11, 12, 13, 14)}
    assert expected <= heard, sorted(expected - heard)
    assert len({h for h in heard if re.fullmatch(r"snd_foot(1[5-9]|2[0-4])", h)}) >= 1


# ----- NFL_EXTRA_FEATURES N5.1 (the research) and GAP_REGISTER G-C1 (the 10,000 games and seasons of S8.1) -----

def test_the_research_documents_exist_and_name_their_sources():
    from specfiles import SPEC, read_spec
    for name, size in (("NFL_RULES_RESEARCH.md", 100000), ("MADDEN_PLAYBOOK_RESEARCH.md", 20000),
                       ("MADDEN_FRANCHISE_RESEARCH.md", 20000)):
        text = read_spec(SPEC / name)
        assert len(text) > size, name
        assert text.count("http") >= 10, name
        assert "SRC-OFFICIAL" in text or "SRC-SECONDARY" in text, name


def test_the_10000_game_and_season_property_runs_of_s81_found_no_failure():
    """work/s81/property_games_s81.py and property_seasons_s81.py (nothing else may run beside them) wrote these reports."""
    for name, first in (("prop_games_10000.txt", "games 10000 "), ("prop_seasons_10000.txt", "seasons 10000 ")):
        lines = need(GAME_ROOT / "work" / "s81" / name).read_text(encoding="utf-8").splitlines()
        assert lines[0].startswith(first) and ", failures 0," in lines[0], lines[0]
        assert not [l for l in lines if l.startswith("FAIL")]
