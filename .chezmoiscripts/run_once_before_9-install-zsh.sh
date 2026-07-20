#!/bin/bash

brew install zsh zsh-completions

sudo sh -c 'echo /opt/homebrew/bin/zsh >> /etc/shells'
echo "chsh -s /opt/homebrew/bin/zsh" ; chsh -s /opt/homebrew/bin/zsh
