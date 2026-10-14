"""Every text Brain shows or speaks, exactly as in spec/STRINGS.md. This is inspired by Jim Kitchen's Brain.

Spaces inside the quotes are part of the original texts and are kept on purpose.
"""

CAPTION = "My Brain by Josh Kennedy, inspired by Jim Kitchen"                      # S01, owner's title format (DECISIONS 2026-10-13)
TITLE_SPOKEN = "My Brain by Josh Kennedy, inspired by Jim Kitchen."                # S04, owner's title format; carries the rule 0.5 attribution
MAIN_PROMPT = " Press a number from one to nine, or the escape key to exit. "      # S05
SELECT = " Select. "                                                               # S06
MODE_NAMES = ("no panning", "stationary panning",                                  # S07, S08
              "semi random panning", "totally random panning")                      # S09, S10
PRESS_SPACE = " Press the space bar to stop. "                                     # S11
WAV_PREFIX, WAV_SUFFIX = "nfl4", ".wav"                                           # S12, S13
CONTACT = "Please contact Jim Kitchen"                                             # S15
NO_VOICES = "Sorry but I couldn't find any voices to use"                          # S16
GAME_MENU_EXE = "gamemenu.exe"                                                     # S17
EXITING = " exiting program "                                                      # S18
NO_GAME_MENU = "Sorry, but I could not find the Kitchensinc game menu program."    # S19

# Clone additions
NO_VOICES_SPOKEN = NO_VOICES + ". " + CONTACT       # screen reader copy of the box (DECISIONS P5)
MESSAGE_TITLE = "Brain"                             # message box title (DECISIONS P5)
