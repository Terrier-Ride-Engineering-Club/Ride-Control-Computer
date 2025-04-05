# IO Controller for TREC's REC Ride Control Computer
    # Made by Jackson Justus (jackjust@bu.edu)

# RCC GPIO PINOUT
ESTOP_PIN = 21
STOP_PIN = 20
DISPATCH_PIN = 18
RIDE_ONOFF_PIN = 17
RESTART_PIN = 19
SERVO1_PIN = "GPIO12"
SERVO2_PIN = "GPIO13"
#UART_TX = 14
#UART_RX = 15

# ROBOCLAW CONSTANTS
ROBOCLAW_SERIAL_PORT = "/dev/ttyAMA0"
ROBOCLAW_SERIAL_ADDRESS = 0x80
ROBOCLAW_SERIAL_BAUD_RATE = 38400
SELECTED_MOTOR = 1
POSITION_MODE_ACTIVE = False
MOTOR_STATIONARY_TIME_THRESHOLD_FOR_POSITION_MODE = 1

# SERVO CONSTANTS
SERVO_IN_POSITION = 0.5
SERVO_OUT_POSITION = 1

# MOTOR CONSTANTS
# NOTE: GoBilda 5303 series motor encoders have a resolution of 1425.1 PPR @ Output shaft
MOTOR_PPR = 1425.1
QUAD_COUNTS_PER_REVOLUTION = MOTOR_PPR * 4
# All speeds in Quad Pulses per Second (QPS)
SLOW_SPEED_QPPS = int(QUAD_COUNTS_PER_REVOLUTION / 10)     # 1 revolution every 20 seconds
MED_SPEED_QPPS = int(QUAD_COUNTS_PER_REVOLUTION / 7)    # 1 revolution every 10 seconds
FAST_SPEED_QPPS = int(QUAD_COUNTS_PER_REVOLUTION / 4)     # 1 revolution every 5 seconds
SLOW_ACCLE_QPPS = 500
MED_ACCL_QPPS = 1000
FAST_ACCL_QPPS = 3000
HOME_POSITION = 0
STOP_DECEL = 500
STOP_ACCEL = 500
STATIONARY_POS_THRESHOLD_TIME = 0.1
SPEED_MAP = {
    "slow": SLOW_SPEED_QPPS,
    "med": MED_SPEED_QPPS,
    "fast": FAST_SPEED_QPPS,
    "home": HOME_POSITION
}
ACCEL_MAP = {
    "slow": SLOW_ACCLE_QPPS,
    "med": MED_ACCL_QPPS,
    "fast": FAST_ACCL_QPPS,
}
POSITION_MAP = {
    "home": HOME_POSITION
}


# MISC CONSTANTS
USING_MOCK_PIN_FACTORY = False


import platform
import logging
import serial
import serial.serialutil
import threading
import time
from abc import ABC, abstractmethod
from Backend.roboclaw import RoboClaw
from gpiozero import Device, Servo, Button
from gpiozero.pins.mock import MockFactory, MockPWMPin

# Configures gpiozero by making a pin factory using the lgpio library.
# On non RPi platforms, use a mock factory to emulate functionality.
try:
    from gpiozero.pins.lgpio import LGPIOFactory
    Device.pin_factory = LGPIOFactory()
except ModuleNotFoundError as e:
    log = logging.getLogger("IOControllerSetup")
    if platform.system() == 'Linux':
        log.critical(f"GPIOZero failed to init: {e}")
    else:
        log.warning(f"Failed to init proper gpio factory: {e} Ignore if not running on a RPi.")
        log.warning("Program will continue with a virtual pin setup.")
    # Configuring the mock environment
    USING_MOCK_PIN_FACTORY = True
    Device.pin_factory = MockFactory(pin_class=MockPWMPin) # Gives every pin PWM Functionality.


# --- Abstract Base Class ---
class IOController(ABC):
    """
    Abstract base class for IO Controllers.
    Defines the required methods for reading control states and performing system-level actions.
    """

    estop_button: Button
    stop_button: Button
    dispatch_button: Button
    ride_onoff_button: Button
    reset_button: Button
    servo1: Servo
    servo2: Servo

    def get_button_map(self):
        return {
            "estop": self.estop_button,
            "stop": self.stop_button,
            "dispatch": self.dispatch_button,
            "rideonoff": self.ride_onoff_button,
            "reset": self.reset_button
        }

    def attach_on_press(self, button_name: str, func_call: callable):
        """Attaches a function call to be called when a specified button is pressed."""
        button = self.get_button_map().get(button_name)
        if button:
            button.when_activated = func_call
        else:
            self.log.error(f"Button {button_name} not found for method attach_on_press().")

    def attach_on_release(self, button_name: str, func_call: callable):
        """Attaches a function call to be called when a specified button is released."""
        button = self.get_button_map().get(button_name)
        if button:
            button.when_deactivated = func_call
        else:
            self.log.error(f"Button {button_name} not found for method attach_on_release().")

    @abstractmethod
    def send_motor_command(self, command: dict):
        ...

    @abstractmethod
    def read_estop(self) -> bool:
        """Return the state of the ESTOP input."""
        pass

    @abstractmethod
    def read_stop(self) -> bool:
        """Return the state of the STOP input."""
        pass

    @abstractmethod
    def read_dispatch(self) -> bool:
        """Return the state of the DISPATCH input."""
        pass

    @abstractmethod
    def read_ride_on_off(self) -> bool:
        """Return the state of the RIDE OFF input."""
        pass

    @abstractmethod
    def read_restart(self) -> bool:
        """Return the state of the RESTART input."""
        pass

    @abstractmethod
    def enable_motors(self):
        """Enable the motor controllers."""
        pass

    @abstractmethod
    def disable_motors(self):
        """Disable the motor controllers."""
        pass

    @abstractmethod
    def terminate_power(self):
        """Immediately cut power (e.g., during ESTOP conditions)."""
        pass

    @abstractmethod
    def set_speed(self, speed):
        """Sets the speed of the motor"""
        pass

    @abstractmethod
    def drive_to_position_raw(self, accel, speed, deccel, position, buffer):
        """Drive to a position expressed as a percentage of the full range of the motor"""
        pass

    @abstractmethod
    def drive_to_position(self, accel, speed, deccel, position, buffer):
        """Sets the speed of the motor"""
        pass

    @abstractmethod
    def stop_motor(self):
        """Stops the motor"""
        pass

    @abstractmethod
    def read_encoder(self):
        """
        Reads the motor encoder.
        NOTE: Currently, this function doesn't check over/underflow, which is fine since we're using pots.
        """
        pass

    @abstractmethod
    def reset_quad_encoders(self):
        """Resets the encoder to 0."""
        pass

    @abstractmethod
    def read_range(self):
        """
        Unsure what this one does.
        TODO: Read manual.
        """
        pass

    @abstractmethod
    def read_position(self) -> dict:
        """Returns position as a percentage across the full set range of the motor"""
        pass

    @abstractmethod
    def read_status(self) -> str:
        """Gets the status of the MC."""
        pass

    @abstractmethod
    def read_temp_sensor(self, sensor):
        """Reads temp from specified sensor (1 or 2)"""
        pass

    @abstractmethod
    def read_voltages(self) -> tuple:
        """Returns a tuple with [0]: main battery. [1]: logic battery."""
        pass

    @abstractmethod
    def read_motor_current(self):
        """Gets motor current"""
        pass

    @abstractmethod
    def read_motor_pwm(self):
        """Reads motor pwm"""
        pass

    @abstractmethod
    def read_input_pin_modes(self) -> tuple:
        """
        Reads what input pins are set to (s3-s5)
        [0]: S3
        [1]: S4
        [2]: S5
        """
        pass
    
    @abstractmethod
    def read_max_speed(self):
        """Reads max speed of the motor"""
        pass

    @abstractmethod
    def read_speed(self):
        """
        Reads the current speed of the motor
        Returns velocity as a percentage of max speed
        """
        pass

    @abstractmethod
    def extend_servos(self):
        pass

    @abstractmethod
    def retract_servos(self):
        pass



# --- Hardware IO Controller ---
class HardwareIOController(IOController):
    """
    Handles all hardware I/O operations for the ride control computer.
    Uses gpiozero for reading physical button states and executes system-level actions.
    """
    def __init__(self):
        self.log = logging.getLogger('IOController')

        if USING_MOCK_PIN_FACTORY:
            factory = MockFactory(pin_class=MockPWMPin)
        else:
            factory = LGPIOFactory()

        # Initialize GPIO inputs as buttons (pull-down enabled by default)
        self.estop_button = Button(ESTOP_PIN, pull_up=False, pin_factory=factory)
        self.stop_button = Button(STOP_PIN, pull_up=False, pin_factory=factory)
        self.dispatch_button = Button(DISPATCH_PIN, pull_up=False, pin_factory=factory)
        self.ride_onoff_button = Button(RIDE_ONOFF_PIN, pull_up=False, pin_factory=factory)
        self.reset_button = Button(RESTART_PIN, pull_up=False, pin_factory=factory)
        self.servo1 = Servo(pin=SERVO1_PIN, pin_factory=factory)
                    # min_pulse_width=600/1_000_000,   # 0.0006
                    # max_pulse_width=2400/1_000_000,  # 0.0024
                    # frame_width=20/1000)             # 0.02 (20 ms standard servo frame)
        self.servo2 = Servo(pin=SERVO2_PIN, pin_factory=factory)
                    # min_pulse_width=600/1_000_000,   # 0.0006
                    # max_pulse_width=2400/1_000_000,  # 0.0024
                    # frame_width=20/1000)             # 0.02 (20 ms standard servo frame)

        # Init RoboClaw
        self.log.info(f"Starting Serial communication with RoboClaw on {ROBOCLAW_SERIAL_PORT}: {ROBOCLAW_SERIAL_ADDRESS}")
        try:
            self.mc = RoboClaw(ROBOCLAW_SERIAL_PORT, ROBOCLAW_SERIAL_ADDRESS, auto_recover=False)
        except (serial.serialutil.SerialException, FileNotFoundError, Exception) as e:
            
            self.log.critical(f"Failed to start RoboClaw: {e}")
            self.log.critical("Creating a mock RoboClaw and ignoring any future calls.")
            class NullRoboClaw:
                def __getattr__(self, name):
                    return lambda *args, **kwargs: None
            self.mc = NullRoboClaw()

        self.log.info("Finished Initializing Hardware IOController!")

    # --- Hardware Read Methods ---
    def read_estop(self) -> bool:
        return self.estop_button.is_pressed

    def read_stop(self) -> bool:
        return self.stop_button.is_pressed

    def read_dispatch(self) -> bool:
        return self.dispatch_button.is_pressed

    def read_ride_on_off(self) -> bool:
        return self.ride_onoff_button.is_pressed

    def read_restart(self) -> bool:
        return self.reset_button.is_pressed

    # --- System-Level Functions ---
    def terminate_power(self):
        """Immediately cut power (used during ESTOP or ride off conditions)."""
        # self.log.info("Power Terminated.")
        self.disable_motors()

    def enable_motors(self):
        """Enable the motor controllers (used during dispatch or restart)."""
        # self.log.info("Motors enabled.")
        # Insert hardware-specific logic here

    def disable_motors(self):
        """Disable the motor controllers (used during STOP or ESTOP)."""
        # self.log.info("Motors disabled.")
        # Insert hardware-specific logic here


    # --- Motor Control Methods ---
    def send_motor_command(self, command) -> bool:
        """
        Returns:
            Bool: Returns true if the ride is in a stopped home position
        """
        try:
            Im1 = f"{self.mc.read_currents()[0]}A"
            enc = self.mc.read_encoder_m1().get("encoder")
            speed = self.mc.read_raw_speed_m1()
            print(f"exec cmd: {command}")
            if command == None:
                self.mc.set_speed_with_acceleration(1,0, FAST_SPEED_QPPS)
                return
            elif command.get('name') == "Move":
                self._position_mode_active = False
                # Parse command
                speed_str = command.get('speed', 'med').lower()
                speed = SPEED_MAP.get(speed_str, MED_SPEED_QPPS)
                direction = command.get('direction') or 'fwd'
                speed *= -1 if direction == 'bwd' else 1
                accel_str = command.get('accel', 'med').lower()
                accel = ACCEL_MAP.get(accel_str, ACCEL_MAP['med'])

                # Print telemetry
                # Im1 = f"{self.mc.read_currents()[0]}A"
                # enc = self.mc.read_raw_speed_m1()
                # print(f"Current: {Im1}, Spd: {enc}")

                self.mc.set_speed_with_acceleration(1, speed, accel)
            elif command.get('name') == "Position":
                # In order for a position command to be executed, the motor must be stationary for a period of time.
                # Non-blocking check: ensure the motor has been stationary for 1 second
                if not hasattr(self, '_position_mode_active'):
                    self._position_mode_active = False
                if not hasattr(self, '_stationary_start_time'):
                    self._stationary_start_time = None

                if not self._position_mode_active:
                    # If the motor has any speed, reset the stationary timer and return early
                    if speed != 0:
                        self.stop_motor()
                        self._stationary_start_time = time.time()
                        return
                    else:
                        # Start timer if not already started
                        if self._stationary_start_time is None:
                            self._stationary_start_time = time.time()
                            return
                        # If motor hasn't been stationary for 1 second, return early
                        elif time.time() - self._stationary_start_time < STATIONARY_POS_THRESHOLD_TIME:
                            return
                        else:
                            # Motor has been stationary for 1 second; enable position mode
                            time.sleep(0.2)
                            self._position_mode_active = True

                        
                position_str = command.get('pos', 'home').lower()
                position = POSITION_MAP.get(position_str, 'home')

                # Print telemetry
                # Im1 = f"{self.mc.read_currents()[0]}A"
                # enc = self.mc.read_encoder_m1().get("encoder")
                print(f"Current: {Im1}, Enc: {enc}, Spd {speed}")

                self.mc.drive_to_position_with_speed_acceleration_deceleration(1, position, 1000, STOP_ACCEL, STOP_DECEL, 0)

                if abs(enc) < 10 and abs(speed) < 10:
                    return True
            else:
                self._position_mode_active = False
                self.stop_motor()
        except Exception as e:
            self.log.error(f"Can't communicate with MC: {e}")

    def extend_servos(self):
        self.servo1.value = SERVO_OUT_POSITION
        self.servo2.value = SERVO_OUT_POSITION

    def retract_servos(self):
        self.servo1.value = SERVO_IN_POSITION
        self.servo2.value = SERVO_IN_POSITION
    
    def set_speed(self, speed): self.mc.set_speed(SELECTED_MOTOR, speed)

    def drive_to_position_raw(self, accel, speed, deccel, position, buffer): self.mc.drive_to_position_raw(SELECTED_MOTOR, accel, speed, deccel, position, buffer)
    
    def drive_to_position(self, accel, speed, deccel, position, buffer): self.mc.drive_to_position(SELECTED_MOTOR, accel, speed, deccel, position, buffer)

    def stop_motor(self): self.mc.set_speed_with_acceleration(SELECTED_MOTOR, 0, FAST_SPEED_QPPS)

    def reset_quad_encoders(self): self.mc.reset_quad_encoders()

    def read_encoder(self): return self.mc.read_encoder(SELECTED_MOTOR)

    def read_range(self): return self.mc.read_range(SELECTED_MOTOR)

    def read_position(self) -> dict: return self.mc.read_encoder_m1()

    def read_status(self): return self.mc.read_status()

    def read_temp_sensor(self, sensor): return self.mc.read_temp_sensor(sensor)

    def read_voltages(self) -> tuple: return self.mc.read_voltages()

    def read_motor_current(self): return self.mc.read_motor_current(SELECTED_MOTOR)

    def read_motor_pwm(self): return self.mc.read_motor_pwm(SELECTED_MOTOR)

    def read_input_pin_modes(self) -> tuple: return self.mc.read_input_pin_modes()

    def read_max_speed(self): return self.mc.read_max_speed(SELECTED_MOTOR)

    def read_speed(self): return self.mc.read_raw_speed_m1()




# --- Simulation Controller ---
class WebIOController(IOController):
    """
    Encapsulates simulation and testing actions for the ride control computer.
    This class manages internal simulated states and mimics button presses without affecting the hardware.
    Optionally, it can wrap an IOController instance to trigger real hardware actions when needed.
    """
    def __init__(self):
        self.log = logging.getLogger('WebIOController')
        mock = MockFactory(pin_class=MockPWMPin)

        self.estop_button = Button(ESTOP_PIN, pull_up=False, pin_factory=mock)
        self.stop_button = Button(STOP_PIN, pull_up=False, pin_factory=mock)
        self.dispatch_button = Button(DISPATCH_PIN, pull_up=False, pin_factory=mock)
        self.ride_onoff_button = Button(RIDE_ONOFF_PIN, pull_up=False, pin_factory=mock)
        self.reset_button = Button(RESTART_PIN, pull_up=False, pin_factory=mock)
        self.servo1 = Servo(pin=SERVO1_PIN, pin_factory=mock)
        self.servo2 = Servo(pin=SERVO2_PIN, pin_factory=mock)

    def read_estop(self) -> bool: return self.estop_button.is_active
    def read_stop(self) -> bool: return self.stop_button.is_active
    def read_dispatch(self) -> bool: return self.dispatch_button.is_active
    def read_ride_on_off(self) -> bool: return self.ride_onoff_button.is_active
    def read_restart(self) -> bool: return self.reset_button.is_active
    
    def enable_motors(self):
        pass

    def disable_motors(self):
        pass

    def terminate_power(self):
        pass

    # --- Simulation Methods ---
    def simulate_estop_toggle(self):
        """Simulate toggling the ESTOP for testing purposes."""
        if self.estop_button.is_active:
            self.estop_button.pin.drive_low()
        else:
            self.estop_button.pin.drive_high()
        self.log.info(f"Simulated ESTOP pressed")

    def simulate_stop_toggle(self):
        """Simulate toggling the STOP for testing purposes."""
        if self.stop_button.is_active:
            self.stop_button.pin.drive_low()
        else:
            self.stop_button.pin.drive_high()
        self.log.info(f"Simulated STOP pressed")

    def simulate_dispatch(self):
        """Simulate a dispatch press (active for one second)."""
        def press_and_release():
            self.dispatch_button.pin.drive_high()
            self.log.info("Simulated DISPATCH pressed.")
            time.sleep(1)
            self.dispatch_button.pin.drive_low()
            self.log.info("Simulated DISPATCH released.")
        threading.Thread(target=press_and_release, daemon=True).start()

    def simulate_ride_off(self):
        """Simulate a ride off press (active for one second)."""
        def press_and_release():
            self.ride_onoff_button.pin.drive_high()
            self.log.info("Simulated RIDE OFF pressed.")
            time.sleep(1)
            self.ride_onoff_button.pin.drive_low()
            self.log.info("Simulated RIDE OFF released.")
        threading.Thread(target=press_and_release, daemon=True).start()

    def simulate_reset(self):
        """Simulate a restart press (active for one second)."""
        def press_and_release():
            self.reset_button.pin.drive_high()
            self.log.info("Simulated RESTART pressed.")
            time.sleep(1)
            self.reset_button.pin.drive_low()
            self.log.info("Simulated RESTART released.")
        threading.Thread(target=press_and_release, daemon=True).start()

    # --- Motor Control Methods ---
    def set_speed(self, speed): return None

    def drive_to_position_raw(self, accel, speed, deccel, position, buffer): return None

    def drive_to_position(self, accel, speed, deccel, position, buffer): return None

    def stop_motor(self): return None

    def read_encoder(self): return 12345

    def reset_quad_encoders(self): return None

    def read_range(self): return (0, 100000)

    def read_position(self): return 50.0

    def read_status(self): return "Normal"

    def read_temp_sensor(self, sensor): return 42.0

    def read_voltages(self) -> tuple: return (24.5, 5.1)

    def read_motor_current(self): return 1.25

    def read_motor_pwm(self): return 0.75

    def read_input_pin_modes(self) -> tuple: return ("Default", "Emergency Stop", "Disabled")

    def read_max_speed(self): return 100000

    def read_speed(self): return 32.5

    def send_motor_command(self, command): return None

    def extend_servos(self):
        pass

    def retract_servos(self):
        pass

class IOControllerFactory():
    """Class to dispatch IOController objects at runtime without duplication"""
    hardware: HardwareIOController
    web: WebIOController
    def __init__(self):
        self.hardware = HardwareIOController()
        self.web = WebIOController()

    def get(self, type: str):
        if type == 'web':
            return self.web
        elif type == 'hardware':
            return self.hardware
        else:
            raise KeyError(f"IOController Type {type} not recognized!")


# if __name__ == "__main__":
#     from gpiozero import Button
#     from gpiozero.pins.mock import MockFactory

#     # Create a mock pin factory
#     mock_factory = MockFactory()

#     # Create a mock button on pin 1 using the mock factory
#     button = Button(1, pin_factory=mock_factory)

#     # Check the initial state (usually not pressed)
#     print("Initial button state:", button.is_pressed)

#     button.when_activated = lambda: print("PRESSED")

#     # To simulate a button press, you can change the state of the underlying pin.
#     # For instance, if your button is active-low, you might drive the pin low to simulate a press:
#     button.pin.drive_low()  # simulate press
#     print("Button state after press simulation:", button.is_pressed)

#     # And then drive the pin high to simulate a release:
#     button.pin.drive_high()  # simulate release
#     print("Button state after release simulation:", button.is_pressed)

# if __name__ == "__main__":

#     print("V>P TEST")
#     io = HardwareIOController()


#     start_time = time.time()
#     while time.time() - start_time < 5:
#         io.send_motor_command({"name": "Move", "duration": 5, "speed": "slow", "direction": "fwd", "accel": "slow"})

#     # start_time = time.time()
#     # while time.time() - start_time < 2:
#     #     io.stop_motor()

#     # start_time = time.time()
#     # while time.time() - start_time < 2:
#     #     # io.send_motor_command({"name": "Position", "duration": 5, "pos": "home"})
#     #     io.send_motor_command({"name": "Move", "duration": 5, "speed": "fast", "direction": "bwd", "accel": "fast"})


#     # start_time = time.time()
#     while io.read_speed() != 0:
#         io.stop_motor()

#     # del io
#     start_time = time.time()
#     while time.time() - start_time < 0.2:
#         pass
#     # time.sleep(1)
#     print("POS TEST")

#     # io = HardwareIOController()

#     start_time = time.time()
#     # while time.time() - start_time < 5:
#     while io.read_position().get("encoder") != 0:
#         io.send_motor_command({"name": "Position", "duration": 5, "pos": "home"})
#         time.sleep(0.01)

#     io.stop_motor()

if __name__ == "__main__":


    io = HardwareIOController()

    while True:
        io.extend_servos()
        time.sleep(2)
        io.retract_servos()
        time.sleep(2)

