# nestor — Claude Code plugin

Council of frontier models for high-stakes decisions. The plugin is **one skill plus references** — no agent, no MCP server, no storage. The calling session executes the protocol; `pal` MCP (external, user-scope) talks to the models.

## Quick reference

- **Type:** plugin (skill only)
- **Core:** `plugins/nestor/skills/nestor/SKILL.md` → `references/` (presets, consensus execution, stage 2, stances, router cases, setup)
- **Requires:** `mcp__pal__consensus` + `mcp__pal__chat` (see `references/setup.md`)

## Development

```bash
claude plugin validate .
python3 -m pytest -q -rs tests/                   # doc checks + private-token scan + consensus state contract (needs PAL_SRC; without it 5 tests SKIP — -rs shows why)
git config core.hooksPath .githooks               # pre-push: token scan over tree and outgoing messages

# A marketplace added from a local path loads the source in place: an edit is live at the next
# session start or /reload-plugins — nothing to redeploy. GitHub installs load a cached copy
# keyed by plugin.json "version": users receive a change only after BOTH a version bump AND a
# push to main. Refresh a cached (GitHub) install on a machine after the push:
claude plugin marketplace update nestor-plugin
claude plugin update nestor@nestor-plugin         # per scope: -s user / -s local; restart the session
```

Roster changes go through design review and a dated entry in `references/presets.md` §Refresh history, never a runtime edit — and every new id gets an entry in `references/openrouter-models.example.json` (`tests/test_doc_links.py` fails otherwise). This repository is public: no personal names, home paths or private project references in files or commit messages (the test enforces it).
