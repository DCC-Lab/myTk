from tkinter import Toplevel
from .base import *
from .button import Button
from .views import View
from .images import Image
from .labels import Label

import pathlib


class Dialog(Base):
    class Replies(StrEnum):
        Ok = "Ok"
        Cancel = "Cancel"
        Abort = "Abort"
        Timedout = "Timedout"

    @classmethod
    def showinfo(cls, message, title="Info", auto_click=(None, None)):
        diag = Dialog(
            dialog_type="info", title=title, message=message, auto_click=auto_click
        )
        return diag.run()

    @classmethod
    def showwarning(cls, message, title="Warning", auto_click=(None, None)):
        diag = Dialog(
            dialog_type="warning", title=title, message=message, auto_click=auto_click
        )
        return diag.run()

    @classmethod
    def showerror(cls, message, title="Error", auto_click=(None, None)):
        diag = Dialog(
            dialog_type="error", title=title, message=message, auto_click=auto_click
        )
        return diag.run()

    def __init__(
        self, dialog_type, title, message, buttons_labels=None, auto_click=(None, None)
    ):
        super().__init__()
        self.dialog_type = dialog_type
        self.title = title
        self.message = message
        self.reply = None
        self.auto_click = auto_click[0]
        self.timeout = auto_click[1]

        if buttons_labels is None:
            self.buttons_labels = [Dialog.Replies.Ok]
        else:
            self.buttons_labels = buttons_labels
        self.buttons = {}

        if self.auto_click is not None:
            if self.auto_click not in self.buttons_labels:
                self.auto_click = None

        self.create_widget(master=None)

    def create_widget(self, master):
        self.widget = Toplevel()
        self.widget.title(self.title)
        self.parent = None

        self.widget.wait_visibility()  # can't grab until window appears, so we wait

        resource_directory = pathlib.Path(__file__).parent / "resources"

        if self.dialog_type == "error":
            icon = Image(filepath=resource_directory / "error.png")
        elif self.dialog_type == "warning":
            icon = Image(filepath=resource_directory / "warning.png")
        elif self.dialog_type == "info":
            icon = Image(filepath=resource_directory / "info.png")
        else:
            icon = Image(filepath=resource_directory / "info.png")

        icon.is_rescalable = False
        icon.grid_into(self, column=0, row=0, pady=20, padx=20, sticky="")

        control_buttons = View(width=200, height=30)
        control_buttons.grid_into(
            widget=self.widget,
            column=1,
            row=1,
            columnspan=2,
            pady=10,
            padx=10,
            sticky="nsew",
        )
        control_buttons.column_resize_weight(0, 1)

        self.buttons = self.create_behavior_buttons()
        for i, button_label in enumerate(self.buttons_labels):
            button = self.buttons[button_label]
            button.grid_into(
                control_buttons, column=2 - i, row=1, pady=5, padx=5, sticky="se"
            )

        label1 = Label(
            text=self.message, wrapping=True, width=30, wraplength=300, justify="center"
        )
        label1.grid_into(
            widget=self.widget,
            column=1,
            columnspan=2,
            row=0,
            pady=5,
            padx=5,
            sticky="nsew",
        )

        self.column_resize_weight(0, 0)
        self.column_resize_weight(1, 1)
        self.widget.resizable(False, False)

        self.assign_default_key_shortcuts()

    def assign_default_key_shortcuts(self):
        if Dialog.Replies.Ok in self.buttons.keys():
            self.widget.bind("<Return>", self.user_clicked_ok)
            self.buttons[Dialog.Replies.Ok].set_as_default()

        self.widget.bind("<Escape>", self.user_clicked_cancel)

    def create_behavior_buttons(self):
        if not self.buttons:
            if Dialog.Replies.Ok in self.buttons_labels:
                button = Button(
                    Dialog.Replies.Ok, user_event_callback=self.user_clicked_ok
                )
                self.buttons[Dialog.Replies.Ok] = button
            if Dialog.Replies.Cancel in self.buttons_labels:
                self.buttons[Dialog.Replies.Cancel] = Button(
                    Dialog.Replies.Cancel, user_event_callback=self.user_clicked_cancel
                )

        return self.buttons

    def user_clicked_ok(self, event, button=None):
        self.reply = Dialog.Replies.Ok
        self.widget.destroy()

    def user_clicked_cancel(self, event, button=None):
        self.reply = Dialog.Replies.Cancel
        self.widget.destroy()

    def user_timeout(self):
        self.reply = Dialog.Replies.Timedout
        self.widget.destroy()

    def run(self):
        if self.auto_click is not None:
            button = self.buttons[self.auto_click]
            if (
                self.auto_click == Dialog.Replies.Ok
            ):  # I am unable to get button.widget.invoke to work
                self.widget.after(500, lambda: self.user_clicked_ok(None, None))
            elif self.auto_click == Dialog.Replies.Cancel:
                self.widget.after(500, lambda: self.user_clicked_cancel(None, None))
        elif self.timeout is not None:
            self.widget.after(self.timeout, self.user_timeout)

        self.widget.grab_set()  # ensure all input goes to our window, including shortcut enter
        self.widget.wait_window()
        # breakpoint()
        return self.reply
