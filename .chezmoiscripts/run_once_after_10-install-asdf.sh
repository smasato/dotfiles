#!/bin/bash

installed_plugins=(`asdf plugin-list`)
plugins=("nodejs" "ruby" "python" "php")

for i in "${plugins[@]}"; do
    if [[ " ${installed_plugins[*]} " =~ " ${i} " ]]; then
        echo $i
    else
        asdf plugin-add $i
    fi
done
