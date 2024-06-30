import platform
from .modulesmanager import ModulesManager
from .bindable import *
from .window import *
from .dialog import Dialog

class App(Bindable):
    app = None

    def __init__(self, geometry=None, name="myTk App", help_url=None):
        super().__init__()

        self.name = name
        self.help_url = help_url
        self.window = Window(geometry)
        self.check_requirements()
        self.create_menu()
        App.app = self

    @property
    def root(self):
        return self.window.widget

    def check_requirements(self):
        mac_version = platform.mac_ver()[0]
        python_version = platform.python_version()

        if mac_version >= "14" and python_version < "3.12":
            Dialog.showwarning(
                message="It is recommended to use Python 3.12 on macOS 14 (Sonoma) with Tk.  If not, you will need to move the mouse while holding the button to register the click."
            )

    def mainloop(self):
        self.window.widget.mainloop()

    def create_menu(self):
        root = self.window.widget
        menubar = Menu(root)

        appmenu = Menu(menubar, name="apple")
        menubar.add_cascade(menu=appmenu)
        appmenu.add_command(label=f"About {self.name}", command=self.about)
        appmenu.add_command(label=f"Preferences", command=self.preferences)
        appmenu.add_separator()

        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label="Save…", command=self.save, accelerator="Command+S")
        filemenu.add_command(label="Quit", command=root.quit)
        menubar.add_cascade(label="File", menu=filemenu)
        editmenu = Menu(menubar, tearoff=0)
        editmenu.add_command(label="Undo", state="disabled")
        editmenu.add_separator()
        editmenu.add_command(label="Cut", state="disabled")
        editmenu.add_command(label="Copy", state="disabled")
        editmenu.add_command(label="Paste", state="disabled")
        editmenu.add_command(label="Select All", state="disabled")

        menubar.add_cascade(label="Edit", menu=editmenu)
        helpmenu = Menu(menubar, tearoff=0)
        if self.help_url is None:
            helpmenu.add_command(label="No help available", command=self.help, state="disabled")
        else:
            helpmenu.add_command(label="Documentation web site", command=self.help)

        menubar.add_cascade(label="Help", menu=helpmenu)

        root.config(menu=menubar)

    def reveal_path(self, path):
        import platform
        import subprocess

        try:
            if platform.system() == 'Windows':
                os.startfile(path)
            elif platform.system() == 'Darwin':
                subprocess.call(["open", path])
            else:
                subprocess.call(['xdg-open', path])
        except:
            Dialog.showerror(
                title=f"Unable to show {path}",
                message=f"An error occured when trying to reveal {path}",
            )

    def save(self):
        raise NotImplementedError("Implement save: in derived class")

    def preferences(self):
        raise NotImplementedError("Implement preferences: in derived class")

    def about(self, timeout=3000):
        Dialog.showinfo(title="About this App", 
                        message="Created with myTk: A simple user interface framework for busy scientists.\n\nhttps://github.com/DCC-Lab/myTk",
                        timeout=timeout)

    def help(self):
        ModulesManager.install_and_import_modules_if_absent({'webbrowser':'webbrowser'})
        webbrowser = ModulesManager.imported.get('webbrowser')
        if self.help_url is not None and webbrowser is not None:
            webbrowser.open(self.help_url)
        else:
            Dialog.showinfo( title="Help",
                             message="There is no help available for this Application.",
                             timeout=3000)

    def quit(self):
        self.root.quit()
