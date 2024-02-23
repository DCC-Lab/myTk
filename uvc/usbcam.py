# Information obtained from StellarNet
# Written by Daniel Cote at http://www.dcclab.ca, https://github.com/DCC-Lab

from typing import NamedTuple
import os
import enum
import struct
import time
import usb.core
import usb.util

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

    def __init__(self, dev):
        self.dev = dev

    def setUVCData(self, value, length, selector, unitId):
        if length == 1:
            pData = struct.pack('c', value)
        elif length == 2:
            pData = struct.pack('h', value)
        elif length == 4:
            pData = struct.pack('i', value)

        if len(pData) != length:
            print("Error in pData conversion")

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

        return self.sendReadControlRequest(request)

    def sendReadControlRequest(self, request:USBDevRequest):
        bytesRead = self.dev.ctrl_transfer(request.bmRequestType,
                         bRequest=request.bRequest,
                         wValue=request.wValue,
                         wIndex=request.wIndex,
                         data_or_wLength=request.wLength)        
        return bytesRead

    def sendWriteControlRequest(self, request:USBDevRequest):
        bytesWritten = self.dev.ctrl_transfer(request.bmRequestType,
                         bRequest=request.bRequest,
                         wValue=request.wValue,
                         wIndex=request.wIndex,
                         data_or_wLength=request.pData)        

        return bytesWritten

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

    def getValue(self, key):
        uvc_control = uvc_controls[key]
        value = self.getUVCData(type = UVCRequestType.UVC_GET_CUR, 
                     length = uvc_control["size"], 
                     selector=uvc_control["selector"], 
                     unitId=uvc_control["unit"])
        return value


    def setValue(self, key, value):
        uvc_control = uvc_controls[key]
        value = self.setUVCData(value = value, 
                     length = uvc_control["size"], 
                     selector=uvc_control["selector"], 
                     unitId=uvc_control["unit"])
        return value


if __name__ == "__main__":


    backend = usb.backend.libusb1.get_backend(find_library=lambda x: "/opt/homebrew/lib/libusb-1.0.dylib")

    usbDevices = utils.connectedUSBDevices(vidpids=[(0x043e, 0x9a4d)])
    # print(usbDevices)

    if len(usbDevices) == 1:
        dev = usbDevices[0]
    else:
        exit(0)

    if dev.is_kernel_driver_active(0):
        dev.detach_kernel_driver(0)

    dev.set_configuration()
    configuration = dev.get_active_configuration()

    interface = configuration[(0,0)]

    camera = MyUSBCamera(dev)

    for key in uvc_controls.keys():
        print(key, "\t", camera.getRangeForControl(key))
        print("\tCurrent ", camera.getValue(key))


    print(camera.getValue("gain"))
    # setValue(dev, "gain", 100)
    # print(getValue(dev, "gain"))

    # print(getValue(dev, "saturation"))
    # setValue(dev, "saturation", 60)
    # print(getValue(dev, "saturation"))
