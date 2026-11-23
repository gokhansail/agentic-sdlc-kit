// Hidden browser tests, step 6 (prompt step-6.txt). Test titles are the IDs of spec-map.json.
//
// Readings accepted: the spectrum view counts as dropped when its element is absent or not drawn; the
// text does not say what string-7 and dot-7 do in 6-string mode (hidden or absent), so they are looked at
// only after the strings select is set to 7; the default string count is not assumed; Y in 6-string mode is
// not tested. The 7-string tests use standard and drop D tuning only, because the text gives string 7 no
// open G note.
import { test, expect } from "@playwright/test";
import {
  CHORDS, CHORD_KEYS, MIDI, STRING_KEYS, by, choose, expectDots, expectNone, expectNotes, expectRendered, expectedNotes, forget, hz, isRendered, notes,
  optionValues, press, readoutName, startApp, waitForNotes,
} from "./helpers.mjs";

async function sevenStrings(page) {
  await choose(page, "strings", 7);
  await expectRendered(page, "string-7");
}

test("s6.browser.no-spectrum", async ({ page }) => {
  await startApp(page);
  await press(page, STRING_KEYS[1]);
  await page.waitForTimeout(500);
  expect(await isRendered(page, "spectrum"), "the spectrum view must be gone").toBe(false);
});

test("s6.browser.readout-kept", async ({ page }) => {
  await startApp(page);
  await press(page, "KeyZ");
  await press(page, STRING_KEYS[1]);
  await expect.poll(() => readoutName(page), { message: "pitch readout after a pluck" }).toBe("E4");
});

test("s6.browser.strings-select", async ({ page }) => {
  await startApp(page);
  const values = await optionValues(page, "strings");
  for (const count of ["6", "7"]) expect(values, `strings has no option ${count}`).toContain(count);
});

test("s6.browser.string7-page", async ({ page }) => {
  await startApp(page);
  await sevenStrings(page);
  await expectRendered(page, "dot-7");
  for (let string = 1; string <= 6; string += 1) await expectRendered(page, `string-${string}`);
});

test("s6.browser.key-y", async ({ page }) => {
  await startApp(page);
  await sevenStrings(page);
  await press(page, "KeyZ");
  await forget(page);
  await press(page, "KeyY");
  const played = await waitForNotes(page, 1);
  expect(played, "Y plays one note").toHaveLength(1);
  expect(played[0].string).toBe(7);
  expect(played[0].frequency, "open string 7 is B1").toBeCloseTo(hz(35), 1);
});

test("s6.browser.chord-7-muted", async ({ page }) => {
  await startApp(page);
  await sevenStrings(page);
  for (const chord of ["C", "Em", "G"]) {
    await press(page, CHORD_KEYS[chord]);
    await expect(by(page, "dot-7"), `dot-7 under ${chord}`).toHaveAttribute("data-fret", "x");
    await expectDots(page, CHORDS[chord]);
    await forget(page);
    await press(page, "Space");
    const expected = expectedNotes(CHORDS[chord]);
    const played = await waitForNotes(page, expected.length);
    expectNotes(played, expected);
    expect(played.filter((note) => note.string === 7), `${chord} must leave string 7 muted`).toEqual([]);
    await forget(page);
    await press(page, "KeyY");
    await expectNone(page, "note");
  }
});

test("s6.browser.dropD-string7", async ({ page }) => {
  await startApp(page);
  await sevenStrings(page);
  await choose(page, "tuning", "dropD");
  await press(page, "KeyZ");
  await forget(page);
  await press(page, "KeyY");
  const low = await waitForNotes(page, 1);
  expect(low[0].string).toBe(7);
  expect(low[0].frequency, "string 7 in drop D is A1").toBeCloseTo(hz(33), 1);
  await forget(page);
  await press(page, STRING_KEYS[6]);
  const six = await waitForNotes(page, 1);
  expect(six[0].frequency, "string 6 in drop D is D2").toBeCloseTo(hz(MIDI.dropD[6]), 1);
  expect((await notes(page)).filter((note) => note.string === 7)).toEqual([]);
});
