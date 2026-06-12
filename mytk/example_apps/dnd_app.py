"""dnd_app.py — drag files from Finder/Explorer onto the window.

Drop one or more files onto the label and their paths are listed. Demonstrates
`Base.accept_dropped_files`, which enables OS file drops on any myTk widget.

    python -m mytk.example_apps.dnd_app
"""

if __name__ == "__main__":
    from mytk import App, Label

    app = App(bring_to_front=True)
    app.window.widget.title("Drag & drop files here")

    label = Label("Drop files onto this window…", wrapping=True)
    label.grid_into(
        app.window, row=0, column=0, padx=40, pady=40, sticky="nsew"
    )
    app.window.row_resize_weight(0, 1)
    app.window.column_resize_weight(0, 1)

    def show(paths):
        label.text = "Dropped:\n" + "\n".join(paths)

    if not label.accept_dropped_files(show):
        label.text = "Drag-and-drop is not available in this environment."

    app.mainloop()
