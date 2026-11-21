// frets are ordered like chordShape returns them: the first entry is the highest-numbered string,
// -1 is a muted string. The strum takes spreadMs from its first note to its last.
export function strumSchedule(frets, direction, startTime, spreadMs) {
  if (direction !== "down" && direction !== "up") {
    throw new RangeError(`direction must be "down" or "up", got ${direction}`);
  }
  const count = frets.length;
  const strings = Array.from({ length: count }, (_, i) => count - i); // down: highest number first
  if (direction === "up") strings.reverse();
  const sounding = strings.filter((string) => frets[count - string] >= 0);
  const gap = sounding.length > 1 ? spreadMs / 1000 / (sounding.length - 1) : 0;
  return sounding.map((string, i) => ({ string, fret: frets[count - string], time: startTime + i * gap }));
}
