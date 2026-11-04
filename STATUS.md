# Status

What is this file? The current state of agentic-sdlc-kit on one page. A new session reads this first and resumes from here.

Last updated: 2026-11-04
Now: Phase 3 planned, not started · phase 2 closed · repository private · metrics code written, tests green

## Phase

Phase 0 Setup closed: G0 passed 2026-10-29 (maintainer check in a fresh session; see LOG).

Phase 1 Playbook closed: G1 passed 2026-11-02 (`auditor` CONDITIONAL ACCEPT, fixes in T-15, `auditor-mini` ACCEPT; `audits/`).

Phase 2 Evidence closed: G2 passed 2026-11-04 (`auditor-mini` ACCEPT; candidates N-1 to N-4 fixed in T-24a, N-5 moved to G5; `audits/`).

## Done

- T-01 Decisions: DEC-001 to DEC-012.
- T-02 Record skeleton (0.0.1).
- T-03 Pre-push guard (0.0.1): installed, every push goes through it.
- T-04 Toolchain check: `docs/toolchain.md`, `requirements-dev.txt`; MCP SDK 2.x (DEC-013).
- T-05 Product `CLAUDE.md`: process rules in English, at most 80 lines. Personal rules are kept outside the repository, each rule in one place (DEC-014, DEC-015).
- T-10 Source map: `docs/source-map.md`, 9 sources, 64 concepts; private sources by ID (DEC-016); all 6 process lessons included (DEC-017).
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

## Next

- P-30 plugin facts probe.

## Repository

- Private (DEC-007). Only the maintainer changes visibility.
- Every push goes through the pre-push guard. Do not use `--no-verify`.
- Tests: `python -m pip install -r requirements-dev.txt`, then `python -m pytest -q`.
- Language: English for every file (DEC-003, DEC-015).

## Open questions

- Which real task runs on Project A (DEC-033), picked by the maintainer before T-33.
- N-5 waits for G5 (`TASKS.md`).
