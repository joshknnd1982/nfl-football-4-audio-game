"""First names for the Franchise's made-up players (nfl4 only, rule 0.13; D-131). This is inspired by Jim Kitchen.

The league draws a made-up player's name from the original's 1,708 surnames (`league.draw_name`), so free agents, draft prospects, the
undrafted rookies of the roster cut and the stand-ins of injuries had a surname only ("Berry"), which a listener takes for a first name (the
owner's report of 2026-10-23: "free agents must have both first and last names. As of now they only have first names."). Each made-up player
now gets a first name too, chosen WITHOUT a draw from a hash of the league's ID and the surname, so the league's random draws and every
rating, age and pick stay exactly what they were. Real players (SX.11) keep their real names.

The list: common English given names, one word each (no space, so "First Surname" splits back at the first space), plain to every speech
voice.
"""
import zlib

FIRST_NAMES = (
    "Aaron", "Adam", "Adrian", "Alan", "Albert", "Alex", "Andre", "Andrew", "Anthony", "Antonio", "Austin", "Avery",
    "Barry", "Ben", "Benjamin", "Blake", "Brad", "Bradley", "Brandon", "Brent", "Brett", "Brian", "Brandon", "Bruce", "Bryan", "Bryce",
    "Caleb", "Calvin", "Cameron", "Carl", "Carlos", "Carson", "Carter", "Casey", "Chad", "Charles", "Chase", "Chris", "Christian", "Clay",
    "Cody", "Cole", "Colin", "Connor", "Corey", "Craig", "Curtis", "Dallas", "Dalton", "Damon", "Daniel", "Darius", "Darnell", "Darren",
    "David", "Dean", "Dennis", "Derek", "Derrick", "Devin", "Dominic", "Don", "Donald", "Donovan", "Douglas", "Drew", "Dylan", "Eddie",
    "Edward", "Elijah", "Eric", "Ethan", "Evan", "Frank", "Gabriel", "Garrett", "Gary", "George", "Grant", "Greg", "Henry", "Hunter",
    "Ian", "Isaac", "Isaiah", "Jack", "Jackson", "Jacob", "Jake", "Jalen", "Jamal", "James", "Jared", "Jason", "Javon", "Jeff", "Jeremy",
    "Jerome", "Jesse", "Joe", "Joel", "John", "Jonathan", "Jordan", "Joseph", "Josh", "Joshua", "Julian", "Justin", "Kevin", "Keith",
    "Kendall", "Kenny", "Kevin", "Kyle", "Lamar", "Lance", "Larry", "Lawrence", "Leon", "Leonard", "Logan", "Lucas", "Luke", "Malcolm",
    "Marcus", "Mario", "Mark", "Martin", "Mason", "Matt", "Matthew", "Maurice", "Max", "Michael", "Miles", "Mitchell", "Nathan", "Neil",
    "Nick", "Noah", "Oliver", "Omar", "Owen", "Patrick", "Paul", "Peter", "Philip", "Quentin", "Randy", "Ray", "Reggie", "Ricky", "Riley",
    "Robert", "Roger", "Ronald", "Ross", "Russell", "Ryan", "Sam", "Scott", "Sean", "Seth", "Shane", "Shawn", "Spencer", "Stephen",
    "Steve", "Taylor", "Terrell", "Terry", "Thomas", "Tim", "Todd", "Tom", "Tony", "Travis", "Trent", "Trevor", "Tristan", "Troy",
    "Tyler", "Tyrone", "Victor", "Vincent", "Wade", "Walter", "Warren", "Wayne", "Wesley", "Will", "William", "Xavier", "Zach",
)
FIRST_NAMES = tuple(dict.fromkeys(FIRST_NAMES))          # the order kept, each name once


_REAL: frozenset | None = None


def real_full_names() -> frozenset:
    """NX-L12 (D-164): the full names of the real men of the shipped rosters and free agents (casefolded), read once: a made-up man never takes one."""
    global _REAL
    if _REAL is None:
        try:
            from .. import real_names
            names = real_names.defaults()
            _REAL = names.real_full_names() if names is not None else frozenset()
        except Exception:                      # the names never cost a first name
            _REAL = frozenset()
    return _REAL


def first_name(league_id: str, surname: str) -> str:
    """The first name of the made-up player `surname` in league `league_id` (the same every time; no draw). NX-L12: never one that makes the full name of
    a real player of the rosters (the next name of the list then)."""
    key = ("%s|%s" % (league_id, surname)).encode("utf-8", "surrogatepass")
    start = zlib.crc32(key) % len(FIRST_NAMES)
    real = real_full_names()
    for step in range(len(FIRST_NAMES)):
        name = FIRST_NAMES[(start + step) % len(FIRST_NAMES)]
        if ("%s %s" % (name, surname)).casefold() not in real:
            return name
    return FIRST_NAMES[start]


def full_name(league_id: str, surname: str) -> str:
    """"First Surname" for a drawn surname; a name that already is the full name is returned as it is."""
    if is_full_name(league_id, surname):
        return surname
    return "%s %s" % (first_name(league_id, surname), surname)


def surname_of(league_id: str, name: str) -> str | None:
    """The drawn surname inside a made-up player's full name, None for any other name (a real player's, a typed one)."""
    if not isinstance(name, str) or " " not in name:
        return None
    first, rest = name.split(" ", 1)
    return rest if first == first_name(league_id, rest) else None


def is_full_name(league_id: str, name: str) -> bool:
    return surname_of(league_id, name) is not None


def name_keys(league_id: str, names) -> set:
    """The names in use as `draw_name` compares them: every name, and the drawn surname inside every made-up full name. A drawn surname is
    in use exactly when it was before the first names existed, so the league's draws do not change."""
    keys = set()
    for name in names:
        keys.add(name)
        surname = surname_of(league_id, name)
        if surname is not None:
            keys.add(surname)
    return keys


def needs_first_name(name, surnames: frozenset) -> bool:
    """A stored name that is a bare drawn surname (a league of 0.12.0 or older, or a player's own roster of the original's draw): one word,
    or one of the original's surnames that has a space ("De Ruijter")."""
    return isinstance(name, str) and bool(name.strip()) and (" " not in name or name in surnames)
