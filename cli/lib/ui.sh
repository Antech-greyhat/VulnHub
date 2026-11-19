#!/usr/bin/env bash
# libnewt/whiptail provides keyboard navigation, hidden input, and themed dialogs.

UI_WIDTH=76
UI_HEIGHT=22
UI_LIST_HEIGHT=8
UI_CHOICE=''
UI_FLAG=''
UI_TRACK=''
UI_STAGE=''
UI_READY=false
UI_BACKTITLE='MFANO HIGH SCHOOL | Linux lab console | Offline scoring'

ui_setup() {
    require_command whiptail || return $?
    [[ -t 0 && -t 1 ]] || {
        error terminal_required 'The menu needs an interactive terminal. Use labctl --json status for scripts.' 2
        return 2
    }
    [[ -n ${TERM:-} && ${TERM:-} != dumb ]] || {
        error terminal_required 'Use a terminal with TERM set, for example xterm-256color.' 2
        return 2
    }
    local rows cols
    rows=$(tput lines 2>/dev/null) || rows=24
    cols=$(tput cols 2>/dev/null) || cols=80
    [[ "$rows" =~ ^[0-9]+$ ]] || rows=24
    [[ "$cols" =~ ^[0-9]+$ ]] || cols=80
    if (( rows < 20 || cols < 64 )); then
        error terminal_too_small 'Resize the terminal to at least 64 columns by 20 rows, or use the direct commands.' 2
        return 2
    fi
    UI_HEIGHT=$((rows-2))
    UI_WIDTH=$((cols-4))
    (( UI_HEIGHT <= 32 )) || UI_HEIGHT=32
    (( UI_WIDTH <= 108 )) || UI_WIDTH=108
    UI_LIST_HEIGHT=$((UI_HEIGHT-14))
    (( UI_LIST_HEIGHT <= 10 )) || UI_LIST_HEIGHT=10
    (( UI_LIST_HEIGHT >= 3 )) || UI_LIST_HEIGHT=3
    if [[ -z ${NEWT_COLORS:-} ]]; then
        if $PLAIN_MODE; then
            NEWT_COLORS=$'root=white,black\nwindow=white,black\nborder=white,black\ntitle=white,black\nbutton=black,white\nactbutton=black,white\nlistbox=white,black\nactlistbox=black,white\ntextbox=white,black\nentry=white,black\nshadow=black,black'
        else
            NEWT_COLORS=$'root=white,black\nwindow=white,black\nborder=cyan,black\ntitle=green,black\nroottext=green,black\nbutton=black,cyan\nactbutton=black,green\ncompactbutton=black,cyan\nlistbox=white,black\nactlistbox=black,cyan\nsellistbox=green,black\nactsellistbox=black,green\ntextbox=white,black\nacttextbox=white,black\nentry=white,black\nlabel=cyan,black\nemptyscale=gray,black\nfullscale=green,black\nhelpline=white,black\nshadow=black,black'
        fi
        export NEWT_COLORS
    fi
    UI_READY=true
}

ui_message() {
    local line visual_lines=0 text_width=$((UI_WIDTH-8)) options=()
    while IFS= read -r line; do
        if [[ -z "$line" ]]; then
            visual_lines=$((visual_lines+1))
        else
            visual_lines=$((visual_lines+(${#line}+text_width-1)/text_width))
        fi
    done <<< "$2"
    (( visual_lines <= UI_HEIGHT-9 )) || options+=(--scrolltext)
    whiptail --clear --fullbuttons --backtitle "$UI_BACKTITLE" --title "$1" \
        "${options[@]}" --msgbox "$2" "$UI_HEIGHT" "$UI_WIDTH"
}

ui_choose() {
    local title=$1 prompt=$2
    shift 2
    UI_CHOICE=$(whiptail --clear --fullbuttons --backtitle "$UI_BACKTITLE" --title "$title" \
        --ok-button Select --cancel-button Back --output-fd 3 \
        --menu "$prompt" "$UI_HEIGHT" "$UI_WIDTH" "$UI_LIST_HEIGHT" "$@" 3>&1 1>&2)
}

ui_read_flag() {
    local prompt
    prompt="Challenge: $1"$'\n\nPaste the exact MFANO{...} flag. Input is hidden.\nKeep MFANO uppercase and the contents lowercase.'
    UI_FLAG=''
    UI_FLAG=$(whiptail --clear --fullbuttons --backtitle "$UI_BACKTITLE" --title "Submit flag // $1" \
        --ok-button Submit --cancel-button Back --output-fd 3 \
        --passwordbox "$prompt" \
        "$UI_HEIGHT" "$UI_WIDTH" 3>&1 1>&2)
}

ui_confirm_reset() {
    whiptail --clear --fullbuttons --backtitle "$UI_BACKTITLE" --title 'Reset mock lab data' \
        --defaultno --yes-button Reset --no-button Back \
        --yesno 'Reseed the mock database and generated lab files? This replaces the current lab data. Your flag progress stays saved.' \
        "$UI_HEIGHT" "$UI_WIDTH"
}

ui_refresh() {
    local rc
    QUIET_ERRORS=true
    load_state
    rc=$?
    QUIET_ERRORS=false
    if (( rc != 0 )); then
        ui_message 'Lab data needs attention' "$LAST_ERROR"
        return "$rc"
    fi
}

ui_progress_text() {
    summary_json | jq -r '"\(.solved) / \(.total) solved  |  \(.remaining) remaining",
        (if .next != null then "Next: \(.next.id) - \(.next.title)"
        elif .total == 0 then "No challenges registered." else "All challenges solved. Well done!" end)'
}

ui_pick_track() {
    local items=()
    mapfile -t items < <(tracks_json | jq -r '.[] |
        [.id,"\(.title)  [\(.solved)/\(.total) solved]"] | .[]')
    ui_choose 'Choose a lab track' 'Select a track, then a challenge. Use arrows, Tab, and Enter.' \
        ALL 'All tracks' "${items[@]}" || return 1
    UI_TRACK=$UI_CHOICE
}

ui_pick_stage() {
    local state=$1 items=() title
    mapfile -t items < <(jq -r --arg track "$UI_TRACK" --arg state "$state" '
        .[] | select(($track == "ALL" or .track == $track) and
            ($state == "all" or .status == $state)) |
        [.id,"\(.title) | \(.difficulty) | \(.status)"] | .[]
    ' <<< "$STAGES")
    if (( ${#items[@]} == 0 )); then
        case "$state" in solved) title='No solved challenges yet' ;; unsolved) title='No remaining challenges' ;; *) title='No challenges registered' ;; esac
        ui_message "$title" 'Choose another track or return to the main menu.'
        return 1
    fi
    ui_choose "Choose a challenge // $UI_TRACK" "$(ui_progress_text)" "${items[@]}" || return 1
    UI_STAGE=$UI_CHOICE
}

ui_show_hint() {
    resolve_stage "$1" || return $?
    local text
    text=$(jq -r '"\(.id) - \(.title)\n\n" +
        (.hint // "No clue has been published for this challenge yet.") +
        (if .evidence != null then "\n\nEvidence: " + .evidence else "" end)' <<< "$SELECTED_STAGE")
    ui_message "Gentle clue // $1" "$text"
}

ui_present() {
    local family=$1 data=$2 title='MFANO // LAB CONTROL' text
    case "$family" in
        labs)
            title='Challenge progress'
            text=$(jq -r '(.labs | map("\(.id) [\(.status | ascii_upcase)]  \(.title)\n  \(.category) | \(.difficulty)") | join("\n\n")) +
                "\n\n\(.progress.solved) / \(.progress.total) solved | \(.progress.remaining) remaining" +
                (if .progress.next != null then "\nNext: " + .progress.next.id else "" end)' <<< "$data")
            ;;
        tracks)
            title='Lab tracks'
            text=$(jq -r '.tracks | map("\(.id) - \(.title)\n  \(.solved)/\(.total) solved | \(.remaining) remaining") | join("\n\n")' <<< "$data")
            ;;
        resolve)
            title='Challenge details'
            text=$(jq -r '.stage | "\(.id) - \(.title)\n\n\(.track_title)\n\(.category)\nDifficulty: \(.difficulty)\nStatus: \(.status)"' <<< "$data")
            ;;
        hints)
            title='Gentle clue'
            text=$(jq -r '.stage | "\(.id) - \(.title)\n\n" + (.hint // "No clue has been published yet.") +
                (if .evidence != null then "\n\nEvidence: " + .evidence else "" end)' <<< "$data")
            ;;
        submit)
            case $(jq -r .result <<< "$data") in
                solved) title='Flag accepted' ;;
                already_solved) title='Already solved' ;;
                valid) title='Flag preview' ;;
            esac
            text=$(jq -r '"\(.stage.id) - \(.stage.title)\n\n" +
                (if .result == "solved" then "Correct flag. Challenge recorded as solved."
                elif .result == "already_solved" then "This challenge is already solved. It was counted once."
                else "Valid flag. Preview only; progress was not changed." end) +
                "\n\n\(.progress.solved) / \(.progress.total) solved | \(.progress.remaining) remaining" +
                (if .progress.next != null then "\nNext: \(.progress.next.id) - \(.progress.next.title)"
                else "\nAll challenges solved. Well done!" end)' <<< "$data")
            ;;
        doctor)
            title='Linux setup check'
            text=$(jq -r '"labctl \(.version) | Offline scoring\nNo authentication required.\n\(.challenge_count) challenges registered.\n\n" +
                (.dependencies | map("\(.name): \(if .available then "available" else "missing" end)\(if .required then " (required)" else " (optional)" end)") | join("\n")) +
                "\n\n" + (if .ready then "Ready." else (.issues | join("\n")) end)' <<< "$data")
            ;;
        lifecycle)
            title='Lab services'
            text=$(jq -r 'if .dry_run then "Preview:\n" + (.argv | @sh)
                else if .output == "" then "Command completed." else .output end end' <<< "$data")
            ;;
        audit)
            title='Dependency audit'
            text=$(jq -r 'if .dry_run then "Preview:\n" + (.argv | @sh)
                else "Dependency audit completed.\n\n" +
                    (if .flag != null then "Vulnerable requests dependency confirmed.\nFlag: " + .flag
                    else "No known-vulnerable requests dependency detected." end) end' <<< "$data")
            ;;
    esac
    ui_message "$title" "$text"
}

ui_result() {
    local family=$1 result=$2 rc=$3 data message
    if data=$(jq -ce '.data // empty' <<< "$result" 2>/dev/null); then
        ui_present "$family" "$data"
    else
        message=$(jq -r '.error.message // "The command could not complete."' <<< "$result" 2>/dev/null) ||
            message='The command could not complete. Run labctl doctor for setup details.'
        ui_message 'Action needs attention' "$message"
    fi
    return "$rc"
}

ui_submit() {
    local id=$1 result rc
    ui_read_flag "$id" || return 0
    result=$(printf '%s\n' "$UI_FLAG" | "$ENTRY_POINT" --json submit "$id" --flag-stdin)
    rc=$?
    UI_FLAG=''
    ui_result submit "$result" "$rc"
}

ui_details() {
    local id=$1 prompt
    while true; do
        ui_refresh || return $?
        resolve_stage "$id" || return $?
        prompt=$(jq -r '"\(.title)\n\(.category) | \(.difficulty)\nStatus: \(.status)"' <<< "$SELECTED_STAGE")
        ui_choose "Challenge // $id" "$prompt" submit 'Submit a flag' hint 'Read a gentle clue' back 'Back to challenges' || return 0
        case "$UI_CHOICE" in
            submit) ui_submit "$id" || true ;;
            hint) ui_show_hint "$id" || return $? ;;
            back) return 0 ;;
        esac
    done
}

ui_browse() {
    local state=$1 action=${2:-browse}
    while true; do
        ui_refresh || return $?
        ui_pick_track || return 0
        while true; do
            ui_refresh || return $?
            ui_pick_stage "$state" || break
            case "$action" in
                submit) ui_submit "$UI_STAGE" || true ;;
                hints) ui_show_hint "$UI_STAGE" || return $? ;;
                browse) ui_details "$UI_STAGE" || return $? ;;
            esac
        done
    done
}

ui_call() {
    local family=$1 result rc
    shift
    result=$("$ENTRY_POINT" --json "$@")
    rc=$?
    ui_result "$family" "$result" "$rc"
}

ui_services() {
    while ui_choose 'Lab services' 'Manage the local Docker lab. Scoring and forensics work offline.' \
        start 'Build and start containers' stop 'Stop containers' reset 'Reseed mock database' \
        shell 'Open Bash in web container' audit 'Audit vulnerable dependency' back 'Main menu'; do
        case "$UI_CHOICE" in
            start|stop) ui_call lifecycle "$UI_CHOICE" || true ;;
            reset) if ui_confirm_reset; then ui_call lifecycle reset --yes || true; fi ;;
            shell) "$ENTRY_POINT" shell || true ;;
            audit) ui_call audit audit || true ;;
            back) return 0 ;;
        esac
    done
}

ui_menu() {
    ui_setup || return $?
    local prompt
    while true; do
        ui_refresh || return $?
        prompt=$'M F A N O  //  L A B  C O N T R O L\n\n'
        prompt+=$(ui_progress_text)
        ui_choose 'MFANO // Linux lab terminal' "$prompt" \
            submit 'Submit a flag' labs 'Browse all challenges' solved 'View solved challenges' \
            unsolved 'View remaining challenges' clues 'Read gentle clues' tracks 'View lab tracks' \
            services 'Manage lab services' doctor 'Check Linux setup' quit 'Exit' || return 0
        case "$UI_CHOICE" in
            submit) ui_browse all submit || return $? ;;
            labs) ui_browse all || return $? ;;
            solved) ui_browse solved || return $? ;;
            unsolved) ui_browse unsolved || return $? ;;
            clues) ui_browse all hints || return $? ;;
            tracks) ui_call tracks tracks || true ;;
            services) ui_services || return $? ;;
            doctor) ui_call doctor doctor || true ;;
            quit) return 0 ;;
        esac
    done
}
