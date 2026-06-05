# Changelog

All notable public changes to `lol-im-afk` are documented here.

This project loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and uses semantic version tags where practical.

## [Unreleased]

- No unreleased changes yet.

## [0.2.0] - 2026-06-04

### Added

- Windows GitHub Actions CI for Python 3.11 and 3.12.
- Tag-based release workflow that builds and publishes `lol-im-afk.exe`.
- `scripts/build-windows.ps1` for local PyInstaller builds.
- Typed internal app events for queue, match-found, accept, champion-select, and failure states.
- Detection for manual ready-check accepts before the app delay finishes.
- Single-instance protection to prevent multiple tray apps from running at the same time.
- Start with Windows setting using the current user's Windows startup registry key.
- Settings-window controls for live status, connection testing, notification testing, startup toggle, lockfile path, timing, sounds, icon theme, and logs.
- Rotating log files and invalid-settings recovery.
- Tests for ready-check race behavior, settings recovery, startup helpers, and event routing.

### Changed

- Bumped app version from `0.1.0` to `0.2.0`.
- Ready-check completion now waits for the League gameflow outcome instead of immediately treating a vanished ready check as failure.
- Manual accepts are reported as successful accepts and do not trigger a duplicate accept request.
- LCU client access is guarded by a lock so settings-window connection tests and the worker can share it safely.
- Generated sound files are cleaned up when changing volume.
- README now documents EXE downloads, automated releases, startup behavior, manual-accept handling, and the expanded test flow.

### Fixed

- False failure notification when the user manually accepted before the randomized auto-accept delay finished.
- Settings-window status/test connection layout overlap.
- Possible stale state after League disconnects or restarts.
- Possible corrupted settings writes by saving settings atomically.

## [0.1.0] - 2026-05-31

### Added

- Initial Windows tray app for local League Client API ready-check auto-accept.
- Randomized accept delay with configurable timing defaults.
- League lockfile discovery and authenticated local LCU requests.
- Tray enabled/disabled toggle and quit action.
- Local logging and CLI diagnostics mode.
- README with scope, install, build, limitations, and Riot policy caveats.

## Post-0.1.0 Improvements Before 0.2.0

These shipped on `main` before the first versioned EXE release.

### Added

- Custom bottom-right popup notifications.
- Stage-aware generated WAV sound cues.
- Settings UI for sounds, timing, lockfile path, tray icon theme, and logs.
- Predefined tray icon themes.
- Left-click tray icon toggle.

### Changed

- Replaced unreadable tray icon text with clearer symbolic icons.
- Improved popup stacking and close-button placement.

[Unreleased]: https://github.com/iksyomaz/lol-im-afk/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/iksyomaz/lol-im-afk/releases/tag/v0.2.0
[0.1.0]: https://github.com/iksyomaz/lol-im-afk/commit/ab4aab4
