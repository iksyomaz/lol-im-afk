# lol-im-afk

A small Windows tray app for League of Legends queues.

`lol-im-afk` watches the local League client for a ready check, waits a small randomized delay, accepts the match, and shows notifications as the queue progresses.

It is intentionally narrow: it automates **only match acceptance**. It does **not** pick champions, ban champions, write chat messages, dodge, start queues, interact with gameplay, or automate anything inside champion select.

## Why

When you are queued with friends, you often want to keep doing something else while waiting for a match. This app helps you notice that a match was found and accepts the ready check for you, so you do not have to sprint back to the PC just to click `Accept`.

You still need to come back for champion select and the game itself.

## Features

- Windows tray app with no terminal window.
- High-contrast tray icon that changes between enabled and disabled states.
- Predefined tray icon themes, including status, AFK runner/seat, and smoke/gamepad.
- Left-click tray icon to toggle enabled/disabled.
- Right-click tray icon for modern Sun Valley-themed settings and quit.
- Custom bottom-right notifications for:
  - queue started
  - match found
  - match accepted automatically or manually
  - champion select started
  - ready check failed and returned to queue or lobby
- Stage-aware notification sounds with preview.
- Default notification sound volume is 70% relative WAV volume, adjustable in Settings.
- Configurable randomized accept delay.
- Configurable League lockfile path.
- Dark/light settings UI theme.
- Start with Windows option.
- Live service status, connection test, notification test, and built-in log viewer.
- Single-instance protection, rotating logs, and recovery from invalid settings.
- Foreground CLI mode for diagnostics.

## Install

Requirements:

- Windows
- League of Legends installed

### Download the EXE

Download `lol-im-afk.exe` from the latest [GitHub Release](https://github.com/iksyomaz/lol-im-afk/releases), run it, and use the tray icon. No terminal or Python installation is required.

Windows may show a SmartScreen warning because this personal project is not code-signed.

Release notes are tracked in [CHANGELOG.md](CHANGELOG.md).

### Run from source

Running from source requires Python 3.11+. Clone the repo, create a virtual environment, and install once:

```powershell
git clone https://github.com/iksyomaz/lol-im-afk.git
cd lol-im-afk
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

Then double-click:

```text
start-tray-hidden.vbs
```

This starts the tray app with `pythonw.exe`, so no terminal window has to stay open.

## Usage

- Left-click the tray icon to toggle auto-accept.
- Right-click the tray icon and choose `Settings` to adjust delay, tray icon theme, sound volume, lockfile path, and logs.
- Enable `Start with Windows` in Settings if desired.
- Keep League open and queue normally.
- When a match is found, the app waits the configured random delay and accepts once.
- If you accept manually before the delay ends, the app detects that and does not send another accept request.
- When champion select starts, the app shows another notification.

If someone else does not accept, the app reports whether League returned the lobby to queue or left matchmaking. It does not retry-spam the League client.

## Sound Cues

The app plays different generated WAV cues for different queue stages:

1. `Queue started`: positive low cue.
2. `Match found`: higher positive cue.
3. `Accepted by me`: higher confirmation cue.
4. `Champion select`: highest positive cue.

Failure states use lower sounds:

- auto-accept is disabled before the delay completes: low failure cue
- ready check fails and queue continues: positive `back in queue` cue
- ready check fails and lobby returns: lower failure cue

Sound can be turned off or adjusted in Settings. The default volume is `70%`; this controls the generated WAV amplitude and still respects your Windows system volume.

## CLI Mode

For debugging, run:

```powershell
lol-im-afk --cli
```

CLI mode prints timing events such as match found, accepted, and champion select started.

## Build an EXE

From PowerShell:

```powershell
.\scripts\build-windows.ps1
```

The executable is written to `dist\lol-im-afk.exe`. Pushing a `v*` Git tag also runs the GitHub Actions release workflow and attaches the executable to a GitHub Release.

## What It Uses

This app uses:

- The local League Client API served by the running League client on `127.0.0.1`.
- The temporary League `lockfile` to discover the local client port and session token.
- Local files under `%USERPROFILE%\.lol-im-afk` for settings, logs, and generated notification sounds.
- Windows desktop APIs through Python libraries for the tray icon, small settings window, popups, and sound playback.
- The MIT-licensed [Sun Valley ttk theme](https://github.com/rdbende/Sun-Valley-ttk-theme) through `sv-ttk` for the settings window.

This app does not use:

- Riot account credentials.
- A Riot Developer API key.
- Riot's public web API.
- Any cloud service, backend, telemetry, analytics, or remote server.
- Memory reading, process injection, packet interception, input macros, screen scraping, or Vanguard bypasses.

Network requests are local-only requests to the League client running on your own machine.

## Riot and ToS Position

This project is not affiliated with, endorsed by, sponsored by, or approved by Riot Games.

Riot's own documentation describes the League Client API as local desktop communication and also says it is unsupported for third-party applications. Riot's Terms of Service broadly restrict unauthorized third-party programs, bots, scripts, and automation. You should read Riot's current rules yourself:

- [Riot Developer Portal: League Client API](https://developer.riotgames.com/docs/lol#league-client-api)
- [Riot Games API Terms](https://support-developer.riotgames.com/hc/en-us/articles/22698917218323-API-Terms-and-Conditions)
- [Riot Games Terms of Service](https://www.riotgames.com/en/terms-of-service-update-2024)

In the author's opinion, `lol-im-afk` is designed to stay on the safe side because it:

- uses only the local client API exposed by the running League client
- performs one narrow out-of-game action: accepting a ready check
- does not provide gameplay advantage inside a match
- does not interact with champion select after it starts
- does not pick, ban, trade, dodge, write messages, or queue for you
- does not read game memory, hook processes, emulate packets, or bypass anti-cheat
- does not reveal hidden information or collect other players' data

That is an implementation stance, not legal advice and not a guarantee. Riot can change its policies, enforcement, or local APIs at any time. Do not extend this app into champion select or gameplay automation.

## Do Not Use This For

- picking or banning champions
- writing or reading champion select chat
- dodging games
- starting queues automatically
- accepting matches while you are not actually available to return
- gameplay automation
- avoiding AFK/leaver penalties

## Test

```powershell
python -m unittest discover -s tests
python -m compileall -q src tests
```

CI runs both checks on Windows with Python 3.11 and 3.12.

## License

MIT. See [LICENSE](LICENSE).
