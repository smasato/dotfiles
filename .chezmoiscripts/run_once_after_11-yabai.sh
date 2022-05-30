#!/bin/bash

sudo sh -c 'echo "$(echo $SUDO_USER) ALL = (root) NOPASSWD: $(which yabai) --load-sa" > /private/etc/sudoers.d/yabai'
