#!/usr/bin/env bash

[[ "$CI" = true ]] || [[ -n "$GITHUB_ACTIONS" ]] || [[ -n "$VIRTUAL_ENV" ]] || exit 1

set -ex

python -m pip install pyinstaller
pyinstaller -F main.py
ls
mv ./dist/main.exe ./kirafan-bot.exe
tar cvf kirafan-bot-pre-release-win-x64-exe.tar kirafan-bot.exe img_1274x718 setting.json
