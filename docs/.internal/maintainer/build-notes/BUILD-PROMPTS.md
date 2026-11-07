# Mfano High School Portal — Vulnerable Lab (Build Prompts)

This folder holds the prompts you feed to **Claude Code** to build the lab in phases.
Each file is one phase. Read this file first, then run the phases in order.

The lab is **Mfano High School Portal** — a fake Kenyan school portal, built on purpose
with security bugs so you can hunt them, write them up, then fix them. "Mfano" means
"example". Nothing in it is real.

---

## How to use

1. Make an empty GitHub repo under your account (e.g. `mfano-vuln-lab`), clone it, `cd` into it.
2. Open Claude Code in that folder.
3. Paste the **GLOBAL RULES** block below once at the start so the agent keeps them in mind.
4. Then paste `phase-0-scaffold.md`. Let it finish, review the PR, merge.
5. Paste the next phase. Repeat in order: 0 → 1 → 2 → 3 → 4 → 5 → 6.

Do each phase one at a time. Do not paste all phases at once.

As you hunt: when an exploit reveals a `MFANO{...}` flag, run `labctl submit MFANO{...}`. It tells you if it is right, marks that stage done, and points you to the next one.

---

## The learning path

- **Phase 0** — Scaffold. The app, mock data, Docker, README, the `labctl` CLI. No bugs scored yet.
- **Phase 1** — Web + Linux files. Report download leaks a path to an unprotected admin page. You learn the Linux filesystem by exploring the lab box.
- **Phase 2** — Networking. A second service with a weak password. You learn ports and services with nmap against your own lab.
- **Phase 3** — Core web. SQL injection, stored XSS, weak sessions, normal user → admin, changing results.
- **Phase 4** — The server. Command injection, bad file upload, SSRF, fake payment tampering. This is where low bugs chain into full control.
- **Phase 5** — Secrets and supply chain. Fake keys in frontend code, a secret in git history, an old dependency, leaky error pages.
- **Phase 6** — Writeups and the fix. A writeup template you fill yourself, then a guided remediation branch where the lab is made secure.

---

## GLOBAL RULES (paste these to Claude Code before Phase 0)

> You are building a **deliberately vulnerable learning lab** called **Mfano High School Portal**.
> It is only for me to practice penetration testing on my own machine. Follow these rules in every phase:
>
> **Safety and scope**
> - All data is mock and fake: made-up students, marks, fees, and fake M-Pesa-style payments. No real people, no real school, no real payment API, no real outbound calls.
> - The app runs **locally only**. Bind the web app to `127.0.0.1`. Use Docker Compose. Do not expose anything to the public internet.
> - The README must warn, in bold, at the very top: this is a vulnerable lab, never deploy it publicly, and if hosting for yourself use Tailscale or Cloudflare Access so only you can reach it.
> - Any secrets or API keys are clearly fake, e.g. `FAKE_KEY_do_not_use_123`. Never commit a real secret.
>
> **The bugs are on purpose**
> - Vulnerabilities in Phases 1–5 are intentional. Do **not** fix them, do not add input validation, security headers, or a WAF, unless the phase says so. Phase 6 is where fixing happens.
>
> **Keep solutions hidden from me**
> - On the `main` branch keep only `SCOREBOARD.md`, which lists how many bugs exist and their OWASP category — **not where they are**.
> - Put any exploit steps, hints, or answers only on a separate `solutions` branch. Never write them on `main`. I want to hunt the bugs myself.
>
> **Flags and scoring (CyberGame style)**
> - Every intentional bug has a flag in the format `MFANO{short_tag}`, planted so that actually exploiting the bug reveals it — e.g. inside another student's report, dumped by an injection, printed by a command, or shown on the unprotected page. Finding the flag only by reading the source does not count; it should fall out of the exploit.
> - On `main` keep only `flags.sha256`: one line per stage, `stage_id:sha256_of_flag:owasp_category:difficulty`. Hashes only — never the plaintext flag, never the location.
> - Put the plaintext flags and where each one is planted only on the `solutions` branch.
> - `labctl` checks a submitted flag by hashing it and matching `flags.sha256`, saves my progress locally, and points me to the next stage. Phase 0 builds this; each later phase appends its flag hashes.
>
> **Tech**
> - Python is the largest language. Use Flask + Jinja2 templates + SQLite for the app. Keep JavaScript small. The `labctl` helper is Python.
> - Each phase goes on its own branch named `phase-N-<slug>`.
> - End every commit message with this trailer:
>   `Co-Authored-By: Claude <noreply@anthropic.com>`
> - Open a pull request from the phase branch into `main`. End the PR description with a line saying it was generated with Claude Code. Do not merge it yourself; I will review and merge.
> - Update `SCOREBOARD.md` each phase: the new bug count and their OWASP 2025 categories, but not their location.

Keep this block in mind for all phases below.
