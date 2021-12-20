#!/bin/bash

brew install zsh
sudo sh -c 'echo /usr/local/bin/zsh >> /etc/shells'
echo "chsh -s /usr/local/bin/zsh" ; chsh -s /usr/local/bin/zsh
