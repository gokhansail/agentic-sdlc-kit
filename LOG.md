# Log

What is this file? A dated record of what was asked, decided, built and checked. Newest entry on top. Entry format: `## YYYY-MM-DD (N) - title`, where N counts entries for that day.

## 2026-10-29 (5) - T-04 toolchain check

- Docs part: Claude Code documentation read by a docs sub-agent; facts and links in `docs/toolchain.md`. Found: `MultiEdit` is not in the current tool list; `--bare` headless runs need an API key, not the subscription login; `claude plugin eval` exists and runs with an isolated config; the behaviour of a missing `@` import is not documented.
- Install part: `developer` (Sonnet) checked machine versions and tried the MCP SDK in a throwaway virtual environment. 2.3.0 and 1.30.0 both need Python 3.10+ and both passed a stdio smoke test. 2.x renames `FastMCP` to `MCPServer`. Added `requirements-dev.txt`.
- Decisions: DEC-013 (SDK 2.x, recommended by TL; the developer had suggested 1.x), DEC-014 (`CLAUDE.local.md` for private instructions). T-05 contract updated.
- TL review: tests 31 passed; guard clean on the new files.
- Maintainer asked to leave nothing unpushed: committed and pushed together with the T-05 task entry.
- Commit: "Add toolchain notes and dev requirements (T-04)".
- Metrics (T-04): review rounds 1, questions back 1 (SDK version), out-of-scope files 0, models Sonnet and the docs sub-agent.

## 2026-10-29 (4) - T-05 added

- The plan to replace the private session file with a committed product `CLAUDE.md` at the end of phase 0 was not in `TASKS.md`. Added as T-05 (after T-04) and to the G0 gate. T-04 now also checks how a missing `@` import behaves.
- Committed with T-04.

## 2026-10-29 (3) - T-03 pre-push guard

- Built by `developer` (Sonnet). The hook is a thin shell wrapper; the logic is in `tools/pre_push_guard.py` (stdlib only, no network). It scans added lines and commit messages of outgoing commits, rejects forbidden paths, prints commit, file:line and pattern name, never the matched text. Fails closed if Python or the script is missing.
- Patterns: generic list committed in `.sdlc/guard-patterns.txt`; private terms in `.sdlc/local/private-patterns.txt`, ignored by git, reported by name only.
- Tests: 31 passed (`python -m pytest -q`), including an end-to-end push to a local bare repository.
- TL review: ran the tests, ran the guard over every tracked and new file (clean), planted a fake key and a user path (both caught, matched text not printed), checked a private term (caught, name only). The debug-flag pattern is narrower than the contract example; accepted.
- Side effect: the developer installed pytest on the machine without asking first. It was reported. Declaring it in `requirements-dev.txt` moves to T-04.
- Installed in this repository with `tools/install_git_hooks.py`. This commit's push is the guard's first real run.
- Commit: "Add pre-push guard for secrets and private content (T-03)".
- Metrics (T-03): review rounds 1, questions back 0, out-of-scope files 0, model Sonnet.

## 2026-10-29 (2) - Task tag rename, first push before the guard

- Task difficulty tags renamed from K/O/Z to [E] easy, [M] medium, [H] hard in `TASKS.md` and the developer role file.
- T-03 contract extended: `.gitattributes` keeps the hook and scripts in LF (the machine converts to CRLF on checkout, and a CRLF hook does not run); an end-to-end test pushes to a local bare repository.
- The maintainer chose to push now, before T-03. Impact: no automatic check on this push. Mitigation: the outgoing commits and pending changes were scanned by hand for key patterns, `.env`, email addresses other than GitHub noreply, absolute user paths, service URLs, debug flags, private file names, private terms and non-English letters. Result: clean; the only name found is the GitHub handle.
- Commit: "Rename task tags to E/M/H, extend T-03 contract".
- Metrics: not a contract task; TL work.

## 2026-10-29 (1) - T-01 decisions and T-02 record skeleton

- Goal: settle the open decisions D-1 to D-11 before any code.
- Decisions (T-01): DEC-001 to DEC-012 recorded in `DECISIONS.md`. The second-client test was dropped; the server is tested with Claude Code only (DEC-011). An evaluation with and without the MCP server was added to phase 4 (DEC-012).
- Started T-02 record skeleton (0.0.1). Technical Lead wrote `TASKS.md`. Scribe wrote `STATUS.md`, `LOG.md`, `CHANGELOG.md`, `LESSONS.md` and `LICENSE` (MIT).
- Outcome: maintainer approved. T-01 and T-02 committed together, locally. Not pushed: push waits for the T-03 guard.
- Commit: "Add decision record, task list and status files (T-01, T-02)".
- Metrics (T-02): review rounds 1 (TL fixed 3 lines in STATUS and LOG), questions back 0, out-of-scope files 0, model Haiku.
