# Dogfood 1

What is this file? Totals from running the kit on a project it was not built in (DEC-034). It holds no file names, no record text and no before/after claim. Numbers in `EVIDENCE.md` do not change because of it.

## Rehearsal (P-33)

| Field | Value |
|---|---|
| Date | 2026-11-07 |
| CLI version | 2.1.296 for the session steps; 2.1.319 after an update on restart, for the uninstall |
| Target | throwaway clone of this repository: renamed records, a non-English record line, an existing pre-push hook, a local bare repository as the only remote |
| Terminal | a PowerShell window the customer opened, not the desktop app |
| Task size | easy, 1 contract |
| Contract lines | 10 |
| Scope guard events | 5: 1 allow, 4 deny |
| Events by state | no contract 2, active contract 3 |
| Events by writer | sub-agent 4, main session 1 |
| Events with a path | 0 |
| Review rounds | 1 |
| Questions back | 2, both by the sub-agent after a denial; neither got past the guard |
| Out-of-scope files | 1, planted through Bash, named by `/sdlc:review` |
| Pushes | 1 clean, passed with the non-English line, the old hook ran; 1 with a fake key, rejected with file, line and pattern name |
| Install | second run reported no change |
| Footprint | the list of DEC-033: 6 items under `.sdlc/`, 1 exclude line, the hook wrapper and 1 saved hook |
| Rollback | hook folder hash-equal, `core.hooksPath` unset, `git status` empty |
| Customer result | passed; every step matched the runbook |

Limits:
- The session ran in the CLI's auto mode, so fewer permission prompts appeared than in default mode. Default mode was not observed.
- Sonnet ran the session. Another model may follow a skill less closely.
- `/sdlc:init` and `/sdlc:contract` wrote their files with a Bash heredoc, not the Write tool. The scope guard did not see those writes. They were allowed paths, so no result changed. T-30b fixed this after the rehearsal.
- A clone of this repository is not a foreign project. The mismatch test is T-33.
- No main-session write outside the root was tried, so whether that deny blocks useful work is not settled. The customer reported no wrong denial.

## Real task (T-33)

| Field | Value |
|---|---|
| Date | 2026-11-07 |
| CLI version | 2.1.319 |
| Target | Project A's own repository, under the exception of DEC-033: a game project with its own records under other names and in another language, its own developer rules file and an existing pre-push hook |
| Terminal | a PowerShell window the customer opened, not the desktop app |
| Sessions | Project A's TL session on Opus, effort high; `sdlc:developer` on Sonnet; `sdlc:scribe` on Haiku |
| Task size | medium, 1 contract, picked by the customer from 3 candidates |
| Contract lines | 10 |
| Scope guard events | 39: 38 allow, 1 deny |
| Events by state | no contract 4, active 35 |
| Events by writer | main session 6, developer 15, scribe 18 |
| Events by tool | Write 4, Edit 35 |
| Events with a path | 0 |
| Deny | 1, before the contract: the main session's note to its own memory folder, outside the project root. The task was not blocked; the note stayed in the session. |
| Wrong denials | 0 |
| Review rounds | developer 3: the first, 1 fix for a gap the TL review found, 1 change the customer asked for. This exceeds the 2-round rule. Scribe 2: the TL review found 2 wrong statements in the first. |
| Questions back | 0 formal; 1 decision passed to the customer |
| Out-of-scope files | 0. One file changed before the task stayed out by name; `--check-worktree` reports it every time. |
| Tests | 158: 155 pass, 0 fail, 3 skipped |
| Pushes | 4 through the chained hook, the branch 2 and main 2; 0 rejected |
| Merge | fast-forward to main after the customer's word |
| Footprint | the list of DEC-033 |
| Rollback of the kit | hook folder hash-equal, `core.hooksPath` unset, exclude file and `git status` equal to the state noted before the task. The task's change stays in Project A by the customer's choice. |
| Customer result | passed; the customer tested the change and reported no problem |

Findings, triaged in DEC-045 (finding 4 fixed in T-33b; 3, 6, 7 and 9 on the phase 5 line of `TASKS.md`; 2, 5 and 8 stated limits; 1 decided in DEC-046 and built in T-39):
1. The outside-root deny also covers the session's own memory folder. This answers the open DEC-037 question: the deny hits ordinary work, though not this task.
2. Writes made by the game engine are not seen by the guard: generated metadata files in batch mode, and a settings file the editor saved again after the customer's test. That re-saved file stopped the branch switch until it was committed.
3. Project A's TL session did not know the kit. It planned to write the contract by hand, which leaves the guard in the no-contract state. The kit TL corrected this and 3 other steps from outside; the kit does not yet introduce itself to a session.
4. The `init` brief put the developer rules file in the always-allowed list; it was removed before the write. Project A's TL asked for 4 more entries, refused for this task.
5. `--check-worktree` cannot tell a file changed before the task from a task change, so a clean task still exits 1.
6. `/sdlc:contract` writes English field names and kit sizes into a tasks file in another language, and it placed the entry under the previous step instead of at the end.
7. Default permission mode asked for each new command shape, and the developer searched for the engine binary on disk each time. The customer called this tiring. A tools section in `.sdlc/project.md` and a narrow allow list are candidates.
8. The developer wrote an engine asset by hand, although Project A's developer rules ask for engine-side writes.
9. The customer asked for a plan budget, for example questions per step and sessions without code, so that process does not replace work. Not measured here.

Limits:
- One task on one project. A kit TL watched every step and corrected 4 of them; a customer alone would have met finding 3.
- The permission mode changed near the end, from default to accept-edits to auto.
- The Windows console select mode froze the session twice until Esc. This is not kit code.
