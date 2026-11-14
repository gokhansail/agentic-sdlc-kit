# Eval runbook

What is this file? The steps the customer follows in PowerShell to run the eval of DEC-012 and DEC-054: 30 questions about a project's records, asked to a model with and without the sdlc server. Each step is a block to paste. Every block starts with a folder check and does nothing when the folder is wrong.

## What the runs do
- The runner is `tools/eval_run.py`. One run is one `claude -p` call on one question.
- The runs use the subscription login. They do not use `--bare` and they do not use an API key. The runner removes `ANTHROPIC_API_KEY` and `ANTHROPIC_AUTH_TOKEN` from the environment it gives to `claude`, so a key left in the window is not used. If a run's start event reports an API key as the credential, the runner stops.
- `total_cost_usd` in the totals is the CLI's list-price estimate. It is not a bill. Every run counts against the subscription usage limits.
- Each run works in a fresh copy of `eval/repo/` in the system temp folder, outside this repository. The model cannot see the question file, the answer keys or the kit.
- Both conditions get the same prompt and the same flags. The model gets the `Read` tool only. The prompt lists the files of the copy. The only difference is `--mcp-config`, which starts the sdlc server with the copy as its root and adds its 10 read-only tools.
- Models: `haiku` and `sonnet`. Full run: 2 models x 2 conditions x 3 repeats x 30 questions = 360 runs (DEC-056). `full-1` (120 runs, 1 per cell, DEC-055) was the first measurement and is not used for the gate.
- Raw output and one record per run go to `%TEMP%\sdlc-eval-out\<label>\`. They stay on this machine. Only the totals go to `eval\results\<label>.json`.
- A call starts only if the estimated USD spent so far plus the per-run cap (`--max-run-usd`, default 0.25) stays within `--budget-usd`; otherwise the runner stops and says so. The CLI checks its cap between turns, so one run can pass the cap by the cost of its last turn, and the total can pass the budget by that amount. It also stops after 3 calls in a row that fail with no cost, which is what a reached usage limit, a lost login or a broken CLI looks like.

## 1. Check the folder, the key variable and the tools
Open PowerShell and go to the kit folder first (`cd <kit folder>`). Then paste:

```powershell
if (-not ((Test-Path .\tools\eval_run.py) -and (Test-Path .\eval\questions.jsonl))) {
  Write-Host "STOP: this is not the kit folder. Run: cd <kit folder>"
} else {
  Remove-Item Env:ANTHROPIC_API_KEY -ErrorAction SilentlyContinue
  Remove-Item Env:ANTHROPIC_AUTH_TOKEN -ErrorAction SilentlyContinue
  Write-Host "API key variables removed from this window (the runner drops them too)"
  claude --version
  python --version
  python -c "import mcp.server.mcpserver; print('mcp package ok')"
}
```

- If `mcp package ok` is missing, run `python -m pip install "mcp>=2.3,<3"`.
- To check the login beforehand, start `claude`, type `/status`, read which account it shows, then leave with `/exit`. The runs use that login.

## 2. Pilot: 20 runs, budget 3 USD
5 questions, one from each of the 5 largest categories (scope, decisions, findings, tasks, guard events), 2 models, 2 conditions, 1 run each. The budget is in estimated USD; the pilot should use far less.

```powershell
if (-not ((Test-Path .\tools\eval_run.py) -and (Test-Path .\eval\questions.jsonl))) {
  Write-Host "STOP: this is not the kit folder. Run: cd <kit folder>"
} else {
  python tools/eval_run.py --label pilot-1 --budget-usd 3 --questions pilot --repeats 1 --models haiku,sonnet | Tee-Object -FilePath "$env:TEMP\eval-pilot-1.log"
}
```

The runner prints one line per run, then one line per model and condition, then a `done:` line and a `totals:` line. The log file `%TEMP%\eval-pilot-1.log` holds the same lines and no raw model output.

Look at the end of it:

```powershell
if (-not (Test-Path .\eval\results\pilot-1.json)) {
  Write-Host "STOP: eval\results\pilot-1.json is missing. Run this from the kit folder, after step 2."
} else {
  Get-Content "$env:TEMP\eval-pilot-1.log" -Tail 8
}
```

Check before going on:
- `errors` is 0 for every line, and `unparsed` is low. A high `unparsed` means the model did not end with the `ANSWER:` line.
- The estimated cost per run in the pilot sets the budget of the full run: cost per run x 360, plus some margin.
- The time per run in the pilot sets the length of a sitting: multiply it by 18 for the full run.

## 3. Full run: 360 runs
The budget is 8 USD (estimated; the per-run cap is 0.25 USD), already filled in below (DEC-056).

```powershell
if (-not ((Test-Path .\tools\eval_run.py) -and (Test-Path .\eval\questions.jsonl))) {
  Write-Host "STOP: this is not the kit folder. Run: cd <kit folder>"
} elseif (-not (Test-Path .\eval\results\pilot-1.json)) {
  Write-Host "STOP: run the pilot (step 2) first"
} else {
  python tools/eval_run.py --label full-2 --budget-usd 8 --questions all --repeats 3 --models haiku,sonnet | Tee-Object -FilePath "$env:TEMP\eval-full-2.log"
}
```

- 360 runs count against the subscription usage limits, so the full run may need more than one sitting. When a limit is reached, the runner prints `stopped: errors` after 3 failed calls. Wait until the limit resets, then continue the same label with the same command plus `--resume`. Runs already done are not repeated, and their estimated cost counts against the budget.
- If you stop it with Ctrl+C or the window closes, the totals so far are written. Continue with `--resume` the same way. On a timeout and on Ctrl+C the runner ends the `claude` process and every process it started (the sdlc server included) and waits for them before it goes on or exits.
- `--resume` is refused (exit code 2, before any call) when `manifest.json` in the output folder is missing or the eval set, a setting or the code a run depends on differs from the first run of the label: questions, models, conditions, repeats, `--max-turns`, `--max-run-usd`, `--timeout-s`, `--no-restricted`, `--seed`, the prompt and flags, and the content of the runner, the server, the `tools` modules the server imports and the `eval/` folder (not `eval/results/`). The message names what differs. Only `--budget-usd` may change, and a commit of other files, such as the records, does not block it. The git commit is written to the manifest and the totals as information only. After a refusal, start a new label.
- `--seed` (default 0) sets the order of the two conditions: across all (repeat, question, model) cells, half start with the server condition and half without (one more when the count is odd), placed by the seed. The same seed gives the same order. Keep the default unless the Technical Lead says otherwise.
- If it prints `stopped: budget`, the budget was too low for the whole run. The totals file says how many runs are done (`done_runs` against `planned_runs`). Do not start a new label; use `--resume` with a higher `--budget-usd`.
- Do not start other long Claude sessions on the same account while the full run runs. They share the usage limit.

## 4. What to send back to the Technical Lead
Send these two things and nothing else:

1. The path of the totals file: `eval\results\pilot-1.json` after the pilot, `eval\results\full-2.json` after the full run.
2. The last lines the runner printed (the one `<model> <condition>` line for each group, the `done:` line and the `totals:` line). Paste them from the window or from the log:

```powershell
if (-not (Test-Path .\eval\results)) {
  Write-Host "STOP: this is not the kit folder. Run: cd <kit folder>"
} else {
  Get-Content "$env:TEMP\eval-full-2.log" -Tail 8
}
```

Do not send the folder `%TEMP%\sdlc-eval-out\`. It holds the raw model output.

## 5. Haiku scope runs with prompt variants (T-54c)
Why: in `full-2`, Haiku with the server got 4 more scope runs wrong than without it (Q02 and Q07, T-54a). These 4 commands ask the 8 scope questions (Q01 to Q08) 5 times each, on Haiku only, in 4 prompt forms: 40 runs per command. `--prompt-variant` is `default`, `files-are` ("The files are: ..." in place of "Use only these files: ...") or `use-tools` (default plus one sentence that the sdlc tools answer questions about scope, contracts and records). `use-tools` is refused with the `no-server` condition. The `scope_check` tool description now says when to use it and that `actor` is `sub-agent` or `main`, so every server run here sees the new description.

Budget: the `full-2` Haiku rate was 0.0009 USD per run with the server and 0.0013 without, so 40 runs cost about 0.05 USD. Each command gets 0.50 USD (the per-run cap is 0.25 USD, and a call starts only if that fits in the budget). Each label has its own output folder, so the 4 commands do not touch each other. Only the totals go to `eval\results\<label>.json`; do not send the folder `%TEMP%\sdlc-eval-out\`.

The 8 scope IDs are `Q01,Q02,Q03,Q04,Q05,Q06,Q07,Q08`. Run the 4 blocks one after the other:

```powershell
if (-not ((Test-Path .\tools\eval_run.py) -and (Test-Path .\eval\questions.jsonl))) {
  Write-Host "STOP: this is not the kit folder. Run: cd <kit folder>"
} else {
  python tools/eval_run.py --label haiku-scope-noserver --budget-usd 0.5 --models haiku --repeats 5 --conditions no-server --prompt-variant default --questions Q01,Q02,Q03,Q04,Q05,Q06,Q07,Q08 | Tee-Object -FilePath "$env:TEMP\eval-haiku-scope-noserver.log"
}
```

```powershell
if (-not ((Test-Path .\tools\eval_run.py) -and (Test-Path .\eval\questions.jsonl))) {
  Write-Host "STOP: this is not the kit folder. Run: cd <kit folder>"
} else {
  python tools/eval_run.py --label haiku-scope-server --budget-usd 0.5 --models haiku --repeats 5 --conditions server --prompt-variant default --questions Q01,Q02,Q03,Q04,Q05,Q06,Q07,Q08 | Tee-Object -FilePath "$env:TEMP\eval-haiku-scope-server.log"
}
```

```powershell
if (-not ((Test-Path .\tools\eval_run.py) -and (Test-Path .\eval\questions.jsonl))) {
  Write-Host "STOP: this is not the kit folder. Run: cd <kit folder>"
} else {
  python tools/eval_run.py --label haiku-scope-filesare --budget-usd 0.5 --models haiku --repeats 5 --conditions server --prompt-variant files-are --questions Q01,Q02,Q03,Q04,Q05,Q06,Q07,Q08 | Tee-Object -FilePath "$env:TEMP\eval-haiku-scope-filesare.log"
}
```

```powershell
if (-not ((Test-Path .\tools\eval_run.py) -and (Test-Path .\eval\questions.jsonl))) {
  Write-Host "STOP: this is not the kit folder. Run: cd <kit folder>"
} else {
  python tools/eval_run.py --label haiku-scope-usetools --budget-usd 0.5 --models haiku --repeats 5 --conditions server --prompt-variant use-tools --questions Q01,Q02,Q03,Q04,Q05,Q06,Q07,Q08 | Tee-Object -FilePath "$env:TEMP\eval-haiku-scope-usetools.log"
}
```

Send back, for each label, the totals file path (`eval\results\<label>.json`) and the last lines of its log, as in step 4.

## Limits
Measured on Claude Code 2.1.319 (`docs/toolchain.md`, V-16). These are facts about what the runs are, and they belong with any result.
- The runs are not isolated from the account. The start event of a run lists the CLI's own bundled skills, slash commands and agents, and the model's context holds that listing and the account's e-mail address. None of the user's own agents, plugins, skills, MCP servers or global `CLAUDE.md` reached the 3 runs that were checked. No flag is known that removes the bundled listings, and none was worked around.
- The model gets `Read` only, by choice (DEC-054): both conditions have the same single tool, so the eval measures the server and not a difference in tools. Without the server the model finds facts by reading the files named in the prompt.
- `total_cost_usd` is an estimate at list price, and usage limits may end a sitting early.
- On Windows, if `claude` exits by itself while a process it started keeps the output pipe open, the runner cannot find that process by the parent's PID. The call then waits up to the timeout and 30 s more, and that process is not ended by the runner.
- The totals come from one synthetic project and 30 questions. A result is a sample.
