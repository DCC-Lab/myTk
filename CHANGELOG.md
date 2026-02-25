# Changelog

All notable changes to myTk are documented here.

## [0.10.6] - 2026-02-24
### Fixed
- `XYPlot.create_widget` was assigning to `self.first_axis` which is a read-only computed property, causing `AttributeError` via `Bindable.__setattr__`; fix calls `self.figure.add_subplot()` directly (same pattern as `Histogram`)

## [0.10.5] - 2026-02-24
### Fixed
- `Histogram.create_widget` never added a subplot, leaving `first_axis` as `None` and causing a crash in `clear_plot()` / `update_plot()` when the histogram was updated (e.g. in `MicroscopeApp`)

## [0.10.4] - 2026-02-24
### Fixed
- `App(no_window=True)` now actually withdraws the main window — the parameter was previously accepted but silently ignored
- Removed stale `no_window=True` from `envtest.py`; tests need a visible window and the parameter had no effect before this fix

## [0.10.3] - 2026-02-18
### Added
- `progressbar_app.py` example demonstrating three ways to update a `ProgressBar`: direct value assignment, `step()`, and background thread via `schedule_on_main_thread()`

## [0.10.2] - 2026-02-18
### Added
- `bring_to_front=True` option on `App` — uses `osascript` on macOS to reliably activate the process window, overcoming editor focus reclaim

## [0.10.1] - 2026-02-17
### Fixed
- `ProgressBar` and `ProgressWindow` fully implemented and tested
- `ProgressBar.step()` now updates `value_variable` directly (bypasses unreliable `ttk.Progressbar.step()` sync)
- `ProgressWindow` exposes `self.progress_bar` after `run()`
- Notification handlers guard against stale observers with `try/except` around `winfo_exists()`

## [0.9.15] - 2026-02-14
### Added
- `Configurable` mixin and `ConfigModel` class for declarative property management with automatic validation and dialog generation (`ConfigurableNumericProperty`, `ConfigurableStringProperty`, `ConfigurationDialog`)

### Fixed
- Mutation-during-iteration bug in `after_cancel_all()`
- `Entry.__init__` was resetting initial value to empty string
- Wildcard re-export and missing `partial` import
- Hanging test in `testCustomDialogs`
- Dead code, hardcoded path, and optional `cv2` import
- Modernized project structure to current Python packaging standards

## [0.9.12] - 2025-xx-xx
### Added
- `schedule_on_main_thread()` on `App` for safely dispatching work from background threads
- `is_main_thread()` utility function
