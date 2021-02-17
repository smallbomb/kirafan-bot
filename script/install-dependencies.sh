#!/usr/bin/env bash

[[ "$CI" = true ]] || [[ -n "$GITHUB_ACTIONS" ]] || [[ -n "$VIRTUAL_ENV" ]] || exit 1

set -ex

echo "CI=$CI"
echo "GITHUB_ACTIONS=$GITHUB_ACTIONS"
echo "VIRTUAL_ENV=$VIRTUAL_ENV"


python -m pip install --upgrade pip
python -m pip install flake8 pytest
python install.py
