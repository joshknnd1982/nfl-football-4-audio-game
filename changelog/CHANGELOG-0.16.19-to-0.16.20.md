# Changelog, versions 0.16.19 to 0.16.20

The older versions of [CHANGELOG.md](../CHANGELOG.md), moved here whole when it grew too long to read in one piece; the newest versions, how to report a bug and where your files are, are in that file.

## 0.16.20 (2026-11-07, test build)

One whistle, now really. From a tester's report on 0.16.19. Everything of 0.16.19 and earlier below is still to be tested too.

### The tackles no longer blow the original game's whistle
From a tester's report (GitHub issue 6): "two whistles appear to be used still." 0.16.18 made every whistle the one whistle the game made, but the original game's three tackle sounds (the pile up, two tacklers and one tackler) end in a referee whistle of their own, so every tackle still blew the original's whistle and every other dead ball the made one. With the N. F. L. rules the game now plays a tackle only up to the moment its old whistle began, then blows the one whistle at that same moment; a play takes as long as before. Your own whistle.wav replaces it there too. A tackle sound of your own (foot4, foot5 or foot6 in the sounds folder) should hold only the hit: it is played whole and the whistle follows it. The Classic rules keep the original game's sounds whole.

**How to test:** play a game with the N. F. L. rules and listen to a run that is tackled, a completed pass and a sack: after the hit you should hear the same whistle as after an incomplete pass, a kick off and the end of a quarter, and no second, different whistle. Turn the stadium sounds off (F9, Rules, Stadium sounds) and listen again. A play with a flag still has two whistles of the same sound: the one that ends the play and the referee's for the flag.

**Tell us:** if you still hear a whistle that is not the same as the others, and after what kind of play.

## 0.16.19 (2026-11-07, test build)

The changelog comes with every release now, and the Start menu opens it. From a tester's report. The four other reports of that night (injured reserve, the safeties and linebackers, the returners in trades, one whistle) were already fixed in 0.16.18; everything of 0.16.18 and earlier below is still to be tested too.

### The changelog in every release, and in the Start menu
From a tester's report (GitHub issue 5): "A change log needs to be included with every release so we know what to test for and what has been changed." Every release on GitHub now has, beside the installer, a file CHANGELOG-<version>.md: the whole changelog as it stood at that version, every item with how to test it. The release's notes carry that version's own part too. Once the game is installed, the Start menu has a new entry, "NFL Football 4 changelog, what is new", which opens this file in Notepad.

**How to test:** open the newest release on the Releases page: below its notes, the assets should list CHANGELOG-<version>.md beside the installer; download it and read it. Install the game, open the Start menu, type "NFL Football 4 changelog" and press Enter: Notepad should open this changelog, with the installed version's section at the top.

**Tell us:** if a release has no changelog file, or the Start menu entry opens nothing.
