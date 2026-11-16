# Changelog, versions 0.16.14 to 0.16.14

The older versions of [CHANGELOG.md](../CHANGELOG.md), moved here whole when it grew too long to read in one piece; the newest versions, how to report a bug and where your files are, are in that file.

## 0.16.14 (2026-11-06, test build)

The keyboard's volume, mute and media keys no longer interrupt the game. Everything of 0.16.13 and earlier below is still to be tested too.

### The volume keys leave the game alone
Before, pressing your keyboard's volume up or volume down key while the game spoke stopped the speech, the game said a stray symbol (NVDA read it as "macron" or "registered"), and the menu started again from its first item. Windows still changed the volume. Now the volume, mute, media (play, pause, next, previous) and browser keys belong to Windows only: the volume changes as always and the game goes on with what it was saying. This is the same in Classic and in the N. F. L. rules. F5 and F6 now say so.

**How to test:** start a game and wait for a play menu. While the announcer is speaking, press volume up and volume down a few times. The volume should change, the sentence should go on to its end, and you should hear no symbol and no repeated menu. Then press Down: the menu should move to the next item as usual.

**Tell us:** if any other key of your keyboard makes the game say a symbol.
