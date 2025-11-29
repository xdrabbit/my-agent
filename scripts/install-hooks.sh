#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
HOOKS_DIR="$ROOT_DIR/.githooks"

if [ ! -d "$HOOKS_DIR" ]; then
  echo "No .githooks directory found in project root"
  exit 1
fi

git config core.hooksPath "$HOOKS_DIR"
echo "Installed git hooks from $HOOKS_DIR (git config core.hooksPath updated)."
echo "To revert: git config --unset core.hooksPath"
