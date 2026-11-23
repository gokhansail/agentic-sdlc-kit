// Shared helpers of the hidden browser tests. A test uses only what the frozen texts give: the data-testid
// names of the page, KeyboardEvent.code key presses and the guitar:* document events. Audio output is never
// measured. The project is served by the runner (run_browser.py) and reached through the baseURL.
import { expect } from "@playwright/test";

// The key the arms were told to send in step 8; the runner passes it in GUITAR_FAKE_KEY.
export const FAKE_KEY = process.env.GUITAR_FAKE_KEY || "{FAKE_KEY}";

// MIDI note of each open string by tuning, indexed by string number (1 is the high E).
export const MIDI = {
  standard: [null, 64, 59, 55, 50, 45, 40, 35],
  dropD: [null, 64, 59, 55, 50, 45, 38, 33],
  openG: [null, 62, 59, 55, 50, 43, 38],
};
export const hz = (midi) => 440 * 2 ** ((midi - 69) / 12);

// Chord shapes of SPEC.md: 6 frets from string 6 to string 1, -1 for a muted string.
export const CHORDS = {
  C: [-1, 3, 2, 0, 1, 0],
  G: [3, 2, 0, 0, 0, 3],
  D: [-1, -1, 0, 2, 3, 2],
  Em: [0, 2, 2, 0, 0, 0],
  Am: [-1, 0, 2, 2, 1, 0],
  F: [1, 3, 3, 2, 1, 1],
  A: [-1, 0, 2, 2, 2, 0],
  E: [0, 2, 2, 1, 0, 0],
};
export const CHORD_KEYS = { C: "KeyQ", G: "KeyW", D: "KeyE", Em: "KeyR", Am: "KeyA", F: "KeyS", A: "KeyD", E: "KeyF" };
export const STRING_KEYS = { 6: "KeyH", 5: "KeyJ", 4: "KeyK", 3: "KeyL", 2: "Semicolon", 1: "Quote" };

export const by = (page, id) => page.getByTestId(id);

// Records the guitar:* events and the audio contexts the page creates. Runs before the page's own scripts.
function observe() {
  const log = { events: [], contexts: [] };
  window.__guitar = log;
  for (const type of ["guitar:note", "guitar:stop", "guitar:mute", "guitar:click"]) {
    document.addEventListener(
      type,
      (event) => {
        let detail = null;
        try {
          detail = event.detail === undefined ? null : JSON.parse(JSON.stringify(event.detail));
        } catch {
          detail = null;
        }
        log.events.push({ type: type.slice("guitar:".length), detail, at: performance.now() / 1000 });
      },
      true,
    );
  }
  const Native = window.AudioContext || window.webkitAudioContext;
  if (Native) {
    class Tracked extends Native {
      constructor(...args) {
        super(...args);
        log.contexts.push(this);
      }
    }
    window.AudioContext = Tracked;
  }
}

export const blur = (page) => page.evaluate(() => document.activeElement && document.activeElement.blur && document.activeElement.blur());

export async function openApp(page) {
  await page.addInitScript(observe);
  await page.goto("/");
}

// Opens the page and clicks start-audio, as a user would. The wait for a running audio context only makes
// the first key press land on a started clock; it never fails a test. Focus goes back to the page body so
// that the keys reach the guitar and not a button or a control that was just used.
export async function startApp(page) {
  await openApp(page);
  // A page without the button fails here after 10 s; a page with it gets the full action timeout to click it.
  await by(page, "start-audio").waitFor({ state: "attached", timeout: 10000 });
  await by(page, "start-audio").click();
  await page.waitForFunction(() => window.__guitar.contexts.some((context) => context.state === "running"), null, { timeout: 5000 }).catch(() => {});
  await blur(page);
}

export const audioRunning = (page) => page.evaluate(() => window.__guitar.contexts.some((context) => context.state === "running"));

export const press = (page, code) => page.keyboard.press(code);
export const forget = (page) => page.evaluate(() => { window.__guitar.events.length = 0; });

const logged = (page, type) =>
  page.evaluate((wanted) => window.__guitar.events.filter((event) => event.type === wanted).map((event) => ({ detail: event.detail, at: event.at })), type);

export const events = async (page, type) => (await logged(page, type)).map((entry) => entry.detail);

// A note or click detail with its numbers read as numbers, so a numeric string is not a failure of its own.
// `at` is the page time in seconds at which the event arrived.
const numbers = (detail, keys) => Object.fromEntries(Object.entries(detail ?? {}).map(([key, value]) => [key, keys.includes(key) ? Number(value) : value]));
export const notes = async (page) => (await logged(page, "note")).map(({ detail, at }) => ({ ...numbers(detail, ["string", "fret", "frequency", "time"]), at }));
export const clicks = async (page) => (await logged(page, "click")).map(({ detail, at }) => ({ ...numbers(detail, ["time"]), at }));
export const stops = async (page) => (await logged(page, "stop")).map(({ detail }) => numbers(detail, ["string"]));

export async function waitForCount(page, type, count, timeout = 8000) {
  await page.waitForFunction(({ wanted, n }) => window.__guitar.events.filter((event) => event.type === wanted).length >= n, { wanted: type, n: count }, { timeout });
}

// The notes of one action: waits for `count` note events, then a moment more so that extra ones show.
export async function waitForNotes(page, count) {
  await waitForCount(page, "note", count);
  await page.waitForTimeout(200);
  return notes(page);
}

export async function expectNone(page, type, ms = 500) {
  await page.waitForTimeout(ms);
  expect(await events(page, type), `no guitar:${type} event was expected`).toEqual([]);
}

export const cents = (a, b) => Math.abs(1200 * Math.log2(a / b));

// Expected sounding notes of a 6-fret shape, from string 6 to string 1.
export function expectedNotes(shape, { tuning = "standard", capo = 0 } = {}) {
  return [6, 5, 4, 3, 2, 1]
    .filter((string) => shape[6 - string] >= 0)
    .map((string) => ({ string, fret: shape[6 - string], hz: hz(MIDI[tuning][string] + shape[6 - string] + capo) }));
}

// Compares the notes of strings 1 to 6 with the expected ones, ordered from string 6 to string 1. A note on a
// string above 6 is not judged here (a 7-string mode may sound string 7), but it can only be string 7.
export function expectNotes(actual, expected, { fret = true } = {}) {
  const six = actual.filter((note) => note.string >= 1 && note.string <= 6).sort((a, b) => b.string - a.string);
  expect(six.map((note) => note.string), "strings that sounded").toEqual(expected.map((note) => note.string));
  if (fret) expect(six.map((note) => note.fret), "frets that sounded").toEqual(expected.map((note) => note.fret));
  six.forEach((note, i) => {
    expect(Number.isFinite(note.frequency), `frequency of string ${note.string}`).toBe(true);
    expect(cents(note.frequency, expected[i].hz), `frequency of string ${note.string} against ${expected[i].hz} Hz`).toBeLessThan(2);
  });
  for (const note of actual) expect([1, 2, 3, 4, 5, 6, 7], `string ${note.string}`).toContain(note.string);
}

export async function expectDots(page, shape, capo = 0, strings = [1, 2, 3, 4, 5, 6]) {
  for (const n of strings) {
    const fret = shape[6 - n];
    await expect(by(page, `dot-${n}`), `dot-${n}`).toHaveAttribute("data-fret", fret < 0 ? "x" : String(fret + capo));
  }
}

// Whether an element is on the page and drawn: present, not display:none (itself or an ancestor), not
// visibility:hidden. A box of zero size still counts, so a thin or empty string row is not a failure.
export const isRendered = (page, id) =>
  page.evaluate((testid) => {
    const element = document.querySelector(`[data-testid="${testid}"]`);
    return element !== null && element.getClientRects().length > 0 && getComputedStyle(element).visibility !== "hidden";
  }, id);

export async function expectRendered(page, id) {
  await expect.poll(() => isRendered(page, id), { message: `${id} must be on the page and drawn` }).toBe(true);
}

export const expectNoChord =(page) => expect(by(page, "chord-name")).toHaveText(/^\s*$/);

// A select is set by option value, or by option text when no value matches; focus goes back to the body.
export async function choose(page, id, value) {
  const select = by(page, id);
  const options = await select.evaluate((element) => [...element.options].map((option) => ({ value: option.value, text: option.textContent.trim() })));
  let index = options.findIndex((option) => option.value === String(value));
  if (index < 0) index = options.findIndex((option) => option.text === String(value));
  expect(index, `${id} has no option ${value} (options: ${options.map((option) => option.value).join(", ")})`).toBeGreaterThanOrEqual(0);
  await select.selectOption({ index });
  await blur(page);
}

export const optionValues = (page, id) => by(page, id).evaluate((element) => [...element.options].map((option) => option.value));

export async function setSlider(page, id, value) {
  await by(page, id).fill(String(value));
  await blur(page);
}

// Types a tempo and leaves the field, so that a change handler runs.
export async function setTempo(page, value) {
  const field = by(page, "tempo");
  await field.fill(String(value));
  await field.press("Tab");
  await blur(page);
}

// Puts the metronome toggle on or off, whether it is a checkbox or a button with aria-pressed.
export async function setMetronome(page, on) {
  const toggle = by(page, "metronome");
  const isOn = await toggle.evaluate((element) => {
    if (element.type === "checkbox") return element.checked;
    const state = element.getAttribute("aria-pressed") ?? element.getAttribute("aria-checked");
    return state === "true";
  });
  if (isOn !== on) await toggle.click();
  await blur(page);
}

// Text of an element sampled every 20 ms for `ms` milliseconds, inside the page.
export function sampleText(page, id, ms) {
  return page.evaluate(
    ({ id: testid, ms: span }) =>
      new Promise((resolve) => {
        const seen = [];
        const start = performance.now();
        const timer = setInterval(() => {
          const element = document.querySelector(`[data-testid="${testid}"]`);
          seen.push(element ? element.textContent.trim() : "");
          if (performance.now() - start >= span) {
            clearInterval(timer);
            resolve(seen);
          }
        }, 20);
      }),
    { id, ms },
  );
}

// "E4 +0": a note name with its octave, then the cents as a whole number, a sign allowed, a unit allowed.
const SHARP = String.fromCharCode(0x266f);
const FLAT = String.fromCharCode(0x266d);
const MINUS = String.fromCharCode(0x2212);
const CENT = String.fromCharCode(0xa2);
export const READOUT = new RegExp(`^\\s*([A-G](?:#|b|${SHARP}|${FLAT})?-?\\d+)(?:\\s+|(?=[+\\-${MINUS}]))([+\\-${MINUS}]?\\d+)\\s*(?:${CENT}|c|cents?)?\\s*$`);

export async function readoutName(page) {
  const text = (await by(page, "pitch-readout").textContent()) ?? "";
  const match = READOUT.exec(text);
  return match ? match[1] : null;
}

// Whether the notes of a strum come in the order of the given strings when read by time.
export function inTimeOrder(list) {
  return list
    .map((note, index) => ({ note, index }))
    .sort((a, b) => a.note.time - b.note.time || a.index - b.index)
    .map(({ note }) => note);
}
// How far a strum is spread. `time` is the AudioContext time at which a note starts (SPEC.md), so it is the
// one number that says how the strum is spread; `timeSpan` is its span and is the only one an upper bound may
// use, because the arrival of an event (`at`) also grows with the load of the machine on a correct page.
// A page may stamp its events with the scheduled start time (all events of a strum arrive together) or fire
// each event at its start (the stamp may be the coarse audio clock), so `spanOf`, the larger of the span of the
// stamps and the span of the arrivals, is used for a lower bound only ("the strum is spread").
const range = (values) => Math.max(...values) - Math.min(...values);
export const timeSpan = (list) => range(list.map((note) => note.time));
export const spanOf = (list) => Math.max(timeSpan(list), range(list.map((note) => note.at ?? note.time)));
// The spread of a strum for a comparison between strums ("a longer set time gives a longer strum"). The arrival
// span of a strum on a loaded machine can exceed the spread that was set, so the span of the stamps is used
// whenever the page stamps its events apart (1 ms or more), and the span of the arrivals only for a page whose
// stamps all coincide.
export const spreadOf = (list) => (timeSpan(list) >= 0.001 ? timeSpan(list) : spanOf(list));

// The accent of a click may be a boolean or a number; a is stronger than b.
export function louder(a, b) {
  if (typeof a === "boolean" && typeof b === "boolean") return a && !b;
  if (typeof a === "number" && typeof b === "number") return a > b;
  return false;
}
