// MIDI note number of each open string, indexed by guitar string number (1 is the high E).
// String 7 is the low B of a 7-string guitar; drop D lowers it to A1 as well.
const TUNINGS = {
  standard: [null, 64, 59, 55, 50, 45, 40, 35],
  dropD: [null, 64, 59, 55, 50, 45, 38, 33],
  openG: [null, 62, 59, 55, 50, 43, 38, 35],
};

const NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];

export function noteFrequency(string, fret, tuning = "standard") {
  if (!Number.isInteger(string) || string < 1 || string > 7) {
    throw new RangeError(`string must be an integer from 1 to 7, got ${string}`);
  }
  if (!Number.isFinite(fret)) {
    throw new RangeError(`fret must be a finite number, got ${fret}`);
  }
  if (!Object.hasOwn(TUNINGS, tuning)) {
    throw new RangeError(`unknown tuning: ${tuning}`);
  }
  return 440 * Math.pow(2, (TUNINGS[tuning][string] + fret - 69) / 12);
}

// Nearest equal-tempered note and the distance to it in whole cents, for example {name: "A4", cents: 20}.
export function noteName(frequency) {
  if (!(frequency > 0)) {
    throw new RangeError(`frequency must be above 0, got ${frequency}`);
  }
  const midi = 69 + 12 * Math.log2(frequency / 440);
  const nearest = Math.round(midi);
  const cents = Math.round((midi - nearest) * 100) + 0; // + 0 turns -0 into 0
  return { name: `${NAMES[((nearest % 12) + 12) % 12]}${Math.floor(nearest / 12) - 1}`, cents };
}
