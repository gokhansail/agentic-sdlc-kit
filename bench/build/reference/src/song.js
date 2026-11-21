import { chordShape } from "./chords.js";
import { clampTempo } from "./metronome.js";

// "C:4 G:4 Am:2 F:2" becomes [{chord: "C", beats: 4}, ...]. An unknown chord or a bad count throws.
export function parseSong(text) {
  const items = String(text).trim().split(/\s+/).filter(Boolean);
  return items.map((item) => {
    const match = /^([^:]+):(\d+)$/.exec(item);
    if (!match) throw new SyntaxError(`expected chord:beats, got "${item}"`);
    const [, chord, count] = match;
    chordShape(chord); // throws on a chord it does not know
    const beats = Number(count);
    if (beats < 1) throw new RangeError(`beats must be at least 1 in "${item}"`);
    return { chord, beats };
  });
}

// Each chord is strummed down on its first beat.
export function songSchedule(song, bpm, startTime) {
  const interval = 60 / clampTempo(bpm);
  let beat = 0;
  return song.map(({ chord, beats }) => {
    const entry = { time: startTime + beat * interval, chord };
    beat += beats;
    return entry;
  });
}
