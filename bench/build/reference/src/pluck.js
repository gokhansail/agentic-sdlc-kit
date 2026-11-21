import { makeRandom } from "./prng.js";

// Karplus-Strong string: a noise burst circulates in a delay line. Each pass goes through a
// two-point average (a lowpass with a delay of exactly 0.5 sample) and a first-order allpass that
// supplies the fractional part of the loop delay, so the loop length is fs / frequency to a
// small fraction of a sample at every pitch.
const LOOP_T60_SECONDS = 3; // the fundamental falls by 60 dB in about this time
const PICK_POSITION = 0.2; // fraction of the string where the pick lifts it (a comb on the burst)
const PEAK = 0.8;

// Phase delay in samples of the allpass (a + z^-1) / (1 + a z^-1) at angular frequency w.
function allpassDelay(a, w) {
  const phaseNumerator = Math.atan2(-Math.sin(w), a + Math.cos(w));
  const phaseDenominator = Math.atan2(-a * Math.sin(w), 1 + a * Math.cos(w));
  return -(phaseNumerator - phaseDenominator) / w;
}

// The allpass coefficient whose phase delay at w is `delay` samples. The delay falls as a rises.
function allpassCoefficient(delay, w) {
  let low = -0.9;
  let high = 0.9;
  for (let i = 0; i < 60; i += 1) {
    const mid = (low + high) / 2;
    if (allpassDelay(mid, w) > delay) low = mid;
    else high = mid;
  }
  return (low + high) / 2;
}

export function renderPluck({ frequency, sampleRate, durationSeconds, seed }) {
  if (!(frequency > 0) || !(sampleRate > 0) || !(frequency < sampleRate / 4)) {
    throw new RangeError("frequency must be above 0 and below a quarter of the sample rate");
  }
  const length = Math.round(sampleRate * durationSeconds);
  const out = new Float32Array(Math.max(length, 0));
  if (out.length === 0) return out;

  const period = sampleRate / frequency;
  const w = (2 * Math.PI * frequency) / sampleRate;
  const wholeDelay = Math.floor(period - 0.5 - 1);
  const apDelay = period - 0.5 - wholeDelay; // in [1, 2)
  const a = allpassCoefficient(apDelay, w);
  const gain = Math.min(0.9999, Math.pow(10, -3 / (frequency * LOOP_T60_SECONDS)));

  // The first wholeDelay + 1 samples are the noise burst; the rest is the loop.
  const total = out.length;
  const y = new Float64Array(Math.max(total, wholeDelay + 1));
  const random = makeRandom(seed);
  const burstLength = wholeDelay + 1;
  const noise = new Float64Array(burstLength);
  let mean = 0;
  for (let i = 0; i < burstLength; i += 1) {
    noise[i] = 2 * random() - 1;
    mean += noise[i];
  }
  mean /= burstLength;
  const lag = Math.max(1, Math.round(PICK_POSITION * burstLength));
  for (let i = 0; i < burstLength; i += 1) {
    const here = noise[i] - mean;
    const before = i >= lag ? noise[i - lag] - mean : 0;
    y[i] = here - before;
  }

  let previousInput = 0;
  let previousOutput = 0;
  for (let n = burstLength; n < y.length; n += 1) {
    const filtered = (gain * (y[n - wholeDelay] + y[n - wholeDelay - 1])) / 2;
    const value = a * filtered + previousInput - a * previousOutput;
    previousInput = filtered;
    previousOutput = value;
    y[n] = value;
  }

  let peak = 0;
  for (let i = 0; i < total; i += 1) peak = Math.max(peak, Math.abs(y[i]));
  const scale = peak > 0 ? PEAK / peak : 0;
  for (let i = 0; i < total; i += 1) out[i] = y[i] * scale;
  return out;
}
