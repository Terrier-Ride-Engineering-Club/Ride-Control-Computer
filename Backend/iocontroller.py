# IO Controller for TREC's REC Ride Control Computer
    # Made by Jackson Justus (jackjust@bu.edu)

import platform
import logging
from gpiozero import Device
from gpiozero.pins.pigpio import PiGPIOFactory

# Use MockFactory for non-Raspberry Pi platforms.
if platform.system() != 'Linux':
    from gpiozero.pins.mock import MockFactory
    Device.pin_factory = MockFactory()
    logging.getLogger('IOController').warning(f'Current platform [{platform.system()}] ≠ Linux. IO Running in mock mode')
else:
    Device.pin_factory = PiGPIOFactory()

from gpiozero import Button
import threading
import time

from roboclaw import RoboClaw

class IOController():
    '''
    This class handles all the I/O operations for the RCC.
    It uses GPIO Zero for reading input states and exposes endpoints for the ride control computer to read these states.
    '''
    def __init__(self):
        self.log = logging.getLogger('IOController')

        # Initial internal states
        self._estop = False
        self._stop = False
        self._dispatch = False
        self._ride_off = False
        self._restart = False

        # Define GPIO pin mappings for each control signal (using BCM numbering)
        self.pin_map = {
            'estop': 4,       # Example: GPIO 4 for ESTOP
            'stop': 17,       # Example: GPIO 17 for STOP
            'dispatch': 27,   # Example: GPIO 27 for DISPATCH
            'ride_off': 22,   # Example: GPIO 22 for RIDE OFF
            'restart': 23     # Example: GPIO 23 for RESTART
        }

        # Define GPIO pin mappings for each control signal (using BCM numbering)
        # Initialize GPIO inputs as buttons (pull-down enabled by default)
        self.estop_button = Button(self.pin_map['estop'], pull_up=False)
        self.stop_button = Button(self.pin_map['stop'], pull_up=False)
        self.dispatch_button = Button(self.pin_map['dispatch'], pull_up=False)
        self.ride_off_button = Button(self.pin_map['ride_off'], pull_up=False)
        self.restart_button = Button(self.pin_map['restart'], pull_up=False)

        # Set up event callbacks to log state changes.
        self.estop_button.when_pressed = lambda: self.log.info("ESTOP Activated")
        self.estop_button.when_released = lambda: self.log.info("ESTOP Released")

        # Log finished initialization
        self.log.info("Finished Initalizing!")


    # --- Read Input States ---
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

    # --- State Action Methods ---
    # These can be used for simulation or to trigger actions if needed.
    def toggle_estop(self):
        """Simulate toggling the ESTOP (for testing purposes)."""
        self._estop = not self._estop

    def toggle_stop(self):
        """Simulate toggling the STOP (for testing purposes)."""
        self._stop = not self._stop

    def trigger_dispatch(self):
        """Simulate a dispatch press (active for one second)."""
        def press_and_release():
            self._dispatch = True
            time.sleep(1)
            self._dispatch = False
        threading.Thread(target=press_and_release, daemon=True).start()

    def trigger_ride_off(self):
        """Simulate a ride off press (active for one second)."""
        def press_and_release():
            self._ride_off = True
            time.sleep(1)
            self._ride_off = False
        threading.Thread(target=press_and_release, daemon=True).start()

    def trigger_restart(self):
        """Simulate a restart press (active for one second)."""
        def press_and_release():
            self._restart = True
            time.sleep(1)
            self._restart = False
        threading.Thread(target=press_and_release, daemon=True).start()

    # --- System-Level Functions ---
    def terminate_power(self):
        """Immediately cut power (used during ESTOP or ride off conditions)."""
        self.log.info("Power Terminated.")
        self.disable_motors()

    def enable_motors(self):
        """Enable the motor controllers (used during dispatch or restart)."""
        self.log.info("Motors enabled.")
        # Implement motor enabling logic here

    def disable_motors(self):
        """Disable the motor controllers (used during STOP or ESTOP)."""
        self.log.info("Motors disabled.")
        # Implement motor disabling logic here