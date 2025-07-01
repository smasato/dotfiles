#!/bin/sh

# Get transcript_path from standard input
transcript_path=$(jq -r '.transcript_path')

# Exit if the transcript file does not exist
if [ ! -f "$transcript_path" ]; then
    exit 0
fi

# Get the working directory from the transcript file
cwd=$(grep 'parentUuid":null' "$transcript_path" | jq -r '.cwd')

# Get the message from the last line of the transcript file
# Use "Completed" if the message does not exist
message=$(tail -n 1 "$transcript_path" | jq -r '.message.content[0].text // "Completed"')

# Display the notification with terminal-notifier
terminal-notifier -title "Claude Code [Stop]" -subtitle "$cwd" -message "$message"
