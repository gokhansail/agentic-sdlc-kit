# Tasks

Written by the Technical Lead. Each task is a contract of at most 15 lines: goal, files to touch and not to touch, acceptance, tests, tag. Tags: [E] easy, [M] medium, [H] hard. A phase gate that is still `[ ]` blocks the next phase. Decisions are in `DECISIONS.md`.

## NOW NEXT
T-6 done 2026-10-28. T-7 is in progress (contract placed 2026-11-03). Next after T-7: T-8, the second fix round for the G2 findings left open by the re-verification.

## Phases

| Phase | Goal | Gate |
|---|---|---|
| 1 Core | repository, data layer, invoice model, numbering | G1: passed 2026-09-25 |
| 2 Billing | tax tables, totals, rounding, Postgres | G2: audit 2026-10-20 conditional; fix round 1 re-verified 2026-10-24, 2 findings not closed |
| 3 Delivery | PDF, reminders, API docs | G3: not started |

## Task list

- [x] T-1 [E] repository and data layer. DEC-001, DEC-002, DEC-003.
- [x] T-2 [M] invoice model and line items.
- [x] T-3 [M] invoice numbering. DEC-004.
- [x] T-4 [M] PDF rendering from HTML. DEC-005.
- [x] T-5 [M] tax tables for three countries.
- [x] T-5a [E] fix round 1 for G2: findings P-1, D-1, C-2 and the first part of C-1.
- [x] T-6 [M] Postgres migration and new invoice numbers. DEC-006, DEC-007.
- [ ] T-7 [M] round at the invoice total. DEC-008.
- [ ] T-8 [E] fix round 2 for G2: findings C-1 and S-1.
- [ ] T-9 [M] reminder scheduler, email only. DEC-009.

## T-7 Invoice rounding
- Size: medium
- Goal: an invoice total is rounded once, at the total (DEC-008).
- Files in: `src/billing/*.py`, `src/billing/tax/*.py`, `src/api/routes/invoices.py`, `src/api/schemas/invoices.py`, `tests/billing/`, `docs/billing/`, `CHANGELOG.md`
- Files out: `src/billing/invoice_pdf.py`, `src/billing/tax/legacy_*.py`, `migrations/`, `src/api/routes/admin.py`
- Acceptance: the total equals the rounded exact sum of the lines.
- Tests: `python -m pytest -q tests/billing` green.
- Design reference: DEC-008.
- Flag: none
- Customer test: create an invoice with three lines of 33.333 and read the total.

## T-8 Fix round 2 for G2
- Size: easy
- Goal: findings C-1 and S-1 of the G2 audit are closed.
- Files in: `src/billing/tax/rates.py`, `src/api/middleware/logging.py`, `tests/billing/`, `tests/api/`
- Files out: `migrations/`, `src/billing/invoice_pdf.py`
- Acceptance: the re-verify table shows both findings CLOSED.
- Tests: `python -m pytest -q` green.
- Design reference: `audits/2026-10-20_gate2.md`.
- Flag: none
- Customer test: none
