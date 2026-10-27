"""The words of the start-up choice and of the saved games. This is inspired by Jim Kitchen.

CLAUDE.md 0.23, playbook 7.17, NX-S1 to NX-S8 (D-086). CLONE texts: the original said nothing about its saved game (it loaded it and
deleted the file). Every text is spoken, so each starts and ends with a space as the original's do. The one-sentence summaries of the
saves are made by `game/save_summary.py` from the pieces here.
"""
from __future__ import annotations

# ----- the start-up menu (NX-S1): its items, in the order the menu builds them -----
MENU_PROMPT = " What do you want to do? "
CONTINUE_GAME = "continue the saved game"
CONTINUE_AUTO = "continue the game that was not finished"
CHOOSE_ANOTHER = "choose another saved game"
CONTINUE_SEASON = "continue the season"
CONTINUE_FRANCHISE = "continue the franchise"
NEW_GAME = "start a new game"
DELETE_GAME = "delete the saved game"
DELETE_DAMAGED = "delete the damaged saved game"
DELETE_SEASON = "delete the season"
DELETE_FRANCHISE = "delete the franchise"
RESTORE_GAME = "restore the saved game that was deleted"
RESTORE_SEASON = "restore the season that was deleted"
RESTORE_FRANCHISE = "restore the franchise that was deleted"
RESTORE_SOMETHING = "restore something that was deleted"
OF_THE_FRANCHISE = " of the franchise"
WHICH_TO_RESTORE = " Which do you want to restore? "

# ----- a list of saved games (choose another, delete which) -----
WHICH_TO_CONTINUE = " Which saved game do you want to continue? "
WHICH_TO_DELETE = " Which saved game do you want to delete? "
LIST_BACK = "go back"

# ----- the sentences about what is saved (NX-S1, NX-S8) -----
YOU_HAVE_A_GAME = " You have a saved game"
YOU_HAVE_AN_UNFINISHED_GAME = " You have a game that was not finished"
IN_SLOT = " in slot %d"
THE_SCORE = ", the %s lead the %s %d to %d"
THE_SCORE_TIED = ", the %s and the %s are tied %d to %d"
THE_SCORE_UNNAMED = ", the score is %d to %d"
IN_THE_QUARTER = " in the %s quarter"
IN_OVER_TIME = " in over time"
WITH_TIME_LEFT = ", with %s left"
ABOUT = "about "
LESS_THAN_A_MINUTE = "less than a minute"
THE_BALL = ". The %s have the ball"
THE_WEEK = ". It is week %d"
THE_PLAYOFF_WEEK = ". It is the %s"
SAVED_ON = ". It was saved on %s. "
NO_DATE = ". "
THE_GAME_IS_DAMAGED = " The saved game%s is damaged and cannot be played. "
THE_GAME_IS_HELD = " The saved game%s is in use by another program and cannot be played now. "
THE_GAME_IS_OLD = " The saved game%s is from a week that is over, so it cannot be played. "
THE_GAME_HAS_NO_SEASON = " The saved game%s belongs to no season, so it cannot be played. "
THE_SEASON = " You have a season in progress: coach %s of the %s, %s, %s. "
THE_SEASON_NO_COACH = " You have a season in progress: the %s, %s, %s. "
THE_FRANCHISE = " You have a franchise in progress: coach %s of the %s, season %d, %s, %s. "
THE_FRANCHISE_OFFSEASON = " You have a franchise in progress: coach %s of the %s, season %d, in the offseason. "
WEEK_RECORD = "week %d"
PLAYOFFS_RECORD = "the %s"
WINS_AND_LOSSES = "%d win%s and %d loss%s"
NOTHING_SAVED = " There is nothing saved. "

# ----- deleting and restoring (NX-S2) -----
DELETE_QUESTION_GAME = " Delete %s? It is kept in the backup, and you can restore it until another is deleted. "
DELETE_QUESTION_SEASON = " Delete the season? Its saved games go with it. It is kept in the backup, and you can restore it until another is deleted. "
DELETE_QUESTION_FRANCHISE = " Delete the franchise? It is kept in the backup, and you can restore it. "
WAS_DELETED = " It was deleted and is kept in the backup. "
COULD_NOT_DELETE = " It could not be moved to the backup, so it was not deleted. "
WAS_RESTORED = " The saved game was restored to slot %d. "
SEASON_RESTORED = " The season was restored. "
FRANCHISE_RESTORED = " The franchise was restored. "
COULD_NOT_RESTORE = " It could not be restored. "
EVERY_SLOT_FULL = " Every slot holds a saved game, so nothing was restored. Delete one first. "
SEASON_EXISTS = " There is a season in progress, so the deleted one was not restored. Delete this one first. "
FRANCHISE_EXISTS = " There is a franchise in progress, so the deleted one was not restored. Delete this one first. "

# ----- D-173 (the owner 2026-10-26): three franchises, each restorable from its kept copies -----
CONTINUE_FRANCHISE_N = "continue franchise %d, the %s"
DELETE_A_FRANCHISE = "delete a franchise"
RESTORE_FRANCHISE_COPY = "restore the deleted franchise of the %s, season %d"
RESTORE_FRANCHISE_UNREADABLE = "restore a deleted franchise that could not be read"
OF_FRANCHISE_N = " of franchise %d"
FRANCHISE_N = " Franchise %d: "
WHICH_FRANCHISE_CONTINUE = " Which franchise do you want to continue? "
WHICH_FRANCHISE_DELETE = " Which franchise do you want to delete? "
WHICH_FRANCHISE_SLOT = " Where do you want the new franchise? You can keep three. "
FRANCHISE_SLOT_EMPTY = "franchise %d, empty"
FRANCHISE_SLOT_FULL = "franchise %d, the %s, season %d, replace it"
DELETE_QUESTION_FRANCHISE_N = " Delete franchise %d, the %s? It is kept in the backup, and you can restore it. "
FRANCHISE_RESTORED_TO = " The franchise was restored as franchise %d. You can continue it now. "
EVERY_FRANCHISE_FULL = " You have three franchises, so the deleted one was not restored. Delete one first; the deleted one stays in the backup. "

# ----- D-176 (a tester of 0.16.6: the backup could be reached only at the start, with a franchise going): a deleted franchise can be restored
# from the new-game question at the start and from F9, Franchise, while playing -----
RESTORE_A_FRANCHISE = "restore a deleted franchise"
WHICH_FRANCHISE_RESTORE = " Which deleted franchise do you want to restore? "
FRANCHISE_RESTORED_PLAY_NOW = " The franchise was restored as franchise %d. Press Enter to play it now, or Escape to stay. "
FRANCHISE_RESTORED_NEXT_START = (" The franchise was restored as franchise %d. To play it, choose it in the start-up menu the next time you start "
                                 "the game. ")
# said before the start-up menu's question when nothing is saved and the menu is there only for the backup (the tester heard only "start a new
# game" and found no restore: rule 0.28 (2), a menu that holds more than it speaks says which key opens the rest)
BACKUP_ONLY = " Nothing is saved now, but the backup keeps what you deleted. Press Down for the restore item. "

# ----- a new game (NX-S7) -----
NEW_KIND_QUESTION = " What kind of game do you want to start? "
NEW_SEASON = "a new season"
NEW_FRANCHISE = "a new franchise"
REPLACE_SEASON_QUESTION = (" Starting a new season replaces your season, and its saved games go with it. They are kept in the backup, "
                           "and you can restore them. Start a new season? ")
SAME_COACH_QUESTION = " Play as coach %s with the %s again? "
GAME_KEPT = " Your saved games are kept. "

# ----- saving while playing (NX-S5, NX-S6) -----
SLOT_QUESTION = " Save the game in which place? "
SLOT_EMPTY = "slot %d, empty"
SLOT_HOLDS = "slot %d, holds %s"
SLOT_CURRENT = ", this game's place"
SLOT_REPLACE_QUESTION = " Replace the saved game in slot %d? "
SAVE_CANCELLED = " The game was not saved. "
QUIT_OR_KEEP = " Do you want to quit, or keep playing? "
QUIT = "quit"
KEEP_PLAYING = "keep playing"
SAVED_IN_SLOT = " Saved in slot %d. "
GAME_OVER_SAVES_MOVED = " The saved game of this week was moved to the backup, because the game is over. "
