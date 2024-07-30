import envtest
import unittest
from enum import Enum

from mytk.notificationcenter import NotificationCenter, ObserverInfo


class TestNotificationName(Enum):
    test       = "test"
    test2      = "test2"
    test3      = "test3"
    test4      = "test4"
    other      = "other"
    wrong      = "wrong"

class TestNotificationCenter(unittest.TestCase):
    def setUp(self):
        self.posted_user_info = None
        self.notification_received = False

    def tearDown(self):
        NotificationCenter().clear()

    def testSingleton(self):
        self.assertIsNotNone(NotificationCenter())

    def testSingletonCanPost(self):
        nc = NotificationCenter()
        nc.post_notification(TestNotificationName.test, self)

    def testadd_observer(self):
        nc = NotificationCenter()
        nc.add_observer(observer=self, method=self.handle, notification_name=TestNotificationName.test)

    def testadd_observerCount(self):
        nc = NotificationCenter()
        self.assertEqual(nc.observers_count(), 0)
        nc.add_observer(observer=self, method=self.handle, notification_name=TestNotificationName.test)
        self.assertEqual(nc.observers_count(), 1)

    def testObserverInfo(self):
        nc = NotificationCenter()
        observer = ObserverInfo(observer=self, method=self.handle, notification_name=TestNotificationName.test, observed_object=nc)
        
        self.assertTrue(observer.matches(ObserverInfo(observer=self)))
        self.assertTrue(observer.matches(ObserverInfo(observer=self, notification_name=TestNotificationName.test)))
        self.assertTrue(observer.matches(ObserverInfo(observer=self, notification_name=None)))
        self.assertTrue(observer.matches(ObserverInfo(observer=self, notification_name=TestNotificationName.test, observed_object=nc)))
        self.assertTrue(observer.matches(ObserverInfo(observer=self, notification_name=None, observed_object=nc)))

        self.assertFalse(observer.matches(ObserverInfo(observer=nc)))
        self.assertFalse(observer.matches(ObserverInfo(observer=nc, notification_name=TestNotificationName.test, observed_object=nc)))
        self.assertFalse(observer.matches(ObserverInfo(observer=nc, notification_name=TestNotificationName.other, observed_object=nc)))
        self.assertFalse(observer.matches(ObserverInfo(observer=nc, notification_name=TestNotificationName.other, observed_object=None)))
        self.assertFalse(observer.matches(ObserverInfo(observer=self, notification_name=TestNotificationName.other, observed_object=None)))

    def testadd_observerremove_observer(self):
        nc = NotificationCenter()
        nc.add_observer(observer=self, method=self.handle, notification_name=TestNotificationName.test)
        self.assertEqual(nc.observers_count(), 1)
        nc.remove_observer(observer=self)
        self.assertEqual(nc.observers_count(), 0)

    def testRemoveMissingObserver(self):
        nc = NotificationCenter()
        self.assertEqual(nc.observers_count(), 0)
        nc.remove_observer(self)
        self.assertEqual(nc.observers_count(), 0)

    def testadd_observerAnySenderAndPostithObject(self):
        nc = NotificationCenter()
        nc.add_observer(observer=self, method=self.handle, notification_name=TestNotificationName.test)
        nc.post_notification(notification_name=TestNotificationName.test, notifying_object=self)
        self.assertTrue(self.notification_received)

        nc.remove_observer(self)

    def testadd_observerAnySenderAndPostWithuser_info(self):
        nc = NotificationCenter()
        nc.add_observer(observer=self, method=self.handle, notification_name=TestNotificationName.test)
        nc.post_notification(notification_name=TestNotificationName.test, notifying_object=self, user_info="1234")
        self.assertTrue(self.notification_received)
        self.assertEqual(self.posted_user_info, "1234")
        nc.remove_observer(self)

    def testadd_observerWrongNotification(self):
        nc = NotificationCenter()
        nc.add_observer(observer=self, method=self.handle, notification_name=TestNotificationName.wrong)
        nc.post_notification(notification_name=TestNotificationName.test, notifying_object=self, user_info="1234")
        self.assertFalse(self.notification_received)
        self.assertNotEqual(self.posted_user_info, "1234")
        nc.remove_observer(self)

    def testadd_observerWrongSender(self):
        someObject = NotificationCenter()
        nc = NotificationCenter()
        nc.add_observer(self, method=self.handle, notification_name=TestNotificationName.test, observed_object=someObject)
        nc.post_notification(notification_name=TestNotificationName.test, notifying_object=self, user_info="1234")
        self.assertFalse(self.notification_received)
        self.assertNotEqual(self.posted_user_info, "1234")
        nc.remove_observer(self)
        self.assertEqual(nc.observers_count(), 0)

    def testadd_observerNoDuplicates(self):
        nc = NotificationCenter()
        nc.add_observer(self, self.handle, TestNotificationName.test, None)
        nc.add_observer(self, self.handle, TestNotificationName.test, None)
        self.assertEqual(nc.observers_count(), 1)

    def testadd_observerNoDuplicates2(self):
        nc = NotificationCenter()
        nc.add_observer(self, self.handle, TestNotificationName.test, None)
        nc.add_observer(self, self.handle, TestNotificationName.test2, None)
        self.assertEqual(nc.observers_count(), 2)

    def testadd_observerNoDuplicates3(self):
        nc = NotificationCenter()
        nc.add_observer(self, self.handle, TestNotificationName.test, None)
        nc.add_observer(self, self.handle, TestNotificationName.test, nc)
        self.assertEqual(nc.observers_count(), 1)

    def testRemoveIncorrectObject(self):
        nc = NotificationCenter()
        someObject = NotificationCenter()
        nc.add_observer(self, self.handle, TestNotificationName.test, someObject)
        nc.remove_observer(someObject)
        self.assertEqual(nc.observers_count(), 1)

    def testRemoveManyObservers(self):
        nc = NotificationCenter()
        someObject = NotificationCenter()
        nc.add_observer(self, self.handle, TestNotificationName.test, someObject)
        nc.add_observer(self, self.handle, TestNotificationName.test2, someObject)
        nc.add_observer(self, self.handle, TestNotificationName.test3, someObject)
        nc.add_observer(self, self.handle, TestNotificationName.test4, None)
        nc.remove_observer(self)
        self.assertEqual(nc.observers_count(), 0)

    def testRemoveManyObservers2(self):
        nc = NotificationCenter()
        someObject = NotificationCenter()
        nc.add_observer(self, self.handle, TestNotificationName.test, someObject)
        nc.add_observer(self, self.handle, TestNotificationName.test2, someObject)
        nc.add_observer(self, self.handle, TestNotificationName.test3, someObject)
        nc.add_observer(self, self.handle, TestNotificationName.test4, None)
        nc.remove_observer(self, observed_object=someObject)
        self.assertEqual(nc.observers_count(), 0)

    def handle(self, notification):
        self.notification_received = True
        self.posted_user_info = notification.user_info

if __name__ == '__main__':
    unittest.main()
