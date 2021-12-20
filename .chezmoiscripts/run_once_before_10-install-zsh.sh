#!/bin/bash

brew install zsh zsh-completions
sudo sh -c 'echo /usr/local/bin/zsh >> /etc/shells'
echo "chsh -s /usr/local/bin/zsh" ; chsh -s /usr/local/bin/zsh

brew tap "romkatv/powerlevel10k"
brew install "romkatv/powerlevel10k/powerlevel10k"
brew install peco
brew install asdf
brew install exa
