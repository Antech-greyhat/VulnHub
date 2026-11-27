#!/usr/bin/env bash
umask 027
export PS1='(4NT3CH ownership) learner:\w\$ '

task() {
    if [[ $# -ne 1 || ! "$1" =~ ^FO-0[1-7]$ ]]; then
        printf '%s\n' 'Usage: task FO-01 (through FO-07)' >&2
        return 2
    fi
    cat "/practice/$1/TASK.txt"
}

cat <<'WELCOME'

4NT3CH VULN3R4BL3 L4B | Linux permissions and ownership
You are inside the sandbox as learner.
Practice files are in /practice. No host folders or ports are shared.

  task FO-01                Read the first task
  cd /practice/FO-01        Work in its directory
  ls -l                     Inspect ownership and permissions
  check-ownership FO-01     Check your work and reveal its flag
  less ~/README.md          Read all tasks (q exits the pager)
  exit                      Return to the host; this attempt is discarded

Record flags on the HOST with ./labctl submit FO-01 in a second terminal.
Your host score is kept separately. The next launch starts fresh practice files.
WELCOME
