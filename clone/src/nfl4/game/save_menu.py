"""Save Game while playing: which of the three places, then quit or keep playing. This is inspired by Jim Kitchen.

CLAUDE.md 0.23, playbook 7.17, NX-S5 and NX-S6 (D-086). The original's Save Game wrote football.sav and ended the program. The clone asks which
place to save in (the game's own place first, or the first empty one for a game that was never saved), says what each place holds before it is
replaced and asks once before replacing a different game, writes the file, says "Game Saved", and asks whether to quit (the first item, so Enter
does what the original did) or keep playing. The questions are the program's menus (`FranchiseQuestion`: Up, Down, the digits, Enter, F1, F2),
and Escape at the place question saves nothing and goes back to the play menu. The engine calls these three methods (game/pag_breaks.py).
"""
from __future__ import annotations

from ..data import debuglog
from ..data.files.shelf import SLOTS
from ..extras.franchise.question import FranchiseQuestion, ask_yes_no
from . import save_summary as SS
from . import save_texts as S


class SaveUi:
    def __init__(self, program):
        self.p = program

    def _order(self, taken: dict) -> list[int]:
        """The places in the order they are read: the game's own place first, else the first empty place, then the others."""
        current = self.p.slot_in_use
        first = current if current in SLOTS else next((slot for slot in SLOTS if slot not in taken), SLOTS[0])
        return [first] + [slot for slot in SLOTS if slot != first]

    def choose_slot(self, engine, record) -> int | None:
        p = self.p
        g = p.g
        store = p.store
        while True:
            taken = {entry.slot: entry for entry in store.shelf.scan(store.classify) if entry.kind == "game"}
            order = self._order(taken)
            labels = []
            for slot in order:
                entry = taken.get(slot)
                label = (S.SLOT_EMPTY % slot if entry is None else S.SLOT_HOLDS % (slot, SS.short_game(entry, with_slot=False)))
                labels.append(label + (S.SLOT_CURRENT if slot == p.slot_in_use else ""))
            answer = FranchiseQuestion(g, S.SLOT_QUESTION, labels, escape_value=-1).ask()
            if answer == -1:
                debuglog.event("save", "slot_cancelled")
                return None
            slot = order[answer]
            entry = taken.get(slot)
            if entry is not None and slot != p.slot_in_use:          # another game's place: its contents were just said; ask once
                if not ask_yes_no(g, S.SLOT_REPLACE_QUESTION % slot, start_yes=False):
                    continue
            debuglog.event("save", "slot_chosen", slot=slot, replaces=entry is not None)
            return slot

    def quit_or_keep(self, engine, slot) -> str:
        p = self.p
        p.slot_in_use = slot
        answer = FranchiseQuestion(p.g, S.SAVED_IN_SLOT % slot + S.QUIT_OR_KEEP, [S.QUIT, S.KEEP_PLAYING], escape_goes_on=True).ask()
        debuglog.event("save", "after_save", choice="keep" if answer == 1 else "quit", slot=slot)
        return "keep" if answer == 1 else "quit"

    def saved_and_quit(self, engine, slot) -> None:
        """The game is saved for good and the program ends: the automatic save of the same game is not needed any more."""
        self.p.store.shelf.remove_auto("the game was saved and the program ends")
