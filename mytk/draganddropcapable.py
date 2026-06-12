"""Drag-and-drop mixin class for widget behavior.

Provides the `DragAndDropCapable` class, a mixin designed to add OS-level
drag-and-drop (files dropped from the system file manager) to GUI widgets that
expose a `widget` attribute compatible with `tk.Widget`. It mirrors
`EventCapable`: a small mixin combined into `Base`, never used on its own.

OS drag-and-drop is not part of core Tk; the heavy lifting (loading the tkdnd
extension onto the window and parsing the dropped payload) lives in `mytk.dnd`.
This mixin is the per-widget API on top of it.
"""

from .dnd import dropped_paths, ensure_tkdnd
from .eventcapable import HasWidget


class DragAndDropCapable:
    """Mixin adding drag-and-drop methods for classes exposing a `widget`.

    Designed to be used alongside base classes that define `self.widget` as a
    `tk.Widget` (and, like the dropped-file callback here, alongside
    `EventCapable` for `self.after`). This class should not be used on its own.

    Responsibilities:
    - Checking whether drag-and-drop can be enabled (`is_drag_and_drop_available`)
    - Registering a widget as a target for dropped files (`accept_dropped_files`)
    """

    widget: "object"  # Hint for static type checkers; a tk.Widget at runtime

    def __init__(self, *args, **kwargs):
        """Initialize internal drop state for cooperative multiple inheritance."""
        self._drop_callbacks = []  # keep strong refs to registered callbacks
        super().__init__()  # cooperative!

    def _valid_mixin_class(self):
        """Ensures that `self.widget` exists before performing widget operations.

        Raises:
            AttributeError: If `self` does not define a `widget` attribute.
        """
        if not isinstance(self, HasWidget):
            raise AttributeError(
                f"DragAndDropCapable requires {self.__class__.__name__} to "
                f"provide a 'widget' attribute"
            )

    def is_drag_and_drop_available(self):
        """Whether OS drag-and-drop can be enabled on this widget's window.

        Loads the tkdnd extension on first call (pulling in the optional
        `tkinterdnd2` dependency); returns False if it cannot be enabled.
        """
        self._valid_mixin_class()
        if self.widget is None:
            return False
        return ensure_tkdnd(self.widget.winfo_toplevel()) is not None

    def accept_dropped_files(self, callback):
        """Accept files dropped onto this widget from the OS file manager.

        ``callback(paths)`` is invoked on each drop with a list of filesystem
        paths. Every dropped file is delivered — it is up to the callback to try
        to use them and report anything it cannot handle. Call this after the
        widget exists (e.g. after grid_into / pack_into / place_into).

        Returns True if drag-and-drop is available in this environment, or False
        if it could not be enabled — in which case the widget keeps working,
        just without drops. Enabling it pulls in the optional ``tkinterdnd2``
        dependency on first use (see :mod:`mytk.dnd`).
        """
        self._valid_mixin_class()
        if self.widget is None:
            raise RuntimeError(
                "accept_dropped_files() needs the widget to exist; place it "
                "(grid_into/pack_into/place_into) first."
            )
        root = self.widget.winfo_toplevel()
        tkdnd = ensure_tkdnd(root)
        if tkdnd is None:
            return False
        self._drop_callbacks.append(callback)

        def on_drop(event):
            # Run the callback on the next event-loop tick (via the tracked
            # self.after), not inline: the OS drag is still in progress during
            # <<Drop>>, so a callback that blocks (e.g. opens a modal dialog)
            # would deadlock the handshake.
            paths = dropped_paths(root, event.data)
            self.after(0, lambda: callback(paths))
            return getattr(event, "action", None)

        self.widget.drop_target_register(tkdnd.DND_FILES)
        self.widget.dnd_bind("<<Drop>>", on_drop)
        return True
