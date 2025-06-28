"""
event_capable.py — Event mixin class for widget behavior

Provides the `EventCapable` class, a mixin designed to add event-related
capabilities to GUI widgets that expose a `widget` attribute compatible with
`tk.Widget`. This includes scheduling timed callbacks, cancelling them, and
binding or generating Tkinter events.

It is used for Base and App, which handle their widgets differently.

Also includes the `HasWidget` protocol to allow static checking of widget
presence for type-checkers.
"""

from contextlib import suppress
from typing import Protocol, runtime_checkable, Callable, Sequence
import tkinter as tk


@runtime_checkable
class HasWidget(Protocol):
    """
    Protocol for objects that expose a `widget` attribute of type `tk.Widget`.

    This can be used with `isinstance(obj, HasWidget)` to check interface compliance.
    """

    widget: tk.Widget


class EventCapable:
    """
    Mixin class providing event-related methods for classes exposing a `widget` attribute.

    Designed to be used alongside other base classes that define `self.widget`
    as a `tk.Widget`. This class should not be used on its own.

    Responsibilities:
    - Scheduling and cancelling timed callbacks (`after`, `after_cancel`, etc.)
    - Event binding and generation via `widget.bind` and `widget.event_generate`
    - Lifecycle cleanup via `__del__`
    """

    widget: "tk.Widget"  # Hint for static type checkers and linters like pylint

    def __init__(self, *args, **kwargs):
        """
        Initializes internal scheduling structures and sets up for cooperative multiple inheritance.
        """
        self.scheduled_tasks = []
        super().__init__(*args, **kwargs)  # cooperative!

    # def __del__(self):
    #     """
    #     Cancels all registered scheduled tasks to prevent dangling callbacks.
    #     Also invokes superclass `__del__` if defined.
    #     """
    #     for task_id in self.scheduled_tasks:
    #         self.after_cancel(task_id)

    #     super_del = getattr(super(), "__del__", None)
    #     if callable(super_del):
    #         with suppress(Exception):
    #             super_del()  # pylint: disable=not-callable

    def _valid_mixin_class(self):
        """
        Ensures that `self.widget` exists before performing widget operations.

        Raises:
            AttributeError: If `self` does not define a `widget` attribute.
        """
        if not isinstance(self, HasWidget):
            raise AttributeError(
                f"EventCapable requires {self.__class__.__name__} to provide a 'widget' attribute"
            )

    def after(self, delay: int, function: Callable) -> int:
        """
        Schedules a function to be called after a given time delay.

        Args:
            delay (int): Delay in milliseconds.
            function (Callable): Function to invoke.

        Returns:
            int: Identifier of the scheduled task, which can be used with `after_cancel`.
        """
        self._valid_mixin_class()
        task_id = None
        if self.widget is not None and function is not None:
            task_id = self.widget.after(delay, function)
            self.scheduled_tasks.append(task_id)
        return task_id

    def after_cancel(self, task_id: int):
        """
        Cancels a previously scheduled task by its ID.

        Args:
            task_id (int): ID of the task returned by `after()`.
        """
        self._valid_mixin_class()
        if self.widget is not None:
            self.widget.after_cancel(task_id)
            self.scheduled_tasks.remove(task_id)

    def after_cancel_many(self, task_ids: Sequence[int]):
        """
        Cancels multiple tasks given a sequence of IDs.

        Args:
            task_ids (Sequence[int]): List or tuple of task IDs to cancel.
        """
        for task_id in task_ids:
            self.after_cancel(task_id)

    def after_cancel_all(self):
        """
        Cancels all currently scheduled tasks for this object.
        """
        self.after_cancel_many(self.scheduled_tasks)

    def bind_event(self, event: str, callback: Callable):
        """
        Binds a callback function to a specific event on the underlying widget.

        Args:
            event (str): Tkinter event string (e.g. "<Button-1>").
            callback (Callable): Function to be called when the event occurs.
        """
        self._valid_mixin_class()
        self.widget.bind(event, callback)

    def event_generate(self, event: str):
        """
        Triggers an event on the underlying widget programmatically.

        Args:
            event (str): Event name to trigger (e.g., "<<CustomEvent>>").
        """
        self._valid_mixin_class()
        self.widget.event_generate(event)
