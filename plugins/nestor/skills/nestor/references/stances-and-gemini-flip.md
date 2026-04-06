# Stances — Roleplay Not Belief, and the Gemini Flip Finding

This file documents the stance semantics for `mcp__pal__consensus` calls and the empirical finding that shaped Nestor's stance discipline.

## The three stance types

When calling `mcp__pal__consensus`, each model in the roster can be assigned a `stance` field:

- **`neutral`** (default) — the model gives its actual best judgment on the question. Use when you want to know what the model *thinks*.
- **`for`** / **`against`** — **roleplay, not belief**. The model generates a defence (`for`) or attack (`against`) of the assigned position regardless of what its neutral answer would be. Use to red-team a specific hypothesis from known angles.
- **`stance_prompt`** — custom framing string, e.g., `"propose unconventional approaches"` or `"focus on operational risk"`. Same roleplay caveat as `for`/`against`: you are directing the model's output, not eliciting its belief.

## The Gemini Flip — empirical finding

**The finding**: on the 2026-04-05 verification run of deliberative mode, Google's Gemini 3.1 Pro **reversed its position on both test questions** between the `against` stance and the `neutral` stance — at **identical confidence scores** (8-9/10 in both directions).

Specifically:

**Question 1 — memory precedence design**
- `against` stance: *"Any static precedence scheme is fundamentally flawed... the system must use explicit conflict surfacing backed by a Shift-to-Explicit-Exceptions abstraction."*
- `neutral` stance: *"Strict most-local wins (Lexical Scoping) is the uniquely correct primary mechanism because it directly maps to the standard software engineering mental model of variable shadowing."*

Same model. Same prompt. Opposite conclusions. 9/10 confidence in both directions.

**Question 2 — whiteboard CRDT design**
- `against` stance: *"Operational Transform (OT) via ShareDB is the optimal choice... attempting CRDT is almost guaranteed to cause a schedule-killing architecture crisis around month 8."*
- `neutral` stance: *"CRDT (using a mature library like Yjs) is the only viable choice for this team's constraints."*

Same pattern. 8/10 confidence in both directions.

## Why this is load-bearing, not a quirk

The 8-9/10 confidence in both directions is what makes the finding disqualifying for vote-counting. The model was not expressing uncertainty when assigned a stance. It was **confidently defending whatever position it had been told to defend**. If the model had answered "low confidence, 5/10, I'm forced to argue this direction", we could discount stance-assigned runs as conditional. But confident-opposite answers at identical scores mean the stance prompt is effectively rewriting the model's conclusion, not constraining its framing.

This behaviour was observed in only one model (Gemini) across two questions in the verification run. Whether Opus, GPT, or other models flip under the same pressure is an **open question** for future tracking. But the observed flip is enough to treat stance-assigned runs as roleplay across all models until evidence proves otherwise.

## Operational implication: do NOT count votes across stance-assigned runs

"2/3 models agree on X" in an adversarial run is **meaningless** when 1/3 of the roster was instructed to argue the opposite of X. The vote is not evidence of belief; it is evidence that the three models completed their assignments. Reporting "2/3 vote for X" from a stance-assigned run is a data-integrity violation — it conflates compliance with belief.

If you need a directional signal across models, use:
- **all-neutral stances** (each model gives its own judgment), or
- **deliberative mode** (all-neutral stage 1 plus anonymised peer critique on top — see `deliberative-stage-2.md`)

## When to use for/against/stance_prompt vs neutral

| Goal | Stance configuration | Why |
|---|---|---|
| Elicit the models' actual judgment on a question | All `neutral` | Avoids the Gemini Flip contamination; each model gives its own best read |
| Red-team a specific hypothesis the user has drafted | `for` + `against` + `neutral` with `stance_prompt` targeting the hypothesis | Deliberate stress-test from known angles — the output is adversarial framing by design, not polling |
| Stress-test from a single specific angle (e.g., security, operational risk, cost) | Single model with `stance_prompt` describing that angle | Directed attack without full for/against structure |

**Default is all-neutral.** Use stances only when the user has a concrete proposal on the table and explicitly wants it pressure-tested from known angles. Nestor's router enforces this: only rule 1 (red-team) assigns non-neutral stances; all other rules use all-neutral.

## Cross-reference

The Gemini Flip finding was discovered during a structured A/B verification run on 2026-04-05. The verification tested both adversarial and deliberative modes across two questions, with identical questions run under different stance configurations to isolate the stance variable. The finding was independently confirmed by a recursive-council run on the Nestor design itself.
