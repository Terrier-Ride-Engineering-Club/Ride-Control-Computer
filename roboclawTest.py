"""
GPIO14 - UART_TX
GPIO15 - UART_RX

RaspiConfig Serial Tutorial: https://resources.basicmicro.com/configuring-the-raspberry-pi-3-serial-port/
RoboClaw tutorial: https://resources.basicmicro.com/packet-serial-with-the-raspberry-pi-3/
"""


from roboclaw import RoboClaw
from time import sleep

if __name__ == "__main__":
    
    address = 0x80
    mc = RoboClaw(port='/dev/ttyAMA0',address=0x80)
    
    MODE = "MOTOR TEST"
    while True:
        if MODE == "DIAGNOSTIC":
            print(f"STATUS: {mc.read_status()}")
            print(f"VOLTAGE: {mc.read_batt_voltage('main')}")
            print(f"ENCODER M1: {mc.read_encoder(1)}")
            print(f"ENCODER M2: {mc.read_encoder(2)}")
            print(f"RANGE M1: {mc.read_range(1)}")
            print(f"RANGE M2: {mc.read_range(2)}")
            print(f"POSITION M1: {mc.read_position(1)}")
            print(f"POSITION M2: {mc.read_position(2)}")
            print(f"TEMP SENSOR 1: {mc.read_temp_sensor(1)}")
            print(f"TEMP SENSOR 2: {mc.read_temp_sensor(2)}")
            print(f"BATT VOLTAGE (Logic): {mc.read_batt_voltage('logic')}")
            print(f"VOLTAGES (Main, Logic): {mc.read_voltages()}")
            print(f"CURRENT VALUES: {mc.read_currents()}")
            print(f"MOTOR CURRENT M1: {mc.read_motor_current(1)}")
            print(f"MOTOR CURRENT M2: {mc.read_motor_current(2)}")
            print(f"MOTOR PWMs: {mc.read_motor_pwms()}")
            print(f"MOTOR PWM M1: {mc.read_motor_pwm(1)}")
            print(f"MOTOR PWM M2: {mc.read_motor_pwm(2)}")
            print(f"INPUT PIN MODES: {mc.read_input_pin_modes()}")
            print(f"MAX SPEED M1: {mc.read_max_speed(1)}")
            print(f"MAX SPEED M2: {mc.read_max_speed(2)}")
            print(f"SPEED M1: {mc.read_speed(1)}")
            print(f"SPEED M2: {mc.read_speed(2)}")
            sleep(2)
        elif MODE == "MOTOR TEST":
            mc.drive_motor(1,1)
            sleep(1)
            mc.drive_motor(1,0)
            sleep(1)
        
        # roboclaw.drive_motor(1,0)
        # sleep(2)