// Hidden engine tests, step 4 (prompt step-4.txt). Project root: the GUITAR_ROOT environment variable.
// Each test imports the engine itself, so a missing engine fails every test and never the file.
// Test names are the IDs of spec-map.json.
//
// The tuning lists are read from string 6 to string 1, as SPEC.md lists standard tuning. The capo is
// not an engine argument: the caller adds it to the fret, so the tests add it too and never pass one.
import assert from "node:assert/strict";
import test from "node:test";
import { loadEngine } from "./load.mjs";
import { CHORDS, OPEN_MIDI, close, midiHz } from "./helpers.mjs";

// MIDI note of each open string by tuning, indexed by string number.
const TUNING_MIDI = {
  standard: OPEN_MIDI,
  dropD: [null, 64, 59, 55, 50, 45, 38], // string 6 down to D2
  openG: [null, 62, 59, 55, 50, 43, 38], // D2 G2 D3 G3 B3 D4 from string 6 to string 1
};
const FRETS = [0, 1, 3, 7, 12, 19];

function checkTuning(noteFrequency, tuning) {
  for (let string = 1; string <= 6; string += 1) {
    for (const fret of FRETS) {
      close(noteFrequency(string, fret, tuning), midiHz(TUNING_MIDI[tuning][string] + fret), `${tuning} string ${string} fret ${fret}`);
    }
  }
}

test("s4.engine.tuning-default", async () => {
  const { noteFrequency } = await loadEngine();
  for (let string = 1; string <= 6; string += 1) {
    for (const fret of FRETS) {
      const expected = midiHz(OPEN_MIDI[string] + fret);
      close(noteFrequency(string, fret), expected, `no tuning, string ${string} fret ${fret}`);
      close(noteFrequency(string, fret, undefined), expected, `tuning undefined, string ${string} fret ${fret}`);
    }
  }
});

test("s4.engine.tuning-standard", async () => {
  const { noteFrequency } = await loadEngine();
  checkTuning(noteFrequency, "standard");
});

test("s4.engine.tuning-dropD", async () => {
  const { noteFrequency } = await loadEngine();
  checkTuning(noteFrequency, "dropD");
  close(noteFrequency(6, 0, "dropD"), 73.41619197935188, "string 6 of drop D is D2");
});

test("s4.engine.tuning-openG", async () => {
  const { noteFrequency } = await loadEngine();
  checkTuning(noteFrequency, "openG");
  close(noteFrequency(1, 0, "openG"), midiHz(62), "string 1 of open G is D4");
});

test("s4.engine.capo-fret-offset", async () => {
  const { noteFrequency } = await loadEngine();
  for (const tuning of Object.keys(TUNING_MIDI)) {
    for (let capo = 0; capo <= 7; capo += 1) {
      for (let string = 1; string <= 6; string += 1) {
        for (const fret of [0, 2, 5, 12, 19]) {
          close(noteFrequency(string, fret + capo, tuning), noteFrequency(string, fret, tuning) * 2 ** (capo / 12), `${tuning} capo ${capo} string ${string} fret ${fret}`);
        }
      }
    }
  }
});

test("s4.engine.capo-moves-shapes", async () => {
  const { chordShape, noteFrequency } = await loadEngine();
  for (const [name, frets] of Object.entries(CHORDS)) {
    assert.deepEqual(Array.from(chordShape(name)), frets, `chord ${name} must keep its shape`);
    for (const tuning of Object.keys(TUNING_MIDI)) {
      for (const capo of [0, 2, 5, 7]) {
        for (let string = 1; string <= 6; string += 1) {
          const fret = frets[6 - string];
          if (fret < 0) continue;
          close(noteFrequency(string, fret + capo, tuning), midiHz(TUNING_MIDI[tuning][string] + fret + capo), `${name} in ${tuning} with capo ${capo}, string ${string}`);
        }
      }
    }
  }
});
