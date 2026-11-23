// Hidden browser tests of the handoff task (prompt handoff.txt). Test titles are the IDs of spec-map.json.
// The clamp test maps to the step 5 decision, which the handoff prompt does not repeat.
//
// Readings accepted: the strums of a song are told apart by a pause of more than half a beat, which no
// strum spread up to 100 ms reaches at 220 BPM; each chord is held to the beat it starts on through the
// time between the first notes of two chords, not through the time of the first note itself, so a page
// that starts the song a little after the click or centres a strum on the beat passes; the chord name is
// read from chord-name, the one name the texts give for it; what the page shows after the song ends is
// not judged. The tempo is the tempo field, set the way step 7 does.
import { test, expect } from "@playwright/test";
import { CHORDS, by, expectNotes, expectedNotes, forget, inTimeOrder, notes, sampleText, setTempo, startApp, waitForCount } from "./helpers.mjs";

const sounding = (shape) => shape.filter((fret) => fret >= 0).length;

// Types a song, presses play and returns the notes of strings 1 to 6, as the strums they form.
async function playSong(page, text, chords, bpm) {
  await by(page, "song-input").fill(text);
  await forget(page);
  await by(page, "song-play").click();
  const wanted = chords.reduce((sum, name) => sum + sounding(CHORDS[name]), 0);
  await waitForCount(page, "note", wanted, 12000);
  await page.waitForTimeout(300);
  const beat = 60 / bpm;
  const groups = [];
  for (const note of inTimeOrder((await notes(page)).filter((item) => item.string <= 6))) {
    const last = groups[groups.length - 1];
    if (last && note.time - last[last.length - 1].time < 0.5 * beat) last.push(note);
    else groups.push([note]);
  }
  return groups;
}

function expectStrums(groups, chords, beats, bpm, tolerance) {
  expect(groups, `one strum per chord of ${chords.join(" ")}`).toHaveLength(chords.length);
  const beat = 60 / bpm;
  let at = 0;
  chords.forEach((name, i) => {
    const strum = groups[i];
    const down = [6, 5, 4, 3, 2, 1].filter((string) => CHORDS[name][6 - string] >= 0);
    expect(inTimeOrder(strum).map((note) => note.string), `${name} is strummed down`).toEqual(down);
    expectNotes(strum, expectedNotes(CHORDS[name]));
    const offset = strum[0].time - groups[0][0].time;
    expect(Math.abs(offset - at * beat), `${name} starts ${offset} s after the first chord, expected ${at * beat} s`).toBeLessThanOrEqual(tolerance);
    at += beats[i];
  });
}

test("handoff.browser.song-controls", async ({ page }) => {
  await startApp(page);
  const input = await by(page, "song-input").evaluate((element) => ({ tag: element.tagName, type: element.type }));
  expect(input.tag === "TEXTAREA" || (input.tag === "INPUT" && (input.type === "text" || input.type === "search")), "song-input must be a text field").toBe(true);
  const play = by(page, "song-play");
  await expect(play).toBeVisible();
  expect(await play.evaluate((element) => element.tagName === "BUTTON" || element.getAttribute("role") === "button"), "song-play must be a button").toBe(true);
});

test("handoff.browser.song-strums", async ({ page }) => {
  await startApp(page);
  await setTempo(page, 200);
  const groups = await playSong(page, "C:4 G:4 Am:2 F:2", ["C", "G", "Am", "F"], 200);
  expectStrums(groups, ["C", "G", "Am", "F"], [4, 4, 2, 2], 200, 0.05);
});

test("handoff.browser.song-chord-name", async ({ page }) => {
  await startApp(page);
  await setTempo(page, 200);
  await by(page, "song-input").fill("C:2 G:2");
  const sampling = sampleText(page, "chord-name", 2600);
  await by(page, "song-play").click();
  const names = (await sampling).filter((text, i, all) => text !== "" && text !== all[i - 1]);
  expect(names[0], `chord names seen: ${names.join(", ")}`).toBe("C");
  expect(names.indexOf("G"), `chord names seen: ${names.join(", ")}`).toBeGreaterThan(0);
});

test("handoff.browser.song-tempo-default", async ({ page }) => {
  await startApp(page);
  const groups = await playSong(page, "G:2 D:1", ["G", "D"], 100);
  expectStrums(groups, ["G", "D"], [2, 1], 100, 0.06);
});

test("handoff.browser.clamp", async ({ page }) => {
  await startApp(page);
  for (const [typed, bpm, tolerance] of [[300, 220, 0.03], [10, 40, 0.1]]) {
    await setTempo(page, typed);
    const groups = await playSong(page, "C:1 G:1", ["C", "G"], bpm);
    expectStrums(groups, ["C", "G"], [1, 1], bpm, tolerance);
    await page.waitForTimeout(300);
  }
});
