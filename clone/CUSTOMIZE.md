# Changing the names and the banter in NFL Football 4

This is inspired by Jim Kitchen. The game is a new version of his N. F. L. football version 4. You can change the team names, the division names, the players' surnames and the announcer's banter, and you can add your own banter lines and your own sounds. With the files left alone the game says and plays exactly what the original does.

## Where the files are

Press F9, choose Customize, then "Open the folder with the names and banter files". The folder is also here:

    %APPDATA%\Kitchensinc Revival\NFL Football 4\customize

It holds these plain text files. Any text editor will do, and a screen reader reads them line by line:

- teams.txt, the 32 team names.
- divisions.txt, the 8 division names.
- surnames.txt, the 1,708 surnames the players' names are drawn from.
- banter.txt, the announcer's remarks.
- footplay.txt, the names of your own team's players. The game writes it at the first game of a season (see below).
- the folder sounds, for your own sound files used in the banter.

After you save a file, choose Reload in the Customize menu, or start the game again. A game in progress keeps the players it already has.

## How a file looks

The first line says what the file is and its format, for example `# NFL Football 4 teams, format 1.` Leave it as it is. Lines that begin with `#` are notes. Every other line is an ID, an equals sign and the text:

    T09 = Mustangs

The ID stays as it is. The text is what the voice speaks, so spell it the way it should sound. A name has 1 to 30 characters, with no comma and no semicolon.

## Rename a team

Open teams.txt and change the name after the ID. The teams are T01 to T32. To rename the Broncos, change `T09 = Broncos` to `T09 = Mustangs`. Two teams cannot have the same name. If you give a team the name another team has, the later one goes back to its original name. A season in progress and a saved game are not affected: they keep numbers, not names.

## Rename a division

Open divisions.txt and change, for example, `D1 = A. F. C. North.` to `D1 = The Northern Group.` The conference names A. F. C. and N. F. C. also appear inside a few fixed sentences of the play offs, and those do not change.

## Your own players' names

footplay.txt holds the 33 names of your own team's players and your quarterback, in sections: Running Backs, Receivers, Defensive Players, Special Teams Players, Kickers and Quarterback. The game draws new random names at the first game of every season, and when a season ends it keeps your old names as footplay.previous.txt. Copy it back over footplay.txt to keep them. If you edit footplay.txt, keep the section headings and the number of names in each section. A section that is wrong gets new random names and the rest stays.

## Other surnames

surnames.txt has 1,708 lines, S0001 to S1708. You can change the names. There are always 1,708 of them.

## The banter

banter.txt has the 142 original lines, B001 to B142. Each time the announcer speaks, the game chooses one line that is on, by chance, and no line comes twice in a game. The F8 key switches all banter off, your lines too.

Change a line by changing the text after its ID. Switch a line off like this:

    B045 = off

Delete a line from the file to get the original back. Add a line of your own with a new ID, B143 or higher:

    B143 = What a hit, Ghip!

Inside a line, these words in square brackets do something:

- `[name]` is a player's name drawn by the game, the same name everywhere in the line.
- `[opponent quarterback]` is the name of the other team's quarterback.
- `[bleep]` plays the original's bleep sound.
- `[sound my laugh.wav]` plays your own sound file from the sounds folder.
- `[pause]` is a short pause of random length. `[pause 2]` is a pause of 2 seconds.
- `[then]` ends a spoken part. The words after it are said as a new part.
- `[faster]` ends a spoken part and says the next part one step faster.
- `[one of: some words | other words | more words]` says one of them, chosen by chance.

A line can be words only, a sound only, or both. For example, a line with text and a sound:

    B144 = What a hit! [sound crunch.wav] Ghip, did you see that?

A line that is only a sound:

    B145 = [sound crowd boo.wav]

A line has at most 500 characters and 20 parts. A sound file goes in the sounds folder inside the customize folder, and the line names it without a folder. Wav files work; if your files are ogg, flac or mp3, they work too when this game's sound layer can read them. A sound file that cannot be used is skipped, the rest of the line is said, and the game tells you once.

## If something is wrong

- A line that cannot be used keeps the original, or is left out if it is new. The game says once how many problems it found in a file, and the log has the details. In the Customize menu, "Check the customization files" reads the results aloud.
- A file that is damaged as a whole (empty, not text, no first line, another format) is copied to a file with the ending damaged1 (the latest three are kept), and a new file with the original names is written. The game says so once.
- A file that is missing is written again, without a word.
- A file that another program holds open, or that cannot be written, is not changed. The original names are used that time.
- "Reset one list to the original" and "Reset all lists to the original" write the original files again. Your own file is kept with the ending before-reset. Your sound files and footplay.txt are never touched.
