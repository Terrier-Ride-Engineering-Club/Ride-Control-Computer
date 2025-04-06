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
from Backend.faults import PREDEFINED_FAULTS
from Backend.state import State
from Backend.states import *
from Backend.event import *
import json

class RideControlComputer():
    '''
    This class outlines the functionality of the RCC.
    '''
    # I/O
    ioFactory: IOControllerFactory
    io: IOController
    log: logging.Logger
    eventList: List[Event] # Holds the IO Events currently active

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
        self._state = OffState()
        self.initialized = False
        self.ioControllerType = 'web' if useWebIOController else 'hardware'
        self.log.info(f"Created RCC w/ Control Type {self.ioControllerType}")
        self.demoMode = demoMode
        if demoMode: self.log.warning("Demo Mode enabled: RCC Will ignore control logic.")
        self.eventList = []
        self.position_command_finished = False
        self.servos_extended = False
        self.stopped_timer = 0
        self.servos_retracted_timer = 0

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

        def attach_button_callbacks(io: IOController):
            # Attach callback methods to io events
            def handle_io_estop_pressed(): self.create_event(EStopPressed()); self.update()
            def handle_io_stop_pressed(): self.create_event(StopPressed()); self.update()
            def handle_io_dispatch_pressed(): self.create_event(DispatchedPressed()); self.update()
            def handle_io_ride_on_off_pressed(): self.delete_event(RideOff()); self.create_event(RideOn());  self.update()
            def handle_io_reset_pressed(): self.create_event(ResetPressed()); self.update()
            io.attach_on_press("estop", handle_io_estop_pressed)
            io.attach_on_press("stop", handle_io_stop_pressed)
            io.attach_on_press("dispatch", handle_io_dispatch_pressed)
            io.attach_on_press("rideonoff", handle_io_ride_on_off_pressed)
            io.attach_on_press("reset", handle_io_reset_pressed)

            def handle_io_estop_released(): self.delete_event(EStopPressed()); self.update()
            def handle_io_stop_released(): self.delete_event(StopPressed()); self.update()
            def handle_io_dispatch_released(): self.delete_event(DispatchedPressed()); self.update()
            def handle_io_ride_on_off_released(): self.delete_event(RideOn()); self.create_event(RideOff()); self.update()
            def handle_io_reset_released(): self.delete_event(ResetPressed()); self.update()
            io.attach_on_release("estop", handle_io_estop_released)
            io.attach_on_release("stop", handle_io_stop_released)
            io.attach_on_release("dispatch", handle_io_dispatch_released)
            io.attach_on_release("rideonoff", handle_io_ride_on_off_released)
            io.attach_on_release("reset", handle_io_reset_released)

        attach_button_callbacks(self.ioFactory.get('web'))
        attach_button_callbacks(self.ioFactory.get('hardware'))

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
        
        if isinstance(self.state, EstoppedState):
            # Will stop motor through timeout
            pass
            # self.io.stop_motor()

        # **Execute state-specific actions**
        self.state.run()

        # Execute specific actions if in idle state:
        # if isinstance(self.state, IdleState):
        #     # If the ride on action is not active,
        #     if any(isinstance(event, RideOn) for event in self.eventList):
        #         # Transition to off state
        #         self.state = self.state.on_event(RideOn())

        # Execute specific actions if in running state:
        if isinstance(self.state, RunningState) or self.demoMode:

            # Servo commands
            if self.rmc.in_parked_position:
                if not self.servos_extended:
                    self.log.info(f"Servos Extending!")
                    self.servos_extended = True
                self.io.extend_servos()
            else:
                if self.servos_extended:
                    self.log.info(f"Servos Retracting!")
                    self.servos_extended = False
                    self.servos_retracted_timer = time.time()
                self.io.retract_servos()
                
            
            # Give the servos some buffer to retract
            if time.time() - self.servos_retracted_timer > 2:

                # Start cycle if not running
                if not self.rmc.is_running:
                    self.log.info("Ride Cycle Started")
                    self.current_motor_instruction = self.rmc.start_cycle()
                
                # Update RMC only if current instruction is Move OR Position & finished
                if (
                    self.current_motor_instruction is None or
                    self.current_motor_instruction.get('name') == 'Move' or
                    (self.current_motor_instruction.get('name') == 'Position' and self.position_command_finished)
                ):
                    new_motor_instr = self.rmc.update(self.position_command_finished)
                    if new_motor_instr != self.current_motor_instruction:
                        self.current_motor_instruction = new_motor_instr
                        self.log.info(f"New Motor Instruction: {new_motor_instr}")

                # With position commands, we must wait till it is finished for us to move to the next one.
                # That is what the position_command_finished does.
                self.position_command_finished = self.io.send_motor_command(self.current_motor_instruction)
        
        if isinstance(self.state, StoppingState):
            self.position_command_finished = self.io.send_motor_command({"name": "Position", "duration": 999, "pos": "home"})

            if self.position_command_finished:
                if not self.servos_extended:
                    self.stopped_timer = time.time()
                    self.log.info(f"Servos Extending!")
                    self.servos_extended = True
                self.io.extend_servos()
            else:
                if self.servos_extended:
                    self.log.info(f"Servos Retracting!")
                    self.servos_extended = False
                    self.servos_retracted_timer = time.time()
                self.io.retract_servos()

            
            if time.time() - self.stopped_timer < 2:
                self.create_event(RideFinishedHoming())

            # Update timeout timer
            self.state = self.state.on_event(None)
        
        # Required to update timer for resetting state
        if isinstance(self.state, ResettingState):
            self.state = self.state.on_event(None)
        
        self.track_dt()

    def is_estop_active(self) -> bool:
        ''' Returns True if any ESTOP condition is active '''
        return (
            self.io.read_estop() or  # Hardware ESTOP
            self.fault_manager.faultRequiresEStop # Faults requiring an ESTOP
        )

    def delete_event(self, event: Event):
        """Handles the creation of an Event by sending it to the appropriate parties."""
        # Remove event from list if it exists
        try:
            self.eventList.remove(event)
        except ValueError:
            pass

        self.log.info(f"Event {event.__class__.__name__} Removed.")

        # Handle EStop even special - need to raise a fault
        # if isinstance(event, EStopPressed):
        #     self.fault_manager.raise_fault(PREDEFINED_FAULTS[101])
    
    def create_event(self, event: Event):
        """Handles the creation of an Event by sending it to the appropriate parties."""
        if isinstance(event, (EStopPressed, RideOff)): # Allows latching behavior for EStop/OnOff
            self.eventList.append(event)
        self.state = self.state.on_event(event)
        self.log.info(f"Event {event.__class__.__name__} Created.")

        # Handle EStop even special - need to raise a fault
        # if isinstance(event, EStopPressed):
        #     self.fault_manager.raise_fault(PREDEFINED_FAULTS[101])


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
    
    def track_dt(self):
        """
        Tracks the delta time of the rcc & prints it to the console every second.
        """
        if not hasattr(self, '_last_update_time'):
            self._last_update_time = time.time()
            self._delta_times = []
            self._last_avg_print_time = time.time()
        current_time = time.time()
        dt = current_time - self._last_update_time
        self._delta_times.append(dt)
        self._last_update_time = current_time

        # Print average delta time every second
        if current_time - self._last_avg_print_time >= 1.0:
            avg_dt = sum(self._delta_times) / len(self._delta_times)
            self.log.info(f"Average delta time: {avg_dt:.6f} seconds")
            self._delta_times.clear()
            self._last_avg_print_time = current_time

            

    
    @property # State Getter
    def state(self) -> State:
        return self._state

    @state.setter # State Setter
    def state(self, new_state: State):
        # Send the current events to the new state
        for event in self.eventList:
            new_state = new_state.on_event(event)
        
        # Set state to new state
        self._state = new_state


if __name__ == '__main__':

    rcc = RideControlComputer()
    rcc.initialize()
    rcc.state = RunningState()
    rcc.start()
