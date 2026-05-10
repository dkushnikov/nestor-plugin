---
name: nestor
description: This skill should be used when the user asks to "ask Nestor", "go to Nestor", "сходи к Нестору", "третье мнение", "что думает совет", "прогони через совет", "глубокий разбор", "важное решение", "критично", "high stakes", "critical decision", "think carefully", "deliberate", "council", "совет", "спросить модели", "second opinion", "что думают другие", "what does the council think", or mentions needing multi-model consultation. Also invoke when you judge your own answer under-calibrated and need an independent multi-model read. Nestor convenes a council of frontier models via the `pal` MCP server, announces its routing decision before running, and returns a synthesised judgment with an explicit agreement map and dissenting views.
---

# Nestor

Nestor is a named consultation mode for multi-model deliberation. When the user or the session needs a multi-model council on a hard decision, invoke this skill to run the deliberation through a disciplined protocol: self-contained question formulation, routing, council execution, synthesis, and structured presentation back to the user.

This skill is **self-contained**. The core protocol — triggers, router, envelopes, presentation, kill criteria — lives in this file. Detailed deliberation mechanics (preset model rosters, fallback chains, the `pal.consensus` step-by-step workflow, stance semantics with the Gemini Flip empirical finding, and the deliberative stage-2 cross-critique template) live in `references/` within this skill and are loaded on demand:

- `references/presets.md` — model rosters for `arch` / `code` / `research` / `brainstorm` / `quick` plus per-vendor fallback chains
- `references/consensus-execution.md` — `mcp__pal__consensus` step-by-step workflow, `continuation_id` handling, stepping discipline
- `references/stances-and-gemini-flip.md` — stance semantics (`for` / `against` / `neutral` as roleplay-not-belief) and the Gemini Flip finding
- `references/deliberative-stage-2.md` — cross-critique protocol, the verbatim critique prompt template, anti-patterns

## When to invoke

Invoke this skill when:

**The user uses an explicit trigger phrase** (already matched by the skill loader via the description above). The full phrase list: "ask Nestor", "go to Nestor", "сходи к Нестору", "третье мнение", "что думает совет", "прогони через совет", "глубокий разбор" (→ forces deliberative mode), "важное решение", "критично", "high stakes", "critical decision", "think carefully", "deliberate", "council", "совет", "спросить модели", "second opinion", "что думают другие", "what does the council think".

**An implicit condition matches and you decide to delegate without being asked**:

- Architectural or strategic decisions with high irreversibility
- The session's current answer feels under-calibrated or session-biased
- A hypothesis built with the user across the session needs pressure-testing from outside the session's framing
- An open question where the shape of disagreement is unknown

**Do NOT invoke Nestor for**:

- Simple factual questions (answer directly or consult the knowledge library)
- In-the-moment implementation decisions with low reversibility cost
- Routine work where committee deliberation adds latency without signal
- When the user explicitly asks for your own opinion ("what do you think?") — answer directly, do not deflect to the council

## Prerequisites

Verify that `mcp__pal__consensus` and `mcp__pal__chat` are available before running the protocol. If the `pal` MCP server is not configured in the current session, report the missing dependency clearly and stop — do not attempt consultation without the underlying tools. Surface this actionable message to the user: *"`pal` MCP server is not available in this session. Install it from [github.com/BeehiveInnovations/pal-mcp-server](https://github.com/BeehiveInnovations/pal-mcp-server). Nestor cannot run without it."*

## Core protocol

Execute these six steps in order for every Nestor consultation:

### Step 1 — Formulate a self-contained question

Translate the user's situation into a fully self-contained question. Every fact the council needs — user context, domain constraints, team size, prior decisions, named options — must be embedded in the question text. Session memory does not travel to the council.

**Example of under-specified vs self-contained**:

- Under-specified: *"Should I rewrite my CLI tool from Python to Go?"*
- Self-contained: *"I maintain a CLI tool, ~3k lines of Python, used daily by a team of 4 engineers. Performance is adequate; the pain points are dependency management and single-binary distribution. Should I rewrite in Go, or address packaging in-place with pipx / shiv / pyinstaller?"*

The under-specified version leaves the council guessing about the actual tradeoffs; the self-contained version lets it reason about the problem the user actually has.

If the user's situation lacks a required detail, ask the user first rather than guessing. A bad question produces a bad council output; the question-quality gate is the single most important step in the whole protocol.

### Step 2 — Route the question

Apply the router decision table below to select four outputs:

- `mode`: adversarial or deliberative
- `preset`: `arch` / `code` / `research` / `brainstorm` / `quick`
- `stances`: per-model assignment (default all-neutral)
- `question_framing`: the exact text sent to each council model

For rules 2–5, `question_framing` is simply the self-contained question from Step 1, passed through unchanged. For rule 1 (named hypothesis to red-team), `question_framing` additionally includes a per-model `stance_prompt` tuned to the specific hypothesis — e.g., one model receives "argue for <hypothesis>", another "argue against <hypothesis>", a third "argue from a skeptical neutral stance". The stance-specific framing is what makes adversarial mode sharp; do not pass the raw question to stance-assigned models and expect them to infer the attack angle.

Match rules in order; first match wins. If no rule matches with confidence, go to Step 3 with `status: needs_clarification` and return to the user for more context instead of guessing.

### Step 3 — Announce the routing before executing

Before running the council, state the routing decision aloud in this exact form:

```
Routing Nestor's consultation:
  Mode: <adversarial | deliberative>
  Preset: <arch | code | research | brainstorm | quick>
  Stances: <all-neutral | for/against/neutral>
  Rule matched: <which router rule fired and why>

Proceeding unless overridden.
```

This announcement is **mandatory**, not optional. It catches confident mis-routing before any tokens are burnt on the wrong configuration. The user can override at this moment.

### Step 4 — Run the council

Use `mcp__pal__consensus` for stage 1 of any mode, and for adversarial mode end-to-end. **Step through the entire consensus workflow with every model in the preset — the full preset roster is authoritative at runtime.** The step-by-step consensus workflow with the full roster is what makes "preset" mean something; it provides the reproducibility guarantee that kill-criteria tracking depends on.

For parameter-level details of the `mcp__pal__consensus` workflow (step numbers, `continuation_id` handling, per-step parameters), see `references/consensus-execution.md`. For the model roster and per-vendor fallback chains of the chosen preset, see `references/presets.md`. Do not invent new model combinations inside Nestor; the presets exist so that routing stays small and testable.

For deliberative mode, after collecting three neutral first-round answers via `mcp__pal__consensus`, run three parallel `mcp__pal__chat` calls to collect anonymised cross-critiques. The cross-critique protocol, the verbatim stage-2 prompt template, and the associated anti-patterns live in `references/deliberative-stage-2.md`. Use that template verbatim; do not improvise.

`mcp__pal__chat` is **only** for deliberative stage-2 cross-critique — never a substitute for `mcp__pal__consensus` in stage 1 or in adversarial mode.

**Degraded-run handling**: if a model fails, times out, or returns an unusable response (empty, obviously truncated, or off-topic) during a legitimate consensus run, proceed with the remaining models and flag the degraded roster in the return envelope's `confidence` field — e.g., `"medium, caveat: only 2/3 models responded usefully; the third returned a parse error"`. If fewer than two models produce usable output, abort synthesis and report the failure to the user honestly rather than papering over a broken council run with a forced single-model synthesis. Degraded handling is for **infrastructure failure**, not for pre-emptive optimisation — see the related "Do NOT deviate from the preset roster" anti-pattern below.

### Step 5 — Synthesise the judgment

Produce the return envelope (see below). Work primarily from the council's output and the self-contained question. Do not inject session context into the synthesis.

Acknowledge the honest v1 limitation: the in-session Claude performing this synthesis still has session history in its attention window. Session framing may subtly influence weighting and emphasis even with deliberate effort to exclude it. This is a known architectural limitation, not a discipline problem. When it affects the synthesis in a visible way, flag the effect to the user; do not pretend the synthesis is fully context-free.

### Step 6 — Present to the user

Use the presentation protocol below. Lead with Nestor's judgment. Add your own session-aware read only if session context materially qualifies the judgment. Keep the two layers visible — never blend them.

## The router

Match rules in order. First match wins. Rule 6 is the safe fallback when nothing else applies.

| # | Condition | Mode | Preset | Stances |
|---|---|---|---|---|
| 1 | Named hypothesis to red-team (user has a draft proposal and explicitly wants it attacked, or `reason_for_consulting` includes "red-team" / "pressure-test") | adversarial | arch | `for` / `against` / `neutral` with `stance_prompt` tuned to the hypothesis |
| 2 | Technical implementation decision with a clear axis (library, framework, algorithm, database choice between named options) | deliberative | code | all-neutral |
| 3 | Factual or research question requiring web-grounded verification ("what is true about", "verify", "market data") | deliberative | research | all-neutral |
| 4 | Exploratory or open-ended framing ("what am I missing", "what's the right framing", "how should I think about") | deliberative | arch | all-neutral |
| 5 | Low-stakes sanity check ("quick check", "is this reasonable", "obvious mistakes") | adversarial | quick | all-neutral |
| 6 | None of the above matches confidently | — | — | Return `status: needs_clarification` with a specific question; do not guess |

## Call envelope (session → Nestor)

The question passed to the council carries this logical shape, even when implemented as structured prose inside the `mcp__pal__consensus` call's `step` parameter:

```
question: <the fully self-contained question>
reason_for_consulting: <"third opinion" | "high stakes" | "red-team this hypothesis" | "exploratory, axis unknown">
hypothesis_being_tested: <optional; if rule 1 fires, the exact hypothesis the council attacks>
constraints: <optional; domain or implementation constraints the council should respect>
```

## Return envelope (Nestor → user)

After the council runs, structure the synthesis around these fields:

```
judgment: <Nestor's synthesised answer — what should be done or how the question should be framed>
confidence: <low | medium | high + brief reason>
agreement_map: <where models agreed, where they diverged, and on what dimension>
dissenting_view: <any substantive minority position, captured with its reasoning>
unaddressed_gaps: <what the question did not account for that the council noticed — a meta-signal back to the user>
```

## Presentation protocol

When presenting Nestor's judgment to the user, use this form if session context adds material qualifications:

```
**Nestor says**: <judgment + confidence + key reasoning>

**Agreement map**: <where models converged, where they diverged>

**What Nestor may have missed about the specific situation**: <session-context qualifications that Nestor could not have known>

**Session-aware read, given <named context>**: <your own take on Nestor's judgment — agreement, refinement, or disagreement>
```

If you have no session context that materially qualifies the judgment, omit the "Session-aware read" section and present Nestor's output cleanly.

Keep the two layers **visible and labeled**. Do not blend Nestor's judgment with session-context qualifications into a single unmarked voice. The user should always be able to tell what came from the council and what came from the session-aware layer on top.

## Run metadata logging

After every Nestor consultation, append a metadata record to the current session log under a `## Nestor consultations` section (create it if missing):

```
- timestamp: <ISO datetime>
  trigger: <explicit phrase that fired, or implicit reason>
  router_decision: <mode + preset + stances>
  router_rule_matched: <rule number from the table>
  session_overrode_router: <true | false; if true, what was overridden and why>
  session_added_qualification: <true | false; if true, what session context shaped the qualification>
```

This metadata is load-bearing for kill criteria. Without it, there is no way to tell after ~10 uses whether the router is earning its keep or whether the persona layer adds signal beyond direct `mcp__pal__consensus` calls without the Nestor wrapper. Do not skip the logging step.

## What NOT to do

- **Do NOT count votes across stance-assigned runs.** If rule 1 fires and stances are assigned, "2/3 agree" is meaningless — one model was instructed to argue the opposite. Report the judgment but flag the stance structure honestly. See `references/stances-and-gemini-flip.md` for the roleplay-not-belief framing and the Gemini Flip empirical finding (same model flipping position between `against` and `neutral` stances at identical confidence).
- **Do NOT skip deliberative stage 2 when stage 1 is unanimous.** Unanimity is not a signal the council got it right; shared blind spots are invisible in unanimous answers. The verified A/B run on 2026-04-05 showed peer critique catching four major unaddressed requirements and two factual errors in a 3/3 unanimous first-round set. See `references/deliberative-stage-2.md`.
- **Do NOT deviate from the preset model roster at runtime, even with defensible reasoning.** Observed on Nestor's first real-use run (2026-04-05, run #1): Claude-as-Nestor excluded `claude-haiku-4.5` from the `quick` preset based on a cross-provider correlation-avoidance argument — the reasoning was *"the synthesizer is Claude, so including Claude in the roster correlates errors; cross-provider pair gives more independent signal."* The argument is defensible in design review, but **unauthorised at runtime**. Preset rosters are spec-level decisions; if you have an argument for changing a roster, surface it to the user as a spec discussion, not a runtime override. Runtime deviation breaks reproducibility across runs, makes kill-criteria metrics noisy, and cannot be validated at the moment of deviation — only in design review. If the full preset cannot respond because of infrastructure failure (model unavailable, timeout, parse error), that is the **degraded-run case** in Step 4 — not a license for pre-emptive optimisation. *(Historical follow-up: on 2026-05-10 the same correlation-avoidance argument was raised again, this time properly in design review during a model-refresh session, and the synthesizer-correlated Anthropic slot was removed from both `quick` and `brainstorm` — see `references/presets.md` refresh history. The runtime decision was still wrong; the design-review decision was right. The rule holds: the path to a roster change is design review, not runtime.)*
- **Do NOT simulate a Nestor personality, voice, or backstory.** Nestor is a function wearing a name, not a character. Respond with structure and discipline, not mannerisms.
- **Do NOT call Nestor recursively inside a Nestor consultation.** One round, one synthesis. Multi-round debate introduces anchoring bias.
- **Do NOT blend Nestor's judgment with session-context qualifications silently.** The presentation protocol separation is the only way the user can tell where Nestor's output ends and the session-aware commentary begins.
- **Do NOT claim context-free judgment.** v1 Nestor is fresh-read consultation with reduced bias. Full architectural isolation is a v2 escape hatch (separate sterile synthesis API call), not a v1 guarantee.
- **Do NOT invoke Nestor when the user explicitly asks for your own opinion.** If the user says "what do you think?", answer directly. Do not deflect to the council.
- **Do NOT persist Nestor-specific state between calls.** Run metadata goes to the current session log only — not to a dedicated Nestor store, not to global memory. Each consultation starts at zero. This statelessness is enforced by the plugin having no storage layer; do not work around it.

## Kill criteria

v1 Nestor is experimental. Revisit after ~10 real uses. Rip-out conditions:

- **Router override rate > 50%** — the router is not earning its keep
- **Synthesis indistinguishable** from direct `mcp__pal__consensus` calls — the persona layer is theatre
- **Latency avoidance** — users start skipping Nestor because the overhead exceeds the value
- **Cognitive tax** — the named persona adds mental overhead rather than reducing it

Rip-out cost is near zero: delete the plugin. Preset rosters and protocol details are preserved in git history and `references/` files — they can be re-activated as a standalone skill without rebuilding from scratch.

## Related

**Within this plugin (progressive disclosure — load on demand):**
- `references/presets.md` — model rosters + per-vendor fallback chains
- `references/consensus-execution.md` — `mcp__pal__consensus` step-by-step workflow details
- `references/stances-and-gemini-flip.md` — stance semantics + Gemini Flip empirical finding
- `references/deliberative-stage-2.md` — cross-critique protocol + verbatim prompt template

**External:**
- [pal MCP server](https://github.com/BeehiveInnovations/pal-mcp-server) — the multi-model MCP server Nestor depends on
