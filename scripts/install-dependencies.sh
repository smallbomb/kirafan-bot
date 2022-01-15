#!/usr/bin/env bash

[[ "$CI" = true ]] || [[ -n "$GITHUB_ACTIONS" ]] || [[ -n "$VIRTUAL_ENV" ]] || exit 1

set -ex

python -m pip install --upgrade pip
pip install -r requirements.txt
if [[ -n "$ImageOS" ]] && [[ "$ImageOS" = ubuntu* ]]; then
  sudo apt-get install xvfb
  Xvfb :0 -screen 0 1024x768x24 > /dev/null 2>&1 &
fi
