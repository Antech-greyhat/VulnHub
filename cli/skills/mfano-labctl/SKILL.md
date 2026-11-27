---
name: mfano-labctl
description: Use the Linux labctl command for 4NT3CH VULN3R4BL3 L4B to discover challenges, read progress and gentle clues, validate or submit a learner-provided flag, and manage explicitly requested local lab services.
---

# labctl for 4NT3CH VULN3R4BL3 L4B

Check `command -v labctl`, then run `labctl --json doctor`. If the command is not
installed, use the checkout's `./labctl` and `make install-local`. Scoring is
offline and requires Bash, jq, sha256sum, and flock; whiptail provides the human
menu. No account or token is needed. Docker and pip-audit are separate helpers.

Use `labctl --json tracks`, then `labctl --json labs --track <track-id>` to
discover registered IDs. Resolve an exact title with `labctl --json resolve
'<title>'`; reuse its stable ID. Read `status`, `solved`, `unsolved`, or `hints
<id>` before a write. Lists default to 50 items; use `--limit` and `--offset`
when needed. Hint text is deliberately gentle and contains no completed solution.

Flags must match the selected challenge. Use `submit <id> --flag-stdin --dry-run`
to validate a learner-provided flag without changing progress, then omit
`--dry-run` only when submission is requested. Prefer the hidden password dialog
for a learner entering the flag directly: `labctl submit <id>`. Never put a flag
in argv. JSON returns the solve result and counts, without echoing the submitted
flag or stored hash. Do not inspect answer keys or test spoilers to invent a
submission unless the user asks for that material.

Progress defaults to the selected checkout's `.labprogress.json`, compatible
with the legacy Python helper. `LABCTL_ROOT` selects another checkout;
`LABCTL_PROGRESS_FILE` selects a score file. Use absolute overrides when changing
working directories. Damaged progress is preserved: do not overwrite it or trash
learner progress without their approval. Duplicate submissions count once.

The read-only escape hatch is `labctl --json inspect stages|progress|hints`.
It exposes sanitized local resources, not arbitrary commands or network access.
Use `start|stop|reset|shell|audit --dry-run` to inspect service invocations. Run
those actions only when requested. Reset replaces mock server data and requires
terminal confirmation or `--yes`; it retains flag progress. Audit can reveal its
own challenge flag after a verified vulnerable dependency finding.

Examples:

```bash
labctl --json doctor
labctl --json unsolved --track F --limit 7
labctl --json submit F-01 --flag-stdin --dry-run <<<'MFANO{learner_supplied_flag}'
```

Read the checkout's `cli/README.md` for the JSON envelope, exit codes, and Linux
installation details. A nonzero `doctor` with a diagnostic data object indicates
setup needs attention; ordinary errors use `ok: false` and `error.code`.
