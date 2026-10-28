---
name: nestor
description: 'Consult Nestor / Нестор for a second opinion or third opinion from other frontier models: "what does the council think" / "что думает совет". Excludes the calling agent''s own opinion, factual lookups, and routine work.'
---

# Nestor

Nestor is a named consultation mode for multi-model deliberation. When the user or the session needs a multi-model council on a hard decision, invoke this skill to run the deliberation through a disciplined protocol: self-contained question formulation, routing, council execution, synthesis, and structured presentation back to the user.

This skill is **self-contained**. The core protocol — triggers, router, envelopes, presentation, kill criteria — lives in this file. Detailed deliberation mechanics (preset model rosters, fallback chains, the `pal.consensus` step-by-step workflow, stance semantics with the Gemini Flip empirical finding, and the deliberative stage-2 cross-critique template) live in `references/` within this skill and are loaded on demand:

- `references/router-cases.md` — eleven acceptance cases for routing, explicit field inheritance and the invariant check
- `references/presets.md` — model rosters for `arch` / `code` / `research` / `brainstorm` / `quick` plus per-vendor fallback chains
- `references/consensus-execution.md` — `mcp__pal__consensus` step-by-step workflow, `continuation_id` handling, stepping discipline
- `references/stances-and-gemini-flip.md` — stance semantics (`for` / `against` / `neutral` as roleplay-not-belief) and the Gemini Flip finding
- `references/deliberative-stage-2.md` — cross-critique protocol, the verbatim critique prompt template, anti-patterns
- `references/setup.md` — what the host must provide: pal install, process topology, metadata sink, background delivery, redeploy
- `references/openrouter-models.example.json` — pal model registry for every preset and fallback id (context windows); a roster refresh updates it too, `tests/test_doc_links.py` checks the coverage

## When to invoke

Invoke this skill when:

**The user explicitly addresses Nestor or asks for other models' opinion** — what the skill loader matches through the description above. Phrases of this kind: "ask Nestor", "go to Nestor", "сходи к Нестору", "спроси Нестора", "Nestor, …" followed by a question, "третье мнение", "second opinion", "что думает совет", "what does the council think", "прогони через совет", "спросить модели", "что думают другие" — and anything equivalent in meaning. Mode words inside such a request ("глубокий разбор" / "deliberate" → deliberative) and a *named* preset ("Nestor quick:", "Nestor brainstorm") steer the router (rule 0; "quick check" alone is rule 5's shape wording, not a preset — see §The router); on their own they are not an invocation. Importance or urgency markers — "критично", "важное решение", "high stakes", "critical decision", "think carefully" — are **not** instructions to convene the council: they are context for the implicit decision below, and must never be recorded in run metadata as an explicit trigger the user did not give.

**An implicit condition matches and you decide to delegate without being asked**:

- Architectural or strategic decisions with high irreversibility
- The session's current answer feels under-calibrated or session-biased
- A hypothesis built with the user across the session needs pressure-testing from outside the session's framing
- An open question where the shape of disagreement is unknown

The importance and irreversibility of the decision weigh into this judgment (that is where "critical" and "high stakes" belong); the recorded `trigger` is then `implicit: <reason>`. This is the session's own decision under the host's policy — it needs no confirmation gate, and it is not a licence to consult on routine work because the user called it urgent.

**Do NOT invoke Nestor for**:

- Simple factual questions (answer directly or consult the knowledge library)
- In-the-moment implementation decisions with low reversibility cost
- Routine work where committee deliberation adds latency without signal
- When the user explicitly asks for your own opinion ("what do you think?") — answer directly, do not deflect to the council

## Prerequisites

Verify that `mcp__pal__consensus` and `mcp__pal__chat` are available before running the protocol. If the `pal` MCP server is not configured in the current session, report the missing dependency clearly and stop — do not attempt consultation without the underlying tools. Tell the user: *"`pal` MCP server is not available in this session; Nestor cannot run without it. Install per `references/setup.md` (pinned release or the citations fork, OpenRouter key in the server env, plus a model registry before any consultation that sends files)."* The host must also provide a place for the run metadata record (Step 6 logging); without one, return the record inline marked `not persisted`.

## Core protocol

Execute these six steps in order for every Nestor consultation:

### Step 1 — Formulate a self-contained question

Translate the user's situation into a fully self-contained question. Every fact the council needs — user context, domain constraints, team size, prior decisions, named options — must be embedded in the question text. Session memory does not travel to the council.

**Example of under-specified vs self-contained**:

- Under-specified: *"Should I rewrite my CLI tool from Python to Go?"*
- Self-contained: *"I maintain a CLI tool, ~3k lines of Python, used daily by a team of 4 engineers. Performance is adequate; the pain points are dependency management and single-binary distribution. Should I rewrite in Go, or address packaging in-place with pipx / shiv / pyinstaller?"*

The under-specified version leaves the council guessing about the actual tradeoffs; the self-contained version lets it reason about the problem the user actually has.

Before routing, verify the question against the **question gate** — five checks, each either satisfied or explicitly not applicable:

1. **Self-contained** — every fact the council needs is in the text (as above).
2. **Estate inventory** — existing systems, specs, tools, and prior decisions that bear on the question are named, or `no applicable estate`. This is the #1 source of post-hoc session corrections: the council cannot know what already exists (52-run retro 2026-08-22: ~20 of 43 session qualifications supplied estate the question omitted).
3. **Scope bounds** — what is in and out of scope (layers, components, already-settled decisions) is stated. An unbounded round-2 question caused the council to re-attack settled design (2026-06-15).
4. **Neutral framing** — the question carries the *proposition or artifact under test* plus decision-relevant facts; it never carries the asker's ownership, preference, confidence, or desired verdict. This holds in EVERY mode — adversarial red-team needs the hypothesis, not "I believe X" — and at every stage: initial prompt, stage-2 critique inputs, round-2 state packets, any search queries, the synthesis. Origin: 2026-06-17 sycophancy incident — stage-2 flipped stage-1 answers that had absorbed the asker's stated leaning.
5. **Privacy pass** — content from privacy-scoped domains travels as an anonymized structural form (no names, no identifying numbers), and the anonymized form must still carry the decision-relevant specifics — over-anonymization that produces generic advice fails the check too. Precedent: 2026-06-07 (company model sent anonymized; findings translated back locally).

If a check fails AND the missing piece would change the routing or materially change the answer, stop and return `needs_clarification` with the specific question (rule 6 shape) instead of running the council. Minor gaps that would not change the outcome are noted, not blocking. A bad question produces a bad council output; this gate is the single most important step in the whole protocol.

**Round-2 consultations** (a follow-up council on the same topic after changes) inherit nothing — the council is stateless. Build the question as a **state packet**: (1) the original neutral question; (2) scope bounds and estate, restated fresh; (3) points settled since round 1, each with its rationale; (4) points still open; (5) what changed — new evidence, revisions made; (6) the delta question for this round. State the reopening rule explicitly: *settled points may be challenged only on new evidence, an internal contradiction, or a material unstated assumption.* The packet stays neutral — never "the user liked answer B" or "we now lean toward X". Without this, round-2 councils re-attack settled points (observed 2026-06-14/15).

### Step 2 — Route the question

Apply the router decision table below to select four outputs:

- `mode`: adversarial or deliberative
- `preset`: `arch` / `code` / `research` / `brainstorm` / `quick`
- `stances`: per-model assignment (default all-neutral)
- `question_framing`: the exact text sent to each council model

For base rules 2–5, `question_framing` is simply the self-contained question from Step 1, passed through unchanged; for rule-2 artifact reviews, append the review dimensions (correctness, omissions, risks, strengths, recommended changes) so the council reviews against criteria rather than inventing stances. Whenever the final route is adversarial with `for` / `against` / `neutral` stances — base rule 1, or rule 0 assigning roles explicitly over an adversarial route — `question_framing` additionally includes a per-model `stance_prompt` tuned to the specific hypothesis — e.g., one model receives "argue for <hypothesis>", another "argue against <hypothesis>", a third "argue from a skeptical neutral stance". An explicit `all-neutral` override removes these opposing stance prompts; use the self-contained question without assigned advocacy. The stance prompts carry the *proposition*, never the asker's ownership or preference (question-gate check 4). The distinction that picks between rules 1 and 2: red-team MY POSITION → base rule 1 with stances; review THIS ARTIFACT → base rule 2, neutral, criteria-based. Rule 0 then overlays only the explicitly requested fields. Sessions previously disambiguated this manually (52-run retro: artifact reviews wobbled between rules 1 and 4); the router now owns it.

Determine the base route from rules 1–5 in order, then overlay rule 0 as described below. If no base rule matches with confidence, go to Step 3 with `status: needs_clarification` and return to the user for more context instead of guessing.

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

If Step 1 or Step 2 ended in `status: needs_clarification`, there is no routing to announce: return the clarification question instead of this block.

This announcement is **mandatory**, not optional — and it is a *notification before execution*, not an intervention window. Because the session cannot tell whether its intermediate output is shown (a non-interactive `claude -p` run or a bot turn surfaces only the final answer), the final presentation **always** opens with one route line — `Route: <mode> · <preset> · <stances> · rule <base>[ + 0: <overlaid fields>]` — before the judgment; the pre-execution block stays as it is, and the route is never reported only inside the run-metadata record (observed omission on a clean-host `-p` run, 2026-10-28). Printing it does not pause the session and adds no approval gate; it makes confident mis-routing visible and overridable (the user can override in their next message, and a mis-routed run can be re-routed and re-run). The session actually waits before executing only where the host's permission rules require it, where the user has asked to confirm before council calls, or where the question gate returns `needs_clarification`.

### Step 4 — Run the council

Use `mcp__pal__consensus` for stage 1 of any mode, and for adversarial mode end-to-end. **Step through the entire consensus workflow with every model in the preset — the full preset roster is authoritative at runtime.** The step-by-step consensus workflow with the full roster is what makes "preset" mean something; it provides the reproducibility guarantee that kill-criteria tracking depends on.

For parameter-level details of the `mcp__pal__consensus` workflow (step numbers, `continuation_id` handling, per-step parameters), see `references/consensus-execution.md`. For the model roster and per-vendor fallback chains of the chosen preset, see `references/presets.md`. Do not invent new model combinations inside Nestor; the presets exist so that routing stays small and testable.

**One consensus workflow at a time.** pal keeps the workflow state on one tool instance per server process, and one process serves the whole session (subagents included); a second step 1 overwrites the first workflow's roster and question. Finish steps 1 → N before starting another consultation; parallel consultations belong in separate sessions. If a step reports a model or question that is not yours, stop and re-run the workflow from step 1 — never splice answers across workflows. Details and the 2026-10-05 incident: `references/consensus-execution.md`.

For deliberative mode, after collecting three neutral first-round answers via `mcp__pal__consensus`, run three parallel `mcp__pal__chat` calls to collect anonymised cross-critiques — each critic receives the **same file packet** stage 1 received (`absolute_file_paths`), nothing more. The cross-critique protocol, the verbatim stage-2 prompt template, and the associated anti-patterns live in `references/deliberative-stage-2.md`. Use that template verbatim; do not improvise.

`mcp__pal__chat` is for deliberative stage-2 cross-critique and for **seat restoration** (below) — never a substitute for `mcp__pal__consensus` as the way to run stage 1 or adversarial mode.

**Degraded-run handling.** A seat has produced a *usable* answer when pal reports `status: success` with non-empty, on-topic content; pal appends failed seats to the workflow as `status: error` and keeps going, so count usable answers, not `total_responses`. A seat cannot be replaced inside a running workflow (pal reads the roster at step 1 only). Finish the workflow, then:

- **3 usable** → normal run.
- **2 usable** → proceed as a *partial-roster* run, by mode. **Deliberative:** synthesis from two answers plus two critiques — the two surviving seats critique each other (each critic receives the other's answer as `Response A` only, with the same evidence packet; protocol in `references/deliberative-stage-2.md` §Partial roster); `stage2: partial-roster` requires both critiques to be usable, with fewer the run is labelled `stage2: stage-1-only`. **Adversarial:** synthesis from the two stage-1 answers (stance-assigned or neutral, as routed), **no critique calls** (adversarial has no stage 2, and stance-assigned answers never enter peer critique), `stage2: skipped-adversarial`. In both modes name the gap in the return envelope's `confidence` — e.g., `"medium, caveat: 2/3 seats usable; the Google seat returned a parse error"`.
- **fewer than 2 usable** → abort synthesis and report the failure honestly rather than papering over a broken council run with a forced single-model synthesis.

**Seat restoration** (decision 2026-10-28) — **this paragraph is the authoritative restoration policy**; `references/consensus-execution.md`, `references/presets.md` and `references/deliberative-stage-2.md` refer to it and add no attempts. Before applying the 3/2/<2 rule, try to restore each failed seat **once**: finish the consensus workflow first, then issue one `mcp__pal__chat` to the seat's first same-vendor fallback from `presets.md` with the **identical step-1 packet** — the same question text, the same `relevant_files` as `absolute_file_paths`, the same stance (for a stance-assigned seat, prepend the same stance instruction the consensus step carried; for neutral seats, none). The user-side packet is identical; the system framing is not — pal runs `chat` under its chat prompt, not the consensus prompt that wraps a seat's stance. Record this in `notes` of the run metadata. The restored answer takes that seat's place — it is the seat's stage-1 answer, not a fourth voice; in deliberative mode it enters stage 2 like any other, in adversarial mode it is simply that seat's stage-1 answer (stance-assigned or neutral, as routed) and no stage 2 follows. One attempt per seat, and only the first fallback: the longer per-vendor chains in `presets.md` are design-review material for the next refresh, not further runtime attempts. If the fallback also fails, the seat stays empty and the rule above applies. This single attempt is separate from the stage-2 limit of one same-vendor retry per failed critic (`references/deliberative-stage-2.md`) — with one coupling: a critic that is itself a restoration fallback gets **no** retry, because its vendor's one runtime fallback is already in use and the chain is never walked deeper; the run proceeds without that critique. Record it as `degraded: <seat> failed (<reason>) → restored via chat: <fallback id>` and list the fallback in `models_used`. Restarting the whole workflow is not the remedy (it re-bills the healthy seats and still cannot swap models mid-run). A seat delivered from the background after the host's ~120 s window is **not** degraded — wait for the task result, continue, and list the seat in the `background` metadata field. Degraded handling is for **infrastructure failure**, not for pre-emptive optimisation — see the related "Do NOT deviate from the preset roster" anti-pattern below.

### Step 5 — Synthesise the judgment

Produce the return envelope (see below). Work primarily from the council's output and the self-contained question. Do not inject session context into the synthesis.

Acknowledge the honest v1 limitation: the calling session performing this synthesis still has session history in its attention window. Session framing may subtly influence weighting and emphasis even with deliberate effort to exclude it. This is a known architectural limitation, not a discipline problem. When it affects the synthesis in a visible way, flag the effect to the user; do not pretend the synthesis is fully context-free.

### Step 6 — Present to the user

Use the presentation protocol below. Open with the one-line route (Step 3), then lead with Nestor's judgment. Add your own session-aware read only if session context materially qualifies the judgment. Keep the two layers visible — never blend them.

## The router

Route in three steps:

1. Determine the **base route** by the question's shape: match rules 1–5 in order; the first match supplies `mode`, `preset`, and `stances`. If none matches confidently, use rule 6.
2. Apply **rule 0** as a field-by-field overlay: replace only the `mode`, `preset`, or `stances` the user explicitly requested. A preset is explicit only when its *name* is given ("Nestor quick:", "via the quick preset", "Nestor brainstorm"); "quick check" alone is rule 5's shape wording, not a preset override — the two coincide on `quick`, so the reading changes nothing there, but "quick check this API spec" is a rule-2 review, not a `quick`-preset run. Inherit every unnamed field from the base route. An explicit mode alone inherits the base preset; an explicit preset alone inherits the base mode. Explicit `all-neutral` beats rule 1's `for` / `against` / `neutral` default. "Red-team this" is a shape trigger for rule 1, not a mode override.
3. **Check the invariants of the overlaid result** — a compatibility check on the four outputs, not another priority rule:
   - *Deliberative requires all-neutral stage 1.* If `mode` is deliberative and the stances are `for` / `against` / `neutral` only because they were **inherited** from the base route (rule 1's red-team shape plus an explicit deliberative override), normalise the stances to all-neutral, remove every per-model `stance_prompt` from `question_framing` (the self-contained question travels without assigned advocacy — check the final framing text, not just the field value), and name the normalisation in the announcement: `Stances: all-neutral (normalised — deliberative stage 1 is neutral; rule 1's advocacy prompts dropped)`.
   - If the user **explicitly** asked for `for` / `against` / `neutral` stances and the mode is deliberative — whether the user named deliberative too, or the base route (rules 2–4) supplied it — return `status: needs_clarification` before any model call, with the concrete choice: *a neutral deliberative consultation* (three neutral answers, then anonymised peer critique) or *an adversarial check with assigned roles* (one stance-assigned round, no stage 2). Role stances exist only in adversarial mode; do not run an undefined hybrid.
   - *Adversarial + all-neutral* is valid — the `quick` preset's normal shape (rule 5) and case 8.
   - A mode-only override changes `mode` and only what that mode's invariants require; preset, review dimensions and the question text are inherited unchanged.

When announcing the matched rule, identify the base rule and any rule-0 fields that changed it; an explicit field that already agrees with the base route leaves that route unchanged.

| # | Condition | Mode | Preset | Stances |
|---|---|---|---|---|
| 0 | Explicit user override — the user names a preset («Nestor brainstorm: …», "quick check via the quick preset"), a mode («глубокий разбор» → deliberative), or stances ("all stances neutral") | explicit mode, else base mode | explicit preset, else base preset | explicit stances, else base stances |
| 1 | Position red-team — the user OWNS a position or hypothesis and wants it attacked ("red-team this", "pressure-test my position") | adversarial | arch | `for` / `against` / `neutral` with `stance_prompt` tuned to the hypothesis; the proposition travels, the asker's ownership and preference do not |
| 2 | Technical operation on an artifact or options — review a drafted artifact (spec, design doc, API, schema, plan, typology) against requirements and constraints with the author's position withheld, OR compare/select among named technical approaches | deliberative | `code` if the artifact/decision is implementation-bound (spec, API, schema, tooling), else `arch` | all-neutral; for artifact review use review dimensions (correctness, omissions, risks, strengths, recommended changes), not stances |
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
assumptions: <the 1–3 premises the judgment stands on — facts taken from the question as true, or inferences the council shared>
agreement_map: <where models agreed, where they diverged, and on what dimension>
dissenting_view: <any substantive minority position, captured with its reasoning; tag the crux type — fact | inference | value | constraint — because the type decides what check would settle it>
would_flip: <the evidence or condition that would reverse the judgment — what to watch for after deciding>
next_check: <the single most informative verification to run before or right after acting, derived from the dissent's crux type; "none" is a valid answer>
unaddressed_gaps: <what the question did not account for that the council noticed — a meta-signal back to the user>
```

`assumptions`, `would_flip` and `next_check` exist so that a week later the *reasons* for a decision can be reconstructed from the record alone, not only its verdict (added v0.7.0; trial — see kill criteria). Keep them short; a templated "no assumptions" is a failed field, not a filled one.

## Presentation protocol

When presenting Nestor's judgment to the user, use this form if session context adds material qualifications:

```
Route: <mode> · <preset> · <stances> · rule <base>[ + 0: <overlaid fields>]

**Nestor says**: <judgment + confidence + key reasoning>

**Agreement map**: <where models converged, where they diverged>

**What Nestor may have missed about the specific situation**: <session-context qualifications that Nestor could not have known>

**Session-aware read, given <named context>**: <your own take on Nestor's judgment — agreement, refinement, or disagreement>
```

If you have no session context that materially qualifies the judgment, omit the "Session-aware read" section and present Nestor's output cleanly.

Keep the two layers **visible and labeled**. Do not blend Nestor's judgment with session-context qualifications into a single unmarked voice. The user should always be able to tell what came from the council and what came from the session-aware layer on top.

## Run metadata logging

After every Nestor consultation, append a metadata record to the current session log under a `## Nestor consultations` section (create the *section* if missing — never the sink itself: a host without a session log gets the record inline, marked `not persisted`, per Prerequisites):

```
- timestamp: <ISO datetime; a host that exposes no clock gets the ISO date, and `host clock unavailable` is appended to `notes` — never an invented time>
  trigger: <explicit phrase that fired, or implicit reason>
  router_decision: <mode + preset + stances>
  router_rule_matched: <rule number from the table>
  models_used: <the models that actually answered, after any fallback substitutions>
  degraded: <false | which slot failed and what was substituted or dropped — write exactly `false` when the run was clean; never append comments after `false` (the analytics sweep parses this field mechanically)>
  stage2: <run | partial (N/3 critiques) | partial-roster | stage-1-only | skipped-adversarial | n/a — `skipped-adversarial` for every adversarial run that reached synthesis (clean or degraded; stage 2 never runs there), `n/a` for any run of either mode that produced no synthesis (fewer than 2 usable answers, or aborted before the workflow finished)>
  background: <none | the seats whose stage-1 step or stage-2 critique was delivered from the host's background after the ~120 s window, e.g. `kimi (step 3, critique)` — delivery cost, not a degradation>
  outcome: <pending | one line: the council's verdict AND what the session/user did with it — recommendation ≠ decision, record both; when a `pending` outcome resolves later in the session, update the record>
  notes: <optional free-text anomalies — double answers, retries that succeeded; anything worth recording that is NOT a degradation>
  session_overrode_router: <true | false; if true, what was overridden and why>
  session_added_qualification: <true | false; if true, what session context shaped the qualification>
  qualification_kind: <none | estate-missed | estate-withheld | new-evidence | mixed — see below>
```

`qualification_kind` classifies *why* the session had to qualify the council's answer (v0.7.0, P9 of the 2026-10-27 review): `estate-missed` — something that already existed (tool, decision, constraint) was left out of the question and could have been included; `estate-withheld` — it was left out on purpose by the privacy pass (anonymised packet) and translated back locally; `new-evidence` — the session held evidence the council could not inspect (files, live systems, verbatim sources); `mixed` when several apply, naming the dominant one. Only `estate-missed` is the question gate's failure; the previous single boolean conflated the three and made the gate unmeasurable (29-run review: 16 "estate-shaped" qualifications of which ~9 were deliberate withholding).

The `models_used` / `degraded` / `stage2` / `outcome` fields exist so the kill criteria and the roster rollback condition are computable from the records themselves — without them, degraded-run rate, fallback frequency, and recommendation-acceptance are invisible to later analytics.

**Core stays parseable.** The fields above are machine-read by the analytics sweep — fill every one, in the template's `key: value` shape, even when the run was unusual. Rich observations, meta-findings, and stories go into `notes` (or prose OUTSIDE the record) — never replace the structured core with free-form text. The three free-form records of 2026-06-17 carried the thread's most valuable findings and broke the sweep at the same time; the lesson is both/and, not either/or.

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
- **Do NOT persist Nestor-specific state between calls.** Run metadata goes to the current session log only — not to a dedicated Nestor store, not to global memory. Each consultation starts at zero. This statelessness is enforced by the plugin having no storage layer; do not work around it. *Clarification (2026-07-30): the ban is on state that feeds back into consultations — write-only observability is compatible with it. A harness-level audit capture (e.g., a PostToolUse hook archiving pal calls) or an after-the-fact analytics sweep over session logs does not violate this rule, precisely because Nestor never reads those artifacts during a run. If a future change would have Nestor read past-run data as input, that is a spec decision (see the decision-graph-memory idea in backlog), not an extension of audit logging.*

## Kill criteria

v1 Nestor is experimental. Revisit after ~10 real uses. Rip-out conditions:

- **Router override rate > 50%** — the router is not earning its keep
- **Synthesis indistinguishable** from direct `mcp__pal__consensus` calls — the persona layer is theatre
- **Latency avoidance** — users start skipping Nestor because the overhead exceeds the value
- **Cognitive tax** — the named persona adds mental overhead rather than reducing it

Revisit executed 2026-08-22 at 52 runs — no condition fired; deliberative mode and the persona layer kept (decision note kept with the host's project records). Standing cadence from v0.5.0: **review after ~15 runs on the current spec version**, checking three falsifiable metrics against the retro baseline:

- **estate-driven qualification rate** (share of `session_added_qualification` entries that supply estate the question omitted; baseline ~20/43) — should FALL with the question gate;
- **manual preset-override rate** (baseline: every code-preset run reached via override, rule 2 fired 0/52) — should FALL with the operation-shaped router;
- **`outcome` fill rate** (baseline 13/52) — should RISE with the lifecycle field.

**Review #1 of v0.5.0 (2026-10-27, 29 runs; decision note kept with the host's project records):** no kill criterion fired (override 1/29; stage 2 caught concrete errors in nearly every run; October was the busiest month on record; the name is in active use). Preset-override rate — PASS (rule 2 fired 17/29 vs 0/52). `outcome` fill — PASS (28/29). Estate-driven qualification — inconclusive: the boolean conflated deliberate privacy withholding with gate misses; replaced by `qualification_kind` (P9). **Next review (`spec-v0.5.0-r2`, ~15 runs) starts a new baseline on that field** and also judges the v0.7.0 trial fields: `assumptions` / `would_flip` / `next_check` stay if, on 5 runs, the record alone lets the user reconstruct why a decision was taken; drop them if they come back templated in 4 of 5.

Rip-out cost is near zero: delete the plugin. Preset rosters and protocol details are preserved in git history and `references/` files — they can be re-activated as a standalone skill without rebuilding from scratch.

## Related

**Within this plugin (progressive disclosure — load on demand):**
- `references/router-cases.md` — eleven acceptance cases for routing, explicit field inheritance and the invariant check
- `references/presets.md` — model rosters + per-vendor fallback chains
- `references/consensus-execution.md` — `mcp__pal__consensus` step-by-step workflow details
- `references/stances-and-gemini-flip.md` — stance semantics + Gemini Flip empirical finding
- `references/deliberative-stage-2.md` — cross-critique protocol + verbatim prompt template
- `references/setup.md` — host requirements (pal install, topology, metadata sink, redeploy)

**External:**
- [pal MCP server](https://github.com/BeehiveInnovations/pal-mcp-server) — the multi-model MCP server Nestor depends on
