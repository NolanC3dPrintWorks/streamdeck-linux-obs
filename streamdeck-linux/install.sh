#!/usr/bin/env bash
# Installs the Stream Deck Linux controller for the current user.
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$HOME/.local/share/streamdeck-tool"
CONFIG_DIR="$HOME/.config/streamdeck-tool"

echo "==> Checking system dependencies"
MISSING=()
command -v python3 >/dev/null || MISSING+=("python3")
command -v playerctl >/dev/null || MISSING+=("playerctl")
pkg-config --exists libusb-1.0 2>/dev/null || MISSING+=("libusb-1.0-0-dev (or libusb1-devel)")
pkg-config --exists hidapi-libusb 2>/dev/null || pkg-config --exists hidapi 2>/dev/null || MISSING+=("libhidapi-libusb0/libhidapi-dev (or hidapi-devel)")

if [ ${#MISSING[@]} -gt 0 ]; then
  echo "Missing (install via your package manager, names vary by distro):"
  printf '  - %s\n' "${MISSING[@]}"
  echo "Debian/Ubuntu example:"
  echo "  sudo apt install python3-venv python3-pip playerctl libusb-1.0-0-dev libhidapi-libusb0 libhidapi-dev"
  echo "Fedora example:"
  echo "  sudo dnf install python3-pip playerctl libusb1-devel hidapi-devel"
  echo "Arch example:"
  echo "  sudo pacman -S python-pip playerctl hidapi libusb"
  read -rp "Continue anyway? [y/N] " ans
  [[ "$ans" =~ ^[Yy]$ ]] || exit 1
fi

echo "==> Installing udev rule (needs sudo)"
sudo cp "$SRC_DIR/install/udev/99-streamdeck.rules" /etc/udev/rules.d/99-streamdeck.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
sudo usermod -aG plugdev "$USER" || true
echo "    NOTE: log out/in (or reboot) for the plugdev group change to apply."

echo "==> Copying app to $APP_DIR"
mkdir -p "$APP_DIR"
cp -r "$SRC_DIR/streamdeck_tool" "$APP_DIR/"
cp "$SRC_DIR/requirements.txt" "$APP_DIR/"

echo "==> Creating Python virtualenv"
python3 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install --upgrade pip
"$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"

echo "==> Setting up config"
mkdir -p "$CONFIG_DIR"
if [ ! -f "$CONFIG_DIR/config.yaml" ]; then
  cp "$SRC_DIR/config.example.yaml" "$CONFIG_DIR/config.yaml"
  echo "    Wrote default config to $CONFIG_DIR/config.yaml — EDIT THIS before running."
else
  echo "    Existing config at $CONFIG_DIR/config.yaml left untouched."
fi

echo "==> Installing systemd user service"
mkdir -p "$HOME/.config/systemd/user"
cp "$SRC_DIR/install/systemd/streamdeck.service" "$HOME/.config/systemd/user/"
systemctl --user daemon-reload

cat <<EOF

Done.

Next steps:
  1. Edit $CONFIG_DIR/config.yaml
     - set your OBS websocket password (OBS > Tools > WebSocket Server Settings)
     - set your audio_apps and button layout
  2. Log out/in (for the plugdev group to take effect), then test it directly:
       $APP_DIR/venv/bin/python -m streamdeck_tool.main --config $CONFIG_DIR/config.yaml -v
  3. Once it works, enable it to start automatically:
       systemctl --user enable --now streamdeck.service
     Logs: journalctl --user -u streamdeck -f
EOF
