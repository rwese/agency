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
skip() { printf "${YELLOW}[SKIP]${NC} %s\n" "$*"; }

cleanup() {
    info "Cleaning up..."
    # Kill all agency tmux sessions and remove sockets
    for socket in /tmp/tmux-501/agency-*; do
        name="$(basename "$socket")"
        tmux -L "$name" kill-server 2>/dev/null || true
        rm -f "$socket" 2>/dev/null || true
    done
    # Also remove any leftover sockets without killing
    rm -f /tmp/tmux-501/agency-* 2>/dev/null || true
    rm -rf "$TEST_CONFIG_DIR" 2>/dev/null || true
}

create_project() {
    local name="$1"
    local dir="/tmp/test-$name"
    rm -rf "$dir"
    mkdir -p "$dir"
    git -C "$dir" init >/dev/null 2>&1
    echo "$dir"
}

# Use installed agency or uv run
AGENCY_CMD="${AGENCY_CMD:-agency}"
MOCK_AGENT="src/agency/mock_agent.py"

# Tests
test_init() {
    info "Test: init"
    local dir
    dir=$(create_project "init")
    timeout 120 $AGENCY_CMD init --dir "$dir" >/dev/null 2>&1 || { fail "init timeout"; return; }
    [[ -f "$dir/.agency/agents.yaml" ]] && pass "init" || fail "init"
    [[ -d "$dir/.agency/agents" ]] && pass "init agents dir" || fail "init agents dir"
}

test_init_with_manager() {
    info "Test: init creates session"
    local dir
    dir=$(create_project "mgr")
    timeout 120 $AGENCY_CMD init --dir "$dir" >/dev/null 2>&1 || { fail "init mgr timeout"; return; }
    [[ -f "$dir/.agency/config.yaml" ]] && pass "init creates config" || fail "init creates config"
    [[ -f "$dir/.agency/agents.yaml" ]] && pass "init creates agents.yaml" || fail "init creates agents.yaml"
}

test_start_session() {
    info "Test: start session"
    local dir socket
    dir=$(create_project "start")
    socket="agency-$(basename "$dir")"
    timeout 120 $AGENCY_CMD init --dir "$dir" >/dev/null 2>&1 || { fail "init timeout"; return; }
    timeout 120 $AGENCY_CMD start --dir "$dir" >/dev/null 2>&1 || { fail "start timeout"; return; }
    sleep 1
    tmux -L "$socket" has-session -t "$socket" 2>/dev/null && pass "start" || fail "start session"
    tmux -L "$socket" kill-session -t "$socket" 2>/dev/null || true
}

test_start_no_agency_dir() {
    info "Test: start without agency dir"
    local dir
    dir=$(create_project "nodir")
    # Expect failure (exit != 0) so we check for non-zero exit
    if timeout 120 $AGENCY_CMD start --dir "$dir" 2>/dev/null; then
        fail "start_no_dir"
    else
        pass "start_no_dir"
    fi
}

test_list() {
    info "Test: list"
    local dir1 dir2
    dir1=$(create_project "list1")
    dir2=$(create_project "list2")
    timeout 120 $AGENCY_CMD init --dir "$dir1" >/dev/null 2>&1 || { fail "init list1 timeout"; return; }
    timeout 120 $AGENCY_CMD init --dir "$dir2" >/dev/null 2>&1 || { fail "init list2 timeout"; return; }
    timeout 120 $AGENCY_CMD start --dir "$dir1" >/dev/null 2>&1 || { fail "start list1 timeout"; return; }
    timeout 120 $AGENCY_CMD start --dir "$dir2" >/dev/null 2>&1 || { fail "start list2 timeout"; return; }
    sleep 1
    out=$($AGENCY_CMD list 2>&1)
    echo "$out" | grep -q "list1" && echo "$out" | grep -q "list2" && pass "list" || fail "list"
    tmux -L agency-list1 kill-session -t agency-list1 2>/dev/null || true
    tmux -L agency-list2 kill-session -t agency-list2 2>/dev/null || true
}

test_members() {
    info "Test: members"
    local dir
    dir=$(create_project "members")
    timeout 120 $AGENCY_CMD init --dir "$dir" >/dev/null 2>&1 || { fail "init members timeout"; return; }
    # Create manager config
    cat > "$dir/.agency/manager.yaml" << 'MANAGEREOF'
name: coordinator
personality: |
  Test manager
MANAGEREOF
    echo 'agents:' > "$dir/.agency/agents.yaml"
    echo '  - name: coder' >> "$dir/.agency/agents.yaml"
    mkdir -p "$dir/.agency/agents"
    echo 'name: coder' > "$dir/.agency/agents/coder.yaml"
    timeout 120 $AGENCY_CMD start --dir "$dir" >/dev/null 2>&1 || { fail "start members timeout"; return; }
    sleep 1
    out=$($AGENCY_CMD members --dir "$dir" 2>&1)
    echo "$out" | grep -q "coordinator" && echo "$out" | grep -q "coder" && pass "members" || fail "members"
    tmux -L agency-members kill-session -t agency-members 2>/dev/null || true
}

test_stop() {
    info "Test: stop"
    local dir session
    dir=$(create_project "stop")
    session="agency-$(basename "$dir")"
    timeout 120 $AGENCY_CMD init --dir "$dir" >/dev/null 2>&1 || { fail "init stop timeout"; return; }
    # Create manager config
    echo 'name: coordinator' > "$dir/.agency/manager.yaml"
    timeout 120 $AGENCY_CMD start --dir "$dir" >/dev/null 2>&1 || { fail "start stop timeout"; return; }
    sleep 1
    # Force stop since mock agent doesn't respond to graceful shutdown
    timeout 60 $AGENCY_CMD stop "$session" --force >/dev/null 2>&1 && pass "stop" || fail "stop"
}

test_kill() {
    info "Test: kill"
    local dir session
    dir=$(create_project "kill")
    session="agency-$(basename "$dir")"
    timeout 120 $AGENCY_CMD init --dir "$dir" >/dev/null 2>&1 || { fail "init kill timeout"; return; }
    # Create manager config
    echo 'name: coordinator' > "$dir/.agency/manager.yaml"
    timeout 120 $AGENCY_CMD start --dir "$dir" >/dev/null 2>&1 || { fail "start kill timeout"; return; }
    sleep 1
    timeout 60 $AGENCY_CMD kill "$session" >/dev/null 2>&1
    ! tmux -L "$session" has-session -t "$session" 2>/dev/null && pass "kill" || fail "kill"
}

test_completions() {
    info "Test: completions"
    out=$($AGENCY_CMD completions bash 2>&1)
    echo "$out" | grep -q "_agency_completions" && pass "completions bash" || fail "completions bash"
    out=$($AGENCY_CMD completions zsh 2>&1)
    echo "$out" | grep -q "_agency" && pass "completions zsh" || fail "completions zsh"
    out=$($AGENCY_CMD completions fish 2>&1)
    echo "$out" | grep -q "complete -c agency" && pass "completions fish" || fail "completions fish"
}

test_tasks() {
    info "Test: tasks"
    local dir
    dir=$(create_project "tasks")
    timeout 60 $AGENCY_CMD init --dir "$dir" >/dev/null 2>&1 || { fail "init tasks timeout"; return; }
    # Run tasks commands from within the project directory
    (cd "$dir" && $AGENCY_CMD tasks add -d "Test task") >/dev/null 2>&1 || { fail "tasks add timeout"; return; }
    out=$(cd "$dir" && $AGENCY_CMD tasks list 2>&1)
    echo "$out" | grep -q "Test task" && pass "tasks add/list" || fail "tasks add/list"
}

test_base_personality() {
    info "Test: base personality injection"
    # Test that session.py generates launch scripts with base personality
    uv run python3 -c "
from agency.session import BASE_PERSONALITY, MANAGER_BASE_ADDITION, AGENT_BASE_ADDITION
assert 'tmux session' in BASE_PERSONALITY
assert 'agency tasks list' in BASE_PERSONALITY
assert 'Manager Responsibilities' in MANAGER_BASE_ADDITION
assert 'Agent Responsibilities' in AGENT_BASE_ADDITION
print('OK')
" && pass "base personality" || fail "base personality"
}

main() {
    info "========================================"
    info "  Agency Test Suite"
    info "========================================"
    cleanup
    
    export AGENCY_AGENT_CMD="python3 $MOCK_AGENT"
    
    test_init
    test_init_with_manager
    test_start_session
    test_start_no_agency_dir
    test_list
    test_members
    test_stop
    test_kill
    test_completions
    test_tasks
    test_base_personality
    
    cleanup
    echo
    info "Results: $PASS passed, $FAIL failed"
    if [[ $FAIL -gt 0 ]]; then
        exit 1
    fi
}

main "$@"
