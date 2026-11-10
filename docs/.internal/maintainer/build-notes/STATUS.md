# Build status (maintainer notes)

Last updated: 2026-11-10. The answer key, the forensics generator and a check
list for the running lab are next door in `../answer-key/`.

## Done

- Phases 0 to 5 (17 web, network and supply-chain bugs) and Phase 7 (7
  forensics challenges) are on `main`.
- Phase 5b (5 weak-crypto challenges, P5B-01 to 05) and Phase 5c (3
  social-engineering challenges on `/intranet`, SE-01 to 03) are merged too.
  That makes 32 stages in `flags.sha256`; the OWASP count in `SCOREBOARD.md`
  is 22, because forensics and social engineering are listed separately.
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
