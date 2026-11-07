# Re-verification: Gate G3, fix round T-34a

- Date: 2026-11-07
- Auditor: `auditor-mini` sub-agent, model Claude Opus 5.5, effort high
- Checks: the 2 conditions of `audits/2026-11-07_gate3.md` (G3-7, P-1), C-1, D-3, a regression check, and one line per remaining Low finding.
- State checked: uncommitted working tree on top of 4639428 (14 modified files plus the untracked gate report). Gate commit: pending the customer's word.
- Run: `python -m pytest -q` in this folder: 515 passed, 1 skipped. Fresh clone of a scratch commit of the working tree (`git stash create`, unreferenced, no ref or stash entry added; `core.autocrlf` true): 515 passed, 1 skipped. Guard `--files` over the 15 changed and new files: exit 0. No model call was made; Project A was not read.

## Findings

| Finding | Claim | Evidence | Status |
|---|---|---|---|
| G3-7 (condition 1) | The customer's statement recorded with date and CLI version | DEC-043 outcome: on 2026-11-07 the customer stated that the rehearsal and the Project A task ran in a PowerShell window they opened, and that the plugin loaded, the guard worked and the push passed; CLI 2.1.296 and 2.1.319 for P-33, 2.1.319 for T-33. LOG 2026-11-07 (5) records that the statement was given and where it sits. Versions agree with LOG 2026-11-07 (2) line "CLI 2.1.296 ... 2.1.319 after an update on restart" and `docs/toolchain.md`. By DEC-043 the auditor checks only that it is recorded. | CLOSED |
| P-1 (condition 2) | LOG and STATUS know T-33b and DEC-045 | `grep -c`: T-33b in `LOG.md` 4, `STATUS.md` 1; DEC-045 in `LOG.md` 3, `STATUS.md` 1 (gate: 0 each). LOG 2026-11-07 (5) covers triage, T-33b with metrics line, the writer brief, the toolchain section, the audit and T-34a. `STATUS.md` "Next" no longer says triage; Now line names the fix round and `auditor-mini`. | CLOSED |
| P-1 | The 4 routed findings on the phase 5 line | `TASKS.md` Later phases, Phase 5, T-51: findings 3, 6, 7 and 9 named, each with a short description, source `docs/dogfood-1.md`, DEC-045. | CLOSED |
| P-1 | Dogfood note points to DEC-045 | `docs/dogfood-1.md` line 63: "Findings, triaged in DEC-045 (...)", with the routing of all 9. | CLOSED |
| P-1 | DEC-035, DEC-039, DEC-044, DEC-045 outcomes filled | All 4 non-empty; DEC-043 also updated. DEC-035: `agents/` source, sync test green. DEC-039: no bypass flag built. DEC-044: see D-3. DEC-045: T-33b done, D-2 open, 4 findings on the phase 5 line. | CLOSED |
| P-1 | Rehearsal clone status recorded | LOG 2026-11-07 (5): the clone was already gone when the TL looked; the TL deleted nothing. Who removed it is not recorded; the condition asked for its status. | CLOSED |
| C-1 | `python -m pytest -q` green in a fresh Windows clone | `.gitattributes` adds `*.md text eol=lf` and `*.txt text eol=lf`, nothing else. Clone: `git ls-files --eol` gives `i/lf w/lf attr/text eol=lf` for the 5 `SKILL.md` files and `templates/guard-patterns.txt` (gate: `w/crlf`). The 7 LF tests pass there; full suite 515 passed, 1 skipped (gate: 6 failed). This folder: 515 passed, 1 skipped. Note: 17 tracked files still check out CRLF in the clone (14 `.json`, `LICENSE`, `.gitignore`, `.gitattributes`); no test reads them for LF and C-1 did not ask for them. | CLOSED |
| D-3 | Toolchain CLI line, DEV_RULES pointer, DEC-044 result on 2.1.319 | `docs/toolchain.md` line 16: "2.1.319 (2026-11-07; 2.1.296 before)". `DEV_RULES.md` line 1: "`agents/*.md` (copied to `.claude/agents/`)". DEC-044 outcome: measured on 2.1.296; on 2.1.319 strict validate adds `ICON_MISSING` (not blocking) and README advice; plain validate exit 0; T-51 decides. | CLOSED |
| Regression | Guard, role sync, evidence | Guard `--files` over 15 files: exit 0. `tests/test_role_sync.py`: 9 passed (here and in the clone). `git diff 2bd234e -- EVIDENCE.md evidence/`: empty; `git diff 2bd234e HEAD` on the same paths: empty; `git status` on them: empty. Project A manifest (untracked, ignored raw folder) SHA-256 starts with `042dcfa8`. `tests/test_scope_guard.py`: 143 passed. | CLOSED |

Low findings (not conditions):
- P-2: CLOSED. LOG 2026-11-07 (5) records the `tech-writer` brief outside the T-33b contract, 1 round, and names P-2.
- P-3: OPEN. No change; listed for the maintainer in LOG 2026-11-07 (5).
- P-4: OPEN. `LESSONS.md` unchanged.
- D-1: OPEN. Customer question; in `STATUS.md` open questions.
- D-2: OPEN. Customer question; in `STATUS.md` open questions and the DEC-045 outcome; Appendix H and `init` do not mention globs.
- R-1: OPEN. No runbook folder check, no lesson entry; the commit itself needs no rewrite.

Notes, not findings: `CHANGELOG.md` line 31 (an older entry) still says "9 findings for triage"; the gate report named it in evidence, not in the recommendation. `STATUS.md` dropped the T-02 to T-05 done lines and is at 59 lines, under its 60-line limit.

## VERDICT

ACCEPT. 9 closed, 0 open, 0 partial. With G3-7 recorded, the 9 G3 criteria pass; no change in this round touches the other 8.

The gate commit is still pending the customer's word.

Stays open: dogfood finding 1 (DEC-037 memory folder), D-1, D-2, P-3, P-4, R-1 for the maintainer; findings 3, 6, 7 and 9 on the phase 5 line; N-5 for G5.
