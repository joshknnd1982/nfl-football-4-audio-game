# AGENTS.md: entry file for any AI coding agent

Project: the Kitchen and PCS Games Revival. Josh Kennedy (the owner, blind, Windows, screen reader NVDA) rebuilds old audio games for blind players as his own open-source games, loosely inspired by Jim Kitchen's games and PCS Games titles. GitHub: https://github.com/joshknnd1982.

These instructions are for ANY AI coding agent: OpenAI Codex, Claude Code or another. "The agent" in every rule file means whichever agent runs this session. Codex and most agents read this file by themselves; Claude Code reads `CLAUDE.md`, a shim that imports this file and the two rule parts. Nothing in the rules depends on one product (section 1.1 of `AGENTS.part02.md`).

## Read first, every session

Read these in full, in this order, before you do anything else. If your tool already loaded them (Claude Code does, through `CLAUDE.md`), do not read them again. If it did not, read them with your file tool, in several reads when one read is cut short. Do not work from memory or from this summary.

1. `AGENTS.part01.md`: the file map and the core rules 0.1 to 0.32.
2. `AGENTS.part02.md`: rules 0.33 onward, the owner and working style (section 1, 1.1), phases and sessions (section 3), folder layout (section 4), legal notes (section 10).

Then read what the phase needs (the file map in `AGENTS.part01.md` names it): `playbook-1-spec-reverse-engineering.md`, `playbook-2-clone.partNN.md` (all parts), `playbook-3-release-platforms.md`, `fixesforgames.partNN.md` (section A first). In a game folder also read `PROJECT_STATE.md` and `spec/OPEN_QUESTIONS.md` (when they are split, every part), and for nfl4 the files its rules name.

A markdown file is a whole file `NAME.md` or parts `NAME.part01.md`, `NAME.part02.md` and so on (no file over 60 KB). Read all parts, in order. Append new text to the LAST part and never enlarge a part past 55 KB.

## If you read nothing else

- Chat with the owner in short plain words: no emoji, no decoration, no table over 3 columns, each command in its own code block, one question at a time with the recommended answer first. He cannot judge anything visual.
- Do the work yourself in this order: read, run, search the web, install a free tool, pick a sensible default and record it in `DECISIONS.md`. Ask the owner only what nobody else can answer (rule 0.8).
- Never claim work you did not do or run. Run the tests and the build before you say it works, and say what was and was not run.
- `original/` is read-only. Never commit original programs, `work/`, tokens or anything private.
- Commit locally after each working step and push the commit to the game's own repository on `joshknnd1982` in the same session (rule 0.35). Never force a push. Releases, tags and new repositories wait for the owner.
- Edit the rule files only in the master folder `C:\Users\joshk\OneDrive\dev`, then run `python games/tools/sync_playbooks.py` (rule 0.9). A lesson that exists only in a state file is lost: add it to `fixesforgames`.
- End every session with `PROJECT_STATE.md`, `SESSION_LOG.md` and a whole new `NEXT_PROMPT.txt` (section 3.3).
