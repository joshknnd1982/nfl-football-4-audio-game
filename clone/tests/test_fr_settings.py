"""The settings keys of the Franchise: nx_season_kind, nx_fr_auto, nx_fr_offseason, nx_fr_picks_told (nfl4 only, rule 0.13).
This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 10.5: a missing or bad value is its default (the settings file's own healing), the Rules menu's reset leaves
them alone, and the defaults keep Classic the default of everything.
"""
from nfl4.data import settingsfile
from nfl4.data.settings import Settings
from nfl4.extras.rules_menu import DEFAULTS, SWITCHES


def test_the_defaults_keep_classic_the_default_of_the_kind_of_season():
    game = Settings.defaults().game
    assert (game.nx_season_kind, game.nx_fr_auto, game.nx_fr_offseason, game.nx_fr_picks_told) == ("classic", False, "full", "first")
    assert game.rules == "nfl"                     # SX.9: the Rules setting of a new player (NQ2); the kind of season stays classic


def test_the_four_keys_are_written_and_read_back():
    settings = Settings.defaults()
    settings.game.nx_season_kind, settings.game.nx_fr_auto = "franchise", True
    settings.game.nx_fr_offseason, settings.game.nx_fr_picks_told = "short", "all"
    text = settingsfile.render(settings)
    for line in ("nx_season_kind = franchise", "nx_fr_auto = on", "nx_fr_offseason = short", "nx_fr_picks_told = all"):
        assert line in text
    parsed, problems = settingsfile.parse(text)
    assert not problems and (parsed.game.nx_season_kind, parsed.game.nx_fr_auto, parsed.game.nx_fr_offseason,
                             parsed.game.nx_fr_picks_told) == ("franchise", True, "short", "all")


def test_a_bad_value_is_a_problem_and_the_key_keeps_its_default():
    text = settingsfile.render(Settings.defaults()).replace("nx_season_kind = classic", "nx_season_kind = both") \
        .replace("nx_fr_offseason = full", "nx_fr_offseason = never").replace("nx_fr_auto = off", "nx_fr_auto = maybe") \
        .replace("nx_fr_picks_told = first", "nx_fr_picks_told = some")
    parsed, problems = settingsfile.parse(text)
    assert len(problems) == 4 and parsed.game.nx_season_kind == "classic" and parsed.game.nx_fr_offseason == "full"
    assert parsed.game.nx_fr_auto is False and parsed.game.nx_fr_picks_told == "first"


def test_a_settings_file_of_an_older_version_without_the_keys_is_whole():
    text = "\n".join(line for line in settingsfile.render(Settings.defaults()).splitlines() if not line.startswith("nx_fr_")
                     and not line.startswith("nx_season_kind"))
    parsed, problems = settingsfile.parse(text)
    assert not problems and parsed.game.nx_season_kind == "classic"


def test_the_rules_menus_reset_does_not_touch_the_franchise_keys():
    assert not any(name.startswith("nx_fr_") or name == "nx_season_kind" for name in SWITCHES + tuple(DEFAULTS))


def test_the_header_of_the_file_explains_the_new_keys():
    text = settingsfile.render(Settings.defaults())
    for name in ("nx_season_kind", "nx_fr_auto", "nx_fr_offseason", "nx_fr_picks_told"):
        assert "# " + name in text
