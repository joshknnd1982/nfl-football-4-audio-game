"""The season's typed prompts and questions: getter, ccn, cqn, GetCoach, ChooseTeam, Getqbs, SayScedual. This is inspired by Jim Kitchen.

GAME_SPEC 4.9 to 4.12 and 8.2 (CODE (lifted) getter p_429d10, ccn p_428f60, cqn p_429510, GetCoach p_4311a0, ChooseTeam
p_4308e0, Getqbs p_4314d0, SayScedual p_42eba0; read in full in S7.4a with the asm beside them). Every text, key test,
wait, draw and pause is the lifted one in the lifted order, the address beside it. Global keys (F5 to F8, F11, F12, Ctrl)
run inside every getkey here and come back as F1 (game/hotkeys.py, D-018).

The clone's own rules for typed names (D-022 items 1 and 2, GAP_REGISTER G-K5, D-034): the original types the character
of the key CODE (LCase(Chr(KeyCode)), Shift makes the next one UCase); the clone keeps that for every key that types
something on the player's keyboard, types the digit a keypad key shows (the original typed a to i), ignores a key that
types nothing (arrows, F2 to F4, Escape, Tab: the original typed % & ' ( q r s and control characters, which the name
check removed again), and stores at most 30 characters (keys beyond them are echoed, not stored).

What the original wrote to files here goes through `SetupStore` (S7.5 writes them): footbal1.dat when the team is
accepted, footbal2.dat when a schedule is made, and the two lines "Quarterback:" and the name appended to footplay.txt.
"""
from __future__ import annotations

from typing import Protocol

from ..data import debuglog
from . import prompt_texts as T
from .vbnum import str_

NAME_LIMIT = 30                 # G-K5 (D-034): the stored characters of a typed name
KEY_F1, KEY_ENTER, KEY_SHIFT, KEY_BACKSPACE = "112", "13", "16", "8"
KEY_UP, KEY_DOWN, KEY_TAB = "38", "40", "9"
YES, NO = 1, 2                  # the answer variable of every question (1 = yes, 2 = no)
SCHEDULE_LIKED, SCHEDULE_REJECTED, SCHEDULE_AGAIN = "liked", "rejected", "again"
DEFAULT_COACH = "coach"         # ccn's default (string 'coach', 0x429463)


class SetupStore(Protocol):
    def write_coach_and_team(self, tn1: int, tn2: int, coach: str) -> None: ...    # footbal1.dat (ChooseTeam)
    def write_schedule(self, schedule) -> None: ...                                 # footbal2.dat (makes)
    def append_quarterback(self, name: str) -> None: ...                           # footplay.txt (Getqbs)


class NullSetupStore:
    def write_coach_and_team(self, tn1, tn2, coach) -> None:
        pass

    def write_schedule(self, schedule) -> None:
        pass

    def append_quarterback(self, name) -> None:
        pass


NULL_SETUP_STORE = NullSetupStore()


def _kept(code: int) -> bool:
    """ccn and cqn keep codes 32, 48 to 57, 65 to 90 and 97 to 122 (0x429169 to 0x42933a)."""
    return code == 32 or 47 < code < 58 or 64 < code < 91 or 96 < code < 123


def clean_name(typed: str, default: str) -> str:
    """ccn (default "coach") and cqn (default ""): fewer than 2 characters typed, only spaces left or fewer than 2
    left give the default; otherwise the kept characters in order, the case as typed, no trimming."""
    if len(typed) < 2:                                   # 0x429041
        return default
    kept = "".join(c for c in typed if _kept(ord(c)))
    spaces = typed.count(" ")                            # L34: every space is counted and kept
    if spaces == len(kept) or len(kept) < 2:             # 0x429434, 0x42945a
        return default
    return kept


def ccn(typed: str) -> str:
    return clean_name(typed, DEFAULT_COACH)


def cqn(typed: str) -> str:
    return clean_name(typed, "")


class Prompts:
    def __init__(self, game):
        self.g = game

    @property
    def keys(self):
        return self.g.keys

    @property
    def store(self) -> SetupStore:
        return self.g.setup_store or NULL_SETUP_STORE

    def _getkey(self) -> str:
        self.keys.getkey(self.g.speech)
        return self.keys.code_text

    def _answer(self, answer: int, speaker) -> None:
        speaker(T.YES if answer == YES else T.NO)

    # ----- getter (8.2) -----

    def typed_character(self, code: str) -> str | None:
        """The character the clone stores for a key (D-022 item 2): a keypad digit, the original's g2 for a key that
        types something, None for a key that types nothing."""
        number = int(code) if code.isdigit() else -1
        if 96 <= number <= 105:
            return str(number - 96)
        if not self.keys.take_typed():
            return None
        return self.keys.char

    def getter(self, prompt: str) -> str:
        """The typed text: the debug log writes only that text was typed and how long it is, never the keys or the text (7.11)."""
        with debuglog.context("typing: " + prompt.strip()[:40]):
            text = self._getter(prompt)
        debuglog.add_typed(text, ccn(text), cqn(text))      # what is spoken is the cleaned form (apostrophes and accents go)
        debuglog.event("input", "text_entered", chars=len(text), prompt=prompt.strip()[:40])
        return text

    def _getter(self, prompt: str) -> str:
        """The typed text r: F1 speaks the prompt again and empties r; Shift makes the next key upper case; Backspace
        speaks and removes the last character; Enter ends; every other key is echoed and appended."""
        g, keys = self.g, self.keys
        shift = 0                                        # L24, 0 at every call
        while True:                                      # L_429d5c
            keys.clk()                                   # 0x429d5f
            g.say5(prompt)                               # 0x429d82
            r = ""                                       # 0x429da6
            while True:                                  # L_429da8
                code = self._getkey()                    # 0x429dab
                if code == KEY_F1:
                    break                                # 0x429dda: the prompt again
                if code == KEY_SHIFT:
                    shift = 1                            # 0x429dff
                    continue
                char = None
                if code not in (KEY_BACKSPACE, KEY_ENTER):
                    char = self.typed_character(code)
                if shift == 1:                           # 0x429e1f
                    shift = 0
                    if char is not None:
                        char = char.upper()              # 0x429e57: g2 = UCase$(g2)
                if code == KEY_BACKSPACE:                # 0x429e75
                    if len(r) < 1:
                        continue
                    keys.char = r[-1]                    # 0x429ede: g2 = Right$(r, 1)
                    g.saykey()                           # 0x429eec
                    r = r[:-1]                           # 0x429f48
                    continue
                if code == KEY_ENTER:                    # 0x429f65
                    return r
                if char is None:                         # the clone: a key that types nothing is ignored (D-022)
                    continue
                keys.char = char
                g.saykey()                               # 0x429f6a
                if len(r) < NAME_LIMIT:                  # G-K5: echoed, not stored beyond 30 characters
                    r += char                            # 0x429fa6

    # ----- GetCoach (4.9) -----

    def get_coach(self) -> str:
        g, season = self.g, self.g.season
        while True:                                      # L_4311f2
            self.keys.clk()                              # 0x4311f5
            season.coach = ccn(self.getter(T.ENTER_COACH))   # 0x431222, 0x431246, 0x431267
            again = self._confirm(T.IS + season.coach + T.COACH_CORRECT, g.say5, g.say2)
            if not again:
                return season.coach

    # ----- the real coach (nfl4 only, SX.11, NX-N1) -----

    def real_names_for_coach(self):
        """The real names when the N. F. L. rules are in use and the coaches are loaded, else None (the original's typed coach)."""
        real = getattr(self.g, "real_names", None)
        if real is None or not real.has_coaches():
            return None
        from ..extras.nfl_rules import is_nfl
        return real if is_nfl(self.g.rules) else None

    def coach_and_team(self) -> None:
        """GetCoach and ChooseTeam. With the real names the team comes first (the coach of a team is known only once it is chosen; the team
        prompts say "coach" as the original does when nothing was typed), then the question that offers the real coach: nothing is typed."""
        real = self.real_names_for_coach()
        if real is None:
            self.get_coach()
            self.choose_team()
            return
        self.g.season.coach = DEFAULT_COACH
        self.choose_team()
        self.real_coach(real)

    def real_coach(self, real) -> None:
        from ..data import debuglog
        from ..extras import nx_texts as X
        from ..extras.franchise.league import team_index
        from ..extras.franchise.question import FranchiseQuestion
        g, season = self.g, self.g.season
        coach = real.coach(team_index(season.tn1, season.tn2))
        how = "typed"
        if coach:
            team = g.league.team(season.tn1, season.tn2).strip()
            pick = FranchiseQuestion(g, [X.text("NXB-N01", team=team, coach=coach)],
                                     [X.text("NXB-N02", coach=coach), X.text("NXB-N03"), X.text("NXB-N04")]).ask()
            how = ("real", "list", "typed")[pick]
            if pick == 0:
                season.coach = coach
            elif pick == 1:
                season.coach = self._coach_from_list(real, team_index(season.tn1, season.tn2))
        if how == "typed":
            self.get_coach()
        self.store.write_coach_and_team(season.tn1, season.tn2, season.coach)       # ChooseTeam wrote it with the first name
        debuglog.event("names", "coach_chosen", how=how)

    def _coach_from_list(self, real, own_team: int) -> str:
        from ..extras import nx_texts as X
        from ..extras.franchise.league import team_ref
        from ..extras.franchise.question import FranchiseQuestion
        g = self.g
        choices = real.coach_choices()
        items = [X.text("NXB-N06", coach=name, team=g.league.team(*team_ref(team)).strip()) for team, name in choices]
        start = next((index for index, (team, _) in enumerate(choices) if team == own_team), 0)
        name = choices[FranchiseQuestion(g, [X.text("NXB-N05")], items, start=start).ask()][1]
        g.say2(X.text("NXB-N07", coach=name))
        return name

    def _confirm(self, question: str, ask, answer_speaker) -> bool:
        """The yes or no question of GetCoach and Getqbs (0x43126d to 0x431482, 0x431702 to 0x431900, 0x431d08 to
        0x431fb7): True when the name is to be asked again. Enter takes the answer, Up and Down toggle it, F1 asks again
        with the answer yes, y accepts, n asks the name again, any other key is echoed and asks again with yes.
        The calls it makes, per caller (question say5, answer say2 " yes " or " no ", getkey, saykey):
        GetCoach 0x4312cb, 0x431319, 0x43133a, 0x43135e, 0x431419; Getqbs own 0x431743, 0x4317ab, 0x4317cc, 0x4317f0,
        0x431894; Getqbs opponent 0x431dbb, 0x431e33, 0x431e50, 0x431e74, 0x431f41."""
        while True:                                      # the question, answer yes
            answer = YES
            ask(question)
            while True:                                  # the answer spoken
                self._answer(answer, answer_speaker)
                code = self._getkey()
                if code == KEY_ENTER:
                    return answer == NO
                if code in (KEY_UP, KEY_DOWN):
                    answer = NO if answer == YES else YES
                    continue
                if code == KEY_F1:
                    break
                self.g.saykey()
                if self.keys.char == "y":
                    return False
                if self.keys.char == "n":
                    return True
                break

    # ----- ChooseTeam (4.10) -----

    def choose_team(self) -> None:
        g, season = self.g, self.g.season
        while True:                                      # L_43094d
            text = " " + season.coach + T.CHOOSE_YOUR_TEAM   # 0x43097b
            season.tn1, season.tn2 = 1, 1                # 0x4309a6, 0x4309c7
            g.say2(text)                                 # 0x4309d4
            if not self._browse_teams():
                continue                                 # any other key: the whole choice again
            if self._team_accepted():
                break
        self.store.write_coach_and_team(season.tn1, season.tn2, season.coach)   # 0x430fc7 to 0x43110f

    def _browse_teams(self) -> bool:
        """L_4309f0: the team alone is spoken; Up and Down step through the 32 teams; Enter ends (True); any other key
        (F1 too) is echoed and the choice starts again (False)."""
        g, season = self.g, self.g.season
        while True:
            g.say2(g.league.team(season.tn1, season.tn2))    # 0x430a3e
            code = self._getkey()                        # 0x430a5d
            if code == KEY_ENTER:
                return True
            if code == KEY_UP:
                season.tn2 -= 1                          # 0x430ace
                if season.tn2 == 0:
                    season.tn2 = 4
                    season.tn1 -= 1
                    if season.tn1 == 0:
                        season.tn1 = 8                   # 0x430b89 (the asm at 0x430b70)
            elif code == KEY_DOWN:
                season.tn2 += 1                          # 0x430bd2
                if season.tn2 == 5:
                    season.tn2 = 1
                    season.tn1 += 1
                    if season.tn1 == 9:
                        season.tn1 = 1                   # 0x430b89 (the asm at 0x430c86)
            else:
                g.saykey()                               # 0x430f8b
                return False

    def _team_accepted(self) -> bool:
        """L_430c92: " <coach> your team is the <team>. Is this correct? " and the answer; True when accepted."""
        g, season = self.g, self.g.season
        while True:
            text = " " + season.coach + T.YOUR_TEAM_IS_THE + g.league.team(season.tn1, season.tn2) + T.IS_THIS_CORRECT
            answer = YES                                 # 0x430d57
            g.say2(text)                                 # 0x430d64
            while True:                                  # L_430d8a
                self._answer(answer, g.say2)             # 0x430dc6 " yes ", 0x430de7 " no "
                code = self._getkey()                    # 0x430e0b
                if code == KEY_ENTER:
                    return answer != NO                  # L_430f60
                if code in (KEY_UP, KEY_DOWN):
                    answer = NO if answer == YES else YES
                    continue
                if code == KEY_F1:
                    continue                             # 0x430ed2: the answer only
                g.saykey()                               # 0x430edb
                if self.keys.char == "n":
                    return False                         # L_430f1c
                if self.keys.char == "y":
                    return True                          # L_430f3b
                break                                    # 0x430f17: the question again

    # ----- Getqbs (4.12) -----

    def getqbs(self, state, saved: bool = False, own_from_file: str = "", defaults: tuple[str, str] | None = None) -> tuple[str, str]:
        """The two quarterbacks' names: the own one from footplay.txt when pag read it (gpn not 0), else asked and
        appended to the file; then the opponent's, asked at every game, except for a loaded game whose footplay.txt was
        read (its name came from football.sav, already in state.quarterbacks[2]). A name nobody types is a random free
        surname; an accepted name is blanked in the pool."""
        g = self.g
        own_default, opponent_default = defaults or ("", "")
        if state.gpn != 0:                               # 0x43158a
            own = own_from_file                          # 0x431b26: the last item of footplay.txt
            if own == "":                                # S7.5: a footplay.txt without a quarterback asks for him, once
                own = self._ask_quarterback(" " + g.season.coach + T.ENTER_OWN_QUARTERBACK,
                                            lambda name: T.IS + name + T.OWN_QUARTERBACK_CORRECT, own_default)
                self.store.append_quarterback(own)
            if saved:
                return own, state.quarterbacks.get(2, "")    # 0x431b5e
        else:
            own = self._ask_quarterback(" " + g.season.coach + T.ENTER_OWN_QUARTERBACK,
                                        lambda name: T.IS + name + T.OWN_QUARTERBACK_CORRECT, own_default)
            self.store.append_quarterback(own)          # 0x431978 to 0x4319ba
        team = g.opponent_team()
        opponent = self._ask_quarterback(T.ENTER_THE_NAME_OF_THE + team + T.QUARTERBACK_OR_PRESS_ENTER,
                                         lambda name: T.IS + name + T.CORRECT_FOR_THE_NAME_OF_THE + team
                                         + T.QUARTERBACK_QUESTION_END, opponent_default)
        return own, opponent

    def _ask_quarterback(self, prompt: str, question, default: str = "") -> str:
        """L_431596 (own) and L_431b64 (opponent): the typed name, else a random free surname (Int(Rnd * 1708) + 1, drawn
        again while the slot is blank: 0x43168e, 0x431c9a); the question; on acceptance the drawn slot is blanked, or
        every pool entry equal to a typed name ignoring case (0x431949, 0x431a8f; 0x432005, 0x4320e1).
        `default` (nfl4 only, SX.11): the real quarterback Enter takes instead of the drawn surname; the slot is still drawn and blanked,
        so the game's draws are the same with or without real names."""
        g = self.g
        while True:
            name = cqn(self.getter(prompt))              # 0x4315da, 0x4315f5 (0x431bd8, 0x431bf7)
            slot = 0                                     # 0x43161d (0x431c2d)
            if name == "":
                slot = g.pool.draw_slot()
                name = default or g.pool.name(slot)
            if not self._confirm(question(name), g.say5, g.say2):
                break
        if slot > 0:
            g.pool.blank(slot)
        else:
            g.pool.blank_matching(name)
        return name

    # ----- SayScedual (4.11) -----

    def say_schedule(self) -> None:
        g, season = self.g, self.g.season
        if season.gtp >= 17:                             # 0x42eca0
            self._say_playoff_games()
            return
        while True:                                      # L_42efd2
            g.say2(" " + g.own_team() + T.SCHEDULE)      # 0x42f04a
            for number, entry in enumerate(season.schedule[:16], start=1):
                g.say2(T.GAME_NUMBER + str_(number))     # 0x42f2cb
                g.dy(0.1, 0x42f30b)
                other = g.league.team(entry.division, entry.team)
                if entry.flag == 1:                      # 0x42f375: the opponent first
                    first, second = other, g.own_team()
                else:
                    first, second = g.own_team(), other
                g.say2(" " + first + T.VERSES_THE + second)   # 0x42f582
                g.dy(0.2, 0x42f5c6)
            if season.gtp > 1:                           # 0x42f645: the question only before week 1 is played
                return
            g.dy(0.2, 0x42f673)
            self.keys.clk()                              # 0x42f69a
            verdict = self._schedule_question()
            if verdict == SCHEDULE_LIKED:
                return
            if verdict == SCHEDULE_REJECTED:
                g.make_schedule()                        # 0x42f957: makes, then the whole schedule again
            # SCHEDULE_AGAIN (F1, 0x42f814): the whole schedule again, unchanged

    def _schedule_question(self) -> str:
        """0x42f6e5 to 0x42f94e: the question with " yes " in it; Up, Down and Tab toggle and speak the answer; Enter
        takes it; y and n answer; F1 speaks the whole schedule again; any other key is echoed and the answer spoken."""
        g = self.g
        g.say5(" " + g.season.coach + T.LIKE_THIS_SCHEDULE)   # 0x42f6fa
        answer = YES                                     # 0x42f72f
        while True:                                      # L_42f73b
            code = self._getkey()                        # 0x42f73e
            if code == KEY_ENTER:
                return SCHEDULE_LIKED if answer == YES else SCHEDULE_REJECTED   # L_42f926
            if code in (KEY_TAB, KEY_UP, KEY_DOWN):
                answer = NO if answer == YES else YES    # L_42f796
            elif code == KEY_F1:
                return SCHEDULE_AGAIN                    # 0x42f814: back to L_42efd2
            else:
                g.saykey()                               # 0x42f81d
                if self.keys.char == "y":
                    return SCHEDULE_LIKED                # L_42f8f0
                if self.keys.char == "n":
                    return SCHEDULE_REJECTED             # L_42f906
            self._answer(answer, g.say5)                 # L_42f85b: 0x42f8a0 " yes ", 0x42f8c7 " no "

    def _say_playoff_games(self) -> None:
        """gtp 17 to 20: one say4 text, " games for the <week name> are. " and " the <A> verses the <B>. " for every
        game of footbal4.dat in its order (0x42ecd4 to 0x42efab)."""
        g, season = self.g, self.g.season
        text = T.GAMES_FOR_THE + T.PLAYOFF_WEEK_NAMES.get(season.gtp, "") + T.ARE
        for first, second in season.playoffs.pairings:
            text += (T.THE + g.league.team(first.division, first.place) + T.VERSES_THE
                     + g.league.team(second.division, second.place) + T.END)
        g.say4(text)                                     # 0x42efab
