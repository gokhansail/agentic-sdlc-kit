# Log

What is this file? A dated record of what was asked, decided, built and checked. Newest entry on top. Entry format: `## YYYY-MM-DD (N) - title`, where N counts entries for that day.

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
