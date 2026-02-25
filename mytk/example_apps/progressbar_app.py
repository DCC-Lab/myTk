"""
progressbar_app.py — Demonstrates three ways to update a ProgressBar in myTk.

1. Direct value assignment:         bar.value = 50
2. Model binding:                   model.bind_property_to_widget_value("progress", bar)
3. NotificationCenter notification: NotificationCenter().post_notification(...)
"""

import threading
import time

if __name__ == "__main__":
    from mytk import *
    from mytk.notificationcenter import NotificationCenter

    app = App(bring_to_front=True)
    app.window.widget.title("ProgressBar demo")

    # ── Method 1: direct value assignment ────────────────────────────────────
    Label("Method 1 — direct: bar.value = i").grid_into(
        app.window, row=0, column=0, pady=(20, 2), padx=20, sticky="w"
    )
    bar1 = ProgressBar(maximum=100)
    bar1.grid_into(app.window, row=1, column=0, pady=(0, 10), padx=20, sticky="ew")

    # ── Method 2: model binding ───────────────────────────────────────────────
    Label("Method 2 — binding: model.progress.set(i)").grid_into(
        app.window, row=2, column=0, pady=(10, 2), padx=20, sticky="w"
    )
    bar2 = ProgressBar(maximum=100)
    bar2.grid_into(app.window, row=3, column=0, pady=(0, 10), padx=20, sticky="ew")

    class Model(Bindable):
        def __init__(self):
            super().__init__()
            self.progress = DoubleVar(value=0)

    model = Model()
    model.bind_property_to_widget_value("progress", bar2)

    # ── Method 3: NotificationCenter ─────────────────────────────────────────
    Label("Method 3 — notification: post step=1").grid_into(
        app.window, row=4, column=0, pady=(10, 2), padx=20, sticky="w"
    )
    bar3 = ProgressBar(maximum=100)
    bar3.grid_into(app.window, row=5, column=0, pady=(0, 20), padx=20, sticky="ew")

    # ── Background task drives all three bars, then quits ────────────────────
    def background_task():
        for i in range(101):
            bar1.value = i
            model.progress.set(i)
            NotificationCenter().post_notification(
                ProgressBarNotification.step, None, user_info={"step": 1}
            )
            time.sleep(0.05)
        app.schedule_on_main_thread(app.quit)

    app.window.column_resize_weight(0, 1)
    thread = threading.Thread(target=background_task, daemon=True)
    thread.start()

    app.mainloop()
