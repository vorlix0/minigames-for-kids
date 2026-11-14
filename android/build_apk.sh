#!/usr/bin/env bash
# Build in Ubuntu/WSL with Buildozer and its dependencies already installed.
set -euo pipefail
repo="$(cd "$(dirname "$0")/.." && pwd)"
if [[ "${BUILD_RELEASE_AAB:-0}" == 1 ]]; then
    for name in P4A_RELEASE_KEYSTORE P4A_RELEASE_KEYALIAS P4A_RELEASE_KEYSTORE_PASSWD P4A_RELEASE_KEYALIAS_PASSWD; do
        if [[ -z "${!name:-}" ]]; then
            echo "Missing required signing variable: $name" >&2
            exit 1
        fi
    done
    if [[ ! -f "$P4A_RELEASE_KEYSTORE" ]]; then
        echo "Signing keystore does not exist." >&2
        exit 1
    fi
fi
stage="$(mktemp -d "$HOME/minigames-build.XXXXXXXX")"
mkdir -p "$stage/games/maze"
cp "$repo/android/main.py" "$repo/android/buildozer.spec" "$repo/android/constraints.txt" "$stage/"
cp "$repo/games/__init__.py" "$stage/games/"
cp "$repo/games/maze/"{__init__,logic,themes}.py "$stage/games/maze/"
cd "$stage"
PIP_CONSTRAINT="$stage/constraints.txt" buildozer android debug
shopt -s nullglob
apks=("$stage"/bin/*.apk)
if (( ${#apks[@]} != 1 )); then
    echo "Expected exactly one APK in $stage/bin, found ${#apks[@]}." >&2
    exit 1
fi
if [[ -n "${APK_OUTPUT_DIR:-}" ]]; then
    mkdir -p "$APK_OUTPUT_DIR"
    cp "${apks[0]}" "$APK_OUTPUT_DIR/"
fi
echo "APK: ${apks[0]}"

if [[ "${BUILD_RELEASE_AAB:-0}" == 1 ]]; then
    PIP_CONSTRAINT="$stage/constraints.txt" buildozer android release
    bundles=("$stage"/bin/*.aab)
    if (( ${#bundles[@]} != 1 )); then
        echo "Expected exactly one AAB in $stage/bin, found ${#bundles[@]}." >&2
        exit 1
    fi
    if [[ -n "${AAB_OUTPUT_DIR:-}" ]]; then
        mkdir -p "$AAB_OUTPUT_DIR"
        cp "${bundles[0]}" "$AAB_OUTPUT_DIR/"
    fi
    echo "AAB: ${bundles[0]}"
fi
