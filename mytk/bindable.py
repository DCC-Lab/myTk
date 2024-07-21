from tkinter import Variable, StringVar, BooleanVar


class Bindable:
    def __init__(self):
        self.observing_me = []

    def bind_property_to_widget_value(self, property_name: str, control_widget: "Base"):
        self.bind_properties(
            property_name, control_widget, other_property_name="value_variable"
        )

    def add_observer(self, observer, my_property_name, context=None):
        """
        We observe the property "my_property_name" of self to notifiy if it changes.
        However, we treat Tk.Variable() differently: we do not observe for a change
        in the actual value_variable (i.e. the Variable()): we observe if the Variable() changes
        its value.
        """
        try:
            var = getattr(self, my_property_name)

            self.observing_me.append((observer, my_property_name, context))

            if isinstance(var, Variable):
                var.trace_add("write", self.traced_tk_variable_changed)

        except AttributeError as err:
            raise AttributeError(
                "Attempting to observe inexistent property '{1}' in Bindable object {0}".format(
                    self, my_property_name
                )
            )

    def traced_tk_variable_changed(self, var, index, mode):
        for observer, property_name, context in self.observing_me:
            observed_var = getattr(self, property_name)

            if isinstance(observed_var, Variable):
                if observed_var._name == var:
                    self.property_value_did_change(property_name)

    def bind_properties(self, this_property_name, other_object, other_property_name):
        """
        Binding properties is a two-way synchronization of the properties in two separate
        objects.  Changing one will notify the other, which will be changed, and vice-versa.
        """
        other_object.add_observer(
            self, other_property_name, context={"binding": this_property_name}
        )
        self.add_observer(
            other_object, this_property_name, context={"binding": other_property_name}
        )
        self.property_value_did_change(this_property_name)

    def __setattr__(self, property_name, new_value):
        """
        We always set the property regardless of the value but we notify only if a change occured
        However, we warn if user is overwriting a Tk Variable with something other than a Variable,
        but it is also possible that the property does not exist yet (which is not an error, it
        happens in __init__)
        """

        try:
            if isinstance(getattr(self, property_name), Variable):
                if new_value is not None and not isinstance(new_value, Variable):
                    raise TypeError(
                        f"You are overwriting the Tk Variable '{property_name}' with a non-tk Variable value '{new_value}'"
                    )
        except AttributeError as err:
            pass

        super().__setattr__(property_name, new_value)

        self.property_value_did_change(property_name)

    def property_value_did_change(self, property_name):
        new_value = getattr(self, property_name)  # Assume python property
        if isinstance(new_value, Variable):  # If tk Variable, get its value
            new_value = new_value.get()

        for observer, observed_property_name, context in self.observing_me:
            if observed_property_name == property_name:
                observer.observed_property_changed(
                    self, observed_property_name, new_value, context
                )

    def observed_property_changed(
        self, observed_object, observed_property_name, new_value, context
    ):
        """
        By default, we assume it is a binding and we treat it.
        We set the property (stored in context {'binding':variable_name}) of self to the new_value.
        However, we treat Tk.Variable() differently: we do not change the value_variable (i.e. the Variable())
        but we change its value.
        """
        if isinstance(context, dict):
            bound_variable = context.get("binding")
            if bound_variable is not None:
                old_value = getattr(self, bound_variable)
                if old_value != new_value:
                    var = getattr(self, bound_variable)

                    if isinstance(var, Variable):
                        var.set(new_value)
                    else:
                        self.__setattr__(bound_variable, new_value)
