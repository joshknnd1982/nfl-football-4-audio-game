"""The six season files: footbal1.dat to footbal5.dat and football.gtp (data/files). This is inspired by Jim Kitchen.

GAME_SPEC 12: the layouts, the Variant types the original writes (Integer for the six division games of footbal2.dat, Single for
the ten others, a Long for the length of the coach's name) and what each reader may accept. Each file's decode raises
FileDamaged for anything the game cannot use, and nothing else.
"""
import random
import struct

import pytest

from nfl4.data.files import byesfile, coachteam, pairingsfile, recordsfile, schedulefile, variant, weekfile
from nfl4.game.playoffs import TeamRef
from nfl4.game.rnd import GameRandom
from nfl4.game.schedule import ScheduleEntry, make_schedule
from nfl4.game.standings import Records
from seasonrig import BASE_BYES, BASE_PAIRINGS

Damaged = variant.FileDamaged


def a_schedule(seed=5, team=(3, 2)):
    return make_schedule(GameRandom(random.Random(seed)), *team)


# ----- footbal1.dat -----

def test_footbal1_holds_the_team_the_coach_length_as_a_long_and_one_code_per_letter():
    raw = coachteam.encode(6, 3, "Kim Lee")
    assert raw == (struct.pack("<Hh", 2, 6) + struct.pack("<Hh", 2, 3) + struct.pack("<Hi", 3, 7)
                   + b"".join(struct.pack("<Hh", 2, ord(c)) for c in "Kim Lee"))
    assert coachteam.decode(raw) == coachteam.CoachTeam(6, 3, "Kim Lee")


@pytest.mark.parametrize("raw", [
    b"", variant.pack_integer(3),                                                        # empty, cut short
    variant.pack_integer(0), variant.pack_integer(0) + b"junk after it", bytes(40),      # a first value of 0, a zeroed file
    coachteam.encode(9, 1, "Kim"), coachteam.encode(1, 5, "Kim"), coachteam.encode(-1, 1, "Kim"),    # no such team
    variant.pack_integer(1) + variant.pack_integer(1) + variant.pack_long(0),            # no coach name
    variant.pack_integer(1) + variant.pack_integer(1) + variant.pack_long(500),          # an absurd length
    variant.pack_integer(1) + variant.pack_integer(1) + variant.pack_long(3) + variant.pack_integer(65),   # name cut short
    variant.pack_integer(1) + variant.pack_integer(1) + variant.pack_long(1) + variant.pack_integer(7),    # a control code
    variant.pack_integer(1) + variant.pack_integer(1) + variant.pack_long(1) + variant.pack_integer(300),  # above 255
    variant.pack_integer(1) + variant.pack_single(1.5),                                  # a fraction as a team
])
def test_footbal1_that_cannot_be_used_is_damaged(raw):
    with pytest.raises(Damaged):
        coachteam.decode(raw)


def test_a_coach_name_with_letters_above_127_survives_as_latin_1():
    assert coachteam.decode(coachteam.encode(1, 1, "Zoë")).coach == "Zoë"
    assert coachteam.decode(coachteam.encode(1, 1, "x" * 150)).coach == "x" * 100      # at most 100 characters are kept


# ----- footbal2.dat -----

def test_footbal2_is_16_records_integers_for_the_division_games_and_singles_for_the_rest():
    schedule = a_schedule()
    raw = schedulefile.encode(schedule)
    division_games = sum(1 for entry in schedule if entry.division == 3)
    assert division_games == 6
    assert len(raw) == 6 * 12 + 10 * 18                              # 12 bytes a division record, 18 for the others
    assert schedulefile.decode(raw) == schedule


def test_the_division_is_found_from_the_schedule_or_given():
    schedule = a_schedule(seed=9, team=(7, 4))
    assert schedulefile.own_division_of(schedule) == 7
    assert schedulefile.encode(schedule) == schedulefile.encode(schedule, own_division=7)
    assert len(schedulefile.encode(schedule, own_division=None)) == 6 * 12 + 10 * 18


def test_a_schedule_of_all_integers_or_all_singles_reads_the_same():
    schedule = a_schedule()
    all_integers = b"".join(variant.pack_integer(x) for e in schedule for x in (e.division, e.team, e.flag))
    all_singles = b"".join(variant.pack_single(x) for e in schedule for x in (e.division, e.team, e.flag))
    assert schedulefile.decode(all_integers) == schedule == schedulefile.decode(all_singles)


def test_footbal2_with_15_or_17_weeks_or_a_bad_value_is_damaged():
    schedule = a_schedule()
    good = schedulefile.encode(schedule)
    with pytest.raises(Damaged):
        schedulefile.decode(schedulefile.encode(schedule[:15]))
    with pytest.raises(Damaged):
        schedulefile.decode(good + variant.pack_integer(1))
    with pytest.raises(Damaged):
        schedulefile.decode(good[:-3])
    for bad in (ScheduleEntry(9, 1, 1), ScheduleEntry(1, 5, 1), ScheduleEntry(1, 1, 3), ScheduleEntry(0, 1, 1)):
        with pytest.raises(Damaged):
            schedulefile.decode(schedulefile.encode([bad] + schedule[1:]))


# ----- football.gtp -----

def test_football_gtp_is_one_integer_for_the_week_0_to_20():
    for gtp in range(0, 21):
        assert weekfile.decode(weekfile.encode(gtp)) == gtp
    assert weekfile.encode(7) == struct.pack("<Hh", 2, 7)
    assert weekfile.decode(variant.pack_single(12.0)) == 12 and weekfile.decode(variant.pack_long(3)) == 3
    assert weekfile.decode(weekfile.encode(5) + b"anything after the first value") == 5


@pytest.mark.parametrize("raw", [b"", b"\x02", variant.pack_integer(-1), variant.pack_integer(21), variant.pack_single(2.5),
                                 bytes(4), bytes(2)])
def test_football_gtp_that_cannot_be_used_is_damaged(raw):
    with pytest.raises(Damaged):
        weekfile.decode(raw)


# ----- footbal3.dat -----

def a_records():
    records = Records()
    for d in range(8):
        for p in range(4):
            records.wins[d][p], records.losses[d][p] = (d * 2 + p) % 17, 16 - (d * 2 + p) % 17
    return records


def test_footbal3_is_64_integers_wins_then_losses_division_by_division():
    records = a_records()
    raw = recordsfile.encode(records)
    assert len(raw) == 256 and raw[:8] == variant.pack_integer(0) + variant.pack_integer(16)
    assert raw[8:12] == variant.pack_integer(1) and recordsfile.decode(raw).as_file_values() == records.as_file_values()


@pytest.mark.parametrize("raw", [b"", recordsfile.encode(Records())[:-4], recordsfile.encode(Records()) + variant.pack_integer(0),
                                 variant.pack_integer(-1) * 64, variant.pack_integer(100) * 64])
def test_footbal3_that_cannot_be_used_is_damaged(raw):
    with pytest.raises(Damaged):
        recordsfile.decode(raw)


# ----- footbal4.dat and footbal5.dat -----

def test_footbal4_holds_four_integers_a_game_visitor_first():
    raw = pairingsfile.encode(BASE_PAIRINGS)
    assert len(raw) == 4 * 4 * 4
    assert raw[:16] == b"".join(variant.pack_integer(x) for x in (3, 1, 4, 1))
    assert pairingsfile.decode(raw) == BASE_PAIRINGS
    assert pairingsfile.decode(b"") == []                          # the original deletes it first: an empty file is no games


@pytest.mark.parametrize("raw", [variant.pack_integer(1) * 6, variant.pack_integer(1) * 3,
                                 variant.pack_integer(9) * 4, variant.pack_integer(0) * 4,
                                 pairingsfile.encode(BASE_PAIRINGS)[:-2]])
def test_footbal4_that_cannot_be_used_is_damaged(raw):
    with pytest.raises(Damaged):
        pairingsfile.decode(raw)


def test_the_games_a_round_has_by_the_week():
    assert pairingsfile.GAMES_AFTER_WEEK == {17: 4, 18: 4, 19: 2, 20: 1}


def test_footbal5_holds_the_four_bye_teams_as_pairs():
    raw = byesfile.encode(BASE_BYES)
    assert len(raw) == 4 * 2 * 4 and byesfile.decode(raw) == BASE_BYES
    singles = b"".join(variant.pack_single(x) for x in (1, 2, 3, 3, 5, 1, 7, 1))
    assert byesfile.decode(singles) == [TeamRef(1, 2), TeamRef(3, 3), TeamRef(5, 1), TeamRef(7, 1)]


@pytest.mark.parametrize("raw", [b"", variant.pack_integer(1) * 6, variant.pack_integer(1) * 10, variant.pack_integer(9) * 8,
                                 variant.pack_integer(1) * 7])
def test_footbal5_that_cannot_be_used_is_damaged(raw):
    with pytest.raises(Damaged):
        byesfile.decode(raw)


def test_random_bytes_in_every_file_give_damaged_or_a_value_never_another_error():
    rng = random.Random(11)
    decoders = [coachteam.decode, schedulefile.decode, weekfile.decode, recordsfile.decode, pairingsfile.decode,
                byesfile.decode]
    for _ in range(600):
        junk = bytes(rng.randrange(256) for _ in range(rng.randrange(0, 60)))
        for decode in decoders:
            try:
                decode(junk)
            except Damaged:
                pass
