import { chordFor } from "./engine.js";

// Browser code lives outside the engine graph and may use the page; it never names a key code.
document.addEventListener("keydown", (event) => {
  // KeyQ in a comment is not a literal
  const action = chordFor(event.code);
  if (action) window.dispatchEvent(new Event("played"));
});
