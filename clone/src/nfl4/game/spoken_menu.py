"""Keyboard menus that speak, for the clone's added functions. This is inspired by Jim Kitchen.

The original had no settings, help or about. The added functions (F1 to F4, DECISIONS P7 S7.4) use
three small menu kinds, all driven by keys alone and all speaking through the same voice:
  SpokenMenu  a list of items with a spoken label; Left and Right change, Enter acts
  ListPicker  a long list (voices, sounds) with Page Up and Down, Home, End and type-ahead
  TextPages   lines to read one by one (help, about)
They read keys with KeyInput.read_key, which keeps keys typed ahead (the original's key fields stay
untouched by them) and returns on Escape. Closing the window raises GameQuit out of read_key.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable

from . import extra_texts as words
from .keys import (KEY_DOWN, KEY_END, KEY_ENTER, KEY_ESCAPE, KEY_F1, KEY_HOME, KEY_LEFT, KEY_PAGE_DOWN,
                   KEY_PAGE_UP, KEY_RIGHT, KEY_SPACE, KEY_UP, KeyInput, typed_character)

TYPE_AHEAD_SECONDS = 1.0


@dataclass
class Item:
    """One menu item. label gives the text spoken when it is reached or changed.

    enter: Enter pressed; returns text to speak instead of the label, or None to speak the label.
    change: Left (-1) or Right (+1) pressed; the label is spoken again afterwards."""
    label: Callable[[], str]
    enter: Callable[[], str | None] | None = None
    change: Callable[[int], None] | None = None


class _Speaker:
    def __init__(self, speech, keys: KeyInput):
        self.speech = speech
        self.keys = keys

    def say(self, text: str) -> None:
        """Replace whatever is being said with text (a menu answers every key at once)."""
        self.speech.stop()
        self.speech.say_async(text)

    def leave(self) -> None:
        self.speech.stop()


class SpokenMenu(_Speaker):
    """`space_enters`: Space acts as Enter; `digits_jump`: the digits 1 to 9 (and 0 for the tenth) go to that item. Both
    are off unless a menu asks (nfl4's F9 Rules menu, NFL_EXTRAS_DESIGN 12.2)."""

    def __init__(self, speech, keys: KeyInput, title: str, items: list[Item], help_text: str = words.MENU_HELP,
                 space_enters: bool = False, digits_jump: bool = False):
        super().__init__(speech, keys)
        self.title = title
        self.items = items
        self.help_text = help_text
        self.space_enters = space_enters
        self.digits_jump = digits_jump
        self.index = 0

    def _digit_item(self, code) -> int | None:
        """The item a digit key goes to (main row or keypad), or None."""
        if not self.digits_jump:
            return None
        char = typed_character(code) if isinstance(code, int) else ""
        if len(char) != 1 or not char.isdigit():
            return None
        number = int(char) or 10
        return number - 1 if number <= len(self.items) else None

    def run(self) -> None:
        self.say(words.menu_opening(self.title, len(self.items)) + " " + self.items[0].label())
        while True:
            code = self.keys.read_key()
            item = self.items[self.index]
            if code == KEY_ESCAPE:
                self.leave()
                return
            if self.space_enters and code == KEY_SPACE:
                code = KEY_ENTER
            jump = self._digit_item(code)
            if jump is not None:
                self.index = jump
                self.say(self.items[self.index].label())
            elif code in (KEY_UP, KEY_DOWN):
                self.index = (self.index + (1 if code == KEY_DOWN else -1)) % len(self.items)
                self.say(self.items[self.index].label())
            elif code in (KEY_HOME, KEY_END):
                self.index = 0 if code == KEY_HOME else len(self.items) - 1
                self.say(self.items[self.index].label())
            elif code in (KEY_LEFT, KEY_RIGHT) and item.change is not None:
                item.change(-1 if code == KEY_LEFT else 1)
                self.say(item.label())
            elif code == KEY_ENTER and item.enter is not None:
                result = item.enter()
                self.say(result if result is not None else item.label())
            elif code == KEY_F1:
                self.say(self.help_text)
            else:
                self.say(item.label())


class ListPicker(_Speaker):
    """A long list read one name at a time. name(i) gives the spoken name of item i.

    With close_on_enter (a choice, the voice list) Enter ends the picker and run() returns the chosen
    index, or None when Escape was pressed; the caller speaks what follows. Otherwise Enter calls
    on_enter(i), which returns text to speak or None, and the list stays (the sound preview).
    search(text) returns the index of the best match for typed letters."""

    def __init__(self, speech, keys: KeyInput, title: str, count: int, name: Callable[[int], str],
                 on_enter: Callable[[int], str | None] | None = None, start: int = 0, close_on_enter: bool = True,
                 search: Callable[[str], int | None] | None = None, help_text: str = words.LIST_HELP,
                 clock: Callable[[], float] = time.monotonic,
                 first_letter: Callable[[str, int], int | None] | None = None,
                 letter_mode: Callable[[], str] = lambda: "type"):
        super().__init__(speech, keys)
        self.title = title
        self.count = count
        self.name = name
        self.on_enter = on_enter
        self.index = max(0, min(start, count - 1))
        self.close_on_enter = close_on_enter
        self.search = search
        self.first_letter = first_letter
        self.letter_mode = letter_mode
        self.help_text = help_text
        self.clock = clock
        self._typed = ""
        self._typed_at = -1e9

    def run(self) -> int | None:
        self.say(f"{self.title}. {self.count} items. Press F1 for help. {self.name(self.index)}")
        while True:
            code = self.keys.read_key()
            if code == KEY_ESCAPE:
                self.leave()
                return None
            if code in (KEY_UP, KEY_DOWN):
                self.index = (self.index + (1 if code == KEY_DOWN else -1)) % self.count
            elif code in (KEY_PAGE_UP, KEY_PAGE_DOWN):
                step = 10 if code == KEY_PAGE_DOWN else -10
                self.index = max(0, min(self.count - 1, self.index + step))
            elif code == KEY_HOME:
                self.index = 0
            elif code == KEY_END:
                self.index = self.count - 1
            elif code == KEY_ENTER:
                if self.close_on_enter:
                    return self.index
                result = self.on_enter(self.index) if self.on_enter is not None else None
                if result is not None:
                    self.say(result)
                continue
            elif code == KEY_F1:
                self.say(self.help_text)
                continue
            elif (self.search is not None or self.first_letter is not None) and (char := typed_character(code)):
                if self.letter_mode() == "first" and self.first_letter is not None and char != " ":
                    found = self.first_letter(char, self.index)      # a letter jumps to the next name that starts with it
                    if found is not None:
                        self.index = found
                    self.say(self.name(self.index))
                    continue
                if self.search is None:
                    self.say(self.name(self.index))
                    continue
                now = self.clock()
                self._typed = (self._typed if now - self._typed_at <= TYPE_AHEAD_SECONDS else "") + char
                self._typed_at = now
                found = self.search(self._typed)
                if found is not None:
                    self.index = found
            self.say(self.name(self.index))


class TextPages(_Speaker):
    """Lines read in order when opened, then one by one with Up and Down."""

    def __init__(self, speech, keys: KeyInput, title: str, lines: tuple[str, ...]):
        super().__init__(speech, keys)
        self.title = title
        self.lines = lines
        self.index = 0

    def run(self) -> None:
        self.speech.stop()
        self.speech.say_async(self.title + ".")
        for line in self.lines:
            self.speech.say_async(line)
        self.speech.say_async(words.PAGES_HELP)
        while True:
            code = self.keys.read_key()
            if code == KEY_ESCAPE:
                self.leave()
                return
            if code in (KEY_UP, KEY_DOWN):
                self.index = (self.index + (1 if code == KEY_DOWN else -1)) % len(self.lines)
                self.say(self.lines[self.index])
            elif code in (KEY_HOME, KEY_END):
                self.index = 0 if code == KEY_HOME else len(self.lines) - 1
                self.say(self.lines[self.index])
            else:
                self.say(words.PAGES_HELP if code == KEY_F1 else self.lines[self.index])
