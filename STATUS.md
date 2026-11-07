# Status

What is this file? The current state of agentic-sdlc-kit on one page. A new session reads this first and resumes from here.

Last updated: 2026-11-07
Now: Phase 3 closed: G3 passed 2026-11-07; phase 4 next · repository private · metrics code written, tests green

## Phase

Phase 0 Setup closed: G0 passed 2026-10-29 (maintainer check in a fresh session; see LOG).

Phase 1 Playbook closed: G1 passed 2026-11-02 (`auditor` CONDITIONAL ACCEPT, fixes in T-15, `auditor-mini` ACCEPT; `audits/`).

Phase 2 Evidence closed: G2 passed 2026-11-04 (`auditor-mini` ACCEPT; candidates N-1 to N-4 fixed in T-24a, N-5 moved to G5; `audits/`).

Phase 3 Plugin closed: G3 passed 2026-11-07 (`auditor` CONDITIONAL ACCEPT, fix round T-34a, `auditor-mini` ACCEPT; `audits/`).

## Done

- T-11 Playbook: `PLAYBOOK.md`, core and appendices A to I, every claim traced to the source map. The maintainer's end-to-end read is still open (G1).
- T-12 Templates: 7 files in `templates/`, each field traced to the source map; C-26 moved to T-44.
- T-13 Role files: 7 role files and `DEV_RULES.md` revised, each traced to the source map; `docs/portability.md` dropped (DEC-018); one term "customer" (DEC-019). Approved 2026-11-01.
- T-14 G1 audit: CONDITIONAL ACCEPT (2026-11-02); 6 questions answered (DEC-020).
- T-15 G1 fixes: all findings fixed; the maintainer read `PLAYBOOK.md` end to end (2026-11-02), no corrections.
- Phase 2 plan: `cto/2026-11-02_phase2-plan.md`; decisions DEC-021 to DEC-027.
- P-20 record format pass: local format note for the parsers; Project B has data for changelog, log and one audit only.
- T-20 metrics core and text metrics: `tools/metrics/`, M1, M2, M5, M6; 128 tests green; M1 counting rule DEC-028. Committed 2026-11-03.
- T-21 git, audit, decision and task metrics: M3, M8, M9, M12, M13 and the table render; 252 tests green; DEC-029. Committed 2026-11-03.
- T-22 run and T-22a: three sources, reruns byte-identical; Project A parser extended for two more metric-line layouts (DEC-030), 19 of 20 v2 entries parsed; 271 tests green. Committed 2026-11-04.
- T-23 `EVIDENCE.md`: 9 metrics, 21 limits items, tables rendered; DEC-031. Committed 2026-11-04.
- T-24 G2 audit and T-24a (N-1 to N-4 closed): Committed 2026-11-04.
- Phase 3 plan: `cto/2026-11-04_phase3-plan.md`; decisions DEC-033 to DEC-043.
- P-30 plugin facts probe: 14 runs and 1 customer terminal run; results in `docs/toolchain.md`, no result contradicts a decision.
- T-30 skeleton and role files: plugin `sdlc` loads with 7 agents, `agents/` is the role source, 280 tests green; DEC-044. Committed 2026-11-05.
- T-31 scope guard hook: denies and allows in live runs, sub-agent included; 388 tests green.
- T-32 git hook installer: target mode, old hook kept, uninstall restores the hook folder; 437 tests green.
- T-30a the 5 commands: skills, project template, 2 script modes; 498 tests green.
- T-33a snapshot guard: a second `--snapshot` for a label is refused; 502 tests green.
- P-33 rehearsal: passed in the maintainer's own terminal; totals in `docs/dogfood-1.md`.
- T-30b: `init` and `contract` write through the file tools; 505 tests green.
- T-33 real task on Project A: medium task merged by the customer; 39 guard events, 1 deny outside the root, 0 out-of-scope files; kit removed, rollback equal; 9 findings in `docs/dogfood-1.md`.
- DEC-045 triage and T-33b: sub-agents cannot change the developer rules file without a Files in line; 515 tests green.
- T-34 G3 audit: CONDITIONAL ACCEPT (`audits/2026-11-07_gate3.md`); fix round T-34a: line endings, records, G3-7 statement.

## Next

- Phase 4 MCP server: first the 3 open questions, then the CTO phase 4 plan.

## Repository

- Private (DEC-007). Only the maintainer changes visibility.
- Every push goes through the pre-push guard. Do not use `--no-verify`.
- Tests: `python -m pip install -r requirements-dev.txt`, then `python -m pytest -q`.
- Language: English for every file (DEC-003, DEC-015).

## Open questions

- Whether the scope guard allows the session's memory folder outside the root (DEC-037, finding 1).
- Kit opting in to its own scope guard in phase 4 (G3 D-1); exact name or glob for the rules file (G3 D-2).
- N-5 waits for G5 (`TASKS.md`).
