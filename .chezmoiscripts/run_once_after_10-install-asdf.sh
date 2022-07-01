#!/bin/bash

plugins=("nodejs" "ruby" "python" "php")

for i in "${plugins[@]}"; do
    asdf plugin-add $i
    asdf install $i latest
done
