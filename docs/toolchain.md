# Toolchain

What is this file? The tools and versions this project relies on, each checked on the build machine or in the official documentation. Checked on 2026-10-29 (T-04). A line marked "not verified" must be checked before the task that needs it.

## Build machine

Checked by running each command.

| Tool | Version | Used for |
|---|---|---|
| Python | 3.10.4 (`python`; `python3` is a store stub on this machine) | guard, metrics scripts, MCP server |
| pytest | 9.2.0 | all tests (`python -m pytest -q`) |
| git | 2.35.1 (Git for Windows) | hooks, history scans; `claude plugin eval` needs 2.31+ |
| GitHub CLI | 2.95.0 | repository and release work |
| Node / npm | 24.18.0 / 11.16.0 | not used yet |
| Claude Code | 2.1.296 | plugin, hooks, headless runs; `claude plugin eval` needs 2.1.269+ |

Python dependencies are listed in `requirements-dev.txt`.

## MCP Python SDK (phase 4)

Checked with `pip index versions mcp`, the wheel metadata, and a smoke test in a throwaway virtual environment: one server with one tool, started over stdio from the SDK client, `list_tools` and `call_tool` both returned the expected result.

| Version | Requires-Python | Server class | Smoke test |
|---|---|---|---|
| 2.3.0 (latest) | >=3.10 | `MCPServer` (`mcp.server.mcpserver`); `FastMCP` was renamed in 2.x | passed |
| 1.30.0 (last 1.x) | >=3.10 | `FastMCP` (`mcp.server.fastmcp`) | passed |

Both ran with pydantic 2.14.2 and anyio 4.15.1. Which major version the server uses is decision DEC-013. Migration notes: https://py.sdk.modelcontextprotocol.io/v2/migration/

## Claude Code plugin (phase 3)

Source: https://code.claude.com/docs/en/plugins/manifest-reference.md unless noted.

- `.claude-plugin/plugin.json` is optional; the only required field is `name` (kebab-case). Check with `claude plugin validate <dir>` (`--strict` for CI).
- Components sit at the plugin root, not inside `.claude-plugin/`: `skills/<name>/SKILL.md`, `commands/` (older form; the docs prefer `skills/`), `agents/`, `hooks/hooks.json`, `.mcp.json`.
- `${CLAUDE_PLUGIN_ROOT}` is the installed plugin path; it changes on update, so no state is written there. `${CLAUDE_PLUGIN_DATA}` is for state. Neither is set for commands Claude runs through the Bash tool.
- Names are namespaced: skill `/<plugin>:<skill>`, agent `<plugin>:<agent>`.
- Plugin agents may set `model` (`sonnet`, `opus`, `haiku`, `fable`, a full ID, or `inherit`). Plugin agents ignore `hooks`, `mcpServers` and `permissionMode` in frontmatter. https://code.claude.com/docs/en/sub-agents.md
- Development load: `claude --plugin-dir <path>`, for one session, repeatable. https://code.claude.com/docs/en/cli-reference.md
- Marketplace: `.claude-plugin/marketplace.json` with `name`, `owner.name`, `plugins[]` (`name`, `source`, relative sources start with `./`). Install with `/plugin marketplace add owner/repo`, then `/plugin install <plugin>@<marketplace>`. The marketplace name comes from the file, not the repository. https://code.claude.com/docs/en/plugins/marketplace-reference.md, https://code.claude.com/docs/en/plugins/install.md

## Hooks (phase 3, scope guard)

Source: https://code.claude.com/docs/en/hooks.md

- `hooks/hooks.json` needs the top-level `hooks` wrapper: `{"hooks": {"PreToolUse": [{"matcher": "Edit|Write", "hooks": [{"type": "command", "command": "..."}]}]}}`.
- A matcher of plain names separated by `|` is an exact list. File-writing tools are `Write`, `Edit` and `NotebookEdit`. There is no `MultiEdit` in the current tool list (https://code.claude.com/docs/en/tools-reference.md).
- The hook gets JSON on stdin: `tool_name`, `tool_input.file_path` (absolute; backslashes on Windows), plus `cwd`, `session_id`, `hook_event_name`.
- To block: exit 2 with the reason on stderr, or exit 0 with `hookSpecificOutput.permissionDecision = "deny"`. Exit 2 wins over any JSON.
- On Windows a shell-form command runs in Git Bash, or PowerShell if Git Bash is missing. Default timeout 600 s.

## Plugin facts measured (P-30)

Measured 2026-11-04 and 2026-11-05 on Claude Code 2.1.296, Windows 10, Git Bash, with a throwaway plugin: 14 `claude -p` runs, plus one run in a terminal the maintainer opened. V-3 was completed on this repository in T-30. IDs are from `cto/2026-11-04_phase3-plan.md` section 5. V-7 fell away (DEC-039). V-10 and V-11 are checked in T-51.

| ID | Result | Measured |
|---|---|---|
| V-1 | confirmed, with a limit | `claude plugin validate --strict` exits 0 on the 7 role files, incl. `effort`, `tools` as a comma string and `model: fable`; `color` is not needed. A missing manifest `author` fails `--strict`. Validate does not check values: `model: banana` and `effort: ludicrous` raised no value finding, so a passing validate proves the form only. Its output lists only files with findings. `--strict` also fails on a `CLAUDE.md` or `CLAUDE.local.md` at the plugin root; see DEC-044. |
| V-2 | confirmed | An agent with `effort: low` wrote with `effort.level` low in the hook input; the main session had medium. An agent with `tools: Read` had only `Read` and could not write. An agent with `model: sonnet` under a main session on `--model haiku` ran on Sonnet: `modelUsage` lists both models. |
| V-3 | confirmed | `hooks/git/`, `tools/`, `tests/` and `.claude/` beside `hooks/hooks.json`: no validate finding, no load warning, and hook, skills and agents all loaded. This repository, with 7 role files in `.claude/agents/`, loaded with `--plugin-dir` and listed the 7 `sdlc:` agents. |
| V-4 | confirmed | PreToolUse fires inside a sub-agent. The input then has `agent_id` and `agent_type`; `agent_type` is namespaced, as `<plugin>:<agent>`. Main-session input has neither field. `NotebookEdit` carries `notebook_path`, `cell_id`, `new_source`, `edit_mode`; `Write` carries `file_path`, `content`; `Edit` carries `file_path`, `old_string`, `new_string`, `replace_all`. Other input fields seen: `transcript_path`, `permission_mode`, `effort`, `tool_use_id`. |
| V-5 | confirmed | The hook environment has `CLAUDE_PROJECT_DIR` and `CLAUDE_PLUGIN_ROOT` as a drive letter with forward slashes, also `CLAUDE_PLUGIN_DATA` and `CLAUDE_EFFORT`. `sh "${CLAUDE_PLUGIN_ROOT}/hooks/<script>"` ran. |
| V-6 | confirmed, with a limit | Exit 2 blocks and its stderr reaches the model. Exit 1, exit 127 and a timeout (limit 2 s, sleep 6 s) let the write through. So the hook fails open on a timeout, and a launcher cannot turn a timeout into a deny. A true process crash was not reproduced: `kill -9` on the hook shell did not kill it under Git Bash. |
| V-8 | confirmed for text, Bash environment not settled | `${CLAUDE_PLUGIN_ROOT}` in `SKILL.md` text is replaced with a forward-slash path, also inside a Bash command line written in the skill. The shell form `$CLAUDE_PLUGIN_ROOT` in a Bash command stopped at the permission check in `-p`, so whether the Bash tool has the variable is not settled. |
| V-9 | confirmed for a terminal, desktop not settled | `--plugin-dir` loads in `claude -p` from a session nested in the desktop app and from a terminal the maintainer opened; a plugin skill ran in both. No hook ran in that terminal. A desktop app session was not tried. |
| V-12 | confirmed | With `disable-model-invocation: true` the Skill tool refuses the skill and names the flag; a typed `/<plugin>:<skill>` runs it. |

Also seen: `claude -p` runs still load the user's own plugins. `claude --plugin-dir <path> plugin details <name>` shows the inventory and token cost without an install; the option goes before `plugin`. For this plugin with 7 agents: about 837 tokens added to every session. With `ANTHROPIC_API_KEY` set, the CLI warns that it takes precedence over the claude.ai login, and connectors are off.

## Scope guard, measured (T-31)

Measured 2026-11-06 on the same machine and CLI version.

- Time per call as the host starts it, 7 series of 20 calls: opted in, median 422 ms to 598 ms, the highest with other work running beside them; maximum 918 ms. Not opted in, one series: median 165 ms, maximum 221 ms. Budget 1 s (DEC-040).
- One direct call took 24.4 s while other work ran on the machine. It did not return in 200 later calls, and its cause is not known. This is why the hook timeout is 30 s and not close to the budget.
- The launcher starts Python twice: one version probe, one guard run.
- `python -I` ignores `PYTHONUTF8`, so the launcher also passes `-X utf8`.
- The `python3` store stub exits 49 on the version probe and is skipped.
- Live runs on Haiku: a main-session write with no contract denied, one inside a contract allowed, a sub-agent write outside the contract denied.

Limits: a hook timeout lets the write through (limit set to 30 s); without Git Bash on Windows the hook does not run; paths are compared as text, so a link, an 8.3 short name, a trailing dot or an alternate data stream can get past it; a write through Bash is not seen (DEC-038). In an opted-in project a path outside the root is denied for the main session too, which includes files the CLI keeps in the user's home folder.

## Git hook in another repository, measured (T-32)

Measured 2026-11-06 on Windows 10, Git Bash, git 2.35.1, Python 3.10.4, with `git push` to a local bare repository. No `claude -p` run.

- `python tools/install_git_hooks.py --target <repo>` leaves `core.hooksPath` unset. `git status` in the target stays empty.
- The old hook gets the same arguments and stdin bytes. A failing old hook stops the push with its own exit code, and the guard does not run.
- After `--uninstall` the SHA-256 of every file in the hook folder equals the values before install.
- The wrapper passes no arguments to the guard. A remote named `--files` would otherwise switch the guard to its manual mode and scan nothing.
- `--target` must be the top folder of the working tree.

Limits: `git push --no-verify` skips the wrapper. A linked worktree of a target fails closed, because `.sdlc/guard/` is per worktree. A new branch with no remote-tracking branches scans its whole history. The copy goes stale after a kit update until `--refresh` runs. An existing `.sdlc/guard-patterns.txt` is never replaced, so a clone of this repository keeps the kit's language pattern. A `forbid-path` line in a project replaces the built-in list. Run on Windows only.

## Plugin commands, measured (T-30a)

Measured 2026-11-06 on Claude Code 2.1.296, Windows 10, Git Bash: 9 `claude -p` runs on Haiku in throwaway repositories.

- All 5 skills ran as typed commands. `claude plugin details` lists 5 skills and 7 agents; about 1,031 tokens are added to every session, about 194 of them from the skills.
- `allowed-tools` in a plugin skill takes effect: the skill's named `python` command ran with no CLI permission for it. A compound command falls outside the pattern, so `; echo` or `&&` needs its own approval. The skills say to run the command alone.
- `disable-model-invocation: true` refused the model's call of `init` and `install-hooks`.
- In `--check-worktree` the rule is `decide()` in `tools/scope_guard.py`, the same one the hook uses.

Limits: one run could not show whether model-invoked `status` and `review` work: the Skill tool returned its normal start line and the model read that as a failure. The `close` run sent `yes` in the same input, so the question before the delete was not observed. A skill started with plain `python` has no `-X utf8`, so `tools/scope_guard.py` sets `backslashreplace` on its own output. `/sdlc:init` writes no exclude line. Ignored files are not seen by `/sdlc:review`. Not run in a terminal the customer opened yet: P-33.

## Rehearsal in the customer's terminal, measured (P-33)

Measured 2026-11-07 in a PowerShell window the customer opened, Windows 10, CLI 2.1.296, then 2.1.319 after an update on restart. Totals are in `docs/dogfood-1.md`.

- Load, the 5 commands, hook block and allow, a sub-agent deny and `git push` all worked there, which closes the terminal half of V-9. A desktop app session is still not tried.
- `/sdlc:init` and `/sdlc:contract close` each asked before writing or deleting.
- `/sdlc:init` and `/sdlc:contract` wrote through a Bash heredoc, which the scope guard does not see, because their `allowed-tools` did not name `Write`. T-30b added the tools: in 2 Sonnet runs on 2026-11-07 all 3 files went through `Write` or `Edit`, and no Bash command wrote them.

Limits: auto mode was on, so default-mode permission prompts were not observed.

## Headless runs and evaluation (phase 4, T-46)

Sources: https://code.claude.com/docs/en/headless.md, https://code.claude.com/docs/en/cli-reference.md, https://code.claude.com/docs/en/plugin-evals.md

- `claude -p "<prompt>" --output-format json --model <id> --mcp-config <file> --strict-mcp-config`. `--strict-mcp-config` ignores every other MCP configuration.
- `--bare` skips hooks, skills, plugins, other MCP servers and `CLAUDE.md`, but needs `ANTHROPIC_API_KEY`; it does not use the subscription login. Without `--bare`, a `-p` run loads the project's hooks and `.mcp.json` without asking.
- `--tools ""` removes built-in tools; MCP tools stay unless `--disallowedTools "mcp__*"`. `--max-turns` and `--max-budget-usd` cap a run.
- Result fields per the SDK result type: `duration_ms`, `num_turns`, `total_cost_usd`, `usage` (input, output, cache tokens), `modelUsage`, `is_error`. https://code.claude.com/docs/en/agent-sdk/typescript.md
- `claude plugin eval` runs suites from `evals/<case>/prompt.md` with graders, 3 runs per case by default, isolated home and config per run, results in `aggregate-result.json`. Every run is a model call billed to the account. Suites that grant shell tools need WSL2 on native Windows.
- Not verified: that `claude -p --output-format json` returns all the result fields above; that `--allowedTools "mcp__<server>__*"` works with a wildcard. Check both with one real run when T-46 starts.

## Memory files (T-05)

Source: https://code.claude.com/docs/en/memory.md

- `CLAUDE.local.md` is loaded automatically after `CLAUDE.md` in the same folder and is meant to be ignored by git.
- `@path` imports resolve relative to the importing file, up to four levels deep.
- Not documented: what happens when an imported file is missing. Nothing here depends on it; private instructions use `CLAUDE.local.md` instead (DEC-014).
