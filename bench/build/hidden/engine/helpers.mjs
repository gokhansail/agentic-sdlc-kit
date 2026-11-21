// Shared constants and small checks of the hidden engine tests from step 2 on. They are kept apart
// from the engine under test, so a test never depends on the code it checks.
import assert from "node:assert/strict";

// MIDI note of each open string in standard tuning, indexed by string number (1 is the high E).
export const OPEN_MIDI = [null, 64, 59, 55, 50, 45, 40];
export const midiHz = (midi) => 440 * 2 ** ((midi - 69) / 12);

// Chord shapes of SPEC.md: 6 frets from string 6 to string 1, -1 for a muted string.
export const CHORDS = {
  C: [-1, 3, 2, 0, 1, 0],
  G: [3, 2, 0, 0, 0, 3],
  D: [-1, -1, 0, 2, 3, 2],
  Em: [0, 2, 2, 0, 0, 0],
  Am: [-1, 0, 2, 2, 1, 0],
  F: [1, 3, 3, 2, 1, 1],
  A: [-1, 0, 2, 2, 2, 0],
  E: [0, 2, 2, 1, 0, 0],
};

// Strings that sound in a 6-fret shape, from string 6 to string 1.
export function soundingStrings(frets) {
  return [6, 5, 4, 3, 2, 1].filter((string) => frets[6 - string] >= 0);
}

export function close(actual, expected, message) {
  assert.ok(Number.isFinite(actual), `${message}: got ${actual}`);
  assert.ok(Math.abs(actual / expected - 1) < 1e-6, `${message}: expected ${expected}, got ${actual}`);
}

// Entries of a schedule in the order they sound; equal times keep the order of the array.
export function inTimeOrder(entries) {
  return entries
    .map((entry, index) => ({ entry, index }))
    .sort((a, b) => a.entry.time - b.entry.time || a.index - b.index)
    .map(({ entry }) => entry);
}

export function timeSpan(entries) {
  const times = entries.map((entry) => entry.time);
  return Math.max(...times) - Math.min(...times);
}

// The hearing rule shared by the step 7 and handoff tests: `louder(a, b)` is true when the accent value a
// is a stronger click than b, whether the engine uses booleans or numbers for it.
export function louder(a, b) {
  if (typeof a === "boolean" && typeof b === "boolean") return a && !b;
  if (typeof a === "number" && typeof b === "number") return a > b;
  return false;
}
