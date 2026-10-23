"""A review that changes the ruling of a play whose flag was declined offers the flag again (nfl4 only, rule 0.13; NFL_EXTRAS_DESIGN
6.4, 9; NFL_RULES_RESEARCH Part 3 section 5 and 15-7-3 Item 3: "the head coach may change an accept or decline decision made before
the review"; NX2's N2.7; PX SX.6). This is inspired by Jim Kitchen.

A play on which a penalty took over (accepted, offset, enforced on the try) is not ruled. Every draw is planned on a strict
scripted source and every number worked out from the rule next to it (B-X38): the horse collar tackle is 15 yards from the dead ball
spot with an automatic first down (fouls_2026 P20, 12-2-8), the run of 4 from the 30 ends on the 34, the corrected run of 5 on the 35.
"""
from nfl4.extras import nx_texts as X
from nfl4.extras import tuning as T
from nfl4.extras.nfl_rules import NflRules
from nfl4.game import outcome as O
from nflrig import RecordingRules, nfl_engine_rig, sim_game
from pagrig import Draws, run_steps
from test_nx_penalties import rows, value_of

ENTER = 13
HORSE_COLLAR = " horse collar tackle, on the Jets, ODef4. "
FLAG = X.text("NXP-01")


def scene(tmp_path, answers, **extras):
    """Third and 5 from the 30, second quarter with 100 seconds left after the warning (a play of the replay official's): a run of
    4 ends on the 34 and is ruled short of the line (fourth and 1). The Jets are flagged for a horse collar tackle (the draws
    are the caller's). The penalty flow took its snapshot at the snap, before the ball moved."""
    rules = NflRules(timeouts_on=False, penalties_on=True, challenges_on=True)
    fields = {"left": 100, "warning_given": True, "period": 2}
    fields.update(extras)
    rig = nfl_engine_rig(tmp_path, answers=answers, rules=rules, wisoff=1, defense=2, half=2, yard_line=30, down=3, to_go=5,
                         quarter=2, offense_play=1, defense_play=3, extras=fields)
    rig.engine._spot_before = (2, 30)
    s = rig.engine.s
    rules.penalty.take_snap(s)                                   # at the snap
    s.yard_line, s.yards, s.result_kind, s.play_kind, s.tackle_sentence = 34, 4, O.RUN, 1, " tackle "
    s.stats[1].running_plays, s.stats[1].running_yards = 1, 4
    return rig


def collar(rig) -> Draws:
    """The end of the play: the foul (P20 among the rows of a run), the Jets' player Def4, no second foul, L = 4 seconds."""
    value = value_of(rig, rows(rig, O.RUN), "P20", offense_play=1, defense_play=3)
    return Draws().below(10000, value).rnd(17, 4).rnd(T.SECOND_FOUL_CHANCE, 2).below(4, 0)


def ruled_wrong(d: Draws) -> Draws:
    """The line to gain window of a booth play is 0 to 59: 10 is wrong, clear (0 is below 85), no hint, the two pauses."""
    return d.below(1000, 10).below(100, 0).below(100, 99).rady().rady()


def texts(rig):
    return [t for t, _, _ in rig.said]


GAIN_4 = " There is a gain of 4 yards on the play"
FIRST_PROMPT = [FLAG, HORSE_COLLAR,
                " Kim if you accept the penalty, it will be first and 10 on your 49 yard line. ",
                " if you decline it, it will be fourth and 1 on your 34 yard line. ", " accept ", " decline "]
DECLINED_FIRST = X.text("NXP-25", situation="it will be fourth and 1 on your 34 yard line")        # the referee (2026-10-23)
REVIEW = [DECLINED_FIRST, X.text("NXR-08"), X.text("NXR-04"), X.text("NXR-05"), " the runner made the first down. "]
SECOND_PROMPT = [" There is a gain of 5 yards on the play", FLAG, HORSE_COLLAR,
                 " Kim if you accept the penalty, it will be first and 10 on the 50 yard line. ",
                 " if you decline it, it will be first and 10 on your 35 yard line. ", " accept "]


def test_the_player_declines_a_flag_the_review_changes_the_ruling_and_the_flag_is_offered_again_and_accepted(tmp_path):
    """Declined at first: accepting would give first and 10 on the 49 (34 plus 15), declining fourth and 1 on the 34 (the run of
    4 ruled short). The replay official finds the first down (5 yards): now declining gives first and 10 on the 35, accepting
    first and 10 on the 50 (35 plus 15), and the player takes it. One flag, one accepted penalty, 15 yards."""
    rig = scene(tmp_path, ["d", ENTER, "a", ENTER])
    d = ruled_wrong(collar(rig)).below(4, 0)                        # the corrected play's live time; nothing after the choice
    assert run_steps(rig, rig.engine.gain_and_end, d) == "next_play"
    assert texts(rig) == ([GAIN_4] + FIRST_PROMPT + REVIEW + SECOND_PROMPT
                          + [" accept ", X.text("NXP-24", yards=15, situation="it will be first and 10 on the 50 yard line"),
                             X.text("NXP-09"), " it's your ball on the 50yard line",
                             " it's first down and 10yards to go"])
    s, x = rig.engine.s, rig.engine.s.extras
    assert (s.half, s.yard_line, s.down, s.to_go) == (2, 50, 1, 10)
    assert (x.flags, x.flag_yards) == ([0, 1], [0, 15])             # counted once, when it was accepted
    assert [e[1] for e in rig.rules.penalty.events] == ["declined", "accepted"]
    assert (s.stats[1].running_plays, s.stats[1].running_yards, s.stats[1].first_downs) == (1, 5, 1)
    assert x.left == 100 - 4                                          # the first live time was given back, the second charged
    assert [(o.kind, o.yards, o.then) for o in rig.engine.outcomes] == [(O.RUN, 4, "reviewed field play"), (O.RUN, 5, "next down")]


def test_the_flag_declined_twice_leaves_the_corrected_play_as_it_is(tmp_path):
    """Declined again: the corrected run of 5 is a first down on the 35. The banter draw 1 in 4 (1: none) comes at the position."""
    rig = scene(tmp_path, ["d", ENTER, "d", ENTER])
    d = ruled_wrong(collar(rig)).below(4, 0).rnd(4, 1)
    assert run_steps(rig, rig.engine.gain_and_end, d) == "next_play"
    assert texts(rig) == ([GAIN_4] + FIRST_PROMPT + REVIEW + SECOND_PROMPT
                          + [" decline ", X.text("NXP-25", situation="it will be first and 10 on your 35 yard line"),
                             " it's your ball on your 35yard line", " it's first down and 10yards to go"])
    s, x = rig.engine.s, rig.engine.s.extras
    assert (s.half, s.yard_line, s.down, s.to_go) == (2, 35, 1, 10)
    assert (x.flags, x.flag_yards) == ([0, 0], [0, 0])
    assert [e[1] for e in rig.rules.penalty.events] == ["declined", "declined"]


def test_a_flag_accepted_at_first_takes_the_play_over_and_the_play_is_not_ruled(tmp_path):
    """Accepted with Enter (the prompt starts at the better answer): the enforcement takes the play away, so there is no ruling,
    no draw of 1000, no review."""
    rig = scene(tmp_path, [ENTER])
    d = collar(rig)
    assert run_steps(rig, rig.engine.gain_and_end, d) == "next_play"
    assert texts(rig) == ([GAIN_4] + FIRST_PROMPT[:5]
                          + [X.text("NXP-24", yards=15, situation="it will be first and 10 on your 49 yard line"),
                             X.text("NXP-09"), " it's your ball on your 49yard line", " it's first down and 10yards to go"])
    assert rig.rules.review.rulings == [] and rig.rules.review.pending is None
    assert [e[1] for e in rig.rules.penalty.events] == ["accepted"] and rig.engine.s.extras.flags == [0, 1]


def test_a_ruling_that_stands_after_a_declined_flag_does_not_offer_the_flag_again(tmp_path):
    """The ruling is right but close (the wrong windows of a booth play are 60 for the line to gain and 4 for the tackle, so the
    close window of the line to gain starts at 64 and 70 is in it): the review confirms it, nothing changes, the flag is not asked
    again."""
    rig = scene(tmp_path, ["d", ENTER])
    d = collar(rig).below(1000, 70).below(100, 99).below(100, 5).rady().rady().rnd(4, 1)
    assert run_steps(rig, rig.engine.gain_and_end, d) == "next_play"
    said = texts(rig)
    assert said[:len(FIRST_PROMPT) + 1] == [GAIN_4] + FIRST_PROMPT
    assert said[len(FIRST_PROMPT) + 1:len(FIRST_PROMPT) + 4] == [DECLINED_FIRST, X.text("NXR-08"), X.text("NXR-04")]
    assert said.count(FLAG) == 1 and X.text("NXR-07") in said
    assert [e[1] for e in rig.rules.penalty.events] == ["declined"]


def test_the_extras_never_lose_a_flag_in_whole_games_and_a_play_a_foul_took_over_is_never_ruled(tmp_path_factory):
    """In 25 whole games with the fouls and the challenges on: whenever a play's decisions included anything but declining or not
    offering a flag, the play was not ruled; every ruling of a play with a flag was after a declined one."""
    class Watching(RecordingRules):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.log = []

        def after_outcome(self, state, outcome):
            marks, rulings = len(self.penalty.events), len(self.review.rulings)
            result = super().after_outcome(state, outcome)
            self.log.append(([e[1] for e in self.penalty.events[marks:]], len(self.review.rulings) - rulings, result.then))
            return result

    benign = ("declined", "not offered")
    taken_over = 0
    for seed in range(1, 26):
        rules = Watching(penalties_on=True, onside_on=True, qb_on=True, challenges_on=True)
        sim_game(tmp_path_factory.mktemp("w%d" % seed), seed, rules=rules)
        for decisions, ruled, then in rules.log:
            if any(d not in benign for d in decisions):
                taken_over += 1
                assert ruled == 0, (seed, decisions)
    assert taken_over >= 100                                            # about 12 accepted fouls a game: the property was tried
