// Hidden engine tests of the handoff task (prompt handoff.txt). Project root: the GUITAR_ROOT
// environment variable. Each test imports the engine itself, so a missing engine fails every test and
// never the file. Test names are the IDs of spec-map.json.
//
// Readings the tests accept: a beat count may be a number or a numeric string; the schedule has one entry
// per chord, at the time of its first beat, counted from startTime. The clamp test maps to the step 5
// decision, which the handoff prompt does not repeat. Chord letters are checked in the case the text uses.
import assert from "node:assert/strict";
import test from "node:test";
import { loadEngine } from "../engine/load.mjs";
import { CHORDS } from "../engine/helpers.mjs";

const SONG = [{ chord: "C", beats: 4 }, { chord: "G", beats: 4 }, { chord: "Am", beats: 2 }, { chord: "F", beats: 2 }];
const EPS = 1e-9;

test("handoff.engine.exports", async () => {
  const engine = await loadEngine();
  for (const name of ["parseSong", "songSchedule"]) assert.equal(typeof engine[name], "function", `${name} is not an exported function`);
});

test("handoff.engine.parse", async () => {
  const { parseSong } = await loadEngine();
  const parsed = parseSong("C:4 G:4 Am:2 F:2");
  assert.ok(Array.isArray(parsed), "parseSong must return an array");
  assert.deepEqual(parsed.map((item) => item.chord), ["C", "G", "Am", "F"]);
  assert.deepEqual(parsed.map((item) => Number(item.beats)), [4, 4, 2, 2]);
  const other = parseSong("Em:1 E:8");
  assert.deepEqual(other.map((item) => item.chord), ["Em", "E"]);
  assert.deepEqual(other.map((item) => Number(item.beats)), [1, 8]);
});

test("handoff.engine.parse-all-chords", async () => {
  const { parseSong } = await loadEngine();
  const names = Object.keys(CHORDS);
  const parsed = parseSong(names.map((name) => `${name}:2`).join(" "));
  assert.deepEqual(parsed.map((item) => item.chord), names);
});

test("handoff.engine.parse-unknown", async () => {
  const { parseSong } = await loadEngine();
  for (const text of ["Bm:4", "C:4 Dm:2", "Xyz:1 C:4", "H:2", "C:4 G:4 Cmaj7:2"]) {
    assert.throws(() => parseSong(text), `parseSong("${text}") must throw`);
  }
  assert.doesNotThrow(() => parseSong("C:4 G:4"), "known chords must not throw");
});

test("handoff.engine.schedule-times", async () => {
  const { songSchedule } = await loadEngine();
  for (const [bpm, expected] of [[120, [0, 2, 4, 5]], [60, [0, 4, 8, 10]], [100, [0, 2.4, 4.8, 6]]]) {
    const schedule = songSchedule(SONG, bpm, 0);
    assert.ok(Array.isArray(schedule), "songSchedule must return an array");
    assert.deepEqual(schedule.map((entry) => entry.chord), ["C", "G", "Am", "F"], `${bpm} BPM: chords`);
    assert.equal(schedule.length, 4, `${bpm} BPM: one entry per chord`);
    schedule.forEach((entry, i) => assert.ok(Math.abs(entry.time - expected[i]) < 1e-6, `${bpm} BPM: chord ${i} at ${entry.time} s, expected ${expected[i]}`));
  }
});

test("handoff.engine.schedule-start", async () => {
  const { songSchedule } = await loadEngine();
  const schedule = songSchedule(SONG, 120, 10);
  [10, 12, 14, 15].forEach((time, i) => assert.ok(Math.abs(schedule[i].time - time) < EPS, `chord ${i} at ${schedule[i].time} s, expected ${time}`));
  const single = songSchedule([{ chord: "Em", beats: 3 }], 90, 2.5);
  assert.equal(single.length, 1);
  assert.equal(single[0].chord, "Em");
  assert.ok(Math.abs(single[0].time - 2.5) < EPS);
});

test("handoff.engine.clamp", async () => {
  const { songSchedule } = await loadEngine();
  const high = songSchedule(SONG, 220, 1);
  for (const bpm of [221, 300, 1000]) assert.deepEqual(songSchedule(SONG, bpm, 1), high, `${bpm} BPM must run as 220`);
  const low = songSchedule(SONG, 40, 1);
  for (const bpm of [39, 10, 0]) assert.deepEqual(songSchedule(SONG, bpm, 1), low, `${bpm} BPM must run as 40`);
  assert.ok(Math.abs(low[1].time - low[0].time - 6) < EPS, "40 BPM: 4 beats take 6 s");
});
