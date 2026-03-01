"""One-to-many notification system for decoupled observer communication.

This implements a notification system where one class can notify many other
objects that something has happened. You use this strategy when the notifier
does not need to know who does what, but it knows that other objects may need
to adjust in response to a change.

At the center of this mechanism is the NotificationCenter: a singleton class
that manages the observers and posts the notifications. Notification names
must be defined as Enum subclasses.

Example::

    class DeviceNotification(Enum):
        will_move = "will_move"
        did_move  = "did_move"

    NotificationCenter().post_notification(
        DeviceNotification.did_move, self, user_info={"position": (x, y, z)}
    )

The NotificationCenter is thread-safe.
"""
from enum import Enum
from threading import RLock


class Notification:
    """A notification object carrying a name, source object, and optional user info."""

    def __init__(self, name, object=None, user_info=None):
        if not isinstance(name, Enum):
            raise ValueError("You must use an enum-subclass of Enum, not a string for the notification name")

        self.name = name
        self.object = object
        self.user_info = user_info

class ObserverInfo:
    """Record describing an observer registration in the NotificationCenter."""

    def __init__(self, observer, method=None, notification_name=None, observed_object=None):
        self.observer = observer
        self.method = method
        self.observed_object = observed_object
        self.notification_name = notification_name

    def matches(self, other_observer) -> bool:
        """Check whether this observer record matches another for lookup purposes."""
        return not (self.notification_name is not None and other_observer.notification_name is not None and self.notification_name != other_observer.notification_name or self.observed_object is not None and other_observer.observed_object is not None and self.observed_object != other_observer.observed_object or self.observer != other_observer.observer)

    def __eq__(self, rhs):
        return self.matches(rhs)

class NotificationCenter:
    """Singleton notification center for one-to-many observer communication.

    All notification names must be Enum members. The center is thread-safe.
    """

    _instance = None

    def destroy(self):
        """Destroy the singleton instance and reset the class-level reference."""
        nc = NotificationCenter()
        NotificationCenter._instance = None
        del(nc)

    def __init__(self):
        if not hasattr(self, 'observers'):
            self.observers = {}
        if not hasattr(self, 'lock'):
            self.lock = RLock()

    def __new__(cls, *args, **kwargs):
        """Return the singleton instance, creating it if necessary."""
        if cls._instance is None:
            cls._instance = object.__new__(cls, *args, **kwargs)
        return cls._instance

    def add_observer(self, observer, method, notification_name=None, observed_object=None):
        """Register an observer to be notified when a notification is posted.

        Args:
            observer: The object that wants to receive notifications.
            method: Callable to invoke with the Notification as its argument.
            notification_name: Enum member identifying the notification to observe.
            observed_object: If provided, only notifications from this object
                will be forwarded.

        Raises:
            ValueError: If notification_name is not None and not an Enum member.
        """
        if notification_name is not None and not isinstance(notification_name, Enum):
            raise ValueError("You must use an enum-subclass of Enum, not a string for the notification_name")

        observer_info = ObserverInfo(observer=observer, method=method, notification_name=notification_name, observed_object=observed_object)

        with self.lock:
            if notification_name not in self.observers:
                self.observers[notification_name] = [observer_info]
            else:
                if observer_info not in self.observers[notification_name]:
                    self.observers[notification_name].append(observer_info)

    def remove_observer(self, observer, notification_name=None, observed_object=None):
        """Unregister an observer so it no longer receives notifications.

        Args:
            observer: The observer object to remove.
            notification_name: If provided, remove only for this notification.
            observed_object: If provided, remove only for this observed object.

        Raises:
            ValueError: If notification_name is not None and not an Enum member.
        """
        if notification_name is not None and not isinstance(notification_name, Enum):
            raise ValueError("You must use an enum-subclass of Enum, not a string for the notification_name")

        observer_to_remove = ObserverInfo(observer=observer, notification_name=notification_name, observed_object=observed_object)

        with self.lock:
            if notification_name is not None:
                self.observers[notification_name] = [currentObserver for currentObserver in self.observers[notification_name] if not currentObserver.matches(observer_to_remove) ]
            else:
                for name in self.observers:
                    self.observers[name] = [observer for observer in self.observers[name] if not observer.matches(observer_to_remove) ]

    def post_notification(self, notification_name, notifying_object, user_info=None):
        """Post a notification, invoking all matching observer callbacks.

        Args:
            notification_name: Enum member identifying the notification.
            notifying_object: The object posting the notification.
            user_info: Optional dict of additional data for observers.

        Raises:
            ValueError: If notification_name is not an Enum member.
        """
        if not isinstance(notification_name, Enum):
            raise ValueError("You must use an enum-subclass of Enum, not a string for the notification_name")

        with self.lock:
            if notification_name in self.observers:
                notification = Notification(notification_name, notifying_object, user_info)
                for observer_info in self.observers[notification_name]:
                    if observer_info.observed_object is None or observer_info.observed_object == notifying_object:
                        observer_info.method(notification)

    def observers_count(self):
        """Return the total number of registered observer entries."""
        with self.lock:
            count = 0
            for name in self.observers:
                count += len(self.observers[name])
            return count

    def clear(self):
        """Remove all registered observers."""
        with self.lock:
            self.observers = {}
