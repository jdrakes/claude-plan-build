#!/usr/bin/env bash
# Copy fixture/ into the target directory (first argument, or the current
# directory when no argument is given), then init a git repo there with one
# commit so the tree is clean. Safe to run twice: the second run finds the
# same files already in place, so there is nothing new to commit.
set -e

target="${1:-.}"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source_dir="$script_dir/fixture"

mkdir -p "$target"
cp -R "$source_dir"/. "$target"/

# A prior `make test` in this same target leaves __pycache__ and
# .pytest_cache behind. Clear them so they never count as a change and
# force a second, spurious commit.
find "$target" -name "__pycache__" -type d -prune -exec rm -rf {} +
rm -rf "$target/.pytest_cache"

if [ ! -d "$target/.git" ]; then
    git init -q "$target"
fi

if [ -n "$(git -C "$target" status --porcelain)" ]; then
    git -C "$target" add -A
    git -C "$target" \
        -c user.email="scaffold@example.com" \
        -c user.name="scaffold" \
        commit -q -m "Scaffold the fixture"
fi
