#!/usr/bin/env bash
# Agency Project Evaluation Runner
# Usage: ./run-eval.sh <project-id>
# Example: ./run-eval.sh 01

set -e

PROJECT_DIR="demo/projects"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -z "$1" ]; then
    echo "Usage: $0 <project-id>"
    echo "Example: $0 01"
    echo ""
    echo "Available projects:"
    ls -1 "$PROJECT_DIR/" 2>/dev/null || echo "  No projects found"
    exit 1
fi

PROJECT_ID="$1"
PROJECT_PATH="$PROJECT_DIR/$PROJECT_ID"

# Find matching project
if [ ! -d "$PROJECT_PATH" ]; then
    # Try fuzzy match
    MATCH=$(ls -1 "$PROJECT_DIR/" 2>/dev/null | grep "^$PROJECT_ID" | head -1)
    if [ -n "$MATCH" ]; then
        PROJECT_PATH="$PROJECT_DIR/$MATCH"
        PROJECT_ID="$MATCH"
    else
        echo "Error: Project '$PROJECT_ID' not found"
        echo ""
        echo "Available projects:"
        ls -1 "$PROJECT_DIR/" 2>/dev/null || echo "  No projects found"
        exit 1
    fi
fi

echo "=== Agency Project Evaluation ==="
echo "Project: $PROJECT_ID"
echo "Path: $PROJECT_PATH"
echo ""

# Check if project exists
if [ ! -f "$PROJECT_PATH/README.md" ]; then
    echo "Error: Not a valid project (no README.md)"
    exit 1
fi

# Read project type from README if possible
PROJECT_TYPE=$(grep -m1 "^**Type:**" "$PROJECT_PATH/README.md" 2>/dev/null | sed 's/.*: //' || echo "unknown")
echo "Type: $PROJECT_TYPE"

# Initialize agency if not exists
if [ ! -d "$PROJECT_PATH/.agency" ]; then
    echo ""
    echo "Initializing agency..."
    cd "$PROJECT_PATH"

    # Try to detect project type
    if grep -q "python\|Python" "$PROJECT_PATH/README.md" 2>/dev/null; then
        LANG="python"
    elif grep -q "JavaScript\|TypeScript" "$PROJECT_PATH/README.md" 2>/dev/null; then
        LANG="javascript"
    elif grep -q "Go\|Golang" "$PROJECT_PATH/README.md" 2>/dev/null; then
        LANG="go"
    else
        LANG="python"
    fi

    agency hire --dir . --type cli --language "$LANG" --team solo --non-interactive 2>/dev/null || \
        agency init --dir . --template basic
    echo "Agency initialized"
else
    echo "Agency already initialized"
fi

echo ""
echo "=== Next Steps ==="
echo "1. Start session: agency session start"
echo "2. Attach: agency session attach"
echo "3. Work through tasks"
echo "4. Stop: agency session stop"
echo ""
echo "After completion:"
echo "5. Run tests (if project has them)"
echo "6. Copy TEST_REPORT_TEMPLATE.md to TEST_REPORT.md"
echo "7. Fill in results"
