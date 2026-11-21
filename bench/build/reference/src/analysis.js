// Analysis of rendered notes: a magnitude spectrum and a pitch detector. Pure functions on samples.
const MAX_FRAME = 16384;
const MIN_HZ = 40;
const MAX_HZ = 2000;

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
    for (let start = 0; start < n; start += size) {
      for (let k = 0; k < size / 2; k += 1) {
        const wRe = Math.cos(angle * k);
        const wIm = Math.sin(angle * k);
        const a = start + k;
        const b = a + size / 2;
        const tRe = re[b] * wRe - im[b] * wIm;
        const tIm = re[b] * wIm + im[b] * wRe;
        re[b] = re[a] - tRe;
        im[b] = im[a] - tIm;
        re[a] += tRe;
        im[a] += tIm;
      }
    }
  }
}

// Hann-weighted spectrum of the first samples; magnitudes are amplitudes, frequencies are in Hz.
export function spectrum(samples, sampleRate) {
  const n = Math.min(samples.length, MAX_FRAME);
  let size = 2;
  while (size < n) size <<= 1;
  const re = new Float64Array(size);
  const im = new Float64Array(size);
  for (let i = 0; i < n; i += 1) re[i] = samples[i] * (0.5 - 0.5 * Math.cos((2 * Math.PI * i) / n));
  fft(re, im);
  const frequencies = [];
  const magnitudes = [];
  for (let k = 0; k <= size / 2; k += 1) {
    frequencies.push((k * sampleRate) / size);
    magnitudes.push(n > 0 ? Math.hypot(re[k], im[k]) / (n / 4) : 0);
  }
  return { frequencies, magnitudes };
}

// First strong peak of the normalised autocorrelation, with parabolic interpolation.
function roughFrequency(x, sampleRate) {
  const n = x.length;
  const minLag = Math.max(2, Math.floor(sampleRate / MAX_HZ));
  const maxLag = Math.min(n - 2, Math.ceil(sampleRate / MIN_HZ));
  const cumulative = new Float64Array(n + 1);
  for (let i = 0; i < n; i += 1) cumulative[i + 1] = cumulative[i] + x[i] * x[i];
  const r = new Float64Array(maxLag + 2);
  for (let lag = 1; lag <= maxLag + 1; lag += 1) {
    let sum = 0;
    for (let i = 0; i + lag < n; i += 1) sum += x[i] * x[i + lag];
    const head = cumulative[n - lag];
    const tail = cumulative[n] - cumulative[lag];
    r[lag] = sum / Math.sqrt(head * tail || 1);
  }
  let start = 1;
  while (start < maxLag && r[start] > 0) start += 1; // leave the lobe around lag 0
  let best = 0;
  for (let lag = Math.max(start, minLag); lag <= maxLag; lag += 1) best = Math.max(best, r[lag]);
  if (best <= 0.2) return 0;
  for (let lag = Math.max(start, minLag); lag <= maxLag; lag += 1) {
    if (r[lag] >= 0.9 * best && r[lag] >= r[lag - 1] && r[lag] > r[lag + 1]) {
      const denominator = r[lag - 1] - 2 * r[lag] + r[lag + 1];
      const shift = denominator === 0 ? 0 : (0.5 * (r[lag - 1] - r[lag + 1])) / denominator;
      return sampleRate / (lag + shift);
    }
  }
  return 0;
}

// Magnitude of the Hann-weighted DFT at one frequency. A positive weight never moves the peak of
// a decaying tone away from its frequency, so the maximum is a precise pitch.
function dftMagnitude(weighted, sampleRate, frequency) {
  const angle = (2 * Math.PI * frequency) / sampleRate;
  const stepRe = Math.cos(angle);
  const stepIm = Math.sin(angle);
  let wRe = 1;
  let wIm = 0;
  let sumRe = 0;
  let sumIm = 0;
  for (let i = 0; i < weighted.length; i += 1) {
    sumRe += weighted[i] * wRe;
    sumIm -= weighted[i] * wIm;
    const nextRe = wRe * stepRe - wIm * stepIm;
    wIm = wRe * stepIm + wIm * stepRe;
    wRe = nextRe;
  }
  return Math.hypot(sumRe, sumIm);
}

// Pitch of a note in Hz, or 0 when there is none. Long notes are read from 0.1 s on, past the pick.
export function detectPitch(samples, sampleRate) {
  const from = samples.length > 0.6 * sampleRate ? Math.round(0.1 * sampleRate) : 0;
  const n = Math.min(samples.length - from, MAX_FRAME);
  if (n < (2 * sampleRate) / MIN_HZ + 4) return 0;
  const x = new Float64Array(n);
  let mean = 0;
  for (let i = 0; i < n; i += 1) {
    x[i] = samples[from + i];
    mean += x[i];
  }
  mean /= n;
  for (let i = 0; i < n; i += 1) x[i] -= mean;

  const rough = roughFrequency(x, sampleRate);
  if (rough === 0) return 0;

  const weighted = x.map((value, i) => value * (0.5 - 0.5 * Math.cos((2 * Math.PI * i) / n)));
  const step = sampleRate / n / 4;
  let bestFrequency = rough;
  let bestValue = -1;
  for (let f = rough * 0.975; f <= rough * 1.025; f += step) {
    const value = dftMagnitude(weighted, sampleRate, f);
    if (value > bestValue) {
      bestValue = value;
      bestFrequency = f;
    }
  }
  let low = bestFrequency - step;
  let high = bestFrequency + step;
  for (let i = 0; i < 30; i += 1) {
    const a = low + (high - low) / 3;
    const b = high - (high - low) / 3;
    if (dftMagnitude(weighted, sampleRate, a) < dftMagnitude(weighted, sampleRate, b)) low = a;
    else high = b;
  }
  return (low + high) / 2;
}
