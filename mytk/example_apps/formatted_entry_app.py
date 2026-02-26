if __name__ == "__main__":
    from mytk import *
    from mytk.entries import FormattedEntry

    def make_row(parent, row, label_text, format_string, reverse_regex, initial_value):
        """Add a labelled FormattedEntry row and a kept-value readout."""
        Label(label_text).grid_into(parent, row=row, column=0, padx=8, pady=4, sticky="e")

        entry = FormattedEntry(
            value=initial_value,
            format_string=format_string,
            reverse_regex=reverse_regex,
            character_width=14,
        )
        entry.grid_into(parent, row=row, column=1, padx=8, pady=4)

        readout = Label("–")
        readout.grid_into(parent, row=row, column=2, padx=8, pady=4, sticky="w")
        entry.bind_property_to_widget_value("value", readout)

        return entry

    app = App(geometry="560x280")
    app.window.widget.title("FormattedEntry demo")

    box = Box(label="FormattedEntry — tab between fields to commit each value")
    box.grid_into(app.window, row=0, column=0, padx=10, pady=10, sticky="nsew")
    app.window.widget.grid_rowconfigure(0, weight=1)
    app.window.widget.grid_columnconfigure(0, weight=1)

    # Header labels
    Label("format string").grid_into(box, row=0, column=1, padx=8, pady=(6, 0))
    Label("kept value").grid_into(box, row=0, column=2, padx=8, pady=(6, 0))

    rows = [
        ("default  {0}",        r"{0}",          r"(.+)",                  3.14159),
        ("2 decimals  {0:.2f}", r"{0:.2f}",       r"([-+]?\d*\.?\d+)",     3.14159),
        ("4 decimals  {0:.4f}", r"{0:.4f}",       r"([-+]?\d*\.?\d+)",     3.14159),
        ("scientific  {0:.3e}", r"{0:.3e}",       r"([-+]?\d*\.?\d+[eE][-+]?\d+|[-+]?\d*\.?\d+)", 0.000314),
        ("percentage  {0:.1%}", r"{0:.1%}",       r"([-+]?\d*\.?\d+)",     0.856),
    ]

    for i, (label, fmt, regex, val) in enumerate(rows):
        make_row(box, row=i + 1, label_text=label, format_string=fmt,
                 reverse_regex=regex, initial_value=val)

    app.mainloop()
