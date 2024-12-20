#!/bin/bash

output_file="cursor_extensions.txt"

if ! command -v cursor >/dev/null; then
    echo "Cursor is not installed."
    exit 1
fi

cursor --list-extensions > "$output_file"

if [ $? -eq 0 ]; then
    echo "Extensions list has been saved to $output_file"
else
    echo "Failed to get extensions list"
    exit 1
fi