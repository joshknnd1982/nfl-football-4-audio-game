"""The N. F. L.'s tie-breaking procedures for the standings and the play-off seeds (nfl4 only, rule 0.13; S-E3, D-202, Q-070). This is inspired by
Jim Kitchen.

A franchise on the real calendar (SZ.8) orders each division and seeds its 14-team play-offs (D-138) by the league's own procedures, read from
the NFL's page "NFL Tiebreaking Procedures" (nfl.com/standings/tie-breaking-procedures, read 2026-11-06, SRC-OFFICIAL; spec NFL_EXTRA_FEATURES
section 24, NX-T5). Classic and a franchise on the original's 16 weeks keep the original's order (game/playoffs.py), untouched.

What is modelled (every step SRC-OFFICIAL unless marked):
* the won-lost-tied percentage first, a tie game half a win and half a loss;
* a tie inside a division: two clubs: head-to-head, division, common games, conference, strength of victory, strength of schedule, the combined
  ranking in points scored and allowed among the conference's teams, then among all teams, net points in common games, net points in all games,
  (net touchdowns), a coin toss; three or more clubs: the same steps, head-to-head as the percentage in the games among the clubs;
* a tie for a wild card: clubs of one division take the division tie-breaker; otherwise two clubs: head-to-head if they played, conference,
  common games (at least four), strength of victory, strength of schedule, the two combined rankings, net points in conference games, net points
  in all games, (net touchdowns), a coin toss; three or more clubs: first all but the best club of each division are set aside by the division
  order, then a head-to-head sweep, then the two-club list from the conference step;
* only one club comes out of a step at a time: when a step leaves two clubs the two-club list starts again at step 1; when it leaves three of
  four, the three-club list starts again (a division: at step 1; a wild card: at step 2); after a club wins, the rest start again;
* the division winners are seeded 1 to 4 by the wild card tie-breakers, the wild cards 5 to 7 in the order they were chosen.
Not modelled: net touchdowns (the season keeps no touchdowns of the computer's games: the step is passed, D-202). The coin toss is not a draw of
the game's random generator: it is a fixed order made from the league's name, the season and the clubs (SHA-256), so the seeds are the same every
time they are worked out (a round resumed from the files) and no game's draws move (B-X162). Strength of victory and of schedule count an
opponent once per game played (SRC-SECONDARY: the usual reading; the NFL's page does not say).

No speech, sound or file code is here. `Game` rows come from the franchise's results (H14), regular season only.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Callable, Iterable, NamedTuple, Sequence

from .league import DIVISIONS, PLACES


class Ref(NamedTuple):            # the same shape as playoffs.TeamRef (division 1 to 8, place 1 to 4)
    division: int
    place: int


class Game(NamedTuple):
    """One regular-season game: two teams and their scores (equal scores: a tie)."""
    first: tuple
    second: tuple
    first_score: int
    second_score: int


def conference_of(team) -> int:
    """0 the A. F. C. (divisions 1 to 4), 1 the N. F. C. (5 to 8)."""
    return 0 if team[0] <= 4 else 1


def all_teams() -> list[Ref]:
    return [Ref(d, p) for d in range(1, DIVISIONS + 1) for p in range(1, PLACES + 1)]


@dataclass
class Table:
    """Every team's games (opponent, own score, opponent's score) and its whole record (wins, losses, ties) as the season's records keep it."""
    records: Callable           # team -> (wins, losses, ties)
    games: dict = field(default_factory=dict)
    coin_key: str = ""
    notes: list = field(default_factory=list)       # one line per tie broken, for the debug log (rule 0.15)

    @classmethod
    def build(cls, records, games: Iterable[Game], coin_key: str = "") -> "Table":
        table = cls(records, {Ref(*t): [] for t in all_teams()}, coin_key)
        for game in games:
            a, b = Ref(*game.first), Ref(*game.second)
            if a not in table.games or b not in table.games or a == b:
                continue
            table.games[a].append((b, game.first_score, game.second_score))
            table.games[b].append((a, game.second_score, game.first_score))
        return table

    # ----- percentages and points -----

    def pct(self, team) -> Fraction:
        wins, losses, ties = self.records(team)
        played = wins + losses + ties
        return Fraction(2 * wins + ties, 2 * played) if played else Fraction(0)

    def pct_against(self, team, opponents) -> Fraction | None:
        """The percentage in the team's games against `opponents` (a set), or None when it played none of them."""
        points = played = 0
        for opponent, own, other in self.games[team]:
            if opponent in opponents:
                played += 1
                points += 2 if own > other else (1 if own == other else 0)
        return Fraction(points, 2 * played) if played else None

    def played_against(self, team, opponents) -> int:
        return sum(1 for opponent, _, _ in self.games[team] if opponent in opponents)

    def net_against(self, team, opponents=None) -> int:
        return sum(own - other for opponent, own, other in self.games[team] if opponents is None or opponent in opponents)

    def strength(self, team, victories: bool) -> Fraction:
        """Strength of victory (the opponents it beat) or of schedule (every opponent), one count a game: their whole percentage."""
        points = played = 0
        for opponent, own, other in self.games[team]:
            if victories and own <= other:
                continue
            wins, losses, ties = self.records(opponent)
            points += 2 * wins + ties
            played += 2 * (wins + losses + ties)
        return Fraction(points, played) if played else Fraction(0)

    def combined_rank(self, team, teams) -> int:
        """Its place in points scored plus its place in points allowed among `teams`; a shared place counts as held alone (the page's example)."""
        scored = {t: sum(own for _, own, _ in self.games[t]) for t in teams}
        allowed = {t: sum(other for _, _, other in self.games[t]) for t in teams}
        return (1 + sum(1 for t in teams if scored[t] > scored[team])) + (1 + sum(1 for t in teams if allowed[t] < allowed[team]))

    def coin(self, clubs) -> list:
        """The coin toss: a fixed order of the clubs (not a draw of the game), the first wins."""
        return sorted(clubs, key=lambda t: hashlib.sha256(("%s|%d|%d" % (self.coin_key, t[0], t[1])).encode("utf-8")).hexdigest())


# ----- the steps: each keeps the clubs with the best value, or all of them when the step does not apply -----

def _keep_best(clubs: list, value: Callable) -> list:
    values = {club: value(club) for club in clubs}
    if any(v is None for v in values.values()):
        return clubs
    best = max(values.values())
    return [club for club in clubs if values[club] == best]


def head_to_head(t: Table, clubs: list) -> list:
    """The percentage in the games among the clubs; a club that played none of the others: the step does not apply."""
    others = set(clubs)
    return _keep_best(clubs, lambda c: t.pct_against(c, others - {c}))


def head_to_head_sweep(t: Table, clubs: list) -> list:
    """Three or more clubs for a wild card: a club that beat each of the others wins; a club that lost to each of the others is set aside."""
    def record_against(club, other):
        rows = [(own, theirs) for opponent, own, theirs in t.games[club] if opponent == other]
        return rows
    for club in clubs:
        rows = [record_against(club, other) for other in clubs if other != club]
        if all(r and all(own > theirs for own, theirs in r) for r in rows):
            return [club]
    swept = [club for club in clubs
             if all((r := record_against(club, other)) and all(own < theirs for own, theirs in r) for other in clubs if other != club)]
    if swept and len(swept) < len(clubs):
        return [club for club in clubs if club not in swept]
    return clubs


def division_games(t: Table, clubs: list) -> list:
    return _keep_best(clubs, lambda c: t.pct_against(c, {Ref(c[0], p) for p in range(1, PLACES + 1)} - {c}))


def conference_games(t: Table, clubs: list) -> list:
    return _keep_best(clubs, lambda c: t.pct_against(c, {x for x in all_teams() if conference_of(x) == conference_of(c)} - {c}))


def _common(t: Table, clubs: list) -> set:
    sets = [{opponent for opponent, _, _ in t.games[c]} for c in clubs]
    return set.intersection(*sets) - set(clubs) if sets else set()


def common_games(t: Table, clubs: list, minimum: int = 1) -> list:
    common = _common(t, clubs)
    if any(t.played_against(c, common) < minimum for c in clubs):
        return clubs
    return _keep_best(clubs, lambda c: t.pct_against(c, common))


def common_games_four(t: Table, clubs: list) -> list:
    return common_games(t, clubs, 4)


def strength_of_victory(t: Table, clubs: list) -> list:
    return _keep_best(clubs, lambda c: t.strength(c, True))


def strength_of_schedule(t: Table, clubs: list) -> list:
    return _keep_best(clubs, lambda c: t.strength(c, False))


def rank_conference(t: Table, clubs: list) -> list:
    return _keep_best(clubs, lambda c: -t.combined_rank(c, [x for x in all_teams() if conference_of(x) == conference_of(c)]))


def rank_league(t: Table, clubs: list) -> list:
    return _keep_best(clubs, lambda c: -t.combined_rank(c, all_teams()))


def net_common(t: Table, clubs: list) -> list:
    common = _common(t, clubs)
    if not common:
        return clubs
    return _keep_best(clubs, lambda c: t.net_against(c, common))


def net_conference(t: Table, clubs: list) -> list:
    return _keep_best(clubs, lambda c: t.net_against(c, {x for x in all_teams() if conference_of(x) == conference_of(c)} - {c}))


def net_all(t: Table, clubs: list) -> list:
    return _keep_best(clubs, lambda c: t.net_against(c))


def coin_toss(t: Table, clubs: list) -> list:
    return t.coin(clubs)[:1]


# The lists of the NFL's page, in order (net touchdowns is passed: D-202).
DIVISION_STEPS = (("head-to-head", head_to_head), ("division record", division_games), ("common games", common_games),
                  ("conference record", conference_games), ("strength of victory", strength_of_victory),
                  ("strength of schedule", strength_of_schedule), ("conference points ranking", rank_conference),
                  ("league points ranking", rank_league), ("net points in common games", net_common), ("net points", net_all),
                  ("coin toss", coin_toss))
WILD_TWO_STEPS = (("head-to-head", head_to_head), ("conference record", conference_games), ("common games", common_games_four),
                  ("strength of victory", strength_of_victory), ("strength of schedule", strength_of_schedule),
                  ("conference points ranking", rank_conference), ("league points ranking", rank_league),
                  ("net points in conference games", net_conference), ("net points", net_all), ("coin toss", coin_toss))
WILD_THREE_STEPS = (("head-to-head sweep", head_to_head_sweep),) + WILD_TWO_STEPS[1:]


@dataclass
class Note:
    """One tie broken: what the place was (`context`, e.g. ("division", 3, 0) the title of division 3, ("wild", 0, 2) the A. F. C.'s third wild
    card), the club that won it, and each club set aside with the step that set it aside (a club set aside by a division's order: "division
    order")."""
    context: tuple
    winner: Ref | None = None
    set_aside: list = field(default_factory=list)      # (club, step name)

    def step_against(self, club) -> str | None:
        return next((step for c, step in self.set_aside if c == club), None)

    def __str__(self) -> str:
        return "%s: %s won; %s" % (self.context, self.winner, ", ".join("%s by %s" % (c, s) for c, s in self.set_aside))


def _run(t: Table, clubs: list, lists: Callable[[list], tuple], note: Note | None = None) -> Ref:
    """Step through the list for the clubs until one is left; whenever a step sets clubs aside, start the list again for those left."""
    clubs = list(clubs)
    while len(clubs) > 1:
        for name, step in lists(clubs):
            kept = step(t, clubs)
            if len(kept) < len(clubs):
                if note is not None:
                    note.set_aside += [(c, name) for c in clubs if c not in kept]
                clubs = kept
                break
        else:                                            # unreachable: the coin always leaves one
            break
    return clubs[0]


def best_in_division(t: Table, clubs: Sequence, note: Note | None = None) -> Ref:
    return _run(t, [Ref(*c) for c in clubs], lambda clubs: DIVISION_STEPS, note)


def best_for_wild_card(t: Table, clubs: Sequence, division_rank: dict, note: Note | None = None) -> Ref:
    """A wild card tie (also the seeds of the division winners): set aside all but each division's best club by the division order, then the
    two-club list, or the three-club list from its second step."""
    best_of: dict = {}
    for club in (Ref(*c) for c in clubs):
        if club[0] not in best_of or division_rank[club] < division_rank[best_of[club[0]]]:
            best_of[club[0]] = club
    left = list(best_of.values())
    if note is not None:
        note.set_aside += [(Ref(*c), "division order") for c in clubs if Ref(*c) not in left]
    return _run(t, left, lambda clubs: WILD_TWO_STEPS if len(clubs) == 2 else WILD_THREE_STEPS, note)


def ordered(t: Table, clubs: Sequence, pick: Callable, count: int | None = None, context: tuple = ()) -> list[Ref]:
    """The clubs best first: by percentage, and inside an equal percentage one club at a time by `pick(tied, note)` (the others start again).
    Every tie broken leaves a Note in `t.notes`, its context `context` plus the place's number (0 the first)."""
    left = [Ref(*c) for c in clubs]
    out: list[Ref] = []
    while left and (count is None or len(out) < count):
        best = max(t.pct(c) for c in left)
        tied = [c for c in left if t.pct(c) == best]
        if len(tied) == 1:
            chosen = tied[0]
        else:
            note = Note(context + (len(out),))
            chosen = note.winner = pick(tied, note)
            t.notes.append(note)
        out.append(chosen)
        left.remove(chosen)
    return out


def division_order(t: Table, division: int) -> list[Ref]:
    """The division's four teams, first to last, by the division tie-breakers."""
    return ordered(t, [Ref(division, p) for p in range(1, PLACES + 1)], lambda tied, note: best_in_division(t, tied, note),
                   context=("division", division))


@dataclass(frozen=True)
class Seeding:
    division_orders: dict             # division -> its four teams, first to last
    winners: list                     # the eight division winners, division 1 to 8
    seeds: dict                       # conference 0 or 1 -> its seven teams, seed 1 first (4 division winners, then 3 wild cards)


def seeding(t: Table, wild_cards: int = 3) -> Seeding:
    orders = {d: division_order(t, d) for d in range(1, DIVISIONS + 1)}
    rank = {team: number for d, order in orders.items() for number, team in enumerate(order)}
    winners = [orders[d][0] for d in range(1, DIVISIONS + 1)]
    seeds: dict = {}
    for conference, divisions in ((0, range(1, 5)), (1, range(5, 9))):
        pick = lambda tied, note: best_for_wild_card(t, tied, rank, note)
        top = ordered(t, [winners[d - 1] for d in divisions], pick, context=("seed", conference))
        others = [team for d in divisions for team in orders[d][1:]]
        seeds[conference] = top + ordered(t, others, pick, wild_cards, context=("wild", conference))
    return Seeding(orders, winners, seeds)


def deciding_notes(notes: Sequence[Note], own, wild_cards: int = 3) -> list[tuple[str, Note]]:
    """The ties that decided the player's team's division title or its last wild card place, in the order they were broken: ("title won",
    note), ("title lost", note), ("wild won", note) or ("wild lost", note). A tie that only moved it inside the bracket says nothing."""
    own = Ref(*own)
    out = []
    for note in notes:
        kind = note.context[0]
        if kind == "division" and note.context[1] == own[0] and note.context[2] == 0:
            word = "title"
        elif kind == "wild" and note.context[1] == conference_of(own) and note.context[2] == wild_cards - 1:
            word = "wild"
        else:
            continue
        if note.winner == own and note.set_aside:
            out.append((word + " won", note))
        elif note.step_against(own) is not None:
            out.append((word + " lost", note))
    return out
