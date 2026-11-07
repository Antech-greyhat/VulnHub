# Build status (maintainer notes)

Last updated: 2026-11-07. Spoiler-free. The flag-by-flag check list is in the
answer key on the `solutions` branch, under the same `docs/.internal/maintainer/`
path.

## Done

- Phases 0 to 5 (17 web, network and supply-chain bugs) are merged into `main`.
- Phase 7 (7 forensics challenges) is merged into `main`.
- `flags.sha256` has 24 stage hashes. `labctl submit` and `labctl status` work.
- The `solutions` branch holds the answer key and the forensics generator. It is
  for reference only. **Never merge it into `main`.**

## Still to verify on a Linux host (Kali)

These were built on Windows without Docker, so the container stack has not been
run end to end yet.

1. `python3 labctl.py start`, then open <http://127.0.0.1:8080>.
2. `nmap -sV 127.0.0.1` should show 8080 and 5432, and **not** the internal
   grading service.
3. `python3 labctl.py shell` opens a shell in the web container.
4. `python3 labctl.py reset` reseeds the database.
5. `pipx install pip-audit && python3 labctl.py audit` detects the old pin.
6. Work through the solutions branch's check list to confirm every flag
   comes out of the running stack.

## Known issue

`tests/test_phase5.py::test_secret_is_recoverable_from_git_history` fails. It
runs `git grep` for the secret, which matches the test file itself, so it can
never pass. A fix is to exclude `tests/` from that grep.

## Next

Phase 6 (writeups and remediation) is on hold until the bugs have been hunted.
The prompt is `phase-6-writeups-and-fix.md` in this folder. The rules every
phase follows are in `BUILD-PROMPTS.md`.
