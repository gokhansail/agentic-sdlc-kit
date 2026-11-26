"""Stub scorer for tests/test_build_run.py: same arguments as tools/build_score.py, writes a fixed result.
STUB_FAIL=1 makes 2 of 10 tests fail and writes a fix prompt; the key file content is never echoed."""
import argparse
import json
import os
import sys

parser = argparse.ArgumentParser()
for name in ("--root", "--step", "--harness", "--fake-key-file", "--out", "--prompt-out"):
    parser.add_argument(name)
parser.add_argument("--baseline", action="append", default=[])
args = parser.parse_args()

fail = os.environ.get("STUB_FAIL") == "1"
passed = 8 if fail else 10
result = {"step": int(args.step), "totals": {"all": {"pass": passed, "fail": 10 - passed, "load error": 0, "total": 10}},
          "regressions": [], "arch": {"violations": 0}, "baselines": [os.path.basename(b) for b in args.baseline]}
with open(args.out, "w", encoding="utf-8") as handle:
    json.dump(result, handle)
if fail:
    with open(args.prompt_out, "w", encoding="utf-8") as handle:
        handle.write("Fix this please.\n")
sys.exit(1 if fail else 0)
