# Lessons

Fixture in the format of templates/lesson-entry.md and of this repository's own lessons file. The entries are invented.

## Entry template

### YYYY-MM-DD - short title

- Problem: what went wrong or slowed down.
- Cause: why it happened.
- Fix: what was done.
- Lesson: the rule to follow next time.

### 2026-01-12 - A stale cache hid a changed record

- Problem: the answer showed an old decision.
- Cause: the reader kept the parsed file between calls.
- Fix: the reader parses on every call.
- Lesson: a read tool holds no state between calls.

## A limit copied without its reason
- Date: 2026-01-20
- Project: Project A
- Problem: a cap of 3 was copied into a contract.
- Cause: the reason for the cap belonged to another task.
- Fix: the cap was removed.
- Lesson: write the reason next to a limit.
