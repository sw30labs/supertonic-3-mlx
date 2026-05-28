#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
export SUPERTONIC_GUI_HOST="${SUPERTONIC_GUI_HOST:-127.0.0.1}"
export SUPERTONIC_GUI_PORT="${SUPERTONIC_GUI_PORT:-8795}"
uv run python gui/server.py

