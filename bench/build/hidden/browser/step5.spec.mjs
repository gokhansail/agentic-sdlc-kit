// Hidden browser tests, step 5 (prompt step-5.txt). Test titles are the IDs of spec-map.json.
//
// How long a string rings is a property of the sound, which the browser tests never measure (the engine
// tests measure the decay of renderPluck). Here the control is checked: its values, that a chosen value
// stays chosen, and that the app still plays one correct note at each setting. No default is assumed.
import { test, expect } from "@playwright/test";
import { MIDI, STRING_KEYS, by, choose, expectNotes, forget, hz, optionValues, press, startApp, waitForNotes } from "./helpers.mjs";

test("s5.browser.sustain-options", async ({ page }) => {
  await startApp(page);
  const values = await optionValues(page, "sustain");
  for (const sustain of ["short", "normal", "long"]) expect(values, `sustain has no option ${sustain}`).toContain(sustain);
});

test("s5.browser.sustain-plays", async ({ page }) => {
  await startApp(page);
  await press(page, "KeyZ");
  for (const sustain of ["short", "long", "normal"]) {
    await choose(page, "sustain", sustain);
    await expect(by(page, "sustain")).toHaveValue(sustain);
    await forget(page);
    await press(page, STRING_KEYS[3]);
    expectNotes(await waitForNotes(page, 1), [{ string: 3, fret: 0, hz: hz(MIDI.standard[3]) }]);
    await page.waitForTimeout(100);
  }
});
