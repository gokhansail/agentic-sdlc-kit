# Dogfood 2

What is this file? Totals from running the kit on 2 real tasks in a second project it was not built in, Project C, a non-game project (DEC-067, DEC-074). It holds no paths, no record text and no commit hashes from Project C, and no before/after claim. Numbers in `EVIDENCE.md` do not change because of it. The form follows `docs/dogfood-1.md`.

## Setup, both tasks

- Terminal: a PowerShell window the customer opened.
- Account: a subscription account, no API key.
- Permission mode: the CLI's auto mode.
- Session: Project C's own TL session on Opus, with the plugin loaded by `--plugin-dir`.
- Developer: Project C's own developer role did the work, not `sdlc:developer` (DEC-074).
- Hooks: `/sdlc:install-hooks` was skipped. The kit's chained pre-push guard was already installed there.

## Task 1: range render

| Field | Value |
|---|---|
| Date | 2026-11-18 |
| CLI version | 2.1.319 |
| Task size | medium, mostly Python, with tests |
| Contract | 14 Files in (including the lock file and `pyproject.toml`), 5 Files out |
| Developer | Sonnet, effort high |
| Duration | 20 min |
| Commits | 1 local commit, 17 paths |
| Scope guard events | 11: 11 allow, 0 deny |
| Events by state | no contract 2, active 9 (main session 8, developer 1) |
| Events by writer | main session 10, developer 1 (Write) |
| Tests | 341 and lint green (Project C TL's run) |
| Review rounds | 1 |
| Questions back | 0 |
| Out-of-scope files | 0 |
| Customer result | passed |

## Task 2: 16th grid cells as wide as 8th

| Field | Value |
|---|---|
| Date | 2026-11-18 |
| CLI version | 2.1.326 |
| Task size | medium, JS, view math |
| Contract | 9 Files in, 6 Files out |
| Duration | developer 9 min, TL session 15 min |
| Commits | 1 local commit, 10 paths |
| Scope guard events | 7: 7 allow, 0 deny |
| Events by state | no contract 2 (contract writes), active 5 (main session, records) |
| Events by writer | main session 7, developer 0 |
| Tests | 342 passed, 1 deselected; 6 of 6 new node unit tests for the view math; lint green (Project C TL's run) |
| Review rounds | 1 |
| Questions back | 0 |
| Out-of-scope files | 0 |
| Decision | 1 open design question: Project C's TL took its own default and told the customer, who agreed |
| Customer result | passed, tested in the browser |

## Trial total

| Field | Value |
|---|---|
| Scope guard events | 18: 18 allow, 0 deny |
| Events by tool | Edit 15, Write 3 |
| Wrong denials | 0 |
| Task 3 | not run, by the customer's choice: the task is hard and has an open shortcut question; 2 tasks give the evidence |
| Pushes | 1 at the end, 2 commits, passed through the chained hook; 0 rejected |
| Rollback of the kit | hook folder hash-equal, exclude file equal, `.sdlc/` file list equal to the noted state, `git status` empty |
| Task commits | stay in Project C by the customer's choice |

Findings, not yet triaged (main one first):
1. The developer wrote files through the shell, which the guard does not see. In task 1, 15 of 16 developer-written files changed through Bash (Python heredoc replace scripts, `sed -i`), 1 through Write, 0 through Edit, although the TL's brief said file tools only. In task 2, 7 files were developer-written and the developer produced 0 guard events. Together the guard saw 1 of 23 developer-written files. No deny came before these writes, so this is habit, not evasion. Project C's developer role file has no file-tools rule; the kit's `developer` role has one. Scope still held: all 27 committed paths were in Files in or always allowed, by the developer's choice, not because the guard checked them. A history scan of past transcripts (read only, pattern match, upper bound, includes temp files) found developer runs with at least one shell-write candidate: Project C 33 of 34, another project of the maintainer 12 of 13, this kit 39 of 50. The gap is general, not a Project C habit.
2. `/sdlc:init` proposed a lessons path outside the project root. This is harmless, because the root lock refuses it, but init should not propose it. It kept the developer rules file out of the always-allowed list on its own, so T-33 finding 4 did not repeat.
3. Project C's TL asked whether an external agent or itself runs task 1, because its own handoff note named an external agent. The customer answered. Compare T-33 finding 3.
4. Task 1's contract left `README.md` out of Files in. One documentation item was not done and was reported as out of contract. Scope held; the cost was one item left for later.
5. `/sdlc:contract` added its contract lines under Project C's existing entry in its tasks file, in that file's language. This is T-33 finding 6 again, in a milder form.

Limits:
- 2 tasks on one project.
- The plugin ran over an existing TL process written by the same author.
- Project C's developer role ran, not the kit's (DEC-074).
- Auto mode only. Default mode was not observed.
- The CLI version changed between the tasks.
- No deny happened, so the deny path was not exercised in a real task.
- No browser tests in task 2: node unit tests for the view math, plus the customer's test.
- Test counts are Project C TL's runs. The kit TL did not rerun them, so that nothing is written in Project C.
- A kit TL watched from outside and read Project C's contract and event file read only.
- The history scan is an upper bound.
