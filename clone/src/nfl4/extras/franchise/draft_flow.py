"""Stages 4 and 5 of the offseason: the draft, and the roster cut with the fill (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 7 (F3, N6.5). The rules are `draft.py` (no speech, no files); this module speaks, asks the player and writes
league.sav, in the way `offseason.py` does for the other stages:

* Stage 4 makes the class at its start (the only draws of the stage) and writes it at once, so a window closed at any later moment
  resumes the same class. Every pick is made, written, then told (the file at a pick is what was just said, B-X53), so a draft closed
  in the middle resumes at its next pick. The player's own pick is a `FranchiseQuestion` (the staff's five, more prospects, the staff's
  pick, the staff's picks for the rest of the draft); every computer pick, and the staff's, is `Draft.best_for` (one code path, I7).
* Stage 5 plans the cut of every team without changing anything (SX.8g: with the players the staff lets go to get a team under the salary
  cap), asks the player about his own team, then applies all the cuts, fills the empty places, ends the draft and writes league.sav in
  one block, and only then speaks the fill (the stage is idempotent until its save, B-X51).
* SX.8m: stage 4 tells the draft's compensatory picks (`comp.py`); after its last pick the player is asked, before anything changes, which undrafted free
  agents his team offers a place in camp; then every team's offers are judged together (`undrafted.run`: the computer teams, and the player's team too when
  the staff handles it) in the stage's last write, and only then told. They wait for the cut like the drafted rookies.
"""
from __future__ import annotations

from .. import nx_texts as X
from .. import tuning as T
from . import aging
from . import contracts as CT
from . import data as D
from . import draft as DR
from . import news
from . import undrafted as UD
from .news_pools import DEFAULT_POOLS
from .question import FranchiseQuestion

STAFF_LIST = 5                                   # the staff's list holds this many prospects (design 7.3)
FIRST_TOLD = 3                                   # picks setting "first": the first picks of round 1 told


def _offseason():
    from . import offseason                      # the stage helpers and the wait live there (a late import: offseason imports this module)
    return offseason


def _told(setting: str, overall: int, next_team: int | None, own_team: int) -> bool:
    """Is the computer's pick number `overall` told? `all` every pick, `mine` none of the computer's, `first` the first three picks
    of the draft and the pick right before each of the player's (design 7.3)."""
    if setting == "all":
        return True
    if setting == "mine":
        return False
    return overall <= FIRST_TOLD or next_team == own_team


# ----- stage 4: the draft -----

def stage_draft(p, n: int, m: int, short: bool) -> None:
    off = _offseason()
    g, store = p.g, p.store
    league = store.league
    words = store.words
    if league.draft is None:                     # the class, written at once: the draws are made once
        DR.Draft.create(league, g.rnd, list(g.pool.original))
        store.save()
    draft = DR.Draft(league)
    g.say2(off._stage_line(n, m, "NXE-14"))
    if draft.own_picks_only(league.team):
        g.say2(X.text("NXK-01", n=draft.place_in_round(league.team)))
    else:                                        # SX.8j: a trade of the season moved one of his picks: the picks he makes, one by one (the compensatory ones apart)
        picks = [X.text("NXK-15", round=r, pick=k) for r, k in draft.picks_of(league.team) if k <= D.TEAMS]
        g.say2(X.text("NXK-14", list=", ".join(picks) if picks else X.text("NXK-13")))
    if draft.comp:                               # SX.8m: the compensatory picks of this draft, the player's named
        g.say2(X.text("NXU-10", n=len(draft.comp)) if len(draft.comp) > 1 else X.text("NXU-11"))
        own_comp = draft.comp_picks_of(league.team)
        if own_comp:
            g.say2(X.text("NXU-12", list=", ".join(X.text("NXK-15", round=r, pick=k) for r, k in own_comp)))
    announced = 0                                # the round whose number was said last
    while not draft.done:
        overall = len(draft.picks) + 1
        round_no, in_round, team = draft.slot(overall)
        mine = team == league.team
        chosen = False
        if mine and not draft.staff_all:
            announced = round_no                 # the prompt names the round
            prospect, chosen = _players_pick(g, draft, words, league, round_no, in_round)
        else:
            prospect = draft.best_for(team)
        player = draft.make_pick(team, prospect)
        store.save()
        if mine:
            if chosen:
                g.say2(X.text("NXK-10", player=player.name, position=words.position(player.pos)))
            else:
                announced = _announce(g, round_no, announced)
                g.say2(X.text("NXK-12", player=player.name, position=words.position(player.pos)))
        else:
            next_team = draft.slot(overall + 1)[2] if overall < draft.total else None
            if _told(g.options.settings.game.nx_fr_picks_told, overall, next_team, league.team):      # read at each pick: F9 may change it
                announced = _announce(g, round_no, announced)
                g.say2(X.text("NXK-03", n=in_round, team=words.team_name(team), player=player.name,
                              position=words.position(player.pos)))
    # the draft is over: the undrafted free agents (SX.8m), asked before anything changes, then the stage is written (the draft record stays until the cut:
    # F9 tells the rookies by their ranges)
    staff_udfa = bool(g.options.settings.game.nx_fr_auto)
    offers, chose = ([], False) if staff_udfa else _undrafted_choice(g, words, draft, league)
    udfa = UD.run(draft, offers, skip=() if staff_udfa else (league.team,), own=(league.team,) if chose else ())
    own = league.waiting_rookies(league.team)
    first = league.players[draft.picks[0][2]]                               # the first pick of the draft: the NWD line (design 8.3)
    told, recent = news.render(league, [news.first_pick_event(draft.picks[0][0], first)], g.news_pools or DEFAULT_POOLS, words, g.rnd)
    lines = [X.text("NXK-11")] + [
        words.prospect_line(player.name, player.pos, *draft.range_of(player), player.age, player.potential) for player in own if player.drafted is not None]
    lines += _undrafted_lines(words, league, draft, udfa, offers, short)
    news.keep(league, told, recent, D.NEWS_OFFSEASON)
    league.stage_no = off._next_stage(D.STAGE_DRAFT)
    store.save()
    if short:
        for line in lines:
            g.say2(line)
    else:
        off.wait_for_enter(g, off._news_texts(told) + lines + [X.text("NXE-03")])


def _announce(g, round_no: int, announced: int) -> int:
    if round_no != announced:
        g.say2(X.text("NXK-02", n=round_no))
    return round_no


def _players_pick(g, draft: DR.Draft, words, league, round_no: int, in_round: int) -> tuple:
    """The player's pick (design 7.3): (the prospect, True when the player chose him himself, False when the staff did)."""
    team = league.team
    ranked = draft.ranked_for(team)
    staff = ranked[:STAFF_LIST]
    places = DR.open_places(draft, team)
    situation = [X.text("NXK-04", coach=league.coach, round=round_no, pick=in_round, list=words.open_places(places)),
                 X.text("NXK-05")]
    items = [words.prospect_line(pr.name, pr.pos, pr.low, pr.high, pr.age, pr.potential) for pr in staff]
    items += [X.text("NXK-07"), X.text("NXK-08"), X.text("NXK-09")]
    start = 0
    while True:
        answer = FranchiseQuestion(g, situation, items, start=start).ask()
        if answer < len(staff):
            return staff[answer], True
        which = answer - len(staff)
        if which == 0:                           # hear more prospects: everybody available, the most valuable to the team first
            lines = [words.prospect_line(pr.name, pr.pos, pr.low, pr.high, pr.age, pr.potential) for pr in ranked]
            taken = FranchiseQuestion(g, [X.text("NXK-07")], lines, escape_value=-1).ask()
            if taken >= 0:
                return ranked[taken], True
            start = answer                       # Escape: back to the question, on the item that was opened
            continue
        if which == 2:                           # the staff makes this pick and every later pick of this draft
            draft.let_the_staff_pick_the_rest()
        return staff[0], False


# ----- stage 5: the roster cut and the fill -----

def stage_cut(p, n: int, m: int, short: bool) -> None:
    off = _offseason()
    g, store = p.g, p.store
    league = store.league
    words = store.words
    settings = g.options.settings.game
    team = league.team
    waiting = DR.waiting_by_team(league)
    plans = {t: DR.staff_cut(league, t, waiting) for t in range(1, D.TEAMS + 1)}
    header = off._stage_line(n, m, "NXE-15")
    spoken: list = []                            # the stage's lines that follow the questions
    asked = False
    mine = plans[team]
    if not mine:
        spoken.append(X.text("NXE-58"))
    elif settings.nx_fr_auto:
        spoken.append(X.text("NXE-56", n=len(mine)))
    else:
        asked = True
        cut = DR.plan_cut(league, team, waiting)             # the cut's own list, then the players let go for the cap
        situation = [header]
        if cut:
            situation += [X.text("NXE-50")] + [
                X.text("NXE-51", player=pl.name, position=words.position(pl.pos), a=pl.age, r=pl.rating) for pl in cut]
        if len(mine) > len(cut):
            situation += [X.text("NXE-59" if cut else "NXA-15", over=words.amount(CT.cap_over(league, team, waiting, cut)))] + [
                words.released_for_the_cap(pl) for pl in mine[len(cut):]]
        if FranchiseQuestion(g, situation, [X.text("NXE-52"), X.text("NXE-53")]).ask() == 1:
            plans[team] = _own_choice(g, words, league, waiting)
            plans[team] += _own_cap_choice(g, words, league, waiting, plans[team])
    first_new = league.next_id
    DR.apply_cut(league, plans, waiting)
    filled = aging.fill_places(league, g.rnd, list(g.pool.original))
    own_filled = [pl for pl in league.players.values() if pl.id >= first_new and pl.team == team]
    league.draft = None
    league.pick_no = 0
    told, recent = news.render(league, [news.cap_event(league)], g.news_pools or DEFAULT_POOLS, words, g.rnd)      # NWK, after the fill
    news.keep(league, told, recent, D.NEWS_OFFSEASON)
    league.stage_no = off._next_stage(D.STAGE_CUT)
    store.save()
    if own_filled:
        spoken.append(X.text("NXE-57", n=len(own_filled)))
        if not short:
            spoken += [words.player(pl) for pl in sorted(own_filled, key=lambda pl: pl.place)]
    space = CT.cap_space(league, team)
    spoken.append(X.text("NXA-14", space=words.amount(space)) if space >= 0 else X.text("NXA-16", over=words.amount(-space)))
    if not short:
        spoken += off._news_texts(told)
    if short:
        for line in spoken:
            g.say2(line)
    else:
        off.wait_for_enter(g, ([] if asked else [header]) + spoken + [X.text("NXE-03")])


def _own_cap_choice(g, words, league, waiting: dict, released: list) -> list:
    """The player's team is over the salary cap after his own choice (SX.8g, design 7.6 and contracts.cap_over): he releases players
    himself, the dearest for what they give first as the staff would, until the cap after the cut and the fill is met. Returns the
    players released besides `released`; nothing when the team is under the cap."""
    team = league.team
    extra: list = []
    while CT.cap_over(league, team, waiting, released + extra) > 0:
        candidates = CT.cap_candidates(league, team, waiting, released + extra)
        if not candidates:
            break                                              # nobody saves anything: the simulation's invariant reports it
        situation = X.text("NXA-13", over=words.amount(CT.cap_over(league, team, waiting, released + extra)))
        choice = candidates[FranchiseQuestion(g, situation, [words.released_for_the_cap(pl) for pl in candidates]).ask()]
        extra.append(choice)
        g.say2(X.text("NXE-55", player=choice.name))
    return extra


def _own_choice(g, words, league, waiting: dict) -> list:
    """The player releases the players himself: for each group with too many players a question over the group's players, the staff's
    choices first, Enter releases the current one until the group fits (design 7.6). Returns the players released."""
    team = league.team
    released = []
    for position in D.ROSTER_ORDER:
        remaining = DR.release_order(DR.group_players(league, team, position, waiting))
        size = D.GROUP_SIZE[position]
        chose = len(remaining) > size                              # the player is asked about this group
        while len(remaining) > size:
            situation = X.text("NXE-54", position=words.group(position), n=len(remaining), m=size)
            choice = remaining.pop(FranchiseQuestion(g, situation, [words.player(pl) for pl in remaining]).ask())
            released.append(choice)
            g.say2(X.text("NXE-55", player=choice.name))
        if not chose:                                              # a group he was not asked about: the staff's floor still applies
            released += DR.floor_releases(remaining, position)     # (in a group he chose from, the players he kept are his decision)
    return released


# ----- stage 4: the undrafted free agents (SX.8m) -----

def _undrafted_choice(g, words, draft, league) -> list:
    """The player's offers of a place in camp to the undrafted free agents (nothing has changed yet): the staff's offers, his own choice, or nobody. Returns
    (the offers (`undrafted.Offer`), True when he chose them himself: his choice is not held to the staff's need rule)."""
    team = league.team
    prospects = UD.pool(draft)
    if not prospects or UD.signed_by(draft, team) >= T.FR_UDFA_MAX:
        return [], False
    staff = UD.team_offers(draft, team, prospects)
    names = {p.index: p for p in prospects}
    situation = [X.text("NXU-24", n=len(prospects), m=T.FR_UDFA_MAX)]
    situation.append(X.text("NXU-25", list=", ".join(names[o.prospect].name for o in staff)) if staff else X.text("NXU-26"))
    answer = FranchiseQuestion(g, situation, [X.text("NXU-A04"), X.text("NXU-A05"), X.text("NXU-A06")]).ask()
    if answer == 0:
        return staff, False
    if answer == 2:
        return [], False
    ranked = sorted(prospects, key=lambda p: (-draft.value(p, draft.needs(team)), p.index))       # the most valuable to his team first
    chosen: list = []
    start = 0
    notice: list = []
    while True:
        lines = [words.prospect_line(p.name, p.pos, p.low, p.high, p.age, p.potential) + ("," + X.text("NXU-C01") if p.index in chosen else "")
                 for p in ranked]
        start = FranchiseQuestion(g, notice + [X.text("NXU-27")], [X.text("NXU-A07")] + lines, start=start).ask()
        if start == 0:                                  # "done" is the first item: the list is long and paged, and Enter alone ends it
            return [UD.Offer(team, index) for index in chosen], True
        prospect = ranked[start - 1]
        if prospect.index in chosen:
            chosen.remove(prospect.index)
            notice = [X.text("NXU-29", player=prospect.name)]
        elif len(chosen) >= T.FR_UDFA_CHASE:
            notice = [X.text("NXU-30")]
        else:
            chosen.append(prospect.index)
            notice = [X.text("NXU-28", player=prospect.name)]


def _undrafted_lines(words, league, draft, udfa, offers: list, short: bool) -> list:
    """What the player hears of the undrafted market: who signed with his team (by range, as his rookies), his offers that went elsewhere, and (a full
    offseason) the league's count."""
    team = league.team
    lines = []
    own = [(prospect, player) for prospect, t, player in udfa.signed if t == team]
    if own:
        lines.append(X.text("NXU-20"))
        lines += [words.prospect_line(player.name, player.pos, prospect.low, prospect.high, player.age, player.potential) for prospect, player in own]
    won = {prospect.index: (t, prospect) for prospect, t, _ in udfa.signed}
    for offer in offers:
        other, prospect = won.get(offer.prospect, (None, None))
        if other is not None and other != team:
            lines.append(X.text("NXU-22", player=prospect.name, team=words.team_name(other)))
        elif other is None:                                   # nobody signed him: his team had filled its places in camp (the review of SX.8m)
            lines.append(X.text("NXU-31", player=draft.prospects[offer.prospect].name))
    if not short and udfa.signed:
        lines.append(X.text("NXU-23", n=len(udfa.signed)))
    return lines
