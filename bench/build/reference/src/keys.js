// The only place in the project that names KeyboardEvent.code values.
const CHORD_KEYS = {
  KeyQ: "C",
  KeyW: "G",
  KeyE: "D",
  KeyR: "Em",
  KeyA: "Am",
  KeyS: "F",
  KeyD: "A",
  KeyF: "E",
};

const STRING_KEYS = {
  KeyH: 6,
  KeyJ: 5,
  KeyK: 4,
  KeyL: 3,
  Semicolon: 2,
  Quote: 1,
  KeyY: 7,
};

export function keyToAction(code) {
  if (typeof code !== "string") return null;
  if (Object.hasOwn(CHORD_KEYS, code)) return { type: "chord", chord: CHORD_KEYS[code] };
  if (Object.hasOwn(STRING_KEYS, code)) return { type: "pluck", string: STRING_KEYS[code] };
  if (code === "KeyZ") return { type: "open" };
  if (code === "Space") return { type: "strum", direction: "down" };
  if (code === "KeyM") return { type: "strum", direction: "up" };
  if (code === "Period") return { type: "mute" };
  return null;
}
