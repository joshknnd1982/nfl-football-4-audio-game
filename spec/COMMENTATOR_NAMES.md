# The color commentator's names (nfl4 only, rule 0.13; SZ.1, D-106)

RETIRED 2026-10-27 (BC.2, D-178, D-180): the owner had the original's commentary and its commenters removed ("get rid of all of Jim Kitchen's commentary and commenting code for Gip and other commenters"). Neither Ghip nor any name below is offered or said any more; the analyst is the made-up Gus Delgado, and an older settings.txt that holds one of these names reads as him (the program keeps only SHA-256 digests of the names to recognize them). This file stays as the record of D-106.

The owner asked on 2026-10-22: "The user should be able to change Ghip's name or pick from among popular sports podcaster names that Claude
researches and puts into the game." The game offers the default (Ghip), the names below and the player's own typed name (F9, Rules, Commentator).
The list is in `game/src/nfl4/extras/commentators.py` (`NAMES`, alphabetical, 28 names). Facts only: a name is the host of a sports podcast or
show that a source below lists. Nothing is a recording or a quotation: the game's commentator is a computer voice that says the game's own lines, and
the README, the About text and CUSTOMIZE.md say that the names are used descriptively and that nobody named has anything to do with the game.
Claude is not a lawyer; the owner can empty the list or ask for a name to be removed at any time (one line of `commentators.py`).

Researched 2026-10-22 by web search. Evidence tags: SRC-SECONDARY for every row (published rankings and show listings; the shows' own pages were
not needed for a name). Popularity is not one number: Edison counts weekly reach, Spotify its own listeners, CastFox and Leaderboarded
Apple Podcasts charts; the order of the list is alphabetical on purpose (typing letters in the list jumps to a name), not a ranking.

## Sources

- Edison Research, "Top Sports Podcasts in the United States" (Weekly Insights, April 1, 2026; full-year 2025 weekly reach, 13+): New Heights with Jason and
  Travis Kelce first, Club Shay Shay (Shannon Sharpe) second, The Pat McAfee Show third; Q1 2026: The Bill Simmons Podcast, Pardon My Take, Club Shay Shay and
  New Heights among the top 50, The Herd with Colin Cowherd a headline. https://www.edisonresearch.com/top-sports-podcasts-in-the-united-states/
  (redirects to ssrs.com/insights/top-sports-podcasts-in-the-united-states/; the page itself could not be fetched, the search result text was used)
- Spotify's top sports podcasts of 2025 (Awful Announcing): New Heights (Jason and Travis Kelce), Pardon My Take, The Bill Simmons Podcast, Fantasy
  Footballers, The Pat McAfee Show, The Ryen Russillo Podcast. https://awfulannouncing.com/podcasts/spotify-reveals-top-sports-podcasts-2025.html
- Barrett Media on the Edison podcast ranker: The Dan Patrick Show; The Herd with Colin Cowherd. https://barrettmedia.com/2024/07/18/the-dan-patrick-show-rises-in-latest-podcast-ranker/
- CastFox's 2026 US football podcast ranking: The Ryen Russillo Show, Pardon My Take, The Herd with Colin Cowherd, The Pat McAfee Show, Club Shay Shay.
  https://www.castfox.net/blog/best-football-podcasts-2026
- Leaderboarded (Apple Podcasts data): Pardon My Take, The Dan Le Batard Show, The Bill Simmons Podcast. https://leaderboarded.com/rankings/podcasts/top-sports-podcasts/
  Podstatus (Apple chart, US sports): Pablo Torre Finds Out. https://podstatus.com/charts/applepodcasts/us/sports
- NFL podcast listings (Podcastle, Async, Ranker; 2024 and 2025): Around the NFL (Gregg Rosenthal, Dan Hanzus, Marc Sessler, Chris Wesseling), The Ringer NFL
  Show (Michael Lombardi, Robert Mays, Kevin Clark, Danny Kelly), Chris Simms Unbuttoned (Chris Simms), Green Light with Chris Long (Chris Long), Move The
  Sticks (Daniel Jeremiah, Bucky Brooks), Ross Tucker Football Podcast (Ross Tucker), Wake Up with Ray and J (Ray Garvin), The Rich Eisen Show (Rich Eisen).
  https://podcastle.ai/blog/best-nfl-podcasts and https://podcastreview.org/list/best-nfl-podcasts/
- CastFox's 2026 UK list (football, the world's game): The Rest Is Football (Gary Lineker, Alan Shearer, Micah Richards). https://www.castfox.net/blog/best-sports-podcasts-uk-2026

## Names (28)

Alan Shearer, Bill Simmons, Bucky Brooks, Chris Long, Chris Simms, Chris Wesseling, Colin Cowherd, Dan Hanzus, Dan Le Batard, Dan Patrick, Daniel Jeremiah,
Danny Kelly, Gary Lineker, Gregg Rosenthal, Jason Kelce, Kevin Clark, Marc Sessler, Micah Richards, Michael Lombardi, Pablo Torre, Pat McAfee, Ray Garvin,
Rich Eisen, Robert Mays, Ross Tucker, Ryen Russillo, Shannon Sharpe, Travis Kelce.

Left out on purpose: shows named for a persona or a pair without a host name in the sources (Pardon My Take's hosts), and any name the sources do not give.

## How the game uses a name

The default lines say `<commentator>`; the name is put in when a line is said, so the lines never state a fact about the person (no "you used to play", no
age, no he or she): gentle asides that fit any name, including a name the player types. A typed name keeps letters, digits, spaces, apostrophes, full
stops and hyphens (2 to 30 characters). The setting is `nx_commentator` in settings.txt; it is used from the next game.

Open question for the owner (Q-049): the announcer's radio banter teases the commentator gently ("your notes have a coffee stain", "tell me honestly,
is film study fun"). With a real person's name chosen that teasing names a real person. Default kept (it is the owner's request and the lines are mild);
the owner can ask for the real names to be taken out of the teasing lines or from the list.

BC.3 (2026-10-27, D-189): the analyst is one of the radio crew (Walt Kessler, Gus Delgado, Nora Banks, the Gridiron Radio Network), named in F9, Rules, Broadcast crew (game/src/nfl4/extras/crew.py, crew_menu.py); the setting is nx_analyst (an old nx_commentator is read once into it), and no name of the crew can be a retired one.
