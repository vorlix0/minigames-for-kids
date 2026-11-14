#!/usr/bin/env bash
# Build in Ubuntu/WSL with Buildozer and its dependencies already installed.
set -euo pipefail
repo="$(cd "$(dirname "$0")/.." && pwd)"
stage="$(mktemp -d "$HOME/minigames-build.XXXXXXXX")"
mkdir -p "$stage/games/maze"
cp "$repo/android/main.py" "$repo/android/buildozer.spec" "$repo/android/constraints.txt" "$stage/"
cp "$repo/games/__init__.py" "$stage/games/"
cp "$repo/games/maze/"{__init__,logic,themes}.py "$stage/games/maze/"
cd "$stage"
PIP_CONSTRAINT="$stage/constraints.txt" buildozer android debug
echo "APK: $(ls "$stage"/bin/*.apk)"
