#!/usr/local/bin/zsh

installed_plugins=(`asdf plugin-list`)
plugins=(nodejs ruby python)

for i in $plugins; do
    if (( ${installed_plugins[(I)$i]} )); then
        echo $i
    else
        asdf plugin-add $i
    fi
done
