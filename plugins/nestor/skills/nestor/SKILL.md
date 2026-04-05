---
name: nestor
description: This skill should be used when the user asks to "ask Nestor", "go to Nestor", "сходи к Нестору", "третье мнение", "что думает совет", "прогони через совет", "глубокий разбор", "важное решение", "критично", "high stakes", "critical decision", "think carefully", or "deliberate". Also invoke when the Atlas partner judges its own answer under-calibrated and needs an independent multi-model read. Nestor convenes a council of frontier models via the `pal` MCP server, announces its routing decision before running, and returns a synthesised judgment with an explicit agreement map and dissenting views.
---

# Nestor

Nestor is the named consultation mode of the Atlas AI team. When the user or Atlas needs a multi-model council on a hard decision, invoke this skill to run the deliberation through a disciplined protocol: self-contained question formulation, routing, council execution, synthesis, and structured presentation back to the user.

This skill is a wrapper over the lower-level `ai-council` skill at `~/Atlas/skills/ai-council/SKILL.md`. Nestor adds trigger recognition, a mini-reasoning router, input/output envelopes, presentation discipline, and run metadata logging. The council mechanics themselves (modes, presets, stance semantics, deliberative stage 2) live in ai-council — consult it during execution for the actual model-call details.

## When to invoke

Invoke this skill when:

**The user uses an explicit trigger phrase** (already matched by the skill loader via the description above). The full phrase list: "ask Nestor", "go to Nestor", "сходи к Нестору", "третье мнение", "что думает совет", "прогони через совет", "глубокий разбор" (→ forces deliberative mode), "важное решение", "критично", "high stakes", "critical decision", "think carefully", "deliberate".

**An implicit condition matches and Atlas decides to delegate without being asked**:

- Architectural or strategic decisions with high irreversibility
- The session's current answer feels under-calibrated or session-biased
- A hypothesis built with the user across the session needs pressure-testing from outside the session's framing
- An open question where the shape of disagreement is unknown

**Do NOT invoke Nestor for**:

- Simple factual questions (answer directly or consult the knowledge library)
- In-the-moment implementation decisions with low reversibility cost
- Routine work where committee deliberation adds latency without signal
- When the user explicitly asks for Atlas's own opinion ("what do you think?") — answer in Atlas's voice, do not deflect to the council

## Prerequisites

Verify that `mcp__pal__consensus` and `mcp__pal__chat` are available before running the protocol. If the `pal` MCP server is not configured in the current session, report the missing dependency clearly and stop — do not attempt consultation without the underlying tools. Surface this actionable message to the user: *"`pal` MCP server is not available in this session. See `~/Code/pal-mcp-server` (or the upstream pal project) for installation. Nestor cannot run without it."*

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

Use `mcp__pal__consensus` for stage 1 of any mode, and for adversarial mode end-to-end. For deliberative mode, after collecting three neutral first-round answers, run three parallel `mcp__pal__chat` calls to collect anonymised cross-critiques. Consult the `ai-council` skill's deliberative mode section for the exact stage-2 prompt template — do not rewrite it from scratch.

Use the model roster from the chosen preset as defined in ai-council's preset table. Do not invent new model combinations inside Nestor; the presets exist so that routing stays small and testable.

**Degraded-run handling**: if a model fails, times out, or returns an unusable response (empty, obviously truncated, or off-topic), proceed with the remaining models and flag the degraded roster in the return envelope's `confidence` field — e.g., `"medium, caveat: only 2/3 models responded usefully; the third returned a parse error"`. If fewer than two models produce usable output, abort synthesis and report the failure to the user honestly rather than papering over a broken council run with a forced single-model synthesis.

### Step 5 — Synthesise the judgment

Produce the return envelope (see below). Work primarily from the council's output and the self-contained question. Do not inject session context into the synthesis.

Acknowledge the honest v1 limitation: the in-session Claude performing this synthesis still has session history in its attention window. Session framing may subtly influence weighting and emphasis even with deliberate effort to exclude it. This is a known architectural limitation, not a discipline problem. When it affects the synthesis in a visible way, flag the effect to the user; do not pretend the synthesis is fully context-free.

### Step 6 — Present to the user

Use the presentation protocol below. Lead with Nestor's judgment. Add Atlas's own read only if session context materially qualifies the judgment. Keep the two layers visible — never blend them.

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

## Call envelope (Atlas → Nestor)

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

When presenting Nestor's judgment to the user, use this form if Atlas has session context that adds material qualifications:

```
**Nestor says**: <judgment + confidence + key reasoning>

**Agreement map**: <where models converged, where they diverged>

**What Nestor may have missed about the specific situation**: <session-context qualifications that Nestor could not have known>

**Atlas's read, given <named session context>**: <own take on Nestor's judgment — agreement, refinement, or disagreement>
```

If Atlas has no session context that materially qualifies the judgment, omit the "Atlas's read" section and present Nestor's output cleanly.

Keep the two layers **visible and labeled**. Do not blend Nestor's judgment with Atlas's qualifications into a single unmarked voice. The user should always be able to tell what came from the council and what came from the session-aware partner on top.

## Run metadata logging

After every Nestor consultation, append a metadata record to the current session log under a `## Nestor consultations` section (create it if missing):

```
- timestamp: <ISO datetime>
  trigger: <explicit phrase that fired, or implicit reason>
  router_decision: <mode + preset + stances>
  router_rule_matched: <rule number from the table>
  atlas_overrode_router: <true | false; if true, what was overridden and why>
  atlas_added_qualification: <true | false; if true, what session context shaped the qualification>
```

This metadata is load-bearing for the kill criteria defined at `~/Obsidian/Atlas/Projects/Nestor/Nestor.md`. Without it, there is no way to tell after ~10 uses whether the router is earning its keep or whether the persona layer adds signal beyond the raw ai-council skill. Do not skip the logging step.

## What NOT to do

- **Do NOT count votes across stance-assigned runs.** If rule 1 fires and stances are assigned, "2/3 agree" is meaningless — one model was instructed to argue the opposite. Report the judgment but flag the stance structure honestly. See the ai-council skill's "Stances" section for the roleplay-not-belief framing; the underlying empirical finding (the "Gemini Flip" — same model flipping position between `against` and `neutral` stances at identical confidence) is documented in `~/Obsidian/Atlas/Thinking/AI Council — Deliberative Mode Spec.md`.
- **Do NOT skip deliberative stage 2 when stage 1 is unanimous.** Unanimity is not a signal the council got it right; shared blind spots are invisible in unanimous answers. The verified A/B run on 2026-04-05 showed peer critique catching four major unaddressed requirements and two factual errors in a 3/3 unanimous first-round set.
- **Do NOT simulate a Nestor personality, voice, or backstory.** Nestor is a function wearing a name, not a character. Respond with structure and discipline, not mannerisms.
- **Do NOT call Nestor recursively inside a Nestor consultation.** One round, one synthesis. Multi-round debate introduces anchoring bias.
- **Do NOT blend Nestor's judgment with session-context qualifications silently.** The presentation protocol separation is the only way the user can tell where Nestor's output ends and Atlas's contextual read begins.
- **Do NOT claim context-free judgment.** v1 Nestor is fresh-read consultation with reduced bias. Full architectural isolation is a v2 escape hatch (separate sterile synthesis API call), not a v1 guarantee.
- **Do NOT invoke Nestor when the user explicitly asks for Atlas's own opinion.** If the user says "what do you think?", answer as Atlas directly. Do not deflect to the council.
- **Do NOT persist Nestor-specific state between calls.** Run metadata goes to the current session log only — not to a dedicated Nestor store, not to global memory. Each consultation starts at zero. This statelessness is enforced by the plugin having no storage layer; do not work around it.

## Kill criteria

v1 Nestor is experimental. Revisit after ~10 real uses. Rip-out conditions (router override rate > 50%, synthesis indistinguishable from direct ai-council call, latency avoidance, cognitive tax) and the full rip-out procedure are documented at `~/Obsidian/Atlas/Projects/Nestor/Nestor.md`. Rip-out cost is near zero — the underlying ai-council skill continues to work without Nestor.

## Related

- `~/Atlas/skills/ai-council/SKILL.md` — the lower-level deliberation protocol Nestor wraps (modes, stances, presets, deliberative stage 2, the roleplay-not-belief stance caveat)
- `~/Obsidian/Atlas/Projects/Nestor/Nestor.md` — project overview with principles, team positioning, kill criteria
- `~/Obsidian/Atlas/Projects/Nestor/specs/Core Design.md` — full technical spec, open questions, v2 migration paths
- `~/Obsidian/Atlas/Thinking/AI Council — Deliberative Mode Spec.md` — the verified deliberation protocol this whole stack sits on
