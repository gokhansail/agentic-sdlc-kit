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

### Changed

- Session instructions (`CLAUDE.md`): the end-of-reply status line fields are defined.
