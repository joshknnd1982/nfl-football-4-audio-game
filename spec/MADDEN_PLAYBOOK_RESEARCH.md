# MADDEN_PLAYBOOK_RESEARCH (nfl4 only): Madden NFL 27 playbooks as a model for the game's optional playbooks

Status: RESEARCH, version 1.0 (2026-10-14, session SX.0), for `spec\NFL_EXTRA_FEATURES.md` section 10 (NX5, playbooks). nfl4 only (CLAUDE.md rule 0.13). Research only: no code, no other file changed. Plain headings and lists, no tables. The last section lists what SX.1 should take from it.

Retrieved 2026-10-14. Research only, nothing in the project folder was changed. Tags: SRC-OFFICIAL means an EA page (help.ea.com or ea.com/games/madden-nfl/madden-nfl-27) or, for the original game's own table, GAME_SPEC.md. SRC-SECONDARY means a community or news site. UNVERIFIED means not found. Where I paraphrase I say so; no EA text is copied. NX-R6 applies: only football concepts and the structure of the feature are used.

The EA and community pages were read from temporary copies that are not kept in the project (the text is EA's).

## Answers in brief

1. Structure. A Madden playbook is a list of formations (families such as Shotgun, I-Form, Singleback, Pistol; defense: 4-3, 3-4, Nickel, Dime, Dollar, Goal Line), each with sets (alignments tied to a personnel group), each with plays; pre-play tools sit on top (audibles, hot routes, formation shifts, custom adjustments). EA's help names the formation level and the role of audibles and hot routes (SRC-OFFICIAL); the set level and the counts come from a community database (SRC-SECONDARY); EA does not publish a play count per playbook (UNVERIFIED).
2. Team playbooks. Every one of the 32 teams has its own unique playbook that reflects the real team's style (SRC-OFFICIAL). EA does not publish the 32 style labels. EA names a style or a formation for 15 teams, some for one side of the ball only (SRC-OFFICIAL, listed in section 5); for the rest I use community scheme labels (SRC-SECONDARY). Madden also has a few non-team books, certain only for "Shotgun Classic" (SRC-SECONDARY), plus custom books the player builds (SRC-OFFICIAL, SRC-SECONDARY).
3. Madden 27 changes (SRC-OFFICIAL): new short-yardage mechanics (a timing meter for quarterback sneaks, a better run-blocking box), defensive coverage improvements (new zone and match checks, double teams, roll coverage), a rebuilt pre-play system (custom adjustments, macros, formation shifts), Coach Mode. In Franchise, playbooks influence sim results less than before, teams change their playbook when their key players change, and coordinators are real people (SRC-OFFICIAL).
4. Names. Section 3 gives two short lists. Plain football words are usable; everything EA names as a feature, mode, ability or branded play is not.
5. Proposed styles (section 4): seven style playbooks: Pro Style, West Coast, Air Raid, Power Run, Zone Run, Option, Pressure. Each has an offense part and a default defense part, a mapping onto the original's families, and a strength and weakness against the original's six defense calls, read from the original's real 5 by 6 table (GAME_SPEC 5.9). The design is mine (a proposal), the facts it uses are tagged.
6. Team assignment (section 5): all 32 teams assigned. 15 teams have an EA statement behind them (SRC-OFFICIAL, some only for one side of the ball); 17 rest on community scheme labels and 2026 coaching reports (SRC-SECONDARY). The weakest are named.
7. Size (section 6): about 30 offense plays and about 18 defense plays per style; top menus of 10 and 7 items; second-level menus of 3 to 6 items; every item at most 6 words.

## 1. How Madden organizes a playbook

What EA says (SRC-OFFICIAL, help.ea.com "Madden NFL 27 playbooks guide" and the Madden beginner guide, retrieved 2026-10-14):
- A playbook is the team's game plan: all the offensive or defensive plays the player can run. There are two kinds: offensive playbooks (plays when the team has the ball) and defensive playbooks. They are chosen separately, and a player may use another team's offensive or defensive playbook with his own team in most modes.
- Offensive playbooks are organized by formations, for example I-Form, Shotgun, Singleback. I-Form is described as the run formation, Shotgun as the pass formation. Defensive formations such as Nickel, 4-3 and Dime change how many defensive backs or linemen are on the field. Nickel is the balanced coverage choice; Goal Line is the short-yardage choice.
- Offense formation families EA names in its advice: Shotgun, Bunch, Trips, Empty, I-Form, Strong, Singleback. Defense: 3-4, 4-3, Bear, Nickel, Dime, Dollar.
- EA lists play types to look for: short passes (Slants, Drags, Stick, Mesh), play-action, screens, crossing routes, inside and outside runs, short-yardage and goal-line plays, read option, speed option, QB power, RPO, bootlegs and rollouts; defense: nickel blitz, edge blitz, linebacker blitz, Cover 0, 1, 2, 3, 4, zone blitz, goal-line packages.
- EA's own practice routine for testing a book names the groups a good book needs: three to five favorite formations, then one reliable inside run, one outside run, one quick pass, one pass at the middle, one at the sideline, one deep shot, one red-zone play and one answer to the blitz. This is the closest official statement of "concept groups".
- Playbooks can be customized in Play Now, Franchise, Ultimate Team, Team Practice and Online H2H, not in Superstar. A smaller book you know well can beat a bigger one you rarely use (EA's words, paraphrased). The playbook is chosen before the game and usually cannot be changed during it.

The levels, as far as the sources go (my wording):
- Level 1, the playbook (one per team, plus generic and custom books).
- Level 2, the formation family (Shotgun, I-Form, Singleback, Pistol, Goal Line on offense; 4-3, 3-4, Nickel, Dime on defense). SRC-OFFICIAL for the idea and a few names.
- Level 3, the set (also called sub-formation), for example Close, Slot, Y Off, Hulk in I-Form; Double Mug, Over, 3-3 in Nickel. Each offensive set has a personnel group counted as backs, tight ends, wide receivers (22, 21, 20 and so on). SRC-SECONDARY (madden.tools pages for I Form and Nickel). EA confirms personnel groups exist: its deep dive speaks of 12 and 13 personnel and of formation shifts between formations that share one personnel group (SRC-OFFICIAL).
- Level 4, the play inside a set: a named run, pass, play-action, RPO or screen on offense; a named coverage with or without a blitz on defense (examples on the Nickel page: Cover 3 Match, Cover 4 Drop, SS Blitz 0, Cover 2 Man). SRC-SECONDARY.
- Concept groups (quick game, deep passing, inside run and so on) are not a documented menu level in the pages I could read. How the Madden 27 play-call screen names its tabs is UNVERIFIED.

Counts (SRC-SECONDARY, madden.tools playbook database, 2026-10-14, it says its coverage is still growing): the whole game holds 34 formation families and 10,694 plays: offense 18 families and 9,007 plays, defense 16 families and 1,687 plays. Examples: Shotgun 238 sets and 5,631 plays, Singleback 63 sets and 1,449 plays, I Form 17 sets and 330 plays; Nickel 31 sets and 672 plays. This is the game-wide pool, not one playbook. Plays per team playbook: no EA figure (UNVERIFIED). One fan claim says Madden 27 playbooks grew about 30 percent over Madden 26 (a video description, weak). Older figures (Madden 17, about 450 to 470 per team book) are too old to rely on. A team book is a selection from the pool, and it has dozens of formations (EA's Week 1 page says the Texans book has fifteen under-center formations, SRC-OFFICIAL).

Audibles and hot routes, one sentence each:
- An audible changes the called play at the line to one of a few preset alternatives; each formation in a book has four preset audible plays that the player can edit in the Creation Center (SRC-SECONDARY, ClutchPoints). EA tells players to practice their audibles and hot routes (SRC-OFFICIAL).
- A hot route changes the route of one receiver before the snap; in Madden 27 hot routes, formation shifts, coverage changes and per-player assignments can be saved inside "custom adjustments" (SRC-OFFICIAL, Gameplay Deep Dive 2026-06-04). In Coach Mode the pre-play menu closes with 15 seconds left on the play clock, which ends audibles and hot routes (SRC-OFFICIAL).

What the game may take: formation family, set and play as three levels, the offensive and defensive book chosen separately (EA does this too), four preset audible alternatives. Nothing else.

## 2. The 32 team playbooks and Madden 27 changes

Release: Madden NFL 27 launched worldwide 2026-08-13 (EA news page; early access from 2026-08-06 and 2026-08-10 per community pages). SRC-OFFICIAL for the 08-13 launch.

Playbooks:
- Every NFL team has a unique playbook reflecting its real strategy, strengths and style (SRC-OFFICIAL). Books are updated through the season to follow what teams really do, in Play Now, Franchise and Superstar (SRC-OFFICIAL, Week 1 breakdown, 2026-09-08).
- EA does not list the 32 books with labels on any page I could reach (UNVERIFIED). Community pages agree there are 32 team books "plus a few custom ones" (ClutchPoints, SRC-SECONDARY).
- Non-team books: "Shotgun Classic", a shotgun-only generic book, is named by games.gg and timesaver.gg (SRC-SECONDARY). "Pistol" and "Multiple D" are named as books by one ranking site (maddenprodigy.com, SRC-SECONDARY, one source only). The settings menu offers the team books "or custom options" (SRC-OFFICIAL). Player-built books come from the Creation Center, starting from a team book (SRC-SECONDARY).
- EA's official starting points (SRC-OFFICIAL): offense: balanced = Pittsburgh Steelers; pass-heavy = Kansas City Chiefs or Los Angeles Rams; power run = Tennessee Titans or Pittsburgh; mobile quarterback = Baltimore Ravens or Buffalo Bills. Defense: balanced = Kansas City; pressure = Pittsburgh; coverage = Green Bay Packers; run-stopping = Baltimore. EA says there is no single best book.
- EA's own four offense playstyles and four defense playstyles (above) are a good official skeleton for the game's styles.
- A community scheme taxonomy exists (madden.tools "Schemes", SRC-SECONDARY): 11 offensive schemes (Air Raid, Multiple Power Run, Multiple Zone Run, Pistol, Run and Shoot, Spread, Vertical Power Run, Vertical Zone Run, West Coast Power Run, West Coast Spread, West Coast Zone Run) and 10 defensive schemes (3-4 Storm, 3-4 Under, 4-3 Cover 3, 4-3 Quarters, 4-3 Under, 46, Base 3-4, Base 4-3, Disguise 3-4, Tampa 2). EA's Madden 27 pages that I read do not name these; they are the scheme labels of Franchise (archetype fit). The site's "example teams" on scheme pages disagree with its own team pages (for example Tampa 2 shows no example team but six team pages list it), so I used the team pages and mark that as weak.
- Not Madden: College Football 27 has 31 defensive playbooks in six Defensive Styles (Man, Man Pressure, Shell, Zone, Zone Pressure, Multiple) (SRC-OFFICIAL, same deep dive). This is not a Madden fact; I only note it because some pages mix the two.

Madden 27 changes (SRC-OFFICIAL, Gameplay Deep Dive 2026-06-04, ea.com pages; paraphrased):
- Short yardage: a timing meter for quarterback sneaks and goal-line pushes whose window depends on the push strength of center, guards and quarterback against the defenders nearest the ball, so a sneak is never automatic; better trench physics; new control over run blocking assignments; on defense a "gap integrity" setting (stay in the assigned gap or shed freely) and a defensive aggression setting for run defense; chip blocks by a tight end or back in pass protection. The "Tush Push" play is in the game, only in Madden. EA's Week 1 page says only six teams have the "Goal Line Sneak" formation; a trade site says seven books have the push (SRC-SECONDARY, unconfirmed).
- Coverage: a new zone behavior set ("look for work", "plaster" which attaches zone defenders to nearby receivers when a play breaks down, red-zone awareness, deep-zone focus), more match-coverage checks against stacks, bunch and trips, double teams of a chosen receiver, roll coverage toward the fastest or best receiver or a side, more man answers against stacks and bunches.
- Pre-play: a rebuilt pre-play control system; "custom adjustments" (up to 20 saved packages per side, 10 active in a game; they hold fronts, leverage, coverage behavior, protection, pressure looks, route concepts, hot routes, player assignments) and ready-made macros (examples: go vertical, slants, mesh, outs on offense; no deep passes, defend the screen on defense); formation shifts return (the play stays, the formation changes within the same personnel group); play-call substitutions of personnel on the play-call screen.
- Coach Mode: the player acts as coach, the computer plays the snap; options include automatic quarterback and snap, coach suggestions, and the pre-play cutoff at 15 seconds on the play clock.
- Coach DNA 2.0: computer coaches have distinct profiles (shells, stunts, pressure tendencies, coverage structures, philosophy) built from real data, they adapt within a game to what is working, set up plays in sequence, and a "CoachSpeak" pre-play suggestion exists with more than 50 situations.

Playbooks in Franchise, staff and coordinators (SRC-OFFICIAL, Franchise Deep Dive 2026-06-04 and help page FAQ):
- Playbooks and scheme choice can directly affect player development (XP), team performance and computer behavior, especially in Franchise and Superstar; EA advises a playbook that fits the team's archetypes and scheme.
- EA says playbooks had too much influence on sim outcomes (SuperSim), so SuperSim was retuned: roster quality should matter more than the playbook choice. A game should keep playbook modifiers small (this matches NX5 N5.2).
- Teams adapt their playbooks to personnel: if a team replaces the quarterback who defined its offense with one of a different style, the team changes how it plays, and the user is asked; the computer teams do the same.
- Franchise coaching staffs include real NFL coordinators (offensive and defensive) with defined identities; a coordinator hired away for a head job changes the team's identity. Coach abilities, playsheets and weekly strategy (from Madden 26) remain part of Franchise.
- Idea for NX6, not an EA fact: tie a team's style to its head coach or coordinator and let it change when the starting quarterback or the coordinator changes.

## 3. Names: usable football vocabulary and EA's own names

List A, plain football vocabulary the game may use:
- Formations (offense): I-Form, Strong I, Weak I, Full House, Singleback, Shotgun, Pistol, Split Backs, Wishbone, Flexbone, Wildcat, Goal Line, Under Center, Trips, Bunch, Empty, Doubles, Twins, Tight, Wing, Slot, Y Off.
- Formations and packages (defense): 4-3, 3-4, 46, Bear, 5-2, Nickel, Dime, Quarter, Prevent, Goal Line. "Dollar" (six defensive backs) and "Mug" (linebackers walked up to the gaps) are common coaching words; use them only with a spoken explanation in F7.
- Coverages: Cover 0, 1, 2, 3, 4 and 6, quarters, palms, Tampa 2, man press, man free, zone, prevent, deep zone, underneath zone, double coverage, bracket.
- Rushes: blitz, zone blitz, safety blitz, corner blitz, linebacker blitz, edge rush, stunt, twist, delayed blitz, A-gap blitz, run blitz, contain, spy.
- Runs: inside zone, outside zone, stretch, power, counter, draw, sweep, toss, pitch, iso, dive, trap, lead, QB sneak, quarterback draw, quarterback keeper, bootleg, read option, speed option, jet sweep, end around, reverse.
- Passes: slant, hitch, curl, flat, out, in, dig, post, corner, go, wheel, seam, drag, mesh, stick, flood, smash, levels, four verticals, deep cross, screen (running back, receiver, tight end, tunnel, bubble), play-action, rollout, bootleg, RPO (run-pass option), hot route, audible, Hail Mary, quick game, play-action shot.
- Strategy words: balanced, pass-heavy, run-heavy, power run, zone run, West Coast, Air Raid, Spread, option, vertical, pressure, coverage, run-stopping, ball control, short yardage, red zone, two-minute drill, no-huddle.
- The names of the styles themselves in section 4 come from here (Pro Style, West Coast, Air Raid, Power Run, Zone Run, Option, Pressure).

List B, EA's own naming or branding, not used (NX-R6):
- Brand and modes: Madden, Madden NFL, Ultimate Team and MUT, Superstar, Franchise as a Madden feature name (the game's mode name is the owner's word; keep it generic if possible), Madden Championship Series.
- Systems: Persona Engine, Persona DNA, Coach DNA, Coach Mode, CoachSpeak, Coach Suggestions, Coach Vision, Custom Adjustments, macros, Formation Shifts as a menu feature, Play Call Substitutions, Dynamic Subs, Playsheets, Weekly Strategy, Coach Abilities, SuperSim, Franchise Points, Staff Points.
- Mechanics: QB Sneak Meter, Timing Based Catching and the catch meter, Tackle Stick, Hot and Cold, Wear and Tear, Home Field Advantage as a rated feature, Smart Zones, Plaster, Look For Work, Red Zone Awareness, Focus, Roll Coverage, Gap Integrity, Defensive Aggression, ID Mike, Chip Block as a setting, jostle.
- Ratings and abilities: X-Factor and its ability names (Unstoppable Force, Ankle Breaker, Double Me, Universal Coverage, Bottleneck, Brick Wall, Pro Reads, Slot-O-Matic, Momentum Shift and similar), Superstar abilities, Zone Ability, "99 Club", OVR ratings, archetype names (Field General, Elusive Back, Power Back, Improviser and similar), team ratings.
- Branded play and formation labels: names such as "Tush Push" and "Goal Line Sneak" as EA play names (use "quarterback sneak, push"), "Gun Doubles Clamp Stack" style formation names, long play strings (for example "Cheap Flat X Post", "Boomerang RPO Alert Swing"), generic book names such as "Shotgun Classic" and "Multiple D", and scheme labels such as "West Coast Zone Run" or "Vertical Power Run" as one label (the single words are fine).
- Match-coverage check names (Box, Bingo, Stubbie, Skinny, Solo and so on) are coaching words but EA uses them as menu options; leave them out.
- I give only a few examples on purpose and did not copy any play list.
- Added 2026-10-20 (PX SX.10a): more EA names that are not used are in `spec\NFL_PLAYS_RESEARCH.md` section 6.4; Madden 27's concepts in plain words are in its section 6.2.

## 4. Proposed style playbooks (7)

Facts used: EA's four offense and four defense playstyles (section 2), the teams EA ties to them, and the original's table (GAME_SPEC 5.9). The mapping and the strengths are my design (a proposal for SX.1; "strong" and "weak" are football logic read from the original's yard ranges, not tested).

The original's table in short (GAME_SPEC 5.9, SRC-OFFICIAL for this project): runs do poorly against the run calls (Goal Line, Short Run, Long Run) and well against the pass calls (Short Pass, Long Pass); End Run is weak against everything except the pass calls; Screen Pass has a huge yard range against the Blitz (11 to 99) but also a 50 percent sack chance; Short and Long Pass have sack chances of 50 and 60 percent against the Blitz, and Long Pass completes only 40 percent (30 percent against a Long Pass call).

Mapping of Madden concepts onto the original's families (used by every style):
- Offense, Line Plunge (inside run): inside zone, power, counter, iso, dive, draw, trap, lead.
- Offense, End Run (outside run): outside zone, stretch, toss, pitch, sweep, jet sweep, end around, option pitch.
- Offense, Screen Pass: running back screen, receiver screen, tight end screen, tunnel and bubble screen.
- Offense, Short Pass: slant, hitch, curl and flat, stick, drag, mesh, quick out, shallow cross, spacing, RPO throw.
- Offense, Long Pass: four verticals, post, corner, go, deep cross, flood, play-action shot, Hail Mary.
- Offense, quarterback keeper family (NX3): QB sneak, keeper or bootleg, QB draw, read-option keep, QB power.
- Defense, Goal Line: goal-line and bear fronts, eight or nine in the box.
- Defense, Short Run: base front run fits, run blitz, inside run force.
- Defense, Long Run: contain, outside force, edge setting, spy.
- Defense, Blitz: Cover 0 and Cover 1 blitz, zone blitz, nickel, safety, corner and linebacker blitz.
- Defense, Short Pass: underneath zone, Cover 2, Cover 3 flat, man under, Dime and Nickel quick coverages.
- Defense, Long Pass: Cover 4 and quarters, deep thirds, prevent, Cover 6.

Size rule for SX.1 (matches N5.2): each style gets at most three small bonus entries and three small penalty entries (an entry is one play family, with the defense calls it applies to); "small" means up to 2 yards on the ends of a yard range, up to 5 points of completion or sack percent, up to 1 point on the fumble denominator; the plus and minus budgets are equal, and the neutral style changes nothing. EA's own warning that playbooks were too strong in the sim supports this.

1. Pro Style (EA balanced).
   - Offense: even mix of inside run, outside run and passes, play-action off the run; no extremes.
   - Defense: balanced base defense, even use of the six calls.
   - Strength: none; weakness: none. It equals Classic except for names, and is the control group for the balance test.
2. West Coast.
   - Offense: short, quick, high-percentage passes, screens, steady runs, ball control; few long shots.
   - Defense: zone coverage (Cover 2 and 3 flavor), two deep safeties, few blitzes (EA's coverage defense).
   - Offense strong: Short Pass and Screen Pass against Blitz, Goal Line, Short Run and Long Run calls (completion up, sacks down). Weak: Long Pass (completion down) and End Run (yards down).
   - Defense strong against Short Pass and Screen; weak against Line Plunge and End Run (yards up for the offense) and against a Long Pass pump.
3. Air Raid.
   - Offense: pass-first spread, many short and deep passes, screens, few runs; high variance.
   - Defense: nickel-heavy, pass-lean balanced defense, few blitzes.
   - Offense strong: Short Pass and Long Pass against Goal Line, Short Run and Long Run calls (a little more yardage and completion). Weak: sack and interception odds up against Blitz, Short Pass and Long Pass calls; runs lose a little yardage.
   - Defense strong against Short and Long Pass (small); weak against Line Plunge and End Run.
4. Power Run.
   - Offense: heavy inside runs with power and counter, tight end and fullback sets, play-action deep shots; lowest pass rate.
   - Defense: run-stopping heavy fronts, goal-line strength (EA's run-stopping defense).
   - Offense strong: Line Plunge against Goal Line, Short Run and Long Run calls (yards up at both ends); fewer fumbles. Weak: Screen and passes (completion down, sack up), End Run no better.
   - Defense strong against Line Plunge and End Run (yards down, including the goal line); weak against Long Pass and Screen Pass (completion up).
5. Zone Run (outside zone and play-action; Shanahan and McVay style).
   - Offense: stretch runs, boots and play-action passes off them, tight ends in the passing game; End Run is the base play.
   - Defense: four-man front with three deep zones (Cover 3), keeps plays in front.
   - Offense strong: End Run against Short Run, Long Run and Goal Line calls (turns the original's weakest play into a usable one); Short Pass after the fake against Goal Line and Short Run. Weak: Long Pass against Blitz and Long Pass calls; Line Plunge unchanged.
   - Defense strong against Long Pass and End Run; weak against Short Pass and Screen (the flats).
6. Option (mobile quarterback; EA: Ravens, Bills, Cardinals).
   - Offense: quarterback keeper family (sneak, keeper, draw), read option and RPO, motion, end runs and quick passes; trick plays are rare.
   - Defense: contain and discipline against the edge and the keeper, run-stopping.
   - Offense strong: keeper family and End Run against Blitz, Short Pass and Long Pass calls (defense with eyes on the pass). Weak: keepers against Goal Line, Short Run and Long Run calls; fumble odds up (1 in 50 becomes about 1 in 45); Long Pass completion down.
   - Defense strong against End Run and keepers; weak against Long Pass.
7. Pressure (EA: Steelers on defense).
   - Offense: deep play-action shots built on a solid run, vertical routes; boom or bust.
   - Defense: blitz-heavy, man coverage behind it, many pressure looks.
   - Offense strong: Long Pass against Goal Line, Short Run and Short Pass calls (yards up, play-action sacks down). Weak: Short Pass and Screen (completion down), Long Pass against Blitz and Long Pass calls (sack up).
   - Defense strong: the Blitz call gains sack chance and lowers completion; weak: Screen Pass and runs against the Blitz gain more yards, Long Pass beats it when it is picked up.

Notes for SX.1:
- EA lets the player choose the offensive book and the defensive book separately (SRC-OFFICIAL). Recommend the same in the game: each style has an offense part and a default defense part, and the menu offers "Offense: <style>" and "Defense: <style>", defaulting both to the team's style. This costs little and lets the table in section 5 name an exception where EA states a different defensive identity.
- "Classic" stays first and equals the original tables (N5.4, C3).
- Computer play choice for a style: a weighted draw over its plays by down, distance, field position and score (N5.6); the weights are part of each style's data file (for example Power Run calls Line Plunge more on first and second down).

## 5. Assignment of the 32 teams

Method: EA statements first (SRC-OFFICIAL, help page 2026-10-14 and Week 1 breakdown 2026-09-08, listed as "EA:"); then community scheme labels for the team (SRC-SECONDARY, madden.tools team pages, "in-game offense / defense scheme", read 2026-10-14, listed as "labels:"); then 2026 coaching reports (SRC-SECONDARY, RotoWire "Previewing Schemes of 2026 NFL Offenses", 2026-07-24, listed as "RW:"; FanSided 2026-09-23 for the Vikings). Each EA book is named after the team (for example the Steelers book). Used game nicknames; Redskins is Washington. If the game keeps one style per team, the style named first is the team's playbook; "defense:" notes a different defensive identity that SX.1 may use if it splits offense and defense.

Tag per team: OFFICIAL means EA's page states at least the offensive or defensive style used; SECONDARY means only community or news sources; where only one side is official, I say which.

Division 1
- Bengals: Air Raid. EA: Multiple Defense playbook (defense only). Labels: West Coast Power Run / Base 4-3. RW: Taylor lets Burrow throw, few play-action designs. Tag: OFFICIAL for defense, SECONDARY for offense. Defense: Pro Style (balanced multiple).
- Browns: Pressure. Labels: Vertical Power Run / Base 4-3. RW: Monken would prefer three-wide and pass-happy. EA (Week 1): the defense ranked fourth in yards allowed last season (not a style). Tag: SECONDARY, weakest assignment (could be Pro Style).
- Ravens: Option. EA: mobile quarterback offense with option plays; run-stopping defense (heavier packages). Labels: Multiple Power Run / Base 3-4. Tag: OFFICIAL.
- Steelers: Pressure (EA names two things: offense balanced or power run, defense pressure with Nickel and Dime blitzes). Labels: West Coast Power Run / Base 3-4. RW: McCarthy calls plays in 2026, lighter personnel likely. Alternative: offense Pro Style, defense Pressure. Tag: OFFICIAL.

Division 2
- Bills: Option. EA: quarterback runs, RPO, scrambles, the "Goal Line Sneak". Labels: West Coast Zone Run / Tampa 2. madden.tools team page: balanced, run-heavy offense. RW: Brady uses extra tight ends. Tag: OFFICIAL.
- Dolphins: Option. EA: motion-heavy book with trick plays (including a double pass) and lots of pre-snap movement. Labels: West Coast Power Run / Tampa 2. RW: Slowik, run-heavy because of the receivers. Tag: OFFICIAL.
- Jets: Pro Style. Labels: Multiple Power Run / Base 4-3. RW: Reich, three-wide single-back base, moderate tight ends. Tag: SECONDARY.
- Patriots: Pro Style. Labels: Multiple Power Run / Base 3-4. RW: McDaniels, power run opens the deep passing game, jumbo personnel, Parcells tree (a multiple, balanced system). Tag: SECONDARY.

Division 3
- Broncos: Pro Style. Labels: West Coast Power Run / Base 3-4. RW: Payton's offense, Webb calls the plays. Tag: SECONDARY.
- Chargers: Zone Run. Labels: Multiple Zone Run / Base 3-4. RW: McDaniel, Shanahan tree, committed to the run, outside zone and gap runs. Tag: SECONDARY.
- Chiefs: Air Raid. EA: pass-heavy offense, quick throws mixed with deeper passes; balanced defense with base formations and blitzes. Labels: West Coast Zone Run / Base 4-3. Defense: Pro Style. Tag: OFFICIAL.
- Raiders: Zone Run. Labels: Multiple Zone Run / Base 4-3. RW: Kubiak, zone-run-heavy, jumbo personnel. Community defense notes: a flexible 4-3 book (games.gg, timesaver.gg). Tag: SECONDARY.

Division 4
- Colts: Pro Style. EA: defense based on Lou Anarumo, six Nickel packages and a Dollar look against spread offenses (defense only). Labels: West Coast Power Run / Tampa 2. RW: Steichen is pragmatic, play-action, adapts to his quarterback. Tag: OFFICIAL for defense, SECONDARY for offense.
- Jaguars: West Coast. EA: defense has many Cover 4 plays and answers to play-action crossers, four verticals and tight-end attacks (defense only). Labels: West Coast Zone Run / Base 4-3. RW: Coen is pragmatic, wants to be good at everything. Tag: OFFICIAL for defense, SECONDARY for offense.
- Texans: West Coast. EA: shotgun-based with fifteen under-center formations, mesh and crossing concepts, stretch and dive runs. Labels: West Coast Zone Run / Base 4-3. Tag: OFFICIAL.
- Titans: Power Run. EA: power run offense; defense built on four-man line packages, bunch fronts, Dime 2-3 and Dollar. Labels: West Coast Power Run / Base 4-3. Tag: OFFICIAL.

Division 5
- Bears: Power Run. Labels: Multiple Power Run / Base 4-3. RW: Johnson commits to a ground-heavy offense with big personnel. Tag: SECONDARY.
- Lions: Power Run. Labels: Multiple Power Run / Base 4-3. RW: Petzing arrives, steady tight-end personnel; a 2025 note says the Lions began that season run-leaning (Establish The Run via search summary, weak). Tag: SECONDARY, could be Pro Style.
- Packers: West Coast. EA: coverage defense (Cover 2, 3 and 4, nickel, dime, dollar). Labels: West Coast Zone Run / Tampa 2. RW: LaFleur uses the run to set up big passes, Shanahan tree. Tag: OFFICIAL for defense, SECONDARY for offense.
- Vikings: Pressure. FanSided 2026-09-23 (data from Sumer Sports): Flores has led the league in blitz rate every season since 2023 (47.7 percent of dropbacks in 2025, 75 percent in the first two games of 2026). Labels: West Coast Zone Run / Base 3-4. RW: O'Connell, McVay tree. Tag: SECONDARY (strong for defense).

Division 6
- Cowboys: Air Raid. Labels: West Coast Power Run / Base 4-3. RW: in 2025 the offense was defined by tempo and willingness to throw. News: the 2026 defense is moving to a 3-4 based multiple scheme (Pro Football Rumors, 2026-02, via search summary). Tag: SECONDARY.
- Eagles: Option. Labels: Multiple Power Run / Base 3-4. A community ranking calls the book strong on RPOs, quarterback runs, short-yardage football (maddenprodigy.com); the push play is in their book (SECONDARY). RW: Mannion, McVay and LaFleur style, no fullback. News: Fangio's 3-4 two-high defense (Eagles site, search summary). Tag: SECONDARY.
- Giants: Power Run. Labels: Multiple Power Run / Base 4-3. RW: Nagy under Harbaugh, jumbo, tight ends and fullbacks, run-first (the quarterback says so, 2026-05-20). Tag: SECONDARY.
- Redskins (the Commanders): Air Raid. Labels: West Coast Zone Run / Base 4-3. RW: Blough replaced Kingsbury; quick-passing spacing kept, more tight ends and more snaps under center expected. News: the defense is a nickel-heavy 4-2-5 with two-high coverages (search summary, weak). Tag: SECONDARY. Alternative: West Coast.

Division 7
- Cardinals: Option. EA: many RPO and quarterback run plays. Labels: West Coast Zone Run / Tampa 2. RW: Mike LaFleur, run-heavy with two tight ends. Community: one defense book is the Packers' book in effect (games.gg). Tag: OFFICIAL for offense.
- Forty Niners: Zone Run. Labels: Multiple Zone Run / Base 4-3. RW: Shanahan runs often and sets up the pass with it; community: one of the best rushing books (games.gg). Defense: a 4-3 Saleh-style book (timesaver.gg), near copy of the Titans'. Tag: SECONDARY.
- Rams: Air Raid. EA: a passing-built offense creating chances after the catch. Labels: West Coast Zone Run / Base 3-4. RW: McVay, tight-end-heavy in 2026. Tag: OFFICIAL.
- Sea hawks: Zone Run. Labels: Multiple Zone Run / Base 3-4. RW: Fleury keeps the prior zone-heavy, play-action-heavy offense with jumbo tendencies. Defense: Cover 3 tradition (Wikipedia "Seattle Cover 3 defense", general). Tag: SECONDARY.

Division 8
- Buccaneers: Air Raid. EA: a compact package of three plays (cross wheels, a read-flat RPO, a play-action cross) from tight doubles and Y-off trips. Labels: West Coast Zone Run / Base 3-4. RW: Robinson stays in a three-wide template. Tag: OFFICIAL.
- Falcons: Power Run. EA: the book is built around a pistol bunch tight end formation. Labels: Multiple Power Run / Base 4-3. RW: Rees, tight end central in the passing game, new coach Stefanski. A community note calls the pistol run game strong (civil.gg). Tag: OFFICIAL for the formation, SECONDARY for the style.
- Panthers: West Coast. Labels: West Coast Zone Run / Tampa 2. RW: Canales stresses the ground game with power looks to protect Young (this points to Power Run: weak assignment). Tag: SECONDARY, could be Power Run.
- Saints: West Coast. Labels: West Coast Zone Run / Base 3-4. RW: Moore, modest tight-end personnel, no fullback. A community ranking praises its passing variety and quick game (maddenprodigy.com). Tag: SECONDARY.

Totals: Pro Style 4 (Patriots, Colts, Jets, Broncos); West Coast 5 (Packers, Texans, Jaguars, Saints, Panthers); Air Raid 6 (Chiefs, Rams, Bengals, Buccaneers, Redskins, Cowboys); Power Run 5 (Titans, Bears, Lions, Giants, Falcons); Zone Run 4 (Forty Niners, Sea hawks, Raiders, Chargers); Option 5 (Ravens, Bills, Cardinals, Eagles, Dolphins); Pressure 3 (Steelers, Vikings, Browns). That is 32.

Caution: the 2026 coaching facts come from a fantasy football preview and news summaries; coaches and play-callers changed in many places, so the assignments are style fits for a game, not claims about the real teams. The assignment is data and the player can change it (N5.4, N5.7).

## 6. Size estimate for spoken menus (at most 12 items per level, at most 6 words per item)

Offense, per style:
- Top menu 10 items: Inside runs, Outside runs, Screens, Short passes, Deep passes, Play action, Quarterback runs, Field goal, Punt, Save game. (Classic keeps the original's 8 items.)
- Second level: 3 to 6 plays per group, never more than 12. About 4 inside runs, 4 outside runs, 3 screens, 6 short passes, 5 deep passes, 4 play-action passes, 4 quarterback runs: about 30 plays (range 24 to 36).
- Example items, all at most 4 words: "Inside zone", "Power, left", "Counter", "Draw play", "Stretch, outside", "Toss sweep", "Jet sweep", "Running back screen", "Tunnel screen", "Slants", "Curl and flat", "Mesh crossers", "Stick", "Four verticals", "Deep post", "Corner route", "Boot, short", "Play action, deep", "Quarterback sneak", "Quarterback keeper", "Quarterback draw", "Read option".

Defense, per style:
- Top menu 7 items: the six original calls (Goal line, Short run, Long run, Blitz, Short pass, Long pass) and Save game.
- Second level: 2 to 5 plays per call; about 2 to 3 goal line, 3 short run, 2 to 3 long run, 5 blitz, 4 short pass, 3 long pass: about 18 plays (range 14 to 24).
- Example items: "Goal line, eight up", "Run blitz", "Contain, outside force", "Cover 2 zone", "Cover 3 zone", "Man free", "Cover 4 quarters", "Zone blitz", "Cover 0 blitz", "Safety blitz", "Corner blitz", "Prevent deep".

Totals: one shared catalog of about 50 offense plays and 30 defense plays with permanent IDs, and seven style lists of about 30 and 18 entries each with their modifiers and weights, about 340 data rows in all. The playbook text files in the customize folder (N5.7) hold them.

Scale check: Madden's game-wide pool is about 10,700 plays (SRC-SECONDARY); a game style is under half a percent of it, in line with EA's advice that a small book you know well can be better than a large one (SRC-OFFICIAL). EA's practice routine needs 8 situation slots (inside run, outside run, quick pass, middle pass, sideline pass, deep shot, red zone, blitz answer); every style covers all 8.

## Could not settle

- EA's list of the 32 team playbooks with offensive and defensive styles: EA pages do not publish it (help.ea.com in en-us, fi, hu; ea.com Madden NFL 27 pages, deep dives and the launch guide were read). Tried: web search for lists, Madden School (HTTP 403), allthings.how (403), ESPN's play-caller page (empty), the in-game Creation Center is not reachable. What exists is partial: 15 teams by EA statement (some for one side of the ball only), the rest by community labels.
- Plays per Madden 27 team playbook: no EA or reliable number.
- The in-game names of the play-call screen's concept groups in Madden 27: not found.
- The generic books beyond "Shotgun Classic" (and single-source "Pistol", "Multiple D"): no EA list.
- The community scheme labels of madden.tools are not EA's statement and are inconsistent between its pages; the teams' real 2026 defensive schemes are only partly sourced (Cowboys, Titans, Commanders, 49ers, Eagles, Vikings by news summaries). The 2025 pass-rate and blitz-rate statistics I found were partial or of unclear season and were not used.
- The "seven books have the push" claim: only one trade site, unverified. EA says six teams have the Goal Line Sneak formation.
- The balance of the seven styles is untested: SX.1's seeded 10,000-game simulation decides.

## Sources (all retrieved 2026-10-14)

SRC-OFFICIAL (EA):
- https://help.ea.com/en-us/articles/madden-nfl/madden-playbooks-guide/ (playbooks guide, fetched through curl; the fi and hu versions are the same text; WebFetch timed out)
- https://help.ea.com/en/articles/madden-nfl/madden-beginner-guide/ (beginner guide)
- https://www.ea.com/games/madden-nfl/madden-nfl-27 (main page; release news list)
- https://www.ea.com/games/madden-nfl/madden-nfl-27/features/m27-gameplay (gameplay features page)
- https://www.ea.com/games/madden-nfl/madden-nfl-27/news/madden-27-gameplay (Gameplay Deep Dive, 2026-06-04)
- https://www.ea.com/games/madden-nfl/madden-nfl-27/news/madden-27-franchise-mode (Franchise Deep Dive, 2026-06-04)
- https://www.ea.com/games/madden-nfl/madden-nfl-27/news/madden-nfl-27-kickoff-week-1-breakdown (Week 1 breakdown, 2026-09-08)
- https://www.ea.com/games/madden-nfl/madden-nfl-27/features/m27-franchise (Franchise features page)
- C:\Users\joshk\OneDrive\dev\games\kitchensinc\nfl4\spec\GAME_SPEC.md section 5.9 (the original's table)

SRC-SECONDARY:
- https://madden.tools/playbooks, /playbooks/formation/i-form, /playbooks/formation/nickel, /schemes, /schemes/west-coast-zone-run and the 32 team pages under /teams/ (community database: formation counts, scheme labels per team)
- https://games.gg/madden-nfl-27/guides/madden-nfl-27-offensive-playbook-guide/ and /madden-nfl-27-best-defensive-playbooks/ (guides, 2026-08-15 and 2026-10-01)
- https://timesaver.gg/blog/madden-nfl-27-best-playbooks-offense-defense (a coin-selling site, low reliability; used only for the generic book name and the 4-3 book note)
- https://www.maddenprodigy.com/best-madden-27-playbooks/ (ranking, tested 2026-08-11; commercial)
- https://clutchpoints.com/gaming/madden-27-how-to-create-custom-playbooks (custom playbooks, audibles)
- https://madden27.wiki/gameplay/playbooks (independent wiki; repeats EA's guide)
- https://maddenturf.com/madden-27-best-playbooks/ (no Madden 27 tier list yet; Madden 26 notes)
- https://www.rotowire.com/football/article/nfl-playcallers-previewing-schemes-of-2026-nfl-offenses-123079 (2026-07-24, 2026 play-caller notes)
- https://fansided.com/nfl/nfl-stat-of-the-week-the-vikings-are-thriving-under-the-blitz-king-brian-flores (2026-09-23, Vikings blitz rate, data from Sumer Sports)
- Search summaries only (not fetched in full, weak): Pro Football Rumors on the Cowboys' 2026 defense, the Eagles' site on Fangio, Establish The Run on the Lions, Sharp Football Analysis tables of unclear season.

## 7. What SX.1 should take from this research (summary and effects on NFL_EXTRA_FEATURES.md)

- N5.1 is met: the structure of a playbook, the two vocabulary lists, the seven styles with their mapping and the assignment of all 32 teams are above. Madden's own list of the 32 team books and their play counts is not published by EA, so the "32 separate team books" alternative of NQ5 is not supported by evidence; the accepted default (a handful of style playbooks plus an assignment of each team to the closest style) stands.
- N5.4 (selection): EA lets the player pick the offensive and the defensive book separately. Recommended for the game: two menu items, "Offense: <style>" and "Defense: <style>", both defaulting to the team's style, "Classic" always first. This also lets a team keep a different defensive identity where EA states one (section 5 notes the cases: Bengals, Colts, Jaguars, Packers, Steelers).
- N5.2 (mapping and balance): each style is a bounded set of changes to the original's table (section 4): at most three small bonus entries and three small penalty entries, equal budgets, the neutral style (Pro Style) equal to Classic in numbers. EA itself reports that playbooks had too much influence on simulated results and retuned them, which supports small modifiers. The strengths and weaknesses written here are read from the original's 5 by 6 table and are untested; SX.1's seeded 10,000-game simulation decides the final numbers (the balance test of NX5's done-when).
- N5.5 (menus): about 30 offense plays and 18 defense plays per style fit the limits (at most 12 items per menu level, at most six words per item); the top offense menu has 10 items (inside runs, outside runs, screens, short passes, deep passes, play action, quarterback runs, field goal, punt, save game) and the defense top menu keeps the original's six calls plus Save game. Classic keeps the original's 8 and 7 items unchanged.
- N5.7 (customization): the shared catalog of about 50 offense and 30 defense plays with permanent IDs, the seven style lists with weights and modifiers, and the team assignment (32 rows) are data in the `customize` folder, about 340 rows in all. The player may rename or disable plays and change the assignment.
- NX3 link: the quarterback keeper family (sneak, keeper or bootleg, draw, read-option keep) is one of the families in every style; the Option style leans on it, and the rule facts for it are in NFL_RULES_RESEARCH.md Part 4.
- NX-R6 (names): section 3, List B is the "do not use" list (EA's feature, mode, ability and branded play names, long play strings, generic book names, scheme labels as single phrases). The style names themselves (Pro Style, West Coast, Air Raid, Power Run, Zone Run, Option, Pressure) are plain football words. The README and About notice (Madden NFL is a trademark of Electronic Arts; not made or endorsed by EA or the NFL) stays as written in NX-R6.
- Weak assignments to revisit at SX.1 if the owner wishes: Browns (Pressure, could be Pro Style), Panthers (West Coast, could be Power Run), Lions (Power Run, could be Pro Style), Redskins (Air Raid, could be West Coast). The assignment is data and the player can change it.
- The 2026 coaching facts behind the assignments come from preview articles and change often; the assignments are style fits for a game, not claims about the real teams.
- Nothing in this research needs an owner decision before SX.1; the owner may veto the seven-style set or the assignment at any time.
