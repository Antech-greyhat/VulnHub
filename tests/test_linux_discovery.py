"""Recover discovery flags using real shell tools, then score them (spoilers)."""
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parent.parent
LAUNCHER = ROOT / "linux-discovery/lab"
SPEC = runpy.run_path(str(ROOT / "docs/.internal/maintainer/answer-key/linux_discovery.py"))
SOLUTIONS = {
    "LD-01": "cat ./-",
    "LD-02": 'cat -- "--fee handover notes--"',
    "LD-03": "cat ./inhere/...school-note",
    "LD-04": '''file -N --mime-type ./inhere/* | awk -F ': ' '$2 == "text/plain" {print $1}' |
while IFS= read -r path; do cat -- "$path"; done''',
    "LD-05": '''find ./inhere -type f -size 1033c ! -executable -exec file -N --mime-type {} + |
awk -F ': ' '$2 == "text/plain" {print $1}' |
while IFS= read -r path; do grep '^MFANO{' "$path"; done''',
    "LD-06": '''status=0
matches=$(find ./system -type f -size 33c -user teacher -group archive 2>/dev/null) || status=$?
# A denied directory gives find exit status 1 while readable matches survive.
[[ $status == 1 && -n $matches && $matches != *$'\\n'* ]]
[[ $(stat -c '%U:%G:%s' -- "$matches") == teacher:archive:33 ]]
cat -- "$matches"''',
    "LD-07": "sort data.txt | uniq -u",
}


def command(*args, expected=0, **kwargs):
    result = subprocess.run(args, text=True, capture_output=True, timeout=30, **kwargs)
    assert result.returncode == expected, result.stdout + result.stderr
    return result


@pytest.fixture
def workspace(tmp_path):
    path = tmp_path / "exercise with spaces"
    # Content-only exercises also run on a host without the container accounts.
    # The Docker tests below enable real ownership and run all seven challenges.
    SPEC["prepare"](path, ROOT / "linux-discovery/README.md", set_ownership=False)
    return path


def score(flag, stage, tmp_path):
    assert flag == SPEC["FLAGS"][stage]
    registered = next(line.split(":")[1] for line in (ROOT / "flags.sha256").read_text().splitlines()
                      if line.startswith(stage + ":"))
    assert hashlib.sha256(flag.encode()).hexdigest() == registered
    progress = tmp_path / "score.json"
    env = dict(os.environ, LABCTL_PROGRESS_FILE=str(progress))
    args = [str(ROOT / "labctl"), "--json", "submit", stage, "--flag-stdin"]
    preview = command(*args, "--dry-run", env=env, input=flag + "\n")
    assert json.loads(preview.stdout)["data"]["result"] == "valid"
    assert not progress.exists() and not Path(str(progress) + ".lock").exists()
    recorded = command(*args, env=env, input=flag + "\n")
    assert json.loads(recorded.stdout)["data"]["recorded"] is True
    repeated = command(*args, env=env, input=flag + "\n")
    assert json.loads(repeated.stdout)["data"]["result"] == "already_solved"
    wrong_id = "LD-02" if stage == "LD-01" else "LD-01"
    rejected = command(str(ROOT / "labctl"), "--json", "submit", wrong_id, "--flag-stdin",
                       env=env, input=flag + "\n", expected=1)
    assert json.loads(rejected.stdout)["error"]["code"] == "wrong_flag"
    assert json.loads(progress.read_text())["solved"] == [stage]


@pytest.mark.parametrize("stage", [stage for stage in SOLUTIONS if stage != "LD-06"])
def test_real_commands_recover_and_score_each_flag(workspace, stage, tmp_path):
    solved = command("bash", "-c", "set -euo pipefail\n" + SOLUTIONS[stage], cwd=workspace / stage,
                     env=dict(os.environ, LC_ALL="C"))
    score(solved.stdout.strip(), stage, tmp_path)


def test_quoting_alone_does_not_handle_leading_options(workspace):
    wrong = subprocess.run(["cat", "--fee handover notes--"], cwd=workspace / "LD-02",
                           text=True, capture_output=True, timeout=10)
    assert wrong.returncode != 0 and "MFANO{" not in wrong.stdout
    restored = command("bash", "-c", 'cat ./"--fee handover notes--"', cwd=workspace / "LD-02")
    assert restored.stdout.strip() == SPEC["FLAGS"]["LD-02"]


def test_hidden_entries_and_repeated_lines_need_discovery(workspace):
    assert command("ls", cwd=workspace / "LD-03/inhere").stdout == ""
    path = workspace / "LD-07/data.txt"
    distinct = command("sort", "-u", str(path)).stdout.splitlines()
    assert len(distinct) == 101
    adjacent = command("uniq", "-u", str(path)).stdout.splitlines()
    assert len(adjacent) > 1
    assert command("bash", "-c", SOLUTIONS["LD-07"], cwd=path.parent).stdout.strip() == SPEC["FLAGS"]["LD-07"]


def test_size_alone_and_nonexecutable_alone_leave_decoys(workspace):
    directory = workspace / "LD-05"
    sized = command("find", "./inhere", "-type", "f", "-size", "1033c", cwd=directory).stdout.splitlines()
    nonexec = command("find", "./inhere", "-type", "f", "-size", "1033c", "!", "-executable",
                      cwd=directory).stdout.splitlines()
    assert len(sized) > len(nonexec) > 1
    assert command("bash", "-c", "set -euo pipefail\n" + SOLUTIONS["LD-05"], cwd=directory).stdout.strip() == SPEC["FLAGS"]["LD-05"]


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
if args[0] == os.environ.get("DOCKER_TEST_FAIL"):
    sys.exit(1)
''')
    tool.chmod(0o755)
    return dict(os.environ, PATH=str(tmp_path) + os.pathsep + os.environ["PATH"], DOCKER_TEST_LOG=str(log)), log


@pytest.mark.parametrize("args,code", [(('--help',), 0), (('unknown',), 2), ((), 2)])
def test_help_and_invalid_invocations_start_nothing(launcher_env, args, code):
    env, log = launcher_env
    result = command(str(LAUNCHER), *args, expected=code, env=env)
    if code == 0:
        assert "second terminal" in result.stdout
    assert not log.exists()


def test_build_streams_only_challenge_sources(launcher_env):
    env, log = launcher_env
    command(str(LAUNCHER), "build", env=env)
    calls = [json.loads(line) for line in log.read_text().splitlines()]
    assert [call["args"][0] for call in calls] == ["info", "build"]
    assert set(calls[1]["members"]) == {
        "linux-discovery/Dockerfile", "linux-discovery/welcome.sh",
        "linux-discovery/README.md", "docs/.internal/maintainer/answer-key/linux_discovery.py",
    }


def test_launcher_limits_container_and_shares_no_host_paths(launcher_env):
    env, log = launcher_env
    master, slave = os.openpty()
    try:
        process = subprocess.Popen([str(LAUNCHER)], env=env, stdin=slave, stdout=slave, stderr=slave)
        os.close(slave)
        assert process.wait(timeout=30) == 0
    finally:
        os.close(master)
    calls = [json.loads(line) for line in log.read_text().splitlines()]
    assert calls[-1]["args"] == [
        "run", "--rm", "--interactive", "--tty", "--network", "none", "--pids-limit", "128",
        "--memory", "256m", "--cpus", "1", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
        "mfano-linux-discovery:local",
    ]


@pytest.mark.parametrize("failure", ["info", "build"])
def test_docker_failure_starts_no_shell(launcher_env, failure):
    env, log = launcher_env
    result = command(str(LAUNCHER), "build", expected=1, env=dict(env, DOCKER_TEST_FAIL=failure))
    assert all(json.loads(line)["args"][0] != "run" for line in log.read_text().splitlines())
    if failure == "info":
        assert "sudo systemctl start docker" in result.stderr


@pytest.fixture(scope="module")
def docker_image():
    if os.environ.get("MFANO_TEST_DOCKER") != "1":
        pytest.skip("Set MFANO_TEST_DOCKER=1 for real Docker discovery checks; CI enables this.")
    image = f"mfano-linux-discovery:test-{os.getpid()}"
    built = subprocess.run([str(LAUNCHER), "build"], env=dict(os.environ, MFANO_DISCOVERY_IMAGE=image),
                           text=True, capture_output=True, timeout=600)
    assert built.returncode == 0, built.stdout + built.stderr
    return image


@pytest.mark.parametrize("stage", SOLUTIONS)
def test_real_container_recovery_and_scoring(docker_image, stage, tmp_path):
    script = f'''set -euo pipefail
[[ $(id -un) == learner ]]
[[ ! -r /usr/local/lib/mfano/discovery.py ]]
cd /practice/{stage}
{SOLUTIONS[stage]}
'''
    solved = command("docker", "run", "--rm", "--interactive", "--network", "none",
                     "--cap-drop", "ALL", "--security-opt", "no-new-privileges", docker_image,
                     "bash", "--noprofile", "--norc", "-s", input=script)
    score(solved.stdout.strip(), stage, tmp_path)


def test_discovery_follows_ownership_and_keeps_all_saved_solves(tmp_path):
    metadata = json.loads((ROOT / "cli/challenges.json").read_text())
    assert [track["id"] for track in metadata["tracks"][:5]] == ["FM", "FO", "LD", "NM", "P1"]
    records = [line.split(":")[0] for line in (ROOT / "flags.sha256").read_text().splitlines()
               if line and not line.startswith("#")]
    earlier_linux = [stage for stage in records if stage.startswith(("FM-", "FO-"))]
    expected = earlier_linux + list(SOLUTIONS)
    existing = [stage for stage in records if stage not in SOLUTIONS]
    progress = tmp_path / "score.json"
    progress.write_text(json.dumps({"solved": existing, "note": "keep"}) + "\n")
    before = progress.read_bytes()
    env = dict(os.environ, LABCTL_PROGRESS_FILE=str(progress))
    result = command(str(ROOT / "labctl"), "--json", "status", "--limit", str(len(expected)), env=env)
    data = json.loads(result.stdout)["data"]
    ids = [stage["id"] for stage in data["labs"]]
    assert ids == expected
    assert data["progress"]["total"] == len(records)
    assert data["progress"]["solved"] == len(existing) and data["progress"]["remaining"] == 7
    assert data["progress"]["next"]["id"] == "LD-01"
    assert progress.read_bytes() == before
    submitted = command(str(ROOT / "labctl"), "--json", "submit", "LD-01", "--flag-stdin",
                        env=env, input=SPEC["FLAGS"]["LD-01"] + "\n")
    assert json.loads(submitted.stdout)["data"]["recorded"] is True
    assert set(json.loads(progress.read_text())["solved"]) == set(existing) | {"LD-01"}
