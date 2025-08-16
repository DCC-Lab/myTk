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
        if not self.is_valid_type(value):
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
        properties = []
        for key in keys:
            properties.append(ConfigurableProperty(name=key, value_type=int))
        
        return properties
   
class ConfigModel:
    def __init__(self, properties:list[ConfigurableProperty] = None):
        self.properties = { pd.name:pd  for pd in properties or []} 
        self._values = { pd.name:pd.default_value  for pd in properties or []} 
    
    @property
    def values(self):
        return self._values
    
    @values.setter
    def values(self, new_values):
        if all(self.is_valid(new_values).values()):
            self._values = new_values
        else:
            raise ValueError("Some values are invalid")
    def update_values(self, new_values):
        if all(self.is_valid(new_values).values()):
            self._values.update(new_values)
        else:
            raise ValueError("Some values are invalid")
        
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
    def __init__(self, populate_body_fct=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
            self.populate_body_fct()
    
    def widget_values(self) -> dict:
        values = {}
        for key, entry_widget in self.configuration_widgets.items():
            values[key] = entry_widget.value_variable.get()
            
        return self.sanitize(values)
        
    def run(self):
        reply = super().run()
        
        self.values.update(self.widget_values())
            
        return reply
