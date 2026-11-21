import { noop } from "./engine.js";

document.addEventListener("keydown", (event) => {
  if (event.code === "KeyQ") noop();
});
