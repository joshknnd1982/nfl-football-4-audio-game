"""The texts of Form_Load: start-up, the week line, today's game, the main menu and the exit. This is inspired by Jim Kitchen.

GAME_SPEC 3 and 4 (CODE (lifted) Form_Load p_486990, read in full in S7.4b). Every text is a string of the exe with its spaces
and its spellings, checked against spec/strings_all.tsv by tests/test_program_texts.py (the second part of this file, the
clone's own texts, is marked and is not in the exe). The title (rule 0.5.1), the thank-you and the "no game menu" sentence
are in game/texts.py; the play-off week names and " verses the " are in game/prompt_texts.py.
"""
from __future__ import annotations

# ----- the first start (0x487c20) -----
WELCOME_TO = " Welcome to "                                 # string 2554: then the clone's title (rule 0.5.1, G-F1)

# ----- the week line (0x488493 to 0x4884e8, 0x488874) -----
THIS_IS_WEEK = " This is week "                             # string 2561: then Str$(gtp)
OF_JIMS_FOOTBALL = " of Jim's N. F. L. football "           # string 2560: ends the week line and the play-off week text
THIS_IS_WEEK_LOG = " This is week #"                        # string 2562: the log's line, then Trim$(Str$(gtp))
THIS_IS_THE = " This is the "                               # string 2559: the play-off week line starts with it

# ----- today's game (0x4891a9 to 0x489800) -----
TODAYS_GAME_IS = " Today's game is "                        # string 2563
AND = " and "                                               # string s529 (also " verses the " in prompt_texts)

# ----- the main menu (0x489934 to 0x489ae2) -----
SELECT = " select "                                         # string 2243: " " & coach & this
CHOICES = {1: " 1. play game ",                             # strings 2564, 2555, 2565, 2566
           2: " 2. see schedule ",
           3: " 3. see standings ",
           4: " 4. exit game "}

# ----- the log's title line (0x488422), the clone's own title (rule 0.5.1) is used instead; kept for STRINGS.md -----
LOG_TITLE_ORIGINAL = "NFL football  By Jim Kitchen"          # string 2558

# ----- clone texts (not in the exe): GAME_SPEC 3, GAP_REGISTER G-F3 (a draft wording, S8.2 listens) -----
SEASON_OVER = " The season is over. A new season begins. "
FIRST_START_F9 = " Press F9 for the added functions: the speech settings, the sounds and the about text. "
