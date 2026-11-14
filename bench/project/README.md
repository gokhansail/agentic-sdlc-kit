# budgetbook

A small household budget ledger: transactions, categories, recurring items, monthly budgets, CSV import and export, and a command line interface. Python 3.10 or later, standard library only.

## Run the tests

From this folder:

```
python -m pytest -q
```

pytest is the only tool needed. The tests use temporary folders and never touch a real ledger file.

## Use it

The ledger is one JSON file. `--data PATH` picks the file; without it the CLI uses `BUDGETBOOK_DATA_FILE` (from the environment or from a `.env` file in the current folder), and then `budgetbook.json`.

```
python -m budgetbook add 2024-03-05 -42.80 "food/groceries" "weekly shop"
python -m budgetbook add 2024-03-01 2500 salary
python -m budgetbook list --from 2024-03-01 --to 2024-03-31
python -m budgetbook report 2024-03
python -m budgetbook budget set food 400
python -m budgetbook recurring add rent -900 housing monthly 2024-01-01
python -m budgetbook forecast 2024-04
python -m budgetbook export march.csv --from 2024-03-01 --to 2024-03-31
```

Amounts are signed: negative is an expense, positive is income or a refund. Categories may have parts, `food/groceries`; a filter on `food` includes everything below it.

## Layout

| Module | Job |
|---|---|
| `money.py` | parse and format amounts (integer cents), exact rounding |
| `dates.py` | date and month parsing, month arithmetic |
| `models.py` | `Transaction` and `RecurringItem` |
| `categories.py` | category names and the parent relation |
| `ledger.py` | the ledger and its JSON file |
| `filters.py` | filters on lists of transactions |
| `recurring.py` | occurrences and forecast of recurring items |
| `csvio.py` | CSV export and import |
| `budgets.py` | monthly limits per category |
| `reports.py` | monthly report |
| `summary.py` | yearly summary |
| `accounts.py` | balances per account |
| `textfmt.py` | text padding and truncation (display team) |
| `rendering.py` | text output for the commands |
| `config.py` | settings from the environment and `.env` |
| `cli.py` | the command line |

## Conventions

- Money is integer cents inside the package; floats are not used for amounts.
- A category is always passed through `normalize_category` before it is stored or compared.
- Output functions in `rendering.py` return strings; only `cli.py` prints.
- `textfmt.py` belongs to the display team. Other teams do not edit it.
