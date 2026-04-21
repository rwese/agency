#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0

pass() { printf "${GREEN}[PASS]${NC} %s\n" "$*"; PASS=$((PASS + 1)); }
fail() { printf "${RED}[FAIL]${NC} %s\n" "$*"; FAIL=$((FAIL + 1)); }
info() { printf "${YELLOW}[INFO]${NC} %s\n" "$*"; }

cleanup() {
    info "Cleaning up..."
    tmux kill-session -t agency-* 2>/dev/null || true
    rm -rf "$HOME/.config/agency" 2>/dev/null || true
}

create_config() {
    mkdir -p "$HOME/.config/agency/agents"
    cat > "$HOME/.config/agency/agents/${1}.yaml" <<EOF
name: $1
personality: |
  Test personality for $1
EOF
}

# Run Python tests
run_tests() {
    info "Running Python pytest tests..."
    if command -v pytest >/dev/null 2>&1; then
        pytest tests/ -v 2>&1 && pass "pytest" || fail "pytest"
    else
        info "pytest not found, skipping"
    fi
}

# Manual integration tests
test_init() {
    info "Test: init"
    rm -rf "$HOME/.config/agency"
    python3 agency.py init >/dev/null 2>&1
    [[ -f "$HOME/.config/agency/agents/example.yaml" ]] && pass "init" || fail "init"
}

test_start() {
    info "Test: start"
    create_config "start1"
    result=$(python3 agency.py start start1 --dir /tmp/test-start 2>/dev/null)
    [[ "$result" =~ ^agency-test-start:start1 ]] && pass "start" || fail "start: $result"
    tmux kill-session -t agency-test-start 2>/dev/null || true
}

test_start_no_dir() {
    info "Test: start_no_dir"
    create_config "nodir"
    ! python3 agency.py start nodir 2>/dev/null && pass "start_no_dir" || fail "start_no_dir"
}

test_list() {
    info "Test: list"
    create_config "list1"
    create_config "list2"
    python3 agency.py start list1 --dir /tmp/test-list1 >/dev/null 2>&1
    python3 agency.py start list2 --dir /tmp/test-list2 >/dev/null 2>&1
    out=$(python3 agency.py list 2>&1)
    echo "$out" | grep -q "test-list1" && echo "$out" | grep -q "test-list2" && pass "list" || fail "list"
    tmux kill-session -t agency-test-list1 agency-test-list2 2>/dev/null || true
}

test_send() {
    info "Test: send"
    create_config "send1"
    python3 agency.py start send1 --dir /tmp/test-send >/dev/null 2>&1
    sleep 1
    tmux has-session -t agency-test-send 2>/dev/null || { fail "send: session died"; return; }
    python3 agency.py send agency-test-send send1 "hello" 2>&1 | grep -q "Sent" && pass "send" || fail "send"
    tmux kill-session -t agency-test-send 2>/dev/null || true
}

test_stop() {
    info "Test: stop"
    create_config "stop1"
    python3 agency.py start stop1 --dir /tmp/test-stop >/dev/null 2>&1
    sleep 1
    timeout 35 python3 agency.py stop agency-test-stop >/dev/null 2>&1 && pass "stop" || fail "stop"
}

test_kill() {
    info "Test: kill"
    create_config "kill1"
    python3 agency.py start kill1 --dir /tmp/test-kill >/dev/null 2>&1
    python3 agency.py kill agency-test-kill >/dev/null 2>&1
    ! tmux has-session -t agency-test-kill 2>/dev/null && pass "kill" || fail "kill"
}

test_kill_all() {
    info "Test: kill-all"
    tmux new-session -d -s "other" "sleep 60"
    create_config "ka1"
    create_config "ka2"
    python3 agency.py start ka1 --dir /tmp/test-ka1 >/dev/null 2>&1
    python3 agency.py start ka2 --dir /tmp/test-ka2 >/dev/null 2>&1
    python3 agency.py kill-all >/dev/null 2>&1
    ! tmux has-session -t "agency-test-ka1" 2>/dev/null && ! tmux has-session -t "agency-test-ka2" 2>/dev/null && pass "kill-all" || fail "kill-all"
    tmux has-session -t "other" 2>/dev/null && pass "other preserved" || fail "other killed"
    tmux kill-session -t "other" 2>/dev/null || true
}

main() {
    info "========================================"
    info "  Agency Test Suite"
    info "========================================"
    cleanup
    
    export AGENCY_AGENT_CMD="python3 mock_agent.py"
    
    test_init
    test_start
    test_start_no_dir
    test_list
    test_send
    test_stop
    test_kill
    test_kill_all
    
    cleanup
    echo
    info "Results: $PASS passed, $FAIL failed"
    [[ $FAIL -gt 0 ]] && exit 1
}

main "$@"
