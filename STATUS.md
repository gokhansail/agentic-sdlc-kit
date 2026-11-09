# Status

What is this file? The current state of agentic-sdlc-kit on one page. A new session reads this first and resumes from here.

Last updated: 2026-11-10
Now: Phase 4 MCP server open; T-46c done (not committed, waits for the maintainer), eval runner fixes next · repository private · code written, tests green

## Phase

Phase 0 Setup closed: G0 passed 2026-10-29 (maintainer check in a fresh session; see LOG).

Phase 1 Playbook closed: G1 passed 2026-11-02 (`auditor` CONDITIONAL ACCEPT, fixes in T-15, `auditor-mini` ACCEPT; `audits/`).

Phase 2 Evidence closed: G2 passed 2026-11-04 (`auditor-mini` ACCEPT; candidates N-1 to N-4 fixed in T-24a, N-5 moved to G5; `audits/`).

Phase 3 Plugin closed: G3 passed 2026-11-07 (`auditor` CONDITIONAL ACCEPT, fix round T-34a, `auditor-mini` ACCEPT; `audits/`).

Phase 4 MCP server open: plan `cto/2026-11-07_phase4-plan.md`.

## Done

- T-31 scope guard hook: denies and allows in live runs, sub-agent included; 388 tests green.
- T-32 git hook installer: target mode, old hook kept, uninstall restores the hook folder; 437 tests green.
- T-30a the 5 commands: skills, project template, 2 script modes; 498 tests green.
- T-33a snapshot guard: a second `--snapshot` for a label is refused; 502 tests green.
- P-33 rehearsal: passed in the maintainer's own terminal; totals in `docs/dogfood-1.md`.
- T-30b: `init` and `contract` write through the file tools; 505 tests green.
- T-33 real task on Project A: medium task merged by the customer; 39 guard events, 1 deny outside the root, 0 out-of-scope files; kit removed, rollback equal; 9 findings in `docs/dogfood-1.md`.
- DEC-045 triage and T-33b: sub-agents cannot change the developer rules file without a Files in line; 515 tests green.
- T-34 G3 audit: CONDITIONAL ACCEPT (`audits/2026-11-07_gate3.md`); fix round T-34a: line endings, records, G3-7 statement.
- Phase 4 plan: `cto/2026-11-07_phase4-plan.md`; decisions DEC-046 to DEC-048.
- T-39 guard: main-session memory folder, exact rules path; 536 tests green.
- T-39a the kit opts in: .sdlc/project.md and .claude/settings.json (DEC-047, DEC-049); 540 tests green; checked live and in a desktop app session.
- T-40 server skeleton: read-only stdio server, status tool, root lock, plugin config; 604 tests green; live call works.
- T-40a developers write with the file tools only (DEC-052); the guard logged 4 of 4 writes.
- T-46a eval set: fictional repository, 30 questions, scorer; frozen.
- T-41 scope_check, contract, changed_outside, guard_events tools; 742 tests green; live run works.
- T-42 decision, lesson, finding, task and log tools; 10 tools in all; 868 tests green; live run works.
- T-44 security pass: 17 findings, 3 High fixed, 0 High open, 2 Medium open in the guard (S-7, S-8); `docs/security.md`; 980 tests green.
- T-44a guard match in bounded time: S-6, S-7, S-8 fixed, 0 security findings open; 992 tests green.
- T-46b runner and runbook: `tools/eval_run.py`, 36 tests, subscription login (DEC-054); 1028 tests green; pilot ran 20 of 20 after a stop that did not stop it (LOG 2026-11-09); pilot totals committed in 663d17d.
- T-46c eval runner review fixes: correct needs no error and a right answer; every call estimated at the per-run cap; 1030 tests green; not committed yet.

## Next

- Rest of the eval runner fixes (review items 3 to 6): process tree stop on Windows, resume refuses changed settings, condition order by fixed seed, 120 runs instead of 360.
- Eval runs after the runner fixes (120 runs proposed; the maintainer decides).
- The 5 review decisions with the maintainer (35-item table kept outside the repository).

## Repository

- Private (DEC-007). Only the maintainer changes visibility.
- Every push goes through the pre-push guard. Do not use `--no-verify`.
- Tests: `python -m pip install -r requirements-dev.txt`, then `python -m pytest -q`.
- Language: English for every file (DEC-003, DEC-015).

## Open questions

- N-5 waits for G5 (`TASKS.md`).
- 5 direction decisions from the 2026-11-09 external reviews.
