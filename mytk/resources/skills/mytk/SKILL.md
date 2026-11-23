---
name: mytk
description: Build cross-platform desktop GUIs in Python with the mytk library (a Tkinter wrapper for scientists). Covers the whole API so nothing gets re-coded by hand - the App class (window, menus, about/preferences/help/save hooks, main-thread queue, timers, remote control), layout (grid_into, fill, View, Box), every widget (Button, Checkbox, RadioButton, PopupMenu, Slider, Entry, IntEntry, FormattedEntry, Label, indicators, ProgressBar, TableView + TabularData, Figure/XYPlot, Image, CanvasView, VideoView, View3D, FileViewer), Dialog and auto-generated settings dialogs (Configurable), two-way property bindings (Bindable), and NotificationCenter. Use whenever writing, editing, reviewing or debugging code that imports mytk, or when asked for a GUI, control panel, instrument front-end or small desktop app in Python. Read it BEFORE writing any tkinter code - check here first whether mytk already does it.
metadata: {"version": "2.4", "applies-to": "mytk >= 1.10"}
---

# mytk

`mytk` is a Tkinter wrapper for scientists: `pip install mytk`, then `from mytk import *`. It is cross-platform (macOS, Windows, Linux) and needs Python >= 3.11.

## Rule zero: do not re-code what mytk already does

Before writing any raw `tkinter`/`ttk` code, look for it in this table. Hand-rolling these is the most common mistake.

| You are about to write... | Use this instead |
|---|---|
| `tk.Tk()`, a menu bar, a Quit handler, `root.mainloop()` | `App(name=..., geometry=...)` then `app.mainloop()` |
| An About box, a Preferences menu item, a Help menu, a Save item | Override `App.about()`, `App.preferences()`, `App.save()`; pass `help_url=` |
| `messagebox.showinfo/showwarning/showerror` | `Dialog.showinfo/showwarning/showerror(message, title=)` |
| A `Toplevel` with Ok/Cancel buttons | Subclass `Dialog`, override `populate_widget_body()`, call `.run()` |
| A settings dialog with labels, entries, validation, clamping | `Configurable` + `ConfigurableNumericProperty` + `show_config_dialog()` |
| `var.trace_add(...)`, or a callback whose only job is to copy widget -> model | `self.bind_property_to_widget_value("prop", widget)` |
| A `value` property plus `trace_add` in your own widget | The `ValueCapable` mixin: `use_value_variable(...)`, `attach_value_variable_to_widget()` |
| A callback that enables/disables a widget when a flag changes | `self.bind_properties("flag", widget, "is_enabled")` |
| A custom callback registry / signal / event bus | `NotificationCenter` with an `Enum` name |
| A `queue.Queue` polled with `after()` to update the GUI from a thread | `app.schedule_on_main_thread(fct, args, kwargs)` |
| `root.after(...)` plus bookkeeping of ids to cancel on quit | `self.after(ms, fct)` on any `App`/widget (tracked, auto-cancelled) |
| `ttk.Frame` / `ttk.LabelFrame` | `View` / `Box(label=...)` |
| `ttk.Treeview` plus your own list of rows, sorting, cell editing | `TableView` + its `data_source` (`TabularData`) |
| Loading CSV/Excel/JSON into a table | `TabularData.load` (JSON), `load_dataframe_from_tabular_data` + `set_records_from_dataframe` (CSV/Excel) |
| `FigureCanvasTkAgg` + toolbar embedding | `Figure` / `XYPlot` / `Histogram` |
| `ImageTk.PhotoImage` on a label, with resize handling | `Image(filepath=...)`, `is_rescalable` (Part 7) |
| `columnconfigure(weight=1)` + `sticky="nsew"` to make something stretch | `grid_into(parent, ..., fill=True)` (or `"x"`, `"y"`) |
| A colored status dot, a level bar, a formatted numeric readout | `BooleanIndicator`, `Level`, `NumericIndicator` |
| An OpenCV capture loop into a label, with start/stop/save buttons | `VideoView` and its `create_behaviour_buttons()` |
| A socket/HTTP server so a script can drive the app | `RemoteControllable` + `@remote_command` |
| `subprocess open` / `xdg-open` / `os.startfile` | `app.reveal_path(path)` |
| `try: import x except: pip install` | `ModulesManager.install_and_import_modules_if_absent({...})` |
| Centering a window on screen | `auto_position="center"` (the default for `App`) |
| A file-system tree browser | `FileViewer(root_dir)` |
| Files dropped from Finder/Explorer | `widget.accept_dropped_files(callback)` |

`from mytk import *` also re-exports the common tkinter names (`StringVar`, `DoubleVar`, `IntVar`, `BooleanVar`, `END`, `HORIZONTAL`, `NSEW`, `ttk`, `tkFont`, ...), so a separate `import tkinter` is rarely needed. `filedialog` is not re-exported: `from tkinter import filedialog`.

## How mytk works: three things to know

1. **Widgets are created on placement.** A mytk object (`Button`, `Label`, ...) is a Python wrapper; the real Tk widget (`.widget`) is `None` until you call `grid_into` / `pack_into` / `place_into`. Simple requests work before that: values (`value`, `value_variable`), states (`is_disabled`, `is_selected`, `Button.is_default`) and options (`width`, `height`, `minimum`, `maximum`, `label`...) are remembered and applied on creation. Only what needs the real widget must come **after** placement: `bind_event`, `accept_dropped_files`, setting `has_focus`, pixel sizes, `widget.column(...)`; those raise `WidgetNotYetCreatedError` or fail on `None`. Placing the same object twice raises `RuntimeError`. The escape hatch to raw Tk is always `obj.widget`. (With mytk < 1.10, states and bindings had to wait until after placement.)
2. **Every widget and the App are `Bindable`.** Assigning a plain attribute notifies observers, which is what makes bindings work (Part 4).
3. **The parent argument is a mytk object**, not a Tk widget: `button.grid_into(self.window, ...)` or `button.grid_into(some_box, ...)`. To place into a raw Tk widget, pass `widget=`: `label.grid_into(widget=some_tk_frame, row=0, column=0)`.

## Part 1: App

```python
from mytk import *

class MyApp(App):
    def __init__(self):
        super().__init__(name="Acquisition", geometry="800x480",
                         help_url="https://example.org/docs")
        self.acquisition_is_running = False          # plain model state

        self.controls = Box(label="Controls")
        self.controls.grid_into(self.window, row=0, column=0, padx=10, pady=10, fill=True)
        self.start = Button("Start", user_event_callback=self.click_start)
        self.start.grid_into(self.controls, row=0, column=0, padx=5, pady=5)

    def click_start(self, event, button):
        self.acquisition_is_running = True

    def save(self): ...          # File > Save. Raises NotImplementedError if not overridden
    def preferences(self): ...   # app menu > Preferences. Same
    def about(self): ...         # optional: the default shows a "Created with myTk" dialog

if __name__ == "__main__":
    MyApp().mainloop()
```

`App(geometry=None, auto_position="center", name="myTk App", help_url=None, bring_to_front=False, no_window=False)`. An offset in `geometry` ("800x600+10+10") together with `auto_position` raises `ValueError`: pass `auto_position=None` in that case.

| Member | What it gives you |
|---|---|
| `app.window` | The main `Window` (a mytk object): the parent for top-level widgets. `window.title`, `window.resizable` |
| `app.root` / `app.widget` | The raw `tk.Tk` |
| `App.app` | Class attribute: the current app, reachable from anywhere |
| menu bar | Built automatically: About, Preferences, File > Save / Quit, Edit, Help. macOS Cmd-Q is routed to `quit()` |
| `save()`, `preferences()`, `about()`, `help()` | Hooks called by the menus. Override them; do not build a second menu |
| `help_url` | Enables Help > "Documentation web site" (opens the browser) |
| `schedule_on_main_thread(fct, args=None, kwargs=None)` | Thread-safe: queue a call for the Tk thread (drained every `run_loop_delay` = 20 ms). **The only safe way to touch widgets from a worker thread** |
| `after(ms, fct)`, `after_cancel(id)`, `after_cancel_all()` | Timers, tracked and cancelled automatically on quit. Also on every widget |
| `bind_event(event, cb)`, `event_generate(event)` | Tk events on the root. Also on every widget |
| `reveal_path(path)` | Open a file/folder in Finder / Explorer / xdg-open |
| `quit()` | Cancels timers and destroys the window. Override and call `super().quit()` to add cleanup |
| `is_running` | Read-only: True while the root window exists |

Pitfall: `is_running`, `root`, `widget`, `window`, `name` and `help_url` are taken on `App`. In particular `self.is_running = True` raises `AttributeError` (no setter): name your own flag `acquisition_is_running` or similar.

Periodic update (no thread needed):

```python
def ticker(self):
    if self.acquisition_is_running:
        self.plot.append(x, y); self.plot.update_plot()
    self.after(500, self.ticker)          # re-arm; cancelled for you at quit
```

Worker thread:

```python
def worker(self):                          # runs in a threading.Thread
    value = instrument.read()              # slow, off the main thread
    self.schedule_on_main_thread(self.show_value, args=[value])
```

Tests and windowless scripts: `App(no_window=True)`. A timed `app.after(200, app.quit)` before `app.mainloop()` runs a real event loop and returns.

## Part 2: Layout

```python
widget.grid_into(parent, row=0, column=0, padx=5, pady=5, sticky="w")   # any tk grid option
widget.grid_into(parent, row=1, column=0, fill=True)      # stretch both ways AND give the cell weight
widget.grid_into(parent, row=2, column=0, fill="x")       # "x"/"width", "y"/"height", True/"both"
widget.pack_into(parent, side=LEFT)
widget.place_into(parent, x=0, y=0, width=100, height=20)
```

- `fill=` sets the child's `sticky` **and** the parent row/column weight in one go (only when that weight is still 0, so explicit weights win). Combining `fill` and `sticky` raises `ValueError`.
- Explicit weights: `parent.row_resize_weight(i, w)`, `parent.column_resize_weight(i, w)`, `parent.all_resize_weight(w)`. `parent.grid_size` gives `(columns, rows)`.
- `parent.add_rows([w1, w2, w3], start_row=0, column=0, padx=5)` grids a column of widgets with the same options.
- `View(width=, height=)` is a plain frame; `Box(label=, width=, height=)` is a titled frame. Given **both** width and height they keep that pixel size; otherwise they shrink to fit their children.
- Debugging a layout: `Base.debug = True` (borders around containers plus placement diagnostics), or `grid_into(..., describe=True)` for one widget.
- Inspecting a running interface: `app.widget_hierarchy()` returns the Tk widget tree as a nested dict (`class`, `name`, `path`, `children`; pass a Tk widget to start from a subtree), and `Base.view_for(tk_widget)` returns the mytk object that owns a Tk widget, or `None`.

State, on every widget, before or after placement: `is_disabled` / `is_enabled`, `enable()`, `disable()`, `is_selected`, `select()`, `deselect()`, `width`, `height`, `background_color`. `has_focus` reads `False` before placement and can only be set after. Disabling a `View`, `Box` or `Dialog` disables the children it has at that moment (not children placed into it later). `background_color` on a `View`/`Box` has no visible effect on macOS (aqua theme); it works on canvas-based widgets everywhere.

### Reusable composite widgets

Subclass `View` or `Box` and create the children in `create_widget`:

```python
class StageView(Box):
    def __init__(self):
        super().__init__(label="Stage")
        self.position = 0.0

    def create_widget(self, master):
        super().create_widget(master)                 # creates the frame first
        self.readout = NumericIndicator(format_string="{0:.2f} mm")
        self.readout.grid_into(self, row=0, column=0, padx=5, pady=5)
        self.bind_property_to_widget_value("position", self.readout)
```

Your own leaf widget subclasses `Base` and overrides `create_widget(self, master)` to set `self.widget`. Declare its options and states with the descriptors from `mytk.base` rather than hand-written properties: `maximum = WidgetOption("to")` (kept in `self._widget_args` until creation, so pass `**self._widget_args` to the Tk constructor) and `is_armed = WidgetState("pressed")`.

If it holds a value, add the `ValueCapable` mixin instead of writing a `value` property and a `trace_add` yourself. It is the interface with the Tk variable: you create the variable, hand it over once, and attach it in `create_widget`.

```python
class Thermometer(Base, ValueCapable):
    value_variable_option = "textvariable"       # Tk option the variable plugs into ("variable" by default)

    def __init__(self):
        super().__init__()
        self.use_value_variable(DoubleVar(value=20))     # gives .value, observable and bindable

    def create_widget(self, master):
        self.widget = ttk.Label(master)
        self.attach_value_variable_to_widget()           # do not forget: the screen would not follow

    def sanitize_value(self, value):             # optional: applied when .value is assigned
        return max(value, -273.15)

    def value_did_change(self, value):           # optional: called on every change, from code or user
        ...
```

`bind_variable(variable)` / `bind_textvariable(variable)` are for making a placed widget use a variable created elsewhere (a shared one), not for attaching its own.

## Part 3: Widget catalog

Callback signatures differ per widget: copy them from this table.

| Widget | Constructor | Value / callback |
|---|---|---|
| `Button` | `Button(label="Button", default=False, width=None, user_event_callback=None)` | callback `(event, button)`; `event` is `None`. `.label` get/set. **An exception raised in the callback is caught and printed, not raised** |
| `Checkbox` | `Checkbox(label="", user_callback=None)` | `.value` bool; callback `(checkbox)`. Checked by default unless bound |
| `RadioButton` | `RadioButton.linked_group({"A": 1, "B": 2}, user_callback=None)` returns a list sharing one `IntVar` | callback `(radio)`; current choice is `radios[0].value_variable.get()` |
| `PopupMenu` | `PopupMenu(menu_items=[...], user_callback=None)` | `.value` text; `.selected_index`; callback `(popup, index)`; `select_index(i)`, `clear_menu_items()`, `add_menu_items([...])` |
| `Slider` | `Slider(value=0, minimum=0, maximum=100, increment=1, width=200, height=20, orient=HORIZONTAL, delegate=None)` | `.value` (clamped); delegate gets `value_updated(object=, value=)` on every change, from code or from the user |
| `Entry` | `Entry(value="", character_width=None)` | `.value` str. Return moves focus away |
| `IntEntry` (= `NumericEntry`) | `IntEntry(value=0, width=None, minimum=0, maximum=100, increment=1)` | Spinbox; `.value` int (clamped) |
| `FormattedEntry` | `FormattedEntry(value=0, character_width=None, format_string="{0:.2f} mm", reverse_regex=r"(.+?)\s*mm")` | `.value` float, shown through `format_string`, parsed back with group 1 of `reverse_regex` on focus-out |
| `LabelledEntry` | `LabelledEntry(label="Name", text="", character_width=None)` (`label` is required) | `.value` str (its entry's); `.entry`, `.label` sub-widgets |
| `Label` | `Label(text=None, wrapping=False, **ttk_label_options)` | `.text` or `.value` get/set, updates on screen |
| `URLLabel` | `URLLabel(url=..., text=...)` | Click opens the browser |
| `NumericIndicator` | `NumericIndicator(value_variable=None, value=0, format_string="{0}")` | Read-only formatted number; `.value` |
| `BooleanIndicator` | `BooleanIndicator(diameter=15)` | Green/red dot; `.value` bool |
| `Level` | `Level(maximum=100, width=200, height=20)` | Horizontal bar; `.value` (clamped to 0..maximum) |
| `ProgressBar` | `ProgressBar(maximum=100, mode="determinate")` | `.value`, `step(d)`, `start()`, `stop()`; also driven by notifications (below) |
| `ProgressWindow` | `ProgressWindow(title, message)` | Modal dialog with a `progress_bar` |
| `TableView` | `TableView(columns_labels={"name": "Heading", ...}, is_treetable=False)` | Part 6 |
| `FileViewer` | `FileViewer(root_dir, columns_labels=None, custom_columns=None)` | Lazy file tree built on `TableView` |
| `Figure`, `XYPlot`, `Histogram` | `Figure(figure=None, figsize=(6,4))`, `XYPlot(figsize)`, `Histogram(figsize)` | Part 7 |
| `Image`, `ImageWithGrid`, `SVGImage`, `DynamicImage` | `Image(filepath=None, url=None, pil_image=None)` | Part 7 |
| `CanvasView`, `JSONCanvas` | `CanvasView(width=200, height=200, **canvas_options)` | Part 7 |
| `VideoView` | `VideoView(device=0, zoom_level=3, auto_start=True)` | OpenCV camera; Part 7 |
| `View3D` (`View3DModernGL`, `View3DPyrender`) | `View3DModernGL(width=820, height=620, background="#1a1a1f")` | `load_file(path)` for GLB/GLTF/OBJ/PLY, `load_file_or_warn(path)` |

`ProgressBar` listens on the NotificationCenter, so any object can drive it without holding a reference to it:

```python
from notificationcenter import NotificationCenter
NotificationCenter().post_notification(ProgressBarNotification.step, self, user_info={"step": 10})
```

Optional heavy dependencies (matplotlib, Pillow, OpenCV, trimesh/moderngl, resvg, tkinterdnd2, zeroconf) are imported on first use and offered for installation through `ModulesManager`; extras pre-install them (`pip install "mytk[video,view3d,dnd,svg,remote]"` or `"mytk[all]"`).

## Part 4: Property bindings (Bindable)

Two distinct communication mechanisms. Pick the right one:

| Need | Mechanism |
|---|---|
| Keep a model value and a widget (or two objects) in sync | **Binding** (one-to-one): `Bindable` |
| Tell many unknown listeners that something happened | **NotificationCenter** (one-to-many): Part 5 |

`Bindable.__setattr__` notifies observers on every plain attribute assignment.

**`value` or `value_variable`?** One rule:

- **`value`** is what you read, write, observe and bind. Every widget with a value has it (`Checkbox`, `PopupMenu`, `Slider`, `Entry`, `IntEntry`, `LabelledEntry`, `Label`, the three indicators, `ProgressBar`), and its observers are notified exactly once whether the code or the user changed it.
- **`value_variable`** is the Tk object (`StringVar`, `DoubleVar`...) that holds it. Touch it only to connect it to the Tk widget or to share it between widgets.

Binding on `"value_variable"` still works (the binding then watches the variable's content, not the object), and it is the only way for `RadioButton`, whose `value` is the constant that button stands for. Prefer `"value"` everywhere else: it applies the widget's limits, so a model value outside a `Slider`'s range is brought back in range and the model follows, whereas `"value_variable"` writes it as is.

### A: model attribute <-> widget (two-way), the common case

```python
self.threshold = 50.0                                   # 1. plain attribute, created first
self.slider = Slider(minimum=0, maximum=100)
self.slider.grid_into(self.window, row=0, column=0)     # 2. place the widget (before or after binding)
self.bind_property_to_widget_value("threshold", self.slider)   # 3. bind: the slider jumps to 50
```

Moving the slider sets `self.threshold`; assigning `self.threshold = 20` moves the slider.

### B: any two properties (two-way)

```python
slider.bind_properties("value", indicator, "value")                     # widget drives widget
self.bind_properties("manual_mode", entry, "is_enabled")                # enable state follows a flag
entry.bind_properties("is_enabled", radio, "is_selected")               # ...or another widget's state
self.bind_properties("status_text", label, "text")                      # label text follows a str
```

`a.bind_properties("pa", b, "pb")`: **`a` wins the initial sync** (its current value is pushed to `b`), after which the two follow each other. So call it on the object that holds the truth, normally the model. `bind_property_to_widget_value(prop, widget)` is shorthand for `bind_properties(prop, widget, "value")` (or `"value_variable"` for a widget without the `value` mechanism, like `RadioButton`).

### C: run code when a property changes (no sync)

```python
self.add_observer(self, "number_of_points", context="refresh_graph")

def observed_property_changed(self, observed_object, observed_property_name, new_value, context):
    super().observed_property_changed(observed_object, observed_property_name, new_value, context)
    if context == "refresh_graph":
        self.refresh()
```

`observed.add_observer(observer, "property", context=None)` is called on the *observed* object; `observer.observed_property_changed(...)` is then invoked on each change.

### Binding pitfalls

- **Call `bind_properties` on the object that holds the truth** (see B): the other side is overwritten at setup.
- **Create the attribute before binding it.** Observing a non-existent property raises `AttributeError` ("Attempting to observe inexistent property").
- **Never overwrite a Tk variable with a plain value**: `self.value_variable = 3` raises `TypeError`. Assign `widget.value = 3` instead.
- **Overriding `observed_property_changed`? Call `super()`**, or every binding on that object silently stops working.
- A plain model class must subclass `Bindable` and call `super().__init__()`. `App` and every widget already do.

## Part 5: NotificationCenter (one-to-many)

A thread-safe singleton for "this happened; whoever cares can react". It lives in the separate `notifcenter` package (a mytk dependency), imported as `notificationcenter`:

```python
from enum import Enum
from notificationcenter import NotificationCenter       # NOT mytk.notificationcenter (removed)

class DeviceNotification(Enum):                          # names MUST be Enum members
    will_move = "will_move"
    did_move = "did_move"

# post
NotificationCenter().post_notification(DeviceNotification.did_move, self,
                                       user_info={"position": (x, y, z)})

# observe
NotificationCenter().add_observer(self, self.handle_did_move,
                                  notification_name=DeviceNotification.did_move,
                                  observed_object=device)      # optional sender filter

def handle_did_move(self, notification):
    notification.name         # the Enum member
    notification.object       # who posted it
    notification.user_info    # dict payload, may be None
```

- A plain-string name raises `ValueError`. `notification_name=None` observes everything.
- `remove_observer(self)` (all) or `remove_observer(self, notification_name=...)`; `clear()` drops every observer. Use it in test teardown: the singleton outlives widgets and test cases.
- Built-in: canvas-based widgets post `BaseNotification.did_resize` (`from mytk.base import BaseNotification`).
- The handler runs synchronously in the posting thread. From a worker thread, wrap GUI work in `App.app.schedule_on_main_thread(...)`.
- Handlers that touch a widget must survive the widget being gone; `winfo_exists()` *raises* once the whole Tk app is destroyed:

```python
def handle_notification(self, notification):
    try:
        if self.widget is None or not self.widget.winfo_exists():
            return
    except Exception:
        return
    ...
```

## Part 6: Dialogs, settings, tables

### Dialog

```python
reply = Dialog.showinfo("Acquisition finished", title="Done")
reply = Dialog.showwarning("Laser is on")
reply = Dialog.showerror(f"Cannot open {path}", title="File error")
Dialog.showinfo("Saved", auto_click=(Dialog.Replies.Ok, 2000))     # closes itself after 2 s
```

All are modal and return a `Dialog.Replies` member (`Ok`, `Cancel`, `Abort`, `Timedout`). Custom modal dialog:

```python
class ExportDialog(Dialog):
    def populate_widget_body(self):
        Label("File name").grid_into(self, row=0, column=0, padx=10, pady=5, sticky="e")
        self.name_entry = Entry(value="data.csv", character_width=20)
        self.name_entry.grid_into(self, row=0, column=1, padx=10, pady=5, sticky="w")

dialog = ExportDialog(title="Export", buttons_labels=[Dialog.Replies.Ok, Dialog.Replies.Cancel])
if dialog.run() == Dialog.Replies.Ok:
    export(dialog.name_entry.value)        # values remain readable after the window closes
```

`Dialog(title, buttons_labels=None, geometry=None, auto_position=None, auto_click=(None, None))`. The button row is added for you below the body; override `user_clicked_ok(event, button=None)` (and call `super()`) to validate before closing.

### Configurable: settings with validation and a generated dialog

```python
class Camera(Configurable):
    exposure_time = ConfigurableNumericProperty(default_value=100, min_value=1, max_value=10000,
                                                displayed_name="Exposure time (ms)")
    gain = ConfigurableNumericProperty(default_value=1.0, min_value=0.1, max_value=16.0)
    mode = ConfigurableStringProperty(default_value="fast", valid_set={"fast", "slow"})

camera = Camera()
camera.exposure_time = 99999            # silently clamped to 10000
camera.update_values({"gain": 2})       # coerced to the property type: 2.0
camera.values                           # {'exposure_time': 10000, 'gain': 2.0, 'mode': 'fast'}
camera.show_config_dialog(title="Camera settings")     # modal; applies on Ok; returns the reply
```

This is the natural body of `App.preferences()`: hold a `Configurable` settings object (or make the app `class MyApp(App, Configurable)`) and call `show_config_dialog()`. `camera.values` is a plain dict, so `json.dump` it to persist settings and `update_values(json.load(...))` to restore. `ConfigurableProperty(validate_fct=, valid_set=, value_type=)` is the generic base; `ConfigurableStringProperty(valid_regex=)`; `ConfigModel(properties=[...], values={...})` builds a schema at runtime.

### TableView and TabularData

The table widget and its data model are separate. **Change the data, never the Treeview**: the view updates itself.

```python
table = TableView(columns_labels={"name": "Name", "power": "Power (mW)", "url": "Link"})
table.grid_into(self.window, row=0, column=0, fill=True)
table.delegate = self                                   # optional, see hooks below

data = table.data_source                                # a TabularData
record = data.append_record({"name": "Laser 1", "power": 12.5, "url": "https://example.org"})
data.update_record(record["__uuid"], {"power": 13.0})   # by uuid or by integer index
data.remove_record(0)
data.field("power")                                     # the column as a list
data.record(0); data.records; data.record_count

with PostponeChangeCalls(data):                         # batch: one refresh at the end
    for row in rows:
        data.append_record(row)

data.save("table.json"); data.load("table.json")                 # JSON, without the internal __ fields
frame = data.load_dataframe_from_tabular_data("file.xlsx", header_row=0)   # .csv/.xls/.xlsx via pandas
data.set_records_from_dataframe(frame)                           # column names must be strings: keep header_row=0
```

- Records are dicts. Each gets `__uuid` (also the Treeview item id) and `__puuid` (parent, for trees). Missing columns are filled with `""`.
- Built in, do not re-code: click a heading to sort (click again to reverse), double-click a cell to edit it in place (`table.all_elements_are_editable = False` to forbid, or override `is_editable(item_id, column_name)`), click a cell whose text starts with `http` to open it.
- Typed columns: `data.update_field_properties("power", {"type": float})` (before adding records). Display format: `table.column_formats["power"] = {"format_string": "{0:.1f}", "multiplier": None}` (both keys required).
- Show a subset or reorder: `table.displaycolumns = ["name", "power"]`. Column widths: `table.widget.column("name", width=120)`.
- Selection: `table.widget.selection()` returns item ids, which are the `__uuid`s: `data.record(item_id)`.
- Delegate hooks, all optional, on any object: `selection_changed(event, table)`, `source_data_changed(table)`, `click(event, table)`, `click_cell(item_id, column_name, table)`, `click_header(column_name, table)`, `doubleclick(event, table)`, `doubleclick_cell(item_id, column_name, table)`, `doubleclick_header(column_name, table)`. The `click`, `click_cell`, `click_header` and `doubleclick` hooks return `True` to let the default behaviour run, `False` to stop it.
- Tree tables: `TableView(..., is_treetable=True)`, then `data.insert_child_records(None, records, pid=parent_uuid)`; `data.record_childs(uuid)`.
- `table.empty()` removes everything.

## Part 7: Plots, images, canvas, video

**Matplotlib.** `Figure` embeds a matplotlib figure; draw with normal matplotlib calls.

```python
plot = XYPlot(figsize=(6, 4))                 # figsize is required for XYPlot/Histogram
plot.grid_into(self.window, row=0, column=0, fill=True)
plot.append(x, y); plot.update_plot()         # simple live line plot; plot.clear_plot()

fig = Figure(figsize=(6, 4)); fig.grid_into(self.window, row=1, column=0)
axis = fig.figure.add_subplot()               # fig.figure, fig.first_axis, fig.axes
axis.plot(xs, ys); fig.figure.canvas.draw()
fig.toolbar                                   # NavigationToolbar2Tk: created, not placed
```

`XYPlot.update_plot()` clears the axis and redraws `plot.x`/`plot.y` as a black line, so set axis labels after it, or subclass and override `update_plot` for anything richer. `fig.styles_pointmarker()` / `fig.styles_points_linemarkers()` return ready-made marker style dicts.

**Images.** `Image(filepath=...)`, `Image(url=...)` or `Image(pil_image=...)`. `image.is_rescalable = True` makes it follow its grid cell, keeping the aspect ratio, but it measures the cell immediately: the cell must have a resize weight (`grid_into(..., fill=True)`) **and** the window must already be laid out, otherwise it raises `ValueError`. Enable it after `app.root.update()`, or from the running loop with `app.after(100, ...)`. To show a new frame: `image.pil_image = new; image.update_display()`. `ImageWithGrid` adds `is_grid_showing` and `grid_count`. `SVGImage(filepath=|data=)` has `load`, `load_from_file`, `accept_dropped_svg_files()`.

**Canvas.** `CanvasView(width, height)`: draw with raw Tk (`canvas.widget.create_line(...)`) or with elements positioned by `Point`s:

```python
from mytk.canvasview import Rectangle, Oval, Line, Arrow, CanvasLabel, Arc
from mytk.vectors import Point, Vector, Basis, DynamicBasis

canvas.place(Rectangle(size=(40, 20), fill="steelblue"), position=Point(60, 40))
canvas.place(CanvasLabel(font_size=10, text="Sample", anchor="w"), position=Point(10, 80))
canvas.save_to_pdf("drawing.pdf")
```

`canvas.relative_basis` expresses positions as fractions of the canvas size, but it is only meaningful once the window is laid out (the canvas is 1x1 pixel before that) and placed elements do not move by themselves: redraw from a `BaseNotification.did_resize` observer. For data axes with ticks use `mytk.dataviews.XYCoordinateSystemElement` (plus `Function`, `DataPoint`): its sizes and positions are `Vector`/`Point` objects in a basis, so copy the setup from `mytk/example_apps/canvas_app.py` rather than guessing. Subclass `DynamicImage` and override `draw_canvas()` for a canvas you redraw yourself. `JSONCanvas` renders JSON Canvas 1.0 documents (`load(dict)`, `load_from_file(path)`).

**Video.** `VideoView(device=0)` shows a live OpenCV camera. `VideoView.available_devices()`; `start_capturing()`, `stop_capturing()`, `start_streaming(path)`, `stop_streaming()`. Ready-made controls: `start, save, stream = video.create_behaviour_buttons()` and `popup = video.create_behaviour_popups()` return already-wired widgets for you to place; or wire your own with `bind_button_to_startstop_behaviour(button)`, `bind_button_to_save_behaviour(button)`, `bind_button_to_stream_behaviour(button)`, `bind_popup_to_camera_selection_behaviour(popup)`.

## Part 8: Remote control, drag and drop, modules

**Remote control.** Expose app methods to other processes (stdlib XML-RPC; each call is marshaled to the Tk thread, so it may touch widgets):

```python
class MyApp(App, RemoteControllable):
    @remote_command
    def set_power(self, value): ...

    @remote_command(name="status")
    def read_status(self):
        return {"on": True}                 # numbers, str, bool, None, list, dict only

app = MyApp(name="Laser")
app.start_remote()                          # 127.0.0.1:8777; stops with the window
# app.advertise_remote()  instead: also announce on the LAN via mDNS (needs zeroconf)
```

Client: `mytk.connect(host, port, app_name="Laser").set_power(2.5)`, `mytk.remote_app.status()` (localhost default), `mytk.discover(app_name="Laser")`, `mytk.browse()`. Shell: `mytk "set_power(2.5)"`, `mytk --list`, `mytk --discover --app-name Laser "status()"`, `mytk --browse`. Positional arguments only.

**Drag and drop.** After placement: `ok = widget.accept_dropped_files(self.files_dropped)`; the callback receives a list of paths. Returns `False` when tkdnd is unavailable (the widget keeps working).

**Optional modules.** `ModulesManager.install_and_import_modules_if_absent({"pip-name": "import_name"}, ask_for_confirmation=True)`, then `ModulesManager.imported["pip-name"]`. Also `ModulesManager.is_installed(name)`.

**Command line.** `python -m mytk` runs the example apps (`-l` lists them, `-e 1,3` runs some, `-t` runs the tests, `-c` prints the class hierarchy); `python -m mytk --install-skill [--project]` installs this skill.

## Checklist before handing back mytk code

- No `tk.Tk()`, `messagebox`, `Toplevel`, `ttk.Frame`, `ttk.Treeview`, `FigureCanvasTkAgg` or hand-made queue polling: each has a mytk equivalent above.
- State is held in plain attributes and bound to widgets; no callback whose only job is to copy a value.
- No widget object is placed twice; `bind_event`, `accept_dropped_files` and raw `obj.widget` calls come after placement.
- `save()` and `preferences()` are overridden (the menu items exist whether or not you implement them).
- Worker threads reach the GUI only through `schedule_on_main_thread`.
- Button callbacks take `(event, button)`; Checkbox and RadioButton callbacks take `(widget)`; PopupMenu callbacks take `(popup, index)`.
- Something not covered here? Read the source before improvising: it is small. `mytk/app.py`, `base.py`, `bindable.py`, and `mytk/example_apps/` (`example.py` tours every widget, `controlpanel_app.py` shows bindings and timers, `filters_app.py` a `TableView` delegate, `canvas_app.py` the canvas API).
