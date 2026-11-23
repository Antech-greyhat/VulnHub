#!/usr/bin/env python3
"""Seed the local Bandit-inspired discovery exercises (spoilers)."""
import grp
import os
from pathlib import Path
import pwd
import random
import sys

ROOT = Path("/practice")
GUIDE = Path("/home/learner/README.md")
FLAGS = {
    "LD-01": "MFANO{4_d4sh_1s_4_f1l3n4m3}",
    "LD-02": "MFANO{qu0t3s_k33p_n4m3s_t0g3th3r}",
    "LD-03": "MFANO{d0t_f1l3s_4r3_st1ll_th3r3}",
    "LD-04": "MFANO{f1l3_typ3s_b3f0r3_c4t}",
    "LD-05": "MFANO{f1nd_m4tch3s_3v3ry_t3st}",
    "LD-06": "MFANO{f1nd_0wn3r_gr0up_4nd_s1z3}",
    "LD-07": "MFANO{s0rt_m4k3s_un1q_w0rk}",
}


def write(path, content, mode=0o444):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content.encode("ascii") if isinstance(content, str) else content)
    path.chmod(mode)
    return path


def text_record(text, size):
    """Keep the flag on its own line while meeting an exact byte-size test."""
    first = (text + "\n").encode("ascii")
    if len(first) > size:
        raise ValueError("Record does not fit the requested size.")
    if len(first) == size:
        return first
    remaining = size - len(first) - 1
    padding = b"School archive padding. "
    return first + (padding * (remaining // len(padding) + 1))[:remaining] + b"\n"


def prepare(root=ROOT, guide=GUIDE, *, set_ownership=True):
    # A new directory is required; no learner work is replaced or removed.
    root.mkdir(mode=0o755, exist_ok=False)
    instructions = guide.read_text(encoding="utf-8")
    rng = random.Random(20261123)
    for stage in FLAGS:
        directory = root / stage
        directory.mkdir(mode=0o755)
        task = instructions.split(f"## {stage}:", 1)[1].split("\n## ", 1)[0]
        write(directory / "TASK.txt", f"{stage}:" + task)

    write(root / "LD-01/-", FLAGS["LD-01"] + "\n")
    write(root / "LD-02/--fee handover notes--", FLAGS["LD-02"] + "\n")
    write(root / "LD-03/inhere/...school-note", FLAGS["LD-03"] + "\n")

    for index in range(10):
        content = FLAGS["LD-04"] + "\n" if index == 4 else b"\0" + rng.randbytes(127)
        write(root / "LD-04/inhere" / f"-record{index:02d}", content)

    for index in range(12):
        shelf = root / "LD-05/inhere" / f"shelf{index:02d}"
        write(shelf / "short-note", text_record("Mock archive record.", 1032))
        write(shelf / "long-note", text_record("Mock archive record.", 1034))
        write(shelf / "run-note", text_record("Mock executable record.", 1033), 0o555)
        write(shelf / "raw-note", b"\0" + rng.randbytes(1032))
    write(root / "LD-05/inhere/shelf09/.register", text_record(FLAGS["LD-05"], 1033))

    records = [
        ("system/var/lib/notices/.receipt", FLAGS["LD-06"] + "\n", "teacher", "archive"),
        ("system/etc/school/record", text_record("Mock school record.", 33), "learner", "archive"),
        ("system/usr/share/record", text_record("Mock school record.", 33), "teacher", "teachers"),
        ("system/var/cache/record", text_record("Mock school record.", 32), "teacher", "archive"),
    ]
    for name, content, owner, group in records:
        path = write(root / "LD-06" / name, content)
        if set_ownership:
            os.chown(path, pwd.getpwnam(owner).pw_uid, grp.getgrnam(group).gr_gid)
    closed = root / "LD-06/system/closed-records"
    write(closed / "private.txt", "Mock restricted directory.\n")
    closed.chmod(0o700)

    # Decoys have the same length and separators as the real flag. Every decoy
    # repeats, so selecting all flag-shaped lines or using sort -u is insufficient.
    flag = FLAGS["LD-07"]
    widths = [len(part) for part in flag[6:-1].split("_")]
    alphabet = "4bcd3fgh1jklmn0pqr5tuvwxyz"
    decoys = set()
    while len(decoys) < 100:
        token = "MFANO{" + "_".join("".join(rng.choice(alphabet) for _ in range(width))
                                    for width in widths) + "}"
        if token != flag:
            decoys.add(token)
    lines = [token for token in sorted(decoys) for _ in range(9)] + [flag]
    rng.shuffle(lines)
    write(root / "LD-07/data.txt", "\n".join(lines) + "\n")


def main():
    if len(sys.argv) != 2 or sys.argv[1] != "prepare":
        print("Usage: discovery.py prepare (inside the Docker build)", file=sys.stderr)
        return 2
    if os.geteuid() != 0:
        print("Prepare the discovery sandbox through ./linux-discovery/lab build.", file=sys.stderr)
        return 1
    try:
        prepare()
    except (OSError, ValueError, KeyError, IndexError) as exc:
        print(f"Could not prepare discovery exercises: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
