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
