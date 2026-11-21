// Hidden engine tests, step 5 (prompt step-5.txt). Project root: the GUITAR_ROOT environment variable.
// Each test imports the engine itself, so a missing engine fails every test and never the file.
// Test names are the IDs of spec-map.json.
//
// "The level falls by 60 dB in 1, 3 and 6 seconds" is measured as a rate on the level of the whole
// note, between 0.2 s and the point 40 dB below the level at 0.2 s (see decay.mjs), and must be within
// 20% of the set time. That accepts a decay set on the fundamental alone and one set on the whole note.
import assert from "node:assert/strict";
import test from "node:test";
import { loadEngine } from "./load.mjs";
import { OPEN_MIDI, midiHz } from "./helpers.mjs";
import { centsBetween, estimatePitch } from "./pitch.mjs";
import { decayTime60 } from "./decay.mjs";

const SAMPLE_RATE = 44100;
const TOLERANCE = 0.2;
const MEASURED_HZ = 110;

for (const [label, decaySeconds] of [["short", 1], ["normal", 3], ["long", 6]]) {
  test(`s5.engine.decay-${label}`, async () => {
    const { renderPluck } = await loadEngine();
    const samples = renderPluck({ frequency: MEASURED_HZ, sampleRate: SAMPLE_RATE, durationSeconds: 1.3 * decaySeconds + 0.3, seed: 7, decaySeconds });
    const measured = decayTime60(samples, SAMPLE_RATE);
    assert.ok(Number.isFinite(measured), `could not measure the decay of a ${MEASURED_HZ} Hz note with decaySeconds ${decaySeconds}`);
    assert.ok(
      Math.abs(measured / decaySeconds - 1) <= TOLERANCE,
      `decaySeconds ${decaySeconds}: the level falls 60 dB in about ${measured.toFixed(2)} s, allowed ${(decaySeconds * (1 - TOLERANCE)).toFixed(2)} to ${(decaySeconds * (1 + TOLERANCE)).toFixed(2)} s`,
    );
  });
}

test("s5.engine.decay-keeps-pitch", async () => {
  const { renderPluck } = await loadEngine();
  const bad = [];
  for (const decaySeconds of [1, 6]) {
    for (const string of [6, 3, 1]) {
      for (const fret of [0, 12]) {
        const frequency = midiHz(OPEN_MIDI[string] + fret);
        const samples = renderPluck({ frequency, sampleRate: SAMPLE_RATE, durationSeconds: 0.6, seed: string * 100 + fret, decaySeconds });
        const measured = estimatePitch(samples, SAMPLE_RATE);
        const cents = measured === null ? NaN : centsBetween(measured, frequency);
        if (!(Math.abs(cents) <= 5)) bad.push(`decaySeconds ${decaySeconds} string ${string} fret ${fret}: ${Number.isNaN(cents) ? "no pitch" : cents.toFixed(1) + " cents"}`);
      }
    }
  }
  assert.equal(bad.length, 0, `pitch outside 5 cents with decaySeconds: ${bad.join("; ")}`);
});
