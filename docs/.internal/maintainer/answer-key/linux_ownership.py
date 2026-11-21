#!/usr/bin/env python3
"""Seed and verify the container's real Unix ownership and access (spoilers)."""
import grp
import json
import os
from pathlib import Path
import pwd
import stat
import sys
import uuid

ROOT = Path("/practice")
FLAGS = {
    "FO-01": "MFANO{chm0d_cl0s3s_pr1v4t3_n0t3s}",
    "FO-02": "MFANO{0ct4l_m0d3s_m4k3_s3ns3}",
    "FO-03": "MFANO{d1r3ct0r13s_n33d_s34rch}",
    "FO-04": "MFANO{ch0wn_f1x3s_th3_0wn3r}",
    "FO-05": "MFANO{chgrp_sh4r3s_w1th_th3_t34m}",
    "FO-06": "MFANO{0wn3r_4nd_gr0up_h4nd0v3r}",
    "FO-07": "MFANO{s3tg1d_k33ps_th3_t34m_gr0up}",
}
# path, required owner, required group, required mode, initial owner/group/mode
TARGETS = {
    "FO-01": [("private-notes.txt", "learner", "learner", 0o600, "learner", "learner", 0o666)],
    "FO-02": [("team-readme.txt", "learner", "teachers", 0o640, "learner", "teachers", 0o600)],
    "FO-03": [("inbox", "learner", "teachers", 0o750, "learner", "teachers", 0o640),
              ("inbox/report.txt", "learner", "teachers", 0o640, "learner", "teachers", 0o640)],
    "FO-04": [("misplaced.txt", "learner", "learner", 0o640, "root", "learner", 0o640)],
    "FO-05": [("report.txt", "learner", "teachers", 0o640, "learner", "learner", 0o640)],
    "FO-06": [("handover.txt", "archivist", "archive", 0o640, "learner", "learner", 0o666)],
    "FO-07": [("shared", "learner", "teachers", 0o2770, "learner", "teachers", 0o777)],
}
DIRECTORIES = {"inbox", "shared"}
CONTENT = "Mock school record: preserve this content while changing ownership and permissions.\n"


def prepare():
    ROOT.mkdir(mode=0o755, exist_ok=False)
    guide = Path("/home/learner/README.md").read_text()
    for stage, targets in TARGETS.items():
        directory = ROOT / stage
        directory.mkdir(mode=0o755)
        task = guide.split(f"## {stage}:", 1)[1].split("\n## ", 1)[0]
        (directory / "TASK.txt").write_text(f"{stage}:" + task)
        for name, _owner, _group, _mode, owner, group, mode in targets:
            path = directory / name
            if name in DIRECTORIES:
                path.mkdir()
            else:
                path.write_text(CONTENT)
            os.chown(path, pwd.getpwnam(owner).pw_uid, grp.getgrnam(group).gr_gid)
            os.chmod(path, mode)


def as_user(username, operation):
    """Use a child with real user/group IDs; do not guess access from mode bits."""
    account = pwd.getpwnam(username)
    read_fd, write_fd = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(read_fd)
        try:
            os.initgroups(username, account.pw_gid)
            os.setgid(account.pw_gid)
            os.setuid(account.pw_uid)
            result = operation()
        except OSError as exc:
            result = {"error": str(exc)}
        with os.fdopen(write_fd, "w") as stream:
            json.dump(result, stream)
        os._exit(0)
    os.close(write_fd)
    with os.fdopen(read_fd) as stream:
        result = json.load(stream)
    _, status = os.waitpid(pid, 0)
    if status != 0 or "error" in result:
        raise ValueError("Could not complete the access check. Preserve the exercise files and retry.")
    return result


def access(username, path, mode, expected):
    observed = as_user(username, lambda: {"allowed": os.access(path, mode)})["allowed"]
    if observed != expected:
        raise ValueError(f"Access for {username} on {path.name} does not meet the task yet.")


def check(stage):
    directory = ROOT / stage
    for name, owner, group, mode, *_initial in TARGETS[stage]:
        path = directory / name
        actual = path.lstat()
        correct_type = stat.S_ISDIR(actual.st_mode) if name in DIRECTORIES else stat.S_ISREG(actual.st_mode)
        if not correct_type:
            raise ValueError(f"{name} must retain its original file type; symlinks do not count.")
        if (actual.st_uid, actual.st_gid, stat.S_IMODE(actual.st_mode)) != (
                pwd.getpwnam(owner).pw_uid, grp.getgrnam(group).gr_gid, mode):
            raise ValueError(f"{name} needs owner {owner}, group {group}, mode {mode:04o}. Inspect it with ls -ld.")
        if name not in DIRECTORIES and path.read_text() != CONTENT:
            raise ValueError(f"Preserve the original content of {name}.")
    path = directory / TARGETS[stage][0][0]
    access("outsider", path, os.R_OK, False)
    if stage in ("FO-01", "FO-04"):
        access("learner", path, os.R_OK | os.W_OK, True)
        access("teacher", path, os.R_OK, False)
    elif stage in ("FO-02", "FO-05"):
        access("learner", path, os.R_OK | os.W_OK, True)
        access("teacher", path, os.R_OK, True)
        access("teacher", path, os.W_OK, False)
    elif stage == "FO-03":
        access("teacher", path / "report.txt", os.R_OK, True)
        access("teacher", path, os.W_OK, False)
        access("outsider", path / "report.txt", os.R_OK, False)
    elif stage == "FO-06":
        access("archivist", path, os.R_OK | os.W_OK, True)
        access("learner", path, os.R_OK, False)
        access("teacher", path, os.R_OK, False)
    elif stage == "FO-07":
        access("teacher", path, os.R_OK | os.W_OK | os.X_OK, True)
        access("outsider", path, os.W_OK | os.X_OK, False)

        def create_probe():
            # Keep a uniquely named mock file for learners to inspect. No user
            # file is replaced or removed by a check.
            probe = path / ("group-check-" + uuid.uuid4().hex + ".txt")
            os.umask(0o007)
            with probe.open("x") as stream:
                stream.write("Teacher-created group inheritance check.\n")
            details = probe.stat()
            return {"uid": details.st_uid, "gid": details.st_gid}

        observed = as_user("teacher", create_probe)
        if observed != {"uid": pwd.getpwnam("teacher").pw_uid, "gid": grp.getgrnam("teachers").gr_gid}:
            raise ValueError("New files must inherit the teachers group.")


def main():
    if os.geteuid() != 0:
        print("Use check-ownership inside the Docker sandbox.", file=sys.stderr)
        return 1
    if len(sys.argv) != 2 or sys.argv[1] not in (*FLAGS, "prepare"):
        print("Choose FO-01 through FO-07.", file=sys.stderr)
        return 2
    try:
        if sys.argv[1] == "prepare":
            prepare()
        else:
            check(sys.argv[1])
            print(FLAGS[sys.argv[1]])
    except (OSError, ValueError) as exc:
        print(f"Not complete: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
