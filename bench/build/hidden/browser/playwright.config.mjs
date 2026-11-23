// Playwright configuration of the hidden browser tests. run_browser.py copies it with the specs into a
// temporary folder under the harness and sets GUITAR_URL (the served project), GUITAR_REPORT (the JSON
// report) and PLAYWRIGHT_BROWSERS_PATH. Nothing is written into the project folder.
import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: ".",
  testMatch: /.*\.spec\.mjs$/,
  outputDir: "./results",
  fullyParallel: true,
  workers: Number(process.env.GUITAR_WORKERS || 4),
  retries: 0,
  timeout: 120000,
  expect: { timeout: 10000 },
  reporter: [["json", { outputFile: process.env.GUITAR_REPORT }]],
  use: {
    baseURL: process.env.GUITAR_URL,
    headless: true,
    actionTimeout: 20000,
    navigationTimeout: 60000,
    viewport: { width: 1280, height: 900 },
    launchOptions: { args: ["--mute-audio"] },
  },
});
