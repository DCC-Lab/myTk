import usb.core
import usb.util
import usb.core
import usb.backend.libusb1

backend = usb.backend.libusb1.get_backend(
    find_library=lambda x: "/opt/homebrew/lib/libusb-1.0.dylib"
)

# Vendor ID and Product ID of your UVC camera
VENDOR_ID = 0x0C45  # Replace VVVV with your actual vendor ID
PRODUCT_ID = 0x6366  # Replace PPPP with your actual product ID

# Find the UVC camera device
dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID, backend=backend)
# print(dev)

if dev is None:
    raise ValueError("Device not found")

# Detach kernel driver if active
if dev.is_kernel_driver_active(0):
    dev.detach_kernel_driver(0)

# Set configuration (assuming default configuration)
dev.set_configuration()

# Find the appropriate interface and endpoints (you need to identify the correct ones for your camera)
interface = 0
endpoint = dev[0][(0, 0)][0]
print(endpoint)
# You may need to send control requests here to configure camera settings (optional)

# Start streaming (this is a simplified example)
dev.ctrl_transfer(0x21, 0x01, 0, 0, None)  # Start streaming command

# You can now read data from the endpoint to get video frames
while True:
    data = dev.read(endpoint.bEndpointAddress, endpoint.wMaxPacketSize)
    # Process the video frame data as needed
