# Status

What is this file? The current state of agentic-sdlc-kit on one page. A new session reads this first and resumes from here.

Last updated: 2026-10-29
Now: Phase 0 · T-05 next · repository private · guard code written, tests green

## Phase

Phase 0 Setup. Gate G0 is open. Decisions are recorded, the pre-push guard is installed, the toolchain is checked. The product `CLAUDE.md` (T-05) is not done, so G0 cannot close yet.

## Done

- T-01 Decisions: DEC-001 to DEC-012 in `DECISIONS.md`. DEC-011 drops the second-client test. DEC-012 adds an evaluation with and without the MCP server to phase 4 (T-46).
- T-02 Record skeleton (0.0.1): `TASKS.md`, `STATUS.md`, `LOG.md`, `CHANGELOG.md`, `LESSONS.md`, `LICENSE`.
- T-03 Pre-push guard (0.0.1): `hooks/git/pre-push`, `tools/pre_push_guard.py`, `tools/install_git_hooks.py`, `.sdlc/guard-patterns.txt`, `.gitattributes`. 31 tests green, including a real push to a local bare repository. Installed in this repository (`core.hooksPath = hooks/git`); a local private pattern list is in place and ignored by git.

- T-04 Toolchain check: `docs/toolchain.md`, `requirements-dev.txt`. MCP SDK 2.3.0 and 1.30.0 both pass a smoke test on Python 3.10; 2.x chosen (DEC-013). Private session instructions go to `CLAUDE.local.md` (DEC-014). Committed and pushed.

## In progress

- None.

## Next

- T-05 Product `CLAUDE.md`. English, at most 80 lines, committed; private session instructions move to `CLAUDE.local.md`. Required for G0.
- G0 gate check, then phase 1.

## Repository

- Private (DEC-007). Only the maintainer changes visibility.
- Every push goes through the pre-push guard. Do not use `--no-verify`.
- Running the tests: `python -m pip install -r requirements-dev.txt`, then `python -m pytest -q`.
- Language: English for everything in the repository (DEC-003).

## Open questions

- None.
