# Status

What is this file? The current state of agentic-sdlc-kit on one page. A new session reads this first and resumes from here.

Last updated: 2026-11-22
Now: Phase 6: T-64a frozen texts and reference guitar done 2026-11-22 (build bench, DEC-082, DEC-083); next T-64c reference and engine tests for steps 2 to 8 and the handoff (no download), or T-64b after the install go-ahead · repository public · code written, last full run 1320 passed, 6 skipped

## Phase

Phase 0 Setup closed: G0 passed 2026-10-29 (maintainer check in a fresh session; see LOG).

Phase 1 Playbook closed: G1 passed 2026-11-02 (`auditor` CONDITIONAL ACCEPT, fixes in T-15, `auditor-mini` ACCEPT; `audits/`).

Phase 2 Evidence closed: G2 passed 2026-11-04 (`auditor-mini` ACCEPT; candidates N-1 to N-4 fixed in T-24a, N-5 moved to G5; `audits/`).

Phase 3 Plugin closed: G3 passed 2026-11-07 (`auditor` CONDITIONAL ACCEPT, fix round T-34a, `auditor-mini` ACCEPT; `audits/`).

Phase 4 MCP server closed: G4 passed 2026-11-13 (`auditor` CONDITIONAL ACCEPT, fix round T-45a to T-45c, `auditor-mini` ACCEPT; `audits/`).

Phase 5 Release closed: G5 passed 2026-11-21 (DEC-081). Planned 2026-11-14 (`cto/2026-11-14_phase5-plan.md`); started 2026-11-14 (T-49, T-54a to T-54c, T-55, T-56a, T-56b, T-56c, T-58, T-59b, T-59a, T-59c to T-59f done; T-52a, T-57 and T-50a done 2026-11-17; T-53 done 2026-11-18; pilot, pre-registration, full run of 42 and T-60 done 2026-11-18 and 2026-11-19; T-50 README done 2026-11-19; T-61 and T-51 done 2026-11-19; T-52 gate G5 done 2026-11-20, T-52b and T-52c done 2026-11-20); bench of kit against plain prompt, 2 arms, 42 runs over 7 tasks (DEC-065, amended by DEC-072). G5 closed 2026-11-21 (install test, seat check with a limit, publish word); v0.1.0 tagged 2026-11-21.

Phase 6 Ongoing: started 2026-11-21, no gate. Build bench (DEC-082, DEC-083): plan `cto/2026-11-21_build-bench-plan.md`, tasks T-63 to T-72.

## Done

- T-64a frozen texts and reference guitar (`developer`, Sonnet, high): `bench/build/` frozen texts (`SPEC.md`, 8 prompts, `answers.md`, `fix-template.txt`, `texts.json` with 17 ids, `spec-map.json`), reference guitar in `bench/build/reference/`, 40 engine tests (35 project, 5 estimator), `arch_check.py`, 33 tests in `tests/test_build_bench.py`; TL checks: 40 of 40 on the reference; 5 pass and 35 fail on a folder with `SPEC.md` only, 0 load errors; worst pitch error 0.0026 cent; customer played it in Chrome; approved 2026-11-22.
- T-63 transcript meter (`developer`, Sonnet, high): `tools/transcript_meter.py` 934 lines, `bench/build/prices.json`, `tests/test_transcript_meter.py` 54 tests, 13 synthetic fixture files, 1 CHANGELOG line; full suite 1287 passed, 6 skipped; TL checks: fixture run 17 lines to 10 messages, 0.037206 USD, `--raw-out` inside the repository refused; review rounds 0; approved 2026-11-21.
- T-62 build bench plan (`cto`): 549 lines, 16 sections; design review by `auditor` (5 High findings, guitar app chosen); DEC-082 and DEC-083 by the customer.
- Phase 5 closed 2026-11-21 (DEC-081): finish plan done, G5-1 to G5-9 met, project frozen at v0.1.0.
- Repository public 2026-11-21 (maintainer): secret scanning, push protection, private vulnerability reporting, fork PR approval for all external contributors, read-only workflow token; rulesets `main` (no deletion, no force push) and `release tags` (`v*`, no deletion, no update), read back through the GitHub API.
- T-52 gate G5 closed (maintainer and TL): install test G5-7 passed, seat check G5-6 passed with a limit (user-level instructions also name the seat), publish word G5-9 given; CHANGELOG `[0.1.0] - 2026-11-21`; tagged `v0.1.0` and pushed 2026-11-21.
- T-52f hosted CI green (`developer`): `tools/metrics/gitstats.py` reads the `Z` suffix that Python 3.10 refused (7 tests), symlink test expects the right error text (1 test); hosted run 44820472971 on bd69407: success, 1239 passed, 0 skipped; approved and pushed 2026-11-21.
- Gate G5 publish-readiness audit (`auditor`, Fable): CONDITIONAL ACCEPT, 1 High, 7 Medium, 7 Low; DEC-080 (80 commits published as they are, 5 line groups accepted); fix round T-52b (`tech-writer`, public pages) and T-52c (`developer`, workflow `permissions` and timeout); `auditor-mini` re-verify: conditions 1 to 3 CLOSED, 4 PARTIAL; 1232 passed, 6 skipped (TL run); committed 80f7bc3.
- T-61 README who did what and what was learned (`tech-writer`), and T-51 v0.1.0, marketplace entry, CI (`developer`): `plugin.json` 0.1.0; marketplace entry `sdlc`; tests workflow on Windows, Python 3.10; `claude plugin validate .` passed; 1232 passed, 6 skipped (TL run); approved 2026-11-19.
- T-50 README (`tech-writer`): `README.md` 103 lines, engineer's note; bench "no difference" wording, scope 2 of 18 per arm, shell-write gap; TL fixed 2 points (role exceeded); approved 2026-11-19.
- T-60 bench results page: `docs/bench-results.md` from `tools/bench_table.py`; category "no difference" on B1 to B6 (18 of 18 full passes per arm, kit to plain 2.51x USD); B7 3 of 3 per arm, 2.15x USD; approved 2026-11-19.
- Bench full run (DEC-078, maintainer's terminal): `full-1` 36 of 36 full passes, 6.48 USD; `full-1-b7` 6 of 6, 3.31 USD; 42 runs, 0 harness errors, 0 reruns.
- T-53 trial on Project C: 2 of 3 tasks (range render, 16th grid cells), 27 committed paths all in contract, 18 scope events all allow, guard saw 1 of 23 developer-written files (shell writes); 1 push passed; rollback equal; `docs/dogfood-2.md` 5 findings.

## Next

- T-64c reference and engine tests for steps 2 to 8 and the handoff (`developer`, no download), or T-64b browser tests after the install go-ahead.
- Then T-65 environment kit; T-66 handoff runner; T-67 dev test (checks the meter against the CLI total; open from T-63: cost-state field map, 9 automated user lines count as `other`, permission waits not separated).
- v0.1.1 triage waits (items under Open questions, plus `docs/toolchain.md` V-10).

## Repository

- Public since 2026-11-21 (DEC-007: only the maintainer changes visibility).
- Every push goes through the pre-push guard. Do not use `--no-verify`.
- Tests: `python -m pip install -r requirements-dev.txt`, then `python -m pytest -q`.
- Language: English for every file (DEC-003, DEC-015).

## Open questions

- R-1 rule question and the 2 lines in `.sdlc/project.md` wait for the maintainer.
- T-53 findings (docs/dogfood-2.md) wait for triage.
- B7 blind review closed, not done (DEC-079).
- T-59 (B7, one large bench task, DEC-070 to DEC-072): checked and frozen at set v3 2026-11-16 (`auditor-mini` ACCEPT); 6 scored runs in `full-1-b7`; Low B7-4 to B7-7 open (README limit lines or G5).
- Bare-word candidate (Low, not triaged): `check-worktree` without dashes still falls to the guard's hook mode and writes 1 event line.
- v0.1.1: G5-F6 skill patterns, G5-F7 second remote, `skills/review/SKILL.md` read-only wording, G5 Low findings F-14 and F-15 partly open (re-verify).
