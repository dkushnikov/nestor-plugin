# Router acceptance cases

These are acceptance cases for an LLM-interpreted routing specification.
They demonstrate unambiguous text, not deterministic routing by an LLM.

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
