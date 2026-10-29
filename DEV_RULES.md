> **What is this file?** Project-specific rules for the `developer` and `tech-writer` sub-agents (and any third-party model profile) of agentic-sdlc-kit. Generic behaviour and report formats live in `.claude/agents/*.md`; this file holds only what is specific to this repository. Keep it under 40 lines. Written by the Technical Lead (first version 2026-10-29).

# Developer rules (agentic-sdlc-kit)

## Scope
1. Touch only the files named in the contract. Tests, fixtures and lockfiles are free. Anything else: stop and return an OPEN QUESTION.
2. Design, scope, naming-of-the-product and publishing decisions are not yours: OPEN QUESTION. Technical choices are yours; list them under "Technical decisions".
3. No commit, no push. No documents except the `CHANGELOG.md` line the contract names. Do not read or write `TASKS.md` (beyond your item), `DECISIONS.md`, `LOG.md`, `STATUS.md`, `cto/`, `audits/`.
4. No network calls in the code you write: the hooks and the MCP server work offline. No secrets, no absolute user paths, no personal data in code, tests or fixtures.

## Language and style
5. Code, comments, docstrings, test names, README snippets: English. **Reports to the TL: Turkish** (user preference; applies to every sub-agent in this project). Comments are rare and explain why, not what.
6. Python: compatible with 3.10 (the machine runs 3.10.4) unless decision D-4 says otherwise; type hints; `pytest -q`; no new dependency without naming it in "Technical decisions". TypeScript (only if D-4 = b): Node 24, `strict` on, `npm test`.
7. Markdown files are the source of truth. The server and the hooks read and write them in place; the only other store is `.sdlc/metrics.jsonl`.

## Verification
8. "Done" means the tests are green: run them and paste the summary line. A test you could not run is reported as "not run: <why>", never as green.
9. Anything that blocks or refuses (hook, validator, path guard) ships with one test proving it blocks and one proving the legal case passes.
10. Path safety: every file operation resolves inside the project root given at start; include tests with `..` segments and absolute paths outside the root.

## Source material
11. When a contract points at `Documents/Unity/...`, a game project or office notes, read only the named section and take **concepts, never text**: no game or repo names, no player data, no URLs, no keys, no company or product names. Numbers come only from `tools/metrics` output.

## Report
12. Fixed format from `developer.md` (or `tech-writer.md`): TASK · MODEL · CHANGED FILES · BUILD/TESTS · OUT OF SCOPE · TECHNICAL DECISIONS · OPEN QUESTION · WHAT THE TL SHOULD CHECK · CHANGELOG. State your model name correctly (Sonnet is not Opus).
