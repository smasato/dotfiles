#!/bin/bash

brew install zsh zsh-completions

if [ `uname -m` = 'arm64' ]; then
    sudo sh -c 'echo /opt/homebrew/bin/zsh >> /etc/shells'
    echo "chsh -s /opt/homebrew/bin/zsh" ; chsh -s /opt/homebrew/bin/zsh
fi

if [ `uname -m` = 'x86_64' ]; then
    sudo sh -c 'echo /usr/local/bin/zsh >> /etc/shells'
    echo "chsh -s /usr/local/bin/zsh" ; chsh -s /usr/local/bin/zsh
fi

brew install peco
brew install exa
