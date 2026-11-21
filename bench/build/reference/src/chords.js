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

// With strings = 7 the result has 7 frets and starts with string 7, which a chord leaves muted.
export function chordShape(name, strings = 6) {
  if (!Object.hasOwn(SHAPES, name)) {
    throw new RangeError(`unknown chord: ${name}`);
  }
  if (strings !== 6 && strings !== 7) {
    throw new RangeError(`strings must be 6 or 7, got ${strings}`);
  }
  const frets = [...SHAPES[name]].map((c) => (c === "x" ? -1 : Number(c)));
  return strings === 7 ? [-1, ...frets] : frets;
}
