#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INNER="$ROOT_DIR/streamdeck-linux"
CONFIG_DIR="$HOME/.config/streamdeck-tool"
APP_DIR="$HOME/.local/share/streamdeck-tool"
TOGGLE="$HOME/bin/streamdeck-toggle"
DESKTOP_FILE="$HOME/.local/share/applications/streamdeck-toggle.desktop"

if [ ! -f "$INNER/install.sh" ]; then
  echo "ERROR: streamdeck-linux/install.sh was not found."
  exit 1
fi

echo "==> Installing Linux Mint/Ubuntu dependencies"
if command -v apt-get >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y \
    python3 python3-venv python3-pip pkg-config playerctl \
    libusb-1.0-0-dev libhidapi-libusb0 libhidapi-dev
else
  echo "apt-get was not found. Install the dependencies listed in streamdeck-linux/README.md, then rerun this installer."
fi

echo "==> Preparing starter configuration"
mkdir -p "$CONFIG_DIR"
if [ ! -f "$CONFIG_DIR/config.yaml" ]; then
  cp "$ROOT_DIR/config.example.yaml" "$CONFIG_DIR/config.yaml"
  echo "    Created $CONFIG_DIR/config.yaml"
else
  echo "    Existing config preserved: $CONFIG_DIR/config.yaml"
fi

echo "==> Running the original Stream Deck installer"
chmod +x "$INNER/install.sh"
"$INNER/install.sh"

echo "==> Creating one-click start/stop toggle"
mkdir -p "$HOME/bin"
cat > "$TOGGLE" <<'TOGGLEEOF'
#!/usr/bin/env bash
set -e

APP="$HOME/.local/share/streamdeck-tool/venv/bin/python"
CONFIG="$HOME/.config/streamdeck-tool/config.yaml"

# Stop a running user service first, if it is active.
if systemctl --user is-active --quiet streamdeck.service 2>/dev/null; then
  systemctl --user stop streamdeck.service
  exit 0
fi

# Stop a manually launched copy if one is running.
if pgrep -u "$USER" -f "python.*-m streamdeck_tool.main" >/dev/null 2>&1; then
  pkill -u "$USER" -f "python.*-m streamdeck_tool.main"
  exit 0
fi

# Start the service when it has been enabled; otherwise run in the background.
if systemctl --user is-enabled --quiet streamdeck.service 2>/dev/null; then
  systemctl --user start streamdeck.service
else
  nohup "$APP" -m streamdeck_tool.main --config "$CONFIG" \
    >"$HOME/.local/share/streamdeck-tool/streamdeck.log" 2>&1 &
fi
TOGGLEEOF
chmod +x "$TOGGLE"

echo "==> Creating application-menu launcher"
mkdir -p "$HOME/.local/share/applications"
cat > "$DESKTOP_FILE" <<EOF2
[Desktop Entry]
Name=Stream Deck Toggle
Comment=Start or stop the Stream Deck Linux controller
Exec=$TOGGLE
Icon=input-gaming
Terminal=false
Type=Application
Categories=Utility;
EOF2
chmod +x "$DESKTOP_FILE"

# Refresh desktop database when available. Failure is harmless.
command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$HOME/.local/share/applications" >/dev/null 2>&1 || true

cat <<EOF3

Installation complete.

NEXT STEPS
1. Log out of Linux Mint/Ubuntu and log back in once.
2. In OBS: Tools > WebSocket Server Settings.
   Enable the WebSocket server and note/set its password.
3. Edit:
   $CONFIG_DIR/config.yaml
   Change obs.password and make the OBS scene/input names match your OBS setup exactly.
4. Open the application menu and search for:
   Stream Deck Toggle
5. Click it once to start the controller; click it again to stop it.

To edit the config:
  nano $CONFIG_DIR/config.yaml

Manual log file (when not using systemd):
  $APP_DIR/streamdeck.log
EOF3
