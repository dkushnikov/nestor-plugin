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

When you say "ask Nestor", "third opinion", "high stakes", "what does the council think?", or similar, the plugin:

1. Formulates a **self-contained question** — strips session context so models reason independently.
2. **Routes** to the right deliberation mode and model roster based on question shape.
3. **Announces its routing** before executing, so you can override a mis-route.
4. **Runs the council** via [pal](https://github.com/BeehiveInnovations/pal-mcp-server) MCP tools.
5. **Synthesises** a judgment with an explicit agreement map, dissenting views, and unaddressed gaps.

Two modes:

**Adversarial** (red-teaming) — three models with assigned stances (for / against / neutral) attack a specific hypothesis. The router picks this when you have a draft proposal and want it pressure-tested.

**Deliberative** (peer-critique) — three models answer neutrally, then each critiques the other two answers anonymously. The router picks this for open-ended questions, technical decisions, or research questions.

## Quick start

### 1. Install pal MCP server

Nestor requires [pal](https://github.com/BeehiveInnovations/pal-mcp-server) — a multi-model MCP server that talks to frontier models via [OpenRouter](https://openrouter.ai/). You'll need `uvx` installed ([install uv](https://docs.astral.sh/uv/getting-started/installation/)).

```bash
# Add pal as an MCP server:
claude mcp add -s user pal -- uvx --from "git+https://github.com/BeehiveInnovations/pal-mcp-server.git" pal-mcp-server
```

Then set your OpenRouter API key. Either export it in your shell profile:

```bash
export OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

Or add it directly to the pal MCP config in `~/.claude.json` under `mcpServers.pal.env`.

### 2. Install Nestor

```bash
claude plugin marketplace add <path-to-nestor-plugin>
claude plugin install nestor@nestor-plugin
```

### 3. Verify

Start a Claude Code session and type:

> Ask Nestor — should I rewrite a 3k-line Python CLI to Go if my only pain points are dependency management and single-binary distribution?

If you see a routing announcement followed by a structured judgment with agreement map, the plugin is working.

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

2. **The router is LLM-interpreted, not deterministic.** Routing rules live in the skill file as markdown and are applied by Claude reading them. It will occasionally mis-route on ambiguous questions. Mitigation: mandatory pre-execution announcement so you can catch and override before tokens are spent.

## Model presets

Nestor routes questions to one of five model rosters:

| Preset | Used for | Models |
|--------|----------|--------|
| `arch` | Red-teaming, exploratory questions | Claude Opus, Gemini Pro, GPT-5 Pro |
| `code` | Technical decisions | Codex, Gemini Pro, Claude Opus |
| `research` | Factual/research questions | Perplexity Sonar, Gemini Pro, GPT-5 Pro |
| `brainstorm` | Creative divergence (explicit only) | DeepSeek, Grok, Llama Maverick |
| `quick` | Low-stakes sanity checks | Gemini Flash, GPT-mini, DeepSeek Flash |

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
