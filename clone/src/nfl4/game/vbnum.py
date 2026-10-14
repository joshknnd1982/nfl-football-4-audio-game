"""Visual Basic 6 number and text rules the original's arithmetic depends on. This is inspired by Jim Kitchen.

The original computes with Variants (every local of the play and clock code is a Variant). Two facts matter:

* Str$ puts a space in front of a number that is not negative (" 7", " 0") and "-" in front of a negative one. The
  original's sentences are built with it, so " game number  1" has two spaces (GAP_REGISTER G-S3, kept).
* A Variant that holds a Single stays a Single through + - * / and Int: R4 with R4 or with an Integer gives R4, only two
  Integers divided give R8 (a Double). The numbers the game clock uses start as Singles (the plays of a quarter are
  Int(Rnd * 8) + 30 stored with FSTP float, vt 4, asm 0x458328 to 0x458338), so the clock's whole chain is Single:
  `single()` rounds to a 32-bit float after every operation and reproduces the original (S7.3a, TESTED against the
  automation library's own VarMul, VarDiv, VarSub, VarAdd and VarInt, which the runtime's __vbaVar* helpers call: 3,588
  of 3,588 inputs equal, a Double chain differs in 57; `work/vb_variant_ops_s73a.py`, fixesforgames B-P40).
"""
from __future__ import annotations

import math
import struct


def single(x: float) -> float:
    """x rounded to a 32-bit float (a VB Single). Values too large for a Single become infinity, as in VB's overflow."""
    try:
        return struct.unpack("<f", struct.pack("<f", x))[0]
    except OverflowError:
        return math.inf if x > 0 else -math.inf


def int_of(x: float) -> int:
    """VB's Int: the largest whole number not above x (a floor, also for negative numbers)."""
    return math.floor(x)


def str_(value) -> str:
    """Str$: a leading space for a number that is not negative, "-" for a negative one. Whole numbers print without a
    decimal point (a Single 12.0 gives " 12"); the game only converts whole numbers."""
    if isinstance(value, float) and value == int(value):
        value = int(value)
    if isinstance(value, int):
        return (" " if value >= 0 else "") + str(value)
    text = format(value, ".15g")
    return (" " if value >= 0 else "") + text


def trim(text: str) -> str:
    """Trim$: removes spaces (only spaces, as VB does) at both ends."""
    return text.strip(" ")


def rtrim(text: str) -> str:
    """RTrim$: removes the spaces at the end."""
    return text.rstrip(" ")
