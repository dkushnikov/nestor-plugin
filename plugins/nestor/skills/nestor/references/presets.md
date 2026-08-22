# Council Presets — Model Rosters and Fallbacks

Defines the five model rosters Nestor uses when routing a consultation. The `arch` / `code` / `research` / `brainstorm` / `quick` presets map to distinct frontier-model combinations optimised for different question shapes. Nestor's router selects the preset; this file defines what each preset actually contains.

Last refreshed: 2026-08-22 — see history note at bottom.

## Preset table

| Preset | Routed to by | Models (use full OpenRouter IDs) | Rationale |
|---|---|---|---|
| `arch` | Router rule 1 (red-team) and rule 4 (exploratory) | `openai/gpt-5.6-sol-pro`, `google/gemini-3.1-pro-preview`, `qwen/qwen3.7-max` | Three frontier reasoners from three distinct training lineages (OpenAI, Google, Alibaba), none from the synthesizer's lab — the Claude chair supplies the Anthropic perspective on top. Composition minimises correlated error with the chair (see Composition principle) |
| `code` | Router rule 2 (technical decision with clear axis) | `openai/gpt-5.6-sol`, `google/gemini-3.1-pro-preview`, `qwen/qwen3.7-max` | OpenAI's current coding flagship + Google frontier reasoner + Alibaba agent-centric flagship as the decorrelated third seat (kimi-k3 was stronger on coding benchmarks but failed the seat on delivery — see 2026-08-22 refresh). The Claude coding perspective is already in the room — the calling session runs Claude Code |
| `research` | Router rule 3 (factual / research) | `perplexity/sonar-deep-research`, `google/gemini-3.1-pro-preview`, `openai/gpt-5.6-sol-pro` | Perplexity for web grounding, plus two top-tier reasoners for interpretation |
| `brainstorm` | Not routed to by default; user must specify explicitly | `deepseek/deepseek-v4-pro`, `x-ai/grok-4.5`, `qwen/qwen3.7-max` | Maximally divergent vendor mix — two Chinese labs with different training cultures (DeepSeek MoE + Alibaba agent-centric) + SpaceXAI. No big-three Western lab member, by design. The synthesizer (Claude) supplies the Anthropic perspective on top |
| `quick` | Router rule 5 (low-stakes sanity check) | `google/gemini-3.5-flash-lite`, `openai/gpt-5.6-luna`, `deepseek/deepseek-v4-flash` | Three cheap-tier models, three different vendors, none correlated with the Anthropic synthesizer |

**Critical**: always use the full OpenRouter model IDs (e.g., `qwen/qwen3.7-max`), never short aliases like `qwen`. The pal tool's built-in alias registry is frozen at Dec 2025 and will not match these IDs, causing 404s or silent resolution to stale models.

## Composition principle

Three rules govern roster membership, in priority order:

1. **No synthesizer-family models.** The chair/synthesizer is a Claude (Fable 5 / Opus-class session). Anthropic models are excluded from every roster: the chair already contributes that perspective during synthesis, and a same-lab member maximises correlated error exactly where the council must be independent — pressure-testing hypotheses the Claude session itself built. This extends the 2026-05-10 design-review decision (which removed Anthropic from `brainstorm`/`quick`) to all presets.
2. **Compose by co-failure, not by headcount.** Ensemble gain tracks *low pairwise error overlap*, not member count or nominal diversity (arXiv 2607.20768: majority voting beat the strongest member in only ~10% of 3-model subsets; the only robust predictor of gain was low error overlap. arXiv 2606.27288: ensembles are capped by the simultaneous-failure rate, which naive estimates undercount ~2.5×). Prefer a slightly-weaker member from a distinct training lineage over a stronger one that fails together with the chair.
3. **Reliable delivery is a membership requirement.** All council traffic flows through OpenRouter; a member is only as good as the endpoint that answers. Prefer models served first-party (single vendor-owned endpoint pool). Open-weight models served by a broad third-party pool carry structural delivery risk: every call is a provider lottery — `moonshotai/kimi-k3` (15 endpoints, ~13 providers, one at 77% uptime with a 16k output cap) failed its `arch`/`code` seat on latency and empty responses despite frontier quality (see 2026-08-22 refresh). Before seating a member, check `openrouter.ai/api/v1/models/<id>/endpoints`.

**Rollback condition** (falsifiable, per kill-criteria discipline): review after ~10 `arch`/`code` runs on the current roster using the run-metadata records (`models_used` / `degraded` / `stage2` fields make this computable). Triggers: (a) the council repeatedly misses failure modes that session-side review then catches — restore `anthropic/claude-opus-5` to whichever preset(s) the misses occurred in (`arch`, `code`, or both); (b) degraded-run rate on a newly seated member exceeds ~2 of 10 runs — first fix the failing slot via its fallback chain, and only then reconsider composition. Either action is a design-review decision, logged in the refresh history. Condition (b) has fired once: kimi-k3, 2026-08-22 — the same-vendor fallback chain shared the failing delivery pool, so the chain remedy was exhausted and the seat was recomposed (qwen swap + rule 3 above).

## Fallback chains per vendor

If a model returns 404 or an error during a consensus run, substitute from the **same vendor** to preserve cross-provider diversity:

Chains are written with **full OpenRouter IDs** — the same rule as the preset table; a bare model name passed to pal falls through to its frozen alias registry and 404s or resolves stale.

- **OpenAI** (reasoning slots, `arch` / `research`): `openai/gpt-5.6-sol-pro` → `openai/gpt-5.6-sol` → `openai/gpt-5.5`
- **OpenAI** (code slot, `code` preset only): `openai/gpt-5.6-sol` → `openai/gpt-5.3-codex` → `openai/gpt-5.5` — codex kept as deliberate code-specialist fallback
- **OpenAI** (quick slot): `openai/gpt-5.6-luna` → `openai/gpt-5.4-mini`
- **Google**: `google/gemini-3.1-pro-preview` → `google/gemini-3.6-flash` → `google/gemini-3.5-flash-lite`; in `quick`, `google/gemini-3.5-flash-lite` → `google/gemini-3.1-flash-lite`
- **DeepSeek**: `deepseek/deepseek-v4-pro` → `deepseek/deepseek-v4-flash` → `deepseek/deepseek-v3.2`
- **Qwen** (`arch` / `code` / `brainstorm`): `qwen/qwen3.7-max` → `qwen/qwen3.7-plus` → `qwen/qwen3.6-max-preview` — all served first-party by Alibaba
- **xAI**: `x-ai/grok-4.5` → `x-ai/grok-4.3` → `x-ai/grok-4.20` — singleton status resolved 2026-07 (three live generations)
- **Perplexity** (`research` preset only): `perplexity/sonar-deep-research` → `perplexity/sonar-pro-search`

Report the substitution to the user — do not silently swap vendors. Vendor diversity is what the preset provides; a silent cross-vendor swap breaks that.

Removed vendors: **Anthropic** (no roster slots remain — the chair supplies the perspective; see Composition principle), **Meta** (no current open frontier: `llama-4-maverick` is 15 months stale, Muse Spark is proprietary, US-only and waitlisted), **Moonshot** (removed 2026-08-22 — OpenRouter delivery unreliability, not model quality; see refresh history. Kimi models remain in `pal-openrouter-models.json` for ad-hoc use).

### Vendor singletons

None in the current rosters — every vendor slot has an in-vendor fallback chain (Perplexity's is two-deep). If an entire vendor chain is exhausted during a run, that is the **degraded-run case**: do not cross-vendor swap; proceed with the remaining models and flag the roster degradation in the return envelope's `confidence` field per Nestor SKILL.md Step 4.

## Presets are authoritative at runtime

The preset rosters are **spec-level decisions**. At runtime, Claude-as-Nestor must use the exact models listed above for the chosen preset. Do not deviate based on reasoning about correlation, synthesizer overlap, redundancy, or any other optimisation target — even if the reasoning is internally consistent.

If you have an argument for changing a preset roster — for example, *"the synthesizer is Claude, so including Claude models in the roster correlates errors and should be swapped out"* — surface it to the user as a spec discussion. Do not act on it unilaterally. Runtime deviations break reproducibility across runs and make kill-criteria metrics noisy, and the judgment "this optimisation is safe" cannot be validated at runtime — only in design review.

If the full preset cannot respond because of infrastructure failure (model unavailable, timeout, parse error), that is the **degraded-run case** — flag the missing model in the return envelope's `confidence` field per the degraded-run handling described in Nestor SKILL.md Step 4. Do not pre-emptively deviate for optimisation reasons and label the result as a degraded run after the fact.

## Refresh history

- **2026-08-22** — Moonshot seat replaced on delivery-reliability evidence (v0.4.0). Rollback condition (b) fired for `moonshotai/kimi-k3` (seated 2026-07-29). Evidence from the `pal-calls.jsonl` audit hook, August `arch`/`code` runs: the kimi consensus step exceeded the 120s MCP foreground window in **12 of 15 runs** (control: 2026-08-21 run with kimi as step 1 — the timeout moved with the model, not the step position); direct `pal.chat` calls **1 clean success of 7** (5 timeouts >120s, 1 «Response blocked or incomplete. Finish reason: stop» = empty content); same-vendor fallback `kimi-k2.6` exceeded the window **2 of 2** times — the whole Moonshot chain shares one delivery pool, so the "fix via fallback chain" remedy was exhausted. Peers on identical prompts: sol-pro 25–60s, gemini 24–47s, no anomalies. Mechanism is delivery, not model: OpenRouter served kimi-k3 via 15 endpoints from ~13 third-party providers of wildly varying quality (worst: status −5, 77% uptime, 16,384-token output cap — a truncated reasoning chain returns finish=stop with empty content); kimi answers that did land were full-weight. Endpoint data: OpenRouter endpoints API, 2026-08-22.
  - **`arch`/`code`: `moonshotai/kimi-k3` → `qwen/qwen3.7-max`.** Chosen over `x-ai/grok-4.5` (stronger on paper and 4 first-party endpoints, but the roster would become all-Western — rule 2 prioritises lineage decorrelation over headline capability) and over `deepseek/deepseek-v4-pro` (17-endpoint mixed pool — same structural risk that just failed). Qwen 3.7 Max: single Alibaba first-party endpoint (100% uptime at decision time), extended thinking, non-Western training lineage preserved, already vetted in `brainstorm`. Cross-preset overlap is precedented (`gemini-3.1-pro-preview` serves three presets).
  - **Composition rule 3 added** — reliable delivery is a membership requirement; endpoints checked before seating.
  - **Moonshot removed from rosters and fallback chains**; kimi models stay in `pal-openrouter-models.json` for ad-hoc use. Decision: Dima, 2026-08-22.
- **2026-07-29** — full generational refresh + composition change (v0.3.0). Context: the synthesizer is now Claude Fable 5, and Chinese open-weights reached the frontier (Kimi K3: #3 GDPval-AA Elo behind only Fable 5 and GPT-5.6 Sol, above Fable 5 on Terminal-Bench 2.1, #1 Arena Frontend Code; Chinese models ≈46% of OpenRouter tokens vs ~4.5% a year earlier).
  - **Anthropic removed from `arch`/`code`** (was `claude-opus-4.7`) → `moonshotai/kimi-k3` enters both. Completes the synthesizer-decorrelation that the 2026-05-10 review started with `brainstorm`/`quick`. Counterargument considered honestly: Opus 5 (released 2026-07-24, ≈Fable-level) is likely stronger than K3 in raw capability, and a cold Anthropic read is not identical to the session-contaminated chair — but the marginal value of a council member is the *independent* signal it adds to a room that already contains a Claude chair, and co-failure evidence (see Composition principle) says the decorrelated member wins. Rollback condition documented above.
  - OpenAI: `gpt-5.5-pro` → `gpt-5.6-sol-pro` in `arch`/`research` (GPT-5.6 family released 2026-07-09; Sol Pro is the reasoning flagship at $5/$30 vs 5.5-pro's $30/$180 — 6× cheaper). `code` slot `gpt-5.3-codex` → `gpt-5.6-sol` (OpenAI positions Sol as its best coding model; no newer codex-branded variant exists — codex kept as first fallback). `quick`: `gpt-5.4-mini` → `gpt-5.6-luna` (newer generation, cheaper).
  - xAI: `grok-4.20` → `grok-4.5` (2026-07-08, #4 on AA Intelligence Index, ~3.8× more token-efficient). Vendor singleton resolved — chain now three-deep. Corporate note: xAI acquired by SpaceX (rebranded SpaceXAI 2026-07); `x-ai/` prefix unchanged on OpenRouter.
  - **Meta removed** — `llama-4-maverick` (2025-04) has no successor; Muse Spark 1.1 is proprietary/US-only/waitlisted. `qwen/qwen3.7-max` (Alibaba flagship, 2026-05-21) takes the brainstorm slot; brainstorm mix is now DeepSeek + SpaceXAI + Alibaba.
  - Google: pro tier **unchanged** — Gemini 3.5 Pro still unreleased (delayed past June over coding performance), `gemini-3.1-pro-preview` remains Google's top text model. `quick` slot `gemini-3.1-flash-lite` → `gemini-3.5-flash-lite` (2026-07-21); fallback chain refreshed to `gemini-3.6-flash` era.
  - Perplexity unchanged — `sonar-deep-research` still the deep-research specialist; `sonar-pro-search` (agentic interactive search) as fallback.
  - All primary-roster and fallback IDs verified against the OpenRouter models API on 2026-07-29.
- **2026-05-24** — Google generational refresh + redeploy. The 2026-05-10 v0.2.0 refresh had never been deployed (source was v0.2.0, installed cache was still v0.1.0); this pass corrects the drift and reinstalls. Gemini 3.5 Flash (GA 2026-05-19) and Gemini 3.1 Flash-Lite (GA 2026-05-07) both postdate v0.2.0:
  - `quick`: Google slot `gemini-2.5-flash` → `gemini-3.1-flash-lite` (current cheap/efficiency tier).
  - Google fallback chain refreshed to current generation — `gemini-3.1-pro-preview` → `gemini-3.5-flash` → `gemini-3.1-flash-lite`; purged stale `gemini-2.5-pro` / `gemini-2.5-flash`.
  - `arch` / `code` / `research` / `brainstorm` unchanged — all rosters verified current against OpenRouter on 2026-05-24.
- **2026-05-10** — model refresh against `pal listmodels`. Major changes:
  - Anthropic: `opus-4.6` → `opus-4.7` everywhere it appeared.
  - OpenAI: `gpt-5.4` → `gpt-5.5-pro` in `arch` and `research`. `gpt-5.3-codex` retained in `code` (no newer codex variant).
  - **DeepSeek added** as a new vendor — `deepseek-v4-pro` enters `brainstorm`, `deepseek-v4-flash` enters `quick`.
  - **Anthropic removed from `brainstorm` and `quick`** — design-review decision to eliminate the synthesizer-roster correlation that Claude-as-Nestor incorrectly attempted to make at runtime on 2026-04-05. The runtime decision was wrong; the design-review version (this refresh) is correct. See SKILL.md "Do NOT deviate from the preset model roster at runtime" anti-pattern for the historical context.
  - Fallback chains rewritten — purged stale references (`gpt-5.2`, `gpt-5.1-codex`, `claude-sonnet-4.6`, `grok-4.1-fast`); added DeepSeek and Perplexity chains; flagged xAI and Meta as vendor singletons with explicit degraded-run handling.
- **2026-04-05** — initial preset definition during Nestor Lite from-design-to-first-use session.
