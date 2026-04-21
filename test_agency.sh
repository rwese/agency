#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0

# Use temp config dir for testing (avoids conflicts with user config)
TEST_CONFIG_DIR="${TMPDIR:-/tmp}/agency-test-$$"
mkdir -p "$TEST_CONFIG_DIR"
export XDG_CONFIG_HOME="$TEST_CONFIG_DIR"

pass() { printf "${GREEN}[PASS]${NC} %s\n" "$*"; PASS=$((PASS + 1)); }
fail() { printf "${RED}[FAIL]${NC} %s\n" "$*"; FAIL=$((FAIL + 1)); }
info() { printf "${YELLOW}[INFO]${NC} %s\n" "$*"; }

cleanup() {
    info "Cleaning up..."
    tmux -L agency kill-session -t agency-* 2>/dev/null || true
    rm -rf "$TEST_CONFIG_DIR" 2>/dev/null || true
}

create_config() {
    mkdir -p "$TEST_CONFIG_DIR/agency/agents"
    cat > "$TEST_CONFIG_DIR/agency/agents/${1}.yaml" <<EOF
name: $1
personality: |
  Test personality for $1
EOF
}

# Use uv run or direct python based on environment
AGENCY_CMD="${AGENCY_CMD:-uv run agency}"
MOCK_AGENT="src/agency/mock_agent.py"

# Manual integration tests
test_init() {
    info "Test: init"
    rm -rf "$TEST_CONFIG_DIR/agency"
    $AGENCY_CMD init >/dev/null 2>&1
    [[ -f "$TEST_CONFIG_DIR/agency/agents/example.yaml" ]] && pass "init" || fail "init"
    [[ -d "$TEST_CONFIG_DIR/agency/managers" ]] && pass "init managers dir" || fail "init managers dir"
}

test_start() {
    info "Test: start"
    create_config "start1"
    result=$($AGENCY_CMD start start1 --dir /tmp/test-start 2>/dev/null)
    [[ "$result" =~ ^agency-test-start:start1 ]] && pass "start" || fail "start: $result"
    tmux -L agency kill-session -t agency-test-start 2>/dev/null || true
}

test_start_no_dir() {
    info "Test: start_no_dir"
    create_config "nodir"
    ! $AGENCY_CMD start nodir 2>/dev/null && pass "start_no_dir" || fail "start_no_dir"
}

test_list() {
    info "Test: list"
    create_config "list1"
    create_config "list2"
    $AGENCY_CMD start list1 --dir /tmp/test-list1 >/dev/null 2>&1
    $AGENCY_CMD start list2 --dir /tmp/test-list2 >/dev/null 2>&1
    out=$($AGENCY_CMD list 2>&1)
    echo "$out" | grep -q "test-list1" && echo "$out" | grep -q "test-list2" && pass "list" || fail "list"
    tmux -L agency kill-session -t agency-test-list1 agency-test-list2 2>/dev/null || true
}

test_send() {
    info "Test: send"
    create_config "send1"
    $AGENCY_CMD start send1 --dir /tmp/test-send >/dev/null 2>&1
    sleep 1
    tmux -L agency has-session -t agency-test-send 2>/dev/null || { fail "send: session died"; return; }
    $AGENCY_CMD send agency-test-send send1 "hello" 2>&1 | grep -q "Sent" && pass "send" || fail "send"
    tmux -L agency kill-session -t agency-test-send 2>/dev/null || true
}

test_stop() {
    info "Test: stop"
    create_config "stop1"
    $AGENCY_CMD start stop1 --dir /tmp/test-stop >/dev/null 2>&1
    sleep 1
    timeout 35 $AGENCY_CMD stop agency-test-stop >/dev/null 2>&1 && pass "stop" || fail "stop"
}

test_kill() {
    info "Test: kill"
    create_config "kill1"
    $AGENCY_CMD start kill1 --dir /tmp/test-kill >/dev/null 2>&1
    $AGENCY_CMD kill agency-test-kill >/dev/null 2>&1
    ! tmux -L agency has-session -t agency-test-kill 2>/dev/null && pass "kill" || fail "kill"
}

test_kill_all() {
    info "Test: kill-all"
    tmux new-session -d -s "other" "sleep 60"
    create_config "ka1"
    create_config "ka2"
    $AGENCY_CMD start ka1 --dir /tmp/test-ka1 >/dev/null 2>&1
    $AGENCY_CMD start ka2 --dir /tmp/test-ka2 >/dev/null 2>&1
    $AGENCY_CMD kill-all >/dev/null 2>&1
    ! tmux -L agency has-session -t "agency-test-ka1" 2>/dev/null && ! tmux -L agency has-session -t "agency-test-ka2" 2>/dev/null && pass "kill-all" || fail "kill-all"
    tmux has-session -t "other" 2>/dev/null && pass "other preserved" || fail "other killed"
    tmux kill-session -t "other" 2>/dev/null || true
}

test_completions() {
    info "Test: completions"
    out=$($AGENCY_CMD completions bash 2>&1)
    echo "$out" | grep -q "_agency_complete" && pass "completions bash" || fail "completions bash: missing function"
    out=$($AGENCY_CMD completions zsh 2>&1)
    echo "$out" | grep -q "_agency" && pass "completions zsh" || fail "completions zsh: missing"
    out=$($AGENCY_CMD completions fish 2>&1)
    echo "$out" | grep -q "complete -c agency" && pass "completions fish" || fail "completions fish: missing"
}

main() {
    info "========================================"
    info "  Agency Test Suite"
    info "========================================"
    cleanup
    
    export AGENCY_AGENT_CMD="python3 $MOCK_AGENT"
    
    test_init
    test_start
    test_start_no_dir
    test_list
    test_send
    test_stop
    test_kill
    test_kill_all
    test_completions
    
    cleanup
    echo
    info "Results: $PASS passed, $FAIL failed"
    if [[ $FAIL -gt 0 ]]; then
        exit 1
    fi
}

main "$@"
