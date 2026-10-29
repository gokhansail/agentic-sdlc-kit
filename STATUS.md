# Status

What is this file? The current state of agentic-sdlc-kit on one page. A new session reads this first and resumes from here.

Last updated: 2026-10-29
Now: Phase 0 · T-04 next · repository private · guard code written, tests green

## Phase

Phase 0 Setup. Gate G0 is open. Decisions are recorded and the pre-push guard is installed. The toolchain check (T-04) is not done, so G0 cannot close yet.

## Done

- T-01 Decisions: DEC-001 to DEC-012 in `DECISIONS.md`. DEC-011 drops the second-client test. DEC-012 adds an evaluation with and without the MCP server to phase 4 (T-46).
- T-02 Record skeleton (0.0.1): `TASKS.md`, `STATUS.md`, `LOG.md`, `CHANGELOG.md`, `LESSONS.md`, `LICENSE`.
- T-03 Pre-push guard (0.0.1): `hooks/git/pre-push`, `tools/pre_push_guard.py`, `tools/install_git_hooks.py`, `.sdlc/guard-patterns.txt`, `.gitattributes`. 31 tests green, including a real push to a local bare repository. Installed in this repository (`core.hooksPath = hooks/git`); a local private pattern list is in place and ignored by git.

## In progress

- None.

## Next

- T-04 Toolchain check. Confirms the tools and versions used in phases 1 to 4, including the minimum `mcp` SDK for Python 3.10 (DEC-004). Adds `requirements-dev.txt` for pytest.

## Repository

- Private (DEC-007). Only the maintainer changes visibility.
- Every push goes through the pre-push guard. Do not use `--no-verify`.
- Running the tests needs pytest (`python -m pytest -q`); it is installed on this machine but not yet declared in the repository (T-04).
- Language: English for everything in the repository (DEC-003).

## Open questions

- None.
