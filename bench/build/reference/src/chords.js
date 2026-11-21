// One character per string, from string 6 to string 1; x is a muted string.
const SHAPES = {
  C: "x32010",
  G: "320003",
  D: "xx0232",
  Em: "022000",
  Am: "x02210",
  F: "133211",
  A: "x02220",
  E: "022100",
};

export function chordShape(name) {
  if (!Object.hasOwn(SHAPES, name)) {
    throw new RangeError(`unknown chord: ${name}`);
  }
  return [...SHAPES[name]].map((c) => (c === "x" ? -1 : Number(c)));
}
