"""The kept copies of the three franchises and their restore while playing (nfl4 only, rule 0.13; D-176). This is inspired by Jim Kitchen.

A tester of 0.16.6: "there is no way to get to that backup option except if you start the game and already have a franchise going." A
deleted or replaced franchise is kept (old\\league-1.sav and its companions, three copies a slot, D-173); the start-up menu restores them
(game/startup_menu.py). These functions give F9's Franchise item the same: every kept copy of every slot, named by its team and season, and
the restore into its own slot when that is empty, else into the first empty slot (FranchiseStore.restore_backup). With three franchises
nothing moves.
"""
from __future__ import annotations

from ...data import debuglog
from ...game import save_texts as S
from .league import team_ref

OK, FULL, FAILED = "ok", "full", "failed"


def slot_stores(g) -> dict:
    """{slot: store} of the slots that can be used now. The slot in use is the program's own store; another slot's is opened silently
    (its notices are not this moment's)."""
    out = {}
    for slot in (1, 2, 3):
        in_use = slot == g.franchise_slot
        store = g.franchise() if in_use else g.franchise_peek(slot)
        if not store.opened:
            store.open(in_use and g.options.settings.game.nx_season_kind == "franchise")
            if not in_use:
                store.take_notices()
        if store.available and not store.creating:
            out[slot] = store
    return out


def kept(g) -> list:
    """[(slot, copy number)] of every kept copy, slot by slot, the newest copy first."""
    return [(slot, number) for slot, store in sorted(slot_stores(g).items()) for number in store.backup_numbers()]


def label(g, slot: int, number: int) -> str:
    store = slot_stores(g).get(slot)
    league = store.peek_backup(number) if store is not None else None
    if league is None:
        return S.RESTORE_FRANCHISE_UNREADABLE
    return S.RESTORE_FRANCHISE_COPY % (g.league.team(*team_ref(league.team)), league.season)


def restore(g, slot: int, number: int) -> tuple[str, int | None]:
    """Copy `number` of `slot` becomes a franchise again: (OK, the slot it went to), (FULL, None) with three franchises, (FAILED, None)."""
    slots = slot_stores(g)
    source = slots.get(slot)
    if source is None:
        return FAILED, None
    target = slot if not source.exists else next((s for s in (1, 2, 3) if s in slots and not slots[s].exists), None)
    if target is None:
        debuglog.event("save", "franchise_restore_full", slot=slot, copy=number, where="F9")
        return FULL, None
    ok = source.restore_backup(number, slots[target])
    debuglog.event("save", "franchise_restore_f9", slot=slot, copy=number, target=target, ok=ok)
    return (OK, target) if ok else (FAILED, None)
