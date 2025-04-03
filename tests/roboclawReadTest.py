"""
GPIO14 - UART_TX
GPIO15 - UART_RX

RaspiConfig Serial Tutorial: https://resources.basicmicro.com/configuring-the-raspberry-pi-3-serial-port/
RoboClaw tutorial: https://resources.basicmicro.com/packet-serial-with-the-raspberry-pi-3/
"""

from Backend.iocontroller import SLOW_SPEED_QPPS, MED_SPEED_QPPS, FAST_SPEED_QPPS, HOME_POSITION
from Backend.roboclaw import RoboClaw
from Backend.iocontroller import HardwareIOController
from time import sleep, time

if __name__ == "__main__":
    io = HardwareIOController()
    print("Starting RoboClaw Read Test")
    prev_time = time()
    try:
        while True:
            current_time = time()
            delta = current_time - prev_time
            prev_time = current_time
            print("Delta Time: {:.3f} sec".format(delta))
            print("Encoder:", io.read_encoder())
            print("Range:", io.read_range())
            print("Position:", io.read_position())
            print("Status:", io.read_status())
            print("Temp Sensor:", io.read_temp_sensor(1))
            print("Voltages:", io.read_voltages())
            print("Motor Current:", io.read_motor_current())
            print("Motor PWM:", io.read_motor_pwm())
            print("Input Pin Modes:", io.read_input_pin_modes())
            print("Max Speed:", io.read_max_speed())
            print("Speed:", io.read_speed())
            print("-" * 40)
            sleep(0.5)  # Delay between readings
    except KeyboardInterrupt:
        print("Test stopped.")