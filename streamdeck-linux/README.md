# Stream Deck Linux Controller

A lightweight controller for physical Elgato Stream Deck devices on Linux.
No official Elgato software is needed — this talks to the hardware directly
over USB/HID.

Controls:
- **OBS Studio** — switch scenes, toggle sources, mute inputs, start/stop
  stream & recording (via OBS's built-in websocket server, OBS 28+)
- **Per-app audio** — mute/unmute and volume up/down for individual apps
  (PulseAudio or PipeWire via its pulse-compat layer)
- **Media keys** — play/pause, next, previous (via `playerctl`, works with
  Spotify, browsers, VLC, etc.)
- **Launch apps / run any shell command**
- **Multiple pages** of buttons, navigable with a "page" button

## Requirements

- A physical Elgato Stream Deck (Mini/Original/MK.2/XL/Plus/Neo — anything
  `python-elgato-streamdeck` supports)
- Linux with Python 3.9+
- OBS Studio 28+ (websocket server built in) with a password set under
  **Tools > WebSocket Server Settings**
- System packages: `playerctl`, `libusb-1.0`, `hidapi` (dev headers to build
  the Python `hidapi` wheel) — see `install.sh` for distro-specific names
- PulseAudio or PipeWire (with `pipewire-pulse`, the default on most distros)
  for per-app volume control

## Install

```bash
./install.sh
```

This installs a udev rule (so you don't need root/sudo to use the device),
creates a virtualenv under `~/.local/share/streamdeck-tool`, copies a
starter config to `~/.config/streamdeck-tool/config.yaml`, and installs a
systemd **user** service (not enabled by default).

**Log out and back in** after the first install so the udev/group change
takes effect.

## Configure

Edit `~/.config/streamdeck-tool/config.yaml`:

- `obs.password` — from OBS's WebSocket Server Settings
- `audio_apps` — friendly name -> substring to match against each app's
  PulseAudio stream name. Find the right string with:
  ```bash
  pactl list sink-inputs | grep application.name
  ```
- `pages` — your button layout. Buttons are numbered left-to-right,
  top-to-bottom, starting at `0`. See `config.example.yaml` for every
  supported button `type`.

The config **hot-reloads** — save the file and the deck redraws itself, no
restart needed.

### Supported button types

| type                    | fields                          | effect                              |
|-------------------------|----------------------------------|--------------------------------------|
| `obs_scene`              | `scene`                         | switch OBS to that scene             |
| `obs_toggle_source`      | `scene`, `source`                | show/hide a source in a scene        |
| `obs_toggle_mute_input`  | `input`                          | mute/unmute an OBS audio input       |
| `obs_start_stop_stream`  | —                                | toggle streaming                     |
| `obs_start_stop_record`  | —                                | toggle recording                     |
| `volume_mute`            | `app`                           | mute/unmute an app's audio           |
| `volume_adjust`          | `app`, `delta` (±%)              | nudge an app's volume                |
| `volume_set`             | `app`, `percent`                 | set an app's volume exactly          |
| `media_play_pause`       | —                                | toggle playback (playerctl)          |
| `media_next` / `media_prev` | —                             | skip track                           |
| `launch_app` / `run_command` | `command`                    | run any shell command                |
| `page`                   | `target` (page name)             | switch the deck to another page      |

Every button can also have a `label` (use `\n` for a second line) and an
optional `icon` (path to a PNG).

## Run

Test it directly first:

```bash
~/.local/share/streamdeck-tool/venv/bin/python -m streamdeck_tool.main -v
```

Once it's working, run it automatically at login:

```bash
systemctl --user enable --now streamdeck.service
journalctl --user -u streamdeck -f   # view logs
```

## Troubleshooting

- **"No Stream Deck found"** — unplug/replug the device, confirm the udev
  rule is installed (`ls /etc/udev/rules.d/99-streamdeck.rules`), and that
  you've logged out/in since installing it. Check `groups` includes
  `plugdev`.
- **OBS actions do nothing** — confirm the websocket server is enabled and
  the password in `config.yaml` matches exactly; check the terminal/log
  output for `OBS not reachable`.
- **Volume buttons don't find the app** — the app needs to actually be
  producing audio (an open stream) for PulseAudio to list it; re-check the
  match string with `pactl list sink-inputs | grep application.name`.
- **Media keys do nothing** — confirm `playerctl status` shows your player
  while it's running.

## Project layout

```
streamdeck_tool/
  main.py         entry point
  config.py       YAML loading + hot reload
  deck.py         hardware device + page/button rendering loop
  renderer.py     draws button labels/icons to key images
  actions.py      routes button presses to obs/audio/media/shell handlers
  obs_client.py   reconnecting OBS websocket wrapper
  audio.py        PulseAudio/PipeWire per-app volume/mute
install/
  udev/           USB permission rule
  systemd/        user service unit
```
