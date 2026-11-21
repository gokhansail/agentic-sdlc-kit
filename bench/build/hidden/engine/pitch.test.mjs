// Known-answer test of the pitch estimator on signals whose pitch is known by construction.
// It needs no project folder, so it passes on an empty project.
import assert from "node:assert/strict";
import test from "node:test";
import { centsBetween, estimatePitch } from "./pitch.mjs";

const RATES = [44100, 48000];
const SINE_HZ = [82.4069, 110, 146.83, 196, 246.94, 329.63, 440, 659.26, 987.77, 1976];
const LIMIT_CENTS = 0.5;

for (const sampleRate of RATES) {
  test(`estimator.sine-${sampleRate}`, () => {
    for (const hz of SINE_HZ) {
      const x = new Float32Array(sampleRate);
      for (let i = 0; i < x.length; i += 1) x[i] = Math.sin((2 * Math.PI * hz * i) / sampleRate);
      const measured = estimatePitch(x, sampleRate);
      assert.ok(measured !== null, `no pitch found for a ${hz} Hz sine`);
      const cents = centsBetween(measured, hz);
      assert.ok(Math.abs(cents) < LIMIT_CENTS, `${hz} Hz sine at ${sampleRate}: ${cents.toFixed(4)} cents`);
    }
  });

  test(`estimator.decaying-harmonics-${sampleRate}`, () => {
    for (const hz of [82.4, 196, 329.63, 987.77]) {
      const x = new Float32Array(sampleRate);
      for (let i = 0; i < x.length; i += 1) {
        const t = i / sampleRate;
        const w = 2 * Math.PI * hz * t;
        x[i] = Math.exp(-2 * t) * (Math.sin(w) + 0.7 * Math.sin(2 * w + 1) + 0.5 * Math.sin(3 * w + 2));
      }
      const measured = estimatePitch(x, sampleRate);
      assert.ok(measured !== null, `no pitch found for ${hz} Hz with harmonics`);
      const cents = centsBetween(measured, hz);
      assert.ok(Math.abs(cents) < LIMIT_CENTS, `${hz} Hz with harmonics at ${sampleRate}: ${cents.toFixed(4)} cents`);
    }
  });
}

test("estimator.silence", () => {
  assert.equal(estimatePitch(new Float32Array(44100), 44100), null);
});
