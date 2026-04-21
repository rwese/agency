#!/usr/bin/env python3
"""Generate agent launch scripts."""
import sys
from pathlib import Path

def escape(s):
    """Escape string for shell."""
    return s.replace('\\', '\\\\').replace('"', '\\"').replace('$', '\\$').replace('`', '\\`')

def create_quiet_settings(sessions_dir: Path) -> None:
    """Create .pi/settings.json with quiet startup for agency sessions."""
    # Ensure sessions directory exists
    sessions_dir.mkdir(parents=True, exist_ok=True)
    pi_dir = sessions_dir / ".pi"
    pi_dir.mkdir(parents=True, exist_ok=True)
    settings_path = pi_dir / "settings.json"
    
    # Only create if doesn't exist
    if not settings_path.exists():
        settings = {
            "quietStartup": True,
            "collapseChangelog": True,
            # Only load essential packages for agent operation
            "packages": [],
            "extensions": [],
            "skills": [],
            "prompts": [],
            "themes": []
        }
        import json
        with open(settings_path, 'w') as f:
            json.dump(settings, f, indent=2)

def main():
    if len(sys.argv) < 4:
        print("Usage: generate_agent_script.py <script_path> <agent_cmd> <agency_dir> [personality]", file=sys.stderr)
        sys.exit(1)
    
    script_path = sys.argv[1]
    agent_cmd = sys.argv[2]
    agency_dir = sys.argv[3]
    personality = sys.argv[4] if len(sys.argv) > 4 else None
    
    # Create quiet settings for agency sessions
    sessions_dir = Path(agency_dir) / "sessions"
    create_quiet_settings(sessions_dir)
    
    with open(script_path, 'w') as f:
        f.write('#!/bin/bash\n')
        f.write(f'cd "{agency_dir}"\n')
        # Use --no-context-files to skip AGENTS.md/CLAUDE.md loading for clean persona
        # Use PI_CODING_AGENT=true to signal agent mode
        base_cmd = f'{agent_cmd} --session-dir "{agency_dir}/sessions" --no-context-files PI_CODING_AGENT=true'
        if personality:
            escaped = escape(personality)
            f.write(f'exec {base_cmd} --append-system-prompt "{escaped}"\n')
        else:
            f.write(f'exec {base_cmd}\n')

if __name__ == '__main__':
    main()
