# Developer rules

What is this file? The short rules file of Tallybook, a small invoicing service. The developer reads only this file and its contract.

## Reading
- Allowed: the contract and this file only.
- Not read: `audits/`, `LOG.md`, `STATUS.md`, `DECISIONS.md`.

## Rules
1. Money is stored as integer cents (DEC-002). No floats in the billing package.
2. Touch only the files named in the contract.
3. Python 3.10; type hints; `pytest -q`.
4. No network calls in tests.

## Enforcement
- Hooks: the scope guard enforces rule 2. Where `.sdlc/project.md` exists, the plugin's scope guard also enforces the files rule.
