"""Count the process metrics from pinned record files.

    python -m tools.metrics --source DIR --profile FILE --label NAME --out FILE [--snapshot]

With --snapshot the record files named in the profile are copied from --source
into evidence/raw/<label>/ with a manifest. Without it the existing copy is
read; --source is then not needed. Either way, only the copy is parsed.
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Sequence

from . import gitstats, inputs, metrics_records, output
from .metrics_text import compute
from .profile import ProfileError, load_profile
from .records import CUTOFF

REPO_ROOT = Path(__file__).resolve().parents[2]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m tools.metrics", description=__doc__.split("\n\n")[0])
    parser.add_argument("--source", help="source root holding the record files (needed with --snapshot)")
    parser.add_argument("--profile", required=True, help="profile JSON for the source")
    parser.add_argument("--label", required=True, help="short name, [a-z0-9-]+")
    parser.add_argument("--out", required=True, help="result JSON, inside the project root")
    parser.add_argument("--snapshot", action="store_true", help="copy the record files and write the manifest first")
    return parser


def run(args: argparse.Namespace, root: Path) -> None:
    label = inputs.check_label(args.label)
    profile = load_profile(Path(args.profile))
    out_path = inputs.resolve_inside(root, Path.cwd() / args.out, "--out", allow_absolute=True)
    if args.snapshot:
        if not args.source:
            raise inputs.InputError("--snapshot needs --source")
        manifest = inputs.snapshot(root, Path(args.source).resolve(), profile, label)
    else:
        manifest = inputs.read_manifest(root, label)
    texts = inputs.load_copies(root, label, profile, manifest)
    folders = inputs.load_folders(root, label, profile, manifest)
    git = inputs.load_git(root, label, manifest)
    metrics, found = compute(profile, texts)
    warnings = Counter(manifest["warnings"])
    warnings.update(found)
    for more, found in (
        metrics_records.compute(profile, texts, folders),
        gitstats.compute(profile, texts, git),
    ):
        metrics.update(more)
        warnings.update(found)
    state: dict = {
        "head": manifest["head"],
        "dirty": manifest["dirty"],
        "files": manifest["files"],
        "profile_sha256": profile.sha256,
    }
    if profile.folders:
        state["folders"] = inputs.folder_summary(manifest["folders"])
    result = {
        "schema": output.SCHEMA,
        "label": label,
        "cutoff": CUTOFF.isoformat(),
        "kit_commit": manifest["kit_commit"],
        "input": state,
        "metrics": metrics,
        "warnings": dict(warnings),
    }
    output.write_json(out_path, result, "result")
    print(f"metrics: wrote {out_path.relative_to(root.resolve()).as_posix()}")


def main(argv: Sequence[str] | None = None, root: Path | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        run(args, (root or REPO_ROOT).resolve())
    except (inputs.InputError, ProfileError, output.OutputError, gitstats.GitError) as err:
        print(f"metrics: {err}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
