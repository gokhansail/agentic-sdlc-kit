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
- Not verified: what happens when an imported file is missing. T-05 avoids the question by using `CLAUDE.local.md` (see DEC-014).
