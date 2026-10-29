# Status

What is this file? The current state of agentic-sdlc-kit on one page. A new session reads this first and resumes from here.

Last updated: 2026-10-29
Now: Phase 0 · T-03 next · repository private · no code yet

## Phase

Phase 0 Setup. Gate G0 is open. Decisions are recorded. The pre-push guard (T-03) and the toolchain check (T-04) are not done, so G0 cannot close yet.

## Done

- T-01 Decisions: DEC-001 to DEC-012 in `DECISIONS.md`. DEC-011 drops the second-client test. DEC-012 adds an evaluation with and without the MCP server to phase 4 (T-46).

- T-02 Record skeleton (0.0.1): `TASKS.md`, `STATUS.md`, `LOG.md`, `CHANGELOG.md`, `LESSONS.md`, `LICENSE`. Approved and committed locally, not pushed.

## In progress

- None.

## Next

- T-03 Pre-push guard (0.0.1). Rejects secrets and private content in pushed commits. No push until it is installed and tested.
- T-04 Toolchain check. Confirms the tools and versions used in phases 1 to 4, including the minimum `mcp` SDK for Python 3.10 (DEC-004).

## Repository

- Private (DEC-007). Only the maintainer changes visibility.
- Pushed up to the tag rename commit (2026-10-29). The maintainer chose to push before T-03; the outgoing commits were scanned by hand first (LOG 2026-10-29 (2)).
- Until the T-03 guard is installed, every push is preceded by the same manual scan.
- Language: English for everything in the repository (DEC-003).

## Open questions

- None.
