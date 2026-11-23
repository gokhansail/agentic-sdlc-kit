// Hidden browser tests, step 3 (prompt step-3.txt). Test titles are the IDs of spec-map.json. The two
// spectrum tests are retired at step 6, where the view is dropped.
//
// Readings accepted: the canvas counts as drawn when its pixels are not all one colour (or, for a canvas
// without a 2d context, when its image differs from a blank canvas of the same size); the readout is a note
// name with its octave and the cents as a whole number, with or without a sign or a unit, because the text
// gives only the example "E4 +0". The readout is checked after single plucks only, because "the last note"
// of a strum may be read two ways. The size of the cents is not judged.
import { test, expect } from "@playwright/test";
import { READOUT, STRING_KEYS, by, press, readoutName, startApp } from "./helpers.mjs";

const canvasState = (page) =>
  page.evaluate(() => {
    const canvas = document.querySelector('[data-testid="spectrum"]');
    if (!canvas || canvas.tagName !== "CANVAS" || canvas.width === 0 || canvas.height === 0) return { present: false, drawn: false, image: "" };
    const blank = document.createElement("canvas");
    blank.width = canvas.width;
    blank.height = canvas.height;
    const context = canvas.getContext("2d");
    let drawn;
    if (context) {
      const data = context.getImageData(0, 0, canvas.width, canvas.height).data;
      drawn = false;
      for (let i = 4; i < data.length; i += 4) {
        if (data[i] !== data[0] || data[i + 1] !== data[1] || data[i + 2] !== data[2] || data[i + 3] !== data[3]) {
          drawn = true;
          break;
        }
      }
    } else {
      drawn = canvas.toDataURL() !== blank.toDataURL();
    }
    return { present: true, drawn, image: canvas.toDataURL() };
  });

test("s3.browser.spectrum-canvas", async ({ page }) => {
  await startApp(page);
  await expect(by(page, "spectrum")).toBeVisible();
  await press(page, STRING_KEYS[1]);
  await expect.poll(async () => (await canvasState(page)).present, { message: "spectrum must be a canvas with a size" }).toBe(true);
  await expect.poll(async () => (await canvasState(page)).drawn, { message: "the canvas shows nothing after a note" }).toBe(true);
});

test("s3.browser.spectrum-changes", async ({ page }) => {
  await startApp(page);
  await press(page, STRING_KEYS[6]);
  await expect.poll(async () => (await canvasState(page)).drawn, { message: "the canvas shows nothing after a note" }).toBe(true);
  const low = (await canvasState(page)).image;
  await press(page, STRING_KEYS[1]);
  await expect.poll(async () => (await canvasState(page)).image, { message: "the spectrum of a high note must differ from that of a low note" }).not.toBe(low);
});

test("s3.browser.readout-pluck", async ({ page }) => {
  await startApp(page);
  await press(page, "KeyZ");
  for (const [string, name] of [[1, "E4"], [5, "A2"], [2, "B3"], [6, "E2"]]) {
    await press(page, STRING_KEYS[string]);
    await expect.poll(() => readoutName(page), { message: `readout after plucking string ${string}` }).toBe(name);
  }
});

test("s3.browser.readout-format", async ({ page }) => {
  await startApp(page);
  await press(page, STRING_KEYS[1]);
  await expect(by(page, "pitch-readout")).toHaveText(READOUT);
  await press(page, "Space");
  await expect(by(page, "pitch-readout")).toHaveText(READOUT);
});
