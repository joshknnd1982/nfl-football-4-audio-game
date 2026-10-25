"""The texts of the season engine and the Super Bowl presentation. This is inspired by Jim Kitchen.

GAME_SPEC 5.14 to 5.17 and STRINGS.md (CODE (lifted) pog p_4615b0, finplay17 p_47d8b0, superbowl p_484860). Every text is
a string of the exe with its spaces and its spellings, copied from the lifted line named next to it and checked against
spec/strings_all.tsv by tests/test_season_texts.py (and the module's names are never assigned twice, B-T40). The sentences
are joined in the engine as the original joins them: the regular week's results use Trim$ numbers ("24, to 17"), the
play-off results use Str$ numbers (a leading space each: "by the score of  24 to 17"), the division and wild card lines
use Trim$ numbers.
"""
from __future__ import annotations

# ----- a regular week (pog, 5.14) -----
GAMES_OF_WEEK = " Games of week number "           # string 2529, 0x462f64; then Trim$(Str$(gtp)) and ". "
OVER_THE = " over the "                              # string 2530: "<winner> over the <loser>"
BY_THE_SCORE_OF = " by the score of "                # string 2531 (also finplay17 and superbowl)
COMMA_TO = ", to "                                   # string s557 (also superbowl)
END = ". "                                           # string s38

# ----- the end of the regular season (pog, 5.15) -----
DIVISION_WINNERS_ARE = " the division winners are. "   # string 2532, 0x469939
AFC_WILD_CARD_TEAMS = " the A. F. C. wild card teams are. "   # string 2533, 0x46ae67
NFC_WILD_CARD_TEAMS = " the N. F. C. wild card teams are. "   # string 2534, 0x46c230
DOT_AT = ". at "                                    # string s556: "<team>. at <wins> and <losses>. "
AND = " and "                                       # string s529
AT = " at "                                         # string s559 (the line of a team that is out)
DID_NOT_MAKE_THE_PLAYOFFS = " did not make it into the playoffs. "   # string 2535, 0x46f9e3

# ----- a play-off result (pog's play-off weeks, finplay17, 5.16 and 5.17): " The <winner> won over the <loser> by the
# score of <Str$ w> to<Str$ l>" with RTrim$ and ". " -----
THE = " The "                                       # string s558
WON_OVER_THE = " won over the "                     # string 2537
TO = " to"                                          # string s560

# ----- the headings of the rounds, pog's wording (5.16) -----
POG_AFC_WILD_CARD = " In the A. F. C. wild card games. "              # string 2536 (also finplay17)
POG_NFC_WILD_CARD = " In the N. F. C. wild card games. "              # string 2538 (also finplay17)
POG_AFC_DIVISION = " In the A. F. C. division play off games. "       # string 2539
POG_NFC_DIVISION = " In the N. F. C. division play off games. "       # string 2540 (also finplay17)
POG_AFC_CHAMPIONSHIP = " In the A. F. C. championship  game. "        # string 2541, two spaces (Q47)
POG_NFC_CHAMPIONSHIP = " In the N. F. C. championship game. "         # string 2542

# ----- the headings of the rounds, finplay17's wording (5.17; Q47: each engine keeps its own text) -----
FIN_AFC_DIVISION = " In the A. F. C. Division play off games. "       # string 2543, capital D
FIN_AFC_CHAMPIONSHIP = " In the A. F. C. Championship game. "         # string 2544
FIN_NFC_CHAMPIONSHIP = " In the N. F. C. Championship game. "         # string 2545
IN_THE_SUPER_BOWL = " In the Super Bowl. "                            # string 2546

# ----- the Super Bowl presentation (superbowl p_484860, 5.6 item 7) -----
HAVE_WON_THE_SUPER_BOWL = " have Won the super Bowl! "     # string 2547
THEY_BEAT_THE = " They beat the "                          # string 2548
