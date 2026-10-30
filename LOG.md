# Log

What is this file? A dated record of what was asked, decided, built and checked. Newest entry on top. Entry format: `## YYYY-MM-DD (N) - title`, where N counts entries for that day.

## 2026-10-30 (4) - T-12 templates

- The maintainer chose the TL recommendation on 4 open questions: 7 templates; one Markdown file each under `templates/`; `tech-writer` (Sonnet, medium); the G1 end-to-end read stays a criterion, done once after T-13 and before G1.
- C-26 (public endpoint checklist) moved from T-12 to T-44, because the kit has no public endpoint. The target cell of the source map row was changed.
- `tech-writer` wrote 7 templates: task contract, decision record, lesson entry, audit report, re-verify table, push checklist, developer rules. One CHANGELOG line added. The writer has no shell tool, so the TL ran the guard and the tests.
- TL review round 1 found 6 items, fixed in round 2:
  - a non-ASCII character, and a field name that did not match the decision record format;
  - a duplicated verdict line and an unsourced counts field in the audit report;
  - the re-verify role name;
  - missing source IDs in the push checklist and the re-verify table;
  - an unsourced sentence in the developer rules.
- The size label field (C-52) was missing from the task contract template, because the TL contract did not list C-52. Added in round 2.
- After round 2 the TL made 2 more edits: one blank line added in the audit report, and the C-02 source ID added to the lesson entry. Role exceeded (2 lines, after the 2-round limit).
- Not added, per the writer report: per-task result fields (C-22) belong in the log. Rule headings (C-32) and report placement (C-15) belong to T-13.
- TL checks: every cited ID exists in the source map; no non-ASCII characters; banned-word list clean; guard clean (exit 0); `python -m pytest -q`: 31 passed. A filled task contract is 10 lines (cap 15).
- Maintainer approved T-12 (2026-10-31).
- Commit: "Add templates (T-12)".
- Metrics (T-12): review rounds 2, questions back 2 (non-ASCII character, who runs the guard), out-of-scope files 0, models Sonnet (tech-writer), Haiku (scribe).

## 2026-10-30 (3) - T-11 closed, heading fix

- The maintainer found `PLAYBOOK.md` too long and asked for a summary. The TL summarised the core and the appendices and reported 2 review items: the core heading "What it is not" did not match its text; the appendices repeat much of the core.
- The maintainer asked for the TL's fixes and decided not to act on the length. Fixed: heading renamed to "Scope and limits". Not done: shortening the appendices (maintainer decision).
- The heading was edited by the TL directly, not by `tech-writer`. Role exceeded at the maintainer's request (one line).
- Impact note: the G1 criterion "maintainer read it once end to end" is not met. The maintainer read the TL summary, not the file. The item stays open for G1; the TL warned that a summary does not replace the read.
- The lesson on plan limits copied without their reason (T-10) was added to `LESSONS.md`.
- Metrics (T-11 fix): review rounds 0, questions back 0, out-of-scope files 0, models none.

## 2026-10-30 (2) - T-11 playbook draft

- The maintainer asked to start T-11 in the same session after T-10.
- `tech-writer` (Sonnet, effort high) wrote `PLAYBOOK.md`: a core of about 450 words and appendices A to I, 2,308 words in total, and one CHANGELOG line. It read only the source map, `CLAUDE.md` and `DECISIONS.md`.
- TL review round 1 found 9 items, fixed in round 2. Three were wrong or unsupported claims: the server was described as already tested; the mechanics table described the source projects as if they were this repository; two sentences had no source row and were removed.
- TL checks after round 2: 65 cited IDs, all present in the map or the decisions; one map row uncited (C-26, target T-12); no non-ASCII characters; banned-word list clean; guard clean; `python -m pytest -q`: 31 passed.
- Rows the writer reported as missing from the map: decision record format (left to T-12 templates). Not added to the map.
- The maintainer approved committing the draft before reading it. The end-to-end read is a G1 criterion, not a commit criterion; changes from the read go in a separate commit.
- Commit: "Add playbook draft (T-11)".
- Metrics (T-11): review rounds 2, questions back 0, out-of-scope files 0, models Sonnet (tech-writer).

## 2026-10-30 (1) - T-10 source map

- Decision DEC-016: the committed source map names private sources by ID and section; the ID-to-file index stays in an ignored local file.
- Decision DEC-017: every process lesson goes into the map and may appear in the playbook; added to the G1 agenda.
- `scout` (Haiku) extracted 51 concepts from the base list plus 13 more method concepts from the same sources; all 16 base rows covered. The TL spot-checked section numbers and lesson dates against the sources: all matched.
- Two deviations from the base list. The contract line "no number from a source" was narrowed by the TL to "no measured number" so method parameters (15-line cap, 2 rounds) can be cited. The lesson cap of 3 from the base list was removed by the maintainer (DEC-017): the lessons log has 19 entries, 6 of them process lessons, and all 6 are in the map. Gate G1 reviews this choice.
- `tech-writer` (Sonnet) wrote `docs/source-map.md` (9 sources, 64 concepts, 6 dropped rows), the local index and one CHANGELOG line. Round 2 fixed three items: one term for the customer role, the concurrency item added to the single-writer concept, a dropped row for the project entry section. A third edit for DEC-017 moved three lessons from the dropped table into the concept table; this was a scope change, not a review round.
- TL review: guard clean over the changed files (exit 0); `python -m pytest -q`: 31 passed.
- Maintainer approved T-10. The maintainer reads the map and the playbook later, before G1.
- Commit: "Add source map with private sources as IDs (T-10)".
- Metrics (T-10): review rounds 2, questions back 0, out-of-scope files 0, models Haiku (scout), Sonnet (tech-writer).

## 2026-10-29 (8) - G0 review findings fixed

- The maintainer asked to fix every finding from the G0 close.
- Status line deviations (gate name in place of a task id; "no code written" although code exists). Cause: the field meanings were not defined. Fix in `CLAUDE.md`: task is the open task, or the next one when none is open; code state is whether the repository holds code, not whether the reply changed any. The ignored local file now states the Turkish line is written in exactly that form, with nothing added, and points to `CLAUDE.md` for the field meanings. Each rule stays in one file (DEC-015). `CLAUDE.md` stays at 80 lines.
- `CLAUDE.md` edited directly by the TL (one line), not by `tech-writer`. Role exceeded at the maintainer's request.
- Clean-clone headless check: retried, failed again on the expired OAuth login. Moved into `TASKS.md` as part of T-46 (isolated session in a clean clone without the ignored local file resumes from the records), so it is tracked, not only noted.
- File name in LOG entry (7): fixed before the G0 commit.

## 2026-10-29 (7) - Gate G0 closed

- Maintainer check (G0): a fresh session in this folder loaded both instruction files (committed `CLAUDE.md` and the ignored local file). The resume procedure read `STATUS.md`, the NOW NEXT line of `TASKS.md`, the top of `LOG.md` and the open decisions (none). The reply followed the private conversation rules.
- Re-check against the T-05 acceptance lines: guard run over every tracked file, clean (exit 0); `python -m pytest -q`: 31 passed; a clean clone has no local instruction file; `CLAUDE.md` has no import of or reference to it; every record it names and the 7 role files exist in the clone.
- Not checked: a headless session in the clean clone. The OAuth login expired again. A clone test on this machine would also load the user-level instruction file, so it is not isolated. An isolated check needs another machine or an API-key bare run (phase 4, T-46).
- Deviations in the resume reply: the end-of-reply status line named the gate instead of a task id; it said no code was written although the guard code exists. Not a blocker; noted.
- Maintainer approved closing G0. Phase 0 closed, phase 1 open. Next: T-10 source map in a fresh session.

## 2026-10-29 (6) - T-05 product CLAUDE.md, all documentation in English

- The maintainer asked for every document in English, committed or not, and no rule kept in two places (DEC-015).
- `CLAUDE.md` written by `tech-writer` (Sonnet): 80 lines, process rules only. TL fixed two lines (dropped "tool-independent", which DEC-011 does not support; corrected who writes the CHANGELOG line).
- Personal rules moved to an ignored local file that starts with a table of which file holds what and a test for new rules. The two earlier private files were merged into it; the TL checked each rule against the old files before removing them.
- The day-0 plan was translated once (Sonnet) into an ignored archive folder and frozen.
- `.gitignore` now ignores the local file and the archive instead of the old private files.
- Not checked: that a fresh session loads both instruction files. A headless check failed on an expired login; the maintainer checks it in a new session (G0).
- Note for T-20: the source records use non-English marker words; committed code must not hold them as literals.
- Metrics (T-05): review rounds 1, questions back 0, out-of-scope files 0, models Sonnet (writer, translation).

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
