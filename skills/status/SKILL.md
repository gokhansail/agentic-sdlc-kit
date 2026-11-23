---
description: Report the phase, the open task, the next step and the open questions from the project records (read only).
allowed-tools: Read, Grep, Glob
---
# status

Read only. Do not write, run tests or change anything.

1. File names: if `.sdlc/project.md` exists, read its `## Records` section. Otherwise use the defaults:
   STATUS.md, TASKS.md, LOG.md, DECISIONS.md.
2. Read the status record, the "NOW NEXT" line or the first unchecked task of the tasks record, the top
   of the log record, and any decision whose outcome or decision line is empty.
3. Answer in the customer's language, in short bullets:
   - phase;
   - the open task, or the next one when none is open;
   - what was done last (from the log);
   - open questions and open decisions;
   - the next step, ending with "next is X, continue?".
4. If `.sdlc/project.md` is missing, say the scope guard is off for this project and that
   `/sdlc-lead:init` turns it on. If `.sdlc/active-contract.md` exists, name its task ID.
5. If a record is missing, say which one. Do not invent its content.
