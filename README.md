# Stream Deck Linux + OBS Easy Installer

This project provides a lightweight, text-focused Stream Deck controller for OBS on Linux, plus a simple Linux Mint/Ubuntu installer and one-click application-menu launcher.

The core application in `streamdeck-linux/` was created for this project. Its `install.sh` is used for the actual Stream Deck application installation.

## What this package installs

- Stream Deck USB/udev permissions
- Python virtual environment and required Python packages
- OBS WebSocket control support
- Per-app audio/media control support
- A starter OBS-oriented `config.yaml`
- A `Stream Deck Toggle` application-menu launcher
- A start/stop toggle script at `~/bin/streamdeck-toggle`

## Requirements

- Linux Mint or Ubuntu, or another Debian/Ubuntu-based distribution using `apt`
- An Elgato Stream Deck supported by `python-elgato-streamdeck`
- OBS Studio 28 or newer
- An available USB connection to the Stream Deck
- Internet access during installation for system/Python packages

## Install

Extract this ZIP somewhere under your home folder, open a terminal in the extracted folder, then run:

```bash
chmod +x install.sh uninstall.sh
./install.sh
```

The installer will ask for your sudo password when it installs Linux packages and the Stream Deck udev rule.

### Important: log out and back in

After the first installation, **log out of your Linux Mint/Ubuntu desktop session and log back in once**. This activates the USB permission/group change used by the Stream Deck.

## Set up OBS WebSocket

In OBS Studio:

1. Open **Tools > WebSocket Server Settings**.
2. Enable the WebSocket server.
3. Leave the port at `4455` unless you specifically need another port.
4. Set or note the WebSocket password.

## Configure the Stream Deck

After installation and after logging out and back in:

1. Open your **Home** folder.
2. Navigate to:

```text
.config/streamdeck-tool/
```

If you do not see `.config`, press:

```text
Ctrl + H
```

to show hidden files and folders.

3. Inside the `streamdeck-tool` folder, right-click an empty area and choose:

**Open in Terminal**

4. Open the configuration file with:

```bash
nano config.yaml
```

5. Edit your OBS connection settings and Stream Deck button configuration.

6. Save the file in Nano:

```text
Ctrl + O
```

Press **Enter** to confirm the filename.

7. Exit Nano:

```text
Ctrl + X
```

You can also open the configuration file from any terminal with:

```bash
nano ~/.config/streamdeck-tool/config.yaml
```

At minimum change:

```yaml
obs:
  host: "localhost"
  port: 4455
  password: "YOUR_OBS_WEBSOCKET_PASSWORD"
```

The names in each OBS button must match your OBS names **exactly**, including capitalization and spaces.

Example:

```yaml
2:
  type: obs_scene
  scene: "P5 Detail"
  label: "P5\nDetail"
```

The `\n` creates a line break on the physical Stream Deck button label.

The included starter config contains example buttons for:

- Starting
- Ending
- Camera 1
- Camera 2
- Camera 1 + Camera 2 Small
- Camera 2 + Camera 1 Small
- BRB
- Mic mute
- Record
- Stream start/stop
- Media and app-audio controls

Edit or remove any entries that do not match your OBS setup.

## Start and stop without a terminal

Open the Linux Mint/Ubuntu application menu and search for:

**Stream Deck Toggle**

Click once to start the controller. Click again to stop it.

On Linux Mint Cinnamon you can right-click the menu entry and add it to the panel, desktop, or favorites.

## Config hot reload

`config.yaml` is watched while the controller runs. In most cases you can save changes to the file and the Stream Deck will redraw automatically without restarting the program.

## Manual testing

To run it directly and see diagnostic output:

```bash
~/.local/share/streamdeck-tool/venv/bin/python \
  -m streamdeck_tool.main \
  --config ~/.config/streamdeck-tool/config.yaml -v
```

Press `Ctrl+C` to stop a manually launched copy.

## Logs

When launched by **Stream Deck Toggle** without the systemd service, the log is:

```bash
~/.local/share/streamdeck-tool/streamdeck.log
```

View it with:

```bash
cat ~/.local/share/streamdeck-tool/streamdeck.log
```

The original installer also installs a systemd user service. It is not enabled automatically. If you later enable it with:

```bash
systemctl --user enable --now streamdeck.service
```

then the Stream Deck controller will start automatically at login. The toggle launcher can still stop/start that user service.

Service logs:

```bash
journalctl --user -u streamdeck.service -f
```

## Common problems

### No Stream Deck found

Log out and back in after installation, unplug/replug the Stream Deck, and verify:

```bash
groups
```

You should normally see `plugdev` in the list.

### OBS buttons do nothing

Confirm OBS is running, WebSocket is enabled, the password matches `config.yaml`, and scene/input names match OBS exactly.

### Launcher starts but nothing appears to happen

Check:

```bash
cat ~/.local/share/streamdeck-tool/streamdeck.log
```

### Audio buttons do not find an application

The application usually needs to be producing audio. To see application names:

```bash
pactl list sink-inputs | grep application.name
```

## Uninstall

From this package folder run:

```bash
./uninstall.sh
```

The uninstaller removes:

- the installed Stream Deck application
- the toggle script
- the menu launcher
- the systemd user service
- the Stream Deck udev rule

It deliberately keeps your personal configuration at:

```bash
~/.config/streamdeck-tool/config.yaml
```

It also leaves system packages installed because other software may depend on them.

## Package layout

```text
streamdeck-linux-obs/
├── install.sh                  easy wrapper installer
├── uninstall.sh                removes the installed application
├── README.md                   these instructions
├── config.example.yaml         starter OBS configuration
└── streamdeck-linux/           core Stream Deck application
    ├── install.sh              application installer
    ├── config.example.yaml
    ├── requirements.txt
    ├── install/
    └── streamdeck_tool/
```


## Project goal

This project exists because I wanted a Stream Deck on Linux that simply works as an OBS controller without requiring icon packs, elaborate themes, plugin ecosystems, or a complicated graphical configuration application. The focus is intentionally on simple text labels, YAML configuration, and low-overhead operation.

## AI assistance

This is an AI-assisted original project. The initial application code was created with Anthropic Claude based on the project requirements. OpenAI ChatGPT was later used to help test, refine, package, document, and simplify installation.

The project was assembled and tested for the specific goal of providing a simple, lightweight Stream Deck controller for OBS on Linux.
