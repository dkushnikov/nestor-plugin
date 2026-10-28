# nestor — Claude Code plugin

Council of frontier models for high-stakes decisions. The plugin is **one skill plus references** — no agent, no MCP server, no storage. The calling session executes the protocol; `pal` MCP (external, user-scope) talks to the models.

## Quick reference

- **Type:** plugin (skill only)
- **Core:** `plugins/nestor/skills/nestor/SKILL.md` → `references/` (presets, consensus execution, stage 2, stances, router cases, setup)
- **Requires:** `mcp__pal__consensus` + `mcp__pal__chat` (see `references/setup.md`)

## Development

```bash
claude plugin validate .
python3 -m pytest -q tests/                       # consensus state contract (needs PAL_SRC) + private-token scan
git config core.hooksPath .githooks               # pre-push: token scan over tree and outgoing messages

# Redeploy after editing source:
claude plugin marketplace update nestor-plugin
claude plugin update nestor@nestor-plugin         # per scope: -s user / -s local; restart the session
```

Roster changes go through design review and a dated entry in `references/presets.md` §Refresh history, never a runtime edit. This repository is public: no personal names, home paths or private project references in files or commit messages (the test enforces it).
