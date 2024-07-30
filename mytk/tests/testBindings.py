import envtest
import unittest
import os
from mytk import *
import re
import io
import contextlib


class Success(Exception):
    pass


class A(Bindable):
    def __init__(self, a):
        super().__init__()
        self.py_a = a
        self.var_a = IntVar(value=a)


class B(Bindable):
    def __init__(self, b):
        super().__init__()
        self.py_b = b
        self.var_b = IntVar(value=b)


class C(Bindable):
    def __init__(self, c):
        super().__init__()
        self.py_c = c
        self.var_c = IntVar(value=c)
        self._dict = {}

    @property
    def foo(self):
        return self._dict.get("foo", None)

    @foo.setter
    def foo(self, value):
        self._dict["foo"] = value


class Observer(Bindable):
    def __init__(self):
        super().__init__()
        self.observed_object = None
        self.observed_property_name = None
        self.new_value = None
        self.context = None
        self.was_called = False

    def observed_property_changed(
        self, observed_object, observed_property_name, new_value, context
    ):
        self.observed_object = observed_object
        self.observed_property_name = observed_property_name
        self.new_value = new_value
        self.context = context
        self.was_called = True


class BuggyObserver(Bindable):

    def observed_property_changed(
        self, observed_object, observed_property_name, new_value, context
    ):
        raise Exception("I will not be caught")


class TestBindings(envtest.MyTkTestCase):

    def test_init(self):
        a = A(1)
        b = B(2)
        self.assertEqual(a.py_a, 1)
        self.assertEqual(b.py_b, 2)
        a.py_a = 3
        self.assertEqual(a.py_a, 3)
        self.assertEqual(b.py_b, 2)

        self.assertTrue(isinstance(a.var_a, Variable))
        self.assertTrue(isinstance(b.var_b, Variable))

    def test_observable_python_property(self):
        a = A(1)
        obs = Observer()
        a.add_observer(obs, "py_a", "SomeContext")

        a.py_a = 2
        self.assertTrue(obs.was_called)

        self.assertEqual(obs.new_value, 2)
        self.assertEqual(obs.context, "SomeContext")
        self.assertEqual(obs.observed_object, a)
        self.assertEqual(obs.observed_property_name, "py_a")

    def test_observable_tk_var(self):
        a = A(1)
        obs = Observer()
        a.add_observer(obs, "var_a", "SomeContext")

        a.var_a.set(2)
        self.assertTrue(obs.was_called)

        self.assertEqual(obs.new_value, 2)
        self.assertEqual(obs.context, "SomeContext")
        self.assertEqual(obs.observed_object, a)
        self.assertEqual(obs.observed_property_name, "var_a")

    def test_observable_overwriting_tk_var(self):
        a = A(1)

        self.assertTrue(isinstance(a.var_a, Variable))

        with self.assertRaises(TypeError):
            a.var_a = 2

    def test_observable_overwriting_tk_var_with_none(self):
        a = A(1)
        self.assertTrue(isinstance(a.var_a, Variable))

        a.var_a = None
        self.assertEqual(a.var_a, None)

    def test_observable_overwriting_tk_var_with_other_tk_var(self):
        a = A(1)
        self.assertTrue(isinstance(a.var_a, Variable))

        a.var_a = StringVar(value="Test")
        self.assertTrue(isinstance(a.var_a, Variable))

    def test_observable_missing_property(self):
        a = A(1)
        obs = Observer()
        with self.assertRaises(AttributeError):
            a.add_observer(obs, "missing", "SomeContext")

    def test_buggy_observer(self):
        a = A(1)
        obs = BuggyObserver()
        a.add_observer(obs, "var_a", "SomeContext")

        self.assertTrue(isinstance(a.var_a, Variable))

        f = io.StringIO()
        with contextlib.redirect_stderr(f):
            a.var_a.set(3)

        self.assertTrue(f.getvalue().startswith("Exception"))

    def test_bound_python_properties_both_sides(self):

        a = A(1)
        b = B(2)
        a.bind_properties("py_a", b, "py_b")

        a.py_a = 3
        self.assertEqual(a.py_a, 3)
        self.assertEqual(b.py_b, 3)
        b.py_b = 4
        self.assertEqual(a.py_a, 4)
        self.assertEqual(b.py_b, 4)
        b.py_b = "test"
        self.assertEqual(a.py_a, b.py_b)

    def test_binding_python_properties_changes_second_property(self):

        a = A(1)
        b = B(2)
        self.assertEqual(a.py_a, 1)
        self.assertEqual(b.py_b, 2)

        a.bind_properties("py_a", b, "py_b")
        self.assertEqual(a.py_a, 1)
        self.assertEqual(b.py_b, 1)

    def test_tk_var_names(self):
        a = A(1)
        b = B(2)

        match = re.match(r"PY_VAR\d+", a.var_a._name)
        self.assertIsNotNone(match)
        match = re.match(r"PY_VAR\d+", b.var_b._name)
        self.assertIsNotNone(match)

    def test_bound_python_property_with_tk_var(self):
        a = A(1)
        b = B(2)
        a.bind_properties("py_a", b, "var_b")
        self.assertTrue(isinstance(a.var_a, Variable))
        self.assertTrue(isinstance(b.var_b, Variable))
        self.assertFalse(isinstance(a.py_a, Variable))
        self.assertFalse(isinstance(b.py_b, Variable))

        a.py_a = 3
        self.assertEqual(a.py_a, 3)
        self.assertEqual(b.var_b.get(), 3)
        b.var_b.set(value=5)
        self.assertEqual(a.py_a, 5)
        self.assertEqual(b.var_b.get(), 5)

        self.assertTrue(isinstance(a.var_a, Variable))
        self.assertTrue(isinstance(b.var_b, Variable))
        self.assertFalse(isinstance(a.py_a, Variable))
        self.assertFalse(isinstance(b.py_b, Variable))

    def test_bound_tk_var_with_python_property(self):
        a = A(1)
        b = B(2)
        b.bind_properties("var_b", a, "py_a")

        self.assertTrue(isinstance(a.var_a, Variable))
        self.assertTrue(isinstance(b.var_b, Variable))
        self.assertFalse(isinstance(a.py_a, Variable))
        self.assertFalse(isinstance(b.py_b, Variable))

        a.py_a = 3
        self.assertEqual(a.py_a, 3)
        self.assertEqual(b.var_b.get(), 3)
        b.var_b.set(value=5)
        self.assertEqual(a.py_a, 5)
        self.assertEqual(b.var_b.get(), 5)

        self.assertTrue(isinstance(a.var_a, Variable))
        self.assertTrue(isinstance(b.var_b, Variable))
        self.assertFalse(isinstance(a.py_a, Variable))
        self.assertFalse(isinstance(b.py_b, Variable))

    def test_variable_bound_to_defined_property(self):
        c = C(c=1)
        c.bind_properties("py_c", c, "foo")
        self.assertEqual(c.py_c, 1)
        self.assertEqual(c.foo, 1)

    def test_defined_property_bound_to_variable(self):
        c = C(c=1)
        c.bind_properties("foo", c, "py_c")
        self.assertEqual(c.foo, None)
        self.assertEqual(c.py_c, None)
        c.foo = 2
        self.assertEqual(c.foo, 2)
        self.assertEqual(c.py_c, 2)


if __name__ == "__main__":
    unittest.main()
