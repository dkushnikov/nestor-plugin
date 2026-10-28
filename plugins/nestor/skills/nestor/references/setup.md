# Setup — what the host must provide

The core protocol (`SKILL.md`) is host-neutral. It needs four things from the host; this file says what each is and how a Claude Code host supplies it. Host-specific details (your paths, your log conventions, your companion scripts) belong in your own notes, not in this plugin.

## 1. pal MCP server with `consensus` and `chat`

Install **pinned** — upstream is dormant and an unconstrained resolve crashes at import (`mcp` SDK 2.x vs pal's old `Server` API). The server environment travels in the same command (`-e`), never through a chat or a commit; `$OPENROUTER_API_KEY` below is expanded by your shell at install time and stored in the MCP config:

```bash
# upstream tag (citations from Perplexity are dropped — see note):
claude mcp add -s user pal -e OPENROUTER_API_KEY="$OPENROUTER_API_KEY" -- uvx --with "mcp<2" --from "git+https://github.com/BeehiveInnovations/pal-mcp-server.git@v9.8.2" pal-mcp-server

# recommended: the citations fork (upstream v9.8.2 + `_append_provider_citations`), pinned to a commit — the branch moves:
claude mcp add -s user pal -e OPENROUTER_API_KEY="$OPENROUTER_API_KEY" -- uvx --with "mcp<2" --from "git+https://github.com/dkushnikov/pal-mcp-server.git@61d869f421e65a8bf163f59e62df880cd2d05092" pal-mcp-server
```

pal v9.8.2 builds its response from `message.content` only and drops the `url_citation` annotations OpenRouter returns for Perplexity; without the fork the `research` preset reports sources it cannot show.

Measured on a fresh host (2026-10-28, uv 0.12, macOS, the fork commit above): the first start fetches and builds pal in about 10–15 s and leaves ~150 MB in the uv cache; later starts take under a second. `--refresh-package pal-mcp-server` (re-resolve the source at every start) is for a checkout you patch locally — with a pinned commit it only adds a network round-trip per session.

`OPENROUTER_MODELS_CONFIG_PATH` — a JSON registry with the preset model ids and their real context windows — is **required for any consultation that sends files** (`relevant_files` in stage 1, `absolute_file_paths` in stage 2 and seat restoration), and only there. pal's built-in registry is frozen at Dec 2025 and holds none of the preset ids, so without your own registry every seat runs on pal's *generic* OpenRouter capabilities (log line `Using generic OpenRouter capabilities for …`): the model id resolves and a text-only question works — the `quick` preset ran clean that way on a fresh host — but the generic entry assumes a **32K context window**, and pal sizes the file packet from it: about 4,900 tokens per seat (`context_window × 0.6 × 0.3 − 1,000`). Files beyond that budget are dropped with a `--- SKIPPED FILES (TOKEN LIMIT) ---` note while the call still reports `status: success`, so a rule-2 artifact review would run against seats that never saw the artifact. A registry entry raises the window to the model's real one (pal's own entries sit at 200K and more) and adds aliases for ad-hoc `chat` calls. `references/openrouter-models.example.json` holds the current presets and fallback chains in pal's format — copy it outside the plugin, set `OPENROUTER_MODELS_CONFIG_PATH` to that copy in the server env (`-e`, like the key), and refresh its windows when a roster changes; the file is server environment — keep it out of the chat too. Verify with `claude mcp list` (`pal … ✔ Connected`) and, in a session, pal's `listmodels` tool, which lists registry entries only: the preset ids must appear under OpenRouter with their registry context windows (`1M context`, `200K context`). Absent ids — or `32K context` when `OPENROUTER_ALLOWED_MODELS` is set — mean the registry did not load.

## 2. Process topology

Claude Code starts one pal server process per session (stdio); subagents and parallel tool calls of that session share it. That process is the serialization boundary in `consensus-execution.md`: **one unfinished consensus workflow per session**. Parallel consultations need separate sessions.

## 3. A sink for run metadata

Every consultation ends with the record in `SKILL.md` §Run metadata logging. The host decides where it lives (a session log, a project journal). If there is no sink, return the record inline marked `not persisted` — never invent a journal entry. Analytics over those records (review triggers, kill-criteria metrics, per-seat delivery) are the host's tooling; the plugin never reads them during a run.

## 4. Background delivery

The host moves MCP calls over ~2 minutes to the background and delivers the result later (Claude Code: `CLAUDE_CODE_MCP_AUTO_BACKGROUND_MS`, 2.1.212+; 0 disables backgrounding). That is a normal outcome for thinking-heavy seats on long packets. If the host archives tool results, note that the archived response of a backgrounded call is only the notice — the answer lands in the session transcript as a task notification.

## Redeploy after editing the plugin source

What a session loads depends on how the marketplace was added (Claude Code 2.1.296, plugin loading reference):

- **Local path** (`claude plugin marketplace add <path-to-clone>`): the plugin loads *in place* from the source directory — `claude plugin list` shows `Read from: <path-to-clone>/plugins/nestor`, and a session's `Read` of a reference file opens the source path. An edit is live at the next session start or `/reload-plugins`, with no version bump and no `plugin update`; the cache copy exists but is not what the session reads. The only step after an edit is `claude plugin validate <repo>`.
- **GitHub / git** (`claude plugin marketplace add <owner>/<repo>`): the session loads a cached copy, and the `version` string in `plugins/nestor/plugin.json` decides whether `claude plugin update` replaces it — same string, same files (Claude Code reports `is already at the latest version`). A change reaches these users only after **both** steps: bump the version, and push the commit to the branch the marketplace is cloned from (`main`). A bump that stays local changes nothing for them — the clean-host test of 2026-10-28 installed 0.7.4 from GitHub while 0.7.5 sat unpushed.

Refresh a cached install (GitHub / git marketplace, after the push):

```bash
claude plugin validate <repo>
claude plugin marketplace update nestor-plugin   # re-fetch the marketplace
claude plugin update nestor@nestor-plugin         # per installed scope: -s user / -s local
```

`claude plugin list` shows the computed version (the manifest `version` on a current Claude Code; an install record created by an older version may still show a 12-character git hash — that is not a stale copy) and, for a local path, the folder it reads from. Diff your `settings.json` after plugin CLI calls — older versions rewrote it wholesale.

## Tests

`tests/test_consensus_state.py` is an executable record of the pal `consensus` state contract the protocol depends on (one workflow per process, `models` read at step 1 only, failed seats appended as `status: error`). Run it after any pal upgrade with `PAL_SRC=<path to the pal checkout>`; without `PAL_SRC` its five tests **skip**, so run `python3 -m pytest -q -rs tests/` and read the skip reasons — `5 passed, 5 skipped` has not checked pal. `tests/test_no_private_tokens.py` keeps host-specific paths and personal names out of this public repo; `.githooks/pre-push` runs it over the tree and the outgoing commit messages (`git config core.hooksPath .githooks`).
