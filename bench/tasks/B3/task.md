Add a budget check to the monthly report: `budgetbook report 2024-03 --budgets`.

Without `--budgets` the report is unchanged. With it, the existing report lines are followed by:

- a line `Budgets:`, then one line per budget, sorted by category name, each in this form with single spaces between the fields: `<category> <spent> <limit> <percent>% <status>`, for example `food 412.50 400.00 103.1% OVER`
- or, when no budgets are set, the single line `No budgets set.` instead.

How the numbers are worked out for the month asked for:

- spent: minus the sum of all amounts in that category and in the categories below it (`food` includes `food/groceries`), for transactions dated in that month. Refunds (positive amounts) reduce it. It is never shown below 0.00.
- percent: spent divided by the limit, times 100, rounded to one decimal, halves rounded up (12.25 becomes 12.3). Always written with one decimal: `0.0%`, `80.0%`.
- status: `OVER` when spent is more than the limit. Otherwise `WARN` when the rounded percent is 80.0 or more. Otherwise `OK`.
- amounts have two decimals and no thousands separator, as everywhere else.
