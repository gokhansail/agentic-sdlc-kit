// Hidden engine tests, step 3 (prompt step-3.txt). Project root: the GUITAR_ROOT environment variable.
// Each test imports the engine itself, so a missing engine fails every test and never the file.
// Test names are the IDs of spec-map.json. The two spectrum tests are retired at step 6.
//
// Readings the tests accept: noteName rounds the cents any way that gives a whole number within 1 of
// the exact distance, 1 included (445 Hz is 19.56 cents above A4, so 19 and 20 both pass); a note name is checked
// on natural notes only, because the text gives no sign for sharps. detectPitch is compared with the
// pitch an independent estimator measures on the same render (0.1 s to 0.5 s, known-answer tested in
// pitch.test.mjs), so a render that is a little off its frequency does not count against detectPitch.
import assert from "node:assert/strict";
import test from "node:test";
import { loadEngine } from "./load.mjs";
import { OPEN_MIDI, midiHz } from "./helpers.mjs";
import { centsBetween, estimatePitch } from "./pitch.mjs";

const RATES = [44100, 48000];
const DETECT_LIMIT_CENTS = 5;

function sine(hz, sampleRate, seconds) {
  const x = new Float32Array(Math.round(sampleRate * seconds));
  for (let i = 0; i < x.length; i += 1) x[i] = 0.5 * Math.sin((2 * Math.PI * hz * i) / sampleRate);
  return x;
}

// The spectrum export is checked by the two retired spectrum tests, so removing it with the view at step 6 is no regression.
test("s3.engine.exports", async () => {
  const engine = await loadEngine();
  for (const name of ["detectPitch", "noteName"]) {
    assert.equal(typeof engine[name], "function", `${name} is not an exported function`);
  }
});

test("s3.engine.spectrum-shape", async () => {
  const { spectrum } = await loadEngine();
  for (const sampleRate of RATES) {
    const result = spectrum(sine(440, sampleRate, 0.5), sampleRate);
    assert.ok(result && typeof result === "object", "spectrum must return an object");
    for (const key of ["frequencies", "magnitudes"]) {
      assert.ok(Array.isArray(result[key]) || ArrayBuffer.isView(result[key]), `${key} must be an array`);
    }
    assert.equal(result.frequencies.length, result.magnitudes.length, "frequencies and magnitudes must have one entry per bin");
    assert.ok(result.frequencies.length >= 8, "the spectrum has too few bins");
    for (let i = 0; i < result.frequencies.length; i += 1) {
      assert.ok(Number.isFinite(result.frequencies[i]) && result.frequencies[i] >= 0, `frequency ${i} is ${result.frequencies[i]}`);
      assert.ok(Number.isFinite(result.magnitudes[i]), `magnitude ${i} is ${result.magnitudes[i]}`);
    }
  }
});

test("s3.engine.spectrum-peak", async () => {
  const { spectrum } = await loadEngine();
  for (const sampleRate of RATES) {
    for (const hz of [196, 440, 987.77]) {
      const { frequencies, magnitudes } = spectrum(sine(hz, sampleRate, 0.5), sampleRate);
      let peak = 0;
      for (let i = 1; i < magnitudes.length; i += 1) if (magnitudes[i] > magnitudes[peak]) peak = i;
      const around = [frequencies[peak - 1], frequencies[peak + 1]].filter((value) => value !== undefined);
      const resolution = Math.max(...around.map((value) => Math.abs(value - frequencies[peak])));
      assert.ok(Math.abs(frequencies[peak] - hz) <= 1.5 * resolution, `a ${hz} Hz sine at ${sampleRate}: the highest magnitude is at ${frequencies[peak]} Hz (bin spacing ${resolution} Hz)`);
    }
  }
});

for (const sampleRate of RATES) {
  test(`s3.engine.detect-render-${sampleRate}`, async () => {
    const { renderPluck, detectPitch } = await loadEngine();
    const bad = [];
    for (let string = 1; string <= 6; string += 1) {
      for (const fret of [0, 5, 12]) {
        const frequency = midiHz(OPEN_MIDI[string] + fret);
        const samples = renderPluck({ frequency, sampleRate, durationSeconds: 1, seed: string * 100 + fret });
        const measured = estimatePitch(samples, sampleRate) ?? frequency;
        const found = detectPitch(samples, sampleRate);
        const cents = Number.isFinite(found) && found > 0 ? centsBetween(found, measured) : NaN;
        if (!(Math.abs(cents) <= DETECT_LIMIT_CENTS)) bad.push(`string ${string} fret ${fret} (${frequency.toFixed(2)} Hz): ${Number.isNaN(cents) ? `got ${found}` : `${cents.toFixed(1)} cents`}`);
      }
    }
    assert.equal(bad.length, 0, `detectPitch outside ${DETECT_LIMIT_CENTS} cents at ${sampleRate} Hz: ${bad.join("; ")}`);
  });
}

test("s3.engine.detect-sine", async () => {
  const { detectPitch } = await loadEngine();
  for (const sampleRate of RATES) {
    for (const hz of [82.41, 110, 196, 301.7, 440, 659.26]) {
      const found = detectPitch(sine(hz, sampleRate, 0.5), sampleRate);
      assert.ok(Number.isFinite(found) && found > 0, `a ${hz} Hz sine gave ${found}`);
      const cents = centsBetween(found, hz);
      assert.ok(Math.abs(cents) <= DETECT_LIMIT_CENTS, `a ${hz} Hz sine at ${sampleRate} Hz gave ${found} Hz (${cents.toFixed(1)} cents)`);
    }
  }
});

test("s3.engine.notename-exact", async () => {
  const { noteName } = await loadEngine();
  const naturals = [[64, "E4"], [59, "B3"], [55, "G3"], [50, "D3"], [45, "A2"], [40, "E2"], [69, "A4"], [60, "C4"], [62, "D4"]];
  for (const [midi, name] of naturals) {
    const result = noteName(midiHz(midi));
    assert.equal(result.name, name, `name of MIDI note ${midi}`);
    assert.ok(result.cents === 0, `cents of ${name} should be 0, got ${result.cents}`);
  }
  assert.equal(noteName(440).name, "A4");
});

test("s3.engine.notename-cents", async () => {
  const { noteName } = await loadEngine();
  const cases = [[440, "A4", 0], [445, "A4", 1200 * Math.log2(445 / 440)], [435, "A4", 1200 * Math.log2(435 / 440)]];
  for (const offset of [-30, -10, 10, 30]) cases.push([midiHz(64) * 2 ** (offset / 1200), "E4", offset]);
  for (const offset of [-25, 25]) cases.push([midiHz(45) * 2 ** (offset / 1200), "A2", offset]);
  for (const [frequency, name, exact] of cases) {
    const result = noteName(frequency);
    assert.equal(result.name, name, `name at ${frequency} Hz`);
    assert.ok(Number.isInteger(result.cents) && Math.abs(result.cents - exact) <= 1 + 1e-9, `cents at ${frequency} Hz: expected about ${exact.toFixed(2)}, got ${result.cents}`);
  }
});

test("s3.engine.notename-whole", async () => {
  const { noteName } = await loadEngine();
  for (const frequency of [82.1, 123.4, 301.7, 440.5, 777.7, 987.1]) {
    const { cents } = noteName(frequency);
    assert.ok(Number.isInteger(cents), `cents at ${frequency} Hz is ${cents}, not a whole number`);
    assert.ok(Math.abs(cents) <= 50, `cents at ${frequency} Hz is ${cents}, more than half a semitone from the nearest note`);
  }
});
