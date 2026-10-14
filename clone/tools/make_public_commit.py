"""Make the next PUBLIC commit from the working tree without touching the private history. Inspired by Jim Kitchen.

The private local history (branch master) holds material that must never be published (string dumps of the original
program, working notes, playbook copies). The public history is a separate chain of commits made with a temporary
git index, so `.gitignore` decides what is public and no branch is switched.
Usage: python clone/tools/make_public_commit.py "<commit message first line>" [--push]
Reads the previous public commit from work/public_commit_sha.txt and writes the new one there.
Push by hand the first time you check `git ls-files` equivalent: this tool prints the file list size and the
files that changed since the previous public commit.
"""
import os
import subprocess
import sys

GAME = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SHA_FILE = os.path.join(GAME, "work", "public_commit_sha.txt")
INDEX = os.path.join(GAME, "work", "public.index")
IDENTITY = {"GIT_AUTHOR_NAME": "Josh Kennedy", "GIT_COMMITTER_NAME": "Josh Kennedy",
            "GIT_AUTHOR_EMAIL": "15981437+joshknnd1982@users.noreply.github.com",
            "GIT_COMMITTER_EMAIL": "15981437+joshknnd1982@users.noreply.github.com"}
TRAILER = "\n\nCo-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>\n"


def git(*args, env=None, input_text=None):
    result = subprocess.run(["git", *args], cwd=GAME, capture_output=True, text=True, env=env, input=input_text)
    if result.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    message = sys.argv[1]
    parent = open(SHA_FILE).read().strip()
    env = dict(os.environ, GIT_INDEX_FILE=INDEX, **IDENTITY)
    git("add", "-A", env=env)
    tree = git("write-tree", env=env)
    if tree == git("rev-parse", f"{parent}^{{tree}}"):
        print("nothing changed since", parent)
        return
    sha = git("commit-tree", tree, "-p", parent, env=env, input_text=message + TRAILER)
    print(git("diff", "--stat", parent, sha))
    open(SHA_FILE, "w").write(sha + "\n")
    print("new public commit", sha)
    if "--push" in sys.argv:
        print(git("push", "origin", f"{sha}:refs/heads/main"))


if __name__ == "__main__":
    main()
