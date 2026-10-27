"""BC.2 (D-178, D-180; CLAUDE.md 0.27 as amended): the original's commentary is gone from every mode. This is inspired by Jim Kitchen.

The owner (2026-10-26): "You need to forget and get rid of all of Jim Kitchen's commentary and commenting code for Gip and other
commenters", and, asked about Classic, "Every mode". spec/NFL_BROADCAST_DESIGN.md sections 2, 8 and 9. What is checked here:

* no text of the game (any string in the program, the generated texts, the default pools) is one of the original's 142 banter lines,
  names Ghip or one of the 28 real podcasters' names D-106 offered; the modules of the original's banter step are gone;
* the original's one draw that came with comments off too, Int(Rnd * 4) + 1 after a play that ends in the field of play, is kept with
  nothing said on it, so seeded whole games with comments off make exactly the draws they made before BC.2 (the digests below were
  recorded by work/bc2_1027/draw_fingerprint.py on the tree of commit 1f796c3, before any change);
* banter.txt is no longer read, made, checked or reset, and a player's old file stays as it was;
* an automatic save written before BC.2 (with the fields banter_names and banter_used) is still used whole;
* Ghip and the retired names in an older settings.txt read as the made-up default, Gus Delgado.
"""
import ast
import hashlib
import importlib.util
import json
import random
from pathlib import Path

import pytest

from nfl4.extras import commentators, nx_texts
from nfl4.game import resume
from nflrig import QUARTERBACKS, RecordingRules, SimEngine
from pagrig import Draws, engine_rig, make_rig, play, run_steps, texts
from test_pag_games import lively_policy

SRC = Path(__file__).resolve().parent.parent / "src" / "nfl4"

# Words and phrases that only the original's 142 banter lines have (each line has at least one of them or names Ghip; a test of S3.5 checked
# the lines against the exe, spec/STRINGS.md keeps them). Lower case.
ORIGINAL_FRAGMENTS = ("ghip", "cheerleader", "wood chuck", "peter piper", "red leather yellow leather", "dog bone", "hotdog", "rhetorical",
                      "dog pound", "bobble head", "cha ching", "felder carb", "shazzam", "zea ow e", "masscot", "staile", "take my wife",
                      "price of rice", "wifes brother", "fifty bucks", "drug test", "thong", "soft tail", "suffering succotash",
                      "holy doughnuts", "butterscotch", "bummer dude", "ping my twitter", "o m g ghip", "whos on first")
# The files where an old text is kept on purpose to be RECOGNIZED, never said: the retired default remarks (B-P196), the remarks of
# 0.10.0 that said Ghip (legacy_markup reads them as the defaults), and the digests of the retired names.
RECOGNIZERS = {"remarks_retired.py", "commentators.py"}


def program_strings():
    """Every string literal of the program, with its file, except the recognizers' and remarks.py's LEGACY_MARKUP and legacy_markup."""
    for path in SRC.rglob("*.py"):
        if path.name in RECOGNIZERS:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        skipped = set()
        for node in ast.walk(tree):                     # docstrings explain the code and are never said
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and ast.get_docstring(node, clean=False):
                skipped.add(id(node.body[0].value))
        if path.name == "remarks.py":
            for node in ast.walk(tree):
                if isinstance(node, (ast.Assign, ast.AnnAssign)) and "LEGACY_MARKUP" in ast.unparse(node.targets[0] if isinstance(node, ast.Assign) else node.target):
                    skipped |= {id(n) for n in ast.walk(node)}
                if isinstance(node, ast.FunctionDef) and node.name == "legacy_markup":
                    skipped |= {id(n) for n in ast.walk(node)}
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in skipped:
                yield path.name, node.value


def word_runs(text, longest=3):
    words = "".join(c if c.isalnum() or c in " '.-" else " " for c in text).split()
    for size in range(1, longest + 1):
        for start in range(len(words) - size + 1):
            yield " ".join(words[start:start + size])


def test_no_text_of_the_game_says_an_original_banter_line_ghip_or_a_retired_name():
    found = []
    every = list(program_strings()) + [("nx_texts.TEXTS", text) for text in nx_texts.TEXTS.values()]
    for where, text in every:
        lower = " ".join(text.lower().split())
        for fragment in ORIGINAL_FRAGMENTS:
            if fragment in lower:
                found.append((where, fragment, text[:80]))
        for run in word_runs(text):
            if commentators.is_retired(run):
                found.append((where, "a retired name", text[:80]))
    assert found == []
    for module in ("nfl4.game.banter", "nfl4.game.banter_lines", "nfl4.game.banter_pool"):
        assert importlib.util.find_spec(module) is None, module
    assert len(commentators.RETIRED_DIGESTS) == 29 and commentators.DEFAULT == "Gus Delgado"


# ----- the draws -----

BEFORE = {                     # work/bc2_1027/fingerprint_before.json (commit 1f796c3): draws, SHA-256 of the sizes, the score
    "classic_2034": (4327, "c0cc2bb1c1d5c64e0f1f448d85a0ab556108ced82b7cd620ca83b8495dee4d11", "(28, 39)"),
    "classic_77": (4373, "fa354a9c15099907ad75145c4d92fe35aaf570cfa1c47a13ceaf68037ec2788a", "(3, 47)"),
    "nfl_2034": (5896, "bdd82dcdb8f755ce50c7b307f21d3659a37b5a487bb9ac4f610e0cbf66456f73", "(21, 27)"),
    "nfl_11": (5734, "cd56a5002e8697349306085e4c3c093c9a6fcc7707391e8ebee60f38809acbeb", "(27, 26)"),
}
PLAYER_SEEDS = {2034: 3034, 77: 78}


def digest(trace):
    return hashlib.sha256(",".join(str(n) for n in trace).encode()).hexdigest()


@pytest.mark.parametrize("case", sorted(BEFORE))
def test_comments_off_seeded_games_make_exactly_the_draws_they_made_before(tmp_path, case):
    kind, seed = case.split("_")
    seed = int(seed)
    if kind == "classic":
        rig = make_rig(tmp_path, rng=random.Random(seed), vtrnt=2)
        rig.keys.policy = lively_policy(rig, PLAYER_SEEDS[seed])
        rig.game.comtog_source = lambda: 1
        rig.rnd.trace = []
        result = play(rig)
    else:
        rig = make_rig(tmp_path, rng=random.Random(seed), fast=True, vtrnt=2, gtp=1)
        rig.game.comtog_source = lambda: 1
        rig.rnd.trace = []
        rules = RecordingRules(penalties_on=True, onside_on=True, qb_on=True, challenges_on=True, playbooks_on=True,
                               broadcast_on=True, stadium_on=True)
        engine = SimEngine(rig.game, rules, quarterback_names=lambda state: QUARTERBACKS)
        rig.game.play_engine = engine
        try:
            result = engine.run()
        finally:
            rig.game.play_engine = None
    assert (len(rig.rnd.trace), digest(rig.rnd.trace), repr(result.scores)) == BEFORE[case]


@pytest.mark.parametrize("comments", [False, True])
def test_the_per_play_draw_is_kept_and_says_nothing(tmp_path, comments):
    """L_4510b6: Int(Rnd * 4) + 1 is drawn after a play that ends in the field of play, and with comments on a 2 (the original's
    banter) says nothing more than the position: no line, no name draw, no pause draw."""
    rig = engine_rig(tmp_path, comments=comments, wisoff=1, yard_line=30, down=2, to_go=7)
    step = run_steps(rig, rig.engine.banter_position, Draws().rnd(4, 2), until=("down_sentence",))
    assert step == "down_sentence"
    said = texts(rig)
    assert len(said) == 1 and "ball on" in said[0]


def test_an_old_banter_txt_is_left_untouched_and_not_read(tmp_path):
    from nfl4.data.customize import Customization
    folder = tmp_path / "customize"
    folder.mkdir()
    old = b"# NFL Football 4 banter, format 1.\nB001 = My own line\nB143 = [sound mine.wav]\n"
    (folder / "banter.txt").write_bytes(old)
    custom = Customization(str(folder))
    assert (folder / "banter.txt").read_bytes() == old
    assert all(spec.file_name != "banter.txt" for spec in custom.specs)
    assert "banter" not in custom.check().lower()
    custom.reload()
    assert (folder / "banter.txt").read_bytes() == old and not list(folder.glob("banter.txt.*"))


def test_an_old_resume_with_banter_fields_is_used_whole(tmp_path):
    rig = make_rig(tmp_path / "a", rng=random.Random(4), fast=True, vtrnt=2)
    engine = SimEngine(rig.game, RecordingRules(), quarterback_names=lambda state: QUARTERBACKS)
    engine.s.player_names = ["Name%d" % n for n in range(58)]
    data = json.loads(resume.capture(engine))
    data["state"]["banter_names"] = data["state"].pop("player_names")          # what 0.16.7 and older wrote
    data["state"]["banter_used"] = [3, 17]
    rig2 = make_rig(tmp_path / "b", rng=random.Random(9), fast=True, vtrnt=2)
    engine2 = SimEngine(rig2.game, RecordingRules(), quarterback_names=lambda state: QUARTERBACKS)
    assert resume.restore(engine2, json.dumps(data)) is True
    assert engine2.s.player_names == ["Name%d" % n for n in range(58)] and not hasattr(engine2.s, "banter_used")


@pytest.mark.parametrize("stored", ["Ghip", "ghip", "  GHIP ", "Pat McAfee", "pat  mcafee", "Rich Eisen"])
def test_a_retired_commentator_name_reads_as_the_default(stored):
    from nfl4.data import settingsfile
    assert commentators.name_of_text(stored) == "Gus Delgado"
    from nfl4.extras import crew
    settings, _problems = settingsfile.parse("nx_commentator = %s\n" % stored)       # a settings file of 0.16.7 or older (BC.3 reads it once)
    assert settings.game.nx_analyst == "Gus Delgado" and settings.game.nx_analyst_own == "" and commentators.name_of(settings.game) == "Gus Delgado"
    assert all(not commentators.is_retired(name) for _kind, name in crew.choices(settings.game, crew.ANALYST))
    for role in crew.ROLES:                                                          # BC.3: no name of the crew can be a retired one
        assert crew.name_of_text(role, stored) == crew.DEFAULTS[role]
        typed, _problems = settingsfile.parse("nx_%s = %s\nnx_%s_own = %s\n" % (role, stored, role, stored))
        assert crew.name_of(typed.game, role) == crew.DEFAULTS[role] and crew.own_of(typed.game, role) == ""
    assert commentators.name_of_text("Sam Rivera") == "Sam Rivera"
