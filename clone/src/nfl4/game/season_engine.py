"""The season engine and the play-offs: pog, finplay17 and the Super Bowl presentation. This is inspired by Jim Kitchen.

GAME_SPEC 5.14 to 5.17 and 5.6 item 7 (CODE (lifted) pog p_4615b0, finplay17 p_47d8b0, superbowl p_484860; the lifted
text is read with the assembly beside it, every Rnd draw is checked against the exe in `work/rnd_check_pog_s36.txt`,
`rnd_check_finplay17_s36.txt` and `rnd_check_superbowl_s73c.txt`, every constant in the const checks). There is no window,
sound card or file code here: the engine talks to the Game (the speakers, the replay list, the keys, the sounds) and to a
`SeasonStore` that S7.5 gives (football.gtp, footbal3.dat, footbal4.dat, footbal5.dat); its state is ONE record, the
Game's `SeasonState` (week counter gtp, records, the play-off pairings and byes), so a later Franchise mode can wrap the
class and its state (NFL_EXTRA_FEATURES 5: no hook of the extras falls in this engine).

What each call does, in the original's order (every draw keeps the range and the order of its lifted line, every spoken
text is the lifted text, every wait is the lifted wait):

* `pog()` runs after a game that was not saved when gtp is not 0 (GAME_SPEC 3 step 8), with the game's final score in
  `Game.m414` (own, opponent): a regular week (gtp 1 to 16: the player's result and the 15 other games, the records, the
  wait with F1 and F2; after week 16 the division winners, the wild cards, the seeds, the files of the bracket and where
  the player's team is), or a play-off week with the player's team (gtp 17 to 19: the round's results, the next round's
  pairings; a loss hands the rest to finplay17), or a conceded Super Bowl (gtp 20, D-029 item 3: Q48 is not reproduced).
* `finplay17()` plays every round from gtp - 16 to the Super Bowl without the player and ends with the celebration and gtp = 0.
* `super_bowl_presentation(scores)` is superbowl, called by pag after a Super Bowl game in place of the final score (Q27).

The clone's decisions (D-029): Q46 is not reproduced, so every play-off result is its own sentence with " The " (the
original joins the two A. F. C. wild card results into one text, loses the first when the player plays the second, drops
" The " in three places and never speaks the player's own A. F. C. championship result); Q48 is not reproduced (a conceded
Super Bowl says " In the Super Bowl. ", the opponent's win over the player's team, the celebration and the wait, and the
season ends). The speech log flag ptf stays 1 when pog returns, as in the original (Form_Load sets it to 0 after pog).
"""
from __future__ import annotations

import logging
from typing import Protocol

from . import season_texts as T
from .league import DIVISIONS, PLACES, League
from .playoffs import (ComputerGame, Pairing, Qualifier, TeamRef, computer_game, end_of_regular_season, score_of)
from .standings import Records
from .vbnum import rtrim, str_, trim

log = logging.getLogger("nfl4.game")

KEY_CODES_OF_REPEAT = ("112", "113")        # F1 and F2: g = "112" or g = "113" repeats the results
FINPLAY_FIRST_PAUSE_SITE = 0x47DF85         # finplay17's dy(0.2) at its start
SUPER_BOWL_PAUSE_SITE = 0x483F1A            # finplay17's dy(L24): 0.2 s the first time, 5 s after F1 or F2
SUPER_BOWL_PAUSE_FIRST, SUPER_BOWL_PAUSE_AGAIN = 0.2, 5.0
WEEK_COMPUTER_GAMES = 15                    # the other games of a regular week
SUPER_BOWL_GTP_MARK = 42                    # superbowl's last statement, Me.gtp = 42; pag sets the real 0 afterwards


class SeasonStateError(Exception):
    """The season's play-off state does not fit the week (a missing or short footbal4.dat or footbal5.dat). S7.4 restarts
    the season with a notice (D-024 item 5); the original would play on with stale values."""


class SeasonStore(Protocol):
    """What S7.5 writes at the moments the original writes its files (GAME_SPEC 12). The engine keeps the same data in
    the Game's SeasonState; the store only has to put it on disk. Nothing is read here: the files are read once, at the
    start of the week loop, into the state."""

    def write_records(self, records: Records) -> None: ...        # footbal3.dat, after a regular week
    def write_gtp(self, gtp: int) -> None: ...                    # football.gtp
    def write_pairings(self, pairings: list[Pairing]) -> None: ...    # footbal4.dat (deleted first, k4, then written)
    def write_byes(self, byes: list[TeamRef]) -> None: ...        # footbal5.dat (deleted first when it exists)


class NullSeasonStore:
    def write_records(self, records) -> None:
        pass

    def write_gtp(self, gtp) -> None:
        pass

    def write_pairings(self, pairings) -> None:
        pass

    def write_byes(self, byes) -> None:
        pass


NULL_STORE = NullSeasonStore()


class ClassicSeasonHooks:
    """H14 (nfl4 only, rule 0.13; NFL_FRANCHISE_DESIGN 13): what the Franchise reads of the season engine. Classic does nothing:
    `game_played` is called once after every result the engine speaks or decides, with the round ("regular", "wild_card",
    "division", "championship", "super_bowl"), the week counter and the two teams as TeamRefs with their scores."""

    def game_played(self, stage: str, week: int, winner: TeamRef, loser: TeamRef, winner_score: int, loser_score: int) -> None:
        pass


CLASSIC_SEASON_HOOKS = ClassicSeasonHooks()

REGULAR, WILD_CARD, DIVISION, CHAMPIONSHIP, SUPER_BOWL = "regular", "wild_card", "division", "championship", "super_bowl"
PLAYOFF_WEEK = {WILD_CARD: 17, DIVISION: 18, CHAMPIONSHIP: 19, SUPER_BOWL: 20}     # the week counter of each round


# ----- the sentences -----

def week_result(winner: str, loser: str, winner_score: int, loser_score: int) -> str:
    """A regular week's result: "<winner> over the <loser> by the score of <w>, to <l>. " (no " The ", Trim$ numbers)."""
    return (winner + T.OVER_THE + loser + T.BY_THE_SCORE_OF + trim(str_(winner_score)) + T.COMMA_TO
            + trim(str_(loser_score)) + T.END)


def playoff_result(winner: str, loser: str, winner_score: int, loser_score: int) -> str:
    """A play-off result: " The <winner> won over the <loser> by the score of <Str$ w> to<Str$ l>" with RTrim$ and ". ":
    each Str$ number brings its own space, so the score has two spaces in front: " ... by the score of  24 to 17. "."""
    text = T.THE + winner + T.WON_OVER_THE + loser + T.BY_THE_SCORE_OF + str_(winner_score) + T.TO + str_(loser_score)
    return rtrim(text) + T.END


def qualifier_line(team: str, wins: int, losses: int) -> str:
    """"<team>. at <wins> and <losses>. " (Trim$ numbers): a division winner or a wild card."""
    return team + T.DOT_AT + trim(str_(wins)) + T.AND + trim(str_(losses)) + T.END


def out_of_the_playoffs(team: str, wins: int, losses: int) -> str:
    """" The <team> at <Str$ w> and <Str$ l>. " + " did not make it into the playoffs. " (0x46f73c to 0x46f9e3: RTrim$ of
    the first part, then ". ", then the second text, so two spaces follow the full stop)."""
    text = T.THE + team + T.AT + str_(wins) + T.AND + str_(losses)
    return rtrim(text) + T.END + T.DID_NOT_MAKE_THE_PLAYOFFS


def super_bowl_sentence(winner: str, loser: str, winner_score: int, loser_score: int) -> str:
    """superbowl's sentence: " The <winner> have Won the super Bowl!  They beat the <loser> by the score of <w>, to <l>. "
    (Trim$ numbers; the two texts around the first "!" each bring a space, so two spaces follow it)."""
    return (T.THE + winner + T.HAVE_WON_THE_SUPER_BOWL + T.THEY_BEAT_THE + loser + T.BY_THE_SCORE_OF
            + trim(str_(winner_score)) + T.COMMA_TO + trim(str_(loser_score)) + T.END)


class PogResult:
    """What pog leaves for the caller: the week counter and whether the season is over (gtp 0)."""

    def __init__(self, gtp: int):
        self.gtp = gtp
        self.season_over = gtp == 0

    def __repr__(self) -> str:
        return "PogResult(gtp=%d, season_over=%s)" % (self.gtp, self.season_over)


class SeasonEngine:
    def __init__(self, game):
        self.g = game
        self.player_won = False             # L3d0: the player won a play-off game

    # ----- small helpers -----

    @property
    def store(self) -> SeasonStore:
        return getattr(self.g, "season_store", None) or NULL_STORE

    @property
    def league(self) -> League:
        return self.g.league

    @property
    def hooks(self) -> ClassicSeasonHooks:
        return getattr(self.g, "season_hooks", CLASSIC_SEASON_HOOKS)

    def name(self, team: TeamRef) -> str:
        return self.g.league.team(team.division, team.place)

    @property
    def scores(self) -> tuple[int, int]:
        """Me.m414: the last game's final score (the player's, the opponent's)."""
        if self.g.m414 is None:
            raise RuntimeError("pog needs the game's final score (Game.m414)")
        return self.g.m414

    def _win(self, team: TeamRef) -> None:
        self.g.season.records.win(team.division, team.place)

    def _loss(self, team: TeamRef) -> None:
        self.g.season.records.loss(team.division, team.place)

    def _round_wait(self, clk_first: bool = False) -> None:
        """The wait after a round (the original's `norep = 1`, getkey, F1 or F2: inrep and wait again, any other key:
        `norep = 0`). Some of the original's waits start with clk, getkey itself does the same."""
        g = self.g
        while True:
            if clk_first:
                g.keys.clk()
            g.norep = 1
            g.keys.getkey(g.speech)
            if g.keys.code_text in KEY_CODES_OF_REPEAT:
                g.inrep()
                continue
            break
        g.norep = 0

    def _pairings(self, count: int) -> list[Pairing]:
        pairings = self.g.season.playoffs.pairings
        if len(pairings) < count:
            raise SeasonStateError("the play-off pairings hold %d games, week %d needs %d"
                                   % (len(pairings), self.g.season.gtp, count))
        return list(pairings[:count])

    def _byes(self, count: int = 4) -> list[TeamRef]:
        """The four bye teams of footbal5.dat, checked BEFORE a round is drawn and spoken (a short list would otherwise
        be found only after four results were heard and thrown away, or written short by a zip)."""
        byes = self.g.season.playoffs.byes
        if len(byes) < count:
            raise SeasonStateError("the bye teams hold %d teams, week %d needs %d"
                                   % (len(byes), self.g.season.gtp, count))
        return list(byes[:count])

    def _write_next_round(self, pairings: list[Pairing]) -> None:
        """k4 (deletes footbal4.dat), then the pairings of the coming round."""
        self.g.season.playoffs.pairings = list(pairings)
        self.store.write_pairings(list(pairings))

    # ----- pog -----

    def pog(self) -> PogResult:
        """pog (GAME_SPEC 5.14 to 5.16): after the player's game."""
        g, season = self.g, self.g.season
        if season.gtp < 1:                                        # the caller skips pog when gtp is 0 (GAME_SPEC 3 step 8)
            raise SeasonStateError("pog is not called when the season is over (gtp %d)" % season.gtp)
        g.ptf = 1
        self.player_won = False                                   # L3d0 = 0 (0x4625a5)
        g.empty_replay()                                          # Me.ilc = 0 (0x4625ce)
        if season.gtp < 17:
            self._regular_week()
        elif season.gtp <= 17:
            self._wild_card_week()
        elif season.gtp <= 18:
            self._division_week()
        elif season.gtp <= 19:
            self._championship_week()
        else:
            self._conceded_super_bowl()
        return PogResult(season.gtp)

    # ----- a regular week (5.14) -----

    def _free_team(self, played: dict[TeamRef, int | None]) -> TeamRef:
        """A random team that has not played this week: its division Int(Rnd * 8) + 1 and its place Int(Rnd * 4) + 1 are
        drawn together again while the team has played (0x464434 to 0x4645c9, 0x464714 to 0x4648a9)."""
        rnd = self.g.rnd
        return rnd.redraw(lambda: TeamRef(rnd(DIVISIONS), rnd(PLACES)), lambda t: played[t] is None,
                          lambda: next(t for t in played if played[t] is None), "a team that has not played this week")

    def _regular_week(self) -> None:
        g, season, rnd = self.g, self.g.season, self.g.rnd
        own, opponent = season.own_team, season.opponent_team
        own_score, opponent_score = self.scores
        played: dict[TeamRef, int | None] = {TeamRef(d, p): None for d in range(1, DIVISIONS + 1)
                                             for p in range(1, PLACES + 1)}
        played[own], played[opponent] = own_score, opponent_score    # L270 (0x462a3f, 0x462b0e)
        g.keys.clk()                                              # 0x462b54
        # footbal3.dat is read here (0x462bb3 to 0x462ea5): the records are in memory
        g.keys.clk()                                              # 0x462eb4
        lines = [T.GAMES_OF_WEEK + trim(str_(season.gtp)) + T.END]   # " Games of week number 5. "
        g.say2(lines[0])
        if own_score <= opponent_score:                           # If Me.m414(1) <= Me.m414(2): the opponent wins (Q41)
            winner, loser, winner_score, loser_score = opponent, own, opponent_score, own_score
        else:
            winner, loser, winner_score, loser_score = own, opponent, own_score, opponent_score
        self._win(winner)
        self._loss(loser)
        self.hooks.game_played(REGULAR, season.gtp, winner, loser, winner_score, loser_score)
        lines.append(week_result(self.name(winner), self.name(loser), winner_score, loser_score))
        g.say2(lines[1])
        for _ in range(WEEK_COMPUTER_GAMES):                      # For Lb0 = 1 To 15
            team_a = self._free_team(played)
            index_a = rnd(32)                                     # La0
            played[team_a] = score_of(index_a)
            team_b = self._free_team(played)
            index_b = rnd.redraw(lambda: rnd(32), lambda i: score_of(i) != score_of(index_a),
                                 lambda: next(i for i in range(1, 33) if score_of(i) != score_of(index_a)),
                                 "a score that differs from the other team's")
            played[team_b] = score_of(index_b)
            if index_a <= index_b:                                # the higher score wins (b > a: B)
                winner, loser, winner_score, loser_score = team_b, team_a, score_of(index_b), score_of(index_a)
            else:
                winner, loser, winner_score, loser_score = team_a, team_b, score_of(index_a), score_of(index_b)
            line = week_result(self.name(winner), self.name(loser), winner_score, loser_score)
            self._win(winner)
            self._loss(loser)
            self.hooks.game_played(REGULAR, season.gtp, winner, loser, winner_score, loser_score)
            lines.append(line)
            g.say2(line)
        g.log_print("")                                           # Print #3,
        season.gtp += 1
        self.store.write_records(season.records)                  # footbal3.dat
        # the wait: clk, getkey; F1 or F2 speaks the 17 lines again (not inrep) and waits again
        g.keys.clk()
        g.keys.getkey(g.speech)
        while g.keys.code_text in KEY_CODES_OF_REPEAT:
            g.keys.clk()
            g.empty_replay()
            for line in lines:
                g.say2(line)
            g.keys.clk()
            g.keys.getkey(g.speech)
        if season.gtp < 17:
            self.store.write_gtp(season.gtp)                      # 0x47d257
            return
        self._end_of_regular_season()

    # ----- the end of the regular season (5.15) -----

    def _qualifier_line(self, q: Qualifier) -> str:
        return qualifier_line(self.name(q.team), q.wins, q.losses)

    def _end_of_regular_season(self) -> None:
        g, season, league = self.g, self.g.season, self.g.league
        own = season.own_team
        result = end_of_regular_season(season.records, own)
        g.empty_replay()                                          # 0x4698e9
        g.ptf = 1
        g.say4(T.DIVISION_WINNERS_ARE)
        for division, winner in enumerate(result.winners, start=1):
            g.say4(league.division_text(division))
            g.say4(self._qualifier_line(winner))
        g.log_print("")
        g.say4(T.AFC_WILD_CARD_TEAMS)
        for card in result.afc_wild_cards:
            g.say4(self._qualifier_line(card))
        g.say4(T.NFC_WILD_CARD_TEAMS)
        for card in result.nfc_wild_cards:
            g.say4(self._qualifier_line(card))
        g.log_print("")
        season.playoffs.pairings = list(result.pairings)          # k4, footbal4.dat; footbal5.dat
        season.playoffs.byes = list(result.byes)
        self.store.write_pairings(list(result.pairings))
        self.store.write_byes(list(result.byes))
        where = result.where(own)
        if where == "wild_card":
            self._round_wait(clk_first=True)                      # 0x46fbc0: the wild card week is next start's game
            self.store.write_gtp(season.gtp)                      # 17
        elif where == "bye":
            self._round_wait(clk_first=True)                      # 0x46fd35
            self._wild_card_games_without_the_player()
        else:
            wins, losses = season.records.record(own.division, own.place)
            g.say4(out_of_the_playoffs(self.name(own), wins, losses))
            g.log_print("")
            self._round_wait()                                    # 0x46fa4b, no clk first
            self.finplay17()                                      # gtp is 0 afterwards; football.gtp is not written

    def _wild_card_games_without_the_player(self) -> None:
        """The player's team has a bye: the four wild card games are played and spoken (0x46fec8 to 0x4734fd), the
        division round's pairings written, the wait, gtp = 18."""
        g, season = self.g, self.g.season
        pairings, byes = self._pairings(4), self._byes()
        g.empty_replay()
        winners = self._computer_round(pairings, T.POG_AFC_WILD_CARD, T.POG_NFC_WILD_CARD, WILD_CARD)
        self._write_next_round(list(zip(winners, byes)))
        self._round_wait()
        season.gtp += 1
        self.store.write_gtp(season.gtp)

    # ----- play-off weeks with the player's team (5.16) -----

    def _computer_game(self, pairing: Pairing, stage: str = WILD_CARD) -> tuple[TeamRef, str]:
        """A computer game (5.17 item 2): the winner and the sentence. `stage` is the round, for H14."""
        visitor, home = pairing
        game: ComputerGame = computer_game(self.g.rnd)
        winner, loser = (visitor, home) if game.first_wins else (home, visitor)
        self.hooks.game_played(stage, PLAYOFF_WEEK[stage], winner, loser, game.winner_score, game.loser_score)
        return winner, playoff_result(self.name(winner), self.name(loser), game.winner_score, game.loser_score)

    def _computer_round(self, pairings: list[Pairing], first_heading: str, second_heading: str,
                        stage: str = WILD_CARD) -> list[TeamRef]:
        """finplay17's and the bye week's round: the first heading, the A. F. C. games, the second heading, the N. F. C.
        games, each result its own say4 right after its draws. Returns the winners in order."""
        g = self.g
        half = len(pairings) // 2
        winners: list[TeamRef] = []
        g.say4(first_heading)
        for index, pairing in enumerate(pairings):
            if index == half:
                g.say4(second_heading)
            winner, sentence = self._computer_game(pairing, stage)
            g.say4(sentence)
            winners.append(winner)
        return winners

    def _player_game(self, stage: str = WILD_CARD) -> tuple[TeamRef, str]:
        """GoSub 0x477000: the player's game of a play-off round, with the final score of the game just played. The
        player's team wins when its score is higher (a tie would go to the opponent, Q41)."""
        season = self.g.season
        own, opponent = season.own_team, season.opponent_team
        own_score, opponent_score = self.scores
        if own_score > opponent_score:
            self.player_won = True                                # L3d0 = 1
            self.hooks.game_played(stage, PLAYOFF_WEEK[stage], own, opponent, own_score, opponent_score)
            return own, playoff_result(self.name(own), self.name(opponent), own_score, opponent_score)
        self.hooks.game_played(stage, PLAYOFF_WEEK[stage], opponent, own, opponent_score, own_score)
        return opponent, playoff_result(self.name(opponent), self.name(own), opponent_score, own_score)

    def _round_with_the_player(self, pairings: list[Pairing], first_heading: str, second_heading: str,
                               stage: str = WILD_CARD) -> list[TeamRef]:
        """A round of pog's play-off weeks: the games in the record order, the player's game from the final score, the
        others as computer games. Q46 not reproduced: every result is its own sentence with " The "."""
        g, own = self.g, self.g.season.own_team
        half = len(pairings) // 2
        winners: list[TeamRef] = []
        g.say4(first_heading)
        for index, pairing in enumerate(pairings):
            if index == half:
                g.say4(second_heading)
            winner, sentence = self._player_game(stage) if own in pairing else self._computer_game(pairing, stage)
            g.say4(sentence)
            winners.append(winner)
        return winners

    def _wild_card_week(self) -> None:
        g, season = self.g, self.g.season
        pairings, byes = self._pairings(4), self._byes()
        season.gtp += 1                                           # 18
        g.empty_replay()
        winners = self._round_with_the_player(pairings, T.POG_AFC_WILD_CARD, T.POG_NFC_WILD_CARD, WILD_CARD)
        self._write_next_round(list(zip(winners, byes)))          # the four winners at the four bye teams
        self._round_wait()
        if not self.player_won:
            season.gtp = 18
            self.finplay17()
        self.store.write_gtp(season.gtp)

    def _division_week(self) -> None:
        g, season = self.g, self.g.season
        pairings = self._pairings(4)
        season.gtp += 1                                           # 19
        g.empty_replay()
        self.player_won = False                                   # L3d0 = 0 (0x477a78)
        winners = self._round_with_the_player(pairings, T.POG_AFC_DIVISION, T.POG_NFC_DIVISION, DIVISION)
        self._write_next_round([(winners[0], winners[1]), (winners[2], winners[3])])
        self._round_wait()
        if not self.player_won:
            season.gtp = 19
            self.finplay17()
        self.store.write_gtp(season.gtp)

    def _championship_week(self) -> None:
        g, season = self.g, self.g.season
        pairings = self._pairings(2)
        season.gtp += 1                                           # 20
        self.player_won = False                                   # 0x47b40c
        g.empty_replay()
        winners = self._round_with_the_player(pairings, T.POG_AFC_CHAMPIONSHIP, T.POG_NFC_CHAMPIONSHIP, CHAMPIONSHIP)
        self._write_next_round([(winners[0], winners[1])])        # the A. F. C. champion at the N. F. C. champion
        self._round_wait()
        if not self.player_won:
            season.gtp = 20
            self.finplay17()
        self.store.write_gtp(season.gtp)

    def _conceded_super_bowl(self) -> None:
        """A conceded Super Bowl (gtp 20 when pog runs, 4.18, Q48 not reproduced, D-029 item 3): " In the Super Bowl. ",
        the opponent's win over the player's team, then finplay17's Super Bowl ending, and the season is over."""
        g, season = self.g, self.g.season
        own, opponent = season.own_team, season.opponent_team
        own_score, opponent_score = self.scores
        g.empty_replay()
        g.say4(T.IN_THE_SUPER_BOWL)
        self.hooks.game_played(SUPER_BOWL, PLAYOFF_WEEK[SUPER_BOWL], opponent, own, opponent_score, own_score)
        g.say4(playoff_result(self.name(opponent), self.name(own), opponent_score, own_score))
        self._super_bowl_ending()
        self.store.write_gtp(season.gtp)                          # 0

    # ----- finplay17 (5.17) -----

    def finplay17(self) -> None:
        """The rounds without the player, from round gtp - 16 (a value outside 1 to 4 starts at the wild card round) to the
        Super Bowl; gtp is 0 at the end."""
        g, season = self.g, self.g.season
        g.empty_replay()
        g.ptf = 1
        g.dy(0.2, FINPLAY_FIRST_PAUSE_SITE)
        start = season.gtp - 16                                   # On L54 GoTo ...
        if not 1 <= start <= 4:
            start = 1
        if start <= 1:
            self._fin_wild_card_round()
        if start <= 2:
            self._fin_division_round()
        if start <= 3:
            self._fin_championship_round()
        self._fin_super_bowl()

    def _fin_wild_card_round(self) -> None:
        pairings, byes = self._pairings(4), self._byes()
        winners = self._computer_round(pairings, T.POG_AFC_WILD_CARD, T.POG_NFC_WILD_CARD, WILD_CARD)
        self._write_next_round(list(zip(winners, byes)))
        self._round_wait()

    def _fin_division_round(self) -> None:
        self.g.empty_replay()                                     # 0x480331
        winners = self._computer_round(self._pairings(4), T.FIN_AFC_DIVISION, T.POG_NFC_DIVISION, DIVISION)
        self._write_next_round([(winners[0], winners[1]), (winners[2], winners[3])])
        self._round_wait()

    def _fin_championship_round(self) -> None:
        self.g.empty_replay()                                     # 0x4824e2
        winners = self._computer_round(self._pairings(2), T.FIN_AFC_CHAMPIONSHIP, T.FIN_NFC_CHAMPIONSHIP, CHAMPIONSHIP)
        self._write_next_round([(winners[0], winners[1])])
        self._round_wait()

    def _fin_super_bowl(self) -> None:
        g = self.g
        pairing = self._pairings(1)[0]
        g.empty_replay()                                          # 0x4836b6
        g.say4(T.IN_THE_SUPER_BOWL)
        winner, sentence = self._computer_game(pairing, SUPER_BOWL)
        g.say4(sentence)
        self._super_bowl_ending()

    def _super_bowl_ending(self) -> None:
        """0x483f11 to 0x484698: after the Super Bowl's result without the player: 0.2 s, 8 to 15 celebration sounds with
        norep = 1 (no crowd ramp, no foot12, no foot25), then getkey; F1 or F2 (the instant replay without its
        introduction), a 5-second pause and the celebration again with new draws (Q50); any other key: norep = 0,
        gtp = 0 (the season is over)."""
        g = self.g
        pause = SUPER_BOWL_PAUSE_FIRST
        while True:
            g.dy(pause, SUPER_BOWL_PAUSE_SITE)
            g.norep = 1
            g.sounds.celebration_run()
            pause = SUPER_BOWL_PAUSE_AGAIN
            g.keys.getkey(g.speech)
            if g.keys.code_text in KEY_CODES_OF_REPEAT:
                g.inrep()
                continue
            break
        g.norep = 0
        g.season.gtp = 0

    # ----- superbowl (5.6 item 7, called by pag) -----

    def super_bowl_presentation(self, scores: tuple[int, int]) -> None:
        """superbowl p_484860 after a Super Bowl game of the player's team, in place of the final score (Q27). `scores` is
        the game's final score (own, opponent). The player's team won: the winner sentence, 8 to 15 celebration sounds,
        foot25 (volume 0, waited), 8 to 15 more; the opponent won: the sentence and 8 to 15 sounds; then getkey: F1 or F2
        play it all again with new draws, any other key ends it. gtp is 42 at the end (pag sets 0)."""
        g, season = self.g, self.g.season
        own_score, opponent_score = scores
        if own_score <= opponent_score:                           # H14: once, whatever F1 and F2 repeat afterwards
            self.hooks.game_played(SUPER_BOWL, PLAYOFF_WEEK[SUPER_BOWL], season.opponent_team, season.own_team,
                                   opponent_score, own_score)
        else:
            self.hooks.game_played(SUPER_BOWL, PLAYOFF_WEEK[SUPER_BOWL], season.own_team, season.opponent_team,
                                   own_score, opponent_score)
        while True:
            g.empty_replay()                                      # Me.ilc = 0 (0x484947)
            g.ptf = 1
            if own_score <= opponent_score:                       # the opponent wins (0x48498a)
                g.say4(super_bowl_sentence(self.name(season.opponent_team), self.name(season.own_team),
                                           opponent_score, own_score))
            else:
                g.say4(super_bowl_sentence(self.name(season.own_team), self.name(season.opponent_team),
                                           own_score, opponent_score))
                g.sounds.celebration_run()
                g.sounds.play(25, 0)
            g.sounds.celebration_run()
            g.keys.getkey(g.speech)
            if g.keys.code_text in KEY_CODES_OF_REPEAT:
                continue
            break
        season.gtp = SUPER_BOWL_GTP_MARK
