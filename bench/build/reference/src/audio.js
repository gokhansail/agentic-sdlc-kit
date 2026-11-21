import { renderPluck } from "./engine.js";

const NOTE_SECONDS = 4;
const FADE_SECONDS = 0.04;

// Browser side of the sound: plays renderPluck buffers through Web Audio. Not part of the engine.
export function createAudio() {
  const context = new AudioContext();
  const buffers = new Map();
  const voices = new Set();

  function bufferFor(string, fret, frequency) {
    const key = `${string}:${fret}`;
    let buffer = buffers.get(key);
    if (!buffer) {
      const samples = renderPluck({
        frequency,
        sampleRate: context.sampleRate,
        durationSeconds: NOTE_SECONDS,
        seed: string * 64 + fret,
      });
      buffer = context.createBuffer(1, samples.length, context.sampleRate);
      buffer.copyToChannel(samples, 0);
      buffers.set(key, buffer);
    }
    return buffer;
  }

  return {
    context,
    resume: () => context.resume(),
    // Starts the note now and returns the AudioContext time it starts.
    play(string, fret, frequency) {
      const time = context.currentTime;
      const source = context.createBufferSource();
      const gain = context.createGain();
      source.buffer = bufferFor(string, fret, frequency);
      source.connect(gain).connect(context.destination);
      const voice = { source, gain };
      voices.add(voice);
      source.onended = () => voices.delete(voice);
      source.start(time);
      return time;
    },
    stopAll() {
      const now = context.currentTime;
      for (const { source, gain } of voices) {
        gain.gain.setValueAtTime(gain.gain.value, now);
        gain.gain.linearRampToValueAtTime(0, now + FADE_SECONDS);
        source.stop(now + FADE_SECONDS);
      }
      voices.clear();
    },
  };
}
