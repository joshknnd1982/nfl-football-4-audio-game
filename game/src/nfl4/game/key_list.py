"""The master list of every key the game handles (CLAUDE.md 0.24, playbook 7.13, NX-H1, D-091). This is inspired by Jim Kitchen.

ONE list, `ROWS`: the key, where it works, what it does, in which mode. Three documents are made from it, and a test
(tests/test_sx10b2_keys.py) fails when a key of the list is missing from any of them or when the code handles a key that is not in
the list:

    F5, the special keys    the original's text word for word (game/help_texts.py), then `help_lines(F5, mode)`: a short line for every
                            key the original's list does not name (Classic too); the features' own F5 lines (extras/nx_texts NXH) follow
    F6, the game help       the original's text word for word, then `help_lines(F6, mode)`: every key, where it works and what it does
    README on GitHub        `readme_text()`, written to game/README_keys.md by `py -3.14 -I game/tools/make_docs.py` (a draft until P11)

A key that a feature of the N. F. L. rules already names in its own F5 line (T, C, A and D at a penalty, the playbook's Back) has its
probe text here instead of a new line: the test looks for the probe in the whole F5. `consts` are the names of the key constants of
the code that the row covers and `letters` the letters it handles; the scan test reads both.
"""
from __future__ import annotations

from typing import NamedTuple

KEY_F5, KEY_F6, KEY_F7 = "116", "117", "118"


class KeyRow(NamedTuple):
    id: str
    keys: str           # as said and written: "Up and Down"
    where: str          # "Anywhere", "In a play menu", ...
    what: str           # one sentence, no end stop
    modes: str          # "all" (Classic and the N. F. L. rules) or "nfl" (the N. F. L. rules only)
    original: bool      # the original game's own key
    probe5: str = ""    # the text of F5 that already names the key (the original's list or a feature's line); "" when `f5` is generated
    f5: str = ""        # the generated F5 line (a key that F5 does not name yet)
    consts: tuple = ()  # the key constants of the code this row covers
    letters: str = ""   # the letter keys this row covers
    feature: str = ""   # the N. F. L. rules switch that gives the key ("timeouts", "challenges", "penalties", "qb", "playbooks"); "" always


ROWS: tuple[KeyRow, ...] = (
    KeyRow("f1", "F1", "Anywhere", "repeats the current prompt, then says where the help is", "all", True, "F1. repeat current prompt.",
           consts=("KEY_F1", "KEY_CODE_F1")),
    KeyRow("f2", "F2", "Anywhere, and in questions and lists", "plays the instant replay of what was just said", "all", True,
           "F2. instant replay.", consts=("KEY_F2",)),
    KeyRow("f3", "F3", "Anywhere in a game", "says the score", "all", True, "F3. say score.", consts=("KEY_F3",)),
    KeyRow("f4", "F4", "Anywhere in a game", "says the game clock; with the N. F. L. rules it also says whether the clock is running",
           "all", True, "F4. announce game clock.", consts=("KEY_F4",)),
    KeyRow("f5", "F5", "Anywhere", "reads the special key instructions", "all", True, "F5. reed special key instructions.",
           consts=("KEY_F5",)),
    KeyRow("f6", "F6", "Anywhere", "reads the game instructions", "all", True, "F6. reed Game instructions.", consts=("KEY_F6",)),
    KeyRow("f7", "F7", "Anywhere", "reads the football words and hints; in Classic it also describes the original's plays", "all", True,
           "f7. football terminology And hints.", consts=("KEY_F7",)),
    KeyRow("f8", "F8", "Anywhere", "switches the comments off and on", "all", True, "f8. comments toggle.", consts=("KEY_F8",)),
    KeyRow("f9", "F9", "Anywhere", "opens the added functions: the speech settings, the sounds, the names and the commentary, the rules, "
           "the franchise and the about text", "all", False, "F9. added functions", consts=("KEY_F9",)),
    KeyRow("f11", "F11", "Anywhere", "adjusts the volume of the voices and the sounds: Up and Down, Enter for the next (with the N. F. L. rules and the broadcast on, the volumes of the color commentator and the referee too)", "all", True,
           "F11. adjust volume of voices and sounds.", consts=("KEY_F11",)),
    KeyRow("f12", "F12", "Anywhere", "changes the voices (with the N. F. L. rules and the broadcast on, the voices of the color commentator and the referee too)", "all", True, "F12. change voice.", consts=("KEY_F12",)),
    KeyRow("ctrl", "Control", "Anywhere", "adjusts the rate of speech: Up and Down, Enter to keep it", "all", True,
           "Control key, adjust rate of speech.", consts=("KEY_CTRL",)),
    KeyRow("escape", "Escape", "Anywhere", "exits the game; in a play menu it asks whether you concede the game; in the F9 menus and "
           "lists it goes back", "all", True, "escape key, exit game.", consts=("KEY_ESCAPE",)),
    KeyRow("alt", "Alt, or F10", "Anywhere", "does what Escape does", "all", True, "",
           " Alt, or F10. the same as the escape key. ", consts=("KEY_ALT", "KEY_F10")),
    KeyRow("updown", "Up and Down", "In every menu", "move to the previous or the next item; they go around from the last item to "
           "the first", "all", True, "", " Up and Down. in a menu, move to the previous or the next item. ", consts=("KEY_UP", "KEY_DOWN")),
    KeyRow("digits", "Digits 1 to 9 and 0", "In the play menus and the kick off menu", "make the item with that number the current "
           "item; 0 is the tenth", "all", True, "", " Digits. in a menu, a number makes that item the current item. "),
    KeyRow("enter", "Enter", "In every menu and question", "takes the current item or the answer", "all", True, "",
           " Enter. takes the current item or answer. ", consts=("KEY_ENTER",)),
    KeyRow("yes_no", "Y, N, Tab", "In a yes or no question", "Y says yes and N says no at once; Up, Down or Tab change the answer and "
           "Enter takes it", "all", True, "", " Y and N. answer a yes or no question, and Up, Down or Tab change the answer. ",
           consts=("KEY_TAB",), letters="yn"),
    KeyRow("coin", "H, T, R, K", "At the coin toss, and at the coin toss before over time in the N. F. L. rules",
           "H is heads and T is tails; then R receives the kick off and K kicks off", "all", True,
           "", " H and T. at the coin toss, heads and tails. R and K. receive or kick off. ", letters="htrk"),
    KeyRow("name", "Letters, digits, Backspace", "When you type a name", "letters and digits type, Backspace deletes the last one and "
           "Enter finishes", "all", True, "", " Typing a name. letters and digits type, Backspace deletes, and Enter finishes. ",
           consts=("KEY_BACKSPACE", "KEY_SHIFT")),
    KeyRow("f9_menus", "Left, Right, Page Up, Page Down, Home, End, Space, letters", "In the F9 menus and lists",
           "Left and Right change a value, Page Up and Page Down move ten items, Home and End go to the ends, Space chooses where "
           "that fits, and typing letters jumps to a name", "all", False, "",
           " In the F9 menus. Left and Right change a value, Page Up and Page Down move ten items, Home and End jump to the ends, and "
           "typing letters jumps to a name. ", consts=("KEY_LEFT", "KEY_RIGHT", "KEY_SPACE", "KEY_PAGE_UP", "KEY_PAGE_DOWN", "KEY_HOME",
                                                       "KEY_END")),
    KeyRow("pages", "Page Up and Page Down", "In the saved game, franchise and season questions", "turn to the previous or the next "
           "page of a long list; F1 says the question again and F2 plays the replay", "all", False, "",
           " In the saved game and franchise questions. Page Up and Page Down turn the page. "),
    KeyRow("timeout", "T", "Anywhere in a game being played, until the play is run", "calls your time out at once; a call during a "
           "running play is granted when the play ends", "nfl", False, " T. calls a time out", consts=("KEY_T",), feature="timeouts"),
    KeyRow("back", "Backspace or Left, B", "In a list of plays or a playbook group", "go back one level, from a list of plays to the "
           "menu it came from; B chooses the Back item", "nfl", False, "Backspace, Left or B. goes back", letters="b", feature="playbooks"),
    KeyRow("right", "Right", "In the offense and defense menus of the N. F. L. rules with a playbook", "on a play family opens its "
           "lists of plays, and in a list goes to the family's next list; on Punt it opens the kinds of punts and the fake punts, and on "
           "Field Goal the fake field goals", "nfl", False, "",
           " Right. in the offense and defense menus, opens the lists of plays of a family, and then the next list; on Punt and Field "
           "Goal, their kinds and fakes. ", consts=("KEY_RIGHT",), feature="playbooks"),
    KeyRow("plus_minus", "Plus and Minus", "In a list of plays", "plus adds the current play to your favourites and minus takes it "
           "off; the main row's plus and the keypad's plus both work", "nfl", False, "",
           " Plus and Minus. in a list of plays, add the play to your favourites or take it off. ",
           consts=("KEY_PLUS_PAD", "KEY_PLUS_MAIN", "KEY_MINUS_PAD", "KEY_MINUS_MAIN"), feature="playbooks"),
    KeyRow("enter_pick", "Enter on a play type", "In the offense and defense menus of the N. F. L. rules with a playbook", "lets the "
           "playbook pick a play of that type for the down, the distance and the field position, and tells you its name; Enter on a play "
           "in a list calls that play", "nfl", False, "Enter on a play type lets the playbook pick the play", feature="playbooks"),
    KeyRow("more", "M", "In the offense and defense menus of the N. F. L. rules with a playbook", "opens More Plays, which holds every "
           "other list of plays; on defense it holds every list of defensive calls and the situation defenses", "nfl", False,
           "M opens More Plays", letters="m", feature="playbooks"),
    KeyRow("play_letters", "F, A, K, P, O, N", "In the offense and defense menus of the N. F. L. rules with a playbook", "F opens "
           "your favourites, A calls your last play again, K kneels down and P spikes the ball when they help, O opens formation and "
           "tempo, and N in More Plays finds a play by its name; the defense menu has F, A, O and N as well, and on fourth down P opens "
           "the kick defense", "nfl", False, "",
           " F, A, K, P, O and N. in the offense menu: favourites, again, kneel down, spike the ball, formation and tempo, and find a "
           "play by name; the defense menu has F, A, O and N too, and on fourth down P. is the kick defense. ",
           letters="fakpon",
           feature="playbooks"),
    KeyRow("likely", "W", "In the offense and defense menus of the N. F. L. rules with a playbook", "says which play the playbook "
           "would most likely pick for the play type you are on, or call in the list you are in, and how often; it draws nothing, so "
           "asking changes nothing in the game", "nfl", False, "",
           " W. in the offense and defense menus, says which play the playbook would most likely pick, and how often. ",
           letters="w", feature="playbooks"),
    KeyRow("target", "R", "In the offense menu of the N. F. L. rules with a playbook", "chooses who your next pass goes to: the first item "
           "keeps the play's own pick, then the receivers, and the first two running backs when the play can throw to one", "nfl", False, "",
           " R. in the offense menu, chooses the receiver of your next pass. ", letters="r", feature="playbooks"),
    KeyRow("blitzer", "L", "In the defense menu of the N. F. L. rules with a playbook", "chooses who blitzes on your next blitz call: the "
           "first item picks a player by chance", "nfl", False, "", " L. in the defense menu, chooses the player who blitzes. ", letters="l",
           feature="playbooks"),
    KeyRow("find", "Letters, Backspace, Enter", "In Find a Play by Name", "type the first letters of a word of the play's name, here "
           "T is a letter too; Backspace deletes the last one and Enter finds the plays", "nfl", False, "",
           " Find a Play by Name. type the first letters of the name, then Enter. ", feature="playbooks"),
    KeyRow("save", "S", "In a play menu", "chooses the Save Game item, the last one; at the penalty question it saves the game with "
           "the question kept", "nfl", False, "", " S. in a play menu, chooses Save Game. ", letters="s"),
    KeyRow("challenge", "C", "In a play menu", "chooses Challenge the Ruling, or says why you cannot challenge", "nfl", False,
           "C. in a play menu", letters="c", feature="challenges"),
    KeyRow("describe", "D", "In a play menu and the kick off menu", "says a plain description of the current item for a person who "
           "knows nothing of football; the menu stays on the item", "nfl", False, "",
           " D. in a play menu and the kick off menu, describes the current item in plain words. ", letters="d"),
    KeyRow("roster", "Up and Down, Left and Right, Page Up and Page Down, Home, End, letters, Enter", "In F9, Franchise, your roster",
           "Up and Down go player by player, Left and Right and Page Up and Page Down go position by position, Home and End go to the first "
           "and the last, a letter goes to the next position that starts with it (E goes to the tight ends and T is never used), and Enter "
           "opens the player's items: make him a starter, the kick returner or the punt returner, or change his name", "nfl", False, "",
           " In your roster. Up and Down go player by player, Left and Right position by position, a letter jumps to a position, and Enter "
           "opens the player's items. "),
    KeyRow("lineup", "Enter on a position", "In F9, Rules, Depth charts, in the starting lineup and in the positions' items",
           "opens the list of the players who may start there, the starter first, then the players of his family who can move there and "
           "the practice squad's players; Enter on a player makes him the starter, and a practice squad player is brought up for the game",
           "nfl", False, "", " In the depth charts. Enter on a position lists the players who may start there; Enter on one makes him the starter. "),
    KeyRow("describe_position", "D in a depth chart", "In F9, Rules, Depth charts, in the starting lineup and in the positions' items",
           "says a plain description of the position the list is on, for a person who knows nothing of football", "nfl", False, "",
           " D in a depth chart. says what the position does. "),
    KeyRow("depth_move", "U, N and the digits 1 to 9", "In F9, Rules, Depth charts, in a position's list of players",
           "U moves the player up one place on the depth chart and N moves him down one place; a digit puts him at that place and the others "
           "move down one; the order is kept until you change it, and the next game uses it", "nfl", False, "",
           " In a position's list of the depth chart. U moves the player up, N moves him down, and a digit puts him at that place. ",
           letters="un"),
    KeyRow("penalty", "A and D", "At a penalty question", "A accepts the penalty and D declines it; Up and Down change the answer and "
           "Enter takes it", "nfl", False, "A. accepts it and D. declines it", letters="ad", feature="penalties"),
    KeyRow("qb_items", "8, 9 and 0", "In the offense menu with quarterback runs", "8 is the quarterback sneak, 9 the keeper and 0 the "
           "draw", "nfl", False, "In the offense menu, 8 is the quarterback sneak", feature="qb"),
)
BY_ID = {row.id: row for row in ROWS}
# key constants of the code that are not keys of the player (the scan test skips them)
NOT_KEYS = frozenset({"KEY_CODES_OF_REPEAT", "KEY_NAMES"})


def rows_for(mode: str, features=None) -> list[KeyRow]:
    """The rows that apply in a mode: "classic" has the rows of mode "all", "nfl" has all of them, or only those whose feature is in
    `features` (the switches that are on; None: every feature) as the features' own help lines are only spoken while the feature is on."""
    return [row for row in ROWS if (mode == "nfl" or row.modes == "all") and (features is None or not row.feature or row.feature in features)]


def help_lines(key: str, mode: str, features=None) -> list[str]:
    """The generated lines that follow the original's text and the features' own lines after F5 (a short line for every key that F5 does not
    name) or F6 (every key, where it works, what it does). Other keys: none."""
    if key == KEY_F5:
        return [row.f5 for row in rows_for(mode, features) if row.f5]
    if key == KEY_F6:
        lines = [" The keys. Each key is said with where it works and what it does. "]
        lines += [" %s. %s. %s. " % (row.keys, row.where, row.what[0].upper() + row.what[1:]) for row in rows_for(mode, features)]
        return lines
    return []


def readme_text() -> str:
    """The Keys section of the GitHub README (game/README_keys.md), made from the rows. Plain text, one key per line."""
    out = ["# Keys", "",
           "Every key the game handles, where it works and what it does. This list is made from the game's master list of keys "
           "(`game/src/nfl4/game/key_list.py`); the same keys are spoken by F5 (the special keys) and F6 (the game instructions). "
           "Keys marked \"N. F. L. rules\" work only with the N. F. L. rules; Classic is the original game exactly.", ""]
    for row in ROWS:
        extra = "" if row.modes == "all" else " (N. F. L. rules only)"
        origin = "original game" if row.original else "added"
        out.append("- **%s**%s: %s. %s. (%s)" % (row.keys, extra, row.where, row.what[0].upper() + row.what[1:], origin))
    out.append("")
    return "\n".join(out)


README_START, README_END = "<!-- keys:start -->", "<!-- keys:end -->"


def readme_block() -> str:
    """The Keys section as it stands inside the repository's README.md (the game folder), between two markers: the rows of README_keys.md
    under a second-level heading (P11, rule 0.24 (3))."""
    text = readme_text()
    return README_START + "\n## Keys" + text[len("# Keys"):].rstrip("\n") + "\n" + README_END


def splice_readme(readme: str) -> str:
    """The README text with its Keys block rewritten from the rows (the rest of the README is the maintainer's own words)."""
    start, end = readme.index(README_START), readme.index(README_END) + len(README_END)
    return readme[:start] + readme_block() + readme[end:]
