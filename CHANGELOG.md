# Changelog

What is this file? The user-visible changes per version, in Keep a Changelog style. Versions follow 0.0.x until the first release (0.1.0).

## [Unreleased]

### Added

- Eval runner (`tools/eval_run.py`, T-46d): a timeout or Ctrl+C ends the CLI and every process it started, `--resume` is refused when the manifest is missing or a setting or the content of the files a run depends on differs (a commit of other files does not block it), the totals record the runner hash and git state (schema 2), and `--seed` orders the two conditions half and half.
- Eval runner fix (`tools/eval_run.py`, T-46c): a run with an error is never scored correct, and every call is budgeted at the per-run cap.
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
- Own scope guard (`.sdlc/project.md`, `.claude/settings.json`): sessions in this repository, desktop app included, run the scope guard from the project settings (DEC-047, DEC-049).
- Dogfood note (`docs/dogfood-1.md`): totals of the rehearsal in a throwaway clone and of one real task on Project A, with 9 findings for triage.
- MCP server skeleton (`server/`, `tools/records.py`, `mcpServers` in `.claude-plugin/plugin.json`): the plugin starts a read-only stdio server with one `status` tool (guard state, active task, Files in and out, record names from `.sdlc/project.md`); the root is fixed at start, a root-lock helper checks path arguments, and a missing or out-of-range `mcp` package stops it with one install line. Needs `python -m pip install "mcp>=2.3,<3"`.
- Eval set (`eval/`, `tests/test_eval.py`, DEC-012): a synthetic invoicing repository, 30 questions with an answer key (frozen SHA-256 in `eval/README.md`) and a scorer (`python eval/score.py answers.jsonl`); written before the server tools exist, no model call.
- Record tools (`tools/lookup.py`, `server/main.py`): the read-only server gains `decisions`, `lessons`, `findings`, `tasks` and `log`, one stdlib reader each (`python tools/lookup.py --root <folder> <record>` prints the same answer as JSON). The record map gains `lessons` and `audits` (`templates/project.md`, `tools/records.py`). An entry a reader cannot parse is counted in the answer, and a map entry outside the project root gives an error answer.
- Scope and event tools (`server/scope.py`, `server/events.py`, `tools/events.py`): the read-only server gains `scope_check` (allow or deny for up to 50 paths, from the guard's own function), `contract`, `changed_outside` and `guard_events` (allow and deny totals per task, tool and agent from `.sdlc/metrics.jsonl`; `python tools/events.py --root <folder>` prints the same totals).
- Server security pass (`docs/security.md`, `server/inputs.py`, `tools/records.py`, `tools/lookup.py`, `tools/events.py`, `tools/scope_guard.py` `_git` only): 17 findings (3 High, 9 Medium, 5 Low; 13 fixed, 2 accepted, 2 Medium open in the guard); the server refuses control files that are links out of the root, too large or hostile to the guard's heading pattern, runs git with `core.fsmonitor` off and no optional locks and refuses a repository config with a filter; record files over 2 MB, an audits folder over 200 entries and answers over 150,000 characters are cut or refused; every tool description starts with "Read only".
- Eval runner (`tools/eval_run.py`, `docs/eval-runbook.md`, `tests/test_eval_run.py`, T-46b, DEC-054): asks the 30 eval questions through `claude -p` on the subscription login (API key removed from the child environment, `Read` tool only) in a fresh copy of `eval/repo/` outside the kit, on 2 models, with and without the server, with a total budget in estimated USD that stops the run before a call that could pass it; raw output stays outside the repository and `eval/results/<label>.json` holds totals only. Tests use a fake `claude`, no model call.

### Changed

- Line endings (`.gitattributes`, `DEV_RULES.md`): `*.md` and `*.txt` are checked out with LF, so the LF tests pass in a Windows clone; `DEV_RULES.md` names `agents/` as the role source.
- Scope guard (`tools/scope_guard.py`, `skills/init/SKILL.md`): the developer rules file named in `.sdlc/project.md` is never covered by the always-allowed list; a sub-agent may write it only when the active contract's Files in names it.
- Session instructions (`CLAUDE.md`): the end-of-reply status line fields are defined.
- Role files and developer rules (`.claude/agents/`, `DEV_RULES.md`): private details removed, each rule traced to the source map.
- Playbook, source map, scout and writer roles, audit template and session instructions: fixes from the G1 audit.
- Metrics profiles (`tools/metrics/profile.py`, `metrics_text.py`): M5 and M6 accept an ordered `task_lines` list; the Project A profile counts metric lines in the middle of a bullet and in a lead review line (DEC-030).
- Metrics snapshot (`tools/metrics/inputs.py`, `python -m tools.metrics --snapshot`): a second `--snapshot` for a label that already has a manifest exits 2 before anything is written, unless `--replace-snapshot` is given; `--replace-snapshot` without `--snapshot` exits 2.
- Scope guard (`tools/scope_guard.py`, `skills/init/SKILL.md`): the main session may write in the CLI's per-project memory folder (found from `transcript_path`); a sub-agent may change the developer rules file only when Files in names its exact path, no glob (DEC-046, DEC-048).
- Plugin commands `init` and `contract` write their files with the Write and Edit tools instead of a shell heredoc, so the scope guard sees the writes.
- Developer rules and role (`DEV_RULES.md`, `agents/developer.md`, `.claude/agents/developer.md`): files are written with the file tools only; no git command that changes state (DEC-052).
- Scope guard match in bounded time (`tools/scope_guard.py`, `server/inputs.py`, `docs/security.md`, T-44a): the heading parse is one pass over the line and `matches` moves a bit set over the path instead of a backtracking regex (same answers as `glob_to_regex` on 6,000 generated pairs); the 2,000-blank heading took 13 s and 9 `**/` against 30 segments took 4.6 s, both now under 1 ms; the server no longer refuses a long blank run; S-6, S-7 and S-8 are FIXED.
