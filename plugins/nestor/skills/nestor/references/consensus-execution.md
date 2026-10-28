# pal.consensus Step-by-Step Execution

The `mcp__pal__consensus` tool is a **multi-step workflow**, not a single-call tool. Understand the step mechanics before invoking it inside Nestor.

## Workflow shape

A consensus call with N models requires N tool invocations:
- **Step 1** — dispatches the question, lists all models, and consults the first model
- **Steps 2 through N** — capture each subsequent model's response one at a time
- The **last step** (step N for an N-model preset) has `next_step_required: false`, which tells pal to synthesise the accumulated responses

For a 3-model preset (all Nestor presets are 3-model), this is **three steps total**. `total_steps` = N, the number of models. pal's own tool description says "models + 1"; the server normalises `total_steps` to `len(models)` at step 1 regardless (observed 2026-10-18: a 4 was silently turned into 3). Pass N.

## Step 1 parameters

```
step: "<the full well-formulated question, self-contained, ready to be shown to models>"
step_number: 1
total_steps: 3  (for a 3-model preset)
next_step_required: true
findings: "<your independent analysis before seeing any model response — not shared with the models>"
relevant_files: ["<absolute paths of the question packet / artifact under review>"]  (optional; embedded for EVERY model, blinded)
models: [
  {"model": "<full-model-id-1>", "stance": "<stance>"},
  {"model": "<full-model-id-2>", "stance": "<stance>"},
  {"model": "<full-model-id-3>", "stance": "<stance>"}
]
```

Step 1 returns a `continuation_id` in the response payload. **Save it immediately** — you will need to pass it to every subsequent step in the same workflow.

**`models` is read at step 1 only.** pal stores the roster on the tool instance at step 1 and consults `models[step_number - 1]` on each later step; a `models` list passed on step 2 or 3 is ignored. There is no in-workflow substitution — see "Seat failure inside a workflow" below.

## Steps 2 and 3 parameters

```
step: "<brief note about moving to the next model — optional but recommended>"
step_number: 2  (or 3 for the final step)
total_steps: 3
next_step_required: true  (false on the final step)
continuation_id: "<from step 1>"
findings: "<summarise what the previous model said — this becomes the internal record>"
```

On step 3 (the last model in a 3-model preset), set `next_step_required: false` to trigger pal's synthesis. The workflow is complete when that step returns.

Each model receives the **original step-1 question** (pal keeps it as `original_proposal`); the `step` text of steps 2+ is never shown to any model.

## One workflow at a time — the state contract

pal keeps the consensus workflow state (question, roster, accumulated answers) on **one `ConsensusTool` instance per pal server process**. Step 1 of any workflow overwrites that state; steps 2+ read it. The `continuation_id` links the steps for conversation memory, but it does **not** reload the state — a step 2 always consults the roster of whichever step 1 ran last on that process.

The practical boundary: **one pal process serves one Claude Code session**, including its subagents and parallel tool calls. Therefore:

- **One unfinished `consensus` workflow per session at a time.** Finish steps 1 → N before starting another consensus. Parallel consultations need separate sessions, not separate `continuation_id`s. (Observed 2026-10-05: three workflows launched within a minute in one session — the Gemini and Qwen seats answered a neighbouring question and had to be re-run sequentially.)
- **Always pass `continuation_id`** from step 1 to every later step. Omitting it isolates nothing — it drops the conversation memory **and the file packet**: pal re-attaches step 1's `relevant_files` to steps 2+ only by merging the thread's initial context when the id is present (`server.py` `reconstruct_thread_context`; `_consult_model` reads the current request's files), so seats 2..N would answer without the files.
- **If step 2+ reports a model or question that is not yours**, the state was overwritten. Stop; do not splice answers across workflows. Re-run the whole workflow from step 1 once the other one has finished.
- **Stage-2 `pal.chat` calls are a different case.** `chat` carries no workflow state; the three critiques may run in parallel (one assistant message, three calls) as `deliberative-stage-2.md` specifies.

## Seat failure inside a workflow

A failing model does not stop the workflow: pal appends `{"status": "error", ...}` to `accumulated_responses` and moves on, and the final `total_responses` counts error entries too. **Count usable answers by `status: success` with non-empty content, never by `total_responses`.**

A failed seat cannot be replaced mid-workflow (`models` is step-1-only). Finish the workflow with the remaining seats, then **restore the seat once** with a single `mcp__pal__chat` to its first same-vendor fallback (`presets.md`), carrying the identical step-1 packet: the same question text (pal's `original_proposal`), the same files via `absolute_file_paths`, the same stance instruction, and `working_directory_absolute_path`. The restored answer is that seat's stage-1 answer. Then apply the degraded-run contract in Nestor SKILL.md Step 4 (deliberative: three usable → normal stage 2, two → partial-roster run with two cross-critiques, labelled; adversarial: synthesis from the usable stage-1 answers (stance-assigned or neutral, as routed) with no stage 2, `skipped-adversarial`; fewer than two usable → no synthesis in either mode). SKILL.md Step 4 §Seat restoration is the authoritative policy; this section restates it and adds no attempts. Do not restart the workflow to swap a model — it re-bills the healthy seats and the roster is still fixed at step 1. Decision 2026-10-28 (external audit finding F3; the alternative — restarting the whole workflow with a substitute roster — re-bills the healthy seats and was rejected).

## Stepping discipline

**Step through every model in the preset before triggering synthesis.** The full consensus workflow is what makes "preset" mean something — it guarantees that the preset's full roster was consulted. Shortcuts violate the preset contract:

- Do not terminate the workflow before all models in the preset have been stepped through
- Do not substitute `mcp__pal__chat` calls for consensus steps when the preset is set (the one exception is restoring a failed seat *after* the workflow has finished, per SKILL.md Step 4)
- Do not pre-emptively deviate from the preset roster based on runtime optimisation reasoning — see `presets.md` for the authoritative-at-runtime rule

## Background delivery

The host moves any MCP call that exceeds ~120 s to the background and returns its result later as a task notification. That is a normal outcome for long packets on thinking-heavy seats (2026-09 → 10: most Qwen step-3 calls), not a failure: wait for the notification, then continue with the next step. Record background-delivered seats in run metadata (`background:` field) — the roster review weighs them (rollback condition (c) in `presets.md`). A call that never returns is the degraded case above.

## Practical note: use of `findings` field

The `findings` field in each step is Nestor's internal record of what happened at that step. It is **not sent to the models** — they only see the `step` field (the question) and their own stance assignment. Use `findings` for structured notes: summary of the previous model's response, routing reasoning, any diagnostic observations. These notes become part of the session log via Nestor's run metadata logging.
