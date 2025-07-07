"""
bindable.py — Property-Observer and Binding Mechanism for Python/Tkinter

This class implements a Property-Value-Observer pattern, which allows objects
to observe changes in specific attributes of other objects. It supports both
traditional Python attributes and Tkinter `Variable` instances, making it
suitable for reactive GUI programming in Tkinter.

It enables:
1. Observing changes in object properties, with optional context.
2. Automatically synchronizing (binding) two properties so that changing one updates the other.

This is inspired by macOS’s Key-Value-Observing (KVO) pattern, and can be used
to build reactive MVC-style architectures in Python/Tkinter applications.

Classes:
    - Bindable: Base class that supports observing and binding properties.

Usage Example:
    class Model(Bindable):
        def __init__(self):
            super().__init__()
            self.name = tk.StringVar()

        def observed_property_changed(self, observed, property_name, new_value, context):
            print(f"{property_name} changed to {new_value}")

    model = Model()
    view = SomeWidget(...)
    model.bind_property_to_widget_value("name", view)

"""

from tkinter import Variable
from collections import namedtuple
from contextlib import suppress

ObserverInfo = namedtuple(
    "ObserverInfo", ["observer", "observed_property_name", "context"]
)


class Bindable:
    """
    A class to 1) observe changes in variables, and possibly 2) bind variables
    together.

    In general, this is called a "one-to-one" pattern because an observer
    registeres specifically for a change in a specific object.  To notify
    one-to-many, use the NotificationCenter.

    It is also called a Property-Value-Observer pattern, identical to the
    Key-Value-Observer pattern on macOS.

    It implements two functionalities:

    1. a callback method to notify a specific object that a change occurred in
    another object.
    2. a binding mechanism so that two properties are always
    synchronized, regardless of which one changed

    """

    def __init__(self, *args, **kwargs):
        """
        We need to assign observing_me before super().__init__()
        because the overriden __setattr__ will be active for subclasses
        in case this is part of a multiple inheritance (it is)
        """
        self.observing_me = []
        super().__init__(*args, **kwargs)  # cooperative!

    def add_observer(self, observer, my_property_name, context=None):
        """
        We observe the property "my_property_name" of self to notifiy if it
        changes.

        When the property "my_property_name" of object "self" changes, the
        method "observed_property_changed" of object "observer" will be
        called. You must implement the following method signature
        in "observer":

        observer.observed_property_changed
        (observed_object, observed_property_name, new_value, context)

        Based on either parameters, you can determine what to do:
        observed_property_name may be sufficient if you have only registered
        the observer for one thing, but you can also provide "context" when
        with anything you want and can be an indicator of what to do
        (e.g., context="object_needs_refresh").

        We treat Tk.Variable() differently. We do not observe for a change in
        the actual value_variable (i.e. the Variable()): we observe if the
        Variable() changes its value.  We really need this to integrate this
        observer pattern with Tk and generalize it to any property. To do so,
        we register à-la-TkVariable with trace_add and redirect the call with
        our observed_property_changed mechanism.
        """

        try:
            var = getattr(self, my_property_name)

            observer_info = ObserverInfo(observer, my_property_name, context)
            self.observing_me.append(observer_info)

            """
            If the property is a regular object property, then __setattr__
            will catch the change and call property_did_change. This is done
            automatically. On the other hand, if the property is a
            Tk.Variable, then we must register using Tk's mechanism (trace_add) to
            observe not the variable itself but when its value is modified.
            """
            if isinstance(var, Variable):
                var.trace_add("write", self.traced_tk_variable_changed)

        except AttributeError as err:
            raise AttributeError(
                f"Attempting to observe inexistent property '{my_property_name}' in Bindable object {self}"
            ) from err

    def __setattr__(self, property_name, new_value):
        """
        Assigns a value to a property and notifies observers if it changed.

        This method overrides the default setattr to automatically trigger
        observer callbacks when a property is modified. If the property is
        a Tkinter Variable, care is taken to avoid accidentally overwriting
        it with a non-variable object, which is typically a mistake.

        We always set the property regardless of the value. It is possible
        that the property does not exist yet (which is not an error, it
        happens in __init__) so we need to cover that case by ignoring
        AttributeError(then the property will be managed in __setattr__ right
        after). Also, we warn if the user is overwriting a Tk Variable with
        something other than a Variable or None, because it is highly likely a mistake.
        """

        with suppress(AttributeError):
            observed_property = getattr(self, property_name)
            if isinstance(observed_property, Variable):
                if new_value is not None and not isinstance(
                    new_value, Variable
                ):
                    raise TypeError(
                        f"You are overwriting the Tk Variable '{property_name}' with a non-tk Variable value '{new_value}'"
                    )

        super().__setattr__(property_name, new_value)

        self.property_value_did_change(property_name)

    # pylint: disable=unused-argument
    def traced_tk_variable_changed(self, var, index, mode):
        """
        This function is called by tk when a Tk.Variable value is changed.

        This is a hook function into our Property-Value-Observing mechanism.
        We do not observe for a change in the actual value_variable (i.e. the
        Variable()): we observe if the tk.Variable() changes its value.  We
        need this to integrate this Property-Observer Pattern with Tk and
        generalize it to any property. To do so, we register à-la-TkVariable
        with trace_add (see above) and call our property_value_did_change
        mechanism.
        """

        for _, property_name, _ in self.observing_me:
            observed_property = getattr(self, property_name)

            if isinstance(observed_property, Variable):
                # pylint: disable=protected-access
                if observed_property._name == var:
                    self.property_value_did_change(property_name)

    def property_value_did_change(self, property_name):
        """
        This is an intermediate method to recover all the parameters of the
        observer (who is observing and what is the context that was provided
        when registering) before calling the observer callback. Again,
        Tk.Variables need special treatment because we are looking at their
        values, not the Tk.Variable object itself.
        """

        new_value = getattr(self, property_name)  # Assume python property
        if isinstance(new_value, Variable):  # If tk Variable, get its value
            new_value = new_value.get()

        if hasattr(self, "observing_me"):
            for observer_info in self.observing_me:
                observer, observed_property_name, context = observer_info
                if observed_property_name == property_name:
                    observer.observed_property_changed(
                        self, observed_property_name, new_value, context
                    )

    def observed_property_changed(
        self, observed_object, observed_property_name, new_value, context
    ):
        """
        This method is called in the observer (not the observed object) when the
        property changed. You implement it in your observer.

        But the binding mechanism uses the same Property-Value-Observing
        mechanism, and we can treat it without having the user do anything.
        Therefore, by default, we check to see if it is a binding, and if it
        is, we treat it, the subclass will not have anything to do. The
        context will be a dictionary and will have the key "binding".  If it
        does not, then it's not a binding and that's it. But if it is, we set
        the property (stored in context{'binding':variable_name}) of self to
        the new_value. Again, we treat Tk.Variable differently: we do not
        change the property that holds the Tk.Variable, we change its
        value.

        If you are using the basic Property-Value-Observing pattern to be
        notified of a change in a property, then your class *needs* to
        override this observed_property_changed() and should perform whatever
        it wants to do based on the context, and then call
        super().observed_property_changed to benefit of property binding management.
        """

        if isinstance(context, dict):
            bound_variable = context.get("binding")
            if bound_variable is not None:
                old_value = getattr(self, bound_variable)
                var = None
                if isinstance(old_value, Variable):
                    var = old_value
                    old_value = var.get()

                if old_value != new_value:
                    if var is not None:
                        var.set(new_value)
                    else:
                        setattr(self, bound_variable, new_value)

    def bind_properties(
        self, this_property_name, other_object, other_property_name
    ):
        """
        Binding properties is a two-way synchronization of the properties in
        two separate objects.  It makes use of the Property-Value-Observing
        mechanism and uses the context to indicate that it is actually "a
        binding".  Changing one property will notify the other, which will be
        changed, and vice-versa.
        """

        other_object.add_observer(
            self, other_property_name, context={"binding": this_property_name}
        )
        self.add_observer(
            other_object,
            this_property_name,
            context={"binding": other_property_name},
        )
        self.property_value_did_change(this_property_name)

    def bind_property_to_widget_value(
        self, property_name: str, control_widget: "Base"
    ):
        """
        Binds an object property to the `value_variable` of a widget-like object.

        The `control_widget` must define a `value_variable` attribute (typically a
        Tkinter Variable) which will remain synchronized with the given property
        of this object. This allows direct model-view bindings in Tkinter.
        """

        self.bind_properties(
            property_name, control_widget, other_property_name="value_variable"
        )
