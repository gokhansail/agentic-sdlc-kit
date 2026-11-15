# Task contract

What is this file? The written order for one task. The technical lead fills it before dispatch. The customer's go-ahead covers this one task. A filled contract has at most 15 lines; if it needs more, split the task.

## <task ID> <task title>
<!-- The task ID is capital letters, one dash, digits and an optional lower-case letter, for example `T-12` or `T-12a`; with no tasks record, number from `T-1`. -->
- Size: <easy, medium or hard; the label sets effort>
- Goal: <one line: what is true when the task is done>
- Files in: <files the developer may change or create>
- Files out: <files the developer must not touch>
- Acceptance: <what can be observed when the task is done>
- Tests: <which tests run, and what green means>
- Design reference: <document or section that backs the design>
- Flag: <name of the toggle if behaviour or cost changes, or "none">
- Customer test: <what the customer checks by hand>

Sources: [C-08, C-40, C-52]
