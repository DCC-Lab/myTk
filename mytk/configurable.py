"""Configurable --- easy settings management with automatic dialog generation.

========================================================================

Scientific instruments and applications almost always have parameters that
need to be adjusted by the user: exposure time, gain, wavelength, threshold
values, file paths, and so on.  Managing those parameters by hand is
tedious: you have to store each value somewhere, write code to check that
the user has not entered something impossible (a negative exposure time, a
wavelength outside the detector range), and build a dialog box so the user
can change the settings interactively.

This module takes care of all of that for you.

The basic idea
--------------
You describe each parameter once — its name, its type, its allowed range,
and a sensible default — and the framework handles validation, correction of
bad values, and the dialog window automatically.

There are two ways to use it.  The simple, recommended way is to inherit
from ``Configurable`` and declare parameters as class attributes:

    from mytk import App, Configurable, ConfigurableNumericProperty

    class Microscope(Configurable):
        exposure_time = ConfigurableNumericProperty(
            default_value  = 100,
            min_value      = 1,
            max_value      = 10000,
            displayed_name = "Exposure time (ms)")

        gain = ConfigurableNumericProperty(
            default_value  = 1.0,
            min_value      = 0.1,
            max_value      = 16.0,
            displayed_name = "Gain")

    scope = Microscope()

    # Read and write parameters like ordinary Python attributes.
    scope.exposure_time = 500
    print(scope.exposure_time)   # 500

    # Show a settings dialog.  The user edits the values and clicks Ok;
    # the new values are applied to the object automatically.
    scope.show_config_dialog(title="Microscope settings")

    # Get all current values at once as a plain dict.
    print(scope.values)   # {'exposure_time': 500, 'gain': 1.0}

Values are always kept valid.  If you accidentally assign a value outside
the allowed range it is silently clamped to the nearest boundary:

    scope.exposure_time = 99999   # stored as 10000 (the maximum)
    scope.exposure_time = -5      # stored as 1     (the minimum)

The second way — ``ConfigModel`` — is for situations where you need to
build the list of parameters programmatically rather than at class
definition time.  Both approaches use the same ``ConfigurableProperty``
building blocks and produce the same dialog.

Available property types
------------------------
``ConfigurableNumericProperty``
    For numbers (integers or floats).  You can set a minimum, maximum,
    a display multiplier, and a format string for the dialog.

``ConfigurableStringProperty``
    For text values.  You can restrict accepted values with a regular
    expression or a fixed set of allowed strings.

``ConfigurableProperty``
    The base class.  Use this when the built-in types do not fit; you
    can supply any validation function you like via ``validate_fct``.
"""

import numbers
import re
from typing import Any

from mytk.dialog import Dialog
from mytk.entries import Entry
from mytk.labels import Label


def is_numeric(value) -> bool:
    """Check whether a value is a real number."""
    return isinstance(value, numbers.Real)

class ConfigurableProperty:
    """Descriptor that defines a single configurable parameter with validation.

    Instances can be declared as class attributes on a ``Configurable`` subclass
    (descriptor-based approach) or collected into a ``ConfigModel`` for dynamic
    schema construction.
    """

    # name is optional so that when a property is declared as a class attribute
    # (the descriptor-based approach), Python supplies the name automatically via
    # __set_name__.  Existing code that passes name= explicitly still works.

    def __init__(self, name=None, default_value=None, displayed_name=None,
                 validate_fct=None, valid_set=None, value_type=None):
        self.name = name
        self.default_value = default_value
        self.displayed_name = displayed_name
        self.validate_fct = validate_fct
        self.valid_set = valid_set
        self.value_type = value_type
        self._validate()

    def _validate(self):
        # Infer value_type from the default when not given explicitly.
        if self.value_type is None and self.default_value is not None:
            self.value_type = type(self.default_value)

        if self.default_value is not None and not self.is_valid(self.default_value):
            raise ValueError(f"Default value {self.default_value} is not valid for this type of property {type(self)}")

        for value in self.valid_set or []:
            if value is not None and not self.is_valid(value):
                raise ValueError(f"Value {value} is not valid for this type of property {type(self)}")

    # ------------------------------------------------------------------
    # Descriptor protocol
    #
    # These three methods turn ConfigurableProperty instances into
    # descriptors so they can be declared as class attributes:
    #
    #   class Camera(Configurable):
    #       exposure_time = ConfigurableNumericProperty(default_value=100)
    #
    # Python calls __set_name__ once at class-creation time so the
    # descriptor knows which attribute name it was bound to, and where
    # to store per-instance values.  Values are stored on the INSTANCE
    # under a private key (_cfgprop_<attr>) so that each instance has
    # its own independent copy and descriptors are never shared state.
    # ------------------------------------------------------------------

    def __set_name__(self, owner, attr_name):
        # If name was not given explicitly, derive it from the attribute name.
        if self.name is None:
            self.name = attr_name
        # Storage key on the instance dict.  Always based on the attribute
        # name, not self.name, so two classes can use the same property
        # type without colliding in __dict__.
        self._attr_name = f"_cfgprop_{attr_name}"

    def __get__(self, obj, objtype=None):
        if obj is None:
            # Accessed on the class itself (e.g. Camera.exposure_time).
            # Return the descriptor so callers can inspect its metadata.
            return self
        attr = getattr(self, '_attr_name', None)
        if attr is None:
            # Descriptor was never attached to a class via __set_name__
            # (e.g. created standalone for ConfigModel).  Nothing to fetch.
            return self.default_value
        return obj.__dict__.get(attr, self.default_value)

    def __set__(self, obj, value):
        attr = getattr(self, '_attr_name', None)
        if attr is None:
            raise AttributeError(
                f"Property '{self.name}' has not been attached to a class. "
                "Ensure it is declared as a class attribute on a Configurable subclass."
            )
        # Sanitize on assignment: type-cast and clamp rather than raising,
        # consistent with the rest of the framework's tolerant-input philosophy.
        obj.__dict__[attr] = self.sanitize(value)

    # ------------------------------------------------------------------
    # Validation and sanitization
    # ------------------------------------------------------------------

    def is_in_valid_set(self, value: Any) -> bool:
        """Return True if value belongs to the valid set, or if no set is defined."""
        if self.valid_set is None:
            return True

        return value in self.valid_set

    def is_valid_type(self, value: Any) -> bool:
        """Return True if value matches the expected type."""
        expected_type = self.value_type

        if expected_type is None or expected_type is Any:
            return True

        return isinstance(value, expected_type)

    def is_valid(self, value: Any) -> bool:
        """Return True if value passes all validation checks."""
        if not self.is_valid_type(value):
            return False
        if not self.is_in_valid_set(value):
            return False
        return not self.validate_fct or self.validate_fct(value)

    def sanitize(self, value) -> Any:
        """Coerce value to the expected type, falling back to the default on failure."""
        if value is None:
            value = self.default_value

        if self.value_type not in (None, Any):
            if isinstance(value, self.value_type):
                return value

            if not self.is_valid_type(value):
                try:
                    value = self.value_type(value)
                except (ValueError, TypeError):
                    value = self.default_value

        return value


class ConfigurableStringProperty(ConfigurableProperty):
    """String-typed configurable property with optional regex validation."""

    def __init__(self, valid_regex=None, name=None, default_value=None,
                 displayed_name=None, validate_fct=None, valid_set=None):
        # valid_regex must be set before super().__init__() because _validate()
        # calls self.is_valid(), which calls the regex check.
        self.valid_regex = valid_regex
        # value_type is always str for this class; not exposed as a parameter.
        super().__init__(name=name, default_value=default_value,
                         displayed_name=displayed_name, validate_fct=validate_fct,
                         valid_set=valid_set, value_type=str)

    def is_valid(self, value: str) -> bool:
        """Return True if the string passes base validation and matches the regex."""
        if not super().is_valid(value):
            return False

        return re.search(self.valid_regex or ".*", value) is not None

class ConfigurableNumericProperty(ConfigurableProperty):
    """Numeric configurable property with range clamping and optional formatting."""

    def __init__(self, min_value=float("-inf"), max_value=float("+inf"),
                 multiplier=1, format_string=None,
                 name=None, default_value=None, displayed_name=None,
                 validate_fct=None, valid_set=None, value_type=None):
        # Range fields must be set before super().__init__() because _validate()
        # calls self.is_valid(), which calls is_in_valid_range().
        self.min_value = min_value
        self.max_value = max_value
        self.multiplier = multiplier
        self.format_string = format_string
        super().__init__(name=name, default_value=default_value,
                         displayed_name=displayed_name, validate_fct=validate_fct,
                         valid_set=valid_set, value_type=value_type)

    def is_valid_type(self, value: Any) -> bool:
        """Return True if value is numeric or matches the explicit type."""
        # When no explicit type is given, require any numeric value rather
        # than accepting arbitrary Python objects.
        if self.value_type is Any:
            return True
        if self.value_type is None:
            return is_numeric(value)
        return isinstance(value, self.value_type)

    def is_in_valid_range(self, value: Any) -> bool:
        """Return True if value falls within the allowed min/max range."""
        try:
            return self.min_value <= value <= self.max_value
        except TypeError:
            return False

    def is_valid(self, value: Any) -> bool:
        """Return True if value passes type, set, and range validation."""
        if not super().is_valid(value):
            return False
        return self.is_in_valid_range(value)

    def sanitize(self, value) -> Any:
        """Coerce and clamp value to the allowed numeric range."""
        value = super().sanitize(value)

        if is_numeric(value) and not self.is_in_valid_range(value):
            if value < self.min_value:
                value = self.min_value
            elif value > self.max_value:
                value = self.max_value

        return value

    @staticmethod
    def int_property_list(keys:list[str]):
        """Build a list of integer properties from the given key names."""
        properties = []
        for key in keys:
            properties.append(ConfigurableNumericProperty(name=key, value_type=int))

        return properties


# ----------------------------------------------------------------------
# Configurable — descriptor-based mixin
#
# Inherit from this to declare configurable properties directly as class
# attributes.  No constructor boilerplate required:
#
#   class Camera(Configurable):
#       exposure_time = ConfigurableNumericProperty(
#           default_value=100, min_value=0, max_value=1000,
#           displayed_name="Exposure time (ms)")
#       gain = ConfigurableNumericProperty(
#           default_value=3, min_value=0, max_value=100,
#           displayed_name="Gain")
#
#   cam = Camera()
#   cam.exposure_time = 200           # direct attribute access, sanitized
#   cam.show_config_dialog()          # auto-generated dialog from schema
#   print(cam.values)                 # {'exposure_time': 200, 'gain': 3}
#
# Compare with the explicit-list style (ConfigModel below), which is
# still available for cases where the schema is built dynamically.
# ----------------------------------------------------------------------

class Configurable:
    """Mixin that turns declared ConfigurableProperty attributes into a managed configuration."""

    @classmethod
    def _configurable_properties(cls) -> dict[str, ConfigurableProperty]:
        """Return all ConfigurableProperty descriptors declared on this class hierarchy.

        Subclass definitions take precedence over parent definitions for the
        same attribute name.
        """
        props = {}
        # reversed MRO goes from object → ... → cls, so later (more
        # specific) assignments overwrite earlier (more general) ones.
        for klass in reversed(cls.__mro__):
            for attr_name, attr_val in vars(klass).items():
                if isinstance(attr_val, ConfigurableProperty):
                    props[attr_name] = attr_val
        return props

    @property
    def values(self) -> dict:
        """Return all current configurable values as a plain dict."""
        return {name: getattr(self, name)
                for name in self._configurable_properties()}

    def update_values(self, new_values: dict):
        """Apply a possibly partial dict of new values.

        Each value is sanitized by its property descriptor on assignment.
        """
        for key, value in new_values.items():
            setattr(self, key, value)

    def is_valid(self, values: dict) -> dict:
        """Return a per-key dict of booleans indicating validity per property schema."""
        props = self._configurable_properties()
        return {k: props[k].is_valid(v) for k, v in values.items()}

    def all_valid(self, values: dict) -> bool:
        """Return True only if every value in the dict passes its schema."""
        return all(self.is_valid(values).values())

    def show_config_dialog(self, title="Configuration", **kwargs):
        """Show a modal configuration dialog built from declared properties.

        If the user clicks Ok the values are applied back to self via
        ``update_values()``.  Extra keyword arguments are forwarded to
        ``ConfigurationDialog`` (e.g. *buttons_labels*, *auto_click*,
        *geometry*).
        """
        props = list(self._configurable_properties().values())
        dialog = ConfigurationDialog(
            properties=props,
            values=self.values,   # seed dialog with current values
            title=title,
            **kwargs
        )
        reply = dialog.run()
        if reply == Dialog.Replies.Ok:
            self.update_values(dialog.values)
        return reply


# ----------------------------------------------------------------------
# ConfigModel — explicit-list style (backward-compatible)
#
# Useful when the schema is constructed dynamically rather than declared
# at class definition time.
#
# To show a dialog, create the properties, build a ConfigurationDialog,
# and call run().  If the user clicked Ok, read the updated values back
# from dialog.values:
#
#   exposure = ConfigurableNumericProperty(
#       name="exposure_time", displayed_name="Exposure time (ms)",
#       default_value=100, min_value=1, max_value=10000)
#   gain = ConfigurableNumericProperty(
#       name="gain", displayed_name="Gain",
#       default_value=1.0, min_value=0.1, max_value=16.0)
#
#   dialog = ConfigurationDialog(
#       properties=[exposure, gain],
#       title="Microscope settings",
#       buttons_labels=["Ok", "Cancel"])
#   reply = dialog.run()
#
#   if reply == Dialog.Replies.Ok:
#       print(dialog.values)   # {'exposure_time': ..., 'gain': ...}
#
# If you are using the Configurable mixin instead, you do not need
# ConfigurationDialog directly — call scope.show_config_dialog() and
# the values are applied back to the object automatically.
# ----------------------------------------------------------------------

class ConfigModel:
    """Explicit-list configuration model for dynamically built property schemas."""

    def __init__(self, properties:list[ConfigurableProperty] = None, values:dict = None):
        self.properties = { pd.name:pd  for pd in properties or []}
        self._values = { pd.name:pd.default_value  for pd in properties or []}
        if values is not None:
            self.update_values(values)

    @property
    def values(self):
        """Return the current configuration values as a dict."""
        return self._values

    @values.setter
    def values(self, new_values):
        if self.all_valid(new_values):
            self._values.update(new_values)
        else:
            invalid = [k for k, v in self.is_valid(new_values).items() if not v]
            raise ValueError(f"Invalid values for keys: {invalid}")

    def update_values(self, new_values):
        """Set new configuration values after validation."""
        self.values = new_values

    def all_valid(self, values) -> bool:
        """Return True only if every value passes its property validation."""
        return all(self.is_valid(values).values())

    def is_valid(self, values):
        """Return a per-key dict of booleans indicating which values are valid."""
        is_valid = {}
        for key, value in values.items():
            property = self.properties[key]
            is_valid[key] = property.is_valid(value)
        return is_valid

    def sanitize(self, values):
        """Return a dict of values coerced to valid types by their properties."""
        sanitized_values = {}
        for key, value in values.items():
            property = self.properties[key]
            sanitized_values[key] = property.sanitize(value)

        return sanitized_values


class ConfigurationDialog(Dialog, ConfigModel):
    """Modal dialog that presents configurable properties as editable fields."""

    def __init__(self, properties=None, values=None, populate_body_fct=None, *args, **kwargs):
        # values= lets callers seed the dialog with specific starting values
        # rather than always starting from property defaults.  This is what
        # Configurable.show_config_dialog() uses to pass the object's current
        # state into the dialog before it opens.
        super().__init__(*args, **kwargs)
        ConfigModel.__init__(self, properties=properties, values=values)
        self.populate_body_fct = populate_body_fct
        self.configuration_widgets = {}

    def populate_widget_body(self):
        """Create label-entry pairs for each configurable property in the dialog body."""
        if self.populate_body_fct is None:
            for i, (key, value) in enumerate(self.values.items()):
                if key in self.properties:
                    text_label = self.properties[key].displayed_name or key
                    if self.properties[key].displayed_name is not None:
                        text_label = self.properties[key].displayed_name

                    Label(text_label).grid_into(self, row=i, column=0, padx=10, pady=5, sticky="e")
                    entry = Entry(character_width=6)
                    entry.value_variable.set(value)
                    entry.grid_into(self, row=i, column=1, padx=10, pady=5, sticky="w")
                    self.configuration_widgets[key] = entry
        else:
            # Contract: populate_body_fct must populate self.configuration_widgets
            # with {property_name: entry_widget} pairs so that widget_values()
            # can read the entries back when the dialog closes.
            self.populate_body_fct()

    def widget_values(self) -> dict:
        """Read and sanitize current values from the dialog entry widgets."""
        values = {}
        for key, entry_widget in self.configuration_widgets.items():
            values[key] = entry_widget.value_variable.get()

        return self.sanitize(values)

    def run(self):
        """Display the dialog and update values if the user clicks Ok."""
        reply = super().run()

        widget_vals = self.widget_values()
        if widget_vals:
            self.update_values(widget_vals)

        return reply
