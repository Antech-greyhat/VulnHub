# Solutions (spoilers)

> This branch is the answer key. It holds the plaintext flags, where each one is
> planted, and how to exploit it. It lives **only** on the `solutions` branch and
> must never be merged into `main`. If you are here to hunt the bugs yourself,
> turn back now.

All demo logins: students `MHS1001`–`MHS1030` / `Student@123`, admin `admin` /
`Mfano@Admin2026`. The app is at <http://127.0.0.1:8080>.

---

## Phase 1 — Web + Linux files (Easy)

### P1-01 · IDOR report download · A01 · `MFANO{idor_reports_are_not_private}`
- **Where:** `portal/student.py` `report()` fetches `report_<sid>.html` by the
  `sid` query param with no ownership check. The flag is in `MHS1013`'s report
  (seeded via the `remark` column in `seed.py`).
- **Exploit:** log in as any student, open *Download report*, then change `sid`
  in the URL (`/student/report?sid=<id>`) to another student's id. The id of
  `MHS1013` is the one carrying the flag in the head-teacher remark.
- **Hint to give yourself:** *look at what the report leaks, and whose report
  you are actually allowed to see.*

### P1-02 · Unprotected ops console · A01 · `MFANO{unlinked_is_not_protected}`
- **Where:** `portal/ops.py` serves `/ops/students` with no `login_required`.
  The clue is an HTML comment in every report footer (`portal/reports.py`).
- **Exploit:** read the report source (or the on-disk report files) → find
  `/ops/students` → open it with no login. The token is on the page.
- **Hint:** *not everything is linked in the menu.*

### P1-03 · Readable files on the box · A02 · `MFANO{ls_cat_grep_find_the_trail}`
- **Where:** `seed.py` `write_reports()` drops `ADMIN_NOTES.txt` into the
  world-readable reports dir (`/srv/mfano/reports` in the container).
- **Exploit:** `python labctl.py shell`, then
  `grep -r MFANO /srv/mfano` or `cat /srv/mfano/reports/ADMIN_NOTES.txt`.
- **Hint:** *explore the filesystem with `ls`, `cat`, `find`, `grep`.*

## Phase 2 — Networking (Easy–Medium)

### P2-01 · Weak backup DB password · A02 · `MFANO{default_creds_open_the_backup}`
- **Where:** `docker-compose.yml` `backupdb` uses `POSTGRES_PASSWORD=postgres`.
  The flag is in the `backup_notes` table (`services/backup/init.sql`).
- **Exploit:** `nmap -sV 127.0.0.1` shows 5432, then
  `psql "postgresql://mfano:postgres@127.0.0.1:5432/results_backup" -c
  "SELECT note FROM backup_notes;"`.
- **Hint:** *default passwords on backups.*

### P2-02 · Trusting the internal network · A02 · `MFANO{internal_does_not_mean_safe}`
- **Where:** `services/grading/app.py` `/internal/metadata` returns an access
  token to any caller, no auth. The service is not published to the host.
- **Exploit:** from inside the lab network (or via the Phase 4 SSRF), hit
  `http://grading:9000/internal/metadata`.
- **Hint:** *"internal only" is not the same as protected.*

## Phase 3 — Core web (Medium)

### P3-01 · SQL injection · A05 · `MFANO{union_select_the_staff_vault}`
- **Where:** `portal/student.py` `search()` concatenates `q` into the SQL. The
  flag is in `staff_secrets.secret` (seeded in `seed.py`).
- **Exploit:** in *Find classmate*, search
  `zzz%' UNION SELECT label, secret FROM staff_secrets --`.
- **Hint:** *the search box builds its query the lazy way; two columns come
  back.*

### P3-02 · Stored XSS → admin token · A05 · `MFANO{stored_script_stole_the_review_token}`
- **Where:** `portal/admin.py` `student_review()` renders `about` with `|safe`.
  The flag is behind the admin-only `/admin/review-token`.
- **Exploit:** set your profile *About me* to
  `<script>fetch('/admin/review-token').then(r=>r.text()).then(t=>new Image().src='/x?'+btoa(t))</script>`,
  then the admin opens your review page and the script runs as admin. (For a
  quick check, log in as admin and open `/admin/review-token` directly.)
- **Hint:** *what you type in your profile runs in whose browser?*

### P3-03 · Forgeable role cookie · A07 · `MFANO{unsigned_cookie_made_me_admin}`
- **Where:** `portal/auth.py` sets a plaintext `mfano_role` cookie;
  `portal/admin.py` `console()` trusts it instead of the signed session.
- **Exploit:** log in as a student, edit the `mfano_role` cookie to `admin`,
  open `/admin/console`.
- **Hint:** *which cookie is signed, and which one is just text?*

### P3-04 · Marks tamper via client role · A01 · `MFANO{client_said_admin_so_marks_changed}`
- **Where:** `portal/student.py` `update_marks()` authorises on a client-sent
  `role` field.
- **Exploit:**
  `curl -b cookie.txt -d 'role=admin&subject=Mathematics&term=2026 Term 1&score=100'
  http://127.0.0.1:8080/student/marks/update`.
- **Hint:** *the server believes you when you say you are admin.*

## Phase 4 — Reaching the server (Hard)

### P4-01 · Command injection · A05 · `MFANO{semicolon_reached_the_shell}`
- **Where:** `portal/admin.py` `ping()` runs `ping -c 1 <host>` with
  `shell=True`. Flag planted at `/srv/mfano/server.flag` (`seed.py`).
- **Exploit:** admin *Tools → Ping*, host =
  `127.0.0.1; cat /srv/mfano/server.flag`.
- **Hint:** *where does the host string end up?*

### P4-02 · Upload → SSTI code exec · A02 · `MFANO{uploaded_script_ran_on_the_server}`
- **Where:** `portal/admin.py` `upload()` saves any file; `preview()` renders it
  with `render_template_string`. Flag is `config['SERVER_FLAG']`.
- **Exploit:** upload a file containing `{{ config['SERVER_FLAG'] }}`, then open
  `/admin/tools/preview?name=<file>`.
- **Hint:** *the preview renders your file as a template.*

### P4-03 · SSRF to grading service · A01 · `MFANO{ssrf_reached_the_grading_service}`
- **Where:** `portal/admin.py` `import_logo()` fetches any URL. Flag at grading
  `/internal/logo-config` (`services/grading/app.py`).
- **Exploit:** admin *Tools → Import logo*, URL =
  `http://grading:9000/internal/logo-config`.
- **Hint:** *the fetcher does not care where the URL points.*

### P4-04 · Payment tamper · A01 · `MFANO{paid_nothing_fees_cleared}`
- **Where:** `portal/payments.py` `pay()` trusts the client `amount`/`status`.
- **Exploit:** on the payments page, *Pay now* with amount = your full balance
  (no real payment). The JSON response carries the flag when the balance hits 0.
- **Hint:** *who decides how much you paid?*

## Phase 5 — Secrets and supply chain (Medium–Hard)

### P5-01 · Secret in frontend · A04 · `MFANO{frontend_key_opened_the_till}`
- **Where:** `portal/static/payment.js` ships a `secretKey`.
- **Exploit:** open the payments page, View Source → `payment.js`, or
  `curl http://127.0.0.1:8080/static/payment.js`.
- **Hint:** *client code is downloaded to every browser.*

### P5-02 · Secret in git history · A04 · `MFANO{git_history_never_forgets}`
- **Where:** `deploy/secrets.env`, added then removed on this branch.
- **Exploit:** `git log -p -S git_history_never_forgets`, or `gitleaks detect`.
- **Hint:** *the latest tree is clean; the history is not.*

### P5-03 · Outdated dependency · A03 · `MFANO{pip_audit_found_the_old_requests}`
- **Where:** `requirements.txt` pins `requests==2.19.1`.
- **Exploit:** `python labctl.py audit` (or `pip-audit -r requirements.txt`). The
  flag prints only when pip-audit actually reports the vulnerable pin.
- **Hint:** *detection, not exploitation. Read the advisory.*

### P5-04 · Leaky error page · A10 · `MFANO{stack_trace_told_everything}`
- **Where:** debug mode on (`MFANO_DEBUG=1`); `portal/diagnostics.py`
  `self-test` raises with the build token in the message.
- **Exploit:** open `http://127.0.0.1:8080/diagnostics/self-test?load=0`; the
  interactive traceback shows the message with the token.
- **Hint:** *make it crash and read the stack trace.*

---

## The intended chain

Phase 1 (unprotected console) and Phase 3 (SQLi, stored XSS, forgeable cookie)
get you to admin. Admin unlocks the Phase 4 server tools, where command
injection and the upload give code execution on the box — the same box whose
filesystem you first explored in Phase 1. SSRF reaches the internal grading
service from Phase 2. Phase 5's frontend key and git-history secret are the
quiet mistakes that tie the payment flow together.

---

## Phase 7: Forensics

The generator is `tools/build_forensics.py` on this branch only. It uses the
standard library and is deterministic, so `python tools/build_forensics.py
forensics/evidence` rebuilds byte-identical files.

### F-01 · PNG metadata · `MFANO{metadata_tells_the_story}`
- **Where:** `tEXt` chunk `Comment` in `01_noticeboard.png`.
- **Solve:** `exiftool 01_noticeboard.png` or `strings 01_noticeboard.png | grep MFANO`.

### F-02 · Appended ZIP · `MFANO{binwalk_carved_the_zip}`
- **Where:** a deflated ZIP is appended after `IEND` in `02_staff_photo.png`.
- **Solve:** `binwalk -e 02_staff_photo.png` (or `unzip 02_staff_photo.png`,
  which skips the PNG prefix) and read `leaked/kcse_mock_chemistry_p1.txt`.

### F-03 · LSB steganography · `MFANO{least_significant_secrets}`
- **Where:** LSB of R, G, B in turn, pixels row by row, MSB-first bytes,
  NUL-terminated (`03_prize_giving.png`).
- **Solve:** `zsteg 03_prize_giving.png` (shows up as `b1,rgb,lsb,xy`), or
  Pillow: `np.packbits(np.array(img).reshape(-1) & 1)`.

### F-04 · Hidden GIF frame · `MFANO{one_frame_too_fast}`
- **Where:** frame 17 of 25 in `04_school_bell.gif`, with a 10 ms delay
  (the others use 120 ms). The GIF comment is a decoy.
- **Solve:** `ffmpeg -i 04_school_bell.gif f%02d.png` or `magick 04_school_bell.gif -coalesce f%02d.png`.

### F-05 · Morse audio · `MFANO{morse_code_never_dies}`
- **Where:** 700 Hz Morse at 80 ms per unit with hiss: `MORSE CODE NEVER DIES`.
- **Solve:** Audacity waveform by eye, or any audio Morse decoder.

### F-06 · Spectrogram · `MFANO{look_at_the_spectrogram}`
- **Where:** text drawn as tone bands from 3 kHz to 9 kHz under a 110 Hz hum
  and noise (`06_assembly_recording.wav`).
- **Solve:** Audacity → Spectrogram view (or Sonic Visualiser). Raise the max
  frequency to at least 10 kHz and zoom the time axis out.

### F-07 · CCTV frame · `MFANO{frame_by_frame_cctv}`
- **Where:** frame index 41 (0-based; `ffmpeg` writes it as `_42`) of
  `07_corridor_cctv.avi`, at 02:13:04. The INFO comment hints "review every frame".
- **Solve:** `ffmpeg -i 07_corridor_cctv.avi f%02d.png`, or step frames in VLC
  (`e` key).
