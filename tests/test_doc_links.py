"""Deterministic checks on the skill text — the part of a spec review a script can do.

Nestor is executed by an LLM reading Markdown, so the usual review gate (tests
over code) does not exist for its instructions. These checks cover what the
2026-10 external audit found by hand and what a text-only review tends to miss:

  1. every Markdown link and every inline path (`references/...`, `plugins/...`,
     `tests/...`, `.githooks/...`, `.claude-plugin/...`) resolves — a renamed
     reference file left README pointing at a file that no longer existed;
  2. every `stage2:` / `qualification_kind:` label used anywhere in the text is
     a member of the enum the run-metadata template declares — a label coined in
     a reference file but absent from SKILL.md breaks the analytics sweep;
  3. the number of router acceptance cases SKILL.md and README claim equals the
     number of rows in references/router-cases.md;
  4. retired formulations (a guaranteed pause before tokens are spent, chat
     "only" for stage 2, the old reference path, ...) do not come back;
  5. every model id in the preset table and fallback chains has an entry in
     references/openrouter-models.example.json — without it a refreshed seat
     runs on pal's generic 32K capabilities and silently loses the file packet.

Run:  python3 -m pytest -q tests/test_doc_links.py
      python3 tests/test_doc_links.py [<plugin root>]   (no pytest needed; exit 1 on failure)
NESTOR_PLUGIN_ROOT=<dir> points the checks at another checkout (e.g. a snapshot).
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(os.environ.get("NESTOR_PLUGIN_ROOT") or Path(__file__).resolve().parents[1]).resolve()
SKILL_DIR = ROOT / "plugins" / "nestor" / "skills" / "nestor"
SKILL = SKILL_DIR / "SKILL.md"
REFERENCES = SKILL_DIR / "references"
ROUTER_CASES = REFERENCES / "router-cases.md"

FENCE_RE = re.compile(r"^[ \t]*(`{3,}|~{3,}).*?^[ \t]*\1[ \t]*$", re.M | re.S)
LINK_RE = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
PATH_RE = re.compile(r"(?<![\w/.\-])(?:references|plugins|tests|\.githooks|\.claude-plugin)/[A-Za-z0-9_./\-]*")
PLACEHOLDER = re.compile(r"[<>…{}$\[\]?*]|\.\.\.")
SKIP_LINK = ("http://", "https://", "mailto:", "#")
ENUM_FIELDS = ("stage2", "qualification_kind")
# Formulations retired by the 2026-10 audits (R2, R4, R5); each must stay at zero hits.
RETIRED = (
    "before any tokens are burnt",
    "so you can override a mis-route",
    "setup-atlas",
    "entire vendor chain is exhausted",
    "used **only** for stage 2",
    "six inputs**:",
)
NUMBER_WORDS = {w: i for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen "
    "fourteen fifteen sixteen seventeen eighteen nineteen twenty".split())}


def docs():
    found = [p for p in (ROOT / "README.md", ROOT / "CLAUDE.md", SKILL) if p.exists()]
    found += sorted(REFERENCES.glob("*.md")) if REFERENCES.is_dir() else []
    assert found, "no documentation files under %s" % ROOT
    return found


def prose(path):
    """The document without fenced code blocks (line numbers preserved)."""
    raw = path.read_text(encoding="utf-8")
    return FENCE_RE.sub(lambda m: "\n" * m.group(0).count("\n"), raw)


def line_of(text, pos):
    return text.count("\n", 0, pos) + 1


def clean(token):
    token = token.rstrip(".,:;!?'\"`)")
    token = re.sub(r"#[A-Za-z0-9_.\-]*$", "", token)
    token = re.sub(r":\d+(?:-\d+)?$", "", token)
    return token


def references_in(path):
    """(line, token) for each local link target and inline path in the document."""
    text = prose(path)
    seen = set()
    for m in LINK_RE.finditer(text):
        t = m.group(1)
        if t.startswith(SKIP_LINK):
            continue
        t = clean(t)
        if t and not PLACEHOLDER.search(t):
            seen.add((line_of(text, m.start()), t))
    for m in PATH_RE.finditer(text):
        t = clean(m.group(0))
        if t and not PLACEHOLDER.search(t):
            seen.add((line_of(text, m.start()), t))
    return sorted(seen)


def resolves(token, doc):
    bases = [doc.parent, ROOT, SKILL_DIR]
    return any((b / token).exists() for b in bases)


def enum_of(field):
    """Labels the run-metadata template in SKILL.md declares for a field."""
    raw = SKILL.read_text(encoding="utf-8")
    m = re.search(r"^\s*%s: <([^>\n]*)>" % re.escape(field), raw, re.M)
    assert m, "SKILL.md declares no `%s: <...>` template line" % field
    labels = set()
    for part in m.group(1).split("|"):
        label = part.strip()
        label = re.split(r"\s+(?:—|-|—)\s+|;", label)[0].strip()   # drop inline explanations
        if label:
            labels.add(normalise(label))
    assert labels, "empty enum for %s" % field
    return labels


def normalise(label):
    label = label.strip().strip("`").strip()
    label = re.sub(r"\s*\(.*$", "", label)         # `partial (2/3)` and `partial (N/3 critiques)` → `partial`
    return label


def label_uses(field):
    """(doc, line, label) for every `field: value` use outside the template itself."""
    uses = []
    for doc in docs():
        raw = doc.read_text(encoding="utf-8")
        for m in re.finditer(r"`?\b%s: ([^\n`|<>]+)" % re.escape(field), raw):
            value = m.group(1).strip().rstrip(".,;)")
            if not value:
                continue
            uses.append((doc, line_of(raw, m.start()), value))
    return uses


def stage2_column_labels():
    """Labels in the `stage2` column of the composition table (deliberative-stage-2.md)."""
    path = REFERENCES / "deliberative-stage-2.md"
    if not path.exists():
        return []
    out = []
    raw = path.read_text(encoding="utf-8")
    header_idx = None
    for n, line in enumerate(raw.splitlines(), 1):
        if not line.startswith("|"):
            header_idx = None
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if header_idx is None:
            header_idx = next((i for i, c in enumerate(cells) if "stage2" in c), -1)
            continue
        if header_idx < 0 or set(line.replace("|", "").strip()) <= {"-", " "}:
            continue
        if header_idx < len(cells):
            # The first code span of the cell is the label; later spans are field names
            # in the row's commentary (`notes`, `confidence`) or the degraded string.
            labels = re.findall(r"`([^`]+)`", cells[header_idx])
            if labels and not labels[0].startswith("degraded:"):
                out.append((path, n, labels[0]))
    return out


def router_case_count():
    rows = re.findall(r"^\| (\d+) \|", ROUTER_CASES.read_text(encoding="utf-8"), re.M)
    assert rows, "no numbered rows in %s" % ROUTER_CASES
    return len(rows)


def claimed_case_counts():
    """Every `<N> acceptance cases` mention in SKILL.md and README (digits or words)."""
    claims = []
    for doc in (SKILL, ROOT / "README.md"):
        if not doc.exists():
            continue
        raw = doc.read_text(encoding="utf-8")
        for m in re.finditer(r"\b(\w+) acceptance cases\b", raw):
            word = m.group(1).lower()
            n = int(word) if word.isdigit() else NUMBER_WORDS.get(word)
            if n is not None:
                claims.append((doc, line_of(raw, m.start()), n))
    return claims


# --- tests -------------------------------------------------------------------

def test_links_and_inline_paths_resolve():
    missing = []
    checked = 0
    for doc in docs():
        for line, tok in references_in(doc):
            checked += 1
            if not resolves(tok, doc):
                missing.append("%s:%d: %s" % (doc.relative_to(ROOT), line, tok))
    assert checked > 0, "no local references found — the regexes or the layout changed"
    assert not missing, "unresolved references:\n  " + "\n  ".join(missing)


def test_metadata_labels_are_in_the_template_enum():
    bad = []
    for field in ENUM_FIELDS:
        enum = enum_of(field)
        for doc, line, value in label_uses(field):
            if normalise(value) not in enum:
                bad.append("%s:%d: %s: %s (enum: %s)" % (doc.relative_to(ROOT), line, field, value, sorted(enum)))
    enum = enum_of("stage2")
    for doc, line, lab in stage2_column_labels():
        if normalise(lab) not in enum:
            bad.append("%s:%d: stage2 column: %s (enum: %s)" % (doc.relative_to(ROOT), line, lab, sorted(enum)))
    assert not bad, "labels outside the declared enum:\n  " + "\n  ".join(bad)


def test_router_case_count_matches_prose():
    rows = router_case_count()
    claims = claimed_case_counts()
    assert claims, "SKILL.md / README no longer state how many acceptance cases exist"
    wrong = ["%s:%d claims %d, table has %d" % (d.relative_to(ROOT), l, n, rows) for d, l, n in claims if n != rows]
    assert not wrong, "\n  ".join(wrong)


def test_retired_formulations_stay_out():
    hits = []
    for doc in docs():
        raw = doc.read_text(encoding="utf-8")
        for phrase in RETIRED:
            for m in re.finditer(re.escape(phrase), raw):
                hits.append("%s:%d: %s" % (doc.relative_to(ROOT), line_of(raw, m.start()), phrase))
    assert not hits, "retired formulation back in the text:\n  " + "\n  ".join(hits)


ROSTER_SECTIONS = ("Preset table", "Fallback chains per vendor", "Vendor singletons")
MODEL_ID_RE = re.compile(r"`([a-z0-9-]+/[a-z0-9][a-z0-9.\-]*)`")


def roster_ids():
    """Every full OpenRouter id named in the preset table and the fallback chains (not the history)."""
    text = (REFERENCES / "presets.md").read_text(encoding="utf-8")
    ids, keep, seen = set(), False, set()
    for line in text.split("\n"):
        if line.startswith("#"):
            heading = line.lstrip("# ").strip()
            keep = heading in ROSTER_SECTIONS
            if keep:
                seen.add(heading)
        elif keep:
            ids.update(MODEL_ID_RE.findall(line))
    missing_sections = sorted(set(ROSTER_SECTIONS) - seen)
    assert not missing_sections, "presets.md roster sections renamed or gone (update ROSTER_SECTIONS): %s" % missing_sections
    assert ids, "no model ids found in presets.md roster sections"
    return ids


def test_registry_example_covers_every_roster_id():
    """references/openrouter-models.example.json must know every preset and fallback id — a roster
    refresh that forgets the example sends the new seat to pal's generic 32K capabilities (setup.md §1)."""
    example = json.loads((REFERENCES / "openrouter-models.example.json").read_text(encoding="utf-8"))
    known = {m["model_name"] for m in example["models"]}
    missing = sorted(roster_ids() - known)
    assert not missing, "roster ids absent from references/openrouter-models.example.json:\n  " + "\n  ".join(missing)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        ROOT = Path(sys.argv[1]).resolve()
        SKILL_DIR = ROOT / "plugins" / "nestor" / "skills" / "nestor"
        SKILL, REFERENCES = SKILL_DIR / "SKILL.md", SKILL_DIR / "references"
        ROUTER_CASES = REFERENCES / "router-cases.md"
    failed = 0
    for name, fn in sorted((k, v) for k, v in globals().items() if k.startswith("test_") and callable(v)):
        try:
            fn()
            print("PASS", name)
        except AssertionError as exc:
            failed += 1
            print("FAIL", name, "—", str(exc).replace("\n", "\n     "))
    print("doc checks: %d files, %d failure(s)" % (len(docs()), failed))
    sys.exit(1 if failed else 0)
