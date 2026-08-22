# Deliberative Mode — Stage 2 Cross-Critique Protocol

Deliberative mode is a two-stage council protocol. Stage 1 collects three neutral first-round answers via `mcp__pal__consensus`. Stage 2 adds an anonymised peer-critique round on top before synthesis. This file specifies stage 2.

## When stage 2 runs

Stage 2 is specific to **deliberative mode**. Adversarial mode does not have a stage 2 — adversarial runs end with synthesis of the three stance-assigned answers from stage 1 directly.

Deliberative mode is routed to by:
- Router rule 2 (technical implementation decision with a clear axis)
- Router rule 3 (factual or research question requiring web-grounded verification)
- Router rule 4 (exploratory or open-ended framing)

Stage 2 runs **unconditionally in deliberative mode**, including when the three stage-1 answers are unanimous. Do not skip stage 2 on unanimity — shared blind spots are invisible in unanimous answers, and the whole point of deliberative mode is to surface them.

## Stage 2 execution

After collecting the three neutral stage-1 answers, run **three parallel `mcp__pal__chat` calls**. Each call sends one council member the other two answers, labelled only as `Response A` and `Response B` (model identity hidden from the reviewer), with the critique prompt template below.

The three calls are independent of each other — each reviewer receives a fixed input (the two *other* members' answers; each critic therefore sees a different pair) and no reviewer's critique affects any other's. **Issue all three `mcp__pal__chat` calls in a single assistant message** (the host supports parallel tool calls in one block) — that is the concrete parallelism mechanism. If the host executes them sequentially anyway, the result is still valid — independence comes from the fixed inputs and anonymisation, not from timing — but the added latency counts against the latency kill criterion, so note sequential execution in the run metadata.

**Balance answer order across critics.** Each stage-1 answer appears in exactly two critique prompts; assign `Response A` / `Response B` so that **each answer appears once as A and once as B** across the three calls (a cyclic rotation gives this automatically; use randomness only to pick which of the two valid rotations). Do not reuse one fixed roster ordering for all critics — ordering anchors are real and persist through deliberation: models systematically over-weight the first-presented answer even when instructed to weigh content only (arXiv 2606.19494, "Hidden Anchors", Jun 2026). Anonymisation removes identity bias; balanced order rotation removes position bias. Both are required.

Note: `mcp__pal__chat` is used **only** for stage 2 cross-critique calls. It is never used as a substitute for `mcp__pal__consensus` in stage 1 or in adversarial mode.

**Always pass `working_directory_absolute_path`** in every `mcp__pal__chat` call — pal's input validation rejects the call without it (observed 2026-08-13: all three parallel stage-2 calls burned a failed round on the missing param before retry).

## Critique prompt template

Use this template verbatim for every stage 2 call. Substitute the original question and the two anonymised answers:

    You are reviewing two anonymised responses to the following question:

    <original question>

    Response A:
    <one of the two other models' stage-1 answers>

    Response B:
    <the other of the two models' stage-1 answers>

    For each response, identify:
    1. One concrete strength (point at a specific claim, not style).
    2. One concrete flaw (point at a specific claim, not style).
    3. One missing consideration.

    Then: what might BOTH responses be missing that the question didn't explicitly ask about?

    Do not rank. Do not summarise. Be specific — point at claims, not at prose style.

The rigid "one concrete strength / one concrete flaw / one missing consideration" structure is deliberate — it is the **anti-shallowness constraint**. Without it, models default to polite summary and lose signal.

## Stage-2 degraded handling

Stage 2 uses `mcp__pal__chat`, so the consensus-run degraded handling in SKILL.md Step 4 does not cover it directly. Rules:

- **A critic call fails or returns unusable output** (error, empty content, off-topic): retry once with that critic's same-vendor fallback from `presets.md`. If the retry also fails, proceed without that critique.
- **Reasoning models need output headroom.** Several roster models (the Sol family, Qwen 3.7 Max) spend tokens on reasoning before emitting content; a tight output cap yields an empty `content` with the budget consumed. Do not set restrictive output limits on stage-2 calls, and treat empty-content-with-usage as a failed call (retry per above), not as a null critique.
- **Proceed with 2/3 critiques**, flagging `stage2: partial (2/3)` in run metadata and the degradation in the return envelope's `confidence`.
- **With 0 or 1 critiques, do not synthesise as deliberative.** Present the stage-1 answers with a stage-1-only label and the failure reported honestly — a single critique masquerading as peer review is worse than visibly skipping stage 2.

## Research-mode stage 2: claim-level grounding

Rule-3 (research preset) runs break the peer-critique assumption for freshness: every council member shares a training cutoff, so peers cannot catch stale facts (observed and adapted in the field 2026-06-07; codified v0.5.0). For research runs, stage 2 is a **conditional grounding pass layered onto critique — not a wholesale replacement**:

1. Extract the crux claims from the stage-1 answers.
2. Classify each claim: freshness-sensitive · externally verifiable · internally reasoned · normative.
3. Web-verify ONLY the freshness-sensitive and externally-verifiable claims. Report each honestly: verified / contradicted / mixed / not-found — never force a verification that the sources do not support, and check that a source actually entails the claim, not merely mentions the topic.
4. Internally-reasoned and normative claims keep peer critique — grounding cannot check inference quality or judgment.
5. Record in run metadata (`notes`) which path each crux took.

Search queries inherit the same neutrality rule as every other stage: no asker leaning, no desired verdict baked into the query.

## Anti-patterns in stage 2

- **No ranking parse.** Prose critiques only. At N=3 peers, ordinal aggregation is statistical theatre — each peer reviews only two others, so any aggregation is too thin to be a meaningful signal. Do not attempt to rank the stage-1 answers based on stage-2 critiques.
- **No chairman model.** Claude-in-session (acting as Nestor) is the synthesiser. External synthesis via a separate "chairman" model loses the session-awareness that the calling session then layers on top of Nestor's output.
- **No iterative debate.** One stage 2 round only. Multi-round debate introduces anchoring bias as models converge on shared framings rather than their independent reads.
- **No stances in stage 2.** All three critique calls run under each model's default voice — not with `for` or `against` stance prompts. The three stage-1 answers were already neutral, and their critiques should also be neutral.
- **No model identity in stage 2 prompts.** Always label the peer answers as `Response A` / `Response B`. Never reveal that "Response A was written by Gemini". Anonymisation is what prevents peer review from collapsing into provider loyalty or stylistic recognition.

## Synthesis after stage 2

Claude (acting as Nestor) synthesises from **six inputs**: three stage-1 answers plus three stage-2 critiques. Lead the synthesis with the judgment itself, then explicitly call out where the critiques **converged on shared weaknesses** in the stage-1 answers — that convergent critique is the strongest meta-signal deliberative mode produces.

**On a 2-1 split, the majority is not the verdict.** Frontier models share training data, so their errors correlate — in roughly one of four divergent cases the minority position is the correct one (arXiv 2606.29270, "Minority Sentinel", Jun 2026). When stage 1 + stage 2 leave a genuine split:

1. Extract the **crux claim** — the specific factual or logical point the sides actually diverge on, not the surface conclusion.
2. For high-stakes questions, run **one grounded verification pass on the crux** (evidence lookup, file read, logic re-derivation) before synthesising. Verify with evidence, not with another model's opinion — the same research found that re-judging a split with an additional LLM has *negative* net gain, while evidence-grounded checks flip verdicts with high precision.
3. Whatever the outcome, carry the dissent into the return envelope's `dissenting_view` with its reasoning intact. A synthesised middle position that erases the split is worse than an honest fork.

## Empirical evidence for stage 2 value

On a 3/3 unanimous first-round test run during the 2026-04-05 verification of deliberative mode, stage 2 peer critique caught **four major unaddressed requirements and two factual errors** in the initial answers that unanimity had hidden. That result is the operational justification for running stage 2 even when stage 1 is unanimous — and for making stage 2 unconditional rather than conditional on stage-1 disagreement.

This finding was established during the 2026-04-05 A/B verification of deliberative mode, comparing stage-1-only vs stage-1+2 outputs on the same questions.
