# Changelog, versions 0.16.9 to 0.16.9

The older versions of [CHANGELOG.md](../CHANGELOG.md), moved here whole when it grew too long to read in one piece; the newest versions, how to report a bug and where your files are, are in that file.

## 0.16.9 (2026-10-27, test build)

The seventeenth test installer. The owner played 0.16.8 and found that the radio crew hardly spoke: in eight plays Gus said one line after the sign-on. The crew now talks about twice as much, and a new menu item lets you choose how much. Everything of 0.16.8 is still to be tested too (its section below).

### The radio crew talks more, and you choose how much
In 0.16.8 Gus spoke only after special plays and moments (a touchdown, a sack, a turnover, a big gain, a third down, the red zone), and only now and then, so most plays had nothing after them: the analyst spoke after about one play in eight, and three or four plays in a row often went by in silence. Now Gus also has lines after ordinary plays: a run that gains well, a run that is stopped, a pass caught, a pass that falls incomplete, a punt and a kick off (104 new lines, written in the manner of the real radio broadcasts the crew is modelled on: a reason and what to watch next). Walt fills more of the breaks Gus leaves with an aside, the network's name or the score. With the default level, a whole game has about 140 lines of the crew instead of about 64, and Gus speaks after about one play in two. The play-by-play, the scores and the clock are unchanged, and the crew still never changes how a game goes.

The new item F9, Rules, How much the crew talks (right after Broadcast, in both rule sets) has four levels: a little (exactly as 0.16.8), some (Gus after about one play in three or four, as on a real radio call), a lot (the default) and the most (a line after nearly every play). Enter goes to the next level and says it; Left and Right go down and up. The change is saved at once and used at once, also in the game you are playing: you do not have to wait for the next game. F9, Rules, Reset brings back "a lot". F6 names the item.
- How to test: play a game with comments on (F8) and listen between plays: after most runs and passes you should now hear Gus, and sometimes Walt first ("walk us through that play"). Then, during the same game, press F9, choose Rules, press Down until you hear "How much the crew talks: a lot", press Enter to hear "the most", press Escape twice and play on: Gus now speaks after nearly every play. Go back and choose "a little": the crew is as quiet as in 0.16.8. Try it in Classic too.
- The first key you press still cuts the line being said, so if you choose your play quickly you hear only the start of Gus's line. Wait a moment before you press a key to hear it all.
- The new lines are in remarks.txt (the pools CRG, CRS, CPC, CPI, CPT and CKR, at the end of the file), and you can change or switch off any of them (CUSTOMIZE.md).
- Tell us: which level you like best, whether "a lot" is right as the default, any line that does not fit the play it follows (a "nice run" after a short gain, say), and any line you hear too often.
