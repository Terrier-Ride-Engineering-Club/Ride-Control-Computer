# Ride Control Computer class for TREC's REC Ride Control Computer
    # Contibuters:
    # Jackson Justus (jackjust@bu.edu)
    # Aryan Kumar 

import logging
from enum import Enum
from Backend.iocontroller import IOController, HardwareIOController, WebIOController
from Backend.faults import Fault, FaultManager, FaultSeverity
from Backend.ridemotioncontroller import RideMotionController

class State(Enum):
    IDLE = 1
    RUNNING = 2
    ESTOPPED = 3
    RESETTING = 4
    OFF = 5


class RideControlComputer():
    '''
    This class outlines the functionality of the RCC.
    '''
    # I/O
    io: IOController
    log: logging.Logger

    # Ride controllers
    _state: State
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
        self._state = State.IDLE
        self.initialized = False
        self.useWebIOController = useWebIOController

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
        if not self.useWebIOController:
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
        It should be called as often as possible.
        '''
        # Read inputs from I/O controller
        self.EStop = self.is_estop_active()
        self.Stop = self.io.read_stop()
        self.RideOff = self.io.read_ride_off()
        self.Reset = self.io.read_restart()
        self.Dispatch = self.io.read_dispatch()


        # Transition logic
        if self.EStop:
            self.state = State.ESTOPPED
        elif self.Stop:
            self.state = State.IDLE
        else:
            if self.state == State.ESTOPPED:
                if self.Reset:
                    self.state = State.RESETTING
            elif self.state == State.RESETTING:
                if not self.Reset:
                    self.state = State.IDLE
            elif self.state == State.OFF:
                if self.Reset:
                    self.state = State.RESETTING
            elif self.state == State.IDLE:
                if self.RideOff:
                    self.state = State.OFF
                elif self.Dispatch:
                    self.state = State.RUNNING
            elif self.state == State.RUNNING:
                if self.Stop:
                    self.state = State.IDLE

        # Execute state-specific actions
        if self.state == State.ESTOPPED:
            self.io.terminate_power()
        elif self.state == State.RUNNING:
            self.io.enable_motors()
            self.run_ride()
        elif self.state == State.IDLE:
            self.io.disable_motors()
        else:
            self.io.disable_motors()


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


    # State Getter/Setters
    @property
    def state(self):
        '''State getter'''
        return self._state

    @state.setter
    def state(self, new_state: State):
        ''' Setter for the state, detects changes and runs transition logic '''
        if new_state.name != self._state.name:
            self.log.info(f'Changed from {self._state.name} to {new_state.name}')
            self._state = new_state  # Update state
