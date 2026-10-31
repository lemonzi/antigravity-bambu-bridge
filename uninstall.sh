#!/usr/bin/env bash
set -e

# Colors
RED='\033[0;31m'
BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${BLUE}==>${NC} Uninstalling Antigravity Bambu Studio Bridge..."

# 1. Unload and remove LaunchAgent
if [[ "$OSTYPE" == "darwin"* ]]; then
  PLIST_PATH="$HOME/Library/LaunchAgents/com.antigravity.bambu-bridge.plist"
  if [ -f "$PLIST_PATH" ]; then
    echo -e "${BLUE}==>${NC} Stopping and removing launchd agent..."
    launchctl unload "$PLIST_PATH" 2>/dev/null || true
    rm -f "$PLIST_PATH"
  fi
fi

# 2. Remove binaries
echo -e "${BLUE}==>${NC} Removing binaries..."
rm -f "$HOME/.local/bin/bambu-bridge.py"
rm -f "$HOME/.local/bin/bambu-card.py"

# 3. Remove plugin
echo -e "${BLUE}==>${NC} Removing Antigravity plugin..."
rm -rf "$HOME/.gemini/config/plugins/bambu-bridge"

echo -e "${GREEN}✓${NC} Uninstallation complete."
