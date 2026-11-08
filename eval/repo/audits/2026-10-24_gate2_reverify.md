# Re-verify table

What is this file? The check of named findings after the developer fixed them. The auditor-mini fills it. It starts no new review. The trigger is a state (fixes are done), not a date.

## Re-verify G2

| Finding | Claim | Evidence | Status |
|---|---|---|---|
| P-1 | `STATUS.md` lists T-5 | `STATUS.md` Done list ends with T-5 and T-5a | CLOSED |
| D-1 | the counter no longer overflows | DEC-007 (2026-10-24) replaces the four-digit counter with six digits; the load test passed | CLOSED |
| C-1 | an unknown country gives an error | `src/billing/tax/rates.py` raises for codes outside the table; the same lookup in `src/billing/tax/legacy_rates.py` still returns 0 | PARTIAL |
| C-2 | the linter passes | linter output: 0 findings | CLOSED |
| S-1 | the header is not logged | `src/api/middleware/logging.py` line 18 still logs all headers | OPEN |

Gate verdict: conditional
