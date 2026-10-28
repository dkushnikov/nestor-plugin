# Nestor

A Claude Code plugin that convenes a council of frontier AI models for high-stakes decisions, exploratory questions, or when you need a third opinion.

Named after [Nestor of Pylos](https://en.wikipedia.org/wiki/Nestor_(mythology)), the wise counsellor in the *Iliad* who convened councils of kings and synthesised divergent views into a single path forward: **call the council, mediate, synthesise**.

## When to use

- You're making an architectural decision and want to check if three frontier models converge before committing.
- You wrote a proposal and want it red-teamed from multiple angles simultaneously.
- You have an open-ended question where you don't know the shape of disagreement.
- Your session's current answer feels under-calibrated and you want an independent multi-model read.
- You're choosing between named technical options (library, framework, database) and want structured comparison.

Nestor is **not** for simple factual questions, routine implementation decisions, or when you just want Claude's own take.

## How it works

When you address Nestor — "ask Nestor", "third opinion", "what does the council think?", or an equivalent request for other models' views — the plugin:

1. Formulates a **self-contained question** — strips session context so models reason independently.
2. **Routes** to the right deliberation mode and model roster based on question shape.
3. **Announces its routing** before executing — a notification, not a pause: a mis-route is visible and you can override it in your next message; the session actually waits only where the host's permission rules, your explicit request, or a needed clarification require it.
4. **Runs the council** via [pal](https://github.com/BeehiveInnovations/pal-mcp-server) MCP tools.
5. **Synthesises** a judgment with an explicit agreement map, dissenting views, and unaddressed gaps.

Calling a decision "critical" or "high stakes" does not by itself convene the council. The session may still decide on its own to consult on an irreversible architectural or strategic call (the skill's implicit conditions), and "what do you think?" always gets Claude's own view instead.

Two modes:

**Adversarial** (red-teaming) — three models with assigned stances (for / against / neutral) attack a specific hypothesis. The router picks this when you have a draft proposal and want it pressure-tested.

**Deliberative** (peer-critique) — three models answer neutrally, then each critiques the other two answers anonymously. The router picks this for open-ended questions, technical decisions, or research questions.

## Quick start

### 1. Install pal MCP server

Nestor requires [pal](https://github.com/BeehiveInnovations/pal-mcp-server) — a multi-model MCP server that talks to frontier models via [OpenRouter](https://openrouter.ai/). You'll need `uvx` installed ([install uv](https://docs.astral.sh/uv/getting-started/installation/)).

> **Note (2026-07):** upstream pal is dormant — no releases or commits since v9.8.2 (2025-12-15). Two consequences: (1) pin the version instead of tracking HEAD; (2) **constrain the `mcp` SDK to `<2`** — pal uses the old low-level `Server` API, and with an unconstrained resolve the 2026 `mcp` SDK crashes it at import (`AttributeError: 'Server' object has no attribute 'list_tools'`). pal's built-in model registry is frozen at Dec 2025; Nestor's presets always pass full OpenRouter IDs, which resolve through pal's generic OpenRouter capabilities — enough for text-only questions, but the generic entry assumes a 32K context and pal then silently drops most files from the packet. Supply a registry (`OPENROUTER_MODELS_CONFIG_PATH`) before any consultation that sends files — see `plugins/nestor/skills/nestor/references/setup.md`.

```bash
# Add pal as an MCP server (pinned release + compatible mcp SDK). The key goes into the
# server's environment with -e; your shell expands $OPENROUTER_API_KEY at install time:
claude mcp add -s user pal -e OPENROUTER_API_KEY="$OPENROUTER_API_KEY" -- uvx --with "mcp<2" --from "git+https://github.com/BeehiveInnovations/pal-mcp-server.git@v9.8.2" pal-mcp-server
claude mcp list   # pal … ✔ Connected — the first start fetches and builds pal, later starts take under a second
```

> **Citations caveat:** pal v9.8.2 builds its response from `message.content` only and drops the `url_citation` annotations OpenRouter returns for Perplexity — the `research` preset then reports sources it cannot show. The maintained fix is a small patch (`_append_provider_citations` in the OpenAI-compatible provider; branch `atlas/citations` of [dkushnikov/pal-mcp-server](https://github.com/dkushnikov/pal-mcp-server)). Install from that fork, pinned to a commit, if you use the `research` preset — the exact command and the model registry (required for consultations that send files) are in `plugins/nestor/skills/nestor/references/setup.md`.

If you skipped `-e`, add the key to the pal entry in `~/.claude.json` under `mcpServers.pal.env`. An `export` in your shell profile reaches pal only when Claude Code itself starts from a shell that loaded that profile. Never paste the key into a Claude session.

### 2. Install Nestor

```bash
# from GitHub — the version the repository publishes on main:
claude plugin marketplace add dkushnikov/nestor-plugin
claude plugin install nestor@nestor-plugin
claude plugin list   # nestor@nestor-plugin, Version: <from plugins/nestor/plugin.json>, enabled

# from a local clone (development) — the session then reads the clone in place, see references/setup.md:
claude plugin marketplace add <path-to-clone>
claude plugin install nestor@nestor-plugin
```

Nestor is one skill plus reference files: no server, no storage, nothing else to configure. Everything a consultation sends leaves your machine along one path — your session → pal → OpenRouter → the three models of the chosen preset, plus, after a seat or critic failure, that seat's documented same-vendor fallback model (`plugins/nestor/skills/nestor/references/presets.md`), which receives the identical packet.

### 3. Verify

Start a Claude Code session and type:

> Ask Nestor — should I rewrite a 3k-line Python CLI to Go if my only pain points are dependency management and single-binary distribution?

If you see a routing announcement followed by a structured judgment with agreement map, the plugin is working. That question routes to the `code` preset — three frontier models, two stages. For a cheaper first run ask a sanity-check question about an idea, not a drafted artifact — «Ask Nestor for a quick check: any obvious mistakes in this idea — …» — which routes to rule 5: the `quick` preset (three cheap-tier models) in adversarial mode, one round, no stage 2. Pasting a spec, design doc or plan makes it a rule-2 artifact review (deliberative, two stages, frontier roster) even when you say "quick check"; and naming the preset on a different question shape keeps that shape's mode (rule 0 inherits the base mode), so «via the quick preset: should I rewrite … to Go?» still runs deliberative stage 2 on the cheap roster. A clean-host rule-5 run on 2026-10-28 took about a minute; its OpenRouter side was not metered, but three short cheap-tier calls price out at a few cents, and the larger cost is the chair — the Claude session that reads the references, runs the three steps and writes the synthesis (≈$0.36 of API tokens on Opus 5.5 in that run; on a Claude subscription it draws from your plan instead).

## Example output

```
Routing Nestor's consultation:
  Mode: deliberative
  Preset: code
  Stances: all-neutral
  Rule matched: #2 (technical implementation decision with clear axis)

judgment: Keep Python. Address packaging with PyInstaller or shiv.
  Rewriting 3k lines of working code for a packaging problem is
  disproportionate. The pain points are solvable without a language change.

confidence: high — all three models converged on "don't rewrite"

agreement_map:
  - Converged: rewrite cost exceeds packaging-fix cost at this scale
  - Converged: single-binary is achievable via PyInstaller/shiv/Nuitka
  - Diverged: whether to also add pipx as a distribution channel
    (2/3 yes, 1 said it adds complexity without solving the core issue)

dissenting_view: none (unanimous on "don't rewrite")

unaddressed_gaps:
  - Cross-platform needs not specified — if Windows is a target,
    Go's cross-compilation is a stronger argument
  - Team's Go experience not mentioned — rewrite cost depends on it
```

## Limitations (honest)

1. **In-session synthesis is not architecturally isolated.** The synthesis step happens in the same Claude session, so session context is still in attention. Mitigations: self-contained question discipline, structured presentation that separates council output from session-aware commentary. A future version could use a separate sterile synthesis call.

2. **The router is LLM-interpreted, not deterministic.** Routing rules live in the skill file as markdown and are applied by Claude reading them. It will occasionally mis-route on ambiguous questions. Mitigation: the mandatory pre-execution routing notification makes a mis-route visible and overridable. It is a notification, not a guaranteed pause before tokens are spent — a real wait comes only from the host's rules, an explicit user request to confirm first, or a `needs_clarification` return.

## Model presets

Nestor routes questions to one of five model rosters — `arch`, `code`, `research`, `brainstorm`, `quick`. The current rosters, the composition rules (no synthesizer-family models, compose by low error overlap, first-party delivery) and the dated refresh history with evidence live in one place: [`references/presets.md`](plugins/nestor/skills/nestor/references/presets.md). Rosters are spec-level decisions, refreshed through design review; the skill never changes them at runtime.

Full model IDs and per-vendor fallback chains: [`references/presets.md`](plugins/nestor/skills/nestor/references/presets.md).

## Key empirical finding: the Gemini Flip

During verification, Gemini reversed its position on test questions between `against` and `neutral` stances — at identical 8-9/10 confidence scores in both directions. This proves stance assignment is **roleplay, not belief elicitation**. Consequence: never count votes across stance-assigned runs. Details: [`references/stances-and-gemini-flip.md`](plugins/nestor/skills/nestor/references/stances-and-gemini-flip.md).

## Acknowledgments

Nestor stands on the shoulders of:

- **[pal MCP server](https://github.com/BeehiveInnovations/pal-mcp-server)** by BeehiveInnovations — the multi-model gateway that powers all cross-model deliberation under the hood.
- **[council-skill](https://github.com/mikedyan/council-skill)** by Mike Yan — the original multi-model council concept for Claude Code that started this rabbit hole.
- **[llm-council](https://github.com/karpathy/llm-council)** by Andrej Karpathy — the anonymized peer-review protocol that inspired Nestor's Stage 2 deliberative mode.

## License

MIT
