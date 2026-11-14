`budgetbook list --from 2024-03-01 --to 2024-03-31` leaves out the transactions dated 2024-03-31. Both dates are meant to be included in the range. The `Total:` line at the end of the list is off by the same amount.

Please fix it. A range with `--from` and `--to` on the same day should show that day's transactions.
