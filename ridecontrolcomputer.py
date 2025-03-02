# Ride Control Computer class for TREC's REC Ride Control Computer
    # Contibuters:
    # Jackson Justus (jackjust@bu.edu)
    # Aryan Kumar 

import logging
from enum import Enum
from Backend.iocontroller import IOController
from Backend.faults import Fault, FaultManager, FaultSeverity
from Backend.ridemotioncontroller import RideMotionController

class State(Enum):
    IDLE = 1
    RUNNING = 2
    ESTOPPED = 3
    RESETTING = 4


class RideControlComputer():
    '''
    This class outlines the functionality of the RCC.
    '''
    # I/O
    io: IOController
    log: logging.Logger

    # Ride controllers
    _state: State
    ESTOP: bool
    OnSwitchActive: bool
    ResetSwitchActive: bool

    def __init__(self):
        '''
        Creates a RideControlComputer object.
        Should NOT initialize any functions. This is left for the initialize() func.
        '''
        # Init vars to safe position
        self.ESTOP = False
        self.OnSwitchActive = False
        self.ResetSwitchActive = False
        self._state = State.IDLE
        self.initialized = False

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
        self.io = IOController()

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
        self.ESTOP = self.is_estop_active()
        self.OnSwitchActive = self.io.read_on_switch()
        self.ResetSwitchActive = self.io.read_reset_switch()

        # Transition logic
        if self.ESTOP:
            self.state = State.ESTOPPED
        elif self.state == State.ESTOPPED and self.ResetSwitchActive:
            self.state = State.RESETTING
        elif self.state == State.RESETTING and not self.ResetSwitchActive:
            self.state = State.IDLE
        elif self.state == State.IDLE and self.OnSwitchActive:
            self.state = State.RUNNING

        # Execute state-specific actions
        if self.state == State.ESTOPPED:
            self.io.terminate_power()
        elif self.state == State.RUNNING:
            self.io.enable_safety_mechanisms()
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
    
    def run_ride():
        '''
        This will run the ride under normal conditions.
        '''

        dt = 0.1  # time delta, for example
        instruction = rmc.update(dt)
        if instruction is not None:
            # Pass the instruction to the IO controller for execution.
            io_controller.execute_instruction(instruction)


    # State Getter/Setters
    @property
    def state(self):
        '''State getter'''
        return self._state

    @state.setter
    def state(self, new_state):
        ''' Setter for the state, detects changes and runs transition logic '''
        if new_state != self._state:
            self.log.info(f'Changed from {self._state.name} to {new_state.name}')
            self._state = new_state  # Update state
