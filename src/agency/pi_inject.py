#!/usr/bin/env python3
"""
Agency v2.0 - pi-inject Client

Unix socket client for communicating with pi-inject extension.
Sends steer, followup, and command messages to a running pi instance.
"""

import json
import os
import socket
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


class MessageType(Enum):
    STEER = "steer"
    FOLLOWUP = "followup"
    COMMAND = "command"
    PING = "ping"


@dataclass
class InjectResponse:
    type: str
    message: Optional[str] = None

    @property
    def is_ok(self) -> bool:
        return self.type == "ok"

    @property
    def is_error(self) -> bool:
        return self.type == "error"

    @property
    def is_pong(self) -> bool:
        return self.type == "pong"


class PiInjectClient:
    """Client for pi-inject Unix socket."""

    def __init__(self, socket_path: Optional[Path] = None):
        """
        Args:
            socket_path: Path to the injector socket. 
                        Defaults to ~/.pi/injector.sock or PI_INJECTOR_SOCKET env var.
        """
        if socket_path:
            self.socket_path = socket_path
        elif env_path := os.environ.get("PI_INJECTOR_SOCKET"):
            self.socket_path = Path(env_path)
        else:
            self.socket_path = Path.home() / ".pi" / "injector.sock"

    def _connect(self) -> socket.socket:
        """Create and connect to the socket."""
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.settimeout(5)
        client.connect(str(self.socket_path))
        return client

    def _send(self, msg_type: MessageType, content: str) -> InjectResponse:
        """Send a message and return the response."""
        client = self._connect()
        try:
            msg = json.dumps({msg_type.value: content}) if msg_type != MessageType.PING else json.dumps({"type": "ping"})
            if msg_type == MessageType.STEER:
                msg = json.dumps({"type": "steer", "message": content})
            elif msg_type == MessageType.FOLLOWUP:
                msg = json.dumps({"type": "followup", "message": content})
            elif msg_type == MessageType.COMMAND:
                msg = json.dumps({"type": "command", "command": content})
            
            client.sendall((msg + "\n").encode())
            response = client.recv(1024).decode()
            
            if response:
                data = json.loads(response)
                return InjectResponse(type=data.get("type", ""), message=data.get("message"))
            return InjectResponse(type="error", message="No response")
        finally:
            client.close()

    def ping(self) -> InjectResponse:
        """Check if pi-inject is running."""
        return self._send(MessageType.PING, "")

    def steer(self, message: str) -> InjectResponse:
        """Send a steer message (interrupts current processing)."""
        return self._send(MessageType.STEER, message)

    def followup(self, message: str) -> InjectResponse:
        """Send a followup message (queued after current task)."""
        return self._send(MessageType.FOLLOWUP, message)

    def command(self, cmd: str) -> InjectResponse:
        """Execute a slash command."""
        return self._send(MessageType.COMMAND, cmd)

    def is_running(self) -> bool:
        """Check if pi-inject socket is accessible."""
        try:
            resp = self.ping()
            return resp.is_pong
        except (socket.error, FileNotFoundError, ConnectionRefusedError):
            return False


def get_client(socket_path: Optional[str] = None) -> PiInjectClient:
    """Get a PiInjectClient instance."""
    path = Path(socket_path) if socket_path else None
    return PiInjectClient(path)


# CLI interface
def main():
    import argparse

    parser = argparse.ArgumentParser(description="pi-inject client")
    parser.add_argument("message", nargs="?", help="Message to send")
    parser.add_argument("--steer", action="store_true", help="Send as steer (interrupts)")
    parser.add_argument("--followup", action="store_true", help="Send as followup")
    parser.add_argument("--command", help="Send as slash command")
    parser.add_argument("--ping", action="store_true", help="Just ping")
    parser.add_argument("--socket", help="Socket path")

    args = parser.parse_args()

    client = get_client(args.socket)

    if args.ping:
        resp = client.ping()
        print(f"Pong!" if resp.is_pong else f"Error: {resp.message}")
        return

    if args.command:
        resp = client.command(args.command)
        print(f"OK" if resp.is_ok else f"Error: {resp.message}")
        return

    if args.message:
        if args.steer:
            resp = client.steer(args.message)
        elif args.followup:
            resp = client.followup(args.message)
        else:
            resp = client.steer(args.message)  # Default to steer
        print(f"OK" if resp.is_ok else f"Error: {resp.message}")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
