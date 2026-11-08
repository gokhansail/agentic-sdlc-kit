## T-7 Invoice rounding
- Size: medium
- Goal: an invoice total is rounded once, at the total, and the line amounts are shown unrounded to the cent below (DEC-008).
- Files in: `src/billing/*.py` `src/billing/tax/*.py` `src/api/{routes,schemas}/invoices.py` `tests/billing/**` `docs/billing/` `CHANGELOG.md`
- Files out: `src/billing/invoice_pdf.py` `src/billing/tax/legacy_*.py` `migrations/` `src/api/routes/admin.py`
- Acceptance: the sum of the printed line amounts may differ from the total by at most one cent; the total equals the rounded exact sum.
- Tests: `python -m pytest -q tests/billing` green; 3 new tests for the rounding cases.
- Design reference: DEC-008 in `DECISIONS.md`.
- Flag: none
- Customer test: create an invoice with three lines of 33.333 and read the total on the screen.
