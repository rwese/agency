#!/usr/bin/env python3
"""Generate agent launch scripts."""
import sys

def escape(s):
    """Escape string for shell."""
    return s.replace('\\', '\\\\').replace('"', '\\"').replace('$', '\\$').replace('`', '\\`')

def main():
    if len(sys.argv) < 4:
        print("Usage: generate_agent_script.py <script_path> <agent_cmd> <agency_dir> [personality]", file=sys.stderr)
        sys.exit(1)
    
    script_path = sys.argv[1]
    agent_cmd = sys.argv[2]
    agency_dir = sys.argv[3]
    personality = sys.argv[4] if len(sys.argv) > 4 else None
    
    with open(script_path, 'w') as f:
        f.write('#!/bin/bash\n')
        f.write(f'cd "{agency_dir}"\n')
        if personality:
            escaped = escape(personality)
            f.write(f'exec {agent_cmd} --session-dir "{agency_dir}/sessions" --append-system-prompt "{escaped}"\n')
        else:
            f.write(f'exec {agent_cmd} --session-dir "{agency_dir}/sessions"\n')

if __name__ == '__main__':
    main()
