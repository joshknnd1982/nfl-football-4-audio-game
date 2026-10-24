### 7.3 The picks

- One code path for every pick (research G: computer picks never depend on how the player watched; invariant I7). `best_for(team, available)` gives each available prospect a value for that team: the middle of his spoken range (low end + 3) + the potential bonus (high +5, average 0, low -4) + the need bonus, its parts ADDED: +8 when the team's group of his position has an open place (its count minus the players left after the retirements minus the rookies already drafted into it; +12 instead of +8 for QB), and for a group of one place (QB, K, P) the place counts as open also when its player's rating is under `FR_DRAFT_WEAK` = 60; +3 more when his middle beats the lowest rating of that group (the incumbents' true ratings and, for the rookies already drafted, the middle of their ranges: a team knows its rookies only by their ranges until the cut); -10 for a K, P or RET when that group has no open place (start values `FR_DRAFT_VALUE`); the highest value wins, ties to the lower prospect number. No draw. The computer's pick is `best_for`'s first; the staff's list for the player is `best_for`'s first five.
- Computer picks are made silently. Spoken (setting `nx_fr_picks_told`, NXF-22, NXF-25, NXF-26; the plain words "picks told" and "draft results", never the EA feature name for it, research E): `first` (default) the first three picks of round 1 and the pick right before each of the player's picks; `mine` only the player's; `all` every pick. A told pick is NXK-03 " pick <n>: the <team> take <player>, <position>. "; each round starts with NXK-02 " round <n>. " when a line of it is spoken.
- The player's pick: NXK-04 " <coach> it is your pick, round <r>, pick <n>. your open places: <list>. " (the list NXK-13 " none " or the positions with counts, NXL-21 " <position> <n> "), then NXK-05 " the staff's list. " and a FranchiseQuestion (3.7): items 1 to 5 the staff's five, each NXK-06 " <player>, <position>, about <lo> to <hi>, age <a>, <potential> potential "; item 6 NXK-07 " hear more prospects " (the available class by value for the team, paged by nine, each an item that takes him); item 7 NXK-08 " let the staff pick " (the first of the list); item 8 NXK-09 " staff makes your other picks " (this and every later pick of this draft are the staff's, with NXK-12 " the staff took <player>, <position>. " for each). Enter on a prospect: NXK-10 " you take <player>, <position>. ". F1: the situation sentence and the current item again.
- League.sav is written after every pick. At the end: NXK-11 " the draft is over. your rookies: " and NXK-06 for each (the range, since the true rating is not known yet).
- A rookie's true rating becomes known (spoken exactly) from the roster cut on.

### 7.4 Rookie names (N6.5)

From the surname pool as `customize\surnames.txt` gives it (the player's own surname file; no other file): `rnd(1708)` again while an ACTIVE player of the league or a prospect of this class has the name (bounded; then the first free name in pool order; then any, a duplicate). So duplicates with active players never happen while free names exist (1,708 names, at most about 1,350 in use at the draft), and a retired player's name may come back (history says " season 3 " with each name, so they stay apart). Decided here (N6.5 left it to SX.8): duplicates are allowed only when the pool is used up.

### 7.5 What a pick does

The rookie joins the team's roster list for his position group (over the group's count for now); the roster cut decides who keeps a place.

### 7.6 The roster cut and the fill (stage 5; research B1's camp report)

- Every team, in team order, one code path `cut(team)`: in each group, the players are ranked by keep value = rating + the youth bonus (age 24 or less: high potential +4, average +2) (start value `FR_KEEP_YOUTH`), ties to the younger, then to the lower player ID; the group keeps its count, the rest are released (status released). No draw.
- The player's team: NXE-50 " the roster cut. the staff would release: " then NXE-51 " <player>, <position>, age <a>, rating <r>. " for each, then a FranchiseQuestion (3.7): NXE-52 " release them " (first) and NXE-53 " choose yourself ". Choose yourself: for each group with too many players, NXE-54 " <position>: players <n>, places <m>. choose who is released. " and a FranchiseQuestion of the group's players (NXL-31, ranked as above, the staff's choices first); Enter releases the current one (NXE-55 " <player> is released. ") until the group fits. With the to-do setting "the staff handles it" the staff's cuts are taken with one sentence (NXE-56 " players released by the staff: <n>. ").
- The fill (invariant I3): every place still empty (a group with fewer players than places) gets an undrafted rookie: name (7.4), rating `45 + below(11)` (45 to 55) in a group of three places or more, `50 + below(11)` (50 to 60) in a group of one or two places (QB, K, P, S, RET), where one weak player is the whole group and would break I5 (start values `FR_FILL_RATING`, `FR_FILL_RATING_SMALL`), potential `below(100)` as 7.1, age 22. Spoken for the player's team: NXE-57 " empty places filled with undrafted rookies: <n>. " and NXL-31 for each.
- Then each team's players are placed in the group's places by rating, the best in place 1 (the order does not change play: the engine draws a place at random; it makes the roster speech start with the best).
- Invariants after the cut and fill (checked every offseason in the tests): every place filled, no group over its count, every rating 40 to 99, every age 21 to 40, every active player in exactly one place.

## 8. The to-do list and the news (F5)

### 8.1 The to-do list (research B10, B11; design 11.1)

- Before each game of the regular season (section 3.4), 0 to 3 items, each a FranchiseQuestion (3.7) with the staff's recommendation as answer 1, then the other answers, then NXD-A01 " later ". The play-off weeks have no items. Every item has its deadline: the kick-off of this week's game. An item answered " later " stays on the list; the F9 Franchise menu's item NXF-11 " to do list " asks the waiting items again; choosing " 1. play game " in the main menu with items waiting says NXD-06 " items still on your to do list: <n>. " once and asks them before the game starts (H15 `before_game`, section 13).
- Setting NXF-20 " the staff handles the to do list " (`nx_fr_auto`, off by default): on, every item takes the staff's recommendation at once and NXD-03 " the staff took care of <n> items. " (NXD-04 for one) is the only sentence; the roster cut of 7.6 too.
- When the setting is OFF, nothing is ever decided for the player (research G: delegation must not decide when the setting says no): an item still open when its game starts is closed with its "do nothing" answer and NXD-30 " the items you left for later were not done. ".
- The items of the core (the list is data, `data.TODO_KINDS`, so the later updates add theirs: contracts, injuries, coordinators, section 17):
  - T1 extra work (in weeks 2, 6, 10 and 14 of the regular season only, `FR_EXTRA_WORK_WEEKS`, start value; when the team has at least two players aged 24 or less with high or average potential and fewer than 3 development points): NXD-10 " extra work this week for one young player. ", answers: 1 the staff's first candidate, 2 its second, each NXD-A02 " <player>, <position>, rating <r>, <potential> potential ", NXD-A03 " nobody this week " (the "do nothing" answer), " later ". The candidates: the two with the highest (potential level, then lowest age, then highest rating), no draw. Chosen: NXD-11 " <player> gets extra work this week. " and one development point (section 6.2). Every computer team gives its first candidate the point in the same weeks, in the same code path, so the player's advantage is only the choice, and a player who answers " nobody this week " or leaves the item undone falls a point behind every computer team that week (said in the F6 help, NXH-37). Only regular-season weeks count, so the league's development never depends on how far the player's team goes in the play-offs.
  - T2 the game plan (regular weeks only, when the player's offense or defense playbook setting is not Classic): NXD-20 " the game plan against the <team>. they play <their_offense> on offense and <their_defense> on defense. the staff recommends <our_offense> and <our_defense>. " (the styles' names; the offense first), answers NXD-21 " use the staff's game plan ", NXD-22 " keep your playbooks " (the "do nothing" answer), " later ". The recommendation is data, `tuning.FR_GAME_PLAN`: for each opponent defense style (and Classic) the player's offense style, and for each opponent offense style the defense style, worked out ONCE by SX.8e with the expected-yards yardstick of `tests\playbook_ev.py` over the tilts of the styles and frozen as data with the script and its report (no draw, no computation in play). Used: the playbooks of this one game are the plan's (the settings do not change); NXD-23 " the game plan is set for this game. ".
- Spoken frame: NXD-01 " <coach> your to do list has <n> items. " (NXD-02 for one), then each item with NXD-05 " item <n>. " before its question.

### 8.2 Development points

A point is +1 on the player's change at the next progression (section 6.2), at most 3 per player per season. They are the core's only lasting effect of the weekly list.

### 8.3 The news (research B11)

- After weeks 1 to 15 of the regular season (when the week's results are recorded, H14; not after week 16, whose next words are the original's division winners and wild cards and whose next menu is a play-off week or the offseason), the news of the week is made from the results, the strengths and the streaks, by rules without draws, at most `FR_NEWS_MAX` = 4 lines, in this order: the player's own team's streak of 3 or more (wins NWY, losses NWZ), the coach's milestone (every 10th win as head coach, NWM), the biggest win of the week (the largest margin; ties to the first game in the week's order; NWB), an upset (the winner's strength at least `FR_UPSET_GAP` = 4 under the loser's; the largest gap; NWU), the league's longest streak of 4 or more of another team (wins NWS, losses NWL), the closest game when it is not already told (NWC). A line is one line of its pool in `customize\news.txt` (section 15), drawn as the remark pools are drawn (`rnd(size)`, again while one of the last three spoken of that pool, the history in league.sav), filled with its placeholders.
- Spoken before the next week's menu (section 3.4); kept in league.sav as text for the whole season and the offseason (the F9 news item says the last week's lines first, then " earlier " pages week by week).
- The offseason's news: the champion (NWT, stage 1), the stars who retired (NWR, stage 2), the first pick of the draft (NWD, stage 4), the player's big improvers (NWP, stage 3); they are told in their stages and kept as the offseason's news.
- F8 (comments) does not silence the news: it is information the player can read again, not commentary. A kind whose lines are all switched off is never told (that is how a player switches a kind of news off).

## 9. History and records (F4, N6.9)

### 9.1 What is kept

- Results of the current season, for each game: the week or round, the two teams, the two scores (from H14 `game_played`, section 13). Kept until the season's history is written, then dropped.
- Per season (written at stage 1): the season number, the champion and the runner-up, the 64 wins and losses, each play-off team's last round, the player's team's record and finish, the best and the worst record (ties: the original's team order), the player's coach's name, and the season's records of section 9.2.
- The coach's career (computed from the seasons): seasons, wins and losses (regular season and play-offs counted apart), play-off seasons, Super Bowls won.
- League records: most wins in a season (team, season); most points in a game (team, opponent, score, season); the biggest win (margin, the game, season); the longest winning streak (team, length, season).
- Retired stars: name, position, the team he last played for, seasons played, peak, the season he retired (from the kept players, section 4.3).

### 9.2 The history menu (F9 Franchise, item NXF-14)

A SpokenMenu with five items (AS BUILT, SX.8o: seven, NXG-06 " awards by season " and NXG-07 " hall of fame " after the five, entry 1.15), each opening a ListPicker (3.7), newest first: NXG-01 " champions by season " (NXG-10 " season <n>: the <champion> over the <runner_up>. "); NXG-02 " your record " (NXG-11 " seasons: <n>. wins: <w>. losses: <l>. play off seasons: <p>. Super Bowls won: <s>. ", one line); NXG-03 " season by season " (NXG-12 " season <n>: you were <w> and <l>, <finish>. champion: the <champion>. the best record: the <best>. the worst: the <worst>. "); NXG-04 " league records " (NXG-13 to NXG-16); NXG-05 " retired stars " (NXG-17). An empty list says NXG-18 " nothing yet. ".

### 9.3 history.txt

Plain UTF-8 text in the franchise folder for reading in Notepad or with a screen reader, written whole (temporary file and rename) when a franchise starts and at every stage 1; never read back by the game (so a damaged or deleted history.txt is only written again). Layout, one fact per line, a blank line between parts:
```
Franchise history: coach <coach>, the <team>.
Written by NFL Football 4 after season <n>.

Your record
<n> seasons, <w> wins and <l> losses. Play-offs <p> times. Super Bowls won: <s>.

Season <n>
Champion: <team>. Runner-up: <team>.
Your team: <w> and <l>, <finish>.
Best record: <team>, <w> and <l>. Worst record: <team>, <w> and <l>.

League records
Most wins in a season: <team>, <w>, season <n>.
...

Retired stars
<name>, <position>, <team>, <n> seasons, best rating <r>, retired after season <s>.
```
The words are the spoken texts of section 9.2 without the speech spellings that only help the voice.

## 10. The files, the extras record and the settings

### 10.1 franchise\league.sav

- Content: UTF-8 JSON, one object, keys in a fixed order with `"format": 1` and `"game": "NFL Football 4 franchise"` first, then the league record of section 4.1. It is a save, not a file the player edits (CUSTOMIZABLE_CONTENT 10's "no JSON" rule is for the player's lists).
- Written whole, at these moments: every write the season engine makes through its store (records, gtp, pairings, byes), the coach and team and the schedule (the setup store), the end of the to-do list, every news of a week, the end of every offseason stage and every draft pick, every franchise setting change. A write: the new text to `league.sav.tmp`, flushed; the present `league.sav` copied to `league.previous.sav`; the temporary file renamed to `league.sav`. So at any moment one of the two files is whole (invariant I10 tests a crash at every step).
- Read once at the start (and when the franchise comes into use), checked WHOLE before use, with the checks that fit the stage the file says it is in:
  - always: the format, the game marker, every rating 40 to 99, every age 21 to 40, every potential, every ID unique, every placed ID an active player of that team and no active player in two places, the history's values, the to-do list and the news;
  - in the season (stage `season`), at stage 1 and from stage 6 on: 32 teams with every one of the 34 places filled and no group over its count, and the season state (gtp 1 to 20, or 0 only at stage 1, the schedule of 16 weeks of real teams, the records 0 to 20 with wins and losses adding up to the weeks played, the pairings and byes of the week);
  - at stages 2 to 5 and during the draft: places may be empty, and a group may hold its count plus the rookies drafted into it (never more than its count plus 7); the class (260 prospects, each with a position, a range of 7 points around his true rating, an age 21 to 23) and the order (32 teams, each once) are checked only at stage 4.
  Anything out of range for its stage is damage (never clamped silently).
- Healing (playbook 7.10; C10; the saved-game rule: a save is never silently overwritten):
  - league.sav damaged and league.previous.sav whole: the damaged file is copied to `league.sav.damaged<n>` (three kept), the previous one is used and written as league.sav, and NXF-30 " the franchise file was damaged. the copy from before the last save is used, and a copy of the damaged file was kept. " is said with the start-up notices. The player loses at most the last step.
  - league.sav missing and league.previous.sav whole: the copy is used and written as league.sav, NXF-36 " the franchise file was missing. the copy from before the last save is used. ".
  - both damaged, or one damaged and the other missing, while `nx_season_kind` is franchise: the damaged ones copied aside, `nx_season_kind` becomes classic, NXF-31 " your franchise could not be read and was set aside. a classic season begins. ".
  - both missing while `nx_season_kind` is franchise: `nx_season_kind` becomes classic, NXF-37 " your franchise could not be found. a classic season begins. ".
  - The franchise is never made again silently.
  - a file over `FR_SAVE_MAX_BYTES` = 8,000,000 bytes is damaged without being read (a league of 20 seasons is under 1,000,000);
  - a `league.sav.tmp` found at the start is the rest of a write that did not finish: it is deleted unread (the rename is the moment a write counts).
  - a format higher than this program knows: left alone (not damage), `nx_season_kind` becomes classic for this run, NXF-34 " this franchise was saved by a newer version of the game and cannot be played here. a classic season begins. ".
  - held by another program: the classic season this run, NXF-35 " the franchise file is in use by another program. a classic season is played this time. "; nothing is written.
  - the folder cannot be written: the franchise plays on from memory with NXF-32 " the franchise could not be saved, so this season's changes will not be kept. " once.
- The classic store is made at every start as today and gives its own notices (a damaged classic season file, footplay.txt) even while the franchise is in use: they are about the classic season, they are true, and they are said as today (review note 9).
- AS BUILT (SX.8m): FORMAT 8 adds `comp` (the compensatory picks awarded for a coming draft), `future_picks` (the first-round picks owed for the draft
  after the coming one), `tags` (the non-exclusive tag and the history of the positions' highest salaries), the market's `moves` and a draft's `comp` and
  `undrafted`; a file of format 7 or older loads with none of them (a migration with no draw, tested at every stage that may hold a market or a draft).
- AS BUILT (SX.8o): FORMAT 10 adds `honors` (the awards of every season and the hall of fame) and `usage` (the season's games each player played his own place and the backs' carries); a file of format 9 or older loads with no award, nobody in the hall and nothing counted this season (a migration with no draw, tested at a week, at stage 1 and in a draft).
- AS BUILT (SX.8n): FORMAT 9 adds `people` (the players' morale, the camp's holdouts with the player's own still to ask at stage 3, the season's trade demands, the player's game goal and its verdict); a file of format 8 or older loads with nobody's morale and nobody holding out (a migration with no draw, tested at a week, at stage 3 and in a draft).
- A later format (2 for the contracts of SX.8g) reads a format-1 file by a migration that fills the new values with their defaults (a test per migration). AS BUILT (SX.8g): `contracts.migrate`, no draw; a rookie of the last four seasons has the scale of his pick, the others the market price; see entry 1.7. AS BUILT (SX.8h): FORMAT 3 adds `resign`, the stage of the expiring contracts in progress (None outside stage 7); a format-2 file has none and loads as it is (a test), the next save is format 3; a format-2 file saved after stage 2 holds the contracts the SX.8g stand-in had signed, so the new stage finds nobody to ask.

### 10.2 franchise\football.sav

A franchise game saved with Save Game is written to the franchise folder by the franchise store, in the classic layout with the extras section (design 12.3). The extras record gets one more value, `franchise` = {"league": the league ID, "season": n, "week": gtp} (absent in every other game; a record without it loads as before). Loading in the franchise: the values must match the league's ID, season and week, else the file is set aside as in G-F5 with NXF-33 " the saved game belongs to another week of your franchise and was set aside. ". The rosters of a loaded franchise game come from the league again (the same names and ratings: nothing changes inside a week), so a loaded game keeps the opponent's names (the original's Q39 does not apply in a franchise).

### 10.3 history.txt

Section 9.3.

### 10.4 customize\news.txt

The news line templates (CUSTOMIZABLE_CONTENT 13 L16), section 15.

### 10.5 settings.txt (C1)

New keys with their defaults: `nx_season_kind = classic` (classic or franchise, section 3.1); `nx_fr_auto = off` (the staff handles the to-do list and the roster cut); `nx_fr_offseason = full` (full or short, section 3.3); `nx_fr_picks_told = first` (first, mine or all, section 7.3). A missing or bad value is its default (the settings file's own healing). The Rules menu's "Reset the rules to the defaults" does not change them (they are the franchise's, in its own menu).

## 11. The F9 items (N6.10, design 12.2)

- F9 gets the item NXF-10 " Franchise " after " Rules " and before " About ", shown only while the Rules are the N. F. L. rules.
- While the franchise is in use, a SpokenMenu: 1 NXF-11 " to do list " (the waiting items asked as in 8.1, or NXD-07 " nothing is waiting. "), 2 NXF-12 " news " (a ListPicker of the season's lines, the last week first), 3 NXF-13 " your roster " (a SpokenMenu of the ten groups, NXL-30 " <group>: <n> " (" quarterback: 1 ", " running backs: 6 "); Enter opens a ListPicker of the group's players, NXL-31 " <player>, <position>, rating <r>, age <a>, <potential> potential ", and a rookie of this offseason before the cut as NXK-06 with his range), 4 NXF-14 " league history " (section 9.2), 5 NXF-15 " team ratings " (NXL-41 " your team is number <k> of 32. ", then a ListPicker of the 32 teams by rank, NXL-40 " <k>. the <team>, <r>. "), 6 NXF-16 " franchise settings " (a SpokenMenu with Left and Right and Enter changing an item and speaking the new value, saved at once: NXF-20 " staff handles the to do list " followed by NXM-20 " on " or NXM-21 " off "; NXF-21 " offseason: every stage " or NXF-24 " offseason: short "; NXF-22 " draft picks told: first and yours ", NXF-25 " draft picks told: only yours " or NXF-26 " draft picks told: every pick "), 7 NXF-17 " play classic seasons " (as built since SX.8g the items are: to do list, news, your roster, league history, team ratings, 6 NXF-28 " salary cap ", franchise settings, play classic seasons; the cap item lists the cap, the player's payroll, dead money and space, the rank of his space and the 32 teams by space) (then one confirming Enter, as F9 Customize's "reset all" asks: NXF-23 " your franchise will wait. press enter to play classic seasons now, or escape to stay. ", section 3.5).
- While a classic season is in use: when a franchise exists, 1 NXF-18 " back to your franchise " (said with NXF-05's team when chosen) and 2 NXF-14 " league history " (of the waiting franchise); when none exists, 1 NXF-19 " start a franchise now " (then one confirming Enter: NXF-27 " your classic season will wait. press enter to start a franchise now, or escape to stay. ", section 3.5).
- Inside a game the items say only what is true then: the to-do list is closed (its deadline was the kick-off), the roster, news, history and ratings work.
- The F9 Rules item 1 says NXM-26 " the franchise uses the N. F. L. rules. " (a row since SX.1) after its value while the franchise is in use (design 11.2); a change to Classic speaks NXF-04 (section 3.1).

## 12. Every new random draw (C4, design 15)

All draws use the one `GameRandom` and its bounded redraw (G-D1). In Classic none of them happens; with the N. F. L. rules and a classic season none of them happens either. In the order they come:
1. A new franchise (section 4.5), once: for the player's team first, then for each other team in order T01 to T32: the level `below(9)`; then for each place in roster order: the name `rnd(1708)` (again while in use; none for the player's team's names from footplay.txt), the rating `below(13)` twice, the potential `below(100)`, the age `below(5)`, `below(5)`, `below(4)` (and `below(5)` for K and P). Then the original's `makes` draws for the player's schedule.
2. A regular week (pog, H14): the original's draws in their order and number of tries; the shift changes the values compared in the redraw of team B's index, so the number of redraws may differ from Classic when strengths differ, never when they are 70.
3. A play-off game without the player: `chance_first(p)` in place of `rnd(2)`, then the original's score draws.
4. The news of a week (after pog): for each line chosen by the rules of 8.3, in their order: its pool line `rnd(size)` (again while one of the last three of that pool); a line with a `[one of:]` choice then draws it as the remarks do (CUSTOMIZABLE_CONTENT 14); news lines have no `[name]` (section 15).
5. The to-do list: no draw (the candidates and the game plan are rules and data).
6. The offseason, in stage order: stage 1 the NWT line; stage 2 for each active player aged 30 to 39 in league order `below(1000)`, then the NWR lines; stage 3 for each active player in league order `below(5)`, then the NWP lines; stage 4 the class: for each prospect `below(35)`, the name `rnd(1708)` (again while in use), `below(15)` twice, `below(100)`, `below(3)`, `below(7)`; the picks draw nothing; the NWD line; stage 5 the fill: for each empty place in team order and roster order: the name, `below(11)`, `below(100)`, then (SX.8g) the one `rnd(size)` of the NWK line (the team with the most cap space; no other contract rule draws); stage 6 the original's `makes` draws.
Each build session writes its draws again in its tests with the strict scripted source, and SX.8f checks that a whole 20-season run repeats exactly from its seed.

## 13. Hooks and seams in the classic code (each a no-op or an identity in Classic; why each is needed)

The franchise lives in the package `clone\src\nfl4\extras\franchise\` (`data.py`, `league.py`, `ratings.py`, `aging.py`, `draft.py`, `todo.py`, `news.py`, `history.py`, `store.py`, `mode.py`, `question.py`, `menus.py`). It reaches the classic code only through these seams; SX.8a (H15 and H14's `game_played`) and SX.8b (H14's `computer_index` and `playoff_first_wins`, the H7 extension with `opponent_names`, the GameRandom method) build them, each tested to leave Classic unchanged (the golden transcript, the trace of draw sizes and every existing season, program and app test).

- H14 (new) Season hooks, `Game.season_hooks` (Classic: `CLASSIC_SEASON_HOOKS`), read by `SeasonEngine` and handed to `playoffs.computer_game`:
  - `computer_index(team, index) -> index` in `_regular_week` after each team's score index is drawn (Classic: the index unchanged), with the redraw's test and scan on the returned values;
  - `playoff_first_wins(rnd, visitor, home) -> bool` in place of `rnd(2) == 1` (Classic: exactly `rnd(2) == 1`);
  - `game_played(stage, week, winner, loser, winner_score, loser_score)` once after every result the engine speaks or decides: the player's game of a regular week and the 15 computer games (`_regular_week`), the play-off games with and without the player (`_round_with_the_player`, `_computer_round`, which also serves the bye week and finplay17's rounds), finplay17's Super Bowl (`_fin_super_bowl`), the conceded Super Bowl (`_conceded_super_bowl`, a path of its own), and the player's Super Bowl game (`super_bowl_presentation`, called ONCE before its loop, whose F1 and F2 repeat the presentation and must not record the game again) (Classic: nothing).
  Why: the franchise must shape the computer's results by strength (N6.3) and record every result for history, news and the draft order (N6.2, N6.5, N6.9); the engine draws and speaks them inside one method, so a wrapper cannot reach them without copying the engine.
- H15 (new) The season frame, `Program.mode` (Classic: `ClassicSeason`, the code of today moved, not changed): `choose_at_start()` (which kind is in use and its stores, before `has_saved_game`), `season_setup()`, `new_season()` (the question of 3.2 is the franchise's; Classic with the N. F. L. rules asks it too, Classic with Rules = Classic never), `before_menu()` (called inside `main_menu` after today's game sentence and before " <coach> select ", on the menu's first pass of the loop only and never for a saved game, section 3.4: Classic nothing), `before_game()` (when choice 1 is taken, before `play_game`: the to-do deadline of 8.1, which may speak; Classic nothing), `game_arguments()` (the rules, own and opponent names, quarterback names and the sinks for `play_game`, values only: Classic the store's footplay.txt and the save sinks as today), `after_week()` (after pog and the standings: Classic nothing), `season_over()` (Classic: delete the season files, " the season is over ", the reset and the new season, as today; the franchise: the offseason of 3.3), the store's `delete_season_files` at `exit_program` (Classic: as today; the franchise store's does nothing, a franchise's gtp is 0 only inside its offseason, which is written stage by stage), `switch_if_needed()` at the top of the week loop (Classic with Rules = Classic: never switches), and `switch_pending()`, which the main menu asks after each key it receives (a hot-key menu may have asked for a switch): true ends the menu's wait and goes back to the week loop (Classic: always false, so the menu is the original's). Why: the offseason must sit between two seasons, the news and the to-do list between the week's announcement and the menu, and the franchise has its own files; these are the original's program flow, which no existing hook reaches (H1 to H13 are inside a game).
- H7 extended (SX.8b): `adopt_roster` keeps the `ratings` and the `quarterback` of the Roster it adopts (Classic's rosters have none, and only getqbs reads `own_names.quarterback`: no change); `new_game_setup`, `Game.new_game_setup`, `Game.play_game` and `PlayEngine` (its constructor and `start`, `game\pag.py`) take `opponent_names` (None: the original's 33 draws for side 2, as today). The franchise also uses the existing `quarterback_names` seam of `play_game`, so Getqbs is not asked. Why: a franchise opponent is a team of the league with its own players and ratings; today side 2 is always drawn.
- GameRandom gets `chance_first(per_mille)`: one number of the source, traced as a draw of size 2, true when the number x 1000 is under per_mille; at 500 it equals `rnd(2) == 1` for every number (test N3). Never called in Classic. Why: the play-off coin must lean by strength while a league of 70s keeps the original's draws, trace and results.
- No hook in the play itself (pag's snap, resolve and apply): the ratings use H8 (`rules.modifiers`) and the state the engine already has (the carrier and the defenders are drawn before the rows are read). `pag.py`'s start changes only to pass `opponent_names` on (H7 above).
- F9: the Franchise item in `game\functions.py` is F9's first item that is shown only sometimes (only with the N. F. L. rules): the item list is built each time F9 opens, so SX.8a changes how `functions.py` builds it and tests that with Rules = Classic the list is exactly today's (the Rules item itself is always shown). The Rules item's label in `extras\rules_menu.py` gets NXM-26.
- Not a hook: the `FranchiseQuestion` class (3.7) uses `getkey`, the speakers and `saykey` as the original's prompts do and changes none of them.

## 14. The new texts (rows for strings_nx.tsv; the build sessions add them and generate STRINGS_NX.md and nx_texts.py, D-017)

Columns as the table has them: id, feature (franchise), kind, speaker, text (with its spaces), note. The rows follow the rules of `work\make_strings_nx.py`: the kinds it knows (sentence, prompt, answer, menu, remark, piece, help; a notice is a sentence), a menu item of at most six words (a line built from data, such as a player or a team in a list, is a sentence), at most 200 characters, a piece without outer spaces, IDs `NX<letter>-<nn>` or `NX<letter>-<letter><nn>`, remark IDs of a known pool. Every placeholder of a row is filled by its own value, so no placeholder appears twice in one row. SX.8a extends the checker: the new placeholders below go into its PLACEHOLDERS, the news pools into REMARK_POOLS (feature franchise) as SX.8e adds them, and it also checks the IDs this file names (as it does for NFL_EXTRAS_DESIGN.md). Each build session adds the rows of its sections. Rows already in the table: NXF-01, NXF-A01, NXF-A02 (SX.1); NXM-20, NXM-21 (on, off), NXM-23 (" the new rules apply from the next game. "), NXM-26 (" the franchise uses the N. F. L. rules. "), NXL-type words that exist are reused: NXB-10 "Back".

New placeholders: <other>, <player>, <position>, <group>, <potential>, <their_offense>, <their_defense>, <our_offense>, <our_defense>, <k>, <r>, <d>, <a>, <w>, <l>, <p>, <s>, <lo>, <hi>, <score>, <finish>, <list>, <stage>, <round>, <pick>, <champion>, <runner_up>, <best>, <worst>, <best_w>, <best_l>, <worst_w>, <worst_l>. (<team>, <coach>, <n>, <m> exist.) A <score> is spoken " 24 to 17 ".

The mode, the question and the menu (NXF)
- NXF-A03 answer say2 " your franchise with the <team> " (the question, when a franchise exists)
- NXF-A04 answer say2 " a new franchise "
- NXF-02 prompt say2 " your franchise with the <team> will be kept as a copy. do you wish to start a new franchise? " (answer starting at " no ")
- NXF-04 sentence say5 " your franchise waits until the rules are the N. F. L. rules again. "
- NXF-05 sentence say2 " back to your franchise with the <team>. "
- NXF-06 sentence say2 " your franchise waits. the classic season goes on. "
- NXF-07 sentence say2 " your new league is ready. 32 teams and their players. "
- NXF-08 sentence say2 " this is season <n> of your franchise. "
- NXF-09 sentence say2 " your team's rating is <r>, number <k> of 32. "
- NXF-10 menu say5 "Franchise" (F9 item)
- NXF-11 menu say5 "to do list"; NXF-12 menu "news"; NXF-13 menu "your roster"; NXF-14 menu "league history"; NXF-15 menu "team ratings"; NXF-16 menu "franchise settings"; NXF-17 menu "play classic seasons"; NXF-18 menu "back to your franchise"; NXF-19 menu "start a franchise now"
- NXF-20 menu say5 "staff handles the to do list" (followed by NXM-20 or NXM-21)
- NXF-21 menu say5 "offseason: every stage"; NXF-24 menu "offseason: short"
- NXF-22 menu say5 "draft picks told: first and yours"; NXF-25 menu "draft picks told: only yours"; NXF-26 menu "draft picks told: every pick"
- NXF-23 sentence say5 " your franchise will wait. press enter to play classic seasons now, or escape to stay. "
- NXF-27 sentence say5 " your classic season will wait. press enter to start a franchise now, or escape to stay. "
- NXF-30 sentence say " the franchise file was damaged. the copy from before the last save is used, and a copy of the damaged file was kept. " (start-up notice)
- NXF-31 sentence say " your franchise could not be read and was set aside. a classic season begins. "
- NXF-32 sentence say " the franchise could not be saved, so this season's changes will not be kept. "
- NXF-33 sentence say " the saved game belongs to another week of your franchise and was set aside. "
- NXF-34 sentence say " this franchise was saved by a newer version of the game and cannot be played here. a classic season begins. "
- NXF-35 sentence say " the franchise file is in use by another program. a classic season is played this time. "
- NXF-36 sentence say " the franchise file was missing. the copy from before the last save is used. "
- NXF-37 sentence say " your franchise could not be found. a classic season begins. "
- NXF-40 menu say2 "more" (paging; the back item is the existing NXB-10 "Back")
- NXF-42 sentence say2 " page <n> of <m>. "

The to-do list (NXD)
- NXD-01 sentence say2 " <coach> your to do list has <n> items. "; NXD-02 sentence say2 " <coach> your to do list has 1 item. "
- NXD-03 sentence say2 " the staff took care of <n> items. "; NXD-04 sentence say2 " the staff took care of 1 item. "
- NXD-05 sentence say2 " item <n>. "
- NXD-06 sentence say2 " items still on your to do list: <n>. "
- NXD-07 sentence say5 " nothing is waiting. "
- NXD-10 prompt say2 " extra work this week for one young player. "
- NXD-11 sentence say2 " <player> gets extra work this week. "
- NXD-20 prompt say2 " the game plan against the <team>. they play <their_offense> on offense and <their_defense> on defense. the staff recommends <our_offense> and <our_defense>. "
- NXD-21 answer say2 "use the staff's game plan"; NXD-22 answer say2 "keep your playbooks"
- NXD-23 sentence say2 " the game plan is set for this game. "
- NXD-30 sentence say2 " the items you left for later were not done. "
- NXD-A01 answer say2 "later"; NXD-A02 answer say2 "<player>, <position>, rating <r>, <potential> potential"; NXD-A03 answer say2 "nobody this week"

The news frame (NXN)
- NXN-01 sentence say2 " this week's news. "; NXN-02 sentence say5 " no news this week. " (F9 news only); NXN-03 sentence say2 " the news of the offseason. "; NXN-04 menu say5 "earlier"

The offseason (NXE)
- NXE-01 sentence say2 " the season is over. the offseason begins. "
- NXE-02 sentence say2 " stage <n> of <m>. <stage>. "
- NXE-03 sentence say2 " press enter to go on. F1 says it again. "
- NXE-11 piece piece "the season in review"; NXE-12 "retirements"; NXE-13 "player development"; NXE-14 "the draft"; NXE-15 "the roster cut"; NXE-16 "the new season"
- NXE-20 sentence say2 " the <champion> won the Super Bowl of season <n>. "
- NXE-21 sentence say2 " your team finished <w> and <l>, <finish>. "
- NXE-22 piece piece "and missed the play offs"; NXE-23 "and lost in the wild card round"; NXE-24 "and lost in the division round"; NXE-25 "and lost in the conference championship"; NXE-26 "and lost the Super Bowl"; NXE-27 "and won the Super Bowl"
- NXE-28 sentence say2 " the best record: the <best>, <best_w> and <best_l>. the worst: the <worst>, <worst_w> and <worst_l>. "
- NXE-29 sentence say2 " as a head coach: seasons <n>, wins <w>, losses <l>. "
- NXE-30 sentence say2 " from your team: "
- NXE-31 sentence say2 " <player>, <position>, age <a>, rating <r>, retires. seasons played: <n>. "
- NXE-32 sentence say2 " nobody from your team retires. "
- NXE-33 sentence say2 " players retiring in the whole league: <n>. "
- NXE-35 sentence say2 " <player> of the <team>, <position>, retires. seasons played: <n>. "
- NXE-40 sentence say2 " your players: improved <n>, declined <m>, the same <k>. "
- NXE-41 sentence say2 " most improved: <player>, <position>, up <d> to <r>. "
- NXE-42 sentence say2 " the biggest drop: <player>, <position>, down <d> to <r>. "
- NXE-43 sentence say2 " your whole roster is in the franchise menu on F9. "
- NXE-50 sentence say2 " the roster cut. the staff would release: "
- NXE-51 sentence say2 " <player>, <position>, age <a>, rating <r>. "
- NXE-52 menu say2 "release them"; NXE-53 menu say2 "choose yourself"
- NXE-54 prompt say2 " <position>: players <n>, places <m>. choose who is released. "
- NXE-55 sentence say2 " <player> is released. "
- NXE-56 sentence say2 " players released by the staff: <n>. "
- NXE-57 sentence say2 " empty places filled with undrafted rookies: <n>. "
- NXE-60 sentence say2 " season <n> begins. " (followed by NXF-09)
- NXE-61 sentence say2 " the new schedule is made. "
- NXE-71 sentence say2 " retiring: <n> in the league, <m> from your team. " (short mode)
- NXE-72 sentence say2 " your players: improved <n>, declined <m>. " (short mode)

The draft (NXK)
- NXK-01 sentence say2 " the draft has 7 rounds. you have pick number <n> in every round. "
- NXK-02 sentence say2 " round <n>. "
- NXK-03 sentence say2 " pick <n>: the <team> take <player>, <position>. "
- NXK-04 prompt say2 " <coach> it is your pick, round <round>, pick <pick>. your open places: <list>. "
- NXK-05 sentence say2 " the staff's list. "
- NXK-06 sentence say2 " <player>, <position>, about <lo> to <hi>, age <a>, <potential> potential " (a list line)
- NXK-07 menu say2 "hear more prospects"; NXK-08 menu say2 "let the staff pick"; NXK-09 menu say2 "staff makes your other picks"
- NXK-10 sentence say2 " you take <player>, <position>. "
- NXK-11 sentence say2 " the draft is over. your rookies: "
- NXK-12 sentence say2 " the staff took <player>, <position>. "
- NXK-13 piece piece "none"
- NXK-20 piece piece "high"; NXK-21 "average"; NXK-22 "low" (the potential words)

Players and positions (NXL)
- NXL-01 piece piece "running back"; NXL-02 "receiver"; NXL-03 "quarterback"; NXL-04 "defensive lineman"; NXL-05 "linebacker"; NXL-06 "cornerback"; NXL-07 "safety"; NXL-08 "returner"; NXL-09 "kicker"; NXL-10 "punter"
- NXL-11 piece piece "running backs"; NXL-12 "receivers"; NXL-14 "defensive linemen"; NXL-15 "linebackers"; NXL-16 "cornerbacks"; NXL-17 "safeties"; NXL-18 "returners" (the groups of more than one place; the groups of one place use NXL-03, NXL-09 and NXL-10)
- NXL-21 piece piece "<position> <n>" (an open place count in NXK-04's list)
- NXL-30 sentence say5 " <group>: <n> " (a roster group in F9)
- NXL-31 sentence say5 " <player>, <position>, rating <r>, age <a>, <potential> potential " (a player in a list)
- NXL-40 sentence say5 " <k>. the <team>, <r>. " (a team in the ratings list)
- NXL-41 sentence say5 " your team is number <k> of 32. "

History (NXG)
- NXG-01 menu say5 "champions by season"; NXG-02 menu "your record"; NXG-03 menu "season by season"; NXG-04 menu "league records"; NXG-05 menu "retired stars"
- NXG-10 sentence say5 " season <n>: the <champion> over the <runner_up>. "
- NXG-11 sentence say5 " seasons: <n>. wins: <w>. losses: <l>. play off seasons: <p>. Super Bowls won: <s>. "
- NXG-12 sentence say5 " season <n>: you were <w> and <l>, <finish>. champion: the <champion>. the best record: the <best>. the worst: the <worst>. "
- NXG-13 sentence say5 " most wins in a season: the <team>, <w>, season <n>. "
- NXG-14 sentence say5 " most points in a game: the <team>, <p> against the <other>, season <n>. "
- NXG-15 sentence say5 " the biggest win: the <team> over the <other>, <score>, season <n>. "
- NXG-16 sentence say5 " the longest winning streak: the <team>, <k> games, season <n>. "
- NXG-17 sentence say5 " <player>, <position>, the <team>. seasons played: <n>. best rating <r>. retired after season <s>. "
- NXG-18 sentence say5 " nothing yet. "

Help (H12, C6), added after the N. F. L. rules help, only while the franchise is in use (each under 200 characters)
- NXH-34 help say5 " With a franchise. F9. the franchise menu: the to do list, the news, your roster, the league history and the team ratings. " (F5)
- NXH-35 help say5 " A franchise is a league that lasts from season to season. Your players have ratings, grow older, improve and decline, and retire. " (F6)
- NXH-37 help say5 " After the play offs comes the offseason with the draft and the roster cut. Before a game you hear the news and your to do list. Extra work you leave undone puts you behind the other teams. " (F6, after NXH-35)
- NXH-36 help say5 " Rating: a player's skill from 40 to 99, where 70 is average. Potential: how fast a young player may still improve. " (F7)
- NXH-38 help say5 " Draft: the yearly choice of new players; the weakest teams pick first. Rookie: a player in his first season. Released: let go from the team. " (F7, after NXH-36)

The news pools (kind remark, speaker say2, feature franchise: the defaults of `customize\news.txt`, section 15; four lines each, so the "never one of the last three" rule always has a line to give)
- NWB (the biggest win): NWB01 " the <team> beat the <other> by <n> points. "; NWB02 " a big win for the <team>, <score> over the <other>. "; NWB03 " the <team> ran over the <other>, <score>. "; NWB04 " the <other> had no answer for the <team>, <score>. "
- NWU (an upset): NWU01 " an upset: the <team> beat the <other>, <score>. "; NWU02 " nobody expected it: the <team> over the <other>, <score>. "; NWU03 " the <other> stumbled against the <team>, <score>. "; NWU04 " a surprise result: the <team> got past the <other>, <score>. "
- NWC (the closest game): NWC01 " the closest game of the week: the <team> over the <other>, <score>. "; NWC02 " the <team> just held off the <other>, <score>. "; NWC03 " a nail biter: the <team> beat the <other>, <score>. "; NWC04 " the <other> came up just short against the <team>, <score>. "
- NWS (a winning streak): NWS01 " the <team> have won <n> in a row. "; NWS02 " nobody can stop the <team>: <n> wins in a row. "; NWS03 " the <team> keep rolling, <n> straight wins. "; NWS04 " <n> wins in a row for the <team>. "
- NWL (a losing streak): NWL01 " the <team> have lost <n> in a row. "; NWL02 " a hard time for the <team>: <n> losses in a row. "; NWL03 " the <team> are looking for a win after <n> straight losses. "; NWL04 " <n> losses in a row for the <team>. "
- NWY (your winning streak): NWY01 " <coach>, your team has won <n> in a row. "; NWY02 " <n> straight wins for coach <coach>. "; NWY03 " the fans are happy, coach <coach>: <n> wins in a row. "; NWY04 " your team is on a roll, <n> wins in a row. "
- NWZ (your losing streak): NWZ01 " <coach>, your team has lost <n> in a row. "; NWZ02 " <n> straight losses for coach <coach>. "; NWZ03 " the fans want a win, coach <coach>: <n> losses in a row. "; NWZ04 " a hard stretch for your team, <n> losses in a row. "
- NWM (the coach's milestone): NWM01 " <coach> won game number <n> as a head coach. "; NWM02 " win number <n> for coach <coach>. "; NWM03 " coach <coach> has <n> wins now. "; NWM04 " another milestone: <n> wins for coach <coach>. "
- NWT (the champion, offseason): NWT01 " the <team> are the champions of season <n>. "; NWT02 " season <n> belongs to the <team>. "; NWT03 " the <team> won it all in season <n>. "; NWT04 " the title of season <n> goes to the <team>. "
- NWR (a star retires, offseason): NWR01 " <player>, <position> of the <team>, retires. "; NWR02 " a great career ends: <player> of the <team> retires. "; NWR03 " the <team> lose <player>, who retires. "; NWR04 " <player> of the <team> says goodbye to football. "
- NWD (the first pick, offseason): NWD01 " with the first pick the <team> took <player>, <position>. "; NWD02 " the first pick of the draft: <player>, <position>, to the <team>. "; NWD03 " the <team> opened the draft with <player>, <position>. "; NWD04 " <player>, <position>, went first, to the <team>. "
- NWP (your big improver, offseason): NWP01 " <player> has worked hard and improved to <r>. "; NWP02 " a big step for <player>: rating <r>. "; NWP03 " <player> is better than ever, rating <r>. "; NWP04 " the extra work paid off for <player>: rating <r>. "
(The pool letters: B biggest win, U upset, C closest, S win streak, L losing streak, Y your win streak, Z your losing streak, M milestone, T champion, R retired star, D first pick, P your improver.)

