# Lessons

What is this file? General lessons from building agentic-sdlc-kit: problems met, their causes, the fix, and what to do next time. Each lesson is one entry. Only general points go here; project-specific detail stays in `LOG.md`.

## Entry template

### YYYY-MM-DD - short title

- Problem: what went wrong or slowed down.
- Cause: why it happened.
- Fix: what was done.
- Lesson: the rule to follow next time.

### 2026-10-30 - A limit copied from the plan without its reason

- Problem: the T-10 contract capped lessons in the source map at 3. Three process lessons were left out, although they are the origin of three rules in the map. The maintainer asked why and the cap had no answer.
- Cause: the TL copied the cap from the day-0 plan into the contract without checking that its reason applied to the source map. The reason (a short playbook) belonged to T-11, not to T-10.
- Fix: the cap was removed (DEC-017); all 6 process lessons are in the map; G1 reviews the choice.
- Lesson: when a plan limit moves into a contract, write its reason next to it. A limit whose reason does not apply to the task is dropped or asked about, not copied.

### 2026-11-09 - A stop that did not stop the eval pilot

- Problem: the maintainer said to stop everything while the pilot ran as a background shell task. The TL stopped the task and reported no process left. The Python runner went on and finished all 20 runs; the TL found its totals file only after the next commit.
- Cause: stopping the background shell did not end the Python child on this machine (Windows, Git Bash). The TL's check looked for the runner by command line, matched nothing, and the TL took the empty answer as proof.
- Fix: the facts were corrected in LOG, STATUS and TASKS and told to the maintainer; the runs used the subscription login (`apiKeySource` none), 0.157 USD at list price.
- Lesson: after a stop, prove it from the output: the run's own files (`runs.jsonl`, the totals file) must stop changing. An empty process search is not proof. Long runs go to the maintainer's terminal, where a stop is a closed window.

### 2026-11-10 - A run plan recommended without the gate criterion

- Problem: the TL recommended 120 eval runs, 1 per cell (DEC-055), and the maintainer chose it. After the run, the eval table could not meet G4-8 and DEC-012, which ask for at least 3 runs per cell. The 120 runs did not count for the gate and the eval was rerun with 360 runs (DEC-056).
- Cause: the recommendation followed two external reviews and the pilot numbers. The TL did not reread the phase gate and the decision that set up the eval before giving the option.
- Fix: DEC-056 reruns the eval as `full-2` with 3 repeats; `full-1` stays as the first measurement; the gate criterion was not relaxed after the result.
- Lesson: before an option changes how a task is measured, read the gate criterion and the decision that set the task up, and name them in the option. A cheaper option that fails the gate is stated as failing it.

### 2026-11-17 - Records in Files out blocked the technical lead

- Problem: during T-57 the TL could not write a task result into `TASKS.md`; the scope guard denied it with "the path is in Files out of T-57".
- Cause: the TL listed the kit records in the contract's Files out to keep the developer away from them. Files out applies to the main session as well as to sub-agents, and it wins over everything else, so the TL locked its own records for the life of the contract.
- Fix: the TL did not work around the guard; it wrote the record after the contract closed.
- Lesson: keep the TL's own records out of Files out. A sub-agent already cannot write a file that Files in does not name, so listing the records in Files out adds nothing for the sub-agent and blocks the TL.
- Repeated 2026-11-25 in T-74: `TASKS.md` again in Files out; the TL's mid-task contract edit was refused. The template does not warn about it; a check in `--check-contract` that flags record files in Files out would catch it.


### 2026-11-26 - Example addresses in records tripped the pre-push guard 3 times

- Problem: after T-75 the push was refused 3 times in a row: a test-case address written as plain text in the `TASKS.md` result line, then in the `CHANGELOG.md` line, then in the commit message.
- Cause: the TL copied the developer's example cases into the records as written; the test file built them from pieces, the records did not.
- Fix: each one was reworded into words and the unpushed commit amended; the push then passed.
- Lesson: in records and commit messages, describe a guard test case in words, never as the literal string the guard looks for. Before a push, grep the staged diff and the message for the guard's own patterns.

### 2026-11-27 - A clipboard check that measured the copied command

- Problem: in the T-67 dev test the clipboard helper looked broken: after `copy S8` the key check gave `False`, and after `copy step` the clipboard held 27 characters instead of 675. A probe from the TL's shell showed the helper writes the clipboard correctly.
- Cause: the maintainer copied each command from the chat with the copy button, which replaced the clipboard with the command text; 27 is the length of the length check itself. A screenshot taken between `copy` and the paste does the same, and one stray command went to the session as a human message.
- Fix: the copy and the check were put on one line, so the helper writes after the line is copied; `copy step` ran from a second window right before the paste.
- Lesson: in a run guide, any step that fills the clipboard comes last before the paste, with no copy or screenshot in between, and a check of the clipboard runs on the same line as the command that fills it.
