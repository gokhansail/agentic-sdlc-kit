// MIDI note number of each open string, indexed by guitar string number (1 is the high E).
const OPEN_MIDI = [null, 64, 59, 55, 50, 45, 40];

export function noteFrequency(string, fret) {
  if (!Number.isInteger(string) || string < 1 || string > 6) {
    throw new RangeError(`string must be an integer from 1 to 6, got ${string}`);
  }
  if (!Number.isFinite(fret)) {
    throw new RangeError(`fret must be a finite number, got ${fret}`);
  }
  return 440 * Math.pow(2, (OPEN_MIDI[string] + fret - 69) / 12);
}
