#!/usr/bin/env bash
set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}==>${NC} Installing Antigravity Bambu Studio Bridge..."

# 1. Paths
INSTALL_DIR="$HOME/.local/bin"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
PLIST_NAME="com.antigravity.bambu-bridge.plist"
PLUGIN_DIR="$HOME/.gemini/config/plugins/bambu-bridge"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$INSTALL_DIR"
mkdir -p "$LAUNCH_AGENTS_DIR"
mkdir -p "$PLUGIN_DIR/rules"

# 2. Install executables
echo -e "${BLUE}==>${NC} Copying binaries to ${INSTALL_DIR}..."
cp "$REPO_DIR/bin/bambu-bridge.py" "$INSTALL_DIR/bambu-bridge.py"
cp "$REPO_DIR/bin/bambu-card.py" "$INSTALL_DIR/bambu-card.py"
chmod +x "$INSTALL_DIR/bambu-bridge.py" "$INSTALL_DIR/bambu-card.py"

# 3. Configure and load macOS LaunchAgent
if [[ "$OSTYPE" == "darwin"* ]]; then
  echo -e "${BLUE}==>${NC} Configuring macOS LaunchAgent..."
  sed "s|__HOME__|$HOME|g" "$REPO_DIR/launchd/$PLIST_NAME" > "$LAUNCH_AGENTS_DIR/$PLIST_NAME"
  
  # Unload previous instance if present
  launchctl unload "$LAUNCH_AGENTS_DIR/$PLIST_NAME" 2>/dev/null || true
  
  # Load new agent
  launchctl load "$LAUNCH_AGENTS_DIR/$PLIST_NAME"
  echo -e "${GREEN}✓${NC} Background daemon registered with launchd"
fi

# 4. Install Antigravity Plugin & Rules
echo -e "${BLUE}==>${NC} Registering Antigravity plugin in ${PLUGIN_DIR}..."
cp "$REPO_DIR/plugin/plugin.json" "$PLUGIN_DIR/plugin.json"
cp "$REPO_DIR/plugin/rules/AGENTS.md" "$PLUGIN_DIR/rules/AGENTS.md"
echo -e "${GREEN}✓${NC} Agent directives installed"

# 5. Health verification
echo -e "${BLUE}==>${NC} Verifying bridge status..."
sleep 1
if curl -s "http://127.0.0.1:48921/health" | grep -q '"status": "ok"'; then
  echo -e "${GREEN}✓${NC} Bridge is healthy and listening on http://127.0.0.1:48921"
else
  echo -e "${YELLOW}!${NC} Daemon started. If health check failed, ensure Python 3 is installed."
fi

echo ""
echo -e "${GREEN}Installation successful!${NC}"
echo -e "Your Antigravity agents will now automatically deliver 1-click Bambu Studio cards for any 3D model."
