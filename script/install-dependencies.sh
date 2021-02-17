#!/usr/bin/env bash

[[ "$CI" = true ]] || [[ -n "$GITHUB_ACTIONS" ]] || [[ -n "$VIRTUAL_ENV" ]] || exit 1

set -ex

echo "$CI"
echo "$GITHUB_ACTIONS"
echo "$VIRTUAL_ENV"

python -m pip install --disable-pip-version-check --upgrade pip setuptools
python -m pip install --upgrade -r dev-requirements.txt
python -m pip install pycountry
python -m pip install -e .