"""The snap's draws of the N. F. L. rules for the scripted-draw tests (NX-D2, D-147): the ball carrier and the two tacklers are one below(100) each over
the usage shares (extras/tuning.py USAGE_RUN, USAGE_PASS, USAGE_TACKLE), where the original drew rnd(6) and rnd(17). A test that was written for the
old draws names the old rnd(6) value; it is read through D-135's depth slots (1, 1, 2, 2, 3, 4) to the place the test expected, and the draw is scripted
at the first value of that place's band."""
from nfl4.extras import tuning as T

OLD_SLOTS = (1, 1, 2, 2, 3, 4)          # D-135's place for each value of the old rnd(6) (the N. F. L. rules outside a franchise)


def carrier_value(place: int, kind: str = "run") -> int:
    shares = T.USAGE_PASS if kind == "pass" else T.USAGE_RUN
    return sum(shares[:place - 1])


def tackle_value(place: int) -> int:
    return sum(T.USAGE_TACKLE[:place - 1])


def nfl_snap_draws(d, carrier=1, d1=1, d2=2, phrase=1, kind="run"):
    """The N. F. L. rules' L_440e54 (carrier, two defenders) and the snap phrase, then its rady; `carrier` is the old rnd(6) value."""
    return (d.below(100, carrier_value(OLD_SLOTS[carrier - 1], kind)).below(100, tackle_value(d1)).below(100, tackle_value(d2))
            .rnd(13, phrase).rady())
