// Hidden browser tests, step 2 (prompt step-2.txt). Test titles are the IDs of spec-map.json.
//
// Readings accepted: "spread over a time I set" may mean the whole strum lasts that time or each gap lasts
// that time, so the span of a strum is only held between 0.4 times the set time and (number of notes) times
// the set time (plus 30 ms for timer jitter); a longer set time must give a longer strum. The order of the
// notes is read from their event times (the order of arrival breaks a tie). A lower bound on the span of a strum
// ("it is spread") takes the larger of the span of the event times and the span of the arrivals, so that a page
// that stamps its events with the scheduled time and one that fires them at the start both pass; an upper bound
// takes the span of the event times only, because the arrivals also stretch when the machine is loaded, and so
// does the comparison between strums of different set times (the arrivals only stand in when all stamps of a strum
// coincide). A stop event is asked for
// when a string is plucked again; whether another action also fires one is not judged.
import { test, expect } from "@playwright/test";
import {
  CHORDS, CHORD_KEYS, STRING_KEYS, by, forget, inTimeOrder, notes, press, setSlider, spanOf, spreadOf, startApp, stops, timeSpan, waitForCount, waitForNotes,
} from "./helpers.mjs";

const JITTER = 0.03;

// One strum of a chord with the current spread: the notes of strings 1 to 6 by time.
async function strumOnce(page, chord, code = "Space") {
  await press(page, CHORD_KEYS[chord]);
  await forget(page);
  const count = CHORDS[chord].filter((fret) => fret >= 0).length;
  await press(page, code);
  const played = (await waitForNotes(page, count)).filter((note) => note.string <= 6);
  expect(played, `${chord}: one note per sounding string`).toHaveLength(count);
  return played;
}

test("s2.browser.slider-default", async ({ page }) => {
  await startApp(page);
  const facts = await by(page, "strum-spread").evaluate((element) =>
    element.tagName === "INPUT"
      ? { kind: element.type, value: element.value, min: element.min, max: element.max }
      : { kind: element.getAttribute("role"), value: element.getAttribute("aria-valuenow"), min: element.getAttribute("aria-valuemin"), max: element.getAttribute("aria-valuemax") },
  );
  expect(["range", "slider"], "strum-spread must be a slider").toContain(facts.kind);
  expect([Number(facts.min), Number(facts.max), Number(facts.value)], "min, max and default of the slider").toEqual([0, 100, 30]);
});

test("s2.browser.spread-default", async ({ page }) => {
  await startApp(page);
  const played = await strumOnce(page, "C");
  const span = spanOf(played);
  expect(span, "a default strum is spread over time").toBeGreaterThanOrEqual(0.4 * 0.03 - 0.001);
  expect(timeSpan(played), "a default strum is not longer than the set time per note").toBeLessThanOrEqual(played.length * 0.03 + JITTER);
  const times = inTimeOrder(played).map((note) => note.time);
  for (let i = 1; i < times.length; i += 1) expect(times[i] - times[i - 1], `notes ${i - 1} and ${i} start one after another`).toBeGreaterThan(1e-6);
});

test("s2.browser.spread-set", async ({ page }) => {
  await startApp(page);
  const spans = [];
  for (const spread of [20, 50, 100]) {
    await setSlider(page, "strum-spread", spread);
    const played = await strumOnce(page, "C");
    const span = spanOf(played);
    expect(span, `${spread} ms: strum too short`).toBeGreaterThanOrEqual((0.4 * spread) / 1000 - 0.001);
    expect(timeSpan(played), `${spread} ms: strum too long`).toBeLessThanOrEqual((played.length * spread) / 1000 + JITTER);
    spans.push(spreadOf(played));
    await page.waitForTimeout(150);
  }
  expect(spans[0], `spans ${spans.join(", ")}`).toBeLessThan(spans[1]);
  expect(spans[1], `spans ${spans.join(", ")}`).toBeLessThan(spans[2]);
  expect(spans[2], "100 ms must spread at least twice as far as 20 ms").toBeGreaterThanOrEqual(2 * spans[0]);
});

test("s2.browser.spread-zero", async ({ page }) => {
  await startApp(page);
  await setSlider(page, "strum-spread", 0);
  const played = await strumOnce(page, "C");
  expect(timeSpan(played), "all notes of a 0 ms strum start together").toBeLessThanOrEqual(0.02);
});

for (const [id, direction, code] of [["s2.browser.down-order", "down", "Space"], ["s2.browser.up-order", "up", "KeyM"]]) {
  test(id, async ({ page }) => {
    await startApp(page);
    for (const chord of ["C", "G", "F", "Em"]) {
      const sounding = [6, 5, 4, 3, 2, 1].filter((string) => CHORDS[chord][6 - string] >= 0);
      const wanted = direction === "down" ? sounding : [...sounding].reverse();
      const played = await strumOnce(page, chord, code);
      expect(inTimeOrder(played).map((note) => note.string), `${chord} strummed ${direction}`).toEqual(wanted);
      await page.waitForTimeout(100);
    }
  });
}

test("s2.browser.muted-skipped", async ({ page }) => {
  await startApp(page);
  for (const code of ["Space", "KeyM"]) {
    const played = await strumOnce(page, "D", code);
    expect(played.map((note) => note.string).sort(), `D with ${code}`).toEqual([1, 2, 3, 4]);
    await page.waitForTimeout(100);
  }
});

test("s2.browser.repluck-stop", async ({ page }) => {
  await startApp(page);
  await press(page, "KeyZ");
  await forget(page);
  await press(page, STRING_KEYS[1]);
  await waitForCount(page, "note", 1);
  await press(page, STRING_KEYS[2]);
  await waitForCount(page, "note", 2);
  await page.waitForTimeout(400);
  expect(await stops(page), "plucking another string stops nothing").toEqual([]);
  await press(page, STRING_KEYS[1]);
  await waitForCount(page, "stop", 1);
  await page.waitForTimeout(300);
  const stopped = await stops(page);
  expect(stopped.length, "plucking string 1 again stops its old note").toBeGreaterThanOrEqual(1);
  expect(stopped.every((detail) => detail.string === 1), `only string 1 stops, got ${JSON.stringify(stopped)}`).toBe(true);
  expect((await notes(page)).filter((note) => note.string === 1)).toHaveLength(2);
});

test("s2.browser.repluck-strum", async ({ page }) => {
  await startApp(page);
  await strumOnce(page, "C");
  await page.waitForTimeout(300);
  await forget(page);
  await press(page, "Space");
  await waitForCount(page, "stop", 5);
  await page.waitForTimeout(300);
  expect([...new Set((await stops(page)).map((detail) => detail.string))].sort(), "a second strum stops the old note of each string").toEqual([1, 2, 3, 4, 5]);
});
