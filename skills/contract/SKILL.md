---
description: Write the task contract into the tasks record and .sdlc/active-contract.md, or close it with the word close.
allowed-tools: Read, Write, Edit, Bash(python *tools/scope_guard.py*), Bash(python3 *tools/scope_guard.py*), Bash(py -3 *tools/scope_guard.py*)
---
# contract

Arguments: `$ARGUMENTS` (the task, or the word `close`). Needs `.sdlc/project.md`; if it is missing, say
`/sdlc:init` comes first and stop.
Every write below uses Write or Edit, never a shell command: the scope guard sees file tools only.

## Open (default)
1. If `.sdlc/active-contract.md` exists: stop. Name its task ID. Say `/sdlc:contract close` first.
2. Read `${CLAUDE_PLUGIN_ROOT}/templates/task-contract.md`. Fill the lines under its `##` heading from the
   customer's text: task ID and title, Size, Goal, Files in, Files out, Acceptance, Tests,
   Design reference, Flag, Customer test. Ask once for anything missing, mainly Files in.
   Every path in Files in and Files out is in backticks. At most 15 lines.
3. Tasks record (name in `.sdlc/project.md`): read it, then Edit it to append the contract as a
   `### [ ] <ID> [size] <title>` entry with the same lines.
4. Write `.sdlc/active-contract.md` with Write: one heading `## <ID> <title>` and the lines. Nothing else
   (no template preface, no Sources line).
5. Run `python "${CLAUDE_PLUGIN_ROOT}/tools/scope_guard.py" --check-contract --root .`
   (if `python` is not found, try `python3`, then `py -3`). Run it alone, no `; echo` or `&&` after it.
   Show its output. If it exits 1, fix the
   active file and run it again.

## Close
Only when `$ARGUMENTS` is `close`. Ask: "Remove the active contract?" After a yes, delete
`.sdlc/active-contract.md` with a shell command (no file tool deletes). Do not edit the tasks record.
