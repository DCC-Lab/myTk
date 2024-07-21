import subprocess
import importlib
import sys


class ModulesManager:
    imported = {}

    @classmethod
    def validate_environment(cls, pip_modules, ask_for_confirmation=True):
        cls.install_and_import_modules_if_absent(
            pip_modules, ask_for_confirmation=ask_for_confirmation
        )

    @classmethod
    def is_installed(cls, module_name):
        try:
            importlib.import_module(module_name)
            return True
        except ModuleNotFoundError:
            return False
        except Exception as err:  # Maybe wrong architecture?
            print(err)
            return False

    @classmethod
    def is_not_installed(cls, module_name):
        return not cls.is_installed(module_name)

    @classmethod
    def is_imported(cls, module_name):
        return module_name in sys.modules

    @classmethod
    def install_and_import_modules_if_absent(
        cls, pip_modules, ask_for_confirmation=True
    ):
        for pip_name, import_name in pip_modules.items():
            if cls.is_not_installed(import_name):
                if ask_for_confirmation:
                    result = askquestion(
                        f"""Module {pip_name} missing""",
                        f"""Do you want to install the missing module '{pip_name}'? If you do not wish to do so, the application may not work.""",
                        icon="warning",
                    )

                    if result != "yes":
                        continue

                cls.install_module(pip_name)

            cls.imported[pip_name] = importlib.import_module(import_name)

    @classmethod
    def install_module(cls, pip_name):
        try:
            completed_process = subprocess.run(
                [sys.executable, "-m", "pip", "install", pip_name],
                capture_output=True,
                check=True,
            )
        except Exception as err:
            raise RuntimeError(f"Unable to install module with PyPi name: {pip_name}")
