# Ride Control Computer class for TREC's REC Ride Control Computer
# Made by Jackson Justus (jackjust@bu.edu)

import logging
from enum import Enum
from Backend.iocontroller import IOController

class State(Enum):
    IDLE = 1
    RUNNING = 2
    ESTOPPED = 3
    RESETTING = 4

class FaultSeverity(Enum):
    LOW = 1      # Warning, does not stop ride
    MEDIUM = 2   # Requires operator intervention
    HIGH = 3     # Stops ride immediately (ESTOP)

class Fault:
    def __init__(self, code, message, severity: FaultSeverity):
        self.code = code
        self.message = message
        self.severity = severity

    def __str__(self):
        return f"[{self.severity.name}] Fault {self.code}: {self.message}"

class FaultManager:
    def __init__(self):
        self.active_faults = []

    def log_fault(self, fault: Fault):
        print(f"FAULT OCCURRED: {fault}")
        self.active_faults.append(fault)

        if fault.severity == FaultSeverity.HIGH:
            print("EMERGENCY STOP TRIGGERED!")
            # Trigger ESTOP behavior here

    def clear_faults(self):
        self.active_faults.clear()

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

    def start(self):
        '''
        Starts the update loop for the RCC
        '''
        while True:
            self.update()

    def update(self):
        '''
        Main logic update loop.
        It should be called as often as possible.
        '''
        # Read inputs from I/O controller
        self.ESTOP = self.io.read_estop()
        self.OnSwitchActive = self.io.read_on_switch()
        self.ResetSwitchActive = self.io.read_reset_switch()

        # Transition logic
        if self.ESTOP:
            self.state = State.ESTOPPED
            self.fault_manager.log_fault(Fault(101, "Emergency Stop Activated", FaultSeverity.HIGH))
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
        elif self.state == State.IDLE:
            self.io.disable_motors()

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
