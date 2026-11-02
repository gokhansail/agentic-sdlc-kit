# Playbook

What is this file? The method behind this kit, written so that it does not depend on one tool. The core is one page. The appendices give the detail. Each paragraph, list item and table row ends with source map IDs in brackets, for example [C-06]. A C-ID points to a row of `docs/source-map.md`. A DEC-ID points to `DECISIONS.md`. This file holds no measured numbers. Measured numbers will be in a separate evidence report (phase 2).

## Core

### What the method is

Several AI agents do software work, each in one role. The customer, a person, sets taste and scope. The technical lead (TL) turns work into written contracts, hands them to other agents and reviews every diff. The developer executes one contract at a time. An independent auditor judges the work at each gate. [C-01]

Three rules hold it together. Each document has one writing role. Whoever wrote or ran the work cannot pass its gate. No change starts without the customer's go-ahead. [C-05, C-11, C-41]

### Scope and limits

It sets who writes, who reviews and what is recorded, so the work can move to another model through files. [C-05, C-15]

The evidence is one person on two projects. Results are descriptive. The process and the person changed at the same time, so the method makes no causal claim and no claim of speed or quality. [DEC-010]

### Roles

There are nine roles: customer, TL, CTO, developer, tech-writer, scout, scribe, auditor and auditor-mini. Only the TL calls other agents. A sub-agent cannot ask the customer or start another sub-agent. It returns with a question. The CTO gives options and writes reports. The tech-writer writes and revises English documents from the TL's brief, in two rounds at most, and adds no claim of its own. The scout searches and counts. The scribe writes the log and the status. The auditor gives gate verdicts. The auditor-mini re-checks named findings. Appendix A has the matrix. [C-02, C-03, C-33, C-34, C-35, C-36, C-37, DEC-009]

### Task loop

The loop has eight steps: status, questions, contract, dispatch, implementation, diff review, records, customer test and commit. The TL asks all open questions in one message, recommendation first. A contract has fixed fields and at most 15 lines. A larger one is split. The customer's go-ahead covers that one task. Diff review has at most 2 rounds. A sub-agent report is a claim, so the TL checks the diff and the test output before saying done. The TL commits and pushes only after the customer approves. [C-06, C-07, C-08, C-39, C-53]

### Phase loop and gates

The TL stops the work at a gate. The customer gives the criterion. The auditor gives the verdict: accept, conditional or reject. The developer fixes. The auditor-mini marks each finding CLOSED, OPEN or PARTIAL, with evidence. The CTO then proposes the next agenda. While a gate is open, the next phase waits. [C-10, C-11, C-12]

### Records

The TL writes the task, decision and lesson records. The scribe writes the log and the status. Documents are kept current, and a changing fact lives in one place. Each task records review rounds, returned questions, the customer's test result and files changed outside the contract. [C-02, C-22, C-28, C-35]

## Appendix A. Roles and authority matrix

| Role | Duties and limits | Source |
|---|---|---|
| Customer | Sets taste and scope. Gives the gate criterion. Tests the product and approves. | [C-01, C-10, C-60] |
| TL | Writes contracts, dispatches, reviews diffs. Writes task, decision and lesson records. Commits and pushes after approval. Does not open code files. | [C-01, C-02, C-18, C-39] |
| CTO | Gives options with the recommendation first. Writes a report only. Writes no code and makes no decision. | [C-33] |
| Developer | Implements one contract. Asks instead of guessing. Never commits. Returns a fixed report. Reads only its contract and the developer rules. | [C-02, C-18, C-32] |
| Tech-writer | Writes and revises English documents from the TL's brief. Two rounds at most. Adds no claim of its own. | [DEC-009] |
| Scout | Reads only. Returns file and line references and numbers. | [C-34] |
| Scribe | Writes the log, the status and the changelog check. Never writes decisions or contracts. | [C-35] |
| Auditor | Runs a full audit with evidence and severity. Ends with a verdict line. Fixes nothing. | [C-36] |
| Auditor-mini | Checks named findings as CLOSED, OPEN or PARTIAL. Starts no new review. | [C-37] |

Who holds each authority:

| Authority | Holder | Source |
|---|---|---|
| Scope and taste | Customer | [C-01, C-04] |
| Gate criterion | Customer | [C-04, C-10] |
| Gate verdict | Auditor | [C-04, C-11] |
| What follows the verdict | Customer | [C-01, C-04] |
| Contracts and dispatch | TL | [C-01, C-02] |
| Task, decision and lesson records | TL | [C-02] |
| Proposes the next agenda after a gate | CTO; the customer decides | [C-10, C-33, C-01] |
| Commit and push | TL, after approval. The developer never commits. | [C-02, C-39] |

Each document has one writing role. Other roles suggest changes. One writer works on a set of files at a time. Read-only roles and record roles may run in parallel. [C-05]

Models are chosen by tier. A small model does search and records. A mid model does development. A high model serves the TL and the CTO. The top model does the final audit. [C-19]

The TL decides whether the scout, the TL or the CTO analyses a side request. [C-14]

## Appendix B. The eight-step task loop

1. Status. The TL states where the work stands. Before trusting a status record, check the working tree (lesson in appendix G). [C-06, C-49]
2. Questions. All open questions go in one message, with options and the recommendation first. An unanswered question gets no default. [C-07]
3. Contract. Fields: a one-line goal, files in and out, observable acceptance, tests, design reference, flag, customer test. At most 15 lines. A longer contract is split. The go-ahead is the permission for that one task. [C-08, C-40]
4. Dispatch. Only the TL dispatches. The developer reads only its contract and the developer rules. [C-02, C-18]
5. Implementation. At an unclear point the developer stops and returns a question. The TL answers or asks the customer, then continues the same agent. A new call starts blank. [C-09, C-54]
6. Diff review. At most 2 rounds. The sub-agent report is a claim. The TL checks the diff and the test output before saying done. [C-06, C-53]
7. Records. The TL updates the records. A stale line is fixed before work starts. After each task the TL asks whether the lesson applies elsewhere. [C-06, C-28, C-29]
8. Customer test, then commit. Automatic tests run before "done". "0 build errors" is not proof. The customer judges behaviour. After approval the TL commits and pushes. One version is one commit. Untested work is not pushed. [C-06, C-30, C-39]

Scope overflow returns as a question. [C-41]

The TL session is cleared only after the records are written and approved. The trigger is 3 to 5 tasks or one large read. Sub-agents start fresh for each task. [C-17]

## Appendix C. Phase loop and gate

1. The TL stops at a gate. [C-10]
2. The customer gives the criterion. [C-10]
3. The auditor judges and gives a verdict line: accept, conditional or reject. Finding IDs carry a type prefix: process, design, code, role, or security and privacy. [C-11, C-44, DEC-020]
4. The developer fixes. The auditor-mini re-verifies each finding as CLOSED, OPEN or PARTIAL, with evidence. The trigger is a state, not a date. [C-12]
5. The CTO proposes the next agenda. [C-10, C-33]

While a gate is open, the next phase waits. [C-10, C-41]

How an audit is run: read documents, code, version history and logs. Check every claim. Count what can be counted. Put evidence first. Never close your own finding. [C-42]

Severity runs critical, high, medium, low, by threat and recurring cost. [C-43]

The re-verify table has the columns finding, claim, evidence and status, followed by the gate verdict. [C-45]

Audits run at gates and after fix rounds, never on a fixed rhythm. [C-57]

Before a public endpoint is deployed, a second reviewer reads it as an attacker. [C-27]

## Appendix D. Flexibility and the impact note

The customer may change direction at any time. The TL writes a one-line impact note, warns, acts if the customer insists, and records it in the log. This also holds when a gate is open. [C-10, C-13]

A go-ahead covers the task it was given for. [C-08]

## Appendix E. Flag rule

A change to behaviour the customer judges by using the product, or a change to cost, ships behind a toggle. The old state then returns in one step. [C-31]

The machine tests correctness. The customer judges behaviour. [C-30]

Before a push, the test flag is off. [C-38]

## Appendix F. Per-task metrics

Each task records four things: review rounds, whether a question came back, the customer's test result, and whether a file outside the contract changed. Many returned questions point at the contract, not at the developer. [C-22]

Tasks carry a size label: easy, medium or hard. The label sets effort, the amount of thinking a model spends on its output. If hard tasks pass 30% of all tasks, the contracts are too big and are split. [C-20, C-52]

If usage regularly passes 80% of the window, lower developer effort first, then TL contract writing. Review is never lowered. [C-21]

Logs are counted by script. The model gets totals, not raw logs. [C-58]

## Appendix G. Decision and lesson records

Decisions come before tasks. [C-41]

A lesson entry has a date, a project label, the problem, the cause, the fix and the lesson. A lesson is recorded when the customer steered the fix. Problems the agent found and fixed alone are not logged. [C-48, C-61]

Standing rules for records and commits:
- Several tasks from one request ship as one version. The changelog lists each item. [C-23]
- Only the current version is tested. Each reply states the version and whether code was written. [C-24]
- No addresses, keys, tokens or personal data in a repository or a commit message. Values live in ignored local files. A leaked value counts as burned. [C-25]
- An approved change is committed. At most one approved step stays uncommitted. [C-59]

The six lessons that came from the source projects: [C-49, C-50, C-51, C-62, C-63, C-64]

1. Status record against working tree. A status record said "awaiting approval" while the working tree held code nobody had reviewed. Rule: check the working tree before trusting a status record. [C-49]
2. Rules on paper. A rule existed that nobody checked. An outside reviewer exposed the gap. Rule: a rule is either enforced or deleted. [C-50]
3. Version ambiguity. An agent asked which version was being tested. Rule: state the current version from the files. [C-51]
4. A "why" question. A rule made the customer switch folders, which went against the principle of the rule. The CTO then became a sub-agent. Rules: when the customer asks why, test the rule against its principle. Re-measure the data a finding rests on before acting on it. [C-62]
5. Stale document line. A fact that changes fast was kept by hand in several files. It stayed stale while a fix waited for permission. Rules: keep the fact in one place. Fix a stale line without asking. [C-63]
6. Unasked testing. The word "start" was stretched into "start and verify". Rule: do the asked action, say what to check, and leave the test to the customer. [C-60, C-64]

## Appendix H. Concept and mechanics

The concepts are tool-neutral: the contract, the single writer and the gate by an independent reviewer. The mechanics below are how the source projects implemented them, with Claude Code. This repository follows the same pattern; see `CLAUDE.md`. [C-55, CLAUDE.md]

Code and documents may reach a second model provider. User data, personal data and keys may not. [C-16]

| Concept | Mechanics in the source projects | Source |
|---|---|---|
| Contract as handover | A task file. A sub-agent receives it in its prompt. A backup developer on another profile reads it from the task file and writes its report under the task. | [C-08, C-15, C-55] |
| Single writer | One role file per role, with the owned files, model and effort set in it. | [C-03, C-05, C-20] |
| Gate by an independent reviewer | The auditor runs as a sub-agent on the top-tier model. | [C-11, C-19, C-36] |
| Narrow reading for the developer | A rules file of at most 40 lines. The source projects enforce the test flag and the private-data rule with a pre-push hook. The standard calls for hooks to enforce the developer rules as well. | [C-18, C-46, C-47, C-56] |
| No test flag in pushed work | A local pre-push guard. It checks committed content, not the working copy. | [C-46] |
| No private data in pushed work | The same guard scans added lines and commit messages for link patterns, a known key and private paths. It reports the location, never the match. | [C-47] |
| Data boundary | Keys stay in a local launcher or the environment. Reads of secret files are denied in settings. | [C-16] |
| Provider | A sub-agent runs on the main session's provider. Another provider is a separate profile, not a sub-agent. | [C-55] |
| Counts | Scripts count the logs. The model reads the totals. | [C-58] |

## Appendix I. Why the method is not specific to Claude Code

This repository is built and run with Claude Code. The kit's server will be tested with Claude Code only. [DEC-011]

The method itself sits in files and rules about who may write them. The contract is a file. The handover is a file, so a backup developer on another model can read the contract and the developer rules and do the same work. [C-05, C-08, C-15]

The guard is a git hook, so it runs whatever editor or agent made the commit. [C-46, C-47]

The parts to rebuild in another tool are the role files, the hooks and the effort settings in appendix H. [C-20, C-56]
