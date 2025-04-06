from Backend.iocontroller import HardwareIOController
import time


if __name__ == "__main__":


    io = HardwareIOController()

    while True:
        print('OUT')
        io.extend_servos()
        time.sleep(2)
        print('IN')
        io.retract_servos()
        time.sleep(2)

