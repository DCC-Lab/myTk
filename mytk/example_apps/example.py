from tkinter import DoubleVar
from tkinter import filedialog
import os

if __name__ == "__main__":
    # package_app_script()
    from mytk import *

    app = App(geometry="1450x900")
    # You would typically put this into the__init__ of your subclass of App:
    app.window.widget.title("Example application myTk")

    label1 = Label("This is centered in grid position (0,0)")
    label1.grid_into(app.window, column=0, row=0, pady=5, padx=5, sticky="")
    label2 = Label("This is top-aligned in grid position (0,1)")
    label2.grid_into(app.window, column=1, row=0, pady=5, padx=5, sticky="n")

    box1 = Box(label="This is a labelled box in grid (0,2)")
    box1.grid_into(app.window, column=2, row=0, pady=5, padx=5, sticky="nsew")
    
    thing1 = LabelledEntry(label="Centerd entry", character_width=5)
    thing1.grid_into(box1, column=0, row=0, padx=10)
    thing2 = LabelledEntry(label="Left-aligned entry", character_width=5)
    thing2.grid_into(box1, column=0, row=1, padx=5, sticky='w')

    # app.window.widget.grid_columnconfigure(1, weight=1)
    # entry1 = Entry()
    # entry1.grid_into(view, column=0, row=1, pady=5, padx=5, sticky="ew")
    # entry2 = Entry(text="initial text")
    # entry2.grid_into(view, column=0, row=2, pady=5, padx=5, sticky="ew")


    view = View(width=100, height=100)
    view.grid_into(app.window, column=0, row=1, pady=5, padx=5, sticky="nsew")
    view.grid_propagate(True)
    view.widget.grid_rowconfigure(0, weight=0)
    view.widget.grid_rowconfigure(1, weight=0)
    view.widget.grid_rowconfigure(2, weight=1)
    popup_label = Label(text='A popup menu')
    popup_label.grid_into(view, column=0, row=0, pady=5, padx=5, sticky="")
    popup = PopupMenu(menu_items=["Option 1", "Option 2", "Option 3"])
    popup.grid_into(view, column=1, row=0, pady=5, padx=5, sticky="")
    linked_label = Label(text='The label below is bound to the popup')
    linked_label.grid_into(view, column=0, columnspan=2, row=1, pady=5, padx=5, sticky="w")
    linked_label2 = Label(text='')
    linked_label2.grid_into(view, column=0, row=2, pady=5, padx=5, sticky="n")
    popup.bind_properties("value_variable", linked_label2, "value_variable")
    popup.selection_changed(0)
    def choose_file(event, button):
        filedialog.askopenfilename()
    button = Button("Choose file…", user_event_callback=choose_file)
    button.grid_into(view, column=0, row=3, pady=5, padx=5, sticky="n")

    view2 = View(width=100, height=100)
    view2.grid_into(app.window, column=1, row=1, pady=5, padx=5, sticky="nsew")
    view2.grid_propagate(True)
    view2.widget.grid_columnconfigure(0, weight=2)

    url1_label = Label(text='Links in labels are clickable:')
    url1_label.grid_into(view2, column=0, row=0, pady=5, padx=5)
    url1 = URLLabel("http://www.python.org")
    url1.grid_into(view2, column=1, row=0, pady=5, padx=5)

    url2_label = Label(text='Links in labels are clickable:')
    url2_label.grid_into(view2, column=0, row=1, pady=5, padx=5)
    url2 = URLLabel(url="http://www.python.org", text="The text can be something else")
    url2.grid_into(view2, column=1, row=1, pady=5, padx=5, sticky="nsew")

    example_dir = os.path.dirname(__file__)
    image = Image(os.path.join(example_dir, "logo.png"))
    image.grid_into(app.window, column=2, row=1, pady=5, padx=5, sticky="")

    box = Box("Some title on top of a box at grid position (1,0)")
    box.grid_into(app.window, column=3, row=0, pady=5, padx=5, sticky="ew")

    columns = {"column1": "Column #1", "name": "The name", "url": "Clickable URL"}
    table = TableView(columns_labels=columns)
    table.grid_into(app.window, column=3, row=0, pady=5, padx=5, sticky="ew")

    for i in range(20):
        table.data_source.append_record({"column1":"Item {0}".format(i), "name":"Something", "url":"http://www.python.org"})


    figure1 = Figure(figsize=(4, 3))
    figure1.grid_into(app.window, column=3, row=1, pady=5, padx=5)
    axis = figure1.figure.add_subplot()
    axis.plot([1, 2, 3], [4, 5, 6])
    axis.set_title("A matplotlib figure in grid position (3,1)")

    try:
        from matplotlib.figure import Figure as MPLFigure

        some_fig = MPLFigure(figsize=(4, 3))
        axis = some_fig.add_subplot()
        axis.plot([1, 2, 3], [-4, -5, -6])
        axis.set_title("You can provide your plt.figure")

        figure2 = Figure(figure=some_fig)
        figure2.grid_into(app.window, column=3, row=2, pady=5, padx=5)
    except :
        pass


    try:
        video = VideoView(device=0)
        video.zoom_level = 5
        video.grid_into(app.window, column=2, row=2, pady=5, padx=5, sticky="")
    except Exception as err:
        video = Label("Unable to load VideoView")
        video.grid_into(app.window, column=2, row=2, pady=5, padx=5, sticky="")

    def i_was_changed(checkbox):
        Dialog.showwarning(message="The checkbox was modified")

    view3 = View(width=100, height=100)
    view3.grid_into(app.window, column=0, row=2, pady=5, padx=5, sticky="nsew")
    view3.widget.grid_rowconfigure(0,weight=0)
    view3.widget.grid_rowconfigure(1,weight=0)
    view3.widget.grid_rowconfigure(2,weight=0)
    checkbox = Checkbox(label="Check me!", user_callback=i_was_changed)
    checkbox.grid_into(view3, column=0, row=0, pady=5, padx=5, sticky="nsew")
    slider = Slider(width=50)
    slider.grid_into(view3, column=0, row=1, pady=5, padx=5, sticky="nsew")
    slider.value_variable.set(0)
    indicator = NumericIndicator(value_variable=DoubleVar(value=0), format_string="Formatted slider value: {0:.1f}%")
    slider.bind_properties('value_variable', indicator, 'value_variable')
    indicator.grid_into(view3, column=0, row=2, pady=5, padx=5, sticky="nsew")
    level = Level()
    
    level.grid_into(view3, column=0, row=3, pady=5, padx=5, sticky="nsew")
    level.bind_properties('value_variable', slider, 'value_variable')
    # view3 = View(width=100, height=100)
    # view3.grid_into(app.window, column=0, row=0, pady=5, padx=5, sticky="nsew")

    canvas = CanvasView()
    canvas.grid_into(app.window, column=1, row=2, pady=5, padx=5, sticky="nsew")
    canvas.widget.create_rectangle(
            4, 4, 200, 200, outline="black", fill="white", width=2
        )
    canvas.widget.create_text((25,50), text="I can draw stuff!", anchor='w')
    canvas.widget.create_text((25,70), text="I can draw rect, ovals!", anchor='w')
    canvas.widget.create_rectangle(
            10, 10, 30, 30, outline="black", fill="blue", width=2
        )
    canvas.widget.create_oval(
            (140, 140, 140+40, 140+30), outline="green", fill="red", width=2
        )

    app.window.all_resize_weight(1)
    
    app.mainloop()
