#!/usr/bin/env bash

[[ "$CI" = true ]] || [[ -n "$GITHUB_ACTIONS" ]] || [[ -n "$VIRTUAL_ENV" ]] || exit 1

set -ex

echo "CI=$CI"
echo "GITHUB_ACTIONS=$GITHUB_ACTIONS"
echo "VIRTUAL_ENV=$VIRTUAL_ENV"

python -m pip install --disable-pip-version-check --upgrade pip setuptools
python -m pip install --upgrade -r requirements.txt
python -m pip install -e .