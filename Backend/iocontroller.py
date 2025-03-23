# IO Controller for TREC's REC Ride Control Computer
    # Made by Jackson Justus (jackjust@bu.edu)

import platform
import logging
from gpiozero import Device

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
            'restart': 23
        }

        # Initialize GPIO inputs as buttons (pull-down enabled by default)
        self.estop_button = Button(self.pin_map['estop'], pull_up=False)
        self.stop_button = Button(self.pin_map['stop'], pull_up=False)
        self.dispatch_button = Button(self.pin_map['dispatch'], pull_up=False)
        self.ride_off_button = Button(self.pin_map['ride_off'], pull_up=False)
        self.restart_button = Button(self.pin_map['restart'], pull_up=False)

        # Set up event callbacks for logging
        self.estop_button.when_pressed = lambda: self.log.info("ESTOP Activated")
        self.estop_button.when_released = lambda: self.log.info("ESTOP Released")

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


# --- Simulation Controller ---
class WebIOController:
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