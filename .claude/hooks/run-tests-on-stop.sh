#!/bin/bash
#
# Stop hook that runs tests after code changes are made.
#
# This hook checks if code was modified during the session and runs
# the test suite to validate the changes.
#

set -e

# Read the JSON input from stdin
INPUT=$(cat)

# Extract relevant fields
TRANSCRIPT_PATH=$(echo "$INPUT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('transcript_path', ''))")
STOP_HOOK_ACTIVE=$(echo "$INPUT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('stop_hook_active', False))")

# Prevent infinite loops - if we're already in a stop hook, exit
if [ "$STOP_HOOK_ACTIVE" = "True" ]; then
    exit 0
fi

# Check if any Python files were modified by looking at the transcript
# We look for Write or Edit tool uses on .py files
if [ -z "$TRANSCRIPT_PATH" ] || [ ! -f "$TRANSCRIPT_PATH" ]; then
    exit 0
fi

# Check if code was modified in this session (Write or Edit on .py files)
CODE_MODIFIED=$(python3 << 'PYEOF'
import json
import sys

transcript_path = sys.argv[1] if len(sys.argv) > 1 else ""
if not transcript_path:
    print("false")
    sys.exit(0)

try:
    with open(transcript_path, 'r') as f:
        modified = False
        for line in f:
            try:
                entry = json.loads(line.strip())
                # Look for tool uses
                if entry.get("type") == "assistant":
                    message = entry.get("message", {})
                    content = message.get("content", [])
                    for block in content:
                        if block.get("type") == "tool_use":
                            tool_name = block.get("name", "")
                            tool_input = block.get("input", {})

                            # Check if it's a Write or Edit on a Python file
                            if tool_name in ("Write", "Edit"):
                                file_path = tool_input.get("file_path", "")
                                if file_path.endswith(".py") and "/test" not in file_path and "test_" not in file_path:
                                    modified = True
                                    break
                    if modified:
                        break
            except json.JSONDecodeError:
                continue

        print("true" if modified else "false")
except Exception as e:
    print("false")
PYEOF
"$TRANSCRIPT_PATH")

# If no code was modified, skip tests
if [ "$CODE_MODIFIED" != "true" ]; then
    exit 0
fi

# Check if tests directory exists
if [ ! -d "$CLAUDE_PROJECT_DIR/tests" ]; then
    exit 0
fi

# Check if there are any test files
TEST_COUNT=$(find "$CLAUDE_PROJECT_DIR/tests" -name "test_*.py" -o -name "*_test.py" 2>/dev/null | wc -l | tr -d ' ')
if [ "$TEST_COUNT" -eq 0 ]; then
    exit 0
fi

# Run the tests and capture output
cd "$CLAUDE_PROJECT_DIR"
TEST_OUTPUT=$(uv run pytest tests/ -v --tb=short 2>&1) || TEST_EXIT_CODE=$?
TEST_EXIT_CODE=${TEST_EXIT_CODE:-0}

# If tests failed, block the stop and report back to Claude
if [ "$TEST_EXIT_CODE" -ne 0 ]; then
    # Output JSON to block stopping and provide feedback
    cat << EOF
{
  "decision": "block",
  "reason": "Tests failed after your code changes. Please review and fix the failing tests:\n\n$TEST_OUTPUT"
}
EOF
    exit 0
fi

# Tests passed - allow stop but add a note
echo "Tests passed successfully after code changes."
exit 0
