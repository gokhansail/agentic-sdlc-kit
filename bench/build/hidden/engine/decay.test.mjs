// Known-answer test of the decay measure on tones whose 60 dB time is known by construction.
// It needs no project folder, so it passes on an empty project.
import assert from "node:assert/strict";
import test from "node:test";
import { decayTime60 } from "./decay.mjs";

const SAMPLE_RATE = 44100;

function tone(t60, harmonics) {
  const x = new Float32Array(Math.round(SAMPLE_RATE * (1.3 * t60 + 0.3)));
  for (let i = 0; i < x.length; i += 1) {
    const t = i / SAMPLE_RATE;
    let value = 0;
    for (let k = 1; k <= harmonics; k += 1) value += Math.sin(2 * Math.PI * 110 * k * t + k) / k;
    x[i] = (0.8 * 10 ** (-3 * t / t60) * value) / 2;
  }
  return x;
}

for (const harmonics of [1, 4]) {
  test(`estimator.decay-${harmonics}-harmonics`, () => {
    for (const t60 of [1, 3, 6]) {
      const measured = decayTime60(tone(t60, harmonics), SAMPLE_RATE);
      assert.ok(Math.abs(measured / t60 - 1) < 0.03, `T60 ${t60} s measured as ${measured} s`);
    }
  });
}

test("estimator.decay-silence", () => {
  assert.ok(Number.isNaN(decayTime60(new Float32Array(44100), SAMPLE_RATE)));
});
