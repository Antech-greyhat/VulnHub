"""Exercise the Linux Bash command and its real whiptail UI using fake flags."""
import concurrent.futures
import errno
import fcntl
import hashlib
import json
import os
from pathlib import Path
import select
import shutil
import struct
import subprocess
import termios
import time

import pytest

ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT / "labctl"
FIXTURE_FLAGS = {"P1-01": "MFANO{fixture_one}", "P1-02": "MFANO{fixture_two}", "F-01": "MFANO{fixture_three}"}


@pytest.fixture
def lab(tmp_path):
    workspace = tmp_path / "lab with spaces"
    workspace.mkdir()
    lines = ["# synthetic test flags"]
    for stage, flag in FIXTURE_FLAGS.items():
        category = "Forensics (image)" if stage.startswith("F-") else "A01 Broken Access Control"
        lines.append(f"{stage}:{hashlib.sha256(flag.encode()).hexdigest()}:{category}:Easy")
    (workspace / "flags.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
    # The CLI needs no tokens; keep host secrets out of child processes and reports.
    env = {key: os.environ[key] for key in ("PATH", "HOME", "LANG", "LC_ALL") if key in os.environ}
    env.update(LABCTL_ROOT=str(workspace), TERM="xterm-256color", PYTHONDONTWRITEBYTECODE="1")
    return workspace, env


def run_cli(lab, *args, flag=None, expected=0):
    workspace, env = lab
    result = subprocess.run(
        [str(CLI), "--json", *args], input=flag, text=True, capture_output=True,
        cwd=workspace.parent, env=env, timeout=20,
    )
    assert result.returncode == expected, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    assert not result.stderr, result.stderr
    return payload


def submit(lab, stage, **kwargs):
    return run_cli(lab, "submit", stage, "--flag-stdin", flag=FIXTURE_FLAGS[stage] + "\n", **kwargs)


def progress_file(lab):
    return lab[0] / ".labprogress.json"


def test_doctor_and_discovery_are_offline(lab):
    data = run_cli(lab, "doctor")["data"]
    assert data["mode"] == "offline" and data["network_required"] is False
    assert data["auth"] == {"required": False, "source": "not_required"}
    assert data["challenge_count"] == 3 and data["ready"] is True
    tracks = run_cli(lab, "tracks")["data"]["tracks"]
    assert [(track["id"], track["total"]) for track in tracks] == [("P1", 2), ("F", 1)]
    assert not progress_file(lab).exists()


def test_selected_challenge_is_required(lab):
    result = run_cli(lab, "submit", "P1-02", "--flag-stdin", flag=FIXTURE_FLAGS["P1-01"], expected=1)
    assert result["error"]["code"] == "wrong_flag"
    assert not progress_file(lab).exists()


def test_submission_updates_counts_and_repeat_is_idempotent(lab):
    result = submit(lab, "P1-01")["data"]
    assert result["result"] == "solved" and result["recorded"] is True
    assert result["progress"]["solved"] == 1 and result["progress"]["remaining"] == 2
    assert result["progress"]["next"]["id"] == "P1-02"
    original = progress_file(lab).stat()
    repeat = submit(lab, "P1-01")["data"]
    assert repeat["result"] == "already_solved" and repeat["recorded"] is False
    assert progress_file(lab).stat().st_mtime_ns == original.st_mtime_ns
    assert json.loads(progress_file(lab).read_text())["solved"] == ["P1-01"]
    assert progress_file(lab).stat().st_mode & 0o777 == 0o600


def test_dry_run_creates_no_progress_or_lock(lab):
    result = run_cli(lab, "submit", "P1-01", "--flag-stdin", "--dry-run", flag=FIXTURE_FLAGS["P1-01"])["data"]
    assert result["result"] == "valid" and result["recorded"] is False and result["dry_run"] is True
    assert sorted(path.name for path in lab[0].iterdir()) == ["flags.sha256"]


def test_submit_trims_whitespace_but_preserves_case(lab):
    run_cli(lab, "submit", "p1-01", "--flag-stdin", flag=" \t" + FIXTURE_FLAGS["P1-01"] + "\r\n")
    run_cli(lab, "submit", "P1-02", "--flag-stdin", flag=FIXTURE_FLAGS["P1-02"].upper(), expected=1)


def test_solved_unsolved_filter_and_pagination(lab):
    submit(lab, "P1-01")
    solved = run_cli(lab, "solved")["data"]
    assert [stage["id"] for stage in solved["labs"]] == ["P1-01"]
    unsolved = run_cli(lab, "unsolved", "--track", "p1")["data"]
    assert [stage["id"] for stage in unsolved["labs"]] == ["P1-02"]
    first = run_cli(lab, "labs", "--limit", "1")["data"]
    assert first["next_offset"] == 1 and first["total"] == 3
    second = run_cli(lab, "labs", "--limit", "1", "--offset", "1")["data"]
    assert second["labs"][0]["id"] == "P1-02" and second["next_offset"] == 2
    empty = run_cli(lab, "labs", "--offset", "99")["data"]
    assert empty["labs"] == [] and empty["next_offset"] is None


def test_resolve_names_and_clues_without_hashes(lab):
    resolved = run_cli(lab, "resolve", "private report forms")["data"]["stage"]
    assert resolved["id"] == "P1-01" and "hash" not in resolved and "hint" not in resolved
    clue = run_cli(lab, "hints", "f-01")["data"]["stage"]
    assert clue["hint"] and clue["evidence"] == "forensics/evidence/01_noticeboard.png"
    for resource in ("stages", "progress", "hints"):
        payload = run_cli(lab, "inspect", resource)
        encoded = json.dumps(payload)
        assert "MFANO{" not in encoded
        for flag in FIXTURE_FLAGS.values():
            assert hashlib.sha256(flag.encode()).hexdigest() not in encoded


def test_legacy_progress_and_extra_fields_are_preserved(lab):
    progress_file(lab).write_text(json.dumps({"solved": ["P1-01", "P1-01", "retired-stage"], "note": "fixture"}))
    original = progress_file(lab).read_bytes()
    assert run_cli(lab, "status")["data"]["progress"]["solved"] == 1
    assert progress_file(lab).read_bytes() == original
    submit(lab, "P1-02")
    saved = json.loads(progress_file(lab).read_text())
    assert saved == {"solved": ["P1-01", "retired-stage", "P1-02"], "note": "fixture"}


@pytest.mark.parametrize("contents", ["{", "null", "[]", '{"solved":"P1-01"}', '{"solved":[1]}', '{"solved":[]}\n{"solved":[]}'])
def test_corrupt_progress_is_never_overwritten(lab, contents):
    progress_file(lab).write_text(contents)
    result = submit(lab, "P1-01", expected=1)
    assert result["error"]["code"] == "invalid_progress"
    assert progress_file(lab).read_text() == contents
    doctor = run_cli(lab, "doctor", expected=1)["data"]
    assert doctor["ready"] is False and doctor["issues"]


def test_progress_override_and_symlink_protection(lab):
    alternate = lab[0].parent / "alternate-score.json"
    lab[1]["LABCTL_PROGRESS_FILE"] = str(alternate)
    submit(lab, "P1-01")
    assert alternate.exists() and not progress_file(lab).exists()
    link = lab[0] / "linked-score.json"
    link.symlink_to(alternate)
    original = alternate.read_bytes()
    lab[1]["LABCTL_PROGRESS_FILE"] = str(link)
    result = submit(lab, "P1-02", expected=1)
    assert result["error"]["code"] == "unsafe_progress"
    assert alternate.read_bytes() == original and link.is_symlink()


def test_concurrent_submissions_do_not_lose_solves(lab):
    stages = list(FIXTURE_FLAGS) * 4
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(lambda stage: submit(lab, stage), stages))
    assert all(result["ok"] for result in results)
    saved = json.loads(progress_file(lab).read_text())["solved"]
    assert len(saved) == 3 and set(saved) == set(FIXTURE_FLAGS)
    summary = run_cli(lab, "status")["data"]["progress"]
    assert summary["solved"] == 3 and summary["remaining"] == 0 and summary["next"] is None
    assert not list(lab[0].glob(".labprogress.json.tmp.*"))


@pytest.mark.parametrize("args,code", [
    (("not-a-command",), "unknown_command"),
    (("resolve", "no-such-challenge"), "unknown_challenge"),
    (("labs", "--track", "NOPE"), "unknown_track"),
    (("labs", "--limit", "0"), "invalid_limit"),
    (("labs", "--limit", "1001"), "invalid_limit"),
    (("labs", "--offset", "-1"), "invalid_offset"),
    (("labs", "--state", "pending"), "invalid_state"),
    (("labs", "--track"), "missing_option_value"),
    (("status", "--dry-run"), "invalid_option"),
    (("submit", "P1-01", "MFANO{should_not_be_argv}"), "invalid_arguments"),
    (("submit", "P1-01"), "missing_flag"),
    (("inspect", "hashes"), "invalid_resource"),
    (("menu",), "interactive_command"),
])
def test_json_usage_errors(lab, args, code):
    result = run_cli(lab, *args, expected=2)
    assert result["ok"] is False and result["error"]["code"] == code
    assert "MFANO{" not in json.dumps(result)


def test_empty_catalog(lab):
    (lab[0] / "flags.sha256").write_text("# no stages\n")
    assert run_cli(lab, "status")["data"]["progress"] == {"solved": 0, "total": 0, "remaining": 0, "next": None}
    assert run_cli(lab, "tracks")["data"]["tracks"] == []


@pytest.mark.parametrize("damage", ["P1-01:not-a-hash:A01:Easy\n", "duplicate"])
def test_bad_hash_table_preserves_existing_progress(lab, damage):
    submit(lab, "P1-01")
    original = progress_file(lab).read_bytes()
    flags_path = lab[0] / "flags.sha256"
    if damage == "duplicate":
        damage = flags_path.read_text() + flags_path.read_text().splitlines()[1] + "\n"
    flags_path.write_text(damage)
    result = submit(lab, "P1-02", expected=1)
    assert result["error"]["code"] == "invalid_flags"
    assert progress_file(lab).read_bytes() == original


def stub_tool(lab, name, script):
    tools = lab[0].parent / "tools"
    tools.mkdir(exist_ok=True)
    path = tools / name
    path.write_text("#!/usr/bin/env bash\n" + script)
    path.chmod(0o755)
    lab[1]["PATH"] = str(tools) + os.pathsep + os.environ["PATH"]
    return path


@pytest.mark.parametrize("plugin", [True, False])
def test_compose_builders_dry_run_and_reset_confirmation(lab, plugin):
    log = lab[0].parent / "compose-args.txt"
    lab[1]["LABCTL_TEST_COMPOSE_LOG"] = str(log)
    stub_tool(lab, "docker", 'if [[ "$1 $2" == "compose version" ]]; then exit ' + ("0" if plugin else "1") + '; fi\nprintf "%s\\n" "$@" >> "$LABCTL_TEST_COMPOSE_LOG"\n')
    stub_tool(lab, "docker-compose", 'printf "%s\\n" "$@" >> "$LABCTL_TEST_COMPOSE_LOG"\n')
    prefix = ["docker", "compose"] if plugin else ["docker-compose"]
    for command, suffix in (("start", ["up", "-d", "--build"]), ("stop", ["down"]), ("reset", ["exec", "-T", "web", "python", "seed.py"]), ("shell", ["exec", "web", "bash"])):
        data = run_cli(lab, command, "--dry-run")["data"]
        assert data["argv"] == prefix + ["--project-directory", str(lab[0]), "-f", str(lab[0] / "docker-compose.yml")] + suffix
    assert not log.exists()
    assert run_cli(lab, "reset", expected=2)["error"]["code"] == "confirmation_required"
    assert not log.exists()
    run_cli(lab, "reset", "--yes")
    assert log.read_text().splitlines()[-5:] == ["exec", "-T", "web", "python", "seed.py"]


@pytest.mark.parametrize("vulnerable", [True, False])
def test_audit_requires_a_real_requests_finding(lab, vulnerable):
    report = {"dependencies": [{"name": "requests", "version": "2.19.1", "vulns": [{"id": "fixture-advisory"}] if vulnerable else []}]}
    stub_tool(lab, "pip-audit", "cat <<'REPORT'\n" + json.dumps(report) + "\nREPORT\nexit " + ("1" if vulnerable else "0") + "\n")
    data = run_cli(lab, "audit")["data"]
    if vulnerable:
        expected_hash = next(line.split(":")[1] for line in (ROOT / "flags.sha256").read_text().splitlines() if line.startswith("P5-03:"))
        assert hashlib.sha256(data["flag"].encode()).hexdigest() == expected_hash
    else:
        assert data["flag"] is None


def test_audit_failure_does_not_reveal_a_flag(lab):
    stub_tool(lab, "pip-audit", "printf '%s\\n' 'requests: advisory service failed'\nexit 1\n")
    result = run_cli(lab, "audit", expected=1)
    assert result["error"]["code"] == "audit_failed" and "MFANO{" not in json.dumps(result)


def test_install_from_another_directory(lab):
    prefix = lab[0].parent / "installed"
    subprocess.run(["make", "install-local", f"PREFIX={prefix}"], cwd=ROOT, check=True, capture_output=True)
    installed = prefix / "bin" / "labctl"
    result = subprocess.run([str(installed), "--json", "doctor"], env=lab[1], cwd=lab[0].parent, text=True, capture_output=True, check=True)
    assert json.loads(result.stdout)["data"]["challenge_count"] == 3
    assert installed.resolve() == CLI
    # A second install is safe; a different existing command is preserved.
    subprocess.run(["make", "install-local", f"PREFIX={prefix}"], cwd=ROOT, check=True, capture_output=True)
    other = lab[0].parent / "other-install" / "bin"
    other.mkdir(parents=True)
    command = other / "labctl"
    command.write_text("existing command\n")
    refused = subprocess.run(["make", "install-local", f"BINDIR={other}"], cwd=ROOT, text=True, capture_output=True)
    assert refused.returncode != 0 and command.read_text() == "existing command\n"


def test_public_metadata_matches_registered_challenges():
    metadata = json.loads((ROOT / "cli" / "challenges.json").read_text())
    ids = {line.split(":")[0] for line in (ROOT / "flags.sha256").read_text().splitlines() if line and not line.startswith("#")}
    assert set(metadata["challenges"]) == ids and len(ids) == 73
    assert all(stage["title"] and stage["hint"] for stage in metadata["challenges"].values())
    assert "MFANO{" not in json.dumps(metadata)


def test_no_auth_doctor_with_missing_jq(lab):
    tools = lab[0].parent / "minimal-tools"
    tools.mkdir()
    for name in ("bash", "readlink", "dirname"):
        (tools / name).symlink_to(shutil.which(name))
    lab[1]["PATH"] = str(tools)
    result = run_cli(lab, "doctor", expected=1)
    assert result["error"]["code"] == "missing_dependency"


def test_doctor_reports_missing_menu_dependency_without_requiring_auth(lab):
    tools = lab[0].parent / "offline-tools"
    tools.mkdir()
    for name in ("bash", "readlink", "dirname", "jq", "sha256sum", "flock"):
        (tools / name).symlink_to(shutil.which(name))
    lab[1]["PATH"] = str(tools)
    data = run_cli(lab, "doctor")["data"]
    assert data["menu_available"] is False and data["ready"] is True
    assert data["auth"]["required"] is False


class Terminal:
    """Real PTY: exercise whiptail's dialogs and keyboard handling, not a mock."""

    def __init__(self, lab, *args):
        master, slave = os.openpty()
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 28, 110, 0, 0))

        def attach_terminal():
            os.setsid()
            fcntl.ioctl(slave, termios.TIOCSCTTY, 0)

        self.process = subprocess.Popen([str(CLI), *args], stdin=slave, stdout=slave, stderr=slave,
            env=lab[1], cwd=lab[0].parent, preexec_fn=attach_terminal)
        os.close(slave)
        self.master = master
        self.output = bytearray()
        self.cursor = 0

    def expect(self, text):
        target = text.encode()
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            position = self.output.find(target, self.cursor)
            if position >= 0:
                self.cursor = position + len(target)
                return
            if select.select([self.master], [], [], 0.1)[0]:
                try:
                    chunk = os.read(self.master, 65536)
                except OSError as exc:
                    if exc.errno == errno.EIO:
                        break
                    raise
                if not chunk:
                    break
                self.output.extend(chunk)
        raise AssertionError(f"Terminal did not show {text!r}; process={self.process.poll()}; screen={self.output[-3000:]!r}")

    def send(self, keys):
        os.write(self.master, keys.encode())

    def close(self):
        if self.process.poll() is None:
            self.process.terminate()
        self.process.wait(timeout=5)
        os.close(self.master)


@pytest.mark.skipif(shutil.which("whiptail") is None, reason="whiptail is needed for the Linux UI")
def test_real_menu_submit_hidden_flag_and_back_navigation(lab):
    terminal = Terminal(lab)
    try:
        terminal.expect("MFANO // Linux lab terminal")
        terminal.send("\r")
        terminal.expect("Choose a lab track")
        terminal.send("\r")
        terminal.expect("Choose a challenge // ALL")
        terminal.send("\r")
        terminal.expect("Submit flag // P1-01")
        terminal.send(FIXTURE_FLAGS["P1-01"] + "\r")
        terminal.expect("Flag accepted")
        assert json.loads(progress_file(lab).read_text())["solved"] == ["P1-01"]
        assert FIXTURE_FLAGS["P1-01"].encode() not in terminal.output
        terminal.send("\r")
        terminal.expect("Choose a challenge // ALL")
        terminal.send("\x1b")
        terminal.expect("Choose a lab track")
        terminal.send("\x1b")
        terminal.expect("MFANO // Linux lab terminal")
        terminal.send("\x1b")
        assert terminal.process.wait(timeout=5) == 0
    finally:
        terminal.close()


@pytest.mark.skipif(shutil.which("whiptail") is None, reason="whiptail is needed for the Linux UI")
def test_real_menu_flag_cancel_does_not_record(lab):
    terminal = Terminal(lab)
    try:
        terminal.expect("MFANO // Linux lab terminal")
        terminal.send("\r")
        terminal.expect("Choose a lab track")
        terminal.send("\r")
        terminal.expect("Choose a challenge // ALL")
        terminal.send("\r")
        terminal.expect("Submit flag // P1-01")
        terminal.send("\x1b")
        terminal.expect("Choose a challenge // ALL")
        assert not progress_file(lab).exists()
    finally:
        terminal.close()


@pytest.mark.skipif(shutil.which("whiptail") is None, reason="whiptail is needed for the Linux UI")
def test_direct_submit_releases_lock_before_result_dialog(lab):
    terminal = Terminal(lab, "submit", "P1-01")
    try:
        terminal.expect("Submit flag // P1-01")
        terminal.send(FIXTURE_FLAGS["P1-01"] + "\r")
        terminal.expect("Flag accepted")
        result = submit(lab, "P1-02")["data"]
        assert result["progress"]["solved"] == 2
        terminal.send("\r")
        assert terminal.process.wait(timeout=5) == 0
    finally:
        terminal.close()


@pytest.mark.skipif(shutil.which("whiptail") is None, reason="whiptail is needed for the Linux UI")
def test_real_menu_gentle_clue_navigation(lab):
    terminal = Terminal(lab)
    try:
        terminal.expect("MFANO // Linux lab terminal")
        terminal.send("\x1b[B" * 4 + "\r")
        terminal.expect("Choose a lab track")
        terminal.send("\r")
        terminal.expect("Choose a challenge // ALL")
        terminal.send("\x1b[B" * 2 + "\r")
        terminal.expect("Gentle clue // F-01")
        terminal.expect("01_noticeboard.png")
        assert not progress_file(lab).exists()
        assert "MFANO{".encode() not in terminal.output
        terminal.send("\r")
        terminal.expect("Choose a challenge // ALL")
    finally:
        terminal.close()
