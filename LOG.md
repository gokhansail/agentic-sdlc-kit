# Log

What is this file? A dated record of what was asked, decided, built and checked. Newest entry on top. Entry format: `## YYYY-MM-DD (N) - title`, where N counts entries for that day.

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
