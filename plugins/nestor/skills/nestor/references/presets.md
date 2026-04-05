# Council Presets — Model Rosters and Fallbacks

Defines the five model rosters Nestor uses when routing a consultation. The `arch` / `code` / `research` / `brainstorm` / `quick` presets map to distinct frontier-model combinations optimised for different question shapes. Nestor's router selects the preset; this file defines what each preset actually contains.

## Preset table

| Preset | Routed to by | Models (use full OpenRouter IDs) | Rationale |
|---|---|---|---|
| `arch` | Router rule 1 (red-team) and rule 4 (exploratory) | `anthropic/claude-opus-4.6`, `google/gemini-3.1-pro-preview`, `openai/gpt-5.4` | Three frontier reasoners, different vendors — max diversity on complex decisions |
| `code` | Router rule 2 (technical decision with clear axis) | `openai/gpt-5.3-codex`, `google/gemini-3.1-pro-preview`, `anthropic/claude-opus-4.6` | Code-specialised + general reasoners |
| `research` | Router rule 3 (factual / research) | `perplexity/sonar-deep-research`, `google/gemini-2.5-pro`, `openai/gpt-5.4` | Perplexity for web grounding, plus two reasoners for interpretation |
| `brainstorm` | Not routed to by default; user must specify explicitly | `anthropic/claude-opus-4.5`, `x-ai/grok-4.20`, `meta-llama/llama-4-maverick` | Different "personalities" for unconventional angles |
| `quick` | Router rule 5 (low-stakes sanity check) | `google/gemini-2.5-flash`, `openai/gpt-5.4-mini`, `anthropic/claude-haiku-4.5` | Cheap and fast |

**Critical**: always use the full OpenRouter model IDs (e.g., `anthropic/claude-opus-4.6`), never short aliases like `opus`. The pal tool's built-in alias registry may not match these IDs, causing 404 errors.

## Fallback chains per vendor

If a model returns 404 or an error during a consensus run, substitute from the **same vendor** to preserve cross-provider diversity:

- **Anthropic**: `claude-opus-4.6` → `claude-opus-4.5` → `claude-sonnet-4.6`
- **Google**: `gemini-3.1-pro-preview` → `gemini-2.5-pro` → `gemini-2.5-flash`
- **OpenAI**: `gpt-5.4` → `gpt-5.2` → `gpt-5.1-codex`
- **xAI**: `grok-4.20` → `grok-4.1-fast`

Report the substitution to the user — do not silently swap vendors. Vendor diversity is what the preset provides; a silent cross-vendor swap breaks that.

## Presets are authoritative at runtime

The preset rosters are **spec-level decisions**. At runtime, Claude-as-Nestor must use the exact models listed above for the chosen preset. Do not deviate based on reasoning about correlation, synthesizer overlap, redundancy, or any other optimisation target — even if the reasoning is internally consistent.

If you have an argument for changing a preset roster — for example, *"the synthesizer is Claude, so including Claude models in the roster correlates errors and should be swapped out"* — surface it to the user as a spec discussion. Do not act on it unilaterally. Runtime deviations break reproducibility across runs and make kill-criteria metrics noisy, and the judgment "this optimisation is safe" cannot be validated at runtime — only in design review.

If the full preset cannot respond because of infrastructure failure (model unavailable, timeout, parse error), that is the **degraded-run case** — flag the missing model in the return envelope's `confidence` field per the degraded-run handling described in Nestor SKILL.md Step 4. Do not pre-emptively deviate for optimisation reasons and label the result as a degraded run after the fact.
