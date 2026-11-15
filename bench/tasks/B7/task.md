Rebuild how `budgetbook` produces the output of its table commands, then add machine-readable output to them.

The eight commands are `list`, `top`, `report`, `summary`, `compare`, `accounts`, `forecast` and `budget list`. Each of them builds its own text by hand today. Change that:

1. Each command describes its output once, as data: the columns of its table (the header shown in text, the key used in JSON and CSV, how a cell is read from a row, left or right alignment) and the lines around the table (title, total). One renderer turns that description and the rows into text, JSON or CSV. A command does not align, quote, join or print table text itself, and adding a column means changing one place. `report` and `compare` print label lines today, not an aligned table; they follow the same rule.
2. The text of all eight commands stays byte for byte what it is today, including the empty results (`No transactions.` and the like) and the cut-off of long descriptions in `list`. Run the commands before you change anything and keep what they print. The tests in `tests/` check part of it.
3. Each of the eight commands takes `--format text|json|csv`. The default is `text`.
4. The tests in `tests/` are green when you finish. Change a test only when the code it calls has moved; what it says about printed output must still hold.

The other commands (`add`, `edit`, `remove`, `installments`, `import`, `export`, `recurring`, `budget set`, `budget remove`) are not part of this task. They print what they print today, they do not take `--format`, and `export` keeps its own columns. The rest of the package (ledger, models, money, dates, config, `textfmt.py` and so on) stays as it is.

Where the code goes: change `budgetbook/cli.py` and `budgetbook/rendering.py`; put new code in new files in `budgetbook/` whose names begin with `table`, `column`, `output`, `format`, `render`, `layout` or `view` (for example `columns.py`), or in a new subfolder of `budgetbook/`; you may also update `README.md` and the files in `tests/`. A change to any other file is out of scope.

## The option

`--format` is an option of the command, like `--count`: `budgetbook --data ledger.json list --format json`, `budgetbook --data ledger.json budget list --format csv`. It may stand before or after the positional arguments of the command. The value must be exactly `text`, `json` or `csv`. Any other value (`xml`, `JSON`, an empty string) is wrong usage and is handled like other wrong usage: exit code 2, nothing on standard output, a message on standard error that contains the value given. Errors found while running, such as a damaged ledger file, behave as in text: the same exit code, the same `error: ...` line on standard error, nothing on standard output. A result with no rows is not an error: exit code 0 in every format.

## JSON

Standard output is one JSON object followed by one newline, and nothing else. Indentation and spacing are free; non-ASCII characters may be written as they are or escaped. The keys appear in the order listed below, and every row object has its keys in the order listed.

- Amounts are strings in the form the text uses: `-42.80`, `2500.00`, two decimals, `-` for a negative amount, no thousands separator. They are never numbers.
- `id`, `count` and `year` are integers. Dates are `YYYY-MM-DD` and months are `YYYY-MM`.
- Rows come in the same order as in the text. Descriptions are never shortened: the cut-off at 30 characters is a text-only rule.
- `null` is used only where a shape below says so. An empty description is the empty string.

Shapes (row keys in parentheses):

- `list`: `transactions` (`id`, `date`, `amount`, `account`, `category`, `description`), `total` (sum of the listed rows), `count` (number of rows). No rows: `[]`, `"0.00"`, `0`.
- `top`: `categories` (`category`, `expenses`). Expenses are positive, as in the text. No rows: `[]`.
- `report`: `month`, `income`, `expenses`, `net`, `categories` (`category`, `total`). These are the figures of the text lines; each category total is signed, as in the text. A month with no bookings: three times `"0.00"` and `[]`.
- `summary`: `year`, `months` (`month`, `income`, `expenses`, `net`), `total` (an object with `income`, `expenses`, `net`). `months` always has the twelve months of the year, January first, with `"0.00"` where nothing was booked.
- `compare`: one flat object with `month` (the month asked for), `expenses`, `previous_expenses`, `change`, `change_percent`. `change_percent` is the percent of the text without the `%` sign, one decimal, rounded as in the text (`"22.7"`, `"-99.0"`), and `null` where the text says `not available`.
- `accounts`: `accounts` (`account`, `balance`), `total`. No rows: `[]` and `"0.00"`.
- `forecast`: `month`, `entries` (`date`, `name`, `amount`, `category`, `account`), `net`. No rows: `[]` and `"0.00"`.
- `budget list`: `budgets` (`category`, `limit`). No rows: `[]`.

## CSV

Standard output is the table of the command and nothing else.

- The first line is the header: the row keys listed for JSON, in that order, separated by commas (`id,date,amount,account,category,description` for `list`). Then one line per row, with the same values in the same order as the JSON rows. A `null` value and an empty description are both an empty field. No rows: the header line only.
- No title line, no total or net line and no label line. So the CSV of `report` has the `categories` rows only, the CSV of `summary` has the twelve month rows and no year row, and the CSV of `compare` is the header and one row.
- The separator is a comma. A field is wrapped in double quotes only when it contains a comma, a double quote or a line feed, and a double quote inside a field is written twice.
- Every line, the last one too, ends with a single line feed. There is no carriage return.
- Descriptions are not shortened.
