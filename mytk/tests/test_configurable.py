import envtest
from typing import Optional, Tuple, Any

from pymicroscope.utils.configurable import ConfigModel, ConfigurableStringProperty, ConfigurableNumericProperty, ConfigurationDialog
from mytk import Dialog, Label, Entry
import threading, atexit, sys


class TestObject(ConfigModel):
    pass

class ConfigurableTestCase(envtest.CoreTestCase):
    def test000_configurable_property(self) -> None:
        """
        Verify that the abstract ImageProvider cannot be instantiated directly.
        """

        prop = ConfigurableNumericProperty(
            name="Exposure Time",
            default_value=100,
            min_value=0,
            max_value=1000,
            validate_fct=lambda x: x >= 0,
            format_string="{:.1f} ms",
            multiplier=1000
        )
        
        self.assertIsNotNone(prop)

    def test010_configurable_property_with_defaults(self) -> None:

        prop = ConfigurableNumericProperty(
            name="Exposure Time",
            default_value=100,
        )
        
        self.assertIsNotNone(prop)
        self.assertTrue(prop.is_in_valid_range(100))
        self.assertTrue(prop.is_in_valid_range(10000))
        self.assertTrue(prop.is_in_valid_range(-10000))
                         
    def test020_configurable_property_validated(self) -> None:

        prop = ConfigurableNumericProperty(
            name="Exposure Time",
            default_value=100,
            min_value=0,
            max_value=1000,            
        )
        
        self.assertIsNotNone(prop)
        self.assertTrue(prop.is_in_valid_range(100))
        self.assertFalse(prop.is_in_valid_range(10000))

    def test022_configurable_property_is_valid_set(self) -> None:

        prop = ConfigurableNumericProperty(
            name="Exposure Time",
            valid_set = set([1,2,3])
        )

        self.assertTrue(prop.is_in_valid_set(1))
        self.assertTrue(prop.is_in_valid_set(2))
        self.assertFalse(prop.is_in_valid_set(0))

    def test022_configurable_property_is_valid_set_as_list(self) -> None:

        prop = ConfigurableNumericProperty(
            name="Exposure Time",
            valid_set = [1,2,3]
        )

        self.assertTrue(prop.is_in_valid_set(1))
        self.assertTrue(prop.is_in_valid_set(2))
        self.assertFalse(prop.is_in_valid_set(0))

    def test025_configurable_property_is_valid(self) -> None:

        prop = ConfigurableNumericProperty(
            name="Exposure Time",
            default_value=100,
            min_value=0,
            max_value=1000,
            value_type=int         
        )
        
        self.assertTrue(prop.is_valid(100))
        self.assertTrue(prop.is_valid(0))
        self.assertTrue(prop.is_valid(1000))
        self.assertFalse(prop.is_valid(-100))
        self.assertFalse(prop.is_valid(5.5))
        self.assertFalse(prop.is_valid(5000.12))
        
    def test025_configurable_property_sanitize(self) -> None:

        prop = ConfigurableNumericProperty(
            name="Exposure Time",
            default_value=100,
            min_value=0,
            max_value=1000,
            value_type=int         
        )

        self.assertEqual(prop.sanitize(-100), 0)
        self.assertEqual(prop.sanitize(2000), 1000)
        self.assertEqual(prop.sanitize(100.5), 100)
        
    def test026_configurable_property_sanitize_no_type(self) -> None:

        prop = ConfigurableNumericProperty(
            name="Exposure Time",
            default_value=100,
            min_value=0,
            max_value=1000,
        )

        self.assertEqual(prop.sanitize(-100.1), 0)
        self.assertEqual(prop.sanitize(2000), 1000)
        self.assertEqual(prop.sanitize(100.5), 100) 

    def test026_configurable_property_sanitize_type_inferred_from_default_no_range(self) -> None:

        prop = ConfigurableNumericProperty(
            name="Exposure Time",
            default_value=100,
        )

        self.assertEqual(prop.sanitize(-100.1), -100)
        self.assertEqual(prop.sanitize(2000), 2000)
        self.assertEqual(prop.sanitize(100.5), 100)

    def test027_configurable_property_sanitize_no_type_no_range(self) -> None:

        prop = ConfigurableNumericProperty(
            name="Exposure Time",
            default_value=100,
            value_type=Any
        )

        self.assertEqual(prop.sanitize(-100.1), -100.1)
        self.assertEqual(prop.sanitize(2000), 2000)
        self.assertEqual(prop.sanitize(100.5), 100.5)

    def test028_configurable_property_wrong_type(self) -> None:

        with self.assertRaises(ValueError):
            prop = ConfigurableNumericProperty(
                name="Exposure Time",
                default_value=100.1,
                min_value=0,
                max_value=1000,
                value_type=int
            )

        with self.assertRaises(ValueError):
            prop = ConfigurableNumericProperty(
                name="Exposure Time",
                default_value=100.0,
                min_value=0,
                max_value=1000,
                value_type=int
            )

    def test028_configurable_property_wrong_str_type(self) -> None:
        with self.assertRaises(ValueError):
            prop = ConfigurableStringProperty(
                name="String",
                default_value=100.0,
            )

    def test029_configurable_property_is_invalid(self) -> None:
        prop = ConfigurableStringProperty(name="String")
        self.assertFalse(prop.is_valid(10))

    def test031_configurable_property_is_in_valid_set_but_set_is_empty(self) -> None:
        prop = ConfigurableStringProperty(name="String")
        self.assertTrue(prop.is_in_valid_set(10))

    def test031_configurable_property_has_invalid_values(self) -> None:
        with self.assertRaises(ValueError):
            prop = ConfigurableStringProperty(name="String", valid_set=['a', 1])

    def test031_configurable_property_sanitize_none_to_default(self) -> None:
        prop = ConfigurableStringProperty(name="String", default_value="Something")
        self.assertEqual(prop.sanitize(None), "Something")

    def test031_configurable_property_sanitize_unabnle_to_cast_defaults_to_default_value(self) -> None:
        prop = ConfigurableNumericProperty(name="Numeric value", default_value=100)
        self.assertEqual(prop.sanitize("adsklahjs"), 100)
            
    def test050_configurable_str_property(self) -> None:

        prop = ConfigurableStringProperty(
            name="Name",
            valid_regex="[ABC]def"
        )

        self.assertEqual(prop.value_type, str)
        
        self.assertTrue(prop.is_valid("Adef"))
        self.assertTrue(prop.is_valid("Bdef"))
        self.assertTrue(prop.is_valid("Cdef"))
        self.assertFalse(prop.is_valid("Test"))
        self.assertFalse(prop.is_valid(100))
        self.assertEqual(prop.sanitize("Cdef"), 'Cdef')

    def test051_configurable_str_property_is_valid_set_as_list(self) -> None:

        prop = ConfigurableStringProperty(
            name="Name",
            valid_set = ["Daniel", "Mireille"],
            valid_regex = ".*"
        )

        self.assertTrue(prop.is_in_valid_set("Daniel"))
        self.assertTrue(prop.is_in_valid_set("Mireille"))
        self.assertFalse(prop.is_in_valid_set("Bob the builder"))

    def test052_configurable_property_fct_validate(self) -> None:

        def is_positive(value):
            return value > 0
        
        prop = ConfigurableNumericProperty(
            name="Name",
            validate_fct = is_positive
        )

        self.assertTrue(prop.is_valid(1))
        self.assertFalse(prop.is_valid(-1))


    def test053_configurable_property_invalid_set(self) -> None:
        with self.assertRaises(ValueError) as err:
            prop = ConfigurableNumericProperty(
                name="Name",
                valid_set=['String']
            )

    
    def test060_quick_propertyy_lists(self):
        props = ConfigurableNumericProperty.int_property_list(['a','b'])
        self.assertIsNotNone(props)
        self.assertEqual(len(props), 2)
        
    def test030_configurable_object_init(self) -> None:

        prop1 = ConfigurableNumericProperty(
            name="exposure_time",
            default_value=100,
            min_value=0,
            max_value=1000,            
        )

        prop2 = ConfigurableNumericProperty(
            name="gain",
            default_value=100,
            min_value=0,
            max_value=1000,            
        )

        prop3 = ConfigurableStringProperty(
            name="name",
            default_value="Test",
        )
        
        obj = TestObject(properties=[prop1, prop2, prop3])
        self.assertIsNotNone(obj)

    def test030_configurable_object_valid_props(self):
        prop1 = ConfigurableNumericProperty(
            name="exposure_time",
            default_value=100,
            min_value=0,
            max_value=1000,            
        )

        prop2 = ConfigurableNumericProperty(
            name="gain",
            default_value=100,
            min_value=0,
            max_value=1000,            
        )

        prop3 = ConfigurableStringProperty(
            name="name",
            default_value="Test",
        )
        
        obj = TestObject(properties=[prop1, prop2, prop3])

        self.assertTrue(obj.is_valid({"gain":1,"exposure_time":1}))

    def test030_configurable_object_invalid_props(self):
        prop1 = ConfigurableNumericProperty(
            name="exposure_time",
            default_value=100,
            min_value=0,
            max_value=1000,            
        )

        prop2 = ConfigurableNumericProperty(
            name="gain",
            default_value=100,
            min_value=0,
            max_value=1000,            
        )

        prop3 = ConfigurableStringProperty(
            name="name",
            default_value="Test",
        )
        
        obj = TestObject(properties=[prop1, prop2, prop3])

        is_valid = obj.is_valid({"gain":-1,"exposure_time":1})
        self.assertFalse(is_valid['gain'])
        self.assertTrue(is_valid['exposure_time'])
    
    def test030_configurable_object_invalid_key(self):
        prop1 = ConfigurableNumericProperty(
            name="exposure_time",
            default_value=100,
            min_value=0,
            max_value=1000,            
        )

        prop2 = ConfigurableNumericProperty(
            name="gain",
            default_value=100,
            min_value=0,
            max_value=1000,            
        )

        prop3 = ConfigurableStringProperty(
            name="name",
            default_value="Test",
        )
        
        obj = TestObject(properties=[prop1, prop2, prop3])

        with self.assertRaises(KeyError):
            self.assertTrue(obj.is_valid({"gain":1,"exposure_time":1,"bla":0}))
        

    def test030_configurable_object_sanitize(self):
        prop1 = ConfigurableNumericProperty(
            name="exposure_time",
            default_value=100,
            min_value=10,
            max_value=1000,            
        )

        prop2 = ConfigurableNumericProperty(
            name="gain",
            default_value=100,
            min_value=1,
            max_value=1000,            
        )

        prop3 = ConfigurableStringProperty(
            name="name",
            default_value="Test",
        )
        
        obj = TestObject(properties=[prop1, prop2, prop3])

        sanitized = obj.sanitize({"gain":0,"exposure_time":1})
        self.assertEqual(sanitized['gain'],1)

        sanitized = obj.sanitize({"gain":0,"exposure_time":10_000})
        self.assertEqual(sanitized['gain'],1) # too low
        self.assertEqual(sanitized['exposure_time'],1_000) # too high

        sanitized = obj.sanitize({"gain":0,"exposure_time":None})
        self.assertEqual(sanitized['exposure_time'], 100) # None -> default_value

        sanitized = obj.sanitize({"gain":0,"exposure_time":"10"})
        self.assertEqual(sanitized['exposure_time'], 10) # Wrong type -> casting

        sanitized = obj.sanitize({"gain":0,"exposure_time":"Wrong"})
        self.assertEqual(sanitized['exposure_time'], 100) # Wrong type -> default_value

    def test099_configurable_object_get_set(self):
        prop1 = ConfigurableNumericProperty(
            name="exposure_time",
            default_value=100,
            min_value=10,
            max_value=1000,            
        )

        prop2 = ConfigurableNumericProperty(
            name="gain",
            default_value=100,
            min_value=1,
            max_value=1000,            
        )

        prop3 = ConfigurableStringProperty(
            name="name",
            default_value="Test",
        )
        
        obj = TestObject(properties=[prop1, prop2, prop3])

        self.assertIsNotNone(obj.values)
        obj.values = {"gain":1}

        with self.assertRaises(ValueError):
            obj.values = {"gain":-1}
        
    def test100_configurable_object_dialog(self) -> None:

        prop1 = ConfigurableNumericProperty(
            name="exposure_time",
            displayed_name="Exposure time",
            default_value=100,
            min_value=0,
            max_value=1000,
        )

        prop2 = ConfigurableNumericProperty(
            name="gain",
            displayed_name="Gain",
            default_value=3,
            min_value=0,
            max_value=1000,
        )

        diag = ConfigurationDialog(title="Configuration", properties=[prop1, prop2],
                                   buttons_labels=["Ok"], auto_click=("Ok", 200))
        reply = diag.run()

        self.assertEqual(diag.values, {"gain":3, 'exposure_time':100})

    def test110_configurable_object_dialog_with_values(self) -> None:

        prop1 = ConfigurableNumericProperty(
            name="exposure_time",
            displayed_name="Exposure time",
            default_value=100,
            min_value=0,
            max_value=1000,
        )

        prop2 = ConfigurableNumericProperty(
            name="gain",
            displayed_name="Gain",
            default_value=3,
            min_value=0,
            max_value=1000,
        )

        diag = ConfigurationDialog(title="Configuration", properties=[prop1, prop2],
                                   buttons_labels=["Ok"], auto_click=("Ok", 200))
        
        diag.values = {"gain":10, 'exposure_time':30}
        reply = diag.run()

        self.assertEqual(diag.values, {"gain":10, 'exposure_time':30})

    # # def test050_ConfiguModel(self) -> None:
    # #     ConfigModel()

    
if __name__ == "__main__":
    envtest.main()
