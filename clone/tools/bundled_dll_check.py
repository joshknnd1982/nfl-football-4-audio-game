"""Load the NVDA controller DLL of a BUILT Brain with this Python's bitness and ask if NVDA runs. Inspired by Jim Kitchen's Brain.

Never speaks (only nvdaController_testIfRunning). Run with nfl4-64 Python for the 64-bit build and
nfl4-32 Python for the 32-bit build, from any folder:
  python -I bundled_dll_check.py <src folder of the clone> <path to the build's brain folder>
"""
import os
import struct
import sys

sys.path.insert(0, sys.argv[1])
from nfl4.speech.nvda import NvdaBackend  # noqa: E402

bits = struct.calcsize("P") * 8
arch = "x64" if bits == 64 else "x86"
path = os.path.join(sys.argv[2], "_internal", "nfl4", "speech", "nvda_client", arch, "nvdaControllerClient.dll")
backend = NvdaBackend(path=path)
print(f"{bits}-bit Python, DLL {path}: exists={os.path.exists(path)}, NVDA reported running={backend.is_available()}")
sys.exit(0 if os.path.exists(path) else 1)
