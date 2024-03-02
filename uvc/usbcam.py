from typing import NamedTuple
import enum
import struct
import time
import usb.core
import usb.util
import array

import hardwarelibrary.utils as utils


class USBDevRequest(NamedTuple):
    bmRequestType:int
    bRequest:int 
    wValue:int = 0
    wIndex:int = 0
    wLength:int = None
    pData:bytearray = None

"""
 UVC Camera-specific constants for USB Cameras
"""

class Dest(enum.IntEnum):
    UVC_CONTROL_INTERFACE_CLASS = 14
    UVC_CONTROL_INTERFACE_SUBCLASS = 1

class Unit(enum.IntEnum):
    UVC_INPUT_TERMINAL_ID = 0x01
    UVC_PROCESSING_UNIT_ID = 0x02


class UVCRequestType(enum.IntEnum):        
    UVC_SET_CUR = 0x01
    UVC_GET_CUR = 0x81
    UVC_GET_MIN = 0x82
    UVC_GET_MAX = 0x83

uvc_controls = {"autoExposure":{"unit":Unit.UVC_INPUT_TERMINAL_ID, "selector":0x02, "size":1},
                "exposure":{"unit":Unit.UVC_INPUT_TERMINAL_ID, "selector":0x04, "size":4},
                "brightness":{"unit":Unit.UVC_PROCESSING_UNIT_ID, "selector":0x02, "size":2},
                "contrast":{"unit":Unit.UVC_PROCESSING_UNIT_ID, "selector":0x03, "size":2},
                "gain":{"unit":Unit.UVC_PROCESSING_UNIT_ID, "selector":0x04, "size":2},
                "saturation":{"unit":Unit.UVC_PROCESSING_UNIT_ID, "selector":0x07, "size":2},
                "sharpness":{"unit":Unit.UVC_PROCESSING_UNIT_ID, "selector":0x08, "size":2},
                "whiteBalance":{"unit":Unit.UVC_PROCESSING_UNIT_ID, "selector":0x0a, "size":2},
                "autoWhiteBalance":{"unit":Unit.UVC_PROCESSING_UNIT_ID, "selector":0x0b, "size":1}
                }

class MyUSBCamera:

    def __init__(self, vidpids):
        backend = usb.backend.libusb1.get_backend(find_library=lambda x: "/opt/homebrew/lib/libusb-1.0.dylib")

        usbDevices = utils.connectedUSBDevices(vidpids=vidpids)

        if len(usbDevices) == 1:
            dev = usbDevices[0]
        elif len(usbDevices) == 0:
            raise RuntimeError("No matching devices. Available: {0}".format(utils.connectedUSBDevices()))
        else:
            raise RuntimeError("More than one matching device : {0}".format(usbDevices))

        self.dev = dev

        if self.dev.is_kernel_driver_active(0):
            self.dev.detach_kernel_driver(0)

        self.dev.set_configuration()
        self.configuration = self.dev.get_active_configuration()


    def startStreaming(self):
        VIDEO_FRAME_INDEX = 0x01
        VIDEO_FORMAT_MJPEG = 0x01
        VIDEO_STREAM_INTERFACE = 0
        CONTROL_TIMEOUT = 1000

        ret = self.dev.ctrl_transfer(usb.util.CTRL_OUT | usb.util.CTRL_TYPE_CLASS | usb.util.CTRL_RECIPIENT_INTERFACE,
                  UVCRequestType.UVC_SET_CUR,
                  (1 << 8) | VIDEO_FRAME_INDEX,
                  VIDEO_STREAM_INTERFACE,
                  None,
                  timeout=CONTROL_TIMEOUT)

    def readFrame(self):
        interface = self.configuration[(0,0)]
        endpoint = interface[0]

        buffer = array.array('B',[0]*endpoint.wMaxPacketSize)
        endpoint.read(size_or_buffer=buffer, timeout=100)

    def setUVCData(self, value, length, selector, unitId):
        if length == 1:
            pData = struct.pack('b', value)
        elif length == 2:
            pData = struct.pack('h', value)
        elif length == 4:
            pData = struct.pack('i', value)

        request = USBDevRequest(bmRequestType=0x21,
                                bRequest=UVCRequestType.UVC_SET_CUR,
                                wValue=(selector<<8) | 0x00,
                                wIndex=(unitId << 8) | 0x00,
                                pData=pData)

        bytesWritten = self.dev.ctrl_transfer(request.bmRequestType,
                         bRequest=request.bRequest,
                         wValue=request.wValue,
                         wIndex=request.wIndex,
                         data_or_wLength=request.pData)        

        return bytesWritten

    def getUVCData(self, type, length, selector, unitId):
        request = USBDevRequest(bmRequestType=0xa1,
                                bRequest=type,
                                wValue=(selector<<8) | 0x00,
                                wIndex=(unitId << 8) | 0x00,
                                wLength=length)

        bytesRead = self.dev.ctrl_transfer(request.bmRequestType,
                         bRequest=request.bRequest,
                         wValue=request.wValue,
                         wIndex=request.wIndex,
                         data_or_wLength=request.wLength)

        if length == 1:
            value = struct.unpack('b', bytes(bytesRead))[0]
        elif length == 2:
            value = struct.unpack('h', bytes(bytesRead))[0]
        elif length == 4:
            value = struct.unpack('i', bytes(bytesRead))[0]

        return value


    def getRangeForControl(self, control_name):
        uvc_control = uvc_controls[control_name]
        minValue = self.getUVCData(type = UVCRequestType.UVC_GET_MIN, 
                     length = uvc_control["size"], 
                     selector=uvc_control["selector"], 
                     unitId=uvc_control["unit"])
        maxValue = self.getUVCData(type = UVCRequestType.UVC_GET_MAX, 
                     length = uvc_control["size"], 
                     selector=uvc_control["selector"], 
                     unitId=uvc_control["unit"])
        return minValue, maxValue

    def getValue(self, control_name):
        uvc_control = uvc_controls[control_name]
        value = self.getUVCData(type = UVCRequestType.UVC_GET_CUR, 
                     length = uvc_control["size"], 
                     selector=uvc_control["selector"], 
                     unitId=uvc_control["unit"])
        return value


    def setValue(self, control_name, value):
        uvc_control = uvc_controls[control_name]
        value = self.setUVCData(value = value, 
                     length = uvc_control["size"], 
                     selector=uvc_control["selector"], 
                     unitId=uvc_control["unit"])
        return value


if __name__ == "__main__":
    # camera = MyUSBCamera(vidpids=[(0x043e, 0x9a4d)])    
    
    # camera = MyUSBCamera(vidpids=[(0x1224, 0x2a25)])
    camera = MyUSBCamera(vidpids=[(0x05ac, 0x1112)])


    for key in uvc_controls.keys():
        print(key, "\t", camera.getRangeForControl(key), "\tcurrent ", camera.getValue(key))

    # camera.startStreaming()
    # camera.readFrame()
