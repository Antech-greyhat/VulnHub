#!/usr/bin/env bash
# Sourced by the scanner's interactive Bash session.
PS1='nmap-lab:\w# '
export PS1

targets() {
    printf '%s\n' 'Practice network: 172.30.77.0/28' \
        'Service targets: 172.30.77.10 and 172.30.77.11' \
        'This scanner: 172.30.77.2; the bridge gateway may also answer discovery.'
}

task() {
    if [[ $# != 1 || ! $1 =~ ^NM-(0[1-9]|1[0-2])$ ]]; then
        printf '%s\n' 'Usage: task NM-01 (through NM-12)' >&2
        return 2
    fi
    awk -v heading="## $1:" '
        index($0, heading) == 1 {show=1; print; next}
        show && /^## / {exit}
        show {print}
    ' /practice/README.md
}

printf '\n%s\n' 'Mfano Nmap enumeration practice' \
    'Type targets for scope, task NM-01 to begin, or less README.md for the guide.' \
    'Save XML in scans/. Check and submit flags in a second HOST terminal.' \
    'Type exit to leave the shell; ./nmap-enumeration/lab stop pauses the services.'
targets
