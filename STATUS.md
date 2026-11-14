# Status

What is this file? The current state of agentic-sdlc-kit on one page. A new session reads this first and resumes from here.

Last updated: 2026-11-14
Now: Phase 4 MCP server closed: G4 passed 2026-11-13 (`auditor-mini` re-verify ACCEPT, all 4 conditions closed); fix commits 4854cbd and ba0c63e pushed; G4 records committed and pushed (8c069c9); DEC-063 adds T-53, evidence from a non-game project, to phase 5; phase 5 plan by `cto` written (`cto/2026-11-14_phase5-plan.md`), DEC-064 to DEC-066 decided; T-49 committed (d95e946); T-54a and T-54b done, waiting for approval; T-54c runs next · repository private · code written, tests green

## Phase

Phase 0 Setup closed: G0 passed 2026-10-29 (maintainer check in a fresh session; see LOG).

Phase 1 Playbook closed: G1 passed 2026-11-02 (`auditor` CONDITIONAL ACCEPT, fixes in T-15, `auditor-mini` ACCEPT; `audits/`).

Phase 2 Evidence closed: G2 passed 2026-11-04 (`auditor-mini` ACCEPT; candidates N-1 to N-4 fixed in T-24a, N-5 moved to G5; `audits/`).

Phase 3 Plugin closed: G3 passed 2026-11-07 (`auditor` CONDITIONAL ACCEPT, fix round T-34a, `auditor-mini` ACCEPT; `audits/`).

Phase 4 MCP server closed: G4 passed 2026-11-13 (`auditor` CONDITIONAL ACCEPT, fix round T-45a to T-45c, `auditor-mini` ACCEPT; `audits/`).

Phase 5 Release: planned 2026-11-14 (`cto/2026-11-14_phase5-plan.md`); not started; bench of kit against plain prompt, 2 arms, 36 runs (DEC-065).

## Done

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
- G0 leftover: a headless session in a clean clone without the local instruction file resumed from the records; DEC-060 keeps the own eval runner (review item 9).
- T-45 G4 audit: CONDITIONAL ACCEPT (`audits/2026-11-11_gate4.md`); 1 High (S-1), 3 Medium, 10 Low; 1065 tests green here and in a fresh clone.
- T-45a S-1 fix: git does not enter nested repositories; a root laid out as a git folder is refused; security row S-18; 1074 tests green; pushed (4854cbd).
- T-45b G4 findings C-1 and C-2 (developer): 1082 tests passed, 6 skipped (TL run); pushed (ba0c63e).
- T-45c G4 documentation items D-1, D-3 items 1 to 3 (item 4 open), D-4 and P-5 (tech-writer, 2 review rounds); live token run in the maintainer's terminal with and without the server: 221 tokens added per session on the plugin path (G4-4, G4-10, DEC-062); pushed (ba0c63e).
- T-45 re-verify (`auditor-mini`): ACCEPT; the 4 G4 conditions closed; 12 of 15 items closed, 1 partly, 2 open (`audits/2026-11-13_gate4-reverify.md`).

## Next

- Maintainer approval and commit of T-54a and T-54b; then T-54c runs in the maintainer's terminal.

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
- Bare-word candidate (Low, not triaged): `check-worktree` without dashes still falls to the guard's hook mode and writes 1 event line.
