#!/usr/bin/env bash
umask 027
export LC_ALL=C
export PS1='(4NT3CH discovery) learner:\w\$ '

task() {
    if [[ $# -ne 1 || ! "$1" =~ ^LD-0[1-7]$ ]]; then
        printf '%s\n' 'Usage: task LD-01 (through LD-07)' >&2
        return 2
    fi
    cat "/practice/$1/TASK.txt"
}

cat <<'WELCOME'

4NT3CH VULN3R4BL3 L4B | Linux file discovery
You are inside the sandbox as learner.
Practice files are in /practice. No host folders or ports are shared.

  task LD-01                Read the first task
  cd /practice/LD-01        Work in its directory
  ls                        Explore the practice files
  less ~/README.md          Read all tasks (q exits the pager)
  exit                      Return to the host; this attempt is discarded

Find a flag in each exercise's files. Copy the complete MFANO{...} value.
Record it on the HOST with ./labctl submit LD-01 in a second terminal.
Host progress is kept separately. Each new launch starts fresh practice files.
WELCOME
