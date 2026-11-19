#!/usr/bin/env bash
# Data and command layer for the Linux Bash CLI. No network is needed to score.

STAGES='[]'
METADATA='{"tracks":[],"challenges":{}}'
PROGRESS='{"solved":[]}'
SELECTED_STAGE=null
QUIET_ERRORS=false
LAST_ERROR=''
TRACK=''
STATE=all
LIMIT=50
OFFSET=0
DRY_RUN=false
FLAG_STDIN=false
CONFIRMED=false
POSITIONAL=()

error() {
    local code=$1 message=$2 exit_code=${3:-1}
    LAST_ERROR=$message
    if ! $QUIET_ERRORS; then
        if $JSON_MODE; then
            if command -v jq >/dev/null 2>&1; then
                jq -cn --arg code "$code" --arg message "$message" \
                    '{ok:false,error:{code:$code,message:$message}}'
            else
                printf '%s\n' '{"ok":false,"error":{"code":"missing_dependency","message":"Install jq: sudo apt install jq."}}'
            fi
        elif ${UI_READY:-false} && ! $PLAIN_MODE; then
            ui_message 'Action needs attention' "$message"
        else
            printf 'labctl: %s\n' "$message" >&2
        fi
    fi
    return "$exit_code"
}

require_command() {
    command -v "$1" >/dev/null 2>&1 || {
        error missing_dependency "Required command '$1' is missing. See cli/README.md for Linux packages."
        return 1
    }
}

usage() {
    cat <<'HELP'
MFANO // LAB CONTROL — Bash CLI for Linux

Usage: labctl [--json] COMMAND [OPTIONS]
       labctl                         Open the full-screen whiptail menu

Discovery and progress:
  tracks                              List tracks with solved/remaining counts
  labs [--track ID] [--state STATE]    List challenges (all, solved, unsolved)
  resolve ID_OR_TITLE                 Find a challenge's stable ID
  status | score                      Show progress and the next challenge
  solved | unsolved                   List solved or remaining challenges
  hints ID_OR_TITLE                   Show a gentle clue, when available
  doctor                              Check Linux tools, data, and progress
  inspect stages|progress|hints       Read sanitized local data as JSON

Flag submission:
  submit ID_OR_TITLE                  Enter a flag in a hidden password box
  submit ID --flag-stdin              Read one flag from stdin (no argv flag)
  submit ID --dry-run                 Validate without recording progress

Lab services:
  start | stop                        Start/build or stop the Docker lab
  reset [--yes]                       Reseed mock data; confirmation required
  shell                               Open Bash inside the web container
  audit                               Detect the vulnerable dependency
  start|stop|reset|shell|audit --dry-run  Preview the exact command

List options: --track ID, --limit N (default 50, max 1000), --offset N
Global options: --json, --no-color, --help, --version

Config: LABCTL_ROOT selects a checkout; LABCTL_PROGRESS_FILE selects a score file.
Scoring is offline. No account, authentication, Python, or Docker is required.
Install on PATH: make install-local (defaults to ~/.local/bin/labctl).
HELP
}

load_catalog() {
    [[ -r "$CATALOG_FILE" && -f "$CATALOG_FILE" ]] || {
        error missing_catalog 'The challenge metadata file is missing or unreadable.'
        return 1
    }
    if ! METADATA=$(jq -ecs '
        if length == 1 and (.[0] |
            type == "object" and (.tracks | type == "array") and
            (.challenges | type == "object") and
            all(.tracks[]; (.id | type == "string") and (.title | type == "string")) and
            ((.tracks | map(.id) | unique | length) == (.tracks | length)) and
            all(.challenges[]; (.title | type == "string") and
                (.hint == null or (.hint | type == "string")) and
                (.evidence == null or (.evidence | type == "string"))))
        then .[0] else error("invalid metadata") end
    ' "$CATALOG_FILE" 2>/dev/null); then
        error invalid_catalog 'The challenge metadata file is damaged. Repair it before using the CLI.'
        return 1
    fi
    [[ -r "$FLAGS_FILE" && -f "$FLAGS_FILE" ]] || {
        error missing_flags 'flags.sha256 is missing or unreadable in the selected checkout.'
        return 1
    }
    if ! STAGES=$(jq -Rnc --argjson metadata "$METADATA" '
        [inputs | gsub("^\\s+|\\s+$"; "") |
            select(length > 0 and (startswith("#") | not)) | split(":") |
            if length != 4 or (.[0] | test("^[A-Za-z][A-Za-z0-9_-]*$") | not) or
                (.[1] | test("^[a-fA-F0-9]{64}$") | not) or .[2] == "" or .[3] == ""
            then error("invalid stage record")
            else {id:.[0],hash:(.[1] | ascii_downcase),category:.[2],difficulty:.[3]} end |
            . as $stage | (.id | split("-")[0]) as $track |
            . + {track:$track,
                track_title:([$metadata.tracks[] | select(.id == $track) | .title][0] // $track),
                title:($metadata.challenges[$stage.id].title // $stage.id),
                hint:($metadata.challenges[$stage.id].hint // null),
                evidence:($metadata.challenges[$stage.id].evidence // null)}
        ] as $stages |
        if ($stages | map(.id) | unique | length) != ($stages | length) or
            ($stages | map(.hash) | unique | length) != ($stages | length)
        then error("duplicate stages") else $stages end
    ' < "$FLAGS_FILE" 2>/dev/null); then
        error invalid_flags 'flags.sha256 contains a damaged or duplicate record. Progress has been preserved.'
        return 1
    fi
}

load_progress() {
    PROGRESS='{"solved":[]}'
    if [[ -L "$PROGRESS_FILE" ]]; then
        error unsafe_progress 'The progress path is a symlink. Set LABCTL_PROGRESS_FILE to its real file instead.'
        return 1
    fi
    [[ -e "$PROGRESS_FILE" ]] || return 0
    [[ -f "$PROGRESS_FILE" && -r "$PROGRESS_FILE" ]] || {
        error unreadable_progress 'The progress path must be a readable JSON file. Existing data has been preserved.'
        return 1
    }
    if ! PROGRESS=$(jq -ecs '
        if length == 1 and (.[0] | type == "object" and
            (.solved | type == "array") and all(.solved[]; type == "string"))
        then .[0] | .solved |= (reduce .[] as $id ([];
            if index($id) == null then . + [$id] else . end))
        else error("invalid progress") end
    ' "$PROGRESS_FILE" 2>/dev/null); then
        error invalid_progress 'The progress JSON is damaged. Repair or move it aside before submitting; it has not been overwritten.'
        return 1
    fi
}

update_statuses() {
    STAGES=$(jq -c --argjson progress "$PROGRESS" '
        map(. as $stage | . + {status:
            (if ($progress.solved | index($stage.id)) != null then "solved" else "unsolved" end)})
    ' <<< "$STAGES")
}

load_state() {
    load_catalog || return $?
    load_progress || return $?
    update_statuses
}

summary_json() {
    jq -c '
        length as $total | (map(select(.status == "solved")) | length) as $solved |
        {total:$total,solved:$solved,remaining:($total-$solved),
            next:(map(select(.status == "unsolved") | del(.hash,.hint))[0] // null)}
    ' <<< "$STAGES"
}

tracks_json() {
    jq -cn --argjson stages "$STAGES" --argjson metadata "$METADATA" '
        def counts($id; $title; $labs):
            ($labs | length) as $total |
            ($labs | map(select(.status == "solved")) | length) as $solved |
            {id:$id,title:$title,total:$total,solved:$solved,remaining:($total-$solved)};
        [$metadata.tracks[] | . as $track |
            [$stages[] | select(.track == $track.id)] as $labs |
            select($labs | length > 0) | counts($track.id; $track.title; $labs)] +
        [$stages | group_by(.track)[] | . as $labs | .[0] as $first |
            select(($metadata.tracks | map(.id) | index($first.track)) == null) |
            counts($first.track; $first.track_title; $labs)]
    '
}

resolve_stage() {
    local matches
    matches=$(jq -c --arg query "$1" '
        ($query | ascii_downcase) as $query |
        map(select((.id | ascii_downcase) == $query or (.title | ascii_downcase) == $query))
    ' <<< "$STAGES") || return 1
    case $(jq 'length' <<< "$matches") in
        0) error unknown_challenge 'Challenge not found. Run labctl labs to discover IDs and titles.' 2; return 2 ;;
        1) SELECTED_STAGE=$(jq -c '.[0]' <<< "$matches") ;;
        *) error ambiguous_challenge 'That title matches multiple challenges. Use a challenge ID.' 2; return 2 ;;
    esac
}

resolve_track() {
    [[ -n "$TRACK" ]] || return 0
    TRACK=$(tracks_json | jq -r --arg query "$TRACK" '
        ($query | ascii_downcase) as $query |
        [.[] | select((.id | ascii_downcase) == $query or (.title | ascii_downcase) == $query) | .id][0] // ""
    ') || return 1
    [[ -n "$TRACK" ]] || {
        error unknown_track 'Track not found. Run labctl tracks to discover track IDs.' 2
        return 2
    }
}

emit() {
    local family=$1 data=$2
    if $JSON_MODE; then
        jq -cn --arg command "$COMMAND" --argjson data "$data" '{ok:true,command:$command,data:$data}'
        return
    fi
    if [[ -t 0 && -t 1 ]] && ! $PLAIN_MODE && [[ "$family" != inspect ]] &&
        command -v whiptail >/dev/null 2>&1; then
        ui_setup || return $?
        ui_present "$family" "$data"
        return
    fi
    case "$family" in
        labs)
            printf '%-8s %-31s %-13s %s\n' 'STAGE' 'CHALLENGE' 'DIFFICULTY' 'STATUS'
            while IFS=$'\t' read -r id title difficulty status; do
                printf '%-8s %-31.31s %-13.13s %s\n' "$id" "$title" "$difficulty" "$status"
            done < <(jq -r '.labs[] | [.id,.title,.difficulty,.status] | @tsv' <<< "$data")
            display_progress "$data"
            ;;
        tracks)
            printf '%-8s %-32s %s\n' 'TRACK' 'THEME' 'PROGRESS'
            while IFS=$'\t' read -r id title solved total remaining; do
                printf '%-8s %-32.32s %s/%s solved, %s remaining\n' "$id" "$title" "$solved" "$total" "$remaining"
            done < <(jq -r '.tracks[] | [.id,.title,.solved,.total,.remaining] | @tsv' <<< "$data")
            ;;
        resolve)
            jq -r '.stage | "\(.id)  \(.title)\n\(.category) | \(.difficulty) | \(.status)"' <<< "$data"
            ;;
        hints)
            jq -r '.stage | "\(.id)  \(.title)\n\(.hint // "No clue has been published for this challenge yet.")" +
                (if .evidence != null then "\nEvidence: " + .evidence else "" end)' <<< "$data"
            ;;
        submit)
            jq -r 'if .result == "solved" then "Correct! Stage \(.stage.id) solved."
                elif .result == "already_solved" then "Stage \(.stage.id) is already solved."
                else "Valid flag for \(.stage.id). Preview only; progress was not changed." end' <<< "$data"
            display_progress "$data"
            ;;
        doctor)
            jq -r '"MFANO Linux CLI \(.version) | offline scoring | no authentication required",
                (.dependencies[] | "\(.name): \(if .available then "available" else "missing" end)\(if .required then " (required)" else " (optional)" end)"),
                "\(.challenge_count) challenges registered",
                (.issues[]), (if .ready then "Ready." else "Setup needs attention." end)' <<< "$data"
            ;;
        lifecycle)
            jq -r 'if .dry_run then "Preview: " + (.argv | @sh) else .output end' <<< "$data"
            ;;
        audit)
            jq -r 'if .dry_run then "Preview: " + (.argv | @sh)
                else (.report | tojson),
                    (if .flag != null then "Outdated dependency confirmed. Flag: " + .flag
                    else "No known-vulnerable requests dependency detected." end) end' <<< "$data"
            ;;
        inspect) jq . <<< "$data" ;;
    esac
}

display_progress() {
    jq -r '.progress | "\(.solved) / \(.total) solved | \(.remaining) remaining",
        (if .next != null then "Next stage: \(.next.id) (\(.next.category), \(.next.difficulty))"
        elif .total == 0 then "No challenges registered." else "All challenges solved. Well done!" end)' <<< "$1"
}

cmd_labs() {
    load_state || return $?
    resolve_track || return $?
    local data
    data=$(jq -cn --argjson stages "$STAGES" --arg track "$TRACK" --arg state "$STATE" \
        --argjson limit "$LIMIT" --argjson offset "$OFFSET" --argjson progress "$(summary_json)" '
        [$stages[] | select(($track == "" or .track == $track) and
            ($state == "all" or .status == $state)) | del(.hash,.hint)] as $labs |
        {labs:$labs[$offset:($offset+$limit)],total:($labs | length),limit:$limit,offset:$offset,
            next_offset:(if ($offset+$limit) < ($labs | length) then $offset+$limit else null end),
            progress:$progress}
    ') || return 1
    emit labs "$data"
}

cmd_tracks() {
    load_state || return $?
    emit tracks "$(jq -cn --argjson tracks "$(tracks_json)" '{tracks:$tracks}')"
}

cmd_resolve() {
    load_state || return $?
    resolve_stage "${POSITIONAL[0]}" || return $?
    emit resolve "$(jq -cn --argjson stage "$SELECTED_STAGE" '{stage:($stage | del(.hash,.hint))}')"
}

cmd_hints() {
    load_state || return $?
    resolve_stage "${POSITIONAL[0]}" || return $?
    emit hints "$(jq -cn --argjson stage "$SELECTED_STAGE" '{stage:($stage | del(.hash))}')"
}

cmd_inspect() {
    load_state || return $?
    local data
    case "${POSITIONAL[0]}" in
        stages) data=$(jq -c 'map(del(.hash,.hint))' <<< "$STAGES") ;;
        progress) data=$(jq -c '{solved}' <<< "$PROGRESS") ;;
        hints) data=$(jq -c 'map({id,title,hint,evidence})' <<< "$STAGES") ;;
        *) error invalid_resource 'inspect accepts stages, progress, or hints.' 2; return 2 ;;
    esac
    emit inspect "$data"
}

submission_result() {
    local result=$1 recorded=$2 id=$3
    emit submit "$(jq -cn --argjson stages "$STAGES" --arg id "$id" --arg result "$result" \
        --argjson recorded "$recorded" --argjson dry_run "$DRY_RUN" --argjson progress "$(summary_json)" '
        {stage:([$stages[] | select(.id == $id) | del(.hash,.hint)][0]),
            result:$result,recorded:$recorded,dry_run:$dry_run,progress:$progress}
    ')"
}

record_submission() (
    # Lock one stable inode; reload under the lock to avoid lost concurrent solves.
    local id=$1 lock=$PROGRESS_FILE.lock fd next_progress temporary
    umask 077
    [[ ! -L "$lock" ]] || { error unsafe_lock 'The progress lock path is a symlink.'; return 1; }
    exec {fd}>>"$lock" || { error progress_write_failed 'Cannot open the progress lock. Check directory permissions.'; return 1; }
    flock -w 10 "$fd" || { error progress_locked 'Progress is busy. Try submitting again shortly.'; return 1; }
    load_progress || return $?
    update_statuses || return $?
    if jq -e --arg id "$id" '.solved | index($id) != null' <<< "$PROGRESS" >/dev/null; then
        flock -u "$fd" || return 1
        submission_result already_solved false "$id"
        return
    fi
    next_progress=$(jq --arg id "$id" '.solved += [$id]' <<< "$PROGRESS") || return 1
    temporary=$(mktemp "$PROGRESS_FILE.tmp.XXXXXX") || {
        error progress_write_failed 'Cannot create a progress update. Existing progress has been preserved.'
        return 1
    }
    if ! printf '%s\n' "$next_progress" > "$temporary"; then
        error progress_write_failed 'Cannot write the progress update. The temporary file was preserved for recovery.'
        return 1
    fi
    if ! mv -T -- "$temporary" "$PROGRESS_FILE"; then
        error progress_write_failed 'Cannot save the progress update. The temporary file was preserved for recovery.'
        return 1
    fi
    PROGRESS=$next_progress
    update_statuses || return $?
    flock -u "$fd" || return 1
    submission_result solved true "$id"
)

cmd_submit() {
    load_state || return $?
    resolve_stage "${POSITIONAL[0]}" || return $?
    require_command sha256sum || return $?
    local flag='' digest expected id
    id=$(jq -r '.id' <<< "$SELECTED_STAGE")
    expected=$(jq -r '.hash' <<< "$SELECTED_STAGE")
    if $FLAG_STDIN; then
        IFS= read -r -n 4097 flag || [[ -n "$flag" ]] || {
            error missing_flag 'No flag was supplied on stdin.' 2
            return 2
        }
    elif [[ -t 0 && -t 1 ]] && ! $JSON_MODE; then
        ui_setup || return $?
        ui_read_flag "$id" || return 0
        flag=$UI_FLAG
        UI_FLAG=''
    else
        error missing_flag 'Use --flag-stdin to supply a flag without an interactive terminal.' 2
        return 2
    fi
    # Match the legacy scorer's whitespace trimming without changing flag case.
    flag=${flag#"${flag%%[![:space:]]*}"}
    flag=${flag%"${flag##*[![:space:]]}"}
    if [[ -z "$flag" ]] || (( ${#flag} > 4096 )); then
        flag=''
        error invalid_flag 'Enter one non-empty flag of at most 4096 characters.' 2
        return 2
    fi
    digest=$(printf '%s' "$flag" | sha256sum) || return 1
    flag=''
    digest=${digest%% *}
    [[ "$digest" == "$expected" ]] || {
        error wrong_flag 'wrong flag for the selected challenge. Progress was not changed.'
        return 1
    }
    if $DRY_RUN; then
        if jq -e --arg id "$id" '.solved | index($id) != null' <<< "$PROGRESS" >/dev/null; then
            submission_result already_solved false "$id"
        else
            submission_result valid false "$id"
        fi
        return
    fi
    require_command flock || return $?
    record_submission "$id"
}

cmd_doctor() {
    local dependencies='[]' issues='[]' tool available required ready=true count=0 data parent
    for tool in jq sha256sum flock whiptail docker docker-compose pip-audit; do
        available=false
        command -v "$tool" >/dev/null 2>&1 && available=true
        required=false
        case "$tool" in jq|sha256sum|flock) required=true ;; esac
        dependencies=$(jq -cn --argjson list "$dependencies" --arg name "$tool" \
            --argjson available "$available" --argjson required "$required" \
            '$list + [{name:$name,available:$available,required:$required}]')
        if $required && ! $available; then
            ready=false
            issues=$(jq -cn --argjson list "$issues" --arg issue "Install the required '$tool' command." '$list + [$issue]')
        fi
    done
    QUIET_ERRORS=true
    if load_catalog; then count=$(jq length <<< "$STAGES"); else
        ready=false
        issues=$(jq -cn --argjson list "$issues" --arg issue "$LAST_ERROR" '$list + [$issue]')
    fi
    if ! load_progress; then
        ready=false
        issues=$(jq -cn --argjson list "$issues" --arg issue "$LAST_ERROR" '$list + [$issue]')
    fi
    QUIET_ERRORS=false
    parent=$(dirname -- "$PROGRESS_FILE")
    if [[ ! -d "$parent" || ! -w "$parent" ]] ||
        [[ -e "$PROGRESS_FILE" && ! -w "$PROGRESS_FILE" ]] ||
        [[ -L "$PROGRESS_FILE.lock" ]] ||
        [[ -e "$PROGRESS_FILE.lock" && ! -w "$PROGRESS_FILE.lock" ]]; then
        ready=false
        issues=$(jq -cn --argjson list "$issues" '$list + ["The progress directory or lock is not writable; check LABCTL_PROGRESS_FILE."]')
    fi
    data=$(jq -cn --arg version "$VERSION" --arg root "$LAB_ROOT" --arg progress_file "$PROGRESS_FILE" \
        --argjson dependencies "$dependencies" --argjson issues "$issues" --argjson ready "$ready" \
        --argjson count "$count" '
        {version:$version,mode:"offline",network_required:false,auth:{required:false,source:"not_required"},
            root:$root,progress_file:$progress_file,challenge_count:$count,fixture_data_found:($count > 0),
            menu_available:([$dependencies[] | select(.name == "whiptail") | .available][0]),
            dependencies:$dependencies,ready:$ready,issues:$issues}
    ') || return 1
    emit doctor "$data"
    $ready
}

COMPOSE=()
compose_command() {
    COMPOSE=()
    if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
        COMPOSE=(docker compose)
    elif command -v docker-compose >/dev/null 2>&1; then
        COMPOSE=(docker-compose)
    else
        error missing_compose 'Docker Compose was not found. On Kali/Debian install docker.io and docker-compose.'
        return 1
    fi
}

cmd_lifecycle() {
    compose_command || return $?
    local parts=() argv output rc
    case "$COMMAND" in
        start) parts=(up -d --build) ;;
        stop) parts=(down) ;;
        reset) parts=(exec -T web python seed.py) ;;
        shell) parts=(exec web bash) ;;
    esac
    argv=$(jq -cn --args '$ARGS.positional' -- "${COMPOSE[@]}" --project-directory "$LAB_ROOT" \
        -f "$LAB_ROOT/docker-compose.yml" "${parts[@]}") || return 1
    if $DRY_RUN; then
        emit lifecycle "$(jq -cn --argjson argv "$argv" '{dry_run:true,argv:$argv}')"
        return
    fi
    if [[ "$COMMAND" == reset ]] && ! $CONFIRMED; then
        if [[ -t 0 && -t 1 ]] && ! $JSON_MODE; then
            ui_setup || return $?
            ui_confirm_reset || return 0
        else
            error confirmation_required 'reset reseeds the mock database. Use --yes after reviewing reset --dry-run.' 2
            return 2
        fi
    fi
    if [[ "$COMMAND" == shell ]]; then
        if $JSON_MODE; then error interactive_command 'shell needs an interactive terminal; use --dry-run for JSON.' 2; return 2; fi
        "${COMPOSE[@]}" --project-directory "$LAB_ROOT" -f "$LAB_ROOT/docker-compose.yml" "${parts[@]}"
        return $?
    fi
    output=$("${COMPOSE[@]}" --project-directory "$LAB_ROOT" -f "$LAB_ROOT/docker-compose.yml" "${parts[@]}" 2>&1)
    rc=$?
    if (( rc != 0 )); then
        if ! $JSON_MODE; then printf '%s\n' "$output" >&2; fi
        error compose_failed 'Docker Compose failed. Check Docker daemon access and the lab service configuration.'
        return 1
    fi
    emit lifecycle "$(jq -cn --argjson argv "$argv" --arg output "$output" '{dry_run:false,argv:$argv,output:$output}')"
}

cmd_audit() {
    local argv report rc flag=null
    argv=$(jq -cn --args '$ARGS.positional' -- pip-audit -r "$LAB_ROOT/requirements.txt" \
        --format json --progress-spinner off) || return 1
    if $DRY_RUN; then
        emit audit "$(jq -cn --argjson argv "$argv" '{dry_run:true,argv:$argv}')"
        return
    fi
    require_command pip-audit || return $?
    report=$(pip-audit -r "$LAB_ROOT/requirements.txt" --format json --progress-spinner off 2>/dev/null)
    rc=$?
    if (( rc > 1 )) || ! jq -e 'type == "object" and (.dependencies | type == "array") and
        all(.dependencies[]; (.name | type == "string") and
            ((.skip_reason | type == "string") or
            ((.version | type == "string") and (.vulns | type == "array"))))' \
        <<< "$report" >/dev/null 2>&1; then
        error audit_failed 'pip-audit could not complete a dependency report. Check its installation and advisory connectivity.'
        return 1
    fi
    # A nonzero process exit or a mention of requests is insufficient evidence.
    if jq -e 'any(.dependencies[]; (.name | ascii_downcase) == "requests" and (.vulns // [] | length) > 0)' \
        <<< "$report" >/dev/null; then
        flag='"MFANO{p1p_4ud1t_f0und_th3_0ld_r3qu3sts}"'
    fi
    emit audit "$(jq -cn --argjson argv "$argv" --argjson report "$report" --argjson flag "$flag" \
        '{dry_run:false,argv:$argv,report:$report,flag:$flag}')"
}

parse_options() {
    local option value
    while (( $# > 0 )); do
        option=$1
        shift
        case "$option" in
            --track|--state|--limit|--offset)
                case "$COMMAND:$option" in
                    labs:*|status:--track|status:--limit|status:--offset|score:--track|score:--limit|score:--offset|solved:--track|solved:--limit|solved:--offset|unsolved:--track|unsolved:--limit|unsolved:--offset) ;;
                    *) error invalid_option 'That option does not apply to this command. Run labctl --help.' 2; return 2 ;;
                esac
                (( $# > 0 )) || { error missing_option_value 'An option is missing its value.' 2; return 2; }
                value=$1
                shift
                case "$option" in
                    --track) TRACK=$value ;;
                    --state) STATE=$value ;;
                    --limit)
                        [[ "$value" =~ ^[0-9]{1,4}$ ]] && (( 10#$value >= 1 && 10#$value <= 1000 )) || {
                            error invalid_limit '--limit must be between 1 and 1000.' 2; return 2;
                        }
                        LIMIT=$((10#$value))
                        ;;
                    --offset)
                        [[ "$value" =~ ^[0-9]{1,9}$ ]] || {
                            error invalid_offset '--offset must be a non-negative integer of at most nine digits.' 2; return 2;
                        }
                        OFFSET=$((10#$value))
                        ;;
                esac
                ;;
            --dry-run)
                case "$COMMAND" in submit|start|stop|reset|shell|audit) DRY_RUN=true ;;
                    *) error invalid_option '--dry-run applies to submit and lab service commands.' 2; return 2 ;; esac
                ;;
            --flag-stdin)
                [[ "$COMMAND" == submit ]] || { error invalid_option '--flag-stdin applies to submit.' 2; return 2; }
                FLAG_STDIN=true
                ;;
            --yes)
                [[ "$COMMAND" == reset ]] || { error invalid_option '--yes applies to reset.' 2; return 2; }
                CONFIRMED=true
                ;;
            --) POSITIONAL+=("$@"); break ;;
            -*) error invalid_option 'Unknown option. Run labctl --help.' 2; return 2 ;;
            *) POSITIONAL+=("$option") ;;
        esac
    done
    case "$STATE" in all|solved|unsolved) ;; *) error invalid_state '--state must be all, solved, or unsolved.' 2; return 2 ;; esac
    case "$COMMAND" in
        submit|resolve|hints|inspect)
            (( ${#POSITIONAL[@]} == 1 )) || { error invalid_arguments 'This command needs exactly one challenge ID/title or inspect resource.' 2; return 2; }
            ;;
        *) (( ${#POSITIONAL[@]} == 0 )) || { error invalid_arguments 'This command takes no positional arguments.' 2; return 2; } ;;
    esac
}

main() {
    local arg
    for arg in "$@"; do
        case "$arg" in --help|-h|help) usage; return 0 ;; esac
    done
    COMMAND=${1:-menu}
    (( $# == 0 )) || shift
    if [[ "$COMMAND" == --version ]]; then
        if $JSON_MODE; then printf '{"ok":true,"data":{"version":"%s"}}\n' "$VERSION";
        else printf 'labctl %s\n' "$VERSION"; fi
        return 0
    fi
    require_command jq || return $?
    case "$COMMAND" in
        menu|tracks|labs|status|score|solved|unsolved|resolve|hints|inspect|submit|doctor|start|stop|reset|shell|audit) ;;
        *) error unknown_command 'Unknown command. Run labctl --help.' 2; return 2 ;;
    esac
    parse_options "$@" || return $?
    case "$COMMAND" in
        menu)
            if $JSON_MODE; then error interactive_command 'Use structured commands such as --json status; menu requires a terminal.' 2; return 2; fi
            ui_menu
            ;;
        labs|status|score) cmd_labs ;;
        solved) STATE=solved; cmd_labs ;;
        unsolved) STATE=unsolved; cmd_labs ;;
        tracks) cmd_tracks ;;
        resolve) cmd_resolve ;;
        hints) cmd_hints ;;
        inspect) cmd_inspect ;;
        submit) cmd_submit ;;
        doctor) cmd_doctor ;;
        start|stop|reset|shell) cmd_lifecycle ;;
        audit) cmd_audit ;;
    esac
}
