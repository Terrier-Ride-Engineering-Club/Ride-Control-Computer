# IO Controller for TREC's REC Ride Control Computer
    # Made by Jackson Justus (jackjust@bu.edu)

import platform
import logging
import serial
from gpiozero import Device, Servo
import serial.serialutil

ROBOCLAW_SERIAL_PORT = "/dev/ttyS0"
ROBOCLAW_SERIAL_ADDRESS = 38400
SELECTED_MOTOR = 1

# Configure gpiozero by making a pin factory. On non RPi platforms, default to mock factory.
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
    from gpiozero.pins.mock import MockFactory
    Device.pin_factory = MockFactory()

from gpiozero import Button
import threading
import time
from abc import ABC, abstractmethod
from roboclaw import RoboClaw


# --- Abstract Base Class ---
class IOController(ABC):
    """
    Abstract base class for IO Controllers.
    Defines the required methods for reading control states and performing system-level actions.
    """

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
    def read_ride_off(self) -> bool:
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
    def read_status(self):
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

        # Define GPIO pin mappings (using BCM numbering)
        self.pin_map = {
            'estop': 4,
            'stop': 17,
            'dispatch': 27,
            'ride_off': 22,
            'restart': 23,
            'servo1': "GPIO12"
        }

        # Initialize GPIO inputs as buttons (pull-down enabled by default)
        self.estop_button = Button(self.pin_map['estop'], pull_up=False)
        self.stop_button = Button(self.pin_map['stop'], pull_up=False)
        self.dispatch_button = Button(self.pin_map['dispatch'], pull_up=False)
        self.ride_off_button = Button(self.pin_map['ride_off'], pull_up=False)
        self.restart_button = Button(self.pin_map['restart'], pull_up=False)
        self.servo1 = Servo(pin=self.pin_map['servo1'])

        # Init RoboClaw
        self.log.info(f"Starting Serial communication with RoboClaw on {ROBOCLAW_SERIAL_PORT}: {ROBOCLAW_SERIAL_ADDRESS}")
        try:
            self.mc = RoboClaw(ROBOCLAW_SERIAL_PORT, ROBOCLAW_SERIAL_ADDRESS)
        except serial.serialutil.SerialException as e:
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

    def read_ride_off(self) -> bool:
        return self.ride_off_button.is_pressed

    def read_restart(self) -> bool:
        return self.restart_button.is_pressed

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
    def __init__(self, io_controller: HardwareIOController = None):
        self.io_controller = io_controller  # Optional, if you want to delegate to hardware actions
        self.log = logging.getLogger('IOControllerSimulator')

        # Internal simulated states
        self._estop = False
        self._stop = False
        self._dispatch = False
        self._ride_off = False
        self._restart = False

    def read_estop(self) -> bool:
        return self._estop

    def read_stop(self) -> bool:
        return self._stop

    def read_dispatch(self) -> bool:
        return self._dispatch

    def read_ride_off(self) -> bool:
        return self._ride_off

    def read_restart(self) -> bool:
        return self._restart
    
    def enable_motors(self):
        pass

    def disable_motors(self):
        pass

    def terminate_power(self):
        pass

    # --- Simulation Methods ---
    def simulate_estop(self):
        """Simulate toggling the ESTOP for testing purposes."""
        self._estop = not self._estop
        self.log.info(f"Simulated ESTOP toggled to {self._estop}")

    def simulate_stop(self):
        """Simulate toggling the STOP for testing purposes."""
        self._stop = not self._stop
        self.log.info(f"Simulated STOP toggled to {self._stop}")

    def simulate_dispatch(self):
        """Simulate a dispatch press (active for one second)."""
        def press_and_release():
            self._dispatch = True
            self.log.info("Simulated DISPATCH pressed.")
            time.sleep(1)
            self._dispatch = False
            self.log.info("Simulated DISPATCH released.")
        threading.Thread(target=press_and_release, daemon=True).start()

    def simulate_ride_off(self):
        """Simulate a ride off press (active for one second)."""
        def press_and_release():
            self._ride_off = True
            self.log.info("Simulated RIDE OFF pressed.")
            time.sleep(1)
            self._ride_off = False
            self.log.info("Simulated RIDE OFF released.")
        threading.Thread(target=press_and_release, daemon=True).start()

    def simulate_restart(self):
        """Simulate a restart press (active for one second)."""
        def press_and_release():
            self._restart = True
            self.log.info("Simulated RESTART pressed.")
            time.sleep(1)
            self._restart = False
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

    io = HardwareIOController()

    while True:
        io.servo1.min()
        time.sleep(1)
        io.servo1.max()
        time.sleep(1)
