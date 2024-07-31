import envtest
import unittest
import os
from mytk import *
from mytk.bindable import Bindable
from mytk.videoview import VideoCapture
import time

class TestVideoCapture(envtest.MyTkTestCase):
    def setUp(self):
        super().setUp()
        self.callback_called = False

    def test_init(self):
        c = VideoCapture()
        self.assertIsNotNone(c)

    def test_available_devices(self):
        devices = VideoCapture.available_devices()
        self.assertTrue(len(devices) > 0)

    def test_start_capture(self):
        device = VideoCapture()
        self.assertIsNotNone(device)
        device.start_capturing()
        device.stop_capturing()

    def test_get_next_frame(self):
        device = VideoCapture()
        self.assertIsNotNone(device)
        device.start_capturing()

        _ = device.get_next_frame()
        start = time.time()
        for i in range(10):
            _ = device.get_next_frame()
            inter_frame_delay = (time.time()-start)/(i+1)
            self.assertTrue( inter_frame_delay > 0.02, f"Delay was {inter_frame_delay}" )
        self.assertEqual(device.frame_counter, 11)

    def test_get_next_frame_continuously(self):
        device = VideoCapture()
        self.assertIsNotNone(device)
        device.start_capturing(run_continuously=True)
        self.assertIsNotNone(device.thread)
        time.sleep(1)
        device.stop_capturing()
        self.assertTrue(device.frame_counter > 10)

    def test_get_next_frame_continuously_with_delegate(self):
        device = VideoCapture(delegate=self)

        self.assertIsNotNone(device)
        device.start_capturing(run_continuously=True)
        self.assertIsNotNone(device.thread)
        time.sleep(1)
        device.stop_capturing()
        self.assertTrue(device.frame_counter > 10)
        self.assertTrue(self.callback_called)

    def frame_ready(self, frame):
        self.callback_called = True

    def test_prop_ids(self):
        device = VideoCapture(device_id=0, delegate=self)
        device.start_capturing()
        device.prop_ids()
        device.stop_capturing()


# class TestVideoView(envtest.MyTkTestCase):
#     def setUp(self):
#         super().setUp()
#         self.callback_called = False

#     def test_init(self):
#         c = VideoView()
        # self.assertIsNotNone(c)


if __name__ == "__main__":
    unittest.main()
