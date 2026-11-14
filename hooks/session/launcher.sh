#!/bin/sh
# Session start launcher. Not opted in (no .sdlc/project.md): print nothing, exit 0.
# Opted in: print the seat text from the plugin; the host adds stdout to the session context.
# No Python, no file written. Any failure is silent and exits 0: a missing seat text must not block a session.
proj="${CLAUDE_PROJECT_DIR:-$PWD}"
[ -f "$proj/.sdlc/project.md" ] || exit 0
seat="${CLAUDE_PLUGIN_ROOT:-}/templates/seat.md"
[ -f "$seat" ] && cat "$seat"
exit 0
