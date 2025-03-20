# from gpiozero.pins.native import NativeFactory
from gpiozero.pins.lgpio import LGPIOFactory
from gpiozero import Device, LED

# Device.pin_factory = NativeFactory()
Device.pin_factory = LGPIOFactory()

# These will now implicitly use NativePin instead of RPiGPIOPin
led1 = LED(16)
led2 = LED(17)