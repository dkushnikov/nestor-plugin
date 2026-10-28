---
name: Install problem
about: pal did not connect, the skill did not load, or the first consultation did not run
title: "[install] <where it stopped>"
labels: install
---

Supported host: Claude Code (interactive or `claude -p`), with pal as a user-scope MCP server and an OpenRouter key. Other hosts are not tested.

Which step stopped, and the exact output (redact the key — it must never appear here):

- `claude --version`
- `claude mcp list` — the `pal` line
- `claude plugin list --json` — the `nestor@nestor-plugin` entry
- The command you ran and what Claude Code or pal printed

If pal connected but a consultation failed: the run-metadata record (the `- timestamp: …` block — in the answer, or in your session log if your host has one) or the error text, and the preset that was routed. Only `timestamp`, `router_decision`, `router_rule_matched`, `models_used`, `degraded`, `stage2`, `background` and `qualification_kind` are safe as they are; **review and redact every other field before posting** — `trigger`, `outcome`, `notes`, `session_overrode_router` and `session_added_qualification` carry your own words and context. If files were part of the question: whether `OPENROUTER_MODELS_CONFIG_PATH` was set (without it pal assumes a 32K context and drops most files — `references/setup.md` §1).

Data path for context: your session → pal → OpenRouter → the three models of the preset (plus a same-vendor fallback after a seat or critic failure). The plugin stores nothing; the record exists only where your session wrote it.
