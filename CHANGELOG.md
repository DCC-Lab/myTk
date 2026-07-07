# Changelog

All notable changes to myTk are documented here.

## [1.7.1]
### Changed
- **`start_remote()` now auto-registers `@remote_command` methods**, so you no
  longer need to call `register_remote_commands()` yourself — tagged methods
  just work. The explicit call remains available and idempotent. `@remote_command`
  is now the primary way to expose methods; `app.remote(...)` is documented as
  the low-level primitive it builds on (still available for free functions or
  dynamic registration).

## [1.7.0]
### Added
- **Remote command-line client** for talking to a running
  `RemoteControllable` app. Call a function and print its result with
  `python -m mytk --remote "turn_on()"` or the standalone `mytk-remote`
  console script (`mytk-remote "add(2, 3)" --port 9000`). `--list` prints the
  exposed functions and their signatures; `--host`/`--port`/`--app-name`
  select and verify the target. Arguments are parsed as Python literals with
  `ast` (no code execution); a bare name means a no-argument call.

## [1.6.1]
### Added
- **`remote_command`** decorator and
  **`RemoteControllable.register_remote_commands()`** for exposing methods
  declared in a class body. `@app.remote` cannot decorate methods at
  class-definition time (there is no live app yet), so tag them with
  `@remote_command` (bare or `@remote_command(name="...")`) and call
  `app.register_remote_commands()` once to register them all. Purely additive:
  existing `self.remote(...)` / `@app.remote` usage is unchanged.

## [1.4.0] - 2026-06-18
### Added
- **`SVGImage`** — a widget that displays an SVG document, rasterized with the
  [`resvg`](https://pypi.org/project/resvg-py/) engine (full SVG fidelity,
  including text, gradients and clipping) and shown through the existing
  `Image`/`ttk.Label` pipeline. Because the source is vector, it re-renders on
  resize for crisp output. Construct it from a path or string:
  `SVGImage(filepath="drawing.svg")` / `SVGImage(data="<svg ...>")`. Accepts
  dropped `.svg` files via `accept_dropped_svg_files()`.
  - New optional extra `pip install mytk[svg]` (`resvg-py`); also installed on
    demand at first use, like the other extras.
- New example app `mytk.example_apps.svgviewer_app`.

### Fixed
- Drag-and-drop now accepts `file://` URIs (percent-encoded, possibly with a
  trailing newline) delivered by GNOME/GTK file managers, which were previously
  dropped silently. The fix is in the shared `dnd.dropped_paths` parser, so it
  applies to every drop target (`SVGImage`, `View3D`, `TableView`, plots).

## [1.3.0] - 2026-06-13
### Changed
- **Heavy/platform-sensitive features are now optional extras; the default
  install stays cross-platform.** `pip install mytk` still brings the common,
  universally pip-installable modules (matplotlib, numpy, pandas, openpyxl,
  pyperclip, requests, Pillow), but the features that need native libraries,
  hardware or a GL context are opt-in:
  - `pip install mytk[video]`  — OpenCV, for `VideoView`
  - `pip install mytk[view3d]` — trimesh + moderngl, for `View3D`
  - `pip install mytk[dnd]`    — tkdnd, for drag-and-drop
  - `pip install mytk[all]`    — all of the above
  All of these also install on demand at first use (via `ModulesManager`), so
  nothing breaks if you skip the extra.
- Dropped `scipy` and `packaging` as declared dependencies — neither is used by
  the library (`packaging` still arrives transitively via matplotlib).

### Fixed
- `VideoView` no longer imported OpenCV at module load, so `import mytk` no longer
  pulls in `opencv-python` (or numpy through it). All third-party modules are now
  imported lazily — `import mytk` touches only the Python standard library.

## [1.2.2] - 2026-06-13
### Fixed
- `View3D` crashed on every render when shown before any geometry was loaded
  (e.g. `view3d_app` opened without a file): the now-default pyrender backend
  always builds a camera pose from the bounding-box centre, which is unset until
  a mesh loads. The camera now falls back to the origin, so an empty viewer
  renders its background and accepts a dropped/loaded file normally.

### Added
- The capabilities demo's `View3D` now accepts dropped mesh files too (when
  `tkinterdnd2` is already installed).

## [1.2.1] - 2026-06-13
### Fixed
- `View3D` hung the app when placed content-sized (no `sticky`/weight, as in the
  capabilities demo): it blitted frames into a `ttk.Label`, which sized itself to
  each rendered image and re-triggered `<Configure>`, growing the widget on every
  frame in a runaway resize loop. It now renders into a `tk.Canvas`, whose size
  is set by the layout and unaffected by what is drawn, so there is no feedback.

## [1.2.0] - 2026-06-13
### Added
- **Drag-and-drop**: any widget can accept files dropped from the OS file
  manager via `Base.accept_dropped_files(callback)` (new `DragAndDropCapable`
  mixin, modelled on `EventCapable`). Built on the optional `tkinterdnd2`/tkdnd
  extension, installed on demand and matched to the running Tcl version; the
  callback runs on the next event-loop tick (safe for dialogs/slow work), and
  drag-and-drop degrades gracefully when the extension can't be loaded.
- **`View3D`**: an embedded off-screen 3D mesh viewer. Loads GLB/GLTF/OBJ/PLY/STL
  via trimesh and renders it inside a normal myTk layout — drag to orbit, scroll
  to zoom, drop a mesh onto it to load. `View3D(...)` is a factory that picks a
  backend (`View3DPyrender` preferred, `View3DModernGL` fallback); per-vertex
  glTF `COLOR_0` alpha is honoured so translucent meshes render correctly. Heavy
  dependencies are optional and installed on demand.
- New examples: `view3d_app.py` and `dnd_app.py`; the capabilities demo
  (`example.py`) now includes a `View3D`, and `pydatagraph_app.py` loads
  Excel/CSV files by drag-and-drop.

## [1.1.0] - 2026-05-23
### Added
- `grid_into(fill=...)` resize shortcut: sets the child's `sticky` and the parent row/column `weight` together so a widget actually grows with the window. Accepts `True`/`"both"`, `"x"`/`"width"`, `"y"`/`"height"`. Existing explicit (nonzero) weights are preserved; cannot be combined with an explicit `sticky`.

### Changed
- `View` and `Box` now disable grid propagation (`grid_propagate(False)`) when **both** `width` and `height` are given, so the requested pixel size is honored instead of being silently overridden by the size of their children. A single dimension (e.g. `Box(width=100)`) or no dimension still sizes to content as before. `View`'s `width`/`height` are now optional — `View()` produces a content-sized frame.

### Fixed
- `grid_into(describe=True)` diagnostics: width/height were swapped (n/s reported as width, e/w as height) and the "expands to fill extra space" booleans were inverted (printed `True` when weight was 0). Output now reports `(width, height)` correctly.

## [0.10.11] - 2026-02-26
### Fixed
- `TabularData._normalize_record()` no longer mutates `required_fields` on every insert
- `TabularData.record()` and `update_record()` now correctly look up records by UUID objects (not just strings)
- `SimpleDialog` key shortcuts (`<Return>`, `<Escape>`) now assigned after buttons are created, not before
- Several bugs fixed in `entries.py`: `Entry` binding order, `FormattedEntry` display initialisation, `FormattedEntry` crash on non-numeric input, `FormattedEntry.value` setter coercion, `CellEntry` focusout reference, `LabelledEntry` value passthrough
- `NumericEntry` consolidated into `IntEntry`; `NumericEntry` kept as alias for backwards compatibility

### Added
- `formatted_entry_app.py` example demonstrating `FormattedEntry` with various format strings

## [0.10.10] - 2026-02-25
### Changed
- `CanvasView.is_disabled` and `Dialog.is_disabled` now propagate disabled/enabled state to all descendant widgets

## [0.10.9] - 2026-02-25
### Changed
- `View.is_disabled` now recursively propagates the disabled/enabled state to all descendant widgets (same behaviour as `Box`)
- Refactored `_propagate_disabled()` helper from `Box` into `Base` to avoid duplication

## [0.10.8] - 2026-02-25
### Changed
- `Box.is_disabled` now recursively propagates the disabled/enabled state to all descendant widgets; disabling a `Box` grays out all contained controls automatically

## [0.10.7] - 2026-02-25
### Added
- `position` parameter on `App`, `Window`, and `Dialog` for named screen placement: `"center"`, `"top-left"`, `"top-right"`, `"bottom-left"`, `"bottom-right"`
- `EventCapable._bind_destroy_cancel()`: automatically cancels all tracked `after()` tasks when a widget is destroyed; called by `grid_into`/`pack_into`/`place_into` as a safety net; convention is to also call it at the end of `create_widget()` overrides
- `_BaseWidget._bind_destroy_cancel()`: no-op fallback so subclasses can safely call it regardless of MRO
- `App.__init__` binds `<Destroy>` on root to cancel all pending Tcl `after`/`after_idle` events via `after info`

### Fixed
- `apply_window_position` deferred callback no longer causes `invalid command name` errors when the widget is destroyed before the `after_idle` fires

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
