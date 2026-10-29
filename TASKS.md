# Tasks

Written by the Technical Lead. Each task is a contract of at most 15 lines: goal, files to touch and not to touch, acceptance, tests, tag. Tags: [E] easy (one file, no behaviour change), [M] medium, [H] hard. A phase gate that is still `[ ]` blocks the next phase. Decisions are in `DECISIONS.md`.

## NOW NEXT
Phase 1: T-11 `PLAYBOOK.md` in progress (contract below). Then T-12 templates.

## Phases

| Phase | Goal | Gate | Verdict by |
|---|---|---|---|
| 0 Setup | decisions, records, guard, toolchain | G0: decisions recorded; guard rejects a planted secret (test); toolchain doc has no "not verified" line for phases 1-3; product `CLAUDE.md` committed (T-05) | TL list + maintainer |
| 1 Playbook | the method in tool-neutral English, no code | G1: every claim maps to a source-map line; no private data; maintainer read it once end to end | `auditor`, then `auditor-mini` |
| 2 Evidence | before/after numbers, reproducible | G2: scripts reproduce the numbers; 3 numbers recounted by hand; limits section | `auditor-mini` |
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

### [ ] T-11 [H] PLAYBOOK.md
- Goal: `PLAYBOOK.md` states the method in tool-neutral English: a core of at most one page, then appendices. Every claim traces to a row of `docs/source-map.md`.
- Writer: `tech-writer` (Sonnet, effort high), two rounds at most. Reads `docs/source-map.md`, `CLAUDE.md`, `DECISIONS.md`; never the private sources.
- Touch: `PLAYBOOK.md` (new), `CHANGELOG.md` (one line). Do not touch: the source map, templates, role files, other records.
- Core: what the method is and is not, roles, task loop, phase loop and gates, records. Appendices: roles and authority matrix; 8-step task loop; phase loop and gate; flexibility and impact note; flag rule; per-task metrics; decision and lesson records with the six lessons as short anonymous examples; concept versus mechanics; why it is not specific to Claude Code.
- Traceability: each paragraph, list item or table row carries its concept IDs in brackets, e.g. [C-06]. No claim without an ID. No measured numbers (phase 2).
- Acceptance: core at most about 500 words; every cited ID exists in the map; no private names or paths; tool names only in the last two appendices; guard clean; writing-style list holds; maintainer reads it once end to end (may follow later, needed for G1).
- Tests: guard over the file; `python -m pytest -q` stays green; TL counts cited IDs against the map with a one-off script.

## Later phases (headlines; contracts are written when the phase opens)
- Phase 1: T-12 templates · T-13 role files and `docs/portability.md` (concept mapping only) · T-14 gate G1. G1 agenda item (DEC-017): all six process lessons are in the map and may appear in the playbook; the auditor reports any privacy, length or relevance problem with them as a finding.
- Phase 2: T-20 metric scripts with synthetic fixtures (the source records use non-English marker words; keep them out of committed code as literals, use unicode escapes or the local pattern file, since the guard rejects those letters) · T-21 run on both source projects, totals only · T-22 gate G2.
- Phase 3: T-30 plugin skeleton and commands · T-31 scope guard hook · T-32 git hook installer command · T-33 dogfood on Project A · T-34 gate G3.
- Phase 4: T-40 server skeleton · T-41 `scope_check` and metrics tools · T-42 decision, lesson, gate and log tools, `.mcp.json` in the plugin · T-44 security pass · T-46 eval with and without the server (DEC-012), plus the G0 leftover: an isolated session in a clean clone without the local instruction file resumes from the records · T-45 gate G4. T-43 dropped (DEC-011).
- Phase 5: T-50 README · T-51 v0.1.0 and marketplace · T-52 gate G5.

## Not on the list
Ideas that come up go here first and are not worked on until the maintainer moves them into a phase.
- (none yet)
