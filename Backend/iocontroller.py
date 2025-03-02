# IOController class for TREC's REC Ride Control Computer
    # Made by Jackson Justus (jackjust@bu.edu)

import logging
# import roboclaw

class IOController():
    '''
    This class handles all the I/O operations for the RCC.
    '''
    def __init__(self):
        self._estop = False
        self._on_switch = False
        self._reset_switch = False

        self.log = logging.getLogger('IOController')


    def read_estop(self) -> bool:
        """Read the emergency stop status (True if ESTOP is active)."""
        return self._estop

    def read_on_switch(self) -> bool:
        """Read the on switch status (True if ON switch is active)."""
        return self._on_switch

    def read_reset_switch(self) -> bool:
        """Read the reset switch status (True if RESET switch is active)."""
        return self._reset_switch


    # State action methods
    def terminate_power(self):
        self.log.info("Power Terminated.")
        self.disable_motors()

    def enable_safety_mechanisms(self):
        self.log.info("Enabling safety mechanisms...")
        # Implement safety code

    def enable_motors(self):
        self.log.info("Motors enabled.")
        # self.enable_motors()

    def disable_motors(self):
        self.log.info("Motors disabled.")
        # self.disable_motors()