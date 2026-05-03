#!/usr/bin/env bash
# Prints all files and directories under the repo root, excluding noise dirs.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

find "$REPO_ROOT" \
    -mindepth 1 \
    \( \
        -name ".git" \
        -o -name ".venv" \
        -o -name ".claude" \
        -o -name ".ruff_cache" \
        -o -name ".github" \
    \) -prune \
    -o -print \
| sed "s|^$(pwd)/||"
