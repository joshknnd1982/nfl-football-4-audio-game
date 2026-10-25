"""A rig for the Franchise's draft and roster cut (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

`draft_league` makes a league that sits at the start of a stage of the offseason (stage 4, the draft, by default) and `offseason_rig`
resumes it on the program rig (tests/frrig.py: the whole program with the real season engine and a stand-in for pag) until a predicate
holds. Every save of the league is noted in `rig.saves` as (stage number, pick number, the draft's pick count, the file or None, the
number of lines spoken so far); `keep=True` keeps the
file as well, and `rig.kept[stage]` holds the file as the first save of each stage wrote it.
"""
import random

from frrig import enter_until, franchise_rig, run_until

from nfl4.extras.franchise import data as D
from nfl4.extras.franchise.files import MemoryFiles
from nfl4.extras.franchise.league import OFFSEASON, LeagueRecord, new_league
from nfl4.extras.franchise.store import FranchiseStore
from nfl4.game.names import load_surnames
from nfl4.game.rnd import GameRandom

SURNAMES = load_surnames()


def draft_league(seed=3, team=5, stage_no=D.STAGE_DRAFT, wins=None, finish=None, mutate=None):
    """A league at the start of an offseason stage. `wins` (32 numbers) and `finish` (32 numbers, D.FINISH_*) make the history entry the
    draft order reads; without them the season's records are 8 and 8 for everybody and nobody was in the play-offs."""
    league = new_league(GameRandom(random.Random(seed)), SURNAMES, "Kim", team, "20260101-000000")
    league.stage, league.stage_no, league.gtp, league.records = OFFSEASON, stage_no, 0, [8, 8] * 32
    if wins is not None:
        league.records = [x for w in wins for x in (w, 16 - w)]
        league.history = [{"season": league.season, "team": team, "coach": "Kim", "champion": 1, "runner_up": 2, "wins": list(wins),
                           "losses": [16 - w for w in wins], "finish": list(finish or [0] * 32), "playoff": [0, 0], "best": 1, "worst": 2,
                           "top_points": None, "big_win": None, "streak": None}]
    if mutate is not None:
        mutate(league)
    return league


def offseason_rig(tmp_path, league, keys=(), until=None, source=None, files=None, short=False, picks_told=None, auto=False, keep=False,
                  **kwargs):
    """Resume `league` (or the files given) on the rig until `until(rig)` (default: the new season's week 1) and return the rig with
    `rig.saves`, `rig.kept` and `rig.start` (the league as it began)."""
    if files is None:
        files = MemoryFiles()
        files.data["league.sav"] = league.to_json().encode("utf-8")
    rig = franchise_rig(tmp_path, list(keys), files=files, kind="franchise", **kwargs,
                        policy=enter_until(lambda: (until or default_until)(rig)))
    settings = rig.game.options.settings.game
    if short:
        settings.nx_fr_offseason = "short"
    if picks_told is not None:
        settings.nx_fr_picks_told = picks_told
    if auto:
        settings.nx_fr_auto = True
    if source is not None:
        rig.game.rnd.source = source
    rig.saves, rig.kept, rig.class_raw = [], {}, None
    real = FranchiseStore.save

    def save(self):
        ok = real(self)
        lg = self.league
        draft = lg.draft
        if draft is not None and not draft["picks"] and rig.class_raw is None:
            rig.class_raw = self.files.data["league.sav"]                 # the file that holds the class, before the first pick
        rig.saves.append((lg.stage_no if lg.stage == OFFSEASON else 0, lg.pick_no, len(draft["picks"]) if draft else -1,
                          self.files.data["league.sav"] if keep else None, len(rig.said)))
        if lg.stage == OFFSEASON and lg.stage_no not in rig.kept:
            rig.kept[lg.stage_no] = self.files.data["league.sav"]
        return ok
    FranchiseStore.save = save
    try:
        run_until(rig)
    finally:
        FranchiseStore.save = real
    rig.start = league
    return rig


def default_until(rig):
    store = rig.fstore
    return store is not None and store.league is not None and store.league.stage == "season" and store.league.season == 2


def saved_league(rig) -> LeagueRecord:
    return LeagueRecord.from_json(rig.files.data["league.sav"].decode("utf-8"))


def replay(rig, chooser):
    """The picks the draft on the rig must have made: the class that was saved, the computer's rule for every team but the player's, and
    for the player's k-th pick (0 to 6) the index into the ranking for his team that `chooser(k)` names. Returns the picks as rows."""
    from nfl4.extras.franchise import draft as DR
    league = LeagueRecord.from_json(rig.class_raw.decode("utf-8"))
    draft = DR.Draft(league)
    mine = 0
    while not draft.done:
        _, _, team = draft.next_slot()
        if team == league.team:
            ranked = draft.ranked_for(team)
            prospect = ranked[chooser(mine)]
            mine += 1
        else:
            prospect = draft.best_for(team)
        draft.make_pick(team, prospect)
    return [[team, index] for team, index, _ in league.draft["picks"]]


def picks_of(league):
    return [[team, index] for team, index, _ in league.draft["picks"]]


def at_stage(number, pick=None):
    """A predicate: the league on the rig is at offseason stage `number` (and, for the draft, has made `pick` picks)."""
    def predicate_of(rig):
        store = rig.fstore
        league = store.league if store is not None else None
        if league is None or league.stage != OFFSEASON or league.stage_no != number:
            return False
        return pick is None or (league.draft is not None and len(league.draft["picks"]) >= pick)
    return predicate_of


__all__ = ["draft_league", "offseason_rig", "saved_league", "at_stage", "default_until", "SURNAMES", "enter_until", "franchise_rig",
           "run_until", "replay", "picks_of"]
