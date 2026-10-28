# Router acceptance cases

These are acceptance cases for an LLM-interpreted routing specification.
They demonstrate unambiguous text, not deterministic routing by an LLM.
Cases 1–8 cover the base rules and rule-0 field inheritance; cases 9–11 cover the invariant check that runs after the overlay (SKILL.md §The router, step 3). For 9–11 the check is on the final `question_framing` — no residual `stance_prompt` after normalisation — not only on the `mode` / `stances` values.

| # | Input | Mode | Preset | Stances | Rule | Reason |
|---|---|---|---|---|---|---|
| 1 | «Nestor, red-team this: вынести монолит в микросервисы» | adversarial | arch | for/against/neutral | 1 | Red-teaming a proposed position selects rule 1, with hypothesis-specific `stance_prompt` for each model. |
| 2 | «Nestor, проверь эту API-spec по требованиям» | deliberative | code | all-neutral (review dimensions) | 2 | Reviewing an implementation-bound API artifact uses correctness, omissions, risks, strengths, and recommended changes as review dimensions. |
| 3 | «Nestor, сравни PostgreSQL и Redis для заданного cache use case» | deliberative | code | all-neutral | 2 | Comparing named technical options for an implementation-bound use case selects the compare/select branch. |
| 4 | «Nestor, проверь свежие данные рынка» | deliberative | research | all-neutral | 3 | Verifying fresh market data requires web-grounded research. |
| 5 | «Nestor, чего не хватает в постановке организационной проблемы?» | deliberative | arch | all-neutral | 4 | Asking what is missing from an organizational problem's framing is open-ended exploration. |
| 6 | «Nestor, quick: очевидные ошибки в этой идее?» | adversarial | quick | all-neutral | 5 (explicit preset agrees) | Looking for obvious mistakes is a sanity check; the explicit `quick` preset agrees with the base route and changes no field. |
| 7 | «Nestor brainstorm: предложи варианты для этой открытой проблемы» | deliberative | brainstorm | all-neutral | 4 base; 0 overlays preset | The open question selects rule 4; explicit `brainstorm` changes only the preset, inheriting deliberative mode and neutral stances. |
| 8 | «Nestor, red-team мою гипотезу, но все stances neutral» | adversarial | arch | all-neutral | 1 base; 0 overlays stances | Red-teaming selects rule 1; explicit neutral stances replace its stance triple and opposing prompts while retaining mode and preset. |
| 9 | «Nestor, глубокий разбор: red-team this — вынести монолит в микросервисы» | deliberative | arch | all-neutral (normalised) | 1 base; 0 overlays mode; invariant check normalises stances | The red-team shape selects rule 1; the explicit deliberative override inherits rule 1's stance triple, which the invariant check normalises to all-neutral. `question_framing` carries the proposition without any `stance_prompt`; the announcement names the normalisation. |
| 10 | «Nestor, deliberative, явно назначь for/against/neutral для этой гипотезы» | — | — | — | 0 → `needs_clarification` | Explicit deliberative and explicit role stances break the deliberative invariant. Before any model call the session asks which one is wanted: a neutral deliberative consultation or a role-assigned adversarial check. |
| 11 | «Nestor, adversarial: проверь эту API-spec по требованиям» | adversarial | code | all-neutral (review dimensions) | 2 base; 0 overlays mode | A mode-only override over a neutral technical review changes the mode and nothing else: preset `code`, the review dimensions and the question text are inherited unchanged; adversarial + all-neutral is valid, so no normalisation and no stage 2. |
