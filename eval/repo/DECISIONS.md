# Decisions

What is this file? The decisions of Tallybook, one entry each, newest at the bottom. Written by the Technical Lead. The outcome is filled later, when the decision can be judged against what happened.

## DEC-001 Storage for version 1
- Date: 2026-09-02
- Raised in: T-1
- Options: a) SQLite file b) Postgres
- Decision: a) SQLite file.
- Reason: no server to run during the first three phases; one file is easy to back up.
- Consequences: all queries go through one small data layer so the engine can change later.
- Outcome: Replaced by DEC-006 on 2026-10-22. The second writer in the test setup locked the file.

## DEC-002 Money as integer cents
- Date: 2026-09-02
- Raised in: T-1
- Options: a) decimal strings b) integer cents
- Decision: b) integer cents in every table and every function.
- Reason: no float rounding in sums.
- Consequences: display code divides by 100 and formats once.
- Outcome: Held through T-6. No float found in the billing package.

## DEC-003 Language of the records
- Date: 2026-09-03
- Raised in: T-1
- Options: a) English b) the maintainer's language
- Decision: a) English for code, documents and records.
- Reason: one language for every reader of the repository.
- Consequences: reports to the maintainer may still be in another language.
- Outcome: Held.

## DEC-004 Invoice number format
- Date: 2026-09-10
- Raised in: T-3
- Options: a) `YYYY-NNNN` b) random token
- Decision: a) `YYYY-NNNN`, a four-digit counter per year.
- Reason: readable numbers a customer can say aloud.
- Consequences: the counter is stored per year; a gap is an error.
- Outcome: Replaced by DEC-007. The four-digit counter overflowed in the load test data.

## DEC-005 PDF engine
- Date: 2026-09-18
- Raised in: T-4
- Options: a) render HTML to PDF b) draw the page directly
- Decision: a) render HTML to PDF.
- Reason: the template is the same file the web view uses.
- Consequences: a headless renderer is a build dependency.
- Outcome:

## DEC-006 Postgres replaces SQLite
- Date: 2026-10-22
- Raised in: T-6
- Options: a) keep SQLite b) move to Postgres now c) move after phase 3
- Decision: b) move to Postgres now; replaces DEC-001.
- Reason: two writers locked the SQLite file in the test setup; the move is cheaper now than after phase 3.
- Consequences: a migration script (T-6); the data layer keeps its interface.
- Outcome: Migration ran on staging on 2026-10-27 with no row lost.

## DEC-007 New invoice number format
- Date: 2026-10-24
- Raised in: T-6
- Options: a) `INV-YYYY-NNNNNN` b) keep `YYYY-NNNN` with a five-digit counter
- Decision: a) `INV-YYYY-NNNNNN`; replaces DEC-004.
- Reason: six digits remove the overflow and the prefix tells an invoice number from a year.
- Consequences: the migration renumbers nothing; old numbers stay as they are.
- Outcome: Held; the load test passed with 1,000,000 numbers.

## DEC-008 Round at the invoice total
- Date: 2026-11-03
- Raised in: T-7
- Options: a) round each line b) round once at the total
- Decision: b) round once at the total.
- Reason: rounding each line made the total differ from the exact sum by up to 2 cents (see LESSONS, 2026-10-18).
- Consequences: line amounts are shown with more digits than the cent; the printed lines may not add up to the total by one cent.
- Outcome:

## DEC-009 Payment reminders by email only
- Date: 2026-11-04
- Raised in: the maintainer, during T-7
- Options: a) email only b) email and SMS
- Decision: a) email only for the first release.
- Reason: SMS needs a provider contract that is not signed.
- Consequences: the reminder scheduler (T-9) has one channel.
- Outcome:
