import { chordShape, keyToAction, noteFrequency } from "./engine.js";
import { createAudio } from "./audio.js";

const STRINGS = [1, 2, 3, 4, 5, 6];
const NO_CHORD = [0, 0, 0, 0, 0, 0];

let chord = null;
let audio = null;

const startButton = document.querySelector('[data-testid="start-audio"]');
const chordName = document.querySelector('[data-testid="chord-name"]');
const dots = new Map(STRINGS.map((n) => [n, document.querySelector(`[data-testid="dot-${n}"]`)]));

// Frets ordered from string 6 to string 1, as chordShape returns them.
function currentFrets() {
  return chord ? chordShape(chord) : NO_CHORD;
}

function fretOf(string) {
  return currentFrets()[6 - string];
}

function showBoard() {
  chordName.textContent = chord ?? "";
  for (const n of STRINGS) {
    const fret = fretOf(n);
    const dot = dots.get(n);
    dot.dataset.fret = fret < 0 ? "x" : String(fret);
    dot.textContent = fret < 0 ? "x" : String(fret);
    dot.style.setProperty("--fret", String(Math.max(fret, 0)));
  }
}

function pluck(string) {
  const fret = fretOf(string);
  if (fret < 0) return;
  const frequency = noteFrequency(string, fret);
  const time = audio.play(string, fret, frequency);
  document.dispatchEvent(new CustomEvent("guitar:note", { detail: { string, fret, frequency, time } }));
}

function strum(direction) {
  const order = direction === "down" ? [6, 5, 4, 3, 2, 1] : [1, 2, 3, 4, 5, 6];
  for (const n of order) pluck(n);
}

function act(action) {
  if (action.type === "chord") {
    chord = action.chord;
    showBoard();
  } else if (action.type === "open") {
    chord = null;
    showBoard();
  } else if (!audio) {
    return;
  } else if (action.type === "strum") {
    strum(action.direction);
  } else if (action.type === "pluck") {
    pluck(action.string);
  } else if (action.type === "mute") {
    audio.stopAll();
    document.dispatchEvent(new CustomEvent("guitar:mute"));
  }
}

startButton.addEventListener("click", async () => {
  if (!audio) audio = createAudio();
  await audio.resume();
  startButton.textContent = "Audio on";
  startButton.blur();
});

document.addEventListener("keydown", (event) => {
  if (event.repeat || event.ctrlKey || event.metaKey || event.altKey) return;
  const action = keyToAction(event.code);
  if (!action) return;
  event.preventDefault();
  act(action);
});

// A held button would otherwise take the spacebar as a click when the key goes up.
document.addEventListener("keyup", (event) => {
  if (keyToAction(event.code)) event.preventDefault();
});

showBoard();
