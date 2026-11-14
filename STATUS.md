# Status

What is this file? The current state of agentic-sdlc-kit on one page. A new session reads this first and resumes from here.

Last updated: 2026-11-14
Now: Phase 4 MCP server closed: G4 passed 2026-11-13 (`auditor-mini` re-verify ACCEPT, all 4 conditions closed); fix commits 4854cbd and ba0c63e pushed; G4 records committed and pushed (8c069c9); DEC-063 adds T-53, evidence from a non-game project, to phase 5; phase 5 plan by `cto` written (`cto/2026-11-14_phase5-plan.md`), DEC-064 to DEC-066 decided; T-49 committed (d95e946); T-54a, T-54b, T-54c done and committed (0f1b0ff, f86de6b); T-55 bench sandbox and 6 tasks done and approved; T-56a probes (5 runs, 1.14 USD) and T-58 guard deny fix (DEC-068) done and approved; next T-56b bench runner · repository private · code written, tests green

## Phase

Phase 0 Setup closed: G0 passed 2026-10-29 (maintainer check in a fresh session; see LOG).

Phase 1 Playbook closed: G1 passed 2026-11-02 (`auditor` CONDITIONAL ACCEPT, fixes in T-15, `auditor-mini` ACCEPT; `audits/`).

Phase 2 Evidence closed: G2 passed 2026-11-04 (`auditor-mini` ACCEPT; candidates N-1 to N-4 fixed in T-24a, N-5 moved to G5; `audits/`).

Phase 3 Plugin closed: G3 passed 2026-11-07 (`auditor` CONDITIONAL ACCEPT, fix round T-34a, `auditor-mini` ACCEPT; `audits/`).

Phase 4 MCP server closed: G4 passed 2026-11-13 (`auditor` CONDITIONAL ACCEPT, fix round T-45a to T-45c, `auditor-mini` ACCEPT; `audits/`).

Phase 5 Release: planned 2026-11-14 (`cto/2026-11-14_phase5-plan.md`); started 2026-11-14 (T-49, T-54a to T-54c, T-55, T-56a, T-58 done); bench of kit against plain prompt, 2 arms, 36 runs (DEC-065).

## Done

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
- Full eval rerun `full-2` (DEC-056): 360 of 360 runs, 0 errors, 2.116 USD list-price estimate; Sonnet 90 of 90 with and without the server, Haiku 83 and 87 of 90; LOG 2026-11-11 (1).
- T-46f eval table renderer: `tools/eval_table.py`, tables in `docs/eval-results.md` from `full-2`; 1065 tests green.
- T-46g eval results text: narrow claim and 10 limits in `docs/eval-results.md`; runbook at 360 runs; committed and pushed (e045d94).
- T-47 graded ceremony (DEC-058): `CLAUDE.md`, `PLAYBOOK.md`, decision template; 1065 tests green.

## Next

- T-56b bench runner (`tools/bench_run.py`), with its own timeout and process stop.
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
- Bare-word candidate (Low, not triaged): `check-worktree` without dashes still falls to the guard's hook mode and writes 1 event line.
