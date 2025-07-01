#!/bin/sh

input=$(cat -)

# Get transcript_path from input
transcript_path=$(echo "$input" | jq -r '.transcript_path')

# Exit if the transcript file does not exist
if [ ! -f "$transcript_path" ]; then
    exit 0
fi

# Get the working directory from the transcript file
cwd=$(grep 'parentUuid":null' "$transcript_path" | jq -r '.cwd')

# Get message from input
message=$(echo "$input" | jq -r '.message')

# Display the notification with terminal-notifier
terminal-notifier -title "Claude Code [Notification]" -subtitle "$cwd" -message "$message"
