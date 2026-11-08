# Project file

What is this file? The opt-in and the one config file of the sdlc plugin for this project (`.sdlc/project.md`). While it exists, the scope guard runs: a write needs an active contract or a path in the always-allowed list. Delete the file to turn the guard off. `/sdlc:init` fills the angle-bracket parts and writes it after the customer's word.

## Records
- Status: `STATUS.md`
- Tasks: `TASKS.md`
- Log: `LOG.md`
- Decisions: `DECISIONS.md`
- Changelog: `CHANGELOG.md`
- Developer rules: `DEV_RULES.md`
- Report language: the language the maintainer writes in

## Always allowed
Paths any writer may change without a contract line. Only backticked globs count; a trailing slash means a folder. A contract's Files out line still wins.
- Records: `STATUS.md`, `TASKS.md`, `LOG.md`, `DECISIONS.md`, `CHANGELOG.md`, `LESSONS.md`
- Reports: `audits/`, `cto/`
- Documents: `docs/`

Sources: [DEC-037, DEC-041, DEC-047, DEC-049]
