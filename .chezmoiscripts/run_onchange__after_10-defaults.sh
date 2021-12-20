#!/bin/bash

# desktopservices
defaults write com.apple.desktopservices DSDontWriteNetworkStores true
defaults write com.apple.desktopservices DSDontWriteUSBStores -bool true

# finder
defaults write com.apple.finder ShowTabView -bool true
defaults write com.apple.finder ShowPathbar -bool true
defaults write com.apple.finder ShowStatusBar -bool true
defaults write com.apple.finder "FXEnableExtensionChangeWarning" -bool "false" && killall Finder
defaults write NSGlobalDomain "NSDocumentSaveNewDocumentsToCloud" -bool "false" 

# keyboard
defaults write NSGlobalDomain KeyRepeat -int 2
defaults write NSGlobalDomain InitialKeyRepeat -int 15
defaults write -g ApplePressAndHoldEnabled -bool false

# dock
defaults write com.apple.systempreferences AttentionPrefBundleIDs 0
defaults write com.apple.dock "orientation" -string "right"
defaults write com.apple.dock "tilesize" -int "36"
defaults write com.apple.dock "autohide" -bool "true"
defaults write com.apple.dock "autohide-time-modifier" -float "0"
defaults write com.apple.dock "autohide-delay" -float "0"
defaults write com.apple.dock "show-recents" -bool "false"
killall Dock

# screenshots
defaults write com.apple.screencapture "disable-shadow" -bool "true" 
defaults write com.apple.screencapture "location" -string "~/Pictures" && killall SystemUIServer
defaults write com.apple.screencapture "show-thumbnail" -bool "false" 

# startup chime
sudo nvram StartupMute=%01
