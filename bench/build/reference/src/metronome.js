export const MIN_BPM = 40;
export const MAX_BPM = 220;
export const DEFAULT_BPM = 100;

// A tempo outside 40 to 220 is set to the nearest end and never refused.
export function clampTempo(bpm) {
  const value = Number(bpm);
  if (Number.isNaN(value)) return DEFAULT_BPM;
  return Math.min(MAX_BPM, Math.max(MIN_BPM, value));
}

// Clicks from time 0 up to durationSeconds, one per beat; the first beat of every bar is the accent.
export function metronomeClicks(bpm, beatsPerBar, durationSeconds) {
  const interval = 60 / clampTempo(bpm);
  const bar = Math.max(1, Math.round(beatsPerBar));
  const clicks = [];
  for (let beat = 0; beat * interval < durationSeconds; beat += 1) {
    clicks.push({ time: beat * interval, accent: beat % bar === 0 });
  }
  return clicks;
}
