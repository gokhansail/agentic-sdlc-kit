# Status

What is this file? The current state of agentic-sdlc-kit on one page. A new session reads this first and resumes from here.

Last updated: 2026-10-30
Now: Phase 1 · T-11 in progress · repository private · guard code written, tests green

## Phase

Phase 0 Setup closed: G0 passed 2026-10-29 (maintainer check in a fresh session; see LOG).

Phase 1 Playbook is open. G1 criteria (TASKS.md): every claim maps to a source-map line; no private data; maintainer read it once end to end; verdict by `auditor`, then `auditor-mini`.

## Done

- T-01 Decisions: DEC-001 to DEC-012.
- T-02 Record skeleton (0.0.1).
- T-03 Pre-push guard (0.0.1): installed, every push goes through it.
- T-04 Toolchain check: `docs/toolchain.md`, `requirements-dev.txt`; MCP SDK 2.x (DEC-013).
- T-05 Product `CLAUDE.md`: process rules in English, at most 80 lines. Personal rules are kept outside the repository, each rule in one place (DEC-014, DEC-015).
- T-10 Source map: `docs/source-map.md`, 9 sources, 64 concepts; private sources by ID (DEC-016); all 6 process lessons included (DEC-017).

## Next

- T-11 `PLAYBOOK.md` (in progress), then T-12 templates, T-13 role files, T-14 gate G1. The maintainer reads the source map and the playbook before G1.

## Repository

- Private (DEC-007). Only the maintainer changes visibility.
- Every push goes through the pre-push guard. Do not use `--no-verify`.
- Tests: `python -m pip install -r requirements-dev.txt`, then `python -m pytest -q`.
- Language: English for every file (DEC-003, DEC-015).

## Open questions

- None.
