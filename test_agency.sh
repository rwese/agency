#!/usr/bin/env bash
# shellcheck disable=SC1090,SC2086,SC2164

set -euo pipefail

AGENCY_DIR="$(cd "$(dirname "$0")" && pwd)"
AGENCY="$AGENCY_DIR/agency"
MOCK_AGENT="$AGENCY_DIR/mock_agent.py"

export AGENCY_AGENT_CMD="python3 $MOCK_AGENT"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

TESTS_PASSED=0
TESTS_FAILED=0

log_pass() { printf "${GREEN}[PASS]${NC} %s\n" "$*"; TESTS_PASSED=$((TESTS_PASSED + 1)); }
log_fail() { printf "${RED}[FAIL]${NC} %s\n" "$*"; TESTS_FAILED=$((TESTS_FAILED + 1)); }
log_info() { printf "${YELLOW}[INFO]${NC} %s\n" "$*"; }

cleanup() {
  log_info "Cleaning up..."
  tmux kill-session -t agency-* 2>/dev/null || true
  rm -rf "$HOME/.agency" "$HOME/.config/agency" 2>/dev/null || true
}

create_config() {
  local name="$1"
  mkdir -p "$HOME/.config/agency/agents"
  cat > "$HOME/.config/agency/agents/${name}.yaml" <<EOF
name: $name
memory_file: ~/.agency/memory/${name}.md
source_dir: ~/.agency/src/$name
storage_dir: ~/.agency/storage/$name
working_dir: ~
EOF
}

# Tests
test_help() {
  log_info "Test: help"
  "$AGENCY" help | grep -q "Agency" && log_pass "help" || log_fail "help"
}

test_version() {
  log_info "Test: version"
  "$AGENCY" version | grep -q "0.1.0" && log_pass "version" || log_fail "version"
}

test_init() {
  log_info "Test: init"
  rm -rf "$HOME/.config/agency"
  "$AGENCY" init
  [[ -f "$HOME/.config/agency/agents/example.yaml" ]] && log_pass "init" || log_fail "init"
}

test_start() {
  log_info "Test: start"
  create_config "start1"
  local session="$("$AGENCY" start start1)"
  # New format: agency-{name}-{word1}-{word2}
  [[ "$session" =~ ^agency-start1-[a-z]+-[a-z]+$ ]] && log_pass "start" || log_fail "start: $session"
  tmux kill-session -t "$session" 2>/dev/null || true
}

test_list() {
  log_info "Test: list"
  create_config "list1"
  create_config "list2"
  local s1="$("$AGENCY" start list1)"
  local s2="$("$AGENCY" start list2)"
  local out="$("$AGENCY" list)"
  echo "$out" | grep -q "$s1" && echo "$out" | grep -q "$s2" && log_pass "list" || log_fail "list"
  tmux kill-session -t "$s1" "$s2" 2>/dev/null || true
}

test_send() {
  log_info "Test: send"
  local session="agency-send-test"
  local mem="$HOME/.agency/memory/send.md"
  mkdir -p "$(dirname "$mem")"
  tmux new-session -d -s "$session" "python3 $MOCK_AGENT --memory-file $mem"
  sleep 1
  "$AGENCY" send "$session" "hello"
  sleep 0.5
  grep -q "hello" "$mem" && log_pass "send" || log_fail "send"
  tmux kill-session -t "$session" 2>/dev/null || true
}

test_stop() {
  log_info "Test: stop"
  local session="agency-stop-test"
  local mem="$HOME/.agency/memory/stop.md"
  mkdir -p "$(dirname "$mem")"
  tmux new-session -d -s "$session" "python3 $MOCK_AGENT --memory-file $mem"
  sleep 1
  timeout 35 "$AGENCY" stop "$session" 2>/dev/null && log_pass "stop" || log_fail "stop"
  ! tmux has-session -t "$session" 2>/dev/null && log_pass "stopped" || log_fail "still running"
}

test_kill() {
  log_info "Test: kill"
  local session="agency-kill-test"
  local mem="$HOME/.agency/memory/kill.md"
  mkdir -p "$(dirname "$mem")"
  tmux new-session -d -s "$session" "python3 $MOCK_AGENT --memory-file $mem"
  sleep 1
  "$AGENCY" kill "$session"
  ! tmux has-session -t "$session" 2>/dev/null && log_pass "kill" || log_fail "kill"
}

test_kill_all() {
  log_info "Test: kill-all"
  tmux new-session -d -s "agency-ta1" "sleep 60"
  tmux new-session -d -s "agency-ta2" "sleep 60"
  tmux new-session -d -s "other" "sleep 60"
  "$AGENCY" kill-all
  ! tmux has-session -t "agency-ta1" 2>/dev/null && ! tmux has-session -t "agency-ta2" 2>/dev/null && log_pass "kill-all" || log_fail "kill-all"
  tmux has-session -t "other" 2>/dev/null && log_pass "other preserved" || log_fail "other killed"
  tmux kill-session -t "other" 2>/dev/null || true
}

main() {
  log_info "========================================"
  log_info "  Agency Test Suite"
  log_info "========================================"
  cleanup
  test_help; test_version; test_init; test_start; test_list; test_send; test_stop; test_kill; test_kill_all
  cleanup
  echo
  log_info "Results: $TESTS_PASSED passed, $TESTS_FAILED failed"
  [[ $TESTS_FAILED -gt 0 ]] && exit 1
}

main "$@"
