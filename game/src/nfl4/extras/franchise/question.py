"""FranchiseQuestion: a question or wait inside the program's flow, on the original's own key wait (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 3.7 (B-W10). The F9 menu classes (game/spoken_menu.py) read keys with `read_key`, which runs no global
key, and speak with `say_async`, which keeps nothing for the replay key; the questions of the program's flow (the new-season
question, the stage waits, later the to-do list and the draft) must work with F1 to F4, F5 to F8, F11, F12, Ctrl and F9 as at
every wait of the original. So this class is built on `getkey` and the speakers, in the manner of `Program.main_menu`:

* the situation (say2, kept for F2) and the current item (say2, " 1. classic season ") are spoken;
* Up and Down move (they wrap) and speak the new item; the digits 1 to 9 (main row and keypad) take that item of the page as
  the current one and speak it; Enter takes the current item;
* F1 says the situation and the current item again (a global key's menu hands F1 back, D-018); F2 is the instant replay;
* Page Down and Page Up turn a page of a paged list (nine items a page, then NXF-40 "more" on the digit 0 and, on later pages,
  NXB-10 "Back"); each page starts with NXF-42 " page n of m. ";
* any other key is echoed (saykey) and the situation and the current item are said again from the top, the item kept;
* `escape_goes_on`: a wait with one item (a stage's end): Escape acts as Enter.
* `escape_value`: a list the player may leave without taking an item (the draft's long list of prospects): Escape answers it.
"""
from __future__ import annotations

from .. import nx_texts as X

KEY_ENTER, KEY_ESCAPE, KEY_F1, KEY_F2 = "13", "27", "112", "113"
KEY_PAGE_UP, KEY_PAGE_DOWN, KEY_UP, KEY_DOWN = "33", "34", "38", "40"
PAGE_SIZE = 9


class FranchiseQuestion:
    def __init__(self, game, situation, items: list, start: int = 0, escape_goes_on: bool = False,
                 page_size: int = PAGE_SIZE, escape_value: int | None = None):
        if not items:
            raise ValueError("a franchise question needs at least one item")
        self.g = game
        self.situation = situation
        self.items = list(items)
        self.escape_goes_on = escape_goes_on
        self.escape_value = escape_value               # a list the player may leave: Escape answers this (-1) without taking an item
        self.page_size = page_size
        self.pages = (len(self.items) + page_size - 1) // page_size
        self.page = min(max(0, start), len(self.items) - 1) // page_size
        self.cursor = min(max(0, start), len(self.items) - 1) - self.page * page_size      # an entry of the page's entries

    # ----- the entries of a page: its items, then the controls -----

    def _page_items(self) -> list:
        first = self.page * self.page_size
        return list(range(first, min(first + self.page_size, len(self.items))))

    def _controls(self) -> list:
        controls = []
        if self.page + 1 < self.pages:
            controls.append("more")
        if self.page > 0:
            controls.append("back")
        return controls

    def _entries(self) -> list:
        return self._page_items() + self._controls()

    def _entry_text(self, position: int) -> str:
        entries = self._entries()
        entry = entries[position]
        if isinstance(entry, int):
            label = self.items[entry].strip()
            return " %d. %s " % (position + 1, label) if label else ""     # a bare wait (NXE-03) speaks no number
        number = 0 if entry == entries[len(self._page_items())] else None
        word = X.text("NXF-40") if entry == "more" else X.text("NXB-10")
        return " %s%s " % ("%d. " % number if number is not None else "", word)

    def _page_line(self) -> str:
        return X.text("NXF-42", n=self.page + 1, m=self.pages) if self.pages > 1 else ""

    # ----- speaking -----

    def _say_all(self) -> None:
        """The situation and the current item, from the top (F1, a key that does nothing, the start)."""
        g = self.g
        g.empty_replay()
        for text in ([self.situation] if isinstance(self.situation, str) else self.situation):
            if text:
                g.say2(text)
        line = self._page_line()
        if line:
            g.say2(line)
        g.say2(self._entry_text(self.cursor))

    def _say_item(self) -> None:
        self.g.say2(self._entry_text(self.cursor))

    def _turn_page(self, step: int) -> None:
        page = self.page + step
        if not 0 <= page < self.pages:
            self._say_item()
            return
        self.page, self.cursor = page, 0
        line = self._page_line()
        if line:
            self.g.say2(line)
        self._say_item()

    # ----- the keys -----

    def _digit(self) -> int | None:
        keys = self.g.keys
        code = keys.code_text
        if code.isdigit() and 96 <= int(code) <= 105:
            return int(code) - 96
        char = keys.char
        return int(char) if len(char) == 1 and char.isdigit() else None

    def ask(self) -> int:
        """The index of the item taken (0 first). Never returns without an Enter (or Escape in a wait)."""
        g, keys = self.g, self.g.keys
        self._say_all()
        while True:
            keys.getkey(g.speech)
            code = keys.code_text
            entries = self._entries()
            if code == KEY_ESCAPE and self.escape_value is not None:
                return self.escape_value
            if code == KEY_ENTER or (code == KEY_ESCAPE and self.escape_goes_on):
                entry = entries[self.cursor]
                if isinstance(entry, int):
                    return entry
                self._turn_page(1 if entry == "more" else -1)
            elif code in (KEY_UP, KEY_DOWN):
                self.cursor = (self.cursor + (1 if code == KEY_DOWN else -1)) % len(entries)
                self._say_item()
            elif code == KEY_PAGE_DOWN:
                self._turn_page(1)
            elif code == KEY_PAGE_UP:
                self._turn_page(-1)
            elif code == KEY_F2:
                g.inrep()
            elif code == KEY_F1:
                self._say_all()
            else:
                digit = self._digit()
                if digit is not None:
                    count = len(self._page_items())
                    if digit == 0 and len(entries) > count:
                        self.cursor = count
                        self._say_item()
                        continue
                    if 1 <= digit <= count:
                        self.cursor = digit - 1
                        self._say_item()
                        continue
                g.saykey()
                self._say_all()


def wait_for_enter(game, lines) -> None:
    """A stage's end: its lines (the last is NXE-03), then Enter (or Escape) goes on, F1 says the stage again."""
    FranchiseQuestion(game, lines, [""], escape_goes_on=True).ask()


def ask_yes_no(game, question: str, start_yes: bool = True) -> bool:
    """A yes or no question of the program's flow (design 3.2: NXF-02 starts at no): the question, the answer (" yes " or
    " no "), Up and Down toggle, y and n answer, Enter takes the answer, F1 asks again, any other key is echoed."""
    from ...game import prompt_texts as T
    g, keys = game, game.keys
    answer = start_yes
    while True:
        g.empty_replay()
        g.say2(question)
        while True:
            g.say2(T.YES if answer else T.NO)
            keys.getkey(g.speech)
            code = keys.code_text
            if code == KEY_ENTER:
                return answer
            if code in (KEY_UP, KEY_DOWN, "9"):
                answer = not answer
                continue
            if code == KEY_F2:
                g.inrep()
                continue
            if code == KEY_F1:
                break
            g.saykey()
            if keys.char in ("y", "n"):
                return keys.char == "y"
            break
