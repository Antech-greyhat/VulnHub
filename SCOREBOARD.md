# Scoreboard

Total intentional bugs so far: **29**

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
| 5d | 1 | A06 Insecure Design |
| 5d | 1 | A08 Software and Data Integrity Failures |
| 5d | 1 | A09 Security Logging and Monitoring Failures |
| BF | 4 | A07 Authentication Failures |

Categories follow the [OWASP Top 10:2025](https://top10.owasp.org/2025/). Locations are not listed here on purpose.

## Web fundamentals

| Stage | Skill |
| ----- | ----- |
| WEB-01 | Follow crawler rules to a yearbook proof and find a developer handover in its HTML source |

## Forensics

Ten offline challenges cover two cases. Beginners can start with the
[print room](forensics/starter/README.md), then examine the media from the
[mock exam leak](forensics/README.md#the-case).

| Stage | Count | Type |
| ----- | ----- | ---- |
| F-01 to F-03 | 3 | Image |
| F-04 | 1 | GIF |
| F-05 to F-06 | 2 | Audio |
| F-07 | 1 | Video |
| F-08 to F-10 | 3 | Print queue timeline, email reply headers and file checksums |

## Beginner OSINT

| Stage | Skill |
| ----- | ----- |
| OSINT-01 | Verify an event venue against the organiser's notices |
| OSINT-02 | Attribute a photograph using captions, dates and reprint credits |
| OSINT-03 | Locate a desk using two landmarks on a visitor map |

All three use the [offline book fair sources](osint/README.md).

## Beginner steganography

| Stage | Evidence | Skill |
| ----- | -------- | ----- |
| STEG-01 | Club notice | Identify invisible Unicode characters by name |
| STEG-02 | Open-day ticket | Isolate the PNG alpha channel and stretch its contrast |
| STEG-03 | Studio chime and cue sheet | Use a supplied passphrase to recover a slip from WAV audio |

The [media club guide](steganography/README.md) includes local commands and
links to 0xRick's tool notes for each exercise.

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

## Linux foundations

Nine file manipulation, seven permissions/ownership, and seven file discovery
exercises precede the web tracks. These teach filesystem commands and are not
counted as OWASP bugs.

| Stage | Count | Skills |
| ----- | ----- | ------ |
| FM-01 to FM-09 | 9 | cat, echo, less, head, tail, tac, grep (fixed strings and regex), wc, paste, join |
| FO-01 to FO-07 | 7 | Symbolic/numeric chmod, directory traversal, chown, chgrp, setgid |
| LD-01 to LD-07 | 7 | Unusual and hidden filenames, file types, find size/permission/owner/group filters, sort and uniq |

## Nmap enumeration

Twelve exercises use a dedicated internal Docker network: ten guided labs and
two final challenges. These teach enumeration and are not counted as OWASP bugs.
Scan reports are checked before their flags can be submitted through labctl.

| Stage | Count | Skills |
| ----- | ----- | ------ |
| NM-01 to NM-05 | 5 | Host discovery, TCP connect/SYN scans, port ranges, service versions, UDP/DNS |
| NM-06 to NM-10 | 5 | Named HTTP, TLS, SSH and FTP NSE scripts, script help and arguments |
| NM-11 to NM-12 | 2 | Independent service discovery, combined TCP/UDP inventory and saved reports |

Total scored challenges: **84** (29 web bugs, 1 web fundamentals flag, 3 social engineering, 3 OSINT,
10 forensics, 3 steganography, 9 Linux file manipulation, 7 Linux permissions/ownership,
7 Linux file discovery, 12 Nmap enumeration).
Existing challenge IDs retain their meaning.
