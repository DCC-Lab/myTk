import envapp
from tkinter import DoubleVar
from tkinter import filedialog
from mytk import *
from mytk.canvasview import *
from mytk.dataviews import *
from mytk.vectors import Point, PointDefault
from mytk.labels import Label

import time
from numpy import linspace, isfinite
from raytracing import *
import colorsys


class CanvasApp(App):
    def __init__(self):
        App.__init__(self, name="Raytracing Application")
        self.window.widget.title("Raytracing")

        self.number_of_heights = 5
        self.max_height = 5
        self.number_of_angles = 5
        self.max_fan_angle = 0.1
        self.dont_show_blocked_rays = True
        self.show_raytraces = True
        self.show_apertures = True
        self.show_labels = True
        self.show_principal_rays = True
        self.show_conjugates = True
        self.show_intermediate_conjugates = False
        self.maximum_x = 60

        self.table_group = View(width=300, height=300)
        self.table_group.grid_into(
            self.window, row=0, column=1, pady=5, padx=5, sticky="nsew"
        )
        self.table_group.column_resize_weight(index=0, weight=1)

        self.button_group = View(width=300, height=200)
        self.button_group.grid_into(
            self.table_group, row=1, column=0, pady=5, padx=5, sticky="nsew"
        )

        self.add_lens_button = Button(
            "Add Lens", user_event_callback=self.click_table_buttons
        )
        self.add_lens_button.grid_into(self.button_group, row=0, column=0, pady=5, padx=5)
        self.add_aperture_button = Button(
            "Add Aperture", user_event_callback=self.click_table_buttons
        )
        self.add_aperture_button.grid_into(self.button_group, row=0, column=1, pady=5, padx=5)

        self.delete_button = Button(
            "Delete element", user_event_callback=self.click_table_buttons
        )
        self.delete_button.grid_into(self.button_group, row=0, column=2, pady=5, padx=5)

        self.tableview = TableView(
            columns_labels={
                "element": "Element",
                "focal_length": "Focal length [mm]",
                "diameter": "Diameter [mm]",
                "position": "Position [mm]",
                "label": "Label",
            }
        )

        self.tableview.grid_into(
            self.table_group,
            column=0,
            row=0,
            columnspan=2,
            pady=5,
            padx=5,
            sticky="nsew",
        )
        self.tableview.displaycolumns = [
            "element",
            "position",
            "focal_length",
            "diameter",
            "label",
        ]
        for column in self.tableview.displaycolumns:
            self.tableview.widget.column(column, width=50, anchor=W)

        self.tableview.data_source.append_record(
            {
                "element": "Lens",
                "focal_length": 100,
                "diameter": 25.4,
                "position": 100,
                "label": "L1",
            }
        )
        self.tableview.data_source.append_record(
            {
                "element": "Lens",
                "focal_length": 50,
                "diameter": 25.4,
                "position": 300,
                "label": "L2",
            }
        )
        self.tableview.data_source.append_record(
            {
                "element": "Aperture",
                "focal_length": "",
                "diameter": 30,
                "position": 400,
                "label": "Aperture",
            }
        )
        self.tableview.delegate = self

        self.controls = Box(label="Display", width=200)
        self.controls.grid_into(
            self.window, column=0, row=0, columnspan=1, pady=5, padx=5, sticky="nsew"
        )

        self.control_input_rays = Box(label="Input ray", width=200)
        self.control_input_rays.grid_into(
            self.controls, column=0, row=0, columnspan=1, pady=5, padx=5, sticky="nsew"
        )

        self.number_heights_label = Label(text="# ray heights:")
        self.number_heights_label.grid_into(
            self.control_input_rays, column=0, row=0, pady=5, padx=5, sticky="w"
        )

        self.number_heights_entry = IntEntry(minimum=2, maximum=100, width=3)
        self.number_heights_entry.grid_into(
            self.control_input_rays, column=1, row=0, pady=5, padx=5, sticky="w"
        )

        self.number_angles_label = Label(text="# ray angles:")
        self.number_angles_label.grid_into(
            self.control_input_rays, column=0, row=1, pady=5, padx=5, sticky="w"
        )

        self.number_angles_entry = IntEntry(minimum=2, maximum=100, width=3)
        self.number_angles_entry.grid_into(
            self.control_input_rays, column=1, row=1, pady=5, padx=5, sticky="w"
        )

        self.max_heights_label = Label(text="Max height:")
        self.max_heights_label.grid_into(
            self.control_input_rays, column=3, row=0, pady=5, padx=5, sticky="w"
        )

        self.max_heights_entry = Entry(character_width=3)
        self.max_heights_entry.grid_into(
            self.control_input_rays, column=4, row=0, pady=5, padx=5, sticky="w"
        )

        self.fan_angles_label = Label(text="Max angle:")
        self.fan_angles_label.grid_into(
            self.control_input_rays, column=3, row=1, pady=5, padx=5, sticky="w"
        )

        self.fan_angles_entry = Entry(character_width=3)
        self.fan_angles_entry.grid_into(
            self.control_input_rays, column=4, row=1, pady=5, padx=5, sticky="w"
        )

        self.show_conjugates_checkbox = Checkbox(label="Show object/image planes")
        self.show_conjugates_checkbox.grid_into(
            self.controls, column=0, row=1, columnspan=4, pady=5, padx=5, sticky="w"
        )

        self.principal_rays_checkbox = Checkbox(
            label="Show principal rays [blue: chief, red: axial]"
        )
        self.principal_rays_checkbox.grid_into(
            self.controls, column=0, row=2, columnspan=4, pady=5, padx=5, sticky="w"
        )

        self.apertures_checkbox = Checkbox(
            label="Show Aperture stop (AS) and field stop (FS)"
        )
        self.apertures_checkbox.grid_into(
            self.controls, column=0, row=3, columnspan=4, pady=5, padx=5, sticky="w"
        )

        self.show_labels_checkbox = Checkbox(label="Show object labels")
        self.show_labels_checkbox.grid_into(
            self.controls, column=0, row=4, columnspan=4, pady=5, padx=5, sticky="w"
        )

        self.blocked_rays_checkbox = Checkbox(label="Do not show blocked rays")
        self.blocked_rays_checkbox.grid_into(
            self.controls, column=0, row=5, columnspan=4, pady=5, padx=5, sticky="w"
        )

        self.canvas = CanvasView(width=1000, height=400, background="white")
        self.canvas.grid_into(
            self.window, column=0, row=1, columnspan=2, pady=5, padx=5, sticky="nsew"
        )
        self.window.column_resize_weight(index=0, weight=0)
        self.window.column_resize_weight(index=1, weight=1)
        self.coords_origin = Point(50, 200)

        self.coords = XYCoordinateSystemElement(
            size=(700, -200), axes_limits=((0, 400), (-25, 25)), width=2
        )
        self.canvas.place(self.coords, position=self.coords_origin)
        optics_basis = self.coords.basis

        self.bind_properties(
            "number_of_heights", self.number_heights_entry, "value_variable"
        )
        self.bind_properties(
            "number_of_angles", self.number_angles_entry, "value_variable"
        )
        # self.bind_properties('maximum_x', self.maximum_x_entry, 'value_variable')
        self.bind_properties(
            "dont_show_blocked_rays", self.blocked_rays_checkbox, "value_variable"
        )
        self.bind_properties(
            "show_apertures", self.apertures_checkbox, "value_variable"
        )
        self.bind_properties("show_labels", self.show_labels_checkbox, "value_variable")
        self.bind_properties(
            "show_principal_rays", self.principal_rays_checkbox, "value_variable"
        )
        self.bind_properties(
            "show_conjugates", self.show_conjugates_checkbox, "value_variable"
        )
        self.bind_properties("max_height", self.max_heights_entry, "value_variable")
        self.bind_properties("max_fan_angle", self.fan_angles_entry, "value_variable")
        self.number_heights_entry.bind_properties(
            "is_disabled", self, "show_principal_rays"
        )
        self.number_angles_entry.bind_properties(
            "is_disabled", self, "show_principal_rays"
        )
        self.max_heights_entry.bind_properties(
            "is_disabled", self, "show_principal_rays"
        )
        self.fan_angles_entry.bind_properties(
            "is_disabled", self, "show_principal_rays"
        )

        self.add_observer(self, "number_of_heights")
        self.add_observer(self, "number_of_angles")
        # self.add_observer(self, 'maximum_x', context='refresh_graph')
        self.add_observer(self, "dont_show_blocked_rays")
        self.add_observer(self, "show_apertures")
        self.add_observer(self, "show_principal_rays")
        self.add_observer(self, "show_labels")
        self.add_observer(self, "show_conjugates")

        # a = Arc(radius=100)
        # a.create(self.canvas, position=self.coords_origin + Point(10, 0, basis=self.coords.basis))

        self.refresh()

    def observed_property_changed(
        self, observed_object, observed_property_name, new_value, context
    ):
        super().observed_property_changed(
            observed_object, observed_property_name, new_value, context
        )
        if context == "refresh_graph":
            self.canvas.widget.delete(self.coords.id)
            self.coords.axes_limits = ((0, float(self.maximum_x)), (-50, 50))

        self.refresh()

    def save_to_pdf(self):
        self.canvas.save_to_pdf(filepath="/tmp/file.pdf")

    def source_data_changed(self):
        self.refresh()

    def click_table_buttons(self, event, button):
        if button == self.delete_button:
            for selected_item in self.tableview.widget.selection():
                record = self.tableview.data_source.record(selected_item)
                self.tableview.data_source.remove_record(selected_item)
        elif button == self.add_lens_button:
            record = self.tableview.data_source.empty_record()
            record["position"] = 50
            record["element"] = "Lens"
            record["focal_length"] = 50
            record["diameter"] = 25.4
            self.tableview.data_source.append_record(record)
        elif button == self.add_aperture_button:
            record = self.tableview.data_source.empty_record()
            record["position"] = 50
            record["element"] = "Aperture"
            record["diameter"] = 25.4
            self.tableview.data_source.append_record(record)

    def refresh(self):
        try:
            self.canvas.widget.delete("ray")
            self.canvas.widget.delete("optics")
            self.canvas.widget.delete("apertures")
            self.canvas.widget.delete("labels")
            self.canvas.widget.delete("conjugates")

            path = self.get_path_from_ui()

            self.create_optical_path(path, self.coords)

            if self.show_raytraces:
                self.create_all_traces(path)

            if self.show_conjugates:
                self.create_conjugate_planes(path)

            if self.show_apertures:
                self.create_apertures_labels(path)

            if self.show_labels:
                self.create_object_labels(path)
        except ValueError as err:
            print(err)

    def create_all_traces(self, path):
        if self.show_principal_rays:
            principal_ray = path.principalRay()
            if principal_ray is not None:
                principal_raytrace = path.trace(principal_ray)
                line_trace = self.create_line_from_raytrace(
                    principal_raytrace, basis=self.coords.basis, color="green"
                )
                self.coords.place(line_trace, position=Point(0, 0))

                axial_ray = path.axialRay()
                axial_raytrace = path.trace(axial_ray)
                line_trace = self.create_line_from_raytrace(
                    axial_raytrace, basis=self.coords.basis, color="red"
                )
                self.coords.place(line_trace, position=Point(0, 0))

        else:
            M = int(self.number_of_heights)
            N = int(self.number_of_angles)
            yMax = float(self.max_height)
            thetaMax = float(self.max_fan_angle)

            rays = UniformRays(yMax=yMax, thetaMax=thetaMax, M=M, N=N)
            self.create_raytraces_lines(path, rays)

    def create_conjugate_planes(self, path):
        arrow_width = 10
        object_z = 0
        object_height = float(self.max_height)*2
        if self.show_principal_rays:
            object_height = path.fieldOfView()

        basis = self.coords.basis
        canvas_object = Arrow(
            start=Point(object_z, -object_height / 2, basis=basis),
            end=Point(object_z, object_height / 2, basis=basis),
            fill="blue",
            width=arrow_width,
            tag=('conjugates')
        )
        self.coords.place(canvas_object, position=Point(0, 0))

        conjugate = path.forwardConjugate()
        image_z = conjugate.transferMatrix.L
        magnification = conjugate.transferMatrix.magnification().transverse
        image_height = magnification * object_height
        canvas_image = Arrow(
            start=Point(image_z, -image_height / 2, basis=basis),
            end=Point(image_z, image_height / 2, basis=basis),
            fill="red",
            width=arrow_width,
            tag=('conjugates')
        )
        self.coords.place(canvas_image, position=Point(0, 0))

    def create_apertures_labels(self, path):
        position = path.apertureStop()
        y_lims = self.coords.axes_limits[1]
        label_position = y_lims[1] * 1.4

        if position.z is not None:
            aperture_stop_label = CanvasLabel(text="AS", tag=("apertures"))
            self.coords.place(
                aperture_stop_label, position=Point(position.z, label_position)
            )

        position = path.fieldStop()
        if position.z is not None:
            field_stop_label = CanvasLabel(text="FS", tag=("apertures"))
            self.coords.place(
                field_stop_label, position=Point(position.z, label_position)
            )

    def create_object_labels(self, path):
        z = 0
        y_lims = self.coords.axes_limits[1]
        label_position = y_lims[1] * 1.1
        for element in path:
            label = CanvasLabel(text=element.label, tag=("labels"))
            self.coords.place(label, position=Point(z, label_position))
            z += element.L

    def create_raytraces_lines(self, path, rays):
        raytraces = path.traceMany(rays)

        if self.dont_show_blocked_rays:
            raytraces_to_show = [
                raytrace for raytrace in raytraces if not raytrace[-1].isBlocked
            ]
        else:
            raytraces_to_show = raytraces

        line_traces = self.raytraces_to_lines(raytraces_to_show, self.coords.basis)

        for line_trace in line_traces:
            self.canvas.place(line_trace, position=self.coords_origin)
            self.canvas.widget.tag_lower(line_trace.id)

    def create_optical_path(self, path, coords):
        z = 0
        for element in path:
            if isinstance(element, Lens):
                diameter = element.apertureDiameter
                if not isfinite(diameter):
                    diameter = 90

                lens = Oval(
                    size=(5, diameter),
                    basis=coords.basis,
                    position_is_center=True,
                    fill="light blue",
                    outline="black",
                    width=2,
                    tag=("optics"),
                )
                coords.place(lens, position=Point(z, 0, basis=coords.basis))
            elif isinstance(element, Aperture):
                diameter = element.apertureDiameter
                if not isfinite(diameter):
                    diameter = 90

                thickness = 3
                aperture_top = Line(
                    points=(
                        Point(-thickness, diameter / 2, basis=coords.basis),
                        Point(thickness, diameter / 2, basis=coords.basis),
                    ),
                    fill="black",
                    width=4,
                    tag=("optics"),
                )
                coords.place(aperture_top, position=Point(z, 0, basis=coords.basis))
                aperture_bottom = Line(
                    points=(
                        Point(-thickness, -diameter / 2, basis=coords.basis),
                        Point(thickness, -diameter / 2, basis=coords.basis),
                    ),
                    fill="black",
                    width=4,
                    tag=("optics"),
                )
                coords.place(aperture_bottom, position=Point(z, 0, basis=coords.basis))

            z += element.L

    def raytraces_to_lines(self, raytraces, basis):
        line_traces = []

        all_initial_y = [raytrace[0].y for raytrace in raytraces]
        max_y = max(all_initial_y)
        min_y = min(all_initial_y)

        with PointDefault(basis=basis):
            for raytrace in raytraces:
                initial_y = raytrace[0].y
                hue = (initial_y - min_y) / float(max_y - min_y)
                color = self.color_from_hue(hue)

                line_trace = self.create_line_from_raytrace(
                    raytrace, basis=basis, color=color
                )
                line_traces.append(line_trace)

        return line_traces

    def create_line_from_raytrace(self, raytrace, basis, color):
        points = [Point(r.z, r.y, basis=basis) for r in raytrace]
        return Line(points, tag=("ray"), fill=color, width=2)

    def color_from_hue(self, hue):
        rgb = colorsys.hsv_to_rgb(hue, 1, 1)
        rgbi = (int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))
        return "#{0:02x}{1:02x}{2:02x}".format(*rgbi)

    def get_path_from_ui(self):
        path = ImagingPath()

        z = 0
        ordered_records = self.tableview.data_source.records
        ordered_records.sort(key=lambda e: float(e["position"]))

        for element in ordered_records:
            if element["element"] == "Lens":
                focal_length = float(element["focal_length"])
                label = element["label"]
                next_z = float(element["position"])
                diameter = float("+inf")
                if element["diameter"] != "":
                    diameter = float(element["diameter"])

                path_element = Lens(f=focal_length, diameter=diameter, label=label)
            elif element["element"] == "Aperture":
                label = element["label"]
                next_z = float(element["position"])
                diameter = float("+inf")
                if element["diameter"] != "":
                    diameter = float(element["diameter"])
                path_element = Aperture(diameter=diameter, label=label)
            else:
                print(f"Unable to include unknown element {element['element']}")

            delta = next_z - z
            path.append(Space(d=delta))
            path.append(path_element)
            z += delta

        if self.show_conjugates or self.show_principal_rays:
            conjugate = path.forwardConjugate()
            image_z = conjugate.transferMatrix.L
            if image_z > z:
                path.append(Space(d=image_z-z))
        else:
            max_x = self.coords.axes_limits[0][1]
            if max_x > z:
                path.append(Space(d=max_x-z))


        # path.append(Space(d=10))

        return path


if __name__ == "__main__":
    app = CanvasApp()

    app.mainloop()
