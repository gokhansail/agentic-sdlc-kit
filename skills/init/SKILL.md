---
description: Opt this project in to the sdlc plugin by writing .sdlc/project.md (typed command only).
disable-model-invocation: true
allowed-tools: Read, Glob, Grep
---
# init

Opt the current project in. Typed by the customer only. Arguments: `$ARGUMENTS`.

1. If `.sdlc/project.md` exists: stop and say so. Do not read it again, do not change it.
2. Find the project's records: look in the project root for the status, tasks, log, decisions and
   changelog files and the developer rules file. Find the test folders (for example `tests/`).
   Use the template's default name when a file does not exist.
3. Read `${CLAUDE_PLUGIN_ROOT}/templates/project.md`. Fill every angle-bracket part and each record
   name that differs. Keep the `## Always allowed` section to backticked globs, one list item each.
   Report language: the language the customer writes in, unless the customer names another.
4. Show the whole proposed file. Ask: "Write it?" Write nothing before the customer's yes. If the
   arguments above already hold the customer's yes, that is the answer.
5. After a yes, write `.sdlc/project.md` (create `.sdlc/` if needed).
6. Tell the customer, in 3 lines:
   - the scope guard is now on: a write needs an active contract (`/sdlc:contract`) or a path in the
     always-allowed list;
   - deleting `.sdlc/project.md` turns it off;
   - `/sdlc:install-hooks` adds the `.sdlc/` line to the git exclude file, so `.sdlc/` is not committed.
