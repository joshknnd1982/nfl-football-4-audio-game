"""The automation library's Variant arithmetic, for tests of the original's number types. This is inspired by Jim Kitchen.

VB6 compiles `a * b`, `a / b`, `a - b`, `a + b` and `Int(a)` on Variants to __vbaVarMul, __vbaVarDiv, __vbaVarSub,
__vbaVarAdd and __vbaVarInt, which call oleaut32's VarMul, VarDiv, VarSub, VarAdd and VarInt. Calling those with
Variants of the types the original holds (a Single for the plays of a quarter, an Integer for the play counter) gives the
original's result without running the original (nfl4 S7.3a, work/vb_variant_ops_s73a.py, fixesforgames B-P40).
Windows only; `available()` is False elsewhere and the tests that need it skip.
"""
import ctypes
import struct
import sys

VT_I2, VT_I4, VT_R4, VT_R8 = 2, 3, 4, 5

_ole = None
if sys.platform == "win32":
    try:
        _ole = ctypes.WinDLL("oleaut32")
        for _name in ("VarAdd", "VarSub", "VarMul", "VarDiv"):
            _fn = getattr(_ole, _name)
            _fn.restype = ctypes.c_long
            _fn.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
        _ole.VarInt.restype = ctypes.c_long
        _ole.VarInt.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    except OSError:
        _ole = None

_SIZE = 16 if ctypes.sizeof(ctypes.c_void_p) == 4 else 24


def available() -> bool:
    return _ole is not None


def variant(vt: int, value):
    buf = ctypes.create_string_buffer(_SIZE)
    fmt = {VT_I2: "<Hxxxxxxh", VT_I4: "<Hxxxxxxi", VT_R4: "<Hxxxxxxf", VT_R8: "<Hxxxxxxd"}[vt]
    struct.pack_into(fmt, buf, 0, vt, value if vt in (VT_R4, VT_R8) else int(value))
    return buf


def read(buf):
    vt = struct.unpack_from("<H", buf, 0)[0]
    fmt = {VT_I2: "<h", VT_I4: "<i", VT_R4: "<f", VT_R8: "<d"}[vt]
    return vt, struct.unpack_from(fmt, buf, 8)[0]


def op(name: str, a, b=None):
    res = ctypes.create_string_buffer(_SIZE)
    if name == "Int":
        hr = _ole.VarInt(ctypes.addressof(a), ctypes.addressof(res))
    else:
        hr = getattr(_ole, "Var" + name)(ctypes.addressof(a), ctypes.addressof(b), ctypes.addressof(res))
    if hr != 0:
        raise RuntimeError("Var%s failed: %x" % (name, hr & 0xFFFFFFFF))
    return res


def clock_chain(total: int, played: int, countdown: float, countdown_vt: int = VT_R4):
    """sgc's arithmetic as the original does it: (pct, mins, L54, secs) as the library computes them. total is a Single
    Variant, played an Integer Variant, CountDown an Integer (100, 125, 170, 215) or a Single (after CountDown + W)."""
    total_v = variant(VT_R4, total)
    left = op("Sub", total_v, variant(VT_I2, played))
    pct = op("Int", op("Div", op("Mul", left, variant(VT_I2, 100)), total_v))
    m = op("Div", op("Mul", pct, variant(VT_I2, 15)), variant(countdown_vt, countdown))
    mins = op("Int", m)
    l54 = op("Int", op("Mul", m, variant(VT_I2, 100)))
    l74 = op("Sub", l54, op("Mul", variant(VT_I2, 100), mins))
    secs = op("Int", op("Div", op("Mul", l74, variant(VT_I2, 60)), variant(VT_I2, 100)))
    return tuple(int(read(v)[1]) for v in (pct, mins, l54, secs))
