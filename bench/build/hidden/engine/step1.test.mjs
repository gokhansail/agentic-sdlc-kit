// Hidden engine tests, step 1 (SPEC.md). Project root: the GUITAR_ROOT environment variable.
// Each test imports the engine itself, so a missing engine fails every test and never the file.
// Test names are the IDs of spec-map.json.
import assert from "node:assert/strict";
import test from "node:test";
import { loadEngine } from "./load.mjs";
import { centsBetween, estimatePitch } from "./pitch.mjs";

const RATES = [44100, 48000];
// MIDI note of each open string, indexed by string number (1 is the high E). Kept apart from the
// engine so a pitch test does not depend on noteFrequency.
const OPEN_MIDI = [null, 64, 59, 55, 50, 45, 40];
const midiHz = (midi) => 440 * 2 ** ((midi - 69) / 12);

const CHORDS = {
  C: [-1, 3, 2, 0, 1, 0],
  G: [3, 2, 0, 0, 0, 3],
  D: [-1, -1, 0, 2, 3, 2],
  Em: [0, 2, 2, 0, 0, 0],
  Am: [-1, 0, 2, 2, 1, 0],
  F: [1, 3, 3, 2, 1, 1],
  A: [-1, 0, 2, 2, 2, 0],
  E: [0, 2, 2, 1, 0, 0],
};

function close(actual, expected, message) {
  assert.ok(Number.isFinite(actual), `${message}: got ${actual}`);
  assert.ok(Math.abs(actual / expected - 1) < 1e-6, `${message}: expected ${expected}, got ${actual}`);
}

function expectAction(actual, expected) {
  assert.ok(actual !== null && typeof actual === "object", `expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`);
  for (const [key, value] of Object.entries(expected)) assert.deepEqual(actual[key], value, `field ${key} of ${JSON.stringify(actual)}`);
}

test("s1.engine.exports", async () => {
  const engine = await loadEngine();
  for (const name of ["noteFrequency", "renderPluck", "chordShape", "keyToAction"]) {
    assert.equal(typeof engine[name], "function", `${name} is not an exported function`);
  }
});

test("s1.engine.note-numbering", async () => {
  const { noteFrequency } = await loadEngine();
  for (let string = 2; string <= 6; string += 1) {
    assert.ok(noteFrequency(string - 1, 0) > noteFrequency(string, 0), `string ${string - 1} should sound higher than string ${string}`);
  }
  close(noteFrequency(1, 0) / noteFrequency(6, 0), 4, "high E over low E");
});

test("s1.engine.note-open-strings", async () => {
  const { noteFrequency } = await loadEngine();
  for (let string = 1; string <= 6; string += 1) {
    close(noteFrequency(string, 0), midiHz(OPEN_MIDI[string]), `open string ${string}`);
  }
});

test("s1.engine.note-a440", async () => {
  const { noteFrequency } = await loadEngine();
  close(noteFrequency(1, 5), 440, "string 1 fret 5 is A4");
  close(noteFrequency(2, 10), 440, "string 2 fret 10 is A4");
  close(noteFrequency(3, 14), 440, "string 3 fret 14 is A4");
  close(noteFrequency(5, 24), 440, "string 5 fret 24 is A4");
});

test("s1.engine.note-frets", async () => {
  const { noteFrequency } = await loadEngine();
  for (let string = 1; string <= 6; string += 1) {
    for (const fret of [1, 3, 7, 12, 19]) {
      close(noteFrequency(string, fret), midiHz(OPEN_MIDI[string] + fret), `string ${string} fret ${fret}`);
    }
  }
});

test("s1.engine.render-length", async () => {
  const { renderPluck } = await loadEngine();
  for (const [sampleRate, durationSeconds] of [[44100, 0.5], [48000, 0.25], [44100, 0.123], [48000, 0.7777], [44100, 1]]) {
    const samples = renderPluck({ frequency: 220, sampleRate, durationSeconds, seed: 1 });
    assert.ok(samples instanceof Float32Array, "renderPluck must return a Float32Array");
    assert.equal(samples.length, Math.round(sampleRate * durationSeconds), `length at ${sampleRate} Hz for ${durationSeconds} s`);
  }
});

test("s1.engine.render-range", async () => {
  const { renderPluck } = await loadEngine();
  for (const sampleRate of RATES) {
    for (const frequency of [82.41, 220, 659.26, 987.77]) {
      const samples = renderPluck({ frequency, sampleRate, durationSeconds: 0.6, seed: 3 });
      let peak = 0;
      for (const value of samples) {
        assert.ok(Number.isFinite(value) && value >= -1 && value <= 1, `sample ${value} outside [-1, 1] (${frequency} Hz, ${sampleRate} Hz)`);
        peak = Math.max(peak, Math.abs(value));
      }
      assert.ok(peak > 0.01, `the render of ${frequency} Hz is silent`);
    }
  }
});

test("s1.engine.render-seed", async () => {
  const { renderPluck } = await loadEngine();
  for (const seed of [0, 1, 42, 123456]) {
    const options = { frequency: 196, sampleRate: 44100, durationSeconds: 0.4, seed };
    const first = renderPluck(options);
    const second = renderPluck({ ...options });
    assert.equal(first.length, second.length);
    for (let i = 0; i < first.length; i += 1) {
      if (first[i] !== second[i]) assert.fail(`seed ${seed}: sample ${i} differs between two renders`);
    }
  }
});

for (const sampleRate of RATES) {
  for (let string = 1; string <= 6; string += 1) {
    test(`s1.engine.pitch-string${string}-${sampleRate}`, async () => {
      const { renderPluck } = await loadEngine();
      const bad = [];
      for (let fret = 0; fret <= 19; fret += 1) {
        const frequency = midiHz(OPEN_MIDI[string] + fret);
        const samples = renderPluck({ frequency, sampleRate, durationSeconds: 0.6, seed: string * 100 + fret });
        const measured = estimatePitch(samples, sampleRate);
        const cents = measured === null ? NaN : centsBetween(measured, frequency);
        if (!(Math.abs(cents) <= 5)) bad.push(`fret ${fret} (${frequency.toFixed(2)} Hz): ${Number.isNaN(cents) ? "no pitch" : cents.toFixed(1) + " cents"}`);
      }
      assert.equal(bad.length, 0, `string ${string} at ${sampleRate} Hz outside 5 cents: ${bad.join("; ")}`);
    });
  }
}

test("s1.engine.chord-shape", async () => {
  const { chordShape } = await loadEngine();
  for (const name of Object.keys(CHORDS)) {
    const shape = chordShape(name);
    assert.ok(Array.isArray(shape), `chordShape("${name}") must be an array`);
    assert.equal(shape.length, 6, `chordShape("${name}") must have 6 frets`);
    for (const fret of shape) assert.ok(Number.isInteger(fret) && fret >= -1, `chordShape("${name}") has ${fret}`);
  }
});

for (const [name, frets] of Object.entries(CHORDS)) {
  test(`s1.engine.chord-${name}`, async () => {
    const { chordShape } = await loadEngine();
    assert.deepEqual(Array.from(chordShape(name)), frets);
  });
}

test("s1.engine.keys-chords", async () => {
  const { keyToAction } = await loadEngine();
  const keys = { KeyQ: "C", KeyW: "G", KeyE: "D", KeyR: "Em", KeyA: "Am", KeyS: "F", KeyD: "A", KeyF: "E" };
  for (const [code, chord] of Object.entries(keys)) expectAction(keyToAction(code), { type: "chord", chord });
});

test("s1.engine.keys-open", async () => {
  const { keyToAction } = await loadEngine();
  expectAction(keyToAction("KeyZ"), { type: "open" });
});

test("s1.engine.keys-strum", async () => {
  const { keyToAction } = await loadEngine();
  expectAction(keyToAction("Space"), { type: "strum", direction: "down" });
  expectAction(keyToAction("KeyM"), { type: "strum", direction: "up" });
});

test("s1.engine.keys-mute", async () => {
  const { keyToAction } = await loadEngine();
  expectAction(keyToAction("Period"), { type: "mute" });
});

test("s1.engine.keys-strings", async () => {
  const { keyToAction } = await loadEngine();
  const keys = { KeyH: 6, KeyJ: 5, KeyK: 4, KeyL: 3, Semicolon: 2, Quote: 1 };
  for (const [code, string] of Object.entries(keys)) expectAction(keyToAction(code), { type: "pluck", string });
});

test("s1.engine.keys-null", async () => {
  const { keyToAction } = await loadEngine();
  for (const code of ["KeyX", "KeyC", "KeyV", "KeyB", "KeyN", "Enter", "Tab", "Escape", "Digit1", "ArrowUp", "ShiftLeft", "", "q"]) {
    assert.equal(keyToAction(code), null, `keyToAction("${code}") should be null`);
  }
});
