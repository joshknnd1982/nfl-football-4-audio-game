"""Injuries of the Franchise in the program: a game's rosters and its injuries, the week's report, the question before a game, F9's list (nfl4 only,
rule 0.13). This is inspired by Jim Kitchen.

NFL_EXTRA_FEATURES INJ-2 to INJ-5 and NFL_FRANCHISE_DESIGN 17 SX.8k (as built: entry 1.11, D-071). The rules are `injuries.py`; this module turns them
into the program's speech and the game's rosters. FRANCHISE ONLY: a `GameInjuries` is made only by the franchise's `game_arguments`, and the play
engine reaches it only through `Game.game_injuries` (None in every other game: ClassicRules and NflRules then do nothing, draw nothing, say nothing).

* `GameInjuries`: the two teams of the player's game. Its rosters are the lineups of the week (the hurt players are not in them, so the place draws skip
  them; a hurt player who plays plays below his best). In a game of weeks 1 to FR_INJ_LAST_WEEK every play that can hurt a player (INJ-3: a rush, a catch,
  a sack, a quarterback's run, a kick-off return) draws `below(10000)` against FR_INJ_PLAY; a hit hurts the tackler (`below(100)` against FR_INJ_TACKLER;
  the first defender named) or the ball carrier, the announcer says so (a line of IJX of injuries.txt) and his place goes to the next man up at once (the
  rosters of the game are rewritten; a quarterback's place goes to the stand-in, made then with a name draw when the team has none). The game's injuries
  are kept in the game's extras record (`ExtrasRecord.injuries`), so Save Game keeps them, and join the league with the game's result (`commit`, from
  H14's game_played). `after_draws` (the snap's hook) keeps the two tacklers two men when the next man up plays two places.
* `report_lines`: the week's injury report of the player's team (INJ-4: who is out, doubtful, questionable, who is back), made in the preparation.
"""
from __future__ import annotations

from ...game import outcome as O
from ...game.gamestate import other
from ...game.setup import Roster
from .. import nx_texts as X
from .. import tuning as T
from . import data as D
from . import injuries as I
from .injury_pools import DEFAULT_POOLS, make_line
from .league import LeagueRecord

SECTIONS = {"Running Backs:": "running_backs", "Receivers:": "receivers", "Defensive Players:": "defense",
            "Special Teams Players:": "special_teams", "Kickers:": "kickers"}
QB_PLACE = D.PLACES_OF["QB"][0]
DEFENSE_FIRST = D.PLACES_OF["DL"][0]
RB_FIRST, WR_FIRST, RET_FIRST = D.PLACES_OF["RB"][0], D.PLACES_OF["WR"][0], D.PLACES_OF["RET"][0]


def _plain(text: str) -> str:
    return text.replace("[", "(").replace("]", ")")


def write_roster(roster: Roster, table: list) -> None:
    """The names and ratings of a lineup into a game's Roster, in place (the game holds this object)."""
    sections = {attribute: [] for attribute in SECTIONS.values()}
    for index, (heading, number, _position) in enumerate(D.PLACES):
        _identity, name, rating = table[index]
        roster.ratings[(heading, number)] = rating
        if heading == "Quarterback:":
            roster.quarterback = name
        else:
            sections[SECTIONS[heading]].append(name)
    for attribute, names in sections.items():
        getattr(roster, attribute)[:] = names


def lineup_roster(league: LeagueRecord, team: int, week: int, staff: bool) -> Roster:
    """The team's Roster for the game of `week`: league.roster_for_game with the week's lineup (equal to it when nobody is hurt)."""
    roster = league.roster_for_game(team)
    if not I.nobody_hurt(league) or league.injuries["stand_ins"]:
        write_roster(roster, I.lineup(league, team, week, staff))
    return roster


class GameInjuries:
    def __init__(self, league: LeagueRecord, own: int, opponent: int, week: int, staff: bool, rnd, surnames: list, words, pools=None, say=None):
        self.league = league
        self.teams = (own, opponent)                   # side 1, side 2
        self.week = week
        self.staff = staff
        self.rnd = rnd
        self.surnames = surnames
        self.words = words
        self.pools = pools or DEFAULT_POOLS
        self.say = say                                 # the game's speech for the announcer's lines (Game.say2 and the banter player)
        self.exposed = 1 <= week <= T.FR_INJ_LAST_WEEK
        self.state = None
        self.identity = {1: [], 2: []}
        I.lineup_decided(league, own, week, staff)     # the kick-off: who of the player's hurt players plays is written into the rows

    def swap_sides(self) -> None:
        """A rig that plays the player's team as side 2 (the whole-program run's stand-in, work/full_sx8f.py) turns the sides before the game starts."""
        self.teams = (self.teams[1], self.teams[0])

    # ----- the record in the game's extras (Save Game keeps it) -----

    @property
    def record(self) -> dict:
        extras = self.state.extras
        if getattr(extras, "injuries", None) is None:
            extras.injuries = {"hurt": [], "stand_ins": []}
        return extras.injuries

    def out(self, side: int) -> frozenset:
        team = self.teams[side - 1]
        return frozenset(row[0] for row in self.record["hurt"] if self.league.players[row[0]].team == team)

    def staff_of(self, side: int) -> bool:
        return self.staff if self.teams[side - 1] == self.league.team else True

    def refresh(self, side: int) -> None:
        team = self.teams[side - 1]
        table = I.lineup(self.league, team, self.week, self.staff_of(side), out=self.out(side), extra_stand_ins=self.record["stand_ins"],
                         make=lambda position: self.make_stand_in(team, position))
        write_roster(self.state.rosters[side], table)
        self.state.quarterbacks[side] = table[QB_PLACE][1]
        self.identity[side] = [entry[0] for entry in table]

    def make_stand_in(self, team: int, position: str) -> list:
        """A place of the game in progress has nobody to play it: the team's stand-in is signed now (a name draw), kept in the game's record."""
        row = I.make_stand_in(self.league, team, position, self.rnd, self.surnames, self.record["stand_ins"])
        self.record["stand_ins"].append(row)
        return row

    def quarterbacks(self, state) -> tuple:
        """The `quarterback_names` of the game (called once, after a saved game was loaded): the rosters of both sides as the week's lineups with the
        game's own injuries so far (a loaded game keeps them), and the two quarterbacks. Without a game state (a caller that only asks the names): the
        week's quarterbacks of the two lineups."""
        if state is None:
            return tuple(I.lineup(self.league, team, self.week, self.staff_of(side))[QB_PLACE][1] for side, team in ((1, self.teams[0]), (2, self.teams[1])))
        self.state = state
        if not isinstance(state.quarterbacks, dict):
            state.quarterbacks = {}
        record = self.record                           # a loaded game's injuries must be players of these two teams (else they are left out)
        record["hurt"][:] = [row for row in record["hurt"] if self.fits(row)]
        record["stand_ins"][:] = [row for row in record["stand_ins"] if row[0] in self.teams and row[1] in D.POSITIONS and isinstance(row[2], str)
                                  and 1 <= len(row[2]) <= 40 and not any(ord(c) < 32 for c in row[2]) and D.RATING_MIN <= row[3] <= D.RATING_MAX]
        for side in (1, 2):
            self.refresh(side)
        return state.quarterbacks[1], state.quarterbacks[2]

    def fits(self, row) -> bool:
        """A loaded game's injury is used only when the league's own check would take it (a damaged saved game must never make league.sav
        unwritable, the review of SX.8k): a player of the two teams, a kind, the games and the offset of an injury of that kind."""
        pid, kind, games, offset = row
        player = self.league.players.get(pid)
        return (player is not None and player.status == "active" and player.team in self.teams and kind in I.KIND_IDS
                and isinstance(games, int) and 1 <= games <= I.max_games() and isinstance(offset, int) and 0 <= offset <= I.width_for(games))

    # ----- the hooks -----

    def after_draws(self, state) -> None:
        """The snap's hook: the two tacklers drawn are two places that may be played by one man (the next man up plays two places): the second becomes
        the next place, down the defense list, that another man plays. Nobody hurt: every place is another man and nothing changes."""
        if self.state is None:
            return
        state.defender2 = self.other_man(state.defense, state.defender1, state.defender2)

    def other_man(self, side: int, first: int, second: int) -> int:
        """Defenders `first` and `second` (1 to 17) of `side` as two men: the second, or the next place down the defense list that another man plays."""
        ids = self.identity[side][DEFENSE_FIRST:DEFENSE_FIRST + 17]
        if not ids or ids[first - 1] != ids[second - 1]:
            return second
        for step in range(1, 17):
            number = (second - 1 + step) % 17 + 1
            if number != first and ids[number - 1] != ids[first - 1]:
                return number
        return second

    def exposed_places(self, outcome, state=None) -> tuple | None:
        """(the side and place of the ball carrier, whether a tackler is hurt in his place by the draw) of a play that can hurt a player, else None. A
        kick-off's returner is the state's `returner` (1 or 2): the record's carrier is the last snap's."""
        if outcome.then is not None or outcome.two_point_try:
            return None
        side = outcome.offense
        if outcome.kind == O.RUN:
            return side, (QB_PLACE if outcome.qb_run else RB_FIRST + outcome.carrier - 1), True
        if outcome.kind == O.PASS_COMPLETE:
            return side, WR_FIRST + outcome.carrier - 1, True
        if outcome.kind == O.SACK:
            return side, QB_PLACE, True
        if outcome.kind == O.KICKOFF_RETURN:
            returner = getattr(state if state is not None else self.state, "returner", 1)
            return side, RET_FIRST + (returner if returner in (1, 2) else 1) - 1, False
        return None

    def after_play(self, state, outcome) -> None:
        """INJ-3: the draws of a play that can hurt a player, in a game of weeks 1 to FR_INJ_LAST_WEEK."""
        if not self.exposed or self.state is None:
            return
        found = self.exposed_places(outcome, state)
        if found is None:
            return
        side, place, tackled = found
        if self.rnd.below(10000) >= T.FR_INJ_PLAY:
            return
        if tackled and self.rnd.below(100) < T.FR_INJ_TACKLER:
            side, place = other(side), DEFENSE_FIRST + outcome.defender1 - 1
        identity = self.identity[side][place]
        if not isinstance(identity, int):
            return                                      # a stand-in is not hurt
        team = self.teams[side - 1]
        if identity in self.out(side):
            return
        more = sum(1 for row in self.record["hurt"] if self.league.players[row[0]].team == team and I.healthy(self.league, row[0], self.week + 1))
        if I.at_limit(self.league, team, identity, self.week, more):
            return                                      # INJ-6: the team has as many hurt as a team may have
        player = self.league.players[identity]
        kind, games, offset = I.draw_injury(self.rnd, player.pos)
        self.record["hurt"].append([identity, kind, games, offset])
        before_qb = self.state.quarterbacks.get(side, "")
        self.refresh(side)
        self.announce(player, team)
        if player.pos == "QB" and self.state.quarterbacks.get(side, "") != before_qb:
            self.say_text(X.text("NXI-30", player=self.state.quarterbacks[side], position=self.words.position("QB")))

    def announce(self, player, team: int) -> None:
        values = {"<player>": _plain(player.name), "<position>": self.words.position(player.pos), "<team>": _plain(self.words.team_name(team))}
        markup = make_line(self.pools, "IJX", values, self.rnd)
        if markup is not None:
            self.say_markup(markup)

    def say_text(self, text: str) -> None:
        if self.say is not None:
            self.say(text, plain=True)

    def say_markup(self, markup: str) -> None:
        if self.say is not None:
            self.say(markup, plain=False)

    # ----- the end of the game -----

    def commit(self) -> None:
        """The game's injuries and stand-ins join the league (with the result of the game: H14's game_played)."""
        if self.state is None:
            return
        record = self.record
        for row in record["stand_ins"]:
            if I.stand_in(self.league, row[0], row[1]) is None:
                self.league.injuries["stand_ins"].append(list(row))
        for pid, kind, games, offset in record["hurt"]:
            I.injure(self.league, pid, kind, games, offset, self.week)
        record["hurt"], record["stand_ins"] = [], []


# ----- the week's report (made in the preparation, told after the news) -----

def _status_line(words, player, row, week: int, injury: str | None) -> str:
    """One line of the report: the named lines for an injury of last week (with the kind's name when a line of its pool is on), the plain ones after."""
    state = I.status_of_row(row, week)
    values = dict(player=_plain(player.name), position=words.position(player.pos))
    if injury is not None:
        values["injury"] = injury
    if state == D.STATUS_DOUBTFUL:
        return X.text("NXI-13" if injury is not None else "NXI-18", **values)
    if state == D.STATUS_QUESTIONABLE:
        return X.text("NXI-14" if injury is not None else "NXI-19", **values)
    low, high = I.spoken_range(row, week)
    if row[3] > D.SUPER_BOWL_WEEK:                              # back only after the Super Bowl (a player back for the play-offs is told his weeks)
        return X.text("NXI-12" if injury is not None else "NXI-17", **values)
    if low == high:
        return X.text("NXI-11" if injury is not None else "NXI-16", n=low, **values)
    return X.text("NXI-10" if injury is not None else "NXI-15", lo=low, hi=high, **values)


def injury_name(pools, kind: str, rnd) -> str | None:
    markup = make_line(pools, kind, {}, rnd)
    return None if markup is None else markup.strip()


def report_lines(league: LeagueRecord, week: int, back: list, words, pools, rnd, staff: bool = False) -> list:
    """The player's team's report before the game of `week`: every player who is not fit (an injury of last week's game first, with its name: one draw
    of its pool), then the stand-ins who play, then who is back. [] when there is nothing to tell."""
    pools = pools or DEFAULT_POOLS
    team = league.team
    hurt = I.hurt_of(league, team, week)
    fresh = [(p, s) for p, s in hurt if I.row_of(league, p.id)[2] == week - 1]
    older = [(p, s) for p, s in hurt if I.row_of(league, p.id)[2] != week - 1]
    lines = []
    for player, _state in fresh:
        row = I.row_of(league, player.id)
        lines.append(_status_line(words, player, row, week, injury_name(pools, row[1], rnd)))
    for player, _state in older:
        lines.append(_status_line(words, player, I.row_of(league, player.id), week, None))
    table = I.lineup(league, team, week, staff)
    for position in D.ROSTER_ORDER:                             # the stand-ins who play this week as the decisions stand (rested players rest)
        if any(table[i][0] == (I.STAND_IN, position) for i in D.PLACES_OF[position]):
            row = I.stand_in(league, team, position)
            lines.append(X.text("NXI-21", player=_plain(row[2]), position=words.position(position)))
    names = [_plain(league.players[pid].name) for pid in back if pid in league.players and league.players[pid].team == team]
    if names:
        lines.append(X.text("NXI-20", list=", ".join(names)))
    return lines


def headline(league: LeagueRecord, week: int):
    """NWJ, the news of another team's injury: the best player of another team hurt in last week's game who is out (equal ratings: the lower id), or None.
    The event's n is the high end of his range."""
    from .news import Event
    best = None
    for row in league.injuries["hurt"]:
        player = league.players[row[0]]
        if player.team == league.team or row[2] != week - 1 or I.status_of_row(row, week) != D.STATUS_OUT:
            continue
        if best is None or (player.rating, -player.id) > (best[0].rating, -best[0].id):
            best = (player, row)
    if best is None:
        return None
    player, row = best
    return Event("NWJ", team=player.team, player=player, n=I.spoken_range(row, week)[1])


def say_report(p, league) -> None:
    """The week's report, once (told mark), after the news (design 3.4)."""
    report = league.injuries.get("report")
    if not report or report["told"] or report["season"] != league.season or report["week"] != league.gtp:
        return
    from .weekly import say_markup
    p.g.say2(X.text("NXI-01"))
    for line in report["lines"]:
        say_markup(p.g, line)
    report["told"] = 1
    p.store.save()


# ----- the question before a game (a to-do item) and F9 -----

def item(league: LeagueRecord, week: int, pid: int) -> dict:
    return {"kind": D.TODO_INJURY, "season": league.season, "week": week, "state": D.ITEM_NEW, "player": pid}


def answers_order(league: LeagueRecord, item_: dict) -> tuple:
    """(play?) of the item's two answers in order: the staff's recommendation first (play a questionable player, rest a doubtful one)."""
    state = I.status(league, item_["player"], item_["week"])
    return (True, False) if I.staff_plays(state) else (False, True)


def item_view(words, league: LeagueRecord, item_: dict) -> tuple:
    player = league.players[item_["player"]]
    state = I.status(league, player.id, item_["week"])
    situation = [X.text("NXI-40" if state == D.STATUS_DOUBTFUL else "NXI-41", player=_plain(player.name), position=words.position(player.pos))]
    answers = [X.text("NXI-A01" if play else "NXI-A02") for play in answers_order(league, item_)]
    return situation, answers


def result_text(league: LeagueRecord, pid: int, play: bool) -> str:
    return X.text("NXI-42" if play else "NXI-43", player=_plain(league.players[pid].name))


def list_lines(words, league: LeagueRecord, week: int, staff: bool) -> list:
    """F9, franchise, injury report: (the line, the player id when Enter changes whether he plays, else None) for each player of the team who is not fit."""
    out = []
    for player, state in I.hurt_of(league, league.team, week):
        line = _status_line(words, player, I.row_of(league, player.id), week, None)
        if state in (D.STATUS_DOUBTFUL, D.STATUS_QUESTIONABLE):
            line += X.text("NXI-51" if I.plays(league, player, week, staff) else "NXI-52")
            out.append((line, player.id))
        else:
            out.append((line, None))
    return out
