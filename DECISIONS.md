# Decisions

One entry per decision. The maintainer decides; the Technical Lead records. "Outcome" is filled when a later fact judges the decision; an empty outcome is normal, not a gap (DEC-058).

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
- Outcome: T-22 (2026-11-03): Project A has v1 and v2 data for M1, M2, M3, M8, M9 and M12; Project B adds v1 data for M3, M8 and M12 only. B is a second v1 source, not the only one. M5 and M6 have v2 data only (Project A and the kit).

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
- Outcome: T-33 cannot enter the series; see DEC-034.

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

## DEC-029 Project B audit folder in M8
- Date: 2026-11-03 · Question: open point M8 in the local format note (P-20), raised in the T-21 contract
- Options: a) count it; the manifest marks each file `tracked: false` and the limits section says its history cannot be checked in git b) leave it out; Project B shows "no data" for M8
- Decision: a) (2026-11-03).
- Reason: it is the only v1 audit data of Project B; the snapshot hash pins the text whether git tracks it or not.
- Consequences: a) adds one limits item for T-23; b) leaves M8 with Project A and the kit only.
- Outcome:

## DEC-030 Project A metric lines in other layouts
- Date: 2026-11-03 · Question: T-22 parse coverage; 9 of 20 Project A v2 log entries with task numbers were not counted
- Options: a) extend the parser to the two layouts seen (metrics label mid-line; TL review line with `tur <n>`) and take `tur <n>` as written b) as a), but map "round 1, no fix" to 0, the kit's rule c) no parser change; a limits item only
- Decision: a) (2026-11-03).
- Reason: 9 of 20 is too large for a limits item. The script does not reinterpret a number in a source record; the source uses both meanings of the round number, and the limits section says so.
- Consequences: reverses the P-20 format note, which treated the TL review line as free text. New task T-22a; Project A is rerun from its existing snapshot. One entry with two conflicting free-text round numbers stays unparsed and goes to the limits section.
- Outcome: T-22a (2026-11-03): Project A M5 v2 n 10 to 18; 19 of 20 entries parsed, one of them without a round number; M6 n 17 per field; no v1 task added; kit result unchanged (same SHA-256). Correction 2026-11-04 (G2 candidate N-3): the unparsed entry holds round numbers for two different tasks, not two conflicting numbers for one task; the entry without a round number holds a fix-round count under another label.

## DEC-031 Numbers outside the rendered block in `EVIDENCE.md`
- Date: 2026-11-04 · Question: T-23 contract; `cto/2026-11-02_phase2-plan.md` asks that every number sit in the rendered block, but the limits section needs numbers the block does not hold (period lengths in days, warning counts, parse coverage)
- Options: a) written by hand in the limits section only, each with its source named; `auditor-mini` checks them at G2 b) first extend `render` and the result schema and rerun; coverage counts stay by hand
- Decision: a) (2026-11-04).
- Reason: the inputs are pinned by hash, so these numbers do not drift. The Project A and B snapshots are private, so b) gives a stranger nothing more to rerun. Coverage counts are by hand under either option.
- Consequences: narrows the T-23 acceptance line of the CTO plan. Metric results stay in the marked block only. Outside it, `EVIDENCE.md` holds method dates and thresholds, and limits numbers with a named source. One more item for G2 to check by hand.
- Outcome:

## DEC-032 Where the G2 rerun happens
- Date: 2026-11-04 · Question: T-24 contract; G2 check 1 asks for a clean checkout, but `evidence/raw/` is ignored by git, so a clean checkout holds no snapshot
- Options: a) a clean working tree of the gate commit in this folder, using the local snapshots b) a fresh clone with the snapshots copied into it
- Decision: a) (2026-11-04).
- Reason: b) makes a second copy of private record text for no gain; `git status --porcelain` shows whether the tree was clean and whether the rerun changed anything.
- Consequences: narrows the G2 row in `TASKS.md` and check 1 of the CTO plan. The gate does not test a fresh clone; the stranger's route for the kit is the one `EVIDENCE.md` describes, tested once by the TL.
- Outcome:

## DEC-033 Where T-33 runs
- Date: 2026-11-04 · Question: D-31; the local instructions keep the source projects read-only, and G3 demands a real task on Project A
- Options: a) a written exception for T-33 only, in Project A's own repository, on a branch b) a full local clone, the result returned as a patch c) change G3 to another real repository d) this repository only
- Decision: a).
- Reason: the value of G3 is the mismatch with a project the kit was not built in. b), c) and d) each remove part of that mismatch. The read-only rule protected the measured data and the project from kit build sessions; the data is pinned (DEC-024, DEC-034), and the session is that project's own TL under its own permission rule.
- Exception: T-33 only; session opened in the Project A folder; writes limited to the 4 items below; ends when T-33 closes or is abandoned; the read-only rule then returns unchanged. It does not start before P-33 passes (DEC-043).
- Written in Project A: 1) `.sdlc/`, not tracked 2) one line for `.sdlc/` in `.git/info/exclude` 3) `.git/hooks/pre-push` as a chain wrapper, the old hook kept beside it, its hash noted first 4) the real task's own change on a branch, under that project's own rules. Not written: plugin files, its `CLAUDE.md`, `core.hooksPath`.
- Approval: the customer names the task and gives the go-ahead in the Project A session. That session writes the contract and reviews the diff. The kit TL receives totals only. A merge needs the customer's "done".
- Rollback: delete the branch, or revert the one commit after the customer's word; uninstall restores the old hook with the same hash; remove `.sdlc/` and the exclude line; `git status` equals the state noted before T-33.
- Consequences: the hook, `.sdlc/` and state steps of the rollback are rehearsed in P-33. Which task runs is open; the customer picks it from Project A's own list before T-33. Filter proposed by `cto`: medium size, at least 2 files, an automatic test exists, not judged by feel only.
- Outcome: T-33 ran 2026-11-07 under this exception. Writes stayed in the 4 items. The task ran on a branch and was merged fast-forward after the customer's word. Kit rollback: hook folder hash-equal, exclude file and `git status` equal to the state noted before. The exception ended at close.

## DEC-034 How T-33 output is recorded
- Date: 2026-11-04 · Question: D-32
- Options: a) `docs/dogfood-1.md` with fixed fields, plus T-33a b) the same note, a written rule instead of T-33a c) `LOG.md` line only
- Decision: a).
- Reason: Project A's v2 series ended at the 2026-11-03 snapshot, so T-33 cannot change a published number by itself. The one route is `--snapshot`: `snapshot()` writes over an existing copy with no check, and `evidence/raw/` is not in git. `PLAYBOOK.md` lesson 2: a rule is enforced or deleted.
- Consequences: `EVIDENCE.md` and `evidence/` do not change in phase 3 (G3-8). T-33a adds a refusal to `--snapshot` when a manifest exists for the label. The note holds totals only, no file names and no before/after claim. A later Project A series takes a new label and belongs to phase 6.
- Outcome: T-33 totals are in `docs/dogfood-1.md`. After T-33, `EVIDENCE.md` and `evidence/` have no change since `2bd234e`, and the Project A manifest hash equals the value noted before T-33.

## DEC-035 Source of truth for the role files
- Date: 2026-11-04 · Question: D-33
- Options: a) `agents/` is the source, `.claude/agents/` a copy, a test fails on any difference after line endings are normalized b) generate `agents/` at release, not committed c) pointer stubs in `.claude/agents/` d) delete `.claude/agents/`, always run with `--plugin-dir .`
- Decision: a).
- Reason: a clone must load as a plugin, which rules out b). c) still doubles the frontmatter. d) depends on V-9. Symlinks are not available on this machine. The test enforces what "one place" cannot.
- Consequences: a role edit touches two files. `CLAUDE.md` names the source folder after T-30.
- Outcome: T-30: `agents/` is the source, `tests/test_role_sync.py` compares the copy; green at G3 (`audits/2026-11-07_gate3.md`). `DEV_RULES.md` points to `agents/` since T-34a.

## DEC-036 Model names in plugin agents
- Date: 2026-11-04 · Question: D-34
- Options: a) keep the aliases (`opus`, `sonnet`, `haiku`, `fable`), no versions b) `inherit` everywhere c) full model IDs
- Decision: a).
- Reason: the alias is the tier in `PLAYBOOK.md` Appendix A. b) lets the auditor run on a small model. c) goes stale at each release; T-13 removed version numbers.
- Consequences: P-30 checks that `fable` validates (V-1) and that `effort` and `tools` take effect (V-2). What happens on an account without an alias stays open until T-51 (V-11).
- Outcome: P-30: `model: sonnet` in a plugin agent ran on Sonnet under a Haiku main session. `claude plugin validate` does not check the value.

## DEC-037 Scope guard states and who it binds
- Date: 2026-11-04 · Question: D-35
- Options: a) no `.sdlc/project.md`: allow, silent; opted in with no contract: deny, except the always-allowed list; active contract: allow `Files in` and the list, deny the rest, `Files out` wins; broken contract: deny b) opted in with no contract: allow with a warning c) block wherever the plugin is enabled
- Decision: a).
- Reason: work started before a contract is the common failure, and b) lets it pass. c) stops every other project of the user.
- Consequences: `.sdlc/project.md` is the opt-in and the one config file, written by `/sdlc:init`. One event line per decision goes to `.sdlc/metrics.jsonl`, no path, not committed; this moves part of the schema from T-41 to T-31. If hook input does not name the sub-agent (V-4), a developer can widen its own scope by editing the contract; that becomes a stated limit, covered by the TL's diff review. TL contracts move to `Files in` and `Files out`.
- Outcome: P-30: hook input names the sub-agent in `agent_type`, so the limit in the consequences falls away; T-31 can deny sub-agent writes to `.sdlc/`. T-31: a main-session write outside the root is denied too; P-33 shows whether that blocks useful work. P-33: no such write was tried and the customer reported no wrong denial, so this stays open for T-33. T-33: one main-session write outside the root, a note to the session's own memory folder, was denied; the task was not blocked. Whether to allow that folder is open for the customer (`docs/dogfood-1.md` finding 1). Decided in DEC-046: allow the memory folder for the main session only.

## DEC-038 Writes through Bash
- Date: 2026-11-04 · Question: D-36
- Options: a) hook on the 3 file tools; `/sdlc:review` compares `git status --porcelain` with the contract; the limit is written down b) a, plus a Bash deny list c) a, plus an automatic check on a stop event d) remove Bash from the developer
- Decision: a).
- Reason: the developer needs Bash for tests, which rules out d). A deny list gives false cover and false blocks. c) can wait until one real task shows whether a is enough.
- Consequences: the scope guard is not a security boundary. It catches a developer leaving its contract by mistake; a Bash write is found at review, not stopped, and ignored files stay unseen. The documents say so, and `PLAYBOOK.md` Appendix H states what exists after T-31.
- Outcome: T-30a added `--check-worktree`, which `/sdlc:review` runs. In a live run it named a file created outside the contract with no file tool. Ignored files stay unseen, as stated.

## DEC-039 Scope guard bypass
- Date: 2026-11-04 · Question: D-37
- Options: a) no bypass flag b) an environment variable set at launch, each skip logged c) a flag file in `.sdlc/local/`
- Decision: a).
- Reason: a bypass an agent can reach is no guard. The normal path is a wider contract after the customer's word. The customer can also start a session without the plugin or remove `.sdlc/project.md`.
- Consequences: a session run without the plugin leaves no log. V-7 needs no check.
- Outcome: no bypass flag was built. In P-33 and T-33 the guard was turned off only by removing `.sdlc/` at rollback.

## DEC-040 Hook runtime
- Date: 2026-11-04 · Question: D-38
- Options: a) Python 3.10+, standard library only, started by a short `sh` launcher b) `python` directly c) `python3` directly d) Node
- Decision: a).
- Reason: the guard is already standard-library Python and phase 4 needs Python (DEC-004). `python3` is a store stub on this machine. Exit 2 blocks and other codes do not (V-6, not verified), so a crash must become a deny.
- Consequences: Python becomes a stated requirement of the plugin, no pip step in phase 3. The launcher checks opt-in without Python, and any failure in an opted-in project is exit 2 with a reason. Windows without Git Bash is a stated limit. `cto` proposes a time budget of 1 s per call; T-31 measures it.
- Outcome: P-30: exit 1 and exit 127 let a write through, as assumed. A timeout does too, and a launcher cannot turn that into a deny; T-31 states it as a limit. T-31: median 422 ms to 598 ms per call, under the 1 s budget; one outlier of 24.4 s, not repeated in 200 calls; hook timeout set to 30 s.

## DEC-041 Commands in phase 3
- Date: 2026-11-04 · Question: D-39
- Options: a) 5 skills: `status`, `init`, `contract`, `review`, `install-hooks` b) 8 skills, 3 of them text-only guides c) 3 skills: `status`, `contract`, `install-hooks`
- Decision: a).
- Reason: G3 needs a contract, a review and an install, and DEC-038 needs `review`. `gate`, `decision` and `lesson` get real tools in T-42 and have no reason to exist before it.
- Consequences: T-33 writes decision and lesson records by hand. `init` and `install-hooks` run only when called by name, if V-12 holds. `templates/task-contract.md` stays the source of the contract form.
- Outcome: built in T-30a, 5 skills. All 5 ran as typed commands in `claude -p` on Haiku, 9 runs. The model's call of `init` and `install-hooks` was refused. Added in the contract: `/sdlc:contract close`. Not yet run in the customer's terminal: P-33.

## DEC-042 Git hook and guard in another repository
- Date: 2026-11-04 · Question: D-40
- Options: a) a target mode in the one installer: copy the guard to `.sdlc/guard/`, chain wrapper in `.git/hooks/pre-push`, `core.hooksPath` left alone, `--uninstall` b) a hook that calls the plugin folder by absolute path c) `core.hooksPath` into a copied folder
- Decision: a).
- Reason: `core.hooksPath` would silently switch off a repository's existing local hook, as Project A's would be. A copy works offline, with no plugin, from any terminal. An absolute path breaks at every plugin update.
- Consequences: T-32 is [H]. Kit mode and its 17 tests stay unchanged. The installer refuses if `core.hooksPath` is set and reports a stale copy. Patterns: a generic template without the language line; private patterns stay per project, created empty, never copied from the kit; project-specific forbidden paths move to the pattern file.
- Outcome: built in T-32. Real pushes to a local bare repository from a repository with an existing hook: clean push passes, planted secret rejected, uninstall leaves the hook folder hash-equal. The kit test file holds 31 tests, not 17, and is unchanged. Set in the contract: the installer writes the exclude line; uninstall leaves the patterns, `.sdlc/local/` and the exclude line for the manual rollback step; `forbid-path` lines replace the built-in list. Not yet run in the customer's terminal: P-33.

## DEC-043 Phase 3 task split, G3 row and where it runs
- Date: 2026-11-04 · Question: D-41, plus the terminal question in item 11 of the CTO report's customer questions
- Options: a) 9 items (P-30, T-30, T-31, T-32, T-30a, T-33a, P-33, T-33, T-34) and 9 G3 criteria b) the 5 tasks as named, only the G3 row sharpened c) a without P-33
- Decision: a). The customer runs P-33 and T-33 in a terminal they opened, not in the desktop app (G3-7).
- Reason: T-31 today would rest on unverified plugin facts, and P-30 closes those. A unit test fed with our own stdin proves the script, not that Claude Code calls it, so G3-3 adds a live check. Without P-33 the first run of the hook chain and the uninstall is on Project A; DEC-033 depends on P-33.
- Consequences: order of `cto/2026-11-04_phase3-plan.md` section 2, about 6 sessions (opinion). Hard share 2 of 8 tagged tasks, 25%, under the 30% rule. The G3 row in `TASKS.md` becomes the 9 criteria of section 3. G3-7 is a customer statement; the auditor checks only that it is recorded.
- Outcome: P-33 and T-33 both ran in a PowerShell window the customer opened, on 2026-11-07. Load, scope guard and 4 pushes through the hook worked there; the customer reported no problem. G3-7: on 2026-11-07 the customer stated that both the rehearsal and the Project A task ran in a PowerShell window they opened, and that the plugin loaded, the guard worked and the push passed. CLI 2.1.296 and 2.1.319 for P-33, 2.1.319 for T-33.

## DEC-044 Strict validate at a repository root with `CLAUDE.md`
- Date: 2026-11-05 · Question: T-30 open question
- Options: a) keep `CLAUDE.md` at the root; on a clean copy `--strict --json` may hold that one warning and no other finding b) move it to `.claude/CLAUDE.md` c) move the plugin to a subfolder
- Decision: a).
- Reason: `--strict` treats warnings as errors, and this warning says the file is not loaded for plugin users, which is the wanted behaviour: the file serves work on the kit. Measured on clean copies: at the root, exit 1 with that warning; at `.claude/CLAUDE.md`, exit 0. b) touches 11 tracked files, and loading from there is not verified in this project. c) needs the guard tools and templates inside the subfolder.
- Consequences: G3-1 reads: on a clean copy, `claude plugin validate . --strict --json` holds the `CLAUDE.md` root warning and no other finding, and plain `validate` exits 0. The inventory (7 agents, commands, hook) comes from `claude plugin details`, because validate lists only files with findings. `CLAUDE.local.md` raises the same warning in a working copy only. T-51 checks whether a marketplace needs strict to pass.
- Outcome: measured on 2.1.296. On 2.1.319 the G3 auditor saw strict validate add a plugin-directory item (`ICON_MISSING`, not blocking) and README advice besides the `CLAUDE.md` warning; plain validate exits 0. G3-1 passed on that basis (`audits/2026-11-07_gate3.md`). T-51 decides whether the icon and README items are fixed.

## DEC-045 Triage of the T-33 findings before G3
- Date: 2026-11-07 · Question: which of the 9 findings in `docs/dogfood-1.md` are fixed in phase 3
- Options: a) fix finding 4 in phase 3 (T-33b), keep finding 1 open for the customer with the deny unchanged, carry the other 7 as stated limits into later phases b) fix findings 3, 4, 5 and 7 in phase 3 c) fix none before G3
- Decision: a). The customer accepted the TL proposal on 2026-11-07.
- Reason: finding 4 lets a sub-agent change its own rules, which the scope guard exists to stop. The other findings cost time and none lets a write leave its contract unseen beyond what DEC-038 already states. b) adds 3 tasks of medium size to a phase that has its real task done.
- Consequences: finding 1 stays an open customer question; the deny outside the root is unchanged. Findings 3, 6, 7 and 9 go to the release phase work on install and first use. Findings 2, 5 and 8 are stated limits: engine-side writes are not seen, `--check-worktree` does not know files changed before the task, a role can miss a line of a project's own rules file.
- Outcome: T-33b built the fix for finding 4; a glob in `Files in` that matches the rules file counts as naming it (G3 finding D-2, open for the customer). Findings 3, 6, 7 and 9 are on the phase 5 line of `TASKS.md`.

## DEC-046 Main-session notes outside the project root
- Date: 2026-11-07 · Question: DEC-037 open point, `docs/dogfood-1.md` finding 1, G3 customer question 2
- Options: a) the main session may write in the CLI's per-project memory folder under the user's Claude configuration folder; every other path outside the root stays denied; sub-agents stay denied b) keep the deny for every path outside the root
- Decision: a). The customer accepted the TL recommendation.
- Reason: in T-33 the deny stopped a memory note and nothing else. The notes are not project code, and a session that cannot keep notes loses them at the end of the conversation.
- Consequences: a phase 4 task in `tools/scope_guard.py` and its tests. The folder is found from the hook input or the CLI's known layout, never from a pattern the project file sets. `PLAYBOOK.md` Appendix H names the exception.
- Outcome:

## DEC-047 The kit runs its own scope guard
- Date: 2026-11-07 · Question: G3 finding D-1, customer question 3
- Options: a) opt this repository in during phase 4: `.sdlc/project.md`, contracts opened with `/sdlc:contract` b) stay out and state in the README that the kit's own sessions run without the guard
- Decision: a). The customer accepted the TL recommendation.
- Reason: the README says the kit is built with its own process; G3 found a document edited outside an open contract that the guard would have flagged.
- Consequences: `tests/test_scope_guard.py` `test_this_repository_has_not_opted_in` flips. The always-allowed list covers the records, `audits/`, `cto/` and `docs/`; the developer rules file stays out (DEC-045). Sessions here load the plugin with `--plugin-dir .`; whether a desktop app session can (V-9) is checked first, and if it cannot, that limit is written down. A TL brief to `tech-writer` gets its own contract line.
- Outcome: T-39a 2026-11-08: `.sdlc/project.md` committed; the guard runs from `.claude/settings.json` (DEC-049), checked live in `claude -p` and in a desktop app session.

## DEC-048 The developer rules file needs its exact name in Files in
- Date: 2026-11-07 · Question: G3 finding D-2, customer question 4
- Options: a) a sub-agent may change the developer rules file only when `Files in` holds its exact path as a token with no `*`, `?` or `{` b) any matching glob counts, and the limit is written down
- Decision: a). The customer accepted the TL recommendation.
- Reason: with b) a broad contract such as `**` re-opens the hole T-33b closed. The cost of a) is one explicit token in the rare task that edits the rules.
- Consequences: a phase 4 change in `tools/scope_guard.py` and its tests, in the same task as DEC-046. `skills/init/SKILL.md` and `PLAYBOOK.md` Appendix H say "exact path".
- Outcome:

## DEC-049 How the kit's own guard runs in a desktop app session
- Date: 2026-11-08 · Question: V-9 desktop half, DEC-047 fallback (`cto/2026-11-07_phase4-plan.md` debt list)
- Options: a) `.claude/settings.json` in this repository registers the same launcher from the repository, with `CLAUDE_PLUGIN_ROOT` set to the project folder b) install the plugin from a local marketplace into the user settings c) open the kit's sessions in a terminal with `--plugin-dir .` d) write the limit down only
- Decision: a). The customer accepted the TL recommendation.
- Reason: a desktop app session in this folder loads no plugin: no `/sdlc` commands and no `sdlc:` agents, and the app has no `--plugin-dir` option. With d) the opt-in protects nothing in daily work. b) runs a cached copy, so each guard change needs an update. c) changes how the customer works.
- Consequences: T-39a adds `.claude/settings.json`; a session that also loads the plugin with `--plugin-dir .` runs the guard twice, and `CLAUDE.md` says not to. Other projects still use the plugin. `docs/toolchain.md` V-9 row records the desktop result.
- Outcome: T-39a 2026-11-08: the settings hook denied a `PLAYBOOK.md` edit with no contract in `claude -p` and in a new desktop app session.

## DEC-050 The phase 4 server reads only
- Date: 2026-11-08 · Question: `cto/2026-11-07_phase4-plan.md` question 1
- Options: a) the server only reads records in phase 4 b) write tools, with the hook matcher widened to the server's tools c) write tools, sub-agents kept away only by role tool lists
- Decision: a). The customer accepted the TL recommendation.
- Reason: the scope guard does not see MCP tool calls, and the developer role has all tools. Writes stay on the file tools the guard sees.
- Consequences: T-42 is [M], read tools only. A write tool is a later decision with its own guard change.
- Outcome:

## DEC-051 The user installs the `mcp` SDK
- Date: 2026-11-08 · Question: `cto/2026-11-07_phase4-plan.md` question 2
- Options: a) the user installs it; the server checks package and version at start and stops with a one-line install hint b) start the server with `uv run` c) a command builds a virtual environment once in the plugin data folder
- Decision: a). The customer accepted the TL recommendation.
- Reason: no new tool for the user in phase 4; the user-facing install path is chosen in phase 5 with the release.
- Consequences: T-40 adds the start check and its test. b) and c) stay open for T-51.
- Outcome:

## DEC-052 Developers write files with the file tools only
- Date: 2026-11-08 · Question: T-40 finding (12 of 14 files written through Bash, 2 guard events)
- Options: a) a rule in `DEV_RULES.md` and the developer role: repository files are created and changed with Write or Edit only; Bash runs tests, reads and measurement scripts; no git command that changes the index, the work tree or history b) keep DEC-038 as it is: Bash writes are found at review
- Decision: a). The customer accepted the TL recommendation.
- Reason: in T-40 the guard saw 2 of 14 writes and `git stash` briefly removed the TL's uncommitted record change. The review check found no file outside the contract, but the event lines, which G4-7 counts, stayed nearly empty.
- Consequences: T-40a. The rule is a convention; DEC-038 is unchanged and `--check-worktree` stays the check. `DEV_RULES.md` rule 7 is narrowed to the read-only server (DEC-050).
- Outcome: T-40a 2026-11-08: rule in `DEV_RULES.md` (rule 5) and the developer role; the next developer task logged 4 of 4 writes.

## DEC-053 How the eval runs (T-46b)
- Date: 2026-11-08 · Question: T-46b, 3 questions to the customer
- Options: isolation a) `claude -p --bare` with the API key b) the subscription login without `--bare`; models a) Haiku and Sonnet b) Haiku, Sonnet and Opus c) Haiku only; budget a) a pilot first b) the full matrix at once.
- Decision: `--bare` with the API key; Haiku and Sonnet; a pilot of 20 runs (5 questions x 2 models x 2 conditions x 1 run, cap 3 USD), then the full matrix of 360 runs with a cap set from the pilot cost. The customer accepted the TL recommendation on all 3.
- Reason: without `--bare` every run loads the user's own plugins, global instructions and memory, so the two conditions would differ in more than the server. Two models meet "several models" in DEC-012 at the lowest cost. The cost per run is not measured yet; the pilot measures it before the larger spend.
- Consequences: the runs bill the API account, so the per-window key reminder does not apply to them. Each run works in a copy of `eval/repo/` outside the kit, so the model cannot read the answer key. Both conditions get the same base tools (Read, Grep, Glob, ToolSearch); the server condition adds the server through `--mcp-config`. Totals go to `eval/results/`, raw output stays outside the repository; `EVIDENCE.md` and `evidence/` stay unchanged (G4-10).
- Outcome:

## DEC-054 Eval runs on the subscription login; Read as the only base tool
- Date: 2026-11-08 · Question: T-46b step 0 (V-16)
- Facts: 11 calls with `ANTHROPIC_API_KEY` were refused with "Credit balance is too low" (0 tokens, 0 USD). On 2026-11-09 the customer's console showed 98.50 USD organization credit; the cause of the refusal is not known. Under `--bare`, Claude Code 2.1.319 offers no Grep, Glob or ToolSearch; `--tools Read,Grep,Glob,ToolSearch` leaves Read only.
- Options: credit a) load API credit and keep `--bare` b) the subscription login without `--bare`; tools a) Read only in both conditions, the prompt lists the files of the copy b) Bash in both conditions.
- Decision: credit b), against the TL recommendation a); tools a), the TL recommendation. Supersedes the isolation part of DEC-053.
- Reason: no extra spend. Read with a file list keeps both conditions equal and keeps the model inside the copy; Bash could reach the kit and the answer key.
- Consequences: the runner drops `--bare` and removes `ANTHROPIC_API_KEY` from the child environment so the login is used; it narrows what loads (`--strict-mcp-config`, `--setting-sources`, `--tools Read`) as far as the CLI allows, and the eval limits section states what still loads. `total_cost_usd` is a list-price estimate, not a bill; the runs count against the subscription's usage limits.
- Outcome:

## DEC-055 The full eval is 120 runs, one per question, model and condition
- Date: 2026-11-10 · Question: run count of the full eval after the 2026-11-09 external reviews
- Facts: the pilot ran 20 runs in about 29 minutes, 0.157 USD list price; Sonnet scored 5 of 5 in both conditions, Haiku 4 of 5 in both. 360 runs at the pilot pace take about 8.7 hours; 120 runs about 3 hours.
- Options: a) 120 runs: 30 questions x 2 models x 2 conditions x 1 repeat b) 360 runs: 3 repeats, as DEC-053 planned.
- Decision: a), the TL recommendation. Supersedes the run count of DEC-053.
- Reason: Sonnet is at the ceiling in the pilot, so repeats add time more than information; one sitting fits the usage limit better. Repeats are added only if the 120 runs show a difference between the conditions.
- Consequences: the runbook full command uses `--repeats 1`; the eval table reports one run per cell, and its limits say so. Budget 3 USD estimated (per-run cap 0.25 USD).
- Outcome: 2026-11-10, `full-1` 120 of 120, 0 errors; Sonnet 30 of 30 in both conditions, Haiku 27 and 29 of 30, the 3 Haiku server misses used Read only; no repeats added. Superseded for the gate by DEC-056 (3 runs per cell). Correction 2026-11-12 (G4 finding D-3): the time estimates in Facts (about 3 hours for 120 runs, about 8.7 hours for 360) were wrong by a factor of 14 to 15; the local run files show 13 minutes for `full-1` and 34 minutes for `full-2`. The estimate came from the 20-run pilot, which ran before T-46d.

## DEC-056 The full eval is rerun with 3 runs per cell
- Date: 2026-11-10 · Question: G4-8 and DEC-012 ask for at least 3 runs per cell; DEC-055 gave 1
- Facts: `full-1` ran 120 runs, 1 per cell (DEC-055). The TL recommended DEC-055 without checking G4-8 (`cto/2026-11-07_phase4-plan.md`) and DEC-012, which both say at least 3 runs per cell. `--resume` cannot extend `full-1` to 3 repeats: the manifest refuses a changed repeat count (T-46d).
- Options: a) a new label `full-2`: 30 questions x 2 models x 2 conditions x 3 repeats = 360 runs b) a decision that 1 run per cell meets G4-8.
- Decision: a), the TL recommendation. Supersedes the run count of DEC-055.
- Reason: b) would relax a gate criterion after the result is known. 3 repeats also answer whether the Haiku gap (27 against 29 of 30) is noise.
- Consequences: `full-2` with `--repeats 3`, budget 8 USD estimated (full-1 cost 0.867 USD for 120 runs). `full-1` stays committed as the first measurement; the eval table for G4 uses `full-2`. The runbook command is updated after the run.
- Outcome: 2026-11-11, `full-2` 360 of 360, 0 errors, 2.116 USD estimated (the run started 2026-11-10 23:44 and ended 2026-11-11 00:18, so the totals and the table header say 2026-11-10; G4 finding D-3); Sonnet 90 of 90 in both conditions; Haiku 83 of 90 with the server (per repeat 0.900 to 0.933), 87 of 90 without (0.967 in each repeat).

## DEC-057 The plugin is the one delivery path
- Date: 2026-11-11 · Question: external review 2026-11-09, item 17: plugin or copied templates as the source
- Facts: the skills already read `templates/` through `${CLAUDE_PLUGIN_ROOT}`; `/sdlc:install-hooks --refresh` replaces stale copies. The maintainer wants the kit listed as a plugin in a Claude plugin catalog, with or without downloads.
- Options: a) the plugin is the one source; copies in a project come from it and are refreshed, never edited by hand b) the templates are the source; the plugin carries only hooks and the server c) keep both as now.
- Decision: a). The maintainer asked for the easiest path to a listed plugin; the TL named a).
- Reason: a catalog listing needs a plugin and a marketplace entry; a) adds no second path to keep equal.
- Consequences: phase 5 adds the marketplace entry (review item 11) and checks the listing steps against the current Claude Code docs before T-51. `PLAYBOOK.md` stays tool-neutral; it is not a second install path.
- Outcome:

## DEC-058 Ceremony scales with the task size
- Date: 2026-11-11 · Question: external review 2026-11-09, items 24, 26, 28
- Facts: on 2026-11-11 three small record updates took three separate `scribe` calls. 34 of 54 decisions had an empty outcome field (review, HEAD 663d17d).
- Options: a) graded: an [E] task has no `.sdlc/active-contract.md` beyond the guard need, no `scribe` call and no LOG entry of its own; the TL records it in one line; audits only at phase and publish boundaries; the decision outcome field is optional; the TL shows evidence (output, file state) when it says a run stopped or a task is done b) only the evidence rule and the optional outcome field c) no change.
- Decision: a), the TL recommendation.
- Reason: [M] and [H] tasks keep the full loop, where the review rounds found defects; the [E] loop cost more than the change.
- Consequences: a task (T-47) changes `CLAUDE.md`, `PLAYBOOK.md` and the decision record template; `DEV_RULES.md` holds sub-agent rules only and does not change. The guard still needs a contract for any write by a sub-agent, so an [E] task by a sub-agent keeps a short active contract. Until that task lands, the current rules apply.
- Outcome:

## DEC-059 Narrow, publish, freeze
- Date: 2026-11-11 · Question: external review 2026-11-09, items 18, 23, 31, 33
- Facts: the plugin is installed in no other project; only the pre-push guard is used elsewhere. `full-2`: Sonnet 90 of 90 with and without the server; Haiku 83 with, 87 without (`docs/eval-results.md`). The phase plan already ends with phase 5 Release.
- Options: a) G4 closes with the 10 current tools; the server is marked experimental and optional; no new capability task is opened; after G5 the kit is frozen and changes only for a concrete need from a project that uses it; work moves to another project b) grow the server in phase 4 c) remove the server.
- Decision: a), the TL recommendation.
- Reason: the eval shows no accuracy gain from the server in this set-up; a kit nobody can install is not used. a) keeps the phase plan and adds a stop rule.
- Consequences: deferred items stay deferred (review 19b, 29); the README (T-50) calls the server experimental and optional. A new idea goes to "Not on the list".
- Outcome:

## DEC-060 The eval keeps its own runner, not `claude plugin eval`
- Date: 2026-11-11 · Question: external review 2026-11-09, item 9
- Facts: DEC-053 and DEC-054 do not name `claude plugin eval`; the two were not compared when T-46b started. The docs page "Test plugins with evals" (code.claude.com, read 2026-11-11) states: a with-plugin and a no-plugin arm; a cost estimate per case and per suite; `--max-cost-usd`; `allowed_tools` per case; a model per case, and `--model` overrides all cases; 3 runs per case per arm by default; graders regex, `tool_used`, `tool_order`, `file_exists`, `llm`, `baseline`, and no custom-code graders; the subscription login works. It does not document per-run input and output tokens, per-run duration or a per-run tool call count, or an arm that removes only the MCP server.
- Options: a) keep `tools/eval_run.py` for G4 and record why b) port the eval to `claude plugin eval` before G4.
- Decision: a). The maintainer chose to read the docs first; the TL wrote the line from them.
- Reason: DEC-012 asks for tokens, duration and tool calls per run, and for an A/B on the server alone; the docs show neither. `full-2` (360 runs) is done, and DEC-059 opens no new capability task.
- Consequences: `docs/eval-results.md` is unchanged. A port is a candidate only after G5, and only if a project that uses the kit needs it.
- Outcome: 2026-11-12, fact added after G4 finding D-4: `claude plugin eval` gives an isolated home and config per run (`docs/toolchain.md`, since 2026-10-29), and the own runner does not; the eval limits state this (T-45c). The decision stands on its 2 reasons.

## DEC-061 G4 fix round: fix S-1, live run in the customer's terminal, adopt the 10 criteria
- Date: 2026-11-11 · Question: G4 audit (`audits/2026-11-11_gate4.md`), customer questions 1 to 3
- Facts: S-1 High: `changed_outside` lets git start a program from a git config in 2 layouts (a nested repository; a root laid out as a git folder), reproduced in scratch; `docs/security.md` says 0 open High. G4-4 asks for a call in a terminal the customer opened; the eval loaded the server with `--mcp-config`, not as a plugin. G4-1 to G4-10 stand only in `cto/2026-11-07_phase4-plan.md` (finding P-3).
- Options: S-1 a) fix with tests b) accept the risk in a decision; G4-4 a) one short Haiku run in the customer's terminal after the fix, with the customer's statement b) a decision that the eval runs suffice; criteria a) adopt all 10 as written b) name the ones that do not bind.
- Decision: a), a), a), the TL recommendations.
- Reason: a public kit with an open High contradicts its own security note; the plugin path is the one delivery path (DEC-057), so it is the one to check live; the audit already used the 10 criteria.
- Consequences: T-45a fixes S-1 and updates the S-3 and S-4 rows. The live run follows T-45a, as G3-7 was recorded. The other conditions (P-1, P-2, S-2) and the Low findings go to a second fix task. Then `auditor-mini` re-verifies.
- Outcome: 2026-11-12, T-45a fixed S-1 (4854cbd). The customer ran the plugin-loaded server in their own terminal on CLI 2.1.319 and confirmed the run; the `status` call returned the open task (`docs/toolchain.md`). Re-verification pending.

## DEC-062 Server token cost for G4-10: measured live, with and without the server
- Date: 2026-11-12 · Question: G4 audit finding P-2
- Facts: G4-10 asks for the tokens the server adds per session from `claude plugin details`; on CLI 2.1.319 that command prints the MCP server as "tool schemas resolved at runtime; not counted" and the same about 1,031 tokens as before the server. The 10 tool definitions are 4,149 characters, 5,173 with output schemas; at 4 characters per token, an estimate, about 1,000 to 1,300 tokens.
- Options: a) one live run with the plugin-loaded server and one without, in the customer's terminal, compare the input tokens of the first turn b) report the definition size only, as an estimate.
- Decision: a), the TL recommendation.
- Reason: the criterion asks for a reported number, and the command it names cannot give it; an estimate from characters is not a measure.
- Consequences: the run pair joins the G4-4 live run in the customer's terminal (DEC-061). `docs/toolchain.md` gets one paragraph: what `plugin details` counts and does not count, the definition size, and the 2 first-turn numbers. The G4-10 wording names the first-turn measure; the change is recorded here, not made silently.
- Outcome: 2026-11-12, one pair in the customer's terminal on CLI 2.1.319: first-turn context 43,461 tokens with the server, 43,240 without, 221 added on the plugin path, where the tools are deferred (`docs/toolchain.md`). The direct-listing cost stays an estimate.

## DEC-063 Evidence from a non-game project before G5
- Date: 2026-11-14 · Question: TL review before phase 5
- Facts: `EVIDENCE.md` counts Project A, Project B and the kit; Project A and Project B are both game projects. The one real task in a foreign project (T-33, G3-5) ran on Project A. The eval (`docs/eval-results.md`) uses one synthetic repository. No run of the kit on a project that is not a game is recorded.
- Options: a) before G5, one real task with the kit on a project that is not a game; collect evidence only; no kit code change b) state the limit in the README and leave the trial to a later version.
- Decision: a). The TL recommended b); the maintainer chose a), as evidence collection, not software development.
- Reason: a reader can read evidence from 2 game projects as "a kit for games". The kit has no game-specific code or rule, but no record shows it working elsewhere.
- Consequences: phase 5 gets T-53, before T-52. T-53 records what T-33 recorded: footprint, guard events, the per-task metric line, rollback. The results go to a dogfood document and, where a metric applies, to `evidence/` through `tools/metrics`. A kit defect found in T-53 is a finding; it is fixed before G5 only if it blocks install or use, otherwise it goes to v0.1.1. The target project is chosen when T-53 opens. The README (T-50) names the project types the evidence comes from, with or without T-53.
- Outcome:

## DEC-064 The kit introduces itself through a session start hook
- Date: 2026-11-14 · Question: `cto/2026-11-14_phase5-plan.md` Q1; T-33 finding 3
- Facts: no file in `skills/`, `templates/` or `hooks/` states the TL seat or the task loop; the text is only in this repository's `CLAUDE.md`. In T-33 the Project A TL session did not know the kit and planned to write the contract by hand.
- Options: a) a SessionStart hook that adds a short seat text only where `.sdlc/project.md` exists b) `/sdlc:init` appends a section to the project's `CLAUDE.md` c) a typed `/sdlc:lead` command.
- Decision: a), the CTO and TL recommendation.
- Reason: automatic, writes no user file, silent in projects that did not opt in, testable. c) depends on the user remembering, which failed in T-33.
- Consequences: T-49 first in phase 5. One probe first: whether a plugin SessionStart hook adds context on the current CLI. The seat text is one template file; it includes the plan budget (T-33 finding 9). Its token cost per session is measured as in DEC-062. T-53 and the bench run after T-49.
- Outcome:

## DEC-065 Kit against plain prompt: 2 arms, 36 runs
- Date: 2026-11-14 · Question: `cto/2026-11-14_phase5-plan.md` Q2
- Facts: no record measures whether the kit gives better work than a plain prompt (`EVIDENCE.md`, `docs/eval-results.md`). CTO estimate, not measured: 3 arms x 6 tasks x 3 repeats = 54 runs, about 52 USD and 9 hours; 2 arms = 36 runs, about 36 USD and 6 hours. The last estimate of this kind was off by a factor of 14 to 15 (DEC-055).
- Options: a) 3 arms: plain, one agent with the kit's rules, full kit; 54 runs b) 2 arms: plain and full kit; 36 runs c) 2 arms, 4 tasks, 24 runs.
- Decision: b). The CTO recommended a).
- Reason: the maintainer's choice; b) answers the question asked, plain prompt against the kit, at about two thirds of the cost.
- Consequences: a sandbox project and 6 tasks with hidden acceptance tests in `bench/` (T-55), a runner reusing `tools/eval_run.py` (T-56), a pilot that sets the budget, then a pre-registration record before the first scored run. If the kit wins, the result cannot say whether the process or the extra agents and tokens carry the gain; the README states this limit.
- Outcome:

## DEC-066 The bench uses Sonnet in every role
- Date: 2026-11-14 · Question: `cto/2026-11-14_phase5-plan.md` Q3
- Facts: the kit as shipped runs an Opus TL, a Sonnet developer and a Haiku scribe. A plain Sonnet prompt against that mix compares models as well as process.
- Options: a) Sonnet in every role in both arms b) a) plus the same arms on Haiku c) the kit as shipped against plain Opus and plain Sonnet.
- Decision: a), the CTO and TL recommendation.
- Reason: same model in each pair, so a difference comes from the process; cost stays in the DEC-065 range.
- Consequences: the README says the bench ran on Sonnet only and is not the kit's default model mix. The Haiku server gap is tested apart (T-54).
- Outcome:

## DEC-067 Project C for T-53
- Date: 2026-11-17 · Question: T-53 target project (DEC-063); cited in `TASKS.md` since 2026-11-14, written 2026-11-17
- Facts: two non-game projects of the customer were read, nothing written. Candidate 1: Python, local server and browser interface, about 320 tests, under active development, its own Turkish TL process, the kit's pre-push guard installed; browser-side code has no tests. Candidate 2: TypeScript and React, 528 fast tests, idle since 2026-11-11, records in English, a hand copy of the kit's process with 6 role files named like the plugin's agents. The TL recommended candidate 2 (idle, clean tree, a stack new to the evidence). The customer has 3 real tasks lined up in candidate 1.
- Options: a) candidate 1, the customer's 3 real tasks b) candidate 2, one task from its review backlog c) defer T-53 to v0.1.1 and state the limit.
- Decision: a), the customer's choice. The TL recommendation was b), then a) once the customer had 3 tasks lined up, since the work happens anyway.
- Reason: real work the customer does anyway; the added cost is the before and after notes and the rollback.
- Consequences: Project C is candidate 1; its name stays out of the repository (DEC-006; private pattern added). T-53 widens from 1 task to up to 3, each recorded on its own. The customer's conditions: nothing in Project C may break, nothing is pushed from Project C during the trial, and the trial starts only on the customer's go. Its browser code has no tests, so part of each result rests on the customer's own check; stated as a limit. Project C already runs a TL process of the same author; the trial shows the plugin installed over that process, not the kit in a project without one; stated as a limit.
- Outcome:

## DEC-068 Fix the guard's deny for the main session before the bench
- Date: 2026-11-14 · Question: T-56a probe result
- Facts: in 3 kit probe runs of bench task B1 (Sonnet, headless, go-ahead given) no run started a sub-agent; the main session edited code itself. The guard denied the edit with no contract in place. K2 and K3 stopped after that one deny, 2 of 7 hidden tests; K1 wrote the contract by hand, it parsed as broken 3 times, then passed, 7 of 7. The deny text tells the main session to "ask the technical lead", but the main session is the technical lead, and it names neither `/sdlc:contract` nor the contract format (`tools/scope_guard.py` lines 455 and 465). The plain run passed 7 of 7.
- Options: a) fix before the bench: a main-session deny names `/sdlc:contract` and the minimal contract format; the seat text says that with a go-ahead given the TL places the contract and hands the work to `developer` b) measure the kit as it is c) a kit-arm prompt that tells it to delegate.
- Decision: a), the TL recommendation.
- Reason: b) would measure a known message defect, not the method; c) gives the two arms different text.
- Consequences: T-58 before T-56b. The fix is general, not tuned to B1; the bench limits state that the defect was found by a probe. The 4 probe runs stay excluded from scoring. The sub-agent questions of T-56a stay open until a probe starts a sub-agent.
- Outcome:

## DEC-069 The bench kit arm gets the server through `--mcp-config`
- Date: 2026-11-15 · Question: T-56b smoke run `smoke-1`
- Facts: under `--strict-mcp-config` the kit arm's init event listed no MCP server: the plugin loaded (agents, hooks, guard events) but its `sdlc` server and the 10 `mcp__plugin_sdlc_sdlc__*` tools were missing. Without the flag the 4 account connectors load in that arm only (V-21).
- Options: a) keep `--strict-mcp-config` in both arms and define the server for the kit arm in a `--mcp-config` file, as the server eval did b) drop the flag in the kit arm.
- Decision: a), the TL and developer recommendation.
- Reason: both arms stay isolated; the only difference between them is the kit.
- Consequences: in the kit arm the server starts from the extracted kit's `server/main.py` with the run copy as project root, and its tools are named `mcp__sdlc__*`, not as the installed plugin names them. The bench limits state that the server was not started through `plugin.json`.
- Outcome:

## DEC-070 Large bench task B7, reported apart from the 6-task category
- Date: 2026-11-15 · Question: `cto/2026-11-15_bench-large-task.md` Q1, Q2; T-59
- Facts: the customer asked for a task the size of rebuilding a whole page or screen. Proposed after `smoke-2` (B1, 1 run per arm: plain 0.038 USD, 11 s; kit 0.305 USD, 115 s; both 7/7). Plain cost on B1 varied 5.5 times across 2 runs (V-19, `smoke-2`); kit to plain ratio 1.7 in one pair, 8 in the other. 0 scored runs; set v1 frozen.
- Options: a) B7 in the same sandbox, reported apart; category on B1 to B6 b) category on 7 tasks c) no large task. Form: a) rebuild of the CLI output layer in the same sandbox b) a second sandbox with an HTML page c) both.
- Decision: a) and a), the CTO recommendation.
- Reason: the addition follows a result that looked bad for the kit, so it must not move the headline. A CLI screen is printed text, which hidden tests can pin byte for byte; a page sandbox costs a second project and a runner change and tests still cannot judge its look. The real page work is in T-53.
- Consequences: set v2 with a new hash; B7 frozen before any model run on it; pre-registered reading H5 (B7 full passes per arm out of 3; cost ratio on B7 against the E tasks; no threshold); the pre-registration states the motive and both hashes; B7 is published whatever its result. A pilot result on B7 changes neither the task nor the kit.
- Outcome:

## DEC-071 B7 scoring: machine primary, blind review secondary
- Date: 2026-11-15 · Question: `cto/2026-11-15_bench-large-task.md` Q3
- Facts: hidden tests can judge printed text, JSON and CSV structure, exit codes and file bytes; they cannot judge module structure, duplication or readability. Every task allows `tests/*`, so an arm can change visible tests.
- Options: a) machine scoring plus the customer's blind review of the 3 B7 diff pairs, reported apart b) machine only c) blind review of all 21 pairs.
- Decision: a), the CTO recommendation.
- Reason: adds a view of design for the one task where design is the point, at about 3 pairs of the customer's time; it cannot change H1 or H5.
- Consequences: `scout` strips `.sdlc/` and the kit record files, names each pair X and Y in a seeded order and keeps the key outside the repository; a fixed form: which one would you merge, and one line why. B7's hidden tests repeat the key visible checks. n = 1 reviewer who knows the kit; the blinding is partial; stated as a limit.
- Outcome:

## DEC-072 Bench count: 7 tasks, 3 repeats, 42 runs
- Date: 2026-11-15 · Question: `cto/2026-11-15_bench-large-task.md` Q4; amends DEC-065
- Facts: DEC-065 planned 2 arms x 6 tasks x 3 repeats = 36 runs. The runner has one per-run cap and timeout for all tasks (2 USD, 2,700 s), and `--resume` refuses changed flags. `bench/README.md` shows `--repeats 2` in its example.
- Options: a) 1 large task, 3 repeats, 42 runs, B7 caps from a pilot b) 2 large tasks, 48 runs c) B7 with 1 repeat, 38 runs.
- Decision: a), the CTO recommendation.
- Reason: 3 repeats as DEC-012 and DEC-065; 1 run per arm would repeat the smoke problem; a second large task changes the mix for one more sample.
- Consequences: mix 2 E, 3 M, 2 H. B1 to B6 run under one label with the current caps, B7 under its own label with caps from the pilot (per-run cap 3 times the pilot kit cost, timeout the larger of 2,700 s and 3 times the pilot time; the factor 3 is opinion). Pilot: B7 and B3, 2 arms, 1 run each, not scored. The pre-registration names the exact commands; the README example is corrected to 3 repeats.
- Outcome:

## DEC-073 The seat text carries the graded ceremony before the first scored run
- Date: 2026-11-15 · Question: `cto/2026-11-15_bench-large-task.md` Q5; `smoke-2`
- Facts: `templates/seat.md` (16 lines) has no line on task size; DEC-058 is in `PLAYBOOK.md` and this repository's `CLAUDE.md` only. In `smoke-2` the kit started `sdlc:developer` 2 times and had 3 guard denies for a one-line fix; the sub-agent started before the main session's contract parsed.
- Options: a) add 1 seat line that delivers DEC-058, read the `smoke-2` stream for the early-start deny and fix it only if its cause is general, 1 check run of B1 (excluded), then freeze the kit b) measure as shipped and state the gap as a limit.
- Decision: a), the CTO recommendation.
- Reason: DEC-058 was decided on 2026-11-11; b) would measure a seat that v0.1.0 does not ship. Expected effect is small (CTO opinion): the overhead comes from delegation and the sequencing fault, and DEC-066 keeps every role on Sonnet.
- Consequences: T-59b before the pilot. It is the second change after a result was seen (after DEC-068); the pre-registration states both. After the check run the kit does not change before the full run except for harness errors.
- Outcome:

## DEC-074 T-53 run setup on Project C
- Date: 2026-11-17 · Question: how T-53 runs inside Project C's existing process (DEC-067)
- Facts: Project C's rules commit and push when the customer approves a task, unless the customer says not to push; DEC-067 forbids pushes during the trial. Project C's TL delegates to its own developer role; the plugin adds its own. Project C's 3 tasks have no explicit file list, and a version bump there changes `pyproject.toml` and `uv.lock`. The kit's chained pre-push guard is already installed in Project C. The third task has an open shortcut question in Project C.
- Options: push a) none until the trial ends, through Project C's own "no push" word b) per task, changing DEC-067; developer c) Project C's own role d) the plugin's role; shortcut question e) when its task comes f) now.
- Decision: a), c), e), the TL recommendation, the customer's word.
- Reason: a) keeps DEC-067 without changing Project C's rules; c) measures the plugin over the process as it runs, the case DEC-067 names; the guard covers any sub-agent. e) does not block the first two tasks.
- Consequences: commits stay local on main, one push at the end; no branch needed. Each contract names every path, incl. `pyproject.toml` and `uv.lock`. `/sdlc:install-hooks` is skipped. The trial measures Project C's developer role, not `sdlc:developer`; stated as a limit.
- Outcome:

## DEC-075 Shell writes the scope guard does not see
- Date: 2026-11-18 · Question: what v0.1.0 does about the shell-write gap found in T-53 (`docs/dogfood-2.md` finding 1)
- Facts: the guard checks Edit and Write calls only. In T-53 it saw 1 of 23 developer-written files; a history scan found shell-write candidates in 39 of 50 of this kit's own developer runs. The kit is frozen at f148c73 for the bench; a guard change before the full run changes the measured kit.
- Options: a) state it as a limit in v0.1.0, fix in v0.1.1 b) fix before the bench full run.
- Decision: a), the TL recommendation, the customer's word.
- Reason: b) needs a new freeze and a new pilot; a) keeps the bench valid and says the limit where users read it.
- Consequences: T-50 README names the gap under limits, with the T-53 numbers. A v0.1.1 task covers shell writes (a Bash write check or a worktree check at review).
- Outcome:

## DEC-076 Plugin user without the MCP SDK
- Date: 2026-11-18 · Question: CTO Q5, DEC-051 options b) and c): what happens when the plugin starts the server and the `mcp` package is missing
- Facts: today a missing or out-of-range `mcp` package stops the server with one install line (DEC-051); the server is experimental and optional (DEC-059).
- Options: a) the server exits quietly and shows one install line; the rest of the plugin works b) the release ships without the server.
- Decision: a), the TL recommendation, the customer's word.
- Reason: the guard, skills and roles need no SDK; b) drops a tested part.
- Consequences: T-51 checks that a session without the SDK shows no failing server beyond the one line, and the README says how to install it.
- Outcome:

## DEC-077 No internal IDs in public-facing text
- Date: 2026-11-18 · Question: where task, decision and bench IDs (T-nn, DEC-nnn, Bn) may appear
- Facts: the customer finds the IDs hard to follow in conversation and in reading; the records use them for tracing.
- Options: a) none in conversation and in public-facing text (`README.md`, `PLAYBOOK.md`, `EVIDENCE.md`, `docs/`); records keep them b) none anywhere in the repository c) conversation only.
- Decision: a), the TL recommendation, the customer's word. The customer also chose to publish after the bench full run, as the finish plan says.
- Reason: a reader of the public text needs words, not IDs; the records need the IDs to trace decisions; b) rewrites hundreds of record lines.
- Consequences: T-50 rewrites the public-facing text in words, an ID only where a reader must find the record, in parentheses. Briefs to `tech-writer` say so.
- Outcome:

## DEC-078 Bench pre-registration (before the first scored run)
- Date: 2026-11-18 · Question: the rule, commands and caps of the bench full run (CTO plan 3.6, `cto/2026-11-15_bench-large-task.md`, DEC-065, DEC-070 to DEC-072)
- Fixed before any scored run: bench set v3 (`e7f25782...2b4b`; v2 was `6b5154df...8a3e`); kit paths unchanged since f148c73 (`git diff f148c73 HEAD` on `.claude-plugin agents skills hooks server templates` empty); 2 arms, plain and kit, Sonnet in every role (DEC-066); seed 0. Changes after a result was seen: DEC-068 (guard deny text) and DEC-073 (seat size line), both before this record. B7 was written and frozen before any model run on it. The pilot set only B7's caps; it changed no task and no kit file.
- Pilot (not scored, labels `pilot-b3`, `pilot-b7`): B3 plain 23 of 23, 47 s, 0.19 USD; kit 23 of 23, 88 s, 0.40 USD. B7 plain 47 of 47, 122 s, 0.32 USD; kit 47 of 47, 259 s, 0.68 USD.
- B7 caps (DEC-072 rule): per-run cap 3 x 0.68 = 2.1 USD; timeout the larger of 2,700 s and 3 x 259 s = 2,700 s; max turns 60.
- Commands, kit folder, customer's terminal: `python tools/bench_run.py --label full-1 --tasks B1,B2,B3,B4,B5,B6 --repeats 3 --budget-usd 40` and `python tools/bench_run.py --label full-1-b7 --tasks B7 --repeats 3 --budget-usd 15 --max-run-usd 2.1`. The two labels may run at the same time in 2 windows; wall time is then a limit, as in T-54c.
- H1, primary, B1 to B6: full passes kit against plain, out of 18 runs each. Kit better: kit minus plain is 3 or more and the kit has no more regressions. No difference: within 2. Plain better: plain minus kit is 3 or more. The README uses the wording of CTO plan 3.6 for the category that comes out; the kit claims better work only in the first case.
- H2: cost ratio kit to plain in USD, tokens and wall time, reported, no threshold. H3: out-of-scope files and visible test changes per arm, reported. H5, B7 apart: full passes out of 3 per arm, and the cost ratio on B7 against the ratio on the easy tasks (B1, B2), no threshold; B7 is reported whatever happens, including "kit failed by cap"; the tables of B1 to B6 and B7 are not merged.
- Scoring: machine only for H1 to H5 (CTO Q4 a). Secondary, B7 only (DEC-071): the customer's blind review of 3 diff pairs, form "which would you merge: X, Y, either, neither" plus one line why; reported apart, cannot change H1 or H5.
- Stop rule: the runner stops at the budget; cells done are reported as they are; no runs added after results are seen; only harness errors (timeout, crash, no result, usage limit, API error, server not connected) are rerun with `--resume --rerun-errors`, and counted. No task is dropped. The result is published in whichever category it falls. After G5 the bench is not rerun to change a published category (DEC-059).
- Outcome:

## DEC-079 B7 blind review not done
- Date: 2026-11-19 · Question: the secondary blind review of the 3 B7 diff pairs (DEC-071, DEC-078) before publishing
- Facts: the pairs were prepared blind in the local, ignored folder; the review needs 30 to 45 minutes of the customer's time; it cannot change H1 or H5.
- Options: a) close it as not done and say so on the results page b) do it before G5.
- Decision: a), the customer's word.
- Reason: it is secondary and descriptive (n = 1 judge, 3 pairs); the publish plan has no slot for it.
- Consequences: `docs/bench-results.md` says the review was not done and will not be done for this bench; the local pairs may stay or be deleted.
- Outcome:

## DEC-080 Public history and the G5 privacy points
- Date: 2026-11-20 · Question: G5-F1 and G5-F2 of `audits/2026-11-20_gate5.md`: review item 32 (public history), N-5, the 3 privacy points (LOG 2026-11-19 (3)); and G5-F6, G5-F7 (limit or fix before v0.1.0).
- Facts: 80 commits, 0 pattern hits public and private. The history holds 5 line groups the tree dropped, none a secret or a name; 1 names an intended reader group of the personal-goal kind. 55 of 80 commits are cited by hash in 38 tracked files; the bench registration rests on c99c9fe. The repositories of Project A, B, C and the unchosen candidate are private on the account (checked 2026-11-20).
- Options: a) publish the 80 commits as they are, with this record b) 1 squashed commit c) rewrite the 2 early commits.
- Decision: a), the customer's word. N-5, `audits/2026-11-02_gate1.md` line 127 and the source hashes in `evidence/` stay as they are; the account amounts in `DECISIONS.md` and `LOG.md` stay. G5-F6 and G5-F7: limit lines in v0.1.0, fixes in v0.1.1. G5 criteria are G5-1 to G5-9 of `cto/2026-11-14_phase5-plan.md` section 6.
- Reason: a squash breaks 55 hash citations and the check that the registration came before the scored runs; no group is a secret or identifies a project or person. Fixing the guard and skills now would ship a kit that differs from the measured one.
- Consequences: the 5 groups of G5-F1 are public with the history. Making Project A, B or C public later ends its label's anonymity (hashes in `evidence/`, descriptions in DEC-067 and `docs/dogfood-2.md`). The personal-goal rule has this one recorded exception, in history only.
- Outcome:

## DEC-081 Phase 5 closed, project frozen at v0.1.0
- Date: 2026-11-21 · Question: is the planned work done, and what happens to the open items.
- Facts: G5-1 to G5-9 met (G5-6 with a limit); `v0.1.0` tagged on 6eda269; repository public 2026-11-21 with the audit's GitHub settings read back; no open task in `TASKS.md`; open items are Low findings, the T-53 findings, R-1 and G5-F6, G5-F7 (limit lines in v0.1.0).
- Options: a) close phase 5 and freeze; open items wait for a v0.1.1 triage in phase 6 b) keep phase 5 open until v0.1.1.
- Decision: a), the customer's word.
- Reason: the finish plan is done; no open item blocks a user of v0.1.0, each is stated as a limit or listed for triage.
- Consequences: phase 6 (ongoing, no gate) starts with no task planned; a v0.1.1 starts only with a triage session and the customer's go-ahead.
- Outcome:
