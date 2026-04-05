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

The three calls run in parallel, not sequentially, because they are independent of each other — each reviewer reads the same two peer answers, and no reviewer's critique affects any other's.

Note: `mcp__pal__chat` is used **only** for stage 2 cross-critique calls. It is never used as a substitute for `mcp__pal__consensus` in stage 1 or in adversarial mode.

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

## Anti-patterns in stage 2

- **No ranking parse.** Prose critiques only. At N=3 peers, ordinal aggregation is statistical theatre — each peer reviews only two others, so any aggregation is too thin to be a meaningful signal. Do not attempt to rank the stage-1 answers based on stage-2 critiques.
- **No chairman model.** Claude-in-session (acting as Nestor) is the synthesiser. External synthesis via a separate "chairman" model loses the session-awareness that Atlas then layers on top of Nestor's output.
- **No iterative debate.** One stage 2 round only. Multi-round debate introduces anchoring bias as models converge on shared framings rather than their independent reads.
- **No stances in stage 2.** All three critique calls run under each model's default voice — not with `for` or `against` stance prompts. The three stage-1 answers were already neutral, and their critiques should also be neutral.
- **No model identity in stage 2 prompts.** Always label the peer answers as `Response A` / `Response B`. Never reveal that "Response A was written by Gemini". Anonymisation is what prevents peer review from collapsing into provider loyalty or stylistic recognition.

## Synthesis after stage 2

Claude (acting as Nestor) synthesises from **six inputs**: three stage-1 answers plus three stage-2 critiques. Lead the synthesis with the judgment itself, then explicitly call out where the critiques **converged on shared weaknesses** in the stage-1 answers — that convergent critique is the strongest meta-signal deliberative mode produces.

## Empirical evidence for stage 2 value

On a 3/3 unanimous first-round test run during the 2026-04-05 verification of deliberative mode, stage 2 peer critique caught **four major unaddressed requirements and two factual errors** in the initial answers that unanimity had hidden. That result is the operational justification for running stage 2 even when stage 1 is unanimous — and for making stage 2 unconditional rather than conditional on stage-1 disagreement.

Full verification transcripts: `~/Obsidian/Atlas/Thinking/AI Council — Deliberative Mode Spec.md`.
