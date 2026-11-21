import { renderPluck } from "./engine.js";

const FADE_SECONDS = 0.04;
const TAIL_SECONDS = 0.3;
const CLICK_SECONDS = 0.05;

// Browser side of the sound: plays renderPluck buffers and metronome clicks through Web Audio.
// Not part of the engine. A string has one voice: a new note stops the old one on that string first.
export function createAudio() {
  const context = new AudioContext();
  const notes = new Map(); // "frequency:decay" -> { samples, buffer }
  const byString = new Map(); // string number -> latest voice
  const live = new Set(); // every voice that has not ended

  // The render of a note; kept so the pitch readout can analyse the same samples that play.
  function note(frequency, decaySeconds) {
    const key = `${frequency.toFixed(3)}:${decaySeconds}`;
    let entry = notes.get(key);
    if (!entry) {
      const samples = renderPluck({
        frequency,
        sampleRate: context.sampleRate,
        durationSeconds: 1.3 * decaySeconds + TAIL_SECONDS,
        seed: Math.round(frequency * 10),
        decaySeconds,
      });
      const buffer = context.createBuffer(1, samples.length, context.sampleRate);
      buffer.copyToChannel(samples, 0);
      entry = { samples, buffer };
      notes.set(key, entry);
    }
    return entry;
  }

  function fadeOut(voice, when) {
    voice.gain.gain.setValueAtTime(1, when);
    voice.gain.gain.linearRampToValueAtTime(0, when + FADE_SECONDS);
    voice.source.stop(when + FADE_SECONDS);
  }

  return {
    context,
    sampleRate: context.sampleRate,
    resume: () => context.resume(),
    samples: (frequency, decaySeconds) => note(frequency, decaySeconds).samples,
    // Starts a note at `when` (AudioContext seconds). Returns true when it stopped an older note on the string.
    play(string, frequency, decaySeconds, when) {
      const older = byString.get(string);
      if (older) fadeOut(older, when);
      const source = context.createBufferSource();
      const gain = context.createGain();
      source.buffer = note(frequency, decaySeconds).buffer;
      source.connect(gain).connect(context.destination);
      const voice = { source, gain };
      byString.set(string, voice);
      live.add(voice);
      source.onended = () => {
        live.delete(voice);
        if (byString.get(string) === voice) byString.delete(string);
      };
      source.start(when);
      return older !== undefined;
    },
    // Fades every note, also those not started yet. Returns the strings that had a note.
    stopAll() {
      const strings = [...byString.keys()];
      const now = context.currentTime;
      for (const voice of live) fadeOut(voice, now);
      byString.clear();
      return strings;
    },
    click(when, accent) {
      const oscillator = context.createOscillator();
      const gain = context.createGain();
      oscillator.frequency.value = accent ? 1600 : 1000;
      gain.gain.setValueAtTime(accent ? 0.5 : 0.25, when);
      gain.gain.exponentialRampToValueAtTime(0.001, when + CLICK_SECONDS);
      oscillator.connect(gain).connect(context.destination);
      oscillator.start(when);
      oscillator.stop(when + CLICK_SECONDS + 0.01);
    },
  };
}
