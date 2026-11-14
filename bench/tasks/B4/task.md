The monthly report lists some categories twice. In my data `food/groceries` shows up as two lines, `food/groceries` and `food / groceries`, and the amount is split between them. I think the grouping in `report` is broken. Please look at how the report adds up the categories.

Expected: one line `food/groceries` with the sum. The names get into the ledger in several ways (typed with `add`, imported from CSV, old data files), and the same category should come out the same way whichever way it got in.
