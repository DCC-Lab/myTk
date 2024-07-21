import envtest
import unittest
from mytk import *
import os
import re
import io
import contextlib


class TestModulesManager(envtest.MyTkTestCase):
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

    def test_install_import(self):
        ModulesManager.install_and_import_modules_if_absent(
            {"matplotlib": "matplotlib"}
        )

    def test_install_import_error(self):
        with self.assertRaises(RuntimeError):
            ModulesManager.install_and_import_modules_if_absent(
                {"alouette": "alouette"}, ask_for_confirmation=False
            )

    def test_validate_environment_error(self):
        with self.assertRaises(RuntimeError):
            ModulesManager.validate_environment(
                {"alouette": "alouette"}, ask_for_confirmation=False
            )

    def test_validate_environment_no_error(self):
        ModulesManager.validate_environment(
            {"os": "os", "path": "path"}, ask_for_confirmation=False
        )


if __name__ == "__main__":
    unittest.main()
