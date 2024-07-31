import tkinter.ttk as ttk

from .modulesmanager import ModulesManager
from .app import App
from .base import Base
from .button import Button
from .popupmenu import PopupMenu
import importlib
import signal
import cv2
import PIL.Image as PILImage
import PIL.ImageTk as PILImageTk
import time
from threading import Thread, RLock
from functools import partial
from contextlib import redirect_stdout, redirect_stderr
import io

class VideoCapture:
    def __init__(self, device_id=0, delegate=None):
        super().__init__()

        self.device_id = device_id
        self.delegate = delegate

        self.thread = None
        self.camera_access_lock = RLock()

        # These variables must be accessed with the RLock()
        self.latest_frame = None
        self._frame_counter = 0
        self.capture = None
        self.videowriter = None
        self.zoom_level = 1
        self._must_abort = False
        self.previous_handler = signal.signal(signal.SIGINT, self.signal_handler)

    @property
    def frame_counter(self):
        with self.camera_access_lock:
            return self._frame_counter

    @property
    def is_running(self):
        with self.camera_access_lock:
            return self.capture is not None

    @property
    def must_abort(self):
        with self.camera_access_lock:
            return self._must_abort

    @must_abort.setter
    def must_abort(self, value):
        with self.camera_access_lock:
            self._must_abort = value

    def signal_handler(self, sig, frame):
        print(f"Handling signal {sig} ({signal.Signals(sig).name}).")
        if sig == signal.SIGINT:
            if self.is_running:
                self.abort = True
            else:
                self.previous_handler(sig, frame)

    @classmethod
    def available_devices(cls):
        available_devices = []
        try:
            index = 0
            while True:
                with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()) as err:
                    cap = cv2.VideoCapture(index)
                    time.sleep(0.3) # HACK? not always available immediately
                    if not cap.read()[0]:
                        break
                    else:
                        available_devices.append(index)
                    cap.release()
                index += 1
        except Exception as err:
            print(err)
            pass

        return available_devices

    def start_capturing(self, run_continuously = False):
        with self.camera_access_lock:
            if not self.is_running:
                try:
                    self._frame_counter = 0
                    with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()) as err:
                        self.capture = cv2.VideoCapture(self.device_id)

                    if run_continuously:
                        self.thread = Thread(target=self.background_thread_get_next_frame)
                        self.thread.start()
                except Exception as err:
                    print(err)
                    self.capture = None

    def stop_capturing(self):
        if self.thread is not None:
            self.must_abort = True
            self.thread.join()
            self.thread = None

        if self.is_running:
            with self.camera_access_lock:
                self.capture.release()
                self.capture = None
                

    def start_streaming(self, filepath):
        with self.camera_access_lock:
            width = self.get_prop_id(cv2.CAP_PROP_FRAME_WIDTH)
            height = self.get_prop_id(cv2.CAP_PROP_FRAME_HEIGHT)
            fourcc = cv2.VideoWriter_fourcc("I", "4", "2", "0")
            self.videowriter = cv2.VideoWriter(
                filepath, fourcc, 20.0, (int(width), int(height)), True
            )

    def stop_streaming(self):
        with self.camera_access_lock:
            if self.videowriter is not None:
                self.videowriter.release()
                self.videowriter = None

    def background_thread_get_next_frame(self):
        while not self.must_abort:
            with self.camera_access_lock:
                latest_frame = self.get_next_frame()
                if latest_frame is not None:
                    if self.delegate is not None:
                        self.delegate.frame_ready(latest_frame)                        
                else:
                    break

            time.sleep(0.005)

    def get_next_frame(self):
        with self.camera_access_lock:
            if self.capture is None:
                return None

            ret, readonly_frame = self.capture.read() # blocking until frame is available

            frame = None
            if ret:
                # The OpenCV documentation is clear: the returned frame from read() is read-only
                # and must be copied to be used (I assume it can be overwritten internally)
                # https://docs.opencv.org/3.4/d8/dfe/classcv_1_1VideoCapture.html#a473055e77dd7faa4d26d686226b292c1
                # Without this copy, the program crashes in a few seconds
                frame = readonly_frame.copy()

                if len(frame.shape) == 3:
                    if frame.shape[2] == 3:
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        # frame = cv.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                self._frame_counter += 1

            return frame


    def prop_ids(self):
        with self.camera_access_lock:
            capture = self.capture
            print(
                "CV_CAP_PROP_FRAME_WIDTH: '{}'".format(
                    capture.get(cv2.CAP_PROP_FRAME_WIDTH)
                )
            )
            print(
                "CV_CAP_PROP_FRAME_HEIGHT : '{}'".format(
                    capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
                )
            )
            print("CAP_PROP_FPS : '{}'".format(capture.get(cv2.CAP_PROP_FPS)))
            print(
                "CAP_PROP_POS_MSEC : '{}'".format(capture.get(cv2.CAP_PROP_POS_MSEC))
            )
            print(
                "CAP_PROP_FRAME_COUNT  : '{}'".format(
                    capture.get(cv2.CAP_PROP_FRAME_COUNT)
                )
            )
            print(
                "CAP_PROP_BRIGHTNESS : '{}'".format(
                    capture.get(cv2.CAP_PROP_BRIGHTNESS)
                )
            )
            print(
                "CAP_PROP_CONTRAST : '{}'".format(capture.get(cv2.CAP_PROP_CONTRAST))
            )
            print(
                "CAP_PROP_SATURATION : '{}'".format(
                    capture.get(cv2.CAP_PROP_SATURATION)
                )
            )
            print("CAP_PROP_HUE : '{}'".format(capture.get(cv2.CAP_PROP_HUE)))
            print("CAP_PROP_GAIN  : '{}'".format(capture.get(cv2.CAP_PROP_GAIN)))
            print(
                "CAP_PROP_CONVERT_RGB : '{}'".format(
                    capture.get(cv2.CAP_PROP_CONVERT_RGB)
                )
            )

    def get_prop_id(self, prop_id):
        """
        Important prop_id:
        CAP_PROP_POS_MSEC Current position of the video file in milliseconds or video capture timestamp.
        CAP_PROP_POS_FRAMES 0-based index of the frame to be decoded/captured next.
        CAP_PROP_FRAME_WIDTH Width of the frames in the video stream.
        CAP_PROP_FRAME_HEIGHT Height of the frames in the video stream.
        CAP_PROP_FPS Frame rate.
        CAP_PROP_FOURCC 4-character code of codec.
        CAP_PROP_FORMAT Format of the Mat objects returned by retrieve() .
        CAP_PROP_MODE Backend-specific value indicating the current capture mode.
        CAP_PROP_CONVERT_RGB Boolean flags indicating whether images should be converted to RGB.
        """
        with self.camera_access_lock:
            if self.capture is not None:
                return self.capture.get(prop_id)
            return None

class VideoView(Base):

    def __init__(self, device=0, zoom_level=3, auto_start=True):
        super().__init__()

        self.new_frame = None
        self.image = None

        self.capture = VideoCapture(device_id=device)
        self.zoom_level = zoom_level
        self.auto_start = auto_start

        self.startstop_behaviour_button = None
        self.save_behaviour_button = None
        self.stream_behaviour_button = None

        self.histogram_xyplot = None

        self._displayed_tkimage = None
        self.next_scheduled_update = None
        self.next_scheduled_update_histogram = None
        self.bind_event('<<FrameReady>>', self.update_display)

    def is_environment_valid(self):
        ModulesManager.install_and_import_modules_if_absent(
            {"opencv-python": "cv2", "Pillow": "PIL"}
        )

        cv2 = ModulesManager.imported.get("opencv-python", None)
        self.PIL = ModulesManager.imported.get("Pillow", None)

        if self.PIL is not None:
            PILImage = importlib.import_module("PIL.Image")
            PILImageTk = importlib.import_module("PIL.ImageTk")

        return all(
            v is not None for v in [cv2, self.PIL, PILImage, PILImageTk]
        )

    def create_widget(self, master):
        self.widget = ttk.Label(master, borderwidth=2, relief="groove")
        if self.auto_start:
            self.start_capturing()

    @property
    def is_running(self):
        return self.capture is not None

    @property
    def startstop_button_label(self):
        if self.is_running:
            return "Stop"
        return "Start"

    def frame_ready(self, frame):
        self.new_frame = frame
        self.generate_event("<<FrameReady>>")


    def update_display(self):
        img = PILImage.fromarray(self.new_frame)
        resized_image = img.resize(
            (img.width // int(self.zoom_level), img.height // int(self.zoom_level)),
            PILImage.NEAREST,
        )
        self.image = resized_image

        # convert to Tkinter image
        photo = PILImageTk.PhotoImage(image=self.image)

        # solution for bug in `PhotoImage`
        self._displayed_tkimage = photo

        # replace image in label
        self.widget.configure(image=photo)

        if self.next_scheduled_update_histogram is None:
            self.update_histogram()

    def update_histogram(self):
        if self.histogram_xyplot is not None:
            self.histogram_xyplot.clear_plot()
            values = self.image.histogram()
            bins_per_channel = len(values) // 3
            decimate = 8
            self.histogram_xyplot.x = list(range(bins_per_channel // decimate))
            self.histogram_xyplot.y.append(values[0:bins_per_channel:decimate])
            self.histogram_xyplot.y.append(
                values[bins_per_channel : 2 * bins_per_channel : decimate]
            )
            self.histogram_xyplot.y.append(values[2 * bins_per_channel :: decimate])

            self.histogram_xyplot.update_plot()

            self.next_scheduled_update_histogram = App.app.root.after(
                100, self.update_histogram
            )

    def create_behaviour_popups(self):
        popup_camera = PopupMenu(
            menu_items=VideoView.available_devices(),
            user_callback=self.camera_selection_changed,
        )

        self.bind_popup_to_camera_selection_behaviour(popup_camera)

        return popup_camera

    def create_behaviour_buttons(self):
        start_button = Button(self.startstop_button_label)
        save_button = Button("Save…")
        stream_button = Button("Stream to disk…")

        self.bind_button_to_startstop_behaviour(start_button)
        self.bind_button_to_save_behaviour(save_button)
        self.bind_button_to_stream_behaviour(stream_button)

        return start_button, save_button, stream_button

    def bind_button_to_startstop_behaviour(self, button):
        button.user_event_callback = self.click_start_stop_button

    def bind_button_to_save_behaviour(self, button):
        button.user_event_callback = self.click_save_button

    def bind_button_to_stream_behaviour(self, button):
        button.user_event_callback = self.click_stream_button

    def bind_popup_to_camera_selection_behaviour(self, popup):
        popup.user_event_callback = self.camera_selection_changed

    def click_start_stop_button(self, event, button):
        if self.is_running:
            self.capture.stop_capturing()
        else:
            self.capture.start_capturing()
        button.widget.configure(text=self.startstop_button_label)

    def click_save_button(self, event, button):
        exts = PILImage.registered_extensions()
        supported_extensions = [
            (f, ex) for ex, f in exts.items() if f in PILImage.SAVE
        ]

        filepath = filedialog.asksaveasfilename(
            parent=button.widget,
            title="Choose a filename:",
            filetypes=supported_extensions,
        )
        if filepath:
            self.image.save(filepath)

    def click_stream_button(self, event, button):
        filepath = filedialog.asksaveasfilename(
            parent=button.widget,
            title="Choose a filename for movie:",
            filetypes=[("AVI", ".avi")],
        )
        if filepath:
            self.start_streaming(filepath)

    def camera_selection_changed(self, index):
        self.stop_capturing()
        self.device = index
        self.start_capturing()

