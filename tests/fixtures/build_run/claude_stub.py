"""Stub `claude` for tests/test_build_run.py. `--version` prints STUB_VERSION; anything else records what it was
started with (arguments, folder, the names of the variables it can see, never their values) in STUB_OUT."""
import json
import os
import sys

if sys.argv[1:] == ["--version"]:
    print(os.environ.get("STUB_VERSION", "2.1.332 (Claude Code)"))
    sys.exit(0)

seen = sorted(n for n in os.environ if n.startswith(("ANTHROPIC", "CLAUDE")))
record = {"argv": sys.argv[1:], "cwd": os.getcwd(), "names": seen, "config_dir": os.environ.get("CLAUDE_CONFIG_DIR"),
          "autoupdate": os.environ.get("DISABLE_AUTOUPDATER")}
with open(os.environ["STUB_OUT"], "w", encoding="utf-8") as handle:
    json.dump(record, handle)
sys.exit(0)
