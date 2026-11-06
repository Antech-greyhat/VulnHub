#!/usr/bin/env python3
"""Helper CLI for the Mfano lab. Run `python labctl.py --help`."""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FLAGS_FILE = ROOT / "flags.sha256"
PROGRESS_FILE = ROOT / ".labprogress.json"


def load_stages():
    stages = []
    for raw in FLAGS_FILE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        stage_id, digest, category, difficulty = line.split(":", 3)
        stages.append({"id": stage_id, "hash": digest, "category": category, "difficulty": difficulty})
    return stages


def load_progress():
    if not PROGRESS_FILE.exists():
        return []
    try:
        return json.loads(PROGRESS_FILE.read_text(encoding="utf-8")).get("solved", [])
    except (json.JSONDecodeError, AttributeError):
        print("Warning: .labprogress.json is damaged, starting from an empty list.", file=sys.stderr)
        return []


def save_progress(solved):
    PROGRESS_FILE.write_text(json.dumps({"solved": solved}, indent=2) + "\n", encoding="utf-8")


def describe_next(stages, solved):
    stage = next((stage for stage in stages if stage["id"] not in solved), None)
    if stage is None:
        return "All stages solved. Well done!" if stages else "No stages built yet."
    return f"Next stage: {stage['id']} ({stage['category']}, {stage['difficulty']})"


def cmd_submit(args):
    digest = hashlib.sha256(args.flag.strip().encode("utf-8")).hexdigest()
    stages = load_stages()
    match = next((stage for stage in stages if stage["hash"] == digest), None)
    if match is None:
        print("wrong flag")
        return 1
    solved = load_progress()
    if match["id"] in solved:
        print(f"Stage {match['id']} is already solved.")
    else:
        solved.append(match["id"])
        save_progress(solved)
        print(f"Correct! Stage {match['id']} solved ({match['category']}, {match['difficulty']}).")
    print(describe_next(stages, solved))
    return 0


def cmd_status(_args):
    stages = load_stages()
    solved = load_progress()
    if stages:
        print(f"{'Stage':<8}{'OWASP 2025 category':<44}{'Difficulty':<14}Status")
        for stage in stages:
            state = "solved" if stage["id"] in solved else "-"
            print(f"{stage['id']:<8}{stage['category']:<44}{stage['difficulty']:<14}{state}")
    done = sum(1 for stage in stages if stage["id"] in solved)
    print(f"{done} / {len(stages)} solved")
    print(describe_next(stages, solved))
    return 0


def compose(*parts):
    if shutil.which("docker") is None:
        print("Docker was not found. Install Docker Desktop, then try again.", file=sys.stderr)
        return 1
    return subprocess.call(["docker", "compose", *parts], cwd=ROOT)


def cmd_start(_args):
    return compose("up", "-d", "--build")


def cmd_stop(_args):
    return compose("down")


def cmd_reset(_args):
    return compose("exec", "web", "python", "seed.py")


def cmd_shell(_args):
    return compose("exec", "web", "bash")


def build_parser():
    parser = argparse.ArgumentParser(prog="labctl", description="Run and score the Mfano lab.")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("start", help="start the lab containers").set_defaults(func=cmd_start)
    commands.add_parser("stop", help="stop the lab containers").set_defaults(func=cmd_stop)
    commands.add_parser("reset", help="rebuild the database with fresh mock data").set_defaults(func=cmd_reset)
    commands.add_parser("shell", help="open a shell inside the app container").set_defaults(func=cmd_shell)
    submit = commands.add_parser("submit", help="check a flag")
    submit.add_argument("flag")
    submit.set_defaults(func=cmd_submit)
    commands.add_parser("status", help="show stages and progress").set_defaults(func=cmd_status)
    commands.add_parser("score", help="same as status").set_defaults(func=cmd_status)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
