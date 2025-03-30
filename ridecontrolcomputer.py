# Ride Control Computer class for TREC's REC Ride Control Computer
    # Contibuters:
    # Jackson Justus (jackjust@bu.edu)
    # Aryan Kumar 

import logging
from enum import Enum
from typing import List
from Backend.iocontroller import IOController, HardwareIOController, WebIOController, IOControllerFactory
from Backend.faults import Fault, FaultManager, FaultSeverity
from Backend.ridemotioncontroller import RideMotionController
from Backend.state import State
from Backend.states import *
from Backend.event import *

class RideControlComputer():
    '''
    This class outlines the functionality of the RCC.
    '''
    # I/O
    ioFactory: IOControllerFactory
    io: IOController
    log: logging.Logger

    # Ride controllers
    state: State
    EStop: bool
    OnSwitchActive: bool
    Reset: bool

    def __init__(self, useWebIOController=False, demoMode = False):
        '''
        Creates a RideControlComputer object.
        Should NOT initialize any functions. This is left for the initialize() func.

        Params:
            useWebIOController (bool): True if this should default to the web IO Controller
            demoMode (bool): True if the rcc should ignore control all logic and start the ride sequence.
        '''
        # Get logger
        self.log = logging.getLogger('RCC')

        # Init vars to safe position
        self.state = OffState()
        self.initialized = False
        self.ioControllerType = 'web' if useWebIOController else 'hardware'
        self.log.info(f"Created RCC w/ Control Type {self.ioControllerType}")
        self.demoMode = demoMode
        if demoMode: self.log.warning("Demo Mode enabled: RCC Will ignore control logic.")

        # Initialize fault manager
        self.fault_manager = FaultManager()

    def initialize(self):
        '''
        Initialize the RCC.
        Carries out the actions detailed in the theory of operations.
        '''
        # Initialize I/O
        self.ioFactory = IOControllerFactory()
        self.io = self.ioFactory.get(self.ioControllerType)

        # Attach callback methods to io funcs
        def handle_io_estop(): self.state = self.state.on_event(EStopPressed())
        def handle_io_stop(): self.state = self.state.on_event(StopPressed())
        def handle_io_dispatch(): self.state = self.state.on_event(DispatchedPressed())
        def handle_io_ride_on_off(): self.state = self.state.on_event(RideOnOffPressed())
        def handle_io_reset(): self.state = self.state.on_event(ResetPressed())
        self.io.attach_on_press("estop", handle_io_estop)
        self.io.attach_on_press("stop", handle_io_stop)
        self.io.attach_on_press("dispatch", handle_io_dispatch)
        self.io.attach_on_press("rideonoff", handle_io_ride_on_off)
        self.io.attach_on_press("reset", handle_io_reset)

        # Define state specific enter/exit actions
        OffState._on_exit = lambda self: self.log.info('Leaving OFF State')

        # Initialize Ride Motion Controller
        self.rmc = RideMotionController()

        self.initialized = True
        self.log.info(f"Ride Control Computer Initialized!")

    def start(self):
        '''
        Starts the update loop for the RCC
        '''
        if not self.initialized:
            raise Exception('RCC Hasn\'t been initalized; Can\'t start.')
        
        while True:
            self.update()

    def update(self):
        '''
        Main logic update loop.
        It should be called as often as possible.

        NOTE: IO events automatically call their respective states when pressed. 
        NOTE: See initialize() for more info.
        '''

        # **Check for faults using sensor and encoder comparisons**
        self.fault_manager.check_faults(self.io, self.rmc)

        # Process non-io events.
        if self.is_estop_active():
            self.state = self.state.on_event(EStopPressed())

        # **Execute state-specific actions**
        self.state.run()

        # Execute specific actions if in running state:
        if isinstance(self.state, RunningState) or self.demoMode:
            if not self.rmc.is_running:
                self.rmc.start_cycle()
            current_motor_instruction = self.rmc.update()
            self.io.send_motor_command(current_motor_instruction)
            

    def is_estop_active(self) -> bool:
        ''' Returns True if any ESTOP condition is active '''
        return (
            self.io.read_estop() or  # Hardware ESTOP
            self.fault_manager.faultRequiresEStop # Faults requiring an ESTOP
        )
    
    def run_ride(self):
        '''
        This will run the ride under normal conditions.
        TODO: Implement
        '''

        dt = 0.1  # time delta, for example
        instruction = self.rmc.update(dt)
        if instruction is not None:
            # Pass the instruction to the IO controller for execution.
            ...

    def change_io_controller(self, controller_type: str) -> str:
        """
        Switches the IO controller to a new implementation at runtime.
        
        Parameters:
            controller_type (str): A string specifying which IO controller to use. Accepted values are "hardware" or "web".
        """
        io_type = controller_type.lower()
        if io_type == "hardware" or io_type ==  "web":
            self.io = self.ioFactory.get(io_type)
            self.ioControllerType = io_type
        else:
            raise ValueError(f"Invalid IO controller type: {io_type}")
        self.log.info(f'Switched IO controller to: {self.ioControllerType}')

    def toggle_io_controller(self) -> str:
        """
        Toggles the IO controller between hardware and web implementations.

        Returns:
            str: The type of control that was switched to.
        """
        if isinstance(self.io, HardwareIOController):
            self.ioControllerType = "web"
        elif isinstance(self.io, WebIOController):
            self.ioControllerType = "hardware"
        else:
            raise ValueError("Current IO controller is not recognized. Cannot toggle.")
        self.change_io_controller(self.ioControllerType)
        return self.ioControllerType


if __name__ == '__main__':

    rcc = RideControlComputer()
    rcc.initialize()
    rcc.state = RunningState()
    rcc.start()

