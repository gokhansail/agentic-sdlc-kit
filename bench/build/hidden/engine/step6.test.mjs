// Hidden engine tests, step 6 (prompt step-6.txt). Project root: the GUITAR_ROOT environment variable.
// Each test imports the engine itself, so a missing engine fails every test and never the file.
// Test names are the IDs of spec-map.json.
//
// Only what the text says is checked: string 7 is B1 (A1 in drop D), chords leave string 7 muted and keep
// their six frets, and the Y key plucks string 7. Open G on string 7 and strumSchedule on 7 frets are not
// in the text and are not tested. chordShape with strings 6 or left out gives the 6-fret shape of SPEC.md.
import assert from "node:assert/strict";
import test from "node:test";
import { loadEngine } from "./load.mjs";
import { CHORDS, close, midiHz } from "./helpers.mjs";

const B1 = 35;
const A1 = 33;

test("s6.engine.string7-standard", async () => {
  const { noteFrequency } = await loadEngine();
  close(noteFrequency(7, 0), midiHz(B1), "open string 7");
  close(noteFrequency(7, 0), 61.73541265701551, "open string 7 is B1");
  for (const fret of [0, 1, 5, 12, 19]) {
    close(noteFrequency(7, fret), midiHz(B1 + fret), `string 7 fret ${fret}`);
    close(noteFrequency(7, fret, "standard"), midiHz(B1 + fret), `string 7 fret ${fret}, standard`);
  }
});

test("s6.engine.string7-dropD", async () => {
  const { noteFrequency } = await loadEngine();
  close(noteFrequency(7, 0, "dropD"), 55, "open string 7 in drop D is A1");
  for (const fret of [0, 1, 5, 12, 19]) close(noteFrequency(7, fret, "dropD"), midiHz(A1 + fret), `string 7 fret ${fret} in drop D`);
});

test("s6.engine.chord-7-muted", async () => {
  const { chordShape } = await loadEngine();
  for (const name of Object.keys(CHORDS)) {
    const shape = chordShape(name, 7);
    assert.ok(Array.isArray(shape), `chordShape("${name}", 7) must be an array`);
    assert.equal(shape.length, 7, `chordShape("${name}", 7) must have 7 frets`);
    assert.equal(shape[0], -1, `chordShape("${name}", 7) must leave string 7 muted`);
  }
});

test("s6.engine.chord-7-frets", async () => {
  const { chordShape } = await loadEngine();
  for (const [name, frets] of Object.entries(CHORDS)) {
    assert.deepEqual(Array.from(chordShape(name, 7)).slice(1), frets, `chordShape("${name}", 7) after string 7`);
  }
});

test("s6.engine.chord-6", async () => {
  const { chordShape } = await loadEngine();
  for (const [name, frets] of Object.entries(CHORDS)) {
    assert.deepEqual(Array.from(chordShape(name)), frets, `chordShape("${name}")`);
    assert.deepEqual(Array.from(chordShape(name, 6)), frets, `chordShape("${name}", 6)`);
  }
});

test("s6.engine.key-y", async () => {
  const { keyToAction } = await loadEngine();
  const action = keyToAction("KeyY");
  assert.ok(action !== null && typeof action === "object", `keyToAction("KeyY") gave ${JSON.stringify(action)}`);
  assert.equal(action.type, "pluck");
  assert.equal(action.string, 7);
});
