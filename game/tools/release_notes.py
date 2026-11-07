"""The changelog on GitHub, as the owner's NVDA add-ons have it (rule 0.39, the owner 2026-11-06: "like my NVDA addons, I want all of my
games ... to produce a changelog by default which is put on my github so everyone knows changes that have been made"). This is inspired by
Jim Kitchen.

CHANGELOG.md sits at the root of the game's folder (the repository's root). This tool does three things with it:

  release_notes.py --check [<version>]
      Says what is wrong with the file: the top section must be "## Unreleased ..." or the version given, the versions go newest first,
      every item of the top section says "How to test:", the file stays under 55,000 bytes, and every file of the changelog\\ folder
      is linked from its "Older versions" list. Exit code 1 when anything is wrong.

  release_notes.py --archive
      When the file is over 50,000 bytes, moves its oldest whole version sections into changelog\\CHANGELOG-<oldest>-to-<newest>.md
      (each under 55,000 bytes, newest first) and lists them, with their full GitHub address, under "## Older versions" at the end of
      CHANGELOG.md. Nothing is deleted or reworded.

  release_notes.py <version> [--template FILE] [--installer FILE] [--out FILE]
      Writes a GitHub release's notes: the version's whole changelog section, word for word, as an NVDA add-on's release has it.
      A template (kept in the session's work folder, never committed) holds the release's own lines around it, with the places
      {version}, {changelog}, {changelog_url}, {releases_url} and {sha256} (the installer's SHA-256 in capitals). With no template
      the notes are the section and a link to the whole file. It refuses a version with no section or a top item with no
      "How to test:".

--repo owner/name and --branch name override what git's origin says. Plain Python, no package of the game is imported.
"""
import argparse
import hashlib
import re
import subprocess
import sys
from pathlib import Path

GAME = Path(__file__).resolve().parent.parent.parent       # game\tools\release_notes.py -> the game's folder
LIMIT = 55_000                                              # no markdown file over 55 KB (AGENTS.md, the split rule)
KEEP = 50_000                                               # --archive brings CHANGELOG.md back under this
ARCHIVE_DIR = "changelog"
OLDER = "## Older versions"
VERSION_HEADING = re.compile(r"^## (\d+\.\d+\.\d+) \((\d{4}-\d{2}-\d{2}), (test build|release)\)$", re.MULTILINE)
UNRELEASED_HEADING = re.compile(r"^## Unreleased\b.*$", re.MULTILINE)
ANY_HEADING = re.compile(r"^## ", re.MULTILINE)


def as_tuple(version):
    return tuple(int(n) for n in version.split("."))


def split_sections(text):
    """(prefix, sections, older): prefix is everything before the first "## Unreleased" or version heading; sections is a list of
    (name, text) where name is "Unreleased" or the version; older is the "## Older versions" block (or "")."""
    starts = [m.start() for m in ANY_HEADING.finditer(text)] + [len(text)]
    prefix_end = None
    sections, older = [], ""
    for start, end in zip(starts, starts[1:]):
        block = text[start:end]
        line = block.split("\n", 1)[0]
        version = VERSION_HEADING.match(line)
        if version or UNRELEASED_HEADING.match(line):
            if prefix_end is None:
                prefix_end = start
            sections.append((version.group(1) if version else "Unreleased", block))
        elif line.strip() == OLDER:
            older = text[start:]
            break
        elif prefix_end is not None:                     # another heading between versions belongs to the version above
            name, body = sections[-1]
            sections[-1] = (name, body + block)
    if prefix_end is None:
        prefix_end = len(text) - len(older) if older else len(text)
    return text[:prefix_end], sections, older


def section(text, version):
    for name, block in split_sections(text)[1]:
        if name == version:
            return block.rstrip("\n") + "\n"
    return None


def items_without_how_to_test(block):
    """The "### " items of a section that do not say how to test them ("Smaller fixes" is a list of small items, nfl4's custom).
    A section with no "### " items must still say "How to test:" once."""
    items = block.split("\n### ")[1:]
    if not items:
        return [] if "How to test:" in block else [block.split("\n", 1)[0]]
    return ["### " + item.split("\n", 1)[0] for item in items
            if "How to test:" not in item and not item.startswith("Smaller fixes")]


def problems(game=GAME, version=None):
    path = game / "CHANGELOG.md"
    if not path.is_file():
        return ["CHANGELOG.md is missing (rule 0.39: every program has it from its first commit)"]
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    found = []
    if b"\r" in raw:
        found.append("CHANGELOG.md has CR line ends (every markdown file here is LF)")
    if len(raw) >= LIMIT:
        found.append("CHANGELOG.md is %d bytes, at or over %d: run release_notes.py --archive" % (len(raw), LIMIT))
    _prefix, sections, older = split_sections(text)
    if not sections:
        return found + ["CHANGELOG.md has no version section and no Unreleased section"]
    top = sections[0][0]
    if version is not None and top not in ("Unreleased", version):
        found.append("the top section is %s, not Unreleased or the program's version %s" % (top, version))
    versions = [name for name, _b in sections if name != "Unreleased"]
    if any(name == "Unreleased" for name, _b in sections[1:]):
        found.append("an Unreleased section that is not at the top")
    if [as_tuple(v) for v in versions] != sorted((as_tuple(v) for v in versions), reverse=True):
        found.append("the versions are not newest first")
    if len(set(versions)) != len(versions):
        found.append("a version has two sections")
    for item in items_without_how_to_test(sections[0][1]):
        found.append("the top section's item %r has no \"How to test:\"" % item)
    folder = game / ARCHIVE_DIR
    for archive in sorted(folder.glob("CHANGELOG-*.md")) if folder.is_dir() else []:
        if "%s/%s" % (ARCHIVE_DIR, archive.name) not in older:
            found.append("%s\\%s is not linked from \"%s\"" % (ARCHIVE_DIR, archive.name, OLDER))
        if archive.stat().st_size >= LIMIT:
            found.append("%s\\%s is over %d bytes" % (ARCHIVE_DIR, archive.name, LIMIT))
    for link in re.findall(r"\]\((?:https://github\.com/[^/]+/[^/]+/blob/[^/]+/)?(changelog/[^)]+)\)", older):
        if not (game / link).is_file():
            found.append("\"%s\" links %s, which is not there" % (OLDER, link))
    return found


def origin(game=GAME):
    """owner/name and the default branch, from git's origin."""
    def git(*args):
        result = subprocess.run(["git", "-C", str(game)] + list(args), capture_output=True, text=True)
        return result.stdout.strip() if result.returncode == 0 else ""
    url = git("remote", "get-url", "origin")
    match = re.search(r"github\.com[:/]([^/]+/[^/]+?)(?:\.git)?$", url)
    head = git("symbolic-ref", "refs/remotes/origin/HEAD")
    branch = head.rsplit("/", 1)[-1] if head else (git("rev-parse", "--abbrev-ref", "HEAD") or "master")
    return (match.group(1) if match else None), branch


def archive(game=GAME, repo=None, branch=None):
    """Move the oldest whole sections out of CHANGELOG.md until it is under KEEP bytes. Returns the files written."""
    path = game / "CHANGELOG.md"
    text = path.read_bytes().decode("utf-8")
    if len(text.encode("utf-8")) < KEEP:
        return []
    if repo is None or branch is None:
        found_repo, found_branch = origin(game)
        repo, branch = repo or found_repo, branch or found_branch
    if not repo:
        raise SystemExit("no GitHub repository in git's origin: give --repo owner/name")
    prefix, sections, older = split_sections(text)
    links = [line for line in older.split("\n") if line.startswith("- [")]

    def whole(kept, new_links):
        lines = new_links + links
        block = ""
        if lines:
            oldest_kept = [name for name, _b in kept if name != "Unreleased"][-1]
            block = (OLDER + "\n\nThe versions before %s are in these files, newest first. Each is a markdown file in the `%s` folder of this "
                     "repository.\n\n%s\n" % (oldest_kept, ARCHIVE_DIR, "\n".join(lines)))
        body = prefix + "".join(b.rstrip("\n") + "\n\n" for _n, b in kept)
        return (body + block).rstrip("\n") + "\n"

    kept, moving = list(sections), []
    def room_for_links(count):                             # a link line is about 150 bytes; count them generously
        return ["- [" + "x" * 200 + "]"] * count

    while len(kept) > 2 and len(whole(kept, room_for_links(len(moving) // 5 + 2)).encode("utf-8")) >= KEEP:
        moving.insert(0, kept.pop())                       # moving stays newest first
    if not moving:
        return []
    chunks, current, size = [], [], 0
    header_room = 400
    for name, block in moving:
        length = len(block.encode("utf-8"))
        if current and size + length + header_room >= LIMIT:
            chunks.append(current)
            current, size = [], 0
        current.append((name, block))
        size += length
    chunks.append(current)
    (game / ARCHIVE_DIR).mkdir(exist_ok=True)
    written, new_links = [], []
    for chunk in chunks:
        newest, oldest = chunk[0][0], chunk[-1][0]
        name = "CHANGELOG-%s-to-%s.md" % (oldest, newest)
        head = ("# Changelog, versions %s to %s\n\nThe older versions of [CHANGELOG.md](../CHANGELOG.md), moved here whole when it grew too "
                "long to read in one piece; the newest versions, how to report a bug and where your files are, are in that file.\n\n"
                % (oldest, newest))
        data = (head + "".join(b.rstrip("\n") + "\n\n" for _n, b in chunk)).rstrip("\n") + "\n"
        (game / ARCHIVE_DIR / name).write_bytes(data.encode("utf-8"))
        written.append(game / ARCHIVE_DIR / name)
        new_links.append("- [%s to %s](https://github.com/%s/blob/%s/%s/%s)" % (oldest, newest, repo, branch, ARCHIVE_DIR, name))
    path.write_bytes(whole(kept, new_links).encode("utf-8"))
    return written


def notes(version, game=GAME, template=None, installer=None, repo=None, branch=None):
    text = (game / "CHANGELOG.md").read_bytes().decode("utf-8")
    block = section(text, version)
    if block is None:
        raise SystemExit("CHANGELOG.md has no section for %s" % version)
    missing = items_without_how_to_test(block)
    if missing:
        raise SystemExit("these items of %s do not say how to test them: %s" % (version, "; ".join(missing)))
    if repo is None or branch is None:
        found_repo, found_branch = origin(game)
        repo, branch = repo or found_repo, branch or found_branch
    base = "https://github.com/%s" % repo if repo else ""
    values = {"version": version, "changelog": block.rstrip("\n"),
              "changelog_url": "%s/blob/%s/CHANGELOG.md" % (base, branch) if base else "CHANGELOG.md",
              "releases_url": "%s/releases" % base if base else "",
              "sha256": hashlib.sha256(Path(installer).read_bytes()).hexdigest().upper() if installer else ""}
    if template:
        body = Path(template).read_bytes().decode("utf-8")
        if "{sha256}" in body and not installer:
            raise SystemExit("the template has {sha256}: give --installer")
        for key, value in values.items():
            body = body.replace("{%s}" % key, value)
    else:
        body = "%s\n\nThe whole changelog, every version with how to test it: %s\n" % (values["changelog"], values["changelog_url"])
    left = re.findall(r"\{(?:version|changelog|changelog_url|releases_url|sha256)\}", body)
    if left:
        raise SystemExit("the template's places were not all filled: %s (give --installer for {sha256})" % ", ".join(left))
    return body.rstrip("\n") + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("version", nargs="?")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--archive", action="store_true")
    parser.add_argument("--template")
    parser.add_argument("--installer")
    parser.add_argument("--out")
    parser.add_argument("--repo")
    parser.add_argument("--branch")
    parser.add_argument("--game", default=str(GAME))
    args = parser.parse_args(argv)
    game = Path(args.game)
    if args.archive:
        for path in archive(game, args.repo, args.branch):
            print("wrote", path)
        print("CHANGELOG.md is %d bytes" % (game / "CHANGELOG.md").stat().st_size)
    if args.check or args.archive:
        found = problems(game, args.version)
        for line in found:
            print("PROBLEM:", line)
        print("changelog check:", "FAIL" if found else "PASS")
        return 1 if found else 0
    if not args.version:
        parser.error("give a version, --check or --archive")
    body = notes(args.version, game, args.template, args.installer, args.repo, args.branch)
    if args.out:
        Path(args.out).write_bytes(body.encode("utf-8"))
        print("wrote", args.out, len(body.encode("utf-8")), "bytes")
    else:
        sys.stdout.write(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
