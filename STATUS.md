# Status

What is this file? The current state of agentic-sdlc-kit on one page. A new session reads this first and resumes from here.

Last updated: 2026-11-16
Now: T-59a done (B7 `budgetbook` output layer frozen; set v2 hash `6b5154df...8a3e`; no model run); next T-59c `auditor-mini` check of B7 · repository private · code written, 1204 tests passed

## Phase

Phase 0 Setup closed: G0 passed 2026-10-29 (maintainer check in a fresh session; see LOG).

Phase 1 Playbook closed: G1 passed 2026-11-02 (`auditor` CONDITIONAL ACCEPT, fixes in T-15, `auditor-mini` ACCEPT; `audits/`).

Phase 2 Evidence closed: G2 passed 2026-11-04 (`auditor-mini` ACCEPT; candidates N-1 to N-4 fixed in T-24a, N-5 moved to G5; `audits/`).

Phase 3 Plugin closed: G3 passed 2026-11-07 (`auditor` CONDITIONAL ACCEPT, fix round T-34a, `auditor-mini` ACCEPT; `audits/`).

Phase 4 MCP server closed: G4 passed 2026-11-13 (`auditor` CONDITIONAL ACCEPT, fix round T-45a to T-45c, `auditor-mini` ACCEPT; `audits/`).

Phase 5 Release: planned 2026-11-14 (`cto/2026-11-14_phase5-plan.md`); started 2026-11-14 (T-49, T-54a to T-54c, T-55, T-56a, T-56b, T-56c, T-58, T-59b, T-59a done); bench of kit against plain prompt, 2 arms, 42 runs over 7 tasks (DEC-065, amended by DEC-072).

## Done

- T-59a B7 large bench task: `budgetbook` output layer as bench task B7 (`bench/tasks/B7/`, 45 hidden tests, 639-line reference patch, 27 of 45 fail on the unchanged project); set v2 hash `6b5154df...8a3e`; 2 review rounds; no model run; 1204 passed.
- T-59b seat size and contract ID format: seat 18 lines (DEC-058 size line; check the contract before delegating); ID format in 3 texts; `check_contract` adds the format on a missing or broken contract (DEC-073); `check-1` 7 of 7 and still `T-FIX-1`; `check-2` 7 of 7, first write parsed; 1195 passed.
- T-56b bench runner: `tools/bench_run.py` (1172 lines, 58 tests); kit arm through `--mcp-config` (DEC-069); smoke-2 on B1 7 of 7 in both arms, 1 run each; 1189 tests green.
- T-58 guard deny text: a main-session deny names /sdlc:contract and the contract format; seat line added; 1131 tests green.
- T-56a bench probes: 5 runs of B1, 1.14 USD; the guard deny stopped 2 of 3 kit runs before T-58; after it the kit run delegated to developer, 7/7; sub-agent marking and cost settled, caps open.
- T-55 bench: sandbox budget ledger (20 modules, 1,511 lines, 115 visible tests) and 6 tasks with hidden tests and reference patches; 1127 tests green.
- T-54c Haiku scope runs: either prompt variant 40 of 40 with the server; default prompt 32 of 40.
- T-54a Haiku raw read: the server gap is 2 scope questions (Q02, Q07).
- T-54b prompt variants and `scope_check` description; 1095 tests green.
- T-49 session start hook: the kit introduces itself in opted-in projects; 438 tokens per session; 1088 tests green.
- T-42 decision, lesson, finding, task and log tools; 10 tools in all; 868 tests green; live run works.
- T-44 security pass: 17 findings, 3 High fixed, 0 High open, 2 Medium open in the guard (S-7, S-8); `docs/security.md`; 980 tests green.
- T-44a guard match in bounded time: S-6, S-7, S-8 fixed, 0 security findings open; 992 tests green.
- T-46d eval runner review items 3 to 5: process tree stop, resume refusal on changed settings, seeded condition order; 1052 tests green; committed and pushed (07672c8).
- T-46e runbook says 120 runs (DEC-055): full command `--repeats 1 --budget-usd 3`; eval tests 60 green; 1 CHANGELOG line.

## Next

- T-59c `auditor-mini` check of B7's text against its hidden tests; pilot (B7 and B3); pre-registration; full run of 42 runs.
- T-53 Project C trial, once the maintainer names Project C (DEC-067 cited in TASKS.md but not written).

## Repository

- Private (DEC-007). Only the maintainer changes visibility.
- Every push goes through the pre-push guard. Do not use `--no-verify`.
- Tests: `python -m pip install -r requirements-dev.txt`, then `python -m pytest -q`.
- Language: English for every file (DEC-003, DEC-015).

## Open questions

- N-5 waits for G5 (`TASKS.md`).
- Public git history (review item 32) waits for G5.
- R-1 rule question and the 2 lines in `.sdlc/project.md` wait for the maintainer.
- CTO Q4 scoring rule waits for the pre-registration; Q5 server without the SDK waits for T-51.
- DEC-067 (Project C choice) is cited in TASKS.md but missing from DECISIONS.md; asked again.
- T-59 (B7, one large bench task, DEC-070 to DEC-072): T-59a done 2026-11-16 (B7 frozen, set v2 hash); T-59c next; 0 scored runs.
- Bare-word candidate (Low, not triaged): `check-worktree` without dashes still falls to the guard's hook mode and writes 1 event line.
