#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

YES=0
DOWNLOAD_MODEL=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    -y|--yes)
      YES=1
      ;;
    --download-model)
      DOWNLOAD_MODEL=1
      ;;
    -h|--help)
      cat <<'EOF'
Usage: ./install.sh [options]

Options:
  -y, --yes         Do not prompt before installing uv.
  --download-model  Download mlx-community/supertonic-3 into models/supertonic-3.
  -h, --help        Show this help.
EOF
      exit 0
      ;;
    *)
      printf 'Unknown option: %s\n' "$1" >&2
      exit 2
      ;;
  esac
  shift
done

if [[ -t 1 ]]; then
  BOLD=$'\033[1m'; GREEN=$'\033[1;32m'; CYAN=$'\033[1;36m'; YELLOW=$'\033[1;33m'; RED=$'\033[1;31m'; RESET=$'\033[0m'
else
  BOLD=""; GREEN=""; CYAN=""; YELLOW=""; RED=""; RESET=""
fi

step() { printf '\n%s=>%s %s\n' "$CYAN" "$RESET" "$1"; }
ok() { printf '  %sok%s %s\n' "$GREEN" "$RESET" "$1"; }
warn() { printf '  %swarn%s %s\n' "$YELLOW" "$RESET" "$1" >&2; }
fail() { printf '\n%serror%s %s\n' "$RED" "$RESET" "$1" >&2; exit 1; }

export PATH="${XDG_BIN_HOME:-$HOME/.local/bin}:$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"

OS="$(uname -s)"
ARCH="$(uname -m)"
if [[ "$OS" != "Darwin" || "$ARCH" != "arm64" ]]; then
  fail "Supertonic 3 MLX requires Apple Silicon macOS. Detected $OS/$ARCH."
fi
ok "platform: $OS/$ARCH"

for tool in git curl; do
  command -v "$tool" >/dev/null 2>&1 || fail "$tool is required."
done
ok "git + curl present"

if ! command -v uv >/dev/null 2>&1; then
  step "uv is not installed"
  if [[ "$YES" -ne 1 ]]; then
    read -r -p "Install uv with the official installer? [y/N] " reply
    case "$reply" in
      y|Y|yes|YES) ;;
      *) fail "uv is required. Install from https://github.com/astral-sh/uv and rerun." ;;
    esac
  fi
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="${XDG_BIN_HOME:-$HOME/.local/bin}:$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
fi
ok "uv present: $(uv --version)"

mkdir -p "$ROOT/models" "$ROOT/output/gui"

step "Syncing Supertonic 3 MLX dependencies"
cd "$ROOT"
uv sync --python 3.11
ok "environment ready"

if [[ "$DOWNLOAD_MODEL" -eq 1 ]]; then
  step "Downloading mlx-community/supertonic-3"
  ./supertonic3 download
  ok "model downloaded"
else
  warn "model not downloaded yet. Run ./install.sh --download-model before generating."
fi

printf '\n%sReady.%s Try:\n' "$BOLD" "$RESET"
printf '  ./gui.sh\n'
printf '  ./supertonic3 generate --text "Supertonic 3 is running locally through MLX." --lang en --voice M1\n'

