"""The score sentences. This is inspired by Jim Kitchen.

GAME_SPEC 5.4 (CODE (lifted) SayScore p_42b590 and SayFinalScore p_42bab0; the strings 770, 771, s38, s39, s40). Arguments:
the score of the player's team and of the opponent. When the player's team leads the sentence is
"<own team>. <n>. <opponent team>. <m>", when the opponent leads "<opponent team>. <m>. <own team>. <n>", when the scores are
equal " tied <n> all". The team names are RTrim'd and followed by ". "; the numbers come from Str$ (a leading space), so a
team's score is separated by two spaces: "Bengals.  7. Browns.  3". The sentence ends with the second number, no full stop.
SayScore says " The score is " (say5) then the sentence (say, waited) and writes an empty line and " The score is <sentence>"
to the log whatever ptf is; SayFinalScore sets ptf to 1, says " The Final score is" (no space at the end) and the sentence
and sets ptf to 0.
"""
from __future__ import annotations

from .vbnum import rtrim, str_

THE_SCORE_IS = " The score is "          # string 770
THE_FINAL_SCORE_IS = " The Final score is"   # string 771, no space at the end
TIED, ALL = " tied", " all"              # strings s39, s40
AFTER_NAME = ". "                         # string s38


def score_sentence(own_team: str, opponent_team: str, own_score: int, opponent_score: int) -> str:
    """The sentence SayScore and SayFinalScore speak after their introduction."""
    if own_score > opponent_score:
        text = rtrim(own_team) + AFTER_NAME + str_(own_score)
        text = rtrim(text) + AFTER_NAME
        text += opponent_team
        text = rtrim(text) + AFTER_NAME
        return text + str_(opponent_score)
    if opponent_score > own_score:
        text = opponent_team
        text = rtrim(text) + AFTER_NAME + str_(opponent_score)
        text = rtrim(text) + AFTER_NAME
        text += own_team
        text = rtrim(text) + AFTER_NAME
        return text + str_(own_score)
    return TIED + str_(own_score) + ALL
