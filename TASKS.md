# Tasks

Written by the Technical Lead. Each task is a contract of at most 15 lines: goal, files to touch and not to touch, acceptance, tests, tag. Tags: [E] easy (one file, no behaviour change), [M] medium, [H] hard. A phase gate that is still `[ ]` blocks the next phase. Decisions are in `DECISIONS.md`.

## NOW NEXT
Phase 2: T-21 done and committed; next is the T-22 contract. Plan: `cto/2026-11-02_phase2-plan.md`, DEC-021 to DEC-028.

## Phases

| Phase | Goal | Gate | Verdict by |
|---|---|---|---|
| 0 Setup | decisions, records, guard, toolchain | G0: decisions recorded; guard rejects a planted secret (test); toolchain doc has no "not verified" line for phases 1-3; product `CLAUDE.md` committed (T-05) | TL list + maintainer |
| 1 Playbook | the method in tool-neutral English, no code | G1: every claim maps to a source-map line; no private data; maintainer read it once end to end | `auditor`, then `auditor-mini` |
| 2 Evidence | before/after numbers, reproducible | G2 (DEC-026): rerun from a clean checkout matches the manifest hashes and leaves `evidence/` and `EVIDENCE.md` unchanged; 3 hand counts (H1, H2, H3) match exactly; limits section of at least 9 items; tests green, a known-answer test per metric; guard clean and `evidence/*.json` holds only fixed keys, numbers, dates, hashes and labels; unparsed metric lines 0 or stated in the limits | `auditor-mini` |
| 3 Plugin | Claude Code plugin: roles, commands, hooks | G3: loads with `--plugin-dir`; scope guard blocks and allows (tests); one real task done with it on Project A | `auditor`, then `auditor-mini` |
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
### [ ] T-22 [M] Run on the three sources (`scout`, runs only; totals to `evidence/*.json`)
### [ ] T-23 [M] `EVIDENCE.md` prose and limits (`tech-writer`)
### [ ] T-24 Gate G2 (`auditor-mini`)

## Later phases (headlines; contracts are written when the phase opens)
- Phase 3: T-30 plugin skeleton and commands · T-31 scope guard hook · T-32 git hook installer command · T-33 dogfood on Project A · T-34 gate G3.
- Phase 4: T-40 server skeleton · T-41 `scope_check` and metrics tools · T-42 decision, lesson, gate and log tools, `.mcp.json` in the plugin · T-44 security pass, incl. the C-26 public endpoint checklist if the kit has a public endpoint by then · T-46 eval with and without the server (DEC-012), plus the G0 leftover: an isolated session in a clean clone without the local instruction file resumes from the records · T-45 gate G4. T-43 dropped (DEC-011).
- Phase 5: T-50 README · T-51 v0.1.0 and marketplace · T-52 gate G5.

## Not on the list
Ideas that come up go here first and are not worked on until the maintainer moves them into a phase.
- (none yet)
