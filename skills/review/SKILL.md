---
description: Compare the working tree with the active contract and report out-of-scope files and each acceptance line (read only).
allowed-tools: Read, Grep, Glob, Bash(python *tools/scope_guard.py*), Bash(python3 *tools/scope_guard.py*), Bash(py -3 *tools/scope_guard.py*), Bash(git status:*), Bash(git diff:*)
---
# review

Read only. Approve nothing; the customer decides.

1. Run `python "${CLAUDE_PLUGIN_ROOT}/tools/scope_guard.py" --check-worktree --root .`
   (if `python` is not found, try `python3`, then `py -3`). Run it alone: no `; echo` or `&&` after it.
   Exit 0: every changed path is inside the
   contract. Exit 1: the lines it prints are paths outside the contract, or the reason there is
   no usable contract (then stop and say so).
2. Read `.sdlc/active-contract.md`. Read the diff: `git diff` and `git status --short`.
   Ignored files are not shown by git; say so if the contract expects one.
3. Run the test command the contract's Tests line names, and report its summary line. If it names
   none or cannot run, write "not run" and the reason.
4. Report, in short bullets:
   - files outside the contract (from step 1), including files changed through Bash;
   - each Acceptance item of the contract: met or not met, with the evidence (file, line, output);
   - tests: result or "not run";
   - anything in the diff the contract does not explain.
5. Do not edit files, do not stage, do not commit. End with "the decision is yours".
