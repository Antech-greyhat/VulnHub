# Linux file discovery

Seven beginner exercises practise the skills missing from our existing Linux
tracks: unusual filenames, hidden entries, identifying text, combining file
search conditions, and finding a line that occurs once. Start after
[file manipulation](../linux-files/README.md) and
[permissions and ownership](../linux-ownership/README.md).

These are local school-themed exercises inspired by the Bandit writeups linked
below. Each contains its own `MFANO{...}` flag, scored by the existing `labctl`.

## Start the sandbox

You need Docker for the practice shell. It supplies separate Unix accounts for
the owner/group search. The sandbox includes Bash, coreutils, `find`, `file`, and
`less`; you do not need to install these tools on your host.

If this is your first Docker lab, follow the numbered
[Docker setup guide](../linux-ownership/README.md#first-time-docker-setup).
Check `docker info`, then run these commands from the VulnHub checkout:

```bash
./linux-discovery/lab
```

The first build needs internet to download Debian and the tools. The learner
shell runs with networking disabled, limited resources, and no host folders or
ports shared. You are logged in as `learner`; practice files live in `/practice`.

```bash
task LD-01
cd /practice/LD-01
ls
```

Read a task with `task LD-01` through `task LD-07`. Each exercise also has a
`TASK.txt`. Recover its flag from the files and copy the complete value through
the closing brace. In a **second terminal on your host**, from this checkout:

```bash
./labctl submit LD-01
./labctl labs --track LD
./labctl hints LD-04
./labctl status
```

After submitting, move to the next exercise's directory inside the sandbox.
The files are read-only; use pipes or `/tmp` for any working notes. Read the
full guide with `less ~/README.md` (`q` closes it). Type `exit` to return to
the host. Each launch starts fresh practice files; host scores survive.

`./linux-discovery/lab --help` shows usage without contacting Docker.
`./linux-discovery/lab build` prepares the image without opening a shell.
If Docker is stopped, use `sudo systemctl start docker`. For socket permission
errors, follow the group membership and login steps in the setup guide.

## LD-01: The single dash

Work in `/practice/LD-01`. A school note is stored in a file named `-`.
Read that file and recover its flag. Think about how a program interprets a
filename that also has a special meaning for standard input.

Tools to explore: `ls`, `cat`, relative paths, input redirection.

## LD-02: The awkward handover name

Work in `/practice/LD-02`. Read the file whose name contains spaces and begins
with two dashes. Keep the filename together as one argument and account for
option parsing.

Tools to explore: `ls`, `cat`, shell quoting, relative paths, end-of-options.

## LD-03: The apparently empty folder

Work in `/practice/LD-03`. The `inhere` directory looks empty in an ordinary
listing, but it contains a hidden school note. Discover and read that note.

Tools to explore: `ls` listing options, `cd`, `cat`.

## LD-04: The readable record

Work in `/practice/LD-04`. The `inhere` directory contains ten dash-prefixed
files. One is plain ASCII text; the others contain binary data. Identify the
text file before printing it, then recover its flag.

Tools to explore: `file`, shell globs, `cat`, relative paths.

## LD-05: The exact archive record

Work in `/practice/LD-05`. Search `inhere` and its subdirectories for a regular
file that is **exactly 1033 bytes**, is **not executable by learner**, and
contains **plain text**. Several files meet only part of those conditions.
Read the matching record and recover the flag within it.

Tools to explore: `find`, byte-size tests, executable tests, `file`, pipes.

## LD-06: The misplaced teacher record

Work in `/practice/LD-06`. Somewhere below `system` is a regular file owned by
user **teacher**, with owning group **archive**, and size **33 bytes**. Find it
and read its flag. Other records have a different owner, group, or size.

Some directories are restricted. Permission errors and matching paths use
different output streams; decide which stream you need to inspect. Hiding an
error does not change your access rights.

Tools to explore: `find`, owner/group tests, byte-size tests, stderr redirection.

## LD-07: The line that occurs once

Work in `/practice/LD-07`. `data.txt` contains shuffled mock flag-shaped records.
Every record repeats except one. Recover the line that occurs **exactly once**;
keeping one copy of every distinct line does not meet the task.

Tools to explore: `sort`, `uniq`, pipes, occurrence counts.

## Bandit coverage and credit

The [reference writeup repository](https://github.com/Antech-greyhat/OverTheWireBandit-Writeup)
contains levels 0–8 as reviewed on 23 November 2026. The level number follows
the starting account in those writeups.

| Writeup level | Skill | Local coverage |
| --- | --- | --- |
| 0 | Read a file | Already covered by FM-01; skipped |
| 1 | A file named `-` | LD-01 |
| 2 | Spaces and leading dashes | LD-02 |
| 3 | Hidden files | LD-03 |
| 4 | Identify the readable file | LD-04 |
| 5 | File size and executable status | LD-05 |
| 6 | Search by owner, group, and size | LD-06 |
| 7 | Search for a known entry | Already covered by FM-03 and FM-06; skipped |
| 8 | A line that occurs once | LD-07 |

FM-08 already introduces sorting before a join; LD-07 adds occurrence counting.
FO teaches changing ownership; LD-06 adds searching with existing ownership.
The local Docker shell supplies the practice environment. For Bandit's SSH
setup, follow the [official starting guide](https://overthewire.org/wargames/bandit/bandit0.html).

[Bandit](https://overthewire.org/wargames/bandit/) is created and hosted by the
[OverTheWire community](https://overthewire.org/). These exercises use original
mock data and local flags.
