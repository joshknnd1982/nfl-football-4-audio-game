"""F9, Franchise, injured reserve: the player places a hurt man on the list, designates him to return and activates him (nfl4 only, rule 0.13; rule 0.40,
D-216). This is inspired by Jim Kitchen.

The menu (Up, Down, digits, Enter, Escape, F1, like every F9 menu; never T):
  1. place a hurt player on injured reserve: his hurt men of the 53, the one chosen goes on the list after one Enter (any other key leaves him);
  2. your players on the reserve lists: each man with his list, the week he went there, the games he has missed and his window; Enter does the next step
     for him: designate him to return (one Enter), or activate him (one Enter; when the 53 is full, the man to release first, then one Enter), or says why
     not yet (too early, still hurt, no returns left, out for the season);
  3. the rules of injured reserve, in plain words.
Every move is made and written, then said (B-X53). The rules are reserve.py; this module speaks.
"""
from __future__ import annotations

from ...data import debuglog
from ...game.keys import KEY_ENTER
from ...game.spoken_menu import Item, ListPicker, SpokenMenu
from .. import nx_texts as X
from .. import roster_file as RF
from .. import tuning as T
from . import contracts as CT
from . import injuries
from . import real_roster
from . import reserve as R


def rules_lines() -> list:
    return [X.text("NXI-R33", n=T.FR_IR_MIN_GAMES), X.text("NXI-R34", n=T.FR_IR_DESIGNATE_AFTER, m=T.FR_IR_WINDOW_WEEKS),
            X.text("NXI-R35", n=T.FR_IR_MIN_GAMES), X.text("NXI-R36", n=T.FR_IR_RETURNS, m=T.FR_IR_PLAYOFF_RETURNS, k=T.FR_IR_MAN_RETURNS),
            X.text("NXI-R37", n=T.FR_IR_MIN_GAMES), X.text("NXI-R38")]


def hurt_line(words, league, player, week: int) -> str:
    row = injuries.row_of(league, player.id)
    games = injuries.left(row, week) if row is not None else 0
    return X.text("NXI-R07", player=player.name, position=words.position_for(player), r=player.rating, n=max(0, games))


def list_line(words, league, player, week: int) -> str:
    """A man on a reserve list: his list, since when, the games missed, and his window or the end of his season."""
    code = "IR" if player.roster_list in R.ON_IR else player.roster_list
    line = X.text("NXI-R11", player=player.name, position=words.position_for(player), list=RF.RESERVE.get(code, code), w=R.placed_week(league, player),
                  n=R.missed(league, player, week))
    if player.roster_list in R.ON_IR:
        if R.ended(league, player, week):
            line += X.text("NXI-R13")
        elif R.designated_week(league, player):
            line += X.text("NXI-R12", n=R.window_left(league, player, week))
    row = injuries.row_of(league, player.id)
    if row is not None and injuries.left(row, week) > 0:
        line += X.text("NXI-R39", n=injuries.left(row, week))
    return line.rstrip() + "."


def report_lines(league, week: int) -> list:
    """The week's injury report (weekly.prepare): the player's men whose practice window closed without an activation (no draw)."""
    if not R.in_season(league):
        return []
    return [X.text("NXI-R28", player=p.name) for p in R.close_windows(league, week)]


def reserve_menu(g, speech, keys, store, words) -> None:
    league = store.league

    def say(text: str) -> None:
        speech.stop()
        speech.say_async(text)

    def confirmed(text: str) -> bool:
        say(text)
        return keys.read_key() == KEY_ENTER

    def pick_from(title: str, lines: list):
        return ListPicker(speech, keys, title, len(lines), lambda i: lines[i]).run()

    def closed() -> str | None:
        if g.play_engine is not None:
            return X.text("NXI-R31")
        if not R.in_season(league):
            return X.text("NXI-R32")
        return None

    def title() -> str:
        week = league.gtp
        return X.text("NXI-R02", n=R.returns_used(league), m=R.returns_allowed(league, week))

    def place_one():
        reason = closed()
        if reason is not None:
            return reason
        week = league.gtp
        hurt = [p for p in league.team_men(league.team) if R.place_problem(league, p, week) in (None, "too few of his family left")]
        if not hurt:
            return X.text("NXI-R10")
        index = pick_from(X.text("NXI-R06"), [hurt_line(words, league, p, week) for p in hurt])
        if index is None:
            return None
        player = hurt[index]
        if R.place_problem(league, player, week) == "too few of his family left":
            return X.text("NXI-R30", player=player.name)
        if not confirmed(X.text("NXI-R08", player=player.name, n=T.FR_IR_MIN_GAMES)):
            return X.text("NXI-R40", player=player.name)
        R.place(league, player, week)
        debuglog.event("franchise", "reserve_placed", season=league.season, week=week, player=player.id, position=player.position or player.pos)   # rule 0.15
        store.save()                                              # made and written, then told (B-X53)
        return X.text("NXI-R09", player=player.name, n=real_roster.room(league, league.team))

    def designate(player, week):
        if not confirmed(X.text("NXI-R16", player=player.name, n=R.returns_left(league, week), m=T.FR_IR_WINDOW_WEEKS)):
            return X.text("NXI-R40", player=player.name)
        R.designate(league, player, week)
        debuglog.event("franchise", "reserve_designated", season=league.season, week=week, player=player.id, used=R.returns_used(league))      # rule 0.15
        store.save()
        return X.text("NXI-R17", player=player.name, n=R.window_left(league, player, week), m=T.FR_IR_MIN_GAMES)

    def activate(player, week):
        release = None
        if real_roster.room(league, league.team) <= 0:
            candidates = R.releasable(league, player, week)
            if not candidates:
                return X.text("NXI-R41")
            from .signings_flow import release_line
            chosen = pick_from(X.text("NXI-R21", player=player.name), [release_line(words, p) for p in candidates])
            if chosen is None:
                return None
            release = candidates[chosen]
            if R.activate_problem(league, player, week, release) is not None:
                return X.text("NXI-R42")
            asked = X.text("NXI-R22", give=release.name, get=player.name, dead=words.amount(CT.dead_money(release)))
        else:
            asked = X.text("NXI-R18", player=player.name)
        if not confirmed(asked):
            return X.text("NXI-R40", player=player.name)
        gone = release.name if release is not None else ""
        dead = R.activate(league, player, week, release)
        debuglog.event("franchise", "reserve_activated", season=league.season, week=week, player=player.id,
                       released=release.id if release is not None else None, dead_money=dead)                      # rule 0.15
        store.save()
        return X.text("NXI-R19", player=player.name) if release is None else X.text("NXI-R20", give=gone, get=player.name)

    def next_step(player):
        """Enter on a man of the lists: the step the rules allow now, or why not."""
        reason = closed()
        if reason is not None:
            return reason
        week = league.gtp
        R.close_windows(league, week)
        if player.roster_list in R.ON_IR and not R.designated_week(league, player):
            problem = R.designate_problem(league, player, week)
            if problem is None:
                return designate(player, week)
            return why(problem, player, week, designating=True)
        problem = R.activate_problem(league, player, week)
        if problem in (None, "no room"):
            return activate(player, week)
        return why(problem, player, week, designating=False)

    def why(problem: str, player, week: int, designating: bool) -> str:
        debuglog.event("franchise", "reserve_refused", week=week, player=player.id, why=problem)                         # rule 0.15
        if problem == "out for the season":
            return X.text("NXI-R28", player=player.name)
        if problem == "too early":
            need = T.FR_IR_DESIGNATE_AFTER if designating else T.FR_IR_MIN_GAMES
            return X.text("NXI-R23" if designating else "NXI-R24", player=player.name, n=R.missed(league, player, week), m=need)
        if problem == "still hurt":
            row = injuries.row_of(league, player.id)
            return X.text("NXI-R25", player=player.name, n=max(1, injuries.left(row, week) if row is not None else 1))
        if problem == "no returns left":
            return X.text("NXI-R26")
        if problem == "he returned twice":
            return X.text("NXI-R27", player=player.name, n=T.FR_IR_MAN_RETURNS)
        return X.text("NXI-R42")

    def the_lists():
        week = league.gtp
        if R.in_season(league):
            R.close_windows(league, week)
        men = R.on_list(league)
        if not men:
            return X.text("NXI-R15")
        lines = [list_line(words, league, p, week) for p in men]

        def enter(index: int):
            text = next_step(men[index])
            men[:] = R.on_list(league)
            lines[:] = [list_line(words, league, p, league.gtp) for p in men]
            return text
        ListPicker(speech, keys, X.text("NXI-R04"), len(lines), lambda i: lines[i] if i < len(lines) else "", on_enter=enter, close_on_enter=False).run()
        return None

    def the_rules():
        lines = rules_lines()
        ListPicker(speech, keys, X.text("NXI-R05"), len(lines), lambda i: lines[i], close_on_enter=False).run()
        return None

    items = [Item(lambda: X.text("NXI-R03"), enter=place_one),
             Item(lambda: X.text("NXI-R04"), enter=the_lists),
             Item(lambda: X.text("NXI-R05"), enter=the_rules)]
    SpokenMenu(speech, keys, title(), items, space_enters=True, digits_jump=True).run()


__all__ = ["reserve_menu", "report_lines", "list_line", "rules_lines"]
