from typing import Any

import envtest

from mytk import Dialog
from mytk.configurable import (
    ConfigModel,
    Configurable,
    ConfigurableNumericProperty,
    ConfigurableStringProperty,
    ConfigurationDialog,
)


class TestObject(ConfigModel):
    pass

class ConfigurableTestCase(envtest.MyTkTestCase):
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


class ConfigurableDescriptorTestCase(envtest.MyTkTestCase):
    """Tests for the descriptor-based Configurable mixin.

    Each test defines its own class inline so descriptor __set_name__
    is always called fresh and classes never share state between tests.
    """

    # ------------------------------------------------------------------
    # Basic descriptor behaviour
    # ------------------------------------------------------------------

    def test200_default_value_returned_before_any_assignment(self):
        class Device(Configurable):
            exposure_time = ConfigurableNumericProperty(default_value=100)

        dev = Device()
        self.assertEqual(dev.exposure_time, 100)

    def test201_set_and_get_value(self):
        class Device(Configurable):
            exposure_time = ConfigurableNumericProperty(default_value=100)

        dev = Device()
        dev.exposure_time = 250
        self.assertEqual(dev.exposure_time, 250)

    def test202_out_of_range_value_is_clamped_on_set(self):
        # __set__ sanitizes, so out-of-range values are silently clamped
        # rather than raising — consistent with the dialog's tolerant approach.
        class Device(Configurable):
            exposure_time = ConfigurableNumericProperty(
                default_value=100, min_value=0, max_value=1000)

        dev = Device()
        dev.exposure_time = 9999
        self.assertEqual(dev.exposure_time, 1000)

        dev.exposure_time = -50
        self.assertEqual(dev.exposure_time, 0)

    def test203_float_cast_to_int_on_set(self):
        class Device(Configurable):
            gain = ConfigurableNumericProperty(default_value=3, value_type=int)

        dev = Device()
        dev.gain = 7.9      # sanitize casts float → int
        self.assertEqual(dev.gain, 7)

    def test204_two_instances_are_independent(self):
        # The descriptor is a class-level singleton, but values must be
        # stored per-instance.  This is the most important correctness
        # property of the descriptor approach.
        class Device(Configurable):
            gain = ConfigurableNumericProperty(default_value=1)

        a = Device()
        b = Device()
        a.gain = 10
        self.assertEqual(a.gain, 10)
        self.assertEqual(b.gain, 1)   # b is unaffected

    def test205_class_level_access_returns_descriptor(self):
        # Camera.exposure_time should give back the descriptor itself, not
        # the default value — that way callers can inspect the schema.
        class Device(Configurable):
            exposure_time = ConfigurableNumericProperty(default_value=100)

        self.assertIsInstance(Device.exposure_time, ConfigurableNumericProperty)

    def test206_name_auto_derived_from_attribute(self):
        class Device(Configurable):
            exposure_time = ConfigurableNumericProperty(default_value=100)

        self.assertEqual(Device.exposure_time.name, "exposure_time")

    def test207_explicit_name_not_overridden_by_set_name(self):
        # If a name is given explicitly it should be preserved.
        class Device(Configurable):
            exp = ConfigurableNumericProperty(name="exposure_time", default_value=100)

        self.assertEqual(Device.exp.name, "exposure_time")

    # ------------------------------------------------------------------
    # Configurable mixin methods
    # ------------------------------------------------------------------

    def test210_values_returns_all_current_values(self):
        class Device(Configurable):
            exposure_time = ConfigurableNumericProperty(default_value=100)
            gain          = ConfigurableNumericProperty(default_value=3)

        dev = Device()
        dev.exposure_time = 200
        v = dev.values
        self.assertEqual(v["exposure_time"], 200)
        self.assertEqual(v["gain"], 3)

    def test211_update_values_partial(self):
        class Device(Configurable):
            exposure_time = ConfigurableNumericProperty(default_value=100)
            gain          = ConfigurableNumericProperty(default_value=3)

        dev = Device()
        dev.update_values({"gain": 10})
        self.assertEqual(dev.gain, 10)
        self.assertEqual(dev.exposure_time, 100)   # unchanged

    def test212_is_valid_returns_per_key_dict(self):
        class Device(Configurable):
            exposure_time = ConfigurableNumericProperty(
                default_value=100, min_value=0, max_value=1000)

        dev = Device()
        result = dev.is_valid({"exposure_time": 500})
        self.assertTrue(result["exposure_time"])

        result = dev.is_valid({"exposure_time": -1})
        self.assertFalse(result["exposure_time"])

    def test213_all_valid_returns_bool(self):
        class Device(Configurable):
            exposure_time = ConfigurableNumericProperty(
                default_value=100, min_value=0, max_value=1000)

        dev = Device()
        self.assertTrue(dev.all_valid({"exposure_time": 500}))
        self.assertFalse(dev.all_valid({"exposure_time": -1}))

    def test214_configurable_properties_discovers_all_descriptors(self):
        class Device(Configurable):
            exposure_time = ConfigurableNumericProperty(default_value=100)
            gain          = ConfigurableNumericProperty(default_value=3)
            label         = ConfigurableStringProperty(default_value="cam")

        props = Device._configurable_properties()
        self.assertIn("exposure_time", props)
        self.assertIn("gain", props)
        self.assertIn("label", props)
        self.assertEqual(len(props), 3)

    # ------------------------------------------------------------------
    # Inheritance
    # ------------------------------------------------------------------

    def test220_subclass_inherits_parent_properties(self):
        class Base(Configurable):
            gain = ConfigurableNumericProperty(default_value=1)

        class Child(Base):
            exposure_time = ConfigurableNumericProperty(default_value=100)

        dev = Child()
        self.assertEqual(dev.gain, 1)
        self.assertEqual(dev.exposure_time, 100)

        props = Child._configurable_properties()
        self.assertIn("gain", props)
        self.assertIn("exposure_time", props)

    def test221_subclass_can_override_parent_property(self):
        class Base(Configurable):
            gain = ConfigurableNumericProperty(default_value=1, max_value=10)

        class Child(Base):
            gain = ConfigurableNumericProperty(default_value=5, max_value=100)

        child = Child()
        self.assertEqual(child.gain, 5)

        # The child's schema (max 100) applies, not the parent's (max 10).
        child.gain = 50
        self.assertEqual(child.gain, 50)

        # Parent instances still use the parent schema.
        parent = Base()
        parent.gain = 50
        self.assertEqual(parent.gain, 10)   # clamped to parent's max

    def test222_parent_and_child_instances_are_independent(self):
        class Base(Configurable):
            gain = ConfigurableNumericProperty(default_value=1)

        class Child(Base):
            pass

        b = Base()
        c = Child()
        b.gain = 9
        self.assertEqual(b.gain, 9)
        self.assertEqual(c.gain, 1)

    # ------------------------------------------------------------------
    # String and mixed property types
    # ------------------------------------------------------------------

    def test230_string_property_descriptor(self):
        class Device(Configurable):
            label = ConfigurableStringProperty(default_value="default")

        dev = Device()
        self.assertEqual(dev.label, "default")
        dev.label = "microscope"
        self.assertEqual(dev.label, "microscope")

    def test231_mixed_numeric_and_string_properties(self):
        class Device(Configurable):
            exposure_time = ConfigurableNumericProperty(default_value=100)
            label         = ConfigurableStringProperty(default_value="cam")

        dev = Device()
        self.assertEqual(dev.values, {"exposure_time": 100, "label": "cam"})

    # ------------------------------------------------------------------
    # Dialog integration
    # ------------------------------------------------------------------

    def test240_show_config_dialog_defaults(self):
        # Dialog opens and immediately auto-clicks Ok.  Values should come
        # back unchanged (default → entry → sanitize → update).
        class Camera(Configurable):
            exposure_time = ConfigurableNumericProperty(
                default_value=100, min_value=0, max_value=1000,
                displayed_name="Exposure time")
            gain = ConfigurableNumericProperty(
                default_value=3, min_value=0, max_value=100,
                displayed_name="Gain")

        cam = Camera()
        reply = cam.show_config_dialog(
            title="Settings",
            buttons_labels=["Ok"],
            auto_click=("Ok", 200),
        )
        self.assertEqual(reply, Dialog.Replies.Ok)
        self.assertEqual(cam.exposure_time, 100)
        self.assertEqual(cam.gain, 3)

    def test241_show_config_dialog_seeds_with_current_values(self):
        # If the object already has non-default values the dialog should
        # open with those values and return them unchanged after Ok.
        class Camera(Configurable):
            exposure_time = ConfigurableNumericProperty(
                default_value=100, min_value=0, max_value=1000,
                displayed_name="Exposure time")
            gain = ConfigurableNumericProperty(
                default_value=3, min_value=0, max_value=100,
                displayed_name="Gain")

        cam = Camera()
        cam.exposure_time = 400
        cam.gain = 8

        reply = cam.show_config_dialog(
            title="Settings",
            buttons_labels=["Ok"],
            auto_click=("Ok", 200),
        )
        self.assertEqual(cam.exposure_time, 400)
        self.assertEqual(cam.gain, 8)


if __name__ == "__main__":
    envtest.unittest.main()
