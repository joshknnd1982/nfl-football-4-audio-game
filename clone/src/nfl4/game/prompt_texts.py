"""The short texts of the hot-key menus and the season prompts. This is inspired by Jim Kitchen.

GAME_SPEC 4.5 to 4.13 and STRINGS.md (CODE (lifted) ctog p_4216b0, adjvol p_421960, adjrate p_423530, GetCoach p_4311a0,
ChooseTeam p_4308e0, Getqbs p_4314d0, SayScedual p_42eba0). Every text is a string of the exe with its spaces and its
spellings for the speech engine ("schedual", "verses", "quarter back"), checked against spec/strings_all.tsv by
tests/test_prompt_texts.py; the long help texts of F5 to F7 are game/help_texts.py (generated). The voices' names in F11
and F12 are speech/roles.py (F11_NAMES are the strings 737, 742 to 745). The clone's own texts are at the end, marked.
"""
from __future__ import annotations

# ----- the answers of every yes or no question -----
YES = " yes "                                               # string s23
NO = " no "                                                 # string s24
IS = " is, "                                                # string s47: " is, <name>, correct for ..."

# ----- F8, ctog (4.5) -----
COMMENTS_OFF = " comments toggle off "                      # string 753, 0x421795 (comtog becomes 1)
COMMENTS_ON = " comments toggle, ON! "                      # string 754, 0x4217cc (comtog becomes 0)

# ----- F11, adjvol (4.6) -----
VOLUME_PROMPT_START = " Press the up arrow key to raise the volume of "          # string 679, 0x422358
VOLUME_PROMPT_MIDDLE = " or the down arrow key to lower it."                     # string 698, 0x4223aa
VOLUME_PROMPT_END = " Press the enter key when the volume is set the way that you want it. "   # string 757
VOLUME_MAXIMUM = " volume maximum "                         # string 758
VOLUME_HIGHER = " volume higher "                           # string 759
VOLUME_MINIMUM = " volume minimum "                         # string 760
VOLUME_LOWER = " volume lower "                             # string 761
SOUND_PROMPT_START = " press the up arrow key to raise the volume of the sounds"           # string 762, 0x422e5c
SOUND_PROMPT_MIDDLE = " or press the down arrow key to lower them. "                       # string 763
SOUND_PROMPT_END = " Press the enter key when you have them set the way that you want them. "   # string 764
DEMO_SOUND = "foot0"                                        # string s30: play2("foot0") after every change

# ----- Ctrl, adjrate (4.8) -----
RATE_PROMPT = "to adjust the speech rate, use the arrow keys and then press enter"   # string 765, 0x423658

# ----- GetCoach (4.9) -----
ENTER_COACH = " Enter the name of your coach "              # string 792, 0x431222
COACH_CORRECT = ", correct for the name of your coach? "    # string 793, 0x4312b5

# ----- ChooseTeam (4.10) -----
CHOOSE_YOUR_TEAM = " choose your team "                     # string 789, 0x43097b: " " & coach & this
YOUR_TEAM_IS_THE = " your team is the "                     # string 790, 0x430cc0
IS_THIS_CORRECT = ". Is this correct? "                     # string 791, 0x430d32

# ----- Getqbs (4.12) -----
ENTER_OWN_QUARTERBACK = " enter the name of your quarter back or press enter "   # string 794, 0x4315c4
OWN_QUARTERBACK_CORRECT = ", correct for the name of your quarter back? "         # string 796, 0x43172d
QUARTERBACK_HEADING = "Quarterback:"                        # string 797, appended to footplay.txt (0x4319a0)
ENTER_THE_NAME_OF_THE = " enter the name of the "           # string 798, 0x431bbd
QUARTERBACK_OR_PRESS_ENTER = " quarter back or press enter "   # string 799, 0x431bcf
CORRECT_FOR_THE_NAME_OF_THE = ", correct for the name of the "    # string 800, 0x431d33
QUARTERBACK_QUESTION_END = " quarter back? "                # string 801, 0x431da9

# ----- SayScedual (4.11) -----
SCHEDULE = " schedual. "                                    # string 691, 0x42f041: " " & team & this
GAME_NUMBER = " game number "                               # string 645, 0x42f281: then Str$(n)
VERSES_THE = " verses the "                                 # string 780
LIKE_THIS_SCHEDULE = " do you like this schedual? yes "     # string 781, 0x42f6e5: " " & coach & this
GAMES_FOR_THE = " games for the "                           # string 782, 0x42ece2
ARE = " are. "                                              # string 787, 0x42edfd
THE = " the "                                               # string s46, 0x42eee6
END = ". "                                                  # string s38
# gtp 17 to 20 (also the week loop's play-off week line, S7.4b): strings 783 to 786
PLAYOFF_WEEK_NAMES = {17: "Wild card play off week", 18: "division play off week",
                      19: "division championship play off week", 20: "super bowl week"}
