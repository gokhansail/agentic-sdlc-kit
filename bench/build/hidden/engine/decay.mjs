// Decay measure used by the step 5 test. It has its own known-answer test on synthetic tones
// (decay.test.mjs), so a decay failure on a render is the render's, not the measure's.
//
// "The level falls by 60 dB in T seconds" is read as a rate: the level of the note (RMS in 50 ms
// blocks) falls 60 / T dB per second. The rate is the slope of a line fitted to the level in dB from
// 0.2 s, after the pick noise, until the level is 40 dB below its value at 0.2 s, or to the end of the
// render. T is then 60 over that slope. A note that never falls 40 dB in the render is measured on the
// part it has, so a decay that is too slow still gives a long T.

const BLOCK_SECONDS = 0.05;
const START_SECONDS = 0.2;
const DEPTH_DB = 40;

export function levelBlocks(samples, sampleRate) {
  const size = Math.round(BLOCK_SECONDS * sampleRate);
  const blocks = [];
  for (let first = 0; first + size <= samples.length; first += size) {
    let sum = 0;
    for (let i = first; i < first + size; i += 1) sum += samples[i] * samples[i];
    const rms = Math.sqrt(sum / size);
    blocks.push({ time: (first + size / 2) / sampleRate, db: rms > 0 ? 20 * Math.log10(rms) : -Infinity });
  }
  return blocks;
}

// Seconds for a 60 dB fall, or NaN when the render is too short or silent to tell.
export function decayTime60(samples, sampleRate) {
  const blocks = levelBlocks(samples, sampleRate).filter((block) => block.time >= START_SECONDS);
  if (blocks.length < 4 || !Number.isFinite(blocks[0].db)) return NaN;
  const floor = blocks[0].db - DEPTH_DB;
  const used = [];
  for (const block of blocks) {
    if (!(block.db >= floor)) break;
    used.push(block);
  }
  if (used.length < 4) return NaN;
  const n = used.length;
  const meanTime = used.reduce((sum, block) => sum + block.time, 0) / n;
  const meanDb = used.reduce((sum, block) => sum + block.db, 0) / n;
  let covariance = 0;
  let variance = 0;
  for (const block of used) {
    covariance += (block.time - meanTime) * (block.db - meanDb);
    variance += (block.time - meanTime) ** 2;
  }
  const slope = covariance / variance; // dB per second, negative while the note dies away
  return slope < 0 ? -60 / slope : Infinity;
}
