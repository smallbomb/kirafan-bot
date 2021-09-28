#!/usr/bin/env bash

[[ "$CI" = true ]] || [[ -n "$GITHUB_ACTIONS" ]] || [[ -n "$VIRTUAL_ENV" ]] || exit 1

set -ex

python -m pip install pyinstaller
pyinstaller -F src/main.py
mv ./dist/main* ./kirafan-bot.exe
tar cvf kirafan-bot.tar kirafan-bot.exe bot_setting.json img_1274x718 LICENSE
