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

If pal connected but a consultation failed: the run-metadata record (or the error text) and the preset that was routed. If files were part of the question: whether `OPENROUTER_MODELS_CONFIG_PATH` was set (without it pal assumes a 32K context and drops most files — `references/setup.md` §1).

Data path for context: your session → pal → OpenRouter → the three models of the preset (plus a same-vendor fallback after a seat or critic failure). Nothing is stored by the plugin; the record you paste is what the session returned to you.
