"""The Franchise's draft as stage 4 on the program rig (nfl4 only, rule 0.13): what is told, the player's pick and every key of its question,
the picks told setting, the staff's picks, a draft closed in the middle, the files (NFL_FRANCHISE_DESIGN 3.7, 7.3, 16 SX.8d).
"""
import pytest

from drrig import (SURNAMES, at_stage, draft_league, enter_until, franchise_rig, offseason_rig, picks_of, replay, run_until,
                   saved_league)
from frrig import DOWN, ENTER, ESC, F1, F9, UP, spoken
from nfl4.extras import nx_texts as X
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import draft as DR
from nfl4.extras.franchise.league import LeagueRecord

PAGE_DOWN, PAGE_UP = 34, 33
TEAM = 5


def prompts(text):
    return [t for t in text if " it is your pick, round " in t]


def told(text):
    return [t for t in text if t.startswith(" pick ") and " take " in t]


def ran(tmp_path, keys=(), picks_told="mine", league=None, until=None, **kwargs):
    return offseason_rig(tmp_path, league or draft_league(seed=3, team=TEAM), keys=keys, picks_told=picks_told,
                         until=until or at_stage(5), **kwargs)


def position_word(position):
    return X.text(D.POSITION_TEXT[position])


# ----- the stage -----

def test_the_stage_names_itself_tells_the_players_pick_and_asks_seven_times(tmp_path):
    rig = ran(tmp_path)
    text = spoken(rig)
    final = saved_league(rig)
    place = final.draft["order"].index(TEAM) + 1
    start = text.index(" stage 5 of 7. the draft. ")
    assert text[start + 1] == X.text("NXK-01", n=place)
    assert len(prompts(text)) == 7 and text.count(X.text("NXK-05")) == 7
    assert [round_no for round_no in range(1, 8) if " Kim it is your pick, round %d, pick %d. " % (round_no, place) in
            "".join(prompts(text))] == [1, 2, 3, 4, 5, 6, 7]
    assert final.stage_no == 5 and final.pick_no == 225 and len(final.draft["picks"]) == 224


def test_the_player_takes_the_staffs_first_prospect_with_enter_and_it_is_told_as_his_pick(tmp_path):
    rig = ran(tmp_path)
    text = spoken(rig)
    final = saved_league(rig)
    mine = [final.players[pid] for team, _, pid in final.draft["picks"] if team == TEAM]
    assert len(mine) == 7
    for player in mine:
        assert X.text("NXK-10", player=player.name, position=position_word(player.pos)) in text
    assert not [t for t in text if t.startswith(" the staff took ")]


def test_after_the_last_pick_the_rookies_are_told_by_their_ranges_and_the_stage_waits(tmp_path):
    rig = ran(tmp_path)
    text = spoken(rig)
    final = saved_league(rig)
    end = text.index(X.text("NXK-11"))
    rookies = final.waiting_rookies(TEAM)
    expected = []
    for player in rookies:
        low, high = final.rookie_range(player)
        expected.append(X.text("NXK-06", player=player.name, position=position_word(player.pos), lo=low, hi=high, a=player.age,
                               potential=X.text(D.POTENTIAL_TEXT[player.potential])))
    assert text[end + 1:end + 8] == expected and text[end + 8] == X.text("NXE-03")


def test_the_player_with_the_first_pick_and_the_player_with_the_last_pick_hear_the_right_pick_numbers(tmp_path):
    wins = [8] * 32
    wins[TEAM - 1] = 0
    first = ran(tmp_path / "first", league=draft_league(wins=wins, finish=[0] * 32))
    assert X.text("NXK-01", n=1) in spoken(first) and " Kim it is your pick, round 1, pick 1. " in "".join(prompts(spoken(first)))
    wins[TEAM - 1] = 16
    finish = [0] * 32
    finish[TEAM - 1] = D.FINISH_CHAMPION
    last = ran(tmp_path / "last", league=draft_league(wins=wins, finish=finish))
    assert X.text("NXK-01", n=32) in spoken(last) and " Kim it is your pick, round 7, pick 32. " in "".join(prompts(spoken(last)))


# ----- the picks told (design 7.3) -----

def expected_told(rig, setting, mine=TEAM):
    final = saved_league(rig)
    order = final.draft["order"]
    words = rig.fstore.words
    lines = []
    for overall, (team, _, pid) in enumerate(final.draft["picks"], start=1):
        if team == mine:
            continue
        next_team = order[overall % 32] if overall < 224 else None
        if setting == "all" or (setting == "first" and (overall <= 3 or next_team == mine)):
            player = final.players[pid]
            lines.append(X.text("NXK-03", n=(overall - 1) % 32 + 1, team=words.team_name(team), player=player.name,
                                position=position_word(player.pos)))
    return lines


@pytest.mark.parametrize("setting", ["first", "mine", "all"])
def test_the_picks_told_setting_decides_which_computer_picks_are_spoken(tmp_path, setting):
    rig = ran(tmp_path, picks_told=setting)
    lines = told(spoken(rig))
    assert lines == expected_told(rig, setting)
    if setting == "all":
        assert len(lines) == 217                                                        # every pick but his seven
    elif setting == "mine":
        assert lines == []
    else:
        assert 7 <= len(lines) <= 7 + 3 + 1                                             # the first three and the pick before each of his seven


def test_with_the_first_setting_the_players_pick_at_the_start_of_a_round_is_preceded_by_the_last_pick_of_the_round_before(tmp_path):
    wins = [8] * 32
    wins[TEAM - 1] = 0
    rig = ran(tmp_path, picks_told="first", league=draft_league(wins=wins, finish=[0] * 32))
    text = spoken(rig)
    lines = told(text)
    assert lines == expected_told(rig, "first")
    assert " pick 32: " in "".join(lines)                                              # the pick before his first pick of rounds 2 to 7
    assert sum(1 for line in lines if line.startswith(" pick 32: ")) == 6              # and no pick before the very first (nothing precedes it)


def test_a_round_is_announced_before_the_first_spoken_line_of_it_and_not_before_the_players_own_prompt(tmp_path):
    rig = ran(tmp_path, picks_told="all")
    text = spoken(rig)
    rounds = [t for t in text if t.startswith(" round ") and t.endswith(". ") and "pick" not in t]
    assert rounds == [X.text("NXK-02", n=n) for n in range(1, 8)]
    for n in range(1, 8):
        at = text.index(X.text("NXK-02", n=n))
        assert text[at + 1].startswith(" pick 1: ")                                    # the first pick of each round is a computer pick here
    quiet = spoken(ran(tmp_path / "quiet", picks_told="mine"))
    assert not [t for t in quiet if t.startswith(" round ") and "pick" not in t]       # nothing but his own prompts is spoken


def test_an_announced_round_is_not_repeated_by_the_staffs_pick_of_his_team(tmp_path):
    rig = ran(tmp_path, keys=["8", ENTER], picks_told="mine")
    text = spoken(rig)
    assert len(prompts(text)) == 1
    announcements = [t for t in text if t.startswith(" round ") and "pick" not in t]
    assert announcements == [X.text("NXK-02", n=n) for n in range(2, 8)]               # round 1's prompt named it; the staff's lines name the rest


# ----- the question (design 7.3, 3.7) -----

def test_every_pick_of_the_default_answer_equals_the_computers_rule_applied_to_the_players_team(tmp_path):
    rig = ran(tmp_path)
    assert picks_of(saved_league(rig)) == replay(rig, lambda k: 0)


KEYS_MIXED = [ENTER,                                  # pick 1: the staff's first
              DOWN, ENTER,                            # pick 2: the second
              "3", ENTER,                             # pick 3: the third (a digit jumps to it)
              "6", ENTER, DOWN, DOWN, ENTER,          # pick 4: hear more prospects, the third of the whole list
              "6", ENTER, ESC, "1", ENTER,            # pick 5: hear more, Escape, back to the question, the first
              "7", ENTER,                             # pick 6: let the staff pick
              "8", ENTER]                             # pick 7: the staff makes this and the rest


def test_the_staffs_list_the_long_list_the_staffs_pick_and_every_key_choose_the_prospects_they_name(tmp_path):
    rig = ran(tmp_path, keys=KEYS_MIXED)
    text = spoken(rig)
    final = saved_league(rig)
    assert picks_of(final) == replay(rig, lambda k: [0, 1, 2, 2, 0, 0, 0][k])
    chosen = [X.text("NXK-10", player=final.players[pid].name, position=position_word(final.players[pid].pos))
              for team, _, pid in final.draft["picks"] if team == TEAM]
    staff = [X.text("NXK-12", player=final.players[pid].name, position=position_word(final.players[pid].pos))
             for team, _, pid in final.draft["picks"] if team == TEAM]
    assert [t for t in text if t in chosen] == chosen[:5]                              # the first five were the player's own choice
    assert [t for t in text if t in staff[5:]] == staff[5:]                            # and the last two the staff's
    assert not final.draft["staff_all"] == 0


def test_the_questions_items_are_numbered_and_the_digits_and_up_and_down_speak_them(tmp_path):
    rig = ran(tmp_path, keys=[UP, "6", DOWN, DOWN, "2", ENTER], until=at_stage(4, pick=8))
    text = spoken(rig)
    start = text.index(X.text("NXK-05"))
    heard = text[start + 1:start + 8]
    assert heard[0].startswith(" 1. ") and heard[1] == " 8. staff makes your other picks "         # Up wraps to the last item
    assert heard[2] == " 6. hear more prospects "                                                    # the digit 6 takes item 6
    assert heard[3] == " 7. let the staff pick " and heard[4] == " 8. staff makes your other picks "   # Down, Down: 7 then 8
    assert heard[5].startswith(" 2. ")                                                               # the digit 2: the second of the staff's list


def test_f1_says_the_situation_and_the_current_item_again_and_an_unknown_key_is_echoed_and_the_question_asked_again(tmp_path):
    rig = ran(tmp_path, keys=[DOWN, F1, "x", ENTER], until=at_stage(4, pick=8))
    text = spoken(rig)
    first = next(i for i, t in enumerate(text) if " it is your pick, round 1" in t)
    prompt = text[first]
    block = text[first:first + 12]
    assert block[0] == prompt and block[1] == X.text("NXK-05") and block[2].startswith(" 1. ") and block[3].startswith(" 2. ")
    assert block[4:7] == [prompt, X.text("NXK-05"), block[3]]                      # F1: the situation and the current item, again
    assert block[7] == "x"                                                           # the unknown key is echoed ...
    assert block[8:11] == [prompt, X.text("NXK-05"), block[3]]                       # ... and the question asked again, the item kept
    assert text[first + 11].startswith(" you take ") and block[3][4:].split(",")[0] in text[first + 11]       # Enter took item 2


def test_page_up_turns_back_a_page_and_the_back_item_of_a_later_page_does_too(tmp_path):
    keys = ["6", ENTER, PAGE_DOWN, PAGE_UP, PAGE_DOWN] + [DOWN] * 10 + [ENTER, ESC, "7", ENTER]
    rig = ran(tmp_path, keys=keys, until=at_stage(4, pick=8))
    text = spoken(rig)
    at = text.index(X.text("NXK-07").strip())
    block = text[at:at + 30]
    pages = [t for t in block if t.startswith(" page ")]
    assert pages == [X.text("NXF-42", n=n, m=29) for n in (1, 2, 1, 2, 1)]       # start, Page Down, Page Up, Page Down, the Back item
    assert " Back " in block and " 0. more " in block                              # the Back item has no digit; more is on 0


def test_the_long_list_is_paged_by_nine_with_more_on_zero_and_escape_leaves_it(tmp_path):
    rig = ran(tmp_path, keys=["6", ENTER, PAGE_DOWN, "0", ESC, "7", ENTER], until=at_stage(4, pick=8))
    text = spoken(rig)
    at = text.index(X.text("NXK-07").strip())
    pages = [t for t in text[at:at + 8] if t.startswith(" page ")]
    assert pages == [X.text("NXF-42", n=1, m=29), X.text("NXF-42", n=2, m=29)]
    more = text.index(" 0. more ")
    assert more > at
    back = [t for t in text[more:] if " it is your pick, round 1" in t]
    assert back                                                                         # Escape went back to the question
    assert text[more + text[more:].index(back[0]) + 2] == " 6. hear more prospects "     # on the item that was opened
    assert any(t.startswith(" the staff took ") for t in text[more:])                   # item 7 then made the pick


def test_the_staff_makes_the_other_picks_when_asked_and_asks_nothing_more(tmp_path):
    rig = ran(tmp_path, keys=["8", ENTER])
    text = spoken(rig)
    final = saved_league(rig)
    assert len(prompts(text)) == 1 and len([t for t in text if t.startswith(" the staff took ")]) == 7
    assert final.draft["staff_all"] == 1


def test_a_draft_is_the_same_whether_the_player_takes_the_staffs_first_lets_the_staff_pick_or_lets_it_make_the_rest(tmp_path):
    """I7: one code path for the computer's picks. The same start and the same seed give the same draft, and the setting of the
    picks told changes nothing but the speech."""
    runs = {"enter": ran(tmp_path / "a", picks_told="all"),
            "staff": ran(tmp_path / "b", keys=["7", ENTER] * 7, picks_told="first"),
            "rest": ran(tmp_path / "c", keys=["8", ENTER], picks_told="mine")}
    picks = {name: picks_of(saved_league(rig)) for name, rig in runs.items()}
    assert picks["enter"] == picks["staff"] == picks["rest"]
    assert saved_league(runs["enter"]).draft["class"] == saved_league(runs["rest"]).draft["class"]


def test_the_open_places_of_the_players_team_are_told_and_a_drafted_rookie_closes_one(tmp_path):
    def mutate(league):
        for index in (33, 0, 31):
            player = league.player_at(TEAM, index)
            player.status, player.place, player.left = "retired", -1, league.season
            league.rosters[TEAM - 1][index] = 0
    rig = ran(tmp_path, league=draft_league(mutate=mutate), until=at_stage(4, pick=1))
    text = spoken(rig)
    assert any(t.endswith(" your open places: quarterback 1, running back 1, kicker 1. ") for t in prompts(text))


# ----- a draft closed in the middle (design 3.3 item 4) -----

def test_a_draft_closed_in_the_middle_resumes_at_its_next_pick_with_the_same_class_and_the_same_draft(tmp_path):
    whole = ran(tmp_path / "whole")
    first = ran(tmp_path / "first", until=at_stage(4, pick=40))
    cut = saved_league(first)
    made = len(cut.draft["picks"])
    assert 40 <= made < 224 and cut.pick_no == made + 1 and cut.stage_no == 4
    second = offseason_rig(tmp_path / "second", None, files=first.files, picks_told="mine", until=at_stage(5))
    text = spoken(second)
    assert text[0] == " stage 5 of 7. the draft. " or " stage 5 of 7. the draft. " in text
    final = saved_league(second)
    assert picks_of(final) == picks_of(saved_league(whole)) and final.draft["class"] == saved_league(whole).draft["class"]
    assert len(prompts(text)) == 7 - sum(1 for team, _, _ in cut.draft["picks"] if team == TEAM)         # only the picks still to come


def test_every_pick_is_written_before_it_is_told_and_the_class_before_the_first_pick(tmp_path):
    rig = ran(tmp_path, picks_told="all")
    counts = [picks for stage, pick_no, picks, _, _ in rig.saves if stage == 4 and picks >= 0]
    assert counts == list(range(0, 225))                                              # the class (0 picks), then after every pick
    assert [pick_no for stage, pick_no, picks, _, _ in rig.saves if stage == 4 and picks >= 0] == list(range(1, 226))
    assert [stage for stage, _, picks, _, _ in rig.saves if picks == 224] == [4, 5]       # the last pick, then the stage's end
    # the file is written before the pick is told and after the pick before it was: the number of lines spoken at each save lies between
    texts = [t for t, _, _ in rig.said]
    final = saved_league(rig)
    line_of = {}
    for overall, (team, _, pid) in enumerate(final.draft["picks"], start=1):
        if team != TEAM:
            player = final.players[pid]
            line_of[overall] = next(i for i, t in enumerate(texts) if t.startswith(" pick %d: " % ((overall - 1) % 32 + 1))
                                    and (" take %s, " % player.name) in t)
    at_save = {picks: spoken_count for stage, _, picks, _, spoken_count in rig.saves if stage == 4 and picks >= 1}
    before = 0
    for overall in sorted(line_of):
        assert before < at_save[overall] <= line_of[overall], overall                  # after the line before, before its own line
        before = line_of[overall]


def test_a_draft_whose_staff_flag_is_set_asks_nothing_after_a_restart(tmp_path):
    from test_fr_draft import mid_draft
    league, draft = mid_draft(seed=3, picks=30, team=TEAM)
    draft.let_the_staff_pick_the_rest()
    still_mine = 7 - sum(1 for team, _, _ in league.draft["picks"] if team == TEAM)               # his picks that are still to come
    rig = offseason_rig(tmp_path, league, picks_told="mine", until=at_stage(5))
    text = spoken(rig)
    assert not prompts(text) and len(saved_league(rig).draft["picks"]) == 224
    assert len([t for t in text if t.startswith(" the staff took ")]) == still_mine >= 1


# ----- short offseason, F9 and the settings -----

def test_the_short_offseason_still_asks_for_the_picks_but_ends_the_draft_without_a_key(tmp_path):
    rig = ran(tmp_path, short=True, until=at_stage(5))
    text = spoken(rig)
    end = text.index(X.text("NXK-11"))
    assert len(prompts(text)) == 7 and " stage 5 of 7. the draft. " in text
    assert X.text("NXE-03") not in text[end:end + 9]


def test_the_players_rookies_are_told_by_their_range_in_f9_until_the_cut(tmp_path, monkeypatch):
    from nfl4.extras.franchise import menus
    from nfl4.game import spoken_menu
    probe = ran(tmp_path / "probe", until=at_stage(4, pick=7))
    cut = saved_league(probe)
    rookie = cut.waiting_rookies(TEAM)[0]                                              # the player's first pick, the same in every run
    low, high = cut.rookie_range(rookie)
    lists, menus_seen = [], []
    real_picker, real_menu = menus._lines_picker, spoken_menu.SpokenMenu.__init__

    def picker(speech, keys, title, lines):
        lists.append((title, list(lines)))
        real_picker(speech, keys, title, lines)

    def menu(self, speech, keys, title, items, *args, **kwargs):
        menus_seen.append((title, [item.label() for item in items]))
        real_menu(self, speech, keys, title, items, *args, **kwargs)
    monkeypatch.setattr(menus, "_lines_picker", picker)
    monkeypatch.setattr(spoken_menu.SpokenMenu, "__init__", menu)
    steps = D.ROSTER_ORDER.index(rookie.pos)
    keys = [ENTER, F9, DOWN, DOWN, DOWN, DOWN, ENTER, DOWN, DOWN, ENTER] + [DOWN] * steps + [ENTER, ESC, ESC, ESC, ESC]
    ran(tmp_path / "f9", keys=keys, until=at_stage(4, pick=8))
    expected = X.text("NXK-06", player=rookie.name, position=position_word(rookie.pos), lo=low, hi=high, a=rookie.age,
                      potential=X.text(D.POTENTIAL_TEXT[rookie.potential]))
    group = [lines for title, lines in lists if expected in lines]
    assert group and group[0][-1] == expected                                           # last: after the players the team has
    roster = [labels for title, labels in menus_seen if title == "your roster"][0]
    count = int(roster[steps].split(":")[1])
    assert count == len(group[0])                                                       # the group line counts the rookie too


def test_the_franchise_settings_menu_cycles_the_picks_told_with_left_right_and_enter_and_keeps_it(tmp_path):
    from nfl4.data import settingsfile
    from test_fr_menus import INTO_FRANCHISE, in_a_franchise
    from nfl4.game.keys import KEY_LEFT as LEFT
    from nfl4.game.keys import KEY_RIGHT as RIGHT
    rig = in_a_franchise(tmp_path, INTO_FRANCHISE + [DOWN] * 6 + [ENTER, DOWN, DOWN, ENTER, RIGHT, LEFT, LEFT, RIGHT])
    text = spoken(rig)
    at = text.index(X.text("NXF-22"))
    assert text[at:at + 5] == [X.text("NXF-22"), X.text("NXF-25"), X.text("NXF-26"), X.text("NXF-25"), X.text("NXF-22")]
    assert rig.game.options.settings.game.nx_fr_picks_told == "mine"                  # first, Enter: mine, Right: all, Left: mine, Left: first, Right: mine
    assert "nx_fr_picks_told = mine" in settingsfile.render(rig.game.options.settings)


def test_a_picks_told_setting_changed_in_f9_during_the_draft_applies_from_the_next_pick(tmp_path):
    from nfl4.game.keys import KEY_RIGHT as RIGHT
    keys = [F9, DOWN, DOWN, DOWN, DOWN, ENTER] + [DOWN] * 6 + [ENTER, DOWN, DOWN, RIGHT, RIGHT, ESC, ESC, ESC]
    rig = ran(tmp_path, keys=keys, picks_told="first")
    assert rig.game.options.settings.game.nx_fr_picks_told == "all"
    final = saved_league(rig)
    place = final.draft["order"].index(TEAM) + 1
    first_rule = expected_told(rig, "first")
    everything = expected_told(rig, "all")
    # picks up to and including his first were under "first"; the rest are told by "all"
    sofar = [line for line, pick in zip(everything, [o for o in range(1, 225) if final.draft["picks"][o - 1][0] != TEAM]) if pick <= place]
    kept = [line for line in sofar if line in first_rule]
    after = [line for line, pick in zip(everything, [o for o in range(1, 225) if final.draft["picks"][o - 1][0] != TEAM]) if pick > place]
    assert told(spoken(rig)) == kept + after
