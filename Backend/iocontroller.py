# IO Controller for TREC's REC Ride Control Computer
    # Made by Jackson Justus (jackjust@bu.edu)

# RCC GPIO PINOUT
ESTOP_PIN = 4
STOP_PIN = 17
DISPATCH_PIN = 27
RIDE_ONOFF_PIN = 22
RESTART_PIN = 23
SERVO1_PIN = "GPIO12"
SERVO2_PIN = "GPIO13"
#UART_TX = 14
#UART_RX = 15

# ROBOCLAW CONSTANTS
ROBOCLAW_SERIAL_PORT = "/dev/ttyS0"
ROBOCLAW_SERIAL_ADDRESS = 38400
SELECTED_MOTOR = 1

# MOTOR CONSTANTS
# NOTE: GoBilda 5303 series motor encoders have a resolution of 1425.1 PPR @ Output shaft
MOTOR_PPR = 1425.1
QUAD_COUNTS_PER_REVOLUTION = MOTOR_PPR * 4
# All speeds in Quad Pulses per Second (QPS)
SLOW_SPEED_QPPS = int(QUAD_COUNTS_PER_REVOLUTION / 15)     # 1 revolution every 20 seconds
MED_SPEED_QPPS = int(QUAD_COUNTS_PER_REVOLUTION / 10)    # 1 revolution every 10 seconds
FAST_SPEED_QPPS = int(QUAD_COUNTS_PER_REVOLUTION / 5)     # 1 revolution every 5 seconds
HOME_POSITION = 0


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
    from gpiozero.pins.mock import MockFactory, MockPWMPin
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

    def attach_on_press(self, button_name: str, func_call: callable):
        """Attaches a function call to be called when a specified button is pressed."""
        if button_name == "estop":
            self.estop_button.when_activated = func_call
        elif button_name == "stop":
            self.stop_button.when_activated = func_call
        elif button_name == "dispatch":
            self.dispatch_button.when_activated = func_call
        elif button_name == "rideonoff":
            self.ride_onoff_button.when_activated = func_call
        elif button_name == "reset":
            self.reset_button.when_activated = func_call
        else:
            self.log.error(f"Button {button_name} not found for method attach_on_press().")

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
    def drive_motor(self, speed):
        """Assert -64 <= speed <= 63"""
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
    def read_position(self):
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



# --- Hardware IO Controller ---
class HardwareIOController(IOController):
    """
    Handles all hardware I/O operations for the ride control computer.
    Uses gpiozero for reading physical button states and executes system-level actions.
    """
    def __init__(self):
        self.log = logging.getLogger('IOController')

        # Initialize GPIO inputs as buttons (pull-down enabled by default)
        self.estop_button = Button(ESTOP_PIN, pull_up=False)
        self.stop_button = Button(STOP_PIN, pull_up=False)
        self.dispatch_button = Button(DISPATCH_PIN, pull_up=False)
        self.ride_onoff_button = Button(RIDE_ONOFF_PIN, pull_up=False)
        self.reset_button = Button(RESTART_PIN, pull_up=False)
        self.servo1 = Servo(pin=SERVO1_PIN)
                    # min_pulse_width=600/1_000_000,   # 0.0006
                    # max_pulse_width=2400/1_000_000,  # 0.0024
                    # frame_width=20/1000)             # 0.02 (20 ms standard servo frame)
        self.servo2 = Servo(pin=SERVO2_PIN)
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
                    # Return a lambda that does nothing for any attribute
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
    def set_speed(self, speed): self.mc.set_speed(SELECTED_MOTOR, speed)

    def drive_to_position_raw(self, accel, speed, deccel, position, buffer): self.mc.drive_to_position_raw(SELECTED_MOTOR, accel, speed, deccel, position, buffer)
    
    def drive_to_position(self, accel, speed, deccel, position, buffer): self.mc.drive_to_position(SELECTED_MOTOR, accel, speed, deccel, position, buffer)

    def drive_motor(self, speed): self.mc.drive_motor(SELECTED_MOTOR, speed)

    def stop_motor(self): self.mc.stop_motor(SELECTED_MOTOR)

    def read_encoder(self): return self.mc.read_encoder(SELECTED_MOTOR)

    def reset_quad_encoders(self): self.mc.reset_quad_encoders()

    def read_range(self): return self.mc.read_range(SELECTED_MOTOR)

    def read_position(self): return self.mc.read_position(SELECTED_MOTOR)

    def read_status(self): return self.mc.read_status()

    def read_temp_sensor(self, sensor): return self.mc.read_temp_sensor(sensor)

    def read_voltages(self) -> tuple: return self.mc.read_voltages()

    def read_motor_current(self): return self.mc.read_motor_current(SELECTED_MOTOR)

    def read_motor_pwm(self): return self.mc.read_motor_pwm(SELECTED_MOTOR)

    def read_input_pin_modes(self) -> tuple: return self.mc.read_input_pin_modes()

    def read_max_speed(self): return self.mc.read_max_speed(SELECTED_MOTOR)

    def read_speed(self): return self.mc.read_speed(SELECTED_MOTOR)




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

    def drive_motor(self, speed): return None

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



if __name__ == "__main__":
    from gpiozero import Button
    from gpiozero.pins.mock import MockFactory

    # Create a mock pin factory
    mock_factory = MockFactory()

    # Create a mock button on pin 1 using the mock factory
    button = Button(1, pin_factory=mock_factory)

    # Check the initial state (usually not pressed)
    print("Initial button state:", button.is_pressed)

    button.when_activated = lambda: print("PRESSED")

    # To simulate a button press, you can change the state of the underlying pin.
    # For instance, if your button is active-low, you might drive the pin low to simulate a press:
    button.pin.drive_low()  # simulate press
    print("Button state after press simulation:", button.is_pressed)

    # And then drive the pin high to simulate a release:
    button.pin.drive_high()  # simulate release
    print("Button state after release simulation:", button.is_pressed)