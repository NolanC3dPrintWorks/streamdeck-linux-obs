#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$HOME/.local/share/streamdeck-tool"
CONFIG_DIR="$HOME/.config/streamdeck-tool"
SERVICE="$HOME/.config/systemd/user/streamdeck.service"
TOGGLE="$HOME/bin/streamdeck-toggle"
DESKTOP_FILE="$HOME/.local/share/applications/streamdeck-toggle.desktop"

echo "==> Stopping Stream Deck controller"
systemctl --user disable --now streamdeck.service >/dev/null 2>&1 || true
pkill -u "$USER" -f "python.*-m streamdeck_tool.main" >/dev/null 2>&1 || true

echo "==> Removing launcher, toggle, service, and installed app"
rm -f "$DESKTOP_FILE"
rm -f "$TOGGLE"
rm -f "$SERVICE"
rm -rf "$APP_DIR"
systemctl --user daemon-reload >/dev/null 2>&1 || true

echo "==> Removing Stream Deck udev rule"
if [ -f /etc/udev/rules.d/99-streamdeck.rules ]; then
  sudo rm -f /etc/udev/rules.d/99-streamdeck.rules
  sudo udevadm control --reload-rules
  sudo udevadm trigger
fi

cat <<EOF2

Uninstall complete.

Your personal configuration was NOT deleted:
  $CONFIG_DIR/config.yaml

If you also want to delete it, run:
  rm -rf "$CONFIG_DIR"

System packages installed by the setup script were left installed because other programs may use them.
EOF2
