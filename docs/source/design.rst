Design & Architecture
=====================

This document explains *how* myTk is built and *why* it is built that way. It
sits between the narrative :doc:`README <readme>` and the per-module
:doc:`API Reference <index>`: read the README to see what myTk does, read this
to understand its structure, then dive into the API for details.


Design goals
------------

myTk exists to make Tkinter pleasant for scientists and other non-professional
programmers who need a working desktop GUI without adopting a heavy framework.
Five goals drive every design decision:

**G1 — Stay simple and portable.**
   Tk ships with Python and is portable across macOS, Windows and Linux. There
   is nothing to install to get a window on screen, and apps move between
   machines and operating systems without surprises. This is the single
   biggest reason myTk is built on Tk rather than Qt or wxWidgets.

**G2 — Bring modern macOS/Cocoa patterns to Tk.**
   Raw Tkinter scatters behaviour across loose callbacks. myTk borrows the
   patterns Apple matured over decades — Key-Value Observing (binding, bindable),
   ``NSNotificationCenter`` (notifications), and delegation — because they
   organize event-driven code far better than ad-hoc callbacks.

**G3 — Encapsulate, but never hide.**
   Every Tk widget is wrapped in a :class:`~mytk.views.View` that exposes
   convenient behaviour, yet the underlying Tk widget is always reachable via
   ``.widget`` for anything myTk does not cover. You are never boxed in and limited.

**G4 — Remove friction.**
   Where Tk forces long verbose text for no reason, myTk supplies a sensible default and
   lets you override it. For example, Tk requires you to name a widget's parent
   at creation; myTk does not. Complex widgets like
   :class:`~mytk.tableview.TableView` work out of the box and let you refine
   behaviour through a *delegate* rather than wiring callbacks by hand.

**G5 — Keep useful but less portable features optional.**
   3D rendering (:class:`~mytk.view3d.View3D`) and OS drag-and-drop pull in
   large or platform-specific dependencies. These are loaded on demand and
   degrade gracefully: if the dependency is absent, the feature reports itself
   unavailable and the rest of the app keeps running.


Architectural overview
-----------------------

myTk is a thin, layered wrapper around Tk. From the bottom up:

* :class:`~mytk.bindable.Bindable` — the foundation. A property-observer and
  two-way binding mechanism with no Tk dependency of its own.
* :class:`~mytk.base.Base` — combines ``Bindable`` with two mixins
  (:class:`~mytk.eventcapable.EventCapable`,
  :class:`~mytk.draganddropcapable.DragAndDropCapable`) to give every widget a
  uniform interface for state, grid geometry, event binding and lifecycle.
* :class:`~mytk.views.View` and its many subclasses — everything visible on
  screen (except the window) is a ``View`` that wraps one Tk widget.
* :class:`~mytk.app.App` and :class:`~mytk.window.Window` — the application
  controller and the top-level container.

The complete class hierarchy (regenerate any time with ``python -m mytk -c``,
which emits this Graphviz source). Solid arrows are subclassing; dashed arrows
are the mixins folded into ``Base`` and ``App``:

.. graphviz::
   :caption: myTk class hierarchy (``python -m mytk -c``)
   :alt: myTk class hierarchy

   digraph myTk {
       rankdir="LR";
       node [shape=box, fontname="Helvetica", fontsize=10];
       edge [arrowsize=0.7];

       "Bindable" [style=filled, fillcolor="#cfe8ff"];
       "Base"     [style=filled, fillcolor="#d8f5d0"];

       "EventCapable"       [style="filled,dashed", fillcolor="#fff2cc"];
       "DragAndDropCapable" [style="filled,dashed", fillcolor="#fff2cc"];
       "EventCapable"       -> "Base" [style=dashed, label="mixin", fontsize=8];
       "DragAndDropCapable" -> "Base" [style=dashed, label="mixin", fontsize=8];
       "EventCapable"       -> "App"  [style=dashed, label="mixin", fontsize=8];

       "Bindable" -> "App";
       "Bindable" -> "TabularData";
       "TabularData" -> "FileTreeData";

       "Bindable" -> "Base";
       "Base" -> "Button";
       "Base" -> "CanvasView";
       "CanvasView" -> "DynamicImage";
       "CanvasView" -> "JSONCanvas";
       "CanvasView" -> "BooleanIndicator";
       "CanvasView" -> "Level";
       "Base" -> "Image";
       "Image" -> "ImageWithGrid";
       "Base" -> "Label";
       "Label" -> "URLLabel";
       "Base" -> "View";
       "View" -> "LabelledEntry";
       "Base" -> "Box";
       "Base" -> "Dialog";
       "Dialog" -> "SimpleDialog";
       "Dialog" -> "ConfigurationDialog";
       "Dialog" -> "ProgressWindow";
       "Base" -> "Window";
       "Base" -> "Checkbox";
       "Base" -> "Entry";
       "Base" -> "FormattedEntry";
       "Base" -> "CellEntry";
       "Base" -> "IntEntry";
       "Base" -> "Slider";
       "Base" -> "Figure";
       "Figure" -> "XYPlot";
       "Figure" -> "Histogram";
       "Base" -> "TableView";
       "TableView" -> "FileViewer";
       "Base" -> "NumericIndicator";
       "Base" -> "PopupMenu";
       "Base" -> "ProgressBar";
       "Base" -> "RadioButton";
       "Base" -> "View3D";
       "View3D" -> "View3DModernGL";
       "View3D" -> "View3DPyrender";
       "Base" -> "VideoView";
   }

Note that :class:`~mytk.app.App` is *not* a ``Base``/``View``: it is a
controller, not something drawn on screen, so it derives from ``Bindable`` and
``EventCapable`` directly. Likewise :class:`~mytk.tabulardata.TabularData` is a
pure model and derives only from ``Bindable``.


Core mechanisms
---------------

These six mechanisms *are* the framework. Everything else is widgets built on
top of them.

Binding and property observation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:class:`~mytk.bindable.Bindable` implements a Property-Value-Observer pattern
inspired by macOS Key-Value Observing. Any object can observe a property on
another object, and two properties can be *bound* so that changing one always
updates the other, whether the change comes through the interface or from your
own code.

* :meth:`~mytk.bindable.Bindable.add_observer` — register interest in a property.
* :meth:`~mytk.bindable.Bindable.bind_properties` — keep two properties
  synchronized in both directions.
* :meth:`~mytk.bindable.Bindable.bind_property_to_widget_value` — synchronize a
  model property with what a widget displays.

It works uniformly on plain Python attributes *and* on Tk ``Variable`` objects,
so reactive GUIs do not require you to think about ``StringVar``/``IntVar``
plumbing. This is the mechanism to reach for when two pieces of state must stay
equal.

Notifications
^^^^^^^^^^^^^

:class:`~mytk.notificationcenter.NotificationCenter` is a singleton providing
one-to-many, decoupled communication, modelled on ``NSNotificationCenter``. A
notifier posts a named notification without knowing who, if anyone, is
listening; observers subscribe by name.

* Notification names must be defined as :class:`enum.Enum` subclasses, which
  keeps them discoverable and typo-proof.
* :meth:`~mytk.notificationcenter.NotificationCenter.add_observer`,
  :meth:`~mytk.notificationcenter.NotificationCenter.post_notification`,
  :meth:`~mytk.notificationcenter.NotificationCenter.remove_observer`.

Use notifications (rather than binding) when the relationship is one-to-many or
when the sender should know nothing about the receivers — e.g. a device
announcing ``will_move`` / ``did_move`` to whatever cares.

Delegation
^^^^^^^^^^

For complex widgets, myTk prefers a *delegate* object over a pile of callbacks.
The widget implements sensible default behaviour and calls optional methods on
your delegate when it needs a decision. :class:`~mytk.tableview.TableView` is
the canonical example; a delegate may implement any subset of:

* ``selection_changed(event)``
* ``click_header(column)`` — default: sort rows by that column
* ``click_cell(item_id, column_id)`` — default: open the value if it is a URL
* ``doubleclick_header(column)`` / ``doubleclick_cell(item_id, column_id)``

This keeps related behaviour in one cohesive object and lets you override only
what you care about.

Events and scheduling
^^^^^^^^^^^^^^^^^^^^^^

:class:`~mytk.eventcapable.EventCapable` is a mixin (on both ``Base`` and
``App``) for timed callbacks and event wiring:
:meth:`~mytk.eventcapable.EventCapable.after`,
:meth:`~mytk.eventcapable.EventCapable.after_cancel` (and ``after_cancel_all``),
:meth:`~mytk.eventcapable.EventCapable.bind_event`, and
:meth:`~mytk.eventcapable.EventCapable.event_generate`. It exists so that
timer and event management is consistent across widgets and the application
object, which otherwise handle their Tk widget very differently.

Configuration
^^^^^^^^^^^^^

Scientific applications are full of adjustable parameters — exposure time,
gain, wavelength, thresholds, paths. :class:`~mytk.configurable.Configurable`
turns a declared set of typed, validated properties into a working settings
dialog automatically:

* :class:`~mytk.configurable.ConfigurableProperty` (and the
  ``ConfigurableStringProperty`` / ``ConfigurableNumericProperty`` subclasses)
  declare a value, its allowed type/range, and know how to
  :meth:`~mytk.configurable.ConfigurableProperty.sanitize` and validate it.
* :class:`~mytk.configurable.Configurable` aggregates them and exposes
  :meth:`~mytk.configurable.Configurable.is_valid`,
  :meth:`~mytk.configurable.Configurable.update_values`, and
  :meth:`~mytk.configurable.Configurable.show_config_dialog`.
* ``ConfigModel`` and ``ConfigurationDialog`` build and present the UI, so you
  never hand-write a settings dialog or its validation logic.

Drag and drop
^^^^^^^^^^^^^

OS-level file drops are not part of core Tk. :class:`~mytk.draganddropcapable.DragAndDropCapable`
is a per-widget mixin (mirroring ``EventCapable``) that adds
:meth:`~mytk.draganddropcapable.DragAndDropCapable.accept_dropped_files`; the
low-level work of loading the ``tkdnd`` extension and parsing the payload lives
in :mod:`mytk.dnd`. The dependency (``tkinterdnd2``/``tkdnd``) is installed on
demand the first time it is used. If it cannot be enabled,
:meth:`~mytk.draganddropcapable.DragAndDropCapable.is_drag_and_drop_available`
returns ``False`` and the app continues without drops.


Data layer (model/view)
------------------------

myTk separates tabular data from its display in a small MVC arrangement:

* :class:`~mytk.tabulardata.TabularData` is the **model** — an ordered,
  observable collection of records (:meth:`~mytk.tabulardata.TabularData.append_record`,
  :meth:`~mytk.tabulardata.TabularData.insert_record`,
  :meth:`~mytk.tabulardata.TabularData.update_record`,
  :meth:`~mytk.tabulardata.TabularData.records_as_namedtuples`, …). It derives
  from ``Bindable``, so changes propagate automatically.
* :class:`~mytk.tableview.TableView` is the **view** — it observes a
  ``TabularData`` source and reacts through
  :meth:`~mytk.tableview.TableView.source_data_changed`,
  ``source_data_added_or_updated`` and ``source_data_deleted``, while a delegate
  customizes interaction.

Editing a cell, sorting, resizing columns and following URL cells are handled
for you; the model stays the single source of truth.


Visualization
-------------

* :class:`~mytk.figures.Figure` embeds a Matplotlib figure (provide your own
  ``plt.figure`` or use the one it creates) with an optional toolbar.
* :class:`~mytk.view3d.View3D` embeds a 3D mesh viewer. It loads
  GLB/GLTF/OBJ/PLY/STL via ``trimesh``, renders off-screen (drag to orbit,
  scroll to zoom), and **picks its backend automatically**: ``pyrender`` if
  available, otherwise a built-in ``moderngl`` renderer. You may instantiate
  ``View3DPyrender`` or ``View3DModernGL`` directly. Like drag-and-drop, the
  heavy dependencies are optional and loaded on demand.


Layout model
------------

Positioning is the part of Tk that confuses newcomers most, so it is worth
stating plainly. Tk offers three geometry managers — ``grid``, ``pack`` and
``place`` — and myTk standardizes on **grid**. A view is divided into a grid of
rows and columns, and children are placed into cells with ``grid_into``.

Key levers:

* **Resizing** is governed by per-row/column ``weight`` (which cells absorb
  extra space) and by each widget's ``sticky`` option (whether the widget grows
  to fill its cell).
* ``grid_propagate`` controls whether a container resizes to fit its children
  or holds a fixed size.
* ``rowspan`` / ``columnspan`` let a widget occupy a range of cells.

A ``View`` can itself contain a grid, so a single grid cell can hold a
self-contained sub-layout. Recommended background reading: the
`pythonguis.com grid/pack/place FAQ
<https://www.pythonguis.com/faq/pack-place-and-grid-in-tkinter/>`_ and
`TkDocs <https://tkdocs.com/tutorial/index.html>`_.


Conventions & idioms
--------------------

* **"View" means anything visible on screen except the window.** The window is
  a :class:`~mytk.window.Window`; everything inside it is a ``View``.
* **The ``.widget`` escape hatch.** Reach through any ``View`` to its raw Tk
  widget when you need behaviour myTk does not implement.
* **Mixin composition.** Cross-cutting capabilities (events, drag-and-drop) are
  small mixins folded into ``Base`` rather than inheritance trees.
* **Enum-named notifications.** Notification identifiers are ``Enum`` members,
  not strings.
* **Delegate methods over callbacks** for non-trivial widgets.


Extending myTk
--------------

The fastest way to learn the extension points is to read
``mytk/example_apps/`` (``mytk.py``, ``lensviewer_app.py``, ``filters_app.py``,
``microscope_app.py``, ``dnd_app.py``, ``view3d_app.py``). In short:

* **A new widget** subclasses :class:`~mytk.base.Base` (or an existing
  ``View``) and implements ``create_widget`` to build its Tk widget.
* **Custom table behaviour** is added by setting a delegate on
  :class:`~mytk.tableview.TableView`, not by subclassing it.
* **A new notification** is a new ``Enum`` member posted through the shared
  :class:`~mytk.notificationcenter.NotificationCenter`.
* **A new 3D backend** follows the ``View3DPyrender`` / ``View3DModernGL``
  pattern.

A minimal application is just:

.. code-block:: python

   from mytk import App, Label

   class MyApp(App):
       def __init__(self):
           super().__init__(geometry="600x400", name="MyApp")
           label = Label("Hello, myTk")
           label.grid_into(self.window, row=0, column=0)

   MyApp().mainloop()


Design decisions & trade-offs
-----------------------------

**Why three coordination mechanisms (binding, notifications, delegation)?**
   They solve different shapes of problem and overlap little. *Binding* is for
   "these two values must stay equal." *Notifications* are for one-to-many,
   sender-knows-nothing broadcast. *Delegation* is for "this widget needs a
   decision from its owner." Forcing all three through a single callback style
   is exactly the tangle myTk set out to avoid.

**Why Tk rather than Qt/wx?**
   Portability and durability. Tk is in the standard library, so there is
   nothing to install and apps survive moves between machines and OSes. The
   author's experience is that Qt, while powerful, is heavier than most
   scientific apps need and more fragile to transport. Encapsulating Tk turned
   out easier than simplifying Qt.

**Why optional, on-demand dependencies?**
   3D rendering and OS drag-and-drop are valuable but expensive (large or
   platform-specific packages). Making them hard requirements would tax every
   user for features most do not need, and would undermine G1 (stay in the
   standard library by default). On-demand loading with graceful degradation
   keeps the baseline install tiny.

