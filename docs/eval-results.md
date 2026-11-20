# Eval results

> **What is this file?** The result of the server eval (`eval/results/full-2.json`): what was run, the tables, what they show and what they do not show. The tables are produced by `tools/eval_table.py`; do not edit between the markers.

## What was run
The eval asks one question: does a model answer questions about a project's records better with the sdlc server attached than without it (DEC-012). The set-up is small and fixed.

- One synthetic repository of about 18 KB, with the records of a fictional project (`eval/README.md`).
- 30 questions about the state of that repository, with an answer key and automatic scoring. The 6 categories are scope and contract (8 questions), decisions (6), findings and gates (6), tasks and status (5), guard events (3) and lessons (2).
- 2 models, Haiku and Sonnet.
- 2 conditions. Both give the model the `Read` tool and a list of the repository files. The server condition adds the server's 10 read-only tools.
- 3 repeats of every question, model and condition: 2 x 2 x 3 x 30 = 360 runs, 90 per model and condition.
- The runs use the subscription login. Each run is one `claude -p` call with a cap of 12 turns and 0.25 USD estimated.

An earlier run, `full-1`, had 1 run per cell (120 runs, DEC-055). It was the first measurement. The gate asks for at least 3 runs per cell, so `full-1` is not used for it (DEC-056). `docs/eval-runbook.md` has the steps.

## Tables
Table 1 has one row per model and condition. Table 2 has the correct answers per category, for the same rows. Cost is the CLI's list-price estimate, not a bill.

<!-- eval-table:start -->
Label full-2; date 2026-11-10; CLI 2.1.319 (Claude Code); runner commit 6579f6cf81d2; git_dirty false; repeats 3; settings: max_run_usd 0.25, max_turns 12, restricted true, setting_sources project,local, timeout_s 300, tools Read.

| Model | Condition | Runs | Correct | Accuracy mean | Accuracy min | Accuracy max | Errors | Unparsed | Cost USD | Cost USD per run | Output tokens | Duration per run (s) | Turns per run | Tool calls | Server tool calls | Read calls |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| haiku | no-server | 90 | 87 | 0.967 | 0.967 | 0.967 | 0 | 0 | 0.115 | 0.0013 | 67069 | 3.8 | 5.28 | 385 | 0 | 385 |
| haiku | server | 90 | 83 | 0.922 | 0.900 | 0.933 | 0 | 0 | 0.078 | 0.0009 | 47805 | 3.3 | 3.27 | 204 | 40 | 164 |
| sonnet | no-server | 90 | 90 | 1.000 | 1.000 | 1.000 | 0 | 0 | 1.138 | 0.0126 | 30657 | 3.4 | 2.93 | 174 | 0 | 174 |
| sonnet | server | 90 | 90 | 1.000 | 1.000 | 1.000 | 0 | 0 | 0.785 | 0.0087 | 18119 | 2.7 | 2.83 | 165 | 141 | 24 |

| Model | Condition | decisions | findings | guard | lessons | scope | tasks |
|---|---|---|---|---|---|---|---|
| haiku | no-server | 18 of 18 | 18 of 18 | 6 of 9 | 6 of 6 | 24 of 24 | 15 of 15 |
| haiku | server | 18 of 18 | 18 of 18 | 6 of 9 | 6 of 6 | 20 of 24 | 15 of 15 |
| sonnet | no-server | 18 of 18 | 18 of 18 | 9 of 9 | 6 of 6 | 24 of 24 | 15 of 15 |
| sonnet | server | 18 of 18 | 18 of 18 | 9 of 9 | 6 of 6 | 24 of 24 | 15 of 15 |
<!-- eval-table:end -->

## What the tables show
All 360 runs finished with 0 errors and 0 unparsed answers.

Sonnet answered 90 of 90 correctly in both conditions, so the server did not change its accuracy. With the server it cost 0.785 USD against 1.138 USD without. It made 24 Read calls against 174, and 18119 output tokens against 30657. Its turns per run were 2.83 against 2.93. It made 141 server tool calls. From local raw output, not in the repository: Sonnet called a server tool in 85 of its 90 server runs.

Haiku answered 83 of 90 correctly with the server and 87 of 90 without. Its accuracy per repeat was 0.900 to 0.933 with the server and 0.967 in each repeat without, so the gap appears in all 3 repeats. Table 2 shows where it is: Haiku with the server answered 20 of 24 scope questions correctly, and without the server 24 of 24. The other categories are equal between the two conditions, including 6 of 9 in guard events in both. With the server Haiku cost 0.078 USD against 0.115 USD without, made 164 Read calls against 385, and had 3.27 turns per run against 5.28. It made 40 server tool calls in 90 runs. From local raw output, not in the repository: Haiku called a server tool in 20 of its 90 server runs, and 6 of its 7 server misses had no server call.

The main eval (`full-2`) did not test a cause for the Haiku gap. A follow-up run tested one; see "Haiku follow-up" below.

## Haiku follow-up
After `full-2`, Haiku was run again on the 8 scope questions only, with 5 repeats, so 40 runs per condition. Each condition has its own totals file, `eval/results/haiku-scope-*.json`. The conditions differ in the server and in the prompt (`--prompt-variant`, `docs/eval-runbook.md` step 5).

| Condition | File | Correct |
|---|---|---|
| server, default prompt | `haiku-scope-server.json` | 32 of 40 |
| server, `files-are` prompt | `haiku-scope-filesare.json` | 40 of 40 |
| server, `use-tools` prompt | `haiku-scope-usetools.json` | 40 of 40 |
| no server | `haiku-scope-noserver.json` | 40 of 40 |

The default prompt lists the files with the words "Use only these files". The `files-are` variant lists them with the words "The files are". The `use-tools` variant is the default prompt plus one sentence that the server tools answer questions about scope, contracts and records.

With the default prompt, the 8 wrong runs were on 2 questions about writes. All 8 made no server call. With either variant, a server call was made in 40 of 40 runs. With the default prompt, a server call was made in 20 of 40 runs. So in this follow-up the wrong runs were runs where the model did not use the server, and both prompt variants removed the gap. The new `scope_check` tool description alone did not remove it: the default prompt still gave 32 of 40.

The per-run counts (runs with a server call, and the wrong runs without one) come from local raw output, which is not in the repository. The committed totals files hold the correct counts and the number of tool calls, not the number of runs with a call. The 4 conditions ran in 4 windows at the same time, so durations are not compared. This follow-up does not say why the model skips the tools with the default prompt.

## Limits
- One synthetic repository of about 18 KB, small enough to be read in full by a model. The result says nothing about a larger repository. A run on a larger repository would be a separate experiment and is not planned.
- 30 questions, written by a Sonnet `developer` agent from the lead's contract (T-46a) and approved by the maintainer. The set tests reading and combining records, not writing them.
- 2 models and one CLI version (Claude Code 2.1.319). Other models and other versions are not measured.
- Read is the only tool besides the server. It was chosen so that both conditions have the same single tool, with the files listed in the prompt, and the eval measures the server and not a difference in tools (DEC-054). The no-server condition therefore finds facts by reading files.
- Cost is a list-price estimate, not a bill. Runs count against the subscription usage limits.
- Each run is capped at 12 turns and 0.25 USD estimated.
- The runs are not isolated from the account. The CLI's own bundled listings were in the model's context (`docs/eval-runbook.md`, Limits). `claude plugin eval` gives an isolated home and config for each run (`docs/toolchain.md`); it was not used, so these runs have no such isolation (DEC-060).
- 90 runs per model and condition are a sample. Haiku with the server had 4 more misses than without (83 against 87 correct of 90), in every repeat. The main eval does not say why; the follow-up above tested one explanation, on 8 questions only.
- `full-1` (1 run per cell) is kept as the first measurement and is not used for the gate.
- The result belongs to this set-up. It is not a general benefit of the server.
