"""Environment kit of the build bench (T-65): set up the bench folders and drive each arm-step.

    python tools/build_run.py <command> --root <ROOT>

Commands: setup, launch [--fresh|--continue], next, status, copy <id> [<id> ...], log <action> [note],
score, end-step. `run.ps1` (copied into ROOT by setup) forwards its arguments here.

Everything the script writes lands under ROOT (outside this repository): the arm folders, the bare remotes, the
kit extract, `runlog\\` (effort log, run state, setup record, scores, meter output, bundles) and `private\\`.
The fake key and environment variable values are never printed or logged. Standard library only.
Exit codes: 0 ok, 1 STOP (next) or a failed score, 2 a refusal or an error.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import os
import re
import secrets
import shutil
import string
import subprocess
import sys
import tarfile
from decimal import Decimal
from pathlib import Path
from typing import Any, Sequence

KIT_ROOT = Path(__file__).resolve().parent.parent
TEXTS_FILE = KIT_ROOT / "bench" / "build" / "texts.json"
SPEC_FILE = KIT_ROOT / "bench" / "build" / "SPEC.md"
HARNESS_SRC = KIT_ROOT / "bench" / "build" / "harness"
RUN_PS1 = KIT_ROOT / "bench" / "build" / "env" / "run.ps1"
SCORE_SCRIPT = Path(__file__).with_name("build_score.py")
METER_SCRIPT = Path(__file__).with_name("transcript_meter.py")

KIT_TAG = "v0.1.0"
KIT_PATHS = (".claude-plugin", "agents", "skills", "hooks", "server", "tools", "templates")
MARKERS = ("CLAUDE.md", "CLAUDE.local.md", "AGENTS.md", ".claude", ".mcp.json")
REMOVED_VARS = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDE_CODE_SUBAGENT_MODEL", "CLAUDE_PROJECT_DIR",
                "CLAUDE_PLUGIN_ROOT")
SECRET_NAME = re.compile(r"(KEY|TOKEN)", re.IGNORECASE)
EFFORT_COLUMNS = ("ts_start", "ts_end", "arm", "step", "action", "text_id", "count", "minutes", "note")
LOG_ALIASES = {"click": "permission_click", "limit": "wait_limit"}
LOG_ACTIONS = ("permission_click", "typed_command", "wait_limit", "restart", "deviation")
CONFIG_OF = {"w1": "c1", "w2": "c2", "p1": "c0"}
# ABBA order of plan 10.1, K0 (session 0 of the kit arm) first.
BUILD_ORDER = (("kit", 0), ("plain", 1), ("kit", 1), ("kit", 2), ("plain", 2), ("plain", 3), ("kit", 3), ("kit", 4),
               ("plain", 4), ("plain", 5), ("kit", 5), ("kit", 6), ("plain", 6), ("plain", 7), ("kit", 7), ("kit", 8),
               ("plain", 8))
FRESH_STEPS = (0, 1, 4, 7)
MAX_FIX_PROMPTS = 3
SOFT_CAP, HARD_CAP, LOOKAHEAD = 3, 5, 3
USD_CEILING, HANDOFF_RESERVE, BLIND_RESERVE, KIT_FACTOR, PROJECTED_STEPS = 65, 15, 5, 2.5, 28

# Tests set this: parents at or above it are not searched for instruction files.
WALK_FLOOR: Path | None = None


class BenchError(Exception):
    """A refusal or an error; the message goes to stderr and the exit code is 2."""


# ----------------------------------------------------------------------------------------------- small helpers

def user_home() -> Path:
    return Path.home()


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def tree_hash(folder: Path) -> str:
    digest = hashlib.sha256()
    files = sorted((p for p in folder.rglob("*") if p.is_file()), key=lambda p: p.relative_to(folder).as_posix())
    for path in files:
        digest.update(path.relative_to(folder).as_posix().encode("utf-8") + b"\0" + hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def inside(child: Path, parent: Path) -> bool:
    child, parent = child.resolve(), parent.resolve()
    return child == parent or parent in child.parents


def set_clipboard(text: str) -> None:
    """The one clipboard function (the tests replace it): PowerShell Set-Clipboard, text passed on stdin as UTF-8."""
    shell = shutil.which("pwsh") or shutil.which("powershell")
    if shell is None:
        raise BenchError("no PowerShell on PATH for the clipboard")
    script = ("[Console]::InputEncoding = [System.Text.Encoding]::UTF8; "
              "$t = [Console]::In.ReadToEnd(); Set-Clipboard -Value $t")
    done = subprocess.run([shell, "-NoProfile", "-NonInteractive", "-Command", script], input=text.encode("utf-8"),
                          capture_output=True, timeout=60)
    if done.returncode != 0:
        raise BenchError("the clipboard could not be set")


def ask(question: str) -> str:
    return input(question + " ")


def git(*args: str, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    exe = shutil.which("git")
    if exe is None:
        raise BenchError("git is not on PATH")
    done = subprocess.run([exe, *args], cwd=cwd, capture_output=True)
    if check and done.returncode != 0:
        raise BenchError(f"git {args[0]} failed")
    return done


# ----------------------------------------------------------------------------------------------- run log and state

class Run:
    """Paths and records of one ROOT."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.runlog = root / "runlog"

    @property
    def state_path(self) -> Path:
        return self.runlog / "run-state.json"

    @property
    def setup_path(self) -> Path:
        return self.runlog / "setup.json"

    @property
    def effort_path(self) -> Path:
        return self.runlog / "effort-log.csv"

    def setup(self) -> dict[str, Any]:
        return read_json(self.setup_path, "runlog/setup.json (run setup first)")

    def state(self) -> dict[str, Any]:
        return read_json(self.state_path, "runlog/run-state.json (run setup first)")

    def save_state(self, state: dict[str, Any]) -> None:
        temp = self.state_path.with_suffix(".tmp")
        temp.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8", newline="\n")
        os.replace(temp, self.state_path)

    def arm_dir(self, setup: dict[str, Any], arm: str) -> Path:
        return self.root / setup["arms"][arm] / "guitar"

    def config_dir(self, setup: dict[str, Any], arm: str) -> Path:
        return self.root / CONFIG_OF[setup["arms"][arm]]

    def log(self, arm: str, step: str, action: str, *, text_id: str = "", count: str | int = "", minutes: str | float = "",
            note: str = "", start: str | None = None, end: str | None = None) -> None:
        stamp = start or now()
        buffer = io.StringIO()
        csv.writer(buffer, lineterminator="\n").writerow(
            [stamp, end if end is not None else stamp, arm, step, action, text_id, count, minutes, note])
        with self.effort_path.open("a", encoding="utf-8", newline="") as handle:
            handle.write(buffer.getvalue())

    def effort_rows(self) -> list[dict[str, str]]:
        with self.effort_path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))


def read_json(path: Path, what: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise BenchError(f"{what} cannot be read") from error


def current(state: dict[str, Any]) -> dict[str, Any] | None:
    sequence, index = state["sequence"], state["index"]
    return sequence[index] if index < len(sequence) else None


def need_current(state: dict[str, Any]) -> dict[str, Any]:
    item = current(state)
    if item is None:
        raise BenchError("every arm-step is done")
    return item


def build_sequence() -> list[dict[str, Any]]:
    items = [{"arm": "pilot", "step": "1", "mode": "fresh"}, {"arm": "pilot", "step": "2", "mode": "continue"}]
    for arm, step in BUILD_ORDER:
        items.append({"arm": arm, "step": str(step), "mode": "fresh" if step in FRESH_STEPS else "continue"})
    return items


# ----------------------------------------------------------------------------------------------- spend

def meter_totals(run: Run, arm: str) -> dict[str, Any] | None:
    path = run.runlog / "meter" / f"{arm}.json"
    if not path.is_file():
        return None
    return read_json(path, f"meter output of {arm}")


def usd_of(value: Any) -> Decimal:
    return Decimal(str(value)) if value is not None else Decimal(0)


def arm_spent(run: Run, arm: str) -> Decimal:
    data = meter_totals(run, arm)
    return usd_of(data["totals"]["usd"]) if data else Decimal(0)


def step_spent(run: Run, arm: str, step: str) -> Decimal | None:
    data = meter_totals(run, arm)
    if not data or step not in data.get("steps", {}):
        return None
    return usd_of(data["steps"][step]["usage"]["usd"])


def projection_of(state: dict[str, Any], arm: str) -> float | None:
    table = state.get("projection")
    if not table:
        return None
    return table.get("kit" if arm == "kit" else "plain")


def money(value: Any) -> str:
    return "none yet" if value is None else f"{float(value):.2f} USD"


def run_meter(run: Run, setup: dict[str, Any], arm: str) -> str | None:
    """Run the transcript meter for an arm; returns None on success, else the reason it did not run."""
    if not any(r["arm"] == arm and r["action"] == "paste_step" for r in run.effort_rows()):
        return "no paste_step row for this arm yet"
    transcripts = run.config_dir(setup, arm) / "projects"
    if not transcripts.is_dir():
        return "no transcript folder yet"
    out = run.runlog / "meter" / f"{arm}.json"
    argv = [sys.executable, str(METER_SCRIPT), "--transcripts", str(transcripts), "--effort-log", str(run.effort_path),
            "--texts", str(TEXTS_FILE), "--arm", arm, "--out", str(out), "--raw-out", str(run.runlog / "meter-raw")]
    if setup.get("model_id"):
        argv += ["--model", setup["model_id"]]
    captured = sorted((run.runlog / "cost-state").glob(f"{arm}-*.json"))
    if captured:
        argv += ["--cost-state", str(captured[-1])]
    done = subprocess.run(argv, capture_output=True, text=True, timeout=600)
    if done.returncode != 0:
        return "meter: " + (done.stderr.strip().splitlines() or ["failed"])[-1]
    return None


# ----------------------------------------------------------------------------------------------- setup

def parent_markers(root: Path) -> list[str]:
    found = []
    floor = WALK_FLOOR.resolve() if WALK_FLOOR is not None else None
    for parent in root.resolve().parents:
        if floor is not None and (parent == floor or parent in floor.parents):
            break
        for name in MARKERS:
            if (parent / name).exists():
                found.append(name)
    return found


def check_root(root: Path) -> Path:
    root = root.resolve()
    if inside(root, KIT_ROOT):
        raise BenchError("--root is inside the repository: nothing the bench writes may land there")
    return root


def extract_kit(target: Path) -> str:
    done = git("archive", "--format=tar", KIT_TAG, *KIT_PATHS, cwd=KIT_ROOT, check=False)
    if done.returncode != 0:
        raise BenchError(f"git archive {KIT_TAG} failed (is the tag present?)")
    target.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(done.stdout)) as archive:
        for member in archive.getmembers():
            name = Path(member.name)
            if name.is_absolute() or ".." in name.parts or member.issym() or member.islnk():
                raise BenchError("the kit archive holds an unsafe path")
            destination = target / name
            if member.isdir():
                destination.mkdir(parents=True, exist_ok=True)
            elif member.isfile():
                destination.parent.mkdir(parents=True, exist_ok=True)
                handle = archive.extractfile(member)
                destination.write_bytes(handle.read() if handle else b"")
    return tree_hash(target)


def cli_version(claude: str, env: dict[str, str]) -> str:
    try:
        done = subprocess.run([claude, "--version"], capture_output=True, text=True, env=env, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise BenchError("claude --version did not run") from error
    lines = done.stdout.strip().splitlines()
    if done.returncode != 0 or not lines:
        raise BenchError("claude --version failed")
    return lines[0].strip()


def init_arm(folder: Path, remote: Path) -> None:
    identity = ("-c", "user.name=Bench User", "-c", "user.email=bench@example.invalid", "-c", "commit.gpgsign=false")
    folder.mkdir(parents=True)
    git("init", "-q", "-b", "main", cwd=folder)
    git("config", "user.name", "Bench User", cwd=folder)
    git("config", "user.email", "bench@example.invalid", cwd=folder)
    shutil.copyfile(SPEC_FILE, folder / "SPEC.md")
    git("add", "SPEC.md", cwd=folder)
    git(*identity, "commit", "-q", "-m", "Add SPEC.md", cwd=folder)
    git("remote", "add", "origin", str(remote), cwd=folder)


def cmd_setup(args: argparse.Namespace) -> int:
    root = check_root(Path(args.root))
    if inside(root, user_home()):
        raise BenchError("--root is under the user's home: use a new folder directly under a drive root")
    markers = parent_markers(root)
    if markers:
        raise BenchError("a parent folder holds " + ", ".join(sorted(set(markers))) + ": pick another root")
    if root.exists() and any(root.iterdir()):
        raise BenchError("--root exists and is not empty")
    claude = shutil.which("claude")
    if claude is None:
        raise BenchError("claude is not on PATH (the CLI version is pinned at setup)")
    version = cli_version(claude, dict(os.environ))

    run = Run(root)
    for name in ("c0", "c1", "c2", "runlog", "private", "remotes", "harness"):
        (root / name).mkdir(parents=True, exist_ok=True)
    for name in ("package.json", "package-lock.json"):
        if (HARNESS_SRC / name).is_file():
            shutil.copyfile(HARNESS_SRC / name, root / "harness" / name)
    plain_folder, kit_folder = secrets.choice([("w1", "w2"), ("w2", "w1")])
    for label in ("w1", "w2", "p1"):
        remote = root / "remotes" / f"{label}.git"
        git("init", "-q", "--bare", "-b", "main", str(remote))
        init_arm(root / label / "guitar", remote)
    kit_hash = extract_kit(root / "kit")
    key = "sk-" + "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(40))
    (root / "private" / "fake-key.txt").write_text(key + "\n", encoding="utf-8", newline="\n")
    if RUN_PS1.is_file():
        shutil.copyfile(RUN_PS1, root / "run.ps1")

    setup = {"arms": {"plain": plain_folder, "kit": kit_folder, "pilot": "p1"}, "cli_version": version,
             "kit_tag": KIT_TAG, "kit_tree_sha256": kit_hash, "fake_key_sha256": sha256_bytes(key.encode("utf-8")),
             "kit_repo": str(KIT_ROOT), "created": now()}
    (run.runlog / "setup.json").write_text(json.dumps(setup, indent=2) + "\n", encoding="utf-8", newline="\n")
    run.save_state({"index": 0, "sequence": build_sequence(), "done": [], "ceiling": None, "projection": None,
                    "pilot_spent": None})
    run.effort_path.write_text(",".join(EFFORT_COLUMNS) + "\n", encoding="utf-8", newline="\n")
    run.log("", "", "setup", note="setup")
    print("setup done")
    print(f"kit extract {KIT_TAG}: sha256 {kit_hash}")
    print(f"CLI version pinned: {version}")
    print("next: install the harness (npm ci in the harness folder), log in once per config folder, then run next")
    return 0


# ----------------------------------------------------------------------------------------------- launch

def cmd_launch(args: argparse.Namespace) -> int:
    run = Run(check_root(Path(args.root)))
    setup, state = run.setup(), run.state()
    item = need_current(state)
    arm, step = item["arm"], item["step"]
    mode = "fresh" if args.fresh else "continue" if args.cont else item["mode"]

    secret_names = sorted(n for n in os.environ if n.startswith(("ANTHROPIC", "CLAUDE")) and SECRET_NAME.search(n))
    if secret_names:
        raise BenchError("a key or token is visible in the environment (" + ", ".join(secret_names)
                         + "): the bench runs on the subscription login; unset it and start again")
    env = {k: v for k, v in os.environ.items() if k not in REMOVED_VARS}
    left = sorted(n for n in env if n.startswith(("ANTHROPIC", "CLAUDE")))
    print("variables kept (names only): " + (", ".join(left) if left else "none"))
    removed = sorted(n for n in REMOVED_VARS if n in os.environ)
    print("variables removed (names only): " + (", ".join(removed) if removed else "none"))

    claude = shutil.which("claude", path=env.get("PATH"))
    if claude is None:
        raise BenchError("claude is not on PATH")
    version = cli_version(claude, env)
    if version != setup["cli_version"]:
        raise BenchError(f"claude --version is {version!r}, the pin is {setup['cli_version']!r}: stop (plan 7)")

    config = run.config_dir(setup, arm)
    env["CLAUDE_CONFIG_DIR"] = str(config)
    env["DISABLE_AUTOUPDATER"] = "1"
    capture_cost_state(run, arm, config)

    command = [claude, "--model", "opus"]
    if arm == "kit":
        command += ["--plugin-dir", str(run.root / "kit")]
    if mode == "continue":
        command.append("--continue")
    print(f"launching: arm {arm}, step {step}, mode {mode}")
    run.log(arm, step, "launch", note=mode)
    done = subprocess.run(command, cwd=run.arm_dir(setup, arm), env=env)
    run.log(arm, step, "exit", note=f"exit code {done.returncode}")
    return 0


def capture_cost_state(run: Run, arm: str, config: Path) -> None:
    source = config / ".claude.json"
    if not source.is_file():
        print("cost state: no file yet")
        return
    try:
        projects = json.loads(source.read_text(encoding="utf-8")).get("projects", {})
    except (OSError, ValueError, AttributeError):
        print("cost state: file unreadable, not copied")
        return
    target = run.runlog / "cost-state"
    target.mkdir(parents=True, exist_ok=True)
    number = len(list(target.glob(f"{arm}-*.json"))) + 1
    (target / f"{arm}-{number:03d}.json").write_text(json.dumps({"projects": projects}, indent=2) + "\n", encoding="utf-8",
                                                      newline="\n")
    print(f"cost state: copied as {arm}-{number:03d}.json")


# ----------------------------------------------------------------------------------------------- next, status

def describe(run: Run, state: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    item = current(state)
    if item is None:
        print("all arm-steps are done")
        return None, None
    spent = arm_spent(run, "plain") + arm_spent(run, "kit")
    ceiling, proj = state.get("ceiling"), projection_of(state, item["arm"])
    print(f"arm: {item['arm']}")
    print(f"step: {item['step']}" + (" (session 0)" if item["step"] == "0" else ""))
    print(f"mode: {item['mode']}")
    print(f"position: {state['index'] + 1} of {len(state['sequence'])}")
    print(f"spent (build, plain + kit): {spent:.2f} USD; pilot: {money(state.get('pilot_spent'))}")
    print(f"ceiling: {money(ceiling)}; step projection: {money(proj)}")
    reason = None
    if ceiling is not None and proj is not None and float(spent) + LOOKAHEAD * proj > ceiling:
        reason = f"spent + {LOOKAHEAD} x projection passes the ceiling"
    return item, reason


def cmd_status(args: argparse.Namespace) -> int:
    run = Run(check_root(Path(args.root)))
    describe(run, run.state())
    return 0


def cmd_next(args: argparse.Namespace) -> int:
    run = Run(check_root(Path(args.root)))
    item, reason = describe(run, run.state())
    if item is None:
        return 0
    if reason:
        print(f"STOP: {reason}")
        return 1
    print("START")
    return 0


# ----------------------------------------------------------------------------------------------- copy, log

def cmd_copy(args: argparse.Namespace) -> int:
    run = Run(check_root(Path(args.root)))
    state = run.state()
    item = need_current(state)
    texts = read_json(TEXTS_FILE, "texts.json")
    ids = [f"S{item['step']}" if i.lower() == "step" else i for i in args.ids]
    unknown = [i for i in ids if i not in texts]
    if unknown:
        raise BenchError("unknown text id: " + ", ".join(unknown) + "; known: " + " ".join(sorted(texts)))
    key = (run.root / "private" / "fake-key.txt").read_text(encoding="utf-8").strip()
    body = " ".join(texts[i]["text"] for i in ids).replace("{FAKE_KEY}", key)
    set_clipboard(body)
    kind = texts[ids[0]]["type"]
    action = {"step": "paste_step", "fix": "paste_fix", "resume": "paste_resume"}.get(kind, "paste_answer")
    run.log(item["arm"], item["step"], action, text_id=" ".join(ids))
    print(f"on the clipboard: {' '.join(ids)} ({len(body)} characters)")
    return 0


def cmd_log(args: argparse.Namespace) -> int:
    run = Run(check_root(Path(args.root)))
    state = run.state()
    item = need_current(state)
    action = LOG_ALIASES.get(args.action, args.action)
    note = " ".join(args.note)
    if action == "usage":
        run.runlog.mkdir(exist_ok=True)
        with (run.runlog / "usage.csv").open("a", encoding="utf-8", newline="") as handle:
            handle.write(f"{now()},{note}\n")
        print("usage number noted")
        return 0
    if action not in LOG_ACTIONS:
        raise BenchError("unknown log action; use: click, limit, restart, deviation, typed_command, usage")
    run.log(item["arm"], item["step"], action, count=1 if action == "permission_click" else "", note=note)
    print(f"logged {action}")
    return 0


# ----------------------------------------------------------------------------------------------- score

def cmd_score(args: argparse.Namespace) -> int:
    run = Run(check_root(Path(args.root)))
    setup, state = run.setup(), run.state()
    item = need_current(state)
    arm, step = item["arm"], item["step"]
    if step == "0":
        raise BenchError("step 0 (session 0) has no score")
    harness = Path(args.harness) if args.harness else run.root / "harness"
    scores = run.runlog / "scores"
    scores.mkdir(parents=True, exist_ok=True)
    prompt_file = run.runlog / "fix-prompt.txt"
    prompt_file.unlink(missing_ok=True)
    out = scores / f"{arm}-{step}.json"
    argv = [sys.executable, str(SCORE_SCRIPT), "--root", str(run.arm_dir(setup, arm)), "--step", step, "--harness",
            str(harness), "--fake-key-file", str(run.root / "private" / "fake-key.txt"), "--out", str(out),
            "--prompt-out", str(prompt_file)]
    for earlier in sorted(scores.glob(f"{arm}-*.json")):
        if earlier != out and int(earlier.stem.rsplit("-", 1)[1]) < int(step):
            argv += ["--baseline", str(earlier)]
    done = subprocess.run(argv, capture_output=True, text=True, timeout=3600)
    if done.returncode not in (0, 1):
        raise BenchError("scorer: " + (done.stderr.strip().splitlines() or ["failed"])[-1])
    result = read_json(out, "score output")
    totals = result["totals"]["all"]
    failing = totals["total"] - totals["pass"]
    run.log(arm, step, "score", count=failing, note=f"{totals['pass']} of {totals['total']}")
    print(f"score (step {step}): {totals['pass']} passed, {totals['fail']} failed, {totals['load error']} load error, "
          f"of {totals['total']}; {len(result['regressions'])} regressions; arch violations {result['arch']['violations']}")

    reason = run_meter(run, setup, arm)
    spend = step_spent(run, arm, step) if reason is None else None
    proj = projection_of(state, arm)
    capped = False
    if spend is None:
        print(f"step spend: unknown ({reason or 'no usage in the meter output yet'})")
    else:
        print(f"step spend: {float(spend):.2f} USD at list price")
        if proj:
            if float(spend) > HARD_CAP * proj:
                capped = True
                print(f"past {HARD_CAP} x the projection: stopped by cap, paste no more fix prompts")
            elif float(spend) > SOFT_CAP * proj:
                print(f"past {SOFT_CAP} x the projection: recorded")

    if failing and prompt_file.is_file():
        used = sum(1 for r in run.effort_rows() if r["arm"] == arm and r["step"] == step and r["action"] == "paste_fix")
        if capped:
            pass
        elif used >= MAX_FIX_PROMPTS:
            print(f"{used} fix prompts used: no more for this step")
        else:
            set_clipboard(prompt_file.read_text(encoding="utf-8"))
            run.log(arm, step, "paste_fix", text_id="FIX", note=f"fix prompt {used + 1}")
            print(f"fix prompt {used + 1} of {MAX_FIX_PROMPTS} is on the clipboard")
    return 0 if not failing else 1


# ----------------------------------------------------------------------------------------------- end-step

def number_from(answer: str, whole: bool) -> float:
    try:
        value = float(answer.strip().replace(",", "."))
    except ValueError:
        raise BenchError("a number is needed")
    if value < 0 or (whole and value != int(value)):
        raise BenchError("a non-negative " + ("whole " if whole else "") + "number is needed")
    return value


def remote_state(folder: Path) -> str:
    head = git("rev-parse", "HEAD", cwd=folder, check=False).stdout.decode().strip()
    refs = git("ls-remote", "origin", cwd=folder, check=False)
    if refs.returncode != 0:
        return "remote unreachable"
    held = [line.split()[0] for line in refs.stdout.decode().splitlines() if line.strip()]
    if not held:
        return "remote holds no commits"
    return "remote holds the local HEAD" if head in held else "remote does not hold the local HEAD"


def cmd_end_step(args: argparse.Namespace) -> int:
    run = Run(check_root(Path(args.root)))
    setup, state = run.setup(), run.state()
    item = need_current(state)
    arm, step = item["arm"], item["step"]
    minutes = number_from(ask(f"Minutes you spent on {arm} step {step}:"), False)
    clicks = int(number_from(ask("Permission clicks you did not log:"), True))
    if clicks:
        run.log(arm, step, "permission_click", count=clicks, note="reported at end-step")
    if step == "0":
        run.log(arm, step, "exit", minutes=minutes, note="end of session 0")
    else:
        run.log(arm, step, "end_step", minutes=minutes)

    folder = run.arm_dir(setup, arm)
    snapshots = run.runlog / "snapshots"
    snapshots.mkdir(parents=True, exist_ok=True)
    bundle = git("bundle", "create", str(snapshots / f"{arm}-{step}.bundle"), "--all", cwd=folder, check=False)
    print("snapshot: " + ("written" if bundle.returncode == 0 else "failed"))
    reason = run_meter(run, setup, arm)
    print("meter: " + ("written" if reason is None else f"not run ({reason})"))
    print(remote_state(folder))

    state["done"].append({"arm": arm, "step": step, "minutes": minutes, "ended": now()})
    state["index"] += 1
    if arm == "pilot" and (current(state) or {}).get("arm") != "pilot":
        finish_pilot(run, state)
    run.save_state(state)
    following = current(state)
    print("next: " + (f"{following['arm']} step {following['step']}, {following['mode']}" if following else "none, all done"))
    return 0


def finish_pilot(run: Run, state: dict[str, Any]) -> None:
    spent = float(arm_spent(run, "pilot"))
    state["pilot_spent"] = round(spent, 4)
    if state.get("ceiling") is None and spent > 0:
        p = spent / 2
        state["projection"] = {"plain": round(p, 4), "kit": round(KIT_FACTOR * p, 4)}
        state["ceiling"] = round(min(3 * PROJECTED_STEPS * p, USD_CEILING - spent - HANDOFF_RESERVE - BLIND_RESERVE), 4)
        print(f"pilot spent {spent:.2f} USD: ceiling and projections set in run-state.json")


# ----------------------------------------------------------------------------------------------- command line

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="build_run.py", description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("--root", required=True, help="the bench folder (outside this repository)")
    sub.add_parser("setup", parents=[shared], help="make the folders, remotes, kit extract and fake key")
    launch = sub.add_parser("launch", parents=[shared], help="start claude for the current arm-step")
    mode = launch.add_mutually_exclusive_group()
    mode.add_argument("--fresh", "-Fresh", action="store_true")
    mode.add_argument("--continue", "-Continue", dest="cont", action="store_true")
    sub.add_parser("next", parents=[shared], help="print the next arm-step and START or STOP")
    sub.add_parser("status", parents=[shared], help="print the current arm-step and the spend")
    copy = sub.add_parser("copy", parents=[shared], help="put frozen texts on the clipboard")
    copy.add_argument("ids", nargs="+")
    log = sub.add_parser("log", parents=[shared], help="add a line to the effort log")
    log.add_argument("action")
    log.add_argument("note", nargs="*")
    score = sub.add_parser("score", parents=[shared], help="score the arm folder, fix prompt to the clipboard")
    score.add_argument("--harness", default=None, help="default: <ROOT>\\harness")
    sub.add_parser("end-step", parents=[shared], help="close the arm-step")
    return parser


COMMANDS = {"setup": cmd_setup, "launch": cmd_launch, "next": cmd_next, "status": cmd_status, "copy": cmd_copy,
            "log": cmd_log, "score": cmd_score, "end-step": cmd_end_step}


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0
    try:
        return COMMANDS[args.command](args)
    except BenchError as error:
        print(f"build_run: {error}", file=sys.stderr)
        return 2
    except (OSError, subprocess.TimeoutExpired) as error:
        print(f"build_run: {type(error).__name__}: the command could not finish", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
