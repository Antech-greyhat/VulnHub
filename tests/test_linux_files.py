"""Solve the file exercises with actual Linux commands, then score them (spoilers)."""
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parent.parent
SPEC = runpy.run_path(str(ROOT / "docs/.internal/maintainer/answer-key/linux_files.py"))
SCRIPTS = {
    "FM-01": "cat part-a.txt part-b.txt > answer.txt",
    "FM-02": "echo 'School backup handover' > handover.txt\necho 'Owner: learner' >> handover.txt\necho 'Status: ready' >> handover.txt",
    "FM-03": "less handbook.txt | grep '^ACTIVE backup-window=' > answer.txt",
    "FM-04": "head -n 1 session.log > bookends.txt\ntail -n 1 session.log >> bookends.txt",
    "FM-05": "tac newest-first.log > oldest-first.log",
    "FM-06": "grep '^ERROR backup ' backup.log > failures.txt\nwc -l < failures.txt > count.txt",
    "FM-07": "paste names.txt scores.txt > results.tsv",
    "FM-08": "sort -k1,1 roster.txt > roster.sorted\nsort -k1,1 marks.txt > marks.sorted\njoin roster.sorted marks.sorted > joined.txt",
    "FM-09": r"""printf '%s\n' Yea -v > answers.txt
grep -F '|bench[2]|' workshop-board.txt |
    grep -v -e '^archived[|]' -e '^draft[|]' |
    grep -E '[|](user|password|comment)[|]' |
    cut -d '|' -f 4 >> answers.txt""",
}


def command(*args, expected=0, **kwargs):
    result = subprocess.run(args, text=True, capture_output=True, timeout=20, **kwargs)
    assert result.returncode == expected, result.stdout + result.stderr
    return result


@pytest.fixture
def workspace(tmp_path):
    path = tmp_path / "exercise with spaces"
    command(sys.executable, "-B", str(ROOT / "linux-files/lab.py"), "prepare", "--workspace", str(path))
    return path


def check(workspace, stage, expected=0):
    return command(sys.executable, "-B", str(ROOT / "linux-files/lab.py"), "check", stage,
                   "--workspace", str(workspace), expected=expected, cwd=workspace.parent)


@pytest.mark.parametrize("stage", SCRIPTS)
def test_real_commands_reveal_registered_flag_and_submit(workspace, stage):
    before = check(workspace, stage, expected=1)
    assert "MFANO{" not in before.stdout + before.stderr
    command("bash", "-c", "set -euo pipefail\n" + SCRIPTS[stage], cwd=workspace / stage,
            env=dict(os.environ, LC_ALL="C", LESS="", LESSOPEN="", LESSCLOSE=""))
    flag = check(workspace, stage).stdout.strip()
    assert flag == SPEC["FLAGS"][stage]
    records = dict(line.split(":", 2)[:2] for line in (ROOT / "flags.sha256").read_text().splitlines()
                   if line and not line.startswith("#"))
    assert hashlib.sha256(flag.encode()).hexdigest() == records[stage]
    progress = workspace.parent / "score.json"
    env = dict(os.environ, LABCTL_PROGRESS_FILE=str(progress))
    preview = command(str(ROOT / "labctl"), "--json", "submit", stage, "--flag-stdin", "--dry-run",
                      input=flag + "\n", env=env)
    assert json.loads(preview.stdout)["data"]["result"] == "valid"
    assert not progress.exists() and not Path(str(progress) + ".lock").exists()
    scored = command(str(ROOT / "labctl"), "--json", "submit", stage, "--flag-stdin", input=flag + "\n", env=env)
    assert json.loads(scored.stdout)["data"]["recorded"] is True
    repeated = command(str(ROOT / "labctl"), "--json", "submit", stage, "--flag-stdin", input=flag + "\n", env=env)
    assert json.loads(repeated.stdout)["data"]["result"] == "already_solved"
    wrong_id = "FM-02" if stage == "FM-01" else "FM-01"
    command(str(ROOT / "labctl"), "--json", "submit", wrong_id, "--flag-stdin", input=flag + "\n", env=env, expected=1)
    assert json.loads(progress.read_text())["solved"] == [stage]


def test_prepare_preserves_existing_answers(workspace):
    answer = workspace / "FM-01/answer.txt"
    answer.write_text("my unfinished work\n")
    command(sys.executable, "-B", str(ROOT / "linux-files/lab.py"), "prepare", "--workspace", str(workspace), expected=1)
    assert answer.read_text() == "my unfinished work\n"


@pytest.mark.parametrize("stage,name,wrong", [
    ("FM-02", "handover.txt", "Outdated handover: this line must not remain.\nSchool backup handover\nOwner: learner\nStatus: ready\n"),
    ("FM-03", "answer.txt", "RETIRED backup-window=03:00\n"),
    ("FM-04", "bookends.txt", "END session=17\nSTART session=17\n"),
    ("FM-05", "oldest-first.log", SPEC["TIMELINE"][::-1]),
    ("FM-06", "failures.txt", SPEC["FAILURES"] + "DEBUG message=ERROR backup status=failed\n"),
    ("FM-07", "results.tsv", "Amani 72\nChebet 81\nNjeri 67\nOtieno 90\n"),
    ("FM-08", "joined.txt", "MHS1004 Otieno 67\nMHS1002 Chebet 54\n"),
    ("FM-09", "answers.txt", "Yea\n-v\nbobthebuilder\nLinuxIsGawd\nReturn the brushes to the art room.\n"),
])
def test_common_mistakes_do_not_reveal_flags(workspace, stage, name, wrong):
    for output, text in SPEC["answers"](stage).items():
        (workspace / stage / output).write_text(text)
    (workspace / stage / name).write_text(wrong)
    result = check(workspace, stage, expected=1)
    assert "MFANO{" not in result.stdout + result.stderr


def test_files_are_first_without_changing_existing_progress(tmp_path):
    progress = tmp_path / "score.json"
    progress.write_text('{"solved":["P1-01"],"note":"keep"}\n')
    original = progress.read_bytes()
    result = command(str(ROOT / "labctl"), "--json", "status", "--limit", "1",
                     env=dict(os.environ, LABCTL_PROGRESS_FILE=str(progress)))
    data = json.loads(result.stdout)["data"]
    assert data["labs"][0]["id"] == data["progress"]["next"]["id"] == "FM-01"
    assert data["progress"]["solved"] == 1
    assert progress.read_bytes() == original
