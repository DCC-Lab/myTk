.. _examples:

Example applications
====================

myTk ships a set of runnable example apps in ``mytk/example_apps/``.
Launch any of them as a module, for example::

    python -m mytk.example_apps.example

Each section shows what the example demonstrates, a screenshot and its
full source.

example.py
----------

**Comprehensive tour of myTk widgets in a single window.**

Lays out Labels, entries, PopupMenu, URLLabel, Image, TableView, Figure, Slider,
Level, Checkbox and a CanvasView (raw and CanvasElement APIs), and conditionally
adds View3D and VideoView when their optional dependencies are available.

Loads ``logo.png`` from this directory; View3D/VideoView/drag-and-drop are optional.

Run it with ``python -m mytk.example_apps.example``.

.. image:: /_static/examples/example.png
   :alt: example.py screenshot
   :width: 100%

.. literalinclude:: ../../mytk/example_apps/example.py
   :language: python
   :linenos:

canvas_app.py
-------------

**Interactive optical ray-tracing playground built on CanvasView.**

Draws lenses, apertures and rays on a CanvasView using its coordinate-system and
dynamic-basis support, with a TableView to edit the optical elements and live
canvas refreshes driven by property binding and notifications.

Needs the optional ``raytracing`` package (and ``pyperclip`` for "Copy script").

Run it with ``python -m mytk.example_apps.canvas_app``.

.. image:: /_static/examples/canvas_app.png
   :alt: canvas_app.py screenshot
   :width: 100%

.. literalinclude:: ../../mytk/example_apps/canvas_app.py
   :language: python
   :linenos:

contrast_app.py
---------------

**Browse a folder of CSV files and plot contrast vs. time.**

Pairs a FileViewer (with custom columns and directory selection) with an XYPlot:
selecting a CSV reads it and plots elapsed time against contrast, using property
binding and PostponeChangeCalls for batched data-source updates.

Needs ``pandas`` and a directory of CSV files to plot.

Run it with ``python -m mytk.example_apps.contrast_app``.

.. note::
   Screenshot not yet available — regenerate with ``make example-shots``.

.. literalinclude:: ../../mytk/example_apps/contrast_app.py
   :language: python
   :linenos:

controlpanel_app.py
-------------------

**Live acquisition control panel with a real-time plot.**

Simulates a continuous acquisition: an XYPlot is appended to on a scheduled timer,
BooleanIndicator widgets show status, and property binding enables/disables the
controls. Demonstrates the after()/ticker update pattern.

Run it with ``python -m mytk.example_apps.controlpanel_app``.

.. image:: /_static/examples/controlpanel_app.png
   :alt: controlpanel_app.py screenshot
   :width: 100%

.. literalinclude:: ../../mytk/example_apps/controlpanel_app.py
   :language: python
   :linenos:

dnd_app.py
----------

**drag files from Finder/Explorer onto the window.**

Drop one or more files onto the label and their paths are listed. Demonstrates
`Base.accept_dropped_files`, which enables OS file drops on any myTk widget.

    python -m mytk.example_apps.dnd_app

Run it with ``python -m mytk.example_apps.dnd_app``.

.. image:: /_static/examples/dnd_app.png
   :alt: dnd_app.py screenshot
   :width: 100%

.. literalinclude:: ../../mytk/example_apps/dnd_app.py
   :language: python
   :linenos:

file_calculator_app.py
----------------------

**File browser that runs a calculation on the selection.**

Combines a FileViewer (custom columns, directory picker) with property binding and a
selection-changed delegate: picking a file triggers a calculation whose result is
shown alongside an XYPlot.

Run it with ``python -m mytk.example_apps.file_calculator_app``.

.. note::
   Screenshot not yet available — regenerate with ``make example-shots``.

.. literalinclude:: ../../mytk/example_apps/file_calculator_app.py
   :language: python
   :linenos:

fileviewer_app.py
-----------------

**Minimal directory browser using FileViewer.**

Shows a FileViewer with configurable columns (name, size, modification date) and a
directory picker, using PostponeChangeCalls for efficient data-source updates.

Run it with ``python -m mytk.example_apps.fileviewer_app``.

.. image:: /_static/examples/fileviewer_app.png
   :alt: fileviewer_app.py screenshot
   :width: 100%

.. literalinclude:: ../../mytk/example_apps/fileviewer_app.py
   :language: python
   :linenos:

filters_app.py
--------------

**Browse a spectral-filter database and plot transmission curves.**

A TableView of optical filters drives an XYPlot of the selected filter's spectrum,
with JSON/ZIP data loading (local or downloaded), a preferences Dialog and clipboard
export.

Reads data from ``tpop_filters_data/`` (or downloads it); ``requests``/``pyperclip``
are optional.

Run it with ``python -m mytk.example_apps.filters_app``.

.. image:: /_static/examples/filters_app.png
   :alt: filters_app.py screenshot
   :width: 100%

.. literalinclude:: ../../mytk/example_apps/filters_app.py
   :language: python
   :linenos:

formatted_entry_app.py
----------------------

**Showcase of FormattedEntry number formatting.**

Lays out FormattedEntry widgets with different format strings and reverse-parse
regexes (plain, fixed decimals, scientific, percentage), bound to values via
bind_property_to_widget_value inside a Box layout.

Run it with ``python -m mytk.example_apps.formatted_entry_app``.

.. image:: /_static/examples/formatted_entry_app.png
   :alt: formatted_entry_app.py screenshot
   :width: 100%

.. literalinclude:: ../../mytk/example_apps/formatted_entry_app.py
   :language: python
   :linenos:

jsoncanvas_app.py
-----------------

**Minimal viewer for JSON Canvas 1.0 documents.**

Loads a built-in sample on startup. Click "Load…" to open a `.canvas` or
`.json` file that follows the JSON Canvas 1.0 spec.

Run it with ``python -m mytk.example_apps.jsoncanvas_app``.

.. image:: /_static/examples/jsoncanvas_app.png
   :alt: jsoncanvas_app.py screenshot
   :width: 100%

.. literalinclude:: ../../mytk/example_apps/jsoncanvas_app.py
   :language: python
   :linenos:

lensviewer_app.py
-----------------

**Catalogue viewer for optical lenses.**

A TableView of lens specifications (from the raytracing package) drives matplotlib
Figures showing the ray-trace diagram and focal-shift dispersion of the selected
lens, via the TableView delegate pattern.

Needs the optional ``raytracing`` package.

Run it with ``python -m mytk.example_apps.lensviewer_app``.

.. image:: /_static/examples/lensviewer_app.png
   :alt: lensviewer_app.py screenshot
   :width: 100%

.. literalinclude:: ../../mytk/example_apps/lensviewer_app.py
   :language: python
   :linenos:

microscope_app.py
-----------------

**Live webcam microscope viewer.**

Wraps a VideoView with camera controls — zoom, exposure and gain — using two-way
property binding (Sliders and an IntEntry to the VideoView) and a live histogram,
plus VideoView's built-in start/save/stream buttons.

Needs a connected camera (device 0) and a VideoView backend (e.g. OpenCV).

Run it with ``python -m mytk.example_apps.microscope_app``.

.. note::
   Screenshot not yet available — regenerate with ``make example-shots``.

.. literalinclude:: ../../mytk/example_apps/microscope_app.py
   :language: python
   :linenos:

powermeter_app.py
-----------------

**Power-meter readout and logging panel.**

Streams readings into an XYPlot (live append), shows status via BooleanIndicator,
and binds device state to Slider/LabelledEntry controls with an event-driven update
loop. Runs in a debug/simulation mode when no hardware is present.

Run it with ``python -m mytk.example_apps.powermeter_app``.

.. image:: /_static/examples/powermeter_app.png
   :alt: powermeter_app.py screenshot
   :width: 100%

.. literalinclude:: ../../mytk/example_apps/powermeter_app.py
   :language: python
   :linenos:

progressbar_app.py
------------------

**Demonstrates three ways to update a ProgressBar in myTk.**

1. Direct value assignment:         bar.value = 50
2. Model binding:                   model.bind_property_to_widget_value("progress", bar)
3. NotificationCenter notification: NotificationCenter().post_notification(...)

Run it with ``python -m mytk.example_apps.progressbar_app``.

.. image:: /_static/examples/progressbar_app.png
   :alt: progressbar_app.py screenshot
   :width: 100%

.. literalinclude:: ../../mytk/example_apps/progressbar_app.py
   :language: python
   :linenos:

pydatagraph_app.py
------------------

**Plot tabular data with a per-column style inspector.**

Loads CSV/Excel into a TableView (with drag-and-drop) and plots columns on an XYPlot,
with an inspector to set each column's marker, colour and line style live. Built on
TabularData with pandas-backed import.

Needs ``pandas`` to load files; a CSV/Excel file (e.g. ``test-excel.xlsx``) to plot.

Run it with ``python -m mytk.example_apps.pydatagraph_app``.

.. image:: /_static/examples/pydatagraph_app.png
   :alt: pydatagraph_app.py screenshot
   :width: 100%

.. literalinclude:: ../../mytk/example_apps/pydatagraph_app.py
   :language: python
   :linenos:

svgviewer_app.py
----------------

**Minimal SVG viewer.**

Opens a window with an `SVGImage`. Pass an SVG file on the command line, drag an
`.svg` file onto the viewer, or click "Load…" to open one. A built-in sample is
shown when no file is given.

    python -m mytk.example_apps.svgviewer_app [path/to/drawing.svg]

`SVGImage` rasterizes the document with the `resvg` engine (full SVG support,
including text, gradients and clipping) and rescales to fill the window. See
`mytk.images.SVGImage`.

Run it with ``python -m mytk.example_apps.svgviewer_app``.

.. image:: /_static/examples/svgviewer_app.png
   :alt: svgviewer_app.py screenshot
   :width: 100%

.. literalinclude:: ../../mytk/example_apps/svgviewer_app.py
   :language: python
   :linenos:

view3d_app.py
-------------

**Minimal 3D mesh viewer.**

Opens a window with a `View3D`. Pass a mesh file on the command line, drag a
mesh file onto the viewer, or click "Load…" to open a GLB/GLTF/OBJ/PLY file.
Drag to orbit, scroll to zoom.

    python -m mytk.example_apps.view3d_app [path/to/scene.glb]

Run it with ``python -m mytk.example_apps.view3d_app``.

.. image:: /_static/examples/view3d_app.png
   :alt: view3d_app.py screenshot
   :width: 100%

.. literalinclude:: ../../mytk/example_apps/view3d_app.py
   :language: python
   :linenos:

