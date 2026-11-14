# Bench

What is this folder? The fixed task set for the kit-against-plain-prompt comparison (DEC-065): one small sandbox project, 6 tasks on it, and the hidden tests that score each task by machine. It was written and frozen before any model run, and no model was called to build it. The runner that uses it comes in T-56.

## Contents
- `project/`: the sandbox, a household budget ledger called `budgetbook` (transactions, categories, recurring items, monthly budgets, CSV import and export, a command line). Python 3.10, standard library only, 20 modules, about 1,500 lines, a visible pytest suite that is green. It has its own `pyproject.toml` and a README on how to run its tests. It has no `.git`.
- `tasks/B1` to `B6`: per task `task.md` (the only text an arm gets), `hidden/` (acceptance tests, a `conftest.py` and test files), `allowed.txt` (paths the task may change, used for scoring only) and `reference.patch` (a known solution, a unified diff relative to `project/`).
- `conftest.py`: keeps the pytest of the kit root from collecting the sandbox and the hidden tests, as `eval/conftest.py` does.
- `.gitattributes`: every file here is checked out with LF.
- `tests/test_bench.py` (in the kit root): the known-answer test.

## How a run uses it
1. Copy `project/` and nothing else from `bench/` into a folder outside the kit. Rename `dot_env` to `.env`. The pre-push guard refuses any file named `.env`, so the sandbox ships it as `dot_env`; the copy has `.env` only. It holds a made-up key, `BENCH_FAKE_KEY`, for the scope trap in B6.
2. `git init` and one baseline commit in the copy (T-56 does this). The arm gets `task.md` as its task.
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

Sizes follow the kit's own scale: 2 E, 3 M, 1 H.

## Known-answer check
`python -m pytest -q tests/test_bench.py` runs, per task and in a temporary copy: the unchanged project fails the hidden tests (failures, not collection errors); with `reference.patch` applied the hidden tests and the visible suite pass; the patch touches only paths allowed by `allowed.txt`. It also checks the hash below, that the sandbox is large enough, that the files pass the pre-push guard, and that both B6 trap checks fail when their rule is broken.

## Frozen
SHA-256 over every file under `project/` and `tasks/`, in this way: take the paths relative to `bench/` with `/` as separator, leave out `__pycache__` and `.pytest_cache` folders and `*.pyc` files, sort the paths as plain strings, and feed into SHA-256 for each file the path in UTF-8, one NUL byte, the content with every CRLF turned into LF, one NUL byte. `tests/test_bench.py` has the same function (`tree_hash`) and checks this line.

SHA-256: `113493b1602a49057bf3b76ea69b494238ef6a63d6ef88c4c1af22c697d66aaf`

The project, the tasks, the hidden tests and the patches do not change after freezing. A change is a new version of the set with a new hash and a new line here; results from different versions are not compared.

## Limits
- One synthetic project and 6 tasks: a result is a sample, not a general measure.
- The author of the kit wrote the sandbox, the tasks and the hidden tests. The tasks were not changed after looking at any model result, and no model was run on them.
- Scoring is by machine only. It does not judge readability or design, and it does not include the customer's own test of a result.
- The visible suite has more tests (about 115 collected) than the 60 the plan named; the extra ones guard behaviour a fix may disturb.
