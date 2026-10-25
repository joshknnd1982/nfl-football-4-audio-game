"""F9, Rules, Depth charts: set the starters and the players for the key downs and moments (nfl4 only, rule 0.13; NX-D3, NX-D4, D-147). This is inspired
by Jim Kitchen.

Outside a franchise: the 32 teams (letters find one), a team's groups (each said with its first man), a group's players in order (Enter makes one the first),
"key downs and moments" (Enter on a situation and role lists the backs or the receivers, "the starter" first), and "back to the real order". The choices
are the settings nx_depth and nx_key_players (extras/depth_chart.py), used from the next game. In a franchise: the player's own team, from the league
(extras/franchise/depth.py), kept in league.sav and used at once; "back to the staff's order". The rules are in those two modules; this one speaks.
"""
from __future__ import annotations

from ..data import debuglog
from ..game.spoken_menu import Item, ListPicker, SpokenMenu
from . import depth_chart as DC
from . import nx_texts as X

GROUP_TEXT = {"RB": "NXM-D20", "WR": "NXM-D21", "TE": "NXM-D22", "DL": "NXM-D23", "LB": "NXM-D24", "CB": "NXM-D25", "S": "NXM-D26", "K": "NXM-D27",
              "P": "NXM-D28", "RET": "NXM-D29"}
POSITION_TEXT = {"RB": "NXM-D30", "FB": "NXM-D31", "WR": "NXM-D32", "TE": "NXM-D33", "DL": "NXM-D34", "LB": "NXM-D35", "CB": "NXM-D36", "S": "NXM-D37",
                 "K": "NXM-D38", "P": "NXM-D39", "QB": "NXM-D40", "OL": "NXM-D41", "LS": "NXM-D42", "RET": "NXM-D29"}
SITUATION_TEXT = {"down": "NXM-K05", "redzone": "NXM-K06", "twominute": "NXM-K07"}
ROLE_TEXT = {"back": "NXM-K08", "receiver": "NXM-K09"}
FRANCHISE_GROUP = {"RB": "RB", "WR": "WR", "DL": "DL", "LB": "LB", "CB": "CB", "S": "S", "RET": "RET", "K": "K", "P": "P"}


def item_label(settings) -> str:
    return X.text("NXM-D01") + ("" if settings.rules == "nfl" else X.text("NXM-22"))


def group_word(group: str) -> str:
    return X.text(GROUP_TEXT[group])


def position_word(pos: str) -> str:
    return X.text(POSITION_TEXT.get(pos, "NXM-D30"))


def depth_menu(game, speech, keys) -> None:
    def say(text: str) -> None:
        speech.stop()
        speech.say_async(text)

    store = game.franchise() if getattr(game, "franchise_in_use", False) else None
    if store is not None and store.league is not None:
        _franchise_menu(game, speech, keys, store, say)
        return
    real = getattr(game, "real_names", None)
    if real is None:
        say(X.text("NXJ-Q20") if game.options.settings.game.rules != "nfl" else X.text("NXJ-Q10"))
        return
    _quick_menu(game, speech, keys, say)


# ----- outside a franchise -----

def _quick_menu(game, speech, keys, say) -> None:
    from .franchise.league import team_ref
    from . import quarterbacks
    settings = game.options.settings.game

    def team_name(team: int) -> str:
        return game.league.team(*team_ref(team))

    def search(text: str):
        text = text.casefold()
        return next((team - 1 for team in range(1, DC.TEAMS + 1) if team_name(team).casefold().startswith(text)), None)

    def real():
        return game.real_names

    def save(depth=None, keys_=None) -> None:
        if depth is not None:
            settings.nx_depth = DC.render_depth(depth)
        if keys_ is not None:
            settings.nx_key_players = DC.render_keys(keys_)
        game.options.save()
        quarterbacks.apply(game)                               # the next game (and a new franchise) uses the new order

    def open_team(index: int):
        team = index + 1

        def players(group: str) -> list:
            return DC.group_players(real(), team, group) if group != "RET" else DC.group_players(real(), team, "RET")

        def first_label(group: str) -> str:
            members = players(group)
            return X.text("NXM-D04", group=group_word(group), player=real().spoken(members[0].name)) if members else \
                X.text("NXM-D43", group=group_word(group))

        def open_group(group: str):
            members = players(group) if group != "RET" else DC.return_candidates(real(), team)
            if not members:
                return X.text("NXM-D14")
            lines = [X.text("NXM-D06", player=real().spoken(p.name), position=position_word(p.pos)) for p in members]
            chosen = ListPicker(speech, keys, X.text("NXM-D05", group=group_word(group), team=team_name(team)), len(lines), lambda i: lines[i]).run()
            if chosen is None:
                return None
            pick = members[chosen]
            current = [p.name for p in (players(group) if group != "RET" else DC.return_candidates(real(), team))]
            depth = DC.put_first(DC.parse_depth(settings.nx_depth), team, group, pick.name, current)
            save(depth=depth)
            debuglog.event("extras", "depth_set", team=team, group=group, first=pick.name)         # rule 0.15
            return X.text("NXM-D08", player=real().spoken(pick.name), group=group_word(group))

        def reset():
            save(depth=DC.reset_team(DC.parse_depth(settings.nx_depth), team),
                 keys_={t: k for t, k in DC.parse_keys(settings.nx_key_players).items() if t != team})
            debuglog.event("extras", "depth_reset", team=team)
            return X.text("NXM-D11", team=team_name(team))

        def keys_menu():
            def label(situation: str, role: str) -> str:
                name = DC.parse_keys(settings.nx_key_players).get(team, {}).get((situation, role))
                who = real().spoken(name) if name else X.text("NXM-K04")
                return X.text("NXM-K03", situation=X.text(SITUATION_TEXT[situation]), group=X.text(ROLE_TEXT[role]), player=who)

            def choose(situation: str, role: str):
                groups = ("RB",) if role == "back" else ("WR", "TE")
                members = [p for g in groups for p in DC.group_players(real(), team, g)]
                lines = [X.text("NXM-K04")] + [X.text("NXM-D06", player=real().spoken(p.name), position=position_word(p.pos)) for p in members]
                chosen = ListPicker(speech, keys, label(situation, role), len(lines), lambda i: lines[i]).run()
                if chosen is None:
                    return None
                all_keys = DC.parse_keys(settings.nx_key_players)
                mine = dict(all_keys.get(team, {}))
                if chosen == 0:
                    mine.pop((situation, role), None)
                else:
                    mine[(situation, role)] = members[chosen - 1].name
                all_keys = {t: k for t, k in all_keys.items() if t != team}
                if mine:
                    all_keys[team] = mine
                save(keys_=all_keys)
                debuglog.event("extras", "key_player_set", team=team, situation=situation, role=role,
                               player=None if chosen == 0 else members[chosen - 1].name)                 # rule 0.15
                where = X.text(SITUATION_TEXT[situation])
                return X.text("NXM-K11", situation=where) if chosen == 0 else \
                    X.text("NXM-K10", situation=where, player=real().spoken(members[chosen - 1].name))
            items = [Item(lambda s=s, r=r: label(s, r), enter=lambda s=s, r=r: choose(s, r)) for s in DC.SITUATIONS for r in DC.ROLES]
            SpokenMenu(speech, keys, X.text("NXM-K02"), items, space_enters=True, digits_jump=True).run()
            return None

        items = [Item(lambda g=g: first_label(g), enter=lambda g=g: open_group(g)) for g, _p in DC.GROUPS]
        items += [Item(lambda: X.text("NXM-K01"), enter=keys_menu), Item(lambda: X.text("NXM-D09"), enter=reset)]
        SpokenMenu(speech, keys, X.text("NXM-D03", team=team_name(team)), items, space_enters=True, digits_jump=True).run()
        return None

    start = 0
    season = getattr(game, "season", None)
    if season is not None and 1 <= getattr(season, "tn1", 0) <= 8 and 1 <= getattr(season, "tn2", 0) <= 4:
        from .franchise.league import team_index
        start = team_index(season.tn1, season.tn2) - 1
    ListPicker(speech, keys, X.text("NXM-D02"), DC.TEAMS, lambda i: team_name(i + 1), on_enter=open_team, close_on_enter=False,
               search=search, start=start).run()


# ----- in a franchise: the player's own team -----

def _franchise_menu(game, speech, keys, store, say) -> None:
    from .franchise import depth as FD
    league = store.league
    words = store.words

    def members(group: str) -> list:
        return FD.chart_of(league, FRANCHISE_GROUP[group])                             # D-149: the places, then the bench

    def first_label(group: str) -> str:
        found = members(group)
        return X.text("NXM-D04", group=group_word(group), player=found[0].name) if found else X.text("NXM-D43", group=group_word(group))

    def open_group(group: str):
        if game.play_engine is not None:
            return X.text("NXI-54")                                # the game has begun: the lineup is the game's
        found = members(group)
        if not found:
            return X.text("NXM-D14")
        lines = [X.text("NXM-D07", player=p.name, position=words.position_of(p), r=p.rating, a=p.age) for p in found]
        chosen = ListPicker(speech, keys, X.text("NXM-D05", group=group_word(group), team=words.team_name(league.team)), len(lines),
                            lambda i: lines[i]).run()
        if chosen is None:
            return None
        pick = found[chosen]
        placed = [p for p in found if p.status == "active"]
        FD.put_first(league, FRANCHISE_GROUP[group], pick.id)
        benched = [p for p in placed if p.status == "reserve"]                          # D-149: the man a bench player pushed out of the places
        debuglog.event("franchise", "depth_set", group=group, first=pick.id, benched=[p.id for p in benched])            # rule 0.15
        store.save()                                                                    # written, then told (B-X53)
        told = X.text("NXM-D08", player=pick.name, group=group_word(group))
        return told + "".join(X.text("NXL-55", player=p.name) for p in benched)

    def keys_menu():
        def label(situation: str, role: str) -> str:
            pid = (league.depth or {}).get("key", {}).get(situation, {}).get(role)
            player = league.players.get(pid) if pid else None
            who = player.name if player is not None and player.team == league.team and player.status == "active" else X.text("NXM-K04")
            return X.text("NXM-K03", situation=X.text(SITUATION_TEXT[situation]), group=X.text(ROLE_TEXT[role]), player=who)

        def choose(situation: str, role: str):
            group = "RB" if role == "back" else "WR"
            found = FD.group_of(league, group)
            lines = [X.text("NXM-K04")] + [X.text("NXM-D07", player=p.name, position=words.position(p.pos), r=p.rating, a=p.age) for p in found]
            chosen = ListPicker(speech, keys, label(situation, role), len(lines), lambda i: lines[i]).run()
            if chosen is None:
                return None
            FD.set_key(league, situation, role, None if chosen == 0 else found[chosen - 1].id)
            debuglog.event("franchise", "key_player_set", situation=situation, role=role, player=None if chosen == 0 else found[chosen - 1].id)
            store.save()
            where = X.text(SITUATION_TEXT[situation])
            return X.text("NXM-K11", situation=where) if chosen == 0 else X.text("NXM-K10", situation=where, player=found[chosen - 1].name)
        items = [Item(lambda s=s, r=r: label(s, r), enter=lambda s=s, r=r: choose(s, r)) for s in DC.SITUATIONS for r in DC.ROLES]
        SpokenMenu(speech, keys, X.text("NXM-K02"), items, space_enters=True, digits_jump=True).run()
        return None

    def reset():
        if game.play_engine is not None:
            return X.text("NXI-54")
        FD.reset(league)
        debuglog.event("franchise", "depth_reset")
        store.save()
        return X.text("NXM-D12")

    groups = [g for g, _p in DC.GROUPS if g in FRANCHISE_GROUP]
    items = [Item(lambda g=g: first_label(g), enter=lambda g=g: open_group(g)) for g in groups]
    items += [Item(lambda: X.text("NXM-K01"), enter=keys_menu), Item(lambda: X.text("NXM-D10"), enter=reset)]
    SpokenMenu(speech, keys, X.text("NXM-D03", team=words.team_name(league.team)), items, space_enters=True, digits_jump=True).run()
