from mytk import *

class Camera(Configurable):
    exposure_time = ConfigurableNumericProperty(
        default_value=100, min_value=0, max_value=1000,
        displayed_name="Exposure time (ms)")
    gain = ConfigurableNumericProperty(
        default_value=3, min_value=0, max_value=100,
        displayed_name="Gain")

app = App()                                                                                                                                                                                             
app.root.withdraw()          # hide the root window                                                                                                                                                     

cam = Camera()
cam.exposure_time = 400       # direct attribute access, sanitized on assignment
cam.show_config_dialog()      # auto-generated dialog, values applied on Ok
print(cam.values)             # {'exposure_time': 400, 'gain': 3}
