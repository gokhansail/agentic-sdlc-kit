// Hidden browser tests, step 8 (prompt step-8.txt). Test titles are the IDs of spec-map.json.
//
// The request to the preset service is answered by the test (page.route) and never leaves the machine.
// The key the Authorization header must carry comes from the environment variable GUITAR_FAKE_KEY, with
// the placeholder {FAKE_KEY} as the default. Readings accepted: the body holds the five named keys with
// the values of the controls, a number may be sent as a number or as a numeric string, other keys in the
// body are not judged, and the content type is not judged. The code counts as shown when the share-code
// element contains it.
import { test, expect } from "@playwright/test";
import { FAKE_KEY, by, choose, setTempo, startApp } from "./helpers.mjs";

const SERVICE_URL = "https://share.example.invalid/v1/presets";
const CORS = {
  "access-control-allow-origin": "*",
  "access-control-allow-headers": "authorization, content-type",
  "access-control-allow-methods": "POST, OPTIONS",
};

// Answers every request to the service. `state.answer` is the body sent back; `seen` collects the requests.
async function intercept(page, state = { answer: { code: "K7Q-4F9X" } }) {
  const seen = [];
  await page.route("https://share.example.invalid/**", async (route) => {
    const request = route.request();
    if (request.method() === "OPTIONS") {
      await route.fulfill({ status: 204, headers: CORS });
      return;
    }
    seen.push({ method: request.method(), url: request.url(), headers: request.headers(), body: request.postData() });
    await route.fulfill({ status: 200, contentType: "application/json", headers: CORS, body: JSON.stringify(state.answer) });
  });
  return seen;
}

async function shareOnce(page, seen) {
  const before = seen.length;
  await by(page, "share").click();
  await expect.poll(() => seen.length, { message: "no request reached the preset service" }).toBeGreaterThan(before);
  return seen[seen.length - 1];
}

test("s8.browser.share-button", async ({ page }) => {
  await startApp(page);
  const button = by(page, "share");
  await expect(button).toBeVisible();
  const isButton = await button.evaluate((element) => element.tagName === "BUTTON" || element.getAttribute("role") === "button");
  expect(isButton, "share must be a button").toBe(true);
  await expect(by(page, "share-code")).toBeAttached();
});

test("s8.browser.share-request", async ({ page }) => {
  await startApp(page);
  const seen = await intercept(page);
  const request = await shareOnce(page, seen);
  expect(request.method).toBe("POST");
  expect(request.url).toBe(SERVICE_URL);
});

test("s8.browser.share-header", async ({ page }) => {
  await startApp(page);
  const seen = await intercept(page);
  const request = await shareOnce(page, seen);
  expect(request.headers.authorization, "the Authorization header").toBe(`Bearer ${FAKE_KEY}`);
});

test("s8.browser.share-body", async ({ page }) => {
  await startApp(page);
  await choose(page, "tuning", "dropD");
  await choose(page, "capo", 3);
  await choose(page, "sustain", "long");
  await choose(page, "strings", 7);
  await setTempo(page, 150);
  const seen = await intercept(page);
  const request = await shareOnce(page, seen);
  let body;
  try {
    body = JSON.parse(request.body);
  } catch {
    throw new Error(`the body is not JSON: ${String(request.body).slice(0, 80)}`);
  }
  for (const key of ["tuning", "capo", "sustain", "strings", "tempo"]) expect(body, `body key ${key}`).toHaveProperty(key);
  expect(body.tuning).toBe("dropD");
  expect(String(body.capo)).toBe("3");
  expect(body.sustain).toBe("long");
  expect(String(body.strings)).toBe("7");
  expect(String(body.tempo)).toBe("150");
});

test("s8.browser.share-code", async ({ page }) => {
  await startApp(page);
  const seen = await intercept(page);
  await shareOnce(page, seen);
  await expect(by(page, "share-code")).toContainText("K7Q-4F9X");
});

test("s8.browser.share-code-new", async ({ page }) => {
  await startApp(page);
  const state = { answer: { code: "K7Q-4F9X" } };
  const seen = await intercept(page, state);
  await shareOnce(page, seen);
  await expect(by(page, "share-code")).toContainText("K7Q-4F9X");
  state.answer = { code: "M2W-8D5Z" };
  await shareOnce(page, seen);
  await expect(by(page, "share-code")).toContainText("M2W-8D5Z");
});
