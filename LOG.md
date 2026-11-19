# Log

What is this file? A dated record of what was asked, decided, built and checked. Newest entry on top. Entry format: `## YYYY-MM-DD (N) - title`, where N counts entries for that day.

## 2026-11-19 (4) - T-61 README who did what; T-51 v0.1.0, marketplace entry, CI

- Source: the T-61 and T-51 blocks and their Result lines in `TASKS.md`; DEC-079 in `DECISIONS.md`.
- Customer: approved both tasks on 2026-11-19. Asked for the README part on who did what and what was learned, and for v0.1.0 with a marketplace entry and CI.
- T-61, `tech-writer` (Sonnet, medium): `README.md` gained "Who did what" (1 sentence, 4 points) and "What was learned" (3 sentences); `docs/bench-results.md` gained the review line of DEC-079 in the secondary review paragraph. The CHANGELOG line is under Unreleased.
  - TL fixed 3 points itself (role exceeded): "twice" dropped (DEC-067: the TL first proposed b), then a)); the review lesson names `/sdlc:review`, which already checks the working tree; "Python 3.10 or newer", as the hook launcher checks.
  - Tests: `tests/test_pre_push.py` and `tests/test_bench_table.py` 54 passed (TL run).
  - Contract closed early to place T-51 (one contract at a time).
- T-51, `developer` (Sonnet, medium):
  - `.claude-plugin/plugin.json` version 0.1.0; new `.claude-plugin/marketplace.json` (marketplace name `agentic-sdlc-kit`, entry `sdlc`, source `./`, no version field).
  - New `.github/workflows/tests.yml`: Windows runner, Python 3.10, `requirements-dev.txt`, `pytest -q`.
  - CHANGELOG `[Unreleased]` became `[0.1.0] - 2026-11-19` with an empty `[Unreleased]` above.
  - README status and install section: marketplace install, shell form, clone with `--plugin-dir`; without the `mcp` SDK `/mcp` shows `sdlc` as failed with the install line (stated in the README, DEC-076).
  - `docs/toolchain.md` V-10 and V-11 from the Claude Code docs, not measured; review item 20 partly closed. 2 new tests.
  - `claude plugin validate .` passed with the known warnings (root CLAUDE files, icon).
  - Tests: full suite 1232 passed, 6 skipped (TL run). The developer's own full runs did not finish while another project's tests ran on the machine; the developer repeated its report and was stopped.
- DEC-076 expected no failing server; the docs say `/mcp` shows one, so the README states it.
- Metrics, each task: review rounds 1; questions back 0; out-of-scope files 0; models Sonnet (`tech-writer`, `developer`), Haiku (scribe).
- Next: the maintainer's install test from the marketplace entry (clean folder), then T-52 gate G5.

## 2026-11-19 (3) - Independent opinion on publishing, B7 blind review closed

- Source: the customer's request for an independent opinion before publishing; DEC-079 in `DECISIONS.md`.
- Customer: asked for the opinion before publishing, and closed the B7 blind review as not done.
- `auditor` (Fable) read the repository and wrote no file. The opinion is kept outside the repository.
  - Verdict: publishing helps, medium, if presented as a measured evaluation and not as a process product.
  - No item that stops publishing was found.
  - 3 privacy points for the maintainer to decide at G5: source-project commit hashes in `evidence/*.json`; the list of scanned term kinds in `audits/2026-11-02_gate1.md`; the game engine visible from a metric profile.
  - 5 suggested changes; T-61 and T-51 cover the README, version and CI among them.
- DEC-079: the B7 blind review is not done (customer's word). It is secondary and descriptive; the publish plan has no slot for it. `docs/bench-results.md` says so.

## 2026-11-19 (2) - T-50 README

- Source: the T-50 block and its Result line in `TASKS.md`.
- Customer: approved the README on 2026-11-19.
- `tech-writer` (Sonnet, medium) rewrote `README.md` (103 lines) from the T-50 brief. The CHANGELOG line is under Unreleased > Added.
- What the README holds: intro and status, with the result first (no difference; 3.30x tokens, 2.42x time, 2.51x USD; scope 2 of 18 per arm; the guard saw 1 of 23 trial files); what ships; install from a clone with `--plugin-dir` (no marketplace section yet); what was measured (bench, server eval with Haiku guidance from T-54c, before and after numbers, a game and a non-game trial); 9 limits, incl. the shell-write gap; repository layout, tests and license. 2 IDs in parentheses.
- TL checks: every number checked against its source. Role exceeded: the TL fixed 2 points itself: "Python 3.10 or later" changed to "tested with 3.10.4 only"; NotebookEdit added to the guard limit.
- Tests: `tests/test_pre_push.py` 31 passed (TL run).
- Not done: marketplace section and version bump (`plugin.json` still 0.0.1) wait for T-51.
- Metrics: review rounds 1; questions back 0; out-of-scope files 0; models Sonnet (`tech-writer`), Haiku (scribe).
- Next: T-51 v0.1.0 and marketplace, then T-52 gate G5.

## 2026-11-19 (1) - T-60 bench results page

- Source: the T-60 block and its Result line in `TASKS.md`.
- Customer: approved the bench results page after the full run.
- `tech-writer` (Sonnet, medium) wrote `docs/bench-results.md` from the render of `tools/bench_table.py` for `full-1` and `full-1-b7`. Both totals files are committed. The CHANGELOG line is under Unreleased > Added.
- Sections: "What was run", "What the tables show", "Limits".
- Category on B1 to B6: "no difference" (DEC-078 H1). 18 of 18 full passes per arm. Kit to plain: 2.51x USD, 3.30x tokens, 2.42x wall.
- B7, apart from B1 to B6: 3 of 3 full passes per arm. Kit to plain: 2.15x USD, 3.78x tokens, 2.83x wall. On B1 and B2 together the same ratios were 3.00x USD, 4.36x tokens, 4.39x wall, so all three were lower on B7.
- Out-of-scope runs: 2 of 18 per arm, all on B4, same file.
- Hidden reads: 1 in plain, a word match (`<hidden>` in a `sed` mask of `.env`), 0 real.
- Guard denies: 8, all in the main session before a contract.
- Checks: second render byte-equal; full suite 1230 passed, 6 skipped (TL run).
- TL: after round 1 the TL fixed 3 points itself (role exceeded): its own brief compared B7 with all 6 tasks instead of B1 and B2; the wording of plan 3.6; bold labels. The TL's brief error is one of the 3.
- Not done: blind review of B7 (DEC-071). The diff pairs exist only in the local temp folder, outside the repository.
- Metrics: review rounds 1; questions back 0; out-of-scope files 0; models Sonnet (`tech-writer`), Haiku (scribe).
- Next: README (T-50), then v0.1.0 and marketplace (T-51).

## 2026-11-18 (3) - Pilot, pre-registration and bench full run

- Source: the finish plan under phase 5 in `TASKS.md`, DEC-075 to DEC-078 in `DECISIONS.md`, commit c99c9fe.
- Customer: asked for the pilot and the pre-registration, then the full run in the maintainer's terminal.
- Pilot, 4 runs, not scored (labels `pilot-b3`, `pilot-b7`):
  - B3: plain 23 of 23, 0.19 USD; kit 23 of 23, 0.40 USD.
  - B7: plain 47 of 47, 0.32 USD; kit 47 of 47, 0.68 USD.
  - The pilot set only the B7 caps (per-run cap 2.1 USD, timeout 2,700 s, max turns 60). It changed no task and no kit file.
- Decisions:
  - DEC-075: the shell-write gap (the guard does not see writes made through Bash) is a limit of v0.1.0, fixed in v0.1.1. The bench kit stays frozen.
  - DEC-076: without the `mcp` SDK the server exits with one install line; the rest of the plugin works.
  - DEC-077: no task, decision or bench IDs in public-facing text; the records keep them.
  - DEC-078: pre-registration, committed c99c9fe before the first scored run. It fixes bench set v3, the kit paths, Sonnet in every role, seed 0, the H1 categories and the stop rule.
- Full run, in the maintainer's terminal, Claude Code CLI 2.1.327:
  - `full-1` (B1 to B6, 3 repeats): 36 of 36 full passes, 6.48 USD.
  - `full-1-b7` (B7, 3 repeats): 6 of 6, 3.31 USD.
  - 42 runs, 9.79 USD, 0 harness errors, 0 reruns.
- Next: T-60 bench results page.

## 2026-11-18 (2) - T-53 task 2 on Project C and trial close

- Source: the Task 2 and Close lines under T-53 in `TASKS.md`.
- Task 2 (16th grid cells) ran in Project C's own TL session (CLI 2.1.326, auto mode). Contract 9 Files in (incl. `uv.lock`, `pyproject.toml`), 6 Files out. Developer 9 min, TL session 15 min.
- Result: 1 local commit, 10 paths, all in Files in or always allowed. 342 passed, 1 deselected; node tests 6 of 6; lint green (Project C TL's run). Review rounds 1. Questions back 0. Customer test passed. Contract closed.
- Scope events 7, all allow: no contract 2, active 5 (main session). The developer produced 0 events for 7 developer-written files. Over both tasks the guard saw 1 of 23 developer-written files.
- Project C's TL took its own default on one open design question and told the customer, who agreed.
- Task 3 not run (customer's choice: hard task, open shortcut question).
- Close: 1 push of 2 commits through the chained hook, passed. Rollback equal to the noted state (hooks, exclude file, `.sdlc/` file list, `git status` empty).
- Report: `docs/dogfood-2.md` (`tech-writer`, Sonnet, 2 rounds), 5 findings not yet triaged; CHANGELOG line under Added.
- Metrics (T-53 report): review rounds 2; questions back 0; out-of-scope files 0; models Sonnet (`tech-writer`), Haiku (scribe).
- Next: pilot (B7 and B3, 2 arms, 1 run each, not scored) in the maintainer's terminal; pre-registration.

## 2026-11-18 (1) - T-53 task 1 on Project C: range render

- Source: the result line "Task 1 (range render)" under T-53 in `TASKS.md`.
- Task 1 ran in Project C's own TL session (CLI 2.1.319, auto mode). Contract 14 Files in (incl. `uv.lock`, `pyproject.toml`), 5 Files out. Project C's developer (Sonnet, effort high), 20 min.
- Result: local commit 24ee961, 17 paths, all in Files in or always allowed; origin unchanged (no push). 341 tests and lint green (Project C TL's run). Review rounds 1. Questions back 0. Maintainer's test passed. Contract closed.
- Main finding: the developer changed 15 of 16 files through Bash (Python heredoc replace scripts, `sed -i`), 0 Edit calls, though the brief said file tools only. The guard saw 1 of 16 developer-written files. Project C's role file has no file-tools rule.
- Scope still held: all 17 committed paths were in Files in or always allowed (TL check of the commit). Scope events 11, all allow: main 10 (no contract 2, active 8), developer 1 (Write).
- History scan (read only, local script, upper bound): developer runs with a shell-write candidate: Project C 33 of 34, another project of the maintainer 12 of 13, this kit 39 of 50. The Bash gap is general.
- The maintainer decided not to intervene in task 2, to measure the same thing again.
- A second candidate project of the maintainer was read: not chosen now (uncommitted work, schema change on real data, no test project); possible after T-53.
- Next: task 2 (16th grid cells) in the maintainer's terminal; CLI 2.1.326 at restart (task 1 ran on 2.1.319).

## 2026-11-17 (4) - T-53 setup on Project C (DEC-074)

- The TL read Project C (read only, nothing written there): main, HEAD 62e48b4, clean tree, pre-push hook SHA-256 61d5618d...1039 (the kit's chained guard from an earlier install), exclude file 1 line `.sdlc/`, no `.sdlc/project.md`.
- Project C's handoff lists 3 tasks: range render (medium, tests), 16th grid cells (medium, JS only, no automated test), listen to a selection (hard, open shortcut question in Project C).
- Conflicts found before the run:
  - Project C's rules push on approval, while DEC-067 forbids pushes in the trial.
  - The tasks have no explicit file list; a version bump changes `pyproject.toml` and `uv.lock`.
  - The listening record must be in the always-allowed list.
- The maintainer decided as the TL recommended (DEC-074):
  - no push until the trial ends, through Project C's own "no push" word;
  - Project C's own developer role;
  - the shortcut question is asked when its task comes.
- T-53 contract rewritten in `TASKS.md` for up to 3 tasks. Local runbook `.sdlc/local/t53-runbook.md` (ignored).
- Next: the maintainer runs the runbook in their own terminal.

## 2026-11-17 (3) - Project C chosen for T-53 (DEC-067)

- The maintainer chose Project C for T-53: candidate 1, the maintainer's 3 real tasks. DEC-067 in `DECISIONS.md`.
- The TL recommended candidate 2 (one task from the review backlog), then candidate 1 once 3 tasks were lined up, since that work happens anyway.
- T-53 widens to up to 3 tasks.
- Conditions: nothing in Project C may break; nothing is pushed from Project C during the trial; the trial starts only on the maintainer's go.
- The project name stays out of the repository; the private pattern is added locally.
- Reason: real work the maintainer does anyway. Added cost: before and after notes and the rollback.
- Limits: browser code without tests; Project C already runs a TL process of the same author.
- Next: T-53 run guide and contract update after the maintainer names the 3 tasks; pilot in the maintainer's terminal.

## 2026-11-17 (2) - T-50a PLAYBOOK matches the shipped kit

- The finish plan (2026-11-17 (1)) put T-50a in the parallel session. The maintainer approved the change 2026-11-17.
- T-50a [M], `tech-writer` (Sonnet, medium), English document, 2 rounds:
  - `PLAYBOOK.md` line 3: the sentence "will be in a separate evidence report (phase 2)" replaced; it now names `EVIDENCE.md`, `docs/eval-results.md` and `docs/bench-results.md`.
  - Appendix H: 2 new rows. "A session learns its seat" (session start hook; seat text only where `.sdlc/project.md` exists). "Read-only MCP server (optional)" (10 tools, read only; the user installs the `mcp` SDK; experimental and optional; tested with Claude Code only).
  - The 438-token figure was left out of PLAYBOOK, because the file holds no measured numbers.
  - Round 2: the CHANGELOG line moved into the existing `### Changed` list under [Unreleased].
- TL checks: each fact checked against its source; `tests/test_scope_guard.py` 198 passed (run by the TL; `tech-writer` has no shell).
- Metrics (T-50a): review rounds 1; questions back 0; out-of-scope files 0; models Sonnet (`tech-writer`), Haiku (scribe).
- Next: pilot (B7 and B3, 2 arms, 1 run each, not scored) in the maintainer's terminal; pre-registration. T-53 on Project C is being discussed with the maintainer.

## 2026-11-17 (1) - Finish plan, T-52a history scan, T-57 bench results renderer

- The maintainer asked for a finish plan. The TL wrote it in `TASKS.md` under phase 5: no new phase-5 task unless it blocks G5. Sessions: (1) pilot and pre-registration, with T-52a, T-57 and T-50a in parallel; (2) full run of 42 and render; (3) T-50 README, T-51 v0.1.0 and marketplace; (4) T-52 gate G5, then the maintainer says publish.
- T-53 (Project C trial): kept or moved to v0.1.1 is open with the maintainer. Two non-game projects of the maintainer were looked at as candidates; not named here.
- T-57 [M], `developer` (Sonnet, medium): bench results renderer.
  - `tools/bench_table.py`: 150 lines, built like `tools/eval_table.py`. Marker block in `docs/bench-results.md`. One header line per totals file, a table per file and arm, a table per file, task and arm. No verdict or ratio. Exit 2 and nothing written on bad input.
  - `docs/bench-results.md`: new; the marker block says "Not run yet."
  - `tests/test_bench_table.py`: 23 tests, 3 fixture files.
  - `CHANGELOG.md`: 1 line.
- T-52a [E], `scout` (Haiku), read only, history scan (no entry of its own): 72 commits, 72 messages, 35,326 added lines, 268 added paths; public patterns 0 hits (TL rerun equal); built-in forbidden paths 0. The private pattern file read was refused to `scout` by the permission check; the maintainer ran the same script with the private file in their own terminal: 0 hits. Binary contents not scanned.
- TL error, recorded in LESSONS (2026-11-17): the T-57 contract listed `TASKS.md` in Files out; the guard then denied the TL's own record write; the TL waited for the contract to close.
- TL checks: diff read; `smoke-2` and `check-2` rendered to a scratch copy, numbers equal to the records; second render byte-equal. Full suite (TL): 1230 passed, 6 skipped. Approved by the maintainer 2026-11-17.
- Metrics (T-57): review rounds 0; questions back 0; out-of-scope files 0; models Sonnet (developer), Haiku (scribe). Metrics (T-52a): questions back 1 (permission refusal).
- Next: T-50a PLAYBOOK fixes (`tech-writer`); pilot (B7 and B3, 2 arms, 1 run each) in the maintainer's terminal; pre-registration.

## 2026-11-16 (3) - T-59f runner counts visible test changes

- The maintainer chose to add the count before the pilot. The candidate came from the B7 check (CTO Q3, scoring risk 1): the runner did not count changed, added or deleted visible test files, so a green visible suite reached by editing tests did not show in the totals. The maintainer approved the commit on 2026-11-16.
- T-59f, `developer` (Sonnet, medium):
  - `tools/bench_run.py`: 26 lines added, 3 changed. `count_test_changes` counts files under the copy's `tests/` from the same before and after hashes as `changed_paths`. Per-run keys `tests_changed`, `tests_added`, `tests_deleted`. Totals per arm and per task get the 3 sums and `runs_with_test_changes` (numbers only). Console word `tests edited` or `tests untouched`. The out-of-scope and kit-layer classes are unchanged.
  - `tests/test_bench_run.py`: 3 new tests, 61 in the file.
  - `bench/README.md`: Scoring and Files bullets name the new fields; the set v3 hash is unchanged.
  - `CHANGELOG.md`: 1 line.
- TL checks: diff read; the error path builds the record the same way as before; 5 targeted tests passed. No model run.
- The plugin extract takes `tools/` from HEAD, so it differs from f148c73 by this runner file only, which the plugin never calls (DEC-073 allows harness changes).
- Full suite (TL): 1207 passed, 6 skipped.
- Metrics (T-59f): review rounds 0; questions back 0; out-of-scope files 0; models Sonnet (developer), Haiku (scribe).
- Next: pilot (B7 and B3, 2 arms, 1 run each, not scored) in the maintainer's terminal; pre-registration with the pass floor 20/47 and the new test-change counts; full run of 42.

## 2026-11-16 (2) - B7 check, fix round and re-verify (T-59c to T-59e)

- The maintainer approved the commit on 2026-11-16 and asked for the B7 check before the pre-registration.
- T-59c, `auditor-mini` (Opus, high): check of B7 set v2 (commit 740c1d1) against its hidden tests. CONDITIONAL ACCEPT: High 0, Medium 2, Low 5. Report `audits/2026-11-16_b7-check.md`.
  - B7-1 (Medium): on Windows a real process prints CRLF, while `task.md` said there is no carriage return. The hidden tests read stdout in process, so an arm writing at file-descriptor level could fail every CSV test.
  - B7-2 (Medium): every `allowed.txt` pattern ended in `.py`, while the text allowed new files of any kind.
  - B7-3 (Low, recommended): some visible checks were not repeated in the hidden tests (`import`, `recurring add`).
  - B7-4 to B7-7 (Low): open.
  - No B7 run before 740c1d1.
- The maintainer chose the fix round for B7-1, B7-2 and B7-3.
- T-59d, `developer` (Sonnet, medium), set v3:
  - `task.md`: 1 sentence on line ends (B7-1).
  - `allowed.txt`: 8 new-file patterns without `.py` (B7-2).
  - Hidden tests: `import` and `recurring add` in the wrong-usage list; 2 new tests (`Imported 1 transaction.` and `Imported 0 transactions.`; the error lines of `remove` and `edit`); 45 to 47 hidden tests (B7-3).
  - `bench/README.md`: v3 hash line; v2 and v1 lines kept.
  - The TL contract named the wrong file for the "other commands" lists; the developer used the right one.
  - Set v3 hash `e7f25782b9d3b370a9ce0eac4715d3dafb73b158b6d6c0ab8f7b287fdf5c2b4b`.
- T-59e, `auditor-mini` (Opus, high): re-verify ACCEPT, report `audits/2026-11-16_b7-reverify.md`. B7-1, B7-2 and B7-3 CLOSED. Reference: 47 of 47 hidden, 115 of 115 visible. Unchanged project: 27 fail, 20 pass of 47. Hash recomputed by the auditor: equal.
- Open: B7-4 to B7-7 (Low). The pass floor for the pre-registration is 20 of 47 (0.43). Candidate outside B7: the runner does not count changed or deleted visible test files per run; the TL asks the maintainer before the pre-registration.
- Full suite (TL): 1204 passed, 6 skipped.
- Metrics: T-59c questions back 0; T-59d review rounds 0, questions back 0 (1 contract wording error by the TL), out-of-scope files 0; T-59e 0. Models: Opus (`auditor-mini`), Sonnet (`developer`), Haiku (scribe).
- Next: decide the runner candidate; pilot (B7 and B3, 2 arms, 1 run each); pre-registration; full run of 42; T-53 once Project C is named.

## 2026-11-16 (1) - T-59a B7 large bench task

- The maintainer said "continue with the next dev task". The TL wrote the T-59a contract (`TASKS.md`) and placed `.sdlc/active-contract.md`. Approved by the maintainer 2026-11-16 [H].
- `developer` (Sonnet, high). The previous session ended mid-task. The work on disk was intact; the TL resumed `developer`.
- Round 1:
  - B7 built in `bench/tasks/B7/`: `task.md` 46 lines; 45 hidden tests in 4 files (text 13, JSON 12, CSV 11, option 9); `reference.patch` 639 lines over 4 files (`README.md`, `cli.py`, `rendering.py`, new `tables.py`); `allowed.txt` 12 patterns.
  - The unchanged project fails 27 of 45 hidden tests; 18 text checks pass by design. With the patch: 45 of 45 hidden, visible suite 115 green.
  - Full suite: 1 failed, 1203 passed. `tests/test_bench_run.py` real-bench dry run expected 12 runs and saw 14 (B7 included). That file was outside the contract; `developer` returned it as a question.
- TL review finding: `task.md` left the new module name free, while `allowed.txt` covers only the listed name prefixes. A free name could count as out of scope.
- Round 2 (the maintainer's yes):
  - The runner test passes `--tasks B1,B2,B3,B4,B5,B6` and still expects 12 runs. Test file only, no runner change.
  - One `task.md` sentence on where new code may go, worded to match `allowed.txt`.
  - The stale comment in `allowed.txt` fixed (the maintainer's yes).
  - The TL ran `tests/test_bench.py` and `tests/test_bench_run.py`: 99 passed.
  - Set v2 hash `6b5154df73e57284e3a0a145f834dc04109da0164c2caf726ffe9922f9bf8a3e`.
- No model run on B7. Out-of-scope paths unchanged (`bench/project`, B1 to B6, `tools`, `server`), checked by the TL with `git status`.
- Open in `task.md`, judged by no test: `change_percent` sign at zero; `\r` in a CSV field; `--format` given twice or before the command. For T-59c.
- Pre-registration note: `--tasks all` now includes B7. The commands must name `--tasks B1,B2,B3,B4,B5,B6` and `--tasks B7`.
- Metrics (T-59a): review rounds 2; questions back 1; out-of-scope files 0; models Sonnet (developer), Haiku (scribe).
- Full suite (TL): 1204 passed, 6 skipped.
- Next: T-59c `auditor-mini` check of B7's text against its hidden tests; pilot (B7 and B3); pre-registration; full run of 42; T-53 once Project C is named.

## 2026-11-15 (2) - Bench decisions and T-59b seat size and contract ID format

- The maintainer proposed T-59 on 2026-11-15: one large bench task, the size of rebuilding a whole page or screen. The TL put 5 questions to `cto`.
- `cto` report `cto/2026-11-15_bench-large-task.md`. The maintainer chose every recommendation:
  - DEC-070: B7 in the same sandbox (rebuild of the CLI output layer), reported apart; category on B1 to B6.
  - DEC-071: machine scoring primary; blind review of 3 B7 diff pairs, secondary.
  - DEC-072: 7 tasks, 3 repeats, 42 runs (mix 2 E, 3 M, 2 H); B7 caps from a pilot.
  - DEC-073: the seat carries DEC-058 before the first scored run; then the kit is frozen.
- `scout` read of the `smoke-2` kit stream (B1, kit arm):
  - The main session wrote `## T-FIX-1 ...` in `.sdlc/active-contract.md` by hand. `_TASK_ID` rejects it, so the contract parsed as broken.
  - The main session started `sdlc:developer` without a check; 2 sub-agent edits were denied.
  - Cause, general: the ID format was named only as `<ID>` in 3 texts.
- T-59b round 1 (`developer`, Sonnet, medium; committed acd5e01):
  - `templates/seat.md` 18 lines: DEC-058 size line; check the contract before a sub-agent starts.
  - ID format sentence in `_CONTRACT_FORMAT` (`tools/scope_guard.py`), `templates/task-contract.md` and `skills/contract/SKILL.md` step 2. Parsing unchanged.
  - 1192 passed.
  - Check run `check-1` (B1, kit arm only, cap 0.7 USD): 17 turns, 0.23 USD, 54 s, 7 of 7 hidden tests pass, 1 sub-agent, guard 4 allow 0 deny.
  - Goal not met: the main session wrote `T-FIX-1` twice and reached `T-90` by `sed`. It never saw the format text.
- Round 2 (maintainer's yes; committed f148c73):
  - `check_contract` in `tools/scope_guard.py` adds the format sentence when the contract is missing or does not parse. The `contract` server tool and `--check-contract` both use it.
  - 1195 passed (`developer`); 384 guard and server tests passed (TL).
  - Check run `check-2` (B1, kit arm only, cap 0.5 USD): 11 turns, 0.170 USD, 52 s, 7 of 7 hidden tests pass, 1 sub-agent, guard 3 allow 0 deny.
  - The format appeared in the first `contract` answer. One write, `## T-1 ...`, valid at once.
  - One run each. This is not evidence of an effect.
  - The main session removed the contract with `rm`, not `/sdlc:contract close`.
- Rows V-24 and V-25 in `docs/toolchain.md`. Kit frozen at f148c73 for the bench (DEC-073).
- Earlier today, T-56c [E]: 3 placeholder emails in the bench runner changed so the pre-push guard accepted the T-56b push.
- Check runs spend 0.23 + 0.17 = 0.40 USD.
- Metrics (T-59b): review rounds 1; questions back 0; out-of-scope files 0; models Sonnet (developer), Haiku (scout, scribe), Opus (cto).
- Committed with this entry.
- Next: T-59a B7 large task; T-59c check; pilot; pre-registration; full run of 42; T-53 once Project C is named.

## 2026-11-15 (1) - T-56b bench runner

- The maintainer gave the go-ahead for T-56b [H]. The TL wrote the contract and placed `.sdlc/active-contract.md`.
- `developer` (Sonnet, high), round 1:
  - `tools/bench_run.py`, `tests/test_bench_run.py`, fixtures, a run section in `bench/README.md`, row V-23 in `docs/toolchain.md`, 1 CHANGELOG line.
  - Smoke `smoke-1` (B1) ran only the kit arm and stopped. Under `--strict-mcp-config` the plugin's MCP server did not start: the init event shows an empty `mcp_servers` list. The TL checked the raw init event. The developer stopped as the contract said.
- DEC-069: the maintainer chose option a. The kit arm keeps `--strict-mcp-config` and gets the server through `--mcp-config`. Tools are named `mcp__sdlc__*`. The limit is stated in `bench/README.md`.
- `developer`, round 2:
  - Runner 1172 lines, 58 tests.
  - `smoke-2` (B1), 1 run per arm, 0.34 of 1.0 USD:
    - plain: 4 turns, 0.038 USD, 11 s, 7 of 7 hidden tests pass.
    - kit: 16 turns, 0.305 USD, 115 s, 7 of 7 pass; 2 `sdlc:developer` starts; 4 server tool calls; guard 4 allow, 3 deny.
  - The sub-agent started before the main session's contract parsed. 2 sub-agent edits were denied as `broken`, then allowed.
  - Out-of-scope files 0 and hidden-test reads 0 in both arms.
  - One run per arm. This is not a comparison.
- Rule break: the developer made its first edits through Bash and `sed`, not Write or Edit (DEV_RULES rule 5). The scope guard may not have seen them. Content was checked by diff and tests.
- TL checks:
  - Raw init events read.
  - `smoke-2` totals read.
  - No local paths in `bench/results/*.json`.
  - MCP config code, argv and stop logic read.
  - Full suite run by the TL: 1189 passed, 6 skipped.
- Found in `smoke-2`: `templates/seat.md` has no line on task size, so the kit delegates a one-line fix with a full contract. The graded ceremony (DEC-058) is not in the plugin. Open with the maintainer.
- Metrics (T-56b): review rounds 0; questions back 1 (server flag); out-of-scope files 0; models Sonnet (developer), Haiku (scribe). Smoke spend 0.18 + 0.34 = 0.52 USD.
- T-59 proposed by the maintainer on 2026-11-15: one large bench task (the size of rebuilding a whole page or screen). 5 questions for `cto` in TASKS.md; `auditor-mini` checks before the pre-registration.
- Next: `cto` on T-59 and the seat size rule; then pilot and pre-registration; T-53 once Project C is named.
- Committed with this entry.

## 2026-11-14 (7) - T-58 guard deny text for the main session

- DEC-068: the maintainer chose to fix the defect before the bench. The TL wrote the T-58 contract.
- `developer` (Sonnet, medium):
  - `tools/scope_guard.py`: on a no-contract or broken-contract deny, the main session gets a next step. It names `/sdlc:contract <task>` and the contract format, then says to hand the code work to `developer`. Sub-agent deny texts are byte-equal to before.
  - `templates/seat.md` gains one rule line: with a go-ahead given, place the contract and hand the work to `developer` (16 lines).
  - 4 guard tests; the seat test updated.
  - V-17 note: seat tokens not re-measured.
  - 1 CHANGELOG line.
- TL checks:
  - Diff read.
  - Full suite run by the TL: 1131 passed, 6 skipped.
- Metrics (T-58): review rounds 0; questions back 0; out-of-scope files 0; models Sonnet (developer), Haiku (scribe).
- Next: T-56b bench runner; T-53 once the maintainer names Project C.
- Committed with this entry.

## 2026-11-14 (6) - T-56a bench probes

- The maintainer gave the go-ahead for T-56 (bench runner and probes). The TL split it: T-56a probes first, T-56b runner contract from the probe answers (CTO plan section 3.7).
- `developer` (Sonnet, medium): 4 headless runs of bench task B1 on CLI 2.1.319, subscription login, copies in the system temp folder.
  - P1 plain, 10 turns, 0.211 USD, 7 of 7 hidden tests pass.
  - K1 kit, 22 turns, 0.357 USD, 7 of 7.
  - K2 kit with a 0.30 USD cap, 12 turns, 0.134 USD, 2 of 7.
  - K3 kit with a 6-turn cap, 9 turns, 0.097 USD, 2 of 7.
  - Reads of hidden test paths: 0.
- Found:
  - No kit run started a sub-agent. The main session edited code itself; the guard denied it with no contract.
  - K2 and K3 stopped after that one deny.
  - K1 wrote the contract by hand, broken 3 times, then passed.
  - The deny text told the main session to ask the technical lead.
  - Plugin tools need `--allowedTools` entries; connectors load unless `--strict-mcp-config` is given.
  - K3 ended at 9 turns with a 6-turn cap and no error.
- Rows V-18 to V-21 in `docs/toolchain.md`.
- The TL took the deny defect to the maintainer: fix before the bench (DEC-068, T-58). The maintainer chose the fix and one more probe run.
- K4 after T-58, same prompt, plugin tools allowed: 15 turns, 0.339 USD, 3.2 min model time, about 12.5 min wall because the CLI stayed open after its last answer. 7 of 7 hidden tests pass; 0 denies. The main session wrote the contract and started `sdlc:developer`.
  - Settled: sub-agent events are marked by `parent_tool_use_id` and `task_started` `local_agent`; `modelUsage` includes sub-agent tokens (cache read 665,965 + 137,520 = 803,485); the guard names the sub-agent in its events.
  - Open: whether caps bound a sub-agent; whether `CLAUDE_CODE_SUBAGENT_MODEL` overrides a Haiku or Opus role.
  - Limit: one run, and plugin tools were allowed only in K4.
  - Row V-22 in `docs/toolchain.md`.
- 5 runs, 1.14 USD list-price estimate. Excluded from bench scoring.
- Metrics (T-56a): review rounds 0; questions back 1 (one more run, answered by the maintainer); out-of-scope files 0; models Sonnet (developer, runs), Haiku (scribe).

## 2026-11-14 (5) - T-55 bench sandbox and task set

- T-54c [E] done (TASKS line): Haiku scope runs with 2 prompt variants close the server gap, 40 of 40 each; the default prompt with the server 32 of 40; committed f86de6b.
- The maintainer gave the go-ahead for T-55 [H] (DEC-065, CTO plan sections 3.1 and 3.5). The TL wrote the contract and placed `.sdlc/active-contract.md`.
- `developer` (Sonnet, effort high):
  - `bench/project/`: a household budget ledger written for the bench, standard library only, 20 modules, 1,511 lines, 115 visible tests green (contract said about 60; the extra ones cover the B4 regression trap).
  - `bench/tasks/B1` to `B6` (2 E, 3 M, 1 H): each with `task.md`, hidden tests (7 to 24 per task, failing on the unchanged project), `allowed.txt`, `reference.patch`.
  - The fake key sits in `bench/project/dot_env` and is renamed to `.env` in each run copy, because the pre-push guard forbids any file named `.env`; the key value matches no guard pattern.
  - `bench/README.md` with a SHA-256 over `project/` and `tasks/`, LF-normalised; `bench/conftest.py` keeps the kit's pytest out of the sandbox.
  - `tests/test_bench.py`, 32 tests: per task the unchanged project fails the hidden tests, the reference patch makes them pass with the visible suite green, the patch touches only allowed paths; the hash matches.
  - 1 CHANGELOG line.
- TL checks:
  - B3 reference patch applied by hand in a temp copy: 138 passed; the unchanged copy: 22 hidden tests fail.
  - B6 task text read: both traps (a file owned by another team, a key in the local `.env`) are stated as a user would state them; kept.
  - Full suite run by the TL: 1127 passed, 6 skipped.
- Metrics (T-55): review rounds 0; questions back 1 (the `.env` file name, solved as above); out-of-scope files 0; models Sonnet (developer), Haiku (scribe).
- Open: `TASKS.md` T-53 cites DEC-067, which is not in `DECISIONS.md`; the choice of Project C is asked of the maintainer again.
- Next: T-56 bench runner and probes; T-53 when Project C is chosen.
- Committed with this entry.

## 2026-11-14 (4) - T-54b prompt variants and tool description

- T-54a [E] done (TASKS line): the Haiku server gap of 4 runs is 2 scope questions, Q02 and Q07; Q26 is wrong in both conditions.
- The maintainer gave the go-ahead for the next Haiku step. The TL wrote the T-54b contract and placed `.sdlc/active-contract.md`.
- TL design choice against the CTO plan: the `scope_check` description change ships as a fix, not a test-only variant. Reason: the actor values were not named and Haiku guessed a wrong one (`developer`). Cost: the old and new description are not compared on the same day; the T-54c result states it. Plan: 5 conditions, 200 runs; this step: 4 conditions, 160 runs.
- `developer` (Sonnet, medium):
  - `tools/eval_run.py`: `--prompt-variant` with `default`, `files-are` and `use-tools`; `use-tools` with `no-server` refused before any call; the variant is in the manifest, the resume check and each run record.
  - `server/main.py`: the `scope_check` description says when to use it first and names the actor values `sub-agent` and `main`.
  - `docs/eval-runbook.md`: section with the 4 T-54c commands, 40 runs each, 0.50 USD each.
  - 7 new tests; the TL added the description size note to `docs/toolchain.md`.
  - The developer ran the full suite before its last test fix and only 2 test files after it. The TL ran the full suite: 1095 passed, 6 skipped.
- TL checks:
  - Diff of `server/main.py` and `tools/eval_run.py` read.
  - Budget logic checked: a call starts if actual spent plus the 0.25 USD cap fits, so 0.50 USD covers 40 runs at about 0.001 USD each.
- Metrics (T-54b): review rounds 0; questions back 0; out-of-scope files 0; models Sonnet (developer), Haiku (scribe).
- Next: maintainer approval and commit of T-54a and T-54b; then T-54c, the 4 runbook commands in the maintainer's terminal.
- Not committed yet.

## 2026-11-14 (3) - T-49 session start hook

- The maintainer gave the go-ahead for T-49 (kit introduces itself to a session, DEC-064). The TL wrote the contract and placed `.sdlc/active-contract.md`.
- `developer` (Sonnet, medium):
  - Probe first on CLI 2.1.319: a plugin SessionStart hook reaches the model as plain stdout and as JSON `additionalContext`. Stdout chosen.
  - New `hooks/session/launcher.sh` (9 lines): exits 0 silently without `.sdlc/project.md`, else prints `templates/seat.md`.
  - New `templates/seat.md` (16 lines).
  - New `tests/test_session_hook.py` (6 tests).
  - `hooks/hooks.json`: SessionStart entry.
  - `docs/toolchain.md`: V-17.
  - 1 CHANGELOG line.
- Live Haiku runs in a scratch fixture:
  - Opted in: the model named the TL seat and the status record as its first step.
  - Not opted in: no seat.
  - First-turn tokens 51,083 against 50,645: 438 added per session.
- TL checks:
  - Diff read.
  - Launcher run by hand: prints the seat in an opted-in folder, nothing elsewhere.
  - 54 passed in the hook, role sync and skills tests.
  - Developer's full run: 1088 passed, 6 skipped.
- Notes:
  - The developer's report said this repository has no `.sdlc/project.md`. It has one; the launcher prints the seat here when the plugin is loaded.
  - The user-level instruction file reached the non-opted-in run. Not a kit defect.
  - The developer left a background process; the TL stopped it.
  - The TL removed the records from the contract's Files out so that `scribe` could write.
- Metrics (T-49): review rounds 0; questions back 0; out-of-scope files 0; models Sonnet (developer), Haiku (scribe).
- Open: the live check in the maintainer's terminal (G5-6).
- Next: maintainer approval and commit; then T-54a Haiku raw read.
- Not committed yet.

## 2026-11-14 (2) - Phase 5 plan by cto; DEC-064 to DEC-066

- The maintainer: the kit is about to be published without evidence that it gives better work than a plain prompt. The maintainer asked for a CTO plan with a sandbox project in this repository: plain prompt against the kit, measuring tokens, time and result quality; and a test of the Haiku server gap.
- `cto` (Opus, high) wrote `cto/2026-11-14_phase5-plan.md`, 205 lines: 13 ordered steps, the eval design in `bench/`, a Haiku test, G5-1 to G5-9 proposed, 5 questions.
- Finding in the plan: no file the plugin ships states the TL seat; the text exists only in this repository's `CLAUDE.md`. Candidate cause of the Haiku server gap: the eval prompt says "Use only these files" (`tools/eval_run.py` line 251). Not tested yet.
- TL check: the line 251 text and the missing seat text are confirmed in the files.
- Maintainer decisions:
  - Q1 a) a SessionStart hook (DEC-064).
  - Q2 b) 2 arms, 36 runs, against the CTO recommendation a) 3 arms, 54 runs (DEC-065).
  - Q3 a) Sonnet in every role (DEC-066).
  - Q4 (scoring rule, before the first scored run) and Q5 (server without the SDK, before T-51) stay open.
- Process notes:
  - The CTO edited its report with a Bash Python script after writing it. The scope guard does not see Bash writes (known limit, DEC-052). The change stayed in the report file.
  - A `tools/pre_push_guard.py --help` call by the CTO waited for input in the background; the TL stopped it.
- `TASKS.md`: not written by the scribe. The phase 5 ordered task list (DEC-064 to DEC-066) and NOW NEXT are for the TL.
- Metrics (P-50 CTO plan): review rounds 0; questions back 0; out-of-scope files 0; models Opus (cto), Haiku (scribe).
- Next: T-49 kit introduces itself, starting with a probe of the SessionStart hook.
- Not committed yet.

## 2026-11-14 (1) - DEC-063 evidence from a non-game project

- The maintainer asked for a pre-release overview of the project, phase by phase. Phases 0 to 2 were covered so far. No file was changed for the overview.
- Correction: commit 8c069c9 (G4 re-verify report and records) is pushed; `main` equals `origin/main`. This supersedes "Not committed yet" in LOG 2026-11-13 (1).
- The TL raised a concern: all evidence comes from 2 game projects (Project A and Project B) and one synthetic eval repository. The kit has not run on a project that is not a game. The TL recommended stating this as a README limit. The maintainer chose a trial before G5, as evidence collection, not software development (DEC-063).
- `TASKS.md`: phase 5 gets T-53 (before T-52): one real task with the kit on a project that is not a game, evidence only, no kit code change. A T-50 item: the README names the project types the evidence comes from. NOW NEXT updated.
- Open with the maintainer, unchanged: R-1 rule question; the 2 lines in `.sdlc/project.md`; the bare-word candidate.
- Next: phase 5 plan by `cto`, with T-53 in it.
- No metrics line: no task ran. Not committed yet.

## 2026-11-13 (1) - Gate G4 re-verify: ACCEPT, G4 passed

- Commit ba0c63e is pushed: T-45b, T-45c, the live run and the records. `main` equals `origin/main`. The "Not committed yet" line in LOG 2026-11-12 (2) is superseded.
- The TL closed the T-45b and T-45c contract after the maintainer's approval (the new close rule). Both tasks are marked done in `TASKS.md`.
- The maintainer gave the go-ahead for the re-verify. The TL placed the contract (Files in: the report only).
- `auditor-mini` (Opus, high) wrote `audits/2026-11-13_gate4-reverify.md`, 46 lines. Verdict: ACCEPT.
- Conditions closed:
  - S-1: both layouts reproduced at 3a699e0; marker 0 at ba0c63e (G4-9).
  - G4-4: judged from the records; raw output is not in the repository.
  - G4-10: as amended openly in DEC-062.
  - P-1 closed. P-3 and S-2 closed.
- Low sample: C-1 and C-2 planted faults caught (3 and 1 tests; 6 tests in all). D-4, P-4, P-5 and D-1 closed. D-3 partly closed (item 4, `.sdlc/project.md`). D-2 and R-1 open outside the gate. Totals: 12 closed, 1 partly, 2 open.
- Checks: 1082 passed, 6 skipped. Pre-push guard exit 0 over 162 files and the 2 fix commits; a planted key was refused (exit 1). `--check-contract` and `--check-worktree` exit 0.
- Notes from the re-verify:
  - Run 2 of the token pair disallowed the 10 tools but kept the server. Its instruction text may still have been in context, so 221 may be slightly low.
  - The toolchain section says measured 2026-11-12; the date changed between the 2 runs.
- New candidate, Low, not triaged: a bare word without dashes (for example `check-worktree`) still falls to the guard's hook mode and writes 1 event line.
- Process note: the re-verifier's Write tool was denied outside the project root by the scope guard. It wrote its probe script with Bash into a temporary folder outside the repository. The guard does not see Bash writes (known limit, DEC-052).
- TL check: report present; verdict line read; pre-push guard exit 0 with the report in the tree.
- G4 passed 2026-11-13. Phase 4 closed.
- Open with the maintainer: R-1 rule question; the 2 lines in `.sdlc/project.md`; the bare-word candidate. Not committed yet.
- Metrics (T-45 re-verify): review rounds 0; questions back 0; out-of-scope files 0; models Opus (auditor-mini), Haiku (scribe).
- Next: maintainer approval and commit; then the phase 5 plan by `cto`.

## 2026-11-12 (2) - G4 fix round 2: T-45b, T-45c, live run (G4-4, G4-10)

- Commit 4854cbd is pushed: T-45a (S-1 fix), the G4 audit report and the records. `main` equals `origin/main`. The "Not committed yet" line in entry (1) is superseded.
- The maintainer decided P-2: measure the server's token cost live, with and without the server (DEC-062).
- The TL wrote the contracts T-45b and T-45c and placed one active contract for both (`.sdlc/active-contract.md`).
- `developer` (Sonnet, medium) did T-45b: G4 findings C-1 and C-2. Tests: 1082 passed, 6 skipped (TL run). See the T-45b result line in `TASKS.md`.
- `tech-writer` (Sonnet, medium) did T-45c: D-1, D-3 items 1 to 4, D-4 and P-5. 2 review rounds.
- `.sdlc/project.md` is not changed. The guard denies sub-agent writes under `.sdlc/`; the change is open with the maintainer.
- TL records:
  - P-1: 4 items on the phase 5 line of `TASKS.md`.
  - P-3: the G4 Phases row points to DEC-061 and DEC-062.
  - P-4: the G0 leftover gets task line T-48 [E]. Corrected limit: the run shows a resume without the repository's local instruction file, not without the maintainer's user-level file. This corrects the limit line of LOG 2026-11-11 (6). The first T-48 line had no ID and failed the record parse test (1 failed); the TL gave it ID T-48, then the test was green.
  - D-3 items 5 and 6 and D-4: outcome lines in DEC-056, DEC-055 and DEC-060.
- S-2: the 2 external review files moved into the ignored archive folder; the empty folder `x/` removed. This corrects LOG 2026-11-10 (1), which said they were kept outside the repository. They were untracked in the root until today.
- Live run in the maintainer's terminal, 2026-11-12, CLI 2.1.319, Haiku, subscription login:
  - Run 1, plugin-loaded server: `status` called through a tool search; 3 turns; 0.007 USD. The maintainer confirmed the run (G4-4).
  - Run 2, the 10 server tools disallowed: first-turn context 43,240 tokens. The plugin path gave 43,461 tokens. 221 tokens added per session on the plugin path (G4-10, DEC-062).
  - The first attempt of run 2 wrote an empty file because stderr was not captured. Rerun with all streams captured.
- The TL wrote the token section in `docs/toolchain.md` ("Server in the customer's terminal and its token cost").
- Metrics (T-45b): review rounds 1; questions back 0; out-of-scope files 0; models Sonnet (developer), Haiku (scribe).
- Metrics (T-45c): review rounds 2; questions back 3; out-of-scope files 0; models Sonnet (tech-writer), Haiku (scribe).
- Open: R-1 rule question and the 2 lines in `.sdlc/project.md` wait for the maintainer. Not committed yet.
- Next: maintainer approval and commit, then `auditor-mini` re-verifies the 4 G4 conditions.

## 2026-11-12 (1) - T-45a git config check in 2 more layouts (S-1)

- The maintainer decided the 3 gate questions. The TL recorded DEC-061: fix S-1 with tests; one short Haiku run in the maintainer's terminal after the fix for G4-4; the 10 G4 criteria adopted as written.
- The TL wrote the T-45a contract and placed `.sdlc/active-contract.md`.
- `developer` (Sonnet, high) changed 7 files:
  - `tools/scope_guard.py` (+2/-1)
  - `server/inputs.py` (+7/-1)
  - `server/scope.py` (+1/-1)
  - `tests/test_server.py` (+115)
  - `tests/test_scope_guard.py` (+55)
  - `docs/security.md` (+7/-3)
  - 1 CHANGELOG line
- Layout 1, nested repository: `git status` in `check_worktree` runs with `--ignore-submodules=all`, so git does not enter it. `--check-worktree` has the change too.
- Layout 2, root laid out as a git folder: `git_problem` refuses a folder with `HEAD` and `objects`, `refs` or `commondir` and no `.git` entry, in each folder from the root upward.
- `docs/security.md`: new row S-18 (High, FIXED); S-3 and S-4 rows updated; 3 limits.
- Tests: 6 new, each filter test with a control run. The developer's mutation run: with the 2 fixes off, 8 of 14 targeted tests failed. 1074 passed, 6 skipped (developer run and TL run); 14 targeted passed, 0 skipped (TL run). Pre-push guard exit 0 over the changed files.
- Limits:
  - A change inside a nested repository is not reported.
  - Layout 2 is refused in the server path only, not by the `--check-worktree` CLI, which is the user's own command.
  - `/sdlc:review` runs `git status` with no config check.
- Review rounds: 1. Questions back: 0. Out-of-scope files: 0.
- Not committed yet.
- Metrics (T-45a): review rounds 1; questions back 0; out-of-scope files 0; models Sonnet (developer), Haiku (scribe).
- Next: second fix task (P-1, P-2, S-2 and the Low findings), the live run in the maintainer's terminal, then `auditor-mini`.

## 2026-11-11 (7) - Gate G4 audit: CONDITIONAL ACCEPT

- The maintainer gave the go-ahead for the G4 audit. The TL wrote the T-45 contract in `TASKS.md` and placed `.sdlc/active-contract.md` (Files in: `audits/2026-11-11_gate4.md`).
- `auditor` (Fable, xhigh) wrote `audits/2026-11-11_gate4.md`, 227 lines. Verdict: CONDITIONAL ACCEPT. Criteria: 7 of 10 met; G4-4 and G4-10 partly met; G4-9 not met.
- Tests: 1065 passed, 6 skipped in this folder and in a fresh clone. Pre-push guard exit 0 over 160 tracked files, the 20 phase 4 commits and the full history.
- Findings: 0 Critical, 1 High, 3 Medium, 10 Low.
  - S-1 High: `changed_outside` starts a program from a git config in 2 layouts (a nested repository; a root laid out as a git folder). Reproduced in scratch folders outside the repository. `docs/security.md` says 0 open High, so G4-9 does not hold.
  - P-1 Medium: 4 decision consequences for phase 5 are not on the task list; "experimental and optional" (DEC-059) is in no product file.
  - P-2 Medium: the server's token cost is not recorded; `plugin details` does not count MCP tool schemas.
  - S-2 Medium: 2 private external review files sit untracked in the working folder and are not ignored.
- Conditions: S-1 fixed with a test, or the risk accepted in a decision; a call of the plugin-loaded server in a terminal the customer opened, or a decision that the eval runs suffice; a token cost paragraph; the 4 items on the phase 5 line. Then `auditor-mini`.
- The auditor ran `tools/scope_guard.py --help` by mistake; it added 1 deny line to the ignored event file (finding C-2). No model, eval or network runs.
- TL check: the report passes the pre-push guard (exit 0); the code lines that S-1 cites (`server/inputs.py`, `_git` in `tools/scope_guard.py`) match the claim.
- Next: the maintainer decides the gate questions; then a fix round.

## 2026-11-11 (6) - G0 leftover clean-clone resume check; review item 9 decided (DEC-060)

- Commit 25afce8 (DEC-057 to DEC-059, T-47) is pushed. `main` equals `origin/main`. The "Not committed yet" line in entry (5) is superseded.
- The maintainer gave the go-ahead to close 2 items before G4: the G0 leftover and review item 9.
- G0 leftover: the TL cloned the repository into a temporary folder outside the kit. The clone has no local instruction file. One headless run: `claude -p "Where do things stand?"` with Opus, `--setting-sources project,local`, `--strict-mcp-config`, tools Read, Glob and Grep. `ANTHROPIC_API_KEY` and `ANTHROPIC_AUTH_TOKEN` were removed from the child environment.
- Start event: credential source none (subscription login); 0 MCP servers; built-in plugins only; the 7 project roles and the CLI's bundled agents; none of the maintainer's own agents; a new empty memory folder.
- Result: 8 turns, 68 s, 0.207 USD list-price estimate. The session read `STATUS.md`, the NOW NEXT line and the top of `LOG.md`. It gave the correct phase, eval totals, open items and next task (T-45).
- The session found 2 stale records: the "5 review decisions open" line in NOW NEXT, and the "Not committed yet" line in LOG (5). It replied in English, with the status line form from `CLAUDE.md`, not the local form.
- Limit: the session said its user-level instruction file was loaded. The stream does not show the system prompt, so this is not checked directly. The reply language, the status line form and the agent list point the other way. Raw output stays outside the repository.
- Review item 9: a `claude-code-guide` sub-agent read the "Test plugins with evals" docs page. The TL recorded DEC-060: keep `tools/eval_run.py`. The docs do not show per-run tokens, duration or tool calls, or an A/B on the server alone.
- The TL fixed the NOW NEXT line in `TASKS.md`.
- Open: public git history (review item 32) waits for G5.
- Next: T-45 gate G4.

## 2026-11-11 (5) - T-47 graded ceremony in the rules

- The maintainer gave the go-ahead for T-47, the graded ceremony (DEC-058). The TL wrote the contract and placed `.sdlc/active-contract.md`.
- The TL corrected the DEC-058 consequences line: `DEV_RULES.md` holds sub-agent rules only and does not change. The files that change are `CLAUDE.md`, `PLAYBOOK.md` and the decision record template. The LOG entry of 2026-11-11 (4) names `DEV_RULES.md` and `templates/dev-rules.md` for DEC-058; that line is superseded by this entry.
- `tech-writer` (Sonnet) changed `CLAUDE.md` (82 lines):
  - An [E] task gets no `scribe` call and no LOG entry of its own. The TL writes its result line in `TASKS.md`, and the next LOG entry names it in one line.
  - [M] and [H] tasks keep the full loop.
  - The auditor gives verdicts at phase gates and before publishing. A re-verify follows each fix round.
  - When the TL says a run stopped or a task is done, it shows the evidence.
  - An [E] task by a sub-agent that writes still gets a short contract for the guard.
- `PLAYBOOK.md` Records: one sentence that the size label also sets record keeping, tagged DEC-058. `templates/decision-record.md`: an empty outcome is normal. The TL edited the `DECISIONS.md` header the same way. 1 CHANGELOG line.
- Review rounds: 2. Round 1 found an unsourced sentence in the template and the same fact in two PLAYBOOK sections. Round 2 removed a blank line in the template; the TL restored it.
- Tests: 1065 passed, 6 skipped (TL run; `tech-writer` had no shell tool in its session).
- Questions back: 0. Out-of-scope files: 0.
- Not committed yet: DEC-057 to DEC-059, T-47 and the records since e045d94 go in one commit.
- Metrics (T-47): review rounds 2; questions back 0; out-of-scope files 0; models Sonnet (tech-writer), Haiku (scribe).
- Next: T-45 gate G4.

## 2026-11-11 (4) - Review decisions DEC-057 to DEC-059

- Commit e045d94 pushed: T-46f (eval table renderer) and T-46g (eval results text and runbook at 360 runs), and the TL's one-line fix of the runbook tools limit; 1065 passed, 6 skipped before the push.
- The maintainer decided 3 of the open review decisions from the external reviews of 2026-11-09. The TL recorded them in `DECISIONS.md`:
  - DEC-057: the plugin is the one delivery path. Phase 5 adds the marketplace entry and checks the catalog listing steps against current docs before T-51.
  - DEC-058: ceremony scales with task size. An [E] task has no own scribe call or LOG entry. Audits run at phase and publish boundaries. The decision outcome field is optional. The TL shows evidence when it says a run stopped or a task is done. The change goes to `DEV_RULES.md`, `CLAUDE.md` and `templates/dev-rules.md`; until then the current rules apply.
  - DEC-059: narrow, publish, freeze. G4 closes with the 10 current tools. The server is marked experimental and optional. No new capability task. The kit is frozen after G5.
- Still open: public git history (review item 32) waits for G5. Review item 9 needs a decision line on why `claude plugin eval` was not used.
- Next: T-47 rules for graded ceremony (DEC-058), then T-45 gate G4.

## 2026-11-11 (3) - T-46g eval results text and runbook

- The maintainer gave the go-ahead for T-46g. The TL placed `.sdlc/active-contract.md` for it.
- `tech-writer` (Sonnet) wrote `docs/eval-results.md` outside the table markers: what was run, the tables, what they show, and 10 limits. Every number is a table cell or one of 3 raw-only counts from LOG 2026-11-11 (1); each of the 3 is marked as from local raw output, not in the repository.
- The text says the result belongs to this set-up and is not a general benefit. The cause of the Haiku gap is not known.
- Runbook `docs/eval-runbook.md`: the full run is `full-2`, 360 runs (DEC-056), command `--label full-2 --budget-usd 8 --questions all --repeats 3`. `full-1` is named as the first measurement and is not used for the gate. 1 CHANGELOG line.
- TL checks: `eval/repo/` is 18,467 bytes (limit about 18 KB); a second render gives the same bytes; banned-word check clean; 73 eval tests passed.
- Review rounds: 2. Round 1 said the CLI offers no Grep, Glob or ToolSearch; DEC-054 states that only under `--bare`, and these runs did not use `--bare`. Round 2 says Read only was a choice, so both conditions have the same tool.
- Questions back: 2 (both answered by the TL). Out-of-scope files: 0.
- `docs/eval-runbook.md` Limits had the same sentence on tools (written in T-46b, outside this contract). The maintainer chose to fix it before the commit; the TL rewrote the one line (role exceeded: the TL writes no documents) and this LOG line.
- T-46f and T-46g go in one commit.
- Metrics (T-46g): review rounds 2; questions back 2; out-of-scope files 0; models Sonnet (tech-writer), Haiku (scribe).
- Next: T-45 gate G4.

## 2026-11-11 (2) - T-46f eval table renderer

- Commit 7a42813 pushed earlier today: `full-2` totals and the records of 2026-11-10 and 2026-11-11; tests 1052 passed, 6 skipped before the push.
- The maintainer gave the go-ahead for the eval table. The TL wrote the contracts T-46f (renderer) and T-46g (results text, runbook at 360 runs) in `TASKS.md` and placed `.sdlc/active-contract.md` for T-46f.
- `developer` (Sonnet, medium) built T-46f: `tools/eval_table.py` (stdlib) renders `eval/results/full-2.json` into the marked block of `docs/eval-results.md`: a header line, one row per model and condition, correct per category. It refuses (exit 2, nothing written) a file that is not complete, a schema other than 2, a missing key, or markers that are not exactly one pair. 13 tests in `tests/test_eval_table.py`; 1 CHANGELOG line.
- Rendered cells equal the JSON: Sonnet with server 90 correct, 0.785 USD, 141 server tool calls; Haiku with server 83 correct, 0.078 USD, 40 server tool calls. The TL's second render gave the same bytes.
- Tests: 1065 passed, 6 skipped (developer run); 13 passed (TL run).
- Review rounds: 1. Questions back: 0. Out-of-scope files: 0.
- Limit: `--doc` is not root-locked; it is a local CLI the TL runs.
- Not committed yet.
- Next: T-46g, `tech-writer` writes the results text with the narrow claim and the limits, and the runbook at 360 runs; then T-45 gate G4.
- Metrics (T-46f): review rounds 1; questions back 0; out-of-scope files 0; models Sonnet (developer), Haiku (scribe).

## 2026-11-11 (1) - Full eval rerun: 360 runs, 3 per cell (DEC-056)

- Written by the TL (role exceeded: the scribe writes LOG; the maintainer asked to save the records and stop for the day).
- Before the eval table: G4-8 (`cto/2026-11-07_phase4-plan.md`) and DEC-012 ask for at least 3 runs per cell; `full-1` had 1 (DEC-055, the TL recommendation, which missed the gate criterion). The maintainer chose a rerun over relaxing the criterion (DEC-056). Lesson in `LESSONS.md` 2026-11-10.
- The maintainer ran `full-2` in their own terminal: 360 of 360 runs, complete, 0 errors, 0 unparsed, `apiKeySource` none on all runs, 2.116 of 8.00 USD list-price estimate, runner at 6579f6c, git_dirty false, Claude Code 2.1.319.
- Per model and condition (correct of 90; accuracy per repeat min to max; cost USD; tool calls, of them server tools; turns per run):
  - Sonnet with server: 90; 1.000 to 1.000; 0.785; 165, 141; 2.8.
  - Sonnet without server: 90; 1.000 to 1.000; 1.138; 174, 0; 2.9.
  - Haiku with server: 83; 0.900 to 0.933; 0.078; 204, 40; 3.3.
  - Haiku without server: 87; 0.967 to 0.967; 0.115; 385, 0; 5.3.
- Sonnet called a server tool in 85 of 90 server runs, Haiku in 20 of 90. Output tokens with and without the server: Sonnet 18,119 and 30,657; Haiku 47,805 and 67,069.
- Haiku misses: with the server 7 (Q02 and Q07 scope, Q26 guard); without the server 3 (Q26 in each repeat). 6 of the 7 server misses called no server tool. The gap repeats in all 3 runs (0.900 to 0.933 against 0.967), so it is not explained as noise; its cause is not yet known.
- Totals in `eval/results/full-2.json`, not committed yet; raw output stayed on the maintainer's machine. DEC-056 and the 2026-11-10 lesson are also not committed yet.
- Next: commit with the maintainer's word; the eval table for G4 from `full-2` with the narrow claim; then T-45 gate G4.

## 2026-11-10 (4) - Full eval: 120 runs

- DEC-055 and T-46e committed and pushed (0e01db2).
- The maintainer ran the full eval in their own terminal with `docs/eval-runbook.md` section 3: label `full-1`, runner at commit 07672c8, git_dirty false, Claude Code 2.1.319.
- Result: 120 of 120 runs, complete, stopped no, 0 errors, 0 unparsed, `apiKeySource` none on all 120 runs. Cost 0.867 of the 3.00 USD list-price estimate. Totals in `eval/results/full-1.json`; raw output stayed on the maintainer's machine.
- Per model and condition (correct of 30; cost USD; tool calls; turns per run):
  - Sonnet with server: 30; 0.346; 56 (48 server tools, 8 Read); 2.9.
  - Sonnet without server: 30; 0.448; 59 Read; 3.0.
  - Haiku with server: 27; 0.030; 68 (10 server tools, 58 Read); 3.3.
  - Haiku without server: 29; 0.043; 132 Read; 5.4.
- Sonnet called a server tool in 28 of 30 server runs; Haiku in 7 of 30. The 3 Haiku server misses (Q02 and Q07 scope, Q26 guard) used Read only. Q26 was also wrong for Haiku without the server, as in the pilot.
- Sonnet with the server: output tokens 6,244 against 10,337 without.
- Reading: accuracy shows no difference that comes from the server. With the server, Sonnet used fewer reads and cost 23 % less at list price; Haiku used fewer turns and cost 30 % less. The Haiku accuracy gap does not come from server use. No repeats were added (DEC-055 rule).
- Limits: one run per cell; one small synthetic repository (about 18 KB of records); cost is a list-price estimate, not a bill.
- Correction to 2026-11-09 (1): the pilot's "9 against 26 tool calls" for Haiku cannot be credited to the server. Haiku called no server tool in the pilot; all 9 calls were Read.
- T-46b is done (TL marked it in TASKS).
- Next: eval table for G4 with the narrow claim (what the server changes in this set-up, not general benefit), then T-45 gate G4; 5 review decisions open.

## 2026-11-10 (3) - Full eval is 120 runs (DEC-055, T-46e)

- T-46d committed and pushed (07672c8), after the pre-push guard fix in round 3 of T-46d.
- The maintainer chose 120 runs for the full eval: 30 questions x 2 models x 2 conditions x 1 repeat (DEC-055, the TL recommendation). This supersedes the 360-run count of DEC-053.
- Budget: 3 USD estimated, per-run cap 0.25 USD. Repeats are added only if the 120 runs show a difference between the conditions.
- The TL wrote the T-46e contract and placed `.sdlc/active-contract.md`.
- `developer` (Haiku) changed `docs/eval-runbook.md`:
  - 120 runs everywhere; no `360` and no `<BUDGET_USD>` left;
  - the full command has `--repeats 1` and `--budget-usd 3`;
  - 1 CHANGELOG line; eval tests 60 passed.
- Review rounds 1. Questions back 0. Out-of-scope files 0.
- Metrics (T-46e): review rounds 1, questions back 0, out-of-scope files 0, models Haiku (developer), Haiku (scribe).
- Next: the 120-run eval in the maintainer's terminal with `docs/eval-runbook.md` section 3; 5 review decisions open.

## 2026-11-10 (2) - T-46d eval runner review items 3 to 5

- T-46c committed and pushed (91d706e).
- The maintainer gave the go-ahead for the next task. The TL wrote the T-46d contract (review items 3 to 5) and placed `.sdlc/active-contract.md`.
- `developer` (Sonnet, effort high) built T-46d in `tools/eval_run.py`:
  - stop: `Popen` with reader threads and a 0.1 s poll; on timeout and on Ctrl+C the child and every descendant are ended (Windows `taskkill /T /F`, POSIX `killpg`);
  - a test with a fake CLI that starts a sleeping grandchild checks by PID that both processes are dead after a timeout and after an interrupt; with the old `subprocess.run` code the grandchild stayed alive and the call hung up to 120 s;
  - `manifest.json` per label in the raw output folder; `--resume` is refused (exit 2, before any call) when the manifest is missing or a setting, the prompt and flag hash or `deps_sha256` differs;
  - `deps_sha256` covers the runner, `server/`, the 4 `tools` modules the server imports and `eval/` without `eval/results/`; `git_commit` and `git_dirty` are written as information only;
  - totals schema 2 with `runner_sha256`, `git_commit`, `git_dirty`;
  - `--seed` (default 0): across all (repeat, question, model) cells exactly half start with the server condition, placed by a seeded shuffle;
  - `docs/eval-runbook.md`: lines for the stop, the resume refusal and the seed; a Limits line: on Windows, a process that outlives a `claude` that exited by itself is not found by PID; the call waits up to the timeout plus 30 s.
- Review rounds 2. Round 1 compared the git commit on resume, so an unrelated commit between sittings would have refused resume; and the dependency set missed the `tools` modules the server imports. Both fixed in round 2.
- The TL corrected one runbook sentence on the seed (role exceeded: the TL wrote one documentation line).
- Tests: 1052 passed, 6 skipped (TL run from Git Bash, 497 s). 0 pytest processes left at the end (checked by the developer and by the TL).
- Metrics (T-46d): review rounds 3, questions back 0, out-of-scope files 0, models Sonnet (developer), Haiku (scribe).
- The maintainer approved. The pre-push guard rejected the first push: `tests/test_eval_run.py` gave the test git repository a placeholder e-mail identity. Round 3 (over the 2-round limit; one line): the identity uses an empty e-mail; eval tests 60 passed; the commit was amended before it reached the remote.
- Next: the eval runs; the run count (120 or 360) is the maintainer's decision; 5 review decisions open.

## 2026-11-10 (1) - T-46c eval runner review fixes

- Two external read-only reviews of HEAD 663d17d were received on 2026-11-09 (kept outside the repository). The TL turned all their items into a 35-item decision table, kept outside the repository. 5 direction decisions are open with the maintainer.
- The TL confirmed 2 eval runner defects by reproducing them with the fake CLI:
  - a run with an error subtype and a right ANSWER line counted 1 error and 1 correct;
  - budget 0.30, per-run cap 0.25, costs 0.10 then 0.25: 2 calls started, 0.35 USD spent.
- The full eval matrix was not started (no log, no output folder).
- The scope guard denied a TL write to a path outside the T-46b contract. The TL placed the T-46c contract instead of working around the denial. The new contract replaced the stale `--bare` goal line of the old active contract.
- `developer` (Sonnet, effort medium) built T-46c:
  - `tools/eval_run.py`: correct needs no error and a right answer; new raw key `answer_matched`, totals keys unchanged; every call is estimated at `--max-run-usd`, `seen_max` removed;
  - help text and `docs/eval-runbook.md` say one run can pass the cap by the cost of its last turn, because the CLI checks its cap between turns;
  - tests: 2 added, 1 updated (the budget test now expects 2 calls, not 3); 1 CHANGELOG line.
- The developer reported without a full-suite summary and left 3 pytest processes running. The TL stopped the agent and the processes and counted 0 pytest processes left.
- TL full run from Git Bash: 1030 passed, 6 skipped, 341 s.
- Record correction: STATUS line 6 and the T-46b status said the pilot totals were not committed. They were committed in 663d17d. TASKS was corrected by the TL; STATUS is corrected in this entry.
- Metrics (T-46c): review rounds 1, questions back 0, out-of-scope files 0, models Sonnet (developer), Haiku (scribe).
- Not committed yet; waits for the maintainer.
- Next: the rest of the eval runner fixes (review items 3 to 6: process tree stop on Windows, resume refuses changed settings, condition order by fixed seed, 120 runs instead of 360), then the eval runs; 5 review decisions open.

## 2026-11-09 (1) - T-46b pilot ran to the end after a stop; API credit check

- The TL started the pilot (20 runs, budget 3 USD) in this session on the customer's word. The customer said to stop everything. The TL stopped the background shell task and reported the pilot stopped with no process left. That was wrong: stopping the shell task did not stop the Python runner, and the TL's process check matched nothing. The runner finished all 20 runs (about 23:37 to 00:06) and wrote `eval/results/pilot-1.json`. Found after the T-46b commit; the totals file is not committed.
- Pilot totals (list-price estimate 0.157 USD, `apiKeySource` none on all 20 runs, 0 errors, 0 unparsed): Haiku 4 of 5 with the server, 4 of 5 without (the guard events question wrong in both); Sonnet 5 of 5 in both. Tool calls per 5 runs: Haiku 9 with the server (all Read), 26 without; Sonnet 8 with (7 server tools), 10 without. Cost per run: Haiku 0.0009 and 0.0016 USD, Sonnet 0.013 and 0.016 USD.
- The customer asked whether the TL session had used the API credit. Checked: the key is not set in the session's process environment, only as a user-level variable. The only calls with the key were the 11 step-0 calls, all refused at 0 USD.
- The customer's console showed 98.50 USD organization credit and 1.51 of a 20 USD monthly limit spent. Why the step-0 key was refused with "Credit balance is too low" is not known. The records that said "no credit" were corrected (DEC-054, V-16, TASKS).
- Next: the pilot in the customer's terminal with `docs/eval-runbook.md`, then the full matrix after the weekly usage limit resets.

## 2026-11-08 (9) - T-46b eval runner and runbook

- T-44a committed and pushed (bcaae50).
- The customer decided the eval set-up (DEC-053): `--bare` with the API key, Haiku and Sonnet, a 20-run pilot before the 360-run matrix.
- `developer` (Sonnet, effort high) built:
  - `tools/eval_run.py` (stdlib);
  - 36 tests; `docs/eval-runbook.md`; `eval/results/`;
  - V-16 in `docs/toolchain.md`; 1 CHANGELOG line.
- Step 0, round 1: 11 `--bare` calls on Haiku refused with "Credit balance is too low", 0 USD. The init event showed `--bare` accepts `--mcp-config`, the 10 tools as `mcp__sdlc__<tool>`, and no Grep, Glob or ToolSearch under `--bare`.
- The customer decided round 2 (DEC-054): the subscription login without `--bare`, against the TL recommendation; Read only in both conditions, with the file list in the prompt.
- Step 0, round 2: 3 subscription runs on Haiku. The server condition answered a real question correctly with `Read` and `mcp__sdlc__decisions`. None of the user's agents, plugins, skills, MCP servers or global `CLAUDE.md` loaded. The CLI's bundled listings and the account e-mail stay in context (runbook Limits). Weekly usage was at 79 %.
- The runner drops `ANTHROPIC_API_KEY` from the child environment and stops all runs if a run reports an API key.
- Tests: 1028 passed, 6 skipped. Guard: 2 denies, both temporary files outside the root; `--check-worktree`: 8 paths, all inside T-46b.
- Metrics (T-46b runner): review rounds 2 (round 2 from DEC-054), questions back 3, out-of-scope files 0, models Sonnet (developer), Haiku (scribe).
- Next: pilot run, then the full matrix. Both are in the 2026-11-09 (1) entry above.

## 2026-11-08 (8) - T-44a guard match in bounded time

- T-44 committed and pushed (1fc790f).
- The maintainer chose to fix S-7 and S-8 before the eval runs. The TL wrote the contract and placed `.sdlc/active-contract.md` (6 Files in, 8 Files out).
- `developer` (Sonnet, effort high) built T-44a:
  - `tools/scope_guard.py`: `heading_text`, one pass over the line, replaces the `_HEADING` pattern; `matches` keeps the reachable path positions as one integer and moves it token by token, no backtracking; `glob_to_regex` unchanged and kept as the test reference;
  - `server/inputs.py`: the T-44 stopgap (refuse a heading run over 16 blanks) removed; the size limits stay;
  - `docs/security.md`: S-6, S-7, S-8 fixed with test names; 2 new limits lines; 1 CHANGELOG line.
- Same answers as the old regex on 6,000 generated pairs (fixed seed, case folding on and off) and on every short string in `tests/` as a pattern; two planted mutations were caught.
- Times, before and after: 2,000-blank heading 12.8 s to under 1 ms; 9 `**/` against 30 segments 4.6 s to 0.05 ms; 50 patterns against a 500-character path 1.6 s to 0.3 ms. The hook timeout is 30 s.
- Findings in `docs/security.md`: 0 open (17 in all: 15 fixed, 2 accepted).
- Tests: 12 new; 992 passed, 6 skipped (TL rerun).
- Guard: 19 writes, 19 allow, 0 deny; `--check-worktree`: 7 paths, all inside T-44a.
- Metrics (T-44a): review rounds 1, questions back 0, out-of-scope files 0, models Sonnet (developer), Haiku (scribe).
- Next: T-46b eval runs in the maintainer's terminal, under a cost cap.

## 2026-11-08 (7) - T-44 security pass

- T-42 committed and pushed (9643651).
- The maintainer gave the go-ahead for T-44. The TL wrote the contract and placed `.sdlc/active-contract.md` (12 Files in, 8 Files out). The contract named the files the developer may read, after the T-42 finding.
- `developer` (Sonnet, effort high) ran T-44:
  - `docs/security.md` (61 lines, 17 findings, input table; C-26 items a to i not applicable while the server is stdio only; limits);
  - new `server/inputs.py`;
  - read limits in `tools/records.py`, `tools/lookup.py` and `tools/events.py`;
  - `_git` in `tools/scope_guard.py` passes `-c core.fsmonitor=false`;
  - `docs/toolchain.md` dependency list; 1 CHANGELOG line.
- Findings:
  - High: 3 fixed, 0 open (G4-9 met). S-1 control files read through a link out of the root; S-2 `core.fsmonitor` and S-3 a clean filter in `.git/config` ran a program on `git status` (both measured).
  - Medium: 7 fixed, 2 open (9 in all; 17 findings: 3 High, 9 Medium, 5 Low). Open: S-7 the guard heading pattern; S-8 the guard glob matcher, slow input makes the hook time out, and a timeout lets the write through (V-6).
  - Low: 3 fixed, 2 accepted (S-4, S-17: no vulnerability scan without network).
- Cost of S-3: `changed_outside` refuses a repository whose git config has a filter or include section, so Git LFS repositories get no answer from that tool.
- C-26 in the source map has 9 items, not 10, as the report states.
- Tests: 112 new; 980 passed, 6 skipped (TL rerun). The skips are file symlink tests this machine cannot run; the junction tests ran.
- Guard: 92 writes, 92 allow, 0 deny, all Write or Edit; `--check-worktree`: 16 paths, all inside T-44.
- Metrics (T-44): review rounds 1, questions back 0, out-of-scope files 0, models Sonnet (developer), Haiku (scribe).
- Next: the maintainer decides S-7 and S-8; then T-46b eval runs.

## 2026-11-08 (6) - T-42 record read tools

- T-41 and T-46a committed and pushed (2070d74).
- The maintainer gave the go-ahead for T-42. The TL wrote the contract and placed `.sdlc/active-contract.md` (11 Files in, 7 Files out).
- `developer` (Sonnet, effort high) built T-42:
  - `tools/lookup.py` (694 lines, stdlib, CLI mode) with readers for decisions, lessons, audit findings, tasks and log;
  - 5 server tools `decisions`, `lessons`, `findings`, `tasks`, `log` (10 tools in all);
  - record map defaults `lessons` and `audits` in `tools/records.py` and `templates/project.md`;
  - fixtures under `tests/fixtures/server/lookup/`; `docs/toolchain.md` V-15; 1 CHANGELOG line.
- Tests: 126 new; 868 passed, 2 skipped (TL rerun). The second skip is a link test this machine cannot run.
- This repository read by the tools: 52 decisions, 1 lesson, 38 tasks, 61 log entries, 6 audit reports, 0 unreadable. Largest answer: `log` with 20 entries, 32,464 characters.
- Live run (Haiku): each of the 5 tools called once, no error, 0.0093 USD.
- Guard: 37 writes, 37 allow, 0 deny; `--check-worktree`: 18 paths, all inside T-42.
- Finding: the T-42 acceptance line asked the tools to parse this repository's `DECISIONS.md`, `LOG.md` and `audits/`, which `DEV_RULES.md` rule 3 forbids a developer to read. The contract did not name the exception; the developer reported it. Cause: the TL contract.
- Metrics (T-42): review rounds 1, questions back 0, out-of-scope files 0, models Sonnet (developer), Haiku (scribe).
- Next: T-44 security pass.

## 2026-11-08 (5) - T-46a eval set, T-41 scope and event tools

- T-40a committed and pushed (311c2b0).
- The TL ran T-46a before T-41 so the eval questions are frozen before the tools exist (`cto/2026-11-07_phase4-plan.md`).
- `developer` (Sonnet) built T-46a:
  - `eval/`: a fictional repository that follows `templates/`; 30 questions (scope 8, decisions 6, findings 6, tasks 5, guard events 3, lessons 2; 11 need 2 or more files); a stdlib scorer; a README;
  - 56 tests; 660 passed, 1 skipped;
  - scope keys recomputed with `tools.scope_guard`; the scorer gives 30 of 30 on the key;
  - frozen SHA-256 `c59798e3...` (full value in `eval/README.md`).
- Guard: 22 writes, 22 allow.
- `developer` (Sonnet, effort high) built T-41:
  - tools `scope_check`, `contract`, `changed_outside`, `guard_events`; `tools/events.py` with a CLI; `.gitattributes` `*.jsonl` LF; `docs/toolchain.md` V-14; 1 CHANGELOG line;
  - 64 tests; 742 passed, 1 skipped (TL rerun);
  - the developer did not read `eval/`.
- Live run (Haiku): each new tool called once, no error, 0.0079 USD.
- Guard: 23 writes, 23 allow. The developer reported one rule 5 break: a one-word fix in 4 places through `sed -i`.
- Metrics (T-39): review rounds 1, questions back 0, out-of-scope files 0, models Sonnet (developer, tech-writer), Haiku (scribe).
- Metrics (T-39a): review rounds 1, questions back 0, out-of-scope files 0, models Sonnet (developer), Haiku (scribe), customer result passed.
- Metrics (T-40): review rounds 1, questions back 0, out-of-scope files 0, models Sonnet (developer), Haiku (scribe); 12 of 14 files written through Bash.
- Metrics (T-40a): review rounds 1, questions back 0, out-of-scope files 0, models Haiku (developer, scribe).
- Metrics (T-46a): review rounds 1, questions back 0, out-of-scope files 0, models Sonnet (developer), Haiku (scribe).
- Metrics (T-41): review rounds 1, questions back 0, out-of-scope files 0, models Sonnet (developer), Haiku (scribe); 1 Bash write.
- Next: T-42 decision, lesson, gate and log read tools.

## 2026-11-08 (4) - T-40a file tools only

- T-40 committed and pushed (cfe21fa).
- The maintainer took the TL recommendation on the T-40 finding: developers write files with Write or Edit only and run no git command that changes state (DEC-052).
- `developer` (Haiku) built T-40a: `DEV_RULES.md` new rule 5, rule 8 narrowed to the read-only server (DEC-050), 28 lines; `agents/developer.md` line 3 and its copy; 1 CHANGELOG line. 604 passed, 1 skipped. Review rounds: 1.
- Guard: 4 writes, 4 allow lines with task T-40a, 0 deny. The developer rules file was allowed through its exact path in Files in, the first live use of DEC-048.
- The TL fixed two rule numbers on the `DEV_RULES.md` Sources line (role exceeded, one line).
- Next: T-41 `scope_check` and metrics tools.

## 2026-11-08 (3) - T-40 server skeleton

- The maintainer decided the 2 server questions with the TL recommendation:
  - the server reads only (DEC-050);
  - the user installs `mcp`; the server stops with a one-line hint when it is missing (DEC-051).
- The TL wrote the T-40 contract and placed `.sdlc/active-contract.md`; the guard was live in this session.
- `developer` (Sonnet, effort high) built T-40:
  - files: `server/` (`main.py`, `status.py`, `rootlock.py`), `tools/records.py`, `tests/test_server.py`, `tests/test_records.py`, 4 fixtures, `mcpServers` in `.claude-plugin/plugin.json`, `.gitattributes` (`*.json` LF), `docs/toolchain.md` (mcp 2.3.0, V-13), 1 CHANGELOG line;
  - 604 passed, 1 skipped (TL rerun);
  - review rounds: 1.
- Developer live runs: 2 (Haiku):
  - the CLI starts the server with `python` directly on Windows;
  - `${CLAUDE_PLUGIN_ROOT}` expands in `args`;
  - tool name `mcp__plugin_sdlc_sdlc__status`;
  - `CLAUDE_PROJECT_DIR` reaches the server;
  - the start folder is not settled.
- TL live run: `status` returned task T-40, state active, 9 Files in. With the SDK missing: exit 1 and the install line.
- Finding: 12 of 14 files were written through Bash (heredoc, scripts), so the guard logged 2 developer events. `--check-worktree`: 16 paths, all inside T-40. No developer rule forbids Bash writes (DEC-038). The developer also ran `git stash` and `git stash pop` once; no change lost.
- Next: the maintainer decides whether the developer rules forbid Bash writes and git state commands; then T-41.

## 2026-11-08 (2) - T-39a the kit runs its own guard

- The desktop app session in this folder loaded no plugin: no `/sdlc` commands, no `sdlc:` agents, no `--plugin-dir` option.
- The maintainer chose the TL recommendation: register the guard in `.claude/settings.json` (DEC-049).
- The TL wrote the T-39a contract.
- `developer` (Sonnet) built T-39a:
  - files: `.sdlc/project.md` (20 lines), `.claude/settings.json` (16 lines), `CLAUDE.md` (2 lines), `tests/test_scope_guard.py` (5 new tests), 1 CHANGELOG line;
  - 540 passed, 1 skipped (TL rerun);
  - review rounds: 1.
- TL live `claude -p` check (Haiku):
  - with no contract: write to `PLAYBOOK.md` denied, write to `LOG.md` allowed;
  - main-session write in the memory folder: allowed; `memory/..`: denied;
  - 4 event lines, none with a path.
  - Probe lines and files removed.
- Maintainer check in a new desktop app session: an Edit to `PLAYBOOK.md` with no contract was denied (`[no-contract]`); file unchanged.
- V-9 closed in `docs/toolchain.md`.
- Next: T-40 server skeleton after the maintainer's 2 answers (server writes records or reads only; how a user gets the `mcp` SDK).

## 2026-11-08 (1) - Phase 4 opened, T-39 guard changes

- Records of DEC-046 to DEC-048 committed and pushed (084cec5). 515 passed, 1 skipped.
- `cto` (Opus) wrote the phase 4 plan, `cto/2026-11-07_phase4-plan.md` (89 lines).
  - Order: T-39, T-39a, T-40, T-41, T-42, T-44, T-46a and T-46b, G0 leftover, T-45.
  - 10 countable G4 lines.
  - 2 maintainer questions block T-40: does the server write records or only read them; how does a user get the `mcp` SDK.
  - CTO objection to the phase 4 line: `.mcp.json` belongs in T-40, not T-42; the TL agrees.
- The TL wrote the T-39 contract (11 lines).
- `developer` (Sonnet) built T-39:
  - files: `tools/scope_guard.py` (+54, -6), `tests/test_scope_guard.py` (+105, 25 cases), `skills/init/SKILL.md`, `tests/test_skills.py`, 1 CHANGELOG line;
  - 536 passed, 1 skipped (TL rerun);
  - review rounds: 1.
- TL hand run: 5 hook inputs in a throwaway folder opted in to the guard:
  - main-session memory write: allowed;
  - sub-agent memory write: denied;
  - `..` out of the memory folder: denied;
  - sub-agent rules-file edit with Files in `**`: denied;
  - the same edit with the exact path: allowed.
  - Event lines hold no path.
- `tech-writer` (Sonnet) updated `PLAYBOOK.md` Appendix H (DEC-046, DEC-048).
- Not verified: the `transcript_path` layout of a live session; to be checked at T-39a when the kit opts in.
- Next: maintainer review and commit of T-39; then T-39a.

## 2026-11-07 (7) - Three open questions decided

- The TL explained the 3 open questions in plain terms; the maintainer took the TL recommendation on all 3.
- DEC-046: the main session may write in the CLI's per-project memory folder; every other path outside the root stays denied; sub-agents stay denied.
- DEC-047: the kit opts in to its own scope guard in phase 4.
- DEC-048: a sub-agent may change the developer rules file only when Files in holds its exact path, no glob.
- The TL added T-39 (guard changes for DEC-046 and DEC-048) and T-39a (kit opt-in) to the phase 4 line of `TASKS.md`.
- The maintainer will continue in a new session.
- Next: phase 4 opens with the CTO plan in a new session.

## 2026-11-07 (6) - G3 passed

- `auditor-mini` (Opus) re-verified the G3 fix round: ACCEPT, 9 of 9 items closed, 0 open (`audits/2026-11-07_gate3_reverify.md`).
- Fresh clone with autocrlf true: 515 passed, 1 skipped. Guard exit 0 over 15 files.
- `EVIDENCE.md` and `evidence/` unchanged since `2bd234e`; Project A manifest hash unchanged.
- Note from the re-verification: 17 files still check out CRLF in a fresh clone (14 `.json`, `LICENSE`, `.gitignore`, `.gitattributes`); no test checks them.
- Low findings still open for the maintainer: P-3, P-4, D-1, D-2, R-1; and DEC-037 finding 1.
- The maintainer approved the gate commit and push.
- Next: phase 4; first the maintainer's 3 open questions (memory folder, kit opting in to its own guard, exact name or glob for the rules file), then the CTO phase 4 plan.

## 2026-11-07 (5) - Triage, T-33b, G3 audit and fix round T-34a

- The maintainer accepted the TL's triage proposal and asked for 4 steps: triage, the rules-file fix, the toolchain note, the clone cleanup.
- Triage (DEC-045):
  - finding 4 fixed in phase 3;
  - finding 1 open for the maintainer; deny unchanged;
  - findings 3, 6, 7, 9 moved to the phase 5 line;
  - findings 2, 5, 8 stated as limits.
- T-33b (`developer`, Sonnet):
  - files: `tools/scope_guard.py`, `skills/init/SKILL.md`, 2 test files, 1 CHANGELOG line;
  - 10 new tests; 515 passed, 1 skipped.
  - TL hand check: a sub-agent write to the rules file, which is in the always-allowed list, was denied (exit 2); the main session was allowed.
  - A glob in Files in that matches the rules file counts as naming it.
- `tech-writer` (Sonnet) changed 1 row of `PLAYBOOK.md` Appendix H on a TL brief outside the T-33b contract: 2 sentences and the DEC-045 tag; 1 round. The T-33b contract did not name this step (G3 finding P-2).
- The TL added the T-33 section to `docs/toolchain.md`.
- The P-33 rehearsal clone was already gone from the maintainer's home folder when the TL looked; the TL deleted nothing.
- `auditor` (Fable) G3 audit: CONDITIONAL ACCEPT, `audits/2026-11-07_gate3.md`.
  - 8 of 9 criteria pass; G3-7 partial.
  - Findings: 0 Critical, 0 High, 2 Medium (P-1 records behind the work; C-1 tests red on a fresh Windows clone, 6 failed), 7 Low (P-2, P-3, P-4, D-1, D-2, D-3, R-1).
  - Conditions: the maintainer's G3-7 statement recorded; P-1 closed.
- The maintainer gave the G3-7 statement on 2026-11-07 (recorded in the DEC-043 outcome) and approved the fix round.
- T-34a (`developer`, Sonnet):
  - `.gitattributes`: `*.md` and `*.txt` set to `eol=lf`; `DEV_RULES.md` line 1 points to `agents/`; 1 CHANGELOG line.
  - Fresh clone with autocrlf true: 515 passed, 1 skipped; this folder: the same.
- The TL closed P-1 and D-3: DEC-035, DEC-039, DEC-043, DEC-044, DEC-045 outcomes; the 4 routed findings on the phase 5 line of `TASKS.md`; the dogfood note points to DEC-045; toolchain table CLI 2.1.319.
- Left open, for the maintainer: DEC-037 memory folder (finding 1); D-1 kit opting in to its own guard; D-2 exact name or glob; P-4 lessons; P-3 contract line length.
- Next: `auditor-mini` re-verifies the 2 conditions and C-1; then the gate commit after the maintainer's word.
- Metrics (T-33b): review rounds 1, questions back 0, out-of-scope files 0 (1 doc changed outside the contract by tech-writer, P-2), models Sonnet (developer, tech-writer).
- Metrics (T-34a): review rounds 1, questions back 0, out-of-scope files 0, model Sonnet.

## 2026-11-07 (4) - T-33 real task on Project A

- The maintainer gave the go-ahead and ran T-33 in a PowerShell window the maintainer opened (G3-7). CLI 2.1.319.
- Project A's own TL session ran on Opus, effort high, with the plugin loaded by `--plugin-dir`. Permission mode was default; it changed near the end to accept-edits, then to auto.
- Before the task:
  - Project A's 2 pending changes were tested and pushed by the maintainer in Project A's normal flow.
  - The start state (HEAD, hook hashes, `git status`, exclude file) was noted outside the repository.
  - Kit baseline: HEAD `2bd234e`. The Project A manifest hash was noted outside the repository.
- Setup:
  - `/sdlc:status`, `/sdlc:init` with the record map and report language, `/sdlc:install-hooks`.
  - 1 deny during setup: the main session wrote a note to its own memory folder, outside the root. The task was not blocked.
- Task:
  - The maintainer picked 1 of 3 candidates, a medium task.
  - Project A's TL wrote a 10-line contract; `/sdlc:contract` wrote it. `--check-contract`: 15 Files in, 5 Files out.
  - Branch, then `developer` (Sonnet): 3 rounds. Round 1 was the first version; round 2 was 1 fix for a gap the TL review found; round 3 was 1 change the maintainer asked for. This exceeds the 2-round rule.
  - `scribe` (Haiku) wrote Project A's records in 2 rounds; the TL review found 2 wrong statements in round 1.
- Checks:
  - `/sdlc:review`: 1 of 14 changed paths outside the contract. That file was changed before the task and kept out by name.
  - Tests: 158 run, 155 pass, 0 fail, 3 skipped.
  - The maintainer tested the change and reported no problem.
- Git:
  - 4 commits, 4 pushes through the chained hook (branch 2, main 2), 0 rejected.
  - Fast-forward merge to main after the maintainer's word.
  - A settings file re-saved by the game editor stopped the first branch switch until it was committed.
- Close:
  - `/sdlc:contract close`, `/sdlc:install-hooks --uninstall`; `.sdlc/` removed; exclude file restored.
  - Hook folder hash-equal; `core.hooksPath` unset; `git status` equal to the noted state.
  - The DEC-033 exception ended.
- Scope guard events: 39; allow 38, deny 1; no contract 4, active 35; main session 6, developer 15, scribe 18; Write 4, Edit 35; with a path 0.
- The kit TL corrected Project A's session 4 times from outside:
  - the developer rules file was removed from the always-allowed list;
  - the contract is written by `/sdlc:contract`, not by hand;
  - test output is kept outside the repository;
  - the TL session runs the contract command instead of a pasted line.
- The TL wrote:
  - `docs/dogfood-1.md` (T-33 section, 9 findings);
  - the DEC-033, DEC-034, DEC-037 and DEC-043 outcomes;
  - one CHANGELOG line;
  - and marked T-33 done.
- Next: T-34 gate G3; triage of the 9 findings with the maintainer.
- Metrics (T-33): review rounds 3 (developer), questions back 0, out-of-scope files 0, models Opus (Project A TL), Sonnet (developer), Haiku (scribe), customer result passed.

## 2026-11-07 (3) - T-30b file tools in init and contract

- The maintainer chose to fix the P-33 finding before T-33.
- The maintainer said the Project A task is picked with that project's TL session.
- `developer` (Haiku) changed:
  - `skills/init/SKILL.md`: `Write` in the tool list; each write step names its tool;
  - `skills/contract/SKILL.md`: `Write` and `Edit` in the tool list; each write step names its tool; the `close` step keeps its shell delete, because no file tool deletes;
  - `tests/test_skills.py`;
  - one CHANGELOG line.
- Live runs: 2 of 2 allowed `claude -p` runs on Sonnet. The TL read the tool names from the logs:
  - `Write` for `.sdlc/project.md`;
  - `Edit` for the tasks record;
  - `Write` for `.sdlc/active-contract.md`;
  - Bash only for reads and `--check-contract`.
- TL checks:
  - diff reviewed;
  - `python -m pytest -q`: 505 passed, 1 skipped;
  - guard over the changed files: exit 0.
- The TL updated `docs/toolchain.md` and `docs/dogfood-1.md`, and marked T-30b done.
- The maintainer approved the commit and push: `2bd234e`.
- Commit `e087e10` "Add the rehearsal note" reached the remote at 00:31 on 2026-11-07, not through the TL. It holds 3 record files, no rehearsal file and no key; the guard passed it. Likely cause: the runbook git block ran in this folder, because the block had no folder check. History left as it is. The TL found it in this push.
- Next: T-33; the maintainer picks the task with the Project A TL session.
- Metrics (T-30b): review rounds 1, questions back 0, out-of-scope files 0, models Haiku (developer, scribe), Sonnet (live runs), customer result not tested.

## 2026-11-07 (2) - P-33 rehearsal

- The maintainer gave the go-ahead and ran P-33 in a PowerShell window the maintainer opened (G3-7).
- Versions: CLI 2.1.296 for the session steps; CLI 2.1.319 after an update on restart, used for the uninstall.
- The TL wrote `.sdlc/local/p33-runbook.md`. The TL dry-ran the preparation, git and rollback steps in a scratch folder first.
- Result of the run:
  - all 12 session steps, 2 pushes and the rollback matched the runbook;
  - one step needed a repeat for one file, because the prompt said to stop at a denial;
  - the window closed once by accident; no state was lost.
- `/sdlc:init` and `/sdlc:contract close` each asked before writing or deleting. This closes the gap left in T-30a.
- `scout` (Haiku) read the event lines: 5 events, all `Write`; 1 allow, 4 deny; sub-agent 4, main session 1; no path recorded.
- Pushes:
  - the clean push passed with a non-English line, and the old hook ran;
  - a fake key was rejected, with file, line and pattern name reported.
- Rollback: hook folder hash-equal to the original; `core.hooksPath` unset; `git status` empty.
- Finding: `init` and `contract` wrote through a Bash heredoc, which the scope guard does not see. Their paths were allowed, so no result changed.
- Limits:
  - auto mode was on;
  - no main-session write outside the root was tried, so the DEC-037 question stays open for T-33.
- The TL wrote `docs/dogfood-1.md`, updated `docs/toolchain.md`, `CLAUDE.md` Records and the DEC-037 outcome, and marked P-33 done.
- The rehearsal clone is still in the maintainer's home folder. Deletion waits for the maintainer's word.
- Committed in `2bd234e` with T-30b.
- Next: the maintainer picks the Project A task for T-33.
- Metrics (P-33): review rounds 1, questions back 2, out-of-scope files 1, models Sonnet (rehearsal session), Haiku (scout, scribe), customer result passed.

## 2026-11-07 (1) - P-33 contract

- The maintainer asked for the P-33 contract.
- The TL wrote the contract in `TASKS.md`. It has 15 fields.
- Scope: one rehearsal in a throwaway clone, in a terminal the customer opened, model Sonnet:
  - the 5 commands;
  - scope guard allow and deny, from the main session and from a sub-agent;
  - pushes to a local bare repository;
  - uninstall and the rollback steps.
- Set in the contract:
  - the TL writes the commands in a local runbook;
  - rehearsal totals go in a new `docs/dogfood-1.md`;
  - a fault found goes to a new contract, with no fix inside the task;
  - the run stops at the first failed step.
- Status: not started, awaiting the maintainer's go-ahead.
- No code changed. No metrics line: no task ran.
- Next: the TL writes the runbook after the go-ahead.

## 2026-11-06 (7) - T-33a snapshot guard

- The maintainer gave the go-ahead to continue with T-33a.
- The TL wrote the contract in `TASKS.md`.
- `developer` (Haiku) changed:
  - `tools/metrics/inputs.py`;
  - `tools/metrics/__main__.py`;
  - `tests/metrics/test_cli.py`;
  - one CHANGELOG line.
- Question back 1: the contract missed `tests/metrics/test_cli_records.py`, which has 2 double-snapshot calls. `developer` stopped with the suite red.
  - The TL added the file to the contract. The gap was in the contract, and DEV_RULES 1 leaves tests free.
  - `developer` added the flag to the 2 calls. No other line changed.
- TL mistake in review: the TL wrote a command that ran `--snapshot` on the real label `kit`, against its own contract, to check the refusal. The host's permission layer denied the whole command, so nothing ran. A failed refusal would have replaced a pinned snapshot. The refusal is proven by tests on a temp project only.
- TL checks:
  - diff reviewed; the check runs before any write;
  - `python -m pytest -q`: 502 passed, 1 skipped;
  - guard over the changed files: exit 0;
  - `git status --porcelain evidence EVIDENCE.md`: empty.
- No fault-planting round for this easy task.
- The maintainer approved the commit and push: `a4e65b2`.
- Next: P-33.
- Metrics (T-33a): review rounds 1, questions back 1, out-of-scope files 0, models Haiku (developer, scribe), customer result not tested.

## 2026-11-06 (6) - T-30a the 5 commands

- The maintainer gave the go-ahead to dispatch T-30a.
- `developer` (Sonnet, medium) changed:
  - `skills/{status,init,contract,review,install-hooks}/SKILL.md` (new);
  - `templates/project.md` (new);
  - `tests/test_skills.py` (new);
  - `tools/scope_guard.py`: `--check-contract` and `--check-worktree` modes;
  - `tests/test_scope_guard.py`: new cases;
  - one CHANGELOG line.
  - No file outside the contract changed.
- `developer` used 6 of 6 allowed `claude -p` runs. `status`, `install-hooks --uninstall` and `contract close` were not seen live in those runs.
- The maintainer approved 3 more runs, recorded in the contract. The TL ran them on Haiku:
  - `status` answered;
  - `install-hooks --uninstall` left the hook folder hash-equal to the original;
  - `contract close` removed the active contract.
- The `close` run sent `yes` in the same input, so the question before the delete was not observed. Cost of the 3 runs: about $0.024.
- Review round 1: the TL planted 28 faults in copies; 26 were caught.
  - The first fault run was invalid: the no-fault baseline failed because the copy had no `.gitignore`. It was fixed and rerun.
  - `developer` added 2 tests, moved `check_worktree` onto `decide()`, added the reports line and fixed the source line in `templates/project.md`, and set `backslashreplace` on the script mode output.
  - The rechecked faults are caught.
- Measured:
  - `allowed-tools` in a plugin skill takes effect;
  - a compound command needs its own approval;
  - `claude plugin details` lists 5 skills;
  - about 1,031 tokens are added to every session.
- Strict validate on a clean copy holds no finding beyond DEC-044.
- `tech-writer` (Sonnet, medium) updated `PLAYBOOK.md` Appendix H. The TL updated `docs/toolchain.md`, the outcomes of DEC-038 and DEC-041, and marked T-30a done.
- TL checks:
  - `python -m pytest -q`: 498 passed, 1 skipped;
  - guard over the changed files: exit 0.
- The maintainer approved the commit and push: `fa4d27b`.
- Next: T-33a.
- Metrics (T-30a): review rounds 1, questions back 1, out-of-scope files 0, models Sonnet (developer, tech-writer), Haiku (scribe, live runs), customer result not tested.

## 2026-11-06 (5) - T-30a contract

- The maintainer asked for the T-30a contract. The TL wrote it in `TASKS.md`; it has 15 fields.
- Scope:
  - 5 skills under `skills/`;
  - `templates/project.md`;
  - `--check-contract` and `--check-worktree` modes in `tools/scope_guard.py`;
  - `tests/test_skills.py`;
  - new cases in `tests/test_scope_guard.py`.
- Set in the contract:
  - `/sdlc:contract close` removes the active contract after the customer's word;
  - `/sdlc:init` does not write the exclude line; `/sdlc:install-hooks` does.
- Status: not dispatched; awaiting the maintainer's go-ahead.
- No code changed. No metrics line: no task ran.
- Next: dispatch T-30a to `developer` after the go-ahead.

## 2026-11-06 (4) - T-32 git hook installer

- The maintainer gave the go-ahead to dispatch T-32.
- `developer` (Sonnet, high) changed:
  - `tools/install_git_hooks.py`;
  - `tools/pre_push_guard.py`;
  - `templates/guard-patterns.txt` (new);
  - `tests/test_install_target.py` (new);
  - one CHANGELOG line.
  - No file outside the contract changed. No `claude -p` run.
- Review round 1: the TL planted 35 faults in copies; 33 were caught. 2 tests were too weak:
  - `--files` mode ignored `forbid-path` lines;
  - `.sdlc` as a file was not tested.
  - `developer` (Sonnet, medium) fixed both tests and one stale-message wording. All 3 rechecked faults are now caught.
- TL end-to-end run in temp repositories, with a space in the path and an existing hook:
  - a clean push passed;
  - a planted secret was rejected;
  - `PLAN.md` and a non-English line passed;
  - stale was reported, and `--refresh` worked;
  - after uninstall the hook folder was hash-equal to the original, and `core.hooksPath` was unset.
- Found for P-33: a clone of this repository keeps its tracked `.sdlc/guard-patterns.txt` with the language line. The prepare step is in `TASKS.md`.
- Accepted beyond the contract:
  - the wrapper passes no arguments to the guard;
  - `--target` must be the top folder;
  - `--repo` with `--target` is refused;
  - a `pre-push` without the marker is refused only when install traces remain.
- `PLAYBOOK.md` not changed: the set of hooks it states is the same. The target install is stated when the command exists in T-30a.
- The TL updated `docs/toolchain.md` and the DEC-042 outcome, and marked T-32 done.
- TL checks:
  - `python -m pytest -q`: 437 passed, 1 skipped;
  - guard over the changed files: exit 0.
- The maintainer approved the commit and push: `7109c3a`.
- Next: T-30a.
- Metrics (T-32): review rounds 1, questions back 0, out-of-scope files 0, models Sonnet (developer), Haiku (scribe), customer result not tested.

## 2026-11-06 (3) - T-32 contract

- The maintainer asked for the T-32 contract. The TL wrote it in `TASKS.md` (15 fields).
- Scope:
  - target mode of `tools/install_git_hooks.py`;
  - a chain wrapper at the target's pre-push hook;
  - `--refresh` and `--uninstall`;
  - a `forbid-path` line in the pattern file;
  - `templates/guard-patterns.txt`;
  - `tests/test_install_target.py`.
- Two choices the plan left open are set in the contract:
  - the installer writes the `.sdlc/` exclude line;
  - uninstall removes the wrapper and `.sdlc/guard/`, and leaves the patterns, `.sdlc/local/` and the exclude line for the manual rollback step.
- Count corrected in the contract: `tests/test_pre_push.py` holds 31 tests, not the 17 in DEC-042.
- No code changed. Not dispatched; awaiting the maintainer's go-ahead.
- Next: dispatch T-32 to `developer` after the go-ahead.

## 2026-11-06 (2) - T-31 scope guard hook

- The maintainer gave the go-ahead for T-31.
- `developer` (Sonnet, high) added:
  - `hooks/hooks.json`;
  - `hooks/scope/launcher.sh`;
  - `tools/scope_guard.py`;
  - `tests/test_scope_guard.py`;
  - `tests/fixtures/scope/`;
  - 2 lines in `.gitignore`;
  - one CHANGELOG line.
  - No file outside the contract changed.
- `developer` used 3 of 3 allowed `claude -p` runs. No retry.
- Live runs on Haiku in a throwaway folder:
  - a main-session write with no contract: denied;
  - a write inside a contract: allowed;
  - a write by `sdlc:scribe` outside the contract: denied.
  - The event lines match and hold no path.
- Review round 1: the TL planted 13 faults in a copy; 12 were caught. A fake Python that is too old did not reach the version check, so removing the check still passed. `developer` fixed that test and confirmed the fault is now caught.
- TL timing check, host start: median 422 ms to 598 ms over 7 series of 20 calls; maximum 918 ms. One direct call took 24.4 s while other work ran. It did not return within the 200 later calls. Its cause is not known.
- `tech-writer` (Sonnet, medium) updated `PLAYBOOK.md` Appendix H and the Enforcement field of `templates/dev-rules.md`. The TL removed one source tag from the new row.
- The TL updated `docs/toolchain.md` and the outcomes of DEC-037 and DEC-040, and marked T-31 done.
- Point to watch at P-33: a main-session write outside the root is denied in an opted-in project. This includes files the CLI keeps in the user's home folder.
- TL checks:
  - `python -m pytest -q`: 388 passed, 1 skipped;
  - guard over the changed files: exit 0;
  - `claude plugin details` lists 1 hook.
- The maintainer approved the commit and push: `04ed356`.
- Next: T-32.
- Metrics (T-31): review rounds 1, questions back 0, out-of-scope files 0, models Sonnet (developer, tech-writer), Haiku (scribe), customer result not tested.

## 2026-11-06 (1) - T-30 pushed, T-31 contract

- Commit `9c03aa3` (T-30 skeleton and role files) went through the pre-push guard on 2026-11-05.
- The records inside that commit still said awaiting approval. This entry and the STATUS update correct that.
- The maintainer asked for the T-31 contract. The TL wrote it in `TASKS.md` (15 lines). Scope:
  - hook;
  - launcher;
  - guard script;
  - grammar of the two `.sdlc/` files;
  - tests;
  - at most 3 Haiku runs.
- TL additions beyond the CTO report:
  - the main session may always write under `.sdlc/`, otherwise no contract can be placed;
  - hook timeout 30 s, because a timeout lets the write through;
  - fixtures use a placeholder for paths, because the pre-push guard rejects absolute user paths.
- Outcome: not committed; awaiting the maintainer's go-ahead.

## 2026-11-05 (4) - T-30 skeleton and role files

- The maintainer gave the go-ahead for T-30.
- `developer` (Sonnet, medium) added:
  - `.claude-plugin/plugin.json`;
  - `agents/` with the 7 roles;
  - one record-name line in 6 role files;
  - the scout example change;
  - `tests/test_role_sync.py`;
  - one CHANGELOG line.
  - No file outside the contract changed.
- `developer` used 1 of 2 allowed `claude -p` runs.
- Open question to the TL: `claude plugin validate . --strict` exits 1 at the repository root. `--strict` treats warnings as errors, and `CLAUDE.md` at a plugin root raises a warning. `CLAUDE.local.md` raises the same warning in a working copy.
- TL measurement on clean copies:
  - `CLAUDE.md` at the root: exit 1.
  - `.claude/CLAUDE.md`: exit 0.
- Maintainer decision: keep `CLAUDE.md` at the root (DEC-044). G3-1 and the T-30 acceptance line are amended.
- Review round 1: the test for an invalid model did not exercise the check. `developer` added one `value_errors` function, used by every value test.
- TL checks:
  - `python -m pytest -q`: 280 passed, 1 skipped.
  - Clean copy, strict validate: shows the `CLAUDE.md` warning. Plain validate: exit 0.
  - A planted bad model on a copy made the sync test fail.
  - Guard over the changed files: exit 0.
  - The load output lists the 7 `sdlc:` agents. `claude plugin details` reports about 837 tokens added to every session.
- The TL updated `docs/toolchain.md` and `CLAUDE.md` (role source folder) and marked T-30 done.
- Outcome: not committed; awaiting the maintainer's approval.
- Next: T-31.
- Metrics (T-30): review rounds 1, questions back 1, out-of-scope files 0, models Sonnet (developer), Haiku (scribe), customer result not tested.

## 2026-11-05 (3) - P-30 pushed, T-30 contract

- The maintainer approved the commit and push.
- Commit `9094dd1` (P-30 closed) went through the pre-push guard together with `ee19916` (P-30 contract).
- The maintainer asked for the T-30 contract. The TL wrote it in `TASKS.md`:
  - Scope: plugin manifest, `agents/` as the role source, a sync test, one record-name line in 6 role files.
  - At most 2 Haiku runs.
- TL choice in the contract: one record-name line per role, instead of rewriting the 19 lines the CTO report counted. The default names stay readable and the record map overrides them.
- Outcome: T-30 not committed; awaiting the maintainer's go-ahead.

## 2026-11-05 (2) - P-30 closed

- The TL found that no run of the first 12 showed `model` taking effect, and none used `Edit`.
- The maintainer approved 2 more probe runs. The TL amended the run limit in the P-30 contract to 14.
- `developer` (Sonnet) ran both, with no retry.
  - An agent with `model: sonnet` ran on Sonnet under a Haiku main session.
  - Real `Edit` hook input was captured.
- TL check against the raw logs: both results held.
- The TL:
  - updated `docs/toolchain.md`;
  - wrote the outcomes of DEC-036, DEC-037 and DEC-040;
  - marked P-30 done and updated NOW NEXT.
- The throwaway folder is removed. The captures stay in the ignored local folder for T-31.
- Outcome: not committed; awaiting the maintainer's approval. Commit `ee19916` (P-30 contract) is also not pushed.
- Next: T-30.
- Metrics (P-30): review rounds 1, questions back 0, out-of-scope files 0, models Sonnet (developer), Haiku (scribe), customer result passed (load in own terminal).

## 2026-11-05 (1) - P-30 run, TL check and terminal test

- The maintainer gave the go-ahead on 2026-11-04.
- `developer` (Sonnet) ran the plugin facts probe the same day: 12 `claude -p` runs on Haiku. One run was lost to a script error and was repeated. The records were not updated that day, so `STATUS.md` still said awaiting the go-ahead.
- 2026-11-05: a new session checked `.sdlc/local/p30-results.md` against the raw run logs. The main results held. No result contradicts a decision.
- TL corrections:
  - The V-2 claim about the model alias is withdrawn, because the main session was also Haiku.
  - The V-5 row pointed at a run with no capture. It now points at r2 to r9.
  - No run used `Edit`.
- Customer terminal test: the skill ran with `--plugin-dir` and replied EXPLICIT-RAN. No hook ran in that terminal. The CLI warned that an API key takes precedence over the login.
- The TL wrote the results into `docs/toolchain.md`, added one CHANGELOG line and updated NOW NEXT.
- TL checks:
  - Guard over `docs/toolchain.md` and `CHANGELOG.md`: exit 0.
  - `python -m pytest -q`: 271 passed, 1 skipped.
- Outcome: not committed. Commit `ee19916` (P-30 contract) is also not pushed.
- Open: 2 more probe runs await the maintainer's word. The throwaway folder is kept until then.

## 2026-11-04 (10) - P-30 contract

- The maintainer asked for the P-30 contract.
- The TL wrote the contract in `TASKS.md` (15 lines):
  - Scope: plugin facts probe, V items except V-7.
  - A throwaway plugin outside `AppData` and outside any repository.
  - At most 12 Haiku runs.
  - Results in ignored local files.
- Outcome: not committed; awaiting the maintainer's go-ahead.

## 2026-11-04 (9) - Phase 3 block and commit

- The maintainer approved the `TASKS.md` phase 3 block, the local exception text and the commit.
- The TL wrote the `TASKS.md` phase 3 block (9 items, no contract), the G3 row with 9 criteria, and NOW NEXT.
- The local exception text is in the private instructions (not committed).
- Commit: Add phase 3 plan and decisions DEC-033 to DEC-043; pushed through the pre-push guard.
- Next: the P-30 contract.

## 2026-11-04 (8) - CTO phase 3 plan and decisions DEC-033 to DEC-043

- The maintainer approved calling `cto` (Opus, effort high) for the phase 3 plan.
- `cto` wrote `cto/2026-11-04_phase3-plan.md` (324 lines): 9 items, 9 G3 criteria, 11 decisions, 12 plugin facts not verified.
- Objections raised in the report:
  - G3 cannot pass under the read-only rule for source projects.
  - The unit-level guard test does not prove that Claude Code calls the hook.
  - T-32 is [H].
  - The scope guard does not stop Bash writes.
- The maintainer accepted all recommendations:
  - DEC-033: written exception for T-33 only, on a branch in Project A's own repository, after P-33. The maintainer runs P-33 and T-33 in a terminal the maintainer opens.
  - DEC-034 to DEC-043: accepted as recommended.
- TL checks:
  - Report read in full.
  - 8 claims recounted against the repository and Project A, read only: snapshot overwrite, installer `core.hooksPath`, pattern line, 17 contract field lines, 19 role lines in 6 files, manifest head, existing hook, validate output.
  - Guard over the report, `DECISIONS.md` and `CHANGELOG.md`: exit 0.
  - `python -m pytest -q`: 271 passed, 1 skipped.
- Outcome: not committed. Open: the Project A task is not picked; the `TASKS.md` phase 3 block, the G3 row and the local exception text wait for the maintainer's go-ahead.
- Metrics (CTO phase 3 plan): review rounds 0, questions back 12, out-of-scope files 0, models Opus (cto), Haiku (scribe), customer result not tested.

## 2026-11-04 (7) - Phase 2 closed

- The maintainer approved closing phase 2 and the commit of T-24, T-24a and both audit reports.
- The TL marked T-24 and T-24a done in `TASKS.md` with Result lines and updated NOW NEXT.
- TL checks:
  - `python -m pytest -q`: 271 passed, 1 skipped.
  - Guard over the changed files: exit 0.
- Commit: Close phase 2: G2 ACCEPT, evidence limits fixed (T-24, T-24a); pushed through the pre-push guard.
- Next: the phase 3 plan (`cto`).

## 2026-11-04 (6) - T-24a candidates N-1 to N-4 closed

- The maintainer chose to fix N-1 to N-4 before closing phase 2. N-5 moved to G5 (T-52 line in `TASKS.md`), because the text is already in the git history; the maintainer decides before the repository goes public.
- The TL wrote the T-24a contract in `TASKS.md` and added a correction to the DEC-030 outcome (N-3).
- `tech-writer` (Sonnet, effort medium) changed `EVIDENCE.md` only: M9 rule, limit 16, new limits 19, 20, 21, the `kit_commit` sentence in the rerun section. No question back, no file outside the contract.
- `auditor-mini` (Opus, effort high), first pass: CONDITIONAL, N-4 partial; one sentence of limit 21 gave one cause for two fields. The TL gave the corrected sentences. Second pass: ACCEPT, 7 closed, 0 open, 0 partial. Report: `audits/2026-11-04_reverify.md`.
- TL checks:
  - Render run again: no change.
  - `python -m pytest -q`: 271 passed, 1 skipped.
  - Guard over the changed files and both audit reports: exit 0.
  - `EVIDENCE.md` ASCII only; 21 limits items.
- Outcome: not committed; awaiting the maintainer's check and the decision to close phase 2.
- Metrics (T-24a): review rounds 1, questions back 0, out-of-scope files 0, models Sonnet (tech-writer), Opus (auditor-mini), Haiku (scribe), customer result not tested.

## 2026-11-04 (5) - T-24 G2 audit: ACCEPT, 5 candidates

- The maintainer approved the G2 run. The TL committed the contract first (2e3f0ee, the gate commit).
- `auditor-mini` (Opus, effort high) ran 7 checks: 9 rows closed, 0 open, 0 partial. Verdict ACCEPT. Report: `audits/2026-11-04_gate2.md`.
- 5 new finding candidates, none a failed criterion:
  - N-1: M5 metric lines lower than a session line for 2 Project A tasks.
  - N-2: M9 denominator leaves out 15 entries with no outcome field.
  - N-3: loose reasons in limit 16 and DEC-030.
  - N-4: the Project A result file records an older tools commit and manifest profile hash.
  - N-5: the committed profiles hold an engine-specific test attribute and folder layout.
- TL checks:
  - The tree holds only the new report.
  - Guard over the report: exit 0.
  - H3 recounted: 103 commits, same 4 weeks.
  - N-1 confirmed on the snapshot.
  - N-2 from the result file warning.
  - N-4 by comparing the hashes.
  - N-5 by reading the profiles; the guard patterns hold no term for N-5.
- Outcome: report not committed; phase 2 not closed; the maintainer decides what happens with the candidates.
- Metrics (T-24): review rounds 0, questions back 0, out-of-scope files 0, models Opus (auditor-mini), Haiku (scribe), customer result not tested.

## 2026-11-04 (4) - T-24 contract

- The maintainer asked for the T-24 contract.
- The TL wrote it in `TASKS.md` (14 lines): the 6 G2 checks plus check 7 for the numbers outside the rendered block (DEC-031). Report: `audits/2026-11-04_gate2.md`, totals only.
- The TL recorded DEC-032: the G2 rerun uses a clean working tree of the gate commit and the local snapshots, since `evidence/raw/` is ignored by git. The G2 row in `TASKS.md` is narrowed to match.
- Order set in the contract: the TL commits the contract first; that commit is the gate commit.
- TL checks:
  - Contract within 15 lines.
  - Guard over `TASKS.md` and `DECISIONS.md`: exit 0.
- Outcome: not committed; awaiting the maintainer's go-ahead.

## 2026-11-04 (3) - T-23 approved and committed

- The maintainer approved the commit of T-23.
- The TL marked T-23 done in `TASKS.md` with a Result line and updated NOW NEXT.
- TL checks:
  - `python -m pytest -q`: 271 passed, 1 skipped.
  - CHANGELOG line present.
  - Guard over the changed files: exit 0.
- Commit: Add evidence report with limits (T-23); pushed through the pre-push guard.
- Next: the T-24 contract.

## 2026-11-04 (2) - T-23 `EVIDENCE.md` written

- The maintainer chose to write the limits numbers by hand, with their source named, and approved going on (DEC-031). The CTO plan line that every number sits in the rendered block is narrowed: metric results stay in the marked block only.
- The TL wrote the T-23 contract in `TASKS.md` (12 lines) and DEC-031.
- `tech-writer` (Sonnet, effort medium) wrote `EVIDENCE.md` and one CHANGELOG line. No question back, no file outside the contract.
- TL review: 9 fixes, 1 fix round.
  - Reading section gaps: M3, M5, M6, M9 direction.
  - Wrong wording of the 30% rule in M13.
  - Limits items 3 and 13.
  - New limits item 18.
  - Rerun section.
  - CHANGELOG line position.
- Found in review: a rerun of the kit from a fresh clone at the commit in `input.head`, on two throwaway clones on one Windows machine. Metrics, warnings and head match `evidence/kit.json`. `kit_commit` differs. 5 of 7 snapshot files have other hashes, with the same text once line endings are normalized. The first draft implied a byte-identical result for a stranger. The rerun section and limits item 18 now state this.
- TL checks:
  - Render run twice, second run no change (SHA-256 equal).
  - `python -m pytest -q`: 271 passed, 1 skipped.
  - Guard over `EVIDENCE.md`, `CHANGELOG.md`, `TASKS.md`, `DECISIONS.md`: exit 0.
  - `EVIDENCE.md` ASCII only; banned-word scan empty.
  - 18 limits items.
- Outcome: not committed; awaiting the maintainer's check.
- Metrics (T-23): review rounds 1, questions back 0, out-of-scope files 0, models Sonnet (tech-writer), Haiku (scribe), customer result not tested.

## 2026-11-04 (1) - T-22 and T-22a approved and committed

- The maintainer approved the commit of T-22a and the T-22 results.
- The TL marked T-22 and T-22a done in `TASKS.md` with Result lines and updated NOW NEXT.
- TL checks:
  - `python -m pytest -q`: 271 passed, 1 skipped.
  - CHANGELOG line present.
  - Guard over `evidence/*.json`: exit 0.
- Commit: "Add metrics results for three sources and Project A line layouts (T-22, T-22a)"; pushed through the pre-push guard.
- Next: the T-23 contract.

## 2026-11-03 (7) - T-22a Project A metric-line layouts

- The maintainer approved calling `developer` for T-22a.
- `developer` (Sonnet, effort medium) added an ordered `task_lines` list for M5 and M6. One task per log entry; the first item in list order wins; other matching lines are counted as `<tag>_extra_task_line`. Changed `profile.py`, `metrics_text.py` and the Project A profile. Added 12 tests and a fixture with invented English markers, and one CHANGELOG line. No question back, no file outside the contract.
- Technical choices the contract did not fix:
  - The new scanner sits in `metrics_text.py` and imports helpers from `records.py`, including the private `_HEADING`, because `records.py` was not in the touch list.
  - A chosen line without any number gives no task and a `<tag>_line_without_number` warning. It does not fall back to the next item.
- TL checks:
  - Diff reviewed: `task_line` profiles go through the old scanner unchanged.
  - `python -m pytest -q`: 271 passed, 1 skipped.
  - Kit rerun from its snapshot: SHA-256 unchanged.
  - `scout` reran Project A from its snapshot twice: byte-identical; input hashes equal to the manifest; guard exit 0.
  - Project A M5 v2 n 10 to 18; M6 v2 n 17 per field. No v1 task added.
  - Coverage: 19 of 20 v2 entries have task numbers parsed. The remaining one goes to the limits section.
- The TL wrote the outcomes of DEC-010 and DEC-030.
- Outcome: not committed; awaiting the maintainer's check.
- Metrics (T-22a): review rounds 0, questions back 0, out-of-scope files 0, models Sonnet (developer), Haiku (scout), Haiku (scribe), customer result not tested.

## 2026-11-03 (6) - T-22 run and coverage gap; T-22a contract

- The maintainer approved the T-22 run.
- The TL committed the T-22 contract first, so the kit snapshot was clean.
- `scout` (Haiku, effort low) ran the metrics on the three snapshots, kit first, then reran without snapshot. No question back, no file edited.
- Results:
  - Rerun byte-identical for all three sources.
  - Kit `dirty: false`; Project A and Project B `dirty: true`, recorded in the manifests (DEC-024).
  - Nothing under `evidence/raw/` in `git status`. Guard over `evidence/*.json`: exit 0. `python -m pytest -q`: 252 passed, 1 skipped.
  - Project B has v1 data for M3, M8 and M12 only. Kit: M1, M2 and M3 "no data" (no released version yet; no test attribute history).
- Parse coverage (G2 check 6), checked by the TL on the snapshot copies:
  - Kit: 20 loose matches, 16 metric lines counted; the other 4 are prose lines, not metric lines. Gap 0.
  - Project A v2: 20 log entries carry task numbers; 11 counted. 9 not counted: 2 with the metrics label mid-line, 6 in a TL review line with a round number, 1 with two conflicting free-text round numbers.
- The maintainer chose to fix the parser and to take the TL review round number as written. The TL recorded DEC-030, updated the local format note, and wrote the T-22a contract in `TASKS.md` (10 lines).
- Outcome: `evidence/*.json` not committed. T-22 stays open until Project A is rerun after T-22a.
- Metrics (T-22 run): review rounds 0, questions back 0, out-of-scope files 0, models Haiku (scout), Haiku (scribe), customer result not tested.

## 2026-11-03 (5) - T-22 contract

- The maintainer asked for the T-22 contract.
- The TL wrote it in `TASKS.md` (9 lines): one snapshot run and one rerun per source with `scout`, byte-identical check, manifest fields, parse coverage per source for G2 check 6, guard over `evidence/*.json`. Source paths stay in the brief only.
- Order set in the contract: the TL commits the contract before the run, so the kit snapshot is clean.
- TL checks:
  - Contract within 15 lines.
  - Added lines ASCII.
  - Guard over `TASKS.md`: exit 0.
- Outcome: not committed; awaiting the maintainer's go-ahead.

## 2026-11-03 (4) - T-21 approved and committed

- The maintainer approved the T-21 commit.
- The TL marked T-21 done in `TASKS.md` with a Result line and updated NOW NEXT.
- TL checks:
  - `python -m pytest -q`: 252 passed, 1 skipped (about 2 minutes).
  - CHANGELOG line present.
- Commit: "Add git, audit, decision and task metrics (T-21)"; pushed through the pre-push guard.
- Next: the T-22 contract.

## 2026-11-03 (3) - T-21 git, audit, decision and task metrics

- The maintainer chose DEC-029 a) (count Project B's untracked audit folder in M8) and approved calling `developer` for T-21. The TL recorded DEC-029.
- `developer` (Sonnet, effort high) wrote `tools/metrics/gitstats.py`, `tools/metrics/metrics_records.py` and `tools/metrics/render.py`, extended `profile.py`, `inputs.py`, `output.py` and `__main__.py` and the 3 profiles, added 124 tests and one CHANGELOG line. No question back, no file outside the contract. Four T-20 profile tests were updated for the new profile content; `metrics_text.py`, `records.py` and `fold.py` unchanged.
- Technical choices the contract did not fix:
  - M12: author dates outside the committer-date span are counted and warned, but do not widen the week span.
  - M13: optional profile key `done_date_body` takes the done date from the first date in a done task's "Result:" line.
  - M8: a re-verify row links to the latest other report dated on or before it; a finding without severity counts as `unrated`.
  - The result JSON gives per folder only file count, untracked count and one digest; no file names.
- TL checks:
  - `python -m pytest -q`: 252 passed, 1 skipped (symlink test; no symlink privilege on this machine).
  - Guard over the changed files: exit 0.
  - No marker literal in `tools/metrics/*.py`; new and changed files ASCII only.
  - Kit run twice: byte-identical JSON. Render twice into a test block: no diff.
  - Kit hand counts matched: M9 1 of 29; M12 18 commits over 2 ISO weeks; M8 15 findings (high 1, medium 4, low 9, unrated 1); M13 15 tagged tasks (E 4, M 8, H 3), 12 done, 2 untagged.
  - `evidence/` removed after the check.
- Limits noted for T-23:
  - Kit M13: 12 of 15 tasks undated (no date in their Result line).
  - The symlink escape path is untested on this machine.
  - DEC-029 needs a limits item.
- Outcome: not committed; awaiting the maintainer's check.
- Metrics (T-21): review rounds 0, questions back 0, out-of-scope files 0, models Sonnet (developer), Haiku (scribe), customer result not tested.

## 2026-11-03 (2) - T-21 contract

- The maintainer asked for the T-21 contract.
- The TL wrote it in `TASKS.md` (13 lines): snapshot of audit folders and git extracts, M3, M8, M9, M12, M13, writer allowlist, render into a marked block with the DEC-025 small-cell rule. Tag raised from [M] to [H].
- The TL recorded DEC-029 as open: whether Project B's untracked audit folder counts in M8. Recommendation a), count it.
- TL checks:
  - Contract within 15 lines.
  - Added lines ASCII; the DEC date line follows the existing format.
- Outcome: not committed. `developer` (Sonnet, effort high) implements T-21 after the maintainer answers DEC-029 and gives the go-ahead.

## 2026-11-03 (1) - T-20 approved and committed

- The maintainer checked T-20 and approved the commit.
- The TL marked T-20 done in `TASKS.md` and updated NOW NEXT.
- TL checks:
  - `python -m pytest -q`: 128 passed.
  - CHANGELOG line present.
- Commit: "Add metrics core and text metrics (T-20)"; pushed through the pre-push guard.
- Next: the T-21 contract.

## 2026-11-02 (8) - T-20 metrics core and text metrics

- The maintainer approved calling `developer` for T-20.
- `developer` (Sonnet, effort high) wrote `tools/metrics/` (7 modules, standard library only), profiles for Project A, Project B and the kit, 97 tests in `tests/metrics/` with invented fixtures, and one CHANGELOG line. No question back, no file outside the contract.
- Technical choices:
  - A run without `--snapshot` reads and hash-checks the existing copy, so no source is needed for a rerun.
  - `kit_commit`, HEAD and dirty flag are taken from the manifest, so a rerun after a later commit stays byte-identical.
  - Record paths in a profile must be relative.
  - Marker regexes live in the profiles only.
- TL checks:
  - `python -m pytest -q`: 128 passed.
  - Kit run twice: byte-identical JSON.
  - Kit M5 v2: n 14, distribution 0:5, 1:4, 2:5, 3+:0.
  - Kit M6 v2: questions back 6 of 14, out-of-scope 0 of 14; both matched by a hand count of the 14 metrics lines.
  - Kit M1 and M2: "no data".
  - No marker literal in `tools/metrics/*.py`.
  - New files ASCII only.
  - Guard clean.
  - `evidence/` removed after the check.
- Limit noted for T-23: the kit counts every `- Metrics (` line as one task, including the CTO plan and audit entries.
- Outcome: not committed; awaiting the maintainer's check.
- Metrics (T-20): review rounds 0, questions back 0, out-of-scope files 0, models Sonnet (developer), Haiku (scribe), customer result not tested.

## 2026-11-02 (7) - T-20 contract

- The maintainer chose option a) for the M1 open point of the local format note. The TL recorded DEC-028: M1 counts version-level revert headings over all version headings; item-level reverts are a separate count; a revert word in the heading scope or in the work log never counts.
- The TL wrote the T-20 contract in `TASKS.md` (13 lines): CLI with snapshot and manifest, folding, profiles for Project A, Project B and the kit, period rule incl. undated headings, M1, M2, M5, M6, deterministic JSON with a free-text refusal, path tests.
- TL checks: contract within 15 lines; added lines ASCII except the middle dot of the DEC date line (existing format); guard clean over `TASKS.md` and `DECISIONS.md`.
- Outcome: not committed; `developer` (Sonnet, effort high) implements T-20 after the maintainer's go-ahead.

## 2026-11-02 (6) - P-20 record format pass

- The maintainer approved the commit and P-20.
- `scout` (Haiku, low) read the record files of Project A and Project B, read only, and returned their formats with placeholders, folded markers and edge cases.
- TL spot check against the sources: changelog heading and status forms, per-task metric-line form, decision heading states, test attributes, Project B audit folder untracked. All matched the scout report.
- Findings:
  - Project A has every record type the metrics read.
  - Project B has a changelog, a log without metric lines and one audit report in an untracked folder; no decision log, task list or test attributes at HEAD.
  - The revert word has three uses in Project A's changelog (version, item, feature in the scope text); only the first two are reverts.
  - A second label family in Project A's log means game measurements, not process metrics.
- The TL wrote the local format note `.sdlc/local/record-formats.md` (ignored, invented examples only) and marked P-20 done in `TASKS.md`.
- Outcome: not committed (`TASKS.md`, records); the T-20 contract is next.
- Metrics (P-20): review rounds 0, questions back 0, out-of-scope files 0, models Haiku (scout), Haiku (scribe).

## 2026-11-02 (5) - Phase 2 decisions

- The maintainer chose the recommended option on D-21 to D-27. The TL recorded DEC-021 to DEC-027.
  - 9 metrics, all counted by script; M4, M7, M10, M11 dropped (DEC-021).
  - Folded ASCII markers in committed profiles (DEC-022).
  - Three sources: Project A, Project B, this repository (DEC-023).
  - Snapshot into `evidence/raw/` plus a SHA-256 manifest (DEC-024).
  - Cells under 5 items show counts only (DEC-025).
  - Five tasks T-20 to T-24; G2 as 6 checks; the G2 verdict stays with `auditor-mini` (DEC-026).
  - Metrics lines carry the customer result from T-20 on (DEC-027).
- The TL updated `TASKS.md`: G2 row, phase 2 section with the P-20 format pass contract and T-20 to T-24 headlines, NOW NEXT.
- Commit: "Add phase 2 plan and decisions DEC-021 to DEC-027".
- Pushed: 20825a8.

## 2026-11-02 (4) - CTO phase 2 plan

- The maintainer approved calling `cto` for the phase 2 plan (phase boundary, fresh session).
- `cto` (Opus, high) wrote `cto/2026-11-02_phase2-plan.md` (120 lines). Proposals:
  - five tasks: T-20 [H] metrics core and text metrics, T-21 [M] git, audit and decision metrics plus table render, T-22 [M] run on three sources, T-23 [M] `EVIDENCE.md` text, T-24 gate G2;
  - 8 of the 12 day-0 metrics counted by script, 4 dropped, one added (share of hard tasks);
  - G2 as 6 checks: byte-identical rerun, 3 named hand counts, a limits list of at least 9 items, tests, privacy, parse coverage;
  - a `scout` format pass before T-20, so `developer` never reads the private records (DEV_RULES 11).
- Seven questions to the maintainer (D-21 to D-27): metric set, marker words, this repository as a third source, input pinning, small cells, task split, customer outcome field.
- TL checks on the report: 0 characters outside ASCII; banned-word list clean; no source-project name, local path or measured count from the sources.
- `scribe` replaced the stale outcome line of 2026-11-02 (3) with the commit and push lines.
- Outcome: not committed; awaiting the maintainer's answers to D-21 to D-27.
- Metrics (CTO phase 2 plan): review rounds 0, questions back 7, out-of-scope files 0, models Opus (cto), Haiku (scribe).

## 2026-11-02 (3) - G1 re-verification, phase 1 closed

- `auditor-mini` (Opus, high) wrote `audits/2026-11-02_reverify.md`: 14 of 14 findings CLOSED, 4 of 4 verdict conditions met. Verdict: ACCEPT.
  - Recount: 151 C-citations in `PLAYBOOK.md`, 0 missing; core 436 words without brackets; engine name 0 times in the tree; 31 tests passed; guard exit 0.
- Three new Low candidates, not blocking:
  - DEC-020 said the engine name was only in the first commit's history. It is also in a later one.
  - The G1 report keeps a lesson count.
  - DEC-020 said "six questions" while the audit asked five.
  - The TL corrected the DEC-020 wording for the first and third. Audit reports are not edited after they are written, so the second stays (DEC-020).
- Phase 1 closed 2026-11-02. Next: the CTO proposes phase 2 at the phase boundary, in a fresh session.
- Metrics (G1 re-verification): review rounds 0, questions back 0, out-of-scope files 0, models Opus (auditor-mini), Haiku (scribe).
- Commit: "Close phase 1: G1 re-verification ACCEPT".
- Pushed: 599aaf8.

## 2026-11-02 (2) - T-15 G1 fixes

- The maintainer chose the auditor's recommendation on all six audit questions (DEC-020). The read criterion stays; the maintainer reads `PLAYBOOK.md` after the fixes.
- The TL removed the engine name and three measured counts from DEC-006 and DEC-017 (S-1). The first commit keeps the engine name in history; the history is not rewritten (DEC-020).
- `tech-writer` (Sonnet, medium) fixed D-1 to D-9, R-1 and R-2 in `PLAYBOOK.md`, `docs/source-map.md`, `scout.md`, `tech-writer.md`, `templates/audit-report.md` and `CLAUDE.md`, and added one CHANGELOG line. `scribe` removed the lesson count from LOG 2026-10-30 (1).
- TL review round 1 found 4 items, fixed in round 2:
  - "Auditor only" kept against DEC-020;
  - two terms for the person in one sentence;
  - Appendix C still listed four finding types after the template got five;
  - 6 more map rows used "user" for the customer.
- The writer also changed "sets" to "proposes" in Appendix C item 5, to match C-10; the TL accepted it.
- TL checks: guard clean (exit 0); `python -m pytest -q`: 31 passed; ASCII only; banned-word list clean; 87 C-citations in `PLAYBOOK.md` lines, 0 missing; core 434 words; `CLAUDE.md` 80 lines.
- The maintainer read `PLAYBOOK.md` end to end after the fixes (2026-11-02). Corrections: none. This meets the G1 read criterion (P-1).
- Maintainer approved T-14 and T-15 (2026-11-02).
- Commit: "Add G1 audit and fixes (T-14, T-15)".
- Pushed: e42b560.
- Metrics (T-15): review rounds 2, questions back 3 (more "user" rows, "proposes" in Appendix C, length of the core sentence), out-of-scope files 0, models Sonnet (tech-writer), Haiku (scribe).

## 2026-11-02 (1) - T-14 gate G1 audit

- The maintainer said LangGraph is not in this project's scope. The TL confirmed: no record or code uses it, and the decisions fix Python with the MCP SDK (DEC-004, DEC-013).
- The maintainer skimmed `PLAYBOOK.md` instead of reading it end to end, saw no problem, and asked the audit to review its content and to ask the maintainer about any problem.
- Impact note: the G1 criterion "maintainer read it once end to end" is not met by a skim. The TL warned and started the audit at the maintainer's request; the auditor was asked to judge the criterion.
- The TL wrote the T-14 contract in `TASKS.md`.
- `auditor` (Fable, xhigh) wrote `audits/2026-11-02_gate1.md`. Verdict: CONDITIONAL ACCEPT.
  - Traceability passed: 139 citations in `PLAYBOOK.md`, 0 missing, all 64 map rows read against their sources.
  - Privacy passed: tree and 13 commits, 0 hits.
  - Read criterion not met.
- Findings: 0 Critical, 1 High (P-1 read criterion), 4 Medium (P-2 records not current, D-1 writer role missing from the playbook, D-2 Appendix H states a hook the source projects do not have, R-1 `scout.md` says the CTO may invoke it), 8 Low. No code finding. The six lessons: no finding.
- R-1 was a stale line that the T-13 contract named and the TL review missed.
- TL checks on the report: R-1, D-2, D-3 and S-1 confirmed in the files; guard clean over the report; the report names no private source.
- Outcome: 5 questions to the maintainer; the fix contract follows the answers. Not committed.
- Metrics (T-14 audit): review rounds 0, questions back 5, out-of-scope files 0, models Fable (auditor), Haiku (scribe).

## 2026-11-01 (1) - T-13 role files in product form

- The maintainer chose the TL recommendation on 5 open questions:
  - revise the 7 role files and `DEV_RULES.md` in place, each traced to the source map;
  - one term for the customer role (DEC-019);
  - `docs/portability.md` dropped; appendices H and I of `PLAYBOOK.md` are the portability note (DEC-018);
  - report language named in the brief, not in committed files (DEC-019);
  - role files stay in `.claude/agents/`; the plugin copy is T-30.
- The TL found these problems before the contract:
  - a local path and purpose-revealing words in the writer role and the developer rules;
  - source-project details and game-specific folder names;
  - references to a `PLAN.md` that does not exist;
  - stale lines (option b of D-4, hard-coded model versions);
  - scribe formats that did not match `LOG.md` and `STATUS.md`;
  - three terms for the same person.
- `tech-writer` (Sonnet, medium) revised the 7 role files and `DEV_RULES.md`, and added one CHANGELOG line. Each file now ends with a Sources line. Every file grew by 1 to 2 lines.
- TL review round 1 found 4 items, fixed in round 2:
  - Sources lines cited rows the text does not use. Removed: developer C-15, C-16, C-55; cto C-13. The writer also removed auditor C-57, auditor-mini C-11 and C-58, and developer rules C-15 and C-16.
  - Rules without a map row are now traced to project records: `TASKS.md` G4, G5, T-02, phase 4; DEC-007; `CLAUDE.md`.
  - scribe sent check items to "Open questions" instead of "Next".
  - a tool name in a writer rule.
- Acceptance rows C-15, C-16 and C-55 are covered by `PLAYBOOK.md` appendix H. All other acceptance rows are cited in a role file.
- TL checks: guard clean over the changed files (exit 0); `python -m pytest -q`: 31 passed; the 8 files are ASCII only; banned-word list clean; every cited ID exists in the map or the decisions.
- Maintainer approved T-13 (2026-11-01).
- Commit: "Revise role files and developer rules (T-13)".
- Metrics (T-13): review rounds 2, questions back 3 (unsourced rules, a D-x label, a tool name in a rule), out-of-scope files 0, models Sonnet (tech-writer), Haiku (scribe).

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
- Two deviations from the base list. The contract line "no number from a source" was narrowed by the TL to "no measured number" so method parameters (15-line cap, 2 rounds) can be cited. The lesson cap of 3 from the base list was removed by the maintainer (DEC-017): 6 entries of the lessons log are process lessons, and all 6 are in the map (total count removed on 2026-11-02, DEC-020). Gate G1 reviews this choice.
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
