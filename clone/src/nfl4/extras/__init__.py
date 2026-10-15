"""The seven extra features of the N. F. L. rules mode (nfl4 ONLY, CLAUDE.md rule 0.13). This is inspired by Jim Kitchen.

spec/NFL_EXTRA_FEATURES.md is the requirement and spec/NFL_EXTRAS_DESIGN.md the design (D-040 to D-042). Nothing in this
package goes into the starter kit, `shared`, `tools`, a playbook or another game. The classic engine (game/pag*.py) reaches
it only through the hooks of game/rules.py (H1 to H13); with the setting Rules = Classic none of this code runs, no random
number is drawn and no word is spoken (P1, C4; the golden Classic transcript proves it).

Built so far:
    SX.2  the real clock (C2, design 5), timeouts (NX1, design 6.3), F1 and F4 in N. F. L. rules mode, the Rules
          setting with its F9 menu, the extras section of football.sav, the timeout remarks of remarks.txt
"""
