// Hidden browser tests, step 1 (SPEC.md, prompt step-1.txt). Run by run_browser.py with Playwright; the
// project is served at the baseURL. Test titles are the IDs of spec-map.json.
//
// A test uses only the data-testid names, key codes and guitar:* events of SPEC.md. Readings accepted:
// the tests judge strings 1 to 6, so a later 7-string default does not matter; the fret in an event is
// compared only where no capo is set; the order of the notes of a strum is left to step 2.
import { test, expect } from "@playwright/test";
import {
  CHORDS, CHORD_KEYS, MIDI, STRING_KEYS, audioRunning, blur, by, events, expectDots, expectNoChord, expectNone, expectNotes, expectedNotes,
  expectRendered, forget, hz, notes, openApp, press, startApp, waitForCount, waitForNotes,
} from "./helpers.mjs";

const OPEN = [0, 0, 0, 0, 0, 0];

test("s1.browser.start-audio", async ({ page }) => {
  await openApp(page);
  const button = by(page, "start-audio");
  await expect(button).toBeVisible();
  const isButton = await button.evaluate((element) => element.tagName === "BUTTON" || element.getAttribute("role") === "button");
  expect(isButton, "start-audio must be a button").toBe(true);
  await button.click();
  await expect.poll(() => audioRunning(page), { message: "no running audio context after the click", timeout: 8000 }).toBe(true);
  await blur(page);
  await press(page, CHORD_KEYS.C);
  await press(page, "Space");
  await waitForCount(page, "note", 1);
});

test("s1.browser.fretboard", async ({ page }) => {
  await startApp(page);
  await expectRendered(page, "fretboard");
  for (let string = 1; string <= 6; string += 1) await expectRendered(page, `string-${string}`);
});

test("s1.browser.chord-name-empty", async ({ page }) => {
  await startApp(page);
  await expectNoChord(page);
});

// Every title is written out once, so that a static read of this file finds all the IDs.
const CHORD_TESTS = [
  ["s1.browser.chord-C", "C"], ["s1.browser.chord-G", "G"], ["s1.browser.chord-D", "D"], ["s1.browser.chord-Em", "Em"],
  ["s1.browser.chord-Am", "Am"], ["s1.browser.chord-F", "F"], ["s1.browser.chord-A", "A"], ["s1.browser.chord-E", "E"],
];

for (const [id, name] of CHORD_TESTS) {
  const shape = CHORDS[name];
  test(id, async ({ page }) => {
    await startApp(page);
    await press(page, CHORD_KEYS[name]);
    await expect(by(page, "chord-name")).toHaveText(name);
    await expectDots(page, shape);
    await forget(page);
    await press(page, "Space");
    const expected = expectedNotes(shape);
    expectNotes(await waitForNotes(page, expected.length), expected);
  });
}

test("s1.browser.chord-stays", async ({ page }) => {
  await startApp(page);
  await press(page, CHORD_KEYS.C);
  await press(page, "Space");
  await waitForCount(page, "note", 1);
  await press(page, STRING_KEYS[1]);
  await press(page, "KeyM");
  await expect(by(page, "chord-name")).toHaveText("C");
  await expectDots(page, CHORDS.C);
  await press(page, CHORD_KEYS.G);
  await expect(by(page, "chord-name")).toHaveText("G");
  await expectDots(page, CHORDS.G);
  await press(page, "Space");
  await expect(by(page, "chord-name")).toHaveText("G");
});

test("s1.browser.keyz-open", async ({ page }) => {
  await startApp(page);
  await press(page, CHORD_KEYS.Em);
  await expect(by(page, "chord-name")).toHaveText("Em");
  await press(page, "KeyZ");
  await expectNoChord(page);
  await expectDots(page, OPEN);
  await forget(page);
  await press(page, "Space");
  const expected = expectedNotes(OPEN);
  expectNotes(await waitForNotes(page, expected.length), expected);
});

test("s1.browser.strum-up", async ({ page }) => {
  await startApp(page);
  await press(page, CHORD_KEYS.G);
  await forget(page);
  await press(page, "KeyM");
  const expected = expectedNotes(CHORDS.G);
  expectNotes(await waitForNotes(page, expected.length), expected);
});

const STRING_TESTS = [
  ["s1.browser.string-6", 6], ["s1.browser.string-5", 5], ["s1.browser.string-4", 4],
  ["s1.browser.string-3", 3], ["s1.browser.string-2", 2], ["s1.browser.string-1", 1],
];

for (const [id, string] of STRING_TESTS) {
  test(id, async ({ page }) => {
    await startApp(page);
    await press(page, "KeyZ");
    await forget(page);
    await press(page, STRING_KEYS[string]);
    const played = await waitForNotes(page, 1);
    expect(played, "one key press plays one note").toHaveLength(1);
    expectNotes(played, [{ string, fret: 0, hz: hz(MIDI.standard[string]) }]);
  });
}

test("s1.browser.string-chord-fret", async ({ page }) => {
  await startApp(page);
  for (const [chord, picks] of [["C", [5, 2, 1]], ["G", [6, 3, 1]]]) {
    await press(page, CHORD_KEYS[chord]);
    for (const string of picks) {
      await forget(page);
      await press(page, STRING_KEYS[string]);
      const fret = CHORDS[chord][6 - string];
      const played = await waitForNotes(page, 1);
      expectNotes(played, [{ string, fret, hz: hz(MIDI.standard[string] + fret) }]);
    }
  }
});

test("s1.browser.string-muted", async ({ page }) => {
  await startApp(page);
  await press(page, CHORD_KEYS.D);
  await forget(page);
  await press(page, STRING_KEYS[6]);
  await press(page, STRING_KEYS[5]);
  await expectNone(page, "note");
  await press(page, STRING_KEYS[4]);
  const played = await waitForNotes(page, 1);
  expectNotes(played, [{ string: 4, fret: 0, hz: hz(MIDI.standard[4]) }]);
});

test("s1.browser.mute-event", async ({ page }) => {
  await startApp(page);
  await press(page, CHORD_KEYS.Am);
  await press(page, "Space");
  await waitForCount(page, "note", 1);
  await forget(page);
  await press(page, "Period");
  await waitForCount(page, "mute", 1);
  await page.waitForTimeout(300);
  expect(await events(page, "note"), "mute must not start a note").toEqual([]);
});

test("s1.browser.note-detail", async ({ page }) => {
  await startApp(page);
  await press(page, "KeyZ");
  await forget(page);
  await press(page, STRING_KEYS[2]);
  await waitForCount(page, "note", 1);
  const [detail] = await events(page, "note");
  for (const key of ["string", "fret", "frequency", "time"]) {
    expect(Number.isFinite(Number(detail?.[key])) && detail?.[key] !== null, `detail.${key} must be a number, got ${JSON.stringify(detail?.[key])}`).toBe(true);
  }
  const [note] = await notes(page);
  expect(note.time, "time is an AudioContext time in seconds").toBeGreaterThanOrEqual(0);
  expect(note.string).toBe(2);
});
