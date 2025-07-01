#!/bin/sh

# Get transcript_path from standard input
transcript_path=$(jq -r '.transcript_path')

# Exit if the transcript file does not exist
if [ ! -f "$transcript_path" ]; then
    exit 0
fi

# Get the working directory from the transcript file
cwd=$(grep 'parentUuid":null' "$transcript_path" | jq -r '.cwd')

# Get message from standard input
message=$(jq -r '.message')

# Display the notification with terminal-notifier
terminal-notifier -title "Claude Code [Notification]" -subtitle "$cwd" -message "$message"
