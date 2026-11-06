---
description: Install, refresh or remove the pre-push guard in this project's git repository (typed command only).
disable-model-invocation: true
allowed-tools: Bash(python *tools/install_git_hooks.py*), Bash(python3 *tools/install_git_hooks.py*), Bash(py -3 *tools/install_git_hooks.py*)
---
# install-hooks

Arguments: `$ARGUMENTS` (empty, `--refresh` or `--uninstall`). Typed by the customer only.

1. Run, from the project root (the top folder of the git working tree):
   `python "${CLAUDE_PLUGIN_ROOT}/tools/install_git_hooks.py" --target . $ARGUMENTS`
   If `python` is not found, try `python3`, then `py -3`. Run it alone: no `; echo` or `&&` after it.
2. Show the installer's output unchanged, in a code block. A failed run shows its exit code in the
   tool result; quote that. Add nothing to the output.
3. Only after the output, in one line each:
   - exit 1 means nothing was written or the copy is stale; the output names the reason;
   - a stale copy is replaced by the same command with `--refresh`;
   - `--uninstall` leaves the pattern files and the `.sdlc/` exclude line; the output lists them.
4. Do not run `git push`, do not edit `.git/`, do not retry with another flag on your own.
