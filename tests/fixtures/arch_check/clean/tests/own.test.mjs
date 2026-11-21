// An arm's own tests may name key codes and use browser names; the check skips test files.
import { chordFor } from "../src/engine.js";

if (chordFor("KeyQ") !== "C") throw new Error("KeyQ should give C");
console.log(typeof window);
