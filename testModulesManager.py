import unittest
import os
from mytk import *
import re
import io
import contextlib

class TestModulesManager(unittest.TestCase):
    def test_is_installed(self):
        self.assertTrue(ModulesManager.is_installed("io"))
        self.assertFalse(ModulesManager.is_installed("alouette"))

    def test_is_not_installed(self):
        self.assertFalse(ModulesManager.is_not_installed("io"))
        self.assertTrue(ModulesManager.is_not_installed("alouette"))

    def test_is_imported(self):
        self.assertTrue(ModulesManager.is_imported("io"))

    def test_install_module(self):
        ModulesManager.install_module("scipy")

    def test_install_error_module(self):
        with self.assertRaises(RuntimeError):
            ModulesManager.install_module("alouette")

    def test_install_noerror_module(self):
        ModulesManager.install_and_import_modules_if_absent({"raytracing":"raytracing"})
        

if __name__ == "__main__":
    unittest.main()