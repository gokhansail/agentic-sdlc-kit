# Lessons

What is this file? The lessons log of Tallybook. The technical lead writes an entry after a task, only when the customer steered the fix.

## Test data looked like real customer data
- Date: 2026-09-20
- Project: tallybook
- Problem: a fixture held names and addresses that looked real.
- Cause: the fixture was copied from a screenshot of a demo account.
- Fix: the fixture was replaced by generated values.
- Lesson: fixtures are generated, never copied from a screen.

## Rounded lines did not add up to the total
- Date: 2026-10-18
- Project: tallybook
- Problem: the printed total was 2 cents away from the exact sum of the lines.
- Cause: each line was rounded before the sum.
- Fix: the rule was changed to round once at the total (DEC-008, task T-7).
- Lesson: state where rounding happens before writing the first total function.

## A migration script ran against the wrong database
- Date: 2026-10-25
- Project: tallybook
- Problem: the first staging migration ran against the test database.
- Cause: the connection string came from an environment variable left over in the shell.
- Fix: the script now prints the target database name and asks for it again.
- Lesson: any destructive script prints its target and waits for the name.

## A fixture clock leaked between tests
- Date: 2026-11-02
- Project: tallybook
- Problem: two tests passed alone and failed together.
- Cause: a fixture set the clock and never reset it.
- Fix: the clock fixture resets in its teardown.
- Lesson: every fixture that changes global state restores it.
