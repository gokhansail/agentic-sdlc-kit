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
- Decision: a). The two source projects appear as "Project A" and "Project B", two game projects. Their size is measured in phase 2. (Engine name and two counts removed on 2026-11-02, DEC-020.)
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
- Options: a) all process lessons (6 entries in the lessons log; total count removed on 2026-11-02, DEC-020) b) at most 3, as in the day-0 plan
- Decision: a).
- Reason: the cap of 3 had no stated reason. The three left out are the origin of three rules in the map (seat rule, current documents, tests belong to the user); without them those rules cannot be traced to an event. Map rows hold anonymous one-line summaries only, so six rows carry no more private detail than three.
- Consequences: the map lists six lesson concepts and no lesson in the dropped table. T-11 may use all six. Gate G1 reviews this choice: the auditor reports any privacy, length or relevance problem with the lessons as a finding.
- Outcome:

## DEC-018 No separate portability document
- Date: 2026-11-01 · Raised in T-13
- Options: a) drop `docs/portability.md`; appendices H and I of `PLAYBOOK.md` are the portability note b) a short file per kit component, concept and part to rebuild, pointing to appendix H c) a table of Claude Code features and their equivalents in a second tool, with a new source row
- Decision: a).
- Reason: appendices H and I already map each concept to its mechanics and list the parts to rebuild in another tool. b) repeats them in a second place. c) needs claims about another tool that no source row backs, and the second-client task was dropped (DEC-011).
- Consequences: T-13 covers the role files and `DEV_RULES.md` only. Source-map rows that target T-13 are traced in the role files or are already cited in appendix H.
- Outcome:

## DEC-019 Role file wording: one term for the person, report language from the brief
- Date: 2026-11-01 · Raised in T-13
- Options for the term: a) "customer", as in `PLAYBOOK.md` b) "maintainer" c) "user". Options for the report language: a) the TL's brief names it; committed files name no language b) the committed developer rules name it
- Decision: a) and a).
- Reason: role files are part of the product and should use the playbook's term. In this repository the customer is the maintainer. The conversation language is the maintainer's choice, not a rule of the method (DEC-015).
- Consequences: role files and `DEV_RULES.md` say "customer" and "the language the brief names". The TL names the language in every brief.
- Outcome:

## DEC-020 Answers to the G1 audit questions
- Date: 2026-11-02 · Raised by `audits/2026-11-02_gate1.md` section 7
- Decision: the auditor's recommendation on its five questions, and the TL's recommendation on a sixth (item 6).
  1. The `tech-writer` role enters the playbook: one sentence in the core Roles paragraph and a row in the Appendix A matrix, cited to DEC-009 (D-1).
  2. Appendix H states the hooks that exist: a pre-push hook for the test flag and private data (C-46, C-47). Hook enforcement of the developer rules is a rule of the standard (C-56), built in T-31 (D-2).
  3. No engine name and no measured count from a private source in the records. DEC-006 and DEC-017 edited; the counts come from phase 2. The engine name stays in the history of the commits before e42b560; the history is not rewritten, because the name is not a secret (S-1). Audit reports are not edited after they are written, so the G1 report keeps its lesson count as evidence.
  4. Gate verdict wording: the auditor gives the verdict, the customer decides what follows (D-3).
  5. The read criterion stays. The maintainer reads `PLAYBOOK.md` end to end after the fixes, and the LOG records the date and the corrections (P-1).
  6. All Low findings are fixed in the same contract as the Medium ones (T-15). The fifth finding type, S- for security and privacy, is kept and traced to this decision (D-8).
- Reason: the fixes are small and touch the same files; one contract and one re-verification cost less than two. Reading after the fixes means the read covers the text that passes the gate.
- Consequences: T-15 fix contract; then the maintainer's read; then `auditor-mini` re-verifies G1.
- Outcome: 2026-11-02, `auditor-mini` closed 14 of 14 findings and all 4 conditions; G1 ACCEPT (`audits/2026-11-02_reverify.md`).

## DEC-021 Phase 2 metric set
- Date: 2026-11-02 · Question: D-21 (`cto/2026-11-02_phase2-plan.md` section 2)
- Options: a) 8 metrics counted by script (M1, M2, M3, M5, M6, M8, M9, M12), M4, M7, M10, M11 dropped, M13 share of hard tasks added b) a) plus M4 as a committed hand list c) minimal set M1, M2, M3, M5, M12
- Decision: a).
- Reason: every published number then comes from a script and can be rerun. M4 is a hand list with a very small n; M7 needs a hand label; M10 is specific to the source domain and includes other people's sessions; M11 has no source, and T-46 measures cost.
- Consequences: 9 metrics in T-20 and T-21. A metric with no record in a source shows "no data", never 0. M9 counts filled outcomes only; the right/wrong label is dropped.
- Outcome:

## DEC-022 Marker words in the source records
- Date: 2026-11-02 · Question: D-22
- Options: a) fold the input text to ASCII and keep the folded markers in a committed profile per source b) profiles kept in `.sdlc/local/` c) unicode escapes in the parser code
- Decision: a).
- Reason: the counting rule behind each published number stays public and readable, and the guard passes. b) hides the rule, which conflicts with the G5 criterion that every README number is reproducible. c) is unreadable in review.
- Consequences: the profiles show the language of the source records; no names or content. No marker literal in code; fixtures use invented English markers, plus one folding test that builds its letters with `chr()`.
- Outcome:

## DEC-023 This repository as a third source
- Date: 2026-11-02 · Question: D-23
- Options: a) yes, in its own column, with no before/after comparison b) no
- Decision: a).
- Reason: it is the only series a stranger can rerun from the public repository.
- Consequences: `evidence/kit.json` next to the two source files. The kit column has v2 data only.
- Outcome:

## DEC-024 Input pinning
- Date: 2026-11-02 · Question: D-24
- Options: a) snapshot the named record files into the ignored `evidence/raw/` plus a manifest with SHA-256 hashes and the source HEAD b) read from a source commit only, after the maintainer commits Project A's records c) read the working tree, no pinning
- Decision: a).
- Reason: it works while Project A has uncommitted record changes, and a rerun can prove it read the same input.
- Consequences: a copy of private record text sits inside the kit folder. `.gitignore` and the guard cover `evidence/raw/`; `git add -f` is the remaining hole and is never used. The snapshot date ends Project A's v2 series before T-33 dogfoods the kit on it.
- Outcome:

## DEC-025 Small cells
- Date: 2026-11-02 · Question: D-25
- Options: a) a cell with fewer than 5 items shows the count and no rate b) rates everywhere with n beside them
- Decision: a).
- Reason: a rate over 2 or 3 items reads as more than it is. The threshold 5 is a judgment, not derived from data; the limits section says so.
- Consequences: the render step applies the rule; the limits section lists the cells shown as counts only.
- Outcome:

## DEC-026 Phase 2 task split and gate
- Date: 2026-11-02 · Question: D-26
- Options: a) five tasks: T-20 core and text metrics, T-21 git, audit and decision metrics plus render, T-22 run, T-23 `EVIDENCE.md` text, T-24 gate b) three tasks as first named c) four, T-22 and T-23 merged
- Decision: a). G2 becomes the 6 checks of the CTO report section 3. The G2 verdict stays with `auditor-mini`.
- Reason: one script task for all parsers does not fit a 15-line contract. Running on private data (`scout`) and writing prose (`tech-writer`) are different roles. Privacy at G2 is covered by the guard and a JSON schema test; the full `auditor` reviews the whole history at G5.
- Consequences: before T-20, `scout` returns the record formats and the TL writes a local format note with invented examples, so `developer` never reads the private records (DEV_RULES 11).
- Outcome:

## DEC-027 Customer result in the per-task metrics line
- Date: 2026-11-02 · Question: D-27
- Options: a) the metrics line records "customer result: done | redo | not tested" from T-20 on b) narrow `PLAYBOOK.md` Appendix F to the three fields the kit records c) leave the mismatch
- Decision: a).
- Reason: Appendix F names the customer's test result as a per-task metric. The kit should record what its playbook says; b) would fit the method to the gap.
- Consequences: the TL dictates the field to `scribe` in every metrics line from T-20 on; `scribe.md` already accepts an outcome value. Earlier lines count as "not recorded".
- Outcome:

## DEC-028 M1 counting rule
- Date: 2026-11-02 · Question: open point M1 in the local format note (P-20)
- Options: a) M1 counts version-level reverts (heading form) over all versions; item-level reverts are a separate count in the same metric b) a version counts as reverted when at least one of its items is reverted
- Decision: a).
- Reason: the metric is named reverted versions. b) puts a whole version taken back and one item taken back into the same number; two counts keep either from inflating the other.
- Consequences: T-20 adds an `items` field next to the M1 rate. A revert word in the heading scope or in the work log never counts. Version-level revert headings carry no date; T-20 gives an undated heading the period of its two dated neighbours when both agree, otherwise `undated` with a warning.
- Outcome:
