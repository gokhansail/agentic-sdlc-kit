/* The key map is the one place that may hold key codes, e.g. "KeyQ". */
const MAP = {
  KeyQ: "C",
  Space: "strum",
};

export function chordFor(code) {
  return MAP[code] ?? (code === "Quote" ? "string 1" : null);
}
