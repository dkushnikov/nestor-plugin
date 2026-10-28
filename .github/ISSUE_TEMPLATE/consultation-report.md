---
name: Consultation report
about: A Nestor run that helped, misled, or went wrong — the pilot's unit of feedback
title: "[run] <one line: what was asked, what came back>"
labels: consultation
---

Paste the run-metadata record (the `- timestamp: …` block — in the answer, or in your session log if your host has one). Only `timestamp`, `router_decision`, `router_rule_matched`, `models_used`, `degraded`, `stage2`, `background` and `qualification_kind` are safe as they are; **review and redact every other field before posting** — `trigger`, `outcome`, `notes`, `session_overrode_router` and `session_added_qualification` carry your own words, your decision, the reason you overrode a route and the session context that shaped the answer. Then answer in a sentence each:

- **What was the decision or question?** The self-contained question is fine; if the real one was confidential, describe its shape (artifact review / red-team / exploratory / sanity check).
- **What changed because of the council?** Understanding, the next check, the decision itself — or nothing.
- **Which ground was new to you?** A fact, a dissent, a gap the council noticed.
- **What would you have done without Nestor?**
- **Anything wrong?** A seat that failed, a confident mistake, a route you had to override, a cost or wait you did not expect.

Do not paste API keys, pal's `.claude.json` entry with its env, or files you sent to the council. Attach `claude --version` and `claude plugin list --json` only if the run itself misbehaved.
