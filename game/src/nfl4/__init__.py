"""NFL Football 4. This is inspired by Jim Kitchen ("NFL football version 4", Kitchens Inc).

Jim Kitchen, blind from birth, made his games free for the blind community; he died in 2015.
This is new code written from the behavior described in spec/GAME_SPEC.md (version 1.0, frozen); no original code.

Packages:
  game    pure logic and the key fields (no window, no sound card needed)
  speech  SAPI 5 (five speakers on one queue), NVDA and JAWS behind one manager
  audio   wav playback, pitch and pan (P7 S7.2 builds the original's seven sound slots on it)
  ui      the Win32 window that receives keys and typed characters
  data    per-user paths, settings, logging, the voice crash guard, the process's start and end
"""

VERSION = "0.16.4"         # P8 S8.2, 2026-10-26: no place of a lineup or depth chart says nobody, the man who fills in is named (an e-mail report, B-P189, D-168), not built yet; PR SR.7, 2026-10-26: the twelfth test installer (real ages and seasons in rosters.txt and a new franchise, Q-078, D-167; the draft's prospects, the rookies before the cut, free agents and awards said by their own position); PR SR.6, 2026-10-26: the eleventh test installer (the roster by positions, the lineup and the choice of starters, the returners, get the latest rosters; D-165, D-166); PR SR.2, 2026-10-25: the real rosters of 2026-10-25 with Madden NFL's positions (rosters.txt layout 2, D-152 to D-158), not built yet (SR.7); 0.16.1, P8, 2026-10-25 (b): the tenth test installer (D-133, D-150: the source folder is game\, the word "clone" retired, nothing new to play); 2026-10-25: the ninth test installer (NX-B2b, D-149: the 53-man Franchise, its benches); 2026-10-24: the eighth test installer (the owner's second report NX-D1 to NX-D5, NX-M1, NX-M2: real positions, starters who play the most, depth charts, key downs, no original music or celebrations); 1.0.0 is the first release (P11)
TITLE = "NFL Football 4"
