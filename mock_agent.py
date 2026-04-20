#!/usr/bin/env python3
"""
Mock Agent - For testing agency session management.

A simple REPL that:
- Reads lines from stdin
- Appends to memory file
- Responds to commands like 'exit' or 'Goodbye'
- Triggers shutdown on SIGTERM
"""

import argparse
import atexit
import os
import signal
import sys
from datetime import datetime
from pathlib import Path


class MockAgent:
    def __init__(self, memory_file: str):
        self.memory_file = Path(os.path.expanduser(memory_file)).resolve()
        self.running = True
        self.shutdown_triggered = False

        # Ensure memory file exists
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.memory_file.exists():
            self.memory_file.write_text(f"# Memory - Agent started at {self._now()}\n\n")

    def _now(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _log(self, message: str) -> None:
        """Append to memory file."""
        timestamp = self._now()
        entry = f"[{timestamp}] {message}\n"
        with open(self.memory_file, "a") as f:
            f.write(entry)

    def _respond(self, message: str) -> None:
        """Print response to stdout (visible in tmux)."""
        print(f"[agent] {message}", flush=True)

    def _save_and_exit(self) -> None:
        """Graceful shutdown: save memory and exit."""
        self._log("Agent shutting down gracefully")
        self._respond("Goodbye")
        self.running = False

    def handle_signal(self, signum, frame) -> None:
        """Handle SIGTERM for graceful shutdown."""
        if not self.shutdown_triggered:
            self.shutdown_triggered = True
            self._log(f"Received signal {signum}, initiating shutdown")
            self._respond("Acknowledged shutdown signal, saving memories...")
            self._save_and_exit()
            sys.exit(0)

    def run(self) -> None:
        """Main REPL loop."""
        self._log("Agent started")
        self._respond(f"Mock agent ready. Memory: {self.memory_file}")
        self._respond("Say 'exit' or 'Goodbye' to quit, or send Ctrl+C")

        # Register signal handler
        signal.signal(signal.SIGTERM, self.handle_signal)
        signal.signal(signal.SIGINT, self.handle_signal)

        while self.running:
            try:
                line = sys.stdin.readline()
                if not line:  # EOF
                    break

                line = line.strip()
                if not line:
                    continue

                self._log(f"Received: {line}")

                # Check for shutdown triggers
                if "exit gracefully" in line.lower() or line.lower() in ("exit", "goodbye", "quit"):
                    self._save_and_exit()
                    break

                # Echo back for testing
                self._respond(f"Echo: {line}")
                self._log(f"Response: Echo: {line}")

            except EOFError:
                break
            except KeyboardInterrupt:
                if self.shutdown_triggered:
                    break
                self._respond("Ctrl+C received, shutting down...")
                self._save_and_exit()
                break

        self._log("Agent stopped")


def main():
    parser = argparse.ArgumentParser(description="Mock Agent for Testing")
    parser.add_argument("--memory-file", help="Path to memory file")
    parser.add_argument("--session-dir", help="Session directory for memory")
    parser.add_argument("--source-dir", default=".", help="Source directory (unused)")
    parser.add_argument("--storage-dir", default=".", help="Storage directory (unused)")

    args = parser.parse_args()

    # Determine memory file location
    if args.memory_file:
        memory_file = args.memory_file
    elif args.session_dir:
        session_path = Path(args.session_dir)
        # Find the session script to extract agent name
        sessions = list(session_path.glob("agency-*.sh"))
        if sessions:
            import re
            match = re.search(r"agency-([a-z-]+)-", sessions[0].name)
            agent_name = match.group(1) if match else "mock"
        else:
            agent_name = "mock"
        memory_file = session_path / f"{agent_name}.md"
    else:
        parser.error("Either --memory-file or --session-dir is required")

    agent = MockAgent(memory_file)
    agent.run()


if __name__ == "__main__":
    main()
