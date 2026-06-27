---
name: mytk
description: Build Tkinter GUIs with the mytk library — connect model state to widgets with two-way property bindings, observe property changes, and broadcast/observe one-to-many events with the NotificationCenter (Enum-based notifications). Use when writing or editing mytk apps/widgets, wiring a variable to its on-screen control, reacting to value changes, or decoupling components via notifications.
metadata: {"version": "1.0", "applies-to": "mytk (this repository)"}
---

# mytk

## Overview

`mytk` is a Tkinter wrapper aimed at scientists. Widgets are Python objects
(subclasses of `Base`) that wrap an underlying Tk/ttk widget, created lazily
when the widget is placed with `grid_into`/`pack_into`/`place_into`.

It offers **two distinct communication mechanisms**. Pick the right one:

| Need | Mechanism | Class |
|------|-----------|-------|
| Keep a model value and a widget (or two objects) in sync | **Property binding** (one-to-one) | `Bindable` |
| Tell *many* unknown listeners that something happened | **NotificationCenter** (one-to-many) | `NotificationCenter` |

Binding is for "this value *is* that value." Notifications are for "this event
happened; whoever cares can react." Don't reach for the NotificationCenter to
sync a single value — use a binding.

---

## Part 1 — Property bindings (Bindable)

### The core idea

Every `Base` widget and the `App` class inherit from `Bindable`. A `Bindable`
can observe changes to a *named property* on another `Bindable`, and `mytk`
builds two-way binding on top of that observer pattern.

`Bindable` overrides `__setattr__`: whenever you assign to a plain Python
attribute, observers are notified automatically. Tk `Variable`s (e.g.
`StringVar`, `DoubleVar`, `BooleanVar`) are handled specially — the binding
watches the variable's *value* (via `trace_add`), not the variable object.

> Critical rule: never overwrite a Tk `Variable` attribute with a plain value.
> Assigning `self.value_variable = 3` raises `TypeError`. Set the variable's
> value instead: `self.value_variable.set(3)` (or assign through a bound plain
> property — see below).

### `value` vs `value_variable`

Most interactive widgets expose:

- `value_variable` — the underlying Tk `Variable` the Tk widget is wired to.
- `value` — a plain Python property that reads/writes `value_variable.get()/set()`.

Bind to `value_variable` (the Tk side) when connecting a model property to a
widget, or use the `value` convenience property.

### Recipe A — connect a model value to its widget

This is the most common task: a model attribute should always reflect (and be
reflected by) an on-screen control. Use `bind_property_to_widget_value`, which
binds a property to the widget's `value_variable`.

```python
from mytk import App, Checkbox, Slider, Label

class MyApp(App):
    def __init__(self):
        super().__init__(name="Demo")

        # 1. A PLAIN python attribute on a Bindable (App is Bindable).
        self.acquisition_is_running = False     # model state
        self.threshold = 50.0

        # 2. The widgets.
        self.run_checkbox = Checkbox(label="Running")
        self.run_checkbox.grid_into(self.window, row=0, column=0)
        self.slider = Slider(minimum=0, maximum=100)
        self.slider.grid_into(self.window, row=1, column=0)

        # 3. Bind model attribute <-> widget value_variable (TWO-WAY).
        self.bind_property_to_widget_value("acquisition_is_running", self.run_checkbox)
        self.bind_property_to_widget_value("threshold", self.slider)

# Now: toggling the checkbox sets self.acquisition_is_running, AND
# setting self.acquisition_is_running = True checks the box. Same for threshold.
```

The binding fires immediately on setup, so the widget is initialized to the
model's current value the moment you bind.

### Recipe B — bind any two properties (two-way)

`bind_properties(this_property, other_object, other_property)` synchronizes any
two properties on two `Bindable`s, regardless of which one changes.

```python
# Mirror one widget's value into another (e.g. a slider drives an indicator):
slider.bind_properties("value_variable", indicator, "value_variable")

# Bind a widget's enabled state to a model flag — disable the entry whenever
# show_principal_rays is True/False:
number_entry.bind_properties("is_disabled", self, "show_principal_rays")

# Bind a Label's text to a model property:
label.bind_properties("value_variable", self, "status_text")  # self.status_text is a str
```

`bind_property_to_widget_value(prop, widget)` is just shorthand for
`bind_properties(prop, widget, "value_variable")`.

### Recipe C — observe a change without binding (run code on change)

When you don't want to *sync* a value but want to *react* to it (recompute,
redraw), register an observer and implement `observed_property_changed`.

```python
class MyApp(App):
    def __init__(self):
        super().__init__()
        self.number_of_points = 100

        # Observe my own property. Optionally pass context to distinguish sources.
        self.add_observer(self, "number_of_points", context="refresh_graph")

    def observed_property_changed(self, observed_object, observed_property_name,
                                  new_value, context):
        # ALWAYS call super() first so binding keeps working — the binding
        # machinery rides on this same callback.
        super().observed_property_changed(observed_object, observed_property_name,
                                          new_value, context)
        if context == "refresh_graph":
            self.refresh()
```

Signature you must implement on the observer:
`observed_property_changed(self, observed_object, observed_property_name, new_value, context)`.
For a Tk `Variable` property, `new_value` is the variable's *value*, not the
variable object.

### Binding pitfalls

- **The class must subclass `Bindable`.** `App` and all `Base` widgets already
  do. A plain model class must `class Model(Bindable)` and call `super().__init__()`.
- **Observing a non-existent property raises `AttributeError`** ("Attempting to
  observe inexistent property ..."). Create the attribute in `__init__` before
  binding.
- **Don't clobber Tk variables.** Bind a *plain* property and let `mytk` push
  values into the `value_variable` for you; never `self.value_variable = <plain>`.
- **Override `observed_property_changed`? Call `super()`** or you silently break
  every binding on that object.
- Bindings are one-to-one. For one-to-many, use the NotificationCenter.

---

## Part 2 — NotificationCenter (one-to-many)

Use the NotificationCenter when a sender wants to announce an event without
knowing who (if anyone) is listening — e.g. "a device moved," "progress
advanced," "the canvas resized." It is a thread-safe singleton.

### Notification names MUST be Enum members

This is enforced: passing a plain string to `post_notification`,
`add_observer`, or `Notification(...)` raises `ValueError`. Define an `Enum`
subclass, conventionally with `will_*`/`did_*` members:

```python
from enum import Enum

class DeviceNotification(Enum):
    will_move = "will_move"
    did_move  = "did_move"
```

### Posting a notification

```python
from mytk.notificationcenter import NotificationCenter

# self is the "notifying_object"; user_info is an optional dict of payload.
NotificationCenter().post_notification(
    DeviceNotification.did_move,
    self,
    user_info={"position": (x, y, z)},
)
```

### Adding an observer

```python
class PositionReadout:
    def __init__(self, device):
        # method is the callable invoked with the Notification as its only arg.
        NotificationCenter().add_observer(
            self,
            self.handle_notification,
            notification_name=DeviceNotification.did_move,
            observed_object=device,   # OPTIONAL: only notifications from `device`
        )

    def handle_notification(self, notification):
        # notification.name      -> the Enum member (e.g. DeviceNotification.did_move)
        # notification.object    -> who posted it (the notifying_object)
        # notification.user_info -> the dict payload (may be None)
        x, y, z = notification.user_info["position"]
        ...
```

- `notification_name=None` observes **all** notifications.
- `observed_object=<obj>` filters to notifications posted by that one object;
  omit it to receive from any sender.
- One handler can serve several notifications — register it for each name and
  branch on `notification.name` (see the `ProgressBar` pattern in
  `mytk/progressbar.py`).

### Built-in notifications

`Base` widgets post `BaseNotification.did_resize` (in `mytk.base`) when resized:

```python
from mytk.base import BaseNotification
NotificationCenter().add_observer(self, self.canvas_did_resize, BaseNotification.did_resize)
```

### Removing observers & guarding stale ones (important)

The NotificationCenter is a **singleton that outlives individual widgets and
test cases**. Observers accumulate and can fire after their Tk widget is gone.

1. Remove observers you no longer need:
   ```python
   NotificationCenter().remove_observer(self)  # all
   NotificationCenter().remove_observer(self, notification_name=DeviceNotification.did_move)
   ```
2. Guard widget-backed handlers — `winfo_exists()` *raises* `TclError` (it does
   not just return False) once the whole Tk app is torn down:
   ```python
   def handle_notification(self, notification):
       try:
           if self.widget is None or not self.widget.winfo_exists():
               return
       except Exception:
           return  # the entire Tk application was destroyed
       ...        # safe to touch the widget here
   ```

### NotificationCenter pitfalls

- Plain-string names → `ValueError`. Always use an `Enum` member.
- `user_info` may be `None`; check before indexing.
- In tests, the singleton persists between cases — call
  `NotificationCenter().clear()` in teardown, or remove your observers, to avoid
  stale-observer crashes.

---

## Quick decision guide

- "Keep this number/flag/text in sync with a control" → `bind_property_to_widget_value`.
- "Keep two arbitrary properties equal" → `bind_properties`.
- "Run code when a property changes (don't sync)" → `add_observer` +
  `observed_property_changed` (call `super()`).
- "Announce an event to any interested listeners" → `NotificationCenter`
  with an `Enum` notification name.

## Reference files in this repo

- `mytk/bindable.py` — binding/observer implementation.
- `mytk/notificationcenter.py` — NotificationCenter, `Notification`, enum rule.
- `mytk/example_apps/controlpanel_app.py` — `bind_property_to_widget_value` in an App.
- `mytk/example_apps/canvas_app.py` — many `bind_properties`, `add_observer`,
  `observed_property_changed`, and a `did_resize` observer.
- `mytk/progressbar.py` — a widget that both defines an `Enum` notification and
  observes it, with a guarded `handle_notification`.
