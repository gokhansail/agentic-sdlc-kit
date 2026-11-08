# Log

What is this file? A dated record of what was asked, decided, built and checked. Newest entry on top. Entry format: `## YYYY-MM-DD (N) - title`, where N counts entries for that day.

## 2026-11-04 (1) - T-7 first pass

- `developer` (Sonnet) changed the rounding in `src/billing/invoice.py` and added 3 tests.
- DEC-009 recorded: reminders by email only.
- One write to `src/billing/invoice_pdf.py` was denied and reported as an open question.
- Metrics: developer, effort medium; review rounds 1 so far; guard 10 events for T-7 (7 allow, 3 deny).

## 2026-11-03 (1) - T-7 contract

- The TL wrote the T-7 contract and placed `.sdlc/active-contract.md`.
- DEC-008 recorded: round at the invoice total.
- Metrics: not a contract task yet; TL work.

## 2026-10-28 (1) - T-6 done

- Postgres migration finished; staging run on 2026-10-27 lost no row.
- Two writes were tried while no contract was active; one was denied.
- Metrics: developer, effort medium; review rounds 2; guard 6 events for T-6 (5 allow, 1 deny).

## 2026-10-24 (1) - G2 re-verification

- `auditor-mini` checked the 5 findings of the G2 audit: 3 CLOSED, C-1 PARTIAL, S-1 OPEN.
- Gate verdict stays conditional. STATUS updated the same day.
- Metrics: not a contract task; audit work.

## 2026-10-23 (1) - T-5a fix round 1

- `developer` (Haiku) fixed P-1, D-1, C-2 and part of C-1.
- Metrics: developer, effort low; review rounds 1; guard 2 events for T-5a (1 allow, 1 deny).

## 2026-10-20 (1) - G2 audit

- `auditor` reported 5 findings and a conditional verdict (`audits/2026-10-20_gate2.md`).
- Metrics: not a contract task; audit work.
