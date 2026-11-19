# Status

What is this file? The current state of agentic-sdlc-kit on one page. A new session reads this first and resumes from here.

Last updated: 2026-11-19
Now: T-60 done (bench results page, category "no difference"); README next · repository private · code written, last full run 1230 passed

## Phase

Phase 0 Setup closed: G0 passed 2026-10-29 (maintainer check in a fresh session; see LOG).

Phase 1 Playbook closed: G1 passed 2026-11-02 (`auditor` CONDITIONAL ACCEPT, fixes in T-15, `auditor-mini` ACCEPT; `audits/`).

Phase 2 Evidence closed: G2 passed 2026-11-04 (`auditor-mini` ACCEPT; candidates N-1 to N-4 fixed in T-24a, N-5 moved to G5; `audits/`).

Phase 3 Plugin closed: G3 passed 2026-11-07 (`auditor` CONDITIONAL ACCEPT, fix round T-34a, `auditor-mini` ACCEPT; `audits/`).

Phase 4 MCP server closed: G4 passed 2026-11-13 (`auditor` CONDITIONAL ACCEPT, fix round T-45a to T-45c, `auditor-mini` ACCEPT; `audits/`).

Phase 5 Release: planned 2026-11-14 (`cto/2026-11-14_phase5-plan.md`); started 2026-11-14 (T-49, T-54a to T-54c, T-55, T-56a, T-56b, T-56c, T-58, T-59b, T-59a, T-59c to T-59f done; T-52a, T-57 and T-50a done 2026-11-17; T-53 done 2026-11-18; pilot, pre-registration, full run of 42 and T-60 done 2026-11-18 and 2026-11-19); bench of kit against plain prompt, 2 arms, 42 runs over 7 tasks (DEC-065, amended by DEC-072).

## Done

- T-60 bench results page: `docs/bench-results.md` from `tools/bench_table.py`; category "no difference" on B1 to B6 (18 of 18 full passes per arm, kit to plain 2.51x USD); B7 3 of 3 per arm, 2.15x USD; approved 2026-11-19.
- Bench full run (DEC-078, maintainer's terminal): `full-1` 36 of 36 full passes, 6.48 USD; `full-1-b7` 6 of 6, 3.31 USD; 42 runs, 0 harness errors, 0 reruns.
- T-53 trial on Project C: 2 of 3 tasks (range render, 16th grid cells), 27 committed paths all in contract, 18 scope events all allow, guard saw 1 of 23 developer-written files (shell writes); 1 push passed; rollback equal; `docs/dogfood-2.md` 5 findings.
- T-50a PLAYBOOK matches the shipped kit (`tech-writer`): line 3 names `EVIDENCE.md`, `docs/eval-results.md`, `docs/bench-results.md`; Appendix H 2 new rows (session start hook, read-only MCP server, optional); CHANGELOG line under `### Changed`; `tests/test_scope_guard.py` 198 passed (TL run).
- T-57 bench results renderer: `tools/bench_table.py` (150 lines; header line per totals file, table per file and arm, table per file, task and arm; no verdict or ratio; exit 2 and nothing written on bad input); `docs/bench-results.md` marker block "Not run yet."; `tests/test_bench_table.py` 23 tests, 3 fixture files; `smoke-2` and `check-2` render equal to the records; 1230 passed, 6 skipped.
- T-52a history scan (`scout`, read only): 72 commits, 72 messages, 35,326 added lines, 268 added paths; public patterns 0 hits; built-in forbidden paths 0; private patterns 0 hits (maintainer's terminal); binary contents not scanned.
- T-59f runner counts visible test changes: `tools/bench_run.py` (`count_test_changes`; per run `tests_changed`, `tests_added`, `tests_deleted`; totals per arm and task with `runs_with_test_changes`; console `tests edited` or `tests untouched`); 3 new tests, 61 in the file; set v3 hash unchanged; no model run; 1207 passed.
- T-59c to T-59e B7 check, fix round and re-verify: `auditor-mini` CONDITIONAL ACCEPT (High 0, Medium 2, Low 5), fixes B7-1 to B7-3 in set v3 (`developer`, 47 hidden tests, hash `e7f25782...2b4b`), re-verify ACCEPT (`audits/2026-11-16_b7-reverify.md`); reference 47 of 47 hidden, 115 visible; unchanged project 20 of 47 pass; 1204 passed.
- T-59a B7 large bench task: `budgetbook` output layer as bench task B7 (`bench/tasks/B7/`, 47 hidden tests in set v3, 45 in v2; 639-line reference patch; 27 fail on the unchanged project in both sets); set v2 hash `6b5154df...8a3e`; 2 review rounds; no model run; 1204 passed.
- T-59b seat size and contract ID format: seat 18 lines (DEC-058 size line; check the contract before delegating); ID format in 3 texts; `check_contract` adds the format on a missing or broken contract (DEC-073); `check-1` 7 of 7 and still `T-FIX-1`; `check-2` 7 of 7, first write parsed; 1195 passed.
- T-56b bench runner: `tools/bench_run.py` (1172 lines, 58 tests); kit arm through `--mcp-config` (DEC-069); smoke-2 on B1 7 of 7 in both arms, 1 run each; 1189 tests green.
- T-58 guard deny text: a main-session deny names /sdlc:contract and the contract format; seat line added; 1131 tests green.
- T-56a bench probes: 5 runs of B1, 1.14 USD; the guard deny stopped 2 of 3 kit runs before T-58; after it the kit run delegated to developer, 7/7; sub-agent marking and cost settled, caps open.
- T-55 bench: sandbox budget ledger (20 modules, 1,511 lines, 115 visible tests) and 6 tasks with hidden tests and reference patches; 1127 tests green.
- T-54c Haiku scope runs: either prompt variant 40 of 40 with the server; default prompt 32 of 40.

## Next

- T-50 README: states the category, the cost ratios, the scope result and the shell-write gap (DEC-075 limit).
- T-51 v0.1.0 and marketplace; T-52 gate G5; then the maintainer says publish.

## Repository

- Private (DEC-007). Only the maintainer changes visibility.
- Every push goes through the pre-push guard. Do not use `--no-verify`.
- Tests: `python -m pip install -r requirements-dev.txt`, then `python -m pytest -q`.
- Language: English for every file (DEC-003, DEC-015).

## Open questions

- N-5 and public git history (review item 32) wait for G5 (`TASKS.md`).
- R-1 rule question and the 2 lines in `.sdlc/project.md` wait for the maintainer.
- T-53 findings (docs/dogfood-2.md) wait for triage.
- B7 blind review (DEC-071) not done; diff pairs only in the local temp folder.
- T-59 (B7, one large bench task, DEC-070 to DEC-072): checked and frozen at set v3 2026-11-16 (`auditor-mini` ACCEPT); 6 scored runs in `full-1-b7`; Low B7-4 to B7-7 open (README limit lines or G5).
- Bare-word candidate (Low, not triaged): `check-worktree` without dashes still falls to the guard's hook mode and writes 1 event line.
