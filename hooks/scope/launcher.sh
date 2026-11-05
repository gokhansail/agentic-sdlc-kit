#!/bin/sh
# Scope guard launcher. The host lets a write through on every exit code except 2,
# so in an opted-in project any result other than 0 or 2 is turned into 2 here.
# Not opted in (no .sdlc/project.md): exit 0 before any Python starts.
# The hook input on stdin must reach the guard unread, so every probe reads /dev/null.
proj="${CLAUDE_PROJECT_DIR:-$PWD}"
[ -f "$proj/.sdlc/project.md" ] || exit 0

deny() {
    echo "scope guard: $1" >&2
    exit 2
}

script="${CLAUDE_PLUGIN_ROOT:-}/tools/scope_guard.py"
if [ -z "${CLAUDE_PLUGIN_ROOT:-}" ] || [ ! -f "$script" ]; then
    deny "guard script not found; writes are denied until the plugin is repaired"
fi

# A candidate counts only if it runs and is Python 3.10 or newer; the Windows store stub fails this.
probe() {
    "$@" -I -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' </dev/null >/dev/null 2>&1
}
if probe python; then
    set -- python
elif probe python3; then
    set -- python3
elif probe py -3; then
    set -- py -3
else
    deny "no working Python 3.10 or newer found (tried python, python3, py -3); writes are denied"
fi

PYTHONUTF8=1 "$@" -I -X utf8 "$script" --root "$proj"
code=$?
case "$code" in
    0 | 2) exit "$code" ;;
esac
deny "the guard failed with exit code $code; the write is denied"
