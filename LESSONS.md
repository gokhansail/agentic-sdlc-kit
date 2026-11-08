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
