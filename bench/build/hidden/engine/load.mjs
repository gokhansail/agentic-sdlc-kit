import path from "node:path";
import { pathToFileURL } from "node:url";

// Imports the project's engine. Called inside each test, so a missing or broken engine is a failure
// of that test and never a load error of the test file.
export async function loadEngine() {
  const root = process.env.GUITAR_ROOT;
  if (!root) throw new Error("GUITAR_ROOT is not set");
  const entry = path.resolve(root, "src", "engine.js");
  return import(pathToFileURL(entry).href);
}
