# Bench results

> **What is this file?** The result of the bench runs `full-1` and `full-1-b7` (`bench/results/full-1.json`, `bench/results/full-1-b7.json`): what was run, the tables, what they show and what they do not show. The tables are produced by `tools/bench_table.py`; do not edit between the markers.

## What was run
The bench asks one question: does a model complete coding tasks better with the kit than with a plain prompt (DEC-065). The rule, the commands and the caps were recorded before the first scored run (DEC-078). The set-up is fixed.

- One synthetic project, a household budget ledger: 20 modules, about 1,500 lines, Python standard library (`bench/README.md`).
- 7 tasks. Each has hidden tests that score a run by machine. Six tasks (B1 to B6) are run under the label `full-1`. The large rebuild task (B7) is run alone under the label `full-1-b7` and is reported apart.
- 2 arms. The plain arm gets the task as a prompt. The kit arm gets the plugin, the roles, the scope guard and the read-only server.
- Sonnet in every role, 3 repeats per task and arm, seed 0.
- `full-1`: 6 tasks x 2 arms x 3 repeats = 36 runs, a cap of 2 USD and 2,700 s per run, a budget of 40 USD.
- `full-1-b7`: 1 task x 2 arms x 3 repeats = 6 runs, a cap of 2.1 USD per run (3 times the kit cost in the pilot) and 2,700 s, a budget of 15 USD.
- The pilot had 4 runs and was not scored. It set only the caps of the large task.

All 42 runs finished, with 0 harness errors and 0 reruns. The runs spent 6.48 USD and 3.31 USD. The CLI was 2.1.327 and the kit commit was c99c9fe. The kit's own files are unchanged since f148c73, where the kit was frozen for the bench.

The rule for the primary result (H1) is fixed beforehand. It compares full passes of the kit and the plain arm on the 6 tasks, out of 18 runs each. If the kit has 3 or more full passes more than plain and no more regressions, the category is "kit better". If the two are within 2, it is "no difference". If plain has 3 or more full passes more, it is "plain better". The kit claims better work only in the first case. Cost, scope and test changes are reported without a threshold.

## Tables
Table 1 has one row per file and arm. Table 2 has one row per file, task and arm. Cost is the CLI's list-price estimate, not a bill.

Render command:

```
python tools/bench_table.py --doc docs/bench-results.md bench/results/<label>.json [more.json ...]
```

<!-- bench-table:start -->
Label full-1; date 2026-11-18; CLI 2.1.327 (Claude Code); kit commit c99c9fe; bench hash e7f25782b9d3; runs 36 of 36; spent USD 6.479.

Label full-1-b7; date 2026-11-18; CLI 2.1.327 (Claude Code); kit commit c99c9fe; bench hash e7f25782b9d3; runs 6 of 6; spent USD 3.308.

| File | Arm | Full pass | Hidden passed | Visible green | Runs with out-of-scope files | Runs with test changes | Hidden reads | Guard denies | Sub-agents spawned | Cost USD | Cost USD per run | Wall per run (s) | Turns per run |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| full-1 | plain | 18 of 18 | 291 of 291 | 18 of 18 | 2 of 18 | 4 of 18 | 1 | 0 | 0 | 1.844 | 0.1024 | 28.0 | 8.44 |
| full-1 | kit | 18 of 18 | 291 of 291 | 18 of 18 | 2 of 18 | 18 of 18 | 0 | 8 | 19 | 4.635 | 0.2575 | 67.8 | 14.33 |
| full-1-b7 | plain | 3 of 3 | 141 of 141 | 3 of 3 | 0 of 3 | 3 of 3 | 0 | 0 | 0 | 1.051 | 0.3502 | 128.6 | 10.00 |
| full-1-b7 | kit | 3 of 3 | 141 of 141 | 3 of 3 | 0 of 3 | 3 of 3 | 0 | 0 | 3 | 2.258 | 0.7526 | 363.3 | 16.33 |

| File | Task | Arm | Full pass | Hidden passed | Cost USD per run |
|---|---|---|---|---|---|
| full-1 | B1 | plain | 3 of 3 | 21 of 21 | 0.0475 |
| full-1 | B1 | kit | 3 of 3 | 21 of 21 | 0.1694 |
| full-1 | B2 | plain | 3 of 3 | 36 of 36 | 0.0903 |
| full-1 | B2 | kit | 3 of 3 | 36 of 36 | 0.2439 |
| full-1 | B3 | plain | 3 of 3 | 69 of 69 | 0.1619 |
| full-1 | B3 | kit | 3 of 3 | 69 of 69 | 0.3397 |
| full-1 | B4 | plain | 3 of 3 | 72 of 72 | 0.0850 |
| full-1 | B4 | kit | 3 of 3 | 72 of 72 | 0.1997 |
| full-1 | B5 | plain | 3 of 3 | 48 of 48 | 0.0737 |
| full-1 | B5 | kit | 3 of 3 | 48 of 48 | 0.2248 |
| full-1 | B6 | plain | 3 of 3 | 45 of 45 | 0.1564 |
| full-1 | B6 | kit | 3 of 3 | 45 of 45 | 0.3676 |
| full-1-b7 | B7 | plain | 3 of 3 | 141 of 141 | 0.3502 |
| full-1-b7 | B7 | kit | 3 of 3 | 141 of 141 | 0.7526 |
<!-- bench-table:end -->

## What the tables show
Task results (H1). On the 6 tasks, the kit had 18 of 18 full passes and plain had 18 of 18. By the recorded rule (within 2) the category is "no difference". There is no difference in task results on this set; the kit cost 3.30 times the tokens (2.51 times in USD) and 2.42 times the time. The kit does not claim better work from this bench.

Cost (H2). On the 6 tasks, the kit to plain ratio was 2.51 in USD (4.635 against 1.844), 3.30 in total tokens (7,645,211 against 2,319,244, cache reads included) and 2.42 in wall time (1,219.9 s against 503.5 s). Turns per run were 14.33 against 8.44.

Large task (H5, reported apart). On the large rebuild task (B7), the kit had 3 of 3 full passes and plain had 3 of 3. The kit to plain ratio was 2.15 in USD (2.258 against 1.051), 3.78 in total tokens (4,154,176 against 1,097,723) and 2.83 in wall time (1,090.0 s against 385.7 s). On the two easy tasks (B1, B2) the ratios were 3.00 in USD (1.240 against 0.413), 4.36 in total tokens (2,013,434 against 461,358) and 4.39 in wall time (363.5 s against 82.8 s). So all three ratios were lower on the large task than on the easy tasks. With 3 runs per arm this is a description, not a measured effect, and no threshold was set.

Scope (H3). Runs with files outside the task's allowed list: 2 of 18 in each arm. All 4 runs were on the bug-fix task with a misleading hint (B4), and the same file in all 4 (`budgetbook/stats.py`). On this set the kit did not reduce out-of-scope writes. The bench scores against the `allowed.txt` of the task, which neither arm sees. The kit's guard checks against the contract that the kit's own lead session writes. On the large task, 0 of 3 in both arms.

Visible test files touched (H3). On the 6 tasks, plain touched visible test files in 4 of 18 runs (4 files modified, 0 added, 0 deleted). The kit did so in 18 of 18 runs (28 modified, 3 added, 0 deleted). On the large task, plain did so in 3 of 3 runs (2 modified, 1 added) and the kit in 3 of 3 (0 modified, 3 added). Every task allows `tests/*`. The hidden tests repeat the key visible checks, so a green visible suite reached by editing tests does not give a full pass. The counts do not say whether an edit was good or bad.

Hidden reads. The table shows 1 for the plain arm. It is a word match, not a read of the hidden tests. In one plain run of the scope-trap task (B6), a shell command masked the values of `.env` with `sed 's/=.*/=<hidden>/'`, and the runner counts any tool call with `hidden` in it. The hidden tests are copied in only after a run ends, so no run could read them. There were 0 real reads.

Guard and sub-agents. The guard denied 8 calls, all in the kit arm. All 8 came from the lead (main) session writing before it had placed a contract, in 3 runs (B1, B2, B6). All 3 runs then passed. The kit spawned 19 sub-agents in 18 runs on the 6 tasks and 3 in 3 runs on the large task, all of the developer role. Plain spawned 0.

Secondary review. The blind review of the 3 large-task diff pairs by the maintainer (DEC-071) was not done when this page was written. It is reported apart and cannot change the category.

## Limits
- One synthetic project and 7 tasks, written by the author of the kit. The tasks were not changed after looking at any model result.
- One model (Sonnet) and one CLI version (2.1.327). Other models and other versions are not measured.
- 3 repeats per task and arm. There is no significance test. The threshold of 3 is a rule chosen beforehand.
- Both arms passed every task, so the set did not separate the arms. The result is at the ceiling of the tests.
- The large task is the only one of its size. Its tests judge printed text, JSON and CSV, exit codes and the ledger file. Machine scoring judges behaviour, not design or readability.
- The scope measure is against `allowed.txt`, which neither arm sees.
- The kit's scope guard checks Edit and Write calls only. Writes through the shell are outside its view (DEC-075).
- The kit arm's server is started by `--mcp-config`, not through the installed plugin (DEC-069). A run does not test the plugin's own server wiring.
- Cost is a list-price estimate. Runs count against the subscription usage limits.
- The result belongs to this set-up. It is not a general measure of the kit.
- After the public release the bench is not rerun to change this category (DEC-059).
