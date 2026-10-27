"""BC.3: the radio crew and the radio format, in both modes (nfl4 only, rule 0.13; CLAUDE.md 0.27 as amended, 0.33; D-178, D-179, D-189).
This is inspired by Jim Kitchen.

spec/NFL_BROADCAST_DESIGN.md sections 3 to 7, 9 to 11. The properties that matter:
- Classic is the original's game: with the crew on, a Classic game makes exactly the random draws of the engine's own Classic (the golden
  transcript's game) and ends with the same score; with the comments off it says exactly what the engine's Classic says.
- The format: the sign-on, the crew, the reporter and the analyst before the kick-off; the network now and then; the quarter and half
  updates; the station breaks; the reporter at half time and at a Franchise game's injury; the clock late in each half and the drive
  summary with the N. F. L. rules' real clock; the sign-off once, last.
- F8 silences all of it; F9, Rules, Broadcast silences the analyst and the reporter and the lines that name them, while the announcer's
  sign-on, breaks and sign-off stay.
- No line of the crew is said twice in a row, and a pool gives no line twice in a game while it has others.
- The names are the player's (F9, Rules, Broadcast crew); remarks.txt is read in Classic too; F11 and F12 ask for the analyst and the
  reporter in both modes; F5, F6 and README_keys name them.
"""
import random
import re
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import pytest

from gamerig import Rig
from nflrig import RecordingRules, nfl_engine_rig, sim_game
from pagrig import make_rig, play
from test_pag_games import lively_policy
from nfl4.data import customlists as cl
from nfl4.data.customize import Customization
from nfl4.data.settings import Settings
from nfl4.extras import broadcast as BC
from nfl4.extras import crew
from nfl4.extras import nx_texts as X
from nfl4.extras import remarks as RM
from nfl4.extras.classic_radio import ClassicRadioRules, classic_rules
from nfl4.extras.nfl_rules import NflRules, rules_from_settings
from nfl4.game import key_list
from nfl4.game.rules import CLASSIC
from nfl4.speech.roles import ALL_ROLES, ANNOUNCER, COLOR, REFEREE, SIDELINE

SEED, PLAYER_SEED = 2034, 3034          # the golden transcript's game (tests/test_pag_golden.py)
FORMAT_POOLS = ("SGN", "CRW", "SON", "UPD", "QUP", "STA", "ASN", "SIN", "SHT", "SGO", "NID", "LID", "DRV", "CLK")
PATTERNS = [(pool, re.compile(re.sub(r"<[a-z ]+>", ".+", re.escape(X.TEXTS[r.id].strip()))))
            for pool in RM.BROADCAST_POOLS for r in RM.DEFAULT_POOLS.lines(pool)]


def pool_of(text: str):
    for pool, pattern in PATTERNS:
        if pattern.fullmatch(text.strip()):
            return pool
    return None


def crew_lines(rig):
    """(pool, role, text) of every line of the broadcast, in order."""
    out = []
    for text, role, _step in rig.said:
        pool = pool_of(text)
        if pool is not None or text == X.text("NXB-B01"):
            out.append((pool or "HINT", role, text))
    return out


def classic_game(tmp_path, rules, comments_off=False, names=None, pools=None):
    rig = make_rig(tmp_path, rng=random.Random(SEED), vtrnt=2)
    rig.keys.policy = lively_policy(rig, PLAYER_SEED)
    if comments_off:
        rig.game.comtog_source = lambda: 1
    if pools is not None:
        rig.game.remark_pools = pools
    rig.rnd.trace = []
    result = play(rig, rules=rules)
    return rig, result


@pytest.fixture(scope="module")
def classic_pair(tmp_path_factory):
    bare = classic_game(tmp_path_factory.mktemp("bare"), CLASSIC)
    radio = classic_game(tmp_path_factory.mktemp("radio"), ClassicRadioRules(broadcast_on=True))
    return bare, radio


# ----- Classic stays the original's game -----

def test_classic_with_the_crew_makes_exactly_the_draws_and_the_score_of_the_engines_classic(classic_pair):
    (bare, bare_result), (radio, radio_result) = classic_pair
    assert len(bare.rnd.trace) > 1000 and radio.rnd.trace == bare.rnd.trace
    assert radio_result.scores == bare_result.scores == (28, 39)                 # the golden transcript's score (BC.2)
    plain = [entry for entry in radio.said if pool_of(entry[0]) is None and entry[0] != X.text("NXB-B01")]
    assert [(t, r) for t, r, _s in plain] == [(t, r) for t, r, _s in bare.said]   # the crew only adds lines; nothing of the game moves


def test_classic_with_the_comments_off_says_exactly_what_the_engines_classic_says(tmp_path, classic_pair):
    (bare, _r), _radio = classic_pair
    off, _result = classic_game(tmp_path, ClassicRadioRules(broadcast_on=True), comments_off=True)
    bare_off, _r2 = classic_game(tmp_path / "bare", CLASSIC, comments_off=True)
    assert off.said == bare_off.said and off.rnd.trace == bare_off.rnd.trace == bare.rnd.trace


def test_the_classic_broadcast_follows_the_radio_format(classic_pair):
    _bare, (radio, _result) = classic_pair
    lines = crew_lines(radio)
    pools = [pool for pool, _role, _text in lines]
    count = Counter(pools)
    assert pools[:6] == ["SGN", "CRW", "HINT", "ASN", "SON", "CKO"]             # the sign-on, the crew, where to set them, Walt names Nora (RC), Nora, Gus
    assert count["SGN"] == count["CRW"] == count["SON"] == count["CKO"] == count["SGO"] == 1 and pools[-1] == "SGO"
    assert count["QUP"] == 3 and count["SHT"] == 1 and count["CHT"] == 1         # quarters one and three and the half; Nora and Gus at the half
    assert count["STA"] == 3                                                     # the two two-minute warnings and half time
    assert count["NID"] + count["LID"] >= 4 and count["LID"] <= 1
    assert count["BN"] >= 5 and count["CLK"] == 0 and count["DRV"] == 0          # no real clock in Classic: no clock or drive lines
    roles = {pool: role for pool, role, _text in lines}
    assert roles["SON"] == roles["SHT"] == SIDELINE and roles["CKO"] == COLOR and roles["SGN"] == roles["BN"] == ANNOUNCER
    texts = [text for _pool, _role, text in lines]
    assert all(texts[i] != texts[i - 1] for i in range(1, len(texts)))
    assert not any(re.search(r"<[a-z ]+>", text) for text in texts)              # every placeholder filled
    assert any("Walt Kessler" in t for t in texts) and any("Nora Banks" in t for t in texts) and any("Gus Delgado" in t for t in texts)


def test_the_half_time_break_has_the_update_then_nora_then_gus_then_the_station_break(classic_pair):
    _bare, (radio, _result) = classic_pair
    pools = [pool for pool, _role, _text in crew_lines(radio)]
    half = pools.index("SHT")
    assert pools[half - 1] == "ASN" and "QUP" in pools[half - 4:half - 1]
    assert pools[half + 1] == "CHT" and pools[half + 2] == "STA"


# ----- the N. F. L. rules -----

def nfl_game(tmp_path, seed, on=True):
    rules = RecordingRules(penalties_on=True, onside_on=True, qb_on=True, challenges_on=True, playbooks_on=True, broadcast_on=on)
    rig, engine, rules, result = sim_game(tmp_path, seed, rules=rules, trace=True)
    return rig, result


@pytest.mark.parametrize("seed", [21, 22, 23])
def test_the_nfl_rules_broadcast_has_the_clock_and_never_moves_a_draw(tmp_path, seed):
    on, result_on = nfl_game(tmp_path / "on", seed, True)
    off, result_off = nfl_game(tmp_path / "off", seed, False)
    assert on.rnd.trace == off.rnd.trace and result_on.scores == result_off.scores
    lines = crew_lines(on)
    count = Counter(pool for pool, _role, _text in lines)
    assert count["SGN"] == count["SGO"] == 1 and lines[-1][0] == "SGO"
    assert count["CLK"] >= 2 and count["QUP"] == 3 and count["STA"] >= 2
    for pool, _role, text in lines:
        if pool == "CLK":
            assert re.search(r"\d+ (second|minute)", text)                       # the time left, said as a time
    texts = [text for _pool, _role, text in lines]
    assert all(texts[i] != texts[i - 1] for i in range(1, len(texts)))


def test_a_drive_that_scores_is_summed_up_now_and_then(tmp_path):
    drives = []
    for seed in (21, 22, 23, 24):
        rig, _result = nfl_game(tmp_path / str(seed), seed)
        drives += [text for pool, _role, text in crew_lines(rig) if pool == "DRV"]
    assert drives
    for text in drives:
        numbers = [int(n) for n in re.findall(r"\d+", text)]
        assert len(numbers) in (2, 3) and all(n >= BC.DRIVE_MIN for n in numbers)     # plays, yards (and minutes), never "1 minutes"


def test_f8_silences_the_whole_crew(tmp_path):
    rules = RecordingRules(penalties_on=True, qb_on=True, playbooks_on=True, broadcast_on=True)
    rig = make_rig(tmp_path, rng=random.Random(41), fast=True, vtrnt=2, gtp=1)
    rig.game.comtog_source = lambda: 1
    from nflrig import QUARTERBACKS, SimEngine
    engine = SimEngine(rig.game, rules, quarterback_names=lambda state: QUARTERBACKS, own_names=None, opponent_names=None)
    rig.game.play_engine = engine
    try:
        engine.run()
    finally:
        rig.game.play_engine = None
    assert crew_lines(rig) == []


def test_broadcast_off_keeps_the_announcers_format_without_the_analyst_and_the_reporter(tmp_path):
    rig, _result = nfl_game(tmp_path, 22, on=False)
    lines = crew_lines(rig)
    pools = Counter(pool for pool, _role, _text in lines)
    assert pools["SGN"] == pools["SGO"] == 1 and pools["QUP"] == 3 and pools["STA"] >= 2
    assert not any(role in (COLOR, SIDELINE) for _pool, role, _text in lines)
    assert not any(pool in ("CRW", "ASK", "ASN", "HINT") for pool, _role, _text in lines)
    assert not any("Gus Delgado" in text or "Nora Banks" in text for _pool, _role, text in lines)   # STA06, NID04, SGO01 are left out


# ----- the reporter at an injury -----

def test_the_reporter_reports_a_hurt_player_at_the_next_dead_ball(tmp_path):
    rules = NflRules(broadcast_on=True)
    rig = nfl_engine_rig(tmp_path, rules=rules, comments=True)
    rig.rnd.source = random.Random(5)
    state = rig.engine.s
    b = rules.broadcast
    b.attach(rig.game, state)
    injuries = SimpleNamespace(record={"hurt": [[7, "knee", 2, 0]]}, league=SimpleNamespace(players={7: SimpleNamespace(name="Lou Park", team=12)}),
                               teams=(12, 30))
    rules._report_injuries(state, injuries, 0)
    assert b.hurt == ("Lou Park", 1)
    b.plays += 1
    b.between(state)
    said = [(role, text) for text, role, _s in rig.said]
    pools = [pool_of(text) for _role, text in said]
    assert pools[:2] == ["ASN", "SIN"] and said[1][0] == SIDELINE and "Lou Park" in said[1][1] and "Bengals" in said[1][1]
    assert b.hurt is None
    b.analyst = False                                                            # Broadcast off: no report
    b.injury(state, "Lou Park", 1)
    assert b.hurt is None


def test_no_injury_line_gives_the_player_a_pronoun():
    for remark in RM.DEFAULT_POOLS.lines("SIN"):
        text = " " + X.TEXTS[remark.id].lower() + " "
        assert not any(word in text for word in (" he ", " his ", " him ", " she ", " her ")), remark.id


# ----- the pools -----

def test_a_pool_gives_no_line_twice_in_a_game_while_it_has_others(tmp_path):
    rules = NflRules(broadcast_on=True)
    rig = nfl_engine_rig(tmp_path, rules=rules, comments=True)
    b = rules.broadcast
    b.attach(rig.game, rig.engine.s)
    said = [b._line(rig.engine.s, "NID", {}, rig.game.say5).id for _ in range(6)]
    assert sorted(said) == ["NID%02d" % n for n in range(1, 7)]
    assert b._line(rig.engine.s, "NID", {}, rig.game.say5) is not None           # then the pool starts again


def test_every_pool_of_the_format_has_its_speaker_and_its_placeholders():
    for pool in FORMAT_POOLS:
        speaker = "sideline" if pool in RM.SIDELINE_POOLS else "say"
        for remark in RM.DEFAULT_POOLS.lines(pool):
            assert X.SPEAKERS[remark.id] == speaker
            assert all(p in RM.PLACEHOLDERS[pool] for p in re.findall(r"<[^<>]+>", X.TEXTS[remark.id])), remark.id
    assert set(FORMAT_POOLS) <= set(RM.COMMENTARY_POOLS)                         # F8 silences them


def test_the_time_is_said_in_words_a_voice_reads_well():
    assert BC.time_words(70) == "1 minute and 10 seconds" and BC.time_words(120) == "2 minutes" and BC.time_words(45) == "45 seconds"
    assert BC.time_words(1) == "1 second" and BC.time_words(61) == "1 minute and 1 second"


# ----- the names -----

NAMES = {"announcer": "Ann Lee", "analyst": "Bo Rivers", "sideline": "Cal Moss", "network": "Radio Nine"}


def test_the_players_names_are_heard_and_the_defaults_are_not(tmp_path):
    rig, _result = classic_game(tmp_path, ClassicRadioRules(broadcast_on=True, crew_names=NAMES))
    texts = [text for _pool, _role, text in crew_lines(rig)]
    joined = " ".join(texts)
    assert all(name in joined for name in NAMES.values())
    assert not any(name in joined for name in crew.DEFAULTS.values())


def test_the_programs_rules_carry_the_names_in_both_modes():
    settings = Settings.defaults()
    for role, name in NAMES.items():
        setattr(settings.game, "nx_" + role, name)
    assert rules_from_settings(settings.game).broadcast.names == NAMES
    settings.game.rules = "classic"
    classic = rules_from_settings(settings.game)
    assert isinstance(classic, ClassicRadioRules) and classic.broadcast.names == NAMES and classic.for_game().broadcast.names == NAMES


def test_a_typed_name_is_remembered_when_the_player_goes_back_to_the_default():
    settings = Settings.defaults().game
    assert crew.choose(settings, crew.SIDELINE, "Kay Dunn", typed=True) is True
    assert crew.choose(settings, crew.SIDELINE, crew.DEFAULTS[crew.SIDELINE]) is True
    assert crew.choices(settings, crew.SIDELINE) == [("default", "Nora Banks"), ("own", "Kay Dunn"), ("type", "")]
    assert crew.step(settings, crew.SIDELINE, 1) is True and crew.name_of(settings, crew.SIDELINE) == "Kay Dunn"


# ----- remarks.txt in Classic -----

def test_remarks_txt_is_read_in_classic_and_a_players_own_sign_on_is_said(tmp_path):
    custom = Customization(str(tmp_path / "customize"), extras=False)
    assert custom.snapshot.remarks is not None and any(spec.file_name == "remarks.txt" for spec in custom.specs)
    path = tmp_path / "customize" / "remarks.txt"
    lines = [line for line in path.read_bytes().decode("utf-8").split("\r\n") if not line.startswith("SGN0")]
    lines += ["SGN01 = off", "SGN02 = off", "SGN03 = off", "SGN04 = off", "SGN05 = My own welcome to <network>.", ""]
    path.write_bytes("\r\n".join(lines).encode("utf-8"))
    custom.reload()
    pools = custom.snapshot.remarks
    assert [r.id for r in pools.lines("SGN")] == ["SGN05"] and custom.snapshot.problem_count("remarks") == 0
    rig, _result = classic_game(tmp_path / "game", ClassicRadioRules(broadcast_on=True), pools=pools)
    spoken = [text.strip() for text, _role, _step in rig.said]
    first_crew = spoken.index(crew_lines(rig)[0][2].strip())                    # CRW: the crew follows the sign-on
    assert "My own welcome to the Gridiron Radio Network." in spoken[:first_crew]
    custom.use_extras(True)
    custom.use_extras(False)
    assert custom.snapshot.remarks is not None and [r.id for r in custom.snapshot.remarks.lines("SGN")] == ["SGN05"]


# ----- F11, F12 and the help -----

F11, ENTER = 122, 13


def f11_roles(tmp_path, rules, broadcast_on=True, comments_off=False):
    from nfl4.game.options import Options
    rig = Rig([F11] + [ENTER] * 12, sounds_dir=tmp_path)
    settings = Settings.defaults()
    settings.audio = rig.sounds.settings
    settings.game.nx_broadcast = broadcast_on
    rig.game.options = Options(settings, rig.speech, save=lambda: True, base_rate=lambda: 0)
    rig.game.rules = rules
    if comments_off:
        rig.game.comtog_source = lambda: 1
    rig.keys.getkey(rig.speech)
    asked = [role for text, role, step in rig.said if "volume" in text.lower() and role in ALL_ROLES]
    return list(dict.fromkeys(asked))           # each speaker once, in the order F11 asks (the sound volume's prompt is the announcer's again)


def test_f11_asks_for_the_analyst_and_the_reporter_in_both_modes_and_the_referee_with_the_nfl_rules(tmp_path):
    classic = f11_roles(tmp_path / "a", classic_rules(Settings.defaults().game))
    assert classic[-2:] == [COLOR, SIDELINE] and REFEREE not in classic
    nfl = f11_roles(tmp_path / "b", NflRules())
    assert nfl[-3:] == [COLOR, SIDELINE, REFEREE]
    assert SIDELINE not in f11_roles(tmp_path / "c", classic_rules(Settings.defaults().game), comments_off=True)
    assert SIDELINE not in f11_roles(tmp_path / "d", classic_rules(Settings.defaults().game), broadcast_on=False)
    assert not set(f11_roles(tmp_path / "e", CLASSIC)) & {COLOR, SIDELINE, REFEREE}     # the engine's bare Classic: the original's five


def test_the_keys_and_the_help_name_the_crew_in_both_modes():
    rows = {row.id: row for row in key_list.ROWS}
    assert "sideline reporter" in rows["f11"].what and "sideline reporter" in rows["f12"].what and "radio crew" in rows["f8"].what
    readme = (Path(__file__).resolve().parents[1] / "README_keys.md").read_text(encoding="utf-8")
    assert "sideline reporter" in readme
    help6 = ClassicRadioRules().extra_help("117")
    assert help6[-5:] == [X.text("NXH-65"), X.text("NXH-66"), X.text("NXH-83"), X.text("NXH-84"), X.text("NXH-70")]     # S-D: NXH-83, how much the crew talks; RC: NXH-84, the play calls
    assert "Broadcast crew" in X.text("NXH-70") and "Walt Kessler" in X.text("NXH-70")
