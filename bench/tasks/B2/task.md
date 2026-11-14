Add a `--limit N` option to `budgetbook list`.

- It keeps only the N latest transactions of the list: the last N by date, and by id among transactions on the same day. They are still printed oldest first, as now.
- The filters (`--from`, `--to`, `--category`, `--account`, `--search`) are applied first; the limit applies to what is left.
- The `Total:` line covers only the rows that are shown.
- When rows were left out, add one more line at the very end, after the `Total:` line: `Showing N of M`, where N is the number of rows shown and M the number that matched the filters. When nothing was left out, print no such line.
- N must be 1 or more. Otherwise exit with code 2 and print an error that mentions `--limit` on stderr.
