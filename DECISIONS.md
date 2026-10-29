# Decisions

One entry per decision. The maintainer decides; the Technical Lead records. "Outcome" is filled in later, when the decision can be judged against what happened. An empty outcome means not reviewed yet.

Entry format: date, question, options, decision, reason, consequences, outcome.

---

## DEC-001 Project name
- Date: 2026-10-29 · Question: D-1
- Options: a) `agentic-sdlc-kit` b) `gated-sdlc` c) `contract-sdlc`
- Decision: a) `agentic-sdlc-kit`. The repository already uses this name.
- Reason: says what the thing is. The other two names describe one mechanism each.
- Consequences: plugin namespace and commands use the `sdlc` prefix (`/sdlc:status` and so on).
- Outcome:

## DEC-002 Location
- Date: 2026-10-29 · Question: D-2
- Options: a) the current projects folder b) elsewhere
- Decision: a). The project stays next to the maintainer's other projects, outside the game documentation repository.
- Outcome:

## DEC-003 Language and what gets committed
- Date: 2026-10-29 · Question: D-3
- Options: a) everything in the repository is English; build records are committed b) build records are ignored; only the product is committed c) build records in the maintainer's language, translated before release
- Decision: a), with two layers:
  - Private layer, never committed (`.gitignore`): the day-0 plan, private rules, local session instructions, raw data. Conversation, quotes and personal context live only here.
  - Record layer, committed: `TASKS.md`, `DECISIONS.md`, `LOG.md`, `STATUS.md`, `CHANGELOG.md`, `audits/`. Written in English as engineering records: decision and reason, task and result, numbers. No conversation, no quotes, no company or person names.
- Reason: the claim "built with its own process" needs the records in the repository. Without them the claim cannot be checked.
- Consequences: the pre-push guard (T-03) and the publish-readiness audit (G5) check the record layer for private content, including git history.
- Outcome:

## DEC-004 Language for the server and scripts
- Date: 2026-10-29 · Question: D-4
- Options: a) Python 3.10+ with the official `mcp` SDK, `pytest` b) TypeScript on Node 24
- Decision: a).
- Reason: Python 3.10.4 is installed; the measurement scripts and the server share one language and one test runner.
- Consequences: T-04 must confirm the minimum `mcp` SDK version that supports Python 3.10.
- Outcome:

## DEC-005 License
- Date: 2026-10-29 · Question: D-5
- Options: a) MIT b) Apache-2.0
- Decision: a) MIT. The maintainer left the choice to the Technical Lead.
- Reason: short and permissive. The kit is documents, templates, hooks and a small server; Apache-2.0's patent grant adds length without a clear need here.
- Outcome:

## DEC-006 Naming the source projects
- Date: 2026-10-29 · Question: D-6
- Options: a) anonymous b) by name
- Decision: a). The two source projects appear as "Project A" (Unity, 63 versions) and "Project B" (Unity/WebGL, 103 commits).
- Reason: the projects are unreleased; their names and data add nothing to the method.
- Consequences: only totals from the measurement scripts enter the repository. Names can be added if the projects are released.
- Outcome:

## DEC-007 When the repository goes public
- Date: 2026-10-29 · Question: D-7
- Options: a) private until the publish-readiness gate b) public now
- Decision: a). The repository is private. It goes public after the G5 audit returns PUBLISH and the maintainer decides. Only the maintainer changes visibility.
- Outcome:

## DEC-008 Who runs the build
- Date: 2026-10-29 · Question: D-8
- Options: a) a session opened in this folder b) a session in the parent documentation folder
- Decision: a). A session opened in this folder is the Technical Lead (Opus, high effort) and resumes from `STATUS.md`.
- Outcome:

## DEC-009 Agent names
- Date: 2026-10-29 · Question: D-9
- Options: a) English names b) names in the maintainer's language
- Decision: a). `cto`, `developer`, `tech-writer`, `scout`, `scribe`, `auditor`, `auditor-mini`.
- Reason: they are part of the product. They do not collide with the maintainer's global agent files, which stay unchanged.
- Outcome:

## DEC-010 Measurement scope
- Date: 2026-10-29 · Question: D-10
- Options: a) both source projects b) Project A only
- Decision: a).
- Reason: Project B ran the first version of the process and Project A the second, so both are needed for a before/after view.
- Consequences: results are descriptive. n = 1 maintainer, and the process and the maintainer changed at the same time; no causal claim.
- Outcome:

## DEC-011 Claude Code only
- Date: 2026-10-29 · Question: D-11 (raised during T-01)
- Options: a) test the MCP server in Claude Code only b) also prove it in a second client
- Decision: a).
- Reason: the server follows the MCP standard. A second client adds setup cost and no new information about the method.
- Consequences: the second-client task is dropped and the G4 gate no longer requires it. The README says the server is standard MCP and has been tested with Claude Code only.
- Outcome:

## DEC-012 Evaluation with and without the MCP server
- Date: 2026-10-29 · Raised by the maintainer during T-01
- Decision: add an evaluation to phase 4 (T-46). A fixed synthetic repository and 30 questions whose answers depend on that repository's state (active contract, scope, open findings, past decisions), each with an answer key and automatic scoring. Matrix: several models, server attached and not attached, at least 3 runs per cell. Recorded per run: correctness, duration, input and output tokens, tool calls, cost estimate, errors.
- Reason: shows with numbers whether the server changes the result. General knowledge questions would not measure that.
- Consequences: raw outputs stay local; the repository gets the script, the questions, the totals and a limits section.
- Outcome:

## DEC-013 MCP SDK major version
- Date: 2026-10-29 · Raised in T-04
- Options: a) 2.x (2.3.0, `MCPServer`) b) 1.x (1.30.0, `FastMCP`)
- Decision: a) 2.x, `mcp>=2.3,<3`.
- Reason: both pass the smoke test on Python 3.10. 2.x is the current major; a new project that starts on the previous one starts with a migration to do. The server is small, and the SDK has a migration guide for older examples.
- Consequences: phase 4 code uses `MCPServer`; examples written for `FastMCP` need translating.
- Outcome:

## DEC-014 Where the private session instructions live
- Date: 2026-10-29 · Raised in T-04, for T-05
- Options: a) `CLAUDE.local.md`, ignored by git b) an `@` import from the committed `CLAUDE.md`
- Decision: a).
- Reason: Claude Code loads `CLAUDE.local.md` after `CLAUDE.md` by itself (documented). The behaviour of an `@` import whose file is missing is not documented, and the import line would show a private file name in the public file. The pre-push guard already rejects `CLAUDE.local.md`.
- Consequences: the committed `CLAUDE.md` mentions no private file; a clone without `CLAUDE.local.md` works as is.
- Outcome:

## DEC-015 All documentation in English, each rule in one place
- Date: 2026-10-29 · Raised by the maintainer during T-05
- Options: a) every file in English, committed or not; process rules only in `CLAUDE.md`, personal rules only in `CLAUDE.local.md`; the day-0 plan translated once and frozen b) private files stay in the maintainer's language next to an English `CLAUDE.md` c) one private `CLAUDE.md` now, split before release
- Decision: a).
- Reason: b) keeps two copies of the same rules that drift apart. c) moves the same split to just before release, the riskiest moment, and leaves the repository without a `CLAUDE.md` until then.
- Consequences: the local file starts with a table that says which file holds what and a test for new rules. The two earlier private files were merged into it and removed. The plan lives in an ignored archive folder and is not a source of truth. Conversation and sub-agent reports stay in the maintainer's language; that rule is in the local file.
- Outcome:

## DEC-016 How the source map names private sources
- Date: 2026-10-30 · Raised in T-10
- Options: a) committed map with source IDs and section numbers; the ID to file mapping in an ignored local index b) the whole map ignored c) real file names in the committed map
- Decision: a).
- Reason: the G1 claim "every claim maps to a source" stays visible in the repository, and an auditor on the maintainer's machine can resolve each ID. b) hides the evidence for that claim. c) exposes the structure of private documents, against DEC-006.
- Consequences: `docs/source-map.md` holds IDs, generic source descriptions and section numbers only; `.sdlc/local/source-index.md` holds the mapping. G1 is audited on the maintainer's machine.
- Outcome:

## DEC-017 All process lessons go into the source map and the playbook
- Date: 2026-10-30 · Raised by the maintainer during T-10
- Options: a) all process lessons (6 of the 19 entries in the lessons log) b) at most 3, as in the day-0 plan
- Decision: a).
- Reason: the cap of 3 had no stated reason. The three left out are the origin of three rules in the map (seat rule, current documents, tests belong to the user); without them those rules cannot be traced to an event. Map rows hold anonymous one-line summaries only, so six rows carry no more private detail than three.
- Consequences: the map lists six lesson concepts and no lesson in the dropped table. T-11 may use all six. Gate G1 reviews this choice: the auditor reports any privacy, length or relevance problem with the lessons as a finding.
- Outcome:
