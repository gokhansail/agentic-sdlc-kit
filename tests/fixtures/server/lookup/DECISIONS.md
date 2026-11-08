# Decisions

Fixture in the format of templates/decision-record.md. The entries are invented.

## DEC-001 Pick the storage format
- Date: 2026-01-05
- Raised in: T-1
- Options: a) plain files b) a database
- Decision: a) plain files.
- Reason: a reader needs no server.
- Consequences: the server reads files. DEC-002 asks about a cache.
- Outcome: checked after T-3, the files stayed under 1 MB.

## DEC-002 Cache the parsed records
- Date: 2026-01-07 · Question: D-2
- Options: a) cache b) parse on each call
- Decision: b). DEC-001 keeps the reader simple.
- Reason: the files are small.
- Consequences:
  - no cache to invalidate
  - the reader parses on every call
- Outcome:

### DEC-003 Answer limit
- Date: 2026-01-09
- Options: a) 100 items b) no limit
- Decision: a).
- Reason: an answer must fit in a model context.
- Outcome: <leave empty until reviewed>

## DEC-010 Revisit the cache after the first release
- Date: 2026-01-15
- Decision: wait. DEC-2 and DEC-1 stay as they are; DEC-100 is a different decision.
- Outcome: reviewed 2026-01-20,
  the cache is still not needed.
