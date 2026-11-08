# Status

What is this file? The current state of Tallybook on one page. A new session reads this first and resumes from here.

Last updated: 2026-10-24
Now: Phase 2 Billing open; G2 conditional, fix round T-5a re-verified, two findings not closed · repository private · code written, tests green

## Phase

Phase 1 Core closed: G1 passed 2026-09-25.

Phase 2 Billing open: audit `audits/2026-10-20_gate2.md`, re-verification `audits/2026-10-24_gate2_reverify.md`.

## Done

- T-1 repository and data layer; decisions DEC-001 to DEC-003.
- T-2 invoice model and line items.
- T-3 invoice numbering; DEC-004.
- T-4 PDF rendering from HTML; DEC-005.
- T-5 tax tables for three countries.
- T-5a fix round 1 for G2: P-1, D-1 and C-2 closed, C-1 partly.

## Open questions

- None.

## Next

Start the Postgres migration, then rounding at the total.
