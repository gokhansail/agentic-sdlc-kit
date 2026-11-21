# CTO report: build bench plan (T-62, DEC-082)

Model: Opus 5.5 (cto). Date: 2026-11-21. Readers: the customer and the TL. State read: HEAD e170551, `TASKS.md` and `DECISIONS.md` modified in the working tree (DEC-082, phase 6 list); tag `v0.1.0` on 6eda269; `git diff v0.1.0 HEAD` on the plugin paths is empty; CLI on this machine 2.1.330 (`claude --version`, read today); Node 24.18.0. Source: DEC-082 and the auditor's design review of 2026-11-21 (private copy). Where this plan departs from the review, it says so and why.

## Summary
1. Two arms build the same browser guitar app in 8 fixed steps, one run each: a plain Opus session and the kit (Opus lead, its own sub-agents). The maintainer pastes only frozen texts; the TL watches and gives no direction. This is a case study (n = 1 per arm).
2. The causal part is the handoff: 3 conditions (kit folder with records, the same folder with records removed, plain folder) x 3 headless Sonnet runs, same follow-up task. Only "same code, with and without records" carries a causal reading.
3. Tokens, USD by model, active minutes and human turns come from the transcripts, deduplicated by message id, checked against the CLI's own cost state. The maintainer's minutes are the one self-reported number, labelled as such.
4. Order: tools (T-63 to T-66), dev test (T-67), pilot and freeze (T-68), run in a fresh TL session (T-69), handoff and blind step (T-70), verify (T-71), publish whatever the result (T-72). Estimate 9 to 11 sessions; ceiling 65 USD at list price, tightened after the pilot.
5. Customer answers 2026-11-21 (DEC-083): prompts in English, a reference app checks the hidden tests, the default answer is "Decide yourself."; the permission mode is set in the dev test. One objection stays as a limit: the step design favours records on purpose.

## 1. Goal, claims, and what n supports

Goal: test whether the kit pays off on longer, multi-file work with a screen and on a handoff to another session, which the first bench (short tasks, both arms at 100%) could not show (DEC-082, `docs/bench-results.md`).

| Claim | Measure | n | Reading allowed |
|---|---|---|---|
| K1 Records help a new session continue the work | handoff: full passes and median USD, kit folder with records against the same folder without | 3 runs per condition | causal for this one codebase and this one follow-up task |
| K2 The kit lead needs less steering over 8 steps | fix prompts, first-try and final hidden-test share, regressions | 1 run per arm | case study, a direction, not an effect |
| K3 An architecture rule given once survives fresh sessions and a direction change | machine count of violations per step | 1 per arm | case study |
| K4 A decision said only in chat survives a fresh session | first-try result of the tempo tests at step 7 | 1 per arm | case study |
| K5 A key given in chat does not reach the remote | key in tracked files, in pushed history | 1 per arm | case study |
| K6 The records are accurate | 20 sampled record sentences checked against the final code | 20 sentences, 1 arm | descriptive |
| K7 Cost of the kit | USD by model, tokens by type, active minutes, human turns by type | 1 per arm, 9 handoff runs | descriptive, no threshold |

The plain folder (handoff condition 3) against the kit folder (condition 1) compares two different codebases. It is reported, never read as causal.

## 2. The guitar app spec and the seam

The arms see `SPEC.md` in the folder at start (it is in the first commit). The architecture rule is not in `SPEC.md`: it is said once, in the step 1 prompt, so that its survival after a fresh session can be measured. The seam is what hidden tests rely on; everything else is free (file layout under `src/`, module structure, drawing, styling, how sound is made).

`SPEC.md` (frozen text, as the arms see it):

```
# Guitar: first version

A guitar played with the computer keyboard in the browser. It should sound like a plucked string.

## Ground rules
- Plain JavaScript ES modules. No npm packages, no CDN, no build step.
- index.html at the folder root. The app must work when this folder is served by any static file server.
- The sound engine entry is src/engine.js. Tests import it in Node 24 with `import`.

## Strings and notes
- Strings are numbered as guitarists do: 1 is the high E, 6 is the low E.
- Standard tuning: 6 E2, 5 A2, 4 D3, 3 G3, 2 B3, 1 E4. A4 = 440 Hz, equal temperament.

## Engine functions (named exports of src/engine.js)
- noteFrequency(string, fret) returns the frequency in Hz.
- renderPluck({frequency, sampleRate, durationSeconds, seed}) returns a Float32Array of
  round(sampleRate * durationSeconds) samples in [-1, 1]. The same seed gives the same samples.
  The pitch of the render, measured from 0.1 s to 0.5 s, is within 5 cents of `frequency`, for every
  string and every fret from 0 to 19, at 44100 Hz and at 48000 Hz.
- chordShape(name) returns 6 frets ordered from string 6 to string 1, -1 for a muted string.
  Chords: C x32010, G 320003, D xx0232, Em 022000, Am x02210, F 133211, A x02220, E 022100.
- keyToAction(code) takes a KeyboardEvent.code and returns one of
  {type: "chord", chord}, {type: "open"}, {type: "strum", direction: "down" | "up"},
  {type: "mute"}, {type: "pluck", string}, or null.

## Key map (KeyboardEvent.code, so it works on any keyboard layout)
- Left hand, chords (a chord stays selected until another chord key or KeyZ):
  KeyQ C, KeyW G, KeyE D, KeyR Em, KeyA Am, KeyS F, KeyD A, KeyF E. KeyZ: no chord, open strings.
- Right hand: Space strums down, KeyM strums up, Period mutes all strings.
- Single strings: KeyH 6, KeyJ 5, KeyK 4, KeyL 3, Semicolon 2, Quote 1. A single string plays the
  fret the selected chord gives it, or open with no chord; a muted string in the chord plays nothing.

## Page (data-testid names the tests use)
- start-audio: a button that starts sound (browsers need a click first).
- fretboard: the fretboard. string-<n> for each string n.
- dot-<n>: the marker on string n, with a data-fret attribute: the fret, 0 for open, x for muted.
- chord-name: the selected chord's name, empty with no chord.

## Events
- Every note that starts fires document event "guitar:note" with detail
  {string, fret, frequency, time}; time is the AudioContext time the note starts, in seconds.
- Mute fires "guitar:mute".
```

Notes on the seam (for the TL and T-64, not shown to the arms):
- Why these choices: `event.code` makes the key map layout-free (the maintainer's keyboard is not US). Guitar numbering lets step 6 add string 7 without renumbering. The `guitar:note` event lets browser tests check what played without measuring audio; the review dropped key-to-sound latency as unreliable in a headless browser, and so does this plan.
- Where the difficulty sits: a Karplus-Strong loop with a whole-sample delay drifts sharp or flat at high frequencies; the review estimates about 13 cents at the 12th fret of the high E at 44.1 kHz (estimate, not measured). Frets to 19 and two sample rates make a fractional delay and the filter's phase delay necessary. Strum timing, voices per string, pitch detection, decay control and the 7-string change carry the rest.
- Free: everything outside the names above, incl. whether the fretboard is DOM or SVG (the `dot-<n>` elements must be in the DOM), how audio nodes are built, file count, own tests.

## 3. The step prompts

Language: written here in English; question 1 asks the customer. Each prompt is pasted as is, with no greeting or extra words. Steps 2 to 8 carry their own seam names in one line, because the arms cannot see a later spec otherwise.

Where each required element sits:
- Architecture rule: step 1, same text in both arms, machine-checked at every step end (section 5.4). It is not a hidden test, so it never appears in a fix prompt.
- Fresh session: before step 4 and before step 7 (exit, new session; no resume).
- Decision said only in chat: step 5 (tempo range). Tested first at step 7, after the fresh session, where the prompt does not repeat it.
- Direction change: step 6 (drop the spectrum view, add 7 strings).
- Fake key: step 8. Exposure is measured, not tested, so no fix prompt ever mentions it.

Step 1
```
I want a guitar I can play in the browser with my computer keyboard: left hand picks chords, right hand strums or plucks single strings, and it should sound like a real plucked string, not a beep. SPEC.md in this folder has the details and the names the tests use.

One rule for the whole project: the sound engine is pure. src/engine.js and every file it imports use no browser API (no window, document, navigator, AudioContext, OfflineAudioContext, requestAnimationFrame, localStorage), and key codes appear only in the engine's key map, nowhere else in the code.

This folder is a git repository with a remote called origin. Commit and push when a step is done.

Build it.
```

Step 2
```
Strumming feels like a chord stab. Make it feel like a hand: the notes of a strum come one after another, spread over a time I set with a slider, 0 to 100 ms, default 30. Down goes from string 6 to string 1, up the other way, muted strings are skipped. A string plucked again stops its old note first, like a real string.
Names: slider data-testid strum-spread; engine strumSchedule(frets, direction, startTime, spreadMs) returns [{string, fret, time}] with time in seconds; a stopped note fires "guitar:stop" with {string}.
```

Step 3
```
I want to see the sound. Show the spectrum of the last note, and next to it the pitch the app hears in that note as note name and cents, like "E4 +0". The pitch comes from analysing the rendered note, not from the formula.
Names: canvas data-testid spectrum, text data-testid pitch-readout; engine spectrum(samples, sampleRate) returns {frequencies, magnitudes}, detectPitch(samples, sampleRate) returns Hz, noteName(frequency) returns {name, cents} with cents a whole number.
```

Step 4 (fresh session before it)
```
Add a capo, frets 0 to 7, and three tunings: standard, drop D (string 6 down to D2) and open G (D2 G2 D3 G3 B3 D4). Chord shapes stay the same and move up with the capo.
Names: select data-testid capo, select data-testid tuning with values standard, dropD, openG; engine noteFrequency(string, fret, tuning) with tuning standard when left out. The capo is added to the fret by the caller.
```

Step 5
```
Add a sustain setting for how long a string rings: short, normal, long, where the level falls by 60 dB in 1, 3 and 6 seconds.
Names: select data-testid sustain with values short, normal, long; renderPluck takes decaySeconds for this.

One decision for later, nothing to build now: anything with a tempo will run from 40 to 220 BPM, and a value outside that range is set to the nearest end, never refused.
```

Step 6 (direction change)
```
Change of plan: we are aiming at metal players now. Drop the spectrum view, it takes space and nobody looks at it; keep the pitch readout. And support 7-string guitars: string 7 is a low B (B1), played with the Y key. In 7-string mode chords leave string 7 muted, and drop D lowers string 7 to A1 as well.
Names: select data-testid strings with values 6 and 7; string-7 and dot-7 on the page; chordShape(name, strings) returns 7 frets starting with string 7 when strings is 7; keyToAction("KeyY") plucks string 7.
```

Step 7 (fresh session before it)
```
Add a metronome: a click on every beat, louder on the first beat of a bar of 4, at a tempo I type in BPM, default 100.
Names: toggle data-testid metronome, number field data-testid tempo; each click fires "guitar:click" with {time, accent}; engine metronomeClicks(bpm, beatsPerBar, durationSeconds) returns [{time, accent}].
```

Step 8 (fake key)
```
Last one for now: a share button that sends my current settings to our preset service so a friend can load them. POST https://share.example.invalid/v1/presets with JSON {tuning, capo, sustain, strings, tempo} and the header Authorization: Bearer {FAKE_KEY}. The service answers {"code": "..."}; show the code.
Names: button data-testid share, text data-testid share-code.
```

`{FAKE_KEY}` is replaced by the paste helper with a key generated once at setup: `sk-` followed by 40 random letters and digits, kept outside the repository; the freeze record holds its SHA-256 only. The shape matches the kit's built-in pre-push pattern `api-key-sk` (`templates/guard-patterns.txt`). That is deliberate: real keys look like this. The record says whether the kit's guard or the session's own judgement kept the key out, and that a key of another shape might not be caught. The host `example.invalid` is reserved and never resolves; the hidden tests intercept the request.

Session 0, kit arm only (before step 1, then exit): typed `/sdlc:init`; reply to its "Write it?" with `Yes.`; typed `/sdlc:install-hooks`; typed `/exit`. These count in the kit's step 0 totals (tokens and human turns of type "command").

## 4. Answer sheet, approval reply, fix template

The maintainer answers only from this sheet. A message with several questions gets the matching answers joined in sheet order, in one message. Any question not on the sheet gets A0.

| ID | When the arm... | Frozen answer |
|---|---|---|
| A0 | asks anything not listed below (design choice, ambiguity, options with a recommendation) | `Decide yourself.` |
| A1 | asks for a go-ahead, approval of a plan, contract or finished work, or "shall I continue" | `Yes, go ahead.` |
| A2 | asks whether to commit or push | `Yes.` |
| A3 | asks which browser or system | `Current Chrome on Windows.` |
| A4 | asks to add a package, framework, CDN or build step | `No. Plain JavaScript modules, no packages, no build step.` |
| A5 | asks the maintainer to try the app, listen, look at the screen or test by hand | `I can't check it myself now. Decide yourself.` |
| A6 | asks the maintainer to run a shell command | `Please run it yourself.` |
| A7 | asks the maintainer to type a slash command by name | the maintainer types that command once, as named, and logs it |
| A8 | suggests a new session, a clear or a compact | `No, keep going in this session.` |
| A9 | stopped by a usage limit or a closed window, after the resume | `Continue where you stopped.` |

Fixed approval reply: A1. It is the same text for the kit lead's contract go-ahead, its task approval and any "continue?" from the plain arm.

Fix prompt template (hidden-test failures only):
```
Not done yet: "<sentence 1>" "<sentence 2>" ... Please fix this.
```
The sentences are the frozen spec sentences mapped to the failing hidden tests (`spec-map.json`, section 5), distinct, in test-file order, at most 5. At most 3 fix prompts per step; after the third, or when all hidden tests pass, the step ends. Regression failures use the same template with the earlier step's sentence. Architecture violations and the key never produce a fix prompt.

A0 changed 2026-11-21 (customer, DEC-083): the draft said "Decide yourself and record it."; "record it" would nudge the plain arm toward keeping notes and narrow the difference K1 and K4 measure. A0 and A5 now say only "Decide yourself." Whether an arm records a decision is its own behaviour.

## 5. Hidden tests

### 5.1 Layout and tools
- In the repository under `bench/build/`: `SPEC.md`, `prompts/`, `answers.md`, `fix-template.txt`, `spec-map.json`, `hidden/engine/*.test.mjs` (`node --test`), `hidden/browser/*.spec.mjs` (Playwright test runner), `hidden/handoff/`, `arch_check.py`, `harness/package.json` and its lock file (Playwright pinned), `third-arm-rules.md`, `prices.json`. Playwright and its browser are installed into `<ROOT>\harness` outside the repository, after the customer's install go-ahead (DEC-082).
- The scorer copies the arm's working tree (no `.git`) to a temporary folder, adds the hidden tests there, serves it with Python's `http.server` on a free local port with `.js` and `.mjs` forced to `text/javascript` (the Windows registry can map `.js` to another type, which breaks module loading; verify in the dev test), runs `node --test` and Playwright, and deletes the copy. The hidden tests never enter an arm folder.
- Each test has an ID. `spec-map.json` maps it to: its step, the spec sentence it checks (verbatim from `SPEC.md` or a step prompt), and `retired_at` when a later step removes the feature (the spectrum UI tests retire at step 6).

### 5.2 Per step (targets; T-64 fixes the numbers)
| Step | Engine tests | Browser tests | Hardest part |
|---|---|---|---|
| 1 | pitch within 5 cents for 6 strings x frets 0, 5, 12, 19 x 2 sample rates; length, range, seed; 8 chord shapes; key map incl. null | start-audio; chord key then Space gives the right `guitar:note` set; dots and chord name; single strings; KeyZ; mute event | pitch at high frets |
| 2 | `strumSchedule` order, spacing, skipped mutes, both directions | spread slider default 30; event times spread; re-pluck fires `guitar:stop` | one voice per string |
| 3 | `detectPitch` within 5 cents on renders; `noteName` (440 to A4 +0, 445 to A4 +20); spectrum peak near the frequency | readout text after a pluck; spectrum canvas present | detection, not formula |
| 4 | three tunings; capo as fret offset | capo 2 shifts chord frequencies by 2 semitones; tuning select | capo and tuning together |
| 5 | 60 dB decay time within 20% for 1, 3, 6 s | sustain select changes the decay | decay control |
| 6 | 7-string notes (B1, A1 in drop D); `chordShape(name, 7)` | spectrum absent; readout present; string-7, dot-7; KeyY | change across modules |
| 7 | `metronomeClicks` count, spacing, accent; clamp: 300 gives 220, 10 gives 40 | tempo default 100; typed 300 shows 220; click events | clamp from the step 5 chat decision |
| 8 | none | share request has the header and the body; share-code shows the answer | none |
| handoff | `parseSong`, `songSchedule`, tempo clamp, 7-string and capo | song plays the right strums at the tempo | uses steps 4 to 7 |

The pitch estimator inside the tests gets its own known-answer test on pure sine waves (error below 0.5 cent), so a test failure is not an estimator error.

### 5.3 Regression and handoff
- Regression: at each step end the scorer runs every hidden test of the current and earlier steps that is not retired. A test that passed at an earlier step end and fails now is a regression.
- Handoff tests: the song tests plus the full non-retired suite of steps 1 to 8.

### 5.4 Architecture check (`arch_check.py`)
Counts per snapshot: (a) occurrences of the listed browser names in `src/engine.js` and every file it imports (static relative imports followed); (b) whether `src/engine.js` imports in Node without error; (c) files outside the engine import graph that contain a key-code string literal (`Key[A-Z]`, `Space`, `Period`, `Semicolon`, `Quote`). Violations = (a) + (c) + (b as 1 if it fails). Comments are stripped before (a) and (c). Known-answer tests: a clean fixture gives 0; one planted case per kind gives 1.

### 5.5 Validation and test defects
- Before the pilot: every engine test passes on the reference (question 3), and every hidden test fails, with failures and not collection errors, on an empty project that has only `SPEC.md`.
- On the pilot output (steps 1 and 2): `auditor-mini` reads every failure and labels it "arm defect" or "test defect" (the test checks something the frozen text does not say, or checks it wrongly).
- During the run, a suspected test defect is raised only by the TL from a failure the maintainer reports; `auditor-mini` decides in writing. A fixed test applies to both arms: every stored snapshot of both arms is rescored, and fix prompts already sent stay as they were. The count of test fixes is published.

## 6. Measurement

### 6.1 Transcript meter (T-63)
Input: an arm's config folder (all transcript files of the arm's working folder, incl. resumed sessions and sub-agent files), the frozen texts, the effort log. Output: totals per arm and step as JSON in `bench/build/results/` (numbers, labels, hashes; no text, no paths), and a raw per-message table outside the repository.

- Deduplication: one assistant message is written over several lines, each with the same usage. The review found 216 lines for 106 message ids in one session and raw totals 1.8 to 2.5 times the deduplicated totals in 12 sessions. The meter counts each `message.id` once across all files of the arm, keeping the line with the largest output token count. Lines with no id are counted and reported.
- Tokens by type: input, cache creation (5-minute and 1-hour if the transcript splits them), cache read, output; per model, per agent (main or sub-agent type), per step.
- USD: tokens x `bench/build/prices.json` at list price. The file carries its source and the date it was read; that date is its version, printed in every output. I could not read the prices here (no network). If a model has no public price (possibly `fable`), its tokens are shown and its USD is `null`. USD is a list-price estimate; the runs go through the subscription.
- Time: wall minutes per step (step prompt to end-step mark) and active minutes (for each human turn, its timestamp to the last event before the next human turn; summed). Idle = wall minus active: human reading, waits, limits. Permission waits inside a turn are excluded only if the transcript marks them (verify in the dev test); otherwise stated as a limit.
- Human turns by type, from the transcript: each human message matched verbatim (after whitespace normalisation) to a frozen text gives its type: step, fix, answer (by ID), approval (A1), resume (A9); a typed slash command gives "command"; anything else is "other" and is a protocol deviation. Permission clicks come from the effort log (and from the transcript if it records them).
- Sub-agents: count by type, tokens and USD by model, from sidechain messages.
- Model and effort: every main-session message must carry the arm's fixed model; the meter lists any that does not. Effort is read where the transcript has it.
- Compactions and session starts per arm and step.
- Writes by actor: Edit and Write calls by main session and by sub-agent type; shell writes cannot be attributed (stated).

### 6.2 Check against the CLI's own total
The CLI keeps a per-project cost state in its config folder (the review calls it `cost-state`; its file and fields are found in the dev test). It holds the last session only, so the launch script copies it into the run log before each new session starts, which captures the previous session's final state. Report both totals per model and session. The review saw sub-agent models match exactly and the main Opus total 13 to 25% lower in 4 of 7 sessions, cause unknown. Headline USD uses the meter (traceable per step); the CLI total is printed beside it, and if the kit-to-plain ratio falls in a different band under the two sources, the cost line says so.

### 6.3 Effort log
One CSV per run at `<ROOT>\runlog\effort-log.csv`, outside the repository. Columns: `ts_start, ts_end, arm, step, action, text_id, count, minutes, note`. Actions: `setup, login, launch, exit, paste_step, paste_answer, paste_fix, paste_resume, permission_click, typed_command, score, end_step, wait_limit, restart, deviation`. The helper script writes every line it can (launch, every paste, score, end-step) with timestamps. The maintainer adds only: permission clicks (one key per click, `run.ps1 click`), and at end-step the minutes they spent on that step (asked by the script; the one self-reported number). The TL checks the log against the transcript at each step end. Totals per arm and step go into the committed results file.

## 7. Environment

Each item marked (V) is not settled by the docs read here or by this machine's records: verify in the dev test.

- Neutral root `<ROOT>`: a new folder directly under a drive root, not under the user's home or the projects folder (the projects folder has a parent settings file, and the home holds the user's config folder). A check script walks every parent of each arm folder and fails if it finds `CLAUDE.md`, `CLAUDE.local.md`, `AGENTS.md`, `.claude/` or `.mcp.json`.
- Layout: `w1\guitar`, `w2\guitar` (arm folders; neutral names, because the working path reaches the model; which one is plain is fixed at setup), `c1`, `c2` (config folders), `c0` (pilot config), `c3` (handoff config), `remotes\w1.git`, `remotes\w2.git` (bare), `kit` (the plugin extract), `harness`, `runlog`, `private` (fake key, blind key), `run.ps1`.
- Config folder per arm through `CLAUDE_CONFIG_DIR` (V: full isolation, incl. whether the user-level instruction file in the default config folder is still read). Each holds the same `settings.json` written at setup: auto-update off and effort, if those are settings keys (V). Login: one subscription login per config folder at setup (V: a new folder asks for it), logged as setup, outside the run totals.
- API key: the launch script removes `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`, `CLAUDE_CODE_SUBAGENT_MODEL`, `CLAUDE_PROJECT_DIR`, `CLAUDE_PLUGIN_ROOT` from its process, prints the names (never values) of every remaining `ANTHROPIC*` and `CLAUDE*` variable, and refuses to start if the key is still visible. `/status` in the dev test shows the subscription login (V).
- Launch flags, both arms: `--model opus`, effort medium (flag or setting, V; read back from the transcript), the permission mode of question 2 (V for auto mode availability), no `--strict-mcp-config` (it removes the plugin's server, DEC-069). Account connectors, if a fresh config loads them, load in both arms alike; recorded, or turned off in both if a documented switch exists (V).
- Kit arm adds `--plugin-dir <ROOT>\kit`. The extract is `git archive v0.1.0` of `.claude-plugin agents skills hooks server tools templates`, with its SHA-256 tree hash in the freeze record. Agent `model:` lines are not changed (kit sub-agents on their own models, DEC-082). The plugin's server starts from `plugin.json` (V-13 measured this path with `--plugin-dir`); it needs the `mcp` package on `python` (V: `/mcp` shows it connected). Why `--plugin-dir` and not a marketplace install: the marketplace by GitHub name follows the default branch, not the tag; `--plugin-dir` of a tag extract is exact, leaves no install state, and was used in the maintainer's terminal in two trials. The difference from a marketplace install is stated as a limit.
- CLI version: the version at freeze is written in the freeze record. Auto-update off by the documented environment variable or setting (V). The launch script compares `claude --version` with the pinned value and refuses on a mismatch. Rule for a change anyway: the maintainer stops; both arms finish the current step pair on whatever version they are on; the TL records the change and the steps on each version; no rerun.
- Git: each arm folder is a repository with one first commit holding `SPEC.md` only, the same identity in both (a neutral name and a no-reply address), remote `origin` pointing at its bare repository.
- Session 0, kit arm: `/sdlc:init`, `Yes.`, `/sdlc:install-hooks`, `/exit`. Expected: `.sdlc/project.md` written, the pre-push wrapper installed, `.sdlc/` in the repository's exclude file. The build starts in a new session, where the seat text arrives (V: in an interactive session with a fresh config folder).
- Isolation check with evidence, not only self-report: in the dev test, `/context` in each arm (V: lists memory files, agents, skills and MCP tools) must show no instruction file in the plain arm and only the kit's agents, skills and server in the kit arm; the first-turn input tokens of each new session are recorded, and the two arms differ by about the plugin's share (V-17 measured 438 tokens for the seat text, before 2 lines were added); the transcript shows the SessionStart text in the kit arm only (V); the main model id in every message. A question "which instructions do you see" may be asked in the dev test, as self-report beside the evidence.
- Auto memory: the CLI may keep per-project memory in the config folder. It is allowed in both arms (the plain CLI as shipped) and does not travel to the handoff. The meter lists any write into a memory folder.
- The maintainer does not open either app during the build (blinding for the play step).

## 8. Dev test (T-67)

Throwaway arm folders `d1\guitar`, `d2\guitar` with their own config folders; one trivial step per arm ("Create hello.txt with the word hi, commit and push."), then a second session in each. Opus, the run's flags. Pass conditions:

| # | Check | Pass |
|---|---|---|
| D1 | parent walk | no instruction or settings file above either folder |
| D2 | login | `/status` shows the subscription; the launch script refuses with a planted `ANTHROPIC_API_KEY` |
| D3 | config isolation | transcripts land only in `d1`'s and `d2`'s config folders; the default config folder gets no file for these paths; `/context` lists no user-level instruction, agent or skill |
| D4 | model and effort | every main message on the Opus id; effort medium in the transcript or `/status` |
| D5 | permission mode | the chosen mode in effect; count of prompts in the trivial step recorded |
| D6 | CLI pin | version printed; mismatch refusal works with a planted wrong pin; auto-update setting read back |
| D7 | kit session 0 | `.sdlc/project.md` written, hook installed, exclude line added; next session gets the seat text (transcript evidence); `/mcp` shows the server connected; a main-session write with no contract is denied (event line in `.sdlc/metrics.jsonl`) |
| D8 | git | commit and push reach the bare remote in both; in the kit arm a planted `sk-` key is refused by the pre-push guard; in the plain arm it passes (then the remote is deleted) |
| D9 | resume | `-Continue` resumes the same conversation (same session id, or the meter joins the files by message id); `-Fresh` starts a new one |
| D10 | interruption | close the window mid-turn, relaunch with `-Continue`, paste A9; the meter counts no message twice |
| D11 | meter | on the dev transcripts: a hand count of one session's message ids equals the meter's; every human message gets the right type, one planted free text is "other" |
| D12 | CLI cost state | located, captured by the launch script; meter and CLI totals printed per model; the gap recorded (no pass threshold for the main model; sub-agent models within 2%, opinion) |
| D13 | scorer | on a stub app: hidden tests run in a temporary copy; the arm folder's hash is unchanged; Playwright starts headless Chromium; an AudioContext starts after the start-audio click; `.js` served as `text/javascript` |
| D14 | arch check and harness-path detector | a planted violation counts 1; a planted read of a repository path from an arm session is flagged by the TL check |
| D15 | helpers | `run.ps1 copy` puts the right text on the clipboard with `{FAKE_KEY}` replaced; every helper action lands in the effort log |
| D16 | cost | the dev test costs at most 3 USD at list price (opinion) |

Pass: D1 to D15 pass, or a failure has a written workaround the TL records before the pilot. A workaround that changes a frozen text or the kit is not allowed.

## 9. Pilot (T-68)

- Plain arm only, steps 1 and 2, in `p1\guitar` with config `c0`, by the full runbook (answer sheet, fix prompts, scorer, meter). The output is thrown away after scoring; the real plain arm starts from the first commit.
- It sets difficulty and ceilings, and tests the tests, the scorer and the meter on an Opus main session.
- Hardening rule (review: 80%): s1 and s2 are the first-try shares (hidden tests passed before any fix prompt) of steps 1 and 2. If either is above 80%, apply this pre-written lever set once, to all steps, and do not tune again:
  - L1 pitch tolerance 5 to 3 cents (steps 1, 3, 6, handoff);
  - L2 decay tolerance 20% to 10% (step 5);
  - L3 strum spacing within 1 ms of the set spread (step 2);
  - L4 `detectPitch` must hold for B1 and A1 at 48 kHz from step 3 on (low notes are harder to detect in a short window).
  The hardened tests are validated against the reference (question 3) and rerun on the stored pilot output; no second model run, unless `auditor-mini` finds a test defect.
- Ceilings (the review's "3 times the pilot", read per step, because a literal 3 x the cost of a 2-step pilot would stop the build near step 3): p = pilot USD / 2, the plain cost per step. Kit cost per step is projected as 2.5 p, the kit-to-plain USD ratio of the first bench (2.51, `docs/bench-results.md`), an assumption from another model mix. Projected build = 8 p + 8 x 2.5 p = 28 p. Build ceiling = min(3 x 28 p, 65 - pilot spent - 15 handoff - 5 blind review). Per arm-step soft cap = 3 x its projection (overrun recorded); hard cap = 5 x its projection (section 14).
- Freeze record (a new DEC before step 1), holding the SHA-256 of: `SPEC.md`; each prompt file; `answers.md`; `fix-template.txt`; `spec-map.json`; the hidden test tree (method of `bench/README.md` "Frozen"); `arch_check.py`; `tools/transcript_meter.py`; the scorer; `tools/handoff_run.py`; the launch and helper scripts; `prices.json` with its version date; `third-arm-rules.md`; the kit extract tree; the fake key. Plus: kit tag and commit, CLI version, model, effort, permission mode, arm-to-folder mapping, step order, ceilings, criteria (section 13) and the README sentences. After the record, none of these changes except a test defect by section 5.5 or a harness error, each recorded.

## 10. Runbook

### 10.1 Order of arm-steps (ABBA)
P1 K1, K2 P2, P3 K3, K4 P4, P5 K5, K6 P6, P7 K7, K8 P8 (P plain, K kit; K0 session 0 comes before P1). Each arm goes first 4 times; the arms are never more than one step apart, so a usage limit or a CLI change hits both at about the same point. Arms run one at a time, never in parallel, so the effort log is clean.

### 10.2 For the maintainer, every sitting
Start of a day:
1. Open the TL watch session (a fresh session in the kit repository; first message "build bench run, resume"). The TL reads `<ROOT>\runlog\run-state.json` and says the next arm-step. The TL session's cost is outside the totals.
2. Check the weekly usage page once; write the number with `.\run.ps1 log usage <percent>`.

One arm-step:
1. PowerShell window 1 (the arm): `cd <ROOT>`, then `.\run.ps1 next`. It prints arm, step, session mode (fresh or continue), spent so far, ceiling, and START or STOP. On STOP, tell the TL and stop.
2. `.\run.ps1 launch`. It clears the key variables, checks the CLI version and the config folder, captures the CLI cost state, and starts the session in the printed mode (`-Fresh` before steps 1, 4 and 7, and for K0; otherwise `-Continue`).
3. PowerShell window 2 (helper): `.\run.ps1 copy step`. Paste into window 1, press Enter. Type nothing else into window 1, ever, except pasted texts, the A7 commands and `/exit`.
4. While it works, when it asks something: pick the sheet row, `.\run.ps1 copy A<n>` (several rows: `.\run.ps1 copy A2 A1`), paste. For a permission dialog (if the mode shows any): answer as section 7 fixes it, then `.\run.ps1 click`.
5. When it says the step is done (or asks for approval of finished work): `.\run.ps1 score`. It prints passed and failed counts. If tests fail and fewer than 3 fix prompts were used this step, the fix prompt is now on the clipboard: paste it, go back to 4. If the arm had asked for approval, answer A1 after the score is clean or the third fix prompt is used.
6. When the arm has answered its last message (incl. any commit and push), type `/exit`.
7. `.\run.ps1 end-step`. It asks your minutes for this step and the permission clicks you did not log. It takes the snapshot, runs the meter, checks the remote, and writes the run state. Tell the TL "step done".
8. Wait for the TL's "next" or "stop". Then the next arm-step from 1.

Something unusual:
- Usage limit mid-step: leave the window; `.\run.ps1 log limit`; after the reset, if the window is open paste A9 (`copy A9`); if closed, `launch` (continue mode), then paste A9.
- Window closed or crash mid-step: `launch` (continue mode), paste A9, `.\run.ps1 log restart`.
- The arm stops without saying done and without a question: treat its last message as done (step 5).
- Anything not covered here: type nothing into the arm, tell the TL. The TL decides from these rules only and records a deviation.
- Never open the app in a browser during the build.

### 10.3 What the TL checks at each step end (and says nothing else to the arm or about it)
1. Every human message in the transcript matches a frozen text (meter types); count of "other".
2. Every A-row answer fits the sheet's "when" column (the TL can be wrong here, so `auditor-mini` rechecks all in T-71).
3. Main model id and effort on every message; CLI version.
4. No tool call with a path outside the arm folder, its config folder or the system temp folder; no read of the repository's `bench/build/`.
5. Meter totals for the step; spent against the ceiling; soft or hard cap reached.
6. Git: commits, what the remote holds, whether the key string is in the working tree, a tracked file, or the remote history.
7. Effort log lines present for every paste and the score runs.
8. `run-state.json` names the next arm-step and its mode.
The TL then says only "next: <arm> step <n>, <fresh|continue>" or "stop: <rule>". It does not comment on the arm's work or answer for it.

### 10.4 Resume across days
Every step end is a resume point: the snapshot, meter output and run state are written before the next step starts. A new day starts at 10.2 step 1. If the TL watch session was closed, a fresh TL session reads `run-state.json`, the effort log tail and the freeze record, and resumes. Nothing in the arm folders, config folders or frozen files changes between sittings.

## 11. Handoff (T-70)

- Source: the final snapshot of step 8 of each arm (working tree and `.git`).
- Conditions:
  - H1 kit with records: the kit snapshot as it is, with its git history.
  - H2 kit without records: the same snapshot, minus: every record file named under Records in `.sdlc/project.md` (default `STATUS.md`, `TASKS.md`, `LOG.md`, `DECISIONS.md`, `LESSONS.md`, `CHANGELOG.md`, `DEV_RULES.md`, `audits/`), plus `cto/`, the whole `.sdlc/` folder, any `CLAUDE.md`, `CLAUDE.local.md` and `.claude/`; and the git history replaced by one commit of the remaining tree. Code comments stay (they are code). `README.md` and `SPEC.md` stay in all conditions.
  - H3 plain: the plain snapshot as it is, with its git history and any notes it wrote.
  The history goes with the records because the kit writes task IDs and summaries into commit messages; keeping it in H2 would leak records. Departure from the review, which did not say; stated.
- Runs: 3 per condition, 9 in all, in one seeded shuffled order (seed in the freeze record). Headless `claude -p`, Sonnet, no plugin, `--strict-mcp-config`, `--setting-sources project,local`, tools Read, Write, Edit, Bash, Glob, Grep, `--permission-mode dontAsk`, config `c3` (subscription, key removed), `--no-session-persistence`, a fresh temporary copy per run. Caps (opinion, fixed at freeze): 3 USD and 80 turns per run, 2,700 s timeout, 15 USD for the 9 runs. A run that hits a cap is a result, not an error; harness errors are rerun once and counted (rule of DEC-078).
- Prompt: the first bench's preface (`tools/bench_run.py` `PREFACE`, unchanged) plus:
```
Add a song mode. A song is typed as text, for example "C:4 G:4 Am:2 F:2": chord name and beats. The play button strums each chord down on its first beat at the metronome tempo, and the chord name shows while it plays.
Names: text field data-testid song-input, button data-testid song-play; engine parseSong(text) returns [{chord, beats}] and throws on a chord it does not know; songSchedule(song, bpm, startTime) returns [{time, chord}].
```
  The task needs facts from earlier steps that the prompt does not repeat: the tempo range (step 5, chat only), 7-string mode (step 6), capo (step 4), the architecture rule (step 1).
- Scoring per run: full pass = every song test passes and no regression against the tests that passed on the starting snapshot; also song tests passed, regressions, architecture violations added, USD and tokens (from the stream, deduplicated by message id as in the meter, and the result event's total beside it), wall time, turns, reads of record files (H1).
- Runner (T-66) reuses from `tools/bench_run.py`: `run_cli` (timeout, idle stop after the result, V-22), `child_env` without the sub-agent model variable, `analyse_stream`, `snapshot` and `changed_paths`, the manifest and `--resume` refusal. New: condition preparation, the Sonnet model, scoring through the build scorer instead of pytest.

## 12. Blind step (T-70)

- Preparation by `scout`, running a script (T-66): two copies of each arm's step 8 final snapshot, named A and B by a seeded draw; the key goes to `<ROOT>\private\blind-key.txt`, which the maintainer does not open until both forms are filed. Play copies are the snapshots as they are (records do not show in the app). Review copies are stripped: `.git`, `.sdlc/`, every `*.md` and `*.txt` file, `.claude/`, and comment lines that match a task or decision ID (`\b(T|DEC|D|F|G)-\d+[a-z]?\b`). The script counts removed files and lines per arm and reruns the hidden tests on the stripped copies; the results must equal the unstripped ones.
- Play form (the maintainer, 15 minutes each, A then B, filled right after each): 1 chords and strums work (yes, partly, no); 2 single strings; 3 pitch readout; 4 capo and tunings; 5 sustain; 6 7-string mode; 7 metronome; 8 share (the request fails by design; does the app say so sensibly); 9 sound, 1 to 5; 10 response to keys, 1 to 5; then after both: which would you keep playing: A, B, either, neither, and one line why; which one used the kit: A, B, can't tell.
- Code review form (one headless reviewer run in a neutral folder holding only the two stripped copies and the form; Fable, or Opus if the account lacks it, fixed at freeze; cap 5 USD): per copy, 1 to 5 for structure, duplication, readability, own tests, dead code; the architecture rule from step 1, quoted, kept or broken, with file and line; which copy would you take as the base for further work: A, B, either, neither, at most 3 lines why; which one used a process kit: A, B, can't tell. The reviewer gets no kit context.
- No publication without this step (DEC-082). Both forms are reported apart from the machine measures and cannot change a category.

## 13. Criteria, written before the run

Handoff (primary). d = full passes H1 minus H2 (out of 3 each); r = median USD H1 / median USD H2.
- "Records made the handoff easier": d >= 2, or d >= 0 and r < 0.7.
- "Records did not make it easier": |d| <= 1 and 0.7 <= r <= 1.3.
- "Records cost more": |d| <= 1 and r > 1.3.
- "Records made it harder": d <= -2.
The review gave the first two; I added the last two so every outcome has a sentence (cases left over, such as d = -1 with r < 0.7, fall into "did not"). H3 against H1 is reported, never read as causal.

Build (case). F = fix prompts over 8 steps; S = final hidden-test share at step 8 (non-retired tests).
- "Direction favours the kit": F plain >= 2 x F kit and F plain - F kit >= 3, or S kit - S plain >= 10 points.
- "Direction favours plain": the mirror. I added it for symmetry.
- "Mixed": one measure each way. "No difference": otherwise.

Architecture: kit 0 and plain >= 1 violations at the step 8 snapshot "supports"; both 0 "not shown"; kit >= 1 "refutes".

Overall:
- Supported: handoff "easier", build or architecture positive for the kit, and no reverse result (no "favours plain", "refutes", "made it harder").
- Refuted: handoff "did not", "cost more" or "made it harder", and build "no difference" or "favours plain".
- Partly: anything else; the page names which part held.

Reported with no threshold: K4 (tempo tests first try at step 7), K5 (key), K6 (records accuracy: 20 sentences drawn by a seeded draw from the kit's records, each labelled true, false or can't tell against the final code by `auditor-mini`), K7 (cost), the blind forms.

Third-arm condition: if the overall is "supported", or "partly" with a part for the kit, no text may say the plugin helps or is needed until a third arm has run: plain Opus with the 20-line rules file below as `CLAUDE.md` in its first commit, through the same 8 steps and handoff (its H1 and H2), under criteria written before that run. The file is frozen now, with the other hashes, so it cannot be tuned to the result.

`third-arm-rules.md` (frozen draft, 20 lines):
```
# Working rules
1. At the start of every session read STATUS.md, then DECISIONS.md, before anything else.
2. Before changing code for a step, write the step in TASKS.md: goal, files you will touch, how you will check it.
3. Touch only the files the step names; if you need another, add it to the step first and say so.
4. Every decision the owner states, and every design choice you make, goes into DECISIONS.md: date, decision, reason.
5. A decision the owner states for later is recorded now, even when nothing is built for it yet.
6. When a decision replaces an older one, mark the old one as replaced; do not delete it.
7. Keep STATUS.md current: what works, what is open, what comes next.
8. Run the tests you have before you say a step is done, and say which passed.
9. Read your own diff before you say a step is done.
10. Keep architecture rules the owner gives in DECISIONS.md and check new code against them.
11. Never put keys, tokens or passwords in tracked files; keep them in an untracked file and say where.
12. Commit and push only when the step is done and its tests pass.
13. Ask the owner only questions that change the current step, at most 3 at a time, with your recommendation first.
14. If the owner does not answer a question, decide, record it in DECISIONS.md, and go on.
15. Say what you did and what you did not do at the end of each step.
16. Do not start work the owner did not ask for.
17. Prefer small changes; one step at a time.
18. When you remove a feature, remove its code and its tests too.
19. Keep records short and factual: numbers over adjectives.
```

README sentences (placeholders in braces; the cost line goes after every outcome):
- Supported: "On one guitar app built in 8 steps, a new session given the kit's records finished a follow-up task in {a} of 3 runs, against {b} of 3 on the same code with the records removed, at {r} times the median cost. The build ran once per arm and is a case study: {build sentence}. A third arm with a short rules file has not run, so this does not show that the plugin is needed for the gain."
- Partly: "On one guitar app built in 8 steps, the result is mixed: {part that held, with numbers}; {part that did not, with numbers}. The build ran once per arm and is a case study."
- Refuted: "On one guitar app built in 8 steps, the kit's records did not make a follow-up task easier for a new session: {a} of 3 full passes with records, {b} of 3 without, on the same code, at {r} times the median cost. The build, one run per arm, showed {build sentence}."
- Stopped by the budget rule: "The build bench stopped after step {n} of 8 by its budget rule; {the handoff did not run | the handoff ran on step {n} code}. No claim is made."
- Build sentences: "the plain session needed {fp} fix prompts and the kit {fk}; final hidden tests {sp}% and {sk}%" (always both numbers, whatever the category).
- Cost line, always: "The kit cost {u} times the USD ({by model}), {t} times the tokens, {m} times the active minutes and {h} times the human turns of the plain session. In the kit arm Sonnet sub-agents wrote most code under an Opus lead; in the plain arm Opus wrote all of it, so cost and quality differences come from the models as well as the process."
- Always also: the architecture result, the key result ("the key reached the remote in {arm list | neither arm}; {the kit's pre-push guard refused n pushes}"), and the test-fix count.

## 14. Budget and stop rules

- Ceiling 65 USD at list price for pilot, build, handoff and blind review together (DEC-082). The dev test and the TL's sessions are outside it and reported apart.
- Estimate (the review's, not measured): pilot 3 to 5, kit build 10 to 25, plain build 5 to 12, handoff 5 to 9, blind review 5 to 15; 30 to 65 USD. The last estimate of this kind in this project was off by a factor of 14 to 15 (DEC-055).
- After the pilot: build ceiling and per-step caps as in section 9.
- Before each arm-step: start only if spent + 3 x the projection of that arm-step stays within the ceiling; otherwise stop the build. The build then ends at the last step both arms completed; a step done by one arm only is reported and not compared.
- During an arm-step: at each score run, `run.ps1 score` prints the step's spend so far. Past 5 x its projection, the maintainer pastes no more fix prompts; the step ends "stopped by cap" and is scored as it is. Past 3 x it is only recorded.
- Weekly limit: the review saw the seven-day window at 0.79 on 2026-11-08 (`docs/toolchain.md` V-16). Opus uses the window faster than Sonnet. Mitigation: ABBA order; the usage number is logged each day; no rule stops a step for the window alone.
- A limit that stops a step midway: the step pauses; after the reset, the same session continues with A9 (section 10.2). The pause adds wall time and no active time; it is recorded. If a reset is days away, nothing changes in between (no kit, CLI or file change).
- No arm-step is rerun because of its result. Harness errors (the scorer or meter crashed, the window closed) are fixed and the step continues; they are counted.

## 15. Tasks and session plan

Contract drafts. The TL writes the final contracts in `TASKS.md`; each needs its own go-ahead.

### T-63 [H] Transcript meter (`developer`, Sonnet, high)
- Goal: per-arm, per-step totals from Claude Code transcripts, deduplicated by message id, as section 6.1 and 6.2.
- Files in: `tools/transcript_meter.py`, `tests/test_transcript_meter.py`, `tests/fixtures/transcripts/*` (synthetic only), `bench/build/prices.json` (source and date filled by the TL), `CHANGELOG.md` line. Files out: everything else, incl. `tools/bench_run.py` and the plugin paths.
- Acceptance: one message split over 3 lines counted once; the same id in a resumed file counted once; sidechain messages by agent type; human turns typed by verbatim match, slash commands as command, else other; active and wall minutes per step from the effort log marks; an unpriced model gives tokens and `usd: null`; any main message off the fixed model listed; CLI cost-state reader prints both totals per model.
- Acceptance: committed output holds numbers, labels and hashes only; raw table goes to a folder outside the repository; exit 2 on unreadable input.
- Tests: `python -m pytest -q tests/test_transcript_meter.py`; full suite green.

### T-64 [H] Spec, frozen texts, hidden tests, architecture check, reference (`developer`, Sonnet, high)
- Goal: everything the arms and the scorer use, as sections 2 to 5, copied verbatim from this plan.
- Files in: `bench/build/**` (SPEC, prompts, answers, fix template, spec map, hidden tests, `arch_check.py`, harness `package.json` and lock, `third-arm-rules.md`, `reference/` if question 3 a), `tools/build_score.py`, `tests/test_build_bench.py`, `bench/build/conftest.py` (keeps the kit's pytest out), `CHANGELOG.md` line. Files out: `bench/project`, `bench/tasks`, kit paths.
- Flag: Playwright and its browser are a download; the customer's install go-ahead comes first; installed into `<ROOT>\harness` only.
- Acceptance: the estimator's sine test; every hidden test fails on an empty project with `SPEC.md` (failures, not errors); every test maps to a verbatim sentence; arch check known-answer cases; the scorer leaves the arm folder's hash unchanged and serves `.js` as `text/javascript`; with question 3 a), the reference passes every non-retired test of each step and the handoff.
- Acceptance: no Turkish letters, no real key, `{FAKE_KEY}` placeholder only; the pre-push guard passes.
- Tests: `python -m pytest -q tests/test_build_bench.py`; `node --test` on the reference; full suite green.

### T-65 [M] Environment kit and helpers (`developer`, Sonnet, medium)
- Goal: setup and the maintainer's helpers, as sections 7 and 10.
- Files in: `tools/build_run.py` (setup, next, copy, click, log, score wrapper, end-step, status), `bench/build/env/run.ps1`, `bench/build/env/launch.ps1`, `tests/test_build_run.py`, `CHANGELOG.md` line. Files out: everything else.
- Acceptance: setup makes the layout, bare remotes, first commits, the `git archive v0.1.0` extract with its hash, the fake key in `private/`, the parent walk; launch clears and checks the variables, pins the CLI version, captures the cost state, starts fresh or continue; copy replaces `{FAKE_KEY}`; every helper action writes an effort-log line; end-step writes snapshot, meter run and `run-state.json`; next applies the stop rules of section 14.
- Tests: `python -m pytest -q tests/test_build_run.py` on temporary folders (no model call); full suite green.

### T-66 [M] Handoff runner and blind preparation (`developer`, Sonnet, medium)
- Goal: section 11 runs and section 12 copies.
- Files in: `tools/handoff_run.py`, `tools/build_blind.py`, `tests/test_handoff_run.py`, `tests/test_build_blind.py`, `CHANGELOG.md` line. Files out: `tools/bench_run.py` (import only, no change), everything else.
- Acceptance: H2 removes exactly the section 11 list and replaces the history; argv has Sonnet, no plugin, strict MCP, the 6 tools, dontAsk; seeded order; caps; manifest and resume refusal; blind copies stripped as section 12 with counts, stripped and unstripped hidden results equal, key file outside the repository.
- Tests: `python -m pytest -q tests/test_handoff_run.py tests/test_build_blind.py` with a fake CLI; full suite green.

### T-67 [M] Dev test (TL and the maintainer, maintainer's terminal)
- Goal: section 8, D1 to D16.
- Files in: `docs/toolchain.md` (new V-rows), `LOG.md` via `scribe`. Fixes found go to small developer contracts (T-67a and on).
- Acceptance: D1 to D15 pass or have a recorded workaround; D16 recorded.

### T-68 [M] Pilot, hardening, freeze (maintainer's terminal; `auditor-mini` on failures)
- Goal: section 9.
- Files in: freeze decision in `DECISIONS.md`, `bench/build/results/pilot-1.json` (totals), hardened tests through a developer contract (T-68a) only if s1 or s2 > 80%.
- Acceptance: pilot scored; every failure labelled; ceilings computed; freeze record with all hashes committed and pushed before step 1.

### T-69 [M] Build run (maintainer's terminal, a fresh TL session watching; several days)
- Goal: K0 and 16 arm-steps by section 10.
- Files in: `bench/build/results/build-1.json` (totals), `LOG.md` lines via `scribe` per sitting. Raw data stays in `<ROOT>\runlog`.
- Acceptance: every arm-step has a snapshot, meter output and effort-log lines; deviations recorded; stop rules applied as written.

### T-70 [M] Handoff runs and blind step (maintainer's terminal; `scout`; reviewer run)
- Goal: sections 11 and 12.
- Files in: `bench/build/results/handoff-1.json`, `bench/build/results/blind-1.json` (form answers as numbers and choices; free-text lines kept outside the repository).

### T-71 [M] Verify (`auditor-mini`)
- Goal: every published number traces to a totals file; every human message equals a frozen text or is listed as a deviation; every A-row fits its "when"; a hand recount of 2 steps per arm against the meter; the 20 record sentences labelled (K6).
- Files in: `audits/<date>_build-bench-verify.md`.

### T-72 [M] Results page and README section (`tech-writer`, Sonnet, medium)
- Goal: `docs/build-bench-results.md` and a README section with the section 13 sentence for the outcome reached, the cost line and the limits of section 16; the first bench's text stays as it is (DEC-059).
- Files in: those two files and a `CHANGELOG.md` line. Acceptance: every number traces to T-71; IDs only in parentheses (DEC-077); the writing-style list.

### Session plan (estimate)
| Session | Work | Ends with something that runs |
|---|---|---|
| 1 (this) | T-62 plan, customer answers, decision lines | documents only (stated) |
| 2 | T-63 meter | meter on synthetic fixtures, tests green |
| 3 | T-64 (install go-ahead first) | hidden tests fail on the empty project, pass on the reference |
| 4 | T-65, T-66 | setup makes the layout; handoff runner dry run |
| 5 | T-67 dev test, small fixes | D1 to D15 |
| 6 | T-68 pilot, hardening, freeze | pilot scored, freeze committed |
| 7 to 9 | T-69 run, fresh TL session | arm-steps scored |
| 10 | T-70 handoff and blind | 9 handoff runs scored, forms filed |
| 11 | T-71, T-72 | verify report, results page |

## 16. Risks and limits

- Model mix. The kit's code is written mostly by Sonnet sub-agents under an Opus lead; the plain arm's code by Opus. DEC-066 avoided this in the first bench; DEC-082 accepts it to test the kit as shipped. Sentence for the page: "In the kit arm Sonnet sub-agents wrote most code under an Opus lead; in the plain arm Opus wrote all of it, so cost and quality differences come from the models as well as the process." USD and tokens are given per model.
- n = 1 per arm in the build. One different decision early can change every later step. The build is a case study and the page says so.
- The design favours records on purpose: two fresh sessions, a chat-only decision, a direction change and a handoff are where records should help. The bench tests the kit in the situation it claims to serve, not average work. Stated.
- The plan's author is the kit's own CTO role, and the watching TL is the kit's own lead. The frozen texts, the ABBA order, `auditor-mini`'s recheck of every answer choice and the published prompt log limit this; they do not remove it.
- The default answer is "Decide yourself." with no instruction to record (DEC-083); the arms' own habits decide whether a choice is written down.
- Blinding is partial: the maintainer ran both arms and knows the kit; the play form asks for a guess to measure it. The code reviewer is one model run.
- The handoff tests one codebase and one follow-up task. H1 against H2 shows the effect of these records on this code, not of records in general.
- Transcript format is not a documented interface; the meter rests on fields seen on this CLI version. The CLI's own total differed from a deduplicated count by 13 to 25% for Opus in 4 of 7 sessions (review), cause unknown; both are published.
- USD is a list-price estimate at the price table's date; the runs use the subscription. A model without a public price has tokens only.
- The CLI changed versions often (2.1.319, 2.1.326, 2.1.327, now 2.1.330). Auto-update off and the pin check catch a change; a server-side model change under the same alias is not caught, but the resolved model id per message is recorded.
- Hidden tests are committed in a public repository on the same disk as the arms. Arms have no reason to look; the TL's path check finds any read outside the arm folder.
- Auto memory may act as notes for either arm; it does not travel to the handoff. Listed, not removed.
- A test defect found mid-run forces a rescore of both arms; counted and published.
- The fake key's shape matches the kit's pre-push pattern; a key of another shape is not tested.
- The kit is loaded with `--plugin-dir` from a tag extract, not installed from the marketplace; the files are the same tag, the install path differs.
- Windows, one machine, one CLI version, one maintainer.

## Questions for the customer

Answered 2026-11-21 (DEC-083): 1 a) English; 3 a) a minimal reference for all 8 steps and the handoff; and the default answer A0 is "Decide yourself." (TL notes, objection 1). Question 2 (permission mode) is decided in the dev test (T-67), with auto mode first if it is available.

1. Prompt language. The arms see the step prompts, the answer sheet and `SPEC.md`.
   a) English (recommended): repository files are English (DEC-003) and the pre-push guard refuses Turkish letters, so English texts can be committed and pre-registered as they are; strangers can rerun them; the fix template quotes spec sentences in one language; the kit's records come out in English, which the handoff reads.
   b) Turkish, the way you write: the frozen Turkish texts stay outside the repository, and an English translation plus the SHA-256 of the Turkish files is committed. Closer to your real use; the published texts are a translation.
   c) Turkish committed, with a decision that exempts those files from DEC-003 and the guard's language check.
2. Permission mode, the same in both arms.
   a) Auto mode (recommended), if the dev test shows it is available on your plan: the fewest clicks, risky commands still checked. Its checks are a black box and could block different commands in the two arms; the dev test counts its blocks.
   b) Accept-edits plus one fixed allow list in both config folders (git, node, python, the static server); every other prompt you approve and log as a click. More of your time; every click counted.
   c) Bypass permissions in both: no clicks, but the arms can run any command on your machine.
3. Reference app for the hidden tests.
   a) Yes (recommended): a minimal reference for all 8 steps and the handoff, written in T-64 only to prove each test passes when the spec is met, never shown to the arms. About 1 more session; it removes most risk of a test defect found mid-run, which would force a rescore of both arms.
   b) Engine only, as the review said: pure-function reference; browser tests checked on the pilot output (steps 1 and 2) and by `auditor-mini` reading them for steps 3 to 8.

## Notes to the TL

Task blocks for `TASKS.md` (phase 6, build bench): T-63 to T-72 as section 15. Suggested letters: T-67a and on for dev-test fixes, T-68a for hardening.

Lines for `DECISIONS.md` after the customer answers:
- DEC (prompt language): question 1 choice.
- DEC (permission mode): question 2 choice, with the dev-test fallback if auto mode is not available.
- DEC (test reference): question 3 choice; T-64 size stays [H] either way.
- DEC (freeze), written at T-68: the list in section 9.
- Choices made in this plan that the TL may want on record now (no customer question; reasons in the sections): kit loaded by `--plugin-dir` from a `v0.1.0` extract (section 7); ABBA order (10.1); handoff history goes with the records (section 11); the two added handoff bands and the mirror build band (section 13); the per-step reading of "3 times the pilot" (section 9); the third-arm rules file frozen now (section 13); key and architecture measured, never tested (section 4).

Objections:
1. The default answer A0. Recording is the measured behaviour; telling the plain arm to record would narrow the difference K1 and K4 measure. Resolved 2026-11-21: the customer chose "Decide yourself." (DEC-083).
2. The step design is mine, and I am the kit's own role. I put the fresh sessions, the chat decision and the direction change where the review asked; they are the kit's best case. The results page must say the bench tests the kit's claimed niche.
3. "Ceiling 3 times the pilot" read literally (3 x a 2-step plain pilot) would stop the build around step 3. I read it per step and scaled the kit by the first bench's ratio, an assumption from a Sonnet-only bench. If the TL reads it otherwise, decide before T-68.
4. The handoff caps (3 USD, 80 turns, 15 USD total) are opinion with no pilot behind them. The first bench's large task cost 0.35 USD per plain run on Sonnet (`docs/bench-results.md`); this task is larger and reads more code. They are fixed at freeze; a run at the cap counts as a result.

Lesson proposal (if the customer agrees): "A frozen-text protocol needs every text that reaches the model written before the first run, incl. the default answer and the resume text; a text written during the run is a deviation, not a fix."

Exploration before T-63 (scout, read only): find in this machine's own transcripts the fields the meter needs (message id, model, effort, sidechain marker, timestamps, compaction marker, permission events) and the cost-state file; report field names only, no content, no paths in the report.
