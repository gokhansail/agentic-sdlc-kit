# Eval set

What is this folder? The fixed question set for the evaluation in DEC-012: does a model answer questions about a project's records better with the MCP server attached than without it. It holds a small synthetic repository, 30 questions about its state, the answer key and a scorer. It was written and frozen before the server tools (T-41 and later) existed, so the tools were not shaped to the questions. No model was called to build it.

## Contents
- `repo/`: a fictional invoicing service ("Tallybook") that has opted in to the kit: `.sdlc/project.md`, an active contract for T-7, guard events in `.sdlc/metrics.jsonl`, and the records `TASKS.md`, `DECISIONS.md`, `LOG.md`, `STATUS.md`, `LESSONS.md`, `CHANGELOG.md`, `DEV_RULES.md`, `audits/`. It has no source code; the questions only ask about its records. pytest does not collect it (`conftest.py`).
- `questions.jsonl`: 30 lines. Fields: `id`, `category`, `question`, `answer_type` (`token`, `yes-no`, `number` or `set`), `key`, `sources` (the files of `repo/` the answer follows from). The 8 scope questions also carry `check` (path and actor), so a test can recompute the key with `tools.scope_guard`.
- `score.py`: the scorer.

## Categories
| Category | Questions |
|---|---|
| scope and contract | 8 |
| decisions | 6 |
| findings and gates | 6 |
| tasks and status | 5 |
| guard events | 3 |
| lessons | 2 |

11 questions need two or more files combined.

## How to score
One answer per question, one JSON line each, in a file such as `answers.jsonl`:

```
{"id": "Q01", "answer": "yes"}
{"id": "Q12", "answer": 3}
{"id": "Q13", "answer": ["DEC-008", "DEC-009"]}
```

Run `python eval/score.py answers.jsonl`. It prints one line per question, the count per category and `total: N/30`. From code: `eval.score` functions `load_questions`, `load_answers`, `score`. Case, spaces, the order of a set and the wording of yes and no (`yes`, `y`, `true`) are normalised; a missing answer is wrong.

## Frozen
SHA-256 of `questions.jsonl`, computed after turning CRLF line endings into LF: `c59798e361ff995ede8ae5332218ca66bd27e4051ade1e2e50ad47a91692371f`

`tests/test_eval.py` checks this hash. The questions, keys and `repo/` do not change after freezing. A change is a new version of the set with a new hash and a new line in this file; results from different versions are not compared.

## Limits
- One fictional repository and 30 questions: a result is a sample, not a general measure.
- The set tests reading and combining records, not writing them.
- The scope keys follow the guard rules at the time of freezing.
