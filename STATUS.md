# Status

What is this file? The current state of agentic-sdlc-kit on one page. A new session reads this first and resumes from here.

Last updated: 2026-10-29
Now: Phase 0 · G0 check · repository private · guard code written, tests green

## Phase

Phase 0 Setup. All phase 0 tasks are done. Gate G0 waits for the maintainer's check; after that, phase 1 opens.

G0 criteria:
- [x] Decisions recorded (DEC-001 to DEC-015).
- [x] The guard rejects a planted secret: 31 tests, plus a dry-run push from this repository that was rejected.
- [x] Toolchain notes have no "not verified" line for phases 1-3 (open points are for phase 4, T-46).
- [x] Product `CLAUDE.md` written (T-05). Committed with the G0 commit.
- [ ] Maintainer check: a fresh session in this folder resumes correctly from these files.

## Done

- T-01 Decisions: DEC-001 to DEC-012.
- T-02 Record skeleton (0.0.1).
- T-03 Pre-push guard (0.0.1): installed, every push goes through it.
- T-04 Toolchain check: `docs/toolchain.md`, `requirements-dev.txt`; MCP SDK 2.x (DEC-013).
- T-05 Product `CLAUDE.md`: process rules in English, at most 80 lines. Personal rules are kept outside the repository, each rule in one place (DEC-014, DEC-015).

## Next

- G0 check, then phase 1 in a fresh session: T-10 source map, T-11 `PLAYBOOK.md`, T-12 templates, T-13 role files, T-14 gate G1.

## Repository

- Private (DEC-007). Only the maintainer changes visibility.
- Every push goes through the pre-push guard. Do not use `--no-verify`.
- Tests: `python -m pip install -r requirements-dev.txt`, then `python -m pytest -q`.
- Language: English for every file (DEC-003, DEC-015).

## Open questions

- None.
