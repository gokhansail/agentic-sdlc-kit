// Hidden engine tests, step 2 (prompt step-2.txt). Project root: the GUITAR_ROOT environment variable.
// Each test imports the engine itself, so a missing engine fails every test and never the file.
// Test names are the IDs of spec-map.json.
//
// Two readings are allowed wherever the text does not choose. "Spread over a time I set" may mean the
// whole strum lasts that time or each gap between notes lasts that time, so the tests only use what
// both readings share: the first note at the start, strictly later notes, a span between 0.4 and
// (number of notes) times the set time, a longer span for a longer set time, and no span at 0 ms.
// The frets argument is read as chordShape returns it: 6 frets from string 6 to string 1.
import assert from "node:assert/strict";
import test from "node:test";
import { loadEngine } from "./load.mjs";
import { CHORDS, inTimeOrder, soundingStrings, timeSpan } from "./helpers.mjs";

const START = 2.5;
const EPS = 1e-9;

function strum(engine, chord, direction, spreadMs, start = START) {
  const entries = engine.strumSchedule(CHORDS[chord], direction, start, spreadMs);
  assert.ok(Array.isArray(entries), "strumSchedule must return an array");
  for (const entry of entries) {
    assert.ok(Number.isInteger(entry.string) && entry.string >= 1 && entry.string <= 6, `bad string in ${JSON.stringify(entry)}`);
    assert.ok(Number.isInteger(entry.fret) && entry.fret >= 0, `bad fret in ${JSON.stringify(entry)}`);
    assert.ok(Number.isFinite(entry.time), `bad time in ${JSON.stringify(entry)}`);
  }
  return entries;
}

test("s2.engine.exports", async () => {
  const engine = await loadEngine();
  assert.equal(typeof engine.strumSchedule, "function", "strumSchedule is not an exported function");
});

test("s2.engine.entry-shape", async () => {
  const engine = await loadEngine();
  for (const [chord, frets] of Object.entries(CHORDS)) {
    for (const direction of ["down", "up"]) {
      const entries = strum(engine, chord, direction, 30);
      for (const entry of entries) {
        assert.equal(entry.fret, frets[6 - entry.string], `${chord} ${direction}: fret of string ${entry.string}`);
      }
    }
  }
});

test("s2.engine.down-order", async () => {
  const engine = await loadEngine();
  for (const [chord, frets] of Object.entries(CHORDS)) {
    const order = inTimeOrder(strum(engine, chord, "down", 30)).map((entry) => entry.string);
    assert.deepEqual(order, soundingStrings(frets), `${chord} down`);
  }
});

test("s2.engine.up-order", async () => {
  const engine = await loadEngine();
  for (const [chord, frets] of Object.entries(CHORDS)) {
    const order = inTimeOrder(strum(engine, chord, "up", 30)).map((entry) => entry.string);
    assert.deepEqual(order, soundingStrings(frets).reverse(), `${chord} up`);
  }
});

test("s2.engine.skip-muted", async () => {
  const engine = await loadEngine();
  for (const [chord, frets] of Object.entries(CHORDS)) {
    for (const direction of ["down", "up"]) {
      const strings = strum(engine, chord, direction, 30).map((entry) => entry.string).sort();
      assert.deepEqual(strings, soundingStrings(frets).sort(), `${chord} ${direction}: only sounding strings`);
    }
  }
  assert.deepEqual(engine.strumSchedule([-1, -1, -1, -1, -1, -1], "down", START, 30), [], "an all-muted shape has no notes");
});

test("s2.engine.time-seconds", async () => {
  const engine = await loadEngine();
  for (const spreadMs of [10, 30, 100]) {
    for (const chord of ["C", "Em", "F", "D"]) {
      const entries = strum(engine, chord, "down", spreadMs, 10);
      const set = spreadMs / 1000;
      for (const entry of entries) {
        assert.ok(entry.time >= 10 - EPS && entry.time <= 10 + entries.length * set + EPS, `${chord} at ${spreadMs} ms: time ${entry.time} is not seconds after the start`);
      }
      const span = timeSpan(entries);
      assert.ok(span >= 0.4 * set - EPS && span <= entries.length * set + EPS, `${chord} at ${spreadMs} ms: span ${span} s is outside what ${spreadMs} ms allows`);
    }
  }
});

test("s2.engine.one-after-another", async () => {
  const engine = await loadEngine();
  for (const chord of ["C", "G", "Em", "F", "D"]) {
    for (const direction of ["down", "up"]) {
      const times = inTimeOrder(strum(engine, chord, direction, 30)).map((entry) => entry.time);
      for (let i = 1; i < times.length; i += 1) {
        assert.ok(times[i] - times[i - 1] > 1e-6, `${chord} ${direction}: notes ${i - 1} and ${i} start together or out of order`);
      }
    }
  }
});

test("s2.engine.spread-set", async () => {
  const engine = await loadEngine();
  for (const chord of ["C", "G", "D"]) {
    const spans = [25, 50, 100].map((spreadMs) => timeSpan(strum(engine, chord, "down", spreadMs)));
    assert.ok(spans[0] < spans[1] && spans[1] < spans[2], `${chord}: a longer set time must give a longer strum, got ${spans.join(", ")}`);
    assert.ok(spans[2] >= 2 * spans[0], `${chord}: 100 ms must spread at least twice as far as 25 ms, got ${spans[2]} and ${spans[0]}`);
  }
});

test("s2.engine.spread-zero", async () => {
  const engine = await loadEngine();
  for (const chord of ["C", "G", "Em", "F"]) {
    for (const direction of ["down", "up"]) {
      const entries = strum(engine, chord, direction, 0);
      assert.equal(entries.length, soundingStrings(CHORDS[chord]).length, `${chord} ${direction}: notes at 0 ms`);
      for (const entry of entries) {
        assert.ok(entry.time >= START - EPS && entry.time - START <= 0.001, `${chord} ${direction}: a 0 ms strum started a note ${entry.time - START} s late`);
      }
    }
  }
});

test("s2.engine.start-time", async () => {
  const engine = await loadEngine();
  for (const direction of ["down", "up"]) {
    const early = strum(engine, "G", direction, 30, 0);
    const late = strum(engine, "G", direction, 30, 5.25);
    assert.ok(Math.abs(Math.min(...early.map((entry) => entry.time))) < 1e-6, `${direction}: the first note must start at the start time`);
    assert.ok(Math.abs(Math.min(...late.map((entry) => entry.time)) - 5.25) < 1e-6, `${direction}: the first note must start at the start time`);
    const byString = (entries) => Object.fromEntries(entries.map((entry) => [entry.string, entry.time]));
    const a = byString(early);
    const b = byString(late);
    for (const string of Object.keys(a)) assert.ok(Math.abs(b[string] - a[string] - 5.25) < 1e-9, `${direction}: string ${string} did not move with the start time`);
  }
});
