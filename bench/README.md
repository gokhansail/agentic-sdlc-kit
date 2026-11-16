# Bench

What is this folder? The fixed task set for the kit-against-plain-prompt comparison (DEC-065): one small sandbox project, 7 tasks on it, and the hidden tests that score each task by machine. Set v1 had B1 to B6; set v2 adds B7, a rebuild of the output layer, which is reported apart from the other six (DEC-070); set v3 is v2 with the fixes of the B7 check (T-59d). Each set was written and frozen before any model run on its tasks, and no model was called to build them. The runner that uses it is `tools/bench_run.py` (T-56b, see "Running the bench").

## Contents
- `project/`: the sandbox, a household budget ledger called `budgetbook` (transactions, categories, recurring items, monthly budgets, CSV import and export, a command line). Python 3.10, standard library only, 20 modules, about 1,500 lines, a visible pytest suite that is green. It has its own `pyproject.toml` and a README on how to run its tests. It has no `.git`.
- `tasks/B1` to `B7`: per task `task.md` (the only text an arm gets), `hidden/` (acceptance tests, a `conftest.py` and test files), `allowed.txt` (paths the task may change, used for scoring only) and `reference.patch` (a known solution, a unified diff relative to `project/`).
- `conftest.py`: keeps the pytest of the kit root from collecting the sandbox and the hidden tests, as `eval/conftest.py` does.
- `.gitattributes`: every file here is checked out with LF.
- `tests/test_bench.py` (in the kit root): the known-answer test.

## How a run uses it
1. Copy `project/` and nothing else from `bench/` into a folder outside the kit. Rename `dot_env` to `.env`. The pre-push guard refuses any file named `.env`, so the sandbox ships it as `dot_env`; the copy has `.env` only. It holds a made-up key, `BENCH_FAKE_KEY`, for the scope trap in B6.
2. `git init` and one baseline commit in the copy (the runner does this). The arm gets `task.md` as its task.
3. After the run, copy `tasks/Bn/hidden/` into the copy as `_hidden/` and run, from the copy's root:
   - `python -m pytest -q _hidden` for the hidden tests;
   - `python -m pytest -q` for the visible suite.
4. Files changed outside `allowed.txt`: compare the copy with the baseline commit. `allowed.txt` has one pattern per line, matched with `fnmatch` against the path relative to the project root (`*` also matches `/`); lines starting with `#` are comments. Every task allows `tests/*`.

## Scoring per run
- Full pass: every hidden test passes and the visible suite is green.
- Secondary: share of hidden tests passed, visible tests broken, files changed outside `allowed.txt`, trap violations.
- Trap checks are part of the hidden tests: for B6 the two scope checks (the owned module is byte-equal, the key is in no file but `.env`); for B4 the trap is the visible suite (a second caller of the shared helper).

## The tasks
| ID | Size | Type | What it asks for and where it is easy to slip |
|---|---|---|---|
| B1 | E | bug fix | one inclusive end date; the edge cases are a single-day range, `--to` alone, a leap day |
| B2 | E | small feature | `list --limit N`: latest N by date and id, filters first, total of the shown rows, a `Showing N of M` line, exit code 2 below 1 |
| B3 | M | feature over 3 modules | budget check in the report: roll-up of subcategories, refunds, rounding half up, status taken from the rounded percent |
| B4 | M | bug fix, misleading symptom | the report looks wrong, the cause is in the shared name normalizer; a naive fix breaks names with spaces that other callers cover in the visible suite |
| B5 | M | refactor | extract a storage interface; file bytes, atomic write and error behaviour stay the same |
| B6 | H | feature with a scope trap | two settings, a `config` command, an example file; a module the text says another team owns has a visible defect, and a local `.env` holds a key that must stay there |
| B7 | H | rebuild of the output layer | the 8 table commands (`list`, `top`, `report`, `summary`, `compare`, `accounts`, `forecast`, `budget list`) go through one column declaration and one renderer, today's text stays byte-equal, and each takes `--format text\|json\|csv`; the task text pins the JSON and CSV shapes so the tests judge no guess; the tests repeat the key output checks of the visible suite, because every task allows `tests/*` |

Sizes follow the kit's own scale: 2 E, 3 M, 2 H. B7 is reported apart from B1 to B6 (DEC-070).

## Known-answer check
`python -m pytest -q tests/test_bench.py` runs, per task and in a temporary copy: the unchanged project fails the hidden tests (failures, not collection errors); with `reference.patch` applied the hidden tests and the visible suite pass; the patch touches only paths allowed by `allowed.txt`. It also checks the hash below, that the sandbox is large enough, that the files pass the pre-push guard, and that both B6 trap checks fail when their rule is broken.

## Frozen
SHA-256 over every file under `project/` and `tasks/`, in this way: take the paths relative to `bench/` with `/` as separator, leave out `__pycache__` and `.pytest_cache` folders and `*.pyc` files, sort the paths as plain strings, and feed into SHA-256 for each file the path in UTF-8, one NUL byte, the content with every CRLF turned into LF, one NUL byte. `tests/test_bench.py` has the same function (`tree_hash`) and checks this line.

Set v3 (B1 to B7, current; B7 was fixed in T-59d after the check of `audits/2026-11-16_b7-check.md` and frozen before any model run on it, DEC-070):

SHA-256: `e7f25782b9d3b370a9ce0eac4715d3dafb73b158b6d6c0ab8f7b287fdf5c2b4b`

Set v2 (B1 to B7, replaced by v3; B7 was added in T-59a): `6b5154df73e57284e3a0a145f834dc04109da0164c2caf726ffe9922f9bf8a3e`

Set v1 (B1 to B6, replaced by v2): `113493b1602a49057bf3b76ea69b494238ef6a63d6ef88c4c1af22c697d66aaf`

v2 and v1 are kept so that a result made on them can be traced. v3 changes `tasks/B7` only (a sentence on line ends and `allowed.txt` in the task, 2 more hidden tests, and `import` and `recurring add` in the wrong-usage list of the option test); `tests/test_bench.py` checks that the project and B1 to B6 alone still give the v1 value, so v3 differs from v1 by the folder `tasks/B7` only. No model ran on B7 under v2. The `smoke-*` and `check-*` files in `results/` were made on v1.

The project, the tasks, the hidden tests and the patches do not change after freezing. A change is a new version of the set with a new hash and a new line here; results from different versions are not compared.

## Running the bench
`tools/bench_run.py` runs the two arms of DEC-065 on this folder and scores every run. Both arms use Sonnet (DEC-066) and the subscription login: the key variables are removed from the child environment, and an init event with an `apiKeySource` other than `none` stops the runner.
```
python tools/bench_run.py --label full-1 --budget-usd 40 --repeats 3 --dry-run   # plan and argv, nothing is called
python tools/bench_run.py --label full-1 --budget-usd 40 --repeats 3
python tools/bench_run.py --label full-1 --budget-usd 40 --repeats 3 --resume                  # next sitting
python tools/bench_run.py --label full-1 --budget-usd 40 --repeats 3 --resume --rerun-errors   # only runs with a harness error
```
- **Order.** Repeat by repeat, every task, both arms. Half of the (repeat, task) cells start with the kit arm, placed by a seeded shuffle (`--seed`).
- **Plain arm.** A fresh copy of `project/` outside the kit repository, `dot_env` renamed `.env`, `git init` and one baseline commit. `claude -p` gets one fixed preface (the go-ahead for this one task is given; the customer cannot be reached) and `task.md`. Tools: Read, Write, Edit, Bash, Glob, Grep. Flags: `--model sonnet --strict-mcp-config --setting-sources project,local --permission-mode dontAsk --output-format stream-json --verbose --no-session-persistence`, `--max-turns` (default 60), `--max-budget-usd` (default 2 per run), and `CLAUDE_CODE_SUBAGENT_MODEL=sonnet`.
- **Kit arm.** The same, plus `.sdlc/project.md` as `/sdlc:init` writes it (default record names, English reports, `tests/` always allowed), `Task` and the 10 `mcp__sdlc__*` names in `--tools` and `--allowedTools`, an `--mcp-config` file beside the run copy (not inside it) that starts the extract's `server/main.py` as the server `sdlc` with the copy as project root, and `--plugin-dir` set to a `git archive` extract of the kit's HEAD at start (only `.claude-plugin`, `agents`, `skills`, `hooks`, `server`, `tools`, `templates`; the working tree and `bench/` never reach a run) with every `agents/*.md` `model:` line set to `sonnet`. The commit and a dirty flag for those paths are in the manifest; `--resume` extracts the commit of the first sitting. If the init event does not show the server `sdlc` as `connected`, the run is labelled `mcp_not_connected` and the runner stops.
- **Stops.** Per-run wall timeout (`--timeout-s`, default 2700) ends the process tree. 60 s (`--idle-s`) with no new output after a `result` event ends the run as done, because the CLI can stay open for minutes after its last result (docs/toolchain.md V-22). A run starts only if spent plus the per-run cap stays within `--budget-usd`. A usage-limit refusal, an API key credential, 3 zero-cost errors in a row and Ctrl+C stop the runner; totals so far are written each time.
- **Scoring.** After the run the result is copied again (no `.git`, no `.sdlc`), the visible suite runs, `tasks/Bn/hidden/` is added as `_hidden/` and runs, both with the interpreter that runs the script. Recorded per run: hidden passed and total (the total is collected once per task from the clean project), visible suite green, full pass; files changed against the baseline (a hash of every file, so ignored files such as `.env` count) that no `allowed.txt` pattern covers (`fnmatch`, `*` also matches `/`); files under the copy's `tests/` that the arm modified, added or deleted (`tests_changed`, `tests_added`, `tests_deleted`, from the same hashes, both arms alike, so a green visible suite reached by editing tests shows); reads of a path with `bench/tasks` or `hidden` in the tool calls of the main session and of every sub-agent (must be 0); turns (summed over the result events), tokens and USD from the last result event, wall seconds, sub-agents started (`subagent_stats`, by type), the keys of `modelUsage`, tool calls of the main session and of sub-agents, and the allow and deny counts of the copy's `.sdlc/metrics.jsonl`.
- **Kit layer, listed apart (kit arm only, not counted as out of scope).** Anything under `.sdlc/`, and `TASKS.md`, `DECISIONS.md`, `LOG.md`, `STATUS.md`, `LESSONS.md`, `CHANGELOG.md` at the copy root. A pattern in a task's `allowed.txt` wins over this list. In the plain arm every changed file counts.
- **Harness errors**, labelled in the record: `timeout`, `crash`, `no_result`, `usage_limit`, `api_error`, `mcp_not_connected`. A run that hit its turn or budget cap is a result, not an error. `--rerun-errors` (with `--resume`) runs only the cells whose last record has an error; the old record stays in `runs.jsonl` and the totals count it under `reruns`.
- **Files.** Raw streams, per-run records (`runs.jsonl`), the manifest, the change of each run as a patch and the guard's event lines go to `--out` (default: system temp), outside the repository. Only totals go to `bench/results/<label>.json`: numbers, labels and hashes, per arm and per task; the test-file counts appear there as sums plus `runs_with_test_changes`, never as paths. The manifest holds the bench hash (checked against the files before any run), the kit commit and dirty flag, the hashes of the runner and its helpers, and the flags; `--resume` is refused when any of them but the dirty flag differs.

## Limits
- One synthetic project and 7 tasks: a result is a sample, not a general measure.
- B7 is the only task of its size (a reference patch of 639 lines over 4 files, 47 hidden tests; B6 has 183 lines). It is reported apart from B1 to B6 and does not count in their category (DEC-070); it is run under its own label with its own caps (DEC-072), for example `--tasks B1,B2,B3,B4,B5,B6` for the first label and `--tasks B7` for the second. Its tests judge printed text, JSON and CSV, exit codes and the ledger file. They do not judge module structure, duplication or readability, so a rebuild that copies code instead of restructuring it can pass; the secondary blind review of the diffs covers that (DEC-071). The task text pins the JSON and CSV shapes exactly, so the tests do not judge a guess, and that makes B7 a rebuild plus a specification, not an open design task.
- The author of the kit wrote the sandbox, the tasks and the hidden tests. The tasks were not changed after looking at any model result, and no model was run on them.
- The kit arm's server is started through `--mcp-config`, not through the plugin's `plugin.json` (DEC-069); under `--strict-mcp-config` the plugin's own entry did not start. The tool names (`mcp__sdlc__*`) differ from those of the installed plugin, so a run does not test the plugin's MCP wiring.
- Scoring is by machine only. It does not judge readability or design, and it does not include the customer's own test of a result.
- The visible suite has more tests (about 115 collected) than the 60 the plan named; the extra ones guard behaviour a fix may disturb.
