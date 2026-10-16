"""plays.txt, styles.txt and team_styles.txt: the player's part of the playbooks (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

CUSTOMIZABLE_CONTENT 13 (L15), CLAUDE.md 0.12, playbook 7.9, design 10 (N5.7). Three lists of data/customlists.py (the same format
and healing), in the folder `playbooks` of the customize folder, read only while the Rules setting is the N. F. L. rules:

    plays.txt        `O001 = Inside Zone` the spoken name of each play of the catalog (O001 to O052 offense, D001 to D030
                     defense), at most 30 characters and six words; `; off` switches the play off in every style
    styles.txt       the seven styles (S1 Pro Style, S2 West Coast, S3 Air Raid, S4 Power Run, S5 Zone Run, S6 Option, S7 Pressure):
                     `S2O017 = weight 7` a play and the computer's weight for it in that style (`off` or weight 0 removes it, a
                     play that is not in the style is added with a weight), `S2OB1 = families 3 4; vs 1 2 3; sack -2; comp 3` a
                     tilt (O offense or D defense, B bonus or P penalty, 1 to 3: the plays of those families against those calls
                     change by the numbers, each within the bounds of design 10.3), `S5QB = 300` how often the computer's
                     quarterback runs, in percent of the usual
    team_styles.txt  `T01 = Air Raid; defense Pro Style` the style each of the 32 teams' offense (and defense) plays; Classic
                     is the original's plays

The yards, the odds and the rules of the original's plays are not in the files: a play only moves them by a few yards and a few
points, never past the bounds. A line that is not understood or is out of its bounds is a problem (one spoken summary per file)
and its default stays.
"""
from __future__ import annotations

import re
from dataclasses import replace

from . import nx_texts as X
from . import playbook_data as D
from . import playbooks as P

WHOLE = re.compile(r"[+-]?[0-9]+")                # a whole number as the files write it (str.isdigit also takes superscripts)
UNSIGNED = re.compile(r"[0-9]+")
PLAY_ID = re.compile(r"([OD])(\d{1,3})", re.IGNORECASE)
MEMBER_ID = re.compile(r"S([1-7])([OD])(\d{3})", re.IGNORECASE)
TILT_ID = re.compile(r"S([1-7])([OD])([BP])([1-3])", re.IGNORECASE)
QB_ID = re.compile(r"S([1-7])QB", re.IGNORECASE)
TEAM_ID = re.compile(r"T(\d{1,2})", re.IGNORECASE)
WEIGHT_MAX = 100
QB_PERCENT_MAX = 1000
MAX_WORDS = 6
NAME_MIN, NAME_MAX = 1, 30
OFFENSE_FAMILIES = D.OFFENSE_FAMILIES
DEFENSE_FAMILIES = D.DEFENSE_FAMILIES

PLAYS_NOTES = (
    "These are the plays of the playbooks of the N. F. L. rules. The game reads this file only when the Rules setting of the F9 "
    "menu is N. F. L. rules.",
    "Each line is an ID, an equals sign and the name the voice speaks. O001 to O052 are offense plays and D001 to D030 are "
    "defense plays. Change a name to have it said your way.",
    "After the name a semicolon and off switch the play off in every style: O004 = Draw Play; off. Delete a line to get the "
    "original back.",
    "A name has 1 to 30 characters and six words at most, with no comma and no semicolon. A menu shows at most eight plays "
    "in a group.",
)
STYLES_NOTES = (
    "These are the styles of the playbooks of the N. F. L. rules: S1 Pro Style, S2 West Coast, S3 Air Raid, S4 Power Run, "
    "S5 Zone Run, S6 Option and S7 Pressure. The game reads this file only when the Rules setting of the F9 menu is N. F. L. rules.",
    "A line like S2O017 = weight 7 puts play O017 in style S2 for offense (O) or defense (D), and the computer calls it with "
    "that weight. S2O017 = off takes it out. Add a line for a play that is not in the style to put it in.",
    "A line like S2OB1 = families 3 4; vs 1 2 3; sack -2; comp 3 is a tilt. The letters say offense (O) or defense (D) and bonus "
    "(B) or penalty (P), then a number from 1 to 3.",
    "The plays of those play families, against those calls of the other team, change by the numbers: ylo and yhi move the "
    "fewest and the most yards by up to 2, sack and comp move the sack and catch chances by up to 5 points, fum moves the fumble "
    "chance, 1 in 50 by up to 5 either way.",
    "The families of the offense are 1 Line Plunge, 2 End Run, 3 Screen Pass, 4 Short Pass, 5 Long Pass and 8, 9 and 10 the "
    "quarterback's sneak, keeper and draw. The families of the defense are 1 Goal Line, 2 Short Run, 3 Long Run, 4 Blitz, "
    "5 Short Pass and 6 Long Pass.",
    "A line like S5QB = 300 sets how often the computer runs its quarterback in this style, in percent of the usual rate.",
    "A number past its bound is a problem and the original number is used. Delete a line to get the original back.",
)
TEAMS_NOTES = (
    "These are the styles the 32 teams play. The game reads this file only when the Rules setting of the F9 menu is N. F. L. rules.",
    "Each line is an ID, an equals sign and the name of a style: Classic, Pro Style, West Coast, Air Raid, Power Run, Zone Run, "
    "Option or Pressure.",
    "After the name a semicolon and defense and another style name give the team's defense a style of its own: T01 = Air Raid; "
    "defense Pro Style. Without it the defense plays the same style.",
    "Classic is the original's plays. The IDs T01 to T32 are the same as in teams.txt. Delete a line to get the original back.",
)


# ----- the built-in text of each file -----

def _style_number(key: str) -> int:
    return [s.key for s in D.STYLES].index(key) + 1


def tilt_text(tilt: D.Tilt) -> str:
    parts = ["families " + " ".join(str(f) for f in tilt.families), "vs " + " ".join(str(v) for v in tilt.vs)]
    parts += ["%s %d" % (name, value) for name, value in zip(D.MOD_NAMES, tilt.mod) if value]
    return "; ".join(parts)


def default_plays() -> list[tuple[str, str]]:
    return [(play.id, X.text(play.name_id)) for play in D.CATALOG]


def default_styles() -> list[tuple[str, str]]:
    entries = []
    for number, style in enumerate(D.STYLES, start=1):
        entries += [("S%d%s" % (number, pid), "weight %d" % w) for pid, w in style.offense]
        entries += [("S%d%s" % (number, pid), "weight %d" % w) for pid, w in style.defense]
        for name, tilts in (("OB", style.off_bonus), ("OP", style.off_penalty), ("DB", style.def_bonus),
                            ("DP", style.def_penalty)):
            entries += [("S%d%s%d" % (number, name, n), tilt_text(t)) for n, t in enumerate(tilts, start=1)]
        entries.append(("S%dQB" % number, str(style.qb_percent)))
    return entries


def default_teams() -> list[tuple[str, str]]:
    entries = []
    for number, (offense, defense) in enumerate(D.TEAM_STYLES, start=1):
        name = P.DEFAULT_TABLE.style_name(offense)
        other = P.DEFAULT_TABLE.style_name(defense)
        entries.append(("T%02d" % number, name if offense == defense else "%s; defense %s" % (name, other)))
    return entries


# ----- reading -----

def _options(value: str) -> tuple[str, list[str]]:
    parts = [part.strip() for part in value.split(";")]
    return parts[0], [part for part in parts[1:] if part]


def _name_problem(name: str) -> str | None:
    from ..data.customize import name_problem          # the limits of every list's names (CUSTOMIZABLE_CONTENT 10)
    reason = name_problem(name)
    if reason:
        return reason
    if len(name.split()) > MAX_WORDS:
        return "a play name has at most %d words" % MAX_WORDS
    return None


def apply_plays(table: P.Table, entries, problems) -> P.Table:
    """plays.txt: the names and the switches. An ID that is not a play, a second line for an ID and a name the limits refuse
    (the original name is used) are problems; an option that is not `off` or `on` is ignored."""
    names = {pid: X.text(play.name_id) for pid, play in D.PLAYS.items()}
    disabled: set[str] = set()
    seen: set[str] = set()
    for entry in entries:
        match = PLAY_ID.fullmatch(entry.id)
        key = "%s%03d" % (match.group(1).upper(), int(match.group(2))) if match else ""
        if key not in D.PLAYS:
            problems.add("line %d" % entry.line,
                         "the ID %s is not a play of this game (O001 to O052, D001 to D030), the line is ignored" % entry.id)
            continue
        if key in seen:
            problems.add(key, "this ID is there twice, the first line is used")
            continue
        seen.add(key)
        name, options = _options(entry.value)
        for option in options:
            word = option.casefold()
            if word == "off":
                disabled.add(key)
            elif word != "on":
                problems.add(key, "'%s' is not off or on, it is ignored" % option[:30])
        if not name:
            problems.add(key, "the line has no name, the original name is used")
            continue
        reason = _name_problem(name)
        if reason:
            problems.add(key, "%s, the original name is used" % reason)
        else:
            names[key] = name
    return replace(table, names=names, disabled=frozenset(disabled))


def _numbers(words: list[str], allowed, what: str) -> tuple[tuple[int, ...] | None, str]:
    values = []
    for word in words:
        if not WHOLE.fullmatch(word) or int(word) not in allowed:
            return None, "%s %s is not one of %s" % (what, word[:12], " ".join(str(a) for a in allowed))
        if int(word) not in values:
            values.append(int(word))
    if not values:
        return None, "%s needs at least one number" % what
    return tuple(values), ""


def parse_tilt(role: str, value: str) -> tuple[D.Tilt | None, str]:
    """(the tilt, "") or (None, the plain reason). `role` O or D: an offense tilt's families are the offense's and its calls are
    the defense's, a defense tilt's the other way round."""
    families_allowed = OFFENSE_FAMILIES if role == "O" else DEFENSE_FAMILIES
    vs_allowed = DEFENSE_FAMILIES if role == "O" else OFFENSE_FAMILIES
    families = vs = None
    mod = dict.fromkeys(D.MOD_NAMES, 0)
    for part in (p.strip() for p in value.split(";")):
        words = part.casefold().split()
        if not words:
            continue
        if words[0] == "families":
            families, reason = _numbers(words[1:], families_allowed, "the family")
        elif words[0] == "vs":
            vs, reason = _numbers(words[1:], vs_allowed, "the call")
        elif words[0] in mod and len(words) == 2:
            if not WHOLE.fullmatch(words[1]):
                return None, "%s %s is not a whole number" % (words[0], words[1][:12])
            amount = int(words[1])
            limit = D.BOUNDS[D.MOD_NAMES.index(words[0])]
            if abs(amount) > limit:
                return None, "%s %d is past the bound %d" % (words[0], amount, limit)
            mod[words[0]] = amount
            continue
        else:
            return None, "'%s' is not families, vs, ylo, yhi, sack, comp or fum with a number" % part[:30]
        if reason:
            return None, reason
    if families is None or vs is None:
        return None, "a tilt needs families and vs"
    return D.Tilt(families, vs, D.Mod(*(mod[name] for name in D.MOD_NAMES))), ""


def _style_line(entry, by_number, styles, seen, problems) -> None:
    """One line of styles.txt over `styles` (the built-in styles, changed in place)."""
    key = entry.id.upper()
    if key in seen:
        problems.add(key, "this ID is there twice, the first line is used")
        return
    seen.add(key)
    member, tilt, qb = MEMBER_ID.fullmatch(key), TILT_ID.fullmatch(key), QB_ID.fullmatch(key)
    if member:
        style = by_number[int(member.group(1))]
        play_id = member.group(2) + member.group(3)
        if play_id not in D.PLAYS:
            problems.add(key, "there is no play %s in this game, the line is ignored" % play_id)
            return
        members = styles[style.key].offense if member.group(2) == "O" else styles[style.key].defense
        name, options = _options(entry.value)
        words = [w for part in [name] + options for w in part.casefold().split()]
        if words == ["off"]:
            members.pop(play_id, None)
        elif len(words) == 2 and words[0] == "weight" and UNSIGNED.fullmatch(words[1]) and int(words[1]) <= WEIGHT_MAX:
            if int(words[1]) == 0:
                members.pop(play_id, None)
            else:
                members[play_id] = int(words[1])
        elif words == ["on"]:
            members.setdefault(play_id, 1)
        else:
            problems.add(key, "the line is not off, on or weight 0 to %d, the original is used" % WEIGHT_MAX)
    elif tilt:
        style = by_number[int(tilt.group(1))]
        tilt_id = tilt.group(2) + tilt.group(3) + tilt.group(4)
        if entry.value.strip().casefold() == "off":
            styles[style.key].tilts.pop(tilt_id, None)
            return
        parsed, reason = parse_tilt(tilt.group(2), entry.value)
        if parsed is None:
            problems.add(key, "%s, the original is used" % reason)
        else:
            styles[style.key].tilts[tilt_id] = parsed
    elif qb:
        style = by_number[int(qb.group(1))]
        if UNSIGNED.fullmatch(entry.value) and int(entry.value) <= QB_PERCENT_MAX:
            styles[style.key] = replace(styles[style.key], qb_percent=int(entry.value))
        else:
            problems.add(key, "the line is not a percent from 0 to %d, the original is used" % QB_PERCENT_MAX)
    else:
        problems.add("line %d" % entry.line, "the ID %s is not a style line (S1O001, S1OB1, S1QB), the line is ignored"
                     % entry.id)


def apply_styles(table: P.Table, entries, problems) -> P.Table:
    """styles.txt over the table's styles. A line that is not understood or is out of its bounds is a problem and the default
    of its ID stays; `off` takes a play or a tilt out."""
    by_number = {number: style for number, style in enumerate(D.STYLES, start=1)}
    # the defaults are the data's, so a file that lacks a line (or a style) keeps it: start from the built-in styles
    styles = {style.key: P.style_book(style) for style in D.STYLES}
    seen: set[str] = set()
    for entry in entries:
        try:
            _style_line(entry, by_number, styles, seen, problems)
        except (ValueError, KeyError, IndexError, TypeError, AttributeError) as exc:     # one line never costs the file
            problems.add(entry.id.upper(), "the line could not be used (%s), the original is used" % type(exc).__name__)
    return replace(table, styles=styles)


def style_choice(name: str, table: P.Table) -> str | None:
    """The style key a name or key stands for (Classic, Pro Style, west, ...), or None."""
    word = name.strip().casefold()
    if not word:
        return None
    if word == X.text("NXM-27").casefold() or word == P.CLASSIC:
        return P.CLASSIC
    for style in D.STYLES:
        if word in (X.text(style.name_id).casefold(), style.key):
            return style.key
    return None


def apply_teams(table: P.Table, entries, problems) -> P.Table:
    teams = list(D.TEAM_STYLES)
    seen: set[int] = set()
    for entry in entries:
        match = TEAM_ID.fullmatch(entry.id)
        number = int(match.group(1)) if match else 0
        if not 1 <= number <= len(teams):
            problems.add("line %d" % entry.line, "the ID %s is not a team (T01 to T32), the line is ignored" % entry.id)
            continue
        if number in seen:
            problems.add(entry.id, "this ID is there twice, the first line is used")
            continue
        seen.add(number)
        name, options = _options(entry.value)
        offense = style_choice(name, table)
        defense = offense
        bad = offense is None
        for option in options:
            words = option.split(None, 1)
            if len(words) == 2 and words[0].casefold() == "defense":
                defense = style_choice(words[1], table)
                bad = bad or defense is None
            else:
                problems.add(entry.id, "'%s' is not defense and a style, it is ignored" % option[:30])
        if bad:
            problems.add(entry.id, "the style %s is not Classic or one of the seven styles, the original is used" % name[:30])
            continue
        teams[number - 1] = (offense, defense)
    return replace(table, teams=tuple(teams))
