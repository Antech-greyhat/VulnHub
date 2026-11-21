#!/usr/bin/env python3
"""Prepare and check the offline Linux file exercises; scoring stays in labctl."""
import argparse
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_WORKSPACE = ROOT / "var" / "linux-files"
MARKER = ".mfano-linux-files"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "check"))
    parser.add_argument("stage", nargs="?", help="challenge ID, such as FM-01")
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    args = parser.parse_args(argv)
    exercises = runpy.run_path(str(ROOT / "docs/.internal/maintainer/answer-key/linux_files.py"))
    workspace = args.workspace.absolute()
    if args.command == "prepare" and args.stage:
        parser.error("prepare does not take a challenge ID")
    if args.command == "check" and args.stage not in exercises["FLAGS"]:
        parser.error("check needs a registered ID from FM-01 through FM-08")
    try:
        if args.command == "prepare":
            # Never replace a learner's answers, even when they look incomplete.
            workspace.mkdir(parents=True, exist_ok=False)
            exercises["prepare"](workspace)
            (workspace / MARKER).write_text("Mfano Linux file exercises v1\n", encoding="utf-8")
            print(f"Ready: {workspace}\nStart with FM-01. Read linux-files/README.md for the tasks.")
        else:
            if not (workspace / MARKER).is_file():
                raise ValueError("Workspace not prepared. Run the prepare command first.")
            exercises["check"](workspace, args.stage)
            # One flag on stdout also supports piping to labctl --flag-stdin.
            print(exercises["FLAGS"][args.stage])
    except FileExistsError:
        print(f"Workspace already exists: {workspace}. Your work was preserved.\n"
              "Use --workspace with a new directory to start another attempt.", file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        print(f"Not complete: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
