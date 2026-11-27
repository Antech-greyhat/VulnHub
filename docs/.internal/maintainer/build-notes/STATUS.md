# Build status (maintainer notes)

Last updated: 2026-11-27. The answer key, the forensics generator and a check
list for the running lab are next door in `../answer-key/`.

## Done

- FM-09 adds a workshop board exercise on fixed strings, regular expressions
  and grep options. It brings the Linux file track to nine exercises and the
  full catalogue to 83.
- The media club track brought the total to 82 with three beginner steganography
  exercises. Learners inspect Unicode tags, isolate a PNG alpha channel
  and extract a slip from a WAV with a supplied passphrase. Each CLI clue
  links to the corresponding section of 0xRick's steganography reference.
- OSINT-01 through OSINT-03 add three offline book fair investigations to the
  catalogue. Learners verify a venue, trace a photo credit and locate a desk
  using saved public records.
- F-08 through F-10 add three beginner print-room cases on log timelines,
  email headers and SHA-256 comparisons. The two packs brought the total
  to 79 scored challenges, including ten forensics cases and three OSINT cases.

- Nmap enumeration adds NM-01 through NM-12: ten guided labs and two final
  challenges for host discovery, connect/SYN scans, full port ranges, versions,
  UDP/DNS and named HTTP/TLS/SSH/FTP scripts. Real services run on a dedicated
  internal Docker network without published ports; learner scan reports persist
  in a named volume. The XML checker reveals flags only after required findings,
  with hashes/catalogue integrated into existing scoring. This brought the
  totals to 73 challenges and 29 OWASP bugs. A dedicated Docker CI job solves all twelve.

- The discovery sandbox brought Linux foundations to 22 exercises across
  FM-01 through FM-08, FO-01 through FO-07, and LD-01 through LD-07. It adds the missing skills
  from the reference Bandit writeups at levels 1–6 and 8; levels 0 and 7 overlap
  existing file-reading/search tasks and are skipped. All Linux tracks use the
  same offline scoring, with existing IDs and progress preserved. The totals at
  that point were 61 flags and 29 OWASP bugs. Docker CI solves both container-based tracks.

- Web brute-force basics adds BF-01 through BF-04: an uppercase form field
  remapped by JavaScript, a Base64 account clue, username-first enumeration,
  a deliberately shared-password-first gate, and an MD5 username clue behind
  a console absent from robots.txt. All four share one plain template, and
  successful logins show a flag and the lesson. Small practice wordlists and
  21 exploit checks are included. This brought the web/social/forensics total
  to 39 flags and 29 OWASP bugs before the Linux foundation tracks.

- Phase 5d (branch `phase-5d-integrity-design`) adds 3 integrity/insecure-design
  challenges in the student account area: P5D-01 insecure deserialization
  (pickle cookie, A08), P5D-02 mass assignment (A06), P5D-03 secrets in an
  exposed log (A09). New files `portal/integrity.py`, `tests/test_phase5d.py`,
  `portal/templates/account/*`; the log viewer is in `portal/diagnostics.py`.
  These three merged challenges are included in the totals above.

- Phases 0 to 5 (17 web, network and supply-chain bugs) and Phase 7 (7
  forensics challenges) are on `main`.
- Phase 5b (5 weak-crypto challenges, P5B-01 to 05) and Phase 5c (3
  social-engineering challenges on `/intranet`, SE-01 to 03) are merged too.
  Forensics and social engineering are listed separately from the OWASP total.
- Every flag uses leetspeak, e.g. `MFANO{c4n_h4ck_f0r_r34l}`. The old
  plain-English flags still show up in old commits, but they only return
  `wrong flag` now.
- The P5-02 git-history secret was planted again with the leet flag, in an
  add-then-remove pair of commits on `deploy/secrets.env`. The older pair still
  holds the retired plain-English secret, which now works as a decoy.
- A plain `git log -- deploy/secrets.env` shows nothing since the phase
  branches were merged, because each add is cancelled by a remove. Use
  `--full-history` (or `git log -p -S <text>`); the P5-02 test does.
- CI (`.github/workflows/tests.yml`) runs the test suite on every push and
  pull request. It checks out the full history, which the P5-02 test needs.
- The answer key moved from the `solutions` branch to
  `docs/.internal/maintainer/answer-key/` on `main`.
- To rebuild the forensics evidence after changing a flag:
  `python3 docs/.internal/maintainer/answer-key/build_forensics.py forensics/evidence`.
  The build is deterministic.

## Still to verify on a Linux host (Kali)

These were built on Windows without Docker, so the container stack has not been
run end to end yet.

1. `python3 labctl.py start`, then open <http://127.0.0.1:8080>.
2. `nmap -sV 127.0.0.1` should show 8080 and 5432, and **not** the internal
   grading service.
3. `python3 labctl.py shell` opens a shell in the web container.
4. `python3 labctl.py reset` reseeds the portal database. The backup Postgres
   keeps its data in a Docker volume, so after any flag change run
   `docker compose down -v` before `start`, or the old flag stays in it.
5. `pipx install pip-audit && python3 labctl.py audit` detects the old pin.
6. Go through `../answer-key/VERIFY.md`.

## Next

Phase 6 (writeups and remediation) is on hold until the bugs have been hunted.
The prompt is `phase-6-writeups-and-fix.md` in this folder. The rules every
phase follows are in `BUILD-PROMPTS.md`.
