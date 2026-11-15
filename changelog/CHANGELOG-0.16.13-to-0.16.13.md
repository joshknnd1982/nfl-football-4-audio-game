# Changelog, versions 0.16.13 to 0.16.13

The older versions of [CHANGELOG.md](../CHANGELOG.md), moved here whole when it grew too long to read in one piece; the newest versions, how to report a bug and where your files are, are in that file.

## 0.16.13 (2026-11-06, test build)

In a franchise on the real calendar, teams with the same record are now put in order by the NFL's own tie-breakers, for the standings, the division titles, the wild cards and the play-off seeds. Everything of 0.16.12 and earlier below is still to be tested too.

### The NFL's tie-breakers in the standings and the play-offs
When two or more teams finish with the same record, the game now follows the NFL's tie-breaking procedures: first the games between the teams, then the record in division games (inside a division) or in conference games (for a wild card), the record against common opponents, the strength of victory and of schedule, points scored and allowed, net points, and last a coin toss. Before, equal teams kept the league's order, and your team won every tie for the last place; now it must win the tie-breaker like everyone else. The coin toss is fixed for each season, so the seeds never change between rounds. The game cannot count touchdowns of the other games, so the NFL's net touchdowns step is skipped. Classic and a franchise on the original's 16 weeks are unchanged.

**How to test:** play a franchise on the real calendar to the end of a regular season (week 18). Listen to the standings after each week: inside a division, a team with a better winning percentage now comes first even with as many losses, and equal teams are in tie-breaker order. At the end of the regular season the game names the division winners, the wild cards and the two teams with a bye; when a tie-breaker decided your division title or your conference's last wild card place, one more sentence says who won it, over whom, and why (for example "the games between the teams"). F6 in a franchise now says that equal records are settled by the NFL's tie-breakers.

**Tell us:** when your team was in a tie, did the sentence make clear why it got in or stayed out?
