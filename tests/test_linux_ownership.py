"""Check the beginner launcher and solve real Docker permission tasks (spoilers)."""
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parent.parent
LAUNCHER = ROOT / "linux-ownership/lab"
SPEC = runpy.run_path(str(ROOT / "docs/.internal/maintainer/answer-key/linux_ownership.py"))
SOLUTIONS = {
    "FO-01": "chmod go-rw private-notes.txt",
    "FO-02": "chmod 640 team-readme.txt",
    "FO-03": "chmod 750 inbox",
    "FO-04": "sudo chown learner misplaced.txt",
    "FO-05": "chgrp teachers report.txt",
    "FO-06": "sudo chown archivist:archive handover.txt\nsudo chmod 640 handover.txt",
    "FO-07": "chmod 2770 shared",
}


@pytest.fixture
def launcher_env(tmp_path):
    tool = tmp_path / "docker"
    log = tmp_path / "docker.jsonl"
    tool.write_text("#!" + sys.executable + "\n" + '''import json, os, sys, tarfile
args = sys.argv[1:]
entry = {"args": args}
if args[0] == "build":
    with tarfile.open(fileobj=sys.stdin.buffer, mode="r|*") as stream:
        entry["members"] = [member.name for member in stream]
with open(os.environ["DOCKER_TEST_LOG"], "a") as stream:
    stream.write(json.dumps(entry) + "\\n")
if args[0] == "info" and os.environ.get("DOCKER_TEST_FAIL_INFO"):
    sys.exit(1)
if args[0] == "build" and os.environ.get("DOCKER_TEST_FAIL_BUILD"):
    sys.exit(1)
''')
    tool.chmod(0o755)
    return dict(os.environ, PATH=str(tmp_path) + os.pathsep + os.environ["PATH"], DOCKER_TEST_LOG=str(log)), log


def run_launcher(env, *args):
    return subprocess.run([str(LAUNCHER), *args], env=env, text=True, capture_output=True, timeout=20)


def test_help_starts_nothing(launcher_env):
    env, log = launcher_env
    result = run_launcher(env, "--help")
    assert result.returncode == 0 and "second terminal" in result.stdout
    assert not log.exists()


def test_build_streams_only_sources_and_never_starts_container(launcher_env):
    env, log = launcher_env
    result = run_launcher(env, "build")
    assert result.returncode == 0, result.stderr
    calls = [json.loads(line) for line in log.read_text().splitlines()]
    assert [call["args"][0] for call in calls] == ["info", "build"]
    assert set(calls[1]["members"]) == {
        "linux-ownership/Dockerfile", "linux-ownership/check-ownership",
        "linux-ownership/welcome.sh", "linux-ownership/README.md",
        "docs/.internal/maintainer/answer-key/linux_ownership.py",
    }


def test_launcher_opens_limited_container_without_host_mounts(launcher_env):
    env, log = launcher_env
    master, slave = os.openpty()
    try:
        process = subprocess.Popen([str(LAUNCHER)], env=env, stdin=slave, stdout=slave, stderr=slave)
        os.close(slave)
        assert process.wait(timeout=20) == 0
    finally:
        os.close(master)
    calls = [json.loads(line) for line in log.read_text().splitlines()]
    args = calls[-1]["args"]
    assert args == ["run", "--rm", "--interactive", "--tty", "--network", "none",
                    "--pids-limit", "128", "--memory", "256m", "--cpus", "1",
                    "mfano-linux-ownership:local"]


def test_stopped_docker_has_actionable_error(launcher_env):
    env, log = launcher_env
    env["DOCKER_TEST_FAIL_INFO"] = "1"
    result = run_launcher(env, "build")
    assert result.returncode == 1 and "sudo systemctl start docker" in result.stderr
    assert len(log.read_text().splitlines()) == 1


def test_noninteractive_shell_starts_nothing(launcher_env):
    env, log = launcher_env
    result = run_launcher(env)
    assert result.returncode == 2 and "normal terminal" in result.stderr
    assert not log.exists()


def test_failed_build_is_not_followed_by_run(launcher_env):
    env, log = launcher_env
    env["DOCKER_TEST_FAIL_BUILD"] = "1"
    result = run_launcher(env, "build")
    assert result.returncode != 0
    assert all(json.loads(line)["args"][0] != "run" for line in log.read_text().splitlines())


@pytest.fixture(scope="module")
def docker_image():
    if os.environ.get("MFANO_TEST_DOCKER") != "1":
        pytest.skip("Set MFANO_TEST_DOCKER=1 for real Docker ownership checks; CI enables this.")
    image = f"mfano-linux-ownership:test-{os.getpid()}"
    built = subprocess.run([str(LAUNCHER), "build"], env=dict(os.environ, MFANO_OWNERSHIP_IMAGE=image),
                           text=True, capture_output=True, timeout=600)
    assert built.returncode == 0, built.stdout + built.stderr
    return image


@pytest.mark.parametrize("stage", SOLUTIONS)
def test_real_container_changes_reveal_and_submit_each_flag(docker_image, stage, tmp_path):
    target = SPEC["TARGETS"][stage][0][0]
    script = f'''set -euo pipefail
cd /practice/{stage}
if check-ownership {stage} > /tmp/before.txt 2>&1; then exit 20; fi
if grep -q 'MFANO{{' /tmp/before.txt; then exit 21; fi
{SOLUTIONS[stage]}
check-ownership {stage}
# chmod 777 must not be accepted as a shortcut.
sudo chmod 777 {target}
if check-ownership {stage} > /tmp/too-open.txt 2>&1; then exit 22; fi
if grep -q 'MFANO{{' /tmp/too-open.txt; then exit 23; fi
'''
    solved = subprocess.run(["docker", "run", "--rm", "--interactive", "--network", "none", docker_image,
                             "bash", "--noprofile", "--norc", "-s"],
                            input=script, text=True, capture_output=True, timeout=60)
    assert solved.returncode == 0, solved.stdout + solved.stderr
    flag = solved.stdout.strip()
    assert flag == SPEC["FLAGS"][stage]
    registered = next(line.split(":")[1] for line in (ROOT / "flags.sha256").read_text().splitlines()
                      if line.startswith(stage + ":"))
    assert hashlib.sha256(flag.encode()).hexdigest() == registered
    progress = tmp_path / "score.json"
    env = dict(os.environ, LABCTL_PROGRESS_FILE=str(progress))
    args = [str(ROOT / "labctl"), "--json", "submit", stage, "--flag-stdin"]
    preview = subprocess.run(args + ["--dry-run"], env=env, input=flag + "\n", text=True, capture_output=True, check=True)
    assert json.loads(preview.stdout)["data"]["result"] == "valid" and not progress.exists()
    recorded = subprocess.run(args, env=env, input=flag + "\n", text=True, capture_output=True, check=True)
    assert json.loads(recorded.stdout)["data"]["recorded"] is True
    repeated = subprocess.run(args, env=env, input=flag + "\n", text=True, capture_output=True, check=True)
    assert json.loads(repeated.stdout)["data"]["result"] == "already_solved"
    rejected = subprocess.run([str(ROOT / "labctl"), "--json", "submit", "FM-01", "--flag-stdin"],
                              env=env, input=flag + "\n", text=True, capture_output=True)
    assert rejected.returncode == 1 and json.loads(rejected.stdout)["error"]["code"] == "wrong_flag"
    assert json.loads(progress.read_text())["solved"] == [stage]


def test_permissions_follow_files_and_preserve_existing_ids(tmp_path):
    progress = tmp_path / "score.json"
    progress.write_text(json.dumps({"solved": list(SPEC["FLAGS"]) +
        [f"FM-{n:02d}" for n in range(1, 9)] + ["P1-01"], "note": "preserve"}))
    original = progress.read_bytes()
    result = subprocess.run([str(ROOT / "labctl"), "--json", "status", "--limit", "20"],
                            env=dict(os.environ, LABCTL_PROGRESS_FILE=str(progress)), text=True, capture_output=True, check=True)
    data = json.loads(result.stdout)["data"]
    ids = [stage["id"] for stage in data["labs"]]
    assert ids[:8] == [f"FM-{n:02d}" for n in range(1, 9)]
    assert ids[8:15] == list(SPEC["FLAGS"])
    assert data["progress"]["next"]["id"] == "P1-02"
    assert data["progress"]["total"] == 54
    assert progress.read_bytes() == original
