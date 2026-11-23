# Live-stack check list (spoilers)

Run these on a Linux host (Kali) with the lab running to confirm every flag
comes out of the real containers. They were written on Windows, where Docker
was not available.

1. `python3 labctl.py start` brings the portal up on <http://127.0.0.1:8080>.
2. `nmap -sV 127.0.0.1` shows 8080 (web) and 5432 (Postgres backup). The grading
   service must **not** appear (it is internal only).
3. `psql "postgresql://mfano:postgres@127.0.0.1:5432/results_backup" -c "SELECT * FROM backup_notes;"`
   gives the P2-01 flag.
4. `python3 labctl.py shell`, then inside the container `cat /srv/mfano/server.flag`
   and `grep -r MFANO /srv/mfano` work (P1-03, P4-01).
5. The P4-01 command injection uses a `; cat ...` payload. It only works on the
   Linux container, so test it there.
6. `pipx install pip-audit && python3 labctl.py audit` prints the P5-03 flag. If
   it can't resolve, run `pip-audit` inside the container.
7. Phase 5b crypto, all against the running portal:
   - P5B-01: `curl "http://127.0.0.1:8080/student/search?q=zzz%25'%20UNION%20SELECT%20username,md5_password%20FROM%20legacy_staff--%20-"`
     (with a logged-in session) leaks the MD5; crack to `chocolate`; log in at
     `/staff/login`.
   - P5B-02: the `mfano_vault` cookie base64-decodes to the flag.
   - P5B-03: crack the `mfano_api` JWT secret (`mfano123`), forge `role=admin`,
     `curl -H "Authorization: Bearer <forged>" .../api/exam-key`.
   - P5B-04: `curl .../static/app.config.js`, then the openssl decrypt in
     `SOLUTIONS.md`.
   - P5B-05: run the byte-at-a-time script in `SOLUTIONS.md` against `/api/seal`.
8. Phase 5c social engineering, in the browser at `/intranet` (logged in as a
   student):
   - SE-01: read `/intranet/directory` (`d.mwaura`) and `/intranet/noticeboard`
     (Simba, 1980), then sign in at `/intranet/login` as `d.mwaura` / `Simba1980`.
   - SE-02: at `/intranet/webmail`, tick #2 and #4 only, submit.
   - SE-03: at `/intranet/helpdesk`, say "reset for d.mwaura, pet is Simba".
   None of these send real mail or take a real credential.
9. Phase 5d integrity and design, logged in as a student:
   - P5D-01: `GET /account/prefs` once to get the `mfano_prefs` cookie; replace
     it with the base64 pickle from `SOLUTIONS.md` and re-request — the flag
     comes back in the JSON.
   - P5D-02: `POST /account/settings` with `is_rep=1`, then open
     `/account/rep-room`.
   - P5D-03: `POST /account/forgot` with `username=admin`, then
     `GET /diagnostics/logs?name=portal-security.log` (no login needed).
10. Web brute-force basics, without logging into the main portal:
    - Inspect `/robots.txt`; discover `/management/` independently with
      Gobuster and `web-bruteforce/wordlists/paths.txt`.
    - BF-01: `/archive/login` source contains a Base64 username. Decode to
      `a.njeri`, inspect the JavaScript mapping `Username` to `username`, and
      guess the password `sunshine` from the practice list.
    - BF-02: enumerate usernames at `/office/login` using a wrong password.
      `incorrect password` identifies `registrar`; then guess `welcome1`.
    - BF-03: at `/backup/login`, use an invalid username and guess passwords.
      `incorrect username` identifies shared password `football`. Hold it
      constant and enumerate usernames to find `archivist`.
    - BF-04: `/management/login` source leaks an MD5 username digest. Match
      it against the username list to recover `examadmin`, then guess `dragon`.
    All errors return HTTP 200. Only a complete, successful login shows its
    flag; the new accounts do not grant a main-portal admin session.
11. Submit every flag in `SOLUTIONS.md` with `labctl submit` and check that
    `labctl status` reaches 61 / 61.

## Linux file manipulation

`python3 -B linux-files/lab.py prepare` creates disposable mock inputs.
The exact command solutions are in `tests/test_linux_files.py`. Every checker
result must match its registered hash, validate in a dry run, record one solve,
reject another challenge ID, and count repeat submissions once.

## Linux permissions and ownership

Run `MFANO_TEST_DOCKER=1 python3 -m pytest -q tests/test_linux_ownership.py`
on a Docker-enabled host. The suite builds the image, solves all seven tasks
with actual chmod/chown/chgrp operations, tests access as separate users,
checks group inheritance, rejects mode 0777, and submits every revealed flag.
The same container checks run in the linux-ownership CI job.

## Linux file discovery

Run `MFANO_TEST_DOCKER=1 python3 -m pytest -q tests/test_linux_discovery.py`
on a Docker-enabled host. All seven tasks are solved as learner using real
shell tools, then submitted through labctl. LD-06 combines actual teacher/archive
ownership with a 33-byte size and preserves results despite permission-denied
directories. The tests also check quoting, hidden listings, executable/binary
decoys, shuffled duplicates, dry runs, repeat submissions, wrong IDs, and saved
progress compatibility. Six content-only tasks run without Docker too.
The linux-ownership CI job runs both Linux container suites.
