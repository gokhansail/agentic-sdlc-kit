# Review items

What is this file? The list of the 35 items (item 19 has 2 rows, 19a and 19b, so the table has 36 rows) from two external read-only reviews of the repository (review 1 and review 2, 2026-11-09), with the decision or task that covers each item and its status. The original table is kept outside the repository, so the numbers in `DECISIONS.md`, `TASKS.md` and `LOG.md` are resolved here (G4 audit finding P-5). Status comes from those records as of 2026-11-20 (rows 10, 11, 18 and 32 brought up to date; the other rows are as of 2026-11-12). "No record" means no tracked record names the item; it does not mean the item was rejected.

| Item | Subject | Decision or task | Status |
|---|---|---|---|
| 1 | A run that ends with an error is not counted as correct | T-46c | done |
| 2 | The budget estimate uses the per-run cap for every call | T-46c | done |
| 3 | A stop ends the whole process tree | T-46d | done |
| 4 | Resume is refused when settings changed | T-46d | done |
| 5 | The order of the two conditions is mixed by a fixed seed | T-46d | done |
| 6 | Run count of the full eval | DEC-055, DEC-056 | done: 120 runs, then 360 runs (3 per cell) |
| 7 | The eval claim is narrow: this set-up only | T-46g | done |
| 8 | A tool call difference is not credited to the server | LOG 2026-11-10 (4) | done: correction in the LOG |
| 9 | Why `claude plugin eval` was not used | DEC-060 | done: own runner kept; isolation line in `docs/eval-results.md` (T-45c) |
| 10 | README: what it is, install, removal, what it does not protect | T-50 | done |
| 11 | Marketplace entry | DEC-057, T-51 | done |
| 12 | Dependency lock file or tested versions | none | no record |
| 13 | Plugin settings call a bare `python` | none | no record |
| 14 | README warning about a packaged-app install of the runtime | none | no record |
| 15 | Use the plugin in a consumer project for 2 weeks and count guard catches | none | no record |
| 16 | A rule that the kit never blocks a project | none | no record |
| 17 | Plugin or templates as the one source | DEC-057 | decided: plugin only |
| 18 | The server is experimental and optional; no growth | DEC-059, T-50 | decided; README wording done (T-50) |
| 19a | The scope guard is an early warning, optional if it catches nothing in 4 weeks | none | no record |
| 19b | A file check when a sub-agent ends | DEC-059 | deferred, not planned |
| 20 | CI on two operating systems with a fixed skipped-test count | none | partly: Windows only in `.github/workflows/tests.yml` (T-51) |
| 21 | Push guard in CI and a dependency scan once public | none | no record |
| 22 | Remove unused code | none | no record |
| 23 | No new capability and no new feature task | DEC-059 | decided |
| 24 | Ceremony scales with task size | DEC-058, T-47 | done |
| 25 | STATUS and LOG generated from git | none | no record |
| 26 | Empty decision outcome fields | DEC-058, T-47 | done: an empty outcome is normal |
| 27 | Two lessons wanted at gate G3 are not in the records | none | no record |
| 28 | The TL shows evidence before saying "stopped" or "done" | DEC-058, T-47 | done |
| 29 | Compare work with and without the process on real tasks | DEC-059 | deferred, not planned |
| 30 | Tokens and minutes in the task metric line | none | no record |
| 31 | Narrow, publish, freeze | DEC-059 | decided; publish open (phase 5) |
| 32 | Public git history | DEC-080 | decided: the full history is published |
| 33 | Move effort to the next project | DEC-059 | decided: after G5 |
| 34 | A short write-up of the findings | none | no record |
| 35 | Keep the review files outside the repository | G4 finding S-2 | done |

Sources: DEC-055 to DEC-060; T-46c, T-46d, T-46g, T-47, T-50 to T-52 in `TASKS.md`; `LOG.md`; `STATUS.md`; G4 audit finding P-5.
