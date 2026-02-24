import unittest
from mytk import *


@unittest.skip("An example to run manually")
class ManualConfigurableExample(unittest.TestCase):
    def test_show_config_dialog(self):
        class Camera(Configurable):
            exposure_time = ConfigurableNumericProperty(
                default_value=100, min_value=0, max_value=1000,
                displayed_name="Exposure time (ms)")
            gain = ConfigurableNumericProperty(
                default_value=3, min_value=0, max_value=100,
                displayed_name="Gain")

        app = App()
        app.root.withdraw()

        cam = Camera()
        cam.exposure_time = 400
        cam.show_config_dialog()
        print(cam.values)


if __name__ == "__main__":
    unittest.main()
