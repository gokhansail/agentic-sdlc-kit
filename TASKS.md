# Tasks

Written by the Technical Lead. Each task is a contract of at most 15 lines: goal, files to touch and not to touch, acceptance, tests, tag. Tags: [K] easy (one file, no behaviour change), [O] medium, [Z] hard. A phase gate that is still `[ ]` blocks the next phase. Decisions are in `DECISIONS.md`.

## NOW NEXT
T-03 Pre-push guard. No push until it is installed and tested.

## Phases

| Phase | Goal | Gate | Verdict by |
|---|---|---|---|
| 0 Setup | decisions, records, guard, toolchain | G0: decisions recorded; guard rejects a planted secret (test); toolchain doc has no "not verified" line for phases 1-3 | TL list + maintainer |
| 1 Playbook | the method in tool-neutral English, no code | G1: every claim maps to a source-map line; no private data; maintainer read it once end to end | `auditor`, then `auditor-mini` |
| 2 Evidence | before/after numbers, reproducible | G2: scripts reproduce the numbers; 3 numbers recounted by hand; limits section | `auditor-mini` |
| 3 Plugin | Claude Code plugin: roles, commands, hooks | G3: loads with `--plugin-dir`; scope guard blocks and allows (tests); one real task done with it on Project A | `auditor`, then `auditor-mini` |
| 4 MCP server | file-based core | G4: tests green; root lock and `..` tests pass; no network; works in Claude Code (DEC-011); eval table from T-46 | `auditor`, then `auditor-mini` |
| 5 Release | README, v0.1.0, marketplace, public | G5: publish-readiness audit incl. git history; every README number reproducible; maintainer says publish | `auditor` |
| 6 Ongoing | dogfood and measurement | none | none |

## Phase 0

### [x] T-01 [K] Decisions
- Goal: settle D-1 to D-11. Result: DEC-001 to DEC-012 in `DECISIONS.md`.

### [x] T-02 [K] Record skeleton (0.0.1)
- Goal: set up the committed record layer (DEC-003).
- Touch: `TASKS.md` (TL), `STATUS.md` (at most 60 lines), `LOG.md`, `CHANGELOG.md` (Unreleased), `LESSONS.md` (empty skeleton), `LICENSE` (MIT, `gokhansail`). Do not touch: `.claude/agents/*`, `DEV_RULES.md`, `README.md`, private files.
- Acceptance: all English, no conversation, no names other than `gokhansail`; `STATUS.md` answers "where are we" on its own; local commit after maintainer approval; no push before T-03.
- Tests: none. Written by TL and `scribe`.

### [ ] T-03 [O] Pre-push guard (0.0.1)
- Goal: stop secrets and private content from reaching the remote.
- Touch: `hooks/git/pre-push`, `tools/install_git_hooks.py`, `.sdlc/guard-patterns.txt` (committed, generic), support for `.sdlc/local/private-patterns.txt` (ignored, names and private terms), `tests/test_pre_push.py`. Do not touch: documents.
- Checks the added lines and commit messages of the commits being pushed: key patterns (`AKIA`, `sk-`, `ghp_`, `xox`), `.env`, private files (plan, private rules), `evidence/raw/`, email addresses other than GitHub noreply, absolute user paths, document and script service URLs, debug flags left on, and non-English letters in English-only files.
- Acceptance: a planted secret is rejected with file, line and pattern; a clean commit passes; a pattern from the local file is caught without that pattern ever being committed; the installer is idempotent.
- Tests: reject, pass, local-pattern, installer re-run. Tag [O], `developer` (Sonnet).

### [ ] T-04 [O] Toolchain check
- Goal: confirm every tool and version used in phases 1-4. No guesses.
- Touch: `docs/toolchain.md`.
- Acceptance: Python 3.10 vs minimum `mcp` SDK version confirmed; Claude Code plugin docs read (`hooks/hooks.json`, `.mcp.json`, `--plugin-dir`, `claude plugin eval`, headless `claude -p` with an MCP config for T-46); each line has a source link and a date.
- Tests: none. `scout` reads, `developer` tries the install, TL writes.

## Later phases (headlines; contracts are written when the phase opens)
- Phase 1: T-10 source map · T-11 `PLAYBOOK.md` · T-12 templates · T-13 role files and `docs/portability.md` (concept mapping only) · T-14 gate G1.
- Phase 2: T-20 metric scripts with synthetic fixtures · T-21 run on both source projects, totals only · T-22 gate G2.
- Phase 3: T-30 plugin skeleton and commands · T-31 scope guard hook · T-32 git hook installer command · T-33 dogfood on Project A · T-34 gate G3.
- Phase 4: T-40 server skeleton · T-41 `scope_check` and metrics tools · T-42 decision, lesson, gate and log tools, `.mcp.json` in the plugin · T-44 security pass · T-46 eval with and without the server (DEC-012) · T-45 gate G4. T-43 dropped (DEC-011).
- Phase 5: T-50 README · T-51 v0.1.0 and marketplace · T-52 gate G5.

## Not on the list
Ideas that come up go here first and are not worked on until the maintainer moves them into a phase.
- (none yet)
