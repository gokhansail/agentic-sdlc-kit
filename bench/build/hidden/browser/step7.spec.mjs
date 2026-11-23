// Hidden browser tests, step 7 (prompt step-7.txt). Test titles are the IDs of spec-map.json. The three
// clamp tests map to the decision of the step 5 prompt, which the step 7 prompt does not repeat.
//
// Readings accepted: the metronome is off or on at the start (the toggle is read, never assumed); a typed
// tempo outside 40 to 220 shows as the nearest end once the field is left, or, if the field keeps what was
// typed, the clicks run at the nearest end; the accent may be a boolean or a number; the first click may
// sit on any beat of a bar, as long as every 4th click is stronger than the three between; click times are
// held to 3% of a beat on average and 15% for each beat, because a page may stamp them from a timer.
import { test, expect } from "@playwright/test";
import { by, clicks, events, forget, louder, setMetronome, setTempo, startApp, waitForCount } from "./helpers.mjs";

const BPM = 200;

// The clicks of the metronome running at the tempo already set, in time order.
async function runClicks(page, count) {
  await forget(page);
  await setMetronome(page, true);
  await waitForCount(page, "click", count, 9000);
  const list = (await clicks(page)).sort((a, b) => a.time - b.time);
  await setMetronome(page, false);
  return list;
}

async function tempoIs(page, expected) {
  if (Number(await by(page, "tempo").inputValue()) === expected) return true;
  const list = await runClicks(page, 4);
  const gaps = list.slice(1).map((click, i) => click.time - list[i].time);
  const beat = 60 / expected;
  return gaps.length >= 3 && gaps.every((gap) => Math.abs(gap - beat) / beat < 0.15);
}

test("s7.browser.tempo-default", async ({ page }) => {
  await startApp(page);
  const facts = await by(page, "tempo").evaluate((element) => ({ tag: element.tagName, type: element.type, value: element.value }));
  expect([facts.tag, facts.type], "tempo must be a number field").toEqual(["INPUT", "number"]);
  expect(Number(facts.value), "default tempo").toBe(100);
});

for (const [id, typed, expected] of [
  ["s7.browser.clamp-high", [300, 221, 1000], 220],
  ["s7.browser.clamp-low", [10, 39, 1], 40],
]) {
  test(id, async ({ page }) => {
    await startApp(page);
    for (const value of typed) {
      await setTempo(page, value);
      expect(await tempoIs(page, expected), `${value} must be set to ${expected}, not refused`).toBe(true);
    }
  });
}

test("s7.browser.clamp-inside", async ({ page }) => {
  await startApp(page);
  for (const value of [40, 150, 220]) {
    await setTempo(page, value);
    await expect(by(page, "tempo"), `${value} stays`).toHaveValue(String(value));
  }
});

test("s7.browser.click-event", async ({ page }) => {
  await startApp(page);
  await setTempo(page, BPM);
  const list = await runClicks(page, 2);
  const [detail] = await events(page, "click");
  expect(Number.isFinite(Number(detail?.time)) && detail?.time !== null, `click time must be a number, got ${JSON.stringify(detail?.time)}`).toBe(true);
  expect(detail !== null && typeof detail === "object" && "accent" in detail, `click needs an accent, got ${JSON.stringify(detail)}`).toBe(true);
  expect(list.length).toBeGreaterThanOrEqual(2);
});

test("s7.browser.click-spacing", async ({ page }) => {
  await startApp(page);
  await setTempo(page, BPM);
  const list = await runClicks(page, 6);
  const gaps = list.slice(0, 6).slice(1).map((click, i) => click.time - list[i].time);
  const beat = 60 / BPM;
  const mean = (list[5].time - list[0].time) / 5;
  expect(Math.abs(mean - beat) / beat, `mean gap ${mean} s against ${beat} s`).toBeLessThan(0.03);
  for (const gap of gaps) expect(Math.abs(gap - beat) / beat, `gaps ${gaps.join(", ")} against ${beat} s`).toBeLessThan(0.15);
});

test("s7.browser.click-accent", async ({ page }) => {
  await startApp(page);
  await setTempo(page, BPM);
  const list = (await runClicks(page, 9)).slice(0, 9);
  const accents = list.map((click) => click.accent);
  const fits = [0, 1, 2, 3].some((offset) => {
    const strong = accents.map((_, i) => i).filter((i) => i >= offset && (i - offset) % 4 === 0);
    const weak = accents.map((_, i) => i).filter((i) => !strong.includes(i));
    return strong.every((i) => weak.every((j) => louder(accents[i], accents[j])));
  });
  expect(fits, `every 4th click must be louder than the others, got ${JSON.stringify(accents)}`).toBe(true);
});

test("s7.browser.metronome-off", async ({ page }) => {
  await startApp(page);
  await setTempo(page, BPM);
  await runClicks(page, 2);
  await page.waitForTimeout(300);
  const before = (await events(page, "click")).length;
  await page.waitForTimeout(1000);
  expect((await events(page, "click")).length, "no click after the toggle is off").toBe(before);
});
