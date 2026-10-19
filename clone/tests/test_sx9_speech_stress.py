"""The speech stress cases of S8.3 with the Franchise's long lists (nfl4 only, rule 0.13; PX SX.9). This is inspired by Jim Kitchen.

The engines are the rig's fakes (tests/gamerig.py): NVDA closing in the middle of the 34 players of the roster, the SAPI voice failing for a
whole franchise year with no screen reader running, and NVDA closing at the draft with slow speech. In every case the program goes on,
the lists are said by the engine that is left, and the league stays whole. JAWS closing and SAPI's own failures are tests/test_jaws.py,
tests/test_speech_manager.py and tests/test_sapi_backend.py.
"""
from frrig import COACH_AND_TEAM, DOWN, ENTER, ESC, F9, WANT_FRANCHISE, enter_until, franchise_rig, quit_policy, run_until
from nfl4.extras.franchise import data as D

INTO_FRANCHISE = [F9, DOWN, DOWN, DOWN, DOWN, ENTER]
TWO = [DOWN, DOWN]                                   # past the to do list and the news to the roster
GROUP_SIZES = (1, 6, 6, 6, 5, 4, 2, 2, 1, 1)          # the roster's ten groups (test_fr_menus)


def every_player_keys():
    keys = []
    for size in GROUP_SIZES:
        keys += [ENTER] + [DOWN] * (size - 1) + [ESC, DOWN]
    return keys


def texts(backend):
    return [t for t, _, _ in backend.said]


def test_nvda_closing_in_the_middle_of_the_roster_goes_on_with_sapi_and_every_player_is_said(tmp_path):
    keys = every_player_keys()
    half = len(keys) // 2
    rest = keys[half:]

    def policy(k):
        rig.nvda.available = False                    # NVDA is closed while the player is in the list
        if rest:
            return rest.pop(0)
        return quit_policy(k)
    rig = franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM + INTO_FRANCHISE + TWO + [ENTER] + keys[:half], policy=policy,
                        mode="nvda", nvda_running=True, speech_per_char=0.002)
    run_until(rig)
    league = rig.fstore.league
    names = [player.name for player in league.active_of(league.team)]
    heard = " ".join(texts(rig.nvda) + texts(rig.sapi))
    assert all(name in heard for name in names)
    assert texts(rig.nvda) and texts(rig.sapi)                # the first half by NVDA, the rest by the SAPI voice
    league.check()


def test_a_franchise_year_with_the_sapi_voice_failing_and_no_screen_reader_reaches_the_next_season(tmp_path):
    rig = franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM,
                        policy=enter_until(lambda: rig.fstore is not None and rig.fstore.league is not None
                                           and rig.fstore.league.season == 2 and rig.fstore.league.gtp >= 2))
    rig.sapi.fail_speak = True
    run_until(rig)
    league = rig.fstore.league
    league.check()
    assert league.season == 2 and len(league.history) == 1
    assert texts(rig.sapi) == [] and texts(rig.nvda) == []     # nothing could be said, nothing stopped the year


def test_nvda_closing_at_the_draft_with_slow_speech_the_offseason_goes_on_with_sapi(tmp_path):
    def closed_at_the_draft():
        league = rig.fstore.league if rig.fstore is not None else None
        if league is not None and league.stage == "offseason" and league.stage_no == D.STAGE_DRAFT:
            rig.nvda.available = False
        return league is not None and league.season == 2 and league.gtp >= 2
    rig = franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM, policy=enter_until(closed_at_the_draft), mode="nvda",
                        nvda_running=True, speech_per_char=0.002)
    run_until(rig)
    league = rig.fstore.league
    league.check()
    assert league.season == 2 and texts(rig.nvda) and texts(rig.sapi)
    assert len(league.history) == 1 and any("round" in t for t in texts(rig.sapi))
