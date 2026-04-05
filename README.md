# Nestor

The Atlas deliberation counsellor. A named consultation mode that convenes a council of frontier models for high-stakes decisions, exploratory questions, or when a third opinion is needed.

Named after [Nestor of Pylos](https://en.wikipedia.org/wiki/Nestor_(mythology)), the wise counsellor in the *Iliad* who convened councils of kings and synthesised divergent views into a single path forward. That mythological role maps with unusual precision to what this plugin does: **call the council, mediate, synthesise**.

## What it does

When Atlas (the primary AI partner) delegates a question to Nestor, Nestor:

1. Reads Atlas's self-contained question.
2. Routes it internally — picks a deliberation mode (adversarial red-teaming vs deliberative peer-critique), a model roster, and stance assignments — based on question shape.
3. **Announces its routing decision** to Atlas before executing, so mis-routing can be caught early.
4. Runs the council using the underlying `pal` MCP tools (`mcp__pal__consensus` for all modes, plus `mcp__pal__chat` × 3 in parallel for deliberative stage-2 cross-critique).
5. Synthesises a judgment: leads with the answer, reports where models agreed and diverged, flags any gaps the original question missed.
6. Returns the judgment in a structured envelope for Atlas to present back to the user.

## Triggers

Nestor activates when Atlas delegates a question, either because the user said so explicitly or because Atlas judged its own answer under-calibrated. Explicit trigger phrases include:

- "Ask Nestor" / "сходи к Нестору" / "go to Nestor"
- "Третье мнение" / "что думает совет?" / "third opinion"
- "Прогони через совет"
- "Глубокий разбор" (triggers deliberative mode specifically)
- "Важное решение" / "high stakes" / "критично"
- "Think carefully" / "deliberate"

## How Nestor differs from Atlas

| | Atlas | Nestor |
|---|---|---|
| Context | Holds full session memory, project history, conversation state | Fresh read every call — no session memory, no project state |
| Role | General-purpose partner that makes decisions *with* the user | Counsellor called by Atlas for structured multi-model consultation |
| Synthesis | Based on session context + user intent | Based on council output + self-contained question (with a known v1 limitation — see below) |
| Interaction | Synchronous conversation | Explicit delegation by Atlas; single-shot consultation |

The isolation from session momentum is part of why calling Nestor is sometimes more valuable than trusting Atlas's own take on a hard decision.

## v1 honest limitations

This is the **Lite** version (v0.1.0). Documented limitations:

1. **In-session synthesis is not architecturally isolated.** The synthesis step is performed by the in-session Claude acting as Nestor, which means the session context is still in attention. Session framing will subtly influence the synthesis. Mitigations: self-contained question discipline, run metadata logging, explicit presentation form ("Nestor says X. My read, given [context]: Y"). v2 escape hatch: separate sterile synthesis API call, deferred until evidence shows it's needed.
2. **The router is LLM-interpreted, not deterministic code.** The router rules live in SKILL.md and are applied by Claude reading markdown. It will occasionally mis-route on multi-category questions. Mitigation: mandatory pre-execution announcement step so Atlas can catch and override before the council runs. v2 escape hatch: router rewritten as a Python/bash script with regex matching.

See `~/Obsidian/Atlas/Projects/Nestor/` for full design docs, principles (P1–P5), kill criteria, and v2 migration paths.

## Prerequisites

**Requires `pal` MCP server installed and configured separately.** This plugin does NOT bundle `pal`. It assumes `mcp__pal__consensus` and `mcp__pal__chat` tools are available in the Claude Code session.

`pal` also needs an OpenRouter API key to reach the frontier models. See `~/Code/pal-mcp-server` (or the upstream pal project) for installation instructions.

## Installation (local development)

From the Claude Code CLI:

```bash
/plugin marketplace add ~/Code/nestor-plugin
/plugin install nestor@nestor-plugin
```

Exact commands may vary by Claude Code version — check `/plugin help` for the current local-install flow.

## Status

Experimental (v0.1.0 — 2026-04-05). Kill criteria are defined in `~/Obsidian/Atlas/Projects/Nestor/Nestor.md`. Revisit after ~10 real uses. Rip-out cost is near zero: delete this repo, done.

## Related

- `~/Atlas/skills/ai-council/SKILL.md` — the lower-level deliberation skill Nestor wraps (can still be called directly for ad-hoc consultations without the Nestor persona layer)
- `~/Obsidian/Atlas/Projects/Nestor/` — full design: `Nestor.md`, `Current State.md`, `specs/Core Design.md`
- `~/Obsidian/Atlas/Thinking/AI Council — Deliberative Mode Spec.md` — the verified deliberation protocol Nestor uses under the hood
- `~/Code/mnemon-plugin` — sibling plugin (the knowledge-library persona of the Atlas team)
- `~/Code/pal-mcp-server` — the MCP server Nestor depends on

## License

MIT
