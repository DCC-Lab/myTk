from typing import Optional, Any, Callable
from dataclasses import dataclass
import numbers
import re
from mytk import Dialog, Label, Entry

def is_numeric(value) -> bool:
    return isinstance(value, numbers.Real)

@dataclass
class ConfigurableProperty:
    name: str
    default_value : Optional[Any] = None
    displayed_name: str = None
    validate_fct : Optional[Callable[[Any], bool]] = None
    valid_set : set | list = None
    value_type: Optional[type] = None

    def __post_init__(self):
        if self.value_type is None and self.default_value is not None:
            self.value_type = type(self.default_value)

        if self.default_value is not None and not self.is_valid(self.default_value):
            raise ValueError(f"Default value {self.default_value} is not valid for this type of property {type(self)}")

        for value in self.valid_set or []:
            if value is not None and not self.is_valid(value):
                raise ValueError(f"Value {value} is not valid for this type of property {type(self)}")

    def is_in_valid_set(self, value: Any) -> bool:
        if self.valid_set is None:
            return True

        return value in self.valid_set

    def is_valid_type(self, value: Any) -> bool:
        expected_type = self.value_type

        if expected_type is None or expected_type is Any:
            return True

        return isinstance(value, expected_type)

    def is_valid(self, value: Any) -> bool:
        # Fix 1: valid_set was never consulted here, making it a silent no-op.
        # A value outside valid_set would pass is_valid(), which defeats the
        # purpose of having the constraint at all.
        if not self.is_valid_type(value):
            return False
        if not self.is_in_valid_set(value):
            return False
        if self.validate_fct and not self.validate_fct(value):
            return False
        return True

    def sanitize(self, value) -> Any:
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


@dataclass
class ConfigurableStringProperty(ConfigurableProperty):
    valid_regex:Optional[Any] = None

    def __post_init__(self):
        self.value_type = str
        super().__post_init__()

    def is_valid(self, value: str) -> bool:
        if not super().is_valid(value):
            return False

        if re.search(self.valid_regex or ".*", value) is None:
            return False

        return True

@dataclass
class ConfigurableNumericProperty(ConfigurableProperty):
    min_value: Optional[Any] = float("-inf")
    max_value: Optional[Any] = float("+inf")
    multiplier: int = 1
    format_string : Optional[str] = None

    def is_valid_type(self, value: Any) -> bool:
        # Fix 6: ConfigurableNumericProperty inherited is_valid_type from the base
        # class, which returns True when value_type is None (i.e. no default was
        # given and no type was specified explicitly).  That meant a
        # ConfigurableNumericProperty with no default accepted any Python object,
        # including strings and None, without complaint.
        #
        # The right default for a *numeric* property is to require a numeric value.
        # We use numbers.Real (the abstract base for all real numbers) so that both
        # int and float are accepted when no explicit type is imposed.
        #
        # Three cases:
        #   value_type is Any   → caller explicitly opted out of type checking
        #   value_type is None  → no type given; fall back to the numeric check
        #   otherwise           → caller gave an explicit type; defer to isinstance
        if self.value_type is Any:
            return True
        if self.value_type is None:
            return is_numeric(value)
        return isinstance(value, self.value_type)

    def is_in_valid_range(self, value: Any) -> bool:
        try:
            return self.min_value <= value <= self.max_value
        except TypeError:
            return False


    def is_valid(self, value: Any) -> bool:
        if not super().is_valid(value):
            return False
        if not self.is_in_valid_range(value):
            return False
        return True

    def sanitize(self, value) -> Any:
        value = super().sanitize(value)

        if is_numeric(value):
            if not self.is_in_valid_range(value):
                if value < self.min_value:
                    value = self.min_value
                elif value > self.max_value:
                    value = self.max_value

        return value

    @staticmethod
    def int_property_list(keys:list[str]):
        # Fix 5: this method lived on ConfigurableNumericProperty but created plain
        # ConfigurableProperty instances, discarding all the range/clamping
        # capabilities that make the subclass useful.
        properties = []
        for key in keys:
            properties.append(ConfigurableNumericProperty(name=key, value_type=int))

        return properties

class ConfigModel:
    def __init__(self, properties:list[ConfigurableProperty] = None, values:dict = None):
        # Fix 9: there was no way to supply starting values at construction time;
        # callers always had to do a two-step init (construct, then update_values).
        # The optional `values` argument lets callers pass an initial dict directly.
        # It is applied through update_values so that validation still runs.
        self.properties = { pd.name:pd  for pd in properties or []}
        self._values = { pd.name:pd.default_value  for pd in properties or []}
        if values is not None:
            self.update_values(values)

    @property
    def values(self):
        return self._values

    @values.setter
    def values(self, new_values):
        # Fix 2: the old setter did self._values = new_values, which replaced the
        # entire dict.  Passing only {"gain": 1} would silently discard every other
        # key.  Merging (update) is strictly safer: partial dicts work correctly and
        # a full replacement still works by just providing all keys.
        #
        # Fix 4 (partial): internal callers used to write
        #   if all(self.is_valid(new_values).values()):
        # which is verbose.  The new all_valid() helper centralises that idiom and
        # the error message now names the offending keys instead of being generic.
        if self.all_valid(new_values):
            self._values.update(new_values)
        else:
            invalid = [k for k, v in self.is_valid(new_values).items() if not v]
            raise ValueError(f"Invalid values for keys: {invalid}")

    def update_values(self, new_values):
        # Fix 3 (partial): update_values was a copy-paste of the setter logic.
        # Both paths now go through the setter so the merge/validation behaviour
        # is guaranteed to be identical everywhere.
        self.values = new_values

    def all_valid(self, values) -> bool:
        # Fix 4: is_valid() returns a per-key dict, which is useful for inspecting
        # which specific keys failed.  But most call sites only need a boolean
        # (is everything valid?).  Having to write all(...values()) everywhere is
        # noisy and easy to forget.  all_valid() provides the boolean shortcut while
        # leaving is_valid() intact for callers that need per-key detail.
        return all(self.is_valid(values).values())

    def is_valid(self, values):
        is_valid = {}
        for key, value in values.items():
            property = self.properties[key]
            is_valid[key] = property.is_valid(value)
        return is_valid

    def sanitize(self, values):
        sanitized_values = {}
        for key, value in values.items():
            property = self.properties[key]
            sanitized_values[key] = property.sanitize(value)

        return sanitized_values

class ConfigurationDialog(Dialog, ConfigModel):
    def __init__(self, properties=None, populate_body_fct=None, *args, **kwargs):
        # Fix 8: the old signature had `populate_body_fct` as the first positional
        # arg followed by *args/**kwargs.  `properties` was buried in **kwargs and
        # was supposed to flow down the MRO chain to ConfigModel.__init__.
        #
        # The chain is:
        #   ConfigurationDialog → Dialog → Base → _BaseWidget
        #       → Bindable → EventCapable → ConfigModel → object
        #
        # Bindable.__init__ and EventCapable.__init__ both call
        # super().__init__() WITHOUT forwarding **kwargs.  So `properties` was
        # silently dropped before reaching ConfigModel — the dialog always started
        # with an empty schema.
        #
        # The fix: declare `properties` as an explicit parameter so it is removed
        # from **kwargs before super().__init__ is called.  The MRO chain therefore
        # never sees it and ConfigModel gets initialised with properties=None
        # (empty).  After the MRO chain completes we call ConfigModel.__init__
        # explicitly to reinitialise with the correct properties.  This is safe
        # because ConfigModel.__init__ only sets self.properties and self._values,
        # which do not conflict with anything Dialog or the widget chain sets.
        super().__init__(*args, **kwargs)
        ConfigModel.__init__(self, properties=properties)
        self.populate_body_fct = populate_body_fct
        self.configuration_widgets = {}

    def populate_widget_body(self):
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
            # Fix 7: when a custom populate_body_fct is provided, widget_values()
            # reads back from self.configuration_widgets.  If the custom function
            # never populates that dict, widget_values() returns {} and run()
            # silently leaves self.values unchanged — the dialog appears to work but
            # does nothing.
            #
            # Contract: populate_body_fct is responsible for populating
            # self.configuration_widgets with {property_name: entry_widget} pairs.
            self.populate_body_fct()

    def widget_values(self) -> dict:
        values = {}
        for key, entry_widget in self.configuration_widgets.items():
            values[key] = entry_widget.value_variable.get()

        return self.sanitize(values)

    def run(self):
        reply = super().run()

        # Fix 3: the old code was self.values.update(self.widget_values()).
        # self.values returns the raw _values dict, so .update() mutated it
        # directly, bypassing the setter and its validation entirely.
        # Using update_values() (which goes through the setter) ensures the
        # same validation path is taken regardless of how values are changed.
        #
        # Fix 7 (partial): if configuration_widgets is empty (e.g. because a
        # custom populate_body_fct did not register any widgets) we skip the
        # update rather than silently merging an empty dict.
        widget_vals = self.widget_values()
        if widget_vals:
            self.update_values(widget_vals)

        return reply
