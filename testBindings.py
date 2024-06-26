import unittest
import os
from mytk import *
import re

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

class Observer(Bindable):
    def __init__(self):
        super().__init__()
        self.observed_object = None
        self.observed_property_name = None
        self.new_value = None
        self.context = None

    def observed_property_changed(self, observed_object, observed_property_name, new_value, context):
        self.observed_object = observed_object
        self.observed_property_name = observed_property_name
        self.new_value = new_value
        self.context = context
        raise Success()

class TestBindings(unittest.TestCase):
    def setUp(self):
        root = Tk()

    def test_init(self):
        a = A(1)
        b = B(2)
        self.assertEqual(a.py_a, 1)
        self.assertEqual(b.py_b, 2)
        a.py_a = 3
        self.assertEqual(a.py_a, 3)
        self.assertEqual(b.py_b, 2)

    def test_observable(self):
        a = A(1)
        obs = Observer()
        a.add_observer(obs, 'py_a', 'SomeContext')

        with self.assertRaises(Success):
            a.py_a = 2

        self.assertEqual(obs.new_value, 2)
        self.assertEqual(obs.context, 'SomeContext')
        self.assertEqual(obs.observed_object, a)
        self.assertEqual(obs.observed_property_name, 'py_a')

    def test_bound_python_properties_both_sides(self):

        a = A(1)
        b = B(2)
        a.bind_properties('py_a', b, 'py_b')

        a.py_a = 3
        self.assertEqual(a.py_a, 3)
        self.assertEqual(b.py_b, 3)
        b.py_b = 4
        self.assertEqual(a.py_a, 4)
        self.assertEqual(b.py_b, 4)
        b.py_b = 'test'
        self.assertEqual(a.py_a, b.py_b)

    def test_bound_python_properties_changes_second(self):
        
        a = A(1)
        b = B(2)
        self.assertEqual(a.py_a, 1)
        self.assertEqual(b.py_b, 2)

        a.bind_properties('py_a', b, 'py_b')
        self.assertEqual(a.py_a, 1)
        self.assertEqual(b.py_b, 1)

    def test_tk_var_names(self):
        a = A(1)
        b = B(2)

        match = re.match(r'PY_VAR\d+', a.var_a._name)
        self.assertIsNotNone(match)
        match = re.match(r'PY_VAR\d+', b.var_b._name)
        self.assertIsNotNone(match)

    def test_bound_python_with_tk_var(self):
        a = A(1)
        b = B(2)
        a.bind_properties('py_a', b, 'var_b')

        a.py_a = 3
        self.assertEqual(a.py_a, 3)
        self.assertEqual(b.var_b.get(), 3)
        b.var_b.set(value=5)
        self.assertEqual(a.py_a, 5)
        self.assertEqual(b.var_b.get(), 5)

if __name__ == "__main__":
    unittest.main()