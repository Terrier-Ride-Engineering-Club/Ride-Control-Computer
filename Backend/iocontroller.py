# IOController class for TREC's REC Ride Control Computer
    # Made by Jackson Justus (jackjust@bu.edu)

import logging
import threading
import time
import roboclaw

# IOController class for TREC's REC Ride Control Computer
# Made by Jackson Justus (jackjust@bu.edu)

import logging

class IOController():
    '''
    This class handles all the I/O operations for the RCC.
    '''
    def __init__(self):
        self._estop = False
        self._stop = False
        self._dispatch = False
        self._ride_off = False
        self._restart = False

        self.log = logging.getLogger('IOController')

    # --- Read Input States ---

    def read_estop(self) -> bool:
        """Read the emergency stop status (True if ESTOP is active)."""
        return self._estop

    def read_stop(self) -> bool:
        """Read the stop button status (True if STOP is active)."""
        return self._stop

    def read_dispatch(self) -> bool:
        """Read the dispatch button status (True if DISPATCH is active)."""
        return self._dispatch

    def read_ride_off(self) -> bool:
        """Read the ride off status (True if RIDE OFF is active)."""
        return self._ride_off

    def read_restart(self) -> bool:
        """Read the restart button status (True if RESTART is active)."""
        return self._restart

    # --- State Action Methods ---
    # NOTE: The only use of these should be for the webserver.
    def toggle_estop(self):
        """Simulates the estop being toggled"""
        self._estop = not self._estop

    def toggle_stop(self):
        """Simulates the stop being toggled"""
        self._stop = not self._stop

    def trigger_dispatch(self):
        """Simulates the dispatch being pressed for one second"""
        # Uses a thread so the time.sleep() call doesn't block the main thread
        def press_and_release():
            self._dispatch = True
            time.sleep(1)  # Hold for 1 second
            self._dispatch = False
        threading.Thread(target=press_and_release, daemon=True).start()

    def trigger_ride_off(self):
        """Simulates the ride off being pressed for one second"""
        def press_and_release():
            self._ride_off = True
            time.sleep(1)  # Hold for 1 second
            self._ride_off = False
        threading.Thread(target=press_and_release, daemon=True).start()

    def trigger_restart(self):
        """Simulates the restart being pressed for one second"""
        def press_and_release():
            self._restart = True
            time.sleep(1)  # Hold for 1 second
            self._restart = False
        threading.Thread(target=press_and_release, daemon=True).start()
    
    # --- System-Level Functions ---
    
    def terminate_power(self):
        """Cut power immediately (used for ESTOP & Ride Off)."""
        self.log.info("Power Terminated.")
        self.disable_motors()

    def enable_motors(self):
        """Enable motor controllers (used for Dispatch & Restart)."""
        self.log.info("Motors enabled.")
        # Implement motor enabling logic here

    def disable_motors(self):
        """Disable motor controllers (used for STOP & ESTOP)."""
        self.log.info("Motors disabled.")
        # Implement motor disabling logic here