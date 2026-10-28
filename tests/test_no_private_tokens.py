"""Keep host-specific and personal tokens out of this public repository.

Scans every tracked text file (and, with --commits <range>, the commit messages
in that range) for: home-directory paths, references to the maintainer's private
repositories and vault folders, session-tracking trailers, and a short list of
personal names kept as salted hashes so the list itself does not name anyone.

Run: python3 tests/test_no_private_tokens.py [--commits origin/main..HEAD]
     python3 -m pytest -q tests/test_no_private_tokens.py
"""
import hashlib
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PATTERNS = [
    (re.compile(r"/Users/[A-Za-z0-9_.-]+"), "home path"),
    (re.compile(r"~/(Atlas|Obsidian|Sources|Data|Code|Projects)\b"), "private tree path"),
    (re.compile(r"\b_claude/"), "private working folder"),
    (re.compile(r"\bProjects/Nestor\b"), "private vault folder"),
    (re.compile("Claude-" + "Session:"), "session trailer"),  # split so this file does not match itself
    (re.compile(r"\bsession[_ ]?[0-9a-f]{8,}\b", re.I), "session id"),
]
SALT = "nestor-public-repo"
TOKEN_RE = re.compile(r"[A-Za-zА-Яа-яЁё][A-Za-zА-Яа-яЁё'’-]{2,}")
# URL allowance: the maintainer's GitHub handle is public in repository URLs.
URL_RE = re.compile(r"https?://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\.git)?(?:@[A-Za-z0-9_./-]+)?")


def _hash(token: str) -> str:
    return hashlib.sha1((SALT + token.lower()).encode("utf-8")).hexdigest()


def _load_private_hashes() -> set:
    extra = ROOT / "tests" / "private-token-hashes.txt"
    hashes = set()
    if extra.exists():
        for line in extra.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                hashes.add(line)
    return hashes


def scan_text(text: str, where: str, hashes: set) -> list:
    hits = []
    stripped = URL_RE.sub("<url>", text)
    for pat, label in PATTERNS:
        for m in pat.finditer(stripped):
            hits.append(f"{where}: {label}: {m.group(0)}")
    for m in TOKEN_RE.finditer(stripped):
        if _hash(m.group(0)) in hashes:
            hits.append(f"{where}: private name at offset {m.start()}")
    return hits


def tracked_files() -> list:
    out = subprocess.run(["git", "-C", str(ROOT), "ls-files"], capture_output=True, text=True, check=True).stdout
    return [ROOT / p for p in out.split("\n") if p and not p.endswith((".png", ".jpg", ".gif", ".ico"))]


def scan_repo(hashes: set) -> list:
    hits = []
    for path in tracked_files():
        if path.name in ("private-token-hashes.txt", "test_no_private_tokens.py"):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        hits += scan_text(text, str(path.relative_to(ROOT)), hashes)
    return hits


def scan_commits(rng: str, hashes: set) -> list:
    out = subprocess.run(["git", "-C", str(ROOT), "log", "--format=%H%n%B%n==END==", rng],
                         capture_output=True, text=True, check=True).stdout
    hits = []
    for block in out.split("==END=="):
        block = block.strip()
        if not block:
            continue
        sha, _, body = block.partition("\n")
        hits += scan_text(body, f"commit {sha[:8]}", hashes)
    return hits


def test_tracked_files_have_no_private_tokens():
    hits = scan_repo(_load_private_hashes())
    assert not hits, "\n".join(hits)


if __name__ == "__main__":
    hashes = _load_private_hashes()
    hits = scan_repo(hashes)
    if "--commits" in sys.argv:
        hits += scan_commits(sys.argv[sys.argv.index("--commits") + 1], hashes)
    if "--hash" in sys.argv:  # helper: print the hash of a token to add to the list
        print(_hash(sys.argv[sys.argv.index("--hash") + 1]))
        sys.exit(0)
    for h in hits:
        print(h)
    print(f"private-token scan: {len(hits)} hit(s)")
    sys.exit(1 if hits else 0)
