import subprocess
import time

usb_path = "1-1.1"

def usb_unbind():
    subprocess.run(["sudo", "tee", "/sys/bus/usb/drivers/usb/unbind"], input=usb_path.encode())
    print("USB port disabled")

def usb_bind():
    subprocess.run(["sudo", "tee", "/sys/bus/usb/drivers/usb/bind"], input=usb_path.encode())
    print("USB port enabled")

while True:
    usb_unbind()
    time.sleep(360)
    usb_bind()
    time.sleep(360)