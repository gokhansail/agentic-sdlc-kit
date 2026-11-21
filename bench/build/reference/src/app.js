import {
  chordShape, clampTempo, detectPitch, keyToAction, metronomeClicks, noteFrequency, noteName,
  parseSong, songSchedule, strumSchedule,
} from "./engine.js";
import { createAudio } from "./audio.js";
import { sharePreset } from "./share.js";

const SUSTAIN_SECONDS = { short: 1, normal: 3, long: 6 };
const BEATS_PER_BAR = 4;
const LOOKAHEAD_SECONDS = 0.25;
const SCHEDULER_MS = 50;
const SONG_LEAD_SECONDS = 0.1;

const $ = (id) => document.querySelector(`[data-testid="${id}"]`);
const startButton = $("start-audio");
const chordName = $("chord-name");
const readout = $("pitch-readout");
const spreadSlider = $("strum-spread");
const capoSelect = $("capo");
const tuningSelect = $("tuning");
const sustainSelect = $("sustain");
const stringsSelect = $("strings");
const metronomeToggle = $("metronome");
const tempoInput = $("tempo");
const shareButton = $("share");
const shareCode = $("share-code");
const shareStatus = document.getElementById("share-status");
const songInput = $("song-input");
const songPlay = $("song-play");
const songStatus = document.getElementById("song-status");
const spreadValue = document.getElementById("spread-value");
const rows = new Map([1, 2, 3, 4, 5, 6, 7].map((n) => [n, $(`string-${n}`)]));
const dots = new Map([1, 2, 3, 4, 5, 6, 7].map((n) => [n, $(`dot-${n}`)]));

let chord = null; // the chord the player selected; null means open strings
let audio = null;
let metronomeTimer = null;
let nextBar = 0;
let songTimers = [];

const emit = (type, detail) => document.dispatchEvent(new CustomEvent(type, { detail }));
const stringCount = () => Number(stringsSelect.value);
const capo = () => Number(capoSelect.value);
const spreadMs = () => Number(spreadSlider.value);
const decaySeconds = () => SUSTAIN_SECONDS[sustainSelect.value];
const tempo = () => clampTempo(tempoInput.value.trim() === "" ? NaN : tempoInput.value);

// Frets of a chord with the capo added, ordered from the highest-numbered string to string 1 as
// chordShape returns them; -1 stays muted. With no chord every string is open.
function shapeOf(name) {
  const strings = stringCount();
  const base = name ? chordShape(name, strings) : new Array(strings).fill(0);
  return base.map((fret) => (fret < 0 ? -1 : fret + capo()));
}

function showBoard(name = chord) {
  const frets = shapeOf(name);
  chordName.textContent = name ?? "";
  for (const [n, row] of rows) {
    row.hidden = n > frets.length;
    const fret = n <= frets.length ? frets[frets.length - n] : -1;
    const dot = dots.get(n);
    dot.dataset.fret = fret < 0 ? "x" : String(fret);
    dot.textContent = fret < 0 ? "x" : String(fret);
    dot.style.setProperty("--fret", String(Math.max(fret, 0)));
  }
}

async function ensureAudio() {
  if (!audio) audio = createAudio();
  await audio.resume();
  startButton.textContent = "Audio on";
  startButton.blur();
}

// Starts one note at an AudioContext time and tells the page about it.
function playNote(string, fret, time) {
  const frequency = noteFrequency(string, fret, tuningSelect.value);
  if (audio.play(string, frequency, decaySeconds(), time)) emit("guitar:stop", { string });
  emit("guitar:note", { string, fret, frequency, time });
  return frequency;
}

// The pitch the app hears: detectPitch on the samples of the last note, shown as "E4 +0".
function showPitch(frequency) {
  const found = detectPitch(audio.samples(frequency, decaySeconds()), audio.sampleRate);
  if (!(found > 0)) {
    readout.textContent = "";
    return;
  }
  const { name, cents } = noteName(found);
  readout.textContent = `${name} ${cents < 0 ? "-" : "+"}${Math.abs(cents)}`;
}

function pluck(string) {
  if (string > stringCount()) return;
  const fret = shapeOf(chord)[stringCount() - string];
  if (fret < 0) return;
  showPitch(playNote(string, fret, audio.context.currentTime));
}

function strum(name, direction, startTime) {
  const entries = strumSchedule(shapeOf(name), direction, startTime, spreadMs());
  let last = null;
  for (const entry of entries) last = playNote(entry.string, entry.fret, entry.time);
  if (last !== null) showPitch(last);
}

function mute() {
  for (const string of audio.stopAll()) emit("guitar:stop", { string });
  emit("guitar:mute");
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
    strum(chord, action.direction, audio.context.currentTime);
  } else if (action.type === "pluck") {
    pluck(action.string);
  } else if (action.type === "mute") {
    mute();
  }
}

// Metronome: bars are scheduled a little ahead of the audio clock. A tempo change counts from the next bar.
function scheduleBars() {
  const horizon = audio.context.currentTime + LOOKAHEAD_SECONDS;
  while (nextBar < horizon) {
    const bpm = tempo();
    const barSeconds = (60 / bpm) * BEATS_PER_BAR;
    for (const click of metronomeClicks(bpm, BEATS_PER_BAR, barSeconds - 1e-6)) {
      const time = nextBar + click.time;
      audio.click(time, click.accent);
      emit("guitar:click", { time, accent: click.accent });
    }
    nextBar += barSeconds;
  }
}

async function setMetronome(on) {
  clearInterval(metronomeTimer);
  metronomeTimer = null;
  if (!on) return;
  await ensureAudio();
  if (!metronomeToggle.checked) return;
  nextBar = audio.context.currentTime + 0.05;
  scheduleBars();
  metronomeTimer = setInterval(scheduleBars, SCHEDULER_MS);
}

function stopSong() {
  for (const timer of songTimers) clearTimeout(timer);
  songTimers = [];
  showBoard();
}

// Song mode: each chord is strummed down on its first beat at the metronome tempo, and its name shows while it plays.
async function playSong() {
  await ensureAudio();
  let song;
  try {
    song = parseSong(songInput.value);
  } catch (error) {
    songStatus.textContent = error.message;
    return;
  }
  if (song.length === 0) {
    songStatus.textContent = "Type a song such as C:4 G:4 Am:2 F:2.";
    return;
  }
  songStatus.textContent = "";
  audio.stopAll();
  stopSong();
  const bpm = tempo();
  const start = audio.context.currentTime + SONG_LEAD_SECONDS;
  for (const { time, chord: name } of songSchedule(song, bpm, start)) {
    strum(name, "down", time);
    songTimers.push(setTimeout(() => showBoard(name), Math.max(0, (time - audio.context.currentTime) * 1000)));
  }
  const end = start + (song.reduce((sum, item) => sum + item.beats, 0) * 60) / bpm;
  songTimers.push(setTimeout(stopSong, Math.max(0, (end - audio.context.currentTime) * 1000)));
}

async function share() {
  shareCode.textContent = "";
  shareStatus.textContent = "Sending...";
  try {
    shareCode.textContent = await sharePreset({
      tuning: tuningSelect.value,
      capo: capo(),
      sustain: sustainSelect.value,
      strings: stringCount(),
      tempo: tempo(),
    });
    shareStatus.textContent = "";
  } catch (error) {
    shareStatus.textContent = `Could not share the settings: ${error.message}.`;
  }
}

startButton.addEventListener("click", ensureAudio);
metronomeToggle.addEventListener("change", () => setMetronome(metronomeToggle.checked));
songPlay.addEventListener("click", playSong);
shareButton.addEventListener("click", share);
tempoInput.addEventListener("change", () => {
  tempoInput.value = String(tempo());
});
spreadSlider.addEventListener("input", () => {
  spreadValue.textContent = `${spreadMs()} ms`;
});
for (const control of [capoSelect, stringsSelect]) control.addEventListener("change", () => showBoard());
// A focused control would keep the keys the player presses for the guitar.
for (const control of [spreadSlider, capoSelect, tuningSelect, sustainSelect, stringsSelect, metronomeToggle]) {
  control.addEventListener("change", () => control.blur());
}

document.addEventListener("keydown", (event) => {
  if (event.repeat || event.ctrlKey || event.metaKey || event.altKey) return;
  if (event.target instanceof Element && event.target.matches('input[type="text"], input[type="number"], textarea')) return;
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
