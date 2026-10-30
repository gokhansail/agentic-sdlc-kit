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
