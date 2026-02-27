#!/bin/bash
#
# QuickVoice Setup Script
# =======================
# Installs dependencies and sets up auto-start on login.
#
# Usage:
#   chmod +x setup.sh
#   ./setup.sh          # Install everything
#   ./setup.sh uninstall # Remove auto-start
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST_NAME="com.quickvoice.agent.plist"
PLIST_SRC="$SCRIPT_DIR/$PLIST_NAME"
PLIST_DST="$HOME/Library/LaunchAgents/$PLIST_NAME"

# ─── Colors ──────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

info()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; exit 1; }

# ─── Uninstall ───────────────────────────────────────────────────
if [ "$1" = "uninstall" ]; then
    echo "Uninstalling QuickVoice auto-start..."
    launchctl unload "$PLIST_DST" 2>/dev/null && info "Agent unloaded." || warn "Agent was not loaded."
    rm -f "$PLIST_DST" && info "Plist removed." || warn "Plist was not found."
    echo "Done. QuickVoice will no longer start on login."
    exit 0
fi

# ─── Install ─────────────────────────────────────────────────────
echo "=============================="
echo "  QuickVoice Setup"
echo "=============================="
echo

# 1. Check for Homebrew
if ! command -v brew &>/dev/null; then
    error "Homebrew is required. Install it from https://brew.sh"
fi
info "Homebrew found."

# 2. Install portaudio (required by PyAudio)
if ! brew list portaudio &>/dev/null; then
    warn "Installing portaudio..."
    brew install portaudio
fi
info "portaudio installed."

# 3. Check for uv (fast package installer)
if ! command -v uv &>/dev/null; then
    warn "Installing uv (fast Python package installer)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi
info "uv found."

# 4. Install Python dependencies
echo
warn "Installing Python dependencies..."
uv pip install --system -r "$SCRIPT_DIR/requirements.txt"
info "Python dependencies installed."

# 4. Set up Launch Agent for auto-start
echo
warn "Setting up auto-start on login..."
mkdir -p "$HOME/Library/LaunchAgents"

# Update the plist with the correct Python path
PYTHON_PATH=$(which python3)
sed "s|/usr/bin/env|$PYTHON_PATH|g" "$PLIST_SRC" > "$PLIST_DST.tmp"
# Also ensure the script path is absolute
sed "s|python3|$PYTHON_PATH|g" "$PLIST_DST.tmp" > "$PLIST_DST.tmp2" 2>/dev/null || true
# Just copy the original plist directly — it uses /usr/bin/env which is reliable
cp "$PLIST_SRC" "$PLIST_DST"
rm -f "$PLIST_DST.tmp" "$PLIST_DST.tmp2" 2>/dev/null

# Load the agent
launchctl unload "$PLIST_DST" 2>/dev/null || true
launchctl load "$PLIST_DST"
info "Launch Agent installed and loaded."

echo
echo "=============================="
echo "  Setup Complete!"
echo "=============================="
echo
echo "QuickVoice will now start automatically on login."
echo "You can also start it manually:  python3 $SCRIPT_DIR/quickvoice.py"
echo
echo "⚠️  IMPORTANT: Grant these permissions in System Settings > Privacy & Security:"
echo "   • Accessibility: your terminal app (for global hotkeys)"
echo "   • Microphone: your terminal app (for audio recording)"
echo
