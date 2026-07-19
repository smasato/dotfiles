#!/bin/bash

set -eu

# Install global agent skills via the mise-managed `skills` CLI.
# Reruns when this list changes (e.g. when a skill is added below).
# skills: ogulcancelik/herdr

if ! command -v skills >/dev/null 2>&1; then
  echo "skills not found on PATH; skipping skill install"
  exit 0
fi

echo "Adding skill: ogulcancelik/herdr"
skills add ogulcancelik/herdr --skill herdr -g
