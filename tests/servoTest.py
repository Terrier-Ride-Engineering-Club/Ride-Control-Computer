from Backend.iocontroller import HardwareIOController
import time


if __name__ == "__main__":


    io = HardwareIOController()

    while True:
        io.extend_servos()
        time.sleep(2)
        io.retract_servos()
        time.sleep(2)

