"""
    This implements a "one-to-many" notification system, when one class needs
    to notify many other objects (possibly one also, or none) that something has
    happened. You use this strategy when the notifier does not really need to
    know who does what, but it knows that other objects may need to adjust in
    response to a change. An example is a window that will notify "I was just
    resized" or a computation section that may notify "I am done calculating"
    so that the interface can react and display the result, or even a
    physical device (such as a translation stage) that will notify "I just
    finished moving", you can start acquiring the image.

    At the center of this mechanism is the NotificationCenter(): a singleton
    class (that is a class with a single instance in the code, never two)
    that will manage the observers and will post the notifications.

    You define notifications names in your code, and post them when
    appropriate. You *must* define notification names as Enum (because if you
    don't it makes it impossible to know if a notification is actually
    acceptaable and error management is nearly impossible. For instance, a
    translation stage could define the following notifications:

    class DeviceNotification(Enum):
        will_move        = "will_move"
        did_move         = "did_move"

    When appropriate, the stage would call, for example:

    notification = Notification(name = DeviceNotification.did_move, 
                                object = self, 
                                user_info = {"position":(x,y,z)})
    NotificationCenter().post_notification(notification)

    In the notification, the object can be self, but also any object that is
    relevant. You can provide any information that may be relevant to the
    observers in user_info. For instance, with the previous example, we may
    want to provide the actual position of the stage. It is totally up to you
    to decide what you include, because you will be the one acting on the
    information you receive. To be notified, an object needs to register for the
    notification. It does so with the following:

    NotificationCenter().add_observer(observer, method, notification_name,
    observed_object)

    The "method" is defined in "observer" and will receive the notification with
    all its information and will be called by the notification center like:

    observer.method(notification)

    therefore it must have the following signature:

    def method(self, notification:Notification)

    The minimum to provide when registering is observer, method and
    notification_name.  The observer will be notified (via the method
    callback observer.method()) when notification_name is posted. If you
    provided "observed_object", then it will be notified only when the
    notification has the same "object". This is useful, for instance, when
    you have several objects that will post identical notifications. An
    example would be a class representing windows that post a "did_resize"
    notification after they have resized: you may want to react to the resize
    notification of a given window, not "all" windows.

    The NotificationCenter is thread-safe.
"""
from threading import RLock
from enum import Enum


class Notification:
    def __init__(self, name, object=None, user_info=None):
        if not isinstance(name, Enum):
            raise ValueError("You must use an enum-subclass of Enum, not a string for the notification name")

        self.name = name
        self.object = object
        self.user_info = user_info

class ObserverInfo:
    def __init__(self, observer, method=None, notification_name=None, observed_object=None):
        self.observer = observer
        self.method = method
        self.observed_object = observed_object
        self.notification_name = notification_name

    def matches(self, other_observer) -> bool:
        if self.notification_name is not None and other_observer.notification_name is not None and self.notification_name != other_observer.notification_name:
            return False
        elif self.observed_object is not None and other_observer.observed_object is not None and self.observed_object != other_observer.observed_object:
            return False
        elif self.observer != other_observer.observer:
            return False
        return True

    def __eq__(self, rhs):
        return self.matches(rhs)

class NotificationCenter:
    _instance = None

    def destroy(self):
        nc = NotificationCenter()
        NotificationCenter._instance = None
        del(nc)

    def __init__(self):
        if not hasattr(self, 'observers'):
            self.observers = {}
        if not hasattr(self, 'lock'):
            self.lock = RLock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = object.__new__(cls, *args, **kwargs)
        return cls._instance

    def add_observer(self, observer, method, notification_name=None, observed_object=None):
        if notification_name is not None and not isinstance(notification_name, Enum):
            raise ValueError("You must use an enum-subclass of Enum, not a string for the notification_name")

        observer_info = ObserverInfo(observer=observer, method=method, notification_name=notification_name, observed_object=observed_object)

        with self.lock:
            if notification_name not in self.observers.keys():
                self.observers[notification_name] = [observer_info]
            else:
                if observer_info not in self.observers[notification_name]:
                    self.observers[notification_name].append(observer_info)

    def remove_observer(self, observer, notification_name=None, observed_object=None):
        if notification_name is not None and not isinstance(notification_name, Enum):
            raise ValueError("You must use an enum-subclass of Enum, not a string for the notification_name")

        observerToRemove = ObserverInfo(observer=observer, notification_name=notification_name, observed_object=observed_object)

        with self.lock:
            if notification_name is not None:
                self.observers[notification_name] = [currentObserver for currentObserver in self.observers[notification_name] if not currentObserver.matches(observerToRemove) ]
            else:
                for name in self.observers.keys():
                    self.observers[name] = [observer for observer in self.observers[name] if not observer.matches(observerToRemove) ]        

    def post_notification(self, notification_name, notifying_object, user_info=None):
        if not isinstance(notification_name, Enum):
            raise ValueError("You must use an enum-subclass of Enum, not a string for the notification_name")

        with self.lock:
            if notification_name in self.observers.keys():
                notification = Notification(notification_name, notifying_object, user_info)
                for observer_info in self.observers[notification_name]:
                    if observer_info.observed_object is None or observer_info.observed_object == notifying_object:
                        observer_info.method(notification)

    def observers_count(self):
        with self.lock:
            count = 0
            for name in self.observers.keys():
                count += len(self.observers[name])
            return count

    def clear(self):
        with self.lock:
            self.observers = {}
