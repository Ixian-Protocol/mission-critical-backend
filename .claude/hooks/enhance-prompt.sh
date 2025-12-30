#!/bin/bash
#
# UserPromptSubmit hook that uses Claude to review and reformulate prompts.
#
# This hook pipes the user's prompt to Claude CLI with instructions to
# reformulate it into a more complete and informative request.
#

set -e

# Read the JSON input from stdin
INPUT=$(cat)

# Extract the prompt from the JSON
PROMPT=$(echo "$INPUT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('prompt', ''))")

# Skip empty prompts
if [ -z "$PROMPT" ]; then
    exit 0
fi

# Common acknowledgment/confirmation patterns that don't need reformulation
PROMPT_LOWER=$(echo "$PROMPT" | tr '[:upper:]' '[:lower:]' | xargs)
case "$PROMPT_LOWER" in
    "yes"|"no"|"ok"|"okay"|"sure"|"yep"|"nope"|"y"|"n"|"yeah"|"nah"|"go ahead"|"proceed"|"continue"|"skip"|"cancel"|"abort"|"done"|"thanks"|"thank you"|"looks good"|"lgtm"|"approved"|"reject"|"accept")
        exit 0
        ;;
esac

# Skip very short prompts (less than 3 words) that are likely simple responses
WORD_COUNT=$(echo "$PROMPT" | wc -w | tr -d ' ')
if [ "$WORD_COUNT" -lt 3 ]; then
    exit 0
fi

# Check if this is a slash command
SLASH_COMMAND=""
if [[ "$PROMPT" == /* ]]; then
    # Extract the slash command (first word)
    SLASH_COMMAND=$(echo "$PROMPT" | awk '{print $1}')
    # Extract the rest of the prompt after the slash command
    PROMPT_BODY=$(echo "$PROMPT" | sed "s|^$SLASH_COMMAND[[:space:]]*||")

    # If there's no body after the slash command, skip reformulation
    if [ -z "$PROMPT_BODY" ]; then
        exit 0
    fi
fi

# Determine what to send to Claude for reformulation
if [ -n "$SLASH_COMMAND" ]; then
    PROMPT_TO_ENHANCE="$PROMPT_BODY"
else
    PROMPT_TO_ENHANCE="$PROMPT"
fi

# Use Claude to reformulate the prompt
ENHANCED=$(claude -p "You are a prompt engineer. Your task is to review the following user prompt and reformulate it to be more complete, specific, and informative for an AI coding assistant to process.

Rules:
1. Keep the original intent intact
2. Add specificity where the request is vague
3. Include relevant context that would help (e.g., mentioning error handling, edge cases, testing considerations)
4. If the prompt is already clear, complete, and specific enough, return it EXACTLY unchanged
5. Do NOT add unnecessary verbosity - be concise
6. Do NOT reformulate simple questions that are already clear
7. Output ONLY the reformulated prompt, nothing else (no preamble, no explanation)

User prompt to reformulate:
$PROMPT_TO_ENHANCE" --allowedTools "" --output-format text 2>/dev/null)

# Trim whitespace from enhanced prompt
ENHANCED=$(echo "$ENHANCED" | xargs)

# If Claude returned something different, output it as additional context
if [ -n "$ENHANCED" ] && [ "$ENHANCED" != "$PROMPT_TO_ENHANCE" ]; then
    # If there was a slash command, prepend it back
    if [ -n "$SLASH_COMMAND" ]; then
        FINAL_ENHANCED="$SLASH_COMMAND $ENHANCED"
        ORIGINAL_DISPLAY="$PROMPT"
    else
        FINAL_ENHANCED="$ENHANCED"
        ORIGINAL_DISPLAY="$PROMPT"
    fi

    cat << EOF
<user-prompt-submit-hook>
Your prompt has been analyzed and reformulated for clarity:

Original: $ORIGINAL_DISPLAY

Reformulated: $FINAL_ENHANCED

Please proceed with the reformulated version of the request.
</user-prompt-submit-hook>
EOF
fi

exit 0
