#!/usr/bin/env python3
"""Mock Agent for testing agency."""
import argparse
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

        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.memory_file.exists():
            self.memory_file.write_text(f"# Memory - {self._now()}\n\n")

    def _now(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _log(self, msg: str) -> None:
        entry = f"[{self._now()}] {msg}\n"
        with open(self.memory_file, "a") as f:
            f.write(entry)

    def _respond(self, msg: str) -> None:
        print(f"[agent] {msg}", flush=True)

    def _exit(self) -> None:
        self._log("Agent shutting down")
        self._respond("Goodbye")
        self.running = False

    def handle_signal(self, signum, frame) -> None:
        if not self.shutdown_triggered:
            self.shutdown_triggered = True
            self._log(f"Received signal {signum}")
            self._respond("Acknowledged shutdown")
            self._exit()
            sys.exit(0)

    def run(self) -> None:
        self._log("Agent started")
        self._respond(f"Mock ready. Memory: {self.memory_file}")

        signal.signal(signal.SIGTERM, self.handle_signal)
        signal.signal(signal.SIGINT, self.handle_signal)

        while self.running:
            try:
                line = sys.stdin.readline()
                if not line:
                    break

                line = line.strip()
                if not line:
                    continue

                self._log(f"Received: {line}")

                # Shutdown triggers
                if "exit gracefully" in line.lower() or line.lower() in ("exit", "goodbye", "quit"):
                    self._exit()
                    break

                self._respond(f"Echo: {line}")

            except EOFError:
                break
            except KeyboardInterrupt:
                if self.shutdown_triggered:
                    break
                self._exit()
                break

        self._log("Agent stopped")


def main():
    parser = argparse.ArgumentParser(description="Mock Agent")
    parser.add_argument("--memory-file", help="Memory file path")
    parser.add_argument("--session-dir", help="Session directory")
    # Ignored for pi compatibility
    parser.add_argument("--append-system-prompt", help=argparse.SUPPRESS)
    parser.add_argument("--no-tools", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--no-skills", action="store_true", help=argparse.SUPPRESS)

    args = parser.parse_args()

    if args.memory_file:
        memory_file = args.memory_file
    elif args.session_dir:
        memory_file = Path(args.session_dir) / "mock.md"
    else:
        memory_file = "/tmp/mock.md"

    agent = MockAgent(memory_file)
    agent.run()


if __name__ == "__main__":
    main()
