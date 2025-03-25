# Fault Framework for TREC's REC Ride Control Computer
    # Made by Aryan Kumar 


from enum import Enum
import logging
from typing import List

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
    

# Predefined faults
PREDEFINED_FAULTS = {
    101: Fault(101, "Emergency Stop Activated", FaultSeverity.HIGH),
    102: Fault(102, "Power Failure", FaultSeverity.HIGH),
    103: Fault(103, "Motor Controller Failure", FaultSeverity.HIGH),
    104: Fault(104, "Sensor Failure", FaultSeverity.MEDIUM),
    105: Fault(105, "Communication Failure", FaultSeverity.MEDIUM),
    106: Fault(106, "Operator Inactivity Timeout", FaultSeverity.LOW),
    # For 106 I'm not sure if we need to interact with the ride often so I'm including it anyway for safety
    107: Fault(107, "Ride Overload Detected", FaultSeverity.HIGH),
    108: Fault(108, "Speed Deviation Detected", FaultSeverity.MEDIUM),
    109: Fault(109, "Unexpected Stop Detected", FaultSeverity.HIGH),
    110: Fault(110, "Safety Restraint Not Locked", FaultSeverity.HIGH),
    111: Fault(111, "Sensor Mismatch", FaultSeverity.MEDIUM),
    112: Fault(112, "Ride Cycle Timeout", FaultSeverity.MEDIUM),
}

class FaultManager:

    active_faults: List[Fault]

    def __init__(self):
        '''
        FaultManager is used to handle multiple faults for the RCC.

        Raise a fault by calling `raise_fault()`.
        '''
        self.log = logging.getLogger('FaultManager')
        self.active_faults = []
        self.faultRequiresEStop = False
        

    def raise_fault(self, fault: Fault):
        '''
        Used by other classes to raise a fault.

        Params:
            fault (Fault): The fault to be raised
        '''

        self.active_faults.append(fault)
        self.log_fault(fault)


        if fault.severity == FaultSeverity.HIGH:
            self.faultRequiresEStop = True

    def check_faults(self, io, rmc):
        """
        Checks for various fault conditions by comparing actual sensor and motor encoder data.
        """
        # Read actual values using the provided methods
        actual_motor_speed = io.read_speed()  # Returns dict {motor_id: speed}
        actual_motor_position = io.read_position()  # Returns dict {motor_id: position}
        actual_sensor_data = io.read_sensor()  # Returns dict {sensor_id: value}

        # Fault Detection Logic
        
        # Emergency stop detection
        if io.read_estop():
            self.raise_fault(PREDEFINED_FAULTS[101])

        # Power failure detection
        if not io.is_power_on():
            self.raise_fault(PREDEFINED_FAULTS[102])

        # Motor controller failure
        if not rmc.is_motor_controller_responsive():
            self.raise_fault(PREDEFINED_FAULTS[103])

        # Sensor failure detection (Assumes None means failure)
        for sensor_id, value in actual_sensor_data.items():
            if value is None:
                self.raise_fault(PREDEFINED_FAULTS[104])
                self.log.warning(f"Sensor {sensor_id} failed.")

        # Communication failure detection
        if not io.is_connected():
            self.raise_fault(PREDEFINED_FAULTS[105])

        # Motor speed deviation detection
        for motor_id, actual_speed in actual_motor_speed.items():
            expected_speed = rmc.get_commanded_speed(motor_id)
            if abs(actual_speed - expected_speed) > 5:  # Threshold adjustable
                # Change the value for correct margin of error (MOE)
                self.raise_fault(PREDEFINED_FAULTS[108])
                self.log.warning(f"Motor {motor_id} speed deviation: Expected {expected_speed}, Got {actual_speed}")

        # Position mismatch detection
        for motor_id, actual_position in actual_motor_position.items():
            expected_position = rmc.get_commanded_position(motor_id)
            if abs(actual_position - expected_position) > 2:  # Threshold adjustable
                # Change the value for the correct MOE
                self.raise_fault(PREDEFINED_FAULTS[111])
                self.log.warning(f"Motor {motor_id} position mismatch: Expected {expected_position}, Got {actual_position}")

        # Ride overload detection
        if rmc.detects_overload():
            self.raise_fault(PREDEFINED_FAULTS[107])

        # Ride cycle timeout detection
        if rmc.ride_cycle_exceeded():
            self.raise_fault(PREDEFINED_FAULTS[112])

    def log_fault(self, fault: Fault):
        if fault.severity == FaultSeverity.LOW:
            self.log.warning(f"FAULT DETECTED: {fault}")
        elif fault.severity == FaultSeverity.MEDIUM:
            self.log.error(f"FAULT DETECTED: {fault}")
        elif fault.severity == FaultSeverity.HIGH:
            self.log.critical(f"FAULT DETECTED: {fault}")

    def clear_all_faults(self):
        self.active_faults.clear()


    def clear_fault(self, faultCodeToClear: int) -> bool:
        '''
        Clears a fault from the active list based on its fault code

        Returns:
            bool: Whether the fault was successfully cleared.
        '''

        for activeFault in self.active_faults[:]:  # Iterate over a copy
            if activeFault.code == faultCodeToClear:
                self.active_faults.remove(activeFault)
                self.log.info(f'Fault #{faultCodeToClear} Cleared')
                return True
        return False