"""Validate Nmap evidence and solve the real training services (spoilers)."""
import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import threading
from xml.etree import ElementTree as ET

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
LAUNCHER = ROOT / "nmap-enumeration/lab"
SPEC = runpy.run_path(str(ROOT / "docs/.internal/maintainer/answer-key/nmap_enumeration.py"))
TARGET = runpy.run_path(str(ROOT / "nmap-enumeration/target.py"))
SOLUTIONS = {
    "NM-01": ["-sn", "172.30.77.0/28"],
    "NM-02": ["-Pn", "-sT", "-p", "21,22,80,443,9999", "--reason", SPEC["PORTAL"]],
    "NM-03": ["-sS", "-p-", "-T3", "--open", "--reason", SPEC["PORTAL"]],
    "NM-04": ["-sV", "--version-light", "-p", "21,22,80,443", SPEC["PORTAL"]],
    "NM-05": ["-sU", "-sV", "-p", "53", "--script", "dns-nsid", SPEC["PORTAL"]],
    "NM-06": ["-sV", "-p", "80", "--script", "http-title,http-headers", SPEC["PORTAL"]],
    "NM-07": ["-sV", "-p", "80", "--script", "http-robots.txt,http-methods", "--script-args",
              "http-methods.url-path=/staff-notices/", SPEC["PORTAL"]],
    "NM-08": ["-sV", "-p", "443", "--script", "ssl-cert", "-v", SPEC["PORTAL"]],
    "NM-09": ["-sV", "-p", "22", "--script", "ssh-hostkey", SPEC["PORTAL"]],
    "NM-10": ["-sV", "-p", "21", "--script", "ftp-anon", SPEC["PORTAL"]],
    "NM-11": ["-sS", "-p-", "--open", "-sV", "--script", "http-title,http-headers", SPEC["ARCHIVE"]],
    "NM-12": ["-sS", "-sU", "-sV", "-p", "T:21,22,53,80,443,31337,U:53", "--script",
              "http-title,http-headers,ssl-cert,ssh-hostkey,dns-nsid", SPEC["PORTAL"]],
}


def command(*args, expected=0, timeout=40, **kwargs):
    result = subprocess.run(args, text=True, capture_output=True, timeout=timeout, **kwargs)
    assert result.returncode == expected, result.stdout + result.stderr
    return result


def score(flag, stage, tmp_path):
    assert flag == SPEC["FLAGS"][stage]
    progress = tmp_path / "score.json"
    env = dict(os.environ, LABCTL_PROGRESS_FILE=str(progress))
    args = [str(ROOT / "labctl"), "--json", "submit", stage, "--flag-stdin"]
    preview = command(*args, "--dry-run", input=flag + "\n", env=env)
    assert json.loads(preview.stdout)["data"]["result"] == "valid"
    assert not progress.exists() and not Path(str(progress) + ".lock").exists()
    assert json.loads(command(*args, input=flag + "\n", env=env).stdout)["data"]["recorded"] is True
    assert json.loads(command(*args, input=flag + "\n", env=env).stdout)["data"]["result"] == "already_solved"
    wrong_id = "NM-02" if stage == "NM-01" else "NM-01"
    rejected = command(str(ROOT / "labctl"), "--json", "submit", wrong_id, "--flag-stdin",
                       input=flag + "\n", env=env, expected=1)
    assert json.loads(rejected.stdout)["error"]["code"] == "wrong_flag"
    assert json.loads(progress.read_text())["solved"] == [stage]


def sample_report():
    root = ET.Element("nmaprun", scanner="nmap", args="nmap -n -sT -p21,22,80,443,9999 -oX scan.xml")
    ET.SubElement(root, "scaninfo", type="connect", protocol="tcp", services="21,22,80,443,9999")
    host = ET.SubElement(root, "host")
    ET.SubElement(host, "status", state="up")
    ET.SubElement(host, "address", addr=SPEC["PORTAL"], addrtype="ipv4")
    ports = ET.SubElement(host, "ports")
    for number, name, product, version in (
        (21, "ftp", "vsftpd", "3.0.3"), (22, "ssh", "OpenSSH", "9.2p1"),
        (80, "http", "BaseHTTPServer", "0.6"), (443, "http", "BaseHTTPServer", "0.6"),
    ):
        port = ET.SubElement(ports, "port", protocol="tcp", portid=str(number))
        ET.SubElement(port, "state", state="open", reason="syn-ack")
        attributes = dict(name=name, product=product, version=version, method="probed")
        if number == 443:
            attributes["tunnel"] = "ssl"
        ET.SubElement(port, "service", **attributes)
    aggregate = ET.SubElement(ports, "extraports", state="closed", count="1")
    ET.SubElement(aggregate, "extrareasons", reason="conn-refused", count="1", proto="tcp", ports="9999")
    ET.SubElement(ET.SubElement(root, "runstats"), "finished", exit="success")
    return root


def encoded(root):
    return b'<?xml version="1.0"?>\n<!DOCTYPE nmaprun>\n' + ET.tostring(root)


def test_compressed_closed_ports_work_across_nmap_xml_versions():
    root = sample_report()
    assert SPEC["check"]("NM-02", encoded(root)) == SPEC["FLAGS"]["NM-02"]
    reason = root.find("host/ports/extraports/extrareasons")
    reason.attrib.pop("ports")
    reason.attrib.pop("proto")
    assert SPEC["check"]("NM-02", encoded(root)) == SPEC["FLAGS"]["NM-02"]
    root.find("scaninfo").set("type", "syn")
    with pytest.raises(SPEC["EvidenceError"], match="connect"):
        SPEC["check"]("NM-02", encoded(root))


@pytest.mark.parametrize("data", [
    b"Nmap scan report for 172.30.77.10",
    b"<nmaprun scanner='nmap'>",
    b"<nmaprun scanner='nmap'><runstats><finished exit='error'/></runstats></nmaprun>",
    b"<!DOCTYPE nmaprun SYSTEM 'file:///nonexistent'><nmaprun/>",
    b"<!DOCTYPE nmaprun [<!ENTITY value 'test'>]><nmaprun/>",
])
def test_bad_or_incomplete_reports_reveal_no_flag(data):
    with pytest.raises(SPEC["EvidenceError"]):
        SPEC["check"]("NM-02", data)


def test_foreign_hosts_and_oversized_reports_are_rejected():
    root = sample_report()
    root.find("host/address").set("addr", "192.0.2.1")
    with pytest.raises(SPEC["EvidenceError"], match="internal"):
        SPEC["check"]("NM-02", encoded(root))
    with pytest.raises(SPEC["EvidenceError"], match="2 MiB"):
        SPEC["check"]("NM-02", b"x" * (SPEC["MAX_XML_BYTES"] + 1))
    root.find("host/address").set("addr", SPEC["PORTAL"])
    root.find("scaninfo").set("services", "1-999999999")
    with pytest.raises(SPEC["EvidenceError"], match="port range"):
        SPEC["check"]("NM-02", encoded(root))


def test_port_name_guesses_do_not_count_as_service_probes():
    root = sample_report()
    assert SPEC["check"]("NM-04", encoded(root)) == SPEC["FLAGS"]["NM-04"]
    root.find("host/ports/port/service").set("method", "table")
    with pytest.raises(SPEC["EvidenceError"], match="version detection"):
        SPEC["check"]("NM-04", encoded(root))


def test_udp_silence_and_script_errors_do_not_count_as_findings():
    root = sample_report()
    info = root.find("scaninfo")
    info.attrib.update(type="udp", protocol="udp", services="53")
    ports = root.find("host/ports")
    ports.clear()
    port = ET.SubElement(ports, "port", protocol="udp", portid="53")
    state = ET.SubElement(port, "state", state="open")
    ET.SubElement(port, "service", name="domain", method="probed")
    script = ET.SubElement(port, "script", id="dns-nsid", output="bind.version: dnsmasq-2.90")
    assert SPEC["check"]("NM-05", encoded(root)) == SPEC["FLAGS"]["NM-05"]
    state.set("state", "open|filtered")
    with pytest.raises(SPEC["EvidenceError"], match="confirmed open"):
        SPEC["check"]("NM-05", encoded(root))
    state.set("state", "open")
    script.set("output", "ERROR: no reply")
    with pytest.raises(SPEC["EvidenceError"], match="successful finding"):
        SPEC["check"]("NM-05", encoded(root))


def test_new_track_preserves_all_previous_solves_and_registers_hashes(tmp_path):
    metadata = json.loads((ROOT / "cli/challenges.json").read_text())
    assert [track["id"] for track in metadata["tracks"][:5]] == ["FM", "FO", "LD", "NM", "P1"]
    records = {parts[0]: parts[1] for line in (ROOT / "flags.sha256").read_text().splitlines()
               if line and not line.startswith("#") for parts in [line.split(":")]}
    assert records.keys() == metadata["challenges"].keys()
    for stage, flag in SPEC["FLAGS"].items():
        assert records[stage] == hashlib.sha256(flag.encode()).hexdigest()
        assert metadata["challenges"][stage]["evidence"] == "nmap-enumeration/README.md"
    previous = [stage for stage in records if stage not in SPEC["FLAGS"]]
    progress = tmp_path / "score.json"
    progress.write_text(json.dumps({"solved": previous, "note": "keep"}) + "\n")
    before = progress.read_bytes()
    env = dict(os.environ, LABCTL_PROGRESS_FILE=str(progress))
    data = json.loads(command(str(ROOT / "labctl"), "--json", "status", "--track", "NM", env=env).stdout)["data"]
    assert [stage["id"] for stage in data["labs"]] == list(SPEC["FLAGS"])
    assert data["progress"]["total"] == len(records) and data["progress"]["solved"] == len(previous)
    assert data["progress"]["remaining"] == 12 and data["progress"]["next"]["id"] == "NM-01"
    assert progress.read_bytes() == before
    command(str(ROOT / "labctl"), "--json", "submit", "NM-01", "--flag-stdin",
            input=SPEC["FLAGS"]["NM-01"] + "\n", env=env)
    stored = json.loads(progress.read_text())
    assert set(stored["solved"]) == set(previous) | {"NM-01"} and stored["note"] == "keep"
    for source in (ROOT / "nmap-enumeration").rglob("*"):
        if source.is_file():
            assert not any(flag in source.read_text() for flag in SPEC["FLAGS"].values())


@pytest.fixture
def launcher_env(tmp_path):
    log = tmp_path / "docker.jsonl"
    script = "#!" + sys.executable + "\n" + '''import json, os, sys, tarfile
args = sys.argv[1:]
if args[:2] == ["compose", "version"] and os.environ.get("FAKE_NO_PLUGIN"):
    sys.exit(1)
entry = {"args": args, "binary": os.path.basename(sys.argv[0])}
if args[0] == "build":
    with tarfile.open(fileobj=sys.stdin.buffer, mode="r|*") as stream:
        entry["members"] = [member.name for member in stream]
if "/opt/mfano/check.py" in args:
    entry["stdin"] = sys.stdin.read()
with open(os.environ["DOCKER_TEST_LOG"], "a") as stream:
    stream.write(json.dumps(entry) + "\\n")
if os.environ.get("DOCKER_TEST_FAIL") in args:
    sys.exit(1)
if "cat" in args:
    sys.stdout.write("fake XML evidence")
'''
    for name in ("docker", "docker-compose"):
        path = tmp_path / name
        path.write_text(script)
        path.chmod(0o755)
    return dict(os.environ, PATH=str(tmp_path) + os.pathsep + os.environ["PATH"], DOCKER_TEST_LOG=str(log)), log


@pytest.mark.parametrize("args,code", [
    (("--help",), 0), (("unknown",), 2), ((), 2),
    (("check", "NM-13", "scans/01.xml"), 2),
    (("check", "NM-01", "scans/../private.xml"), 2),
    (("check", "NM-01", "/tmp/01.xml"), 2),
])
def test_help_and_invalid_invocations_run_no_docker(launcher_env, args, code):
    env, log = launcher_env
    result = command(str(LAUNCHER), *args, env=env, expected=code)
    if code == 0:
        assert "second HOST terminal" in result.stdout
    assert not log.exists()


def test_build_sends_only_training_sources(launcher_env):
    env, log = launcher_env
    command(str(LAUNCHER), "build", env=env)
    builds = [entry for entry in map(json.loads, log.read_text().splitlines()) if entry["args"][0] == "build"]
    assert len(builds) == 2
    assert set(builds[0]["members"]) == {
        "nmap-enumeration/Dockerfile.scanner", "nmap-enumeration/welcome.sh", "nmap-enumeration/README.md",
    }
    assert set(builds[1]["members"]) == {
        "nmap-enumeration/Dockerfile.target", "nmap-enumeration/target.py", "nmap-enumeration/config",
        "nmap-enumeration/config/dnsmasq.conf", "nmap-enumeration/config/sshd_config",
        "nmap-enumeration/config/vsftpd.conf", "docs/.internal/maintainer/answer-key/nmap_enumeration.py",
    }


def test_checker_reads_scanner_report_and_streams_it_to_target(launcher_env):
    env, log = launcher_env
    command(str(LAUNCHER), "check", "NM-06", "scans/06.xml", env=env)
    calls = list(map(json.loads, log.read_text().splitlines()))
    reads = [call for call in calls if "cat" in call["args"]]
    checks = [call for call in calls if "/opt/mfano/check.py" in call["args"]]
    assert reads[0]["args"][-5:] == ["-T", "scanner", "cat", "--", "scans/06.xml"]
    assert checks[0]["args"][-7:] == ["-T", "target", "python3", "-B", "/opt/mfano/check.py", "check", "NM-06"]
    assert checks[0]["stdin"] == "fake XML evidence"


def test_stop_keeps_reports_and_old_compose_is_supported(launcher_env):
    env, log = launcher_env
    command(str(LAUNCHER), "stop", env=dict(env, FAKE_NO_PLUGIN="1"))
    calls = list(map(json.loads, log.read_text().splitlines()))
    assert calls[-1]["binary"] == "docker-compose" and calls[-1]["args"][-1] == "stop"
    assert all("down" not in call["args"] and "--volumes" not in call["args"] for call in calls)


@pytest.mark.parametrize("failure", ["info", "build", "up"])
def test_failed_docker_or_build_does_not_start_services(launcher_env, failure):
    env, log = launcher_env
    command(str(LAUNCHER), "start", env=dict(env, DOCKER_TEST_FAIL=failure), expected=1)
    calls = list(map(json.loads, log.read_text().splitlines()))
    if failure == "up":
        assert sum("up" in call["args"] for call in calls) == 1
        assert calls[-1]["args"][-4:] == ["logs", "--no-color", "target", "archive"]
    else:
        assert all("up" not in call["args"] for call in calls)


def test_network_is_internal_and_has_no_host_bind_mounts_or_ports():
    config = yaml.safe_load((ROOT / "nmap-enumeration/compose.yml").read_text())
    assert config["networks"]["practice"]["internal"] is True
    assert config["networks"]["practice"]["ipam"]["config"] == [{"subnet": str(SPEC["NETWORK"])}]
    services = config["services"]
    assert set(services) == {"scanner", "target", "archive"}
    for service in services.values():
        assert "ports" not in service and set(service["networks"]) == {"practice"}
        assert service["cap_drop"] == ["ALL"]
        assert service["security_opt"] == ["no-new-privileges:true"]
    assert services["scanner"]["cap_add"] == ["NET_RAW"]
    assert services["scanner"]["volumes"] == ["scans:/practice/scans"]
    assert "volumes" not in services["target"] and "volumes" not in services["archive"]
    assert services["target"]["read_only"] is True and services["archive"]["read_only"] is True


@pytest.fixture
def local_http():
    server = TARGET["make_http_server"]("portal", "127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_port
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_real_nmap_http_scripts_read_the_service(local_http, tmp_path):
    if shutil.which("nmap") is None:
        pytest.skip("Install nmap for local protocol checks; CI installs it.")
    report = tmp_path / "http.xml"
    command("nmap", "-n", "-Pn", "-sT", "-sV", "--version-light", "-p", str(local_http),
            "--script", "http-title,http-headers,http-robots.txt,http-methods", "--script-args",
            "http-methods.url-path=/staff-notices/", "-oX", str(report), "127.0.0.1", timeout=90)
    port = ET.parse(report).find("host/ports/port")
    assert port.find("service").get("name") == "http" and port.find("service").get("method") == "probed"
    scripts = {script.get("id"): script.get("output") for script in port.findall("script")}
    assert TARGET["PORTAL_TITLE"] in scripts["http-title"]
    assert "X-Lab-Role: portal" in scripts["http-headers"]
    assert "/staff-notices/" in scripts["http-robots.txt"] and "/archive-transfer/" in scripts["http-robots.txt"]
    assert "GET" in scripts["http-methods"] and "OPTIONS" in scripts["http-methods"]
    with pytest.raises(SPEC["EvidenceError"], match="internal"):
        SPEC["check"]("NM-06", report.read_bytes())


def test_real_nmap_reads_the_synthetic_tls_certificate(tmp_path):
    if shutil.which("nmap") is None or shutil.which("openssl") is None:
        pytest.skip("Install nmap and openssl for local TLS checks; CI provides both.")
    certificate, key = tmp_path / "fake-training.crt", tmp_path / "fake-training.key"
    command("openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "1",
            "-keyout", str(key), "-out", str(certificate), "-subj", "/CN=portal.mfano.test",
            "-addext", "subjectAltName=DNS:portal.mfano.test,DNS:archive.mfano.test")
    server = TARGET["make_http_server"]("portal", "127.0.0.1", 0, certificate, key)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    report = tmp_path / "tls.xml"
    try:
        command("nmap", "-n", "-Pn", "-sT", "-sV", "--version-light", "-p", str(server.server_port),
                "--script", "ssl-cert", "-oX", str(report), "127.0.0.1", timeout=90)
        port = ET.parse(report).find("host/ports/port")
        assert port.find("service").get("tunnel") == "ssl"
        text = port.find("script[@id='ssl-cert']").get("output")
        assert "portal.mfano.test" in text and "archive.mfano.test" in text
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.fixture(scope="module")
def live_lab():
    if os.environ.get("MFANO_TEST_NMAP") != "1":
        pytest.skip("Set MFANO_TEST_NMAP=1 for real Docker Nmap checks; CI enables this.")
    env = dict(os.environ, MFANO_NMAP_PROJECT=f"mfano-nmap-test-{os.getpid()}",
               MFANO_NMAP_SCANNER_IMAGE=f"mfano-nmap-scanner:test-{os.getpid()}",
               MFANO_NMAP_TARGET_IMAGE=f"mfano-nmap-target:test-{os.getpid()}")
    try:
        command(str(LAUNCHER), "start", env=env, timeout=900)
        yield env
    finally:
        # The dedicated project is stopped; its reports and images are retained.
        command(str(LAUNCHER), "stop", env=env, timeout=60)


def live_compose(env, *args, timeout=180):
    if subprocess.run(["docker", "compose", "version"], capture_output=True, env=env).returncode == 0:
        prefix = ["docker", "compose"]
    else:
        prefix = ["docker-compose"]
    return command(*prefix, "--project-name", env["MFANO_NMAP_PROJECT"],
                   "--file", str(ROOT / "nmap-enumeration/compose.yml"), *args, env=env, timeout=timeout)


@pytest.mark.parametrize("stage", SOLUTIONS)
def test_real_docker_scan_reveals_and_scores_each_flag(live_lab, stage, tmp_path):
    basename = "scans/" + stage.lower()
    output = ["-oA", basename] if stage == "NM-12" else ["-oX", basename + ".xml"]
    live_compose(live_lab, "exec", "-T", "scanner", "nmap", "-n", *SOLUTIONS[stage], *output)
    flag = command(str(LAUNCHER), "check", stage, basename + ".xml", env=live_lab).stdout.strip()
    score(flag, stage, tmp_path)
    if stage == "NM-12":
        for extension in (".nmap", ".gnmap", ".xml"):
            live_compose(live_lab, "exec", "-T", "scanner", "test", "-s", basename + extension)


def test_live_network_blocks_external_routing_and_retains_reports(live_lab):
    routes = live_compose(live_lab, "exec", "-T", "scanner", "ip", "route").stdout
    assert "default" not in routes
    live_compose(live_lab, "exec", "-T", "scanner", "bash", "-c", "printf 'keep scan notes\\n' > scans/keep.txt")
    command(str(LAUNCHER), "stop", env=live_lab, timeout=60)
    # Restarting the existing containers exercises persistence without rebuilding.
    live_compose(live_lab, "up", "--detach", timeout=60)
    assert live_compose(live_lab, "exec", "-T", "scanner", "cat", "scans/keep.txt").stdout == "keep scan notes\n"
