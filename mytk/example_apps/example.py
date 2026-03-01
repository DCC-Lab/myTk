from pathlib import Path
from tkinter import DoubleVar, filedialog

from mytk.canvasview import Arrow, CanvasLabel, Line, Oval, Rectangle
from mytk.vectors import Point

if __name__ == "__main__":
    # package_app_script()
    from mytk import *

    app = App(geometry="1350x720")
    app.window.widget.title("Example application myTk")

    label_box1 = Box(label="Label (centered)")
    label_box1.grid_into(app.window, column=0, row=0, pady=2, padx=3, sticky="nsew")
    label1 = Label("Centered label")
    label1.grid_into(label_box1, column=0, row=0, pady=2, padx=3, sticky="")

    label_box2 = Box(label="Label (top-aligned)")
    label_box2.grid_into(app.window, column=1, row=0, pady=2, padx=3, sticky="nsew")
    label2 = Label("Top-aligned label")
    label2.grid_into(label_box2, column=0, row=0, pady=2, padx=3, sticky="n")

    box1 = Box(label="Box / LabelledEntry")
    box1.grid_into(app.window, column=2, row=0, pady=2, padx=3, sticky="nsew")
    thing1 = LabelledEntry(label="Centered entry", character_width=5)
    thing1.grid_into(box1, column=0, row=0, padx=6)
    thing2 = LabelledEntry(label="Left-aligned entry", character_width=5)
    thing2.grid_into(box1, column=0, row=1, padx=4, sticky='w')

    view = Box(label="PopupMenu")
    view.grid_into(app.window, column=0, row=1, pady=2, padx=3, sticky="nsew")
    view.widget.grid_rowconfigure(0, weight=0)
    view.widget.grid_rowconfigure(1, weight=0)
    view.widget.grid_rowconfigure(2, weight=1)
    popup_label = Label(text='A popup menu')
    popup_label.grid_into(view, column=0, row=0, pady=2, padx=3, sticky="")
    popup = PopupMenu(menu_items=["Option 1", "Option 2", "Option 3"])
    popup.grid_into(view, column=1, row=0, pady=2, padx=3, sticky="")
    linked_label = Label(text='Label below is bound to the popup')
    linked_label.grid_into(view, column=0, columnspan=2, row=1, pady=2, padx=3, sticky="w")
    linked_label2 = Label(text='')
    linked_label2.grid_into(view, column=0, row=2, pady=2, padx=3, sticky="n")
    popup.bind_properties("value_variable", linked_label2, "value_variable")
    popup.selection_changed(0)
    def choose_file(event, button):
        filedialog.askopenfilename()
    button = Button("Choose file…", user_event_callback=choose_file)
    button.grid_into(view, column=0, row=3, pady=2, padx=3, sticky="n")

    view2 = Box(label="URLLabel")
    view2.grid_into(app.window, column=1, row=1, pady=2, padx=3, sticky="nsew")
    view2.widget.grid_columnconfigure(0, weight=2)
    url1_label = Label(text='Clickable links:')
    url1_label.grid_into(view2, column=0, row=0, pady=2, padx=3)
    url1 = URLLabel("http://www.python.org")
    url1.grid_into(view2, column=1, row=0, pady=2, padx=3)
    url2_label = Label(text='Custom link text:')
    url2_label.grid_into(view2, column=0, row=1, pady=2, padx=3)
    url2 = URLLabel(url="http://www.python.org", text="The Python website")
    url2.grid_into(view2, column=1, row=1, pady=2, padx=3, sticky="nsew")

    example_dir = Path(__file__).parent
    image_box = Box(label="Image")
    image_box.grid_into(app.window, column=2, row=1, pady=2, padx=3, sticky="")
    image = Image(example_dir / "logo.png")
    image.pil_image = image.pil_image.resize((66, 80), image.PILImage.LANCZOS)
    image.grid_into(image_box, column=0, row=0, pady=2, padx=3)

    table_box = Box(label="TableView")
    table_box.grid_into(app.window, column=3, row=0, pady=2, padx=3, sticky="nsew")

    columns = {"column1": "Column #1", "name": "The name", "url": "Clickable URL"}
    table = TableView(columns_labels=columns)
    table.grid_into(table_box, column=0, row=0, pady=10, padx=10, sticky="ew")
    for i in range(3):
        table.data_source.append_record({"column1": "Item {0}".format(i), "name": "Something", "url": "http://www.python.org"})
    table.widget.configure(height=3)
    table.widget.column("column1", width=70)
    table.widget.column("name", width=80)
    table.widget.column("url", width=120)

    figure1 = Figure(figsize=(3, 2))
    figure1.grid_into(app.window, column=3, row=1, pady=2, padx=3)
    axis = figure1.figure.add_subplot()
    axis.plot([1, 2, 3], [4, 5, 6])
    axis.set_title("Figure", fontsize=9)

    try:
        from matplotlib.figure import Figure as MPLFigure
        some_fig = MPLFigure(figsize=(3, 2))
        axis = some_fig.add_subplot()
        axis.plot([1, 2, 3], [-4, -5, -6])
        axis.set_title("Figure (external MPLFigure)", fontsize=9)
        figure2 = Figure(figure=some_fig)
        figure2.grid_into(app.window, column=3, row=2, pady=2, padx=3)
    except:
        pass

    video_box = Box(label="VideoView")
    video_box.grid_into(app.window, column=2, row=2, pady=2, padx=3, sticky="")
    try:
        video = VideoView(device=0, zoom_level=8)
        video.grid_into(video_box, column=0, row=0, pady=2, padx=3, sticky="")
    except Exception:
        video = Label("Unable to load VideoView")
        video.grid_into(video_box, column=0, row=0, pady=2, padx=3, sticky="")

    def i_was_changed(checkbox):
        Dialog.showwarning(message="The checkbox was modified")

    view3 = Box(label="Checkbox / Slider / Level")
    view3.grid_into(app.window, column=0, row=2, pady=2, padx=3, sticky="nsew")
    view3.widget.grid_rowconfigure(0, weight=0)
    view3.widget.grid_rowconfigure(1, weight=0)
    view3.widget.grid_rowconfigure(2, weight=0)
    checkbox = Checkbox(label="Check me!", user_callback=i_was_changed)
    checkbox.grid_into(view3, column=0, row=0, pady=2, padx=3, sticky="nsew")
    slider = Slider(width=50)
    slider.grid_into(view3, column=0, row=1, pady=2, padx=3, sticky="nsew")
    slider.value_variable.set(0)
    indicator = NumericIndicator(value_variable=DoubleVar(value=0), format_string="Slider: {0:.1f}%")
    slider.bind_properties('value_variable', indicator, 'value_variable')
    indicator.grid_into(view3, column=0, row=2, pady=2, padx=3, sticky="nsew")
    level = Level()
    level.grid_into(view3, column=0, row=3, pady=2, padx=3, sticky="nsew")
    level.bind_properties('value_variable', slider, 'value_variable')

    # --- CanvasView demo: raw API and CanvasElement API ---
    canvas_box = Box(label="CanvasView")
    canvas_box.grid_into(app.window, column=1, row=2, pady=2, padx=3, sticky="nsew")
    canvas = CanvasView(width=160, height=160)
    canvas.grid_into(canvas_box, column=0, row=0, pady=2, padx=3)

    # Raw canvas API
    canvas.widget.create_text(7, 7, text="Raw canvas API:", anchor='w', font=('Helvetica', 9, 'bold'))
    canvas.widget.create_rectangle(2, 16, 156, 71, outline="black", fill="white", width=1)
    canvas.widget.create_text(15, 30, text="Rectangles, ovals, text", anchor='w')
    canvas.widget.create_rectangle(8, 42, 30, 62, outline="black", fill="steelblue", width=2)
    canvas.widget.create_oval(38, 42, 69, 62, outline="darkgreen", fill="lightgreen", width=2)
    canvas.widget.create_text(77, 52, text="canvas.widget.*", anchor='w', font=('Helvetica', 8))

    # CanvasElement API (canvas.place())
    canvas.widget.create_text(7, 78, text="CanvasElement API:", anchor='w', font=('Helvetica', 9, 'bold'))
    rect_elem = Rectangle(size=(41, 20), outline="navy", fill="lightblue", width=2)
    canvas.place(rect_elem, position=Point(31, 100))
    oval_elem = Oval(size=(37, 20), outline="darkred", fill="lightyellow", width=2)
    canvas.place(oval_elem, position=Point(99, 100))
    arrow_elem = Arrow(start=Point(0, 0), end=Point(48, 0), fill="purple")
    canvas.place(arrow_elem, position=Point(10, 125))
    line_elem = Line(points=[Point(0, 0), Point(48, 0)], fill="gray", width=1, dash=(4, 2))
    canvas.place(line_elem, position=Point(78, 125))
    lbl_elem = CanvasLabel(font_size=8, text="canvas.place(element, pos)", anchor='w')
    canvas.place(lbl_elem, position=Point(7, 145))

    # --- Enable/Disable Box demo ---
    disable_view = Box(label="Box (disable/enable)")
    disable_view.grid_into(app.window, column=4, row=0, rowspan=3, pady=2, padx=3, sticky="nsew")
    disable_view.widget.grid_rowconfigure(0, weight=1)
    disable_view.widget.grid_rowconfigure(1, weight=0)

    demo_box = Box(label="Children can be disabled")
    demo_box.grid_into(disable_view, column=0, row=0, pady=2, padx=3, sticky="nsew")

    entry_in_box = LabelledEntry(label="An entry", character_width=8)
    entry_in_box.grid_into(demo_box, column=0, row=0, padx=8, pady=2, sticky='w')

    def noop(event, btn):
        pass
    button_in_box = Button("Click me", user_event_callback=noop)
    button_in_box.grid_into(demo_box, column=0, row=1, padx=8, pady=2)

    checkbox_in_box = Checkbox(label="A checkbox")
    checkbox_in_box.grid_into(demo_box, column=0, row=2, padx=8, pady=2, sticky='w')

    slider_in_box = Slider(width=100)
    slider_in_box.grid_into(demo_box, column=0, row=3, padx=8, pady=2, sticky='ew')
    slider_in_box.value_variable.set(40)

    popup_in_box = PopupMenu(menu_items=["Choice A", "Choice B", "Choice C"])
    popup_in_box.grid_into(demo_box, column=0, row=4, padx=8, pady=2)

    def toggle_disabled(event, btn):
        demo_box.is_disabled = not demo_box.is_disabled
        btn.widget.config(text="Enable box" if demo_box.is_disabled else "Disable box")

    toggle_btn = Button("Disable box", user_event_callback=toggle_disabled)
    toggle_btn.grid_into(disable_view, column=0, row=1, pady=(2, 8), padx=3)

    app.window.all_resize_weight(1)

    app.mainloop()
