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
from .draganddropcapable import DragAndDropCapable
from .eventcapable import EventCapable
from .valuecapable import ValueCapable


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


class WidgetNotYetCreatedError(RuntimeError):
    """Raised when a request can only be answered by the real Tk widget.

    myTk creates the underlying Tk widget on placement (grid_into, pack_into,
    place_into). Simple options and states can be set and read before that;
    anything that needs the widget itself raises this error.
    """


class WidgetOption:
    """Descriptor for a Tk configuration option that works before placement.

    Before the Tk widget exists, the value is kept in ``_widget_args`` (and is
    handed to the Tk constructor on creation). Once the widget exists, the
    widget itself is the single source of truth.

    Args:
        tk_name (str): Key used in ``_widget_args``, i.e. the keyword accepted
            by the Tk constructor (``"width"``, ``"from_"``, ``"text"``...).
        default: Value returned before placement if the option was never set.
    """

    def __init__(self, tk_name, default=None):
        self.tk_name = tk_name
        self.default = default

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        if obj.widget is None:
            return obj._widget_args.get(self.tk_name, self.default)
        return obj.widget[self.tk_name.rstrip("_")]

    def __set__(self, obj, value):
        if obj.widget is None:
            obj._widget_args[self.tk_name] = value
        else:
            obj.widget[self.tk_name.rstrip("_")] = value


class WidgetState:
    """Descriptor for a ttk state flag that works before placement.

    Before the Tk widget exists, the requested state is kept in
    ``_pending_states`` and applied by ``_create_and_setup_widget`` right after
    creation. Once the widget exists, the widget is the single source of truth.

    Args:
        name (str): The ttk state name (``"disabled"``, ``"selected"``...).
    """

    def __init__(self, name):
        self.name = name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        if obj.widget is None:
            return obj._pending_states.get(self.name, False)
        return obj.widget.instate([self.name])

    def __set__(self, obj, value):
        if obj.widget is None:
            obj._pending_states[self.name] = bool(value)
        elif value:
            obj.widget.state([self.name])
        else:
            obj.widget.state(["!" + self.name])


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
        self._pending_states = {}
        self._background_color = None

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

    @staticmethod
    def view_for(widget):
        """Return the mytk View that owns this tkinter widget, or None."""
        return getattr(widget, "mytk_view", None)

    def _widget_is_alive(self):
        """Whether the Tk widget has been created and not destroyed since."""
        if self.widget is None:
            return False
        try:
            return bool(self.widget.winfo_exists())
        except Exception:
            return False  # the whole Tk application is gone

    def _create_and_setup_widget(self, master):
        """Create the Tk widget and apply everything requested before it existed.

        This is the single point through which a widget comes to life: the
        placement methods (grid_into, pack_into, place_into) and Dialog.run()
        all go through it. Subclasses override ``create_widget``, never this.

        Args:
            master (tk.Widget): The Tk parent of the widget to create.

        Raises:
            RuntimeError: If the widget already exists (placing a widget twice
                would silently create a second Tk widget).
        """
        if self._widget_is_alive():
            raise RuntimeError(
                f"{_class_nice_(self)} is already placed: a widget can only be "
                "created once. Create a new object to place it elsewhere."
            )

        # A widget destroyed since its creation is created anew: forget the dead
        # Tk widget first, so options are read from the remembered arguments
        # again instead of from a widget that no longer exists.
        self.widget = None

        self.create_widget(master=master)
        if self.widget is not None:
            # Stamp the owner on the Tk widget, for Base.view_for().
            self.widget.mytk_view = self
        self._apply_pending_states()
        self._bind_destroy_cancel()
        self._apply_background_color()

    def _apply_pending_states(self):
        """Apply the ttk states requested before the widget existed."""
        if self.widget is None:
            return
        for name, value in self._pending_states.items():
            with contextlib.suppress(Exception):  # classic Tk widgets have no state()
                self.widget.state([name if value else "!" + name])
        self._pending_states = {}

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

        if widget is None:
            widget = parent.widget
        self._create_and_setup_widget(master=widget)

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
        self._create_and_setup_widget(master=parent.widget)
        self.parent = parent

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
        self._create_and_setup_widget(master=parent.widget)
        self.parent = parent

        if self.widget is not None:
            self.widget.place(x=x, y=y, width=width, height=height)

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

    is_disabled = WidgetState("disabled")
    """Whether the widget is disabled (grayed out). Can be set before placement."""

    is_selected = WidgetState("selected")
    """Whether the widget is in the 'selected' state. Can be set before placement."""

    @property
    def has_focus(self):
        """Whether the widget currently has focus (always False before placement)."""
        if self.widget is None:
            return False
        self.widget.update()
        return self.widget.instate(["focus"])

    @has_focus.setter
    def has_focus(self, value):
        if self.widget is None:
            raise WidgetNotYetCreatedError(
                "Focus can only be changed once the widget has been placed on "
                "screen. myTk creates the widget upon placement."
            )
        if value:
            self.widget.state(["focus"])
        else:
            self.widget.state(["!focus"])

    width = WidgetOption("width")
    """The widget width. Can be set before placement."""

    height = WidgetOption("height")
    """The widget height. Can be set before placement."""

    @property
    def background_color(self):
        """The widget's background color (a Tk color name or ``#rrggbb`` string).

        Set this to recolor the widget's background. The value is remembered even
        before the widget exists (myTk creates widgets on placement) and is
        applied as soon as it is created.

        How it is applied depends on the kind of underlying widget:

        - **Classic Tk widgets** (e.g. the ``Canvas`` behind ``CanvasView`` and
          the indicators) honor it directly, including the focus-highlight
          border, so the whole widget takes the color.
        - **Themed ttk widgets** (``View``/``Box`` and most controls) get a
          private ``ttk.Style`` configured with this background. This works on
          the *clam*/*default*/*classic* themes (Linux, Windows). The macOS
          **aqua** theme draws frames natively and ignores a style background,
          so setting it on a ``View``/``Box`` has no visible effect there — set
          it on the classic widget that sits on top (e.g. an indicator) instead.

        Returns:
            str | None: The configured color, or None if never set.
        """
        return self._background_color

    @background_color.setter
    def background_color(self, value):
        self._background_color = value
        self._apply_background_color()

    def _apply_background_color(self):
        """Apply ``background_color`` to the underlying widget, if both exist.

        Called by the setter and by the placement methods (grid/pack/place)
        once the widget has been created. No-op when either is missing.
        """
        import tkinter.ttk as ttk

        color = self._background_color
        if color is None or self.widget is None:
            return

        if isinstance(self.widget, ttk.Widget):
            # Themed widgets don't take a -background option; route it through a
            # private style derived from the widget's own class (e.g. TFrame).
            base_class = self.widget.winfo_class()
            style_name = f"bg{id(self):x}.{base_class}"
            ttk.Style().configure(style_name, background=color)
            with contextlib.suppress(Exception):
                self.widget.configure(style=style_name)
        else:
            # Classic widgets take -background directly; also recolor the
            # focus-highlight border so it blends instead of framing a square.
            with contextlib.suppress(Exception):
                self.widget.configure(background=color)
            with contextlib.suppress(Exception):
                self.widget.configure(highlightbackground=color)

    def _inherited_background_color(self):
        """Best-effort effective background color of this widget's container.

        Used to blend a classic widget (e.g. the ``Canvas`` behind an indicator)
        into whatever themed container holds it, instead of showing a lighter
        square. Returns a Tk color *name* whenever possible so the result stays
        correct when the system appearance changes (light/dark mode).

        - A **classic** parent reports its real background via ``-background``.
        - On macOS **aqua**, ttk reports ``systemWindowBackgroundColor`` for both
          a plain ``Frame`` and a ``LabelFrame``, even though aqua draws each
          nested group box one shade darker. macOS exposes that scale as the
          dynamic colors ``systemWindowBackgroundColor`` (level 0),
          ``systemWindowBackgroundColor1`` (level 1), … so we recover the right
          shade by counting enclosing ``ttk.LabelFrame`` ancestors.
        - On other themes a ttk parent honors its style background, so we use it.

        Returns:
            str | None: A color name/value, or None if it cannot be determined.
        """
        import tkinter.ttk as ttk
        from tkinter import TclError

        if self.widget is None:
            return None
        try:
            parent = self.widget.nametowidget(self.widget.winfo_parent())
        except Exception:
            return None

        # Classic containers expose their rendered background directly.
        try:
            return parent.cget("background")
        except TclError:
            pass  # themed widget: no -background option

        try:
            root = self.widget.winfo_toplevel()
            if self.widget.tk.call("tk", "windowingsystem") == "aqua":
                level, node = 0, parent
                while True:
                    if node.winfo_class() == "TLabelframe":
                        level += 1
                    if node == root:
                        break
                    node = node.nametowidget(node.winfo_parent())
                if level == 0:
                    return "systemWindowBackgroundColor"
                return f"systemWindowBackgroundColor{min(level, 7)}"
            style_name = parent.cget("style") or parent.winfo_class()
            return ttk.Style().lookup(style_name, "background") or None
        except Exception:
            return None

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


class Base(_BaseWidget, Bindable, EventCapable, DragAndDropCapable):
    """Composite base class combining widget management, binding, event, and
    drag-and-drop capabilities."""

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

    def _adopt_value_variable(self, variable):
        """Make ``variable`` this widget's value variable, if it is not already."""
        if variable is self.value_variable:
            return
        if isinstance(self, ValueCapable):
            self.use_value_variable(variable)
        else:
            self.value_variable = variable

    value_variable_option = "variable"
    """Name of the tk widget option that takes the value variable: "variable"
    (Checkbutton, Radiobutton, Scale) or "textvariable" (Label, Button, Entry,
    Spinbox, Menubutton). Subclasses set it once at class level."""

    def attach_value_variable_to_widget(self):
        """Makes the tk widget display and edit ``self.value_variable``.

        Called from ``create_widget`` once the tk widget exists: until then,
        ``value_variable`` holds the value but no widget is connected to it.
        """
        if self.widget is not None:
            self.widget.configure(
                **{self.value_variable_option: self.value_variable}
            )
            self.widget.update()

    def bind_textvariable(self, variable):
        """Replaces ``value_variable`` and attaches it as the widget's textvariable.

        To attach the widget's own ``value_variable``, use
        ``attach_value_variable_to_widget()``.

        Args:
            variable (tk.Variable): The variable to bind (e.g., StringVar).
        """
        if self.widget is not None:
            self._adopt_value_variable(variable)
            self.widget.configure(textvariable=variable)
            self.widget.update()

    def bind_variable(self, variable):
        """Replaces ``value_variable`` and attaches it as the widget's variable.

        Use this to make a widget use a variable created elsewhere, for
        instance one shared by a group of radio buttons. To attach the
        widget's own ``value_variable``, use
        ``attach_value_variable_to_widget()``.

        Args:
            variable (tk.Variable): The variable to bind (e.g., BooleanVar, IntVar).
        """
        if self.widget is not None:
            self._adopt_value_variable(variable)
            self.widget.configure(variable=variable)
            self.widget.update()
