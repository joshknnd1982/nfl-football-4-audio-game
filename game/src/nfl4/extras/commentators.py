"""The color analyst's name (nfl4 only, rule 0.13; SZ.1, D-106; BC.2, D-178, D-180). This is inspired by Jim Kitchen.

The owner (2026-10-26): "You need to forget and get rid of all of Jim Kitchen's commentary and commenting code for Gip and other
commenters." So the original's character (Ghip) and the list of real podcasters' names the player could give him (D-106) are gone from
every mode: the analyst of the radio broadcast (extras/broadcast.py) is a made-up person, Gus Delgado (spec/NFL_BROADCAST_DESIGN.md
section 3, checked by a web search for a real broadcaster of that name on 2026-10-26), and the player may type another name in F9, Rules,
Commentator (nobody has to type anything, rule 0.19). BC.3 turns the item into the broadcast crew's four names.

The name is the setting `nx_commentator`. Every default line that turns to the analyst says `<commentator>` (strings_nx.tsv) and the name
is put in when the line is said (extras/remarks.py), so a name chosen in the menu is heard everywhere.

    DEFAULT        "Gus Delgado"
    clean(name)    a typed or stored name made safe to speak and store, "" when it cannot be used
    name_of_text(name)  the name a stored or given text stands for: the default when it is empty, unusable or a retired name
    choices(current)    the items of the list: the default, the player's own name when it is not the default, the item that types one
"""
from __future__ import annotations

import hashlib
import re
import unicodedata

DEFAULT = "Gus Delgado"
NAME_MAX = 30
# The names an older settings.txt may hold that are no longer offered (BC.2): the original's Ghip and the 28 names of D-106's list. They
# are kept only as SHA-256 digests of the casefolded name, so no real person's name is in the program; a stored name that matches one
# reads as the default once and is saved as the default.
RETIRED_DIGESTS = frozenset((
    "01a6350de16d73db69548d61993b43af7d5f56e250084fa20d1998bed16e29b8",
    "0e0aa17d7b7978c8c46cf0adb432c11e194dbf104d1f3b881d46781d26e694e5",
    "1291fd3964d9b423dfeb79d45b65c5b98b428509f5e56cf1af28da79153070d8",
    "1dabe73c5ae46c0f067a2817b7fb45aee3bbd3d465eb30174104a985608319b2",
    "20c6349b759be29ffa40191283dbd44c24dd458d345c15a38ac99f6be0647533",
    "2a2b7da9f8b3a689a5d1d925a1fa1ba34182043bfdd7a508f323032459883c27",
    "2dea7463a2e6ebc8ba3af21934c71ee3cd82ba843b18925821fa6ba0858b2cfc",
    "37475ea97a250d31aaf52f0c2e1ec451738ef5b7cd49c955676dc2a2d8a7c5d4",
    "391ff2d4bd5eb2b3228dccc11196092a067de99de7ced63119d3c27e80dc6c2b",
    "51f8730848e35972c1cfbec9d7d933afaaf4ddb6aa5ae0770c3c6420b4eb7fc9",
    "54efa0351070ae2316c833ffa8e7693d1d1fae3d84ca1e0bf365385b4e182f03",
    "5f5303a90b442316ff633ed74dfa8885abf4680b0a63b1da5ffb0dfa22a0699a",
    "5fe7151b395b9f7161efaf46f3456fc42a26f7e868b7da4014026bf05777af93",
    "801011955989cc7d97b18f54fc95df8a7adad696cf8e5bf50e8cec27487f17a2",
    "84e8db70ff921212f9bf5ed23a0382b88e92d032fce036330bd493f7cf9f12fc",
    "8a30fc3b979d65a06e6d457c84a333e55eedb88c310b5498866b70c216765ecc",
    "90f52850cb6dd664bef0fed753a1b1023c6aa37e780c64172ff4c1c2b015b5d0",
    "98cc31ae09533d2cb29f9037f3e5dfbe6670a8ba1b23ff683eace1d881852e50",
    "a126051ea09368035614b90a37cd16f9c90a3855c1b29dcaf88c42e3dbdf65ab",
    "a6103bd3700c6f943592362e8d9594cb2c79627b67b30b8980e66c1740b6340b",
    "a7b72a4eb71afcb542d3eca09270262f698ffc268c6e81e7358bae70706c942e",
    "a7f5cb5fd215428fa9b62fd6ffb1d3c18b6cd9a53611888ca03a4553682160e1",
    "abc31627df774080b82785bd8ecfab6191c0444cd49b4c260726e1163a0c7dd3",
    "b0ebd6602f817ff31afc1444b6f51127820030b1f36c7671f7797806aae90030",
    "bf47f237aa8afd6d2781027d7f4ade4a13bea4d46881c539b726e7c0921d1404",
    "c2b16c0d41dc35a6eb8a570637ee09a1fa61fc1dbd661650721f13225e7d9c2d",
    "f173d4ad0e5bd8959befc26f9a57d0b175565f04acbfc7ebfafc926fadd3be36",
    "f895c4a9c35507fde5316ff48cfa63127f083920f406f803baa58422d37bc4f6",
    "ff7537936044d8ccf01bb89a9512d06ff5915a86fbab7924923350a85adc7bbb",
))
_UNSAFE = re.compile(r"[^A-Za-z0-9 '.\-]")


def clean(name) -> str:
    """The name as it is stored and spoken: letters, digits, spaces, apostrophes, full stops and hyphens, one space between words, at most
    NAME_MAX characters. "" when nothing usable is left (fewer than two characters)."""
    if not isinstance(name, str):
        return ""
    # S8.3 round 2: an accented letter is folded to its plain letter ("José" is "Jose"), not dropped ("Jos"); the voices that cannot say an
    # accent (SX.11's respellings) then still say the name
    folded = "".join(c for c in unicodedata.normalize("NFKD", name) if not unicodedata.combining(c))
    text = " ".join(_UNSAFE.sub("", folded).split())[:NAME_MAX].strip()
    return text if len(text) >= 2 else ""


def digest(name: str) -> str:
    return hashlib.sha256(" ".join(name.split()).casefold().encode("utf-8")).hexdigest()


def is_retired(name: str) -> bool:
    """True for Ghip and the names of the retired list of real podcasters (D-106), in any case and spacing."""
    return bool(name) and digest(name) in RETIRED_DIGESTS


def name_of_text(name) -> str:
    """The analyst's name for a stored or given text: the cleaned name, or the default when it is empty, unusable or retired."""
    text = clean(name)
    return text if text and not is_retired(text) else DEFAULT


def choices(current: str) -> list[tuple[str, str]]:
    """The items of the list in F9, Rules, Commentator as (kind, name): the default first, the player's own name when it is not the
    default, and last the item that lets the player type one. kind is "default", "own" or "type"."""
    items = [("default", DEFAULT)]
    current = name_of_text(current)
    if current != DEFAULT:
        items.append(("own", current))
    items.append(("type", ""))
    return items


def name_of(game_settings) -> str:
    """The analyst's name for a game: the setting, or the default when it is missing, unusable or retired."""
    return name_of_text(getattr(game_settings, "nx_commentator", DEFAULT))
