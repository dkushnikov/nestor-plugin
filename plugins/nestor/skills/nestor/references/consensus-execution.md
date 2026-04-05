# pal.consensus Step-by-Step Execution

The `mcp__pal__consensus` tool is a **multi-step workflow**, not a single-call tool. Understand the step mechanics before invoking it inside Nestor.

## Workflow shape

A consensus call with N models requires N tool invocations:
- **Step 1** — dispatches the question, lists all models, and consults the first model
- **Steps 2 through N** — capture each subsequent model's response one at a time
- The **last step** (step N for an N-model preset) has `next_step_required: false`, which tells pal to synthesise the accumulated responses

For a 3-model preset (all Nestor presets are 3-model), this is **three steps total**.

## Step 1 parameters

```
step: "<the full well-formulated question, self-contained, ready to be shown to models>"
step_number: 1
total_steps: 3  (for a 3-model preset)
next_step_required: true
findings: "<your independent analysis before seeing any model response — not shared with the models>"
models: [
  {"model": "<full-model-id-1>", "stance": "<stance>"},
  {"model": "<full-model-id-2>", "stance": "<stance>"},
  {"model": "<full-model-id-3>", "stance": "<stance>"}
]
```

Step 1 returns a `continuation_id` in the response payload. **Save it immediately** — you will need to pass it to every subsequent step in the same workflow.

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

## continuation_id handling

pal uses a single shared process for all consensus runs. The `continuation_id` is the handle that links steps within one workflow. It must be passed correctly or pal loses the workflow state.

- **Main thread (normal Nestor use)**: pass `continuation_id` from step 1 to every subsequent step. This is the happy path.
- **Subagent or parallel runs**: do NOT pass `continuation_id`. Each step will be independent — you lose cross-step context but avoid thread contamination from parallel workflows running concurrently. If step 2+ returns the wrong models or the wrong question, that is continuation_id contamination — retry without passing the ID.

Nestor calls happen on the main thread, so the main-thread rule applies: pass `continuation_id` through every step.

## Stepping discipline

**Step through every model in the preset before triggering synthesis.** The full consensus workflow is what makes "preset" mean something — it guarantees that the preset's full roster was consulted. Shortcuts violate the preset contract:

- Do not terminate the workflow before all models in the preset have been stepped through
- Do not substitute `mcp__pal__chat` calls for consensus steps when the preset is set
- Do not pre-emptively deviate from the preset roster based on runtime optimisation reasoning — see `presets.md` for the authoritative-at-runtime rule

If a model fails or returns an unusable response during a step, invoke the **degraded-run handling** described in Nestor SKILL.md Step 4 — flag the missing model in the return envelope's `confidence` field, do not silently drop it.

## Practical note: use of `findings` field

The `findings` field in each step is Nestor's internal record of what happened at that step. It is **not sent to the models** — they only see the `step` field (the question) and their own stance assignment. Use `findings` for structured notes: summary of the previous model's response, routing reasoning, any diagnostic observations. These notes become part of the session log via Nestor's run metadata logging.
