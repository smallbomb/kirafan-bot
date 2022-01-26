#!/usr/bin/env bash

[[ "$CI" = true ]] || [[ -n "$GITHUB_ACTIONS" ]] || [[ -n "$VIRTUAL_ENV" ]] || exit 1

set -ex

python -m pip install --upgrade pip
pip install -r requirements.txt
if [[ -n "$ImageOS" ]] && [[ "$ImageOS" = ubuntu* ]]; then
  sudo apt-get install xvfb
  sudo apt-get install scrot
  Xvfb :0 -screen 0 1366x768x24 > /dev/null 2>&1 &
fi
