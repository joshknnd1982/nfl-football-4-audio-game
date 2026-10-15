"""The number types of pag's draws and tests, against the automation library (fixesforgames B-P40, A43 item 3). This is inspired by Jim Kitchen.

Read in the asm (S7.3b): `Int(Rnd * 6) + 1` and every draw with a constant range multiply on the FPU (FMUL float, then
__vbaFPInt): Int of the exact product, which `GameRandom.below` gives for every 24-bit Rnd. A draw whose range is a
Variant stores Rnd as a Single Variant (FSTP dword, type 4) and calls __vbaVarMul and __vbaVarInt (the yards 0x44da18,
the return 0x445cf6, the interception 0x44bc75): the product is a Single first, `GameRandom.below_single`. The sack and
completion tests store Rnd * 100 with FSTP dword (0x44a399, 0x44b367) and compare that Single. Int(L64 / 2) is VarDiv
and VarInt of a Single by an Integer (0x43f10a). Each is compared here with oleaut32's own functions on Variants of the
types the original holds, for VB's Rnd values (multiples of 2^-24).
"""
import random

import pytest

import oleauto
from nfl4.game.rnd import GameRandom
from nfl4.game.vbnum import int_of, single

pytestmark = pytest.mark.skipif(not oleauto.available(), reason="the automation library is Windows only")


class Fixed:
    def __init__(self, x):
        self.x = x

    def random(self):
        return self.x


def vb_rnd_values(count=4000, seed=3):
    """VB's Rnd: k / 2^24; random ones plus the ones just below every bucket edge of n = 2 to 99 (where a Single
    rounding can reach the next integer)."""
    rng = random.Random(seed)
    values = {rng.randrange(1 << 24) / (1 << 24) for _ in range(count)}
    for n in range(2, 100):
        for k in range(1, n):
            edge = int(k * (1 << 24) / n)
            values.update((edge + d) / (1 << 24) for d in (-2, -1, 0, 1))
    return sorted(v for v in values if 0 <= v < 1)


def library_int_of_product(x, n):
    product = oleauto.op("Mul", oleauto.variant(oleauto.VT_R4, x), oleauto.variant(oleauto.VT_I2, n))
    vt, value = oleauto.read(oleauto.op("Int", product))
    assert vt == oleauto.VT_R4
    return int(value)


@pytest.mark.parametrize("n", [2, 3, 5, 6, 9, 10, 12, 15, 30, 35, 39, 41, 67, 87, 89, 90])
def test_below_single_is_varint_of_varmul_of_a_single_by_an_integer(n):
    for x in vb_rnd_values(600):
        assert GameRandom(Fixed(x)).below_single(n) == min(library_int_of_product(x, n), n - 1), (x, n)


def test_a_single_rounding_does_change_some_draws_so_the_type_matters():
    changed = [(x, n) for n in range(2, 100) for x in vb_rnd_values(0)
               if GameRandom(Fixed(x)).below(n) != GameRandom(Fixed(x)).below_single(n)]
    assert changed                                                     # at a few bucket edges, as the library does


def test_the_fpu_draws_are_int_of_the_exact_product_for_every_24_bit_rnd():
    for x in vb_rnd_values(2000):
        for n in (2, 3, 4, 6, 7, 8, 9, 10, 13, 17, 28, 30, 35, 40, 50, 58, 70, 142, 1708):
            exact = (int(x * (1 << 24)) * n) >> 24                     # integer arithmetic: no rounding at all
            assert GameRandom(Fixed(x)).below(n) == exact


@pytest.mark.parametrize("threshold", [5, 10, 15, 20, 25, 30, 40, 50, 60, 70, 90])
def test_the_percent_tests_compare_a_single_as_fstp_dword_stores_it(threshold):
    import struct
    for x in vb_rnd_values(1500) + [threshold / 100, threshold / 100 + 2 ** -26, threshold / 100 - 2 ** -26]:
        stored = struct.unpack("<f", struct.pack("<f", x * 100))[0]   # FMUL then FSTP float
        assert (single(x * 100) <= threshold) == (stored <= threshold)


def test_int_of_l64_over_2_is_exact_in_the_library():
    for x in range(2, 11):
        quotient = oleauto.op("Div", oleauto.variant(oleauto.VT_R4, x), oleauto.variant(oleauto.VT_I2, 2))
        vt, value = oleauto.read(oleauto.op("Int", quotient))
        assert int(value) == x // 2 == int_of(x / 2)
