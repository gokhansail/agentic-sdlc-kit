// Sound engine entry. Pure: no browser API anywhere in this import graph.
export { noteFrequency, noteName } from "./notes.js";
export { renderPluck } from "./pluck.js";
export { chordShape } from "./chords.js";
export { keyToAction } from "./keys.js";
export { strumSchedule } from "./strum.js";
export { spectrum, detectPitch } from "./analysis.js";
export { metronomeClicks, clampTempo } from "./metronome.js";
export { parseSong, songSchedule } from "./song.js";
