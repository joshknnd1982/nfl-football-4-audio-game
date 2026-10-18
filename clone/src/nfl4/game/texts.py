"""Texts NFL Football 4 shows or speaks, exactly as in spec/STRINGS.md (ids given). This is inspired by Jim Kitchen.

Spaces inside the quotes are part of the original texts and are kept on purpose (GAME_SPEC 17.2, GAP_REGISTER G-S3).
S7.1 holds only what the skeleton speaks or shows; the game's texts come with S7.3 and S7.4.
"""

# Rule 0.5.1 (owner, 2026-10-13): the caption replaces the original caption "NFL football  By Jim Kitchen" (ids 2551, 2558);
# it is the window's title and the first line of footballlog.txt, and it stays as it is (rule 0.16 leaves it alone).
CAPTION = "NFL Football 4 by Josh Kennedy, inspired by Jim Kitchen"

# Rule 0.16 (owner, 2026-10-18, playbook 7.12): the spoken start-up title is one welcome sentence that names the game, its
# author and its inspiration, spoken once at every launch where the title was (GAP_REGISTER G-F1). It replaces the spoken
# " Jim's N. F. L. Football, version 4. " of the first start (id 2556) AND the original's " Welcome to " (id 2554) before it,
# so the word welcome is said once. The game's name is said as a person says it: the letters of NFL spaced so the voices spell them.
GAME_SPOKEN = "N. F. L. football"
INSPIRATION = "Jim Kitchen's original games"
TITLE_SPOKEN = f"Welcome to Josh Kennedy's {GAME_SPOKEN}, loosely inspired by {INSPIRATION}."

NO_VOICES = "Sorry but I couldn't find any voices to use"                          # 2570
CONTACT = "Please contact Jim Kitchen"                                             # 2569, never shown by the clone (D-008)
THANK_YOU = " Thank you for playing N. F. L. football version 4 By Jim Kitchen "   # 2567, the exit (S7.4)
NO_GAME_MENU = "Sorry, but I could not find the Kitchensinc game menu program."    # 2572, the exit (S7.4)

# Clone additions (CLONE in the conformance tests)
REPOSITORY = "https://github.com/joshknnd1982/nfl-football-4-audio-game"            # D-007 repository name, D-008
NO_VOICES_CONTACT = "For help, see " + REPOSITORY                                  # G-F9: replaces CONTACT
NO_VOICES_SPOKEN = NO_VOICES + ". " + NO_VOICES_CONTACT                            # screen reader copy of the box (G-F9)
MESSAGE_TITLE = "NFL Football 4"                                                   # message box title
