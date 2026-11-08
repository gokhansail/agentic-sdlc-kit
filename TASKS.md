# Tasks

Written by the Technical Lead. Each task is a contract of at most 15 lines: goal, files to touch and not to touch, acceptance, tests, tag. Tags: [E] easy (one file, no behaviour change), [M] medium, [H] hard. A phase gate that is still `[ ]` blocks the next phase. Decisions are in `DECISIONS.md`.

## NOW NEXT
T-33 done 2026-11-07: one real task on Project A, merged by the customer, kit removed, rollback equal to the noted state. G3 passed 2026-11-07 (`auditor-mini` ACCEPT). The 3 open questions are decided (DEC-046, DEC-047, DEC-048). Phase 4 plan written (`cto/2026-11-07_phase4-plan.md`). T-39 done 2026-11-08. Now: T-39a, then T-40 after the customer's 2 server answers.

## Phases

| Phase | Goal | Gate | Verdict by |
|---|---|---|---|
| 0 Setup | decisions, records, guard, toolchain | G0: decisions recorded; guard rejects a planted secret (test); toolchain doc has no "not verified" line for phases 1-3; product `CLAUDE.md` committed (T-05) | TL list + maintainer |
| 1 Playbook | the method in tool-neutral English, no code | G1: every claim maps to a source-map line; no private data; maintainer read it once end to end | `auditor`, then `auditor-mini` |
| 2 Evidence | before/after numbers, reproducible | G2 (DEC-026, DEC-032): rerun from a clean working tree of the gate commit matches the manifest hashes and leaves `evidence/` and `EVIDENCE.md` unchanged; 3 hand counts (H1, H2, H3) match exactly; limits section of at least 9 items; tests green, a known-answer test per metric; guard clean and `evidence/*.json` holds only fixed keys, numbers, dates, hashes and labels; unparsed metric lines 0 or stated in the limits | `auditor-mini` |
| 3 Plugin | Claude Code plugin: roles, commands, hooks | G3 (DEC-043, 9 criteria, evidence in `cto/2026-11-04_phase3-plan.md` section 3): G3-1 plugin validates and loads, as amended by DEC-044; G3-2 scope guard tests per state on captured real hook input; G3-3 scope guard live: a sub-agent write denied and allowed in a real session; G3-4 git hook in a foreign repository, incl. existing hook kept and uninstall; G3-5 one real task on Project A (DEC-033); G3-6 footprint equals the agreed list, rollback rehearsed; G3-7 load, hook and push worked in the customer's own terminal; G3-8 `EVIDENCE.md`, `evidence/` and the Project A manifest unchanged; G3-9 guard clean, role sync test green, toolchain doc current, playbook states the hooks that exist | `auditor`, then `auditor-mini` |
| 4 MCP server | file-based core | G4: tests green; root lock and `..` tests pass; no network; works in Claude Code (DEC-011); eval table from T-46 | `auditor`, then `auditor-mini` |
| 5 Release | README, v0.1.0, marketplace, public | G5: publish-readiness audit incl. git history; every README number reproducible; maintainer says publish | `auditor` |
| 6 Ongoing | dogfood and measurement | none | none |

## Phase 0

### [x] T-01 [E] Decisions
- Goal: settle D-1 to D-11. Result: DEC-001 to DEC-012 in `DECISIONS.md`.

### [x] T-02 [E] Record skeleton (0.0.1)
- Goal: set up the committed record layer (DEC-003).
- Touch: `TASKS.md` (TL), `STATUS.md` (at most 60 lines), `LOG.md`, `CHANGELOG.md` (Unreleased), `LESSONS.md` (empty skeleton), `LICENSE` (MIT, `gokhansail`). Do not touch: `.claude/agents/*`, `DEV_RULES.md`, `README.md`, private files.
- Acceptance: all English, no conversation, no names other than `gokhansail`; `STATUS.md` answers "where are we" on its own; local commit after maintainer approval; no push before T-03.
- Tests: none. Written by TL and `scribe`.

### [x] T-03 [M] Pre-push guard (0.0.1)
- Goal: stop secrets and private content from reaching the remote.
- Touch: `hooks/git/pre-push`, `tools/install_git_hooks.py`, `.sdlc/guard-patterns.txt` (committed, generic), support for `.sdlc/local/private-patterns.txt` (ignored, names and private terms), `tests/test_pre_push.py`, `.gitattributes` (LF for the hook and scripts; the machine converts to CRLF on checkout and a CRLF hook does not run). Do not touch: documents.
- Checks the added lines and commit messages of the commits being pushed: key patterns (`AKIA`, `sk-`, `ghp_`, `xox`), `.env`, private files (plan, private rules), `evidence/raw/`, email addresses other than GitHub noreply, absolute user paths, document and script service URLs, debug flags left on, and non-English letters in English-only files.
- Acceptance: a planted secret is rejected with file, line and pattern; a clean commit passes; a pattern from the local file is caught without that pattern ever being committed; the installer is idempotent; the installed hook runs through a real `git push` to a local bare repository on this machine (Windows, Git Bash; call `python`, not `python3`).
- Tests: reject, pass, local-pattern, installer re-run, end-to-end push to a bare repository. Tag [M], `developer` (Sonnet).

### [x] T-04 [M] Toolchain check
- Goal: confirm every tool and version used in phases 1-4. No guesses.
- Touch: `docs/toolchain.md`, `requirements-dev.txt` (pytest is used by T-03 tests but not declared yet).
- Acceptance: Python 3.10 vs minimum `mcp` SDK version confirmed; Claude Code plugin docs read (`hooks/hooks.json`, `.mcp.json`, `--plugin-dir`, `claude plugin eval`, headless `claude -p` with an MCP config for T-46); how Claude Code treats an `@` import in `CLAUDE.md` when the imported file is missing (needed by T-05); each line has a source link and a date.
- Tests: none. `scout` reads, `developer` tries the install, TL writes.

### [x] T-05 [E] Product CLAUDE.md (after T-04; scope widened by DEC-015)
- Goal: a committed English `CLAUDE.md` of at most 80 lines that tells any session how this repository is run: roles, records, task loop, gates, language, guard. It is part of the evidence that the project uses its own process.
- Touch: `CLAUDE.md` (replaced by the product version), `.gitignore` (replace the `CLAUDE.md` line with `CLAUDE.local.md`), `CLAUDE.local.md` (new, ignored; takes the current private session instructions, DEC-014). Do not touch: role files, `DEV_RULES.md`, other records.
- Acceptance: no private content in the committed file and no private file name in it (guard passes); a fresh session in this folder still gets the maintainer's private instructions; a clone without `CLAUDE.local.md` works; writing rules from DEC-003 hold.
- Tests: guard run over the new file. `tech-writer` writes the English text from a TL brief; TL moves the private text.

## Phase 1

### [x] T-10 [M] Source map
- Goal: `docs/source-map.md` lists every concept the playbook may use, each with a source ID and section, so T-11 to T-13 and G1 can trace every claim (DEC-016).
- Steps: `scout` (Haiku) reads the sources on the base list kept outside the repository, read only, and returns concept, source, section, one-line summary. `tech-writer` (Sonnet) writes the map and the local index from that list. The TL checks rows against the sources.
- Touch: `docs/source-map.md` (new), `.sdlc/local/source-index.md` (new, ignored: source ID to real file), `CHANGELOG.md` (one line). Do not touch: the sources, `PLAYBOOK.md`, templates, role files, other records.
- Format: a source table (ID, generic description such as "agent working standard" or "Project A work rules", language) and a concept table (ID, concept, source ID and section, target part: T-11, T-12 or T-13). Lessons: every process lesson, anonymous (DEC-017).
- Acceptance: every row of the base list is covered or listed as dropped with a reason; every source ID resolves in the local index; the committed file has no source file name, path, project or person name, and no measured number taken from a source (counts, usage, prices; these come only from phase 2; method parameters such as the 15-line cap are allowed); guard clean; the writing-style list holds.
- Tests: guard run over the new committed file; `python -m pytest -q` stays green.

### [x] T-11 [H] PLAYBOOK.md
- Result: draft committed; one heading fixed after review ("What it is not" to "Scope and limits"). The maintainer read a TL summary, not the file end to end; the G1 read item stays open.
- Goal: `PLAYBOOK.md` states the method in tool-neutral English: a core of at most one page, then appendices. Every claim traces to a row of `docs/source-map.md`.
- Writer: `tech-writer` (Sonnet, effort high), two rounds at most. Reads `docs/source-map.md`, `CLAUDE.md`, `DECISIONS.md`; never the private sources.
- Touch: `PLAYBOOK.md` (new), `CHANGELOG.md` (one line). Do not touch: the source map, templates, role files, other records.
- Core: what the method is and is not, roles, task loop, phase loop and gates, records. Appendices: roles and authority matrix; 8-step task loop; phase loop and gate; flexibility and impact note; flag rule; per-task metrics; decision and lesson records with the six lessons as short anonymous examples; concept versus mechanics; why it is not specific to Claude Code.
- Traceability: each paragraph, list item or table row carries its concept IDs in brackets, e.g. [C-06]. No claim without an ID. No measured numbers (phase 2).
- Acceptance: core at most about 500 words; every cited ID exists in the map; no private names or paths; tool names only in the last two appendices; guard clean; writing-style list holds; maintainer reads it once end to end (may follow later, needed for G1).
- Tests: guard over the file; `python -m pytest -q` stays green; TL counts cited IDs against the map with a one-off script.

### [x] T-12 [M] Templates
- Result: 7 templates in `templates/`, 2 review rounds; size label field (C-52) added in round 2; C-26 moved to T-44.
- Goal: `templates/` holds 7 fill-in templates that match the playbook, so a new project can start the method by copying them.
- Writer: `tech-writer` (Sonnet, effort medium), two rounds at most. Reads `PLAYBOOK.md`, `docs/source-map.md`, `DECISIONS.md` (record format), `DEV_RULES.md`, `CLAUDE.md`; never the private sources.
- Files (new): `templates/task-contract.md` [C-08, C-40], `templates/decision-record.md` [format of `DECISIONS.md`], `templates/lesson-entry.md` [C-48, C-61], `templates/audit-report.md` [C-42, C-43, C-44], `templates/reverify-table.md` [C-37, C-45], `templates/push-checklist.md` [C-25, C-38], `templates/dev-rules.md` [C-18, C-56].
- Also touch: `CHANGELOG.md` (one line); `docs/source-map.md` only the target cell of C-26 (T-12 to T-44). Do not touch: `PLAYBOOK.md`, role files, other records, the guard.
- Form: each file starts with a "What is this file?" line, then the fields, each with a one-line fill-in instruction; it ends with the source IDs it uses. No example data from the source projects. Tool-neutral: no tool or product names.
- Acceptance: each template has every field its source rows name and no field without a source; a filled contract fits in 15 lines; a filled dev-rules file fits in 40 lines; every cited ID exists in the map; no private names or paths; guard clean; writing-style list holds.
- Tests: guard over the new files; `python -m pytest -q` stays green; the TL checks each template's fields against its map rows.
- Deferred: C-26 public endpoint checklist goes to T-44 (the kit has no public endpoint).

### [x] T-13 [M] Role files in product form
- Result: 7 role files and `DEV_RULES.md` revised in 2 rounds, each ends with a Sources line; `docs/portability.md` dropped (DEC-018).
- Goal: the 7 files in `.claude/agents/` and `DEV_RULES.md` hold only rules a stranger can use, each traced to a source-map row or a decision (DEC-018, DEC-019).
- Writer: `tech-writer` (Sonnet, effort medium), two rounds at most. Reads the 8 files, `docs/source-map.md`, `PLAYBOOK.md` appendix A, `DECISIONS.md`, `CLAUDE.md`, `LOG.md` and `STATUS.md` (for their formats); never the private sources.
- Touch: `.claude/agents/{cto,developer,scout,scribe,auditor,auditor-mini,tech-writer}.md`, `DEV_RULES.md`, `CHANGELOG.md` (one line). Do not touch: front matter `name`, `model`, `effort`, `tools`; `PLAYBOOK.md`, templates, the source map, other records, the guard.
- Fix: local paths, private source details, purpose-revealing words and game-specific folder names; references to `PLAN.md` (none exists); stale lines (D-4 option b, hard-coded model versions); formats in `scribe.md` that differ from `LOG.md` and `STATUS.md`; "user" becomes "customer"; report language becomes "the language the brief names".
- Trace: each file ends with one `Sources:` line of C-IDs and DEC-IDs, as in `templates/`. `tech-writer.md` traces to DEC-003 and DEC-015. A rule with no row is removed or listed in the report.
- Acceptance: map rows C-02, C-03, C-15, C-16, C-19, C-20, C-32 to C-37, C-44, C-54, C-55, C-56, C-58 are each cited in a role file or in `PLAYBOOK.md` appendix H; ASCII only; no file grows by more than 5 lines; `DEV_RULES.md` stays under 40 lines; guard clean; writing-style list holds.
- Tests: guard over the changed files; `python -m pytest -q` stays green; the TL checks each cited ID against the map and greps for the fixed items.

### [x] T-14 Gate G1
- Result: `auditor` CONDITIONAL ACCEPT (2026-11-02); answers in DEC-020; fixes in T-15; `auditor-mini` ACCEPT, 14 of 14 findings closed (`audits/2026-11-02_reverify.md`). Phase 1 closed.
- Goal: an independent verdict on phase 1 (ACCEPT, CONDITIONAL ACCEPT or REJECT) in `audits/2026-11-02_gate1.md`.
- Auditor: `auditor` (Fable, xhigh), on the maintainer's machine (DEC-016). Reads the whole repository, its git history, `.sdlc/local/source-index.md` and the private sources it names, read only. No private name, path or quote enters the report.
- Agenda: (1) every claim in `PLAYBOOK.md`, `templates/` and `.claude/agents/` cites an existing row, and the row backs the claim; map rows checked against their source sections (all rows the core cites, at least 15 others); (2) no private data in the tree or the history; (3) the read criterion: the maintainer skimmed `PLAYBOOK.md` on 2026-11-02 and asked this audit to review its content; the auditor judges whether the criterion is met; (4) `PLAYBOOK.md` content: correct, consistent with `CLAUDE.md`, role files and templates, writing-style list; (5) the six lessons (DEC-017): privacy, length, relevance; (6) phase 1 process: T-10 to T-13 records, review rounds, role-exceeded entries.
- Content problems go to the customer as questions in the report; the auditor fixes nothing.
- Then: the TL takes the questions to the maintainer, writes fix contracts, `auditor-mini` re-verifies.

### [x] T-15 [M] G1 fixes
- Result: all findings fixed in 2 rounds; the maintainer read `PLAYBOOK.md` end to end on 2026-11-02, no corrections.
- Goal: close the G1 findings by the answers in DEC-020, so `auditor-mini` can re-verify.
- Writer: `tech-writer` (Sonnet, effort medium), two rounds at most. Reads `audits/2026-11-02_gate1.md` sections 4 and 7, `DECISIONS.md` (DEC-009, DEC-020), the files below; never the private sources.
- Touch: `PLAYBOOK.md` (D-1, D-2, D-3, D-4, D-5, D-9; line 17 "one maintainer" to "one person", D-6); `docs/source-map.md` (C-10 "sets" to "proposes"; "user" to "customer" in the 8 rows of D-6); `.claude/agents/scout.md` (R-1); `.claude/agents/tech-writer.md` (R-2); `templates/audit-report.md` (D-8, cite DEC-020); `CLAUDE.md` (D-7: the 1-2 tasks are the plan, the 3-5 trigger is the ceiling; no new line); `CHANGELOG.md` (one line). The TL edits `DECISIONS.md` (S-1, done); `scribe` edits the count in LOG 2026-10-30 (1).
- Do not touch: other role files, other templates, `DEV_RULES.md`, the audit report, the front matter of role files except the `description` of `scout.md`.
- Acceptance: each finding in the touch list is fixed as the report recommends, or the report lists why not; every cited ID exists; `CLAUDE.md` stays at most 80 lines; ASCII only; guard clean; writing-style list holds.
- Tests: guard over the changed files; `python -m pytest -q` stays green; the TL re-counts the citations in `PLAYBOOK.md` (0 missing).

## Phase 2

Plan: `cto/2026-11-02_phase2-plan.md`. Metrics M1, M2, M3, M5, M6, M8, M9, M12, M13 (DEC-021); folded ASCII markers in committed profiles (DEC-022); three sources: Project A, Project B, this repository (DEC-023); snapshot plus manifest (DEC-024); cells under 5 items show counts only (DEC-025); metrics lines carry the customer result from T-20 on (DEC-027).

### [x] P-20 [E] Record format pass (prerequisite of T-20)
- Result: `.sdlc/local/record-formats.md` written 2026-11-02; Project A has all record types; Project B has changelog, log and one untracked audit report only; open points for T-20 and T-21 listed at the end of the note.
- Goal: `developer` can parse the source record formats without reading the private records (DEV_RULES 11, DEC-026).
- Steps: `scout` (Haiku, low) reads the record files of Project A and Project B named in the brief, read only, and returns per record type: file role, heading and entry grammar, marker words in folded ASCII, metric-line phrasings, date formats, edge cases. No quotes, no names, no counts beyond the number of phrasings. The TL writes the format note from that.
- Touch: `.sdlc/local/record-formats.md` (new, ignored), written by the TL with invented examples only. Do not touch: the sources, committed files.
- Acceptance: every record type that a DEC-021 metric reads is covered for each source that has it; each example in the note is invented; nothing committed.
- Tests: none; guard run over the tree stays clean.

### [x] T-20 [H] Metrics core and text metrics (M1, M2, M5, M6)
- Result: `tools/metrics/` (7 modules), 3 profiles, 97 new tests (128 total green); kit rerun byte-identical; approved by the maintainer 2026-11-03. Limit for T-23: the kit counts every metrics line as a task, incl. CTO plan and audit entries.
- Goal: a standard-library script that counts M1, M2, M5 and M6 from pinned record files, so every published number can be rerun (DEC-021, DEC-024). `developer`, Sonnet, effort high.
- Reads: `cto/2026-11-02_phase2-plan.md` sections 2 and 4; DEC-021 to DEC-025 and DEC-028; `.sdlc/local/record-formats.md` sections "Folding", the changelog and work log of Project A and Project B, "This repository". Never the source folders (DEV_RULES 11).
- Touch: `tools/metrics/{__main__,fold,profile,inputs,records,metrics_text,output}.py`, `tools/metrics/profiles/{project-a,project-b,kit}.json`, `tests/metrics/`, `tests/fixtures/metrics/`, `CHANGELOG.md` (one line). Do not touch: `tools/pre_push_guard.py`, `.gitignore`, `requirements-dev.txt`, the records; no `tools/__init__.py`.
- CLI: `python -m tools.metrics --source <dir> --profile <file> --label <name> --out <file> [--snapshot]`. `--snapshot` copies the record files the profile names into `evidence/raw/<label>/` and writes `manifest.json` there (SHA-256 per file, source HEAD, dirty flag, profile SHA-256). Every run parses the copy only.
- Folding: NFKD, combining marks dropped, dotless i to i, casefold, on every line before matching. Markers are regexes in the profile; no marker literal in code (DEC-022). A metric whose profile entry is empty or whose file is missing shows "no data", never 0.
- Period: v1 before 2026-10-25, v2 from it, by the heading date. A date-range heading takes its end date. An undated heading takes the period of its two dated neighbours when both agree; otherwise it goes to `undated` with a warning.
- M1 (DEC-028): version-level revert headings / all version headings; item-level reverts as a separate count `items`. A revert word in the heading scope or in the work log never counts.
- M2: headings whose status (text after the second em dash) has the to-be-tested marker / all version headings; headings with the no-change marker counted apart as `no_change`.
- M5, M6: per-task metric lines only. M5 is the distribution of review rounds 0, 1, 2, 3+. M6 is the share of tasks with questions back >= 1 and with out-of-scope files >= 1, each over the tasks that carry that field. Session lines, lines without a number and missing fields go to `warnings`, never guessed.
- Output: the schema of plan section 4, plus `undated`; sorted keys, no timestamps. The writer refuses any string that is not a fixed status word, metric ID, warning name, label, ISO date or hex hash.
- Acceptance: each metric matches a fixture with a known answer; one test per metric-line phrasing in the note, with invented English markers; one folding test whose letters are built with `chr()`; two runs give byte-identical JSON; the writer has a refuse test and a pass test (DEV_RULES 9); snapshot paths with `..` or absolute paths outside the root are refused (rule 10); no network, no new dependency; ASCII only; guard clean.
- Tests: `python -m pytest -q` green, summary line pasted. Report to the TL in Turkish.

### [x] T-21 [H] Git, audit, decision and task metrics; table render (M3, M8, M9, M12, M13)
- Result: `gitstats.py`, `metrics_records.py`, `render.py` new, 124 new tests (252 total green, 1 skipped); kit rerun and re-render byte-identical; approved by the maintainer 2026-11-03. Limits for T-23: 12 of 15 kit tasks undated in M13; symlink escape untested on this machine; DEC-029 needs a limits item; full test run takes about 2 minutes.
- Goal: count M3, M8, M9, M12, M13 on the T-20 core and render every result into a marked block, so T-22 only runs and T-23 writes around fixed tables (DEC-021, DEC-025). `developer`, Sonnet, effort high; tag raised from [M]: five metrics, git snapshot, schema change and render in one contract.
- Reads: plan sections 2 and 4; DEC-021 to DEC-025, DEC-029; `.sdlc/local/record-formats.md` sections "Folding", decision log, task list, audit reports, tests (git), "This repository"; the T-20 code. Never the source folders (DEV_RULES 11).
- Touch: `tools/metrics/{gitstats,metrics_records,render}.py` (new); `tools/metrics/{__main__,profile,inputs,output}.py` and the 3 profiles per the plan section 2 table (extend); `tests/metrics/`, `tests/fixtures/metrics/`, `CHANGELOG.md` (one line). Do not touch: `metrics_text.py` behaviour, `tools/pre_push_guard.py`, `.gitignore`, `requirements-dev.txt`, the records; no `EVIDENCE.md` (T-23).
- Snapshot: also copies the files of a profile folder entry (directory plus file-name regex; skip regex), with `tracked` per file in the manifest (DEC-029); writes `git-log.txt` (hash, author date, committer date, up to HEAD) and `git-tests.txt` (ISO week, its last commit by author date, attribute count by `git grep` over the profile path glob). A run without `--snapshot` still reads the copies only.
- M3: attribute count at the last commit of each ISO week, `weeks` {YYYY-Www: count}; the v1 and v2 cell is the count of the last week in that period.
- M12: commits per ISO week by author date, versions per ISO week by changelog heading date; per period `count`, `versions`, `weeks` (ISO weeks from first to last item, empty weeks included). Author dates outside the committer-date span are counted and go to `warnings`.
- M8: findings per report, period by report date; severity from the heading, else the first severity line of the finding; key = report date + ID; a re-verify row links to the latest audit report on or before its date that has that ID; status = first word of the cell. Per period: `severity` counts, `latest` status counts (`none` if never re-verified), `days_to_closed` distribution 0, 1-3, 4-7, 8+.
- M9: entries from the first entry heading on; date from the heading or the entry's date line; filled = outcome not empty and not the profile's empty pattern; an entry without an outcome field goes to `warnings`, not to n.
- M13: task headings with a size tag, mapped to E, M, H by the profile; `distribution` and `done`; period by the done date when present, else `undated`; untagged headings go to `warnings`.
- Output: the writer allowlist grows by these keys and by ISO week, severity, status and tag labels only; the refuse test still passes. Render: `python -m tools.metrics.render --doc <file> <json>...` validates each JSON, rewrites only the block between `<!-- metrics:begin -->` and `<!-- metrics:end -->`, refuses a missing or doubled marker; one table per metric, columns source and period; a cell under 5 items shows the count and no rate (DEC-025); "no data" stays "no data".
- Acceptance: each metric matches a fixture with a known answer; git metrics from a repository built in a temp dir with fixed author and committer dates (pattern of `tests/test_pre_push.py`); one test per layout in the note (finding heading and severity line, re-verify table, decision heading and outcome layouts, task tag sets) with invented English markers; re-render gives no diff and leaves text outside the block unchanged; two runs byte-identical; no network, no new dependency; ASCII only; guard clean.
- Tests: `python -m pytest -q` green, summary line pasted. Report to the TL in Turkish.
### [x] T-22 [M] Run on the three sources (`scout`, runs only; totals to `evidence/*.json`)
- Result: three snapshots, reruns byte-identical; kit clean, Project A and B dirty (recorded); coverage gap in Project A fixed by T-22a; approved by the maintainer 2026-11-04. Limits for T-23: one Project A entry unparsed; Project B v1 only for M3, M8, M12; kit has no version data.
- Goal: one pinned run per source, so T-23 writes around fixed numbers and G2 can rerun them (DEC-023, DEC-024). `scout`, Haiku, effort low; runs commands, edits no file.
- Order: the TL commits this contract first, so the kit snapshot has `dirty: false`. Source paths go in the brief only, never in a committed file.
- Runs: `python -m tools.metrics --source <dir> --profile tools/metrics/profiles/<label>.json --label <label> --out evidence/<label>.json --snapshot` for `project-a`, `project-b`, `kit`; then the same three again without `--snapshot` and `--source`.
- Touch: `evidence/{project-a,project-b,kit}.json` (new, committed); `evidence/raw/` (local, ignored). Do not touch: the sources, `tools/`, `tests/`, the records, `EVIDENCE.md` (T-23).
- Acceptance: the second run gives byte-identical JSON per source (SHA-256 compare); each JSON has `input.head`, `input.dirty`, a SHA-256 per file and `profile_sha256`; `git status --porcelain` lists nothing under `evidence/raw/`.
- Parse coverage (G2 check 6): per source, lines in the snapshot copy of the log that match the loose pattern the TL names in the brief (the profile's `task_line` marker word, no anchors), minus the lines the run counted (n plus that metric's line warnings).
- Checks: `python tools/pre_push_guard.py --files evidence/*.json` exit 0; `python -m pytest -q` still green.
- Report to the TL in Turkish: per source and metric, status, n per period, warning counts; manifest short head and dirty flag; the coverage numbers. Numbers only: no source file names, no quotes, no record text.
- After: the TL checks the numbers against the T-21 kit hand counts, writes the DEC-010 outcome and the limits found for T-23; `scribe` writes LOG, STATUS, the metrics line and one CHANGELOG line.
### [x] T-22a [M] Project A: two more metric-line layouts (M5, M6)
- Result: `task_lines` in `profile.py` and `metrics_text.py`, 12 new tests (271 total green, 1 skipped); Project A M5 v2 n 10 to 18, 19 of 20 entries parsed; kit result unchanged; approved by the maintainer 2026-11-04.
- Goal: count the Project A tasks whose numbers sit mid-line or in a TL review line, so M5 and M6 cover 19 of 20 v2 log entries with task numbers instead of 11 (DEC-030). `developer`, Sonnet, effort medium. Found by the T-22 coverage check.
- Reads: DEC-030; `.sdlc/local/record-formats.md` sections "Folding" and Project A "Work log" (layouts 1 to 3); the T-20 code. Never the source folders or `evidence/raw/project-*` (DEV_RULES 11).
- Rule: a profile may give `task_lines`, an ordered list, in place of `task_line`; each item has its own line regex and its own fields. Per entry, the first item in list order that matches a line of that entry gives the entry's one task; any other matching line in that entry is ignored and counted as warning `<tag>_extra_task_line`. Session lines keep their current handling.
- Project A profile: item 1 the metrics label anywhere in a bullet (layouts 1, 2); item 2 a bullet starting with the TL review label that holds `tur <n>`, review rounds = n as written (layout 3). Questions back and out-of-scope fields as today in both.
- Unchanged: a profile with `task_line` gives the same result as before; `evidence/kit.json` rerun from its snapshot keeps SHA-256 `4a5b2e99...`. Do not touch: `metrics_records.py`, `gitstats.py`, `render.py`, the kit and Project B profiles, the guard, `.gitignore`, `evidence/`.
- Touch: `tools/metrics/{profile,metrics_text}.py`, `tools/metrics/profiles/project-a.json`, `tests/metrics/`, `tests/fixtures/metrics/`, `CHANGELOG.md` (one line).
- Acceptance: one fixture test per layout with invented English markers; a test for an entry with lines of both items (item 1 wins, one warning); a test that `task_line` and `task_lines` together are refused; no network, no new dependency; ASCII only; guard clean.
- Tests: `python -m pytest -q` green, summary line pasted. Report to the TL in Turkish.
- After: `scout` reruns Project A from its existing snapshot (same input hashes); the TL repeats the coverage count and checks whether item 2 added v1 tasks.
### [x] T-23 [M] `EVIDENCE.md` prose and limits (`tech-writer`)
- Result: `EVIDENCE.md` with 9 metrics and 18 limits items, tables rendered, second render no change; 271 tests green; 1 fix round, 9 fixes; approved by the maintainer 2026-11-04. For T-24: `evidence/raw/` is ignored by git, so a clean checkout holds no snapshot; the numbers outside the block are checked by hand (DEC-031).
- Goal: a reader sees what was measured, how to rerun it, the results, and what they do not show (DEC-010, DEC-021, DEC-031). `tech-writer`, Sonnet, effort medium.
- Input: the TL's brief holds the facts with their sources; the rendered tables come from a local file. The writer does not read `evidence/raw/` or `.sdlc/local/`.
- Sections: what this is; sources and periods; metrics and counting rules (9 metrics, one line each); results (the two marker lines of `render`); how to read the results; limits; how to rerun.
- Results rule: metric results sit only between the markers. Outside: method dates and thresholds, and limits numbers with a named source (DEC-031).
- Reading section: covers all 9 metrics, including those that did not improve; repeats no number; no causal wording.
- Limits: the 9 items of G2 check 3, plus: the Project B audit folder not tracked in git (DEC-029); parse coverage per source; two meanings of the review round number (DEC-030); the kit counts every metric line as a task; undated tasks in M13; M8 closure data exists for the kit only.
- Privacy: Project A and Project B only; no engine, tool or source names; no record text.
- Touch: `EVIDENCE.md` (new), `CHANGELOG.md` (one line). Do not touch: anything else.
- Acceptance: limits section of at least 9 items; every number outside the markers traces to the brief; writing-style list holds; ASCII only; `what is this file` line on top.
- After: the TL runs `python -m tools.metrics.render --doc EVIDENCE.md evidence/project-a.json evidence/project-b.json evidence/kit.json` twice (second run no diff), the guard over `EVIDENCE.md`, and `python -m pytest -q`; `scribe` writes LOG, STATUS and the metrics line.
- Report to the TL in Turkish: sections, limits count, any number or claim the brief did not support.
### [x] T-24 Gate G2 (`auditor-mini`)
- Result: `auditor-mini` ACCEPT (2026-11-04), 7 checks closed; 5 candidates: N-1 to N-4 closed in T-24a, N-5 moved to G5; reports `audits/2026-11-04_gate2.md`, `audits/2026-11-04_reverify.md`; phase 2 closed by the maintainer 2026-11-04.
- Goal: the G2 verdict: the 6 checks of `cto/2026-11-02_phase2-plan.md` section 3 plus the hand-written numbers (DEC-026, DEC-031, DEC-032). `auditor-mini`, Opus, effort high. ACCEPT / CONDITIONAL / REJECT; fixes nothing.
- Order: the TL commits this contract first; that commit is the gate commit. Phase 2 range: `e42b560..` the gate commit.
- Check 1 reproduce (DEC-032): with `git status --porcelain` empty in this folder, rerun `python -m tools.metrics --profile tools/metrics/profiles/<label>.json --label <label> --out evidence/<label>.json` for `project-a`, `project-b`, `kit`, then `render` as in T-23. Pass: snapshot hashes equal `input` in each result file; `git status --porcelain evidence/ EVIDENCE.md` prints nothing. On a difference, leave the tree and report it.
- Check 2 hand counts: H1, H2, H3 from the snapshot copies in `evidence/raw/`, without `tools/metrics`; exact equality with `EVIDENCE.md`. One may be replaced by a pick of the auditor's own, with the reason.
- Check 3 limits: each item of section 3 check 3 is present in `EVIDENCE.md`; at least 9.
- Check 4 tests: `python -m pytest -q` green; a known-answer test per metric; a determinism test; a test that the JSON writer refuses a free-text value.
- Check 5 privacy: guard exit 0 over the tree and the phase 2 commits; `evidence/*.json` holds only fixed keys, numbers, dates, hashes and the 3 labels.
- Check 6 parse coverage: per source, loose metric-line matches minus lines parsed, recounted on the snapshots; 0, or the count is in the limits.
- Check 7 hand-written numbers (DEC-031): every number outside the marked block traces to its named source and equals it; no metric result sits outside the block.
- Report: `audits/2026-11-04_gate2.md`, English, a table check | evidence | status, then the verdict. Totals only: no record text, no quotes, no marker words, no source paths. `python tools/pre_push_guard.py --files` on it: exit 0.
- Touch: that report only. Source paths go in the brief, never in a committed file.
- Return to the TL in Turkish, at most 15 lines.
- After: the TL checks the report; `scribe` writes LOG, STATUS and the metrics line; the maintainer decides on closing phase 2.

### [x] T-24a [M] G2 candidates N-1 to N-4 in `EVIDENCE.md` (`tech-writer`)
- Result: `EVIDENCE.md` holds 21 limits items; first recheck CONDITIONAL on one sentence of limit 21, second ACCEPT; approved by the maintainer 2026-11-04.
- Goal: close the four candidates of `audits/2026-11-04_gate2.md` that touch how the numbers read, before phase 2 closes. Text only. `tech-writer`, Sonnet, effort medium.
- N-1: new limit: 2 Project A tasks count 1 lower in M5 than in the session line of the same log; the distribution with the session values is stated, with its source.
- N-2: the M9 rule says entries with an outcome field; new limit: 15 of 58 Project A entries have no such field and are outside n.
- N-3: limit 16 states the real reasons; the kit loose pattern is named. The TL corrects the DEC-030 outcome.
- N-4: new limit on the Project A result file; the rerun section says `kit_commit` records the commit at snapshot time. No rerun, no tool change.
- Touch: `EVIDENCE.md`. The tables stay as rendered. Limits 1 to 18 keep their numbers. No new CHANGELOG line; the [Unreleased] line covers it. Do not touch: `tools/`, `evidence/`, the audit report.
- Acceptance: the same style list, ASCII only, every new number traces to the brief; second `render` no change; guard exit 0; `python -m pytest -q` green.
- After: `auditor-mini` rechecks the changed lines and N-1 to N-4 and writes `audits/2026-11-04_reverify.md`; `scribe` writes LOG, STATUS and the metrics line.
- N-5 is not in this task: it moves to G5 (Later phases), because the text is already in the git history.

## Phase 3

Plan: `cto/2026-11-04_phase3-plan.md`. T-33 runs in Project A's own repository under a written exception, after P-33 (DEC-033); output in `docs/dogfood-1.md`, `EVIDENCE.md` unchanged (DEC-034); `agents/` is the role source (DEC-035); aliases for models (DEC-036); guard states (DEC-037, DEC-038, DEC-039); Python launcher (DEC-040); 5 commands (DEC-041); installer target mode (DEC-042); split and terminal (DEC-043). Headlines only; each contract is written when its turn comes, after the customer's go-ahead. New contracts use `Files in` and `Files out` (DEC-037).

Order:
- [x] P-30 [M] plugin facts probe: closes V-1 to V-9 and V-12. Results in `docs/toolchain.md`.
- [x] T-30 [M] skeleton and role files. Needs P-30.
- [x] T-31 [H] scope guard hook. Needs P-30.
- [x] T-32 [H] git hook installer, target mode. Needs T-30.
- [x] T-30a [M] the 5 commands. Needs T-31, T-32.
- [x] T-33a [E] `--snapshot` refuses over an existing manifest.
- [x] P-33 [M] rehearsal in a throwaway clone, customer's terminal. Needs T-30a, T-32. Watch: main-session writes outside the root are denied (DEC-037 outcome); record whether that blocks useful work. Prepare: a clone of this repository holds a tracked `.sdlc/guard-patterns.txt` with the language line, and the installer keeps it (checked in T-32 review), so remove that file in the clone before install or the planned non-English record line is rejected.
- [x] T-30b [E] `init` and `contract` write through the file tools. Found by P-33.
- [x] T-33 [M] one real task on Project A, customer's terminal. Needs P-33, T-33a, T-30b. The customer picks the task with that project's TL session. Result 2026-11-07: a medium task, 10-line contract, 39 guard events (38 allow, 1 deny outside the root), 0 out-of-scope files, 155 of 158 tests pass and 0 fail, 4 pushes through the chained hook, fast-forward merge; developer review rounds 3, over the 2-round rule. Totals and 9 findings in `docs/dogfood-1.md`.
- [x] T-33b [M] sub-agents cannot change the developer rules file without a contract line. Found by T-33 (finding 4, DEC-045).
- [x] T-34 gate G3: `auditor`, then `auditor-mini`. `auditor` 2026-11-07: CONDITIONAL ACCEPT (`audits/2026-11-07_gate3.md`); fix round T-34a; `auditor-mini` 2026-11-07: ACCEPT, 9 of 9 closed (`audits/2026-11-07_gate3_reverify.md`). G3 passed.
- [x] T-34a [E] G3 fix round: line endings for `.md` and `.txt` (C-1), `DEV_RULES.md` pointer (D-3); the TL closes P-1, P-2, D-3 and the G3-7 record.

### [x] P-30 [M] Plugin facts probe (`developer`, Sonnet, effort medium)
- Result: 14 runs and 1 customer terminal run. No result contradicts a decision. Still open: true process crash, `$CLAUDE_PLUGIN_ROOT` in the Bash tool, a desktop app session, a populated `.claude/` (`docs/toolchain.md`).
- Size: medium.
- Goal: V-1 to V-6, V-8, V-9 and V-12 of `cto/2026-11-04_phase3-plan.md` section 5 each end as confirmed, refuted or not settled, with the observation. V-7 falls away (DEC-039). No product code.
- Method: one throwaway plugin: a copy of the 7 role files, a root shaped like this repository (`hooks/git/`, `tools/`, `tests/`, `.claude/`), one skill, a PreToolUse hook on `Write|Edit|NotebookEdit` that logs its stdin and the names of its `CLAUDE_*` variables.
- Place: a throwaway folder in the home directory, outside `AppData` and outside any repository; the brief names it. Every run has it as working directory. Never this repository, Project A or Project B.
- Limits: at most 12 `claude -p` runs, each `--model haiku`, `--max-turns 8`, `--permission-mode acceptEdits`. No permission bypass flag, no `claude plugin install`, no change to user settings. Amended 2026-11-05 with the customer's word: 2 more runs, 14 in all, same flags: one sub-agent with `model: sonnet` (does `model` take effect), one `Edit` (real hook input).
- Hook cases: exit 0, exit 2, exit 1, a crash, and a timeout of 2 s, each with one write; a write from the main session against one from a sub-agent; the `NotebookEdit` field name.
- Files in: `.sdlc/local/p30-results.md` (ignored by git): one row per V item with status, command, observation and CLI version. `.sdlc/local/p30-capture/` (ignored by git): one JSON per hook case, paths replaced by invented ones, session IDs removed.
- Files out: everything tracked in this repository, incl. `docs/toolchain.md` (the TL writes it), `.claude/` and `CHANGELOG.md`.
- Acceptance: every V item has a row; a confirmed or refuted row names the run that shows it; the V-4 row states whether the hook fired in the sub-agent and which input field names the agent; `git status --porcelain` is empty afterwards.
- Tests: no new test. `python -m pytest -q` stays green, summary line pasted.
- Design reference: `cto/2026-11-04_phase3-plan.md` sections 2 and 5; DEC-037, DEC-040, DEC-041, DEC-043.
- Flag: none.
- Customer test: one load command given in the report, run in a terminal the customer opened; the result goes in the V-9 row. The desktop half of V-9 may stay not settled (DEC-043).
- Report to the TL in Turkish, fixed format, one line per V item. A result that contradicts a decision is an OPEN QUESTION, not a change of plan.
- After: the TL writes the results into `docs/toolchain.md` with one CHANGELOG line and removes the throwaway folder after the customer test; a refuted fact that changes a decision goes to the customer; `scribe` writes LOG, STATUS and the metrics line.

### [x] T-30 [M] Skeleton and role files (`developer`, Sonnet, effort medium)
- Result: plugin `sdlc` loads with 7 agents; 280 tests green, 1 skipped; strict validate as in DEC-044; about 837 tokens added to every session.
- Size: medium.
- Goal: the repository root loads as plugin `sdlc` with 7 agents; `agents/` is the role source and `.claude/agents/` a tested copy (DEC-035); role text no longer assumes this repository's record names. No commands and no hook: those are T-30a and T-31.
- Manifest: `.claude-plugin/plugin.json` with `name` `sdlc`, `version` `0.0.1`, `description`, `author.name` `gokhansail`, `license` `MIT`. `author` is needed for `--strict` (P-30). No email, no URL.
- Roles: copy the 7 files to `agents/`, frontmatter unchanged, aliases stay (DEC-036). In the 6 files that name records (all but `tech-writer.md`), in both folders, add after the opening paragraph: "Record names: this role uses the default names (`TASKS.md`, `DECISIONS.md`, `STATUS.md`, `LOG.md`, `CHANGELOG.md`, `DEV_RULES.md`). If `.sdlc/project.md` exists, its record map gives the real file for each." In `scout.md` replace the `python -m tools.metrics <path>` example with "run the project's measurement script on <path>". No other wording change.
- Files in: `.claude-plugin/plugin.json`, `agents/*.md`, `.claude/agents/*.md`, `tests/test_role_sync.py`, one `CHANGELOG.md` line.
- Files out: everything else, incl. `hooks/`, `skills/`, `tools/`, `DEV_RULES.md`, `CLAUDE.md`, `docs/`, `evidence/`, `EVIDENCE.md`.
- Limits: at most 2 `claude -p` runs, each `--model haiku`, `--max-turns 3`, working directory a throwaway folder in the scratchpad, never Project A or Project B. No permission bypass flag, no `claude plugin install`, no change to user settings.
- Acceptance: on a clean copy `claude plugin validate . --strict --json` holds the `CLAUDE.md` root warning and no other finding, and plain `validate` exits 0 (DEC-044); one `claude --plugin-dir <repository> -p` run lists the 7 `sdlc:` agents, with `.claude/` populated as it is here (closes the last "not verified" line of `docs/toolchain.md`); the `claude plugin details` token cost is in the report; no local path in a tracked file; guard exit 0 over the changed files.
- Tests: `tests/test_role_sync.py`: the two folders hold the same 7 names and the same text after line endings are normalized; `model` is one of `opus`, `sonnet`, `haiku`, `fable` and `effort` one of `low`, `medium`, `high`, `xhigh` in every role, because validate does not check values (P-30). The comparison shows one test that fails on a planted difference and one that passes (DEV_RULES 9). `python -m pytest -q` green, summary line pasted.
- Design reference: `cto/2026-11-04_phase3-plan.md` sections 2 and 5, debt list; DEC-035, DEC-036, DEC-037.
- Flag: none.
- Customer test: none; nothing changes in use yet. The first run in the customer's terminal is P-33.
- Report to the TL in Turkish, fixed format. A result that contradicts a decision is an OPEN QUESTION.
- After: the TL updates `docs/toolchain.md` and `CLAUDE.md` (role source folder); `scribe` writes LOG, STATUS and the metrics line.

### [x] T-31 [H] Scope guard hook (`developer`, Sonnet, effort high)
- Result: guard denies and allows in live runs, sub-agent included; 388 tests green, 1 skipped; 13 of 13 planted faults caught after one test fix; median 422 ms to 598 ms per call. Live check in a real terminal: P-33.
- Size: hard.
- Goal: with the plugin loaded, an opted-in project gets each `Write`, `Edit` and `NotebookEdit` call allowed or denied by the active contract, per the state table of D-35 in the CTO report (DEC-037). It catches a developer leaving its contract by mistake and is not a security boundary (DEC-038). No bypass (DEC-039). No commands: those are T-30a.
- Parts: `hooks/hooks.json` (matcher `Write|Edit|NotebookEdit`, timeout 30 s, because a timeout lets the write through, P-30); `hooks/scope/launcher.sh`; `tools/scope_guard.py`, standard library only, with parser and decision as functions T-41 can import.
- Launcher (DEC-040): no `.sdlc/project.md` under `CLAUDE_PROJECT_DIR`: exit 0 before Python starts. Otherwise find a Python of at least 3.10 (`python`, `python3`, `py -3`; the store stub must not count), run it with `-I` and `PYTHONUTF8=1`, and turn any result other than 0 or 2 into exit 2 with a reason.
- Grammar: `.sdlc/project.md`: backticked globs in a `## Always allowed` section; no section means an empty list. `.sdlc/active-contract.md`: one heading holding the task ID, one `Files in` line and one `Files out` line as in `templates/task-contract.md`. Only backticked tokens count; braces expand; a trailing `/` is a folder; `*` and `**` work. No token in `Files in`, or a missing or repeated field, is a broken contract.
- Rules beyond the table: the path comes from `file_path` or `notebook_path`; a missing field or bad JSON is a deny. Outside the root is a deny, `..` resolved, `/` and `\` unified, case-insensitive on Windows. A sub-agent (`agent_id` or `agent_type` in the input) never writes under `.sdlc/`, in any state. The main session may always write under `.sdlc/`, so the TL can place a contract. `Files out` wins over `Files in` and the always-allowed list. A deny is exit 2 with state, relative path and next step on stderr. One event line per decision in `.sdlc/metrics.jsonl`: date, task ID, state, decision, tool, agent if any, no path; a failed log write does not change the decision.
- Files in: `hooks/hooks.json`, `hooks/scope/launcher.sh`, `tools/scope_guard.py`, `tests/test_scope_guard.py`, `tests/fixtures/scope/*`, `.gitignore` (`.sdlc/metrics.jsonl`, `.sdlc/active-contract.md`), one `CHANGELOG.md` line.
- Files out: everything else, incl. `agents/`, `.claude/`, `hooks/git/`, `tools/pre_push_guard.py`, `tools/install_git_hooks.py`, `DEV_RULES.md`, `PLAYBOOK.md`, `docs/`, `evidence/`, `EVIDENCE.md`. No `.sdlc/project.md` in this repository.
- Limits: at most 3 `claude -p` runs, each `--model haiku`, `--max-turns 8`, `--permission-mode acceptEdits`, in a throwaway folder in the scratchpad, never Project A or Project B. No permission bypass flag, no `claude plugin install`, no change to user settings.
- Acceptance: live runs show a main-session write denied with no contract, one allowed inside a contract, and a write by `sdlc:scribe` outside the contract denied, each with its event line; `claude plugin details` lists 1 hook; strict validate on a clean copy holds no finding beyond DEC-044; median time per call over 20 calls reported against the 1 s budget, over budget is an OPEN QUESTION; guard exit 0 over the changed files.
- Tests: `tests/test_scope_guard.py`: one block and one pass test per state; `..`, absolute outside the root, case and separator variants; `Files out` wins; backticks only and braces; broken contract; sub-agent and main session under `.sdlc/`; each of the 3 path fields of the captured tools; launcher with no Python, a too-old Python, a missing script and a crashing script all exit 2 in an opted-in project; not opted in passes with no Python on `PATH`; the event line holds no path. Fixtures: copies of `.sdlc/local/p30-capture/` with `{ROOT}` in place of paths, because the pre-push guard rejects absolute user paths. `python -m pytest -q` green, summary line pasted.
- Design reference: `cto/2026-11-04_phase3-plan.md` D-35 to D-38; DEC-037 to DEC-040; `docs/toolchain.md` section "Plugin facts measured".
- Flag: none. Removing `.sdlc/project.md` turns the guard off (DEC-039).
- Customer test: none here; the live check in the customer's terminal is P-33 (G3-3).
- Report to the TL in Turkish, fixed format; a result that contradicts a decision is an OPEN QUESTION. After: the TL updates `docs/toolchain.md` and the DEC-040 outcome (timeout limit); `tech-writer` updates `PLAYBOOK.md` Appendix H and the Enforcement field of `templates/dev-rules.md`; `scribe` writes LOG, STATUS and the metrics line.

### [x] T-32 [H] Git hook installer, target mode (`developer`, Sonnet, effort high)
- Result: target mode built; 437 tests green, 1 skipped; 35 of 35 planted faults caught after one test fix round; the TL's own run in temp repositories passed. Live check in the customer's terminal: P-33.
- Size: hard.
- Goal: `python tools/install_git_hooks.py --target <repo>` gives a repository that is not this one the pre-push guard, keeps its existing pre-push hook running, and `--uninstall` returns its hook folder byte for byte (DEC-042). Kit mode behaves as today. No command: `/sdlc:install-hooks` is T-30a.
- Install: paths come from `git rev-parse --git-path`, not from joining `.git`. Exit 1 with nothing written for: not a git repository, a bare repository, `core.hooksPath` set at any config scope, `.sdlc` being a file, a saved old hook beside a `pre-push` that is not our wrapper. `--force` with `--target`, and `--refresh` or `--uninstall` without it, are refused. Writes: `.sdlc/guard/pre_push_guard.py` (copy); `.sdlc/guard-patterns.txt` from the template and an empty `.sdlc/local/private-patterns.txt`, each only if absent; one `.sdlc/` line in `info/exclude`, only if absent; the old hook moved to `hooks/pre-push.sdlc-old`, bytes and mode kept; the wrapper at `hooks/pre-push` with LF endings.
- Wrapper: `sh`, with a marker line. It reads stdin once, runs the saved hook first, if any, with the same arguments and the same stdin bytes, and a non-zero result stops the push with that code. It then runs the guard with the same input, under the Python search of `hooks/scope/launcher.sh` and `-I -X utf8`. No Python, or a missing guard or pattern file: exit 1 with a reason (fails closed, DEC-042).
- Rerun and uninstall: copy and wrapper equal to the kit's: "no change", exit 0, and the wrapper is never saved as the old hook. Different: reports stale, exit 1, changes nothing; `--refresh` replaces the copy and the wrapper, never the patterns. `--target <repo> --uninstall` removes the wrapper, puts the saved hook back, removes `.sdlc/guard/`, and prints what stays for the manual rollback step: the patterns, `.sdlc/local/`, the exclude line (DEC-033). Not installed: "no change", exit 0. A `pre-push` without the marker: refused.
- Guard and template: the public pattern file may hold `forbid-path <glob>` lines; a glob with no `/` matches the file name in any folder, otherwise the full path. Any such line replaces `FORBIDDEN_PATHS`; a file with none keeps that list. In the private file such a line is a broken pattern (fails closed). `CONTENT_EXEMPT` gains `templates/guard-patterns.txt`. That file has a "What is this file?" comment, every pattern of `.sdlc/guard-patterns.txt` except `non-english-char`, and `forbid-path` lines for the list without `PLAN.md` and `evidence/raw/*`.
- Files in: `tools/install_git_hooks.py`, `tools/pre_push_guard.py`, `templates/guard-patterns.txt`, `tests/test_install_target.py`, one `CHANGELOG.md` line.
- Files out: everything else, incl. `tests/test_pre_push.py`, `hooks/`, `.sdlc/guard-patterns.txt`, `agents/`, `.claude/`, `skills/`, `docs/`, `PLAYBOOK.md`, `evidence/`, `EVIDENCE.md`.
- Limits: no `claude -p` run. Temp folders only, never Project A or Project B. This repository's git config is not changed. State in the report: a linked worktree of a target fails closed, because `.sdlc/guard/` is per worktree.
- Acceptance: in a foreign repository built in a temp folder, with an existing pre-push hook, real `git push` runs to a local bare repository: a clean push passes and the old hook saw the same stdin; a planted secret is rejected; a failing old hook blocks. After uninstall the SHA-256 of every file in the hook folder equals the values before install and `core.hooksPath` is unset. `tests/test_pre_push.py` is unchanged and its 31 tests pass. Guard exit 0 over the changed files.
- Tests: `tests/test_install_target.py`: one refuse and one pass per refusal (DEV_RULES 9); with and without an old hook; a rerun does not chain twice; stale and `--refresh`; two refs on stdin; a target path with a space and a non-ASCII letter built with `chr()`; `--target` with `..` segments (rule 10); patterns never overwritten; no kit term in the created private file; the exclude line once, also in a file with no final newline; only LF in the wrapper; no Python on `PATH` and a missing guard both block; `forbid-path` replaces the list and an absent one keeps it; the template equals the kit file without the language line. `python -m pytest -q` green, summary line pasted.
- Design reference: `cto/2026-11-04_phase3-plan.md` D-40 and D-31 rollback; DEC-033, DEC-040, DEC-042; `docs/toolchain.md`.
- Flag: none. `--uninstall` removes it.
- Customer test: none here; the first real use is P-33 (G3-4).
- Report to the TL in Turkish, fixed format; a result that contradicts a decision is an OPEN QUESTION. After: the TL updates `docs/toolchain.md` and the DEC-042 outcome; `tech-writer` updates `PLAYBOOK.md` Appendix H if the hooks it states changed; `scribe` writes LOG, STATUS and the metrics line.

### [x] T-30a [M] The 5 commands (`developer`, Sonnet, effort medium)
- Result: 5 skills, `templates/project.md`, 2 script modes; 498 tests green, 1 skipped; 28 of 28 planted faults caught after one fix round; every acceptance step seen in 9 Haiku runs. Live check in the customer's terminal: P-33.
- Size: medium.
- Goal: with the plugin loaded, a customer can run the whole loop in a project: `/sdlc:status`, `/sdlc:init`, `/sdlc:contract`, `/sdlc:review`, `/sdlc:install-hooks` (DEC-041). Each skill is thin: logic stays in scripts and templates.
- Form: `skills/<name>/SKILL.md`, at most 40 lines each, English, ASCII, a one-line `description`. Plugin paths only as `${CLAUDE_PLUGIN_ROOT}` in the skill text, never `$CLAUDE_PLUGIN_ROOT` (V-8). Python as in `hooks/scope/launcher.sh`: `python`, then `python3`, then `py -3`. Record names come from the record map in `.sdlc/project.md`, default names when it is absent.
- `status`: read only. Reports phase, open task, next step and open questions from the records. `init`: `disable-model-invocation: true`. Refuses if `.sdlc/project.md` exists. Finds the project's records and test folders, shows the proposed file from `templates/project.md`, writes it after the customer's word, and says that the scope guard is now on and that the `.sdlc/` exclude line comes from `/sdlc:install-hooks`.
- `contract`: from `${CLAUDE_PLUGIN_ROOT}/templates/task-contract.md` it writes the contract to the tasks record and a copy to `.sdlc/active-contract.md`, then runs `--check-contract`. Refuses while an active contract exists. `/sdlc:contract close` removes the active file after the customer's word. `review`: read only. Runs `--check-worktree`, reads the diff and the project's test result, and reports files outside the contract and each acceptance line as met or not met. The customer decides; it approves nothing.
- `install-hooks`: `disable-model-invocation: true`. Runs `tools/install_git_hooks.py --target <project root>`, passes `--refresh` or `--uninstall` when named, and shows the installer's output unchanged. Script modes in `tools/scope_guard.py`, read before stdin and with no event line: `--check-contract` (exit 0, or 1 with the reason) and `--check-worktree` (compares `git status --porcelain -z` with `Files in`, `Files out` and the always-allowed list using the existing parser and matcher, skips `.sdlc/`, prints the paths outside, exit 0 or 1; no contract is exit 1). The hook path stays unchanged.
- Files in: `skills/{status,init,contract,review,install-hooks}/SKILL.md`, `templates/project.md` (record map, developer rules file, report language, `## Always allowed`), `tools/scope_guard.py`, `tests/test_skills.py`, `tests/test_scope_guard.py` (new cases only), `tests/fixtures/`, one `CHANGELOG.md` line.
- Files out: everything else, incl. `hooks/`, `agents/`, `.claude/`, `.claude-plugin/`, `tools/install_git_hooks.py`, `tools/pre_push_guard.py`, `templates/task-contract.md`, `DEV_RULES.md`, `PLAYBOOK.md`, `docs/`, `evidence/`, `EVIDENCE.md`. No `.sdlc/project.md` in this repository.
- Limits: at most 6 `claude -p` runs, each `--model haiku`, `--max-turns 8`, in a throwaway repository in the scratchpad, never Project A or Project B. Amended 2026-11-06 with the customer's word: 3 more runs, 9 in all, same flags, run by the TL: `status`, `install-hooks --uninstall`, `contract close`. No permission bypass flag, no `claude plugin install`, no change to user settings; `--allowedTools` may name the commands a skill runs. The first run settles whether `allowed-tools` in a plugin skill takes effect; the result goes in the report.
- Acceptance: in one throwaway repository, typed commands run in order: `init` writes the opt-in file; a write with no contract is denied; `contract` makes a write inside it pass and one outside it fail; `review` names a file changed through Bash outside the contract; `install-hooks` installs and `--uninstall` restores; `status` answers. Asking the model to run `init` or `install-hooks` is refused. On a clean copy strict validate holds no finding beyond DEC-044; `claude plugin details` lists 5 skills, token cost in the report. Guard exit 0 over the changed files.
- Tests: `tests/test_skills.py`: exactly the 5 folders; the flag on `init` and `install-hooks` and on no other; every plugin path named in a skill exists; no `$CLAUDE_PLUGIN_ROOT` form; the line limit; a filled `templates/project.md` gives the expected always-allowed list through the guard's parser. `tests/test_scope_guard.py`: one pass and one refuse for each mode (DEV_RULES 9), including the unfilled template as a broken contract, a rename, a path in `Files out`, and the hook path unchanged. `python -m pytest -q` green, summary line pasted.
- Design reference: `cto/2026-11-04_phase3-plan.md` D-35, D-36, D-39; DEC-037, DEC-038, DEC-041; `docs/toolchain.md` V-8, V-12.
- Flag: none. Removing `.sdlc/project.md` turns the guard off (DEC-039).
- Customer test: none here; the first use in the customer's terminal is P-33.
- Report to the TL in Turkish, fixed format; a result that contradicts a decision is an OPEN QUESTION. After: the TL updates `docs/toolchain.md`; `tech-writer` updates `PLAYBOOK.md` Appendix H with the commands and the target install; `scribe` writes LOG, STATUS and the metrics line.

### [x] T-33a [E] `--snapshot` refuses over an existing manifest (`developer`, Haiku)
- Result: refusal and `--replace-snapshot` in; 502 tests green, 1 skipped; `evidence/` and `EVIDENCE.md` unchanged. One question back: the contract missed `tests/metrics/test_cli_records.py`.
- Size: easy.
- Goal: a second `--snapshot` for a label cannot replace a pinned copy by accident, so T-33 cannot pull Project A into the v2 series (DEC-034). Refusal only: no rerun, no number changes.
- Rule: `snapshot()` in `tools/metrics/inputs.py` raises `InputError` when `<raw dir>/manifest.json` exists, before anything is written. The new flag `--replace-snapshot` allows it. The flag without `--snapshot` is refused. The refusal names the label and the flag and exits 2.
- Files in: `tools/metrics/inputs.py`, `tools/metrics/__main__.py`, `tests/metrics/test_cli.py`, `tests/metrics/test_cli_records.py` (added 2026-11-06 by the TL: the contract missed its 2 double-snapshot calls; DEV_RULES 1 leaves tests free), one `CHANGELOG.md` line.
- Files out: everything else, incl. `evidence/`, `EVIDENCE.md`, the other files in `tools/metrics/`, `tools/metrics/profiles/`. Do not run `--snapshot` on the real labels. Tests use their temp project only.
- Acceptance: a second snapshot for a label exits 2 and leaves the copy and its manifest byte-identical, even when the source changed; a first snapshot passes; `--replace-snapshot` replaces; the flag alone exits 2. A rerun without `--snapshot` works as before. `git status --porcelain evidence/ EVIDENCE.md` prints nothing. Guard exit 0 over the changed files.
- Tests: `tests/metrics/test_cli.py`: one refuse and one pass (DEV_RULES 9), the flag alone, a copy unchanged after a refusal. Existing tests that snapshot twice on one label pass `--replace-snapshot`; change nothing else in them. `python -m pytest -q` green, summary line pasted.
- Design reference: `cto/2026-11-04_phase3-plan.md` D-32; DEC-024, DEC-034.
- Flag: `--replace-snapshot`.
- Customer test: none.
- Report to the TL in Turkish, fixed format. After: `scribe` writes LOG, STATUS and the metrics line.

### [x] P-33 [M] Rehearsal in a throwaway clone (customer, in a terminal the customer opened; `scout`, Haiku, reads the result)
- Result: every step passed in the customer's terminal on 2026-11-07; 5 events, 1 allow, 4 deny, 4 of them from a sub-agent; rollback hash-equal. Totals in `docs/dogfood-1.md`. Finding: `init` and `contract` write through Bash, which the guard does not see.
- Size: medium.
- Goal: the whole loop runs once in a repository shaped like Project A, in the customer's own terminal, before anything touches Project A. It gives the live part of G3-3 and G3-4, the rollback part of G3-6 and the load, block and push part of G3-7 (DEC-033, DEC-043). No product code.
- Prepare: the TL writes the exact commands in `.sdlc/local/p33-runbook.md`. A fresh clone of this repository in a throwaway folder in the home directory, outside `AppData`. Origin removed, a local bare repository as the only remote. Records renamed. A non-English record line committed. An existing pre-push hook that writes a marker file. `.sdlc/guard-patterns.txt` removed before install (T-32 review). `git status` and the SHA-256 of the hook folder noted first.
- Session: `claude --plugin-dir <kit>` in the clone, model Sonnet, in this order: `/sdlc:status` before opt-in; `/sdlc:init` (the question before the write is seen, record map follows the renamed records); a write with no contract denied; `/sdlc:contract` with one file in and one out; a write by `sdlc:scribe` inside allowed, outside denied, with no contract denied after close; a file made through Bash named by `/sdlc:review`; `/sdlc:contract close` (the question before the delete is seen).
- Git and rollback: `/sdlc:install-hooks`, a second run says no change; a clean push passes and the marker shows the old hook ran; the non-English line passes; a planted fake key is rejected. `/sdlc:install-hooks --uninstall`, then rollback steps 4 and 5 of DEC-033 by hand: hook hash equal, `core.hooksPath` unset, `git status` equal to the noted state.
- Watch: record whether a denied main-session write outside the root blocked useful work (DEC-037 outcome), and every deny the customer thinks was wrong.
- Files in: `.sdlc/local/p33-runbook.md` and `.sdlc/local/p33-results.md` (ignored by git), `docs/dogfood-1.md` (new, TL: rehearsal totals in the fixed fields of DEC-034), `docs/toolchain.md`, `CLAUDE.md` (one Records row for `docs/dogfood-1.md`).
- Files out: everything else, incl. `skills/`, `tools/`, `hooks/`, `agents/`, `templates/`, `evidence/`, `EVIDENCE.md`. Project A and Project B are not touched or read. A fault found here goes to a new contract; no fix inside this task.
- Limits: stop at the first failed step and return it to the TL. No permission bypass flag, no `claude plugin install`, no change to user settings. `ANTHROPIC_API_KEY` removed in that window before `claude`. The clone is deleted only after the customer's word.
- Acceptance: every step above seen in the customer's terminal; the event lines in the clone's `.sdlc/metrics.jsonl` show allow and deny by state and agent, read by `scout` as totals with no path; CLI version and date recorded; guard exit 0 over `docs/dogfood-1.md`.
- Tests: no new test. `python -m pytest -q` stays green.
- Design reference: `cto/2026-11-04_phase3-plan.md` section 3, D-31 rollback, D-32; DEC-033, DEC-034, DEC-037, DEC-043.
- Flag: none.
- Customer test: the customer runs this task. Their statement that load, block and push worked in their terminal is the G3-7 evidence.
- After: `scribe` writes LOG, STATUS and the metrics line. T-33 starts only after this task passes (DEC-033), and the customer picks its task first.

### [x] T-30b [E] `init` and `contract` write through the file tools (`developer`, Haiku)
- Result: 2 skills and 3 tests changed; 505 tests green, 1 skipped; in 2 Sonnet runs all 3 files went through `Write` or `Edit`. The `close` step keeps its shell delete.
- Size: easy.
- Goal: the kit's own commands pass the scope guard's hook instead of writing through Bash, which P-33 found (DEC-038). Text only: no script changes.
- Rule: `skills/init/SKILL.md` lists `Write` in `allowed-tools`; `skills/contract/SKILL.md` lists `Write` and `Edit`. Each write step says to use that tool and never a shell command. The `close` step of `contract` keeps its shell delete, because no file tool deletes. The question before a write or delete stays.
- Files in: `skills/init/SKILL.md`, `skills/contract/SKILL.md`, `tests/test_skills.py`, one `CHANGELOG.md` line.
- Files out: everything else, incl. `skills/status/`, `skills/review/`, `skills/install-hooks/`, `tools/`, `templates/`, `docs/`, `PLAYBOOK.md`, `evidence/`, `EVIDENCE.md`.
- Limits: at most 2 `claude -p` runs, each `--model sonnet`, `--max-turns 8`, in a throwaway repository in the scratchpad, never Project A or Project B. No permission bypass flag, no `claude plugin install`, no change to user settings.
- Acceptance: the run log shows `Write` for `.sdlc/project.md`, `Write` for `.sdlc/active-contract.md`, `Write` or `Edit` for the tasks record, and no Bash command writing any of them. `check-contract` still reports the contract. Guard exit 0 over the changed files.
- Tests: `tests/test_skills.py`: `init` and `contract` name the tools; the 2 read-only skills still name none; neither skill text holds a heredoc or a redirect. `python -m pytest -q` green, summary line pasted.
- Design reference: `docs/dogfood-1.md` limits; DEC-038, DEC-041.
- Flag: none.
- Customer test: none; T-33 is the next real use.
- Report to the TL in Turkish, fixed format, with the tool name of each write in the live run. After: the TL updates `docs/toolchain.md`; `scribe` writes LOG, STATUS and the metrics line.

### [x] T-33b [M] Developer rules file outside the always-allowed list (`developer`, Sonnet)
- Result: 4 files and 1 CHANGELOG line; 10 new tests, 515 green, 1 skipped; a hand run denied a sub-agent write to the rules file in the always-allowed list and allowed the main session. A broad glob in `Files in` that matches the file counts as naming it. `PLAYBOOK.md` Appendix H updated by `tech-writer`.
- Size: medium.
- Goal: a sub-agent cannot change the rules it works under unless the contract names the file. In T-33 the `init` brief put that file in the always-allowed list (DEC-045).
- Rule: `tools/scope_guard.py` reads the backticked path on the `Developer rules:` line of `.sdlc/project.md`. A sub-agent write to that path is denied unless the active contract's `Files in` names it; the always-allowed list does not cover it, in any state. `Files out` still wins. The main session is not affected. No `Developer rules:` line: no change in behaviour. `--check-worktree` is not changed. `skills/init/SKILL.md` step 3 says the developer rules file never goes in the always-allowed list, even when the arguments name it, and says so to the customer.
- Files in: `tools/scope_guard.py`, `tests/test_scope_guard.py`, `skills/init/SKILL.md`, `tests/test_skills.py`, one `CHANGELOG.md` line.
- Files out: everything else, incl. `hooks/`, `templates/`, `agents/`, `.claude/`, `docs/`, `PLAYBOOK.md`, `evidence/`, `EVIDENCE.md`.
- Acceptance: with the file in the always-allowed list, a sub-agent write to it is denied in the no-contract and active states with a reason that names the developer rules; the main session is allowed; a contract whose `Files in` names it allows the sub-agent. Existing tests unchanged and green. Guard exit 0 over the changed files.
- Tests: new cases in `tests/test_scope_guard.py` for each acceptance line, incl. a case-folded path on Windows; `tests/test_skills.py` checks the `init` sentence. `python -m pytest -q` green, summary line pasted.
- Design reference: `docs/dogfood-1.md` finding 4; DEC-037, DEC-045.
- Flag: none. Customer test: none; next real use is a later project.
- Report to the TL in Turkish, fixed format. No live `claude -p` run. After: `scribe` writes LOG, STATUS and the metrics line.

### [x] T-34a [E] Line endings and rules pointer (`developer`, Sonnet)
- Result: 2 lines in `.gitattributes`, `DEV_RULES.md` line 1, 1 CHANGELOG line; renormalize staged no line-ending change. Fresh clone with `core.autocrlf` true: the 6 files `w/lf`, 515 passed, 1 skipped; this folder the same.
- Size: easy.
- Goal: `python -m pytest -q` is green in a fresh Windows clone (G3 finding C-1), and `DEV_RULES.md` names the role source (D-3).
- Rule: `.gitattributes` adds `*.md text eol=lf` and `*.txt text eol=lf`; nothing else changes there. Run `git add --renormalize .` and report what it staged. `DEV_RULES.md` line 1: "`.claude/agents/*.md`" becomes "`agents/*.md` (copied to `.claude/agents/`)"; no other line.
- Files in: `.gitattributes`, `DEV_RULES.md`, files that `--renormalize` stages (expected: none, the index is LF), one `CHANGELOG.md` line.
- Files out: everything else, incl. `tests/`, `tools/`, `skills/`, `templates/`, `evidence/`, `EVIDENCE.md`.
- Acceptance: in a fresh `git clone` of a scratch commit of this tree, in the scratchpad, `git ls-files --eol` shows `w/lf` for the 5 `SKILL.md` files and `templates/guard-patterns.txt`, and `python -m pytest -q` is green; the same in this folder. Guard exit 0 over the changed files.
- Tests: none new; the 6 LF tests named in C-1 are the check. Summary lines of both runs pasted.
- Design reference: `audits/2026-11-07_gate3.md` C-1, D-3.
- Flag: none. Customer test: none.
- Report to the TL in Turkish, fixed format. No commit in this folder. After: `scribe` writes LOG and STATUS; `auditor-mini` re-verifies.

## Phase 4

Plan: `cto/2026-11-07_phase4-plan.md`. Order: T-39, T-39a, T-40, T-41, T-42, T-44, T-46a and T-46b, G0 leftover, T-45. T-40 waits for the customer's answers on server writes and SDK install.

- [x] T-39 [M] scope guard: memory folder for the main session, exact path for the rules file. DEC-046, DEC-048.

### [x] T-39 [M] Memory folder and exact rules path (`developer`, Sonnet, effort medium)
- Result: 5 files and 1 CHANGELOG line, 25 new test cases, 536 passed, 1 skipped; review rounds 1. TL hand run on 5 hook inputs: memory write by the main session allowed, by a sub-agent denied, `..` out of it denied; rules file with `**` denied, with the exact path allowed. `PLAYBOOK.md` Appendix H updated by `tech-writer`. Live `transcript_path` layout checked at T-39a.
- Goal: the main session may keep notes in the CLI's per-project memory folder (DEC-046); a sub-agent changes the developer rules file only when `Files in` holds its exact path (DEC-048).
- Rule 1: memory folder = the folder `memory` next to the hook input's `transcript_path` file, only when that file's parent folder sits in a folder named `projects`. A main-session write under it (after `..` is resolved, case-folded on Windows) is allowed with its own reason. Sub-agent, no `transcript_path`, or another layout: unchanged deny. Never read from `.sdlc/project.md`. The event line records the path as `<memory>/<relative>`, never the absolute path.
- Rule 2: the rules-file exception counts only a `Files in` token, before brace expansion, with no `*`, `?` or `{`, equal to the rules path after normalisation (case-folded on Windows). A glob such as `**` or `*.md` no longer counts. Main session unchanged.
- Keep: `check`, `decide`, `Contract` stay importable with old call forms working (new parameters optional); `--check-worktree` unchanged; standard library only.
- Files in: `tools/scope_guard.py`, `tests/test_scope_guard.py`, `skills/init/SKILL.md`, `tests/test_skills.py`, one `CHANGELOG.md` line.
- Files out: everything else, incl. `hooks/`, `templates/`, `agents/`, `.claude/`, `docs/`, `PLAYBOOK.md`, `tests/fixtures/` existing files.
- Acceptance: main session memory write allowed; sub-agent memory write denied; `..` escape from the memory folder denied; missing or wrong-layout `transcript_path` denied; event line holds no absolute path; rules file with exact token allowed, with `**`, `*.md` or `{a,b}` token denied for a sub-agent. Existing tests green.
- Tests: one case per acceptance line, incl. a case-folded Windows path; `test_skills.py` checks "exact path" in `init`. `python -m pytest -q` summary pasted.
- After: `tech-writer` updates `PLAYBOOK.md` Appendix H (two sentences); `scribe` writes LOG, STATUS, metrics line. Report in Turkish, fixed format, no commit.

## Later phases (headlines; contracts are written when the phase opens)
- Phase 4: T-39 scope guard: memory folder for the main session (DEC-046) and exact path for the rules file (DEC-048) · T-39a the kit opts in to its own guard (DEC-047) · T-40 server skeleton · T-41 `scope_check` and metrics tools · T-42 decision, lesson, gate and log tools, `.mcp.json` in the plugin · T-44 security pass, incl. the C-26 public endpoint checklist if the kit has a public endpoint by then · T-46 eval with and without the server (DEC-012), plus the G0 leftover: an isolated session in a clean clone without the local instruction file resumes from the records · T-45 gate G4. T-43 dropped (DEC-011).
- Phase 5: T-50 README · T-51 v0.1.0 and marketplace, with the T-33 findings routed by DEC-045 (`docs/dogfood-1.md`): 3 the kit introduces itself to a session, 6 contract fields and placement in another project's tasks file, 7 a tools section in `.sdlc/project.md` and a narrow allow list, 9 a plan budget · T-52 gate G5, incl. G2 candidate N-5: engine-specific test attribute and folder layout in the profiles and in the git history; the maintainer decides before the repository goes public.

## Not on the list
Ideas that come up go here first and are not worked on until the maintainer moves them into a phase.
- (none yet)
