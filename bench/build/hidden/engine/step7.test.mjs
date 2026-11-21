// Hidden engine tests, step 7 (prompt step-7.txt). Project root: the GUITAR_ROOT environment variable.
// Each test imports the engine itself, so a missing engine fails every test and never the file.
// Test names are the IDs of spec-map.json. The three clamp tests belong to step 7 but map to the
// decision of the step 5 prompt, which the step 7 prompt does not repeat.
//
// Readings the tests accept: the first click may sit at time 0 or up to one beat later, so the count is
// checked against the first click's own time; the accent may be a boolean or a number as long as the
// first beat of a bar is stronger than the others; a bar is beatsPerBar clicks counted from the first.
import assert from "node:assert/strict";
import test from "node:test";
import { loadEngine } from "./load.mjs";
import { louder } from "./helpers.mjs";

const EPS = 1e-6;

function clicks(engine, bpm, beatsPerBar, durationSeconds) {
  const result = engine.metronomeClicks(bpm, beatsPerBar, durationSeconds);
  assert.ok(Array.isArray(result), "metronomeClicks must return an array");
  for (const click of result) {
    assert.ok(click !== null && typeof click === "object" && Number.isFinite(click.time) && "accent" in click, `bad click ${JSON.stringify(click)}`);
  }
  return result;
}

test("s7.engine.exports", async () => {
  const engine = await loadEngine();
  assert.equal(typeof engine.metronomeClicks, "function", "metronomeClicks is not an exported function");
});

test("s7.engine.click-spacing", async () => {
  const engine = await loadEngine();
  for (const bpm of [40, 60, 100, 120, 220]) {
    const interval = 60 / bpm;
    const result = clicks(engine, bpm, 4, 10.5 * interval);
    assert.ok(result.length >= 9, `${bpm} BPM: ${result.length} clicks in 10.5 beats`);
    for (let i = 1; i < result.length; i += 1) {
      assert.ok(Math.abs(result[i].time - result[i - 1].time - interval) < EPS, `${bpm} BPM: click ${i} is ${result[i].time - result[i - 1].time} s after the one before, expected ${interval}`);
    }
  }
});

test("s7.engine.click-count", async () => {
  const engine = await loadEngine();
  for (const bpm of [40, 100, 120, 220]) {
    const interval = 60 / bpm;
    const duration = 10.5 * interval; // half a beat past a click, so no click sits on the end
    const result = clicks(engine, bpm, 4, duration);
    const first = result[0].time;
    assert.ok(first >= 0 && first < interval + EPS, `${bpm} BPM: the first click is at ${first} s`);
    assert.equal(result.length, Math.floor((duration - first) / interval) + 1, `${bpm} BPM: number of clicks in ${duration} s`);
    assert.ok(result[result.length - 1].time < duration, `${bpm} BPM: a click lies at or after the end`);
  }
});

test("s7.engine.accent-bar-4", async () => {
  const engine = await loadEngine();
  for (const bpm of [60, 100, 120]) {
    const result = clicks(engine, bpm, 4, 20.5 * (60 / bpm));
    const strong = result.filter((_, i) => i % 4 === 0).map((click) => click.accent);
    const weak = result.filter((_, i) => i % 4 !== 0).map((click) => click.accent);
    assert.ok(strong.length >= 5 && weak.length >= 15, `${bpm} BPM: too few clicks`);
    assert.ok(strong.every((value) => value === strong[0]), `${bpm} BPM: the first beats of the bars differ from each other`);
    assert.ok(weak.every((value) => value === weak[0]), `${bpm} BPM: the other beats differ from each other`);
    assert.ok(louder(strong[0], weak[0]), `${bpm} BPM: the first beat of a bar (${strong[0]}) must be louder than the others (${weak[0]})`);
  }
});

test("s7.engine.accent-bar-length", async () => {
  const engine = await loadEngine();
  for (const beatsPerBar of [2, 3, 5]) {
    const result = clicks(engine, 120, beatsPerBar, 12.25);
    const strong = result.filter((_, i) => i % beatsPerBar === 0).map((click) => click.accent);
    const weak = result.filter((_, i) => i % beatsPerBar !== 0).map((click) => click.accent);
    assert.ok(louder(strong[0], weak[0]), `${beatsPerBar} beats a bar: the first beat (${strong[0]}) must be louder than the others (${weak[0]})`);
    assert.ok(strong.every((value) => value === strong[0]) && weak.every((value) => value === weak[0]), `${beatsPerBar} beats a bar: accents are not regular`);
  }
});

test("s7.engine.clamp-high", async () => {
  const engine = await loadEngine();
  const expected = clicks(engine, 220, 4, 6.1);
  for (const bpm of [221, 300, 1000]) assert.deepEqual(clicks(engine, bpm, 4, 6.1), expected, `${bpm} BPM must run as 220`);
});

test("s7.engine.clamp-low", async () => {
  const engine = await loadEngine();
  const expected = clicks(engine, 40, 4, 6.1);
  for (const bpm of [39, 10, 0, -20]) assert.deepEqual(clicks(engine, bpm, 4, 6.1), expected, `${bpm} BPM must run as 40`);
});

test("s7.engine.clamp-inside", async () => {
  const engine = await loadEngine();
  const slow = clicks(engine, 40, 4, 6.1);
  assert.ok(Math.abs(slow[1].time - slow[0].time - 1.5) < EPS, "40 BPM must keep its 1.5 s beat");
  const fast = clicks(engine, 220, 4, 6.1);
  assert.ok(Math.abs(fast[1].time - fast[0].time - 60 / 220) < EPS, "220 BPM must keep its beat");
  const middle = clicks(engine, 130, 4, 6.1);
  assert.ok(Math.abs(middle[1].time - middle[0].time - 60 / 130) < EPS, "130 BPM must keep its beat");
});
