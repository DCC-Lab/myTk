from mytk import *
from time import sleep

# App / Window
# App(geometry="800x600", position="center")

# App(geometry="1200x800", position="top-right")

# # Dialog class methods auto-center by default
Dialog.showinfo(message="Done!", auto_click=(Dialog.Replies.Ok, 1000))

# # Custom dialog instance
# dlg = Dialog(title="Settings", position="top-left")
