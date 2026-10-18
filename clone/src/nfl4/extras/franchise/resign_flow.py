"""Stage 7 of the offseason: the expiring contracts (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 17 SX.8h (F6, N6.6, D-067). The rules are `resign.py` (no speech, no files, no draw); this module speaks, asks the player
and writes league.sav, in the way `draft_flow.py` does for the draft:

* The stage starts with ONE block: the computer's teams (and the player's too when the staff handles it) are settled by `resign.run_teams`,
  the player's own players whose contract ran out are listed in `league.resign["pending"]` (the most valuable first), and the league is
  written. Only then does the stage speak. A window closed at any later moment resumes at the player who is next.
* Each of the player's players is a talk of at most three rounds (`resign.Talk`): sign him at his price, offer less (he accepts, comes down
  halfway to his floor, or in the last round leaves), use the franchise tag (once a year), or let him go. A decision is applied and written
  before it is told (B-X53). Nothing is decided for the player: when the staff does not handle it every player of his is asked, and a window
  closed before the answer leaves him as he was.
* A player who is let go is a free agent ("free"); free agency (SX.8i) is the market they go to, and until it exists stage 6 drops them.
"""
from __future__ import annotations

from .. import nx_texts as X
from .. import tuning as T
from . import data as D
from . import resign as R
from .question import FranchiseQuestion

SIGN, LESS, TAG, OPEN_TAG, GO = "sign", "less", "tag", "open_tag", "go"      # OPEN_TAG: the non-exclusive tag (SX.8m)
ANSWER_TEXT = {SIGN: "NXW-A01", LESS: "NXW-A02", GO: "NXW-A03"}


def _offseason():
    from . import offseason                      # the stage helpers and the wait live there (a late import: offseason imports this module)
    return offseason


def stage_contracts(p, n: int, m: int, short: bool) -> None:
    off = _offseason()
    g, store = p.g, p.store
    league = store.league
    words = store.words
    staff = bool(g.options.settings.game.nx_fr_auto)
    if league.resign is None:                    # the stage starts: the other teams are settled, the player's players wait; written before anything is said
        league.resign = R.begin(league, staff)
        store.save()
    state = league.resign
    intro = [off._stage_line(n, m, "NXE-17")]
    if state["league_gone"]:
        intro.append(X.text("NXW-41", n=state["league_gone"]))
    if not short:
        for pid in state["stars"]:
            star = league.players[pid]
            intro.append(X.text("NXW-40", player=star.name, team=words.team_name(star.team), position=words.position(star.pos), r=star.rating))
    if staff:
        own = X.text("NXW-30", n=state["signed"], m=state["let_go"]) if state["signed"] or state["let_go"] else X.text("NXW-02")
    elif state["pending"]:
        own = (X.text("NXW-01", coach=league.coach, n=len(state["pending"])) if len(state["pending"]) > 1
               else X.text("NXW-06", coach=league.coach))
    else:
        own = X.text("NXW-02")
    preface = intro + [own]
    asked = False
    while state["pending"]:
        if g.options.settings.game.nx_fr_auto:   # read at every step: the staff setting turned on in F9 hands the rest of the players to the staff
            plan = R.plan_team(league, league.team)
            R.apply_plan(league, plan)
            state["pending"] = []
            state["signed"] += len(plan.signed)
            state["let_go"] += len(plan.gone)
            store.save()                         # written before it is told
            if not asked:
                for line in preface[:-1]:        # the stage's lines without "you will be asked about each one"
                    g.say2(line)
            g.say2(X.text("NXW-30", n=len(plan.signed), m=len(plan.gone)))
            asked = True
            break
        _talk(g, words, store, league, state, league.players[state["pending"][0]], preface if not asked else [])
        asked = True
    closing = []
    if asked:
        closing.append(X.text("NXW-31", n=state["signed"], m=state["let_go"]))
    league.resign = None
    league.stage_no = off._next_stage(D.STAGE_CONTRACTS)
    store.save()
    if short:
        for line in (preface if not asked else []) + closing:
            g.say2(line)
    else:
        off.wait_for_enter(g, ([] if asked else preface) + closing + [X.text("NXE-03")])


def _talk(g, words, store, league, state: dict, player, preface: list) -> None:
    """One player's talk until he is settled (signed, tagged or let go): the decision is applied and written, then told."""
    team = league.team
    how = R.mood(league, team)
    talk = R.Talk.start(player, how)
    tag_price = R.tag_salary(league, player)
    from . import tags
    open_price = tags.nonexclusive_salary(league, player)
    lines = list(preface)
    lines.append(X.text("NXW-03", player=player.name, position=words.position(player.pos), a=player.age, r=player.rating,
                        potential=words.potential(player.potential), mood=words.mood(how), contract=words.contract_of(talk.ask, talk.years)))
    while True:
        space = R.room(league, team)
        kinds = []
        if talk.ask <= space:
            kinds.append(SIGN)
        if R.lower_offer(talk.ask, talk.least) < talk.ask and R.lower_offer(talk.ask, talk.least) <= space:      # (nothing is lower than his minimum)
            kinds.append(LESS)
        if not state["tag_used"] and tag_price <= space:
            kinds.append(TAG)
        if not state["tag_used"] and open_price <= space:
            kinds.append(OPEN_TAG)                    # SX.8m: other teams may make him an offer at free agency
        kinds.append(GO)
        if SIGN in kinds or LESS in kinds:
            lines.append(X.text("NXW-04", room=words.amount(space)))
        else:
            lines.append(X.text("NXW-05", room=words.amount(space)) if space >= 0 else X.text("NXW-07"))
        items = [X.text("NXW-A04", contract=words.contract_of(tag_price, 1)) if kind == TAG
                 else X.text("NXU-A10", contract=words.contract_of(open_price, 1)) if kind == OPEN_TAG else X.text(ANSWER_TEXT[kind]) for kind in kinds]
        kind = kinds[FranchiseQuestion(g, lines, items).ask()]
        if kind == LESS:
            result, salary = talk.offer_less()
            if result == R.COUNTER:
                lines = [X.text("NXW-11", player=player.name, contract=words.contract_of(talk.ask, talk.years), round=talk.round,
                                m=T.FR_TALK_ROUNDS)]
                continue
            kind = SIGN if result == R.ACCEPTED else GO
            ended = result == R.ENDED
            talk.ask = salary if result == R.ACCEPTED else talk.ask
        else:
            ended = False
        break
    state["pending"].pop(0)
    if kind == SIGN:
        R.sign_again(league, player, talk.ask, talk.years)
        state["signed"] += 1
        text = X.text("NXW-10", player=player.name, contract=words.contract_of(talk.ask, talk.years))
    elif kind == TAG:
        R.sign_again(league, player, tag_price, 1)
        state["signed"] += 1
        state["tag_used"] = 1
        text = X.text("NXW-14", player=player.name, contract=words.contract_of(tag_price, 1))
    elif kind == OPEN_TAG:
        R.sign_again(league, player, open_price, 1)
        state["signed"] += 1
        state["tag_used"] = 1
        league.tags["open"] = [player.id, league.season]          # free agency (stage 8) asks the other teams
        text = X.text("NXU-57", player=player.name, contract=words.contract_of(open_price, 1))
    else:
        R.let_go(league, player)
        state["let_go"] += 1
        text = X.text("NXW-12" if ended else "NXW-13", player=player.name)
    store.save()                                  # written before it is told (B-X53)
    g.say2(text)
