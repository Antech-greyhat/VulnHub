# labctl for Linux

`labctl` is the Linux console for **4NT3CH VULN3R4BL3 L4B**. Use it to browse
challenge tracks, read hints, score flags offline, and manage the web portal's
services. The keyboard menus use Bash 4+, jq, and whiptail/libnewt, with a dark
background, cyan selection, and green headings. Windows support is planned for
a later release.

## Install and open

On Kali, Debian, or Ubuntu:

```bash
sudo apt update
sudo apt install -y bash jq whiptail coreutils util-linux make
make install-local
export PATH="$HOME/.local/bin:$PATH"
labctl
```

Before installation, run `./labctl` from the checkout. `make install-local`
creates `~/.local/bin/labctl` as a symlink to this checkout, so it finds its data
from any working directory. Keep the checkout in place. An existing, different
command is preserved; use `make install-local BINDIR=/another/bin` if necessary.

Use arrows to select, Tab to move between controls, and Enter to confirm. Back
or Escape returns to the previous screen; Escape at the main menu exits. Long
read-only dialogs support scrolling; use Tab to focus their OK button.
The menu needs at least 64 columns and 20 rows. `NO_COLOR=1` or `--no-color`
uses plain command output and a monochrome menu. A custom `NEWT_COLORS` palette
is respected.

## Lab workflow

1. Open `labctl`, then choose **Submit a flag**.
2. Choose the track and challenge ID. The list shows title, difficulty, and status.
3. Paste the exact flag into the hidden input box.
4. The CLI compares its SHA-256 hash with that challenge's registered hash,
   records a correct submission, and shows solved/remaining counts and the next
   challenge. A flag belonging to another challenge is rejected for the selected ID.

The menu also offers all challenges, solved challenges, remaining challenges,
gentle clues, track totals, setup diagnostics, and Docker service controls.
Clues contain no flags, payloads, passwords, or completed solutions. Forensics
clues identify the corresponding evidence file.

Direct commands use styled dialogs when a terminal and whiptail are available:

```bash
labctl tracks
labctl labs --track FM
labctl labs --track OSINT
labctl labs --track P3
labctl resolve 'Private report forms'
labctl solved
labctl unsolved --track F
labctl hints F-01
labctl submit P1-01
labctl submit P1-01 --dry-run
```

New learners should start with the eight file manipulation exercises in
[`linux-files/README.md`](../linux-files/README.md). Prepare their workspace with
`python3 -B linux-files/lab.py prepare`, complete the requested output, and run
`python3 -B linux-files/lab.py check FM-01` to reveal the flag. Submit it with
`labctl submit FM-01`. The checker never changes scoring progress on its own.

Next, follow [`linux-ownership/README.md`](../linux-ownership/README.md) and run
`./linux-ownership/lab` from the checkout. Its single-command Docker launcher
opens the permissions sandbox; `task FO-01` and `check-ownership FO-01` work
inside. Submit each earned flag on the host with `labctl submit FO-01`.
The guide includes Docker installation, first launch, exit and fresh attempts.

For the three book fair investigations, find the reference code in the source
pack and wrap it in `MFANO{...}`. Use `labctl hints OSINT-01` for a clue and
`labctl submit OSINT-01` to score the first case. [Beginner OSINT guide](../osint/README.md)

For a first forensics case, read the print queue and submit its job ID in the
same format with `labctl submit F-08`. Use `labctl solved --track F` to see
your progress. [Print-room case files and instructions](../forensics/starter/README.md)

Use `labctl labs --track STEG` for the media club cases. Start with
`labctl hints STEG-01` and enter the recovered flag with `labctl submit STEG-01`.
Each clue links to a section of 0xRick's reference. [Steganography guide](../steganography/README.md)

`status` and `score` are aliases for the all-challenges progress view. Lists
accept `--limit` (default 50, range 1–1000) and `--offset` (default 0).
`labs --state all|solved|unsolved` filters by completion. IDs and exact titles
resolve without regard to letter case; partial title search is not implied.

Flags are read from a password box or one stdin line, never from a flag argument.
For scripts, provide `--flag-stdin`; this here-string uses an illustrative flag:

```bash
labctl --json submit P1-01 --flag-stdin --dry-run <<<'MFANO{your_flag_here}'
```

Use the password box for ordinary submissions so a flag does not enter shell
history. Flag contents are case-sensitive. Surrounding whitespace is trimmed;
uppercase text inside the braces is not converted automatically.

## Offline configuration and persistence

Scoring, discovery, progress, and clues require no Python, Docker, account,
authentication, or network. `doctor` reports `mode: "offline"` and an auth source
of `"not_required"`; there is no login or API token configuration.

Configuration comes from environment variables, followed by checkout defaults:

| Variable | Default | Purpose |
| --- | --- | --- |
| `LABCTL_ROOT` | Checkout containing the installed Bash command | Select another lab checkout, including its hashes and Compose file |
| `LABCTL_PROGRESS_FILE` | `$LABCTL_ROOT/.labprogress.json` | Select a different score file; its parent directory must exist |

Relative overrides resolve against the caller's working directory; absolute paths
are recommended for scripts. Challenge titles and clues come from
`cli/challenges.json` beside the installed command. `flags.sha256` remains the
authoritative registration of challenge IDs, categories, difficulty, and hashes.

The existing `{"solved": ["P1-01", ...]}` progress format is retained. Duplicate
IDs count once; retired IDs and additional existing fields are preserved on
writes. Read commands never rewrite progress. A stable `.labprogress.json.lock`
serializes writers, and updates replace the score file atomically with mode 0600.
A repeated correct submission does not rewrite the score file. Dry runs create
neither a progress file nor a lock.

Damaged JSON is reported and preserved rather than silently starting over.
Progress and lock symlinks are rejected; configure the real progress file path.
If a write fails, any `.labprogress.json.tmp.*` file is retained for recovery.
Intentional disposal of a score, lock, or recovery file should use Linux Trash,
for example `gio trash -- /exact/path`, after deciding the data is no longer needed.

`labctl.py` remains a legacy maintainer helper for existing imports and checks.
The documented Linux player interface and scoring implementation are Bash.

## JSON contract

`--json` can appear before or after the command. It emits one JSON document on
stdout, without ANSI escapes, prompts, flags, or stored hashes. The deliberate
exception is `audit`, which reveals its challenge flag only after a verified
vulnerable `requests` finding. All other commands avoid returning submitted flags.
Errors never echo the submitted flag. No credential configuration is involved.

Successful commands use a CLI envelope rather than an API pass-through:

```json
{"ok":true,"command":"status","data":{"labs":[],"total":0,"limit":50,"offset":0,"next_offset":null,"progress":{"total":0,"solved":0,"remaining":0,"next":null}}}
```

Failures have a stable code and human-readable message:

```json
{"ok":false,"error":{"code":"wrong_flag","message":"wrong flag for the selected challenge. Progress was not changed."}}
```

Examples by command family:

```bash
# Diagnostics: data.ready, data.dependencies, data.issues, data.auth
labctl --json doctor

# Discovery: data.tracks with per-track solved/remaining counts
labctl --json tracks

# Resolution: data.stage, including its stable id
labctl --json resolve 'The noticeboard'

# Collections: data.labs, total, limit, offset, next_offset, progress
labctl --json labs --track F --state unsolved --limit 3 --offset 0
labctl --json solved

# Exact read: data.stage with hint and optional evidence path
labctl --json hints F-01

# Write preview: data.stage, result, recorded, dry_run, progress
labctl --json submit P1-01 --flag-stdin --dry-run <<<'MFANO{your_flag_here}'

# Service preview: data.argv, data.dry_run
labctl --json start --dry-run

# Read-only escape hatch: data is the sanitized resource itself
labctl --json inspect stages
labctl --json inspect progress
labctl --json inspect hints
```

Submission results are `"solved"`, `"already_solved"`, or `"valid"` (preview).
`recorded` is true only when this invocation records a new solve. Progress counts
refer to the complete selected checkout, even when a list is filtered or paginated.
`next` is the first unsolved registered challenge, or null. `inspect` exposes
public stage metadata, normalized solved IDs, or gentle clues; it provides no
arbitrary shell execution, file access, or network request.

Exit 0 means success, including an empty list, duplicate solve, canceled dialog,
or valid preview. Exit 1 means a wrong flag, dependency/data problem, or failed
service command; exit 2 means invalid arguments or a missing interactive/input
requirement. `doctor` returns a diagnostic envelope with `ok: true` and
`data.ready: false`, but exits 1 when required setup or data needs attention.
`--help` is human-readable and `--version` also supports `--json`.

## Docker and audit helpers

```bash
labctl start                  # Build and start the local lab
labctl stop                   # Stop containers
labctl reset --dry-run        # Preview reseeding
labctl reset                  # Confirm in a terminal dialog
labctl reset --yes            # Explicit confirmation for scripts
labctl shell                  # Bash inside the web container
labctl audit                  # Requires pip-audit and advisory connectivity
```

The Bash helper tries the `docker compose` plugin, then `docker-compose`. It
always selects the lab's Compose file and project directory explicitly, including
when invoked outside the checkout. Reset reseeds mock server data and retains
flag progress. These commands never run automatically when opening a menu.
`--dry-run` previews each helper's exact argument array. An interactive shell
does not produce JSON; `shell --dry-run` does.

## Maintainer checks and companion skill

Install ShellCheck for linting and use the project's Python environment for tests:

```bash
sudo apt install -y shellcheck
make check
make test
```

The CLI tests invoke Bash as a subprocess and use synthetic flag tables. They
cover matching the selected challenge, persistence, legacy progress, corruption,
concurrent writers, bounded lists, command previews, installation from another
directory, and real whiptail submission/cancellation through a PTY.

`cli/skills/mfano-labctl/SKILL.md` is a small companion skill for future Codex
threads. `make install-skill` installs it under `~/.codex/skills/mfano-labctl` and
preserves any existing directory at that location. It starts with diagnostics
and ID discovery, then uses safe reads and explicit submission previews.
