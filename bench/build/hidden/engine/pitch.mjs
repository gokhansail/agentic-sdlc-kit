// Pitch estimator used by the hidden engine tests. It has its own known-answer test on pure sines
// (pitch.test.mjs), so a pitch failure on a render is the render's, not the estimator's.
//
// Stage 1: normalised autocorrelation (by FFT) gives a rough fundamental.
// Stage 2: a Hann-windowed DFT magnitude is scanned around that value and the peak is refined
// by a ternary search. For a window that is never negative the magnitude peaks exactly at the
// signal's frequency, so an amplitude decay does not bias the result.

const MIN_HZ = 60;
const MAX_HZ = 2500;

export function centsBetween(measured, expected) {
  return 1200 * Math.log2(measured / expected);
}

function fft(re, im) {
  const n = re.length;
  for (let i = 1, j = 0; i < n; i += 1) {
    let bit = n >> 1;
    for (; j & bit; bit >>= 1) j ^= bit;
    j ^= bit;
    if (i < j) {
      [re[i], re[j]] = [re[j], re[i]];
      [im[i], im[j]] = [im[j], im[i]];
    }
  }
  for (let size = 2; size <= n; size <<= 1) {
    const angle = (-2 * Math.PI) / size;
    const stepRe = Math.cos(angle);
    const stepIm = Math.sin(angle);
    for (let start = 0; start < n; start += size) {
      let wRe = 1;
      let wIm = 0;
      for (let k = 0; k < size / 2; k += 1) {
        const a = start + k;
        const b = a + size / 2;
        const tRe = re[b] * wRe - im[b] * wIm;
        const tIm = re[b] * wIm + im[b] * wRe;
        re[b] = re[a] - tRe;
        im[b] = im[a] - tIm;
        re[a] += tRe;
        im[a] += tIm;
        const nextRe = wRe * stepRe - wIm * stepIm;
        wIm = wRe * stepIm + wIm * stepRe;
        wRe = nextRe;
      }
    }
  }
}

function roughFrequency(x, sampleRate) {
  const n = x.length;
  let size = 1;
  while (size < 2 * n) size <<= 1;
  const re = new Float64Array(size);
  const im = new Float64Array(size);
  re.set(x);
  fft(re, im);
  for (let i = 0; i < size; i += 1) {
    re[i] = re[i] * re[i] + im[i] * im[i];
    im[i] = 0;
  }
  fft(re, im); // power spectrum is real and even, so the forward FFT gives the autocorrelation
  const cumulative = new Float64Array(n + 1);
  for (let i = 0; i < n; i += 1) cumulative[i + 1] = cumulative[i] + x[i] * x[i];
  const maxLag = Math.min(n - 2, Math.ceil(sampleRate / MIN_HZ));
  const minLag = Math.max(2, Math.floor(sampleRate / MAX_HZ));
  const r = new Float64Array(maxLag + 2);
  for (let lag = 1; lag <= maxLag + 1; lag += 1) {
    const head = cumulative[n - lag];
    const tail = cumulative[n] - cumulative[lag];
    r[lag] = re[lag] / size / Math.sqrt(head * tail || 1);
  }
  // Skip the lobe around lag 0: start where the autocorrelation first goes negative.
  let start = 1;
  while (start < maxLag && r[start] > 0) start += 1;
  let best = 0;
  for (let lag = Math.max(start, minLag); lag <= maxLag; lag += 1) best = Math.max(best, r[lag]);
  if (best <= 0) return null;
  for (let lag = Math.max(start, minLag); lag <= maxLag; lag += 1) {
    if (r[lag] >= 0.9 * best && r[lag] >= r[lag - 1] && r[lag] > r[lag + 1]) {
      const left = r[lag - 1];
      const right = r[lag + 1];
      const denominator = left - 2 * r[lag] + right;
      const shift = denominator === 0 ? 0 : (0.5 * (left - right)) / denominator;
      return sampleRate / (lag + shift);
    }
  }
  return null;
}

function makeMagnitude(x, sampleRate) {
  const n = x.length;
  const windowed = new Float64Array(n);
  for (let i = 0; i < n; i += 1) windowed[i] = x[i] * (0.5 - 0.5 * Math.cos((2 * Math.PI * i) / n));
  return (frequency) => {
    const angle = (2 * Math.PI * frequency) / sampleRate;
    const stepRe = Math.cos(angle);
    const stepIm = Math.sin(angle);
    let wRe = 1;
    let wIm = 0;
    let sumRe = 0;
    let sumIm = 0;
    for (let i = 0; i < n; i += 1) {
      sumRe += windowed[i] * wRe;
      sumIm -= windowed[i] * wIm;
      const nextRe = wRe * stepRe - wIm * stepIm;
      wIm = wRe * stepIm + wIm * stepRe;
      wRe = nextRe;
    }
    return Math.hypot(sumRe, sumIm);
  };
}

// Returns the fundamental in Hz, measured on the samples from `from` to `to` seconds, or null when
// no pitch is found.
export function estimatePitch(samples, sampleRate, { from = 0.1, to = 0.5 } = {}) {
  const first = Math.round(from * sampleRate);
  const last = Math.min(samples.length, Math.round(to * sampleRate));
  if (last - first < 64) return null;
  const x = new Float64Array(last - first);
  let mean = 0;
  for (let i = 0; i < x.length; i += 1) {
    x[i] = samples[first + i];
    mean += x[i];
  }
  mean /= x.length;
  for (let i = 0; i < x.length; i += 1) x[i] -= mean;

  const rough = roughFrequency(x, sampleRate);
  if (rough === null) return null;

  const magnitude = makeMagnitude(x, sampleRate);
  const binWidth = sampleRate / x.length;
  const step = binWidth / 4;
  const span = rough * 0.025;
  let bestFrequency = rough;
  let bestValue = -1;
  for (let f = rough - span; f <= rough + span; f += step) {
    const value = magnitude(f);
    if (value > bestValue) {
      bestValue = value;
      bestFrequency = f;
    }
  }
  let low = bestFrequency - step;
  let high = bestFrequency + step;
  for (let i = 0; i < 40; i += 1) {
    const a = low + (high - low) / 3;
    const b = high - (high - low) / 3;
    if (magnitude(a) < magnitude(b)) low = a;
    else high = b;
  }
  return (low + high) / 2;
}
