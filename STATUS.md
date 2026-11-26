# Status

What is this file? The current state of agentic-sdlc-kit on one page. A new session reads this first and resumes from here.

Last updated: 2026-11-26
Now: Phase 6: T-77 fixes and T-67 dev test part 1 done 2026-11-26; next T-67 part 2 on a fresh setup · repository public · code written, last full run 1424 passed, 15 skipped.

## Phase

Phase 0 Setup closed: G0 passed 2026-10-29 (maintainer check in a fresh session; see LOG).

Phase 1 Playbook closed: G1 passed 2026-11-02 (`auditor` CONDITIONAL ACCEPT, fixes in T-15, `auditor-mini` ACCEPT; `audits/`).

Phase 2 Evidence closed: G2 passed 2026-11-04 (`auditor-mini` ACCEPT; candidates N-1 to N-4 fixed in T-24a, N-5 moved to G5; `audits/`).

Phase 3 Plugin closed: G3 passed 2026-11-07 (`auditor` CONDITIONAL ACCEPT, fix round T-34a, `auditor-mini` ACCEPT; `audits/`).

Phase 4 MCP server closed: G4 passed 2026-11-13 (`auditor` CONDITIONAL ACCEPT, fix round T-45a to T-45c, `auditor-mini` ACCEPT; `audits/`).

Phase 5 Release closed: G5 passed 2026-11-21 (DEC-081). Planned 2026-11-14 (`cto/2026-11-14_phase5-plan.md`); started 2026-11-14 (T-49, T-54a to T-54c, T-55, T-56a, T-56b, T-56c, T-58, T-59b, T-59a, T-59c to T-59f done; T-52a, T-57 and T-50a done 2026-11-17; T-53 done 2026-11-18; pilot, pre-registration, full run of 42 and T-60 done 2026-11-18 and 2026-11-19; T-50 README done 2026-11-19; T-61 and T-51 done 2026-11-19; T-52 gate G5 done 2026-11-20, T-52b and T-52c done 2026-11-20); bench of kit against plain prompt, 2 arms, 42 runs over 7 tasks (DEC-065, amended by DEC-072). G5 closed 2026-11-21 (install test, seat check with a limit, publish word); v0.1.0 tagged 2026-11-21.

Phase 6 Ongoing: started 2026-11-21, no gate. Build bench (DEC-082, DEC-083): plan `cto/2026-11-21_build-bench-plan.md`, tasks T-63 to T-72; shrunk 2026-11-26 (DEC-087).

## Done

- T-77 dev test fixes (`developer`, Sonnet, medium, review rounds 0): launch pins `--permission-mode auto` and `--effort medium`, turns off claude.ai connectors; setup disables them in the 3 config folders; meter matches the fake key placeholder; targeted 80 passed, full suite 1424 passed, 15 skipped; approved and pushed 2026-11-26.
- T-67 dev test part 1 (maintainer's terminal, CLI 2.1.332): setup, launch refusal, separate logins, model, push to bare remote, end-step, transcripts all passed; 4 findings, 3 fixed in T-77, finding 3 (PostToolUse tip text with no hook) open for part 2.
- T-65 environment kit, slim (`developer`, Sonnet, medium): `tools/build_run.py` 677 lines, `bench/build/env/run.ps1` 11 lines, `tests/test_build_run.py` 21 tests; TL checks: 21 passed, launch code read, full suite 1412 passed, 15 skipped; review rounds 0; approved and pushed 2026-11-26 (DEC-087).
- T-74 v0.1.1 for the directory (`developer`, Sonnet, medium): `auditor` on `opus` (DEC-086), `plugin.json` 0.1.1 with icon, homepage, repository, keywords; `.claude-plugin/icon.png` 1024 x 1024; TL checks: `git grep -i fable` 0 hits outside history, bench, eval, toolchain and tests; `claude plugin validate .` passed with 2 warnings; full suite 1391 passed, 15 skipped; review rounds 2; tagged `v0.1.1`.
- T-73 plugin renamed `sdlc` to `sdlc-lead` (`developer`, Sonnet, medium): 17 files, DEC-085; commands `/sdlc-lead:*`, install `sdlc-lead@agentic-sdlc-kit`; TL checks: `claude plugin validate .` passed with 1 warning (no icon); full suite 1399 passed, 6 skipped; review rounds 1; customer check with v0.1.1.
- T-64d build scorer (`developer`, Sonnet, medium): `tools/build_score.py` 417 lines, `tests/test_build_score.py` 38 tests, `tests/fixtures/build_score/`; TL checks: reference at handoff 152 of 152; folder with `SPEC.md` only at step 1: 0 of 59, 0 load errors; blocking-script page at step 1: 0 of 59, 408 s against a 900 s limit (T-64b watch item closed); full suite 1399 passed, 6 skipped; approved 2026-11-23.
- T-64b hidden browser tests (`developer`, Sonnet, high): 71 Playwright tests in `bench/build/hidden/browser/` (69 not retired), `run_browser.py` 228 lines, harness pinned to `@playwright/test` 1.65.1; TL checks: 69 of 69 on the reference; 0 pass, 69 fail, 0 load errors on a folder with `SPEC.md` only; under load 9 of 9 runs 69 of 69 after 1 review round (timeouts, upper bounds from `SPEC.md` stamps); full suite 1361 passed, 6 skipped; approved 2026-11-23.
- T-64c reference and engine tests for steps 2 to 8 and the handoff (`developer`, Sonnet, high): `prompts/handoff.txt` byte-equal to plan section 11; engine tests `step2` to `step7` and `handoff/song.test.mjs`; `spec-map.json` 85 entries, spectrum tests retired at step 6; reference grown to step 8 plus song mode (5 new modules); `tests/test_build_bench.py` 50 tests; TL checks: 93 of 93 on the reference; 8 pass and 85 fail on a folder with `SPEC.md` only, 0 load errors; arch check 0; customer played it in Chrome; approved 2026-11-22.
- T-64a frozen texts and reference guitar (`developer`, Sonnet, high): `bench/build/` frozen texts (`SPEC.md`, 8 prompts, `answers.md`, `fix-template.txt`, `texts.json` with 17 ids, `spec-map.json`), reference guitar in `bench/build/reference/`, 40 engine tests (35 project, 5 estimator), `arch_check.py`, 33 tests in `tests/test_build_bench.py`; TL checks: 40 of 40 on the reference; 5 pass and 35 fail on a folder with `SPEC.md` only, 0 load errors; worst pitch error 0.0026 cent; customer played it in Chrome; approved 2026-11-22.
- T-63 transcript meter (`developer`, Sonnet, high): `tools/transcript_meter.py` 934 lines, `bench/build/prices.json`, `tests/test_transcript_meter.py` 54 tests, 13 synthetic fixture files, 1 CHANGELOG line; full suite 1287 passed, 6 skipped; TL checks: fixture run 17 lines to 10 messages, 0.037206 USD, `--raw-out` inside the repository refused; review rounds 0; approved 2026-11-21.
- T-62 build bench plan (`cto`): 549 lines, 16 sections; design review by `auditor` (5 High findings, guitar app chosen); DEC-082 and DEC-083 by the customer.
- Phase 5 closed 2026-11-21 (DEC-081): finish plan done, G5-1 to G5-9 met, project frozen at v0.1.0.
- Repository public 2026-11-21 (maintainer): secret scanning, push protection, private vulnerability reporting, fork PR approval for all external contributors, read-only workflow token; rulesets `main` (no deletion, no force push) and `release tags` (`v*`, no deletion, no update), read back through the GitHub API.

## Next

- T-67 part 2 on a fresh setup (the harness install needs its own go-ahead). Open from part 1: finding 3 (PostToolUse tip text). Open from T-63: cost-state field map, 9 automated user lines count as `other`, permission waits not separated.
- Then T-68 pilot, T-69 build run and T-72 results page. T-66, T-70 and T-71 are decided after T-69 (DEC-087).
- Customer submits v0.1.1 to the plugin directory on 2026-11-27 (tracking tag `v0.1.1`); v0.1.1 triage waits (Open questions, plus `docs/toolchain.md` V-10).

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
