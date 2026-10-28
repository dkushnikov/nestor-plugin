# Setup — what the host must provide

The core protocol (`SKILL.md`) is host-neutral. It needs four things from the host; this file says what each is and how a Claude Code host supplies it. Host-specific details (your paths, your log conventions, your companion scripts) belong in your own notes, not in this plugin.

## 1. pal MCP server with `consensus` and `chat`

Install **pinned** — upstream is dormant and an unconstrained resolve crashes at import (`mcp` SDK 2.x vs pal's old `Server` API):

```bash
# upstream tag (citations from Perplexity are dropped — see note):
claude mcp add -s user pal -- uvx --with "mcp<2" --from "git+https://github.com/BeehiveInnovations/pal-mcp-server.git@v9.8.2" pal-mcp-server

# recommended: the citations fork (upstream v9.8.2 + `_append_provider_citations`):
claude mcp add -s user pal -- uvx --with "mcp<2" --refresh-package pal-mcp-server --from "git+https://github.com/dkushnikov/pal-mcp-server.git@atlas/citations" pal-mcp-server
```

pal v9.8.2 builds its response from `message.content` only and drops the `url_citation` annotations OpenRouter returns for Perplexity; without the fork the `research` preset reports sources it cannot show.

Server environment (set in the MCP config, never pasted into a chat): `OPENROUTER_API_KEY`; `OPENROUTER_MODELS_CONFIG_PATH` pointing at a JSON registry with current model ids and aliases — pal's built-in registry is frozen at Dec 2025, and Nestor's presets use full OpenRouter ids that must resolve. Verify with `claude mcp list`.

## 2. Process topology

Claude Code starts one pal server process per session (stdio); subagents and parallel tool calls of that session share it. That process is the serialization boundary in `consensus-execution.md`: **one unfinished consensus workflow per session**. Parallel consultations need separate sessions.

## 3. A sink for run metadata

Every consultation ends with the record in `SKILL.md` §Run metadata logging. The host decides where it lives (a session log, a project journal). If there is no sink, return the record inline marked `not persisted` — never invent a journal entry. Analytics over those records (review triggers, kill-criteria metrics, per-seat delivery) are the host's tooling; the plugin never reads them during a run.

## 4. Background delivery

The host moves MCP calls over ~2 minutes to the background and delivers the result later (Claude Code: `CLAUDE_CODE_MCP_AUTO_BACKGROUND_MS`, 2.1.212+; 0 disables backgrounding). That is a normal outcome for thinking-heavy seats on long packets. If the host archives tool results, note that the archived response of a backgrounded call is only the notice — the answer lands in the session transcript as a task notification.

## Redeploy after editing the plugin source

```bash
claude plugin validate <repo>
claude plugin marketplace update nestor-plugin   # re-scan the directory source
claude plugin update nestor@nestor-plugin         # per installed scope: -s user / -s local
```

Sessions load the installed cache, not the source; an edit is live only after the update ran and `claude plugin list` shows the new hash in every scope. Diff your `settings.json` after plugin CLI calls — older versions rewrote it wholesale.

## Tests

`tests/test_consensus_state.py` is an executable record of the pal `consensus` state contract the protocol depends on (one workflow per process, `models` read at step 1 only, failed seats appended as `status: error`). Run it after any pal upgrade with `PAL_SRC=<path to the pal checkout>`. `tests/test_no_private_tokens.py` keeps host-specific paths and personal names out of this public repo; `.githooks/pre-push` runs it over the tree and the outgoing commit messages (`git config core.hooksPath .githooks`).
