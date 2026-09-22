#!/usr/bin/env bash
# Install the Book Genesis skills for one agent.
# Usage: bash install.sh <target> [--dest PATH] [--agents-dest PATH] [--dry-run] [--force]
# List targets with: python runner/installer.py targets
set -euo pipefail

repo_dir="$(cd "$(dirname "$0")" && pwd)"

if command -v python3 >/dev/null 2>&1; then
  python_bin="python3"
elif command -v python >/dev/null 2>&1; then
  python_bin="python"
else
  echo "Python 3.10 or newer was not found in PATH." >&2
  exit 1
fi

if [ "$#" -eq 0 ]; then
  echo "Usage: bash install.sh <target> [--dest PATH] [--agents-dest PATH] [--dry-run] [--force]" >&2
  echo "Targets:" >&2
  "$python_bin" "$repo_dir/runner/installer.py" targets >&2
  exit 2
fi

exec "$python_bin" "$repo_dir/runner/installer.py" install "$@"
