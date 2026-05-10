# Council Presets — Model Rosters and Fallbacks

Defines the five model rosters Nestor uses when routing a consultation. The `arch` / `code` / `research` / `brainstorm` / `quick` presets map to distinct frontier-model combinations optimised for different question shapes. Nestor's router selects the preset; this file defines what each preset actually contains.

Last refreshed: 2026-05-10 — see history note at bottom.

## Preset table

| Preset | Routed to by | Models (use full OpenRouter IDs) | Rationale |
|---|---|---|---|
| `arch` | Router rule 1 (red-team) and rule 4 (exploratory) | `anthropic/claude-opus-4.7`, `google/gemini-3.1-pro-preview`, `openai/gpt-5.5-pro` | Three frontier reasoners from the three major Western labs — max diversity on complex decisions while keeping Western-RLHF baseline |
| `code` | Router rule 2 (technical decision with clear axis) | `openai/gpt-5.3-codex`, `google/gemini-3.1-pro-preview`, `anthropic/claude-opus-4.7` | Code-specialised model + two general reasoners for design-level tradeoffs |
| `research` | Router rule 3 (factual / research) | `perplexity/sonar-deep-research`, `google/gemini-3.1-pro-preview`, `openai/gpt-5.5-pro` | Perplexity for web grounding, plus two top-tier reasoners for interpretation |
| `brainstorm` | Not routed to by default; user must specify explicitly | `deepseek/deepseek-v4-pro`, `x-ai/grok-4.20`, `meta-llama/llama-4-maverick` | Maximally divergent vendor mix — Chinese MoE + xAI + Meta open-source. No Western-frontier-lab member, by design. The synthesizer (Claude) supplies the Anthropic perspective on top |
| `quick` | Router rule 5 (low-stakes sanity check) | `google/gemini-2.5-flash`, `openai/gpt-5.4-mini`, `deepseek/deepseek-v4-flash` | Three cheap-tier models, three different vendors, none correlated with the Anthropic synthesizer |

**Critical**: always use the full OpenRouter model IDs (e.g., `anthropic/claude-opus-4.7`), never short aliases like `opus`. The pal tool's built-in alias registry may not match these IDs, causing 404 errors.

## Fallback chains per vendor

If a model returns 404 or an error during a consensus run, substitute from the **same vendor** to preserve cross-provider diversity:

- **Anthropic**: `claude-opus-4.7` → `claude-opus-4.6` → `claude-opus-4.5`
- **Google**: `gemini-3.1-pro-preview` → `gemini-2.5-pro` → `gemini-2.5-flash`
- **OpenAI** (general): `gpt-5.5-pro` → `gpt-5.5` → `gpt-5.4`
- **OpenAI** (codex slot, `code` preset only): `gpt-5.3-codex` → `gpt-5.5` → `gpt-5.4` — no current 5.x codex variant beyond 5.3, so general-tier fallback is used
- **OpenAI** (mini slot, `quick` preset only): `gpt-5.4-mini` only — no in-vendor cheap-tier fallback at present; treat slot loss as degraded run
- **DeepSeek**: `deepseek-v4-pro` → `deepseek-v4-flash` → `deepseek-r1-0528`
- **Perplexity** (`research` preset only): `sonar-deep-research` → `sonar-pro-search`
- **xAI**: `grok-4.20` only — **no in-vendor fallback** (grok-4.1-fast retired). On failure, declare degraded run rather than cross-vendor swap. See "Vendor singletons" below.
- **Meta-Llama**: `llama-4-maverick` only — **no in-vendor fallback**. Same handling as xAI.

Report the substitution to the user — do not silently swap vendors. Vendor diversity is what the preset provides; a silent cross-vendor swap breaks that.

### Vendor singletons (xAI, Meta-Llama)

Two slots have no in-vendor fallback: the xAI slot in `brainstorm` and the Meta-Llama slot in `brainstorm`. If either fails:

1. Do **not** silently swap to a different vendor. The whole point of `brainstorm` is the divergent vendor mix.
2. Report the failure to the user explicitly.
3. Proceed with the remaining two models and flag in the return envelope's `confidence` field — e.g., `"medium, caveat: only 2/3 brainstorm models responded; xAI grok-4.20 returned 404"`.
4. If the user wants a third model anyway, they can explicitly request a cross-vendor swap as an override, which becomes a session decision logged in run metadata.

## Presets are authoritative at runtime

The preset rosters are **spec-level decisions**. At runtime, Claude-as-Nestor must use the exact models listed above for the chosen preset. Do not deviate based on reasoning about correlation, synthesizer overlap, redundancy, or any other optimisation target — even if the reasoning is internally consistent.

If you have an argument for changing a preset roster — for example, *"the synthesizer is Claude, so including Claude models in the roster correlates errors and should be swapped out"* — surface it to the user as a spec discussion. Do not act on it unilaterally. Runtime deviations break reproducibility across runs and make kill-criteria metrics noisy, and the judgment "this optimisation is safe" cannot be validated at runtime — only in design review.

If the full preset cannot respond because of infrastructure failure (model unavailable, timeout, parse error), that is the **degraded-run case** — flag the missing model in the return envelope's `confidence` field per the degraded-run handling described in Nestor SKILL.md Step 4. Do not pre-emptively deviate for optimisation reasons and label the result as a degraded run after the fact.

## Refresh history

- **2026-05-10** — model refresh against `pal listmodels`. Major changes:
  - Anthropic: `opus-4.6` → `opus-4.7` everywhere it appeared.
  - OpenAI: `gpt-5.4` → `gpt-5.5-pro` in `arch` and `research`. `gpt-5.3-codex` retained in `code` (no newer codex variant).
  - **DeepSeek added** as a new vendor — `deepseek-v4-pro` enters `brainstorm`, `deepseek-v4-flash` enters `quick`.
  - **Anthropic removed from `brainstorm` and `quick`** — design-review decision to eliminate the synthesizer-roster correlation that Claude-as-Nestor incorrectly attempted to make at runtime on 2026-04-05. The runtime decision was wrong; the design-review version (this refresh) is correct. See SKILL.md "Do NOT deviate from the preset model roster at runtime" anti-pattern for the historical context.
  - Fallback chains rewritten — purged stale references (`gpt-5.2`, `gpt-5.1-codex`, `claude-sonnet-4.6`, `grok-4.1-fast`); added DeepSeek and Perplexity chains; flagged xAI and Meta as vendor singletons with explicit degraded-run handling.
- **2026-04-05** — initial preset definition during Nestor Lite from-design-to-first-use session.
