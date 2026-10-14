"""Clear the Control Flow Guard flag in the header of a PyInstaller exe. Inspired by Jim Kitchen's Brain.

PyInstaller's bootloader is built with Control Flow Guard (IMAGE_DLLCHARACTERISTICS_GUARD_CF). A process with that
flag kills itself with 0xC0000409 (fast fail) when code calls an address that is not a valid indirect-call target,
which is exactly what a voice that emulates a CPU does (SmoothTalker, the owner's SAPI 5 wrapper of the Dr. Sbaitso
engine, runs under Unicorn/QEMU, which generates code at run time). python.exe is not built with the flag and runs
those voices fine, so Brain's exe must not have it either. Only the two flag bytes in the optional header change; the
appended archive is untouched; the PE checksum is recomputed (it is 0 for most exes: then it stays 0).
Usage: python clear_cfg_flag.py <nfl4.exe> [--check]    (--check only reports)
"""
import struct
import sys

import pefile

GUARD_CF = 0x4000


def main() -> int:
    path = sys.argv[1]
    check_only = "--check" in sys.argv
    pe = pefile.PE(path, fast_load=True)
    offset = pe.OPTIONAL_HEADER.get_field_absolute_offset("DllCharacteristics")
    value = pe.OPTIONAL_HEADER.DllCharacteristics
    checksum = pe.OPTIONAL_HEADER.CheckSum
    pe.close()
    print(f"{path}: DllCharacteristics {value:#06x}, Control Flow Guard {'ON' if value & GUARD_CF else 'off'}")
    if check_only or not value & GUARD_CF:
        return 0
    with open(path, "r+b") as handle:
        handle.seek(offset)
        handle.write(struct.pack("<H", value & ~GUARD_CF))
    if checksum:                                   # a signed or checksummed exe: recompute it
        pe = pefile.PE(path, fast_load=True)
        pe.OPTIONAL_HEADER.CheckSum = pe.generate_checksum()
        data = pe.write()
        pe.close()
        with open(path, "wb") as handle:
            handle.write(data)
    print("  cleared")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
