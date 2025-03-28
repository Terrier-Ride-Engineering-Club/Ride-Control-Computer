# Ride Control Computer class for TREC's REC Ride Control Computer
    # Contibuters:
    # Jackson Justus (jackjust@bu.edu)
    # Aryan Kumar 

import logging
from enum import Enum
from typing import List
from Backend.iocontroller import IOController, HardwareIOController, WebIOController
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
    io: IOController
    log: logging.Logger

    # Ride controllers
    state: State
    EStop: bool
    OnSwitchActive: bool
    Reset: bool

    def __init__(self, useWebIOController=False):
        '''
        Creates a RideControlComputer object.
        Should NOT initialize any functions. This is left for the initialize() func.
        '''
        # Init vars to safe position
        self.EStop = False
        self.OnSwitchActive = False
        self.Reset = False
        self.state = OffState()
        self.initialized = False
        self.ioControllerType = 'web' if useWebIOController else 'hardware'

        # Get logger
        self.log = logging.getLogger('RCC')
        
        # Initialize fault manager
        self.fault_manager = FaultManager()

    def initialize(self):
        '''
        Initialize the RCC.
        Carries out the actions detailed in the theory of operations.
        '''
        # Initialize I/O
        if not self.ioControllerType:
            self.io = HardwareIOController()
        else:
            self.io = WebIOController()

        # Initialize Ride Motion Controller
        self.rmc = RideMotionController()

        self.initialized = True

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
        It should be called as often as possible
        '''
        # Read input flags
        estop_active = self.is_estop_active()
        stop_active = self.io.read_stop()
        ride_on_off_active = self.io.read_ride_on_off()
        reset_active = self.io.read_restart()
        dispatch_active = self.io.read_dispatch()

        # **Check for faults using sensor and encoder comparisons**
        self.fault_manager.check_faults(self.io, self.rmc)

        # Process events in fixed priority order: EStop, Stop, RideOnOff, Reset, Dispatch
        if estop_active:
            self.state = self.state.on_event(EStopPressed())
        if stop_active:
            self.state = self.state.on_event(StopPressed())
        if ride_on_off_active:
            self.state = self.state.on_event(RideOnOffPressed())
        if reset_active:
            self.state = self.state.on_event(ResetPressed())
        if dispatch_active:
            self.state = self.state.on_event(DispatchedPressed())

        # **Execute state-specific actions**
        self.state.run()
            

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

    def change_io_controller(self, controller_type: str):
        """
        Switches the IO controller to a new implementation at runtime.
        
        Parameters:
            controller_type (str): A string specifying which IO controller to use. Accepted values are "hardware" or "web".
        """
        if controller_type.lower() == "hardware":
            self.io = HardwareIOController()
        elif controller_type.lower() == "web":
            self.io = WebIOController()
        else:
            raise ValueError(f"Invalid IO controller type: {controller_type}")
        self.log.info(f'Switched IO controller to: {self.io.__class__.__name__}')

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
