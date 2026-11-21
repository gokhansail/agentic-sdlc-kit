# Guitar: first version

A guitar played with the computer keyboard in the browser. It should sound like a plucked string.

## Ground rules
- Plain JavaScript ES modules. No npm packages, no CDN, no build step.
- index.html at the folder root. The app must work when this folder is served by any static file server.
- The sound engine entry is src/engine.js. Tests import it in Node 24 with `import`.

## Strings and notes
- Strings are numbered as guitarists do: 1 is the high E, 6 is the low E.
- Standard tuning: 6 E2, 5 A2, 4 D3, 3 G3, 2 B3, 1 E4. A4 = 440 Hz, equal temperament.

## Engine functions (named exports of src/engine.js)
- noteFrequency(string, fret) returns the frequency in Hz.
- renderPluck({frequency, sampleRate, durationSeconds, seed}) returns a Float32Array of
  round(sampleRate * durationSeconds) samples in [-1, 1]. The same seed gives the same samples.
  The pitch of the render, measured from 0.1 s to 0.5 s, is within 5 cents of `frequency`, for every
  string and every fret from 0 to 19, at 44100 Hz and at 48000 Hz.
- chordShape(name) returns 6 frets ordered from string 6 to string 1, -1 for a muted string.
  Chords: C x32010, G 320003, D xx0232, Em 022000, Am x02210, F 133211, A x02220, E 022100.
- keyToAction(code) takes a KeyboardEvent.code and returns one of
  {type: "chord", chord}, {type: "open"}, {type: "strum", direction: "down" | "up"},
  {type: "mute"}, {type: "pluck", string}, or null.

## Key map (KeyboardEvent.code, so it works on any keyboard layout)
- Left hand, chords (a chord stays selected until another chord key or KeyZ):
  KeyQ C, KeyW G, KeyE D, KeyR Em, KeyA Am, KeyS F, KeyD A, KeyF E. KeyZ: no chord, open strings.
- Right hand: Space strums down, KeyM strums up, Period mutes all strings.
- Single strings: KeyH 6, KeyJ 5, KeyK 4, KeyL 3, Semicolon 2, Quote 1. A single string plays the
  fret the selected chord gives it, or open with no chord; a muted string in the chord plays nothing.

## Page (data-testid names the tests use)
- start-audio: a button that starts sound (browsers need a click first).
- fretboard: the fretboard. string-<n> for each string n.
- dot-<n>: the marker on string n, with a data-fret attribute: the fret, 0 for open, x for muted.
- chord-name: the selected chord's name, empty with no chord.

## Events
- Every note that starts fires document event "guitar:note" with detail
  {string, fret, frequency, time}; time is the AudioContext time the note starts, in seconds.
- Mute fires "guitar:mute".
