"""Every real NFL play and every Madden NFL playbook concept, as football concepts (nfl4 only, rule 0.13; NX-P1 to NX-P7, NX-R7;
design `spec/NFL_PLAYS_DESIGN.md`, built from SX.10b). This is inspired by Jim Kitchen.

    model_data.py   the published and computed NFL numbers every model is calibrated to (sources on each table)
    catalog.py      the concepts: offense, defense, special teams, tries and clock plays, with their IDs, groups and parameters
    model.py        the outcome models: pure functions over a concept, a defense call, the situation and the game's random source
    play_menus.py   the spoken menus in the original's style: the original's items first, then the lists, favourites, again, find

Nothing here is read by Classic, and in SX.10b nothing here is wired into the engine yet: SX.10c (offense), SX.10d (defense and
special teams) and SX.10e (the computer's calling, the bands, the 10,000 games) connect it through the hooks of design section 7.
Madden NFL is a trademark of Electronic Arts; no EA play name, list, art, rating or text is used, only football concepts.
"""
