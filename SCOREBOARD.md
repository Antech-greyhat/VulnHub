# Scoreboard

Total intentional bugs so far: **22**

| Phase | Count | OWASP 2025 category |
| ----- | ----- | ------------------- |
| 0 | 0 | None (scaffold) |
| 1 | 2 | A01 Broken Access Control |
| 1 | 1 | A02 Security Misconfiguration |
| 2 | 2 | A02 Security Misconfiguration |
| 3 | 2 | A05 Injection |
| 3 | 1 | A07 Authentication Failures |
| 3 | 1 | A01 Broken Access Control |
| 4 | 1 | A05 Injection |
| 4 | 1 | A02 Security Misconfiguration |
| 4 | 2 | A01 Broken Access Control |
| 5 | 2 | A04 Cryptographic Failures |
| 5 | 1 | A03 Software Supply Chain Failures |
| 5 | 1 | A10 Mishandling of Exceptional Conditions |
| 5b | 4 | A04 Cryptographic Failures |
| 5b | 1 | A07 Authentication Failures |

Categories follow the [OWASP Top 10:2025](https://top10.owasp.org/2025/). Locations are not listed here on purpose.

## Forensics

Seven offline challenges in `forensics/evidence/`. These are not web bugs, so
they are not counted in the OWASP total above.

| Stage | Count | Type |
| ----- | ----- | ---- |
| F-01 to F-03 | 3 | Image |
| F-04 | 1 | GIF |
| F-05 to F-06 | 2 | Audio |
| F-07 | 1 | Video |

## Social engineering (SEE)

Three contained awareness challenges on the staff intranet (`/intranet`). Every
person, post and message is a fake NPC; nothing sends real mail and no real
credentials are involved. These are not web code bugs, so they are not counted
in the OWASP total above.

| Stage | Count | Type |
| ----- | ----- | ---- |
| SE-01 | 1 | OSINT / password profiling |
| SE-02 | 1 | Phishing spotting (defence) |
| SE-03 | 1 | Pretexting (scripted helpdesk bot) |
