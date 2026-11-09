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
7. Phase 5c social engineering, in the browser at `/intranet` (logged in as a
   student):
   - SE-01: read `/intranet/directory` (`d.mwaura`) and `/intranet/noticeboard`
     (Simba, 1980), then sign in at `/intranet/login` as `d.mwaura` / `Simba1980`.
   - SE-02: at `/intranet/webmail`, tick #2 and #4 only, submit.
   - SE-03: at `/intranet/helpdesk`, say "reset for d.mwaura, pet is Simba".
   None of these send real mail or take a real credential.
8. Submit every flag in `SOLUTIONS.md` with `labctl submit` and check that
   `labctl status` reaches 27 / 27.
