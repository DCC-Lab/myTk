"""Base module for custom Tkinter widget behavior.

This module defines a `Base` class that extends `Bindable` to provide a
unified interface for managing Tkinter widget state, dynamic geometry placement,
event binding, and lifecycle scheduling.

Includes support for property observation, variable binding, and diagnostic output.
"""
import contextlib
import re
from enum import Enum

from .bindable import Bindable
from .eventcapable import EventCapable


def _class_nice_(cls):
    """Returns a nicely formatted class name string for debugging or introspection.

    Args:
        cls: An instance whose class name should be extracted.

    Returns:
        str: The class name as a string, without module prefix.
    """
    full_name = str(cls.__class__)
    match = re.search("'(.*?)'", full_name)
    if match is not None:
        return match.group(1).split(".")[-1]


class BaseNotification(Enum):
    """Enum for core notification messages emitted by Base-derived classes."""

    did_resize = "did_resize"


class _BaseWidget:
    """Abstract base class for all UI related methods in the framework.

    Provides:
    - Tkinter state management (enabled, selected, focused)
    - Layout control (size, grid, pack, place)
    - Diagnostic debug support

    Event-related methods are in EventCapable and binding-related methods are in Bindable.
    They are all combined into Base.
    """

    debug = False

    def __init__(self, *args, **kwargs):
        """Initializes the widget base with properties and environment validation."""
        super().__init__(*args, **kwargs)
        self.widget = None
        self.parent = None
        self.value_variable = None
        self._widget_args = {}

        self._grid_kwargs = None
        self.is_environment_valid()

    def create_widget(self, master, **kwargs):
        """Actually create the widget as needed.

        Subclasses must override this method to create self.widget.
        As a convention, call self._bind_destroy_cancel() at the end of your
        implementation so that any scheduled after() tasks are automatically
        cancelled when the widget is destroyed. The placement methods
        (grid_into, pack_into, place_into) also call it as a safety net.
        """
        raise NotImplementedError(
            "You must override create_widget in your class to create the widget"
        )

    def _bind_destroy_cancel(self):
        """No-op fallback. Overridden by EventCapable when present in the MRO."""
        pass

    """
    Placing widgets in other widgets
    """

    def add_rows(self, elements, start_row, column, **kwargs):
        """Adds several elements in a column with similar grid settings."""
        for i, element in enumerate(elements):
            element.grid_into(self, row=start_row + i, column=column, **kwargs)

    # Maps the high-level `fill` shortcut to (sticky, grow_column, grow_row).
    # Making a widget resize needs two things that must agree: `sticky` on the
    # child (fill the cell) and `weight` on the parent's row/column (grow the
    # cell). `fill` sets both at once. e/w are horizontal (width → column);
    # n/s are vertical (height → row).
    _FILL_MAP = {
        True: ("nsew", True, True),
        "both": ("nsew", True, True),
        "x": ("ew", True, False),
        "width": ("ew", True, False),
        "y": ("ns", False, True),
        "height": ("ns", False, True),
    }

    def grid_into(
        self, parent=None, widget=None, fill=None, describe=False, **kwargs
    ):
        """Places the widget into a grid layout.

        Args:
            parent (Base): Parent widget wrapper.
            widget (tk.Widget): Optional target widget.
            fill: High-level resize shortcut. Sets both the child's `sticky`
                and the parent row/column `weight` so the widget actually grows
                with the window. One of: ``True``/``"both"`` (fill and grow in
                both directions), ``"x"``/``"width"`` (horizontal only),
                ``"y"``/``"height"`` (vertical only), or ``None`` (default, no
                automatic resizing). Cannot be combined with an explicit
                ``sticky``. The parent weight is only set when it is currently
                0, so explicit proportional weights are preserved.
            describe (bool): If True, prints diagnostics about layout and geometry.
            **kwargs: Grid options (row, column, sticky, etc.)
        """
        self.parent = parent
        self.parent_grid_cell = {
            "row": kwargs.get("row", 0),
            "column": kwargs.get("column", 0),
        }
        self._grid_kwargs = kwargs

        grow_column = grow_row = False
        if fill is not None:
            if "sticky" in kwargs:
                raise ValueError(
                    "Use either fill=... or sticky=..., not both: fill sets "
                    "sticky and the parent row/column weight together."
                )
            key = fill.lower() if isinstance(fill, str) else fill
            try:
                fill_sticky, grow_column, grow_row = Base._FILL_MAP[key]
            except (KeyError, TypeError):
                raise ValueError(
                    f"Invalid fill={fill!r}. Use True/'both', 'x'/'width', "
                    f"or 'y'/'height'."
                )
            kwargs["sticky"] = fill_sticky

        if widget is not None:
            self.create_widget(master=widget)
        else:
            self.create_widget(master=parent.widget)
            widget = parent.widget

        self._bind_destroy_cancel()

        column = 0
        if "column" in kwargs:
            column = kwargs["column"]

        row = 0
        if "row" in kwargs:
            row = kwargs["row"]

        sticky = ""
        if "sticky" in kwargs:
            sticky = kwargs["sticky"].lower()

        if self.widget is not None:
            self.widget.grid(kwargs)

        # `widget` is the parent/master container here. Give its row/column the
        # weight implied by `fill` so the cell (and thus the child) grows with
        # available space. Only set it when unset, to keep explicit weights.
        if grow_column and widget.grid_columnconfigure(column)["weight"] == 0:
            widget.grid_columnconfigure(column, weight=1)
        if grow_row and widget.grid_rowconfigure(row)["weight"] == 0:
            widget.grid_rowconfigure(row, weight=1)

        if describe or Base.debug:
            try:
                print(
                    f"\nPlacing widget {_class_nice_(self)} into {_class_nice_(parent)}.grid({row},{column})"
                )
                # sticky e+w (horizontal) stretches width; n+s (vertical)
                # stretches height. The widget only fills its cell on these axes.
                stretch_width_to_fit = "e" in sticky and "w" in sticky
                stretch_height_to_fit = "n" in sticky and "s" in sticky
                print(
                    f"  Widget stretches to fill its cell (width, height): {stretch_width_to_fit, stretch_height_to_fit}"
                )

                row_weight = parent.widget.grid_rowconfigure(row)["weight"]
                column_weight = parent.widget.grid_columnconfigure(column)[
                    "weight"
                ]

                # The cell only grows with the window when its weight is > 0:
                # column weight governs width, row weight governs height.
                print(
                    f"  Grid cell grows with extra space (width, height): {column_weight != 0, row_weight != 0} (column weight={column_weight}, row weight={row_weight})"
                )
                print(
                    f"  Parent propagates resize to parents: {parent.widget.propagate() != 0}"
                )
                window_geometry = self.widget.winfo_toplevel().geometry()
                print(
                    f"  Top window will resize geometry : {window_geometry!='1x1+0+0'} ({window_geometry})"
                )
                print()
            except Exception as err:
                print(
                    f"Unable to describe widget {_class_nice_(self)} into parent {_class_nice_(parent)}.\n{err}"
                )

    @property
    def grid_size(self):
        """Returns the grid size (columns, rows) of the widget."""
        return self.widget.grid_size()

    def all_resize_weight(self, weight):
        """Applies the same resize weight to all rows and columns of the widget's grid.

        Args:
            weight (int): Resize weight to apply.
        """
        cols, rows = self.grid_size
        for i in range(cols):
            self.column_resize_weight(i, weight)

        for j in range(rows):
            self.row_resize_weight(j, weight)

    def column_resize_weight(self, index, weight):
        """Sets the resize weight for a specific column."""
        self.widget.columnconfigure(index, weight=weight)

    def row_resize_weight(self, index, weight):
        """Sets the resize weight for a specific row."""
        self.widget.rowconfigure(index, weight=weight)

    def grid_propagate(self, value):
        """Controls whether the geometry manager should let children resize the container."""
        self.widget.grid_propagate(value)

    def pack_into(self, parent, **kwargs):
        """Packs the widget into the parent using the pack geometry manager.

        Args:
            parent (Base): Parent widget.
            **kwargs: Pack options.
        """
        self.create_widget(master=parent.widget)
        self.parent = parent
        self._bind_destroy_cancel()

        if self.widget is not None:
            self.widget.pack(kwargs)

    def place_into(self, parent, x, y, width, height):
        """Places the widget into absolute coordinates inside the parent.

        Args:
            parent (Base): Parent widget.
            x (int): X-coordinate.
            y (int): Y-coordinate.
            width (int): Width in pixels.
            height (int): Height in pixels.
        """
        self.create_widget(master=parent.widget)
        self.parent = parent
        self._bind_destroy_cancel()

        if self.widget is not None:
            self.widget.place(x=x, y=y, width=width, height=height)

    def accept_dropped_files(self, callback):
        """Accept files dropped onto this widget from the OS file manager.

        ``callback(paths)`` is invoked on each drop with a list of filesystem
        paths. Call this after the widget exists (e.g. after grid_into /
        pack_into / place_into).

        Returns True if drag-and-drop is available in this environment, or False
        if it could not be enabled — in which case the widget keeps working,
        just without drops. Enabling it pulls in the optional ``tkinterdnd2``
        dependency on first use (see :mod:`mytk.dnd`).
        """
        from .dnd import dropped_paths, ensure_tkdnd

        if self.widget is None:
            raise RuntimeError(
                "accept_dropped_files() needs the widget to exist; place it "
                "(grid_into/pack_into/place_into) first."
            )
        root = self.widget.winfo_toplevel()
        tkdnd = ensure_tkdnd(root)
        if tkdnd is None:
            return False
        self.widget.drop_target_register(tkdnd.DND_FILES)
        self.widget.dnd_bind(
            "<<Drop>>", lambda event: callback(dropped_paths(root, event.data))
        )
        return True

    @property
    def debug_kwargs(self):
        """Returns debug border styling if class-level `debug` is True.

        Returns:
            dict: Widget keyword arguments like borderwidth and relief.
        """
        if Base.debug:
            return {"borderwidth": 2, "relief": "groove"}
        return {}

    def is_environment_valid(self):
        """Validates the runtime environment."""
        return True

    @property
    def is_disabled(self):
        """Whether the widget is currently disabled (grayed out)."""
        if self.widget is None:
            raise Exception(
                "You can only query or change the state once it has been placed on screen. myTk creates the widget upon placement."
            )
        return self.widget.instate(["disabled"])

    @is_disabled.setter
    def is_disabled(self, value):
        if self.widget is None:
            raise Exception(
                "You can only query or change the state once it has been placed on screen. myTk creates the widget upon placement."
            )
        if value:
            self.widget.state(["disabled"])
        else:
            self.widget.state(["!disabled"])

    @property
    def is_selected(self):
        """Whether the widget is currently in the 'selected' state."""
        if self.widget is None:
            raise Exception(
                "You can only query or change the state once it has been placed on screen. myTk creates the widget upon placement."
            )
        return self.widget.instate(["selected"])

    @is_selected.setter
    def is_selected(self, value):
        if self.widget is None:
            raise Exception(
                "You can only query or change the state once it has been placed on screen. myTk creates the widget upon placement."
            )
        if value:
            self.widget.state(["selected"])
        else:
            self.widget.state(["!selected"])

    @property
    def has_focus(self):
        """Whether the widget currently has focus."""
        if self.widget is None:
            raise Exception(
                "You can only query or change the state once it has been placed on screen. myTk creates the widget upon placement."
            )
        self.widget.update()
        return self.widget.instate(["focus"])

    @has_focus.setter
    def has_focus(self, value):
        if self.widget is None:
            raise Exception(
                "You can only query or change the state once it has been placed on screen. myTk creates the widget upon placement."
            )
        if value:
            self.widget.state(["focus"])
        else:
            self.widget.state(["!focus"])

    @property
    def width(self):
        """Gets or sets the widget width."""
        if self.widget is None:
            return self._widget_args.get("width")

        return self.widget["width"]

    @width.setter
    def width(self, value):
        if self.widget is None:
            self._widget_args["width"] = value
        else:
            self.widget["width"] = value

    @property
    def height(self):
        """Gets or sets the widget height."""
        if self.widget is None:
            return self._widget_args.get("height")
        return self.widget["height"]

    @height.setter
    def height(self, value):
        if self.widget is None:
            self._widget_args["height"] = value
        else:
            self.widget["height"] = value

    @property
    def is_enabled(self):
        """Whether the widget is enabled (not disabled)."""
        return not self.is_disabled

    @is_enabled.setter
    def is_enabled(self, value):
        """Enables the widget."""
        self.is_disabled = not value

    def enable(self):
        """Enables the widget."""
        self.is_disabled = False

    def disable(self):
        """Disables the widget."""
        self.is_disabled = True

    def select(self):
        """Marks the widget as selected."""
        self.is_selected = True

    def deselect(self):
        """Unselects the widget."""
        self.is_selected = False

    def keys(self):
        """Prints all configurable options of the underlying widget."""
        print(self.widget.configure().keys())


class Base(_BaseWidget, Bindable, EventCapable):
    """Composite base class combining widget management, binding, and event capabilities."""

    def _propagate_disabled(self, widget, disabled):
        for child in widget.winfo_children():
            try:
                if disabled:
                    child.state(["disabled"])
                else:
                    child.state(["!disabled"])
            except AttributeError:
                with contextlib.suppress(Exception):
                    child.configure(state="disabled" if disabled else "normal")
            self._propagate_disabled(child, disabled)

    def bind_textvariable(self, variable):
        """Binds a textvariable (e.g., StringVar) to the widget.

        Args:
            variable (tk.Variable): The variable to bind.
        """
        if self.widget is not None:
            self.value_variable = variable
            self.widget.configure(textvariable=variable)
            self.widget.update()

    def bind_variable(self, variable):
        """Binds a general-purpose variable (e.g., BooleanVar, IntVar).

        Args:
            variable (tk.Variable): The variable to bind.
        """
        if self.widget is not None:
            self.value_variable = variable
            self.widget.configure(variable=variable)
            self.widget.update()
