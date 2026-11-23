// Hidden browser tests, step 4 (prompt step-4.txt). Test titles are the IDs of spec-map.json.
//
// Readings accepted: the capo tests use the F chord (133211), which has no open string, because the text
// does not say whether a capo moves an open string. With a capo the dot of a sounding string may show the
// fret of the shape or that fret plus the capo, and the fret in a guitar:note event is not compared; the
// frequency must be exactly the capo's semitones higher. A capo of 0 and standard tuning are the state of
// a page nobody touched, as in steps 1 to 3.
import { test, expect } from "@playwright/test";
import {
  CHORDS, CHORD_KEYS, MIDI, STRING_KEYS, by, choose, expectNotes, expectedNotes, forget, hz, optionValues, press, startApp, waitForNotes,
} from "./helpers.mjs";

const OPEN = [0, 0, 0, 0, 0, 0];

async function optionsOf(page, id) {
  return by(page, id).evaluate((element) => [...element.options].flatMap((option) => [option.value, option.textContent.trim()]));
}

async function strumChord(page, chord, expected, fret = false) {
  await press(page, CHORD_KEYS[chord]);
  await forget(page);
  await press(page, "Space");
  expectNotes(await waitForNotes(page, expected.length), expected, { fret });
}

test("s4.browser.capo-select", async ({ page }) => {
  await startApp(page);
  const options = await optionsOf(page, "capo");
  for (let fret = 0; fret <= 7; fret += 1) expect(options, `capo has no option ${fret}`).toContain(String(fret));
});

test("s4.browser.capo-moves-chord", async ({ page }) => {
  await startApp(page);
  for (const capo of [2, 5, 7]) {
    await choose(page, "capo", capo);
    await strumChord(page, "F", expectedNotes(CHORDS.F, { capo }));
    for (let string = 1; string <= 6; string += 1) {
      const base = CHORDS.F[6 - string];
      await expect(by(page, `dot-${string}`), `dot-${string} with capo ${capo}`).toHaveAttribute("data-fret", new RegExp(`^(${base}|${base + capo})$`));
    }
    await page.waitForTimeout(100);
  }
});

test("s4.browser.capo-single-string", async ({ page }) => {
  await startApp(page);
  await choose(page, "capo", 3);
  await press(page, CHORD_KEYS.F);
  for (const string of [1, 4]) {
    await forget(page);
    await press(page, STRING_KEYS[string]);
    expectNotes(await waitForNotes(page, 1), [{ string, fret: 0, hz: hz(MIDI.standard[string] + CHORDS.F[6 - string] + 3) }], { fret: false });
  }
});

test("s4.browser.tuning-select", async ({ page }) => {
  await startApp(page);
  const values = await optionValues(page, "tuning");
  for (const tuning of ["standard", "dropD", "openG"]) expect(values, `tuning has no option ${tuning}`).toContain(tuning);
});

test("s4.browser.tuning-open-strings", async ({ page }) => {
  await startApp(page);
  for (const tuning of ["dropD", "openG", "standard"]) {
    await choose(page, "tuning", tuning);
    await press(page, "KeyZ");
    await forget(page);
    await press(page, "Space");
    expectNotes(await waitForNotes(page, 6), expectedNotes(OPEN, { tuning }));
    await page.waitForTimeout(100);
  }
});

test("s4.browser.capo-and-tuning", async ({ page }) => {
  await startApp(page);
  for (const [tuning, capo] of [["dropD", 2], ["openG", 5]]) {
    await choose(page, "tuning", tuning);
    await choose(page, "capo", capo);
    await strumChord(page, "F", expectedNotes(CHORDS.F, { tuning, capo }));
    await page.waitForTimeout(100);
  }
});
