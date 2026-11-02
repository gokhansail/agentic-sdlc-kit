# Source map

What is this file? The list of concepts the playbook, templates and role files may use, each traced to a section of a source document. The source files are private, so they appear here as IDs (DEC-016). The ID-to-file index is kept on the maintainer's machine and is not committed. Gate G1 checks every playbook claim against a row in table 2. All process lessons in the lessons log are listed (DEC-017).

## 1. Sources

| ID | Description | Language |
|---|---|---|
| S-01 | Agent working standard | Turkish |
| S-02 | Cross-project rules | Turkish |
| S-03 | Lessons log | Turkish |
| S-04 | Role files (six: CTO, developer, scout, scribe, auditor, auditor-mini) | Turkish |
| S-05 | Project A work rules | Turkish |
| S-06 | Project A task file | Turkish |
| S-07 | Project A audit folder guide | English |
| S-08 | Project A pre-push hook | Shell |
| S-09 | Project B pre-push hook | Shell |

Targets: T-11 playbook, T-12 templates, T-13 role files and portability notes.

## 2. Concepts

| C-ID | Concept | Source | Target | Summary |
|---|---|---|---|---|
| C-01 | Core sentence and division of labour | S-01 §6.0 | T-11 | The customer sets taste and scope. The TL turns work into contracts, dispatches and reviews diffs. The developer executes. The auditor gives the gate verdict. |
| C-02 | Session equals role (seat rule) | S-01 §6.1 table and the two limits below it; S-02 rule 25 | T-11, T-13 | A session in the project folder is the TL. Only the TL calls sub-agents. A sub-agent cannot ask the customer or start another sub-agent. The TL writes task, decision and lesson records. The developer never commits. |
| C-03 | Role catalogue with owned files | S-01 §6.2 table | T-11, T-13 | Each role has owned files, duties, limits and a model: customer, CTO, TL, developer, scout, scribe, auditor, auditor-mini. |
| C-04 | Authority matrix | S-01 §6.3 | T-11 | The matrix says who sets scope, sets gate criteria, gives the verdict, edits records and commits. Only the auditor gives a verdict. |
| C-05 | Single writer per file | S-01 §6.0 and §6.2 owned-files column; S-01 §6.9 concurrency item | T-11 | Each document has one writing role. Other roles suggest changes. One writer per set of files at a time; read-only and record roles may run in parallel. |
| C-06 | Eight-step task loop | S-01 §6.4 steps 1-8 | T-11 | Status, questions, contract, dispatch, implementation, diff review (at most 2 rounds), records, customer test, then commit on approval. |
| C-07 | Batch open questions with options | S-01 §6.4 step 2 | T-11 | All open questions go in one message, recommendation first. An unanswered question gets no default. |
| C-08 | Contract size cap and go-ahead | S-01 §6.4 step 3 | T-11, T-12 | A contract has fixed fields. A contract over 15 lines is split. The customer's go-ahead is the permission for that one task. |
| C-09 | Sub-agent returns early with a question | S-01 §6.4 step 5 | T-11 | At an unclear point the developer stops and returns a question. The TL answers or asks the customer, then resumes the same agent. |
| C-10 | Phase loop stopped by a gate | S-01 §6.5 steps 1-4 | T-11 | The TL stops at a gate. The customer gives the criterion, the auditor judges, fixes follow, findings are re-verified, and the CTO proposes the next agenda. The next phase waits while the gate is open. |
| C-11 | Gate verdict by independent auditor | S-02 rule 22 | T-11 | Whoever wrote or ran the work cannot pass its gate. The verdict is accept, conditional or reject. |
| C-12 | Finding re-verified before close | S-02 rule 24; S-01 §6.5 step 3 | T-11 | The developer fixes. The auditor-mini marks each finding CLOSED, OPEN or PARTIAL with evidence. The trigger is a state, not a date. |
| C-13 | Flexibility with impact note | S-01 §6.6 item 1; S-02 rule 23 | T-11 | The customer may change direction at any time. The TL writes a one-line impact note, warns, acts if the customer insists, and logs it. |
| C-14 | Routing of side analysis | S-01 §6.6 item 2 | T-11 | The TL decides whether the scout, the TL or the CTO analyses a side request. |
| C-15 | Model-independent handover through files | S-01 §6.7 | T-11, T-13 | The contract file is the handover. A backup developer on another model reads the contract and the developer rules, and writes its report under the task. The TL checks it. |
| C-16 | Data boundary for external providers | S-01 §6.13 items 1-4 | T-11, T-13 | Code and documents may reach a second model provider. User data, personal data and keys may not. Keys stay in a local launcher or the environment. Reads of secret files are denied in settings. |
| C-17 | Context hygiene at task boundary | S-01 §6.8 | T-11 | The TL session is cleared only after records are written and approved. The trigger is 3-5 tasks or one large read. Sub-agents start fresh for each task. |
| C-18 | Narrow reading per role | S-01 §7.3 item 3 | T-11 | The TL does not open code files. The developer reads only its contract and the developer rules. |
| C-19 | Model routing by role | S-01 §6.10 table; §7.3 items 1-2 | T-11, T-13 | A small model does search and records. A mid model does development. A high model serves the TL and CTO. The top model does the final audit. |
| C-20 | Effort per role | S-01 §6.10; §7.3 item 2 | T-13 | Effort is set in the role file. Hard tasks raise developer effort. Effort adds thinking on output, not input context. |
| C-21 | Usage-ceiling order of reductions | S-01 §6.10 safety-valve paragraph | T-11 | If usage regularly passes 80% of the window, lower developer effort first, then TL contract writing. Review is never lowered. |
| C-22 | Per-task metrics | S-01 §6.11 | T-11 | Per task, record review rounds, whether a question came back, the customer's test result, and whether a file outside the contract changed. Many returned questions point at the contract. |
| C-23 | One request equals one version | S-02 rule 16 | T-11 | Several tasks from one request ship as one version. The changelog lists each item. |
| C-24 | One current version, stated each reply | S-02 rule 10 | T-11 | Only the current state is tested. Each reply states the version and whether code was written. |
| C-25 | Secrets and private data stay out of the repository | S-02 rule 17 | T-11 | No addresses, keys, tokens or personal data in a repository or commit message. Values live only in ignored local files. A leaked value counts as burned. |
| C-26 | Standard for public endpoints | S-02 rule 13 a-j | T-44 | Write-only endpoint, fail closed without a key, validate input, escape formulas, cheap checks before locks, rate and volume limits, minimal permission, a closing path, local tests with mutation checks. |
| C-27 | Adversarial review before deploy | S-02 rule 13, how-to-apply part | T-11, T-12 | A second reviewer reads the endpoint as an attacker before deploy. |
| C-28 | Documents current, documents first | S-02 rule 18 | T-11 | A stale line is fixed before work starts. A changing fact lives in one place. A check runs at the end of each task. |
| C-29 | Generalisable lesson check | S-02 rule 19 | T-11 | After each task, ask whether the lesson applies elsewhere. Record the event, and the rule if it repeats. |
| C-30 | Machine tests correctness, human judges feel | S-02 rule 20 | T-11 | Automatic tests run before "done". The customer judges feel. "0 build errors" is not proof. |
| C-31 | Behaviour change behind a flag | S-02 rule 21 | T-11 | Changes to feel, camera or cost ship behind a toggle, so the old state returns in one step. |
| C-32 | Role file: developer | S-04 developer role, input, method and report sections | T-13 | Implements one contract, asks instead of guessing, never commits, and returns a fixed report. |
| C-33 | Role file: CTO | S-04 CTO role, input, method, output and rules sections | T-13 | Gives options with the recommendation first. Writes a report only. Writes no code and makes no decision. |
| C-34 | Role file: scout | S-04 scout role, method and report sections | T-13 | Reads only. Returns file and line references and numbers. |
| C-35 | Role file: scribe | S-04 scribe role, what it writes, what it does not touch, and rules sections | T-13 | Writes the log, the status and the changelog check. Never writes decisions or contracts. |
| C-36 | Role file: auditor | S-04 auditor role, method, output and rules sections | T-13 | Runs a full audit with evidence and severity. Ends with a verdict line. Fixes nothing. |
| C-37 | Role file: auditor-mini | S-04 auditor-mini role, method, output and rules sections | T-13 | Checks named findings as CLOSED, OPEN or PARTIAL. Starts no new review. |
| C-38 | Push checklist | S-05 §7 checklist | T-12 | Before a push: test flag off, version and changelog updated, build and tests green, git status in scope, document and secret scan, co-author line, model name in the report. |
| C-39 | Approval means commit and push | S-05 §7 first paragraph; S-06 work rule 6 | T-11 | After approval the TL commits and pushes. One version is one commit. Untested work is not pushed. |
| C-40 | Task contract template | S-06 contract template section (under the work rules, unnumbered) | T-12 | One-line goal, files in and out, observable acceptance, tests, design reference, flag, customer test. |
| C-41 | Standing work rules list | S-06 work rules 0-11 | T-11 | No change without a go-ahead. Decisions come before tasks. One request is one version. Documents stay current. The customer tests. Scope overflow returns as a question. A gate blocks the next phase. |
| C-42 | Audit method | S-07 "How an audit is run" 1-6 | T-11, T-12 | Read documents, code, git and logs. Check every claim. Count what can be counted. Put evidence first. Never close your own finding. |
| C-43 | Severity scale | S-07 "Severity scale" | T-12 | Critical, high, medium, low, by threat and recurring cost. |
| C-44 | Verdict line and finding prefixes | S-04 auditor role, output section | T-12, T-13 | A verdict line of accept, conditional or reject. Finding IDs carry a type prefix: process, design, code or role. |
| C-45 | Re-verify table | S-07 file table, re-verify row; S-04 auditor-mini role, output section | T-12 | Columns are finding, claim, evidence and status, followed by the gate verdict. |
| C-46 | Local pre-push guard: test flag | S-08 whole file; S-09 test-flag part | T-13 | Blocks a push while a test flag is on in the pushed commits. It checks committed content, not the working copy. |
| C-47 | Local pre-push guard: private data scan | S-09 scan part | T-13 | Blocks a push when added lines or commit messages match link patterns, a known key or private paths. It reports the location only, never the match. |
| C-48 | Lesson entry format | S-03 entry structure | T-12 | Date, project label, problem, cause, fix, lesson. |
| C-49 | Lesson: status record versus working tree | S-03 entry 2026-10-26, process: status record said awaiting approval | T-11 | A status record said "awaiting approval" while the tree held unreviewed code. Check git status before trusting a status record. |
| C-50 | Lesson: rules on paper | S-03 entry 2026-10-24, process: independent audit | T-11 | A rule nobody checks is either enforced or deleted. An outside reviewer exposed the gap. |
| C-51 | Lesson: version ambiguity | S-03 entry 2026-10-11, process: version ambiguity | T-11 | An agent asked which version was tested. State the current version from the files. |
| C-52 | Task size labels, 30% cap on hard tasks | S-01 §6.2 last paragraph | T-11, T-12 | Easy, medium and hard labels set effort. If hard tasks pass 30%, contracts are too big and get split. |
| C-53 | Sub-agent report is a claim | S-01 §6.9 last item; §6.4 step 6 | T-11 | The TL checks the diff and the test output before saying "done". |
| C-54 | Continue the same sub-agent for answers | S-01 §6.9 continue item | T-11, T-13 | Answers go back to the same agent. A new call starts blank. |
| C-55 | Sub-agents share the main provider | S-01 §6.1 last paragraph and table note | T-13 | A sub-agent runs on the main session's provider. Another provider is a separate profile, not a sub-agent. |
| C-56 | Developer short rules file, hook-enforced | S-01 §7.2 | T-12, T-13 | The developer reads a short rules file of at most 40 lines. Hooks enforce the same rules. |
| C-57 | State-triggered audit, no calendar | S-01 §6.5 last paragraph; §7.3 item 5 | T-11 | Audits run at gates and after fix rounds, never on a fixed rhythm. |
| C-58 | Counts by script, model reads totals | S-01 §7.3 item 6 | T-11, T-13 | Logs are counted by script. The model gets totals, not raw logs. |
| C-59 | Commit only on approval, no pile-up | S-02 rules 8, 11 | T-11 | An approved change is committed. At most one approved step stays uncommitted. |
| C-60 | Tests belong to the customer | S-02 rule 15 | T-11 | The agent does not test the product unless asked. It says what to check. Automatic code tests are the exception. |
| C-61 | Lesson recorded when the customer steered the fix | S-02 rule 12 | T-11 | A lesson is recorded when the customer directed the fix. Issues the agent found and fixed alone are not logged. |
| C-62 | Lesson: a "why" question tests the rule | S-03 entry 2026-10-26, process: separate CTO session | T-11 | A rule made the customer switch folders, against its own principle; the CTO became a sub-agent. When the customer asks why, test the rule against its principle. Re-measure the data a finding rests on before acting on it. |
| C-63 | Lesson: stale document line | S-03 entry 2026-10-24, process: stale document | T-11 | A fast-changing fact kept by hand in several files stayed stale while a fix waited for permission. Keep it in one place; fix a stale line without asking. |
| C-64 | Lesson: unasked testing | S-03 entry 2026-10-11, process: unasked testing | T-11 | "Start" was stretched into "start and verify". Do the asked action, say what to check, leave the test to the customer. |

## 3. Dropped

| Item | Reason |
|---|---|
| S-01 §7.1 two launch profiles per provider | Provider setup mechanics, not method. |
| S-01 §6.12 entry steps for a new and an existing project | Project-specific setup, not method. |
| S-02 rule 9 ignore entry for a new project folder | Specific to the source folder layout. |
| S-02 rule 1 report data problems with evidence | Rests on game playtest data. |
| S-02 rules 2-7 and 14 | Game design and player telemetry. |
| S-01 sections 1-5 and 8-11 | Cost study, prices and pilot results. Measured numbers stay out until phase 2. |
