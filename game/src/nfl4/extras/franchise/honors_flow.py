"""The awards and the hall of fame in words: stage 1's lines, the history menu's lists and history.txt (nfl4 only, rule 0.13). This is inspired by Jim
Kitchen.

NFL_FRANCHISE_DESIGN 17 SX.8o (D-076). The rules are `honors.py`; this module only makes the sentences (rows NXG- of spec\\strings_nx.tsv).
"""
from __future__ import annotations

from .. import nx_texts as X
from . import honors


def award_name(award: str) -> str:
    return X.text(honors.AWARD_TEXT[award])


def award_line(league, words, row: list) -> str:
    """Stage 1's sentence of one award row: the player's own player and the player himself are named so (NXG-B03, NXG-B05)."""
    _season, award, pid, name, position, team = row
    if award == "coy":
        if team == league.team:
            return X.text("NXG-B05", award=award_name(award), coach=league.coach)
        return X.text("NXG-B04", award=award_name(award), name=name, team=words.team_name(team))
    if team == league.team:
        return X.text("NXG-B03", award=award_name(award), player=name, position=words.award_position(league, pid, position))
    return X.text("NXG-B02", award=award_name(award), player=name, position=words.award_position(league, pid, position), team=words.team_name(team))


def member_line(words, player) -> str:
    return X.text("NXG-B07", player=player.name, position=words.position_for(player), team=words.team_name(player.team), n=player.seasons, r=player.peak)


def stage_lines(league, words, awards: list, inducted: list) -> list:
    """Stage 1: the season's awards, then the hall's new class (nothing about the hall when nobody enters)."""
    lines = [X.text("NXG-B01")] + [award_line(league, words, row) for row in awards] if awards else []
    if inducted:
        lines.append(X.text("NXG-B06"))
        lines += [member_line(words, player) for player in inducted]
    return lines


def short_lines(league, words, awards: list, inducted: list) -> list:
    """Stage 1 with the offseason short: the most valuable player and the size of the hall's class."""
    lines = [award_line(league, words, row) for row in awards if row[1] == "mvp"]
    if inducted:
        lines.append(X.text("NXG-B09") if len(inducted) == 1 else X.text("NXG-B08", n=len(inducted)))
    return lines


# ----- the history menu -----

def award_lines(league, words) -> list:
    """NXG-20 and NXG-21: every award, the newest season first, in the order of the awards."""
    rows = sorted(league.honors["awards"], key=lambda row: (-row[0], honors.AWARDS.index(row[1])))
    out = []
    for season, award, pid, name, position, team in rows:
        if award == "coy":
            out.append(X.text("NXG-21", n=season, award=award_name(award), name=name, team=words.team_name(team)))
        else:
            out.append(X.text("NXG-20", n=season, award=award_name(award), player=name, position=words.award_position(league, pid, position), team=words.team_name(team)))
    return out


def hall_lines(league, words) -> list:
    """NXG-22: the hall's members, the newest class first."""
    return [X.text("NXG-22", player=p.name, position=words.position_for(p), team=words.team_name(p.team), n=p.seasons, r=p.peak, s=season)
            for p, season in honors.hall_members(league)]


# ----- history.txt (design 9.3) -----

def text_lines(league, words) -> list:
    """history.txt's parts "Awards" and "Hall of fame" (none while they are empty)."""
    out = []
    rows = sorted(league.honors["awards"], key=lambda row: (-row[0], honors.AWARDS.index(row[1])))
    if rows:
        out += ["", "Awards"]
        for season, award, pid, name, position, team in rows:
            who = name if award == "coy" else "%s, %s" % (name, words.award_position(league, pid, position).strip())
            out.append("%s, season %d: %s, the %s." % (_sentence(award_name(award)), season, who, words.team_name(team)))
    members = honors.hall_members(league)
    if members:
        out += ["", "Hall of fame"]
        for p, season in members:
            out.append("%s, %s, %s, %d seasons, best rating %d, entered in season %d." %
                       (p.name, words.position_for(p).strip(), words.team_name(p.team), p.seasons, p.peak, season))
    return out


def _sentence(text: str) -> str:
    text = text.strip()
    return text[:1].upper() + text[1:]
