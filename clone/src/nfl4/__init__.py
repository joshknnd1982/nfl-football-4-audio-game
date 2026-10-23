"""NFL Football 4 clone. This is inspired by Jim Kitchen ("NFL football version 4", Kitchens Inc).

Jim Kitchen, blind from birth, made his games free for the blind community; he died in 2015.
This is new code written from the behavior described in spec/GAME_SPEC.md (version 1.0, frozen); no original code.

Packages:
  game    pure logic and the key fields (no window, no sound card needed)
  speech  SAPI 5 (five speakers on one queue), NVDA and JAWS behind one manager
  audio   wav playback, pitch and pan (P7 S7.2 builds the original's seven sound slots on it)
  ui      the Win32 window that receives keys and typed characters
  data    per-user paths, settings, logging, the voice crash guard, the process's start and end
"""

VERSION = "0.13.0"         # P8, 2026-10-23: the sixth test installer (the latest calendar, 14-team play-offs, the trade window, the quarterbacks' list); 1.0.0 is the first release (P11)
TITLE = "NFL Football 4"
