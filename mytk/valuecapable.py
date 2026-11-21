"""Value mixin class for widget behavior.

Provides the `ValueCapable` class, a mixin for widgets that hold one value the
user can see or change (a checkbox state, a slider position, the text of an
entry). It gathers in one place what every such widget needs:

- a plain ``value`` property over the widget's Tk ``value_variable``,
- one place to keep the value valid (``sanitize_value``),
- one place to react when it changes (``value_did_change``),
- notification of the observers of ``value``, whoever changed it (the program
  or the user), so that ``value`` can be observed and bound like any property.

Two names, one rule:

- ``value`` is what you read, write, observe and bind:
  ``model.bind_properties("threshold", slider, "value")``.
- ``value_variable`` is the Tk object that holds it. It is only needed to
  connect it to a Tk widget (``bind_variable``, ``bind_textvariable``) or to
  share it between widgets (``use_value_variable``).

Like `EventCapable` and `DragAndDropCapable`, it is combined with `Base` and
never used on its own: it relies on `Bindable` to notify observers.

A widget creates its own Tk variable and hands it over once, in its
constructor, then connects it to the Tk widget in ``create_widget`` exactly as
before::

    class Checkbox(Base, ValueCapable):
        def __init__(self, label=""):
            super().__init__()
            self.use_value_variable(BooleanVar(value=True))

        def create_widget(self, master):
            self.widget = ttk.Checkbutton(master, text=self.label)
            self.bind_variable(self.value_variable)
"""

from contextlib import suppress
from tkinter import TclError


class ValueCapable:
    """Mixin adding a ``value`` property backed by a Tk variable."""

    def __init__(self, *args, **kwargs):
        """Initialize value state for cooperative multiple inheritance."""
        self.value_variable = None
        self._value_trace_id = None
        self._value_is_set_by_property = False
        super().__init__()  # cooperative!

    def use_value_variable(self, variable):
        """Make ``variable`` the Tk variable that holds this widget's value.

        Call it once in the constructor with a new variable (``StringVar``,
        ``DoubleVar``, ``IntVar``, ``BooleanVar``). Calling it again replaces
        the variable, for instance to share one between several widgets.

        Args:
            variable (tk.Variable): The variable holding the value.
        """
        if self.value_variable is not None and self._value_trace_id is not None:
            with suppress(TclError):
                self.value_variable.trace_remove("write", self._value_trace_id)

        self.value_variable = variable
        self._value_trace_id = variable.trace_add(
            "write", self._value_variable_written
        )

    @property
    def value(self):
        """The current value of the widget, as a plain Python value."""
        if self.value_variable is None:
            return None
        return self.value_variable.get()

    @value.setter
    def value(self, new_value):
        # Bindable notifies the observers of `value` right after this setter
        # returns, as it does for any assignment. The flag tells the trace not
        # to notify them a first time while the variable is being written.
        self._value_is_set_by_property = True
        try:
            self.value_variable.set(self.sanitize_value(new_value))
        finally:
            self._value_is_set_by_property = False

    def sanitize_value(self, value):
        """Return the value to actually store when ``value`` is assigned.

        Override to keep the value valid, for instance within a range. The
        default accepts everything.
        """
        return value

    def value_did_change(self, value):
        """Called every time the value changes, whoever changed it.

        Override to react: redraw, update a label, inform a delegate. The
        default does nothing.
        """

    def _value_variable_written(self, *_):
        """Tk calls this whenever the variable is written, by anyone."""
        try:
            value = self.value_variable.get()
        except TclError:
            return  # transient text that is not a value yet, e.g. an empty number entry

        self.value_did_change(value)

        if not self._value_is_set_by_property:
            # The user (or a direct write to the variable) changed the value:
            # the observers of `value` would otherwise never know.
            self.property_value_did_change("value")
