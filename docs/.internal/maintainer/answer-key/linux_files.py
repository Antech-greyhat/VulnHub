"""Deterministic file practice fixtures and answers (spoilers)."""
FLAGS = {
    "FM-01": "MFANO{c4t_r34ds_1n_0rd3r}",
    "FM-02": "MFANO{3ch0_wr1t3s_4nd_4pp3nds}",
    "FM-03": "MFANO{l3ss_f1nds_th3_d3t41l}",
    "FM-04": "MFANO{h34d_4nd_t41l_b00k3nds}",
    "FM-05": "MFANO{t4c_r3v3rs3s_l1n3s}",
    "FM-06": "MFANO{gr3p_f1lt3rs_wc_c0unts}",
    "FM-07": "MFANO{p4st3_4l1gns_c0lumns}",
    "FM-08": "MFANO{j01n_m4tch3s_s0rt3d_k3ys}",
    "FM-09": "MFANO{gr3p_f1nds_th3_h4nd0v3r}",
}

TIMELINE = "08:00 session opened\n12:00 ledger reconciled\n16:00 archive sync complete\n"
FAILURES = "".join(f"ERROR backup job={n:02d} status=failed\n" for n in range(3, 28, 3))
LOG = "".join(
    (f"ERROR backup job={n:02d} status=failed\n" if n % 3 == 0 else
     f"INFO backup job={n:02d} status=complete\n") +
    ("DEBUG message=ERROR backup status=failed\n" if n % 5 == 0 else "") +
    ("ERROR backup-check status=failed\n" if n % 7 == 0 else "")
    for n in range(1, 28)
)
NAMES = ["Amani", "Chebet", "Njeri", "Otieno"]
SCORES = ["72", "81", "67", "90"]
ROSTER = "MHS1004 Otieno\nMHS1002 Chebet\nMHS1005 Zawadi\nMHS1001 Amani\nMHS1003 Njeri\n"
MARKS = "MHS1003 67\nMHS1006 54\nMHS1001 72\nMHS1004 90\nMHS1002 81\n"
JOINED = "MHS1001 Amani 72\nMHS1002 Chebet 81\nMHS1003 Njeri 67\nMHS1004 Otieno 90\n"


def inputs(workshop_board):
    flag = FLAGS["FM-01"]
    return {
        "FM-01": {"part-a.txt": flag[:12], "part-b.txt": flag[12:] + "\n"},
        "FM-02": {"old-note.txt": "Outdated handover: this line must not remain.\n"},
        "FM-03": {"handbook.txt": "\n".join(
            "ACTIVE backup-window=22:15" if n == 173 else
            ("RETIRED backup-window=03:00" if n == 42 else
             f"Section {n:03d}: verify the mock school backup inventory.")
            for n in range(1, 321)) + "\n"},
        "FM-04": {"session.log": "START session=17\n" +
            "".join(f"INFO session=17 item={n:03d}\n" for n in range(1, 151)) +
            "END session=17\n"},
        "FM-05": {"newest-first.log": "".join(reversed(TIMELINE.splitlines(keepends=True)))},
        "FM-06": {"backup.log": LOG},
        "FM-07": {"names.txt": "\n".join(NAMES) + "\n", "scores.txt": "\n".join(SCORES) + "\n"},
        "FM-08": {"roster.txt": ROSTER, "marks.txt": MARKS},
        "FM-09": {"workshop-board.txt": workshop_board},
    }


def answers(stage):
    return {
        "FM-01": {"answer.txt": FLAGS["FM-01"] + "\n"},
        "FM-02": {"handover.txt": "School backup handover\nOwner: learner\nStatus: ready\n"},
        "FM-03": {"answer.txt": "ACTIVE backup-window=22:15\n"},
        "FM-04": {"bookends.txt": "START session=17\nEND session=17\n"},
        "FM-05": {"oldest-first.log": TIMELINE},
        "FM-06": {"failures.txt": FAILURES, "count.txt": "9\n"},
        "FM-07": {"results.tsv": "".join(f"{name}\t{score}\n" for name, score in zip(NAMES, SCORES))},
        "FM-08": {"joined.txt": JOINED},
        "FM-09": {"answers.txt": (
            "Yea\n-v\nbobthebuilder\nLinuxIsGawd\n"
            "The spare hinge is in the blue chalk tin.\n"
        )},
    }[stage]


def prepare(workspace, workshop_board):
    fixtures = inputs(workshop_board)
    for stage, files in fixtures.items():
        directory = workspace / stage
        directory.mkdir()
        for name, text in files.items():
            (directory / name).write_text(text, encoding="utf-8")
    # FM-02 starts with stale content so > versus >> makes a visible difference.
    (workspace / "FM-02/handover.txt").write_text(
        fixtures["FM-02"]["old-note.txt"], encoding="utf-8")


def check(workspace, stage):
    for name, expected in answers(stage).items():
        path = workspace / stage / name
        if not path.is_file():
            raise ValueError(f"{stage}/{name} is missing. Read this challenge's task and create it.")
        actual = path.read_text(encoding="utf-8")
        # wc implementations may pad a number; accept that harmless whitespace.
        matched = actual.strip() == expected.strip() if name == "count.txt" else actual == expected
        if not matched:
            raise ValueError(f"{stage}/{name} does not match the task yet. Check content, order and line endings.")
