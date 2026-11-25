# agentic-sdlc-kit

A Claude Code plugin and a written method for running software work with several AI agents. The method has fixed roles, a written task contract for each task, a review of every diff, records in plain files, and an independent audit at phase gates.

One maintainer ran the work. The text, the code and the bench tasks were written by AI agents under this process. The repository is built with its own process, and its task, decision, audit and log records are in the repository.

Status: version 0.1.1, experimental. The plugin was used on 2 real projects and measured on 2 synthetic projects, the bench sandbox and the eval repository. The limits are listed below.

## Who did what

The maintainer set the rules, the roles and the gates, ran the trials on their own projects and in their own terminal, and approved every task before it was committed. Other points from the records:
- After a small test looked bad for the kit, the maintainer asked for a large rebuild task, and the rule for it was fixed before any run on it (DEC-070, DEC-078).
- The maintainer asked why a limit in a contract had no reason behind it. The limit was removed and the lesson is in `LESSONS.md`.
- The maintainer commissioned two external read-only reviews. Their 35 items (36 rows) are in `docs/review-items.md`, with the decision or task that covers each. For 12 rows no record names the item.
- The maintainer decided against the lead's recommendation, for example on the eval login (DEC-054) and on the non-game trial project, where the lead first proposed another candidate (DEC-067).

## Result

On 6 tasks in one synthetic project, a plain prompt and the kit both passed 18 of 18 runs, by hidden tests. The bench rule was written before the first scored run. By that rule the result is "no difference".

No difference in task results on this set; the kit cost 3.30 times the tokens and 2.42 times the time (2.51 times in USD).

The kit did not reduce out-of-scope writes on this set. 2 of 18 runs had a file outside the task's allowed list in each arm, the same file, on the same task. What the kit adds is a written contract and records for each task, at that cost.

The main limit: the scope guard sees only Edit and Write calls. In the second real trial it saw 1 of 23 files that the developer role wrote. The rest went through the shell.

What was learned. The pilot of 4 runs before the scored runs had already shown both arms at 100%, so this set could not separate them. A next bench needs harder tasks, chosen by a pilot before the set is frozen. The scope guard missed shell writes, so the working-tree check at review (`/sdlc:review`) is the step that catches them, not the file-tool hook.

Full tables and limits: `docs/bench-results.md`.

## What it ships

- `agents/`: 7 role files (`cto`, `developer`, `tech-writer`, `scout`, `scribe`, `auditor`, `auditor-mini`). Each has a model and an effort level.
- `skills/`: 5 commands. `init` opts a project in. `contract` writes or closes the task contract. `review` compares the working tree with the contract. `status` reports the phase, the open task and the next step. `install-hooks` installs the pre-push guard.
- `hooks/`: `hooks.json` registers the scope guard on file writes and a session start hook. The session start hook adds a short text about the lead's role in a project that has `.sdlc/project.md`. `hooks/git/pre-push` is the pre-push guard. It rejects secrets and private patterns in the commits that no remote has yet. The `install-hooks` command installs a wrapper in the project's hooks folder and a copy of the guard script. It does not copy `hooks/git/pre-push` itself.
- `server/`: a read-only MCP server with 10 tools for records, scope and guard events. It is experimental and optional. It was tested with Claude Code only.
- `templates/`: the task contract, decision record, lesson entry, audit report and other templates.
- `PLAYBOOK.md`: the method itself, not tied to one tool.

## Install and first steps

Requirements: Claude Code, git, Python 3.10 or newer as `python`, `python3` or `py -3` (the hook checks for it; tested with 3.10.4 only), and `sh` (on Windows, Git Bash). The hooks run through `sh`. All 7 roles use the model aliases `opus`, `sonnet` or `haiku`. The MCP server is optional and needs the `mcp` Python package: `python -m pip install "mcp>=2.3,<3"` (see below).

This repository is its own plugin marketplace. In a Claude Code session, add it and install the plugin:

```
/plugin marketplace add gokhansail/agentic-sdlc-kit
/plugin install sdlc-lead@agentic-sdlc-kit
```

The same from the shell. The default scope is `user`, which enables the plugin in every project; `--scope project` writes `.claude/settings.json` of the current project instead:

```
claude plugin marketplace add gokhansail/agentic-sdlc-kit
claude plugin install sdlc-lead@agentic-sdlc-kit [--scope user|project|local]
```

Users get an update only when the plugin version is raised.

From a clone, load the plugin for one session:

```
claude --plugin-dir <path to the clone>
```

A clone can also be added as a marketplace with `/plugin marketplace add ./path/to/clone` (a local path starts with `./` or `../`).

The server needs the `mcp` Python package. Install it with:

```
python -m pip install "mcp>=2.3,<3"
```

Without the package the server exits at start with that one install line. `/mcp` then shows `sdlc` as failed to connect, and the install line explains why. The guard, the skills and the roles work without it.

The server is started as bare `python`. Where that name is missing, or is another interpreter than the one that holds `mcp`, the server fails to start, or fails although the package is installed. The hooks try `python`, `python3` and `py -3`; the server does not.

Then, in the project you want to work on:

1. `/sdlc-lead:init` opts the project in. It writes `.sdlc/project.md`, which maps the kit's record names to the project's own. It runs only when you type it, and it asks before writing.
2. `/sdlc-lead:contract <task>` writes the active contract: the files in scope and the files out of scope. The scope guard allows or denies each Edit and Write call against it. A write outside the contract is denied.
3. `/sdlc-lead:review` lists the files changed outside the contract and checks each acceptance line. It reads the working tree and runs the test command that the contract names.
4. `/sdlc-lead:status` reports the phase, the open task and the open questions from the project records.
5. `/sdlc-lead:install-hooks` installs the pre-push guard in the project's git repository. It runs only when you type it. `--refresh` replaces a stale copy and `--uninstall` restores the old hook folder.
6. `/sdlc-lead:contract close` closes the contract when the task is approved.

## What was measured

Bench (`docs/bench-results.md`). One synthetic project, a household budget ledger of 20 modules. 7 tasks with hidden tests, 2 arms (plain prompt, and the kit with its roles, guard and server), Sonnet in every role, 3 repeats. The 6 tasks together: 18 of 18 full passes in each arm, the kit at 3.30 times the tokens, 2.42 times the time and 2.51 times the cost in USD. Scope: 2 of 18 runs with an out-of-scope file in each arm. The large rebuild task is reported apart: 3 of 3 passes in each arm, 2.15 times in USD, 3.78 times the tokens and 2.83 times the time. On the two easiest tasks the same ratios were 3.00, 4.36 and 4.39, so all three were lower on the large task. That is 3 runs per arm, a description and not an effect. The pre-registration is in the decision record (DEC-078).

Server eval (`docs/eval-results.md`). 30 questions about a small synthetic repository, 3 repeats, with and without the server. Sonnet answered 90 of 90 correctly in both conditions; with the server the cost was 0.785 USD against 1.138 USD. Haiku answered 83 of 90 with the server and 87 of 90 without. A follow-up on the 8 scope questions with Haiku, 5 repeats, 40 runs per condition: with the default prompt and the server, 32 of 40 correct, and all 8 wrong runs made no server call. With either of two prompt variants, 40 of 40, and a server call in 40 of 40 runs. Without the server, 40 of 40. The two questions that were wrong are about writes. Guidance that follows: with Haiku, say in the prompt that the server tools answer questions about scope and records. Without that, Haiku skipped the tools in half the runs.

Before and after numbers (`EVIDENCE.md`). Counts from the record files of two earlier game projects and of this repository, before and after the process changed. They are descriptive. They do not show that the process caused any change.

Two real-project trials. The first ran on a game project (`docs/dogfood-1.md`): 1 medium task, 39 scope guard events (38 allow, 1 deny), 0 files out of scope, 158 tests (155 passed, 3 skipped), 4 pushes through the pre-push guard, none rejected. It gave 9 findings. The second ran on a project that is not a game, a Python tool with browser code (`docs/dogfood-2.md`): 2 medium tasks, 18 guard events (all allow), 0 files out of scope, 1 push, none rejected. It gave 5 findings, the main one being the shell-write gap below.

## Limits

- The scope guard checks the file-tool calls (Write, Edit, NotebookEdit) only. A write through the shell is outside its view. In the non-game trial it saw 1 of 23 files the developer wrote. A scan of past runs found a shell-write candidate in 39 of 50 of this kit's own developer runs. A fix is planned for the next version.
- The guard checks against the contract that the lead session itself writes. It does not know the task's real scope. It catches a mistake and is not a security boundary.
- A hook timeout lets the write through. Without Git Bash on Windows the hook does not run.
- The pre-push guard scans the commits that no remote has yet. A first push of existing history to a second remote is not scanned, because the commits another remote already has are skipped. A fix is planned for version 0.1.1 (DEC-080).
- 3 skills (`contract`, `review`, `install-hooks`) approve command patterns wider than the scripts they name. While such a skill is active, a `python` command that holds the script path as text could run without a permission prompt. This was not tried live. The patterns are to be narrowed in version 0.1.1 (DEC-080). See `docs/security.md`.
- The bench used one synthetic project and one model (Sonnet). Everything was run on one Windows machine with Claude Code versions 2.1.296 to 2.1.327. Other platforms and versions are not tested.
- Both bench arms passed every task, so the set did not separate them. The scope measure uses a list of allowed files that neither arm sees.
- A Sonnet `developer` agent wrote the bench sandbox, tasks, hidden tests and reference patches from the lead's contract. The maintainer approved them. No bench run was used to build them. Both arms ran the same Sonnet model.
- The kit was changed twice after a result was seen on B1, a task of the scored set (DEC-068 guard deny text, DEC-073 seat text and contract check text). 8 kit-arm runs and 2 plain runs on B1 came before the scored run and are not scored. The task set was not changed.
- The maintainer ran the trials. Both trial projects belong to the same maintainer.
- The server is experimental and optional, read only, and tested with Claude Code only. In the eval, Haiku with the default prompt answered fewer questions correctly with the server than without.
- Two findings of the first trial are not fixed in this version: `/sdlc-lead:contract` writes English field names into a tasks file in another language and places the entry under the previous step; and in default permission mode the developer role triggered a prompt for each new command shape, which the maintainer found tiring. Details are in `docs/dogfood-1.md`.
- After the public release the bench and the eval are not rerun to change a published result (DEC-059).

## Repository layout

| Path | Holds |
|---|---|
| `agents/`, `skills/`, `hooks/`, `server/`, `templates/` | the plugin and its parts |
| `tools/` | the scope guard, the pre-push guard, record readers, bench and eval runners, metric scripts |
| `tests/` | the test suite |
| `bench/`, `eval/` | the synthetic project and tasks for the bench; the questions for the server eval |
| `evidence/` | totals from the metric scripts |
| `docs/` | measured results, toolchain notes, security notes, source map |
| `PLAYBOOK.md` | the method |
| `EVIDENCE.md` | before and after numbers and how they were counted |
| `TASKS.md`, `DECISIONS.md`, `LOG.md`, `STATUS.md`, `LESSONS.md`, `CHANGELOG.md` | the kit's own records: tasks, decisions with reasons, what happened, current state, lessons, changes per version |
| `audits/`, `cto/` | audit reports and CTO plans |

The records are kept as the kit was built. They use task and decision IDs; the other documents use words.

## Tests and license

```
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

MIT license, see `LICENSE`.
