"""
GPIO14 - UART_TX
GPIO15 - UART_RX

RaspiConfig Serial Tutorial: https://resources.basicmicro.com/configuring-the-raspberry-pi-3-serial-port/
RoboClaw tutorial: https://resources.basicmicro.com/packet-serial-with-the-raspberry-pi-3/
"""

from Backend.iocontroller import SLOW_SPEED_QPPS,MED_SPEED_QPPS,FAST_SPEED_QPPS, HOME_POSITION
from Backend.roboclaw import RoboClaw
from time import sleep, time

if __name__ == "__main__":
    
    address = 0x80
    mc = RoboClaw(port='/dev/ttyAMA0',address=0x80)
    
    MODE = "MOTOR TEST"
    while True:
        if MODE == "DIAGNOSTIC":
            print(f"VER: {mc.read_version()}")
            print(f"STATUS: {mc.read_status()}")
            # print(f"VOLTAGE: {mc.read_batt_voltage('main')}")
            print(f"ENCODER M1: {mc.read_encoder(1)}")
            # print(f"ENCODER M2: {mc.read_encoder(2)}")
            # print(f"RANGE M1: {mc.read_range(1)}")
            # print(f"RANGE M2: {mc.read_range(2)}")
            # print(f"POSITION M1: {mc.read_position(1)}")
            # print(f"POSITION M2: {mc.read_position(2)}")
            print(f"TEMP SENSOR 1: {mc.read_temp_sensor(1)}")
            # print(f"TEMP SENSOR 2: {mc.read_temp_sensor(2)}")
            # print(f"BATT VOLTAGE (Logic): {mc.read_batt_voltage('logic')}")
            print(f"VOLTAGES (Main, Logic): {mc.read_voltages()}")
            # print(f"STOP ALL!!: {mc.stop_all()}")
            print(f"SET CURRENT: {mc.set_m2_max_current_limit(2000)}")
            print(f"GET CONFIG: {mc.read_standard_config()}")
            print(f"GET SPins: {mc.read_s_pin_modes()}")
            # print(f"SAVE CURRENT: {mc.write_settings_to_eeprom()}")
            # print(f"READ CURRENT: {mc.read_m2_max_current_limit()}")
            # print(f"STOP ALL!!: {mc.drive_motor(1,50)}")
            # print(f"CURRENT VALUES: {mc.read_currents()}")
            # print(f"MOTOR CURRENT M1: {mc.read_motor_current(1)}")
            # print(f"MOTOR CURRENT M2: {mc.read_motor_current(2)}")
            # print(f"MOTOR PWMs: {mc.read_motor_pwms()}")
            # print(f"MOTOR PWM M1: {mc.read_motor_pwm(1)}")
            # print(f"MOTOR PWM M2: {mc.read_motor_pwm(2)}")
            # print(f"INPUT PIN MODES: {mc.read_input_pin_modes()}")
            # print(f"MAX SPEED M1: {mc.read_max_speed(1)}")
            # print(f"MAX SPEED M2: {mc.read_max_speed(2)}")
            # print(f"SPEED M1: {mc.read_speed(1)}")
            # print(f"SPEED M2: {mc.read_speed(2)}")
            sleep(2)
        elif MODE == "MOTOR TEST":
            # print(f"RESETTING ENCODERS: {mc.reset_quad_encoders()}")

            # print("Forward - Med/Slow")
            # print(f"STATUS: {mc.read_status()}")
            # start_time = time()
            # while time() - start_time < 5:
            #     mc.set_speed_with_acceleration(1, MED_SPEED_QPPS, SLOW_SPEED_QPPS)
            #     sleep(0.1)  # Adjust interval as needed

            # print("Stop - Slow")
            # print(f"STATUS: {mc.read_status()}")
            # start_time = time()
            # mc.reset_quad_encoders()
            # while time() - start_time < 2:
            #     mc.set_speed_with_acceleration(1, 0, SLOW_SPEED_QPPS)
            #     sleep(0.1)

            print("Forward - Fast/Fast")
            print(f"STATUS: {mc.read_status()}")
            print(f"ENC POS: {mc.read_encoder(1)}, HOME: {HOME_POSITION}")
            start_time = time()
            while time() - start_time < 2:
                mc.set_speed_with_acceleration(1, FAST_SPEED_QPPS, FAST_SPEED_QPPS)
                sleep(0.05)

            print("Reverse - Fast/Fast")
            print(f"STATUS: {mc.read_status()}")
            print(f"ENC POS: {mc.read_encoder(1)}, HOME: {HOME_POSITION}")
            start_time = time()
            while time() - start_time < 2:
                mc.set_speed_with_acceleration(1, -FAST_SPEED_QPPS, FAST_SPEED_QPPS)
                sleep(0.05)

            print("Home - Fast/Slow")
            print(f"STATUS: {mc.read_status()}")
            print(f"ENC POS: {mc.read_encoder(1)}, HOME: {HOME_POSITION}")
            print(f"READ RANGE: {mc.read_range(1)}")
            print(f"READ PID: {mc.read_position_pid_constants()}")
            # print(f"SET PID...{mc.set_position_pid_constants(0,3618*2,0,0,0,0,10000)}")
            print(f"READ PID: {mc.read_position_pid_constants()}")
            print(f"READ RANGE: {mc.read_range(1)}")
            start_time = time()
            while time() - start_time < 10:
                # mc.drive_to_position_with_speed_acceleration_deceleration(1, HOME_POSITION, FAST_SPEED_QPPS, FAST_SPEED_QPPS, SLOW_SPEED_QPPS)
                mc.drive_to_position(1, 1, 1, 1, 1000, 0)
                # mc.drive_to_position_buffered(1,5000,100)
                print(f"ENC: {mc.read_encoder(1)}, HOME: {HOME_POSITION}")
                sleep(0.05)
        
        # roboclaw.drive_motor(1,0)
        # sleep(2)