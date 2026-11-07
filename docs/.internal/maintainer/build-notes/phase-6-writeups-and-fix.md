# Phase 6 — Writeups and the fix

Follow the GLOBAL RULES, with one change: **this is the phase where fixing is allowed.**

Do this phase only after I have hunted the bugs myself.

Branch: `phase-6-writeups-and-fix`.

## Part A — Writeup template (for me to fill)

- Create `writeups/TEMPLATE.md` with sections I fill in per bug: Title, OWASP 2025 category, Where I found it, How I exploited it (my steps), Impact, Proof (screenshot/output), How to fix.
- Create one empty writeup file per bug, named by category, e.g. `writeups/01-idor-report.md`, pre-filled with the template and the category only — **not** the answer. I write the rest.
- Do not fill in the exploit steps for me. The point is I write them from my own hunting. You may fill them on the `solutions` branch only, as a check I can compare against after I am done.

## Part B — Guided remediation

- Create `REMEDIATION.md`: a checklist of every intentional bug by category (not location), each with the general fix in plain words — parameterised queries, output escaping, server-side access checks, real file-type checks, no secrets in client code, pinned and updated dependencies, safe error handling, strong sessions.
- Then apply the fixes in the code on this branch, one commit per fix, each commit message naming the category it closes. After this branch, the lab should be the **secure** version.
- Keep the vulnerable version intact on `main` so I always have both to compare for my portfolio.

## Done when
- `writeups/` has a template and one file per bug (category only).
- `REMEDIATION.md` lists every fix.
- The code on this branch is the secured version, one commit per fix.

Open a PR into `main`. Do not merge until I have finished my writeups.

---

Later, for my portfolio: I take the filled writeups plus the before/after code (vulnerable `main` vs secured branch) and publish them as my own learning writeups.
