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
