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
      {version}, {changelog}, {changelog_url}, {releases_url}, {sha256} (the installer's SHA-256 in capitals) and {installer_url}
      (the installer's direct download link). With no template the notes are the section and a link to the whole file. With
      --installer the notes always give the direct link: a template that has no {installer_url} gets a "Download the installer:"
      line before its "Install:" line (nfl4 issue 8, a tester 2026-11-09: "You should always give the installer link"). It
      refuses a version with no section or a top item with no "How to test:".

  release_notes.py <version> --full FILE
      Writes the whole changelog as it stood at that version (the version's section and every older one, from CHANGELOG.md and the
      changelog\\ folder, word for word, newest first, with the "Before you start" part) for the release's asset
      CHANGELOG-<version>.md: a tester who downloads the installer can download what changed beside it (issue 5, 2026-11-07).

  release_notes.py <version> --verify-release
      Asks GitHub (gh) about the published release v<version>: its notes must carry the version's whole section word for word, the
      asset CHANGELOG-<version>.md must be there, the notes must give the direct download link of every installer (.exe) asset, and
      it must not be a draft. Exit code 1 when anything is wrong.

  release_notes.py --backfill [--dry-run]
      Mends every published release that fails --verify-release: notes with no section get it (in place of their short list of
      what is new), notes with no direct installer link get it, a missing CHANGELOG-<version>.md is uploaded. Nothing else of a
      release changes; a version with no section in the changelog is reported and left alone.

--repo owner/name and --branch name override what git's origin says. Plain Python, no package of the game is imported.
"""
import argparse
import hashlib
import json
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
              "sha256": hashlib.sha256(Path(installer).read_bytes()).hexdigest().upper() if installer else "",
              "installer_url": installer_url(repo, version, Path(installer).name) if installer and repo else ""}
    if template:
        body = Path(template).read_bytes().decode("utf-8")
        for place in ("{sha256}", "{installer_url}"):
            if place in body and not values[place.strip("{}")]:
                raise SystemExit("the template has %s: give --installer (and a repository for {installer_url})" % place)
        for key, value in values.items():
            body = body.replace("{%s}" % key, value)
    else:
        body = "%s\n\nThe whole changelog, every version with how to test it: %s\n" % (values["changelog"], values["changelog_url"])
    left = re.findall(r"\{(?:version|changelog|changelog_url|releases_url|sha256|installer_url)\}", body)
    if left:
        raise SystemExit("the template's places were not all filled: %s (give --installer for {sha256})" % ", ".join(left))
    if values["installer_url"]:
        body = with_installer_links(body, [values["installer_url"]])
    return body.rstrip("\n") + "\n"


# ----- The direct installer link in every release's notes (nfl4 issue 8, a tester 2026-11-09, on a note that gave it: "You should
# always give the installer link that was a very good thing."). The release page alone makes a screen reader user find the asset.

DOWNLOAD_LINE = "Download the installer: "


def installer_url(repo, version, name):
    return "https://github.com/%s/releases/download/v%s/%s" % (repo, version, name)


def with_installer_links(body, urls):
    """The notes with a "Download the installer:" line for every link they do not already give: before the "Install:" line, else
    at the end (never inside the changelog section). Notes that give every link come back unchanged."""
    body = body.replace("\r\n", "\n")
    missing = [url for url in urls if url not in body]
    if not missing:
        return body
    added = "".join("%s%s\n\n" % (DOWNLOAD_LINE, url) for url in missing)
    match = re.search(r"^Install:", body, re.MULTILINE)
    if match:
        return body[:match.start()] + added + body[match.start():]
    return body.rstrip("\n") + "\n\n" + added.rstrip("\n") + "\n"


# ----- The changelog in every release (issue 5, a tester 2026-11-07: "A change log needs to be included with every release so we
# know what to test for and what has been changed."). The notes carry the version's section; the asset carries every version.

def asset_name(version):
    return "CHANGELOG-%s.md" % version


def every_section(game=GAME):
    """(prefix, sections) of CHANGELOG.md and every file of the changelog folder, newest first, each version once."""
    text = (game / "CHANGELOG.md").read_bytes().decode("utf-8")
    prefix, sections, _older = split_sections(text)
    folder = game / ARCHIVE_DIR
    for path in sorted(folder.glob("CHANGELOG-*.md")) if folder.is_dir() else []:
        sections = sections + split_sections(path.read_bytes().decode("utf-8"))[1]
    seen, out = set(), []
    for name, block in sections:
        if name != "Unreleased" and name not in seen:
            seen.add(name)
            out.append((name, block))
    out.sort(key=lambda item: as_tuple(item[0]), reverse=True)
    return prefix, out


def full_changelog(version, game=GAME):
    """The whole changelog as it stood at <version>: its section and every older one, word for word."""
    prefix, sections = every_section(game)
    kept = [(name, block) for name, block in sections if as_tuple(name) <= as_tuple(version)]
    if not kept or kept[0][0] != version:
        raise SystemExit("the changelog has no section for %s" % version)
    head = (prefix.rstrip("\n") + "\n\nThis file is the changelog as it stood at version %s, attached to that version's release on "
            "GitHub.\n\n" % version)
    return (head + "".join(block.rstrip("\n") + "\n\n" for _n, block in kept)).rstrip("\n") + "\n"


def gh(*args):
    result = subprocess.run(["gh"] + list(args), capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        raise SystemExit("gh %s failed: %s" % (" ".join(args[:3]), result.stderr.strip()))
    return result.stdout


def _plain(text):
    return text.replace("\r\n", "\n").strip()


def release_body_problems(version, body, assets, draft, block):
    """What is wrong with one published release (its notes, asset names and draft flag) against its changelog section."""
    if block is None:
        return ["the changelog has no section for %s" % version]
    found = []
    if _plain(block) not in _plain(body):
        found.append("the notes of v%s do not carry its changelog section word for word" % version)
    if asset_name(version) not in assets:
        found.append("the release v%s has no asset %s" % (version, asset_name(version)))
    for name in installers(assets):
        if "/releases/download/v%s/%s" % (version, name) not in body:
            found.append("the notes of v%s do not give the direct download link of %s" % (version, name))
    if draft:
        found.append("the release v%s is a draft" % version)
    return found


def installers(assets):
    return [name for name in assets if name.lower().endswith(".exe")]


def _release(version, repo):
    data = json.loads(gh("release", "view", "v" + version, "--repo", repo, "--json", "body,assets,isDraft"))
    return data["body"] or "", [a["name"] for a in data["assets"]], data["isDraft"]


def _repo_branch(game, repo, branch):
    if repo is None or branch is None:
        found_repo, found_branch = origin(game)
        repo, branch = repo or found_repo, branch or found_branch
    if not repo:
        raise SystemExit("no GitHub repository in git's origin: give --repo owner/name")
    return repo, branch


def release_problems(version, game=GAME, repo=None, branch=None):
    repo, branch = _repo_branch(game, repo, branch)
    blocks = dict(every_section(game)[1])
    body, assets, draft = _release(version, repo)
    return release_body_problems(version, body, assets, draft, blocks.get(version))


def mended_body(body, version, block, changelog_url):
    """Old notes with the version's section put in place of their short "What is new" list (or after the opening lines)."""
    body = body.replace("\r\n", "\n")
    if _plain(block) in _plain(body):
        return body
    added = ("What is new in this build, word for word from CHANGELOG.md (the file is also beside the program, and attached below "
             "as %s with every older version):\n\n%s\n\nEvery version, with how to test each item: %s\n\n"
             % (asset_name(version), block.rstrip("\n"), changelog_url))
    match = re.search(r"^What is new in this build.*?(?=^Install:)", body, re.MULTILINE | re.DOTALL)
    if match:
        return body[:match.start()] + added + body[match.end():]
    paragraphs = body.split("\n\n")
    keep = min(2, len(paragraphs))
    return "\n\n".join(paragraphs[:keep]) + "\n\n" + added + "\n\n".join(paragraphs[keep:])


def backfill(game=GAME, repo=None, branch=None, dry_run=False):
    """Mend every published release that lacks its section or its asset. Returns the versions still failing."""
    import tempfile
    repo, branch = _repo_branch(game, repo, branch)
    blocks = dict(every_section(game)[1])
    url = "https://github.com/%s/blob/%s/CHANGELOG.md" % (repo, branch)
    tags = [r["tagName"] for r in json.loads(gh("release", "list", "--repo", repo, "--limit", "200", "--json", "tagName"))]
    failed = []
    for tag in tags:
        version = tag.lstrip("v")
        if not re.fullmatch(r"\d+\.\d+\.\d+", version):
            continue
        body, assets, draft = _release(version, repo)
        found = release_body_problems(version, body, assets, draft, blocks.get(version))
        if not found:
            print("v%s: PASS" % version)
            continue
        if blocks.get(version) is None:
            print("v%s: LEFT ALONE, %s" % (version, found[0]))
            failed.append(version)
            continue
        print("v%s: mending (%s)" % (version, "; ".join(found)))
        if dry_run:
            continue
        with tempfile.TemporaryDirectory() as folder:
            new_body = mended_body(body, version, blocks[version], url)
            new_body = with_installer_links(new_body, [installer_url(repo, version, name) for name in installers(assets)])
            if _plain(new_body) != _plain(body):
                notes_file = Path(folder) / "notes.md"
                notes_file.write_bytes(new_body.encode("utf-8"))
                gh("release", "edit", tag, "--repo", repo, "--notes-file", str(notes_file))
            if asset_name(version) not in assets:
                full = Path(folder) / asset_name(version)
                full.write_bytes(full_changelog(version, game).encode("utf-8"))
                gh("release", "upload", tag, str(full), "--repo", repo)
        again = release_problems(version, game, repo, branch)
        print("v%s: %s" % (version, "PASS" if not again else "FAIL, " + "; ".join(again)))
        if again:
            failed.append(version)
    return failed


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
    parser.add_argument("--full")
    parser.add_argument("--verify-release", action="store_true")
    parser.add_argument("--backfill", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
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
    if args.backfill:
        failed = backfill(game, args.repo, args.branch, args.dry_run)
        return 1 if failed else 0
    if not args.version:
        parser.error("give a version, --check, --archive or --backfill")
    if args.full:
        data = full_changelog(args.version, game)
        Path(args.full).write_bytes(data.encode("utf-8"))
        print("wrote", args.full, len(data.encode("utf-8")), "bytes")
        return 0
    if args.verify_release:
        found = release_problems(args.version, game, args.repo, args.branch)
        for line in found:
            print("PROBLEM:", line)
        print("release v%s:" % args.version, "FAIL" if found else "PASS")
        return 1 if found else 0
    body = notes(args.version, game, args.template, args.installer, args.repo, args.branch)
    if args.out:
        Path(args.out).write_bytes(body.encode("utf-8"))
        print("wrote", args.out, len(body.encode("utf-8")), "bytes")
    else:
        sys.stdout.write(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
