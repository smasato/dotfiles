#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Current Sound Device
# @raycast.mode inline
# @raycast.refreshTime 10s

# Optional parameters:
# @raycast.icon 🎵
# @raycast.packageName Sound Control

# Documentation:
# @raycast.description Display the currently active sound device.
# @raycast.author smasato
# @raycast.authorURL https://raycast.com/smasato

if ! command -v SwitchAudioSource &> /dev/null; then
    echo "SwitchAudioSource is not installed."
    exit 1
fi

input_device=$(SwitchAudioSource -c -t input)
output_device=$(SwitchAudioSource -c -t output)

echo "🔊 $output_device / 🎙️ $input_device"
