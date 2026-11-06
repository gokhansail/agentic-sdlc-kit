# Changelog

What is this file? The user-visible changes per version, in Keep a Changelog style. Versions follow 0.0.x until the first release (0.1.0).

## [Unreleased]

### Added

- Decision record (`DECISIONS.md`): DEC-001 to DEC-012.
- Task list (`TASKS.md`) with phases and gates.
- Status page (`STATUS.md`) for resuming work.
- Build log (`LOG.md`).
- Lessons skeleton (`LESSONS.md`), no entries yet.
- MIT license (`LICENSE`).
- Pre-push guard (`hooks/git/pre-push`, `tools/pre_push_guard.py`, `tools/install_git_hooks.py`, `.sdlc/guard-patterns.txt`): rejects secrets, private files and private terms in outgoing commits.
- Toolchain notes (`docs/toolchain.md`) and development requirements (`requirements-dev.txt`).
- Session instructions (`CLAUDE.md`): how a session in this repository runs the work.
- Templates (`templates/`): task contract, decision record, lesson entry, audit report, re-verify table, push checklist, developer rules.
- Source map (`docs/source-map.md`): the concepts the playbook may use, each traced to a source section.
- Playbook (`PLAYBOOK.md`): the method in tool-neutral English, every claim traced to the source map.
- Phase 2 plan (`cto/2026-11-02_phase2-plan.md`) and decisions DEC-021 to DEC-027: metric set, input pinning and gate G2 checks.
- Phase 3 plan (`cto/2026-11-04_phase3-plan.md`) and decisions DEC-033 to DEC-043: where the real task runs, scope guard design, commands and gate G3 criteria.
- Plugin facts measured with a throwaway plugin (`docs/toolchain.md`): role frontmatter, hook input and exit codes, skill text, load in a terminal.
- Metrics core (`tools/metrics/`, `python -m tools.metrics`): snapshot with SHA-256 manifest, source profiles, text metrics M1, M2, M5, M6 as deterministic JSON.
- Git, audit, decision and task metrics M3, M8, M9, M12, M13 with folder snapshots and git extracts (`tools/metrics/gitstats.py`, `metrics_records.py`), and the table render into a marked block (`python -m tools.metrics.render`).
- Evidence report (`EVIDENCE.md`): sources and periods, counting rules, result tables, how to read them, limits and rerun commands.
- Plugin skeleton (`.claude-plugin/plugin.json`, `agents/`): the repository root loads as plugin `sdlc` with 7 agents; `.claude/agents/` is a copy checked by `tests/test_role_sync.py`; role files name the default record names and read `.sdlc/project.md` when it exists.
- Scope guard (`hooks/hooks.json`, `hooks/scope/launcher.sh`, `tools/scope_guard.py`): in a project with `.sdlc/project.md`, each `Write`, `Edit` and `NotebookEdit` call is allowed or denied by `.sdlc/active-contract.md`; one event line per decision goes to `.sdlc/metrics.jsonl`. It catches a mistake and is not a security boundary.
- Git hook installer, target mode (`python tools/install_git_hooks.py --target <repo>`, `templates/guard-patterns.txt`): puts the pre-push guard into another repository without `core.hooksPath`, runs the repository's own pre-push hook first, reports a stale copy (`--refresh`) and restores the hook folder byte for byte (`--uninstall`); pattern files accept `forbid-path` lines.
- Plugin commands (`skills/{status,init,contract,review,install-hooks}/SKILL.md`, `templates/project.md`, `python tools/scope_guard.py --check-contract` and `--check-worktree`): `/sdlc:init` opts a project in, `/sdlc:contract` writes the active contract, `/sdlc:review` lists changed files outside it, `/sdlc:install-hooks` installs the pre-push guard in the project; `init` and `install-hooks` run only when typed.

### Changed

- Session instructions (`CLAUDE.md`): the end-of-reply status line fields are defined.
- Role files and developer rules (`.claude/agents/`, `DEV_RULES.md`): private details removed, each rule traced to the source map.
- Playbook, source map, scout and writer roles, audit template and session instructions: fixes from the G1 audit.
- Metrics profiles (`tools/metrics/profile.py`, `metrics_text.py`): M5 and M6 accept an ordered `task_lines` list; the Project A profile counts metric lines in the middle of a bullet and in a lead review line (DEC-030).
- Metrics snapshot (`tools/metrics/inputs.py`, `python -m tools.metrics --snapshot`): a second `--snapshot` for a label that already has a manifest exits 2 before anything is written, unless `--replace-snapshot` is given; `--replace-snapshot` without `--snapshot` exits 2.
- Plugin commands `init` and `contract` write their files with the Write and Edit tools instead of a shell heredoc, so the scope guard sees the writes.
