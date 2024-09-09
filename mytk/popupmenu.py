from tkinter import StringVar, Menu
import tkinter.ttk as ttk
from functools import partial

from .base import Base


class PopupMenu(Base):
    def __init__(self, menu_items=None, user_callback=None):
        Base.__init__(self)

        self.selected_index = None
        self.user_callback = user_callback
        self.menu_items = menu_items
        self.menu = None

    @property
    def value(self):
        return self.value_variable.get()

    @value.setter
    def value(self, value):
        return self.value_variable.set(value=value)

    def create_widget(self, master):
        self.parent = master
        self.menu = Menu(master, tearoff=0)
        self.widget = ttk.Menubutton(master, text="-", menu=self.menu)
        if self.value_variable is None:
            self.value_variable = StringVar(value="Select menu item")

        self.bind_textvariable(self.value_variable)

        if self.menu_items is not None:
            self.add_menu_items(self.menu_items)

    def clear_menu_items(self):
        if self.widget is not None:
            self.menu.delete(0, "end")
        self.menu_items = []

    def add_menu_items(self, menu_items):
        self.menu_items = menu_items
        labels = menu_items
        for i, label in enumerate(labels):
            self.menu.add_command(
                label=label, command=partial(self.selection_changed, i)
            )

    def selection_changed(self, selected_index):
        self.selected_index = selected_index
        if selected_index is not None:
            self.value_variable.set(value=self.menu_items[self.selected_index])
        else:
            self.value_variable.set("")

        if self.user_callback is not None:
            self.user_callback(self, selected_index)

    def select_index(self, index):
        self.selection_changed(index)
